// The words of an extraction block, with their offsets in the block's own
// text (reader-pdf-selection). One selection model for the original PDF and
// the extracted text: a selection is a run of these words, so the quote it
// sends is always an exact slice of the block, and anchoring is exact by
// construction (annotations.translate_selection checks text[start:end]).
//
// Offsets here are UTF-16 indices (JavaScript strings); the sidecar's anchors
// are Unicode code points (Python str). `toCodepoint`/`fromCodepoint` convert
// at the wire, so a block with mathematical letters (𝑧, 𝐂, outside the BMP)
// anchors the same text on both sides.

export interface Token {
  /** UTF-16 offsets into the block text. */
  start: number;
  end: number;
  /** Comparison key: letters and digits only, NFKC, lower case, LaTeX
   *  commands dropped. Empty for pure punctuation or pure markup. */
  key: string;
  /** About how many glyphs the token draws on the page (for estimated
   *  layout): markup and LaTeX commands draw nothing. At least 1. */
  glyphs: number;
  /** An inline formula (`$…$`, `\(…\)`): one unit, its LaTeX the quote. */
  math: boolean;
}

/** Blocks selected and quoted whole: their extraction text (LaTeX, a Markdown
 *  table) is the quote; there is no word inside them to snap to. */
export const ATOMIC_TYPES: ReadonlySet<string> = new Set([
  "Equation",
  "Table",
  "TableGroup",
  "Figure",
  "FigureGroup",
  "Picture",
  "PictureGroup",
  "Form",
  "ComplexRegion",
  "Handwriting",
]);

/** Page furniture never joins a selection: running heads and footers repeat
 *  on every page and would pollute one that crosses a page. */
export const FURNITURE_TYPES: ReadonlySet<string> = new Set(["PageHeader", "PageFooter", "TableOfContents"]);

/** Blocks whose line breaks are meaning (code keeps them when copied). */
const VERBATIM_TYPES: ReadonlySet<string> = new Set(["Code"]);

export function isAtomicType(blockType: string | null | undefined): boolean {
  return ATOMIC_TYPES.has(blockType ?? "");
}

const LATEX_COMMAND = /\\[a-zA-Z]+/g;

/** The comparison key of a piece of text (see `Token.key`). */
export function keyOf(text: string): string {
  return text
    .normalize("NFKC")
    .replace(LATEX_COMMAND, " ")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "");
}

function glyphCount(text: string, math: boolean): number {
  if (math) return Math.max(1, keyOf(text).length);
  const visible = text.replace(/\*\*|__|`/g, "").replace(LATEX_COMMAND, "x");
  return Math.max(1, Array.from(visible).length);
}

/** Where the inline formula opening at `at` closes (exclusive), or -1. */
function mathClose(text: string, at: number): number {
  if (text.startsWith("$$", at)) {
    const close = text.indexOf("$$", at + 2);
    return close === -1 ? -1 : close + 2;
  }
  if (text[at] === "$") {
    // `\$` is an escaped currency dollar, never a delimiter.
    for (let i = at + 1; i < text.length; i++) {
      if (text[i] === "\\") {
        i += 1;
        continue;
      }
      if (text[i] === "$") return i + 1;
      // An unclosed dollar in prose stays prose: no formula spans a blank line.
      if (text[i] === "\n" && text[i + 1] === "\n") return -1;
    }
    return -1;
  }
  if (text.startsWith("\\(", at)) {
    const close = text.indexOf("\\)", at + 2);
    return close === -1 ? -1 : close + 2;
  }
  if (text.startsWith("\\[", at)) {
    const close = text.indexOf("\\]", at + 2);
    return close === -1 ? -1 : close + 2;
  }
  return -1;
}

function opensMath(text: string, at: number): boolean {
  if (text[at] === "$") return at === 0 || text[at - 1] !== "\\";
  return text.startsWith("\\(", at) || text.startsWith("\\[", at);
}

/** The block's words: maximal runs of non-space characters, where an inline
 *  formula (which may hold spaces) is part of the run it touches. */
export function tokenize(text: string): Token[] {
  const tokens: Token[] = [];
  let start = -1;
  let math = false;
  const close = (end: number) => {
    if (start === -1) return;
    const piece = text.slice(start, end);
    tokens.push({ start, end, key: keyOf(piece), glyphs: glyphCount(piece, math), math });
    start = -1;
    math = false;
  };
  let i = 0;
  while (i < text.length) {
    const ch = text[i];
    if (/\s/.test(ch)) {
      close(i);
      i += 1;
      continue;
    }
    if (start === -1) start = i;
    if (opensMath(text, i)) {
      const end = mathClose(text, i);
      if (end !== -1) {
        math = true;
        i = end;
        continue;
      }
    }
    i += 1;
  }
  close(text.length);
  return tokens;
}

// ---- code points ------------------------------------------------------------

/** The code-point offset of UTF-16 index `index` in `text`. */
export function toCodepoint(text: string, index: number): number {
  // A surrogate pair is one code point; token offsets never split one.
  return Array.from(text.slice(0, Math.max(0, index))).length;
}

/** The UTF-16 index of code point `codepoint` in `text` (clamped). */
export function fromCodepoint(text: string, codepoint: number): number {
  let index = 0;
  let count = 0;
  while (index < text.length && count < codepoint) {
    const code = text.charCodeAt(index);
    index += code >= 0xd800 && code <= 0xdbff && index + 1 < text.length ? 2 : 1;
    count += 1;
  }
  return index;
}

// ---- the text a selection copies ----------------------------------------------

/** Clean text for the clipboard and the capture's display quote: whitespace
 *  runs (the extraction's line breaks) become one space and Markdown bold
 *  markers go; inline maths keeps its LaTeX. A formula, a table or code keeps
 *  its own lines. */
export function cleanText(slice: string, blockType: string | null | undefined): string {
  if (isAtomicType(blockType) || VERBATIM_TYPES.has(blockType ?? "")) return slice.trim();
  return slice
    .replace(/\*\*|__/g, "")
    .replace(/\s+/g, " ")
    .trim();
}
