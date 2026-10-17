// RW4a's kill switches on the screen (spec §7.7, §12 "kill-switch parity", G20):
// with library_ask.enabled off (or the sources service, or reader_inquiry off)
// the prompt contract carries no `libraryAsk` key, the palette has no Orient or
// library rows, Ctrl+Shift+F does nothing, and Shift+Enter in the library
// search is today's Enter (a deep search). The snapshots in
// __snapshots__/libraryAskSwitchOff.test.tsx.snap were written on the base
// commit (8eb1ba5d2), before any RW4a frontend code existed; a library-ask or
// comparison call would throw here, because the api mocks name only the calls
// the base code made.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture } from "../../fixtures/readerIntentContract";
import type { ReaderIntentContractDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSearchSources: vi.fn(), readerSetMode: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

/** The intent palette as the sidecar sends it with RW4a off: no library rows. */
function intentWithoutLibrary(): ReaderIntentContractDto {
  const strip = (groups: ReaderIntentContractDto["palette"]) => groups
    .map((group) => ({ ...group, actions: group.actions.filter((action) => (action.effect.kind as string) !== "library_ask") }))
    .filter((group) => group.actions.length > 0);
  return { ...readerIntentContractFixture, palette: strip(readerIntentContractFixture.palette), notesPalette: strip(readerIntentContractFixture.notesPalette) };
}

/** React's generated ids depend on render order; the markup is the contract. */
function markup(container: HTMLElement): string {
  return container.innerHTML.replace(/:r[0-9a-z]+:/g, ":r:").replace(/«r[0-9a-z]+»/g, "«r»");
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

function noLibraryCalls(): void {
  for (const mock of Object.values(api)) {
    for (const call of mock.mock.calls) expect(JSON.stringify(call)).not.toMatch(/library_?ask|libraryAsk|compare|organiz/i);
  }
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerSearchSources.mockResolvedValue({
    query: "eigen", deep: true, searchedSources: 1, basis: "keyword", rewritten: null,
    hits: [{ sourceId: view.sourceId, sourceTitle: "Matrices", extractionId: view.extractionId, spanId: "span_spectral_worked", section: "Spectral", page: 3, snippet: "the spectral theorem" }],
  });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

const OFF_CONTRACTS: Array<[string, () => Record<string, unknown>]> = [
  ["library_ask off (the intent box on)", () => ({ readerEnabled: true, inquiryEnabled: true, intent: intentWithoutLibrary(), activeReading: { foldBlocks: 3 } })],
  ["reader_inquiry off as well (the flat rail)", () => ({ readerEnabled: true })],
];

it.each(OFF_CONTRACTS)("the palette and Ctrl+Shift+F are today's with %s", async (_label, value) => {
  contract.value = value();
  const view_ = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.keyDown(window, { key: "F", ctrlKey: true, shiftKey: true });
  expect(markup(view_.container)).toMatchSnapshot("reader after Ctrl+Shift+F");
  select(block);
  await screen.findByText(/^selected ·/);
  fireEvent.keyDown(window, { key: "Tab" });
  expect(markup(view_.container)).toMatchSnapshot("reader after a selection and Tab");
  noLibraryCalls();
});

it.each(OFF_CONTRACTS)("Shift+Enter in the library search is today's Enter with %s", async (_label, value) => {
  contract.value = value();
  const view_ = render(<ReaderScreen onError={vi.fn()} />);
  const search = await screen.findByPlaceholderText("search all sources…");
  fireEvent.change(search, { target: { value: "eigen" } });
  fireEvent.keyDown(search, { key: "Enter", shiftKey: true });
  await waitFor(() => expect(api.readerSearchSources).toHaveBeenCalledWith({ query: "eigen", deep: true }));
  await screen.findByText("the spectral theorem");
  expect(markup(view_.container)).toMatchSnapshot("library after Shift+Enter");
  noLibraryCalls();
});
