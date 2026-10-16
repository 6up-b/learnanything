// UX Phase 4.3 (docs/specs/ux_learnloop_v1.md §7.5, "Diagnostic set
// results"): the short check's results fold into the feedback flow. One line
// on top, a verdict per question, and one next step on ↵. Raw status,
// "Feedback withheld… released now" and "observation N" go; a held grade
// shows "held for review", never a score. `[ui] practice_feedback =
// "classic"` restores the screen exactly.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ProbeBlockEndDto } from "../api/dto";
import { setAlgoConfig } from "../app/algoConfig";
import { DiagnosticReviewScreen } from "./DiagnosticReviewScreen";

const { api } = vi.hoisted(() => ({ api: { getNextProbeItem: vi.fn(), startGuidedRedo: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ ProbeRemintAction: () => null }));
vi.mock("../components/CausalAttribution", () => ({ CausalFeedbackPanel: () => <div>causal panel</div> }));

function blockEnd(overrides: Partial<ProbeBlockEndDto> = {}): ProbeBlockEndDto {
  return {
    episodeId: "ep_1",
    status: "converted_to_tutoring",
    releasedFeedback: [
      { attemptId: "att_1", practiceItemId: "pi_1", rubricScore: 4, maxPoints: 4, feedbackMd: "Clean setup.", fatalErrors: [], heldForReview: false },
      { attemptId: "att_2", practiceItemId: "pi_2", rubricScore: 1, maxPoints: 4, feedbackMd: "The condition was dropped.", fatalErrors: [], heldForReview: false },
      { attemptId: "att_3", practiceItemId: "pi_3", rubricScore: 0, maxPoints: 4, feedbackMd: null, fatalErrors: [], heldForReview: true }
    ],
    normalizedMisconceptionIds: [],
    openSet: null,
    completionReason: "value_of_information_exhausted",
    firstErrorStepOrClaim: null,
    route: "ordinary_practice",
    decision: null,
    ...overrides
  } as ProbeBlockEndDto;
}

function props(overrides: Partial<ComponentProps<typeof DiagnosticReviewScreen>> = {}): ComponentProps<typeof DiagnosticReviewScreen> {
  return {
    blockEnd: blockEnd(),
    learningObjectId: "lo_cond",
    learningObjectTitle: "Conditional probability",
    sessionId: "s1",
    onContinueDiagnostic: vi.fn(),
    onAsk: vi.fn(),
    onOpenRepair: vi.fn(),
    onGuidedRedo: vi.fn(),
    onBack: vi.fn(),
    onError: vi.fn(),
    ...overrides
  };
}

function bodyText(): string {
  return document.body.textContent ?? "";
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  api.getNextProbeItem.mockResolvedValue({ active: false });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setAlgoConfig(undefined);
});

it("opens with one line and a verdict per question, held grades held", () => {
  render(<DiagnosticReviewScreen {...props()} />);
  expect(screen.getByText("That's the short check done. Here's what it showed.")).toBeTruthy();
  const rows = screen.getAllByTestId("check-verdict").map((row) => row.textContent ?? "");
  expect(rows[0]).toContain("Right");
  expect(rows[1]).toContain("Partly right");
  expect(rows[2]).toContain("Held for review");
  expect(rows[2]).not.toMatch(/0\s*\/\s*4/);
  expect(bodyText()).toContain("The condition was dropped.");
  for (const internal of ["converted_to_tutoring", "Feedback withheld", "observation", "value_of_information", "1/4", "4/4"]) {
    expect(bodyText()).not.toContain(internal);
  }
});

it("takes the one next step on Enter", async () => {
  const callbacks = props();
  render(<DiagnosticReviewScreen {...callbacks} />);
  expect(screen.getByRole("button", { name: /Back to practice/ })).toBeTruthy();
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
  await waitFor(() => expect(callbacks.onBack).toHaveBeenCalled());
});

it("makes fixing a shared mix-up the next step when the check found one", async () => {
  const end = blockEnd();
  end.releasedFeedback[1].causalFeedback = {
    commonRepair: { status: "deliver", decision: "deliver", reason: "covers", message: "Restrict to the condition first.",
      misconceptionId: "mis_1", factorId: "f_1", decisionReceiptId: "r_1" }
  } as unknown as ProbeBlockEndDto["releasedFeedback"][number]["causalFeedback"];
  const callbacks = props({ blockEnd: end });
  render(<DiagnosticReviewScreen {...callbacks} />);
  expect(screen.getByRole("button", { name: "Fix this mix-up · about 4 min" })).toBeTruthy();
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
  expect(callbacks.onOpenRepair).toHaveBeenCalledWith("mis_1");
});

it("keeps the full results behind details", () => {
  render(<DiagnosticReviewScreen {...props()} />);
  expect(screen.queryByText("causal panel")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(bodyText()).toContain("held for review");
  expect(bodyText()).not.toMatch(/\b0\/4\b/);
});

it("classic restores the screen exactly", () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<DiagnosticReviewScreen {...props()} />);
  expect(bodyText()).toContain("Diagnostic check complete");
  expect(bodyText()).toContain("Feedback withheld during the block, released now:");
  expect(bodyText()).toContain("observation 1");
  expect(bodyText()).toContain("converted_to_tutoring");
});
