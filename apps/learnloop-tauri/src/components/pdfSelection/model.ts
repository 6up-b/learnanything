// One selection model for the original PDF (reader-pdf-selection).
//
// The document is the extraction's selectable blocks in reading order (two
// columns read as the extraction reads them, footnotes after the body), each
// a run of units: its words, or the whole block for a formula, table or
// figure. A position is (block, unit); a selection is one or more ranges of
// positions. Everything the Reader does with a selection reads this model:
// - hit-testing a point on a page (PDF points) snaps to a unit;
// - dragging, double/triple click and Shift+arrows move a range's head;
// - the nodes a selection sends are exact slices of each block's own text,
//   with code-point offsets, so the sidecar anchors them exactly
//   (annotations.translate_selection) and Ask, the palette, checks, citations
//   and notes behave as on the extracted text;
// - the copied text is the extraction's (maths as LaTeX);
// - region boxes (selection paint, saved highlights) come from the model's
//   word boxes, never from screen coordinates, so they survive zoom, resize,
//   reload and a re-read (an anchor placed on the open reading).
// Pages' word boxes arrive as pages are drawn: first from the page's text
// content (`setPageText`, its runs split by their font family's widths), then
// from where each glyph is painted (`setPageGlyphs`, the operator list); until
// then a block's words are laid out by estimate, so keyboard moves work
// everywhere.

import type { ReaderPdfBlockDto } from "../../api/dto";
import {
  assignWords,
  estimatedGeometry,
  glyphWords,
  regionGeometry,
  textLayerGeometry,
  type BlockGeometry,
  type Box,
  type GlyphItem,
  type GlyphWord,
  type TextStyles,
} from "./geometry";
import { cleanText, FURNITURE_TYPES, fromCodepoint, isAtomicType, keyOf, toCodepoint, tokenize, type Token } from "./tokens";

export type { Box, GlyphItem, GlyphWord, TextStyles } from "./geometry";

export interface SelBlock {
  index: number;
  spanId: string;
  page: number;
  bbox: Box;
  blockType: string;
  text: string;
  atomic: boolean;
}

/** A place in the document: a block (reading order) and a unit in it. */
export interface Pos {
  block: number;
  unit: number;
}

/** A selected run, from where it started (anchor) to where it ends (head). */
export interface SelRange {
  anchor: Pos;
  head: Pos;
}

/** One block's part of a selection, as the sidecar anchors it: `start` and
 *  `end` are code points into the block's text, `quote` is that exact slice. */
export interface SpanNode {
  spanId: string;
  quote: string;
  start: number;
  end: number;
}

/** What a selection hands the Reader: the same shape the extracted-text view
 *  sends (`ReaderSelection`), plus the text it copies. */
export interface SelectionPayload {
  spanId: string;
  quote: string;
  nodes: SpanNode[];
  text: string;
  /** Reader RW5a: a Ctrl+drag box over a figure (its block, page and box in
   *  the block's coordinate space), when the Reader asks for regions. */
  region?: { spanId: string; page: number; bbox: number[] };
}

function isSelectable(block: ReaderPdfBlockDto): boolean {
  return (
    !FURNITURE_TYPES.has(block.blockType ?? "") &&
    (block.text ?? "").trim().length > 0 &&
    Array.isArray(block.bbox) &&
    block.bbox.length === 4
  );
}

export class SelectionModel {
  readonly blocks: SelBlock[] = [];
  /** Bumps whenever a page's word boxes change: overlays recompute. */
  version = 0;
  private readonly onPage = new Map<number, number[]>();
  /** Every box on a page, selectable or not (a running head's words must
   *  land in its own box, not in the nearest paragraph). */
  private readonly allBoxes = new Map<number, Array<{ index: number; bbox: Box }>>();
  private readonly bySpan = new Map<string, number>();
  private readonly tokenCache = new Map<number, Token[]>();
  private readonly pageGeometry = new Map<number, Map<number, BlockGeometry>>();
  /** Pages whose words are placed from their painted glyphs. */
  private readonly painted = new Set<number>();
  private readonly estimated = new Map<number, BlockGeometry>();

