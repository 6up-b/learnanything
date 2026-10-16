// Where an extraction block's words sit on its page (reader-pdf-selection).
//
// Two sources, one result (a box per word, a line per word):
// - the page's own text, where it has one: its words are aligned to the
//   extraction's words by their letters, so a word is drawn where the PDF
//   draws it, a hyphenated word keeps both halves, and the extraction's text
//   (LaTeX for maths) stays the quote. Where each glyph sits comes from the
//   page's operator list (`operatorWords`: every glyph's own advance in its
//   own font, as pdf.js paints it); until that is read, from pdf.js's text
//   content (`glyphWords`), whose runs are split into words by the advance
//   widths of the run's font family (Codex review F1: never one font's
//   widths for every font);
// - estimated lines inside the block's box, where the page has no text layer
//   (a scan read by GLM-OCR or OCR'd by Marker): the block's words are laid
//   out over as many lines as its box holds. Honest, approximate.
// A formula, table or figure is one region: the block's own box.
//
// Every coordinate is in PDF points with the origin at the top left of the
// page as shown (the crop box after rotation), the space the extraction's
// boxes use, so nothing here depends on zoom.

import { keyOf, type Token } from "./tokens";

export type Box = [number, number, number, number];

/** One pdf.js text item (`page.getTextContent().items`). */
export interface GlyphItem {
  str: string;
  transform: number[];
  width: number;
  height: number;
  hasEOL?: boolean;
  /** The item's font (a key of the text content's `styles`). */
  fontName?: string;
}

/** pdf.js's text styles (`page.getTextContent().styles`): each font's
 *  fallback family ("serif", "sans-serif" or "monospace"). */
export type TextStyles = Readonly<Record<string, { fontFamily?: string } | undefined>>;

/** A word of the page's text layer. */
export interface GlyphWord {
  text: string;
  key: string;
  box: Box;
}

export interface BlockLine {
  y0: number;
  y1: number;
  /** The block's units on this line, in reading order. */
  units: number[];
}

export interface BlockGeometry {
  source: "text_layer" | "estimated" | "region";
  /** Per unit: its boxes (two for a word hyphenated across a line break). */
  boxes: Box[][];
  /** Per unit: the line its first box is on. */
  line: number[];
  /** Per unit, per box: the line the box is on. */
  boxLines: number[][];
  lines: BlockLine[];
}

// ---- the text layer's words -----------------------------------------------------

// Relative advance widths (per 1000 em) for splitting a text item into
// words: pdf.js's text content gives one width per item, not per glyph. The
// item's font family picks the table, as pdf.js's own text layer picks the
// family it measures a run in: Helvetica's AFM for sans-serif, Times-Roman's
// for serif, one width for every glyph of a monospaced font. Exact for the
// standard fonts; for an embedded font only an estimate, which the page's
// operator list replaces (`operatorWords`).
const HELVETICA: Record<string, number> = (() => {
  const table: Record<string, number> = {};
  const rows: Array<[string, number]> = [
    [" ", 278], ["!", 278], ['"', 355], ["#", 556], ["$", 556], ["%", 889], ["&", 667], ["'", 191],
    ["(", 333], [")", 333], ["*", 389], ["+", 584], [",", 278], ["-", 333], [".", 278], ["/", 278],
    [":", 278], [";", 278], ["<", 584], ["=", 584], [">", 584], ["?", 556], ["@", 1015], ["[", 278],
    ["\\", 278], ["]", 278], ["^", 469], ["_", 556], ["`", 333], ["{", 334], ["|", 260], ["}", 334], ["~", 584],
    ["A", 667], ["B", 667], ["C", 722], ["D", 722], ["E", 667], ["F", 611], ["G", 778], ["H", 722], ["I", 278],
    ["J", 500], ["K", 667], ["L", 556], ["M", 833], ["N", 722], ["O", 778], ["P", 667], ["Q", 778], ["R", 722],
    ["S", 667], ["T", 611], ["U", 722], ["V", 667], ["W", 944], ["X", 667], ["Y", 667], ["Z", 611],
    ["a", 556], ["b", 556], ["c", 500], ["d", 556], ["e", 556], ["f", 278], ["g", 556], ["h", 556], ["i", 222],
    ["j", 222], ["k", 500], ["l", 222], ["m", 833], ["n", 556], ["o", 556], ["p", 556], ["q", 556], ["r", 333],
    ["s", 500], ["t", 278], ["u", 556], ["v", 500], ["w", 722], ["x", 500], ["y", 500], ["z", 500],
  ];
  for (const [ch, width] of rows) table[ch] = width;
  for (let digit = 0; digit <= 9; digit++) table[String(digit)] = 556;
  return table;
})();

