import os
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
sys.path.insert(0, P)
import gartenlib  # noqa: E402

w = gartenlib.lade("webexport")
ziel = sys.argv[sys.argv.index("--") + 1]
w.vorbereiten()
print("PROBE", w.bake_gruppe("hecke", ziel, samples=64))
