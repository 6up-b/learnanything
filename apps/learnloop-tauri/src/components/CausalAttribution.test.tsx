// The repair status panel's line for a withheld quick check (K9.2): only the learner's own "Not now"
// is told "You asked me"; a check withheld for recent burden or the session budget is not theirs.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CausalRepairStatusDto } from "../api/dto";
import { CausalRepairStatusPanel, probeOfferCopy } from "./CausalAttribution";

vi.mock("../api/client", () => ({ api: {} }));

afterEach(cleanup);

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
