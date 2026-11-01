// The return stack (G57): every detour pushes an entry; back and forward walk
// it like an editor; the first entry is always where the learner was.
import { expect, it } from "vitest";
import {
  back,
  besideTrail,
  canGoBack,
  canGoForward,
  dropCurrent,
  EMPTY_STACK,
  forward,
  goTo,
  hasDetour,
  markReturned,
  openDetours,
  pushDetour,
  replaceCurrent,
  stackInquiryExchange,
  unreturnedDetours,
  type ReturnEntry,
} from "./returnStack";

function entry(id: string, over: Partial<ReturnEntry> = {}): ReturnEntry {
  return {
    id, kind: "peek", sourceId: "src", sourceTitle: "Book", extractionId: "ext", spanId: id,
    selection: null, railTab: "guide", exchangeId: null, label: id, openedAt: 0, ...over,
  };
}

const origin = entry("origin", { kind: "origin", selection: { spanId: "origin", quote: "kept words" } });

it("the first detour records the origin; there is no detour before it", () => {
  expect(hasDetour(EMPTY_STACK)).toBe(false);
  const stack = pushDetour(EMPTY_STACK, origin, entry("a"));
  expect(stack.entries.map((e) => e.id)).toEqual(["origin", "a"]);
  expect(stack.entries[0].kind).toBe("origin");
  expect(stack.entries[0].selection?.quote).toBe("kept words");
  expect(stack.cursor).toBe(1);
  expect(hasDetour(stack)).toBe(true);
});

it("back and forward walk the stack; the origin is one step behind the first detour", () => {
  let stack = pushDetour(pushDetour(EMPTY_STACK, origin, entry("a")), origin, entry("b"));
  expect(canGoForward(stack)).toBe(false);
  let moved = back(stack);
  expect(moved.target?.id).toBe("a");
  stack = moved.stack;
  moved = back(stack);
  expect(moved.target?.id).toBe("origin");
  stack = moved.stack;
  expect(canGoBack(stack)).toBe(false);
  expect(back(stack).target).toBeNull();
  moved = forward(stack);
  expect(moved.target?.id).toBe("a");
  expect(goTo(moved.stack, 2).target?.id).toBe("b");
});

it("a new detour from an earlier position drops the forward entries", () => {
  let stack = pushDetour(pushDetour(EMPTY_STACK, origin, entry("a")), origin, entry("b"));
  stack = back(stack).stack;
  stack = pushDetour(stack, origin, entry("c"));
  expect(stack.entries.map((e) => e.id)).toEqual(["origin", "a", "c"]);
  expect(stack.cursor).toBe(2);
});

it("pushing the entry already current changes nothing", () => {
  const stack = pushDetour(EMPTY_STACK, origin, entry("a"));
  expect(pushDetour(stack, origin, entry("a2", { spanId: "a" }))).toBe(stack);
});

it("names its inquiry by the first branch entry and lists the open detours", () => {
  let stack = pushDetour(EMPTY_STACK, origin, entry("peek"));
  expect(stackInquiryExchange(stack)).toBeNull();
  stack = pushDetour(stack, origin, entry("root", { kind: "branch", exchangeId: "root" }));
  stack = pushDetour(stack, origin, entry("child", { kind: "branch", exchangeId: "child" }));
  expect(stackInquiryExchange(stack)).toBe("root");
  expect(openDetours(stack).map((e) => e.id)).toEqual(["peek", "root", "child"]);
});

it("a detour is returned once: walking forward and back again finds nothing new to return", () => {
  let stack = pushDetour(pushDetour(EMPTY_STACK, origin, entry("a")), origin, entry("b"));
  expect(unreturnedDetours(stack).map((e) => e.id)).toEqual(["a", "b"]);
  stack = markReturned(goTo(stack, 0).stack, unreturnedDetours(stack).map((e) => e.id));
  stack = forward(stack).stack;
  expect(unreturnedDetours(back(stack).stack)).toEqual([]);
  // A new detour pushed later is the only one left to return.
  stack = pushDetour(stack, origin, entry("c"));
  expect(stack.entries.map((e) => e.id)).toEqual(["origin", "a", "c"]);
  expect(unreturnedDetours(stack).map((e) => e.id)).toEqual(["c"]);
});

it("Reader CA6: closing side by side drops its crumb only while it is current, moving nothing", () => {
  const side = entry("sbs", { kind: "side_by_side", spanId: "origin", label: "side by side with Axler §5.A" });
  const one = pushDetour(EMPTY_STACK, origin, side);
  expect(dropCurrent(one, "sbs")).toBe(EMPTY_STACK);
  const two = pushDetour(pushDetour(EMPTY_STACK, origin, entry("p1")), origin, side);
  expect(dropCurrent(two, "sbs")).toEqual({ ...two, entries: two.entries.slice(0, 2), cursor: 1 });
  // Walked off it already (or another id): unchanged.
  const walked = back(two).stack;
  expect(dropCurrent(walked, "sbs")).toBe(walked);
  expect(dropCurrent(two, "p1")).toBe(two);
});

it("Reader CA6 (Codex review F6): side by side with another section is another detour; replaceCurrent keeps the id", () => {
  const axler = { sourceId: "src_axler", sourceTitle: "Axler", extractionId: "ext_axler", sectionId: "ax5a", title: "5.A", spanId: "a1", by: "judged" as const };
  const lay = { ...axler, sourceId: "src_lay", sourceTitle: "Lay", extractionId: "ext_lay", sectionId: "lay52", title: "5.2" };
  const side = entry("sbs", { kind: "side_by_side", spanId: "origin", sideBySide: axler });
  const one = pushDetour(EMPTY_STACK, origin, side);
  // The same passage, another pair: not deduplicated away.
  const other = pushDetour(one, origin, entry("sbs2", { kind: "side_by_side", spanId: "origin", sideBySide: lay }));
  expect(other.entries.map((e) => e.id)).toEqual(["origin", "sbs", "sbs2"]);
  // The same pair again: a no-op, as before.
  expect(pushDetour(one, origin, entry("sbs3", { kind: "side_by_side", spanId: "origin", sideBySide: axler }))).toBe(one);
  // Replacing the current pair keeps its entry id; another entry is unchanged.
  const replaced = replaceCurrent(one, "sbs", { label: "side by side with Lay §5.2", sideBySide: lay });
  expect(replaced.entries[1]).toMatchObject({ id: "sbs", label: "side by side with Lay §5.2", sideBySide: lay });
  expect(replaced.cursor).toBe(1);
  expect(replaceCurrent(one, "origin", { label: "x" })).toBe(one);
});

// Reader CA6b (Codex re-review F8): the way back to side by side is kept only
// while side by side comes before the current entry (a detour from it).
it("besideTrail: the stack while a side_by_side entry is behind the current one; otherwise none", () => {
  const sbs = entry("s", { kind: "side_by_side" });
  const onCrumb = pushDetour(EMPTY_STACK, origin, sbs);
  expect(besideTrail(EMPTY_STACK)).toBeNull();
  expect(besideTrail(onCrumb)).toBeNull();
  const detour = pushDetour(onCrumb, origin, entry("d", { kind: "source", sourceId: "src_other" }));
  expect(besideTrail(detour)).toBe(detour);
  expect(besideTrail(back(detour).stack)).toBeNull();
  expect(besideTrail(pushDetour(EMPTY_STACK, origin, entry("p")))).toBeNull();
});
