---
title: "Desktop module · src/screens/reader/useReaderWorkbench.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReaderWorkbench"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReaderWorkbench.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReaderWorkbench.ts"
source_commit: "7e26da6c7a44594e03b96fb1b499ea81cc47199e"
source_commit_timestamp: "2026-10-25T02:35:10-04:00"
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

# `src/screens/reader/useReaderWorkbench.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `ReaderWorkbenchCheck`, `ReaderWorkbenchProps`, `ReaderWorkbenchResume`, `ActiveWorkbench` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderWorkbench.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderWorkbench.ts) |
| Source lines | 541 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `7e26da6c7a44594e03b96fb1b499ea81cc47199e` |
| Commit timestamp | `2026-10-25T02:35:10-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]]

## Public API

- `export interface ReaderWorkbenchCheck` — interface, line 63
- `export interface ReaderWorkbenchProps` — interface, line 76
- `export interface ReaderWorkbenchResume` — interface, line 106
- `export interface ActiveWorkbench` — interface, line 114
- `export interface ReaderWorkbench` — interface, line 130
- `export function useReaderWorkbench(input:` — function, line 170

## Internal implementation anchors

- `interface Ticket` — interface, line 159
- `function newKey(): string` — function, line 166
- `const props = input.props` — const, line 178
- `const extractionRef = useRef(extractionId)` — const, line 185
- `const cardRef = useRef(card)` — const, line 187
- `const activeRef = useRef<ActiveWorkbench | null>(null)` — const, line 189
- `const propsRef = useRef(props)` — const, line 191
- `const generation = useRef(0)` — const, line 199
- `const openSeq = useRef(0)` — const, line 200
- `const bump = useCallback(()` — const, line 201
- `const ticket = useCallback((isOpen: boolean): Ticket` — const, line 205
- `const fresh = useCallback((sent: Ticket)` — const, line 212
- `const onOpenBook = useCallback((session: WorkbenchSessionDto, book: Pick<Ticket, "extractionId" | "sourceId">)` — const, line 218
- `const admits = useCallback((sent: Ticket, session: WorkbenchSessionDto)` — const, line 223
- `const refreshSeq = useRef(0)` — const, line 228
- `const refresh = useCallback(async ()` — const, line 229
- `const current = extractionRef.current` — const, line 230
- `const asked = refreshSeq.current` — const, line 233
- `const result = await api.workbenchForSource(` — const, line 235
- `const initialAttemptId = props?.initialAttemptId ?? null` — const, line 253
- `const openedAttemptRef = useRef<string | null>(null)` — const, line 254
- `const sent = ticket(true)` — const, line 258
- `const session = result.session` — const, line 261
- `const shown = cardRef.current` — const, line 262
- `const onResize = ()` — const, line 273
- `const setWidth = useCallback((next: number)` — const, line 278
- `const clamped = clampSplitWidth(next, window.innerWidth)` — const, line 279
- `const resizeBy = useCallback((delta: number)` — const, line 283
- `const clamped = clampSplitWidth(current + delta, window.innerWidth)` — const, line 285
- `const admitting = useRef(new Set<string>())` — const, line 299
- `const admit = useCallback((session: WorkbenchSessionDto)` — const, line 300
- `const book =` — const, line 301
- `const sentGeneration = generation.current` — const, line 306
- `const asked = session.sessionId` — const, line 307
- `type Serve =` — type, line 322
- `const begin = useCallback((session: WorkbenchSessionDto, sent: Ticket, readOnly = false, serve?: Serve)` — const, line 325
- `const shown = cardRef.current` — const, line 326
- `const openSelection = useCallback(async (request:` — const, line 334
- `const sent = ticket(true)` — const, line 336
- `const result = await api.workbenchOpen(` — const, line 338
- `const openItem = useCallback(async (request:` — const, line 348
- `const sent = ticket(true)` — const, line 350
- `const result = await api.workbenchOpen(` — const, line 352
- `const resume = useCallback(async (sessionId: string)` — const, line 362
- `const sent = ticket(true)` — const, line 363
- `const result = await api.workbenchOpen(` — const, line 369
- `const checkMe = props?.checkMe ?? null` — const, line 381
- `const openedCheckRef = useRef<` — const, line 382
- `const sent = ticket(true)` — const, line 387
- `const exercise = props?.exercise ?? null` — const, line 415
- `const openedExerciseRef = useRef<` — const, line 416
- `const sent = ticket(true)` — const, line 421
- `const resumeRequest = props?.resumeProblem ?? null` — const, line 451
- `const resumedRef = useRef<` — const, line 452
- `const reopenAbandoned = useCallback(async ()` — const, line 466
- `const update = useCallback((session: WorkbenchSessionDto, shownIn?: number)` — const, line 475
- `const current = activeRef.current` — const, line 477
- `const close = useCallback((session: WorkbenchSessionDto | null, options?:` — const, line 484
- `const shown = activeRef.current` — const, line 488
- `const target = session ?? shown?.session ?? null` — const, line 491
- `const submitted = useCallback((result: WorkbenchSubmitDto, shownIn?: number)` — const, line 506
- `const current = activeRef.current` — const, line 507
- `const shown = current !== null && (shownIn === undefined || shownIn === generation.current) && current.session.sessionId === result.session.sessionId && (!result.session.extractionId || result.session.extractionId === extractionRef.current)` — const, line 508
- `const spanId = result.session.spanIds[0] ?? current.session.spanIds[0] ?? ""` — const, line 515

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ReaderWorkbenchCheck`, `ReaderWorkbenchProps`, `ReaderWorkbenchResume`; references `ReaderWorkbenchCheck`, `ReaderWorkbenchProps`, `ReaderWorkbenchResume`
- [[Reference/Desktop/TypeScript/app/readerWorkbench|src/app/readerWorkbench.ts]] — import-or-re-export: `ReaderWorkbenchCheck`; references `ReaderWorkbenchCheck`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ReaderWorkbenchProps`, `useReaderWorkbench`; references `ReaderWorkbenchProps`, `useReaderWorkbench`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `ActiveWorkbench`, `ReaderWorkbench`; references `ActiveWorkbench`, `ReaderWorkbench`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderImportExerciseInput`, `SessionSnapshot`, `SourceLibraryCard`, `WorkbenchSessionDto`, `WorkbenchSubmitDto`, `WorkbenchSummaryDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `ReaderWorkbenchExercise`
- [[Reference/Desktop/TypeScript/screens/workbench/splitWidth|src/screens/workbench/splitWidth.ts]] — import-or-re-export; imports `SPLIT_STEP`, `clampSplitWidth`, `defaultSplitWidth`, `isNarrow`, `readSplitWidth`, `writeSplitWidth`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readerWorkbenchResume.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerWorkbenchResume.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerWorkbenchQueue.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerWorkbenchQueue.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/readerWorkbenchExercise.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerWorkbenchExercise.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/useReaderWorkbench.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderWorkbench.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
