// The client workspace model (spec §18.2): every op, pairs capped at two, expel, open beside without
// duplicates, close and undo, and the versions each op expects (the server's write protocol, §3.4).
import { describe, expect, it } from "vitest";
import type { ContentRefDto, DeskStateDto } from "../../../api/dto";
import {
  PAIR_COPY,
  applyDeskOp,
  closeWindow,
  createDesk,
  deskById,
  findDuplicate,
  focusAlong,
  focusPane,
  focusedWindowId,
  fromDeskState,
  moveFocused,
  moveWindowTo,
  openBeside,
  pairFocused,
  rangeCovers,
  setFocus,
  undoClose,
  unpairFocused,
  type Workspace,
} from "./workspace";

const book = (id: string): ContentRefDto => ({ kind: "source", sourceId: `src_${id}`, extractionId: `ext_${id}`, view: "render" });
const video = (id: string): ContentRefDto => ({ kind: "video", sourceId: `src_${id}`, extractionId: `ext_${id}` });

/** One desk "d1" at version 5 with windows w1..wN, each alone in its slot, w1 focused. */
function deskWith(count: number, focus = "w1"): Workspace {
  const state: DeskStateDto = {
    version: 1,
    desks: [{
      deskId: "d1", title: "softmax", position: "a", focusWindowId: focus, goalId: null,
      companion: { dock: "br", shown: false }, version: 5,
      slots: Array.from({ length: count }, (_, index) => ({
        slot: index,
        windows: [{ windowId: `w${index + 1}`, pane: 0, kind: "source", active: true, content: book(String(index + 1)), view: {} }],
      })),
    }],
    runningPadIds: [],
    serverSeq: [],
  };
  return fromDeskState(state);
}

function ids(ws: Workspace, deskId = "d1"): string[][] {
  return deskById(ws, deskId)!.slots;
}

let counter = 0;
const mint = () => `new${++counter}`;

describe("reading desk.state", () => {
  it("orders desks by position then id, and slots and panes by their numbers", () => {
    const ws = fromDeskState({
      version: 1,
      runningPadIds: [],
      serverSeq: [],
      desks: [
        { deskId: "b", title: "B", position: "m", focusWindowId: null, goalId: null, companion: { dock: "br", shown: false }, version: 1, slots: [] },
        {
          deskId: "a", title: "A", position: "m", focusWindowId: null, goalId: null, companion: { dock: "br", shown: false }, version: 1,
          slots: [
            { slot: 1, windows: [{ windowId: "y", pane: 0, kind: "source", active: true, content: book("y"), view: {} }] },
            { slot: 0, windows: [
              { windowId: "x2", pane: 1, kind: "video", active: false, content: video("x2"), view: {} },
              { windowId: "x1", pane: 0, kind: "source", active: true, content: book("x1"), view: {} },
            ] },
          ],
        },
        { deskId: "c", title: "C", position: "a", focusWindowId: null, goalId: null, companion: { dock: "br", shown: false }, version: 1, slots: [] },
      ],
    });
    expect(ws.desks.map((desk) => desk.deskId)).toEqual(["c", "a", "b"]);
    expect(ids(ws, "a")).toEqual([["x1", "x2"], ["y"]]);
    expect(focusedWindowId(ws, deskById(ws, "a"))).toBe("x1");
  });
});