const TIMES: Record<string, number> = (() => {
  const table: Record<string, number> = {};
  const rows: Array<[string, number]> = [
    [" ", 250], ["!", 333], ['"', 408], ["#", 500], ["$", 500], ["%", 833], ["&", 778], ["'", 180],
    ["(", 333], [")", 333], ["*", 500], ["+", 564], [",", 250], ["-", 333], [".", 250], ["/", 278],
    [":", 278], [";", 278], ["<", 564], ["=", 564], [">", 564], ["?", 444], ["@", 921], ["[", 333],
    ["\\", 278], ["]", 333], ["^", 469], ["_", 500], ["`", 333], ["{", 480], ["|", 200], ["}", 480], ["~", 541],
    ["A", 722], ["B", 667], ["C", 667], ["D", 722], ["E", 611], ["F", 556], ["G", 722], ["H", 722], ["I", 333],
    ["J", 389], ["K", 722], ["L", 611], ["M", 889], ["N", 722], ["O", 722], ["P", 556], ["Q", 722], ["R", 667],
    ["S", 556], ["T", 611], ["U", 722], ["V", 722], ["W", 944], ["X", 722], ["Y", 722], ["Z", 611],
    ["a", 444], ["b", 500], ["c", 444], ["d", 500], ["e", 444], ["f", 333], ["g", 500], ["h", 500], ["i", 278],
    ["j", 278], ["k", 500], ["l", 278], ["m", 778], ["n", 500], ["o", 500], ["p", 500], ["q", 500], ["r", 333],
    ["s", 389], ["t", 278], ["u", 500], ["v", 500], ["w", 722], ["x", 500], ["y", 500], ["z", 444],
  ];
  for (const [ch, width] of rows) table[ch] = width;
  for (let digit = 0; digit <= 9; digit++) table[String(digit)] = 500;
  return table;
})();

type Advance = (ch: string) => number;
const SANS_ADVANCE: Advance = (ch) => HELVETICA[ch] ?? 556;
const SERIF_ADVANCE: Advance = (ch) => TIMES[ch] ?? 500;
const MONO_ADVANCE: Advance = () => 600;

/** The advance widths of a text item's font family (sans-serif when unknown). */
function advanceFor(item: GlyphItem, styles: TextStyles | null | undefined): Advance {
  const family = (item.fontName && styles?.[item.fontName]?.fontFamily) || "";
  if (/monospace/i.test(family)) return MONO_ADVANCE;
  if (/serif/i.test(family) && !/sans-serif/i.test(family)) return SERIF_ADVANCE;
  return SANS_ADVANCE;
}

function multiply(m1: number[], m2: number[]): number[] {
  return [
    m1[0] * m2[0] + m1[2] * m2[1],
    m1[1] * m2[0] + m1[3] * m2[1],
    m1[0] * m2[2] + m1[2] * m2[3],
    m1[1] * m2[2] + m1[3] * m2[3],
    m1[0] * m2[4] + m1[2] * m2[5] + m1[4],
    m1[1] * m2[4] + m1[3] * m2[5] + m1[5],
  ];
}

const ASCENT = 0.8;
const DESCENT = 0.2;

/** The page's text-layer words, in top-left PDF points. `viewportTransform`
 *  is the page's viewport transform at scale 1 (`page.getViewport({scale:
 *  1}).transform`): it moves the PDF's own space to the page as shown.
 *  Rotated or vertical text is left out (nothing to snap a line to). Two
 *  items that touch with no space between them (a letter and its
 *  superscript, an italic run) make one word. `styles` (the text content's)
 *  says each item's font family, whose widths split the item into words. */
