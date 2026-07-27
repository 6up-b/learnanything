// Morphing Julia-set fractal backdrop — ASCII density rendering. Escape-time
// math runs in a worker; the main thread copies pre-rasterized monospace glyphs
// from a palette-aware atlas into one Canvas 2D surface.

import { useEffect, useRef, type CSSProperties } from "react";
import { CHAR_H, CHAR_W, prefersReducedMotion } from "./shared";
import {
  FULLSCREEN_CANVAS_STYLE,
  MonospaceGlyphAtlas,
  readAmberAtlasPalette
} from "./glyphAtlas";
import JuliaWorker from "./julia.worker?worker";

const GLYPHS = ".:-=+*#%@";
const MAX_IT = 28;
const FRAME_MS = 50; // ~20fps — the set morphs slowly, full rAF is wasted heat
const THETA_PER_MS = 0.004 / FRAME_MS;

type JuliaFrameResponse = {
  id: number;
  cols: number;
  rows: number;
  iterations: Uint8Array;
};

export function JuliaBackdrop({ scanlines }: { scanlines: CSSProperties }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { colors, glow } = readAmberAtlasPalette(0.25);
    const reduce = prefersReducedMotion();
    const worker = new JuliaWorker();

    let atlas: MonospaceGlyphAtlas | null = null;
    let cols = 80;
    let rows = 40;
    let width = 0;
    let height = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let raf = 0;
    let resizeRaf = 0;
    let requestId = 0;
    let acceptedRequestId = 0;
    let inFlight = false;
    let lastRequestedAt = -Infinity;
    const thetaOrigin = Math.random() * Math.PI * 2;
    let cells = new Uint16Array(0);
    const codeByIteration = new Uint16Array(MAX_IT + 1);

    function rebuildAtlas() {
      atlas = new MonospaceGlyphAtlas({
        glyphs: GLYPHS,
        colors,
        dpr,
        glowColor: glow,
        glowBlur: 6
      });
      for (let it = 0; it < MAX_IT; it++) {
        let colorIndex = Math.floor((it / MAX_IT) * colors.length);
        if (colorIndex >= colors.length) colorIndex = colors.length - 1;
        let glyphIndex = Math.floor((it / MAX_IT) * GLYPHS.length);
        if (glyphIndex >= GLYPHS.length) glyphIndex = GLYPHS.length - 1;
        codeByIteration[it] = atlas.code(glyphIndex, colorIndex);
      }
      codeByIteration[MAX_IT] = 0;
    }

    function resize() {
      const rect = container!.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      const nextDpr = Math.min(window.devicePixelRatio || 1, 2);
      const dprChanged = nextDpr !== dpr;
      dpr = nextDpr;
      canvas!.width = Math.max(1, Math.floor(width * dpr));
      canvas!.height = Math.max(1, Math.floor(height * dpr));
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx!.imageSmoothingEnabled = false;
      cols = Math.max(20, Math.min(200, Math.floor(width / CHAR_W)));
      rows = Math.max(10, Math.min(110, Math.floor(height / CHAR_H)));
      cells = new Uint16Array(cols * rows);
      if (!atlas || dprChanged) rebuildAtlas();
      acceptedRequestId = ++requestId;
      inFlight = false;
      ctx!.clearRect(0, 0, width, height);
      requestFrame(reduce ? 0 : performance.now());
    }

    function requestFrame(ts: number) {
      if (inFlight) return;
      inFlight = true;
      lastRequestedAt = ts;
      const id = ++requestId;
      acceptedRequestId = id;
      const theta = reduce ? 0 : thetaOrigin + ts * THETA_PER_MS;
      const reSpan = 3.4;
      const imSpan = (reSpan * (rows * CHAR_H)) / Math.max(1, cols * CHAR_W);
      worker.postMessage({
        id,
        cols,
        rows,
        cr: reduce ? -0.7269 : 0.7885 * Math.cos(theta),
        ci: reduce ? 0.1889 : 0.7885 * Math.sin(theta),
        reSpan,
        imSpan
      });
    }

    function renderFrame(iterations: Uint8Array) {
      for (let i = 0; i < iterations.length; i++) cells[i] = codeByIteration[iterations[i]];
      ctx!.clearRect(0, 0, width, height);
      atlas!.draw(ctx!, cells, cols);
    }

    worker.onmessage = (event: MessageEvent<JuliaFrameResponse>) => {
      const response = event.data;
      if (
        response.id !== acceptedRequestId ||
        response.cols !== cols ||
        response.rows !== rows
      ) {
        return;
      }
      inFlight = false;
      renderFrame(response.iterations);
    };

    function frame(ts: number) {
      if (!reduce && !inFlight && ts - lastRequestedAt >= FRAME_MS) requestFrame(ts);
      raf = requestAnimationFrame(frame);
    }

    rebuildAtlas();
    resize();
    const ro = new ResizeObserver(() => {
      cancelAnimationFrame(resizeRaf);
      resizeRaf = requestAnimationFrame(() => resize());
    });
    ro.observe(container);
    if (!reduce) raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      cancelAnimationFrame(resizeRaf);
      ro.disconnect();
      worker.terminate();
    };
  }, []);

  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, overflow: "hidden", background: "var(--shell-bg)" }}>
      <canvas ref={canvasRef} style={FULLSCREEN_CANVAS_STYLE} />
      <div style={scanlines} />
    </div>
  );
}