  constructor(source: readonly ReaderPdfBlockDto[]) {
    for (const dto of source) {
      if (!Array.isArray(dto.bbox) || dto.bbox.length !== 4) continue;
      const bbox = dto.bbox as Box;
      const boxes = this.allBoxes.get(dto.page) ?? [];
      if (!isSelectable(dto) || this.bySpan.has(dto.spanId)) {
        boxes.push({ index: -1, bbox });
        this.allBoxes.set(dto.page, boxes);
        continue;
      }
      const index = this.blocks.length;
      this.blocks.push({
        index,
        spanId: dto.spanId,
        page: dto.page,
        bbox,
        blockType: dto.blockType ?? "",
        text: dto.text ?? "",
        atomic: isAtomicType(dto.blockType),
      });
      boxes.push({ index, bbox });
      this.allBoxes.set(dto.page, boxes);
      this.bySpan.set(dto.spanId, index);
      const list = this.onPage.get(dto.page) ?? [];
      list.push(index);
      this.onPage.set(dto.page, list);
    }
  }

  blockIndex(spanId: string): number | undefined {
    return this.bySpan.get(spanId);
  }

  blocksOnPage(page: number): readonly number[] {
    return this.onPage.get(page) ?? [];
  }

  /** Whether a point lies in a box nothing can be selected in (a figure with
   *  no text, a running head) and in no selectable block. */
  inDeadBox(page: number, x: number, y: number): boolean {
    const boxes = this.allBoxes.get(page) ?? [];
    return boxes.some((entry) => entry.index === -1 && inside(entry.bbox, x, y))
      && !boxes.some((entry) => entry.index !== -1 && inside(entry.bbox, x, y, 1));
  }

  /** The block's units (words; one for a formula, table or figure). */
  units(block: number): Token[] {
    let tokens = this.tokenCache.get(block);
    if (!tokens) {
      const entry = this.blocks[block];
      tokens = entry.atomic
        ? [{ start: 0, end: entry.text.length, key: keyOf(entry.text), glyphs: 1, math: true }]
        : tokenize(entry.text);
      this.tokenCache.set(block, tokens);
    }
    return tokens;
  }

  unitCount(block: number): number {
    return this.units(block).length;
  }

  hasPageText(page: number): boolean {
    return this.pageGeometry.has(page);
  }

  /** Whether the page's words are placed from its painted glyphs. */
  hasPageGlyphs(page: number): boolean {
    return this.painted.has(page);
  }

  /** The page's text content arrived (it is being drawn): place its blocks'
   *  words on it. `viewportTransform` is the page viewport's at scale 1;
   *  `styles` (the text content's) gives each run's font family. A page
   *  already placed from its glyphs keeps them. */
  setPageText(page: number, items: readonly GlyphItem[], viewportTransform: readonly number[], styles?: TextStyles | null): void {
    if (this.painted.has(page)) return;
    this.placeWords(page, glyphWords(items, viewportTransform, styles));
  }

  /** Where the page paints each glyph is known (its operator list,
   *  `operatorWords`): its blocks' words are placed from those words. */
  setPageGlyphs(page: number, words: readonly GlyphWord[]): void {
    this.painted.add(page);
    this.placeWords(page, words);
  }

  private placeWords(page: number, words: readonly GlyphWord[]): void {
    const assigned = assignWords(words, this.allBoxes.get(page) ?? []);
    const geometry = new Map<number, BlockGeometry>();
    for (const index of this.blocksOnPage(page)) {
      const block = this.blocks[index];
      geometry.set(
        index,
        block.atomic ? regionGeometry(block.bbox) : textLayerGeometry(this.units(index), assigned.get(index) ?? [], block.bbox),
      );
    }
    this.pageGeometry.set(page, geometry);
    this.version += 1;
  }

  /** The block's word boxes: from its page's text layer once that is known,
   *  else estimated inside its box. */
  geometry(block: number): BlockGeometry {
    const entry = this.blocks[block];
    const fromPage = this.pageGeometry.get(entry.page)?.get(block);
    if (fromPage) return fromPage;
    let estimate = this.estimated.get(block);
    if (!estimate) {
      estimate = entry.atomic ? regionGeometry(entry.bbox) : estimatedGeometry(this.units(block), entry.bbox);
      this.estimated.set(block, estimate);
    }
    return estimate;
  }
}

// ---- positions ------------------------------------------------------------------------

export function comparePos(a: Pos, b: Pos): number {
  return a.block - b.block || a.unit - b.unit;
}

