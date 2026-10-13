// The return stack (G57): every detour pushes an entry; back and forward walk
// it like an editor; the first entry is always where the learner was.
import { expect, it } from "vitest";
import {
  back,
  canGoBack,
  canGoForward,
  EMPTY_STACK,
  forward,
  goTo,
  hasDetour,
  markReturned,
  openDetours,
  pushDetour,
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
