---
title: "Desktop module · src/screens/reader/figures/sketch/SketchFigure.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.sketch.SketchFigure"
language: "TypeScript"
area: "TypeScript/screens/reader/figures/sketch"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.tsx"
source_commit: "0789bfcbea576a16363b70c092fc6fdc7c47cfea"
source_commit_timestamp: "2026-10-31T19:50:29-04:00"
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

# `src/screens/reader/figures/sketch/SketchFigure.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SketchFigure` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.tsx) |
| Source lines | 601 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `0789bfcbea576a16363b70c092fc6fdc7c47cfea` |
| Commit timestamp | `2026-10-31T19:50:29-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]]

## Public API

- `export const SKETCH_FRAME =` — const, line 45
- `export const SKETCH_COPY =` — const, line 53
- `export function checksStand(sketch: FigureSketchDto | null | undefined, withdrawn = false): boolean` — function, line 76
- `export function sketchBadge(figure: Pick<FigureViewDto, "grounding" | "sketch">, withdrawn = false): string` — function, line 81
- `export const ATTRIBUTE_WORDS: Record<string, string> =` — const, line 89
- `export function sketchCheckLines(sketch: FigureSketchDto | null | undefined): string[]` — function, line 92
- `export const TABLE_PAGE = 50` — const, line 132
- `export function predictionTarget(program: SketchProgram, prediction: Pick<FigurePredictionDto, "index" | "targetStep">): number` — function, line 194
- `export function SketchFigure(` — function, line 208

## Internal implementation anchors

- `const quote = (name: string)` — const, line 86
- `const lines = sketch.checks.map((check)` — const, line 94
- `const parts: string[] = []` — const, line 95
- `const plural = parts.length > 1 || check.elements.length > 1 || (check.partial ?? []).some((entry)` — const, line 98
- `const subject = parts.length ? parts.join(" and ") : `the value $` — const, line 99
- `const settings = `at $` — const, line 100
- `const unnamed = sketch.unnamedElements` — const, line 106
- `const named = sketch.notCovered.map(quote).join(", ")` — const, line 108
- `const others = unnamed ? `$` — const, line 109
- `function defaultsOf(program: SketchProgram): Params` — function, line 115
- `function clampStep(parameter: SketchParameter, raw: number): number` — function, line 120
- `const clamped = Math.min(parameter.max, Math.max(parameter.min, raw))` — const, line 122
- `const steps = Math.round((clamped - parameter.min) / parameter.step)` — const, line 123
- `function settingsText(params: Params): string` — function, line 127
- `const num = (value: unknown)` — const, line 134
- `function ProbeEntries(` — function, line 138
- `const entries = Array.isArray(value) ? value : []` — const, line 141
- `const pages = Math.max(1, Math.ceil(entries.length / TABLE_PAGE))` — const, line 142
- `const current = Math.min(page, pages - 1)` — const, line 143
- `const first = current * TABLE_PAGE` — const, line 144
- `const shown = entries.slice(first, first + TABLE_PAGE)` — const, line 145
- `const range = entries.length ? `$` — const, line 146
- `const cell =` — const, line 147
- `const PLAY_MS = 60` — const, line 183
- `function freshSeed(): number` — function, line 186
- `const cryptoObject = (globalThis as` — const, line 187
- `const total = clockSteps(program)` — const, line 196
- `const change = program.predictions?.[prediction.index]?.change ??` — const, line 197
- `type RunState = |` — type, line 202
- `const factory = useContext(SketchRunnerContext)` — const, line 209
- `const reduced = useMemo(prefersReducedMotion, [])` — const, line 223
- `const runner = useRef<SketchRunner | null>(null)` — const, line 224
- `const loaded = useRef<Promise<unknown> | null>(null)` — const, line 225
- `const busy = useRef(false)` — const, line 226
- `const timer = useRef<ReturnType<typeof setInterval> | null>(null)` — const, line 227
- `const queue = useRef<Promise<unknown>>(Promise.resolve())` — const, line 232
- `const runId = useRef(0)` — const, line 233
- `const at = useRef<` — const, line 234
- `const target = useRef<number | null>(null)` — const, line 237
- `const pendingTarget = useRef<number | null>(null)` — const, line 238
- `const total = clockSteps(program)` — const, line 239
- `const names = useMemo(()` — const, line 240
- `const schedule = useMemo(()` — const, line 242
- `const withdrawn = useChecksWithdrawn(figure.figureId)` — const, line 243
- `const verifiedSeed = figure.sketch?.seed ?? 1` — const, line 244
- `const tested = figure.sketch?.tested` — const, line 245
- `const enqueue = useCallback(<T,>(operation: ()` — const, line 247
- `const next = queue.current.then(operation, operation)` — const, line 248
- `const stopPlay = useCallback(()` — const, line 253
- `const fail = useCallback((caught: unknown, params: Params)` — const, line 260
- `const message = caught instanceof Error ? caught.message : String(caught)` — const, line 266
- `const errorKind = caught instanceof SketchRunError ? caught.kind : "error"` — const, line 267
- `const created = withWatchdog(factory(), undefined, ()` — const, line 274
- `const audit = useCallback((params: Params, seed: number, index: number, digest: string)` — const, line 289
- `const entry = tested.find((item)` — const, line 291
- `const position = entry ? entry.steps.indexOf(index) : -1` — const, line 292
- `const readChecked = useCallback(async (active: SketchRunner, params: Params, index: number, seed: number)` — const, line 298
- `const result = await active.read(params, index)` — const, line 299
- `const sceneIssues = sceneProblems(result.scene, names)` — const, line 301
- `const probeIssues = probeProblems(result.probes, program.probes)` — const, line 303
- `const commit = useCallback((id: number, read:` — const, line 308
- `const advanceRun = useCallback(async (id: number, active: SketchRunner, end: number, reads: number)` — const, line 319
- `let reached = from` — let, line 323
- `let done = 0` — let, line 324
- `let last:` — let, line 325
- `const next = Math.min(end, schedule.find((step)` — const, line 327
- `const advance = useCallback(async ()` — const, line 340
- `const active = runner.current` — const, line 341
- `const id = runId.current` — const, line 343
- `const end = Math.min(total, target.current ?? total)` — const, line 347
- `const advanceRef = useRef(advance)` — const, line 361
- `const playTo = useCallback((end: number)` — const, line 364
- `const active = runner.current` — const, line 375
- `const ready = loaded.current` — const, line 376
- `const id = runId.current` — const, line 379
- `const runParams = params` — const, line 380
- `const goal = pendingTarget.current` — const, line 381
- `const read = await readChecked(active, runParams, 0, seed)` — const, line 390
- `const play = ()` — const, line 404
- `const setParam = (name: string, raw: number)` — const, line 418
- `const parameter = program.parameters.find((item)` — const, line 419
- `const onHandle = (id: string, x: number, y: number)` — const, line 425
- `const handle = scene?.elements.find((element)` — const, line 426
- `const applyPrediction = (prediction: FigurePredictionDto)` — const, line 437
- `const change = program.predictions?.[prediction.index]?.change ??` — const, line 438
- `const next = defaultsOf(program)` — const, line 443
- `const parameter = program.parameters.find((item)` — const, line 445
- `const exact = Number(value) + 0` — const, line 446
- `const resume = ()` — const, line 453
- `const onKeyDown = (event: KeyboardEvent<HTMLDivElement>)` — const, line 458
- `const target = event.target as HTMLElement` — const, line 459
- `const openPrediction = ctl.contract?.predictions && !skipped && !figure.predictions.some((prediction)` — const, line 467
- `const answeredPrediction = figure.predictions.find((prediction)` — const, line 469
- `const locked = openPrediction !== null` — const, line 470
- `const stands = checksStand(figure.sketch, withdrawn)` — const, line 471
- `const checkLines = stands ? sketchCheckLines(figure.sketch) : []` — const, line 472
- `const withdrawnShown = !stands && Boolean(figure.sketch?.checks?.length)` — const, line 473
- `const prefill = state.kind === "error" ? `$` — const, line 474
- `const value = params[parameter.name] ?? parameter.default` — const, line 500

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `SKETCH_FRAME`, `SketchFigure`, `checksStand`, `sketchBadge`; references `SKETCH_FRAME`, `SketchFigure`, `checksStand`, `sketchBadge`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigurePredictionDto`, `FigureSketchDto`, `FigureViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `PredictionBlock`, `PredictionResult`, `linkStyle`, `prefersReducedMotion`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export; imports `formatValue`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchScene (tsx)|src/screens/reader/figures/sketch/SketchScene.tsx]] — import-or-re-export; imports `SketchSceneView`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/checksWithdrawn|src/screens/reader/figures/sketch/checksWithdrawn.ts]] — import-or-re-export; imports `useChecksWithdrawn`, `withdrawChecks`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchEngine|src/screens/reader/figures/sketch/sketchEngine.ts]] — import-or-re-export; imports `Params`, `SketchRunError`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchRunner|src/screens/reader/figures/sketch/sketchRunner.ts]] — import-or-re-export; imports `SketchRunner`, `SketchRunnerContext`, `withWatchdog`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|src/screens/reader/figures/sketch/sketchScene.ts]] — import-or-re-export; imports `Scene`, `SketchParameter`, `SketchProbe`, `SketchProgram`, `clockSteps`, `probeProblems`, `readSchedule`, `sceneProblems`, `usableSchedule`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresCtl`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.tsx](../../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
