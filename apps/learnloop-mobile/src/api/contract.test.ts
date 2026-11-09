// The phone's half of the request contract (mobile v2 §7.2). Every wrapper in `phone.ts` is called
// with the argument shapes the screens use, and the request it puts on the wire is recorded in
// `contract/<method>.json`, with the reply fields the screens read. `tests/test_mobile_phone_contract.py`
// runs each recorded request through the host's own checks and each `reads` list against a real
// reply. A renamed or added field on either side then fails the build, not the phone.
//
// The files are compared, never silently rewritten: `LEARNLOOP_UPDATE_PHONE_CONTRACT=1` rewrites them.
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { saveCredential } from "../store/credential";
import { phone, type SubmitInput } from "./phone";
import { PHONE_METHODS } from "./phoneMethods";
import phoneSource from "./phone.ts?raw";

const CONTRACT_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "contract");
const UPDATE = process.env.LEARNLOOP_UPDATE_PHONE_CONTRACT === "1";

type Wrapper = keyof typeof phone;
/** The two status reads are GETs, not `/rpc`; the host's own tests cover them. */
const NOT_RPC: readonly Wrapper[] = ["queueRevision", "submissionStatus"];

const SUBMIT: SubmitInput = {
  sessionId: "s1", practiceItemId: "i1", answerMd: "My answer", attemptType: "independent_attempt", submissionId: "k1",
  latencySeconds: 42, schedulerCandidateId: "cand_i1", assessmentContractVersionId: "acv", hintsUsed: 0, authoredHints: 0, bookCounted: false
};

/** Every shape each wrapper is called with on today's screens. */
const EXAMPLES: Record<Exclude<Wrapper, (typeof NOT_RPC)[number]>, ReadonlyArray<() => Promise<unknown>>> = {
  startSession: [() => phone.startSession(15), () => phone.startSession(15, "s_desk")],
  adoptSession: [() => phone.adoptSession("s_desk", 0)],
  getSession: [() => phone.getSession("s1")],
  endSession: [() => phone.endSession("s1")],
  getTodayQueue: [() => phone.getTodayQueue("s1", 20, 15), () => phone.getTodayQueue("s1", 20, null)],
  getPracticeItem: [() => phone.getPracticeItem("i1", "s1")],
  getProbeContract: [() => phone.getProbeContract("i1", "s1")],
  saveDraft: [
    () => phone.saveDraft({ sessionId: "s1", practiceItemId: "i1", answerMd: "Half", submissionId: "k1", schedulerCandidateId: "cand_i1", hintsUsed: 0 }),
    () =>
      phone.saveDraft({
        sessionId: "s1", practiceItemId: "i1", answerMd: "Half", submissionId: "k1", schedulerCandidateId: null, hintsUsed: 1,
        planPresentationId: "pp1", firstHintProgress: "draft_started", hintSeen: true, pageSeen: true, declaredStuck: true
      })
  ],
  skipItem: [() => phone.skipItem("s1", "i1")],
  submitAttempt: [
    () => phone.submitAttempt(SUBMIT),
    () =>
      phone.submitAttempt({
        ...SUBMIT, answerMd: "", attemptType: "hinted_attempt", schedulerCandidateId: null, hintsUsed: 2, authoredHints: 1, bookCounted: true,
        planPresentationId: "pp1", firstHintProgress: "no_draft", declaredStuck: true
      }),
    // Mobile v2 V3: a probe's answer names its presentation, with no help.
    () =>
      phone.submitAttempt({
        ...SUBMIT, attemptType: "diagnostic_probe", schedulerCandidateId: null, probePresentationId: "pres_1", planPresentationId: "pp1"
      })
  ],
  acknowledge: [() => phone.acknowledge("s1", "i1", "k1")],
  getFeedback: [() => phone.getFeedback("a1"), () => phone.getFeedback("a1", false)],
  getClarification: [() => phone.getClarification("a1")],
  answerClarification: [() => phone.answerClarification("a1", "I meant the transpose.", "r1")],
  diagnosisStatus: [() => phone.diagnosisStatus("a1")],
  submitElicitingResponse: [() => phone.submitElicitingResponse("a1", 0, "logits")],
  // Mobile v2 V2.
  getDailyPlan: [() => phone.getDailyPlan("s1"), () => phone.getDailyPlan(null)],
  nextPlanItem: [() => phone.nextPlanItem("s1", "r_next"), () => phone.nextPlanItem("s1", "r_next", "i9")],
  skipPlanItem: [() => phone.skipPlanItem("s1", "i1", "r_skip")],
  setPlanMinutes: [() => phone.setPlanMinutes(40, null), () => phone.setPlanMinutes(10, "s1")],
  planKeepGoing: [() => phone.planKeepGoing("s1"), () => phone.planKeepGoing("s1", true), () => phone.planKeepGoing(null)],
  routerObjectiveExplain: [() => phone.routerObjectiveExplain("rd1")],
  recordAnswerDisplay: [() => phone.recordAnswerDisplay("a1", "display_1")],
  contestGrade: [() => phone.contestGrade("a1", "The other convention.", "contest_1"), () => phone.contestGrade("a1", "", "contest_2")],
  followupStatus: [() => phone.followupStatus("a1")],
  followupContinueWithout: [() => phone.followupContinueWithout("a1")],
  followupShowAnyway: [() => phone.followupShowAnyway("a1")],
  // Mobile v2 V3.
  followupNext: [() => phone.followupNext("a1")],
  planPrefetch: [() => phone.planPrefetch("s1")],
  recordHypothesisExposure: [
    () => phone.recordHypothesisExposure({ attemptId: "a1", surface: "marks_feedback", hypothesisVersionIds: ["h1", "h2"], shownAt: "2026-11-06T12:00:00.000Z" })
  ],
  recordHypothesisMark: [
    () => phone.recordHypothesisMark({ attemptId: "a1", mark: "my_gap", hypothesisVersionId: "h1", freeText: null, surface: "marks_feedback" }),
    () => phone.recordHypothesisMark({ attemptId: "a1", mark: "none_of_these", hypothesisVersionId: null, freeText: "Something else.", surface: "marks_feedback" })
  ],
  recordHintReveal: [
    () =>
      phone.recordHintReveal({
        sessionId: "s1", practiceItemId: "i1", submissionId: "k1", authoredIndex: 0, answerMd: "Half", revealedAt: "2026-11-06T12:00:00.000Z"
      })
  ]
};

