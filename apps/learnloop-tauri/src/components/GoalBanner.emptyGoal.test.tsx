// UX-8 (UX journey audit, walks student-1 #128, beginner-1 #84): a goal nothing has checked yet said
// "all facets certified — hold the line until the due date." beside "BEHIND", on an open-ended goal too,
// and offered "practice at-risk facets" with nothing to practise. Each empty state now says what is true.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { GoalDto, GoalPaceDto, GoalReportSummaryDto } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { GoalBanner } from "./GoalBanner";

vi.mock("../api/client", () => ({
  api: {
    getGoalReportSeries: vi.fn(() => new Promise(() => undefined)),
    getExamStatus: vi.fn(() => new Promise(() => undefined)),
    getGoalReport: vi.fn(() => new Promise(() => undefined))
  }
}));

const NOW = Date.parse("2026-11-17T18:00:00Z");

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  // The banner remembers the last count it celebrated; this lane's jsdom has no storage of its own.
  const store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
    removeItem: (key: string) => void store.delete(key),
    clear: () => store.clear()
  });
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function pace(overrides: Partial<GoalPaceDto> = {}): GoalPaceDto {
  return {
    attemptsPerDay: 0,
    attemptsLast14d: 0,
    daysLeft: null,
    attemptsRemaining: 0,
    neededPerDay: null,
    onPace: null,
    attemptsLogged: 0,
    paceKind: "activity",
    ...overrides
  };
}

function report(overrides: Partial<GoalReportSummaryDto> = {}): GoalReportSummaryDto {
  return {
    onTrackCount: 0,
    total: 0,
    onTrackFraction: null,
    atRiskCount: 0,
    horizon: "2026-12-09T00:00:00Z",
    dueAt: null,
    certifiedCount: 0,
    examinedCount: 0,
    attainmentFraction: null,
    predictedRecallMean: null,
    attemptsRemaining: 0,
    attemptsRemainingIsPartial: false,
    pace: pace(),
    ...overrides
  };
}

function goal(dueAt: string | null, summary: GoalReportSummaryDto, overrides: Partial<GoalDto> = {}): GoalDto {
  return {
    id: "goal_1",
    title: "Linear algebra midterm",
    intentSentence: null,
    creationSource: "learner",
    resolvedQuestSentence: null,
    questBasis: null,
    status: "active",
    priority: 1,
    targetRecall: 0.8,
    dueAt,
    facetScope: { concepts: [], facets: [] },
    exam: { enabled: false, itemCount: 0 },
    practicableItemCount: 0,
    createdAt: "2026-11-17T10:00:00Z",
    updatedAt: "2026-11-17T10:00:00Z",
    report: summary,
    ...overrides
  };
}

function show(g: GoalDto): string {
  const { container } = render(
    <GoalBanner goals={[g]} onError={() => undefined} onPracticeAtRisk={() => undefined} onNewGoal={() => undefined} onGoalChanged={() => undefined} />
  );
  return container.textContent ?? "";
}

/** What an empty goal's report must never say (the vacuous truths the walks saw). The at-risk list keeps its own
 *  words (a later stage's jargon sweep): only the sentences and actions this state chooses are held to the glossary. */
function expectNoVacuousTruths(text: string): void {
  expect(text).not.toMatch(/hold the line/);
  expect(text).not.toMatch(/certified/i);
  expect(text).not.toMatch(/BEHIND/);
}

it("UX-8: no answers and no due date: says nothing is checked yet and what will move it, with no verdict", () => {
  // beginner-1 #84: an open-ended goal with nothing from the library in it yet.
  const text = show(goal(null, report()));
  expectNoVacuousTruths(text);
  expect(text).not.toMatch(/facets?/i);
  const line = screen.getByTestId("goal-empty-state").textContent ?? "";
  expect(line).toBe(
    "Nothing has been checked for this goal yet. None of the topics in your books is part of it so far: add or read a book that covers it, and its questions will count here."
  );
  expect(findJargon(line)).toEqual([]);
  expect(screen.getByTestId("goal-status").textContent).toBe("NOT STARTED");
  // Nothing to practise: no button that only answers "Nothing for this goal is ready to practise yet."
  expect(screen.queryByRole("button", { name: /practi[sc]e/i })).toBeNull();
});

it("UX-8: no answers with a due date: says nothing is checked yet and how long is left, never BEHIND", () => {
  // student-1 #128: an exam on Dec 9, 22 days away, nothing answered.
  const text = show(goal("2026-12-09T18:00:00Z", report({ dueAt: "2026-12-09T18:00:00Z", pace: pace({ daysLeft: 22 }) })));
  expectNoVacuousTruths(text);
  expect(text).not.toMatch(/facets?/i);
  const line = screen.getByTestId("goal-empty-state").textContent ?? "";
  expect(line).toBe(
    "Nothing has been checked for this goal yet. None of the topics in your books is part of it so far: add or read a book that covers it, and its questions will count here. It is due in 22 days."
  );
  expect(findJargon(line)).toEqual([]);
  expect(screen.getByTestId("goal-status").textContent).toBe("NOT STARTED");
});

