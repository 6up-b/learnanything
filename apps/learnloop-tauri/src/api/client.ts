import { invoke } from "@tauri-apps/api/core";
import { invalidate, invalidateAll, setQueryData, type QueryTag } from "./queryCache";
import { READER_PREFIX, TAG } from "./queryTags";
import type {
  AppSnapshot,
  AnswerCalibrationReportDto,
  CreateVaultInput,
  CreateVaultResult,
  LearnerProfileDto,
  ProbeRemintResultDto,
  RungVariantRequestDto,
  RungVariantRequestResultDto,
  StartingLevel,
  AttemptResultDto,
  CliCommandResult,
  CommandError,
  ConceptGraphSnapshot,
  ConfirmQuickAddInput,
  EntityProvenance,
  FacetMergeResultDto,
  PlanQuickAddInput,
  ProposeFacetMergeInput,
  QuickAddConfirmationDto,
  QuickAddPlanDto,
  QuickAddResultDto,
  SpanViewDto,
  SpanViewInput,
  SubjectRegistryDto,
  FacetMasterySnapshot,
  AttemptTraceDto,
  CapabilityGridResult,
  FacetEvidenceTimelineDto,
  FeedbackBundle,
  AttemptTraceEvidenceDto,
  GradingClarificationResultDto,
  AnswerGradingClarificationResultDto,
  UnresolvedCauseSelfReportResponse,
  ElicitingResponseResultDto,
  UnresolvedCauseSelfReportResultDto,
  CausalProbeDeferResultDto,
  CausalProbeOfferResultDto,
  CausalRepairStatusResultDto,
  StartRemediationDto,
  PrimedRetryResultDto,
  GuidedRedoDto,
  GradingProviderResult,
  AnimationRuntimeDto,
  ConceptAnimationDto,
  OpenrouterKeyResult,
  RequestConceptAnimationResult,
  SettingsDto,
  TranscriptionKeyResult,
  UpdateAiSettingsInput,
  UpdateIngestSettingsInput,
  UpdateAnimationSettingsInput,
  DetectProviderCapabilitiesInput,
  ProviderCapabilitiesDto,
  UpdateProviderModalitiesInput,
  InspectorEntity,
  KnowledgeMapHistory,
  KnowledgeMapSnapshot,
  PracticeItemDetail,
  PracticeSubmissionAcknowledgementDto,
  PracticeSubmissionRecoveryDto,
  GetNextProbeItemDto,
  ProbeContractDto,
  ProposalsSnapshot,
  StopProbeResultDto,
  QueueInput,
  QueueSnapshot,
  RecentIngestsSnapshot,
  IngestJobDto,
  IngestJobsSnapshot,
  IngestSourceClassification,
  StartIngestInput,
  IngestBatchDto,
  IngestBatchesSnapshot,
  RetrySynthesisInput,
  SynthesisCandidateSummary,
  StartImportBatchInput,
  SourceDeletionPlanDto,
  SourceDeletionResultDto,
  SourceLibrarySnapshot,
  SourceOutline,
  SelectionPreviewDto,
  EffectiveOutlineDto,
  SaveUnitSelectionInput,
  UnitSelectionState,
  AcquisitionPreview,
  BuildPlan,
  BuildPlanSelectionInput,
  IngestBudgetsDto,
  StartExtractionRepairInput,
  RuntimeHealth,
  SchedulerExplanationDto,
  SessionEndSummary,
  SessionSnapshot,
  SessionStartInput,
  SqliteExecResult,
  SqliteTableSnapshot,
  SqliteTablesSnapshot,
  VaultFileContent,
  VaultSummary,
  VaultTreeSnapshot,
  SubmitAttemptInput,
  AskTutorQuestionInput,
  TutorAnswerDto,
  TutorOpeningDto,
  TutorTranscriptInput,
  TutorTranscriptSnapshot,
  TutorSaveNoteResult,
  PromotionIntent,
  PromoteTutorQuestionResult,
  QuestionQueueSnapshot,
  QueueRevisionDto,
  QuestionResolution,
  ResolveQuestionEventResult,
  RetirementReason,
  StartTeachBackInput,
  StartTeachBackResult,
  SubmitTeachBackTurnInput,
  TeachBackTurnResult,
  BeginProbeDialogueResult,
  CalibrationSessionProgressDto,
  CreateGoalInput,
  EndProbeDialogueResult,
  NextProbeDialogueTurnResult,
  RecordProbeDialogueTurnResult,
  CreateGoalResult,
  ExamAnswerResult,
  ExamReportSnapshot,
  ExamSessionSnapshot,
  ExamStatusSnapshot,
  GenerateCommissioningPracticeResult,
  GenerateStarterPracticeResult,
  GoalDto,
  GoalFeasibilityInput,
  GoalFeasibilityResult,
  GoalReportSnapshot,
  GoalSeriesSnapshot,
  GoalsListSnapshot,
  StartCalibrationSessionInput,
  SourceSetDto,
  SourceSetsSnapshot,
  SourceCoverageDto,
  StartInventoryInput,
  CreateStudyMapInput,
  BuildStudyMapInput,
  StudyMapDto,
  AppendResultDto,
  AppendSourceInput,
  RefreshResultDto,
  RefreshRevisionInput,
  MaintenanceFeedSnapshot,
  MeasurementHealthDto,
  ReviewCountsDto,
  MaintenanceNoticeDto,
  SourceConflictDto,
  ResolveConflictInput,
  ExamReadinessReportDto,
  ClaimCandidateDto,
  ForecastTrackRecordDto,
  HypothesisEventDto,
  PresentedClaimDto,
  RemediationDto,
  ReviewLogDto,
  OverconfidenceSnapshot,
  StartOverconfidenceProbeResult,
  ReentrySummarySnapshot,
  DecayPressureSnapshot,
  ProposeGraphEditsInput,
  ProposeGraphEditsResult,
  QueueRestructureRequestInput,
  QueueRestructureRequestResult,
  ResolveEdgeDirectionInput,
  ResolveEdgeDirectionResult,
  FacetDetailDto,
  FacetListDto,
  PreviewKnowledgeMapInput,
  KnowledgeMapPreviewDto,
  PreviewBlueprintReadinessInput,
  BlueprintReadinessPreviewDto,
  BlueprintVersionDto,
  ComposeDraftResult,
  ExemplarPoolSnapshot,
  ConfirmReceiptDto,
  RunStateDto,
  RunListDto,
  RunAdvanceResultDto,
  AssessOpenDto,
  AssessResultDto,
  BoundaryDiffDto,
  RestoreDto,
  DepthInvitationResultDto,
  AcceptEdgeResultDto,
  TriageResultDto,
  TriageStatusDto,
  LadderPolicyDto,
  LadderStatusDto,
  LadderAdvanceResultDto,
  PoolDto,
  PoolStatusDto,
  PoolForRunDto,
  PoolNextSurfaceDto,
  ReaderPromptContractDto,
  ReaderAskInput,
  ReaderAnswerDto,
  ReaderAskHistoryDto,
  ReaderGuidePlanDto,
  ReaderMarkProgressResultDto,
  ReaderProgressListDto,
  ReaderAuthorSectionQuestionDto,
  ReaderAuthoredQuestionDto,
  ReaderSourceSearchDto,
  ReaderAnswerMode,
  ReaderDisposition,
  ReaderDispositionResultDto,
  ReaderRenderViewDto,
  ReaderPdfViewDto,
  ReaderWatchPlanDto,
  ReaderTranslateSelectionInput,
  ReaderTranslationDto,
  ReaderCaptureInput,
  ReaderCaptureReceiptDto,
  ReaderCreateAnnotationInput,
  ReaderAnnotationResultDto,
  ReaderBlockRegionDto,
  ReaderInvokePresetInput,
  ReaderPresetReceiptDto,
  ReaderSetModeResultDto,
  ReaderQuestionControlResultDto,
  ReaderEnqueueRequestInput,
  ReaderEnqueueRequestDto,
  ReaderRequestRow,
  ReaderAuthorQAInput,
  ReaderAuthoredCardDto,
  ReaderImportExerciseInput,
  ReaderExerciseImportReceiptDto,
  ReaderExerciseImportStatusDto,
  ReaderCoachLintDto,
  ReaderMaintainInput,
  ReaderArcDto,
  ReaderRestorationDto,
  AdjudicationQueueDto,
  AdjudicationRecordInput,
  AdjudicationRecordResultDto,
  AdjudicationScoreboardDto,
} from "./dto";

