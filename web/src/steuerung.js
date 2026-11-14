import { joystickVektor } from './logik/joystick.js';

/**
 * PC: WASD + Maus (Pointer Lock), Shift schneller. iPad: Joystick links, Wischen rechts.
 * Maus und Touch sind immer beide aktiv (Touch-PCs, Smartboards mit Stift und Finger).
 */
export class Steuerung {
  constructor(canvas, joystickEl, knaufEl, yaw = 0) {
    this.yaw = yaw;
    this.pitch = 0;
    this.tasten = new Set();
    this.joy = { x: 0, y: 0 };
    this.joyFinger = null;
    this.blickFinger = null;
    // Nur für Hinweistext und ob der Joystick von Anfang an sichtbar ist – schaltet nichts ab
    this.touch = matchMedia('(pointer: coarse)').matches;
    this.joystickEl = joystickEl;
    this.knaufEl = knaufEl;
    addEventListener('keydown', (e) => this.tasten.add(e.code));
    addEventListener('keyup', (e) => this.tasten.delete(e.code));
    // Fenster verlässt den Fokus (Alt+Tab, Tab-Wechsel): keyup kommt nie an → sonst läuft man weiter
    addEventListener('blur', () => this.loslassen());
    document.addEventListener('visibilitychange', () => { if (document.hidden) this.loslassen(); });
    // Ohne Pointer Lock (z. B. eingebettet oder nach Touch-Start): Umschauen durch Ziehen mit der linken Maustaste
    this.ziehen = false;
    canvas.addEventListener('mousedown', (e) => { if (e.button === 0) this.ziehen = true; });
    addEventListener('mouseup', () => { this.ziehen = false; });
    canvas.addEventListener('mousemove', (e) => {
      if (document.pointerLockElement !== canvas && !this.ziehen) return;
      this.drehen(e.movementX * 0.0022, e.movementY * 0.0022);
    });
    canvas.addEventListener('touchstart', (e) => this.touchStart(e), { passive: false });
    canvas.addEventListener('touchmove', (e) => this.touchBewegung(e), { passive: false });
    canvas.addEventListener('touchend', (e) => this.touchEnde(e));
    canvas.addEventListener('touchcancel', (e) => this.touchEnde(e));
  }

  drehen(dx, dy) {
    this.yaw -= dx;
    this.pitch = Math.max(-1.3, Math.min(1.3, this.pitch - dy));
  }

  loslassen() {
    this.tasten.clear();
    this.ziehen = false;
  }

  touchStart(e) {
    e.preventDefault(); // verhindert auch die nachgeahmten Maus-Ereignisse → kein Doppel-Drehen
    this.joystickEl.hidden = false; // Touch auf einem „Maus“-Gerät: Joystick ab jetzt zeigen
    for (const t of e.changedTouches) {
      if (t.clientX < innerWidth * 0.45 && this.joyFinger === null) {
        this.joyFinger = { id: t.identifier, x0: t.clientX, y0: t.clientY };
        Object.assign(this.joystickEl.style, { left: `${t.clientX - 70}px`, top: `${t.clientY - 70}px`, bottom: 'auto' });
      } else if (this.blickFinger === null) {
        this.blickFinger = { id: t.identifier, x: t.clientX, y: t.clientY };
      }
    }
  }

  touchBewegung(e) {
    e.preventDefault();
    for (const t of e.changedTouches) {
      if (this.joyFinger && t.identifier === this.joyFinger.id) {
        const dx = t.clientX - this.joyFinger.x0;
        const dy = t.clientY - this.joyFinger.y0;
        this.joy = joystickVektor(dx, dy, 60);
        this.knaufEl.style.transform = `translate(${this.joy.x * 45}px, ${this.joy.y * 45}px)`;
      } else if (this.blickFinger && t.identifier === this.blickFinger.id) {
        this.drehen((t.clientX - this.blickFinger.x) * 0.005, (t.clientY - this.blickFinger.y) * 0.005);
        this.blickFinger.x = t.clientX;
        this.blickFinger.y = t.clientY;
      }
    }
  }

  touchEnde(e) {
    for (const t of e.changedTouches) {
      if (this.joyFinger && t.identifier === this.joyFinger.id) {
        this.joyFinger = null;
        this.joy = { x: 0, y: 0 };
        this.knaufEl.style.transform = '';
      }
      if (this.blickFinger && t.identifier === this.blickFinger.id) this.blickFinger = null;
    }
  }

  /** {vor, seit, schnell} mit Werten in [-1, 1]. */
  eingabe() {
    const k = this.tasten;
    let vor = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    let seit = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    if (this.joy.x || this.joy.y) { vor = -this.joy.y; seit = this.joy.x; }
    return { vor, seit, schnell: k.has('ShiftLeft') || k.has('ShiftRight') };
  }
}
