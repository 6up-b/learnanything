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
source_commit: "9ed381bc3787439c88ffe3ec08b319b51049fa02"
source_commit_timestamp: "2026-11-01T03:48:43-05:00"
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
| Source lines | 934 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `9ed381bc3787439c88ffe3ec08b319b51049fa02` |
| Commit timestamp | `2026-11-01T03:48:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]]

## Public API

- `export const LIBRARY_COPY =` — const, line 59
- `export const SCOPE_COPY =` — const, line 89
- `export interface CompareRequest` — interface, line 132
- `export function comparePayload(request: CompareRequest): Required<CompareRequestDto>` — function, line 153
- `export interface ScopeChips` — interface, line 170
- `export type SourceCaller =` — type, line 190
- `export interface LibraryAskRequest` — interface, line 192
- `export const JOB_POLL_MS = 250` — const, line 220
- `export type LibraryAskIntent =` — type, line 242
- `export interface LibraryAskState` — interface, line 244
- `export function notesPhase(status: string): ModelActionPhase` — function, line 280
- `export function comparePhase(status: string): ModelActionPhase` — function, line 289
- `export function useLibraryAsk(` — function, line 304
- `export type LibraryAskController = ReturnType<typeof useLibraryAsk>` — type, line 934

## Internal implementation anchors

- `const COUNT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight"]` — const, line 126
- `function countWord(n: number): string` — function, line 127
- `interface Stage<T>` — interface, line 206
- `const IDLE =` — const, line 214
- `const CANCELLED =` — const, line 215
- `type JobStage = "ask" | "notes" | "compare" | "tutor" | "scope"` — type, line 217
- `const JOB_STAGES: JobStage[] = ["ask", "notes", "compare", "tutor", "scope"]` — const, line 218
- `function pause(ms: number): Promise<void>` — function, line 222
- `const SAYS_WHY = new Set(["exam_material", "comparison_withheld"])` — const, line 228
- `function failureLine(error: unknown, fallback: string): string` — function, line 231
- `const code = getCommandError(error)?.code` — const, line 232
- `function shownCompared(current: LibraryAskState): string[]` — function, line 298
- `const table = current.compare.value ?? current.previous?.[current.previous.length - 1] ?? null` — const, line 300
- `const openSourceRef = useRef(openSourceId)` — const, line 316
- `const openOf = useCallback((state: LibraryAskState | null | undefined): string | null` — const, line 318
- `const settings = contract?.libraryAsk ?? null` — const, line 320
- `const enabled = Boolean(settings)` — const, line 321
- `const keep = settings && contract?.compareKeep?.library ? contract.compareKeep : null` — const, line 323
- `const scopeOn = Boolean(settings?.compare && settings?.compareScope)` — const, line 325
- `const byPoint = Boolean(settings?.compare && settings?.compareByPoint)` — const, line 327
- `const keyRef = useRef(0)` — const, line 329
- `const stateRef = useRef<LibraryAskState | null>(null)` — const, line 330
- `const update = useCallback((key: number, patch: (current: LibraryAskState)` — const, line 333
- `const jobsRef = useRef<Partial<Record<JobStage, string>>>(` — const, line 339
- `const epochsRef = useRef<Record<JobStage, number>>(` — const, line 340
- `const cancelStage = useCallback((stage: JobStage)` — const, line 342
- `const jobId = jobsRef.current[stage]` — const, line 344
- `const runJob = useCallback(async <T,>(stage: JobStage, start: ()` — const, line 352
- `const epoch = epochsRef.current[stage]` — const, line 354
- `const live = ()` — const, line 355
- `let job = await start()` — let, line 357
- `const loadNotes = useCallback(async (key: number, askId: string)` — const, line 379
- `const notes = await runJob("notes", ()` — const, line 382
- `const runCompareRef = useRef<(key: number, askId: string, pins: string[])` — const, line 391
- `const run = useCallback(async (request: LibraryAskRequest, personalized: boolean, intent: LibraryAskIntent =` — const, line 393
- `const key = ++keyRef.current` — const, line 398
- `const comparing = intent.kind === "compare"` — const, line 399
- `const ask = await runJob("ask", ()` — const, line 407
- `const ask = useCallback((request: LibraryAskRequest)` — const, line 425
- `const retry = useCallback(()` — const, line 430
- `const current = stateRef.current` — const, line 431
- `const setPersonalized = useCallback((on: boolean)` — const, line 436
- `const current = stateRef.current` — const, line 437
- `const retryNotes = useCallback(()` — const, line 441
- `const current = stateRef.current` — const, line 442
- `const cancelNotes = useCallback(()` — const, line 447
- `const current = stateRef.current` — const, line 448
- `const cancelCompare = useCallback(()` — const, line 452
- `const current = stateRef.current` — const, line 453
- `const cancelTutor = useCallback(()` — const, line 457
- `const current = stateRef.current` — const, line 458
- `const togglePin = useCallback((hitKey: string)` — const, line 463
- `const current = stateRef.current` — const, line 464
- `const pinned = s.pinned.includes(hitKey) ? s.pinned.filter((k)` — const, line 467
- `const canCompare = (()` — const, line 474
- `const sources = new Set(state.pinned.map((k)` — const, line 476
- `const runCompare = useCallback(async (key: number, request: CompareRequest)` — const, line 481
- `const about = stateRef.current?.key === key ? stateRef.current.tutorBasis : null` — const, line 484
- `const table = await runJob("compare", ()` — const, line 493
- `const phase = comparePhase(table.status)` — const, line 495
- `const runPinsCompare = useCallback(async (key: number, askId: string, pinnedSpanKeys: string[], perspectives: string[] = [])` — const, line 507
- `const requested = keep?.perspectives ? perspectives.slice(0, keep.maxPerspectives) : []` — const, line 508
- `const openSourceId = openOf(stateRef.current)` — const, line 509
- `const table = await runJob("compare", ()` — const, line 518
- `const phase = comparePhase(table.status)` — const, line 521
- `const compare = useCallback(async (perspectives: string[] = [])` — const, line 530
- `const current = stateRef.current` — const, line 531
- `const compareWith = useCallback(async (request: LibraryAskRequest, pins: string[])` — const, line 542
- `const compareFrom = useCallback((request: CompareRequest, chips: ScopeChips | null = null, library: LibraryBookDto[] = [])` — const, line 548
- `const key = ++keyRef.current` — const, line 552
- `const query = request.question ?? ""` — const, line 553
- `const askBox = useCallback(async (request: LibraryAskRequest)` — const, line 567
- `const key = ++keyRef.current` — const, line 574
- `let reading: CompareScopeReadingDto | null = null` — let, line 579
- `const titles = new Map((reading.library ?? []).map((book)` — const, line 587
- `const missed = !reading || reading.status === "fallback" && reading.reason !== "too_few_books" && reading.reason !== "cold_attempt"` — const, line 599
- `const compareAll = useCallback(()` — const, line 604
- `const current = stateRef.current` — const, line 605
- `const compareBooks = useCallback(()` — const, line 615
- `const current = stateRef.current` — const, line 616
- `const ask = current?.ask.value` — const, line 617
- `const seen = new Map<string, string>()` — const, line 619
- `const books = [...seen].map(([sourceId, title])` — const, line 621
- `const comparisonAskId = (current: LibraryAskState): string | null` — const, line 630
- `const compareChosen = useCallback((current: LibraryAskState, books: LibraryBookDto[], chips: Partial<ScopeChips> =` — const, line 637
- `const key = current.key` — const, line 639
- `const last = current.lastCompare ?? current.direct ?? null` — const, line 640
- `const askId = comparisonAskId(current)` — const, line 653
- `const sourceIds = books.map((book)` — const, line 654
- `const requestedPerspectives = perspectives ?? last?.requestedPerspectives ?? []` — const, line 655
- `const base = stateRef.current?.chips ?? current.chips` — const, line 661
- `const setBooks = useCallback((books: LibraryBookDto[])` — const, line 667
- `const current = stateRef.current` — const, line 668
- `const judgmentId = current.chips.judgmentId` — const, line 671
- `const reword = useCallback((): string | null` — const, line 679
- `const current = stateRef.current` — const, line 680
- `const chips = current?.chips` — const, line 681
- `const judgmentId = chips?.askJudgmentId ?? null` — const, line 683
- `const refine = useCallback(async (words: string)` — const, line 691
- `const current = stateRef.current` — const, line 692
- `const text = words.trim()` — const, line 693
- `const key = current.key` — const, line 695
- `const compared = current.chips.books.length ? current.chips.books : (current.compare.value?.rows ?? []).flatMap((row)` — const, line 696
- `let reading: CompareScopeReadingDto | null = null` — let, line 699
- `const now = stateRef.current?.key === key ? stateRef.current : null` — const, line 707
- `const askId = now ? comparisonAskId(now) : null` — const, line 708
- `const titles = new Map([...(reading.library ?? []), ...compared].map((book)` — const, line 710
- `const named = reading.sourceIds` — const, line 711
- `const ids = reading.change === "add" ? [...new Set([...compared.map((book)` — const, line 712
- `const books = ids.map((sourceId)` — const, line 714
- `const before = now.lastCompare?.requestedPerspectives ?? []` — const, line 723
- `const requested = [...before.filter((value)` — const, line 730
- `const replaceView = useCallback((remove: string)` — const, line 741
- `const current = stateRef.current` — const, line 742
- `const limit = current?.viewLimit` — const, line 743
- `const askId = current ? comparisonAskId(current) : null` — const, line 744
- `const compared = shownCompared(current)` — const, line 746
- `const keepViews = useCallback(()` — const, line 751
- `const current = stateRef.current` — const, line 752
- `const askTutor = useCallback(async (question: string, about?: "pins" | "comparison")` — const, line 763
- `const current = stateRef.current` — const, line 764
- `const basis = about ?? (current.pinned.length || !current.direct ? "pins" : "comparison")` — const, line 766
- `const shown = basis === "comparison" ? current.compare.value : null` — const, line 767
- `const comparisonId = shown?.comparisonId ?? null` — const, line 768
- `const passagesId = comparisonId ? null : shown?.passagesId ?? null` — const, line 769
- `const pins = basis !== "comparison" ? current.pinned : []` — const, line 770
- `const askIdOf = basis === "comparison" ? shown?.askId ?? null : current.ask.value?.askId ?? null` — const, line 771
- `const key = current.key` — const, line 773
- `const askId = askIdOf` — const, line 775
- `const pinnedSpanKeys = pins` — const, line 776
- `const answer = await runJob("tutor", ()` — const, line 778
- `const practice = useCallback(async ()` — const, line 790
- `const current = stateRef.current` — const, line 791
- `const ask = current?.ask.value ?? (current?.direct ?` — const, line 793
- `const key = current.key` — const, line 797
- `const result = await api.findPractice(` — const, line 800
- `const peek = useCallback(async (hitKey: string, title: string | null = null)` — const, line 818
- `const current = stateRef.current` — const, line 819
- `const hit = current?.ask.value?.hits.find((h)` — const, line 820
- `const at = hitKey.indexOf(":")` — const, line 823
- `const target = hit ?` — const, line 824
- `const key = current.key` — const, line 827
- `const closePeek = useCallback(()` — const, line 838
- `const current = stateRef.current` — const, line 839
- `const close = useCallback(()` — const, line 844
- `const retryCompare = useCallback(()` — const, line 867
- `const current = stateRef.current` — const, line 868
- `const last = current?.lastCompare` — const, line 869
- `const compareAgain = useCallback((table: CompareTableDto)` — const, line 875
- `const current = stateRef.current` — const, line 876
- `const pinnedSpanKeys = table.rows.map((row)` — const, line 878
- `const requested = keep?.perspectives ? (table.requestedPerspectives ?? []).slice(0, keep.maxPerspectives) : []` — const, line 880
- `const openSourceId = openOf(current)` — const, line 881
- `const sourceIds = [...new Set(table.rows.map((row)` — const, line 886
- `const key = current.key` — const, line 891
- `const next = await runJob("compare", ()` — const, line 895
- `const phase = comparePhase(next.status)` — const, line 899
- `const whereElse = useCallback((words: string, asked: string | null = null)` — const, line 912
- `const current = stateRef.current` — const, line 913
- `const view = words.trim()` — const, line 914
- `const question = (asked ?? current.compare.value?.scope?.question ?? current.compare.value?.query ?? current.request.query ?? "").trim()` — const, line 916

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`; references `CompareRequest`, `SCOPE_COPY`, `useLibraryAsk`
- [[Reference/Desktop/TypeScript/screens/reader/CompareScope|src/screens/reader/CompareScope.tsx]] — import-or-re-export: `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`, `ScopeChips`; references `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`, `ScopeChips`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|src/screens/reader/LibraryAnswer.tsx]] — import-or-re-export: `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`; references `LIBRARY_COPY`, `LibraryAskController`, `SCOPE_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|src/screens/reader/LibraryPane.tsx]] — import-or-re-export: `LIBRARY_COPY`, `LibraryAskController`; references `LIBRARY_COPY`, `LibraryAskController`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryExercises|src/screens/reader/useLibraryExercises.ts]] — import-or-re-export: `JOB_POLL_MS`; references `JOB_POLL_MS`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CompareDoor`, `CompareRequestDto`, `CompareScopeReadingDto`, `CompareTableDto`, `FindPracticeResultDto`, `LibraryAskDto`, `LibraryAskEntry`, `LibraryBookDto`, `LibraryJobDto`, `LibraryNotesDto`, `LibraryTutorDto`, `ReaderPromptContractDto`, `SourceIdentity`, `SpanViewDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`

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

- [apps/learnloop-tauri/src/screens/reader/libraryExercises.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/libraryExercises.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/libraryAskJobs.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/libraryAskJobs.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/findSectionReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/advancedPanels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareScopeCodexReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareScopeCodexReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/compareScope.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/compareScope.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/comparePointTableCodexReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTableCodexReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/comparePointTable.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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
