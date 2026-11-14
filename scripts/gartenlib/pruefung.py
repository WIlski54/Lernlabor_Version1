"""Prüfungen je Aufgabe. Jede Funktion liefert {"ok": bool, "fehler": [...]}."""
import json
import os

import bpy
from mathutils import Vector

from .util import modus_setzen, pfad


def _e(fehler, **mehr):
    return {"ok": not fehler, "fehler": fehler, **mehr}


def einrichtung():
    f = []
    cp = bpy.context.preferences.addons["cycles"].preferences
    if cp.compute_device_type != "OPTIX":
        f.append(f"Gerätetyp {cp.compute_device_type}")
    if not any(d.use and d.type == "OPTIX" and "4090" in d.name for d in cp.devices):
        f.append("RTX 4090 nicht als OptiX-Gerät aktiv")
    sc = bpy.context.scene
    if sc.cycles.device != "GPU":
        f.append("Cycles nicht auf GPU")
    if sc.view_settings.view_transform != "AgX":
        f.append("kein AgX")
    if not bpy.data.filepath.lower().endswith("garten.blend"):
        f.append("garten.blend nicht gespeichert")
    return _e(f)


def struktur():
    from .setup import SAMMLUNGEN
    f = [n for n, _ in SAMMLUNGEN if n not in bpy.data.collections]
    st = bpy.data.objects.get("Steuerung")
    if st is None or "modus" not in st:
        f.append("Steuerung/modus fehlt")
    for n in ("Cube", "Light"):
        if n in bpy.data.objects:
            f.append(f"Standardobjekt {n} noch vorhanden")
    if "Maske_Rasen" in bpy.data.collections:
        for n in ("02_Architektur", "04_Hardscape", "01a_Beete"):
            if n not in bpy.data.collections["Maske_Rasen"].children:
                f.append(f"Maske_Rasen ohne {n}")
    return _e(f)


