// @vitest-environment jsdom
import { afterEach, describe, expect, it } from "vitest";
import type { PromotedRowDto } from "../../../api/dto";
import { captureNodes, headerLine, objectAt, objectInput, placeMenu, placeSubmenu, promotedReason, shownPromoted, verbsFor, type MenuObject } from "./model";

const row = (rowId: string, extra: Partial<PromotedRowDto> = {}): PromotedRowDto => ({
  rowId, kind: "question", glyph: "?", label: rowId, reason: "you asked about this", action: { verb: "open" }, learnerAt: null,
  checked: true, judgeRank: 0, basis: "union", extra: {}, ...extra,
} as unknown as PromotedRowDto);

afterEach(() => {
  document.body.innerHTML = "";
  window.getSelection()?.removeAllRanges();
});

describe("the verbs for each object kind", () => {
  it("keeps the fixed order and leaves out what does not apply (none shown disabled)", () => {
    expect(verbsFor("passage").map((verb) => verb.id)).toEqual(["ask", "note", "append", "carry", "open_beside", "find", "compare", "show_me", "make_practice", "teach_me", "knows"]);
    expect(verbsFor("window").map((verb) => verb.id)).toEqual(["new_desk", "gather", "share_slot", "own_slot", "knows"]);
    // A margin note is the learner's own words: no Append, Compare, Open beside, Show me or practice from it.
    expect(verbsFor("note").map((verb) => verb.id)).toEqual(["ask", "carry", "find", "knows"]);
    expect(verbsFor("highlight").map((verb) => verb.id)).not.toContain("note");
    expect(verbsFor("pad_line").map((verb) => verb.id)).toContain("submit");
  });

  it("letters are unique within a kind, so a letter runs one verb", () => {
    for (const kind of ["passage", "cue", "highlight", "note", "window", "pad_line"] as const) {
      const keys = verbsFor(kind).map((verb) => verb.key);
      expect(new Set(keys).size).toBe(keys.length);
    }
  });
});

describe("the header and the object as the server reads it", () => {
  it("names the kind and the first 46 characters of the selection or the object", () => {
    const at = { x: 0, y: 0 };
    expect(headerLine({ kind: "cue", windowId: "w", text: "short words", at }, false)).toBe("a transcript cue · “short words”");
    const long = "x".repeat(60);
    expect(headerLine({ kind: "passage", windowId: "w", text: "ignored", selection: long, at }, false)).toBe(`a passage · “${"x".repeat(46)}…”`);
  });

  it("sends only what the object has", () => {
    expect(objectInput({ kind: "cue", windowId: "w1", text: "", extractionId: "e", spanId: "s", t: 12, at: { x: 0, y: 0 } }, "d1"))
      .toEqual({ objectKind: "cue", extractionId: "e", spanId: "s", t: 12, windowId: "w1", deskId: "d1" });
    expect(objectInput({ kind: "window", windowId: "w1", text: "", at: { x: 0, y: 0 } }, null)).toEqual({ objectKind: "window", windowId: "w1" });
  });
});

describe("the promoted rows", () => {
  it("keeps the server's order, drops rows dismissed here and shows at most four", () => {
    const rows = ["a", "b", "c", "d", "e", "f"].map((id) => row(id));
    expect(shownPromoted(rows, new Set()).map((each) => each.rowId)).toEqual(["a", "b", "c", "d"]);
    expect(shownPromoted(rows, new Set(["b"])).map((each) => each.rowId)).toEqual(["a", "c", "d", "e"]);
  });

  it("says a judge's unchecked finding was found by search, not checked", () => {
    expect(promotedReason(row("a", { checked: false, reason: "treats the same idea" }))).toBe("treats the same idea · found by search, not checked");
    expect(promotedReason(row("a", { checked: true, reason: "you asked about this" }))).toBe("you asked about this");
  });
});

describe("where the menu goes", () => {
  it("opens 2 px down and right of the pointer, moved in from the right and bottom edges and below the top bar", () => {
    const viewport = { w: 1440, h: 900 };
    expect(placeMenu({ x: 400, y: 300 }, { w: 360, h: 300 }, viewport)).toEqual({ left: 402, top: 302 });
    expect(placeMenu({ x: 1300, y: 800 }, { w: 360, h: 300 }, viewport)).toEqual({ left: 1440 - 360 - 10, top: 900 - 300 - 10 });
    expect(placeMenu({ x: 5, y: 2 }, { w: 360, h: 300 }, viewport)).toEqual({ left: 10, top: 44 });
  });

  it("puts the submenu 4 px right of its row and 6 px above it", () => {
    expect(placeSubmenu({ right: 700, top: 400 }, 260, { w: 1440 })).toEqual({ left: 704, top: 394 });
    expect(placeSubmenu({ right: 1400, top: 400 }, 260, { w: 1440 })).toEqual({ left: 1440 - 260 - 8, top: 394 });
  });
});

