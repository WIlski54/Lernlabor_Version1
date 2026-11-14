"""Fassadendetails: echte Holzbretter mit Fugen, Dachrinnen und Fallrohre, Sockel, Fensterbänke, Außenleuchten.
Läuft nach architektur.baue() (die Objekte hängen an Haus/Flügel/Carport)."""
import math

import bmesh
import bpy
from mathutils import Vector

from . import layout as L
from .architektur import _quer, _wandpunkt, fase
from .util import bm_box, leere, material, mesh_aus_bmesh

S = "02b_Fassade"


def _rohr(bm, a, b, r, seg=12):
    """Rohr (Zylinder mit Deckeln) von a nach b."""
    d = (b - a).normalized()
    hilf = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(hilf).normalized()
    v = d.cross(u)
    ringe = []
    for p in (a, b):
        ringe.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for k in range(seg):
        j = (k + 1) % seg
        bm.faces.new((ringe[0][k], ringe[0][j], ringe[1][j], ringe[1][k]))
    bm.faces.new(list(reversed(ringe[0])))
    bm.faces.new(ringe[1])


def _frei(intervall, gesperrt):
    """Zieht gesperrte Intervalle von [a, b] ab; liefert die freien Teilintervalle."""
    teile = [intervall]
    for s0, s1 in gesperrt:
        neu = []
        for a, b in teile:
            if s1 <= a or s0 >= b:
                neu.append((a, b))
                continue
            if s0 > a:
                neu.append((a, s0))
            if s1 < b:
                neu.append((s1, b))
        teile = neu
    return [(a, b) for a, b in teile if b - a > 0.02]


def _seitenlaenge(seite, breite, tiefe):
    return breite if seite in ("S", "N") else tiefe


def bretter(eltern, breite, tiefe, z0, z1, oeffnungen, z_boden, mat):
    """Senkrechte Boden-Deckel-Schalung (12 cm Bretter, 12 mm Fuge) rund um einen Baukörper, Fenster ausgespart."""
    bm = bmesh.new()
    bb, dicke, fuge = 0.12, 0.022, 0.012
    for seite in ("S", "N", "O", "W"):
        laenge = _seitenlaenge(seite, breite, tiefe)
        seite_oeff = [(v, b, z_boden + br, z_boden + br + h) for s, v, br, b, h, _ in oeffnungen if s == seite]
        s = -laenge / 2
        while s < laenge / 2 - 0.01:
            s_ende = min(s + bb, laenge / 2)
            mitte_s = (s + s_ende) / 2
            gesperrt = [(zu, zo) for v, b, zu, zo in seite_oeff if v - b / 2 < s_ende and v + b / 2 > s]
            for za, ze in _frei((z0, z1), gesperrt):
                p, n = _wandpunkt(seite, mitte_s, breite, tiefe)
                mitte = p + n * (dicke / 2 + 0.004) + Vector((0, 0, (za + ze) / 2))
                bm_box(bm, _quer(n, s_ende - s - 0.002, dicke, ze - za), mitte)
            s += bb + fuge
    o = mesh_aus_bmesh(f"{eltern.name}_Schalung", bm, S, eltern, [mat])
    fase(o, 0.002, 1)
    return o


def rinnen(name, eltern, breite, tiefe, ueberstand, z, mat, mitte=(0.0, 0.0), nur_vorne=False, fallrohre=()):
    """Dachrinnen entlang der Traufen und Fallrohre (je (x, y) an der Wand, mit Verbindung zur Rinne)."""
    bm = bmesh.new()
    b2, t2 = breite / 2 + ueberstand + 0.06, tiefe / 2 + ueberstand + 0.06
    mx, my = mitte
    zr = z - 0.07
    ecken = [Vector((mx - b2, my - t2, zr)), Vector((mx + b2, my - t2, zr)),
             Vector((mx + b2, my + t2, zr)), Vector((mx - b2, my + t2, zr))]
    kanten = [(0, 1)] if nur_vorne else [(0, 1), (1, 2), (2, 3), (3, 0)]
    for i, j in kanten:
        _rohr(bm, ecken[i], ecken[j], 0.055, 10)
    for x, y, rx, ry in fallrohre:  # (x, y) an der Wand; (rx, ry) Punkt an der Rinne
        oben = Vector((x, y, zr - 0.35))
        _rohr(bm, Vector((x, y, 0.02)), oben, 0.045)
        _rohr(bm, Vector((rx, ry, zr)), oben, 0.04)
    return mesh_aus_bmesh(name, bm, S, eltern, [mat])


