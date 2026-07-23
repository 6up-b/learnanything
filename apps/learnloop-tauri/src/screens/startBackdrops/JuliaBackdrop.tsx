// Morphing Julia-set fractal backdrop — ASCII density rendering. The complex
// parameter c walks the circle c = 0.7885·e^{iθ}, sweeping through connected
// and dust-like Julia sets. Chars by escape iteration count, colored with the
// palette-aware bd-c-amber-* span classes; the non-escaping interior stays
// blank so the hero overlay remains readable.

import { useEffect, useRef, type CSSProperties } from "react";
import { FONT_MONO } from "../../components/term";
import { AMBER_CLASS_RAMP, CHAR_H, CHAR_W, prefersReducedMotion } from "./shared";

const CHARS = " .:-=+*#%@";
const MAX_IT = 28;
const FRAME_MS = 50; // ~20fps — the set morphs slowly, full rAF is wasted heat

export function JuliaBackdrop({ scanlines }: { scanlines: CSSProperties }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const pre = preRef.current;
    if (!container || !pre) return;

    const reduce = prefersReducedMotion();
    let cols = 80;
    let rows = 40;
    let theta = Math.random() * Math.PI * 2;

    function renderFrame(cr: number, ci: number) {
      // Complex-plane window; imaginary extent follows the cell aspect so the
      // set isn't squashed by the non-square glyph grid.
      const RE_SPAN = 3.4;
      const IM_SPAN = (RE_SPAN * (rows * CHAR_H)) / Math.max(1, cols * CHAR_W);
      let html = "";
      let curClass: string | null = null;
      let run = "";
      const flush = () => {
        if (run.length === 0) return;
        html += curClass === null ? run : `<span class="${curClass}">${run}</span>`;
        run = "";
      };
      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          let zr = (x / (cols - 1) - 0.5) * RE_SPAN;
          let zi = (y / (rows - 1) - 0.5) * IM_SPAN;
          let it = 0;
          while (it < MAX_IT) {
            const zr2 = zr * zr;
            const zi2 = zi * zi;
            if (zr2 + zi2 > 4) break;
            zi = 2 * zr * zi + ci;
            zr = zr2 - zi2 + cr;
            it++;
          }
          // Interior (never escaped) stays blank; escape speed picks the glyph.
          const cls =
            it >= MAX_IT
              ? null
              : AMBER_CLASS_RAMP[Math.min(AMBER_CLASS_RAMP.length - 1, Math.floor((it / MAX_IT) * AMBER_CLASS_RAMP.length))];
          const ch =
            it >= MAX_IT ? " " : CHARS[Math.min(CHARS.length - 1, 1 + Math.floor((it / MAX_IT) * (CHARS.length - 1)))];
          if (cls !== curClass) {
            flush();
            curClass = cls;
          }
          run += ch;
        }
        flush();
        html += "\n";
        curClass = null;
      }
      pre!.innerHTML = html;
    }

    function resize() {
      const rect = container!.getBoundingClientRect();
      cols = Math.max(20, Math.min(200, Math.floor(rect.width / CHAR_W)));
      rows = Math.max(10, Math.min(110, Math.floor(rect.height / CHAR_H)));
    }
    resize();
    // Coalesce reduced-motion repaints: a full-grid Julia evaluation is ~10k
    // cells x MAX_IT, too heavy to redo on every callback of a drag-resize.
    const ro = new ResizeObserver(() => {
      resize();
      if (reduce) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => renderFrame(-0.7269, 0.1889));
      }
    });
    ro.observe(container);

    let raf = 0;
    let last = 0;
    function frame(ts: number) {
      if (ts - last < FRAME_MS) {
        raf = requestAnimationFrame(frame);
        return;
      }
      last = ts;
      theta += 0.004;
      renderFrame(0.7885 * Math.cos(theta), 0.7885 * Math.sin(theta));
      raf = requestAnimationFrame(frame);
    }
    if (reduce) {
      renderFrame(-0.7269, 0.1889); // a classic, detailed static Julia set
    } else {
      raf = requestAnimationFrame(frame);
    }
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, overflow: "hidden", background: "var(--shell-bg)" }}>
      <pre
        ref={preRef}
        style={{
          position: "absolute",
          inset: 0,
          margin: 0,
          padding: 0,
          fontFamily: FONT_MONO,
          fontSize: 12,
          lineHeight: "12px",
          letterSpacing: 0,
          whiteSpace: "pre",
          userSelect: "none",
          textShadow: "0 0 6px color-mix(in srgb, var(--amber) 25%, transparent)"
        }}
      />
      <div style={scanlines} />
    </div>
  );
}
