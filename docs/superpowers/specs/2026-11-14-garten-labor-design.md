# Garten-Labor – begehbare Forschungswelt für Klasse 7–8 – Design

Stand: 2026-11-14 · Branch `garten-labor` · Original gesichert als Tag `blender-original`

## Ziel

Schülerinnen und Schüler der Klassen 7–8 erkunden am PC oder auf Standard-iPads (9./10. Generation) im Browser
einen Garten mit Haus. Sie sammeln Pflanzen und Tiere eines Lebensraums, untersuchen sie im Labor im Erdgeschoss
(Mikroskop) und halten Ergebnisse auf einem Team-Whiteboard fest. Die Lehrkraft legt Sitzungen an und sieht die
Fortschritte der Teams.

Grundlage ist die vorhandene Blender-Szene. Sie wird für das iPad stark vereinfacht und als Web-3D-Anwendung
ausgeliefert, mit vorberechnetem Licht.

## Gesamtvorhaben und Zuschnitt

| Version | Inhalt |
|---|---|
| **1 – Durchstich (dieses Dokument)** | Garten + Labor begehbar, Lebensraum **Hecke** mit 5 Arten, Sammelbuch, Mikroskop, Team-Whiteboard, Login (Klassencode + Teamname), einfache Lehrerseite, Praxistest auf Schul-iPad |
| 2 | Lebensräume **Wiese/Beete** und **Teich** (neu modelliert) mit ihren Arten |
| 3 | Bestimmungsstation, Forschungsprotokoll, Aquarium/Terrarium, Nahrungsnetz-Wand, Tafel |
| 4 | Gemeinsame **Klassentafel** (live, von der Lehrkraft freigeschaltet) |

Versionen 2–4 bekommen jeweils ein eigenes Design und einen eigenen Plan, sobald Version 1 auf echten iPads trägt.

## Rahmenbedingungen

- **Zielgeräte:** iPad 9./10. Generation (A13/A14) in Safari sowie PCs mit aktuellem Browser.
- **Leistungsziele:**
  - ≥ 30 Bilder/s auf dem iPad
  - ≤ 80 MB Download beim ersten Besuch
  - ≤ 1,5 Mio. Dreiecke gleichzeitig sichtbar
  - ≤ 150 Draw Calls
- **Netz:** Bis zu 30 Geräte laden gleichzeitig über den Schulanschluss. Deshalb wird alles stark komprimiert und das Haus zuerst geladen. Nach dem ersten Besuch bleibt die Welt per Service Worker im Gerätespeicher.
- **Server:** Hetzner, verwaltet mit Coolify (Docker-Deployment, HTTPS über Coolify).
- **Datenschutz:**
  - Keine echten Namen: Teams wählen einen Fantasienamen aus einer Vorschlagsliste.
  - Gespeichert werden nur Sitzung, Team, Funde, Beobachtungen und Whiteboard.
- **Original bleibt unangetastet:**
  - `garten.blend` wird nie verändert. Das Labor entsteht in der Kopie `labor.blend`.
  - Der Stand vor dem Labor ist im Git als Tag `blender-original` markiert.
- **Lizenzen:** Fremdbilder (z. B. Makrofotos) nur mit freier Lizenz, Lizenzliste in `web/inhalte/LIZENZEN.md` und nur nach Freigabe durch die Lehrkraft. Downloads nur nach Freigabe.

## Version 1 im Detail

### Welt

- **Garten:** aus der Blender-Szene übernommen und vereinfacht. Hecke, Birken und Ahorn, Rasen, Beete, Hof, Seitenflügel und Carport; der Teich folgt in Version 2.
- **Haus Erdgeschoss = Forschungslabor:** Die Wohnungseinrichtung wird ersetzt durch:
  - Labortische und einen Mikroskop-Arbeitsplatz
  - eine Whiteboard-Wand
  - Regale mit Sammelgefäßen
  - helle Laborbeleuchtung
- **Obergeschoss:** geschlossen, nicht begehbar.
- **Kollision:** Wände, Möbel, Hecke und Bäume halten auf; auf dem Boden gilt Schwerkraft. Hinein geht es durch die Terrassentür.

### Steuerung

| Gerät | Bewegen | Umschauen | Untersuchen |
|---|---|---|---|
| PC | WASD (+ Shift schneller) | Maus (Pointer Lock) | Fadenkreuz + Klick |
| iPad | virtueller Joystick links | Wischen rechts | direktes Antippen |

Interaktive Objekte schimmern in Reichweite (ca. 2,5 m) leicht.

### Lebensraum Hecke – 5 Arten

| Art | Typ | Verhalten/Ort | Mikroskop-Merkmale (Beispiele) |
|---|---|---|---|
| Hainbuche | Pflanze | Hecke selbst, Blattprobe | Blattadern, Spaltöffnungen, Blattrand |
| Zitronenfalter | Insekt | fliegt entlang der Hecke, setzt sich ab und zu | Schuppen auf dem Flügel, Saugrüssel |
| Siebenpunkt-Marienkäfer | Insekt | krabbelt auf Blättern der Hecke | Deckflügel, Fühler, Beine |
| Blattlaus (Kolonie) | Insekt | sitzt an Trieben, klein und versteckt | Saugrüssel, Siphonen |
| Gartenkreuzspinne | Spinnentier | sitzt im Netz zwischen Zweigen | Spinnwarzen, 8 Beine, Augen |

