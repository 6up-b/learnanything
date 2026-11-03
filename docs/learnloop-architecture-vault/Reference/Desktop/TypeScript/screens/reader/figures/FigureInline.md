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
source_commit: "9e12d91330e6fa42d51fd7c7319294c7015e803f"
source_commit_timestamp: "2026-11-02T20:08:53-05:00"
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
| Source lines | 697 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `9e12d91330e6fa42d51fd7c7319294c7015e803f` |
| Commit timestamp | `2026-11-02T20:08:53-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]]

## Public API

- `export const FIGURE_FRAME =` — const, line 29
- `export const SOURCE_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze(` — const, line 50
- `export function sourceCheckReasons(keys: readonly string[] | null | undefined): string[]` — function, line 107
- `export const PROPERTY_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze(` — const, line 112
- `export function frameBadge(verification: FigureViewDto["verification"], grounding?: FigureViewDto["grounding"]): string` — function, line 124
- `export function FigureGoal(` — function, line 134
- `export function FigurePassages(` — function, line 149
- `export function frameChecks(keys: readonly string[] | null | undefined): string[]` — function, line 165
- `export const FIGURE_COPY =` — const, line 176
- `export const linkStyle: CSSProperties =` — const, line 212
- `export function prefersReducedMotion(): boolean` — function, line 224
- `export function FigurePendingLine(` — function, line 243
- `export function PredictionBlock(` — function, line 261
- `export function PredictionResult(` — function, line 317
- `export function figureHomeLine(home: FigureHome): string` — function, line 560
- `export function FigureInline(` — function, line 564
- `export function FiguresUnder(` — function, line 675

## Internal implementation anchors

- `const UNREADABLE = "LearnLoop couldn't read the book's equation exactly"` — const, line 49
- `const goal = figure.goalText?.trim()` — const, line 135
- `const PLAY_STEPS = 40` — const, line 208
- `const PLAY_MS = 150` — const, line 209
- `const REDUCED_STEPS = 20` — const, line 210
- `function defaultsOf(compiled: CompiledFigure): Record<string, number>` — function, line 233
- `function clamp(parameter: FigureParameter, value: number): number` — function, line 237
- `const group = `prediction-$` — const, line 280
- `const submit = async ()` — const, line 281
- `const answered = prediction.answered` — const, line 318
- `const choiceLabel = (value: string | null)` — const, line 322
- `function ParameterControl(` — function, line 362
- `const step = (parameter.max - parameter.min) / REDUCED_STEPS` — const, line 379
- `const labels = useFigureLabels()` — const, line 380
- `const spoken = labels ? labels.plain(parameter.label) : parameter.label` — const, line 381
- `function FigureBody(` — function, line 408
- `const reduced = useMemo(prefersReducedMotion, [])` — const, line 415
- `const timer = useRef<ReturnType<typeof setInterval> | null>(null)` — const, line 416
- `const data = useMemo(()` — const, line 418
- `const answeredPrediction = figure.predictions.find((prediction)` — const, line 420
- `const openPrediction = ctl.contract?.predictions && !skipped && !answeredPrediction ? figure.predictions[0] ?? null : null` — const, line 421
- `const readoutFormat = (data.panels.find((panel)` — const, line 422
- `const setParam = (name: string, raw: number)` — const, line 428
- `const parameter = compiled.parameters.find((item)` — const, line 429
- `const stopPlay = ()` — const, line 434
- `const play = (parameter: FigureParameter)` — const, line 440
- `let index = 0` — let, line 447
- `const value = parameter.min + ((parameter.max - parameter.min) * index) / PLAY_STEPS` — const, line 450
- `const applyPrediction = (prediction: FigurePredictionDto)` — const, line 457
- `const change = compiled.spec.predictions?.[prediction.index]?.change ??` — const, line 458
- `const next =` — const, line 460
- `const parameter = compiled.parameters.find((item)` — const, line 462
- `const onKeyDown = (event: KeyboardEvent<HTMLDivElement>)` — const, line 469
- `const target = event.target as HTMLElement` — const, line 470
- `const assumptions = figure.assumptions ?? []` — const, line 478
- `const controlsLocked = openPrediction !== null` — const, line 479
- `const shown = figure.verification === "verified" || figure.verification === "illustrative"` — const, line 565
- `const expanded = shown && ctl.expandedKey === figurePlacementKey(figure)` — const, line 566
- `const isSketch = figure.tier === "sketch"` — const, line 568
- `const isManim = figure.tier === "manim"` — const, line 571
- `const fuller = figure.fuller ?? null` — const, line 573
- `const fullerReady = fuller?.state === "ready" && fuller.figure ? fuller.figure : null` — const, line 574
- `const compiled = useMemo(()` — const, line 575
- `const program = useMemo(()` — const, line 583
- `const withdrawn = useChecksWithdrawn(figure.figureId)` — const, line 585
- `const checks = isManim ? (figure.manim?.checks.length ? [`$` — const, line 613
- `const toggle = ()` — const, line 618
- `const openFuller = ()` — const, line 624
- `const openQuick = ()` — const, line 629
- `const notRightOn = (target: FigureViewDto)` — const, line 634
- `const body = showingFuller && fullerReady ? <ManimFigureBody figure=` — const, line 636
- `const askOptIn = ctl.optInSpanId === spanId && ctl.manimOptIn === "ask"` — const, line 678
- `function FollowedFigureInline(` — function, line 693
- `const followCtl = useMemo<FiguresCtl>( ()` — const, line 694

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `FiguresUnder`; references `FiguresUnder`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `frameBadge`; references `frameBadge`
- [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]] — import-or-re-export: `FIGURE_FRAME`, `linkStyle`; references `FIGURE_FRAME`, `linkStyle`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export: `FIGURE_FRAME`, `linkStyle`, `sourceCheckReasons`; references `FIGURE_FRAME`, `linkStyle`, `sourceCheckReasons`
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
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export; imports `CheckedBadge`, `CheckedLines`, `FigureLabelsProvider`, `FigureSourceInfo`, `LabelText`, `labelElements`, `useFigureLabels`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export; imports `CompiledFigure`, `FigureParameter`, `compileSpec`, `evaluateFigure`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export; imports `SKETCH_FRAME`, `SketchFigure`, `checksStand`, `sketchBadge`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/checksWithdrawn|src/screens/reader/figures/sketch/checksWithdrawn.ts]] — import-or-re-export; imports `useChecksWithdrawn`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/sketchScene (ts)|src/screens/reader/figures/sketch/sketchScene.ts]] — import-or-re-export; imports `parseProgram`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `/** RW5d P1: built with nothing from the learner's books (grounding "none"`, `// RW5c (spec §7.3): drawn only from an element's closed role`, `aiBuilt: "AI-built"`, `aiDefined: "AI-defined"`, `aiElement: "AI-built · not checked against the book"`, `beside the book's own left-hand side.
  bookChecked: "matches the book's equation (checked)"`, `checksLead: "checked by LearnLoop:"`, `code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book"`, `const`, `derivedFrom: "computed by LearnLoop from it"`, `failed: "couldn't build a reliable version of this"`, `illustration: "AI-built illustration of an interpretation · not checked against the book"`, `limitedToPlot: "limited to the plotted range"`, `noTerms: "no terms in this range"`, `restIllustration: "the rest is an illustration"`, `unsupported: "can't draw this yet · noted"`
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
- [apps/learnloop-tauri/src/screens/reader/figures/figureLabels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureLabels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/FigureInline.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
