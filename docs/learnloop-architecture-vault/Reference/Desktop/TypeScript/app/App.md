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
| Source lines | 2714 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]]

## Public API

- `export function App()` — function, line 143

## Internal implementation anchors

- `type Place, type ReaderSurface, type ShellMode, type UthToolId } from "./shell"` — type, line 56
- `type ReaderSurface, type ShellMode, type UthToolId } from "./shell"` — type, line 57
- `type ShellMode, type UthToolId } from "./shell"` — type, line 58
- `type UthToolId } from "./shell"` — type, line 59
- `type PracticeOffer, type ProposalOrigin } from "./practiceOffer"` — type, line 96
- `type ProposalOrigin } from "./practiceOffer"` — type, line 97
- `const NOTHING_TO_ASK = "Nothing here to ask about: open a question, feedback or a note first."` — const, line 108
- `type OpenSourceTarget =` — type, line 110
- `const ReaderScreen = lazy(()` — const, line 118
- `const DeskShell = lazy(()` — const, line 119
- `const LessonScreen = lazy(()` — const, line 120
- `const GraphScreen = lazy(()` — const, line 121
- `const IngestScreen = lazy(()` — const, line 122
- `const ExamScreen = lazy(()` — const, line 123
- `const ProposalsScreen = lazy(()` — const, line 124
- `const RegistryReviewScreen = lazy(()` — const, line 125
- `const KnowledgeMapView = lazy(()` — const, line 127
- `const LibraryScreen = lazy(()` — const, line 128
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview" | "offer"` — type, line 130
- `type VaultFilesChangedEvent =` — type, line 132
- `const previousTabRef = useRef<TopTab>(tab)` — const, line 152
- `const readerSkimmingRef = useRef(false)` — const, line 155
- `const noteReaderSkimming = useCallback((muted: boolean)` — const, line 156
- `const previous = previousTabRef.current` — const, line 160
- `const landing = shellRef.current === "simple" && tab === "start" ? "today" : tab` — const, line 165
- `const armed = wrapUpOfferArmed(previous, landing) && !readerSkimmingRef.current` — const, line 166
- `const chooseReaderSurface = useCallback((surface: ReaderSurface)` — const, line 177
- `const readerSourceRef = useRef<ReaderOpenSource | null>(null)` — const, line 183
- `const aiOkAsked = useAiOkAsked()` — const, line 200
- `const dailyPlanQuery = useDailyPlan(session?.sessionId ?? null, Boolean(session))` — const, line 217
- `const planServing = dailyPlanQuery.data?.enabled === true && dailyPlanQuery.data.plan !== null` — const, line 218
- `const planAtOffer = useRef<` — const, line 221
- `const read = dailyPlanQuery.data` — const, line 227
- `const onPracticeDraft = useCallback((draft: PracticeDraftMirror)` — const, line 309
- `const sessionMoved = useSessionMoved()` — const, line 312
- `const startupStartedRef = useRef(false)` — const, line 344
- `const teachBackActiveRef = useRef(false)` — const, line 348
- `const practiceAskAllowedRef = useRef(false)` — const, line 352
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 353
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 356
- `const practiceAskStateRef = useRef<(()` — const, line 362
- `const onPracticeAskState = useCallback( (reader: (()` — const, line 363
- `const practiceAskOpenRef = useRef<(()` — const, line 371
- `const onPracticeAskOpener = useCallback((open: (()` — const, line 372
- `const shell: ShellMode = snapshot ? algoConfig().shell : "classic"` — const, line 382
- `const shellRef = useRef<ShellMode>(shell)` — const, line 394
- `const simple = shell === "simple"` — const, line 396
- `const sessionRef = useRef<SessionSnapshot | null>(session)` — const, line 401
- `const implicitStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 403
- `const pendingStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 407
- `const vaultGenRef = useRef(0)` — const, line 412
- `const vaultChangesRef = useRef(0)` — const, line 417
- `const pushNotice = useCallback((input: NoticeInput)` — const, line 419
- `const onError = useCallback( (message: string, report?: ErrorReport)` — const, line 428
- `const command = report?.error === undefined ? null : getCommandError(report.error)` — const, line 434
- `const code = command?.code ?? null` — const, line 435
- `const notify = useCallback( (message: string)` — const, line 448
- `const reportError = useCallback( (error: unknown, fallback: string, action?:` — const, line 459
- `const message = errorMessage(error, fallback)` — const, line 461
- `const command = getCommandError(error)` — const, line 466
- `const code = command?.code ?? null` — const, line 467
- `const needSession = useCallback( (need: keyof typeof NEEDS_SESSION)` — const, line 474
- `const settingsNotice: ShellNotice | null = simple ? notices[notices.length - 1] ?? null : null` — const, line 485
- `const settingsNoticeId = settingsNotice?.id ?? null` — const, line 486
- `const dismissSettingsNotice = useCallback(()` — const, line 487
- `const onPaletteEntities = useCallback((ids:` — const, line 494
- `const refreshAiConnection = useCallback(()` — const, line 499
- `const landOnLibraryIfEmpty = useCallback(async (appSnapshot: AppSnapshot)` — const, line 505
- `const library = await api.getSourceLibrary()` — const, line 508
- `const restoreLastPlace = useCallback(async (appSnapshot: AppSnapshot)` — const, line 519
- `const place = rememberedPlace()` — const, line 520
- `const tool = rememberedTool()` — const, line 522
- `const root = appSnapshot.vault?.root` — const, line 534
- `const sourceId = root ? rememberedBook(root) : null` — const, line 535
- `const card = (await api.getSourceLibrary()).sources.find((entry)` — const, line 538
- `const loadInitialVault = useCallback(async ()` — const, line 551
- `const appSnapshot = await api.loadVault()` — const, line 554
- `const checkpoint = appSnapshot.activeSession?.checkpoint` — const, line 558
- `let disposed = false` — let, line 583
- `let unlisten: (()` — let, line 584
- `let invalidateTimer: number | null = null` — let, line 589
- `const scheduleInvalidateAll = ()` — const, line 590
- `const next = payload.refresh.snapshot` — const, line 607
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 617
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 652
- `let disposed = false` — let, line 674
- `const refresh = ()` — const, line 675
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 686
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 693
- `const hasSnapshot = snapshot !== null` — const, line 706
- `const place = placeOfTab(tab)` — const, line 709
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 712
- `const rememberedBookRef = useRef<string | null>(null)` — const, line 720
- `const root = snapshot?.vault?.root` — const, line 736
- `const runKeyActionRef = useRef<(action: KeyAction)` — const, line 742
- `const onKey = (event: KeyboardEvent)` — const, line 751
- `const binding = matchShellKey(event, shellRef.current, isTypingTarget(event.target))` — const, line 752
- `const restored = useMemo( ()` — const, line 761
- `const subjectOptions = useMemo(()` — const, line 767
- `const titles = new Map((snapshot?.vault?.subjectTitles ?? []).map((entry)` — const, line 768
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 771
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 774
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 775
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 780
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 787
- `const applyGradingProvider = useCallback( async (provider: string)` — const, line 793
- `const result = await api.setGradingProvider(provider)` — const, line 795
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 817
- `function beginSession(next: SessionSnapshot, firstStep?: PlanStepDto | null)` — function, line 831
- `const action = planStepAction(firstStep,` — const, line 858
- `function implicitSession(): Promise<SessionSnapshot | null>` — function, line 910
- `const generation = vaultGenRef.current` — const, line 914
- `const current = ()` — const, line 915
- `let started: Promise<SessionSnapshot | null> | null = null` — let, line 916
- `const minutes = await implicitSessionMinutes()` — const, line 919
- `const next = await startSessionHere(minutes)` — const, line 928
- `function startSessionHere(minutes: number): Promise<SessionSnapshot | null>` — function, line 949
- `const generation = vaultGenRef.current` — const, line 955
- `let request: Promise<SessionSnapshot | null>` — let, line 956
- `const pending: Promise<SessionSnapshot | null> = request .then((next)` — const, line 963
- `function withImplicitSession(action: (started: SessionSnapshot, stillOpen: ()` — function, line 981
- `const generation = vaultGenRef.current` — const, line 983
- `const stillOpen = ()` — const, line 984
- `function showPractice(id: string)` — function, line 990
- `function openPractice( id: string, schedulerCandidateId?: string | null, proposalOrigin?: ProposalOrigin | null, planPresentationId?: string | null )` — function, line 999
- `async function pickCheckMe( request: ReaderCheckMeRequest, sessionId: string, // UX Phase 3 fix round 1 (F1): after an implicit start, whether the vault // it started in is still the open one (checked after each request). options:` — function, line 1037
- `const stillOpen = options.stillOpen ?? (()` — const, line 1044
- `const result = await api.planLearnerPick( request.practiceItemId, sessionId, null, request.proposalId ?? null, request.importId ?? null )` — const, line 1046
- `const offer = readerCheckOffer(result, request.practiceItemId, request.proposalId ?? null, request.importId ?? null)` — const, line 1050
- `const served = await api.getPracticeItem(request.practiceItemId, sessionId, offer.proposalOrigin ?? null)` — const, line 1052
- `const onReaderWorkbenchSubmitted: NonNullable<ReaderWorkbenchProps["onSubmitted"]> = (result, at)` — const, line 1093
- `const readerWorkbench: ReaderWorkbenchProps | undefined = algoConfig().workbench ?` — const, line 1105
- `function openReaderExercise(request: ReaderExerciseRequest, options:` — function, line 1129
- `function exerciseFromReader(request: ReaderExerciseRequest)` — function, line 1138
- `function checkMeFromReader(request: ReaderCheckMeRequest)` — function, line 1152
- `function backFromPractice(options:` — function, line 1168
- `const target = readerTargetBack(readerReturn,` — const, line 1170
- `async function openPlanReadingNow(reading: PlanReadingDto, estMinutes: number | null)` — function, line 1185
- `const library = await api.getSourceLibrary()` — const, line 1186
- `const target = readerTargetForReading(reading, library.sources)` — const, line 1187
- `async function openPlanReading(reading: PlanReadingDto, estMinutes: number | null = null)` — function, line 1197
- `async function openPassageNow(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1213
- `const generation = vaultGenRef.current` — const, line 1214
- `const library = await api.getSourceLibrary()` — const, line 1215
- `const card = library.sources.find((entry)` — const, line 1217
- `async function openPassage(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1227
- `function resumeProblem(problem: WorkbenchOpenProblemDto)` — function, line 1237
- `async function openStudiedNow(restoration: IntentRestorationDto)` — function, line 1246
- `const library = await api.getSourceLibrary()` — const, line 1247
- `const target = readerTargetForRestoration(restoration, library.sources)` — const, line 1248
- `async function openStudied(restoration: IntentRestorationDto)` — function, line 1256
- `function routePlanStep(step: PlanStepDto | null)` — function, line 1270
- `const action = planStepAction(step)` — const, line 1277
- `function openPlanOffer(step: PlanLessonOfferStepDto)` — function, line 1291
- `function answerPlanOffer(response: "accepted" | "chose_alternative" | "declined")` — function, line 1300
- `const sessionId = session?.sessionId ?? null` — const, line 1301
- `function closeOfferPage()` — function, line 1320
- `function answerSomethingElseOnOffer(result: SomethingElseChosenDto)` — function, line 1327
- `const entry = lessonEntryFor(result)` — const, line 1330
- `function openPrimedRetry(id: string)` — function, line 1338
- `function showPrimed(id: string)` — function, line 1352
- `function openGuidedRedo(redo: RedoContext)` — function, line 1363
- `function showGuidedRedo(redo: RedoContext)` — function, line 1379
- `function openFeedback(id: string)` — function, line 1388
- `function teachMeFromReader(request:` — function, line 1403
- `async function startQuickCheck(learningObjectIds: string[], beforeOpen?: ()` — function, line 1408
- `const generation = vaultGenRef.current` — const, line 1411
- `const implicit = !session && shellRef.current === "simple"` — const, line 1412
- `const stillOpen = ()` — const, line 1413
- `let current = session` — let, line 1414
- `const requestId = globalThis.crypto?.randomUUID?.() ?? `$` — const, line 1423
- `const progress = await api.startQuickCheck(` — const, line 1424
- `const nothing = quickCheckNothingToAsk(progress)` — const, line 1428
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 1441
- `function openLibraryShelf()` — function, line 1449
- `function lookInLibrary(phrase: string)` — function, line 1456
- `const seq = readerOpenSeq + 1` — const, line 1457
- `function openLibraryFile(path: string)` — function, line 1466
- `function installHandedSession(next: SessionSnapshot)` — function, line 1475
- `const item = next.checkpoint?.currentPracticeItemId ?? null` — const, line 1480
- `async function adoptSessionBack(from: SessionMoved)` — function, line 1486
- `async function startFreshOverMoved(from: SessionMoved)` — function, line 1495
- `const minutes = session?.availableMinutes ?? (await implicitSessionMinutes())` — const, line 1497
- `const next = await startSessionOrAsk(` — const, line 1499
- `function letGoOfEndedSession()` — function, line 1518
- `function clearLocalCheckpoint(identity?:` — function, line 1530
- `const checkpoint = current.checkpoint` — const, line 1534
- `function endSession(summary: SessionEndSummary)` — function, line 1553
- `function gotoTab(next: TopTab)` — function, line 1572
- `function gotoPlace(place: Place)` — function, line 1596
- `function selectUthTool(tool: UthToolId, options:` — function, line 1605
- `function openUnderTheHood()` — function, line 1613
- `async function openAnotherLibrary()` — function, line 1617
- `const selected = await openDialog(` — const, line 1619
- `function openRepair(misconceptionId: string)` — function, line 1628
- `function openExam(goalId: string)` — function, line 1633
- `function exitExam()` — function, line 1638
- `function openCalibration(id: string, options?:` — function, line 1645
- `function exitCalibration()` — function, line 1653
- `const askCurrentContext = useCallback((): boolean` — const, line 1663
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 1698
- `const openBook = useCallback((card: SourceLibraryCard)` — const, line 1710
- `const keepAddedItem = useCallback( (item: AddSourceItemDto)` — const, line 1720
- `const openAddedItem = useCallback( async (item: AddSourceItemDto)` — const, line 1729
- `let card: SourceLibraryCard | undefined` — let, line 1739
- `const adder = useAddSource(` — const, line 1772
- `const addSources = adder.add` — const, line 1773
- `const fileDragging = useSourceFileDrop(` — const, line 1774
- `function gotoProposalBatch(patchId: string)` — function, line 1791
- `function resetShellForVault()` — function, line 1797
- `const changeVault = useCallback( async (path: string)` — const, line 1836
- `let selected = false` — let, line 1838
- `let selectionAttempted = false` — let, line 1839
- `const next = await api.loadVault()` — const, line 1875
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 1883
- `const libraryFilesProps =` — const, line 1906
- `function libraryPlace(booksOnly = false)` — function, line 1919
- `const gradingTrouble = simple && snapshot !== null && !manualGrading && aiConnection !== null && aiConnection.needs !== "connect" && !(snapshot.health.ai?.ready ?? snapshot.health.codex.ready ?? false)` — const, line 1944
- `const readerHolding = simple && tab === "reader" && readerSource !== null && !examGoalId && !calibrationSessionId` — const, line 1953
- `function paletteCommands(): PaletteCommand[]` — function, line 1957
- `const current = uthTool(uthToolOfTab(tab, uthToolState))` — const, line 1958
- `const practicing = tab === "today" && todayStage === "practice"` — const, line 1994
- `function wrapUpLine(landing: WrapUpLanding)` — function, line 2023
- `function renderBody()` — function, line 2028
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 2052
- `const todayPlace = ()` — const, line 2078
- `const start = ( <StartScreen onBegin=` — const, line 2111
- `const fromReader = simplePracticeFeedback() && returnsToReader(readerReturn, practiceItemId)` — const, line 2225
- `const planNext = Boolean(session && !calibrationSessionId && planServing)` — const, line 2226
- `const feedbackDock = algoConfig().ask !== null && askTarget?.context === "feedback" ? askTarget : null` — const, line 2229
- `const today = ( <TodayScreen key=` — const, line 2270
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 2311
- `function renderIngest()` — function, line 2333
- `function renderProposals()` — function, line 2350
- `function renderRegistry()` — function, line 2366
- `function renderMaintain()` — function, line 2381
- `function renderUthTool(tool: UthToolId)` — function, line 2393
- `function renderRemainingTabs()` — function, line 2422
- `const shellTree = ( <> <TerminalFrame active=` — const, line 2463
- `function unique(values: Array<string | null>): string[]` — function, line 2712

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/main|src/main.tsx]] — import-or-re-export: `App`; references `App`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AddSourceItemDto`, `AiConnectionDto`, `AppSnapshot`, `AttemptProgress`, `CommandError`, `DailyPlanDto`, `IntentRestorationDto`, `PlanLessonOfferStepDto`, `PlanReadingDto`, `PlanStepDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `SomethingElseChosenDto`, `SourceLibraryCard`, `WorkbenchOpenProblemDto`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `clearQueryCache`, `invalidateAllQueries`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/app/ShellChromeRoot|src/app/ShellChromeRoot.tsx]] — import-or-re-export; imports `ShellChromeRoot`
- [[Reference/Desktop/TypeScript/app/aiOk|src/app/aiOk.ts]] — import-or-re-export; imports `answerAiOk`, `useAiOkAsked`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `setAlgoConfig`, `setRenderedShell`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export; imports `todayQueueInput`
- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export; imports `useCheckHandoff`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `planStepAction`, `readerTargetForReading`, `servedForExplicitStep`, `useDailyPlan`
- [[Reference/Desktop/TypeScript/app/intentCheck|src/app/intentCheck.ts]] — import-or-re-export; imports `readerTargetForRestoration`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `KeyAction`, `matchShellKey`
- [[Reference/Desktop/TypeScript/app/notices|src/app/notices.ts]] — import-or-re-export; imports `NEEDS_SESSION`, `NoticeInput`, `ShellNotice`, `addNotice`, `dismissNotice`, `noticeAfterSessionBegins`, `placeNotice`, `resolveNotices`, `sessionNotice`
- [[Reference/Desktop/TypeScript/app/practiceDraft|src/app/practiceDraft.ts]] — import-or-re-export; imports `PracticeDraftMirror`, `restoredPracticeDraft`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `feedbackOrigin`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/app/practiceOffer|src/app/practiceOffer.ts]] — import-or-re-export; imports `PracticeOffer`, `ProposalOrigin`, `planPresentationForServe`, `proposalOriginForServe`, `schedulerCandidateForServe`
- [[Reference/Desktop/TypeScript/app/readerCheck|src/app/readerCheck.ts]] — import-or-re-export; imports `ReaderReturn`, `keepReaderReturn`, `readerCheckOffer`, `returnsToReader`
- [[Reference/Desktop/TypeScript/app/readerWorkbench|src/app/readerWorkbench.ts]] — import-or-re-export; imports `consumeShown`, `readerTargetBack`, `readerWorkbenchCheck`, `sessionAfterWorkbenchSubmit`, `workbenchReturn`
- [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]] — import-or-re-export; imports `recordRecentVault`, `removeRecentVault`
- [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]] — import-or-re-export; imports `adoptMovedSession`, `startSessionOrAsk`
- [[Reference/Desktop/TypeScript/app/sessionMoved|src/app/sessionMoved.ts]] — import-or-re-export; imports `SessionMoved`, `setSessionMoved`, `useSessionMoved`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `Place`, `ReaderSurface`, `ShellMode`, `UthToolId`, `isTabTool`, `placeOfTab`, `rememberBook`, `rememberPlace`, `rememberReaderSurface`, `rememberTool`, `rememberedBook`, `rememberedPlace`, `rememberedReaderSurface`, `rememberedTool`, `tabForPlace`, `uthTool`, `uthToolOfTab`, `visibleUthTools`
- [[Reference/Desktop/TypeScript/app/todayCause|src/app/todayCause.ts]] — import-or-re-export; imports `LESSON_KEPT`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `implicitSessionMinutes`
- [[Reference/Desktop/TypeScript/app/useGlobalAdd|src/app/useGlobalAdd.ts]] — import-or-re-export; imports `useGlobalAdd`
- [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|src/app/useQueueRevisionPoll.ts]] — import-or-re-export; imports `revisionPollHeld`, `useQueueRevisionPoll`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `selectWithDraftFlush`
- [[Reference/Desktop/TypeScript/app/wrapUpOffer|src/app/wrapUpOffer.ts]] — import-or-re-export; imports `WrapUpLanding`, `wrapUpOfferArmed`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export; imports `AddPopover`, `DropOverlay`, `addedItemDestination`, `pastExamKeptLine`, `useAddSource`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export; imports `AdjudicationOverlay`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export; imports `CommandPalette`, `PaletteCommand`
- [[Reference/Desktop/TypeScript/components/ConnectAI|src/components/ConnectAI.tsx]] — import-or-re-export; imports `ConnectAISheet`
- [[Reference/Desktop/TypeScript/components/DockedAsk|src/components/DockedAsk.tsx]] — import-or-re-export; imports `DockedAsk`
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
- [[Reference/Desktop/TypeScript/components/pdfDocumentCache|src/components/pdfDocumentCache.ts]] — import-or-re-export; imports `clearPdfDocuments`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `NavBadgeCounts`, `TerminalFrame`, `TopTab`
- [[Reference/Desktop/TypeScript/components/useSourceFileDrop|src/components/useSourceFileDrop.ts]] — import-or-re-export; imports `pickSourceFiles`, `useSourceFileDrop`
- [[Reference/Desktop/TypeScript/copy/refusals|src/copy/refusals.ts]] — import-or-re-export; imports `NO_ASK_NOT_YET`, `NO_ASK_TEACH_BACK`, `quickCheckNothingToAsk`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `ErrorReport`, `NoticeRetry`, `RETRY_RAN`, `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export; imports `CalibrationScreen`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export; imports `DiagnosticReviewScreen`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export; imports `FeedbackScreen`
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
- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export; imports `RedoContext`
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
