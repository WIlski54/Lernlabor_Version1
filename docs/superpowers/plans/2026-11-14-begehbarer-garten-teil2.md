# Begehbarer Garten – Teil 2 (Grundstück, Erdgeschoss innen, Laufen) – Umsetzungsplan

> **Für ausführende Agenten:** BENÖTIGTER SUB-SKILL: superpowers:subagent-driven-development (empfohlen) oder superpowers:executing-plans, um den Plan Aufgabe für Aufgabe abzuarbeiten. Schritte nutzen Checkboxen (`- [ ]`).

**Ziel:** Die Szene aus Teil 1 wird zu einem rundum geschlossenen Grundstück mit eingerichtetem, beleuchtetem Erdgeschoss, durch das Stephan im Eevee-Viewport mit mindestens 25 fps laufen kann.

**Architektur:** Es gelten dieselben Konventionen wie in Teil 1: Python-Module in `scripts/gartenlib/`, Ausführung über den MCP-Aufruf, Prüfungen in `pruefung.py`, Renders über `scripts/render.sh`. Neu sind drei Module: `kulisse.py` (Wiese, Hecken, Baumkulisse), `innenraum.py` (Boden, Küche, Möbel, Licht, Lichtsonden) und `lauf.py` (Walk-Einstellungen, Startansicht, fps-Messung, Modus-Treiber). Die Maße stehen weiter zentral in `layout.py`.

**Tech-Stack:** Blender 5.1.1 (bpy, bmesh, Geometry Nodes, Eevee mit Lichtsonden, Cycles/OptiX), Poly-Haven-API (Möbel und Texturen, CC0).

**Spec:** `docs/superpowers/specs/2026-11-14-begehbarer-garten-design.md` (Schritte 5–7)
**Vorgänger:** `docs/superpowers/plans/2026-11-14-begehbarer-garten-teil1.md` (Konventionen, MCP-Aufruf, Prüfaufruf und Render-Aufruf gelten unverändert)

---

## Konventionen (Kurzfassung aus Teil 1)

**MCP-Aufruf** (in jedem Schritt `<modul>` und `<funktion>` ersetzen):

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

**Render:**
- Aufruf: `bash "D:/KI Projekte/Blender MArtists/scripts/render.sh" <ausgabe.png> <ENGINE> <samples> <prozent> <kamera> <modus>`
- Vorher `gartenlib.lade("util").speichern()` ausführen.

**Downloads und Installationen:** nur nach ausdrücklichem Ja von Stephan im Chat.

---

## Dateistruktur

| Datei | Änderung |
|---|---|
| `scripts/gartenlib/layout.py` | + `HECKEN`, `HECKE_MASS`, `WIESE`, `KULISSE`, `INNEN`, `KAMERA_LAUFEN` |
| `scripts/gartenlib/setup.py` | + Collections `01b_Wiese`, `01c_Heckenkern`, `05g_Hecke`, `Bib_Heckenblatt`; `Maske_Rasen` + `01c_Heckenkern` |
| `scripts/gartenlib/baeume.py` | `baum()` bekommt `blatt_faktor` und `sammlung` |
| `scripts/gartenlib/kulisse.py` | neu: Wiese, Hecken, Baumkulisse |
| `scripts/polyhaven.py` | + Rollen für Möbel/Innentexturen; `plan` zeigt nur fehlende Dateien als Downloadgröße |
| `scripts/gartenlib/materialien.py` | + `M_Parkett`, `M_Arbeitsplatte` |
| `scripts/gartenlib/innenraum.py` | neu: Boden, Decke, Küche, Möbel, Lichter, Lichtsonden, Innenkamera |
| `scripts/gartenlib/lauf.py` | neu: Walk-Einstellungen, Laufkamera, Startansicht, Modus-Treiber, fps-Messung |
| `scripts/gartenlib/pflanzen.py` | Rispenfarbe dezenter |
| `scripts/gartenlib/pruefung.py` | + `kulisse()`, `innenraum()`, `lauf()` |
| `docs/Anleitung_Laufen.md` | neu: Kurzanleitung für Stephan |

---

### Task 16: Feinschliff aus der Qualitätsprobe und neue Prüfungen

**Dateien:** Ändern: `scripts/gartenlib/pflanzen.py`, `scripts/gartenlib/pruefung.py`

- [ ] **Schritt 1: Rispen dezenter.** In `pflanzen.graeser_bibliothek()` die Zeile mit `m_rispe` ersetzen:

```python
    m_rispe = pflanzen_material("M_Grasbluete", [(0.0, (0.36, 0.32, 0.25)), (1.0, (0.52, 0.47, 0.38))],
                                durchscheinend=0.6, rauheit=0.6)
```

- [ ] **Schritt 2: Neue Prüfungen an `pruefung.py` anhängen** (sie schlagen fehl, bis die Aufgaben gebaut sind)

```python
def kulisse():
    from . import layout as L
    f = []
    if "Wiese" not in bpy.data.objects:
        f.append("Wiese fehlt")
    hecken = [o for o in bpy.data.objects if o.name.startswith("Hecke_") and o.name.endswith("_Laub")]
    if len(hecken) < len(L.HECKEN):
        f.append(f"nur {len(hecken)} Hecken mit Laub")
    baeume = [o for o in bpy.data.collections["05f_Kulisse"].objects if o.name.startswith("Kulisse_") and not o.name.endswith("_Laub")]
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
```

- [ ] **Schritt 3: Gräser neu bauen, prüfen.** MCP: `pflanzen.graeser_bibliothek()`, danach `util.speichern()`. Prüfaufruf `bepflanzung()`, erwartet `ok: true`. Prüfaufruf `kulisse()`, erwartet `ok: false` (Wiese fehlt).

