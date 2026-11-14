"""blender -b labor.blend -P pipeline/blender/labor_bauen.py – baut das Labor und speichert labor.blend."""
import os
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
sys.path.insert(0, P)
import gartenlib  # noqa: E402

print(gartenlib.lade("labor").baue())
gartenlib.lade("util").speichern()
print("FERTIG labor")
