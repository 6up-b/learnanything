// Plain words on the Phase 4 surfaces (docs/specs/ux_learnloop_v1.md §9,
// Phase 7.2 started in Phase 1): the practice card, feedback, the short
// check's results, the repair step and the session finish, rendered with
// fixture data in the default (simple) presentation, must not show a term
// from the glossary's left column. Their behaviour has its own tests; here
// they meet the deny-list.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, ProbeBlockEndDto, SessionEndSummary } from "../api/dto";
import { setAlgoConfig } from "../app/algoConfig";
import { SessionFinishHud } from "../components/SessionFinishHud";
import { DiagnosticReviewScreen } from "../screens/DiagnosticReviewScreen";
import { FeedbackScreen } from "../screens/FeedbackScreen";
import { PracticeScreen } from "../screens/PracticeScreen";
import { RepairScreen } from "../screens/RepairScreen";
import { findJargon } from "./denyList";

const { api } = vi.hoisted(() => {
  const known: Record<string, ReturnType<typeof vi.fn>> = {};
  const api = new Proxy(known, {
    get(target, prop: string) {
      if (!(prop in target)) target[prop] = vi.fn(() => Promise.reject(new Error(`${prop} not mocked`)));
      return target[prop];
    }
  });
  return { api };
});
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({ MathLiveEditor: () => <textarea aria-label="answer" /> }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/OpenInSource", () => ({ OpenInSource: () => null }));

const ITEM = {
  id: "pi_1", learningObjectId: "lo_1", learningObjectTitle: "Conditional probability", subject: "probability",
  subjects: ["probability"], practiceMode: "constructed_response", attemptTypesAllowed: [],
  presentation: { practiceItemId: "pi_1", blocks: [
    { kind: "prompt", markdown: "Given that the sum is 8, what is P(first = 3)?", label: null },
    { kind: "required_method_instruction", markdown: "Use counting in your answer.", label: null }
  ] },
  prompt: "Given that the sum is 8, what is P(first = 3)?", expectedAnswer: "Five outcomes; one has first = 3: 1/5.",
  hints: ["Which outcomes have sum 8?"], hintPolicy: { maxUsefulHints: 1 }, candidateErrorTypes: [], tags: [],
  sourceRefs: [], attempts: [], evidenceFacets: ["facet_conditional"], evidenceWeights: {},
  rubric: { maxPoints: 4, criteria: [{ id: "setup", description: "Sets up the conditional", points: 4 }], fatalErrors: [] },
  mastery: { mean: 0.4, variance: 0.1 }, elicitation: null, activeFollowupKind: "cold_retry"
};

const BUNDLE = {
  version: 1, attemptId: "att_1", practiceItemId: "pi_1", learningObjectId: "lo_1",
  learningObjectTitle: "Conditional probability", rubricScore: 2, maxPoints: 4, correctness: 0.5,
  graderConfidence: 0.8, gradingSource: "codex", fallbackReason: null, manualReviewReason: "provisional_pending_clarification",
  fsrsRating: "hard", nextDueAt: "2026-10-20T00:00:00Z",
  criterionEvidence: [
    { criterionId: "setup", criterionDescription: "Sets up the conditional", pointsAwarded: 2, pointsPossible: 2, evidence: null, notes: null, graderTier: 2 },
    { criterionId: "restrict", criterionDescription: "Keeps only the outcomes with sum 8", pointsAwarded: 0, pointsPossible: 2, evidence: null, notes: null, graderTier: 2, assessed: false }
  ],
  fatalErrors: [], errorAttributions: [],
  surprise: { predictiveSurprise: 1, bayesianSurprise: 1, surpriseDirection: "negative", fsrsIntervalFactor: 0.8, followupThresholdNats: 0.5, triggeredActions: [], suppressedActions: [], gateDiagnostics: null },
  masteryBefore: { mean: 0.5, variance: 0.1 }, masteryAfter: { mean: 0.4, variance: 0.1 }, masteryStep: null,
  feedbackMd: "You used the unconditional probability.", repairSuggestions: [], guidedRedoAvailable: true,
  interventionNeed: null, primed: false, autoPrimed: true, sourceRefs: [], followupQueued: true,
  heldForReview: false, learnerAnswerMd: "1/6", learnerExplanationMd: "each roll is fair", answeredPresentation: null,
  matchedMisconception: {
    id: "mis_1", statement: "Treats P(A|B) as P(A)", correctionStatement: "Conditioning shrinks the outcomes to five.",
    mechanism: "drops the condition", targetFacet: "facet_conditional", confusedWithFacet: "facet_unconditional", status: "active"
  },
  coldCheckResult: { passed: true, outcome: "cold_success", claim: "repair_confirmed", claimDowngradedReason: null, caseKind: null,
    caseRef: null, caseSummary: "conditioning", factorId: null, episodeId: null, instructedAt: "2026-10-12T00:00:00Z", checkedAt: null }
} as unknown as FeedbackBundle;

const BLOCK_END = {
  episodeId: "ep_1", status: "converted_to_tutoring",
  releasedFeedback: [
    { attemptId: "att_1", practiceItemId: "pi_1", rubricScore: 4, maxPoints: 4, feedbackMd: "Clean.", fatalErrors: [], heldForReview: false },
    { attemptId: "att_2", practiceItemId: "pi_2", rubricScore: 0, maxPoints: 4, feedbackMd: null, fatalErrors: [], heldForReview: true }
  ],
  normalizedMisconceptionIds: ["mis_1"], openSet: null, completionReason: "probe_budget", firstErrorStepOrClaim: null,
  route: "tutoring", decision: null
} as unknown as ProbeBlockEndDto;

function expectPlain() {
  expect(findJargon(document.body.textContent ?? "")).toEqual([]);
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" }, practice: { stuckPrompt: true } });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.getPracticeItem.mockResolvedValue(ITEM);
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.getFeedback.mockResolvedValue(BUNDLE);
  api.getAttemptTrace.mockRejectedValue(new Error("none"));
  api.getAttemptTraceEvidence.mockRejectedValue(new Error("none"));
  api.getGradingClarification.mockResolvedValue({ clarification: null });
  api.diagnosisStatus.mockResolvedValue({ version: 1, attemptId: "att_1", status: "pending", cardEnabled: true, responses: [] });
  api.startRemediation.mockResolvedValue({ version: 1, episode: { id: "ep_1", passagesShown: [] }, case: {
    id: "mis_1", statement: "Treats P(A|B) as P(A)", correctionStatement: "Conditioning shrinks the outcomes.",
    mechanism: "drops the condition", targetFacet: "facet_conditional", confusedWithFacet: "facet_unconditional",
    status: "returned", history: [{ id: "h1", label: "returned", at: "2026-10-12T00:00:00Z" }]
  } });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("the practice card, its stuck prompt and its self-grade", async () => {
  render(
    <PracticeScreen session={{ sessionId: "s1" } as never} practiceItemId="pi_1" gradingReady={false} gradingProvider="codex"
      onFeedback={vi.fn()} onBlockEnd={vi.fn()} onContinueDiagnostic={vi.fn()} onBack={vi.fn()} onCheckpointCleared={vi.fn()}
      onDraftSaved={vi.fn()} onTeachBackActive={vi.fn()} onAskAvailabilityChange={vi.fn()} onInspect={vi.fn()} onAsk={vi.fn()}
      onError={vi.fn()} />
  );
  await screen.findByText("Given that the sum is 8, what is P(first = 3)?");
  expectPlain();
  fireEvent.click(screen.getByRole("button", { name: /I'm stuck/ }));
  expectPlain();
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await screen.findByRole("button", { name: "Got it" });
  fireEvent.click(screen.getByRole("button", { name: "Partly" }));
  expectPlain();
});

it("feedback, its contest box and its why", async () => {
  render(
    <FeedbackScreen attemptId="att_1" sessionId="s1" onNext={vi.fn()} onBack={vi.fn()} onOpenNotes={vi.fn()}
      onPrimedRetry={vi.fn()} onGuidedRedo={vi.fn()} onOpenRepair={vi.fn()} onInspect={vi.fn()} onAsk={vi.fn()} onError={vi.fn()} />
  );
  await screen.findByText("Partly right");
  expectPlain();
  fireEvent.click(screen.getByRole("button", { name: /I think I was right/ }));
  fireEvent.click(screen.getByRole("button", { name: /why\?/ }));
  expectPlain();
});

it("the short check's results", () => {
  render(
    <DiagnosticReviewScreen blockEnd={BLOCK_END} learningObjectId="lo_1" learningObjectTitle="Conditional probability"
      sessionId="s1" onContinueDiagnostic={vi.fn()} onAsk={vi.fn()} onBack={vi.fn()} onError={vi.fn()} />
  );
  expectPlain();
});

it("the repair step", async () => {
  render(<RepairScreen misconceptionId="mis_1" onClose={vi.fn()} onPractice={vi.fn()} onError={vi.fn()} />);
  await screen.findByText("Fix this mix-up · about 4 min");
  await screen.findByText(/Conditioning shrinks the outcomes/);
  expectPlain();
});

it("the session finish", async () => {
  const summary = {
    version: 1, sessionId: "s1", startedAt: "2026-10-15T10:00:00Z", endedAt: "2026-10-15T10:20:00Z",
    attemptsRecorded: 3, itemsReviewed: 1, followupsQueued: 1, streak: { current: 2, longest: 2, activeToday: true },
    facetsDemonstrated: 2, predictionsMoved: { up: 1, down: 0 }, corrections: 1, misconceptionsTouched: { resolved: 1, returned: 0 },
    coldChecksCompleted: 1, coldChecksPassed: 1,
    topics: [{ learningObjectId: "lo_1", title: "Conditional probability", evidence: "on_your_own" }]
  } as unknown as SessionEndSummary;
  await act(async () => {
    render(<SessionFinishHud summary={summary} onDismiss={vi.fn()} />);
  });
  expectPlain();
});
