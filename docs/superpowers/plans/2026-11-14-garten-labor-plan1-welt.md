# Garten-Labor – Plan 1: Welt auf dem iPad – Umsetzungsplan

> **Für ausführende Agenten:** BENÖTIGTER SUB-SKILL: superpowers:subagent-driven-development (empfohlen) oder superpowers:executing-plans, um den Plan Aufgabe für Aufgabe abzuarbeiten. Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Garten und Haus-Erdgeschoss (als Labor-Rohbau) sind als Web-3D-Welt auf PC und Standard-iPad begehbar, mit Kollision, vorberechnetem Licht und ≥ 30 Bildern/s. Ausgeliefert wird über Coolify von GitHub.

**Architektur:**
- Blender (`labor.blend`) ist das Studio. Das Python-Modul `gartenlib/webexport.py` erzeugt im Hintergrundmodus:
  - Lightmap-gebackene Bauteile
  - instanzierte Pflanzen
  - Bäume mit Blatttexturen
  - Kollisionsgeometrie
  - Himmel, Rasenmaske und Weltkonfiguration
- Ein Node-Skript optimiert die GLB-Dateien (Meshopt, WebP) und prüft das Leistungsbudget.
- Die Web-App (Vite + Three.js + three-mesh-bvh) lädt die Welt und steuert per Tastatur/Maus oder Touch.
- Ein Flask-Server liefert alles aus, als Docker-Image über Coolify.

**Tech-Stack:** Blender 5.1.1 (bpy, Cycles-Bake), Node 25 / npm 11, Vite, Three.js, three-mesh-bvh, gltf-transform, sharp, vitest, Python 3.14 (lokal) bzw. 3.13 (Docker), Flask, gunicorn, pytest, Docker, Coolify, GitHub.

**Spec:** `docs/superpowers/specs/2026-11-14-garten-labor-design.md` (dieser Plan deckt dort „Welt“, „Steuerung“, „Weg von Blender ins Web“, „Server – Auslieferung“ und die Leistungsziele ab).

**Plan 2 (danach):** Arten und Tiere, Sammelbuch, Mikroskop-Ansicht, Whiteboard-Editor, Auftrag, Anmeldung, Lehrerseite.

---

## Konventionen

**Pfade**
- Projekt: `D:\KI Projekte\Blender MArtists`
- Branch: `garten-labor`
- **`garten.blend` wird nie verändert.** Gearbeitet wird ausschließlich in `labor.blend`.

**MCP-Aufruf** (Blender-UI mit geöffneter `labor.blend`):

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

**Blender im Hintergrund:**
`"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b "D:/KI Projekte/Blender MArtists/labor.blend" -P <skript> -- <argumente>`

**Rendern:** `BLEND="D:/KI Projekte/Blender MArtists/labor.blend" bash scripts/render.sh …` (ab Task 0 unterstützt `render.sh` die Variable `BLEND`).

**Koordinaten Blender → Three.js:** `(x, y, z)_three = (x, z, -y)`. Für Quaternionen gilt `(qx, qy, qz, qw)_three = (qx, qz, -qy, qw)`.

**Commits:** am Ende jeder Aufgabe auf `garten-labor`, mit Co-Author-Zeile.

---

## Dateistruktur

| Datei | Aufgabe |
|---|---|
| `scripts/render.sh` | ändern: `BLEND`-Variable |
| `scripts/gartenlib/labor.py` | neu: Labor-Rohbau im EG (Boden, Licht, Whiteboard-Fläche, Labortische, Mikroskop, Regal mit Sammelgläsern) |
| `scripts/gartenlib/webexport.py` | neu: Export der Webfassung (Bake, Pflanzen, Bäume, Kollision, Himmel, Maske, `welt.json`) |
| `pipeline/blender/labor_bauen.py` | neu: CLI-Einstieg Labor |
| `pipeline/blender/web_export.py` | neu: CLI-Einstieg Webexport |
| `web/package.json`, `web/vite.config.js`, `web/index.html`, `web/style.css` | neu: Web-App-Gerüst |
| `web/src/logik/joystick.js`, `bewegung.js`, `rasenmaske.js` | neu: reine Logik (mit Tests) |
| `web/src/welt.js`, `steuerung.js`, `kollision.js`, `gras.js`, `leistung.js`, `main.js` | neu: 3D-Teile |
| `web/public/sw.js` | neu: Service Worker |
| `web/public/welt/*` | erzeugt: GLB, Texturen, JSON, BIN (eingecheckt) |
| `web/tools/optimieren.mjs` | neu: Optimierung und Budgetprüfung |
| `web/tests/*.test.js` | neu: vitest |
| `server/app.py`, `server/requirements.txt`, `server/tests/test_app.py` | neu |
| `Dockerfile`, `.dockerignore` | neu |
| `.gitignore` | ändern |

---

### Task 0: Branch vorbereiten

**Dateien:** Ändern: `.gitignore`, `scripts/render.sh`. Neu: `labor.blend` (nicht in Git).

- [ ] **Schritt 1: Branch prüfen und `labor.blend` anlegen**

```bash
cd "/d/KI Projekte/Blender MArtists" && git branch --show-current && cp garten.blend labor.blend && ls -la labor.blend garten.blend
```

Erwartet: `garten-labor`, beide Dateien vorhanden, gleich groß.

- [ ] **Schritt 2: `.gitignore` ergänzen** (anhängen)

```
web/node_modules/
web/dist/
server/.venv/
server/**/__pycache__/
*.sqlite
```

- [ ] **Schritt 3: `scripts/render.sh` auf wählbare Datei umstellen.** Die Blender-Zeile ersetzen durch:

```bash
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b "${BLEND:-$DIR/../garten.blend}" -P "$DIR/render_cli.py" -- "$@"
```

- [ ] **Schritt 4: `labor.blend` in der Blender-UI öffnen** (MCP)

```python
import bpy
bpy.ops.wm.open_mainfile(filepath=r"D:\KI Projekte\Blender MArtists\labor.blend")
result = {"datei": bpy.data.filepath}
```

Erwartet: `…\labor.blend`.

- [ ] **Schritt 5: Commit** `git add .gitignore scripts/render.sh && git commit -m "Branch garten-labor vorbereitet"`

---

### Task 1: Labor-Rohbau im Erdgeschoss

**Dateien:** Neu: `scripts/gartenlib/labor.py`, `pipeline/blender/labor_bauen.py`

- [ ] **Schritt 1: `labor.py` schreiben**

```python
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
    ecken = [p - n * 0.016 + a * sa * b / 2 + Vector((0, 0, zc + sz * h / 2)) for sa, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new([bm.verts.new(e) for e in ecken])
    for loop, k in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = k
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
```

- [ ] **Schritt 2: Prüfung an `pruefung.py` anhängen** (sie schlägt fehl, bis das Labor gebaut ist)

```python
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
```

Prüfaufruf `labor()`: erwartet `ok: false`.

- [ ] **Schritt 3: CLI-Einstieg `pipeline/blender/labor_bauen.py`**

```python
"""blender -b labor.blend -P pipeline/blender/labor_bauen.py – baut das Labor und speichert labor.blend."""
import os
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
sys.path.insert(0, P)
import gartenlib  # noqa: E402

print(gartenlib.lade("labor").baue())
gartenlib.lade("util").speichern()
print("FERTIG labor")
```

- [ ] **Schritt 4: Ausführen** (MCP, `labor.blend` ist offen)
1. `labor.baue()`
2. `innenraum.sonden_backen()`
3. `util.speichern()`

Prüfaufruf `labor()`: erwartet `ok: true`.

- [ ] **Schritt 5: Sichtprüfung**

```bash
cd "/d/KI Projekte/Blender MArtists" && BLEND="D:/KI Projekte/Blender MArtists/labor.blend" bash scripts/render.sh "D:/KI Projekte/Blender MArtists/renders/20_labor.png" CYCLES 256 50 Kamera_Innen 1
```

Bild ansehen. Soll:
- helles Labor mit Arbeitsinsel und Hockern, Whiteboard an der Westwand
- Mikroskoptisch unter dem Nordfenster, Regal mit Gläsern an der Ostwand
- keine Wohnungsmöbel mehr

- [ ] **Schritt 6: Commit** `git add scripts pipeline && git commit -m "Labor-Rohbau im Erdgeschoss"`

---

### Task 2: Webexport – Grundlagen, Himmel, Rasenmaske, Weltkonfiguration

**Dateien:** Neu: `scripts/gartenlib/webexport.py` (Teil 1), `pipeline/blender/web_export.py`

- [ ] **Schritt 1: `webexport.py` Teil 1 schreiben**

