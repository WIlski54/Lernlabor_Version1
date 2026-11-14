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

const fuellung = document.getElementById('lade-fuellung');
const welt = await ladeWelt(szene, renderer, (a, t) => {
  fuellung.style.width = `${Math.round(a * 100)}%`;
  document.getElementById('lade-text').textContent = t;
});
document.getElementById('lade').hidden = true;

const { konfig } = welt;
const augen = konfig.augenhoehe;
const kollision = new Kollision(welt.kollisionWaende, welt.kollisionBoden);
const gras = new Gras(szene, welt.rasenmaske);
const fuss = new THREE.Vector3(konfig.start.position[0], 0, konfig.start.position[2]);
// Strahl ab Augenhöhe des Startpunkts nach unten (nicht ab 5 m, sonst träfe er ein Obergeschoss/Dach)
fuss.y = kollision.bodenHoehe(fuss.x, konfig.start.position[1], fuss.z, 0) ?? 0;
let fallTempo = 0;

const steuerung = new Steuerung(canvas, document.getElementById('joystick'), document.getElementById('joystick-knauf'), konfig.start.yaw);
const startEl = document.getElementById('start');
document.getElementById('start-hinweis').textContent = steuerung.touch
  ? 'Links ziehen = gehen · rechts wischen = umschauen'
  : 'W A S D = gehen · Maus = umschauen · Shift = schneller · Esc = Pause';
startEl.hidden = false;
document.getElementById('start-knopf').addEventListener('click', () => {
  startEl.hidden = true;
  if (steuerung.touch) document.getElementById('joystick').hidden = false;
  else { canvas.requestPointerLock(); document.getElementById('fadenkreuz').hidden = false; }
});
document.addEventListener('pointerlockchange', () => {
  if (!steuerung.touch && document.pointerLockElement !== canvas) startEl.hidden = false;
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
