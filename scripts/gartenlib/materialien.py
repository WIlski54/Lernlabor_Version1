"""PBR-Materialien aus Poly-Haven-Texturen. Box-Projektion auf Objektkoordinaten (keine UVs nötig)."""
import glob
import json
import os

import bpy

from .util import pfad

TEXTUR_MATS = {
    # feiner Körnungsputz (Außen): kleine Skala, kräftiges Relief, warmweiß, nur dezente Verschmutzung
    "M_Putz": dict(rolle="tex_aussenputz", skala=0.9, tint=(1.12, 1.09, 1.02), bump=0.9, rauheit_min=0.8, schmutz=0.22),
    "M_Sockel": dict(rolle="tex_putz", skala=1.5, tint=(0.2, 0.2, 0.21), schmutz=0.3),
    "M_Holzfassade": dict(rolle="tex_holzfassade", skala=2.0, vertikal=True, insel_variation=0.18),
    "M_Traufe": dict(rolle="tex_holzfassade", skala=2.0, tint=(0.95, 0.8, 0.65), vertikal=True),
    "M_Dachblech": dict(rolle="tex_dachblech", skala=1.5, tint=(0.25, 0.25, 0.27)),
    "M_Dachziegel": dict(rolle="tex_dachziegel", skala=1.5),
    "M_Holzdeck": dict(rolle="tex_holzdeck", skala=2.0),
    "M_Trittplatten": dict(rolle="tex_trittstein", skala=1.0, verschiebung=0.005),
    "M_Weg_Platten": dict(rolle="tex_weg", skala=2.0, tint=(0.45, 0.45, 0.47), rauheit_min=0.6),
    "M_Polygonalplatten": dict(rolle="tex_steinplatten", skala=2.5, tint=(0.13, 0.13, 0.14), rauheit_min=0.8, bump=1.0),
    "M_Beet": dict(rolle="tex_beet", skala=1.5, tint=(0.45, 0.4, 0.35)),
    # Boden unter dem Rasen grasgrün getönt: beim Laufen (leichte Rasenstücke) fallen Lücken so nicht auf
    "M_Erde": dict(rolle="tex_beet", skala=1.5, tint=(0.2, 0.42, 0.08)),
    "M_Rinde_Ahorn": dict(rolle="tex_rinde_ahorn", skala=0.8),
    "M_Parkett": dict(rolle="tex_parkett", skala=2.0),
    "M_Teppich": dict(rolle="tex_teppich", skala=0.6, rauheit_min=0.85),
    "M_Teppich_Hochflor": dict(rolle="tex_teppich_hochflor", skala=0.35, bump=1.0, rauheit_min=0.9),
    "M_Teppich_Boucle": dict(rolle="tex_teppich_boucle", skala=0.45, bump=0.8, rauheit_min=0.9),
    # dunkles Jacquard-Muster aufhellen (Helligkeit × 2,2 + 0,55), dann salbeigrün tönen
    "M_Tapete": dict(rolle="tex_tapete", skala=0.55, grau=(2.2, 0.55), tint=(0.66, 0.72, 0.6), bump=0.25, rauheit_min=0.75),
    "M_Eiche": dict(rolle="tex_parkett", skala=1.5, vertikal=True, insel_variation=0.12),
    "M_Vorhang": dict(rolle="tex_vorhang", skala=0.8, grau=True, tint=(0.95, 0.91, 0.84), rauheit_min=0.85),
    "M_Arbeitsplatte": dict(rolle="tex_arbeitsplatte", skala=3.0, rauheit_min=0.25),
}


def auswahl():
    with open(pfad("assets", "auswahl.json"), encoding="utf-8") as f:
        return json.load(f)


def _karte(ordner, kennung):
    for datei in sorted(glob.glob(os.path.join(ordner, "*"))):
        if kennung in os.path.basename(datei).lower():
            return datei
    return None


def _sock(sammlung, name, typ):
    for s in sammlung:
        if s.name == name and s.type == typ and getattr(s, "enabled", True):
            return s
    raise KeyError(f"{name}/{typ}")


def mix_farbe(nt, a, b, fac=1.0, art="MIX"):
    """a, b: Ausgangs-Socket oder RGB-Tupel; fac: Zahl oder Socket. Liefert den Ergebnis-Socket."""
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = art
    for name, wert in (("A", a), ("B", b)):
        s = _sock(n.inputs, name, "RGBA")
        if isinstance(wert, tuple):
            s.default_value = (*wert[:3], 1.0)
        else:
            nt.links.new(wert, s)
    f = _sock(n.inputs, "Factor", "VALUE")
    if isinstance(fac, (int, float)):
        f.default_value = fac
    else:
        nt.links.new(fac, f)
    return _sock(n.outputs, "Result", "RGBA")


