"""Forschungslabor im Erdgeschoss (ersetzt die Wohnungseinrichtung). Nur in labor.blend ausführen!"""
import bmesh
import bpy
from mathutils import Vector

from . import layout as L
from .architektur import _quer, _wandpunkt, fase
from .util import bm_box, boxen_objekt, leere, material, mesh_aus_bmesh, neues_objekt

S = "03_Innenraum"


def _pruefe_datei():
    if not bpy.data.filepath.lower().endswith("labor.blend"):
        raise RuntimeError("labor.baue() nur in labor.blend ausführen – garten.blend bleibt unverändert!")


def _mats():
    return {
        "boden": material("M_Laborboden", (0.5, 0.52, 0.53), 0.45),
        "platte": material("M_Labortisch_Platte", (0.12, 0.12, 0.13), 0.35),
        "gestell": material("M_Labor_Gestell", (0.75, 0.76, 0.78), 0.35, 1.0),
        "korpus": material("M_Labor_Korpus", (0.8, 0.8, 0.78), 0.5),
        "board": material("M_Whiteboard", (0.92, 0.92, 0.92), 0.12),
        "alu": material("M_Beschlag", (0.62, 0.62, 0.63), 0.3, 1.0),
        "weiss": material("M_Mikroskop_Weiss", (0.86, 0.86, 0.84), 0.3),
        "schwarz": material("M_Mikroskop_Schwarz", (0.02, 0.02, 0.02), 0.35),
        "glas": bpy.data.materials["M_Glas"],
        "deckel": material("M_Glas_Deckel", (0.05, 0.08, 0.06), 0.5),
        "licht": material("M_Lichtpaneel", (1.0, 1.0, 1.0), 0.5),
        "decke": material("M_Decke", (0.82, 0.81, 0.78), 0.9),
        "hocker": material("M_Hocker", (0.15, 0.3, 0.45), 0.5),
    }


def _tisch(name, haus, mitte, groesse, m, hoehe=0.9):
    """Labortisch: dunkle Platte, Metallgestell mit vier Beinen und Zarge."""
    x, y = mitte
    b, t = groesse
    z = L.INNEN["boden_z"] + 0.02
    platte = [((b, t, 0.03), (x, y, z + hoehe - 0.015))]
    gestell = [((0.05, 0.05, hoehe - 0.03), (x + sx * (b / 2 - 0.06), y + sy * (t / 2 - 0.06), z + (hoehe - 0.03) / 2))
               for sx in (-1, 1) for sy in (-1, 1)]
    gestell += [((b - 0.1, 0.03, 0.08), (x, y + sy * (t / 2 - 0.06), z + hoehe - 0.07)) for sy in (-1, 1)]
    fase(boxen_objekt(f"Labor_{name}_Platte", platte, S, haus, m["platte"]), 0.004, 2)
    fase(boxen_objekt(f"Labor_{name}_Gestell", gestell, S, haus, m["gestell"]), 0.003, 1)


def _hocker(name, haus, ort, m):
    from .fassade import _rohr
    x, y = ort
    z = L.INNEN["boden_z"] + 0.02
    bm = bmesh.new()
    _rohr(bm, Vector((x, y, z + 0.6)), Vector((x, y, z + 0.66)), 0.18, 20)
    _rohr(bm, Vector((x, y, z)), Vector((x, y, z + 0.6)), 0.025, 10)
    _rohr(bm, Vector((x, y, z)), Vector((x, y, z + 0.02)), 0.22, 20)
    fase(mesh_aus_bmesh(f"Labor_{name}", bm, S, haus, [m["hocker"]]), 0.004, 1)


