// The zoom's one writer (spec §6.3): a requestAnimationFrame loop that moves p and writes each frame's
// transforms and opacities straight onto the elements, never through React, so a frame lays nothing
// out. React lays the page out only at rest: when a zoom begins (nothing moves yet) and in the one
// commit after it ends, whose layout is exactly the zoom's last frame.
import { frameAt, release, settleNow, step, type Camera, type Frame, type Motion, type ZoomItem } from "./engine";
import type { Rect } from "../geometry";

export interface SlotElements {
  box: HTMLElement;
  /** The window's content (absent for a desk never opened: only its card shows). */
  inner: HTMLElement | null;
  card: HTMLElement | null;
}

export interface ZoomPlan {
  base: 0 | 1;
  A: Camera;
  B: Camera;
  items: Array<ZoomItem & { key: string; focus?: boolean }>;
  /** The overview's rings around slots (the selection's amber, its relations' cyan): siblings in the world
   * laid out at the slot's card rect, following the slot's morph and fading in with q. */
  rings?: Array<{ key: string; a: Rect; b: Rect }>;
}

export interface ZoomTargets {
  world: HTMLElement;
  slots: Map<string, SlotElements>;
  rings?: Map<string, HTMLElement>;
  /** Links and desk labels: they fade in late. */
  late: HTMLElement[];
  slivers: HTMLElement[];
  /** Called with each frame's q (0 reading, 1 overview), and with null when the zoom's styles go: what moves
   * in step with the zoom without being one of its slots (the companion easing into its pill). */
  followers?: Array<(q: number | null) => void>;
}

export interface FrameClock {
  request(callback: (now: number) => void): number;
  cancel(handle: number): void;
}

export const ANIMATION_FRAMES: FrameClock = {
  request: (callback) => window.requestAnimationFrame(callback),
  cancel: (handle) => window.cancelAnimationFrame(handle),
};

/** The focused window's edge through the zoom: the reading view's amber edge and shadow fade over the
 * first third, leaving the plain 1 px edge every window has (at q = 0 the reading view's `.focus`). */
export function focusEdge(q: number): string {
  const edge = Math.max(0, 1 - 3 * q);
  return `0 0 0 1px rgba(107, 85, 52, ${edge.toFixed(3)}), 0 0 0 1px #000, 0 10px 40px rgba(0, 0, 0, ${(0.5 * edge).toFixed(3)})`;
}

export function cameraTransform(camera: Camera): string {
  return `translate(${camera.x}px, ${camera.y}px) scale(${camera.s})`;
}

export class ZoomController {
  plan: ZoomPlan | null = null;
  private targets: ZoomTargets | null = null;
  private motion: Motion = { p: 0, v: 0, target: 0, goal: null };
  private handle = 0;
  private last = 0;
  /** Frame times of the running zoom (ms), kept for the harness's trace. */
  readonly frameTimes: number[] = [];
  lastFrame: Frame | null = null;

  constructor(
    private readonly clock: FrameClock,
    /** The zoom reached `goal`: the caller commits the view it names (or nothing, when it is the base). */
    private readonly onEnd: (goal: 0 | 1, base: 0 | 1) => void,
  ) {}

  get active(): boolean {
    return this.plan !== null;
  }

  get progress(): number {
    return this.motion.p;
  }

  /** Where a gesture takes p from. Undecided, the fingers' place; while the spring carries p to a goal,
   * where p is now: a wheel that takes over the spring starts there, never from the old target. */
  get target(): number {
    return this.motion.goal !== null ? this.motion.p : this.motion.target;
  }

  get velocity(): number {
    return this.motion.v;
  }

  begin(plan: ZoomPlan, targets: ZoomTargets): void {
    this.plan = plan;
    this.targets = targets;
    this.motion = { p: plan.base, v: 0, target: plan.base, goal: null };
    this.frameTimes.length = 0;
    for (const item of plan.items) {
      const slot = targets.slots.get(item.key);
      if (!slot) continue;
      slot.box.style.transformOrigin = "0 0";
      if (slot.inner) {
        slot.inner.style.transformOrigin = "0 0";
        // Only what was on screen keeps its content through the zoom; the rest show their card.
        slot.inner.style.visibility = item.live ? "visible" : "hidden";
      }
      if (slot.card) slot.card.style.visibility = "visible";
    }
    for (const ring of targets.rings?.values() ?? []) ring.style.transformOrigin = "0 0";
    this.write(frameAt(plan.base, plan.A, plan.B, plan.items));
  }

  /** The fingers' place (undecided). */
  setTarget(target: number): void {
    if (!this.plan) return;
    this.motion = { ...this.motion, goal: null, target: Math.max(0, Math.min(1, target)) };
    this.run();
  }

  /** Decided: the spring carries p to the goal. */
  go(goal: 0 | 1): void {
    if (!this.plan) return;
    this.motion = { ...this.motion, goal };
    this.run();
  }

