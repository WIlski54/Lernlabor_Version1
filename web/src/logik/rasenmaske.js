/** Rasenmaske aus dem Blender-Export: 1 Byte je Zelle, Zeilen in +z. */
export function istRasen(m, x, z) {
  const ix = Math.floor((x - m.x0) / m.aufloesung);
  const iz = Math.floor((z - m.z0) / m.aufloesung);
  if (ix < 0 || iz < 0 || ix >= m.breite || iz >= m.hoehe) return false;
  return m.daten[iz * m.breite + ix] > 127;
}

/** Deterministischer Zufall 0…1 je Rasterzelle. */
export function hash2(ix, iz) {
  let h = (Math.imul(ix, 374761393) + Math.imul(iz, 668265263)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Positionen für Grasbüschel im Umkreis, gleichmäßig mit Zufallsversatz, nur auf Rasen. */
export function grasPositionen(m, cx, cz, radius, raster) {
  const erg = [];
  const i0 = Math.floor((cx - radius) / raster);
  const i1 = Math.ceil((cx + radius) / raster);
  const k0 = Math.floor((cz - radius) / raster);
  const k1 = Math.ceil((cz + radius) / raster);
  for (let iz = k0; iz <= k1; iz++) {
    for (let ix = i0; ix <= i1; ix++) {
      const x = (ix + hash2(ix, iz)) * raster;
      const z = (iz + hash2(iz, ix)) * raster;
      if (Math.hypot(x - cx, z - cz) > radius || !istRasen(m, x, z)) continue;
      erg.push({ x, z, r: hash2(ix + 7, iz) * Math.PI * 2, s: 0.8 + 0.4 * hash2(ix, iz + 11) });
    }
  }
  return erg;
}
