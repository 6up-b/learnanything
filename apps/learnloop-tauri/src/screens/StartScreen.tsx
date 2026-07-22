// Warm-up / Session start screen — ported from the LearnLoop handoff prototype.
// Left: a switchable animated ASCII / canvas backdrop (lorenz · waves · fluid ·
// torus · axes · tesseract) with a hero overlay. Right: the session-readiness
// form (energy / sleep / minutes), a derived scheduler-mode card, a live queue
// preview, and the begin action. The readiness controls feed the real
// get_today_queue / start_session commands.

import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { api } from "../api/client";
import type { QueueSnapshot, ScheduledItemDto, SessionSnapshot, StreakSummary, VaultSummary } from "../api/dto";
import { EmptyPlaceholder, KeyBar, SectionHeader } from "../components/ui";

const COLOR = {
  bg: "#0e0e0e",
  bgElev: "#181818",
  border: "#2a2a2a",
  borderStrong: "#3a3a3a",
  text: "#d8d8e0",
  textDim: "#9090a0",
  textItalic: "#8088a0",
  textFaint: "#666778",
  amber: "#e3a063",
  amberLink: "#f0b878",
  green: "#7fd28f",
  cyan: "#6ad0e0",
  red: "#e07e7e",
  pink: "#dc7fb8"
};

const FONT_MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace';

const LOW_MASTERY_WORDS = [
  "better", "oriented", "motivated", "prepared", "improve", "develop",
  "grow", "progress", "explore", "notice", "remember", "familiar",
  "grounded", "persistent", "unstuck", "ready"
];
const HIGH_MASTERY_WORDS = [
  "fluent", "sharp", "confident", "capable", "skilled", "proficient",
  "precise", "fast", "strong", "strategic", "insightful", "adaptive",
  "resourceful", "articulate", "analytical", "creative", "disciplined",
  "an expert", "masterful", "brilliant", "advanced", "independent",
  "intelligent", "unstoppable", "god"
];

function CyclingTypewriterText({ prefix, words, wordColor, speed = 50, untypeSpeed = 32, holdMs = 2500 }: {
  prefix?: string;
  words: string[];
  wordColor?: string;
  speed?: number;
  untypeSpeed?: number;
  holdMs?: number;
}) {
  const [idx, setIdx] = useState(0);
  const [displayed, setDisplayed] = useState("");
  const [phase, setPhase] = useState<"typing" | "holding" | "untyping">("typing");

  const word = words[idx % words.length];

  useEffect(() => {
    setDisplayed("");
    setPhase("typing");
  }, [idx]);

  useEffect(() => {
    if (phase === "typing") {
      if (displayed.length >= word.length) { setPhase("holding"); return; }
      const id = setTimeout(() => setDisplayed(word.slice(0, displayed.length + 1)), speed);
      return () => clearTimeout(id);
    }
    if (phase === "holding") {
      const id = setTimeout(() => setPhase("untyping"), holdMs);
      return () => clearTimeout(id);
    }
    // untyping
    if (displayed.length === 0) { setIdx((i) => i + 1); return; }
    const id = setTimeout(() => setDisplayed(displayed.slice(0, -1)), untypeSpeed);
    return () => clearTimeout(id);
  }, [phase, displayed, word, speed, untypeSpeed, holdMs]);

  const cursorColor = wordColor ?? "#ffffff";
  return (
    <span>
      {prefix ? <span style={{ opacity: 0.82 }}>{prefix}</span> : null}
      <span style={{ color: wordColor ?? "#ffffff" }}>{displayed}</span>
      <span
        style={{
          display: "inline-block",
          width: "0.5em",
          height: "0.2em",
          background: cursorColor,
          verticalAlign: "text-bottom",
          marginLeft: "0.15em",
          animation: "typewriter-blink 0.8s step-end infinite"
        }}
      />
    </span>
  );
}

type BackdropName = "lorenz" | "waves" | "fluid" | "torus" | "axes" | "tesseract";
const BACKDROP_ORDER: BackdropName[] = ["lorenz", "waves", "fluid", "torus", "axes", "tesseract"];

// ── Fluid gradient backdrop ──────────────────────────────────────────────
// Soft radial-gradient "blobs" drift around the canvas with additive blending.
function FluidBackdrop() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const blobs = [
      { x: 0.3, y: 0.3, color: "rgba(118, 57, 7, 0.85)", speed: 0.00018, phase: 0.0, radius: 0.65 },
      { x: 0.72, y: 0.38, color: "rgba(71, 58, 41, 0.75)", speed: 0.00022, phase: 1.2, radius: 0.55 },
      { x: 0.55, y: 0.72, color: "rgba(84, 55, 43, 0.55)", speed: 0.0002, phase: 2.4, radius: 0.6 },
      { x: 0.22, y: 0.68, color: "rgba(116, 42, 89, 0.55)", speed: 0.00025, phase: 3.6, radius: 0.5 },
      { x: 0.85, y: 0.85, color: "rgba(59, 100, 12, 0.6)", speed: 0.00017, phase: 4.8, radius: 0.55 }
    ];

    let raf = 0;
    let dpr = window.devicePixelRatio || 1;
    function resize() {
      const rect = canvas!.getBoundingClientRect();
      dpr = window.devicePixelRatio || 1;
      canvas!.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas!.height = Math.max(1, Math.floor(rect.height * dpr));
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    function frame(ts: number) {
      const w = canvas!.width / dpr;
      const h = canvas!.height / dpr;
      ctx!.globalCompositeOperation = "source-over";
      ctx!.fillStyle = "#0a0a14";
      ctx!.fillRect(0, 0, w, h);
      ctx!.globalCompositeOperation = "lighter";
      const R = Math.max(w, h);
      for (const b of blobs) {
        const cx = (b.x + 0.22 * Math.cos(ts * b.speed + b.phase)) * w;
        const cy = (b.y + 0.22 * Math.sin(ts * b.speed * 1.3 + b.phase)) * h;
        const r = R * b.radius;
        const g = ctx!.createRadialGradient(cx, cy, 0, cx, cy, r);
        g.addColorStop(0, b.color);
        g.addColorStop(0.6, b.color.replace(/[\d.]+\)$/, "0.18)"));
        g.addColorStop(1, "rgba(0,0,0,0)");
        ctx!.fillStyle = g;
        ctx!.fillRect(0, 0, w, h);
      }
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);
  return <canvas ref={ref} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", display: "block" }} />;
}

