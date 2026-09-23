---
title: "Desktop module · src/api/dto.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.api.dto"
language: "TypeScript"
area: "TypeScript/api"
source_path: "apps/learnloop-tauri/src/api/dto.ts"
source_paths:
  - "apps/learnloop-tauri/src/api/dto.ts"
source_commit: "c369ee23244d6f87e7bc33ef2c6a9bba55aeb982"
source_commit_timestamp: "2026-09-23T15:38:43-04:00"
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

# `src/api/dto.ts`

Area: [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Owns the renderer's TypeScript representation of sidecar request, response, and view contracts.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/api/dto.ts](../../../../../../apps/learnloop-tauri/src/api/dto.ts) |
| Source lines | 6249 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `c369ee23244d6f87e7bc33ef2c6a9bba55aeb982` |
| Commit timestamp | `2026-09-23T15:38:43-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]]

## Public API

- `export type IsoTimestamp = string` — type, line 1
- `export type Ulid = string` — type, line 2
- `export type AttemptType = | "independent_attempt" | "hinted_attempt" | "dont_know" | "diagnostic_probe" | "guided_walkthrough" | "reconstruction_after_walkthrough" | "skip" | "self_report" | "open_text" | "teach_back"` — type, line 4
- `export type FsrsRating = "again" | "hard" | "good" | "easy"` — type, line 16
- `export type GradingSource = "codex" | "ai" | "self"` — type, line 17
- `export interface RuntimeHealth` — interface, line 19
- `export interface GradingProviderResult` — interface, line 49
- `export interface SettingsProviderDto` — interface, line 56
- `export interface SettingsAiDto` — interface, line 67
- `export interface OpenrouterKeyStateDto` — interface, line 76
- `export interface KeyStateDto` — interface, line 82
- `export interface IngestBudgetsDto` — interface, line 89
- `export type IngestBudgetField = keyof IngestBudgetsDto` — type, line 97
- `export type IngestBudgetBoundsDto = Record<IngestBudgetField,` — type, line 101
- `export interface IngestProviderLimitsDto` — interface, line 105
- `export type AudioMode = "transcription" | "native"` — type, line 111
- `export interface NativeModalityStateDto` — interface, line 116
- `export interface CatalogStateDto` — interface, line 130
- `export interface SettingsNativeIngestDto` — interface, line 137
- `export interface SettingsIngestDto` — interface, line 146
- `export interface SettingsDto` — interface, line 159
- `export type AnimationRenderer = "manim" | "video_model"` — type, line 170
- `export interface SettingsVideoDto` — interface, line 174
- `export interface SettingsAnimationDto` — interface, line 184
- `export interface UpdateAnimationSettingsInput` — interface, line 198
- `export interface UpdateIngestSettingsInput` — interface, line 206
- `export interface DetectProviderCapabilitiesInput` — interface, line 221
- `export interface ProviderCapabilitiesDto` — interface, line 226
- `export interface UpdateProviderModalitiesInput` — interface, line 241
- `export interface TranscriptionKeyResult` — interface, line 246
- `export interface AnimationRuntimeDto` — interface, line 253
- `export interface StoryboardShotDto` — interface, line 271
- `export interface StoryboardDto` — interface, line 277
- `export interface ConceptAnimationDto` — interface, line 284
- `export interface RequestConceptAnimationResult` — interface, line 307
- `export interface UseCaseChoiceInput` — interface, line 314
- `export interface UpdateAiSettingsInput` — interface, line 319
- `export interface OpenrouterKeyResult` — interface, line 324
- `export interface FacetMasteryLearningObject` — interface, line 332
- `export interface FacetMasteryPracticeItem` — interface, line 339
- `export interface FacetMasteryFacet` — interface, line 349
- `export interface FacetMasterySnapshot` — interface, line 361
- `export interface KnowledgeMapPoint` — interface, line 371
- `export interface KnowledgeMapSnapshot` — interface, line 389
- `export type CapabilityArcStatus = "demonstrated" | "required" | "absent"` — type, line 399
- `export interface KnowledgeFacetPoint` — interface, line 401
- `export interface KnowledgeFieldEdge` — interface, line 434
- `export interface KnowledgeNextGap` — interface, line 440
- `export interface KnowledgeFacetField` — interface, line 450
- `export interface KnowledgeHistoryAttempt` — interface, line 461
- `export interface KnowledgeHistorySeriesPoint` — interface, line 473
- `export interface KnowledgeMapHistory` — interface, line 481
- `export interface VaultSummary` — interface, line 488
- `export interface StreakSummary` — interface, line 505
- `export interface AppSnapshot` — interface, line 514
- `export interface SessionStartInput` — interface, line 523
- `export interface SessionSnapshot` — interface, line 530
- `export interface SessionEndSummary` — interface, line 542
- `export interface SessionCheckpoint` — interface, line 561
- `export interface QueueInput` — interface, line 576
- `export interface SchedulerComponents` — interface, line 583
- `export interface ScheduledItemDto` — interface, line 596
- `export type FollowupKind = | "certification_cold_probe" | "cold_retry" | "intervention_followup" | "negative_surprise_followup"` — type, line 623
- `export interface QueueSection` — interface, line 629
- `export interface DeferredColdCheckDto` — interface, line 637
- `export interface QueueSnapshot` — interface, line 648
- `export interface CriterionTargetDto` — interface, line 660
- `export interface RubricCriterionDto` — interface, line 666
- `export interface RubricFatalErrorDto` — interface, line 687
- `export interface RubricDto` — interface, line 693
- `export interface CandidateErrorTypeDto` — interface, line 701
- `export interface ElicitationDecisionDto` — interface, line 713
- `export type PresentationBlockKind = | "prompt" | "error_hunt_worked_solution" | "laddered_stem_stimulus"` — type, line 735
- `export interface PresentationBlockDto` — interface, line 740
- `export interface ItemPresentationDto` — interface, line 749
- `export interface PracticeItemDetail` — interface, line 754
- `export interface TraceExercisedFacetDto` — interface, line 808
- `export interface AttemptTraceEvidenceDto` — interface, line 816
- `export interface GradingClarificationDto` — interface, line 827
- `export interface GradingClarificationResultDto` — interface, line 847
- `export type ClarificationOutcome = "resolved" | "abstained" | "regrade_failed"` — type, line 854
- `export interface AnswerGradingClarificationResultDto` — interface, line 856
- `export interface AttemptHistoryRowDto` — interface, line 867
- `export interface SourceRefDto` — interface, line 879
- `export interface PracticeItemStateDto` — interface, line 889
- `export interface MasteryDto` — interface, line 898
- `export interface MasteryStepFactorDto` — interface, line 909
- `export interface MasteryStepDto` — interface, line 921
- `export interface SchedulerExplanationDto` — interface, line 934
- `export interface SelfGradeErrorAttributionDto` — interface, line 947
- `export interface SelfGradeInputDto` — interface, line 952
- `export interface SubmitAttemptInput` — interface, line 961
- `export interface ProbeBlockEndDto` — interface, line 991
- `export interface ProbeContractDto` — interface, line 1018
- `export interface StopProbeResultDto` — interface, line 1039
- `export interface GetNextProbeItemDto` — interface, line 1047
- `export interface ResolvedSourceRefDto` — interface, line 1054
- `export interface AttemptResultDto` — interface, line 1077
- `export interface PracticeSubmissionRecoveryDto` — interface, line 1104
- `export interface PracticeSubmissionAcknowledgementDto` — interface, line 1110
- `export interface FeedbackBundle` — interface, line 1116
- `export interface ColdCheckResultDto` — interface, line 1187
- `export interface CausalFeedbackDto` — interface, line 1207
- `export interface CausalTargetRefDto` — interface, line 1272
- `export interface CausalDivergenceAnchorDto` — interface, line 1284
- `export interface RepairedTraceDto` — interface, line 1295
- `export interface CausalRepairClassDto` — interface, line 1305
- `export interface CausalHypothesisDto` — interface, line 1317
- `export interface CausalMinimalityDto` — interface, line 1341
- `export interface DiagnosisReceiptDto` — interface, line 1355
- `export type CausalTraceConsistencyState = | "contradicted" | "consistent_with_claims" | "no_deterministic_claims" | "unknown"` — type, line 1457
- `export interface CausalProbeNeedDto` — interface, line 1463
- `export type CausalRepairStatusState = | "started" | "needs_disambiguation" | "deferred_machine_checks" | "safe_common_repair_available" | "blocked_pending_review"` — type, line 1480
- `export type CausalRepairActionId = "take_quick_check" | "teach_me_now" | "not_now"` — type, line 1490
- `export interface CausalRepairActionDto` — interface, line 1492
- `export interface CausalRepairStatusDto` — interface, line 1497
- `export interface CausalRepairStatusResultDto` — interface, line 1538
- `export interface CausalProbeOfferDto` — interface, line 1545
- `export interface CausalProbeOfferResultDto` — interface, line 1557
- `export interface CausalProbePreferenceDto` — interface, line 1562
- `export interface CausalProbeDeferResultDto` — interface, line 1574
- `export interface CausalEpisodeDto` — interface, line 1579
- `export interface PersistedRegradeDto` — interface, line 1591
- `export interface MatchedMisconceptionDto` — interface, line 1599
- `export interface UnresolvedCauseDto` — interface, line 1609
- `export type UnresolvedCauseSelfReportResponse = | "slipped" | "believed_candidate" | "item_unclear" | "notation_confused" | "other_valid_approach" | "diagnosis_wrong"` — type, line 1638
- `export interface ElicitingResponseResultDto` — interface, line 1654
- `export interface UnresolvedCauseSelfReportResultDto` — interface, line 1665
- `export interface PrimedRetryResultDto` — interface, line 1674
- `export interface GuidedRedoDto` — interface, line 1689
- `export type TutorQuestionContext = "library" | "practice" | "feedback" | "reader"` — type, line 1713
- `export interface AskTutorQuestionInput` — interface, line 1715
- `export interface TutorCitationDto` — interface, line 1728
- `export interface TutorAnswerDto` — interface, line 1734
- `export interface TutorOpeningDto` — interface, line 1749
- `export interface TutorQuestionEventDto` — interface, line 1754
- `export type PromotionIntent = "practice" | "gap"` — type, line 1781
- `export type PromotionRoute = "auto_apply" | "review_required" | "diagnostic_pending" | "existing_item"` — type, line 1783
- `export type QuestionNature = "core_recall" | "mechanism" | "transfer" | "edge_case" | "what_if"` — type, line 1785
- `export interface QuestionPromotionDto` — interface, line 1787
- `export interface PromoteTutorQuestionInput` — interface, line 1805
- `export interface QuestionPromotionRequestDto` — interface, line 1812
- `export interface PromoteTutorQuestionResult` — interface, line 1828
- `export type QuestionResolution = "open" | "resolved" | "dismissed"` — type, line 1838
- `export interface QuestionQueueRowDto` — interface, line 1840
- `export interface QuestionQueueSnapshot` — interface, line 1861
- `export interface ResolveQuestionEventResult` — interface, line 1867
- `export interface QueueRevisionDto` — interface, line 1874
- `export const RETIREMENT_REASONS = [ "too_easy", "ambiguous", "missing_context", "duplicate_surface", "wrong_granularity", "no_longer_relevant", "bad_underlying_explanation", "superseded_by_better_activity", "should_be_reference_not_memorized", "dont_care_enou…` — const, line 1884
- `export type RetirementReason = (typeof RETIREMENT_REASONS)[number]` — type, line 1898
- `export interface TutorTranscriptInput` — interface, line 1900
- `export interface TutorTranscriptSnapshot` — interface, line 1908
- `export interface TutorSaveNoteResult` — interface, line 1914
- `export type RubricTier = "core" | "transfer"` — type, line 1922
- `export interface TeachBackPlannedDto` — interface, line 1924
- `export interface TeachBackTurnDto` — interface, line 1930
- `export interface TeachBackStateDto` — interface, line 1937
- `export interface StartTeachBackInput` — interface, line 1947
- `export interface StartTeachBackResult` — interface, line 1954
- `export interface SubmitTeachBackTurnInput` — interface, line 1965
- `export interface TeachBackQuestionResult` — interface, line 1975
- `export type TeachBackFinishResult = AttemptResultDto &` — type, line 1989
- `export type TeachBackTurnResult = TeachBackQuestionResult | TeachBackFinishResult` — type, line 1996
- `export interface FollowupSourceDto` — interface, line 1998
- `export interface FollowupRatingDto` — interface, line 2002
- `export interface InterventionNeedDto` — interface, line 2007
- `export interface CriterionEvidenceRowDto` — interface, line 2024
- `export interface ErrorEventDto` — interface, line 2036
- `export interface AttemptSurpriseDto` — interface, line 2049
- `export interface FollowupGateSignalDto` — interface, line 2067
- `export interface FollowupGateSubscoreDto` — interface, line 2081
- `export interface FollowupGateDiagnosticsDto` — interface, line 2092
- `export interface RepairSuggestionDto` — interface, line 2127
- `export interface AttemptInspectorDetail` — interface, line 2168
- `export interface NoteInspectorDetail` — interface, line 2197
- `export interface ProbeEpisodeInspectorDetail` — interface, line 2213
- `export type InspectorEntity = |` — type, line 2240
- `export interface InspectorSearchResult` — interface, line 2250
- `export interface LearningObjectDetail` — interface, line 2258
- `export interface ConceptReferenceDto` — interface, line 2279
- `export interface ConceptInspectorDetail` — interface, line 2291
- `export interface CommandError` — interface, line 2314
- `export interface CliCommandResult` — interface, line 2321
- `export interface RecentIngestEntry` — interface, line 2329
- `export interface RecentIngestsSnapshot` — interface, line 2343
- `export type IngestMode = "canonical" | "exam"` — type, line 2348
- `export type IngestJobStatus = "queued" | "running" | "completed" | "failed" | "cancelled"` — type, line 2349
- `export type IngestJobPhase = | "queued" | "preparing" | "fetching" | "extracting" | "staging" | "authoring" | "cancelling" | "completed" | "failed" | "cancelled"` — type, line 2350
- `export interface IngestSourceClassification` — interface, line 2362
- `export interface IngestJobResult` — interface, line 2368
- `export interface IngestJobError` — interface, line 2386
- `export interface IngestJobDto` — interface, line 2392
- `export interface IngestJobsSnapshot` — interface, line 2411
- `export type PdfEngine = "auto" | "marker" | "pypdf" | "native"` — type, line 2416
- `export interface StartIngestInput` — interface, line 2418
- `export type DurableIngestStatus = | "queued" | "running" | "waiting_for_input" | "completed" | "failed" | "blocked" | "cancelled"` — type, line 2427
- `export interface IngestJobView` — interface, line 2436
- `export interface IngestBatchDto` — interface, line 2475
- `export interface IngestBatchesSnapshot` — interface, line 2493
- `export interface RetrySynthesisInput` — interface, line 2498
- `export interface SynthesisCandidateSummary` — interface, line 2513
- `export interface StartImportBatchInput` — interface, line 2524
- `export type SourceReadiness = "ready" | "processing" | "needs_extraction"` — type, line 2542
- `export interface SourceLibraryCard` — interface, line 2544
- `export interface SourceDeletionCollectionImpact` — interface, line 2565
- `export interface SourceDeletionPlanDto` — interface, line 2573
- `export interface SourceDeletionResultDto` — interface, line 2591
- `export interface SourceLibrarySnapshot` — interface, line 2599
- `export interface UnitInventoryMarker` — interface, line 2606
- `export interface OutlineUnit` — interface, line 2612
- `export interface SelectionPreviewDto` — interface, line 2630
- `export interface EffectiveUnitDto` — interface, line 2642
- `export interface EffectiveOutlineDto` — interface, line 2652
- `export interface UnitSelectionState` — interface, line 2658
- `export interface SourceOutline` — interface, line 2665
- `export interface SaveUnitSelectionInput` — interface, line 2683
- `export interface SourceSetScopeDto` — interface, line 2692
- `export interface SourceSetMemberDto` — interface, line 2697
- `export interface SourceSetDto` — interface, line 2705
- `export interface SourceSetSummaryDto` — interface, line 2713
- `export interface SourceSetsSnapshot` — interface, line 2720
- `export interface CoverageReadinessFlag` — interface, line 2725
- `export interface SourceCoverageDto` — interface, line 2730
- `export interface CoverageRollupDto` — interface, line 2741
- `export interface StartInventoryInput` — interface, line 2750
- `export interface CreateStudyMapInput` — interface, line 2759
- `export interface BuildStudyMapInput` — interface, line 2768
- `export interface StudyMapDto` — interface, line 2778
- `export type StartingLevel = "new_to_this" | "some_exposure" | "comfortable" | "strong_background"` — type, line 2797
- `export type AuthoringPreset = "narrow_adjunct"` — type, line 2798
- `export interface StudyMapBriefDto` — interface, line 2800
- `export interface RungVariantRequestDto` — interface, line 2826
- `export interface ProbeRemintResultDto` — interface, line 2841
- `export interface RungVariantRequestResultDto` — interface, line 2851
- `export interface LearnerProfileDto` — interface, line 2862
- `export interface PlanQuickAddInput` — interface, line 2869
- `export interface ConfirmQuickAddInput` — interface, line 2875
- `export interface ProposeFacetMergeInput` — interface, line 2885
- `export interface QuickAddConsentDto` — interface, line 2893
- `export interface QuickAddConfirmationDto` — interface, line 2901
- `export interface QuickAddPlanDto` — interface, line 2919
- `export interface QuickAddResultDto` — interface, line 2942
- `export interface SpanViewInput` — interface, line 2952
- `export interface SpanNeighborDto` — interface, line 2960
- `export interface SpanViewDto` — interface, line 2969
- `export interface FacetContractCardDto` — interface, line 2998
- `export interface IdentifiabilityWarningDto` — interface, line 3017
- `export interface MeasurementRankDto` — interface, line 3032
- `export interface SubjectRegistryDto` — interface, line 3044
- `export interface FacetMergeResultDto` — interface, line 3054
- `export interface AcquisitionPreviewItem` — interface, line 3062
- `export interface AcquisitionPreview` — interface, line 3078
- `export interface BuildPlanStage` — interface, line 3090
- `export interface BuildPlanSource` — interface, line 3100
- `export interface BuildPlan` — interface, line 3114
- `export interface BuildPlanSelectionInput` — interface, line 3139
- `export interface ExtractionRepairConsent` — interface, line 3144
- `export interface StartExtractionRepairInput` — interface, line 3152
- `export interface ConceptGraphLearningObject` — interface, line 3161
- `export interface ConceptGraphNode` — interface, line 3167
- `export interface ConceptGraphEdge` — interface, line 3178
- `export interface ConceptGraphSnapshot` — interface, line 3186
- `export interface VaultTreeNode` — interface, line 3194
- `export interface VaultTreeSnapshot` — interface, line 3202
- `export interface VaultFileContent` — interface, line 3208
- `export interface SqliteTableInfo` — interface, line 3224
- `export interface SqliteTablesSnapshot` — interface, line 3229
- `export interface SqliteColumn` — interface, line 3235
- `export interface SqliteRow` — interface, line 3244
- `export interface SqliteTableSnapshot` — interface, line 3249
- `export type SqliteExecResult = |` — type, line 3260
- `export type ProposalDecision = "pending" | "accepted" | "rejected"` — type, line 3264
- `export type ProposalReviewRoute = "auto_apply" | "review_required" | "reject"` — type, line 3265
- `export interface ProposalSourceRefDto` — interface, line 3267
- `export interface ProposalItemDto` — interface, line 3273
- `export interface ProposalAgentRunDto` — interface, line 3295
- `export interface ProposalDecisionCounts` — interface, line 3307
- `export interface ProposalBatchDto` — interface, line 3313
- `export interface ProposalsSnapshot` — interface, line 3325
- `export interface EntitySourceLink` — interface, line 3336
- `export interface SourceConflictRef` — interface, line 3351
- `export interface NotationMappingRef` — interface, line 3362
- `export interface IntroducedBy` — interface, line 3371
- `export interface EntityProvenance` — interface, line 3380
- `export interface GoalPaceDto` — interface, line 3395
- `export interface GoalLatestExamDto` — interface, line 3406
- `export interface GoalReportSummaryDto` — interface, line 3411
- `export type MeasurementStateDto = "measured" | "inferred" | "claimed" | "unknown"` — type, line 3452
- `export interface GoalAtRiskFacetDto` — interface, line 3454
- `export interface ComponentReadinessDto` — interface, line 3485
- `export interface RecipeProjectionDto` — interface, line 3493
- `export interface BlueprintProjectionDto` — interface, line 3501
- `export interface LoReadinessDto` — interface, line 3509
- `export interface GoalDto` — interface, line 3517
- `export interface GoalsListSnapshot` — interface, line 3539
- `export interface GoalReportSnapshot` — interface, line 3544
- `export interface TraceTargetDto` — interface, line 3557
- `export interface TraceCriterionDto` — interface, line 3563
- `export interface AttemptTraceDto` — interface, line 3578
- `export interface CapabilityGridCellDto` — interface, line 3590
- `export interface CapabilityGridDto` — interface, line 3604
- `export interface CapabilityGridResult` — interface, line 3612
- `export interface DemonstratedTimelinePointDto` — interface, line 3618
- `export interface ObservationDerivationDto` — interface, line 3634
- `export interface ReadyCapabilitySliceDto` — interface, line 3643
- `export interface ReadyDerivationDto` — interface, line 3652
- `export interface FacetEvidenceTimelineDto` — interface, line 3667
- `export interface GoalSeriesPointDto` — interface, line 3679
- `export interface GoalSeriesSnapshot` — interface, line 3696
- `export interface GoalFeasibilityInput` — interface, line 3702
- `export interface GoalMaterialGap` — interface, line 3715
- `export interface GoalFeasibilityResult` — interface, line 3722
- `export interface GenerateStarterPracticeResult` — interface, line 3733
- `export interface GenerateCommissioningPracticeResult` — interface, line 3743
- `export interface ReviewCountsDto` — interface, line 3759
- `export interface CreateGoalInput` — interface, line 3772
- `export interface CreateGoalResult` — interface, line 3787
- `export type CalibrationSessionStatus = "active" | "completed" | "stopped" | "expired"` — type, line 3795
- `export interface CalibrationEpisodeDto` — interface, line 3797
- `export interface CalibrationNextTargetDto` — interface, line 3807
- `export interface StartCalibrationSessionInput` — interface, line 3816
- `export interface CalibrationSessionProgressDto` — interface, line 3823
- `export interface DialogueTurnDto` — interface, line 3843
- `export interface BeginProbeDialogueResult` — interface, line 3853
- `export interface NextProbeDialogueTurnResult` — interface, line 3860
- `export interface RecordProbeDialogueTurnResult` — interface, line 3867
- `export interface EndProbeDialogueResult` — interface, line 3873
- `export interface ExamStatusSnapshot` — interface, line 3880
- `export interface ExamItemDto` — interface, line 3896
- `export interface ExamSessionSnapshot` — interface, line 3908
- `export interface ExamAnswerResult` — interface, line 3920
- `export interface ExamFacetOutcomeDto` — interface, line 3928
- `export interface ExamItemRepairDto` — interface, line 3938
- `export interface ExamItemOutcomeDto` — interface, line 3951
- `export interface ExamReportSnapshot` — interface, line 3963
- `export interface StudyMapDiffDto` — interface, line 3976
- `export interface MergeReviewProposalDto` — interface, line 3987
- `export interface AppendResultDto` — interface, line 3995
- `export interface AppendSourceInput` — interface, line 4013
- `export interface RefreshResultDto` — interface, line 4022
- `export interface RefreshRevisionInput` — interface, line 4035
- `export type MaintenanceSeverity = "info" | "warning" | "action_needed"` — type, line 4044
- `export interface MaintenanceNoticeDto` — interface, line 4046
- `export interface MaintenanceFeedSnapshot` — interface, line 4065
- `export interface MeasurementMetricDto` — interface, line 4073
- `export interface ReachabilityCellDto` — interface, line 4086
- `export interface MeasurementHealthDto` — interface, line 4095
- `export interface InstrumentAuditDto` — interface, line 4286
- `export type ConflictResolutionKind = | "prefer_for_context" | "keep_both_scoped" | "notation_mapping" | "dismiss"` — type, line 4351
- `export interface SourceConflictDto` — interface, line 4357
- `export interface ResolveConflictInput` — interface, line 4378
- `export interface FacetCapabilityStateDto` — interface, line 4385
- `export interface PredictedScoreDto` — interface, line 4394
- `export interface TaskFamilyReadinessDto` — interface, line 4401
- `export interface ExamReadinessReportDto` — interface, line 4413
- `export type ClaimClass = "estimate" | "diagnosis" | "policy" | "ledger_fact"` — type, line 4426
- `export type ClaimTemperature = "hot" | "cold"` — type, line 4427
- `export interface ClaimCandidateDto` — interface, line 4429
- `export interface PresentedClaimDto extends ClaimCandidateDto` — interface, line 4444
- `export interface HypothesisEventDto` — interface, line 4451
- `export type BeliefWithdrawalReason = | "contradicted_by_trace" | "superseded" | "adjudicated" | "retired_misdiagnosed"` — type, line 4470
- `export interface ReviewChangelogEntryDto` — interface, line 4476
- `export interface WorkingHypothesisDto` — interface, line 4517
- `export interface ReviewLogDto` — interface, line 4530
- `export interface RemediationEpisodeDto` — interface, line 4536
- `export interface RemediationCaseDto` — interface, line 4551
- `export interface RemediationDto` — interface, line 4562
- `export interface StartRemediationDto` — interface, line 4578
- `export interface ForecastTrackRecordDto` — interface, line 4589
- `export interface CalibrationBinDto` — interface, line 4597
- `export interface AnswerCalibrationReportDto` — interface, line 4605
- `export interface OverconfidentFacetDto` — interface, line 4634
- `export interface OverconfidenceSnapshot` — interface, line 4645
- `export interface StartOverconfidenceProbeResult` — interface, line 4651
- `export interface ReentrySlippedFacetDto` — interface, line 4660
- `export interface ReentrySummaryDto` — interface, line 4667
- `export interface ReentrySummarySnapshot` — interface, line 4678
- `export interface DecayPressureFacetDto` — interface, line 4685
- `export interface DecayPressureDto` — interface, line 4694
- `export interface DecayPressureSnapshot` — interface, line 4700
- `export type GraphEditItemType = | "concept_edge" | "learning_object" | "task_blueprint" | "concept"` — type, line 4713
- `export type GraphEditOperation = "create" | "update" | "delete"` — type, line 4719
- `export interface GraphEditInput` — interface, line 4723
- `export interface ProposeGraphEditsInput` — interface, line 4730
- `export interface GraphEditItemDto` — interface, line 4738
- `export interface ProposeGraphEditsResult extends ProposalsSnapshot` — interface, line 4751
- `export interface QueueRestructureRequestInput` — interface, line 4756
- `export interface RestructureRequestDto` — interface, line 4765
- `export interface QueueRestructureRequestResult` — interface, line 4775
- `export type EdgeDirectionResolution = "keep" | "flip" | "retype_related" | "retire"` — type, line 4780
- `export interface ResolveEdgeDirectionInput` — interface, line 4782
- `export interface EdgeDirectionResolutionDto` — interface, line 4791
- `export interface ResolveEdgeDirectionResult extends ProposalsSnapshot` — interface, line 4801
- `export interface FacetDetailContractDto` — interface, line 4807
- `export interface FacetLockReasonDto` — interface, line 4821
- `export interface FacetLockDto` — interface, line 4826
- `export interface FacetMembershipRowDto` — interface, line 4832
- `export interface FacetCapabilityLedgerRowDto` — interface, line 4842
- `export interface FacetEvidenceDto` — interface, line 4854
- `export interface FacetDetailDto` — interface, line 4861
- `export interface FacetSummaryDto` — interface, line 4873
- `export interface FacetListDto` — interface, line 4881
- `export interface PreviewEdgeInput` — interface, line 4888
- `export interface PreviewKnowledgeMapInput` — interface, line 4894
- `export interface KnowledgeMapPreviewPoint` — interface, line 4899
- `export interface KnowledgeMapPreviewDto` — interface, line 4907
- `export interface PreviewBlueprintReadinessInput` — interface, line 4916
- `export interface BlueprintReadinessSummaryDto` — interface, line 4923
- `export interface BlueprintReadinessPreviewDto` — interface, line 4928
- `export type GraphEditorNoticeType = "ambiguous_edge_direction" | "restructure_request"` — type, line 4944
- `export interface AmbiguousEdgeDirectionDetail` — interface, line 4949
- `export interface RestructureRequestDetail` — interface, line 4968
- `export type RecipeCapability = | "retrieval" | "schema_interpretation" | "procedure_execution" | "method_selection" | "coordination"` — type, line 4984
- `export type RecipeModality = | "hard" | "path_specific" | "facilitating" | "instructional_order"` — type, line 4992
- `export interface RecipeComponentDto` — interface, line 4998
- `export interface BlueprintRecipeDto` — interface, line 5004
- `export interface LoBlueprintDto` — interface, line 5012
- `export interface CreateVaultInput` — interface, line 5022
- `export interface CreateVaultResult` — interface, line 5031
- `export interface GpInterval` — interface, line 5046
- `export type GpCalibrationStatus = "heuristic" | "simulation_validated" | "live_calibrated"` — type, line 5054
- `export type GpClaimLanguage = "provisional" | "calibrated" | "insufficient"` — type, line 5055
- `export interface BlueprintExemplarDto` — interface, line 5058
- `export interface BlueprintVersionDto` — interface, line 5067
- `export interface ExemplarPoolItemDto` — interface, line 5079
- `export interface ExemplarPoolEntryDto` — interface, line 5087
- `export interface ExemplarPoolSnapshot` — interface, line 5093
- `export interface ComposeDraftResult` — interface, line 5098
- `export interface ConfirmReceiptDto` — interface, line 5110
- `export interface RunNextActionDto` — interface, line 5126
- `export interface RunHistoryEntryDto` — interface, line 5131
- `export interface RunStateDto` — interface, line 5138
- `export interface RunAdvanceResultDto` — interface, line 5151
- `export type BoundaryCellState = "demonstrated" | "developing" | "untested" | "weak" | "contested"` — type, line 5158
- `export interface BoundaryCellDto` — interface, line 5159
- `export interface BoundaryDiffDto` — interface, line 5169
- `export interface AssessOpenDto` — interface, line 5179
- `export interface AssessReviewStateDto` — interface, line 5199
- `export interface AssessResultDto` — interface, line 5205
- `export interface DepthEdgeDto` — interface, line 5231
- `export interface DepthInvitationDto` — interface, line 5244
- `export interface DepthInvitationResultDto` — interface, line 5258
- `export interface AcceptEdgeResultDto` — interface, line 5263
- `export interface RestoreDto` — interface, line 5271
- `export interface LadderStageDto` — interface, line 5286
- `export interface LadderPolicyDto` — interface, line 5301
- `export interface LadderStatusDto` — interface, line 5314
- `export interface LadderAdvanceResultDto` — interface, line 5320
- `export interface PoolSurfaceDto` — interface, line 5327
- `export interface PoolDto` — interface, line 5334
- `export interface PoolStatusDto` — interface, line 5345
- `export interface PoolAnchorCandidateDto` — interface, line 5351
- `export interface PoolForRunDto` — interface, line 5356
- `export interface ServedSurfaceDto` — interface, line 5372
- `export interface PoolNextSurfaceDto` — interface, line 5383
- `export interface TriageRouteDto` — interface, line 5394
- `export interface TriageAlternativeDto` — interface, line 5402
- `export interface TriageResultDto` — interface, line 5407
- `export interface RunListEntryDto` — interface, line 5432
- `export interface RunListDto` — interface, line 5441
- `export interface TriageTraceEntryDto` — interface, line 5447
- `export interface TriageStatusDto` — interface, line 5460
- `export interface ReaderPromptContractDto` — interface, line 5468
- `export type ReaderAnswerMode = "answer_directly" | "help_me_reason" | "ask_me_first"` — type, line 5481
- `export interface ReaderAskInput` — interface, line 5484
- `export interface ReaderAnswerDto` — interface, line 5497
- `export interface ReaderAskHistoryExchangeDto` — interface, line 5511
- `export interface ReaderAskHistoryDto` — interface, line 5521
- `export type ReaderDisposition = | "comprehension_only" | "check_once_later" | "keep_developing" | "reference_only"` — type, line 5527
- `export interface ReaderDispositionResultDto` — interface, line 5532
- `export type ReaderAnchorStatus = | "exact" | "reanchored" | "needs_reanchor" | "orphaned" | "manually_anchored"` — type, line 5540
- `export type ReaderBlockHealthStatus = "ok" | "suspect" | "failed" | "unknown"` — type, line 5547
- `export type ReaderRecommendedView = "derived" | "crop_adjacent" | "crop_default" | "warn_link"` — type, line 5548
- `export interface ReaderWatchPausePointDto` — interface, line 5553
- `export interface ReaderWatchPlanDto` — interface, line 5564
- `export interface ReaderRenderBlockDto` — interface, line 5572
- `export interface ReaderRenderViewDto` — interface, line 5590
- `export interface ReaderSuggestedPassageDto` — interface, line 5606
- `export interface ReaderSectionQuestionDto` — interface, line 5615
- `export interface ReaderAuthoredQuestionDto` — interface, line 5642
- `export interface ReaderAuthorSectionQuestionDto` — interface, line 5654
- `export interface ReaderSourceSearchHitDto` — interface, line 5662
- `export interface ReaderSourceSearchDto` — interface, line 5672
- `export interface ReaderSectionProgressDto` — interface, line 5680
- `export interface ReaderProgressListDto` — interface, line 5690
- `export interface ReaderMarkProgressResultDto` — interface, line 5696
- `export interface ReaderGuideSectionDto` — interface, line 5703
- `export interface ReaderGuidePlanDto` — interface, line 5713
- `export interface ReaderPdfBlockDto` — interface, line 5729
- `export interface ReaderPdfViewDto` — interface, line 5741
- `export interface ReaderRawSelectionNode` — interface, line 5752
- `export interface ReaderRawSelection` — interface, line 5766
- `export interface ReaderTranslateSelectionInput` — interface, line 5773
- `export interface ReaderAnchorSegmentDto` — interface, line 5778
- `export interface ReaderTranslationDto` — interface, line 5788
- `export interface ReaderCaptureInput` — interface, line 5796
- `export interface ReaderCaptureReceiptDto` — interface, line 5808
- `export interface ReaderCreateAnnotationInput` — interface, line 5820
- `export interface ReaderAnnotationResultDto` — interface, line 5831
- `export interface ReaderBlockRegionDto` — interface, line 5838
- `export interface ReaderInvokePresetInput` — interface, line 5850
- `export interface ReaderPresetReceiptDto extends ReaderCaptureReceiptDto` — interface, line 5863
- `export interface ReaderImportExerciseInput` — interface, line 5872
- `export interface ReaderExerciseImportReceiptDto` — interface, line 5881
- `export interface ReaderExerciseImportedItem` — interface, line 5886
- `export interface ReaderExerciseImportSkip` — interface, line 5900
- `export interface ReaderExerciseImportResult` — interface, line 5906
- `export interface ReaderExerciseImportStatusDto` — interface, line 5913
- `export interface ReaderAuthorQAInput` — interface, line 5921
- `export interface ReaderAuthoredCardDto` — interface, line 5931
- `export interface ReaderCoachSuggestion` — interface, line 5943
- `export interface ReaderCoachLintDto` — interface, line 5947
- `export interface ReaderMaintainInput` — interface, line 5953
- `export interface ReaderArcDto` — interface, line 5968
- `export interface ReaderRestorationAnnotationDto` — interface, line 5982
- `export interface ReaderRestorationDto` — interface, line 5993
- `export interface ReaderSetModeResultDto` — interface, line 6006
- `export interface ReaderQuestionControlResultDto` — interface, line 6012
- `export interface ReaderEnqueueRequestInput` — interface, line 6019
- `export interface ReaderRequestScopeDto` — interface, line 6031
- `export interface ReaderEnqueueRequestDto` — interface, line 6037
- `export interface ReaderRequestRow` — interface, line 6053
- `export interface StubDiagnosticPackDto` — interface, line 6068
- `export interface StubPoolSurfacesDto` — interface, line 6072
- `export type AdjudicationVerdict = | "correct" | "wrong_anchor" | "wrong_repair" | "should_have_abstained" | "correctly_abstained" | "should_not_have_abstained"` — type, line 6084
- `export type AdjudicationQueueReason = string` — type, line 6093
- `export interface AdjudicationAnchorDto` — interface, line 6095
- `export interface AdjudicationRepairClassOptionDto` — interface, line 6106
- `export interface AdjudicationShownToLearnerDto` — interface, line 6113
- `export interface AdjudicationCaseDto` — interface, line 6133
- `export interface AdjudicationQueueDto` — interface, line 6160
- `export interface AdjudicationRecordInput` — interface, line 6167
- `export interface AdjudicationBeliefEffectDto` — interface, line 6186
- `export interface AdjudicationOutcomeDto` — interface, line 6195
- `export interface AdjudicationRecordResultDto` — interface, line 6204
- `export interface AdjudicationScoreboardGroupDto` — interface, line 6221
- `export interface AdjudicationScoreboardDto` — interface, line 6243

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `AcceptEdgeResultDto`, `AcquisitionPreview`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationRecordResultDto`, `AdjudicationScoreboardDto`, `AnimationRuntimeDto`, `AnswerCalibrationReportDto`, `AnswerGradingClarificationResultDto`, `AppSnapshot`, `AppendResultDto`, `AppendSourceInput`, `AskTutorQuestionInput`, `AssessOpenDto`, `AssessResultDto`, `AttemptResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `BeginProbeDialogueResult`, `BlueprintReadinessPreviewDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `BuildPlan`, `BuildPlanSelectionInput`, `BuildStudyMapInput`, `CalibrationSessionProgressDto`, `CapabilityGridResult`, `CausalProbeDeferResultDto`, `CausalProbeOfferResultDto`, `CausalRepairStatusResultDto`, `ClaimCandidateDto`, `CliCommandResult`, `CommandError`, `ComposeDraftResult`, `ConceptAnimationDto`, `ConceptGraphSnapshot`, `ConfirmQuickAddInput`, `ConfirmReceiptDto`, `CreateGoalInput`, `CreateGoalResult`, `CreateStudyMapInput`, `CreateVaultInput`, `CreateVaultResult`, `DecayPressureSnapshot`, `DepthInvitationResultDto`, `DetectProviderCapabilitiesInput`, `EffectiveOutlineDto`, `ElicitingResponseResultDto`, `EndProbeDialogueResult`, `EntityProvenance`, `ExamAnswerResult`, `ExamReadinessReportDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`, `ExamStatusSnapshot`, `ExemplarPoolSnapshot`, `FacetDetailDto`, `FacetEvidenceTimelineDto`, `FacetListDto`, `FacetMasterySnapshot`, `FacetMergeResultDto`, `FeedbackBundle`, `ForecastTrackRecordDto`, `GenerateCommissioningPracticeResult`, `GenerateStarterPracticeResult`, `GetNextProbeItemDto`, `GoalDto`, `GoalFeasibilityInput`, `GoalFeasibilityResult`, `GoalReportSnapshot`, `GoalSeriesSnapshot`, `GoalsListSnapshot`, `GradingClarificationResultDto`, `GradingProviderResult`, `GuidedRedoDto`, `HypothesisEventDto`, `IngestBatchDto`, `IngestBatchesSnapshot`, `IngestBudgetsDto`, `IngestJobDto`, `IngestJobsSnapshot`, `IngestSourceClassification`, `InspectorEntity`, `KnowledgeMapHistory`, `KnowledgeMapPreviewDto`, `KnowledgeMapSnapshot`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `LearnerProfileDto`, `MaintenanceFeedSnapshot`, `MaintenanceNoticeDto`, `MeasurementHealthDto`, `NextProbeDialogueTurnResult`, `OpenrouterKeyResult`, `OverconfidenceSnapshot`, `PlanQuickAddInput`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `PoolStatusDto`, `PracticeItemDetail`, `PracticeSubmissionAcknowledgementDto`, `PracticeSubmissionRecoveryDto`, `PresentedClaimDto`, `PreviewBlueprintReadinessInput`, `PreviewKnowledgeMapInput`, `PrimedRetryResultDto`, `ProbeContractDto`, `ProbeRemintResultDto`, `PromoteTutorQuestionResult`, `PromotionIntent`, `ProposalsSnapshot`, `ProposeFacetMergeInput`, `ProposeGraphEditsInput`, `ProposeGraphEditsResult`, `ProviderCapabilitiesDto`, `QuestionQueueSnapshot`, `QuestionResolution`, `QueueInput`, `QueueRestructureRequestInput`, `QueueRestructureRequestResult`, `QueueRevisionDto`, `QueueSnapshot`, `QuickAddConfirmationDto`, `QuickAddPlanDto`, `QuickAddResultDto`, `ReaderAnnotationResultDto`, `ReaderAnswerDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderAskHistoryDto`, `ReaderAskInput`, `ReaderAuthorQAInput`, `ReaderAuthorSectionQuestionDto`, `ReaderAuthoredCardDto`, `ReaderAuthoredQuestionDto`, `ReaderBlockRegionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderCoachLintDto`, `ReaderCreateAnnotationInput`, `ReaderDisposition`, `ReaderDispositionResultDto`, `ReaderEnqueueRequestDto`, `ReaderEnqueueRequestInput`, `ReaderExerciseImportReceiptDto`, `ReaderExerciseImportStatusDto`, `ReaderGuidePlanDto`, `ReaderImportExerciseInput`, `ReaderInvokePresetInput`, `ReaderMaintainInput`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderProgressListDto`, `ReaderPromptContractDto`, `ReaderQuestionControlResultDto`, `ReaderRenderViewDto`, `ReaderRequestRow`, `ReaderRestorationDto`, `ReaderSetModeResultDto`, `ReaderSourceSearchDto`, `ReaderTranslateSelectionInput`, `ReaderTranslationDto`, `ReaderWatchPlanDto`, `RecentIngestsSnapshot`, `RecordProbeDialogueTurnResult`, `ReentrySummarySnapshot`, `RefreshResultDto`, `RefreshRevisionInput`, `RemediationDto`, `RequestConceptAnimationResult`, `ResolveConflictInput`, `ResolveEdgeDirectionInput`, `ResolveEdgeDirectionResult`, `ResolveQuestionEventResult`, `RestoreDto`, `RetirementReason`, `RetrySynthesisInput`, `ReviewCountsDto`, `ReviewLogDto`, `RunAdvanceResultDto`, `RunListDto`, `RunStateDto`, `RungVariantRequestDto`, `RungVariantRequestResultDto`, `RuntimeHealth`, `SaveUnitSelectionInput`, `SchedulerExplanationDto`, `SelectionPreviewDto`, `SessionEndSummary`, `SessionSnapshot`, `SessionStartInput`, `SettingsDto`, `SourceConflictDto`, `SourceCoverageDto`, `SourceDeletionPlanDto`, `SourceDeletionResultDto`, `SourceLibrarySnapshot`, `SourceOutline`, `SourceSetDto`, `SourceSetsSnapshot`, `SpanViewDto`, `SpanViewInput`, `SqliteExecResult`, `SqliteTableSnapshot`, `SqliteTablesSnapshot`, `StartCalibrationSessionInput`, `StartExtractionRepairInput`, `StartImportBatchInput`, `StartIngestInput`, `StartInventoryInput`, `StartOverconfidenceProbeResult`, `StartRemediationDto`, `StartTeachBackInput`, `StartTeachBackResult`, `StartingLevel`, `StopProbeResultDto`, `StudyMapDto`, `SubjectRegistryDto`, `SubmitAttemptInput`, `SubmitTeachBackTurnInput`, `SynthesisCandidateSummary`, `TeachBackTurnResult`, `TranscriptionKeyResult`, `TriageResultDto`, `TriageStatusDto`, `TutorAnswerDto`, `TutorOpeningDto`, `TutorSaveNoteResult`, `TutorTranscriptInput`, `TutorTranscriptSnapshot`, `UnitSelectionState`, `UnresolvedCauseSelfReportResponse`, `UnresolvedCauseSelfReportResultDto`, `UpdateAiSettingsInput`, `UpdateAnimationSettingsInput`, `UpdateIngestSettingsInput`, `UpdateProviderModalitiesInput`, `VaultFileContent`, `VaultSummary`, `VaultTreeSnapshot`; references `AcceptEdgeResultDto`, `AcquisitionPreview`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationRecordResultDto`, `AdjudicationScoreboardDto`, `AnimationRuntimeDto`, `AnswerCalibrationReportDto`, `AnswerGradingClarificationResultDto`, `AppSnapshot`, `AppendResultDto`, `AppendSourceInput`, `AskTutorQuestionInput`, `AssessOpenDto`, `AssessResultDto`, `AttemptResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `BeginProbeDialogueResult`, `BlueprintReadinessPreviewDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `BuildPlan`, `BuildPlanSelectionInput`, `BuildStudyMapInput`, `CalibrationSessionProgressDto`, `CapabilityGridResult`, `CausalProbeDeferResultDto`, `CausalProbeOfferResultDto`, `CausalRepairStatusResultDto`, `ClaimCandidateDto`, `CliCommandResult`, `CommandError`, `ComposeDraftResult`, `ConceptAnimationDto`, `ConceptGraphSnapshot`, `ConfirmQuickAddInput`, `ConfirmReceiptDto`, `CreateGoalInput`, `CreateGoalResult`, `CreateStudyMapInput`, `CreateVaultInput`, `CreateVaultResult`, `DecayPressureSnapshot`, `DepthInvitationResultDto`, `DetectProviderCapabilitiesInput`, `EffectiveOutlineDto`, `ElicitingResponseResultDto`, `EndProbeDialogueResult`, `EntityProvenance`, `ExamAnswerResult`, `ExamReadinessReportDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`, `ExamStatusSnapshot`, `ExemplarPoolSnapshot`, `FacetDetailDto`, `FacetEvidenceTimelineDto`, `FacetListDto`, `FacetMasterySnapshot`, `FacetMergeResultDto`, `FeedbackBundle`, `ForecastTrackRecordDto`, `GenerateCommissioningPracticeResult`, `GenerateStarterPracticeResult`, `GetNextProbeItemDto`, `GoalDto`, `GoalFeasibilityInput`, `GoalFeasibilityResult`, `GoalReportSnapshot`, `GoalSeriesSnapshot`, `GoalsListSnapshot`, `GradingClarificationResultDto`, `GradingProviderResult`, `GuidedRedoDto`, `HypothesisEventDto`, `IngestBatchDto`, `IngestBatchesSnapshot`, `IngestBudgetsDto`, `IngestJobDto`, `IngestJobsSnapshot`, `IngestSourceClassification`, `InspectorEntity`, `KnowledgeMapHistory`, `KnowledgeMapPreviewDto`, `KnowledgeMapSnapshot`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `LearnerProfileDto`, `MaintenanceFeedSnapshot`, `MaintenanceNoticeDto`, `MeasurementHealthDto`, `NextProbeDialogueTurnResult`, `OpenrouterKeyResult`, `OverconfidenceSnapshot`, `PlanQuickAddInput`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `PoolStatusDto`, `PracticeItemDetail`, `PracticeSubmissionAcknowledgementDto`, `PracticeSubmissionRecoveryDto`, `PresentedClaimDto`, `PreviewBlueprintReadinessInput`, `PreviewKnowledgeMapInput`, `PrimedRetryResultDto`, `ProbeContractDto`, `ProbeRemintResultDto`, `PromoteTutorQuestionResult`, `PromotionIntent`, `ProposalsSnapshot`, `ProposeFacetMergeInput`, `ProposeGraphEditsInput`, `ProposeGraphEditsResult`, `ProviderCapabilitiesDto`, `QuestionQueueSnapshot`, `QuestionResolution`, `QueueInput`, `QueueRestructureRequestInput`, `QueueRestructureRequestResult`, `QueueRevisionDto`, `QueueSnapshot`, `QuickAddConfirmationDto`, `QuickAddPlanDto`, `QuickAddResultDto`, `ReaderAnnotationResultDto`, `ReaderAnswerDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderAskHistoryDto`, `ReaderAskInput`, `ReaderAuthorQAInput`, `ReaderAuthorSectionQuestionDto`, `ReaderAuthoredCardDto`, `ReaderAuthoredQuestionDto`, `ReaderBlockRegionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderCoachLintDto`, `ReaderCreateAnnotationInput`, `ReaderDisposition`, `ReaderDispositionResultDto`, `ReaderEnqueueRequestDto`, `ReaderEnqueueRequestInput`, `ReaderExerciseImportReceiptDto`, `ReaderExerciseImportStatusDto`, `ReaderGuidePlanDto`, `ReaderImportExerciseInput`, `ReaderInvokePresetInput`, `ReaderMaintainInput`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderProgressListDto`, `ReaderPromptContractDto`, `ReaderQuestionControlResultDto`, `ReaderRenderViewDto`, `ReaderRequestRow`, `ReaderRestorationDto`, `ReaderSetModeResultDto`, `ReaderSourceSearchDto`, `ReaderTranslateSelectionInput`, `ReaderTranslationDto`, `ReaderWatchPlanDto`, `RecentIngestsSnapshot`, `RecordProbeDialogueTurnResult`, `ReentrySummarySnapshot`, `RefreshResultDto`, `RefreshRevisionInput`, `RemediationDto`, `RequestConceptAnimationResult`, `ResolveConflictInput`, `ResolveEdgeDirectionInput`, `ResolveEdgeDirectionResult`, `ResolveQuestionEventResult`, `RestoreDto`, `RetirementReason`, `RetrySynthesisInput`, `ReviewCountsDto`, `ReviewLogDto`, `RunAdvanceResultDto`, `RunListDto`, `RunStateDto`, `RungVariantRequestDto`, `RungVariantRequestResultDto`, `RuntimeHealth`, `SaveUnitSelectionInput`, `SchedulerExplanationDto`, `SelectionPreviewDto`, `SessionEndSummary`, `SessionSnapshot`, `SessionStartInput`, `SettingsDto`, `SourceConflictDto`, `SourceCoverageDto`, `SourceDeletionPlanDto`, `SourceDeletionResultDto`, `SourceLibrarySnapshot`, `SourceOutline`, `SourceSetDto`, `SourceSetsSnapshot`, `SpanViewDto`, `SpanViewInput`, `SqliteExecResult`, `SqliteTableSnapshot`, `SqliteTablesSnapshot`, `StartCalibrationSessionInput`, `StartExtractionRepairInput`, `StartImportBatchInput`, `StartIngestInput`, `StartInventoryInput`, `StartOverconfidenceProbeResult`, `StartRemediationDto`, `StartTeachBackInput`, `StartTeachBackResult`, `StartingLevel`, `StopProbeResultDto`, `StudyMapDto`, `SubjectRegistryDto`, `SubmitAttemptInput`, `SubmitTeachBackTurnInput`, `SynthesisCandidateSummary`, `TeachBackTurnResult`, `TranscriptionKeyResult`, `TriageResultDto`, `TriageStatusDto`, `TutorAnswerDto`, `TutorOpeningDto`, `TutorSaveNoteResult`, `TutorTranscriptInput`, `TutorTranscriptSnapshot`, `UnitSelectionState`, `UnresolvedCauseSelfReportResponse`, `UnresolvedCauseSelfReportResultDto`, `UpdateAiSettingsInput`, `UpdateAnimationSettingsInput`, `UpdateIngestSettingsInput`, `UpdateProviderModalitiesInput`, `VaultFileContent`, `VaultSummary`, `VaultTreeSnapshot`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export: `CommandError`; references `CommandError`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export: `CommandError`; references `CommandError`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `AppSnapshot`, `GuidedRedoDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `TriageResultDto`; references `AppSnapshot`, `GuidedRedoDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `TriageResultDto`
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export: `CommandError`, `SourceSetDto`, `SourceSetSummaryDto`; references `CommandError`, `SourceSetDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `AdjudicationCaseDto`, `AdjudicationOutcomeDto`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationScoreboardDto`, `AdjudicationVerdict`; references `AdjudicationCaseDto`, `AdjudicationOutcomeDto`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationScoreboardDto`, `AdjudicationVerdict`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `AskTutorQuestionInput`, `CommandError`, `PromotionIntent`, `QuestionPromotionDto`, `QuestionPromotionRequestDto`, `TutorCitationDto`, `TutorQuestionContext`, `TutorQuestionEventDto`; references `AskTutorQuestionInput`, `CommandError`, `PromotionIntent`, `QuestionPromotionDto`, `QuestionPromotionRequestDto`, `TutorCitationDto`, `TutorQuestionContext`, `TutorQuestionEventDto`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export: `CommandError`, `RETIREMENT_REASONS`, `RetirementReason`; references `CommandError`, `RETIREMENT_REASONS`, `RetirementReason`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `CausalDivergenceAnchorDto`, `CausalEpisodeDto`, `CausalFeedbackDto`, `CausalHypothesisDto`, `CausalProbeOfferDto`, `CausalRepairActionId`, `CausalRepairStatusDto`, `CausalRepairStatusState`, `CausalTargetRefDto`, `RepairedTraceDto`, `UnresolvedCauseSelfReportResponse`; references `CausalDivergenceAnchorDto`, `CausalEpisodeDto`, `CausalFeedbackDto`, `CausalHypothesisDto`, `CausalProbeOfferDto`, `CausalRepairActionId`, `CausalRepairStatusDto`, `CausalRepairStatusState`, `CausalTargetRefDto`, `RepairedTraceDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export: `ClaimCandidateDto`, `PresentedClaimDto`; references `ClaimCandidateDto`, `PresentedClaimDto`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export: `CliCommandResult`, `SessionSnapshot`; references `CliCommandResult`, `SessionSnapshot`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export: `AnimationRuntimeDto`, `ConceptAnimationDto`, `StoryboardDto`; references `AnimationRuntimeDto`, `ConceptAnimationDto`, `StoryboardDto`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `CommandError`, `DialogueTurnDto`, `GuidedRedoDto`, `ProbeBlockEndDto`; references `CommandError`, `DialogueTurnDto`, `GuidedRedoDto`, `ProbeBlockEndDto`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export: `BlueprintVersionDto`, `CommandError`, `DepthEdgeDto`; references `BlueprintVersionDto`, `CommandError`, `DepthEdgeDto`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `FacetDetailDto`, `FacetSummaryDto`, `RestructureRequestDto`; references `FacetDetailDto`, `FacetSummaryDto`, `RestructureRequestDto`
- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `ClaimCandidateDto`, `ExamStatusSnapshot`, `GoalAtRiskFacetDto`, `GoalDto`, `GoalPaceDto`, `GoalReportSummaryDto`, `GoalSeriesPointDto`; references `ClaimCandidateDto`, `ExamStatusSnapshot`, `GoalAtRiskFacetDto`, `GoalDto`, `GoalPaceDto`, `GoalReportSummaryDto`, `GoalSeriesPointDto`
- [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]] — import-or-re-export: `GoalDto`; references `GoalDto`
- [[Reference/Desktop/TypeScript/components/GoalTrajectoryChart|src/components/GoalTrajectoryChart.tsx]] — import-or-re-export: `GoalSeriesPointDto`; references `GoalSeriesPointDto`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export: `ConceptGraphNode`, `CreateGoalResult`, `GoalFeasibilityResult`; references `ConceptGraphNode`, `CreateGoalResult`, `GoalFeasibilityResult`
- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export: `CommandError`, `DurableIngestStatus`, `IngestBatchDto`, `IngestJobView`, `SynthesisCandidateSummary`; references `CommandError`, `DurableIngestStatus`, `IngestBatchDto`, `IngestJobView`, `SynthesisCandidateSummary`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `AttemptInspectorDetail`, `CapabilityGridResult`, `ConceptInspectorDetail`, `ConceptReferenceDto`, `ErrorEventDto`, `InspectorEntity`, `InspectorSearchResult`, `LearningObjectDetail`, `MasteryDto`, `NoteInspectorDetail`, `PracticeItemDetail`, `ProbeEpisodeInspectorDetail`, `SchedulerComponents`, `SchedulerExplanationDto`; references `AttemptInspectorDetail`, `CapabilityGridResult`, `ConceptInspectorDetail`, `ConceptReferenceDto`, `ErrorEventDto`, `InspectorEntity`, `InspectorSearchResult`, `LearningObjectDetail`, `MasteryDto`, `NoteInspectorDetail`, `PracticeItemDetail`, `ProbeEpisodeInspectorDetail`, `SchedulerComponents`, `SchedulerExplanationDto`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export: `ItemPresentationDto`, `PresentationBlockDto`; references `ItemPresentationDto`, `PresentationBlockDto`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export: `AttemptTraceDto`, `CapabilityGridResult`, `ComponentReadinessDto`, `DemonstratedTimelinePointDto`, `FacetEvidenceTimelineDto`, `LoReadinessDto`, `ObservationDerivationDto`, `ReadyDerivationDto`, `TraceCriterionDto`, `UnresolvedCauseDto`, `UnresolvedCauseSelfReportResponse`; references `AttemptTraceDto`, `CapabilityGridResult`, `ComponentReadinessDto`, `DemonstratedTimelinePointDto`, `FacetEvidenceTimelineDto`, `LoReadinessDto`, `ReadyDerivationDto`, `TraceCriterionDto`, `UnresolvedCauseDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]] — import-or-re-export: `AudioMode`, `NativeModalityStateDto`, `PdfEngine`, `ProviderCapabilitiesDto`, `SettingsDto`, `SettingsProviderDto`; references `AudioMode`, `NativeModalityStateDto`, `PdfEngine`, `ProviderCapabilitiesDto`, `SettingsDto`, `SettingsProviderDto`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `StartingLevel`; references `StartingLevel`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export: `SpanNeighborDto`, `SpanViewDto`; references `SpanNeighborDto`, `SpanViewDto`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `BuildPlan`, `BuildPlanStage`, `CommandError`, `EffectiveOutlineDto`, `EffectiveUnitDto`, `IngestBudgetBoundsDto`, `IngestBudgetField`, `IngestBudgetsDto`, `OutlineUnit`, `SelectionPreviewDto`, `SourceOutline`, `StartExtractionRepairInput`; references `BuildPlan`, `BuildPlanStage`, `CommandError`, `EffectiveOutlineDto`, `EffectiveUnitDto`, `IngestBudgetBoundsDto`, `IngestBudgetField`, `IngestBudgetsDto`, `OutlineUnit`, `SelectionPreviewDto`, `SourceOutline`, `StartExtractionRepairInput`
- [[Reference/Desktop/TypeScript/components/PdfReaderPane|src/components/PdfReaderPane.tsx]] — import-or-re-export: `ReaderPdfBlockDto`; references `ReaderPdfBlockDto`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `CommandError`, `GuidedRedoDto`, `ProbeBlockEndDto`, `UnresolvedCauseSelfReportResponse`; references `CommandError`, `GuidedRedoDto`, `ProbeBlockEndDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export: `EntityProvenance`, `EntitySourceLink`; references `EntityProvenance`, `EntitySourceLink`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `CommandError`, `QuestionQueueRowDto`; references `CommandError`, `QuestionQueueRowDto`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `QuickAddPlanDto`, `StudyMapBriefDto`; references `QuickAddPlanDto`, `StudyMapBriefDto`
- [[Reference/Desktop/TypeScript/components/RepairAffordances|src/components/RepairAffordances.tsx]] — import-or-re-export: `CausalFeedbackDto`; references `CausalFeedbackDto`
- [[Reference/Desktop/TypeScript/components/RepairTrace|src/components/RepairTrace.tsx]] — import-or-re-export: `RepairedTraceDto`; references `RepairedTraceDto`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export: `SessionEndSummary`; references `SessionEndSummary`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `CommandError`, `SourceDeletionPlanDto`, `SourceLibraryCard`, `SourceReadiness`, `SourceSetDto`, `SourceSetSummaryDto`, `StudyMapBriefDto`; references `CommandError`, `SourceDeletionPlanDto`, `SourceLibraryCard`, `SourceReadiness`, `SourceSetDto`, `SourceSetSummaryDto`, `StudyMapBriefDto`
- [[Reference/Desktop/TypeScript/components/StudyMapBriefWizard|src/components/StudyMapBriefWizard.tsx]] — import-or-re-export: `StartingLevel`, `StudyMapBriefDto`; references `StartingLevel`, `StudyMapBriefDto`
- [[Reference/Desktop/TypeScript/components/TrackRecordView|src/components/TrackRecordView.tsx]] — import-or-re-export: `AnswerCalibrationReportDto`, `CalibrationBinDto`, `ForecastTrackRecordDto`; references `AnswerCalibrationReportDto`, `CalibrationBinDto`, `ForecastTrackRecordDto`
- [[Reference/Desktop/TypeScript/components/WhyDiagnosisOverlay|src/components/WhyDiagnosisOverlay.tsx]] — import-or-re-export: `TriageResultDto`; references `TriageResultDto`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export: `CommandError`; references `CommandError`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export: `ComposeDraftResult`, `ExemplarPoolEntryDto`, `GoalDto`, `RunListEntryDto`; references `ComposeDraftResult`, `ExemplarPoolEntryDto`, `GoalDto`, `RunListEntryDto`
- [[Reference/Desktop/TypeScript/components/goldenpath/TriageDecisionAid|src/components/goldenpath/TriageDecisionAid.tsx]] — import-or-re-export: `TriageResultDto`, `TriageRouteDto`; references `TriageResultDto`, `TriageRouteDto`
- [[Reference/Desktop/TypeScript/components/goldenpath/shared|src/components/goldenpath/shared.tsx]] — import-or-re-export: `BoundaryCellDto`, `BoundaryCellState`, `DepthEdgeDto`, `GpCalibrationStatus`, `GpClaimLanguage`, `GpInterval`, `LadderStageDto`, `ReaderDisposition`; references `BoundaryCellDto`, `BoundaryCellState`, `DepthEdgeDto`, `GpCalibrationStatus`, `GpClaimLanguage`, `GpInterval`, `LadderStageDto`, `ReaderDisposition`
- [[Reference/Desktop/TypeScript/components/graphedit/GeometryPreview|src/components/graphedit/GeometryPreview.tsx]] — import-or-re-export: `KnowledgeMapPreviewDto`; references `KnowledgeMapPreviewDto`
- [[Reference/Desktop/TypeScript/components/graphedit/SyllabusColumn|src/components/graphedit/SyllabusColumn.tsx]] — import-or-re-export: `ConceptGraphNode`; references `ConceptGraphNode`
- [[Reference/Desktop/TypeScript/components/graphedit/pending|src/components/graphedit/pending.ts]] — import-or-re-export: `ConceptGraphEdge`, `ConceptGraphNode`, `GraphEditInput`, `PreviewKnowledgeMapInput`; references `ConceptGraphEdge`, `ConceptGraphNode`, `GraphEditInput`, `PreviewKnowledgeMapInput`
- [[Reference/Desktop/TypeScript/components/recipeedit/RecipeTreeEditor|src/components/recipeedit/RecipeTreeEditor.tsx]] — import-or-re-export: `BlueprintReadinessPreviewDto`, `FacetSummaryDto`, `LoBlueprintDto`, `RecipeComponentDto`; references `BlueprintReadinessPreviewDto`, `FacetSummaryDto`, `LoBlueprintDto`, `RecipeComponentDto`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export: `CommandError`; references `CommandError`
- [[Reference/Desktop/TypeScript/fixtures/goldenpath/index|src/fixtures/goldenpath/index.ts]] — import-or-re-export: `AssessOpenDto`, `AssessResultDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `ConfirmReceiptDto`, `DepthInvitationResultDto`, `LadderPolicyDto`, `PoolDto`, `PoolNextSurfaceDto`, `ReaderPromptContractDto`, `RestoreDto`, `RunStateDto`, `TriageResultDto`; references `AssessOpenDto`, `AssessResultDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `ConfirmReceiptDto`, `DepthInvitationResultDto`, `LadderPolicyDto`, `PoolDto`, `PoolNextSurfaceDto`, `ReaderPromptContractDto`, `RestoreDto`, `RunStateDto`, `TriageResultDto`
- [[Reference/Desktop/TypeScript/fixtures/readerRenderView|src/fixtures/readerRenderView.ts]] — import-or-re-export: `ReaderRenderViewDto`; references `ReaderRenderViewDto`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export: `CalibrationSessionProgressDto`, `CommandError`, `GuidedRedoDto`; references `CalibrationSessionProgressDto`, `CommandError`, `GuidedRedoDto`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export: `CommandError`, `GuidedRedoDto`, `ProbeBlockEndDto`; references `CommandError`, `GuidedRedoDto`, `ProbeBlockEndDto`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `CommandError`, `ExamFacetOutcomeDto`, `ExamItemDto`, `ExamItemOutcomeDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`; references `CommandError`, `ExamFacetOutcomeDto`, `ExamItemDto`, `ExamItemOutcomeDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `GradingClarificationDto`, `GuidedRedoDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `PracticeItemDetail`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `UnresolvedCauseSelfReportResponse`; references `AnswerGradingClarificationResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `CandidateErrorTypeDto`, `CausalRepairStatusDto`, `ClaimCandidateDto`, `ColdCheckResultDto`, `CriterionEvidenceRowDto`, `ElicitingResponseResultDto`, `ErrorEventDto`, `FeedbackBundle`, `FollowupGateDiagnosticsDto`, `FollowupGateSignalDto`, `GradingClarificationDto`, `GuidedRedoDto`, `MasteryDto`, `MasteryStepDto`, `MatchedMisconceptionDto`, `PracticeItemDetail`, `RepairSuggestionDto`, `ResolvedSourceRefDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `AssessOpenDto`, `AssessResultDto`, `DepthInvitationResultDto`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `RestoreDto`, `RunStateDto`, `ServedSurfaceDto`, `TriageResultDto`, `TriageStatusDto`; references `AssessOpenDto`, `AssessResultDto`, `DepthInvitationResultDto`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `RestoreDto`, `RunStateDto`, `ServedSurfaceDto`, `TriageResultDto`, `TriageStatusDto`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `CommandError`, `ConceptGraphEdge`, `ConceptGraphNode`, `ConceptGraphSnapshot`, `GoalDto`, `GoalReportSnapshot`, `KnowledgeMapPreviewDto`; references `CommandError`, `ConceptGraphEdge`, `ConceptGraphNode`, `ConceptGraphSnapshot`, `GoalDto`, `GoalReportSnapshot`, `KnowledgeMapPreviewDto`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `AcquisitionPreviewItem`, `CommandError`, `IngestBatchDto`, `IngestJobDto`, `IngestJobPhase`, `IngestMode`, `PdfEngine`, `SourceLibraryCard`, `StartingLevel`; references `AcquisitionPreviewItem`, `CommandError`, `IngestBatchDto`, `IngestJobDto`, `IngestJobPhase`, `IngestMode`, `PdfEngine`, `SourceLibraryCard`, `StartingLevel`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `DecayPressureDto`, `KnowledgeFacetPoint`, `KnowledgeMapHistory`, `KnowledgeMapPoint`, `KnowledgeMapSnapshot`; references `DecayPressureDto`, `KnowledgeFacetPoint`, `KnowledgeMapHistory`, `KnowledgeMapPoint`, `KnowledgeMapSnapshot`
- [[Reference/Desktop/TypeScript/screens/KnowledgeStrataView|src/screens/KnowledgeStrataView.tsx]] — import-or-re-export: `KnowledgeMapHistory`, `KnowledgeMapPoint`; references `KnowledgeMapHistory`, `KnowledgeMapPoint`
- [[Reference/Desktop/TypeScript/screens/KnowledgeTerrainView|src/screens/KnowledgeTerrainView.tsx]] — import-or-re-export: `CapabilityArcStatus`, `KnowledgeFacetField`, `KnowledgeFacetPoint`; references `CapabilityArcStatus`, `KnowledgeFacetField`, `KnowledgeFacetPoint`
- [[Reference/Desktop/TypeScript/screens/KnowledgeWellView|src/screens/KnowledgeWellView.tsx]] — import-or-re-export: `DecayPressureDto`, `KnowledgeFacetField`, `KnowledgeFacetPoint`; references `DecayPressureDto`, `KnowledgeFacetField`, `KnowledgeFacetPoint`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `CoverageRollupDto`, `ProposalBatchDto`, `ProposalItemDto`, `ProposalsSnapshot`, `SourceSetSummaryDto`, `VaultFileContent`, `VaultTreeNode`, `VaultTreeSnapshot`; references `CoverageRollupDto`, `ProposalBatchDto`, `ProposalItemDto`, `ProposalsSnapshot`, `SourceSetSummaryDto`, `VaultFileContent`, `VaultTreeNode`, `VaultTreeSnapshot`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `AmbiguousEdgeDirectionDetail`, `AppendResultDto`, `ConflictResolutionKind`, `EdgeDirectionResolution`, `ExamReadinessReportDto`, `GenerateCommissioningPracticeResult`, `MaintenanceNoticeDto`, `MaintenanceSeverity`, `MeasurementHealthDto`, `RestructureRequestDetail`, `SourceConflictDto`, `SourceSetSummaryDto`; references `AmbiguousEdgeDirectionDetail`, `AppendResultDto`, `ConflictResolutionKind`, `EdgeDirectionResolution`, `ExamReadinessReportDto`, `GenerateCommissioningPracticeResult`, `MaintenanceNoticeDto`, `MaintenanceSeverity`, `MeasurementHealthDto`, `RestructureRequestDetail`, `SourceConflictDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `AttemptResultDto`, `AttemptType`, `CandidateErrorTypeDto`, `GuidedRedoDto`, `PracticeItemDetail`, `ProbeBlockEndDto`, `ProbeContractDto`, `RubricCriterionDto`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SessionSnapshot`, `TeachBackStateDto`, `TeachBackTurnDto`; references `AttemptResultDto`, `AttemptType`, `CandidateErrorTypeDto`, `GuidedRedoDto`, `PracticeItemDetail`, `ProbeBlockEndDto`, `ProbeContractDto`, `RubricCriterionDto`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SessionSnapshot`, `TeachBackStateDto`, `TeachBackTurnDto`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export: `ProposalBatchDto`, `ProposalItemDto`, `ProposalReviewRoute`, `ProposalSourceRefDto`, `ProposalsSnapshot`; references `ProposalBatchDto`, `ProposalItemDto`, `ProposalReviewRoute`, `ProposalSourceRefDto`, `ProposalsSnapshot`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderDisposition`, `ReaderExerciseImportResult`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderPdfViewDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `SourceLibraryCard`; references `ReaderAnswerMode`, `ReaderArcDto`, `ReaderCoachLintDto`, `ReaderDisposition`, `ReaderExerciseImportResult`, `ReaderGuidePlanDto`, `ReaderGuideSectionDto`, `ReaderPdfViewDto`, `ReaderPromptContractDto`, `ReaderRenderBlockDto`, `ReaderRenderViewDto`, `ReaderSourceSearchDto`, `ReaderWatchPlanDto`, `SourceLibraryCard`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export: `FacetContractCardDto`, `IdentifiabilityWarningDto`, `MeasurementRankDto`, `SubjectRegistryDto`; references `FacetContractCardDto`, `IdentifiabilityWarningDto`, `MeasurementRankDto`, `SubjectRegistryDto`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export: `CausalRepairStatusDto`, `SpanViewDto`, `StartRemediationDto`; references `CausalRepairStatusDto`, `SpanViewDto`, `StartRemediationDto`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export: `BeliefWithdrawalReason`, `ClaimCandidateDto`, `KnowledgeHistoryAttempt`, `ReviewChangelogEntryDto`, `ReviewLogDto`, `WorkingHypothesisDto`; references `BeliefWithdrawalReason`, `ClaimCandidateDto`, `KnowledgeHistoryAttempt`, `ReviewChangelogEntryDto`, `ReviewLogDto`, `WorkingHypothesisDto`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `AnimationRenderer`, `IngestBudgetField`, `IngestBudgetsDto`, `RuntimeHealth`, `SettingsDto`, `UseCaseChoiceInput`; references `AnimationRenderer`, `IngestBudgetField`, `IngestBudgetsDto`, `RuntimeHealth`, `SettingsDto`, `UseCaseChoiceInput`
- [[Reference/Desktop/TypeScript/screens/SqliteBrowser|src/screens/SqliteBrowser.tsx]] — import-or-re-export: `SqliteExecResult`, `SqliteTableInfo`, `SqliteTableSnapshot`; references `SqliteExecResult`, `SqliteTableInfo`, `SqliteTableSnapshot`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `QueueSnapshot`, `ScheduledItemDto`, `SessionSnapshot`, `StreakSummary`, `VaultSummary`; references `QueueSnapshot`, `ScheduledItemDto`, `SessionSnapshot`, `StreakSummary`, `VaultSummary`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `ClaimCandidateDto`, `DecayPressureDto`, `GoalDto`, `IngestBatchDto`, `OverconfidentFacetDto`, `PracticeItemDetail`, `QueueSection`, `QueueSnapshot`, `ReentrySummaryDto`, `ScheduledItemDto`, `SchedulerComponents`, `SessionEndSummary`, `SessionSnapshot`; references `ClaimCandidateDto`, `DecayPressureDto`, `GoalDto`, `IngestBatchDto`, `OverconfidentFacetDto`, `PracticeItemDetail`, `QueueSection`, `QueueSnapshot`, `ReentrySummaryDto`, `ScheduledItemDto`, `SchedulerComponents`, `SessionEndSummary`, `SessionSnapshot`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_build_study_map_routing.py](../../../../../../tests/test_build_study_map_routing.py) — cross-boundary name contract: references uniquely owned exported name `BuildStudyMapInput`; it does **not** directly execute this source module.
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct source contract: references the exact source path.
- [tests/test_ingest_latency_journey.py](../../../../../../tests/test_ingest_latency_journey.py) — cross-boundary name contract: references uniquely owned exported name `StartImportBatchInput`; it does **not** directly execute this source module.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/dto.ts](../../../../../../apps/learnloop-tauri/src/api/dto.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
