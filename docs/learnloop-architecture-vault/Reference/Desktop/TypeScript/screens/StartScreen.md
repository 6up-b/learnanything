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
| Source lines | 1962 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]]

## Public API

- `export function minuteChoicesFor(summary: StartSummaryDto | null, minutes: number | null): number[]` — function, line 1536
- `export const STREAK_KEEP_LABEL = "begin a session today to keep your streak"` — const, line 1593
- `export const STREAK_KEEP_PLAN_LABEL = "begin today's plan to keep your streak"` — const, line 1595
- `export function StartScreen(` — function, line 1655

## Internal implementation anchors

- `const LOW_MASTERY_WORDS = [ "better", "oriented", "motivated", "prepared", "improve", "develop", "grow", "progress", "explore", "notice", "remember", "familiar", "grounded", "persistent", "unstuck", "ready" ]` — const, line 47
- `const HIGH_MASTERY_WORDS = [ "fluent", "sharp", "confident", "capable", "skilled", "proficient", "precise", "fast", "strong", "strategic", "insightful", "adaptive", "resourceful", "articulate", "analytical", "creative", "disciplined", "an expert", "masterful"…` — const, line 52
- `const GOD_WORD_HOLD_MS = 10_000` — const, line 59
- `const GLITCH_CHARS = "!<>-_\\/[]` — const, line 60
- `function useGlitchText(text: string)` — function, line 66
- `let dead = false` — let, line 76
- `const timers: number[] = []` — const, line 77
- `const randChar = ()` — const, line 78
- `const burst = (durationMs: number, decrypt: boolean, done?: ()` — const, line 80
- `const start = performance.now()` — const, line 81
- `const id = window.setInterval(()` — const, line 83
- `const t = (performance.now() - start) / durationMs` — const, line 85
- `const settled = decrypt ? t * text.length > i + Math.random() * 0.9 : Math.random() > 0.5` — const, line 98
- `const loop = ()` — const, line 109
- `const id = window.setTimeout( ()` — const, line 111
- `function GlitchText(` — function, line 131
- `function CyclingTypewriterText(` — function, line 140
- `const word = words[idx % words.length]` — const, line 152
- `const isGodWord = word.toLowerCase() === "god"` — const, line 153
- `const isGodRevealed = isGodWord && phase === "holding" && displayed === word` — const, line 154
- `const currentHoldMs = isGodWord ? GOD_WORD_HOLD_MS : holdMs` — const, line 155
- `const id = setTimeout(()` — const, line 165
- `const id = setTimeout(()` — const, line 169
- `const id = setTimeout(()` — const, line 174
- `const cursorColor = wordColor ?? "var(--text)"` — const, line 178
- `type BackdropName = | "lorenz" | "waves" | "fluid" | "torus" | "axes" | "tesseract" | "julia" | "life" | "clifford" | "pendulum" | "threebody"` — type, line 216
- `const BACKDROP_ORDER: BackdropName[] = [ "lorenz", "waves", "fluid", "torus", "axes", "tesseract", "julia", "life", "clifford", "pendulum", "threebody" ]` — const, line 219
- `function FluidBackdrop()` — function, line 227
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 228
- `const canvas = ref.current` — const, line 230
- `const ctx = canvas.getContext("2d")` — const, line 232
- `const P = readPaletteColors()` — const, line 234
- `const bgDeep = rgba(mixRgb(P.bg, BLACK, 0.55), 1)` — const, line 235
- `const blobs = [` — const, line 237
- `const reduce = prefersReducedMotion()` — const, line 244
- `let raf = 0` — let, line 246
- `let dpr = window.devicePixelRatio || 1` — let, line 247
- `function resize()` — function, line 248
- `const rect = canvas!.getBoundingClientRect()` — const, line 249
- `function drawFrame(ts: number)` — function, line 257
- `const w = canvas!.width / dpr` — const, line 258
- `const h = canvas!.height / dpr` — const, line 259
- `const R = Math.max(w, h)` — const, line 264
- `const cx = (b.x + 0.22 * Math.cos(ts * b.speed + b.phase)) * w` — const, line 266
- `const cy = (b.y + 0.22 * Math.sin(ts * b.speed * 1.3 + b.phase)) * h` — const, line 267
- `const r = R * b.radius` — const, line 268
- `const g = ctx!.createRadialGradient(cx, cy, 0, cx, cy, r)` — const, line 269
- `function frame(ts: number)` — function, line 278
- `const ro = new ResizeObserver(resize)` — const, line 283
- `function NoiseOverlay()` — function, line 299
- `const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'> <filter id='n' x='0' y='0' width='100%' height='100%'> <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/> <feColorMat…` — const, line 300
- `const dataUri = `url("data:image/svg+xml` — const, line 307
- `const CRT_SCANLINES: CSSProperties =` — const, line 324
- `type LorenzTr =` — type, line 333
- `function LorenzBackdrop(` — function, line 334
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 335
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 336
- `const densityRef = useRef(density)` — const, line 337
- `const intensityRef = useRef(intensity)` — const, line 338
- `const needsRebuildRef = useRef(false)` — const, line 339
- `const container = containerRef.current` — const, line 350
- `const canvas = canvasRef.current` — const, line 351
- `const ctx = canvas.getContext("2d")` — const, line 353
- `const CHAR_W = 7` — const, line 356
- `const CHAR_H = 12` — const, line 357
- `const SIGMA = 10` — const, line 358
- `const RHO = 28` — const, line 359
- `const BETA = 8 / 3` — const, line 360
- `const DT = 0.006` — const, line 361
- `const SUBSTEPS = 3` — const, line 362
- `const TRAIL_LEN = 110` — const, line 363
- `const CHARS = ".,-+*#@"` — const, line 364
- `let cols = 80` — let, line 366
- `let rows = 40` — let, line 367
- `let width = 0` — let, line 368
- `let height = 0` — let, line 369
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 370
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 371
- `let cells = new Uint16Array(0)` — let, line 372
- `let dimCodes = new Uint16Array(CHARS.length)` — let, line 373
- `let hotCodes = new Uint16Array(CHARS.length)` — let, line 374
- `let trajectories: LorenzTr[] = []` — let, line 375
- `function stepOnce(tr: LorenzTr)` — function, line 377
- `function makeTrajectories()` — function, line 384
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 386
- `const numHot = Math.max(1, Math.min(Math.ceil(total / 3), Math.round(total * 0.18)))` — const, line 387
- `const seed = i / Math.max(1, total - 1) - 0.5` — const, line 389
- `const reduce = prefersReducedMotion()` — const, line 409
- `const P = readPaletteColors()` — const, line 410
- `const dimColor = resolveCssColor( "color-mix(in srgb, var(--dim) 55%, transparent)", rgba(P.dim, 0.55) )` — const, line 411
- `const hotColor = resolveCssColor("var(--amber)", rgba(P.amber, 1))` — const, line 415
- `const hotGlow = resolveCssColor( "color-mix(in srgb, var(--amber) 55%, transparent)", rgba(P.amber, 0.55) )` — const, line 416
- `function rebuildAtlas()` — function, line 421
- `function renderFrame(simulationFrames = 1)` — function, line 437
- `const fill = intensityRef.current` — const, line 450
- `const SCALE_X = (cols * 0.42) / 25` — const, line 453
- `const SCALE_Z = (rows * 0.85) / 50` — const, line 454
- `const ORIGIN_X = cols * 0.5` — const, line 455
- `const ORIGIN_Y = rows * 0.88` — const, line 456
- `const len = tr.trail.length` — const, line 459
- `const p = tr.trail[i]` — const, line 462
- `const cx = Math.floor(ORIGIN_X + p[0] * SCALE_X)` — const, line 463
- `const cy = Math.floor(ORIGIN_Y - p[1] * SCALE_Z)` — const, line 464
- `const age = i / Math.max(1, len - 1)` — const, line 466
- `const ci = Math.min(CHARS.length - 1, Math.floor(age * CHARS.length))` — const, line 467
- `const index = cy * cols + cx` — const, line 468
- `function resize()` — function, line 478
- `const rect = container!.getBoundingClientRect()` — const, line 479
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 482
- `const dprChanged = nextDpr !== dpr` — const, line 483
- `const ro = new ResizeObserver(resize)` — const, line 498
- `let raf = 0` — let, line 501
- `let last = 0` — let, line 502
- `function draw(ts: number)` — function, line 503
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 508
- `function WaveBackdrop(` — function, line 533
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 534
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 535
- `const densityRef = useRef(density)` — const, line 536
- `const intensityRef = useRef(intensity)` — const, line 537
- `const needsRebuildRef = useRef(false)` — const, line 538
- `const container = containerRef.current` — const, line 549
- `const canvas = canvasRef.current` — const, line 550
- `const ctx = canvas.getContext("2d")` — const, line 552
- `const CHAR_W = 7` — const, line 555
- `const CHAR_H = 12` — const, line 556
- `let cols = 80` — let, line 558
- `let rows = 40` — let, line 559
- `let width = 0` — let, line 560
- `let height = 0` — let, line 561
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 562
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 563
- `let cells = new Uint16Array(0)` — let, line 564
- `const charCodes = new Map<string, number>()` — const, line 565
- `let mouse =` — let, line 566
- `let strings: CursedString[] = []` — let, line 567
- `const baseString = "LINEAR_ALGEBRA"` — const, line 569
- `let currentString = baseString` — let, line 570
- `const mutations: Array<(s: string)` — const, line 571
- `function mutateString()` — function, line 579
- `const fn = mutations[Math.floor(Math.random() * mutations.length)]` — const, line 580
- `class CursedString` — class, line 585
- `let y = this.baseY + Math.sin(x * this.wavelength + this.time * this.speed + this.offset) * this.amplitude` — let, line 610
- `const dx = x - mouse.x` — const, line 612
- `const dy = y - mouse.y` — const, line 613
- `const dist = Math.sqrt(dx * dx + dy * dy)` — const, line 614
- `function createStrings()` — function, line 620
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 622
- `const depth = 0.6 + Math.random() * 0.8` — const, line 624
- `const reduce = prefersReducedMotion()` — const, line 629
- `const glyphs = "LINEAR_GB03#"` — const, line 631
- `function rebuildAtlas()` — function, line 633
- `function resize()` — function, line 645
- `const rect = container!.getBoundingClientRect()` — const, line 646
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 649
- `const dprChanged = nextDpr !== dpr` — const, line 650
- `const ro = new ResizeObserver(resize)` — const, line 666
- `function onMove(e: MouseEvent)` — function, line 669
- `const rect = container!.getBoundingClientRect()` — const, line 670
- `function renderFrame(time: number)` — function, line 676
- `const fill = intensityRef.current` — const, line 681
- `const y = s.getY(x)` — const, line 686
- `const charIndex = (x + Math.floor(time * 0.01)) % currentString.length` — const, line 689
- `let char = currentString[charIndex]` — let, line 690
- `let raf = 0` — let, line 699
- `let lastMutation = 0` — let, line 700
- `let lastFrame = 0` — let, line 701
- `function draw(time: number)` — function, line 702
- `const TORUS_W = 60` — const, line 736
- `const TORUS_H = 26` — const, line 737
- `const RAMP = ".,-~:` — const, line 738
- `const RAMP_COLOR_INDEX = [0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]` — const, line 739
- `const TORUS_THETA = Array.from(` — const, line 740
- `const TORUS_PHI = Array.from(` — const, line 741
- `const TORUS_COS_THETA = TORUS_THETA.map(Math.cos)` — const, line 742
- `const TORUS_SIN_THETA = TORUS_THETA.map(Math.sin)` — const, line 743
- `const TORUS_COS_PHI = TORUS_PHI.map(Math.cos)` — const, line 744
- `const TORUS_SIN_PHI = TORUS_PHI.map(Math.sin)` — const, line 745
- `function Torus()` — function, line 746
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 747
- `const aRef = useRef(0)` — const, line 748
- `const bRef = useRef(0)` — const, line 749
- `const canvas = ref.current` — const, line 752
- `const ctx = canvas.getContext("2d")` — const, line 753
- `const reduce = prefersReducedMotion()` — const, line 755
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 756
- `const width = TORUS_W * 7` — const, line 757
- `const height = TORUS_H * 12` — const, line 758
- `const atlas = new MonospaceGlyphAtlas(` — const, line 764
- `const codes = new Uint16Array(RAMP.length)` — const, line 771
- `const buf = new Int8Array(TORUS_W * TORUS_H)` — const, line 773
- `const zbuf = new Float64Array(TORUS_W * TORUS_H)` — const, line 774
- `const cells = new Uint16Array(TORUS_W * TORUS_H)` — const, line 775
- `let raf = 0` — let, line 776
- `let last = 0` — let, line 777
- `function renderFrame(elapsed: number)` — function, line 778
- `const W = TORUS_W` — const, line 779
- `const H = TORUS_H` — const, line 780
- `const A = aRef.current` — const, line 784
- `const B = bRef.current` — const, line 785
- `const cosA = Math.cos(A)` — const, line 786
- `const sinA = Math.sin(A)` — const, line 787
- `const cosB = Math.cos(B)` — const, line 788
- `const sinB = Math.sin(B)` — const, line 789
- `const cosT = TORUS_COS_THETA[ti]` — const, line 791
- `const sinT = TORUS_SIN_THETA[ti]` — const, line 792
- `const cosP = TORUS_COS_PHI[pi]` — const, line 794
- `const sinP = TORUS_SIN_PHI[pi]` — const, line 795
- `const circleX = 2 + cosT` — const, line 796
- `const circleY = sinT` — const, line 797
- `const x = circleX * (cosB * cosP + sinA * sinB * sinP) - circleY * cosA * sinB` — const, line 798
- `const y = circleX * (sinB * cosP - sinA * cosB * sinP) + circleY * cosA * cosB` — const, line 799
- `const z = 5 + cosA * circleX * sinP + circleY * sinA` — const, line 800
- `const ooz = 1 / z` — const, line 801
- `const xp = Math.floor(W / 2 + 30 * ooz * x)` — const, line 802
- `const yp = Math.floor(H / 2 - 13 * ooz * y)` — const, line 803
- `const L = cosP * cosT * sinB - cosA * cosT * sinP - sinA * sinT + cosB * (cosA * sinT - cosT * sinA * sinP)` — const, line 804
- `const idx = xp + W * yp` — const, line 807
- `const lum = buf[i]` — const, line 816
- `const frameScale = elapsed / 33` — const, line 821
- `function frame(ts: number)` — function, line 825
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 830
- `function AxesBackdrop()` — function, line 859
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 860
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 861
- `const container = containerRef.current` — const, line 864
- `const canvas = canvasRef.current` — const, line 865
- `const ctx = canvas.getContext("2d")` — const, line 867
- `const CHAR_W = 7` — const, line 870
- `const CHAR_H = 12` — const, line 871
- `const AXIS_RAMP = ".:-=+*#"` — const, line 872
- `const GLYPHS = `$` — const, line 873
- `const AXES = [` — const, line 874
- `const P = readPaletteColors()` — const, line 880
- `const colors = [P.red, P.green, P.cyan, P.amber].map((color)` — const, line 881
- `const glow = resolveCssColor( "color-mix(in srgb, var(--amber) 25%, transparent)", rgba(P.amber, 0.25) )` — const, line 882
- `const reduce = prefersReducedMotion()` — const, line 886
- `let cols = 80` — let, line 887
- `let rows = 40` — let, line 888
- `let width = 0` — let, line 889
- `let height = 0` — let, line 890
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 891
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 892
- `let cells = new Uint16Array(0)` — let, line 893
- `let raf = 0` — let, line 894
- `let last = 0` — let, line 895
- `let yaw = 0.7` — let, line 896
- `const pitch = -0.5` — const, line 897
- `function rebuildAtlas()` — function, line 899
- `function resize()` — function, line 909
- `const rect = container!.getBoundingClientRect()` — const, line 910
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 913
- `const dprChanged = nextDpr !== dpr` — const, line 914
- `const ro = new ResizeObserver(()` — const, line 927
- `function rotate(p: number[], yaw: number, pitch: number)` — function, line 933
- `const cy = Math.cos(yaw)` — const, line 935
- `const sy = Math.sin(yaw)` — const, line 936
- `const x1 = x * cy + z * sy` — const, line 937
- `const z1 = -x * sy + z * cy` — const, line 938
- `const cp = Math.cos(pitch)` — const, line 939
- `const sp = Math.sin(pitch)` — const, line 940
- `const y2 = y * cp - z1 * sp` — const, line 941
- `const z2 = y * sp + z1 * cp` — const, line 942
- `function plot( x0: number, y0: number, x1: number, y1: number, colorIndex: number )` — function, line 946
- `const dx = x1 - x0` — const, line 953
- `const dy = y1 - y0` — const, line 954
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy)))` — const, line 955
- `const t = s / steps` — const, line 957
- `const xi = Math.round(x0 + dx * t)` — const, line 958
- `const yi = Math.round(y0 + dy * t)` — const, line 959
- `const ci = Math.min(AXIS_RAMP.length - 1, Math.floor(t * AXIS_RAMP.length))` — const, line 961
- `function draw(elapsed: number)` — function, line 966
- `const cx = cols / 2` — const, line 970
- `const cyy = rows / 2` — const, line 971
- `const scale = Math.min(cols, rows * 2) * 0.34` — const, line 972
- `const aspect = CHAR_W / CHAR_H` — const, line 973
- `const project = (p: number[])` — const, line 975
- `const txi = Math.round(tx)` — const, line 984
- `const tyi = Math.round(ty)` — const, line 985
- `const oxi = Math.round(ox)` — const, line 990
- `const oyi = Math.round(oy)` — const, line 991
- `function frame(ts: number)` — function, line 1000
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 1005
- `function TesseractBackdrop()` — function, line 1030
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 1031
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 1032
- `const container = containerRef.current` — const, line 1035
- `const canvas = canvasRef.current` — const, line 1036
- `const ctx = canvas.getContext("2d")` — const, line 1038
- `const CHAR_W = 7` — const, line 1041
- `const CHAR_H = 12` — const, line 1042
- `const CHARS = ".:-=+*#"` — const, line 1043
- `const AMBER_LEVELS = 6` — const, line 1044
- `const COLOR_BY_BRIGHTNESS = [0, 0, 1, 1, 2, 3]` — const, line 1045
- `type Edge =` — type, line 1047
- `const verts: number[][] = []` — const, line 1049
- `const edges: Edge[] = []` — const, line 1059
- `const j = i ^ (1 << bit)` — const, line 1062
- `let cols = 80` — let, line 1067
- `let rows = 40` — let, line 1068
- `let width = 0` — let, line 1069
- `let height = 0` — let, line 1070
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 1071
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 1072
- `let cells = new Uint16Array(0)` — let, line 1073
- `let zbuf = new Float64Array(0)` — let, line 1074
- `const reduce = prefersReducedMotion()` — const, line 1076
- `let raf = 0` — let, line 1077
- `let last = 0` — let, line 1078
- `let t = 0` — let, line 1079
- `const aspect = CHAR_W / CHAR_H` — const, line 1080
- `function rebuildAtlas()` — function, line 1082
- `function resize()` — function, line 1092
- `const rect = container!.getBoundingClientRect()` — const, line 1093
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1096
- `const dprChanged = nextDpr !== dpr` — const, line 1097
- `const ro = new ResizeObserver(()` — const, line 1112
- `function rotatePlane(p: number[], a: number, i: number, j: number)` — function, line 1118
- `const q = p.slice()` — const, line 1119
- `const c = Math.cos(a)` — const, line 1120
- `const s = Math.sin(a)` — const, line 1121
- `function rot4(p: number[], t: number)` — function, line 1127
- `let q = p` — let, line 1128
- `function draw(elapsed: number)` — function, line 1141
- `const D4 = 3.2` — const, line 1146
- `const D3 = 4.0` — const, line 1147
- `let dmin = Infinity` — let, line 1149
- `let dmax = -Infinity` — let, line 1150
- `const projected = verts.map((v)` — const, line 1152
- `const k4 = D4 / (D4 - w)` — const, line 1157
- `const x3 = x * k4` — const, line 1158
- `const y3 = y * k4` — const, line 1159
- `const z3 = z * k4` — const, line 1160
- `const k3 = D3 / (D3 - z3)` — const, line 1163
- `const sx = x3 * k3` — const, line 1164
- `const sy = y3 * k3` — const, line 1165
- `const depth = z3 + 0.35 * w` — const, line 1169
- `const scale = Math.min(cols, rows) * 0.26` — const, line 1178
- `const cx = cols / 2` — const, line 1179
- `const cy = rows / 2` — const, line 1180
- `function brightnessOf(depth: number, boost = 0)` — function, line 1182
- `const u = (depth - dmin) / Math.max(1e-6, dmax - dmin)` — const, line 1183
- `const b = Math.floor(u * (AMBER_LEVELS - 1)) + boost` — const, line 1184
- `const screen = projected.map((p)` — const, line 1188
- `function plot( x0: number, y0: number, z0: number, b0: number, x1: number, y1: number, z1: number, b1: number, isWConnector: boolean )` — function, line 1195
- `const dx = x1 - x0` — const, line 1206
- `const dy = y1 - y0` — const, line 1207
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy) * 1.25))` — const, line 1208
- `const u = s / steps` — const, line 1211
- `const xi = Math.round(x0 + dx * u)` — const, line 1213
- `const yi = Math.round(y0 + dy * u)` — const, line 1214
- `const z = z0 + (z1 - z0) * u` — const, line 1217
- `const index = yi * cols + xi` — const, line 1218
- `let bri = Math.round(b0 + (b1 - b0) * u)` — let, line 1222
- `const ci = Math.min( CHARS.length - 1, Math.floor((bri / (AMBER_LEVELS - 1)) * (CHARS.length - 1)) )` — const, line 1228
- `const a = screen[e.i]` — const, line 1238
- `const b = screen[e.j]` — const, line 1239
- `function frame(ts: number)` — function, line 1258
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 1263
- `function BackdropHeroText(` — function, line 1299
- `function StartDebugCycler(` — function, line 1383
- `const next = ()` — const, line 1385
- `const i = BACKDROP_ORDER.indexOf(backdrop)` — const, line 1386
- `function BackdropPanel(` — function, line 1427
- `let inner: ReactNode` — let, line 1446
- `const DEFAULT_MINUTE_PRESETS = [10, 15, 25, 40, 60]` — const, line 1531
- `const FIRST_RUN_MINUTES = 25` — const, line 1533
- `const base = summary?.minuteChoices ?? summary?.minutesPresets ?? DEFAULT_MINUTE_PRESETS` — const, line 1537
- `const values = new Set(base)` — const, line 1538
- `function MinutesPicker(` — function, line 1543
- `const sel = m === value` — const, line 1547
- `function titleCase(value: string): string` — function, line 1572
- `function vaultAlias(vault: VaultSummary | null): string` — function, line 1578
- `const basename = vault.root.replace(/\\/g, "/").split("/").filter(Boolean).pop() ?? ""` — const, line 1580
- `const STREAK_COUNTS_TITLE = "counts the days on which you began a session"` — const, line 1596
- `function StreakBadge(` — function, line 1598
- `const keepLabel = plan ? STREAK_KEEP_PLAN_LABEL : STREAK_KEEP_LABEL` — const, line 1600
- `function NewVaultAffordance(` — function, line 1625
- `const stored = localStorage.getItem("learnloop.startBackdrop")` — const, line 1670
- `const summaryQuery = useCachedQuery(["get_start_summary"], ()` — const, line 1677
- `const summary: StartSummaryDto | null = summaryQuery.data ?? null` — const, line 1678
- `const summaryState = peek<StartSummaryDto>(["get_start_summary"])` — const, line 1681
- `const summaryCurrent = summary !== null && summaryState.invalidatedAt <= summaryState.updatedAt` — const, line 1682
- `const streak = summary?.streak ?? snapshotStreak` — const, line 1683
- `const rememberedMinutes = summaryCurrent ? summary.rememberedMinutes : summaryQuery.error ? FIRST_RUN_MINUTES : null` — const, line 1687
- `const planQuery = useDailyPlan(null)` — const, line 1695
- `const planKnown = planQuery.data !== undefined || planQuery.error !== null` — const, line 1696
- `const plan = planQuery.data?.enabled ? planQuery.data.plan : null` — const, line 1697
- `const minutes = plan ? plan.rememberedMinutes : chosenMinutes ?? rememberedMinutes` — const, line 1699
- `const choices = plan ? plan.minuteChoices : minuteChoicesFor(summaryCurrent ? summary : null, minutes)` — const, line 1700
- `const previewInput: QueueInput | null = minutes == null || !planKnown || plan ? null :` — const, line 1706
- `const previewQuery = useCachedQuery( previewInput ? ["get_today_queue", previewInput] : null, ()` — const, line 1707
- `const preview: QueueSnapshot | null = previewQuery.data ?? lastPreview` — const, line 1716
- `const previewIsPrevious = previewQuery.data === undefined && lastPreview !== null` — const, line 1717
- `const previewLoading = plan ? false : minutes == null || !planKnown || previewQuery.loading` — const, line 1718
- `function chooseMinutes(next: number)` — function, line 1732
- `function stepMinutes(delta: number)` — function, line 1746
- `const index = choices.indexOf(minutes)` — const, line 1748
- `const next = choices[Math.max(0, Math.min(choices.length - 1, (index < 0 ? 0 : index) + delta))]` — const, line 1749
- `const onKey = (event: KeyboardEvent)` — const, line 1754
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1756
- `async function begin()` — function, line 1772
- `const session = await startSessionOrAsk(` — const, line 1777
- `const first = await api.nextPlanItem(` — const, line 1781
- `const items: ScheduledItemDto[] = preview?.sections.flatMap((section)` — const, line 1793
- `const masteryValues = items.filter((i)` — const, line 1795
- `const avgMastery = masteryValues.length > 0 ? masteryValues.reduce((a, b)` — const, line 1796
- `const masteryWords = avgMastery >= 0.65 ? HIGH_MASTERY_WORDS : LOW_MASTERY_WORDS` — const, line 1797
- `const queueSummary = [` — const, line 1799
- `const recommendedBudget = minutes == null ? "—" : minutes <= 20 ? "short_session — probe_eig suppressed (≤20 min)" : minutes >= 45 ? "full_loop — probe_eig active" : "standard_loop — probe_eig active"` — const, line 1808
- `const now = new Date()` — const, line 1816
- `const dateLine = `$` — const, line 1817
- `const goalMeta = vault ? `$` — const, line 1821
- `const freshInstall = !vault || vault.counts.learningObjects === 0` — const, line 1825
- `const minutesNote = plan ? "today's plan · one tap changes the minutes, remembered next time" : summary?.minutesSource === "last_session" && chosenMinutes == null ? "minutes from your last session · one tap changes them" : "pick today's minutes · they are rem…` — const, line 1830

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
- [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]] — import-or-re-export; imports `startSessionOrAsk`
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
