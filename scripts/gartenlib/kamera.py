"""Referenzkamera mit der Perspektive des Referenzbilds, dazu eine Übersichtskamera."""
import bpy
from mathutils import Vector

from . import layout as L
from .util import neues_objekt

UEBERSICHT = {"ort": (16.0, -30.0, 24.0), "ziel": (-3.0, 3.0, 0.0), "brennweite": 28.0}
HECKE_NAH = {"ort": (-19.0, -8.0, 1.6), "ziel": (-23.5, -3.0, 1.0), "brennweite": 30.0}  # Westhecke vom Rasen aus
HAUS_NAH = {"ort": (-2.0, 0.5, 1.65), "ziel": (-9.5, 9.0, 3.2), "brennweite": 24.0}  # Blick vom Rasen auf die Hausfront


def _kamera(name, ort, ziel, brennweite):
    alt = bpy.data.objects.get(name)
    if alt is not None:
        bpy.data.objects.remove(alt, do_unlink=True)
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = brennweite
    cam.sensor_width = 36.0
    cam.clip_start = 0.05
    cam.clip_end = 500.0
    o = neues_objekt(name, cam, "07_Kameras")
    o.location = ort
    o.rotation_euler = (Vector(ziel) - Vector(ort)).to_track_quat("-Z", "Y").to_euler()
    return o


def baue():
    K = L.KAMERA
    o = _kamera("Kamera_Referenz", K["ort"], K["ziel"], K["brennweite"])
    _kamera("Kamera_Uebersicht", UEBERSICHT["ort"], UEBERSICHT["ziel"], UEBERSICHT["brennweite"])
    _kamera("Kamera_Haus", HAUS_NAH["ort"], HAUS_NAH["ziel"], HAUS_NAH["brennweite"])
    _kamera("Kamera_Hecke", HECKE_NAH["ort"], HECKE_NAH["ziel"], HECKE_NAH["brennweite"])
    bpy.context.scene.camera = o
    return {"rotation": list(o.rotation_euler)}
