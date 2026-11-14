"""Laufen im Viewport: Walk-Einstellungen, Laufkamera, Startansicht, Modus-Treiber, fps-Messung."""
import math
import time

import bpy
from mathutils import Quaternion, Vector

from . import layout as L
from .util import modus_setzen, neues_objekt, setze, view3d_kontext


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
    sc.render.use_simplify = True
    setze(sc.render, "simplify_subdivision", 1, log)
    setze(sc.render, "simplify_subdivision_render", 6, log)
    return {"log": log}


def startansicht(kamera="Kamera_Laufen", modus=0.0):
    """Setzt alle 3D-Viewports auf die Position der Laufkamera (ohne die Kamera selbst zu bewegen), Eevee gerendert."""
    cam = bpy.data.objects[kamera]
    modus_setzen(modus)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.shadow_resolution_scale = 0.5 + 0.5 * modus  # nicht per Treiber steuerbar, daher hier
    vorne = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    for o in bpy.context.view_layer.objects:  # keine Auswahl-Umrisse beim Laufen
        o.select_set(False)
    for fenster in bpy.context.window_manager.windows:
        for bereich in fenster.screen.areas:
            if bereich.type != "VIEW_3D":
                continue
            raum = bereich.spaces[0]
            raum.shading.type = "RENDERED"
            raum.overlay.show_overlays = False  # keine Beziehungslinien, Lampen-/Kamerasymbole, Umrisse
            raum.lens = cam.data.lens
            raum.clip_start, raum.clip_end = 0.05, 500.0
            r3d = raum.region_3d
            r3d.view_perspective = "PERSP"
            r3d.view_rotation = cam.matrix_world.to_quaternion()
            r3d.view_distance = 0.5
            r3d.view_location = cam.matrix_world.translation + vorne * 0.5
    return {"ansicht": kamera}


def fps_messen(bilder=40, aufwaermen_max_s=20.0):
    """Dreht die Ansicht pro Bild leicht (wie beim Umschauen) und misst die Zeichenrate im 3D-Viewport.
    Wärmt vorher auf, bis 8 Bilder in Folge um weniger als 25 % schwanken (Eevee baut nach Änderungen
    Shader und Schatten neu auf – diese Phase würde die Messung verfälschen)."""
    ctx = view3d_kontext()
    r3d = ctx["area"].spaces[0].region_3d
    start = r3d.view_rotation.copy()
    schritt = Quaternion(Vector((0, 0, 1)), math.radians(0.5))

    def bild():
        r3d.view_rotation = schritt @ r3d.view_rotation
        t0 = time.perf_counter()
        bpy.ops.wm.redraw_timer(type="DRAW", iterations=1)
        return time.perf_counter() - t0

    with bpy.context.temp_override(**ctx):
        ende = time.perf_counter() + aufwaermen_max_s
        letzte = []
        while time.perf_counter() < ende:
            letzte = (letzte + [bild()])[-8:]
            if len(letzte) == 8 and max(letzte) < 1.25 * min(letzte):
                break
        zeiten = sorted(bild() for _ in range(bilder))
    r3d.view_rotation = start
    median = zeiten[len(zeiten) // 2]
    fps = 1.0 / median
    bpy.data.objects["Steuerung"]["fps_laufen"] = fps
    return {"fps": round(fps, 1), "ms_median": round(median * 1000, 1), "ms_max": round(zeiten[-1] * 1000, 1)}