- [ ] **Schritt 4: Commit** `git add scripts && git commit -m "Feinschliff Rispen, Prüfungen Teil 2"`

---

### Task 17: Wiese und Hecken

**Dateien:** Ändern: `scripts/gartenlib/layout.py`, `scripts/gartenlib/setup.py`; Neu: `scripts/gartenlib/kulisse.py`

- [ ] **Schritt 1: An `layout.py` anhängen**

```python
# ---------------------------------------------------------------- Teil 2: Kulisse
# Hecken als Mittellinien ((x0, y0), (x1, y1)); Lücke im Süden für den Weg am Seitenflügel
HECKEN = [
    ((-23.5, 25.5), (15.5, 25.5)),
    ((-23.5, -21.5), (-23.5, 25.5)),
    ((-23.5, -21.5), (2.0, -21.5)),
    ((15.5, -21.5), (15.5, 25.5)),
]
HECKE_MASS = {"hoehe": 1.8, "tiefe": 0.8}
WIESE = {"mitte": (-4.0, 2.0), "halbe_breite": 60.0}
KULISSE = {
    "anzahl": 26, "r_min": 34.0, "r_max": 52.0, "mitte": (-4.0, 2.0), "seed": 9, "blatt_faktor": 0.45,
    "vorlagen": [("Kulisse_Birke_A", "birke", 15.0, 11), ("Kulisse_Birke_B", "birke", 13.0, 12),
                 ("Kulisse_Ahorn_A", "ahorn", 12.0, 13), ("Kulisse_Ahorn_B", "ahorn", 14.0, 14)],
}
```

- [ ] **Schritt 2: Collections ergänzen.** In `setup.py` die Liste `SAMMLUNGEN` um diese Einträge erweitern (vor `("06_Licht", None)` bzw. am Listenende für `Bib_Heckenblatt`):

```python
    ("01b_Wiese", "01_Gelaende"), ("01c_Heckenkern", "01_Gelaende"), ("05g_Hecke", "05_Pflanzen"),
    ("Bib_Heckenblatt", "99_Bibliothek"),
```

In `struktur()` die Masken-Zeile ändern zu:

```python
    for maske, kinder in (("Maske_Rasen", ("02_Architektur", "04_Hardscape", "01a_Beete", "01c_Heckenkern")),
                          ("Maske_Beet", ("02_Architektur", "04_Hardscape"))):
```

MCP: `setup.struktur()`, danach Prüfaufruf `struktur()`, erwartet `ok: true`.

- [ ] **Schritt 3: `kulisse.py` mit Wiese und Hecken schreiben**

```python
"""Umgebung: Wiese um das Grundstück, Hecken an der Grenze, Baumkulisse."""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import gn
from . import layout as L
from .pflanzen import pflanzen_material
from .util import leere, material, mesh_aus_bmesh


def wiese():
    """Ring aus vier Rechtecken zwischen Grundstück und Außenrand, mit lockerem Gras."""
    leere("01b_Wiese")
    x0, y0, x1, y1 = L.GRUNDSTUECK
    mx, my = L.WIESE["mitte"]
    h = L.WIESE["halbe_breite"]
    X0, Y0, X1, Y1 = mx - h, my - h, mx + h, my + h
    bm = bmesh.new()
    for a, b in (((X0, Y0), (X1, y0)), ((X0, y1), (X1, Y1)), ((X0, y0), (x0, y1)), ((x1, y0), (X1, y1))):
        bm.faces.new([bm.verts.new((a[0], a[1], 0)), bm.verts.new((b[0], a[1], 0)),
                      bm.verts.new((b[0], b[1], 0)), bm.verts.new((a[0], b[1], 0))])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    o = mesh_aus_bmesh("Wiese", bm, "01b_Wiese", mats=[material("M_Erde")])
    gn.anwenden(o, "Wiese", "Bib_Halme", "Maske_Beet", dichte_lauf=4, dichte_schoen=40, abstand=0.06,
                skala=(0.9, 1.6), neigung=0.2, seed=7, basis=True)
    return {"wiese": o.name}


def heckenblatt_bibliothek():
    leere("Bib_Heckenblatt")
    m = pflanzen_material("M_Heckenblatt", [(0.0, (0.02, 0.05, 0.012)), (0.6, (0.04, 0.09, 0.02)),
                                            (1.0, (0.08, 0.13, 0.03))], durchscheinend=0.3, form="birke")
    rnd = random.Random(31)
    for k in range(6):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        for _ in range(14):
            c = Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), rnd.uniform(-0.05, 0.05)))
            l = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 1))).normalized()
            w = l.cross(Vector((0.3, 0.2, 1.0))).normalized()
            b, hh = rnd.uniform(0.035, 0.05), rnd.uniform(0.05, 0.07)
            f = bm.faces.new([bm.verts.new(p) for p in (c - w * b / 2, c + w * b / 2, c + l * hh + w * b / 2, c + l * hh - w * b / 2)])
            for loop, koord in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uv].uv = koord
        mesh_aus_bmesh(f"Heckenblaetter_{k}", bm, "Bib_Heckenblatt", mats=[m])


def hecken():
    leere("01c_Heckenkern")
    leere("05g_Hecke")
    heckenblatt_bibliothek()
    kern_mat = material("M_Hecke_Kern", (0.01, 0.025, 0.008), 0.9)
    hoehe, tiefe = L.HECKE_MASS["hoehe"], L.HECKE_MASS["tiefe"]
    for i, (a, b) in enumerate(L.HECKEN):
        a, b = Vector(a), Vector(b)
        laenge = (b - a).length
        bm = bmesh.new()
        geo = bmesh.ops.create_cube(bm, size=1.0)
        for v in geo["verts"]:
            v.co = Vector((v.co.x * laenge, v.co.y * tiefe, (v.co.z + 0.5) * hoehe))
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
        for v in bm.verts:  # leicht unregelmäßige Oberfläche
            v.co += Vector((0, math.sin(v.co.x * 1.7) * 0.05, math.sin(v.co.x * 0.9 + v.co.z) * 0.05))
        kern = mesh_aus_bmesh(f"Hecke_{i + 1}_Kern", bm, "01c_Heckenkern", mats=[kern_mat])
        kern.location = ((a.x + b.x) / 2, (a.y + b.y) / 2, 0.0)
        kern.rotation_euler = (0.0, 0.0, math.atan2(b.y - a.y, b.x - a.x))
        laub = bpy.data.objects.new(f"Hecke_{i + 1}_Laub", kern.data)
        bpy.data.collections["05g_Hecke"].objects.link(laub)
        laub.location, laub.rotation_euler = kern.location, kern.rotation_euler
        gn.anwenden(laub, "Streuen", "Bib_Heckenblatt", "Maske_Beet", dichte_lauf=120, dichte_schoen=500,
                    abstand=0.03, skala=(0.8, 1.3), neigung=3.14, seed=40 + i, basis=False)
    return {"hecken": len(L.HECKEN)}
```

