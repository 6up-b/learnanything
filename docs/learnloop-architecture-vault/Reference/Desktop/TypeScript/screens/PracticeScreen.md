---
title: "Desktop module · src/screens/PracticeScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.PracticeScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/PracticeScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/PracticeScreen.tsx"
source_commit: "43bcc8fac4be9bfc864222dd8821769f1ee74d88"
source_commit_timestamp: "2026-11-03T19:34:35-05:00"
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

# `src/screens/PracticeScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PracticeScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/PracticeScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.tsx) |
| Source lines | 3120 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `43bcc8fac4be9bfc864222dd8821769f1ee74d88` |
| Commit timestamp | `2026-11-03T19:34:35-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]]

## Public API

- `export function PracticeScreen(` — function, line 131
- `export function helpRecordLine(` — function, line 3018

## Internal implementation anchors

- `const WORK_IN_STEPS_KEY = "ll.workbench.workInSteps"` — const, line 52
- `function rememberedWorkInSteps(): boolean` — function, line 53
- `function rememberWorkInSteps(on: boolean): void` — function, line 60
- `type CommittedAttemptRecovery =` — type, line 69
- `type PracticeCheckpointIdentity =` — type, line 75
- `function committedAttemptRecovery(error: unknown): CommittedAttemptRecovery | null` — function, line 80
- `const command = getCommandError(error)` — const, line 81
- `const details = command.details as` — const, line 85
- `const attemptId = details.attempt_id ?? details.attemptId` — const, line 91
- `const attemptType = details.attempt_type ?? details.attemptType` — const, line 93
- `function activeProbeContract(contract: ProbeContractDto): ProbeContractDto | null` — function, line 104
- `const restrictions = contract.restrictions` — const, line 114
- `const originalPageOpen = useRef(false)` — const, line 268
- `const stuckPrompt = algoConfig().stuckPrompt` — const, line 274
- `const ratingTap = algoConfig().ratingTap` — const, line 292
- `const firstHint = useFirstHintProgress(` — const, line 299
- `const firstHintRef = useRef(firstHint.value)` — const, line 301
- `const hintSeenRef = useRef(hintSeen)` — const, line 308
- `const seeHint = useCallback(()` — const, line 310
- `const simple = simplePracticeFeedback()` — const, line 325
- `const disclosedRef = useRef(disclosed)` — const, line 338
- `const mountedRef = useRef(true)` — const, line 344
- `const proposalOriginRef = useRef(proposalOrigin)` — const, line 346
- `const submissionId = useRef(restoredSubmissionId?.trim() || crypto.randomUUID())` — const, line 348
- `const latestDraft = useRef(` — const, line 349
- `const suppressDraftFlush = useRef(false)` — const, line 366
- `const vaultFrozen = useRef(false)` — const, line 367
- `const reloadOnResume = useRef(false)` — const, line 371
- `const draftWrites = useRef<Promise<unknown>>(Promise.resolve())` — const, line 373
- `const isTeachBack = item?.practiceMode === "teach_back"` — const, line 374
- `const teachBackRef = useRef(true)` — const, line 379
- `const teachBackActive = item ? item.practiceMode === "teach_back" : Boolean(restoredTeachBack)` — const, line 384
- `const openedAtMs = useRef(Date.now())` — const, line 391
- `const elapsedSeconds = ()` — const, line 397
- `const attemptProgressRef = useRef<AttemptProgress>("no_draft")` — const, line 410
- `const stepsWorkRef = useRef<string | null>(null)` — const, line 414
- `const onStepsWork = useCallback((workMd: string)` — const, line 415
- `const askState = ():` — const, line 416
- `const steps = stepsWorkRef.current` — const, line 417
- `const askStateRef = useRef(askState)` — const, line 424
- `const panelOn = algoConfig().ask !== null` — const, line 435
- `const openAsk = (options?:` — const, line 452
- `const openAskRef = useRef(openAsk)` — const, line 476
- `const editorSlotRef = useRef<HTMLDivElement>(null)` — const, line 489
- `const belowRef = useRef<HTMLDivElement>(null)` — const, line 490
- `const recomputeEditorMax = useCallback(()` — const, line 493
- `const slot = editorSlotRef.current` — const, line 494
- `const top = slot.getBoundingClientRect().top` — const, line 496
- `const below = belowRef.current?.offsetHeight ?? 0` — const, line 497
- `const keybar = (document.querySelector(".keybar") as HTMLElement | null)?.offsetHeight ?? 36` — const, line 498
- `const next = Math.max(140, Math.floor(window.innerHeight - top - below - keybar - 28))` — const, line 499
- `const sessionMovedRef = useRef(sessionMoved)` — const, line 523
- `const draftSavingDisabled = ()` — const, line 525
- `const saveDraft = useCallback(()` — const, line 528
- `const draft = latestDraft.current` — const, line 529
- `const write = draftWrites.current.catch(()` — const, line 530
- `const flushDraft = useCallback(async ()` — const, line 536
- `const settleDraftForVaultSwitch = useCallback(async ()` — const, line 548
- `const adaptive = algoConfig().adaptiveHints` — const, line 560
- `const answerRef = useRef(answer)` — const, line 562
- `const adaptiveHints = useAdaptiveHints(` — const, line 564
- `const deliveredHints = adaptiveHints.entries.length` — const, line 584
- `const frozen = restoredDisclosure ?` — const, line 615
- `let cancelled = false` — let, line 635
- `const abandonLoad = ()` — const, line 647
- `const recoverOrLoad = async ()` — const, line 654
- `const retryKey = restoredSubmissionId?.trim()` — const, line 655
- `const recovery = await api.recoverPracticeSubmission(` — const, line 658
- `const recoveredItem = await api.getPracticeItem(practiceItemId).catch(()` — const, line 668
- `const routed = await routeAfterAttempt(recovery.result, recoveredItem, abandonLoad)` — const, line 673
- `const recovery = committedAttemptRecovery(error)` — const, line 686
- `const timer = setTimeout(()` — const, line 730
- `const frozen = disclosedRef.current` — const, line 747
- `const practiceReady = item !== null && probeLoadState === "ready"` — const, line 759
- `const probeActive = Boolean(probe?.active && probe.presentationId)` — const, line 760
- `const interactionReady = practiceReady && committedRecovery === null && !vaultChanging && !sessionMoved` — const, line 761
- `const workbenchAvailable = algoConfig().workbench && practiceReady && committedRecovery === null && !probeActive && !isTeachBack && !redo && !primed` — const, line 767
- `const workbenchOffered = workbenchAvailable && !vaultChanging` — const, line 768
- `const wbAutoOpened = useRef(false)` — const, line 777
- `const wbOrigin = planPresentationId ? "plan" : "practice"` — const, line 778
- `const wbEntry = wbOrigin === "plan" ? "plan" : "practice_screen"` — const, line 779
- `const hintsUsedRef = useRef(hintsUsed)` — const, line 783
- `const carriedRef = useRef(` — const, line 787
- `const serveRef = useRef(` — const, line 790
- `const enteringSteps = useRef(false)` — const, line 799
- `const transition = useRef(` — const, line 804
- `const stepsShown = useRef(false)` — const, line 805
- `const beginTransition = useCallback((): number | null` — const, line 806
- `const endTransition = useCallback((token: number)` — const, line 811
- `const handOff = useCallback(async (): Promise<number>` — const, line 814
- `const handOffFailed = useCallback((token: number, heldAt: number | undefined)` — const, line 819
- `const showSteps = useCallback((next: WorkbenchSessionDto)` — const, line 824
- `const openWorkbench = useCallback(async ()` — const, line 828
- `const token = beginTransition()` — const, line 830
- `let heldAt: number | undefined` — let, line 832
- `const result = await api.workbenchOpen(` — const, line 835
- `const resumeWorkbench = useCallback(async (entry: WorkbenchSummaryDto)` — const, line 851
- `const token = beginTransition()` — const, line 852
- `let heldAt: number | undefined` — let, line 854
- `const result = await api.workbenchOpen(` — const, line 859
- `const backToAnswerBox = useCallback((closing: WorkbenchSessionDto | null)` — const, line 873
- `const carried = closing?.carriedHints ?? 0` — const, line 876
- `const earlier = closing?.earlierOpened === true` — const, line 884
- `const refreshWbItemSessions = useCallback(()` — const, line 895
- `const itemId = item.id` — const, line 897
- `const wbItemSessions = item && wbItems.itemId === item.id ? wbItems.sessions : []` — const, line 915
- `const assistPending = workbenchOffered && item !== null && (wbItems.itemId !== item.id || wbItems.state === "pending")` — const, line 917
- `const assistLookupFailed = workbenchOffered && item !== null && wbItems.itemId === item.id && wbItems.state === "failed"` — const, line 918
- `const assistPendingRef = useRef(assistPending)` — const, line 919
- `const wbOpenEntry = wbItemSessions.find((entry)` — const, line 921
- `const stepsMode = workbenchAvailable && wbSession !== null` — const, line 922
- `const bookCarried = bookLeft || wbItemSessions.some((entry)` — const, line 934
- `const bookCounts = bookCarried || pageSeen` — const, line 938
- `const earlierCounted = earlierCountedFor !== null && earlierCountedFor === submissionId.current` — const, line 942
- `const answerHints = hintsUsed + (bookCounts ? 1 : 0)` — const, line 943
- `const onKey = (event: KeyboardEvent)` — const, line 957
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 988
- `const onResize = ()` — const, line 1034
- `const observer = new ResizeObserver(()` — const, line 1036
- `const scorePreview = useMemo(()` — const, line 1044
- `let score = Math.round(Object.values(selfGrade.criterionPoints).reduce((sum, value)` — let, line 1046
- `const fatal = item.rubric.fatalErrors.find((candidate)` — const, line 1049
- `const onYourOwnCheck = item?.activeFollowupKind === "cold_retry" || item?.activeFollowupKind === "certification_cold_probe"` — const, line 1057
- `const intentCheck = (probeActive ? probe?.intentCheck : undefined) ?? item?.intentCheck ?? null` — const, line 1069
- `const asPrinted = useAsPrinted(item?.id)` — const, line 1077
- `const originalPageOffered = !probeActive && !onYourOwnCheck && !isTeachBack && !intentCheck?.locatorsHidden` — const, line 1078
- `function openOriginalPage(target:` — function, line 1079
- `const coldTakeStep = onYourOwnCheck && Boolean(intentCheck?.helpHeader)` — const, line 1090
- `const coldCheck = Boolean(intentCheck?.cold) || onYourOwnCheck` — const, line 1091
- `function practiceAskTarget(extra?: Partial<AskTarget>): AskTarget` — function, line 1095
- `function onFigureEvent(event: PanelFigureEvent)` — function, line 1114
- `function onAskAnswered(answered:` — function, line 1119
- `const refreshHelpRecord = useCallback(()` — const, line 1127
- `const key = submissionId.current` — const, line 1129
- `const shownHintCount = adaptiveHints.entries.length` — const, line 1143
- `const takeWorkedFromAsk = adaptive && !probeActive && !isTeachBack ? (level: 4 | 5)` — const, line 1150
- `const askReturnFocus = useRef<HTMLElement | null>(null)` — const, line 1155
- `function closeDockedAsk()` — function, line 1159
- `const back = askReturnFocus.current` — const, line 1161
- `function onEarlierOpened()` — function, line 1166
- `const key = submissionId.current` — const, line 1168
- `function revealHint()` — function, line 1177
- `function revealAuthoredHint()` — function, line 1208
- `async function revealAuthoredAt(index: number): Promise<string | null>` — function, line 1224
- `const recorded = await Promise.resolve(api.recordHintReveal?.(` — const, line 1233
- `async function stopDiagnosing()` — function, line 1243
- `async function routeAfterAttempt( result: AttemptResultDto, recoveredItem: PracticeItemDetail | null = item, cancelled: ()` — function, line 1256
- `const learningObjectId = recoveredItem?.learningObjectId ?? result.learningObjectId` — const, line 1262
- `const learningObjectTitle = recoveredItem?.learningObjectTitle ?? result.learningObjectId` — const, line 1263
- `const next = await api.getNextProbeItem(learningObjectId)` — const, line 1275
- `function pressStuck()` — function, line 1296
- `const editor = editorSlotRef.current?.querySelector<HTMLElement>("[role=textbox]")` — const, line 1299
- `async function freezeBeforeSelfGrade(itemId: string, key: string): Promise<void>` — function, line 1306
- `const frozen =` — const, line 1308
- `async function submit(gradeOverride?: SelfGradeInputDto)` — function, line 1327
- `const submittedItemId = item.id` — const, line 1329
- `const submittedKey = submissionId.current` — const, line 1330
- `const grade = gradeOverride ?? selfGrade` — const, line 1333
- `const emptyStuck = stuck && !answer.trim() && !whyLine.trim() && !redo` — const, line 1336
- `const validation = emptyStuck ?` — const, line 1349
- `const result = await api.submitAttempt(` — const, line 1359
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 1408
- `const recovery = committedAttemptRecovery(error)` — const, line 1411
- `const command = getCommandError(error)` — const, line 1420
- `async function dontKnow()` — function, line 1439
- `const submittedItemId = item.id` — const, line 1441
- `const submittedKey = submissionId.current` — const, line 1442
- `const result = await api.submitDontKnow(` — const, line 1447
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 1465
- `const recovery = committedAttemptRecovery(error)` — const, line 1468
- `async function skip()` — function, line 1479
- `const skippedIdentity =` — const, line 1481
- `async function acknowledgeCheckpoint(practiceItemId: string, expectedSubmissionId: string): Promise<boolean>` — function, line 1495
- `const result = await api.acknowledgePracticeSubmission(` — const, line 1498
- `const loadError = itemLoadError ?? probeLoadError` — const, line 1512
- `const diagnostic = committedRecovery.attemptType === "diagnostic_probe" || probeActive` — const, line 1538
- `const dockedPanel = dockedAsk && panelOn && !stepsMode ? ( <AskOverlay variant="docked" target=` — const, line 1623
- `const on = answerConfidence === level` — const, line 2136
- `const locked = submitting || selfGradeVisible` — const, line 2137
- `function TeachBackConversation(` — function, line 2439
- `const startedRef = useRef(false)` — const, line 2468
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 2469
- `const lastRole = turns.length > 0 ? turns[turns.length - 1].role : null` — const, line 2471
- `const needsText = turns.length === 0 || lastRole === "ai"` — const, line 2475
- `const start = useCallback(()` — const, line 2477
- `const node = transcriptRef.current` — const, line 2507
- `async function send(finish = false)` — function, line 2511
- `const text = input.trim()` — const, line 2513
- `const result = await api.submitTeachBackTurn(` — const, line 2519
- `const onKey = (event: KeyboardEvent)` — const, line 2545
- `const submitLabel = turns.length === 0 ? "Start teaching" : lastRole === "learner" ? "Continue" : "Send answer"` — const, line 2556
- `const questionsAnswered = asked > 0 && lastRole === "learner"` — const, line 2558
- `function gradeFromParts( item: PracticeItemDetail, base: SelfGradeInputDto, got: (criterionId: string)` — function, line 2675
- `function PlainSelfGrade(` — function, line 2694
- `const criteria = item.rubric?.criteria ?? []` — const, line 2731
- `const fullAnswer = expectedAnswerText(item.expectedAnswer).trim()` — const, line 2732
- `const exposure = useAnswerExposure(exposureKey, showFullAnswer && Boolean(fullAnswer), recordDisplay)` — const, line 2737
- `function SelfGradePanel(` — function, line 2793
- `const awarded = value.criterionPoints[criterion.id] ?? 0` — const, line 2824
- `const docked = awarded < criterion.points` — const, line 2825
- `const points = Number(event.target.value)` — const, line 2841
- `const stillDocked = points < criterion.points` — const, line 2842
- `function CriterionErrorPicker(` — function, line 2906
- `const selected = new Set( (value.errorAttributions ?? []).filter((a)` — const, line 2917
- `const toggle = (errorType: string)` — const, line 2920
- `const list = value.errorAttributions ?? []` — const, line 2921
- `const exists = list.some((a)` — const, line 2922
- `const relevant = candidates.filter((c)` — const, line 2930
- `const others = candidates.filter((c)` — const, line 2931
- `const chip = (c: CandidateErrorTypeDto)` — const, line 2932
- `function prunedAttributions(item: PracticeItemDetail, grade: SelfGradeInputDto): SelfGradeErrorAttributionDto[]` — function, line 2969
- `const docked = new Set( (item.rubric?.criteria ?? []) .filter((criterion)` — const, line 2970
- `const NON_RECORDING_ATTEMPT_TYPES: ReadonlySet<AttemptType> = new Set(["guided_walkthrough", "skip"])` — const, line 2981
- `function defaultAttemptType(allowed: readonly AttemptType[]): AttemptType` — function, line 2983
- `function composeRedoAnswer(prefix: string, redoText: string): string` — function, line 2996
- `const suffix = redoText.replace(/^[ \t]+/, "")` — const, line 2997
- `function recordHintReveal(input: Parameters<typeof api.recordHintReveal>[0]): void` — function, line 3006
- `const parts: string[] = []` — const, line 3032
- `const worked = (entries ?? []).filter((entry)` — const, line 3037
- `const plain = Math.max(0, hints - worked.length)` — const, line 3038
- `let clientOnly: number` — let, line 3051
- `let clientWorked: number[] = []` — let, line 3052
- `const listedIds = new Set(server.items.map((entry)` — const, line 3057
- `const unlisted = entries.filter((entry)` — const, line 3058
- `const serverHints = server.items.filter((entry)` — const, line 3062
- `const listed = new Set<string>()` — const, line 3066
- `function chooseAttemptType(allowed: readonly AttemptType[], hintsUsed: number): AttemptType` — function, line 3097
- `const allows = (type: AttemptType)` — const, line 3098
- `function validateSelfGrade( item: PracticeItemDetail, value: SelfGradeInputDto, required: boolean ): Record<string, string>` — function, line 3103
- `const errors: Record<string, string> =` — const, line 3109
- `const points = value.criterionPoints[criterion.id]` — const, line 3111

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `PracticeScreen`; references `PracticeScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AttemptProgress`, `AttemptResultDto`, `AttemptType`, `CandidateErrorTypeDto`, `DifficultyRating`, `FirstHintProgress`, `GuidedRedoDto`, `HelpRecordDto`, `PracticeItemDetail`, `ProbeBlockEndDto`, `ProbeContractDto`, `RubricCriterionDto`, `SelfGradeDisclosureDto`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SessionSnapshot`, `TeachBackStateDto`, `TeachBackTurnDto`, `WorkbenchSessionDto`, `WorkbenchSummaryDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `STUCK_PROMPT_TEXT`, `algoConfig`, `masteryTone`, `setAdaptiveHelpStyle`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export; imports `expectedAnswerText`, `simplePracticeFeedback`
- [[Reference/Desktop/TypeScript/app/useCloseWithFlush|src/app/useCloseWithFlush.ts]] — import-or-re-export; imports `useCloseWithFlush`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `registerVaultDraft`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export; imports `AS_PRINTED_COPY`, `AsPrinted`, `OriginalPageLink`, `printedPageLabel`, `useAsPrinted`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `CardControls`
- [[Reference/Desktop/TypeScript/components/DockedAsk|src/components/DockedAsk.tsx]] — import-or-re-export; imports `DockedAsk`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `DetailsToggle`, `PrimaryAction`, `QuietAction`, `VoicePanel`, `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export; imports `PANEL_FIGURE_COPY`, `PanelFigureEvent`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export; imports `ASK_COPY`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`, `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `EntityLink`, `KeyBar`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/MathLiveEditor|src/render/MathLiveEditor.tsx]] — import-or-re-export; imports `MathLiveEditor`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export; imports `AnswerWaiting`
- [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|src/screens/feedback/answerExposure.ts]] — import-or-re-export; imports `RecordDisplay`, `useAnswerExposure`
- [[Reference/Desktop/TypeScript/screens/practice/DifficultyRatingTap|src/screens/practice/DifficultyRatingTap.tsx]] — import-or-re-export; imports `DifficultyRatingTap`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export; imports `HintPanel`
- [[Reference/Desktop/TypeScript/screens/practice/WhyThisItem|src/screens/practice/WhyThisItem.tsx]] — import-or-re-export; imports `WhyThisItem`
- [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]] — import-or-re-export; imports `useAdaptiveHints`
- [[Reference/Desktop/TypeScript/screens/practice/useFirstHintProgress|src/screens/practice/useFirstHintProgress.ts]] — import-or-re-export; imports `useFirstHintProgress`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export; imports `Workbench`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.workbench.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.workbench.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.ownerCapture1025.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.ownerCapture1025.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.intentCheck.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.intentCheck.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.hintTelemetry.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.hintTelemetry.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.firstHintRestore.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.firstHintRestore.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_diagnostic.py](../../../../../../tests/test_sidecar_diagnostic.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/PracticeScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
