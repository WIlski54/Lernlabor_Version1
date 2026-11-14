import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { Kollision, weltGeometrie } from '../src/kollision.js';

/** Rechteck aus zwei Dreiecken, Ecken a, b, c, d (gegen den Uhrzeigersinn). */
function rechteck(a, b, c, d, Typ = Float32Array, normalisiert = false) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Typ([...a, ...b, ...c, ...d]), 3, normalisiert));
  g.setIndex([0, 1, 2, 0, 2, 3]);
  return g;
}

function testWelt() {
  const wurzel = new THREE.Group();
  const waende = new THREE.Mesh(rechteck([1, 0, -5], [1, 0, 5], [1, 3, 5], [1, 3, -5]));
  waende.name = 'Waende';
  const boden = new THREE.Mesh(rechteck([-10, 0, -10], [-10, 0, 10], [10, 0, 10], [10, 0, -10]));
  boden.name = 'Boden';
  wurzel.add(waende, boden);
  return { waende, boden };
}

describe('Kollision', () => {
  it('stoppt vor der Wand (auch bei großem Schritt)', () => {
    const { waende, boden } = testWelt();
    const k = new Kollision(waende, boden);
    const neu = k.schiebe(new THREE.Vector3(0, 0, 0), 2, 0);
    expect(neu.x).toBeLessThanOrEqual(1 - 0.3 + 1e-3);
    expect(neu.x).toBeGreaterThan(0.5);
    expect(neu.z).toBeCloseTo(0);
  });

  it('blockiert Bewegung parallel zur Wand nicht', () => {
    const { waende, boden } = testWelt();
    const k = new Kollision(waende, boden);
    const neu = k.schiebe(new THREE.Vector3(0, 0, 0), 0, 2);
    expect(neu.x).toBeCloseTo(0);
    expect(neu.z).toBeCloseTo(2);
  });

  it('findet den Boden', () => {
    const { waende, boden } = testWelt();
    const k = new Kollision(waende, boden);
    expect(k.bodenHoehe(0, 0, 0)).toBeCloseTo(0);
    expect(k.bodenHoehe(50, 0, 50)).toBeNull();
  });

  it('wandelt quantisierte Positionen (Int16 normalisiert + Knotenskalierung) korrekt um', () => {
    // Wie KHR_mesh_quantization: Werte in [-1, 1] als Int16, Dequantisierung über Knoten-Skalierung 10
    const q = (v) => Math.round(v * 32767);
    const wand = rechteck(
      [q(0.1), 0, q(-0.5)], [q(0.1), 0, q(0.5)], [q(0.1), q(0.3), q(0.5)], [q(0.1), q(0.3), q(-0.5)],
      Int16Array, true,
    );
    const flaeche = rechteck(
      [q(-1), 0, q(-1)], [q(-1), 0, q(1)], [q(1), 0, q(1)], [q(1), 0, q(-1)],
      Int16Array, true,
    );
    const wurzel = new THREE.Group();
    const knoten = new THREE.Group();
    knoten.position.set(0, 0.5, 0); // Eltern-Transform, wird über die Wurzel aktualisiert
    const waende = new THREE.Mesh(wand);
    waende.scale.setScalar(10);
    const boden = new THREE.Mesh(flaeche);
    boden.scale.setScalar(10);
    knoten.add(waende, boden);
    wurzel.add(knoten);

    const g = weltGeometrie(waende);
    expect(g.attributes.position.array).toBeInstanceOf(Float32Array);
    g.computeBoundingBox();
    expect(g.boundingBox.min.x).toBeCloseTo(1, 3);
    expect(g.boundingBox.max.x).toBeCloseTo(1, 3);
    expect(g.boundingBox.min.y).toBeCloseTo(0.5, 3);
    expect(g.boundingBox.max.y).toBeCloseTo(3.5, 3);
    expect(g.boundingBox.min.z).toBeCloseTo(-5, 3);
    expect(g.boundingBox.max.z).toBeCloseTo(5, 3);

    const k = new Kollision(waende, boden);
    expect(k.bodenHoehe(0, 0.5, 0)).toBeCloseTo(0.5, 3);
    const neu = k.schiebe(new THREE.Vector3(0, 0.5, 0), 2, 0);
    expect(neu.x).toBeLessThanOrEqual(1 - 0.3 + 1e-3);
  });
});
