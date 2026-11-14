"""HDRI-Himmel (bewölkt), weiche Sonne, leichter Dunst (nur im Modus Schönbild)."""
import glob
import math

import bpy

from .materialien import auswahl
from .util import box, neues_objekt, pfad, treiber_modus


def baue(staerke=1.0, drehung_grad=150.0, sonne=1.2, dunst=0.0012):
    datei = glob.glob(pfad("assets", "polyhaven", "hdris", auswahl()["hdri_himmel"], "*.hdr"))[0]
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("Welt")
    sc.world = w
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(drehung_grad))
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(datei, check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = staerke
    aus = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], aus.inputs["Surface"])

    for name in ("Sonne", "Dunst"):
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    licht = bpy.data.lights.get("Sonne") or bpy.data.lights.new("Sonne", "SUN")
    licht.energy = sonne
    licht.angle = math.radians(6.0)
    licht.color = (1.0, 0.97, 0.92)
    o = neues_objekt("Sonne", licht, "06_Licht")
    o.rotation_euler = (math.radians(50.0), 0.0, math.radians(140.0))

    m = bpy.data.materials.get("M_Dunst") or bpy.data.materials.new("M_Dunst")
    mnt = m.node_tree
    mnt.nodes.clear()
    vol = mnt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = dunst
    vol.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1.0)
    maus = mnt.nodes.new("ShaderNodeOutputMaterial")
    mnt.links.new(vol.outputs[0], maus.inputs["Volume"])
    d = box("Dunst", (140.0, 140.0, 40.0), (0.0, 0.0, -1.0), "06_Licht", mat=m)
    d.display_type = "WIRE"
    treiber_modus(d, "hide_viewport", "m < 0.5")
    return {"hdri": datei}
