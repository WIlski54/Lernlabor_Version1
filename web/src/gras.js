import * as THREE from 'three';
import { grasPositionen } from './logik/rasenmaske.js';

function bueschelGeometrie() {
  const pos = [];
  const farbe = [];
  const unten = [0.05, 0.12, 0.03];
  const oben = [0.17, 0.29, 0.07];
  for (let i = 0; i < 8; i++) {
    const w = (i / 8) * Math.PI * 2 + i * 0.7;
    const r = 0.02 + (i % 3) * 0.012;
    const bx = Math.cos(w) * r;
    const bz = Math.sin(w) * r;
    const h = 0.07 + ((i * 37) % 10) * 0.006;
    const neig = 0.03 + (i % 4) * 0.012;
    const qx = -Math.sin(w) * 0.006;
    const qz = Math.cos(w) * 0.006;
    const sx = bx + Math.cos(w) * neig;
    const sz = bz + Math.sin(w) * neig;
    pos.push(bx - qx, 0, bz - qz, bx + qx, 0, bz + qz, sx, h, sz);
    farbe.push(...unten, ...unten, ...oben);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(farbe, 3));
  g.computeVertexNormals();
  return g;
}

/** Grasbüschel im Umkreis der Spielfigur; werden beim Gehen neu verteilt. */
export class Gras {
  constructor(szene, maske, anzahl = 9000, radius = 13, raster = 0.28) {
    this.maske = maske;
    this.radius = radius;
    this.raster = raster;
    this.mesh = new THREE.InstancedMesh(bueschelGeometrie(),
      new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }), anzahl);
    this.mesh.frustumCulled = false;
    this.mesh.count = 0;
    szene.add(this.mesh);
    this.zentrum = null;
    this.m = new THREE.Matrix4();
    this.q = new THREE.Quaternion();
    this.achse = new THREE.Vector3(0, 1, 0);
  }

  aktualisiere(fuss) {
    if (this.zentrum && Math.hypot(fuss.x - this.zentrum.x, fuss.z - this.zentrum.z) < 1.5) return;
    this.zentrum = { x: fuss.x, z: fuss.z };
    const liste = grasPositionen(this.maske, fuss.x, fuss.z, this.radius, this.raster);
    const n = Math.min(liste.length, this.mesh.instanceMatrix.count);
    for (let i = 0; i < n; i++) {
      const p = liste[i];
      this.q.setFromAxisAngle(this.achse, p.r);
      this.m.compose(new THREE.Vector3(p.x, 0.0, p.z), this.q, new THREE.Vector3(p.s, p.s, p.s));
      this.mesh.setMatrixAt(i, this.m);
    }
    this.mesh.count = n;
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}
