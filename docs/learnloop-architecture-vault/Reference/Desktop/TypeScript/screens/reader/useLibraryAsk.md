---
title: "Desktop module · src/screens/reader/useLibraryAsk.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useLibraryAsk"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useLibraryAsk.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useLibraryAsk.ts"
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

# `src/screens/reader/useLibraryAsk.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `LIBRARY_COPY`, `SCOPE_COPY`, `CompareRequest`, `comparePayload` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useLibraryAsk.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useLibraryAsk.ts) |
| Source lines | 940 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]]

## Public API

- `export const LIBRARY_COPY =` — const, line 61
- `export const SCOPE_COPY =` — const, line 91
- `export interface CompareRequest` — interface, line 134
- `export function comparePayload(request: CompareRequest): Required<CompareRequestDto>` — function, line 155
- `export interface ScopeChips` — interface, line 172
- `export type SourceCaller =` — type, line 192
- `export interface LibraryAskRequest` — interface, line 194
- `export const JOB_POLL_MS = 250` — const, line 222
- `export type LibraryAskIntent =` — type, line 244
- `export interface LibraryAskState` — interface, line 246
- `export function notesPhase(status: string): ModelActionPhase` — function, line 282
- `export function comparePhase(status: string): ModelActionPhase` — function, line 291
- `export function useLibraryAsk(` — function, line 306
- `export type LibraryAskController = ReturnType<typeof useLibraryAsk>` — type, line 940

## Internal implementation anchors

