"""Haus, Vordach, Seitenflügel und Carport als Graumodell mit echten Öffnungen."""
import math

import bmesh
import bpy
from mathutils import Vector

from . import layout as L
from .util import box, boxen_objekt, collection, leere, material, mesh_aus_bmesh, neues_objekt

S = "02_Architektur"


def glas_material():
    m = bpy.data.materials.get("M_Glas")
    if m is None:
        m = bpy.data.materials.new("M_Glas")
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.9, 0.95, 0.95, 1.0)
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.02
        b.inputs["IOR"].default_value = 1.5
        if hasattr(m, "use_raytrace_refraction"):
            m.use_raytrace_refraction = True
    return m


def mats():
    return {
        "putz": material("M_Putz", (0.78, 0.77, 0.74), 0.85),
        "holz": material("M_Holzfassade", (0.30, 0.17, 0.09), 0.7),
        "blech": material("M_Dachblech", (0.06, 0.06, 0.065), 0.45, 0.6),
        "traufe": material("M_Traufe", (0.08, 0.06, 0.05), 0.7),
        "ziegel": material("M_Dachziegel", (0.12, 0.12, 0.13), 0.6),
        "rahmen": material("M_Rahmen", (0.03, 0.03, 0.035), 0.4),
        "stahl": material("M_Stahl_Schwarz", (0.02, 0.02, 0.02), 0.5),
        "tuer": material("M_Haustuer", (0.12, 0.07, 0.04), 0.5),
        "glas": glas_material(),
        "holz_dunkel": material("M_Fassade_Dunkel", (0.02, 0.017, 0.014), 0.85),  # sichtbar in den Brettfugen
        "innenwand": material("M_Innenwand", (0.80, 0.79, 0.76), 0.85),
    }


def fase(o, breite=0.01, segmente=2):
    """Leicht gerundete Kanten – messerscharfe Kanten verraten CG sofort."""
    m = o.modifiers.new("Fase", "BEVEL")
    m.width = breite
    m.segments = segmente
    m.limit_method = "ANGLE"
    m.use_clamp_overlap = True
    if hasattr(m, "harden_normals"):
        m.harden_normals = True
    return m