```python
"""Webfassung der Szene für Three.js (iPad-tauglich). Läuft im Hintergrund auf labor.blend:
blender -b labor.blend -P pipeline/blender/web_export.py -- <zielordner> [teil1,teil2,…]
Die Szene wird nur im Speicher verändert, labor.blend wird nicht gespeichert."""
import json
import math
import os
import struct

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import layout as L
from .util import collection, leere, modus_setzen

TMP = "WEB_TMP"


def drei(v):
    """Blender (Z oben) → Three.js (Y oben)."""
    return [round(v[0], 4), round(v[2], 4), round(-v[1], 4)]


def vorbereiten():
    if not bpy.data.filepath.lower().endswith("labor.blend"):
        raise RuntimeError("Webexport nur aus labor.blend")
    cp = bpy.context.preferences.addons["cycles"].preferences
    cp.compute_device_type = "OPTIX"
    cp.refresh_devices()
    for d in cp.devices:
        d.use = d.type == "OPTIX"
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    modus_setzen(0.0)
    collection(TMP)
    leere(TMP)


def auswahl_setzen(objekte, aktiv=None):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objekte:
        o.select_set(True)
    bpy.context.view_layer.objects.active = aktiv or (objekte[0] if objekte else None)


def kopie(o, dg):
    """Ausgewertete Kopie (Modifier angewandt, Weltkoordinaten in den Daten) in WEB_TMP.
    Objekte mit Geometry Nodes (Rasen, Wiese) liefern nur ihr Grundnetz – die Pflanzen kommen als Instanzen."""
    if any(m.type == "NODES" for m in o.modifiers):
        me = o.data.copy()
    else:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    k = bpy.data.objects.new(f"WEB_{o.name}", me)
    bpy.data.collections[TMP].objects.link(k)
    return k


def vereinen(name, objekte):
    objekte = [o for o in objekte if o.type == "MESH" and len(o.data.polygons)]
    if len(objekte) > 1:
        with bpy.context.temp_override(active_object=objekte[0], selected_editable_objects=objekte,
                                       selected_objects=objekte):
            bpy.ops.object.join()
    o = objekte[0]
    o.name = name
    o.data.name = name
    return o


def exportieren(objekte, pfad, materialien=True):
    auswahl_setzen(objekte)
    bpy.ops.export_scene.gltf(filepath=pfad, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials="EXPORT" if materialien else "NONE",
                              export_image_format="AUTO", export_animations=False, export_skins=False,
                              export_morph=False, export_cameras=False, export_lights=False)


def himmel(ziel):
    """HDRI als 2048×1024-JPG (bewölkter Himmel als Hintergrund)."""
    env = [n for n in bpy.context.scene.world.node_tree.nodes if n.type == "TEX_ENVIRONMENT"][0]
    img = env.image.copy()
    img.scale(2048, 1024)
    img.filepath_raw = os.path.join(ziel, "himmel.jpg")
    img.file_format = "JPEG"
    img.save()
    bpy.data.images.remove(img)


def rasenmaske(ziel, aufloesung=0.1):
    """1 Byte je 10 cm: 255 = Rasen (keine Maske-Geometrie in der Nähe), 0 = sonst. Zeilen laufen in +z (Three.js)."""
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in bpy.data.collections["Maske_Rasen"].all_objects:
        if o.type not in ("MESH", "CURVE"):
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        start = len(verts)
        verts += [v.co.copy() for v in me.vertices]
        polys += [[start + i for i in p.vertices] for p in me.polygons]
        bpy.data.meshes.remove(me)
    baum = BVHTree.FromPolygons(verts, polys)
    x0, y0, x1, y1 = L.GRUNDSTUECK
    breite, hoehe = int((x1 - x0) / aufloesung), int((y1 - y0) / aufloesung)
    daten = bytearray(breite * hoehe)
    for iz in range(hoehe):
        y = y1 - (iz + 0.5) * aufloesung                     # Three z = -Blender y
        for ix in range(breite):
            x = x0 + (ix + 0.5) * aufloesung
            treffer = baum.find_nearest(Vector((x, y, 0.0)), 0.15)
            daten[iz * breite + ix] = 0 if treffer[0] is not None else 255
    with open(os.path.join(ziel, "rasenmaske.bin"), "wb") as f:
        f.write(daten)
    kopf = {"x0": x0, "z0": -y1, "aufloesung": aufloesung, "breite": breite, "hoehe": hoehe}
    with open(os.path.join(ziel, "rasenmaske.json"), "w", encoding="utf-8") as f:
        json.dump(kopf, f)
    return {"rasen_anteil": round(sum(1 for b in daten if b) / len(daten), 3)}


def weltkonfig(ziel):
    cam = bpy.data.objects["Kamera_Laufen"]
    vorne = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    v3 = drei(vorne)
    sonne = bpy.data.objects["Sonne"].matrix_world.to_3x3() @ Vector((0, 0, -1))
    mik = bpy.data.objects["Labor_Mikroskop"]
    mitte_mik = mik.matrix_world @ (sum((Vector(c) for c in mik.bound_box), Vector()) / 8)
    konf = {
        "start": {"position": drei(cam.matrix_world.translation), "yaw": round(math.atan2(-v3[0], -v3[2]), 4)},
        "sonne_richtung": drei(sonne),
        "mikroskop": drei(mitte_mik),
        "whiteboard": "Whiteboard_Flaeche",
        "augenhoehe": 1.65,
    }
    with open(os.path.join(ziel, "welt.json"), "w", encoding="utf-8") as f:
        json.dump(konf, f, indent=1)
    return konf
```

> `exportieren(…, materialien=False)` exportiert ohne Materialien (für die Kollisionsdatei).

- [ ] **Schritt 2: `alles()` als Rahmen anhängen.** Die Teile aus Task 3–5 werden dort registriert.

```python
TEILE = {}


def teil(name):
    def deko(fn):
        TEILE[name] = fn
        return fn
    return deko


@teil("basis")
def _basis(ziel):
    himmel(ziel)
    return {"maske": rasenmaske(ziel), "welt": weltkonfig(ziel)}


def alles(ziel, nur=None):
    os.makedirs(ziel, exist_ok=True)
    vorbereiten()
    erg = {}
    for name, fn in TEILE.items():
        if nur and name not in nur:
            continue
        erg[name] = fn(ziel)
        print("TEIL FERTIG", name, flush=True)
    return erg
```

- [ ] **Schritt 3: CLI-Einstieg `pipeline/blender/web_export.py`**

```python
"""blender -b labor.blend -P pipeline/blender/web_export.py -- <zielordner> [teil1,teil2]"""
import json
import os
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
sys.path.insert(0, P)
import gartenlib  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
ziel = argv[0]
nur = argv[1].split(",") if len(argv) > 1 and argv[1] else None
erg = gartenlib.lade("webexport").alles(ziel, nur)
print("ERGEBNIS", json.dumps(erg, default=str)[:2000])
print("FERTIG webexport")
```

- [ ] **Schritt 4: Teil „basis“ ausführen**

```bash
cd "/d/KI Projekte/Blender MArtists" && mkdir -p web/public/welt && "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b labor.blend -P pipeline/blender/web_export.py -- "D:/KI Projekte/Blender MArtists/web/public/welt" basis 2>&1 | grep -E "FERTIG|ERGEBNIS|Error|Traceback"
ls -la web/public/welt
```

Erwartet:
- `TEIL FERTIG basis` und `FERTIG webexport`
- Dateien `himmel.jpg`, `rasenmaske.bin` (400 × 480 = 192 000 Bytes), `rasenmaske.json`, `welt.json`
- `rasen_anteil` zwischen 0,4 und 0,8

- [ ] **Schritt 5: Commit** `git add scripts pipeline web/public/welt && git commit -m "Webexport: Himmel, Rasenmaske, Weltkonfiguration"`

---

### Task 3: Webexport – Lightmap-Bake der Bauteile

**Dateien:** Ändern: `scripts/gartenlib/webexport.py` (anhängen)

- [ ] **Schritt 1: Bake-Funktionen anhängen**

```python
GRUPPEN = {
    # name: (Collections, Namensanfänge ausschließen, Auflösung)
    "haus": (["02_Architektur"], ("Glas_", "Schneider_", "WEB_"), 4096),
    "labor": (["03_Innenraum"], ("Labor_Sammelglaeser", "Whiteboard_Flaeche", "WEB_"), 2048),
    "hof": (["04_Hardscape"], ("WEB_",), 2048),
    "boden": (["01a_Beete", "05a_Rasen"], ("WEB_",), 2048),
    "hecke": (["01c_Heckenkern"], ("WEB_",), 2048),
}


def _gruppenobjekte(sammlungen, ohne):
    erg = []
    for s in sammlungen:
        for o in bpy.data.collections[s].all_objects:
            if o.type in ("MESH", "CURVE") and not o.name.startswith(ohne):
                if o.hide_render or o.name.endswith("_Laub"):   # Laub teilt die Kern-Daten, kommt als Instanzen
                    continue
                if any(m and m.name == "M_Glas" for m in getattr(o.data, "materials", [])):
                    continue
                erg.append(o)
    return erg


def _lightmap_uv(o):
    me = o.data
    lm = me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = lm                       # Ziel des Bakes; vorhandene UVs bleiben 'active_render'
    auswahl_setzen([o])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def _backen(o, bild, samples):
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.render.bake.margin = 8
    knoten = []
    for m in o.data.materials:
        if m is None or not m.use_nodes:
            continue
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.image = bild
        m.node_tree.nodes.active = n
        knoten.append((m, n))
    auswahl_setzen([o])
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT", "COLOR"}, margin=8, use_clear=True)
    for m, n in knoten:
        m.node_tree.nodes.remove(n)


def _bild_speichern(bild, pfad, faktor=0.5):
    """Linearen Bake halbieren (Spielraum über 1.0; die Web-App multipliziert ×2) und als PNG speichern."""
    px = np.empty(len(bild.pixels), dtype=np.float32)
    bild.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    px[:, :3] = np.clip(px[:, :3] * faktor, 0.0, 1.0)
    px[:, 3] = 1.0
    bild.pixels.foreach_set(px.ravel())
    bild.filepath_raw = pfad
    bild.file_format = "PNG"
    bild.save()


def _webmaterial(name, pfad):
    m = bpy.data.materials.new(f"WEB_Licht_{name}")
    b = m.node_tree.nodes.get("Principled BSDF")
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(pfad)
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    return m


def bake_gruppe(name, ziel, samples=192):
    sammlungen, ohne, aufl = GRUPPEN[name]
    dg = bpy.context.evaluated_depsgraph_get()
    originale = _gruppenobjekte(sammlungen, ohne)
    kopien = [kopie(o, dg) for o in originale]
    for o in originale:                       # Originale verbergen, damit Kopie und Original sich nicht verschatten
        o.hide_render = True
    o = vereinen(f"Licht_{name}", kopien)
    _lightmap_uv(o)
    bild = bpy.data.images.new(f"Licht_{name}", aufl, aufl, alpha=False, float_buffer=True)
    _backen(o, bild, samples)
    pfad = os.path.join(ziel, f"licht_{name}.png")
    _bild_speichern(bild, pfad)
    me = o.data
    for uv in [u for u in me.uv_layers if u.name != "Lightmap"]:
        me.uv_layers.remove(uv)
    me.materials.clear()
    me.materials.append(_webmaterial(name, pfad))
    for p in me.polygons:
        p.material_index = 0
    exportieren([o], os.path.join(ziel, f"{name}.glb"))
    for orig in originale:
        orig.hide_render = False
    return {"dreiecke": sum(len(p.vertices) - 2 for p in me.polygons), "aufloesung": aufl}


def glas_export(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.data.objects if o.type == "MESH" and
            any(m and m.name == "M_Glas" for m in o.data.materials) and not o.name.startswith("WEB_")]
    o = vereinen("Glas", [kopie(x, dg) for x in objs])
    exportieren([o], os.path.join(ziel, "glas.glb"))
    return {"objekte": len(objs)}


def whiteboard_export(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    k = kopie(bpy.data.objects["Whiteboard_Flaeche"], dg)
    k.name = "Whiteboard_Flaeche"
    exportieren([k], os.path.join(ziel, "whiteboard.glb"))
    return {"ok": True}


@teil("bake")
def _bake(ziel):
    erg = {name: bake_gruppe(name, ziel) for name in GRUPPEN}
    erg["glas"] = glas_export(ziel)
    erg["whiteboard"] = whiteboard_export(ziel)
    return erg
```

- [ ] **Schritt 2: Probe mit nur einer Gruppe.** Zuerst „hecke“ allein über einen kurzen Teil testen. Dafür vorübergehend in einer Python-Konsole des Hintergrundaufrufs, also als eigenes Skript `pipeline/blender/probe_bake.py`:

