import { invoke } from "@tauri-apps/api/core";
import type {
  AppSnapshot,
  AnswerCalibrationReportDto,
  CreateVaultInput,
  CreateVaultResult,
  LearnerProfileDto,
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
  PrimedRetryResultDto,
  GradingProviderResult,
  OpenrouterKeyResult,
  SettingsDto,
  UpdateAiSettingsInput,
  InspectorEntity,
  KnowledgeMapHistory,
  KnowledgeMapSnapshot,
  PracticeItemDetail,
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
  SourceLibrarySnapshot,
  SourceOutline,
  SelectionPreviewDto,
  EffectiveOutlineDto,
  SaveUnitSelectionInput,
  UnitSelectionState,
  AcquisitionPreview,
  BuildPlan,
  BuildPlanSelectionInput,
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
  ReaderCoachLintDto,
  ReaderMaintainInput,
  ReaderArcDto,
  ReaderRestorationDto,
} from "./dto";

async function call<T>(command: string, args: Record<string, unknown> = {}): Promise<T> {
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

export const api = {
  selectVault: (path?: string | null) => call<VaultSummary | null>("select_vault", { path }),
  loadVault: () => call<AppSnapshot>("load_vault"),
  createVault: (input: CreateVaultInput) => call<CreateVaultResult>("create_vault", { input }),
  getLearnerProfile: () => call<LearnerProfileDto>("get_learner_profile"),
  setLearnerProfile: (input: { startingLevel: StartingLevel; levelNote?: string | null }) =>
    call<LearnerProfileDto>("set_learner_profile", { input }),
  reloadVault: () => call<AppSnapshot>("reload_vault"),
  getRuntimeHealth: () => call<RuntimeHealth>("get_runtime_health"),
  startSession: (input: SessionStartInput) => call<SessionSnapshot>("start_session", { input }),
  getSession: (sessionId: string) => call<SessionSnapshot>("get_session", { sessionId }),
  clearSessionCheckpoint: (sessionId: string) => call<{ cleared: boolean }>("clear_session_checkpoint", { sessionId }),
  endSession: (sessionId: string) => call<SessionEndSummary>("end_session", { sessionId }),
  getTodayQueue: (input: QueueInput) => call<QueueSnapshot>("get_today_queue", { input }),
  explainPracticeItem: (practiceItemId: string) =>
    call<SchedulerExplanationDto>("explain_practice_item", { practiceItemId }),
  openQueueItem: (practiceItemId: string) => call<PracticeItemDetail>("open_queue_item", { practiceItemId }),
  getPracticeItem: (practiceItemId: string) => call<PracticeItemDetail>("get_practice_item", { practiceItemId }),
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
  }) => call<{ ok: boolean }>("save_practice_draft", { input }),
  submitAttempt: (input: SubmitAttemptInput) => call<AttemptResultDto>("submit_attempt", { input }),
  submitDontKnow: (input: {
    sessionId: string;
    practiceItemId: string;
    hintsUsed: number;
    latencySeconds?: number | null;
    probePresentationId?: string | null;
    answerConfidence?: number | null;
    assessmentContractVersionId?: string | null;
    submissionId?: string | null;
  }) => call<AttemptResultDto>("submit_dont_know", { input }),
  skipPracticeItem: (input: { sessionId: string; practiceItemId: string }) =>
    call<QueueSnapshot>("skip_practice_item", { input }),
  getFeedback: (attemptId: string) => call<FeedbackBundle>("get_feedback", { attemptId }),
  getAttempt: (attemptId: string) => call<unknown>("get_attempt", { attemptId }),
  triggerRegrade: (attemptId: string) => call<FeedbackBundle>("trigger_regrade", { input: { attemptId } }),
  addErrorEvent: (attemptId: string, errorType: string, severity = 0.5) =>
    call<FeedbackBundle>("add_error_event", { input: { attemptId, errorType, severity } }),
  triggerFollowup: (attemptId: string) =>
    call<FeedbackBundle>("trigger_followup", { input: { attemptId } }),
  rateFollowup: (attemptId: string, useful: boolean) =>
    call<FeedbackBundle>("rate_followup", { input: { attemptId, useful } }),
  startPrimedRetry: (attemptId: string) =>
    call<PrimedRetryResultDto>("start_primed_retry", { input: { attemptId } }),
  inspectEntity: (id: string) => call<InspectorEntity>("inspect_entity", { id }),
  getConceptGraph: () => call<ConceptGraphSnapshot>("get_concept_graph"),
  getVaultTree: () => call<VaultTreeSnapshot>("get_vault_tree"),
  getRecentIngests: () => call<RecentIngestsSnapshot>("get_recent_ingests"),
  classifyIngestSource: (source: string) =>
    call<IngestSourceClassification>("classify_ingest_source", { input: { source } }),
  startIngest: (input: StartIngestInput) => call<IngestJobDto>("start_ingest", { input }),
  getIngestJob: (jobId: string) => call<IngestJobDto>("get_ingest_job", { jobId }),
  getIngestJobs: () => call<IngestJobsSnapshot>("get_ingest_jobs"),
  cancelIngest: (jobId: string) => call<IngestJobDto>("cancel_ingest", { jobId }),
  startImportBatch: (input: StartImportBatchInput) => call<IngestBatchDto>("start_import_batch", { input }),
  getIngestBatch: (batchId: string) => call<IngestBatchDto>("get_ingest_batch", { batchId }),
  listIngestBatches: (limit = 30) => call<IngestBatchesSnapshot>("list_ingest_batches", { input: { limit } }),
  cancelIngestBatch: (batchId: string) => call<IngestBatchDto>("cancel_ingest_batch", { batchId }),
  resumeIngestBatch: (batchId: string) => call<IngestBatchDto>("resume_ingest_batch", { batchId }),
  retrySynthesis: (input: RetrySynthesisInput) =>
    call<IngestBatchDto>("retry_synthesis", { input }),
  getSynthesisCandidate: (batchId: string) =>
    call<SynthesisCandidateSummary>("get_synthesis_candidate", { batchId }),
  getSourceLibrary: () => call<SourceLibrarySnapshot>("get_source_library"),
  getSourceOutline: (extractionRef: string) =>
    call<SourceOutline>("get_source_outline", { extractionRef }),
  getSelectionPreview: (extractionRef: string, selectedUnitIds?: string[] | null) =>
    call<SelectionPreviewDto>("get_selection_preview", {
      input: { extractionRef, selectedUnitIds: selectedUnitIds ?? null }
    }),
  getEffectiveOutline: (extractionRef: string, boundaryOverrides: Record<string, unknown>[]) =>
    call<EffectiveOutlineDto>("get_effective_outline", { input: { extractionRef, boundaryOverrides } }),
  saveUnitSelection: (input: SaveUnitSelectionInput) =>
    call<{ version: number } & UnitSelectionState & { extractionId: string }>("save_unit_selection", { input }),
  getAcquisitionPreview: (inputs: string[]) =>
    call<AcquisitionPreview>("get_acquisition_preview", { input: { inputs } }),
  getBuildPlan: (selections: BuildPlanSelectionInput[], subjectId?: string | null) =>
    call<BuildPlan>("get_build_plan", { input: { selections, subjectId: subjectId ?? null } }),
  startExtractionRepair: (input: StartExtractionRepairInput) =>
    call<IngestBatchDto>("start_extraction_repair", { input }),
  listSourceSets: () => call<SourceSetsSnapshot>("list_source_sets"),
  getSourceSet: (sourceSetId: string) =>
    call<{ version: number; sourceSet: SourceSetDto }>("get_source_set", { sourceSetId }),
  upsertSourceSet: (input: SourceSetDto) =>
    call<{ version: number; sourceSet: SourceSetDto }>("upsert_source_set", { input }),
  getSourceCoverage: (sourceSetId: string) =>
    call<{ version: number; coverage: SourceCoverageDto }>("get_source_coverage", { sourceSetId }),
  startInventory: (input: StartInventoryInput) =>
    call<IngestBatchDto>("start_inventory", { input }),
  createStudyMap: (input: CreateStudyMapInput) =>
    call<{ version: number; studyMap: StudyMapDto }>("create_study_map", { input }),
  // Enqueue a collection's study-map build as a durable Activity batch (inventory
  // members → bootstrap_synthesis). The multi-member, in-app counterpart to Quick
  // add's confirm step; returns the batch view (IngestBatchDto).
  buildStudyMap: (input: BuildStudyMapInput) => call<IngestBatchDto>("build_study_map", { input }),
  // ING M7 — Update study map (§10), maintenance feed (§11), exam readiness (§15).
  appendSource: (input: AppendSourceInput) =>
    call<{ version: number; append: AppendResultDto }>("append_source", { input }),
  refreshRevision: (input: RefreshRevisionInput) =>
    call<{ version: number; refresh: RefreshResultDto }>("refresh_revision", { input }),
  getMaintenanceFeed: (subjectId?: string | null) =>
    call<MaintenanceFeedSnapshot>("maintenance_feed", { input: { subjectId: subjectId ?? null } }),
  maintenanceNoticeAction: (noticeId: string, action: "dismiss" | "snooze", snoozedUntil?: string | null) =>
    call<{ version: number; notice: MaintenanceNoticeDto | null }>("maintenance_notice_action", {
      input: { noticeId, action, snoozedUntil: snoozedUntil ?? null }
    }),
  listSourceConflicts: (status = "open") =>
    call<{ version: number; conflicts: SourceConflictDto[] }>("list_source_conflicts", { input: { status } }),
  resolveSourceConflict: (input: ResolveConflictInput) =>
    call<{ version: number; conflict: SourceConflictDto }>("resolve_source_conflict", { input }),
  getExamReadiness: (subjectId?: string | null) =>
    call<{ version: number; report: ExamReadinessReportDto }>("exam_readiness", {
      input: { subjectId: subjectId ?? null }
    }),
  planQuickAdd: (input: PlanQuickAddInput) =>
    call<{ version: number; plan: QuickAddPlanDto }>("plan_quick_add", { input }),
  confirmQuickAdd: (input: ConfirmQuickAddInput) =>
    call<{ version: number; quickAdd: QuickAddResultDto; batch: IngestBatchDto; confirmation: QuickAddConfirmationDto }>(
      "confirm_quick_add",
      { input },
    ),
  getSpanView: (input: SpanViewInput) =>
    call<{ version: number; spanView: SpanViewDto }>("get_span_view", { input }),
  getSubjectRegistry: (subjectId: string) =>
    call<SubjectRegistryDto>("get_subject_registry", { input: { subjectId } }),
  proposeFacetMerge: (input: ProposeFacetMergeInput) =>
    call<{ version: number } & FacetMergeResultDto>("propose_facet_merge", { input }),
  readVaultFile: (path: string) => call<VaultFileContent>("read_vault_file", { path }),
  writeVaultFile: (path: string, body: string) => call<VaultFileContent>("write_vault_file", { path, body }),
  createVaultFile: (path: string, body = "") =>
    call<VaultFileContent>("create_vault_file", { input: { path, body } }),
  sqliteTables: (path: string) => call<SqliteTablesSnapshot>("sqlite_tables", { input: { path } }),
  sqliteTable: (path: string, table: string, limit = 200, offset = 0) =>
    call<SqliteTableSnapshot>("sqlite_table", { input: { path, table, limit, offset } }),
  sqliteExec: (path: string, sql: string) => call<SqliteExecResult>("sqlite_exec", { input: { path, sql } }),
  sqliteUpdateCell: (path: string, table: string, rowid: number, column: string, value: string | null) =>
    call<{ version: number; ok: boolean }>("sqlite_update_cell", { input: { path, table, rowid, column, value } }),
  sqliteInsertRow: (path: string, table: string) =>
    call<{ version: number; rowid: number | null }>("sqlite_insert_row", { input: { path, table } }),
  sqliteDeleteRow: (path: string, table: string, rowid: number) =>
    call<{ version: number; ok: boolean }>("sqlite_delete_row", { input: { path, table, rowid } }),
  getProposals: () => call<ProposalsSnapshot>("get_proposals"),
  getEntityProvenance: (entityType: string, entityId: string) =>
    call<EntityProvenance>("get_entity_provenance", { entityType, entityId }),
  acceptProposalItems: (patchId: string, itemIds?: string[] | null) =>
    call<ProposalsSnapshot>("accept_proposal_items", { input: { patchId, itemIds: itemIds ?? null } }),
  rejectProposalItems: (patchId: string, itemIds?: string[] | null) =>
    call<ProposalsSnapshot>("reject_proposal_items", { input: { patchId, itemIds: itemIds ?? null } }),
  resetProposalItems: (patchId: string, itemIds?: string[] | null) =>
    call<ProposalsSnapshot>("reset_proposal_items", { input: { patchId, itemIds: itemIds ?? null } }),
  editProposalItem: (patchId: string, itemId: string, payloadJson: string) =>
    call<ProposalsSnapshot>("edit_proposal_item", { input: { patchId, itemId, payloadJson } }),
  refreshProposalItemValidation: (patchId: string, itemId: string) =>
    call<ProposalsSnapshot>("refresh_proposal_item_validation", { input: { patchId, itemId } }),
  deleteProposalItem: (patchId: string, itemId: string) =>
    call<ProposalsSnapshot>("delete_proposal_item", { input: { patchId, itemId } }),
  runCliCommand: (argv: string[]) => call<CliCommandResult>("run_cli_command", { input: { argv } }),
  addNote: (input: {
    subjectId: string;
    noteId: string;
    title: string;
    body: string;
    relatedLos?: string[];
  }) =>
    call<CliCommandResult>("run_cli_command", {
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
    }),
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
    call<ProposeGraphEditsResult>("propose_graph_edits", { input }),
  queueRestructureRequest: (input: QueueRestructureRequestInput) =>
    call<QueueRestructureRequestResult>("queue_restructure_request", { input }),
  resolveEdgeDirection: (input: ResolveEdgeDirectionInput) =>
    call<ResolveEdgeDirectionResult>("resolve_edge_direction", { input }),
  getFacetDetail: (facetId: string) => call<FacetDetailDto>("get_facet_detail", { facetId }),
  listFacets: () => call<FacetListDto>("list_facets"),
  previewKnowledgeMap: (input: PreviewKnowledgeMapInput) =>
    call<KnowledgeMapPreviewDto>("preview_knowledge_map", { input }),
  previewBlueprintReadiness: (input: PreviewBlueprintReadinessInput) =>
    call<BlueprintReadinessPreviewDto>("preview_blueprint_readiness", { input }),
  getKnowledgeMapHistory: () => call<KnowledgeMapHistory>("get_knowledge_map_history"),
  setGradingProvider: (provider: string) =>
    call<GradingProviderResult>("set_grading_provider", { provider }),
  getSettings: () => call<SettingsDto>("get_settings"),
  updateAiSettings: (input: UpdateAiSettingsInput) =>
    call<SettingsDto>("update_ai_settings", { input }),
  setOpenrouterApiKey: (apiKey: string) =>
    call<OpenrouterKeyResult>("set_openrouter_api_key", { apiKey }),
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
  promoteTutorQuestion: (eventId: string, intent: PromotionIntent) =>
    call<PromoteTutorQuestionResult>("promote_tutor_question", { input: { eventId, intent } }),
  listQuestionQueue: (input?: { resolution?: string | null; limit?: number | null }) =>
    call<QuestionQueueSnapshot>("list_question_queue", { input: input ?? {} }),
  authorPracticeItem: (input: { learningObjectId: string; prompt: string; expectedAnswer: string; practiceMode?: string; hints?: string[] }) =>
    call<{ practiceItemId: string }>("author_practice_item", { input }),
  // Learner-initiated re-runging: request an easier/harder sibling variant of
  // an item. Records the evidence package synchronously, authors async.
  requestRungVariant: (input: { practiceItemId: string; direction: "easier" | "harder"; sessionId?: string | null }) =>
    call<RungVariantRequestResultDto>("request_rung_variant", { input }),
  getRungVariantStatus: (input: { requestId: string }) =>
    call<{ request: RungVariantRequestDto }>("get_rung_variant_status", { input }),
  editPracticeItem: (input: { practiceItemId: string; prompt?: string; expectedAnswer?: string; hints?: string[]; reason?: string }) =>
    call<{ practiceItemId: string; changed: string[] }>("edit_practice_item", { input }),
  retirePracticeItem: (input: { practiceItemId: string; reason: RetirementReason; note?: string }) =>
    call<{ practiceItemId: string; status: string }>("retire_practice_item", { input }),
  splitPracticeItem: (input: { practiceItemId: string; parts: Array<{ prompt: string; expectedAnswer: string }>; reason?: string }) =>
    call<{ practiceItemId: string; created: string[] }>("split_practice_item", { input }),
  resolveQuestionEvent: (eventId: string, resolution: QuestionResolution) =>
    call<ResolveQuestionEventResult>("resolve_question_event", { input: { eventId, resolution } }),
  startTeachBack: (input: StartTeachBackInput) =>
    call<StartTeachBackResult>("start_teach_back", { input }),
  submitTeachBackTurn: (input: SubmitTeachBackTurnInput) =>
    call<TeachBackTurnResult>("submit_teach_back_turn", { input }),
  goalsList: () => call<GoalsListSnapshot>("goals_list"),
  getGoalReport: (goalId: string) => call<GoalReportSnapshot>("get_goal_report", { goalId }),
  getGoalReportSeries: (goalId: string, opts?: { intervalDays?: number; maxPoints?: number }) =>
    call<GoalSeriesSnapshot>("get_goal_report_series", { input: { goalId, ...(opts ?? {}) } }),
  goalFeasibility: (input: GoalFeasibilityInput) =>
    call<GoalFeasibilityResult>("goal_feasibility", { input }),
  getOverconfidenceList: (goalId: string) =>
    call<OverconfidenceSnapshot>("get_overconfidence_list", { goalId }),
  startOverconfidenceProbe: (learningObjectId: string, facetId?: string | null) =>
    call<StartOverconfidenceProbeResult>("start_overconfidence_probe", {
      input: { learningObjectId, facetId: facetId ?? null }
    }),
  getReentrySummary: (goalId?: string | null) =>
    call<ReentrySummarySnapshot>("get_reentry_summary", { input: { goalId: goalId ?? null } }),
  getDecayPressure: (goalId?: string | null) =>
    call<DecayPressureSnapshot>("get_decay_pressure", { input: { goalId: goalId ?? null } }),
  createGoal: (input: CreateGoalInput) => call<CreateGoalResult>("create_goal", { input }),
  updateGoalStatus: (goalId: string, status: GoalDto["status"]) =>
    call<CreateGoalResult>("update_goal_status", { input: { goalId, status } }),
  getExamStatus: (goalId: string) => call<ExamStatusSnapshot>("get_exam_status", { goalId }),
  startExam: (goalId: string) => call<ExamSessionSnapshot>("start_exam", { input: { goalId } }),
  submitExamAnswer: (sessionId: string, practiceItemId: string, answerMd: string) =>
    call<ExamAnswerResult>("submit_exam_answer", { input: { sessionId, practiceItemId, answerMd } }),
  finishExam: (sessionId: string) => call<ExamReportSnapshot>("finish_exam", { input: { sessionId } }),
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
    call<{ version: number; event: HypothesisEventDto }>("respond_claim", {
      input: { presentationId, responsePayload }
    }),
  dismissClaim: (presentationId: string) =>
    call<{ version: number; event: HypothesisEventDto }>("dismiss_claim", { presentationId }),
  exportClaims: () => call<{ version: number; events: HypothesisEventDto[] }>("export_claims"),
  purgeClaims: () => call<{ version: number; purged: number }>("purge_claims"),
  getReviewLog: () => call<ReviewLogDto>("get_review_log"),
  startRemediation: (misconceptionId: string) =>
    call<RemediationDto>("start_remediation", { misconceptionId }),
  prescribeRemediation: (episodeId: string) =>
    call<RemediationDto>("prescribe_remediation", { episodeId }),
  startRemediationTreatment: (episodeId: string) =>
    call<RemediationDto>("start_remediation_treatment", { episodeId }),
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
  readerAsk: (input: ReaderAskInput) => call<ReaderAnswerDto>("reader_ask", { input }),
  readerSetAnswerMode: (input: { extractionId: string; spanId: string; answerMode: ReaderAnswerMode }) =>
    call<{ eventId: string; answerMode: ReaderAnswerMode }>("reader_set_answer_mode", { input }),
  readerPresentQuestion: (input: { practiceItemId: string; readingPhase: string; goalId?: string | null; targetContractVersionId?: string | null }) =>
    call<Record<string, unknown>>("reader_present_question", { input }),
  readerSubmitQuestion: (input: { administrationId: string; response?: string | null; targetKey?: string | null; outcomeClass?: string }) =>
    call<{ eventId: string }>("reader_submit_question", { input }),
  readerWatchPlan: (sourceId: string) =>
    call<ReaderWatchPlanDto>("reader_watch_plan", { input: { sourceId } }),
  readerSkipQuestion: (administrationId: string) =>
    call<{ eventId: string; signal: string }>("reader_skip_question", { input: { administrationId } }),
  readerChooseDisposition: (input: {
    disposition: ReaderDisposition;
    subjectId: string;
    subjectType?: string;
    commitmentTarget?: Record<string, unknown> | null;
    goalId?: string | null;
    clientIdempotencyKey?: string | null;
  }) => call<ReaderDispositionResultDto>("reader_choose_disposition", { input }),
  readerRestoreSource: (input: { extractionId: string; spanId: string; coldSurfaceId?: string | null; coldAdministrationId?: string | null }) =>
    call<Record<string, unknown>>("reader_restore_source", { input }),
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
    call<ReaderAuthorSectionQuestionDto>("reader_author_section_question", { input }),
  readerAuthoredQuestionAction: (input: { questionId: string; action: "answered" | "dismissed"; response?: string | null }) =>
    call<{ question: ReaderAuthoredQuestionDto }>("reader_authored_question_action", { input }),
  readerEscalateAuthoredQuestion: (input: { questionId: string; learningObjectId: string }) =>
    call<{ practiceItemId: string; question: ReaderAuthoredQuestionDto }>("reader_escalate_authored_question", { input }),
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
  }) => call<ReaderMarkProgressResultDto>("reader_mark_section_progress", { input }),
  readerBlockHealth: (input: { extractionId: string; spanId: string }) =>
    call<Record<string, unknown>>("reader_block_health", { input }),
  readerBlockOriginalRegion: (input: { extractionId: string; spanId: string }) =>
    call<ReaderBlockRegionDto>("reader_block_original_region", { input }),
  readerTranslateSelection: (input: ReaderTranslateSelectionInput) =>
    call<ReaderTranslationDto>("reader_translate_selection", { input }),
  readerCapture: (input: ReaderCaptureInput) =>
    call<ReaderCaptureReceiptDto>("reader_capture", { input }),
  readerCreateAnnotation: (input: ReaderCreateAnnotationInput) =>
    call<ReaderAnnotationResultDto>("reader_create_annotation", { input }),
  readerEditAnnotation: (input: { annotationId: string; learnerText?: string | null; whatIThinkIsGoingOn?: string | null; annotationType?: string | null }) =>
    call<ReaderAnnotationResultDto>("reader_edit_annotation", { input }),
  readerDeleteIntentAnnotation: (input: { annotationId: string; reason?: string | null }) =>
    call<{ eventId: string }>("reader_delete_intent_annotation", { input }),
  readerReanchor: (input: { annotationId: string; newExtractionId: string }) =>
    call<ReaderAnnotationResultDto>("reader_reanchor", { input }),
  readerAnnotationHistory: (input: { annotationId: string }) =>
    call<Record<string, unknown>>("reader_annotation_history", { input }),
  readerSourceAnnotations: (input: { sourceId: string }) =>
    call<{ annotations: unknown[] }>("reader_source_annotations", { input }),
  readerOutboxStatus: (input: { clientIdempotencyKey: string }) =>
    call<{ outbox: Record<string, unknown> | null }>("reader_outbox_status", { input }),
  readerDrainOutbox: () =>
    call<{ drained: string[]; failed: string[] }>("reader_drain_outbox", { input: {} }),
  // reader.* (P3 slice 2: palette, demand-paged synthesis, source objects)
  readerInvokePreset: (input: ReaderInvokePresetInput) =>
    call<ReaderPresetReceiptDto>("reader_invoke_preset", { input }),
  readerSetMode: (input: { mode: string; extractionId?: string | null; sessionId?: string | null }) =>
    call<ReaderSetModeResultDto>("reader_set_mode", { input }),
  readerQuestionControl: (input: { control: string; administrationId?: string | null; subjectId?: string | null; subjectType?: string }) =>
    call<ReaderQuestionControlResultDto>("reader_question_control", { input }),
  readerEnqueueRequest: (input: ReaderEnqueueRequestInput) =>
    call<ReaderEnqueueRequestDto>("reader_enqueue_request", { input }),
  readerRequestStatus: (requestId: string) =>
    call<{ request: ReaderRequestRow | null }>("reader_request_status", { input: { requestId } }),
  readerCancelRequest: (requestId: string) =>
    call<{ request: ReaderRequestRow | null }>("reader_cancel_request", { input: { requestId } }),
  readerRetryRequest: (requestId: string) =>
    call<{ request: ReaderRequestRow | null }>("reader_retry_request", { input: { requestId } }),
  readerSourceRequests: (sourceId: string) =>
    call<{ requests: ReaderRequestRow[] }>("reader_source_requests", { input: { sourceId } }),
  readerDrainRequests: () =>
    call<{ completed: string[]; failed: string[]; partial: string[] }>("reader_drain_requests", { input: {} }),
  readerSourceObjects: (sourceId: string) =>
    call<{ sourceObjects: unknown[] }>("reader_source_objects", { input: { sourceId } }),
  readerReviewSourceObject: (input: { sourceObjectId: string; status: string }) =>
    call<Record<string, unknown>>("reader_review_source_object", { input }),
  readerLinkRelation: (input: { sourceObjectId: string; relatedObjectId?: string | null; relationType?: string; learnerText?: string | null }) =>
    call<Record<string, unknown>>("reader_link_relation", { input }),
  readerProposalInbox: (input?: { status?: string; sourceObjectId?: string | null }) =>
    call<{ proposals: unknown[] }>("reader_proposal_inbox", { input: input ?? {} }),
  readerSearchSources: (input: { query: string; limit?: number }) =>
    call<ReaderSourceSearchDto>("reader_search_sources", { input }),
  readerManualAnchor: (input: { annotationId: string; extractionId: string; rawSelection: Record<string, unknown>; renderViewId?: string | null }) =>
    call<{ annotationId: string; status: string }>("reader_manual_anchor", { input }),
  readerAcceptProposal: (proposalId: string) =>
    call<{ proposal: Record<string, unknown> }>("reader_accept_proposal", { input: { proposalId } }),
  readerRejectProposal: (proposalId: string) =>
    call<{ proposal: Record<string, unknown> }>("reader_reject_proposal", { input: { proposalId } }),
  // reader.* (P3 slice 3: authoring + coach + maintenance, arcs + depth + primes, restoration)
  readerAuthorQA: (input: ReaderAuthorQAInput) =>
    call<ReaderAuthoredCardDto>("reader_author_qa", { input }),
  readerCoachLint: (input: { question: string; answer: string; level?: string }) =>
    call<ReaderCoachLintDto>("reader_coach_lint", { input }),
  readerMaintain: (input: ReaderMaintainInput) =>
    call<Record<string, unknown>>("reader_maintain", { input }),
  readerArc: (input: { arcId?: string | null; commitmentId?: string | null; sourceId?: string | null }) =>
    call<ReaderArcDto>("reader_arc", { input }),
  readerSetDepthPolicy: (input: { arcId: string; policy: string }) =>
    call<{ arcId: string; policy: string }>("reader_set_depth_policy", { input }),
  readerPauseArc: (input: { arcId: string; reason?: string | null }) =>
    call<{ arcId: string; paused: boolean }>("reader_pause_arc", { input }),
  readerShrinkEnvelope: (input: { arcId: string; bounds: Record<string, unknown>; reviewedEdges?: unknown[] }) =>
    call<{ arcId: string; shrunk: boolean }>("reader_shrink_envelope", { input }),
  readerPrime: (input: { arcId: string; questionRef: string; section?: string | null; answer?: boolean; gaveUp?: boolean }) =>
    call<Record<string, unknown>>("reader_prime", { input }),
  readerRestore: (input: { sourceId: string; extractionId?: string | null; runId?: string | null; idempotencyKey?: string | null }) =>
    call<ReaderRestorationDto>("reader_restore", { input })
};
