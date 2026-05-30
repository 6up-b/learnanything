import { useCallback, useEffect, useRef, useState } from "react";
import type { SessionEndSummary } from "../api/dto";

// Full-screen "session complete" overlay rendered as ASCII/unicode art, in
// LearnLoop's terminal/CLI language. The whole HUD — concentric rings, a
// segmented progress meter that fills 0→100%, orbiting satellites, sonar pings,
// side telemetry, a big block-digit percentage, registration codes and the
// resolved stats — is drawn into a single monospace character grid each frame
// (the same <pre> + innerHTML technique as the Start-screen backdrop).
//
// It is ONE continuous flow (no jump cuts). On dismissal the grid collapses
// CRT-style before unmounting. Self-contained: renders purely from
// SessionEndSummary; honors prefers-reduced-motion (static completed frame,
// instant dismiss).
const EXIT_MS = 520;
const CHAR_W = 7;
const CHAR_H = 12;
const ACTIVE_FRAME_MS = 33;
const COMPLETE_FRAME_MS = 66;

// 5-row block-digit font for the hero percentage.
const GLYPHS: Record<string, string[]> = {
  "0": ["████", "█  █", "█  █", "█  █", "████"],
  "1": ["  █ ", " ██ ", "  █ ", "  █ ", "████"],
  "2": ["████", "   █", "████", "█   ", "████"],
  "3": ["████", "   █", " ███", "   █", "████"],
  "4": ["█  █", "█  █", "████", "   █", "   █"],
  "5": ["████", "█   ", "████", "   █", "████"],
  "6": ["████", "█   ", "████", "█  █", "████"],
  "7": ["████", "   █", "  █ ", " █  ", " █  "],
  "8": ["████", "█  █", "████", "█  █", "████"],
  "9": ["████", "█  █", "████", "   █", "████"]
};

const C = {
  amber: 1,
  amberHi: 2,
  amberMid: 3,
  amberLow: 4,
  faintDot: 5,
  green: 6,
  dim: 7,
  faint: 8
} as const;

type ColorId = (typeof C)[keyof typeof C];

const COLOR_CLASS: Record<ColorId, string> = {
  [C.amber]: "sfin-c-amber",
  [C.amberHi]: "sfin-c-amber-hi",
  [C.amberMid]: "sfin-c-amber-mid",
  [C.amberLow]: "sfin-c-amber-low",
  [C.faintDot]: "sfin-c-faint-dot",
  [C.green]: "sfin-c-green",
  [C.dim]: "sfin-c-dim",
  [C.faint]: "sfin-c-faint"
};
const NEEDS_ESCAPE_RE = /[&<>]/;
const HTML_ESCAPE_RE = /[&<>]/g;

