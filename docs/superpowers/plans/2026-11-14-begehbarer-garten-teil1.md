# Begehbarer Garten – Teil 1 (bis zur Qualitätsprobe) – Umsetzungsplan

> **Für ausführende Agenten:** BENÖTIGTER SUB-SKILL: superpowers:subagent-driven-development (empfohlen) oder superpowers:executing-plans, um den Plan Aufgabe für Aufgabe abzuarbeiten. Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Eine Blender-5.1-Szene `garten.blend` mit Haus, Seitenflügel, Carport, Hof und bepflanzten Beeten im Stil des Referenzbilds, die aus der Referenzkamera in Cycles nahezu fotorealistisch rendert.

**Architektur:** Alle Bausteine sind Python-Module im Paket `scripts/gartenlib/`. Sie werden über das Blender-MCP-Add-on im laufenden Blender importiert und ausgeführt. Jedes Modul baut genau einen Teil der Szene, leert vorher seine Collection und kann deshalb beliebig oft neu laufen. Alle Maße stehen zentral in `layout.py`. Prüfungen liegen in `pruefung.py` und liefern `{"ok": bool, "fehler": [...]}`. Renders laufen über die Kommandozeile im Hintergrund, damit Blender bedienbar bleibt.

**Tech-Stack:** Blender 5.1.1 (bpy, bmesh, Geometry Nodes, Cycles/OptiX, Eevee), Python-Standardbibliothek, Poly-Haven-API (CC0), Blender-Erweiterung „Sapling Tree Gen“.

**Umfang:** Teil 1 umfasst die Design-Schritte 1–4 (Einrichtung → Qualitätsprobe). Teil 2 (Grundstück/Kulisse, Erdgeschoss innen, Lauf-Tuning) wird erst nach der Qualitätsprobe geplant, weil deren Ergebnis den Inhalt bestimmt.

**Spec:** `docs/superpowers/specs/2026-11-14-begehbarer-garten-design.md`

---

## Konventionen

**Pfade**
- Projekt: `D:\KI Projekte\Blender MArtists`
- Blender: `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`
- Blender-Python: `C:\Program Files\Blender Foundation\Blender 5.1\5.1\python\bin\python.exe`

**MCP-Aufruf:** So wird ein Baustein mit `mcp__Blender__execute_blender_code` ausgeführt. `<modul>` und `<funktion>` werden pro Schritt ersetzt.

```python
import sys, importlib
P = r"D:\KI Projekte\Blender MArtists\scripts"
if P not in sys.path:
    sys.path.insert(0, P)
import gartenlib
importlib.reload(gartenlib)
modul = gartenlib.lade("<modul>")
result = modul.<funktion>()
```

**Prüfaufruf:** Derselbe Kopf wie beim MCP-Aufruf, danach `result = gartenlib.lade("pruefung").<pruefung>()`.

**Render:**
- Aufruf: `bash "D:/KI Projekte/Blender MArtists/scripts/render.sh" <ausgabe.png> <ENGINE> <samples> <prozent> <kamera> <modus>`
- Vorher immer `util.speichern()` ausführen, denn der Render liest die gespeicherte Datei.
- Längere Renders laufen im Hintergrund (`run_in_background`).

**Downloads:** Erst nach ausdrücklicher Freigabe durch Stephan im Chat, mit Dateiliste und Gesamtgröße.

**Git:** Versioniert werden nur `scripts/` und `docs/`. `assets/`, `renders/` und `*.blend` stehen in `.gitignore`.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `scripts/gartenlib/__init__.py` | `lade(name)`: Module neu laden (util, layout zuerst) |
| `scripts/gartenlib/util.py` | Pfade, sichere Attribut-Setzer, Collections, Box-/Mesh-Helfer, Speichern, GN-/Treiber-Helfer |
| `scripts/gartenlib/layout.py` | Alle Maße und Positionen (reine Daten) |
| `scripts/gartenlib/setup.py` | Render-Einstellungen, Collections, Steuerung |
| `scripts/gartenlib/architektur.py` | Haus, Vordach, Seitenflügel, Carport inkl. Öffnungen, Rahmen, Glas, Dächern |
| `scripts/gartenlib/hardscape.py` | Platten, Weg, Terrasse, Trittplatten, Feuerschale, Sessel, Poller |
| `scripts/gartenlib/kamera.py` | Referenzkamera |
| `scripts/polyhaven.py` | Poly-Haven-Client (eigenständig, nur Standardbibliothek) |
| `scripts/gartenlib/materialien.py` | PBR-Materialbaukasten, Fugen, Zuweisung per Materialname |
| `scripts/gartenlib/welt.py` | HDRI-Himmel, Sonne, Dunst |
| `scripts/gartenlib/gn.py` | Geometry-Nodes-Gruppe `GN_Streuen` und Anwenden mit Modus-Treiber |
| `scripts/gartenlib/gelaende.py` | Beet-Flächen |
| `scripts/gartenlib/pflanzen.py` | Pflanzenmaterialien, Halm-/Gras-/Stauden-Bibliotheken, Rasen, Bepflanzung, Poly-Haven-Sträucher |
| `scripts/gartenlib/baeume.py` | Birken und Ahorn mit Sapling, Rindenmaterialien |
| `scripts/gartenlib/pruefung.py` | Alle Prüfungen |
| `scripts/render_cli.py` | Render im Hintergrundmodus |
| `scripts/render.sh` | Bequemer Render-Aufruf |

---

### Task 0: Projektgerüst

**Dateien:**
- Neu: `scripts/gartenlib/__init__.py`, `scripts/gartenlib/util.py`, `scripts/gartenlib/pruefung.py`, `scripts/render_cli.py`, `scripts/render.sh`, `.gitignore`
- Neu: `docs/referenz/bild2.webp` (Kopie des Referenzbilds)

- [ ] **Schritt 1: Git-Repository und Ordner anlegen**

```bash
cd "/d/KI Projekte/Blender MArtists" && git init && mkdir -p scripts/gartenlib assets renders docs/referenz
cp "/c/Users/Admin/AppData/Local/Temp/claude/aca4d6597c5a6368/97169088-26ba-449c-91ad-0921067960e4/images/2.webp" docs/referenz/bild2.webp
```

`.gitignore`:

```
assets/
renders/
*.blend
*.blend1
__pycache__/
```

- [ ] **Schritt 2: `scripts/gartenlib/__init__.py` schreiben**

```python
"""Bausteine für die Gartenszene. Laden in Blender: gartenlib.lade("modul")."""
import importlib

BASIS = ["util", "layout"]


def lade(name):
    """Lädt util, layout und das gewünschte Modul neu (für iteratives Arbeiten im laufenden Blender)."""
    for basis in BASIS:
        try:
            importlib.reload(importlib.import_module(f"gartenlib.{basis}"))
        except ModuleNotFoundError:
            pass
    return importlib.reload(importlib.import_module(f"gartenlib.{name}"))
```

- [ ] **Schritt 3: `scripts/gartenlib/util.py` schreiben**

```python
"""Hilfsfunktionen für den Szenenbau."""
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

PROJEKT = r"D:\KI Projekte\Blender MArtists"


def pfad(*teile):
    return os.path.join(PROJEKT, *teile)


def setze(obj, attr, wert, log):
    """Setzt ein Attribut, falls es in dieser Blender-Version existiert; Probleme landen im Log."""
    if not hasattr(obj, attr):
        log.append(f"fehlt: {type(obj).__name__}.{attr}")
        return False
    try:
        setattr(obj, attr, wert)
        return True
    except Exception as e:  # z. B. unbekannter Enum-Wert
        log.append(f"{attr}={wert!r}: {e}")
        return False


def coll(name):
    return bpy.data.collections[name]


def collection(name, eltern=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    ziel = bpy.context.scene.collection if eltern is None else coll(eltern)
    if c.name not in ziel.children:
        ziel.children.link(c)
    return c


def layer_collection(name, lc=None):
    lc = lc or bpy.context.view_layer.layer_collection
    if lc.collection.name == name:
        return lc
    for kind in lc.children:
        treffer = layer_collection(name, kind)
        if treffer:
            return treffer
    return None


def leere(name):
    """Entfernt alle Objekte einer Collection (rekursiv) und danach verwaiste Meshes/Kurven."""
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for o in list(c.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for cu in list(bpy.data.curves):
        if cu.users == 0:
            bpy.data.curves.remove(cu)


def neues_objekt(name, daten, sammlung, eltern=None):
    o = bpy.data.objects.new(name, daten)
    coll(sammlung).objects.link(o)
    if eltern is not None:
        o.parent = eltern
    return o


def material(name, farbe=(0.8, 0.8, 0.8), rauheit=0.5, metall=0.0):
    """Holt ein Material oder legt einen einfachen Platzhalter an (Task 8 wertet ihn auf)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        try:
            m.use_nodes = True
        except Exception:
            pass
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*farbe, 1.0)
        b.inputs["Roughness"].default_value = rauheit
        b.inputs["Metallic"].default_value = metall
        m.diffuse_color = (*farbe, 1.0)
    return m


def bm_box(bm, groesse, mitte, rot=(0.0, 0.0, 0.0)):
    """Fügt einem BMesh einen Quader hinzu (zentriert auf mitte, gedreht um rot in Radiant)."""
    geo = bmesh.ops.create_cube(bm, size=1.0)
    m = Euler(rot).to_matrix()
    for v in geo["verts"]:
        lokal = Vector((v.co.x * groesse[0], v.co.y * groesse[1], v.co.z * groesse[2]))
        v.co = m @ lokal + Vector(mitte)
    return geo


def mesh_aus_bmesh(name, bm, sammlung, eltern=None, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return neues_objekt(name, me, sammlung, eltern)


def box(name, groesse, ort=(0, 0, 0), sammlung="02_Architektur", eltern=None, rot_z=0.0, boden=True, mat=None):
    """Quader als eigenes Objekt; bei boden=True liegt die Unterseite auf ort.z."""
    bm = bmesh.new()
    bm_box(bm, groesse, (0.0, 0.0, groesse[2] / 2 if boden else 0.0))
    o = mesh_aus_bmesh(name, bm, sammlung, eltern, [mat] if mat else [])
    o.location = ort
    o.rotation_euler = (0.0, 0.0, rot_z)
    return o


def boxen_objekt(name, liste, sammlung, eltern, mat):
    """Viele Quader in einem Objekt. liste: (groesse, mitte) oder (groesse, mitte, rot)."""
    bm = bmesh.new()
    for eintrag in liste:
        bm_box(bm, *eintrag)
    return mesh_aus_bmesh(name, bm, sammlung, eltern, [mat])


def speichern():
    if not bpy.data.filepath:
        bpy.ops.wm.save_as_mainfile(filepath=pfad("garten.blend"))
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
    return bpy.data.filepath


def view3d_kontext():
    for fenster in bpy.context.window_manager.windows:
        for bereich in fenster.screen.areas:
            if bereich.type == "VIEW_3D":
                region = next(r for r in bereich.regions if r.type == "WINDOW")
                return dict(window=fenster, area=bereich, region=region)
    raise RuntimeError("Kein 3D-Viewport gefunden")


def gn_kennung(gruppe, name):
    for item in gruppe.interface.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and item.in_out == "INPUT" and item.name == name:
            return item.identifier
    raise KeyError(name)


def gn_setze(mod, name, wert):
    mod[gn_kennung(mod.node_group, name)] = wert


def treiber_modus(ziel, datenpfad, ausdruck):
    """Treiber, der von Steuerung['modus'] abhängt; im Ausdruck heißt der Wert m."""
    ziel.driver_remove(datenpfad)
    fc = ziel.driver_add(datenpfad)
    d = fc.driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "m"
    v.type = "SINGLE_PROP"
    v.targets[0].id_type = "OBJECT"
    v.targets[0].id = bpy.data.objects["Steuerung"]
    v.targets[0].data_path = '["modus"]'
    d.expression = ausdruck
    return fc


def modus_setzen(wert):
    bpy.data.objects["Steuerung"]["modus"] = float(wert)
    sc = bpy.context.scene
    sc.frame_set(sc.frame_current)
```

