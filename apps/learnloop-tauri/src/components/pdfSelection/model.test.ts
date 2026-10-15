// @vitest-environment node
// The PDF selection model on synthetic PDFs parsed by the real pdf.js
// (reader-pdf-selection): two columns, a footnote drawn between them, a word
// hyphenated across a line break, a display formula, a table, inline maths,
// a page break, and a scanned page with no text layer.
import { beforeAll, describe, expect, it } from "vitest";
import {
  anchorRange,
  hitTest,
  marqueeRanges,
  moveHead,
  rangeRects,
  rangesFromNodes,
  selectionNodes,
  selectionPayload,
  selectionText,
  SelectionModel,
  type Pos,
  type SelRange,
} from "./model";
import { toCodepoint } from "./tokens";
import { buildPdf, readPdf } from "./testing/syntheticPdf";
import { linePoint, SYNTHETIC_BLOCKS, SYNTHETIC_PAGES } from "./testing/syntheticBook";

let model: SelectionModel;

beforeAll(async () => {
  model = new SelectionModel(SYNTHETIC_BLOCKS);
  for (const page of await readPdf(buildPdf(SYNTHETIC_PAGES))) model.setPageText(page.page, page.items, page.transform);
});

/** The `nth` unit reading `text` in a block. */
function find(spanId: string, text: string, nth = 0): Pos {
  const block = model.blockIndex(spanId) as number;
  const source = model.blocks[block].text;
  const hits = model.units(block).flatMap((unit, index) => (source.slice(unit.start, unit.end) === text ? [index] : []));
  if (hits[nth] === undefined) throw new Error(`no ${text} in ${spanId}`);
  return { block, unit: hits[nth] };
}

/** Where a pointer on that word is: the centre of its (first) box. */
function on(pos: Pos, piece = 0): { page: number; x: number; y: number } {
  const box = model.geometry(pos.block).boxes[pos.unit][piece];
  return { page: model.blocks[pos.block].page, x: (box[0] + box[2]) / 2, y: (box[1] + box[3]) / 2 };
}

/** The unit a pointer at the centre of `text` hits. */
function at(spanId: string, text: string, nth = 0): Pos {
  const point = on(find(spanId, text, nth));
  const pos = hitTest(model, point.page, point.x, point.y);
  if (!pos) throw new Error(`nothing under ${text}`);
  return pos;
}

function word(pos: Pos): string {
  const block = model.blocks[pos.block];
  const unit = model.units(pos.block)[pos.unit];
  return block.text.slice(unit.start, unit.end);
}

function span(pos: Pos): string {
  return model.blocks[pos.block].spanId;
}

function drag(from: Pos, to: Pos): SelRange[] {
  return [{ anchor: from, head: to }];
}

describe("the page's own words", () => {
  it("leaves running heads and page numbers out of every selection", () => {
    expect(model.blocksOnPage(0).map((index) => model.blocks[index].spanId)).toEqual(["s1", "s2", "s3", "s4"]);
    // The page number "7" lies in no block; the head is furniture.
    const units = model.blocksOnPage(0).flatMap((index) => model.units(index).map((unit) => model.blocks[index].text.slice(unit.start, unit.end)));
    expect(units).not.toContain("7");
    expect(units).not.toContain("Synthetic");
  });

  it("places words where the PDF draws them (Helvetica's own advance widths)", () => {
    const geometry = model.geometry(model.blockIndex("s2") as number);
    expect(geometry.source).toBe("text_layer");
    const [the] = geometry.boxes[find("s2", "The").unit];
    const [quick] = geometry.boxes[find("s2", "quick").unit];
    expect(the[0]).toBeCloseTo(72, 1);
    // "The " is (611 + 556 + 556 + 278) / 1000 em at 10 pt.
    expect(quick[0]).toBeCloseTo(72 + 20.01, 1);
    const [right] = model.geometry(model.blockIndex("s3") as number).boxes[0];
    expect(right[0]).toBeCloseTo(320, 1);
  });

  it("snaps a point to the word under it, between words to the nearer, past a line's end to its last", () => {
    expect(word(at("s2", "quick"))).toBe("quick");
    const [quick] = model.geometry(model.blockIndex("s2") as number).boxes[find("s2", "quick").unit];
    expect(word(hitTest(model, 0, quick[2] + 0.5, (quick[1] + quick[3]) / 2) as Pos)).toBe("quick");
    expect(word(hitTest(model, 0, 289, (quick[1] + quick[3]) / 2) as Pos)).toBe("over");
    // In the column gap, level with the left column's first line: its last word.
    expect(word(hitTest(model, 0, 300, (quick[1] + quick[3]) / 2) as Pos)).toBe("over");
  });

  it("joins a word hyphenated across a line break: both halves select it, it copies whole", () => {
    const first = find("s2", "computation");
    expect(hitTest(model, 0, on(first, 0).x, on(first, 0).y)).toEqual(first);
    expect(hitTest(model, 0, on(first, 1).x, on(first, 1).y)).toEqual(first);
    const geometry = model.geometry(first.block);
    expect(geometry.boxes[first.unit]).toHaveLength(2);
    expect(geometry.boxLines[first.unit]).toEqual([1, 2]);
    const ranges = drag(at("s2", "long"), at("s2", "of"));
    expect(selectionText(model, ranges)).toBe("long computation of");
    // Painted on both lines.
    expect(rangeRects(model, ranges, 0)).toHaveLength(2);
  });
});

