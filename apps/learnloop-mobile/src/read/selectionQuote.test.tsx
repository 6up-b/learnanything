// UX-26 on the phone: the phone Reader draws its passages with the desktop's renderer, and its selection sheet took
// the selection's text, every KaTeX layer of each formula included. The sheet now shows, and Ask sends, each formula
// once as its TeX; Save (a highlight) anchors with the words as selected, as it always did.
import { App, answers, called, describe, expect, fireEvent, installFakeHost, it, render, screen, waitFor } from "../test/fakeHost";

installFakeHost();

const guide = {
  version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
  sections: [{ id: "u1", label: "Symmetric matrices", startSpanId: "b1", endSpanId: "b1", spanIds: ["b1"], question: null, suggestedPassages: [] }]
};
const PASSAGE = "orthonormal vectors into a matrix \\(Q\\) produces an orthogonal matrix, which means that \\(Q^T = Q^{-1}\\text{.}\\) We then have";
const section = {
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c1", status: "ok", layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null },
  range: { sectionId: "u1", fromSpanId: null, toSpanId: null, blockCount: 1 },
  blocks: [{ displayNodeId: "node-b1", spanId: "b1", blockType: "Text", markdown: PASSAGE, sanitized: false, katexNodes: [], assets: [],
    health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0 }]
};
const CLEAN = "orthonormal vectors into a matrix $Q$ produces an orthogonal matrix, which means that $Q^T = Q^{-1}\\text{.}$ We then have";

describe("UX-26: the phone's selection quote takes each formula once, as its TeX", () => {
  it("the sheet shows it, Ask sends it, and Save anchors with the words as selected", async () => {
    Object.assign(answers, {
      get_source_library: { sources: [{ sourceId: "src1", title: "Understanding Linear Algebra", extractionId: "ext1", readerEnabled: true }] },
      "reader.guide_plan": guide,
      "reader.render_view": section,
      "reader.get_progress": { version: 1, extractionId: "ext1", sections: [] },
      "reader.log_activity": { recorded: 1 },
      "reader.dose_offer": { version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null },
      "reader.ask": { eventId: "e1", readerAnswerEventId: "ra1", answerMd: "Because Q is orthogonal.", answerMode: "explain",
        citations: [], manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: 4 },
      "reader.capture": { annotationId: "an1", anchorStatus: "exact" }
    });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Read" }));
    fireEvent.click(await screen.findByRole("button", { name: /Understanding Linear Algebra/ }));
    await screen.findByText(/We then have/);
    const book = document.querySelector<HTMLElement>(".book")!;
    const range = document.createRange();
    // The passage's paragraph (its block also holds a "View the page" button).
    range.selectNodeContents(book.querySelector("[data-span] p")!);
    window.getSelection()!.removeAllRanges();
    window.getSelection()!.addRange(range);
    const asSelected = window.getSelection()!.toString().trim();
    expect(asSelected).toContain("QQQ");
    fireEvent.mouseUp(book);

    const quote = await screen.findByText((_, element) => element?.tagName === "BLOCKQUOTE");
    expect(quote.textContent).toBe(`§ ${CLEAN}`);
    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "Why?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("Because Q is orthogonal.");
    expect(called("reader.ask")[0].params.selectionQuote).toBe(CLEAN);

    fireEvent.click(screen.getByRole("button", { name: /^Save/ }));
    await waitFor(() => expect(called("reader.capture")).toHaveLength(1));
    expect(called("reader.capture")[0].params.rawSelection).toEqual({ nodes: [{ spanId: "b1", quote: asSelected }] });
  });
});
