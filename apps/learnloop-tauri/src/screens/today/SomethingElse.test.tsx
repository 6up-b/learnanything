// Instruct hand-off IH3 (spec_instruct_handoff_v1 §6): the quiet "Something else would help" link on the desktop.
// Where it shows (only when the sidecar says so, never a modal), what it offers (the plan's own options in plain words,
// the router's own pick left off the offer page), what it sends (the choice, its note, the act's own key) and what the
// host does with the reply (a lesson opens as the learner's own start, anything else is the step it served).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { findJargon } from "../../copy/denyList";
import { clear } from "../../api/queryCache";
import type { PlanLessonOfferStepDto, SomethingElseChosenDto, SomethingElseOptionsDto } from "../../api/dto";
import { LessonOfferPage } from "./LessonOfferPage";
import { SOMETHING_ELSE_LINK, SomethingElse, lessonEntryFor } from "./SomethingElse";

const { api } = vi.hoisted(() => ({
  api: {
    getDailyPlan: vi.fn(),
    planSomethingElseOptions: vi.fn(),
    planSomethingElse: vi.fn(),
    lessonSuggestionRespond: vi.fn(),
    recordOfferShown: vi.fn(async () => ({ version: 1, recorded: true }))
  }
}));
vi.mock("../../api/client", () => ({ api }));

const OPTIONS: SomethingElseOptionsDto = {
  version: 1, enabled: true, drawn: true, decisionId: "dec1", device: "desktop",
  options: [
    { kind: "question", ref: "cand_q", label: "Another question", minutes: 6, propensity: 0.2, plansPick: false, servable: true },
    { kind: "review", ref: "cand_r", label: "Review something from earlier", minutes: 4, propensity: null, plansPick: false, servable: true },
    { kind: "read", ref: "cand_read", label: "Read Bayes' rule", minutes: 12, propensity: null, plansPick: false, servable: true },
    { kind: "lesson", ref: "lesson_offer:lo_relu", label: "Learn ReLU", minutes: 15, propensity: 0.3, plansPick: true, servable: true },
    { kind: "stop", ref: "stop_for_today", label: "Stop for today", minutes: null, propensity: null, plansPick: false, servable: true }
  ]
};
const SERVED = (extra: Record<string, unknown> = {}): SomethingElseChosenDto => ({
  version: 1, enabled: true, plan: null,
  preference: { id: "k", outcome: "served", kind: "question", ref: "cand_q", servedDecisionId: "d1", lesson: null, replayed: false },
  ...extra
} as SomethingElseChosenDto);

