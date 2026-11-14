"""Erdgeschoss innen: Parkett, Decke, Küche, Poly-Haven-Möbel, Leuchten, Eevee-Lichtsonden, Innenkamera."""
import glob
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import layout as L
from .architektur import fase
from .materialien import auswahl
from .util import bm_box, boxen_objekt, leere, material, mesh_aus_bmesh, neues_objekt, pfad, setze, view3d_kontext

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


def _moebel(rolle, name, ort, drehung, hoehe, haus, cache, log, oberkanten):
    """hoehe: False = auf dem Boden, True = an der Decke hängend, Zahl = so hoch über dem Fußboden,
    'auf:<Name>' = auf der Oberkante eines schon platzierten Möbels."""
    a = auswahl()
    if rolle not in a:
        log.append(f"{name}: Rolle {rolle} nicht gewählt – übersprungen")
        return
    aid = a[rolle][0] if isinstance(a[rolle], list) else a[rolle]
    if aid not in cache:
        cache[aid] = _modell_laden(aid)
    c = cache[aid]
    I = L.INNEN
    if hoehe is True:
        z = I["decke_z"] - c["hoehe"]
    elif hoehe is False or hoehe is None:
        z = I["boden_z"] + 0.02
    elif isinstance(hoehe, str) and hoehe.startswith("auf:"):
        z = oberkanten[hoehe[4:]]
    else:
        z = I["boden_z"] + float(hoehe)
    skala = I.get("skalierung", {}).get(name.rsplit("_", 1)[0], (1.0, 1.0, 1.0))
    oberkanten[name] = z + c["hoehe"] * skala[2]
    wurzel = neues_objekt(f"Moebel_{name}", None, S, eltern=haus)
    wurzel.location = (ort[0], ort[1], z)
    wurzel.rotation_euler = (0.0, 0.0, math.radians(drehung))
    wurzel.scale = skala
    for o, mw in c["teile"]:
        teil = o if not c["benutzt"] else o.copy()
        bpy.data.collections[S].objects.link(teil)
        teil.parent = wurzel
        teil.matrix_parent_inverse = Matrix.Identity(4)
        teil.matrix_basis = Matrix.Translation(-c["mitte_unten"]) @ mw
    c["benutzt"] = True
    log.append(f"{name}: {aid} ({c['hoehe']:.2f} m hoch)")


def _unterschrank(korpus, sockel, fronten, cx, cy, b, t, z, richtung):
    """Unterschrank mit zurückgesetztem Sockel, Einzeltüren (4 mm Fuge) und Griffmulde unter der Platte.
    richtung: +1 = Fronten zeigen nach +y, -1 = nach -y."""
    yf = cy + richtung * t / 2
    korpus.append(((b, t - 0.02, 0.76), (cx, cy - richtung * 0.01, z + 0.48)))
    sockel.append(((b - 0.02, t - 0.1, 0.1), (cx, cy - richtung * 0.05, z + 0.05)))
    n = max(1, round(b / 0.6))
    w = b / n
    for i in range(n):
        fronten.append(((w - 0.004, 0.019, 0.70), (cx - b / 2 + w * (i + 0.5), yf - richtung * 0.0095, z + 0.45)))