def _mikroskop(haus, ort, z, m):
    """Schematisches, gut erkennbares Durchlichtmikroskop; Okulare zeigen nach -y (zum Nutzer)."""
    from .fassade import _rohr
    x, y = ort
    weiss, schwarz = bmesh.new(), bmesh.new()
    bm_box(weiss, (0.18, 0.24, 0.035), (x, y, z + 0.0175))                 # Fuß
    bm_box(weiss, (0.05, 0.06, 0.3), (x, y + 0.08, z + 0.185))             # Stativ
    bm_box(weiss, (0.07, 0.12, 0.06), (x, y + 0.03, z + 0.35))             # Kopf
    bm_box(schwarz, (0.14, 0.13, 0.012), (x, y - 0.01, z + 0.15))          # Objekttisch
    _rohr(schwarz, Vector((x, y - 0.01, z + 0.035)), Vector((x, y - 0.01, z + 0.06)), 0.02)   # Leuchte
    _rohr(schwarz, Vector((x, y - 0.02, z + 0.3)), Vector((x, y - 0.02, z + 0.27)), 0.032)    # Revolver
    for dx in (-0.018, 0.0, 0.018):                                                           # Objektive
        _rohr(schwarz, Vector((x + dx, y - 0.02, z + 0.27)), Vector((x + dx, y - 0.02, z + 0.225)), 0.008)
    _rohr(weiss, Vector((x, y + 0.0, z + 0.37)), Vector((x, y - 0.06, z + 0.44)), 0.02)       # Tubus
    for dx in (-0.024, 0.024):                                                                # Okulare
        _rohr(schwarz, Vector((x + dx, y - 0.06, z + 0.44)), Vector((x + dx * 1.2, y - 0.09, z + 0.48)), 0.012)
    _rohr(schwarz, Vector((x - 0.055, y + 0.08, z + 0.13)), Vector((x + 0.055, y + 0.08, z + 0.13)), 0.022)  # Triebknöpfe
    o1 = mesh_aus_bmesh("Labor_Mikroskop", weiss, S, haus, [m["weiss"]])
    o2 = mesh_aus_bmesh("Labor_Mikroskop_Teile", schwarz, S, haus, [m["schwarz"]])
    for o in (o1, o2):
        fase(o, 0.003, 1)


def _whiteboard(haus, m):
    """Whiteboard an der Westwand: Rahmen, Ablage und eine eigene Fläche mit UVs 0…1 (Web-App malt darauf)."""
    I = L.INNEN
    p, n = _wandpunkt("W", -2.0, I["breite"], I["tiefe"])          # W: y = -versatz → y = 2.0
    zc, b, h = I["boden_z"] + 1.55, 3.0, 1.2
    a = Vector((-n.y, n.x, 0.0))
    rahmen = [(_quer(n, b + 0.05, 0.03, 0.025), p - n * 0.015 + Vector((0, 0, zc + sz * (h / 2 + 0.0125))))
              for sz in (-1, 1)]
    rahmen += [(_quer(n, 0.025, 0.03, h + 0.05), p - n * 0.015 + a * sx * (b / 2 + 0.0125) + Vector((0, 0, zc)))
               for sx in (-1, 1)]
    rahmen.append((_quer(n, b, 0.07, 0.02), p - n * 0.04 + Vector((0, 0, zc - h / 2 - 0.035))))   # Ablage
    fase(boxen_objekt("Labor_Whiteboard_Rahmen", rahmen, S, haus, m["alu"]), 0.003, 1)
    boxen_objekt("Labor_Whiteboard_Traeger", [(_quer(n, b, 0.015, h), p - n * 0.0075 + Vector((0, 0, zc)))],
                 S, haus, m["board"])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rechts = n.cross(Vector((0, 0, 1)))                              # von vorn (aus dem Raum) gesehen rechts
    ecken = [p - n * 0.016 + rechts * sa * b / 2 + Vector((0, 0, zc + sz * h / 2))
             for sa, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]   # gegen den Uhrzeigersinn → Normale zum Raum
    f = bm.faces.new([bm.verts.new(e) for e in ecken])
    for loop, k in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = k
    f.normal_update()                                                # faces.new rechnet keine Normale
    if f.normal.dot(-n) < 0:
        f.normal_flip()
    mesh_aus_bmesh("Whiteboard_Flaeche", bm, S, haus, [m["board"]])