```python
import os
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
sys.path.insert(0, P)
import gartenlib  # noqa: E402

w = gartenlib.lade("webexport")
ziel = sys.argv[sys.argv.index("--") + 1]
w.vorbereiten()
print("PROBE", w.bake_gruppe("hecke", ziel, samples=64))
```

```bash
cd "/d/KI Projekte/Blender MArtists" && time "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b labor.blend -P pipeline/blender/probe_bake.py -- "D:/KI Projekte/Blender MArtists/web/public/welt" 2>&1 | grep -E "PROBE|Error|Traceback"
```

Erwartet: `PROBE {'dreiecke': …, 'aufloesung': 2048}`, Dateien `licht_hecke.png` und `hecke.glb`. `licht_hecke.png` mit Read ansehen: grüne Laubstruktur, keine schwarzen Flächen.

Bei schwarzen oder leeren Lightmaps:
- Prüfen, ob die Materialien der Gruppe Knoten haben (`use_nodes`).
- Prüfen, ob die Kopie gerendert wird (`hide_render` der Kopie `False`).

- [ ] **Schritt 3: Alle Gruppen backen** (Hintergrund, dauert mehrere Minuten)

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b labor.blend -P pipeline/blender/web_export.py -- "D:/KI Projekte/Blender MArtists/web/public/welt" bake 2>&1 | grep -E "FERTIG|ERGEBNIS|Error|Traceback|memory"
```

Erwartet:
- `TEIL FERTIG bake`
- Dateien `haus.glb`, `labor.glb`, `hof.glb`, `boden.glb`, `hecke.glb`, `glas.glb`, `whiteboard.glb` und `licht_*.png`

`licht_haus.png` und `licht_labor.png` ansehen: erkennbare Fassaden- und Innenflächen mit weichem Licht und Schatten.

- [ ] **Schritt 4: Commit** `git add scripts pipeline web/public/welt && git commit -m "Webexport: Lightmap-Bake der Bauteile"`

---

### Task 4: Webexport – Pflanzen, Bäume, Wiese

**Dateien:** Ändern: `scripts/gartenlib/webexport.py` (anhängen)

- [ ] **Schritt 1: Pflanzen- und Baumexport anhängen**

```python
# Vereinfachung je Prototyp (Anteil der Dreiecke, die bleiben) und Ausdünnung der Instanzen
VEREINFACHUNG = {"Ziergras": 0.25, "Staude": 0.35, "Kiefernpolster": 0.08, "Rasenstueck_Lauf": 1.0,
                 "Heckenballen_Lauf": 0.2}
AUSDUENNEN = {"Heckenballen_Lauf": 4}           # jede 4. Hecken-Instanz
IGNORIEREN = ("fern_", "shrub_", "pine_sapling")  # Poly-Haven-Sträucher (Alpha-Texturen) im Web weglassen


def _praefix(name):
    for p in VEREINFACHUNG:
        if name.startswith(p):
            return p
    return None


def _rampenfarbe(m):
    for n in m.node_tree.nodes if m and m.use_nodes else []:
        if n.type == "VALTORGB":
            return tuple(n.color_ramp.evaluate(0.5))[:3]
        if n.type == "BSDF_PRINCIPLED" and not n.inputs["Base Color"].is_linked:
            return tuple(n.inputs["Base Color"].default_value)[:3]
    return (0.1, 0.2, 0.05)


def _einfache_materialien(o):
    neu = []
    for m in o.data.materials:
        wm = bpy.data.materials.new(f"WEB_P_{m.name if m else 'leer'}")
        b = wm.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*_rampenfarbe(m), 1.0)
        b.inputs["Roughness"].default_value = 0.8
        neu.append(wm)
    o.data.materials.clear()
    for wm in neu:
        o.data.materials.append(wm)


def _instanzdaten(dg, filter_fn):
    """{prototypname: [pos(3), quat(4), skala(1)] …} in Three.js-Koordinaten."""
    daten = {}
    zaehler = {}
    for inst in dg.object_instances:
        if not inst.is_instance or inst.parent is None:
            continue
        if not filter_fn(inst.parent.original):
            continue
        name = inst.object.original.name
        if name.startswith(IGNORIEREN) or _praefix(name) is None:
            continue
        zaehler[name] = zaehler.get(name, 0) + 1
        if zaehler[name] % AUSDUENNEN.get(_praefix(name), 1):
            continue
        loc, rot, sk = inst.matrix_world.decompose()
        daten.setdefault(name, []).append(drei(loc) + [round(rot.x, 5), round(rot.z, 5), round(-rot.y, 5),
                                                         round(rot.w, 5), round(sk.x, 4)])
    return daten


