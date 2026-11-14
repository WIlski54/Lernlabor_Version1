/** Auslenkung (Pixel) → Vektor mit Länge ≤ 1; kleine Auslenkungen (Totzone) zählen nicht. */
export function joystickVektor(dx, dy, radius, totzone = 0.12) {
  let x = dx / radius;
  let y = dy / radius;
  const l = Math.hypot(x, y);
  if (l < totzone) return { x: 0, y: 0 };
  if (l > 1) { x /= l; y /= l; }
  return { x, y };
}
