// A pad's cells share one session: the kernel starts on the first ⇧↵, an edit runs in the live kernel, a new
// shape (or a stopped session) reopens the frame, and each cell's header reads its own run.
import { beforeEach, describe, expect, it } from "vitest";
import type { NotebookSessionDto } from "../../../api/dto";
import { MARIMO_CELL_INSERT, MARIMO_CELL_ROW, notebookMenuRequest } from "./menuBridge";
import {
  cellShape,
  cellStateLine,
  needsOpen,
  notePadSession,
  noteRunPending,
  padNotebook,
  resetPadNotebooksForTests,
  startPadNotebook,
} from "./padNotebooks";

function session(state: NotebookSessionDto["state"], extra: Partial<NotebookSessionDto> = {}): NotebookSessionDto {
  return { version: 1, sessionId: "nbs_1", owner: "pad:p1", state, stopReason: null, error: null, restarts: 0, framesAttached: 1,
    cells: [], startSeconds: [], frameUrl: "http://127.0.0.1:1/s/x/", memoryBytes: null, ...extra };
}

beforeEach(() => resetPadNotebooksForTests());

describe("a pad's notebook", () => {
  it("reads the cells' shape from the pad's blocks", () => {
    expect(cellShape([{ blockId: "a", kind: "cell" }, { blockId: "t", kind: "text" }, { blockId: "b", kind: "cell" }])).toEqual(["a", "b"]);
  });

  it("says Ready to run until the first ⇧↵, then starting, then Finished", () => {
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("Ready to run");
    expect(needsOpen(padNotebook("p1"), ["a"])).toBe(true);
    startPadNotebook("p1", ["a"]);
    noteRunPending("p1", "a");
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("Starting Python…");
    notePadSession("p1", session("ready", { padCells: { a: "c_a" }, cellRuns: { c_a: { status: "idle", ms: 41.6, error: false } } }));
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("Finished");
    expect(padNotebook("p1").pending).toEqual({});
  });

  it("keeps the names from the open when a status reading carries none", () => {
    startPadNotebook("p1", ["a"]);
    notePadSession("p1", session("ready", { padCells: { a: "c_a" } }));
    notePadSession("p1", session("ready", { cellRuns: { c_a: { status: "running", ms: null, error: false } } }));
    expect(padNotebook("p1").names).toEqual({ a: "c_a" });
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("running…");
  });

  it("runs an edit in the live kernel, but reopens for a new shape or a stopped session", () => {
    startPadNotebook("p1", ["a"]);
    notePadSession("p1", session("ready", { padCells: { a: "c_a" } }));
    expect(needsOpen(padNotebook("p1"), ["a"])).toBe(false);
    expect(needsOpen(padNotebook("p1"), ["a", "b"])).toBe(true);
    expect(needsOpen(padNotebook("p1"), ["b", "a"])).toBe(true);
    const generation = padNotebook("p1").generation;
    startPadNotebook("p1", ["a", "b"]);
    expect(padNotebook("p1").generation).toBe(generation + 1);
    notePadSession("p1", session("stopped", { stopReason: "idle" }));
    expect(needsOpen(padNotebook("p1"), ["a", "b"])).toBe(true);
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("Python paused · ⇧↵ (Shift+Enter) resumes it");
  });

  it("says when a cell raised and when a run could not be sent", () => {
    startPadNotebook("p1", ["a"]);
    notePadSession("p1", session("ready", { padCells: { a: "c_a" }, cellRuns: { c_a: { status: "idle", ms: 3, error: true } } }));
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("Code didn’t finish. Check your code and run it again.");
    noteRunPending("p1", "a", "couldn't run: no window shows the notebook");
    expect(cellStateLine(padNotebook("p1"), "a")).toBe("couldn't run: no window shows the notebook");
  });

  it("keeps each pad's state apart", () => {
    startPadNotebook("p1", ["a"]);
    expect(padNotebook("p2").started).toBe(false);
  });
});

describe("the menu's marimo row and the frame's right-click", () => {
  it("inserts an empty cell of the learner's", () => {
    expect(MARIMO_CELL_INSERT).toEqual({ kind: "cell", provenance: "learner", bodyMd: "", payload: {} });
    expect(MARIMO_CELL_ROW).toMatchObject({ key: "m", glyph: "◆", label: "Python cell" });
  });

  it("labels the pad menu for the notebook's owner", () => {
    const menu = { ll: "menu" as const, text: "softmax", rect: null, x: 10, y: 20 };
    expect(notebookMenuRequest(menu, "lesson:l1")).toMatchObject({ lessonId: "l1", padId: null, label: "the lesson",
      insertLabel: "add under this lesson (the notebook stays as the teacher made it)", text: "softmax", x: 10, y: 20 });
    expect(notebookMenuRequest(menu, "pad:p1")).toMatchObject({ padId: "p1", label: "your pad" });
    expect(notebookMenuRequest({ ll: "click" }, "pad:p1")).toBeNull();
  });
});
