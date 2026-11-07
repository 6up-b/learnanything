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
  AsPrintedViewDto,
  ReaderAnswerDto,
  ReaderAskHistoryDto,
  ReaderCaptureReceiptDto,
  ReaderDoseOfferDto,
  ReaderDoseOfferEvent,
  ReaderGuidePlanDto,
  ReaderProgressListDto,
  ReaderRenderBlockDto,
  ReaderRenderViewDto,
  SessionEndSummary,
  SessionSnapshot,
  SourceLibraryCard
} from "@desktop/api/dto";
import { call, getJson, rpcOnce, runLong, type AcceptedJob, type JobState, type RpcOutcome } from "./http";

/** Mobile v2 V4: a block as a phone origin gets it: a withheld passage's text never reaches the phone. */
export type PhoneReaderBlock = ReaderRenderBlockDto & { readonly withheld?: boolean };

/** Mobile v2 §3.2: one section of a reading (``reader.render_view`` with ``sectionId``). */
export interface PhoneSectionDto extends Omit<ReaderRenderViewDto, "blocks"> {
  readonly blocks: PhoneReaderBlock[];
  readonly range?: { sectionId: string | null; fromSpanId: string | null; toSpanId: string | null; blockCount: number };
}

/** The Read tab's book (``get_source_library`` at a phone origin): only books the phone's Reader opens. */
export interface PhoneBookDto extends SourceLibraryCard {
  readonly extractionId: string;
}

/** Mobile v2 §3.5: what the selection sheet's Ask sends (the desktop's ``reader.ask``). */
export interface PhoneAskInput {
  readonly extractionId: string;
  readonly spanId: string;
  readonly question: string;
  readonly selectionSpanIds?: string[];
  readonly selectionQuote?: string | null;
  readonly retrievalIntent?: "explain" | "alternative" | "remediate";
  readonly parentExchangeId?: string | null;
}

/** One section's reading progress, as the desktop's Reader reports it (`reader.mark_section_progress`). */
export interface ProgressInput {
  readonly extractionId: string;
  readonly sectionId: string;
  readonly spansSeen?: number;
  readonly spanCount?: number;
  readonly completed?: boolean;
}

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
  // ── Mobile v2 V4 (D4): the phone Reader, text first. Every one is the desktop's handler. ──
  library: () => call<{ sources: PhoneBookDto[] }>("get_source_library", {}),
  guidePlan: (extractionId: string) => call<ReaderGuidePlanDto>("reader.guide_plan", { extractionId }),
  /** §3.2: one section's blocks, in the desktop's block shape. */
  section: (extractionId: string, sectionId: string) =>
    call<PhoneSectionDto>("reader.render_view", { extractionId, sectionId }),
  readerProgress: (extractionId: string) => call<ReaderProgressListDto>("reader.get_progress", { extractionId }),
  /** §3.4: the dose arm's draw at a section boundary (the server's, made before anything shows). */
  doseOffer: (extractionId: string, sectionId: string, visitId: string) =>
    call<ReaderDoseOfferDto>("reader.dose_offer", { extractionId, sectionId, visitId }),
  /** §3.5: the desktop's Ask on the selected passages, as a job (D2: its routes and budgets). */
  ask: (input: PhoneAskInput, requestId: string, options: { isCancelled?: () => boolean } = {}) =>
    runLong<ReaderAnswerDto>("reader.ask", input, requestId, options),
  askHistory: (extractionId: string) => call<ReaderAskHistoryDto>("reader.ask_history", { extractionId }),
  /** §3.5's Save: a plain highlight of the selection (local first; the desktop drains its outbox). */
  save: (input: {
    sourceId: string;
    revisionId: string;
    extractionId: string;
    clientIdempotencyKey: string;
    rawSelection: { nodes: Array<{ spanId: string; quote: string }> };
    renderViewId?: string | null;
  }) => call<ReaderCaptureReceiptDto>("reader.capture", { ...input, action: "highlight" }),
  /** CA7's *as printed* after feedback: what the item may show of its print, decided on the server. */
  asPrinted: (practiceItemId: string) => call<AsPrintedViewDto>("practice.as_printed", { practiceItemId, render: true }),
  /** The plan's reading block, ended as the desktop's banner and skip end it (DL1 §6.10). */
  planReadingEnded: (outcome: "left_reader" | "skipped", sessionId: string | null) =>
    call<PhonePlanDto>("plan_reading_ended", { outcome, sessionId }),
  // §5.4's reader intents, sent by the outbox (`store/outbox.ts`, `READER_INTENT`) under the intent's own key, once
  // per flush: an accepted job (202) is sent again under its key until the host answers its end (Codex review F7).
  markProgress: (input: ProgressInput, requestId: string): Promise<RpcOutcome<unknown>> =>
    rpcOnce("reader.mark_section_progress", input, requestId),
  logActivity: (events: ReadonlyArray<Record<string, unknown>>, requestId: string): Promise<RpcOutcome<unknown>> =>
    rpcOnce("reader.log_activity", { events }, requestId),
  doseOfferEvent: (drawId: string, event: ReaderDoseOfferEvent, requestId: string): Promise<RpcOutcome<unknown>> =>
    rpcOnce("reader.dose_offer_event", { drawId, event }, requestId),
  /** A taken extra question's answer, as the desktop's quick-check card sends it (Codex review F9). */
  authoredQuestionAction: (questionId: string, response: string) =>
    call<{ question: unknown }>("reader.authored_question_action", { questionId, action: "answered", response }),
  queueRevision: () => getJson<{ revision: number }>("/api/v1/queue-revision"),
  submissionStatus: (submissionId: string) =>
    getJson<JobState<AttemptResultDto>>(`/api/v1/submissions/${encodeURIComponent(submissionId)}`)
};