def _kueche(haus):
    from .fassade import _rohr
    I = L.INNEN
    z = I["boden_z"]
    k = I["kueche"]
    front = material("M_Kueche_Front", (0.05, 0.05, 0.055), 0.55)
    korpus_m = material("M_Kueche_Korpus", (0.025, 0.025, 0.027), 0.7)
    edelstahl = material("M_Edelstahl", (0.62, 0.62, 0.64), 0.22, 1.0)
    glas_schwarz = material("M_Glas_Schwarz", (0.008, 0.008, 0.01), 0.05)
    platte = bpy.data.materials["M_Arbeitsplatte"]
    korpus, sockel, fronten, glas = [], [], [], []

    (zx, zy), (zb, zt) = k["zeile"]
    _unterschrank(korpus, sockel, fronten, zx, zy, zb, zt, z, -1)
    (ix, iy), (ib, it) = k["insel"]
    _unterschrank(korpus, sockel, fronten, ix, iy, ib, it, z, +1)
    fronten.append(((ib, 0.019, 0.76), (ix, iy - (it / 2 + 0.0095), z + 0.48)))  # Rückseite der Insel
    # Hochschrank: links durchgehende Tür, rechts Unterschrank – Backofen – Oberschrank
    (hx, hy), (hb, ht) = k["hochschrank"]
    yf = hy - ht / 2
    korpus.append(((hb, ht - 0.02, 2.2), (hx, hy + 0.01, z + 1.2)))
    sockel.append(((hb - 0.02, ht - 0.1, 0.1), (hx, hy + 0.05, z + 0.05)))
    w = hb / 2
    fronten.append(((w - 0.004, 0.019, 2.18), (hx - w / 2, yf + 0.0095, z + 1.2)))
    fronten.append(((w - 0.004, 0.019, 0.80), (hx + w / 2, yf + 0.0095, z + 0.5)))
    fronten.append(((w - 0.004, 0.019, 0.76), (hx + w / 2, yf + 0.0095, z + 1.91)))
    glas.append(((w - 0.03, 0.025, 0.56), (hx + w / 2, yf + 0.012, z + 1.22)))       # Backofen
    glas.append(((0.78, 0.52, 0.006), (ix, iy + 0.05, z + 0.903)))                    # Kochfeld

    for name, teile, mat, breite in (("Innen_Kueche", korpus, korpus_m, 0.002), ("Innen_Kueche_Sockel", sockel, korpus_m, 0.0),
                                     ("Innen_Kueche_Fronten", fronten, front, 0.002), ("Innen_Kueche_Glas", glas, glas_schwarz, 0.002)):
        o = boxen_objekt(name, teile, S, haus, mat)
        if breite:
            fase(o, breite, 1)
    # Arbeitsplatten: Zeile mit kleinem Überstand, Insel mit Thekenüberstand zum Wohnbereich
    platten = [((zb + 0.02, zt + 0.03, 0.04), (zx, zy - 0.015, z + 0.88)),
               ((ib + 0.04, it + 0.34, 0.04), (ix, iy - 0.15, z + 0.88))]
    ap = boxen_objekt("Innen_Arbeitsplatte", platten, S, haus, platte)
    fase(ap, 0.003, 2)
    # Spüle: Ausschnitt in der Platte, Becken aus Edelstahl, Armatur
    sx = zx - zb / 2 + 0.9
    schneider = boxen_objekt("Innen_Spuele_Schneider", [((0.5, 0.4, 0.3), (sx, zy - 0.02, z + 0.88))], S, haus, edelstahl)
    schneider.hide_render = True
    schneider.display_type = "WIRE"
    schneider.hide_set(True)
    bo = ap.modifiers.new("Spuele", "BOOLEAN")
    bo.operation = "DIFFERENCE"
    bo.object = schneider
    bo.solver = "EXACT"
    ap.modifiers.move(len(ap.modifiers) - 1, 0)
    bm = bmesh.new()
    geo = bmesh.ops.create_cube(bm, size=1.0)
    for v in geo["verts"]:
        v.co = Vector((v.co.x * 0.49 + sx, v.co.y * 0.39 + zy - 0.02, v.co.z * 0.2 + z + 0.80))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.5], context="FACES")
    for a, e in ((Vector((sx, zy + 0.22, z + 0.9)), Vector((sx, zy + 0.22, z + 1.25))),
                 (Vector((sx, zy + 0.22, z + 1.25)), Vector((sx, zy + 0.02, z + 1.25))),
                 (Vector((sx, zy + 0.02, z + 1.25)), Vector((sx, zy + 0.02, z + 1.18)))):
        _rohr(bm, a, e, 0.012, 12)
    becken = mesh_aus_bmesh("Innen_Spuele", bm, S, haus, [edelstahl])
    fase(becken, 0.002, 1)


def _sockelleisten(haus):
    from .architektur import _quer, _wandpunkt
    from .fassade import _frei
    I = L.INNEN
    b, t = I["breite"], I["tiefe"]
    (zx, _), (zb, _) = I["kueche"]["zeile"]
    (hx, _), (hb, _) = I["kueche"]["hochschrank"]
    kueche_n = (-(hx + hb / 2), -(zx - zb / 2))  # Nordwand: versatz = -x
    bm = bmesh.new()
    for seite in ("S", "N", "O", "W"):
        laenge = b if seite in ("S", "N") else t
        gesperrt = [(v - br / 2, v + br / 2) for s, v, bru, br, h, _ in L.HAUS_EG_OEFFNUNGEN if s == seite and bru < 0.3]
        if seite == "N":
            gesperrt.append(kueche_n)
        for a, e in _frei((-laenge / 2, laenge / 2), gesperrt):
            p, n = _wandpunkt(seite, (a + e) / 2, b, t)
            bm_box(bm, _quer(n, e - a, 0.012, 0.07), p - n * 0.006 + Vector((0, 0, I["boden_z"] + 0.055)))
    o = mesh_aus_bmesh("Innen_Sockelleisten", bm, S, haus, [material("M_Sockelleiste", (0.82, 0.81, 0.79), 0.4)])
    fase(o, 0.002, 1)


