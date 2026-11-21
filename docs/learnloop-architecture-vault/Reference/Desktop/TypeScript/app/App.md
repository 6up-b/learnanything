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
| Source lines | 2690 |
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

- `export function App()` — function, line 139

## Internal implementation anchors

- `type Place, type ShellMode, type UthToolId } from "./shell"` — type, line 54
- `type ShellMode, type UthToolId } from "./shell"` — type, line 55
- `type UthToolId } from "./shell"` — type, line 56
- `type PracticeOffer, type ProposalOrigin } from "./practiceOffer"` — type, line 93
- `type ProposalOrigin } from "./practiceOffer"` — type, line 94
- `const NOTHING_TO_ASK = "Nothing here to ask about: open a question, feedback or a note first."` — const, line 105
- `type OpenSourceTarget =` — type, line 107
- `const ReaderScreen = lazy(()` — const, line 115
- `const LessonScreen = lazy(()` — const, line 116
- `const GraphScreen = lazy(()` — const, line 117
- `const IngestScreen = lazy(()` — const, line 118
- `const ExamScreen = lazy(()` — const, line 119
- `const ProposalsScreen = lazy(()` — const, line 120
- `const RegistryReviewScreen = lazy(()` — const, line 121
- `const KnowledgeMapView = lazy(()` — const, line 123
- `const LibraryScreen = lazy(()` — const, line 124
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview" | "offer"` — type, line 126
- `type VaultFilesChangedEvent =` — type, line 128
- `const previousTabRef = useRef<TopTab>(tab)` — const, line 148
- `const readerSkimmingRef = useRef(false)` — const, line 151
- `const noteReaderSkimming = useCallback((muted: boolean)` — const, line 152
- `const previous = previousTabRef.current` — const, line 156
- `const landing = shellRef.current === "simple" && tab === "start" ? "today" : tab` — const, line 161
- `const armed = wrapUpOfferArmed(previous, landing) && !readerSkimmingRef.current` — const, line 162
- `const readerSourceRef = useRef<ReaderOpenSource | null>(null)` — const, line 172
- `const aiOkAsked = useAiOkAsked()` — const, line 189
- `const dailyPlanQuery = useDailyPlan(session?.sessionId ?? null, Boolean(session))` — const, line 206
- `const planServing = dailyPlanQuery.data?.enabled === true && dailyPlanQuery.data.plan !== null` — const, line 207
- `const planAtOffer = useRef<` — const, line 210
- `const read = dailyPlanQuery.data` — const, line 216
- `const onPracticeDraft = useCallback((draft: PracticeDraftMirror)` — const, line 298
- `const sessionMoved = useSessionMoved()` — const, line 301
- `const startupStartedRef = useRef(false)` — const, line 333
- `const teachBackActiveRef = useRef(false)` — const, line 337
- `const practiceAskAllowedRef = useRef(false)` — const, line 341
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 342
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 345
- `const practiceAskStateRef = useRef<(()` — const, line 351
- `const onPracticeAskState = useCallback( (reader: (()` — const, line 352
- `const practiceAskOpenRef = useRef<(()` — const, line 360
- `const onPracticeAskOpener = useCallback((open: (()` — const, line 361
- `const shell: ShellMode = snapshot ? algoConfig().shell : "classic"` — const, line 371
- `const shellRef = useRef<ShellMode>(shell)` — const, line 383
- `const simple = shell === "simple"` — const, line 385
- `const sessionRef = useRef<SessionSnapshot | null>(session)` — const, line 390
- `const implicitStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 392
- `const pendingStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 396
- `const vaultGenRef = useRef(0)` — const, line 401
- `const vaultChangesRef = useRef(0)` — const, line 406
- `const pushNotice = useCallback((input: NoticeInput)` — const, line 408
- `const onError = useCallback( (message: string, report?: ErrorReport)` — const, line 417
- `const command = report?.error === undefined ? null : getCommandError(report.error)` — const, line 423
- `const code = command?.code ?? null` — const, line 424
- `const notify = useCallback( (message: string)` — const, line 437
- `const reportError = useCallback( (error: unknown, fallback: string, action?:` — const, line 448
- `const message = errorMessage(error, fallback)` — const, line 450
- `const command = getCommandError(error)` — const, line 455
- `const code = command?.code ?? null` — const, line 456
- `const needSession = useCallback( (need: keyof typeof NEEDS_SESSION)` — const, line 463
- `const settingsNotice: ShellNotice | null = simple ? notices[notices.length - 1] ?? null : null` — const, line 474
- `const settingsNoticeId = settingsNotice?.id ?? null` — const, line 475
- `const dismissSettingsNotice = useCallback(()` — const, line 476
- `const onPaletteEntities = useCallback((ids:` — const, line 483
- `const refreshAiConnection = useCallback(()` — const, line 488
- `const landOnLibraryIfEmpty = useCallback(async (appSnapshot: AppSnapshot)` — const, line 494
- `const library = await api.getSourceLibrary()` — const, line 497
- `const restoreLastPlace = useCallback(async (appSnapshot: AppSnapshot)` — const, line 508
- `const place = rememberedPlace()` — const, line 509
- `const tool = rememberedTool()` — const, line 511
- `const root = appSnapshot.vault?.root` — const, line 523
- `const sourceId = root ? rememberedBook(root) : null` — const, line 524
- `const card = (await api.getSourceLibrary()).sources.find((entry)` — const, line 527
- `const loadInitialVault = useCallback(async ()` — const, line 540
- `const appSnapshot = await api.loadVault()` — const, line 543
- `const checkpoint = appSnapshot.activeSession?.checkpoint` — const, line 547
- `let disposed = false` — let, line 572
- `let unlisten: (()` — let, line 573
- `let invalidateTimer: number | null = null` — let, line 578
- `const scheduleInvalidateAll = ()` — const, line 579
- `const next = payload.refresh.snapshot` — const, line 596
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 606
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 641
- `let disposed = false` — let, line 663
- `const refresh = ()` — const, line 664
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 675
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 682
- `const hasSnapshot = snapshot !== null` — const, line 695
- `const place = placeOfTab(tab)` — const, line 698
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 701
- `const rememberedBookRef = useRef<string | null>(null)` — const, line 709
- `const root = snapshot?.vault?.root` — const, line 725
- `const runKeyActionRef = useRef<(action: KeyAction)` — const, line 731
- `const onKey = (event: KeyboardEvent)` — const, line 740
- `const binding = matchShellKey(event, shellRef.current, isTypingTarget(event.target))` — const, line 741
- `const restored = useMemo( ()` — const, line 750
- `const subjectOptions = useMemo(()` — const, line 756
- `const titles = new Map((snapshot?.vault?.subjectTitles ?? []).map((entry)` — const, line 757
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 760
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 763
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 764
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 769
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 776
- `const applyGradingProvider = useCallback( async (provider: string)` — const, line 782
- `const result = await api.setGradingProvider(provider)` — const, line 784
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 806
- `function beginSession(next: SessionSnapshot, firstStep?: PlanStepDto | null)` — function, line 820
- `const action = planStepAction(firstStep,` — const, line 847
- `function implicitSession(): Promise<SessionSnapshot | null>` — function, line 899
- `const generation = vaultGenRef.current` — const, line 903
- `const current = ()` — const, line 904
- `let started: Promise<SessionSnapshot | null> | null = null` — let, line 905
- `const minutes = await implicitSessionMinutes()` — const, line 908
- `const next = await startSessionHere(minutes)` — const, line 917
- `function startSessionHere(minutes: number): Promise<SessionSnapshot | null>` — function, line 938
- `const generation = vaultGenRef.current` — const, line 944
- `let request: Promise<SessionSnapshot | null>` — let, line 945
- `const pending: Promise<SessionSnapshot | null> = request .then((next)` — const, line 952
- `function withImplicitSession(action: (started: SessionSnapshot, stillOpen: ()` — function, line 970
- `const generation = vaultGenRef.current` — const, line 972
- `const stillOpen = ()` — const, line 973
- `function showPractice(id: string)` — function, line 979
- `function openPractice( id: string, schedulerCandidateId?: string | null, proposalOrigin?: ProposalOrigin | null, planPresentationId?: string | null )` — function, line 988
- `async function pickCheckMe( request: ReaderCheckMeRequest, sessionId: string, // UX Phase 3 fix round 1 (F1): after an implicit start, whether the vault // it started in is still the open one (checked after each request). options:` — function, line 1026
- `const stillOpen = options.stillOpen ?? (()` — const, line 1033
- `const result = await api.planLearnerPick( request.practiceItemId, sessionId, null, request.proposalId ?? null, request.importId ?? null )` — const, line 1035
- `const offer = readerCheckOffer(result, request.practiceItemId, request.proposalId ?? null, request.importId ?? null)` — const, line 1039
- `const served = await api.getPracticeItem(request.practiceItemId, sessionId, offer.proposalOrigin ?? null)` — const, line 1041
- `const onReaderWorkbenchSubmitted: NonNullable<ReaderWorkbenchProps["onSubmitted"]> = (result, at)` — const, line 1082
- `const readerWorkbench: ReaderWorkbenchProps | undefined = algoConfig().workbench ?` — const, line 1094
- `function openReaderExercise(request: ReaderExerciseRequest, options:` — function, line 1118
- `function exerciseFromReader(request: ReaderExerciseRequest)` — function, line 1127
- `function checkMeFromReader(request: ReaderCheckMeRequest)` — function, line 1141
- `function backFromPractice(options:` — function, line 1157
- `const target = readerTargetBack(readerReturn,` — const, line 1159
- `async function openPlanReadingNow(reading: PlanReadingDto, estMinutes: number | null)` — function, line 1174
- `const library = await api.getSourceLibrary()` — const, line 1175
- `const target = readerTargetForReading(reading, library.sources)` — const, line 1176
- `async function openPlanReading(reading: PlanReadingDto, estMinutes: number | null = null)` — function, line 1186
- `async function openPassageNow(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1202
- `const generation = vaultGenRef.current` — const, line 1203
- `const library = await api.getSourceLibrary()` — const, line 1204
- `const card = library.sources.find((entry)` — const, line 1206
- `async function openPassage(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1216
- `function resumeProblem(problem: WorkbenchOpenProblemDto)` — function, line 1226
- `async function openStudiedNow(restoration: IntentRestorationDto)` — function, line 1235
- `const library = await api.getSourceLibrary()` — const, line 1236
- `const target = readerTargetForRestoration(restoration, library.sources)` — const, line 1237
- `async function openStudied(restoration: IntentRestorationDto)` — function, line 1245
- `function routePlanStep(step: PlanStepDto | null)` — function, line 1259
- `const action = planStepAction(step)` — const, line 1266
- `function openPlanOffer(step: PlanLessonOfferStepDto)` — function, line 1280
- `function answerPlanOffer(response: "accepted" | "chose_alternative" | "declined")` — function, line 1289
- `const sessionId = session?.sessionId ?? null` — const, line 1290
- `function closeOfferPage()` — function, line 1309
- `function answerSomethingElseOnOffer(result: SomethingElseChosenDto)` — function, line 1316
- `const entry = lessonEntryFor(result)` — const, line 1319
- `function openPrimedRetry(id: string)` — function, line 1327
- `function showPrimed(id: string)` — function, line 1341
- `function openGuidedRedo(redo: RedoContext)` — function, line 1352
- `function showGuidedRedo(redo: RedoContext)` — function, line 1368
- `function openFeedback(id: string)` — function, line 1377
- `function teachMeFromReader(request:` — function, line 1392
- `async function startQuickCheck(learningObjectIds: string[], beforeOpen?: ()` — function, line 1397
- `const generation = vaultGenRef.current` — const, line 1400
- `const implicit = !session && shellRef.current === "simple"` — const, line 1401
- `const stillOpen = ()` — const, line 1402
- `let current = session` — let, line 1403
- `const requestId = globalThis.crypto?.randomUUID?.() ?? `$` — const, line 1412
- `const progress = await api.startQuickCheck(` — const, line 1413
- `const nothing = quickCheckNothingToAsk(progress)` — const, line 1417
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 1430
- `function openLibraryShelf()` — function, line 1438
- `function lookInLibrary(phrase: string)` — function, line 1445
- `const seq = readerOpenSeq + 1` — const, line 1446
- `function openLibraryFile(path: string)` — function, line 1455
- `function installHandedSession(next: SessionSnapshot)` — function, line 1464
- `const item = next.checkpoint?.currentPracticeItemId ?? null` — const, line 1469
- `async function adoptSessionBack(from: SessionMoved)` — function, line 1475
- `async function startFreshOverMoved(from: SessionMoved)` — function, line 1484
- `const minutes = session?.availableMinutes ?? (await implicitSessionMinutes())` — const, line 1486
- `const next = await startSessionOrAsk(` — const, line 1488
- `function letGoOfEndedSession()` — function, line 1507
- `function clearLocalCheckpoint(identity?:` — function, line 1519
- `const checkpoint = current.checkpoint` — const, line 1523
- `function endSession(summary: SessionEndSummary)` — function, line 1542
- `function gotoTab(next: TopTab)` — function, line 1561
- `function gotoPlace(place: Place)` — function, line 1585
- `function selectUthTool(tool: UthToolId, options:` — function, line 1594
- `function openUnderTheHood()` — function, line 1602
- `async function openAnotherLibrary()` — function, line 1606
- `const selected = await openDialog(` — const, line 1608
- `function openRepair(misconceptionId: string)` — function, line 1617
- `function openExam(goalId: string)` — function, line 1622
- `function exitExam()` — function, line 1627
- `function openCalibration(id: string, options?:` — function, line 1634
- `function exitCalibration()` — function, line 1642
- `const askCurrentContext = useCallback((): boolean` — const, line 1652
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 1687
- `const openBook = useCallback((card: SourceLibraryCard)` — const, line 1699
- `const keepAddedItem = useCallback( (item: AddSourceItemDto)` — const, line 1709
- `const openAddedItem = useCallback( async (item: AddSourceItemDto)` — const, line 1718
- `let card: SourceLibraryCard | undefined` — let, line 1728
- `const adder = useAddSource(` — const, line 1761
- `const addSources = adder.add` — const, line 1762
- `const fileDragging = useSourceFileDrop(` — const, line 1763
- `function gotoProposalBatch(patchId: string)` — function, line 1780
- `function resetShellForVault()` — function, line 1786
- `const changeVault = useCallback( async (path: string)` — const, line 1825
- `let selected = false` — let, line 1827
- `let selectionAttempted = false` — let, line 1828
- `const next = await api.loadVault()` — const, line 1864
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 1872
- `const libraryFilesProps =` — const, line 1895
- `function libraryPlace(booksOnly = false)` — function, line 1908
- `const gradingTrouble = simple && snapshot !== null && !manualGrading && aiConnection !== null && aiConnection.needs !== "connect" && !(snapshot.health.ai?.ready ?? snapshot.health.codex.ready ?? false)` — const, line 1933
- `const readerHolding = simple && tab === "reader" && readerSource !== null && !examGoalId && !calibrationSessionId` — const, line 1942
- `function paletteCommands(): PaletteCommand[]` — function, line 1946
- `const current = uthTool(uthToolOfTab(tab, uthToolState))` — const, line 1947
- `const practicing = tab === "today" && todayStage === "practice"` — const, line 1983
- `function wrapUpLine(landing: WrapUpLanding)` — function, line 2012
- `function renderBody()` — function, line 2017
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 2041
- `const todayPlace = ()` — const, line 2067
- `const start = ( <StartScreen onBegin=` — const, line 2099
- `const fromReader = simplePracticeFeedback() && returnsToReader(readerReturn, practiceItemId)` — const, line 2213
- `const planNext = Boolean(session && !calibrationSessionId && planServing)` — const, line 2214
- `const feedbackDock = algoConfig().ask !== null && askTarget?.context === "feedback" ? askTarget : null` — const, line 2217
- `const today = ( <TodayScreen key=` — const, line 2258
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 2299
- `function renderIngest()` — function, line 2321
- `function renderProposals()` — function, line 2338
- `function renderRegistry()` — function, line 2354
- `function renderMaintain()` — function, line 2369
- `function renderUthTool(tool: UthToolId)` — function, line 2381
- `function renderRemainingTabs()` — function, line 2410
- `const shellTree = ( <> <TerminalFrame active=` — const, line 2439
- `function unique(values: Array<string | null>): string[]` — function, line 2688

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
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `Place`, `ShellMode`, `UthToolId`, `isTabTool`, `placeOfTab`, `rememberBook`, `rememberPlace`, `rememberTool`, `rememberedBook`, `rememberedPlace`, `rememberedTool`, `tabForPlace`, `uthTool`, `uthToolOfTab`, `visibleUthTools`
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
