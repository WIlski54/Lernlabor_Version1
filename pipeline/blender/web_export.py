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