- [ ] **Schritt 4: `scripts/gartenlib/pruefung.py` mit allen Prüfungen schreiben** (sie schlagen fehl, bis die zugehörige Aufgabe gebaut ist)

```python
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
            d = (bpy.data.objects[f"Sessel_{i}"].location - mitte).length
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
    if len(punkte) < 10000:
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
```

- [ ] **Schritt 5: `scripts/render_cli.py` und `scripts/render.sh` schreiben**

```python
"""Render im Hintergrund: blender -b garten.blend -P render_cli.py -- ausgabe ENGINE samples prozent [kamera] [modus]"""
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
ausgabe, engine, samples, prozent = argv[0], argv[1], int(argv[2]), int(argv[3])
kamera = argv[4] if len(argv) > 4 else None
modus = float(argv[5]) if len(argv) > 5 else 1.0

sc = bpy.context.scene
cp = bpy.context.preferences.addons["cycles"].preferences
cp.compute_device_type = "OPTIX"
cp.refresh_devices()
for d in cp.devices:
    d.use = d.type == "OPTIX"
sc.render.engine = engine
if engine == "CYCLES":
    sc.cycles.device = "GPU"
    sc.cycles.samples = samples
if engine == "BLENDER_WORKBENCH":
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = True
sc.render.resolution_percentage = prozent
if kamera:
    sc.camera = bpy.data.objects[kamera]
st = bpy.data.objects.get("Steuerung")
if st is not None:
    st["modus"] = modus
sc.frame_set(sc.frame_current)
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = ausgabe
bpy.ops.render.render(write_still=True)
print("FERTIG", ausgabe)
```

```bash
#!/usr/bin/env bash
# Aufruf: render.sh <ausgabe.png> <ENGINE> <samples> <prozent> [kamera] [modus]
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b "$DIR/../garten.blend" -P "$DIR/render_cli.py" -- "$@"
```

- [ ] **Schritt 6: Import im laufenden Blender testen**

MCP-Aufruf mit `modul = gartenlib.lade("util")` und `result = {"pfad": modul.pfad("x")}`.
Erwartet: `{"pfad": "D:\\KI Projekte\\Blender MArtists\\x"}`.

- [ ] **Schritt 7: Commit**

```bash
cd "/d/KI Projekte/Blender MArtists" && git add .gitignore scripts docs && git commit -m "Projektgerüst für die Gartenszene"
```

---

### Task 1: Render-Einrichtung

**Dateien:** Neu: `scripts/gartenlib/setup.py` (Teil 1)

- [ ] **Schritt 1: Prüfung ausführen, sie muss fehlschlagen**

Prüfaufruf `einrichtung()`. Erwartet: `ok: false` mit „Gerätetyp NONE“ und „garten.blend nicht gespeichert“.

- [ ] **Schritt 2: `setup.py` mit `render_einrichten()` schreiben**

```python
"""Render-Einstellungen, Collections und Steuerung."""
import bpy

from .util import collection, layer_collection, neues_objekt, setze

SAMMLUNGEN = [
    ("00_Steuerung", None), ("01_Gelaende", None), ("01a_Beete", "01_Gelaende"),
    ("02_Architektur", None), ("03_Innenraum", None), ("04_Hardscape", None),
    ("05_Pflanzen", None), ("05a_Rasen", "05_Pflanzen"), ("05b_Graeser", "05_Pflanzen"),
    ("05c_Stauden", "05_Pflanzen"), ("05d_Straeucher", "05_Pflanzen"), ("05e_Baeume", "05_Pflanzen"),
    ("05f_Kulisse", "05_Pflanzen"), ("06_Licht", None), ("07_Kameras", None),
    ("98_Masken", None), ("Maske_Rasen", "98_Masken"), ("Maske_Beet", "98_Masken"),
    ("99_Bibliothek", None), ("Bib_Halme", "99_Bibliothek"), ("Bib_Graeser", "99_Bibliothek"),
    ("Bib_Stauden", "99_Bibliothek"), ("Bib_Polster", "99_Bibliothek"),
]


def render_einrichten():
    log = []
    cp = bpy.context.preferences.addons["cycles"].preferences
    cp.compute_device_type = "OPTIX"
    cp.refresh_devices()
    for d in cp.devices:
        d.use = d.type == "OPTIX"
    bpy.ops.wm.save_userpref()

    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100

    for attr, wert in [("device", "GPU"), ("samples", 1024), ("use_adaptive_sampling", True),
                       ("adaptive_threshold", 0.01), ("use_denoising", True), ("denoiser", "OPTIX"),
                       ("preview_samples", 64), ("use_preview_denoising", True), ("max_bounces", 12),
                       ("diffuse_bounces", 4), ("glossy_bounces", 4), ("transmission_bounces", 8),
                       ("transparent_max_bounces", 64)]:
        setze(sc.cycles, attr, wert, log)

    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        if setze(sc.view_settings, "look", look, []):
            break
    else:
        log.append("AgX-Look nicht gesetzt")

    r.engine = "BLENDER_EEVEE"
    e = sc.eevee
    for attr, wert in [("use_raytracing", True), ("ray_tracing_method", "SCREEN"), ("use_shadows", True),
                       ("shadow_ray_count", 2), ("shadow_step_count", 8), ("shadow_resolution_scale", 1.0),
                       ("use_volumetric_shadows", True), ("volumetric_tile_size", "4"),
                       ("taa_samples", 16), ("taa_render_samples", 128), ("use_fast_gi", True)]:
        setze(e, attr, wert, log)
    if hasattr(e, "ray_tracing_options"):
        setze(e.ray_tracing_options, "resolution_scale", "1", log)
    return {"log": log, "geraete": [(d.name, d.type, d.use) for d in cp.devices]}
```

- [ ] **Schritt 3: Ausführen und speichern**

MCP-Aufruf `setup.render_einrichten()`, danach `gartenlib.lade("util").speichern()`.
- Erwartet: Unter `geraete` steht die RTX 4090 als OPTIX mit `use: true`.
- Steht in `log` „fehlt: …“, sind das Eevee-Optionen, die es in 5.1 nicht gibt. Das ist unkritisch, wird aber notiert.

- [ ] **Schritt 4: Prüfung erneut ausführen.** Erwartet: `ok: true`.

- [ ] **Schritt 5: Commit** `git add scripts && git commit -m "Render-Einrichtung OptiX/AgX/Eevee"`

---

### Task 2: Collections und Steuerung

**Dateien:** Ändern: `scripts/gartenlib/setup.py` (Funktion `struktur` anhängen)

- [ ] **Schritt 1: Prüfung `struktur()` ausführen.** Erwartet: `ok: false` (Collections fehlen, Cube noch da).

- [ ] **Schritt 2: `struktur()` an `setup.py` anhängen**

```python
def struktur():
    for name, eltern in SAMMLUNGEN:
        collection(name, eltern)
    for maske, kinder in (("Maske_Rasen", ("02_Architektur", "04_Hardscape", "01a_Beete")),
                          ("Maske_Beet", ("02_Architektur", "04_Hardscape"))):
        ziel = bpy.data.collections[maske]
        for kind in kinder:
            if kind not in ziel.children:
                ziel.children.link(bpy.data.collections[kind])
    for name in ("98_Masken", "99_Bibliothek"):
        layer_collection(name).exclude = True
    for name in ("Cube", "Light", "Camera"):
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    st = bpy.data.objects.get("Steuerung")
    if st is None:
        st = neues_objekt("Steuerung", None, "00_Steuerung")
        st.empty_display_type = "PLAIN_AXES"
    if "modus" not in st:
        st["modus"] = 0.0
    st.id_properties_ui("modus").update(
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
        description="0 = Laufen (schnell), 1 = Schönbild (volle Dichte)")
    return {"sammlungen": sorted(c.name for c in bpy.data.collections)}
```

- [ ] **Schritt 3: Ausführen und speichern.** MCP-Aufruf `setup.struktur()`, danach `util.speichern()`.
- [ ] **Schritt 4: Prüfung `struktur()`.** Erwartet: `ok: true`.
- [ ] **Schritt 5: Commit** `git commit -am "Collections und Steuerung"` (zuvor `git add scripts`).

---

### Task 3: Layout und Architektur (Graumodell)

**Dateien:** Neu: `scripts/gartenlib/layout.py`, `scripts/gartenlib/architektur.py`

- [ ] **Schritt 1: `layout.py` schreiben**

