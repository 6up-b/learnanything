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
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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
| Source lines | 6109 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

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
- `export interface SettingsAiDto` — interface, line 64
- `export interface OpenrouterKeyStateDto` — interface, line 73
- `export interface KeyStateDto` — interface, line 79
- `export interface IngestBudgetsDto` — interface, line 86
- `export type IngestBudgetField = keyof IngestBudgetsDto` — type, line 94
- `export type IngestBudgetBoundsDto = Record<IngestBudgetField,` — type, line 98
- `export interface IngestProviderLimitsDto` — interface, line 102
- `export interface SettingsIngestDto` — interface, line 108
- `export interface SettingsDto` — interface, line 119
- `export interface UpdateIngestSettingsInput` — interface, line 127
- `export interface TranscriptionKeyResult` — interface, line 138
- `export interface AnimationRuntimeDto` — interface, line 145
- `export interface ConceptAnimationDto` — interface, line 155
- `export interface RequestConceptAnimationResult` — interface, line 175
- `export interface UseCaseChoiceInput` — interface, line 182
- `export interface UpdateAiSettingsInput` — interface, line 187
- `export interface OpenrouterKeyResult` — interface, line 192
- `export interface FacetMasteryLearningObject` — interface, line 200
- `export interface FacetMasteryPracticeItem` — interface, line 207
- `export interface FacetMasteryFacet` — interface, line 217
- `export interface FacetMasterySnapshot` — interface, line 229
- `export interface KnowledgeMapPoint` — interface, line 239
- `export interface KnowledgeMapSnapshot` — interface, line 257
- `export type CapabilityArcStatus = "demonstrated" | "required" | "absent"` — type, line 267
- `export interface KnowledgeFacetPoint` — interface, line 269
- `export interface KnowledgeFieldEdge` — interface, line 302
- `export interface KnowledgeNextGap` — interface, line 308
- `export interface KnowledgeFacetField` — interface, line 318
- `export interface KnowledgeHistoryAttempt` — interface, line 329
- `export interface KnowledgeHistorySeriesPoint` — interface, line 341
- `export interface KnowledgeMapHistory` — interface, line 349
- `export interface VaultSummary` — interface, line 356
- `export interface StreakSummary` — interface, line 373
- `export interface AppSnapshot` — interface, line 382
- `export interface SessionStartInput` — interface, line 391
- `export interface SessionSnapshot` — interface, line 398
- `export interface SessionEndSummary` — interface, line 410
- `export interface SessionCheckpoint` — interface, line 429
- `export interface QueueInput` — interface, line 444
- `export interface SchedulerComponents` — interface, line 451
- `export interface ScheduledItemDto` — interface, line 464
- `export type FollowupKind = | "certification_cold_probe" | "cold_retry" | "intervention_followup" | "negative_surprise_followup"` — type, line 489
- `export interface QueueSection` — interface, line 495
- `export interface DeferredColdCheckDto` — interface, line 503
- `export interface QueueSnapshot` — interface, line 514
- `export interface CriterionTargetDto` — interface, line 526
- `export interface RubricCriterionDto` — interface, line 532
- `export interface RubricFatalErrorDto` — interface, line 553
- `export interface RubricDto` — interface, line 559
- `export interface CandidateErrorTypeDto` — interface, line 567
- `export interface ElicitationDecisionDto` — interface, line 579
- `export type PresentationBlockKind = | "prompt" | "error_hunt_worked_solution" | "laddered_stem_stimulus"` — type, line 601
- `export interface PresentationBlockDto` — interface, line 606
- `export interface ItemPresentationDto` — interface, line 615
- `export interface PracticeItemDetail` — interface, line 620
- `export interface TraceExercisedFacetDto` — interface, line 674
- `export interface AttemptTraceEvidenceDto` — interface, line 682
- `export interface GradingClarificationDto` — interface, line 693
- `export interface GradingClarificationResultDto` — interface, line 713
- `export type ClarificationOutcome = "resolved" | "abstained" | "regrade_failed"` — type, line 720
- `export interface AnswerGradingClarificationResultDto` — interface, line 722
- `export interface AttemptHistoryRowDto` — interface, line 733
- `export interface SourceRefDto` — interface, line 745
- `export interface PracticeItemStateDto` — interface, line 755
- `export interface MasteryDto` — interface, line 764
- `export interface MasteryStepFactorDto` — interface, line 775
- `export interface MasteryStepDto` — interface, line 787
- `export interface SchedulerExplanationDto` — interface, line 800
- `export interface SelfGradeErrorAttributionDto` — interface, line 813
- `export interface SelfGradeInputDto` — interface, line 818
- `export interface SubmitAttemptInput` — interface, line 827
- `export interface ProbeBlockEndDto` — interface, line 856
- `export interface ProbeContractDto` — interface, line 883
- `export interface StopProbeResultDto` — interface, line 904
- `export interface GetNextProbeItemDto` — interface, line 912
- `export interface ResolvedSourceRefDto` — interface, line 919
- `export interface AttemptResultDto` — interface, line 942
- `export interface PracticeSubmissionRecoveryDto` — interface, line 969
- `export interface PracticeSubmissionAcknowledgementDto` — interface, line 975
- `export interface FeedbackBundle` — interface, line 981
- `export interface ColdCheckResultDto` — interface, line 1052
- `export interface CausalFeedbackDto` — interface, line 1072
- `export interface CausalTargetRefDto` — interface, line 1137
- `export interface CausalDivergenceAnchorDto` — interface, line 1149
- `export interface RepairedTraceDto` — interface, line 1160
- `export interface CausalRepairClassDto` — interface, line 1170
- `export interface CausalHypothesisDto` — interface, line 1182
- `export interface CausalMinimalityDto` — interface, line 1206
- `export interface DiagnosisReceiptDto` — interface, line 1220
- `export type CausalTraceConsistencyState = | "contradicted" | "consistent_with_claims" | "no_deterministic_claims" | "unknown"` — type, line 1322
- `export interface CausalProbeNeedDto` — interface, line 1328
- `export type CausalRepairStatusState = | "started" | "needs_disambiguation" | "deferred_machine_checks" | "safe_common_repair_available" | "blocked_pending_review"` — type, line 1345
- `export type CausalRepairActionId = "take_quick_check" | "teach_me_now" | "not_now"` — type, line 1355
- `export interface CausalRepairActionDto` — interface, line 1357
- `export interface CausalRepairStatusDto` — interface, line 1362
- `export interface CausalRepairStatusResultDto` — interface, line 1403
- `export interface CausalProbeOfferDto` — interface, line 1410
- `export interface CausalProbeOfferResultDto` — interface, line 1422
- `export interface CausalProbePreferenceDto` — interface, line 1427
- `export interface CausalProbeDeferResultDto` — interface, line 1439
- `export interface CausalEpisodeDto` — interface, line 1444
- `export interface PersistedRegradeDto` — interface, line 1456
- `export interface MatchedMisconceptionDto` — interface, line 1464
- `export interface UnresolvedCauseDto` — interface, line 1474
- `export type UnresolvedCauseSelfReportResponse = | "slipped" | "believed_candidate" | "item_unclear" | "notation_confused" | "other_valid_approach" | "diagnosis_wrong"` — type, line 1503
- `export interface ElicitingResponseResultDto` — interface, line 1519
- `export interface UnresolvedCauseSelfReportResultDto` — interface, line 1530
- `export interface PrimedRetryResultDto` — interface, line 1539
- `export interface GuidedRedoDto` — interface, line 1554
- `export type TutorQuestionContext = "library" | "practice" | "feedback" | "reader"` — type, line 1578
- `export interface AskTutorQuestionInput` — interface, line 1580
- `export interface TutorCitationDto` — interface, line 1593
- `export interface TutorAnswerDto` — interface, line 1599
- `export interface TutorOpeningDto` — interface, line 1614
- `export interface TutorQuestionEventDto` — interface, line 1619
- `export type PromotionIntent = "practice" | "gap"` — type, line 1646
- `export type PromotionRoute = "auto_apply" | "review_required" | "diagnostic_pending" | "existing_item"` — type, line 1648
- `export type QuestionNature = "core_recall" | "mechanism" | "transfer" | "edge_case" | "what_if"` — type, line 1650
- `export interface QuestionPromotionDto` — interface, line 1652
- `export interface PromoteTutorQuestionInput` — interface, line 1670
- `export interface QuestionPromotionRequestDto` — interface, line 1677
- `export interface PromoteTutorQuestionResult` — interface, line 1693
- `export type QuestionResolution = "open" | "resolved" | "dismissed"` — type, line 1703
- `export interface QuestionQueueRowDto` — interface, line 1705
- `export interface QuestionQueueSnapshot` — interface, line 1726
- `export interface ResolveQuestionEventResult` — interface, line 1732
- `export interface QueueRevisionDto` — interface, line 1739
- `export const RETIREMENT_REASONS = [ "too_easy", "ambiguous", "missing_context", "duplicate_surface", "wrong_granularity", "no_longer_relevant", "bad_underlying_explanation", "superseded_by_better_activity", "should_be_reference_not_memorized", "dont_care_enou…` — const, line 1749
- `export type RetirementReason = (typeof RETIREMENT_REASONS)[number]` — type, line 1763
- `export interface TutorTranscriptInput` — interface, line 1765
- `export interface TutorTranscriptSnapshot` — interface, line 1773
- `export interface TutorSaveNoteResult` — interface, line 1779
- `export type RubricTier = "core" | "transfer"` — type, line 1787
- `export interface TeachBackPlannedDto` — interface, line 1789
- `export interface TeachBackTurnDto` — interface, line 1795
- `export interface TeachBackStateDto` — interface, line 1802
- `export interface StartTeachBackInput` — interface, line 1810
- `export interface StartTeachBackResult` — interface, line 1815
- `export interface SubmitTeachBackTurnInput` — interface, line 1826
- `export interface TeachBackQuestionResult` — interface, line 1835
- `export type TeachBackFinishResult = AttemptResultDto &` — type, line 1849
- `export type TeachBackTurnResult = TeachBackQuestionResult | TeachBackFinishResult` — type, line 1856
- `export interface FollowupSourceDto` — interface, line 1858
- `export interface FollowupRatingDto` — interface, line 1862
- `export interface InterventionNeedDto` — interface, line 1867
- `export interface CriterionEvidenceRowDto` — interface, line 1884
- `export interface ErrorEventDto` — interface, line 1896
- `export interface AttemptSurpriseDto` — interface, line 1909
- `export interface FollowupGateSignalDto` — interface, line 1927
- `export interface FollowupGateSubscoreDto` — interface, line 1941
- `export interface FollowupGateDiagnosticsDto` — interface, line 1952
- `export interface RepairSuggestionDto` — interface, line 1987
- `export interface AttemptInspectorDetail` — interface, line 2028
- `export interface NoteInspectorDetail` — interface, line 2057
- `export interface ProbeEpisodeInspectorDetail` — interface, line 2073
- `export type InspectorEntity = |` — type, line 2100
- `export interface InspectorSearchResult` — interface, line 2110
- `export interface LearningObjectDetail` — interface, line 2118
- `export interface ConceptReferenceDto` — interface, line 2139
- `export interface ConceptInspectorDetail` — interface, line 2151
- `export interface CommandError` — interface, line 2174
- `export interface CliCommandResult` — interface, line 2181
- `export interface RecentIngestEntry` — interface, line 2189
- `export interface RecentIngestsSnapshot` — interface, line 2203
- `export type IngestMode = "canonical" | "exam"` — type, line 2208
- `export type IngestJobStatus = "queued" | "running" | "completed" | "failed" | "cancelled"` — type, line 2209
- `export type IngestJobPhase = | "queued" | "preparing" | "fetching" | "extracting" | "staging" | "authoring" | "cancelling" | "completed" | "failed" | "cancelled"` — type, line 2210
- `export interface IngestSourceClassification` — interface, line 2222
- `export interface IngestJobResult` — interface, line 2228
- `export interface IngestJobError` — interface, line 2246
- `export interface IngestJobDto` — interface, line 2252
- `export interface IngestJobsSnapshot` — interface, line 2271
- `export type PdfEngine = "auto" | "marker" | "pypdf" | "native"` — type, line 2276
- `export interface StartIngestInput` — interface, line 2278
- `export type DurableIngestStatus = | "queued" | "running" | "waiting_for_input" | "completed" | "failed" | "blocked" | "cancelled"` — type, line 2287
- `export interface IngestJobView` — interface, line 2296
- `export interface IngestBatchDto` — interface, line 2335
- `export interface IngestBatchesSnapshot` — interface, line 2353
- `export interface RetrySynthesisInput` — interface, line 2358
- `export interface SynthesisCandidateSummary` — interface, line 2373
- `export interface StartImportBatchInput` — interface, line 2384
- `export type SourceReadiness = "ready" | "processing" | "needs_extraction"` — type, line 2402
- `export interface SourceLibraryCard` — interface, line 2404
- `export interface SourceDeletionCollectionImpact` — interface, line 2425
- `export interface SourceDeletionPlanDto` — interface, line 2433
- `export interface SourceDeletionResultDto` — interface, line 2451
- `export interface SourceLibrarySnapshot` — interface, line 2459
- `export interface UnitInventoryMarker` — interface, line 2466
- `export interface OutlineUnit` — interface, line 2472
- `export interface SelectionPreviewDto` — interface, line 2490
- `export interface EffectiveUnitDto` — interface, line 2502
- `export interface EffectiveOutlineDto` — interface, line 2512
- `export interface UnitSelectionState` — interface, line 2518
- `export interface SourceOutline` — interface, line 2525
- `export interface SaveUnitSelectionInput` — interface, line 2543
- `export interface SourceSetScopeDto` — interface, line 2552
- `export interface SourceSetMemberDto` — interface, line 2557
- `export interface SourceSetDto` — interface, line 2565
- `export interface SourceSetSummaryDto` — interface, line 2573
- `export interface SourceSetsSnapshot` — interface, line 2580
- `export interface CoverageReadinessFlag` — interface, line 2585
- `export interface SourceCoverageDto` — interface, line 2590
- `export interface CoverageRollupDto` — interface, line 2601
- `export interface StartInventoryInput` — interface, line 2610
- `export interface CreateStudyMapInput` — interface, line 2619
- `export interface BuildStudyMapInput` — interface, line 2628
- `export interface StudyMapDto` — interface, line 2638
- `export type StartingLevel = "new_to_this" | "some_exposure" | "comfortable" | "strong_background"` — type, line 2657
- `export type AuthoringPreset = "narrow_adjunct"` — type, line 2658
- `export interface StudyMapBriefDto` — interface, line 2660
- `export interface RungVariantRequestDto` — interface, line 2686
- `export interface ProbeRemintResultDto` — interface, line 2701
- `export interface RungVariantRequestResultDto` — interface, line 2711
- `export interface LearnerProfileDto` — interface, line 2722
- `export interface PlanQuickAddInput` — interface, line 2729
- `export interface ConfirmQuickAddInput` — interface, line 2735
- `export interface ProposeFacetMergeInput` — interface, line 2745
- `export interface QuickAddConsentDto` — interface, line 2753
- `export interface QuickAddConfirmationDto` — interface, line 2761
- `export interface QuickAddPlanDto` — interface, line 2779
- `export interface QuickAddResultDto` — interface, line 2802
- `export interface SpanViewInput` — interface, line 2812
- `export interface SpanNeighborDto` — interface, line 2820
- `export interface SpanViewDto` — interface, line 2829
- `export interface FacetContractCardDto` — interface, line 2858
- `export interface IdentifiabilityWarningDto` — interface, line 2877
- `export interface MeasurementRankDto` — interface, line 2892
- `export interface SubjectRegistryDto` — interface, line 2904
- `export interface FacetMergeResultDto` — interface, line 2914
- `export interface AcquisitionPreviewItem` — interface, line 2922
- `export interface AcquisitionPreview` — interface, line 2938
- `export interface BuildPlanStage` — interface, line 2950
- `export interface BuildPlanSource` — interface, line 2960
- `export interface BuildPlan` — interface, line 2974
- `export interface BuildPlanSelectionInput` — interface, line 2999
- `export interface ExtractionRepairConsent` — interface, line 3004
- `export interface StartExtractionRepairInput` — interface, line 3012
- `export interface ConceptGraphLearningObject` — interface, line 3021
- `export interface ConceptGraphNode` — interface, line 3027
- `export interface ConceptGraphEdge` — interface, line 3038
- `export interface ConceptGraphSnapshot` — interface, line 3046
- `export interface VaultTreeNode` — interface, line 3054
- `export interface VaultTreeSnapshot` — interface, line 3062
- `export interface VaultFileContent` — interface, line 3068
- `export interface SqliteTableInfo` — interface, line 3084
- `export interface SqliteTablesSnapshot` — interface, line 3089
- `export interface SqliteColumn` — interface, line 3095
- `export interface SqliteRow` — interface, line 3104
- `export interface SqliteTableSnapshot` — interface, line 3109
- `export type SqliteExecResult = |` — type, line 3120
- `export type ProposalDecision = "pending" | "accepted" | "rejected"` — type, line 3124
- `export type ProposalReviewRoute = "auto_apply" | "review_required" | "reject"` — type, line 3125
- `export interface ProposalSourceRefDto` — interface, line 3127
- `export interface ProposalItemDto` — interface, line 3133
- `export interface ProposalAgentRunDto` — interface, line 3155
- `export interface ProposalDecisionCounts` — interface, line 3167
- `export interface ProposalBatchDto` — interface, line 3173
- `export interface ProposalsSnapshot` — interface, line 3185
- `export interface EntitySourceLink` — interface, line 3196
- `export interface SourceConflictRef` — interface, line 3211
- `export interface NotationMappingRef` — interface, line 3222
- `export interface IntroducedBy` — interface, line 3231
- `export interface EntityProvenance` — interface, line 3240
- `export interface GoalPaceDto` — interface, line 3255
- `export interface GoalLatestExamDto` — interface, line 3266
- `export interface GoalReportSummaryDto` — interface, line 3271
- `export type MeasurementStateDto = "measured" | "inferred" | "claimed" | "unknown"` — type, line 3312
- `export interface GoalAtRiskFacetDto` — interface, line 3314
- `export interface ComponentReadinessDto` — interface, line 3345
- `export interface RecipeProjectionDto` — interface, line 3353
- `export interface BlueprintProjectionDto` — interface, line 3361
- `export interface LoReadinessDto` — interface, line 3369
- `export interface GoalDto` — interface, line 3377
- `export interface GoalsListSnapshot` — interface, line 3399
- `export interface GoalReportSnapshot` — interface, line 3404
- `export interface TraceTargetDto` — interface, line 3417
- `export interface TraceCriterionDto` — interface, line 3423
- `export interface AttemptTraceDto` — interface, line 3438
- `export interface CapabilityGridCellDto` — interface, line 3450
- `export interface CapabilityGridDto` — interface, line 3464
- `export interface CapabilityGridResult` — interface, line 3472
- `export interface DemonstratedTimelinePointDto` — interface, line 3478
- `export interface ObservationDerivationDto` — interface, line 3494
- `export interface ReadyCapabilitySliceDto` — interface, line 3503
- `export interface ReadyDerivationDto` — interface, line 3512
- `export interface FacetEvidenceTimelineDto` — interface, line 3527
- `export interface GoalSeriesPointDto` — interface, line 3539
- `export interface GoalSeriesSnapshot` — interface, line 3556
- `export interface GoalFeasibilityInput` — interface, line 3562
- `export interface GoalMaterialGap` — interface, line 3575
- `export interface GoalFeasibilityResult` — interface, line 3582
- `export interface GenerateStarterPracticeResult` — interface, line 3593
- `export interface GenerateCommissioningPracticeResult` — interface, line 3603
- `export interface ReviewCountsDto` — interface, line 3619
- `export interface CreateGoalInput` — interface, line 3632
- `export interface CreateGoalResult` — interface, line 3647
- `export type CalibrationSessionStatus = "active" | "completed" | "stopped" | "expired"` — type, line 3655
- `export interface CalibrationEpisodeDto` — interface, line 3657
- `export interface CalibrationNextTargetDto` — interface, line 3667
- `export interface StartCalibrationSessionInput` — interface, line 3676
- `export interface CalibrationSessionProgressDto` — interface, line 3683
- `export interface DialogueTurnDto` — interface, line 3703
- `export interface BeginProbeDialogueResult` — interface, line 3713
- `export interface NextProbeDialogueTurnResult` — interface, line 3720
- `export interface RecordProbeDialogueTurnResult` — interface, line 3727
- `export interface EndProbeDialogueResult` — interface, line 3733
- `export interface ExamStatusSnapshot` — interface, line 3740
- `export interface ExamItemDto` — interface, line 3756
- `export interface ExamSessionSnapshot` — interface, line 3768
- `export interface ExamAnswerResult` — interface, line 3780
- `export interface ExamFacetOutcomeDto` — interface, line 3788
- `export interface ExamItemRepairDto` — interface, line 3798
- `export interface ExamItemOutcomeDto` — interface, line 3811
- `export interface ExamReportSnapshot` — interface, line 3823
- `export interface StudyMapDiffDto` — interface, line 3836
- `export interface MergeReviewProposalDto` — interface, line 3847
- `export interface AppendResultDto` — interface, line 3855
- `export interface AppendSourceInput` — interface, line 3873
- `export interface RefreshResultDto` — interface, line 3882
- `export interface RefreshRevisionInput` — interface, line 3895
- `export type MaintenanceSeverity = "info" | "warning" | "action_needed"` — type, line 3904
- `export interface MaintenanceNoticeDto` — interface, line 3906
- `export interface MaintenanceFeedSnapshot` — interface, line 3925
- `export interface MeasurementMetricDto` — interface, line 3933
- `export interface ReachabilityCellDto` — interface, line 3946
- `export interface MeasurementHealthDto` — interface, line 3955
- `export interface InstrumentAuditDto` — interface, line 4146
- `export type ConflictResolutionKind = | "prefer_for_context" | "keep_both_scoped" | "notation_mapping" | "dismiss"` — type, line 4211
- `export interface SourceConflictDto` — interface, line 4217
- `export interface ResolveConflictInput` — interface, line 4238
- `export interface FacetCapabilityStateDto` — interface, line 4245
- `export interface PredictedScoreDto` — interface, line 4254
- `export interface TaskFamilyReadinessDto` — interface, line 4261
- `export interface ExamReadinessReportDto` — interface, line 4273
- `export type ClaimClass = "estimate" | "diagnosis" | "policy" | "ledger_fact"` — type, line 4286
- `export type ClaimTemperature = "hot" | "cold"` — type, line 4287
- `export interface ClaimCandidateDto` — interface, line 4289
- `export interface PresentedClaimDto extends ClaimCandidateDto` — interface, line 4304
- `export interface HypothesisEventDto` — interface, line 4311
- `export type BeliefWithdrawalReason = | "contradicted_by_trace" | "superseded" | "adjudicated" | "retired_misdiagnosed"` — type, line 4330
- `export interface ReviewChangelogEntryDto` — interface, line 4336
- `export interface WorkingHypothesisDto` — interface, line 4377
- `export interface ReviewLogDto` — interface, line 4390
- `export interface RemediationEpisodeDto` — interface, line 4396
- `export interface RemediationCaseDto` — interface, line 4411
- `export interface RemediationDto` — interface, line 4422
- `export interface StartRemediationDto` — interface, line 4438
- `export interface ForecastTrackRecordDto` — interface, line 4449
- `export interface CalibrationBinDto` — interface, line 4457
- `export interface AnswerCalibrationReportDto` — interface, line 4465
- `export interface OverconfidentFacetDto` — interface, line 4494
- `export interface OverconfidenceSnapshot` — interface, line 4505
- `export interface StartOverconfidenceProbeResult` — interface, line 4511
- `export interface ReentrySlippedFacetDto` — interface, line 4520
- `export interface ReentrySummaryDto` — interface, line 4527
- `export interface ReentrySummarySnapshot` — interface, line 4538
- `export interface DecayPressureFacetDto` — interface, line 4545
- `export interface DecayPressureDto` — interface, line 4554
- `export interface DecayPressureSnapshot` — interface, line 4560
- `export type GraphEditItemType = | "concept_edge" | "learning_object" | "task_blueprint" | "concept"` — type, line 4573
- `export type GraphEditOperation = "create" | "update" | "delete"` — type, line 4579
- `export interface GraphEditInput` — interface, line 4583
- `export interface ProposeGraphEditsInput` — interface, line 4590
- `export interface GraphEditItemDto` — interface, line 4598
- `export interface ProposeGraphEditsResult extends ProposalsSnapshot` — interface, line 4611
- `export interface QueueRestructureRequestInput` — interface, line 4616
- `export interface RestructureRequestDto` — interface, line 4625
- `export interface QueueRestructureRequestResult` — interface, line 4635
- `export type EdgeDirectionResolution = "keep" | "flip" | "retype_related" | "retire"` — type, line 4640
- `export interface ResolveEdgeDirectionInput` — interface, line 4642
- `export interface EdgeDirectionResolutionDto` — interface, line 4651
- `export interface ResolveEdgeDirectionResult extends ProposalsSnapshot` — interface, line 4661
- `export interface FacetDetailContractDto` — interface, line 4667
- `export interface FacetLockReasonDto` — interface, line 4681
- `export interface FacetLockDto` — interface, line 4686
- `export interface FacetMembershipRowDto` — interface, line 4692
- `export interface FacetCapabilityLedgerRowDto` — interface, line 4702
- `export interface FacetEvidenceDto` — interface, line 4714
- `export interface FacetDetailDto` — interface, line 4721
- `export interface FacetSummaryDto` — interface, line 4733
- `export interface FacetListDto` — interface, line 4741
- `export interface PreviewEdgeInput` — interface, line 4748
- `export interface PreviewKnowledgeMapInput` — interface, line 4754
- `export interface KnowledgeMapPreviewPoint` — interface, line 4759
- `export interface KnowledgeMapPreviewDto` — interface, line 4767
- `export interface PreviewBlueprintReadinessInput` — interface, line 4776
- `export interface BlueprintReadinessSummaryDto` — interface, line 4783
- `export interface BlueprintReadinessPreviewDto` — interface, line 4788
- `export type GraphEditorNoticeType = "ambiguous_edge_direction" | "restructure_request"` — type, line 4804
- `export interface AmbiguousEdgeDirectionDetail` — interface, line 4809
- `export interface RestructureRequestDetail` — interface, line 4828
- `export type RecipeCapability = | "retrieval" | "schema_interpretation" | "procedure_execution" | "method_selection" | "coordination"` — type, line 4844
- `export type RecipeModality = | "hard" | "path_specific" | "facilitating" | "instructional_order"` — type, line 4852
- `export interface RecipeComponentDto` — interface, line 4858
- `export interface BlueprintRecipeDto` — interface, line 4864
- `export interface LoBlueprintDto` — interface, line 4872
- `export interface CreateVaultInput` — interface, line 4882
- `export interface CreateVaultResult` — interface, line 4891
- `export interface GpInterval` — interface, line 4906
- `export type GpCalibrationStatus = "heuristic" | "simulation_validated" | "live_calibrated"` — type, line 4914
- `export type GpClaimLanguage = "provisional" | "calibrated" | "insufficient"` — type, line 4915
- `export interface BlueprintExemplarDto` — interface, line 4918
- `export interface BlueprintVersionDto` — interface, line 4927
- `export interface ExemplarPoolItemDto` — interface, line 4939
- `export interface ExemplarPoolEntryDto` — interface, line 4947
- `export interface ExemplarPoolSnapshot` — interface, line 4953
- `export interface ComposeDraftResult` — interface, line 4958
- `export interface ConfirmReceiptDto` — interface, line 4970
- `export interface RunNextActionDto` — interface, line 4986
- `export interface RunHistoryEntryDto` — interface, line 4991
- `export interface RunStateDto` — interface, line 4998
- `export interface RunAdvanceResultDto` — interface, line 5011
- `export type BoundaryCellState = "demonstrated" | "developing" | "untested" | "weak" | "contested"` — type, line 5018
- `export interface BoundaryCellDto` — interface, line 5019
- `export interface BoundaryDiffDto` — interface, line 5029
- `export interface AssessOpenDto` — interface, line 5039
- `export interface AssessReviewStateDto` — interface, line 5059
- `export interface AssessResultDto` — interface, line 5065
- `export interface DepthEdgeDto` — interface, line 5091
- `export interface DepthInvitationDto` — interface, line 5104
- `export interface DepthInvitationResultDto` — interface, line 5118
- `export interface AcceptEdgeResultDto` — interface, line 5123
- `export interface RestoreDto` — interface, line 5131
- `export interface LadderStageDto` — interface, line 5146
- `export interface LadderPolicyDto` — interface, line 5161
- `export interface LadderStatusDto` — interface, line 5174
- `export interface LadderAdvanceResultDto` — interface, line 5180
- `export interface PoolSurfaceDto` — interface, line 5187
- `export interface PoolDto` — interface, line 5194
- `export interface PoolStatusDto` — interface, line 5205
- `export interface PoolAnchorCandidateDto` — interface, line 5211
- `export interface PoolForRunDto` — interface, line 5216
- `export interface ServedSurfaceDto` — interface, line 5232
- `export interface PoolNextSurfaceDto` — interface, line 5243
- `export interface TriageRouteDto` — interface, line 5254
- `export interface TriageAlternativeDto` — interface, line 5262
- `export interface TriageResultDto` — interface, line 5267
- `export interface RunListEntryDto` — interface, line 5292
- `export interface RunListDto` — interface, line 5301
- `export interface TriageTraceEntryDto` — interface, line 5307
- `export interface TriageStatusDto` — interface, line 5320
- `export interface ReaderPromptContractDto` — interface, line 5328
- `export type ReaderAnswerMode = "answer_directly" | "help_me_reason" | "ask_me_first"` — type, line 5341
- `export interface ReaderAskInput` — interface, line 5344
- `export interface ReaderAnswerDto` — interface, line 5357
- `export interface ReaderAskHistoryExchangeDto` — interface, line 5371
- `export interface ReaderAskHistoryDto` — interface, line 5381
- `export type ReaderDisposition = | "comprehension_only" | "check_once_later" | "keep_developing" | "reference_only"` — type, line 5387
- `export interface ReaderDispositionResultDto` — interface, line 5392
- `export type ReaderAnchorStatus = | "exact" | "reanchored" | "needs_reanchor" | "orphaned" | "manually_anchored"` — type, line 5400
- `export type ReaderBlockHealthStatus = "ok" | "suspect" | "failed" | "unknown"` — type, line 5407
- `export type ReaderRecommendedView = "derived" | "crop_adjacent" | "crop_default" | "warn_link"` — type, line 5408
- `export interface ReaderWatchPausePointDto` — interface, line 5413
- `export interface ReaderWatchPlanDto` — interface, line 5424
- `export interface ReaderRenderBlockDto` — interface, line 5432
- `export interface ReaderRenderViewDto` — interface, line 5450
- `export interface ReaderSuggestedPassageDto` — interface, line 5466
- `export interface ReaderSectionQuestionDto` — interface, line 5475
- `export interface ReaderAuthoredQuestionDto` — interface, line 5502
- `export interface ReaderAuthorSectionQuestionDto` — interface, line 5514
- `export interface ReaderSourceSearchHitDto` — interface, line 5522
- `export interface ReaderSourceSearchDto` — interface, line 5532
- `export interface ReaderSectionProgressDto` — interface, line 5540
- `export interface ReaderProgressListDto` — interface, line 5550
- `export interface ReaderMarkProgressResultDto` — interface, line 5556
- `export interface ReaderGuideSectionDto` — interface, line 5563
- `export interface ReaderGuidePlanDto` — interface, line 5573
- `export interface ReaderPdfBlockDto` — interface, line 5589
- `export interface ReaderPdfViewDto` — interface, line 5601
- `export interface ReaderRawSelectionNode` — interface, line 5612
- `export interface ReaderRawSelection` — interface, line 5626
- `export interface ReaderTranslateSelectionInput` — interface, line 5633
- `export interface ReaderAnchorSegmentDto` — interface, line 5638
- `export interface ReaderTranslationDto` — interface, line 5648
- `export interface ReaderCaptureInput` — interface, line 5656
- `export interface ReaderCaptureReceiptDto` — interface, line 5668
- `export interface ReaderCreateAnnotationInput` — interface, line 5680
- `export interface ReaderAnnotationResultDto` — interface, line 5691
- `export interface ReaderBlockRegionDto` — interface, line 5698
- `export interface ReaderInvokePresetInput` — interface, line 5710
- `export interface ReaderPresetReceiptDto extends ReaderCaptureReceiptDto` — interface, line 5723
- `export interface ReaderImportExerciseInput` — interface, line 5732
- `export interface ReaderExerciseImportReceiptDto` — interface, line 5741
- `export interface ReaderExerciseImportedItem` — interface, line 5746
- `export interface ReaderExerciseImportSkip` — interface, line 5760
- `export interface ReaderExerciseImportResult` — interface, line 5766
- `export interface ReaderExerciseImportStatusDto` — interface, line 5773
- `export interface ReaderAuthorQAInput` — interface, line 5781
- `export interface ReaderAuthoredCardDto` — interface, line 5791
- `export interface ReaderCoachSuggestion` — interface, line 5803
- `export interface ReaderCoachLintDto` — interface, line 5807
- `export interface ReaderMaintainInput` — interface, line 5813
- `export interface ReaderArcDto` — interface, line 5828
- `export interface ReaderRestorationAnnotationDto` — interface, line 5842
- `export interface ReaderRestorationDto` — interface, line 5853
- `export interface ReaderSetModeResultDto` — interface, line 5866
- `export interface ReaderQuestionControlResultDto` — interface, line 5872
- `export interface ReaderEnqueueRequestInput` — interface, line 5879
- `export interface ReaderRequestScopeDto` — interface, line 5891
- `export interface ReaderEnqueueRequestDto` — interface, line 5897
- `export interface ReaderRequestRow` — interface, line 5913
- `export interface StubDiagnosticPackDto` — interface, line 5928
- `export interface StubPoolSurfacesDto` — interface, line 5932
- `export type AdjudicationVerdict = | "correct" | "wrong_anchor" | "wrong_repair" | "should_have_abstained" | "correctly_abstained" | "should_not_have_abstained"` — type, line 5944
- `export type AdjudicationQueueReason = string` — type, line 5953
- `export interface AdjudicationAnchorDto` — interface, line 5955
- `export interface AdjudicationRepairClassOptionDto` — interface, line 5966
- `export interface AdjudicationShownToLearnerDto` — interface, line 5973
- `export interface AdjudicationCaseDto` — interface, line 5993
- `export interface AdjudicationQueueDto` — interface, line 6020
- `export interface AdjudicationRecordInput` — interface, line 6027
- `export interface AdjudicationBeliefEffectDto` — interface, line 6046
- `export interface AdjudicationOutcomeDto` — interface, line 6055
- `export interface AdjudicationRecordResultDto` — interface, line 6064
- `export interface AdjudicationScoreboardGroupDto` — interface, line 6081
- `export interface AdjudicationScoreboardDto` — interface, line 6103

