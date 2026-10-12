import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, QueueInput, QueueSnapshot, ScheduledItemDto } from "../api/dto";
import { clear, invalidate } from "../api/queryCache";
import { TAG } from "../api/queryTags";
import { FeedbackScreen } from "./FeedbackScreen";

// Every api method this screen does not exercise here resolves to nothing it
// can render; the ones under test are plain mocks.
const { api } = vi.hoisted(() => {
  const known: Record<string, ReturnType<typeof vi.fn>> = {
    getFeedback: vi.fn(),
    getTodayQueue: vi.fn(),
    getPracticeItem: vi.fn(),
    getAttemptTrace: vi.fn(),
    getAttemptTraceEvidence: vi.fn(),
    getGradingClarification: vi.fn()
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
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("../components/ClaimSurface", () => ({ ClaimSurface: () => null, mintVisitId: () => "visit" }));
vi.mock("../components/KnowledgeModel", () => ({ AttemptTraceView: () => null, UnresolvedCauseCard: () => null }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/RepairTrace", () => ({ RepairTraceBlocks: () => null }));
vi.mock("../components/RepairAffordances", () => ({ CommonRepairCard: () => null, GuidedRedoAffordance: () => null }));

const FEEDBACK = {
  version: 1,
  attemptId: "att_1",
  practiceItemId: "pi_answered",
  learningObjectId: "lo_eigen",
  learningObjectTitle: "Eigenvalues",
  rubricScore: 3,
  maxPoints: 4,
  correctness: 0.75,
  graderConfidence: 0.9,
  gradingSource: "manual",
  fallbackReason: null,
  manualReviewReason: null,
  fsrsRating: "good",
  nextDueAt: "2026-10-20T00:00:00Z",
  criterionEvidence: [],
  fatalErrors: [],
  errorAttributions: [],
  surprise: {
    predictiveSurprise: null,
    bayesianSurprise: null,
    surpriseDirection: null,
    fsrsIntervalFactor: null,
    followupThresholdNats: null,
    triggeredActions: [],
    suppressedActions: [],
    gateDiagnostics: null
  },
  masteryBefore: null,
  masteryAfter: null,
  masteryStep: null,
  feedbackMd: null,
  repairSuggestions: [],
  guidedRedoAvailable: false,
  interventionNeed: null,
  primed: false,
  sourceRefs: [],
  followupQueued: false
} as unknown as FeedbackBundle;

const NEXT_QUEUE: QueueInput = { sessionId: "s1", availableMinutes: 25, energy: null };

function item(practiceItemId: string, schedulerCandidateId: string, learningObjectTitle: string): ScheduledItemDto {
  return { practiceItemId, schedulerCandidateId, learningObjectTitle } as unknown as ScheduledItemDto;
}

function queue(...sections: ScheduledItemDto[][]): QueueSnapshot {
  return {
    version: 1,
    generatedAt: "2026-10-12T12:00:00Z",
    sessionId: "s1",
    sections: sections.map((items, i) => ({ title: `section ${i}`, items })),
    totalItems: sections.flat().length
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function props(overrides: Partial<ComponentProps<typeof FeedbackScreen>> = {}): ComponentProps<typeof FeedbackScreen> {
  return {
    attemptId: "att_1",
    sessionId: "s1",
    nextQueue: NEXT_QUEUE,
    onOpenNext: vi.fn(),
    onNext: vi.fn(),
    onBack: vi.fn(),
    onOpenNotes: vi.fn(),
    onPrimedRetry: vi.fn(),
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

beforeEach(() => {
  api.getFeedback.mockResolvedValue(FEEDBACK);
  api.getPracticeItem.mockReturnValue(new Promise(() => undefined));
  api.getAttemptTrace.mockRejectedValue(new Error("no trace"));
  api.getAttemptTraceEvidence.mockRejectedValue(new Error("no evidence"));
  api.getGradingClarification.mockRejectedValue(new Error("no clarification"));
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

// Daily-loop P2 (spec §6.5): Next on feedback opens the next item directly.
it("opens the head of the live queue on Next, with the candidate of the slate that ranked it", async () => {
  api.getTodayQueue.mockResolvedValue(
    queue([], [item("pi_head", "cand_head", "Bayes' rule"), item("pi_second", "cand_2", "Priors")], [item("pi_later", "cand_3", "Later")])
  );
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("Eigenvalues");
  await waitFor(() => expect(api.getTodayQueue).toHaveBeenCalledWith(NEXT_QUEUE));
  // The key bar names what Next will open.
  expect(await screen.findByText("next: Bayes' rule")).toBeTruthy();

  await press("n");
  expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_head", "cand_head");
  expect(callbacks.onNext).not.toHaveBeenCalled();
  expect(callbacks.onBack).not.toHaveBeenCalled();
});

it("advances on Enter as well as n", async () => {
  api.getTodayQueue.mockResolvedValue(queue([item("pi_head", "cand_head", "Bayes' rule")]));
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("next: Bayes' rule");
  await press("Enter");
  expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_head", "cand_head");
});

it("keeps the list one key away: Esc and b open it, never the next item", async () => {
  api.getTodayQueue.mockResolvedValue(queue([item("pi_head", "cand_head", "Bayes' rule")]));
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("next: Bayes' rule");
  await press("Escape");
  await press("b");
  expect(callbacks.onBack).toHaveBeenCalledTimes(2);
  expect(callbacks.onOpenNext).not.toHaveBeenCalled();
  expect(callbacks.onNext).not.toHaveBeenCalled();
});

it("reads the queue only once feedback is on screen", async () => {
  const bundle = deferred<FeedbackBundle>();
  api.getFeedback.mockReturnValue(bundle.promise);
  api.getTodayQueue.mockResolvedValue(queue([item("pi_head", "cand_head", "Bayes' rule")]));
  render(<FeedbackScreen {...props()} />);
  await act(async () => { await Promise.resolve(); });
  expect(api.getTodayQueue).not.toHaveBeenCalled();
  await act(async () => bundle.resolve(FEEDBACK));
  await waitFor(() => expect(api.getTodayQueue).toHaveBeenCalledOnce());
});

it("never opens a head the queue had before an invalidation: it waits for the rebuilt queue", async () => {
  api.getTodayQueue
    .mockResolvedValueOnce(queue([item("pi_stale", "cand_stale", "Stale")]))
    .mockResolvedValueOnce(queue([item("pi_fresh", "cand_fresh", "Fresh")]));
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("next: Stale");
  // A regrade or forced follow-up on this screen invalidates the queue.
  await act(async () => invalidate({ tags: [TAG.queue] }));
  await press("n");
  await waitFor(() => expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_fresh", "cand_fresh"));
  expect(callbacks.onOpenNext).toHaveBeenCalledOnce();
});

it("never opens a head from a queue invalidated while it was being read", async () => {
  const prefetch = deferred<QueueSnapshot>();
  api.getTodayQueue
    .mockReturnValueOnce(prefetch.promise)
    .mockResolvedValue(queue([item("pi_fresh", "cand_fresh", "Fresh")]));
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await waitFor(() => expect(api.getTodayQueue).toHaveBeenCalledOnce());
  // The invalidation lands while the prefetch is still in flight, and Next is
  // pressed before its (now stale) response arrives.
  await act(async () => invalidate({ tags: [TAG.queue] }));
  await press("n");
  expect(screen.getByText("opening next…")).toBeTruthy();
  await act(async () => prefetch.resolve(queue([item("pi_stale", "cand_stale", "Stale")])));
  await waitFor(() => expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_fresh", "cand_fresh"));
  expect(callbacks.onOpenNext).toHaveBeenCalledOnce();
  expect(callbacks.onOpenNext).not.toHaveBeenCalledWith("pi_stale", "cand_stale");
  expect(api.getTodayQueue).toHaveBeenCalledTimes(2);
});

it("falls back to the list when the queue is empty or cannot be read", async () => {
  api.getTodayQueue.mockResolvedValue(queue([]));
  const empty = props();
  render(<FeedbackScreen {...empty} />);
  expect(await screen.findByText("list (queue empty)")).toBeTruthy();
  await press("n");
  expect(empty.onNext).toHaveBeenCalledOnce();
  expect(empty.onOpenNext).not.toHaveBeenCalled();
  cleanup();
  clear();

  api.getTodayQueue.mockRejectedValue(new Error("sidecar down"));
  const failing = props();
  render(<FeedbackScreen {...failing} />);
  await screen.findByText("Eigenvalues");
  await press("n");
  await waitFor(() => expect(failing.onNext).toHaveBeenCalledOnce());
  expect(failing.onOpenNext).not.toHaveBeenCalled();
});

it("drops a pending advance when the learner goes back to the list first", async () => {
  const slow = deferred<QueueSnapshot>();
  api.getTodayQueue.mockReturnValue(slow.promise);
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("Eigenvalues");
  await press("n");
  expect(await screen.findByText("opening next…")).toBeTruthy();
  await press("b");
  await act(async () => slow.resolve(queue([item("pi_head", "cand_head", "Bayes' rule")])));
  expect(callbacks.onBack).toHaveBeenCalledOnce();
  expect(callbacks.onOpenNext).not.toHaveBeenCalled();
  expect(callbacks.onNext).not.toHaveBeenCalled();
});

it("keeps the old Next where no live queue applies (no session, or a calibration round)", async () => {
  const callbacks = props({ nextQueue: null });
  render(<FeedbackScreen {...callbacks} />);
  await screen.findByText("Eigenvalues");
  expect(screen.getByText("continue")).toBeTruthy();
  await press("n");
  expect(callbacks.onNext).toHaveBeenCalledOnce();
  expect(api.getTodayQueue).not.toHaveBeenCalled();
});
