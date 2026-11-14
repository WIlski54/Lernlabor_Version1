"""Birken und Ahorn mit eigenem Baumgenerator (verzweigte Röhren + Blattkarten).
Birkenrinde prozedural, Ahornrinde von Poly Haven."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import layout as L
from .materialien import mathe, mix_farbe, pbr
from .pflanzen import pflanzen_material
from .util import leere, mesh_aus_bmesh

# Je Stufe: (anzahl_kinder, t_start, winkel_grad, längenverhältnis, radiusverhältnis, hängen, wackeln)
ARTEN = {
    "birke": {
        "stamm": (0.95, 0.011),  # (anteil der zielhöhe, radius je meter höhe)
        "stufen": [(34, 0.30, 42, 0.38, 0.45, 0.10, 0.10),
                   (8, 0.15, 38, 0.55, 0.55, 0.55, 0.15),
                   (6, 0.20, 32, 0.50, 0.55, 1.00, 0.20)],
        "krone": "kegel", "blatt": (0.05, 0.065), "blatt_dichte": 140,
    },
    "ahorn": {
        "stamm": (0.75, 0.022),
        "stufen": [(26, 0.28, 55, 0.62, 0.55, 0.05, 0.12),
                   (9, 0.15, 45, 0.55, 0.55, 0.20, 0.18),
                   (7, 0.20, 38, 0.50, 0.55, 0.35, 0.22)],
        "krone": "rund", "blatt": (0.10, 0.11), "blatt_dichte": 120,
    },
}


def _basis(d):
    hilf = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(hilf).normalized()
    return u, d.cross(u).normalized()


def _rohr(bm, punkte, radien, seg):
    """Verjüngte Röhre entlang punkte; parallel transportierte Ringe vermeiden Verdrehungen."""
    d0 = (punkte[1] - punkte[0]).normalized()
    u, _ = _basis(d0)
    alt = None
    for i, p in enumerate(punkte):
        d = (punkte[min(i + 1, len(punkte) - 1)] - punkte[max(i - 1, 0)]).normalized()
        u = (u - d * u.dot(d)).normalized()
        v = d.cross(u)
        ring = [bm.verts.new(p + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * radien[i])
                for k in range(seg)]
        if alt:
            for k in range(seg):
                bm.faces.new((alt[k], alt[(k + 1) % seg], ring[(k + 1) % seg], ring[k]))
        alt = ring


def _blatt(bm, uv, c, richtung, groesse, rnd):
    l = (richtung + Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.8, 0.2)))).normalized()
    w = l.cross(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1.0)).normalized())
    if w.length < 1e-4:
        return
    w.normalize()
    b, h = groesse[0] * rnd.uniform(0.8, 1.2), groesse[1] * rnd.uniform(0.8, 1.2)
    vs = [bm.verts.new(p) for p in (c - w * b / 2, c + w * b / 2, c + l * h + w * b / 2, c + l * h - w * b / 2)]
    f = bm.faces.new(vs)
    for loop, koord in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = koord


class _Bauer:
    def __init__(self, art, rnd):
        self.a = ARTEN[art]
        self.rnd = rnd
        self.holz = bmesh.new()
        self.laub = bmesh.new()
        self.uv = self.laub.loops.layers.uv.new("UVMap")

    def ast(self, start, richtung, laenge, radius, stufe):
        rnd = self.rnd
        if stufe == 0:
            n, haengen, wackeln = max(8, int(laenge / 0.4)), 0.0, 0.03
        else:
            _, _, _, _, _, haengen, wackeln = self.a["stufen"][stufe - 1]
            n = max(3, int(laenge / 0.25))
        schritt = laenge / n
        punkte, d = [start.copy()], richtung.copy()
        for i in range(n):
            t = (i + 1) / n
            d = (d + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * wackeln
                 + Vector((0, 0, -1)) * haengen * t * 0.35).normalized()
            punkte.append(punkte[-1] + d * schritt)
        radien = [max(radius * (1 - 0.75 * i / n), 0.004) for i in range(n + 1)]
        _rohr(self.holz, punkte, radien, 10 if stufe == 0 else (6 if stufe == 1 else 4))

        stufen = self.a["stufen"]
        if stufe >= len(stufen) - 1:  # Blätter an den beiden feinsten Stufen
            for _ in range(int(laenge * self.a["blatt_dichte"])):
                t = rnd.uniform(0.25, 1.0)
                idx = min(int(t * n), n - 1)
                p = punkte[idx].lerp(punkte[idx + 1], t * n - idx)
                _blatt(self.laub, self.uv, p, (punkte[idx + 1] - punkte[idx]).normalized(), self.a["blatt"], rnd)
        if stufe >= len(stufen):
            return
        anzahl, t0, winkel, verh, rverh, _, _ = stufen[stufe]
        phi = rnd.uniform(0, 2 * math.pi)
        for j in range(anzahl):
            t = t0 + (1 - t0) * (j + rnd.uniform(0, 1)) / anzahl * 0.95
            idx = min(int(t * n), n - 1)
            p = punkte[idx].lerp(punkte[idx + 1], t * n - idx)
            pd = (punkte[idx + 1] - punkte[idx]).normalized()
            u, v = _basis(pd)
            phi += 2.39996 + rnd.uniform(-0.3, 0.3)  # goldener Winkel
            a = math.radians(winkel * rnd.uniform(0.8, 1.2))
            kd = (pd * math.cos(a) + (u * math.cos(phi) + v * math.sin(phi)) * math.sin(a)).normalized()
            if stufe == 0:
                form = (1 - t) * 1.3 + 0.15 if self.a["krone"] == "kegel" else math.sin(math.pi * min(1.0, 0.25 + t * 0.85)) + 0.2
                kl = laenge * verh * form * rnd.uniform(0.85, 1.15)
            else:
                kl = laenge * verh * (1 - 0.5 * t) * rnd.uniform(0.8, 1.2)
            r_hier = radius * (1 - 0.75 * t)
            self.ast(p, kd, kl, max(r_hier * rverh, 0.004), stufe + 1)


def rinde_birke():
    m = bpy.data.materials.get("M_Rinde_Birke") or bpy.data.materials.new("M_Rinde_Birke")
    m.use_fake_user = True
    nt = m.node_tree
    nt.nodes.clear()
    aus = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3.0, 3.0, 25.0)       # waagerechte Lentizellen
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    streifen = nt.nodes.new("ShaderNodeTexNoise")
    streifen.inputs["Scale"].default_value = 1.0
    streifen.inputs["Detail"].default_value = 2.0
    nt.links.new(mp.outputs["Vector"], streifen.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.6
    mr.inputs["From Max"].default_value = 0.68
    nt.links.new(streifen.outputs["Fac"], mr.inputs["Value"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    fuss = nt.nodes.new("ShaderNodeMapRange")              # unten dunkel und rissig
    fuss.inputs["From Min"].default_value = 0.4
    fuss.inputs["From Max"].default_value = 2.0
    fuss.inputs["To Min"].default_value = 1.0
    fuss.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], fuss.inputs["Value"])
    riss = nt.nodes.new("ShaderNodeTexNoise")
    riss.inputs["Scale"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], riss.inputs["Vector"])
    fuss_maske = mathe(nt, "GREATER_THAN", mathe(nt, "MULTIPLY", fuss.outputs["Result"], riss.outputs["Fac"]), 0.3)
    maske = mathe(nt, "MAXIMUM", mr.outputs["Result"], fuss_maske)
    farbe = mix_farbe(nt, (0.72, 0.70, 0.66), (0.05, 0.045, 0.04), maske)
    nt.links.new(farbe, bsdf.inputs["Base Color"])
    nt.links.new(mathe(nt, "MULTIPLY_ADD", maske, 0.3, 0.6), bsdf.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.3
    nt.links.new(maske, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs[0], aus.inputs["Surface"])
    return m


def baum(name, art, ort, hoehe, seed, laub_mat, rinde_mat):
    rnd = random.Random(seed * 101 + 7)
    a = ARTEN[art]
    bauer = _Bauer(art, rnd)
    stamm_l = hoehe * a["stamm"][0]
    bauer.ast(Vector((0, 0, -0.1)), Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 1)).normalized(),
              stamm_l, hoehe * a["stamm"][1], 0)
    obj = mesh_aus_bmesh(name, bauer.holz, "05e_Baeume", mats=[rinde_mat])
    laub = mesh_aus_bmesh(f"{name}_Laub", bauer.laub, "05e_Baeume", eltern=obj, mats=[laub_mat])
    for p in obj.data.polygons:
        p.use_smooth = True
    hmax = max(max(v.co.z for v in obj.data.vertices), max((v.co.z for v in laub.data.vertices), default=0))
    k = hoehe / hmax
    obj.scale = (k, k, k)
    obj.location = (ort[0], ort[1], 0.0)
    obj.rotation_euler = (0.0, 0.0, seed * 1.3)
    return {"name": name, "blaetter": len(laub.data.polygons), "holz_flaechen": len(obj.data.polygons)}


def baue():
    leere("05e_Baeume")
    birke_rinde = rinde_birke()
    ahorn_rinde = pbr("M_Rinde_Ahorn", "tex_rinde_ahorn", skala=0.8, tint=(0.45, 0.42, 0.38))
    birke_laub = pflanzen_material("M_Blatt_Birke", [(0.0, (0.05, 0.10, 0.02)), (0.6, (0.10, 0.17, 0.04)),
                                                     (1.0, (0.20, 0.24, 0.06))], durchscheinend=0.4, alpha_ellipse=True)
    ahorn_laub = pflanzen_material("M_Blatt_Ahorn", [(0.0, (0.10, 0.12, 0.02)), (0.5, (0.22, 0.22, 0.04)),
                                                     (1.0, (0.35, 0.30, 0.06))], durchscheinend=0.4, alpha_ellipse=True)
    erg = []
    for name, art, ort, hoehe, seed in L.BAEUME:
        if art == "birke":
            erg.append(baum(name, art, ort, hoehe, seed, birke_laub, birke_rinde))
        else:
            erg.append(baum(name, art, ort, hoehe, seed, ahorn_laub, ahorn_rinde))
    return {"baeume": erg}
