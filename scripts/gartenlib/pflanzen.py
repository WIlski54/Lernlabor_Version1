"""Pflanzen: Materialien, Halm-/Gras-/Staudenbibliotheken, Rasen, Bepflanzung, Poly-Haven-Sträucher."""
import glob
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import gn
from . import layout as L
from .util import leere, material, mesh_aus_bmesh, pfad


def _farbrampe(nt, wert, farben):
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = farben[0][0], (*farben[0][1], 1.0)
    el[-1].position, el[-1].color = farben[-1][0], (*farben[-1][1], 1.0)
    for pos, rgb in farben[1:-1]:
        e = el.new(pos)
        e.color = (*rgb, 1.0)
    nt.links.new(wert, ramp.inputs["Fac"])
    return ramp.outputs["Color"]


def pflanzen_material(name, farben, durchscheinend=0.3, rauheit=0.45, spitze=None, alpha_ellipse=False):
    """farben: [(pos, (r,g,b)), …] über Zufall pro Instanz/Insel; spitze: ((r,g,b), stärke) über Attribut t."""
    from .materialien import mathe, mix_farbe
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_fake_user = True
    nt = m.node_tree
    nt.nodes.clear()
    aus = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rauheit
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    zufall = mathe(nt, "MULTIPLY_ADD", geo.outputs["Random Per Island"], 0.3,
                   mathe(nt, "MULTIPLY", oi.outputs["Random"], 0.7))
    farbe = _farbrampe(nt, zufall, farben)
    if spitze:
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "t"
        farbe = mix_farbe(nt, farbe, spitze[0], mathe(nt, "MULTIPLY", attr.outputs["Fac"], spitze[1]))
    nt.links.new(farbe, bsdf.inputs["Base Color"])
    nt.links.new(farbe, tr.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = durchscheinend
    nt.links.new(bsdf.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    ende = mix.outputs[0]
    if alpha_ellipse:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["UV"], sep.inputs[0])
        qx = mathe(nt, "POWER", mathe(nt, "MULTIPLY_ADD", sep.outputs["X"], 2.0, -1.0), 2.0)
        qy = mathe(nt, "POWER", mathe(nt, "MULTIPLY_ADD", sep.outputs["Y"], 2.0, -1.0), 2.0)
        maske = mathe(nt, "LESS_THAN", mathe(nt, "ADD", qx, qy), 1.0)
        trans = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(maske, mix2.inputs["Fac"])
        nt.links.new(trans.outputs[0], mix2.inputs[1])
        nt.links.new(ende, mix2.inputs[2])
        ende = mix2.outputs[0]
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "DITHERED"
    nt.links.new(ende, aus.inputs["Surface"])
    return m


def _t_layer(bm):
    return bm.verts.layers.float.get("t") or bm.verts.layers.float.new("t")


def halm(bm, basis, richtung, hoehe, breite, neigung, segmente=4, haengen=0.0):
    """Halm als Streifen ab basis (x, y, z); speichert t (0 unten … 1 Spitze). Liefert die Flächen."""
    tl = _t_layer(bm)
    quer = Vector((-richtung[1], richtung[0], 0.0))
    z0 = basis[2] if len(basis) > 2 else 0.0
    links, rechts = [], []
    for k in range(segmente + 1):
        t = k / segmente
        aus = neigung * hoehe * t ** 1.6
        mitte = Vector((basis[0] + richtung[0] * aus, basis[1] + richtung[1] * aus,
                        z0 + hoehe * (t - haengen * t ** 2.5)))
        halb = breite * (1.0 - 0.85 * t) / 2
        for liste, seite in ((links, -1), (rechts, 1)):
            v = bm.verts.new(mitte + quer * halb * seite)
            v[tl] = t
            liste.append(v)
    return [bm.faces.new((links[k], rechts[k], rechts[k + 1], links[k + 1])) for k in range(segmente)]


def _spitze(basis, richtung, hoehe, neigung, haengen=0.0):
    return Vector((basis[0] + richtung[0] * neigung * hoehe, basis[1] + richtung[1] * neigung * hoehe,
                   (basis[2] if len(basis) > 2 else 0.0) + hoehe * (1 - haengen)))


# ---------------------------------------------------------------- Rasen

def halm_bibliothek():
    leere("Bib_Halme")
    m = pflanzen_material("M_Gras", [(0.0, (0.035, 0.085, 0.015)), (0.5, (0.07, 0.15, 0.025)),
                                     (0.9, (0.11, 0.19, 0.035)), (1.0, (0.20, 0.19, 0.08))],
                          durchscheinend=0.3, spitze=((0.22, 0.22, 0.09), 0.5))
    rnd = random.Random(3)
    for k in range(8):
        bm = bmesh.new()
        for _ in range(rnd.randint(25, 40)):
            w = rnd.uniform(0, 2 * math.pi)
            r = 0.045 * math.sqrt(rnd.random())
            rw = w + rnd.uniform(-0.6, 0.6)
            halm(bm, (math.cos(w) * r, math.sin(w) * r, 0.0), (math.cos(rw), math.sin(rw)),
                 rnd.uniform(0.05, 0.12), 0.004 * rnd.uniform(0.8, 1.2), rnd.uniform(0.05, 0.35))
        mesh_aus_bmesh(f"Halme_{k}", bm, "Bib_Halme", mats=[m])


def rasen():
    leere("05a_Rasen")
    halm_bibliothek()
    x0, y0, x1, y1 = L.GRUNDSTUECK
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)]])
    o = mesh_aus_bmesh("Rasen", bm, "05a_Rasen", mats=[material("M_Erde", (0.05, 0.06, 0.03), 0.95)])
    gn.anwenden(o, "Rasen", "Bib_Halme", "Maske_Rasen", dichte_lauf=60, dichte_schoen=500, abstand=0.03,
                skala=(0.7, 1.2), neigung=0.15, seed=1, basis=True)
    return {"rasen": o.name}


