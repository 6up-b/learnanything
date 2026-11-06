// Teacher TE2 (spec_teacher_v1 §11.3, §11.5, §19): the quick question in a lesson, and a lesson started from what
// the learner types.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { LessonGoalDto, LessonViewDto } from "../api/dto";
import { LessonScreen, PROBE_POLL_MS } from "./LessonScreen";

const { api } = vi.hoisted(() => ({
  api: { lessonTurn: vi.fn(), lessonView: vi.fn(), lessonActivity: vi.fn(), lessonGoal: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
});

function lesson(overrides: Partial<LessonViewDto> = {}): LessonViewDto {
  return {
    version: 1, lessonId: "les1", goal: "Eigenvalues", learningObjectIds: ["lo_eigen"], closed: false,
    closeReason: null, feed: [{ kind: "message", text: "Before we start, one quick question.", choices: [] }],
    plan: [], openCheck: null, openPrediction: null, quickCheck: { learningObjectIds: ["lo_eigen"] },
    inspector: { doctrine: "teacher_doctrine_v1", route: null, model: null, forecasts: [] }, te2: true,
    ...overrides,
  };
}

const PREPARING = { probeRef: "p1", status: "preparing" as const, label: "Preparing a question on this…", teachAnyway: true };
const OPEN = { probeRef: "p1", status: "open" as const, label: "A quick question first",
               question: "Name a vector the map only stretches.", teachAnyway: false };

async function open(first: LessonViewDto) {
  api.lessonTurn.mockResolvedValueOnce(first);
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
}

it("while a question is prepared it says so, offers Teach it anyway, and checks back until it opens", async () => {
  vi.useFakeTimers();
  await open(lesson({ probe: PREPARING }));
  expect(screen.getByTestId("lesson-probe-preparing").textContent).toContain("Preparing a question on this…");
  api.lessonView.mockResolvedValueOnce(lesson({ probe: OPEN }));
  await act(async () => { vi.advanceTimersByTime(PROBE_POLL_MS); });
  expect(api.lessonView).toHaveBeenCalledWith({ lessonId: "les1" });
  expect(screen.getByTestId("lesson-probe").textContent).toContain("Name a vector the map only stretches.")
  // Open: on your own, the reply box away.
  expect(screen.queryByLabelText("Reply to the teacher")).toBeNull();
});

it("Teach it anyway retires the question and the lesson goes on", async () => {
  await open(lesson({ probe: PREPARING }));
  api.lessonTurn.mockResolvedValueOnce(lesson({ probe: null }));
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-teach-anyway")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "teach_anyway", lessonId: "les1" });
  expect(screen.queryByTestId("lesson-probe-preparing")).toBeNull();
});

it("an open question is answered on its own, the tap only after a draft, and its grade lands in the feed", async () => {
  await open(lesson({ probe: OPEN }));
  expect(screen.queryByTestId("lesson-probe-tap")).toBeNull();
  fireEvent.change(screen.getByLabelText("Your answer to the question"), { target: { value: "(1, 0)" } });
  fireEvent.click(screen.getByText("3"));
  api.lessonTurn.mockResolvedValueOnce(lesson({
    probe: null, feed: [{ kind: "probe_result", probeRef: "p1", result: "right", graderFeedback: "Yes." }] }));
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-probe-submit")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "answer_probe", lessonId: "les1", probeRef: "p1",
                                                    answer: "(1, 0)", tap: 3 });
  expect(screen.getByTestId("lesson-probe-result").textContent).toContain("right");
  expect(screen.getByLabelText("Reply to the teacher")).toBeTruthy();
});

const GOAL: LessonGoalDto = {
  status: "ready", goalKey: "lesson_goal:x", message: null,
  topics: [{ learningObjectId: "lo_eigen", title: "Eigenvalues", phrase: "eigenvalues" }],
  unmatched: [{ phrase: "when diagonalization fails", proposedTitle: "When diagonalization fails",
                proposedStatement: "When a matrix has too few eigenvectors." }],
  subjectId: "linear-algebra", subjects: [{ subjectId: "linear-algebra", title: "Linear algebra" }],
};

it("a typed goal lists what it covers, offers each leftover once, and starts with the learner's yes", async () => {
  await act(async () => {
    render(<LessonScreen entry={{ kind: "typed" }} onClose={vi.fn()} onError={vi.fn()} />);
  });
  expect(api.lessonTurn).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("What do you want to learn?"),
                   { target: { value: "how do I find eigenvalues, and when diagonalization fails" } });
  api.lessonGoal.mockResolvedValueOnce(GOAL);
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-goal-find")); });
  expect(screen.getByTestId("lesson-goal-topics").textContent).toContain("Eigenvalues");
  const leftover = screen.getByTestId("lesson-goal-unmatched");
  expect(leftover.textContent).toContain("Not in your books yet: “when diagonalization fails”. Add it as a topic?");
  fireEvent.click(screen.getByText("Yes"));
  expect(leftover.textContent).toContain("taught from LearnLoop's model");
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-goal-start-button")); });
  expect(api.lessonTurn).toHaveBeenCalledWith({
    action: "open", entry: "typed_goal", goalText: "how do I find eigenvalues, and when diagonalization fails",
    addTopics: ["when diagonalization fails"], subjectId: "linear-algebra" });
});

it("no to every leftover still starts on what the books cover", async () => {
  await act(async () => {
    render(<LessonScreen entry={{ kind: "typed" }} onClose={vi.fn()} onError={vi.fn()} />);
  });
  fireEvent.change(screen.getByLabelText("What do you want to learn?"), { target: { value: "eigenvalues" } });
  api.lessonGoal.mockResolvedValueOnce(GOAL);
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-goal-find")); });
  fireEvent.click(screen.getByText("No"));
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-goal-start-button")); });
  expect(api.lessonTurn).toHaveBeenCalledWith({ action: "open", entry: "typed_goal", goalText: "eigenvalues",
                                                addTopics: [] });
});