- [ ] **Schritt 4: Ausführen.** Nacheinander per MCP-Aufruf:
1. `kulisse.wiese()`
2. `kulisse.hecken()`
3. `util.speichern()`

Prüfaufrufe:
- `rasen()`: erwartet `ok: true`, es wächst also kein Rasen in den Heckenkernen und das Gras auf dem Hof bleibt weg.
- `kulisse()`: erwartet weiterhin `ok: false`, aber nur mit dem Fehler „Kulissenbäume“.

- [ ] **Schritt 5: Commit** `git add scripts && git commit -m "Wiese und Hecken"`

---

### Task 18: Baumkulisse

**Dateien:** Ändern: `scripts/gartenlib/baeume.py`, `scripts/gartenlib/kulisse.py`

- [ ] **Schritt 1: `baeume.py` erweitern.**
- In `_Bauer.__init__` die Signatur auf `def __init__(self, art, rnd, blatt_faktor=1.0):` ändern und `self.blatt_faktor = blatt_faktor` setzen.
- In `ast()` die Blattzahl-Zeile ersetzen durch:

```python
            for _ in range(int(laenge * self.a["blatt_dichte"] * self.blatt_faktor)):
```

`baum()` vollständig ersetzen:

```python
def baum(name, art, ort, hoehe, seed, laub_mat, rinde_mat, blatt_faktor=1.0, sammlung="05e_Baeume"):
    rnd = random.Random(seed * 101 + 7)
    a = ARTEN[art]
    bauer = _Bauer(art, rnd, blatt_faktor)
    stamm_l = hoehe * a["stamm"][0]
    bauer.ast(Vector((0, 0, -0.1)), Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 1)).normalized(),
              stamm_l, hoehe * a["stamm"][1], 0)
    obj = mesh_aus_bmesh(name, bauer.holz, sammlung, mats=[rinde_mat])
    laub = mesh_aus_bmesh(f"{name}_Laub", bauer.laub, sammlung, eltern=obj, mats=[laub_mat])
    for p in obj.data.polygons:
        p.use_smooth = True
    hmax = max(max(v.co.z for v in obj.data.vertices), max((v.co.z for v in laub.data.vertices), default=0))
    k = hoehe / hmax
    obj.scale = (k, k, k)
    obj.location = (ort[0], ort[1], 0.0)
    obj.rotation_euler = (0.0, 0.0, seed * 1.3)
    return {"name": name, "blaetter": len(laub.data.polygons), "holz_flaechen": len(obj.data.polygons)}
```

- [ ] **Schritt 2: `baumkulisse()` an `kulisse.py` anhängen**

```python
def baumkulisse():
    """Vier Vorlagebäume, als verknüpfte Kopien (geteilte Mesh-Daten) im Ring um das Grundstück verteilt."""
    from .baeume import baum
    leere("05f_Kulisse")
    K = L.KULISSE
    mats = {"birke": (bpy.data.materials["M_Blatt_Birke"], bpy.data.materials["M_Rinde_Birke"]),
            "ahorn": (bpy.data.materials["M_Blatt_Ahorn"], bpy.data.materials["M_Rinde_Ahorn"])}
    vorlagen = []
    for name, art, hoehe, seed in K["vorlagen"]:
        laub_m, rinde_m = mats[art]
        baum(name, art, (0.0, 0.0), hoehe, seed, laub_m, rinde_m, blatt_faktor=K["blatt_faktor"], sammlung="05f_Kulisse")
        vorlagen.append(bpy.data.objects[name])
    rnd = random.Random(K["seed"])
    mx, my = K["mitte"]
    platziert = 0
    for i in range(K["anzahl"]):
        w = 2 * math.pi * (i + rnd.uniform(-0.35, 0.35)) / K["anzahl"]
        r = rnd.uniform(K["r_min"], K["r_max"])
        ort = (mx + math.cos(w) * r, my + math.sin(w) * r, 0.0)
        v = vorlagen[i % len(vorlagen)]
        if i < len(vorlagen):
            o = v
        else:
            o = v.copy()  # teilt die Mesh-Daten
            bpy.data.collections["05f_Kulisse"].objects.link(o)
            laub_v = bpy.data.objects[f"{v.name}_Laub"]
            laub = laub_v.copy()
            laub.name = f"Kulisse_{i:02d}_Laub"
            bpy.data.collections["05f_Kulisse"].objects.link(laub)
            laub.parent = o
            o.name = f"Kulisse_{i:02d}"
        o.location = ort
        o.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
        s = o.scale.x * rnd.uniform(0.85, 1.15)
        o.scale = (s, s, s)
        platziert += 1
    return {"kulissenbaeume": platziert}
```

