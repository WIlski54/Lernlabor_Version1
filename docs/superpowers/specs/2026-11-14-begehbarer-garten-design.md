# Begehbarer fotorealistischer Garten mit Haus – Design

Stand: 2026-11-14 · Blender 5.1.1 · RTX 4090 (24 GB)

## Ziel

Eine Blender-Szene im Stil des Referenzbilds (blenderartists.org, „3D visualization of a landscape project“):
moderner Garten mit Haus, bewölkter Sommertag, nahezu fotorealistisch. Man kann sie im Blender-Viewport
zu Fuß erkunden und von festen Kameras in Cycles-Qualität rendern. Die Szene ist **an das Referenzbild angelehnt,
aber keine Kopie**.

**Erfolgskriterien**
- Ein Cycles-Render aus der Referenzkamera hält im direkten Vergleich mit dem Referenzbild bei Rasen, Gräsern, Materialien und Licht mit. Bei den Bäumen ist ein kleiner Abstand akzeptiert.
- Im Modus „Laufen“ läuft die Walk-Navigation in Eevee mit mindestens 25 fps (Viewport, 1440p).
- Garten und Erdgeschoss innen sind begehbar.

## Rahmenbedingungen

- Nur kostenlose Assets: Poly Haven (CC0) und die Blender-Erweiterung „Sapling Tree Gen“.
- Jeder Download wird vorher mit Dateiliste und Gesamtgröße zur Freigabe vorgelegt.
- Der Bau läuft per Python über das Blender-MCP-Add-on im laufenden Blender.
- Projektordner: `D:\KI Projekte\Blender MArtists\` (Laufwerk C: hat nur 92 GB frei, daher alles auf D:).

## Szeneninhalt

| Bereich | Inhalt |
|---|---|
| Gelände | Grundstück ca. 30 × 40 m, leicht modelliert; außen eine Baumkulisse mit weniger Details |
| Haupthaus | 2-geschossig, ca. 12 × 9 m; EG weißer Putz, OG senkrechte Holzverschalung, flaches Walmdach aus dunklem Blech, Fallrohre, Außenleuchten; überdachter Eingang mit Pfeilern, Holzterrasse |
| Seitenflügel | eingeschossig, rechts im Vordergrund; dunkler Holz-Dachüberstand, große Glastüren |
| Erdgeschoss innen | offener Wohn-/Essbereich mit Küchenblock (ca. 8 × 6 m), Zugang über die Terrassentür, Poly-Haven-Möbel, warme Deckenleuchte |
| Hof | Feuerschale, 4 grüne Lattensessel (per Skript modelliert), dunkle Polygonalplatten, Trittplatten durch den Rasen, Gartenleuchten-Poller |
| Carport | Ziegeldach auf Stützen, hinten rechts |
| Bepflanzung | Rasen; Beete mit Ziergräsern, weißen Stauden, Kiefernpolstern; Birkengruppe; großer Ahorn links vorn |

### Collections

`01_Gelaende`, `02_Architektur`, `03_Innenraum`, `04_Hardscape`, `05_Pflanzen` (Unter-Collections: Rasen,
Graeser, Stauden, Straeucher, Baeume, Kulisse), `06_Licht`, `07_Kameras`, `00_Steuerung`.

### Dateien

- `garten.blend`: Hauptdatei
- `assets/polyhaven/{hdris,textures,models}/`: Downloads, relativ verknüpft
- `scripts/`: die Python-Bausteine je Schritt, damit sie sich wiederholen lassen
- `renders/`: Testrender und Qualitätsproben

## Technik

**Render-Einstellungen**
- Cycles: Gerät OptiX (RTX 4090), adaptive Samples (Standbild bis 1024), OptiX-Denoiser.
- Eevee: Raytracing an, hochaufgelöste Schatten, leichter Volumen-Dunst.
- Farbmanagement: AgX, Look mit etwas höherem Kontrast.

**Licht**
- Bewölktes Poly-Haven-HDRI (4K) als Welt, dazu eine schwache Sonne für weiche Schatten.
- Innen: Licht durch die Fenster (Portale bzw. Flächenlichter) und eine warme Deckenleuchte.

**Materialien**
Poly-Haven-PBR-Texturen (Putz, Holzverschalung, Steinplatten, Dachblech, Ziegel, Holzdeck, Rinde) in 2K–4K.

**Pflanzen**
- **Rasen:** Geometry-Nodes-Halme, die nach einer Dichtekarte verteilt werden, mit Farbvariation.
- **Ziergräser und Stauden:** GN-Horste bzw. -Blüten sowie Poly-Haven-Pflanzenmodelle.
- **Freiflächen:** Auf Wegen, Platten und unter Möbeln wächst nichts. Das regelt eine Abstandsmaske zu den Hardscape-Objekten.
- **Bäume:** Birken und Ahorn mit Sapling erzeugt, dazu Poly-Haven-Rinde und Blatt-Alphatexturen.
- **Kulisse:** Varianten mit weniger Details, als Instanzen verteilt.

**Steuerung „Laufen / Schönbild“**
Das Empty `00_Steuerung/Steuerung` trägt die Eigenschaft `modus` (0 = Laufen, 1 = Schönbild).
Über Treiber regelt sie gemeinsam:
- die Pflanzendichte der GN-Verteiler,
- die Detailstufe der Kulisse,
- die Eevee-Schatten- und Raytracing-Qualität.

**Begehen**
- Eevee-Viewport, Walk-Navigation (Menü View › Navigation › Walk Navigation; Tastenkürzel Shift+` hängt am deutschen Tastaturlayout ggf. auf einer anderen Taste), Schwerkraft an, Augenhöhe 1,70 m.
- Bekannte Grenze: Blenders Walk-Navigation kennt keine Wandkollision, nur den Boden.

**Kameras**
- `Kamera_Referenz`: Perspektive wie im Referenzbild, für Vergleichsrender.
- Weitere Kameras zeigen Terrasse, Innenraum und die Gesamtansicht.

## Ablauf und Prüfpunkte

1. **Einrichtung:** OptiX, AgX, Ordnerstruktur, Collections, Referenzkamera, Hof als Rohbau (Graumodell).
   *Prüfung:* Viewport-Screenshot, Perspektive passend zum Referenzbild.
2. **Materialien und Himmel:** Download der Liste (nach Freigabe), Materialien zuweisen.
   *Prüfung:* Cycles-Testrender des Rohbaus.
3. **Bepflanzung des Hofs:** Rasen, Gräser, Stauden, Sträucher, Bäume.
   *Prüfung:* Testrender.
4. **Qualitätsprobe:** Cycles-Render aus `Kamera_Referenz` in voller Qualität, Vergleich mit dem Referenzbild.
   **Der Nutzer entscheidet, ob es weitergeht.**
5. **Grundstück:** übriges Gelände, Carport, Kulisse.
6. **Erdgeschoss innen:** Raum, Möbel, Licht.
7. **Lauf-Tuning:** fps im Modus „Laufen“ messen, Dichte und Detailstufen anpassen, bis mindestens 25 fps erreicht sind.

Nach jedem Schritt wird `garten.blend` gespeichert. Ich schaue mir jedes Testrender selbst an, bevor ich weitermache.

## Nicht im Umfang

- Obergeschoss innen, Wandkollision, Export in Spiel-Engines oder ins Web.
- Kostenpflichtige Asset-Pakete. Sie sind später nachrüstbar: Die Pflanzen-Collections lassen sich austauschen.
