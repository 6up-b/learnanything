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
source_commit: "7f37f7bef54c4dc6170182720840faf546d9f51b"
source_commit_timestamp: "2026-09-03T10:56:04-07:00"
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
| Source lines | 1868 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7f37f7bef54c4dc6170182720840faf546d9f51b` |
| Commit timestamp | `2026-09-03T10:56:04-07:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]]

## Public API

- `export function StartScreen(` — function, line 1652

## Internal implementation anchors

- `const LOW_MASTERY_WORDS = [ "better", "oriented", "motivated", "prepared", "improve", "develop", "grow", "progress", "explore", "notice", "remember", "familiar", "grounded", "persistent", "unstuck", "ready" ]` — const, line 30
- `const HIGH_MASTERY_WORDS = [ "fluent", "sharp", "confident", "capable", "skilled", "proficient", "precise", "fast", "strong", "strategic", "insightful", "adaptive", "resourceful", "articulate", "analytical", "creative", "disciplined", "an expert", "masterful"…` — const, line 35
- `const GOD_WORD_HOLD_MS = 10_000` — const, line 42
- `const GLITCH_CHARS = "!<>-_\\/[]` — const, line 43
- `function useGlitchText(text: string)` — function, line 49
- `let dead = false` — let, line 59
- `const timers: number[] = []` — const, line 60
- `const randChar = ()` — const, line 61
- `const burst = (durationMs: number, decrypt: boolean, done?: ()` — const, line 63
- `const start = performance.now()` — const, line 64
- `const id = window.setInterval(()` — const, line 66
- `const t = (performance.now() - start) / durationMs` — const, line 68
- `const settled = decrypt ? t * text.length > i + Math.random() * 0.9 : Math.random() > 0.5` — const, line 81
- `const loop = ()` — const, line 92
- `const id = window.setTimeout( ()` — const, line 94
- `function GlitchText(` — function, line 114
- `function CyclingTypewriterText(` — function, line 123
- `const word = words[idx % words.length]` — const, line 135
- `const isGodWord = word.toLowerCase() === "god"` — const, line 136
- `const isGodRevealed = isGodWord && phase === "holding" && displayed === word` — const, line 137
- `const currentHoldMs = isGodWord ? GOD_WORD_HOLD_MS : holdMs` — const, line 138
- `const id = setTimeout(()` — const, line 148
- `const id = setTimeout(()` — const, line 152
- `const id = setTimeout(()` — const, line 157
- `const cursorColor = wordColor ?? "var(--text)"` — const, line 161
- `type BackdropName = | "lorenz" | "waves" | "fluid" | "torus" | "axes" | "tesseract" | "julia" | "life" | "clifford" | "pendulum" | "threebody"` — type, line 199
- `const BACKDROP_ORDER: BackdropName[] = [ "lorenz", "waves", "fluid", "torus", "axes", "tesseract", "julia", "life", "clifford", "pendulum", "threebody" ]` — const, line 202
- `function FluidBackdrop()` — function, line 210
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 211
- `const canvas = ref.current` — const, line 213
- `const ctx = canvas.getContext("2d")` — const, line 215
- `const P = readPaletteColors()` — const, line 217
- `const bgDeep = rgba(mixRgb(P.bg, BLACK, 0.55), 1)` — const, line 218
- `const blobs = [` — const, line 220
- `const reduce = prefersReducedMotion()` — const, line 227
- `let raf = 0` — let, line 229
- `let dpr = window.devicePixelRatio || 1` — let, line 230
- `function resize()` — function, line 231
- `const rect = canvas!.getBoundingClientRect()` — const, line 232
- `function drawFrame(ts: number)` — function, line 240
- `const w = canvas!.width / dpr` — const, line 241
- `const h = canvas!.height / dpr` — const, line 242
- `const R = Math.max(w, h)` — const, line 247
- `const cx = (b.x + 0.22 * Math.cos(ts * b.speed + b.phase)) * w` — const, line 249
- `const cy = (b.y + 0.22 * Math.sin(ts * b.speed * 1.3 + b.phase)) * h` — const, line 250
- `const r = R * b.radius` — const, line 251
- `const g = ctx!.createRadialGradient(cx, cy, 0, cx, cy, r)` — const, line 252
- `function frame(ts: number)` — function, line 261
- `const ro = new ResizeObserver(resize)` — const, line 266
- `function NoiseOverlay()` — function, line 282
- `const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'> <filter id='n' x='0' y='0' width='100%' height='100%'> <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/> <feColorMat…` — const, line 283
- `const dataUri = `url("data:image/svg+xml` — const, line 290
- `const CRT_SCANLINES: CSSProperties =` — const, line 307
- `type LorenzTr =` — type, line 316
- `function LorenzBackdrop(` — function, line 317
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 318
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 319
- `const densityRef = useRef(density)` — const, line 320
- `const intensityRef = useRef(intensity)` — const, line 321
- `const needsRebuildRef = useRef(false)` — const, line 322
- `const container = containerRef.current` — const, line 333
- `const canvas = canvasRef.current` — const, line 334
- `const ctx = canvas.getContext("2d")` — const, line 336
- `const CHAR_W = 7` — const, line 339
- `const CHAR_H = 12` — const, line 340
- `const SIGMA = 10` — const, line 341
- `const RHO = 28` — const, line 342
- `const BETA = 8 / 3` — const, line 343
- `const DT = 0.006` — const, line 344
- `const SUBSTEPS = 3` — const, line 345
- `const TRAIL_LEN = 110` — const, line 346
- `const CHARS = ".,-+*#@"` — const, line 347
- `let cols = 80` — let, line 349
- `let rows = 40` — let, line 350
- `let width = 0` — let, line 351
- `let height = 0` — let, line 352
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 353
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 354
- `let cells = new Uint16Array(0)` — let, line 355
- `let dimCodes = new Uint16Array(CHARS.length)` — let, line 356
- `let hotCodes = new Uint16Array(CHARS.length)` — let, line 357
- `let trajectories: LorenzTr[] = []` — let, line 358
- `function stepOnce(tr: LorenzTr)` — function, line 360
- `function makeTrajectories()` — function, line 367
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 369
- `const numHot = Math.max(1, Math.min(Math.ceil(total / 3), Math.round(total * 0.18)))` — const, line 370
- `const seed = i / Math.max(1, total - 1) - 0.5` — const, line 372
- `const reduce = prefersReducedMotion()` — const, line 392
- `const P = readPaletteColors()` — const, line 393
- `const dimColor = resolveCssColor( "color-mix(in srgb, var(--dim) 55%, transparent)", rgba(P.dim, 0.55) )` — const, line 394
- `const hotColor = resolveCssColor("var(--amber)", rgba(P.amber, 1))` — const, line 398
- `const hotGlow = resolveCssColor( "color-mix(in srgb, var(--amber) 55%, transparent)", rgba(P.amber, 0.55) )` — const, line 399
- `function rebuildAtlas()` — function, line 404
- `function renderFrame(simulationFrames = 1)` — function, line 420
- `const fill = intensityRef.current` — const, line 433
- `const SCALE_X = (cols * 0.42) / 25` — const, line 436
- `const SCALE_Z = (rows * 0.85) / 50` — const, line 437
- `const ORIGIN_X = cols * 0.5` — const, line 438
- `const ORIGIN_Y = rows * 0.88` — const, line 439
- `const len = tr.trail.length` — const, line 442
- `const p = tr.trail[i]` — const, line 445
- `const cx = Math.floor(ORIGIN_X + p[0] * SCALE_X)` — const, line 446
- `const cy = Math.floor(ORIGIN_Y - p[1] * SCALE_Z)` — const, line 447
- `const age = i / Math.max(1, len - 1)` — const, line 449
- `const ci = Math.min(CHARS.length - 1, Math.floor(age * CHARS.length))` — const, line 450
- `const index = cy * cols + cx` — const, line 451
- `function resize()` — function, line 461
- `const rect = container!.getBoundingClientRect()` — const, line 462
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 465
- `const dprChanged = nextDpr !== dpr` — const, line 466
- `const ro = new ResizeObserver(resize)` — const, line 481
- `let raf = 0` — let, line 484
- `let last = 0` — let, line 485
- `function draw(ts: number)` — function, line 486
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 491
- `function WaveBackdrop(` — function, line 516
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 517
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 518
- `const densityRef = useRef(density)` — const, line 519
- `const intensityRef = useRef(intensity)` — const, line 520
- `const needsRebuildRef = useRef(false)` — const, line 521
- `const container = containerRef.current` — const, line 532
- `const canvas = canvasRef.current` — const, line 533
- `const ctx = canvas.getContext("2d")` — const, line 535
- `const CHAR_W = 7` — const, line 538
- `const CHAR_H = 12` — const, line 539
- `let cols = 80` — let, line 541
- `let rows = 40` — let, line 542
- `let width = 0` — let, line 543
- `let height = 0` — let, line 544
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 545
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 546
- `let cells = new Uint16Array(0)` — let, line 547
- `const charCodes = new Map<string, number>()` — const, line 548
- `let mouse =` — let, line 549
- `let strings: CursedString[] = []` — let, line 550
- `const baseString = "LINEAR_ALGEBRA"` — const, line 552
- `let currentString = baseString` — let, line 553
- `const mutations: Array<(s: string)` — const, line 554
- `function mutateString()` — function, line 562
- `const fn = mutations[Math.floor(Math.random() * mutations.length)]` — const, line 563
- `class CursedString` — class, line 568
- `let y = this.baseY + Math.sin(x * this.wavelength + this.time * this.speed + this.offset) * this.amplitude` — let, line 593
- `const dx = x - mouse.x` — const, line 595
- `const dy = y - mouse.y` — const, line 596
- `const dist = Math.sqrt(dx * dx + dy * dy)` — const, line 597
- `function createStrings()` — function, line 603
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 605
- `const depth = 0.6 + Math.random() * 0.8` — const, line 607
- `const reduce = prefersReducedMotion()` — const, line 612
- `const glyphs = "LINEAR_GB03#"` — const, line 614
- `function rebuildAtlas()` — function, line 616
- `function resize()` — function, line 628
- `const rect = container!.getBoundingClientRect()` — const, line 629
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 632
- `const dprChanged = nextDpr !== dpr` — const, line 633
- `const ro = new ResizeObserver(resize)` — const, line 649
- `function onMove(e: MouseEvent)` — function, line 652
- `const rect = container!.getBoundingClientRect()` — const, line 653
- `function renderFrame(time: number)` — function, line 659
- `const fill = intensityRef.current` — const, line 664
- `const y = s.getY(x)` — const, line 669
- `const charIndex = (x + Math.floor(time * 0.01)) % currentString.length` — const, line 672
- `let char = currentString[charIndex]` — let, line 673
- `let raf = 0` — let, line 682
- `let lastMutation = 0` — let, line 683
- `let lastFrame = 0` — let, line 684
- `function draw(time: number)` — function, line 685
- `const TORUS_W = 60` — const, line 719
- `const TORUS_H = 26` — const, line 720
- `const RAMP = ".,-~:` — const, line 721
- `const RAMP_COLOR_INDEX = [0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]` — const, line 722
- `const TORUS_THETA = Array.from(` — const, line 723
- `const TORUS_PHI = Array.from(` — const, line 724
- `const TORUS_COS_THETA = TORUS_THETA.map(Math.cos)` — const, line 725
- `const TORUS_SIN_THETA = TORUS_THETA.map(Math.sin)` — const, line 726
- `const TORUS_COS_PHI = TORUS_PHI.map(Math.cos)` — const, line 727
- `const TORUS_SIN_PHI = TORUS_PHI.map(Math.sin)` — const, line 728
- `function Torus()` — function, line 729
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 730
- `const aRef = useRef(0)` — const, line 731
- `const bRef = useRef(0)` — const, line 732
- `const canvas = ref.current` — const, line 735
- `const ctx = canvas.getContext("2d")` — const, line 736
- `const reduce = prefersReducedMotion()` — const, line 738
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 739
- `const width = TORUS_W * 7` — const, line 740
- `const height = TORUS_H * 12` — const, line 741
- `const atlas = new MonospaceGlyphAtlas(` — const, line 747
- `const codes = new Uint16Array(RAMP.length)` — const, line 754
- `const buf = new Int8Array(TORUS_W * TORUS_H)` — const, line 756
- `const zbuf = new Float64Array(TORUS_W * TORUS_H)` — const, line 757
- `const cells = new Uint16Array(TORUS_W * TORUS_H)` — const, line 758
- `let raf = 0` — let, line 759
- `let last = 0` — let, line 760
- `function renderFrame(elapsed: number)` — function, line 761
- `const W = TORUS_W` — const, line 762
- `const H = TORUS_H` — const, line 763
- `const A = aRef.current` — const, line 767
- `const B = bRef.current` — const, line 768
- `const cosA = Math.cos(A)` — const, line 769
- `const sinA = Math.sin(A)` — const, line 770
- `const cosB = Math.cos(B)` — const, line 771
- `const sinB = Math.sin(B)` — const, line 772
- `const cosT = TORUS_COS_THETA[ti]` — const, line 774
- `const sinT = TORUS_SIN_THETA[ti]` — const, line 775
- `const cosP = TORUS_COS_PHI[pi]` — const, line 777
- `const sinP = TORUS_SIN_PHI[pi]` — const, line 778
- `const circleX = 2 + cosT` — const, line 779
- `const circleY = sinT` — const, line 780
- `const x = circleX * (cosB * cosP + sinA * sinB * sinP) - circleY * cosA * sinB` — const, line 781
- `const y = circleX * (sinB * cosP - sinA * cosB * sinP) + circleY * cosA * cosB` — const, line 782
- `const z = 5 + cosA * circleX * sinP + circleY * sinA` — const, line 783
- `const ooz = 1 / z` — const, line 784
- `const xp = Math.floor(W / 2 + 30 * ooz * x)` — const, line 785
- `const yp = Math.floor(H / 2 - 13 * ooz * y)` — const, line 786
- `const L = cosP * cosT * sinB - cosA * cosT * sinP - sinA * sinT + cosB * (cosA * sinT - cosT * sinA * sinP)` — const, line 787
- `const idx = xp + W * yp` — const, line 790
- `const lum = buf[i]` — const, line 799
- `const frameScale = elapsed / 33` — const, line 804
- `function frame(ts: number)` — function, line 808
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 813
- `function AxesBackdrop()` — function, line 842
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 843
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 844
- `const container = containerRef.current` — const, line 847
- `const canvas = canvasRef.current` — const, line 848
- `const ctx = canvas.getContext("2d")` — const, line 850
- `const CHAR_W = 7` — const, line 853
- `const CHAR_H = 12` — const, line 854
- `const AXIS_RAMP = ".:-=+*#"` — const, line 855
- `const GLYPHS = `$` — const, line 856
- `const AXES = [` — const, line 857
- `const P = readPaletteColors()` — const, line 863
- `const colors = [P.red, P.green, P.cyan, P.amber].map((color)` — const, line 864
- `const glow = resolveCssColor( "color-mix(in srgb, var(--amber) 25%, transparent)", rgba(P.amber, 0.25) )` — const, line 865
- `const reduce = prefersReducedMotion()` — const, line 869
- `let cols = 80` — let, line 870
- `let rows = 40` — let, line 871
- `let width = 0` — let, line 872
- `let height = 0` — let, line 873
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 874
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 875
- `let cells = new Uint16Array(0)` — let, line 876
- `let raf = 0` — let, line 877
- `let last = 0` — let, line 878
- `let yaw = 0.7` — let, line 879
- `const pitch = -0.5` — const, line 880
- `function rebuildAtlas()` — function, line 882
- `function resize()` — function, line 892
- `const rect = container!.getBoundingClientRect()` — const, line 893
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 896
- `const dprChanged = nextDpr !== dpr` — const, line 897
- `const ro = new ResizeObserver(()` — const, line 910
- `function rotate(p: number[], yaw: number, pitch: number)` — function, line 916
- `const cy = Math.cos(yaw)` — const, line 918
- `const sy = Math.sin(yaw)` — const, line 919
- `const x1 = x * cy + z * sy` — const, line 920
- `const z1 = -x * sy + z * cy` — const, line 921
- `const cp = Math.cos(pitch)` — const, line 922
- `const sp = Math.sin(pitch)` — const, line 923
- `const y2 = y * cp - z1 * sp` — const, line 924
- `const z2 = y * sp + z1 * cp` — const, line 925
- `function plot( x0: number, y0: number, x1: number, y1: number, colorIndex: number )` — function, line 929
- `const dx = x1 - x0` — const, line 936
- `const dy = y1 - y0` — const, line 937
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy)))` — const, line 938
- `const t = s / steps` — const, line 940
- `const xi = Math.round(x0 + dx * t)` — const, line 941
- `const yi = Math.round(y0 + dy * t)` — const, line 942
- `const ci = Math.min(AXIS_RAMP.length - 1, Math.floor(t * AXIS_RAMP.length))` — const, line 944
- `function draw(elapsed: number)` — function, line 949
- `const cx = cols / 2` — const, line 953
- `const cyy = rows / 2` — const, line 954
- `const scale = Math.min(cols, rows * 2) * 0.34` — const, line 955
- `const aspect = CHAR_W / CHAR_H` — const, line 956
- `const project = (p: number[])` — const, line 958
- `const txi = Math.round(tx)` — const, line 967
- `const tyi = Math.round(ty)` — const, line 968
- `const oxi = Math.round(ox)` — const, line 973
- `const oyi = Math.round(oy)` — const, line 974
- `function frame(ts: number)` — function, line 983
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 988
- `function TesseractBackdrop()` — function, line 1013
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 1014
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 1015
- `const container = containerRef.current` — const, line 1018
- `const canvas = canvasRef.current` — const, line 1019
- `const ctx = canvas.getContext("2d")` — const, line 1021
- `const CHAR_W = 7` — const, line 1024
- `const CHAR_H = 12` — const, line 1025
- `const CHARS = ".:-=+*#"` — const, line 1026
- `const AMBER_LEVELS = 6` — const, line 1027
- `const COLOR_BY_BRIGHTNESS = [0, 0, 1, 1, 2, 3]` — const, line 1028
- `type Edge =` — type, line 1030
- `const verts: number[][] = []` — const, line 1032
- `const edges: Edge[] = []` — const, line 1042
- `const j = i ^ (1 << bit)` — const, line 1045
- `let cols = 80` — let, line 1050
- `let rows = 40` — let, line 1051
- `let width = 0` — let, line 1052
- `let height = 0` — let, line 1053
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 1054
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 1055
- `let cells = new Uint16Array(0)` — let, line 1056
- `let zbuf = new Float64Array(0)` — let, line 1057
- `const reduce = prefersReducedMotion()` — const, line 1059
- `let raf = 0` — let, line 1060
- `let last = 0` — let, line 1061
- `let t = 0` — let, line 1062
- `const aspect = CHAR_W / CHAR_H` — const, line 1063
- `function rebuildAtlas()` — function, line 1065
- `function resize()` — function, line 1075
- `const rect = container!.getBoundingClientRect()` — const, line 1076
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1079
- `const dprChanged = nextDpr !== dpr` — const, line 1080
- `const ro = new ResizeObserver(()` — const, line 1095
- `function rotatePlane(p: number[], a: number, i: number, j: number)` — function, line 1101
- `const q = p.slice()` — const, line 1102
- `const c = Math.cos(a)` — const, line 1103
- `const s = Math.sin(a)` — const, line 1104
- `function rot4(p: number[], t: number)` — function, line 1110
- `let q = p` — let, line 1111
- `function draw(elapsed: number)` — function, line 1124
- `const D4 = 3.2` — const, line 1129
- `const D3 = 4.0` — const, line 1130
- `let dmin = Infinity` — let, line 1132
- `let dmax = -Infinity` — let, line 1133
- `const projected = verts.map((v)` — const, line 1135
- `const k4 = D4 / (D4 - w)` — const, line 1140
- `const x3 = x * k4` — const, line 1141
- `const y3 = y * k4` — const, line 1142
- `const z3 = z * k4` — const, line 1143
- `const k3 = D3 / (D3 - z3)` — const, line 1146
- `const sx = x3 * k3` — const, line 1147
- `const sy = y3 * k3` — const, line 1148
- `const depth = z3 + 0.35 * w` — const, line 1152
- `const scale = Math.min(cols, rows) * 0.26` — const, line 1161
- `const cx = cols / 2` — const, line 1162
- `const cy = rows / 2` — const, line 1163
- `function brightnessOf(depth: number, boost = 0)` — function, line 1165
- `const u = (depth - dmin) / Math.max(1e-6, dmax - dmin)` — const, line 1166
- `const b = Math.floor(u * (AMBER_LEVELS - 1)) + boost` — const, line 1167
- `const screen = projected.map((p)` — const, line 1171
- `function plot( x0: number, y0: number, z0: number, b0: number, x1: number, y1: number, z1: number, b1: number, isWConnector: boolean )` — function, line 1178
- `const dx = x1 - x0` — const, line 1189
- `const dy = y1 - y0` — const, line 1190
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy) * 1.25))` — const, line 1191
- `const u = s / steps` — const, line 1194
- `const xi = Math.round(x0 + dx * u)` — const, line 1196
- `const yi = Math.round(y0 + dy * u)` — const, line 1197
- `const z = z0 + (z1 - z0) * u` — const, line 1200
- `const index = yi * cols + xi` — const, line 1201
- `let bri = Math.round(b0 + (b1 - b0) * u)` — let, line 1205
- `const ci = Math.min( CHARS.length - 1, Math.floor((bri / (AMBER_LEVELS - 1)) * (CHARS.length - 1)) )` — const, line 1211
- `const a = screen[e.i]` — const, line 1221
- `const b = screen[e.j]` — const, line 1222
- `function frame(ts: number)` — function, line 1241
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 1246
- `function BackdropHeroText(` — function, line 1282
- `function StartDebugCycler(` — function, line 1366
- `const next = ()` — const, line 1368
- `const i = BACKDROP_ORDER.indexOf(backdrop)` — const, line 1369
- `function BackdropPanel(` — function, line 1410
- `let inner: ReactNode` — let, line 1429
- `function MonoSlider(` — function, line 1513
- `const filled = Math.round(value * width)` — const, line 1514
- `function MinutesPicker(` — function, line 1535
- `const presets = [10, 20, 30, 45, 60]` — const, line 1536
- `const sel = m === value` — const, line 1540
- `function energyBucket(value: number): "low" | "medium" | "high"` — function, line 1563
- `function readinessScore(energy: number, sleep: number, minutes: number): number` — function, line 1567
- `function readinessQueueLimit(energy: number, sleep: number, minutes: number): number` — function, line 1571
- `const score = readinessScore(energy, sleep, minutes)` — const, line 1572
- `const timeSlots = Math.max(1, Math.ceil(minutes / 5))` — const, line 1573
- `function titleCase(value: string): string` — function, line 1577
- `function vaultAlias(vault: VaultSummary | null): string` — function, line 1583
- `const basename = vault.root.replace(/\\/g, "/").split("/").filter(Boolean).pop() ?? ""` — const, line 1585
- `function StreakBadge(` — function, line 1594
- `function NewVaultAffordance(` — function, line 1622
- `const stored = localStorage.getItem("learnloop.startBackdrop")` — const, line 1666
- `const energyValue = energyBucket(energy)` — const, line 1674
- `const queueLimit = readinessQueueLimit(energy, sleep, minutes)` — const, line 1675
- `const readinessFactor = readinessScore(energy, sleep, minutes).toFixed(2)` — const, line 1676
- `const previewQuery = useCachedQuery( ["get_today_queue",` — const, line 1682
- `const preview: QueueSnapshot | null = previewQuery.data ?? null` — const, line 1687
- `const previewLoading = previewQuery.loading` — const, line 1688
- `const onKey = (event: KeyboardEvent)` — const, line 1699
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1700
- `async function begin()` — function, line 1711
- `const session = await api.startSession(` — const, line 1715
- `const items: ScheduledItemDto[] = preview?.sections.flatMap((section)` — const, line 1724
- `const masteryValues = items.filter((i)` — const, line 1726
- `const avgMastery = masteryValues.length > 0 ? masteryValues.reduce((a, b)` — const, line 1727
- `const masteryWords = avgMastery >= 0.65 ? HIGH_MASTERY_WORDS : LOW_MASTERY_WORDS` — const, line 1728
- `const queueSummary = [` — const, line 1730
- `const recommendedBudget = minutes <= 20 ? "short_session — probe_eig suppressed (≤20 min)" : minutes >= 45 ? "full_loop — probe_eig active" : "standard_loop — probe_eig active"` — const, line 1740
- `const now = new Date()` — const, line 1746
- `const dateLine = `$` — const, line 1747
- `const goalMeta = vault ? `$` — const, line 1751
- `const freshInstall = !vault || vault.counts.learningObjects === 0` — const, line 1755

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `StartScreen`; references `StartScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `QueueSnapshot`, `ScheduledItemDto`, `SessionSnapshot`, `StreakSummary`, `VaultSummary`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `TAG`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export; imports `useCachedQuery`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `KeyBar`, `SectionHeader`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/CliffordBackdrop|src/screens/startBackdrops/CliffordBackdrop.tsx]] — import-or-re-export; imports `CliffordBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]] — import-or-re-export; imports `JuliaBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/LifeBackdrop|src/screens/startBackdrops/LifeBackdrop.tsx]] — import-or-re-export; imports `LifeBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/PendulumBackdrop|src/screens/startBackdrops/PendulumBackdrop.tsx]] — import-or-re-export; imports `PendulumBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/ThreeBodyBackdrop|src/screens/startBackdrops/ThreeBodyBackdrop.tsx]] — import-or-re-export; imports `ThreeBodyBackdrop`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]] — import-or-re-export; imports `FULLSCREEN_CANVAS_STYLE`, `MonospaceGlyphAtlas`, `readAmberAtlasPalette`, `resolveCssColor`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]] — import-or-re-export; imports `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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
