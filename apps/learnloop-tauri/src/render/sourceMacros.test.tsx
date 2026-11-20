// UX-2 (UX journey audit, walks student-1, beginner-1, retainer-1, phone-2): a source's own TeX macros. The sample
// chapter writes \vvec, \real, \twovec and \amp in every formula and defines them once, in a part of the page the
// extraction drops; the Reader showed them as red raw commands, \real as KaTeX's own ℜ, and one-line snippets
// showed raw "\(\uvec\)". The sidecar now sends the source's macros beside its reading.
// @vitest-environment node
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { QuestionQueueRowDto } from "../api/dto";
import { questionThread } from "../app/todayPlan";
import { MarkdownMath } from "./MarkdownMath";
import { MathMacrosProvider } from "./mathMacros";
import { clipMath, plainMathLine } from "./mathSnippet";

// As reader.render_view sends them for the sample (tests/test_ux2_source_macros.py reads the same page).
const BOOK: Record<string, string> = {
  "\\vvec": "{\\mathbf v}",
  "\\uvec": "{\\mathbf u}",
  "\\real": "{\\mathbb R}",
  "\\twovec": "\\left[\\begin{array}{r}#1 \\\\ #2\n\\end{array}\\right]",
  "\\amp": "&"
};

// KaTeX's two ways of showing what it cannot read: an error span, or the raw command in its error colour.
const ERROR = /katex-error|mathcolor="#cc0000"/;

function page(value: string, macros?: Record<string, string> | null): string {
  const markdown = createElement(MarkdownMath, { value });
  return renderToStaticMarkup(macros === undefined ? markdown : createElement(MathMacrosProvider, { macros, children: markdown }));
}

const PASSAGE =
  "Suppose that \\(\\uvec\\) is an eigenvector of \\(B\\) with associated eigenvalue \\(\\lambda\\) and that \\(\\uvec\\) has unit length. " +
  "Explain why \\(\\lambda = \\uvec\\cdot(B\\uvec)\\text{.}\\)";

describe("UX-2: the Reader's renderer draws a source's own macros", () => {
  it("\\vvec is a bold v and \\real is the book's ℝ, with no error node", () => {
    const text = "Let \\(\\vvec \\in \\real^n\\) and \\(\\xvec = \\twovec{1}{2}\\).";
    const html = page(text, { ...BOOK, "\\xvec": "{\\mathbf x}" });
    expect(html).not.toMatch(ERROR);
    expect(html).toContain('<mi mathvariant="bold">v</mi>');
    expect(html).toContain('<mi mathvariant="double-struck">R</mi>');
    expect(html).not.toContain("ℜ");
    // What the walks saw without them: red raw commands, and \real as KaTeX's ℜ.
    const before = page("Let \\(\\vvec \\in \\real^n\\).");
    expect(before).toMatch(ERROR);
    expect(before).toContain("ℜ");
  });

  it("a matrix written with the book's \\amp renders", () => {
    expect(page("\\(\\left[\\begin{array}{rr}1 \\amp 2 \\\\ 3 \\amp 4\\end{array}\\right]\\)", BOOK)).not.toMatch(ERROR);
  });

  it("no macros, or none from the source, renders exactly as before", () => {
    const text = "Addition commutes: $u + v = v + u$.";
    expect(page(text, {})).toBe(page(text));
    expect(page(text, null)).toBe(page(text));
  });

  it("a recursive macro is one formula's error under KaTeX's own expansion limit; the rest of the page renders", () => {
    const html = page("$\\loop$ then $x^2$", { "\\loop": "\\loop\\loop" });
    expect(html.match(/katex-error/g)).toHaveLength(1);
    expect(html).toContain("<msup>");
  });

  it("a table that expands past KaTeX's limit fails in the formula, not the page", () => {
    // Twelve doublings: 4096 tokens from one command.
    const table: Record<string, string> = {};
    for (let level = 0; level < 12; level++) table[`\\m${"abcdefghijkl"[level]}`] = `\\m${"abcdefghijklm"[level + 1]}\\m${"abcdefghijklm"[level + 1]}`;
    table["\\mm"] = "x";
    const html = page("$\\ma$ and $y$", table);
    expect(html.match(/katex-error/g)).toHaveLength(1);
    expect(html).toContain("<mi>y</mi>");
  });

  it("a definition inside one formula never reaches another render, and the source's table is never written", () => {
    const table = { ...BOOK };
    page("$\\gdef\\leak{y}\\leak$", table);
    expect(Object.keys(table)).toEqual(Object.keys(BOOK));
    expect(page("$\\leak$", table)).toMatch(ERROR);
  });
});

describe("UX-2: snippets render their math or show clean text", () => {
  it("a clipped passage in the Ask chip never cuts a formula, and renders with the book's macros", () => {
    for (const limit of [40, 60, 100, 150]) {
      const clipped = clipMath(PASSAGE, limit);
      expect((clipped.match(/\\\(/g) ?? []).length).toBe((clipped.match(/\\\)/g) ?? []).length);
      expect(clipped.endsWith("…")).toBe(true);
      expect(page(clipped, BOOK)).not.toMatch(ERROR);
    }
    expect(clipMath(PASSAGE, PASSAGE.length)).toBe(PASSAGE);
  });

  it("a one-line snippet never shows a backslash command", () => {
    const line = plainMathLine(PASSAGE);
    expect(line).not.toMatch(/\\[A-Za-z(){}[\]]/);
    expect(line).toContain("is an eigenvector of B with associated eigenvalue λ");
    // The line cannot render the book's \uvec: it says its name, never the command.
    expect(line).toContain("Explain why λ = uvec·(Buvec).");
    // A label the sidecar cut inside a formula (its 60 characters) still shows no TeX.
    expect(plainMathLine("Explain why \\(\\lambda = \\…")).toBe("Explain why λ = …");
    expect(plainMathLine("If \\(\\vvec\\in\\real^n\\), then \\(\\frac{1}{N}\\sum_j x_j\\)")).toBe("If vvec∈real^n, then 1/N ∑_j x_j");
    expect(plainMathLine("Plain words stay as they are.")).toBe("Plain words stay as they are.");
  });

  it("Today's thread line shows a question's passage without raw TeX", () => {
    const row = {
      id: "q1",
      questionMd: "Why does \\(\\uvec\\cdot(C\\uvec)\\) give the variance?",
      resolution: "open",
      createdAt: "2026-11-17T10:00:00Z",
      sourceCitation: { extractionId: "ext1", spanId: "s5", label: "Suppose that \\(\\uvec\\) is an eigenvector of \\(B\\) with asso…", sourceId: "src1" }
    } as unknown as QuestionQueueRowDto;
    const thread = questionThread(row);
    expect(thread.kind === "question" && thread.place).toBe("Suppose that uvec is an eigenvector of B with asso…");
    expect(thread.text).not.toMatch(/\\/);
  });
});
