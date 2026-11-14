"""Hofplatten, Weg, Carport-Boden, Terrasse, Trittplatten, Feuerschale, Sessel, Poller."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import layout as L
from .util import box, boxen_objekt, leere, material, mesh_aus_bmesh, neues_objekt

S = "04_Hardscape"


def mats():
    return {
        "platten": material("M_Polygonalplatten", (0.12, 0.12, 0.12), 0.7),
        "weg": material("M_Weg_Platten", (0.18, 0.18, 0.18), 0.7),
        "tritt": material("M_Trittplatten", (0.35, 0.34, 0.32), 0.8),
        "deck": material("M_Holzdeck", (0.35, 0.22, 0.12), 0.6),
        "stahl": material("M_Stahl_Schwarz", (0.02, 0.02, 0.02), 0.5),
        "sessel": material("M_Sessel_Gruen", (0.05, 0.08, 0.035), 0.45),
        "kohle": material("M_Holz_Verkohlt", (0.04, 0.03, 0.025), 0.9),
    }


def hof_platten(m):
    r = L.HOF["radius"]
    bm = bmesh.new()
    seg = int(2 * r / 0.05)
    bmesh.ops.create_grid(bm, x_segments=seg, y_segments=seg, size=r)
    k = r / max(abs(v.co.x) for v in bm.verts)  # auf exakt ±r normieren (Größensemantik versionsunabhängig)
    for v in bm.verts:
        v.co.x *= k
        v.co.y *= k
    def grenze(v):
        w = math.atan2(v.co.y, v.co.x)
        return r * (1 + 0.03 * math.sin(5 * w) + 0.02 * math.sin(11 * w + 1.3))

    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.xy.length > grenze(v)], context="VERTS")
    for v in [v for v in bm.verts if v.is_boundary]:  # Treppenkante glätten: Randpunkte auf die Kontur ziehen
        k = grenze(v) / max(v.co.xy.length, 1e-6)
        v.co.x *= k
        v.co.y *= k
    o = mesh_aus_bmesh("Hof_Platten", bm, S, mats=[m["platten"]])
    o.location = (*L.HOF["mitte"], 0.02)
    s = o.modifiers.new("Dicke", "SOLIDIFY")
    s.thickness = 0.06
    s.offset = -1.0


def weg_und_boden(m):
    x0, y0, x1, y1 = L.WEG_FLUEGEL
    box("Weg_Fluegel", (x1 - x0, y1 - y0, 0.06), ((x0 + x1) / 2, (y0 + y1) / 2, -0.04), S, mat=m["weg"])
    C = L.CARPORT
    box("Carport_Boden", (C["breite"], C["tiefe"], 0.06), (*C["mitte"], -0.04), S, mat=m["weg"])
    T = L.TERRASSE
    box("Terrasse", T["groesse"], (*T["mitte_lokal"], 0.0), S, eltern=bpy.data.objects["Haus"], mat=m["deck"])


def trittplatten(m):
    rnd = random.Random(7)
    T = L.TRITTPLATTEN
    a, e = Vector(T["start"]), Vector(T["ende"])
    d = e - a
    winkel = math.atan2(d.y, d.x) + math.pi / 2
    sx, sy, sz = T["groesse"]
    for i in range(T["anzahl"]):
        p = a + d * (i / (T["anzahl"] - 1)) + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.08, 0.08)))
        o = box(f"Trittplatte_{i + 1:02d}", (sx * rnd.uniform(0.9, 1.1), sy * rnd.uniform(0.9, 1.15), sz),
                (p.x, p.y, -0.035), S, rot_z=winkel + rnd.uniform(-0.25, 0.25), mat=m["tritt"])
        bev = o.modifiers.new("Fase", "BEVEL")
        bev.width = 0.012
        bev.segments = 2


def feuerschale(m):
    cx, cy = L.HOF["mitte"]
    bm = bmesh.new()
    profil = [(0.0, 0.30), (0.30, 0.31), (0.42, 0.36), (0.49, 0.44), (0.50, 0.46)]
    vs = [bm.verts.new((x, 0.0, z)) for x, z in profil]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=64, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    schale = mesh_aus_bmesh("Feuerschale", bm, S, mats=[m["stahl"]])
    schale.location = (cx, cy, 0.02)
    sol = schale.modifiers.new("Dicke", "SOLIDIFY")
    sol.thickness = 0.008
    sub = schale.modifiers.new("Glatt", "SUBSURF")
    sub.levels, sub.render_levels = 1, 2

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.18, radius2=0.16, depth=0.30)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.15))
    fuss = mesh_aus_bmesh("Feuerschale_Fuss", bm, S, mats=[m["stahl"]])
    fuss.location = (cx, cy, 0.02)

    bm = bmesh.new()
    for i, (w, neig) in enumerate([(0.2, 0.15), (2.2, 0.1), (4.1, 0.2)]):
        geo = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.05, radius2=0.045, depth=0.5)
        rot = Matrix.Rotation(w, 3, "Z") @ Matrix.Rotation(math.pi / 2 - neig, 3, "Y")
        bmesh.ops.rotate(bm, verts=geo["verts"], cent=(0, 0, 0), matrix=rot)
        bmesh.ops.translate(bm, verts=geo["verts"], vec=(0, 0, 0.40 + 0.04 * i))
    holz = mesh_aus_bmesh("Feuerschale_Holz", bm, S, mats=[m["kohle"]])
    holz.location = (cx, cy, 0.02)


def sessel(name, ort, rot_z, m):
    wurzel = neues_objekt(name, None, S)
    wurzel.location = (ort[0], ort[1], 0.02)
    wurzel.rotation_euler = (0.0, 0.0, rot_z)
    cu = bpy.data.curves.new(f"{name}_Rahmen", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.012
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    zuege = [[(sx, -0.38, 0.0), (sx, -0.36, 0.60), (sx, 0.30, 0.60), (sx, 0.40, 0.0)] for sx in (-0.36, 0.36)]
    zuege += [[(-0.36, -0.30, 0.34), (0.36, -0.30, 0.34)], [(-0.36, 0.30, 0.30), (0.36, 0.30, 0.30)]]
    for punkte in zuege:
        sp = cu.splines.new("POLY")
        sp.points.add(len(punkte) - 1)
        for pt, co in zip(sp.points, punkte):
            pt.co = (*co, 1.0)
    cu.materials.append(m["sessel"])
    neues_objekt(f"{name}_Rahmen", cu, S, wurzel)
    latten = []
    n = 13
    for k in range(n):
        x = -0.33 + k * 0.66 / (n - 1)
        latten.append(((0.034, 0.60, 0.008), (x, -0.03, 0.37), (-0.10, 0.0, 0.0)))  # Sitz
        latten.append(((0.034, 0.008, 0.55), (x, 0.36, 0.62), (-0.30, 0.0, 0.0)))   # Rücken
    boxen_objekt(f"{name}_Latten", latten, S, wurzel, m["sessel"])
    return wurzel


def alle_sessel(m):
    rnd = random.Random(5)
    c = Vector(L.HOF["mitte"])
    for i, w in enumerate(L.SESSEL_WINKEL):
        p = c + Vector((math.cos(math.radians(w)), math.sin(math.radians(w)))) * L.SESSEL_RADIUS
        d = c - p
        sessel(f"Sessel_{i + 1}", p, math.atan2(d.x, -d.y) + rnd.uniform(-0.17, 0.17), m)


def poller(m):
    for i, (x, y) in enumerate(L.POLLER):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.06, radius2=0.06, depth=0.7)
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.35))
        o = mesh_aus_bmesh(f"Poller_{i + 1}", bm, S, mats=[m["stahl"]])
        o.location = (x, y, 0.0)


def baue():
    leere(S)
    m = mats()
    hof_platten(m)
    weg_und_boden(m)
    trittplatten(m)
    feuerschale(m)
    alle_sessel(m)
    poller(m)
    return {"objekte": len(bpy.data.collections[S].all_objects)}
