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
source_commit: "42fc3a995cf040e1c4fd84e7656601631e56cb84"
source_commit_timestamp: "2026-10-31T19:41:54-04:00"
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
| Source lines | 1210 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `42fc3a995cf040e1c4fd84e7656601631e56cb84` |
| Commit timestamp | `2026-10-31T19:41:54-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]]

## Public API

- `export const INQUIRY_CHECK_POLL_MS = 3000` — const, line 72
- `export const INQUIRY_CHECK_MAX_POLLS = 200` — const, line 73
- `export interface ReconnectState` — interface, line 92
- `export interface InquiryCheckState` — interface, line 100
- `export interface ReaderInquiryInput` — interface, line 116
- `export interface ReaderInquiry` — interface, line 162
- `export function useReaderInquiry(input: ReaderInquiryInput): ReaderInquiry` — function, line 227

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 17
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type SetStateAction, } from "react"` — type, line 20
- `type RailTab, type ReturnEntry, type ReturnStack, } from "./returnStack"` — type, line 65
- `type ReturnEntry, type ReturnStack, } from "./returnStack"` — type, line 66
- `type ReturnStack, } from "./returnStack"` — type, line 67
- `function spendRefusalLine(refusal: string | null | undefined): string` — function, line 77
- `function newKey(): string` — function, line 83
- `const askEpoch = useRef(0)` — const, line 239
- `const askPending = useRef(false)` — const, line 240
- `const askFindInputRef = useRef<HTMLInputElement | null>(null)` — const, line 246
- `const returnStackRef = useRef<ReturnStack>(EMPTY_STACK)` — const, line 252
- `const lastSourceRef = useRef<ReturnEntry | null>(null)` — const, line 254
- `const inquiryRef = useRef(false)` — const, line 256
- `const settleScrollRef = useRef<number | null>(null)` — const, line 258
- `const reconnectBaseRef = useRef(0)` — const, line 262
- `const inquiryJobsRef = useRef<Record<string,` — const, line 267
- `const resetInquiryState = useCallback(()` — const, line 277
- `const noteSourceOpened = useCallback(( card: SourceLibraryCard, extractionId: string, jumpSpan: string | undefined, via: "search" | "restore" | undefined, )` — const, line 299
- `const left = lastSourceRef.current` — const, line 310
- `const entry: ReturnEntry =` — const, line 312
- `const next = pushDetour(returnStackRef.current, left, entry)` — const, line 317
- `const rememberLeftSource = useCallback((entry: ReturnEntry)` — const, line 332
- `let cancelled = false` — let, line 341
- `const restored: ReaderExchange[] = result.exchanges.map((exchange)` — const, line 347
- `const live = new Map(current.map((exchange)` — const, line 366
- `const root = inquiry && hasDetour(returnStack) ? returnStack.entries[0] : null` — const, line 385
- `const saved = root && root.sourceId === render.sourceId && root.spanId ? root.spanId : readingSpan` — const, line 386
- `const passageLabel = useCallback((spanId: string | null): string` — const, line 397
- `const section = spanId ? guideSectionBySpan.get(spanId) : undefined` — const, line 398
- `const positionEntry = useCallback((): ReturnEntry | null` — const, line 404
- `const spanId = readingSpan ?? activeSpan` — const, line 406
- `const pushDetours = useCallback((entries: ReturnEntry[])` — const, line 415
- `const origin = positionEntry()` — const, line 417
- `let next = returnStackRef.current` — let, line 419
- `const before = next` — const, line 421
- `const pushSideBySide = useCallback((label: string, target: PaneTarget): string | null` — const, line 435
- `const entry: ReturnEntry =` — const, line 437
- `const before = returnStackRef.current` — const, line 442
- `const replaceSideBySide = useCallback((entryId: string, label: string, target: PaneTarget): boolean` — const, line 447
- `const next = replaceCurrent(returnStackRef.current, entryId,` — const, line 448
- `const dropDetour = useCallback((entryId: string)` — const, line 455
- `const next = dropCurrent(returnStackRef.current, entryId)` — const, line 456
- `const peekPassage = useCallback((spanId: string)` — const, line 462
- `const here = readingSpan ?? activeSpan` — const, line 463
- `const inquiryRoot = useCallback((exchangeId: string): ReaderExchange | null` — const, line 475
- `const byId = new Map(history.map((exchange)` — const, line 476
- `let current = byId.get(exchangeId) ?? null` — let, line 477
- `const seen = new Set<string>()` — const, line 478
- `const showReconnect = useCallback((exchangeId: string, inline: boolean)` — const, line 488
- `const root = inquiryRoot(exchangeId)` — const, line 490
- `const restoreEntry = useCallback(async (next: ReturnStack, target: ReturnEntry, via: string)` — const, line 497
- `const previous = returnStackRef.current` — const, line 500
- `const returning = next.cursor === 0 ? unreturnedDetours(previous) : []` — const, line 503
- `const settled = markReturned(next, returning.map((detour)` — const, line 504
- `const card = (library ?? []).find((candidate)` — const, line 508
- `const openSource = openSourceRef.current` — const, line 509
- `const nextIds = new Set(ids)` — const, line 522
- `const now = Date.now()` — const, line 529
- `const inquiryExchange = stackInquiryExchange(previous)` — const, line 541
- `const onBodyScroll = useCallback(()` — const, line 551
- `const body = bodyRef.current` — const, line 556
- `const screen = Math.max(1, body.clientHeight)` — const, line 564
- `const settleFrom = settleScrollRef.current` — const, line 566
- `const onKey = (event: KeyboardEvent)` — const, line 581
- `const stack = returnStackRef.current` — const, line 585
- `const moved = event.key === "ArrowLeft" ? stackBack(stack) : stackForward(stack)` — const, line 586
- `const askJobRef = useRef<` — const, line 598
- `const submitAsk = useCallback(async ( asked: string, parent: ReaderExchange | null, // RW1b: a routed Ask runs in its routed answer mode, and its funnel event // names the intention and the entry (the intent box or its palette). override?:` — const, line 599
- `const groundingSpan = parent?.spanId ?? selection?.spanId ?? activeSpan` — const, line 609
- `const epoch = askEpoch.current` — const, line 612
- `const selectionSpanIds = parent ? parent.selectionSpanIds : selection ? [...new Set(selectionNodes(selection).map((n)` — const, line 617
- `const selectionQuote = parent ? parent.selectionQuoteMd : selection ? (selection.editedText ?? selection.quote).trim() || null : null` — const, line 620
- `const edited = !parent && selection?.editedText != null && selection.editedText.trim() !== selection.quote.trim()` — const, line 625
- `const selectionSourceQuote = parent ? parent.selectionSourceQuoteMd ?? null : edited && selection ? selection.quote.trim() || null : null` — const, line 626
- `const jobKind = parent ? "follow_up" : "ask"` — const, line 629
- `const job =` — const, line 630
- `const answer = await api.readerAsk(` — const, line 637
- `const waited = Date.now() - job.startedAt` — const, line 656
- `const exchange: ReaderExchange =` — const, line 667
- `const branchEntry = (target: ReaderExchange, label: string): ReturnEntry` — const, line 698
- `const pushes: ReturnEntry[] = []` — const, line 703
- `const next = new Set(ids)` — const, line 713
- `const composerHadFocus = document.activeElement === askComposerRef.current` — const, line 723
- `const onAskTab = railTab === "ask"` — const, line 729
- `const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find( (element)` — const, line 734
- `const phase = phaseForError(error)` — const, line 742
- `const ask = useCallback(()` — const, line 769
- `const askAnotherWay = useCallback((exchange: ReaderExchange)` — const, line 775
- `const askDidntHelp = useCallback((exchange: ReaderExchange, text: string)` — const, line 783
- `const cancelAsk = useCallback(()` — const, line 791
- `const job = askJobRef.current` — const, line 792
- `const updateExchange = useCallback((id: string, patch: Partial<ReaderExchange>)` — const, line 812
- `const setInquiryStatus = useCallback(async (root: ReaderExchange, resolution: InquiryResolution, trigger: "chip" | "key" = "chip")` — const, line 816
- `const result = await api.readerSetInquiryStatus(` — const, line 819
- `const markBranchDone = useCallback(async (branch: ReaderExchange)` — const, line 828
- `const committedFor = useCallback((root: ReaderExchange): Set<InquiryCommitment>` — const, line 840
- `const done = new Set<InquiryCommitment>(inquiryCommitments[root.id] ?? [])` — const, line 841
- `const commitPendingRef = useRef<Set<string>>(new Set())` — const, line 855
- `const commitKeysRef = useRef<Record<string, string>>(` — const, line 856
- `const commitInquiry = useCallback(async (root: ReaderExchange, preset: InquiryCommitment)` — const, line 860
- `const slot = `$` — const, line 862
- `const key = commitKeysRef.current[slot] ?? (commitKeysRef.current[slot] = newKey())` — const, line 865
- `const spanIds = root.selectionSpanIds.length ? root.selectionSpanIds : [root.spanId]` — const, line 866
- `const receipt = await api.readerInvokePreset(` — const, line 868
- `const openInquiry = useCallback((rootId: string, fallbackSpanId?: string | null)` — const, line 896
- `const root = history.find((exchange)` — const, line 897
- `const next = new Set(ids)` — const, line 906
- `const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find( (element)` — const, line 919
- `const settleInquiryJob = useCallback((rootId: string, batchId: string | null, waitId: string | null, status: "completed" | "failed" | "cancelled", extra:` — const, line 932
- `const job = inquiryJobsRef.current[rootId]` — const, line 935
- `const waited = Date.now() - job.startedAt` — const, line 938
- `const recordUnqueuedCheck = useCallback((failureReason: string)` — const, line 951
- `const jobId = newActivityId()` — const, line 952
- `const startQuickCheck = useCallback(async (rootId: string, via: "inline" | "rail")` — const, line 963
- `const waitId = newKey()` — const, line 968
- `const visitIds = visitPayload()` — const, line 969
- `const startedAt = Date.now()` — const, line 970
- `const activity = learnerActivitySnapshot()` — const, line 971
- `const result = await api.readerReconnectAnswer(` — const, line 973
- `const batchId = result.batchId` — const, line 978
- `const tracked = inquiryJobsRef.current[rootId]` — const, line 979
- `const phase = phaseForError(error)` — const, line 997
- `const cancelQuickCheck = useCallback((rootId: string)` — const, line 1005
- `const current = inquiryChecks[rootId]` — const, line 1006
- `const wait = current?.batchId ?` — const, line 1007
- `const batchId = wait?.batchId ?? null` — const, line 1010
- `const dismissInquiryCheck = useCallback((rootId: string)` — const, line 1020
- `const answerReconnect = useCallback(async (answer: "yes" | "still_unclear" | "quick_check", text = "")` — const, line 1027
- `const line = reconnect` — const, line 1028
- `const via = line.inline ? "inline" : "rail"` — const, line 1030
- `const result = await api.readerReconnectAnswer(` — const, line 1038
- `const root = history.find((item)` — const, line 1047
- `const watching = Object.entries(inquiryChecks).filter( ([, check])` — const, line 1062
- `const extractionId = render.extractionId` — const, line 1066
- `const timer = window.setInterval(()` — const, line 1067
- `const batchId = check.batchId as string` — const, line 1069
- `const waitId = check.waitId as string` — const, line 1070
- `const attempts = (check.attempts ?? 0) + 1` — const, line 1071
- `const same = (checks: typeof inquiryChecks)` — const, line 1074
- `const timedOut = ()` — const, line 1075
- `const job = result.job ?? null` — const, line 1081
- `const landedQuestion = result.question` — const, line 1083
- `const code = job.errorCode ?? "error"` — const, line 1094
- `const phase: ModelActionPhase = code === "capped" ? "capped" : code === "provider_unavailable" ? "unreachable" : "failed"` — const, line 1096
- `const failure = code === "spend_refused" ? spendRefusalLine(job.refusal) : null` — const, line 1097
- `const phase = phaseForError(error)` — const, line 1108
- `const pollErrors = (check.pollErrors ?? 0) + 1` — const, line 1116
- `const inquiryCheckAction = useCallback(async (rootId: string, action: "answered" | "self_checked" | "dismissed", value?: string)` — const, line 1127
- `const check = inquiryChecks[rootId]` — const, line 1128
- `const result = await api.readerInquiryQuestionAction(` — const, line 1131
- `const escalateInquiryCheck = useCallback(async (rootId: string)` — const, line 1143
- `const check = inquiryChecks[rootId]` — const, line 1144
- `const passageCheckOffered = useMemo(()` — const, line 1159
- `const root = history.find((exchange)` — const, line 1161
- `const normalizedAskFind = askFindQuery.trim().toLowerCase()` — const, line 1170
- `const visibleAskHistory = useMemo( ()` — const, line 1171
- `const onFind = (event: KeyboardEvent)` — const, line 1184

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
- [[Reference/Desktop/TypeScript/screens/reader/returnStack|src/screens/reader/returnStack.ts]] — import-or-re-export; imports `EMPTY_STACK`, `RailTab`, `ReturnEntry`, `ReturnStack`, `dropCurrent`, `hasDetour`, `markReturned`, `pushDetour`, `replaceCurrent`, `stackBack`, `stackForward`, `stackInquiryExchange`, `unreturnedDetours`
- [[Reference/Desktop/TypeScript/screens/reader/sideBySide|src/screens/reader/sideBySide.ts]] — import-or-re-export; imports `PaneTarget`
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
