"""Wohnlichkeit im Erdgeschoss: Holzlamellen-Raumteiler, Kassetten-Vertäfelung mit Strukturtapete,
schwebende Wandregale, Teppiche (Hochflor mit Fasern, Bouclé, Läufer mit Fransen) und Kokos-Fußmatten.
Läuft innerhalb von innenraum.baue() (alle Objekte hängen am Haus, Collection 03_Innenraum)."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import gn
from . import layout as L
from .architektur import _quer, _wandpunkt, fase
from .util import bm_box, boxen_objekt, material, mesh_aus_bmesh

S = "03_Innenraum"


def _mat_einfach(name, farbe, rauheit, rauschen=0.0, skala=60.0):
    """Einfaches Material, optional mit feinem Relief (Filz, Kokos, Lack)."""
    from .materialien import mathe
    m = material(name, farbe, rauheit)
    if rauschen > 0:
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        if bsdf and not bsdf.inputs["Normal"].is_linked:
            tx = nt.nodes.new("ShaderNodeTexNoise")
            tx.inputs["Scale"].default_value = skala
            tx.inputs["Detail"].default_value = 6.0
            bp = nt.nodes.new("ShaderNodeBump")
            bp.inputs["Strength"].default_value = rauschen
            nt.links.new(tx.outputs["Fac"], bp.inputs["Height"])
            nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ---------------------------------------------------------------- Holzlamellen-Raumteiler

def lamellenwand(haus):
    I = L.INNEN
    W = I["lamellenwand"]
    x0, x1 = W["x"]
    y, z0, z1 = W["y"], I["boden_z"] + 0.02, I["decke_z"] - 0.005
    eiche = bpy.data.materials["M_Eiche"]
    filz = _mat_einfach("M_Filz", (0.045, 0.045, 0.05), 0.95, rauschen=0.25, skala=120)
    boxen_objekt("Innen_Lamellen_Filz", [((x1 - x0, 0.03, z1 - z0), ((x0 + x1) / 2, y, (z0 + z1) / 2))], S, haus, filz)
    latten = []
    x = x0 + 0.03
    while x < x1 - 0.02:
        for seite in (-1, 1):
            latten.append(((0.042, 0.03, z1 - z0 - 0.004), (x, y + seite * 0.03, (z0 + z1) / 2)))
        x += 0.072
    fase(boxen_objekt("Innen_Lamellen", latten, S, haus, eiche), 0.003, 1)


# ---------------------------------------------------------------- Vertäfelung + Tapete

def vertaefelung(haus):
    I = L.INNEN
    b, t = I["breite"], I["tiefe"]
    z0 = I["boden_z"] + 0.02
    z1 = z0 + 1.0
    lack = _mat_einfach("M_Vertaefelung", (0.045, 0.085, 0.06), 0.38, rauschen=0.03, skala=40)
    tapete = bpy.data.materials["M_Tapete"]
    platte, rahmen, tap = [], [], []
    for seite, a, e in I["vertaefelung"]:
        laenge = e - a

        def stueck(liste, s0, s1, za, ze, dicke, seite=seite):
            m, n = _wandpunkt(seite, (s0 + s1) / 2, b, t)
            liste.append((_quer(n, s1 - s0, dicke, ze - za), m - n * (dicke / 2) + Vector((0, 0, (za + ze) / 2))))

        stueck(platte, a, e, z0, z1, 0.012)
        stueck(rahmen, a, e, z0, z0 + 0.14, 0.03)                 # Sockel-Riegel
        stueck(rahmen, a, e, z1 - 0.08, z1, 0.03)                 # oberer Riegel
        felder = max(1, round(laenge / 0.6))
        for k in range(felder + 1):                               # senkrechte Rahmenhölzer
            s = a + laenge * k / felder
            s0, s1 = max(a, s - 0.035), min(e, s + 0.035)
            stueck(rahmen, s0, s1, z0 + 0.14, z1 - 0.08, 0.03)
        stueck(rahmen, a, e, z1, z1 + 0.03, 0.045)                # Abschlussleiste
        stueck(tap, a, e, z1 + 0.03, I["decke_z"] - 0.006, 0.003)
    fase(boxen_objekt("Innen_Vertaefelung_Platte", platte, S, haus, lack), 0.002, 1)
    fase(boxen_objekt("Innen_Vertaefelung_Rahmen", rahmen, S, haus, lack), 0.004, 2)
    boxen_objekt("Innen_Tapete", tap, S, haus, tapete)


# ---------------------------------------------------------------- Wandregal

def wandregal(haus):
    I = L.INNEN
    seite, a, e, hoehen = I["wandregal"]
    p, n = _wandpunkt(seite, (a + e) / 2, I["breite"], I["tiefe"])
    boards = [(_quer(n, e - a, 0.24, 0.035), p - n * 0.12 + Vector((0, 0, I["boden_z"] + h - 0.0175))) for h in hoehen]
    fase(boxen_objekt("Innen_Wandregal", boards, S, haus, bpy.data.materials["M_Eiche"]), 0.003, 2)


# ---------------------------------------------------------------- Teppiche

def flor_bibliothek():
    from .pflanzen import halm, pflanzen_material
    from .util import leere
    leere("Bib_Teppichflor")
    m = pflanzen_material("M_Flor", [(0.0, (0.55, 0.49, 0.39)), (1.0, (0.72, 0.66, 0.55))], durchscheinend=0.25, rauheit=0.9)
    rnd = random.Random(71)
    for k in range(4):
        bm = bmesh.new()
        for _ in range(8):
            w = rnd.uniform(0, 2 * math.pi)
            halm(bm, (math.cos(w) * 0.004, math.sin(w) * 0.004, 0.0), (math.cos(w), math.sin(w)),
                 rnd.uniform(0.018, 0.03), 0.004, rnd.uniform(0.4, 1.0), segmente=3, haengen=rnd.uniform(0.2, 0.5))
        mesh_aus_bmesh(f"Flor_{k}", bm, "Bib_Teppichflor", mats=[m])


def teppiche(haus):
    I = L.INNEN
    z = I["boden_z"] + 0.02
    for name, (x, y), (b, t), mat_name, flor in I["teppiche"]:
        o = boxen_objekt(f"Innen_Teppich_{name}", [((b, t, 0.014), (x, y, z + 0.007))], S, haus,
                         bpy.data.materials[mat_name])
        fase(o, 0.005, 2)
        if flor:
            bm = bmesh.new()
            bm.faces.new([bm.verts.new((x + sx * b / 2 * 0.98, y + sy * t / 2 * 0.98, z + 0.014))
                          for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
            fl = mesh_aus_bmesh(f"Innen_Teppich_{name}_Flor", bm, S, haus)
            gn.anwenden(fl, "Flor", "Bib_Teppichflor", "Maske_Beet", dichte_lauf=0.0, dichte_schoen=9000.0,
                        abstand=0.004, skala=(0.8, 1.3), neigung=0.35, seed=5, basis=False, ausschluss_abstand=-1.0)
    # Fransen an den Schmalseiten des Läufers
    lx, ly = I["laeufer_fransen"][0]
    lb, lt = I["laeufer_fransen"][1]
    fransen = []
    for sx in (-1, 1):
        yy = ly - lt / 2 + 0.01
        while yy < ly + lt / 2 - 0.005:
            fransen.append(((0.06, 0.004, 0.003), (lx + sx * (lb / 2 + 0.028), yy, z + 0.002)))
            yy += 0.011
    boxen_objekt("Innen_Laeufer_Fransen", fransen, S, haus, _mat_einfach("M_Fransen", (0.7, 0.66, 0.58), 0.9))


def fussmatten(haus):
    I = L.INNEN
    z = I["boden_z"] + 0.02
    kokos = _mat_einfach("M_Kokos", (0.2, 0.13, 0.065), 1.0, rauschen=0.9, skala=160)
    gummi = _mat_einfach("M_Gummi", (0.015, 0.015, 0.015), 0.7)
    matten, raender = [], []
    for (x, y), (b, t) in I["fussmatten"]:
        raender.append(((b + 0.04, t + 0.04, 0.008), (x, y, z + 0.004)))
        matten.append(((b, t, 0.016), (x, y, z + 0.008)))
    fase(boxen_objekt("Innen_Fussmatten", matten, S, haus, kokos), 0.003, 1)
    fase(boxen_objekt("Innen_Fussmatten_Rand", raender, S, haus, gummi), 0.003, 1)


def baue(haus):
    lamellenwand(haus)
    vertaefelung(haus)
    wandregal(haus)
    flor_bibliothek()
    teppiche(haus)
    fussmatten(haus)