export function glyphWords(
  items: readonly GlyphItem[],
  viewportTransform: readonly number[],
  styles?: TextStyles | null,
): GlyphWord[] {
  const words: GlyphWord[] = [];
  const state: { open: { text: string; box: Box; height: number } | null } = { open: null };
  const flush = () => {
    if (state.open && state.open.text) words.push({ text: state.open.text, key: keyOf(state.open.text), box: state.open.box });
    state.open = null;
  };
  const xScale = Math.hypot(viewportTransform[0], viewportTransform[1]) || 1;
  for (const item of items) {
    if (typeof item.str !== "string" || item.str.length === 0 || !Array.isArray(item.transform)) {
      if (item.hasEOL) flush();
      continue;
    }
    const tx = multiply(viewportTransform as number[], item.transform);
    if (Math.abs(Math.atan2(tx[1], tx[0])) > 0.02) {
      flush();
      continue;
    }
    const height = Math.hypot(tx[2], tx[3]) || item.height || 0;
    const width = item.width * xScale;
    if (height <= 0 || !(width >= 0)) continue;
    const left = tx[4];
    const top = tx[5] - height * ASCENT;
    const bottom = tx[5] + height * DESCENT;
    const chars = Array.from(item.str);
    const advance = advanceFor(item, styles);
    const total = chars.reduce((sum, ch) => sum + advance(ch), 0) || 1;
    // A run touching the open word (no space between them) continues it.
    const open = state.open;
    const touches =
      open !== null &&
      !/\s/.test(chars[0] ?? " ") &&
      Math.abs(left - open.box[2]) <= 0.25 * Math.max(height, open.height) &&
      top < open.box[3] &&
      bottom > open.box[1];
    if (!touches) flush();
    let cursor = 0;
    for (const ch of chars) {
      const x0 = left + (cursor / total) * width;
      cursor += advance(ch);
      const x1 = left + (cursor / total) * width;
      if (/\s/.test(ch)) {
        flush();
        continue;
      }
      const current = state.open;
      if (current === null) {
        state.open = { text: ch, box: [x0, top, x1, bottom], height };
      } else {
        current.text += ch;
        current.box = [
          Math.min(current.box[0], x0),
          Math.min(current.box[1], top),
          Math.max(current.box[2], x1),
          Math.max(current.box[3], bottom),
        ];
        current.height = Math.max(current.height, height);
      }
    }
    if (item.hasEOL) flush();
  }
  flush();
  return words;
}

// ---- the page's words from its operator list ---------------------------------------

/** A page's operator list (`page.getOperatorList()`). */
export interface OperatorListLike {
  fnArray: ArrayLike<number>;
  argsArray: ArrayLike<unknown>;
}

/** What a glyph's placement needs of its font (pdf.js's loaded font object,
 *  `page.commonObjs.get(fontName)`). */
export interface PdfFontInfo {
  fontMatrix?: ArrayLike<number> | null;
  isType3Font?: boolean;
  vertical?: boolean;
  bbox?: ArrayLike<number> | null;
}

/** The operator ids (pdf.js's `OPS`) the placement reads. */
export type OpsTable = Readonly<Record<string, number>>;

interface PaintState {
  ctm: number[];
  textMatrix: number[];
  x: number;
  y: number;
  lineX: number;
  lineY: number;
  font: PdfFontInfo | null;
  fontSize: number;
  fontDirection: number;
  charSpacing: number;
  wordSpacing: number;
  hScale: number;
  leading: number;
  rise: number;
}

const IDENTITY = [1, 0, 0, 1, 0, 0];
const FONT_IDENTITY = [0.001, 0, 0, 0.001, 0, 0];
/** pdf.js's own thresholds (its text content): a gap wider than this share
 *  of the font size is a space; a jump back further than this starts anew. */
const SPACE_GAP_EM = 0.102;
const BACK_GAP_EM = 0.2;

function matrixOf(value: unknown): number[] | null {
  if (value === null || typeof value !== "object" || typeof (value as ArrayLike<number>).length !== "number") return null;
  const matrix = Array.from(value as ArrayLike<number>, Number).slice(0, 6);
  return matrix.length === 6 && matrix.every(Number.isFinite) ? matrix : null;
}

function numberArg(args: unknown, index = 0): number {
  const value = Array.isArray(args) ? Number(args[index]) : NaN;
  return Number.isFinite(value) ? value : 0;
}

