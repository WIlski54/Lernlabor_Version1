import * as THREE from 'three';
import { ladeWelt } from './welt.js';
import { Leistung } from './leistung.js';
import { Steuerung } from './steuerung.js';
import { Kollision } from './kollision.js';
import { Gras } from './gras.js';
import { bewegungsvektor } from './logik/bewegung.js';

const canvas = document.getElementById('welt');
const ipad = /iPad|Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: !ipad, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, ipad ? 1.0 : 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;

const szene = new THREE.Scene();
const kamera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.05, 400);
addEventListener('resize', () => {
  kamera.aspect = innerWidth / innerHeight;
  kamera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

if ('serviceWorker' in navigator && import.meta.env.PROD) navigator.serviceWorker.register('/sw.js');

const ladeEl = document.getElementById('lade');
let abgebrochen = false; // nach einer Fehlermeldung bleibt sie stehen (kein Start-Overlay darüber)

/** Ersetzt den Ladebildschirm durch eine Meldung mit „Neu laden“-Knopf. */
function zeigeMeldung(text) {
  abgebrochen = true;
  if (document.pointerLockElement) document.exitPointerLock();
  for (const id of ['start', 'joystick', 'fadenkreuz']) document.getElementById(id).hidden = true;
  const meldung = document.createElement('div');
  meldung.className = 'meldung';
  meldung.textContent = text;
  const knopf = document.createElement('button');
  knopf.className = 'neu-laden';
  knopf.textContent = 'Neu laden';
  knopf.addEventListener('click', () => location.reload());
  ladeEl.replaceChildren(ladeEl.querySelector('.titel') ?? '', meldung, knopf);
  ladeEl.hidden = false;
}

// iPad: läuft der Grafikspeicher über, verliert Safari den WebGL-Kontext → Meldung statt schwarzem Bild
canvas.addEventListener('webglcontextlost', (e) => {
  e.preventDefault();
  console.error('WebGL-Kontext verloren');
  zeigeMeldung('Grafikspeicher voll – bitte Seite neu laden');
});

const fuellung = document.getElementById('lade-fuellung');
let welt;
try {
  welt = await ladeWelt(szene, renderer, (a, t) => {
    fuellung.style.width = `${Math.round(a * 100)}%`;
    document.getElementById('lade-text').textContent = t;
  });
} catch (fehler) {
  console.error(fehler);
  if (!abgebrochen) zeigeMeldung('Laden fehlgeschlagen – bitte neu laden');
  await new Promise(() => {}); // Modul hier anhalten: ohne Welt gibt es nichts zu starten
}
if (abgebrochen) await new Promise(() => {}); // Kontext ging während des Ladens verloren
ladeEl.hidden = true;

const { konfig } = welt;
const augen = konfig.augenhoehe;
const kollision = new Kollision(welt.kollisionWaende, welt.kollisionBoden);
const gras = new Gras(szene, welt.rasenmaske);
const labor = new URLSearchParams(location.search).has('labor') && konfig.labor_start;
const start = labor ? konfig.labor_start : konfig.start;
const fuss = new THREE.Vector3(start.position[0], 0, start.position[2]);
// Strahl ab Augenhöhe nach unten (nicht ab 5 m, sonst träfe er ein Obergeschoss/Dach);
// im Labor liegt der Startpunkt auf Fußhöhe, der Strahl beginnt 1 m darüber (Decke ≈ 2,75 m)
fuss.y = kollision.bodenHoehe(fuss.x, start.position[1], fuss.z, labor ? 1.0 : 0) ?? 0;
let fallTempo = 0;

const steuerung = new Steuerung(canvas, document.getElementById('joystick'), document.getElementById('joystick-knauf'), start.yaw);
const startEl = document.getElementById('start');
const hinweisEl = document.getElementById('start-hinweis');
const HINWEIS = steuerung.touch
  ? 'Links ziehen = gehen · rechts wischen = umschauen'
  : 'W A S D = gehen · Maus = umschauen · Shift = schneller · Esc = Pause';
hinweisEl.textContent = HINWEIS;
startEl.hidden = false;
// Zeigertyp des letzten Klicks/Antippens – „click“ ist nicht überall ein PointerEvent (ältere Safari),
// und per Tastatur (Enter) ist pointerType leer
let zeigerTyp = steuerung.touch ? 'touch' : 'mouse';
addEventListener('pointerdown', (e) => { zeigerTyp = e.pointerType || zeigerTyp; }, true);
let lockFehler = 0;
document.getElementById('start-knopf').addEventListener('click', (e) => {
  startEl.hidden = true;
  const typ = e.pointerType || zeigerTyp;
  // Pointer Lock nur bei echter Maus – nach Finger/Stift (Touch-PC, Smartboard) bleibt der Zeiger frei
  if (typ === 'mouse') {
    try { canvas.requestPointerLock()?.catch?.(() => {}); } catch { /* Fehler meldet pointerlockerror */ }
    document.getElementById('fadenkreuz').hidden = false;
  }
  if (typ === 'touch' || steuerung.touch) document.getElementById('joystick').hidden = false;
});
document.addEventListener('pointerlockchange', () => {
  if (document.pointerLockElement === canvas) { lockFehler = 0; hinweisEl.textContent = HINWEIS; return; }
  if (!abgebrochen) startEl.hidden = false; // Esc: Pause
});
document.addEventListener('pointerlockerror', () => {
  // z. B. Klick zu kurz nach Esc (Chrome) → Start-Overlay erneut anbieten. Scheitert es gleich wieder
  // (eingebettetes Fenster ohne Erlaubnis), bleibt es beim Umschauen mit gedrückter Maustaste.
  lockFehler += 1;
  if (abgebrochen || lockFehler > 1) return;
  hinweisEl.textContent = 'Mauszeiger konnte nicht eingefangen werden – bitte noch einmal klicken (oder mit gedrückter Maustaste ziehen)';
  startEl.hidden = false;
});

const leistung = new Leistung(document.getElementById('fps'), renderer);
const uhr = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(uhr.getDelta(), 0.05);
  const e = steuerung.eingabe();
  const v = bewegungsvektor(steuerung.yaw, e.vor, e.seit, e.schnell ? 4.0 : 1.8, dt);
  if (v.x || v.z) {
    const neu = kollision.schiebe(fuss, v.x, v.z);
    fuss.x = neu.x;
    fuss.z = neu.z;
  }
  const boden = kollision.bodenHoehe(fuss.x, fuss.y, fuss.z);
  if (boden !== null && boden >= fuss.y - 0.02) { fuss.y = boden; fallTempo = 0; } else {
    fallTempo = Math.min(fallTempo + 9.81 * dt, 12);
    fuss.y = boden !== null ? Math.max(boden, fuss.y - fallTempo * dt) : fuss.y;
  }
  kamera.position.set(fuss.x, fuss.y + augen, fuss.z);
  kamera.rotation.set(steuerung.pitch, steuerung.yaw, 0, 'YXZ');
  gras.aktualisiere(fuss);
  renderer.render(szene, kamera);
  leistung.tick(dt);
});
