// UX Phase 4.2 (docs/specs/ux_learnloop_v1.md §7.5, W5b): feedback leads with
// one verdict in words, the learner's answer beside a full answer, the
// criteria as plain ✓ / ✗ lines, one sentence on what went wrong, ONE next
// step and Next. Everything technical sits behind "details ▸". "I think I was
// right" opens a one-line box and the regrade happens in place. A grade held
// for review says so and never shows a score. `[ui] practice_feedback =
// "classic"` restores the screen exactly.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, PracticeItemDetail } from "../api/dto";
import { clear } from "../api/queryCache";
import { setAlgoConfig } from "../app/algoConfig";
import { FeedbackScreen } from "./FeedbackScreen";

const { api } = vi.hoisted(() => {
  const known: Record<string, ReturnType<typeof vi.fn>> = {
    getFeedback: vi.fn(),
    getPracticeItem: vi.fn(),
    getAttemptTrace: vi.fn(),
    getAttemptTraceEvidence: vi.fn(),
    getGradingClarification: vi.fn(),
    diagnosisStatus: vi.fn(),
    refreshFeedback: vi.fn(),
    triggerRegrade: vi.fn(),
    startPrimedRetry: vi.fn(),
    startGuidedRedo: vi.fn(),
    recordDiagnosisFeedback: vi.fn(),
    recordAnswerDisplay: vi.fn()
  };
  const fallback = new Map<string, ReturnType<typeof vi.fn>>();
  const api = new Proxy(known, {
    get(target, prop: string) {
      if (prop in target) return target[prop];
      if (!fallback.has(prop)) fallback.set(prop, vi.fn(() => Promise.reject(new Error(`${prop} not mocked`))));
      return fallback.get(prop);
    }
  });
  return { api };
});
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/ClaimSurface", () => ({
  ClaimSurface: ({ claim }: { claim: { claimText: string } }) => <div>{claim.claimText}</div>,
  mintVisitId: () => "visit"
}));
vi.mock("../components/KnowledgeModel", () => ({ AttemptTraceView: () => null, UnresolvedCauseCard: () => null }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/RepairTrace", () => ({ RepairTraceBlocks: () => null }));

const BUNDLE = {
  version: 1,
  attemptId: "att_01JABCDEFGHJKMNPQRSTVWXYZ",
  practiceItemId: "pi_cond_001",
  learningObjectId: "lo_conditional",
  learningObjectTitle: "Conditional probability",
  rubricScore: 2,
  maxPoints: 4,
  correctness: 0.5,
  graderConfidence: 0.9,
  gradingSource: "ai",
  fallbackReason: null,
  manualReviewReason: null,
  fsrsRating: "hard",
  nextDueAt: "2026-10-20T00:00:00Z",
  criterionEvidence: [
    { criterionId: "setup", criterionDescription: "Set up the conditional probability", pointsAwarded: 2, pointsPossible: 2, evidence: null, notes: null, graderTier: 2 },
    { criterionId: "restrict", criterionDescription: "Restricted the sample space to the condition", pointsAwarded: 0, pointsPossible: 2, evidence: null, notes: null, graderTier: 2 }
  ],
  fatalErrors: [],
  errorAttributions: [],
  surprise: {
    predictiveSurprise: 1.2,
    bayesianSurprise: 0.4,
    surpriseDirection: "negative",
    fsrsIntervalFactor: 0.85,
    followupThresholdNats: 0.9,
    triggeredActions: [],
    suppressedActions: [],
    gateDiagnostics: null
  },
  masteryBefore: { mean: 0.5, variance: 0.05 },
  masteryAfter: { mean: 0.42, variance: 0.04 },
  masteryStep: null,
  feedbackMd: "You used the unconditional probability.",
  repairSuggestions: [],
  guidedRedoAvailable: false,
  interventionNeed: null,
  primed: false,
  sourceRefs: [],
  followupQueued: false,
  heldForReview: false,
  learnerAnswerMd: "P(first=3 | sum=8) = 1/6",
  learnerExplanationMd: null,
  answeredPresentation: null
} as unknown as FeedbackBundle;

const ITEM = {
  id: "pi_cond_001",
  learningObjectId: "lo_conditional",
  learningObjectTitle: "Conditional probability",
  subject: "probability",
  subjects: ["probability"],
  practiceMode: "constructed_response",
  attemptTypesAllowed: [],
  teachBackSource: null,
  presentation: {
    practiceItemId: "pi_cond_001",
    blocks: [{ kind: "prompt", markdown: "Given that the sum is 8, what is P(first = 3)?", label: null }]
  },
  prompt: "Given that the sum is 8, what is P(first = 3)?",
  expectedAnswer: "Five equally likely outcomes; one has first = 3: 1/5.",
  hints: [],
  rubric: null,
  candidateErrorTypes: [],
  sourceRefs: []
} as unknown as PracticeItemDetail;

function props(overrides: Partial<ComponentProps<typeof FeedbackScreen>> = {}): ComponentProps<typeof FeedbackScreen> {
  return {
    attemptId: BUNDLE.attemptId,
    sessionId: "s1",
    onNext: vi.fn(),
    onBack: vi.fn(),
    onOpenNotes: vi.fn(),
    onPrimedRetry: vi.fn(),
    onGuidedRedo: vi.fn(),
    onOpenRepair: vi.fn(),
    onInspect: vi.fn(),
    onAsk: vi.fn(),
    onError: vi.fn(),
    ...overrides
  };
}

async function press(key: string) {
  await act(async () => {
    fireEvent.keyDown(window, { key });
  });
}

function bodyText(): string {
  return document.body.textContent ?? "";
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  api.getFeedback.mockResolvedValue(BUNDLE);
  api.getPracticeItem.mockResolvedValue(ITEM);
  api.getAttemptTrace.mockRejectedValue(new Error("no trace"));
  api.getAttemptTraceEvidence.mockRejectedValue(new Error("no evidence"));
  api.getGradingClarification.mockResolvedValue({ clarification: null });
  api.recordAnswerDisplay.mockResolvedValue({ version: 1, recorded: true });
});
afterEach(() => {
  cleanup();
  clear();
  vi.clearAllMocks();
  setAlgoConfig(undefined);
});

it("leads with a verdict in words, never the score, and keeps the machine's numbers off the surface", async () => {
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Partly right")).toBeTruthy();
  const text = bodyText();
  expect(text).not.toContain("2 / 4");
  for (const internal of ["grader_tier", "FSRS", "Belief update", "nats", "retrievability", "Diagnostic follow-up", BUNDLE.attemptId, "constructed_response"]) {
    expect(text).not.toContain(internal);
  }
});

it("shows the learner's answer beside a full answer, and the criteria as plain ✓ / ✗ lines", async () => {
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("P(first=3 | sum=8) = 1/6")).toBeTruthy();
  expect(screen.getByText("You wrote")).toBeTruthy();
  expect(screen.getByText("A full answer")).toBeTruthy();
  expect(await screen.findByText("Five equally likely outcomes; one has first = 3: 1/5.")).toBeTruthy();
  expect(screen.getByText("Given that the sum is 8, what is P(first = 3)?")).toBeTruthy();
  const setup = screen.getByText("Set up the conditional probability").closest("[data-criterion]");
  const restrict = screen.getByText("Restricted the sample space to the condition").closest("[data-criterion]");
  expect(setup?.textContent).toContain("✓");
  expect(restrict?.textContent).toContain("✗");
  // The grader's own sentence is the one line on what went wrong.
  expect(screen.getByText("You used the unconditional probability.")).toBeTruthy();
});

