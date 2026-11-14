"""Alle Maße und Positionen in Metern. Ursprung nahe Hofmitte, +Y grob Blickrichtung der Referenzkamera."""

GRUNDSTUECK = (-24.0, -22.0, 16.0, 26.0)  # xmin, ymin, xmax, ymax

HAUS = {
    "mitte": (-10.5, 12.5), "rot_grad": -25.0,
    "breite": 12.0, "tiefe": 9.0, "eg_h": 3.0, "og_h": 2.8,
    "wand": 0.3, "boden": 0.15, "decke": 0.25,
    "dach_ueberstand": 0.6, "dach_neigung": 15.0,
}
# Öffnungen: (seite, versatz entlang der Wand, brüstung über Fußboden innen, breite, höhe, art)
# seite: S = Front (-Y lokal), N, O (+X), W; art: fenster | tuer | tuer_offen (rechte Hälfte Glas, linke offen)
HAUS_EG_OEFFNUNGEN = [
    ("S", -4.2, 0.0, 1.1, 2.3, "tuer"),
    ("S", -1.6, 0.9, 1.8, 1.5, "fenster"),
    ("S", 2.6, 0.0, 2.6, 2.4, "tuer_offen"),
    ("O", 0.0, 0.9, 1.4, 1.5, "fenster"),
    ("W", 1.0, 0.9, 1.4, 1.5, "fenster"),
    ("N", 2.0, 0.9, 2.0, 1.5, "fenster"),
]
HAUS_OG_OEFFNUNGEN = [
    ("S", -3.6, 0.9, 1.4, 1.3, "fenster"),
    ("S", 0.0, 0.9, 1.4, 1.3, "fenster"),
    ("S", 3.6, 0.9, 1.4, 1.3, "fenster"),
    ("O", 0.0, 0.9, 1.2, 1.3, "fenster"),
    ("W", 0.0, 0.9, 1.2, 1.3, "fenster"),
    ("N", -2.0, 0.9, 1.4, 1.3, "fenster"),
]
VORDACH = {"mitte_lokal": (-3.4, -5.7), "breite": 5.0, "tiefe": 2.4, "hoehe": 2.9,
           "neigung": 12.0, "ueberstand": 0.15, "stuetzen_lokal": [(-5.6, -6.6), (-1.2, -6.6)]}
TERRASSE = {"mitte_lokal": (0.0, -6.1), "groesse": (12.0, 3.2, 0.15)}

FLUEGEL = {
    "xmin": 5.0, "xmax": 11.0, "ymin": -18.0, "ymax": 5.0, "h": 3.2, "wand": 0.3,
    "ueberstand": 1.2, "neigung": 12.0,
    "oeffnungen": [
        ("W", -8.0, 0.0, 2.2, 2.5, "fenster"),
        ("W", -3.5, 0.0, 2.2, 2.5, "fenster"),
        ("W", 1.0, 0.0, 2.2, 2.5, "fenster"),
        ("W", 5.5, 0.0, 2.2, 2.5, "fenster"),
        ("N", 0.0, 0.9, 1.6, 1.4, "fenster"),
    ],
}
CARPORT = {"mitte": (6.5, 11.0), "breite": 6.0, "tiefe": 6.5, "hoehe": 2.6, "ueberstand": 0.35, "neigung": 20.0}

HOF = {"mitte": (-2.0, -1.5), "radius": 4.0}
SESSEL_WINKEL = [150.0, 215.0, 290.0, 30.0]
SESSEL_RADIUS = 1.9
WEG_FLUEGEL = (2.6, -18.0, 5.0, -2.0)  # xmin, ymin, xmax, ymax
TRITTPLATTEN = {"start": (2.4, -0.6), "ende": (4.4, 7.2), "anzahl": 9, "groesse": (0.75, 0.45, 0.06)}
POLLER = [(2.3, -6.8), (-6.2, 2.4), (3.0, 1.8), (-5.8, -6.4)]

KAMERA = {"ort": (3.8, -8.6, 1.6), "ziel": (-2.3, 4.0, 2.1), "brennweite": 20.0}

BEETE = {
    "Beet_Hof_West": [(-12.0, -9.0), (-6.5, -7.5), (-6.2, -4.5), (-6.6, -1.0), (-7.5, 1.5), (-11.0, 1.0), (-12.5, -4.0)],
    "Beet_Ahorn": [(-5.0, -8.6), (0.5, -8.6), (1.0, -5.6), (-0.8, -4.9), (-3.0, -5.3), (-5.0, -5.8)],
    "Beet_Vorne": [(1.2, -9.6), (2.5, -9.6), (2.5, -4.0), (1.9, -3.4), (1.3, -5.0)],
    "Beet_Mitte": [(-1.0, 3.0), (2.0, 2.2), (3.4, 3.6), (3.0, 6.2), (0.4, 7.0), (-2.2, 5.4)],
    "Beet_Carport": [(1.5, 8.0), (3.3, 7.6), (3.4, 12.5), (1.2, 12.8)],
    "Beet_Haus": [(-6.2, 6.2), (-3.0, 6.0), (-2.2, 9.8), (-4.6, 10.6)],
}


def _mix(graeser=1.0, stauden=1.0, polster=1.0, kiefer=1.0, boden=1.0):
    """Schichten je Beet: (bibliothek, ziel-collection, dichte_lauf, dichte_schoen, mindestabstand, (skala_min, skala_max))."""
    return [
        ("Bib_Graeser", "05b_Graeser", 0.4 * graeser, 1.0 * graeser, 0.7, (0.8, 1.3)),
        ("Bib_Stauden", "05c_Stauden", 1.0 * stauden, 2.5 * stauden, 0.3, (0.8, 1.2)),
        ("Bib_Polster", "05d_Straeucher", 0.1 * polster, 0.25 * polster, 1.0, (0.6, 1.0)),
        ("Bib_Kiefer", "05d_Straeucher", 0.15 * kiefer, 0.4 * kiefer, 0.9, (0.8, 1.7)),
        ("Bib_Halme", "05b_Graeser", 20.0 * boden, 80.0 * boden, 0.06, (0.8, 1.5)),
    ]


BEPFLANZUNG = {
    "Beet_Hof_West": _mix(1.2, 1.0, 0.8, 0.8),
    "Beet_Ahorn": _mix(0.6, 1.4, 0.6, 1.0),
    "Beet_Vorne": _mix(0.3, 1.2, 0.6, 2.0),
    "Beet_Mitte": _mix(0.8, 1.5, 0.6, 2.0),
    "Beet_Carport": _mix(1.6, 0.6, 0.5, 0.5),
    "Beet_Haus": _mix(1.0, 1.0, 0.8, 0.8),
}

# (name, art, ort, zielhöhe, seed)
BAEUME = [
    ("Baum_Ahorn_1", "ahorn", (-1.8, -6.2), 8.0, 4),
    ("Baum_Birke_1", "birke", (1.0, 4.8), 11.0, 1),
    ("Baum_Birke_2", "birke", (2.0, 10.0), 12.5, 2),
    ("Baum_Birke_3", "birke", (-4.0, 8.0), 10.0, 3),
]
