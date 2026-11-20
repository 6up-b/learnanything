// UX-25 (walks student-2 #65, retainer-2 #38-44, project-1, expert-1): the display equations the web-page
// extraction keeps are bare TeX environments, "\begin{equation*} A = QDQ^{-1} = QDQ^T. \end{equation*}", in no
// $$; remark-math left them as text and the Reader printed the raw commands. The renderer now draws a bare
// display environment KaTeX knows as display math, with the source's macros. Nothing stored changes, and the
// book-math check still finds no equation there, so such a block still gets no "checked" label.
// @vitest-environment node
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MarkdownMath } from "./MarkdownMath";
import { MathMacrosProvider } from "./mathMacros";
import { pageMathSegments } from "./pageMathSegments";

// The sample chapter's own definitions of what its kept equations use (as reader.render_view sends them).
const BOOK: Record<string, string> = {
  "\\uvec": "{\\mathbf u}",
  "\\dtil": "\\widetilde{\\mathbf d}"
};

// The three environments the extraction keeps of the sample chapter
// (samples/understanding-linear-algebra-symmetric-matrices-and-variance.html), each a block of its own.
const KEPT = [
  "\\begin{equation*}\nA = QDQ^{-1} = QDQ^T.\n\\end{equation*}",
  "\\begin{equation*}\nV = \\frac 1N\\sum_j~|\\dtil_j|^2.\n\\end{equation*}",
  "\\begin{equation*}\nV = V_{\\uvec_1} + V_{\\uvec_2}.\n\\end{equation*}"
];

const ERROR = /katex-error|mathcolor="#cc0000"/;

function page(value: string, macros: Record<string, string> | null = BOOK): string {
  return renderToStaticMarkup(createElement(MathMacrosProvider, { macros, children: createElement(MarkdownMath, { value }) }));
}

/** The page's text with KaTeX's own copy of each formula's source (its <annotation>) taken out. */
function shown(html: string): string {
  return html.replace(/<annotation encoding="application\/x-tex">[\s\S]*?<\/annotation>/g, "");
}

function displays(html: string): number {
  return (html.match(/class="katex-display"/g) ?? []).length;
}

describe("UX-25: a kept display environment is drawn as display math", () => {
  it.each(KEPT)("%s", (block) => {
    const html = page(block);
    expect(displays(html)).toBe(1);
    expect(html).not.toMatch(ERROR);
    expect(shown(html)).not.toContain("\\begin");
    expect(shown(html)).not.toContain("\\end");
  });

  it("with the source's macros: \\dtil and \\uvec are the book's symbols, not red commands", () => {
    expect(page(KEPT[1])).toContain('<mi mathvariant="bold">d</mi>');
    expect(page(KEPT[2])).toContain('<mi mathvariant="bold">u</mi>');
    expect(page(KEPT[2], null)).toMatch(ERROR);
  });

  it("in a paragraph, between words, it is drawn on its own line and the words stay", () => {
    const html = page("We then have \\begin{equation*} A = QDQ^{-1} = QDQ^T. \\end{equation*} In this case, A is orthogonally diagonalizable.");
    expect(displays(html)).toBe(1);
    expect(shown(html)).toContain("We then have");
    expect(shown(html)).toContain("In this case, A is orthogonally diagonalizable.");
    expect(shown(html)).not.toContain("\\begin");
  });

  it("align, gather and the numbered forms too; two in a block are two displays", () => {
    for (const [env, body] of [
      ["equation", "x = 1"], ["align", "x &= 1 \\\\ y &= 2"], ["align*", "x &= 1 \\\\ y &= 2"],
      ["gather", "x = 1 \\\\ y = 2"], ["gather*", "x = 1 \\\\ y = 2"], ["alignat*", "{2} x &= 1 & y &= 2"]
    ]) {
      const html = page(`\\begin{${env}}\n${body}\n\\end{${env}}`);
      expect(displays(html), env).toBe(1);
      expect(html, env).not.toMatch(ERROR);
    }
    expect(displays(page(`${KEPT[0]}\n\nThen\n\n${KEPT[2]}`))).toBe(2);
  });

  it("an environment already inside math, or in code, is left as it was", () => {
    // Already display math: one display each, never a second $$ around it.
    for (const value of ["$$\n\\begin{aligned} x &= 1 \\end{aligned}\n$$", "$$\n\\begin{equation*} x = 1 \\end{equation*}\n$$", "\\[\\begin{align*} x &= 1 \\end{align*}\\]"]) {
      const html = page(value);
      expect(displays(html), value).toBe(1);
      expect(html, value).not.toMatch(ERROR);
      expect(shown(html), value).not.toContain("$$");
    }
    // A matrix inside inline math stays inline.
    const inline = page("Here \\(A = \\begin{bmatrix} 1 \\amp 2 \\end{bmatrix}\\).");
    expect(displays(inline)).toBe(0);
    expect((inline.match(/class="katex"/g) ?? []).length).toBe(1);
    // Code shows the source as written.
    expect(shown(page("Type `\\begin{equation*} x \\end{equation*}` for it."))).toContain("<code>\\begin{equation*} x \\end{equation*}</code>");
    const fenced = page("```\n\\begin{equation*}\nx\n\\end{equation*}\n```");
    expect(displays(fenced)).toBe(0);
    expect(fenced).toContain("<pre><code>\\begin{equation*}\nx\n\\end{equation*}\n</code></pre>");
  });

  it("an environment KaTeX cannot draw, or one never closed, stays text rather than an error", () => {
    for (const value of ["\\begin{multline*} a \\\\ b \\end{multline*}", "\\begin{equation*} A = QDQ^T and the rest"]) {
      const html = page(value);
      expect(displays(html), value).toBe(0);
      expect(html, value).not.toMatch(ERROR);
    }
  });

  it("the book-math check still finds no equation in a bare environment, so it is never labelled checked", () => {
    for (const block of KEPT) expect(pageMathSegments(block)).toEqual([]);
  });
});