describe("what was right-clicked", () => {
  const source = () => ({ sourceId: "src1", extractionId: "ext1" });
  const at = { x: 10, y: 20 };
  const mountHtml = (html: string) => {
    document.body.innerHTML = html;
  };

  it("reads a passage, with the passages a selection over it touches", () => {
    mountHtml(`<div data-desk-window="w1"><div data-span-id="s1">first words</div> <div data-span-id="s2">second words</div></div>`);
    const object = objectAt(document.querySelector("[data-span-id=s1]") as Element, () => "source", source, at);
    expect(object).toMatchObject({ kind: "passage", windowId: "w1", spanId: "s1", spanIds: ["s1"], extractionId: "ext1", sourceId: "src1", text: "first words" });
    const range = document.createRange();
    range.setStart(document.querySelector("[data-span-id=s1]")?.firstChild as Node, 6);
    range.setEnd(document.querySelector("[data-span-id=s2]")?.firstChild as Node, 6);
    window.getSelection()?.addRange(range);
    const selected = objectAt(document.querySelector("[data-span-id=s1]") as Element, () => "source", source, at);
    expect(selected?.selection).toBe("words second");
    expect(selected?.spanIds).toEqual(["s1", "s2"]);
    // Each passage's own words of the selection: what a capture quotes for it.
    expect(selected?.slices).toEqual([{ spanId: "s1", quote: "words" }, { spanId: "s2", quote: "second" }]);
    expect(captureNodes(selected as MenuObject)).toEqual([{ spanId: "s1", quote: "words" }, { spanId: "s2", quote: "second" }]);
  });

  it("a selection inside a highlighted passage stays the selection (the verbs act on those words)", () => {
    mountHtml(`<div data-desk-window="w1"><div data-span-id="s1" data-annotation-id="a1" data-annotation-kind="highlight">marked words here</div></div>`);
    const text = document.querySelector("[data-span-id=s1]")?.firstChild as Node;
    const range = document.createRange();
    range.setStart(text, 7);
    range.setEnd(text, 12);
    window.getSelection()?.addRange(range);
    const object = objectAt(document.querySelector("[data-span-id=s1]") as Element, () => "source", source, at);
    expect(object).toMatchObject({ kind: "highlight", annotationId: "a1", selection: "words", spanIds: ["s1"], slices: [{ spanId: "s1", quote: "words" }] });
    expect(headerLine(object as MenuObject, false)).toBe("your highlight · “words”");
  });

  it("reads a transcript cue with its time", () => {
    mountHtml(`<div data-desk-window="w2"><span data-span-id="c1" data-transcript-span="c1" data-t="42.5">a cue</span></div>`);
    expect(objectAt(document.querySelector("[data-t]") as Element, () => "video", source, at)).toMatchObject({ kind: "cue", spanId: "c1", t: 42.5 });
  });

  it("reads a highlight on its passage, and a margin note's card by the passage it names", () => {
    mountHtml(`<div data-desk-window="w1"><div data-span-id="s1" data-annotation-id="a1" data-annotation-kind="highlight">marked</div>
      <div data-annotation-id="a2" data-annotation-kind="note" data-annotation-span="s1" data-annotation-spans='["s1","s2"]'><span id="n">my note</span></div></div>`);
    expect(objectAt(document.querySelector("[data-span-id=s1]") as Element, () => "source", source, at)).toMatchObject({ kind: "highlight", annotationId: "a1", spanId: "s1" });
    expect(objectAt(document.getElementById("n") as Element, () => "source", source, at)).toMatchObject({ kind: "note", annotationId: "a2", spanId: "s1", spanIds: ["s1", "s2"], text: "my note" });
  });

  it("reads a window header and a pad line, and nothing elsewhere", () => {
    mountHtml(`<div data-desk-window="w3"><div class="desk-pane-head"><b id="h">A book</b></div>
      <div data-pad="p1"><div data-block="b1"><span id="line">my line</span></div></div><div id="bare">chrome</div></div>
      <div id="outside">x</div>`);
    expect(objectAt(document.getElementById("h") as Element, () => "source", source, at)).toMatchObject({ kind: "window", windowId: "w3", text: "A book" });
    expect(objectAt(document.getElementById("line") as Element, () => "pad_stack", () => null, at)).toMatchObject({ kind: "pad_line", padId: "p1", blockId: "b1", text: "my line" });
    expect(objectAt(document.getElementById("bare") as Element, () => "source", source, at)).toBeNull();
    expect(objectAt(document.getElementById("outside") as Element, () => "source", source, at)).toBeNull();
  });
});
