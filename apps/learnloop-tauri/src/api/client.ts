import { invoke } from "@tauri-apps/api/core";
import type {
  AppSnapshot,
  AttemptResultDto,
  CliCommandResult,
  CommandError,
  ConceptGraphSnapshot,
  FeedbackBundle,
  InspectorEntity,
  PracticeItemDetail,
  ProposalsSnapshot,
  QueueInput,
  QueueSnapshot,
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
  SubmitAttemptInput
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
  inspectEntity: (id: string) => call<InspectorEntity>("inspect_entity", { id }),
  getConceptGraph: () => call<ConceptGraphSnapshot>("get_concept_graph"),
  getVaultTree: () => call<VaultTreeSnapshot>("get_vault_tree"),
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
    })
};