  /** The fingers lifted with this velocity. */
  release(): void {
    if (!this.plan || this.motion.goal !== null) return;
    this.go(release(this.plan.base, this.motion.target, this.motion.v));
  }

  /** Settle at once (a key or a pointer press during the zoom). */
  settle(): void {
    if (!this.plan) return;
    this.finish(settleNow(this.plan.base, this.motion));
  }

  /** Drive p directly (the harness; a scrub that needs no chase). */
  setProgress(p: number): void {
    if (!this.plan) return;
    this.motion = { ...this.motion, p, target: p, v: 0, goal: null };
    this.write(frameAt(p, this.plan.A, this.plan.B, this.plan.items));
  }

  /** Remove every style the zoom wrote: the layout is whatever React laid out. */
  clean(): void {
    const targets = this.targets;
    if (targets) {
      for (const slot of targets.slots.values()) {
        slot.box.style.transform = "";
        slot.box.style.transformOrigin = "";
        slot.box.style.opacity = "";
        slot.box.style.boxShadow = "";
        if (slot.inner) {
          slot.inner.style.transform = "";
          slot.inner.style.transformOrigin = "";
          slot.inner.style.opacity = "";
          slot.inner.style.visibility = "";
        }
        if (slot.card) {
          slot.card.style.opacity = "";
          slot.card.style.visibility = "";
        }
      }
      for (const ring of targets.rings?.values() ?? []) {
        ring.style.transform = "";
        ring.style.opacity = "";
      }
      for (const element of targets.late) element.style.opacity = "";
      for (const element of targets.slivers) element.style.opacity = "";
      for (const follow of targets.followers ?? []) follow(null);
    }
    this.clock.cancel(this.handle);
    this.handle = 0;
    this.plan = null;
    this.targets = null;
  }

  private run(): void {
    if (this.handle) return;
    this.last = 0;
    this.handle = this.clock.request((now) => this.tick(now));
  }

  private tick(now: number): void {
    this.handle = 0;
    const plan = this.plan;
    if (!plan) return;
    const dt = this.last ? (now - this.last) / 1000 : 1 / 60;
    this.last = now;
    this.frameTimes.push(now);
    const { motion, arrived } = step(this.motion, dt);
    this.motion = motion;
    this.write(frameAt(motion.p, plan.A, plan.B, plan.items));
    if (motion.goal !== null && arrived) {
      this.finish(motion.goal);
      return;
    }
    if (motion.goal === null && motion.p === motion.target) {
      this.motion = { ...motion, v: 0 };
      return;
    }
    this.handle = this.clock.request((next) => this.tick(next));
  }

  private finish(goal: 0 | 1): void {
    const plan = this.plan;
    if (!plan) return;
    this.clock.cancel(this.handle);
    this.handle = 0;
    // The last frame is exactly the goal's: the commit then changes no pixel.
    this.write(frameAt(goal, plan.A, plan.B, plan.items));
    this.onEnd(goal, plan.base);
  }

  private write(frame: Frame): void {
    const plan = this.plan;
    const targets = this.targets;
    if (!plan || !targets) return;
    this.lastFrame = frame;
    targets.world.style.transform = cameraTransform(frame.camera);
    plan.items.forEach((item, index) => {
      const slot = targets.slots.get(item.key);
      const values = frame.items[index];
      if (!slot || !values) return;
      slot.box.style.transform = `translate(${values.tx}px, ${values.ty}px) scale(${values.sx}, ${values.sy})`;
      if (item.recede) slot.box.style.opacity = String(values.opacity);
      if (item.focus) slot.box.style.boxShadow = focusEdge(frame.q);
      if (slot.inner) {
        slot.inner.style.transform = `scale(${values.innerSx}, ${values.innerSy})`;
        if (item.live) slot.inner.style.opacity = String(values.contentOpacity);
      }
      if (slot.card) slot.card.style.opacity = String(values.cardOpacity);
    });
    for (const ring of plan.rings ?? []) {
      const element = targets.rings?.get(ring.key);
      if (!element) continue;
      const q = frame.q;
      const r = { x: ring.a.x + (ring.b.x - ring.a.x) * q, y: ring.a.y + (ring.b.y - ring.a.y) * q, w: ring.a.w + (ring.b.w - ring.a.w) * q, h: ring.a.h + (ring.b.h - ring.a.h) * q };
      element.style.transform = `translate(${r.x - ring.b.x}px, ${r.y - ring.b.y}px) scale(${r.w / ring.b.w}, ${r.h / ring.b.h})`;
      element.style.opacity = String(q);
    }
    for (const element of targets.late) element.style.opacity = String(frame.lateOpacity);
    for (const element of targets.slivers) element.style.opacity = String(frame.sliverOpacity);
    for (const follow of targets.followers ?? []) follow(frame.q);
  }
}
