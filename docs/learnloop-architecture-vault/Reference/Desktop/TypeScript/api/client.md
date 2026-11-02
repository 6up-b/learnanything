---
title: "Desktop module · src/api/client.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.client"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/client.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/client.ts"
source_commit: "6975ac1949e79b05a13f0cf392d617aa1d91fc25"
source_commit_timestamp: "2026-11-02T03:56:28-05:00"
source_worktree_state: "staged-or-mixed"
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

# `src/api/client.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Defines the typed renderer-side RPC facade that converts UI actions into named Tauri commands.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/client.ts](../../../../../../apps/learnloop-tauri/src/api/client.ts) |
| Source lines | 1951 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `6975ac1949e79b05a13f0cf392d617aa1d91fc25` |
| Commit timestamp | `2026-11-02T03:56:28-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]]

## Public API

- `export const api =` — const, line 536

## Internal implementation anchors

- `function readRpcDebugFlag(): boolean` — function, line 381
- `const RPC_DEBUG = import.meta.env.DEV && readRpcDebugFlag()` — const, line 388
- `const rpcCounts = new Map<string, number>()` — const, line 389
- `async function call<T>(command: string, args: Record<string, unknown> =` — function, line 394
- `const count = (rpcCounts.get(command) ?? 0) + 1` — const, line 396
- `let result: T` — let, line 400
- `const normalized = normalizeError(error)` — const, line 404
- `function normalizeError(error: unknown): CommandError` — function, line 414
- `const commandError = error as CommandError` — const, line 416
- `const validationErrors = (commandError.details as` — const, line 417
- `const ATTEMPT_TAGS: readonly QueryTag[] = [TAG.queue, TAG.graph, TAG.goals, TAG.review, TAG.maintenance, TAG.errors]` — const, line 456
- `const INGEST_TAGS: readonly QueryTag[] = [TAG.sources, TAG.library, TAG.maintenance]` — const, line 458
- `const REVISION_TAGS: readonly QueryTag[] = [TAG.sources, TAG.graph, TAG.proposals, TAG.registry, TAG.maintenance]` — const, line 460
- `function settled<T>(promise: Promise<T>, onSettled: ()` — function, line 469
- `function mutating<T>(tags: readonly QueryTag[], promise: Promise<T>): Promise<T>` — function, line 482
- `function mutatingAll<T>(promise: Promise<T>): Promise<T>` — function, line 487
- `function mutatingReader<T>(promise: Promise<T>, extraTags: readonly QueryTag[] = []): Promise<T>` — function, line 492
- `function afterProposalMutation( promise: Promise<ProposalsSnapshot>, extraTags: readonly QueryTag[] = [] ): Promise<ProposalsSnapshot>` — function, line 500
- `function afterSettingsMutation(promise: Promise<SettingsDto>): Promise<SettingsDto>` — function, line 522

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/app/autoAdvance|src/app/autoAdvance.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/app/todayPlan|src/app/todayPlan.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AddSource|src/components/AddSource.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CapturePhoto|src/components/CapturePhoto.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ChatGPTPlanSettings|src/components/ChatGPTPlanSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ConnectAI|src/components/ConnectAI.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/DiagnosisCard|src/components/DiagnosisCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/FacetIdentityPanel|src/components/FacetIdentityPanel.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalCard|src/components/GoalCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/IntentControl|src/components/IntentControl.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/PlacementControls|src/components/PlacementControls.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/PlanFallbackOffer|src/components/PlanFallbackOffer.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/PlanReadingBanner|src/components/PlanReadingBanner.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ReadinessLine|src/components/ReadinessLine.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/RewordConfirms|src/components/RewordConfirms.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/SourceOffers|src/components/SourceOffers.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/TrackRecordView|src/components/TrackRecordView.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/recipeedit/RecipeTreeEditor|src/components/recipeedit/RecipeTreeEditor.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/LibraryPlace|src/screens/LibraryPlace.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/practice/HelpStyleSettings|src/screens/practice/HelpStyleSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/practice/WhyThisItem|src/screens/practice/WhyThisItem.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableScope|src/screens/reader/DeliverableScope.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|src/screens/reader/DoseOffer.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/HiddenNotesSettings|src/screens/reader/HiddenNotesSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/NotesGapsSettings|src/screens/reader/NotesGapsSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCorrespondenceSettings|src/screens/reader/ReaderCorrespondenceSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCueSettings|src/screens/reader/ReaderCueSettings.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/ScopeFromPassage|src/screens/reader/ScopeFromPassage.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|src/screens/reader/TutorOffers.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|src/screens/reader/WrapUpOffer.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/correspondentsRead|src/screens/reader/correspondentsRead.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/guidePlan|src/screens/reader/guidePlan.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|src/screens/reader/useCueDiscovery.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|src/screens/reader/useCueImpressions.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useKeptComparisons|src/screens/reader/useKeptComparisons.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryExercises|src/screens/reader/useLibraryExercises.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|src/screens/reader/useReadingProgress.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|src/screens/today/LessonSuggestionCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/underhood/tools|src/screens/underhood/tools.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|src/screens/workbench/useWorkbenchHelp.ts]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export: `api`; references `api`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/capture|src/api/capture.ts]] — dynamic import
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — dynamic import; imports `AcceptEdgeResultDto`, `AcquisitionPreview`, `AddSourceInput`, `AddSourceResultDto`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationRecordResultDto`, `AdjudicationScoreboardDto`, `AiConnectionDto`, `AiUseFallbackDto`, `AnimationRuntimeDto`, `AnswerCalibrationReportDto`, `AnswerGradingClarificationResultDto`, `AppSnapshot`, `AppendResultDto`, `AppendSourceInput`, `AsPrintedViewDto`, `AskTutorQuestionInput`, `AssessOpenDto`, `AssessResultDto`, `AttemptResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `BeginProbeDialogueResult`, `BlueprintReadinessPreviewDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `BuildPlan`, `BuildPlanSelectionInput`, `BuildStudyMapInput`, `CalibrationSessionProgressDto`, `CapabilityGridResult`, `CausalProbeDeferResultDto`, `CausalProbeOfferResultDto`, `CausalRepairStatusResultDto`, `ChatGPTPlanDto`, `ClaimCandidateDto`, `CliCommandResult`, `CommandError`, `CompareRequestDto`, `CompareScopeReadingDto`, `CompareTableDto`, `ComposeDraftResult`, `ConceptAnimationDto`, `ConceptGraphSnapshot`, `ConfirmQuickAddInput`, `ConfirmReceiptDto`, `CorrespondencePreferencesDto`, `CorrespondentOperationDto`, `CorrespondentPeekDto`, `CorrespondentsDto`, `CoverageCorrectionChoice`, `CreateGoalInput`, `CreateGoalResult`, `CreateStudyMapInput`, `CreateVaultInput`, `CreateVaultResult`, `CueDensity`, `DailyPlanDto`, `DecayPressureSnapshot`, `DeliverablePathChoice`, `DeliverableReadyDto`, `DeliverableScopeDto`, `DeliverableSliceDto`, `DepthInvitationResultDto`, `DetectProviderCapabilitiesInput`, `DiagnosisCardDto`, `DiagnosisCardResponse`, `DiagnosisFeedbackResultDto`, `DifficultyRating`, `EffectiveOutlineDto`, `ElicitingResponseResultDto`, `EndProbeDialogueResult`, `EntityProvenance`, `EscalationResponse`, `ExamAnswerResult`, `ExamReadinessReportDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`, `ExamStatusSnapshot`, `ExemplarPoolSnapshot`, `ExerciseCandidatesDto`, `FacetDetailDto`, `FacetEvidenceTimelineDto`, `FacetIdentityActionDto`, `FacetListDto`, `FacetMasterySnapshot`, `FacetMergeResultDto`, `FacetRewordDecisionDto`, `FeedbackBundle`, `FigureBuildResultDto`, `FigurePredictionResultDto`, `FiguresDto`, `FindExercisesDto`, `FindPracticeResultDto`, `FirstHintProgress`, `ForecastTrackRecordDto`, `GenerateCommissioningPracticeResult`, `GenerateStarterPracticeResult`, `GetNextProbeItemDto`, `GoalDto`, `GoalFeasibilityInput`, `GoalFeasibilityResult`, `GoalReportSnapshot`, `GoalSeriesSnapshot`, `GoalsListSnapshot`, `GradingClarificationResultDto`, `GradingProviderResult`, `GuidedRedoDto`, `HelpStyle`, `HiddenNoteDto`, `HintCancelDto`, `HintDiscriminateAnswerDto`, `HintJobDto`, `HintRequestInput`, `HypothesisEventDto`, `IngestBatchDto`, `IngestBatchesSnapshot`, `IngestBudgetsDto`, `IngestJobDto`, `IngestJobsSnapshot`, `IngestSourceClassification`, `InquirySelfCheck`, `InspectorEntity`, `IntentChoice`, `IntentScopeKind`, `IntentViewDto`, `KeepComparisonResultDto`, `KeepTakeDto`, `KeptMarksDto`, `KnowledgeMapHistory`, `KnowledgeMapPreviewDto`, `KnowledgeMapSnapshot`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `LearnerProfileDto`, `LearnerTextGapReversal`, `LearnerTextGapReversalDto`, `LearnerTextGapStatusDto`, `LessonSuggestionDto`, `LessonSuggestionResponseDto`, `LessonTurnInput`, `LessonViewDto`, `LibraryAskDto`, `LibraryAskEntry`, `LibraryExpansion`, `LibraryJobDto`, `LibraryNotesDto`, `LibraryTutorDto`, `MaintenanceFeedSnapshot`, `MaintenanceNoticeDto`, `MeasurementHealthDto`, `NextProbeDialogueTurnResult`, `NoteLinkDto`, `NoteMarksDto`, `NoteSearchDto`, `NotesPathDto`, `OpenrouterKeyResult`, `OverconfidenceSnapshot`, `PlacementSelfReportInput`, `PlacementSelfReportResult`, `PlacementStateDto`, `PlanQuickAddInput`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `PoolStatusDto`, `PracticeCallerDto`, `PracticeItemDetail`, `PracticeRequestDto`, `PracticeSubmissionAcknowledgementDto`, `PracticeSubmissionRecoveryDto`, `PresentedClaimDto`, `PreviewBlueprintReadinessInput`, `PreviewKnowledgeMapInput`, `PrimedRetryResultDto`, `PrintRegionDto`, `PrintedCropsDto`, `ProbeContractDto`, `ProbeRemintResultDto`, `PromoteTutorQuestionResult`, `PromotionIntent`, `ProposalsSnapshot`, `ProposeFacetMergeInput`, `ProposeGraphEditsInput`, `ProposeGraphEditsResult`, `ProviderCapabilitiesDto`, `QuestionQueueSnapshot`, `QuestionResolution`, `QueueInput`, `QueueRestructureRequestInput`, `QueueRestructureRequestResult`, `QueueRevisionDto`, `QueueSnapshot`, `QuickAddConfirmationDto`, `QuickAddPlanDto`, `QuickAddResultDto`, `ReaderActiveQuestionDto`, `ReaderActiveQuestionRequestDto`, `ReaderActiveQuestionStatusDto`, `ReaderActiveStyle`, `ReaderActivityEvent`, `ReaderAnnotationResultDto`, `ReaderAnswerDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderAskHistoryDto`, `ReaderAskInput`, `ReaderAuthorQAInput`, `ReaderAuthorSectionQuestionDto`, `ReaderAuthoredCardDto`, `ReaderAuthoredQuestionDto`, `ReaderBlockRegionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderCoachLintDto`, `ReaderCreateAnnotationInput`, `ReaderCueAction`, `ReaderCueActionDto`, `ReaderCueDiscoveryJobDto`, `ReaderCueImpressionInput`, `ReaderCuePreferencesDto`, `ReaderCueTapAction`, `ReaderCueTapDto`, `ReaderDisposition`, `ReaderDispositionResultDto`, `ReaderEnqueueRequestDto`, `ReaderEnqueueRequestInput`, `ReaderExerciseImportReceiptDto`, `ReaderExerciseImportStatusDto`, `ReaderFollowupsDto`, `ReaderGuidePlanDto`, `ReaderImportExerciseInput`, `ReaderInquiryQuestionActionInput`, `ReaderInquiryQuestionDto`, `ReaderInquiryQuestionReadDto`, `ReaderInquiryStatusDto`, `ReaderIntentRoutingDto`, `ReaderInvokePresetInput`, `ReaderMaintainInput`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderProgressListDto`, `ReaderPromptContractDto`, `ReaderQuestionControlResultDto`, `ReaderRecapDto`, `ReaderRecapEvent`, `ReaderReconnectAnswerDto`, `ReaderReconnectAnswerInput`, `ReaderRenderViewDto`, `ReaderRequestRow`, `ReaderRestorationDto`, `ReaderSavedPlaceDto`, `ReaderSetInquiryStatusInput`, `ReaderSetModeResultDto`, `ReaderSourceSearchDto`, `ReaderSpanLearningObjectsDto`, `ReaderTranslateSelectionInput`, `ReaderTranslationDto`, `ReaderWatchPlanDto`, `ReaderWrapUpDto`, `ReaderWrapUpOfferDto`, `ReadingPathChoice`, `ReadingPathDepth`, `ReadingPathDto`, `RecentIngestsSnapshot`, `RecordProbeDialogueTurnResult`, `ReentrySummarySnapshot`, `RefreshResultDto`, `RefreshRevisionInput`, `RemediationDto`, `RequestConceptAnimationResult`, `ResolveConflictInput`, `ResolveEdgeDirectionInput`, `ResolveEdgeDirectionResult`, `ResolveQuestionEventResult`, `RestoreDto`, `RetirementReason`, `RetrySynthesisInput`, `ReviewCountsDto`, `ReviewLogDto`, `RunAdvanceResultDto`, `RunListDto`, `RunStateDto`, `RungVariantRequestDto`, `RungVariantRequestResultDto`, `RuntimeHealth`, `SaveUnitSelectionInput`, `SchedulerExplanationDto`, `SelectionPreviewDto`, `SessionEndSummary`, `SessionSnapshot`, `SessionStartInput`, `SettingsDto`, `SideBySideSectionDto`, `SourceActionKind`, `SourceActionResultDto`, `SourceConflictDto`, `SourceCoverageDto`, `SourceDeletionPlanDto`, `SourceDeletionResultDto`, `SourceExerciseImportDto`, `SourceLibrarySnapshot`, `SourceOutline`, `SourceSetDto`, `SourceSetsSnapshot`, `SourceToolRunDto`, `SpanViewDto`, `SpanViewInput`, `SqliteExecResult`, `SqliteTableSnapshot`, `SqliteTablesSnapshot`, `StartCalibrationSessionInput`, `StartExtractionRepairInput`, `StartImportBatchInput`, `StartIngestInput`, `StartInventoryInput`, `StartOverconfidenceProbeResult`, `StartQuickCheckInput`, `StartRemediationDto`, `StartSummaryDto`, `StartTeachBackInput`, `StartTeachBackResult`, `StartingLevel`, `StopProbeResultDto`, `StudyMapDto`, `SubjectRegistryDto`, `SubmitAttemptInput`, `SubmitTeachBackTurnInput`, `SynthesisCandidateSummary`, `TeachBackTurnResult`, `TextRecognitionKeyResult`, `TodayHeadlineDto`, `TranscriptionKeyResult`, `TranscriptionReportDto`, `TriageResultDto`, `TriageStatusDto`, `TutorAnswerDto`, `TutorOpeningDto`, `TutorSaveNoteResult`, `TutorTranscriptInput`, `TutorTranscriptSnapshot`, `UnitSelectionState`, `UnresolvedCauseSelfReportResponse`, `UnresolvedCauseSelfReportResultDto`, `UpdateAiSettingsInput`, `UpdateAnimationSettingsInput`, `UpdateIngestSettingsInput`, `UpdateProviderModalitiesInput`, `VaultFileContent`, `VaultSummary`, `VaultTreeSnapshot`, `WorkbenchAdmitDto`, `WorkbenchAnotherPassageDto`, `WorkbenchCompareMethodsDto`, `WorkbenchCompareOfferDto`, `WorkbenchHelpJobDto`, `WorkbenchHelpStateDto`, `WorkbenchOpenInput`, `WorkbenchOpenProblemDto`, `WorkbenchRequestHelpInput`, `WorkbenchSaveStepDto`, `WorkbenchSaveStepInput`, `WorkbenchSessionDto`, `WorkbenchSubmitDto`, `WorkbenchSubmitInput`, `WorkbenchSummaryDto`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `QueryTag`, `invalidate`, `invalidateAll`, `setQueryData`
- [[Reference/Desktop/TypeScript/api/queryTags|src/api/queryTags.ts]] — import-or-re-export; imports `READER_PREFIX`, `TAG`
- [[Reference/Desktop/TypeScript/app/planFallback|src/app/planFallback.ts]] — import-or-re-export; imports `noteFallbackOffer`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/core`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/reader/guidePlan.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.guide.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.guide.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/autoAdvance.test.tsx](../../../../../../apps/learnloop-tauri/src/app/autoAdvance.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct source contract: references the exact source path.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/client.ts](../../../../../../apps/learnloop-tauri/src/api/client.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
