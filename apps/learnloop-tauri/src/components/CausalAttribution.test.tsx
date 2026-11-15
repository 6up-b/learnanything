// The repair status panel's line for a withheld quick check (K9.2): only the learner's own "Not now"
// is told "You asked me"; a check withheld for recent burden or the session budget is not theirs.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CausalRepairStatusDto } from "../api/dto";
import { CausalRepairStatusPanel } from "./CausalAttribution";

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