it("shows the question as it was given, with a method-explicit instruction", async () => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    answeredPresentation: {
      practiceItemId: "pi_cond_001",
      blocks: [
        { kind: "prompt", markdown: "Compute det(A).", label: null },
        { kind: "required_method_instruction", markdown: "Use cofactor expansion in your answer.", label: null }
      ]
    }
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Use cofactor expansion in your answer.")).toBeTruthy();
  expect(screen.getByText("Compute det(A).")).toBeTruthy();
});

it("keeps the score and what the grader looked for behind details, toggled by the button or `.`", async () => {
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  expect(screen.queryByText("2 / 4")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(await screen.findByText("2 / 4")).toBeTruthy();
  expect(bodyText()).toContain("What the grader looked for");
  await press(".");
  expect(screen.queryByText("2 / 4")).toBeNull();
});

it("says held for review and shows no score anywhere, even in details", async () => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    heldForReview: true,
    criterionEvidence: BUNDLE.criterionEvidence.map((row) => ({ ...row, assessed: false })),
    manualReviewReason: "route_unverified_hold"
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Held for review")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  await screen.findByText(/held for review/i, { selector: "[data-testid=details-score]" });
  const text = bodyText();
  expect(text).not.toMatch(/\b2(\.0)? \/ 4/);
  expect(text).not.toContain("manual review recommended");
  expect(text).not.toContain("Partly right");
});