Die Arten bilden eine Nahrungskette (Hainbuche → Blattlaus → Marienkäfer; Kreuzspinne fängt Fluginsekten). Sie ist Grundlage für Auftrag ③.

Bewegte Tiere sind einfach animiert:
- **Flattern:** Flügelschlag und Bahn entlang eines Pfads mit Pausen.
- **Krabbeln:** Bewegung über die Blattoberfläche.

Ihre Trefferzonen sind großzügig, damit niemand frustriert wird.

### Sammelbuch

- Antippen eines Fundstücks in Reichweite startet eine kurze Animation ins Sammelglas. Danach ist der Eintrag im Sammelbuch.
- **Inhalt eines Eintrags:**
  - Bild, Name und Gruppe (Pflanze/Insekt/Spinnentier)
  - 3 Merkmale, Nahrung, Lebensraum
  - Fundort und Uhrzeit (automatisch)
  - eigene Beobachtungen aus dem Mikroskop
- Das Sammelbuch ist jederzeit über eine Schaltfläche erreichbar.

### Labor: Mikroskop

1. Am Mikroskop-Arbeitsplatz eine Probe aus dem Sammelbuch wählen.
2. Es öffnet sich die Okular-Ansicht: ein rundes Sichtfeld, anfangs unscharf, mit **Fokusregler** zum Scharfstellen und **Vergrößerung** in 2–3 Stufen.
3. Merkmale lassen sich als Punkte antippen und zeigen eine Beschriftung samt kurzer Erklärung.
4. Ein Textfeld „Meine Beobachtung“ speichert ins Sammelbuch.

**Bildquellen:**
- in Blender gerenderte Nahaufnahmen der Modelle, oder
- frei lizenzierte Makro- und Mikroskopfotos (nach Freigabe).

### Labor: Team-Whiteboard

- **Ansicht:** An der Laborwand hängt das Whiteboard des Teams als Bild in der 3D-Welt. Antippen öffnet einen Vollbild-Editor.
- **Werkzeuge im Editor:**
  - Sticker der gesammelten Arten (Bild + Name) zum Hinziehen und Verschieben
  - Stift (3 Farben)
  - Pfeile
  - Textnotizen
  - Radierer
  - Rückgängig
- **Speichern** aktualisiert das Bild an der Wand und auf dem Server.

### Forschungsauftrag (Version 1)

„Wer lebt in der Hecke?“ – als Auftragskarte am Bildschirmrand, mit Haken bei erledigten Teilaufgaben:
1. Sammelt mindestens 4 Bewohner der Hecke.
2. Untersucht 2 davon unter dem Mikroskop und notiert je ein Merkmal.
3. Gestaltet auf dem Whiteboard: Wer frisst wen?

### Anmeldung und Lehrerseite

- **Lehrkraft:**
  - `/lehrer`, Anmeldung mit PIN (aus der Server-Konfiguration).
  - Sitzung anlegen, z. B. „7b – Hecke“; der Server erzeugt einen Code wie `BIO-7B-K4`.
- **Live-Übersicht je Team:**
  - Fortschritt der drei Teilaufgaben
  - Funde (x/5) und Mikroskop-Beobachtungen
  - Whiteboard-Vorschau, groß anzeigen, als PNG herunterladen
  - Sitzung schließen
- **Schüler:** Startseite → Code eingeben → Teamname wählen (Vorschlagsliste, keine echten Namen) → Start im Labor.

### Fehlerbehandlung

- **Server nicht erreichbar:** Alles wird lokal gespeichert (IndexedDB) und später synchronisiert. Ein dezenter Hinweis „offline – wird später gespeichert“ erscheint.
- **Langsames Netz:** Ladebalken; das Haus erscheint zuerst, der Garten wird nachgeladen.
- **Datensicherung:** Der Teamstand wird alle 10 s und bei jeder Aktion automatisch gesichert.
- **Gleiches Team auf zwei Geräten:** Letzter Stand gewinnt beim Whiteboard. Funde werden zusammengeführt (Vereinigungsmenge).

## Architektur

### Ordner auf dem Branch

| Ordner | Inhalt |
|---|---|
| `pipeline/` | Blender-Skripte (Python, `bpy`): Labor einrichten, vereinfachen, Lichtberechnung (Lightmaps), Export |
| `web/` | Three.js-App (Vite-Build, statische Dateien) |
| `web/inhalte/` | Artendaten (JSON), Mikroskopbilder, Sticker, `LIZENZEN.md` |
| `server/` | Flask + Flask-SocketIO + SQLite, Dockerfile für Coolify |
| `docs/` | Design, Pläne, Anleitung für Lehrkräfte |

### Weg von Blender ins Web (`pipeline/`)

