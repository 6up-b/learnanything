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
| Source lines | 2457 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `9ed381bc3787439c88ffe3ec08b319b51049fa02` |
| Commit timestamp | `2026-11-01T03:48:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]]

## Public API

- `export function App()` — function, line 126

## Internal implementation anchors

- `type Place, type ShellMode, type UthToolId } from "./shell"` — type, line 47
- `type ShellMode, type UthToolId } from "./shell"` — type, line 48
- `type UthToolId } from "./shell"` — type, line 49
- `type PracticeOffer, type ProposalOrigin } from "./practiceOffer"` — type, line 83
- `type ProposalOrigin } from "./practiceOffer"` — type, line 84
- `type OpenSourceTarget =` — type, line 94
- `const ReaderScreen = lazy(()` — const, line 102
- `const GraphScreen = lazy(()` — const, line 103
- `const IngestScreen = lazy(()` — const, line 104
- `const ExamScreen = lazy(()` — const, line 105
- `const ProposalsScreen = lazy(()` — const, line 106
- `const RegistryReviewScreen = lazy(()` — const, line 107
- `const GoldenPathScreen = lazy(()` — const, line 108
- `const KnowledgeMapView = lazy(()` — const, line 110
- `const LibraryScreen = lazy(()` — const, line 111
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview"` — type, line 113
- `type VaultFilesChangedEvent =` — type, line 115
- `const previousTabRef = useRef<TopTab>(tab)` — const, line 135
- `const readerSkimmingRef = useRef(false)` — const, line 138
- `const noteReaderSkimming = useCallback((muted: boolean)` — const, line 139
- `const previous = previousTabRef.current` — const, line 143
- `const landing = shellRef.current === "simple" && tab === "start" ? "today" : tab` — const, line 148
- `const armed = wrapUpOfferArmed(previous, landing) && !readerSkimmingRef.current` — const, line 149
- `const readerSourceRef = useRef<ReaderOpenSource | null>(null)` — const, line 159
- `const dailyPlanQuery = useDailyPlan(session?.sessionId ?? null, Boolean(session))` — const, line 186
- `const planServing = dailyPlanQuery.data?.enabled === true && dailyPlanQuery.data.plan !== null` — const, line 187
- `const onPracticeDraft = useCallback((draft: PracticeDraftMirror)` — const, line 264
- `const startupStartedRef = useRef(false)` — const, line 296
- `const teachBackActiveRef = useRef(false)` — const, line 300
- `const practiceAskAllowedRef = useRef(false)` — const, line 304
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 305
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 308
- `const practiceAskStateRef = useRef<(()` — const, line 314
- `const onPracticeAskState = useCallback( (reader: (()` — const, line 315
- `const practiceAskOpenRef = useRef<(()` — const, line 323
- `const onPracticeAskOpener = useCallback((open: (()` — const, line 324
- `const shell: ShellMode = snapshot ? algoConfig().shell : "classic"` — const, line 334
- `const shellRef = useRef<ShellMode>(shell)` — const, line 346
- `const simple = shell === "simple"` — const, line 348
- `const sessionRef = useRef<SessionSnapshot | null>(session)` — const, line 353
- `const implicitStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 355
- `const pendingStartRef = useRef<Promise<SessionSnapshot | null> | null>(null)` — const, line 359
- `const vaultGenRef = useRef(0)` — const, line 364
- `const vaultChangesRef = useRef(0)` — const, line 369
- `const pushNotice = useCallback((input: NoticeInput)` — const, line 371
- `const onError = useCallback( (message: string, report?: ErrorReport)` — const, line 376
- `const command = report?.error === undefined ? null : getCommandError(report.error)` — const, line 382
- `const code = command?.code ?? null` — const, line 383
- `const notify = useCallback( (message: string)` — const, line 396
- `const reportError = useCallback( (error: unknown, fallback: string, action?:` — const, line 405
- `const message = errorMessage(error, fallback)` — const, line 407
- `const command = getCommandError(error)` — const, line 412
- `const code = command?.code ?? null` — const, line 413
- `const needSession = useCallback( (need: keyof typeof NEEDS_SESSION)` — const, line 420
- `const settingsNotice: ShellNotice | null = simple ? notices[notices.length - 1] ?? null : null` — const, line 431
- `const settingsNoticeId = settingsNotice?.id ?? null` — const, line 432
- `const dismissSettingsNotice = useCallback(()` — const, line 433
- `const onPaletteEntities = useCallback((ids:` — const, line 440
- `const refreshAiConnection = useCallback(()` — const, line 445
- `const landOnLibraryIfEmpty = useCallback(async (appSnapshot: AppSnapshot)` — const, line 451
- `const library = await api.getSourceLibrary()` — const, line 454
- `const restoreLastPlace = useCallback(async (appSnapshot: AppSnapshot)` — const, line 465
- `const place = rememberedPlace()` — const, line 466
- `const tool = rememberedTool()` — const, line 468
- `const root = appSnapshot.vault?.root` — const, line 480
- `const sourceId = root ? rememberedBook(root) : null` — const, line 481
- `const card = (await api.getSourceLibrary()).sources.find((entry)` — const, line 484
- `const loadInitialVault = useCallback(async ()` — const, line 497
- `const appSnapshot = await api.loadVault()` — const, line 500
- `const checkpoint = appSnapshot.activeSession?.checkpoint` — const, line 504
- `let disposed = false` — let, line 529
- `let unlisten: (()` — let, line 530
- `let invalidateTimer: number | null = null` — let, line 535
- `const scheduleInvalidateAll = ()` — const, line 536
- `const next = payload.refresh.snapshot` — const, line 553
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 563
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 598
- `let disposed = false` — let, line 604
- `const refresh = ()` — const, line 605
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 616
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 623
- `const hasSnapshot = snapshot !== null` — const, line 636
- `const place = placeOfTab(tab)` — const, line 639
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 642
- `const rememberedBookRef = useRef<string | null>(null)` — const, line 650
- `const root = snapshot?.vault?.root` — const, line 666
- `const runKeyActionRef = useRef<(action: KeyAction)` — const, line 672
- `const onKey = (event: KeyboardEvent)` — const, line 681
- `const binding = matchShellKey(event, shellRef.current, isTypingTarget(event.target))` — const, line 682
- `const restored = useMemo( ()` — const, line 691
- `const subjectOptions = useMemo(()` — const, line 697
- `const titles = new Map((snapshot?.vault?.subjectTitles ?? []).map((entry)` — const, line 698
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 701
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 704
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 705
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 710
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 717
- `const applyGradingProvider = useCallback( async (provider: string)` — const, line 723
- `const result = await api.setGradingProvider(provider)` — const, line 725
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 747
- `function beginSession(next: SessionSnapshot, firstStep?: PlanStepDto | null)` — function, line 761
- `const action = planStepAction(firstStep,` — const, line 784
- `function implicitSession(): Promise<SessionSnapshot | null>` — function, line 836
- `const generation = vaultGenRef.current` — const, line 840
- `const current = ()` — const, line 841
- `let started: Promise<SessionSnapshot | null> | null = null` — let, line 842
- `const minutes = await implicitSessionMinutes()` — const, line 845
- `const next = await startSessionHere(minutes)` — const, line 854
- `function startSessionHere(minutes: number): Promise<SessionSnapshot | null>` — function, line 875
- `const generation = vaultGenRef.current` — const, line 881
- `let request: Promise<SessionSnapshot>` — let, line 882
- `const pending: Promise<SessionSnapshot | null> = request .then((next)` — const, line 888
- `function withImplicitSession(action: (started: SessionSnapshot, stillOpen: ()` — function, line 906
- `const generation = vaultGenRef.current` — const, line 908
- `const stillOpen = ()` — const, line 909
- `function showPractice(id: string)` — function, line 915
- `function openPractice( id: string, schedulerCandidateId?: string | null, proposalOrigin?: ProposalOrigin | null, planPresentationId?: string | null )` — function, line 924
- `async function pickCheckMe( request: ReaderCheckMeRequest, sessionId: string, // UX Phase 3 fix round 1 (F1): after an implicit start, whether the vault // it started in is still the open one (checked after each request). options:` — function, line 962
- `const stillOpen = options.stillOpen ?? (()` — const, line 969
- `const result = await api.planLearnerPick( request.practiceItemId, sessionId, null, request.proposalId ?? null, request.importId ?? null )` — const, line 971
- `const offer = readerCheckOffer(result, request.practiceItemId, request.proposalId ?? null, request.importId ?? null)` — const, line 975
- `const served = await api.getPracticeItem(request.practiceItemId, sessionId, offer.proposalOrigin ?? null)` — const, line 977
- `const onReaderWorkbenchSubmitted: NonNullable<ReaderWorkbenchProps["onSubmitted"]> = (result, at)` — const, line 1018
- `const readerWorkbench: ReaderWorkbenchProps | undefined = algoConfig().workbench ?` — const, line 1030
- `function openReaderExercise(request: ReaderExerciseRequest, options:` — function, line 1054
- `function exerciseFromReader(request: ReaderExerciseRequest)` — function, line 1063
- `function checkMeFromReader(request: ReaderCheckMeRequest)` — function, line 1077
- `function backFromPractice(options:` — function, line 1093
- `const target = readerTargetBack(readerReturn,` — const, line 1095
- `async function openPlanReadingNow(reading: PlanReadingDto, estMinutes: number | null)` — function, line 1110
- `const library = await api.getSourceLibrary()` — const, line 1111
- `const target = readerTargetForReading(reading, library.sources)` — const, line 1112
- `async function openPlanReading(reading: PlanReadingDto, estMinutes: number | null = null)` — function, line 1121
- `async function openPassageNow(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1137
- `const generation = vaultGenRef.current` — const, line 1138
- `const library = await api.getSourceLibrary()` — const, line 1139
- `const card = library.sources.find((entry)` — const, line 1141
- `async function openPassage(sourceId: string, spanId: string | null, reading: string | null)` — function, line 1151
- `function resumeProblem(problem: WorkbenchOpenProblemDto)` — function, line 1161
- `async function openStudiedNow(restoration: IntentRestorationDto)` — function, line 1170
- `const library = await api.getSourceLibrary()` — const, line 1171
- `const target = readerTargetForRestoration(restoration, library.sources)` — const, line 1172
- `async function openStudied(restoration: IntentRestorationDto)` — function, line 1180
- `function routePlanStep(step: PlanStepDto | null)` — function, line 1194
- `const action = planStepAction(step)` — const, line 1195
- `function openPrimedRetry(id: string)` — function, line 1207
- `function showPrimed(id: string)` — function, line 1221
- `function openGuidedRedo(redo: GuidedRedoDto)` — function, line 1232
- `function showGuidedRedo(redo: GuidedRedoDto)` — function, line 1248
- `function openFeedback(id: string)` — function, line 1257
- `async function startQuickCheck(learningObjectIds: string[])` — function, line 1272
- `const generation = vaultGenRef.current` — const, line 1275
- `const implicit = !session && shellRef.current === "simple"` — const, line 1276
- `const stillOpen = ()` — const, line 1277
- `let current = session` — let, line 1278
- `const requestId = globalThis.crypto?.randomUUID?.() ?? `$` — const, line 1287
- `const progress = await api.startQuickCheck(` — const, line 1288
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 1297
- `function openLibraryShelf()` — function, line 1305
- `function openLibraryFile(path: string)` — function, line 1311
- `function clearLocalCheckpoint(identity?:` — function, line 1317
- `const checkpoint = current.checkpoint` — const, line 1321
- `function endSession(summary: SessionEndSummary)` — function, line 1340
- `function gotoTab(next: TopTab)` — function, line 1359
- `function gotoPlace(place: Place)` — function, line 1380
- `function selectUthTool(tool: UthToolId, options:` — function, line 1386
- `function openUnderTheHood()` — function, line 1394
- `async function openAnotherLibrary()` — function, line 1398
- `const selected = await openDialog(` — const, line 1400
- `function openRepair(misconceptionId: string)` — function, line 1409
- `function openExam(goalId: string)` — function, line 1414
- `function exitExam()` — function, line 1419
- `function openCalibration(id: string, options?:` — function, line 1426
- `function exitCalibration()` — function, line 1434
- `const askCurrentContext = useCallback((): boolean` — const, line 1444
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 1479
- `const openBook = useCallback((card: SourceLibraryCard)` — const, line 1491
- `const openAddedItem = useCallback( async (item: AddSourceItemDto)` — const, line 1499
- `let card: SourceLibraryCard | undefined` — let, line 1509
- `const adder = useAddSource(` — const, line 1538
- `const addSources = adder.add` — const, line 1539
- `const fileDragging = useSourceFileDrop(` — const, line 1540
- `function gotoProposalBatch(patchId: string)` — function, line 1557
- `function resetShellForVault()` — function, line 1563
- `const changeVault = useCallback( async (path: string)` — const, line 1603
- `let selected = false` — let, line 1605
- `let selectionAttempted = false` — let, line 1606
- `const next = await api.loadVault()` — const, line 1642
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 1650
- `const libraryFilesProps =` — const, line 1673
- `function libraryPlace(booksOnly = false)` — function, line 1686
- `const gradingTrouble = simple && snapshot !== null && !manualGrading && aiConnection !== null && aiConnection.needs !== "connect" && !(snapshot.health.ai?.ready ?? snapshot.health.codex.ready ?? false)` — const, line 1711
- `const readerHolding = simple && tab === "reader" && readerSource !== null && !examGoalId && !calibrationSessionId && !(goldenRunId && SHOW_GOLDEN_PATH)` — const, line 1720
- `function paletteCommands(): PaletteCommand[]` — function, line 1724
- `const current = uthTool(uthToolOfTab(tab, uthToolState))` — const, line 1725
- `const practicing = tab === "today" && todayStage === "practice"` — const, line 1761
- `function wrapUpLine(landing: WrapUpLanding)` — function, line 1788
- `function renderBody()` — function, line 1793
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 1833
- `const todayPlace = ()` — const, line 1857
- `const start = ( <StartScreen onBegin=` — const, line 1879
- `const fromReader = simplePracticeFeedback() && returnsToReader(readerReturn, practiceItemId)` — const, line 1973
- `const planNext = Boolean(session && !calibrationSessionId && planServing)` — const, line 1974
- `const feedbackDock = algoConfig().ask !== null && askTarget?.context === "feedback" ? askTarget : null` — const, line 1977
- `const today = ( <TodayScreen key=` — const, line 2016
- `const tool = uthToolOfTab(tab, uthToolState)` — const, line 2056
- `function renderIngest()` — function, line 2081
- `function renderProposals()` — function, line 2098
- `function renderRegistry()` — function, line 2114
- `function renderGolden()` — function, line 2129
- `function renderMaintain()` — function, line 2152
- `function renderUthTool(tool: UthToolId)` — function, line 2164
- `function renderAfterGolden()` — function, line 2195
- `const shellTree = ( <> <TerminalFrame active=` — const, line 2224
- `function unique(values: Array<string | null>): string[]` — function, line 2455

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
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export; imports `Place`, `ShellMode`, `UthToolId`, `isTabTool`, `placeOfTab`, `rememberBook`, `rememberPlace`, `rememberTool`, `rememberedBook`, `rememberedPlace`, `rememberedTool`, `tabForPlace`, `uthTool`, `uthToolOfTab`, `visibleUthTools`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export; imports `implicitSessionMinutes`
- [[Reference/Desktop/TypeScript/app/useGlobalAdd|src/app/useGlobalAdd.ts]] — import-or-re-export; imports `useGlobalAdd`
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
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export; imports `SessionFinishHud`
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
- [apps/learnloop-tauri/src/app/App.fixRound5.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound5.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound4.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound3.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound3.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/App.fixRound2.test.tsx](../../../../../../apps/learnloop-tauri/src/app/App.fixRound2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