```python
"""Alle Maße und Positionen in Metern. Ursprung nahe Hofmitte, +Y grob Blickrichtung der Referenzkamera."""

GRUNDSTUECK = (-24.0, -22.0, 16.0, 26.0)  # xmin, ymin, xmax, ymax

HAUS = {
    "mitte": (-10.5, 12.5), "rot_grad": -25.0,
    "breite": 12.0, "tiefe": 9.0, "eg_h": 3.0, "og_h": 2.8,
    "wand": 0.3, "boden": 0.15, "decke": 0.25,
    "dach_ueberstand": 0.6, "dach_neigung": 15.0,
}
# Öffnungen: (seite, versatz entlang der Wand, brüstung über Fußboden innen, breite, höhe, art)
# seite: S = Front (-Y lokal), N, O (+X), W; art: fenster | tuer | tuer_offen (rechte Hälfte Glas, linke offen)
HAUS_EG_OEFFNUNGEN = [
    ("S", -4.2, 0.0, 1.1, 2.3, "tuer"),
    ("S", -1.6, 0.9, 1.8, 1.5, "fenster"),
    ("S", 2.6, 0.0, 2.6, 2.4, "tuer_offen"),
    ("O", 0.0, 0.9, 1.4, 1.5, "fenster"),
    ("W", 1.0, 0.9, 1.4, 1.5, "fenster"),
    ("N", 2.0, 0.9, 2.0, 1.5, "fenster"),
]
HAUS_OG_OEFFNUNGEN = [
    ("S", -3.6, 0.9, 1.4, 1.3, "fenster"),
    ("S", 0.0, 0.9, 1.4, 1.3, "fenster"),
    ("S", 3.6, 0.9, 1.4, 1.3, "fenster"),
    ("O", 0.0, 0.9, 1.2, 1.3, "fenster"),
    ("W", 0.0, 0.9, 1.2, 1.3, "fenster"),
    ("N", -2.0, 0.9, 1.4, 1.3, "fenster"),
]
VORDACH = {"mitte_lokal": (-3.4, -5.7), "breite": 5.0, "tiefe": 2.4, "hoehe": 2.9,
           "neigung": 12.0, "ueberstand": 0.15, "stuetzen_lokal": [(-5.6, -6.6), (-1.2, -6.6)]}
TERRASSE = {"mitte_lokal": (0.0, -6.1), "groesse": (12.0, 3.2, 0.15)}

FLUEGEL = {
    "xmin": 5.0, "xmax": 11.0, "ymin": -18.0, "ymax": 5.0, "h": 3.2, "wand": 0.3,
    "ueberstand": 1.2, "neigung": 12.0,
    "oeffnungen": [
        ("W", -8.0, 0.0, 2.2, 2.5, "fenster"),
        ("W", -3.5, 0.0, 2.2, 2.5, "fenster"),
        ("W", 1.0, 0.0, 2.2, 2.5, "fenster"),
        ("W", 5.5, 0.0, 2.2, 2.5, "fenster"),
        ("N", 0.0, 0.9, 1.6, 1.4, "fenster"),
    ],
}
CARPORT = {"mitte": (6.5, 11.0), "breite": 6.0, "tiefe": 6.5, "hoehe": 2.6, "ueberstand": 0.35, "neigung": 20.0}

HOF = {"mitte": (-2.0, -1.5), "radius": 4.0}
SESSEL_WINKEL = [150.0, 215.0, 290.0, 30.0]
SESSEL_RADIUS = 1.9
WEG_FLUEGEL = (2.6, -18.0, 5.0, -2.0)  # xmin, ymin, xmax, ymax
TRITTPLATTEN = {"start": (2.4, -0.6), "ende": (4.4, 7.2), "anzahl": 9, "groesse": (0.75, 0.45, 0.06)}
POLLER = [(2.3, -6.8), (-6.2, 2.4), (3.0, 1.8), (-5.8, -6.4)]

KAMERA = {"ort": (3.8, -8.6, 1.6), "ziel": (-2.3, 4.0, 2.1), "brennweite": 20.0}

BEETE = {
    "Beet_Hof_West": [(-12.0, -9.0), (-6.5, -7.5), (-6.2, -4.5), (-6.6, -1.0), (-7.5, 1.5), (-11.0, 1.0), (-12.5, -4.0)],
    "Beet_Ahorn": [(-5.0, -8.6), (0.5, -8.6), (1.0, -5.6), (-0.8, -4.9), (-3.0, -5.3), (-5.0, -5.8)],
    "Beet_Vorne": [(1.2, -9.6), (2.5, -9.6), (2.5, -4.0), (1.9, -3.4), (1.3, -5.0)],
    "Beet_Mitte": [(-1.0, 3.0), (2.0, 2.2), (3.4, 3.6), (3.0, 6.2), (0.4, 7.0), (-2.2, 5.4)],
    "Beet_Carport": [(1.5, 8.0), (3.3, 7.6), (3.4, 12.5), (1.2, 12.8)],
    "Beet_Haus": [(-6.2, 6.2), (-3.0, 6.0), (-2.2, 9.8), (-4.6, 10.6)],
}


def _mix(graeser=1.0, stauden=1.0, polster=1.0, boden=1.0):
    """Schichten je Beet: (bibliothek, ziel-collection, dichte_lauf, dichte_schoen, mindestabstand, (skala_min, skala_max))."""
    return [
        ("Bib_Graeser", "05b_Graeser", 0.4 * graeser, 1.0 * graeser, 0.7, (0.8, 1.3)),
        ("Bib_Stauden", "05c_Stauden", 0.8 * stauden, 2.0 * stauden, 0.35, (0.8, 1.2)),
        ("Bib_Polster", "05d_Straeucher", 0.1 * polster, 0.25 * polster, 1.3, (0.7, 1.1)),
        ("Bib_Halme", "05b_Graeser", 15.0 * boden, 60.0 * boden, 0.06, (0.8, 1.5)),
    ]


BEPFLANZUNG = {
    "Beet_Hof_West": _mix(1.2, 1.0, 0.8),
    "Beet_Ahorn": _mix(0.6, 1.4, 0.6),
    "Beet_Vorne": _mix(0.3, 1.2, 1.6),
    "Beet_Mitte": _mix(0.8, 1.5, 1.4),
    "Beet_Carport": _mix(1.6, 0.6, 0.5),
    "Beet_Haus": _mix(1.0, 1.0, 0.8),
}

# (name, art, ort, zielhöhe, seed)
BAEUME = [
    ("Baum_Ahorn_1", "ahorn", (-1.8, -6.2), 8.0, 4),
    ("Baum_Birke_1", "birke", (1.0, 4.8), 11.0, 1),
    ("Baum_Birke_2", "birke", (2.0, 10.0), 12.5, 2),
    ("Baum_Birke_3", "birke", (-4.0, 8.0), 10.0, 3),
]
```

- [ ] **Schritt 2: Prüfung `architektur()`.** Erwartet: `ok: false` mit „fehlt Haus …“.

- [ ] **Schritt 3: `architektur.py` schreiben**

