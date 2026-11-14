"""Umgebung: Wiese um das Grundstück, Hecken an der Grenze, Baumkulisse."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import gn
from . import layout as L
from .pflanzen import pflanzen_material
from .util import leere, material, mesh_aus_bmesh


def wiese():
    """Ring aus vier Rechtecken zwischen Grundstück und Außenrand, mit lockerem Gras."""
    leere("01b_Wiese")
    x0, y0, x1, y1 = L.GRUNDSTUECK
    mx, my = L.WIESE["mitte"]
    h = L.WIESE["halbe_breite"]
    X0, Y0, X1, Y1 = mx - h, my - h, mx + h, my + h
    bm = bmesh.new()
    for a, b in (((X0, Y0), (X1, y0)), ((X0, y1), (X1, Y1)), ((X0, y0), (x0, y1)), ((x1, y0), (X1, y1))):
        bm.faces.new([bm.verts.new((a[0], a[1], 0)), bm.verts.new((b[0], a[1], 0)),
                      bm.verts.new((b[0], b[1], 0)), bm.verts.new((a[0], b[1], 0))])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    o = mesh_aus_bmesh("Wiese", bm, "01b_Wiese", mats=[material("M_Erde")])
    gn.anwenden(o, "Wiese", "Bib_Halme", "Maske_Beet", dichte_lauf=0.6, dichte_schoen=40, abstand=0.06,
                skala=(0.9, 1.6), neigung=0.2, seed=7, basis=True, bibliothek_lauf="Bib_Halme_Lauf")
    return {"wiese": o.name}


def heckenblatt_bibliothek():
    leere("Bib_Heckenblatt")
    m = pflanzen_material("M_Heckenblatt", [(0.0, (0.02, 0.05, 0.012)), (0.6, (0.04, 0.09, 0.02)),
                                            (1.0, (0.08, 0.13, 0.03))], durchscheinend=0.3, form="birke")
    rnd = random.Random(31)
    for k in range(6):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        for _ in range(14):
            c = Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), rnd.uniform(-0.05, 0.05)))
            l = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 1))).normalized()
            w = l.cross(Vector((0.3, 0.2, 1.0))).normalized()
            b, hh = rnd.uniform(0.035, 0.05), rnd.uniform(0.05, 0.07)
            f = bm.faces.new([bm.verts.new(p) for p in (c - w * b / 2, c + w * b / 2,
                                                         c + l * hh + w * b / 2, c + l * hh - w * b / 2)])
            for loop, koord in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uv].uv = koord
        mesh_aus_bmesh(f"Heckenblaetter_{k}", bm, "Bib_Heckenblatt", mats=[m])


def heckenblatt_bibliothek_lauf():
    """Leichte Blattgruppen ohne Alpha-Ausschnitt (deckend, größer) für den Modus Laufen."""
    leere("Bib_Heckenblatt_Lauf")
    m = pflanzen_material("M_Heckenblatt_Lauf", [(0.0, (0.02, 0.05, 0.012)), (0.6, (0.035, 0.08, 0.018)),
                                                 (1.0, (0.06, 0.11, 0.025))], durchscheinend=0.2)
    rnd = random.Random(37)
    for k in range(4):
        bm = bmesh.new()
        for _ in range(30):  # großer Blattballen, damit wenige Instanzen reichen
            c = Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(-0.15, 0.15)))
            l = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 1))).normalized()
            w = l.cross(Vector((0.3, 0.2, 1.0))).normalized()
            b, hh = rnd.uniform(0.09, 0.12), rnd.uniform(0.1, 0.13)
            bm.faces.new([bm.verts.new(p) for p in (c - w * b / 2, c + w * b / 2, c + l * hh + w * b * 0.3,
                                                     c + l * hh - w * b * 0.3)])
        mesh_aus_bmesh(f"Heckenblaetter_Lauf_{k}", bm, "Bib_Heckenblatt_Lauf", mats=[m])


def hecken():
    leere("01c_Heckenkern")
    leere("05g_Hecke")
    heckenblatt_bibliothek()
    heckenblatt_bibliothek_lauf()
    kern_mat = material("M_Hecke_Kern", (0.01, 0.025, 0.008), 0.9)
    hoehe, tiefe = L.HECKE_MASS["hoehe"], L.HECKE_MASS["tiefe"]
    for i, (a, b) in enumerate(L.HECKEN):
        a, b = Vector(a), Vector(b)
        laenge = (b - a).length
        bm = bmesh.new()
        geo = bmesh.ops.create_cube(bm, size=1.0)
        for v in geo["verts"]:
            v.co = Vector((v.co.x * laenge, v.co.y * tiefe, (v.co.z + 0.5) * hoehe))
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
        for v in bm.verts:  # leicht unregelmäßige Oberfläche
            v.co += Vector((0, math.sin(v.co.x * 1.7) * 0.05, math.sin(v.co.x * 0.9 + v.co.z) * 0.05))
        kern = mesh_aus_bmesh(f"Hecke_{i + 1}_Kern", bm, "01c_Heckenkern", mats=[kern_mat])
        kern.location = ((a.x + b.x) / 2, (a.y + b.y) / 2, 0.0)
        kern.rotation_euler = (0.0, 0.0, math.atan2(b.y - a.y, b.x - a.x))
        laub = bpy.data.objects.new(f"Hecke_{i + 1}_Laub", kern.data)
        bpy.data.collections["05g_Hecke"].objects.link(laub)
        laub.location, laub.rotation_euler = kern.location, kern.rotation_euler
        gn.anwenden(laub, "Streuen", "Bib_Heckenblatt", "Maske_Beet", dichte_lauf=5, dichte_schoen=500,
                    abstand=0.03, skala=(0.8, 1.3), neigung=3.14, seed=40 + i, basis=False,
                    bibliothek_lauf="Bib_Heckenblatt_Lauf")
    return {"hecken": len(L.HECKEN)}


def baumkulisse():
    """Vier Vorlagebäume, als verknüpfte Kopien (geteilte Mesh-Daten) im Ring um das Grundstück verteilt."""
    from .baeume import baum
    leere("05f_Kulisse")
    K = L.KULISSE
    mats = {"birke": (bpy.data.materials["M_Blatt_Birke"], bpy.data.materials["M_Rinde_Birke"]),
            "ahorn": (bpy.data.materials["M_Blatt_Ahorn"], bpy.data.materials["M_Rinde_Ahorn"])}
    vorlagen = []
    for name, art, hoehe, seed in K["vorlagen"]:
        laub_m, rinde_m = mats[art]
        baum(name, art, (0.0, 0.0), hoehe, seed, laub_m, rinde_m, blatt_faktor=K["blatt_faktor"], sammlung="05f_Kulisse")
        vorlagen.append(bpy.data.objects[name])
    rnd = random.Random(K["seed"])
    mx, my = K["mitte"]
    platziert = 0
    for i in range(K["anzahl"]):
        w = 2 * math.pi * (i + rnd.uniform(-0.35, 0.35)) / K["anzahl"]
        r = rnd.uniform(K["r_min"], K["r_max"])
        ort = (mx + math.cos(w) * r, my + math.sin(w) * r, 0.0)
        v = vorlagen[i % len(vorlagen)]
        if i < len(vorlagen):
            o = v
        else:
            o = v.copy()  # teilt die Mesh-Daten
            bpy.data.collections["05f_Kulisse"].objects.link(o)
            laub = bpy.data.objects[f"{v.name}_Laub"].copy()
            bpy.data.collections["05f_Kulisse"].objects.link(laub)
            laub.parent = o
            o.name = f"Kulisse_{i:02d}"
            laub.name = f"Kulisse_{i:02d}_Laub"
        o.location = ort
        o.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
        s = o.scale.x * rnd.uniform(0.85, 1.15)
        o.scale = (s, s, s)
        platziert += 1
    return {"kulissenbaeume": platziert}
