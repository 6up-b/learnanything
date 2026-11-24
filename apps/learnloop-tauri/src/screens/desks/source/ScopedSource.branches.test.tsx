// Ported from screens/ReaderScreen.branches.test.tsx (the Reader's retirement, phase 2 step 1): the same cases,
// mounting the scoped source a source window mounts, without the standalone screen's own branches.
// Left out of the step 1 copy (kept in the original); where each went in step 2 (the original is deleted with the
// standalone screen):
//   - "does not attach an in-flight answer after leaving and reopening a source": PORTED here as "does not attach an
//     in-flight answer after closing the source's window and opening it again" (leaving a book is closing its window).
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ScopedSource } from "./ScopedSource";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../../api/dto";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
// Composition with main: the guide-overlay fix reads peek() (absent on the branch).
vi.mock("../../../api/queryCache", () => ({ getOrFetch: (_key: unknown, fetch: () => unknown) => fetch(), peek: () => ({ data: undefined }) }));
vi.mock("../../reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const saved = {
  eventId: "root", extractionId: view.extractionId, spanId: "span_symmetric_prose",
  questionMd: "Saved question", answerMd: "Saved answer", answerMode: "answer_directly", citations: [],
  selectionSpanIds: ["span_symmetric_prose", "span_spectral_worked"], selectionQuoteMd: "Saved exact selection", createdAt: null,
};
const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
beforeEach(() => {
  vi.resetAllMocks();
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGuidePlan.mockResolvedValue({ sections: [] });
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [saved] });
  api.readerAsk.mockResolvedValue({ readerAnswerEventId: "child", parentExchangeId: "root", answerMd: "Follow-up answer", answerMode: "answer_directly", citations: [] });
});
afterEach(cleanup);

async function openFollowUp() {
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Saved question/ }));
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
}

it("hydrates an old root, submits inherited anchors, and restores its child after remount", async () => {
  const onError = vi.fn();
  const first = render(<ScopedSource initialSource={initialSource} onError={onError} />);
  await openFollowUp();
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Why does that follow?" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up · ctrl+↵" }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledWith(expect.objectContaining({
    extractionId: view.extractionId, spanId: saved.spanId, parentExchangeId: "root", question: "Why does that follow?",
    selectionSpanIds: saved.selectionSpanIds, selectionQuote: saved.selectionQuoteMd,
  })));
  expect(await screen.findByText("Follow-up answer")).toBeTruthy();
  first.unmount();
  api.readerAskHistory.mockResolvedValue({ exchanges: [{ ...saved, eventId: "child", parentExchangeId: "root", questionMd: "Why does that follow?", answerMd: "Follow-up answer" }, saved] });
  render(<ScopedSource initialSource={initialSource} onError={onError} />);
  await openFollowUp();
  fireEvent.click(screen.getByRole("button", { name: /▸ Why does that follow/ }));
  expect(screen.getByText("Follow-up answer")).toBeTruthy();
  expect(onError).not.toHaveBeenCalled();
});

it("new thread explicitly clears the parent and uses the current passage", async () => {
  render(<ScopedSource initialSource={initialSource} onError={vi.fn()} />);
  await openFollowUp();
  fireEvent.click(screen.getByRole("button", { name: "new thread from current passage" }));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Different topic" } });
  fireEvent.click(screen.getByRole("button", { name: "ask · ctrl+↵" }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledWith(expect.objectContaining({ parentExchangeId: null, spanId: initialSource.spanId })));
});

it("retains the question and parent on failure so a follow-up can be retried", async () => {
  const onError = vi.fn();
  api.readerAsk.mockRejectedValueOnce(new Error("Provider offline"));
  render(<ScopedSource initialSource={initialSource} onError={onError} />);
  await openFollowUp();
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Retry me" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up · ctrl+↵" }));
  await waitFor(() => expect(onError).toHaveBeenCalledWith("Provider offline"));
  expect((screen.getByPlaceholderText("ask about this passage…") as HTMLTextAreaElement).value).toBe("Retry me");
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up · ctrl+↵" }));
  expect(await screen.findByText("Follow-up answer")).toBeTruthy();
  expect(api.readerAsk.mock.calls[1][0].parentExchangeId).toBe("root");
});

// Ported in phase 2 step 2 from "does not attach an in-flight answer after leaving and reopening a source": the way
// out was the old header's "← Library" and the way back its list of books (the standalone frame's); on the desks the
// book is left by closing its window (the source unmounts) and opened again in a new one (a new source).
it("does not attach an in-flight answer after closing the source's window and opening it again", async () => {
  let finish!: (answer: unknown) => void;
  api.readerAsk.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  render(<ScopedSource initialSource={initialSource} onError={vi.fn()} />);
  await openFollowUp();
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Still running" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up · ctrl+↵" }));
  cleanup();
  render(<ScopedSource initialSource={initialSource} onError={vi.fn()} />);
  await openFollowUp();
  await act(async () => finish({ readerAnswerEventId: "late", parentExchangeId: "root", answerMd: "Stale response", answerMode: "answer_directly", citations: [] }));
  expect(screen.queryByText("Stale response")).toBeNull();
  expect((screen.getByPlaceholderText("ask about this passage…") as HTMLTextAreaElement).value).toBe("");
});