def sockel(eltern, breite, tiefe, oeffnungen, z_boden, hoehe, mat):
    bm = bmesh.new()
    for seite in ("S", "N", "O", "W"):
        laenge = _seitenlaenge(seite, breite, tiefe)
        tueren = [(v - b / 2, v + b / 2) for s, v, br, b, h, _ in oeffnungen if s == seite and z_boden + br < hoehe]
        for a, e in _frei((-laenge / 2, laenge / 2), tueren):
            p, n = _wandpunkt(seite, (a + e) / 2, breite, tiefe)
            bm_box(bm, _quer(n, e - a, 0.015, hoehe), p + n * 0.0075 + Vector((0, 0, hoehe / 2)))
    o = mesh_aus_bmesh(f"{eltern.name}_Sockel", bm, S, eltern, [mat])
    fase(o, 0.003, 1)
    return o


def fensterbaenke(eltern, breite, tiefe, oeffnungen, z_boden, mat, vorstand=0.05):
    bm = bmesh.new()
    for seite, versatz, br, b, h, art in oeffnungen:
        if art != "fenster" or br < 0.2:
            continue
        p, n = _wandpunkt(seite, versatz, breite, tiefe)
        z = z_boden + br
        tief = 0.11 + vorstand
        bm_box(bm, _quer(n, b + 0.04, tief, 0.03), p + n * (vorstand - tief / 2) + Vector((0, 0, z - 0.015)))
    o = mesh_aus_bmesh(f"{eltern.name}_Fensterbaenke", bm, S, eltern, [mat])
    fase(o, 0.003, 1)
    return o


def leuchten(eltern, breite, tiefe, positionen, mat):
    bm = bmesh.new()
    for seite, versatz, z in positionen:
        p, n = _wandpunkt(seite, versatz, breite, tiefe)
        bm_box(bm, _quer(n, 0.1, 0.12, 0.24), p + n * 0.06 + Vector((0, 0, z)))
    o = mesh_aus_bmesh(f"{eltern.name}_Leuchten", bm, S, eltern, [mat])
    fase(o, 0.004, 2)
    return o


def baue():
    leere(S)
    holz = bpy.data.materials["M_Holzfassade"]
    rahmen = bpy.data.materials["M_Rahmen"]
    sockel_m = bpy.data.materials["M_Sockel"]
    rinne = material("M_Rinne", (0.05, 0.05, 0.055), 0.35, 0.8)
    H, F, C, V = L.HAUS, L.FLUEGEL, L.CARPORT, L.VORDACH
    haus = bpy.data.objects["Haus"]
    fl = bpy.data.objects["Fluegel_Wurzel"]
    carport = bpy.data.objects["Carport"]
    b, t = H["breite"], H["tiefe"]
    fb, ft = F["xmax"] - F["xmin"], F["ymax"] - F["ymin"]

    z_dach = H["eg_h"] + H["og_h"]
    ue = H["dach_ueberstand"]
    bretter(haus, b, t, H["eg_h"], z_dach, L.HAUS_OG_OEFFNUNGEN, H["eg_h"], holz)
    rinnen("Haus_Rinnen", haus, b, t, ue, z_dach, rinne,
           fallrohre=[(sx * (b / 2 - 0.25), -t / 2 - 0.07, sx * (b / 2 - 0.25), -t / 2 - ue - 0.06) for sx in (-1, 1)])
    rinnen("Vordach_Rinne", haus, V["breite"], V["tiefe"], V["ueberstand"], V["hoehe"], rinne,
           mitte=V["mitte_lokal"], nur_vorne=True)
    rinnen("Fluegel_Rinnen", fl, fb, ft, F["ueberstand"], F["h"], rinne,
           fallrohre=[(-fb / 2 - 0.07, sy * (ft / 2 - 0.3), -fb / 2 - F["ueberstand"] - 0.06, sy * (ft / 2 - 0.3))
                      for sy in (-1, 1)])
    rinnen("Carport_Rinnen", carport, C["breite"], C["tiefe"], C["ueberstand"], C["hoehe"], rinne)
    sockel(haus, b, t, L.HAUS_EG_OEFFNUNGEN, H["boden"], 0.35, sockel_m)
    sockel(fl, fb, ft, F["oeffnungen"], 0.15, 0.35, sockel_m)
    eg_baenke = fensterbaenke(haus, b, t, L.HAUS_EG_OEFFNUNGEN, H["boden"], rahmen)
    eg_baenke.name = "Haus_Fensterbaenke_EG"
    og_baenke = fensterbaenke(haus, b, t, L.HAUS_OG_OEFFNUNGEN, H["eg_h"], rahmen, vorstand=0.08)
    og_baenke.name = "Haus_Fensterbaenke_OG"
    leuchten(haus, b, t, [("S", -3.3, 2.1), ("S", 4.3, 2.3)], rahmen)
    leuchten(fl, fb, ft, [("W", -5.75, 2.4), ("W", -1.25, 2.4), ("W", 3.25, 2.4)], rahmen)
    return {"objekte": len(bpy.data.collections[S].objects)}
