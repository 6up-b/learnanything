---
title: "Desktop module · src/screens/reader/useReaderInquiry.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.useReaderInquiry"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts"
source_commit: "3c53842db1b523879e37e80906e17487f5431cab"
source_commit_timestamp: "2026-10-23T22:19:10-04:00"
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

# `src/screens/reader/useReaderInquiry.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `INQUIRY_CHECK_POLL_MS`, `INQUIRY_CHECK_MAX_POLLS`, `ReconnectState`, `InquiryCheckState` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts) |
| Source lines | 1172 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `3c53842db1b523879e37e80906e17487f5431cab` |
| Commit timestamp | `2026-10-23T22:19:10-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]]

## Public API

- `export const INQUIRY_CHECK_POLL_MS = 3000` — const, line 69
- `export const INQUIRY_CHECK_MAX_POLLS = 200` — const, line 70
- `export interface ReconnectState` — interface, line 89
- `export interface InquiryCheckState` — interface, line 97
- `export interface ReaderInquiryInput` — interface, line 113
- `export interface ReaderInquiry` — interface, line 159
- `export function useReaderInquiry(input: ReaderInquiryInput): ReaderInquiry` — function, line 216

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 17
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type SetStateAction, } from "react"` — type, line 20
- `type RailTab, type ReturnEntry, type ReturnStack, } from "./returnStack"` — type, line 62
- `type ReturnEntry, type ReturnStack, } from "./returnStack"` — type, line 63
- `type ReturnStack, } from "./returnStack"` — type, line 64
- `function spendRefusalLine(refusal: string | null | undefined): string` — function, line 74
- `function newKey(): string` — function, line 80
- `const askEpoch = useRef(0)` — const, line 228
- `const askPending = useRef(false)` — const, line 229
- `const askFindInputRef = useRef<HTMLInputElement | null>(null)` — const, line 235
- `const returnStackRef = useRef<ReturnStack>(EMPTY_STACK)` — const, line 241
- `const lastSourceRef = useRef<ReturnEntry | null>(null)` — const, line 243
- `const inquiryRef = useRef(false)` — const, line 245
- `const settleScrollRef = useRef<number | null>(null)` — const, line 247
- `const reconnectBaseRef = useRef(0)` — const, line 251
- `const inquiryJobsRef = useRef<Record<string,` — const, line 256
- `const resetInquiryState = useCallback(()` — const, line 266
- `const noteSourceOpened = useCallback(( card: SourceLibraryCard, extractionId: string, jumpSpan: string | undefined, via: "search" | "restore" | undefined, )` — const, line 288
- `const left = lastSourceRef.current` — const, line 299
- `const entry: ReturnEntry =` — const, line 301
- `const next = pushDetour(returnStackRef.current, left, entry)` — const, line 306
- `const rememberLeftSource = useCallback((entry: ReturnEntry)` — const, line 321
- `let cancelled = false` — let, line 330
- `const restored: ReaderExchange[] = result.exchanges.map((exchange)` — const, line 336
- `const live = new Map(current.map((exchange)` — const, line 355
- `const root = inquiry && hasDetour(returnStack) ? returnStack.entries[0] : null` — const, line 374
- `const saved = root && root.sourceId === render.sourceId && root.spanId ? root.spanId : readingSpan` — const, line 375
- `const passageLabel = useCallback((spanId: string | null): string` — const, line 386
- `const section = spanId ? guideSectionBySpan.get(spanId) : undefined` — const, line 387
- `const positionEntry = useCallback((): ReturnEntry | null` — const, line 393
- `const spanId = readingSpan ?? activeSpan` — const, line 395
- `const pushDetours = useCallback((entries: ReturnEntry[])` — const, line 404
- `const origin = positionEntry()` — const, line 406
- `let next = returnStackRef.current` — let, line 408
- `const before = next` — const, line 410
- `const peekPassage = useCallback((spanId: string)` — const, line 424
- `const here = readingSpan ?? activeSpan` — const, line 425
- `const inquiryRoot = useCallback((exchangeId: string): ReaderExchange | null` — const, line 437
- `const byId = new Map(history.map((exchange)` — const, line 438
- `let current = byId.get(exchangeId) ?? null` — let, line 439
- `const seen = new Set<string>()` — const, line 440
- `const showReconnect = useCallback((exchangeId: string, inline: boolean)` — const, line 450
- `const root = inquiryRoot(exchangeId)` — const, line 452
- `const restoreEntry = useCallback(async (next: ReturnStack, target: ReturnEntry, via: string)` — const, line 459
- `const previous = returnStackRef.current` — const, line 462
- `const returning = next.cursor === 0 ? unreturnedDetours(previous) : []` — const, line 465
- `const settled = markReturned(next, returning.map((detour)` — const, line 466
- `const card = (library ?? []).find((candidate)` — const, line 470
- `const openSource = openSourceRef.current` — const, line 471
- `const nextIds = new Set(ids)` — const, line 484
- `const now = Date.now()` — const, line 491
- `const inquiryExchange = stackInquiryExchange(previous)` — const, line 503
- `const onBodyScroll = useCallback(()` — const, line 513
- `const body = bodyRef.current` — const, line 518
- `const screen = Math.max(1, body.clientHeight)` — const, line 526
- `const settleFrom = settleScrollRef.current` — const, line 528
- `const onKey = (event: KeyboardEvent)` — const, line 543
- `const stack = returnStackRef.current` — const, line 547
- `const moved = event.key === "ArrowLeft" ? stackBack(stack) : stackForward(stack)` — const, line 548
- `const askJobRef = useRef<` — const, line 560
- `const submitAsk = useCallback(async ( asked: string, parent: ReaderExchange | null, // RW1b: a routed Ask runs in its routed answer mode, and its funnel event // names the intention and the entry (the intent box or its palette). override?:` — const, line 561
- `const groundingSpan = parent?.spanId ?? selection?.spanId ?? activeSpan` — const, line 571
- `const epoch = askEpoch.current` — const, line 574
- `const selectionSpanIds = parent ? parent.selectionSpanIds : selection ? [...new Set(selectionNodes(selection).map((n)` — const, line 579
- `const selectionQuote = parent ? parent.selectionQuoteMd : selection ? (selection.editedText ?? selection.quote).trim() || null : null` — const, line 582
- `const edited = !parent && selection?.editedText != null && selection.editedText.trim() !== selection.quote.trim()` — const, line 587
- `const selectionSourceQuote = parent ? parent.selectionSourceQuoteMd ?? null : edited && selection ? selection.quote.trim() || null : null` — const, line 588
- `const jobKind = parent ? "follow_up" : "ask"` — const, line 591
- `const job =` — const, line 592
- `const answer = await api.readerAsk(` — const, line 599
- `const waited = Date.now() - job.startedAt` — const, line 618
- `const exchange: ReaderExchange =` — const, line 629
- `const branchEntry = (target: ReaderExchange, label: string): ReturnEntry` — const, line 660
- `const pushes: ReturnEntry[] = []` — const, line 665
- `const next = new Set(ids)` — const, line 675
- `const composerHadFocus = document.activeElement === askComposerRef.current` — const, line 685
- `const onAskTab = railTab === "ask"` — const, line 691
- `const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find( (element)` — const, line 696
- `const phase = phaseForError(error)` — const, line 704
- `const ask = useCallback(()` — const, line 731
- `const askAnotherWay = useCallback((exchange: ReaderExchange)` — const, line 737
- `const askDidntHelp = useCallback((exchange: ReaderExchange, text: string)` — const, line 745
- `const cancelAsk = useCallback(()` — const, line 753
- `const job = askJobRef.current` — const, line 754
- `const updateExchange = useCallback((id: string, patch: Partial<ReaderExchange>)` — const, line 774
- `const setInquiryStatus = useCallback(async (root: ReaderExchange, resolution: InquiryResolution, trigger: "chip" | "key" = "chip")` — const, line 778
- `const result = await api.readerSetInquiryStatus(` — const, line 781
- `const markBranchDone = useCallback(async (branch: ReaderExchange)` — const, line 790
- `const committedFor = useCallback((root: ReaderExchange): Set<InquiryCommitment>` — const, line 802
- `const done = new Set<InquiryCommitment>(inquiryCommitments[root.id] ?? [])` — const, line 803
- `const commitPendingRef = useRef<Set<string>>(new Set())` — const, line 817
- `const commitKeysRef = useRef<Record<string, string>>(` — const, line 818
- `const commitInquiry = useCallback(async (root: ReaderExchange, preset: InquiryCommitment)` — const, line 822
- `const slot = `$` — const, line 824
- `const key = commitKeysRef.current[slot] ?? (commitKeysRef.current[slot] = newKey())` — const, line 827
- `const spanIds = root.selectionSpanIds.length ? root.selectionSpanIds : [root.spanId]` — const, line 828
- `const receipt = await api.readerInvokePreset(` — const, line 830
- `const openInquiry = useCallback((rootId: string, fallbackSpanId?: string | null)` — const, line 858
- `const root = history.find((exchange)` — const, line 859
- `const next = new Set(ids)` — const, line 868
- `const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find( (element)` — const, line 881
- `const settleInquiryJob = useCallback((rootId: string, batchId: string | null, waitId: string | null, status: "completed" | "failed" | "cancelled", extra:` — const, line 894
- `const job = inquiryJobsRef.current[rootId]` — const, line 897
- `const waited = Date.now() - job.startedAt` — const, line 900
- `const recordUnqueuedCheck = useCallback((failureReason: string)` — const, line 913
- `const jobId = newActivityId()` — const, line 914
- `const startQuickCheck = useCallback(async (rootId: string, via: "inline" | "rail")` — const, line 925
- `const waitId = newKey()` — const, line 930
- `const visitIds = visitPayload()` — const, line 931
- `const startedAt = Date.now()` — const, line 932
- `const activity = learnerActivitySnapshot()` — const, line 933
- `const result = await api.readerReconnectAnswer(` — const, line 935
- `const batchId = result.batchId` — const, line 940
- `const tracked = inquiryJobsRef.current[rootId]` — const, line 941
- `const phase = phaseForError(error)` — const, line 959
- `const cancelQuickCheck = useCallback((rootId: string)` — const, line 967
- `const current = inquiryChecks[rootId]` — const, line 968
- `const wait = current?.batchId ?` — const, line 969
- `const batchId = wait?.batchId ?? null` — const, line 972
- `const dismissInquiryCheck = useCallback((rootId: string)` — const, line 982
- `const answerReconnect = useCallback(async (answer: "yes" | "still_unclear" | "quick_check", text = "")` — const, line 989
- `const line = reconnect` — const, line 990
- `const via = line.inline ? "inline" : "rail"` — const, line 992
- `const result = await api.readerReconnectAnswer(` — const, line 1000
- `const root = history.find((item)` — const, line 1009
- `const watching = Object.entries(inquiryChecks).filter( ([, check])` — const, line 1024
- `const extractionId = render.extractionId` — const, line 1028
- `const timer = window.setInterval(()` — const, line 1029
- `const batchId = check.batchId as string` — const, line 1031
- `const waitId = check.waitId as string` — const, line 1032
- `const attempts = (check.attempts ?? 0) + 1` — const, line 1033
- `const same = (checks: typeof inquiryChecks)` — const, line 1036
- `const timedOut = ()` — const, line 1037
- `const job = result.job ?? null` — const, line 1043
- `const landedQuestion = result.question` — const, line 1045
- `const code = job.errorCode ?? "error"` — const, line 1056
- `const phase: ModelActionPhase = code === "capped" ? "capped" : code === "provider_unavailable" ? "unreachable" : "failed"` — const, line 1058
- `const failure = code === "spend_refused" ? spendRefusalLine(job.refusal) : null` — const, line 1059
- `const phase = phaseForError(error)` — const, line 1070
- `const pollErrors = (check.pollErrors ?? 0) + 1` — const, line 1078
- `const inquiryCheckAction = useCallback(async (rootId: string, action: "answered" | "self_checked" | "dismissed", value?: string)` — const, line 1089
- `const check = inquiryChecks[rootId]` — const, line 1090
- `const result = await api.readerInquiryQuestionAction(` — const, line 1093
- `const escalateInquiryCheck = useCallback(async (rootId: string)` — const, line 1105
- `const check = inquiryChecks[rootId]` — const, line 1106
- `const passageCheckOffered = useMemo(()` — const, line 1121
- `const root = history.find((exchange)` — const, line 1123
- `const normalizedAskFind = askFindQuery.trim().toLowerCase()` — const, line 1132
- `const visibleAskHistory = useMemo( ()` — const, line 1133
- `const onFind = (event: KeyboardEvent)` — const, line 1146

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `useReaderInquiry`; references `useReaderInquiry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InquiryResolution`, `InquirySelfCheck`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderGuideSectionDto`, `ReaderInquiryQuestionDto`, `ReaderRenderViewDto`, `ReaderRetrievalIntent`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export; imports `InquiryCommitment`, `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export; imports `TUTOR_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`
- [[Reference/Desktop/TypeScript/screens/reader/checkOffer|src/screens/reader/checkOffer.ts]] — import-or-re-export; imports `checkOffer`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `MarginAnnotation`, `ReaderSelection`, `clip`, `selectionNodes`
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `EMPTY_STACK`, `RailTab`, `ReturnEntry`, `ReturnStack`, `hasDetour`, `markReturned`, `pushDetour`, `stackBack`, `stackForward`, `stackInquiryExchange`, `unreturnedDetours`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|src/screens/reader/useReaderVisit.ts]] — import-or-re-export; imports `ReaderVisit`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export; imports `encodeReadingPlace`, `readingPositionKey`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/readerHooks.parity.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