```python
"""Haus, Vordach, Seitenflügel und Carport als Graumodell mit echten Öffnungen."""
import math

import bmesh
import bpy
from mathutils import Vector

from . import layout as L
from .util import box, boxen_objekt, collection, leere, material, mesh_aus_bmesh, neues_objekt

S = "02_Architektur"


def glas_material():
    m = bpy.data.materials.get("M_Glas")
    if m is None:
        m = bpy.data.materials.new("M_Glas")
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.9, 0.95, 0.95, 1.0)
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.02
        b.inputs["IOR"].default_value = 1.5
        if hasattr(m, "use_raytrace_refraction"):
            m.use_raytrace_refraction = True
    return m


def mats():
    return {
        "putz": material("M_Putz", (0.78, 0.77, 0.74), 0.85),
        "holz": material("M_Holzfassade", (0.30, 0.17, 0.09), 0.7),
        "blech": material("M_Dachblech", (0.06, 0.06, 0.065), 0.45, 0.6),
        "traufe": material("M_Traufe", (0.08, 0.06, 0.05), 0.7),
        "ziegel": material("M_Dachziegel", (0.12, 0.12, 0.13), 0.6),
        "rahmen": material("M_Rahmen", (0.03, 0.03, 0.035), 0.4),
        "stahl": material("M_Stahl_Schwarz", (0.02, 0.02, 0.02), 0.5),
        "tuer": material("M_Haustuer", (0.12, 0.07, 0.04), 0.5),
        "glas": glas_material(),
    }


def walmdach(name, breite, tiefe, ueberstand, neigung_grad, z, eltern, mat_dach, mat_traufe,
             mitte=(0.0, 0.0), dicke=0.18):
    """Geschlossenes Walmdach inkl. Traufkante; Unterseite = Dachuntersicht (Material 1)."""
    b, t = breite + 2 * ueberstand, tiefe + 2 * ueberstand
    h = min(b, t) / 2 * math.tan(math.radians(neigung_grad))
    bm = bmesh.new()
    oben = [bm.verts.new(p) for p in [(-b / 2, -t / 2, 0), (b / 2, -t / 2, 0), (b / 2, t / 2, 0), (-b / 2, t / 2, 0)]]
    unten = [bm.verts.new((v.co.x, v.co.y, -dicke)) for v in oben]
    if b >= t:
        r = (b - t) / 2
        r0, r1 = bm.verts.new((-r, 0, h)), bm.verts.new((r, 0, h))
        dach = [(oben[0], oben[1], r1, r0), (oben[1], oben[2], r1), (oben[2], oben[3], r0, r1), (oben[3], oben[0], r0)]
    else:
        r = (t - b) / 2
        r0, r1 = bm.verts.new((0, -r, h)), bm.verts.new((0, r, h))
        dach = [(oben[0], oben[1], r0), (oben[1], oben[2], r1, r0), (oben[2], oben[3], r1), (oben[3], oben[0], r0, r1)]
    for f in dach:
        bm.faces.new(f).material_index = 0
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((unten[i], unten[j], oben[j], oben[i])).material_index = 1
    bm.faces.new(list(reversed(unten))).material_index = 1
    o = mesh_aus_bmesh(name, bm, S, eltern, [mat_dach, mat_traufe])
    o.location = (mitte[0], mitte[1], z)
    return o


def _wandpunkt(seite, versatz, breite, tiefe):
    if seite == "S":
        return Vector((versatz, -tiefe / 2, 0)), Vector((0, -1, 0))
    if seite == "N":
        return Vector((-versatz, tiefe / 2, 0)), Vector((0, 1, 0))
    if seite == "O":
        return Vector((breite / 2, versatz, 0)), Vector((1, 0, 0))
    if seite == "W":
        return Vector((-breite / 2, -versatz, 0)), Vector((-1, 0, 0))
    raise ValueError(seite)


def _quer(normal, laengs, tief, hoch):
    """Box-Größe: 'laengs' entlang der Wand, 'tief' entlang der Wandnormalen."""
    return (tief, laengs, hoch) if abs(normal.x) > 0.5 else (laengs, tief, hoch)


def _korpus(name, wurzel, breite, tiefe, z0, hoehe, wand, boden, decke, mat, schneider):
    """Hohler Quader; alle Objekte in der Schneider-Collection werden per Boolean abgezogen."""
    o = box(name, (breite, tiefe, hoehe), (0, 0, z0), S, eltern=wurzel, mat=mat)
    s = box(f"Schneider_{name}_Innen", (breite - 2 * wand, tiefe - 2 * wand, hoehe - boden - decke),
            (0, 0, z0 + boden), schneider.name, eltern=wurzel)
    _als_schneider(s)
    m = o.modifiers.new("Oeffnungen", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.operand_type = "COLLECTION"
    m.collection = schneider
    m.solver = "EXACT"
    return o


def _als_schneider(o):
    o.display_type = "WIRE"
    o.hide_render = True
    o.hide_set(True)


def _oeffnung(name, wurzel, schneider, seite, versatz, z_unten, b, h, art, breite, tiefe, wand, m):
    p, n = _wandpunkt(seite, versatz, breite, tiefe)
    zc = z_unten + h / 2
    s = box(f"Schneider_{name}", _quer(n, b, wand * 3, h), (p.x, p.y, zc), schneider.name, eltern=wurzel, boden=False)
    _als_schneider(s)
    a = Vector((-n.y, n.x, 0))          # Richtung entlang der Wand
    mitte = p - n * 0.10                # Rahmenebene 10 cm hinter der Außenfläche
    rb, rt = 0.06, 0.07
    teile = [
        (_quer(n, b, rt, rb), mitte + Vector((0, 0, zc + h / 2 - rb / 2))),
        (_quer(n, rb, rt, h), mitte + a * (b / 2 - rb / 2) + Vector((0, 0, zc))),
        (_quer(n, rb, rt, h), mitte - a * (b / 2 - rb / 2) + Vector((0, 0, zc))),
    ]
    if art == "fenster":
        teile.append((_quer(n, b, rt, rb), mitte + Vector((0, 0, zc - h / 2 + rb / 2))))
    if art == "tuer_offen":
        teile.append((_quer(n, rb, rt, h), mitte + Vector((0, 0, zc))))
    boxen_objekt(f"Rahmen_{name}", teile, S, wurzel, m["rahmen"])
    if art == "fenster":
        boxen_objekt(f"Glas_{name}", [(_quer(n, b - 2 * rb, 0.02, h - 2 * rb), mitte + Vector((0, 0, zc)))],
                     S, wurzel, m["glas"])
    elif art == "tuer_offen":
        halb = (b - 3 * rb) / 2
        boxen_objekt(f"Glas_{name}", [(_quer(n, halb, 0.02, h - rb), mitte + a * (b / 4) + Vector((0, 0, zc - rb / 2)))],
                     S, wurzel, m["glas"])
    elif art == "tuer":
        boxen_objekt(f"Tuerblatt_{name}", [(_quer(n, b - 2 * rb, 0.05, h - rb), mitte + Vector((0, 0, zc - rb / 2)))],
                     S, wurzel, m["tuer"])


def _oeffnungen(praefix, liste, z_boden, wurzel, schneider, breite, tiefe, wand, m):
    for i, (seite, versatz, bruestung, b, h, art) in enumerate(liste):
        _oeffnung(f"{praefix}_{i + 1:02d}", wurzel, schneider, seite, versatz, z_boden + bruestung,
                  b, h, art, breite, tiefe, wand, m)


def haus(m):
    H = L.HAUS
    wurzel = neues_objekt("Haus", None, S)
    wurzel.location = (*H["mitte"], 0.0)
    wurzel.rotation_euler = (0.0, 0.0, math.radians(H["rot_grad"]))
    sch_eg = collection("Schneider_Haus_EG", S)
    sch_og = collection("Schneider_Haus_OG", S)
    b, t, w = H["breite"], H["tiefe"], H["wand"]
    _korpus("Haus_EG", wurzel, b, t, 0.0, H["eg_h"], w, H["boden"], H["decke"], m["putz"], sch_eg)
    _korpus("Haus_OG", wurzel, b, t, H["eg_h"], H["og_h"], w, 0.0, H["decke"], m["holz"], sch_og)
    _oeffnungen("EG", L.HAUS_EG_OEFFNUNGEN, H["boden"], wurzel, sch_eg, b, t, w, m)
    _oeffnungen("OG", L.HAUS_OG_OEFFNUNGEN, H["eg_h"], wurzel, sch_og, b, t, w, m)
    walmdach("Haus_Dach", b, t, H["dach_ueberstand"], H["dach_neigung"], H["eg_h"] + H["og_h"],
             wurzel, m["blech"], m["traufe"])
    V = L.VORDACH
    walmdach("Vordach_Dach", V["breite"], V["tiefe"], V["ueberstand"], V["neigung"], V["hoehe"],
             wurzel, m["blech"], m["traufe"], mitte=V["mitte_lokal"], dicke=0.15)
    boxen_objekt("Vordach_Stuetzen", [((0.3, 0.3, V["hoehe"]), (x, y, V["hoehe"] / 2)) for x, y in V["stuetzen_lokal"]],
                 S, wurzel, m["putz"])
    rohre = []
    for sx in (-1, 1):
        rohre.append(((0.1, 0.1, H["eg_h"] + H["og_h"]), (sx * (b / 2 + 0.08), -t / 2 - 0.08, (H["eg_h"] + H["og_h"]) / 2)))
    boxen_objekt("Fallrohre", rohre, S, wurzel, m["stahl"])
    return wurzel


def fluegel(m):
    F = L.FLUEGEL
    b, t = F["xmax"] - F["xmin"], F["ymax"] - F["ymin"]
    wurzel = neues_objekt("Fluegel_Wurzel", None, S)
    wurzel.location = ((F["xmin"] + F["xmax"]) / 2, (F["ymin"] + F["ymax"]) / 2, 0.0)
    sch = collection("Schneider_Fluegel", S)
    _korpus("Fluegel", wurzel, b, t, 0.0, F["h"], F["wand"], 0.15, 0.25, m["putz"], sch)
    _oeffnungen("FL", F["oeffnungen"], 0.15, wurzel, sch, b, t, F["wand"], m)
    walmdach("Fluegel_Dach", b, t, F["ueberstand"], F["neigung"], F["h"], wurzel, m["blech"], m["traufe"], dicke=0.3)


def carport(m):
    C = L.CARPORT
    b, t, h = C["breite"], C["tiefe"], C["hoehe"]
    wurzel = neues_objekt("Carport", None, S)
    wurzel.location = (*C["mitte"], 0.0)
    boxen_objekt("Carport_Stuetzen", [((0.15, 0.15, h), (sx * (b / 2 - 0.2), sy * (t / 2 - 0.2), h / 2))
                                      for sx in (-1, 1) for sy in (-1, 1)], S, wurzel, m["stahl"])
    balken = [((b, 0.12, 0.3), (0, sy * (t / 2 - 0.2), h - 0.15)) for sy in (-1, 1)]
    balken += [((0.12, t, 0.3), (sx * (b / 2 - 0.2), 0, h - 0.15)) for sx in (-1, 1)]
    boxen_objekt("Carport_Rahmen", balken, S, wurzel, m["traufe"])
    walmdach("Carport_Dach", b, t, C["ueberstand"], C["neigung"], h, wurzel, m["ziegel"], m["traufe"])


def baue():
    leere(S)
    m = mats()
    haus(m)
    fluegel(m)
    carport(m)
    return {"objekte": len(bpy.data.collections[S].all_objects)}
```

- [ ] **Schritt 4: Ausführen und speichern.** MCP-Aufruf `architektur.baue()`, danach `util.speichern()`. Erwartet: deutlich über 40 Objekte.

- [ ] **Schritt 5: Prüfung `architektur()`.** Erwartet: `ok: true`.
- Ist die Tür blockiert: Prüfen, ob `hide_set` die Booleans stört. Gegenprobe: in `_als_schneider` die Zeile `o.hide_set(True)` entfernen und neu bauen.
- Hilft das nicht, mit `systematic-debugging` vorgehen.

- [ ] **Schritt 6: Sichtprüfung.**
- Mit `mcp__Blender__get_screenshot_of_window_as_image` einen Screenshot machen.
- Erwartet: hohle Häuser mit Fensteröffnungen, Walmdächern und Vordach. Keine Dächer stehen schräg, keine Flächen zeigen nach innen.

- [ ] **Schritt 7: Commit** `git add scripts && git commit -m "Architektur-Graumodell"`

---

### Task 4: Hardscape (Graumodell)

**Dateien:** Neu: `scripts/gartenlib/hardscape.py`

- [ ] **Schritt 1: Prüfung `hardscape()`.** Erwartet: `ok: false`.

- [ ] **Schritt 2: `hardscape.py` schreiben**

```python
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
    weg = []
    for v in bm.verts:
        w = math.atan2(v.co.y, v.co.x)
        grenze = r * (1 + 0.03 * math.sin(5 * w) + 0.02 * math.sin(11 * w + 1.3))
        if v.co.xy.length > grenze:
            weg.append(v)
    bmesh.ops.delete(bm, geom=weg, context="VERTS")
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
```

- [ ] **Schritt 3: Ausführen und speichern.** MCP-Aufruf `hardscape.baue()`, danach `util.speichern()`.
- [ ] **Schritt 4: Prüfung `hardscape()`.** Erwartet: `ok: true`.
- [ ] **Schritt 5: Sichtprüfung per Screenshot.** Sessel schauen zur Feuerschale, die Platten liegen bündig über dem Boden (z = 0,02), die Terrasse liegt vor der Hausfront.
- [ ] **Schritt 6: Commit** `git add scripts && git commit -m "Hardscape-Graumodell"`

---

### Task 5: Referenzkamera und Graumodell-Render

**Dateien:** Neu: `scripts/gartenlib/kamera.py`

- [ ] **Schritt 1: Prüfung `kamera()`.** Erwartet: `ok: false`.

- [ ] **Schritt 2: `kamera.py` schreiben**

```python
"""Referenzkamera mit der Perspektive des Referenzbilds."""
import bpy
from mathutils import Vector

from . import layout as L
from .util import neues_objekt


def baue():
    K = L.KAMERA
    alt = bpy.data.objects.get("Kamera_Referenz")
    if alt is not None:
        bpy.data.objects.remove(alt, do_unlink=True)
    cam = bpy.data.cameras.get("Kamera_Referenz") or bpy.data.cameras.new("Kamera_Referenz")
    cam.lens = K["brennweite"]
    cam.sensor_width = 36.0
    cam.clip_start = 0.05
    cam.clip_end = 500.0
    o = neues_objekt("Kamera_Referenz", cam, "07_Kameras")
    o.location = K["ort"]
    o.rotation_euler = (Vector(K["ziel"]) - Vector(K["ort"])).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return {"rotation": list(o.rotation_euler)}
```

- [ ] **Schritt 3: Ausführen, speichern, Prüfung.** Erwartet: `ok: true`.

- [ ] **Schritt 4: Graumodell rendern**

```bash
bash "/d/KI Projekte/Blender MArtists/scripts/render.sh" "D:/KI Projekte/Blender MArtists/renders/01_graumodell.png" BLENDER_WORKBENCH 1 50 Kamera_Referenz 0
```

