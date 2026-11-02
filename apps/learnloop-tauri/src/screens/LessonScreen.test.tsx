import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { LessonViewDto } from "../api/dto";
import { LessonScreen } from "./LessonScreen";

const { api } = vi.hoisted(() => ({
  api: { lessonTurn: vi.fn(), lessonView: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function lesson(overrides: Partial<LessonViewDto> = {}): LessonViewDto {
  return {
    version: 1, lessonId: "les1", goal: "Eigenvalues", learningObjectIds: ["lo_eigen"], closed: false,
    closeReason: null,
    feed: [{ kind: "message", text: "Here is the map.", choices: [] }],
    plan: [{ id: "n1", statement: "An eigenvalue scales its eigenvector.", position: "current" },
           { id: "n2", statement: "Find them.", position: "upcoming" }],
    openCheck: null, openPrediction: null, quickCheck: { learningObjectIds: ["lo_eigen"] },
    inspector: { doctrine: "teacher_doctrine_v1", route: "chatgpt_medium", model: "m", forecasts: [] },
    ...overrides,
  };
}

async function open(first: LessonViewDto, onQuickCheck = vi.fn()) {
  api.lessonTurn.mockResolvedValueOnce(first);
  const onError = vi.fn();
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onQuickCheck={onQuickCheck} onError={onError} />);
  });
  return { onError, onQuickCheck };
}

it("opens a lesson on the topic and shows the document and the map as positions", async () => {
  await open(lesson());
  expect(api.lessonTurn).toHaveBeenCalledWith({ action: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] });
  expect(screen.getByText("Here is the map.")).toBeTruthy();
  const map = screen.getByTestId("lesson-plan");
  expect(map.querySelector('[data-position="current"]')?.textContent).toContain("scales its eigenvector");
  expect(map.querySelector('[data-position="upcoming"]')).toBeTruthy();
});

it("offers the quick check at open, never prompting it", async () => {
  const { onQuickCheck } = await open(lesson());
  fireEvent.click(screen.getByTestId("lesson-quick-check"));
  expect(onQuickCheck).toHaveBeenCalledWith(["lo_eigen"]);
});

it("keeps a check collapsed until opened, shows the tap only after a draft, and sends thinking to the teacher", async () => {
  const withCheck = lesson({
    feed: [{ kind: "message", text: "Try it.", choices: [] },
           { kind: "check", checkRef: "c1", node: "n1", question: "What equation gives the eigenvalues?", form: "free",
             choices: [], unanchored: true }],
    openCheck: { checkRef: "c1", question: "What equation gives the eigenvalues?", form: "free", choices: [] },
  });
  await open(withCheck);
  expect(screen.queryByText("What equation gives the eigenvalues?")).toBeNull();
  fireEvent.click(screen.getByTestId("lesson-check-collapsed"));
  expect(screen.getByText("What equation gives the eigenvalues?")).toBeTruthy();
  expect(screen.queryByTestId("lesson-tap")).toBeNull();
  fireEvent.change(screen.getByLabelText("Your answer"), { target: { value: "det(A - tI) = 0" } });
  expect(screen.getByTestId("lesson-tap")).toBeTruthy();
  fireEvent.click(screen.getByText("4"));
  fireEvent.change(screen.getByLabelText("Your thinking (optional)"), { target: { value: "char poly" } });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByText("Submit answer")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "answer_check", lessonId: "les1", checkRef: "c1",
                                                    answer: "det(A - tI) = 0", tap: 4, thinking: "char poly" });
});

it("the close card promises only the checks that were set, and a plan outage keeps the lesson", async () => {
  await open(lesson({
    closed: true, closeReason: "goal_reached",
    feed: [{ kind: "close", reason: "goal_reached", recap: "Retrieve: det(A - tI) = 0.",
             delayedChecks: [{ learningObjectId: "lo_eigen", title: "Eigenvalues", purpose: "retention", due: "2099-01-01" }] }],
  }));
  const card = screen.getByTestId("lesson-close");
  expect(card.textContent).toContain("Lesson done.");
  expect(card.textContent).toContain("one question on Eigenvalues, on your own");
  expect(screen.queryByText("Send")).toBeNull();
});

it("a plan outage shows a plain line, not an error", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now." });
  const onError = vi.fn();
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={onError} />);
  });
  expect(screen.getByTestId("lesson-unavailable").textContent).toContain("isn't available");
  expect(onError).not.toHaveBeenCalled();
});

it("an opening that failed after the lesson was saved is resumed, never opened twice (review F11)", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now.",
                                         details: { lesson_id: "les1" } });
  api.lessonView.mockResolvedValueOnce(lesson({ feed: [] }));
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
  expect(api.lessonView).toHaveBeenCalledWith({ lessonId: "les1" });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "resume", lessonId: "les1" });
  expect(api.lessonTurn).toHaveBeenCalledTimes(2);
  expect(screen.getByText("Here is the map.")).toBeTruthy();
  expect(screen.queryByTestId("lesson-retry")).toBeNull();
});

it("an opening that saved nothing is repeated by Try again", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The plan is unavailable." });
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "open", entry: "learning_object",
                                                    learningObjectIds: ["lo_eigen"] });
  expect(screen.getByText("Here is the map.")).toBeTruthy();
});

it("a reply that hit an outage resumes the saved lesson", async () => {
  await open(lesson());
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now." });
  api.lessonView.mockResolvedValueOnce(lesson({ feed: [{ kind: "message", text: "Here is the map.", choices: [] },
                                                       { kind: "learner", text: "Go ahead.", checkRef: null }] }));
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "Go ahead." } });
  await act(async () => { fireEvent.click(screen.getByText("Send")); });
  expect(screen.getByText("Go ahead.")).toBeTruthy();
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "resume", lessonId: "les1" });
});
