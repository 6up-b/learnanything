import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../api/dto";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
vi.mock("../api/queryCache", () => ({ getOrFetch: (_key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

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
  const first = render(<ReaderScreen initialSource={initialSource} onError={onError} />);
  await openFollowUp();
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Why does that follow?" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up ↵" }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledWith(expect.objectContaining({
    extractionId: view.extractionId, spanId: saved.spanId, parentExchangeId: "root", question: "Why does that follow?",
    selectionSpanIds: saved.selectionSpanIds, selectionQuote: saved.selectionQuoteMd,
  })));
  expect(await screen.findByText("Follow-up answer")).toBeTruthy();
  first.unmount();
  api.readerAskHistory.mockResolvedValue({ exchanges: [{ ...saved, eventId: "child", parentExchangeId: "root", questionMd: "Why does that follow?", answerMd: "Follow-up answer" }, saved] });
  render(<ReaderScreen initialSource={initialSource} onError={onError} />);
  await openFollowUp();
  fireEvent.click(screen.getByRole("button", { name: /▸ Why does that follow/ }));
  expect(screen.getByText("Follow-up answer")).toBeTruthy();
  expect(onError).not.toHaveBeenCalled();
});

it("new thread explicitly clears the parent and uses the current passage", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await openFollowUp();
  fireEvent.click(screen.getByRole("button", { name: "new thread from current passage" }));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Different topic" } });
  fireEvent.click(screen.getByRole("button", { name: "ask ↵" }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledWith(expect.objectContaining({ parentExchangeId: null, spanId: initialSource.spanId })));
});

it("retains the question and parent on failure so a follow-up can be retried", async () => {
  const onError = vi.fn();
  api.readerAsk.mockRejectedValueOnce(new Error("Provider offline"));
  render(<ReaderScreen initialSource={initialSource} onError={onError} />);
  await openFollowUp();
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Retry me" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up ↵" }));
  await waitFor(() => expect(onError).toHaveBeenCalledWith("Provider offline"));
  expect((screen.getByPlaceholderText("ask about this passage…") as HTMLTextAreaElement).value).toBe("Retry me");
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up ↵" }));
  expect(await screen.findByText("Follow-up answer")).toBeTruthy();
  expect(api.readerAsk.mock.calls[1][0].parentExchangeId).toBe("root");
});

it("does not attach an in-flight answer after leaving and reopening a source", async () => {
  let finish!: (answer: unknown) => void;
  api.readerAsk.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await openFollowUp();
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Still running" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up ↵" }));
  fireEvent.click(screen.getByText("← library"));
  fireEvent.click(await screen.findByText("Matrices"));
  await openFollowUp();
  await act(async () => finish({ readerAnswerEventId: "late", parentExchangeId: "root", answerMd: "Stale response", answerMode: "answer_directly", citations: [] }));
  expect(screen.queryByText("Stale response")).toBeNull();
  expect((screen.getByPlaceholderText("ask about this passage…") as HTMLTextAreaElement).value).toBe("");
});
