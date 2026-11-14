import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

const W = '/welt/';

function laderMit(manager) {
  const l = new GLTFLoader(manager);
  l.setMeshoptDecoder(MeshoptDecoder);
  return l;
}

/** Gebackene Bauteile: unbeleuchtet, Lightmap ×2 (wurde beim Export halbiert). */
function gebacken(wurzel) {
  wurzel.traverse((o) => {
    if (!o.isMesh) return;
    const alt = o.material;
    o.material = new THREE.MeshBasicMaterial({ map: alt.map, color: new THREE.Color(2, 2, 2) });
    alt.dispose();
  });
}

function pflanzenMaterial(alt) {
  return new THREE.MeshLambertMaterial({
    color: alt.color, map: alt.map || null, alphaTest: alt.map ? 0.5 : 0, side: THREE.DoubleSide,
  });
}

/**
 * Instanzen aus <name>.json/.bin (8 float32 je Instanz: Position, Quaternion xyzw, Skalierung).
 * KHR_mesh_quantization legt die Dequantisierung als Knoten-Transform ab – daher wird jede
 * Instanzmatrix mit der Matrix des Meshes relativ zur glTF-Wurzel multipliziert.
 */
async function instanzen(szene, gltf, name) {
  const [index, puffer] = await Promise.all([
    fetch(`${W}${name}.json`).then((r) => r.json()),
    fetch(`${W}${name}.bin`).then((r) => r.arrayBuffer()),
  ]);
  const f = new Float32Array(puffer);
  const m = new THREE.Matrix4();
  const p = new THREE.Vector3();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  const farbe = new THREE.Color();
  gltf.scene.updateMatrixWorld(true); // gltf.scene selbst ist Einheitsmatrix
  for (const [knotenName, { offset, anzahl }] of Object.entries(index)) {
    const knoten = gltf.scene.getObjectByName(knotenName);
    if (!knoten) continue;
    const meshes = [];
    knoten.traverse((o) => { if (o.isMesh) meshes.push(o); });
    for (const mesh of meshes) {
      const basis = mesh.matrixWorld;
      const im = new THREE.InstancedMesh(mesh.geometry, pflanzenMaterial(mesh.material), anzahl);
      for (let i = 0; i < anzahl; i++) {
        const k = (offset + i) * 8;
        p.set(f[k], f[k + 1], f[k + 2]);
        q.set(f[k + 3], f[k + 4], f[k + 5], f[k + 6]);
        s.setScalar(f[k + 7]);
        m.compose(p, q, s).multiply(basis);
        im.setMatrixAt(i, m);
        im.setColorAt(i, farbe.setScalar(0.85 + 0.3 * ((i * 0.618) % 1)));
      }
      im.instanceMatrix.needsUpdate = true;
      if (im.instanceColor) im.instanceColor.needsUpdate = true;
      szene.add(im);
    }
  }
}

/** Lädt die Welt in Etappen (Haus zuerst). fortschritt(anteil 0…1, text). */
export async function ladeWelt(szene, renderer, fortschritt) {
  const manager = new THREE.LoadingManager();
  manager.onProgress = (_u, geladen, gesamt) => fortschritt(geladen / gesamt, 'Lade Welt …');
  const lader = laderMit(manager);
  const glb = (n) => lader.loadAsync(`${W}${n}.glb`);
  const konfig = await fetch(`${W}welt.json`).then((r) => r.json());

  const himmel = await new THREE.TextureLoader(manager).loadAsync(`${W}himmel.jpg`);
  himmel.mapping = THREE.EquirectangularReflectionMapping;
  himmel.colorSpace = THREE.SRGBColorSpace;
  szene.background = himmel;
  const pmrem = new THREE.PMREMGenerator(renderer);
  szene.environment = pmrem.fromEquirectangular(himmel).texture;
  pmrem.dispose();
  szene.fog = new THREE.Fog(0xcfd6d8, 45, 160);

  szene.add(new THREE.HemisphereLight(0xe2ebf2, 0x45552f, 1.6));
  const sonne = new THREE.DirectionalLight(0xfff1df, 1.1);
  sonne.position.set(...konfig.sonne_richtung.map((v) => -v * 50));
  szene.add(sonne);

  // 1. Haus und Labor (Startpunkt) – zuerst sichtbar
  for (const n of ['haus', 'labor']) { const g = await glb(n); gebacken(g.scene); szene.add(g.scene); }
  const glas = await glb('glas');
  glas.scene.traverse((o) => {
    if (o.isMesh) o.material = new THREE.MeshStandardMaterial({ color: 0xe6f2ee, transparent: true, opacity: 0.2, roughness: 0.04, metalness: 0, depthWrite: false });
  });
  szene.add(glas.scene);
  const wb = await glb('whiteboard');
  szene.add(wb.scene);
  const whiteboard = wb.scene.getObjectByName(konfig.whiteboard);
  if (whiteboard) whiteboard.material = new THREE.MeshBasicMaterial({ color: 0xf4f4f2 });
  const kollision = await glb('kollision');

  // 2. Garten
  for (const n of ['boden', 'hof', 'hecke']) { const g = await glb(n); gebacken(g.scene); szene.add(g.scene); }
  const wiese = await glb('wiese');
  wiese.scene.traverse((o) => { if (o.isMesh) o.material = new THREE.MeshLambertMaterial({ color: 0x3f5a22 }); });
  szene.add(wiese.scene);
  const pflanzen = await glb('pflanzen');
  await instanzen(szene, pflanzen, 'pflanzen_instanzen');
  const baeume = await glb('baeume');
  baeume.scene.traverse((o) => { if (o.isMesh) o.material = pflanzenMaterial(o.material); });
  for (const kind of [...baeume.scene.children]) {
    if (kind.name.startsWith('WEBB_')) szene.add(kind); // Gartenbäume einzeln (Transform bleibt erhalten), Kulisse instanziert
  }
  await instanzen(szene, baeume, 'baeume_instanzen');

  const [maskeKopf, maskeDaten] = await Promise.all([
    fetch(`${W}rasenmaske.json`).then((r) => r.json()),
    fetch(`${W}rasenmaske.bin`).then((r) => r.arrayBuffer()),
  ]);
  return {
    konfig, whiteboard,
    kollisionWaende: kollision.scene.getObjectByName('Waende'),
    kollisionBoden: kollision.scene.getObjectByName('Boden'),
    rasenmaske: { ...maskeKopf, daten: new Uint8Array(maskeDaten) },
  };
}