/**
 * The reply fields the screens read and the host always sends (`a[].b` reads each element). The
 * optional ones a screen checks for (an intent banner, a summary) are not listed: absent is a case
 * the screen already handles.
 */
const SESSION_READS = ["sessionId", "availableMinutes", "endedAt", "ownerDeviceId", "ownerLabel", "ownerGeneration", "checkpoint"];
const READS: Record<string, readonly string[]> = {
  start_session: SESSION_READS,
  get_session: SESSION_READS,
  adopt_session: [],
  end_session: ["attemptsRecorded"],
  get_today_queue: [
    "sections[].items[].practiceItemId", "sections[].items[].schedulerCandidateId", "sections[].items[].learningObjectTitle", "deviceDeferredCount"
  ],
  skip_practice_item: ["sections", "deviceDeferredCount"],
  get_practice_item: [
    "learningObjectTitle", "attemptTypesAllowed", "assessmentContractVersionId", "presentation.blocks[].kind", "presentation.blocks[].markdown",
    "presentation.blocks[].label"
  ],
  get_probe_contract: ["active"],
  save_practice_draft: [],
  submit_attempt: ["attemptId"],
  acknowledge_practice_submission: [],
  // `diagnosisStatus` is absent when no diagnosis was queued, which the screen reads as "none".
  get_feedback: ["learningObjectTitle", "rubricScore", "maxPoints", "manualReviewReason", "feedbackMd", "criterionEvidence", "repairSuggestions"],
  get_grading_clarification: ["clarification"],
  answer_grading_clarification: ["feedback", "error"],
  diagnosis_status: ["status", "cardEnabled"],
  submit_eliciting_response: ["admissibleAsIndependent"],
  // Mobile v2 V2. A plan reply's body is read where the plan is on (`tests/test_mobile_v2_plan.py`);
  // here, on a vault whose plan is off, every one says whether it is.
  get_daily_plan: ["enabled", "plan"],
  next_plan_item: ["enabled"],
  set_plan_minutes: ["enabled"],
  plan_keep_going: ["enabled"],
  router_objective_explain: ["available", "lines"],
  record_answer_display: ["recorded"],
  trigger_regrade: ["contest"],
  followup_status: ["enabled"],
  followup_continue_without: ["continued"],
  followup_show_anyway: ["released"],
  followup_next: ["action", "line", "practiceItemId", "presentationId"],
  plan_prefetch: [],
  record_hypothesis_exposure: ["recorded"],
  record_hypothesis_mark: ["recorded", "marks"],
  "practice.record_hint_reveal": ["recorded"]
};

