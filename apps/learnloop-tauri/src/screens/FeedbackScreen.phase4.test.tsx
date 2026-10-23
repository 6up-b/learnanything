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
// Round 5: the shell window (Tauri), when a test provides one.
const { shell } = vi.hoisted(() => ({ shell: { window: null as unknown } }));
vi.mock("@tauri-apps/api/window", () => ({
  getCurrentWindow: () => {
    if (!shell.window) throw new Error("not in the shell");
    return shell.window;
  }
}));
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
  api.recordAnswerDisplay.mockReset();
  api.recordAnswerDisplay.mockResolvedValue({ version: 1, recorded: true });
});
afterEach(() => {
  cleanup();
  clear();
  vi.clearAllMocks();
  vi.useRealTimers();
  setAlgoConfig(undefined);
  // The page visibility the final-verification F1 tests set.
  delete (document as unknown as Record<string, unknown>).visibilityState;
  shell.window = null;
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

it("F1: showing the full answer charges the reveal ledger, once per visit", async () => {
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Five equally likely outcomes; one has first = 3: 1/5.")).toBeTruthy();
  await waitFor(() =>
    expect(api.recordAnswerDisplay).toHaveBeenCalledWith(BUNDLE.attemptId, expect.stringMatching(/^display_/))
  );
  // Details and the bundle's re-reads re-render the surface; nothing new is charged.
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  await press(".");
  expect(api.recordAnswerDisplay).toHaveBeenCalledTimes(1);
});

it("F1 (re-review): reopening the feedback is a fresh exposure, charged under a new visit", async () => {
  const first = render(<FeedbackScreen {...props()} />);
  await screen.findByText("Five equally likely outcomes; one has first = 3: 1/5.");
  await waitFor(() => expect(api.recordAnswerDisplay).toHaveBeenCalledTimes(1));
  first.unmount();
  clear();

  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Five equally likely outcomes; one has first = 3: 1/5.");
  await waitFor(() => expect(api.recordAnswerDisplay).toHaveBeenCalledTimes(2));
  const [[firstAttempt, firstVisit], [secondAttempt, secondVisit]] = api.recordAnswerDisplay.mock.calls;
  expect([firstAttempt, secondAttempt]).toEqual([BUNDLE.attemptId, BUNDLE.attemptId]);
  expect(firstVisit).toMatch(/^display_/);
  expect(secondVisit).toMatch(/^display_/);
  expect(secondVisit).not.toBe(firstVisit);
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
    answeredCriteria: [
      { criterionId: "setup", description: "Set up P(first=3 | sum=7)", pointsPossible: 2 },
      { criterionId: "restrict", description: "Restricted to the six outcomes", pointsPossible: 2 }
    ],
    answeredMaxPoints: 4
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

it("F8: a frozen criterion with an underscored id keeps its description and points", async () => {
  // The sidecar sends the frozen criteria as rows carrying their id; the id
  // fixtures use (`criterion_correct_selection`) is never camel-cased away.
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    criterionEvidence: [
      { criterionId: "criterion_correct_selection", criterionDescription: "Today's wording", pointsAwarded: 1, pointsPossible: 8, evidence: null, notes: null, graderTier: 2 }
    ],
    answeredCriteria: [{ criterionId: "criterion_correct_selection", description: "Chose the conditional sample space", pointsPossible: 2 }],
    answeredMaxPoints: 2
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Chose the conditional sample space")).toBeTruthy();
  expect(screen.queryByText("Today's wording")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(bodyText()).toContain("1.0 / 2.0");
  expect(bodyText()).not.toContain("1.0 / 8.0");
});

it("F9: a regrade under the corrected item shows its key and rubric beside the question given", async () => {
  // After an ordinary regrade the sidecar sends no frozen key or criteria:
  // the screen reads the corrected item (what the regrade graded against)
  // and the regrade's own rows, and keeps the question the learner was given.
  api.getPracticeItem.mockResolvedValue({ ...ITEM, expectedAnswer: "The corrected key: 1/5." });
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    rubricScore: 6,
    maxPoints: 8,
    correctness: 0.75,
    criterionEvidence: [
      { criterionId: "setup", criterionDescription: "Set up and restricted the sample space", pointsAwarded: 6, pointsPossible: 8, evidence: null, notes: null, graderTier: 3 }
    ],
    answeredPresentation: {
      practiceItemId: "pi_cond_001",
      blocks: [{ kind: "prompt", markdown: "Given that the sum is 7, what is P(first = 3)?", label: null }]
    },
    answeredExpectedAnswer: null,
    answeredCriteria: null,
    answeredMaxPoints: null,
    regrade: { oldScore: 2, newScore: 6, maxPoints: 8, regradedAt: "2026-10-14T00:00:00Z", direction: "up", oldHeld: false }
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("The corrected key: 1/5.")).toBeTruthy();
  expect(screen.getByText("Given that the sum is 7, what is P(first = 3)?")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("details-score").textContent).toContain("6 / 8");
  expect(bodyText()).toContain("6.0 / 8.0");
});

it("F9: an answer still graded under its contract scores out of the contract's maximum", async () => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    rubricScore: 4,
    maxPoints: 8,
    correctness: 1,
    criterionEvidence: [
      { criterionId: "setup", criterionDescription: "Today's 8-point criterion", pointsAwarded: 4, pointsPossible: 8, evidence: null, notes: null, graderTier: 2 }
    ],
    answeredExpectedAnswer: "Six equally likely outcomes; one has first = 3: 1/6.",
    answeredCriteria: [{ criterionId: "setup", description: "Set up P(first=3 | sum=7)", pointsPossible: 4 }],
    answeredMaxPoints: 4
  });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Right");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("details-score").textContent).toContain("4 / 4");
  expect(bodyText()).not.toContain("4 / 8");
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

async function sendContest(reason: string) {
  fireEvent.change(screen.getByRole("textbox", { name: /why you think you were right/i }), { target: { value: reason } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /look again/i }));
  });
}