beforeEach(() => {
  clear();
  api.getDailyPlan.mockResolvedValue({ version: 1, enabled: true, plan: null, somethingElse: true });
  api.planSomethingElseOptions.mockResolvedValue(OPTIONS);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function mount(props: Partial<Parameters<typeof SomethingElse>[0]> = {}) {
  const onChosen = vi.fn();
  const onError = vi.fn();
  render(<SomethingElse sessionId="sess1" surface="feedback" attemptId="att1" onChosen={onChosen} onError={onError} {...props} />);
  return { onChosen, onError };
}

it("is one quiet link, and nothing is asked or written until it is used", async () => {
  mount({ enabled: true });
  expect(screen.getByTestId("something-else-link").textContent).toBe(SOMETHING_ELSE_LINK);
  expect(SOMETHING_ELSE_LINK).toBe("Something else would help");
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(api.planSomethingElseOptions).not.toHaveBeenCalled();
  expect(api.planSomethingElse).not.toHaveBeenCalled();
});

it("shows only when the plan says so: the switch off leaves nothing", async () => {
  api.getDailyPlan.mockResolvedValue({ version: 1, enabled: true, plan: null });
  mount();
  await act(async () => undefined);
  expect(screen.queryByTestId("something-else")).toBeNull();
  cleanup();
  mount({ enabled: false });
  expect(screen.queryByTestId("something-else")).toBeNull();
  cleanup();
  api.getDailyPlan.mockResolvedValue({ version: 1, enabled: true, plan: null, somethingElse: true });
  clear();
  mount();
  await act(async () => undefined);
  expect(screen.getByTestId("something-else-link")).toBeTruthy();
});

it("opens in place with the plan's own options in plain words and an optional note", async () => {
  mount({ enabled: true });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  const panel = screen.getByTestId("something-else-panel");
  expect(panel.getAttribute("role")).not.toBe("dialog");
  expect(api.planSomethingElseOptions).toHaveBeenCalledWith("sess1");
  expect(screen.getByTestId("something-else-option-question").textContent).toBe("Another question (about 6 min)");
  expect(screen.getByTestId("something-else-option-review").textContent).toBe("Review something from earlier (about 4 min)");
  expect(screen.getByTestId("something-else-option-read").textContent).toBe("Read Bayes' rule (about 12 min)");
  expect(screen.getByTestId("something-else-option-lesson").textContent).toBe("Learn ReLU (about 15 min)");
  expect(screen.getByTestId("something-else-option-stop").textContent).toBe("Stop for today");
  expect(screen.getByTestId("something-else-note")).toBeTruthy();
  expect(findJargon(panel.textContent ?? "")).toEqual([]);
  // the router's probabilities are the log's, never shown to the learner
  expect(panel.textContent).not.toMatch(/0\.2|0\.3|%/);
  expect(panel.textContent).toContain("It isn't counted as knowing something.");
});

it("sends the choice with its note and its own key, closes, and tells the host", async () => {
  api.planSomethingElse.mockResolvedValueOnce(SERVED());
  const { onChosen } = mount({ enabled: true });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  fireEvent.change(screen.getByTestId("something-else-note"), { target: { value: "  a harder one, please  " } });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-question")); });
  expect(api.planSomethingElse).toHaveBeenCalledTimes(1);
  const sent = api.planSomethingElse.mock.calls[0][0];
  expect(sent).toMatchObject({ kind: "question", ref: "cand_q", surface: "feedback", attemptId: "att1", sessionId: "sess1",
                               noteMd: "a harder one, please" });
  expect(String(sent.preferenceId).length).toBeGreaterThan(8);
  expect(onChosen).toHaveBeenCalledTimes(1);
  expect(screen.queryByTestId("something-else-panel")).toBeNull();
  expect(screen.getByTestId("something-else-link")).toBeTruthy();
});

it("a failed send keeps the same key, so a retry writes once", async () => {
  api.planSomethingElse.mockRejectedValueOnce(new Error("sidecar busy")).mockResolvedValueOnce(SERVED());
  const { onChosen, onError } = mount({ enabled: true });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-review")); });
  expect(onError).toHaveBeenCalledTimes(1);
  expect(onChosen).not.toHaveBeenCalled();
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-review")); });
  const [first, second] = api.planSomethingElse.mock.calls.map((call) => call[0]);
  expect(second.preferenceId).toBe(first.preferenceId);
  expect(onChosen).toHaveBeenCalledTimes(1);
});

it("leaves 'learn this' off where lessons can't open, and the plan's own pick off the offer page", async () => {
  mount({ enabled: true, canStartLesson: false });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  expect(screen.queryByTestId("something-else-option-lesson")).toBeNull();
  expect(screen.getByTestId("something-else-option-question")).toBeTruthy();
  cleanup();
  mount({ enabled: true, hidePlansPick: true });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  expect(screen.queryByTestId("something-else-option-lesson")).toBeNull();
});

it("says so when nothing else is available", async () => {
  api.planSomethingElseOptions.mockResolvedValueOnce({ version: 1, enabled: true, options: [] });
  mount({ enabled: true });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  expect(screen.getByTestId("something-else-none").textContent).toBe("Nothing else is available right now.");
});

it("a chosen lesson becomes the learner's own start, with no suggestion pre-answered", () => {
  const entry = lessonEntryFor(SERVED({
    preference: { id: "k", outcome: "lesson", kind: "lesson", ref: "lesson_offer:lo_relu", servedDecisionId: "d1",
                  lesson: { learningObjectIds: ["lo_relu"], title: "ReLU" }, replayed: false }
  }));
  expect(entry).toEqual({ kind: "open", entry: "learning_object", learningObjectIds: ["lo_relu"], title: "ReLU" });
  expect(lessonEntryFor(SERVED())).toBeNull();
});

it("sits in the offer page's slot, uses the offer_page surface and leaves the page's own pick off", async () => {
  const step: PlanLessonOfferStepDto = {
    kind: "lesson_offer", planId: "p1", blockId: "blk1", blockOrdinal: 2, estMinutes: 12, boundary: true, why: "", whyKind: "computed",
    offer: { decisionId: "dec1", blockId: "blk1", minutes: 12, whyLabel: "Suggested by LearnLoop's planner", answered: null,
             suggestion: { ref: "lesson:lo_relu", title: "ReLU", learningObjectIds: ["lo_relu"], reason: "cold_failing", why: "w" },
             alternatives: [] }
  };
  const onSomethingElse = vi.fn();
  api.planSomethingElse.mockResolvedValueOnce(SERVED());
  render(<LessonOfferPage step={step} sessionId="sess1" onStartLesson={vi.fn()} onAnswered={vi.fn()} onError={vi.fn()}
                          onSomethingElse={onSomethingElse} />);
  await act(async () => undefined);
  const slot = screen.getByTestId("lesson-offer-something-else-slot");
  expect(slot.contains(screen.getByTestId("something-else-link"))).toBe(true);
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-link")); });
  expect(screen.queryByTestId("something-else-option-lesson")).toBeNull();
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-question")); });
  expect(api.planSomethingElse.mock.calls[0][0]).toMatchObject({ surface: "offer_page", kind: "question" });
  expect(onSomethingElse).toHaveBeenCalledTimes(1);
  // the Start button is untouched: nothing started by itself
  expect(api.lessonSuggestionRespond).not.toHaveBeenCalled();
});
