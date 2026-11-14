"""Geschnittene Hainbuchenhecke: organischer Kern (gerundet, ausgebeult, unten schmaler) und nach außen
ausgerichtete Zweige mit geformten, gefalteten Blättern. Für den Modus Laufen gibt es Blattballen."""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

from . import layout as L
from .util import gn_kennung, gn_setze, leere, material, mesh_aus_bmesh, treiber_modus

NAME = "GN_Hecke"


# ---------------------------------------------------------------- Kern

def _profil(w, h, r, schritt=0.07):
    """Querschnitt (y, z) einer geschnittenen Hecke: unten etwas schmaler, oben gerundete Kanten."""
    pts = [(-w * 0.82, 0.0), (-w * 0.95, 0.35)]
    for k in range(1, 8):  # linke Flanke
        pts.append((-w, 0.35 + (h - r - 0.35) * k / 7))
    for k in range(1, 7):  # linke Rundung
        a = math.pi - k * (math.pi / 2) / 6
        pts.append((-w + r + math.cos(a) * r, h - r + math.sin(a) * r))
    n_oben = max(2, int((2 * (w - r)) / schritt))
    for k in range(1, n_oben):
        pts.append((-w + r + 2 * (w - r) * k / n_oben, h))
    for k in range(0, 7):  # rechte Rundung
        a = math.pi / 2 - k * (math.pi / 2) / 6
        pts.append((w - r + math.cos(a) * r, h - r + math.sin(a) * r))
    for k in range(1, 8):
        pts.append((w, h - r - (h - r - 0.35) * k / 7))
    pts += [(w * 0.95, 0.35), (w * 0.82, 0.0)]
    return pts


def kern_mesh(laenge, tiefe, hoehe, seed):
    """Heckenkörper entlang X, zentriert; Oberfläche mit Rauschen ausgebeult."""
    prof = _profil(tiefe / 2, hoehe, 0.2)
    # Normalen des Profils (2D) für die Auslenkung
    norm = []
    for i, (y, z) in enumerate(prof):
        y0, z0 = prof[max(i - 1, 0)]
        y1, z1 = prof[min(i + 1, len(prof) - 1)]
        ty, tz = y1 - y0, z1 - z0
        l = math.hypot(ty, tz) or 1.0
        n = (tz / l, -ty / l)
        if n[0] * y + n[1] * (z - hoehe / 2) < 0:
            n = (-n[0], -n[1])
        norm.append(n)
    bm = bmesh.new()
    schritte = max(2, int(laenge / 0.1))
    ringe = []
    off = Vector((seed * 13.1, seed * 7.7, 0.0))
    for s in range(schritte + 1):
        x = -laenge / 2 + laenge * s / schritte
        ring = []
        for (y, z), (ny, nz) in zip(prof, norm):
            p = Vector((x, y, z))
            fein = noise.fractal(p * 1.6 + off, 0.6, 2.0, 3) * 0.06
            grob = noise.noise(p * 0.35 + off) * 0.06
            d = fein + grob if z > 0.02 else 0.0
            ring.append(bm.verts.new((x, y + ny * d, z + nz * d)))
        ringe.append(ring)
    for s in range(schritte):
        for i in range(len(prof) - 1):
            bm.faces.new((ringe[s][i], ringe[s + 1][i], ringe[s + 1][i + 1], ringe[s][i + 1]))
    for ring, rev in ((ringe[0], True), (ringe[-1], False)):
        f = bm.faces.new(list(reversed(ring)) if rev else ring)
        f.select = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


# ---------------------------------------------------------------- Blätter und Zweige

def _blatt(bm, uv, basis, richtung, normale, laenge, breite, falte):
    """Eiförmiges, leicht gesägtes Blatt mit Mittelrippen-Falte; UV: u quer, v längs."""
    seite = richtung.cross(normale).normalized()
    pts, uvs = [], []
    n = 7
    for k in range(n + 1):  # rechte Kante von Stiel zu Spitze, dann links zurück
        t = k / n
        b = math.sin(math.pi * t ** 0.75) * breite / 2 * (1.0 + 0.08 * (k % 2))
        pts.append((t, b))
    rand = pts + [(t, -b) for t, b in reversed(pts[1:-1])]
    mitte_v = []
    for t, b in rand:
        h = abs(b) / (breite / 2 + 1e-6)
        p = basis + richtung * (t * laenge) + seite * b + normale * (falte * h * breite)
        mitte_v.append(bm.verts.new(p))
        uvs.append((0.5 + b / breite, t))
    f = bm.faces.new(mitte_v)
    for loop, k in zip(f.loops, uvs):
        loop[uv].uv = k
    return f


