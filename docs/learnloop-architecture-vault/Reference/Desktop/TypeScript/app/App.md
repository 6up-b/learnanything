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
source_commit: "05e1f7dbe01e8455c04a69866b2a90172bd575df"
source_commit_timestamp: "2026-11-09T08:41:56-05:00"
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
| Source lines | 2679 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `05e1f7dbe01e8455c04a69866b2a90172bd575df` |
| Commit timestamp | `2026-11-09T08:41:56-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]]

## Public API

- `export function App()` — function, line 136

## Internal implementation anchors

- `type Place, type ShellMode, type UthToolId } from "./shell"` — type, line 50
- `type ShellMode, type UthToolId } from "./shell"` — type, line 51
- `type UthToolId } from "./shell"` — type, line 52
- `type PracticeOffer, type ProposalOrigin } from "./practiceOffer"` — type, line 92
- `type ProposalOrigin } from "./practiceOffer"` — type, line 93
- `type OpenSourceTarget =` — type, line 103
- `const ReaderScreen = lazy(()` — const, line 111
- `const LessonScreen = lazy(()` — const, line 112
- `const GraphScreen = lazy(()` — const, line 113
- `const IngestScreen = lazy(()` — const, line 114
- `const ExamScreen = lazy(()` — const, line 115
- `const ProposalsScreen = lazy(()` — const, line 116
- `const RegistryReviewScreen = lazy(()` — const, line 117
- `const GoldenPathScreen = lazy(()` — const, line 118
- `const KnowledgeMapView = lazy(()` — const, line 120
- `const LibraryScreen = lazy(()` — const, line 121
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview" | "offer"` — type, line 123
- `type VaultFilesChangedEvent =` — type, line 125
- `const previousTabRef = useRef<TopTab>(tab)` — const, line 145
- `const readerSkimmingRef = useRef(false)` — const, line 148
- `const noteReaderSkimming = useCallback((muted: boolean)` — const, line 149
- `const previous = previousTabRef.current` — const, line 153
- `const landing = shellRef.current === "simple" && tab === "start" ? "today" : tab` — const, line 158
- `const armed = wrapUpOfferArmed(previous, landing) && !readerSkimmingRef.current` — const, line 159
- `const readerSourceRef = useRef<ReaderOpenSource | null>(null)` — const, line 169
- `const dailyPlanQuery = useDailyPlan(session?.sessionId ?? null, Boolean(session))` — const, line 201
- `const planServing = dailyPlanQuery.data?.enabled === true && dailyPlanQuery.data.plan !== null` — const, line 202
- `const planAtOffer = useRef<` — const, line 205
- `const read = dailyPlanQuery.data` — const, line 211
- `const onPracticeDraft = useCallback((draft: PracticeDraftMirror)` — const, line 300
- `const sessionMoved = useSessionMoved()` — const, line 303
- `const startupStartedRef = useRef(false)` — const, line 335
- `const teachBackActiveRef = useRef(false)` — const, line 339
- `const practiceAskAllowedRef = useRef(false)` — const, line 343
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 344
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 347
- `const practiceAskStateRef = useRef<(()` — const, line 353
- `const onPracticeAskState = useCallback( (reader: (()` — const, line 354
- `const practiceAskOpenRef = useRef<(()` — const, line 362
- `const onPracticeAskOpener = useCallback((open: (()` — const, line 363
- `const shell: ShellMode = snapshot ? algoConfig().shell : "classic"` — const, line 373
- `const shellRef = useRef<ShellMode>(shell)` — const, line 385
- `const simple = shell === "simple"` — const, line 387
- `const sessionRef = useRef<SessionSnapshot | null>(session)` — const, line 392
- `const implicitStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 394
- `const pendingStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 398
- `const vaultGenRef = useRef(0)` — const, line 403
- `const vaultChangesRef = useRef(0)` — const, line 408
- `const pushNotice = useCallback((input: NoticeInput)` — const, line 410
- `const onError = useCallback( (message: string, report?: ErrorReport)` — const, line 415
- `const command = report?.error === undefined ? null : getCommandError(report.error)` — const, line 421
- `const code = command?.code ?? null` — const, line 422
- `const notify = useCallback( (message: string)` — const, line 435
- `const reportError = useCallback( (error: unknown, fallback: string, action?:` — const, line 444
- `const message = errorMessage(error, fallback)` — const, line 446
- `const command = getCommandError(error)` — const, line 451
- `const code = command?.code ?? null` — const, line 452
- `const needSession = useCallback( (need: keyof typeof NEEDS_SESSION)` — const, line 459
- `const settingsNotice: ShellNotice | null = simple ? notices[notices.length - 1] ?? null : null` — const, line 470
- `const settingsNoticeId = settingsNotice?.id ?? null` — const, line 471
- `const dismissSettingsNotice = useCallback(()` — const, line 472
- `const onPaletteEntities = useCallback((ids:` — const, line 479
- `const refreshAiConnection = useCallback(()` — const, line 484
- `const landOnLibraryIfEmpty = useCallback(async (appSnapshot: AppSnapshot)` — const, line 490
- `const library = await api.getSourceLibrary()` — const, line 493
- `const restoreLastPlace = useCallback(async (appSnapshot: AppSnapshot)` — const, line 504
- `const place = rememberedPlace()` — const, line 505
- `const tool = rememberedTool()` — const, line 507
- `const root = appSnapshot.vault?.root` — const, line 519
- `const sourceId = root ? rememberedBook(root) : null` — const, line 520
- `const card = (await api.getSourceLibrary()).sources.find((entry)` — const, line 523
- `const loadInitialVault = useCallback(async ()` — const, line 536
- `const appSnapshot = await api.loadVault()` — const, line 539
- `const checkpoint = appSnapshot.activeSession?.checkpoint` — const, line 543
- `let disposed = false` — let, line 568
- `let unlisten: (()` — let, line 569
- `let invalidateTimer: number | null = null` — let, line 574
- `const scheduleInvalidateAll = ()` — const, line 575
- `const next = payload.refresh.snapshot` — const, line 592
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 602
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 637
- `let disposed = false` — let, line 660
- `const refresh = ()` — const, line 661
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 672
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 679
- `const hasSnapshot = snapshot !== null` — const, line 692
- `const place = placeOfTab(tab)` — const, line 695
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 698
- `const rememberedBookRef = useRef<string | null>(null)` — const, line 706
- `const root = snapshot?.vault?.root` — const, line 722
- `const runKeyActionRef = useRef<(action: KeyAction)` — const, line 728
- `const onKey = (event: KeyboardEvent)` — const, line 737
- `const binding = matchShellKey(event, shellRef.current, isTypingTarget(event.target))` — const, line 738
- `const restored = useMemo( ()` — const, line 747
- `const subjectOptions = useMemo(()` — const, line 753
- `const titles = new Map((snapshot?.vault?.subjectTitles ?? []).map((entry)` — const, line 754
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 757
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 760
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 761
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 766
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 773
- `const applyGradingProvider = useCallback( async (provider: string)` — const, line 779
- `const result = await api.setGradingProvider(provider)` — const, line 781
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 803
- `function beginSession(next: SessionSnapshot, firstStep?: PlanStepDto | null)` — function, line 817
- `const action = planStepAction(firstStep,` — const, line 840
- `function implicitSession(): Promise<SessionSnapshot | null>` — function, line 892
- `const generation = vaultGenRef.current` — const, line 896
- `const current = ()` — const, line 897
- `let started: Promise<SessionSnapshot | null> | null = null` — let, line 898
- `const minutes = await implicitSessionMinutes()` — const, line 901
- `const next = await startSessionHere(minutes)` — const, line 910
- `function startSessionHere(minutes: number): Promise<SessionSnapshot | null>` — function, line 931
- `const generation = vaultGenRef.current` — const, line 937
- `let request: Promise<SessionSnapshot | null>` — let, line 938
- `const pending: Promise<SessionSnapshot | null> = request .then((next)` — const, line 945
- `function withImplicitSession(action: (started: SessionSnapshot, stillOpen: ()` — function, line 963
- `const generation = vaultGenRef.current` — const, line 965
- `const stillOpen = ()` — const, line 966
- `function showPractice(id: string)` — function, line 972
- `function openPractice( id: string, schedulerCandidateId?: string | null, proposalOrigin?: ProposalOrigin | null, planPresentationId?: string | null )` — function, line 981
- `async function pickCheckMe( request: ReaderCheckMeRequest, sessionId: string, // UX Phase 3 fix round 1 (F1): after an implicit start, whether the vault // it started in is still the open one (checked after each request). options:` — function, line 1019
- `const stillOpen = options.stillOpen ?? (()` — const, line 1026
- `const result = await api.planLearnerPick( request.practiceItemId, sessionId, null, request.proposalId ?? null, request.importId ?? null )` — const, line 1028
- `const offer = readerCheckOffer(result, request.practiceItemId, request.proposalId ?? null, request.importId ?? null)` — const, line 1032
- `const served = await api.getPracticeItem(request.practiceItemId, sessionId, offer.proposalOrigin ?? null)` — const, line 1034
- `const onReaderWorkbenchSubmitted: NonNullable<ReaderWorkbenchProps["onSubmitted"]> = (result, at)` — const, line 1075
- `const readerWorkbench: ReaderWorkbenchProps | undefined = algoConfig().workbench ?` — const, line 1087
- `function openReaderExercise(request: ReaderExerciseRequest, options:` — function, line 1111
- `function exerciseFromReader(request: ReaderExerciseRequest)` — function, line 1120
- `function checkMeFromReader(request: ReaderCheckMeRequest)` — function, line 1134
- `function backFromPractice(options:` — function, line 1150
- `const target = readerTargetBack(readerReturn,` — const, line 1152
- `async function openPlanReadingNow(reading: PlanReadingDto, estMinutes: number | null)` — function, line 1167
- `const library = await api.getSourceLibrary()` — const, line 1168
- `const target = readerTargetForReading(reading, library.sources)` — const, line 1169
- `async function openPlanReading(reading: PlanReadingDto, estMinutes: number | null = null)` — function, line 1179
- `async function openPassageNow(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1195
- `const generation = vaultGenRef.current` — const, line 1196
- `const library = await api.getSourceLibrary()` — const, line 1197
- `const card = library.sources.find((entry)` — const, line 1199
- `async function openPassage(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1209
- `function resumeProblem(problem: WorkbenchOpenProblemDto)` — function, line 1219
- `async function openStudiedNow(restoration: IntentRestorationDto)` — function, line 1228
- `const library = await api.getSourceLibrary()` — const, line 1229
- `const target = readerTargetForRestoration(restoration, library.sources)` — const, line 1230
- `async function openStudied(restoration: IntentRestorationDto)` — function, line 1238
- `function routePlanStep(step: PlanStepDto | null)` — function, line 1252
- `const action = planStepAction(step)` — const, line 1259
- `function answerPlanOffer(response: "accepted" | "chose_alternative" | "declined")` — function, line 1274
- `const sessionId = session?.sessionId ?? null` — const, line 1275
- `function closeOfferPage()` — function, line 1292
- `function answerSomethingElseOnOffer(result: SomethingElseChosenDto)` — function, line 1299
- `const entry = lessonEntryFor(result)` — const, line 1302
- `function openPrimedRetry(id: string)` — function, line 1310
- `function showPrimed(id: string)` — function, line 1324
- `function openGuidedRedo(redo: GuidedRedoDto)` — function, line 1335
- `function showGuidedRedo(redo: GuidedRedoDto)` — function, line 1351
- `function openFeedback(id: string)` — function, line 1360
- `function teachMeFromReader(request:` — function, line 1375
- `async function startQuickCheck(learningObjectIds: string[])` — function, line 1380
- `const generation = vaultGenRef.current` — const, line 1383
- `const implicit = !session && shellRef.current === "simple"` — const, line 1384
- `const stillOpen = ()` — const, line 1385
- `let current = session` — let, line 1386
- `const requestId = globalThis.crypto?.randomUUID?.() ?? `$` — const, line 1395
- `const progress = await api.startQuickCheck(` — const, line 1396
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 1405
- `function openLibraryShelf()` — function, line 1413
- `function lookInLibrary(phrase: string)` — function, line 1420
- `const seq = readerOpenSeq + 1` — const, line 1421
- `function openLibraryFile(path: string)` — function, line 1430
- `function installHandedSession(next: SessionSnapshot)` — function, line 1439
- `const item = next.checkpoint?.currentPracticeItemId ?? null` — const, line 1444
- `async function adoptSessionBack(from: SessionMoved)` — function, line 1450
- `async function startFreshOverMoved(from: SessionMoved)` — function, line 1459
- `const minutes = session?.availableMinutes ?? (await implicitSessionMinutes())` — const, line 1461
- `const next = await startSessionOrAsk(` — const, line 1463
- `function letGoOfEndedSession()` — function, line 1482
- `function clearLocalCheckpoint(identity?:` — function, line 1494
- `const checkpoint = current.checkpoint` — const, line 1498
- `function endSession(summary: SessionEndSummary)` — function, line 1517
- `function gotoTab(next: TopTab)` — function, line 1536
- `function gotoPlace(place: Place)` — function, line 1557
- `function selectUthTool(tool: UthToolId, options:` — function, line 1563
- `function openUnderTheHood()` — function, line 1571
- `async function openAnotherLibrary()` — function, line 1575
- `const selected = await openDialog(` — const, line 1577
- `function openRepair(misconceptionId: string)` — function, line 1586
- `function openExam(goalId: string)` — function, line 1591
- `function exitExam()` — function, line 1596
- `function openCalibration(id: string, options?:` — function, line 1603
- `function exitCalibration()` — function, line 1611
- `const askCurrentContext = useCallback((): boolean` — const, line 1621
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 1656
- `const openBook = useCallback((card: SourceLibraryCard)` — const, line 1668
- `const openAddedItem = useCallback( async (item: AddSourceItemDto)` — const, line 1676
- `let card: SourceLibraryCard | undefined` — let, line 1686
- `const adder = useAddSource(` — const, line 1715
- `const addSources = adder.add` — const, line 1716
- `const fileDragging = useSourceFileDrop(` — const, line 1717
- `function gotoProposalBatch(patchId: string)` — function, line 1734
- `function resetShellForVault()` — function, line 1740
- `const changeVault = useCallback( async (path: string)` — const, line 1780
- `let selected = false` — let, line 1782
- `let selectionAttempted = false` — let, line 1783
- `const next = await api.loadVault()` — const, line 1819
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 1827
- `const libraryFilesProps =` — const, line 1850
- `function libraryPlace(booksOnly = false)` — function, line 1863
- `const gradingTrouble = simple && snapshot !== null && !manualGrading && aiConnection !== null && aiConnection.needs !== "connect" && !(snapshot.health.ai?.ready ?? snapshot.health.codex.ready ?? false)` — const, line 1888
- `const readerHolding = simple && tab === "reader" && readerSource !== null && !examGoalId && !calibrationSessionId && !(goldenRunId && SHOW_GOLDEN_PATH)` — const, line 1897
- `function paletteCommands(): PaletteCommand[]` — function, line 1901
- `const current = uthTool(uthToolOfTab(tab, uthToolState))` — const, line 1902
- `const practicing = tab === "today" && todayStage === "practice"` — const, line 1938
- `function wrapUpLine(landing: WrapUpLanding)` — function, line 1965
- `function renderBody()` — function, line 1970
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 2010
- `const todayPlace = ()` — const, line 2034
- `const start = ( <StartScreen onBegin=` — const, line 2057
- `const fromReader = simplePracticeFeedback() && returnsToReader(readerReturn, practiceItemId)` — const, line 2169
- `const planNext = Boolean(session && !calibrationSessionId && planServing)` — const, line 2170
- `const feedbackDock = algoConfig().ask !== null && askTarget?.context === "feedback" ? askTarget : null` — const, line 2173
- `const today = ( <TodayScreen key=` — const, line 2214
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 2255
- `function renderIngest()` — function, line 2280
- `function renderProposals()` — function, line 2297
- `function renderRegistry()` — function, line 2313
- `function renderGolden()` — function, line 2328
- `function renderMaintain()` — function, line 2351
- `function renderUthTool(tool: UthToolId)` — function, line 2363
- `function renderAfterGolden()` — function, line 2394
- `const shellTree = ( <> <TerminalFrame active=` — const, line 2423
- `function unique(values: Array<string | null>): string[]` — function, line 2677

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/main|src/main.tsx]] — import-or-re-export: `App`; references `App`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AddSourceItemDto`, `AiConnectionDto`, `AppSnapshot`, `AttemptProgress`, `CommandError`, `DailyPlanDto`, `GuidedRedoDto`, `IntentRestorationDto`, `PlanLessonOfferStepDto`, `PlanReadingDto`, `PlanStepDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `SomethingElseChosenDto`, `SourceLibraryCard`, `TriageResultDto`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `clearQueryCache`, `invalidateAllQueries`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/app/ShellChromeRoot|src/app/ShellChromeRoot.tsx]] — import-or-re-export; imports `ShellChromeRoot`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `setAlgoConfig`, `setRenderedShell`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `planStepAction`, `readerTargetForReading`, `servedForExplicitStep`, `useDailyPlan`
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
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `setNextReaderVisitInitiator`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export; imports `ReaderWorkbenchCheck`, `ReaderWorkbenchProps`, `ReaderWorkbenchResume`
- [[Reference/Desktop/TypeScript/screens/today/LessonOfferPage|src/screens/today/LessonOfferPage.tsx]] — import-or-re-export; imports `LessonOfferPage`
- [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]] — import-or-re-export; imports `lessonEntryFor`
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
- [apps/learnloop-tauri/src/app/App.offerPage.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.offerPage.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.lessonSuggestion.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.lessonSuggestion.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound5.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound5.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound4.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