function apply(m: readonly number[], x: number, y: number): [number, number] {
  return [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
}

/** The page's words where pdf.js paints their glyphs, in top-left PDF points:
 *  the operator list is walked as pdf.js's canvas walks it (the graphics and
 *  text state, form XObjects, groups), and each glyph advances by its own
 *  width in its own font. A space glyph, a gap wider than a space or a jump
 *  to another line ends a word; a glyph touching the word before it (a
 *  superscript, an italic run, a kern) continues it. Rotated and vertical
 *  text is left out, as in `glyphWords`; annotations' appearances too (they
 *  are not the page's text). `fontOf` gives a font by its loaded name. */
export function operatorWords(
  opList: OperatorListLike,
  ops: OpsTable,
  fontOf: (name: string) => PdfFontInfo | null,
  viewportTransform: readonly number[],
): GlyphWord[] {
  const words: GlyphWord[] = [];
  let open: { text: string; box: Box; height: number } | null = null;
  // Where the next glyph starts if it continues the open word (page points).
  let pen: [number, number] | null = null;
  const flush = () => {
    if (open && open.text) words.push({ text: open.text, key: keyOf(open.text), box: open.box });
    open = null;
  };
  let state: PaintState = {
    ctm: [...IDENTITY], textMatrix: [...IDENTITY], x: 0, y: 0, lineX: 0, lineY: 0, font: null, fontSize: 0,
    fontDirection: 1, charSpacing: 0, wordSpacing: 0, hScale: 1, leading: 0, rise: 0,
  };
  const stack: PaintState[] = [];
  const save = () => stack.push({ ...state, ctm: [...state.ctm], textMatrix: [...state.textMatrix] });
  const restore = () => {
    const previous = stack.pop();
    if (previous) state = previous;
  };
  const moveText = (x: number, y: number) => {
    state.lineX += x;
    state.lineY += y;
    state.x = state.lineX;
    state.y = state.lineY;
  };
  let inAnnotation = 0;

  const showText = (glyphs: unknown) => {
    if (!Array.isArray(glyphs)) return;
    const font = state.font ?? {};
    const fontSize = state.fontSize;
    if (fontSize === 0) return;
    const type3 = Boolean(font.isType3Font);
    const fontMatrix = matrixOf(font.fontMatrix) ?? FONT_IDENTITY;
    const hs = state.hScale * state.fontDirection;
    const m = multiply(viewportTransform as number[], multiply(state.ctm, state.textMatrix));
    const upright = Math.abs(Math.atan2(m[1], m[0])) <= 0.02 && !font.vertical && inAnnotation === 0;
    // The em's height on the page: pdf.js's text content's for a Type3 font
    // drawn at size 1 or less (its glyph box's height in its own units).
    let em = fontSize;
    if (type3 && fontSize <= 1 && fontMatrix.join() !== FONT_IDENTITY.join()) {
      const bbox = Array.from(font.bbox ?? [], Number);
      const glyphHeight = bbox.length >= 4 ? bbox[3] - bbox[1] : 0;
      if (glyphHeight > 0) em *= glyphHeight * fontMatrix[3];
    }
    const height = Math.abs(em) * Math.hypot(m[2], m[3]);
    const baseline = state.y + state.rise;
    let x = 0;
    for (const glyph of glyphs) {
      if (typeof glyph === "number") {
        x -= (glyph * fontSize) / 1000;
        continue;
      }
      if (glyph === null || typeof glyph !== "object") continue;
      const entry = glyph as { unicode?: unknown; width?: unknown; isSpace?: unknown };
      const width = Number(entry.width) || 0;
      const isSpaceGlyph = entry.isSpace === true;
      const spacing = (isSpaceGlyph ? state.wordSpacing : 0) + state.charSpacing;
      const painted = type3 ? (width * fontMatrix[0] + fontMatrix[4]) * fontSize : width * fontSize * fontMatrix[0];
      const advance = painted + (type3 ? spacing : spacing * state.fontDirection);
      const text = typeof entry.unicode === "string" ? entry.unicode : "";
      if (!upright || !(height > 0)) {
        x += advance;
        flush();
        pen = null;
        continue;
      }
      const [x0, y0] = apply(m, state.x + x * hs, baseline);
      const [x1] = apply(m, state.x + (x + painted) * hs, baseline);
      const next = apply(m, state.x + (x + advance) * hs, baseline);
      x += advance;
      if (isSpaceGlyph || (text.length > 0 && /^\s+$/.test(text))) {
        flush();
        pen = next;
        continue;
      }
      const box: Box = [Math.min(x0, x1), y0 - height * ASCENT, Math.max(x0, x1), y0 + height * DESCENT];
      const current = open as { text: string; box: Box; height: number } | null;
      let joins = false;
      if (current !== null && pen !== null) {
        const tolerance = Math.max(height, current.height);
        const direction = x1 >= x0 ? 1 : -1;
        const gap = (x0 - pen[0]) * direction;
        joins = gap <= SPACE_GAP_EM * tolerance && gap >= -BACK_GAP_EM * tolerance && box[1] < current.box[3] && box[3] > current.box[1];
      }
      if (current !== null && joins) {
        current.text += text;
        current.box = [
          Math.min(current.box[0], box[0]),
          Math.min(current.box[1], box[1]),
          Math.max(current.box[2], box[2]),
          Math.max(current.box[3], box[3]),
        ];
        current.height = Math.max(current.height, height);
      } else {
        flush();
        open = { text, box, height };
      }
      pen = next;
    }
    state.x += x * hs;
  };

  const { fnArray, argsArray } = opList;
  for (let index = 0; index < fnArray.length; index++) {
    const fn = fnArray[index];
    const args = argsArray[index] as unknown[] | null | undefined;
    switch (fn) {
      case ops.save:
        save();
        break;
      case ops.restore:
        restore();
        break;
      case ops.transform: {
        const matrix = matrixOf(args);
        if (matrix) state.ctm = multiply(state.ctm, matrix);
        break;
      }
      case ops.paintFormXObjectBegin: {
        save();
        const matrix = matrixOf(Array.isArray(args) ? args[0] : null);
        if (matrix) state.ctm = multiply(state.ctm, matrix);
        break;
      }
      case ops.paintFormXObjectEnd:
        restore();
        break;
      case ops.beginGroup: {
        save();
        const group = Array.isArray(args) ? (args[0] as { matrix?: unknown } | null) : null;
        const matrix = matrixOf(group?.matrix);
        if (matrix) state.ctm = multiply(state.ctm, matrix);
        break;
      }
      case ops.endGroup:
        restore();
        break;
      case ops.beginAnnotation:
        inAnnotation += 1;
        break;
      case ops.endAnnotation:
        inAnnotation = Math.max(0, inAnnotation - 1);
        break;
      case ops.beginText:
        state.textMatrix = [...IDENTITY];
        state.x = state.lineX = 0;
        state.y = state.lineY = 0;
        break;
      case ops.setCharSpacing:
        state.charSpacing = numberArg(args);
        break;
      case ops.setWordSpacing:
        state.wordSpacing = numberArg(args);
        break;
      case ops.setHScale:
        state.hScale = numberArg(args) / 100;
        break;
      case ops.setLeading:
        state.leading = -numberArg(args);
        break;
      case ops.setFont: {
        const name = Array.isArray(args) ? String(args[0] ?? "") : "";
        let size = numberArg(args, 1);
        state.fontDirection = size < 0 ? -1 : 1;
        if (size < 0) size = -size;
        state.font = fontOf(name);
        state.fontSize = size;
        break;
      }
      case ops.setTextRise:
        state.rise = numberArg(args);
        break;
      case ops.moveText:
        moveText(numberArg(args, 0), numberArg(args, 1));
        break;
      case ops.setLeadingMoveText:
        state.leading = numberArg(args, 1);
        moveText(numberArg(args, 0), numberArg(args, 1));
        break;
      case ops.setTextMatrix: {
        const matrix = matrixOf(Array.isArray(args) && args.length === 1 ? args[0] : args);
        if (matrix) state.textMatrix = matrix;
        state.x = state.lineX = 0;
        state.y = state.lineY = 0;
        break;
      }
      case ops.nextLine:
        moveText(0, state.leading);
        break;
      case ops.showText:
      case ops.showSpacedText:
        showText(Array.isArray(args) ? args[0] : null);
        break;
      case ops.nextLineShowText:
        moveText(0, state.leading);
        showText(Array.isArray(args) ? args[0] : null);
        break;
      case ops.nextLineSetSpacingShowText:
        state.wordSpacing = numberArg(args, 0);
        state.charSpacing = numberArg(args, 1);
        moveText(0, state.leading);
        showText(Array.isArray(args) ? args[2] : null);
        break;
      default:
        break;
    }
  }
  flush();
  return words;
}

// ---- the words of one block, in lines ---------------------------------------------

interface Line {
  words: GlyphWord[];
  cy: number;
  height: number;
  y0: number;
  y1: number;
}

function center(box: Box): [number, number] {
  return [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2];
}

/** The block's text-layer words grouped into lines, top to bottom, each line
 *  left to right. A superscript or subscript stays on its line. */
export function intoLines(words: readonly GlyphWord[]): Line[] {
  const sorted = [...words].sort((a, b) => center(a.box)[1] - center(b.box)[1]);
  const lines: Line[] = [];
  for (const word of sorted) {
    const [, cy] = center(word.box);
    const height = word.box[3] - word.box[1];
    const last = lines[lines.length - 1];
    if (last && cy - last.cy <= 0.5 * Math.max(last.height, height)) {
      last.words.push(word);
      last.cy = (last.cy * (last.words.length - 1) + cy) / last.words.length;
      last.height = Math.max(last.height, height);
      last.y0 = Math.min(last.y0, word.box[1]);
      last.y1 = Math.max(last.y1, word.box[3]);
    } else {
      lines.push({ words: [word], cy, height, y0: word.box[1], y1: word.box[3] });
    }
  }
  for (const line of lines) line.words.sort((a, b) => a.box[0] - b.box[0]);
  return lines;
}

const HYPHENS = /[-­‐‑]$/;

interface Piece {
  box: Box;
  /** The line (of the block's text-layer lines) the box is on. */
  line: number;
}

interface GlyphToken {
  key: string;
  /** Its boxes in order (two for a word hyphenated across a line break). */
  pieces: Piece[];
  glyphs: number;
}

/** The block's glyph words as tokens in reading order, with a word broken by
 *  a hyphen at a line end joined to its other half when the extraction has
 *  the whole word. */
function glyphTokens(lines: Line[], tokenKeys: ReadonlySet<string>): GlyphToken[] {
  const out: GlyphToken[] = [];
  let carry: GlyphToken | null = null;
  for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
    const line = lines[lineIndex];
    for (let wordIndex = 0; wordIndex < line.words.length; wordIndex++) {
      const word = line.words[wordIndex];
      const glyphs = Math.max(1, Array.from(word.text).length);
      const piece: Piece = { box: word.box, line: lineIndex };
      if (carry !== null) {
        const held: GlyphToken = carry;
        carry = null;
        if (wordIndex === 0 && tokenKeys.has(held.key + word.key)) {
          out.push({ key: held.key + word.key, pieces: [...held.pieces, piece], glyphs: held.glyphs + glyphs });
          continue;
        }
        out.push(held);
      }
      const lineEnd = wordIndex === line.words.length - 1 && lineIndex < lines.length - 1;
      const stem = keyOf(word.text.replace(HYPHENS, ""));
      if (lineEnd && HYPHENS.test(word.text) && stem) {
        carry = { key: stem, pieces: [piece], glyphs };
        continue;
      }
      out.push({ key: word.key, pieces: [piece], glyphs });
    }
  }
  if (carry !== null) out.push(carry);
  return out;
}

