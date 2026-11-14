# So läufst du durch den Garten

1. `garten.blend` in Blender öffnen. Die Ansicht steht am Startpunkt auf dem Weg neben dem Seitenflügel
   (Eevee, Modus „Laufen“).
2. Maus über den 3D-Bereich halten und **Shift + `** drücken. Auf der deutschen Tastatur ist das meist
   **Shift + ^** (die Taste links neben der 1). Alternativ geht es über das Menü
   **View › Navigation › Walk Navigation**.
3. Steuerung:

   | Aktion | Taste |
   |---|---|
   | laufen | **W A S D** |
   | umschauen | **Maus** |
   | schneller | **Shift** halten |
   | springen | **V** |
   | Schwerkraft an/aus (fliegen) | **Tab** |
   | hinbeamen | auf ein Ziel schauen, dann **Leertaste** |

4. Beenden:
   - **linke Maustaste**: Position behalten
   - **rechte Maustaste** oder **Esc**: zurück zur Ausgangsposition

Ins Haus kommst du durch die **rechte, offene Hälfte der Terrassentür**.

## Startpunkt zurückholen

Im Tab **Scripting** in die Python-Konsole eingeben:

```python
import sys; sys.path.insert(0, r"D:\KI Projekte\Blender MArtists\scripts")
import gartenlib; gartenlib.lade("lauf").startansicht()
```

Für den Blick ins Haus: `gartenlib.lade("lauf").startansicht("Kamera_Innen")`

## Schnell oder schön

Die Szene hat zwei Modi:

| Modus | Wert | Wirkung |
|---|---|---|
| **Laufen** | 0 | leichte Rasenstücke und Heckenballen, kein Dunst, ca. 30–40 Bilder/s |
| **Schönbild** | 1 | volle Pflanzendichte, feine Blätter, Dunst |

So stellst du um:
- **Laufen:** `gartenlib.lade("lauf").startansicht()` in der Konsole. Damit sind auch die Eevee-Schatten passend eingestellt.
- **Schönbild:** Objekt **Steuerung** auswählen, mit **N** die Seitenleiste öffnen und unter *Item › Properties* den Wert **modus** auf **1** setzen. Danach in der Zeitleiste ein Bild vor- und zurückspringen, damit Blender umschaltet.

## Fotorealistisches Standbild (Cycles)

1. Eine Kamera als aktive Kamera setzen, z. B. *Kamera_Referenz* (Blick wie im Vorbild), *Kamera_Innen* oder *Kamera_Uebersicht*: auswählen und **Ctrl + Numpad 0**.
2. Render-Engine auf **Cycles** stellen, Modus **1**.
3. **F12** drücken. Auf der RTX 4090 dauert ein Bild in 1920 × 1080 rund eine Minute.

## Grenzen

- Wände halten dich beim Laufen nicht auf. Blender beachtet nur den Boden.
- Das Obergeschoss ist nicht eingerichtet und nicht begehbar.