- `const COUNT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight"]` — const, line 128
- `function countWord(n: number): string` — function, line 129
- `interface Stage<T>` — interface, line 208
- `const IDLE =` — const, line 216
- `const CANCELLED =` — const, line 217
- `type JobStage = "ask" | "notes" | "compare" | "tutor" | "scope"` — type, line 219
- `const JOB_STAGES: JobStage[] = ["ask", "notes", "compare", "tutor", "scope"]` — const, line 220
- `function pause(ms: number): Promise<void>` — function, line 224
- `const SAYS_WHY = new Set(["exam_material", "comparison_withheld"])` — const, line 230
- `function failureLine(error: unknown, fallback: string): string` — function, line 233
- `const code = getCommandError(error)?.code` — const, line 234
- `function shownCompared(current: LibraryAskState): string[]` — function, line 300
- `const table = current.compare.value ?? current.previous?.[current.previous.length - 1] ?? null` — const, line 302
- `const openSourceRef = useRef(openSourceId)` — const, line 318
- `const openOf = useCallback((state: LibraryAskState | null | undefined): string | null` — const, line 320
- `const settings = contract?.libraryAsk ?? null` — const, line 322
- `const enabled = Boolean(settings)` — const, line 323
- `const keep = settings && contract?.compareKeep?.library ? contract.compareKeep : null` — const, line 325
- `const scopeOn = Boolean(settings?.compare && settings?.compareScope)` — const, line 327
- `const byPoint = Boolean(settings?.compare && settings?.compareByPoint)` — const, line 329
- `const keyRef = useRef(0)` — const, line 331
- `const stateRef = useRef<LibraryAskState | null>(null)` — const, line 332
- `const update = useCallback((key: number, patch: (current: LibraryAskState)` — const, line 335
- `const jobsRef = useRef<Partial<Record<JobStage, string>>>(` — const, line 341
- `const whenLive = useWhenLive()` — const, line 342
- `const epochsRef = useRef<Record<JobStage, number>>(` — const, line 343
- `const cancelStage = useCallback((stage: JobStage)` — const, line 345
- `const jobId = jobsRef.current[stage]` — const, line 347
- `const runJob = useCallback(async <T,>(stage: JobStage, start: ()` — const, line 355
- `const epoch = epochsRef.current[stage]` — const, line 357
- `const live = ()` — const, line 358
- `let job = await start()` — let, line 360
- `const loadNotes = useCallback(async (key: number, askId: string)` — const, line 384
- `const notes = await runJob("notes", ()` — const, line 387
- `const runCompareRef = useRef<(key: number, askId: string, pins: string[])` — const, line 396
- `const run = useCallback(async (request: LibraryAskRequest, personalized: boolean, intent: LibraryAskIntent =` — const, line 398
- `const key = ++keyRef.current` — const, line 403
- `const comparing = intent.kind === "compare"` — const, line 404
- `const ask = await runJob("ask", ()` — const, line 412
- `const ask = useCallback((request: LibraryAskRequest)` — const, line 431
- `const retry = useCallback(()` — const, line 436
- `const current = stateRef.current` — const, line 437
- `const setPersonalized = useCallback((on: boolean)` — const, line 442
- `const current = stateRef.current` — const, line 443
- `const retryNotes = useCallback(()` — const, line 447
- `const current = stateRef.current` — const, line 448
- `const cancelNotes = useCallback(()` — const, line 453
- `const current = stateRef.current` — const, line 454
- `const cancelCompare = useCallback(()` — const, line 458
- `const current = stateRef.current` — const, line 459
- `const cancelTutor = useCallback(()` — const, line 463
- `const current = stateRef.current` — const, line 464
- `const togglePin = useCallback((hitKey: string)` — const, line 469
- `const current = stateRef.current` — const, line 470
- `const pinned = s.pinned.includes(hitKey) ? s.pinned.filter((k)` — const, line 473
- `const canCompare = (()` — const, line 480
- `const sources = new Set(state.pinned.map((k)` — const, line 482
- `const runCompare = useCallback(async (key: number, request: CompareRequest)` — const, line 487
- `const about = stateRef.current?.key === key ? stateRef.current.tutorBasis : null` — const, line 490
- `const table = await runJob("compare", ()` — const, line 499
- `const phase = comparePhase(table.status)` — const, line 501
- `const runPinsCompare = useCallback(async (key: number, askId: string, pinnedSpanKeys: string[], perspectives: string[] = [])` — const, line 513
- `const requested = keep?.perspectives ? perspectives.slice(0, keep.maxPerspectives) : []` — const, line 514
- `const openSourceId = openOf(stateRef.current)` — const, line 515
- `const table = await runJob("compare", ()` — const, line 524
- `const phase = comparePhase(table.status)` — const, line 527
- `const compare = useCallback(async (perspectives: string[] = [])` — const, line 536
- `const current = stateRef.current` — const, line 537
- `const compareWith = useCallback(async (request: LibraryAskRequest, pins: string[])` — const, line 548
- `const compareFrom = useCallback((request: CompareRequest, chips: ScopeChips | null = null, library: LibraryBookDto[] = [])` — const, line 554
- `const key = ++keyRef.current` — const, line 558
- `const query = request.question ?? ""` — const, line 559
- `const askBox = useCallback(async (request: LibraryAskRequest)` — const, line 573
- `const key = ++keyRef.current` — const, line 580
- `let reading: CompareScopeReadingDto | null = null` — let, line 585
- `const titles = new Map((reading.library ?? []).map((book)` — const, line 593
- `const missed = !reading || reading.status === "fallback" && reading.reason !== "too_few_books" && reading.reason !== "cold_attempt"` — const, line 605
- `const compareAll = useCallback(()` — const, line 610
- `const current = stateRef.current` — const, line 611
- `const compareBooks = useCallback(()` — const, line 621
- `const current = stateRef.current` — const, line 622
- `const ask = current?.ask.value` — const, line 623
- `const seen = new Map<string, string>()` — const, line 625
- `const books = [...seen].map(([sourceId, title])` — const, line 627
- `const comparisonAskId = (current: LibraryAskState): string | null` — const, line 636
- `const compareChosen = useCallback((current: LibraryAskState, books: LibraryBookDto[], chips: Partial<ScopeChips> =` — const, line 643
- `const key = current.key` — const, line 645
- `const last = current.lastCompare ?? current.direct ?? null` — const, line 646
- `const askId = comparisonAskId(current)` — const, line 659
- `const sourceIds = books.map((book)` — const, line 660
- `const requestedPerspectives = perspectives ?? last?.requestedPerspectives ?? []` — const, line 661
- `const base = stateRef.current?.chips ?? current.chips` — const, line 667
- `const setBooks = useCallback((books: LibraryBookDto[])` — const, line 673
- `const current = stateRef.current` — const, line 674
- `const judgmentId = current.chips.judgmentId` — const, line 677
- `const reword = useCallback((): string | null` — const, line 685
- `const current = stateRef.current` — const, line 686
- `const chips = current?.chips` — const, line 687
- `const judgmentId = chips?.askJudgmentId ?? null` — const, line 689
- `const refine = useCallback(async (words: string)` — const, line 697
- `const current = stateRef.current` — const, line 698
- `const text = words.trim()` — const, line 699
- `const key = current.key` — const, line 701
- `const compared = current.chips.books.length ? current.chips.books : (current.compare.value?.rows ?? []).flatMap((row)` — const, line 702
- `let reading: CompareScopeReadingDto | null = null` — let, line 705
- `const now = stateRef.current?.key === key ? stateRef.current : null` — const, line 713
- `const askId = now ? comparisonAskId(now) : null` — const, line 714
- `const titles = new Map([...(reading.library ?? []), ...compared].map((book)` — const, line 716
- `const named = reading.sourceIds` — const, line 717
- `const ids = reading.change === "add" ? [...new Set([...compared.map((book)` — const, line 718
- `const books = ids.map((sourceId)` — const, line 720
- `const before = now.lastCompare?.requestedPerspectives ?? []` — const, line 729
- `const requested = [...before.filter((value)` — const, line 736
- `const replaceView = useCallback((remove: string)` — const, line 747
- `const current = stateRef.current` — const, line 748
- `const limit = current?.viewLimit` — const, line 749
- `const askId = current ? comparisonAskId(current) : null` — const, line 750
- `const compared = shownCompared(current)` — const, line 752
- `const keepViews = useCallback(()` — const, line 757
- `const current = stateRef.current` — const, line 758
- `const askTutor = useCallback(async (question: string, about?: "pins" | "comparison")` — const, line 769
- `const current = stateRef.current` — const, line 770
- `const basis = about ?? (current.pinned.length || !current.direct ? "pins" : "comparison")` — const, line 772
- `const shown = basis === "comparison" ? current.compare.value : null` — const, line 773
- `const comparisonId = shown?.comparisonId ?? null` — const, line 774
- `const passagesId = comparisonId ? null : shown?.passagesId ?? null` — const, line 775
- `const pins = basis !== "comparison" ? current.pinned : []` — const, line 776
- `const askIdOf = basis === "comparison" ? shown?.askId ?? null : current.ask.value?.askId ?? null` — const, line 777
- `const key = current.key` — const, line 779
- `const askId = askIdOf` — const, line 781
- `const pinnedSpanKeys = pins` — const, line 782
- `const answer = await runJob("tutor", ()` — const, line 784
- `const practice = useCallback(async ()` — const, line 796
- `const current = stateRef.current` — const, line 797
- `const ask = current?.ask.value ?? (current?.direct ?` — const, line 799
- `const key = current.key` — const, line 803
- `const result = await api.findPractice(` — const, line 806
- `const peek = useCallback(async (hitKey: string, title: string | null = null)` — const, line 824
- `const current = stateRef.current` — const, line 825
- `const hit = current?.ask.value?.hits.find((h)` — const, line 826
- `const at = hitKey.indexOf(":")` — const, line 829
- `const target = hit ?` — const, line 830
- `const key = current.key` — const, line 833
- `const closePeek = useCallback(()` — const, line 844
- `const current = stateRef.current` — const, line 845
- `const close = useCallback(()` — const, line 850
- `const retryCompare = useCallback(()` — const, line 873
- `const current = stateRef.current` — const, line 874
- `const last = current?.lastCompare` — const, line 875
- `const compareAgain = useCallback((table: CompareTableDto)` — const, line 881
- `const current = stateRef.current` — const, line 882
- `const pinnedSpanKeys = table.rows.map((row)` — const, line 884
- `const requested = keep?.perspectives ? (table.requestedPerspectives ?? []).slice(0, keep.maxPerspectives) : []` — const, line 886
- `const openSourceId = openOf(current)` — const, line 887
- `const sourceIds = [...new Set(table.rows.map((row)` — const, line 892
- `const key = current.key` — const, line 897
- `const next = await runJob("compare", ()` — const, line 901
- `const phase = comparePhase(next.status)` — const, line 905
- `const whereElse = useCallback((words: string, asked: string | null = null)` — const, line 918
- `const current = stateRef.current` — const, line 919
- `const view = words.trim()` — const, line 920
- `const question = (asked ?? current.compare.value?.scope?.question ?? current.compare.value?.query ?? current.request.query ?? "").trim()` — const, line 922

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/source/ScopedSource|src/screens/desks/source/ScopedSource.tsx]] — import-or-re-export: `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`; references `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`
- [[Reference/Desktop/TypeScript/screens/desks/windows/PanelWindow|src/screens/desks/windows/PanelWindow.tsx]] — import-or-re-export: `useLibraryAsk`; references `useLibraryAsk`
- [[Reference/Desktop/TypeScript/screens/reader/CompareScope|src/screens/reader/CompareScope.tsx]] — import-or-re-export: `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`, `ScopeChips`; references `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`, `ScopeChips`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`; references `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export: `LIBRARY_COPY`, `LibraryAskController`; references `LIBRARY_COPY`, `LibraryAskController`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryExercises|src/screens/reader/useLibraryExercises.ts]] — import-or-re-export: `JOB_POLL_MS`; references `JOB_POLL_MS`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompareDoor`, `CompareRequestDto`, `CompareScopeReadingDto`, `CompareTableDto`, `FindPracticeResultDto`, `LibraryAskDto`, `LibraryAskEntry`, `LibraryBookDto`, `LibraryJobDto`, `LibraryNotesDto`, `LibraryTutorDto`, `ReaderPromptContractDto`, `SourceIdentity`, `SpanViewDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWhenLive`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `passageKeys`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.
- [[Workflows/Import Canonical Sources|Import Canonical Sources]] — owns import sequencing.
- [[Architecture/Content Pipeline#Durable checkpoint ladder|content checkpoint ladder]] — owns pipeline persistence semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/pausedProducers.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/pausedProducers.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryExercises.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/libraryExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryAskJobs.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/libraryAskJobs.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareScopeCodexReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareScopeCodexReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareScope.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareScope.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/comparePointTableCodexReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTableCodexReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/useLibraryAsk.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useLibraryAsk.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