Erwartet: Die Ausgabe endet mit `FERTIG …01_graumodell.png`.

- [ ] **Schritt 5: Mit dem Referenzbild vergleichen.** `renders/01_graumodell.png` und `docs/referenz/bild2.webp` mit Read ansehen. Soll-Bild:
- Feuerschale leicht links der Mitte, Haupthaus links-mittig im Hintergrund
- Seitenflügel mit Dachüberstand am rechten Rand, Carport rechts hinten
- Horizont etwa auf halber Höhe

Weicht es deutlich ab, `KAMERA` in `layout.py` anpassen (zuerst `ziel`, dann `ort`), Kamera neu bauen und neu rendern. Höchstens 3 Durchläufe, danach den Stand Stephan zeigen.

- [ ] **Schritt 6: Commit** `git add scripts && git commit -m "Referenzkamera"`

---

### Task 6: Poly-Haven-Kandidaten suchen und Auswahl festlegen

**Dateien:** Neu: `scripts/polyhaven.py`; erzeugt `assets/kandidaten.json`, `assets/kandidaten.html`, `assets/auswahl.json`

- [ ] **Schritt 1: Prüfung `assets()`.** Erwartet: `ok: false`, „auswahl.json fehlt“.

- [ ] **Schritt 2: `scripts/polyhaven.py` schreiben**

```python
"""Poly-Haven-Client, nur Standardbibliothek.
  python polyhaven.py kandidaten  -> assets/kandidaten.json + kandidaten.html
  python polyhaven.py plan        -> Dateiliste + Gesamtgröße aus assets/auswahl.json (lädt nichts)
  python polyhaven.py lade        -> lädt den Plan (vorhandene Dateien gleicher Größe werden übersprungen)
"""
import json
import os
import sys
import urllib.request

API = "https://api.polyhaven.com"
KOPF = {"User-Agent": "garten-szene-blender/1.0"}
PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(PROJEKT, "assets")
ZIEL = os.path.join(ASSETS, "polyhaven")

ROLLEN = {
    "hdri_himmel": ("hdris", ["overcast", "cloudy"]),
    "tex_putz": ("textures", ["plaster"]),
    "tex_holzfassade": ("textures", ["planks", "siding", "wood_wall", "wooden"]),
    "tex_dachblech": ("textures", ["metal_plate", "corrugated", "metal_roof", "painted_metal"]),
    "tex_dachziegel": ("textures", ["roof_tiles", "roof"]),
    "tex_steinplatten": ("textures", ["slate", "flagstone", "stone_tiles", "rock_tile"]),
    "tex_trittstein": ("textures", ["concrete", "paving", "stone_floor"]),
    "tex_holzdeck": ("textures", ["wood_floor", "deck", "planks"]),
    "tex_beet": ("textures", ["mulch", "soil", "forest_ground", "forrest_ground", "mud"]),
    "tex_rinde_ahorn": ("textures", ["bark"]),
    "modelle_straeucher": ("models", ["shrub", "bush", "pine", "fern", "plant"]),
}
AUFLOESUNG = {"hdris": "4k", "textures": "2k", "models": "2k"}
KARTEN = {"Diffuse": ("jpg", "png"), "Rough": ("jpg", "png"), "Displacement": ("png", "jpg")}


def _json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=KOPF), timeout=60) as r:
        return json.load(r)


def suche(typ, begriffe, n):
    treffer = []
    for aid, info in _json(f"{API}/assets?t={typ}").items():
        text = " ".join([aid, info.get("name", ""), *info.get("tags", []), *info.get("categories", [])]).lower()
        if any(b in text for b in begriffe):
            treffer.append((info.get("download_count", 0), aid, info.get("name", "")))
    treffer.sort(reverse=True)
    return [{"id": a, "name": nm, "downloads": d,
             "bild": f"https://cdn.polyhaven.com/asset_img/thumbs/{a}.png?width=256"} for d, a, nm in treffer[:n]]


def kandidaten():
    erg = {rolle: suche(typ, begriffe, 16 if typ == "models" else 10) for rolle, (typ, begriffe) in ROLLEN.items()}
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "kandidaten.json"), "w", encoding="utf-8") as f:
        json.dump(erg, f, indent=1, ensure_ascii=False)
    html = ["<!doctype html><meta charset=utf-8><title>Poly Haven Kandidaten</title>",
            "<style>body{font-family:sans-serif;background:#1d1d1d;color:#eee;padding:16px}"
            "figure{display:inline-block;margin:6px;width:200px;vertical-align:top}img{width:200px}</style>"]
    for rolle, liste in erg.items():
        html.append(f"<h2>{rolle}</h2>")
        html += [f"<figure><img src='{k['bild']}'><figcaption>{k['id']}<br>{k['downloads']} Downloads"
                 f"</figcaption></figure>" for k in liste]
    with open(os.path.join(ASSETS, "kandidaten.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return erg


def _waehle(formate, bevorzugt):
    for fmt in bevorzugt:
        if fmt in formate:
            return formate[fmt]
    return next(iter(formate.values()))


def plan():
    with open(os.path.join(ASSETS, "auswahl.json"), encoding="utf-8") as f:
        auswahl = json.load(f)
    dateien = {}
    for rolle, ids in auswahl.items():
        typ = ROLLEN[rolle][0]
        res = AUFLOESUNG[typ]
        for aid in ([ids] if isinstance(ids, str) else ids):
            info = _json(f"{API}/files/{aid}")
            ordner = os.path.join(ZIEL, typ, aid)
            if typ == "hdris":
                eintraege = [info["hdri"][res]["hdr"]]
            elif typ == "textures":
                eintraege = [_waehle(info[k][res], fm) for k, fm in KARTEN.items() if k in info and res in info[k]]
            else:
                blend = info["blend"][res]["blend"]
                eintraege = [blend]
                for rel, inc in blend.get("include", {}).items():
                    dateien[os.path.join(ordner, *rel.split("/"))] = (inc["url"], inc["size"])
            for e in eintraege:
                dateien[os.path.join(ordner, os.path.basename(e["url"]))] = (e["url"], e["size"])
    return [(url, ziel, groesse) for ziel, (url, groesse) in sorted(dateien.items())]


def lade():
    for url, ziel, groesse in plan():
        if os.path.exists(ziel) and os.path.getsize(ziel) == groesse:
            continue
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=KOPF), timeout=300) as r, open(ziel, "wb") as f:
            while True:
                stueck = r.read(1 << 20)
                if not stueck:
                    break
                f.write(stueck)
        print("geladen", os.path.relpath(ziel, PROJEKT), f"{groesse / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    befehl = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if befehl == "kandidaten":
        for rolle, liste in kandidaten().items():
            print(rolle, [k["id"] for k in liste])
    elif befehl == "plan":
        p = plan()
        for url, ziel, groesse in p:
            print(f"{groesse / 1e6:8.1f} MB  {os.path.relpath(ziel, PROJEKT)}")
        print(f"GESAMT {sum(g for _, _, g in p) / 1e6:.0f} MB in {len(p)} Dateien")
    elif befehl == "lade":
        lade()
```

- [ ] **Schritt 3: Kandidaten abfragen.** Das liest nur API-Daten, es wird nichts heruntergeladen.

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/5.1/python/bin/python.exe" scripts/polyhaven.py kandidaten
```

Erwartet: Jede Rolle hat mindestens einen Treffer. Bei leeren Rollen die Suchbegriffe in `ROLLEN` erweitern.

- [ ] **Schritt 4: Vorschaubilder ansehen.**
- `assets/kandidaten.html` im eingebauten Browser öffnen (`mcp__Claude_Browser__preview_start` mit `url: file:///D:/KI%20Projekte/Blender%20MArtists/assets/kandidaten.html`).
- Pro Rolle per Screenshot das passendste Asset wählen:
  - **hdri_himmel:** gleichmäßig bewölkt, mit Bäumen oder Landschaft am Horizont
  - **tex_putz:** heller, feiner Putz
  - **tex_holzfassade:** braune Bretter
  - **tex_dachblech:** dunkles Metall
  - **tex_dachziegel:** dunkle Ziegel
  - **tex_steinplatten:** dunkler Schiefer oder Naturstein
  - **tex_trittstein:** grauer Beton oder Stein
  - **tex_holzdeck:** Holzdielen
  - **tex_beet:** Mulch oder Erde
  - **tex_rinde_ahorn:** graubraune Rinde
  - **modelle_straeucher:** 2–4 kompakte, runde Sträucher, möglichst nadelig oder kleinblättrig

- [ ] **Schritt 5: `assets/auswahl.json` schreiben.** Format (die IDs sind Beispiele und werden durch die Auswahl aus Schritt 4 ersetzt):

```json
{
  "hdri_himmel": "<hdri-id>",
  "tex_putz": "<id>",
  "tex_holzfassade": "<id>",
  "tex_dachblech": "<id>",
  "tex_dachziegel": "<id>",
  "tex_steinplatten": "<id>",
  "tex_trittstein": "<id>",
  "tex_holzdeck": "<id>",
  "tex_beet": "<id>",
  "tex_rinde_ahorn": "<id>",
  "modelle_straeucher": ["<id>", "<id>"]
}
```

- [ ] **Schritt 6: Download-Plan erstellen.**

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/5.1/python/bin/python.exe" scripts/polyhaven.py plan
```

Erwartet: eine Dateiliste und `GESAMT … MB` (grob 0,5–1,5 GB).

- [ ] **Schritt 7: FREIGABE.**
- Stephan bekommt die gewählten Assets mit Vorschau (Link zu `assets/kandidaten.html`), die Dateiliste und die Gesamtgröße.
- Gefragt wird: „Darf ich diese Dateien von polyhaven.com nach `assets/polyhaven/` laden?“
- **Ohne ein klares Ja geht es nicht weiter.**

- [ ] **Schritt 8: Commit** `git add scripts && git commit -m "Poly-Haven-Client und Kandidatensuche"`

---

### Task 7: Assets herunterladen

- [ ] **Schritt 1: Download nach Freigabe im Hintergrund starten**

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/5.1/python/bin/python.exe" scripts/polyhaven.py lade
```

Erwartet: je Datei eine Zeile „geladen …“. Bei Netzwerkfehlern denselben Befehl erneut ausführen, Vorhandenes wird übersprungen.

- [ ] **Schritt 2: Prüfung `assets()`.** Erwartet: `ok: true`.

---

### Task 8: Materialbaukasten

**Dateien:** Neu: `scripts/gartenlib/materialien.py`

- [ ] **Schritt 1: Prüfung `materialien()`.** Erwartet: `ok: false` (Materialien ohne Bildtextur).

- [ ] **Schritt 2: `materialien.py` schreiben**

