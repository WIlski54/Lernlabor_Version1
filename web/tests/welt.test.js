import { describe, it, expect, vi, afterEach } from 'vitest';
import * as THREE from 'three';
import { ladeWelt } from '../src/welt.js';

afterEach(() => vi.unstubAllGlobals());

describe('ladeWelt', () => {
  it('bricht mit der URL ab, wenn eine Datei fehlt (statt HTML als JSON zu lesen)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404 })));
    await expect(ladeWelt(new THREE.Scene(), null, () => {})).rejects.toThrow('/welt/welt.json');
  });
});
