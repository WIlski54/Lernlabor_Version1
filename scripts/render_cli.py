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
