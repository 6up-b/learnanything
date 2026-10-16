// @vitest-environment node
// Words where the PDF draws them, in any font (Codex review F1 of
// reader-pdf-selection): synthetic PDFs in Courier, Times-Roman and a Type3
// font with widths unlike any standard font, parsed by the real pdf.js. Every
// expected coordinate here is worked out by hand from the PDF's own numbers
// (the standard fonts' AFM widths, the Type3 font's /Widths, Tc, Tw, Tz, Ts,
// Tm, TL, the form's /Matrix), never from what the code computes.
//
// Two sources place a page's words: the operator list (`operatorWords`:
// every glyph's own advance, as pdf.js paints it), and until it is read the
// text content (`glyphWords`: a run split by its font family's widths, exact
// for the standard fonts, an estimate for an embedded one).
import { beforeAll, describe, expect, it } from "vitest";
import type { ReaderPdfBlockDto } from "../../api/dto";
import { glyphWords, operatorWords, type GlyphWord } from "./geometry";
import { hitTest, SelectionModel } from "./model";
import { buildPdf, fontKey, paintPdf, readPdf, type PaintedPage, type ParsedPage, type PdfPageSpec } from "./testing/syntheticPdf";

const PAGE_H = 792;

// Times-Roman's AFM widths (per 1000 em) for the letters used here.
const TIMES: Record<string, number> = { " ": 250, T: 611, h: 500, e: 444, q: 500, u: 500, i: 278, c: 444, k: 500, b: 500, r: 333, o: 500, w: 722, n: 500, f: 333, x: 500 };
const timesWidth = (text: string, size: number) => Array.from(text).reduce((sum, ch) => sum + TIMES[ch], 0) * (size / 1000);

const SPEC: PdfPageSpec[] = [
  {
    texts: [
      // The review's case: Courier is 600 units a glyph, so at 10 pt every
      // glyph is 6 pt wide, "i" as much as "W".
      { x: 72, y: 100, size: 10, text: "iiiiiiiiii WWWWWWWWWW end", font: "Courier" },
      { x: 72, y: 200, size: 12, text: "The quick brown fox", font: "Times-Roman" },
      // Type3: "a" 900 units, "b" 100, a space 250; at 20 pt "aab" is 38 pt
      // wide and "b" 2 pt.
      { x: 72, y: 300, size: 20, text: "aab b", font: "Type3" },
    ],
    raw: [
      // LaTeX's way: no space glyph, a kern of a third of an em between words.
      `BT /${fontKey("Times-Roman")} 10 Tf 72 ${PAGE_H - 400} Td [(The)-333(quick)-333(brown)] TJ ET`,
    ],
  },
  {
    raw: [
      // Character spacing 2, word spacing 4, horizontal scaling 150 %, a text
      // matrix: each glyph advances (6 + 2) × 1.5 = 12 pt and paints 9 pt; a
      // space advances (6 + 2 + 4) × 1.5 = 18 pt.
      `q BT /${fontKey("Courier")} 10 Tf 2 Tc 4 Tw 150 Tz 1 0 0 1 72 ${PAGE_H - 300} Tm (ab cd) Tj ET Q`,
      // Leading 14: T*, ' and " each move a line down.
      `q BT /${fontKey("Courier")} 10 Tf 14 TL 72 ${PAGE_H - 342} Td (one) Tj T* (two) Tj (three) ' 1 0 (four) " ET Q`,
      // Text rise 3: the baseline 3 pt up.
      `q BT /${fontKey("Courier")} 10 Tf 3 Ts 300 ${PAGE_H - 342} Td (up) Tj ET Q`,
      // A form XObject (/Matrix [1 0 0 1 300 100]) under a 10 pt shift: its
      // "Form" at (310, 110) in PDF space, its baseline 682 pt from the top.
      "q 1 0 0 1 10 10 cm /Fm1 Do Q",
    ],
  },
];

let parsed: ParsedPage[];
let painted: { pages: PaintedPage[]; ops: Record<string, number> };