// ---- alignment ----------------------------------------------------------------------

const LOOKAHEAD = 12;

/** Pairs (extraction token, glyph token) with equal non-empty keys, in order:
 *  a greedy walk with a short lookahead. The two sequences are mostly the same
 *  words; what differs is maths (junk or missing glyphs), ligatures already
 *  folded by NFKC, and the odd glyph the extraction dropped. */
export function alignKeys(tokens: readonly string[], glyphs: readonly string[]): Array<[number, number]> {
  const pairs: Array<[number, number]> = [];
  let i = 0;
  let j = 0;
  while (i < tokens.length && j < glyphs.length) {
    if (tokens[i] && tokens[i] === glyphs[j]) {
      pairs.push([i, j]);
      i += 1;
      j += 1;
      continue;
    }
    let skipGlyphs = -1;
    let skipTokens = -1;
    if (tokens[i]) {
      for (let k = 1; k <= LOOKAHEAD && j + k < glyphs.length; k++) {
        if (glyphs[j + k] === tokens[i]) {
          skipGlyphs = k;
          break;
        }
      }
    }
    if (glyphs[j]) {
      for (let k = 1; k <= LOOKAHEAD && i + k < tokens.length; k++) {
        if (tokens[i + k] === glyphs[j]) {
          skipTokens = k;
          break;
        }
      }
    }
    if (skipGlyphs !== -1 && (skipTokens === -1 || skipGlyphs <= skipTokens)) j += skipGlyphs;
    else if (skipTokens !== -1) i += skipTokens;
    else {
      i += 1;
      j += 1;
    }
  }
  return pairs;
}

