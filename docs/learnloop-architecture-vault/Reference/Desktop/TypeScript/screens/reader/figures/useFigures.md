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
| Source lines | 576 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]]

## Public API

- `export const FIGURE_POLL_MS = 1500` — const, line 18
- `export const RICH_POLL_MS = 5000` — const, line 21
- `export const PREFETCH_POLL_LIFETIME_MS = 20 * 60 * 1000` — const, line 28
- `export interface FigureRequestInput` — interface, line 30
- `export type FigureRequestOutcome = "shown" | "not_shown" | "cancelled" | "skipped"` — type, line 50
- `export interface FigurePending` — interface, line 53
- `export interface FiguresContract` — interface, line 66
- `export interface FigureHome` — interface, line 82
- `export interface FollowedFigure` — interface, line 90
- `export interface FiguresCtl` — interface, line 96
- `export function figurePlacementKey(figure: Pick<FigureViewDto, "figureId" | "anchorSpanId">): string` — function, line 143
- `export function useFigures(` — function, line 151

## Internal implementation anchors

- `function sleep(ms: number): Promise<void>` — function, line 147
- `const enabled = Boolean(contract && extractionId)` — const, line 168
- `const followOn = enabled && followEnabled` — const, line 169
- `const prefetchClock = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 178
- `const followedRef = useRef(followed)` — const, line 180
- `const setExpanded = useCallback((figure: FigureViewDto | null)` — const, line 185
- `const generation = useRef(0)` — const, line 187
- `const followGeneration = useRef(0)` — const, line 190
- `const runs = useRef(new Map<string, object>())` — const, line 191
- `const onBuiltRef = useRef(onBuilt)` — const, line 192
- `const mine = generation.current` — const, line 207
- `const keys = new Set(followedRef.current.map((entry)` — const, line 224
- `const fullerRunning = (figure: FigureViewDto)` — const, line 239
- `const speculativeFuller = figures.some((figure)` — const, line 241
- `const prefetchActive = prefetchPending || speculativeFuller` — const, line 242
- `const mine = generation.current` — const, line 248
- `const richRunning = ( (prefetchActive && !prefetchExpired) || richPending.some((line)` — const, line 252
- `const mine = generation.current` — const, line 258
- `const timer = setTimeout(()` — const, line 259
- `const land = useCallback((figure: FigureViewDto)` — const, line 273
- `const sameRequest = (item: FigureViewDto)` — const, line 274
- `const goalOnly = figure.spanIds.length === 0 && figure.region === null` — const, line 282
- `const anchors = goalOnly ? [...new Set([figure.anchorSpanId, ...list.filter((item)` — const, line 283
- `const placed = anchors.map((anchorSpanId)` — const, line 286
- `const run = useCallback( (key: string, anchorSpanId: string, start: ()` — const, line 298
- `const mine = generation.current` — const, line 301
- `const token =` — const, line 302
- `const live = ()` — const, line 304
- `let jobId: string | null = null` — let, line 305
- `const retry = ()` — const, line 306
- `const cancel = ()` — const, line 307
- `let job = await start()` — let, line 315
- `const rich = job.state === "done" ? job.result?.rich ?? null : null` — const, line 324
- `const figure = job.state === "done" ? job.result?.figure ?? null : null` — const, line 330
- `const shown = figure !== null && (figure.verification === "verified" || figure.verification === "illustrative")` — const, line 331
- `const command = getCommandError(error)` — const, line 343
- `const request = useCallback( (input: FigureRequestInput): Promise<FigureRequestOutcome>` — const, line 354
- `const spanIds = [...new Set(input.spanIds)]` — const, line 357
- `const anchor = spanIds[spanIds.length - 1] ?? input.region?.spanId ?? input.readingAt?.spanId ?? ""` — const, line 358
- `const region = input.region && contract?.region ? input.region : null` — const, line 361
- `const goal = input.goalText?.trim() ? input.goalText.trim() : null` — const, line 362
- `const key = `req:$` — const, line 363
- `const origin = input.origin ?? (goal ? "show_me" : "selection")` — const, line 364
- `const anchored = spanIds.length > 0 || region !== null` — const, line 371
- `const readingAt = input.readingAt?.spanId ?` — const, line 372
- `const refresh = useCallback(()` — const, line 392
- `const mine = generation.current` — const, line 394
- `const cancelRich = useCallback((richJobId: string)` — const, line 405
- `const retryRich = useCallback((richJobId: string)` — const, line 410
- `const answerManimOptIn = useCallback((choice: "allow" | "decline")` — const, line 416
- `const revise = useCallback( (figure: FigureViewDto, note: string, differentKind?: boolean)` — const, line 424
- `const rebuild = useCallback( (figure: FigureViewDto)` — const, line 434
- `const rechecking = useRef(new Set<string>())` — const, line 444
- `const recheck = useCallback( (figure: FigureViewDto)` — const, line 445
- `const started = await Promise.resolve(api.readerFigureRecheck(` — const, line 450
- `let state = started?.state` — let, line 451
- `const jobId = started?.jobId` — const, line 452
- `const patchPrediction = useCallback((found: FigurePredictionResultDto)` — const, line 463
- `const patch = (figure: FigureViewDto): FigureViewDto` — const, line 464
- `const follow = useCallback( async (ref: CorrespondentFigureDto, home: FigureHome, at: string): Promise<boolean>` — const, line 473
- `const mine = generation.current` — const, line 476
- `const mineFollow = followGeneration.current` — const, line 477
- `const current = ()` — const, line 478
- `const refuse = ()` — const, line 481
- `const keys = new Set(followedRef.current.filter((entry)` — const, line 483
- `let found: FigureViewDto | undefined` — let, line 490
- `const listed = await api.readerFigures(` — const, line 493
- `const figure: FigureViewDto =` — const, line 503
- `const predict = useCallback( async (figure: FigureViewDto, index: number, answer: string)` — const, line 512
- `const found = await api.readerFigurePredict(` — const, line 515
- `const explain = useCallback( async (_figure: FigureViewDto, predictionId: string, text: string)` — const, line 522
- `const found = await api.readerFigureExplain(` — const, line 525
- `const shownFollowed = useMemo(()` — const, line 533
- `const under = useCallback( (spanId: string | null | undefined)` — const, line 535

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `FiguresContract`, `FiguresCtl`, `figurePlacementKey`; references `FiguresContract`, `FiguresCtl`, `figurePlacementKey`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `FiguresContract`, `FiguresCtl`, `figurePlacementKey`; references `FiguresContract`, `FiguresCtl`, `figurePlacementKey`
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
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `frameBadge`
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
