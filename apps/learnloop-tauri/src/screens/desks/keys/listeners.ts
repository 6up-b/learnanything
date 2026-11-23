// DeskShell's listener router (spec §3.6, §5.4): one real listener per event type and phase, whatever
// the number of windows. Each window registers through its own hub (lifecycle.tsx); the router hands
// an event to the windows entitled to it:
//
// - input (keys, pointer and mouse, clipboard, selection): the active window only. A pointer press
//   makes the window under it active before the press is handed on, so a drag that starts in a window
//   is that window's;
// - everything else (resize, blur, focus, message, …): every window that is not paused.
//
// The shell's own handlers (the key router, the bare-Alt tracker) run first through `intercept`: an
// event they take reaches no window.
import type { ListenTarget, ListenerHub } from "../lifecycle";

const INPUT_TYPES = new Set([
  "keydown", "keyup", "keypress",
  "mousedown", "mouseup", "mousemove", "click", "dblclick", "contextmenu",
  "pointerdown", "pointerup", "pointermove", "pointercancel",
  "touchstart", "touchmove", "touchend",
  "copy", "cut", "paste", "selectionchange", "wheel",
]);

const POINTER_PRESS = new Set(["mousedown", "pointerdown", "touchstart"]);

interface Subscription {
  windowId: string;
  target: ListenTarget;
  type: string;
  capture: boolean;
  handler: (event: Event) => void;
}

export interface RouterHooks {
  /** The window that owns input now. */
  activeWindowId(): string | null;
  /** Whether a window is paused (offscreen, hidden, preview): it gets no non-input events. */
  isPaused(windowId: string): boolean;
  /** A pointer press inside a window, before anything is handed on: the shell makes it active. */
  onPointerWindow?(windowId: string, event: Event): void;
  /** The shell's own handling, first; true takes the event from every window. */
  intercept?(type: string, phase: "capture" | "bubble", event: Event): boolean;
}

export const WINDOW_ATTRIBUTE = "data-desk-window";

/** The desk window an event target sits in, if any. */
export function windowOfTarget(target: EventTarget | null): string | null {
  if (!(target instanceof Element)) return null;
  return target.closest(`[${WINDOW_ATTRIBUTE}]`)?.getAttribute(WINDOW_ATTRIBUTE) ?? null;
}

export class DeskListenerRouter {
  private subscriptions: Subscription[] = [];
  private installed = new Map<string, () => void>();
  /** Set while a press has just moved the activity: input goes to that window at once. */
  private pressedWindow: string | null = null;

  constructor(private readonly hooks: RouterHooks) {}

  hubFor(windowId: string): ListenerHub {
    return {
      listen: (target, type, handler, options) => {
        const capture = typeof options === "boolean" ? options : Boolean(options?.capture);
        const subscription: Subscription = { windowId, target, type, capture, handler: handler as (event: Event) => void };
        this.subscriptions.push(subscription);
        this.install(target, type, capture);
        return () => {
          this.subscriptions = this.subscriptions.filter((entry) => entry !== subscription);
        };
      },
    };
  }

  /** The shell listens for a type itself (keys) even when no window does. */
  ensure(target: ListenTarget, type: string): void {
    this.install(target, type, true);
    this.install(target, type, false);
  }

  /** How many real listeners are installed: one per (target, type, phase), never one per window. */
  get realListenerCount(): number {
    return this.installed.size;
  }

  subscriberCount(windowId?: string): number {
    return windowId ? this.subscriptions.filter((entry) => entry.windowId === windowId).length : this.subscriptions.length;
  }

  dispose(): void {
    for (const remove of this.installed.values()) remove();
    this.installed.clear();
    this.subscriptions = [];
  }

  private install(target: ListenTarget, type: string, capture: boolean): void {
    const key = `${target}:${type}:${capture ? "c" : "b"}`;
    if (this.installed.has(key)) return;
    const node: EventTarget = target === "window" ? window : document;
    const listener = (event: Event) => this.dispatch(target, type, capture, event);
    node.addEventListener(type, listener, capture);
    this.installed.set(key, () => node.removeEventListener(type, listener, capture));
  }

  private dispatch(target: ListenTarget, type: string, capture: boolean, event: Event): void {
    const input = INPUT_TYPES.has(type);
    if (capture && POINTER_PRESS.has(type) && target === "window") {
      const pressed = windowOfTarget(event.target);
      this.pressedWindow = pressed;
      if (pressed) this.hooks.onPointerWindow?.(pressed, event);
    }
    if (target === "window" && this.hooks.intercept?.(type, capture ? "capture" : "bubble", event)) return;
    const active = this.pressedWindow && POINTER_PRESS.has(type) ? this.pressedWindow : this.hooks.activeWindowId();
    let stopped = false;
    const original = event.stopImmediatePropagation.bind(event);
    // A subscriber that stops immediate propagation stops the windows after it too, as it would have
    // stopped the other real listeners on the same target.
    event.stopImmediatePropagation = () => {
      stopped = true;
      original();
    };
    try {
      for (const subscription of [...this.subscriptions]) {
        if (stopped) break;
        if (subscription.target !== target || subscription.type !== type || subscription.capture !== capture) continue;
        // Input goes only to the active window, and never to a paused one (a card in the overview, a
        // hidden desk); other events skip paused windows.
        if (input ? subscription.windowId !== active || this.hooks.isPaused(subscription.windowId) : this.hooks.isPaused(subscription.windowId)) continue;
        subscription.handler(event);
      }
    } finally {
      event.stopImmediatePropagation = original;
      if (!capture && POINTER_PRESS.has(type)) this.pressedWindow = null;
    }
  }
}
