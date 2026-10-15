// UX Phase 4.3 (docs/specs/ux_learnloop_v1.md §7.5): repair becomes one timed
// step, "Fix this mix-up · about 4 min": compare the two ideas, read both
// passages, then try one, each on the one primary button (or ↵), instead of
// the four-click flow. The measurement bookkeeping ("exposure, not proof",
// "Demonstrated credit", "not measurable") leaves the surface.
// `[ui] practice_feedback = "classic"` restores the screen exactly.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { RepairScreen } from "./RepairScreen";

const { api } = vi.hoisted(() => ({ api: {
  startRemediation: vi.fn(), prescribeRemediation: vi.fn(), startRemediationTreatment: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../components/OpenInSource", () => ({ OpenInSource: () => null }));

const CASE = {
  id: "mis_1",
  statement: "Treats P(A|B) as P(A)",
  correctionStatement: "Conditioning shrinks the outcomes to the ones where the condition holds.",
  mechanism: "drops the condition",
  targetFacet: "facet_conditional_probability",
  confusedWithFacet: "facet_unconditional_probability",
  status: "active",
  history: [{ id: "h1", label: "detected", at: "2026-10-10T00:00:00Z" }]
};
const EPISODE = { id: "ep_1", passagesShown: [], primedItemId: null, coldItemId: null };
const PASSAGES = [
  { role: "target", facetId: "facet_conditional_probability", spanView: { extractionId: "ex_1", spanId: "sp_1", sectionPath: ["2.2 Conditional probability"], blockType: "paragraph", text: "P(A|B) = P(A and B) / P(B)." } },
  { role: "confused_with", facetId: "facet_unconditional_probability", spanView: { extractionId: "ex_1", spanId: "sp_2", sectionPath: ["1.3 Probability"], blockType: "paragraph", text: "P(A) counts every outcome." } }
];

function bodyText(): string {
  return document.body.textContent ?? "";
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  api.startRemediation.mockResolvedValue({ version: 1, episode: EPISODE, case: CASE });
  api.prescribeRemediation.mockResolvedValue({ version: 1, episode: { ...EPISODE, passagesShown: PASSAGES }, case: CASE });
  api.startRemediationTreatment.mockResolvedValue({
    version: 1, episode: { ...EPISODE, passagesShown: PASSAGES, primedItemId: "pi_related" }, case: CASE,
    primedItemId: "pi_related", coldItemId: null, coldUnmeasurableReason: "no_independent_surface"
  });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setAlgoConfig(undefined);
});

it("is one timed step: compare, read both passages, then try one, each on the primary button", async () => {
  const onPractice = vi.fn();
  render(<RepairScreen misconceptionId="mis_1" sessionId="s1" onClose={vi.fn()} onPractice={onPractice} onError={vi.fn()} />);
  expect(await screen.findByText("Fix this mix-up · about 4 min")).toBeTruthy();
  expect(await screen.findByText(/Conditioning shrinks the outcomes/)).toBeTruthy();
  expect(bodyText()).toContain("conditional probability");
  expect(bodyText()).not.toContain("facet_");
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Read both passages/ }));
  });
  expect(await screen.findByText("P(A|B) = P(A and B) / P(B).")).toBeTruthy();
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Try one now/ }));
  });
  await waitFor(() => expect(onPractice).toHaveBeenCalledWith("pi_related"));
  expect(api.startRemediationTreatment).toHaveBeenCalledWith("ep_1");
});

it("advances on Enter as well", async () => {
  const onPractice = vi.fn();
  render(<RepairScreen misconceptionId="mis_1" onClose={vi.fn()} onPractice={onPractice} onError={vi.fn()} />);
  await screen.findByRole("button", { name: /Read both passages/ });
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
  await screen.findByRole("button", { name: /Try one now/ });
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
  await waitFor(() => expect(onPractice).toHaveBeenCalledWith("pi_related"));
});

it("keeps the measurement bookkeeping off the surface", async () => {
  render(<RepairScreen misconceptionId="mis_1" onClose={vi.fn()} onPractice={vi.fn()} onError={vi.fn()} />);
  await screen.findByRole("button", { name: /Read both passages/ });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Read both passages/ }));
  });
  await screen.findByText("P(A|B) = P(A and B) / P(B).");
  for (const internal of ["exposure", "proof", "Demonstrated credit", "not measurable", "prime", "canonical", "misconception", "active"]) {
    expect(bodyText()).not.toContain(internal);
  }
});

it("classic restores the screen exactly", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<RepairScreen misconceptionId="mis_1" onClose={vi.fn()} onPractice={vi.fn()} onError={vi.fn()} />);
  expect(await screen.findByText("compare the two ideas")).toBeTruthy();
  expect(screen.getByRole("button", { name: "show me the sources" })).toBeTruthy();
  expect(bodyText()).toContain("reading is recorded as exposure, not proof");
});
