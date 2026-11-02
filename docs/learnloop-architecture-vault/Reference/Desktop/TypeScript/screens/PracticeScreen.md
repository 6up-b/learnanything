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
source_commit: "afb17672c627b4f4422c149ac63dd2addef98a9b"
source_commit_timestamp: "2026-11-01T20:23:43-05:00"
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
| Source lines | 3114 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `afb17672c627b4f4422c149ac63dd2addef98a9b` |
| Commit timestamp | `2026-11-01T20:23:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]]

## Public API

- `export function PracticeScreen(` — function, line 131
- `export function helpRecordLine(` — function, line 3012

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
- `const originalPageOpen = useRef(false)` — const, line 265
- `const stuckPrompt = algoConfig().stuckPrompt` — const, line 271
- `const ratingTap = algoConfig().ratingTap` — const, line 289
- `const firstHint = useFirstHintProgress(` — const, line 296
- `const firstHintRef = useRef(firstHint.value)` — const, line 298
- `const hintSeenRef = useRef(hintSeen)` — const, line 305
- `const seeHint = useCallback(()` — const, line 307
- `const simple = simplePracticeFeedback()` — const, line 322
- `const disclosedRef = useRef(disclosed)` — const, line 335
- `const mountedRef = useRef(true)` — const, line 341
- `const proposalOriginRef = useRef(proposalOrigin)` — const, line 343
- `const submissionId = useRef(restoredSubmissionId?.trim() || crypto.randomUUID())` — const, line 345
- `const latestDraft = useRef(` — const, line 346
- `const suppressDraftFlush = useRef(false)` — const, line 363
- `const vaultFrozen = useRef(false)` — const, line 364
- `const reloadOnResume = useRef(false)` — const, line 368
- `const draftWrites = useRef<Promise<unknown>>(Promise.resolve())` — const, line 370
- `const isTeachBack = item?.practiceMode === "teach_back"` — const, line 371
- `const teachBackRef = useRef(true)` — const, line 376
- `const teachBackActive = item ? item.practiceMode === "teach_back" : Boolean(restoredTeachBack)` — const, line 381
- `const openedAtMs = useRef(Date.now())` — const, line 388
- `const elapsedSeconds = ()` — const, line 394
- `const attemptProgressRef = useRef<AttemptProgress>("no_draft")` — const, line 407
- `const stepsWorkRef = useRef<string | null>(null)` — const, line 411
- `const onStepsWork = useCallback((workMd: string)` — const, line 412
- `const askState = ():` — const, line 413
- `const steps = stepsWorkRef.current` — const, line 414
- `const askStateRef = useRef(askState)` — const, line 421
- `const panelOn = algoConfig().ask !== null` — const, line 432
- `const openAsk = (options?:` — const, line 449
- `const openAskRef = useRef(openAsk)` — const, line 473
- `const editorSlotRef = useRef<HTMLDivElement>(null)` — const, line 486
- `const belowRef = useRef<HTMLDivElement>(null)` — const, line 487
- `const recomputeEditorMax = useCallback(()` — const, line 490
- `const slot = editorSlotRef.current` — const, line 491
- `const top = slot.getBoundingClientRect().top` — const, line 493
- `const below = belowRef.current?.offsetHeight ?? 0` — const, line 494
- `const keybar = (document.querySelector(".keybar") as HTMLElement | null)?.offsetHeight ?? 36` — const, line 495
- `const next = Math.max(140, Math.floor(window.innerHeight - top - below - keybar - 28))` — const, line 496
- `const draftSavingDisabled = ()` — const, line 519
- `const saveDraft = useCallback(()` — const, line 522
- `const draft = latestDraft.current` — const, line 523
- `const write = draftWrites.current.catch(()` — const, line 524
- `const flushDraft = useCallback(async ()` — const, line 530
- `const settleDraftForVaultSwitch = useCallback(async ()` — const, line 542
- `const adaptive = algoConfig().adaptiveHints` — const, line 554
- `const answerRef = useRef(answer)` — const, line 556
- `const adaptiveHints = useAdaptiveHints(` — const, line 558
- `const deliveredHints = adaptiveHints.entries.length` — const, line 578
- `const frozen = restoredDisclosure ?` — const, line 609
- `let cancelled = false` — let, line 629
- `const abandonLoad = ()` — const, line 641
- `const recoverOrLoad = async ()` — const, line 648
- `const retryKey = restoredSubmissionId?.trim()` — const, line 649
- `const recovery = await api.recoverPracticeSubmission(` — const, line 652
- `const recoveredItem = await api.getPracticeItem(practiceItemId).catch(()` — const, line 662
- `const routed = await routeAfterAttempt(recovery.result, recoveredItem, abandonLoad)` — const, line 667
- `const recovery = committedAttemptRecovery(error)` — const, line 680
- `const timer = setTimeout(()` — const, line 724
- `const frozen = disclosedRef.current` — const, line 741
- `const practiceReady = item !== null && probeLoadState === "ready"` — const, line 753
- `const probeActive = Boolean(probe?.active && probe.presentationId)` — const, line 754
- `const interactionReady = practiceReady && committedRecovery === null && !vaultChanging` — const, line 755
- `const workbenchAvailable = algoConfig().workbench && practiceReady && committedRecovery === null && !probeActive && !isTeachBack && !redo && !primed` — const, line 761
- `const workbenchOffered = workbenchAvailable && !vaultChanging` — const, line 762
- `const wbAutoOpened = useRef(false)` — const, line 771
- `const wbOrigin = planPresentationId ? "plan" : "practice"` — const, line 772
- `const wbEntry = wbOrigin === "plan" ? "plan" : "practice_screen"` — const, line 773
- `const hintsUsedRef = useRef(hintsUsed)` — const, line 777
- `const carriedRef = useRef(` — const, line 781
- `const serveRef = useRef(` — const, line 784
- `const enteringSteps = useRef(false)` — const, line 793
- `const transition = useRef(` — const, line 798
- `const stepsShown = useRef(false)` — const, line 799
- `const beginTransition = useCallback((): number | null` — const, line 800
- `const endTransition = useCallback((token: number)` — const, line 805
- `const handOff = useCallback(async (): Promise<number>` — const, line 808
- `const handOffFailed = useCallback((token: number, heldAt: number | undefined)` — const, line 813
- `const showSteps = useCallback((next: WorkbenchSessionDto)` — const, line 818
- `const openWorkbench = useCallback(async ()` — const, line 822
- `const token = beginTransition()` — const, line 824
- `let heldAt: number | undefined` — let, line 826
- `const result = await api.workbenchOpen(` — const, line 829
- `const resumeWorkbench = useCallback(async (entry: WorkbenchSummaryDto)` — const, line 845
- `const token = beginTransition()` — const, line 846
- `let heldAt: number | undefined` — let, line 848
- `const result = await api.workbenchOpen(` — const, line 853
- `const backToAnswerBox = useCallback((closing: WorkbenchSessionDto | null)` — const, line 867
- `const carried = closing?.carriedHints ?? 0` — const, line 870
- `const earlier = closing?.earlierOpened === true` — const, line 878
- `const refreshWbItemSessions = useCallback(()` — const, line 889
- `const itemId = item.id` — const, line 891
- `const wbItemSessions = item && wbItems.itemId === item.id ? wbItems.sessions : []` — const, line 909
- `const assistPending = workbenchOffered && item !== null && (wbItems.itemId !== item.id || wbItems.state === "pending")` — const, line 911
- `const assistLookupFailed = workbenchOffered && item !== null && wbItems.itemId === item.id && wbItems.state === "failed"` — const, line 912
- `const assistPendingRef = useRef(assistPending)` — const, line 913
- `const wbOpenEntry = wbItemSessions.find((entry)` — const, line 915
- `const stepsMode = workbenchAvailable && wbSession !== null` — const, line 916
- `const bookCarried = bookLeft || wbItemSessions.some((entry)` — const, line 928
- `const bookCounts = bookCarried || pageSeen` — const, line 932
- `const earlierCounted = earlierCountedFor !== null && earlierCountedFor === submissionId.current` — const, line 936
- `const answerHints = hintsUsed + (bookCounts ? 1 : 0)` — const, line 937
- `const onKey = (event: KeyboardEvent)` — const, line 951
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 982
- `const onResize = ()` — const, line 1028
- `const observer = new ResizeObserver(()` — const, line 1030
- `const scorePreview = useMemo(()` — const, line 1038
- `let score = Math.round(Object.values(selfGrade.criterionPoints).reduce((sum, value)` — let, line 1040
- `const fatal = item.rubric.fatalErrors.find((candidate)` — const, line 1043
- `const onYourOwnCheck = item?.activeFollowupKind === "cold_retry" || item?.activeFollowupKind === "certification_cold_probe"` — const, line 1051
- `const intentCheck = (probeActive ? probe?.intentCheck : undefined) ?? item?.intentCheck ?? null` — const, line 1063
- `const asPrinted = useAsPrinted(item?.id)` — const, line 1071
- `const originalPageOffered = !probeActive && !onYourOwnCheck && !isTeachBack && !intentCheck?.locatorsHidden` — const, line 1072
- `function openOriginalPage(target:` — function, line 1073
- `const coldTakeStep = onYourOwnCheck && Boolean(intentCheck?.helpHeader)` — const, line 1084
- `const coldCheck = Boolean(intentCheck?.cold) || onYourOwnCheck` — const, line 1085
- `function practiceAskTarget(extra?: Partial<AskTarget>): AskTarget` — function, line 1089
- `function onFigureEvent(event: PanelFigureEvent)` — function, line 1108
- `function onAskAnswered(answered:` — function, line 1113
- `const refreshHelpRecord = useCallback(()` — const, line 1121
- `const key = submissionId.current` — const, line 1123
- `const shownHintCount = adaptiveHints.entries.length` — const, line 1137
- `const takeWorkedFromAsk = adaptive && !probeActive && !isTeachBack ? (level: 4 | 5)` — const, line 1144
- `const askReturnFocus = useRef<HTMLElement | null>(null)` — const, line 1149
- `function closeDockedAsk()` — function, line 1153
- `const back = askReturnFocus.current` — const, line 1155
- `function onEarlierOpened()` — function, line 1160
- `const key = submissionId.current` — const, line 1162
- `function revealHint()` — function, line 1171
- `function revealAuthoredHint()` — function, line 1202
- `async function revealAuthoredAt(index: number): Promise<string | null>` — function, line 1218
- `const recorded = await Promise.resolve(api.recordHintReveal?.(` — const, line 1227
- `async function stopDiagnosing()` — function, line 1237
- `async function routeAfterAttempt( result: AttemptResultDto, recoveredItem: PracticeItemDetail | null = item, cancelled: ()` — function, line 1250
- `const learningObjectId = recoveredItem?.learningObjectId ?? result.learningObjectId` — const, line 1256
- `const learningObjectTitle = recoveredItem?.learningObjectTitle ?? result.learningObjectId` — const, line 1257
- `const next = await api.getNextProbeItem(learningObjectId)` — const, line 1269
- `function pressStuck()` — function, line 1290
- `const editor = editorSlotRef.current?.querySelector<HTMLElement>("[role=textbox]")` — const, line 1293
- `async function freezeBeforeSelfGrade(itemId: string, key: string): Promise<void>` — function, line 1300
- `const frozen =` — const, line 1302
- `async function submit(gradeOverride?: SelfGradeInputDto)` — function, line 1321
- `const submittedItemId = item.id` — const, line 1323
- `const submittedKey = submissionId.current` — const, line 1324
- `const grade = gradeOverride ?? selfGrade` — const, line 1327
- `const emptyStuck = stuck && !answer.trim() && !whyLine.trim() && !redo` — const, line 1330
- `const validation = emptyStuck ?` — const, line 1343
- `const result = await api.submitAttempt(` — const, line 1353
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 1402
- `const recovery = committedAttemptRecovery(error)` — const, line 1405
- `const command = getCommandError(error)` — const, line 1414
- `async function dontKnow()` — function, line 1433
- `const submittedItemId = item.id` — const, line 1435
- `const submittedKey = submissionId.current` — const, line 1436
- `const result = await api.submitDontKnow(` — const, line 1441
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 1459
- `const recovery = committedAttemptRecovery(error)` — const, line 1462
- `async function skip()` — function, line 1473
- `const skippedIdentity =` — const, line 1475
- `async function acknowledgeCheckpoint(practiceItemId: string, expectedSubmissionId: string): Promise<boolean>` — function, line 1489
- `const result = await api.acknowledgePracticeSubmission(` — const, line 1492
- `const loadError = itemLoadError ?? probeLoadError` — const, line 1506
- `const diagnostic = committedRecovery.attemptType === "diagnostic_probe" || probeActive` — const, line 1532
- `const dockedPanel = dockedAsk && panelOn && !stepsMode ? ( <AskOverlay variant="docked" target=` — const, line 1617
- `const on = answerConfidence === level` — const, line 2130
- `const locked = submitting || selfGradeVisible` — const, line 2131
- `function TeachBackConversation(` — function, line 2433
- `const startedRef = useRef(false)` — const, line 2462
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 2463
- `const lastRole = turns.length > 0 ? turns[turns.length - 1].role : null` — const, line 2465
- `const needsText = turns.length === 0 || lastRole === "ai"` — const, line 2469
- `const start = useCallback(()` — const, line 2471
- `const node = transcriptRef.current` — const, line 2501
- `async function send(finish = false)` — function, line 2505
- `const text = input.trim()` — const, line 2507
- `const result = await api.submitTeachBackTurn(` — const, line 2513
- `const onKey = (event: KeyboardEvent)` — const, line 2539
- `const submitLabel = turns.length === 0 ? "Start teaching" : lastRole === "learner" ? "Continue" : "Send answer"` — const, line 2550
- `const questionsAnswered = asked > 0 && lastRole === "learner"` — const, line 2552
- `function gradeFromParts( item: PracticeItemDetail, base: SelfGradeInputDto, got: (criterionId: string)` — function, line 2669
- `function PlainSelfGrade(` — function, line 2688
- `const criteria = item.rubric?.criteria ?? []` — const, line 2725
- `const fullAnswer = expectedAnswerText(item.expectedAnswer).trim()` — const, line 2726
- `const exposure = useAnswerExposure(exposureKey, showFullAnswer && Boolean(fullAnswer), recordDisplay)` — const, line 2731
- `function SelfGradePanel(` — function, line 2787
- `const awarded = value.criterionPoints[criterion.id] ?? 0` — const, line 2818
- `const docked = awarded < criterion.points` — const, line 2819
- `const points = Number(event.target.value)` — const, line 2835
- `const stillDocked = points < criterion.points` — const, line 2836
- `function CriterionErrorPicker(` — function, line 2900
- `const selected = new Set( (value.errorAttributions ?? []).filter((a)` — const, line 2911
- `const toggle = (errorType: string)` — const, line 2914
- `const list = value.errorAttributions ?? []` — const, line 2915
- `const exists = list.some((a)` — const, line 2916
- `const relevant = candidates.filter((c)` — const, line 2924
- `const others = candidates.filter((c)` — const, line 2925
- `const chip = (c: CandidateErrorTypeDto)` — const, line 2926
- `function prunedAttributions(item: PracticeItemDetail, grade: SelfGradeInputDto): SelfGradeErrorAttributionDto[]` — function, line 2963
- `const docked = new Set( (item.rubric?.criteria ?? []) .filter((criterion)` — const, line 2964
- `const NON_RECORDING_ATTEMPT_TYPES: ReadonlySet<AttemptType> = new Set(["guided_walkthrough", "skip"])` — const, line 2975
- `function defaultAttemptType(allowed: readonly AttemptType[]): AttemptType` — function, line 2977
- `function composeRedoAnswer(prefix: string, redoText: string): string` — function, line 2990
- `const suffix = redoText.replace(/^[ \t]+/, "")` — const, line 2991
- `function recordHintReveal(input: Parameters<typeof api.recordHintReveal>[0]): void` — function, line 3000
- `const parts: string[] = []` — const, line 3026
- `const worked = (entries ?? []).filter((entry)` — const, line 3031
- `const plain = Math.max(0, hints - worked.length)` — const, line 3032
- `let clientOnly: number` — let, line 3045
- `let clientWorked: number[] = []` — let, line 3046
- `const listedIds = new Set(server.items.map((entry)` — const, line 3051
- `const unlisted = entries.filter((entry)` — const, line 3052
- `const serverHints = server.items.filter((entry)` — const, line 3056
- `const listed = new Set<string>()` — const, line 3060
- `function chooseAttemptType(allowed: readonly AttemptType[], hintsUsed: number): AttemptType` — function, line 3091
- `const allows = (type: AttemptType)` — const, line 3092
- `function validateSelfGrade( item: PracticeItemDetail, value: SelfGradeInputDto, required: boolean ): Record<string, string>` — function, line 3097
- `const errors: Record<string, string> =` — const, line 3103
- `const points = value.criterionPoints[criterion.id]` — const, line 3105

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
