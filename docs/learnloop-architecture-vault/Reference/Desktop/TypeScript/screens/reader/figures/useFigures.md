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
source_commit: "63f2337c4d6837df7b3f647fd1d90d0afd7f7561"
source_commit_timestamp: "2026-11-01T23:15:09-05:00"
source_worktree_state: "staged-or-mixed"
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

Provides `FIGURE_POLL_MS`, `RICH_POLL_MS`, `FigureRequestInput`, `FigureRequestOutcome` and related exports within the desktop's TypeScript/screens/reader/figures ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts) |
| Source lines | 496 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `63f2337c4d6837df7b3f647fd1d90d0afd7f7561` |
| Commit timestamp | `2026-11-01T23:15:09-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]]

## Public API

- `export const FIGURE_POLL_MS = 1500` — const, line 18
- `export const RICH_POLL_MS = 5000` — const, line 21
- `export interface FigureRequestInput` — interface, line 23
- `export type FigureRequestOutcome = "shown" | "not_shown" | "cancelled" | "skipped"` — type, line 43
- `export interface FigurePending` — interface, line 46
- `export interface FiguresContract` — interface, line 59
- `export interface FigureHome` — interface, line 75
- `export interface FollowedFigure` — interface, line 83
- `export interface FiguresCtl` — interface, line 89
- `export function figurePlacementKey(figure: Pick<FigureViewDto, "figureId" | "anchorSpanId">): string` — function, line 130
- `export function useFigures(` — function, line 138

## Internal implementation anchors

- `function sleep(ms: number): Promise<void>` — function, line 134
- `const enabled = Boolean(contract && extractionId)` — const, line 152
- `const followOn = enabled && followEnabled` — const, line 153
- `const followedRef = useRef(followed)` — const, line 159
- `const setExpanded = useCallback((figure: FigureViewDto | null)` — const, line 164
- `const generation = useRef(0)` — const, line 166
- `const followGeneration = useRef(0)` — const, line 169
- `const runs = useRef(new Map<string, object>())` — const, line 170
- `const onBuiltRef = useRef(onBuilt)` — const, line 171
- `const mine = generation.current` — const, line 182
- `const keys = new Set(followedRef.current.map((entry)` — const, line 198
- `const richRunning = ( richPending.some((line)` — const, line 207
- `const mine = generation.current` — const, line 212
- `const timer = setTimeout(()` — const, line 213
- `const land = useCallback((figure: FigureViewDto)` — const, line 226
- `const sameRequest = (item: FigureViewDto)` — const, line 227
- `const goalOnly = figure.spanIds.length === 0 && figure.region === null` — const, line 235
- `const anchors = goalOnly ? [...new Set([figure.anchorSpanId, ...list.filter((item)` — const, line 236
- `const placed = anchors.map((anchorSpanId)` — const, line 239
- `const run = useCallback( (key: string, anchorSpanId: string, start: ()` — const, line 251
- `const mine = generation.current` — const, line 254
- `const token =` — const, line 255
- `const live = ()` — const, line 257
- `let jobId: string | null = null` — let, line 258
- `const retry = ()` — const, line 259
- `const cancel = ()` — const, line 260
- `let job = await start()` — let, line 268
- `const rich = job.state === "done" ? job.result?.rich ?? null : null` — const, line 277
- `const figure = job.state === "done" ? job.result?.figure ?? null : null` — const, line 283
- `const shown = figure !== null && (figure.verification === "verified" || figure.verification === "illustrative")` — const, line 284
- `const command = getCommandError(error)` — const, line 296
- `const request = useCallback( (input: FigureRequestInput): Promise<FigureRequestOutcome>` — const, line 307
- `const spanIds = [...new Set(input.spanIds)]` — const, line 310
- `const anchor = spanIds[spanIds.length - 1] ?? input.region?.spanId ?? input.readingAt?.spanId ?? ""` — const, line 311
- `const region = input.region && contract?.region ? input.region : null` — const, line 314
- `const goal = input.goalText?.trim() ? input.goalText.trim() : null` — const, line 315
- `const key = `req:$` — const, line 316
- `const origin = input.origin ?? (goal ? "show_me" : "selection")` — const, line 317
- `const anchored = spanIds.length > 0 || region !== null` — const, line 324
- `const readingAt = input.readingAt?.spanId ?` — const, line 325
- `const refresh = useCallback(()` — const, line 345
- `const mine = generation.current` — const, line 347
- `const cancelRich = useCallback((richJobId: string)` — const, line 358
- `const retryRich = useCallback((richJobId: string)` — const, line 363
- `const answerManimOptIn = useCallback((choice: "allow" | "decline")` — const, line 369
- `const revise = useCallback( (figure: FigureViewDto, note: string, differentKind?: boolean)` — const, line 377
- `const patchPrediction = useCallback((found: FigurePredictionResultDto)` — const, line 386
- `const patch = (figure: FigureViewDto): FigureViewDto` — const, line 387
- `const follow = useCallback( async (ref: CorrespondentFigureDto, home: FigureHome, at: string): Promise<boolean>` — const, line 396
- `const mine = generation.current` — const, line 399
- `const mineFollow = followGeneration.current` — const, line 400
- `const current = ()` — const, line 401
- `const refuse = ()` — const, line 404
- `const keys = new Set(followedRef.current.filter((entry)` — const, line 406
- `let found: FigureViewDto | undefined` — let, line 413
- `const listed = await api.readerFigures(` — const, line 416
- `const figure: FigureViewDto =` — const, line 426
- `const predict = useCallback( async (figure: FigureViewDto, index: number, answer: string)` — const, line 435
- `const found = await api.readerFigurePredict(` — const, line 438
- `const explain = useCallback( async (_figure: FigureViewDto, predictionId: string, text: string)` — const, line 445
- `const found = await api.readerFigureExplain(` — const, line 448
- `const shownFollowed = useMemo(()` — const, line 456
- `const under = useCallback( (spanId: string | null | undefined)` — const, line 458

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `FiguresContract`, `FiguresCtl`, `figurePlacementKey`; references `FiguresContract`, `FiguresCtl`, `figurePlacementKey`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `FigureRequestOutcome`, `FiguresCtl`, `useFigures`; references `FigureRequestOutcome`, `FiguresCtl`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `/** RW5d P1: built with nothing from the learner's books (grounding "none"`, `checksLead: "checked by LearnLoop:"`, `code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book"`, `const`, `failed: "couldn't build a reliable version of this"`, `illustration: "AI-built illustration of an interpretation · not checked against the book"`, `unsupported: "can't draw this yet · noted"`; references `const`
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