- [ ] **Schritt 3: Ausführen.** MCP-Aufruf `kulisse.baumkulisse()`, danach `util.speichern()`. Prüfaufruf `kulisse()`: erwartet `ok: true`. Prüfaufruf `baeume()`: erwartet weiterhin `ok: true`.

- [ ] **Schritt 4: Renders ansehen** (CYCLES, 128 Samples, 50 %): `renders/08_kulisse_referenz.png` (Kamera_Referenz) und `renders/08_kulisse_uebersicht.png` (Kamera_Uebersicht). Soll:
- In der Übersicht ist das Grundstück rundum von Hecke und Wiese umgeben, und dahinter steht ein lockerer Baumring.
- In der Referenzansicht wirkt der Hintergrund wie Bild 2: Bäume statt freiem Horizont, das HDRI ist höchstens zwischen den Bäumen zu sehen.

Wirkt der Ring zu dicht, `anzahl` in `KULISSE` senken, wirkt er zu dünn, erhöhen. Höchstens 2 Runden.

- [ ] **Schritt 5: Commit** `git add scripts && git commit -m "Baumkulisse"`

---

### Task 19: Möbel und Innentexturen von Poly Haven (mit Freigabe)

**Dateien:** Ändern: `scripts/polyhaven.py`, `assets/auswahl.json`

- [ ] **Schritt 1: Rollen ergänzen.** In `ROLLEN` in `scripts/polyhaven.py` anhängen:

```python
    "tex_parkett": ("textures", ["wood_floor", "parquet", "laminate"]),
    "tex_arbeitsplatte": ("textures", ["marble", "granite", "terrazzo"]),
    "modelle_sofa": ("models", ["sofa", "couch"]),
    "modelle_sessel_innen": ("models", ["armchair"]),
    "modelle_couchtisch": ("models", ["coffee_table", "side_table"]),
    "modelle_esstisch": ("models", ["dining_table", "wooden_table", "table"]),
    "modelle_stuhl": ("models", ["chair"]),
    "modelle_lampe": ("models", ["floor_lamp", "lamp"]),
    "modelle_zimmerpflanze": ("models", ["potted_plant"]),
    "modelle_teppich": ("models", ["rug", "carpet"]),
```

Im `__main__`-Zweig `plan` den Ausgabeteil ersetzen, damit nur fehlende Dateien als Download zählen:

```python
    elif befehl == "plan":
        p = plan()
        fehlend = [(u, z, g) for u, z, g in p if not (os.path.exists(z) and os.path.getsize(z) == g)]
        for url, ziel, groesse in fehlend:
            print(f"{groesse / 1e6:8.1f} MB  {os.path.relpath(ziel, PROJEKT)}")
        print(f"NEU ZU LADEN: {sum(g for _, _, g in fehlend) / 1e6:.0f} MB in {len(fehlend)} Dateien "
              f"({len(p) - len(fehlend)} schon vorhanden)")
```

- [ ] **Schritt 2: Kandidaten abfragen.** Es werden nur API-Daten gelesen.

```bash
cd "/d/KI Projekte/Blender MArtists" && "/c/Program Files/Blender Foundation/Blender 5.1/5.1/python/bin/python.exe" scripts/polyhaven.py kandidaten
```

- [ ] **Schritt 3: Vorschaubilder ansehen.** `assets/kandidaten.html` im eingebauten Browser öffnen und pro neuer Rolle das passendste Modell wählen.
- **Allgemein:** schlicht-modern, passend zu Putz, Holz und Anthrazit.
- **Teppich:** Fehlt ein Teppich, bleibt die Rolle weg; `innenraum.py` überspringt fehlende Rollen.

- [ ] **Schritt 4: Neue Rollen in `assets/auswahl.json` eintragen.**
- Format wie bisher: eine ID als Text, Modelle dürfen auch Listen sein, `innenraum.py` nimmt das erste Element.
- Danach `polyhaven.py plan` ausführen. Erwartet: `NEU ZU LADEN: … MB in … Dateien (52 schon vorhanden)`.

- [ ] **Schritt 5: FREIGABE.**
- Stephan die gewählten Modelle, die Dateiliste und die Größe zeigen und fragen: „Darf ich diese Dateien von polyhaven.com laden?“
- **Ohne ein klares Ja geht es nicht weiter.**

- [ ] **Schritt 6: Laden** mit `polyhaven.py lade`. Danach Prüfaufruf `assets()`, erwartet `ok: true`.

- [ ] **Schritt 7: Commit** `git add scripts && git commit -m "Poly-Haven-Rollen für den Innenraum"`

---

### Task 20: Erdgeschoss innen

**Dateien:** Ändern: `scripts/gartenlib/layout.py`, `scripts/gartenlib/materialien.py`; Neu: `scripts/gartenlib/innenraum.py`

- [ ] **Schritt 1: An `layout.py` anhängen**