beforeAll(async () => {
  const bytes = buildPdf(SPEC);
  parsed = await readPdf(bytes);
  painted = await paintPdf(bytes);
});

function fromOperators(page: number): GlyphWord[] {
  const entry = painted.pages[page];
  return operatorWords(entry.opList, painted.ops, (name) => entry.fonts.get(name) ?? null, entry.transform);
}

function fromText(page: number): GlyphWord[] {
  const entry = parsed[page];
  return glyphWords(entry.items, entry.transform, entry.styles);
}

/** The words reading `texts`, in order, with their [left, right] in points. */
function spans(words: readonly GlyphWord[], texts: readonly string[]): Array<[string, number, number]> {
  return texts.map((text) => {
    const word = words.find((candidate) => candidate.text === text);
    if (!word) throw new Error(`no word ${text} in ${words.map((w) => w.text).join(" ")}`);
    return [text, word.box[0], word.box[2]];
  });
}

/** Each word's ends within `points` of the expected ones (0.005 pt: exact). */
function expectSpans(actual: Array<[string, number, number]>, expected: Array<[string, number, number]>, points = 0.005) {
  expect(actual.map(([text]) => text)).toEqual(expected.map(([text]) => text));
  actual.forEach(([, left, right], index) => {
    expect(Math.abs(left - expected[index][1])).toBeLessThanOrEqual(points);
    expect(Math.abs(right - expected[index][2])).toBeLessThanOrEqual(points);
  });
}

const COURIER: Array<[string, number, number]> = [
  ["iiiiiiiiii", 72, 132],
  ["WWWWWWWWWW", 138, 198],
  ["end", 204, 222],
];

const TIMES_LINE: Array<[string, number, number]> = (() => {
  const out: Array<[string, number, number]> = [];
  let x = 72;
  for (const word of ["The", "quick", "brown", "fox"]) {
    out.push([word, x, x + timesWidth(word, 12)]);
    x += timesWidth(word, 12) + timesWidth(" ", 12);
  }
  return out;
})();

describe("the operator list: each glyph where pdf.js paints it", () => {
  it("Courier: every glyph 6 pt at 10 pt", () => {
    expectSpans(spans(fromOperators(0), ["iiiiiiiiii", "WWWWWWWWWW", "end"]), COURIER);
  });

  it("Times-Roman: the AFM widths", () => {
    expectSpans(spans(fromOperators(0), ["The", "quick", "brown", "fox"]), TIMES_LINE);
  });

  it("a Type3 font: its own /Widths, unlike any standard font's", () => {
    expectSpans(spans(fromOperators(0), ["aab", "b"]), [
      ["aab", 72, 110],
      ["b", 115, 117],
    ]);
  });

  it("words spaced by kerning alone (no space glyph), as LaTeX writes them", () => {
    const the = timesWidth("The", 10);
    const quick = timesWidth("quick", 10);
    const kern = 3.33;
    const words = fromOperators(0).filter((word) => word.box[1] > 380 && word.box[1] < 400);
    expectSpans(spans(words, ["The", "quick", "brown"]), [
      ["The", 72, 72 + the],
      ["quick", 72 + the + kern, 72 + the + kern + quick],
      ["brown", 72 + the + 2 * kern + quick, 72 + the + 2 * kern + quick + timesWidth("brown", 10)],
    ]);
  });

  it("character and word spacing, horizontal scaling and a text matrix", () => {
    expectSpans(spans(fromOperators(1), ["ab", "cd"]), [
      ["ab", 72, 93],
      ["cd", 114, 135],
    ]);
  });

  it("leading (T*, ' and \"), text rise and a form XObject", () => {
    const words = fromOperators(1);
    const box = (text: string) => words.find((word) => word.text === text)!.box;
    // One line each, 14 pt apart: the baselines at 342, 356, 370, 384.
    [["one", 342], ["two", 356], ["three", 370], ["four", 384]].forEach(([text, baseline]) => {
      expect(box(text as string)[0]).toBeCloseTo(72, 2);
      expect(box(text as string)[3]).toBeCloseTo((baseline as number) + 2, 2);
    });
    expect(box("three")[2]).toBeCloseTo(72 + 5 * 6, 2);
    // Raised 3 pt: the baseline at 339.
    expect(box("up")[0]).toBeCloseTo(300, 2);
    expect(box("up")[3]).toBeCloseTo(339 + 2, 2);
    expect([...box("Form")]).toEqual([310, 674, 334, 684].map((value) => expect.closeTo(value, 2)));
  });
});

