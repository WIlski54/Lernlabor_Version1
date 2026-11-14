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
