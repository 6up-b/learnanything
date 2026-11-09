// §3.5: the selection sheet's Ask is the desktop's `reader.ask` on the selected spans, as a job; a selection on
// what the reading holds out offers no Ask; the host's refusals are one plain line. Save is a highlight.
import { answers, called, describe, expect, fireEvent, installFakeHost, it, render, screen, waitFor } from "../test/fakeHost";
import { SelectionSheet } from "./SelectionSheet";

installFakeHost();

const section = {
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c", status: "ok", blocks: [], layers: {},
  protection: { withheld: false, heldOutSpanIds: ["b6"], message: "This passage is held out for evaluation." }
};

function open(spanIds: string[], askOff = false) {
  render(
    <SelectionSheet selection={{ spanIds, quote: "Every vector space has a zero vector." }} section={section} askOff={askOff}
      protectionMessage={section.protection.message} onClose={() => undefined} onError={() => undefined} />
  );
}

describe("the selection sheet (§3.5)", () => {
  it("asks about the selected passages, by their spans, and answers in the three voices", async () => {
    answers["reader.ask"] = { eventId: "e1", readerAnswerEventId: "ra1", answerMd: "Because the axioms say so.", answerMode: "explain",
      citations: [], manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: 4 };
    open(["b1", "b2"]);
    expect(screen.getByText("Every vector space has a zero vector.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "Why is there one?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("Because the axioms say so.")).toBeTruthy();
    const [ask] = called("reader.ask");
    expect(ask.params).toEqual({ extractionId: "ext1", spanId: "b1", selectionSpanIds: ["b1", "b2"],
      selectionQuote: "Every vector space has a zero vector.", question: "Why is there one?", retrievalIntent: "explain" });
    expect(ask.requestId).toBeTruthy();
    // A follow-up names the exchange it follows.
    fireEvent.click(screen.getByRole("button", { name: "Another way" }));
    await waitFor(() => expect(called("reader.ask")).toHaveLength(2));
    expect(called("reader.ask")[1].params).toMatchObject({ retrievalIntent: "alternative", parentExchangeId: "ra1" });
  });

  it("offers no Ask on a protected selection, and says why in the desktop's words", () => {
    open(["b5", "b6"], true);
    expect(screen.queryByRole("button", { name: "Ask" })).toBeNull();
    expect(screen.getByText("This passage is held out for evaluation.")).toBeTruthy();
  });

  it("a check on your own refuses the Ask on the host, and the sheet says so in one line", async () => {
    answers["reader.ask"] = { status: 409, body: { ok: false, error: { code: "cold_check_open", message: "Ask is off while a check on your own is open. Finish it first, and Ask is back.", retryable: false } } };
    open(["b1"]);
    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "Hint?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(/Ask is off while a check on your own is open/)).toBeTruthy();
  });

  it("Save is a highlight of the selection, with its own key", async () => {
    answers["reader.capture"] = { annotationId: "a1", receipt: "acknowledged" };
    open(["b1"]);
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByRole("button", { name: "Saved" })).toBeTruthy();
    expect(called("reader.capture")[0].params).toMatchObject({ action: "highlight", extractionId: "ext1", sourceId: "src1", revisionId: "rev1" });
  });
});
