// What MarkdownMath does to a block before KaTeX sees it, in one place, because two readers must agree on it: the page
// (MarkdownMath.tsx) and the check behind "matches the book's equation (checked)" (pageMathSegments.ts, which runs in
// the sidecar's sealed engine, bundled into sketch-engine/markdown/page-markdown.js).
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

// remark-math only recognizes $…$ / $$…$$, but model-generated prose (tutor
// answers, open questions) routinely uses \(…\) / \[…\] — which plain markdown
// then mangles by swallowing the backslashes. Rewrite those delimiters to the
// dollar forms before parsing, leaving code fences and inline code untouched.
const CODE_SEGMENT = /(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|`[^`\n]*`)/g;
const WRITTEN = -1;

/** Normalized text, and for each of its UTF-16 units the unit of the input it came from (or -1, written here). */
export type NormalizedText = { text: string; places: number[] };

function rewrite(input: NormalizedText, pattern: RegExp, open: string, close: string): NormalizedText {
  const out: NormalizedText = { text: "", places: [] };
  const copy = (from: number, to: number) => {
    out.text += input.text.slice(from, to);
    for (let at = from; at < to; at++) out.places.push(input.places[at]);
  };
  const write = (text: string) => {
    out.text += text;
    for (let at = 0; at < text.length; at++) out.places.push(WRITTEN);
  };
  let last = 0;
  for (const match of input.text.matchAll(pattern)) {
    const at = match.index;
    const body = match[1];
    const begin = at + 2 + (body.length - body.trimStart().length);
    copy(last, at);
    write(open);
    copy(begin, begin + body.trim().length);
    write(close);
    last = at + match[0].length;
  }
  copy(last, input.text.length);
  return out;
}

function rewriteDelimiters(text: string, offset: number): NormalizedText {
  const start: NormalizedText = { text, places: [] };
  for (let at = 0; at < text.length; at++) start.places.push(offset + at);
  const display = rewrite(start, /\\\[([\s\S]+?)\\\]/g, "\n$$\n", "\n$$\n");
  return rewrite(display, /\\\(([\s\S]+?)\\\)/g, "$", "$");
}

export function normalizeWithPlaces(value: string): NormalizedText {
  const out: NormalizedText = { text: "", places: [] };
  let offset = 0;
  value.split(CODE_SEGMENT).forEach((segment, index) => {
    if (index % 2 === 1) {
      out.text += segment;
      for (let at = 0; at < segment.length; at++) out.places.push(offset + at);
    } else {
      const done = rewriteDelimiters(segment, offset);
      out.text += done.text;
      for (const place of done.places) out.places.push(place);
    }
    offset += segment.length;
  });
  return out;
}

export function normalizeMathDelimiters(value: string): string {
  return normalizeWithPlaces(value).text;
}

// Module-level plugin list: a fresh array per render defeats react-markdown's own memoisation.
export const REMARK_PLUGINS = [remarkGfm, remarkMath];