it("F10: an edited reason after an unconfirmed send is a new contest with a new key", async () => {
  api.triggerRegrade.mockRejectedValueOnce({ code: "sidecar_unavailable", message: "The sidecar is not running", retryable: true });
  api.triggerRegrade.mockResolvedValueOnce({ ...BUNDLE, contest: { recorded: true, regraded: true, reviewRequested: true } });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await sendContest("1/5 is right");
  expect(await screen.findByText("Your note couldn't be sent. Try again.")).toBeTruthy();

  await sendContest("1/5: five outcomes sum to 8");
  await screen.findByText(/Your note is kept/);
  const [first, second] = api.triggerRegrade.mock.calls;
  expect(second[1]).toBe("1/5: five outcomes sum to 8");
  expect(second[2]).not.toBe(first[2]);
});

it("F10: cancelling an unconfirmed contest and opening a new one gets a new key", async () => {
  api.triggerRegrade.mockRejectedValueOnce({ code: "sidecar_unavailable", message: "The sidecar is not running", retryable: true });
  api.triggerRegrade.mockResolvedValueOnce({ ...BUNDLE, contest: { recorded: true, regraded: true, reviewRequested: true } });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await sendContest("1/5 is right");
  await screen.findByText("Your note couldn't be sent. Try again.");
  fireEvent.click(screen.getByRole("button", { name: /never mind/i }));

  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await sendContest("1/5 is right");
  await screen.findByText(/Your note is kept/);
  const [first, second] = api.triggerRegrade.mock.calls;
  expect(second[2]).not.toBe(first[2]);
});

// == Round 3 (docs/reviews/ux-phase4-feedback-codex-review.md §9) ==========================
//
// F1: the full answer is on screen only while a committed display row covers
// it (`feedback/answerExposure.ts`; its property test drives random timelines).
// F9: the grade's key and maximum come from its contract, from the regrade that
// just ran ("live"), or nowhere ("unrecorded", labelled).

const KEY = "Five equally likely outcomes; one has first = 3: 1/5.";
const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

async function advance(ms: number) {
  await act(async () => {
    vi.advanceTimersByTime(ms);
  });
  await flush();
}

async function setVisibility(state: DocumentVisibilityState) {
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => state });
  await act(async () => {
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await flush();
}

/** Writes that land at once, stamped when they land (as the sidecar stamps). */
function stampWrites() {
  api.recordAnswerDisplay.mockImplementation(() =>
    Promise.resolve({ version: 1, recorded: true, alreadyRecorded: false, recordedAt: new Date(Date.now()).toISOString() })
  );
}

/** The next write waits until `release()`. */
function holdNextWrite(): { release: () => void } {
  let release = () => undefined as void;
  api.recordAnswerDisplay.mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        release = () => resolve({ version: 1, recorded: true, recordedAt: new Date(Date.now()).toISOString() });
      })
  );
  return { release: () => release() };
}