1. **Kopieren:** `labor.blend` aus `garten.blend`, einmalig. Danach wird nur noch `labor.blend` verändert.
2. **Labor einrichten:** Wohnungseinrichtung entfernen, Laboreinrichtung bauen (vorhandene `gartenlib`-Muster).
3. **Webfassung erzeugen:**
   - **Gebäude, Boden, Wege, Hardscape:** zu wenigen Objekten zusammenführen, zweite UV-Map, **Lightmap-Bake in Cycles** (RTX 4090) in Texturatlanten (2K).
   - **Hecke:** einfacher Grundkörper + instanzierte Blattkarten (GPU-Instancing, Richtwert ≤ 30 000).
   - **Rasen:** instanzierte Halmbüschel in Kameranähe, sonst Rasentextur.
   - **Bäume:** schlanke Stämme + Blattbüschel-Karten.
   - **Kulisse:** Hecke und Baumring vereinfacht, Horizont aus dem HDRI.
4. **Export:** glTF/GLB mit Meshopt-Kompression, Texturen als KTX2 (Basis Universal), meist 1K.
5. **Budgetprüfung:** Ein Skript prüft Dateigröße, Dreiecke und Anzahl der Objekte gegen die Leistungsziele.

### Web-App (`web/`) – Module

| Modul | Aufgabe |
|---|---|
| `welt` | GLB laden (Haus zuerst), Instancing, Himmel, Service Worker |
| `steuerung` | PC- und Touch-Steuerung, Kollision (Kapsel gegen BVH, `three-mesh-bvh`) |
| `interaktion` | Ziele per Strahl (Fadenkreuz/Antippen), Reichweite, Schimmer-Hinweis |
| `arten` | Artendaten laden, Tierverhalten (fliegen, krabbeln, sitzen) |
| `sammelbuch` | Oberfläche und Daten der Funde |
| `mikroskop` | Okular-Ansicht, Fokus, Vergrößerung, Merkmalspunkte |
| `whiteboard` | Editor (Canvas), Wandtextur |
| `auftrag` | Auftragskarte, Fortschrittslogik |
| `sitzung` | Anmeldung, Speichern/Synchronisieren (REST + Socket.IO), Offline-Puffer |
| `leistung` | fps- und Speicheranzeige (Testmodus) |

Die Oberflächen (Sammelbuch, Mikroskop, Whiteboard-Editor, Auftragskarte) liegen als HTML-Ebenen über der 3D-Ansicht und sind auf Touch und große Schrift ausgelegt.

### Server (`server/`)

- **Flask + Flask-SocketIO, SQLite.**
- **Tabellen:** `sitzung`, `team`, `fund`, `beobachtung`, `whiteboard` (Whiteboard als JSON + PNG).
- **REST:**
  - Sitzung anlegen und schließen (Lehrer-PIN)
  - Team beitreten
  - Stand laden und speichern
  - Whiteboard speichern
  - Lehrerübersicht
- **Socket.IO:** Live-Aktualisierung der Lehrerübersicht.
- **Auslieferung:** Docker-Image, Deployment über Coolify aus einem **privaten** Git-Repository (z. B. GitHub). Die statischen Dateien der Web-App liefert derselbe Container aus.
- Das Repository liegt bisher nur lokal. Ein Remote anlegen und pushen ist Teil des Plans und geschieht nur mit Freigabe.
- Die großen Assets (GLB, KTX2) werden mit eingecheckt, weil sie Teil der ausgelieferten Web-App sind (Budget ≤ 80 MB). `.blend`-Dateien und `assets/polyhaven/` bleiben ausgeschlossen.
- **Konfiguration über Umgebungsvariablen:** Lehrer-PIN, Datenbankpfad.

## Tests und Abnahme

- **Server:** pytest für alle REST-Endpunkte (Sitzung, Beitritt, Speichern, Rechte).
- **Web-App:** vitest für Logik ohne 3D (Auftragsfortschritt, Sammelbuch-Zusammenführung, Offline-Puffer).
- **Pipeline:** Budgetprüfung als Skript, das bei Überschreitung fehlschlägt.
- **Browser:** automatischer Durchlauf im eingebauten Browser (laden, laufen, sammeln, Mikroskop, Whiteboard speichern).
- **Abnahme Version 1:**
  - Ein vollständiger Auftrag lässt sich auf einem **echten iPad 9./10. Generation** mit ≥ 30 Bilder/s durchspielen.
  - Die Lehrerübersicht zeigt den Fortschritt live.
  - Ein Neuladen verliert keine Daten.

## Nicht in Version 1

- Wiese und Teich mit ihren Arten
- Bestimmungsstation, Forschungsprotokoll, Aquarium/Terrarium, Nahrungsnetz-Wand
- Tafel und gemeinsame Klassentafel
- Mehrspieler-Avatare (Teams sehen sich nicht gegenseitig)
- Obergeschoss
- IServ-Anmeldung
- Fotorealismus auf Cycles-Niveau. Die iPad-Fassung ist bewusst vereinfacht; die Blender-Fassung bleibt als Original erhalten.