// Development aid for verifying the query cache: with
// localStorage.setItem("learnloop.debugRpc", "1") every sidecar command is
// counted and logged, so "returning to a tab issued no RPC" is checkable from
// the devtools console (window.__llRpcCounts). Off in production builds.
function readRpcDebugFlag(): boolean {
  try {
    return localStorage.getItem("learnloop.debugRpc") === "1";
  } catch {
    return false;
  }
}
const RPC_DEBUG = import.meta.env.DEV && readRpcDebugFlag();
const rpcCounts = new Map<string, number>();
if (RPC_DEBUG) {
  (window as unknown as { __llRpcCounts?: Map<string, number> }).__llRpcCounts = rpcCounts;
}

async function call<T>(command: string, args: Record<string, unknown> = {}): Promise<T> {
  if (RPC_DEBUG) {
    const count = (rpcCounts.get(command) ?? 0) + 1;
    rpcCounts.set(command, count);
    console.debug(`[rpc ${count}] ${command}`);
  }
  try {
    return await invoke<T>(command, args);
  } catch (error) {
    throw normalizeError(error);
  }
}

function normalizeError(error: unknown): CommandError {
  if (error && typeof error === "object" && "code" in error && "message" in error) {
    const commandError = error as CommandError;
    const validationErrors = (commandError.details as { errors?: Array<{ type?: string }> } | undefined)?.errors;
    if (commandError.code === "validation_error" && validationErrors?.some((entry) => entry.type === "extra_forbidden")) {
      return {
        ...commandError,
        code: "stale_sidecar_schema",
        message: "The frontend is newer than the running LearnLoop sidecar. Restart the Tauri app to load the updated request schema.",
        retryable: false
      };
    }
    return commandError;
  }
  // Tauri rejects with "Command <name> not found" when the running Rust binary
  // predates a newly added #[tauri::command] (e.g. dev app not restarted after
  // a Rust rebuild). Surface an actionable message instead of the raw string.
  if (typeof error === "string" && /^Command \S+ not found/.test(error)) {
    return {
      code: "stale_app_binary",
      message: `${error}. The running app is older than the frontend — restart the app (npm run dev) to load the new backend commands.`,
      retryable: false
    };
  }
  return {
    code: "internal",
    message: typeof error === "string" ? error : "Tauri command failed.",
    retryable: false
  };
}

// ---------------------------------------------------------------------------
// Cache invalidation after mutations.
//
// A mutation wrapper marks the cached reads it can affect stale once the
// sidecar has acknowledged the change, so every caller (screens, overlays,
// dialogs) keeps the query cache consistent without knowing it exists. Tags
// are coarse on purpose; a missed tag costs a brief stale paint (every mount
// revalidates), never a permanently stale screen.
// ---------------------------------------------------------------------------

/** Reads affected by any attempt, grade, remediation, or claim response. */
const ATTEMPT_TAGS: readonly QueryTag[] = [TAG.queue, TAG.graph, TAG.goals, TAG.review, TAG.maintenance];
/** Reads affected by ingest/source-set/study-map work. */
const INGEST_TAGS: readonly QueryTag[] = [TAG.sources, TAG.library, TAG.maintenance];
/** Reads affected when a new revision or appended source reshapes the map. */
const REVISION_TAGS: readonly QueryTag[] = [TAG.sources, TAG.graph, TAG.proposals, TAG.registry, TAG.maintenance];

function mutating<T>(tags: readonly QueryTag[], promise: Promise<T>): Promise<T> {
  return promise.then((result) => {
    invalidate({ tags });
    return result;
  });
}

/** For operations that can touch arbitrary state (SQL admin, CLI passthrough, vault reload). */
function mutatingAll<T>(promise: Promise<T>): Promise<T> {
  return promise.then((result) => {
    invalidateAll();
    return result;
  });
}

/** Reader mutations mostly know an annotation/extraction id, not the source: invalidate every per-source reader read. */
function mutatingReader<T>(promise: Promise<T>, extraTags: readonly QueryTag[] = []): Promise<T> {
  return promise.then((result) => {
    invalidate({ tagPrefix: READER_PREFIX });
    if (extraTags.length) invalidate({ tags: extraTags });
    return result;
  });
}

/** Proposal mutations return the full snapshot: seed the cache with it instead of refetching. */
function afterProposalMutation(
  promise: Promise<ProposalsSnapshot>,
  extraTags: readonly QueryTag[] = []
): Promise<ProposalsSnapshot> {
  return promise.then((snapshot) => {
    setQueryData(["get_proposals"], snapshot, [TAG.proposals]);
    if (extraTags.length) invalidate({ tags: extraTags });
    return snapshot;
  });
}

/** Settings mutations return the full settings payload: seed it, then refresh the other settings-tagged reads. */
function afterSettingsMutation(promise: Promise<SettingsDto>): Promise<SettingsDto> {
  return promise.then((settings) => {
    setQueryData(["get_settings"], settings, [TAG.settings]);
    invalidate({ tags: [TAG.settings] });
    return settings;
  });
}

