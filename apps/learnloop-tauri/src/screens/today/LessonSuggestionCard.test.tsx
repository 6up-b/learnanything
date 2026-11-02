// Teacher TE1b: Today's lesson suggestion card (spec_teacher_v1 §15.1, §19).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { LessonSuggestionDto } from "../../api/dto";
import { LessonSuggestionCard } from "./LessonSuggestionCard";
import { LessonScreen } from "../LessonScreen";

const { api } = vi.hoisted(() => ({
  api: { lessonSuggestion: vi.fn(), lessonSuggestionRespond: vi.fn(), lessonTurn: vi.fn(), lessonView: vi.fn() }
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const CARD: LessonSuggestionDto = {
  decisionId: "dec1", day: "2026-11-02", minutes: 15, whyLabel: "Suggested by LearnLoop's planner",
  suggestion: { ref: "lesson:lo_eigen", title: "Eigenvalues", learningObjectIds: ["lo_eigen"], reason: "new_goal",
                why: "It's on your goal and you haven't started it yet." },
  alternatives: [
    { ref: "lesson:lo_det", title: "Determinants", learningObjectIds: ["lo_det"], reason: "cold_failing",
      why: "Your last two checks on it didn't come out right." },
    { ref: "lesson:lo_svd", title: "SVD", learningObjectIds: ["lo_svd"], reason: "new_goal", why: "On your goal." }
  ]
};

async function mount(card: LessonSuggestionDto | null = CARD) {
  api.lessonSuggestion.mockResolvedValueOnce({ suggestion: card });
  const onStartLesson = vi.fn();
  const onError = vi.fn();
  await act(async () => {
    render(<LessonSuggestionCard sessionId="sess1" onStartLesson={onStartLesson} onError={onError} />);
  });
  return { onStartLesson, onError };
}

it("shows the day's card: the topic in plain words, about 15 minutes, the reason, Start, two alternatives, Not now", async () => {
  await mount();
  expect(api.lessonSuggestion).toHaveBeenCalledWith({ sessionId: "sess1" });
  const card = screen.getByTestId("lesson-suggestion-card");
  expect(card.textContent).toContain("Learn Eigenvalues now? (about 15 min)");
  expect(card.textContent).toContain("It's on your goal and you haven't started it yet.");
  expect(card.textContent).toContain("Suggested by LearnLoop's planner");
  expect(screen.getByRole("button", { name: "Start" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Or: Determinants" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Or: SVD" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Not now" })).toBeTruthy();
  // A card in the page, never a dialog.
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("shows nothing when there is no card today", async () => {
  await mount(null);
  expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
});

it("Start records the response and opens the lesson with the decision and the recorded lesson id", async () => {
  const { onStartLesson } = await mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "accepted", candidateRef: "lesson:lo_eigen",
    lesson: { lessonId: "les_1", decisionId: "dec1", learningObjectIds: ["lo_eigen"], title: "Eigenvalues" }
  });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Start" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "accepted", sessionId: "sess1" });
  expect(onStartLesson).toHaveBeenCalledWith({
    kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"], title: "Eigenvalues",
    suggestion: { decisionId: "dec1", lessonId: "les_1" }
  });
  expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
});

it("an alternative names its candidate", async () => {
  const { onStartLesson } = await mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "chose_alternative", candidateRef: "lesson:lo_det",
    lesson: { lessonId: "les_2", decisionId: "dec1", learningObjectIds: ["lo_det"], title: "Determinants" }
  });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Or: Determinants" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({
    decisionId: "dec1", response: "chose_alternative", sessionId: "sess1", candidateRef: "lesson:lo_det" });
  expect(onStartLesson.mock.calls[0][0].learningObjectIds).toEqual(["lo_det"]);
});

it("Not now records the decline, hides the card and opens nothing", async () => {
  const { onStartLesson } = await mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "declined", candidateRef: "lesson:lo_eigen", lesson: null });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "declined", sessionId: "sess1" });
  expect(onStartLesson).not.toHaveBeenCalled();
  expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
});

it("a failed card read shows no card and reports nothing", async () => {
  api.lessonSuggestion.mockRejectedValueOnce(new Error("boom"));
  const onError = vi.fn();
  await act(async () => {
    render(<LessonSuggestionCard sessionId={null} onStartLesson={vi.fn()} onError={onError} />);
  });
  expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
  expect(onError).not.toHaveBeenCalled();
});

it("the lesson screen opens a suggested lesson with its origin, the decision and the lesson id", async () => {
  api.lessonTurn.mockResolvedValueOnce({
    version: 1, lessonId: "les_1", goal: "Eigenvalues", learningObjectIds: ["lo_eigen"], closed: false,
    closeReason: null, feed: [], plan: [], openCheck: null, openPrediction: null,
    quickCheck: { learningObjectIds: ["lo_eigen"] },
    inspector: { doctrine: null, route: null, model: null, forecasts: [] }
  });
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"],
                                  suggestion: { decisionId: "dec1", lessonId: "les_1" } }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
  expect(api.lessonTurn).toHaveBeenCalledWith({
    action: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"], origin: "router_suggestion",
    suggestionDecisionId: "dec1", lessonId: "les_1" });
});

// Landing ruling R2 (codex verify F8): a Start whose lesson never opened offers "Open the lesson" and "Not now";
// "Not now" releases the reservation (the Start stays recorded) and opens nothing.
const PENDING: LessonSuggestionDto = {
  ...CARD, alternatives: [],
  pendingLesson: { lessonId: "les_9", decisionId: "dec1", learningObjectIds: ["lo_eigen"], title: "Eigenvalues" }
};

it("a pending lesson offers Open the lesson and Not now", async () => {
  await mount(PENDING);
  const card = screen.getByTestId("lesson-suggestion-card");
  expect(card.textContent).toContain("Your lesson on Eigenvalues hasn't opened yet.");
  expect(screen.getByRole("button", { name: "Open the lesson" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Not now" })).toBeTruthy();
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("Not now on a pending lesson releases it, hides the card and opens nothing", async () => {
  const { onStartLesson, onError } = await mount(PENDING);
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "released", candidateRef: "lesson:lo_eigen", lesson: null });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "released", sessionId: "sess1" });
  expect(onStartLesson).not.toHaveBeenCalled();
  expect(onError).not.toHaveBeenCalled();
  expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
});

it("a failed release keeps the pending card and reports the error", async () => {
  const { onStartLesson, onError } = await mount(PENDING);
  api.lessonSuggestionRespond.mockRejectedValueOnce(new Error("That lesson is no longer on your Today card."));
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  expect(onError.mock.calls[0][0]).toContain("That lesson is no longer on your Today card.");
  expect(onStartLesson).not.toHaveBeenCalled();
  expect(screen.getByTestId("lesson-suggestion-card")).toBeTruthy();
});
