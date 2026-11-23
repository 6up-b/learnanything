// Lessons as windows, the pure part (spec §11.1): a stack's item keys, the tab's words, where a lesson already is,
// the op that puts one in a stack, and the summaries' store (one read per tick, openings, reveals).
import { describe, expect, it, vi } from "vitest";
import type { LessonSummaryDto } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { fromDeskState } from "../model/workspace";
import { LessonDesk } from "./host";
import { addLessonToStack, findLesson, lessonMedium, lessonOfKey, lessonTabMeta, lessonTabTitle, modeButtons, stackItemKeys, stackWindowOf } from "./model";

const SUMMARY: LessonSummaryDto = {
  lessonId: "les_1", title: "eigenvalues", goal: null, openedAt: "2026-11-21T10:00:00Z", closed: true, closeReason: "goal_reached",
  learningObjectIds: ["lo_eigen"], madeFrom: "selection", additionsPadId: null,
};

describe("a stack's items", () => {
  it("are its pads, its lessons, pads added through its view, then openings not yet among them", () => {
    const keys = stackItemKeys([{ kind: "pad", padId: "p1" }, { kind: "lesson", lessonId: "les_1" }], { addedPads: ["p2", "p1"] },
      ["lesson-opening:1", "lesson:les_1"]);
    expect(keys).toEqual(["p1", "lesson:les_1", "p2", "lesson-opening:1"]);
    expect(lessonOfKey("lesson:les_1")).toBe("les_1");
    expect(lessonOfKey("lesson-opening:1")).toBeNull();
    expect(lessonOfKey("p1")).toBeNull();
  });
});

describe("a lesson tab's words", () => {
  it("reads “Teacher lesson · <topic>” and “made <date> from your <what>”", () => {
    expect(lessonTabTitle("eigenvalues")).toBe("Teacher lesson · eigenvalues");
    expect(lessonTabTitle("  ")).toBe("Teacher lesson");
    expect(lessonTabMeta(SUMMARY)).toBe("made 21 Nov from your selection");
    expect(lessonTabMeta({ ...SUMMARY, madeFrom: "check" })).toBe("made 21 Nov from your check");
    expect(lessonTabMeta({ ...SUMMARY, madeFrom: "suggestion", openedAt: null })).toBe("made from today's suggestion");
    expect(lessonTabMeta(null)).toBe("");
  });

  it("offers review (or “lesson” while it is open) and your additions; never redo or extend before RD9c", () => {
    expect(modeButtons(true).map((each) => each.label)).toEqual(["review", "your additions"]);
    expect(modeButtons(false).map((each) => each.label)).toEqual(["lesson", "your additions"]);
    expect(lessonMedium({ medium: "notebook" })).toBe("notebook");
    expect(lessonMedium({})).toBe("lesson");
    expect(lessonMedium(null)).toBe("lesson");
  });
});

describe("where a lesson goes on a desk", () => {
  it("joins the desk's stack by one add_to_stack (none when it is there) and the stack takes the focus unless told not to", () => {
    const ws = fromDeskState(new FixtureDeskServer().state());
    const stack = stackWindowOf(ws, "fx_desk_softmax") as string;
    expect(stack).toBe("fx_w_pads");
    expect(findLesson(ws, "fx_desk_softmax", "les_1")).toBeNull();
    const step = addLessonToStack(ws, "fx_desk_softmax", stack, "les_1");
    expect(step.ops.map((op) => op.op)).toEqual(["add_to_stack", "set_focus"]);
    expect(step.ops[0]).toMatchObject({ entry: { kind: "lesson", lessonId: "les_1" }, windowId: "fx_w_pads" });
    expect(findLesson(step.ws, "fx_desk_softmax", "les_1")).toEqual({ windowId: "fx_w_pads", inStack: true });
    expect(addLessonToStack(step.ws, "fx_desk_softmax", stack, "les_1", { focus: false }).ops).toEqual([]);
    expect(addLessonToStack(ws, "fx_desk_softmax", stack, "les_1", { focus: false }).ops.map((op) => op.op)).toEqual(["add_to_stack"]);
  });

  it("finds a lesson in a window of its own before any stack", () => {
    const state = new FixtureDeskServer().state();
    const desk = state.desks.find((each) => each.deskId === "fx_desk_softmax")!;
    desk.slots.push({ slot: desk.slots.length, windows: [{ windowId: "w_lesson", pane: 0, kind: "lesson", active: true, view: {}, content: { kind: "lesson", lessonId: "les_1" } }] } as never);
    expect(findLesson(fromDeskState(state), "fx_desk_softmax", "les_1")).toEqual({ windowId: "w_lesson", inStack: false });
  });
});

describe("the desks' lessons store", () => {
  it("reads every summary asked for in one tick in one call, and each only once", async () => {
    const list = vi.fn(async (input: { lessonIds?: string[] }) => ({ lessons: (input.lessonIds ?? []).map((lessonId) => ({ ...SUMMARY, lessonId })) }));
    const desk = new LessonDesk({ list }, () => undefined);
    expect(desk.summary("les_1")).toBeNull();
    expect(desk.summary("les_2")).toBeNull();
    expect(desk.summary("les_1")).toBeNull();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(list).toHaveBeenCalledTimes(1);
    expect(list.mock.calls[0][0]).toEqual({ lessonIds: ["les_1", "les_2"] });
    expect(desk.summary("les_2")?.title).toBe("eigenvalues");
    expect(list).toHaveBeenCalledTimes(1);
  });

  it("an opening is shown under its key, then under its lesson's (with the same React key), and is done once the stack holds it", () => {
    const onOpened = vi.fn();
    const desk = new LessonDesk({ list: async () => ({ lessons: [] }) }, onOpened);
    const key = desk.open("w1", { kind: "open", entry: "reader_selection", selection: { extractionId: "e", spanIds: ["s"] } });
    expect(desk.openingsFor("w1")).toEqual([key]);
    expect(desk.openingTitle(key)).toBe("your selection");
    expect(desk.takeReveal("w1", [key])).toBe(key);
    desk.opened(key, "les_9");
    desk.opened(key, "les_9");
    expect(onOpened).toHaveBeenCalledTimes(1);
    expect(desk.openingsFor("w1")).toEqual(["lesson:les_9"]);
    expect(desk.reactKey("lesson:les_9")).toBe(key);
    // A later mount reads the stored lesson: it is never opened twice.
    expect(desk.entryFor("lesson:les_9")).toEqual({ kind: "resume", lessonId: "les_9" });
    desk.landed("w1", ["les_9"]);
    expect(desk.openingsFor("w1")).toEqual([]);
  });
});