export const api = {
  selectVault: (path?: string | null) => call<VaultSummary | null>("select_vault", { path }),
  loadVault: () => call<AppSnapshot>("load_vault"),
  getReviewCounts: () => call<ReviewCountsDto>("get_review_counts"),
  createVault: (input: CreateVaultInput) => call<CreateVaultResult>("create_vault", { input }),
  getLearnerProfile: () => call<LearnerProfileDto>("get_learner_profile"),
  setLearnerProfile: (input: { startingLevel: StartingLevel; levelNote?: string | null }) =>
    mutating([TAG.settings], call<LearnerProfileDto>("set_learner_profile", { input })),
  reloadVault: () => mutatingAll(call<AppSnapshot>("reload_vault")),
  getRuntimeHealth: () => call<RuntimeHealth>("get_runtime_health"),
  startSession: (input: SessionStartInput) => mutating([TAG.queue], call<SessionSnapshot>("start_session", { input })),
  getSession: (sessionId: string) => call<SessionSnapshot>("get_session", { sessionId }),
  clearSessionCheckpoint: (sessionId: string) => call<{ cleared: boolean }>("clear_session_checkpoint", { sessionId }),
  endSession: (sessionId: string) => mutating([TAG.queue], call<SessionEndSummary>("end_session", { sessionId })),
  getTodayQueue: (input: QueueInput) => call<QueueSnapshot>("get_today_queue", { input }),
  getQueueRevision: () => call<QueueRevisionDto>("get_queue_revision"),
  explainPracticeItem: (practiceItemId: string) =>
    call<SchedulerExplanationDto>("explain_practice_item", { practiceItemId }),
  openQueueItem: (practiceItemId: string) => call<PracticeItemDetail>("open_queue_item", { practiceItemId }),
  // `sessionId` marks this as a serve rather than a read: it is what lets the
  // sidecar spend (and bound) the Meas §3.A6 per-session elicitation budget.
  // Omit it for read-only opens — the detail then carries `elicitation: null`.
  getPracticeItem: (practiceItemId: string, sessionId?: string | null) =>
    call<PracticeItemDetail>("get_practice_item", { practiceItemId, sessionId: sessionId ?? null }),
  getProbeContract: (practiceItemId: string, sessionId?: string) =>
    call<ProbeContractDto>("get_probe_contract", { practiceItemId, sessionId: sessionId ?? null }),
  stopProbeDiagnosing: (practiceItemId: string) =>
    call<StopProbeResultDto>("stop_probe_diagnosing", { practiceItemId }),
  getNextProbeItem: (learningObjectId: string) =>
    call<GetNextProbeItemDto>("get_next_probe_item", { learningObjectId }),
  savePracticeDraft: (input: {
    sessionId: string;
    practiceItemId: string;
    answerMd: string;
    hintsUsed: number;
    submissionId: string;
  }) => call<{ ok: boolean }>("save_practice_draft", { input }),
  recoverPracticeSubmission: (input: {
    sessionId: string;
    practiceItemId: string;
    submissionId: string;
  }) => call<PracticeSubmissionRecoveryDto>("recover_practice_submission", { input }),
  acknowledgePracticeSubmission: (input: {
    sessionId: string;
    practiceItemId: string;
    submissionId: string;
  }) => call<PracticeSubmissionAcknowledgementDto>("acknowledge_practice_submission", { input }),
  submitAttempt: (input: SubmitAttemptInput) => mutating(ATTEMPT_TAGS, call<AttemptResultDto>("submit_attempt", { input })),
  submitDontKnow: (input: {
    sessionId: string;
    practiceItemId: string;
    hintsUsed: number;
    latencySeconds?: number | null;
    probePresentationId?: string | null;
    answerConfidence?: number | null;
    assessmentContractVersionId?: string | null;
    submissionId?: string | null;
  }) => mutating(ATTEMPT_TAGS, call<AttemptResultDto>("submit_dont_know", { input })),
  skipPracticeItem: (input: { sessionId: string; practiceItemId: string }) =>
    mutating([TAG.queue], call<QueueSnapshot>("skip_practice_item", { input })),
  getFeedback: (attemptId: string) => call<FeedbackBundle>("get_feedback", { attemptId }),
  getAttempt: (attemptId: string) => call<unknown>("get_attempt", { attemptId }),
  // Meas §3.A6/§3.A8 — the two post-grade reads the feedback surface owes the
  // learner: what a volunteered explanation bought, and the one question that
  // can still move a provisional grade.
  getAttemptTraceEvidence: (attemptId: string) =>
    call<AttemptTraceEvidenceDto>("get_attempt_trace_evidence", { attemptId }),
  getGradingClarification: (attemptId: string) =>
    call<GradingClarificationResultDto>("get_grading_clarification", { attemptId }),
  answerGradingClarification: (attemptId: string, answerMd: string) =>
    mutating(ATTEMPT_TAGS, call<AnswerGradingClarificationResultDto>("answer_grading_clarification", {
      input: { attemptId, answerMd }
    })),
  triggerRegrade: (attemptId: string) => mutating(ATTEMPT_TAGS, call<FeedbackBundle>("trigger_regrade", { input: { attemptId } })),
  addErrorEvent: (attemptId: string, errorType: string, severity = 0.5) =>
    mutating([TAG.review, TAG.maintenance], call<FeedbackBundle>("add_error_event", { input: { attemptId, errorType, severity } })),
  triggerFollowup: (attemptId: string) =>
    call<FeedbackBundle>("trigger_followup", { input: { attemptId } }),
  rateFollowup: (attemptId: string, useful: boolean) =>
    call<FeedbackBundle>("rate_followup", { input: { attemptId, useful } }),
  reportUnresolvedCause: (input: {
    factorId: string;
    response: UnresolvedCauseSelfReportResponse;
    candidateIndex?: number | null;
  }) =>
    mutating(ATTEMPT_TAGS, call<UnresolvedCauseSelfReportResultDto>("report_unresolved_cause", {
      input: { ...input, candidateIndex: input.candidateIndex ?? null }
    })),
  /**
   * The learner's unaided answer to an eliciting repair suggestion's question.
   * `suggestionIndex` indexes `feedback.repairSuggestions`.
   */
  submitElicitingResponse: (input: {
    attemptId: string;
    suggestionIndex: number;
    responseMd: string;
  }) => mutating(ATTEMPT_TAGS, call<ElicitingResponseResultDto>("submit_eliciting_response", { input })),
  contestCausalDiagnosis: (
    attemptId: string,
    response: Exclude<UnresolvedCauseSelfReportResponse, "believed_candidate">,
  ) =>
    mutating(ATTEMPT_TAGS, call<UnresolvedCauseSelfReportResultDto>("contest_causal_diagnosis", {
      input: { attemptId, response }
    })),
  // ── P2 causal repair orchestration (spec_causal_attribution_v1 §6) ────────
  // One orchestration service behind four RPCs. `causalRepairStatus` is a pure
  // read (it records the decision receipt but mints no remediation episode);
  // the three action calls are the learner offer.
  causalRepairStatus: (misconceptionId: string, sessionId?: string | null) =>
    call<CausalRepairStatusResultDto>("causal_repair_status", {
      input: { misconceptionId, sessionId: sessionId ?? null }
    }),
  /** "Take the quick check" — enter the factor-aware episode and pin the probe. */
  causalProbeOfferAction: (input: {
    factorId: string;
    misconceptionId?: string | null;
    sessionId?: string | null;
    decisionReceiptId?: string | null;
  }) =>
    mutating(ATTEMPT_TAGS, call<CausalProbeOfferResultDto>("causal_probe_offer_action", {
      input: {
        factorId: input.factorId,
        misconceptionId: input.misconceptionId ?? null,
        sessionId: input.sessionId ?? null,
        decisionReceiptId: input.decisionReceiptId ?? null
      }
    })),
  /** "Not now" — persists the decline so the next attempt does not re-offer.
   *  The factor stays divergent; only the offer is withdrawn. */
  causalProbeDefer: (input: {
    factorId: string;
    misconceptionId?: string | null;
    sessionId?: string | null;
  }) =>
    mutating(ATTEMPT_TAGS, call<CausalProbeDeferResultDto>("causal_probe_defer", {
      input: {
        factorId: input.factorId,
        misconceptionId: input.misconceptionId ?? null,
        sessionId: input.sessionId ?? null
      }
    })),
  /** "Teach me now" — explicit learner authorisation to repair under ambiguity. */
  causalTeachMeNow: (input: {
    factorId: string;
    misconceptionId: string;
    sessionId?: string | null;
  }) =>
    mutating(ATTEMPT_TAGS, call<CausalRepairStatusResultDto>("causal_teach_me_now", {
      input: {
        factorId: input.factorId,
        misconceptionId: input.misconceptionId,
        sessionId: input.sessionId ?? null
      }
    })),
  startPrimedRetry: (attemptId: string) =>
    mutating([TAG.queue], call<PrimedRetryResultDto>("start_primed_retry", { input: { attemptId } })),
  startGuidedRedo: (attemptId: string) =>
    mutating([TAG.queue], call<GuidedRedoDto>("start_guided_redo", { input: { attemptId } })),
  inspectEntity: (id: string) => call<InspectorEntity>("inspect_entity", { id }),
  getConceptGraph: () => call<ConceptGraphSnapshot>("get_concept_graph"),
  getVaultTree: () => call<VaultTreeSnapshot>("get_vault_tree"),
  getRecentIngests: () => call<RecentIngestsSnapshot>("get_recent_ingests"),
  classifyIngestSource: (source: string) =>
    call<IngestSourceClassification>("classify_ingest_source", { input: { source } }),
  startIngest: (input: StartIngestInput) => mutating(INGEST_TAGS, call<IngestJobDto>("start_ingest", { input })),
  getIngestJob: (jobId: string) => call<IngestJobDto>("get_ingest_job", { jobId }),
  getIngestJobs: () => call<IngestJobsSnapshot>("get_ingest_jobs"),
  cancelIngest: (jobId: string) => mutating(INGEST_TAGS, call<IngestJobDto>("cancel_ingest", { jobId })),
  startImportBatch: (input: StartImportBatchInput) => mutating(INGEST_TAGS, call<IngestBatchDto>("start_import_batch", { input })),
  getIngestBatch: (batchId: string) => call<IngestBatchDto>("get_ingest_batch", { batchId }),
  listIngestBatches: (limit = 30) => call<IngestBatchesSnapshot>("list_ingest_batches", { input: { limit } }),
  cancelIngestBatch: (batchId: string) => mutating(INGEST_TAGS, call<IngestBatchDto>("cancel_ingest_batch", { batchId })),
  resumeIngestBatch: (batchId: string) => mutating(INGEST_TAGS, call<IngestBatchDto>("resume_ingest_batch", { batchId })),
  retrySynthesis: (input: RetrySynthesisInput) =>
    mutating(INGEST_TAGS, call<IngestBatchDto>("retry_synthesis", { input })),
  getSynthesisCandidate: (batchId: string) =>
    call<SynthesisCandidateSummary>("get_synthesis_candidate", { batchId }),
  getSourceLibrary: () => call<SourceLibrarySnapshot>("get_source_library"),
  // Read-only impact report; `delete_source` is the destructive half and
  // re-checks the same blockers, so the preview is advisory, not a token.
  previewSourceDeletion: (sourceId: string) =>
    call<{ version: number; plan: SourceDeletionPlanDto }>("preview_source_deletion", { sourceId }),
  deleteSource: (sourceId: string) =>
    mutating(INGEST_TAGS, call<{ version: number; deleted: SourceDeletionResultDto }>("delete_source", { sourceId })),
  getSourceOutline: (extractionRef: string) =>
    call<SourceOutline>("get_source_outline", { extractionRef }),
  getSelectionPreview: (extractionRef: string, selectedUnitIds?: string[] | null) =>
    call<SelectionPreviewDto>("get_selection_preview", {
      input: { extractionRef, selectedUnitIds: selectedUnitIds ?? null }
    }),
  getEffectiveOutline: (extractionRef: string, boundaryOverrides: Record<string, unknown>[]) =>
    call<EffectiveOutlineDto>("get_effective_outline", { input: { extractionRef, boundaryOverrides } }),
  saveUnitSelection: (input: SaveUnitSelectionInput) =>
    mutating(INGEST_TAGS, call<{ version: number } & UnitSelectionState & { extractionId: string }>("save_unit_selection", { input })),
  getAcquisitionPreview: (inputs: string[]) =>
    call<AcquisitionPreview>("get_acquisition_preview", { input: { inputs } }),
  // `budgetOverrides` makes the plan chart the per-run ceilings the learner set
  // on the plan screen rather than the vault's [ingest.budgets] defaults.
  getBuildPlan: (
    selections: BuildPlanSelectionInput[],
    subjectId?: string | null,
    budgetOverrides?: Partial<IngestBudgetsDto>
  ) =>
    call<BuildPlan>("get_build_plan", {
      input: { selections, subjectId: subjectId ?? null, budgetOverrides: budgetOverrides ?? {} }
    }),
  startExtractionRepair: (input: StartExtractionRepairInput) =>
    mutating(INGEST_TAGS, call<IngestBatchDto>("start_extraction_repair", { input })),
  listSourceSets: () => call<SourceSetsSnapshot>("list_source_sets"),
  getSourceSet: (sourceSetId: string) =>
    call<{ version: number; sourceSet: SourceSetDto }>("get_source_set", { sourceSetId }),
  upsertSourceSet: (input: SourceSetDto) =>
    mutating(INGEST_TAGS, call<{ version: number; sourceSet: SourceSetDto }>("upsert_source_set", { input })),
  getSourceCoverage: (sourceSetId: string) =>
    call<{ version: number; coverage: SourceCoverageDto }>("get_source_coverage", { sourceSetId }),
  startInventory: (input: StartInventoryInput) =>
    mutating(INGEST_TAGS, call<IngestBatchDto>("start_inventory", { input })),
  createStudyMap: (input: CreateStudyMapInput) =>
    mutating(INGEST_TAGS, call<{ version: number; studyMap: StudyMapDto }>("create_study_map", { input })),
  // Enqueue a collection's study-map build as a durable Activity batch (inventory
  // members → bootstrap_synthesis). The multi-member, in-app counterpart to Quick
  // add's confirm step; returns the batch view (IngestBatchDto).
  buildStudyMap: (input: BuildStudyMapInput) => mutating(INGEST_TAGS, call<IngestBatchDto>("build_study_map", { input })),
  // ING M7 — Update study map (§10), maintenance feed (§11), exam readiness (§15).
  appendSource: (input: AppendSourceInput) =>
    mutating(REVISION_TAGS, call<{ version: number; append: AppendResultDto }>("append_source", { input })),
  refreshRevision: (input: RefreshRevisionInput) =>
    mutating(REVISION_TAGS, call<{ version: number; refresh: RefreshResultDto }>("refresh_revision", { input })),
  getMaintenanceFeed: (subjectId?: string | null) =>
    call<MaintenanceFeedSnapshot>("maintenance_feed", { input: { subjectId: subjectId ?? null } }),
  getMeasurementHealth: () => call<MeasurementHealthDto>("get_measurement_health"),
  // Enqueue-and-return: the generation runs on the sidecar's job worker, so this
  // resolves in milliseconds and the caller watches the batch, not this promise.
  generateCommissioningPractice: (input?: {
    learningObjectIds?: string[];
    limit?: number | null;
    reason?: string | null;
  }) =>
    mutating([TAG.queue], call<GenerateCommissioningPracticeResult>("generate_commissioning_practice", {
      input: {
        learningObjectIds: input?.learningObjectIds ?? [],
        limit: input?.limit ?? null,
        reason: input?.reason ?? null
      }
    })),
  scheduleCertificationColdProbes: (learningObjectId?: string | null) =>
    mutating([TAG.queue, TAG.goals, TAG.maintenance], call<{ version: number; schedule: Record<string, unknown> }>(
      "schedule_certification_cold_probes",
      { input: { learningObjectId: learningObjectId ?? null } },
    )),
  transitionCausalProbeCandidate: (input: {
    candidateId: string;
    toStatus: string;
    reviewer?: string | null;
    reason?: string | null;
  }) =>
    mutating([TAG.maintenance], call<{ version: number; candidate: Record<string, unknown> }>(
      "transition_causal_probe_candidate",
      { input: { ...input, reviewer: input.reviewer ?? null, reason: input.reason ?? null } },
    )),
  applyIntegrationBackfill: () =>
    mutatingAll(call<{
      version: number;
      applied: Record<string, unknown>;
      integrationBackfill: MeasurementHealthDto["integrationBackfill"];
    }>("apply_integration_backfill", { input: { confirm: true } })),
  maintenanceNoticeAction: (noticeId: string, action: "dismiss" | "snooze", snoozedUntil?: string | null) =>
    mutating([TAG.maintenance], call<{ version: number; notice: MaintenanceNoticeDto | null }>("maintenance_notice_action", {
      input: { noticeId, action, snoozedUntil: snoozedUntil ?? null }
    })),
  listSourceConflicts: (status = "open") =>
    call<{ version: number; conflicts: SourceConflictDto[] }>("list_source_conflicts", { input: { status } }),
  resolveSourceConflict: (input: ResolveConflictInput) =>
    mutating([TAG.maintenance], call<{ version: number; conflict: SourceConflictDto }>("resolve_source_conflict", { input })),
  getExamReadiness: (subjectId?: string | null) =>
    call<{ version: number; report: ExamReadinessReportDto }>("exam_readiness", {
      input: { subjectId: subjectId ?? null }
    }),
  planQuickAdd: (input: PlanQuickAddInput) =>
    call<{ version: number; plan: QuickAddPlanDto }>("plan_quick_add", { input }),
  confirmQuickAdd: (input: ConfirmQuickAddInput) =>
    mutating(INGEST_TAGS, call<{ version: number; quickAdd: QuickAddResultDto; batch: IngestBatchDto; confirmation: QuickAddConfirmationDto }>(
      "confirm_quick_add",
      { input },
    )),
  getSpanView: (input: SpanViewInput) =>
    call<{ version: number; spanView: SpanViewDto }>("get_span_view", { input }),
  getSubjectRegistry: (subjectId: string) =>
    call<SubjectRegistryDto>("get_subject_registry", { input: { subjectId } }),
  proposeFacetMerge: (input: ProposeFacetMergeInput) =>
    mutating([TAG.proposals], call<{ version: number } & FacetMergeResultDto>("propose_facet_merge", { input })),
  readVaultFile: (path: string) => call<VaultFileContent>("read_vault_file", { path }),
  writeVaultFile: (path: string, body: string) => mutating([TAG.library], call<VaultFileContent>("write_vault_file", { path, body })),
  createVaultFile: (path: string, body = "") =>
    mutating([TAG.library], call<VaultFileContent>("create_vault_file", { input: { path, body } })),
  sqliteTables: (path: string) => call<SqliteTablesSnapshot>("sqlite_tables", { input: { path } }),
  sqliteTable: (path: string, table: string, limit = 200, offset = 0) =>
    call<SqliteTableSnapshot>("sqlite_table", { input: { path, table, limit, offset } }),
  sqliteExec: (path: string, sql: string) => mutatingAll(call<SqliteExecResult>("sqlite_exec", { input: { path, sql } })),
  sqliteUpdateCell: (path: string, table: string, rowid: number, column: string, value: string | null) =>
    mutatingAll(call<{ version: number; ok: boolean }>("sqlite_update_cell", { input: { path, table, rowid, column, value } })),
  sqliteInsertRow: (path: string, table: string) =>
    mutatingAll(call<{ version: number; rowid: number | null }>("sqlite_insert_row", { input: { path, table } })),
  sqliteDeleteRow: (path: string, table: string, rowid: number) =>
    mutatingAll(call<{ version: number; ok: boolean }>("sqlite_delete_row", { input: { path, table, rowid } })),
  getProposals: () => call<ProposalsSnapshot>("get_proposals"),
  getEntityProvenance: (entityType: string, entityId: string) =>
    call<EntityProvenance>("get_entity_provenance", { entityType, entityId }),
  acceptProposalItems: (patchId: string, itemIds?: string[] | null) =>
    afterProposalMutation(call<ProposalsSnapshot>("accept_proposal_items", { input: { patchId, itemIds: itemIds ?? null } }), [TAG.graph, TAG.library, TAG.registry, TAG.queue, TAG.sources, TAG.maintenance]),
  rejectProposalItems: (patchId: string, itemIds?: string[] | null) =>
    afterProposalMutation(call<ProposalsSnapshot>("reject_proposal_items", { input: { patchId, itemIds: itemIds ?? null } })),
  resetProposalItems: (patchId: string, itemIds?: string[] | null) =>
    afterProposalMutation(call<ProposalsSnapshot>("reset_proposal_items", { input: { patchId, itemIds: itemIds ?? null } })),
  editProposalItem: (patchId: string, itemId: string, payloadJson: string) =>
    afterProposalMutation(call<ProposalsSnapshot>("edit_proposal_item", { input: { patchId, itemId, payloadJson } })),
  refreshProposalItemValidation: (patchId: string, itemId: string) =>
    afterProposalMutation(call<ProposalsSnapshot>("refresh_proposal_item_validation", { input: { patchId, itemId } })),
  deleteProposalItem: (patchId: string, itemId: string) =>
    afterProposalMutation(call<ProposalsSnapshot>("delete_proposal_item", { input: { patchId, itemId } })),
  runCliCommand: (argv: string[]) => mutatingAll(call<CliCommandResult>("run_cli_command", { input: { argv } })),
  addNote: (input: {
    subjectId: string;
    noteId: string;
    title: string;
    body: string;
    relatedLos?: string[];
  }) =>
    mutating([TAG.library], call<CliCommandResult>("run_cli_command", {
      input: {
        argv: [
          "add-note",
          input.subjectId,
          input.noteId,
          input.title,
          "--body",
          input.body,
          "--source-type",
          "learner_note",
          ...(input.relatedLos && input.relatedLos.length > 0
            ? ["--related-los", input.relatedLos.join(",")]
            : [])
        ]
      }
    })),
  getFacetMastery: () => call<FacetMasterySnapshot>("get_facet_mastery"),
  // KM3b §9.6 provenance UI.
  getAttemptTrace: (attemptId: string) => call<AttemptTraceDto>("get_attempt_trace", { attemptId }),
  getCapabilityGrid: (learningObjectId: string) =>
    call<CapabilityGridResult>("get_capability_grid", { learningObjectId }),
  getFacetEvidenceTimeline: (facetId: string) =>
    call<FacetEvidenceTimelineDto>("get_facet_evidence_timeline", { facetId }),
  getKnowledgeMap: () => call<KnowledgeMapSnapshot>("get_knowledge_map"),
  // Graph / knowledge-map editor (spec §8/§12). One write path: edits compile to
  // items in the existing proposals machinery.
  proposeGraphEdits: (input: ProposeGraphEditsInput) =>
    mutating([TAG.proposals], call<ProposeGraphEditsResult>("propose_graph_edits", { input })),
  queueRestructureRequest: (input: QueueRestructureRequestInput) =>
    mutating([TAG.proposals], call<QueueRestructureRequestResult>("queue_restructure_request", { input })),
  resolveEdgeDirection: (input: ResolveEdgeDirectionInput) =>
    mutating([TAG.graph, TAG.maintenance], call<ResolveEdgeDirectionResult>("resolve_edge_direction", { input })),
  getFacetDetail: (facetId: string) => call<FacetDetailDto>("get_facet_detail", { facetId }),
  listFacets: () => call<FacetListDto>("list_facets"),
  previewKnowledgeMap: (input: PreviewKnowledgeMapInput) =>
    call<KnowledgeMapPreviewDto>("preview_knowledge_map", { input }),
  previewBlueprintReadiness: (input: PreviewBlueprintReadinessInput) =>
    call<BlueprintReadinessPreviewDto>("preview_blueprint_readiness", { input }),
  getKnowledgeMapHistory: () => call<KnowledgeMapHistory>("get_knowledge_map_history"),
  setGradingProvider: (provider: string) =>
    mutating([TAG.settings], call<GradingProviderResult>("set_grading_provider", { provider })),
  getSettings: () => call<SettingsDto>("get_settings"),
  updateAiSettings: (input: UpdateAiSettingsInput) =>
    afterSettingsMutation(call<SettingsDto>("update_ai_settings", { input })),
  setOpenrouterApiKey: (apiKey: string) =>
    mutating([TAG.settings], call<OpenrouterKeyResult>("set_openrouter_api_key", { apiKey })),
  updateIngestSettings: (input: UpdateIngestSettingsInput) =>
    afterSettingsMutation(call<SettingsDto>("update_ingest_settings", { input })),
  detectProviderCapabilities: (input: DetectProviderCapabilitiesInput) =>
    call<ProviderCapabilitiesDto>("detect_provider_capabilities", { input }),
  updateProviderModalities: (input: UpdateProviderModalitiesInput) =>
    afterSettingsMutation(call<SettingsDto>("update_provider_modalities", { input })),
  setTranscriptionApiKey: (apiKey: string) =>
    mutating([TAG.settings], call<TranscriptionKeyResult>("set_transcription_api_key", { apiKey })),
  updateAnimationSettings: (input: UpdateAnimationSettingsInput) =>
    afterSettingsMutation(call<SettingsDto>("update_animation_settings", { input })),
  getAnimationRuntime: () => call<AnimationRuntimeDto>("get_animation_runtime"),
  requestConceptAnimation: (input: { conceptId: string; learningObjectId?: string | null; consent: boolean }) =>
    call<RequestConceptAnimationResult>("request_concept_animation", { input }),
  getConceptAnimationStatus: (animationId: string) =>
    call<ConceptAnimationDto>("get_concept_animation_status", { animationId }),
  listConceptAnimations: (conceptId: string) =>
    call<{ animations: ConceptAnimationDto[] }>("list_concept_animations", { conceptId }),
  askTutorQuestion: (input: AskTutorQuestionInput) =>
    call<TutorAnswerDto>("ask_tutor_question", { input }),
  previewTutorOpening: (input: { practiceItemId: string; sessionId?: string }) =>
    call<TutorOpeningDto>("preview_tutor_opening", { input }),
  rateTutorAnswer: (eventId: string, useful: boolean) =>
    call<{ ok: boolean }>("rate_tutor_answer", { input: { eventId, useful } }),
  saveTutorAnswerNote: (eventId: string, subjectId?: string) =>
    call<TutorSaveNoteResult>("save_tutor_answer_note", {
      input: { eventId, ...(subjectId ? { subjectId } : {}) }
    }),
  getTutorTranscript: (input: TutorTranscriptInput) =>
    call<TutorTranscriptSnapshot>("get_tutor_transcript", { input }),
  promoteTutorQuestion: (
    eventId: string,
    intent: PromotionIntent,
    options?: { subjectId?: string; learningObjectId?: string }
  ) =>
    mutating([TAG.queue], call<PromoteTutorQuestionResult>("promote_tutor_question", {
      input: {
        eventId,
        intent,
        ...(options?.subjectId ? { subjectId: options.subjectId } : {}),
        ...(options?.learningObjectId
          ? { learningObjectId: options.learningObjectId }
          : {})
      }
    })),
  listQuestionQueue: (input?: { resolution?: string | null; limit?: number | null }) =>
    call<QuestionQueueSnapshot>("list_question_queue", { input: input ?? {} }),
  authorPracticeItem: (input: { learningObjectId: string; prompt: string; expectedAnswer: string; practiceMode?: string; hints?: string[] }) =>
    mutating([TAG.queue], call<{ practiceItemId: string }>("author_practice_item", { input })),
  // Learner-initiated re-runging: request an easier/harder sibling variant of
  // an item. Records the evidence package synchronously, authors async.
  requestRungVariant: (input: { practiceItemId: string; direction: "easier" | "harder"; sessionId?: string | null }) =>
    mutating([TAG.queue], call<RungVariantRequestResultDto>("request_rung_variant", { input })),
  getRungVariantStatus: (input: { requestId: string }) =>
    call<{ request: RungVariantRequestDto }>("get_rung_variant_status", { input }),
  // Keep an administered diagnostic probe as an ordinary practice item: a new
  // item is minted (mechanical copy, shared surface group); the probe stays
  // single-use/retired. Idempotent server-side ("already_reminted").
  remintDiagnosticProbe: (input: { attemptId: string }) =>
    mutating([TAG.queue], call<ProbeRemintResultDto>("remint_diagnostic_probe", { input })),
  editPracticeItem: (input: { practiceItemId: string; prompt?: string; expectedAnswer?: string; hints?: string[]; reason?: string }) =>
    mutating([TAG.queue], call<{ practiceItemId: string; changed: string[] }>("edit_practice_item", { input })),
  retirePracticeItem: (input: { practiceItemId: string; reason: RetirementReason; note?: string }) =>
    mutating([TAG.queue, TAG.graph, TAG.library], call<{ practiceItemId: string; status: string; queueRevision: number }>("retire_practice_item", { input })),
  splitPracticeItem: (input: { practiceItemId: string; parts: Array<{ prompt: string; expectedAnswer: string }>; reason?: string }) =>
    mutating([TAG.queue], call<{ practiceItemId: string; created: string[] }>("split_practice_item", { input })),
  resolveQuestionEvent: (eventId: string, resolution: QuestionResolution) =>
    mutating([TAG.queue], call<ResolveQuestionEventResult>("resolve_question_event", { input: { eventId, resolution } })),
  requestTeachBack: (input: { learningObjectId?: string; practiceItemId?: string }) =>
    mutating([TAG.queue], call<{ version: number; practiceItemId: string; created: boolean }>("request_teach_back", { input })),
  startTeachBack: (input: StartTeachBackInput) =>
    call<StartTeachBackResult>("start_teach_back", { input }),
  submitTeachBackTurn: (input: SubmitTeachBackTurnInput) =>
    mutating(ATTEMPT_TAGS, call<TeachBackTurnResult>("submit_teach_back_turn", { input })),
  goalsList: () => call<GoalsListSnapshot>("goals_list"),
  getGoalReport: (goalId: string) => call<GoalReportSnapshot>("get_goal_report", { goalId }),
  getGoalReportSeries: (goalId: string, opts?: { intervalDays?: number; maxPoints?: number }) =>
    call<GoalSeriesSnapshot>("get_goal_report_series", { input: { goalId, ...(opts ?? {}) } }),
  goalFeasibility: (input: GoalFeasibilityInput) =>
    call<GoalFeasibilityResult>("goal_feasibility", { input }),
  getOverconfidenceList: (goalId: string) =>
    call<OverconfidenceSnapshot>("get_overconfidence_list", { goalId }),
  startOverconfidenceProbe: (learningObjectId: string, facetId?: string | null) =>
    mutating([TAG.queue], call<StartOverconfidenceProbeResult>("start_overconfidence_probe", {
      input: { learningObjectId, facetId: facetId ?? null }
    })),
  getReentrySummary: (goalId?: string | null) =>
    call<ReentrySummarySnapshot>("get_reentry_summary", { input: { goalId: goalId ?? null } }),
  getDecayPressure: (goalId?: string | null) =>
    call<DecayPressureSnapshot>("get_decay_pressure", { input: { goalId: goalId ?? null } }),
  createGoal: (input: CreateGoalInput) => mutating([TAG.goals, TAG.queue], call<CreateGoalResult>("create_goal", { input })),
  // Authors practice for named learning objects with the completed-probe gate
  // waived — the only expansion path that works from zero items.
  generateStarterPractice: (learningObjectIds: string[], reason?: string) =>
    mutating([TAG.queue], call<GenerateStarterPracticeResult>("generate_starter_practice", {
      input: { learningObjectIds, reason: reason ?? null }
    })),
  updateGoalStatus: (goalId: string, status: GoalDto["status"]) =>
    mutating([TAG.goals, TAG.queue], call<CreateGoalResult>("update_goal_status", { input: { goalId, status } })),
  updateGoalIntent: (goalId: string, intentSentence: string | null) =>
    mutating([TAG.goals, TAG.queue], call<CreateGoalResult>("update_goal_intent", {
      input: { goalId, intentSentence }
    })),
  getExamStatus: (goalId: string) => call<ExamStatusSnapshot>("get_exam_status", { goalId }),
  startExam: (goalId: string) => mutating([TAG.goals, TAG.queue], call<ExamSessionSnapshot>("start_exam", { input: { goalId } })),
  submitExamAnswer: (sessionId: string, practiceItemId: string, answerMd: string) =>
    call<ExamAnswerResult>("submit_exam_answer", { input: { sessionId, practiceItemId, answerMd } }),
  finishExam: (sessionId: string) => mutating(ATTEMPT_TAGS, call<ExamReportSnapshot>("finish_exam", { input: { sessionId } })),
  startCalibrationSession: (input: StartCalibrationSessionInput) =>
    call<CalibrationSessionProgressDto>("start_calibration_session", { input }),
  getCalibrationSession: (calibrationSessionId: string) =>
    call<CalibrationSessionProgressDto>("get_calibration_session", { calibrationSessionId }),
  stopCalibrationSession: (calibrationSessionId: string) =>
    call<CalibrationSessionProgressDto>("stop_calibration_session", { calibrationSessionId }),
  beginProbeDialogue: (learningObjectId: string) =>
    call<BeginProbeDialogueResult>("begin_probe_dialogue", { learningObjectId }),
  nextProbeDialogueTurn: (dialogueState: string) =>
    call<NextProbeDialogueTurnResult>("next_probe_dialogue_turn", { dialogueState }),
  recordProbeDialogueTurn: (dialogueState: string, presentationId: string) =>
    call<RecordProbeDialogueTurnResult>("record_probe_dialogue_turn", { dialogueState, presentationId }),
  endProbeDialogue: (dialogueState: string) =>
    call<EndProbeDialogueResult>("end_probe_dialogue", { dialogueState }),
  presentClaims: (claims: ClaimCandidateDto[], context: { sessionId?: string | null; visitId?: string | null }) =>
    call<{ version: number; claims: PresentedClaimDto[] }>("present_claims", {
      input: { claims, sessionId: context.sessionId ?? null, visitId: context.visitId ?? null }
    }),
  respondClaim: (presentationId: string, responsePayload: Record<string, unknown>) =>
    mutating(ATTEMPT_TAGS, call<{ version: number; event: HypothesisEventDto }>("respond_claim", {
      input: { presentationId, responsePayload }
    })),
  dismissClaim: (presentationId: string) =>
    call<{ version: number; event: HypothesisEventDto }>("dismiss_claim", { presentationId }),
  exportClaims: () => call<{ version: number; events: HypothesisEventDto[] }>("export_claims"),
  purgeClaims: () => mutatingAll(call<{ version: number; purged: number }>("purge_claims")),
  getReviewLog: () => call<ReviewLogDto>("get_review_log"),
  // Returns `episode: null` + the typed §6 `repairStatus` when the causal state
  // holds the branch-specific repair — a state to render, not an error to toast.
  startRemediation: (misconceptionId: string) =>
    mutating(ATTEMPT_TAGS, call<StartRemediationDto>("start_remediation", { misconceptionId })),
  prescribeRemediation: (episodeId: string) =>
    call<RemediationDto>("prescribe_remediation", { episodeId }),
  startRemediationTreatment: (episodeId: string) =>
    mutating(ATTEMPT_TAGS, call<RemediationDto>("start_remediation_treatment", { episodeId })),
  getRemediation: (episodeId: string) => call<RemediationDto>("get_remediation", { episodeId }),
  getForecastTrackRecord: (goalId?: string | null) =>
    call<ForecastTrackRecordDto>("get_forecast_track_record", { input: { goalId: goalId ?? null } }),
  getAnswerCalibration: () =>
    call<AnswerCalibrationReportDto>("get_answer_calibration"),

  // ── P2 narrow golden path (spec_p2 §9; spec_tauri_ui §3) ───────────────────
  // Each command forwards `input` to a dotted sidecar method (see commands.rs).
  // blueprint.*
  blueprintRegister: (input: { blueprintSlug: string; spec: Record<string, unknown>; authoringVersion?: string }) =>
    call<BlueprintVersionDto>("blueprint_register", { input }),
  blueprintReview: (blueprintVersionId: string, checks?: Record<string, unknown> | null) =>
    call<BlueprintVersionDto>("blueprint_review", { input: { blueprintVersionId, checks: checks ?? null } }),
  blueprintGetVersion: (blueprintVersionId: string) =>
    call<BlueprintVersionDto>("blueprint_get_version", { input: { blueprintVersionId } }),
  blueprintDiscoverCandidates: (learningObjectId?: string | null) =>
    call<ExemplarPoolSnapshot>("blueprint_discover_candidates", { input: { learningObjectId: learningObjectId ?? null } }),
  blueprintComposeDraft: (input: { learningObjectId: string; anchorItemIds: string[]; heldOutItemId: string; title?: string }) =>
    call<ComposeDraftResult>("blueprint_compose_draft", { input }),
  // golden_path.* spine
  goldenPathConfirm: (input: {
    goalId: string;
    blueprintVersionId: string;
    contractBody: Record<string, unknown>;
    depthPreset: string;
    sourceRev: string;
    unitId: string;
    action?: string;
    assessmentSurfaceId?: string | null;
    assessmentPracticeItemId?: string | null;
  }) => call<ConfirmReceiptDto>("golden_path_confirm", { input }),
  goldenPathRunStatus: (runId: string) =>
    call<RunStateDto>("golden_path_run_status", { input: { runId } }),
  goldenPathListRuns: () => call<RunListDto>("golden_path_list_runs", { input: {} }),
  goldenPathAdvance: (input: {
    runId: string;
    toState: string;
    reason: string;
    idempotencyKey: string;
    expectedHeadEventId?: string | null;
    successorMilestone?: string | null;
  }) => call<RunAdvanceResultDto>("golden_path_advance", { input }),
  // golden_path.* assessment + restoration + milestone
  goldenPathAssessOpen: (runId: string) =>
    call<AssessOpenDto>("golden_path_assess_open", { input: { runId } }),
  goldenPathAssessSubmit: (input: {
    runId: string;
    administrationId: string;
    surfaceId: string;
    rubricScore: number;
    maxPoints: number;
    attemptId: string;
    responseText?: string | null;
    graderConfidence?: number | null;
    hasFatal?: boolean;
    revealFeedback?: boolean;
  }) => call<AssessResultDto>("golden_path_assess_submit", { input }),
  goldenPathAssessResult: (runId: string) =>
    call<AssessResultDto>("golden_path_assess_result", { input: { runId } }),
  goldenPathRestore: (runId: string) =>
    call<RestoreDto>("golden_path_restore", { input: { runId } }),
  goldenPathBoundaryDiff: (runId: string) =>
    call<BoundaryDiffDto>("golden_path_boundary_diff", { input: { runId } }),
  goldenPathDepthInvitation: (runId: string) =>
    call<DepthInvitationResultDto>("golden_path_depth_invitation", { input: { runId } }),
  goldenPathAcceptEdge: (runId: string) =>
    call<AcceptEdgeResultDto>("golden_path_accept_edge", { input: { runId } }),
  goldenPathDeclineEdge: (runId: string, reason?: string | null) =>
    call<AcceptEdgeResultDto>("golden_path_decline_edge", { input: { runId, reason: reason ?? null } }),
  // diagnostic.* (baseline + triage)
  diagnosticBaselineEnter: (input: { runId: string; learningObjectId: string; packId: string; visibleCap?: number | null }) =>
    call<Record<string, unknown>>("diagnostic_baseline_enter", { input }),
  diagnosticBoundaryView: (runId: string) =>
    call<BoundaryDiffDto>("diagnostic_boundary_view", { input: { runId } }),
  diagnosticTriage: (input: { runId: string; attempt: Record<string, unknown>; routingPrior?: Record<string, unknown> | null }) =>
    call<TriageResultDto>("diagnostic_triage", { input }),
  diagnosticTriageStatus: (runId: string) =>
    call<TriageStatusDto>("diagnostic_triage_status", { input: { runId } }),
  diagnosticTriageDecide: (input: { runId: string; triageEventId: string; chosenReason: string; actor?: string }) =>
    call<TriageResultDto>("diagnostic_triage_decide", { input }),
  diagnosticTriageOverride: (input: { runId: string; triageEventId: string; chosenReason: string; actor?: string }) =>
    call<TriageResultDto>("diagnostic_triage_override", { input }),
  diagnosticPackList: (blueprintVersionId: string) =>
    call<{ version: number; packs: unknown[] }>("diagnostic_pack_list", { input: { blueprintVersionId } }),
  // ladder.* + practice_pool.*
  ladderPolicy: (policySlug = "ladder_v1") =>
    call<LadderPolicyDto>("ladder_policy", { input: { policySlug } }),
  ladderStatus: (runId: string) => call<LadderStatusDto>("ladder_status", { input: { runId } }),
  ladderEnter: (input: { runId: string; reason?: string | null; triage?: Record<string, unknown> | null; demonstratedCapability?: boolean }) =>
    call<Record<string, unknown>>("ladder_enter", { input }),
  ladderAdvance: (input: {
    runId: string;
    fromStage: string;
    outcome: string;
    surfaceId?: string | null;
    scaffoldUse?: number | null;
    eligible?: boolean;
    idempotencyKey?: string | null;
  }) => call<LadderAdvanceResultDto>("ladder_advance", { input }),
  practicePoolStatus: (poolId: string) => call<PoolStatusDto>("practice_pool_status", { input: { poolId } }),
  practicePoolNextSurface: (poolId: string, opts?: { warmthThreshold?: number; cadence?: number }) =>
    call<PoolNextSurfaceDto>("practice_pool_next_surface", { input: { poolId, ...(opts ?? {}) } }),
  practicePoolAdmitSurface: (input: { poolId: string; surfaceSlug: string; surfaceId?: string | null; checks?: Record<string, unknown> | null }) =>
    call<PoolDto>("practice_pool_admit_surface", { input }),
  practicePoolReview: (poolId: string, checks?: Record<string, unknown> | null) =>
    call<PoolDto>("practice_pool_review", { input: { poolId, checks: checks ?? null } }),
  // practice_pool.* run composition — discovery + seeding for the run workspace
  practicePoolForRun: (runId: string) =>
    call<PoolForRunDto>("practice_pool_for_run", { input: { runId } }),
  practicePoolSeedForRun: (runId: string) =>
    call<PoolForRunDto>("practice_pool_seed_for_run", { input: { runId } }),
  practicePoolAdmitAnchor: (input: { runId: string; poolId: string; surfaceSlug: string }) =>
    call<PoolForRunDto>("practice_pool_admit_anchor", { input }),
  // reader.* (U-033)
  readerPromptContract: () => call<ReaderPromptContractDto>("reader_prompt_contract", { input: {} }),
  readerAsk: (input: ReaderAskInput) => mutatingReader(call<ReaderAnswerDto>("reader_ask", { input })),
  readerAskHistory: (extractionId: string) =>
    call<ReaderAskHistoryDto>("reader_ask_history", { input: { extractionId } }),
  readerSetAnswerMode: (input: { extractionId: string; spanId: string; answerMode: ReaderAnswerMode }) =>
    mutatingReader(call<{ eventId: string; answerMode: ReaderAnswerMode }>("reader_set_answer_mode", { input })),
  readerPresentQuestion: (input: { practiceItemId: string; readingPhase: string; goalId?: string | null; targetContractVersionId?: string | null }) =>
    call<Record<string, unknown>>("reader_present_question", { input }),
  readerSubmitQuestion: (input: { administrationId: string; response?: string | null; targetKey?: string | null; outcomeClass?: string }) =>
    mutatingReader(call<{ eventId: string }>("reader_submit_question", { input })),
  readerWatchPlan: (sourceId: string) =>
    call<ReaderWatchPlanDto>("reader_watch_plan", { input: { sourceId } }),
  readerSkipQuestion: (administrationId: string) =>
    mutatingReader(call<{ eventId: string; signal: string }>("reader_skip_question", { input: { administrationId } })),
  readerChooseDisposition: (input: {
    disposition: ReaderDisposition;
    subjectId: string;
    subjectType?: string;
    commitmentTarget?: Record<string, unknown> | null;
    goalId?: string | null;
    clientIdempotencyKey?: string | null;
  }) => mutatingReader(call<ReaderDispositionResultDto>("reader_choose_disposition", { input })),
  readerRestoreSource: (input: { extractionId: string; spanId: string; coldSurfaceId?: string | null; coldAdministrationId?: string | null }) =>
    mutatingReader(call<Record<string, unknown>>("reader_restore_source", { input })),
  readerRoutingPrior: (targetKey: string, coldObservationAt?: string | null) =>
    call<Record<string, unknown>>("reader_routing_prior", { input: { targetKey, coldObservationAt: coldObservationAt ?? null } }),
  // reader.* (P3 slice 1: render views, block health, annotations, capture/outbox)
  readerRenderView: (input: { extractionId: string; revisionId?: string | null }) =>
    call<ReaderRenderViewDto>("reader_render_view", { input }),
  readerGuidePlan: (input: { extractionId: string }) =>
    call<ReaderGuidePlanDto>("reader_guide_plan", { input }),
  readerPdfView: (input: { extractionId: string }) =>
    call<ReaderPdfViewDto>("reader_pdf_view", { input }),
  // reader quick-check producer: enqueue authoring for a section; act on the result.
  readerAuthorSectionQuestion: (input: { extractionId: string; sectionId: string }) =>
    mutatingReader(call<ReaderAuthorSectionQuestionDto>("reader_author_section_question", { input })),
  readerAuthoredQuestionAction: (input: { questionId: string; action: "answered" | "dismissed"; response?: string | null }) =>
    mutatingReader(call<{ question: ReaderAuthoredQuestionDto }>("reader_authored_question_action", { input })),
  readerEscalateAuthoredQuestion: (input: { questionId: string; learningObjectId: string }) =>
    mutatingReader(call<{ practiceItemId: string; question: ReaderAuthoredQuestionDto }>("reader_escalate_authored_question", { input }), [TAG.queue, TAG.proposals]),
  // durable reading progress (reader-first seeding): hydrate on load, write on
  // reveal/complete; completion triggers progressive practice generation.
  readerGetProgress: (input: { extractionId: string }) =>
    call<ReaderProgressListDto>("reader_get_progress", { input }),
  readerMarkSectionProgress: (input: {
    extractionId: string;
    sectionId: string;
    spansSeen?: number;
    spanCount?: number;
    revealed?: boolean;
    completed?: boolean;
  }) => mutatingReader(call<ReaderMarkProgressResultDto>("reader_mark_section_progress", { input })),
  readerBlockHealth: (input: { extractionId: string; spanId: string }) =>
    call<Record<string, unknown>>("reader_block_health", { input }),
  readerBlockOriginalRegion: (input: { extractionId: string; spanId: string }) =>
    call<ReaderBlockRegionDto>("reader_block_original_region", { input }),
  readerTranslateSelection: (input: ReaderTranslateSelectionInput) =>
    call<ReaderTranslationDto>("reader_translate_selection", { input }),
  readerCapture: (input: ReaderCaptureInput) =>
    mutatingReader(call<ReaderCaptureReceiptDto>("reader_capture", { input })),
  readerCreateAnnotation: (input: ReaderCreateAnnotationInput) =>
    mutatingReader(call<ReaderAnnotationResultDto>("reader_create_annotation", { input })),
  readerEditAnnotation: (input: { annotationId: string; learnerText?: string | null; whatIThinkIsGoingOn?: string | null; annotationType?: string | null }) =>
    mutatingReader(call<ReaderAnnotationResultDto>("reader_edit_annotation", { input })),
  readerDeleteIntentAnnotation: (input: { annotationId: string; reason?: string | null }) =>
    mutatingReader(call<{ eventId: string }>("reader_delete_intent_annotation", { input })),
  readerReanchor: (input: { annotationId: string; newExtractionId: string }) =>
    mutatingReader(call<ReaderAnnotationResultDto>("reader_reanchor", { input })),
  readerAnnotationHistory: (input: { annotationId: string }) =>
    call<Record<string, unknown>>("reader_annotation_history", { input }),
  readerSourceAnnotations: (input: { sourceId: string }) =>
    call<{ annotations: unknown[] }>("reader_source_annotations", { input }),
  readerOutboxStatus: (input: { clientIdempotencyKey: string }) =>
    call<{ outbox: Record<string, unknown> | null }>("reader_outbox_status", { input }),
  readerDrainOutbox: () =>
    mutatingReader(call<{ drained: string[]; failed: string[] }>("reader_drain_outbox", { input: {} })),
  // reader.* (P3 slice 2: palette, demand-paged synthesis, source objects)
  readerInvokePreset: (input: ReaderInvokePresetInput) =>
    mutatingReader(call<ReaderPresetReceiptDto>("reader_invoke_preset", { input })),
  readerSetMode: (input: { mode: string; extractionId?: string | null; sessionId?: string | null }) =>
    mutatingReader(call<ReaderSetModeResultDto>("reader_set_mode", { input })),
  readerQuestionControl: (input: { control: string; administrationId?: string | null; subjectId?: string | null; subjectType?: string }) =>
    mutatingReader(call<ReaderQuestionControlResultDto>("reader_question_control", { input })),
  readerEnqueueRequest: (input: ReaderEnqueueRequestInput) =>
    mutatingReader(call<ReaderEnqueueRequestDto>("reader_enqueue_request", { input })),
  readerRequestStatus: (requestId: string) =>
    call<{ request: ReaderRequestRow | null }>("reader_request_status", { input: { requestId } }),
  readerCancelRequest: (requestId: string) =>
    mutatingReader(call<{ request: ReaderRequestRow | null }>("reader_cancel_request", { input: { requestId } })),
  readerRetryRequest: (requestId: string) =>
    mutatingReader(call<{ request: ReaderRequestRow | null }>("reader_retry_request", { input: { requestId } })),
  readerSourceRequests: (sourceId: string) =>
    call<{ requests: ReaderRequestRow[] }>("reader_source_requests", { input: { sourceId } }),
  readerDrainRequests: () =>
    mutatingReader(call<{ completed: string[]; failed: string[]; partial: string[] }>("reader_drain_requests", { input: {} })),
  readerSourceObjects: (sourceId: string) =>
    call<{ sourceObjects: unknown[] }>("reader_source_objects", { input: { sourceId } }),
  readerReviewSourceObject: (input: { sourceObjectId: string; status: string }) =>
    mutatingReader(call<Record<string, unknown>>("reader_review_source_object", { input })),
  readerLinkRelation: (input: { sourceObjectId: string; relatedObjectId?: string | null; relationType?: string; learnerText?: string | null }) =>
    mutatingReader(call<Record<string, unknown>>("reader_link_relation", { input })),
  readerProposalInbox: (input?: { status?: string; sourceObjectId?: string | null }) =>
    call<{ proposals: unknown[] }>("reader_proposal_inbox", { input: input ?? {} }),
  readerSearchSources: (input: { query: string; limit?: number }) =>
    call<ReaderSourceSearchDto>("reader_search_sources", { input }),
  readerManualAnchor: (input: { annotationId: string; extractionId: string; rawSelection: Record<string, unknown>; renderViewId?: string | null }) =>
    mutatingReader(call<{ annotationId: string; status: string }>("reader_manual_anchor", { input })),
  readerAcceptProposal: (proposalId: string) =>
    mutatingReader(call<{ proposal: Record<string, unknown> }>("reader_accept_proposal", { input: { proposalId } }), [TAG.proposals, TAG.graph, TAG.library]),
  readerRejectProposal: (proposalId: string) =>
    mutatingReader(call<{ proposal: Record<string, unknown> }>("reader_reject_proposal", { input: { proposalId } }), [TAG.proposals, TAG.graph, TAG.library]),
  // reader.* (P3 slice 3: authoring + coach + maintenance, arcs + depth + primes, restoration)
  readerAuthorQA: (input: ReaderAuthorQAInput) =>
    mutatingReader(call<ReaderAuthoredCardDto>("reader_author_qa", { input }), [TAG.queue, TAG.proposals]),
  readerImportExercise: (input: ReaderImportExerciseInput) =>
    mutatingReader(call<ReaderExerciseImportReceiptDto>("reader_import_exercise", { input }), [TAG.queue, TAG.proposals]),
  readerExerciseImportStatus: (input: { batchId: string }) =>
    call<ReaderExerciseImportStatusDto>("reader_exercise_import_status", { input }),
  readerCoachLint: (input: { question: string; answer: string; level?: string }) =>
    call<ReaderCoachLintDto>("reader_coach_lint", { input }),
  readerMaintain: (input: ReaderMaintainInput) =>
    mutatingReader(call<Record<string, unknown>>("reader_maintain", { input })),
  readerArc: (input: { arcId?: string | null; commitmentId?: string | null; sourceId?: string | null }) =>
    call<ReaderArcDto>("reader_arc", { input }),
  readerSetDepthPolicy: (input: { arcId: string; policy: string }) =>
    mutatingReader(call<{ arcId: string; policy: string }>("reader_set_depth_policy", { input })),
  readerPauseArc: (input: { arcId: string; reason?: string | null }) =>
    mutatingReader(call<{ arcId: string; paused: boolean }>("reader_pause_arc", { input })),
  readerShrinkEnvelope: (input: { arcId: string; bounds: Record<string, unknown>; reviewedEdges?: unknown[] }) =>
    mutatingReader(call<{ arcId: string; shrunk: boolean }>("reader_shrink_envelope", { input })),
  readerPrime: (input: { arcId: string; questionRef: string; section?: string | null; answer?: boolean; gaveUp?: boolean }) =>
    mutatingReader(call<Record<string, unknown>>("reader_prime", { input })),
  readerRestore: (input: { sourceId: string; extractionId?: string | null; runId?: string | null; idempotencyKey?: string | null }) =>
    mutatingReader(call<ReaderRestorationDto>("reader_restore", { input })),
  // adjudication.* (diagnosis adjudication store, §2 A4). `record` returns the
  // belief effect arm (d) actually applied; the overlay reports that, not the
  // effect the verdict implies.
  adjudicationQueue: (input?: { learningObjectId?: string | null; reasons?: string[] | null; limit?: number }) =>
    call<AdjudicationQueueDto>("adjudication_queue", { input: input ?? {} }),
  adjudicationRecord: (input: AdjudicationRecordInput) =>
    mutating(ATTEMPT_TAGS, call<AdjudicationRecordResultDto>("adjudication_record", { input })),
  adjudicationScoreboard: (groupBy: "version" | "queue_reason" | "none" = "version") =>
    call<AdjudicationScoreboardDto>("adjudication_scoreboard", { input: { groupBy } })
};