describe("reading order", () => {
  it("follows the extraction across two columns, not the content stream (the footnote is drawn between them)", () => {
    const ranges = drag(at("s2", "quietly."), at("s3", "begins"));
    expect(selectionNodes(model, ranges).map((node) => [node.spanId, node.quote])).toEqual([
      ["s2", "quietly."],
      ["s3", "Right column begins"],
    ]);
    expect(selectionText(model, ranges)).toBe("quietly.\n\nRight column begins");
  });

  it("reads on over a page break, with the page's footnote after its body", () => {
    const ranges = drag(at("s3", "column."), at("s5", "on"));
    expect(selectionNodes(model, ranges).map((node) => [node.spanId, node.quote])).toEqual([
      ["s3", "column."],
      ["s4", "1 A footnote about foxes, read after the body."],
      ["s5", "Continuing on"],
    ]);
  });

  it("selects the same run dragged backwards", () => {
    const forward = selectionNodes(model, drag(at("s2", "The"), at("s2", "dog")));
    const backward = selectionNodes(model, drag(at("s2", "dog"), at("s2", "The")));
    expect(forward[0].quote).toBe("The quick brown fox jumps over the lazy dog");
    expect(backward).toEqual(forward);
  });
});

describe("formulas, tables and inline maths", () => {
  it("takes a display formula whole, with its LaTeX as the selected text", () => {
    const point = linePoint("s6", 0, 0.3);
    const pos = hitTest(model, point.page, point.x, point.y) as Pos;
    expect(span(pos)).toBe("s6");
    const payload = selectionPayload(model, drag(pos, pos));
    expect(payload?.text).toBe("$$\nx^{2} + y^{2} = 1\n$$");
    expect(payload?.nodes).toEqual([{ spanId: "s6", quote: "$$\nx^{2} + y^{2} = 1\n$$", start: 0, end: 23 }]);
    expect(rangeRects(model, drag(pos, pos), 1)).toEqual([model.blocks[pos.block].bbox]);
  });

  it("takes a table whole, with its Markdown as the selected text", () => {
    const pos = hitTest(model, 1, 162, 206) as Pos;
    expect(span(pos)).toBe("s8");
    expect(selectionText(model, drag(pos, pos))).toBe("| a | b |\n| --- | --- |\n| 1 | 2 |");
  });

  it("keeps inline maths one unit, drawn over its glyphs, quoted as LaTeX", () => {
    // Its glyphs ("x2 > 0") are three text-layer words; the unit covers them.
    const pos = find("s9", "$x^{2} > 0$");
    const [box] = model.geometry(pos.block).boxes[pos.unit];
    expect(box[2] - box[0]).toBeGreaterThan(20);
    expect(hitTest(model, 1, box[2] - 1, (box[1] + box[3]) / 2)).toEqual(pos);
    const ranges = drag(at("s9", "positive;"), pos);
    expect(selectionText(model, ranges)).toBe("positive; then $x^{2} > 0$");
  });
});

