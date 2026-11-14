import * as THREE from 'three';
import { MeshBVH, acceleratedRaycast } from 'three-mesh-bvh';

THREE.Mesh.prototype.raycast = acceleratedRaycast;

/**
 * Alle Meshes unter 'objekt' als eine Float32-Geometrie in Weltkoordinaten (nur Position + Index).
 * Nötig wegen KHR_mesh_quantization: Positionen sind normalisierte Int16-Werte, die Dequantisierung
 * steckt im Knoten-Transform. applyMatrix4 direkt auf dem Int16-Attribut würde auf [-1, 1] klemmen.
 */
export function weltGeometrie(objekt) {
  let wurzel = objekt;
  while (wurzel.parent) wurzel = wurzel.parent;
  wurzel.updateMatrixWorld(true);

  const meshes = [];
  objekt.traverse((o) => { if (o.isMesh) meshes.push(o); });
  let punkte = 0;
  let indizes = 0;
  for (const m of meshes) {
    const n = m.geometry.attributes.position.count;
    punkte += n;
    indizes += m.geometry.index ? m.geometry.index.count : n;
  }
  const pos = new Float32Array(punkte * 3);
  const idx = punkte > 65535 ? new Uint32Array(indizes) : new Uint16Array(indizes);
  const v = new THREE.Vector3();
  let p0 = 0;
  let i0 = 0;
  for (const m of meshes) {
    const attr = m.geometry.attributes.position;
    for (let i = 0; i < attr.count; i++) {
      // getX/getY/getZ wenden die Normalisierung an
      v.set(attr.getX(i), attr.getY(i), attr.getZ(i)).applyMatrix4(m.matrixWorld);
      pos[(p0 + i) * 3] = v.x;
      pos[(p0 + i) * 3 + 1] = v.y;
      pos[(p0 + i) * 3 + 2] = v.z;
    }
    const index = m.geometry.index;
    if (index) for (let i = 0; i < index.count; i++) idx[i0 + i] = index.getX(i) + p0;
    else for (let i = 0; i < attr.count; i++) idx[i0 + i] = i + p0;
    i0 += index ? index.count : attr.count;
    p0 += attr.count;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  return g;
}

/** Kapsel gegen Wände (seitlich ausweichen), Boden per Strahl nach unten (Stufen bis 0,4 m). */
export class Kollision {
  constructor(waende, boden, radius = 0.3) {
    this.waendeGeo = weltGeometrie(waende);
    this.bvh = new MeshBVH(this.waendeGeo);
    const bodenGeo = weltGeometrie(boden);
    bodenGeo.boundsTree = new MeshBVH(bodenGeo);
    // Eigenes Mesh mit Einheitsmatrix; beidseitig, damit falsch orientierte Flächen nicht durchfallen lassen
    this.boden = new THREE.Mesh(bodenGeo, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
    this.boden.updateMatrixWorld(true);
    this.radius = radius;
    this.strahl = new THREE.Raycaster();
    this.strahl.firstHitOnly = true;
    this.unten = new THREE.Vector3(0, -1, 0);
    this.ursprung = new THREE.Vector3();
    this.seg = new THREE.Line3();
    this.box = new THREE.Box3();
    this.dreieckPunkt = new THREE.Vector3();
    this.kapselPunkt = new THREE.Vector3();
  }

  /**
   * Neue Fußposition nach horizontaler Bewegung um (dx, dz).
   * In Teilschritten von höchstens radius/2, damit schnelle Bewegung nicht durch Wände tunnelt.
   */
  schiebe(fuss, dx, dz) {
    const schritte = Math.max(1, Math.ceil(Math.hypot(dx, dz) / (this.radius * 0.5)));
    let x = fuss.x;
    let z = fuss.z;
    for (let i = 0; i < schritte; i++) {
      this.loese(x + dx / schritte, fuss.y, z + dz / schritte);
      x = this.seg.start.x;
      z = this.seg.start.z;
    }
    return new THREE.Vector3(x, fuss.y, z);
  }

  /** Schiebt die Kapsel an (x, y, z) aus den Wänden heraus; Ergebnis in this.seg. */
  loese(x, y, z) {
    const r = this.radius;
    const seg = this.seg;
    seg.start.set(x, y + 0.45, z);
    seg.end.set(x, y + 1.6, z);
    const box = this.box;
    const dreieckPunkt = this.dreieckPunkt;
    const kapselPunkt = this.kapselPunkt;
    for (let durchgang = 0; durchgang < 3; durchgang++) {
      box.makeEmpty().expandByPoint(seg.start).expandByPoint(seg.end);
      box.min.addScalar(-r);
      box.max.addScalar(r);
      this.bvh.shapecast({
        intersectsBounds: (b) => b.intersectsBox(box),
        intersectsTriangle: (tri) => {
          const abstand = tri.closestPointToSegment(seg, dreieckPunkt, kapselPunkt);
          if (abstand >= r) return false;
          const richtung = kapselPunkt.sub(dreieckPunkt);
          richtung.y = 0;
          if (richtung.lengthSq() < 1e-8) return false;
          richtung.normalize().multiplyScalar(r - abstand);
          seg.start.add(richtung);
          seg.end.add(richtung);
          return false;
        },
      });
    }
  }

  /** Bodenhöhe unter (x, z), höchstens 'stufe' über y; null = kein Boden. */
  bodenHoehe(x, y, z, stufe = 0.4) {
    this.strahl.set(this.ursprung.set(x, y + stufe, z), this.unten);
    this.strahl.far = stufe + 30;
    const t = this.strahl.intersectObject(this.boden, false);
    return t.length ? t[0].point.y : null;
  }
}
