---
title: "Desktop module · src/screens/StartScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.StartScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/StartScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/StartScreen.tsx"
source_commit: "c94882abe7a8f5a7cde491603d6abba8a4c0e2db"
source_commit_timestamp: "2026-10-22T16:58:30-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/StartScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `StartScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/StartScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/StartScreen.tsx) |
| Source lines | 1960 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c94882abe7a8f5a7cde491603d6abba8a4c0e2db` |
| Commit timestamp | `2026-10-22T16:58:30-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]]

## Public API

- `export function minuteChoicesFor(summary: StartSummaryDto | null, minutes: number | null): number[]` — function, line 1535
- `export const STREAK_KEEP_LABEL = "begin a session today to keep your streak"` — const, line 1592
- `export const STREAK_KEEP_PLAN_LABEL = "begin today's plan to keep your streak"` — const, line 1594
- `export function StartScreen(` — function, line 1654

## Internal implementation anchors

- `const LOW_MASTERY_WORDS = [ "better", "oriented", "motivated", "prepared", "improve", "develop", "grow", "progress", "explore", "notice", "remember", "familiar", "grounded", "persistent", "unstuck", "ready" ]` — const, line 46
- `const HIGH_MASTERY_WORDS = [ "fluent", "sharp", "confident", "capable", "skilled", "proficient", "precise", "fast", "strong", "strategic", "insightful", "adaptive", "resourceful", "articulate", "analytical", "creative", "disciplined", "an expert", "masterful"…` — const, line 51
- `const GOD_WORD_HOLD_MS = 10_000` — const, line 58
- `const GLITCH_CHARS = "!<>-_\\/[]` — const, line 59
- `function useGlitchText(text: string)` — function, line 65
- `let dead = false` — let, line 75
- `const timers: number[] = []` — const, line 76
- `const randChar = ()` — const, line 77
- `const burst = (durationMs: number, decrypt: boolean, done?: ()` — const, line 79
- `const start = performance.now()` — const, line 80
- `const id = window.setInterval(()` — const, line 82
- `const t = (performance.now() - start) / durationMs` — const, line 84
- `const settled = decrypt ? t * text.length > i + Math.random() * 0.9 : Math.random() > 0.5` — const, line 97
- `const loop = ()` — const, line 108
- `const id = window.setTimeout( ()` — const, line 110
- `function GlitchText(` — function, line 130
- `function CyclingTypewriterText(` — function, line 139
- `const word = words[idx % words.length]` — const, line 151
- `const isGodWord = word.toLowerCase() === "god"` — const, line 152
- `const isGodRevealed = isGodWord && phase === "holding" && displayed === word` — const, line 153
- `const currentHoldMs = isGodWord ? GOD_WORD_HOLD_MS : holdMs` — const, line 154
- `const id = setTimeout(()` — const, line 164
- `const id = setTimeout(()` — const, line 168
- `const id = setTimeout(()` — const, line 173
- `const cursorColor = wordColor ?? "var(--text)"` — const, line 177
- `type BackdropName = | "lorenz" | "waves" | "fluid" | "torus" | "axes" | "tesseract" | "julia" | "life" | "clifford" | "pendulum" | "threebody"` — type, line 215
- `const BACKDROP_ORDER: BackdropName[] = [ "lorenz", "waves", "fluid", "torus", "axes", "tesseract", "julia", "life", "clifford", "pendulum", "threebody" ]` — const, line 218
- `function FluidBackdrop()` — function, line 226
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 227
- `const canvas = ref.current` — const, line 229
- `const ctx = canvas.getContext("2d")` — const, line 231
- `const P = readPaletteColors()` — const, line 233
- `const bgDeep = rgba(mixRgb(P.bg, BLACK, 0.55), 1)` — const, line 234
- `const blobs = [` — const, line 236
- `const reduce = prefersReducedMotion()` — const, line 243
- `let raf = 0` — let, line 245
- `let dpr = window.devicePixelRatio || 1` — let, line 246
- `function resize()` — function, line 247
- `const rect = canvas!.getBoundingClientRect()` — const, line 248
- `function drawFrame(ts: number)` — function, line 256
- `const w = canvas!.width / dpr` — const, line 257
- `const h = canvas!.height / dpr` — const, line 258
- `const R = Math.max(w, h)` — const, line 263
- `const cx = (b.x + 0.22 * Math.cos(ts * b.speed + b.phase)) * w` — const, line 265
- `const cy = (b.y + 0.22 * Math.sin(ts * b.speed * 1.3 + b.phase)) * h` — const, line 266
- `const r = R * b.radius` — const, line 267
- `const g = ctx!.createRadialGradient(cx, cy, 0, cx, cy, r)` — const, line 268
- `function frame(ts: number)` — function, line 277
- `const ro = new ResizeObserver(resize)` — const, line 282
- `function NoiseOverlay()` — function, line 298
- `const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'> <filter id='n' x='0' y='0' width='100%' height='100%'> <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/> <feColorMat…` — const, line 299
- `const dataUri = `url("data:image/svg+xml` — const, line 306
- `const CRT_SCANLINES: CSSProperties =` — const, line 323
- `type LorenzTr =` — type, line 332
- `function LorenzBackdrop(` — function, line 333
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 334
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 335
- `const densityRef = useRef(density)` — const, line 336
- `const intensityRef = useRef(intensity)` — const, line 337
- `const needsRebuildRef = useRef(false)` — const, line 338
- `const container = containerRef.current` — const, line 349
- `const canvas = canvasRef.current` — const, line 350
- `const ctx = canvas.getContext("2d")` — const, line 352
- `const CHAR_W = 7` — const, line 355
- `const CHAR_H = 12` — const, line 356
- `const SIGMA = 10` — const, line 357
- `const RHO = 28` — const, line 358
- `const BETA = 8 / 3` — const, line 359
- `const DT = 0.006` — const, line 360
- `const SUBSTEPS = 3` — const, line 361
- `const TRAIL_LEN = 110` — const, line 362
- `const CHARS = ".,-+*#@"` — const, line 363
- `let cols = 80` — let, line 365
- `let rows = 40` — let, line 366
- `let width = 0` — let, line 367
- `let height = 0` — let, line 368
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 369
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 370
- `let cells = new Uint16Array(0)` — let, line 371
- `let dimCodes = new Uint16Array(CHARS.length)` — let, line 372
- `let hotCodes = new Uint16Array(CHARS.length)` — let, line 373
- `let trajectories: LorenzTr[] = []` — let, line 374
- `function stepOnce(tr: LorenzTr)` — function, line 376
- `function makeTrajectories()` — function, line 383
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 385
- `const numHot = Math.max(1, Math.min(Math.ceil(total / 3), Math.round(total * 0.18)))` — const, line 386
- `const seed = i / Math.max(1, total - 1) - 0.5` — const, line 388
- `const reduce = prefersReducedMotion()` — const, line 408
- `const P = readPaletteColors()` — const, line 409
- `const dimColor = resolveCssColor( "color-mix(in srgb, var(--dim) 55%, transparent)", rgba(P.dim, 0.55) )` — const, line 410
- `const hotColor = resolveCssColor("var(--amber)", rgba(P.amber, 1))` — const, line 414
- `const hotGlow = resolveCssColor( "color-mix(in srgb, var(--amber) 55%, transparent)", rgba(P.amber, 0.55) )` — const, line 415
- `function rebuildAtlas()` — function, line 420
- `function renderFrame(simulationFrames = 1)` — function, line 436
- `const fill = intensityRef.current` — const, line 449
- `const SCALE_X = (cols * 0.42) / 25` — const, line 452
- `const SCALE_Z = (rows * 0.85) / 50` — const, line 453
- `const ORIGIN_X = cols * 0.5` — const, line 454
- `const ORIGIN_Y = rows * 0.88` — const, line 455
- `const len = tr.trail.length` — const, line 458
- `const p = tr.trail[i]` — const, line 461
- `const cx = Math.floor(ORIGIN_X + p[0] * SCALE_X)` — const, line 462
- `const cy = Math.floor(ORIGIN_Y - p[1] * SCALE_Z)` — const, line 463
- `const age = i / Math.max(1, len - 1)` — const, line 465
- `const ci = Math.min(CHARS.length - 1, Math.floor(age * CHARS.length))` — const, line 466
- `const index = cy * cols + cx` — const, line 467
- `function resize()` — function, line 477
- `const rect = container!.getBoundingClientRect()` — const, line 478
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 481
- `const dprChanged = nextDpr !== dpr` — const, line 482
- `const ro = new ResizeObserver(resize)` — const, line 497
- `let raf = 0` — let, line 500
- `let last = 0` — let, line 501
- `function draw(ts: number)` — function, line 502
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 507
- `function WaveBackdrop(` — function, line 532
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 533
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 534
- `const densityRef = useRef(density)` — const, line 535
- `const intensityRef = useRef(intensity)` — const, line 536
- `const needsRebuildRef = useRef(false)` — const, line 537
- `const container = containerRef.current` — const, line 548
- `const canvas = canvasRef.current` — const, line 549
- `const ctx = canvas.getContext("2d")` — const, line 551
- `const CHAR_W = 7` — const, line 554
- `const CHAR_H = 12` — const, line 555
- `let cols = 80` — let, line 557
- `let rows = 40` — let, line 558
- `let width = 0` — let, line 559
- `let height = 0` — let, line 560
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 561
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 562
- `let cells = new Uint16Array(0)` — let, line 563
- `const charCodes = new Map<string, number>()` — const, line 564
- `let mouse =` — let, line 565
- `let strings: CursedString[] = []` — let, line 566
- `const baseString = "LINEAR_ALGEBRA"` — const, line 568
- `let currentString = baseString` — let, line 569
- `const mutations: Array<(s: string)` — const, line 570
- `function mutateString()` — function, line 578
- `const fn = mutations[Math.floor(Math.random() * mutations.length)]` — const, line 579
- `class CursedString` — class, line 584
- `let y = this.baseY + Math.sin(x * this.wavelength + this.time * this.speed + this.offset) * this.amplitude` — let, line 609
- `const dx = x - mouse.x` — const, line 611
- `const dy = y - mouse.y` — const, line 612
- `const dist = Math.sqrt(dx * dx + dy * dy)` — const, line 613
- `function createStrings()` — function, line 619
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 621
- `const depth = 0.6 + Math.random() * 0.8` — const, line 623
- `const reduce = prefersReducedMotion()` — const, line 628
- `const glyphs = "LINEAR_GB03#"` — const, line 630
- `function rebuildAtlas()` — function, line 632
- `function resize()` — function, line 644
- `const rect = container!.getBoundingClientRect()` — const, line 645
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 648
- `const dprChanged = nextDpr !== dpr` — const, line 649
- `const ro = new ResizeObserver(resize)` — const, line 665
- `function onMove(e: MouseEvent)` — function, line 668
- `const rect = container!.getBoundingClientRect()` — const, line 669
- `function renderFrame(time: number)` — function, line 675
- `const fill = intensityRef.current` — const, line 680
- `const y = s.getY(x)` — const, line 685
- `const charIndex = (x + Math.floor(time * 0.01)) % currentString.length` — const, line 688
- `let char = currentString[charIndex]` — let, line 689
- `let raf = 0` — let, line 698
- `let lastMutation = 0` — let, line 699
- `let lastFrame = 0` — let, line 700
- `function draw(time: number)` — function, line 701
- `const TORUS_W = 60` — const, line 735
- `const TORUS_H = 26` — const, line 736
- `const RAMP = ".,-~:` — const, line 737
- `const RAMP_COLOR_INDEX = [0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]` — const, line 738
- `const TORUS_THETA = Array.from(` — const, line 739
- `const TORUS_PHI = Array.from(` — const, line 740
- `const TORUS_COS_THETA = TORUS_THETA.map(Math.cos)` — const, line 741
- `const TORUS_SIN_THETA = TORUS_THETA.map(Math.sin)` — const, line 742
- `const TORUS_COS_PHI = TORUS_PHI.map(Math.cos)` — const, line 743
- `const TORUS_SIN_PHI = TORUS_PHI.map(Math.sin)` — const, line 744
- `function Torus()` — function, line 745
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 746
- `const aRef = useRef(0)` — const, line 747
- `const bRef = useRef(0)` — const, line 748
- `const canvas = ref.current` — const, line 751
- `const ctx = canvas.getContext("2d")` — const, line 752
- `const reduce = prefersReducedMotion()` — const, line 754
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 755
- `const width = TORUS_W * 7` — const, line 756
- `const height = TORUS_H * 12` — const, line 757
- `const atlas = new MonospaceGlyphAtlas(` — const, line 763
- `const codes = new Uint16Array(RAMP.length)` — const, line 770
- `const buf = new Int8Array(TORUS_W * TORUS_H)` — const, line 772
- `const zbuf = new Float64Array(TORUS_W * TORUS_H)` — const, line 773
- `const cells = new Uint16Array(TORUS_W * TORUS_H)` — const, line 774
- `let raf = 0` — let, line 775
- `let last = 0` — let, line 776
- `function renderFrame(elapsed: number)` — function, line 777
- `const W = TORUS_W` — const, line 778
- `const H = TORUS_H` — const, line 779
- `const A = aRef.current` — const, line 783
- `const B = bRef.current` — const, line 784
- `const cosA = Math.cos(A)` — const, line 785
- `const sinA = Math.sin(A)` — const, line 786
- `const cosB = Math.cos(B)` — const, line 787
- `const sinB = Math.sin(B)` — const, line 788
- `const cosT = TORUS_COS_THETA[ti]` — const, line 790
- `const sinT = TORUS_SIN_THETA[ti]` — const, line 791
- `const cosP = TORUS_COS_PHI[pi]` — const, line 793
- `const sinP = TORUS_SIN_PHI[pi]` — const, line 794
- `const circleX = 2 + cosT` — const, line 795
- `const circleY = sinT` — const, line 796
- `const x = circleX * (cosB * cosP + sinA * sinB * sinP) - circleY * cosA * sinB` — const, line 797
- `const y = circleX * (sinB * cosP - sinA * cosB * sinP) + circleY * cosA * cosB` — const, line 798
- `const z = 5 + cosA * circleX * sinP + circleY * sinA` — const, line 799
- `const ooz = 1 / z` — const, line 800
- `const xp = Math.floor(W / 2 + 30 * ooz * x)` — const, line 801
- `const yp = Math.floor(H / 2 - 13 * ooz * y)` — const, line 802
- `const L = cosP * cosT * sinB - cosA * cosT * sinP - sinA * sinT + cosB * (cosA * sinT - cosT * sinA * sinP)` — const, line 803
- `const idx = xp + W * yp` — const, line 806
- `const lum = buf[i]` — const, line 815
- `const frameScale = elapsed / 33` — const, line 820
- `function frame(ts: number)` — function, line 824
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 829
- `function AxesBackdrop()` — function, line 858
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 859
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 860
- `const container = containerRef.current` — const, line 863
- `const canvas = canvasRef.current` — const, line 864
- `const ctx = canvas.getContext("2d")` — const, line 866
- `const CHAR_W = 7` — const, line 869
- `const CHAR_H = 12` — const, line 870
- `const AXIS_RAMP = ".:-=+*#"` — const, line 871
- `const GLYPHS = `$` — const, line 872
- `const AXES = [` — const, line 873
- `const P = readPaletteColors()` — const, line 879
- `const colors = [P.red, P.green, P.cyan, P.amber].map((color)` — const, line 880
- `const glow = resolveCssColor( "color-mix(in srgb, var(--amber) 25%, transparent)", rgba(P.amber, 0.25) )` — const, line 881
- `const reduce = prefersReducedMotion()` — const, line 885
- `let cols = 80` — let, line 886
- `let rows = 40` — let, line 887
- `let width = 0` — let, line 888
- `let height = 0` — let, line 889
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 890
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 891
- `let cells = new Uint16Array(0)` — let, line 892
- `let raf = 0` — let, line 893
- `let last = 0` — let, line 894
- `let yaw = 0.7` — let, line 895
- `const pitch = -0.5` — const, line 896
- `function rebuildAtlas()` — function, line 898
- `function resize()` — function, line 908
- `const rect = container!.getBoundingClientRect()` — const, line 909
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 912
- `const dprChanged = nextDpr !== dpr` — const, line 913
- `const ro = new ResizeObserver(()` — const, line 926
- `function rotate(p: number[], yaw: number, pitch: number)` — function, line 932
- `const cy = Math.cos(yaw)` — const, line 934
- `const sy = Math.sin(yaw)` — const, line 935
- `const x1 = x * cy + z * sy` — const, line 936
- `const z1 = -x * sy + z * cy` — const, line 937
- `const cp = Math.cos(pitch)` — const, line 938
- `const sp = Math.sin(pitch)` — const, line 939
- `const y2 = y * cp - z1 * sp` — const, line 940
- `const z2 = y * sp + z1 * cp` — const, line 941
- `function plot( x0: number, y0: number, x1: number, y1: number, colorIndex: number )` — function, line 945
- `const dx = x1 - x0` — const, line 952
- `const dy = y1 - y0` — const, line 953
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy)))` — const, line 954
- `const t = s / steps` — const, line 956
- `const xi = Math.round(x0 + dx * t)` — const, line 957
- `const yi = Math.round(y0 + dy * t)` — const, line 958
- `const ci = Math.min(AXIS_RAMP.length - 1, Math.floor(t * AXIS_RAMP.length))` — const, line 960
- `function draw(elapsed: number)` — function, line 965
- `const cx = cols / 2` — const, line 969
- `const cyy = rows / 2` — const, line 970
- `const scale = Math.min(cols, rows * 2) * 0.34` — const, line 971
- `const aspect = CHAR_W / CHAR_H` — const, line 972
- `const project = (p: number[])` — const, line 974
- `const txi = Math.round(tx)` — const, line 983
- `const tyi = Math.round(ty)` — const, line 984
- `const oxi = Math.round(ox)` — const, line 989
- `const oyi = Math.round(oy)` — const, line 990
- `function frame(ts: number)` — function, line 999
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 1004
- `function TesseractBackdrop()` — function, line 1029
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 1030
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 1031
- `const container = containerRef.current` — const, line 1034
- `const canvas = canvasRef.current` — const, line 1035
- `const ctx = canvas.getContext("2d")` — const, line 1037
- `const CHAR_W = 7` — const, line 1040
- `const CHAR_H = 12` — const, line 1041
- `const CHARS = ".:-=+*#"` — const, line 1042
- `const AMBER_LEVELS = 6` — const, line 1043
- `const COLOR_BY_BRIGHTNESS = [0, 0, 1, 1, 2, 3]` — const, line 1044
- `type Edge =` — type, line 1046
- `const verts: number[][] = []` — const, line 1048
- `const edges: Edge[] = []` — const, line 1058
- `const j = i ^ (1 << bit)` — const, line 1061
- `let cols = 80` — let, line 1066
- `let rows = 40` — let, line 1067
- `let width = 0` — let, line 1068
- `let height = 0` — let, line 1069
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 1070
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 1071
- `let cells = new Uint16Array(0)` — let, line 1072
- `let zbuf = new Float64Array(0)` — let, line 1073
- `const reduce = prefersReducedMotion()` — const, line 1075
- `let raf = 0` — let, line 1076
- `let last = 0` — let, line 1077
- `let t = 0` — let, line 1078
- `const aspect = CHAR_W / CHAR_H` — const, line 1079
- `function rebuildAtlas()` — function, line 1081
- `function resize()` — function, line 1091
- `const rect = container!.getBoundingClientRect()` — const, line 1092
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1095
- `const dprChanged = nextDpr !== dpr` — const, line 1096
- `const ro = new ResizeObserver(()` — const, line 1111
- `function rotatePlane(p: number[], a: number, i: number, j: number)` — function, line 1117
- `const q = p.slice()` — const, line 1118
- `const c = Math.cos(a)` — const, line 1119
- `const s = Math.sin(a)` — const, line 1120
- `function rot4(p: number[], t: number)` — function, line 1126
- `let q = p` — let, line 1127
- `function draw(elapsed: number)` — function, line 1140
- `const D4 = 3.2` — const, line 1145
- `const D3 = 4.0` — const, line 1146
- `let dmin = Infinity` — let, line 1148
- `let dmax = -Infinity` — let, line 1149
- `const projected = verts.map((v)` — const, line 1151
- `const k4 = D4 / (D4 - w)` — const, line 1156
- `const x3 = x * k4` — const, line 1157
- `const y3 = y * k4` — const, line 1158
- `const z3 = z * k4` — const, line 1159
- `const k3 = D3 / (D3 - z3)` — const, line 1162
- `const sx = x3 * k3` — const, line 1163
- `const sy = y3 * k3` — const, line 1164
- `const depth = z3 + 0.35 * w` — const, line 1168
- `const scale = Math.min(cols, rows) * 0.26` — const, line 1177
- `const cx = cols / 2` — const, line 1178
- `const cy = rows / 2` — const, line 1179
- `function brightnessOf(depth: number, boost = 0)` — function, line 1181
- `const u = (depth - dmin) / Math.max(1e-6, dmax - dmin)` — const, line 1182
- `const b = Math.floor(u * (AMBER_LEVELS - 1)) + boost` — const, line 1183
- `const screen = projected.map((p)` — const, line 1187
- `function plot( x0: number, y0: number, z0: number, b0: number, x1: number, y1: number, z1: number, b1: number, isWConnector: boolean )` — function, line 1194
- `const dx = x1 - x0` — const, line 1205
- `const dy = y1 - y0` — const, line 1206
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy) * 1.25))` — const, line 1207
- `const u = s / steps` — const, line 1210
- `const xi = Math.round(x0 + dx * u)` — const, line 1212
- `const yi = Math.round(y0 + dy * u)` — const, line 1213
- `const z = z0 + (z1 - z0) * u` — const, line 1216
- `const index = yi * cols + xi` — const, line 1217
- `let bri = Math.round(b0 + (b1 - b0) * u)` — let, line 1221
- `const ci = Math.min( CHARS.length - 1, Math.floor((bri / (AMBER_LEVELS - 1)) * (CHARS.length - 1)) )` — const, line 1227
- `const a = screen[e.i]` — const, line 1237
- `const b = screen[e.j]` — const, line 1238
- `function frame(ts: number)` — function, line 1257
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 1262
- `function BackdropHeroText(` — function, line 1298
- `function StartDebugCycler(` — function, line 1382
- `const next = ()` — const, line 1384
- `const i = BACKDROP_ORDER.indexOf(backdrop)` — const, line 1385
- `function BackdropPanel(` — function, line 1426
- `let inner: ReactNode` — let, line 1445
- `const DEFAULT_MINUTE_PRESETS = [10, 15, 25, 40, 60]` — const, line 1530
- `const FIRST_RUN_MINUTES = 25` — const, line 1532
- `const base = summary?.minuteChoices ?? summary?.minutesPresets ?? DEFAULT_MINUTE_PRESETS` — const, line 1536
- `const values = new Set(base)` — const, line 1537
- `function MinutesPicker(` — function, line 1542
- `const sel = m === value` — const, line 1546
- `function titleCase(value: string): string` — function, line 1571
- `function vaultAlias(vault: VaultSummary | null): string` — function, line 1577
- `const basename = vault.root.replace(/\\/g, "/").split("/").filter(Boolean).pop() ?? ""` — const, line 1579
- `const STREAK_COUNTS_TITLE = "counts the days on which you began a session"` — const, line 1595
- `function StreakBadge(` — function, line 1597
- `const keepLabel = plan ? STREAK_KEEP_PLAN_LABEL : STREAK_KEEP_LABEL` — const, line 1599
- `function NewVaultAffordance(` — function, line 1624
- `const stored = localStorage.getItem("learnloop.startBackdrop")` — const, line 1669
- `const summaryQuery = useCachedQuery(["get_start_summary"], ()` — const, line 1676
- `const summary: StartSummaryDto | null = summaryQuery.data ?? null` — const, line 1677
- `const summaryState = peek<StartSummaryDto>(["get_start_summary"])` — const, line 1680
- `const summaryCurrent = summary !== null && summaryState.invalidatedAt <= summaryState.updatedAt` — const, line 1681
- `const streak = summary?.streak ?? snapshotStreak` — const, line 1682
- `const rememberedMinutes = summaryCurrent ? summary.rememberedMinutes : summaryQuery.error ? FIRST_RUN_MINUTES : null` — const, line 1686
- `const planQuery = useDailyPlan(null)` — const, line 1694
- `const planKnown = planQuery.data !== undefined || planQuery.error !== null` — const, line 1695
- `const plan = planQuery.data?.enabled ? planQuery.data.plan : null` — const, line 1696
- `const minutes = plan ? plan.rememberedMinutes : chosenMinutes ?? rememberedMinutes` — const, line 1698
- `const choices = plan ? plan.minuteChoices : minuteChoicesFor(summaryCurrent ? summary : null, minutes)` — const, line 1699
- `const previewInput: QueueInput | null = minutes == null || !planKnown || plan ? null :` — const, line 1705
- `const previewQuery = useCachedQuery( previewInput ? ["get_today_queue", previewInput] : null, ()` — const, line 1706
- `const preview: QueueSnapshot | null = previewQuery.data ?? lastPreview` — const, line 1715
- `const previewIsPrevious = previewQuery.data === undefined && lastPreview !== null` — const, line 1716
- `const previewLoading = plan ? false : minutes == null || !planKnown || previewQuery.loading` — const, line 1717
- `function chooseMinutes(next: number)` — function, line 1731
- `function stepMinutes(delta: number)` — function, line 1745
- `const index = choices.indexOf(minutes)` — const, line 1747
- `const next = choices[Math.max(0, Math.min(choices.length - 1, (index < 0 ? 0 : index) + delta))]` — const, line 1748
- `const onKey = (event: KeyboardEvent)` — const, line 1753
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1755
- `async function begin()` — function, line 1771
- `const session = await api.startSession(` — const, line 1776
- `const first = await api.nextPlanItem(` — const, line 1779
- `const items: ScheduledItemDto[] = preview?.sections.flatMap((section)` — const, line 1791
- `const masteryValues = items.filter((i)` — const, line 1793
- `const avgMastery = masteryValues.length > 0 ? masteryValues.reduce((a, b)` — const, line 1794
- `const masteryWords = avgMastery >= 0.65 ? HIGH_MASTERY_WORDS : LOW_MASTERY_WORDS` — const, line 1795
- `const queueSummary = [` — const, line 1797
- `const recommendedBudget = minutes == null ? "—" : minutes <= 20 ? "short_session — probe_eig suppressed (≤20 min)" : minutes >= 45 ? "full_loop — probe_eig active" : "standard_loop — probe_eig active"` — const, line 1806
- `const now = new Date()` — const, line 1814
- `const dateLine = `$` — const, line 1815
- `const goalMeta = vault ? `$` — const, line 1819
- `const freshInstall = !vault || vault.counts.learningObjects === 0` — const, line 1823
- `const minutesNote = plan ? "today's plan · one tap changes the minutes, remembered next time" : summary?.minutesSource === "last_session" && chosenMinutes == null ? "minutes from your last session · one tap changes them" : "pick today's minutes · they are rem…` — const, line 1828

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `StartScreen`; references `StartScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PlanStepDto`, `QueueInput`, `QueueSnapshot`, `ScheduledItemDto`, `SessionSnapshot`, `StartSummaryDto`, `StreakSummary`, `VaultSummary`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `peek`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `aboutMinutes`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `KeyBar`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/CliffordBackdrop|src/screens/startBackdrops/CliffordBackdrop.tsx]] — import-or-re-export; imports `CliffordBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]] — import-or-re-export; imports `JuliaBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/LifeBackdrop|src/screens/startBackdrops/LifeBackdrop.tsx]] — import-or-re-export; imports `LifeBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/PendulumBackdrop|src/screens/startBackdrops/PendulumBackdrop.tsx]] — import-or-re-export; imports `PendulumBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/ThreeBodyBackdrop|src/screens/startBackdrops/ThreeBodyBackdrop.tsx]] — import-or-re-export; imports `ThreeBodyBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]] — import-or-re-export; imports `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`, `resolveCssColor`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`
- [[Reference/Desktop/TypeScript/screens/today/DailyPlanView|src/screens/today/DailyPlanView.tsx]] — import-or-re-export; imports `PlanSplitLine`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/StartScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/StartScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_daily_loop_start_minutes.py](../../../../../../tests/test_daily_loop_start_minutes.py) — cross-boundary name contract: references uniquely owned exported name `StartScreen`; it does **not** directly execute this source module.
- [tests/test_daily_loop_start_postpone.py](../../../../../../tests/test_daily_loop_start_postpone.py) — cross-boundary name contract: references uniquely owned exported name `StartScreen`; it does **not** directly execute this source module.
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — cross-boundary name contract: references uniquely owned exported name `StartScreen`; it does **not** directly execute this source module.
- [tests/test_tui_app.py](../../../../../../tests/test_tui_app.py) — cross-boundary name contract: references uniquely owned exported name `StartScreen`; it does **not** directly execute this source module.
- [tests/test_tui_theme.py](../../../../../../tests/test_tui_theme.py) — cross-boundary name contract: references uniquely owned exported name `StartScreen`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/StartScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/StartScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
