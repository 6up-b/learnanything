// The allowlisted methods the phone's screens use (§4.5), with the desktop's DTOs.
import type {
  AnswerGradingClarificationResultDto,
  AttemptResultDto,
  AttemptType,
  DailyPlanDto,
  DiagnosisCardDto,
  ElicitingResponseResultDto,
  FeedbackBundle,
  FirstHintProgress,
  FollowupDto,
  GradingClarificationResultDto,
  HypothesisMark,
  HypothesisMarksDto,
  PlanStepDto,
  PracticeItemDetail,
  ProbeContractDto,
  QueueSnapshot,
  SessionEndSummary,
  SessionSnapshot,
  SomethingElseChosenDto,
  SomethingElseKind,
  SomethingElseOptionsDto
} from "@desktop/api/dto";
import { call, getJson, runLong, type AcceptedJob, type JobState } from "./http";

/** Mobile v2 §2.2: everything open waits for the desktop. The phone's Next crosses a boundary past it;
 *  its Skip is the desktop's own skip link, for the first of them. */
export interface HeldStepDto {
  readonly kind: "held_for_desktop";
  readonly planId: string;
  readonly heldCount: number;
  readonly heldReadings: number;
  readonly firstHeldItemId: string | null;
  /** J5: a stop drawn past this held work, offered as a done step's (the plan stays open for that work). */
  readonly stopOffer?: { readonly stopReason: string | null } | null;
}

export type PhoneStepDto = PlanStepDto | HeldStepDto;

/** FG1 §6: the workflow's read of one answer, or nothing (no workflow, the switch off). */
export type FollowupStatusDto = { enabled: false } | ({ enabled: true } & FollowupDto);

/** The desktop's plan reply, as a phone origin gets it: its step may be held, and it carries the count. */
export interface PhonePlanDto extends Omit<DailyPlanDto, "step"> {
  readonly step?: PhoneStepDto | null;
  readonly device?: { readonly surface: string; readonly deferredCount: number; readonly readingsWaiting: number };
}

/** IH3: what a phone choice came to (the plan's reply, with the preference it kept). */
export interface PhoneSomethingElseDto extends Omit<SomethingElseChosenDto, "step"> {
  readonly step?: PhoneStepDto | null;
}

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
  readonly hintsUsed?: number;
  readonly authoredHints?: number;
  readonly bookCounted?: boolean;
  readonly planPresentationId?: string | null;
  readonly firstHintProgress?: FirstHintProgress | null;
  /** Mobile v2 V3 (D3): a probe's answer consumes its committed presentation. */
  readonly probePresentationId?: string | null;
}

/** FG1 §6.1: what Next on a miss's feedback does: wait for its question, open it, or go on. */
export interface FollowupNextDto {
  readonly version: number;
  readonly action: "wait" | "open" | "continue";
  readonly line: string | null;
  readonly practiceItemId: string | null;
  readonly presentationId: string | null;
}

