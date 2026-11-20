// "Waiting you can see" (docs/reviews/ux-waiting.md): a goal's details wait
// longest for the projection of where the goal is heading (10 to 14 s uncached
// in the walks, exam-1 #3 and seasoned-2 #14, which read "loading trajectory…").
// The shared waiting line says it, after its delay, and is gone when it lands.
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { GoalDto } from "../api/dto";
import { GoalBanner } from "./GoalBanner";

const { api } = vi.hoisted(() => ({ api: {
  getGoalReportSeries: vi.fn(), getExamStatus: vi.fn(() => new Promise(() => undefined)), getGoalReport: vi.fn(() => new Promise(() => undefined))
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("./GoalTrajectoryChart", () => ({ GoalTrajectoryChart: () => <div data-testid="trajectory-chart" /> }));

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(Date.parse("2026-11-17T18:00:00Z"));
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null, setItem: (key: string, value: string) => void store.set(key, value),
    removeItem: (key: string) => void store.delete(key), clear: () => store.clear()
  });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); });

const GOAL = {
  id: "goal_1", title: "Linear algebra midterm", intentSentence: null, creationSource: "learner", resolvedQuestSentence: null, questBasis: null,
  status: "active", priority: 1, targetRecall: 0.8, dueAt: "2026-12-09T00:00:00Z", facetScope: { concepts: [], facets: [] },
  exam: { enabled: false, itemCount: 0 }, practicableItemCount: 3, createdAt: "2026-11-17T10:00:00Z", updatedAt: "2026-11-17T10:00:00Z",
  report: {
    onTrackCount: 1, total: 2, onTrackFraction: 0.5, atRiskCount: 1, horizon: "2026-12-09T00:00:00Z", dueAt: "2026-12-09T00:00:00Z",
    certifiedCount: 1, examinedCount: 2, attainmentFraction: 0.5, predictedRecallMean: 0.6, attemptsRemaining: 4, attemptsRemainingIsPartial: false,
    pace: { attemptsPerDay: 1, attemptsLast14d: 6, daysLeft: 22, attemptsRemaining: 4, neededPerDay: 0.2, onPace: true, attemptsLogged: 6, paceKind: "activity" }
  }
} as unknown as GoalDto;

it("the goal's projection: nothing before the delay, then the line, gone when the chart lands", async () => {
  let land!: (value: unknown) => void;
  api.getGoalReportSeries.mockReturnValue(new Promise((done) => { land = done; }));
  render(<GoalBanner goals={[GOAL]} onError={() => undefined} onPracticeAtRisk={() => undefined} onNewGoal={() => undefined} onGoalChanged={() => undefined} />);
  await act(async () => { await vi.advanceTimersByTimeAsync(300); });
  expect(screen.queryByText("Working out where this goal is heading…")).toBeNull();
  await act(async () => { await vi.advanceTimersByTimeAsync(100); });
  expect(screen.getByTestId("trajectory-wait").textContent).toBe("◐ Working out where this goal is heading…");
  await act(async () => { land({ series: [] }); await vi.advanceTimersByTimeAsync(0); });
  expect(screen.getByTestId("trajectory-chart")).toBeTruthy();
  expect(screen.queryByTestId("trajectory-wait")).toBeNull();
});
