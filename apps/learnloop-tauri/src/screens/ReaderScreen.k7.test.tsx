// K7 on the real screen: an Alt chord keeps the capture; a bare Alt clears it.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
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

const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: null };

beforeEach(() => {
  vi.resetAllMocks();
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(cleanup);

async function selectProse() {
  const block = await screen.findByText(view.blocks[1].markdown);
  const range = document.createRange();
  range.selectNodeContents(block);
  const selection = window.getSelection()!;
  selection.removeAllRanges();
  selection.addRange(range);
  fireEvent.mouseUp(block);
  await screen.findByText(/^selected ·/);
}

function press(type: "keyDown" | "keyUp", key: string, init: Record<string, unknown> = {}) {
  act(() => {
    fireEvent[type](window, { key, ...init });
  });
}

it("Alt+← keeps the capture (the chord no longer clears it)", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await selectProse();
  press("keyDown", "Alt", { altKey: true });
  press("keyDown", "ArrowLeft", { altKey: true });
  press("keyUp", "ArrowLeft", { altKey: true });
  press("keyUp", "Alt");
  expect(screen.queryByText(/^selected ·/)).not.toBeNull();
});

it("a bare Alt press still clears the capture", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await selectProse();
  press("keyDown", "Alt", { altKey: true });
  press("keyUp", "Alt");
  expect(screen.queryByText(/^selected ·/)).toBeNull();
});
