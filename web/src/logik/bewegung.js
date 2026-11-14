/** Bewegung in der Ebene: yaw = Blickrichtung (0 = -z), vor/seit ∈ [-1, 1]. Diagonal nicht schneller. */
export function bewegungsvektor(yaw, vor, seit, tempo, dt) {
  const fx = -Math.sin(yaw);
  const fz = -Math.cos(yaw);
  const rx = Math.cos(yaw);
  const rz = -Math.sin(yaw);
  let x = fx * vor + rx * seit;
  let z = fz * vor + rz * seit;
  const l = Math.hypot(x, z);
  if (l > 1) { x /= l; z /= l; }
  return { x: x * tempo * dt, z: z * tempo * dt };
}