/** A reply the host journey cannot reach without a diagnosis model, pinned by these tests instead. */
const REPLY_PINNED_BY: Record<string, readonly string[]> = {
  submit_eliciting_response: ["tests/test_dialogue_causal_join.py", "tests/test_ux_phase4_feedback.py"],
  // A mark needs a list of causes, which only a diagnosis writes.
  record_hypothesis_mark: ["tests/test_hypothesis_marks.py"]
};

interface Recorded {
  readonly wrapper: string;
  readonly envelope: { method: string; params: Record<string, unknown>; request_id?: string };
}

const sent: Array<{ method: string; params: Record<string, unknown>; request_id?: string }> = [];

beforeEach(async () => {
  sent.length = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      sent.push(JSON.parse(init?.body as string));
      return new Response(JSON.stringify({ ok: true, result: {} }), { status: 200 });
    })
  );
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

async function record(): Promise<Map<string, Recorded[]>> {
  const byMethod = new Map<string, Recorded[]>();
  for (const [wrapper, examples] of Object.entries(EXAMPLES) as Array<[string, ReadonlyArray<() => Promise<unknown>>]>) {
    for (const example of examples) {
      sent.length = 0;
      await example();
      expect(sent, wrapper).toHaveLength(1);
      const envelope = sent[0];
      const list = byMethod.get(envelope.method) ?? [];
      list.push({ wrapper, envelope });
      byMethod.set(envelope.method, list);
    }
  }
  return byMethod;
}

function render(method: string, requests: Recorded[]): string {
  const contract: Record<string, unknown> = { method, requests, reads: READS[method] ?? [] };
  if (REPLY_PINNED_BY[method]) contract.replyPinnedBy = REPLY_PINNED_BY[method];
  return `${JSON.stringify(contract, null, 2)}\n`;
}

describe("the request contract (§7.2)", () => {
  it("every /rpc wrapper has examples", () => {
    const wrappers = Object.keys(phone).filter((name) => !NOT_RPC.includes(name as Wrapper)).sort();
    expect(Object.keys(EXAMPLES).sort()).toEqual(wrappers);
  });

  it("phone.ts names only methods the allowlist has", () => {
    const named = [...phoneSource.matchAll(/\b(?:call|runLong)(?:<[^()]*?>)?\(\s*"([a-z_.]+)"/g)].map((match) => match[1]);
    expect(named.length).toBeGreaterThan(0);
    const allowed = new Set<string>(PHONE_METHODS);
    expect(named.filter((name) => !allowed.has(name))).toEqual([]);
  });

  it("each method's recorded requests and reads are the committed ones", async () => {
    const byMethod = await record();
    expect(Object.keys(READS).sort()).toEqual([...byMethod.keys()].sort());
    if (UPDATE) mkdirSync(CONTRACT_DIR, { recursive: true });
    const stale: string[] = [];
    for (const [method, requests] of byMethod) {
      const path = join(CONTRACT_DIR, `${method}.json`);
      const expected = render(method, requests);
      if (UPDATE) writeFileSync(path, expected);
      if (!existsSync(path) || readFileSync(path, "utf8") !== expected) stale.push(method);
    }
    const extra = existsSync(CONTRACT_DIR)
      ? readdirSync(CONTRACT_DIR).filter((name) => name.endsWith(".json") && !byMethod.has(name.slice(0, -5)))
      : [];
    expect({ stale, extra }, "rerun with LEARNLOOP_UPDATE_PHONE_CONTRACT=1 and review the diff").toEqual({ stale: [], extra: [] });
  });
});