// ---- spreading tokens over glyph runs ------------------------------------------------

/** Lay `weights` (one per token) along the glyph pieces in order, each token
 *  taking its share of their total width: a token may get part of a glyph
 *  word or span several. Returns the boxes (with lines) per token. */
function spread(weights: readonly number[], pieces: ReadonlyArray<Piece>): Piece[][] {
  const widths = pieces.map((piece) => Math.max(0.01, piece.box[2] - piece.box[0]));
  const totalWidth = widths.reduce((a, b) => a + b, 0);
  const totalWeight = weights.reduce((a, b) => a + b, 0) || 1;
  const locate = (at: number): Piece => {
    let cumulative = 0;
    for (let index = 0; index < pieces.length; index++) {
      if (at <= cumulative + widths[index] || index === pieces.length - 1) {
        const piece = pieces[index];
        const x = Math.min(piece.box[2], piece.box[0] + Math.max(0, at - cumulative));
        return { box: [x, piece.box[1], x + 0.5, piece.box[3]], line: piece.line };
      }
      cumulative += widths[index];
    }
    const piece = pieces[pieces.length - 1];
    return { box: [piece.box[2], piece.box[1], piece.box[2] + 0.5, piece.box[3]], line: piece.line };
  };
  const out: Piece[][] = [];
  let from = 0;
  for (const weight of weights) {
    const to = from + (weight / totalWeight) * totalWidth;
    const parts: Piece[] = [];
    let cumulative = 0;
    pieces.forEach((piece, index) => {
      const a = cumulative;
      cumulative += widths[index];
      const lo = Math.max(a, from);
      const hi = Math.min(cumulative, to);
      if (hi - lo <= 1e-6) return;
      const x0 = piece.box[0] + (lo - a);
      const x1 = piece.box[0] + (hi - a);
      const last = parts[parts.length - 1];
      if (last && last.line === piece.line) {
        last.box = [Math.min(last.box[0], x0), Math.min(last.box[1], piece.box[1]), Math.max(last.box[2], x1), Math.max(last.box[3], piece.box[3])];
      } else {
        parts.push({ box: [x0, piece.box[1], x1, piece.box[3]], line: piece.line });
      }
    });
    out.push(parts.length ? parts : [locate(from)]);
    from = to;
  }
  return out;
}