export function ordered(range: SelRange): [Pos, Pos] {
  return comparePos(range.anchor, range.head) <= 0 ? [range.anchor, range.head] : [range.head, range.anchor];
}

export function samePos(a: Pos | null | undefined, b: Pos | null | undefined): boolean {
  return Boolean(a && b && a.block === b.block && a.unit === b.unit);
}

export function blockRange(model: SelectionModel, block: number): SelRange {
  return { anchor: { block, unit: 0 }, head: { block, unit: Math.max(0, model.unitCount(block) - 1) } };
}

/** The next (+1) or previous (-1) unit in reading order, across blocks. */
export function step(model: SelectionModel, pos: Pos, delta: 1 | -1): Pos {
  if (delta === 1) {
    if (pos.unit + 1 < model.unitCount(pos.block)) return { block: pos.block, unit: pos.unit + 1 };
    for (let block = pos.block + 1; block < model.blocks.length; block++) {
      if (model.unitCount(block) > 0) return { block, unit: 0 };
    }
    return pos;
  }
  if (pos.unit > 0) return { block: pos.block, unit: pos.unit - 1 };
  for (let block = pos.block - 1; block >= 0; block--) {
    const count = model.unitCount(block);
    if (count > 0) return { block, unit: count - 1 };
  }
  return pos;
}

function unitCenterX(model: SelectionModel, pos: Pos): number {
  const box = model.geometry(pos.block).boxes[pos.unit]?.[0];
  return box ? (box[0] + box[2]) / 2 : model.blocks[pos.block].bbox[0];
}

function nearestOnLine(model: SelectionModel, block: number, line: number, x: number): Pos {
  const geometry = model.geometry(block);
  const units = geometry.lines[line]?.units ?? [];
  let best = units[0] ?? 0;
  let bestDistance = Infinity;
  for (const unit of units) {
    for (const box of geometry.boxes[unit] ?? []) {
      const distance = x < box[0] ? box[0] - x : x > box[2] ? x - box[2] : 0;
      if (distance < bestDistance) {
        bestDistance = distance;
        best = unit;
      }
    }
  }
  return { block, unit: best };
}

export type HeadMove = "left" | "right" | "up" | "down" | "lineStart" | "lineEnd";

/** Move a selection's head by a word, a line, or to a line's ends. `goalX`
 *  keeps the column over several line moves (as a text editor does). */
export function moveHead(model: SelectionModel, head: Pos, move: HeadMove, goalX?: number | null): { pos: Pos; goalX: number | null } {
  if (move === "left") return { pos: step(model, head, -1), goalX: null };
  if (move === "right") return { pos: step(model, head, 1), goalX: null };
  const geometry = model.geometry(head.block);
  const line = geometry.line[head.unit] ?? 0;
  if (move === "lineStart" || move === "lineEnd") {
    const units = geometry.lines[line]?.units ?? [head.unit];
    return { pos: { block: head.block, unit: move === "lineStart" ? units[0] : units[units.length - 1] }, goalX: null };
  }
  const x = goalX ?? unitCenterX(model, head);
  if (move === "down") {
    if (line + 1 < geometry.lines.length) return { pos: nearestOnLine(model, head.block, line + 1, x), goalX: x };
    for (let block = head.block + 1; block < model.blocks.length; block++) {
      if (model.unitCount(block) > 0) return { pos: nearestOnLine(model, block, 0, x), goalX: x };
    }
    return { pos: head, goalX: x };
  }
  if (line > 0) return { pos: nearestOnLine(model, head.block, line - 1, x), goalX: x };
  for (let block = head.block - 1; block >= 0; block--) {
    if (model.unitCount(block) > 0) {
      const last = model.geometry(block).lines.length - 1;
      return { pos: nearestOnLine(model, block, Math.max(0, last), x), goalX: x };
    }
  }
  return { pos: head, goalX: x };
}

/** The units on the same line as `pos` (a triple click selects its block). */
export function lineRange(model: SelectionModel, pos: Pos): SelRange {
  const geometry = model.geometry(pos.block);
  const units = geometry.lines[geometry.line[pos.unit] ?? 0]?.units ?? [pos.unit];
  return { anchor: { block: pos.block, unit: units[0] }, head: { block: pos.block, unit: units[units.length - 1] } };
}

// ---- hit-testing ------------------------------------------------------------------------