function displayIds(): string[] {
  return api.recordAnswerDisplay.mock.calls.map(([, id]) => String(id));
}

it("F1 (round 3): the full answer appears only once its display row is committed", async () => {
  vi.useFakeTimers();
  const held = holdNextWrite();
  render(<FeedbackScreen {...props()} />);
  await flush();
  expect(screen.getByText("A full answer")).toBeTruthy();
  expect(screen.queryByText(KEY)).toBeNull();
  expect(displayIds()).toHaveLength(1);
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
});

it("F1 (round 3): a write that failed is never taken as shown, and is retried under the same display", async () => {
  vi.useFakeTimers();
  stampWrites();
  api.recordAnswerDisplay.mockRejectedValueOnce({ code: "display_not_recorded", message: "not recorded", retryable: true });
  render(<FeedbackScreen {...props()} />);
  await flush();
  expect(screen.queryByText(KEY)).toBeNull();
  expect(screen.getByText(/can't be shown right now/)).toBeTruthy();
  await advance(5 * SECOND);
  expect(screen.getByText(KEY)).toBeTruthy();
  const [first, retry] = displayIds();
  expect(retry).toBe(first);
  await advance(10 * MINUTE);
  expect(displayIds()).toHaveLength(2);
});

it("F1 (round 3): returning after the row's grace writes a new row before the answer shows again", async () => {
  vi.useFakeTimers();
  stampWrites();
  render(<FeedbackScreen {...props()} />);
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  await setVisibility("hidden");
  await advance(2 * DAY);
  expect(displayIds()).toHaveLength(1);
  const held = holdNextWrite();
  await setVisibility("visible");
  expect(screen.queryByText(KEY)).toBeNull();
  expect(displayIds()).toHaveLength(2);
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  const [mounted, returned] = displayIds();
  expect(returned).not.toBe(mounted);
});

it("F1 (round 3): a machine that slept with the answer open hides it at its first check, until a new row lands", async () => {
  vi.useFakeTimers();
  stampWrites();
  render(<FeedbackScreen {...props()} />);
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  // Asleep for two days: the wall clock moves, no timer runs.
  vi.setSystemTime(Date.now() + 2 * DAY);
  const held = holdNextWrite();
  await advance(5 * SECOND);
  expect(screen.queryByText(KEY)).toBeNull();
  expect(displayIds()).toHaveLength(2);
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
});

it("F1 (round 3): an answer in use stays on screen for 50 hours, always covered by a row no older than its grace", async () => {
  vi.useFakeTimers();
  const stamps: number[] = [];
  api.recordAnswerDisplay.mockImplementation(() => {
    stamps.push(Date.now());
    return Promise.resolve({ version: 1, recorded: true, recordedAt: new Date(Date.now()).toISOString() });
  });
  render(<FeedbackScreen {...props()} />);
  await flush();
  for (let minute = 0; minute < 50 * 60; minute += 10) {
    fireEvent.pointerDown(window);
    await advance(10 * MINUTE);
    if (screen.queryByText(KEY)) {
      const latest = Math.max(...stamps.filter((at) => at <= Date.now()));
      expect(Date.now() - latest).toBeLessThan(HOUR);
    }
  }
  expect(screen.getByText(KEY)).toBeTruthy();
  expect(stamps.length).toBeGreaterThanOrEqual(70);
  expect(new Set(displayIds()).size).toBe(stamps.length);
});

it("F1 (round 3): an unattended screen hides the answer as away, writes nothing more, and shows it again on request", async () => {
  vi.useFakeTimers();
  stampWrites();
  render(<FeedbackScreen {...props()} />);
  await flush();
  await advance(3 * HOUR);
  expect(screen.queryByText(KEY)).toBeNull();
  expect(screen.getByText(/Hidden while you were away/)).toBeTruthy();
  expect(displayIds()).toHaveLength(1);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Show it/ }));
  });
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  expect(displayIds()).toHaveLength(2);
});