it("UX-8: topics in scope but no answers yet: says answering is what starts it, and offers practice when there is some", () => {
  const text = show(
    goal(null, report({ total: 6, atRiskCount: 6, attemptsRemaining: 18, pace: pace({ attemptsRemaining: 18 }) }), { practicableItemCount: 4 })
  );
  expectNoVacuousTruths(text);
  const line = screen.getByTestId("goal-empty-state").textContent ?? "";
  expect(line).toBe("Nothing has been checked for this goal yet. Answer its questions on your own and this report will start to fill in.");
  expect(findJargon(line)).toEqual([]);
  expect(screen.getByRole("button", { name: "practise for this goal ↵" })).toBeTruthy();
});

it("UX-8: answers but nothing checked: counts the answers and says which kind count here", () => {
  const text = show(
    goal(
      "2026-12-09T18:00:00Z",
      report({ total: 6, atRiskCount: 6, attemptsRemaining: 18, dueAt: "2026-12-09T18:00:00Z", pace: pace({ attemptsLogged: 3, attemptsLast14d: 3, attemptsPerDay: 0.2, daysLeft: 22, attemptsRemaining: 18 }) }),
      { practicableItemCount: 0 }
    )
  );
  expectNoVacuousTruths(text);
  const line = screen.getByTestId("goal-empty-state").textContent ?? "";
  expect(line).toBe(
    // UX-17: its topics have no questions (practicableItemCount 0), so the sentence says that, not "this goal's questions".
    "You have answered 3 questions, but none has checked this goal's topics yet. This goal's topics have no questions yet. Once there are some, the ones you answer on your own count here. It is due in 22 days."
  );
  expect(findJargon(line)).toEqual([]);
  // No question of this goal is ready to practise: no button.
  expect(screen.queryByRole("button", { name: /practi[sc]e/i })).toBeNull();
});

it("UX-8: everything examined and certified keeps its sentence, its standing and its action (unchanged)", () => {
  show(
    goal(
      "2026-12-09T18:00:00Z",
      report({
        total: 4, onTrackCount: 4, onTrackFraction: 1, certifiedCount: 4, examinedCount: 4, attainmentFraction: 1, predictedRecallMean: 0.9,
        dueAt: "2026-12-09T18:00:00Z", pace: pace({ attemptsLogged: 20, attemptsLast14d: 20, attemptsPerDay: 1.4, daysLeft: 22 })
      }),
      { practicableItemCount: 9 }
    )
  );
  expect(screen.queryByTestId("goal-empty-state")).toBeNull();
  expect(screen.getByText("all facets certified — hold the line until the due date.")).toBeTruthy();
  expect(screen.getByTestId("goal-status").textContent).toBe("ON TRACK");
  expect(screen.getByRole("button", { name: "practice at-risk facets ↵" })).toBeTruthy();
});

// UX-17 (UX journey audit part 2, project-1 #24-27): a goal whose topics exist but have no questions yet said
// "None of the topics in your books is part of it so far", beside a goal box that counted "3 topics from your books".
it("UX-17: topics in the goal but no questions on them yet: names the topics and says the questions are what is missing", () => {
  const text = show(goal(null, report(), {
    facetScope: { concepts: ["preparing_face_images", "computing_a_pca_basis", "pca_compression_quality"], facets: [] },
    practicableItemCount: 0
  }));
  expectNoVacuousTruths(text);
  expect(text).not.toContain("None of the topics in your books");
  const line = screen.getByTestId("goal-empty-state").textContent ?? "";
  expect(line).toBe(
    "Nothing has been checked for this goal yet. This goal has 3 topics, but no questions on them yet. Once there are some, the ones you answer on your own count here."
  );
  expect(findJargon(line)).toEqual([]);
  expect(screen.queryByRole("button", { name: /practi[sc]e/i })).toBeNull();
});

it("UX-17: one topic, and topics counted by the report with no questions, say it in the same words", () => {
  show(goal(null, report(), { facetScope: { concepts: ["eigen"], facets: [] }, practicableItemCount: 0 }));
  expect(screen.getByTestId("goal-empty-state").textContent).toBe(
    "Nothing has been checked for this goal yet. This goal has 1 topic, but no questions on it yet. Once there are some, the ones you answer on your own count here."
  );
  cleanup();
  show(goal(null, report({ total: 4, atRiskCount: 4 }), { practicableItemCount: 0 }));
  expect(screen.getByTestId("goal-empty-state").textContent).toBe(
    "Nothing has been checked for this goal yet. This goal's topics have no questions yet. Once there are some, the ones you answer on your own count here."
  );
});

it("UX-17: no topics at all keeps the no-topics sentence; questions to answer keep theirs", () => {
  show(goal(null, report()));
  expect(screen.getByTestId("goal-empty-state").textContent).toContain("None of the topics in your books is part of it so far");
  cleanup();
  show(goal(null, report({ total: 3, atRiskCount: 3 }), { facetScope: { concepts: ["eigen"], facets: [] }, practicableItemCount: 5 }));
  expect(screen.getByTestId("goal-empty-state").textContent).toBe(
    "Nothing has been checked for this goal yet. Answer its questions on your own and this report will start to fill in."
  );
});