export function SessionFinishHud({
  summary,
  onDismiss
}: {
  summary: SessionEndSummary | null;
  onDismiss: () => void;
}) {
  const active = summary !== null;
  const [closing, setClosing] = useState(false);
  const closingRef = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (active) return;
    closingRef.current = false;
    setClosing(false);
  }, [active]);

  const requestClose = useCallback(() => {
    if (closingRef.current) return;
    closingRef.current = true;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      onDismiss();
      return;
    }
    setClosing(true);
    window.setTimeout(onDismiss, EXIT_MS);
  }, [onDismiss]);

  useEffect(() => {
    if (!active) return;
    const onKey = (event: KeyboardEvent) => {
      event.preventDefault();
      event.stopPropagation();
      requestClose();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [active, requestClose]);

  // The render loop: builds the character grid every frame from a single 0→100
  // progress driver plus time-based rotation / sonar / telemetry phases.
  useEffect(() => {
    if (!active || !summary) return;
    const container = containerRef.current;
    const pre = preRef.current;
    if (!container || !pre) return;

    const aspect = CHAR_W / CHAR_H;
    const code = summary.sessionId.slice(-6).toUpperCase();
    const logNo = (parseInt(summary.sessionId.slice(-5), 36) % 9000) + 1000;
    const elapsed = formatElapsed(summary.startedAt, summary.endedAt);
    const attempts = String(summary.attemptsRecorded);
    const items = String(summary.itemsReviewed);
    const followups = summary.followupsQueued != null ? String(summary.followupsQueued) : "—";
    const streakDays = `${summary.streak.current}d`;
    const streakActive = summary.streak.activeToday;
    const bestStreak = `BEST STREAK ${summary.streak.longest}D`;

    let cols = 0;
    let rows = 0;
    let grid: string[] = [];
    let cgrid = new Uint8Array(0);
    const resize = () => {
      const rect = container.getBoundingClientRect();
      const nextCols = Math.max(40, Math.floor(rect.width / CHAR_W));
      const nextRows = Math.max(24, Math.floor(rect.height / CHAR_H));
      if (nextCols === cols && nextRows === rows) return;
      cols = nextCols;
      rows = nextRows;
      grid = new Array(cols * rows);
      cgrid = new Uint8Array(cols * rows);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    let raf = 0;
    let startTs = 0;
    let lastDrawTs = 0;

    const draw = (ts: number) => {
      if (closingRef.current) return;
      if (!startTs) startTs = ts;
      const sinceStart = ts - startTs;
      // 0→100 progress, eased, with a short lead-in.
      const pt = Math.min(1, Math.max(0, (sinceStart - 300) / 2050));
      const pct = reduce ? 100 : Math.round((1 - Math.pow(1 - pt, 3)) * 100);
      const f = pct / 100;
      const done = pct >= 100;
      const phase = reduce ? 0 : ts / 1000;

      const frameMs = done ? COMPLETE_FRAME_MS : ACTIVE_FRAME_MS;
      if (!reduce && lastDrawTs && ts - lastDrawTs < frameMs) {
        raf = requestAnimationFrame(draw);
        return;
      }
      lastDrawTs = ts;

      grid.fill(" ");
      cgrid.fill(0);
      const set = (r: number, c: number, ch: string, color: ColorId) => {
        if (r < 0 || r >= rows || c < 0 || c >= cols) return;
        const i = r * cols + c;
        grid[i] = ch;
        cgrid[i] = color;
      };
      const put = (r: number, c: number, str: string, color: ColorId) => {
        for (let k = 0; k < str.length; k++) set(r, c + k, str[k], color);
      };
      const putCenter = (r: number, str: string, color: ColorId) => put(r, Math.round((cols - str.length) / 2), str, color);

      // Centre on the middle *index* of the 0..cols-1 grid, not cols/2 (which is
      // half a cell too far right and shifts the ring + digits off-centre).
      const cx = (cols - 1) / 2;
      const cy = (rows - 1) / 2;
      const maxR = Math.min(cx - 2, (cy - 2) / aspect);
      const rMeter = maxR * 0.82;
      const rOuter = maxR * 0.99;
      const rClaw = maxR * 0.9;
      const rInner = maxR * 0.6;

      const place = (rad: number, ang: number, ch: string, color: ColorId) =>
        set(Math.round(cy + rad * aspect * Math.sin(ang)), Math.round(cx + rad * Math.cos(ang)), ch, color);

      const ringSteps = (rad: number) => Math.max(48, Math.round(2 * Math.PI * rad * 1.5));

      // faint outer dotted ring + inner dotted ring
      for (const rad of [rOuter, rInner]) {
        const steps = ringSteps(rad);
        for (let s = 0; s < steps; s++) {
          if (s % 3 !== 0) continue;
          place(rad, (s / steps) * 2 * Math.PI, "·", C.faintDot);
        }
      }

      // sonar pings — expanding faint rings
      if (!reduce) {
        for (const off of [0, 0.5]) {
          const prog = ((phase / 3.4) + off) % 1;
          const rad = maxR * (0.14 + prog * 0.72);
          const shade = prog < 0.7 ? C.amberLow : C.faintDot;
          const steps = ringSteps(rad);
          for (let s = 0; s < steps; s++) {
            if (s % 4 !== 0) continue;
            place(rad, (s / steps) * 2 * Math.PI, "·", shade);
          }
        }
      }

      // rotating claw arcs (4 short bright segments)
      for (let k = 0; k < 4; k++) {
        const base = phase * 0.18 + k * 0.25;
        for (let d = -0.035; d <= 0.035; d += 0.012) {
          place(rClaw, (base + d) * 2 * Math.PI, "█", C.amberMid);
        }
      }

      // segmented progress meter
      {
        const steps = ringSteps(rMeter);
        for (let s = 0; s < steps; s++) {
          const t = s / steps;
          const ang = -Math.PI / 2 + t * 2 * Math.PI;
          const lit = t <= f;
          const head = !done && lit && f - t < 2.5 / steps;
          place(rMeter, ang, lit ? "█" : "·", head ? C.green : lit ? C.amber : C.amberLow);
        }
      }

      // orbiting satellites
      if (!reduce) {
        place(rMeter * 1.06, phase * 0.9 - Math.PI / 2, "●", C.amberHi);
        place(rInner * 0.96, -phase * 1.2, "●", C.green);
        place(rOuter, phase * 0.5, "○", C.faint);
      }

      // cardinal chevrons just outside the meter
      place(rMeter * 1.12, -Math.PI / 2, "▼", C.amberMid);
      place(rMeter * 1.12, Math.PI / 2, "▲", C.amberMid);
      place(rMeter * 1.12, 0, "◀", C.amberMid);
      place(rMeter * 1.12, Math.PI, "▶", C.amberMid);

      // side telemetry columns (scanning segmented bars)
      const teleRows = Math.min(10, Math.floor(rows * 0.34));
      const teleTop = Math.round(cy - teleRows / 2);
      for (let i = 0; i < teleRows; i++) {
        const onL = !reduce && Math.sin(phase * 3 - i * 0.6) > 0.2;
        const onR = !reduce && Math.sin(phase * 3 - i * 0.6 + 1.5) > 0.2;
        put(teleTop + i, 3, "▮▮", onL ? C.amber : C.amberLow);
        put(teleTop + i, cols - 5, "▮▮", onR ? C.amber : C.amberLow);
      }

      // X-boxed registration squares + microcodes
      const xr = Math.round(cy - rInner * aspect);
      put(xr, Math.round(cx - rInner), "⊠", C.faint);
      put(xr, Math.round(cx - rInner) + 2, "K-12", C.faint);
      put(Math.round(cy + rInner * aspect), Math.round(cx + rInner) - 4, "RLA ⊠", C.faint);

      // corner brackets + registration codes
      set(0, 0, "┌", C.faint);
      set(0, cols - 1, "┐", C.faint);
      set(rows - 1, 0, "└", C.faint);
      set(rows - 1, cols - 1, "┘", C.faint);
      put(1, 2, `LL//RUNNER · ${code}`, C.faint);
      const logStr = `LOG #${logNo}`;
      put(1, cols - 2 - logStr.length, logStr, C.faint);
      put(rows - 2, 2, bestStreak, C.faint);
      const status = done ? "● STATUS OK" : "○ FINALIZING";
      put(rows - 2, cols - 2 - status.length, status, done ? C.amber : C.faint);

      // centre readout
      putCenter(Math.round(cy) - 5, "S E S S I O N   C O M P L E T E", C.amber);

      // big block-digit percentage
      const digits = String(pct);
      const blockW = digits.length * 5 - 1;
      const startCol = Math.round(cx - (blockW - 1) / 2);
      const topRow = Math.round(cy) - 2;
      for (let di = 0; di < digits.length; di++) {
        const glyph = GLYPHS[digits[di]];
        for (let r = 0; r < 5; r++) {
          for (let c = 0; c < 4; c++) {
            if (glyph[r][c] === "█") set(topRow + r, startCol + di * 5 + c, "█", C.amberHi);
          }
        }
      }
      put(topRow + 2, startCol + blockW + 1, "%", C.dim);

      // status line / resolved stats
      if (!done) {
        putCenter(Math.round(cy) + 5, `FINALIZING // ${code}`, C.faint);
      } else {
        const segs: Array<[string, ColorId]> = [
          ["ATTEMPTS ", C.faint], [attempts, C.amber], ["    ", C.faint],
          ["ITEMS ", C.faint], [items, C.amber], ["    ", C.faint],
          ["FOLLOW-UPS ", C.faint], [followups, C.green], ["    ", C.faint],
          ["STREAK ", C.faint], [streakDays, streakActive ? C.green : C.amber]
        ];
        const total = segs.reduce((n, [s]) => n + s.length, 0);
        let col = Math.round(cx - total / 2);
        for (const [s, color] of segs) {
          put(Math.round(cy) + 5, col, s, color);
          col += s.length;
        }
        putCenter(rows - 4, `▍ PRESS ANY KEY TO CONTINUE · ELAPSED ${elapsed}`, C.dim);
      }

      // rasterize to colored spans (run-length per row)
      let html = "";
      for (let r = 0; r < rows; r++) {
        let run = "";
        let cur = 0;
        const flush = () => {
          if (!run) return;
          html += cur ? `<span class="${COLOR_CLASS[cur as ColorId]}">${esc(run)}</span>` : esc(run);
          run = "";
        };
        for (let c = 0; c < cols; c++) {
          const i = r * cols + c;
          const color = cgrid[i];
          if (color !== cur) {
            flush();
            cur = color;
          }
          run += grid[i];
        }
        flush();
        html += "\n";
      }
      pre.innerHTML = html;

      if (!reduce) raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [active, summary]);

  if (!summary) return null;

  return (
    <div
      ref={containerRef}
      className={`sfin-overlay${closing ? " sfin-exiting" : ""}`}
      role="dialog"
      aria-label="Session complete"
      onClick={requestClose}
    >
      <pre ref={preRef} className="sfin-ascii" aria-hidden="true" />
      <div className="sfin-scan" />
    </div>
  );
}

function esc(s: string): string {
  return NEEDS_ESCAPE_RE.test(s)
    ? s.replace(HTML_ESCAPE_RE, (ch) => (ch === "&" ? "&amp;" : ch === "<" ? "&lt;" : "&gt;"))
    : s;
}

function formatElapsed(startedAt: string, endedAt: string): string {
  const ms = new Date(endedAt).getTime() - new Date(startedAt).getTime();
  if (!Number.isFinite(ms) || ms < 0) return "0:00";
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