```python
"""PBR-Materialien aus Poly-Haven-Texturen. Box-Projektion auf Objektkoordinaten (keine UVs nötig)."""
import glob
import json
import os

import bpy

from .util import pfad

TEXTUR_MATS = {
    "M_Putz": dict(rolle="tex_putz", skala=2.0),
    "M_Holzfassade": dict(rolle="tex_holzfassade", skala=2.0, vertikal=True),
    "M_Traufe": dict(rolle="tex_holzfassade", skala=2.0, tint=(0.3, 0.25, 0.22), vertikal=True),
    "M_Dachblech": dict(rolle="tex_dachblech", skala=1.5, tint=(0.25, 0.25, 0.27)),
    "M_Dachziegel": dict(rolle="tex_dachziegel", skala=1.5),
    "M_Holzdeck": dict(rolle="tex_holzdeck", skala=2.0),
    "M_Trittplatten": dict(rolle="tex_trittstein", skala=1.0, verschiebung=0.005),
    "M_Weg_Platten": dict(rolle="tex_trittstein", skala=1.2, tint=(0.5, 0.5, 0.52), fugen="quadrat", fugen_groesse=0.6),
    "M_Polygonalplatten": dict(rolle="tex_steinplatten", skala=1.0, tint=(0.5, 0.5, 0.52), fugen="voronoi", fugen_groesse=0.55),
    "M_Beet": dict(rolle="tex_beet", skala=1.5, verschiebung=0.01),
    "M_Erde": dict(rolle="tex_beet", skala=1.5, tint=(0.55, 0.6, 0.45)),
    "M_Rinde_Ahorn": dict(rolle="tex_rinde_ahorn", skala=0.8),
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


def pbr(name, rolle, skala=1.0, tint=None, vertikal=False, verschiebung=0.0, bump=0.4, fugen=None, fugen_groesse=0.6):
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
    if tint:
        farbe = mix_farbe(nt, farbe, tint, 1.0, "MULTIPLY")
    rough_datei = _karte(ordner, "_rough_")
    rauheit = _bild(nt, rough_datei, False, vek).outputs["Color"] if rough_datei else 0.7
    disp_datei = _karte(ordner, "_disp_")
    hoehe = _bild(nt, disp_datei, False, vek).outputs["Color"] if disp_datei else None

    if fugen:
        maske = _fugen_maske(nt, obj_vek, fugen, fugen_groesse)
        if fugen == "voronoi":
            var = _zell_variation(nt, obj_vek, fugen_groesse)
            mul = nt.nodes.new("ShaderNodeMix")
            mul.data_type = "RGBA"
            mul.blend_type = "MULTIPLY"
            _sock(mul.inputs, "Factor", "VALUE").default_value = 1.0
            nt.links.new(farbe, _sock(mul.inputs, "A", "RGBA"))
            kom = nt.nodes.new("ShaderNodeCombineColor")
            for i in range(3):
                nt.links.new(var, kom.inputs[i])
            nt.links.new(kom.outputs[0], _sock(mul.inputs, "B", "RGBA"))
            farbe = _sock(mul.outputs, "Result", "RGBA")
        farbe = mix_farbe(nt, farbe, (0.025, 0.025, 0.025), maske)
        rauheit = mathe(nt, "MAXIMUM", rauheit, mathe(nt, "MULTIPLY", maske, 0.95))
        hoehe = mathe(nt, "SUBTRACT", hoehe if hoehe is not None else 0.5, mathe(nt, "MULTIPLY", maske, 0.6))

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


def baue():
    erg = {}
    for name, opts in TEXTUR_MATS.items():
        pbr(name, **opts)
        erg[name] = "ok"
    return erg
```

- [ ] **Schritt 3: Ausführen und speichern.** MCP-Aufruf `materialien.baue()`, danach `util.speichern()`.
- [ ] **Schritt 4: Prüfung `materialien()`.** Erwartet: `ok: true`.
- [ ] **Schritt 5: Commit** `git add scripts && git commit -m "PBR-Materialbaukasten"`

---

### Task 9: Himmel, Sonne, Dunst

**Dateien:** Neu: `scripts/gartenlib/welt.py`

- [ ] **Schritt 1: Prüfung `welt()`.** Erwartet: `ok: false`.

- [ ] **Schritt 2: `welt.py` schreiben**

```python
"""HDRI-Himmel (bewölkt), weiche Sonne, leichter Dunst (nur im Modus Schönbild)."""
import glob
import math

import bpy

from .materialien import auswahl
from .util import box, neues_objekt, pfad, treiber_modus


def baue(staerke=1.0, drehung_grad=0.0, sonne=1.2, dunst=0.0012):
    datei = glob.glob(pfad("assets", "polyhaven", "hdris", auswahl()["hdri_himmel"], "*.hdr"))[0]
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("Welt")
    sc.world = w
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(drehung_grad))
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(datei, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = staerke
    aus = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], aus.inputs["Surface"])

    for name in ("Sonne", "Dunst"):
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    licht = bpy.data.lights.get("Sonne") or bpy.data.lights.new("Sonne", "SUN")
    licht.energy = sonne
    licht.angle = math.radians(6.0)
    licht.color = (1.0, 0.97, 0.92)
    o = neues_objekt("Sonne", licht, "06_Licht")
    o.rotation_euler = (math.radians(50.0), 0.0, math.radians(140.0))

    m = bpy.data.materials.get("M_Dunst") or bpy.data.materials.new("M_Dunst")
    mnt = m.node_tree
    mnt.nodes.clear()
    vol = mnt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = dunst
    vol.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1.0)
    maus = mnt.nodes.new("ShaderNodeOutputMaterial")
    mnt.links.new(vol.outputs[0], maus.inputs["Volume"])
    d = box("Dunst", (140.0, 140.0, 40.0), (0.0, 0.0, -1.0), "06_Licht", mat=m)
    d.display_type = "WIRE"
    treiber_modus(d, "hide_viewport", "m < 0.5")
    return {"hdri": datei}
```

- [ ] **Schritt 3: Ausführen, speichern, Prüfung.** Erwartet: `ok: true`.
- [ ] **Schritt 4: Commit** `git add scripts && git commit -m "Himmel, Sonne, Dunst"`

---

### Task 10: Cycles-Testrender des Rohbaus

- [ ] **Schritt 1: Speichern und rendern** (50 %, 128 Samples)

```bash
bash "/d/KI Projekte/Blender MArtists/scripts/render.sh" "D:/KI Projekte/Blender MArtists/renders/02_rohbau_cycles.png" CYCLES 128 50 Kamera_Referenz 1
```

- [ ] **Schritt 2: Bild ansehen und mit der Referenz vergleichen.** Nachjustiert wird über die Parameter, nicht über den Code:

| Befund | Korrektur |
|---|---|
| Bild zu hell/dunkel | `welt.baue(staerke=…)` (0,5–2,0) |
| Schatten zu hart | `sonne` kleiner (0,5–1,0) |
| Holz läuft waagerecht | bei `M_Holzfassade`/`M_Traufe` in `TEXTUR_MATS` `vertikal` umschalten |
| Texturen zu grob/fein | `skala` in `TEXTUR_MATS` anpassen |
| Fugen zu breit/schmal | `0.015` in `_fugen_maske` ändern |
| Platten zu hell | `tint` von `M_Polygonalplatten` absenken |

Höchstens 3 Durchläufe.

- [ ] **Schritt 3: Commit** `git add scripts && git commit -m "Rohbau-Feinabstimmung"`

---

### Task 11: Streu-Knoten, Beete und Rasen

**Dateien:** Neu: `scripts/gartenlib/gn.py`, `scripts/gartenlib/gelaende.py`, `scripts/gartenlib/pflanzen.py` (Teil 1)

- [ ] **Schritt 1: Prüfung `rasen()`.** Erwartet: `ok: false`, „Rasen oder Modifier fehlt“.

- [ ] **Schritt 2: `gn.py` schreiben**