def _instanzen_schreiben(daten, ziel, basisname):
    index, puffer, offset = {}, bytearray(), 0
    for name, liste in sorted(daten.items()):
        for werte in liste:
            puffer += struct.pack("<8f", *werte)
        index[name] = {"offset": offset, "anzahl": len(liste)}
        offset += len(liste)
    with open(os.path.join(ziel, f"{basisname}.bin"), "wb") as f:
        f.write(puffer)
    with open(os.path.join(ziel, f"{basisname}.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
    return {k: v["anzahl"] for k, v in index.items()}


def _prototypen_exportieren(namen, ziel, dateiname):
    protos = []
    for name in namen:
        orig = bpy.data.objects[name]
        me = orig.data.copy()
        k = bpy.data.objects.new(name, me)            # gleicher Name wie in den Instanzdaten (Original wird umbenannt)
        orig.name = f"{name}_orig"
        k.name = name
        bpy.data.collections[TMP].objects.link(k)
        anteil = VEREINFACHUNG.get(_praefix(name), 1.0)
        if anteil < 1.0:
            dm = k.modifiers.new("Vereinfachen", "DECIMATE")
            dm.ratio = anteil
        _einfache_materialien(k)
        protos.append(k)
    exportieren(protos, os.path.join(ziel, dateiname))
    return len(protos)


@teil("pflanzen")
def _pflanzen(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    daten = _instanzdaten(dg, lambda p: p.name.startswith(("Pflanzung_", "Hecke_")))
    anz = _instanzen_schreiben(daten, ziel, "pflanzen_instanzen")
    _prototypen_exportieren(sorted(daten), ziel, "pflanzen.glb")
    return anz


def _blatttextur(name, form, farbe, pfad, n=128):
    """Blattform als RGBA-PNG (Alpha = Blattumriss), passend zu den UVs der Baum-Blätter (u quer, v längs)."""
    v, u = np.mgrid[0:n, 0:n] / (n - 1)
    cx = 2 * u - 1
    if form == "ahorn":
        cy = 2 * v - 0.9
        r = np.sqrt(cx ** 2 + cy ** 2)
        w = np.arctan2(cx, cy)
        maske = r < 0.35 + 0.6 * np.abs(np.cos(2.5 * w)) ** 3
    else:
        maske = np.abs(cx) < np.sin(np.pi * np.clip(v, 0, 1) ** 0.7) * 0.95
    ader = np.exp(-(cx / 0.05) ** 2) * 0.25
    px = np.zeros((n, n, 4), dtype=np.float32)
    for k in range(3):
        px[:, :, k] = farbe[k] * (0.85 + 0.3 * v) * (1 - ader)
    px[:, :, 3] = maske.astype(np.float32)
    img = bpy.data.images.new(name, n, n, alpha=True)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = pfad
    img.file_format = "PNG"
    img.save()
    return img


def _blattmaterial(name, bild):
    m = bpy.data.materials.new(f"WEB_Blatt_{name}")
    b = m.node_tree.nodes.get("Principled BSDF")
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bild
    m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    m.node_tree.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m


@teil("baeume")
def _baeume(ziel):
    from . import baeume as B
    alt = {k: dict(v) for k, v in B.ARTEN.items()}
    try:
        for art in B.ARTEN.values():                      # weniger, dafür größere Blätter
            art["blatt"] = (art["blatt"][0] * 2.2, art["blatt"][1] * 2.2)
        bilder = {"birke": _blatttextur("blatt_birke", "birke", (0.12, 0.2, 0.05), os.path.join(ziel, "blatt_birke.png")),
                  "ahorn": _blatttextur("blatt_ahorn", "ahorn", (0.3, 0.3, 0.07), os.path.join(ziel, "blatt_ahorn.png"))}
        laub = {a: _blattmaterial(a, b) for a, b in bilder.items()}
        rinde = {"birke": bpy.data.materials.new("WEB_Rinde_birke"), "ahorn": bpy.data.materials.new("WEB_Rinde_ahorn")}
        rinde["birke"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.73, 0.68, 1)
        rinde["ahorn"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.2, 0.17, 1)
        objekte = []
        for name, art, ort, hoehe, seed in L.BAEUME:
            B.baum(f"WEBB_{name}", art, ort, hoehe, seed, laub[art], rinde[art], blatt_faktor=0.12, sammlung=TMP)
            objekte += [bpy.data.objects[f"WEBB_{name}"], bpy.data.objects[f"WEBB_{name}_Laub"]]
        protos = []
        for name, art, hoehe, seed in L.KULISSE["vorlagen"]:
            B.baum(f"WEBK_{name}", art, (0.0, 0.0), hoehe, seed, laub[art], rinde[art], blatt_faktor=0.05, sammlung=TMP)
            protos.append(name)
    finally:
        B.ARTEN.clear()
        B.ARTEN.update(alt)
    # Kulisse: Instanzen aus den vorhandenen Kulissenbäumen (Vorlage über die geteilten Mesh-Daten)
    vorlage_von_mesh = {bpy.data.objects[n].data.name: n for n, *_ in L.KULISSE["vorlagen"]}
    daten = {}
    for o in bpy.data.collections["05f_Kulisse"].objects:
        if o.name.endswith("_Laub") or o.data.name not in vorlage_von_mesh:
            continue
        loc, rot, sk = o.matrix_world.decompose()
        daten.setdefault(f"WEBK_{vorlage_von_mesh[o.data.name]}", []).append(
            drei(loc) + [round(rot.x, 5), round(rot.z, 5), round(-rot.y, 5), round(rot.w, 5), round(sk.x, 4)])
    anz = _instanzen_schreiben(daten, ziel, "baeume_instanzen")
    kulisse = []
    for name in protos:                                   # Stamm + Laub zu einem Prototyp vereinen
        stamm, laub_o = bpy.data.objects[f"WEBK_{name}"], bpy.data.objects[f"WEBK_{name}_Laub"]
        laub_o.parent = None
        laub_o.matrix_world = stamm.matrix_world
        stamm.scale = (1, 1, 1)
        laub_o.scale = (1, 1, 1)
        kulisse.append(vereinen(f"WEBK_{name}", [stamm, laub_o]))
    exportieren(objekte + kulisse, os.path.join(ziel, "baeume.glb"))
    return {"gartenbaeume": len(L.BAEUME), "kulisse_instanzen": anz}


@teil("wiese")
def _wiese(ziel):
    dg = bpy.context.evaluated_depsgraph_get()
    k = kopie(bpy.data.objects["Wiese"], dg)
    k.data.materials.clear()
    m = bpy.data.materials.new("WEB_Wiese")
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.16, 0.04, 1)
    k.data.materials.append(m)
    exportieren([k], os.path.join(ziel, "wiese.glb"))
    return {"ok": True}
```

> Zu den Kulissenbäumen: Deren Skalierung steckt in der Objekt-Transformation (Skalierung der Vorlage × Zufall). Die Instanzdaten übernehmen sie als einheitlichen Faktor `sk.x`. Die Web-Prototypen sind in Originalgröße (Skalierung 1), deshalb ergibt Prototyp × Instanzskalierung die richtige Höhe.

- [ ] **Schritt 2: Ausführen**

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b labor.blend -P pipeline/blender/web_export.py -- "D:/KI Projekte/Blender MArtists/web/public/welt" pflanzen,baeume,wiese 2>&1 | grep -E "FERTIG|ERGEBNIS|Error|Traceback"
```

Erwartet:
- `pflanzen.glb`, `pflanzen_instanzen.{bin,json}`
- `baeume.glb`, `baeume_instanzen.{bin,json}`, `blatt_birke.png`, `blatt_ahorn.png`
- `wiese.glb`
- In `pflanzen_instanzen.json` stehen Schlüssel wie `Ziergras_0`, `Staude_1`, `Kiefernpolster_2`, `Heckenballen_Lauf_0`, `Rasenstueck_Lauf_3`.

- [ ] **Schritt 3: Commit** `git add scripts web/public/welt && git commit -m "Webexport: Pflanzen, Bäume, Wiese"`

---

### Task 5: Webexport – Kollision

**Dateien:** Ändern: `scripts/gartenlib/webexport.py` (anhängen)

- [ ] **Schritt 1: Kollisionsexport anhängen**

```python
WAND_SAMMLUNGEN_NAMEN = ("Haus_EG", "Haus_OG", "Fluegel", "Vordach_Stuetzen", "Carport_Stuetzen", "Feuerschale",
                         "Feuerschale_Fuss")
BODEN_NAMEN = ("Rasen", "Wiese", "Hof_Platten", "Weg_Fluegel", "Carport_Boden", "Terrasse", "Labor_Boden")


def _box_aus_bbox(bm, o):
    ecken = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(e.x for e in ecken), min(e.y for e in ecken), min(e.z for e in ecken)))
    mx = Vector((max(e.x for e in ecken), max(e.y for e in ecken), max(e.z for e in ecken)))
    from .util import bm_box
    bm_box(bm, mx - mn, (mn + mx) / 2)


@teil("kollision")
def _kollision(ziel):
    from .util import mesh_aus_bmesh
    from .fassade import _rohr
    dg = bpy.context.evaluated_depsgraph_get()
    waende = [kopie(bpy.data.objects[n], dg) for n in WAND_SAMMLUNGEN_NAMEN if n in bpy.data.objects]
    waende += [kopie(o, dg) for o in bpy.data.objects
               if o.name.startswith("Tuerblatt_") or (o.name.startswith("Hecke_") and o.name.endswith("_Kern"))]
    bm = bmesh.new()                                    # Möbel, Sessel, Poller als Quader; Stämme als Zylinder
    for o in bpy.data.collections["03_Innenraum"].all_objects:
        if o.type == "MESH" and o.name.startswith("Labor_") and not o.name.startswith(("Labor_Boden", "Labor_Lichtpaneele")):
            _box_aus_bbox(bm, o)
    for o in bpy.data.collections["04_Hardscape"].all_objects:
        if o.type in ("MESH", "CURVE") and o.name.startswith(("Sessel_", "Poller_")):
            _box_aus_bbox(bm, o)
    for name, _a, ort, _h, _s in L.BAEUME:
        _rohr(bm, Vector((ort[0], ort[1], 0)), Vector((ort[0], ort[1], 3.0)), 0.28, 10)
    hilfen = mesh_aus_bmesh("WEB_Kollision_Hilfen", bm, TMP)
    waende.append(hilfen)
    w = vereinen("Waende", waende)
    boden = vereinen("Boden", [kopie(bpy.data.objects[n], dg) for n in BODEN_NAMEN if n in bpy.data.objects] +
                     [kopie(o, dg) for o in bpy.data.objects if o.name.startswith("Trittplatte_")])
    for o in (w, boden):
        o.data.materials.clear()
    exportieren([w, boden], os.path.join(ziel, "kollision.glb"), materialien=False)
    return {"waende_dreiecke": sum(len(p.vertices) - 2 for p in w.data.polygons),
            "boden_dreiecke": sum(len(p.vertices) - 2 for p in boden.data.polygons)}
```

- [ ] **Schritt 2: Ausführen**

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b labor.blend -P pipeline/blender/web_export.py -- "D:/KI Projekte/Blender MArtists/web/public/welt" kollision 2>&1 | grep -E "FERTIG|ERGEBNIS|Error|Traceback"
```

Erwartet: `kollision.glb` mit den Knoten `Waende` und `Boden`, Dreiecke im fünf- bis sechsstelligen Bereich.

- [ ] **Schritt 3: Commit** `git add scripts web/public/welt && git commit -m "Webexport: Kollisionsgeometrie"`

---

### Task 6: Web-App-Gerüst, Optimierung und Budgetprüfung

**Dateien:** Neu: `web/package.json`, `web/vite.config.js`, `web/tools/optimieren.mjs`

- [ ] **Schritt 1: `web/package.json`**

```json
{
  "name": "garten-labor",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host",
    "build": "vite build",
    "test": "vitest run",
    "optimieren": "node tools/optimieren.mjs"
  },
  "dependencies": {
    "three": "^0.180.0",
    "three-mesh-bvh": "^0.9.0"
  },
  "devDependencies": {
    "@gltf-transform/core": "^4.2.0",
    "@gltf-transform/extensions": "^4.2.0",
    "@gltf-transform/functions": "^4.2.0",
    "meshoptimizer": "^0.25.0",
    "sharp": "^0.34.0",
    "vite": "^7.0.0",
    "vitest": "^3.2.0"
  }
}
```

- [ ] **Schritt 2: `web/vite.config.js`**

```js
import { defineConfig } from 'vite';

export default defineConfig({
  build: { outDir: 'dist', assetsInlineLimit: 0, chunkSizeWarningLimit: 1500 },
  test: { environment: 'node', include: ['tests/**/*.test.js'] },
});
```

- [ ] **Schritt 3: Installieren** `cd "/d/KI Projekte/Blender MArtists/web" && npm install`. Erwartet: keine Fehler, `node_modules` vorhanden.

- [ ] **Schritt 4: `web/tools/optimieren.mjs`**

```js
// Optimiert alle GLB in public/welt (Meshopt-Geometrie, WebP-Texturen) und prüft das iPad-Budget.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, meshopt, textureCompress } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';

const ORDNER = path.resolve('public/welt');
const BUDGET = { megabyte: 80, dreiecke: 1_500_000 };
const GRAS_DREIECKE = 120_000; // dynamisches Gras in der Web-App (Task 9)
const MAX_TEXTUR = { haus: 4096 };

await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});

function dreieckeJeKnoten(doc) {
  const erg = {};
  for (const knoten of doc.getRoot().listNodes()) {
    const mesh = knoten.getMesh();
    if (!mesh) continue;
    let n = 0;
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      n += (idx ? idx.getCount() : prim.getAttribute('POSITION').getCount()) / 3;
    }
    erg[knoten.getName()] = (erg[knoten.getName()] || 0) + n;
  }
  return erg;
}

function instanzen(datei) {
  const p = path.join(ORDNER, datei);
  return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : {};
}

const inst = { ...instanzen('pflanzen_instanzen.json'), ...instanzen('baeume_instanzen.json') };
let summeDreiecke = GRAS_DREIECKE;
const bericht = [];
for (const datei of fs.readdirSync(ORDNER).filter((d) => d.endsWith('.glb'))) {
  const voll = path.join(ORDNER, datei);
  const doc = await io.read(voll);
  const basis = datei.replace('.glb', '');
  const groesse = MAX_TEXTUR[basis] || 2048;
  await doc.transform(
    dedup(), weld(), prune(),
    textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 85, resize: [groesse, groesse] }),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  await io.write(voll, doc);
  let tris = 0;
  if (datei !== 'kollision.glb') {
    for (const [name, n] of Object.entries(dreieckeJeKnoten(doc))) {
      tris += n * (inst[name] ? inst[name].anzahl : 1);
    }
  }
  summeDreiecke += tris;
  bericht.push({ datei, MB: +(fs.statSync(voll).size / 1e6).toFixed(2), dreiecke: Math.round(tris) });
}
for (const png of fs.readdirSync(ORDNER).filter((d) => d.startsWith('licht_') && d.endsWith('.png'))) {
  fs.rmSync(path.join(ORDNER, png)); // steckt jetzt als WebP in der GLB
}
const mb = fs.readdirSync(ORDNER).reduce((s, d) => s + fs.statSync(path.join(ORDNER, d)).size, 0) / 1e6;
console.table(bericht);
console.log(`GESAMT ${mb.toFixed(1)} MB, ${Math.round(summeDreiecke).toLocaleString('de-DE')} Dreiecke`);
if (mb > BUDGET.megabyte || summeDreiecke > BUDGET.dreiecke) {
  console.error('BUDGET ÜBERSCHRITTEN');
  process.exit(1);
}
console.log('BUDGET OK');
```

- [ ] **Schritt 5: Optimieren und Budget prüfen** `cd "/d/KI Projekte/Blender MArtists/web" && npm run optimieren`.
- Erwartet: eine Tabelle und am Ende `BUDGET OK`.
- **Bei Überschreitung** in `webexport.py` nachsteuern und die betroffenen Teile neu exportieren (Task 3/4, Schritt 2), dann erneut optimieren:

| Ursache | Stellschraube |
|---|---|
| zu viele Dreiecke in Pflanzen | `VEREINFACHUNG` senken, `AUSDUENNEN` erhöhen |
| Bäume zu schwer | `blatt_faktor` für die Bäume senken |
| zu viele MB | Auflösung der Gruppe `haus` auf 2048 |

- [ ] **Schritt 6: Commit** `git add web/package.json web/package-lock.json web/vite.config.js web/tools web/public/welt && git commit -m "Web-App-Gerüst, Optimierung und Budgetprüfung"`

---

### Task 7: Reine Logik mit Tests (Joystick, Bewegung, Rasenmaske)

**Dateien:** Neu: `web/src/logik/joystick.js`, `web/src/logik/bewegung.js`, `web/src/logik/rasenmaske.js`, `web/tests/logik.test.js`

- [ ] **Schritt 1: Tests schreiben** `web/tests/logik.test.js`

```js
import { describe, it, expect } from 'vitest';
import { joystickVektor } from '../src/logik/joystick.js';
import { bewegungsvektor } from '../src/logik/bewegung.js';
import { istRasen, grasPositionen } from '../src/logik/rasenmaske.js';