describe("the text content, before the operator list is read: the run's font family's widths", () => {
  it("monospace and serif runs are split exactly for the standard fonts", () => {
    expect(Object.values(parsed[0].styles).map((style) => style.fontFamily)).toEqual(expect.arrayContaining(["monospace", "serif"]));
    expectSpans(spans(fromText(0), ["iiiiiiiiii", "WWWWWWWWWW", "end"]), COURIER);
    expectSpans(spans(fromText(0), ["The", "quick", "brown", "fox"]), TIMES_LINE);
  });

  it("a kerned run is split to within a point (its spaces' widths are pdf.js's guess)", () => {
    const words = fromText(0).filter((word) => word.box[1] > 380 && word.box[1] < 400);
    const exact = fromOperators(0).filter((word) => word.box[1] > 380 && word.box[1] < 400);
    expectSpans(spans(words, ["The", "quick", "brown"]), spans(exact, ["The", "quick", "brown"]), 1);
  });
});

describe("selecting in those fonts", () => {
  const block = (spanId: string, text: string, bbox: number[]): ReaderPdfBlockDto => ({ spanId, page: 0, bbox, blockType: "Text", text });
  const BLOCKS: ReaderPdfBlockDto[] = [
    block("courier", "iiiiiiiiii WWWWWWWWWW end", [71, 91, 300, 103]),
    block("times", "The quick brown fox", [71, 189, 300, 203]),
    block("type3", "aab b", [71, 283, 300, 305]),
  ];
  const word = (model: SelectionModel, x: number, y: number) => {
    const pos = hitTest(model, 0, x, y)!;
    const entry = model.blocks[pos.block];
    const unit = model.units(pos.block)[pos.unit];
    return entry.text.slice(unit.start, unit.end);
  };

  it("a click inside a word selects that word, from the operator list (the review's x = 102 in Courier)", () => {
    const model = new SelectionModel(BLOCKS);
    model.setPageText(0, parsed[0].items, parsed[0].transform, parsed[0].styles);
    model.setPageGlyphs(0, fromOperators(0));
    expect(model.hasPageGlyphs(0)).toBe(true);
    expect(word(model, 102, 97)).toBe("iiiiiiiiii");
    expect(word(model, 131, 97)).toBe("iiiiiiiiii");
    expect(word(model, 139, 97)).toBe("WWWWWWWWWW");
    expect(word(model, 95, 196)).toBe("quick");
    expect(word(model, 108, 292)).toBe("aab");
    expect(word(model, 116, 292)).toBe("b");
  });

  it("and from the text content while the operator list is not read yet", () => {
    const model = new SelectionModel(BLOCKS);
    model.setPageText(0, parsed[0].items, parsed[0].transform, parsed[0].styles);
    expect(model.hasPageGlyphs(0)).toBe(false);
    expect(word(model, 102, 97)).toBe("iiiiiiiiii");
    expect(word(model, 139, 97)).toBe("WWWWWWWWWW");
    expect(word(model, 95, 196)).toBe("quick");
  });

  it("a page placed from its glyphs keeps them when its text content arrives again (a redraw at another zoom)", () => {
    const model = new SelectionModel(BLOCKS);
    model.setPageGlyphs(0, fromOperators(0));
    // A text content whose runs carry no family would split by sans-serif widths.
    model.setPageText(0, parsed[0].items, parsed[0].transform, null);
    expect(word(model, 102, 97)).toBe("iiiiiiiiii");
    expect(word(model, 108, 292)).toBe("aab");
  });
});
