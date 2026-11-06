import { describe, expect, it } from "vitest";
import { fragmentFor, parseFragment, pop, push, stackOf, TABS, top, writeFragment } from "./navigation";

describe("the fragment (§4.2)", () => {
  it("names the tab and the path, and reads back what it wrote", () => {
    expect(fragmentFor("today")).toBe("#/today");
    expect(fragmentFor("read", ["ext 1", "sec/2"])).toBe("#/read/ext%201/sec%2F2");
    expect(parseFragment(fragmentFor("read", ["ext 1", "sec/2"]))).toEqual({ tab: "read", path: ["ext 1", "sec/2"] });
    expect(parseFragment("#/today/question/i1")).toEqual({ tab: "today", path: ["question", "i1"] });
  });

  it("anything it doesn't know is Today, never an error", () => {
    for (const hash of ["", "#", "#/", "#/nowhere/x", "#token=abc", "#/%E0%A4%A"]) {
      expect(parseFragment(hash).tab).toBe("today");
    }
  });

  it("is replaced, not pushed: the app has no browser chrome to go back with", () => {
    const before = window.history.length;
    writeFragment("capture");
    expect(window.location.hash).toBe("#/capture");
    writeFragment("today", ["question", "i1"]);
    expect(window.location.hash).toBe("#/today/question/i1");
    expect(window.history.length).toBe(before);
  });
});

describe("a stack (§4.2)", () => {
  it("pushes, pops back to its root and never below it", () => {
    let stack = stackOf("library");
    stack = push(stack, "book");
    stack = push(stack, "section");
    expect(top(stack)).toBe("section");
    stack = pop(pop(pop(stack)));
    expect(stack.routes).toEqual(["library"]);
  });
});

it("the four places, the + read as Capture", () => {
  expect(TABS.map((spec) => spec.label)).toEqual(["Today", "Read", "+", "Progress"]);
  expect(TABS.find((spec) => spec.label === "+")?.name).toBe("Capture");
});
