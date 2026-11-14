"""Hilfsfunktionen für den Szenenbau."""
import os

import bmesh
import bpy
from mathutils import Euler, Vector

PROJEKT = r"D:\KI Projekte\Blender MArtists"


def pfad(*teile):
    return os.path.join(PROJEKT, *teile)


def setze(obj, attr, wert, log):
    """Setzt ein Attribut, falls es in dieser Blender-Version existiert; Probleme landen im Log."""
    if not hasattr(obj, attr):
        log.append(f"fehlt: {type(obj).__name__}.{attr}")
        return False
    try:
        setattr(obj, attr, wert)
        return True
    except Exception as e:  # z. B. unbekannter Enum-Wert
        log.append(f"{attr}={wert!r}: {e}")
        return False


def coll(name):
    return bpy.data.collections[name]


def collection(name, eltern=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    ziel = bpy.context.scene.collection if eltern is None else coll(eltern)
    if c.name not in ziel.children:
        ziel.children.link(c)
    return c


def layer_collection(name, lc=None):
    lc = lc or bpy.context.view_layer.layer_collection
    if lc.collection.name == name:
        return lc
    for kind in lc.children:
        treffer = layer_collection(name, kind)
        if treffer:
            return treffer
    return None


def leere(name):
    """Entfernt alle Objekte einer Collection (rekursiv) und danach verwaiste Meshes/Kurven."""
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for o in list(c.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for cu in list(bpy.data.curves):
        if cu.users == 0:
            bpy.data.curves.remove(cu)


def neues_objekt(name, daten, sammlung, eltern=None):
    o = bpy.data.objects.new(name, daten)
    coll(sammlung).objects.link(o)
    if eltern is not None:
        o.parent = eltern
    return o


def material(name, farbe=(0.8, 0.8, 0.8), rauheit=0.5, metall=0.0):
    """Holt ein Material oder legt einen einfachen Platzhalter an (Task 8 wertet ihn auf)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        try:
            m.use_nodes = True
        except Exception:
            pass
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*farbe, 1.0)
        b.inputs["Roughness"].default_value = rauheit
        b.inputs["Metallic"].default_value = metall
        m.diffuse_color = (*farbe, 1.0)
    return m


def bm_box(bm, groesse, mitte, rot=(0.0, 0.0, 0.0)):
    """Fügt einem BMesh einen Quader hinzu (zentriert auf mitte, gedreht um rot in Radiant)."""
    geo = bmesh.ops.create_cube(bm, size=1.0)
    m = Euler(rot).to_matrix()
    for v in geo["verts"]:
        lokal = Vector((v.co.x * groesse[0], v.co.y * groesse[1], v.co.z * groesse[2]))
        v.co = m @ lokal + Vector(mitte)
    return geo


def mesh_aus_bmesh(name, bm, sammlung, eltern=None, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return neues_objekt(name, me, sammlung, eltern)


def box(name, groesse, ort=(0, 0, 0), sammlung="02_Architektur", eltern=None, rot_z=0.0, boden=True, mat=None):
    """Quader als eigenes Objekt; bei boden=True liegt die Unterseite auf ort.z."""
    bm = bmesh.new()
    bm_box(bm, groesse, (0.0, 0.0, groesse[2] / 2 if boden else 0.0))
    o = mesh_aus_bmesh(name, bm, sammlung, eltern, [mat] if mat else [])
    o.location = ort
    o.rotation_euler = (0.0, 0.0, rot_z)
    return o


def boxen_objekt(name, liste, sammlung, eltern, mat):
    """Viele Quader in einem Objekt. liste: (groesse, mitte) oder (groesse, mitte, rot)."""
    bm = bmesh.new()
    for eintrag in liste:
        bm_box(bm, *eintrag)
    return mesh_aus_bmesh(name, bm, sammlung, eltern, [mat])


def speichern():
    if not bpy.data.filepath:
        bpy.ops.wm.save_as_mainfile(filepath=pfad("garten.blend"))
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
    return bpy.data.filepath


def view3d_kontext():
    for fenster in bpy.context.window_manager.windows:
        for bereich in fenster.screen.areas:
            if bereich.type == "VIEW_3D":
                region = next(r for r in bereich.regions if r.type == "WINDOW")
                return dict(window=fenster, area=bereich, region=region)
    raise RuntimeError("Kein 3D-Viewport gefunden")


def gn_kennung(gruppe, name):
    for item in gruppe.interface.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and item.in_out == "INPUT" and item.name == name:
            return item.identifier
    raise KeyError(name)


def gn_setze(mod, name, wert):
    mod[gn_kennung(mod.node_group, name)] = wert


def treiber_modus(ziel, datenpfad, ausdruck):
    """Treiber, der von Steuerung['modus'] abhängt; im Ausdruck heißt der Wert m."""
    ziel.driver_remove(datenpfad)
    fc = ziel.driver_add(datenpfad)
    d = fc.driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "m"
    v.type = "SINGLE_PROP"
    v.targets[0].id_type = "OBJECT"
    v.targets[0].id = bpy.data.objects["Steuerung"]
    v.targets[0].data_path = '["modus"]'
    d.expression = ausdruck
    return fc


def modus_setzen(wert):
    bpy.data.objects["Steuerung"]["modus"] = float(wert)
    sc = bpy.context.scene
    sc.frame_set(sc.frame_current)