// ---- one block ---------------------------------------------------------------------

/** The block geometry from each unit's pieces: lines renumbered top to bottom
 *  over the lines that hold a unit, each line's extent its pieces' (and its
 *  text line's, when known). */
function finalize(source: BlockGeometry["source"], parts: Piece[][], extents: ReadonlyArray<{ y0: number; y1: number }>): BlockGeometry {
  const used = [...new Set(parts.map((pieces) => pieces[0]?.line ?? 0))].sort((a, b) => a - b);
  const renumber = new Map(used.map((raw, index) => [raw, index] as const));
  const lines: BlockLine[] = used.map((raw) => ({
    y0: extents[raw]?.y0 ?? Infinity,
    y1: extents[raw]?.y1 ?? -Infinity,
    units: [],
  }));
  const line = parts.map((pieces) => renumber.get(pieces[0]?.line ?? 0) ?? 0);
  parts.forEach((pieces, unit) => {
    const entry = lines[line[unit]];
    entry.units.push(unit);
    for (const piece of pieces) {
      const target = lines[renumber.get(piece.line) ?? line[unit]];
      target.y0 = Math.min(target.y0, piece.box[1]);
      target.y1 = Math.max(target.y1, piece.box[3]);
    }
  });
  const boxLines = parts.map((pieces, unit) => pieces.map((piece) => renumber.get(piece.line) ?? line[unit]));
  return { source, boxes: parts.map((pieces) => pieces.map((piece) => piece.box)), line, boxLines, lines };
}

/** The region geometry of a formula, table or figure: one unit, its box. */
export function regionGeometry(bbox: Box): BlockGeometry {
  return { source: "region", boxes: [[bbox]], line: [0], boxLines: [[0]], lines: [{ y0: bbox[1], y1: bbox[3], units: [0] }] };
}

/** Words laid out over the lines the block's box holds, when the page has no
 *  text layer for it: the box is filled line by line, each full line spread
 *  across the box's width (book text is justified), the last line at the
 *  average glyph width. Approximate, and marked so. */
export function estimatedGeometry(tokens: readonly Token[], bbox: Box): BlockGeometry {
  const width = Math.max(1, bbox[2] - bbox[0]);
  const height = Math.max(1, bbox[3] - bbox[1]);
  if (!tokens.length) return { source: "estimated", boxes: [], line: [], boxLines: [], lines: [] };
  const weights = tokens.map((token) => token.glyphs + 1);
  const totalGlyphs = weights.reduce((a, b) => a + b, 0);
  // Glyph width ≈ 0.5 em and leading ≈ 1.2 em fill the box: 0.6 em² per glyph.
  const em = Math.sqrt((width * height) / (0.6 * totalGlyphs));
  const lineCount = Math.max(1, Math.min(tokens.length, Math.round(height / (1.2 * em))));
  const perLine = totalGlyphs / lineCount;
  const lineOf: number[] = [];
  let cumulative = 0;
  for (const weight of weights) {
    lineOf.push(Math.min(lineCount - 1, Math.floor((cumulative + weight / 2) / perLine)));
    cumulative += weight;
  }
  const lineHeight = height / lineCount;
  const parts: Piece[][] = tokens.map(() => []);
  const averageGlyph = width / perLine;
  for (let lineIndex = 0; lineIndex < lineCount; lineIndex++) {
    const members = lineOf.flatMap((value, unit) => (value === lineIndex ? [unit] : []));
    if (!members.length) continue;
    const lineWeight = members.reduce((sum, unit) => sum + weights[unit], 0);
    const last = lineIndex === lineCount - 1 && lineCount > 1;
    const glyphWidth = last ? Math.min(averageGlyph, width / lineWeight) : width / lineWeight;
    const y0 = bbox[1] + lineIndex * lineHeight;
    let x = bbox[0];
    for (const unit of members) {
      const w = Math.max(0.5, (weights[unit] - 1) * glyphWidth);
      parts[unit] = [{ box: [x, y0, x + w, y0 + lineHeight], line: lineIndex }];
      x += weights[unit] * glyphWidth;
    }
  }
  const extents = Array.from({ length: lineCount }, (_, lineIndex) => ({
    y0: bbox[1] + lineIndex * lineHeight,
    y1: bbox[1] + (lineIndex + 1) * lineHeight,
  }));
  return finalize("estimated", parts, extents);
}

/** The block's word boxes from the page's text-layer words that fall in it,
 *  aligned to the extraction's tokens; with no word in it, estimated. */