## Internal implementation anchors

No non-exported declaration anchor was detected by the static extractor.

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export: `AcceptEdgeResultDto`, `AcquisitionPreview`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationRecordResultDto`, `AdjudicationScoreboardDto`, `AnimationRuntimeDto`, `AnswerCalibrationReportDto`, `AnswerGradingClarificationResultDto`, `AppSnapshot`, `AppendResultDto`, `AppendSourceInput`, `AskTutorQuestionInput`, `AssessOpenDto`, `AssessResultDto`, `AttemptResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `BeginProbeDialogueResult`, `BlueprintReadinessPreviewDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `BuildPlan`, `BuildPlanSelectionInput`, `BuildStudyMapInput`, `CalibrationSessionProgressDto`, `CapabilityGridResult`, `CausalProbeDeferResultDto`, `CausalProbeOfferResultDto`, `CausalRepairStatusResultDto`, `ClaimCandidateDto`, `CliCommandResult`, `CommandError`, `ComposeDraftResult`, `ConceptAnimationDto`, `ConceptGraphSnapshot`, `ConfirmQuickAddInput`, `ConfirmReceiptDto`, `CreateGoalInput`, `CreateGoalResult`, `CreateStudyMapInput`, `CreateVaultInput`, `CreateVaultResult`, `DecayPressureSnapshot`, `DepthInvitationResultDto`, `EffectiveOutlineDto`, `ElicitingResponseResultDto`, `EndProbeDialogueResult`, `EntityProvenance`, `ExamAnswerResult`, `ExamReadinessReportDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`, `ExamStatusSnapshot`, `ExemplarPoolSnapshot`, `FacetDetailDto`, `FacetEvidenceTimelineDto`, `FacetListDto`, `FacetMasterySnapshot`, `FacetMergeResultDto`, `FeedbackBundle`, `ForecastTrackRecordDto`, `GenerateCommissioningPracticeResult`, `GenerateStarterPracticeResult`, `GetNextProbeItemDto`, `GoalDto`, `GoalFeasibilityInput`, `GoalFeasibilityResult`, `GoalReportSnapshot`, `GoalSeriesSnapshot`, `GoalsListSnapshot`, `GradingClarificationResultDto`, `GradingProviderResult`, `GuidedRedoDto`, `HypothesisEventDto`, `IngestBatchDto`, `IngestBatchesSnapshot`, `IngestBudgetsDto`, `IngestJobDto`, `IngestJobsSnapshot`, `IngestSourceClassification`, `InspectorEntity`, `KnowledgeMapHistory`, `KnowledgeMapPreviewDto`, `KnowledgeMapSnapshot`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `LearnerProfileDto`, `MaintenanceFeedSnapshot`, `MaintenanceNoticeDto`, `MeasurementHealthDto`, `NextProbeDialogueTurnResult`, `OpenrouterKeyResult`, `OverconfidenceSnapshot`, `PlanQuickAddInput`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `PoolStatusDto`, `PracticeItemDetail`, `PracticeSubmissionAcknowledgementDto`, `PracticeSubmissionRecoveryDto`, `PresentedClaimDto`, `PreviewBlueprintReadinessInput`, `PreviewKnowledgeMapInput`, `PrimedRetryResultDto`, `ProbeContractDto`, `ProbeRemintResultDto`, `PromoteTutorQuestionResult`, `PromotionIntent`, `ProposalsSnapshot`, `ProposeFacetMergeInput`, `ProposeGraphEditsInput`, `ProposeGraphEditsResult`, `QuestionQueueSnapshot`, `QuestionResolution`, `QueueInput`, `QueueRestructureRequestInput`, `QueueRestructureRequestResult`, `QueueRevisionDto`, `QueueSnapshot`, `QuickAddConfirmationDto`, `QuickAddPlanDto`, `QuickAddResultDto`, `ReaderAnnotationResultDto`, `ReaderAnswerDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderAskHistoryDto`, `ReaderAskInput`, `ReaderAuthorQAInput`, `ReaderAuthorSectionQuestionDto`, `ReaderAuthoredCardDto`, `ReaderAuthoredQuestionDto`, `ReaderBlockRegionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderCoachLintDto`, `ReaderCreateAnnotationInput`, `ReaderDisposition`, `ReaderDispositionResultDto`, `ReaderEnqueueRequestDto`, `ReaderEnqueueRequestInput`, `ReaderExerciseImportReceiptDto`, `ReaderExerciseImportStatusDto`, `ReaderGuidePlanDto`, `ReaderImportExerciseInput`, `ReaderInvokePresetInput`, `ReaderMaintainInput`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderProgressListDto`, `ReaderPromptContractDto`, `ReaderQuestionControlResultDto`, `ReaderRenderViewDto`, `ReaderRequestRow`, `ReaderRestorationDto`, `ReaderSetModeResultDto`, `ReaderSourceSearchDto`, `ReaderTranslateSelectionInput`, `ReaderTranslationDto`, `ReaderWatchPlanDto`, `RecentIngestsSnapshot`, `RecordProbeDialogueTurnResult`, `ReentrySummarySnapshot`, `RefreshResultDto`, `RefreshRevisionInput`, `RemediationDto`, `RequestConceptAnimationResult`, `ResolveConflictInput`, `ResolveEdgeDirectionInput`, `ResolveEdgeDirectionResult`, `ResolveQuestionEventResult`, `RestoreDto`, `RetirementReason`, `RetrySynthesisInput`, `ReviewCountsDto`, `ReviewLogDto`, `RunAdvanceResultDto`, `RunListDto`, `RunStateDto`, `RungVariantRequestDto`, `RungVariantRequestResultDto`, `RuntimeHealth`, `SaveUnitSelectionInput`, `SchedulerExplanationDto`, `SelectionPreviewDto`, `SessionEndSummary`, `SessionSnapshot`, `SessionStartInput`, `SettingsDto`, `SourceConflictDto`, `SourceCoverageDto`, `SourceDeletionPlanDto`, `SourceDeletionResultDto`, `SourceLibrarySnapshot`, `SourceOutline`, `SourceSetDto`, `SourceSetsSnapshot`, `SpanViewDto`, `SpanViewInput`, `SqliteExecResult`, `SqliteTableSnapshot`, `SqliteTablesSnapshot`, `StartCalibrationSessionInput`, `StartExtractionRepairInput`, `StartImportBatchInput`, `StartIngestInput`, `StartInventoryInput`, `StartOverconfidenceProbeResult`, `StartRemediationDto`, `StartTeachBackInput`, `StartTeachBackResult`, `StartingLevel`, `StopProbeResultDto`, `StudyMapDto`, `SubjectRegistryDto`, `SubmitAttemptInput`, `SubmitTeachBackTurnInput`, `SynthesisCandidateSummary`, `TeachBackTurnResult`, `TranscriptionKeyResult`, `TriageResultDto`, `TriageStatusDto`, `TutorAnswerDto`, `TutorOpeningDto`, `TutorSaveNoteResult`, `TutorTranscriptInput`, `TutorTranscriptSnapshot`, `UnitSelectionState`, `UnresolvedCauseSelfReportResponse`, `UnresolvedCauseSelfReportResultDto`, `UpdateAiSettingsInput`, `UpdateIngestSettingsInput`, `VaultFileContent`, `VaultSummary`, `VaultTreeSnapshot`; references `AcceptEdgeResultDto`, `AcquisitionPreview`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationRecordResultDto`, `AdjudicationScoreboardDto`, `AnimationRuntimeDto`, `AnswerCalibrationReportDto`, `AnswerGradingClarificationResultDto`, `AppSnapshot`, `AppendResultDto`, `AppendSourceInput`, `AskTutorQuestionInput`, `AssessOpenDto`, `AssessResultDto`, `AttemptResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `BeginProbeDialogueResult`, `BlueprintReadinessPreviewDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `BuildPlan`, `BuildPlanSelectionInput`, `BuildStudyMapInput`, `CalibrationSessionProgressDto`, `CapabilityGridResult`, `CausalProbeDeferResultDto`, `CausalProbeOfferResultDto`, `CausalRepairStatusResultDto`, `ClaimCandidateDto`, `CliCommandResult`, `CommandError`, `ComposeDraftResult`, `ConceptAnimationDto`, `ConceptGraphSnapshot`, `ConfirmQuickAddInput`, `ConfirmReceiptDto`, `CreateGoalInput`, `CreateGoalResult`, `CreateStudyMapInput`, `CreateVaultInput`, `CreateVaultResult`, `DecayPressureSnapshot`, `DepthInvitationResultDto`, `EffectiveOutlineDto`, `ElicitingResponseResultDto`, `EndProbeDialogueResult`, `EntityProvenance`, `ExamAnswerResult`, `ExamReadinessReportDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`, `ExamStatusSnapshot`, `ExemplarPoolSnapshot`, `FacetDetailDto`, `FacetEvidenceTimelineDto`, `FacetListDto`, `FacetMasterySnapshot`, `FacetMergeResultDto`, `FeedbackBundle`, `ForecastTrackRecordDto`, `GenerateCommissioningPracticeResult`, `GenerateStarterPracticeResult`, `GetNextProbeItemDto`, `GoalDto`, `GoalFeasibilityInput`, `GoalFeasibilityResult`, `GoalReportSnapshot`, `GoalSeriesSnapshot`, `GoalsListSnapshot`, `GradingClarificationResultDto`, `GradingProviderResult`, `GuidedRedoDto`, `HypothesisEventDto`, `IngestBatchDto`, `IngestBatchesSnapshot`, `IngestBudgetsDto`, `IngestJobDto`, `IngestJobsSnapshot`, `IngestSourceClassification`, `InspectorEntity`, `KnowledgeMapHistory`, `KnowledgeMapPreviewDto`, `KnowledgeMapSnapshot`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `LearnerProfileDto`, `MaintenanceFeedSnapshot`, `MaintenanceNoticeDto`, `MeasurementHealthDto`, `NextProbeDialogueTurnResult`, `OpenrouterKeyResult`, `OverconfidenceSnapshot`, `PlanQuickAddInput`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `PoolStatusDto`, `PracticeItemDetail`, `PracticeSubmissionAcknowledgementDto`, `PracticeSubmissionRecoveryDto`, `PresentedClaimDto`, `PreviewBlueprintReadinessInput`, `PreviewKnowledgeMapInput`, `PrimedRetryResultDto`, `ProbeContractDto`, `ProbeRemintResultDto`, `PromoteTutorQuestionResult`, `PromotionIntent`, `ProposalsSnapshot`, `ProposeFacetMergeInput`, `ProposeGraphEditsInput`, `ProposeGraphEditsResult`, `QuestionQueueSnapshot`, `QuestionResolution`, `QueueInput`, `QueueRestructureRequestInput`, `QueueRestructureRequestResult`, `QueueRevisionDto`, `QueueSnapshot`, `QuickAddConfirmationDto`, `QuickAddPlanDto`, `QuickAddResultDto`, `ReaderAnnotationResultDto`, `ReaderAnswerDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderAskHistoryDto`, `ReaderAskInput`, `ReaderAuthorQAInput`, `ReaderAuthorSectionQuestionDto`, `ReaderAuthoredCardDto`, `ReaderAuthoredQuestionDto`, `ReaderBlockRegionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderCoachLintDto`, `ReaderCreateAnnotationInput`, `ReaderDisposition`, `ReaderDispositionResultDto`, `ReaderEnqueueRequestDto`, `ReaderEnqueueRequestInput`, `ReaderExerciseImportReceiptDto`, `ReaderExerciseImportStatusDto`, `ReaderGuidePlanDto`, `ReaderImportExerciseInput`, `ReaderInvokePresetInput`, `ReaderMaintainInput`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderProgressListDto`, `ReaderPromptContractDto`, `ReaderQuestionControlResultDto`, `ReaderRenderViewDto`, `ReaderRequestRow`, `ReaderRestorationDto`, `ReaderSetModeResultDto`, `ReaderSourceSearchDto`, `ReaderTranslateSelectionInput`, `ReaderTranslationDto`, `ReaderWatchPlanDto`, `RecentIngestsSnapshot`, `RecordProbeDialogueTurnResult`, `ReentrySummarySnapshot`, `RefreshResultDto`, `RefreshRevisionInput`, `RemediationDto`, `RequestConceptAnimationResult`, `ResolveConflictInput`, `ResolveEdgeDirectionInput`, `ResolveEdgeDirectionResult`, `ResolveQuestionEventResult`, `RestoreDto`, `RetirementReason`, `RetrySynthesisInput`, `ReviewCountsDto`, `ReviewLogDto`, `RunAdvanceResultDto`, `RunListDto`, `RunStateDto`, `RungVariantRequestDto`, `RungVariantRequestResultDto`, `RuntimeHealth`, `SaveUnitSelectionInput`, `SchedulerExplanationDto`, `SelectionPreviewDto`, `SessionEndSummary`, `SessionSnapshot`, `SessionStartInput`, `SettingsDto`, `SourceConflictDto`, `SourceCoverageDto`, `SourceDeletionPlanDto`, `SourceDeletionResultDto`, `SourceLibrarySnapshot`, `SourceOutline`, `SourceSetDto`, `SourceSetsSnapshot`, `SpanViewDto`, `SpanViewInput`, `SqliteExecResult`, `SqliteTableSnapshot`, `SqliteTablesSnapshot`, `StartCalibrationSessionInput`, `StartExtractionRepairInput`, `StartImportBatchInput`, `StartIngestInput`, `StartInventoryInput`, `StartOverconfidenceProbeResult`, `StartRemediationDto`, `StartTeachBackInput`, `StartTeachBackResult`, `StartingLevel`, `StopProbeResultDto`, `StudyMapDto`, `SubjectRegistryDto`, `SubmitAttemptInput`, `SubmitTeachBackTurnInput`, `SynthesisCandidateSummary`, `TeachBackTurnResult`, `TranscriptionKeyResult`, `TriageResultDto`, `TriageStatusDto`, `TutorAnswerDto`, `TutorOpeningDto`, `TutorSaveNoteResult`, `TutorTranscriptInput`, `TutorTranscriptSnapshot`, `UnitSelectionState`, `UnresolvedCauseSelfReportResponse`, `UnresolvedCauseSelfReportResultDto`, `UpdateAiSettingsInput`, `UpdateIngestSettingsInput`, `VaultFileContent`, `VaultSummary`, `VaultTreeSnapshot`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `AppSnapshot`, `GuidedRedoDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `TriageResultDto`; references `AppSnapshot`, `GuidedRedoDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `TriageResultDto`
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export: `CommandError`, `SourceSetDto`, `SourceSetSummaryDto`; references `CommandError`, `SourceSetDto`, `SourceSetSummaryDto`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `AdjudicationCaseDto`, `AdjudicationOutcomeDto`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationScoreboardDto`, `AdjudicationVerdict`; references `AdjudicationCaseDto`, `AdjudicationOutcomeDto`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationScoreboardDto`, `AdjudicationVerdict`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `AskTutorQuestionInput`, `CommandError`, `PromotionIntent`, `QuestionPromotionDto`, `QuestionPromotionRequestDto`, `TutorCitationDto`, `TutorQuestionContext`, `TutorQuestionEventDto`; references `AskTutorQuestionInput`, `CommandError`, `PromotionIntent`, `QuestionPromotionDto`, `QuestionPromotionRequestDto`, `TutorCitationDto`, `TutorQuestionContext`, `TutorQuestionEventDto`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export: `CommandError`, `RETIREMENT_REASONS`, `RetirementReason`; references `CommandError`, `RETIREMENT_REASONS`, `RetirementReason`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `CausalDivergenceAnchorDto`, `CausalEpisodeDto`, `CausalFeedbackDto`, `CausalHypothesisDto`, `CausalProbeOfferDto`, `CausalRepairActionId`, `CausalRepairStatusDto`, `CausalRepairStatusState`, `CausalTargetRefDto`, `RepairedTraceDto`, `UnresolvedCauseSelfReportResponse`; references `CausalDivergenceAnchorDto`, `CausalEpisodeDto`, `CausalFeedbackDto`, `CausalHypothesisDto`, `CausalProbeOfferDto`, `CausalRepairActionId`, `CausalRepairStatusDto`, `CausalRepairStatusState`, `CausalTargetRefDto`, `RepairedTraceDto`, `UnresolvedCauseSelfReportResponse`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export: `ClaimCandidateDto`, `PresentedClaimDto`; references `ClaimCandidateDto`, `PresentedClaimDto`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export: `CliCommandResult`, `SessionSnapshot`; references `CliCommandResult`, `SessionSnapshot`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export: `AnimationRuntimeDto`, `ConceptAnimationDto`; references `AnimationRuntimeDto`, `ConceptAnimationDto`
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
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export: `IngestBudgetField`, `IngestBudgetsDto`, `RuntimeHealth`, `SettingsDto`, `UseCaseChoiceInput`; references `IngestBudgetField`, `IngestBudgetsDto`, `RuntimeHealth`, `SettingsDto`, `UseCaseChoiceInput`
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
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/dto.ts](../../../../../../apps/learnloop-tauri/src/api/dto.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
