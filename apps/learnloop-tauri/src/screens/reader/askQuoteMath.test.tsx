// UX-26 on the real Reader with the real renderer: a passage with a formula, selected and asked about, sends the
// tutor (and keeps for "§ from the book") the passage with the formula once, as its TeX. A highlight of the same
// selection anchors with exactly the words it anchored with before (the sidecar finds the passage from them), and an
// exchange saved before the fix is shown as it was stored.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerCapture: vi.fn(), readerSetInquiryStatus: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_symmetric_prose" };
const PROSE = view.blocks.find((block) => block.spanId === "span_symmetric_prose")!;

// What the old code quoted from the same selection: every layer of the formula.
const OLD = "QQQ produces an orthogonal matrix, which means that QT=Q−1.Q^T = Q^{-1}\\text{.}QT=Q−1.";

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerAsk.mockResolvedValue({
    eventId: "q1", readerAnswerEventId: "ev1", parentExchangeId: null, answerMd: "Because it is symmetric.",
    answerMode: "answer_directly", citations: [], manifest: { version: "v" }, model: "stub-model",
  });
  api.readerCapture.mockResolvedValue({ annotationId: "an1", anchorStatus: "exact" });
});
afterEach(cleanup);

async function selectProse(): Promise<HTMLElement> {
  await screen.findAllByText(/admits an orthonormal eigenbasis/);
  const block = Array.from(document.querySelectorAll<HTMLElement>('[data-span-id="span_symmetric_prose"]')).find((element) => element.querySelector(".katex"))!;
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  return block;
}

const CLEAN =
  "A real symmetric matrix $A = A^\\top$ admits an orthonormal eigenbasis. When choosing a decomposition for a variance problem, " +
  "the spectral decomposition is preferred over a general SVD because the eigenvalues are the variances along principal axes.";

it("UX-26: asking about a passage with a formula sends the passage with the formula once, as its TeX", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  const box = await screen.findByPlaceholderText("ask about this passage…");
  fireEvent.change(box, { target: { value: "Why orthonormal?" } });
  fireEvent.keyDown(box, { key: "Enter", ctrlKey: true });
  await screen.findByText("Because it is symmetric.");
  expect(api.readerAsk).toHaveBeenCalledTimes(1);
  expect(api.readerAsk.mock.calls[0][0].selectionQuote).toBe(CLEAN);
  expect(PROSE.markdown).toContain("$A = A^\\top$");
  // "§ from the book" draws that formula, once, and shows no dollar sign.
  const quoted = screen.getByText(/admits an orthonormal eigenbasis/, { selector: "blockquote p" });
  expect(quoted.querySelectorAll(".katex")).toHaveLength(1);
  expect(quoted.textContent).not.toContain("$");
});

it("UX-26: a highlight of the same selection anchors with the words it always did", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  const block = await selectProse();
  // The anchor's words, as the old code took them: the block's selected text, every layer included.
  const asBefore = (block.textContent ?? "").replace(/\s+/g, " ").trim();
  expect(asBefore).toContain("A=A⊤A = A^\\topA=A⊤");
  fireEvent.click(await screen.findByRole("button", { name: "highlight" }));
  await vi.waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
  expect(api.readerCapture.mock.calls[0][0].rawSelection.nodes).toEqual([{ spanId: "span_symmetric_prose", quote: asBefore }]);
});

it("UX-26: an exchange saved before the fix is shown as it was stored", async () => {
  api.readerAskHistory.mockResolvedValue({ exchanges: [{
    eventId: "old", parentExchangeId: null, extractionId: view.extractionId, spanId: "span_symmetric_prose",
    questionMd: "Old question?", answerMd: "Old answer", answerMode: "answer_directly", citations: [],
    selectionSpanIds: ["span_symmetric_prose"], selectionQuoteMd: `into a matrix ${OLD}`, createdAt: null,
    questionEventId: "q_old", resolution: "open",
  }] });
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Old question\?/ }));
  expect(document.body.textContent).toContain(OLD);
});