describe('joystickVektor', () => {
  it('ignoriert kleine Ausschläge (Totzone)', () => {
    expect(joystickVektor(3, 2, 60)).toEqual({ x: 0, y: 0 });
  });
  it('begrenzt auf Länge 1', () => {
    const v = joystickVektor(120, 0, 60);
    expect(v.x).toBeCloseTo(1);
    expect(v.y).toBeCloseTo(0);
  });
  it('liefert Zwischenwerte linear', () => {
    expect(joystickVektor(30, 0, 60).x).toBeCloseTo(0.5);
  });
});

describe('bewegungsvektor', () => {
  it('vorwärts bei Blickrichtung 0 geht nach -z', () => {
    const v = bewegungsvektor(0, 1, 0, 2, 0.5);
    expect(v.x).toBeCloseTo(0);
    expect(v.z).toBeCloseTo(-1);
  });
  it('rechts bei Blickrichtung 0 geht nach +x', () => {
    expect(bewegungsvektor(0, 0, 1, 1, 1).x).toBeCloseTo(1);
  });
  it('Blickrichtung 90° (links) – vorwärts geht nach -x', () => {
    expect(bewegungsvektor(Math.PI / 2, 1, 0, 1, 1).x).toBeCloseTo(-1);
  });
  it('diagonal ist nicht schneller', () => {
    const v = bewegungsvektor(0, 1, 1, 1, 1);
    expect(Math.hypot(v.x, v.z)).toBeCloseTo(1);
  });
});

describe('Rasenmaske', () => {
  const maske = { x0: 0, z0: 0, aufloesung: 1, breite: 4, hoehe: 4,
    daten: Uint8Array.from([255, 255, 0, 0, 255, 255, 0, 0, 255, 255, 255, 255, 0, 0, 0, 0]) };
  it('erkennt Rasen und Nicht-Rasen', () => {
    expect(istRasen(maske, 0.5, 0.5)).toBe(true);
    expect(istRasen(maske, 2.5, 0.5)).toBe(false);
    expect(istRasen(maske, -1, 0)).toBe(false);
  });
  it('setzt Grasbüschel nur auf Rasen und immer gleich', () => {
    const a = grasPositionen(maske, 2, 2, 3, 0.5);
    const b = grasPositionen(maske, 2, 2, 3, 0.5);
    expect(a.length).toBeGreaterThan(0);
    expect(a).toEqual(b);
    for (const p of a) expect(istRasen(maske, p.x, p.z)).toBe(true);
  });
});
```

- [ ] **Schritt 2: Tests laufen lassen** `cd "/d/KI Projekte/Blender MArtists/web" && npm test`. Erwartet: FAIL (Module fehlen).

- [ ] **Schritt 3: Module schreiben**

`web/src/logik/joystick.js`:

```js
/** Auslenkung (Pixel) → Vektor mit Länge ≤ 1; kleine Auslenkungen (Totzone) zählen nicht. */
export function joystickVektor(dx, dy, radius, totzone = 0.12) {
  let x = dx / radius;
  let y = dy / radius;
  const l = Math.hypot(x, y);
  if (l < totzone) return { x: 0, y: 0 };
  if (l > 1) { x /= l; y /= l; }
  return { x, y };
}
```

`web/src/logik/bewegung.js`:

```js
/** Bewegung in der Ebene: yaw = Blickrichtung (0 = -z), vor/seit ∈ [-1, 1]. Diagonal nicht schneller. */
export function bewegungsvektor(yaw, vor, seit, tempo, dt) {
  const fx = -Math.sin(yaw);
  const fz = -Math.cos(yaw);
  const rx = Math.cos(yaw);
  const rz = -Math.sin(yaw);
  let x = fx * vor + rx * seit;
  let z = fz * vor + rz * seit;
  const l = Math.hypot(x, z);
  if (l > 1) { x /= l; z /= l; }
  return { x: x * tempo * dt, z: z * tempo * dt };
}
```

`web/src/logik/rasenmaske.js`:

```js
/** Rasenmaske aus dem Blender-Export: 1 Byte je Zelle, Zeilen in +z. */
export function istRasen(m, x, z) {
  const ix = Math.floor((x - m.x0) / m.aufloesung);
  const iz = Math.floor((z - m.z0) / m.aufloesung);
  if (ix < 0 || iz < 0 || ix >= m.breite || iz >= m.hoehe) return false;
  return m.daten[iz * m.breite + ix] > 127;
}

