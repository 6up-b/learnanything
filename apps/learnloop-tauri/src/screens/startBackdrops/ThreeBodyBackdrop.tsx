// Three-body backdrop — the stable figure-8 choreography (Chenciner–Montgomery)
// integrated with velocity Verlet (symplectic, so the orbit stays bounded for
// hours) plus gravitational softening. The camera slowly rotates so the
// figure-8 precesses across the panel; body trails emerge from the fade layer.

import { useEffect, useRef } from "react";
import { BLACK, mixRgb, prefersReducedMotion, readPaletteColors, rgba, type Rgb } from "./shared";

const DT = 0.008;
const SUBSTEPS = 6;
const SOFTENING2 = 1e-6;
const PERIOD = 6.3259; // figure-8 period at G = m = 1

type Body = { x: number; y: number; vx: number; vy: number; ax: number; ay: number };

function figure8(): Body[] {
  const r1x = 0.97000436;
  const r1y = -0.24308753;
  const v3x = -0.93240737;
  const v3y = -0.86473146;
  return [
    { x: r1x, y: r1y, vx: -v3x / 2, vy: -v3y / 2, ax: 0, ay: 0 },
    { x: -r1x, y: -r1y, vx: -v3x / 2, vy: -v3y / 2, ax: 0, ay: 0 },
    { x: 0, y: 0, vx: v3x, vy: v3y, ax: 0, ay: 0 }
  ];
}

function computeAccels(bodies: Body[]) {
  for (const b of bodies) {
    b.ax = 0;
    b.ay = 0;
  }
  for (let i = 0; i < bodies.length; i++) {
    for (let j = i + 1; j < bodies.length; j++) {
      const dx = bodies[j].x - bodies[i].x;
      const dy = bodies[j].y - bodies[i].y;
      const r2 = dx * dx + dy * dy + SOFTENING2;
      const inv = 1 / (Math.sqrt(r2) * r2); // G = m = 1
      bodies[i].ax += dx * inv;
      bodies[i].ay += dy * inv;
      bodies[j].ax -= dx * inv;
      bodies[j].ay -= dy * inv;
    }
  }
}

function verletStep(bodies: Body[], dt: number) {
  for (const b of bodies) {
    b.vx += 0.5 * dt * b.ax;
    b.vy += 0.5 * dt * b.ay;
    b.x += dt * b.vx;
    b.y += dt * b.vy;
  }
  computeAccels(bodies);
  for (const b of bodies) {
    b.vx += 0.5 * dt * b.ax;
    b.vy += 0.5 * dt * b.ay;
  }
}

export function ThreeBodyBackdrop() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const P = readPaletteColors();
    const bgDeep = mixRgb(P.bg, BLACK, 0.55);
    const accents: Rgb[] = [P.amber, P.cyan, P.pink];
    const reduce = prefersReducedMotion();

    let raf = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let bodies = figure8();
    computeAccels(bodies);
    let steps = 0;
    let viewAngle = 0;

    function prime() {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      ctx!.globalCompositeOperation = "source-over";
      ctx!.fillStyle = rgba(bgDeep, 1);
      ctx!.fillRect(0, 0, w, h);
    }

    function reset() {
      bodies = figure8();
      computeAccels(bodies);
      steps = 0;
      prime();
    }

    function project(b: Body) {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      // world box x ∈ [-1.35, 1.35], y ∈ [-0.6, 0.6] with margin, rotated
      const cosA = Math.cos(viewAngle);
      const sinA = Math.sin(viewAngle);
      const rx = b.x * cosA - b.y * sinA;
      const ry = b.x * sinA + b.y * cosA;
      const scale = Math.min(w / 3.4, h / 2.0);
      return { px: w / 2 + rx * scale, py: h / 2 + ry * scale };
    }

    function drawBodies(trailOnly: boolean) {
      for (let i = 0; i < bodies.length; i++) {
        const { px, py } = project(bodies[i]);
        const c = accents[i];
        if (trailOnly) {
          ctx!.fillStyle = rgba(c, 0.5);
          ctx!.fillRect(px - 1, py - 1, 2, 2);
          continue;
        }
        // three concentric alpha discs: soft glow around a hot core
        for (const [r, a] of [
          [5, 0.15],
          [3, 0.4],
          [1.5, 1]
        ] as const) {
          ctx!.fillStyle = rgba(c, a);
          ctx!.beginPath();
          ctx!.arc(px, py, r, 0, Math.PI * 2);
          ctx!.fill();
        }
      }
    }

    function safetyCheck() {
      // escape → reset (softening keeps energy drift small; the box check is
      // the practical guard)
      for (const b of bodies) {
        if (!Number.isFinite(b.x) || Math.abs(b.x) > 4 || Math.abs(b.y) > 2) {
          reset();
          return;
        }
      }
    }

    function resize() {
      const rect = canvas!.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas!.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas!.height = Math.max(1, Math.floor(rect.height * dpr));
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      prime();
    }

    function staticFrame() {
      // one full period of trail, bodies at their final positions
      bodies = figure8();
      computeAccels(bodies);
      const n = Math.ceil(PERIOD / DT);
      for (let s = 0; s < n; s++) {
        verletStep(bodies, DT);
        if (s % 4 === 0) drawBodies(true);
      }
      drawBodies(false);
    }

    resize();
    // Coalesce reduced-motion repaints: staticFrame() integrates a full orbital
    // period, so redoing it on every callback of a drag-resize would jank.
    const ro = new ResizeObserver(() => {
      resize();
      if (reduce) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => staticFrame());
      }
    });
    ro.observe(canvas);

    function frame() {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      viewAngle += 0.02 / 60; // ~0.02 rad/s at 60fps — a slow precession
      ctx!.globalCompositeOperation = "source-over";
      ctx!.fillStyle = rgba(bgDeep, 0.03);
      ctx!.fillRect(0, 0, w, h);
      for (let s = 0; s < SUBSTEPS; s++) {
        verletStep(bodies, DT);
        steps++;
      }
      if (steps % 600 === 0) safetyCheck();
      drawBodies(false);
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

  return <canvas ref={ref} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", display: "block" }} />;
}