```python
# ---------------------------------------------------------------- Teil 2: Erdgeschoss innen (Haus-lokale Koordinaten)
# Innenraum: x −5,7 … 5,7, y −4,2 … 4,2, Fußboden z 0,15, Decke z 2,75.
# Terrassentür offen bei x 1,3 … 2,6 an der Südwand – dieser Streifen bleibt frei.
INNEN = {
    "boden_z": 0.15, "decke_z": 2.75, "breite": 11.4, "tiefe": 8.4,
    "kueche": {"zeile": ((2.3, 3.89), (3.6, 0.62)), "hochschrank": ((4.9, 3.89), (1.2, 0.62)),
               "insel": ((2.3, 1.7), (2.4, 0.9))},
    # (rolle, name, (x, y), drehung_grad) – Annahme: Poly-Haven-Möbel zeigen mit der Front nach −Y
    "moebel": [
        ("modelle_teppich", "Teppich", (-2.8, -1.8), 0.0),
        ("modelle_sofa", "Sofa", (-2.8, -0.6), 0.0),
        ("modelle_couchtisch", "Couchtisch", (-2.8, -2.0), 0.0),
        ("modelle_sessel_innen", "Sessel_Innen", (-4.8, -2.2), -90.0),
        ("modelle_lampe", "Stehlampe", (-5.2, -0.4), 0.0),
        ("modelle_esstisch", "Esstisch", (-2.2, 2.4), 0.0),
        ("modelle_stuhl", "Stuhl_1", (-2.9, 1.7), 180.0),
        ("modelle_stuhl", "Stuhl_2", (-1.5, 1.7), 180.0),
        ("modelle_stuhl", "Stuhl_3", (-2.9, 3.1), 0.0),
        ("modelle_stuhl", "Stuhl_4", (-1.5, 3.1), 0.0),
        ("modelle_zimmerpflanze", "Pflanze_1", (5.1, -3.6), 0.0),
        ("modelle_zimmerpflanze", "Pflanze_2", (-5.2, 3.6), 0.0),
    ],
    # (name, typ, (x, y, z), leistung_w, größe_m)
    "lichter": [
        ("Licht_Essen", "AREA", (-2.2, 2.4, 2.70), 120.0, 0.8),
        ("Licht_Wohnen", "AREA", (-2.8, -1.5, 2.70), 150.0, 1.2),
        ("Licht_Kueche", "AREA", (2.3, 2.8, 2.70), 150.0, 1.0),
    ],
    "kamera": {"ort": (4.6, 3.2, 1.6), "ziel": (-3.0, -2.0, 1.1), "brennweite": 18.0},
}
```

- [ ] **Schritt 2: Materialien ergänzen.** In `TEXTUR_MATS` in `materialien.py` anhängen:

```python
    "M_Parkett": dict(rolle="tex_parkett", skala=2.0),
    "M_Arbeitsplatte": dict(rolle="tex_arbeitsplatte", skala=1.0, rauheit_min=0.25),
```

- [ ] **Schritt 3: Prüfaufruf `innenraum()`.** Erwartet `ok: false`.

- [ ] **Schritt 4: `innenraum.py` schreiben**