# ---------------------------------------------------------------- Beete

def graeser_bibliothek():
    leere("Bib_Graeser")
    m_gras = pflanzen_material("M_Ziergras", [(0.0, (0.06, 0.10, 0.03)), (0.5, (0.14, 0.16, 0.06)),
                                              (1.0, (0.32, 0.28, 0.14))],
                               durchscheinend=0.35, spitze=((0.45, 0.40, 0.22), 0.7))
    m_rispe = pflanzen_material("M_Grasbluete", [(0.0, (0.32, 0.28, 0.20)), (1.0, (0.50, 0.45, 0.35))],
                                durchscheinend=0.5, rauheit=0.6)
    rnd = random.Random(11)
    for k in range(5):
        h = rnd.uniform(0.6, 1.3)
        bm = bmesh.new()
        for _ in range(rnd.randint(120, 200)):
            w = rnd.uniform(0, 2 * math.pi)
            r = 0.12 * math.sqrt(rnd.random())
            rw = w + rnd.uniform(-0.4, 0.4)
            halm(bm, (math.cos(w) * r, math.sin(w) * r, 0.0), (math.cos(rw), math.sin(rw)),
                 h * rnd.uniform(0.6, 1.0), 0.008, rnd.uniform(0.15, 0.7), segmente=6, haengen=rnd.uniform(0.1, 0.35))
        if k < 2:  # Rispen (Federgras-/Chinaschilf-Optik)
            for _ in range(rnd.randint(10, 20)):
                w = rnd.uniform(0, 2 * math.pi)
                r = 0.08 * math.sqrt(rnd.random())
                basis = (math.cos(w) * r, math.sin(w) * r, 0.0)
                richtung = (math.cos(w), math.sin(w))
                hh, ng = h * rnd.uniform(1.05, 1.2), rnd.uniform(0.15, 0.4)
                for f in halm(bm, basis, richtung, hh, 0.003, ng, segmente=4):
                    f.material_index = 1
                kopf = _spitze(basis, richtung, hh, ng)
                for _ in range(rnd.randint(6, 10)):
                    kw = rnd.uniform(0, 2 * math.pi)
                    for f in halm(bm, (kopf.x, kopf.y, kopf.z - 0.25), (math.cos(kw), math.sin(kw)),
                                  rnd.uniform(0.18, 0.3), 0.012, 0.15, segmente=3):
                        f.material_index = 1
        mesh_aus_bmesh(f"Ziergras_{k}", bm, "Bib_Graeser", mats=[m_gras, m_rispe])


