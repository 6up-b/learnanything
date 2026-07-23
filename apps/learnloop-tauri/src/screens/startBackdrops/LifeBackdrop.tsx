// Conway's Game of Life backdrop — ASCII, torus topology (wrap-around edges so
// no dead borders). Cells carry an age so gliders burn bright while stable
// ash cools into the dim amber tiers. Auto-reseeds on stagnation (period-1/2
// oscillation detected via grid hashes), population collapse, or a timer.

import { useEffect, useRef, type CSSProperties } from "react";
import { FONT_MONO } from "../../components/term";
import { CHAR_H, CHAR_W, prefersReducedMotion } from "./shared";

const STEP_MS = 75; // ~13 generations/second
const SOUP_DENSITY = 0.28;
const RESEED_AFTER_MS = 90_000;

// age bucket → glyph + palette class (newborns hottest, ash coolest)
function cellGlyph(age: number): { ch: string; cls: string } {
  if (age <= 2) return { ch: "@", cls: "bd-c-amber-hi" };
  if (age <= 6) return { ch: "#", cls: "bd-c-amber" };
  if (age <= 15) return { ch: "*", cls: "bd-c-amber-mid" };
  return { ch: ":", cls: "bd-c-amber-low" };
}

export function LifeBackdrop({ scanlines }: { scanlines: CSSProperties }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const pre = preRef.current;
    if (!container || !pre) return;

    const reduce = prefersReducedMotion();
    let cols = 80;
    let rows = 40;
    let grid = new Uint8Array(0); // 0 = dead, else age (capped 255)
    let next = new Uint8Array(0);
    let hashes: number[] = []; // rolling recent grid hashes for stagnation detection
    let seededAt = 0;
    let prevCols = 0;
    let prevRows = 0;

    function seed() {
      for (let i = 0; i < grid.length; i++) {
        grid[i] = Math.random() < SOUP_DENSITY ? 1 : 0;
      }
      hashes = [];
      seededAt = performance.now();
    }

    function alloc() {
      const fresh = new Uint8Array(cols * rows);
      if (grid.length > 0 && prevCols > 0) {
        // Preserve the overlapping region so a live colony survives a window
        // drag; newly exposed area gets fresh soup.
        const copyCols = Math.min(prevCols, cols);
        const copyRows = Math.min(prevRows, rows);
        for (let y = 0; y < rows; y++) {
          for (let x = 0; x < cols; x++) {
            fresh[y * cols + x] =
              x < copyCols && y < copyRows
                ? grid[y * prevCols + x]
                : Math.random() < SOUP_DENSITY
                  ? 1
                  : 0;
          }
        }
      } else {
        for (let i = 0; i < fresh.length; i++) fresh[i] = Math.random() < SOUP_DENSITY ? 1 : 0;
      }
      grid = fresh;
      next = new Uint8Array(cols * rows);
      prevCols = cols;
      prevRows = rows;
      hashes = [];
      seededAt = performance.now();
    }

    function gridHash(): number {
      // FNV-1a over aliveness (not age) so pure aging doesn't defeat detection
      let h = 0x811c9dc5;
      for (let i = 0; i < grid.length; i++) {
        h ^= grid[i] > 0 ? 1 : 0;
        h = Math.imul(h, 0x01000193);
      }
      return h >>> 0;
    }

    function step() {
      let population = 0;
      for (let y = 0; y < rows; y++) {
        const up = ((y - 1 + rows) % rows) * cols;
        const mid = y * cols;
        const down = ((y + 1) % rows) * cols;
        for (let x = 0; x < cols; x++) {
          const l = (x - 1 + cols) % cols;
          const r = (x + 1) % cols;
          const n =
            (grid[up + l] > 0 ? 1 : 0) + (grid[up + x] > 0 ? 1 : 0) + (grid[up + r] > 0 ? 1 : 0) +
            (grid[mid + l] > 0 ? 1 : 0) + (grid[mid + r] > 0 ? 1 : 0) +
            (grid[down + l] > 0 ? 1 : 0) + (grid[down + x] > 0 ? 1 : 0) + (grid[down + r] > 0 ? 1 : 0);
          const alive = grid[mid + x] > 0;
          if (alive ? n === 2 || n === 3 : n === 3) {
            next[mid + x] = alive ? Math.min(255, grid[mid + x] + 1) : 1;
            population++;
          } else {
            next[mid + x] = 0;
          }
        }
      }
      const swap = grid;
      grid = next;
      next = swap;

      // reseed on: still-life/blinker lock (hash equals 1 or 2 generations ago),
      // population collapse, or the periodic timer.
      const h = gridHash();
      const stagnant = hashes.length >= 2 && (h === hashes[hashes.length - 1] || h === hashes[hashes.length - 2]);
      hashes.push(h);
      if (hashes.length > 4) hashes.shift();
      const collapsed = population < grid.length * 0.02;
      const expired = performance.now() - seededAt > RESEED_AFTER_MS;
      if (stagnant || collapsed || expired) seed();
    }

    function renderFrame() {
      let html = "";
      let curClass: string | null = null;
      let run = "";
      const flush = () => {
        if (run.length === 0) return;
        html += curClass === null ? run : `<span class="${curClass}">${run}</span>`;
        run = "";
      };
      for (let y = 0; y < rows; y++) {
        const base = y * cols;
        for (let x = 0; x < cols; x++) {
          const age = grid[base + x];
          if (age === 0) {
            if (curClass !== null) {
              flush();
              curClass = null;
            }
            run += " ";
            continue;
          }
          const { ch, cls } = cellGlyph(age);
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
      cols = Math.max(20, Math.min(220, Math.floor(rect.width / CHAR_W)));
      rows = Math.max(10, Math.min(120, Math.floor(rect.height / CHAR_H)));
      alloc();
    }
    resize();
    // Coalesce reduced-motion repaints: settling the grid costs 40 full
    // generations, too heavy to redo on every callback of a drag-resize.
    // (Safe to read `raf` here — the observer only fires after the effect body,
    // where `raf` is declared.)
    const ro = new ResizeObserver(() => {
      resize();
      if (reduce) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          for (let g = 0; g < 40; g++) step();
          renderFrame();
        });
      }
    });
    ro.observe(container);

    let raf = 0;
    let last = 0;
    function frame(ts: number) {
      if (ts - last < STEP_MS) {
        raf = requestAnimationFrame(frame);
        return;
      }
      last = ts;
      step();
      renderFrame();
      raf = requestAnimationFrame(frame);
    }
    if (reduce) {
      for (let g = 0; g < 40; g++) step();
      renderFrame();
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
          textShadow: "0 0 6px color-mix(in srgb, var(--amber) 22%, transparent)"
        }}
      />
      <div style={scanlines} />
    </div>
  );
}