it("contests in place: I think I was right opens a one-line box and regrades with the learner's reason", async () => {
  api.triggerRegrade.mockResolvedValue({ ...BUNDLE, rubricScore: 4, correctness: 1 });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  const box = screen.getByRole("textbox", { name: /why you think you were right/i });
  fireEvent.change(box, { target: { value: "1/5 is what I meant" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /look again/i }));
  });
  expect(api.triggerRegrade).toHaveBeenCalledWith(BUNDLE.attemptId, "1/5 is what I meant", expect.any(String));
  expect(await screen.findByText("Right")).toBeTruthy();
  expect(bodyText()).toContain("now Right");
});

it("keeps the reason and says so plainly when the grader cannot look again", async () => {
  // Codex review F7: the sidecar confirms the note is kept and says the grader
  // did not run (no error any more once the note is recorded).
  api.triggerRegrade.mockResolvedValue({ ...BUNDLE, contest: { recorded: true, regraded: false, reviewRequested: true } });
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /look again/i }));
  });
  expect(await screen.findByText(/your note is kept/i)).toBeTruthy();
  expect(callbacks.onError).not.toHaveBeenCalled();
  expect(bodyText()).not.toContain("Codex");
});

it("never offers to contest a grade the learner gave themselves", async () => {
  api.getFeedback.mockResolvedValue({ ...BUNDLE, gradingSource: "self", fallbackReason: "provider_auth_required" });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  expect(screen.queryByRole("button", { name: /I think I was right/ })).toBeNull();
  expect(bodyText()).toContain("graded by you");
  expect(bodyText()).not.toContain("provider_auth_required");
});

it("offers one next step: fixing a named mix-up as a timed step", async () => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    matchedMisconception: {
      id: "mis_uncond",
      statement: "Treats P(A|B) as P(A)",
      correctionStatement: "Conditioning on the sum shrinks the outcomes to five.",
      mechanism: null,
      targetFacet: "facet_conditional",
      confusedWithFacet: "facet_unconditional",
      status: "active"
    }
  });
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  const fix = await screen.findByRole("button", { name: "Fix this mix-up · about 4 min" });
  fireEvent.click(fix);
  expect(callbacks.onOpenRepair).toHaveBeenCalledWith("mis_uncond");
  // One next step, not three.
  expect(screen.queryByRole("button", { name: /Try a similar one/ })).toBeNull();
  expect(bodyText()).toContain("Conditioning on the sum shrinks the outcomes to five.");
  expect(bodyText()).not.toMatch(/misconception/i);
});