def _teppich(haus):
    I = L.INNEN
    (x, y), (b, t) = I["teppich"]
    o = boxen_objekt("Innen_Teppich", [((b, t, 0.012), (x, y, I["boden_z"] + 0.026))], S, haus,
                     bpy.data.materials["M_Teppich"])
    fase(o, 0.004, 2)


def _vorhaenge(haus):
    """Leinenvorhänge in Falten (Sinuswelle), seitlich der Fenster, 10 cm vor der Innenwand."""
    from .architektur import _wandpunkt
    I = L.INNEN
    mat = bpy.data.materials["M_Vorhang"]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    z0, z1 = I["boden_z"] + 0.03, I["decke_z"] - 0.04
    for seite, versatz, breite in I["vorhaenge"]:
        p, n = _wandpunkt(seite, versatz, I["breite"], I["tiefe"])
        a = Vector((-n.y, n.x, 0.0))
        spalten = 28
        reihen = []
        for zz in (z0, z1):
            reihe = []
            for k in range(spalten + 1):
                s = (k / spalten - 0.5) * breite
                welle = 0.045 * math.sin(k / spalten * breite / 0.13 * 2 * math.pi)
                reihe.append(bm.verts.new(p - n * (0.1 + welle) + a * s + Vector((0, 0, zz))))
            reihen.append(reihe)
        for k in range(spalten):
            f = bm.faces.new((reihen[0][k], reihen[0][k + 1], reihen[1][k + 1], reihen[1][k]))
            for loop, (u, v) in zip(f.loops, ((k / spalten, 0), ((k + 1) / spalten, 0), ((k + 1) / spalten, 1), (k / spalten, 1))):
                loop[uv].uv = (u * breite, v * (z1 - z0))
    o = mesh_aus_bmesh("Innen_Vorhaenge", bm, S, haus, [mat])
    for poly in o.data.polygons:
        poly.use_smooth = True


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


def _kamera(haus, name="Kamera_Innen", schluessel="kamera"):
    K = L.INNEN[schluessel]
    alt = bpy.data.objects.get(name)
    if alt is not None:
        bpy.data.objects.remove(alt, do_unlink=True)
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = K["brennweite"]
    cam.clip_start = 0.05
    o = neues_objekt(name, cam, "07_Kameras")
    mw = haus.matrix_world
    ort, ziel = mw @ Vector(K["ort"]), mw @ Vector(K["ziel"])
    o.location = ort
    o.rotation_euler = (ziel - ort).to_track_quat("-Z", "Y").to_euler()


def baue():
    log = []
    leere(S)
    # verwaiste Möbel-Materialien/-Bilder früherer Läufe entfernen (sonst wachsen Datei und GPU-Speicher)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    haus = bpy.data.objects["Haus"]
    I = L.INNEN
    boxen_objekt("Innen_Boden", [((I["breite"], I["tiefe"], 0.02), (0.0, 0.0, I["boden_z"] + 0.01))], S, haus,
                 bpy.data.materials["M_Parkett"])
    boxen_objekt("Innen_Decke", [((I["breite"], I["tiefe"], 0.01), (0.0, 0.0, I["decke_z"] - 0.006))], S, haus,
                 material("M_Decke", (0.82, 0.81, 0.78), 0.9))
    _kueche(haus)
    _sockelleisten(haus)
    cache, oberkanten = {}, {}
    for rolle, name, ort, drehung, hoehe in I["moebel"]:
        _moebel(rolle, name, ort, drehung, hoehe, haus, cache, log, oberkanten)
    _teppich(haus)
    _vorhaenge(haus)
    _lichter(haus)
    _lichtsonden(haus, log)
    _kamera(haus)
    _kamera(haus, "Kamera_Innen_2", "kamera_2")
    return {"log": log, "objekte": len(bpy.data.collections[S].all_objects)}


def sonden_backen():
    """Eevee-Lichtsonden backen (nötig für weiches Licht im Innenraum beim Laufen)."""
    with bpy.context.temp_override(**view3d_kontext()):
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
    return {"gebacken": True}
