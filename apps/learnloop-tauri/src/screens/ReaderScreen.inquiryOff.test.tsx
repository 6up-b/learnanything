// RW1a's kill switch on the screen: reader_inquiry off (the contract carries no
// inquiryEnabled) is today's flat Ask rail, and reader.ask goes out without a
// parentExchangeId, exactly as before.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../api/dto";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const saved = {
  eventId: "root", extractionId: view.extractionId, spanId: "span_symmetric_prose",
  questionMd: "Saved question", answerMd: "Saved answer", answerMode: "answer_directly", citations: [], createdAt: null,
};
const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

beforeEach(() => {
  vi.resetAllMocks();
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [saved] });
  api.readerAsk.mockResolvedValue({ eventId: "q2", readerAnswerEventId: "a2", answerMd: "Fresh answer", answerMode: "answer_directly", citations: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(cleanup);

it("shows today's flat history with no follow-up, status or detour controls", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  expect(await screen.findByText("Previous asks")).toBeTruthy();
  expect(screen.queryByText("Clarification threads")).toBeNull();
  expect(screen.queryByRole("button", { name: "ask follow-up" })).toBeNull();
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
  expect(screen.queryByRole("button", { name: /reopen|resolved/ })).toBeNull();
});

it("asks without a parentExchangeId and never logs inquiry activity", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.change(await screen.findByPlaceholderText("ask about this passage…"), { target: { value: "Plain question" } });
  fireEvent.click(screen.getByRole("button", { name: "ask ↵" }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect("parentExchangeId" in api.readerAsk.mock.calls[0][0]).toBe(false);
  expect(await screen.findByText("Fresh answer")).toBeTruthy();
  expect(api.readerLogActivity).not.toHaveBeenCalled();
});