function inside(box: Box, x: number, y: number, tolerance = 0): boolean {
  return x >= box[0] - tolerance && x <= box[2] + tolerance && y >= box[1] - tolerance && y <= box[3] + tolerance;
}

/** The block under (or nearest to) a point on a page; null with no block on it. */
export function blockAt(model: SelectionModel, page: number, x: number, y: number): number | null {
  const candidates = model.blocksOnPage(page);
  if (!candidates.length) return null;
  let best: number | null = null;
  let bestArea = Infinity;
  for (const index of candidates) {
    const box = model.blocks[index].bbox;
    if (!inside(box, x, y, 1)) continue;
    const area = (box[2] - box[0]) * (box[3] - box[1]);
    if (area < bestArea) {
      bestArea = area;
      best = index;
    }
  }
  if (best !== null) return best;
  let bestDistance = Infinity;
  for (const index of candidates) {
    const box = model.blocks[index].bbox;
    const dx = x < box[0] ? box[0] - x : x > box[2] ? x - box[2] : 0;
    const dy = y < box[1] ? box[1] - y : y > box[3] ? y - box[3] : 0;
    // Reading runs down a column: a point beside a column belongs to the
    // line level with it before the one above or below.
    const distance = dy * 3 + dx;
    if (distance < bestDistance) {
      bestDistance = distance;
      best = index;
    }
  }
  return best;
}

/** The unit under (or nearest to) a point on a page, in PDF points. */
export function hitTest(model: SelectionModel, page: number, x: number, y: number): Pos | null {
  // A click on a figure with no text (or a running head) selects nothing,
  // never the nearest caption.
  if (model.inDeadBox(page, x, y)) return null;
  const block = blockAt(model, page, x, y);
  if (block === null || model.unitCount(block) === 0) return null;
  if (model.blocks[block].atomic) return { block, unit: 0 };
  const geometry = model.geometry(block);
  // The line level with the point, else the nearest line.
  let line = 0;
  let lineDistance = Infinity;
  geometry.lines.forEach((entry, index) => {
    const distance = y < entry.y0 ? entry.y0 - y : y > entry.y1 ? y - entry.y1 : 0;
    if (distance < lineDistance) {
      lineDistance = distance;
      line = index;
    }
  });
  // A word hyphenated onto this line from the one above counts here too.
  let best: number | null = null;
  let bestDistance = Infinity;
  geometry.boxes.forEach((boxes, unit) => {
    boxes.forEach((box, piece) => {
      if ((geometry.boxLines[unit]?.[piece] ?? geometry.line[unit]) !== line) return;
      const distance = x < box[0] ? box[0] - x : x > box[2] ? x - box[2] : 0;
      if (distance < bestDistance) {
        bestDistance = distance;
        best = unit;
      }
    });
  });
  return best === null ? { block, unit: 0 } : { block, unit: best };
}

// ---- what a selection is -------------------------------------------------------------

/** One node per block per range: the exact slice of the block's text from the
 *  range's first unit there to its last, with code-point offsets. */
export function selectionNodes(model: SelectionModel, ranges: readonly SelRange[]): SpanNode[] {
  const nodes: SpanNode[] = [];
  const sorted = [...ranges].map(ordered).sort((a, b) => comparePos(a[0], b[0]));
  for (const [lo, hi] of sorted) {
    for (let block = lo.block; block <= hi.block; block++) {
      const units = model.units(block);
      if (!units.length) continue;
      const first = block === lo.block ? Math.min(lo.unit, units.length - 1) : 0;
      const last = block === hi.block ? Math.min(hi.unit, units.length - 1) : units.length - 1;
      if (last < first) continue;
      const text = model.blocks[block].text;
      const start = units[first].start;
      const end = units[last].end;
      nodes.push({
        spanId: model.blocks[block].spanId,
        quote: text.slice(start, end),
        start: toCodepoint(text, start),
        end: toCodepoint(text, end),
      });
    }
  }
  return nodes;
}

const SENTENCE_END = /[.!?:;)\]]$|\$\$$/;
/** Blocks a paragraph can run on between (over a page or column break). */
const PROSE_TYPES: ReadonlySet<string> = new Set(["Text", "TextInlineMath"]);

/** The text a selection copies: each block's part cleaned (one space for the
 *  extraction's line breaks, maths as LaTeX); blocks a paragraph apart, a
 *  paragraph that runs on over a page or column break joined with a space. */
