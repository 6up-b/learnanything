// "Waiting you can see" (docs/reviews/ux-waiting.md, the owner's case 3): a
// Teacher lesson's turn says "The teacher is writing…" through the shared
// waiting line, with what is normal for a long wait; finding a typed goal in
// the books says that instead, since no teacher is writing then.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { LessonViewDto } from "../api/dto";
import { WAIT_LATER_MS } from "../components/Waiting";
import { LessonScreen } from "./LessonScreen";

const { api } = vi.hoisted(() => ({
  api: { lessonTurn: vi.fn(), lessonView: vi.fn(), lessonActivity: vi.fn(), lessonGoal: vi.fn(), readerLogActivity: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

function lesson(): LessonViewDto {
  return {
    version: 1, lessonId: "les1", goal: "Eigenvalues", learningObjectIds: ["lo_eigen"], closed: false, closeReason: null,
    feed: [{ kind: "message", text: "Here is the map.", choices: [] }],
    plan: [{ id: "n1", statement: "An eigenvalue scales its eigenvector.", position: "current" }],
    openCheck: null, openPrediction: null, quickCheck: { learningObjectIds: ["lo_eigen"] },
    inspector: { doctrine: "teacher_doctrine_v1", route: "chatgpt_medium", model: "m", forecasts: [] },
  } as LessonViewDto;
}
function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
async function advance(ms: number) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => { cleanup(); vi.clearAllMocks(); vi.useRealTimers(); });

it("a lesson turn: nothing before the delay, 'The teacher is writing…', then what is normal, gone when the turn lands", async () => {
  const turn = deferred<LessonViewDto>();
  api.lessonTurn.mockReturnValueOnce(turn.promise);
  render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                       onClose={vi.fn()} onQuickCheck={vi.fn()} onError={vi.fn()} />);
  await advance(300);
  expect(screen.queryByText("The teacher is writing…")).toBeNull();
  await advance(100);
  expect(screen.getByTestId("lesson-wait").textContent).toBe("◐ The teacher is writing…");
  await advance(WAIT_LATER_MS);
  expect(screen.getByTestId("lesson-wait-later").textContent).toBe("This can take a minute or two.");
  turn.resolve(lesson());
  await advance(0);
  expect(screen.getByText("Here is the map.")).toBeTruthy();
  expect(screen.queryByTestId("lesson-wait")).toBeNull();
});

it("finding a typed goal says it looks in the books, and claims no time", async () => {
  const found = deferred<unknown>();
  api.lessonGoal.mockReturnValueOnce(found.promise);
  render(<LessonScreen entry={{ kind: "typed" }} onClose={vi.fn()} onError={vi.fn()} />);
  fireEvent.change(screen.getByLabelText("What do you want to learn?"), { target: { value: "eigenvalues" } });
  fireEvent.click(screen.getByTestId("lesson-goal-find"));
  await advance(400);
  expect(screen.getByTestId("lesson-wait").textContent).toBe("◐ Looking in your books…");
  await advance(WAIT_LATER_MS);
  expect(screen.queryByTestId("lesson-wait-later")).toBeNull();
});
