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
source_commit: "4bfee21b99e126a187df694660dbff4f7bb6cbea"
source_commit_timestamp: "2026-07-27T07:17:49-04:00"
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
| Source lines | 1882 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `4bfee21b99e126a187df694660dbff4f7bb6cbea` |
| Commit timestamp | `2026-07-27T07:17:49-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]]

## Public API

- `export function StartScreen(` — function, line 1650

## Internal implementation anchors

- `const LOW_MASTERY_WORDS = [ "better", "oriented", "motivated", "prepared", "improve", "develop", "grow", "progress", "explore", "notice", "remember", "familiar", "grounded", "persistent", "unstuck", "ready" ]` — const, line 28
- `const HIGH_MASTERY_WORDS = [ "fluent", "sharp", "confident", "capable", "skilled", "proficient", "precise", "fast", "strong", "strategic", "insightful", "adaptive", "resourceful", "articulate", "analytical", "creative", "disciplined", "an expert", "masterful"…` — const, line 33
- `const GOD_WORD_HOLD_MS = 10_000` — const, line 40
- `const GLITCH_CHARS = "!<>-_\\/[]` — const, line 41
- `function useGlitchText(text: string)` — function, line 47
- `let dead = false` — let, line 57
- `const timers: number[] = []` — const, line 58
- `const randChar = ()` — const, line 59
- `const burst = (durationMs: number, decrypt: boolean, done?: ()` — const, line 61
- `const start = performance.now()` — const, line 62
- `const id = window.setInterval(()` — const, line 64
- `const t = (performance.now() - start) / durationMs` — const, line 66
- `const settled = decrypt ? t * text.length > i + Math.random() * 0.9 : Math.random() > 0.5` — const, line 79
- `const loop = ()` — const, line 90
- `const id = window.setTimeout( ()` — const, line 92
- `function GlitchText(` — function, line 112
- `function CyclingTypewriterText(` — function, line 121
- `const word = words[idx % words.length]` — const, line 133
- `const isGodWord = word.toLowerCase() === "god"` — const, line 134
- `const isGodRevealed = isGodWord && phase === "holding" && displayed === word` — const, line 135
- `const currentHoldMs = isGodWord ? GOD_WORD_HOLD_MS : holdMs` — const, line 136
- `const id = setTimeout(()` — const, line 146
- `const id = setTimeout(()` — const, line 150
- `const id = setTimeout(()` — const, line 155
- `const cursorColor = wordColor ?? "var(--text)"` — const, line 159
- `type BackdropName = | "lorenz" | "waves" | "fluid" | "torus" | "axes" | "tesseract" | "julia" | "life" | "clifford" | "pendulum" | "threebody"` — type, line 197
- `const BACKDROP_ORDER: BackdropName[] = [ "lorenz", "waves", "fluid", "torus", "axes", "tesseract", "julia", "life", "clifford", "pendulum", "threebody" ]` — const, line 200
- `function FluidBackdrop()` — function, line 208
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 209
- `const canvas = ref.current` — const, line 211
- `const ctx = canvas.getContext("2d")` — const, line 213
- `const P = readPaletteColors()` — const, line 215
- `const bgDeep = rgba(mixRgb(P.bg, BLACK, 0.55), 1)` — const, line 216
- `const blobs = [` — const, line 218
- `const reduce = prefersReducedMotion()` — const, line 225
- `let raf = 0` — let, line 227
- `let dpr = window.devicePixelRatio || 1` — let, line 228
- `function resize()` — function, line 229
- `const rect = canvas!.getBoundingClientRect()` — const, line 230
- `function drawFrame(ts: number)` — function, line 238
- `const w = canvas!.width / dpr` — const, line 239
- `const h = canvas!.height / dpr` — const, line 240
- `const R = Math.max(w, h)` — const, line 245
- `const cx = (b.x + 0.22 * Math.cos(ts * b.speed + b.phase)) * w` — const, line 247
- `const cy = (b.y + 0.22 * Math.sin(ts * b.speed * 1.3 + b.phase)) * h` — const, line 248
- `const r = R * b.radius` — const, line 249
- `const g = ctx!.createRadialGradient(cx, cy, 0, cx, cy, r)` — const, line 250
- `function frame(ts: number)` — function, line 259
- `const ro = new ResizeObserver(resize)` — const, line 264
- `function NoiseOverlay()` — function, line 280
- `const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'> <filter id='n' x='0' y='0' width='100%' height='100%'> <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/> <feColorMat…` — const, line 281
- `const dataUri = `url("data:image/svg+xml` — const, line 288
- `const CRT_SCANLINES: CSSProperties =` — const, line 305
- `type LorenzTr =` — type, line 314
- `function LorenzBackdrop(` — function, line 315
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 316
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 317
- `const densityRef = useRef(density)` — const, line 318
- `const intensityRef = useRef(intensity)` — const, line 319
- `const needsRebuildRef = useRef(false)` — const, line 320
- `const container = containerRef.current` — const, line 331
- `const canvas = canvasRef.current` — const, line 332
- `const ctx = canvas.getContext("2d")` — const, line 334
- `const CHAR_W = 7` — const, line 337
- `const CHAR_H = 12` — const, line 338
- `const SIGMA = 10` — const, line 339
- `const RHO = 28` — const, line 340
- `const BETA = 8 / 3` — const, line 341
- `const DT = 0.006` — const, line 342
- `const SUBSTEPS = 3` — const, line 343
- `const TRAIL_LEN = 110` — const, line 344
- `const CHARS = ".,-+*#@"` — const, line 345
- `let cols = 80` — let, line 347
- `let rows = 40` — let, line 348
- `let width = 0` — let, line 349
- `let height = 0` — let, line 350
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 351
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 352
- `let cells = new Uint16Array(0)` — let, line 353
- `let dimCodes = new Uint16Array(CHARS.length)` — let, line 354
- `let hotCodes = new Uint16Array(CHARS.length)` — let, line 355
- `let trajectories: LorenzTr[] = []` — let, line 356
- `function stepOnce(tr: LorenzTr)` — function, line 358
- `function makeTrajectories()` — function, line 365
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 367
- `const numHot = Math.max(1, Math.min(Math.ceil(total / 3), Math.round(total * 0.18)))` — const, line 368
- `const seed = i / Math.max(1, total - 1) - 0.5` — const, line 370
- `const reduce = prefersReducedMotion()` — const, line 390
- `const P = readPaletteColors()` — const, line 391
- `const dimColor = resolveCssColor( "color-mix(in srgb, var(--dim) 55%, transparent)", rgba(P.dim, 0.55) )` — const, line 392
- `const hotColor = resolveCssColor("var(--amber)", rgba(P.amber, 1))` — const, line 396
- `const hotGlow = resolveCssColor( "color-mix(in srgb, var(--amber) 55%, transparent)", rgba(P.amber, 0.55) )` — const, line 397
- `function rebuildAtlas()` — function, line 402
- `function renderFrame(simulationFrames = 1)` — function, line 418
- `const fill = intensityRef.current` — const, line 431
- `const SCALE_X = (cols * 0.42) / 25` — const, line 434
- `const SCALE_Z = (rows * 0.85) / 50` — const, line 435
- `const ORIGIN_X = cols * 0.5` — const, line 436
- `const ORIGIN_Y = rows * 0.88` — const, line 437
- `const len = tr.trail.length` — const, line 440
- `const p = tr.trail[i]` — const, line 443
- `const cx = Math.floor(ORIGIN_X + p[0] * SCALE_X)` — const, line 444
- `const cy = Math.floor(ORIGIN_Y - p[1] * SCALE_Z)` — const, line 445
- `const age = i / Math.max(1, len - 1)` — const, line 447
- `const ci = Math.min(CHARS.length - 1, Math.floor(age * CHARS.length))` — const, line 448
- `const index = cy * cols + cx` — const, line 449
- `function resize()` — function, line 459
- `const rect = container!.getBoundingClientRect()` — const, line 460
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 463
- `const dprChanged = nextDpr !== dpr` — const, line 464
- `const ro = new ResizeObserver(resize)` — const, line 479
- `let raf = 0` — let, line 482
- `let last = 0` — let, line 483
- `function draw(ts: number)` — function, line 484
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 489
- `function WaveBackdrop(` — function, line 514
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 515
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 516
- `const densityRef = useRef(density)` — const, line 517
- `const intensityRef = useRef(intensity)` — const, line 518
- `const needsRebuildRef = useRef(false)` — const, line 519
- `const container = containerRef.current` — const, line 530
- `const canvas = canvasRef.current` — const, line 531
- `const ctx = canvas.getContext("2d")` — const, line 533
- `const CHAR_W = 7` — const, line 536
- `const CHAR_H = 12` — const, line 537
- `let cols = 80` — let, line 539
- `let rows = 40` — let, line 540
- `let width = 0` — let, line 541
- `let height = 0` — let, line 542
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 543
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 544
- `let cells = new Uint16Array(0)` — let, line 545
- `const charCodes = new Map<string, number>()` — const, line 546
- `let mouse =` — let, line 547
- `let strings: CursedString[] = []` — let, line 548
- `const baseString = "LINEAR_ALGEBRA"` — const, line 550
- `let currentString = baseString` — let, line 551
- `const mutations: Array<(s: string)` — const, line 552
- `function mutateString()` — function, line 560
- `const fn = mutations[Math.floor(Math.random() * mutations.length)]` — const, line 561
- `class CursedString` — class, line 566
- `let y = this.baseY + Math.sin(x * this.wavelength + this.time * this.speed + this.offset) * this.amplitude` — let, line 591
- `const dx = x - mouse.x` — const, line 593
- `const dy = y - mouse.y` — const, line 594
- `const dist = Math.sqrt(dx * dx + dy * dy)` — const, line 595
- `function createStrings()` — function, line 601
- `const total = Math.max(2, Math.round(densityRef.current))` — const, line 603
- `const depth = 0.6 + Math.random() * 0.8` — const, line 605
- `const reduce = prefersReducedMotion()` — const, line 610
- `const glyphs = "LINEAR_GB03#"` — const, line 612
- `function rebuildAtlas()` — function, line 614
- `function resize()` — function, line 626
- `const rect = container!.getBoundingClientRect()` — const, line 627
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 630
- `const dprChanged = nextDpr !== dpr` — const, line 631
- `const ro = new ResizeObserver(resize)` — const, line 647
- `function onMove(e: MouseEvent)` — function, line 650
- `const rect = container!.getBoundingClientRect()` — const, line 651
- `function renderFrame(time: number)` — function, line 657
- `const fill = intensityRef.current` — const, line 662
- `const y = s.getY(x)` — const, line 667
- `const charIndex = (x + Math.floor(time * 0.01)) % currentString.length` — const, line 670
- `let char = currentString[charIndex]` — let, line 671
- `let raf = 0` — let, line 680
- `let lastMutation = 0` — let, line 681
- `let lastFrame = 0` — let, line 682
- `function draw(time: number)` — function, line 683
- `const TORUS_W = 60` — const, line 717
- `const TORUS_H = 26` — const, line 718
- `const RAMP = ".,-~:` — const, line 719
- `const RAMP_COLOR_INDEX = [0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]` — const, line 720
- `const TORUS_THETA = Array.from(` — const, line 721
- `const TORUS_PHI = Array.from(` — const, line 722
- `const TORUS_COS_THETA = TORUS_THETA.map(Math.cos)` — const, line 723
- `const TORUS_SIN_THETA = TORUS_THETA.map(Math.sin)` — const, line 724
- `const TORUS_COS_PHI = TORUS_PHI.map(Math.cos)` — const, line 725
- `const TORUS_SIN_PHI = TORUS_PHI.map(Math.sin)` — const, line 726
- `function Torus()` — function, line 727
- `const ref = useRef<HTMLCanvasElement>(null)` — const, line 728
- `const aRef = useRef(0)` — const, line 729
- `const bRef = useRef(0)` — const, line 730
- `const canvas = ref.current` — const, line 733
- `const ctx = canvas.getContext("2d")` — const, line 734
- `const reduce = prefersReducedMotion()` — const, line 736
- `const dpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 737
- `const width = TORUS_W * 7` — const, line 738
- `const height = TORUS_H * 12` — const, line 739
- `const atlas = new MonospaceGlyphAtlas(` — const, line 745
- `const codes = new Uint16Array(RAMP.length)` — const, line 752
- `const buf = new Int8Array(TORUS_W * TORUS_H)` — const, line 754
- `const zbuf = new Float64Array(TORUS_W * TORUS_H)` — const, line 755
- `const cells = new Uint16Array(TORUS_W * TORUS_H)` — const, line 756
- `let raf = 0` — let, line 757
- `let last = 0` — let, line 758
- `function renderFrame(elapsed: number)` — function, line 759
- `const W = TORUS_W` — const, line 760
- `const H = TORUS_H` — const, line 761
- `const A = aRef.current` — const, line 765
- `const B = bRef.current` — const, line 766
- `const cosA = Math.cos(A)` — const, line 767
- `const sinA = Math.sin(A)` — const, line 768
- `const cosB = Math.cos(B)` — const, line 769
- `const sinB = Math.sin(B)` — const, line 770
- `const cosT = TORUS_COS_THETA[ti]` — const, line 772
- `const sinT = TORUS_SIN_THETA[ti]` — const, line 773
- `const cosP = TORUS_COS_PHI[pi]` — const, line 775
- `const sinP = TORUS_SIN_PHI[pi]` — const, line 776
- `const circleX = 2 + cosT` — const, line 777
- `const circleY = sinT` — const, line 778
- `const x = circleX * (cosB * cosP + sinA * sinB * sinP) - circleY * cosA * sinB` — const, line 779
- `const y = circleX * (sinB * cosP - sinA * cosB * sinP) + circleY * cosA * cosB` — const, line 780
- `const z = 5 + cosA * circleX * sinP + circleY * sinA` — const, line 781
- `const ooz = 1 / z` — const, line 782
- `const xp = Math.floor(W / 2 + 30 * ooz * x)` — const, line 783
- `const yp = Math.floor(H / 2 - 13 * ooz * y)` — const, line 784
- `const L = cosP * cosT * sinB - cosA * cosT * sinP - sinA * sinT + cosB * (cosA * sinT - cosT * sinA * sinP)` — const, line 785
- `const idx = xp + W * yp` — const, line 788
- `const lum = buf[i]` — const, line 797
- `const frameScale = elapsed / 33` — const, line 802
- `function frame(ts: number)` — function, line 806
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 811
- `function AxesBackdrop()` — function, line 840
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 841
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 842
- `const container = containerRef.current` — const, line 845
- `const canvas = canvasRef.current` — const, line 846
- `const ctx = canvas.getContext("2d")` — const, line 848
- `const CHAR_W = 7` — const, line 851
- `const CHAR_H = 12` — const, line 852
- `const AXIS_RAMP = ".:-=+*#"` — const, line 853
- `const GLYPHS = `$` — const, line 854
- `const AXES = [` — const, line 855
- `const P = readPaletteColors()` — const, line 861
- `const colors = [P.red, P.green, P.cyan, P.amber].map((color)` — const, line 862
- `const glow = resolveCssColor( "color-mix(in srgb, var(--amber) 25%, transparent)", rgba(P.amber, 0.25) )` — const, line 863
- `const reduce = prefersReducedMotion()` — const, line 867
- `let cols = 80` — let, line 868
- `let rows = 40` — let, line 869
- `let width = 0` — let, line 870
- `let height = 0` — let, line 871
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 872
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 873
- `let cells = new Uint16Array(0)` — let, line 874
- `let raf = 0` — let, line 875
- `let last = 0` — let, line 876
- `let yaw = 0.7` — let, line 877
- `const pitch = -0.5` — const, line 878
- `function rebuildAtlas()` — function, line 880
- `function resize()` — function, line 890
- `const rect = container!.getBoundingClientRect()` — const, line 891
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 894
- `const dprChanged = nextDpr !== dpr` — const, line 895
- `const ro = new ResizeObserver(()` — const, line 908
- `function rotate(p: number[], yaw: number, pitch: number)` — function, line 914
- `const cy = Math.cos(yaw)` — const, line 916
- `const sy = Math.sin(yaw)` — const, line 917
- `const x1 = x * cy + z * sy` — const, line 918
- `const z1 = -x * sy + z * cy` — const, line 919
- `const cp = Math.cos(pitch)` — const, line 920
- `const sp = Math.sin(pitch)` — const, line 921
- `const y2 = y * cp - z1 * sp` — const, line 922
- `const z2 = y * sp + z1 * cp` — const, line 923
- `function plot( x0: number, y0: number, x1: number, y1: number, colorIndex: number )` — function, line 927
- `const dx = x1 - x0` — const, line 934
- `const dy = y1 - y0` — const, line 935
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy)))` — const, line 936
- `const t = s / steps` — const, line 938
- `const xi = Math.round(x0 + dx * t)` — const, line 939
- `const yi = Math.round(y0 + dy * t)` — const, line 940
- `const ci = Math.min(AXIS_RAMP.length - 1, Math.floor(t * AXIS_RAMP.length))` — const, line 942
- `function draw(elapsed: number)` — function, line 947
- `const cx = cols / 2` — const, line 951
- `const cyy = rows / 2` — const, line 952
- `const scale = Math.min(cols, rows * 2) * 0.34` — const, line 953
- `const aspect = CHAR_W / CHAR_H` — const, line 954
- `const project = (p: number[])` — const, line 956
- `const txi = Math.round(tx)` — const, line 965
- `const tyi = Math.round(ty)` — const, line 966
- `const oxi = Math.round(ox)` — const, line 971
- `const oyi = Math.round(oy)` — const, line 972
- `function frame(ts: number)` — function, line 981
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 986
- `function TesseractBackdrop()` — function, line 1011
- `const containerRef = useRef<HTMLDivElement>(null)` — const, line 1012
- `const canvasRef = useRef<HTMLCanvasElement>(null)` — const, line 1013
- `const container = containerRef.current` — const, line 1016
- `const canvas = canvasRef.current` — const, line 1017
- `const ctx = canvas.getContext("2d")` — const, line 1019
- `const CHAR_W = 7` — const, line 1022
- `const CHAR_H = 12` — const, line 1023
- `const CHARS = ".:-=+*#"` — const, line 1024
- `const AMBER_LEVELS = 6` — const, line 1025
- `const COLOR_BY_BRIGHTNESS = [0, 0, 1, 1, 2, 3]` — const, line 1026
- `type Edge =` — type, line 1028
- `const verts: number[][] = []` — const, line 1030
- `const edges: Edge[] = []` — const, line 1040
- `const j = i ^ (1 << bit)` — const, line 1043
- `let cols = 80` — let, line 1048
- `let rows = 40` — let, line 1049
- `let width = 0` — let, line 1050
- `let height = 0` — let, line 1051
- `let dpr = Math.min(window.devicePixelRatio || 1, 2)` — let, line 1052
- `let atlas: MonospaceGlyphAtlas | null = null` — let, line 1053
- `let cells = new Uint16Array(0)` — let, line 1054
- `let zbuf = new Float64Array(0)` — let, line 1055
- `const reduce = prefersReducedMotion()` — const, line 1057
- `let raf = 0` — let, line 1058
- `let last = 0` — let, line 1059
- `let t = 0` — let, line 1060
- `const aspect = CHAR_W / CHAR_H` — const, line 1061
- `function rebuildAtlas()` — function, line 1063
- `function resize()` — function, line 1073
- `const rect = container!.getBoundingClientRect()` — const, line 1074
- `const nextDpr = Math.min(window.devicePixelRatio || 1, 2)` — const, line 1077
- `const dprChanged = nextDpr !== dpr` — const, line 1078
- `const ro = new ResizeObserver(()` — const, line 1093
- `function rotatePlane(p: number[], a: number, i: number, j: number)` — function, line 1099
- `const q = p.slice()` — const, line 1100
- `const c = Math.cos(a)` — const, line 1101
- `const s = Math.sin(a)` — const, line 1102
- `function rot4(p: number[], t: number)` — function, line 1108
- `let q = p` — let, line 1109
- `function draw(elapsed: number)` — function, line 1122
- `const D4 = 3.2` — const, line 1127
- `const D3 = 4.0` — const, line 1128
- `let dmin = Infinity` — let, line 1130
- `let dmax = -Infinity` — let, line 1131
- `const projected = verts.map((v)` — const, line 1133
- `const k4 = D4 / (D4 - w)` — const, line 1138
- `const x3 = x * k4` — const, line 1139
- `const y3 = y * k4` — const, line 1140
- `const z3 = z * k4` — const, line 1141
- `const k3 = D3 / (D3 - z3)` — const, line 1144
- `const sx = x3 * k3` — const, line 1145
- `const sy = y3 * k3` — const, line 1146
- `const depth = z3 + 0.35 * w` — const, line 1150
- `const scale = Math.min(cols, rows) * 0.26` — const, line 1159
- `const cx = cols / 2` — const, line 1160
- `const cy = rows / 2` — const, line 1161
- `function brightnessOf(depth: number, boost = 0)` — function, line 1163
- `const u = (depth - dmin) / Math.max(1e-6, dmax - dmin)` — const, line 1164
- `const b = Math.floor(u * (AMBER_LEVELS - 1)) + boost` — const, line 1165
- `const screen = projected.map((p)` — const, line 1169
- `function plot( x0: number, y0: number, z0: number, b0: number, x1: number, y1: number, z1: number, b1: number, isWConnector: boolean )` — function, line 1176
- `const dx = x1 - x0` — const, line 1187
- `const dy = y1 - y0` — const, line 1188
- `const steps = Math.max(2, Math.ceil(Math.hypot(dx, dy) * 1.25))` — const, line 1189
- `const u = s / steps` — const, line 1192
- `const xi = Math.round(x0 + dx * u)` — const, line 1194
- `const yi = Math.round(y0 + dy * u)` — const, line 1195
- `const z = z0 + (z1 - z0) * u` — const, line 1198
- `const index = yi * cols + xi` — const, line 1199
- `let bri = Math.round(b0 + (b1 - b0) * u)` — let, line 1203
- `const ci = Math.min( CHARS.length - 1, Math.floor((bri / (AMBER_LEVELS - 1)) * (CHARS.length - 1)) )` — const, line 1209
- `const a = screen[e.i]` — const, line 1219
- `const b = screen[e.j]` — const, line 1220
- `function frame(ts: number)` — function, line 1239
- `const elapsed = last === 0 ? 33 : Math.min(100, ts - last)` — const, line 1244
- `function BackdropHeroText(` — function, line 1280
- `function StartDebugCycler(` — function, line 1364
- `const next = ()` — const, line 1366
- `const i = BACKDROP_ORDER.indexOf(backdrop)` — const, line 1367
- `function BackdropPanel(` — function, line 1408
- `let inner: ReactNode` — let, line 1427
- `function MonoSlider(` — function, line 1511
- `const filled = Math.round(value * width)` — const, line 1512
- `function MinutesPicker(` — function, line 1533
- `const presets = [10, 20, 30, 45, 60]` — const, line 1534
- `const sel = m === value` — const, line 1538
- `function energyBucket(value: number): "low" | "medium" | "high"` — function, line 1561
- `function readinessScore(energy: number, sleep: number, minutes: number): number` — function, line 1565
- `function readinessQueueLimit(energy: number, sleep: number, minutes: number): number` — function, line 1569
- `const score = readinessScore(energy, sleep, minutes)` — const, line 1570
- `const timeSlots = Math.max(1, Math.ceil(minutes / 5))` — const, line 1571
- `function titleCase(value: string): string` — function, line 1575
- `function vaultAlias(vault: VaultSummary | null): string` — function, line 1581
- `const basename = vault.root.replace(/\\/g, "/").split("/").filter(Boolean).pop() ?? ""` — const, line 1583
- `function StreakBadge(` — function, line 1592
- `function NewVaultAffordance(` — function, line 1620
- `const stored = localStorage.getItem("learnloop.startBackdrop")` — const, line 1664
- `const previewRequestRef = useRef<` — const, line 1673
- `const energyValue = energyBucket(energy)` — const, line 1675
- `const queueLimit = readinessQueueLimit(energy, sleep, minutes)` — const, line 1676
- `const readinessFactor = readinessScore(energy, sleep, minutes).toFixed(2)` — const, line 1677
- `let cancelled = false` — let, line 1684
- `const key = JSON.stringify(` — const, line 1685
- `const inFlight = previewRequestRef.current` — const, line 1686
- `const promise = inFlight?.key === key ? inFlight.promise : api.getTodayQueue(` — const, line 1687
- `const onKey = (event: KeyboardEvent)` — const, line 1713
- `const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase()` — const, line 1714
- `async function begin()` — function, line 1725
- `const session = await api.startSession(` — const, line 1729
- `const items: ScheduledItemDto[] = preview?.sections.flatMap((section)` — const, line 1738
- `const masteryValues = items.filter((i)` — const, line 1740
- `const avgMastery = masteryValues.length > 0 ? masteryValues.reduce((a, b)` — const, line 1741
- `const masteryWords = avgMastery >= 0.65 ? HIGH_MASTERY_WORDS : LOW_MASTERY_WORDS` — const, line 1742
- `const queueSummary = [` — const, line 1744
- `const recommendedBudget = minutes <= 20 ? "short_session — probe_eig suppressed (≤20 min)" : minutes >= 45 ? "full_loop — probe_eig active" : "standard_loop — probe_eig active"` — const, line 1754
- `const now = new Date()` — const, line 1760
- `const dateLine = `$` — const, line 1761
- `const goalMeta = vault ? `$` — const, line 1765
- `const freshInstall = !vault || vault.counts.learningObjects === 0` — const, line 1769

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `StartScreen`; references `StartScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `QueueSnapshot`, `ScheduledItemDto`, `SessionSnapshot`, `StreakSummary`, `VaultSummary`
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
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/StartScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/StartScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
