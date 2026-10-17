// RW2a's pure step model (spec §5.1, §5.7; UX §5.1-5.3, S7): the default book
// visibility by entry, the local work list (insert after, delete, undo), the
// problem's title, the saved line, and the split's width rule (half the
// window, at least 480 px, remembered, stacked below 1,040 px).
import { expect, it } from "vitest";
import {
  BOOK_OPEN_ENTRIES,
  WORKBENCH_COPY,
  defaultBookVisible,
  deleteLocal,
  fromServer,
  insertAfter,
  liveSteps,
  problemTitle,
  restoreLocal,
  savedLabel,
} from "./stepModel";
import { MIN_WORKBENCH_WIDTH, NARROW_BREAKPOINT, clampSplitWidth, defaultSplitWidth, isNarrow } from "./splitWidth";
import type { WorkbenchStepDto } from "../../api/dto";

const step = (stepId: string, ordinal: number, bodyMd: string, kind: "step" | "stuck" = "step"): WorkbenchStepDto => ({
  stepId, chainId: `c_${stepId}`, ordinal, kind, bodyMd, deleted: false, createdAt: "2026-10-17T09:00:00Z",
  editedAt: "2026-10-17T09:00:00Z", versions: [],
});

it("the book starts open for working through, resuming and the Guide's exercise; hidden for checks and the plan", () => {
  expect([...BOOK_OPEN_ENTRIES].sort()).toEqual(["path_exercise", "resume", "work_through"]);
  expect(defaultBookVisible("work_through", "reader")).toBe(true);
  expect(defaultBookVisible("resume", "reader")).toBe(true);
  expect(defaultBookVisible("path_exercise", "reader")).toBe(true);
  for (const entry of ["check_me", "practice_this", "discriminating_problem", "plan"] as const) {
    expect(defaultBookVisible(entry, "reader")).toBe(false);
  }
  // Off the Reader there is no book beside the problem.
  expect(defaultBookVisible("work_through", "practice")).toBe(false);
  expect(defaultBookVisible("practice_screen", "practice")).toBe(false);
});

it("the server's steps become the local list in order, keyed by their chain", () => {
  const local = fromServer([step("b", 2, "two"), step("a", 1, "one")]);
  expect(local.map((entry) => [entry.key, entry.serverId, entry.body])).toEqual([["c_a", "a", "one"], ["c_b", "b", "two"]]);
});

it("a new step goes right after the one the learner pressed Enter in, or at the end", () => {
  let local = fromServer([step("a", 1, "one"), step("b", 2, "three")]);
  local = insertAfter(local, "c_a", { key: "k2", kind: "step" });
  expect(local.map((entry) => entry.key)).toEqual(["c_a", "k2", "c_b"]);
  local = insertAfter(local, null, { key: "k4", kind: "stuck" });
  expect(local.map((entry) => [entry.key, entry.kind])).toEqual([["c_a", "step"], ["k2", "step"], ["c_b", "step"], ["k4", "stuck"]]);
  expect(local[1].serverId).toBeNull();
});

it("a delete is kept as 'deleted · undo' until the learner leaves; undo brings it back", () => {
  let local = fromServer([step("a", 1, "one"), step("b", 2, "two")]);
  local = deleteLocal(local, "c_b");
  expect(local.find((entry) => entry.key === "c_b")?.deleted).toBe(true);
  expect(liveSteps(local).map((entry) => entry.body)).toEqual(["one"]);
  local = restoreLocal(local, "c_b");
  expect(liveSteps(local).map((entry) => entry.body)).toEqual(["one", "two"]);
});

it("the problem's title is its exercise number when the stem names one", () => {
  expect(problemTitle("Exercise 5.14 Let X be Uniform(-1, 0).")).toBe("Exercise 5.14");
  expect(problemTitle("Problem 3: show that…")).toBe("Problem 3");
  expect(problemTitle("Let X be Uniform(-1, 0) with probability p.")).toBe("this problem");
});

it("the saved line never says 'error' (UX §5.3)", () => {
  const now = Date.parse("2026-10-17T09:05:00Z");
  expect(savedLabel({ state: "saved", savedAt: "2026-10-17T09:04:50Z" }, now)).toBe("saved · just now");
  expect(savedLabel({ state: "saved", savedAt: "2026-10-17T09:03:00Z" }, now)).toBe("saved · 2 min ago");
  expect(savedLabel({ state: "retrying", savedAt: null }, now)).toBe("not saved yet — retrying · your text is safe in this window");
  expect(savedLabel({ state: "offline", savedAt: null }, now)).toBe("sidecar unreachable — keeping your steps here; they'll save when it's back");
  for (const line of Object.values(WORKBENCH_COPY)) expect(line).not.toMatch(/\b(error|wrong|mistake|failed|weak)\b/i);
});

it("the workbench takes half the window, at least 480 px, and stacks below 1,040 px", () => {
  expect(MIN_WORKBENCH_WIDTH).toBe(480);
  expect(NARROW_BREAKPOINT).toBe(1040);
  expect(defaultSplitWidth(1600)).toBe(800);
  expect(defaultSplitWidth(1100)).toBe(550);
  expect(clampSplitWidth(300, 1600)).toBe(480);
  // The book keeps a readable column beside it.
  expect(clampSplitWidth(1500, 1600)).toBe(1600 - 360);
  expect(isNarrow(1039)).toBe(true);
  expect(isNarrow(1040)).toBe(false);
});
