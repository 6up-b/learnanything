import { useCallback, useEffect, useRef, useState } from "react";

// Scroll-wheel zoom for the SVG wireframe views (knowledge well, terrain).
//
// Deliberately self-contained so it can be tuned or ripped out in one place:
//   * every knob lives in SCROLL_ZOOM below — set `enabled: false` to disable
//     the whole behaviour without touching a call site;
//   * a view opts in with three lines (hook call, `ref`, and a `view` that
//     folds in k/panX/panY). Deleting those three lines removes it entirely.
//
// The projection in wire3d is affine about the viewport centre — screen =
// (cx, cy) + scale · v — so magnifying `scale` and translating the centre is
// an exact screen-space zoom. That means we can anchor the zoom under the
// pointer with a closed form and never re-derive geometry: the fabric, the
// beads and the labels all keep their existing 3D pipeline.
//
// The flourish: wheel notches move a *target*, and a rAF loop linearly
// interpolates the live value toward it each frame (in log space for k, so a
// notch feels the same at ×1 and at ×4). Set `animated: false` for a hard snap.

export const SCROLL_ZOOM = {
  /** Master switch — false makes the hook a no-op that always reports ×1. */
  enabled: true,
  /** false ⇒ jump straight to the target (no interpolation flourish). */
  animated: true,
  min: 0.75,
  max: 5,
  /** Zoom per wheel-pixel, exponential: k *= exp(-deltaY · wheelGain). */
  wheelGain: 0.0022,
  /** Fraction of the remaining distance covered per 60fps frame. */
  lerp: 0.16,
  /** Below this relative gap the animation snaps and the rAF loop stops. */
  settleEps: 0.0012,
  /** Zoom toward the cursor rather than the scene centre. */
  anchorToPointer: true,
  /** How much marker glyphs grow with zoom (0 = fixed size, 1 = full scale). */
  markerGain: 0.35,
  /** Pan is clamped to (k − 1) · contentRadius · panLeash, so ×1 is centred. */
  panLeash: 1,
  /** Readout: fully lit for `holdMs`, then fades over `fadeMs`. */
  holdMs: 900,
  fadeMs: 700,
  /** Residual opacity of the readout while zoomed but idle. */
  restOpacity: 0.32
};

export interface ScrollZoomOptions {
  /** viewBox width of the target <svg> — maps client px to viewBox units. */
  viewWidth: number;
  /** viewBox-space scene centre (the point that is fixed at ×1). */
  centerX: number;
  centerY: number;
  /** Approximate on-screen radius of the scene at ×1; leashes the pan. */
  contentRadius: number;
  /** Fired on every wheel notch — the well uses it to pause the idle drift. */
  onInteract?: () => void;
  /** Per-view override of SCROLL_ZOOM.enabled. */
  enabled?: boolean;
}

export interface ScrollZoom {
  /** Callback ref for the <svg>; attaches a non-passive wheel listener. */
  ref: (el: SVGSVGElement | null) => void;
  /** Live magnification (multiply the viewport `scale` by this). */
  k: number;
  /** Live viewport-centre offset in viewBox units. */
  panX: number;
  panY: number;
  /** Suggested multiplier for marker glyph sizes. */
  markerScale: number;
  /** True once the view is off its resting ×1 framing. */
  zoomed: boolean;
  /** 0..1 opacity for a transient zoom readout. */
  readout: number;
  /** Multiply the zoom, optionally anchored at a viewBox point (else centre). */
  zoomBy: (factor: number, anchorX?: number, anchorY?: number) => void;
  /** Ease back to ×1, centred. */
  reset: () => void;
}

interface Frame {
  k: number;
  panX: number;
  panY: number;
}

const REST: Frame = { k: 1, panX: 0, panY: 0 };
const clamp = (value: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, value));