it("offers the guided redo when the grader kept the learner's correct work", async () => {
  api.getFeedback.mockResolvedValue({ ...BUNDLE, guidedRedoAvailable: true });
  api.startGuidedRedo.mockResolvedValue({ practiceItemId: "pi_cond_001", learnerWorkPrefix: "Setup" });
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  const redo = await screen.findByRole("button", { name: "Redo the part you missed" });
  await act(async () => {
    fireEvent.click(redo);
  });
  expect(callbacks.onGuidedRedo).toHaveBeenCalled();
});

it("otherwise offers a similar question, on the button or `t`", async () => {
  api.startPrimedRetry.mockResolvedValue({ available: true, practiceItem: { id: "pi_sibling" } });
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByRole("button", { name: /Try a similar one/ });
  await press("t");
  await waitFor(() => expect(callbacks.onPrimedRetry).toHaveBeenCalledWith("pi_sibling"));
});

it("has a Next button, and Next returns to where the attempt started", async () => {
  const callbacks = props({ origin: "reader" });
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("Partly right");
  expect(screen.getByText(/Back to the book/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /^Next/ }));
  await waitFor(() => expect(callbacks.onNext).toHaveBeenCalledOnce());
  await press("Enter");
  await waitFor(() => expect(callbacks.onNext).toHaveBeenCalledTimes(2));
});

it("replaces the grader's sentence with the diagnosis in place when it lands, with no analyzing banner", async () => {
  api.getFeedback.mockResolvedValue({ ...BUNDLE, diagnosisStatus: "pending" });
  let resolveCard!: (value: unknown) => void;
  api.diagnosisStatus.mockReturnValueOnce(new Promise((done) => { resolveCard = done; }));
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("You used the unconditional probability.")).toBeTruthy();
  expect(bodyText()).not.toMatch(/analyzing/i);
  api.refreshFeedback.mockResolvedValue({ ...BUNDLE, diagnosisStatus: "done" });
  api.diagnosisStatus.mockResolvedValue({
    version: 1, attemptId: BUNDLE.attemptId, status: "done", cardEnabled: true, diagnosisId: "dx_1",
    responses: [], summaryMd: "You conditioned on the wrong event: use only outcomes with sum 8.",
    repairSuggestions: [], madeBefore: [], prerequisiteGap: null
  });
  await act(async () => resolveCard({
    version: 1, attemptId: BUNDLE.attemptId, status: "done", cardEnabled: true, diagnosisId: "dx_1",
    responses: [], summaryMd: "You conditioned on the wrong event: use only outcomes with sum 8.",
    repairSuggestions: [], madeBefore: [], prerequisiteGap: null
  }));
  expect(await screen.findByText("You conditioned on the wrong event: use only outcomes with sum 8.")).toBeTruthy();
  expect(screen.queryByText("You used the unconditional probability.")).toBeNull();
});

it("says a provisional grade may change, with the one question behind details", async () => {
  api.getFeedback.mockResolvedValue({ ...BUNDLE, manualReviewReason: "provisional_pending_clarification" });
  api.getGradingClarification.mockResolvedValue({
    clarification: { id: "cl_1", attemptId: BUNDLE.attemptId, reason: "ambiguous_notation", questionMd: "Did you mean 1/5 or 1/6?", status: "open" }
  });
  render(<FeedbackScreen {...props()} />);
  const line = await screen.findByRole("button", { name: /This grade may change after one question/ });
  expect(screen.queryByText("Did you mean 1/5 or 1/6?")).toBeNull();
  fireEvent.click(line);
  expect(await screen.findByText("Did you mean 1/5 or 1/6?")).toBeTruthy();
});

it("classic restores the screen exactly: the score block, the grader tier and the schedule", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Conditional probability");
  await waitFor(() => expect(bodyText()).toContain("grader_tier 2"));
  expect(bodyText()).toContain("Rubric · criterion evidence");
  expect(bodyText()).toContain("FSRS rating");
  expect(screen.queryByText("Partly right")).toBeNull();
  expect(screen.queryByRole("button", { name: /I think I was right/ })).toBeNull();
});