```python
"""Erdgeschoss innen: Parkett, Decke, Küche, Poly-Haven-Möbel, Leuchten, Eevee-Lichtsonden, Innenkamera."""
import glob
import math

import bpy
from mathutils import Matrix, Vector

from . import layout as L
from .materialien import auswahl
from .util import boxen_objekt, leere, material, neues_objekt, pfad, setze, view3d_kontext

S = "03_Innenraum"


def _modell_laden(aid):
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
    teile = [(o, o.matrix_world.copy()) for o in meshes]
    ecken = [mw @ Vector(c) for o, mw in teile for c in o.bound_box]
    mitte_unten = Vector(((min(e.x for e in ecken) + max(e.x for e in ecken)) / 2,
                          (min(e.y for e in ecken) + max(e.y for e in ecken)) / 2, min(e.z for e in ecken)))
    return {"teile": teile, "mitte_unten": mitte_unten, "benutzt": False}


def _moebel(rolle, name, ort, drehung, haus, cache, log):
    a = auswahl()
    if rolle not in a:
        log.append(f"{name}: Rolle {rolle} nicht gewählt – übersprungen")
        return
    aid = a[rolle][0] if isinstance(a[rolle], list) else a[rolle]
    if aid not in cache:
        cache[aid] = _modell_laden(aid)
    c = cache[aid]
    wurzel = neues_objekt(f"Moebel_{name}", None, S, eltern=haus)
    wurzel.location = (ort[0], ort[1], L.INNEN["boden_z"] + 0.02)
    wurzel.rotation_euler = (0.0, 0.0, math.radians(drehung))
    for o, mw in c["teile"]:
        teil = o if not c["benutzt"] else o.copy()
        bpy.data.collections[S].objects.link(teil)
        teil.parent = wurzel
        teil.matrix_parent_inverse = Matrix.Identity(4)
        teil.matrix_basis = Matrix.Translation(-c["mitte_unten"]) @ mw
    c["benutzt"] = True


def _kueche(haus):
    I = L.INNEN
    z = I["boden_z"]
    front = material("M_Kueche_Front", (0.05, 0.05, 0.055), 0.55)
    platte = bpy.data.materials["M_Arbeitsplatte"]
    k = I["kueche"]
    korpusse = []
    for (x, y), (b, t) in (k["zeile"], k["insel"]):
        korpusse.append(((b, t, 0.86), (x, y, z + 0.43)))
    (hx, hy), (hb, ht) = k["hochschrank"]
    korpusse.append(((hb, ht, 2.3), (hx, hy, z + 1.15)))
    boxen_objekt("Innen_Kueche", korpusse, S, haus, front)
    platten = [((b + 0.04, t + 0.04, 0.04), (x, y, z + 0.88)) for (x, y), (b, t) in (k["zeile"], k["insel"])]
    boxen_objekt("Innen_Arbeitsplatte", platten, S, haus, platte)


def _lichter(haus):
    for name, typ, (x, y, z), leistung, groesse in L.INNEN["lichter"]:
        li = bpy.data.lights.get(name) or bpy.data.lights.new(name, typ)
        li.energy = leistung
        li.color = (1.0, 0.82, 0.62)  # warmweiß, ca. 2900 K
        if typ == "AREA":
            li.size = groesse
        o = neues_objekt(name, li, S, eltern=haus)
        o.location = (x, y, z)


def _lichtsonden(haus, log):
    I = L.INNEN
    mitte_z = (I["boden_z"] + I["decke_z"]) / 2
    gi = bpy.data.lightprobes.get("Innen_GI") or bpy.data.lightprobes.new("Innen_GI", "VOLUME")
    o = neues_objekt("Innen_GI", gi, S, eltern=haus)
    o.location = (0.0, 0.0, mitte_z)
    o.scale = (I["breite"] / 2, I["tiefe"] / 2, (I["decke_z"] - I["boden_z"]) / 2)
    for attr, wert in (("resolution_x", 12), ("resolution_y", 9), ("resolution_z", 4)):
        setze(gi, attr, wert, log)
    ref = bpy.data.lightprobes.get("Innen_Reflexion") or bpy.data.lightprobes.new("Innen_Reflexion", "SPHERE")
    setze(ref, "influence_distance", 7.0, log)
    o2 = neues_objekt("Innen_Reflexion", ref, S, eltern=haus)
    o2.location = (0.0, 0.0, mitte_z)


def _kamera(haus):
    K = L.INNEN["kamera"]
    alt = bpy.data.objects.get("Kamera_Innen")
    if alt is not None:
        bpy.data.objects.remove(alt, do_unlink=True)
    cam = bpy.data.cameras.get("Kamera_Innen") or bpy.data.cameras.new("Kamera_Innen")
    cam.lens = K["brennweite"]
    cam.clip_start = 0.05
    o = neues_objekt("Kamera_Innen", cam, "07_Kameras")
    mw = haus.matrix_world
    ort, ziel = mw @ Vector(K["ort"]), mw @ Vector(K["ziel"])
    o.location = ort
    o.rotation_euler = (ziel - ort).to_track_quat("-Z", "Y").to_euler()


def baue():
    log = []
    leere(S)
    haus = bpy.data.objects["Haus"]
    I = L.INNEN
    boxen_objekt("Innen_Boden", [((I["breite"], I["tiefe"], 0.02), (0.0, 0.0, I["boden_z"] + 0.01))], S, haus,
                 bpy.data.materials["M_Parkett"])
    boxen_objekt("Innen_Decke", [((I["breite"], I["tiefe"], 0.01), (0.0, 0.0, I["decke_z"] - 0.006))], S, haus,
                 material("M_Decke", (0.82, 0.81, 0.78), 0.9))
    _kueche(haus)
    cache = {}
    for rolle, name, ort, drehung in I["moebel"]:
        _moebel(rolle, name, ort, drehung, haus, cache, log)
    _lichter(haus)
    _lichtsonden(haus, log)
    _kamera(haus)
    return {"log": log, "objekte": len(bpy.data.collections[S].all_objects)}


def sonden_backen():
    """Eevee-Lichtsonden backen (nötig für weiches Licht im Innenraum beim Laufen)."""
    with bpy.context.temp_override(**view3d_kontext()):
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
    return {"gebacken": True}
```

- [ ] **Schritt 5: Ausführen.** Nacheinander per MCP-Aufruf:
1. `materialien.baue()`
2. `innenraum.baue()`
3. `innenraum.sonden_backen()`
4. `util.speichern()`

Steht in `log`, dass etwas „übersprungen“ wurde, ist das okay, solange die Prüfung mindestens 6 Möbel zählt.

- [ ] **Schritt 6: Prüfaufruf `innenraum()`.** Erwartet: `ok: true`.
- Ist die Terrassentür blockiert, steht ein Möbelstück im Laufweg x 1,3 … 2,6. Dann `ort` in `INNEN["moebel"]` verschieben.

- [ ] **Schritt 7: Innenrender** `renders/09_innen.png` (CYCLES, 256 Samples, 50 %, Kamera_Innen, Modus 1) ansehen. Soll:
- Möbel stehen auf dem Boden, nicht darin und nicht schwebend.
- Sofa, Sessel und Stühle zeigen zum Couchtisch bzw. Esstisch.
- Der Raum ist hell genug, die Fenster zeigen den Garten.

Korrekturen:
- **Falsch gedrehte Möbel:** `drehung_grad` in `INNEN["moebel"]` um 90°/180° anpassen.
- **Zu dunkel:** `leistung_w` erhöhen.

Neu bauen und rendern, höchstens 3 Runden.

- [ ] **Schritt 8: Commit** `git add scripts && git commit -m "Erdgeschoss innen"`

---

### Task 21: Laufen einrichten und auf mindestens 25 fps abstimmen

**Dateien:** Ändern: `scripts/gartenlib/layout.py`; Neu: `scripts/gartenlib/lauf.py`

- [ ] **Schritt 1: An `layout.py` anhängen**

```python
# ---------------------------------------------------------------- Teil 2: Laufen
KAMERA_LAUFEN = {"ort": (3.8, -8.6, 1.7), "ziel": (-2.3, 4.0, 1.6), "brennweite": 24.0}
```

- [ ] **Schritt 2: Prüfaufruf `lauf()`.** Erwartet `ok: false`.

- [ ] **Schritt 3: `lauf.py` schreiben**

