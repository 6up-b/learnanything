// UX fix stage 3 (item 5; stage 1's UX-6 sweep): a note that can't be saved
// because its question has no subject says so where the note is written, in
// plain words, and keeps the words; it is not the shell's sticky red error.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, PracticeItemDetail } from "../api/dto";
import { clear } from "../api/queryCache";
import { setAlgoConfig } from "../app/algoConfig";
import { FeedbackScreen } from "./FeedbackScreen";
import { findJargon } from "../copy/denyList";

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
    recordAnswerDisplay: vi.fn(),
    addNote: vi.fn()
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

it("a question filed under no subject: the note panel says why the note can't be saved, and keeps it", async () => {
  api.getPracticeItem.mockResolvedValue({ ...ITEM, subject: null, subjects: [] });
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText(/You used the unconditional probability/);
  await press("j");
  const body = await screen.findByPlaceholderText(/write your note/);
  fireEvent.change(body, { target: { value: "Restrict to the condition first." } });
  await act(async () => {
    fireEvent.keyDown(body, { key: "Enter", ctrlKey: true });
  });
  const line = await screen.findByTestId("note-refusal");
  expect(line.getAttribute("role")).toBe("status");
  expect(line.textContent).toBe("This note can't be saved here: the question isn't filed under a subject yet. Your words are still here.");
  expect(findJargon(line.textContent ?? "")).toEqual([]);
  expect((body as HTMLTextAreaElement).value).toBe("Restrict to the condition first.");
  expect(callbacks.onError).not.toHaveBeenCalled();
  expect(api.addNote).not.toHaveBeenCalled();
});