/** Deterministischer Zufall 0…1 je Rasterzelle. */
export function hash2(ix, iz) {
  let h = (Math.imul(ix, 374761393) + Math.imul(iz, 668265263)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Positionen für Grasbüschel im Umkreis, gleichmäßig mit Zufallsversatz, nur auf Rasen. */
export function grasPositionen(m, cx, cz, radius, raster) {
  const erg = [];
  const i0 = Math.floor((cx - radius) / raster);
  const i1 = Math.ceil((cx + radius) / raster);
  const k0 = Math.floor((cz - radius) / raster);
  const k1 = Math.ceil((cz + radius) / raster);
  for (let iz = k0; iz <= k1; iz++) {
    for (let ix = i0; ix <= i1; ix++) {
      const x = (ix + hash2(ix, iz)) * raster;
      const z = (iz + hash2(iz, ix)) * raster;
      if (Math.hypot(x - cx, z - cz) > radius || !istRasen(m, x, z)) continue;
      erg.push({ x, z, r: hash2(ix + 7, iz) * Math.PI * 2, s: 0.8 + 0.4 * hash2(ix, iz + 11) });
    }
  }
  return erg;
}
```

- [ ] **Schritt 4: Tests laufen lassen** `npm test`. Erwartet: alle PASS.

- [ ] **Schritt 5: Commit** `git add web/src/logik web/tests && git commit -m "Web-App: Logik für Joystick, Bewegung, Rasenmaske"`

---

### Task 8: Web-App – Welt laden und darstellen

**Dateien:** Neu: `web/index.html`, `web/style.css`, `web/src/welt.js`, `web/src/leistung.js`, `web/src/main.js` (Teil 1)

- [ ] **Schritt 1: `web/index.html`**

```html
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <title>Garten-Labor</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <canvas id="welt"></canvas>
  <div id="lade"><div class="titel">Garten-Labor</div><div class="balken"><div id="lade-fuellung"></div></div><div id="lade-text">Lade Labor …</div></div>
  <div id="start" hidden><button id="start-knopf">Los geht's – Welt betreten</button><p class="hinweis" id="start-hinweis"></p></div>
  <div id="fadenkreuz" hidden></div>
  <div id="joystick" hidden><div id="joystick-knauf"></div></div>
  <div id="fps" hidden></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Schritt 2: `web/style.css`**

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; height: 100%; overflow: hidden; background: #cfd6d8; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; touch-action: none; -webkit-user-select: none; user-select: none; }
#welt { display: block; width: 100vw; height: 100vh; }
#lade { position: fixed; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; background: #23332a; color: #eef3ea; }
#lade .titel { font-size: 34px; font-weight: 700; letter-spacing: .5px; }
#lade .balken { width: min(420px, 80vw); height: 12px; border-radius: 6px; background: #3d5244; overflow: hidden; }
#lade-fuellung { height: 100%; width: 0; background: #9bd36a; transition: width .2s; }
#start { position: fixed; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; background: rgba(20, 30, 24, .55); }
#start[hidden], #lade[hidden] { display: none; }
#start-knopf { font-size: 24px; padding: 18px 34px; border: 0; border-radius: 14px; background: #9bd36a; color: #15230f; font-weight: 700; }
.hinweis { color: #fff; font-size: 17px; max-width: 560px; text-align: center; line-height: 1.4; }
#fadenkreuz { position: fixed; left: 50%; top: 50%; width: 10px; height: 10px; margin: -5px 0 0 -5px; border: 2px solid rgba(255,255,255,.85); border-radius: 50%; pointer-events: none; }
#joystick { position: fixed; left: 40px; bottom: 40px; width: 140px; height: 140px; border-radius: 50%; background: rgba(255,255,255,.18); border: 2px solid rgba(255,255,255,.4); pointer-events: none; }
#joystick-knauf { position: absolute; left: 45px; top: 45px; width: 50px; height: 50px; border-radius: 50%; background: rgba(255,255,255,.75); }
#fps { position: fixed; right: 10px; top: 10px; padding: 4px 8px; border-radius: 6px; background: rgba(0,0,0,.55); color: #9bd36a; font: 13px ui-monospace, monospace; }
```

- [ ] **Schritt 3: `web/src/leistung.js`**

```js
/** Bildratenanzeige (Testmodus: URL-Parameter ?test oder Taste F). */
export class Leistung {
  constructor(element, renderer) {
    this.el = element;
    this.renderer = renderer;
    this.zeiten = [];
    this.sichtbar = new URLSearchParams(location.search).has('test');
    this.el.hidden = !this.sichtbar;
    addEventListener('keydown', (e) => { if (e.code === 'KeyF') { this.sichtbar = !this.sichtbar; this.el.hidden = !this.sichtbar; } });
  }
  tick(dt) {
    this.zeiten.push(dt);
    if (this.zeiten.length < 30) return;
    const mittel = this.zeiten.reduce((a, b) => a + b, 0) / this.zeiten.length;
    this.zeiten.length = 0;
    if (!this.sichtbar) return;
    const info = this.renderer.info;
    this.el.textContent = `${(1 / mittel).toFixed(0)} fps · ${(info.render.triangles / 1000).toFixed(0)}k Dreiecke · ${info.render.calls} Aufrufe`;
  }
}
```

- [ ] **Schritt 4: `web/src/welt.js`**

```js
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

const W = '/welt/';

function laderMit(manager) {
  const l = new GLTFLoader(manager);
  l.setMeshoptDecoder(MeshoptDecoder);
  return l;
}

/** Gebackene Bauteile: unbeleuchtet, Lightmap ×2 (wurde beim Export halbiert). */
function gebacken(wurzel) {
  wurzel.traverse((o) => {
    if (!o.isMesh) return;
    const alt = o.material;
    o.material = new THREE.MeshBasicMaterial({ map: alt.map, color: new THREE.Color(2, 2, 2) });
    alt.dispose();
  });
}

function pflanzenMaterial(alt) {
  return new THREE.MeshLambertMaterial({
    color: alt.color, map: alt.map || null, alphaTest: alt.map ? 0.5 : 0, side: THREE.DoubleSide,
  });
}

async function instanzen(szene, gltf, name) {
  const [index, puffer] = await Promise.all([
    fetch(`${W}${name}.json`).then((r) => r.json()),
    fetch(`${W}${name}.bin`).then((r) => r.arrayBuffer()),
  ]);
  const f = new Float32Array(puffer);
  const m = new THREE.Matrix4();
  const p = new THREE.Vector3();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  const farbe = new THREE.Color();
  for (const [knotenName, { offset, anzahl }] of Object.entries(index)) {
    const knoten = gltf.scene.getObjectByName(knotenName);
    if (!knoten) continue;
    const meshes = [];
    knoten.traverse((o) => { if (o.isMesh) meshes.push(o); });
    for (const mesh of meshes) {
      const im = new THREE.InstancedMesh(mesh.geometry, pflanzenMaterial(mesh.material), anzahl);
      for (let i = 0; i < anzahl; i++) {
        const k = (offset + i) * 8;
        p.set(f[k], f[k + 1], f[k + 2]);
        q.set(f[k + 3], f[k + 4], f[k + 5], f[k + 6]);
        s.setScalar(f[k + 7]);
        m.compose(p, q, s);
        im.setMatrixAt(i, m);
        im.setColorAt(i, farbe.setScalar(0.85 + 0.3 * ((i * 0.618) % 1)));
      }
      im.instanceMatrix.needsUpdate = true;
      szene.add(im);
    }
  }
}

/** Lädt die Welt in Etappen (Haus zuerst). fortschritt(anteil 0…1, text). */
export async function ladeWelt(szene, renderer, fortschritt) {
  const manager = new THREE.LoadingManager();
  manager.onProgress = (_u, geladen, gesamt) => fortschritt(geladen / gesamt, 'Lade Welt …');
  const lader = laderMit(manager);
  const glb = (n) => lader.loadAsync(`${W}${n}.glb`);
  const konfig = await fetch(`${W}welt.json`).then((r) => r.json());

  const himmel = await new THREE.TextureLoader(manager).loadAsync(`${W}himmel.jpg`);
  himmel.mapping = THREE.EquirectangularReflectionMapping;
  himmel.colorSpace = THREE.SRGBColorSpace;
  szene.background = himmel;
  const pmrem = new THREE.PMREMGenerator(renderer);
  szene.environment = pmrem.fromEquirectangular(himmel).texture;
  szene.fog = new THREE.Fog(0xcfd6d8, 45, 160);

  szene.add(new THREE.HemisphereLight(0xe2ebf2, 0x45552f, 1.6));
  const sonne = new THREE.DirectionalLight(0xfff1df, 1.1);
  sonne.position.set(...konfig.sonne_richtung.map((v) => -v * 50));
  szene.add(sonne);

  // 1. Haus und Labor (Startpunkt) – zuerst sichtbar
  for (const n of ['haus', 'labor']) { const g = await glb(n); gebacken(g.scene); szene.add(g.scene); }
  const glas = await glb('glas');
  glas.scene.traverse((o) => {
    if (o.isMesh) o.material = new THREE.MeshStandardMaterial({ color: 0xe6f2ee, transparent: true, opacity: 0.2, roughness: 0.04, metalness: 0, depthWrite: false });
  });
  szene.add(glas.scene);
  const wb = await glb('whiteboard');
  szene.add(wb.scene);
  const whiteboard = wb.scene.getObjectByName(konfig.whiteboard);
  if (whiteboard) whiteboard.material = new THREE.MeshBasicMaterial({ color: 0xf4f4f2 });
  const kollision = await glb('kollision');

  // 2. Garten
  for (const n of ['boden', 'hof', 'hecke']) { const g = await glb(n); gebacken(g.scene); szene.add(g.scene); }
  const wiese = await glb('wiese');
  wiese.scene.traverse((o) => { if (o.isMesh) o.material = new THREE.MeshLambertMaterial({ color: 0x3f5a22 }); });
  szene.add(wiese.scene);
  const pflanzen = await glb('pflanzen');
  await instanzen(szene, pflanzen, 'pflanzen_instanzen');
  const baeume = await glb('baeume');
  baeume.scene.traverse((o) => { if (o.isMesh) o.material = pflanzenMaterial(o.material); });
  for (const kind of [...baeume.scene.children]) {
    if (kind.name.startsWith('WEBB_')) szene.add(kind); // Gartenbäume einzeln, Kulisse instanziert
  }
  await instanzen(szene, baeume, 'baeume_instanzen');

  const [maskeKopf, maskeDaten] = await Promise.all([
    fetch(`${W}rasenmaske.json`).then((r) => r.json()),
    fetch(`${W}rasenmaske.bin`).then((r) => r.arrayBuffer()),
  ]);
  return {
    konfig, whiteboard,
    kollisionWaende: kollision.scene.getObjectByName('Waende'),
    kollisionBoden: kollision.scene.getObjectByName('Boden'),
    rasenmaske: { ...maskeKopf, daten: new Uint8Array(maskeDaten) },
  };
}
```

- [ ] **Schritt 5: `web/src/main.js` (Teil 1: nur ansehen, noch ohne Steuerung)**

```js
import * as THREE from 'three';
import { ladeWelt } from './welt.js';
import { Leistung } from './leistung.js';

const canvas = document.getElementById('welt');
const ipad = /iPad|Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: !ipad, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, ipad ? 1.0 : 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = 1.0;

const szene = new THREE.Scene();
const kamera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.05, 400);
addEventListener('resize', () => {
  kamera.aspect = innerWidth / innerHeight;
  kamera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

const fuellung = document.getElementById('lade-fuellung');
const welt = await ladeWelt(szene, renderer, (a, t) => {
  fuellung.style.width = `${Math.round(a * 100)}%`;
  document.getElementById('lade-text').textContent = t;
});
document.getElementById('lade').hidden = true;

const start = welt.konfig.start;
kamera.position.set(...start.position);
kamera.rotation.set(0, start.yaw, 0, 'YXZ');

const leistung = new Leistung(document.getElementById('fps'), renderer);
const uhr = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(uhr.getDelta(), 0.05);
  renderer.render(szene, kamera);
  leistung.tick(dt);
});
```

- [ ] **Schritt 6: Im eingebauten Browser prüfen.**
1. `.claude/launch.json` anlegen bzw. ergänzen: Eintrag `{"name": "web", "runtimeExecutable": "npm", "runtimeArgs": ["run", "dev", "--prefix", "web"], "port": 5173}`.
2. `mcp__Claude_Browser__preview_start` mit `name: "web"` aufrufen, dann `/?test` öffnen.
3. Screenshot. Erwartet: Blick vom Startpunkt auf Garten und Haus, Himmel, Hecke, Bäume und Lightmap-Licht.
4. Konsole ohne Fehler (`read_console_messages`, `onlyErrors`).

- [ ] **Schritt 7: Commit** `git add web .claude/launch.json && git commit -m "Web-App: Welt laden und darstellen"`

---

### Task 9: Steuerung, Kollision, Gras

**Dateien:** Neu: `web/src/steuerung.js`, `web/src/kollision.js`, `web/src/gras.js`. Ändern: `web/src/main.js` (ersetzen)

- [ ] **Schritt 1: `web/src/steuerung.js`**

```js
import { joystickVektor } from './logik/joystick.js';

/** PC: WASD + Maus (Pointer Lock), Shift schneller. iPad: Joystick links, Wischen rechts. */
export class Steuerung {
  constructor(canvas, joystickEl, knaufEl, yaw = 0) {
    this.yaw = yaw;
    this.pitch = 0;
    this.tasten = new Set();
    this.joy = { x: 0, y: 0 };
    this.joyFinger = null;
    this.blickFinger = null;
    this.touch = matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 1;
    this.joystickEl = joystickEl;
    this.knaufEl = knaufEl;
    addEventListener('keydown', (e) => this.tasten.add(e.code));
    addEventListener('keyup', (e) => this.tasten.delete(e.code));
    canvas.addEventListener('mousemove', (e) => {
      if (document.pointerLockElement !== canvas) return;
      this.drehen(e.movementX * 0.0022, e.movementY * 0.0022);
    });
    canvas.addEventListener('touchstart', (e) => this.touchStart(e), { passive: false });
    canvas.addEventListener('touchmove', (e) => this.touchBewegung(e), { passive: false });
    canvas.addEventListener('touchend', (e) => this.touchEnde(e));
    canvas.addEventListener('touchcancel', (e) => this.touchEnde(e));
  }

  drehen(dx, dy) {
    this.yaw -= dx;
    this.pitch = Math.max(-1.3, Math.min(1.3, this.pitch - dy));
  }

  touchStart(e) {
    e.preventDefault();
    for (const t of e.changedTouches) {
      if (t.clientX < innerWidth * 0.45 && this.joyFinger === null) {
        this.joyFinger = { id: t.identifier, x0: t.clientX, y0: t.clientY };
        Object.assign(this.joystickEl.style, { left: `${t.clientX - 70}px`, top: `${t.clientY - 70}px`, bottom: 'auto' });
      } else if (this.blickFinger === null) {
        this.blickFinger = { id: t.identifier, x: t.clientX, y: t.clientY };
      }
    }
  }

  touchBewegung(e) {
    e.preventDefault();
    for (const t of e.changedTouches) {
      if (this.joyFinger && t.identifier === this.joyFinger.id) {
        const dx = t.clientX - this.joyFinger.x0;
        const dy = t.clientY - this.joyFinger.y0;
        this.joy = joystickVektor(dx, dy, 60);
        this.knaufEl.style.transform = `translate(${this.joy.x * 45}px, ${this.joy.y * 45}px)`;
      } else if (this.blickFinger && t.identifier === this.blickFinger.id) {
        this.drehen((t.clientX - this.blickFinger.x) * 0.005, (t.clientY - this.blickFinger.y) * 0.005);
        this.blickFinger.x = t.clientX;
        this.blickFinger.y = t.clientY;
      }
    }
  }

  touchEnde(e) {
    for (const t of e.changedTouches) {
      if (this.joyFinger && t.identifier === this.joyFinger.id) {
        this.joyFinger = null;
        this.joy = { x: 0, y: 0 };
        this.knaufEl.style.transform = '';
      }
      if (this.blickFinger && t.identifier === this.blickFinger.id) this.blickFinger = null;
    }
  }

  /** {vor, seit, schnell} mit Werten in [-1, 1]. */
  eingabe() {
    const k = this.tasten;
    let vor = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    let seit = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    if (this.joy.x || this.joy.y) { vor = -this.joy.y; seit = this.joy.x; }
    return { vor, seit, schnell: k.has('ShiftLeft') || k.has('ShiftRight') };
  }
}
```

- [ ] **Schritt 2: `web/src/kollision.js`**

```js
import * as THREE from 'three';
import { MeshBVH, acceleratedRaycast } from 'three-mesh-bvh';

THREE.Mesh.prototype.raycast = acceleratedRaycast;

/** Kapsel gegen Wände (seitlich ausweichen), Boden per Strahl nach unten (Stufen bis 0,4 m). */
export class Kollision {
  constructor(waende, boden, radius = 0.3) {
    waende.updateMatrixWorld(true);
    boden.updateMatrixWorld(true);
    this.waendeGeo = waende.geometry.clone().applyMatrix4(waende.matrixWorld);
    this.bvh = new MeshBVH(this.waendeGeo);
    this.boden = boden;
    this.boden.geometry.boundsTree = new MeshBVH(boden.geometry);
    this.radius = radius;
    this.strahl = new THREE.Raycaster();
    this.strahl.firstHitOnly = true;
    this.unten = new THREE.Vector3(0, -1, 0);
  }

  /** Neue Fußposition nach horizontaler Bewegung um (dx, dz). */
  schiebe(fuss, dx, dz) {
    const r = this.radius;
    const seg = new THREE.Line3(new THREE.Vector3(fuss.x + dx, fuss.y + 0.45, fuss.z + dz),
      new THREE.Vector3(fuss.x + dx, fuss.y + 1.6, fuss.z + dz));
    const box = new THREE.Box3();
    const dreieckPunkt = new THREE.Vector3();
    const kapselPunkt = new THREE.Vector3();
    for (let durchgang = 0; durchgang < 3; durchgang++) {
      box.makeEmpty().expandByPoint(seg.start).expandByPoint(seg.end);
      box.min.addScalar(-r);
      box.max.addScalar(r);
      this.bvh.shapecast({
        intersectsBounds: (b) => b.intersectsBox(box),
        intersectsTriangle: (tri) => {
          const abstand = tri.closestPointToSegment(seg, dreieckPunkt, kapselPunkt);
          if (abstand >= r) return false;
          const richtung = kapselPunkt.sub(dreieckPunkt);
          richtung.y = 0;
          if (richtung.lengthSq() < 1e-8) return false;
          richtung.normalize().multiplyScalar(r - abstand);
          seg.start.add(richtung);
          seg.end.add(richtung);
          return false;
        },
      });
    }
    return new THREE.Vector3(seg.start.x, fuss.y, seg.start.z);
  }

  /** Bodenhöhe unter (x, z), höchstens 'stufe' über y; null = kein Boden. */
  bodenHoehe(x, y, z, stufe = 0.4) {
    this.strahl.set(new THREE.Vector3(x, y + stufe, z), this.unten);
    this.strahl.far = stufe + 30;
    const t = this.strahl.intersectObject(this.boden, false);
    return t.length ? t[0].point.y : null;
  }
}
```

- [ ] **Schritt 3: `web/src/gras.js`**

```js
import * as THREE from 'three';
import { grasPositionen } from './logik/rasenmaske.js';

function bueschelGeometrie() {
  const pos = [];
  const farbe = [];
  const unten = [0.05, 0.12, 0.03];
  const oben = [0.17, 0.29, 0.07];
  for (let i = 0; i < 8; i++) {
    const w = (i / 8) * Math.PI * 2 + i * 0.7;
    const r = 0.02 + (i % 3) * 0.012;
    const bx = Math.cos(w) * r;
    const bz = Math.sin(w) * r;
    const h = 0.07 + ((i * 37) % 10) * 0.006;
    const neig = 0.03 + (i % 4) * 0.012;
    const qx = -Math.sin(w) * 0.006;
    const qz = Math.cos(w) * 0.006;
    const sx = bx + Math.cos(w) * neig;
    const sz = bz + Math.sin(w) * neig;
    pos.push(bx - qx, 0, bz - qz, bx + qx, 0, bz + qz, sx, h, sz);
    farbe.push(...unten, ...unten, ...oben);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(farbe, 3));
  g.computeVertexNormals();
  return g;
}

/** Grasbüschel im Umkreis der Spielfigur; werden beim Gehen neu verteilt. */
export class Gras {
  constructor(szene, maske, anzahl = 9000, radius = 13, raster = 0.28) {
    this.maske = maske;
    this.radius = radius;
    this.raster = raster;
    this.mesh = new THREE.InstancedMesh(bueschelGeometrie(),
      new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }), anzahl);
    this.mesh.frustumCulled = false;
    this.mesh.count = 0;
    szene.add(this.mesh);
    this.zentrum = null;
    this.m = new THREE.Matrix4();
    this.q = new THREE.Quaternion();
    this.achse = new THREE.Vector3(0, 1, 0);
  }

  aktualisiere(fuss) {
    if (this.zentrum && Math.hypot(fuss.x - this.zentrum.x, fuss.z - this.zentrum.z) < 1.5) return;
    this.zentrum = { x: fuss.x, z: fuss.z };
    const liste = grasPositionen(this.maske, fuss.x, fuss.z, this.radius, this.raster);
    const n = Math.min(liste.length, this.mesh.instanceMatrix.count);
    for (let i = 0; i < n; i++) {
      const p = liste[i];
      this.q.setFromAxisAngle(this.achse, p.r);
      this.m.compose(new THREE.Vector3(p.x, 0.0, p.z), this.q, new THREE.Vector3(p.s, p.s, p.s));
      this.mesh.setMatrixAt(i, this.m);
    }
    this.mesh.count = n;
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}
```

- [ ] **Schritt 4: `web/src/main.js` vollständig ersetzen**

```js
import * as THREE from 'three';
import { ladeWelt } from './welt.js';
import { Leistung } from './leistung.js';
import { Steuerung } from './steuerung.js';
import { Kollision } from './kollision.js';
import { Gras } from './gras.js';
import { bewegungsvektor } from './logik/bewegung.js';

const canvas = document.getElementById('welt');
const ipad = /iPad|Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: !ipad, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, ipad ? 1.0 : 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;

const szene = new THREE.Scene();
const kamera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.05, 400);
addEventListener('resize', () => {
  kamera.aspect = innerWidth / innerHeight;
  kamera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

if ('serviceWorker' in navigator && import.meta.env.PROD) navigator.serviceWorker.register('/sw.js');

const fuellung = document.getElementById('lade-fuellung');
const welt = await ladeWelt(szene, renderer, (a, t) => {
  fuellung.style.width = `${Math.round(a * 100)}%`;
  document.getElementById('lade-text').textContent = t;
});
document.getElementById('lade').hidden = true;

const { konfig } = welt;
const augen = konfig.augenhoehe;
const kollision = new Kollision(welt.kollisionWaende, welt.kollisionBoden);
const gras = new Gras(szene, welt.rasenmaske);
const fuss = new THREE.Vector3(konfig.start.position[0], 0, konfig.start.position[2]);
fuss.y = kollision.bodenHoehe(fuss.x, 5, fuss.z, 0) ?? 0;
let fallTempo = 0;

const steuerung = new Steuerung(canvas, document.getElementById('joystick'), document.getElementById('joystick-knauf'), konfig.start.yaw);
const startEl = document.getElementById('start');
document.getElementById('start-hinweis').textContent = steuerung.touch
  ? 'Links ziehen = gehen · rechts wischen = umschauen'
  : 'W A S D = gehen · Maus = umschauen · Shift = schneller · Esc = Pause';
startEl.hidden = false;
document.getElementById('start-knopf').addEventListener('click', () => {
  startEl.hidden = true;
  if (steuerung.touch) document.getElementById('joystick').hidden = false;
  else { canvas.requestPointerLock(); document.getElementById('fadenkreuz').hidden = false; }
});
document.addEventListener('pointerlockchange', () => {
  if (!steuerung.touch && document.pointerLockElement !== canvas) startEl.hidden = false;
});

const leistung = new Leistung(document.getElementById('fps'), renderer);
const uhr = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(uhr.getDelta(), 0.05);
  const e = steuerung.eingabe();
  const v = bewegungsvektor(steuerung.yaw, e.vor, e.seit, e.schnell ? 4.0 : 1.8, dt);
  if (v.x || v.z) {
    const neu = kollision.schiebe(fuss, v.x, v.z);
    fuss.x = neu.x;
    fuss.z = neu.z;
  }
  const boden = kollision.bodenHoehe(fuss.x, fuss.y, fuss.z);
  if (boden !== null && boden >= fuss.y - 0.02) { fuss.y = boden; fallTempo = 0; } else {
    fallTempo = Math.min(fallTempo + 9.81 * dt, 12);
    fuss.y = boden !== null ? Math.max(boden, fuss.y - fallTempo * dt) : fuss.y;
  }
  kamera.position.set(fuss.x, fuss.y + augen, fuss.z);
  kamera.rotation.set(steuerung.pitch, steuerung.yaw, 0, 'YXZ');
  gras.aktualisiere(fuss);
  renderer.render(szene, kamera);
  leistung.tick(dt);
});
```

- [ ] **Schritt 5: Im Browser testen** (Vorschau `web`, `/?test`). Mit `browser_batch`:
1. Start-Knopf anklicken.
2. Taste `w` etwa 3 Sekunden gedrückt halten (mehrfach `key`).
3. Screenshot.

Erwartet:
- Die Kamera bewegt sich vorwärts und durchdringt keine Wände.
- Am Haus führt der Weg nur durch die offene Terrassentür hinein.
- Gras ist im Umkreis sichtbar.
- Die fps-Anzeige läuft.

Zusätzlich im Konsolen-Test prüfen, dass `kollision.schiebe` vor einer Wand stoppt: Startposition vor die Hauswand setzen und `w` halten. Die Position bleibt vor der Wand.

- [ ] **Schritt 6: Tests** `npm test` (Logik-Tests weiterhin PASS) und `npm run build` (erwartet: `dist/` ohne Fehler).

- [ ] **Schritt 7: Commit** `git add web && git commit -m "Web-App: Steuerung PC/iPad, Kollision, Gras"`

---

### Task 10: Service Worker

**Dateien:** Neu: `web/public/sw.js`

- [ ] **Schritt 1: `web/public/sw.js`**

```js
// Hält die Welt-Dateien nach dem ersten Laden auf dem Gerät (Cache zuerst), alles andere Netz zuerst.
const CACHE = 'garten-labor-welt-v1';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((namen) => Promise.all(namen.filter((n) => n !== CACHE).map((n) => caches.delete(n)))));
  self.clients.claim();
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/welt/')) {
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const treffer = await c.match(e.request);
      if (treffer) return treffer;
      const antwort = await fetch(e.request);
      if (antwort.ok) c.put(e.request, antwort.clone());
      return antwort;
    }));
  }
});
```

> Wenn sich die Welt-Dateien ändern, muss `CACHE` hochgezählt werden (v2, v3 …), sonst behalten Geräte die alte Fassung.

- [ ] **Schritt 2: Build prüfen** `npm run build && ls dist/sw.js`. Erwartet: Die Datei ist vorhanden.

- [ ] **Schritt 3: Commit** `git add web/public/sw.js && git commit -m "Service Worker für Offline-Zwischenspeicher"`

---

### Task 11: Server und Docker-Image

**Dateien:** Neu: `server/app.py`, `server/requirements.txt`, `server/tests/test_app.py`, `Dockerfile`, `.dockerignore`

- [ ] **Schritt 1: Test schreiben** `server/tests/test_app.py`

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402


def _app(tmp_path):
    (tmp_path / "welt").mkdir()
    (tmp_path / "index.html").write_text("<html>Garten-Labor</html>", encoding="utf-8")
    (tmp_path / "welt" / "haus.glb").write_bytes(b"glTF")
    (tmp_path / "sw.js").write_text("// sw", encoding="utf-8")
    return create_app(str(tmp_path)).test_client()


def test_gesundheit(tmp_path):
    r = _app(tmp_path).get("/api/gesundheit")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}


def test_startseite_und_spa_fallback(tmp_path):
    c = _app(tmp_path)
    assert b"Garten-Labor" in c.get("/").data
    assert b"Garten-Labor" in c.get("/irgendwas/unbekannt").data


def test_weltdateien_mit_cache(tmp_path):
    r = _app(tmp_path).get("/welt/haus.glb")
    assert r.status_code == 200
    assert r.data == b"glTF"
    assert r.cache_control.max_age == 3600


def test_service_worker_nicht_zwischengespeichert(tmp_path):
    r = _app(tmp_path).get("/sw.js")
    assert r.status_code == 200
    assert r.cache_control.no_cache


def test_kein_pfad_ausbruch(tmp_path):
    r = _app(tmp_path).get("/../app.py")
    assert b"Garten-Labor" in r.data or r.status_code == 404
```

