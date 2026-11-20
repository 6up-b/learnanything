// UX-11 on the phone: a web page read now keeps its display equations and its exercises' matrices (the sample
// chapter's 34 displays, where its reading kept 3). The phone Reader draws them with the desktop's renderer and
// the page's own macros: a display of matrices, the exercise's matrices as list items, and a display in the middle
// of a list item's sentence. The blocks are taken, shortened, from what the extraction stores for
// samples/understanding-linear-algebra-symmetric-matrices-and-variance.html (extractor html, version 3).
import { App, answers, describe, expect, fireEvent, installFakeHost, it, render, screen } from "../test/fakeHost";

installFakeHost();

const guide = {
  version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
  sections: [{ id: "u1", label: "Section 7.1 Symmetric matrices and variance", startSpanId: "s1", endSpanId: "s3",
    spanIds: ["s1", "s2", "s3"], question: null, suggestedPassages: [] }]
};
const block = (span: string, markdown: string) => ({
  displayNodeId: `node-${span}`, spanId: span, blockType: "Text", markdown, sanitized: false, katexNodes: [], assets: [],
  health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0
});
const MATRICES =
  "\\begin{equation*}\nP = \\begin{bmatrix}\n\\vvec_1\\amp\\vvec_2\\amp\\ldots\\amp\\vvec_m\n\\end{bmatrix},\n\\hspace{24pt}\n" +
  "D = \\begin{bmatrix}\n\\lambda_1 \\amp 0 \\amp \\ldots \\amp 0 \\\\\n0 \\amp \\lambda_2 \\amp \\ldots \\amp 0 \\\\\n" +
  "\\vdots\\amp\\vdots\\amp\\ddots\\amp\\vdots\\\\\n0 \\amp 0 \\amp \\ldots \\amp \\lambda_m\n\\end{bmatrix},\n\\end{equation*}";
const EXERCISE =
  "- For each of the following matrices, determine whether there is a basis for \\(\\real^2\\) consisting of eigenvectors of that matrix.\n" +
  "- \\(\\begin{bmatrix} 3 \\amp -4 \\\\ 4 \\amp 3 \\end{bmatrix} \\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 1 \\amp 1 \\\\ -1 \\amp 3 \\end{bmatrix} \\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 1 \\amp 0\\\\ -1 \\amp 2 \\end{bmatrix} \\text{.}\\)\n" +
  "- \\(\\begin{bmatrix} 9 \\amp 2 \\\\ 2 \\amp 6 \\end{bmatrix} \\text{.}\\)";
const ACTIVITY =
  "- To simplify our calculations, find the demeaned data points\\begin{equation*} \\dtil_j = \\dvec_j - \\overline{\\dvec} \\end{equation*}and plot them in Figure 7.1.13.";
const section = {
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "3",
  contentHash: "c1", status: "ok", layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null },
  range: { sectionId: "u1", fromSpanId: null, toSpanId: null, blockCount: 3 },
  blocks: [block("s1", MATRICES), block("s2", EXERCISE), block("s3", ACTIVITY)],
  mathMacros: {
    "\\vvec": "{\\mathbf v}", "\\dvec": "{\\mathbf d}", "\\dtil": "\\widetilde{\\mathbf d}", "\\real": "{\\mathbb R}",
    "\\amp": "&"
  }
};

const ERROR = /katex-error|mathcolor="#cc0000"/;

describe("UX-11: the phone Reader draws a web page's display equations and matrices", () => {
  it("the matrices display, the exercise's four matrices and a display inside a task, with the page's macros", async () => {
    Object.assign(answers, {
      get_source_library: { sources: [{ sourceId: "src1", title: "Understanding Linear Algebra", extractionId: "ext1", readerEnabled: true }] },
      "reader.guide_plan": guide,
      "reader.render_view": section,
      "reader.get_progress": { version: 1, extractionId: "ext1", sections: [] },
      "reader.log_activity": { recorded: 1 },
      "reader.dose_offer": { version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null }
    });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Read" }));
    fireEvent.click(await screen.findByRole("button", { name: /Understanding Linear Algebra/ }));
    await screen.findByText(/For each of the following matrices/);
    const html = document.querySelector(".book")?.innerHTML ?? "";
    expect((html.match(/class="katex-display"/g) ?? []).length).toBe(2);
    expect(html).not.toMatch(ERROR);
    expect(html).toContain('<mi mathvariant="bold">v</mi>');
    expect(html).toContain('<mi mathvariant="bold">d</mi>');
    const shown = html.replace(/<annotation encoding="application\/x-tex">[\s\S]*?<\/annotation>/g, "");
    expect(shown).not.toMatch(/\\begin|\\amp/);
    expect(shown).toContain("and plot them in Figure 7.1.13.");
  });
});