```python
"""Laufen im Viewport: Walk-Einstellungen, Laufkamera, Startansicht, Modus-Treiber, fps-Messung."""
import math
import time

import bpy
from mathutils import Quaternion, Vector

from . import layout as L
from .util import modus_setzen, neues_objekt, setze, treiber_modus, view3d_kontext


def einrichten():
    log = []
    prefs = bpy.context.preferences
    setze(prefs.inputs, "navigation_mode", "WALK", log)
    wn = prefs.inputs.walk_navigation
    for attr, wert in (("use_gravity", True), ("view_height", 1.7), ("jump_height", 0.4), ("walk_speed", 2.5),
                       ("walk_speed_factor", 3.0), ("teleport_time", 0.2), ("mouse_speed", 1.0)):
        setze(wn, attr, wert, log)
    bpy.ops.wm.save_userpref()

    K = L.KAMERA_LAUFEN
    alt = bpy.data.objects.get("Kamera_Laufen")
    if alt is not None:
        bpy.data.objects.remove(alt, do_unlink=True)
    cam = bpy.data.cameras.get("Kamera_Laufen") or bpy.data.cameras.new("Kamera_Laufen")
    cam.lens = K["brennweite"]
    cam.clip_start = 0.05
    cam.clip_end = 500.0
    o = neues_objekt("Kamera_Laufen", cam, "07_Kameras")
    o.location = K["ort"]
    o.rotation_euler = (Vector(K["ziel"]) - Vector(K["ort"])).to_track_quat("-Z", "Y").to_euler()

    sc = bpy.context.scene
    treiber_modus(sc, "eevee.shadow_resolution_scale", "0.5 + 0.5 * m")
    sc.render.use_simplify = True
    setze(sc.render, "simplify_subdivision", 1, log)
    setze(sc.render, "simplify_subdivision_render", 6, log)
    return {"log": log}


def startansicht(kamera="Kamera_Laufen", modus=0.0):
    """Setzt alle 3D-Viewports auf die Position der Laufkamera (ohne die Kamera selbst zu bewegen), Eevee gerendert."""
    cam = bpy.data.objects[kamera]
    modus_setzen(modus)
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    vorne = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    for fenster in bpy.context.window_manager.windows:
        for bereich in fenster.screen.areas:
            if bereich.type != "VIEW_3D":
                continue
            raum = bereich.spaces[0]
            raum.shading.type = "RENDERED"
            raum.lens = cam.data.lens
            raum.clip_start, raum.clip_end = 0.05, 500.0
            r3d = raum.region_3d
            r3d.view_perspective = "PERSP"
            r3d.view_rotation = cam.matrix_world.to_quaternion()
            r3d.view_distance = 0.5
            r3d.view_location = cam.matrix_world.translation + vorne * 0.5
    return {"ansicht": kamera}


def fps_messen(bilder=40):
    """Dreht die Ansicht pro Bild leicht (wie beim Umschauen) und misst die Zeichenrate im 3D-Viewport."""
    ctx = view3d_kontext()
    r3d = ctx["area"].spaces[0].region_3d
    start = r3d.view_rotation.copy()
    schritt = Quaternion(Vector((0, 0, 1)), math.radians(0.5))
    with bpy.context.temp_override(**ctx):
        bpy.ops.wm.redraw_timer(type="DRAW", iterations=5)  # Aufwärmen, Shader kompilieren
        t = time.perf_counter()
        for _ in range(bilder):
            r3d.view_rotation = schritt @ r3d.view_rotation
            bpy.ops.wm.redraw_timer(type="DRAW", iterations=1)
        dauer = time.perf_counter() - t
    r3d.view_rotation = start
    fps = bilder / dauer
    bpy.data.objects["Steuerung"]["fps_laufen"] = fps
    return {"fps": round(fps, 1)}
```

- [ ] **Schritt 4: Einrichten und messen.** Nacheinander per MCP-Aufruf:
1. `lauf.einrichten()`
2. `lauf.startansicht()`
3. `lauf.fps_messen()`

Beim ersten Mal kompiliert Eevee Shader und das kann dauern. Deshalb `fps_messen()` zweimal aufrufen und den zweiten Wert nehmen.
- Prüfung: Die Messung hängt am Viewport. Ist das Blender-Fenster minimiert, misst sie Unsinn. Bei weniger als 2 fps oder mehr als 500 fps Stephan bitten, Blender in den Vordergrund zu holen, und erneut messen.

- [ ] **Schritt 5: Abstimmen, bis mindestens 25 fps erreicht sind.** Nach jeder Stellschraube neu messen und nach Erreichen aufhören. Reihenfolge:

| # | Stellschraube | Code (MCP) |
|---|---|---|
| 1 | Rasen dünner beim Laufen | in `pflanzen.rasen()` `dichte_lauf=35`, dann `pflanzen.rasen()` |
| 2 | Hecken dünner | in `kulisse.hecken()` `dichte_lauf=60`, dann `kulisse.hecken()` |
| 3 | Wiese ohne Gras beim Laufen | in `kulisse.wiese()` `dichte_lauf=0`, dann `kulisse.wiese()` |
| 4 | Raytracing halbe Auflösung | `bpy.context.scene.eevee.ray_tracing_options.resolution_scale = "2"` |
| 5 | Weniger Viewport-Samples | `bpy.context.scene.eevee.taa_samples = 8` |
| 6 | Bodengras in Beeten dünner | in `layout._mix` die Halme-Schicht auf `10.0 * boden` setzen, dann `pflanzen.bepflanzung()` |

Bei Stellschrauben 1–3 und 6 die Zahl im Code ändern, damit sie beim Neubauen erhalten bleibt.

- [ ] **Schritt 6: Prüfaufruf `lauf()`.** Erwartet: `ok: true` mit `fps` ≥ 25. Danach `util.speichern()`.

- [ ] **Schritt 7: Commit** `git add scripts && git commit -m "Laufen eingerichtet und abgestimmt"`

---

### Task 22: Anleitung, Gesamtprüfung, Abschlussrenders

**Dateien:** Neu: `docs/Anleitung_Laufen.md`