```python
"""Geometry-Nodes-Gruppe GN_Streuen: verteilt Instanzen einer Bibliothek auf Flächen, mit Abstand zu Ausschluss-Geometrie."""
import bpy

from .util import gn_kennung, gn_setze, treiber_modus

NAME = "GN_Streuen"


def _sock(sammlung, name, typ=None):
    for s in sammlung:
        if s.name == name and (typ is None or s.type == typ) and getattr(s, "enabled", True):
            return s
    raise KeyError(f"{name}/{typ}")


def streuer():
    alt = bpy.data.node_groups.get(NAME)
    if alt is not None:
        bpy.data.node_groups.remove(alt)
    ng = bpy.data.node_groups.new(NAME, "GeometryNodeTree")
    i = ng.interface
    i.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    i.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    i.new_socket("Bibliothek", in_out="INPUT", socket_type="NodeSocketCollection")
    i.new_socket("Ausschluss", in_out="INPUT", socket_type="NodeSocketCollection")
    for name, wert, typ in [("Dichte", 10.0, "NodeSocketFloat"), ("Mindestabstand", 0.1, "NodeSocketFloat"),
                            ("Ausschluss_Abstand", 0.05, "NodeSocketFloat"), ("Skala_Min", 0.8, "NodeSocketFloat"),
                            ("Skala_Max", 1.2, "NodeSocketFloat"), ("Neigung", 0.1, "NodeSocketFloat"),
                            ("Seed", 0, "NodeSocketInt"), ("Basis_behalten", False, "NodeSocketBool")]:
        i.new_socket(name, in_out="INPUT", socket_type=typ).default_value = wert

    N, Lk = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    vert = N.new("GeometryNodeDistributePointsOnFaces")
    vert.distribute_method = "POISSON"
    Lk.new(gi.outputs["Geometry"], vert.inputs["Mesh"])
    Lk.new(gi.outputs["Mindestabstand"], vert.inputs["Distance Min"])
    Lk.new(gi.outputs["Dichte"], vert.inputs["Density Max"])
    Lk.new(gi.outputs["Seed"], vert.inputs["Seed"])

    ci_a = N.new("GeometryNodeCollectionInfo")
    ci_a.transform_space = "RELATIVE"
    Lk.new(gi.outputs["Ausschluss"], ci_a.inputs["Collection"])
    real = N.new("GeometryNodeRealizeInstances")
    Lk.new(ci_a.outputs[0], real.inputs[0])
    prox = N.new("GeometryNodeProximity")
    prox.target_element = "FACES"
    Lk.new(real.outputs[0], prox.inputs[0])
    cmp = N.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "LESS_THAN"
    Lk.new(_sock(prox.outputs, "Distance"), _sock(cmp.inputs, "A", "VALUE"))
    Lk.new(gi.outputs["Ausschluss_Abstand"], _sock(cmp.inputs, "B", "VALUE"))
    loe = N.new("GeometryNodeDeleteGeometry")
    loe.domain = "POINT"
    Lk.new(vert.outputs["Points"], loe.inputs["Geometry"])
    Lk.new(cmp.outputs["Result"], loe.inputs["Selection"])

    ci_b = N.new("GeometryNodeCollectionInfo")
    ci_b.transform_space = "ORIGINAL"
    ci_b.inputs["Separate Children"].default_value = True
    ci_b.inputs["Reset Children"].default_value = True
    Lk.new(gi.outputs["Bibliothek"], ci_b.inputs["Collection"])

    def zufall(typ, mn, mx, plus):
        r = N.new("FunctionNodeRandomValue")
        r.data_type = typ
        st = "INT" if typ == "INT" else "VALUE"
        for name, w in (("Min", mn), ("Max", mx)):
            s = _sock(r.inputs, name, st)
            if isinstance(w, (int, float)):
                s.default_value = w
            else:
                Lk.new(w, s)
        add = N.new("ShaderNodeMath")
        add.operation = "ADD"
        Lk.new(gi.outputs["Seed"], add.inputs[0])
        add.inputs[1].default_value = plus
        Lk.new(add.outputs[0], r.inputs["Seed"])
        return _sock(r.outputs, "Value", st)

    neg = N.new("ShaderNodeMath")
    neg.operation = "MULTIPLY"
    Lk.new(gi.outputs["Neigung"], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    rot = N.new("ShaderNodeCombineXYZ")
    Lk.new(zufall("FLOAT", neg.outputs[0], gi.outputs["Neigung"], 2), rot.inputs["X"])
    Lk.new(zufall("FLOAT", neg.outputs[0], gi.outputs["Neigung"], 3), rot.inputs["Y"])
    Lk.new(zufall("FLOAT", 0.0, 6.2832, 1), rot.inputs["Z"])

    iop = N.new("GeometryNodeInstanceOnPoints")
    Lk.new(loe.outputs["Geometry"], iop.inputs["Points"])
    Lk.new(ci_b.outputs[0], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    Lk.new(zufall("INT", 0, 9999, 5), iop.inputs["Instance Index"])
    Lk.new(rot.outputs[0], iop.inputs["Rotation"])
    Lk.new(zufall("FLOAT", gi.outputs["Skala_Min"], gi.outputs["Skala_Max"], 4), iop.inputs["Scale"])

    join = N.new("GeometryNodeJoinGeometry")
    Lk.new(gi.outputs["Geometry"], join.inputs[0])
    Lk.new(iop.outputs["Instances"], join.inputs[0])
    sw = N.new("GeometryNodeSwitch")
    sw.input_type = "GEOMETRY"
    Lk.new(gi.outputs["Basis_behalten"], sw.inputs["Switch"])
    Lk.new(iop.outputs["Instances"], sw.inputs["False"])
    Lk.new(join.outputs[0], sw.inputs["True"])
    Lk.new(sw.outputs[0], go.inputs["Geometry"])
    return ng


def anwenden(obj, modname, bibliothek, ausschluss, dichte_lauf, dichte_schoen, abstand=0.1,
             skala=(0.8, 1.2), neigung=0.1, seed=0, basis=False, ausschluss_abstand=0.05):
    ng = bpy.data.node_groups.get(NAME) or streuer()
    mod = obj.modifiers.get(modname) or obj.modifiers.new(modname, "NODES")
    mod.node_group = ng
    gn_setze(mod, "Bibliothek", bpy.data.collections[bibliothek])
    gn_setze(mod, "Ausschluss", bpy.data.collections[ausschluss])
    gn_setze(mod, "Mindestabstand", float(abstand))
    gn_setze(mod, "Ausschluss_Abstand", float(ausschluss_abstand))
    gn_setze(mod, "Skala_Min", float(skala[0]))
    gn_setze(mod, "Skala_Max", float(skala[1]))
    gn_setze(mod, "Neigung", float(neigung))
    gn_setze(mod, "Seed", int(seed))
    gn_setze(mod, "Basis_behalten", bool(basis))
    kennung = gn_kennung(ng, "Dichte")
    treiber_modus(obj, f'modifiers["{modname}"]["{kennung}"]',
                  f"{dichte_lauf} + ({dichte_schoen} - {dichte_lauf}) * m")
    return mod
```

- [ ] **Schritt 3: `gelaende.py` schreiben**

```python
"""Beetflächen (Mulch) als ebene Polygone knapp über dem Boden."""
import bmesh

from . import layout as L
from .util import leere, material, mesh_aus_bmesh


def _flaeche(punkte):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(punkte, punkte[1:] + punkte[:1])) / 2


def beete():
    leere("01a_Beete")
    m = material("M_Beet", (0.08, 0.06, 0.04), 0.9)
    for name, punkte in L.BEETE.items():
        if _flaeche(punkte) < 0:
            punkte = list(reversed(punkte))
        bm = bmesh.new()
        bm.faces.new([bm.verts.new((x, y, 0.01)) for x, y in punkte])
        mesh_aus_bmesh(name, bm, "01a_Beete", mats=[m])
    return {"beete": list(L.BEETE)}
```

- [ ] **Schritt 4: `pflanzen.py` (Teil 1: Material, Halme, Rasen) schreiben**

```python
"""Pflanzen: Materialien, Halm-/Gras-/Staudenbibliotheken, Rasen, Bepflanzung, Poly-Haven-Sträucher."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import gn
from . import layout as L
from .util import leere, material, mesh_aus_bmesh


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
    from .materialien import mix_farbe, mathe
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
    zufall = mathe(nt, "MULTIPLY_ADD", geo.outputs["Random Per Island"], 0.3, mathe(nt, "MULTIPLY", oi.outputs["Random"], 0.7))
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


def halm_bibliothek():
    leere("Bib_Halme")
    m = pflanzen_material("M_Gras", [(0.0, (0.025, 0.06, 0.012)), (0.5, (0.05, 0.11, 0.02)),
                                     (0.85, (0.09, 0.15, 0.03)), (1.0, (0.20, 0.19, 0.08))],
                          durchscheinend=0.3, spitze=((0.22, 0.22, 0.09), 0.5))
    rnd = random.Random(3)
    for k in range(8):
        bm = bmesh.new()
        for _ in range(rnd.randint(10, 18)):
            w = rnd.uniform(0, 2 * math.pi)
            r = 0.035 * math.sqrt(rnd.random())
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
    gn.anwenden(o, "Rasen", "Bib_Halme", "Maske_Rasen", dichte_lauf=60, dichte_schoen=300, abstand=0.03,
                skala=(0.7, 1.2), neigung=0.15, seed=1, basis=True)
    return {"rasen": o.name}
```

- [ ] **Schritt 5: Ausführen.** Nacheinander per MCP-Aufruf:
1. `gn.streuer()`
2. `gelaende.beete()`
3. `pflanzen.rasen()`
4. `util.speichern()`

- [ ] **Schritt 6: Prüfung `rasen()`.** Erwartet: `ok: true`, `instanzen` > 10 000, kein Gras auf dem Hof.
- Wächst Gras auf dem Hof: prüfen, ob `Maske_Rasen` die Collection `04_Hardscape` enthält.
- Sind es 0 Instanzen, die Teilprüfung „leere Ausschluss-Collection liefert Abstand 0“ machen: `Ausschluss_Abstand` testweise auf −1 setzen. Kommen dann Instanzen, liegt es an der Maske.

- [ ] **Schritt 7: Testrender** (CYCLES, 128 Samples, 50 %) nach `renders/03_rasen.png` und ansehen.
- Soll: gemähter, feinkörniger Rasen ohne sichtbares Muster.
- Bei Bedarf Halmhöhe (0,05–0,12) oder Farben in `halm_bibliothek` anpassen.

- [ ] **Schritt 8: Commit** `git add scripts && git commit -m "Streu-Knoten, Beete, Rasen"`

---

### Task 12: Ziergräser, Stauden und Beetbepflanzung

**Dateien:** Ändern: `scripts/gartenlib/pflanzen.py` (Funktionen anhängen)

- [ ] **Schritt 1: Prüfung `bepflanzung()`.** Erwartet: `ok: false`.

- [ ] **Schritt 2: Funktionen an `pflanzen.py` anhängen**

```python
def graeser_bibliothek():
    leere("Bib_Graeser")
    m_gras = pflanzen_material("M_Ziergras", [(0.0, (0.06, 0.10, 0.03)), (0.5, (0.14, 0.16, 0.06)), (1.0, (0.32, 0.28, 0.14))],
                               durchscheinend=0.35, spitze=((0.45, 0.40, 0.22), 0.7))
    m_rispe = pflanzen_material("M_Grasbluete", [(0.0, (0.55, 0.50, 0.40)), (1.0, (0.75, 0.70, 0.60))],
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
        if k < 3:  # Rispen (Federgras-/Chinaschilf-Optik)
            for _ in range(rnd.randint(15, 30)):
                w = rnd.uniform(0, 2 * math.pi)
                r = 0.08 * math.sqrt(rnd.random())
                basis = (math.cos(w) * r, math.sin(w) * r, 0.0)
                richtung = (math.cos(w), math.sin(w))
                hh, ng = h * rnd.uniform(1.15, 1.35), rnd.uniform(0.05, 0.2)
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
            l = rnd.uniform(0.12, 0.2)
            pts = [b0, b0 + d * l * 0.4 + q * 0.035 + Vector((0, 0, 0.05)),
                   b0 + d * l + Vector((0, 0, 0.04)), b0 + d * l * 0.4 - q * 0.035 + Vector((0, 0, 0.05))]
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
```

- [ ] **Schritt 3: Ausführen.** Nacheinander per MCP-Aufruf:
1. `pflanzen.graeser_bibliothek()`
2. `pflanzen.stauden_bibliothek()`
3. `pflanzen.bepflanzung()`
4. `util.speichern()`

- [ ] **Schritt 4: Prüfung `bepflanzung()`.** Erwartet: `ok: true`.

- [ ] **Schritt 5: Testrender** `renders/04_beete.png` (CYCLES, 128, 50 %) ansehen.
- Soll: überhängende Grashorste, helle Rispen, weiße Blütentupfer, Mulch kaum sichtbar.
- Gegebenenfalls Dichten in `layout._mix` oder Höhen in den Bibliotheken anpassen (höchstens 3 Runden).

- [ ] **Schritt 6: Commit** `git add scripts && git commit -m "Ziergräser, Stauden, Beetbepflanzung"`

---

### Task 13: Poly-Haven-Sträucher als Polster

**Dateien:** Ändern: `scripts/gartenlib/pflanzen.py` (Funktion anhängen)