it("F1 (round 3): an overlay closed within the row's grace shows the answer at once; after it, a new row first", async () => {
  vi.useFakeTimers();
  stampWrites();
  const base = props();
  const view = render(<FeedbackScreen {...base} answerCovered={false} />);
  await flush();
  view.rerender(<FeedbackScreen {...base} answerCovered />);
  await flush();
  expect(screen.queryByText(KEY)).toBeNull();
  await advance(10 * MINUTE);
  view.rerender(<FeedbackScreen {...base} answerCovered={false} />);
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  expect(displayIds()).toHaveLength(1);
  view.rerender(<FeedbackScreen {...base} answerCovered />);
  await advance(2 * DAY);
  expect(displayIds()).toHaveLength(1);
  const held = holdNextWrite();
  view.rerender(<FeedbackScreen {...base} answerCovered={false} />);
  await flush();
  expect(screen.queryByText(KEY)).toBeNull();
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  expect(new Set(displayIds()).size).toBe(2);
});

const UNRECORDED = {
  ...BUNDLE,
  rubricScore: 6,
  maxPoints: 10,
  correctness: 0.75,
  criterionEvidence: [
    { criterionId: "setup", criterionDescription: "Today's 10-point criterion", pointsAwarded: 6, pointsPossible: 10, evidence: null, notes: null, graderTier: 3 }
  ],
  answeredSource: "unrecorded",
  answeredExpectedAnswer: null,
  answeredCriteria: null,
  answeredMaxPoints: null,
  regrade: {
    oldScore: 2, newScore: 6, maxPoints: 10, regradedAt: "2026-10-14T00:00:00Z", direction: "up", oldHeld: false,
    oldMaxPoints: 4, newMaxPoints: null
  }
} as unknown as FeedbackBundle;

it("F9 (round 3): an unrecorded version says so, labels the current answer as current, charges it, and never shows the item's maximum", async () => {
  api.getFeedback.mockResolvedValue(UNRECORDED);
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  expect(screen.getByText("The version of this question it was graded against wasn't kept.")).toBeTruthy();
  expect(screen.queryByText("A full answer")).toBeNull();
  expect(screen.getByText("The answer as the question reads now")).toBeTruthy();
  expect(await screen.findByText(KEY)).toBeTruthy();
  expect(screen.getByText("It may not be the one this was graded against.")).toBeTruthy();
  expect(api.recordAnswerDisplay).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("details-score").textContent).toContain("6 points");
  expect(bodyText()).not.toMatch(/\/ 10/);
  expect(bodyText()).toContain("6.0 points");
  expect(screen.getByTestId("regrade-history").textContent).toBe("Looked at again: 2 / 4 → 6 points.");
});

it("F9 (round 3): an unrecorded version's grade is scored out of the maximum recorded with it", async () => {
  api.getFeedback.mockResolvedValue({
    ...UNRECORDED,
    answeredMaxPoints: 8,
    regrade: { ...(UNRECORDED.regrade as object), newMaxPoints: 8 }
  });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("details-score").textContent).toContain("6 / 8");
  expect(bodyText()).not.toMatch(/\/ 10/);
  expect(screen.getByTestId("regrade-history").textContent).toBe("Looked at again: 2 / 4 → 6 / 8.");
});

it.each(["contract", "live"] as const)("F9 (round 3): a %s grade shows its own key with no label", async (source) => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    answeredSource: source,
    answeredExpectedAnswer: "The graded key: 1/5.",
    answeredCriteria: [
      { criterionId: "setup", description: "Set up the conditional probability", pointsPossible: 2 },
      { criterionId: "restrict", description: "Restricted the sample space to the condition", pointsPossible: 2 }
    ],
    answeredMaxPoints: 4
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("The graded key: 1/5.")).toBeTruthy();
  expect(screen.queryByText(KEY)).toBeNull();
  expect(screen.queryByText(/wasn't kept/)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("details-score").textContent).toContain("2 / 4");
});