export function textLayerGeometry(tokens: readonly Token[], words: readonly GlyphWord[], bbox: Box): BlockGeometry {
  if (!tokens.length) return { source: "text_layer", boxes: [], line: [], boxLines: [], lines: [] };
  if (!words.length) return estimatedGeometry(tokens, bbox);
  const lines = intoLines(words);
  const glyphs = glyphTokens(lines, new Set(tokens.map((token) => token.key).filter(Boolean)));
  const pairs = alignKeys(tokens.map((token) => token.key), glyphs.map((glyph) => glyph.key));
  if (!pairs.length) {
    // Nothing in common (a text layer of junk glyphs): the words, in order,
    // over the glyph runs that are there.
    const laid = spread(tokens.map((token) => token.glyphs + 1), glyphs.flatMap((glyph) => glyph.pieces));
    return finalize("text_layer", laid, lines);
  }
  const parts: Piece[][] = tokens.map(() => []);
  for (const [i, j] of pairs) parts[i] = glyphs[j].pieces.map((piece) => ({ box: [...piece.box] as Box, line: piece.line }));
  const matchedGlyphs = pairs.map(([, j]) => glyphs[j]);
  const glyphWidth = (() => {
    const w = matchedGlyphs.reduce((sum, glyph) => sum + glyph.pieces.reduce((s, piece) => s + (piece.box[2] - piece.box[0]), 0), 0);
    const n = matchedGlyphs.reduce((sum, glyph) => sum + glyph.glyphs, 0);
    return n > 0 ? w / n : 4;
  })();
  // The gaps between matched pairs (and before the first, after the last).
  const anchors: Array<[number, number]> = [[-1, -1], ...pairs, [tokens.length, glyphs.length]];
  for (let k = 0; k < anchors.length - 1; k++) {
    const [i0, j0] = anchors[k];
    const [i1, j1] = anchors[k + 1];
    const gap = Array.from({ length: Math.max(0, i1 - i0 - 1) }, (_, n) => i0 + 1 + n);
    if (!gap.length) continue;
    const gapPieces = glyphs.slice(j0 + 1, j1).flatMap((glyph) => glyph.pieces);
    if (gapPieces.length) {
      const laid = spread(gap.map((unit) => tokens[unit].glyphs + 1), gapPieces);
      gap.forEach((unit, n) => {
        parts[unit] = laid[n];
      });
      continue;
    }
    // No glyph for them (maths the text layer does not carry): placed just
    // after the matched word before them, else just before the one after.
    const before = i0 >= 0 ? parts[i0][parts[i0].length - 1] : null;
    const after = i1 < tokens.length ? parts[i1][0] : null;
    const host = (before ?? after) as Piece;
    const total = gap.reduce((sum, unit) => sum + (tokens[unit].glyphs + 1) * glyphWidth, 0);
    let x = before ? before.box[2] + glyphWidth * 0.3 : host.box[0] - total;
    const room = before && after && after.line === before.line ? Math.max(0, after.box[0] - x) : Infinity;
    const squeeze = room < total ? room / total : 1;
    for (const unit of gap) {
      const w = Math.max(0.5, tokens[unit].glyphs * glyphWidth * squeeze);
      const x0 = Math.max(bbox[0], Math.min(x, bbox[2] - 0.5));
      parts[unit] = [{ box: [x0, host.box[1], Math.max(x0 + 0.5, Math.min(x0 + w, bbox[2])), host.box[3]], line: host.line }];
      x += (tokens[unit].glyphs + 1) * glyphWidth * squeeze;
    }
  }
  return finalize("text_layer", parts, lines);
}

/** Which block each text-layer word belongs to: the smallest block box its
 *  centre falls in (with a small tolerance, boxes from a layout model are
 *  tight). Words in no box (page numbers, a running head with no block) are
 *  left out. Returns words by block index. */
export function assignWords(
  words: readonly GlyphWord[],
  blocks: ReadonlyArray<{ index: number; bbox: Box }>,
): Map<number, GlyphWord[]> {
  const out = new Map<number, GlyphWord[]>();
  for (const word of words) {
    const [cx, cy] = center(word.box);
    const height = word.box[3] - word.box[1];
    let best: { index: number; area: number } | null = null;
    for (const block of blocks) {
      const tolX = 2;
      const tolY = Math.min(4, height * 0.3);
      if (cx < block.bbox[0] - tolX || cx > block.bbox[2] + tolX || cy < block.bbox[1] - tolY || cy > block.bbox[3] + tolY) {
        continue;
      }
      const area = (block.bbox[2] - block.bbox[0]) * (block.bbox[3] - block.bbox[1]);
      if (!best || area < best.area) best = { index: block.index, area };
    }
    if (best) {
      const list = out.get(best.index) ?? [];
      list.push(word);
      out.set(best.index, list);
    }
  }
  return out;
}
