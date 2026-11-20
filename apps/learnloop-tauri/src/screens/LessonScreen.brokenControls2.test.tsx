// Broken controls, second round (UX journey audit part 2): the lesson screen's Close says whether a lesson was
// left open (so the shell can say where it went), and the learner's reply stays on screen while the teacher writes.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { LessonViewDto } from "../api/dto";
import { LessonScreen } from "./LessonScreen";

const { api } = vi.hoisted(() => ({
  api: { lessonTurn: vi.fn(), lessonView: vi.fn(), lessonActivity: vi.fn(), lessonGoal: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function lesson(overrides: Partial<LessonViewDto> = {}): LessonViewDto {
  return {
    version: 1, lessonId: "les1", goal: "Dot product", learningObjectIds: ["lo_dot"], closed: false,
    closeReason: null,
    feed: [{ kind: "message", text: "Here is the map.", choices: [] }],
    plan: [{ id: "n1", statement: "Project onto a unit direction.", position: "current" }],
    openCheck: null, openPrediction: null, quickCheck: { learningObjectIds: ["lo_dot"] },
    inspector: { doctrine: "teacher_doctrine_v1", route: "chatgpt_medium", model: "m", forecasts: [] },
    ...overrides,
  };
}

async function open(first: LessonViewDto, onClose = vi.fn()) {
  api.lessonTurn.mockResolvedValueOnce(first);
  const onError = vi.fn();
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_dot"] }}
                         onClose={onClose} onError={onError} />);
  });
  return { onClose, onError };
}

it("UX-14: Close on a lesson still open says it was kept, so the shell can say where it went", async () => {
  const { onClose } = await open(lesson());
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(onClose).toHaveBeenCalledWith(true);
});

it("UX-14: Close on a lesson that has ended, or before one opened, keeps nothing", async () => {
  const { onClose } = await open(lesson({ closed: true, closeReason: "learner_stop" }));
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(onClose).toHaveBeenCalledWith(false);
  cleanup();
  const typedClose = vi.fn();
  await act(async () => {
    render(<LessonScreen entry={{ kind: "typed" }} onClose={typedClose} onError={vi.fn()} />);
  });
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(typedClose).toHaveBeenCalledWith(false);
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

// UX-22 (lesson-1 #20-24): after Send the learner's reply vanished from the screen for the 31 to 83 s the teacher
// took to write ("I cannot see my own words"): the box was cleared and the thread shows a reply only once the turn
// comes back with it.
it("UX-22: a sent reply stays in the thread, marked as sent, while the teacher writes, and is shown once after", async () => {
  await open(lesson());
  const turn = deferred<LessonViewDto>();
  api.lessonTurn.mockReturnValueOnce(turn.promise);
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "I see the projection but not why it's perpendicular." } });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Send" })); });
  expect((screen.getByLabelText("Reply to the teacher") as HTMLTextAreaElement).value).toBe("");
  const sent = screen.getByTestId("lesson-learner-sent");
  expect(sent.textContent).toContain("I see the projection but not why it's perpendicular.");
  expect(sent.textContent).toContain("sent");
  await act(async () => {
    turn.resolve(lesson({ feed: [
      { kind: "message", text: "Here is the map.", choices: [] },
      { kind: "learner", text: "I see the projection but not why it's perpendicular.", checkRef: null },
      { kind: "message", text: "Because the leftover is orthogonal.", choices: [] }
    ] }));
  });
  expect(screen.queryByTestId("lesson-learner-sent")).toBeNull();
  expect(screen.getAllByText("I see the projection but not why it's perpendicular.")).toHaveLength(1);
});

it("UX-22: a turn that fails puts the reply back in the box, so nothing typed is lost", async () => {
  const { onError } = await open(lesson());
  api.lessonTurn.mockRejectedValueOnce({ code: "internal", message: "Something went wrong." });
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "my reply" } });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Send" })); });
  expect(onError).toHaveBeenCalled();
  expect(screen.queryByTestId("lesson-learner-sent")).toBeNull();
  expect((screen.getByLabelText("Reply to the teacher") as HTMLTextAreaElement).value).toBe("my reply");
});

it("UX-22: with the teacher unavailable, the reply stays in the thread until the saved lesson shows it, once", async () => {
  await open(lesson());
  const saved = deferred<LessonViewDto>();
  api.lessonView.mockReturnValueOnce(saved.promise);
  api.lessonTurn.mockRejectedValueOnce({ code: "teacher_unavailable", message: "The teacher isn't available right now.", details: {} });
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "my reply" } });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Send" })); });
  expect(screen.getByTestId("lesson-retry")).toBeTruthy();
  expect(screen.getByTestId("lesson-learner-sent").textContent).toContain("my reply");
  await act(async () => { saved.resolve(lesson({ feed: [{ kind: "message", text: "Here is the map.", choices: [] }, { kind: "learner", text: "my reply", checkRef: null }] })); });
  expect(screen.queryByTestId("lesson-learner-sent")).toBeNull();
  expect(screen.getAllByText("my reply")).toHaveLength(1);
});