def _regal_mit_glaesern(haus, m):
    """Wandregal an der Ostwand über der Arbeitszeile, darauf Sammelgläser mit Deckeln."""
    from .fassade import _rohr
    I = L.INNEN
    boards = []
    glaeser, deckel = bmesh.new(), bmesh.new()
    for h in (1.45, 1.85):
        z = I["boden_z"] + h
        boards.append(((0.28, 2.6, 0.03), (5.56, -2.45, z - 0.015)))
        for k in range(7):
            y = -3.6 + k * 0.38
            _rohr(glaeser, Vector((5.56, y, z)), Vector((5.56, y, z + 0.12)), 0.045, 16)
            _rohr(deckel, Vector((5.56, y, z + 0.12)), Vector((5.56, y, z + 0.135)), 0.047, 16)
    fase(boxen_objekt("Labor_Wandregal", boards, S, haus, m["korpus"]), 0.003, 1)
    mesh_aus_bmesh("Labor_Sammelglaeser", glaeser, S, haus, [m["glas"]])
    mesh_aus_bmesh("Labor_Glasdeckel", deckel, S, haus, [m["deckel"]])


def _licht(haus, m):
    I = L.INNEN
    paneele = []
    for x in (-3.5, 0.0, 3.5):
        for y in (-1.8, 1.8):
            name = f"Licht_Labor_{x:+.0f}_{y:+.0f}"
            li = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
            li.shape = "RECTANGLE"
            li.size, li.size_y = 1.2, 0.3
            li.energy = 110.0
            li.color = (1.0, 0.98, 0.95)
            o = neues_objekt(name, li, S, eltern=haus)
            o.location = (x, y, I["decke_z"] - 0.03)
            paneele.append(((1.2, 0.3, 0.02), (x, y, I["decke_z"] - 0.016)))
    pm = m["licht"]
    b = pm.node_tree.nodes.get("Principled BSDF")
    if b is not None:
        b.inputs["Emission Color"].default_value = (1.0, 0.98, 0.95, 1.0)
        b.inputs["Emission Strength"].default_value = 6.0
    boxen_objekt("Labor_Lichtpaneele", paneele, S, haus, pm)


def baue():
    _pruefe_datei()
    from . import innenraum
    leere(S)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    haus = bpy.data.objects["Haus"]
    I = L.INNEN
    m = _mats()
    boxen_objekt("Labor_Boden", [((I["breite"], I["tiefe"], 0.02), (0.0, 0.0, I["boden_z"] + 0.01))], S, haus, m["boden"])
    boxen_objekt("Innen_Decke", [((I["breite"], I["tiefe"], 0.01), (0.0, 0.0, I["decke_z"] - 0.006))], S, haus, m["decke"])
    innenraum._sockelleisten(haus)
    innenraum._fensterbaenke_innen(haus)
    _tisch("Mikroskoptisch", haus, (-2.0, 3.79), (2.0, 0.7), m)
    _mikroskop(haus, (-2.0, 3.72), I["boden_z"] + 0.02 + 0.9, m)
    _hocker("Hocker_Mikroskop", haus, (-2.0, 3.05), m)
    _tisch("Arbeitsinsel", haus, (0.0, 0.8), (2.4, 1.2), m)
    for i, (x, y) in enumerate(((-0.7, 0.0), (0.7, 0.0), (-0.7, 1.6), (0.7, 1.6))):
        _hocker(f"Hocker_{i + 1}", haus, (x, y), m)
    _tisch("Arbeitszeile", haus, (5.35, -2.45), (0.7, 3.1), m)
    _regal_mit_glaesern(haus, m)
    _whiteboard(haus, m)
    _licht(haus, m)
    innenraum._lichtsonden(haus, [])
    innenraum._kamera(haus)
    return {"objekte": len(bpy.data.collections[S].all_objects)}