describe("a scanned page (an image, no text layer)", () => {
  it("places the words by estimate inside the layout boxes, so a drag still snaps to words", () => {
    const block = model.blockIndex("s11") as number;
    expect(model.hasPageText(2)).toBe(true);
    expect(model.geometry(block).source).toBe("estimated");
    expect(model.geometry(block).lines.length).toBeGreaterThan(1);
    const from = hitTest(model, 2, 75, 115) as Pos;
    const to = hitTest(model, 2, 160, 140) as Pos;
    expect(word(from)).toBe("A");
    const nodes = selectionNodes(model, drag(from, to));
    expect(nodes).toHaveLength(1);
    const text = model.blocks[block].text;
    expect(nodes[0].quote.startsWith("A scanned page")).toBe(true);
    expect(text.indexOf(nodes[0].quote)).toBe(0);
  });

  it("sends code-point offsets: mathematical letters outside the BMP count once", () => {
    const block = model.blockIndex("s11") as number;
    const text = model.blocks[block].text;
    const units = model.units(block);
    const z = units.findIndex((unit) => text.slice(unit.start, unit.end) === "𝑧");
    const w = units.findIndex((unit) => text.slice(unit.start, unit.end) === "𝑤");
    const [node] = selectionNodes(model, drag({ block, unit: z }, { block, unit: w }));
    expect(node.quote).toBe("𝑧 and 𝑤");
    const codepoints = Array.from(text);
    expect(codepoints.slice(node.start, node.end).join("")).toBe("𝑧 and 𝑤");
    expect(node.start).toBe(toCodepoint(text, units[z].start));
    expect(node.end - node.start).toBe(7);
    // And back: the anchor names the same words.
    expect(anchorRange(model, "s11", node.start, node.end)).toEqual({ anchor: { block, unit: z }, head: { block, unit: w } });
  });
});

describe("keys", () => {
  it("moves the head by a word and by a line, keeping the column", () => {
    const the = find("s2", "The");
    expect(word(moveHead(model, the, "right").pos)).toBe("quick");
    expect(word(moveHead(model, moveHead(model, the, "right").pos, "left").pos)).toBe("The");
    // "quick" (92-115) is over "lazy" (89-106); "lazy" over "of" (99-108).
    const down = moveHead(model, find("s2", "quick"), "down");
    expect(word(down.pos)).toBe("lazy");
    const again = moveHead(model, down.pos, "down", down.goalX);
    expect(word(again.pos)).toBe("of");
    expect(word(moveHead(model, again.pos, "up", again.goalX).pos)).toBe("lazy");
    expect(word(moveHead(model, the, "lineEnd").pos)).toBe("over");
    expect(word(moveHead(model, find("s2", "fox"), "lineStart").pos)).toBe("The");
  });

  it("crosses into the next block in reading order (the right column after the left)", () => {
    const last = find("s2", "background");
    const next = moveHead(model, last, "down");
    expect(span(next.pos)).toBe("s3");
    expect(span(moveHead(model, next.pos, "up", next.goalX).pos)).toBe("s2");
    // The last word of a block steps to the next block's first.
    const end = { block: last.block, unit: model.unitCount(last.block) - 1 };
    expect(word(moveHead(model, end, "right").pos)).toBe("Right");
  });
});

describe("anchors and boxes", () => {
  it("paints a saved anchor on the words it names, one box per line", () => {
    const block = model.blockIndex("s2") as number;
    const text = model.blocks[block].text;
    const start = text.indexOf("lazy dog");
    const range = anchorRange(model, "s2", start, start + "lazy dog".length) as SelRange;
    expect(selectionText(model, [range])).toBe("lazy dog");
    const [box] = rangeRects(model, [range], 0);
    expect(box[0]).toBeGreaterThan(85);
    expect(box[2]).toBeLessThan(130);
    // An anchor of a block not on this reading draws nothing.
    expect(anchorRange(model, "gone", 0, 4)).toBeNull();
  });

  it("restores a selection from its nodes (the return stack, the extracted text)", () => {
    const ranges = drag(at("s3", "column."), at("s5", "on"));
    const nodes = selectionNodes(model, ranges);
    expect(selectionNodes(model, rangesFromNodes(model, nodes))).toEqual(nodes);
    // A node with no offsets (made on the extracted text) is its whole block.
    expect(selectionNodes(model, rangesFromNodes(model, [{ spanId: "s7" }]))[0].quote).toBe(model.blocks[model.blockIndex("s7") as number].text);
  });

  it("selects the words a ctrl-drawn box holds, and a formula it covers", () => {
    const ranges = marqueeRanges(model, [
      { page: 1, rect: [70, 160, 150, 174] },
      { page: 1, rect: [190, 110, 320, 140] },
    ]);
    expect(selectionNodes(model, ranges).map((node) => [node.spanId, node.quote])).toEqual([
      ["s6", "$$\nx^{2} + y^{2} = 1\n$$"],
      ["s7", "Table 1 lists two"],
    ]);
  });
});
