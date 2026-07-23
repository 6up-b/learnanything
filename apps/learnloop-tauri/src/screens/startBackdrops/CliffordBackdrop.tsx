// Clifford strange-attractor backdrop — Canvas 2D point cloud. The map
//   x' = sin(a·y) + c·cos(a·x),  y' = sin(b·x) + d·cos(b·y)
// is iterated ~1500 times per frame and plotted as additive dots; the
// parameters drift slowly on incommensurate sine schedules so the attractor
// continuously morphs. A translucent background fade pass leaves ghost trails.

import { useEffect, useRef } from "react";
import { BLACK, mixRgb, prefersReducedMotion, readPaletteColors, rgba } from "./shared";

const POINTS_PER_FRAME = 1500;
const STATIC_POINTS = 40_000;

export function CliffordBackdrop() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const P = readPaletteColors();
    const bgDeep = rgba(mixRgb(P.bg, BLACK, 0.55), 1);
    const dotColors = [rgba(P.amber, 0.6), rgba(P.cyan, 0.45), rgba(P.pink, 0.45)];
    const reduce = prefersReducedMotion();

    let raf = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let x = 0.1;
    let y = 0;

    function params(t: number) {
      return {
        a: -1.4 + 0.25 * Math.sin(t * 7e-5),
        b: 1.6 + 0.2 * Math.sin(t * 8.3e-5 + 2),
        c: 1.0 + 0.2 * Math.sin(t * 6.1e-5 + 4),
        d: 0.7 + 0.2 * Math.sin(t * 9.1e-5 + 1)
      };
    }

    function plotPoints(t: number, count: number) {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      const { a, b, c, d } = params(t);
      // domain [-2.2, 2.2]² with margin, letterboxed to the canvas
      const scale = Math.min(w, h) / 4.8;
      const cx = w / 2;
      const cy = h / 2;
      ctx!.globalCompositeOperation = "lighter";
      ctx!.globalAlpha = 0.5;
      for (let i = 0; i < count; i++) {
        const nx = Math.sin(a * y) + c * Math.cos(a * x);
        const ny = Math.sin(b * x) + d * Math.cos(b * y);
        x = nx;
        y = ny;
        if (!Number.isFinite(x) || !Number.isFinite(y)) {
          x = 0.1;
          y = 0;
          continue;
        }
        if (i % 500 === 0) {
          ctx!.fillStyle = dotColors[Math.floor(i / 500) % dotColors.length];
        }
        ctx!.fillRect(cx + x * scale, cy + y * scale, 1, 1);
      }
      ctx!.globalAlpha = 1;
      ctx!.globalCompositeOperation = "source-over";
    }

    function prime() {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      ctx!.globalCompositeOperation = "source-over";
      ctx!.fillStyle = bgDeep;
      ctx!.fillRect(0, 0, w, h);
    }

    function resize() {
      const rect = canvas!.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas!.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas!.height = Math.max(1, Math.floor(rect.height * dpr));
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      // resizing clears the bitmap — re-prime so trails don't smear on alpha
      prime();
    }
    resize();
    // A drag-resize delivers one observer callback per frame. Regenerating the
    // reduced-motion static frame (STATIC_POINTS iterations) synchronously in
    // each would jank the drag, so collapse them into a single trailing rAF.
    const ro = new ResizeObserver(() => {
      resize();
      if (reduce) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => plotPoints(0, STATIC_POINTS));
      }
    });
    ro.observe(canvas);

    function frame(ts: number) {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      // fade pass: old points sink into the background
      ctx!.globalCompositeOperation = "source-over";
      ctx!.fillStyle = rgba(mixRgb(P.bg, BLACK, 0.55), 0.08);
      ctx!.fillRect(0, 0, w, h);
      plotPoints(ts, POINTS_PER_FRAME);
      raf = requestAnimationFrame(frame);
    }
    if (reduce) {
      plotPoints(0, STATIC_POINTS);
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