describe("open beside", () => {
  it("inserts right of the focus, focuses it, and stamps each op with the version it expects", () => {
    const ws = deskWith(3, "w2");
    const step = openBeside(ws, "d1", book("9"), () => "w9");
    expect(ids(step.ws)).toEqual([["w1"], ["w2"], ["w9"], ["w3"]]);
    expect(focusedWindowId(step.ws, deskById(step.ws, "d1"))).toBe("w9");
    expect(step.ops.map((op) => [op.op, op.expectedVersion])).toEqual([["open_window", 5], ["set_focus", 6]]);
    expect(step.ops[0]).toMatchObject({ afterWindowId: "w2", windowId: "w9" });
    expect(deskById(step.ws, "d1")!.version).toBe(7);
  });

  it("opens nothing new when the source is already on the desk: it focuses that window", () => {
    const ws = deskWith(3, "w1");
    const step = openBeside(ws, "d1", { kind: "source", sourceId: "src_3", extractionId: "ext_3", view: "pdf" }, mint);
    expect(step.existed).toBe(true);
    expect(step.windowId).toBe("w3");
    expect(ids(step.ws)).toEqual([["w1"], ["w2"], ["w3"]]);
    expect(step.ops.map((op) => op.op)).toEqual(["set_focus"]);
  });

  it("a ranged window covers only its range; another passage of the book opens beside", () => {
    let ws = deskWith(1);
    ws = applyDeskOp(ws, {
      op: "open_window", deskId: "d1", windowId: "r", afterWindowId: "w1",
      content: { kind: "source", sourceId: "src_b", extractionId: "ext_b", range: { fromSpanId: "s2", toSpanId: "s4" } },
    });
    const order = (span: string) => ["s1", "s2", "s3", "s4", "s5"].indexOf(span);
    expect(findDuplicate(ws, deskById(ws, "d1")!, book("b"), "s3", order)).toBe("r");
    expect(findDuplicate(ws, deskById(ws, "d1")!, book("b"), "s5", order)).toBeNull();
    expect(rangeCovers({ kind: "source", sourceId: "x", extractionId: "y", range: { fromSpanId: "s2", toSpanId: "s4" } }, "s3")).toBe(false);
    expect(rangeCovers(book("x"), "anything")).toBe(true);
  });
});

describe("pairs", () => {
  it("alt+, stacks the focus with its right neighbour; the focus is the active pane", () => {
    const step = pairFocused(deskWith(3, "w1"), "d1");
    expect(ids(step.ws)).toEqual([["w1", "w2"], ["w3"]]);
    expect(step.ws.windows.w1.active).toBe(true);
    expect(step.ws.windows.w2.active).toBe(false);
    expect(step.ops).toEqual([{ op: "pair", deskId: "d1", windowId: "w1", expectedVersion: 5 }]);
  });

  it("a slot holds at most two windows, and nothing to the right says so", () => {
    const paired = pairFocused(deskWith(3, "w1"), "d1").ws;
    const third = pairFocused(paired, "d1");
    expect(third.ops).toEqual([]);
    expect(third.notice).toBe(PAIR_COPY.full);
    const last = pairFocused(deskWith(2, "w2"), "d1");
    expect(last.ops).toEqual([]);
    expect(last.notice).toBe(PAIR_COPY.nothingRight);
    // The neighbour already a pair: still two at most.
    let ws = pairFocused(deskWith(3, "w2"), "d1").ws;
    ws = setFocus(ws, "d1", "w1").ws;
    expect(pairFocused(ws, "d1").notice).toBe(PAIR_COPY.full);
  });

  it("alt+. gives the active pane its own slot right after the pair and keeps its focus", () => {
    let ws = pairFocused(deskWith(3, "w1"), "d1").ws;
    ws = setFocus(ws, "d1", "w2").ws;
    expect(ws.windows.w2.active).toBe(true);
    const step = unpairFocused(ws, "d1");
    expect(ids(step.ws)).toEqual([["w1"], ["w2"], ["w3"]]);
    expect(focusedWindowId(step.ws, deskById(step.ws, "d1"))).toBe("w2");
    expect(step.ws.windows.w1.active).toBe(true);
  });

  it("alt+j/k moves between the panes of a pair, and past the end hands over to the desks", () => {
    const ws = pairFocused(deskWith(2, "w1"), "d1").ws;
    const down = focusPane(ws, "d1", 1)!;
    expect(focusedWindowId(down.ws, deskById(down.ws, "d1"))).toBe("w2");
    expect(down.ops.map((op) => op.op)).toEqual(["set_active_pane", "set_focus"]);
    expect(focusPane(down.ws, "d1", 1)).toBeNull();
    expect(focusPane(deskWith(2), "d1", 1)).toBeNull();
  });
});

