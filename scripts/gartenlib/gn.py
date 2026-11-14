"""Geometry-Nodes-Gruppe GN_Streuen: verteilt Instanzen einer Bibliothek auf Flächen, mit Abstand zu Ausschluss-Geometrie."""
import bpy

from .util import gn_kennung, gn_setze, treiber_modus

NAME = "GN_Streuen"


def _sock(sammlung, name, typ=None):
    for s in sammlung:
        if s.name == name and (typ is None or s.type == typ) and getattr(s, "enabled", True):
            return s
    raise KeyError(f"{name}/{typ}")


def streuer():
    alt = bpy.data.node_groups.get(NAME)
    if alt is not None:
        bpy.data.node_groups.remove(alt)
    ng = bpy.data.node_groups.new(NAME, "GeometryNodeTree")
    i = ng.interface
    i.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    i.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    i.new_socket("Bibliothek", in_out="INPUT", socket_type="NodeSocketCollection")
    i.new_socket("Ausschluss", in_out="INPUT", socket_type="NodeSocketCollection")
    for name, wert, typ in [("Dichte", 10.0, "NodeSocketFloat"), ("Mindestabstand", 0.1, "NodeSocketFloat"),
                            ("Ausschluss_Abstand", 0.05, "NodeSocketFloat"), ("Skala_Min", 0.8, "NodeSocketFloat"),
                            ("Skala_Max", 1.2, "NodeSocketFloat"), ("Neigung", 0.1, "NodeSocketFloat"),
                            ("Seed", 0, "NodeSocketInt"), ("Basis_behalten", False, "NodeSocketBool")]:
        i.new_socket(name, in_out="INPUT", socket_type=typ).default_value = wert

    N, Lk = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    vert = N.new("GeometryNodeDistributePointsOnFaces")
    vert.distribute_method = "POISSON"
    Lk.new(gi.outputs["Geometry"], vert.inputs["Mesh"])
    Lk.new(gi.outputs["Mindestabstand"], vert.inputs["Distance Min"])
    Lk.new(gi.outputs["Dichte"], vert.inputs["Density Max"])
    Lk.new(gi.outputs["Seed"], vert.inputs["Seed"])

    ci_a = N.new("GeometryNodeCollectionInfo")
    ci_a.transform_space = "RELATIVE"
    Lk.new(gi.outputs["Ausschluss"], ci_a.inputs["Collection"])
    real = N.new("GeometryNodeRealizeInstances")
    Lk.new(ci_a.outputs[0], real.inputs[0])
    prox = N.new("GeometryNodeProximity")
    prox.target_element = "FACES"
    Lk.new(real.outputs[0], prox.inputs[0])
    cmp = N.new("FunctionNodeCompare")
    cmp.data_type = "FLOAT"
    cmp.operation = "LESS_THAN"
    Lk.new(_sock(prox.outputs, "Distance"), _sock(cmp.inputs, "A", "VALUE"))
    Lk.new(gi.outputs["Ausschluss_Abstand"], _sock(cmp.inputs, "B", "VALUE"))
    loe = N.new("GeometryNodeDeleteGeometry")
    loe.domain = "POINT"
    Lk.new(vert.outputs["Points"], loe.inputs["Geometry"])
    Lk.new(cmp.outputs["Result"], loe.inputs["Selection"])

    ci_b = N.new("GeometryNodeCollectionInfo")
    ci_b.transform_space = "ORIGINAL"
    ci_b.inputs["Separate Children"].default_value = True
    ci_b.inputs["Reset Children"].default_value = True
    Lk.new(gi.outputs["Bibliothek"], ci_b.inputs["Collection"])

    def zufall(typ, mn, mx, plus):
        r = N.new("FunctionNodeRandomValue")
        r.data_type = typ
        st = "INT" if typ == "INT" else "VALUE"
        for name, w in (("Min", mn), ("Max", mx)):
            s = _sock(r.inputs, name, st)
            if isinstance(w, (int, float)):
                s.default_value = w
            else:
                Lk.new(w, s)
        add = N.new("ShaderNodeMath")
        add.operation = "ADD"
        Lk.new(gi.outputs["Seed"], add.inputs[0])
        add.inputs[1].default_value = plus
        Lk.new(add.outputs[0], r.inputs["Seed"])
        return _sock(r.outputs, "Value", st)

    neg = N.new("ShaderNodeMath")
    neg.operation = "MULTIPLY"
    Lk.new(gi.outputs["Neigung"], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    rot = N.new("ShaderNodeCombineXYZ")
    Lk.new(zufall("FLOAT", neg.outputs[0], gi.outputs["Neigung"], 2), rot.inputs["X"])
    Lk.new(zufall("FLOAT", neg.outputs[0], gi.outputs["Neigung"], 3), rot.inputs["Y"])
    Lk.new(zufall("FLOAT", 0.0, 6.2832, 1), rot.inputs["Z"])

    iop = N.new("GeometryNodeInstanceOnPoints")
    Lk.new(loe.outputs["Geometry"], iop.inputs["Points"])
    Lk.new(ci_b.outputs[0], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    Lk.new(zufall("INT", 0, 9999, 5), iop.inputs["Instance Index"])
    Lk.new(rot.outputs[0], iop.inputs["Rotation"])
    Lk.new(zufall("FLOAT", gi.outputs["Skala_Min"], gi.outputs["Skala_Max"], 4), iop.inputs["Scale"])

    join = N.new("GeometryNodeJoinGeometry")
    Lk.new(gi.outputs["Geometry"], join.inputs[0])
    Lk.new(iop.outputs["Instances"], join.inputs[0])
    sw = N.new("GeometryNodeSwitch")
    sw.input_type = "GEOMETRY"
    Lk.new(gi.outputs["Basis_behalten"], sw.inputs["Switch"])
    Lk.new(iop.outputs["Instances"], sw.inputs["False"])
    Lk.new(join.outputs[0], sw.inputs["True"])
    Lk.new(sw.outputs[0], go.inputs["Geometry"])
    return ng


def anwenden(obj, modname, bibliothek, ausschluss, dichte_lauf, dichte_schoen, abstand=0.1,
             skala=(0.8, 1.2), neigung=0.1, seed=0, basis=False, ausschluss_abstand=0.05):
    ng = bpy.data.node_groups.get(NAME) or streuer()
    mod = obj.modifiers.get(modname) or obj.modifiers.new(modname, "NODES")
    mod.node_group = ng
    gn_setze(mod, "Bibliothek", bpy.data.collections[bibliothek])
    gn_setze(mod, "Ausschluss", bpy.data.collections[ausschluss])
    gn_setze(mod, "Mindestabstand", float(abstand))
    gn_setze(mod, "Ausschluss_Abstand", float(ausschluss_abstand))
    gn_setze(mod, "Skala_Min", float(skala[0]))
    gn_setze(mod, "Skala_Max", float(skala[1]))
    gn_setze(mod, "Neigung", float(neigung))
    gn_setze(mod, "Seed", int(seed))
    gn_setze(mod, "Basis_behalten", bool(basis))
    kennung = gn_kennung(ng, "Dichte")
    treiber_modus(obj, f'modifiers["{modname}"]["{kennung}"]',
                  f"{dichte_lauf} + ({dichte_schoen} - {dichte_lauf}) * m")
    return mod
