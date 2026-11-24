---
title: "Desktop module · src/screens/reader/figures/useFigures.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.useFigures"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts"
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

# `src/screens/reader/figures/useFigures.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `FIGURE_POLL_MS`, `RICH_POLL_MS`, `PREFETCH_POLL_LIFETIME_MS`, `FigureRequestInput` and related exports within the desktop's TypeScript/screens/reader/figures ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts) |
| Source lines | 588 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]]

## Public API

- `export const FIGURE_POLL_MS = 1500` — const, line 19
- `export const RICH_POLL_MS = 5000` — const, line 22
- `export const PREFETCH_POLL_LIFETIME_MS = 20 * 60 * 1000` — const, line 29
- `export interface FigureRequestInput` — interface, line 31
- `export type FigureRequestOutcome = "shown" | "not_shown" | "cancelled" | "skipped"` — type, line 51
- `export interface FigurePending` — interface, line 54
- `export interface FiguresContract` — interface, line 67
- `export interface FigureHome` — interface, line 83
- `export interface FollowedFigure` — interface, line 91
- `export interface FiguresCtl` — interface, line 97
- `export function figurePlacementKey(figure: Pick<FigureViewDto, "figureId" | "anchorSpanId">): string` — function, line 144
- `export function useFigures(` — function, line 152

## Internal implementation anchors

