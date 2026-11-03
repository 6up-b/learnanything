// RW5c: the shared corpus through the Reader's real pipeline (MarkdownMath: remark-math and rehype-katex, no options).
// tests/test_rw5c_katex_tree.py pins that the sealed engine's KaTeX gives this same MathML, what the Python reader does
// with each form, and that what it reads means what this MathML means. This lane is what ties those to the page.
// @vitest-environment node
import { readFileSync } from "node:fs";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MarkdownMath } from "../../../render/MarkdownMath";
import { normalizeMathDelimiters } from "../../../render/markdownPipeline";
import { pageMathSegments } from "../../../render/pageMathSegments";
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

type Block = { block: string; segments: string[]; page?: string[] };

const squeezed = (latex: string) => latex.split(/\s+/).join(" ").trim();

/** What the page marks as a displayed equation, against what it marks inline, in element order. */
function renderedDisplays(block: string): boolean[] {
  return [...page(block).matchAll(/<span class="katex-display">|<span class="katex">/g)]
    .reduce<boolean[]>((out, match, index, all) => {
      // A displayed equation is a katex span inside its katex-display.
      if (index > 0 && all[index - 1][0].includes("katex-display")) return out;
      return [...out, match[0].includes("katex-display")];
    }, []);
}

describe("the page's segments are the reader's", () => {
  for (const item of corpus.blocks as Block[]) {
    it(`the page: ${item.block}`, () => expect(renderedSources(item.block)).toEqual(item.page ?? item.segments));
    it(`the reader: ${item.block}`, () => expect(pageMathSegments(item.block).map((found) => squeezed(found.latex))).toEqual(item.segments));
  }

  it("each element is displayed or inline as on the page", () => {
    for (const item of corpus.blocks as Block[]) {
      if (item.page) continue;
      expect(pageMathSegments(item.block).map((found) => found.display), item.block).toEqual(renderedDisplays(item.block));
    }
  });

  it("each segment's place is in the block's own text, in code points", () => {
    for (const item of corpus.blocks as Block[]) {
      const points = Array.from(item.block);
      for (const found of pageMathSegments(item.block)) {
        const place = points.slice(found.start, found.end).join("");
        expect(place.includes(found.latex) || (found.latex.includes("\n") && place.length >= found.latex.length), item.block).toBe(true);
      }
    }
  });
});

describe("whatever the markdown around them, the reader's segments are the page's", () => {
  // A seeded generator of what a block can hold around an equation. Struck-through math and a ```math fence are shown
  // and on purpose not read, so they are not generated here; the corpus pins them.
  const WRAPS: ((math: string, next: () => string) => string)[] = [
    (math) => `$${math}$`,
    (math) => `$$${math}$$`,
    (math) => `$$\n${math}\n$$`,
    (math) => `\\[${math}\\]`,
    (math) => `\\(${math}\\)`,
    (math) => `\`$${math}$\``,
    (math) => `\`\`$${math}$\`\``,
    (math) => `    $${math}$`,
    (math) => `\n\n    $${math}$\n\n`,
    (math) => `[r]: https://example.org "$${math}$"`,
    (math) => `\n\n[r]: https://example.org "$${math}$"\n\n`,
    (math) => `[l](https://example.org "$${math}$")`,
    (math) => `[$${math}$](https://example.org)`,
    (math) => `![$${math}$](a.png)`,
    (math) => `<span title="$${math}$">t</span>`,
    (math) => `<!-- $${math}$ -->`,
    (math) => `<div>$${math}$</div>`,
    (math) => `\n\n<div>\n$${math}$\n</div>\n\n`,
    (math) => `\n\n[^n]: $${math}$\n\n`,
    (math) => `\n\n[^n]: $${math}$\n\nnote[^n] here`,
    (math) => `> $${math}$`,
    (math) => `\n\n> $$\n> ${math}\n> $$\n\n`,
    (math) => `\n- $${math}$\n`,
    (math) => `\n\n| a |\n|---|\n| $${math}$ |\n\n`,
    (math) => `\n# $${math}$\n`,
    (math) => `*$${math}$*`,
    (math) => `\\$${math}\\$`,
    (math) => `$${math}`,
    (math) => `\n\n\`\`\`\n$${math}$\n\`\`\`\n\n`,
    (math) => `\n\n~~~\n$${math}$\n~~~\n\n`,
    (_math, next) => `word ${next()} word`,
    (_math, next) => `${next()}\n\n${next()}`,
    (_math, next) => `${next()}\n${next()}`,
  ];
  const EQUATIONS = ["f(x)=x", "y = 2", "a_1 = b^2", "\\frac{a}{b} = c", "g(x) = x + 1"];

  function generated(seed: number): string[] {
    let state = seed;
    const below = (limit: number) => {
      // Numerical Recipes' LCG: nothing but a repeatable shuffle.
      state = (state * 69069 + 1) >>> 0;
      return state % limit;
    };
    const one = (depth: number): string => {
      const shapes = depth > 2 ? WRAPS.length - 3 : WRAPS.length;
      return WRAPS[below(shapes)](EQUATIONS[below(EQUATIONS.length)], () => one(depth + 1));
    };
    return Array.from({ length: 1500 }, () => one(0));
  }

  it("1500 generated blocks", () => {
    let withMath = 0;
    for (const block of generated(20261102)) {
      const shown = renderedSources(block);
      withMath += shown.length ? 1 : 0;
      expect(pageMathSegments(block).map((found) => squeezed(found.latex)), block).toEqual(shown);
    }
    expect(withMath).toBeGreaterThan(300);
  });
});

describe("the bundle the sidecar runs", () => {
  const file = (name: string) => readFileSync(new URL(`../../../../sketch-engine/markdown/${name}`, import.meta.url), "utf8");

  it("is this source built from these packages, byte for byte", async () => {
    // @ts-expect-error build.mjs is plain node, with no types
    const { outputs } = (await import("../../../../sketch-engine/markdown/build.mjs")) as { outputs: () => Promise<{ bundle: string; licenses: string; lock: string }> };
    const made = await outputs();
    expect(made.bundle === file("page-markdown.js")).toBe(true);
    expect(made.licenses).toBe(file("LICENSES.txt"));
    expect(made.lock).toBe(file("page-markdown.lock.json"));
  });

  it("finds what this source finds", () => {
    const bundled = new Function(`${file("page-markdown.js")}; return pageMarkdown;`)() as { pageMathSegments: typeof pageMathSegments };
    for (const item of corpus.blocks as Block[]) {
      expect(bundled.pageMathSegments(item.block), item.block).toEqual(pageMathSegments(item.block));
    }
  });
});

describe("the normalization is the one the page always had", () => {
  it("rewrites \\[ and \\( outside code only", () => {
    expect(normalizeMathDelimiters("a \\[ x \\] b \\( y \\) `\\(z\\)`")).toBe("a \n$$\nx\n$$\n b $y$ `\\(z\\)`");
    expect(normalizeMathDelimiters("```\n\\[x\\]\n```\n\\[y\\]")).toBe("```\n\\[x\\]\n```\n\n$$\ny\n$$\n");
  });
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
