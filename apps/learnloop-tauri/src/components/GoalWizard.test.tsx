// Router objective RO4 §8.5, landing ruling R2: the goal form asks the dated use weight the frictionless way:
// one optional field, prefilled with the default the sidecar names, that can be left alone. Shown only where
// the objective is on (goal_feasibility's useWeightDefault) and the goal has a date.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { GoalWizard } from "./GoalWizard";

const api = vi.hoisted(() => ({
  getConceptGraph: vi.fn(),
  goalFeasibility: vi.fn(),
  createGoal: vi.fn(),
  generateStarterPractice: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));

function feasibility(useWeightDefault: { dated: number } | null) {
  return {
    version: 1,
    scopeFacetCount: 2,
    onTrackCount: 1,
    projectedOnTrackFraction: 0.5,
    uncoveredConcepts: [],
    materialGaps: [],
    resolvedQuestSentence: null,
    questBasis: null,
    useWeightDefault
  };
}

beforeEach(() => {
  for (const fn of Object.values(api)) fn.mockReset();
  api.getConceptGraph.mockResolvedValue({
    concepts: [{ id: "svd", title: "Singular values", aliases: [], learningObjects: ["lo_svd"], practiceItemCount: 3 }]
  });
  api.createGoal.mockResolvedValue({ version: 1, goal: { id: "goal_midterm" }, populationBatch: null });
});

afterEach(() => cleanup());

async function toTheDateStep(useWeightDefault: { dated: number } | null) {
  api.goalFeasibility.mockResolvedValue(feasibility(useWeightDefault));
  const { container } = render(<GoalWizard onClose={vi.fn()} onCreated={vi.fn()} onError={vi.fn()} />);
  fireEvent.change(screen.getByPlaceholderText("e.g. Linear algebra midterm"), { target: { value: "Midterm" } });
  fireEvent.click(await screen.findByText("Singular values"));
  fireEvent.click(screen.getByText("next →"));
  fireEvent.click(screen.getByText("next →"));
  const date = container.querySelector('input[type="date"]') as HTMLInputElement;
  fireEvent.change(date, { target: { value: "2026-12-15" } });
  await waitFor(() => expect(api.goalFeasibility).toHaveBeenCalled(), { timeout: 2000 });
  return container;
}

async function createFromTheDateStep() {
  fireEvent.click(screen.getByText("next →"));
  await act(async () => {
    fireEvent.click(screen.getByText("create goal ↵"));
  });
  await waitFor(() => expect(api.createGoal).toHaveBeenCalledTimes(1));
  return api.createGoal.mock.calls[0][0];
}

it("prefills the optional use weight with the default and sends nothing when it is left alone", async () => {
  await toTheDateStep({ dated: 1 });
  const field = (await screen.findByLabelText(/how much this date counts/i)) as HTMLInputElement;
  expect(field.value).toBe("1");
  const sent = await createFromTheDateStep();
  expect(sent).not.toHaveProperty("datedUseWeight");
});

it("sends the weight the learner asked for", async () => {
  await toTheDateStep({ dated: 1 });
  const field = (await screen.findByLabelText(/how much this date counts/i)) as HTMLInputElement;
  fireEvent.change(field, { target: { value: "2.5" } });
  const sent = await createFromTheDateStep();
  expect(sent.datedUseWeight).toBe(2.5);
});

it("asks nothing where the objective is off, or for an open-ended goal", async () => {
  await toTheDateStep(null);
  await waitFor(() => expect(screen.queryByText(/facets on track/)).not.toBeNull(), { timeout: 2000 });
  expect(screen.queryByLabelText(/how much this date counts/i)).toBeNull();
  const sent = await createFromTheDateStep();
  expect(sent).not.toHaveProperty("datedUseWeight");
  cleanup();
  api.createGoal.mockClear();
  await toTheDateStep({ dated: 1 });
  await screen.findByLabelText(/how much this date counts/i);
  fireEvent.click(screen.getByText("open-ended (no deadline)"));
  expect(screen.queryByLabelText(/how much this date counts/i)).toBeNull();
});
