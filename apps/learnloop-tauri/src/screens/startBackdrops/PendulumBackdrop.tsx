// Double-pendulum backdrop — five pendulums released from nearly identical
// initial conditions (offsets of 0.004 rad) so chaotic divergence is the show:
// they shadow each other for a few seconds, then fan out irreversibly. Two
// stacked canvases: a persistent trail layer (faded each frame, tip dots
// accumulate) under an arm layer (fully redrawn). RK4 integration.

import { useEffect, useRef } from "react";
import { BLACK, mixRgb, prefersReducedMotion, readPaletteColors, rgba, type Rgb } from "./shared";

const N_PENDULUMS = 5;
const G = 9.81;
const DT = 1 / 240;
const SUBSTEPS = 4;
const RESEED_MS = 180_000;

type State = { th1: number; th2: number; w1: number; w2: number };

// Exact equal-mass, equal-length (m1=m2=1, l1=l2=1) double-pendulum angular
// accelerations — the standard Lagrangian result, specialized:
//   D    = 2m1 + m2 − m2·cos(2θ1−2θ2)          → 3 − cos(2Δ)
//   θ1'' = [−g(2m1+m2)sinθ1 − m2·g·sin(θ1−2θ2)
//           − 2·sinΔ·m2(ω2²l2 + ω1²l1·cosΔ)] / (l1·D)
//   θ2'' = [2·sinΔ(ω1²l1(m1+m2) + g(m1+m2)cosθ1
//           + ω2²l2·m2·cosΔ)] / (l2·D)
function accel(s: State): [number, number] {
  const { th1, th2, w1, w2 } = s;
  const d = th1 - th2;
  const cd = Math.cos(d);
  const sd = Math.sin(d);
  const den = 3 - Math.cos(2 * d);
  const a1 = (-3 * G * Math.sin(th1) - G * Math.sin(th1 - 2 * th2) - 2 * sd * (w2 * w2 + w1 * w1 * cd)) / den;
  const a2 = (2 * sd * (2 * w1 * w1 + 2 * G * Math.cos(th1) + w2 * w2 * cd)) / den;
  return [a1, a2];
}

function deriv(s: State): State {
  const [a1, a2] = accel(s);
  return { th1: s.w1, th2: s.w2, w1: a1, w2: a2 };
}

function rk4(s: State, dt: number): State {
  const add = (a: State, b: State, k: number): State => ({
    th1: a.th1 + b.th1 * k,
    th2: a.th2 + b.th2 * k,
    w1: a.w1 + b.w1 * k,
    w2: a.w2 + b.w2 * k
  });
  const k1 = deriv(s);
  const k2 = deriv(add(s, k1, dt / 2));
  const k3 = deriv(add(s, k2, dt / 2));
  const k4 = deriv(add(s, k3, dt));
  return {
    th1: s.th1 + (dt / 6) * (k1.th1 + 2 * k2.th1 + 2 * k3.th1 + k4.th1),
    th2: s.th2 + (dt / 6) * (k1.th2 + 2 * k2.th2 + 2 * k3.th2 + k4.th2),
    w1: s.w1 + (dt / 6) * (k1.w1 + 2 * k2.w1 + 2 * k3.w1 + k4.w1),
    w2: s.w2 + (dt / 6) * (k1.w2 + 2 * k2.w2 + 2 * k3.w2 + k4.w2)
  };
}

