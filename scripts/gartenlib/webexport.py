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
    haus = bpy.data.objects["Haus"]
    lpos = drei(haus.matrix_world @ Vector((-2.0, 2.4, L.INNEN["boden_z"])))
    ld = drei(haus.matrix_world.to_3x3() @ Vector((0, 1, 0)))
    konf = {
        "start": {"position": drei(cam.matrix_world.translation), "yaw": round(math.atan2(-v3[0], -v3[2]), 4)},
        "labor_start": {"position": lpos, "yaw": round(math.atan2(-ld[0], -ld[2]), 4)},
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


# Vereinfachung je Prototyp (Anteil der Dreiecke, die bleiben) und Ausdünnung der Instanzen
# (Rasenstücke kommen nur aus den Beeten mit Bib_Halme; den Rasen selbst zeichnet die Web-App als Gras.)
VEREINFACHUNG = {"Ziergras": 0.25, "Staude": 0.35, "Kiefernpolster": 0.08, "Rasenstueck_Lauf": 0.5,
                 "Heckenballen_Lauf": 0.2}
AUSDUENNEN = {"Heckenballen_Lauf": 6}           # jede 6. Hecken-Instanz (Budget: ~1 Mio. Dreiecke für Pflanzen + Bäume)
IGNORIEREN = ("fern_", "shrub_", "pine_sapling")  # Poly-Haven-Sträucher (Alpha-Texturen) im Web weglassen
# Bäume: Blattmenge (Faktor auf blatt_dichte), Blattgröße (Faktor auf ARTEN["blatt"]), kleinste Röhrenfläche
# in m² (dünnere Zweige entfallen – jede Aströhre ist eine eigene Insel, Decimate kann sie kaum verkleinern)
# und Anteil der verbleibenden Holz-Dreiecke. Die Kulisse (34–52 m entfernt, im Nebel) bekommt wenige,
# sehr große Blätter.
BAUM_WEB = {"garten": {"blatt_faktor": 0.12, "blatt_skala": 2.2, "zweig_min": 0.01, "holz": 0.4},
            "kulisse": {"blatt_faktor": 0.025, "blatt_skala": 4.5, "zweig_min": 0.1, "holz": 0.3}}


def _praefix(name):
    for p in VEREINFACHUNG:
        if name.startswith(p):
            return p
    return None


def _dreiecke(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def _dezimieren(o, anteil):
    """Decimate (Collapse) direkt anwenden – vor dem Vereinen nötig, join übernimmt keine Modifier."""
    if anteil >= 1.0:
        return
    dm = o.modifiers.new("Vereinfachen", "DECIMATE")
    dm.ratio = anteil
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=dm.name)


def _zweige_entfernen(o, flaeche_min):
    """Löscht zusammenhängende Röhren (Inseln) mit weniger als flaeche_min m² (Mesh-Koordinaten)."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    gesehen, weg = set(), []
    for f in bm.faces:
        if f in gesehen:
            continue
        stapel, insel = [f], []
        gesehen.add(f)
        while stapel:
            g = stapel.pop()
            insel.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in gesehen:
                        gesehen.add(h)
                        stapel.append(h)
        if sum(x.calc_area() for x in insel) < flaeche_min:
            weg += insel
    bmesh.ops.delete(bm, geom=weg, context="FACES")
    bm.to_mesh(o.data)
    bm.free()


def _rampenfarbe(m):
    """Blattfarbe: der Farbverlauf, der wirklich in Principled 'Base Color' einspeist
    (nicht eine Alpha-/Formmaske); sonst Basisfarbe des Principled."""
    if not (m and m.use_nodes):
        return (0.1, 0.2, 0.05)
    for p in (n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"):
        eing = p.inputs["Base Color"]
        if not eing.is_linked:
            return tuple(eing.default_value)[:3]
        stapel, gesehen = [eing.links[0].from_node], set()
        while stapel:
            n = stapel.pop(0)
            if n in gesehen:
                continue
            gesehen.add(n)
            if n.type == "VALTORGB":
                return tuple(n.color_ramp.evaluate(0.5))[:3]
            stapel += [l.from_node for i in n.inputs for l in i.links]
    return (0.1, 0.2, 0.05)


def _einfache_materialien(o):
    neu = []
    for m in o.data.materials:
        wm = bpy.data.materials.new(f"WEB_P_{m.name if m else 'leer'}")
        b = wm.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*_rampenfarbe(m), 1.0)
        b.inputs["Roughness"].default_value = 0.8
        neu.append(wm)
    for i, wm in enumerate(neu):       # Slots einzeln ersetzen: materials.clear() setzt alle Flächen auf Slot 0
        o.data.materials[i] = wm


def _instanzdaten(dg, filter_fn):
    """{prototypname: [pos(3), quat(4), skala(1)] …} in Three.js-Koordinaten."""
    daten = {}
    zaehler = {}
    for inst in dg.object_instances:
        if not inst.is_instance or inst.parent is None:
            continue
        if not filter_fn(inst.parent.original):
            continue
        name = inst.object.original.name
        if name.startswith(IGNORIEREN) or _praefix(name) is None:
            continue
        zaehler[name] = zaehler.get(name, 0) + 1
        if zaehler[name] % AUSDUENNEN.get(_praefix(name), 1):
            continue
        loc, rot, sk = inst.matrix_world.decompose()
        daten.setdefault(name, []).append(drei(loc) + [round(rot.x, 5), round(rot.z, 5), round(-rot.y, 5),
                                                         round(rot.w, 5), round(sk.x, 4)])
    return daten


def _instanzen_schreiben(daten, ziel, basisname):
    index, puffer, offset = {}, bytearray(), 0
    for name, liste in sorted(daten.items()):
        for werte in liste:
            puffer += struct.pack("<8f", *werte)
        index[name] = {"offset": offset, "anzahl": len(liste)}
        offset += len(liste)
    with open(os.path.join(ziel, f"{basisname}.bin"), "wb") as f:
        f.write(puffer)
    with open(os.path.join(ziel, f"{basisname}.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
    return {k: v["anzahl"] for k, v in index.items()}


def _prototypen_exportieren(namen, ziel, dateiname):
    """Kopien der Bibliotheksobjekte unter dem Originalnamen (= Schlüssel der Instanzdaten) exportieren."""
    protos, dreiecke, originale = [], {}, []
    for name in namen:
        orig = bpy.data.objects[name]
        k = bpy.data.objects.new(f"WEB_{name}", orig.data.copy())
        bpy.data.collections[TMP].objects.link(k)
        _dezimieren(k, VEREINFACHUNG.get(_praefix(name), 1.0))
        _einfache_materialien(k)
        orig.name = f"{name}_orig"
        k.name = name
        originale.append((orig, k, name))
        dreiecke[name] = _dreiecke(k.data)
        protos.append(k)
    exportieren(protos, os.path.join(ziel, dateiname))
    for orig, k, name in originale:                  # Namen zurücksetzen
        k.name = f"WEB_{name}"
        orig.name = name
    return dreiecke


@teil("pflanzen")
def _pflanzen(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    daten = _instanzdaten(dg, lambda p: p.name.startswith(("Pflanzung_", "Hecke_")))
    anz = _instanzen_schreiben(daten, ziel, "pflanzen_instanzen")
    dreiecke = _prototypen_exportieren(sorted(daten), ziel, "pflanzen.glb")
    return {"instanzen": anz, "dreiecke": dreiecke,
            "summe_instanziert": sum(dreiecke[n] * anz[n] for n in anz)}


def _srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def _blatttextur(name, form, farbe, pfad, n=128):
    """Blattform als RGBA-PNG (Alpha = Blattumriss), passend zu den UVs der Baum-Blätter (u quer, v längs).
    farbe ist linear; das 8-Bit-Bild speichert sRGB (pixels eines Byte-Bildes werden nicht umgerechnet)."""
    v, u = np.mgrid[0:n, 0:n] / (n - 1)
    cx = 2 * u - 1
    if form == "ahorn":
        cy = 2 * v - 0.9
        r = np.sqrt(cx ** 2 + cy ** 2)
        w = np.arctan2(cx, cy)
        maske = r < 0.35 + 0.6 * np.abs(np.cos(2.5 * w)) ** 3
    else:
        maske = np.abs(cx) < np.sin(np.pi * np.clip(v, 0, 1) ** 0.7) * 0.95
    ader = np.exp(-(cx / 0.05) ** 2) * 0.25
    px = np.zeros((n, n, 4), dtype=np.float32)
    for k in range(3):
        px[:, :, k] = _srgb(farbe[k] * (0.85 + 0.3 * v) * (1 - ader))
    px[:, :, 3] = maske.astype(np.float32)
    img = bpy.data.images.new(name, n, n, alpha=True)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = pfad
    img.file_format = "PNG"
    img.save()
    return img


def _blattmaterial(name, bild):
    m = bpy.data.materials.new(f"WEB_Blatt_{name}")
    b = m.node_tree.nodes.get("Principled BSDF")
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bild
    m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    m.node_tree.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m


def _hoehe_roh(*objekte):
    """Höchster Punkt in den (unskalierten) Mesh-Daten von Stamm und Laub."""
    return max(max((v.co.z for v in o.data.vertices), default=0.0) for o in objekte)


@teil("baeume")
def _baeume(ziel):
    from . import baeume as B
    alt = {k: dict(v) for k, v in B.ARTEN.items()}
    def blattgroesse(faktor):                             # weniger, dafür größere Blätter
        for k, art in B.ARTEN.items():
            art["blatt"] = (alt[k]["blatt"][0] * faktor, alt[k]["blatt"][1] * faktor)

    try:
        bilder = {"birke": _blatttextur("blatt_birke", "birke", (0.12, 0.2, 0.05), os.path.join(ziel, "blatt_birke.png")),
                  "ahorn": _blatttextur("blatt_ahorn", "ahorn", (0.3, 0.3, 0.07), os.path.join(ziel, "blatt_ahorn.png"))}
        laub = {a: _blattmaterial(a, b) for a, b in bilder.items()}
        rinde = {"birke": bpy.data.materials.new("WEB_Rinde_birke"), "ahorn": bpy.data.materials.new("WEB_Rinde_ahorn")}
        rinde["birke"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.73, 0.68, 1)
        rinde["ahorn"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.2, 0.17, 1)
        G, K = BAUM_WEB["garten"], BAUM_WEB["kulisse"]
        objekte, garten = [], {}
        blattgroesse(G["blatt_skala"])
        for name, art, ort, hoehe, seed in L.BAEUME:
            B.baum(f"WEBB_{name}", art, ort, hoehe, seed, laub[art], rinde[art], blatt_faktor=G["blatt_faktor"],
                   sammlung=TMP)
            stamm, laub_o = bpy.data.objects[f"WEBB_{name}"], bpy.data.objects[f"WEBB_{name}_Laub"]
            _zweige_entfernen(stamm, G["zweig_min"])
            _dezimieren(stamm, G["holz"])
            garten[f"WEBB_{name}"] = _dreiecke(stamm.data) + _dreiecke(laub_o.data)
            objekte += [stamm, laub_o]
        protos = []
        blattgroesse(K["blatt_skala"])
        for name, art, hoehe, seed in L.KULISSE["vorlagen"]:
            B.baum(f"WEBK_{name}", art, (0.0, 0.0), hoehe, seed, laub[art], rinde[art], blatt_faktor=K["blatt_faktor"],
                   sammlung=TMP)
            protos.append(name)
    finally:
        B.ARTEN.clear()
        B.ARTEN.update(alt)
    # Kulisse: Instanzen aus den vorhandenen Kulissenbäumen (Vorlage über die geteilten Mesh-Daten).
    # Der Web-Prototyp hat Skalierung 1; seine Rohhöhe weicht von der Vorlage ab (anderer Zufallsverlauf
    # durch weniger Blätter), daher wird die Instanzskalierung um hoehe_vorlage / hoehe_web korrigiert.
    korrektur = {}
    for name in protos:
        korrektur[name] = _hoehe_roh(bpy.data.objects[name], bpy.data.objects[f"{name}_Laub"]) / _hoehe_roh(
            bpy.data.objects[f"WEBK_{name}"], bpy.data.objects[f"WEBK_{name}_Laub"])
    vorlage_von_mesh = {bpy.data.objects[n].data.name: n for n, *_ in L.KULISSE["vorlagen"]}
    daten = {}
    for o in bpy.data.collections["05f_Kulisse"].objects:
        if o.name.endswith("_Laub") or o.data.name not in vorlage_von_mesh:
            continue
        vorlage = vorlage_von_mesh[o.data.name]
        loc, rot, sk = o.matrix_world.decompose()
        daten.setdefault(f"WEBK_{vorlage}", []).append(
            drei(loc) + [round(rot.x, 5), round(rot.z, 5), round(-rot.y, 5), round(rot.w, 5),
                         round(sk.x * korrektur[vorlage], 4)])
    anz = _instanzen_schreiben(daten, ziel, "baeume_instanzen")
    kulisse, dreiecke = [], {}
    for name in protos:                                   # Stamm + Laub zu einem Prototyp vereinen
        stamm, laub_o = bpy.data.objects[f"WEBK_{name}"], bpy.data.objects[f"WEBK_{name}_Laub"]
        _zweige_entfernen(stamm, K["zweig_min"])
        _dezimieren(stamm, K["holz"])
        laub_o.parent = None
        for o in (stamm, laub_o):                         # Prototyp im Ursprung, ohne Drehung, Skalierung 1
            o.location, o.rotation_euler, o.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
        p = vereinen(f"WEBK_{name}", [stamm, laub_o])
        dreiecke[p.name] = _dreiecke(p.data)
        kulisse.append(p)
    exportieren(objekte + kulisse, os.path.join(ziel, "baeume.glb"))
    return {"gartenbaeume": garten, "kulisse_instanzen": anz, "kulisse_dreiecke": dreiecke,
            "hoehenkorrektur": {k: round(v, 3) for k, v in korrektur.items()},
            "summe": sum(garten.values()) + sum(dreiecke[n] * anz[n] for n in anz)}


@teil("wiese")
def _wiese(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    k = kopie(bpy.data.objects["Wiese"], dg)
    k.data.materials.clear()
    m = bpy.data.materials.new("WEB_Wiese")
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.16, 0.04, 1)
    k.data.materials.append(m)
    exportieren([k], os.path.join(ziel, "wiese.glb"))
    return {"ok": True, "dreiecke": _dreiecke(k.data)}


WAND_SAMMLUNGEN_NAMEN = ("Haus_EG", "Haus_OG", "Fluegel", "Vordach_Stuetzen", "Carport_Stuetzen", "Feuerschale",
                         "Feuerschale_Fuss")
BODEN_NAMEN = ("Rasen", "Wiese", "Hof_Platten", "Weg_Fluegel", "Carport_Boden", "Terrasse", "Labor_Boden")


def _box_aus_bbox(bm, o):
    ecken = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(e.x for e in ecken), min(e.y for e in ecken), min(e.z for e in ecken)))
    mx = Vector((max(e.x for e in ecken), max(e.y for e in ecken), max(e.z for e in ecken)))
    from .util import bm_box
    bm_box(bm, mx - mn, (mn + mx) / 2)


@teil("kollision")
def _kollision(ziel):
    from .util import mesh_aus_bmesh
    from .fassade import _rohr
    dg = bpy.context.evaluated_depsgraph_get()
    waende = [kopie(bpy.data.objects[n], dg) for n in WAND_SAMMLUNGEN_NAMEN if n in bpy.data.objects]
    waende += [kopie(o, dg) for o in bpy.data.objects
               if o.type == "MESH" and (o.name.startswith(("Tuerblatt_", "Glas_")) or
                                        (o.name.startswith("Hecke_") and o.name.endswith("_Kern")))]
    bm = bmesh.new()                                    # Möbel, Sessel, Poller als Quader; Stämme als Zylinder
    for o in bpy.data.collections["03_Innenraum"].all_objects:
        if o.type == "MESH" and o.name.startswith("Labor_") and not o.name.startswith(("Labor_Boden", "Labor_Lichtpaneele")):
            _box_aus_bbox(bm, o)
    for o in bpy.data.collections["04_Hardscape"].all_objects:
        if o.type in ("MESH", "CURVE") and o.name.startswith(("Sessel_", "Poller_")):
            _box_aus_bbox(bm, o)
    for name, _a, ort, _h, _s in L.BAEUME:
        _rohr(bm, Vector((ort[0], ort[1], 0)), Vector((ort[0], ort[1], 3.0)), 0.28, 10)
    hilfen = mesh_aus_bmesh("WEB_Kollision_Hilfen", bm, TMP)
    waende.append(hilfen)
    w = vereinen("Waende", waende)
    boden = vereinen("Boden", [kopie(bpy.data.objects[n], dg) for n in BODEN_NAMEN if n in bpy.data.objects] +
                     [kopie(o, dg) for o in bpy.data.objects if o.name.startswith("Trittplatte_")])
    for o in (w, boden):
        o.data.materials.clear()
    exportieren([w, boden], os.path.join(ziel, "kollision.glb"), materialien=False)
    return {"waende_dreiecke": sum(len(p.vertices) - 2 for p in w.data.polygons),
            "boden_dreiecke": sum(len(p.vertices) - 2 for p in boden.data.polygons)}