it("F9 (round 3): a regrade in place shows what it read, from its own response", async () => {
  api.triggerRegrade.mockResolvedValue({
    ...BUNDLE,
    rubricScore: 6,
    maxPoints: 8,
    correctness: 0.75,
    answeredSource: "live",
    answeredExpectedAnswer: "The corrected key: 1/5, from five outcomes.",
    answeredCriteria: [{ criterionId: "setup", description: "Set up and restricted", pointsPossible: 8 }],
    answeredMaxPoints: 8,
    contest: { recorded: true, regraded: true, reviewRequested: true }
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText(KEY)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await sendContest("All five outcomes are there");
  expect(await screen.findByText("The corrected key: 1/5, from five outcomes.")).toBeTruthy();
  expect(screen.queryByText(KEY)).toBeNull();
});

it("F9 (final): after a regrade in place the screen re-reads the item, never keeping the one it loaded with", async () => {
  // A sidecar that sends no source with the regrade (the old shape): the
  // screen re-reads the item rather than keep the one it loaded with.
  api.getPracticeItem
    .mockResolvedValueOnce(ITEM)
    .mockResolvedValue({ ...ITEM, expectedAnswer: "The corrected key: 1/5, from five outcomes." });
  api.triggerRegrade.mockResolvedValue({
    ...BUNDLE,
    rubricScore: 6,
    maxPoints: 8,
    correctness: 0.75,
    contest: { recorded: true, regraded: true, reviewRequested: true }
  });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText(KEY)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  await sendContest("All five outcomes are there");
  expect(await screen.findByText("The corrected key: 1/5, from five outcomes.")).toBeTruthy();
  expect(screen.queryByText(KEY)).toBeNull();
});

it("F9 (final): the regrade history scores each side out of its own grade's maximum", async () => {
  api.getFeedback.mockResolvedValue({
    ...BUNDLE,
    rubricScore: 6,
    maxPoints: 8,
    correctness: 0.75,
    answeredSource: "contract",
    answeredMaxPoints: 8,
    regrade: {
      oldScore: 2, newScore: 6, maxPoints: 8, regradedAt: "2026-10-14T00:00:00Z", direction: "up", oldHeld: false,
      oldMaxPoints: 4, newMaxPoints: 8
    }
  });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(screen.getByTestId("regrade-history").textContent).toBe("Looked at again: 2 / 4 → 6 / 8.");
});

// == Round 4 (docs/reviews/ux-phase4-feedback-codex-review.md §10) ==========================

it("F1-1 (round 4): hidden the moment the page is hidden, and back only after a fresh row, even within its grace", async () => {
  vi.useFakeTimers();
  stampWrites();
  render(<FeedbackScreen {...props()} />);
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  await act(async () => {
    Object.defineProperty(document, "visibilityState", { configurable: true, get: () => "hidden" });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  // Synchronously: the frame a suspend keeps is the hidden one.
  expect(screen.queryByText(KEY)).toBeNull();
  await advance(10 * SECOND);
  const held = holdNextWrite();
  await setVisibility("visible");
  expect(screen.queryByText(KEY)).toBeNull();
  expect(displayIds()).toHaveLength(2);
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
});

it.each(["blur", "pagehide", "freeze"] as const)(
  "F1-1 (round 4): a %s hides the answer until a fresh row is acknowledged",
  async (signal) => {
    vi.useFakeTimers();
    stampWrites();
    render(<FeedbackScreen {...props()} />);
    await flush();
    expect(screen.getByText(KEY)).toBeTruthy();
    await act(async () => {
      if (signal === "freeze") document.dispatchEvent(new Event("freeze"));
      else window.dispatchEvent(new Event(signal));
    });
    expect(screen.queryByText(KEY)).toBeNull();
    const held = holdNextWrite();
    await act(async () => {
      if (signal === "freeze") document.dispatchEvent(new Event("resume"));
      else window.dispatchEvent(new Event(signal === "blur" ? "focus" : "pageshow"));
    });
    await flush();
    expect(screen.queryByText(KEY)).toBeNull();
    await act(async () => held.release());
    await flush();
    expect(screen.getByText(KEY)).toBeTruthy();
    expect(new Set(displayIds()).size).toBe(2);
  }
);

it("F1-3 (round 4): a backwards clock jump hides the answer until a fresh row is acknowledged", async () => {
  vi.useFakeTimers();
  stampWrites();
  render(<FeedbackScreen {...props()} />);
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  vi.setSystemTime(Date.now() - 2 * MINUTE);
  const held = holdNextWrite();
  await advance(5 * SECOND);
  expect(screen.queryByText(KEY)).toBeNull();
  expect(displayIds()).toHaveLength(2);
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
});

it("F9 (round 4): an unrecorded grade's details show only what the grade recorded, never today's rubric", async () => {
  api.getFeedback.mockResolvedValue({
    ...UNRECORDED,
    criterionEvidence: [
      { criterionId: "setup", criterionDescription: "The correct answer is B.", pointsAwarded: 6, pointsPossible: 10, evidence: null, notes: null, graderTier: 3, tier: "transfer" }
    ]
  });
  render(<FeedbackScreen {...props()} />);
  await screen.findByText("Partly right");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(bodyText()).not.toContain("The correct answer is B.");
  expect(screen.queryByText("What the grader looked for")).toBeNull();
  expect(screen.getByText("What this grade recorded")).toBeTruthy();
  expect(screen.getByTestId("recorded-criteria").textContent).toContain("setup");
  expect(screen.getByTestId("recorded-criteria").textContent).toContain("6.0 points");
  expect(bodyText()).not.toMatch(/transfer/);
});

// == Round 5 (docs/reviews/ux-phase4-feedback-codex-review.md §11) ==========================

/** A shell window whose events the test delivers and whose state queries it answers. */
function fakeShellWindow() {
  const handlers: Record<string, (event: { payload: unknown }) => void> = {};
  const queries: { minimized: ((value: boolean) => void)[]; visible: ((value: boolean) => void)[] } = { minimized: [], visible: [] };
  const listen = (name: string) => (handler: (event: { payload: unknown }) => void) => {
    handlers[name] = handler;
    return Promise.resolve(() => undefined);
  };
  return {
    handlers,
    queries,
    window: {
      onResized: listen("resized"),
      onScaleChanged: listen("scale"),
      onFocusChanged: listen("focus"),
      isMinimized: () => new Promise<boolean>((resolve) => queries.minimized.push(resolve)),
      isVisible: () => new Promise<boolean>((resolve) => queries.visible.push(resolve))
    }
  };
}

it.each(["resized", "scale", "focus"] as const)(
  "F1-1 (round 5): a shell %s event hides the answer at once, before the window's state is known",
  async (event) => {
    vi.useFakeTimers();
    stampWrites();
    const fake = fakeShellWindow();
    shell.window = fake.window;
    render(<FeedbackScreen {...props()} />);
    await flush();
    expect(screen.getByText(KEY)).toBeTruthy();
    await act(async () => {
      fake.handlers[event]?.({ payload: event === "focus" ? false : {} });
    });
    // The state query is still unresolved: the answer is already gone.
    expect(screen.queryByText(KEY)).toBeNull();
    await advance(SECOND);
    expect(screen.queryByText(KEY)).toBeNull();
  }
);

it("F1-1 (round 5): the answer returns only after the window is known visible and unminimized, and a fresh row lands", async () => {
  vi.useFakeTimers();
  stampWrites();
  const fake = fakeShellWindow();
  shell.window = fake.window;
  render(<FeedbackScreen {...props()} />);
  await flush();
  await act(async () => {
    fake.handlers.resized?.({ payload: {} });
  });
  await advance(SECOND);
  // Minimized: stays hidden, nothing written.
  await act(async () => {
    fake.queries.minimized.forEach((resolve) => resolve(true));
    fake.queries.visible.forEach((resolve) => resolve(true));
  });
  await advance(SECOND);
  expect(screen.queryByText(KEY)).toBeNull();
  expect(displayIds()).toHaveLength(1);
  // Restored: visible and unminimized, then a fresh row.
  fake.queries.minimized.length = 0;
  fake.queries.visible.length = 0;
  await act(async () => {
    fake.handlers.resized?.({ payload: {} });
  });
  await advance(SECOND);
  const held = holdNextWrite();
  await act(async () => {
    fake.queries.minimized.forEach((resolve) => resolve(false));
    fake.queries.visible.forEach((resolve) => resolve(true));
  });
  await advance(SECOND);
  expect(screen.queryByText(KEY)).toBeNull();
  await act(async () => held.release());
  await flush();
  expect(screen.getByText(KEY)).toBeTruthy();
  expect(new Set(displayIds()).size).toBe(2);
});

// == Round 6 (docs/reviews/ux-phase4-feedback-codex-review.md §12) ==========================

/** Answer the shell's `index`-th state query (in the order they were asked). */
async function answerQuery(fake: ReturnType<typeof fakeShellWindow>, index: number, minimized: boolean, visible: boolean) {
  await act(async () => {
    fake.queries.minimized[index]?.(minimized);
    fake.queries.visible[index]?.(visible);
  });
  await flush();
}

const LATER_EVENTS: [string, (fake: ReturnType<typeof fakeShellWindow>) => void][] = [
  ["a shell focus change", (fake) => fake.handlers.focus?.({ payload: false })],
  ["a shell resize", (fake) => fake.handlers.resized?.({ payload: {} })],
  ["pagehide", () => window.dispatchEvent(new Event("pagehide"))],
  ["blur", () => window.dispatchEvent(new Event("blur"))],
  ["freeze", () => document.dispatchEvent(new Event("freeze"))]
];

it.each(LATER_EVENTS)(
  "F1-1 (round 6): a stale shell reply never releases the hold of a later event (%s)",
  async (_name, later) => {
    vi.useFakeTimers();
    stampWrites();
    const fake = fakeShellWindow();
    shell.window = fake.window;
    render(<FeedbackScreen {...props()} />);
    await flush();
    expect(screen.getByText(KEY)).toBeTruthy();
    const before = displayIds().length;
    // Resize A: hidden; after the settle, A's state query is in flight.
    await act(async () => {
      fake.handlers.resized?.({ payload: {} });
    });
    await advance(SECOND);
    expect(fake.queries.visible).toHaveLength(1);
    // Event B hides again while A's query is in flight.
    await act(async () => later(fake));
    // A's reply (visible, unminimized) arrives: it is stale and releases nothing.
    await answerQuery(fake, 0, false, true);
    await advance(10 * SECOND);
    expect(screen.queryByText(KEY)).toBeNull();
    expect(displayIds()).toHaveLength(before);
    // Only the latest query releases: B's, asked after its own settle.
    expect(fake.queries.visible).toHaveLength(2);
    await answerQuery(fake, 1, true, true);
    await advance(10 * SECOND);
    expect(screen.queryByText(KEY)).toBeNull();
    expect(displayIds()).toHaveLength(before);
  }
);

it("F1-1 (round 6): the latest query releases the hold, after a fresh row", async () => {
  vi.useFakeTimers();
  stampWrites();
  const fake = fakeShellWindow();
  shell.window = fake.window;
  render(<FeedbackScreen {...props()} />);
  await flush();
  const before = displayIds().length;
  await act(async () => {
    fake.handlers.resized?.({ payload: {} });
  });
  await advance(SECOND);
  await act(async () => {
    fake.handlers.focus?.({ payload: false });
  });
  await answerQuery(fake, 0, false, true);
  await advance(SECOND);
  expect(screen.queryByText(KEY)).toBeNull();
  await answerQuery(fake, 1, false, true);
  await advance(SECOND);
  expect(screen.getByText(KEY)).toBeTruthy();
  expect(displayIds().length).toBe(before + 1);
});

// Reader workbench RW2c (spec §5.10, G40): "compare methods ▸" after a correct
// Submit, only while workbench.compare_methods_enabled is on (the config's
// `compareMethods`); off, the feedback screen asks the server nothing.
it("RW2c off: a right answer with workbench help on but no compareMethods key asks for no comparison", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" }, workbench: { enabled: true, help: { enabled: true, bridge: true, symbolic: true } } });
  api.getFeedback.mockResolvedValue({ ...BUNDLE, rubricScore: 4, correctness: 1 });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("Right")).toBeTruthy();
  expect(api.workbenchCompareOffer).not.toHaveBeenCalled();
  expect(screen.queryByTestId("feedback-compare-methods")).toBeNull();
});

it("RW2c on: a right answer asks whether compare methods is offered, and shows it when it is", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" }, workbench: { enabled: true, help: { enabled: true, bridge: true, symbolic: true, compareMethods: true } } });
  api.getFeedback.mockResolvedValue({ ...BUNDLE, rubricScore: 4, correctness: 1 });
  api.workbenchCompareOffer.mockResolvedValue({ version: 1, available: true, reason: null, referenceKind: "item_key" });
  render(<FeedbackScreen {...props()} />);
  expect(await screen.findByText("compare methods ▸")).toBeTruthy();
  expect(api.workbenchCompareOffer).toHaveBeenCalledWith({ attemptId: BUNDLE.attemptId });
});
