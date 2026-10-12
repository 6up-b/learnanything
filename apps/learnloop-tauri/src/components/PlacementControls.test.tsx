import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { LearningObjectPlacementDto } from "../api/dto";
import { ASSUMED_LABEL, KnowThisAction, PlacementSection } from "./PlacementControls";

const { api } = vi.hoisted(() => ({ api: { placementSelfReport: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const base: LearningObjectPlacementDto = {
  active: true,
  algorithmVersion: "mvp-0.11",
  quickCheckK: 4,
  quickCheckBudgetMinutes: 8,
  learningObjectId: "lo_diag",
  intent: null,
  intentReason: null,
  assumed: false,
  label: null,
  source: null,
  firstReviewDue: null,
  firstReviewIsDue: false,
  lastOutcome: null,
  returnedByLearner: false
};

function section(placement: LearningObjectPlacementDto) {
  const props = { onChanged: vi.fn(), onQuickCheck: vi.fn(), onError: vi.fn() };
  render(<PlacementSection learningObjectId="lo_diag" placement={placement} {...props} />);
  return props;
}

it("labels an assumed LO honestly and offers 'I don't know this'", async () => {
  api.placementSelfReport.mockResolvedValue({});
  const props = section({
    ...base, assumed: true, label: ASSUMED_LABEL, source: "self_report", firstReviewDue: "2026-10-26T12:00:00Z"
  });
  expect(screen.getByText(ASSUMED_LABEL)).toBeTruthy();
  expect(screen.getByText("first review 2026-10-26 is the check")).toBeTruthy();
  expect(screen.queryByText("✓ I know this")).toBeNull();
  await act(async () => {
    fireEvent.click(screen.getByText("✗ I don't know this"));
  });
  expect(api.placementSelfReport).toHaveBeenCalledWith({ report: "dont_know_this", learningObjectIds: ["lo_diag"] });
  expect(props.onChanged).toHaveBeenCalled();
});

it("offers 'I know this' and the never-prompted quick check on an LO being learned", async () => {
  api.placementSelfReport.mockResolvedValue({});
  const props = section(base);
  expect(screen.queryByText(ASSUMED_LABEL)).toBeNull();
  expect(screen.getByText("learning: practice is the placement")).toBeTruthy();
  await act(async () => {
    fireEvent.click(screen.getByText("✓ I know this"));
  });
  expect(api.placementSelfReport).toHaveBeenCalledWith({ report: "know_this", learningObjectIds: ["lo_diag"] });
  fireEvent.click(screen.getByText("? Check what I already know"));
  expect(props.onQuickCheck).toHaveBeenCalledWith(["lo_diag"]);
});

it("says why an LO is back to learning, and renders nothing while placement is off", () => {
  section({ ...base, intent: "learning", intentReason: "check_missed", lastOutcome: "failed" });
  expect(screen.getByText("the first review missed, so this is back to learning")).toBeTruthy();
  cleanup();
  section({ ...base, intent: "learning", intentReason: "missed_in_maintenance", lastOutcome: "passed" });
  expect(screen.getByText("a later review missed, so this is back to learning")).toBeTruthy();
  cleanup();
  section({ ...base, intent: "learning", intentReason: "i_dont_know_this", lastOutcome: "passed" });
  expect(screen.getByText("you said you don't know this yet, so it is being taught")).toBeTruthy();
  cleanup();
  const { container } = render(
    <PlacementSection learningObjectId="lo_diag" placement={{ ...base, active: false }} onChanged={vi.fn()} onError={vi.fn()} />
  );
  expect(container.textContent).toBe("");
});

it("'I know this' on a card reports the card's LO, then moves on", async () => {
  api.placementSelfReport.mockResolvedValue({});
  const onDone = vi.fn();
  render(<KnowThisAction practiceItemId="pi_diag_mid" sessionId="s1" onDone={onDone} onError={vi.fn()} />);
  await act(async () => {
    fireEvent.click(screen.getByText("✓ I know this"));
  });
  expect(api.placementSelfReport).toHaveBeenCalledWith({
    report: "know_this", practiceItemId: "pi_diag_mid", sessionId: "s1"
  });
  expect(onDone).toHaveBeenCalled();
});

it("labels a checked LO as maintenance and still offers 'I don't know this'", async () => {
  api.placementSelfReport.mockResolvedValue({});
  section({ ...base, intent: "maintenance", intentReason: "check_passed", lastOutcome: "passed" });
  expect(screen.getByText("its first review passed: in maintenance, the rest of its new items are skipped")).toBeTruthy();
  expect(screen.queryByText("✓ I know this")).toBeNull();
  await act(async () => {
    fireEvent.click(screen.getByText("✗ I don't know this"));
  });
  expect(api.placementSelfReport).toHaveBeenCalledWith({ report: "dont_know_this", learningObjectIds: ["lo_diag"] });
});

it("says why a first review short of full marks kept the LO in maintenance (owner decision 2026-10-12)", () => {
  const maintained = { ...base, intent: "maintenance" as const, intentReason: "check_passed" as const, lastOutcome: "passed" as const };
  section({ ...maintained, outcomeReason: "slip" });
  expect(
    screen.getByText("its first review slipped, not a knowledge gap: in maintenance, the rest of its new items are skipped")
  ).toBeTruthy();
  cleanup();
  section({ ...maintained, outcomeReason: "item_contract" });
  expect(screen.getByText(/missed what the question expected, not a knowledge gap/)).toBeTruthy();
  cleanup();
  section({ ...maintained, outcomeReason: "unassessed" });
  expect(screen.getByText(/took a route the grader could not check/)).toBeTruthy();
  cleanup();
  section({ ...maintained, outcomeReason: "interaction_context" });
  expect(screen.getByText(/thrown by how it was presented, not a knowledge gap/)).toBeTruthy();
  cleanup();
  section({ ...maintained, outcomeReason: "clean" });
  expect(screen.getByText("its first review passed: in maintenance, the rest of its new items are skipped")).toBeTruthy();
  cleanup();
  section({ ...maintained, outcomeReason: "slip", awaitingDiagnosis: true });
  expect(screen.getByText("in maintenance; waiting for the diagnosis of your last answer before deciding")).toBeTruthy();
  cleanup();
  section({
    ...base, assumed: true, label: ASSUMED_LABEL, source: "self_report", firstReviewDue: "2026-10-26T12:00:00Z",
    firstReviewIsDue: true, awaitingDiagnosis: true
  });
  expect(screen.getByText("waiting for the diagnosis of your last answer before deciding")).toBeTruthy();
  cleanup();
  section({ ...base, intent: "learning", intentReason: "check_missed", outcomeReason: "knowledge_gap", lastOutcome: "failed" });
  expect(screen.getByText("the first review showed a knowledge gap, so this is back to learning")).toBeTruthy();
  cleanup();
  // Codex review F5: a diagnosis that named no cause is not a pass.
  section({ ...base, intent: "learning", intentReason: "check_missed", outcomeReason: "no_gap_attributed", lastOutcome: "failed" });
  expect(screen.getByText("the first review missed, so this is back to learning")).toBeTruthy();
});
