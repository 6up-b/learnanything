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
| Source lines | 732 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]]

## Public API

- `export const FIGURE_FRAME =` — const, line 31
- `export const SOURCE_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze(` — const, line 52
- `export function sourceCheckReasons(keys: readonly string[] | null | undefined): string[]` — function, line 113
- `export const PROPERTY_CHECK_COPY: Readonly<Record<string, string>> = Object.freeze(` — const, line 118
- `export function frameBadge(verification: FigureViewDto["verification"], grounding?: FigureViewDto["grounding"]): string` — function, line 130
- `export function figureBadge(figure: Pick<FigureViewDto, "labelCode" | "sketch">, withdrawn = false): string` — function, line 140
- `export function FigureGoal(` — function, line 159
- `export function FigurePassages(` — function, line 174
- `export function frameChecks(keys: readonly string[] | null | undefined): string[]` — function, line 190
- `export const FIGURE_COPY =` — const, line 201
- `export const linkStyle: CSSProperties =` — const, line 237
- `export function prefersReducedMotion(): boolean` — function, line 249
- `export function FigurePendingLine(` — function, line 268
- `export function PredictionBlock(` — function, line 286
- `export function PredictionResult(` — function, line 342
- `export function figureHomeLine(home: FigureHome): string` — function, line 595
- `export function FigureInline(` — function, line 599
- `export function FiguresUnder(` — function, line 710

## Internal implementation anchors

- `const UNREADABLE = "LearnLoop couldn't read the book's equation exactly"` — const, line 51
- `const goal = figure.goalText?.trim()` — const, line 160
- `const PLAY_STEPS = 40` — const, line 233
- `const PLAY_MS = 150` — const, line 234
- `const REDUCED_STEPS = 20` — const, line 235
- `function defaultsOf(compiled: CompiledFigure): Record<string, number>` — function, line 258
- `function clamp(parameter: FigureParameter, value: number): number` — function, line 262
- `const group = `prediction-$` — const, line 305
- `const submit = async ()` — const, line 306
- `const answered = prediction.answered` — const, line 343
- `const choiceLabel = (value: string | null)` — const, line 347
- `function ParameterControl(` — function, line 387
- `const step = (parameter.max - parameter.min) / REDUCED_STEPS` — const, line 404
- `const labels = useFigureLabels()` — const, line 405
- `const spoken = labels ? labels.plain(parameter.label) : parameter.label` — const, line 406
- `function FigureBody(` — function, line 433
- `const initial = useCallback(()` — const, line 435
- `const reduced = useMemo(prefersReducedMotion, [])` — const, line 442
- `const timer = useRef<ReturnType<typeof setInterval> | null>(null)` — const, line 443
- `const data = useMemo(()` — const, line 445
- `const answeredPrediction = figure.predictions.find((prediction)` — const, line 447
- `const openPrediction = ctl.contract?.predictions && !skipped && !answeredPrediction ? figure.predictions[0] ?? null : null` — const, line 448
- `const readoutFormat = (data.panels.find((panel)` — const, line 449
- `const paused = useWindowPaused()` — const, line 455
- `const setParam = (name: string, raw: number)` — const, line 463
- `const parameter = compiled.parameters.find((item)` — const, line 464
- `const stopPlay = ()` — const, line 469
- `const play = (parameter: FigureParameter)` — const, line 475
- `let index = 0` — let, line 482
- `const value = parameter.min + ((parameter.max - parameter.min) * index) / PLAY_STEPS` — const, line 485
- `const applyPrediction = (prediction: FigurePredictionDto)` — const, line 492
- `const change = compiled.spec.predictions?.[prediction.index]?.change ??` — const, line 493
- `const next =` — const, line 495
- `const parameter = compiled.parameters.find((item)` — const, line 497
- `const onKeyDown = (event: KeyboardEvent<HTMLDivElement>)` — const, line 504
- `const target = event.target as HTMLElement` — const, line 505
- `const assumptions = figure.assumptions ?? []` — const, line 513
- `const controlsLocked = openPrediction !== null` — const, line 514
- `const shown = figure.shown` — const, line 600
- `const expanded = shown && ctl.expandedKey === figurePlacementKey(figure)` — const, line 601
- `const isSketch = figure.tier === "sketch"` — const, line 603
- `const isManim = figure.tier === "manim"` — const, line 606
- `const fuller = figure.fuller ?? null` — const, line 608
- `const fullerReady = fuller?.state === "ready" && fuller.figure ? fuller.figure : null` — const, line 609
- `const compiled = useMemo(()` — const, line 610
- `const program = useMemo(()` — const, line 618
- `const withdrawn = useChecksWithdrawn(figure.figureId)` — const, line 620
- `const checks = isManim ? (figure.manim?.checks.length ? [`$` — const, line 648
- `const toggle = ()` — const, line 653
- `const openFuller = ()` — const, line 659
- `const openQuick = ()` — const, line 664
- `const notRightOn = (target: FigureViewDto)` — const, line 669
- `const body = showingFuller && fullerReady ? <ManimFigureBody figure=` — const, line 671
- `const askOptIn = ctl.optInSpanId === spanId && ctl.manimOptIn === "ask"` — const, line 713
- `function FollowedFigureInline(` — function, line 728
- `const followCtl = useMemo<FiguresCtl>( ()` — const, line 729

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/LessonView|src/screens/LessonView.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/desks/companion/companionFigures|src/screens/desks/companion/companionFigures.tsx]] — import-or-re-export: `FigureInline`; references `FigureInline`
- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `FiguresUnder`; references `FiguresUnder`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `frameBadge`; references `frameBadge`
- [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]] — import-or-re-export: `FIGURE_FRAME`, `linkStyle`; references `FIGURE_FRAME`, `linkStyle`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export: `FIGURE_FRAME`, `linkStyle`, `sourceCheckReasons`; references `FIGURE_FRAME`, `linkStyle`, `sourceCheckReasons`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `PredictionBlock`, `PredictionResult`, `linkStyle`, `prefersReducedMotion`; references `PredictionBlock`, `PredictionResult`, `linkStyle`, `prefersReducedMotion`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export: `SOURCE_CHECK_COPY`, `frameBadge`; references `SOURCE_CHECK_COPY`, `frameBadge`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigurePredictionDto`, `FigureViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `logReaderAction`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export; imports `FigurePanel`, `formatValue`
- [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]] — import-or-re-export; imports `FullerLine`, `ManimFigureBody`, `ManimNotRight`, `ManimOptInLine`, `RICH_FRAME`, `RichPendingLine`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export; imports `CheckedBadge`, `CheckedLines`, `FigureLabelsProvider`, `FigureSourceInfo`, `LabelText`, `labelElements`, `useFigureLabels`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export; imports `CompiledFigure`, `FigureParameter`, `compileSpec`, `evaluateFigure`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sharedParams|src/screens/reader/figures/sharedParams.ts]] — import-or-re-export; imports `useSharedParams`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export; imports `SKETCH_FRAME`, `SketchFigure`, `checksStand`
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
- [apps/learnloop-tauri/src/screens/reader/figures/sharedParams.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/sharedParams.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figuresFollowSection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/figureLabels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureLabels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