// Found in the Phase 4 harness walk (fake AI, the linear-algebra library copy).
it("offers nothing to contest on a right answer", async () => {
  api.getFeedback.mockResolvedValue({ ...BUNDLE, rubricScore: 4, correctness: 1 });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Right")).toBeTruthy();
  expect(screen.queryByRole("button", { name: /I think I was right/ })).toBeNull();
  await press("r");
  expect(screen.queryByRole("textbox", { name: /why you think you were right/i })).toBeNull();
});

it("offers why? when the possible causes are known but no sentence is, and keeps the learner's verdict noted", async () => {
  const causal = {
    receiptId: "r1", verifiedCorrection: null,
    causalHypotheses: [{ hypothesisId: "h1", label: "old rule", statement: "The old rule still seemed to apply.", causeScope: "learner_state", supportScore: null }],
    unverified: [], proposedNextAction: null, demonstratedCriteria: [], firstDivergence: null, protectedTargets: [],
    contestAction: { available: true, reasons: ["diagnosis_wrong"], factorId: null },
    repairedTrace: null, repairedTraceWithheldReason: null, permittedUses: []
  };
  api.getFeedback.mockResolvedValue({ ...BUNDLE, feedbackMd: null, causalFeedback: causal });
  api.contestCausalDiagnosis.mockResolvedValue({});
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /why\?/ }));
  expect(screen.getByText(/The old rule still seemed to apply/)).toBeTruthy();
  api.getFeedback.mockResolvedValue({ ...BUNDLE, feedbackMd: null, causalFeedback: { ...causal, contestAction: { available: false, reasons: [], factorId: null } } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "this doesn't sound right" }));
  });
  expect(await screen.findByText("Noted. Thanks.")).toBeTruthy();
});

// == Codex review (docs/reviews/ux-phase4-feedback-codex-review.md) ==========

it("F1: showing the full answer charges the reveal ledger, once per attempt", async () => {
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Five equally likely outcomes; one has first = 3: 1/5.")).toBeTruthy();
  await waitFor(() => expect(api.recordAnswerDisplay).toHaveBeenCalledWith(BUNDLE.attemptId));
  // Details and the bundle's re-reads re-render the surface; nothing new is charged.
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  await press(".");
  expect(api.recordAnswerDisplay).toHaveBeenCalledTimes(1);
});

it("F1: no full answer on screen, nothing charged", async () => {
  api.getPracticeItem.mockResolvedValue({ ...ITEM, expectedAnswer: "" });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  expect(screen.queryByText("A full answer")).toBeNull();
  expect(api.recordAnswerDisplay).not.toHaveBeenCalled();
});

it("F5: the full answer and criteria are the graded contract's, never today's key beside the question given", async () => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    answeredPresentation: {
      practiceItemId: "pi_cond_001",
      blocks: [{ kind: "prompt", markdown: "Given that the sum is 7, what is P(first = 3)?", label: null }]
    },
    answeredExpectedAnswer: "Six equally likely outcomes; one has first = 3: 1/6.",
    answeredCriteria: {
      setup: { description: "Set up P(first=3 | sum=7)", pointsPossible: 2 },
      restrict: { description: "Restricted to the six outcomes", pointsPossible: 2 }
    }
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Six equally likely outcomes; one has first = 3: 1/6.")).toBeTruthy();
  expect(screen.getByText("Given that the sum is 7, what is P(first = 3)?")).toBeTruthy();
  expect(screen.queryByText("Five equally likely outcomes; one has first = 3: 1/5.")).toBeNull();
  expect(screen.getByText("Set up P(first=3 | sum=7)")).toBeTruthy();
  expect(screen.queryByText("Set up the conditional probability")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(bodyText()).toContain("Restricted to the six outcomes");
  expect(bodyText()).not.toContain("Restricted the sample space to the condition");
});

