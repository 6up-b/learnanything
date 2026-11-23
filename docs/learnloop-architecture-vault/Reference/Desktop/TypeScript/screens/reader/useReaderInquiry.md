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

Provides `INQUIRY_CHECK_POLL_MS`, `INQUIRY_CHECK_MAX_POLLS`, `AskAnchor`, `AskOverride` and related exports within the desktop's TypeScript/screens/reader ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts](../../../../../../../apps/learnloop-tauri/src/screens/reader/useReaderInquiry.ts) |
| Source lines | 1370 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]]

## Public API

- `export const INQUIRY_CHECK_POLL_MS = 3000` — const, line 74
- `export const INQUIRY_CHECK_MAX_POLLS = 200` — const, line 75
- `export interface AskAnchor` — interface, line 95
- `export interface AskOverride` — interface, line 104
- `export interface ReconnectState` — interface, line 111
- `export interface InquiryCheckState` — interface, line 119
- `export interface ReaderInquiryInput` — interface, line 135
- `export interface ReaderInquiry` — interface, line 184
- `export function useReaderInquiry(input: ReaderInquiryInput): ReaderInquiry` — function, line 259

## Internal implementation anchors

- `type Dispatch, type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 17
- `type MutableRefObject, type RefObject, type SetStateAction, } from "react"` — type, line 18
- `type RefObject, type SetStateAction, } from "react"` — type, line 19
- `type SetStateAction, } from "react"` — type, line 20
- `type RailTab, type ReturnEntry, type ReturnStack, } from "./returnStack"` — type, line 66
- `type ReturnEntry, type ReturnStack, } from "./returnStack"` — type, line 67
- `type ReturnStack, } from "./returnStack"` — type, line 68
- `function spendRefusalLine(refusal: string | null | undefined): string` — function, line 79
- `function newKey(): string` — function, line 85
- `const askEpoch = useRef(0)` — const, line 271
- `const askPending = useRef(false)` — const, line 272
- `const historyRef = useRef(history)` — const, line 278
- `const askFindInputRef = useRef<HTMLInputElement | null>(null)` — const, line 283
- `const returnStackRef = useRef<ReturnStack>(EMPTY_STACK)` — const, line 289
- `const lastSourceRef = useRef<ReturnEntry | null>(null)` — const, line 291
- `const inquiryRef = useRef(false)` — const, line 293
- `const settleScrollRef = useRef<number | null>(null)` — const, line 295
- `const reconnectBaseRef = useRef(0)` — const, line 299
- `const inquiryJobsRef = useRef<Record<string,` — const, line 304
- `const failedAskRef = useRef<` — const, line 320
- `const composerGenRef = useRef(0)` — const, line 327
- `const composerOpenRef = useRef(0)` — const, line 334
- `const resetInquiryState = useCallback(()` — const, line 335
- `const noteSourceOpened = useCallback(( card: SourceLibraryCard, extractionId: string, jumpSpan: string | undefined, via: "search" | "restore" | undefined, )` — const, line 360
- `const left = lastSourceRef.current` — const, line 371
- `const entry: ReturnEntry =` — const, line 373
- `const next = pushDetour(returnStackRef.current, left, entry)` — const, line 378
- `const rememberLeftSource = useCallback((entry: ReturnEntry)` — const, line 393
- `let cancelled = false` — let, line 402
- `const restored: ReaderExchange[] = result.exchanges.map((exchange)` — const, line 408
- `const live = new Map(current.map((exchange)` — const, line 427
- `const root = inquiry && hasDetour(returnStack) ? returnStack.entries[0] : null` — const, line 446
- `const saved = root && root.sourceId === render.sourceId && root.spanId ? root.spanId : readingSpan` — const, line 447
- `const passageLabel = useCallback((spanId: string | null): string` — const, line 458
- `const section = spanId ? guideSectionBySpan.get(spanId) : undefined` — const, line 459
- `const positionEntry = useCallback((): ReturnEntry | null` — const, line 465
- `const spanId = readingSpan ?? activeSpan` — const, line 467
- `const pushDetours = useCallback((entries: ReturnEntry[])` — const, line 476
- `const origin = positionEntry()` — const, line 478
- `let next = returnStackRef.current` — let, line 480
- `const before = next` — const, line 482
- `const pushSideBySide = useCallback((label: string, target: PaneTarget): string | null` — const, line 496
- `const entry: ReturnEntry =` — const, line 498
- `const before = returnStackRef.current` — const, line 503
- `const replaceSideBySide = useCallback((entryId: string, label: string, target: PaneTarget): boolean` — const, line 508
- `const next = replaceCurrent(returnStackRef.current, entryId,` — const, line 509
- `const snapshotSideBySide = useCallback((label: string, target: PaneTarget): boolean` — const, line 521
- `const stack = returnStackRef.current` — const, line 522
- `const current = stack.entries[stack.cursor]` — const, line 523
- `const next = replaceCurrent(stack, current.id,` — const, line 525
- `const seedReturnStack = useCallback((stack: ReturnStack)` — const, line 534
- `const dropDetour = useCallback((entryId: string)` — const, line 540
- `const next = dropCurrent(returnStackRef.current, entryId)` — const, line 541
- `const peekPassage = useCallback((spanId: string)` — const, line 547
- `const here = readingSpan ?? activeSpan` — const, line 548
- `const inquiryRoot = useCallback((exchangeId: string): ReaderExchange | null` — const, line 560
- `const byId = new Map(history.map((exchange)` — const, line 561
- `let current = byId.get(exchangeId) ?? null` — let, line 562
- `const seen = new Set<string>()` — const, line 563
- `const showReconnect = useCallback((exchangeId: string, inline: boolean)` — const, line 573
- `const root = inquiryRoot(exchangeId)` — const, line 575
- `const restoreEntry = useCallback(async (next: ReturnStack, target: ReturnEntry, via: string)` — const, line 582
- `const previous = returnStackRef.current` — const, line 585
- `const returning = next.cursor === 0 ? unreturnedDetours(previous) : []` — const, line 588
- `const settled = markReturned(next, returning.map((detour)` — const, line 589
- `const card = (library ?? []).find((candidate)` — const, line 593
- `const openSource = openSourceRef.current` — const, line 594
- `const nextIds = new Set(ids)` — const, line 607
- `const now = Date.now()` — const, line 614
- `const inquiryExchange = stackInquiryExchange(previous)` — const, line 626
- `const onBodyScroll = useCallback(()` — const, line 636
- `const body = bodyRef.current` — const, line 641
- `const screen = Math.max(1, body.clientHeight)` — const, line 649
- `const settleFrom = settleScrollRef.current` — const, line 651
- `const hub = useListenerHub()` — const, line 664
- `const onKey = (event: KeyboardEvent)` — const, line 667
- `const stack = returnStackRef.current` — const, line 671
- `const moved = event.key === "ArrowLeft" ? stackBack(stack) : stackForward(stack)` — const, line 672
- `const askJobRef = useRef<` — const, line 683
- `const submitAsk = useCallback(async ( asked: string, parent: ReaderExchange | null, // RW1b: a routed Ask runs in its routed answer mode, and its funnel event // names the intention and the entry (the intent box or its palette). override?: AskOverride, )` — const, line 684
- `const anchor = parent ? null : override?.anchor ?? null` — const, line 696
- `const about = parent ? parent.about ?? null : anchor?.about ?? null` — const, line 697
- `const groundingSpan = parent?.spanId ?? anchor?.spanId ?? selection?.spanId ?? activeSpan` — const, line 698
- `const epoch = askEpoch.current` — const, line 701
- `const composer = composerGenRef.current` — const, line 702
- `const composerOpen = composerOpenRef.current` — const, line 703
- `const selectionSpanIds = parent ? parent.selectionSpanIds : anchor ? anchor.selectionSpanIds : selection ? [...new Set(selectionNodes(selection).map((n)` — const, line 709
- `const selectionQuote = parent ? parent.selectionQuoteMd : anchor ? anchor.selectionQuote : selection ? (selection.editedText ?? selection.quote).trim() || null : null` — const, line 713
- `const edited = !parent && !anchor && selection?.editedText != null && selection.editedText.trim() !== selection.quote.trim()` — const, line 719
- `const selectionSourceQuote = parent ? parent.selectionSourceQuoteMd ?? null : edited && selection ? selection.quote.trim() || null : null` — const, line 720
- `const jobKind = parent ? "follow_up" : "ask"` — const, line 723
- `const job =` — const, line 724
- `const askReading = about?.extractionId ?? render.extractionId` — const, line 731
- `const answer = await api.readerAsk(` — const, line 732
- `const waited = Date.now() - job.startedAt` — const, line 753
- `const exchange: ReaderExchange =` — const, line 764
- `const ownComposer = composerOpen === composerOpenRef.current` — const, line 791
- `const branchEntry = (target: ReaderExchange, label: string): ReturnEntry` — const, line 799
- `const pushes: ReturnEntry[] = []` — const, line 804
- `const next = new Set(ids)` — const, line 814
- `const composerHadFocus = document.activeElement === askComposerRef.current` — const, line 826
- `const onAskTab = railTab === "ask"` — const, line 832
- `const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find( (element)` — const, line 837
- `const phase = phaseForError(error)` — const, line 845
- `const ask = useCallback(()` — const, line 877
- `const failed = failedAskRef.current` — const, line 881
- `const anchor = composerAnchorRef?.current ?? null` — const, line 887
- `const retryAsk = useCallback(()` — const, line 896
- `const failed = failedAskRef.current` — const, line 897
- `const forgetFailedAsk = useCallback(()` — const, line 905
- `const askAnotherWay = useCallback((exchange: ReaderExchange)` — const, line 919
- `const askDidntHelp = useCallback((exchange: ReaderExchange, text: string)` — const, line 927
- `const cancelAsk = useCallback(()` — const, line 935
- `const job = askJobRef.current` — const, line 936
- `const extractionOf = useCallback((rootId: string): string` — const, line 957
- `const updateExchange = useCallback((id: string, patch: Partial<ReaderExchange>)` — const, line 961
- `const setInquiryStatus = useCallback(async (root: ReaderExchange, resolution: InquiryResolution, trigger: "chip" | "key" = "chip")` — const, line 965
- `const result = await api.readerSetInquiryStatus(` — const, line 968
- `const markBranchDone = useCallback(async (branch: ReaderExchange)` — const, line 977
- `const committedFor = useCallback((root: ReaderExchange): Set<InquiryCommitment>` — const, line 989
- `const done = new Set<InquiryCommitment>(inquiryCommitments[root.id] ?? [])` — const, line 990
- `const commitPendingRef = useRef<Set<string>>(new Set())` — const, line 1004
- `const commitKeysRef = useRef<Record<string, string>>(` — const, line 1005
- `const commitInquiry = useCallback(async (root: ReaderExchange, preset: InquiryCommitment)` — const, line 1009
- `const slot = `$` — const, line 1011
- `const key = commitKeysRef.current[slot] ?? (commitKeysRef.current[slot] = newKey())` — const, line 1014
- `const spanIds = root.selectionSpanIds.length ? root.selectionSpanIds : [root.spanId]` — const, line 1015
- `const about = root.about ?? null` — const, line 1018
- `const receipt = await api.readerInvokePreset(` — const, line 1024
- `const openInquiry = useCallback((rootId: string, fallbackSpanId?: string | null)` — const, line 1056
- `const root = history.find((exchange)` — const, line 1057
- `const next = new Set(ids)` — const, line 1066
- `const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find( (element)` — const, line 1079
- `const settleInquiryJob = useCallback((rootId: string, batchId: string | null, waitId: string | null, status: "completed" | "failed" | "cancelled", extra:` — const, line 1092
- `const job = inquiryJobsRef.current[rootId]` — const, line 1095
- `const waited = Date.now() - job.startedAt` — const, line 1098
- `const recordUnqueuedCheck = useCallback((failureReason: string)` — const, line 1111
- `const jobId = newActivityId()` — const, line 1112
- `const startQuickCheck = useCallback(async (rootId: string, via: "inline" | "rail")` — const, line 1123
- `const waitId = newKey()` — const, line 1128
- `const visitIds = visitPayload()` — const, line 1129
- `const startedAt = Date.now()` — const, line 1130
- `const activity = learnerActivitySnapshot()` — const, line 1131
- `const result = await api.readerReconnectAnswer(` — const, line 1133
- `const batchId = result.batchId` — const, line 1138
- `const tracked = inquiryJobsRef.current[rootId]` — const, line 1139
- `const phase = phaseForError(error)` — const, line 1157
- `const cancelQuickCheck = useCallback((rootId: string)` — const, line 1165
- `const current = inquiryChecks[rootId]` — const, line 1166
- `const wait = current?.batchId ?` — const, line 1167
- `const batchId = wait?.batchId ?? null` — const, line 1170
- `const dismissInquiryCheck = useCallback((rootId: string)` — const, line 1180
- `const answerReconnect = useCallback(async (answer: "yes" | "still_unclear" | "quick_check", text = "")` — const, line 1187
- `const line = reconnect` — const, line 1188
- `const via = line.inline ? "inline" : "rail"` — const, line 1190
- `const result = await api.readerReconnectAnswer(` — const, line 1198
- `const root = history.find((item)` — const, line 1207
- `const paused = useWindowPaused()` — const, line 1221
- `const watching = Object.entries(inquiryChecks).filter( ([, check])` — const, line 1224
- `const timer = window.setInterval(()` — const, line 1228
- `const batchId = check.batchId as string` — const, line 1230
- `const waitId = check.waitId as string` — const, line 1231
- `const attempts = (check.attempts ?? 0) + 1` — const, line 1232
- `const same = (checks: typeof inquiryChecks)` — const, line 1235
- `const timedOut = ()` — const, line 1236
- `const job = result.job ?? null` — const, line 1242
- `const landedQuestion = result.question` — const, line 1244
- `const code = job.errorCode ?? "error"` — const, line 1255
- `const phase: ModelActionPhase = code === "capped" ? "capped" : code === "provider_unavailable" ? "unreachable" : "failed"` — const, line 1257
- `const failure = code === "spend_refused" ? spendRefusalLine(job.refusal) : null` — const, line 1258
- `const phase = phaseForError(error)` — const, line 1269
- `const pollErrors = (check.pollErrors ?? 0) + 1` — const, line 1277
- `const inquiryCheckAction = useCallback(async (rootId: string, action: "answered" | "self_checked" | "dismissed", value?: string)` — const, line 1288
- `const check = inquiryChecks[rootId]` — const, line 1289
- `const result = await api.readerInquiryQuestionAction(` — const, line 1292
- `const escalateInquiryCheck = useCallback(async (rootId: string)` — const, line 1304
- `const check = inquiryChecks[rootId]` — const, line 1305
- `const passageCheckOffered = useMemo(()` — const, line 1320
- `const root = history.find((exchange)` — const, line 1322
- `const normalizedAskFind = askFindQuery.trim().toLowerCase()` — const, line 1331
- `const visibleAskHistory = useMemo( ()` — const, line 1332
- `const onFind = (event: KeyboardEvent)` — const, line 1345

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `AskAnchor`, `useReaderInquiry`; references `AskAnchor`, `useReaderInquiry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InquiryResolution`, `InquirySelfCheck`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderGuideSectionDto`, `ReaderInquiryQuestionDto`, `ReaderRenderViewDto`, `ReaderRetrievalIntent`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export; imports `PassageAlign`
- [[Reference/Desktop/TypeScript/components/scrollWithin|src/components/scrollWithin.ts]] — import-or-re-export; imports `scrollIntoViewWithin`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useListenerHub`, `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `ModelActionPhase`, `phaseForError`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]] — import-or-re-export; imports `AskAbout`, `InquiryCommitment`, `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export; imports `TUTOR_COPY`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `activitySince`, `learnerActivitySnapshot`, `logReaderAction`, `logReaderActivity`, `newActivityId`, `noteLearnerActivity`
- [[Reference/Desktop/TypeScript/screens/reader/checkOffer|src/screens/reader/checkOffer.ts]] — import-or-re-export; imports `checkOffer`
- [[Reference/Desktop/TypeScript/screens/reader/readerCache|src/screens/reader/readerCache.ts]] — import-or-re-export; imports `cachedSourceRead`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `MarginAnnotation`, `ReaderSelection`, `clip`, `passageKeys`, `sectionWords`, `selectionNodes`
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
