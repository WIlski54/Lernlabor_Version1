// Optimiert alle GLB in public/welt (Meshopt-Geometrie, WebP-Texturen) und prüft das iPad-Budget.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, meshopt, textureCompress } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';

const ORDNER = path.resolve('public/welt');
const BUDGET = { megabyte: 80, dreiecke: 1_500_000 };
const GRAS_DREIECKE = 120_000; // dynamisches Gras in der Web-App (Task 9)
const MAX_TEXTUR = { haus: 4096 };

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
  const doc = await io.read(voll);
  const basis = datei.replace('.glb', '');
  const groesse = MAX_TEXTUR[basis] || 2048;
  await doc.transform(
    dedup(), weld(), prune(),
    textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 85, resize: [groesse, groesse] }),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  await io.write(voll, doc);
  let tris = 0;
  if (datei !== 'kollision.glb') {
    for (const [name, n] of Object.entries(dreieckeJeKnoten(doc))) {
      tris += n * (inst[name] ? inst[name].anzahl : 1);
    }
  }
  summeDreiecke += tris;
  bericht.push({ datei, MB: +(fs.statSync(voll).size / 1e6).toFixed(2), dreiecke: Math.round(tris) });
}
for (const png of fs.readdirSync(ORDNER).filter((d) => d.startsWith('licht_') && d.endsWith('.png'))) {
  fs.rmSync(path.join(ORDNER, png)); // steckt jetzt als WebP in der GLB
}
const mb = fs.readdirSync(ORDNER).reduce((s, d) => s + fs.statSync(path.join(ORDNER, d)).size, 0) / 1e6;
console.table(bericht);
console.log(`GESAMT ${mb.toFixed(1)} MB, ${Math.round(summeDreiecke).toLocaleString('de-DE')} Dreiecke`);
if (mb > BUDGET.megabyte || summeDreiecke > BUDGET.dreiecke) {
  console.error('BUDGET ÜBERSCHRITTEN');
  process.exit(1);
}
console.log('BUDGET OK');