const HELD = {
  ...BUNDLE,
  rubricScore: 0,
  correctness: 0,
  heldForReview: true,
  criterionEvidence: BUNDLE.criterionEvidence.map((row) => ({ ...row, pointsAwarded: 0, assessed: false })),
  manualReviewReason: "route_unverified_hold"
} as unknown as FeedbackBundle;
const RELEASED = { ...BUNDLE, rubricScore: 4, correctness: 1, heldForReview: false } as unknown as FeedbackBundle;

it("F6: a hold released in place says Held for review → Right, never the held score", async () => {
  api.getFeedback.mockResolvedValue(HELD);
  api.triggerRegrade.mockResolvedValue({ ...RELEASED, contest: { recorded: true, regraded: true, reviewRequested: false } });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Held for review");
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /look again/i }));
  });
  expect(await screen.findByText(/now Right/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("regrade-history").textContent).toBe("Looked at again: Held for review → Right.");
  expect(bodyText()).not.toMatch(/\b0(\.0)? \/ 4/);
});

it("F6: a reopened feedback whose regrade released a hold shows no held score either", async () => {
  api.getFeedback.mockResolvedValue({
    ...RELEASED,
    regrade: { oldScore: 0, newScore: 4, maxPoints: 4, regradedAt: "2026-10-14T00:00:00Z", direction: "up", oldHeld: true }
  });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Right");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("regrade-history").textContent).toBe("Looked at again: Held for review → Right.");
  expect(bodyText()).not.toMatch(/\b0(\.0)? \/ 4/);
});

it("F6: an ordinary regrade keeps its numbers in details", async () => {
  api.getFeedback.mockResolvedValue({
    ...RELEASED,
    regrade: { oldScore: 2, newScore: 4, maxPoints: 4, regradedAt: "2026-10-14T00:00:00Z", direction: "up", oldHeld: false }
  });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Right");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("regrade-history").textContent).toBe("Looked at again: 2 / 4 → 4 / 4.");
});

it("F7: a contest that was not confirmed keeps the box and the reason, and a retry reuses its key", async () => {
  api.triggerRegrade.mockRejectedValueOnce({ code: "sidecar_unavailable", message: "The sidecar is not running", retryable: true });
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  fireEvent.change(screen.getByRole("textbox", { name: /why you think you were right/i }), { target: { value: "1/5 is right" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /look again/i }));
  });
  expect(await screen.findByText("Your note couldn't be sent. Try again.")).toBeTruthy();
  expect(bodyText()).not.toMatch(/note is kept/i);
  const box = screen.getByRole("textbox", { name: /why you think you were right/i }) as HTMLInputElement;
  expect(box.value).toBe("1/5 is right");
  expect(callbacks.onError).not.toHaveBeenCalled();

  api.triggerRegrade.mockResolvedValueOnce({ ...BUNDLE, contest: { recorded: true, regraded: true, reviewRequested: true } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /look again/i }));
  });
  expect(await screen.findByText(/Your note is kept\. It's marked for review\./)).toBeTruthy();
  const [first, second] = api.triggerRegrade.mock.calls;
  expect(second[2]).toBe(first[2]);
  expect(second[1]).toBe("1/5 is right");
  expect(screen.queryByRole("textbox", { name: /why you think you were right/i })).toBeNull();
});

it("F7: a new contest after a confirmed one gets a new key", async () => {
  api.triggerRegrade.mockResolvedValue({ ...BUNDLE, contest: { recorded: true, regraded: true, reviewRequested: true } });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  for (let round = 0; round < 2; round += 1) {
    fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /look again/i }));
    });
    await screen.findByText(/Your note is kept/);
  }
  const [first, second] = api.triggerRegrade.mock.calls;
  expect(second[2]).not.toBe(first[2]);
});
