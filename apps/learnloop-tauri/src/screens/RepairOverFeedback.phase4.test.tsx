// UX Phase 4, Codex review F2: App keeps feedback (or the short check's
// results) mounted under the repair step's overlay. One key must do one
// thing: ↵ takes the step's primary action and never also advances the screen
// underneath (to the queue head, the plan or the book), Esc closes only the
// overlay, and none of the underlying shortcuts run while it is open.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, PracticeItemDetail, ProbeBlockEndDto } from "../api/dto";
import { clear } from "../api/queryCache";
import { setAlgoConfig } from "../app/algoConfig";
import { DiagnosticReviewScreen } from "./DiagnosticReviewScreen";
import { FeedbackScreen } from "./FeedbackScreen";
import { RepairScreen } from "./RepairScreen";

const { api } = vi.hoisted(() => {
  const known: Record<string, ReturnType<typeof vi.fn>> = {
    getFeedback: vi.fn(),
    getPracticeItem: vi.fn(),
    getAttemptTrace: vi.fn(),
    getAttemptTraceEvidence: vi.fn(),
    getGradingClarification: vi.fn(),
    getTodayQueue: vi.fn(),
    recordAnswerDisplay: vi.fn(),
    startRemediation: vi.fn(),
    prescribeRemediation: vi.fn(),
    startRemediationTreatment: vi.fn(),
    getNextProbeItem: vi.fn()
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
vi.mock("../components/ClaimSurface", () => ({ ClaimSurface: () => null, mintVisitId: () => "visit" }));
vi.mock("../components/KnowledgeModel", () => ({ AttemptTraceView: () => null, UnresolvedCauseCard: () => null }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/RepairTrace", () => ({ RepairTraceBlocks: () => null }));
vi.mock("../components/OpenInSource", () => ({ OpenInSource: () => null }));

const BUNDLE = {
  version: 1,
  attemptId: "att_1",
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
  criterionEvidence: [],
  fatalErrors: [],
  errorAttributions: [],
  surprise: {
    predictiveSurprise: null, bayesianSurprise: null, surpriseDirection: null, fsrsIntervalFactor: null,
    followupThresholdNats: null, triggeredActions: [], suppressedActions: [], gateDiagnostics: null
  },
  masteryBefore: null,
  masteryAfter: null,
  masteryStep: null,
  feedbackMd: "You used the unconditional probability.",
  repairSuggestions: [],
  guidedRedoAvailable: false,
  interventionNeed: null,
  primed: false,
  sourceRefs: [],
  followupQueued: false,
  heldForReview: false,
  learnerAnswerMd: "1/6",
  learnerExplanationMd: null,
  answeredPresentation: null,
  matchedMisconception: {
    id: "mis_1", statement: "Treats P(A|B) as P(A)", correctionStatement: "Conditioning shrinks the outcomes.",
    mechanism: null, targetFacet: null, confusedWithFacet: null, status: "active"
  }
} as unknown as FeedbackBundle;

const ITEM = {
  id: "pi_cond_001", learningObjectId: "lo_conditional", learningObjectTitle: "Conditional probability",
  subject: "probability", subjects: ["probability"], practiceMode: "constructed_response", attemptTypesAllowed: [],
  presentation: { practiceItemId: "pi_cond_001", blocks: [{ kind: "prompt", markdown: "P(first = 3 | sum = 8)?", label: null }] },
  prompt: "P(first = 3 | sum = 8)?", expectedAnswer: "1/5", hints: [], rubric: null, candidateErrorTypes: [], sourceRefs: []
} as unknown as PracticeItemDetail;

const CASE = {
  id: "mis_1", statement: "Treats P(A|B) as P(A)", correctionStatement: "Conditioning shrinks the outcomes.",
  mechanism: null, targetFacet: "facet_a", confusedWithFacet: "facet_b", status: "active", history: []
};
const EPISODE = { id: "ep_1", passagesShown: [], primedItemId: null, coldItemId: null };

function feedbackProps(overrides: Partial<ComponentProps<typeof FeedbackScreen>> = {}): ComponentProps<typeof FeedbackScreen> {
  return {
    attemptId: "att_1",
    sessionId: "s1",
    // Next opens the live queue's head once the queue read resolves (async).
    nextQueue: { sessionId: "s1", availableMinutes: 25, energy: null },
    onOpenNext: vi.fn(),
    onNext: vi.fn(),
    onBack: vi.fn(),
    onOpenNotes: vi.fn(),
    onPrimedRetry: vi.fn(),
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

/** Let every pending promise (the queue read, the repair calls) settle. */
async function settle() {
  for (let tick = 0; tick < 5; tick += 1) {
    await act(async () => {
      await new Promise((done) => setTimeout(done, 0));
    });
  }
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  api.getFeedback.mockResolvedValue(BUNDLE);
  api.getPracticeItem.mockResolvedValue(ITEM);
  api.getAttemptTrace.mockRejectedValue(new Error("no trace"));
  api.getAttemptTraceEvidence.mockRejectedValue(new Error("no evidence"));
  api.getGradingClarification.mockResolvedValue({ clarification: null });
  api.recordAnswerDisplay.mockResolvedValue({ version: 1, recorded: true });
  api.getTodayQueue.mockResolvedValue({
    version: 1, generatedAt: "2026-10-15T00:00:00Z", sessionId: "s1", totalItems: 1,
    sections: [{ title: "due", items: [{ practiceItemId: "pi_next", schedulerCandidateId: "cand_next", learningObjectTitle: "Next" }] }]
  });
  api.startRemediation.mockResolvedValue({ version: 1, episode: EPISODE, case: CASE });
  api.prescribeRemediation.mockResolvedValue({ version: 1, episode: { ...EPISODE, passagesShown: [] }, case: CASE });
  api.startRemediationTreatment.mockResolvedValue({
    version: 1, episode: { ...EPISODE, primedItemId: "pi_related" }, case: CASE, primedItemId: "pi_related", coldItemId: null
  });
});
afterEach(() => {
  cleanup();
  clear();
  vi.clearAllMocks();
  setAlgoConfig(undefined);
});

it.each([
  ["App suspends feedback's keys while the step is open", true],
  ["the step's own keys never reach feedback", false]
])("one Enter over feedback runs the repair step only (%s)", async (_label, suspended) => {
  const feedback = feedbackProps({ keysSuspended: suspended });
  const onClose = vi.fn();
  render(
    <>
      <FeedbackScreen {...feedback} />
      <RepairScreen misconceptionId="mis_1" sessionId="s1" onClose={onClose} onPractice={vi.fn()} onError={vi.fn()} />
    </>
  );
  await screen.findByText("Partly right");
  await screen.findByRole("button", { name: /Read both passages/ });
  await settle();

  await press("Enter");
  await settle();

  expect(api.prescribeRemediation).toHaveBeenCalledOnce();
  expect(feedback.onOpenNext).not.toHaveBeenCalled();
  expect(feedback.onNext).not.toHaveBeenCalled();

  await press("Escape");
  await settle();
  expect(onClose).toHaveBeenCalledOnce();
  expect(feedback.onBack).not.toHaveBeenCalled();
});

it("none of feedback's shortcuts run under the step", async () => {
  const feedback = feedbackProps({ keysSuspended: true });
  render(
    <>
      <FeedbackScreen {...feedback} />
      <RepairScreen misconceptionId="mis_1" sessionId="s1" onClose={vi.fn()} onPractice={vi.fn()} onError={vi.fn()} />
    </>
  );
  await screen.findByText("Partly right");
  await settle();
  for (const key of ["n", "b", "r", "."]) await press(key);
  await settle();
  expect(feedback.onOpenNext).not.toHaveBeenCalled();
  expect(feedback.onNext).not.toHaveBeenCalled();
  expect(feedback.onBack).not.toHaveBeenCalled();
  expect(screen.queryByRole("textbox", { name: /why you think you were right/i })).toBeNull();
  expect(screen.queryByTestId("feedback-details")).toBeNull();
});

it("with the step closed, Enter advances feedback once the queue resolves", async () => {
  const feedback = feedbackProps();
  render(<FeedbackScreen {...feedback} />);
  await screen.findByText("Partly right");
  await settle();
  await press("Enter");
  await waitFor(() => expect(feedback.onOpenNext).toHaveBeenCalledWith("pi_next", "cand_next"));
});

it("the short check's results stay put under the step: ↵ and Esc are the step's", async () => {
  const blockEnd = {
    route: "ordinary_practice",
    releasedFeedback: [{ attemptId: "att_1", practiceItemId: "pi_cond_001", rubricScore: 2, maxPoints: 4, feedbackMd: null }],
    normalizedMisconceptionIds: [],
    openSet: null
  } as unknown as ProbeBlockEndDto;
  const onBack = vi.fn();
  const onClose = vi.fn();
  render(
    <>
      <DiagnosticReviewScreen
        blockEnd={blockEnd}
        learningObjectId="lo_conditional"
        learningObjectTitle="Conditional probability"
        sessionId="s1"
        onContinueDiagnostic={vi.fn()}
        onAsk={vi.fn()}
        onOpenRepair={vi.fn()}
        onBack={onBack}
        onError={vi.fn()}
        keysSuspended
      />
      <RepairScreen misconceptionId="mis_1" sessionId="s1" onClose={onClose} onPractice={vi.fn()} onError={vi.fn()} />
    </>
  );
  await screen.findByRole("button", { name: /Read both passages/ });
  await settle();
  await press("Enter");
  await settle();
  expect(api.prescribeRemediation).toHaveBeenCalledOnce();
  expect(api.getNextProbeItem).not.toHaveBeenCalled();
  await press("Escape");
  await settle();
  expect(onClose).toHaveBeenCalledOnce();
  expect(onBack).not.toHaveBeenCalled();
});
