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
    "tex_weg": ("textures", ["square", "paving", "tiles"]),
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
