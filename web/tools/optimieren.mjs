// Optimiert alle GLB in public/welt (Meshopt-Geometrie, WebP-Texturen) und prüft das iPad-Budget.
// Mehrfaches Ausführen ist unschädlich: schon optimierte GLB werden übersprungen. Am Ende wird ein
// Hash über public/welt als Cache-Name in public/sw.js eingetragen (Geräte laden dann neu).
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, meshopt, textureCompress } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const ORDNER = path.resolve('public/welt');
const SERVICE_WORKER = path.resolve('public/sw.js');
const BUDGET = { megabyte: 80, dreiecke: 1_500_000 };
const GRAS_DREIECKE = 120_000; // dynamisches Gras in der Web-App (Task 9)
// iPad-Grafikspeicher: nur das Haus braucht 4K; die Boden-Lightmap ist großflächig und weich → 512 reicht.
const MAX_TEXTUR = { haus: 4096, boden: 512 };

await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});

function dreieckeJeKnoten(doc) {
  const erg = {};
  for (const knoten of doc.getRoot().listNodes()) {
    const mesh = knoten.getMesh();
    if (!mesh) continue;
    let n = 0;
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      n += (idx ? idx.getCount() : prim.getAttribute('POSITION').getCount()) / 3;
    }
    erg[knoten.getName()] = (erg[knoten.getName()] || 0) + n;
  }
  return erg;
}

function instanzen(datei) {
  const p = path.join(ORDNER, datei);
  return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : {};
}

const inst = { ...instanzen('pflanzen_instanzen.json'), ...instanzen('baeume_instanzen.json') };
let summeDreiecke = GRAS_DREIECKE;
const bericht = [];
for (const datei of fs.readdirSync(ORDNER).filter((d) => d.endsWith('.glb'))) {
  const voll = path.join(ORDNER, datei);
  // asset.generator aus dem JSON lesen – io.read() ersetzt ihn durch den eigenen
  const json = await io.readAsJSON(voll);
  const schonOptimiert = (json.json.asset.generator || '').includes('glTF-Transform');
  const doc = await io.readJSON(json);
  const basis = datei.replace('.glb', '');
  const groesse = MAX_TEXTUR[basis] || 2048;
  if (schonOptimiert) {
    console.log(`${datei}: übersprungen (schon optimiert)`);
  } else {
    await doc.transform(
      dedup(), weld(), prune(),
      textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 85, resize: [groesse, groesse] }),
      meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
    );
    await io.write(voll, doc);
  }
  let tris = 0;
  if (datei !== 'kollision.glb') {
    for (const [name, n] of Object.entries(dreieckeJeKnoten(doc))) {
      tris += n * (inst[name] ? inst[name].anzahl : 1);
    }
  }
  summeDreiecke += tris;
  bericht.push({ datei, MB: +(fs.statSync(voll).size / 1e6).toFixed(2), dreiecke: Math.round(tris) });
}
// Lightmaps und Blatttexturen schreibt der Blender-Export daneben; sie stecken jetzt als WebP in den GLB.
for (const png of fs.readdirSync(ORDNER).filter((d) => /^(licht|blatt)_.*\.png$/.test(d))) {
  fs.rmSync(path.join(ORDNER, png));
}
const mb = fs.readdirSync(ORDNER).reduce((s, d) => s + fs.statSync(path.join(ORDNER, d)).size, 0) / 1e6;
console.table(bericht);
console.log(`GESAMT ${mb.toFixed(1)} MB, ${Math.round(summeDreiecke).toLocaleString('de-DE')} Dreiecke`);
if (mb > BUDGET.megabyte || summeDreiecke > BUDGET.dreiecke) {
  console.error('BUDGET ÜBERSCHRITTEN');
  process.exit(1);
}
console.log('BUDGET OK');

// Cache-Name des Service Workers = Inhalt von public/welt → neue Welt, neuer Cache
const hash = crypto.createHash('sha256');
for (const d of fs.readdirSync(ORDNER).sort()) {
  hash.update(`${d}\n`);
  hash.update(fs.readFileSync(path.join(ORDNER, d)));
}
const cacheName = `garten-labor-welt-${hash.digest('hex').slice(0, 10)}`;
const sw = fs.readFileSync(SERVICE_WORKER, 'utf8');
const swNeu = sw.replace(/^const CACHE = '[^']*';/m, `const CACHE = '${cacheName}';`);
if (swNeu === sw && !sw.includes(`'${cacheName}'`)) {
  console.error(`sw.js: Zeile "const CACHE = '…';" nicht gefunden`);
  process.exit(1);
}
fs.writeFileSync(SERVICE_WORKER, swNeu);
console.log(`sw.js: CACHE = '${cacheName}'`);
