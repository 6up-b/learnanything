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
| Source lines | 1051 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]]

## Public API

- `export const api =` — const, line 283

## Internal implementation anchors

- `async function call<T>(command: string, args: Record<string, unknown> =` — function, line 244
- `function normalizeError(error: unknown): CommandError` — function, line 252
- `const commandError = error as CommandError` — const, line 254
- `const validationErrors = (commandError.details as` — const, line 255

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AddToCollection|src/components/AddToCollection.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CausalAttribution|src/components/CausalAttribution.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ClaimSurface|src/components/ClaimSurface.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ConceptAnimationSection|src/components/ConceptAnimationSection.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/FacetInspector|src/components/FacetInspector.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalBanner|src/components/GoalBanner.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalReviewCard|src/components/GoalReviewCard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/GoalWizard|src/components/GoalWizard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/IngestActivity|src/components/IngestActivity.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/KnowledgeModel|src/components/KnowledgeModel.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/OutlineAndPlan|src/components/OutlineAndPlan.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ProbeBlockResult|src/components/ProbeBlockResult.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/ProvenancePanel|src/components/ProvenancePanel.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/QuestionQueue|src/components/QuestionQueue.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/SourceLibrarySidebar|src/components/SourceLibrarySidebar.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/TrackRecordView|src/components/TrackRecordView.tsx]] — import-or-re-export: `api`; references `api`
- [[Reference/Desktop/TypeScript/components/WriteCardDialog|src/components/WriteCardDialog.tsx]] — import-or-re-export: `api`; references `api`
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
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export: `api`; references `api`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AcceptEdgeResultDto`, `AcquisitionPreview`, `AdjudicationQueueDto`, `AdjudicationRecordInput`, `AdjudicationRecordResultDto`, `AdjudicationScoreboardDto`, `AnimationRuntimeDto`, `AnswerCalibrationReportDto`, `AnswerGradingClarificationResultDto`, `AppSnapshot`, `AppendResultDto`, `AppendSourceInput`, `AskTutorQuestionInput`, `AssessOpenDto`, `AssessResultDto`, `AttemptResultDto`, `AttemptTraceDto`, `AttemptTraceEvidenceDto`, `BeginProbeDialogueResult`, `BlueprintReadinessPreviewDto`, `BlueprintVersionDto`, `BoundaryDiffDto`, `BuildPlan`, `BuildPlanSelectionInput`, `BuildStudyMapInput`, `CalibrationSessionProgressDto`, `CapabilityGridResult`, `CausalProbeDeferResultDto`, `CausalProbeOfferResultDto`, `CausalRepairStatusResultDto`, `ClaimCandidateDto`, `CliCommandResult`, `CommandError`, `ComposeDraftResult`, `ConceptAnimationDto`, `ConceptGraphSnapshot`, `ConfirmQuickAddInput`, `ConfirmReceiptDto`, `CreateGoalInput`, `CreateGoalResult`, `CreateStudyMapInput`, `CreateVaultInput`, `CreateVaultResult`, `DecayPressureSnapshot`, `DepthInvitationResultDto`, `EffectiveOutlineDto`, `ElicitingResponseResultDto`, `EndProbeDialogueResult`, `EntityProvenance`, `ExamAnswerResult`, `ExamReadinessReportDto`, `ExamReportSnapshot`, `ExamSessionSnapshot`, `ExamStatusSnapshot`, `ExemplarPoolSnapshot`, `FacetDetailDto`, `FacetEvidenceTimelineDto`, `FacetListDto`, `FacetMasterySnapshot`, `FacetMergeResultDto`, `FeedbackBundle`, `ForecastTrackRecordDto`, `GenerateCommissioningPracticeResult`, `GenerateStarterPracticeResult`, `GetNextProbeItemDto`, `GoalDto`, `GoalFeasibilityInput`, `GoalFeasibilityResult`, `GoalReportSnapshot`, `GoalSeriesSnapshot`, `GoalsListSnapshot`, `GradingClarificationResultDto`, `GradingProviderResult`, `GuidedRedoDto`, `HypothesisEventDto`, `IngestBatchDto`, `IngestBatchesSnapshot`, `IngestBudgetsDto`, `IngestJobDto`, `IngestJobsSnapshot`, `IngestSourceClassification`, `InspectorEntity`, `KnowledgeMapHistory`, `KnowledgeMapPreviewDto`, `KnowledgeMapSnapshot`, `LadderAdvanceResultDto`, `LadderPolicyDto`, `LadderStatusDto`, `LearnerProfileDto`, `MaintenanceFeedSnapshot`, `MaintenanceNoticeDto`, `MeasurementHealthDto`, `NextProbeDialogueTurnResult`, `OpenrouterKeyResult`, `OverconfidenceSnapshot`, `PlanQuickAddInput`, `PoolDto`, `PoolForRunDto`, `PoolNextSurfaceDto`, `PoolStatusDto`, `PracticeItemDetail`, `PracticeSubmissionAcknowledgementDto`, `PracticeSubmissionRecoveryDto`, `PresentedClaimDto`, `PreviewBlueprintReadinessInput`, `PreviewKnowledgeMapInput`, `PrimedRetryResultDto`, `ProbeContractDto`, `ProbeRemintResultDto`, `PromoteTutorQuestionResult`, `PromotionIntent`, `ProposalsSnapshot`, `ProposeFacetMergeInput`, `ProposeGraphEditsInput`, `ProposeGraphEditsResult`, `QuestionQueueSnapshot`, `QuestionResolution`, `QueueInput`, `QueueRestructureRequestInput`, `QueueRestructureRequestResult`, `QueueRevisionDto`, `QueueSnapshot`, `QuickAddConfirmationDto`, `QuickAddPlanDto`, `QuickAddResultDto`, `ReaderAnnotationResultDto`, `ReaderAnswerDto`, `ReaderAnswerMode`, `ReaderArcDto`, `ReaderAskHistoryDto`, `ReaderAskInput`, `ReaderAuthorQAInput`, `ReaderAuthorSectionQuestionDto`, `ReaderAuthoredCardDto`, `ReaderAuthoredQuestionDto`, `ReaderBlockRegionDto`, `ReaderCaptureInput`, `ReaderCaptureReceiptDto`, `ReaderCoachLintDto`, `ReaderCreateAnnotationInput`, `ReaderDisposition`, `ReaderDispositionResultDto`, `ReaderEnqueueRequestDto`, `ReaderEnqueueRequestInput`, `ReaderExerciseImportReceiptDto`, `ReaderExerciseImportStatusDto`, `ReaderGuidePlanDto`, `ReaderImportExerciseInput`, `ReaderInvokePresetInput`, `ReaderMaintainInput`, `ReaderMarkProgressResultDto`, `ReaderPdfViewDto`, `ReaderPresetReceiptDto`, `ReaderProgressListDto`, `ReaderPromptContractDto`, `ReaderQuestionControlResultDto`, `ReaderRenderViewDto`, `ReaderRequestRow`, `ReaderRestorationDto`, `ReaderSetModeResultDto`, `ReaderSourceSearchDto`, `ReaderTranslateSelectionInput`, `ReaderTranslationDto`, `ReaderWatchPlanDto`, `RecentIngestsSnapshot`, `RecordProbeDialogueTurnResult`, `ReentrySummarySnapshot`, `RefreshResultDto`, `RefreshRevisionInput`, `RemediationDto`, `RequestConceptAnimationResult`, `ResolveConflictInput`, `ResolveEdgeDirectionInput`, `ResolveEdgeDirectionResult`, `ResolveQuestionEventResult`, `RestoreDto`, `RetirementReason`, `RetrySynthesisInput`, `ReviewCountsDto`, `ReviewLogDto`, `RunAdvanceResultDto`, `RunListDto`, `RunStateDto`, `RungVariantRequestDto`, `RungVariantRequestResultDto`, `RuntimeHealth`, `SaveUnitSelectionInput`, `SchedulerExplanationDto`, `SelectionPreviewDto`, `SessionEndSummary`, `SessionSnapshot`, `SessionStartInput`, `SettingsDto`, `SourceConflictDto`, `SourceCoverageDto`, `SourceDeletionPlanDto`, `SourceDeletionResultDto`, `SourceLibrarySnapshot`, `SourceOutline`, `SourceSetDto`, `SourceSetsSnapshot`, `SpanViewDto`, `SpanViewInput`, `SqliteExecResult`, `SqliteTableSnapshot`, `SqliteTablesSnapshot`, `StartCalibrationSessionInput`, `StartExtractionRepairInput`, `StartImportBatchInput`, `StartIngestInput`, `StartInventoryInput`, `StartOverconfidenceProbeResult`, `StartRemediationDto`, `StartTeachBackInput`, `StartTeachBackResult`, `StartingLevel`, `StopProbeResultDto`, `StudyMapDto`, `SubjectRegistryDto`, `SubmitAttemptInput`, `SubmitTeachBackTurnInput`, `SynthesisCandidateSummary`, `TeachBackTurnResult`, `TranscriptionKeyResult`, `TriageResultDto`, `TriageStatusDto`, `TutorAnswerDto`, `TutorOpeningDto`, `TutorSaveNoteResult`, `TutorTranscriptInput`, `TutorTranscriptSnapshot`, `UnitSelectionState`, `UnresolvedCauseSelfReportResponse`, `UnresolvedCauseSelfReportResultDto`, `UpdateAiSettingsInput`, `UpdateIngestSettingsInput`, `VaultFileContent`, `VaultSummary`, `VaultTreeSnapshot`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/core`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Adapter Architecture#Sidecar structure|sidecar structure]] — owns the four-layer RPC contract.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct source contract: references the exact source path.
- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Add or change an RPC in all four layers: DTO, client facade, Rust command/registration, and Python sidecar handler/registry.
- Preserve camelCase wire names and typed error behavior; exercise `tests/test_desktop_rpc_contract.py` plus the feature's sidecar tests.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/api/client.ts](../../../../../../apps/learnloop-tauri/src/api/client.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