export function PendulumBackdrop() {
  const trailRef = useRef<HTMLCanvasElement>(null);
  const armRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const trailCanvas = trailRef.current;
    const armCanvas = armRef.current;
    if (!trailCanvas || !armCanvas) return;
    const trailCtx = trailCanvas.getContext("2d");
    const armCtx = armCanvas.getContext("2d");
    if (!trailCtx || !armCtx) return;

    const P = readPaletteColors();
    const bgDeep = mixRgb(P.bg, BLACK, 0.55);
    const accents: Rgb[] = [P.amber, P.green, P.cyan, P.pink, P.red];
    const reduce = prefersReducedMotion();

    let raf = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let pendulums: State[] = [];
    let seededAt = 0;

    function seed() {
      const th1 = (0.6 + Math.random() * 0.3) * Math.PI;
      pendulums = Array.from({ length: N_PENDULUMS }, (_, i) => ({
        th1,
        th2: 0.5 * Math.PI + i * 0.004,
        w1: 0,
        w2: 0
      }));
      seededAt = performance.now();
      primeTrail();
    }

    function primeTrail() {
      const w = trailCanvas!.width / dpr;
      const h = trailCanvas!.height / dpr;
      trailCtx!.globalCompositeOperation = "source-over";
      trailCtx!.fillStyle = rgba(bgDeep, 1);
      trailCtx!.fillRect(0, 0, w, h);
    }

    function geometry() {
      const w = armCanvas!.width / dpr;
      const h = armCanvas!.height / dpr;
      return { w, h, ax: w / 2, ay: h * 0.38, arm: Math.min(w, h) * 0.21 };
    }

    function tipOf(s: State, g: ReturnType<typeof geometry>) {
      const x1 = g.ax + g.arm * Math.sin(s.th1);
      const y1 = g.ay + g.arm * Math.cos(s.th1);
      const x2 = x1 + g.arm * Math.sin(s.th2);
      const y2 = y1 + g.arm * Math.cos(s.th2);
      return { x1, y1, x2, y2 };
    }

    function stepAll(substeps: number) {
      for (let i = 0; i < pendulums.length; i++) {
        let s = pendulums[i];
        for (let k = 0; k < substeps; k++) s = rk4(s, DT);
        pendulums[i] = s;
      }
      // reseed on numerical blow-up or the periodic timer
      const blown = pendulums.some((s) => Math.abs(s.w1) > 60 || Math.abs(s.w2) > 60 || !Number.isFinite(s.th1));
      if (blown || performance.now() - seededAt > RESEED_MS) seed();
    }

    function drawTrails() {
      const g = geometry();
      trailCtx!.globalCompositeOperation = "source-over";
      trailCtx!.fillStyle = rgba(bgDeep, 0.045);
      trailCtx!.fillRect(0, 0, g.w, g.h);
      for (let i = 0; i < pendulums.length; i++) {
        const { x2, y2 } = tipOf(pendulums[i], g);
        trailCtx!.fillStyle = rgba(accents[i % accents.length], 0.5);
        trailCtx!.fillRect(x2 - 1, y2 - 1, 2, 2);
      }
    }

    function drawArms() {
      const g = geometry();
      armCtx!.clearRect(0, 0, g.w, g.h);
      for (let i = 0; i < pendulums.length; i++) {
        const { x1, y1, x2, y2 } = tipOf(pendulums[i], g);
        const c = accents[i % accents.length];
        armCtx!.strokeStyle = rgba(c, 0.3);
        armCtx!.lineWidth = 1;
        armCtx!.beginPath();
        armCtx!.moveTo(g.ax, g.ay);
        armCtx!.lineTo(x1, y1);
        armCtx!.lineTo(x2, y2);
        armCtx!.stroke();
        armCtx!.fillStyle = rgba(c, 0.85);
        armCtx!.beginPath();
        armCtx!.arc(x2, y2, 2.5, 0, Math.PI * 2);
        armCtx!.fill();
        armCtx!.fillStyle = rgba(c, 0.5);
        armCtx!.beginPath();
        armCtx!.arc(x1, y1, 1.8, 0, Math.PI * 2);
        armCtx!.fill();
      }
    }

    function staticFrame() {
      // integrate a stretch plotting trail dots (no fade), then draw arms once
      const g = geometry();
      for (let n = 0; n < 1200; n++) {
        stepAll(1);
        for (let i = 0; i < pendulums.length; i++) {
          const { x2, y2 } = tipOf(pendulums[i], g);
          trailCtx!.fillStyle = rgba(accents[i % accents.length], 0.35);
          trailCtx!.fillRect(x2 - 1, y2 - 1, 2, 2);
        }
      }
      drawArms();
    }

    function resize() {
      const rect = armCanvas!.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      for (const cv of [trailCanvas!, armCanvas!]) {
        cv.width = Math.max(1, Math.floor(rect.width * dpr));
        cv.height = Math.max(1, Math.floor(rect.height * dpr));
      }
      trailCtx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      armCtx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      primeTrail();
    }
    seed();
    resize();
    // Coalesce reduced-motion repaints: staticFrame() runs 1200 RK4 steps per
    // pendulum, far too heavy to redo on every callback of a drag-resize.
    const ro = new ResizeObserver(() => {
      resize();
      if (reduce && pendulums.length) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => staticFrame());
      }
    });
    ro.observe(armCanvas);

    function frame() {
      stepAll(SUBSTEPS);
      drawTrails();
      drawArms();
      raf = requestAnimationFrame(frame);
    }
    if (reduce) {
      staticFrame();
    } else {
      raf = requestAnimationFrame(frame);
    }
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  const style = { position: "absolute", inset: 0, width: "100%", height: "100%", display: "block" } as const;
  return (
    <>
      <canvas ref={trailRef} style={style} />
      <canvas ref={armRef} style={style} />
    </>
  );
}