def _anwenden(o):
    """Modifier (Booleans) fest anwenden: ersetzt die Mesh-Daten durch das ausgewertete Ergebnis."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    neu = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    alt = o.data
    o.modifiers.clear()
    o.data = neu
    if alt.users == 0:
        bpy.data.meshes.remove(alt)


def _innen_faerben(o, breite, tiefe, wand, z_unten, z_oben, mat):
    """Flächen im Innenraum bekommen das Innenwand-Material (glatter weißer Anstrich)."""
    me = o.data
    me.materials.append(mat)
    idx = len(me.materials) - 1
    # alles, was nicht auf der Außenfläche liegt (Innenwände, Fensterlaibungen), bekommt den Innenanstrich
    gx, gy = breite / 2 - 0.01, tiefe / 2 - 0.01
    for p in me.polygons:
        c = p.center
        if abs(c.x) <= gx and abs(c.y) <= gy and z_unten - 0.005 <= c.z <= z_oben + 0.005:
            p.material_index = idx


def _strahl_schnitt(p, d, a, b):
    """Schnitt Strahl p + d·s mit Strecke a–b (2D); liefert s oder None."""
    e = b - a
    nenner = d.x * e.y - d.y * e.x
    if abs(nenner) < 1e-9:
        return None
    q = a - p
    s = (q.x * e.y - q.y * e.x) / nenner
    r = (q.x * d.y - q.y * d.x) / nenner
    return s if -1e-6 <= r <= 1 + 1e-6 else None


def _ebene_z(pts, x, y):
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    return pts[0].z - (n.x * (x - pts[0].x) + n.y * (y - pts[0].y)) / n.z


def _falze(bm, flaechen, abstand=0.5, breite=0.025, hoehe=0.03):
    """Stehfalze: schmale Leisten von der Traufe die Dachfläche hinauf bis zu First/Grat."""
    for pts in flaechen:  # pts[0], pts[1] = Traufkante
        e0, e1 = pts[0], pts[1]
        u = e1 - e0
        laenge = u.length
        u.normalize()
        mitte = sum(pts, Vector()) / len(pts)
        w = Vector((-u.y, u.x, 0.0))
        if w.dot(mitte - e0) < 0:
            w = -w
        n = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized()
        if n.z < 0:
            n = -n
        kanten = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(1, len(pts))]
        t = (laenge - abstand * int(laenge / abstand)) / 2 + abstand / 2
        while t < laenge - 0.05:
            s0 = e0 + u * t
            treffer = [s for a, b in kanten
                       if (s := _strahl_schnitt(s0.xy, w.xy, a.xy, b.xy)) is not None and s > 1e-4]
            if treffer and min(treffer) > 0.1:
                ende = s0 + w * min(treffer)
                ende.z = _ebene_z(pts, ende.x, ende.y)
                h = breite / 2
                unten = [s0 - u * h, s0 + u * h, ende + u * h, ende - u * h]
                oben = [p + n * hoehe for p in unten]
                vs = [bm.verts.new(p) for p in unten + oben]
                for f in ((4, 5, 6, 7), (0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                    bm.faces.new([vs[i] for i in f]).material_index = 0
            t += abstand


def walmdach(name, breite, tiefe, ueberstand, neigung_grad, z, eltern, mat_dach, mat_traufe,
             mitte=(0.0, 0.0), dicke=0.18, falze=False):
    """Geschlossenes Walmdach inkl. Traufkante; Unterseite = Dachuntersicht (Material 1)."""
    b, t = breite + 2 * ueberstand, tiefe + 2 * ueberstand
    h = min(b, t) / 2 * math.tan(math.radians(neigung_grad))
    bm = bmesh.new()
    oben = [bm.verts.new(p) for p in [(-b / 2, -t / 2, 0), (b / 2, -t / 2, 0), (b / 2, t / 2, 0), (-b / 2, t / 2, 0)]]
    unten = [bm.verts.new((v.co.x, v.co.y, -dicke)) for v in oben]
    if b >= t:
        r = (b - t) / 2
        r0, r1 = bm.verts.new((-r, 0, h)), bm.verts.new((r, 0, h))
        dach = [(oben[0], oben[1], r1, r0), (oben[1], oben[2], r1), (oben[2], oben[3], r0, r1), (oben[3], oben[0], r0)]
    else:
        r = (t - b) / 2
        r0, r1 = bm.verts.new((0, -r, h)), bm.verts.new((0, r, h))
        dach = [(oben[0], oben[1], r0), (oben[1], oben[2], r1, r0), (oben[2], oben[3], r1), (oben[3], oben[0], r0, r1)]
    for f in dach:
        bm.faces.new(f).material_index = 0
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((unten[i], unten[j], oben[j], oben[i])).material_index = 1
    bm.faces.new(list(reversed(unten))).material_index = 1
    if falze:
        _falze(bm, [[v.co.copy() for v in f] for f in dach])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = mesh_aus_bmesh(name, bm, S, eltern, [mat_dach, mat_traufe])
    o.location = (mitte[0], mitte[1], z)
    fase(o, 0.008)
    return o


def _wandpunkt(seite, versatz, breite, tiefe):
    if seite == "S":
        return Vector((versatz, -tiefe / 2, 0)), Vector((0, -1, 0))
    if seite == "N":
        return Vector((-versatz, tiefe / 2, 0)), Vector((0, 1, 0))
    if seite == "O":
        return Vector((breite / 2, versatz, 0)), Vector((1, 0, 0))
    if seite == "W":
        return Vector((-breite / 2, -versatz, 0)), Vector((-1, 0, 0))
    raise ValueError(seite)


def _quer(normal, laengs, tief, hoch):
    """Box-Größe: 'laengs' entlang der Wand, 'tief' entlang der Wandnormalen."""
    return (tief, laengs, hoch) if abs(normal.x) > 0.5 else (laengs, tief, hoch)


def _als_schneider(o):
    o.display_type = "WIRE"
    o.hide_render = True
    o.hide_set(True)


def _korpus(name, wurzel, breite, tiefe, z0, hoehe, wand, boden, decke, mat, schneider):
    """Hohler Quader; alle Objekte in der Schneider-Collection werden per Boolean abgezogen."""
    o = box(name, (breite, tiefe, hoehe), (0, 0, z0), S, eltern=wurzel, mat=mat)
    s = box(f"Schneider_{name}_Innen", (breite - 2 * wand, tiefe - 2 * wand, hoehe - boden - decke),
            (0, 0, z0 + boden), schneider.name, eltern=wurzel)
    _als_schneider(s)
    m = o.modifiers.new("Oeffnungen", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.operand_type = "COLLECTION"
    m.collection = schneider
    m.solver = "EXACT"
    return o


def _oeffnung(name, wurzel, schneider, seite, versatz, z_unten, b, h, art, breite, tiefe, wand, m):
    p, n = _wandpunkt(seite, versatz, breite, tiefe)
    zc = z_unten + h / 2
    s = box(f"Schneider_{name}", _quer(n, b, wand * 3, h), (p.x, p.y, zc), schneider.name, eltern=wurzel, boden=False)
    _als_schneider(s)
    a = Vector((-n.y, n.x, 0))          # Richtung entlang der Wand
    mitte = p - n * 0.10                # Rahmenebene 10 cm hinter der Außenfläche
    rb, rt = 0.06, 0.07
    teile = [
        (_quer(n, b, rt, rb), mitte + Vector((0, 0, zc + h / 2 - rb / 2))),
        (_quer(n, rb, rt, h), mitte + a * (b / 2 - rb / 2) + Vector((0, 0, zc))),
        (_quer(n, rb, rt, h), mitte - a * (b / 2 - rb / 2) + Vector((0, 0, zc))),
    ]
    if art == "fenster":
        teile.append((_quer(n, b, rt, rb), mitte + Vector((0, 0, zc - h / 2 + rb / 2))))
    if art == "tuer_offen":
        teile.append((_quer(n, rb, rt, h), mitte + Vector((0, 0, zc))))
    fase(boxen_objekt(f"Rahmen_{name}", teile, S, wurzel, m["rahmen"]), 0.004)
    if art == "fenster":
        boxen_objekt(f"Glas_{name}", [(_quer(n, b - 2 * rb, 0.02, h - 2 * rb), mitte + Vector((0, 0, zc)))],
                     S, wurzel, m["glas"])
    elif art == "tuer_offen":
        halb = (b - 3 * rb) / 2
        boxen_objekt(f"Glas_{name}", [(_quer(n, halb, 0.02, h - rb), mitte + a * (b / 4) + Vector((0, 0, zc - rb / 2)))],
                     S, wurzel, m["glas"])
    elif art == "tuer":
        boxen_objekt(f"Tuerblatt_{name}", [(_quer(n, b - 2 * rb, 0.05, h - rb), mitte + Vector((0, 0, zc - rb / 2)))],
                     S, wurzel, m["tuer"])


def _oeffnungen(praefix, liste, z_boden, wurzel, schneider, breite, tiefe, wand, m):
    for i, (seite, versatz, bruestung, b, h, art) in enumerate(liste):
        _oeffnung(f"{praefix}_{i + 1:02d}", wurzel, schneider, seite, versatz, z_boden + bruestung,
                  b, h, art, breite, tiefe, wand, m)


def haus(m):
    H = L.HAUS
    wurzel = neues_objekt("Haus", None, S)
    wurzel.location = (*H["mitte"], 0.0)
    wurzel.rotation_euler = (0.0, 0.0, math.radians(H["rot_grad"]))
    sch_eg = collection("Schneider_Haus_EG", S)
    sch_og = collection("Schneider_Haus_OG", S)
    b, t, w = H["breite"], H["tiefe"], H["wand"]
    eg = _korpus("Haus_EG", wurzel, b, t, 0.0, H["eg_h"], w, H["boden"], H["decke"], m["putz"], sch_eg)
    og = _korpus("Haus_OG", wurzel, b, t, H["eg_h"], H["og_h"], w, 0.0, H["decke"], m["holz_dunkel"], sch_og)
    _oeffnungen("EG", L.HAUS_EG_OEFFNUNGEN, H["boden"], wurzel, sch_eg, b, t, w, m)
    _oeffnungen("OG", L.HAUS_OG_OEFFNUNGEN, H["eg_h"], wurzel, sch_og, b, t, w, m)
    for korpus in (eg, og):
        _anwenden(korpus)
        fase(korpus, 0.012)
    _innen_faerben(eg, b, t, w, H["boden"], H["eg_h"] - H["decke"], m["innenwand"])
    walmdach("Haus_Dach", b, t, H["dach_ueberstand"], H["dach_neigung"], H["eg_h"] + H["og_h"],
             wurzel, m["blech"], m["traufe"], falze=True)
    V = L.VORDACH
    walmdach("Vordach_Dach", V["breite"], V["tiefe"], V["ueberstand"], V["neigung"], V["hoehe"],
             wurzel, m["blech"], m["traufe"], mitte=V["mitte_lokal"], dicke=0.15, falze=True)
    fase(boxen_objekt("Vordach_Stuetzen", [((0.3, 0.3, V["hoehe"]), (x, y, V["hoehe"] / 2))
                                         for x, y in V["stuetzen_lokal"]], S, wurzel, m["putz"]), 0.01)
    return wurzel


def fluegel(m):
    F = L.FLUEGEL
    b, t = F["xmax"] - F["xmin"], F["ymax"] - F["ymin"]
    wurzel = neues_objekt("Fluegel_Wurzel", None, S)
    wurzel.location = ((F["xmin"] + F["xmax"]) / 2, (F["ymin"] + F["ymax"]) / 2, 0.0)
    sch = collection("Schneider_Fluegel", S)
    korpus = _korpus("Fluegel", wurzel, b, t, 0.0, F["h"], F["wand"], 0.15, 0.25, m["putz"], sch)
    _oeffnungen("FL", F["oeffnungen"], 0.15, wurzel, sch, b, t, F["wand"], m)
    _anwenden(korpus)
    fase(korpus, 0.012)
    walmdach("Fluegel_Dach", b, t, F["ueberstand"], F["neigung"], F["h"], wurzel, m["blech"], m["traufe"],
             dicke=0.3, falze=True)


def carport(m):
    C = L.CARPORT
    b, t, h = C["breite"], C["tiefe"], C["hoehe"]
    wurzel = neues_objekt("Carport", None, S)
    wurzel.location = (*C["mitte"], 0.0)
    boxen_objekt("Carport_Stuetzen", [((0.15, 0.15, h), (sx * (b / 2 - 0.2), sy * (t / 2 - 0.2), h / 2))
                                      for sx in (-1, 1) for sy in (-1, 1)], S, wurzel, m["stahl"])
    balken = [((b, 0.12, 0.3), (0, sy * (t / 2 - 0.2), h - 0.15)) for sy in (-1, 1)]
    balken += [((0.12, t, 0.3), (sx * (b / 2 - 0.2), 0, h - 0.15)) for sx in (-1, 1)]
    boxen_objekt("Carport_Rahmen", balken, S, wurzel, m["traufe"])
    walmdach("Carport_Dach", b, t, C["ueberstand"], C["neigung"], h, wurzel, m["ziegel"], m["traufe"])


def baue():
    leere(S)
    m = mats()
    haus(m)
    fluegel(m)
    carport(m)
    return {"objekte": len(bpy.data.collections[S].all_objects)}
