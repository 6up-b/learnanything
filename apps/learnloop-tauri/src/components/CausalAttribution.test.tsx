// The repair status panel's line for a withheld quick check (K9.2): only the learner's own "Not now"
// is told "You asked me"; a check withheld for recent burden or the session budget is not theirs.
import { act, cleanup, render, renderHook, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import type { CausalRepairStatusDto } from "../api/dto";
import {
  CausalRepairStatusPanel,
  ROUTER_DECISION_POLL_FIRST_MS,
  ROUTER_DECISION_POLL_TRIES,
  probeOfferCopy,
  useCausalRepairActions,
  useRouterDecisionPoll,
} from "./CausalAttribution";

vi.mock("../api/client", () => ({ api: {} }));

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

// The orchestrator's message for every withheld offer (causal_orchestrator.DEFERRED_OFFER_MESSAGE).
const DEFERRED_MESSAGE =
  "I'm holding this targeted repair because two explanations would need different help. I won't ask again right now.";

function withheld(reason: string): CausalRepairStatusDto {
  return {
    status: "needs_disambiguation",
    reason,
    message: DEFERRED_MESSAGE,
    misconceptionId: "mc_1",
    factorId: "factor_1",
    learningObjectId: "lo_1",
    attemptId: "att_1",
    probeOffered: false,
    probeDecision: reason,
    probeDecisionReason: null,
    decisionReceiptId: "receipt_1",
    candidateId: null,
    blindBundleIds: [],
    hypothesisSetId: null,
    repairClassIds: [],
    commonRepairClassId: null,
    pendingMachineCheckIds: [],
    learnerPreference: "none",
    actions: [{ id: "teach_me_now", label: "Teach me now" }],
    episode: null,
    parameters: {},
    evsiProvenance: {}
  };
}

describe("CausalRepairStatusPanel, a withheld quick check", () => {
  it("tells the learner they asked only after their own Not now", () => {
    render(<CausalRepairStatusPanel status={withheld("defer_learner_preference")} />);
    expect(screen.getByText(/You asked me not to check again for now/)).toBeTruthy();
    expect(screen.getByText(DEFERRED_MESSAGE)).toBeTruthy();
  });

  it.each(["defer_recent_burden", "defer_session_budget"])(
    "says nothing of the learner asking when it was withheld for %s",
    (reason) => {
      render(<CausalRepairStatusPanel status={withheld(reason)} />);
      expect(screen.queryByText(/You asked me/)).toBeNull();
      expect(screen.getByText(DEFERRED_MESSAGE)).toBeTruthy();
    }
  );
});

describe("the probe router's tag", () => {
  it("renders a status carrying the router's disposition as any other", () => {
    const status: CausalRepairStatusDto = {
      ...withheld("defer_learner_preference"),
      routerState: "unavailable",
      routerDecisionId: "decision_1",
      hardStopReasons: ["learner_preference"]
    };
    render(<CausalRepairStatusPanel status={status} />);
    expect(screen.getByText(/You asked me not to check again for now/)).toBeTruthy();
  });

  it("explains an offer refused for want of the router's selection, and one refused by the learner's Not now", () => {
    expect(probeOfferCopy("router_decision_required")).toMatch(/no quick check to take/);
    expect(probeOfferCopy("learner_preference")).toMatch(/You asked me not to check again/);
    expect(probeOfferCopy("something_else")).toBe("The quick check could not be started right now.");
  });
});

describe("the router's decision, made in its job (G2 review R19)", () => {
  const pending: CausalRepairStatusDto = {
    ...withheld("router_decision_pending"),
    routerState: "pending",
    routerDecisionId: null,
    hardStopReasons: []
  };

  it("reads a pending status again, backing off, until the router has decided", async () => {
    vi.useFakeTimers();
    const reread = vi.fn(async () => {});
    const { rerender } = renderHook(({ status }) => useRouterDecisionPoll(status, reread), {
      initialProps: { status: pending as CausalRepairStatusDto | null }
    });
    await act(async () => { vi.advanceTimersByTime(ROUTER_DECISION_POLL_FIRST_MS - 1); });
    expect(reread).not.toHaveBeenCalled();
    await act(async () => { vi.advanceTimersByTime(1); });
    expect(reread).toHaveBeenCalledTimes(1);
    // Still pending: the next read waits twice as long.
    rerender({ status: { ...pending } });
    await act(async () => { vi.advanceTimersByTime(2 * ROUTER_DECISION_POLL_FIRST_MS); });
    expect(reread).toHaveBeenCalledTimes(2);
    // Decided: no more reads.
    rerender({ status: { ...pending, routerState: "selected", routerDecisionId: "decision_1" } });
    await act(async () => { vi.advanceTimersByTime(60_000); });
    expect(reread).toHaveBeenCalledTimes(2);
  });

  it("stops after its tries", async () => {
    vi.useFakeTimers();
    const reread = vi.fn(async () => {});
    const { rerender } = renderHook(({ status }) => useRouterDecisionPoll(status, reread), {
      initialProps: { status: pending as CausalRepairStatusDto | null }
    });
    for (let i = 0; i < ROUTER_DECISION_POLL_TRIES + 3; i += 1) {
      await act(async () => { vi.advanceTimersByTime(ROUTER_DECISION_POLL_FIRST_MS * 2 ** i); });
      rerender({ status: { ...pending } });
    }
    expect(reread).toHaveBeenCalledTimes(ROUTER_DECISION_POLL_TRIES);
  });
});

describe("the shown factor's status (G2 review R12)", () => {
  it("re-reads the factor the status named after Not now, and Teach me now names it", async () => {
    const mocked = api as unknown as Record<string, ReturnType<typeof vi.fn>>;
    mocked.causalProbeDefer = vi.fn(async () => ({ version: 1, preference: {} }));
    mocked.causalRepairStatus = vi.fn(async () => ({ version: 1, repairStatus: pending() }));
    mocked.causalTeachMeNow = vi.fn(async () => ({ version: 1, repairStatus: pending() }));
    const onStatus = vi.fn();
    const { result } = renderHook(() => useCausalRepairActions({ sessionId: "sess", onStatus }));
    const status = { ...withheld("router_selected_probe"), factorId: "factor_2" };
    await act(async () => { result.current.runAction("not_now", status); });
    expect(mocked.causalRepairStatus).toHaveBeenCalledWith("mc_1", "sess", { factorId: "factor_2" });
    await act(async () => { result.current.runAction("teach_me_now", status); });
    expect(mocked.causalTeachMeNow).toHaveBeenCalledWith(
      expect.objectContaining({ factorId: "factor_2", misconceptionId: "mc_1" }));

    function pending(): CausalRepairStatusDto {
      return { ...status, routerState: "pending" };
    }
  });
});
