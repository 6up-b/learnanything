---
title: "Desktop module · src/app/App.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.App"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/App.tsx"
source_paths:
  - "apps/learnloop-tauri/src/app/App.tsx"
source_commit: "01fa9698ae962d7b0977b90915e12e269c3b8db5"
source_commit_timestamp: "2026-11-03T12:40:09-05:00"
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

# `src/app/App.tsx`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Owns desktop navigation and cross-screen state, connecting startup, sessions, overlays, vault refresh, and route handoffs.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) |
| Source lines | 2575 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `01fa9698ae962d7b0977b90915e12e269c3b8db5` |
| Commit timestamp | `2026-11-03T12:40:09-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]]

## Public API

- `export function App()` — function, line 133

## Internal implementation anchors

- `type Place, type ShellMode, type UthToolId } from "./shell"` — type, line 49
- `type ShellMode, type UthToolId } from "./shell"` — type, line 50
- `type UthToolId } from "./shell"` — type, line 51
- `type PracticeOffer, type ProposalOrigin } from "./practiceOffer"` — type, line 89
- `type ProposalOrigin } from "./practiceOffer"` — type, line 90
- `type OpenSourceTarget =` — type, line 100
- `const ReaderScreen = lazy(()` — const, line 108
- `const LessonScreen = lazy(()` — const, line 109
- `const GraphScreen = lazy(()` — const, line 110
- `const IngestScreen = lazy(()` — const, line 111
- `const ExamScreen = lazy(()` — const, line 112
- `const ProposalsScreen = lazy(()` — const, line 113
- `const RegistryReviewScreen = lazy(()` — const, line 114
- `const GoldenPathScreen = lazy(()` — const, line 115
- `const KnowledgeMapView = lazy(()` — const, line 117
- `const LibraryScreen = lazy(()` — const, line 118
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview"` — type, line 120
- `type VaultFilesChangedEvent =` — type, line 122
- `const previousTabRef = useRef<TopTab>(tab)` — const, line 142
- `const readerSkimmingRef = useRef(false)` — const, line 145
- `const noteReaderSkimming = useCallback((muted: boolean)` — const, line 146
- `const previous = previousTabRef.current` — const, line 150
- `const landing = shellRef.current === "simple" && tab === "start" ? "today" : tab` — const, line 155
- `const armed = wrapUpOfferArmed(previous, landing) && !readerSkimmingRef.current` — const, line 156
- `const readerSourceRef = useRef<ReaderOpenSource | null>(null)` — const, line 166
- `const dailyPlanQuery = useDailyPlan(session?.sessionId ?? null, Boolean(session))` — const, line 193
- `const planServing = dailyPlanQuery.data?.enabled === true && dailyPlanQuery.data.plan !== null` — const, line 194
- `const onPracticeDraft = useCallback((draft: PracticeDraftMirror)` — const, line 273
- `const sessionMoved = useSessionMoved()` — const, line 276
- `const startupStartedRef = useRef(false)` — const, line 308
- `const teachBackActiveRef = useRef(false)` — const, line 312
- `const practiceAskAllowedRef = useRef(false)` — const, line 316
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 317
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 320
- `const practiceAskStateRef = useRef<(()` — const, line 326
- `const onPracticeAskState = useCallback( (reader: (()` — const, line 327
- `const practiceAskOpenRef = useRef<(()` — const, line 335
- `const onPracticeAskOpener = useCallback((open: (()` — const, line 336
- `const shell: ShellMode = snapshot ? algoConfig().shell : "classic"` — const, line 346
- `const shellRef = useRef<ShellMode>(shell)` — const, line 358
- `const simple = shell === "simple"` — const, line 360
- `const sessionRef = useRef<SessionSnapshot | null>(session)` — const, line 365
- `const implicitStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 367
- `const pendingStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 371
- `const vaultGenRef = useRef(0)` — const, line 376
- `const vaultChangesRef = useRef(0)` — const, line 381
- `const pushNotice = useCallback((input: NoticeInput)` — const, line 383
- `const onError = useCallback( (message: string, report?: ErrorReport)` — const, line 388
- `const command = report?.error === undefined ? null : getCommandError(report.error)` — const, line 394
- `const code = command?.code ?? null` — const, line 395
- `const notify = useCallback( (message: string)` — const, line 408
- `const reportError = useCallback( (error: unknown, fallback: string, action?:` — const, line 417
- `const message = errorMessage(error, fallback)` — const, line 419
- `const command = getCommandError(error)` — const, line 424
- `const code = command?.code ?? null` — const, line 425
- `const needSession = useCallback( (need: keyof typeof NEEDS_SESSION)` — const, line 432
- `const settingsNotice: ShellNotice | null = simple ? notices[notices.length - 1] ?? null : null` — const, line 443
- `const settingsNoticeId = settingsNotice?.id ?? null` — const, line 444
- `const dismissSettingsNotice = useCallback(()` — const, line 445
- `const onPaletteEntities = useCallback((ids:` — const, line 452
- `const refreshAiConnection = useCallback(()` — const, line 457
- `const landOnLibraryIfEmpty = useCallback(async (appSnapshot: AppSnapshot)` — const, line 463
- `const library = await api.getSourceLibrary()` — const, line 466
- `const restoreLastPlace = useCallback(async (appSnapshot: AppSnapshot)` — const, line 477
- `const place = rememberedPlace()` — const, line 478
- `const tool = rememberedTool()` — const, line 480
- `const root = appSnapshot.vault?.root` — const, line 492
- `const sourceId = root ? rememberedBook(root) : null` — const, line 493
- `const card = (await api.getSourceLibrary()).sources.find((entry)` — const, line 496
- `const loadInitialVault = useCallback(async ()` — const, line 509
- `const appSnapshot = await api.loadVault()` — const, line 512
- `const checkpoint = appSnapshot.activeSession?.checkpoint` — const, line 516
- `let disposed = false` — let, line 541
- `let unlisten: (()` — let, line 542
- `let invalidateTimer: number | null = null` — let, line 547
- `const scheduleInvalidateAll = ()` — const, line 548
- `const next = payload.refresh.snapshot` — const, line 565
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 575
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 610
- `let disposed = false` — let, line 633
- `const refresh = ()` — const, line 634
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 645
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 652
- `const hasSnapshot = snapshot !== null` — const, line 665
- `const place = placeOfTab(tab)` — const, line 668
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 671
- `const rememberedBookRef = useRef<string | null>(null)` — const, line 679
- `const root = snapshot?.vault?.root` — const, line 695
- `const runKeyActionRef = useRef<(action: KeyAction)` — const, line 701
- `const onKey = (event: KeyboardEvent)` — const, line 710
- `const binding = matchShellKey(event, shellRef.current, isTypingTarget(event.target))` — const, line 711
- `const restored = useMemo( ()` — const, line 720
- `const subjectOptions = useMemo(()` — const, line 726
- `const titles = new Map((snapshot?.vault?.subjectTitles ?? []).map((entry)` — const, line 727
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 730
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 733
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 734
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 739
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 746
- `const applyGradingProvider = useCallback( async (provider: string)` — const, line 752
- `const result = await api.setGradingProvider(provider)` — const, line 754
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 776
- `function beginSession(next: SessionSnapshot, firstStep?: PlanStepDto | null)` — function, line 790
- `const action = planStepAction(firstStep,` — const, line 813
- `function implicitSession(): Promise<SessionSnapshot | null>` — function, line 865
- `const generation = vaultGenRef.current` — const, line 869
- `const current = ()` — const, line 870
- `let started: Promise<SessionSnapshot | null> | null = null` — let, line 871
- `const minutes = await implicitSessionMinutes()` — const, line 874
- `const next = await startSessionHere(minutes)` — const, line 883
- `function startSessionHere(minutes: number): Promise<SessionSnapshot | null>` — function, line 904
- `const generation = vaultGenRef.current` — const, line 910
- `let request: Promise<SessionSnapshot | null>` — let, line 911
- `const pending: Promise<SessionSnapshot | null> = request .then((next)` — const, line 918
- `function withImplicitSession(action: (started: SessionSnapshot, stillOpen: ()` — function, line 936
- `const generation = vaultGenRef.current` — const, line 938
- `const stillOpen = ()` — const, line 939
- `function showPractice(id: string)` — function, line 945
- `function openPractice( id: string, schedulerCandidateId?: string | null, proposalOrigin?: ProposalOrigin | null, planPresentationId?: string | null )` — function, line 954
- `async function pickCheckMe( request: ReaderCheckMeRequest, sessionId: string, // UX Phase 3 fix round 1 (F1): after an implicit start, whether the vault // it started in is still the open one (checked after each request). options:` — function, line 992
- `const stillOpen = options.stillOpen ?? (()` — const, line 999
- `const result = await api.planLearnerPick( request.practiceItemId, sessionId, null, request.proposalId ?? null, request.importId ?? null )` — const, line 1001
- `const offer = readerCheckOffer(result, request.practiceItemId, request.proposalId ?? null, request.importId ?? null)` — const, line 1005
- `const served = await api.getPracticeItem(request.practiceItemId, sessionId, offer.proposalOrigin ?? null)` — const, line 1007
- `const onReaderWorkbenchSubmitted: NonNullable<ReaderWorkbenchProps["onSubmitted"]> = (result, at)` — const, line 1048
- `const readerWorkbench: ReaderWorkbenchProps | undefined = algoConfig().workbench ?` — const, line 1060
- `function openReaderExercise(request: ReaderExerciseRequest, options:` — function, line 1084
- `function exerciseFromReader(request: ReaderExerciseRequest)` — function, line 1093
- `function checkMeFromReader(request: ReaderCheckMeRequest)` — function, line 1107
- `function backFromPractice(options:` — function, line 1123
- `const target = readerTargetBack(readerReturn,` — const, line 1125
- `async function openPlanReadingNow(reading: PlanReadingDto, estMinutes: number | null)` — function, line 1140
- `const library = await api.getSourceLibrary()` — const, line 1141
- `const target = readerTargetForReading(reading, library.sources)` — const, line 1142
- `async function openPlanReading(reading: PlanReadingDto, estMinutes: number | null = null)` — function, line 1151
- `async function openPassageNow(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1167
- `const generation = vaultGenRef.current` — const, line 1168
- `const library = await api.getSourceLibrary()` — const, line 1169
- `const card = library.sources.find((entry)` — const, line 1171
- `async function openPassage(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1181
- `function resumeProblem(problem: WorkbenchOpenProblemDto)` — function, line 1191
- `async function openStudiedNow(restoration: IntentRestorationDto)` — function, line 1200
- `const library = await api.getSourceLibrary()` — const, line 1201
- `const target = readerTargetForRestoration(restoration, library.sources)` — const, line 1202
- `async function openStudied(restoration: IntentRestorationDto)` — function, line 1210
- `function routePlanStep(step: PlanStepDto | null)` — function, line 1224
- `const action = planStepAction(step)` — const, line 1225
- `function openPrimedRetry(id: string)` — function, line 1237
- `function showPrimed(id: string)` — function, line 1251
- `function openGuidedRedo(redo: GuidedRedoDto)` — function, line 1262
- `function showGuidedRedo(redo: GuidedRedoDto)` — function, line 1278
- `function openFeedback(id: string)` — function, line 1287
- `function teachMeFromReader(request:` — function, line 1302
- `async function startQuickCheck(learningObjectIds: string[])` — function, line 1307
- `const generation = vaultGenRef.current` — const, line 1310
- `const implicit = !session && shellRef.current === "simple"` — const, line 1311
- `const stillOpen = ()` — const, line 1312
- `let current = session` — let, line 1313
- `const requestId = globalThis.crypto?.randomUUID?.() ?? `$` — const, line 1322
- `const progress = await api.startQuickCheck(` — const, line 1323
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 1332
- `function openLibraryShelf()` — function, line 1340
- `function openLibraryFile(path: string)` — function, line 1346
- `function installHandedSession(next: SessionSnapshot)` — function, line 1355
- `const item = next.checkpoint?.currentPracticeItemId ?? null` — const, line 1360
- `async function adoptSessionBack(from: SessionMoved)` — function, line 1366
- `async function startFreshOverMoved(from: SessionMoved)` — function, line 1375
- `const minutes = session?.availableMinutes ?? (await implicitSessionMinutes())` — const, line 1377
- `const next = await startSessionOrAsk(` — const, line 1379
- `function letGoOfEndedSession()` — function, line 1398
- `function clearLocalCheckpoint(identity?:` — function, line 1410
- `const checkpoint = current.checkpoint` — const, line 1414
- `function endSession(summary: SessionEndSummary)` — function, line 1433
- `function gotoTab(next: TopTab)` — function, line 1452
- `function gotoPlace(place: Place)` — function, line 1473
- `function selectUthTool(tool: UthToolId, options:` — function, line 1479
- `function openUnderTheHood()` — function, line 1487
- `async function openAnotherLibrary()` — function, line 1491
- `const selected = await openDialog(` — const, line 1493
- `function openRepair(misconceptionId: string)` — function, line 1502
- `function openExam(goalId: string)` — function, line 1507
- `function exitExam()` — function, line 1512
- `function openCalibration(id: string, options?:` — function, line 1519
- `function exitCalibration()` — function, line 1527
- `const askCurrentContext = useCallback((): boolean` — const, line 1537
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 1572
- `const openBook = useCallback((card: SourceLibraryCard)` — const, line 1584
- `const openAddedItem = useCallback( async (item: AddSourceItemDto)` — const, line 1592
- `let card: SourceLibraryCard | undefined` — let, line 1602
- `const adder = useAddSource(` — const, line 1631
- `const addSources = adder.add` — const, line 1632
- `const fileDragging = useSourceFileDrop(` — const, line 1633
- `function gotoProposalBatch(patchId: string)` — function, line 1650
- `function resetShellForVault()` — function, line 1656
- `const changeVault = useCallback( async (path: string)` — const, line 1696
- `let selected = false` — let, line 1698
- `let selectionAttempted = false` — let, line 1699
- `const next = await api.loadVault()` — const, line 1735
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 1743
- `const libraryFilesProps =` — const, line 1766
- `function libraryPlace(booksOnly = false)` — function, line 1779
- `const gradingTrouble = simple && snapshot !== null && !manualGrading && aiConnection !== null && aiConnection.needs !== "connect" && !(snapshot.health.ai?.ready ?? snapshot.health.codex.ready ?? false)` — const, line 1804
- `const readerHolding = simple && tab === "reader" && readerSource !== null && !examGoalId && !calibrationSessionId && !(goldenRunId && SHOW_GOLDEN_PATH)` — const, line 1813
- `function paletteCommands(): PaletteCommand[]` — function, line 1817
- `const current = uthTool(uthToolOfTab(tab, uthToolState))` — const, line 1818
- `const practicing = tab === "today" && todayStage === "practice"` — const, line 1854
- `function wrapUpLine(landing: WrapUpLanding)` — function, line 1881
- `function renderBody()` — function, line 1886
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 1926
- `const todayPlace = ()` — const, line 1950
- `const start = ( <StartScreen onBegin=` — const, line 1973
- `const fromReader = simplePracticeFeedback() && returnsToReader(readerReturn, practiceItemId)` — const, line 2068
- `const planNext = Boolean(session && !calibrationSessionId && planServing)` — const, line 2069
- `const feedbackDock = algoConfig().ask !== null && askTarget?.context === "feedback" ? askTarget : null` — const, line 2072
- `const today = ( <TodayScreen key=` — const, line 2111
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 2152
- `function renderIngest()` — function, line 2177
- `function renderProposals()` — function, line 2194
- `function renderRegistry()` — function, line 2210
- `function renderGolden()` — function, line 2225
- `function renderMaintain()` — function, line 2248
- `function renderUthTool(tool: UthToolId)` — function, line 2260
- `function renderAfterGolden()` — function, line 2291
- `const shellTree = ( <> <TerminalFrame active=` — const, line 2320
- `function unique(values: Array<string | null>): string[]` — function, line 2573

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/main|src/main.tsx]] — import-or-re-export: `App`; references `App`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AddSourceItemDto`, `AiConnectionDto`, `AppSnapshot`, `AttemptProgress`, `CommandError`, `GuidedRedoDto`, `IntentRestorationDto`, `PlanReadingDto`, `PlanStepDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `SourceLibraryCard`, `TriageResultDto`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `clearQueryCache`, `invalidateAllQueries`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/app/ShellChromeRoot|src/app/ShellChromeRoot.tsx]] — import-or-re-export; imports `ShellChromeRoot`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `setAlgoConfig`, `setRenderedShell`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `planStepAction`, `readerTargetForReading`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/app/intentCheck|src/app/intentCheck.ts]] — import-or-re-export; imports `readerTargetForRestoration`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `KeyAction`, `matchShellKey`
- [[Reference/Desktop/TypeScript/app/notices|src/app/notices.ts]] — import-or-re-export; imports `NEEDS_SESSION`, `NoticeInput`, `ShellNotice`, `addNotice`, `dismissNotice`, `noticeAfterSessionBegins`, `resolveNotices`, `sessionNotice`
- [[Reference/Desktop/TypeScript/app/practiceDraft|src/app/practiceDraft.ts]] — import-or-re-export; imports `PracticeDraftMirror`, `restoredPracticeDraft`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `feedbackOrigin`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/app/practiceOffer|src/app/practiceOffer.ts]] — import-or-re-export; imports `PracticeOffer`, `ProposalOrigin`, `planPresentationForServe`, `proposalOriginForServe`, `schedulerCandidateForServe`
- [[Reference/Desktop/TypeScript/app/readerCheck|src/app/readerCheck.ts]] — import-or-re-export; imports `ReaderReturn`, `keepReaderReturn`, `readerCheckOffer`, `returnsToReader`
- [[Reference/Desktop/TypeScript/app/readerWorkbench|src/app/readerWorkbench.ts]] — import-or-re-export; imports `consumeShown`, `readerTargetBack`, `readerWorkbenchCheck`, `sessionAfterWorkbenchSubmit`, `workbenchReturn`
- [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]] — import-or-re-export; imports `recordRecentVault`, `removeRecentVault`
- [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]] — import-or-re-export; imports `adoptMovedSession`, `startSessionOrAsk`
- [[Reference/Desktop/TypeScript/app/sessionMoved|src/app/sessionMoved.ts]] — import-or-re-export; imports `SessionMoved`, `setSessionMoved`, `useSessionMoved`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `Place`, `ShellMode`, `UthToolId`, `isTabTool`, `placeOfTab`, `rememberBook`, `rememberPlace`, `rememberTool`, `rememberedBook`, `rememberedPlace`, `rememberedTool`, `tabForPlace`, `uthTool`, `uthToolOfTab`, `visibleUthTools`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `implicitSessionMinutes`
- [[Reference/Desktop/TypeScript/app/useGlobalAdd|src/app/useGlobalAdd.ts]] — import-or-re-export; imports `useGlobalAdd`
- [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|src/app/useQueueRevisionPoll.ts]] — import-or-re-export; imports `revisionPollHeld`, `useQueueRevisionPoll`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `selectWithDraftFlush`
- [[Reference/Desktop/TypeScript/app/wrapUpOffer|src/app/wrapUpOffer.ts]] — import-or-re-export; imports `WrapUpLanding`, `wrapUpOfferArmed`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export; imports `AddPopover`, `DropOverlay`, `useAddSource`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export; imports `AdjudicationOverlay`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export; imports `CommandPalette`, `PaletteCommand`
- [[Reference/Desktop/TypeScript/components/ConnectAI|src/components/ConnectAI.tsx]] — import-or-re-export; imports `ConnectAISheet`
- [[Reference/Desktop/TypeScript/components/DockedAsk|src/components/DockedAsk.tsx]] — import-or-re-export; imports `DockedAsk`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export; imports `ExemplarConfirmDialog`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export; imports `InspectorOverlay`
- [[Reference/Desktop/TypeScript/components/KeyboardHelp|src/components/KeyboardHelp.tsx]] — import-or-re-export; imports `KeyboardHelp`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export; imports `NewVaultWizard`
- [[Reference/Desktop/TypeScript/components/NoticeHost|src/components/NoticeHost.tsx]] — import-or-re-export; imports `NoticeHost`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/PlanFallbackOffer|src/components/PlanFallbackOffer.tsx]] — import-or-re-export; imports `PlanFallbackOffer`
- [[Reference/Desktop/TypeScript/components/PlanReadingBanner|src/components/PlanReadingBanner.tsx]] — import-or-re-export; imports `PlanReadingBanner`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export; imports `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/SessionElsewherePrompt|src/components/SessionElsewherePrompt.tsx]] — import-or-re-export; imports `SessionElsewherePrompt`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export; imports `SessionFinishHud`
- [[Reference/Desktop/TypeScript/components/SessionMovedBanner|src/components/SessionMovedBanner.tsx]] — import-or-re-export; imports `SessionMovedBanner`
- [[Reference/Desktop/TypeScript/components/WhyDiagnosisOverlay|src/components/WhyDiagnosisOverlay.tsx]] — import-or-re-export; imports `WhyDiagnosisOverlay`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export; imports `GoldenPathSetup`
- [[Reference/Desktop/TypeScript/components/pdfDocumentCache|src/components/pdfDocumentCache.ts]] — import-or-re-export; imports `clearPdfDocuments`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `NavBadgeCounts`, `SHOW_GOLDEN_PATH`, `TerminalFrame`, `TopTab`
- [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]] — import-or-re-export; imports `pickSourceFiles`, `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ErrorReport`, `NoticeRetry`, `RETRY_RAN`, `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export; imports `CalibrationScreen`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export; imports `DiagnosticReviewScreen`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export; imports `FeedbackScreen`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — dynamic import; imports `LessonEntry`
- [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] — import-or-re-export; imports `LibraryPlace`, `LibraryView`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export; imports `MaintenanceScreen`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export; imports `PracticeScreen`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — dynamic import; imports `ReaderCheckMeRequest`, `ReaderExerciseRequest`, `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export; imports `RepairScreen`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export; imports `ReviewScreen`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export; imports `SettingsOverlay`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export; imports `StartScreen`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export; imports `TodayScreen`
- [[Reference/Desktop/TypeScript/screens/UnderTheHoodScreen|src/screens/UnderTheHoodScreen.tsx]] — import-or-re-export; imports `UnderTheHoodScreen`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|src/screens/reader/WrapUpOffer.tsx]] — import-or-re-export; imports `WrapUpOffer`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export; imports `ReaderWorkbenchCheck`, `ReaderWorkbenchProps`, `ReaderWorkbenchResume`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export; imports `TodayPlace`
- [[Reference/Desktop/TypeScript/screens/underhood/tools|src/screens/underhood/tools.tsx]] — import-or-re-export; imports `CalibrationTool`, `DataTool`, `InspectorTool`, `MistakesTool`, `SpendTool`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/event`, `@tauri-apps/plugin-dialog`, `react`, `react-dom`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Architecture Overview#Runtime composition|runtime composition]] — shows this entry point in the whole process graph.
- [[Workflows/Initialize a Vault|Initialize a Vault]] — owns first-run behavior.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/app/App.wrapUpSkim.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.wrapUpSkim.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.today.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.today.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.shell.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.shell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.queueRevision.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.queueRevision.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.lessonSuggestion.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.lessonSuggestion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound5.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound5.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound4.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound3.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound3.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
