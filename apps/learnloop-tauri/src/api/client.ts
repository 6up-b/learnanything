import { invoke } from "@tauri-apps/api/core";
import type {
  AppSnapshot,
  AttemptResultDto,
  CliCommandResult,
  CommandError,
  ConceptGraphSnapshot,
  FacetMasterySnapshot,
  FeedbackBundle,
  PrimedRetryResultDto,
  GradingProviderResult,
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
  StartImportBatchInput,
  SourceLibrarySnapshot,
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
    return error as CommandError;
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
  getSourceLibrary: () => call<SourceLibrarySnapshot>("get_source_library"),
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
  getKnowledgeMap: () => call<KnowledgeMapSnapshot>("get_knowledge_map"),
  getKnowledgeMapHistory: () => call<KnowledgeMapHistory>("get_knowledge_map_history"),
  setGradingProvider: (provider: string) =>
    call<GradingProviderResult>("set_grading_provider", { provider }),
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
    call<EndProbeDialogueResult>("end_probe_dialogue", { dialogueState })
};
