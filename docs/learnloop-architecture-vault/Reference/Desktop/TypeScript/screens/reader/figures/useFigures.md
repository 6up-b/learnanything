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
source_commit: "8427228c2d6ecbf8bf612e57a5e1d5d0c0d7fb6b"
source_commit_timestamp: "2026-10-31T14:41:14-04:00"
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

Provides `FIGURE_POLL_MS`, `FigureRequestInput`, `FigureRequestOutcome`, `FigurePending` and related exports within the desktop's TypeScript/screens/reader/figures ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts) |
| Source lines | 304 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `8427228c2d6ecbf8bf612e57a5e1d5d0c0d7fb6b` |
| Commit timestamp | `2026-10-31T14:41:14-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]]

## Public API

- `export const FIGURE_POLL_MS = 1500` — const, line 18
- `export interface FigureRequestInput` — interface, line 20
- `export type FigureRequestOutcome = "shown" | "not_shown" | "cancelled" | "skipped"` — type, line 40
- `export interface FigurePending` — interface, line 43
- `export interface FiguresContract` — interface, line 56
- `export interface FiguresCtl` — interface, line 68
- `export function figurePlacementKey(figure: Pick<FigureViewDto, "figureId" | "anchorSpanId">): string` — function, line 88
- `export function useFigures(` — function, line 96

## Internal implementation anchors

- `function sleep(ms: number): Promise<void>` — function, line 92
- `const enabled = Boolean(contract && extractionId)` — const, line 105
- `const setExpanded = useCallback((figure: FigureViewDto | null)` — const, line 109
- `const generation = useRef(0)` — const, line 111
- `const runs = useRef(new Map<string, object>())` — const, line 112
- `const onBuiltRef = useRef(onBuilt)` — const, line 113
- `const mine = generation.current` — const, line 122
- `const land = useCallback((figure: FigureViewDto)` — const, line 130
- `const sameRequest = (item: FigureViewDto)` — const, line 131
- `const goalOnly = figure.spanIds.length === 0 && figure.region === null` — const, line 139
- `const anchors = goalOnly ? [...new Set([figure.anchorSpanId, ...list.filter((item)` — const, line 140
- `const placed = anchors.map((anchorSpanId)` — const, line 143
- `const run = useCallback( (key: string, anchorSpanId: string, start: ()` — const, line 155
- `const mine = generation.current` — const, line 158
- `const token =` — const, line 159
- `const live = ()` — const, line 161
- `let jobId: string | null = null` — let, line 162
- `const retry = ()` — const, line 163
- `const cancel = ()` — const, line 164
- `let job = await start()` — let, line 172
- `const figure = job.state === "done" ? job.result?.figure ?? null : null` — const, line 181
- `const shown = figure !== null && (figure.verification === "verified" || figure.verification === "illustrative")` — const, line 182
- `const command = getCommandError(error)` — const, line 194
- `const request = useCallback( (input: FigureRequestInput): Promise<FigureRequestOutcome>` — const, line 205
- `const spanIds = [...new Set(input.spanIds)]` — const, line 208
- `const anchor = spanIds[spanIds.length - 1] ?? input.region?.spanId ?? input.readingAt?.spanId ?? ""` — const, line 209
- `const region = input.region && contract?.region ? input.region : null` — const, line 210
- `const goal = input.goalText?.trim() ? input.goalText.trim() : null` — const, line 211
- `const key = `req:$` — const, line 212
- `const origin = input.origin ?? (goal ? "show_me" : "selection")` — const, line 213
- `const anchored = spanIds.length > 0 || region !== null` — const, line 220
- `const readingAt = input.readingAt?.spanId ?` — const, line 221
- `const revise = useCallback( (figure: FigureViewDto, note: string)` — const, line 241
- `const patchPrediction = useCallback((found: FigurePredictionResultDto)` — const, line 249
- `const predict = useCallback( async (figure: FigureViewDto, index: number, answer: string)` — const, line 257
- `const found = await api.readerFigurePredict(` — const, line 260
- `const explain = useCallback( async (_figure: FigureViewDto, predictionId: string, text: string)` — const, line 267
- `const found = await api.readerFigureExplain(` — const, line 270
- `const under = useCallback( (spanId: string | null | undefined)` — const, line 277

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `FigureRequestOutcome`, `FiguresCtl`, `useFigures`; references `FigureRequestOutcome`, `FiguresCtl`, `useFigures`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `/** RW5d P1: built with nothing from the learner's books (grounding "none"`, `checksLead: "checked by LearnLoop:"`, `code-written). */
  notFromBooks: "not from your books — LearnLoop's model's illustration · not checked against the book"`, `const`, `failed: "couldn't build a reliable version of this"`, `illustration: "AI-built illustration of an interpretation · not checked against the book"`, `unsupported: "can't draw this yet · noted"`; references `const`
- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/SketchFigure|src/screens/reader/figures/sketch/SketchFigure.tsx]] — import-or-re-export: `FiguresCtl`; references `FiguresCtl`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `FiguresContract`, `useFigures`; references `FiguresContract`, `useFigures`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureBuildResultDto`, `FigurePredictionResultDto`, `FigureViewDto`, `LibraryJobDto`
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