- [ ] **Schritt 2: Lokale Testumgebung anlegen und Test laufen lassen**

```bash
cd "/d/KI Projekte/Blender MArtists/server" && py -m venv .venv && .venv/Scripts/python -m pip install -q flask gunicorn pytest && .venv/Scripts/python -m pytest -q
```

Erwartet: FAIL (`app` fehlt).

- [ ] **Schritt 3: `server/app.py`**

```python
"""Garten-Labor-Server: liefert die Web-App aus. Plan 2 ergänzt Sitzungen, Teams und Speichern."""
import os

from flask import Flask, jsonify, send_from_directory


def create_app(dist=None):
    dist = os.path.abspath(dist or os.environ.get(
        "WEB_DIST", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "dist")))
    app = Flask(__name__, static_folder=None)

    @app.get("/api/gesundheit")
    def gesundheit():
        return jsonify(ok=True)

    @app.get("/", defaults={"pfad": "index.html"})
    @app.get("/<path:pfad>")
    def statisch(pfad):
        voll = os.path.abspath(os.path.join(dist, pfad))
        if not voll.startswith(dist + os.sep) or not os.path.isfile(voll):
            pfad = "index.html"
        antwort = send_from_directory(dist, pfad)
        if pfad.startswith("assets/"):
            antwort.cache_control.max_age = 31536000      # Vite-Dateinamen enthalten einen Hash
            antwort.cache_control.immutable = True
        elif pfad.startswith("welt/"):
            antwort.cache_control.max_age = 3600
        else:
            antwort.cache_control.no_cache = True
        return antwort

    return app


app = create_app()
```