export const phone = {
  startSession: (availableMinutes: number, replace?: string) =>
    call<SessionSnapshot>("start_session", { availableMinutes, ...(replace ? { replace } : {}) }),
  adoptSession: (sessionId: string, expectedGeneration: number) =>
    call<Record<string, unknown>>("adopt_session", { sessionId, expectedGeneration }),
  getSession: (sessionId: string) => call<SessionSnapshot>("get_session", { sessionId }),
  endSession: (sessionId: string) => call<SessionEndSummary>("end_session", { sessionId }),
  // `limit`: the phone shows every row it is given, so the offer's receipt is what it showed (§6.4).
  getTodayQueue: (sessionId: string, limit: number, availableMinutes?: number | null) =>
    call<QueueSnapshot>("get_today_queue", { sessionId, limit, availableMinutes: availableMinutes ?? null }),
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
    hintsUsed?: number;
    planPresentationId?: string | null;
    firstHintProgress?: FirstHintProgress | null;
    hintSeen?: boolean;
    pageSeen?: boolean;
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
  diagnosisStatus: (attemptId: string) => call<DiagnosisCardDto>("diagnosis_status", { attemptId }),
  // `suggestionIndex` indexes the bundle's `repairSuggestions`, which is the handler's contract.
  submitElicitingResponse: (attemptId: string, suggestionIndex: number, responseMd: string) =>
    call<ElicitingResponseResultDto>("submit_eliciting_response", { attemptId, suggestionIndex, responseMd }),
  // ── Mobile v2 V2, J1: Today is the shared plan, filtered at the step (§2.2). ──
  getDailyPlan: (sessionId: string | null) => call<PhonePlanDto>("get_daily_plan", { sessionId }),
  /** Long-capable (§2.2): a decision at a boundary can call a model, so this is a job under `requestId`.
   *  Always a serve: the phone makes no peek, because a peek can cross a boundary and write its decision. */
  nextPlanItem: (sessionId: string, requestId: string, skipPracticeItemId?: string | null) =>
    runLong<PhonePlanDto>(
      "next_plan_item",
      { sessionId, serve: true, ...(skipPracticeItemId ? { skipPracticeItemId } : {}) },
      requestId
    ),
  /** Spec_instruct_handoff_v1 §3a: starts the next boundary's model calls while feedback shows, and returns. It
   *  writes nothing and returns no step, so it isn't a peek. Next's serve finds the job. */
  planPrefetch: (sessionId: string) => call<{ started: boolean; reason: string }>("plan_prefetch", { sessionId }),
  /** Spec_instruct_handoff_v1 §6 (IH3): what the plan could do at this boundary, in plain words, for "Something else
   *  would help". Draws nothing. A lesson or a reading comes back `servable: false` (the phone logs it, the desktop serves it). */
  planSomethingElseOptions: (sessionId: string | null) =>
    call<SomethingElseOptionsDto>("plan_something_else_options", { sessionId }),
  /** IH3: serve the action the learner chose and keep it with the options then. `preferenceId` is the act's own key: a
   *  retried send is answered as it was made and writes once. */
  planSomethingElse: (input: {
    sessionId: string | null;
    kind: SomethingElseKind;
    ref: string | null;
    surface: "phone_feedback" | "phone_today";
    attemptId?: string | null;
    noteMd?: string | null;
    preferenceId: string;
  }) => call<PhoneSomethingElseDto>("plan_something_else", input),
  /** The plan's record of a skip (the desktop's skip link), serving nothing: Today reads what is next. */
  skipPlanItem: (sessionId: string, skipPracticeItemId: string, requestId: string) =>
    runLong<PhonePlanDto>("next_plan_item", { sessionId, skipPracticeItemId }, requestId),
  setPlanMinutes: (minutes: number, sessionId: string | null) => call<PhonePlanDto>("set_plan_minutes", { minutes, sessionId }),
  /** J5: "Keep going" builds one more block of minutes; `stop` is "Done for today". */
  planKeepGoing: (sessionId: string | null, stop = false) =>
    call<PhonePlanDto>("plan_keep_going", { sessionId, ...(stop ? { stop: true } : {}) }),
  // ── J4: the router's visible decisions (read only). ──
  routerObjectiveExplain: (decisionId: string) =>
    call<{ version: number; available: boolean; decisionId?: string; lines: string[] }>("router_objective_explain", { decisionId }),
  // ── J2: reveals, the contest. ──
  /** One routine display row for the full answer, written before it shows (UX Phase 4, round 3 F1). */
  recordAnswerDisplay: (attemptId: string, displayId: string) =>
    call<{ recorded: boolean; alreadyRecorded?: boolean; recordedAt?: string }>("record_answer_display", { attemptId, displayId }),
  /** "I think I was right": the reason is kept before the regrade, which stays blind to it. One key per contest. */
  contestGrade: (attemptId: string, learnerReason: string, contestId: string) =>
    runLong<FeedbackBundle>("trigger_regrade", { attemptId, learnerReason, contestId }, contestId),
  // ── J3 without probes: the held feedback and its ways out, and the optional marks. ──
  followupStatus: (attemptId: string) => call<FollowupStatusDto>("followup_status", { attemptId }),
  followupContinueWithout: (attemptId: string) => call<{ continued: boolean }>("followup_continue_without", { attemptId }),
  followupShowAnyway: (attemptId: string) => call<{ released: boolean }>("followup_show_anyway", { attemptId }),
  // ── V3 (D3): the miss's question, opened by Next and answered here. Not retried: it can write. ──
  followupNext: (attemptId: string) => call<FollowupNextDto>("followup_next", { attemptId }),
  recordHypothesisExposure: (input: { attemptId: string; surface: string; hypothesisVersionIds: string[]; shownAt: string }) =>
    call<{ recorded: boolean }>("record_hypothesis_exposure", input),
  recordHypothesisMark: (input: {
    attemptId: string;
    mark: HypothesisMark | "none_of_these" | "cleared";
    hypothesisVersionId: string | null;
    freeText: string | null;
    surface: string;
  }) => call<{ recorded: boolean; marks: HypothesisMarksDto | null }>("record_hypothesis_mark", input),
  // ── J16 partial: an item's own hint, revealed here (telemetry; submit counts it). ──
  recordHintReveal: (input: {
    sessionId: string;
    practiceItemId: string;
    submissionId: string;
    authoredIndex: number;
    answerMd: string;
    revealedAt: string;
  }) => call<{ recorded: boolean; reason: string | null; assistId: string | null }>("practice.record_hint_reveal", input),
  queueRevision: () => getJson<{ revision: number }>("/api/v1/queue-revision"),
  submissionStatus: (submissionId: string) =>
    getJson<JobState<AttemptResultDto>>(`/api/v1/submissions/${encodeURIComponent(submissionId)}`)
};
