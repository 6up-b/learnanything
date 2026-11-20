// UX-25 on the phone (the walks saw it on the desktop; the phone draws the same blocks with the desktop's renderer):
// a display equation the web-page extraction keeps as a bare "\begin{equation*} … \end{equation*}" is drawn as
// display math, with the source's own macros, never as raw commands.
import { App, answers, describe, expect, fireEvent, installFakeHost, it, render, screen } from "../test/fakeHost";

installFakeHost();

const guide = {
  version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
  sections: [{ id: "u1", label: "Symmetric matrices", startSpanId: "b0", endSpanId: "b2", spanIds: ["b0", "b1", "b2"], question: null, suggestedPassages: [] }]
};
const block = (span: string, markdown: string) => ({
  displayNodeId: `node-${span}`, spanId: span, blockType: "Text", markdown, sanitized: false, katexNodes: [], assets: [],
  health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0
});
// Two of the sample chapter's kept environments, as their blocks hold them, and the macro one of them uses.
const section = {
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c1", status: "ok", layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null },
  range: { sectionId: "u1", fromSpanId: null, toSpanId: null, blockCount: 3 },
  blocks: [
    block("b0", "We then have"),
    block("b1", "\\begin{equation*}\nA = QDQ^{-1} = QDQ^T.\n\\end{equation*}"),
    block("b2", "\\begin{equation*}\nV = V_{\\uvec_1} + V_{\\uvec_2}.\n\\end{equation*}")
  ],
  mathMacros: { "\\uvec": "{\\mathbf u}" }
};

const ERROR = /katex-error|mathcolor="#cc0000"/;

describe("UX-25: the phone Reader draws a kept display environment as display math", () => {
  it("both kept equations are displays, with the book's \\uvec, and no raw \\begin is shown", async () => {
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
    await screen.findByText("We then have");
    const html = document.querySelector(".book")?.innerHTML ?? "";
    expect((html.match(/class="katex-display"/g) ?? []).length).toBe(2);
    expect(html).not.toMatch(ERROR);
    expect(html).toContain('<mi mathvariant="bold">u</mi>');
    expect(html.replace(/<annotation encoding="application\/x-tex">[\s\S]*?<\/annotation>/g, "")).not.toContain("\\begin");
  });
});
