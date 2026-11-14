import * as THREE from 'three';
import { ladeWelt } from './welt.js';
import { Leistung } from './leistung.js';

const canvas = document.getElementById('welt');
const ipad = /iPad|Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: !ipad, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, ipad ? 1.0 : 1.5));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = 1.0;

const szene = new THREE.Scene();
const kamera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.05, 400);
addEventListener('resize', () => {
  kamera.aspect = innerWidth / innerHeight;
  kamera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

const fuellung = document.getElementById('lade-fuellung');
const welt = await ladeWelt(szene, renderer, (a, t) => {
  fuellung.style.width = `${Math.round(a * 100)}%`;
  document.getElementById('lade-text').textContent = t;
});
document.getElementById('lade').hidden = true;

const start = welt.konfig.start;
kamera.position.set(...start.position);
kamera.rotation.set(0, start.yaw, 0, 'YXZ');

const leistung = new Leistung(document.getElementById('fps'), renderer);
const uhr = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(uhr.getDelta(), 0.05);
  renderer.render(szene, kamera);
  leistung.tick(dt);
});
