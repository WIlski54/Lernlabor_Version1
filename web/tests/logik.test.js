import { describe, it, expect } from 'vitest';
import { joystickVektor } from '../src/logik/joystick.js';
import { bewegungsvektor } from '../src/logik/bewegung.js';
import { istRasen, grasPositionen } from '../src/logik/rasenmaske.js';

describe('joystickVektor', () => {
  it('ignoriert kleine Ausschläge (Totzone)', () => {
    expect(joystickVektor(3, 2, 60)).toEqual({ x: 0, y: 0 });
  });
  it('begrenzt auf Länge 1', () => {
    const v = joystickVektor(120, 0, 60);
    expect(v.x).toBeCloseTo(1);
    expect(v.y).toBeCloseTo(0);
  });
  it('liefert Zwischenwerte linear', () => {
    expect(joystickVektor(30, 0, 60).x).toBeCloseTo(0.5);
  });
});

describe('bewegungsvektor', () => {
  it('vorwärts bei Blickrichtung 0 geht nach -z', () => {
    const v = bewegungsvektor(0, 1, 0, 2, 0.5);
    expect(v.x).toBeCloseTo(0);
    expect(v.z).toBeCloseTo(-1);
  });
  it('rechts bei Blickrichtung 0 geht nach +x', () => {
    expect(bewegungsvektor(0, 0, 1, 1, 1).x).toBeCloseTo(1);
  });
  it('Blickrichtung 90° (links) – vorwärts geht nach -x', () => {
    expect(bewegungsvektor(Math.PI / 2, 1, 0, 1, 1).x).toBeCloseTo(-1);
  });
  it('diagonal ist nicht schneller', () => {
    const v = bewegungsvektor(0, 1, 1, 1, 1);
    expect(Math.hypot(v.x, v.z)).toBeCloseTo(1);
  });
});

describe('Rasenmaske', () => {
  const maske = { x0: 0, z0: 0, aufloesung: 1, breite: 4, hoehe: 4,
    daten: Uint8Array.from([255, 255, 0, 0, 255, 255, 0, 0, 255, 255, 255, 255, 0, 0, 0, 0]) };
  it('erkennt Rasen und Nicht-Rasen', () => {
    expect(istRasen(maske, 0.5, 0.5)).toBe(true);
    expect(istRasen(maske, 2.5, 0.5)).toBe(false);
    expect(istRasen(maske, -1, 0)).toBe(false);
  });
  it('setzt Grasbüschel nur auf Rasen und immer gleich', () => {
    const a = grasPositionen(maske, 2, 2, 3, 0.5);
    const b = grasPositionen(maske, 2, 2, 3, 0.5);
    expect(a.length).toBeGreaterThan(0);
    expect(a).toEqual(b);
    for (const p of a) expect(istRasen(maske, p.x, p.z)).toBe(true);
  });
});
