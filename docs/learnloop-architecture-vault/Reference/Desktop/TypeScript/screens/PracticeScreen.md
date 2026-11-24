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
| Source lines | 3170 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]]

## Public API

- `export function PracticeScreen(` — function, line 135
- `export function helpRecordLine(` — function, line 3059

## Internal implementation anchors

- `const WORK_IN_STEPS_KEY = "ll.workbench.workInSteps"` — const, line 56
- `function rememberedWorkInSteps(): boolean` — function, line 57
- `function rememberWorkInSteps(on: boolean): void` — function, line 64
- `type CommittedAttemptRecovery =` — type, line 73
- `type PracticeCheckpointIdentity =` — type, line 79
- `function committedAttemptRecovery(error: unknown): CommittedAttemptRecovery | null` — function, line 84
- `const command = getCommandError(error)` — const, line 85
- `const details = command.details as` — const, line 89
- `const attemptId = details.attempt_id ?? details.attemptId` — const, line 95
- `const attemptType = details.attempt_type ?? details.attemptType` — const, line 97
- `function activeProbeContract(contract: ProbeContractDto): ProbeContractDto | null` — function, line 108
- `const restrictions = contract.restrictions` — const, line 118
- `const originalPageOpen = useRef(false)` — const, line 276
- `const ratingTap = algoConfig().ratingTap` — const, line 299
- `const firstHint = useFirstHintProgress(` — const, line 306
- `const firstHintRef = useRef(firstHint.value)` — const, line 308
- `const hintSeenRef = useRef(hintSeen)` — const, line 315
- `const seeHint = useCallback(()` — const, line 317
- `const simple = simplePracticeFeedback()` — const, line 332
- `const disclosedRef = useRef(disclosed)` — const, line 345
- `const mountedRef = useRef(true)` — const, line 351
- `const proposalOriginRef = useRef(proposalOrigin)` — const, line 353
- `const submissionId = useRef(restoredSubmissionId?.trim() || crypto.randomUUID())` — const, line 355
- `const latestDraft = useRef(` — const, line 356
- `const suppressDraftFlush = useRef(false)` — const, line 373
- `const vaultFrozen = useRef(false)` — const, line 374
- `const reloadOnResume = useRef(false)` — const, line 378
- `const draftWrites = useRef<Promise<unknown>>(Promise.resolve())` — const, line 384
- `const isTeachBack = item?.practiceMode === "teach_back"` — const, line 385
- `const teachBackRef = useRef(true)` — const, line 390
- `const teachBackActive = item ? item.practiceMode === "teach_back" : Boolean(restoredTeachBack)` — const, line 395
- `const openedAtMs = useRef(Date.now())` — const, line 402
- `const elapsedSeconds = ()` — const, line 408
- `const activeClock = useAttemptClock()` — const, line 416
- `const attemptProgressRef = useRef<AttemptProgress>("no_draft")` — const, line 425
- `const stepsWorkRef = useRef<string | null>(null)` — const, line 429
- `const onStepsWork = useCallback((workMd: string)` — const, line 430
- `const askState = ():` — const, line 431
- `const steps = stepsWorkRef.current` — const, line 432
- `const askStateRef = useRef(askState)` — const, line 439
- `const panelOn = algoConfig().ask !== null` — const, line 450
- `const openAsk = (options?:` — const, line 467
- `const openAskRef = useRef(openAsk)` — const, line 491
- `const editorSlotRef = useRef<HTMLDivElement>(null)` — const, line 505
- `const belowRef = useRef<HTMLDivElement>(null)` — const, line 506
- `const recomputeEditorMax = useCallback(()` — const, line 509
- `const slot = editorSlotRef.current` — const, line 510
- `const below = belowRef.current?.offsetHeight ?? 0` — const, line 512
- `const sessionMovedRef = useRef(sessionMoved)` — const, line 536
- `const draftSavingDisabled = ()` — const, line 538
- `const saveDraft = useCallback(()` — const, line 541
- `const draft = latestDraft.current` — const, line 542
- `const write = draftWrites.current.catch(()` — const, line 543
- `const flushDraft = useCallback(async ()` — const, line 549
- `const settleDraftForVaultSwitch = useCallback(async ()` — const, line 561
- `const adaptive = algoConfig().adaptiveHints` — const, line 573
- `const answerRef = useRef(answer)` — const, line 575
- `const adaptiveHints = useAdaptiveHints(` — const, line 577
- `const deliveredHints = adaptiveHints.entries.length` — const, line 597
- `const frozen = restoredDisclosure ?` — const, line 628
- `let cancelled = false` — let, line 648
- `const abandonLoad = ()` — const, line 660
- `const recoverOrLoad = async ()` — const, line 667
- `const retryKey = restoredSubmissionId?.trim()` — const, line 668
- `const recovery = await api.recoverPracticeSubmission(` — const, line 671
- `const recoveredItem = await api.getPracticeItem(practiceItemId).catch(()` — const, line 681
- `const routed = await routeAfterAttempt(recovery.result, recoveredItem, abandonLoad)` — const, line 686
- `const recovery = committedAttemptRecovery(error)` — const, line 699
- `const timer = setTimeout(()` — const, line 743
- `const frozen = disclosedRef.current` — const, line 760
- `const practiceReady = item !== null && probeLoadState === "ready"` — const, line 772
- `const probeActive = Boolean(probe?.active && probe.presentationId)` — const, line 773
- `const interactionReady = practiceReady && committedRecovery === null && !vaultChanging && !sessionMoved` — const, line 775
- `const workbenchAvailable = algoConfig().workbench && practiceReady && committedRecovery === null && !probeActive && !isTeachBack && !redo && !primed` — const, line 781
- `const workbenchOffered = workbenchAvailable && !vaultChanging` — const, line 782
- `const wbAutoOpened = useRef(false)` — const, line 791
- `const wbOrigin = planPresentationId ? "plan" : "practice"` — const, line 792
- `const wbEntry = wbOrigin === "plan" ? "plan" : "practice_screen"` — const, line 793
- `const hintsUsedRef = useRef(hintsUsed)` — const, line 797
- `const carriedRef = useRef(` — const, line 801
- `const serveRef = useRef(` — const, line 804
- `const enteringSteps = useRef(false)` — const, line 813
- `const transition = useRef(` — const, line 818
- `const stepsShown = useRef(false)` — const, line 819
- `const beginTransition = useCallback((): number | null` — const, line 820
- `const endTransition = useCallback((token: number)` — const, line 825
- `const handOff = useCallback(async (): Promise<number>` — const, line 828
- `const handOffFailed = useCallback((token: number, heldAt: number | undefined)` — const, line 833
- `const showSteps = useCallback((next: WorkbenchSessionDto)` — const, line 838
- `const openWorkbench = useCallback(async ()` — const, line 842
- `const token = beginTransition()` — const, line 844
- `let heldAt: number | undefined` — let, line 846
- `const result = await api.workbenchOpen(` — const, line 849
- `const resumeWorkbench = useCallback(async (entry: WorkbenchSummaryDto)` — const, line 865
- `const token = beginTransition()` — const, line 866
- `let heldAt: number | undefined` — let, line 868
- `const result = await api.workbenchOpen(` — const, line 873
- `const backToAnswerBox = useCallback((closing: WorkbenchSessionDto | null)` — const, line 887
- `const carried = closing?.carriedHints ?? 0` — const, line 890
- `const earlier = closing?.earlierOpened === true` — const, line 898
- `const refreshWbItemSessions = useCallback(()` — const, line 909
- `const itemId = item.id` — const, line 911
- `const wbItemSessions = item && wbItems.itemId === item.id ? wbItems.sessions : []` — const, line 929
- `const assistPending = workbenchOffered && item !== null && (wbItems.itemId !== item.id || wbItems.state === "pending")` — const, line 931
- `const assistLookupFailed = workbenchOffered && item !== null && wbItems.itemId === item.id && wbItems.state === "failed"` — const, line 932
- `const assistPendingRef = useRef(assistPending)` — const, line 933
- `const wbOpenEntry = wbItemSessions.find((entry)` — const, line 935
- `const stepsMode = workbenchAvailable && wbSession !== null` — const, line 936
- `const bookCarried = bookLeft || wbItemSessions.some((entry)` — const, line 948
- `const bookCounts = bookCarried || pageSeen` — const, line 952
- `const earlierCounted = earlierCountedFor !== null && earlierCountedFor === submissionId.current` — const, line 956
- `const answerHints = hintsUsed + (bookCounts ? 1 : 0)` — const, line 957
- `const onKey = (event: KeyboardEvent)` — const, line 981
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 1012
- `const onResize = ()` — const, line 1055
- `const observer = new ResizeObserver(()` — const, line 1057
- `const scorePreview = useMemo(()` — const, line 1065
- `let score = Math.round(Object.values(selfGrade.criterionPoints).reduce((sum, value)` — let, line 1067
- `const fatal = item.rubric.fatalErrors.find((candidate)` — const, line 1070
- `const onYourOwnCheck = item?.activeFollowupKind === "cold_retry" || item?.activeFollowupKind === "certification_cold_probe"` — const, line 1078
- `const intentCheck = (probeActive ? probe?.intentCheck : undefined) ?? item?.intentCheck ?? null` — const, line 1090
- `const asPrinted = useAsPrinted(item?.id)` — const, line 1098
- `const originalPageOffered = !probeActive && !onYourOwnCheck && !isTeachBack && !intentCheck?.locatorsHidden` — const, line 1099
- `function openOriginalPage(target:` — function, line 1100
- `const coldTakeStep = onYourOwnCheck && Boolean(intentCheck?.helpHeader)` — const, line 1111
- `const coldCheck = Boolean(intentCheck?.cold) || onYourOwnCheck` — const, line 1112
- `function practiceAskTarget(extra?: Partial<AskTarget>): AskTarget` — function, line 1116
- `function onFigureEvent(event: PanelFigureEvent)` — function, line 1135
- `function onAskAnswered(answered:` — function, line 1140
- `const refreshHelpRecord = useCallback(()` — const, line 1148
- `const key = submissionId.current` — const, line 1150
- `const shownHintCount = adaptiveHints.entries.length` — const, line 1164
- `const takeWorkedFromAsk = adaptive && !probeActive && !isTeachBack ? (level: 4 | 5)` — const, line 1171
- `const askReturnFocus = useRef<HTMLElement | null>(null)` — const, line 1176
- `function closeDockedAsk()` — function, line 1180
- `const back = askReturnFocus.current` — const, line 1182
- `function onEarlierOpened()` — function, line 1187
- `const key = submissionId.current` — const, line 1189
- `function revealHint()` — function, line 1198
- `function revealAuthoredHint()` — function, line 1229
- `async function revealAuthoredAt(index: number): Promise<string | null>` — function, line 1245
- `const recorded = await Promise.resolve(api.recordHintReveal?.(` — const, line 1254
- `async function stopDiagnosing()` — function, line 1264
- `const stopped = await api.stopProbeDiagnosing(item.id)` — const, line 1267
- `const askTutor = ()` — const, line 1271
- `async function routeAfterAttempt( result: AttemptResultDto, recoveredItem: PracticeItemDetail | null = item, cancelled: ()` — function, line 1284
- `const learningObjectId = recoveredItem?.learningObjectId ?? result.learningObjectId` — const, line 1290
- `const learningObjectTitle = recoveredItem?.learningObjectTitle ?? result.learningObjectId` — const, line 1291
- `const next = await api.getNextProbeItem(learningObjectId)` — const, line 1303
- `function pressStuck()` — function, line 1324
- `const editor = editorSlotRef.current?.querySelector<HTMLElement>("[role=textbox]")` — const, line 1327
- `async function freezeBeforeSelfGrade(itemId: string, key: string): Promise<void>` — function, line 1334
- `const frozen =` — const, line 1336
- `async function submit(gradeOverride?: SelfGradeInputDto)` — function, line 1355
- `const submittedItemId = item.id` — const, line 1357
- `const submittedKey = submissionId.current` — const, line 1358
- `const grade = gradeOverride ?? selfGrade` — const, line 1361
- `const emptyStuck = stuck && !answer.trim() && !whyLine.trim() && !redo` — const, line 1364
- `const validation = emptyStuck ?` — const, line 1377
- `const result = await api.submitAttempt(` — const, line 1387
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 1437
- `const recovery = committedAttemptRecovery(error)` — const, line 1440
- `const command = getCommandError(error)` — const, line 1449
- `async function skip()` — function, line 1468
- `const skippedIdentity =` — const, line 1470
- `async function acknowledgeCheckpoint(practiceItemId: string, expectedSubmissionId: string): Promise<boolean>` — function, line 1484
- `const result = await api.acknowledgePracticeSubmission(` — const, line 1487
- `const loadError = itemLoadError ?? probeLoadError` — const, line 1502
- `const diagnostic = committedRecovery.attemptType === "diagnostic_probe" || probeActive` — const, line 1528
- `const dockedPanel = dockedAsk && panelOn && !stepsMode ? ( <AskOverlay variant="docked" target=` — const, line 1618
- `const on = answerConfidence === level` — const, line 2334
- `const locked = submitting || selfGradeVisible` — const, line 2335
- `function TeachBackConversation(` — function, line 2453
- `const startedRef = useRef(false)` — const, line 2482
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 2483
- `const activeClock = useAttemptClock()` — const, line 2486
- `const clockKey = `teach_back:$` — const, line 2487
- `const lastRole = turns.length > 0 ? turns[turns.length - 1].role : null` — const, line 2492
- `const needsText = turns.length === 0 || lastRole === "ai"` — const, line 2496
- `const start = useCallback(()` — const, line 2498
- `const node = transcriptRef.current` — const, line 2528
- `async function send(finish = false)` — function, line 2532
- `const text = input.trim()` — const, line 2534
- `const result = await api.submitTeachBackTurn(` — const, line 2540
- `const onKey = (event: KeyboardEvent)` — const, line 2568
- `const submitLabel = turns.length === 0 ? "Start teaching" : lastRole === "learner" ? "Continue" : "Send answer"` — const, line 2579
- `const questionsAnswered = asked > 0 && lastRole === "learner"` — const, line 2581
- `function gradeFromParts( item: PracticeItemDetail, base: SelfGradeInputDto, got: (criterionId: string)` — function, line 2698
- `function PlainSelfGrade(` — function, line 2717
- `const criteria = item.rubric?.criteria ?? []` — const, line 2754
- `const fullAnswer = expectedAnswerText(item.expectedAnswer).trim()` — const, line 2755
- `const exposure = useAnswerExposure(exposureKey, showFullAnswer && Boolean(fullAnswer), recordDisplay)` — const, line 2760
- `function SelfGradePanel(` — function, line 2816
- `const awarded = value.criterionPoints[criterion.id] ?? 0` — const, line 2847
- `const docked = awarded < criterion.points` — const, line 2848
- `const points = Number(event.target.value)` — const, line 2864
- `const stillDocked = points < criterion.points` — const, line 2865
- `function CriterionErrorPicker(` — function, line 2929
- `const selected = new Set( (value.errorAttributions ?? []).filter((a)` — const, line 2940
- `const toggle = (errorType: string)` — const, line 2943
- `const list = value.errorAttributions ?? []` — const, line 2944
- `const exists = list.some((a)` — const, line 2945
- `const relevant = candidates.filter((c)` — const, line 2953
- `const others = candidates.filter((c)` — const, line 2954
- `const chip = (c: CandidateErrorTypeDto)` — const, line 2955
- `function prunedAttributions(item: PracticeItemDetail, grade: SelfGradeInputDto): SelfGradeErrorAttributionDto[]` — function, line 2992
- `const docked = new Set( (item.rubric?.criteria ?? []) .filter((criterion)` — const, line 2993
- `const NON_RECORDING_ATTEMPT_TYPES: ReadonlySet<AttemptType> = new Set(["guided_walkthrough", "skip"])` — const, line 3004
- `function defaultAttemptType(allowed: readonly AttemptType[]): AttemptType` — function, line 3006
- `function RedoWhatToFix(` — function, line 3019
- `function composeRedoAnswer(prefix: string, redoText: string): string` — function, line 3037
- `const suffix = redoText.replace(/^[ \t]+/, "")` — const, line 3038
- `function recordHintReveal(input: Parameters<typeof api.recordHintReveal>[0]): void` — function, line 3047
- `const parts: string[] = []` — const, line 3073
- `const worked = (entries ?? []).filter((entry)` — const, line 3078
- `const plain = Math.max(0, hints - worked.length)` — const, line 3079
- `let clientOnly: number` — let, line 3092
- `let clientWorked: number[] = []` — let, line 3093
- `const listedIds = new Set(server.items.map((entry)` — const, line 3098
- `const unlisted = entries.filter((entry)` — const, line 3099
- `const serverHints = server.items.filter((entry)` — const, line 3103
- `const listed = new Set<string>()` — const, line 3107
- `function chooseAttemptType(allowed: readonly AttemptType[], hintsUsed: number): AttemptType` — function, line 3138
- `const allows = (type: AttemptType)` — const, line 3139
- `function validateSelfGrade( item: PracticeItemDetail, value: SelfGradeInputDto, required: boolean ): Record<string, string>` — function, line 3144
- `const errors: Record<string, string> =` — const, line 3150
- `const points = value.criterionPoints[criterion.id]` — const, line 3152
- `function answerBoxCap(slot: HTMLElement, below: number): number` — function, line 3165
- `const scroller = slot.closest(".screen-scroll") as HTMLElement | null` — const, line 3166
- `const keybar = (document.querySelector(".keybar") as HTMLElement | null)?.offsetHeight ?? 36` — const, line 3167
- `const visible = scroller && scroller.clientHeight > 0 ? scroller.clientHeight : window.innerHeight - keybar` — const, line 3168

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `PracticeScreen`; references `PracticeScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AttemptProgress`, `AttemptResultDto`, `AttemptType`, `CandidateErrorTypeDto`, `DifficultyRating`, `FirstHintProgress`, `HelpRecordDto`, `PracticeItemDetail`, `ProbeBlockEndDto`, `ProbeContractDto`, `RubricCriterionDto`, `SelfGradeDisclosureDto`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SessionSnapshot`, `TeachBackStateDto`, `TeachBackTurnDto`, `WorkbenchSessionDto`, `WorkbenchSummaryDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `STUCK_PROMPT_TEXT`, `algoConfig`, `masteryTone`, `setAdaptiveHelpStyle`
- [[Reference/Desktop/TypeScript/app/checkHandoff|src/app/checkHandoff.ts]] — import-or-re-export; imports `CheckHandoff`, `STOP_AND_TEACH_LABEL`, `handoffOpensLesson`
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
- [[Reference/Desktop/TypeScript/components/Waiting|src/components/Waiting.tsx]] — import-or-re-export; imports `Waiting`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export; imports `PANEL_FIGURE_COPY`, `PanelFigureEvent`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export; imports `ASK_COPY`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`, `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `EntityLink`, `KeyBar`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/copy/refusals|src/copy/refusals.ts]] — import-or-re-export; imports `NO_ASK_SHORT_CHECK`, `NO_ASK_TEACH_BACK`, `NO_HINTS_ON_YOUR_OWN`, `NO_HINTS_SHORT_CHECK`
- [[Reference/Desktop/TypeScript/copy/waiting|src/copy/waiting.ts]] — import-or-re-export; imports `WAITING_COPY`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/MathLiveEditor|src/render/MathLiveEditor.tsx]] — import-or-re-export; imports `MathLiveEditor`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export; imports `AnswerWaiting`, `RedoContext`
- [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|src/screens/feedback/answerExposure.ts]] — import-or-re-export; imports `RecordDisplay`, `useAnswerExposure`
- [[Reference/Desktop/TypeScript/screens/practice/DifficultyRatingTap|src/screens/practice/DifficultyRatingTap.tsx]] — import-or-re-export; imports `DifficultyRatingTap`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export; imports `HintPanel`
- [[Reference/Desktop/TypeScript/screens/practice/WhyThisItem|src/screens/practice/WhyThisItem.tsx]] — import-or-re-export; imports `WhyThisItem`
- [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]] — import-or-re-export; imports `useAdaptiveHints`
- [[Reference/Desktop/TypeScript/screens/practice/useFirstHintProgress|src/screens/practice/useFirstHintProgress.ts]] — import-or-re-export; imports `useFirstHintProgress`
- [[Reference/Desktop/TypeScript/screens/useAttemptClock|src/screens/useAttemptClock.ts]] — import-or-re-export; imports `useAttemptClock`
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
- [apps/learnloop-tauri/src/screens/PracticeScreen.waiting.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.waiting.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.refusals.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.refusals.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.phase4.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.phase4.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.ownerCapture1025.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.ownerCapture1025.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/PracticeScreen.intentCheck.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.intentCheck.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/PracticeScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
