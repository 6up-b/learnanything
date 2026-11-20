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
