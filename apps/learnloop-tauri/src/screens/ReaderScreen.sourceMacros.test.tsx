// UX-2 on the real Reader screen (walks student-1 #132, retainer-1 #19, beginner-1 #61): a source's formulas are drawn
// with its own macros (reader.render_view's mathMacros), in the book's text and in the Ask chip's clipped quote.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import type { ReaderRenderViewDto, SourceLibraryCard } from "../api/dto";

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

const PROSE = "If \\(\\vvec\\) is in \\(\\real^n\\), then so is \\(2\\vvec\\).";
const view: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  blocks: [readerRenderViewFixture.blocks[0], { ...readerRenderViewFixture.blocks[1], markdown: PROSE }],
  mathMacros: { "\\vvec": "{\\mathbf v}", "\\real": "{\\mathbb R}" }
};
const initialSource = { card: { sourceId: view.sourceId, title: "Understanding Linear Algebra", canonicalUri: "page.html", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: null };

// KaTeX's two ways of showing what it cannot read: an error span, or the raw command in its error colour.
const ERROR = /katex-error|mathcolor="#cc0000"/;

beforeEach(() => {
  vi.resetAllMocks();
  Element.prototype.scrollIntoView = vi.fn();
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(cleanup);

async function shownPage(reply: ReaderRenderViewDto): Promise<string> {
  api.readerRenderView.mockResolvedValue(reply);
  const { container } = render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await screen.findAllByText(/then so is/);
  return container.innerHTML;
}

it("UX-2: the book's \\vvec and \\real render as the book defines them, with no error node", async () => {
  const html = await shownPage(view);
  expect(html).not.toMatch(ERROR);
  expect(html).toContain('<mi mathvariant="bold">v</mi>');
  expect(html).toContain('<mi mathvariant="double-struck">R</mi>');
  expect(html).not.toContain("ℜ");
});

it("UX-2: a reading from an older sidecar (no mathMacros) renders as before", async () => {
  const { mathMacros: _none, ...older } = view;
  expect(await shownPage(older)).toMatch(ERROR);
});