- [ ] **Schritt 1: Prüfung `polster()`.** Erwartet: `ok: false`, „Bib_Polster leer“.

- [ ] **Schritt 2: Funktion anhängen**

```python
def polyhaven_polster(breite_ziel=1.0):
    """Hängt die gewählten Poly-Haven-Strauchmodelle an, legt Transformationen in die Mesh-Daten und normiert die Breite."""
    import glob
    from mathutils import Matrix
    from .materialien import auswahl
    from .util import pfad
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
```

- [ ] **Schritt 3: Ausführen, speichern, Prüfung.** Erwartet: `ok: true`.
- Die Sträucher erscheinen automatisch in den Beeten, weil die Bepflanzung `Bib_Polster` schon referenziert.
- Die Prüfung misst Objektmaße. Da hier die Mesh-Daten skaliert werden, sind die Maße rund 1,0 m.

- [ ] **Schritt 4: Testrender** `renders/05_polster.png` ansehen. Es müssen dichte, runde Polster zwischen den Gräsern stehen.
- [ ] **Schritt 5: Commit** `git add scripts && git commit -m "Poly-Haven-Sträucher als Polster"`

---

### Task 14: Bäume mit Sapling

**Dateien:** Neu: `scripts/gartenlib/baeume.py`

- [ ] **Schritt 1: FREIGABE für die Erweiterung.**
- Stephan fragen: „Darf ich die kostenlose Blender-Erweiterung ‚Sapling Tree Gen‘ von extensions.blender.org installieren (wenige hundert KB)?“
- **Ohne Ja geht es nicht weiter.**

- [ ] **Schritt 2: Installieren** (MCP)

```python
import bpy
import sys
P = r"D:\KI Projekte\Blender MArtists\scripts"
if P not in sys.path:
    sys.path.insert(0, P)
from gartenlib.util import view3d_kontext
repos = bpy.context.preferences.extensions.repos
idx = next(i for i, r in enumerate(repos) if r.module == "blender_org")
with bpy.context.temp_override(**view3d_kontext()):
    bpy.ops.extensions.repo_sync(repo_index=idx)
    bpy.ops.extensions.package_install(repo_index=idx, pkg_id="sapling_tree_gen")
result = {"tree_add": hasattr(bpy.ops.curve, "tree_add")}
```

- Erwartet: `{"tree_add": true}`.
- Klappt das nicht, installiert Stephan die Erweiterung selbst über Edit › Preferences › Get Extensions › „Sapling Tree Gen“ › Install.

- [ ] **Schritt 3: Prüfung `baeume()`.** Erwartet: `ok: false`.

- [ ] **Schritt 4: `baeume.py` schreiben**

```python
"""Birken und Ahorn mit Sapling Tree Gen; Birkenrinde prozedural, Ahornrinde von Poly Haven."""
import ast
import os

import addon_utils
import bpy

from . import layout as L
from .materialien import mathe, mix_farbe, pbr
from .pflanzen import pflanzen_material
from .util import layer_collection, leere, neues_objekt, view3d_kontext

PRESET_KANDIDATEN = {"birke": ["birch", "aspen"], "ahorn": ["maple", "tupelo", "aspen"]}


def _sapling_ordner():
    for m in addon_utils.modules():
        if "sapling" in m.__name__.lower():
            return os.path.join(os.path.dirname(m.__file__), "presets")
    raise RuntimeError("Sapling Tree Gen ist nicht installiert")


def presets():
    return sorted(os.listdir(_sapling_ordner()))


def _preset(art):
    ordner = _sapling_ordner()
    dateien = os.listdir(ordner)
    for teil in PRESET_KANDIDATEN[art]:
        treffer = [d for d in dateien if teil in d.lower()]
        if treffer:
            with open(os.path.join(ordner, treffer[0]), encoding="utf-8") as f:
                text = f.read()
            return ast.literal_eval(text[text.index("{"): text.rindex("}") + 1])
    raise FileNotFoundError(f"Kein Sapling-Preset für {art}: {dateien}")


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
    einst = _preset(art)
    erlaubt = set(bpy.ops.curve.tree_add.get_rna_type().properties.keys())
    einst = {k: v for k, v in einst.items() if k in erlaubt}
    einst.update(dict(do_update=True, bevel=True, showLeaves=True, useArm=False, seed=seed))
    bpy.context.view_layer.active_layer_collection = layer_collection("05e_Baeume")
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    vorher = set(bpy.data.objects)
    with bpy.context.temp_override(**view3d_kontext()):
        bpy.ops.curve.tree_add(**einst)
    neu = [o for o in bpy.data.objects if o not in vorher]
    stamm = next(o for o in neu if o.type == "CURVE")
    laub = next((o for o in neu if o.type == "MESH"), None)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(stamm.evaluated_get(dg))
    me.materials.clear()
    me.materials.append(rinde_mat)
    obj = neues_objekt(name, me, "05e_Baeume")
    if laub is not None:
        laub.name = f"{name}_Laub"
        laub.parent = obj
        laub.data.materials.clear()
        laub.data.materials.append(laub_mat)
    for o in neu:
        if o is not laub and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    hmax = max(v.co.z for v in me.vertices)
    if laub is not None:
        hmax = max(hmax, max(v.co.z for v in laub.data.vertices))
    k = hoehe / hmax
    obj.scale = (k, k, k)
    obj.location = (ort[0], ort[1], 0.0)
    obj.rotation_euler = (0.0, 0.0, seed * 1.3)
    return obj


def baue():
    leere("05e_Baeume")
    birke_rinde = rinde_birke()
    ahorn_rinde = pbr("M_Rinde_Ahorn", "tex_rinde_ahorn", skala=0.8)
    birke_laub = pflanzen_material("M_Blatt_Birke", [(0.0, (0.05, 0.10, 0.02)), (0.6, (0.10, 0.17, 0.04)),
                                                     (1.0, (0.20, 0.24, 0.06))], durchscheinend=0.4, alpha_ellipse=True)
    ahorn_laub = pflanzen_material("M_Blatt_Ahorn", [(0.0, (0.10, 0.12, 0.02)), (0.5, (0.22, 0.22, 0.04)),
                                                     (1.0, (0.35, 0.30, 0.06))], durchscheinend=0.4, alpha_ellipse=True)
    for name, art, ort, hoehe, seed in L.BAEUME:
        if art == "birke":
            baum(name, art, ort, hoehe, seed, birke_laub, birke_rinde)
        else:
            baum(name, art, ort, hoehe, seed, ahorn_laub, ahorn_rinde)
    return {"baeume": [b[0] for b in L.BAEUME]}
```

- [ ] **Schritt 5: Presets ansehen.** MCP-Aufruf `baeume.presets()`.
- Erwartet: eine Liste mit Dateinamen, darunter etwas mit „birch“.
- Fehlt „maple“, nutzt der Code automatisch „tupelo“ oder „aspen“.

- [ ] **Schritt 6: Ausführen, speichern, Prüfung `baeume()`.** Erwartet: `ok: true`.
- Fehlt Laub: prüfen, ob `laub.data.uv_layers` existiert.
- Gibt es keine UV-Map, in `pflanzen_material` die Option `alpha_ellipse` für Laub abschalten (Blätter werden dann als Vierecke gerendert) und das in den Notizen festhalten.

- [ ] **Schritt 7: Testrender** `renders/06_baeume.png` ansehen. Soll:
- weiße Birkenstämme mit dunklen Querstreifen und lockere, durchscheinende Kronen
- der Ahorn links vorn mit olivgelbem Laub, das ins Bild ragt

Zu dichte oder kahle Kronen über den Sapling-Parameter `leaves` in `einst.update(...)` regeln (höchstens 3 Runden).

- [ ] **Schritt 8: Commit** `git add scripts && git commit -m "Bäume mit Sapling"`

---

### Task 15: Qualitätsprobe

- [ ] **Schritt 1: Speichern und in voller Qualität rendern** (1920 × 1080, 1024 Samples, Modus Schönbild), im Hintergrund

```bash
bash "/d/KI Projekte/Blender MArtists/scripts/render.sh" "D:/KI Projekte/Blender MArtists/renders/qualitaetsprobe.png" CYCLES 1024 100 Kamera_Referenz 1
```

- [ ] **Schritt 2: Prüfung `qualitaetsprobe()`.** Erwartet: `ok: true`.

- [ ] **Schritt 3: Selbst bewerten.** `renders/qualitaetsprobe.png` und `docs/referenz/bild2.webp` ansehen und je Bereich eine ehrliche Note geben (passt / nah dran / deutlich schwächer):
- Rasen, Ziergräser, Stauden
- Platten und Feuerstelle, Fassaden
- Licht und Himmel, Bäume

- [ ] **Schritt 4: ENTSCHEIDUNG.**
- Stephan bekommt das Bild (SendUserFile), die Bewertung und höchstens drei konkrete Verbesserungsvorschläge.
- Gefragt wird: „Weiter mit Teil 2 (Grundstück, Erdgeschoss innen, Laufen), oder zuerst nachbessern?“
- **Hier endet Teil 1.**

- [ ] **Schritt 5: Commit** `git add scripts docs && git commit -m "Qualitätsprobe Teil 1"`

---

## Selbstprüfung des Plans (erledigt beim Schreiben)

**Abdeckung der Spec (Schritte 1–4):**

| Design-Schritt | Umgesetzt in |
|---|---|
| Einrichtung | Task 0–2 |
| Referenzkamera und Rohbau | Task 3–5 |
| Materialien und Himmel | Task 6–10 |
| Bepflanzung | Task 11–14 |
| Qualitätsprobe | Task 15 |

- Der Umschalter „Laufen/Schönbild“ ist über `treiber_modus` in allen Streu-Modifiern und im Dunst eingebaut.
- Die Eevee-Schattenqualität per Treiber kommt in Teil 2 (Lauf-Tuning), weil sie erst mit fps-Messung sinnvoll ist.

**Einheitliche Namen:**
- Collections, Bibliotheken (`Bib_*`), Masken (`Maske_Rasen`, `Maske_Beet`) und Modifier-Namen (`Rasen`, `Streuen`) sind zwischen `setup.py`, `pflanzen.py`, `gn.py` und `pruefung.py` abgeglichen.
- Die Objektnamen in `pruefung.architektur/hardscape` entsprechen denen in `architektur.py`/`hardscape.py`.

**Bekannte Risiken mit Gegenmaßnahme im Plan:**
- Boolean-Operanden in versteckten Collections (Task 3, Schritt 5)
- Maske bei leerer Collection (Task 11, Schritt 6)
- Sapling ohne Ahorn-Preset oder ohne Laub-UV (Task 14, Schritt 5/6)
- Eevee-Optionsnamen in 5.1 (`setze` protokolliert statt abzubrechen)
