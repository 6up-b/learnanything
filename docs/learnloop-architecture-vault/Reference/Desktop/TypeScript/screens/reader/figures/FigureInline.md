---
title: "Desktop module · src/screens/reader/figures/FigureInline.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.FigureInline"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx"
source_commit: "47c892762f2845348a5efaa4d16192161094013f"
source_commit_timestamp: "2026-11-02T05:28:14-05:00"
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

# `src/screens/reader/figures/FigureInline.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `FigureInline` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx) |
| Source lines | 603 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `47c892762f2845348a5efaa4d16192161094013f` |
| Commit timestamp | `2026-11-02T05:28:14-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]]

## Public API

- `export const FIGURE_FRAME =` — const, line 28
- `export const PROPERTY_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze(` — const, line 37
- `export function frameBadge(verification: FigureViewDto["verification"], grounding?: FigureViewDto["grounding"]): string` — function, line 49
- `export function FigureGoal(` — function, line 59
- `export function FigurePassages(` — function, line 74
- `export function frameChecks(keys: readonly string[] | null | undefined): string[]` — function, line 90
- `export const FIGURE_COPY =` — const, line 101
- `export const linkStyle: CSSProperties =` — const, line 135
- `export function prefersReducedMotion(): boolean` — function, line 147
- `export function FigurePendingLine(` — function, line 166
- `export function PredictionBlock(` — function, line 184
- `export function PredictionResult(` — function, line 240
- `export function figureHomeLine(home: FigureHome): string` — function, line 475
- `export function FigureInline(` — function, line 479
- `export function FiguresUnder(` — function, line 581

## Internal implementation anchors

- `const goal = figure.goalText?.trim()` — const, line 60
- `const PLAY_STEPS = 40` — const, line 131
- `const PLAY_MS = 150` — const, line 132
- `const REDUCED_STEPS = 20` — const, line 133
- `function defaultsOf(compiled: CompiledFigure): Record<string, number>` — function, line 156
- `function clamp(parameter: FigureParameter, value: number): number` — function, line 160
- `const group = `prediction-$` — const, line 203
- `const submit = async ()` — const, line 204
- `const answered = prediction.answered` — const, line 241
- `const choiceLabel = (value: string | null)` — const, line 245
- `function ParameterControl(` — function, line 285
- `const step = (parameter.max - parameter.min) / REDUCED_STEPS` — const, line 302
- `function FigureBody(` — function, line 329
- `const reduced = useMemo(prefersReducedMotion, [])` — const, line 336
- `const timer = useRef<ReturnType<typeof setInterval> | null>(null)` — const, line 337
- `const data = useMemo(()` — const, line 339
- `const answeredPrediction = figure.predictions.find((prediction)` — const, line 341
- `const openPrediction = ctl.contract?.predictions && !skipped && !answeredPrediction ? figure.predictions[0] ?? null : null` — const, line 342
- `const readoutFormat = (data.panels.find((panel)` — const, line 343
- `const setParam = (name: string, raw: number)` — const, line 349
- `const parameter = compiled.parameters.find((item)` — const, line 350
- `const stopPlay = ()` — const, line 355
- `const play = (parameter: FigureParameter)` — const, line 361
- `let index = 0` — let, line 368
- `const value = parameter.min + ((parameter.max - parameter.min) * index) / PLAY_STEPS` — const, line 371
- `const applyPrediction = (prediction: FigurePredictionDto)` — const, line 378
- `const change = compiled.spec.predictions?.[prediction.index]?.change ??` — const, line 379
- `const next =` — const, line 381
- `const parameter = compiled.parameters.find((item)` — const, line 383
- `const onKeyDown = (event: KeyboardEvent<HTMLDivElement>)` — const, line 390
- `const target = event.target as HTMLElement` — const, line 391
- `const assumptions = figure.assumptions ?? []` — const, line 399
- `const controlsLocked = openPrediction !== null` — const, line 400
- `const shown = figure.verification === "verified" || figure.verification === "illustrative"` — const, line 480
- `const expanded = shown && ctl.expandedKey === figurePlacementKey(figure)` — const, line 481
- `const isSketch = figure.tier === "sketch"` — const, line 483
- `const isManim = figure.tier === "manim"` — const, line 486
- `const fuller = figure.fuller ?? null` — const, line 488
- `const fullerReady = fuller?.state === "ready" && fuller.figure ? fuller.figure : null` — const, line 489
- `const compiled = useMemo(()` — const, line 490
- `const program = useMemo(()` — const, line 498
- `const withdrawn = useChecksWithdrawn(figure.figureId)` — const, line 500
- `const checks = isManim ? (figure.manim?.checks.length ? [`$` — const, line 523
- `const toggle = ()` — const, line 528
- `const openFuller = ()` — const, line 532
- `const openQuick = ()` — const, line 537
- `const notRightOn = (target: FigureViewDto)` — const, line 542
- `const body = showingFuller && fullerReady ? <ManimFigureBody figure=` — const, line 544
- `const askOptIn = ctl.optInSpanId === spanId && ctl.manimOptIn === "ask"` — const, line 584
- `function FollowedFigureInline(` — function, line 599
- `const followCtl = useMemo<FiguresCtl>( ()` — const, line 600

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `FiguresUnder`; references `FiguresUnder`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `frameBadge`; references `frameBadge`
- [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]] — import-or-re-export: `FIGURE_FRAME`, `linkStyle`; references `FIGURE_FRAME`, `linkStyle`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `PredictionBlock`, `PredictionResult`, `linkStyle`, `prefersReducedMotion`; references `PredictionBlock`, `PredictionResult`, `linkStyle`, `prefersReducedMotion`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export: `frameBadge`; references `frameBadge`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigurePredictionDto`, `FigureViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export; imports `FigurePanel`, `formatValue`
- [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]] — import-or-re-export; imports `FullerLine`, `ManimFigureBody`, `ManimNotRight`, `ManimOptInLine`, `RICH_FRAME`, `RichPendingLine`, `manimBadge`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export; imports `CompiledFigure`, `FigureParameter`, `compileSpec`, `evaluateFigure`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export; imports `SKETCH_FRAME`, `SketchFigure`, `checksStand`, `sketchBadge`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/checksWithdrawn|src/screens/reader/figures/sketch/checksWithdrawn.ts]] — import-or-re-export; imports `useChecksWithdrawn`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|src/screens/reader/figures/sketch/sketchScene.ts]] — import-or-re-export; imports `parseProgram`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `/** RW5d P1: built with nothing from the learner's books (grounding "none"`, `checksLead: "checked by LearnLoop:"`, `code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book"`, `const`, `failed: "couldn't build a reliable version of this"`, `illustration: "AI-built illustration of an interpretation · not checked against the book"`, `unsupported: "can't draw this yet · noted"`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerQuote`, `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchSandboxReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sketch/SketchFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/showMe.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/showMe.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/LessonScreen.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/LessonScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
