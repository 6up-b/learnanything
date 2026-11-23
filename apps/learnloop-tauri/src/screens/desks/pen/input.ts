// Pen input (spec §10.10 "Input rules"): which pointers draw, the pen's barrel button as an eraser, and the
// samples a stroke keeps. Pure apart from the event objects it reads, so it is tested with plain objects.
//
// - Touch never draws (palm rejection): a touch pointer is ignored, and so is any second pointer while a stroke
//   is being drawn.
// - A pen draws; its first touch while pen mode is off turns pen mode on and already draws.
// - The mouse draws only with "simulate pen" on (a testing aid), and only in pen mode.
// - The barrel button (button 2 or 5) or the eraser end (buttons bit 32) erases: strokes it passes over go.
// - Each sample keeps x, y (client pixels until the layer makes them its own), the time since the stroke began,
//   pressure (0..1; a mouse with its button down reports none, and the Pointer Events rule for it is 0.5), and
//   tilt (-90..90 degrees; 0 when the device reports none).

export interface PointerLike {
  pointerId: number;
  pointerType: string;
  button: number;
  buttons: number;
  clientX: number;
  clientY: number;
  pressure: number;
  tiltX?: number;
  tiltY?: number;
  timeStamp: number;
  getCoalescedEvents?: () => PointerLike[];
}

export interface Sample {
  x: number;
  y: number;
  t: number;
  pressure: number;
  tiltX: number;
  tiltY: number;
}

export interface FinishedStroke {
  pointerType: "pen" | "mouse";
  samples: Sample[];
}

export type DownOutcome =
  /** Not ours: the event goes on as it would without pen mode (touch scrolls, the mouse selects). */
  | { kind: "pass"; turnOn?: false }
  /** A stroke began (`turnOn`: a pen's first touch turned pen mode on). */
  | { kind: "draw"; turnOn: boolean }
  /** The barrel button or the eraser end: the pointer erases until it lifts. */
  | { kind: "erase"; turnOn: boolean };

/** The Pointer Events pressure of a mouse with a button down. */
const MOUSE_PRESSURE = 0.5;
const BARREL_BUTTONS = new Set([2, 5]);
const ERASER_BITS = 32;

function clamp(value: number, low: number, high: number): number {
  return Math.min(high, Math.max(low, value));
}

export class PenInput {
  private active: { pointerId: number; pointerType: "pen" | "mouse"; erase: boolean; start: number; samples: Sample[] } | null = null;

  constructor(private readonly simulate: () => boolean = () => false) {}

  get drawing(): boolean {
    return this.active !== null && !this.active.erase;
  }

  get erasing(): boolean {
    return this.active?.erase ?? false;
  }

  /** A pointer went down. `penOn`: pen mode is on now. */
  down(event: PointerLike, penOn: boolean): DownOutcome {
    if (this.active) return { kind: "pass" };
    const pen = event.pointerType === "pen";
    const mouse = event.pointerType === "mouse" && this.simulate();
    if (!pen && !mouse) return { kind: "pass" };
    if (mouse && !penOn) return { kind: "pass" };
    const turnOn = pen && !penOn;
    const erase = BARREL_BUTTONS.has(event.button) || (event.buttons & ERASER_BITS) !== 0;
    this.active = { pointerId: event.pointerId, pointerType: pen ? "pen" : "mouse", erase, start: event.timeStamp, samples: [] };
    if (!erase) this.active.samples.push(this.sample(event));
    return { kind: erase ? "erase" : "draw", turnOn };
  }

  /** A pointer moved: the samples it adds (its coalesced events, where the platform gives them), or the eraser's
   * positions. Another pointer's moves are ignored. */
  move(event: PointerLike): Sample[] {
    if (!this.active || event.pointerId !== this.active.pointerId) return [];
    const events = event.getCoalescedEvents?.() ?? [];
    const samples = (events.length ? events : [event]).map((each) => this.sample(each));
    if (!this.active.erase) this.active.samples.push(...samples);
    return samples;
  }

  /** The pointer lifted: the stroke drawn (null for an eraser, another pointer, or nothing). */
  up(event: PointerLike): FinishedStroke | null {
    if (!this.active || event.pointerId !== this.active.pointerId) return null;
    const done = this.active;
    this.active = null;
    if (done.erase) return null;
    return { pointerType: done.pointerType, samples: done.samples };
  }

  /** The stroke was interrupted (pointercancel, a paused window): nothing is kept. */
  cancel(): void {
    this.active = null;
  }

  private sample(event: PointerLike): Sample {
    const start = this.active?.start ?? event.timeStamp;
    const reported = Number.isFinite(event.pressure) ? event.pressure : 0;
    const pressure = event.pointerType === "mouse" && reported === 0 ? MOUSE_PRESSURE : clamp(reported, 0, 1);
    return {
      x: event.clientX,
      y: event.clientY,
      t: Math.max(0, event.timeStamp - start),
      pressure,
      tiltX: clamp(Number.isFinite(event.tiltX) ? (event.tiltX as number) : 0, -90, 90),
      tiltY: clamp(Number.isFinite(event.tiltY) ? (event.tiltY as number) : 0, -90, 90),
    };
  }
}
