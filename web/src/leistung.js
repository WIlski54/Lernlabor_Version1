/** Bildratenanzeige (Testmodus: URL-Parameter ?test oder Taste F). */
export class Leistung {
  constructor(element, renderer) {
    this.el = element;
    this.renderer = renderer;
    this.zeiten = [];
    this.sichtbar = new URLSearchParams(location.search).has('test');
    this.el.hidden = !this.sichtbar;
    addEventListener('keydown', (e) => { if (e.code === 'KeyF') { this.sichtbar = !this.sichtbar; this.el.hidden = !this.sichtbar; } });
  }
  tick(dt) {
    this.zeiten.push(dt);
    if (this.zeiten.length < 30) return;
    const mittel = this.zeiten.reduce((a, b) => a + b, 0) / this.zeiten.length;
    this.zeiten.length = 0;
    if (!this.sichtbar) return;
    const info = this.renderer.info;
    this.el.textContent = `${(1 / mittel).toFixed(0)} fps · ${(info.render.triangles / 1000).toFixed(0)}k Dreiecke · ${info.render.calls} Aufrufe`;
  }
}