def _bluete(bm, mitte, r):
    for i in range(8):
        a = 2 * math.pi * i / 8
        p0 = mitte + Vector((math.cos(a - 0.25), math.sin(a - 0.25), 0)) * r * 0.25
        p1 = mitte + Vector((math.cos(a), math.sin(a), 0.15)) * r
        p2 = mitte + Vector((math.cos(a + 0.25), math.sin(a + 0.25), 0)) * r * 0.25
        bm.faces.new([bm.verts.new(p) for p in (mitte, p0, p1, p2)]).material_index = 0
    ring = [bm.verts.new(mitte + Vector((math.cos(2 * math.pi * j / 6), math.sin(2 * math.pi * j / 6), 0.1)) * r * 0.28)
            for j in range(6)]
    bm.faces.new(ring).material_index = 1


def stauden_bibliothek():
    leere("Bib_Stauden")
    mats = [pflanzen_material("M_Bluete_Weiss", [(0.0, (0.75, 0.75, 0.72)), (1.0, (0.85, 0.85, 0.82))], durchscheinend=0.4),
            pflanzen_material("M_Bluete_Mitte", [(0.0, (0.55, 0.40, 0.05)), (1.0, (0.70, 0.55, 0.10))], durchscheinend=0.1),
            pflanzen_material("M_Staudenblatt", [(0.0, (0.03, 0.07, 0.02)), (1.0, (0.07, 0.12, 0.03))], durchscheinend=0.3)]
    rnd = random.Random(17)
    for k in range(4):
        bm = bmesh.new()
        for _ in range(rnd.randint(18, 35)):
            w = rnd.uniform(0, 2 * math.pi)
            r = 0.1 * math.sqrt(rnd.random())
            basis = (math.cos(w) * r, math.sin(w) * r, 0.0)
            richtung = (math.cos(w), math.sin(w))
            hh, ng = rnd.uniform(0.35, 0.75), rnd.uniform(0.03, 0.15)
            for f in halm(bm, basis, richtung, hh, 0.004, ng, segmente=3):
                f.material_index = 2
            _bluete(bm, _spitze(basis, richtung, hh, ng), rnd.uniform(0.025, 0.035))
        for _ in range(12):
            w = rnd.uniform(0, 2 * math.pi)
            d = Vector((math.cos(w), math.sin(w), 0))
            q = Vector((-d.y, d.x, 0))
            b0 = d * rnd.uniform(0.0, 0.06) + Vector((0, 0, 0.03))
            laenge = rnd.uniform(0.12, 0.2)
            pts = [b0, b0 + d * laenge * 0.4 + q * 0.035 + Vector((0, 0, 0.05)),
                   b0 + d * laenge + Vector((0, 0, 0.04)), b0 + d * laenge * 0.4 - q * 0.035 + Vector((0, 0, 0.05))]
            bm.faces.new([bm.verts.new(p) for p in pts]).material_index = 2
        mesh_aus_bmesh(f"Staude_{k}", bm, "Bib_Stauden", mats=mats)


def bepflanzung():
    for c in ("05b_Graeser", "05c_Stauden", "05d_Straeucher"):
        leere(c)
    for nr, (beet, schichten) in enumerate(L.BEPFLANZUNG.items()):
        quelle = bpy.data.objects[beet]
        for i, (bib, ziel, d_lauf, d_schoen, abstand, skala) in enumerate(schichten):
            if d_schoen <= 0:
                continue
            o = bpy.data.objects.new(f"Pflanzung_{beet}_{bib}", quelle.data)
            bpy.data.collections[ziel].objects.link(o)
            gn.anwenden(o, "Streuen", bib, "Maske_Beet", d_lauf, d_schoen, abstand, skala, 0.12,
                        seed=nr * 10 + i, basis=False, ausschluss_abstand=0.15)
    return {"beete": len(L.BEPFLANZUNG)}