export function selectionText(model: SelectionModel, ranges: readonly SelRange[]): string {
  const nodes = selectionNodes(model, ranges);
  let out = "";
  let previousType = "";
  nodes.forEach((node) => {
    const block = model.blocks[model.blockIndex(node.spanId) ?? 0];
    const piece = cleanText(node.quote, block.blockType);
    if (!piece) return;
    if (out) {
      const runsOn = PROSE_TYPES.has(previousType) && PROSE_TYPES.has(block.blockType)
        && !SENTENCE_END.test(out.trimEnd()) && /^[\p{Ll}(,]/u.test(piece);
      out += runsOn ? " " : "\n\n";
    }
    out += piece;
    previousType = block.blockType;
  });
  return out;
}

/** The selection as the Reader takes it (the extracted-text view's shape):
 *  the primary span is the block carrying most of the selected text, so a
 *  sliver of a neighbour never claims the active passage. */
export function selectionPayload(model: SelectionModel, ranges: readonly SelRange[]): SelectionPayload | null {
  const nodes = selectionNodes(model, ranges).filter((node) => node.quote.trim().length > 0);
  if (!nodes.length) return null;
  const primary = [...nodes].sort((a, b) => b.quote.length - a.quote.length)[0];
  const quote = nodes
    .map((node) => {
      const block = model.blocks[model.blockIndex(node.spanId) ?? 0];
      return cleanText(node.quote, block.blockType).replace(/\s+/g, " ");
    })
    .join(" ")
    .trim();
  return { spanId: primary.spanId, quote, nodes, text: selectionText(model, ranges) };
}

/** The range a saved anchor covers on the open reading: the units of the
 *  block that overlap its code points. Null when the block is not here. */
export function anchorRange(model: SelectionModel, spanId: string, start: number, end: number): SelRange | null {
  const block = model.blockIndex(spanId);
  if (block === undefined) return null;
  const units = model.units(block);
  if (!units.length) return null;
  const text = model.blocks[block].text;
  const from = fromCodepoint(text, Math.max(0, start));
  const to = fromCodepoint(text, Math.max(start, end));
  let first = -1;
  let last = -1;
  units.forEach((unit, index) => {
    const overlaps = unit.end > from && unit.start < to;
    if (overlaps || (from === to && unit.start <= from && from <= unit.end)) {
      if (first === -1) first = index;
      last = index;
    }
  });
  if (first === -1) return null;
  return { anchor: { block, unit: first }, head: { block, unit: last } };
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** A node the extracted-text view made (a native selection of a rendered
 *  block), in the shape the original PDF's model sends: when its quote is in
 *  the block's text once (exactly, or with the extraction's line breaks for
 *  spaces), the exact slice with code-point offsets, so both views anchor,
 *  paint and restore a selection the same way. Otherwise (rendered maths,
 *  a repeated phrase) the node as it is, for the sidecar's own tiers. */
export function exactNode<T extends { spanId: string; quote: string }>(
  blockText: string | null | undefined,
  node: T,
): T | (T & { start: number; end: number }) {
  const text = blockText ?? "";
  const quote = node.quote.trim();
  if (!text || !quote) return node;
  let at = -1;
  let length = 0;
  const first = text.indexOf(quote);
  if (first !== -1) {
    if (text.indexOf(quote, first + 1) !== -1) return node;
    at = first;
    length = quote.length;
  } else {
    const pattern = new RegExp(quote.split(/\s+/).map(escapeRegExp).join("\\s+"), "gu");
    const matches = [...text.matchAll(pattern)];
    if (matches.length !== 1 || matches[0].index === undefined) return node;
    at = matches[0].index;
    length = matches[0][0].length;
  }
  return {
    ...node,
    quote: text.slice(at, at + length),
    start: toCodepoint(text, at),
    end: toCodepoint(text, at + length),
  };
}

/** The ranges a selection's nodes cover here (a selection restored from the
 *  return stack, or made on the extracted text): nodes with offsets by their
 *  offsets, others as their whole block. */
export function rangesFromNodes(
  model: SelectionModel,
  nodes: ReadonlyArray<{ spanId: string; start?: number; end?: number }>,
): SelRange[] {
  const ranges: SelRange[] = [];
  for (const node of nodes) {
    const block = model.blockIndex(node.spanId);
    if (block === undefined) continue;
    const range =
      typeof node.start === "number" && typeof node.end === "number"
        ? anchorRange(model, node.spanId, node.start, node.end)
        : blockRange(model, block);
    if (range) ranges.push(range);
  }
  return ranges;
}

// ---- region boxes ---------------------------------------------------------------------

/** The boxes a set of ranges paints on one page: one per line per block
 *  (the line's selected words, end to end), a formula, table or figure its
 *  own box. PDF points; the caller scales them. */
export function rangeRects(model: SelectionModel, ranges: readonly SelRange[], page: number): Box[] {
  const rects: Box[] = [];
  const onPage = model.blocksOnPage(page);
  if (!onPage.length) return rects;
  const first = onPage[0];
  const last = onPage[onPage.length - 1];
  for (const range of ranges) {
    const [lo, hi] = ordered(range);
    if (hi.block < first || lo.block > last) continue;
    for (let block = Math.max(lo.block, first); block <= Math.min(hi.block, last); block++) {
      if (model.blocks[block].page !== page) continue;
      const count = model.unitCount(block);
      if (!count) continue;
      if (model.blocks[block].atomic) {
        rects.push(model.blocks[block].bbox);
        continue;
      }
      const geometry = model.geometry(block);
      const from = block === lo.block ? lo.unit : 0;
      const to = block === hi.block ? hi.unit : count - 1;
      // One box per line: the line's selected words end to end (a
      // hyphenated word's second half joins the next line's box).
      const perLine = new Map<number, Box>();
      for (let unit = from; unit <= to; unit++) {
        (geometry.boxes[unit] ?? []).forEach((box, piece) => {
          const line = geometry.boxLines[unit]?.[piece] ?? geometry.line[unit] ?? 0;
          const current = perLine.get(line);
          perLine.set(
            line,
            current
              ? [Math.min(current[0], box[0]), Math.min(current[1], box[1]), Math.max(current[2], box[2]), Math.max(current[3], box[3])]
              : ([...box] as Box),
          );
        });
      }
      rects.push(...[...perLine.entries()].sort((a, b) => a[0] - b[0]).map(([, box]) => box));
    }
  }
  return rects;
}

/** Ranges from marquee boxes: every word whose box centre a box holds, and a
 *  formula, table or figure a box covers a quarter of; contiguous runs. */
export function marqueeRanges(model: SelectionModel, boxes: ReadonlyArray<{ page: number; rect: number[] }>): SelRange[] {
  const picked: Pos[] = [];
  const pages = [...new Set(boxes.map((box) => box.page))];
  for (const page of pages) {
    const rects = boxes.filter((box) => box.page === page).map((box) => box.rect as Box);
    for (const block of model.blocksOnPage(page)) {
      const entry = model.blocks[block];
      if (entry.atomic) {
        const area = (entry.bbox[2] - entry.bbox[0]) * (entry.bbox[3] - entry.bbox[1]);
        const covered = rects.some((rect) => {
          const w = Math.min(rect[2], entry.bbox[2]) - Math.max(rect[0], entry.bbox[0]);
          const h = Math.min(rect[3], entry.bbox[3]) - Math.max(rect[1], entry.bbox[1]);
          const rectArea = (rect[2] - rect[0]) * (rect[3] - rect[1]);
          return w > 0 && h > 0 && w * h > 0.25 * Math.min(area, rectArea);
        });
        if (covered) picked.push({ block, unit: 0 });
        continue;
      }
      const geometry = model.geometry(block);
      geometry.boxes.forEach((unitBoxes, unit) => {
        const hit = unitBoxes.some((box) => {
          const cx = (box[0] + box[2]) / 2;
          const cy = (box[1] + box[3]) / 2;
          return rects.some((rect) => inside(rect, cx, cy));
        });
        if (hit) picked.push({ block, unit });
      });
    }
  }
  picked.sort(comparePos);
  const ranges: SelRange[] = [];
  for (const pos of picked) {
    const last = ranges[ranges.length - 1];
    if (last && samePos(step(model, last.head, 1), pos)) last.head = pos;
    else ranges.push({ anchor: pos, head: pos });
  }
  return ranges;
}

/** Whether a point lies on a painted range (a right-click inside the selection). */
export function onRanges(model: SelectionModel, ranges: readonly SelRange[], page: number, x: number, y: number): boolean {
  return rangeRects(model, ranges, page).some((rect) => inside(rect, x, y, 1.5));
}