def architektur():
    from . import layout as L
    f = [f"fehlt {n}" for n in ("Haus", "Haus_EG", "Haus_OG", "Haus_Dach", "Vordach_Dach",
                                 "Fluegel", "Fluegel_Dach", "Carport_Dach") if n not in bpy.data.objects]
    if f:
        return _e(f)
    H = L.HAUS
    tuer = next(o for o in L.HAUS_EG_OEFFNUNGEN if o[5] == "tuer_offen")
    x_offen = tuer[1] - tuer[3] / 4  # offene Hälfte der Terrassentür
    haus = bpy.data.objects["Haus"]
    start = haus.matrix_world @ Vector((x_offen, -H["tiefe"] / 2 - 1.0, 1.2))
    richtung = (haus.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
    dg = bpy.context.evaluated_depsgraph_get()
    treffer, ort, *_ = bpy.context.scene.ray_cast(dg, start, richtung)
    if not treffer:
        f.append("Strahl durch die Terrassentür trifft nichts (Rückwand fehlt?)")
    elif (ort - start).length < 3.0:
        f.append(f"Terrassentür blockiert, Treffer nach {(ort - start).length:.2f} m")
    if not any(o.name.startswith("Glas_") for o in bpy.data.objects):
        f.append("keine Glasscheiben")
    return _e(f)


def hardscape():
    from . import layout as L
    namen = ["Hof_Platten", "Weg_Fluegel", "Carport_Boden", "Terrasse", "Feuerschale",
             "Feuerschale_Fuss", "Feuerschale_Holz", "Trittplatte_01"]
    namen += [f"Sessel_{i}" for i in range(1, 5)] + [f"Poller_{i}" for i in range(1, len(L.POLLER) + 1)]
    f = [f"fehlt {n}" for n in namen if n not in bpy.data.objects]
    if not f:
        mitte = Vector((*L.HOF["mitte"], 0))
        for i in range(1, 5):
            o = bpy.data.objects[f"Sessel_{i}"]
            d = (Vector((o.location.x, o.location.y, 0)) - mitte).length
            if not 1.5 <= d <= 2.4:
                f.append(f"Sessel_{i} {d:.2f} m von der Feuerschale")
    return _e(f)


def kamera():
    from . import layout as L
    o = bpy.data.objects.get("Kamera_Referenz")
    f = []
    if o is None:
        return _e(["Kamera_Referenz fehlt"])
    if bpy.context.scene.camera != o:
        f.append("nicht Szenenkamera")
    if abs(o.data.lens - L.KAMERA["brennweite"]) > 0.01:
        f.append("falsche Brennweite")
    return _e(f)


def _auswahl():
    p = pfad("assets", "auswahl.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def assets():
    a = _auswahl()
    if a is None:
        return _e(["assets/auswahl.json fehlt"])
    f = []
    typen = {"hdri": "hdris", "tex": "textures", "modelle": "models"}
    for rolle, ids in a.items():
        typ = typen[rolle.split("_")[0]]
        for aid in ([ids] if isinstance(ids, str) else ids):
            ordner = pfad("assets", "polyhaven", typ, aid)
            if not os.path.isdir(ordner) or not os.listdir(ordner):
                f.append(f"{rolle}: {aid} nicht geladen")
    return _e(f)


def materialien():
    from .materialien import TEXTUR_MATS
    f = []
    for name in TEXTUR_MATS:
        m = bpy.data.materials.get(name)
        if m is None:
            f.append(f"fehlt {name}")
            continue
        bilder = [n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE"]
        if not bilder:
            f.append(f"{name} ohne Bildtextur")
        for b in bilder:
            if b is None or not os.path.exists(bpy.path.abspath(b.filepath)):
                f.append(f"{name}: Bilddatei fehlt")
    return _e(f)


def welt():
    f = []
    w = bpy.context.scene.world
    env = [n for n in w.node_tree.nodes if n.type == "TEX_ENVIRONMENT"] if w else []
    if not env or env[0].image is None or not os.path.exists(bpy.path.abspath(env[0].image.filepath)):
        f.append("HDRI fehlt")
    for n in ("Sonne", "Dunst"):
        if n not in bpy.data.objects:
            f.append(f"fehlt {n}")
    return _e(f)


def _instanzen(praefix_oder_obj):
    dg = bpy.context.evaluated_depsgraph_get()
    erg = []
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent:
            name = inst.parent.original.name
            if name == praefix_oder_obj or name.startswith(praefix_oder_obj + "_"):
                erg.append(inst.matrix_world.translation.copy())
    return erg


def rasen():
    from . import layout as L
    f = []
    o = bpy.data.objects.get("Rasen")
    if o is None or "Rasen" not in o.modifiers:
        return _e(["Rasen oder Modifier fehlt"])
    if len(bpy.data.collections["Bib_Halme"].objects) < 8:
        f.append("weniger als 8 Halmbüschel")
    alt = bpy.data.objects["Steuerung"]["modus"]
    modus_setzen(0.0)
    punkte = _instanzen("Rasen")
    modus_setzen(alt)
    mitte = Vector((*L.HOF["mitte"], 0))
    auf_hof = sum(1 for p in punkte if (Vector((p.x, p.y, 0)) - mitte).length < L.HOF["radius"] - 0.3)
    if len(punkte) < 3000:  # im Modus Laufen bewusst wenige große Rasenstücke (0,8 m) statt vieler Büschel
        f.append(f"nur {len(punkte)} Rasen-Instanzen im Modus Laufen")
    if auf_hof:
        f.append(f"{auf_hof} Grasbüschel wachsen auf den Hofplatten")
    return _e(f, instanzen=len(punkte))


def bepflanzung():
    from . import layout as L
    f = []
    for bib, mindest in (("Bib_Graeser", 5), ("Bib_Stauden", 4)):
        if len(bpy.data.collections[bib].objects) < mindest:
            f.append(f"{bib} hat zu wenige Varianten")
    alt = bpy.data.objects["Steuerung"]["modus"]
    modus_setzen(0.0)
    for beet in L.BEPFLANZUNG:
        if not _instanzen(f"Pflanzung_{beet}"):
            f.append(f"{beet} ohne Pflanzen")
    modus_setzen(alt)
    return _e(f)


def polster():
    objs = list(bpy.data.collections["Bib_Polster"].objects)
    f = [] if objs else ["Bib_Polster leer"]
    for o in objs:
        breite = max(o.dimensions.x, o.dimensions.y)
        if not 0.8 <= breite <= 1.2:
            f.append(f"{o.name} nicht normiert ({breite:.2f} m)")
    return _e(f)


def baeume():
    from . import layout as L
    f = []
    for name, _art, _ort, hoehe, _seed in L.BAEUME:
        o = bpy.data.objects.get(name)
        if o is None:
            f.append(f"fehlt {name}")
            continue
        laub = bpy.data.objects.get(f"{name}_Laub")
        if laub is None:
            f.append(f"{name} ohne Laub")
        h = max((o.matrix_world @ Vector(c)).z for c in o.bound_box)
        if laub:
            h = max(h, max((laub.matrix_world @ Vector(c)).z for c in laub.bound_box))
        if abs(h - hoehe) > 0.15 * hoehe:
            f.append(f"{name}: Höhe {h:.1f} m statt {hoehe} m")
    return _e(f)


def qualitaetsprobe():
    p = pfad("renders", "qualitaetsprobe.png")
    return _e([] if os.path.exists(p) else ["renders/qualitaetsprobe.png fehlt"])


def kulisse():
    from . import layout as L
    f = []
    if "Wiese" not in bpy.data.objects:
        f.append("Wiese fehlt")
    hecken = [o for o in bpy.data.objects if o.name.startswith("Hecke_") and o.name.endswith("_Laub")]
    if len(hecken) < len(L.HECKEN):
        f.append(f"nur {len(hecken)} Hecken mit Laub")
    baeume = [o for o in bpy.data.collections["05f_Kulisse"].objects
              if o.name.startswith("Kulisse_") and not o.name.endswith("_Laub")]
    if len(baeume) < L.KULISSE["anzahl"]:
        f.append(f"nur {len(baeume)} Kulissenbäume")
    return _e(f)


def innenraum():
    from . import layout as L
    f = [f"fehlt {n}" for n in ("Innen_Boden", "Innen_Kueche", "Kamera_Innen", "Innen_GI", "Innen_Reflexion")
         if n not in bpy.data.objects]
    moebel = [o for o in bpy.data.objects if o.name.startswith("Moebel_")]
    if len(moebel) < 6:
        f.append(f"nur {len(moebel)} Möbel")
    for name, *_ in L.INNEN["lichter"]:
        if name not in bpy.data.objects:
            f.append(f"fehlt {name}")
    tuer = architektur()
    if not tuer["ok"]:
        f += tuer["fehler"]
    return _e(f, moebel=len(moebel))


def lauf():
    f = []
    wn = bpy.context.preferences.inputs.walk_navigation
    if not wn.use_gravity:
        f.append("Schwerkraft beim Laufen aus")
    if abs(wn.view_height - 1.7) > 0.01:
        f.append("Augenhöhe nicht 1,70 m")
    if "Kamera_Laufen" not in bpy.data.objects:
        f.append("Kamera_Laufen fehlt")
    fps = bpy.data.objects["Steuerung"].get("fps_laufen", 0.0)
    if fps < 25.0:
        f.append(f"nur {fps:.1f} fps im Modus Laufen")
    return _e(f, fps=fps)


def labor():
    f = [f"fehlt {n}" for n in ("Labor_Boden", "Labor_Mikroskop", "Whiteboard_Flaeche", "Labor_Arbeitsinsel_Platte",
                                 "Labor_Sammelglaeser") if n not in bpy.data.objects]
    if any(o.name.startswith("Moebel_") for o in bpy.data.objects):
        f.append("Wohnungsmöbel noch vorhanden")
    if not bpy.data.filepath.lower().endswith("labor.blend"):
        f.append("nicht in labor.blend")
    tuer = architektur()
    if not tuer["ok"]:
        f += tuer["fehler"]
    return _e(f)
