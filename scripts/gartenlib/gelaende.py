"""Beetflächen (Mulch) als ebene Polygone knapp über dem Boden."""
import bmesh

from . import layout as L
from .util import leere, material, mesh_aus_bmesh


def _flaeche(punkte):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(punkte, punkte[1:] + punkte[:1])) / 2


def beete():
    leere("01a_Beete")
    m = material("M_Beet", (0.08, 0.06, 0.04), 0.9)
    for name, punkte in L.BEETE.items():
        if _flaeche(punkte) < 0:
            punkte = list(reversed(punkte))
        bm = bmesh.new()
        bm.faces.new([bm.verts.new((x, y, 0.01)) for x, y in punkte])
        mesh_aus_bmesh(name, bm, "01a_Beete", mats=[m])
    return {"beete": list(L.BEETE)}