def zweig_bibliothek(name="Bib_Heckenzweig", anzahl=6, blaetter=(14, 22), seed=41, mat=None):
    leere(name)
    rnd = random.Random(seed)
    for k in range(anzahl):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        n_bl = rnd.randint(*blaetter)
        for i in range(n_bl):
            # Blätter rosettenartig um die lokale Z-Achse (= Heckenaußenseite), leicht gestaffelt
            w = i * 2.39996 + rnd.uniform(-0.3, 0.3)
            r = rnd.uniform(0.0, 0.06)
            basis = Vector((math.cos(w) * r, math.sin(w) * r, rnd.uniform(-0.04, 0.03)))
            richtung = Vector((math.cos(w), math.sin(w), rnd.uniform(-0.25, 0.35))).normalized()
            normale = Vector((rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), 1.0)).normalized()
            normale = (normale - richtung * normale.dot(richtung)).normalized()
            _blatt(bm, uv, basis, richtung, normale, rnd.uniform(0.045, 0.068), rnd.uniform(0.026, 0.04),
                   rnd.uniform(0.15, 0.35))
        mesh_aus_bmesh(f"{name}_{k}", bm, name, mats=[mat])


def blattmaterial():
    """Hainbuchenblatt: Farbvariation je Blatt, leichte Transluzenz, Adern als Relief (aus den UVs)."""
    from .materialien import mathe, mix_farbe
    from .pflanzen import _farbrampe
    m = bpy.data.materials.get("M_Hecke_Blatt") or bpy.data.materials.new("M_Hecke_Blatt")
    m.use_fake_user = True
    nt = m.node_tree
    nt.nodes.clear()
    aus = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.55
    if "Specular IOR Level" in bsdf.inputs:  # weniger Himmelsspiegelung – sonst wirken ferne Blätter weißlich
        bsdf.inputs["Specular IOR Level"].default_value = 0.3
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    zufall = mathe(nt, "MULTIPLY_ADD", geo.outputs["Random Per Island"], 0.65, mathe(nt, "MULTIPLY", oi.outputs["Random"], 0.35))
    farbe = _farbrampe(nt, zufall, [(0.0, (0.018, 0.045, 0.01)), (0.45, (0.035, 0.08, 0.018)),
                                    (0.85, (0.07, 0.13, 0.03)), (1.0, (0.13, 0.17, 0.05))])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])
    quer = mathe(nt, "ABSOLUTE", mathe(nt, "SUBTRACT", sep.outputs["X"], 0.5))
    rippe = mathe(nt, "LESS_THAN", quer, 0.025)
    seitenadern = mathe(nt, "GREATER_THAN", mathe(nt, "SINE", mathe(nt, "MULTIPLY_ADD", sep.outputs["Y"], 55.0,
                                                                      mathe(nt, "MULTIPLY", quer, -28.0))), 0.85)
    adern = mathe(nt, "MAXIMUM", rippe, mathe(nt, "MULTIPLY", seitenadern, 0.6))
    farbe = mix_farbe(nt, farbe, (0.12, 0.17, 0.06), mathe(nt, "MULTIPLY", adern, 0.35))
    nt.links.new(farbe, bsdf.inputs["Base Color"])
    nt.links.new(farbe, tr.inputs["Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.35
    bp.inputs["Distance"].default_value = 0.002
    nt.links.new(mathe(nt, "SUBTRACT", 1.0, adern), bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.3
    nt.links.new(bsdf.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], aus.inputs["Surface"])
    return m


def kernmaterial():
    """Heckeninneres als dichtes Laubbild: Voronoi-Zellen = einzelne Blätter (je eigener Grünton,
    dunkle Zwischenräume als Tiefe, gewölbtes Relief). Unten bräunlich (Äste, Laubstreu).
    Wichtig für den Modus Laufen, in dem nur wenige echte Blattballen gestreut werden."""
    from .materialien import mathe, mix_farbe
    from .pflanzen import _farbrampe
    m = bpy.data.materials.get("M_Hecke_Kern") or bpy.data.materials.new("M_Hecke_Kern")
    nt = m.node_tree
    nt.nodes.clear()
    aus = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.55
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 22.0
    vor.inputs["Randomness"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    kante = nt.nodes.new("ShaderNodeTexVoronoi")
    kante.feature = "DISTANCE_TO_EDGE"
    kante.inputs["Scale"].default_value = 22.0
    kante.inputs["Randomness"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], kante.inputs["Vector"])
    zelle = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vor.outputs["Color"], zelle.inputs[0])
    blatt = _farbrampe(nt, zelle.outputs[0], [(0.0, (0.012, 0.035, 0.008)), (0.5, (0.03, 0.07, 0.016)),
                                              (0.85, (0.06, 0.11, 0.025)), (1.0, (0.1, 0.14, 0.04))])
    # Zwischenräume (nahe der Zellkante) dunkel → wirkt wie Tiefe zwischen den Blättern
    luecke = mathe(nt, "LESS_THAN", kante.outputs["Distance"], 0.06)
    farbe = mix_farbe(nt, blatt, (0.004, 0.01, 0.003), mathe(nt, "MULTIPLY", luecke, 0.85))
    gross = nt.nodes.new("ShaderNodeTexNoise")
    gross.inputs["Scale"].default_value = 1.2
    nt.links.new(tc.outputs["Object"], gross.inputs["Vector"])
    farbe = mix_farbe(nt, farbe, (0.45, 0.45, 0.45), mathe(nt, "MULTIPLY", gross.outputs["Fac"], 0.6), "MULTIPLY")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    unten = mathe(nt, "LESS_THAN", sep.outputs["Z"], 0.3)
    farbe = mix_farbe(nt, farbe, (0.03, 0.02, 0.012), mathe(nt, "MULTIPLY", unten, 0.8))
    nt.links.new(farbe, bsdf.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.7
    nt.links.new(kante.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs[0], aus.inputs["Surface"])
    return m


# ---------------------------------------------------------------- Geometry Nodes

def _sock(sammlung, name, typ=None):
    for s in sammlung:
        if s.name == name and (typ is None or s.type == typ) and getattr(s, "enabled", True):
            return s
    raise KeyError(f"{name}/{typ}")


def hecken_knoten():
    """GN_Hecke: Zweige auf der Kernoberfläche, Z-Achse entlang der Normalen, zufällige Drehung,
    in unterschiedlicher Tiefe; unten ausgedünnt."""
    alt = bpy.data.node_groups.get(NAME)
    if alt is not None:
        bpy.data.node_groups.remove(alt)
    ng = bpy.data.node_groups.new(NAME, "GeometryNodeTree")
    i = ng.interface
    i.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    i.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    i.new_socket("Bibliothek", in_out="INPUT", socket_type="NodeSocketCollection")
    i.new_socket("Bibliothek_Lauf", in_out="INPUT", socket_type="NodeSocketCollection")
    for name, wert, typ in [("Lauf_Bibliothek", 0.0, "NodeSocketFloat"), ("Dichte", 200.0, "NodeSocketFloat"),
                            ("Tiefe", 0.12, "NodeSocketFloat"), ("Seed", 0, "NodeSocketInt")]:
        i.new_socket(name, in_out="INPUT", socket_type=typ).default_value = wert
    N, Lk = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    vert = N.new("GeometryNodeDistributePointsOnFaces")
    vert.distribute_method = "RANDOM"
    Lk.new(gi.outputs["Geometry"], vert.inputs["Mesh"])
    Lk.new(gi.outputs["Dichte"], vert.inputs["Density"])
    Lk.new(gi.outputs["Seed"], vert.inputs["Seed"])

    def zufall(mn, mx, plus):
        r = N.new("FunctionNodeRandomValue")
        r.data_type = "FLOAT"
        _sock(r.inputs, "Min", "VALUE").default_value = mn
        _sock(r.inputs, "Max", "VALUE").default_value = mx
        add = N.new("ShaderNodeMath")
        add.operation = "ADD"
        Lk.new(gi.outputs["Seed"], add.inputs[0])
        add.inputs[1].default_value = plus
        Lk.new(add.outputs[0], r.inputs["Seed"])
        return _sock(r.outputs, "Value", "VALUE")

    # unten ausdünnen: Punkte unterhalb einer zufälligen Höhe (0 … 0,3 m) löschen
    pos = N.new("GeometryNodeInputPosition")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(pos.outputs[0], sep.inputs[0])
    cmp = N.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "LESS_THAN"
    Lk.new(sep.outputs["Z"], _sock(cmp.inputs, "A", "VALUE"))
    Lk.new(zufall(0.0, 0.3, 7), _sock(cmp.inputs, "B", "VALUE"))
    loe = N.new("GeometryNodeDeleteGeometry")
    loe.domain = "POINT"
    Lk.new(vert.outputs["Points"], loe.inputs["Geometry"])
    Lk.new(cmp.outputs["Result"], loe.inputs["Selection"])

    # in die Tiefe versetzen (entlang -Normale)
    tiefe = N.new("ShaderNodeMath")
    tiefe.operation = "MULTIPLY"
    Lk.new(zufall(-0.4, 1.0, 3), tiefe.inputs[0])  # überwiegend nach außen – im Kern wären Zweige unsichtbar
    Lk.new(gi.outputs["Tiefe"], tiefe.inputs[1])
    skal = N.new("ShaderNodeVectorMath")
    skal.operation = "SCALE"
    Lk.new(vert.outputs["Normal"], skal.inputs[0])
    Lk.new(tiefe.outputs[0], _sock(skal.inputs, "Scale"))
    setpos = N.new("GeometryNodeSetPosition")
    Lk.new(loe.outputs["Geometry"], setpos.inputs["Geometry"])
    Lk.new(skal.outputs["Vector"], setpos.inputs["Offset"])

    # Ausrichtung: Normale + zufällige Drehung um die eigene Achse + leichte Neigung
    eul = N.new("ShaderNodeCombineXYZ")
    Lk.new(zufall(-0.45, 0.45, 11), eul.inputs["X"])
    Lk.new(zufall(-0.45, 0.45, 12), eul.inputs["Y"])
    Lk.new(zufall(0.0, 6.2832, 13), eul.inputs["Z"])
    e2r = N.new("FunctionNodeEulerToRotation")
    Lk.new(eul.outputs[0], e2r.inputs[0])
    rot = N.new("FunctionNodeRotateRotation")
    rot.rotation_space = "LOCAL"
    Lk.new(vert.outputs["Rotation"], rot.inputs[0])
    Lk.new(e2r.outputs[0], rot.inputs[1])

    ci = N.new("GeometryNodeCollectionInfo")
    ci.transform_space = "ORIGINAL"
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    Lk.new(gi.outputs["Bibliothek"], ci.inputs["Collection"])
    ci_l = N.new("GeometryNodeCollectionInfo")
    ci_l.transform_space = "ORIGINAL"
    ci_l.inputs["Separate Children"].default_value = True
    ci_l.inputs["Reset Children"].default_value = True
    Lk.new(gi.outputs["Bibliothek_Lauf"], ci_l.inputs["Collection"])
    cmp_l = N.new("FunctionNodeCompare")
    cmp_l.data_type = "FLOAT"
    cmp_l.operation = "GREATER_THAN"
    Lk.new(gi.outputs["Lauf_Bibliothek"], _sock(cmp_l.inputs, "A", "VALUE"))
    _sock(cmp_l.inputs, "B", "VALUE").default_value = 0.5
    sw = N.new("GeometryNodeSwitch")
    sw.input_type = "GEOMETRY"
    Lk.new(cmp_l.outputs["Result"], sw.inputs["Switch"])
    Lk.new(ci.outputs[0], sw.inputs["False"])
    Lk.new(ci_l.outputs[0], sw.inputs["True"])

    idx = N.new("FunctionNodeRandomValue")
    idx.data_type = "INT"
    _sock(idx.inputs, "Min", "INT").default_value = 0
    _sock(idx.inputs, "Max", "INT").default_value = 9999
    iop = N.new("GeometryNodeInstanceOnPoints")
    Lk.new(setpos.outputs["Geometry"], iop.inputs["Points"])
    Lk.new(sw.outputs[0], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    Lk.new(_sock(idx.outputs, "Value", "INT"), iop.inputs["Instance Index"])
    Lk.new(rot.outputs[0], iop.inputs["Rotation"])
    Lk.new(zufall(0.8, 1.3, 17), iop.inputs["Scale"])
    Lk.new(iop.outputs["Instances"], go.inputs["Geometry"])
    return ng


def ballen_bibliothek():
    """Leichte Blattballen für den Modus Laufen (wenige große Instanzen, geformte Blätter, kein Alpha)."""
    m = bpy.data.materials["M_Hecke_Blatt"]
    leere("Bib_Heckenblatt_Lauf")
    rnd = random.Random(53)
    for k in range(4):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        for i in range(95):
            w = i * 2.39996
            r = 0.28 * math.sqrt(rnd.random())
            basis = Vector((math.cos(w) * r, math.sin(w) * r, rnd.uniform(-0.08, 0.05)))
            richtung = Vector((math.cos(w), math.sin(w), rnd.uniform(-0.2, 0.3))).normalized()
            normale = Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 1.0)).normalized()
            normale = (normale - richtung * normale.dot(richtung)).normalized()
            _blatt(bm, uv, basis, richtung, normale, rnd.uniform(0.07, 0.1), rnd.uniform(0.04, 0.055), 0.25)
        mesh_aus_bmesh(f"Heckenballen_Lauf_{k}", bm, "Bib_Heckenblatt_Lauf", mats=[m])


def baue():
    leere("01c_Heckenkern")
    leere("05g_Hecke")
    blatt = blattmaterial()
    kern_m = kernmaterial()
    zweig_bibliothek(mat=blatt)
    ballen_bibliothek()
    ng = hecken_knoten()
    hoehe, tiefe = L.HECKE_MASS["hoehe"], L.HECKE_MASS["tiefe"]
    for i, (a, b) in enumerate(L.HECKEN):
        a, b = Vector(a), Vector(b)
        laenge = (b - a).length + 0.6  # Enden überlappen an den Ecken
        kern = mesh_aus_bmesh(f"Hecke_{i + 1}_Kern", kern_mesh(laenge, tiefe, hoehe, i), "01c_Heckenkern",
                              mats=[kern_m])
        for poly in kern.data.polygons:  # weich schattieren – keine sichtbaren Rechteckflächen
            poly.use_smooth = True
        kern.location = ((a.x + b.x) / 2, (a.y + b.y) / 2, 0.0)
        kern.rotation_euler = (0.0, 0.0, math.atan2(b.y - a.y, b.x - a.x))
        laub = bpy.data.objects.new(f"Hecke_{i + 1}_Laub", kern.data)
        bpy.data.collections["05g_Hecke"].objects.link(laub)
        laub.location, laub.rotation_euler = kern.location, kern.rotation_euler
        mod = laub.modifiers.new("Hecke", "NODES")
        mod.node_group = ng
        gn_setze(mod, "Bibliothek", bpy.data.collections["Bib_Heckenzweig"])
        gn_setze(mod, "Bibliothek_Lauf", bpy.data.collections["Bib_Heckenblatt_Lauf"])
        gn_setze(mod, "Seed", 60 + i)
        gn_setze(mod, "Tiefe", 0.06)
        treiber_modus(laub, f'modifiers["Hecke"]["{gn_kennung(ng, "Dichte")}"]', "12.0 + (600.0 - 12.0) * m")
        treiber_modus(laub, f'modifiers["Hecke"]["{gn_kennung(ng, "Lauf_Bibliothek")}"]', "1.0 - m")
    return {"hecken": len(L.HECKEN)}
