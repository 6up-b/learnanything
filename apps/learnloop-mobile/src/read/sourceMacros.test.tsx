// UX-2 (UX journey audit, walk phone-2 #37): the phone Reader drew the sample chapter's \vvec as a red raw command
// and its \real as KaTeX's ℜ. The section reply now carries the source's own macros (reader.render_view's mathMacros),
// and the phone renders the book's formulas with them.
import { App, beforeEach, answers, describe, expect, fireEvent, installFakeHost, it, render, screen } from "../test/fakeHost";

installFakeHost();

const guide = {
  version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
  sections: [{ id: "u1", label: "7.1 Symmetric matrices", startSpanId: "b0", endSpanId: "b1", spanIds: ["b0", "b1"], question: null, suggestedPassages: [] }]
};
const block = (span: string, markdown: string) => ({
  displayNodeId: `node-${span}`, spanId: span, blockType: "Text", markdown, sanitized: false, katexNodes: [], assets: [],
  health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0
});
const section = (mathMacros?: Record<string, string>) => ({
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c1", status: "ok", layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null },
  range: { sectionId: "u1", fromSpanId: null, toSpanId: null, blockCount: 2 },
  blocks: [block("b0", "# 7.1 Symmetric matrices"), block("b1", "If \\(\\vvec\\) is in \\(\\real^n\\), then so is its scaling.")],
  ...(mathMacros ? { mathMacros } : {})
});

// KaTeX's two ways of showing what it cannot read: an error span, or the raw command in its error colour.
const ERROR = /katex-error|mathcolor="#cc0000"/;

function serve(reply: unknown) {
  Object.assign(answers, {
    get_source_library: { sources: [{ sourceId: "src1", title: "Understanding Linear Algebra", extractionId: "ext1", readerEnabled: true }] },
    "reader.guide_plan": guide,
    "reader.render_view": reply,
    "reader.get_progress": { version: 1, extractionId: "ext1", sections: [] },
    "reader.log_activity": { recorded: 1 },
    "reader.dose_offer": { version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null }
  });
}

async function openBook(): Promise<string> {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Read" }));
  fireEvent.click(await screen.findByRole("button", { name: /Understanding Linear Algebra/ }));
  await screen.findByText(/then so is its scaling/);
  return document.querySelector(".book")?.innerHTML ?? "";
}

beforeEach(() => serve(section({ "\\vvec": "{\\mathbf v}", "\\real": "{\\mathbb R}" })));

describe("UX-2: the phone Reader renders a source's own macros", () => {
  it("\\vvec is a bold v and \\real the book's ℝ, with no error node", async () => {
    const html = await openBook();
    expect(html).not.toMatch(ERROR);
    expect(html).toContain('<mi mathvariant="bold">v</mi>');
    expect(html).toContain('<mi mathvariant="double-struck">R</mi>');
    expect(html).not.toContain("ℜ");
  });

  it("a reply from an older desktop, with no macros, renders as before", async () => {
    serve(section());
    const html = await openBook();
    expect(html).toMatch(ERROR);
  });
});