export function useScrollZoom(options: ScrollZoomOptions): ScrollZoom {
  const enabled = options.enabled ?? SCROLL_ZOOM.enabled;
  const opts = useRef(options);
  opts.current = options;

  const [frame, setFrame] = useState<Frame>(REST);
  const [readout, setReadout] = useState(0);
  const live = useRef<Frame>(REST);
  const target = useRef<Frame>(REST);
  const touchedAt = useRef(-Infinity);
  const raf = useRef(0);
  const element = useRef<SVGSVGElement | null>(null);

  const fadeAt = (now: number) => {
    const age = now - touchedAt.current;
    const fade = age <= SCROLL_ZOOM.holdMs ? 1 : 1 - (age - SCROLL_ZOOM.holdMs) / SCROLL_ZOOM.fadeMs;
    const floor = target.current.k === 1 && live.current.k === 1 ? 0 : SCROLL_ZOOM.restOpacity;
    return clamp(Math.max(fade, floor), 0, 1);
  };

  // Interpolate `live` toward `target` once per frame; park the loop as soon as
  // both the motion and the readout have settled so idle views cost nothing.
  const pump = useCallback(() => {
    if (raf.current) return;
    let prev = performance.now();
    const tick = (now: number) => {
      const dt = Math.min(64, now - prev);
      prev = now;
      const from = live.current;
      const to = target.current;
      const t = SCROLL_ZOOM.animated ? 1 - Math.pow(1 - SCROLL_ZOOM.lerp, dt / 16.667) : 1;
      let next: Frame = {
        k: Math.exp(Math.log(from.k) + (Math.log(to.k) - Math.log(from.k)) * t),
        panX: from.panX + (to.panX - from.panX) * t,
        panY: from.panY + (to.panY - from.panY) * t
      };
      const settled =
        Math.abs(next.k - to.k) <= SCROLL_ZOOM.settleEps * to.k &&
        Math.abs(next.panX - to.panX) <= 0.2 &&
        Math.abs(next.panY - to.panY) <= 0.2;
      if (settled) next = to;
      live.current = next;
      const fade = fadeAt(now);
      const readoutFloor = to.k === 1 && next.k === 1 ? 0 : SCROLL_ZOOM.restOpacity;
      const readoutSettled = Math.abs(fade - readoutFloor) <= 0.001;
      setFrame(next);
      setReadout(fade);
      // A zoomed view deliberately keeps a faint resting readout. Its non-zero
      // opacity is static UI, not unfinished animation; using `fade > 0` here
      // kept this loop alive forever after the camera had stopped moving.
      raf.current = !settled || !readoutSettled ? requestAnimationFrame(tick) : 0;
    };
    raf.current = requestAnimationFrame(tick);
  }, []);

  const aim = useCallback(
    (next: Frame) => {
      target.current = next;
      touchedAt.current = performance.now();
      pump();
    },
    [pump]
  );

  const reset = useCallback(() => {
    if (target.current.k === 1 && target.current.panX === 0 && target.current.panY === 0) return;
    aim(REST);
  }, [aim]);

  // Scale by `factor` while holding the viewBox point (ax, ay) still:
  //   screen = centre + pan + k·v   ⇒   pan' = (a − centre)(1 − f) + f·pan
  const zoomBy = useCallback(
    (factor: number, ax?: number, ay?: number) => {
      const cfg = opts.current;
      const previous = target.current;
      const k = clamp(previous.k * factor, SCROLL_ZOOM.min, SCROLL_ZOOM.max);
      const f = k / previous.k;
      const anchorX = ax ?? cfg.centerX;
      const anchorY = ay ?? cfg.centerY;
      const leash = Math.max(0, k - 1) * cfg.contentRadius * SCROLL_ZOOM.panLeash;
      cfg.onInteract?.();
      aim({
        k,
        panX: clamp((anchorX - cfg.centerX) * (1 - f) + f * previous.panX, -leash, leash),
        panY: clamp((anchorY - cfg.centerY) * (1 - f) + f * previous.panY, -leash, leash)
      });
    },
    [aim]
  );

  // Wheel handling lives on a native, non-passive listener: React routes wheel
  // through a passive root listener, where preventDefault() is a no-op and the
  // surrounding scroll pane would eat the gesture. Trackpad pinch arrives here
  // as ctrlKey+wheel and is treated as an ordinary zoom, which is what we want.
  const onWheel = useRef((event: WheelEvent) => {
    const el = element.current;
    if (!el || event.deltaY === 0) return;
    event.preventDefault();
    const rect = el.getBoundingClientRect();
    if (rect.width <= 0) return;
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? rect.height : 1;
    const factor = Math.exp(-event.deltaY * unit * SCROLL_ZOOM.wheelGain);
    if (!SCROLL_ZOOM.anchorToPointer) {
      zoomBy(factor);
      return;
    }
    const toViewBox = opts.current.viewWidth / rect.width;
    zoomBy(factor, (event.clientX - rect.left) * toViewBox, (event.clientY - rect.top) * toViewBox);
  });

  // The node lives in state, and the listener is attached by an effect keyed to
  // it. Attaching inside the ref callback instead looks tidier but breaks under
  // StrictMode: React 18 double-invokes effects while calling callback refs
  // once, so a mount-scoped cleanup detaches the listener and nothing puts it
  // back — the wheel silently stops zooming in dev.
  const [node, setNode] = useState<SVGSVGElement | null>(null);
  const ref = useCallback((el: SVGSVGElement | null) => {
    element.current = el;
    setNode(el);
  }, []);

  useEffect(() => {
    if (!node || !enabled) return;
    const listener = (event: WheelEvent) => onWheel.current(event);
    node.addEventListener("wheel", listener, { passive: false });
    return () => node.removeEventListener("wheel", listener);
  }, [node, enabled]);

  useEffect(() => {
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
      raf.current = 0;
    };
  }, []);

  const noop = useCallback(() => {}, []);

  if (!enabled) {
    return { ref, k: 1, panX: 0, panY: 0, markerScale: 1, zoomed: false, readout: 0, zoomBy: noop, reset: noop };
  }

  return {
    ref,
    zoomBy,
    k: frame.k,
    panX: frame.panX,
    panY: frame.panY,
    markerScale: 1 + (frame.k - 1) * SCROLL_ZOOM.markerGain,
    zoomed: Math.abs(frame.k - 1) > 0.005 || frame.panX !== 0 || frame.panY !== 0,
    readout,
    reset
  };
}
