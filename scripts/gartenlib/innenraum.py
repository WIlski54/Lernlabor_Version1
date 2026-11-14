"""Erdgeschoss innen: Parkett, Decke, Küche, Poly-Haven-Möbel, Leuchten, Eevee-Lichtsonden, Innenkamera."""
import glob
import math

import bpy
from mathutils import Matrix, Vector

from . import layout as L
from .materialien import auswahl
from .util import boxen_objekt, leere, material, neues_objekt, pfad, setze, view3d_kontext

S = "03_Innenraum"


def _modell_laden(aid):
    datei = glob.glob(pfad("assets", "polyhaven", "models", aid, "*.blend"))[0]
    with bpy.data.libraries.load(datei, link=False) as (quelle, neu):
        neu.objects = list(quelle.objects)
    objs = [o for o in neu.objects if o is not None]
    meshes = [o for o in objs if o.type == "MESH"]
    if any("lod" in o.name.lower() for o in meshes):
        meshes = [o for o in meshes if "lod0" in o.name.lower().replace("_", "")]
    teile = [(o, o.matrix_world.copy()) for o in meshes]
    for o in objs:
        if o not in meshes:
            bpy.data.objects.remove(o)
    ecken = [mw @ Vector(c) for o, mw in teile for c in o.bound_box]
    mitte_unten = Vector(((min(e.x for e in ecken) + max(e.x for e in ecken)) / 2,
                          (min(e.y for e in ecken) + max(e.y for e in ecken)) / 2, min(e.z for e in ecken)))
    hoehe = max(e.z for e in ecken) - min(e.z for e in ecken)
    return {"teile": teile, "mitte_unten": mitte_unten, "hoehe": hoehe, "benutzt": False}


def _moebel(rolle, name, ort, drehung, an_decke, haus, cache, log):
    a = auswahl()
    if rolle not in a:
        log.append(f"{name}: Rolle {rolle} nicht gewählt – übersprungen")
        return
    aid = a[rolle][0] if isinstance(a[rolle], list) else a[rolle]
    if aid not in cache:
        cache[aid] = _modell_laden(aid)
    c = cache[aid]
    I = L.INNEN
    z = I["decke_z"] - c["hoehe"] if an_decke else I["boden_z"] + 0.02
    wurzel = neues_objekt(f"Moebel_{name}", None, S, eltern=haus)
    wurzel.location = (ort[0], ort[1], z)
    wurzel.rotation_euler = (0.0, 0.0, math.radians(drehung))
    for o, mw in c["teile"]:
        teil = o if not c["benutzt"] else o.copy()
        bpy.data.collections[S].objects.link(teil)
        teil.parent = wurzel
        teil.matrix_parent_inverse = Matrix.Identity(4)
        teil.matrix_basis = Matrix.Translation(-c["mitte_unten"]) @ mw
    c["benutzt"] = True
    log.append(f"{name}: {aid} ({c['hoehe']:.2f} m hoch)")


def _kueche(haus):
    I = L.INNEN
    z = I["boden_z"]
    front = material("M_Kueche_Front", (0.05, 0.05, 0.055), 0.55)
    platte = bpy.data.materials["M_Arbeitsplatte"]
    k = I["kueche"]
    korpusse = [((b, t, 0.86), (x, y, z + 0.43)) for (x, y), (b, t) in (k["zeile"], k["insel"])]
    (hx, hy), (hb, ht) = k["hochschrank"]
    korpusse.append(((hb, ht, 2.3), (hx, hy, z + 1.15)))
    boxen_objekt("Innen_Kueche", korpusse, S, haus, front)
    platten = [((b + 0.04, t + 0.04, 0.04), (x, y, z + 0.88)) for (x, y), (b, t) in (k["zeile"], k["insel"])]
    boxen_objekt("Innen_Arbeitsplatte", platten, S, haus, platte)


def _lichter(haus):
    for name, typ, (x, y, z), leistung, groesse in L.INNEN["lichter"]:
        li = bpy.data.lights.get(name)
        if li is not None and li.type != typ:
            bpy.data.lights.remove(li)
            li = None
        li = li or bpy.data.lights.new(name, typ)
        li.energy = leistung
        li.color = (1.0, 0.82, 0.62)  # warmweiß, ca. 2900 K
        if typ == "AREA":
            li.size = groesse
        else:
            li.shadow_soft_size = groesse
        o = neues_objekt(name, li, S, eltern=haus)
        o.location = (x, y, z)


def _lichtsonden(haus, log):
    I = L.INNEN
    mitte_z = (I["boden_z"] + I["decke_z"]) / 2
    gi = bpy.data.lightprobes.get("Innen_GI") or bpy.data.lightprobes.new("Innen_GI", "VOLUME")
    o = neues_objekt("Innen_GI", gi, S, eltern=haus)
    o.location = (0.0, 0.0, mitte_z)
    o.scale = (I["breite"] / 2, I["tiefe"] / 2, (I["decke_z"] - I["boden_z"]) / 2)
    for attr, wert in (("resolution_x", 12), ("resolution_y", 9), ("resolution_z", 4)):
        setze(gi, attr, wert, log)
    ref = bpy.data.lightprobes.get("Innen_Reflexion") or bpy.data.lightprobes.new("Innen_Reflexion", "SPHERE")
    setze(ref, "influence_distance", 7.0, log)
    o2 = neues_objekt("Innen_Reflexion", ref, S, eltern=haus)
    o2.location = (0.0, 0.0, mitte_z)


def _kamera(haus):
    K = L.INNEN["kamera"]
    alt = bpy.data.objects.get("Kamera_Innen")
    if alt is not None:
        bpy.data.objects.remove(alt, do_unlink=True)
    cam = bpy.data.cameras.get("Kamera_Innen") or bpy.data.cameras.new("Kamera_Innen")
    cam.lens = K["brennweite"]
    cam.clip_start = 0.05
    o = neues_objekt("Kamera_Innen", cam, "07_Kameras")
    mw = haus.matrix_world
    ort, ziel = mw @ Vector(K["ort"]), mw @ Vector(K["ziel"])
    o.location = ort
    o.rotation_euler = (ziel - ort).to_track_quat("-Z", "Y").to_euler()


def baue():
    log = []
    leere(S)
    haus = bpy.data.objects["Haus"]
    I = L.INNEN
    boxen_objekt("Innen_Boden", [((I["breite"], I["tiefe"], 0.02), (0.0, 0.0, I["boden_z"] + 0.01))], S, haus,
                 bpy.data.materials["M_Parkett"])
    boxen_objekt("Innen_Decke", [((I["breite"], I["tiefe"], 0.01), (0.0, 0.0, I["decke_z"] - 0.006))], S, haus,
                 material("M_Decke", (0.82, 0.81, 0.78), 0.9))
    _kueche(haus)
    cache = {}
    for rolle, name, ort, drehung, an_decke in I["moebel"]:
        _moebel(rolle, name, ort, drehung, an_decke, haus, cache, log)
    _lichter(haus)
    _lichtsonden(haus, log)
    _kamera(haus)
    return {"log": log, "objekte": len(bpy.data.collections[S].all_objects)}


def sonden_backen():
    """Eevee-Lichtsonden backen (nötig für weiches Licht im Innenraum beim Laufen)."""
    with bpy.context.temp_override(**view3d_kontext()):
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
    return {"gebacken": True}
