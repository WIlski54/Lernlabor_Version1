"""Webfassung der Szene für Three.js (iPad-tauglich). Läuft im Hintergrund auf labor.blend:
blender -b labor.blend -P pipeline/blender/web_export.py -- <zielordner> [teil1,teil2,…]
Die Szene wird nur im Speicher verändert, labor.blend wird nicht gespeichert."""
import json
import math
import os
import struct

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import layout as L
from .util import collection, leere, modus_setzen

TMP = "WEB_TMP"


def drei(v):
    """Blender (Z oben) → Three.js (Y oben)."""
    return [round(v[0], 4), round(v[2], 4), round(-v[1], 4)]


def vorbereiten():
    if not bpy.data.filepath.lower().endswith("labor.blend"):
        raise RuntimeError("Webexport nur aus labor.blend")
    cp = bpy.context.preferences.addons["cycles"].preferences
    cp.compute_device_type = "OPTIX"
    cp.refresh_devices()
    for d in cp.devices:
        d.use = d.type == "OPTIX"
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    modus_setzen(0.0)
    collection(TMP)
    leere(TMP)


def auswahl_setzen(objekte, aktiv=None):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objekte:
        o.select_set(True)
    bpy.context.view_layer.objects.active = aktiv or (objekte[0] if objekte else None)


def kopie(o, dg):
    """Ausgewertete Kopie (Modifier angewandt, Weltkoordinaten in den Daten) in WEB_TMP.
    Objekte mit Geometry Nodes (Rasen, Wiese) liefern nur ihr Grundnetz – die Pflanzen kommen als Instanzen."""
    if any(m.type == "NODES" for m in o.modifiers):
        me = o.data.copy()
    else:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    k = bpy.data.objects.new(f"WEB_{o.name}", me)
    bpy.data.collections[TMP].objects.link(k)
    return k


def vereinen(name, objekte):
    objekte = [o for o in objekte if o.type == "MESH" and len(o.data.polygons)]
    if len(objekte) > 1:
        with bpy.context.temp_override(active_object=objekte[0], selected_editable_objects=objekte,
                                       selected_objects=objekte):
            bpy.ops.object.join()
    o = objekte[0]
    o.name = name
    o.data.name = name
    return o


def exportieren(objekte, pfad, materialien=True):
    auswahl_setzen(objekte)
    bpy.ops.export_scene.gltf(filepath=pfad, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials="EXPORT" if materialien else "NONE",
                              export_image_format="AUTO", export_animations=False, export_skins=False,
                              export_morph=False, export_cameras=False, export_lights=False)


def himmel(ziel):
    """HDRI als 2048×1024-JPG (bewölkter Himmel als Hintergrund)."""
    env = [n for n in bpy.context.scene.world.node_tree.nodes if n.type == "TEX_ENVIRONMENT"][0]
    img = env.image.copy()
    img.scale(2048, 1024)
    img.filepath_raw = os.path.join(ziel, "himmel.jpg")
    img.file_format = "JPEG"
    img.save()
    bpy.data.images.remove(img)