- `function sleep(ms: number): Promise<void>` — function, line 148
- `const enabled = Boolean(contract && extractionId)` — const, line 169
- `const followOn = enabled && followEnabled` — const, line 170
- `const whenLive = useWhenLive()` — const, line 171
- `const prefetchClock = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 180
- `const followedRef = useRef(followed)` — const, line 182
- `const setExpanded = useCallback((figure: FigureViewDto | null)` — const, line 187
- `const generation = useRef(0)` — const, line 189
- `const followGeneration = useRef(0)` — const, line 192
- `const runs = useRef(new Map<string, object>())` — const, line 193
- `const onBuiltRef = useRef(onBuilt)` — const, line 194
- `const mine = generation.current` — const, line 209
- `const keys = new Set(followedRef.current.map((entry)` — const, line 226
- `const fullerRunning = (figure: FigureViewDto)` — const, line 241
- `const speculativeFuller = figures.some((figure)` — const, line 243
- `const prefetchActive = prefetchPending || speculativeFuller` — const, line 244
- `const mine = generation.current` — const, line 250
- `const richRunning = ( (prefetchActive && !prefetchExpired) || richPending.some((line)` — const, line 254
- `const mine = generation.current` — const, line 260
- `const timer = setTimeout(()` — const, line 261
- `const land = useCallback((figure: FigureViewDto)` — const, line 277
- `const sameRequest = (item: FigureViewDto)` — const, line 278
- `const goalOnly = figure.spanIds.length === 0 && figure.region === null` — const, line 286
- `const anchors = goalOnly ? [...new Set([figure.anchorSpanId, ...list.filter((item)` — const, line 287
- `const placed = anchors.map((anchorSpanId)` — const, line 290
- `const run = useCallback( (key: string, anchorSpanId: string, start: ()` — const, line 302
- `const mine = generation.current` — const, line 305
- `const token =` — const, line 306
- `const live = ()` — const, line 308
- `let jobId: string | null = null` — let, line 309
- `const retry = ()` — const, line 310
- `const cancel = ()` — const, line 311
- `let job = await start()` — let, line 319
- `const rich = job.state === "done" ? job.result?.rich ?? null : null` — const, line 329
- `const figure = job.state === "done" ? job.result?.figure ?? null : null` — const, line 341
- `const shown = figure !== null && figure.shown` — const, line 342
- `const command = getCommandError(error)` — const, line 354
- `const request = useCallback( (input: FigureRequestInput): Promise<FigureRequestOutcome>` — const, line 365
- `const spanIds = [...new Set(input.spanIds)]` — const, line 368
- `const anchor = spanIds[spanIds.length - 1] ?? input.region?.spanId ?? input.readingAt?.spanId ?? ""` — const, line 369
- `const region = input.region && contract?.region ? input.region : null` — const, line 372
- `const goal = input.goalText?.trim() ? input.goalText.trim() : null` — const, line 373
- `const key = `req:$` — const, line 374
- `const origin = input.origin ?? (goal ? "show_me" : "selection")` — const, line 375
- `const anchored = spanIds.length > 0 || region !== null` — const, line 382
- `const readingAt = input.readingAt?.spanId ?` — const, line 383
- `const refresh = useCallback(()` — const, line 403
- `const mine = generation.current` — const, line 405
- `const cancelRich = useCallback((richJobId: string)` — const, line 416
- `const retryRich = useCallback((richJobId: string)` — const, line 421
- `const answerManimOptIn = useCallback((choice: "allow" | "decline")` — const, line 427
- `const revise = useCallback( (figure: FigureViewDto, note: string, differentKind?: boolean)` — const, line 435
- `const rebuild = useCallback( (figure: FigureViewDto)` — const, line 445
- `const rechecking = useRef(new Set<string>())` — const, line 455
- `const recheck = useCallback( (figure: FigureViewDto)` — const, line 456
- `const started = await Promise.resolve(api.readerFigureRecheck(` — const, line 461
- `let state = started?.state` — let, line 462
- `const jobId = started?.jobId` — const, line 463
- `const patchPrediction = useCallback((found: FigurePredictionResultDto)` — const, line 475
- `const patch = (figure: FigureViewDto): FigureViewDto` — const, line 476
- `const follow = useCallback( async (ref: CorrespondentFigureDto, home: FigureHome, at: string): Promise<boolean>` — const, line 485
- `const mine = generation.current` — const, line 488
- `const mineFollow = followGeneration.current` — const, line 489
- `const current = ()` — const, line 490
- `const refuse = ()` — const, line 493
- `const keys = new Set(followedRef.current.filter((entry)` — const, line 495
- `let found: FigureViewDto | undefined` — let, line 502
- `const listed = await api.readerFigures(` — const, line 505
- `const figure: FigureViewDto =` — const, line 515
- `const predict = useCallback( async (figure: FigureViewDto, index: number, answer: string)` — const, line 524
- `const found = await api.readerFigurePredict(` — const, line 527
- `const explain = useCallback( async (_figure: FigureViewDto, predictionId: string, text: string)` — const, line 534
- `const found = await api.readerFigureExplain(` — const, line 537
- `const shownFollowed = useMemo(()` — const, line 545
- `const under = useCallback( (spanId: string | null | undefined)` — const, line 547

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `FiguresContract`, `FiguresCtl`, `figurePlacementKey`; references `FiguresContract`, `FiguresCtl`, `figurePlacementKey`
- [[Reference/Desktop/TypeScript/screens/LessonView|src/screens/LessonView.tsx]] — import-or-re-export: `FiguresContract`, `FiguresCtl`, `figurePlacementKey`; references `FiguresContract`, `FiguresCtl`, `figurePlacementKey`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `FigureRequestOutcome`, `FiguresCtl`, `useFigures`; references `FigureRequestOutcome`, `FiguresCtl`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `/** RW5d P1: built with nothing from the learner's books (grounding "none"`, `// RW5c (spec §7.3): drawn only from an element's closed role`, `aiBuilt: "AI-built"`, `aiDefined: "AI-defined"`, `aiElement: "AI-built · not checked against the book"`, `beside the book's own left-hand side.
  bookChecked: "matches the book's equation (checked)"`, `checksLead: "checked by LearnLoop:"`, `code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book"`, `const`, `derivedFrom: "computed by LearnLoop from it"`, `failed: "couldn't build a reliable version of this"`, `illustration: "AI-built illustration of an interpretation · not checked against the book"`, `limitedToPlot: "limited to the plotted range"`, `noTerms: "no terms in this range"`, `restIllustration: "the rest is an illustration"`, `unsupported: "can't draw this yet · noted"`; references `const`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]] — import-or-re-export: `FiguresCtl`; references `FiguresCtl`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `FiguresCtl`; references `FiguresCtl`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `FiguresContract`, `useFigures`; references `FiguresContract`, `useFigures`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CorrespondentFigureDto`, `FigureBuildResultDto`, `FigurePredictionResultDto`, `FigureRichPendingDto`, `FigureViewDto`, `LibraryJobDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `SOURCE_CHECK_COPY`, `frameBadge`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `passageKeys`

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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