`server/requirements.txt`:

```
flask>=3.1
gunicorn>=23
```

- [ ] **Schritt 4: Tests laufen lassen** `.venv/Scripts/python -m pytest -q`. Erwartet: 5 passed.

- [ ] **Schritt 5: `Dockerfile` (Projektwurzel)**

```dockerfile
FROM node:22-alpine AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --omit=optional
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt
COPY server/ server/
COPY --from=web /app/web/dist web/dist
ENV WEB_DIST=/app/web/dist PORT=8000
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "--threads", "4", "--chdir", "server", "app:app"]
```

`.dockerignore`:

```
assets/
renders/
*.blend
*.blend1
web/node_modules/
web/dist/
server/.venv/
**/__pycache__/
docs/
```

> Hinweis: `npm ci --omit=optional` lässt `sharp` (nur für die Optimierung lokal nötig) im Image weg. Falls `npm ci` wegen `sharp` scheitert, `sharp` und die gltf-transform-Pakete in `optionalDependencies` verschieben.

- [ ] **Schritt 6: Image lokal bauen und testen**

```bash
cd "/d/KI Projekte/Blender MArtists" && docker build -t garten-labor . && docker run -d --rm -p 8000:8000 --name gl garten-labor && sleep 3 && curl -s localhost:8000/api/gesundheit && curl -s -o /dev/null -w "%{http_code} %{size_download}\n" localhost:8000/welt/haus.glb; docker stop gl
```

Erwartet: `{"ok":true}` und `200` mit der Größe von `haus.glb`.

- [ ] **Schritt 7: Commit** `git add server Dockerfile .dockerignore && git commit -m "Server und Docker-Image"`

---

### Task 12: Veröffentlichen (GitHub + Coolify)

- [ ] **Schritt 1: FREIGABE einholen.**
- Stephan fragen: „Darf ich den Branch `garten-labor` (inklusive Skripten, Dokumentation und der Weltdateien, etwa … MB) nach `https://github.com/WIlski54/Lernlabor_Version1` pushen?“
- Hinweis: **Das Repository ist öffentlich**, der Code und die Weltdateien wären für alle sichtbar. Es kommen keine Geheimnisse hinein (die Lehrer-PIN folgt in Plan 2 als Coolify-Variable). Möchte Stephan es privat, stellt er das vorher auf GitHub um und verbindet Coolify mit seinem GitHub-Konto.
- **Ohne Ja geht es nicht weiter.**

- [ ] **Schritt 2: Remote setzen und pushen**

```bash
cd "/d/KI Projekte/Blender MArtists" && git remote add origin https://github.com/WIlski54/Lernlabor_Version1.git && git push -u origin garten-labor && git push origin blender-original
```

- [ ] **Schritt 3: Coolify einrichten.** Stephan macht das in der Coolify-Oberfläche; Claude gibt die Werte vor:
1. **New Resource** → **Public Repository** (bzw. GitHub App bei privat) → URL `https://github.com/WIlski54/Lernlabor_Version1`
2. **Branch:** `garten-labor` · **Build Pack:** Dockerfile · **Port:** `8000`
3. **Domain** eintragen (z. B. `https://labor.<deine-domain>`), dann **Deploy**.
4. Nach dem Deployment die Domain + `/api/gesundheit` öffnen. Erwartet: `{"ok":true}`.

- [ ] **Schritt 4: Im eingebauten Browser die öffentliche URL mit `?test` öffnen.** Laden, Startknopf, Gehen (wie Task 9, Schritt 5) prüfen.

---

### Task 13: Praxistest auf einem Schul-iPad

- [ ] **Schritt 1: Testanleitung an Stephan**
1. Auf einem iPad 9./10. Generation in Safari `https://<domain>/?test` öffnen. Die erste Ladezeit notieren.
2. „Los geht's“ antippen und 2 Minuten im Garten und im Labor herumgehen (links ziehen, rechts wischen).
3. Die fps-Anzeige oben rechts beobachten: Wert im Garten bei Blick auf die Hecke, Wert im Labor.
4. Auf Ruckler, Abstürze (Seite lädt neu) und Darstellungsfehler achten.
5. Seite neu laden: Geht es jetzt deutlich schneller? (Das zeigt, dass der Service Worker greift.)

- [ ] **Schritt 2: Ergebnis auswerten.**

| Ergebnis | Folge |
|---|---|
| ≥ 30 fps, keine Abstürze | Abnahme von Plan 1 erfüllt → Plan 2 schreiben |
| 20–30 fps | `renderer.setPixelRatio` auf 0.85, Gras-Anzahl auf 6000, `AUSDUENNEN` der Hecke auf 6, neu exportieren und optimieren |
| Absturz/Neuladen | Speicher zu knapp: Texturen der Gruppe `haus` auf 2048, `boden`/`hof`/`hecke` auf 1024, neu exportieren |

- [ ] **Schritt 3: Messwerte in `docs/Testprotokoll_iPad.md` festhalten** (Gerät, iPadOS, Ladezeit, fps Garten/Labor, Auffälligkeiten). Danach Commit.

---

## Selbstprüfung des Plans

**Abdeckung der Spec (Teil von Version 1, der in Plan 1 liegt):**

| Spec-Punkt | Umsetzung |
|---|---|
| Labor im EG, Wohnungseinrichtung entfernt, Whiteboard-Fläche, Mikroskop-Platz | Task 1 |
| Garten vereinfacht, Lightmaps, Pflanzen instanziert, Bäume mit Blattkarten, Kulisse | Task 3–4 |
| Kollision mit Wänden, Möbeln, Hecke und Bäumen | Task 5, 9 |
| Steuerung PC/iPad | Task 9 |
| Haus zuerst laden, Ladebalken | Task 8 |
| Service Worker | Task 10 |
| Leistungsziele mit Budgetprüfung | Task 6 |
| fps-Anzeige | Task 8 |
| Praxistest | Task 13 |
| Server-Auslieferung über Coolify | Task 11–12 |
| Original unverändert | Task 0 (Kopie), `_pruefe_datei`/`vorbereiten` verweigern andere Dateien |

Bewusst in Plan 2: Arten und Tiere, Interaktion (Schimmer, Antippen), Sammelbuch, Mikroskop-Ansicht, Whiteboard-Editor, Auftrag, Anmeldung, Lehrerseite, Offline-Synchronisation der Daten.

**Einheitliche Namen:**
- `Whiteboard_Flaeche` (Blender-Objekt, GLB-Knoten, `welt.json`)
- `Labor_Mikroskop` (Blender, `weltkonfig`)
- `Waende`/`Boden` (Kollision)
- `*_instanzen.json/.bin` mit 8 Floats je Instanz (Export und `welt.js`)
- `bewegungsvektor`, `joystickVektor`, `istRasen`, `grasPositionen` (Logik, Tests, Nutzung)

**Bekannte Risiken mit Gegenmaßnahme im Plan:**
- GPU-Speicher beim Bake: Modus 0 und 1K-Modelltexturen sind gesetzt. Bei Out-of-Memory andere Programme schließen.
- Leere Lightmaps: Prüfschritt in Task 3, Schritt 2.
- Budget überschritten: Stellschrauben in Task 6.
- iPad-Leistung: Stellschrauben in Task 13.
- `sharp` im Docker-Build: Hinweis in Task 11.