def rasenmaske(ziel, aufloesung=0.1):
    """1 Byte je 10 cm: 255 = Rasen (keine Maske-Geometrie in der Nähe), 0 = sonst. Zeilen laufen in +z (Three.js)."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in bpy.data.collections["Maske_Rasen"].all_objects:
        if o.type not in ("MESH", "CURVE"):
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        start = len(verts)
        verts += [v.co.copy() for v in me.vertices]
        polys += [[start + i for i in p.vertices] for p in me.polygons]
        bpy.data.meshes.remove(me)
    baum = BVHTree.FromPolygons(verts, polys)
    x0, y0, x1, y1 = L.GRUNDSTUECK
    breite, hoehe = int((x1 - x0) / aufloesung), int((y1 - y0) / aufloesung)
    daten = bytearray(breite * hoehe)
    for iz in range(hoehe):
        y = y1 - (iz + 0.5) * aufloesung                     # Three z = -Blender y
        for ix in range(breite):
            x = x0 + (ix + 0.5) * aufloesung
            treffer = baum.find_nearest(Vector((x, y, 0.0)), 0.15)
            daten[iz * breite + ix] = 0 if treffer[0] is not None else 255
    with open(os.path.join(ziel, "rasenmaske.bin"), "wb") as f:
        f.write(daten)
    kopf = {"x0": x0, "z0": -y1, "aufloesung": aufloesung, "breite": breite, "hoehe": hoehe}
    with open(os.path.join(ziel, "rasenmaske.json"), "w", encoding="utf-8") as f:
        json.dump(kopf, f)
    return {"rasen_anteil": round(sum(1 for b in daten if b) / len(daten), 3)}


def weltkonfig(ziel):
    cam = bpy.data.objects["Kamera_Laufen"]
    vorne = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    v3 = drei(vorne)
    sonne = bpy.data.objects["Sonne"].matrix_world.to_3x3() @ Vector((0, 0, -1))
    mik = bpy.data.objects["Labor_Mikroskop"]
    mitte_mik = mik.matrix_world @ (sum((Vector(c) for c in mik.bound_box), Vector()) / 8)
    konf = {
        "start": {"position": drei(cam.matrix_world.translation), "yaw": round(math.atan2(-v3[0], -v3[2]), 4)},
        "sonne_richtung": drei(sonne),
        "mikroskop": drei(mitte_mik),
        "whiteboard": "Whiteboard_Flaeche",
        "augenhoehe": 1.65,
    }
    with open(os.path.join(ziel, "welt.json"), "w", encoding="utf-8") as f:
        json.dump(konf, f, indent=1)
    return konf


TEILE = {}


def teil(name):
    def deko(fn):
        TEILE[name] = fn
        return fn
    return deko


@teil("basis")
def _basis(ziel):
    himmel(ziel)
    return {"maske": rasenmaske(ziel), "welt": weltkonfig(ziel)}


def alles(ziel, nur=None):
    os.makedirs(ziel, exist_ok=True)
    vorbereiten()
    erg = {}
    for name, fn in TEILE.items():
        if nur and name not in nur:
            continue
        erg[name] = fn(ziel)
        print("TEIL FERTIG", name, flush=True)
    return erg


GRUPPEN = {
    # name: (Collections, Namensanfänge ausschließen, Auflösung)
    "haus": (["02_Architektur"], ("Glas_", "Schneider_", "WEB_"), 4096),
    "labor": (["03_Innenraum"], ("Labor_Sammelglaeser", "Whiteboard_Flaeche", "WEB_"), 2048),
    "hof": (["04_Hardscape"], ("WEB_",), 2048),
    "boden": (["01a_Beete", "05a_Rasen"], ("WEB_",), 2048),
    "hecke": (["01c_Heckenkern"], ("WEB_",), 2048),
}


def _gruppenobjekte(sammlungen, ohne):
    erg = []
    for s in sammlungen:
        for o in bpy.data.collections[s].all_objects:
            if o.type in ("MESH", "CURVE") and not o.name.startswith(ohne):
                if o.hide_render or o.name.endswith("_Laub"):   # Laub teilt die Kern-Daten, kommt als Instanzen
                    continue
                if any(m and m.name == "M_Glas" for m in getattr(o.data, "materials", [])):
                    continue
                erg.append(o)
    return erg


def _lightmap_uv(o, aufl):
    me = o.data
    lm = me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = lm                       # Ziel des Bakes; vorhandene UVs bleiben 'active_render'
    auswahl_setzen([o])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    # Neu packen mit 4 px Abstand: bei vielen kleinen Inseln (Haus) frisst island_margin sonst ~85 % der Fläche
    bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=4 / aufl, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def _ersatzmaterial():
    """Für leere Materialplätze: der Bake braucht in jedem Platz einen Bildknoten."""
    m = bpy.data.materials.get("WEB_Ersatz") or bpy.data.materials.new("WEB_Ersatz")
    return m


def _backen(o, bild, samples):
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.render.bake.margin = 8
    for i, m in enumerate(o.data.materials):
        if m is None:
            o.data.materials[i] = _ersatzmaterial()
    knoten = []
    for m in o.data.materials:
        if m is None or not m.use_nodes:
            continue
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = bild
        m.node_tree.nodes.active = n
        knoten.append((m, n))
    auswahl_setzen([o])
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT", "COLOR"}, margin=8, use_clear=True)
    for m, n in knoten:
        m.node_tree.nodes.remove(n)


def _bild_speichern(bild, pfad, faktor=0.5):
    """Linearen Bake halbieren (Spielraum über 1.0; die Web-App multipliziert ×2) und als PNG speichern."""
    px = np.empty(len(bild.pixels), dtype=np.float32)
    bild.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    px[:, :3] = np.clip(px[:, :3] * faktor, 0.0, 1.0)
    px[:, 3] = 1.0
    bild.pixels.foreach_set(px.ravel())
    bild.filepath_raw = pfad
    bild.file_format = "PNG"
    bild.save()


def _webmaterial(name, pfad):
    m = bpy.data.materials.new(f"WEB_Licht_{name}")
    b = m.node_tree.nodes.get("Principled BSDF")
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(pfad)
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    return m


def bake_gruppe(name, ziel, samples=192):
    sammlungen, ohne, aufl = GRUPPEN[name]
    dg = bpy.context.evaluated_depsgraph_get()
    originale = _gruppenobjekte(sammlungen, ohne)
    kopien = [kopie(o, dg) for o in originale]
    for o in originale:                       # Originale verbergen, damit Kopie und Original sich nicht verschatten
        o.hide_render = True
    o = vereinen(f"Licht_{name}", kopien)
    _lightmap_uv(o, aufl)
    bild = bpy.data.images.new(f"Licht_{name}", aufl, aufl, alpha=False, float_buffer=True)
    _backen(o, bild, samples)
    pfad = os.path.join(ziel, f"licht_{name}.png")
    _bild_speichern(bild, pfad)
    me = o.data
    for uv in [u for u in me.uv_layers if u.name != "Lightmap"]:
        me.uv_layers.remove(uv)
    me.materials.clear()
    me.materials.append(_webmaterial(name, pfad))
    for p in me.polygons:
        p.material_index = 0
    exportieren([o], os.path.join(ziel, f"{name}.glb"))
    o.hide_render = True                      # fertige Kopie soll die folgenden Gruppen nicht doppelt verschatten
    for orig in originale:
        orig.hide_render = False
    return {"dreiecke": sum(len(p.vertices) - 2 for p in me.polygons), "aufloesung": aufl}


def glas_export(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.data.objects if o.type == "MESH" and
            any(m and m.name == "M_Glas" for m in o.data.materials) and not o.name.startswith("WEB_")]
    o = vereinen("Glas", [kopie(x, dg) for x in objs])
    exportieren([o], os.path.join(ziel, "glas.glb"))
    return {"objekte": len(objs)}


def whiteboard_export(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    orig = bpy.data.objects["Whiteboard_Flaeche"]
    k = kopie(orig, dg)
    orig.name = "Whiteboard_Flaeche_Original"     # sonst hieße die Kopie „Whiteboard_Flaeche.001“
    k.name = "Whiteboard_Flaeche"
    exportieren([k], os.path.join(ziel, "whiteboard.glb"))
    k.name = "WEB_Whiteboard_Flaeche"
    orig.name = "Whiteboard_Flaeche"
    return {"ok": True, "name": "Whiteboard_Flaeche"}


@teil("bake")
def _bake(ziel):
    erg = {name: bake_gruppe(name, ziel) for name in GRUPPEN}
    erg["glas"] = glas_export(ziel)
    erg["whiteboard"] = whiteboard_export(ziel)
    return erg