describe("moving, focusing, closing", () => {
  it("alt+[ / alt+] move the focused window one slot; the ends do nothing", () => {
    const right = moveFocused(deskWith(3, "w1"), "d1", 1);
    expect(ids(right.ws)).toEqual([["w2"], ["w1"], ["w3"]]);
    expect(moveFocused(deskWith(3, "w1"), "d1", -1).ops).toEqual([]);
    expect(moveFocused(deskWith(3, "w3"), "d1", 1).ops).toEqual([]);
  });

  it("a shelf drag moves a window to the slot it is dropped on", () => {
    expect(ids(moveWindowTo(deskWith(4), "d1", "w4", 0).ws)).toEqual([["w4"], ["w1"], ["w2"], ["w3"]]);
    expect(moveWindowTo(deskWith(4), "d1", "w4", 3).ops).toEqual([]);
  });

  it("alt+h/l moves the focus along the strip", () => {
    const step = focusAlong(deskWith(3, "w2"), "d1", 1);
    expect(focusedWindowId(step.ws, deskById(step.ws, "d1"))).toBe("w3");
    expect(focusAlong(step.ws, "d1", 1).ops).toEqual([]);
  });

  it("closing the focus moves it to the window now in its slot; undo puts it back in place", () => {
    const closed = closeWindow(deskWith(3, "w2"), "d1", "w2");
    expect(ids(closed.ws)).toEqual([["w1"], ["w3"]]);
    expect(focusedWindowId(closed.ws, deskById(closed.ws, "d1"))).toBe("w3");
    expect(closed.ops.map((op) => [op.op, op.expectedVersion])).toEqual([["close_window", 5], ["set_focus", 6]]);
    const back = undoClose(closed.ws, "d1");
    expect(ids(back.ws)).toEqual([["w1"], ["w2"], ["w3"]]);
    expect(focusedWindowId(back.ws, deskById(back.ws, "d1"))).toBe("w2");
    expect(back.ops.map((op) => op.op)).toEqual(["reopen_window", "set_focus"]);
    expect(back.ws.closed.d1).toEqual([]);
  });

  it("closing one pane of a pair leaves the other alone in the slot", () => {
    const ws = pairFocused(deskWith(2, "w1"), "d1").ws;
    const closed = closeWindow(ws, "d1", "w1");
    expect(ids(closed.ws)).toEqual([["w2"]]);
    expect(closed.ws.windows.w2.active).toBe(true);
  });
});

describe("desks", () => {
  it("a new desk sorts after the others and starts at version 1", () => {
    const step = createDesk(deskWith(1), "d2", "attention");
    expect(step.ws.desks.map((desk) => desk.deskId)).toEqual(["d1", "d2"]);
    expect(step.ops[0]).toMatchObject({ op: "create_desk", deskId: "d2", title: "attention" });
    expect(step.ops[0].expectedVersion).toBeUndefined();
    expect(deskById(step.ws, "d2")!.version).toBe(1);
  });

  it("a transfer names both desks' versions and leaves the window alone on the destination", () => {
    let ws = createDesk(deskWith(2), "d2", "other").ws;
    ws = applyDeskOp(ws, { op: "move_to_desk", deskId: "d1", windowId: "w1", toDeskId: "d2", expectedVersion: 5, toExpectedVersion: 1 });
    expect(ids(ws, "d1")).toEqual([["w2"]]);
    expect(ids(ws, "d2")).toEqual([["w1"]]);
    expect(deskById(ws, "d1")!.version).toBe(6);
    expect(deskById(ws, "d2")!.version).toBe(2);
    expect(ws.windows.w1.deskId).toBe("d2");
  });
});
