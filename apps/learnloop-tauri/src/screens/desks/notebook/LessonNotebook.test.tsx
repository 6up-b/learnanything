// A notebook lesson in its lesson window: the lesson's own session (owner lesson:<id>, no path: the sidecar opens
// the lesson's notebook), held cells released once their commit point is answered and never in a review, the frame
// read more often while a commit point waits, nothing opened by a paused window, and the frame's right-click
// labelled for the lesson.
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { LessonViewDto, NotebookLessonDto, NotebookSessionDto } from "../../../api/dto";
import { FIXTURE_LESSON_VIEW } from "../../../fixtures/desks/lessons";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { COMMIT_POLL_MS, LessonNotebook, lessonReleases, waitingOnCommit, type LessonNotebookApi } from "./LessonNotebook";
import { notebookMenuRequest } from "./menuBridge";
import { POLL_MS } from "./NotebookFrame";

vi.mock("../../../api/client", () => ({ api: {} }));

const POINT = { name: "commit_square", held: ["reveal_square"] };

function lesson(extra: Partial<NotebookLessonDto> = {}, committed = false): NotebookLessonDto {
  return { review: false, released: [], commitPoints: [{ ...POINT, committed }], ...extra };
}

function session(state: NotebookSessionDto["state"], lessonPart: NotebookLessonDto | undefined): NotebookSessionDto {
  return { version: 1, sessionId: "nbs_l", owner: "lesson:les_1", state, stopReason: null, error: null, restarts: 0, framesAttached: 1,
    cells: [], startSeconds: [], frameUrl: "http://127.0.0.1:40123/s/x/", memoryBytes: null, ...(lessonPart ? { lesson: lessonPart } : {}) };
}

function calls(reading: () => NotebookSessionDto): LessonNotebookApi & { released: string[][] } {
  const made = {
    released: [] as string[][],
    notebookOpen: vi.fn(async () => reading()),
    notebookStatus: vi.fn(async () => reading()),
    notebookRelease: vi.fn(async (input: { sessionId: string; cells: string[] }) => {
      made.released.push(input.cells);
      return { released: input.cells };
    }),
  };
  return made;
}

function Lesson({ api, view = FIXTURE_LESSON_VIEW, state = "active" }: { api: LessonNotebookApi; view?: LessonViewDto; state?: WindowState }) {
  return (
    <WindowScope lifecycle={{ windowId: "w1", state }} hub={DIRECT_HUB}>
      <LessonNotebook lessonId="les_1" view={view} calls={api} />
    </WindowScope>
  );
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

async function settle() {
  await act(async () => {
    for (let i = 0; i < 4; i += 1) await Promise.resolve();
  });
}

it("releases what an answered commit point holds, once, and nothing before", () => {
  expect(lessonReleases(session("ready", lesson()))).toEqual([]);
  expect(lessonReleases(session("ready", lesson({}, true)))).toEqual(["reveal_square"]);
  expect(lessonReleases(session("ready", lesson({ released: ["reveal_square"] }, true)))).toEqual([]);
  expect(lessonReleases(session("ready", lesson({ review: true }, true)))).toEqual([]);
  expect(lessonReleases(session("restarting", lesson({}, true)))).toEqual([]);
  expect(lessonReleases(session("ready", undefined))).toEqual([]);
  expect(waitingOnCommit(session("ready", lesson()))).toBe(true);
  expect(waitingOnCommit(session("ready", lesson({}, true)))).toBe(false);
  expect(waitingOnCommit(session("ready", lesson({ review: true })))).toBe(false);
});

it("opens the lesson's own session, reads it often while a commit point waits, and releases at the commit", async () => {
  let now = session("ready", lesson());
  const api = calls(() => now);
  render(<Lesson api={api} />);
  await settle();
  expect(api.notebookOpen).toHaveBeenCalledWith({ owner: "lesson:les_1", view: "app" });
  expect(api.released).toEqual([]);
  now = session("ready", lesson({}, true));
  await act(async () => vi.advanceTimersByTime(COMMIT_POLL_MS));
  await settle();
  expect(api.notebookStatus).toHaveBeenCalledTimes(1);
  expect(api.released).toEqual([["reveal_square"]]);
  now = session("ready", lesson({ released: ["reveal_square"] }, true));
  await act(async () => vi.advanceTimersByTime(COMMIT_POLL_MS));
  await settle();
  expect(api.notebookStatus).toHaveBeenCalledTimes(1);  // nothing waits now: back to the frame's slow reading
  await act(async () => vi.advanceTimersByTime(POLL_MS.ready));
  await settle();
  expect(api.notebookStatus).toHaveBeenCalledTimes(2);
  expect(api.released).toEqual([["reveal_square"]]);
});

it("a review says so and releases nothing, even with a commit recorded", async () => {
  const api = calls(() => session("ready", lesson({ review: true }, true)));
  render(<Lesson api={api} view={{ ...FIXTURE_LESSON_VIEW, closed: true }} />);
  await settle();
  expect(screen.getByText("Review the notebook from this lesson.")).toBeTruthy();
  await act(async () => vi.advanceTimersByTime(POLL_MS.ready));
  await settle();
  expect(api.released).toEqual([]);
});

it("a paused lesson window opens nothing until it is live again", async () => {
  const api = calls(() => session("ready", lesson()));
  const view = render(<Lesson api={api} state="offscreen" />);
  await settle();
  await act(async () => vi.advanceTimersByTime(POLL_MS.ready * 2));
  expect(api.notebookOpen).not.toHaveBeenCalled();
  view.rerender(<Lesson api={api} state="active" />);
  await settle();
  expect(api.notebookOpen).toHaveBeenCalledTimes(1);
});

it("the frame's right-click opens the pad menu labelled for the lesson, its inserts under the lesson", () => {
  const request = notebookMenuRequest({ ll: "menu", text: "softmax", rect: null, x: 4, y: 8 }, "lesson:les_1");
  expect(request).toMatchObject({ lessonId: "les_1", padId: null, label: "the lesson",
    insertLabel: "add under this lesson (the notebook stays as the teacher made it)" });
});