- [ ] **Schritt 1: Anleitung schreiben**

```markdown
# So läufst du durch den Garten

1. `garten.blend` in Blender öffnen.
2. Maus über den 3D-Bereich, **Shift + `** drücken (auf deutscher Tastatur ggf. die Taste links neben der 1 –
   oder Menü **View › Navigation › Walk Navigation**).
3. Laufen: **W A S D**, umschauen: **Maus**, schneller: **Shift** halten, springen: **V**,
   Schwerkraft an/aus: **Tab**, hinbeamen: auf ein Ziel schauen und **Leertaste** drücken.
4. Beenden: **linke Maustaste** (Position behalten) oder **rechte Maustaste/Esc** (zurück zum Start).

**Startposition zurückholen:** In Blender `Scripting`-Tab, unten in die Python-Konsole:
`import gartenlib; gartenlib.lade("lauf").startansicht()` (vorher einmal
`import sys; sys.path.insert(0, r"D:\KI Projekte\Blender MArtists\scripts")`).

**Schnell oder schön:** Objekt **Steuerung** auswählen, im Eigenschaften-Panel (N) unter *Item › Properties*
den Wert **modus** setzen: **0 = Laufen** (flüssig), **1 = Schönbild** (volle Pflanzendichte, Dunst) –
danach kurz auf der Zeitleiste ein Bild weiter/zurück, damit Blender umschaltet.

**Fotorealistisches Standbild:** Kamera auswählen (z. B. *Kamera_Referenz*, *Kamera_Innen*), Ansicht durch die
Kamera (**Numpad 0**), Render-Engine auf **Cycles**, **F12**.

Grenzen: Wände halten dich beim Laufen nicht auf – Blender beachtet nur den Boden.
```

- [ ] **Schritt 2: Gesamtprüfung.** MCP:

```python
import sys, importlib
P = r"D:\KI Projekte\Blender MArtists\scripts"
if P not in sys.path:
    sys.path.insert(0, P)
import gartenlib
pr = gartenlib.lade("pruefung")
result = {k: getattr(pr, k)() for k in ["einrichtung", "struktur", "architektur", "hardscape", "kamera", "assets",
                                         "materialien", "welt", "rasen", "bepflanzung", "polster", "baeume",
                                         "kulisse", "innenraum", "lauf"]}
```

Erwartet: alle `ok: true`.

- [ ] **Schritt 3: Abschlussrenders** (CYCLES, 1024 Samples, 100 %, Modus 1), im Hintergrund:
- `renders/final_referenz.png` (Kamera_Referenz)
- `renders/final_innen.png` (Kamera_Innen)
- `renders/final_uebersicht.png` (Kamera_Uebersicht)

Alle drei ansehen und ehrlich mit Bild 2 vergleichen.

- [ ] **Schritt 4: Startansicht setzen und speichern.** MCP: `lauf.startansicht()`, danach `util.speichern()`. Beim Öffnen steht Stephan dann am Startpunkt in Eevee.

- [ ] **Schritt 5: Commit** `git add scripts docs && git commit -m "Teil 2 abgeschlossen: Anleitung und Abschlussrenders"`

- [ ] **Schritt 6: Übergabe.**
- Stephan bekommt die drei Renders (SendUserFile), den Link zur Anleitung, die gemessene fps-Zahl und ehrliche Grenzen: keine Wandkollision, Obergeschoss nicht begehbar.
- Danach fragen, ob Stephan selbst probelaufen möchte.

---

## Selbstprüfung des Plans

**Abdeckung der Spec:**

| Spec-Schritt | Umsetzung |
|---|---|
| Schritt 5, Grundstück und Kulisse | Task 17–18; Carport und Hof stehen schon aus Teil 1 |
| Schritt 6, Erdgeschoss innen mit Möbeln und Licht | Task 19–20 |
| Schritt 7, Lauf-Tuning mit fps-Messung und mindestens 25 fps | Task 21 |
| Steuerung „Laufen/Schönbild“ inkl. Eevee-Schatten | Task 21, Schritt 3 (`treiber_modus` auf `eevee.shadow_resolution_scale`) |
| Kameras für Terrasse, Innen, Übersicht | Kamera_Laufen (Startpunkt), Kamera_Innen, Kamera_Uebersicht |

Restpunkte aus der Qualitätsprobe:
- Die Rispenfarbe ist in Task 16 enthalten.
- Die Dachuntersicht bleibt bewusst so, auch in Bild 2 ist sie dunkel.

**Platzhalter:** keine. Die einzige Auswahl zur Laufzeit ist die Asset-Wahl in Task 19 (bewusst, weil per Freigabe).

**Einheitliche Namen:**
- Für `baum(..., blatt_faktor, sammlung)` liefert Task 18 die neue Signatur. Der Aufruf aus `baeume.baue()` bleibt kompatibel (Standardwerte).
- Die Collections `01b_Wiese`, `01c_Heckenkern`, `05g_Hecke` und `Bib_Heckenblatt` kommen in Task 17, Schritt 2, bevor sie benutzt werden.
- `M_Parkett` und `M_Arbeitsplatte` kommen in Task 20, Schritt 2, vor `innenraum.baue()`.
- `Steuerung["fps_laufen"]` schreibt `lauf.fps_messen()`, gelesen wird es von `pruefung.lauf()`.

**Risiken mit Gegenmaßnahme im Plan:**
- Ausrichtung der Möbelfronten (Task 20, Schritt 7)
- fps-Messung bei minimiertem Fenster (Task 21, Schritt 4)
- Fehlender Teppich bei Poly Haven (Rolle wird übersprungen)
- Lichtsonden-Attribute je Version (`setze` protokolliert statt abzubrechen)
