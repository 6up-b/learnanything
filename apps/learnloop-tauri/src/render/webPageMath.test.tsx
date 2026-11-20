// UX-11: a web page read now keeps its display equations (the sample chapter's 34, where its reading kept 3), as
// the page writes them: bare environments, as blocks of their own or in the middle of an exercise's list item, and
// its exercises' matrices. These are blocks as the extraction stores them for
// samples/understanding-linear-algebra-symmetric-matrices-and-variance.html (extractor html, version 3), drawn
// with the page's own macros (reader.render_view's mathMacros). A MathML formula the extraction turns into TeX
// reaches the renderer as \[ … \] or \( … \).
// @vitest-environment node
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MarkdownMath } from "./MarkdownMath";
import { MathMacrosProvider } from "./mathMacros";

// The chapter's own definitions of what these blocks use, as the page defines them.
const BOOK: Record<string, string> = {
  "\\vvec": "{\\mathbf v}",
  "\\dvec": "{\\mathbf d}",
  "\\dtil": "\\widetilde{\\mathbf d}",
  "\\real": "{\\mathbb R}",
  "\\amp": "&",
  "\\twovec": "\\left[\\begin{array}{r}#1 \\\\ #2\n\\end{array}\\right]"
};

// Display 2 of 34: the preview's P and D, a block of its own.
const MATRICES =
  "\\begin{equation*}\nP = \\begin{bmatrix}\n\\vvec_1\\amp\\vvec_2\\amp\\ldots\\amp\\vvec_m\n\\end{bmatrix},\n\\hspace{24pt}\n" +
  "D = \\begin{bmatrix}\n\\lambda_1 \\amp 0 \\amp \\ldots \\amp 0 \\\\\n0 \\amp \\lambda_2 \\amp \\ldots \\amp 0 \\\\\n" +
  "\\vdots\\amp\\vdots\\amp\\ddots\\amp\\vdots\\\\\n0 \\amp 0 \\amp \\ldots \\amp \\lambda_m\n\\end{bmatrix},\n\\end{equation*}";
// Activity 7.1.2's exercise: "For each of the following matrices", then the matrices, each a list item.
const EXERCISE =
  "provides a diagonal matrix \\(D\\) constructed from the eigenvalues of \\(A\\) with the columns of \\(P\\) containing the associated eigenvectors.\n" +
  "- For each of the following matrices, determine whether there is a basis for \\(\\real^2\\) consisting of eigenvectors of that matrix. When there is such a basis, form the matrices \\(P\\) and \\(D\\) and verify that the matrix equals \\(PDP^{-1}\\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 3 \\amp -4 \\\\ 4 \\amp 3 \\end{bmatrix} \\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 1 \\amp 1 \\\\ -1 \\amp 3 \\end{bmatrix} \\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 1 \\amp 0\\\\ -1 \\amp 2 \\end{bmatrix} \\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 9 \\amp 2 \\\\ 2 \\amp 6 \\end{bmatrix} \\text{.}\\)";
// Activity 7.1.4's tasks (four of its eight list items): two displays (16 and 17 of 34) in the middle of list
// items' sentences.
const ACTIVITY =
  "- Find the centroid, or mean, \\(\\overline{\\dvec} = \\frac1N\\sum_j \\dvec_j\\text{.}\\) Then plot the data points and their centroid in Figure 7.1.12.\n" +
  "- Notice that the centroid lies in the center of the data so the spread of the data will be measured by how far away the points are from the centroid. To simplify our calculations, find the demeaned data points\\begin{equation*} \\dtil_j = \\dvec_j - \\overline{\\dvec} \\end{equation*}and plot them in Figure 7.1.13.\n" +
  "- Now that the data has been demeaned, we will define the total variance as the average of the squares of the distances from the origin; that is, the total variance is\\begin{equation*} V = \\frac 1N\\sum_j~|\\dtil_j|^2. \\end{equation*}Find the total variance \\(V\\) for our set of three points.\n" +
  "- Plot the projections of the demeaned data points onto the lines defined by vectors \\(\\vvec_1=\\twovec11\\) and \\(\\vvec_2=\\twovec{-1}1\\) using Figure 7.1.15.";
// Exercise 6's data matrix (display 32 of 34).
const DATA = "\\begin{equation*}\n\\begin{bmatrix}\n2 \\amp 0 \\amp 4 \\amp 4 \\amp 5 \\amp 3 \\\\\n1 \\amp 0 \\amp 3 \\amp 5 \\amp 4 \\amp 5\n\\end{bmatrix}.\n\\end{equation*}";

const ERROR = /katex-error|mathcolor="#cc0000"/;

function page(value: string, macros: Record<string, string> | null = BOOK): string {
  return renderToStaticMarkup(createElement(MathMacrosProvider, { macros, children: createElement(MarkdownMath, { value }) }));
}

function shown(html: string): string {
  return html.replace(/<annotation encoding="application\/x-tex">[\s\S]*?<\/annotation>/g, "");
}

function count(html: string, pattern: RegExp): number {
  return (html.match(pattern) ?? []).length;
}

describe("UX-11: a web page's display equations and matrices are drawn, with the page's macros", () => {
  it("a display of matrices is one display, its \\amp columns and \\vvec drawn", () => {
    const html = page(MATRICES);
    expect(count(html, /class="katex-display"/g)).toBe(1);
    expect(html).not.toMatch(ERROR);
    expect(html).toContain('<mi mathvariant="bold">v</mi>');
    expect(count(html, /<mtable/g)).toBeGreaterThanOrEqual(2);
    expect(shown(html)).not.toMatch(/\\begin|\\amp/);
  });

  it("the exercise's four matrices are drawn after its sentence, each a list item", () => {
    const html = page(EXERCISE);
    expect(html).not.toMatch(ERROR);
    expect(shown(html)).toContain("For each of the following matrices");
    expect(count(html, /<li>/g)).toBe(5);
    expect(count(html, /<mtable/g)).toBe(4);
    expect(shown(html)).not.toMatch(/\\begin|\\amp/);
  });

  it("a display in the middle of a list item's sentence is drawn as display math, the words around it kept", () => {
    const html = page(ACTIVITY);
    expect(count(html, /class="katex-display"/g)).toBe(2);
    expect(html).not.toMatch(ERROR);
    expect(html).toContain('<mi mathvariant="bold">d</mi>');
    expect(shown(html)).toContain("find the demeaned data points");
    expect(shown(html)).toContain("and plot them in Figure 7.1.13.");
    expect(shown(html)).toContain("Find the total variance");
    expect(shown(html)).not.toContain("\\begin");
  });

  it("the data matrix an exercise asks about is drawn", () => {
    const html = page(DATA);
    expect(count(html, /class="katex-display"/g)).toBe(1);
    expect(count(html, /<mn>5<\/mn>/g)).toBe(3);
    expect(html).not.toMatch(ERROR);
  });

  it("without the page's macros, its \\amp and \\vvec are the errors the macros prevent", () => {
    expect(page(MATRICES, null)).toMatch(ERROR);
  });

  it("a MathML formula turned into TeX: \\[ … \\] is a display, \\( … \\) inline, in a sentence", () => {
    const html = page("The mean is \\[\\bar x = \\frac{1}{n}\\sum_{i=1}^n x_i\\] for a sample \\(x_1, \\ldots, x_n\\).");
    expect(count(html, /class="katex-display"/g)).toBe(1);
    expect(count(html, /class="katex"/g)).toBe(2);
    expect(html).not.toMatch(ERROR);
    expect(shown(html)).toContain("for a sample");
  });
});
