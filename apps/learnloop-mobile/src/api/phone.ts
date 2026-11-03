// The allowlisted methods the phone's screens use (§4.5), with the desktop's DTOs.
import type {
  AnswerGradingClarificationResultDto,
  AttemptResultDto,
  AttemptType,
  DiagnosisStatusValue,
  FeedbackBundle,
  GradingClarificationResultDto,
  PracticeItemDetail,
  ProbeContractDto,
  QueueSnapshot,
  SessionEndSummary,
  SessionSnapshot
} from "@desktop/api/dto";
import { call, getJson, runLong, type AcceptedJob, type JobState } from "./http";

export interface OwnerSnapshot {
  readonly session_id: string;
  readonly owner_label?: string | null;
  readonly owner_generation?: number | null;
  readonly has_draft?: boolean;
  readonly draft_first_line?: string | null;
}

export interface SubmitInput {
  readonly sessionId: string;
  readonly practiceItemId: string;
  readonly answerMd: string;
  readonly attemptType: AttemptType;
  readonly submissionId: string;
  readonly latencySeconds?: number;
  readonly schedulerCandidateId?: string | null;
  readonly assessmentContractVersionId?: string | null;
  readonly declaredStuck?: boolean;
}

export const phone = {
  startSession: (availableMinutes: number, replace?: string) =>
    call<SessionSnapshot>("start_session", { availableMinutes, ...(replace ? { replace } : {}) }),
  adoptSession: (sessionId: string, expectedGeneration: number) =>
    call<Record<string, unknown>>("adopt_session", { sessionId, expectedGeneration }),
  getSession: (sessionId: string) => call<SessionSnapshot>("get_session", { sessionId }),
  endSession: (sessionId: string) => call<SessionEndSummary>("end_session", { sessionId }),
  // `limit`: the phone shows every row it is given, so the offer's receipt is what it showed (§6.4).
  getTodayQueue: (sessionId: string, limit: number) => call<QueueSnapshot>("get_today_queue", { sessionId, limit }),
  getPracticeItem: (practiceItemId: string, sessionId: string) =>
    call<PracticeItemDetail>("get_practice_item", { practiceItemId, sessionId }),
  getProbeContract: (practiceItemId: string, sessionId: string) =>
    call<ProbeContractDto>("get_probe_contract", { practiceItemId, sessionId }),
  saveDraft: (input: {
    sessionId: string;
    practiceItemId: string;
    answerMd: string;
    submissionId: string;
    schedulerCandidateId?: string | null;
    declaredStuck?: boolean;
  }) => call<{ ok: boolean }>("save_practice_draft", input),
  skipItem: (sessionId: string, practiceItemId: string) =>
    call<QueueSnapshot>("skip_practice_item", { sessionId, practiceItemId }),
  submitAttempt: (input: SubmitInput, options: { onAccepted?: (job: AcceptedJob) => void; isCancelled?: () => boolean } = {}) =>
    runLong<AttemptResultDto>("submit_attempt", input, input.submissionId, options),
  acknowledge: (sessionId: string, practiceItemId: string, submissionId: string) =>
    call<{ status: string; acknowledged: boolean }>("acknowledge_practice_submission", { sessionId, practiceItemId, submissionId }),
  getFeedback: (attemptId: string, recordOpen = true) => call<FeedbackBundle>("get_feedback", { attemptId, recordOpen }),
  getClarification: (attemptId: string) => call<GradingClarificationResultDto>("get_grading_clarification", { attemptId }),
  answerClarification: (attemptId: string, answerMd: string, requestId: string) =>
    runLong<AnswerGradingClarificationResultDto>("answer_grading_clarification", { attemptId, answerMd }, requestId),
  diagnosisStatus: (attemptId: string) => call<{ status: DiagnosisStatusValue; summary?: string | null }>("diagnosis_status", { attemptId }),
  queueRevision: () => getJson<{ revision: number }>("/api/v1/queue-revision"),
  submissionStatus: (submissionId: string) =>
    getJson<JobState<AttemptResultDto>>(`/api/v1/submissions/${encodeURIComponent(submissionId)}`)
};
