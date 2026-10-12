// Daily-loop P2 auto-advance after a write made on the feedback screen itself,
// through the real client wrapper and query cache: only the Tauri transport is
// faked, so the test sees exactly the invalidations the wrappers perform.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, QueueInput, QueueSnapshot, ScheduledItemDto } from "../api/dto";
import { clear } from "../api/queryCache";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("../components/ClaimSurface", () => ({ ClaimSurface: () => null, mintVisitId: () => "visit" }));
vi.mock("../components/KnowledgeModel", () => ({ AttemptTraceView: () => null, UnresolvedCauseCard: () => null }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/RepairTrace", () => ({ RepairTraceBlocks: () => null }));
vi.mock("../components/RepairAffordances", () => ({ CommonRepairCard: () => null, GuidedRedoAffordance: () => null }));

import { FeedbackScreen } from "./FeedbackScreen";

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

function queueWith(practiceItemId: string, title: string): QueueSnapshot {
  const item = { practiceItemId, schedulerCandidateId: `cand_${practiceItemId}`, learningObjectTitle: title };
  return {
    version: 1,
    generatedAt: "2026-10-12T12:00:00Z",
    sessionId: "s1",
    sections: [{ title: "due", items: [item as unknown as ScheduledItemDto] }],
    totalItems: 1
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function props(): ComponentProps<typeof FeedbackScreen> {
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
    onError: vi.fn()
  };
}

async function press(key: string) {
  await act(async () => {
    fireEvent.keyDown(window, { key });
  });
}

/** The fake sidecar: the queue head is server state a forced follow-up changes. */
let serverHead: { id: string; title: string };
let followup: ReturnType<typeof deferred<void>> | null;
let queueReads: number;
beforeEach(() => {
  serverHead = { id: "pi_before", title: "Before the follow-up" };
  followup = null;
  queueReads = 0;
  invoke.mockImplementation(async (command: string) => {
    switch (command) {
      case "get_feedback":
        return FEEDBACK;
      case "get_today_queue":
        queueReads += 1;
        return queueWith(serverHead.id, serverHead.title);
      case "trigger_followup":
        if (followup) await followup.promise;
        serverHead = { id: "pi_followup", title: "Diagnostic follow-up" };
        return { ...FEEDBACK, followupQueued: true };
      case "get_practice_item":
        return new Promise(() => undefined);
      default:
        throw new Error(`${command} not faked`);
    }
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

it("opens the forced follow-up after Shift+D, not the head the queue had before it", async () => {
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  expect(await screen.findByText("next: Before the follow-up")).toBeTruthy();

  await press("D");
  await waitFor(() => expect(screen.getByText("force follow-up")).toBeTruthy());
  await press("n");

  await waitFor(() => expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_followup", "cand_pi_followup"));
  expect(callbacks.onOpenNext).toHaveBeenCalledOnce();
  expect(queueReads).toBeGreaterThanOrEqual(2);
});

it("waits for a forced follow-up still in flight before opening the next item", async () => {
  const callbacks = props();
  render(<FeedbackScreen {...callbacks} />);
  expect(await screen.findByText("next: Before the follow-up")).toBeTruthy();

  followup = deferred<void>();
  await press("D");
  expect(screen.getByText("triggering…")).toBeTruthy();
  await press("n");
  expect(callbacks.onOpenNext).not.toHaveBeenCalled();

  await act(async () => followup!.resolve());
  await waitFor(() => expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_followup", "cand_pi_followup"));
  expect(callbacks.onOpenNext).toHaveBeenCalledOnce();
});