def kiefernpolster(anzahl=3):
    """Prozedurale Bergkiefer-Polster: dunkle Kuppel plus Nadelbüschel auf der Oberfläche (Breite ca. 1 m)."""
    m_nadel = pflanzen_material("M_Kiefer", [(0.0, (0.015, 0.04, 0.012)), (0.6, (0.03, 0.07, 0.02)),
                                             (1.0, (0.06, 0.10, 0.03))],
                                durchscheinend=0.15, rauheit=0.5, spitze=((0.10, 0.14, 0.04), 0.6))
    m_kern = material("M_Kiefer_Kern", (0.008, 0.02, 0.006), 0.8)
    leere("Bib_Kiefer")
    rnd = random.Random(23)
    for k in range(anzahl):
        rx, ry, h = 0.5, rnd.uniform(0.42, 0.5), rnd.uniform(0.3, 0.45)
        bm = bmesh.new()
        kern = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
        for v in kern["verts"]:
            v.co = Vector((v.co.x * rx * 0.7, v.co.y * ry * 0.7, max(v.co.z, 0.0) * h * 0.7))
        for f in bm.faces:
            f.material_index = 1
        for _ in range(1600):
            phi = rnd.uniform(0, 2 * math.pi)
            th = math.acos(rnd.uniform(0.05, 1.0))          # obere Halbkugel
            p = (math.sin(th) * math.cos(phi) * rx, math.sin(th) * math.sin(phi) * ry, math.cos(th) * h)
            richtung = (math.cos(phi + rnd.uniform(-0.4, 0.4)), math.sin(phi + rnd.uniform(-0.4, 0.4)))
            neigung = 0.2 + 1.2 * math.sin(th)
            for _ in range(6):
                halm(bm, (p[0] + rnd.uniform(-0.03, 0.03), p[1] + rnd.uniform(-0.03, 0.03), p[2] - 0.08),
                     richtung, rnd.uniform(0.10, 0.18), 0.003, neigung, segmente=2)
        mesh_aus_bmesh(f"Kiefernpolster_{k}", bm, "Bib_Kiefer", mats=[m_nadel, m_kern])
    return {"kiefernpolster": anzahl}


# ---------------------------------------------------------------- Poly-Haven-Sträucher

def polyhaven_polster(breite_ziel=1.0):
    """Hängt die gewählten Poly-Haven-Modelle an, legt Transformationen in die Mesh-Daten und normiert die Breite."""
    from .materialien import auswahl
    leere("Bib_Polster")
    ziel = bpy.data.collections["Bib_Polster"]
    for aid in auswahl()["modelle_straeucher"]:
        datei = glob.glob(pfad("assets", "polyhaven", "models", aid, "*.blend"))[0]
        with bpy.data.libraries.load(datei, link=False) as (quelle, neu):
            neu.objects = list(quelle.objects)
        objs = [o for o in neu.objects if o is not None]
        meshes = [o for o in objs if o.type == "MESH"]
        if any("lod" in o.name.lower() for o in meshes):
            meshes = [o for o in meshes if "lod0" in o.name.lower().replace("_", "")]
        for o in objs:
            if o not in meshes:
                bpy.data.objects.remove(o)
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None
            o.data.transform(mw)
            o.matrix_world = Matrix.Identity(4)
            xs = [v.co.x for v in o.data.vertices]
            ys = [v.co.y for v in o.data.vertices]
            zs = [v.co.z for v in o.data.vertices]
            k = breite_ziel / max(max(xs) - min(xs), max(ys) - min(ys))
            mitte = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)))
            o.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-mitte))
            ziel.objects.link(o)
    return {"polster": [o.name for o in ziel.objects]}
