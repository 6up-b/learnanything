// A small synthetic book for the selection tests (reader-pdf-selection):
// the pages a PDF draws and the blocks an extraction would read from them,
// with each block's box derived from the lines drawn in it. All text is
// invented. Page 0: two columns, a running head, a footnote drawn (in the
// content stream) between the columns, a word hyphenated across a line
// break. Page 1: a paragraph running on from page 0, a display formula whose
// glyphs are not its LaTeX, a table, inline maths. Page 2: a scan (an image,
// no text layer) with GLM-OCR-like boxes, mathematical letters outside the
// BMP, and a formula.

import type { ReaderPdfBlockDto } from "../../../api/dto";
import type { PdfPageSpec, PdfText } from "./syntheticPdf";

interface Para {
  spanId: string | null;
  blockType: string;
  x: number;
  y: number;
  size: number;
  leading: number;
  width: number;
  lines: string[];
  /** The extraction's text (default: the lines joined by spaces). */
  text?: string;
  /** Glyph runs drawn on one line at their own x (a table's cells). */
  cells?: Array<{ x: number; line: number; text: string }>;
}

function paraTexts(para: Para): PdfText[] {
  if (para.cells) {
    return para.cells.map((cell) => ({ x: cell.x, y: para.y + cell.line * para.leading, size: para.size, text: cell.text }));
  }
  return para.lines.map((line, index) => ({ x: para.x, y: para.y + index * para.leading, size: para.size, text: line }));
}

function paraBox(para: Para): number[] {
  const lineCount = para.cells ? Math.max(...para.cells.map((cell) => cell.line)) + 1 : para.lines.length;
  const lastBaseline = para.y + (lineCount - 1) * para.leading;
  return [para.x - 1, para.y - para.size * 0.8 - 1, para.x + para.width, lastBaseline + para.size * 0.2 + 1];
}

const PAGE0: Para[] = [
  { spanId: "h0", blockType: "PageHeader", x: 72, y: 40, size: 8, leading: 10, width: 200, lines: ["Synthetic Notes on Foxes"] },
  { spanId: "s1", blockType: "SectionHeader", x: 72, y: 90, size: 14, leading: 16, width: 218, lines: ["1 Foxes and Dogs"] },
  {
    spanId: "s2",
    blockType: "Text",
    x: 72,
    y: 120,
    size: 10,
    leading: 14,
    width: 218,
    lines: ["The quick brown fox jumps over", "the lazy dog while a long compu-", "tation of the integral runs in", "the background very quietly."],
    text: "The quick brown fox jumps over the lazy dog while a long computation of the integral runs in the background very quietly.",
  },
  {
    spanId: "s4",
    blockType: "Footnote",
    x: 72,
    y: 740,
    size: 8,
    leading: 10,
    width: 300,
    lines: ["1 A footnote about foxes, read after the body."],
  },
  {
    spanId: "s3",
    blockType: "Text",
    x: 320,
    y: 120,
    size: 10,
    leading: 14,
    width: 220,
    lines: ["Right column begins with the", "second paragraph of this page,", "which a careful reader reads", "after the whole left column."],
  },
  { spanId: null, blockType: "", x: 300, y: 770, size: 8, leading: 10, width: 10, lines: ["7"] },
];

const PAGE1: Para[] = [
  {
    spanId: "s5",
    blockType: "Text",
    x: 72,
    y: 90,
    size: 10,
    leading: 14,
    width: 300,
    lines: ["Continuing on the next page, the", "paragraph ends with an equation:"],
  },
  {
    spanId: "s6",
    blockType: "Equation",
    x: 200,
    y: 130,
    size: 12,
    leading: 14,
    width: 100,
    lines: ["x2 + y2 = 1"],
    text: "$$\nx^{2} + y^{2} = 1\n$$",
  },
  { spanId: "s7", blockType: "Text", x: 72, y: 170, size: 10, leading: 14, width: 300, lines: ["Table 1 lists two values of the", "unknowns a and b."] },
  {
    spanId: "s8",
    blockType: "Table",
    x: 90,
    y: 210,
    size: 10,
    leading: 14,
    width: 110,
    lines: [],
    cells: [
      { x: 100, line: 0, text: "a" },
      { x: 160, line: 0, text: "b" },
      { x: 100, line: 1, text: "1" },
      { x: 160, line: 1, text: "2" },
    ],
    text: "| a | b |\n| --- | --- |\n| 1 | 2 |",
  },
  {
    spanId: "s9",
    blockType: "Text",
    x: 72,
    y: 260,
    size: 10,
    leading: 14,
    width: 300,
    lines: ["Let x be positive; then x2 > 0", "holds for every such x."],
    text: "Let $x$ be positive; then $x^{2} > 0$ holds for every such $x$.",
  },
];

/** The scanned page's blocks: boxes as a layout model gives them, no glyphs. */
const PAGE2_BLOCKS: ReaderPdfBlockDto[] = [
  { spanId: "s10", page: 2, bbox: [72, 80, 300, 98], blockType: "SectionHeader", text: "2 A Scanned Page" },
  {
    spanId: "s11",
    page: 2,
    bbox: [72, 110, 540, 190],
    blockType: "Text",
    text:
      "A scanned page has no text layer at all, only a picture of the words, so the words are placed by " +
      "estimate inside the box the layout model found. Vectors 𝑧 and 𝑤 span 𝐂² here.",
  },
  { spanId: "s12", page: 2, bbox: [200, 200, 400, 230], blockType: "Equation", text: "$$\\int_0^1 x \\, dx = \\tfrac{1}{2}$$" },
  { spanId: "s13", page: 2, bbox: [72, 240, 540, 280], blockType: "Text", text: "The last words of the synthetic book sit on this scanned page." },
];

function blocksOf(page: number, paras: Para[]): ReaderPdfBlockDto[] {
  return paras
    .filter((para) => para.spanId !== null)
    .map((para) => ({
      spanId: para.spanId as string,
      page,
      bbox: paraBox(para),
      blockType: para.blockType,
      text: para.text ?? para.lines.join(" "),
    }));
}

/** The pages to draw, in content-stream order. */
export const SYNTHETIC_PAGES: PdfPageSpec[] = [
  { texts: PAGE0.flatMap(paraTexts) },
  { texts: PAGE1.flatMap(paraTexts) },
  { scanned: true },
];

/** The extraction's blocks in reading order (as reader.pdf_view sends them):
 *  the left column, the right column, then the footnote. */
export const SYNTHETIC_BLOCKS: ReaderPdfBlockDto[] = (() => {
  const page0 = blocksOf(0, PAGE0);
  const order = ["h0", "s1", "s2", "s3", "s4"];
  page0.sort((a, b) => order.indexOf(a.spanId) - order.indexOf(b.spanId));
  return [...page0, ...blocksOf(1, PAGE1), ...PAGE2_BLOCKS];
})();

/** A block's box centre line and a point inside its n-th drawn line. */
export function linePoint(spanId: string, line: number, fraction: number): { page: number; x: number; y: number } {
  const all: Array<[number, Para]> = [...PAGE0.map((p) => [0, p] as [number, Para]), ...PAGE1.map((p) => [1, p] as [number, Para])];
  const found = all.find(([, para]) => para.spanId === spanId);
  if (!found) throw new Error(`no drawn block ${spanId}`);
  const [page, para] = found;
  const baseline = para.y + line * para.leading;
  const text = para.lines[line] ?? "";
  // Helvetica averages about half an em per glyph.
  const width = text.length * para.size * 0.5;
  return { page, x: para.x + width * fraction, y: baseline - para.size * 0.3 };
}
