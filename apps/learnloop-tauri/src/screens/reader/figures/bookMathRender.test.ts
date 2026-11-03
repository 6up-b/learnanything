// RW5c: the shared corpus through the Reader's real pipeline (MarkdownMath: remark-math and rehype-katex, no options).
// tests/test_rw5c_katex_tree.py pins that the sealed engine's KaTeX gives this same MathML, what the Python reader does
// with each form, and that what it reads means what this MathML means. This lane is what ties those to the page.
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MarkdownMath } from "../../../render/MarkdownMath";
import corpus from "./bookMathRenderCorpus.json";

function page(block: string): string {
  return renderToStaticMarkup(createElement(MarkdownMath, { value: block }));
}

// KaTeX's two ways of showing what it cannot read: an error span, or the raw command in its error colour.
const ERROR = /katex-error|mathcolor="#cc0000"/;

function unescaped(text: string): string {
  return text.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&");
}

/** The MathML the page holds for its one math element, as KaTeX's <semantics> wraps it. */
function mathml(block: string): string {
  const found = page(block).match(/<semantics>(?:<mrow>)?([\s\S]*?)(?:<\/mrow>)?<annotation/);
  expect(found, block).not.toBeNull();
  return found![1];
}

/** The source of each math element the page rendered, in reading order. */
function renderedSources(block: string): string[] {
  return [...page(block).matchAll(/<annotation encoding="application\/x-tex">([\s\S]*?)<\/annotation>/g)].map((match) => unescaped(match[1]).split(/\s+/).join(" ").trim());
}

describe("the source's rendered structure", () => {
  for (const item of [...corpus.refused, ...corpus.read]) {
    it(item.rhs, () => expect(mathml(`$${item.rhs}$`)).toBe(item.mathml));
  }
  for (const item of corpus.whole) {
    it(item.latex, () => expect(mathml(`$${item.latex}$`)).toBe(item.mathml));
  }
});

describe("what the page cannot render shows an error, so it is never read", () => {
  for (const item of corpus.not_rendered) {
    it(item.rhs, () => expect(page(`$${item.rhs}$`)).toMatch(ERROR));
  }
  it("Astra's double superscript", () => expect(page("$f(x)=e^x^2$")).toMatch(ERROR));
});

describe("the page's segments are the reader's", () => {
  for (const item of corpus.blocks as { block: string; segments: string[]; page?: string[] }[]) {
    it(item.block, () => expect(renderedSources(item.block)).toEqual(item.page ?? item.segments));
  }
});

describe("a definition reaches nothing else on the page", () => {
  it("the page shows what the definition makes of its own segment", () => {
    expect(mathml("$\\def\\sin{\\cos}f(x)=\\sin(x)$")).toContain("<mi>cos</mi>");
  });
  it("not the next segment of its block", () => {
    const html = page("$\\gdef\\foo{1}\\foo$ and $\\foo$");
    expect(html).toMatch(ERROR);
    expect(mathml("$\\gdef\\foo{1}\\foo$")).toBe("<mn>1</mn>");
  });
  it("not another block", () => {
    expect(page("$\\gdef\\foo{1}\\foo$")).not.toMatch(ERROR);
    expect(page("$\\foo$")).toMatch(ERROR);
  });
});