def mathe(nt, op, a, b=0.0, c=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, w in enumerate((a, b, c)):
        if w is None:
            continue
        if isinstance(w, (int, float)):
            n.inputs[i].default_value = w
        else:
            nt.links.new(w, n.inputs[i])
    return n.outputs[0]


def _bild(nt, datei, farbe, vektor):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(datei, check_existing=True)
    n.image.colorspace_settings.name = "sRGB" if farbe else "Non-Color"
    n.projection = "BOX"
    n.projection_blend = 0.3
    nt.links.new(vektor, n.inputs["Vector"])
    return n


def _fugen_maske(nt, vektor, art, groesse):
    """1 = Fuge, 0 = Platte."""
    if art == "voronoi":
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.voronoi_dimensions = "2D"
        v.feature = "DISTANCE_TO_EDGE"
        v.inputs["Scale"].default_value = 1.0 / groesse
        v.inputs["Randomness"].default_value = 0.85
        nt.links.new(vektor, v.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 0.015 / groesse
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        nt.links.new(v.outputs["Distance"], mr.inputs["Value"])
        return mr.outputs["Result"]
    b = nt.nodes.new("ShaderNodeTexBrick")
    b.offset = 0.0
    b.squash = 1.0
    b.inputs["Scale"].default_value = 1.0
    b.inputs["Mortar Size"].default_value = 0.006
    b.inputs["Mortar Smooth"].default_value = 0.1
    b.inputs["Brick Width"].default_value = groesse
    b.inputs["Row Height"].default_value = groesse
    nt.links.new(vektor, b.inputs["Vector"])
    return b.outputs["Fac"]


def _zell_variation(nt, vektor, groesse):
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.voronoi_dimensions = "2D"
    v.inputs["Scale"].default_value = 1.0 / groesse
    v.inputs["Randomness"].default_value = 0.85
    nt.links.new(vektor, v.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.75
    mr.inputs["To Max"].default_value = 1.2
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(v.outputs["Color"], sep.inputs[0])
    nt.links.new(sep.outputs[0], mr.inputs["Value"])
    return mr.outputs["Result"]


def _schmutz(nt, farbe, staerke):
    """Dunkelt Fassaden unten (Spritzwasser) und in Ecken/Fugen (Ambient Occlusion) leicht ab."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    unten = nt.nodes.new("ShaderNodeMapRange")
    unten.inputs["From Min"].default_value = 0.0
    unten.inputs["From Max"].default_value = 0.7
    unten.inputs["To Min"].default_value = 1.0
    unten.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], unten.inputs["Value"])
    rausch = nt.nodes.new("ShaderNodeTexNoise")
    rausch.inputs["Scale"].default_value = 3.0
    rausch.inputs["Detail"].default_value = 6.0
    f_unten = mathe(nt, "MULTIPLY", mathe(nt, "MULTIPLY", unten.outputs["Result"], rausch.outputs["Fac"]), staerke * 1.6)
    farbe = mix_farbe(nt, farbe, (0.55, 0.52, 0.47), mathe(nt, "MINIMUM", f_unten, 1.0), "MULTIPLY")
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.4
    f_ao = mathe(nt, "MULTIPLY", mathe(nt, "SUBTRACT", 1.0, ao.outputs["AO"]), staerke)
    return mix_farbe(nt, farbe, (0.5, 0.48, 0.45), f_ao, "MULTIPLY")


def _insel_variation(nt, farbe, k):
    """Helligkeit je Mesh-Insel (z. B. je Fassadenbrett) um ±k variieren."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 1.0 - k
    mr.inputs["To Max"].default_value = 1.0 + k
    nt.links.new(geo.outputs["Random Per Island"], mr.inputs["Value"])
    kom = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(mr.outputs["Result"], kom.inputs[i])
    return mix_farbe(nt, farbe, kom.outputs[0], 1.0, "MULTIPLY")


def pbr(name, rolle, skala=1.0, tint=None, vertikal=False, verschiebung=0.0, bump=0.4, fugen=None, fugen_groesse=0.6,
        rauheit_min=0.0, insel_variation=0.0, schmutz=0.0, grau=False):
    ordner = pfad("assets", "polyhaven", "textures", auswahl()[rolle])
    diff = _karte(ordner, "_diff_")
    if diff is None:
        raise FileNotFoundError(f"Keine Diffuse-Textur in {ordner}")
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_fake_user = True
    nt = m.node_tree
    nt.nodes.clear()
    aus = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], aus.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    obj_vek = tc.outputs["Object"]
    vek = obj_vek
    if vertikal:  # Bretter senkrecht: (Z, Z, X+Y) – vertauscht die Achsen auf allen Wandseiten
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(vek, sep.inputs[0])
        kom = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(sep.outputs["Z"], kom.inputs["X"])
        nt.links.new(sep.outputs["Z"], kom.inputs["Y"])
        nt.links.new(mathe(nt, "ADD", sep.outputs["X"], sep.outputs["Y"]), kom.inputs["Z"])
        vek = kom.outputs[0]
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / skala,) * 3
    nt.links.new(vek, mp.inputs["Vector"])
    vek = mp.outputs["Vector"]

    farbe = _bild(nt, diff, True, vek).outputs["Color"]
    if grau:  # Farbe der Textur verwerfen, nur Helligkeitsstruktur behalten (z. B. blaues Leinen → cremeweiß)
        faktor, versatz = grau if isinstance(grau, tuple) else (1.6, 0.0)
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(farbe, bw.inputs[0])
        hell = mathe(nt, "MULTIPLY_ADD", bw.outputs[0], faktor, versatz)
        kom = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3):
            nt.links.new(hell, kom.inputs[i])
        farbe = kom.outputs[0]
    if tint:
        farbe = mix_farbe(nt, farbe, tint, 1.0, "MULTIPLY")
    if insel_variation > 0:
        farbe = _insel_variation(nt, farbe, insel_variation)
    if schmutz > 0:
        farbe = _schmutz(nt, farbe, schmutz)
    rough_datei = _karte(ordner, "_rough_")
    rauheit = _bild(nt, rough_datei, False, vek).outputs["Color"] if rough_datei else 0.7
    disp_datei = _karte(ordner, "_disp_")
    hoehe = _bild(nt, disp_datei, False, vek).outputs["Color"] if disp_datei else None

    if fugen:
        maske = _fugen_maske(nt, obj_vek, fugen, fugen_groesse)
        if fugen == "voronoi":
            var = _zell_variation(nt, obj_vek, fugen_groesse)
            kom = nt.nodes.new("ShaderNodeCombineColor")
            for i in range(3):
                nt.links.new(var, kom.inputs[i])
            farbe = mix_farbe(nt, farbe, kom.outputs[0], 1.0, "MULTIPLY")
        farbe = mix_farbe(nt, farbe, (0.025, 0.025, 0.025), maske)
        rauheit = mathe(nt, "MAXIMUM", rauheit, mathe(nt, "MULTIPLY", maske, 0.95))
        hoehe = mathe(nt, "SUBTRACT", hoehe if hoehe is not None else 0.5, mathe(nt, "MULTIPLY", maske, 0.6))

    if rauheit_min > 0 and not isinstance(rauheit, float):
        rauheit = mathe(nt, "MAXIMUM", rauheit, rauheit_min)
    nt.links.new(farbe, bsdf.inputs["Base Color"])
    if isinstance(rauheit, float):
        bsdf.inputs["Roughness"].default_value = rauheit
    else:
        nt.links.new(rauheit, bsdf.inputs["Roughness"])
    if hoehe is not None:
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.02
        nt.links.new(hoehe, bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
        if verschiebung > 0:
            d = nt.nodes.new("ShaderNodeDisplacement")
            d.inputs["Midlevel"].default_value = 0.5
            d.inputs["Scale"].default_value = verschiebung
            nt.links.new(hoehe, d.inputs["Height"])
            nt.links.new(d.outputs[0], aus.inputs["Displacement"])
            m.displacement_method = "BOTH"
    return m


def modelltexturen_verkleinern(max_px=1024):
    """Texturen der Poly-Haven-Modelle (Möbel, Deko, Sträucher) als verkleinerte Kopien unter
    assets/polyhaven/models_1k/ speichern und die Bilder darauf umstellen – spart GPU-Speicher in Cycles.
    Die Originale bleiben unverändert; bereits verkleinerte Kopien werden wiederverwendet."""
    import os
    quelle = os.path.normcase(pfad("assets", "polyhaven", "models"))
    ziel_basis = pfad("assets", "polyhaven", f"models_{max_px // 1024}k")
    umgestellt, gespart = 0, 0.0
    for im in bpy.data.images:
        if im.source != "FILE" or not im.filepath:
            continue
        abs_pfad = os.path.normcase(os.path.abspath(bpy.path.abspath(im.filepath)))
        if not abs_pfad.startswith(quelle) or max(im.size) <= max_px:
            continue
        rel = os.path.relpath(abs_pfad, quelle)
        neu = os.path.join(ziel_basis, rel)
        w, h = im.size
        k = max_px / max(w, h)
        bpp = 16 if im.is_float else 4
        if not os.path.exists(neu):
            os.makedirs(os.path.dirname(neu), exist_ok=True)
            kopie = im.copy()
            kopie.scale(max(1, int(w * k)), max(1, int(h * k)))
            kopie.filepath_raw = neu
            kopie.file_format = im.file_format
            kopie.save()
            bpy.data.images.remove(kopie)
        im.filepath = neu
        im.reload()
        umgestellt += 1
        gespart += w * h * bpp * (1 - k * k) / 1e6
    return {"umgestellt": umgestellt, "gespart_mb": round(gespart)}


def baue():
    erg = {}
    for name, opts in TEXTUR_MATS.items():
        pbr(name, **opts)
        erg[name] = "ok"
    return erg
