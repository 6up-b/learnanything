// G2-R26: Continue after a router-owned check's question opens the question the probe router chose. While the
// router's decision job has not run, the sidecar answers "pending" and the screen asks again (backing off) instead of
// opening another question; once its question stands, that question is opened; if it never decides, back to practice.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ProbeBlockEndDto } from "../api/dto";
import { setAlgoConfig } from "../app/algoConfig";
import { ROUTER_DECISION_POLL_FIRST_MS, ROUTER_DECISION_POLL_TRIES } from "../app/routerDecisionPoll";
import { DiagnosticReviewScreen } from "./DiagnosticReviewScreen";

const { api } = vi.hoisted(() => ({ api: { getNextProbeItem: vi.fn(), startGuidedRedo: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ ProbeRemintAction: () => null }));
vi.mock("../components/CausalAttribution", () => ({ CausalFeedbackPanel: () => <div>causal panel</div> }));

function props(): ComponentProps<typeof DiagnosticReviewScreen> {
  return {
    blockEnd: {
      episodeId: "ep_router",
      status: "in_progress",
      releasedFeedback: [
        { attemptId: "att_1", practiceItemId: "pi_first", rubricScore: 0, maxPoints: 4, feedbackMd: "Not yet.",
          fatalErrors: [], heldForReview: false },
      ],
      normalizedMisconceptionIds: [],
      openSet: null,
      completionReason: null,
      firstErrorStepOrClaim: null,
      route: "next_block",
      decision: null,
    } as unknown as ProbeBlockEndDto,
    learningObjectId: "lo_router",
    learningObjectTitle: "Singular values",
    sessionId: "s1",
    onContinueDiagnostic: vi.fn(),
    onAsk: vi.fn(),
    onOpenRepair: vi.fn(),
    onGuidedRedo: vi.fn(),
    onBack: vi.fn(),
    onError: vi.fn(),
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
  setAlgoConfig(undefined);
});

async function pressContinue() {
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
}

it("waits for the router's decision and then opens the question it chose", async () => {
  api.getNextProbeItem
    .mockResolvedValueOnce({ version: 1, active: false, routerState: "pending", practiceItemId: null })
    .mockResolvedValueOnce({ version: 1, active: true, routerState: "standing", practiceItemId: "pi_router_second",
                             presentationId: "pp_1" });
  const callbacks = props();
  render(<DiagnosticReviewScreen {...callbacks} />);
  await pressContinue();
  expect(api.getNextProbeItem).toHaveBeenCalledWith("lo_router", "ep_router");
  expect(callbacks.onContinueDiagnostic).not.toHaveBeenCalled();
  await act(async () => { await vi.advanceTimersByTimeAsync(ROUTER_DECISION_POLL_FIRST_MS); });
  expect(api.getNextProbeItem).toHaveBeenCalledTimes(2);
  expect(callbacks.onContinueDiagnostic).toHaveBeenCalledWith("pi_router_second");
  expect(callbacks.onBack).not.toHaveBeenCalled();
});

it("opens the router's standing question at once once it is chosen", async () => {
  api.getNextProbeItem.mockResolvedValue({ version: 1, active: true, routerState: "standing",
                                           practiceItemId: "pi_router_second", presentationId: "pp_1" });
  const callbacks = props();
  render(<DiagnosticReviewScreen {...callbacks} />);
  await pressContinue();
  expect(api.getNextProbeItem).toHaveBeenCalledTimes(1);
  expect(callbacks.onContinueDiagnostic).toHaveBeenCalledWith("pi_router_second");
});

it("never opens another question while the router has not decided, and goes back when it does not", async () => {
  api.getNextProbeItem.mockResolvedValue({ version: 1, active: false, routerState: "pending", practiceItemId: null });
  const callbacks = props();
  render(<DiagnosticReviewScreen {...callbacks} />);
  await pressContinue();
  for (let i = 0; i < ROUTER_DECISION_POLL_TRIES; i += 1) {
    await act(async () => { await vi.advanceTimersByTimeAsync(ROUTER_DECISION_POLL_FIRST_MS * 2 ** i); });
  }
  expect(api.getNextProbeItem).toHaveBeenCalledTimes(ROUTER_DECISION_POLL_TRIES + 1);
  expect(callbacks.onContinueDiagnostic).not.toHaveBeenCalled();
  expect(callbacks.onBack).toHaveBeenCalled();
});
