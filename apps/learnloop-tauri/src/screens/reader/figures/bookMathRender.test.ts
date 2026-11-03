// RW5c Codex review F1: how TeX groups a book's equation, pinned against the corpus the Python reader
// is tested on (tests/test_rw5c_book_math.py), so the two lanes compare the page's meaning with code's.
import katex from "katex";
import { describe, expect, it } from "vitest";
import corpus from "./bookMathRenderCorpus.json";

function mathml(tex: string): string {
  const html = katex.renderToString(tex, { output: "mathml", throwOnError: true, strict: "ignore" });
  const found = html.match(/<semantics>(?:<mrow>)?([\s\S]*?)(?:<\/mrow>)?<annotation/);
  return found ? found[1] : html;
}

describe("the source's rendered structure", () => {
  for (const item of [...corpus.refused, ...corpus.read]) {
    it(item.rhs, () => expect(mathml(item.rhs)).toBe(item.mathml));
  }
});