// ── Perlin / fractal-noise overlay (additive) ─────────────────────────────
function NoiseOverlay() {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'>
    <filter id='n' x='0' y='0' width='100%' height='100%'>
      <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/>
      <feColorMatrix values='0 0 0 0 1   0 0 0 0 1   0 0 0 0 1   0 0 0 0.65 0'/>
    </filter>
    <rect width='100%' height='100%' filter='url(#n)'/>
  </svg>`;
  const dataUri = `url("data:image/svg+xml;utf8,${encodeURIComponent(svg)}")`;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage: dataUri,
        backgroundRepeat: "repeat",
        backgroundSize: "240px 240px",
        mixBlendMode: "plus-lighter",
        opacity: 0.18,
        pointerEvents: "none"
      }}
    />
  );
}

const CRT_SCANLINES: CSSProperties = {
  position: "absolute",
  inset: 0,
  pointerEvents: "none",
  backgroundImage:
    "repeating-linear-gradient(to bottom, rgba(255,255,255,0.035) 0px, rgba(255,255,255,0.035) 1px, transparent 2px, transparent 4px)"
};

// ── Lorenz / chaos attractor backdrop ─────────────────────────────────────
type LorenzTr = { x: number; y: number; z: number; trail: number[][]; hot: boolean };
function LorenzBackdrop({ density = 12, intensity = 0.8 }: { density?: number; intensity?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const dimPreRef = useRef<HTMLPreElement>(null);
  const hotPreRef = useRef<HTMLPreElement>(null);
  const densityRef = useRef(density);
  const intensityRef = useRef(intensity);
  const needsRebuildRef = useRef(false);

  useEffect(() => {
    if (densityRef.current !== density) needsRebuildRef.current = true;
    densityRef.current = density;
  }, [density]);
  useEffect(() => {
    intensityRef.current = intensity;
  }, [intensity]);

  useEffect(() => {
    const container = containerRef.current;
    const dimPre = dimPreRef.current;
    const hotPre = hotPreRef.current;
    if (!container || !dimPre || !hotPre) return;

    const CHAR_W = 7;
    const CHAR_H = 12;
    const SIGMA = 10;
    const RHO = 28;
    const BETA = 8 / 3;
    const DT = 0.006;
    const SUBSTEPS = 3;
    const TRAIL_LEN = 110;
    const CHARS = ".,-+*#@";

    let cols = 80;
    let rows = 40;
    let trajectories: LorenzTr[] = [];

    function stepOnce(tr: LorenzTr) {
      const { x, y, z } = tr;
      tr.x = x + SIGMA * (y - x) * DT;
      tr.y = y + (x * (RHO - z) - y) * DT;
      tr.z = z + (x * y - BETA * z) * DT;
    }

    function makeTrajectories() {
      trajectories = [];
      const total = Math.max(2, Math.round(densityRef.current));
      const numHot = Math.max(1, Math.min(Math.ceil(total / 3), Math.round(total * 0.18)));
      for (let i = 0; i < total; i++) {
        const seed = i / Math.max(1, total - 1) - 0.5;
        trajectories.push({
          x: 0.1 + Math.random() * 0.6 + seed * 1.2,
          y: 0.1 + Math.random() * 0.6,
          z: 20 + Math.random() * 6 + seed * 4,
          trail: [],
          hot: i < numHot
        });
      }
      for (let s = 0; s < 600; s++) {
        for (const tr of trajectories) stepOnce(tr);
      }
      for (let s = 0; s < TRAIL_LEN; s++) {
        for (const tr of trajectories) {
          for (let k = 0; k < SUBSTEPS; k++) stepOnce(tr);
          tr.trail.push([tr.x, tr.z]);
        }
      }
    }

    function resize() {
      const rect = container!.getBoundingClientRect();
      cols = Math.max(20, Math.floor(rect.width / CHAR_W));
      rows = Math.max(20, Math.floor(rect.height / CHAR_H));
      makeTrajectories();
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    let raf = 0;
    function draw() {
      if (needsRebuildRef.current) {
        makeTrajectories();
        needsRebuildRef.current = false;
      }
      for (const tr of trajectories) {
        for (let k = 0; k < SUBSTEPS; k++) stepOnce(tr);
        tr.trail.push([tr.x, tr.z]);
        if (tr.trail.length > TRAIL_LEN) tr.trail.shift();
      }

      const fill = intensityRef.current;
      const dimGrid = Array.from({ length: rows }, () => Array(cols).fill(" "));
      const hotGrid = Array.from({ length: rows }, () => Array(cols).fill(" "));

      const SCALE_X = (cols * 0.42) / 25;
      const SCALE_Z = (rows * 0.85) / 50;
      const ORIGIN_X = cols * 0.5;
      const ORIGIN_Y = rows * 0.88;

      for (const tr of trajectories) {
        const grid = tr.hot ? hotGrid : dimGrid;
        const len = tr.trail.length;
        for (let i = 0; i < len; i++) {
          if (fill < 1 && Math.random() > fill) continue;
          const p = tr.trail[i];
          const cx = Math.floor(ORIGIN_X + p[0] * SCALE_X);
          const cy = Math.floor(ORIGIN_Y - p[1] * SCALE_Z);
          if (cx < 0 || cx >= cols || cy < 0 || cy >= rows) continue;
          const age = i / Math.max(1, len - 1);
          const ci = Math.min(CHARS.length - 1, Math.floor(age * CHARS.length));
          grid[cy][cx] = CHARS[ci];
        }
      }

      dimPre!.textContent = dimGrid.map((r) => r.join("")).join("\n");
      hotPre!.textContent = hotGrid.map((r) => r.join("")).join("\n");
      raf = requestAnimationFrame(draw);
    }
    raf = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
      <pre
        ref={dimPreRef}
        style={{
          position: "absolute",
          inset: 0,
          margin: 0,
          padding: 0,
          fontFamily: FONT_MONO,
          fontSize: 12,
          lineHeight: "12px",
          letterSpacing: 0,
          color: "rgba(150, 155, 168, 0.55)",
          whiteSpace: "pre",
          userSelect: "none"
        }}
      />
      <pre
        ref={hotPreRef}
        style={{
          position: "absolute",
          inset: 0,
          margin: 0,
          padding: 0,
          fontFamily: FONT_MONO,
          fontSize: 12,
          lineHeight: "12px",
          letterSpacing: 0,
          color: COLOR.amber,
          textShadow: "0 0 6px rgba(227, 160, 99, 0.55), 0 0 14px rgba(227, 160, 99, 0.20)",
          whiteSpace: "pre",
          userSelect: "none"
        }}
      />
      <div style={CRT_SCANLINES} />
    </div>
  );
}

// ── ASCII wave backdrop ───────────────────────────────────────────────────
function WaveBackdrop({ density = 14, intensity = 0.7 }: { density?: number; intensity?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);
  const densityRef = useRef(density);
  const intensityRef = useRef(intensity);
  const needsRebuildRef = useRef(false);

  useEffect(() => {
    if (densityRef.current !== density) needsRebuildRef.current = true;
    densityRef.current = density;
  }, [density]);
  useEffect(() => {
    intensityRef.current = intensity;
  }, [intensity]);

  useEffect(() => {
    const container = containerRef.current;
    const pre = preRef.current;
    if (!container || !pre) return;

    const CHAR_W = 7;
    const CHAR_H = 12;

    let cols = 80;
    let rows = 40;
    let mouse = { x: cols / 2, y: rows / 2 };
    let strings: CursedString[] = [];

    const baseString = "LINEAR_ALGEBRA";
    let currentString = baseString;
    const mutations: Array<(s: string) => string> = [
      (s) => s.split("").reverse().join(""),
      (s) => s.replace(/O/g, "0"),
      (s) => s.replace(/E/g, "3"),
      (s) => s.slice(0, Math.max(1, Math.floor(Math.random() * s.length))),
      (s) => s + "_ERR"
    ];

    function mutateString() {
      const fn = mutations[Math.floor(Math.random() * mutations.length)];
      currentString = fn(currentString);
      if (currentString.length < 2) currentString = baseString;
    }

    class CursedString {
      index: number;
      total: number;
      depth: number;
      baseY: number;
      amplitude: number;
      wavelength: number;
      speed: number;
      offset: number;
      time: number;
      constructor(index: number, total: number, depth: number) {
        this.index = index;
        this.total = total;
        this.depth = depth;
        this.baseY = (index / total) * rows;
        this.amplitude = 2 + depth * 4;
        this.wavelength = 0.08;
        this.speed = 0.0 + depth * 0.002;
        this.offset = Math.random() * 100;
        this.time = 0;
      }
      update(t: number) {
        this.time = t;
      }
      getY(x: number) {
        let y = this.baseY + Math.sin(x * this.wavelength + this.time * this.speed + this.offset) * this.amplitude;
        y += Math.sin(x * 0.04 + this.time * 0.0015) * (this.amplitude * 0.5);
        const dx = x - mouse.x;
        const dy = y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 10) y += (10 - dist) * 0.3 * this.depth;
        return Math.floor(y);
      }
    }

    function createStrings() {
      strings = [];
      const total = Math.max(2, Math.round(densityRef.current));
      for (let i = 0; i < total; i++) {
        const depth = 0.6 + Math.random() * 0.8;
        strings.push(new CursedString(i, total, depth));
      }
    }

    function resize() {
      const rect = container!.getBoundingClientRect();
      cols = Math.max(10, Math.floor(rect.width / CHAR_W));
      rows = Math.max(10, Math.floor(rect.height / CHAR_H));
      mouse = { x: cols / 2, y: rows / 2 };
      createStrings();
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    function onMove(e: MouseEvent) {
      const rect = container!.getBoundingClientRect();
      mouse.x = (e.clientX - rect.left) / CHAR_W;
      mouse.y = (e.clientY - rect.top) / CHAR_H;
    }
    container.addEventListener("mousemove", onMove);

    let raf = 0;
    let lastMutation = 0;
    function draw(time: number) {
      if (needsRebuildRef.current) {
        createStrings();
        needsRebuildRef.current = false;
      }
      const fill = intensityRef.current;
      const grid = Array.from({ length: rows }, () => Array(cols).fill(" "));
      strings.forEach((s) => {
        s.update(time);
        for (let x = 0; x < cols; x++) {
          const y = s.getY(x);
          if (y < 0 || y >= rows) continue;
          if (fill < 1 && Math.random() > fill) continue;
          const charIndex = (x + Math.floor(time * 0.01)) % currentString.length;
          let char = currentString[charIndex];
          if (Math.random() < 0.015) char = "#";
          grid[y][x] = char;
        }
      });
      pre!.textContent = grid.map((r) => r.join("")).join("\n");
      if (time - lastMutation > 2500) {
        mutateString();
        lastMutation = time;
      }
      raf = requestAnimationFrame(draw);
    }
    raf = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      container.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
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
          color: COLOR.amber,
          textShadow: "0 0 6px rgba(227, 160, 99, 0.45), 0 0 14px rgba(227, 160, 99, 0.15)",
          whiteSpace: "pre",
          userSelect: "none"
        }}
      />
      <div style={CRT_SCANLINES} />
    </div>
  );
}

// ── Torus renderer (donut.c, colored) ─────────────────────────────────────
const TORUS_W = 60;
const TORUS_H = 26;
const RAMP = ".,-~:;=!*#$@";
const RAMP_COLORS = [
  "#523a3a",
  "#664545",
  "#927164",
  "#9a7c5a",
  "#b08b6d",
  "#ac845f",
  "#b29473",
  "#be9c60",
  "#bfa183",
  "#ac8a56",
  "#eeb86e",
  "#d5b585"
];
function Torus() {
  const ref = useRef<HTMLPreElement>(null);
  const aRef = useRef(0);
  const bRef = useRef(0);
  useEffect(() => {
    if (!ref.current) return;
    const node = ref.current;
    let raf = 0;
    let last = 0;
    function frame(ts: number) {
      if (ts - last < 33) {
        raf = requestAnimationFrame(frame);
        return;
      }
      last = ts;
      const W = TORUS_W;
      const H = TORUS_H;
      const buf = new Array(W * H).fill(-1);
      const zbuf = new Array(W * H).fill(0);
      const A = aRef.current;
      const B = bRef.current;
      const cosA = Math.cos(A);
      const sinA = Math.sin(A);
      const cosB = Math.cos(B);
      const sinB = Math.sin(B);
      for (let theta = 0; theta < 6.28; theta += 0.1) {
        const cosT = Math.cos(theta);
        const sinT = Math.sin(theta);
        for (let phi = 0; phi < 6.28; phi += 0.028) {
          const cosP = Math.cos(phi);
          const sinP = Math.sin(phi);
          const circleX = 2 + cosT;
          const circleY = sinT;
          const x = circleX * (cosB * cosP + sinA * sinB * sinP) - circleY * cosA * sinB;
          const y = circleX * (sinB * cosP - sinA * cosB * sinP) + circleY * cosA * cosB;
          const z = 5 + cosA * circleX * sinP + circleY * sinA;
          const ooz = 1 / z;
          const xp = Math.floor(W / 2 + 30 * ooz * x);
          const yp = Math.floor(H / 2 - 13 * ooz * y);
          const L = cosP * cosT * sinB - cosA * cosT * sinP - sinA * sinT + cosB * (cosA * sinT - cosT * sinA * sinP);
          if (xp < 0 || xp >= W || yp < 0 || yp >= H) continue;
          if (L <= 0) continue;
          const idx = xp + W * yp;
          if (ooz > zbuf[idx]) {
            zbuf[idx] = ooz;
            buf[idx] = Math.min(RAMP.length - 1, Math.max(0, Math.floor(L * 8)));
          }
        }
      }

      let html = "";
      let curColor: string | null = null;
      let run = "";
      const flush = () => {
        if (run.length === 0) return;
        html += curColor === null ? run : `<span style="color:${curColor}">${run}</span>`;
        run = "";
      };
      for (let i = 0; i < H; i++) {
        for (let j = 0; j < W; j++) {
          const k = i * W + j;
          const lum = buf[k];
          const ch = lum < 0 ? " " : RAMP[lum];
          const color = lum < 0 ? null : RAMP_COLORS[lum];
          if (color !== curColor) {
            flush();
            curColor = color;
          }
          run += ch === " " ? " " : ch;
        }
        flush();
        html += "\n";
        curColor = null;
      }
      node.innerHTML = html;
      aRef.current += 0.045;
      bRef.current += 0.025;
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <pre
      ref={ref}
      style={{
        margin: 0,
        fontFamily: FONT_MONO,
        fontSize: 12,
        lineHeight: "12px",
        letterSpacing: 0,
        color: COLOR.amber,
        whiteSpace: "pre",
        userSelect: "none",
        textShadow: "0 0 6px rgba(227, 160, 99, 0.18)"
      }}
    />
  );
}

// ── Rotating coordinate-axes / basis-vectors backdrop ──────────────────────
function AxesBackdrop() {
  const containerRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const pre = preRef.current;
    if (!container || !pre) return;

    const CHAR_W = 7;
    const CHAR_H = 12;
    const AXIS_RAMP = ".:-=+*#";
    const AXES = [
      { v: [1, 0, 0], color: COLOR.red, label: "X" },
      { v: [0, 1, 0], color: COLOR.green, label: "Y" },
      { v: [0, 0, 1], color: COLOR.cyan, label: "Z" }
    ];

    let cols = 80;
    let rows = 40;
    function resize() {
      const rect = container!.getBoundingClientRect();
      cols = Math.max(20, Math.floor(rect.width / CHAR_W));
      rows = Math.max(20, Math.floor(rect.height / CHAR_H));
    }
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    function rotate(p: number[], yaw: number, pitch: number) {
      const [x, y, z] = p;
      const cy = Math.cos(yaw);
      const sy = Math.sin(yaw);
      const x1 = x * cy + z * sy;
      const z1 = -x * sy + z * cy;
      const cp = Math.cos(pitch);
      const sp = Math.sin(pitch);
      const y2 = y * cp - z1 * sp;
      const z2 = y * sp + z1 * cp;
      return [x1, y2, z2];
    }

    let raf = 0;
    let yaw = 0.7;
    const pitch = -0.5;

    function plot(
      x0: number,
      y0: number,
      x1: number,
      y1: number,
      ax: { color: string },
      grid: string[][],
      cgrid: (string | null)[][]
    ) {
      const dx = x1 - x0;
      const dy = y1 - y0;
      const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy)));
      for (let s = 0; s <= steps; s++) {
        const t = s / steps;
        const xi = Math.round(x0 + dx * t);
        const yi = Math.round(y0 + dy * t);
        if (xi < 0 || xi >= cols || yi < 0 || yi >= rows) continue;
        const ci = Math.min(AXIS_RAMP.length - 1, Math.floor(t * AXIS_RAMP.length));
        grid[yi][xi] = AXIS_RAMP[ci];
        cgrid[yi][xi] = ax.color;
      }
    }

    function draw() {
      yaw += 0.0032;
      const grid: string[][] = Array.from({ length: rows }, () => Array(cols).fill(" "));
      const cgrid: (string | null)[][] = Array.from({ length: rows }, () => Array(cols).fill(null));

      const cx = cols / 2;
      const cyy = rows / 2;
      const scale = Math.min(cols, rows * 2) * 0.34;
      const aspect = CHAR_W / CHAR_H;

      const project = (p: number[]) => {
        const [x, y] = rotate(p, yaw, pitch);
        return [cx + x * scale, cyy - y * scale * aspect];
      };

      const [ox, oy] = project([0, 0, 0]);
      for (const ax of AXES) {
        const [tx, ty] = project(ax.v);
        plot(ox, oy, tx, ty, ax, grid, cgrid);
        const txi = Math.round(tx);
        const tyi = Math.round(ty);
        if (txi >= 0 && txi < cols && tyi >= 0 && tyi < rows) {
          grid[tyi][txi] = ax.label;
          cgrid[tyi][txi] = ax.color;
        }
      }
      const oxi = Math.round(ox);
      const oyi = Math.round(oy);
      if (oxi >= 0 && oxi < cols && oyi >= 0 && oyi < rows) {
        grid[oyi][oxi] = "+";
        cgrid[oyi][oxi] = COLOR.amber;
      }

      let html = "";
      for (let i = 0; i < rows; i++) {
        let run = "";
        let cur: string | null = null;
        const flush = () => {
          if (!run) return;
          html += cur ? `<span style="color:${cur}">${run}</span>` : run;
          run = "";
        };
        for (let j = 0; j < cols; j++) {
          const ch = grid[i][j];
          const col = cgrid[i][j];
          if (col !== cur) {
            flush();
            cur = col;
          }
          run += ch === " " ? " " : ch;
        }
        flush();
        html += "\n";
      }
      pre!.innerHTML = html;
      raf = requestAnimationFrame(draw);
    }
    raf = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <div ref={containerRef} style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#000" }}>
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
          color: COLOR.amber,
          textShadow: "0 0 6px rgba(227, 160, 99, 0.25)",
          whiteSpace: "pre",
          userSelect: "none"
        }}
      />
      <div style={CRT_SCANLINES} />
    </div>
  );
}

// ── Rotating tesseract / hypercube backdrop ────────────────────────────────
function TesseractBackdrop() {
  const containerRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const pre = preRef.current;
    if (!container || !pre) return;

    const CHAR_W = 7;
    const CHAR_H = 12;
    const CHARS = ".:-=+*#";
    const AMBER = ["#5a4326", "#7c5a30", "#9a6f3a", "#c08a4a", "#e3a063", "#f0c890"];

    type Edge = { i: number; j: number; axis: number };

    const verts: number[][] = [];
    for (let i = 0; i < 16; i++) {
      verts.push([
        i & 1 ? 1 : -1,
        i & 2 ? 1 : -1,
        i & 4 ? 1 : -1,
        i & 8 ? 1 : -1
      ]);
    }

    const edges: Edge[] = [];
    for (let i = 0; i < 16; i++) {
      for (let bit = 0; bit < 4; bit++) {
        const j = i ^ (1 << bit);
        if (i < j) edges.push({ i, j, axis: bit });
      }
    }

    let cols = 80;
    let rows = 40;

    function resize() {
      const rect = container!.getBoundingClientRect();
      cols = Math.max(20, Math.floor(rect.width / CHAR_W));
      rows = Math.max(20, Math.floor(rect.height / CHAR_H));
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    function rotatePlane(p: number[], a: number, i: number, j: number) {
      const q = p.slice();
      const c = Math.cos(a);
      const s = Math.sin(a);
      q[i] = p[i] * c - p[j] * s;
      q[j] = p[i] * s + p[j] * c;
      return q;
    }

    function rot4(p: number[], t: number) {
      let q = p;

      // Rotate in several true 4D coordinate planes.
      // Including XW/YW/ZW makes the inner/outer cube relationship visibly change.
      q = rotatePlane(q, t * 0.55, 0, 3); // XW
      q = rotatePlane(q, t * 0.37, 1, 3); // YW
      q = rotatePlane(q, t * 0.23, 2, 3); // ZW
      q = rotatePlane(q, t * 0.31, 0, 1); // XY
      q = rotatePlane(q, t * 0.19, 1, 2); // YZ

      return q;
    }

    let raf = 0;
    let t = 0;
    const aspect = CHAR_W / CHAR_H;

    function draw() {
      t += 0.006;

      const grid: string[][] = Array.from({ length: rows }, () => Array(cols).fill(" "));
      const cgrid: (string | null)[][] = Array.from({ length: rows }, () => Array(cols).fill(null));

      // Real geometric depth buffer. Larger = closer.
      const zbuf: number[][] = Array.from({ length: rows }, () => Array(cols).fill(-Infinity));

      const D4 = 3.2; // 4D camera distance from W
      const D3 = 4.0; // 3D camera distance from Z

      let dmin = Infinity;
      let dmax = -Infinity;

      const projected = verts.map((v) => {
        const [x, y, z, w] = rot4(v, t);

        // 4D perspective projection into 3D.
        // Points with larger w appear larger/nearer.
        const k4 = D4 / (D4 - w);
        const x3 = x * k4;
        const y3 = y * k4;
        const z3 = z * k4;

        // 3D perspective projection into 2D.
        const k3 = D3 / (D3 - z3);
        const sx = x3 * k3;
        const sy = y3 * k3;

        // Actual depth used for both brightness and occlusion.
        // z3 dominates ordinary 3D nearness, w contributes 4D nearness.
        const depth = z3 + 0.35 * w;

        dmin = Math.min(dmin, depth);
        dmax = Math.max(dmax, depth);

        return { sx, sy, depth, w };
      });

      // Stable scale helps the tesseract breathe naturally under projection.
      const scale = Math.min(cols, rows) * 0.26;
      const cx = cols / 2;
      const cy = rows / 2;

      function brightnessOf(depth: number, boost = 0) {
        const u = (depth - dmin) / Math.max(1e-6, dmax - dmin);
        const b = Math.floor(u * (AMBER.length - 1)) + boost;
        return Math.max(0, Math.min(AMBER.length - 1, b));
      }

      const screen = projected.map((p) => ({
        x: cx + p.sx * scale,
        y: cy - p.sy * scale * aspect,
        depth: p.depth,
        bright: brightnessOf(p.depth)
      }));

      function plot(
        x0: number,
        y0: number,
        z0: number,
        b0: number,
        x1: number,
        y1: number,
        z1: number,
        b1: number,
        isWConnector: boolean
      ) {
        const dx = x1 - x0;
        const dy = y1 - y0;
        const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy) * 1.25));

        for (let s = 0; s <= steps; s++) {
          const u = s / steps;

          const xi = Math.round(x0 + dx * u);
          const yi = Math.round(y0 + dy * u);
          if (xi < 0 || xi >= cols || yi < 0 || yi >= rows) continue;

          const z = z0 + (z1 - z0) * u;
          if (z <= zbuf[yi][xi]) continue;
          zbuf[yi][xi] = z;

          let bri = Math.round(b0 + (b1 - b0) * u);

          // W-axis connectors are the special tesseract edges.
          // Slightly dimming them makes the two cube cells easier to perceive.
          if (isWConnector) bri = Math.max(0, bri - 1);

          const ci = Math.min(
            CHARS.length - 1,
            Math.floor((bri / (AMBER.length - 1)) * (CHARS.length - 1))
          );

          grid[yi][xi] = CHARS[ci];
          cgrid[yi][xi] = AMBER[bri];
        }
      }

      for (const e of edges) {
        const a = screen[e.i];
        const b = screen[e.j];

        plot(
          a.x,
          a.y,
          a.depth,
          a.bright,
          b.x,
          b.y,
          b.depth,
          b.bright,
          e.axis === 3
        );
      }

      let html = "";

      for (let i = 0; i < rows; i++) {
        let run = "";
        let cur: string | null = null;

        const flush = () => {
          if (!run) return;
          html += cur ? `<span style="color:${cur}">${run}</span>` : run;
          run = "";
        };

        for (let j = 0; j < cols; j++) {
          const col = cgrid[i][j];

          if (col !== cur) {
            flush();
            cur = col;
          }

          run += grid[i][j];
        }

        flush();
        html += "\n";
      }

      pre!.innerHTML = html;
      raf = requestAnimationFrame(draw);
    }

    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        background: "#000"
      }}
    >
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
          color: COLOR.amber,
          textShadow:
            "0 0 6px rgba(227, 160, 99, 0.45), 0 0 14px rgba(227, 160, 99, 0.18)",
          whiteSpace: "pre",
          userSelect: "none"
        }}
      />
      <div style={CRT_SCANLINES} />
    </div>
  );
}

// ── Hero overlay (active goal + title) shared across backdrops ─────────────
function BackdropHeroText({ dateLine, vaultAlias, masteryWords, goalMeta }: {
  dateLine: string;
  vaultAlias: string;
  masteryWords: string[];
  goalMeta: string;
}) {
  return (
    <div
      style={{
        position: "relative",
        zIndex: 1,
        pointerEvents: "none",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        justifyContent: "space-between",
        padding: "32px 36px",
        height: "100%",
        color: "#ffffff"
      }}
    >
      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.65)", letterSpacing: "0.02em" }}>
        <span style={{ color: "#ffffff", textDecoration: "underline", textUnderlineOffset: 3 }}>session warm-up</span>
        {"  ·  "}
        {dateLine}
      </div>
      <div style={{ maxWidth: 500 }}>
        <div
          style={{
            fontSize: 12,
            color: "rgba(255,255,255,0.55)",
            textTransform: "uppercase",
            letterSpacing: "0.18em",
            marginBottom: 14
          }}
        >
          {vaultAlias}
        </div>
        <div
          style={{
            fontSize: 38,
            lineHeight: 1.05,
            fontWeight: 600,
            color: "#ffffff",
            textShadow: "0 2px 24px rgba(0,0,0,0.7), 0 0 8px rgba(0,0,0,0.5)",
            letterSpacing: "-0.01em"
          }}
        >
          <div style={{ opacity: 0.82 }}>Escape will make me</div>
          <div style={{ minHeight: "1.1em" }}>
            <CyclingTypewriterText
              words={masteryWords}
              wordColor={COLOR.amber}
            />
          </div>
        </div>
        <div
          style={{
            marginTop: 18,
            fontSize: 13,
            color: "rgba(255,255,255,0.75)",
            lineHeight: 1.65,
            textShadow: "0 1px 6px rgba(0,0,0,0.6)"
          }}
        >
          {goalMeta}
        </div>
      </div>
      <div
        style={{
          fontFamily: FONT_MONO,
          fontSize: 11,
          color: "rgba(255,255,255,0.6)",
          letterSpacing: "0.04em",
          textShadow: "0 1px 4px rgba(0,0,0,0.6)"
        }}
      >
        ready when you are →
      </div>
    </div>
  );
}

// Click-to-cycle backdrop affordance pinned to the start panel.
function StartDebugCycler({ backdrop, onSetBackdrop }: { backdrop: BackdropName; onSetBackdrop: (next: BackdropName) => void }) {
  const [hover, setHover] = useState(false);
  const next = () => {
    const i = BACKDROP_ORDER.indexOf(backdrop);
    onSetBackdrop(BACKDROP_ORDER[(i + 1) % BACKDROP_ORDER.length]);
  };
  return (
    <div
      onClick={next}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      title="cycle backdrop"
      style={{
        position: "absolute",
        top: 14,
        right: 16,
        zIndex: 6,
        cursor: "pointer",
        userSelect: "none",
        pointerEvents: "auto",
        fontFamily: FONT_MONO,
        fontSize: 11,
        letterSpacing: "0.02em",
        padding: "3px 9px",
        borderRadius: 4,
        border: `1px solid ${hover ? COLOR.amber : "rgba(255,255,255,0.18)"}`,
        background: hover ? "rgba(36,29,18,0.85)" : "rgba(0,0,0,0.35)",
        color: hover ? COLOR.amber : "rgba(255,255,255,0.6)",
        opacity: hover ? 1 : 0.55,
        transition: "opacity 140ms ease, color 140ms ease, border-color 140ms ease",
        display: "inline-flex",
        alignItems: "center",
        gap: 6
      }}
    >
      <span style={{ opacity: 0.8 }}>⟳</span>
      <span>backdrop:</span>
      <span style={{ color: hover ? COLOR.amber : "rgba(255,255,255,0.85)" }}>{backdrop}</span>
      <span style={{ opacity: 0.6 }}>›</span>
    </div>
  );
}

// Left panel — renders the selected backdrop with vignette, hero, and cycler.
function BackdropPanel({
  backdrop,
  density,
  intensity,
  onSetBackdrop,
  dateLine,
  vaultAlias,
  masteryWords,
  goalMeta
}: {
  backdrop: BackdropName;
  density: number;
  intensity: number;
  onSetBackdrop: (next: BackdropName) => void;
  dateLine: string;
  vaultAlias: string;
  masteryWords: string[];
  goalMeta: string;
}) {
  let inner: ReactNode;
  if (backdrop === "lorenz") inner = <LorenzBackdrop density={density} intensity={intensity} />;
  else if (backdrop === "waves") inner = <WaveBackdrop density={density} intensity={intensity} />;
  else if (backdrop === "fluid")
    inner = (
      <>
        <FluidBackdrop />
        <NoiseOverlay />
      </>
    );
  else if (backdrop === "axes") inner = <AxesBackdrop />;
  else if (backdrop === "tesseract") inner = <TesseractBackdrop />;

  if (backdrop === "torus") {
    return (
      <div
        style={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 30,
          gap: 18,
          minHeight: 0,
          overflow: "hidden",
          borderRight: `1px solid ${COLOR.border}`,
          background: "radial-gradient(ellipse at center, #18120f 0%, #040404 70%)"
        }}
      >
        <StartDebugCycler backdrop={backdrop} onSetBackdrop={onSetBackdrop} />
        <div style={{ textAlign: "center", alignSelf: "stretch" }}>
          <div style={{ fontSize: 13, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 3, marginBottom: 4 }}>
            session warm-up
          </div>
          <div style={{ color: COLOR.textDim, fontSize: 12, fontStyle: "italic" }}>{dateLine}</div>
        </div>
        <div style={{ padding: 14, border: `1px solid ${COLOR.borderStrong}`, background: "#000", boxShadow: "0 0 60px rgba(255, 162, 75, 0.06)" }}>
          <Torus />
        </div>
        <div style={{ textAlign: "center", maxWidth: 460, lineHeight: 1.6 }}>
          <div style={{ color: COLOR.text, fontSize: 13 }}>
            <CyclingTypewriterText prefix="Escape will make me " words={masteryWords} wordColor={COLOR.amber} />
          </div>
          <div style={{ marginTop: 4, fontStyle: "italic", color: COLOR.textItalic, fontSize: 12 }}>{goalMeta}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "relative",
        borderRight: `1px solid ${COLOR.border}`,
        overflow: "hidden",
        height: "100%",
        minHeight: 0,
        background: backdrop === "fluid" ? "#0a0a14" : "#000"
      }}
    >
      {inner}
      <StartDebugCycler backdrop={backdrop} onSetBackdrop={onSetBackdrop} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,0.55) 100%)"
        }}
      />
      <BackdropHeroText dateLine={dateLine} vaultAlias={vaultAlias} masteryWords={masteryWords} goalMeta={goalMeta} />
    </div>
  );
}

// ── Slider with block-character fill ───────────────────────────────────────
function MonoSlider({ label, value, onChange, width = 14 }: { label: string; value: number; onChange: (v: number) => void; width?: number }) {
  const filled = Math.round(value * width);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "110px 1fr 40px", alignItems: "center", gap: 12, padding: "4px 0" }}>
      <span style={{ fontSize: 12, color: COLOR.textFaint }}>{label}</span>
      <div style={{ fontFamily: FONT_MONO, fontSize: 14, cursor: "pointer", userSelect: "none" }}>
        {Array.from({ length: width }).map((_, i) => (
          <span
            key={i}
            onClick={() => onChange((i + 1) / width)}
            style={{ color: i < filled ? COLOR.amber : COLOR.borderStrong, padding: "0 1px" }}
          >
            ▓
          </span>
        ))}
      </div>
      <span style={{ textAlign: "right", fontSize: 12, color: COLOR.textDim }}>{(value * 10).toFixed(1)}</span>
    </div>
  );
}

// ── Available-minutes preset chips ─────────────────────────────────────────
function MinutesPicker({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const presets = [10, 20, 30, 45, 60];
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {presets.map((m) => {
        const sel = m === value;
        return (
          <span
            key={m}
            onClick={() => onChange(m)}
            style={{
              padding: "4px 12px",
              border: `1px solid ${sel ? COLOR.amber : COLOR.border}`,
              background: sel ? "#241d12" : "transparent",
              color: sel ? COLOR.amber : COLOR.text,
              cursor: "pointer",
              fontSize: 12,
              fontFamily: FONT_MONO
            }}
          >
            {m}m
          </span>
        );
      })}
    </div>
  );
}

function energyBucket(value: number): "low" | "medium" | "high" {
  return value < 0.4 ? "low" : value < 0.7 ? "medium" : "high";
}

function readinessScore(energy: number, sleep: number, minutes: number): number {
  return 0.5 * energy + 0.3 * sleep + 0.2 * Math.min(1, minutes / 60);
}

function readinessQueueLimit(energy: number, sleep: number, minutes: number): number {
  const score = readinessScore(energy, sleep, minutes);
  const timeSlots = Math.max(1, Math.ceil(minutes / 5));
  return Math.max(1, Math.min(50, Math.ceil(timeSlots * score)));
}

function titleCase(value: string): string {
  return value
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function vaultAlias(vault: VaultSummary | null): string {
  if (!vault) return "vault";
  const basename = vault.root.replace(/\\/g, "/").split("/").filter(Boolean).pop() ?? "";
  if (basename) return titleCase(basename);
  if (vault.subjects.length) return titleCase(vault.subjects[0]);
  return "vault";
}

// Compact day-streak indicator for the footer key bar. Amber accent + lowercase
// mono labels match the rest of the start screen; a filled dot means today is
// already logged, a hollow dot means the streak is still waiting on today.
function StreakBadge({ streak }: { streak: StreakSummary }) {
  const { current, activeToday, longest } = streak;
  if (current <= 0) {
    return (
      <span style={{ color: COLOR.textFaint, display: "inline-flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: COLOR.borderStrong }}>○</span>
        no streak yet · begin today
      </span>
    );
  }
  return (
    <span style={{ color: COLOR.textDim, display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span
        title={activeToday ? "logged today" : "practice today to keep your streak"}
        style={{ color: activeToday ? COLOR.amber : COLOR.borderStrong }}
      >
        {activeToday ? "●" : "○"}
      </span>
      <span>
        <b style={{ color: COLOR.amber }}>{current}</b> day{current === 1 ? "" : "s"} streak
      </span>
      {longest > current ? <span style={{ color: COLOR.textFaint }}>· best {longest}</span> : null}
    </span>
  );
}

// "create a new vault ▸" affordance for the Start screen. Prominent (amber,
// filled) on a fresh/empty vault; a quieter ghost link once the vault has content.
function NewVaultAffordance({ fresh, onClick }: { fresh: boolean; onClick: () => void }) {
  return (
    <span
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
      title="Create a brand-new vault and onboard from scratch"
      style={{
        flexShrink: 0,
        padding: "6px 14px",
        fontFamily: FONT_MONO,
        fontSize: 12,
        cursor: "pointer",
        whiteSpace: "nowrap",
        border: `1px solid ${fresh ? COLOR.amber : COLOR.border}`,
        background: fresh ? "#241d12" : "transparent",
        color: fresh ? COLOR.amber : COLOR.textDim
      }}
    >
      + create a new vault ▸
    </span>
  );
}

export function StartScreen({
  onBegin,
  onError,
  vault,
  streak,
  onNewVault
}: {
  onBegin: (session: SessionSnapshot) => void;
  onError: (message: string) => void;
  vault: VaultSummary | null;
  streak: StreakSummary;
  onNewVault: () => void;
}) {
  const [backdrop, setBackdrop] = useState<BackdropName>(
    () => (localStorage.getItem("learnloop.startBackdrop") as BackdropName | null) ?? "axes"
  );
  const [energy, setEnergy] = useState(0.7);
  const [sleep, setSleep] = useState(0.5);
  const [minutes, setMinutes] = useState(30);
  const [preview, setPreview] = useState<QueueSnapshot | null>(null);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const previewRequestRef = useRef<{ key: string; promise: Promise<QueueSnapshot> } | null>(null);

  const energyValue = energyBucket(energy);
  const queueLimit = readinessQueueLimit(energy, sleep, minutes);
  const readinessFactor = readinessScore(energy, sleep, minutes).toFixed(2);

  useEffect(() => {
    localStorage.setItem("learnloop.startBackdrop", backdrop);
  }, [backdrop]);

  useEffect(() => {
    let cancelled = false;
    const key = JSON.stringify({ energy: energyValue, availableMinutes: minutes, limit: queueLimit });
    const inFlight = previewRequestRef.current;
    const promise =
      inFlight?.key === key
        ? inFlight.promise
        : api.getTodayQueue({ energy: energyValue, availableMinutes: minutes, limit: queueLimit });

    previewRequestRef.current = { key, promise };
    setPreviewLoading(true);
    promise
      .then((queue) => {
        if (!cancelled) setPreview(queue);
      })
      .catch((error) => {
        if (!cancelled) onError(error.message);
      })
      .finally(() => {
        if (previewRequestRef.current?.promise === promise) {
          previewRequestRef.current = null;
        }
        if (!cancelled) setPreviewLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [energyValue, minutes, onError, queueLimit, sleep]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (event.key === "Enter") {
        event.preventDefault();
        void begin();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  async function begin() {
    if (loading) return;
    setLoading(true);
    try {
      const session = await api.startSession({ energy: energyValue, sleepQuality: sleep, availableMinutes: minutes });
      onBegin(session);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const items: ScheduledItemDto[] = preview?.sections.flatMap((section) => section.items) ?? [];

  const masteryValues = items.filter((i) => i.mastery !== null).map((i) => i.mastery as number);
  const avgMastery = masteryValues.length > 0 ? masteryValues.reduce((a, b) => a + b, 0) / masteryValues.length : 0;
  const masteryWords = avgMastery >= 0.65 ? HIGH_MASTERY_WORDS : LOW_MASTERY_WORDS;

  const queueSummary = [
    { label: "due now", count: items.filter((i) => i.dueStatus === "due").length, color: COLOR.amber },
    { label: "probe queue", count: items.filter((i) => i.isProbe).length, color: COLOR.pink },
    { label: "later today", count: items.filter((i) => i.dueStatus === "later").length, color: COLOR.textDim },
    { label: "follow-ups", count: items.filter((i) => i.isFollowup).length, color: COLOR.green }
  ];

  // Mirror the scheduler's ACTUAL rule (scheduler.py): probe_eig is suppressed
  // when available_minutes <= scheduler.short_session_minutes (default 20).
  // Energy feeds the readiness factor, not probe suppression.
  const recommendedBudget =
    minutes <= 20
      ? "short_session — probe_eig suppressed (≤20 min)"
      : minutes >= 45
      ? "full_loop — probe_eig active"
      : "standard_loop — probe_eig active";
  const now = new Date();
  const dateLine = `${now.toLocaleDateString(undefined, { weekday: "long" })} · ${now.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit"
  })}`;
  const goalMeta = vault
    ? `${vault.counts.concepts} concepts in scope · ${vault.counts.learningObjects} active learning_objects · ${vault.counts.errorTypes} error types`
    : "11 concepts in scope · 18 active learning_objects · 3 open misconceptions";
  // A fresh install / empty vault gets a louder "create a new vault" affordance.
  const freshInstall = !vault || vault.counts.learningObjects === 0;

  if (previewLoading && !preview) {
    return <EmptyPlaceholder title="Loading today's queue" />;
  }

  return (
    <div className="screen">
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", minHeight: 0 }}>
        <BackdropPanel
          backdrop={backdrop}
          density={14}
          intensity={0.7}
          onSetBackdrop={setBackdrop}
          dateLine={dateLine}
          vaultAlias={vaultAlias(vault)}
          masteryWords={masteryWords}
          goalMeta={goalMeta}
        />

        {/* RIGHT — readiness form + queue preview */}
        <div style={{ padding: "24px 30px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 18, color: COLOR.text, fontWeight: 600 }}>ready to practice?</div>
              <span style={{ fontStyle: "italic", color: COLOR.textItalic, fontSize: 12 }}>
                tell the scheduler about today; it adjusts the queue, not your goals
              </span>
            </div>
            <NewVaultAffordance fresh={freshInstall} onClick={onNewVault} />
          </div>

          <SectionHeader>Readiness</SectionHeader>
          <div style={{ padding: "4px 0" }}>
            <MonoSlider label="energy" value={energy} onChange={setEnergy} />
            <MonoSlider label="sleep quality" value={sleep} onChange={setSleep} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "110px 1fr", gap: 12, alignItems: "center", marginTop: 4 }}>
            <span style={{ fontSize: 12, color: COLOR.textFaint }}>available time</span>
            <MinutesPicker value={minutes} onChange={setMinutes} />
          </div>

          <div style={{ marginTop: 6, padding: "10px 12px", borderLeft: `3px solid ${COLOR.cyan}`, background: "#10212a", fontSize: 12 }}>
            <span style={{ color: COLOR.cyan, fontWeight: 600 }}>scheduler mode</span>{"  "}
            <span style={{ color: COLOR.textDim }}>{recommendedBudget}</span>{"  "}
            <span style={{ color: COLOR.textFaint }}>·</span>{"  "}
            <span style={{ color: COLOR.textFaint }}>readiness_factor</span>{" "}
            <span style={{ color: COLOR.amber }}>{readinessFactor}</span>
          </div>

          <SectionHeader>Today's queue · preview</SectionHeader>
          <div style={{ border: `1px solid ${COLOR.border}`, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
            {queueSummary.map((q, i) => (
              <div
                key={q.label}
                style={{
                  padding: "10px 14px",
                  borderRight: i % 2 === 0 ? `1px solid ${COLOR.border}` : "none",
                  borderBottom: i < 2 ? `1px solid ${COLOR.border}` : "none"
                }}
              >
                <div style={{ fontSize: 22, color: q.color, fontFamily: FONT_MONO }}>{q.count}</div>
                <span style={{ fontSize: 12, color: COLOR.textFaint }}>{q.label}</span>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 4, padding: "10px 12px", border: `1px dashed ${COLOR.border}`, fontSize: 12, color: COLOR.textDim }}>
            <span style={{ color: COLOR.amber }}>queue</span>
            {"  ·  "}
            {preview ? `${preview.totalItems} item${preview.totalItems === 1 ? "" : "s"} scheduled - ${queueLimit} readiness slot${queueLimit === 1 ? "" : "s"}` : "loading scheduled items…"}
          </div>

          <div style={{ flex: 1 }} />
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 16 }}>
            <span style={{ padding: "8px 14px", border: `1px solid ${COLOR.border}`, fontSize: 13, color: COLOR.textDim, cursor: "pointer" }}>
              postpone
            </span>
            <span
              onClick={begin}
              style={{
                padding: "8px 18px",
                border: `1px solid ${COLOR.amber}`,
                background: "#241d12",
                color: COLOR.amber,
                fontSize: 13,
                fontWeight: 600,
                cursor: loading ? "wait" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                opacity: loading ? 0.7 : 1
              }}
            >
              {loading ? "starting…" : "begin session"}
              <span style={{ color: COLOR.amber }}>↵</span>
            </span>
          </div>
        </div>
      </div>

      <KeyBar
        keys={[
          { key: "↵", label: "begin session" },
          { key: "←/→", label: "adjust" },
          { key: "alt+1..8", label: "tabs" },
          { key: "^p", label: "palette" }
        ]}
        right={<StreakBadge streak={streak} />}
      />
    </div>
  );
}
