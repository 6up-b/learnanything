// RW1b's kill switches on the screen (spec §4.5, §12 "kill-switch parity"):
// with reader_intent.enabled off (or reader_inquiry off) the prompt contract
// carries no `intent` key, and a selection behaves exactly as before RW1b --
// no intent box, the palette in Notes and the rail flipped to Notes, keys
// doing what they did. The snapshots in __snapshots__/intentSwitchOff.test.tsx.snap
// were written on the base commit (09acb51fd), before any RW1b frontend code
// existed; an intent or active-reading call would throw here, because the api
// mocks name only the calls the base code made.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(),
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
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

const OFF_CONTRACTS: Array<[string, Record<string, unknown>]> = [
  ["reader_intent off (the contract names inquiry only)", { readerEnabled: true, inquiryEnabled: true }],
  ["reader_inquiry off as well (the flat rail)", { readerEnabled: true }],
];

it.each(OFF_CONTRACTS)("a selection is today's with %s", async (_label, value) => {
  contract.value = value;
  const view_ = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  expect(markup(view_.container)).toMatchSnapshot("reader before a selection");
  select(block);
  await screen.findByText(/^selected ·/);
  expect(markup(view_.container)).toMatchSnapshot("reader after a selection (the rail on Notes)");
  fireEvent.keyDown(window, { key: "Tab" });
  fireEvent.keyDown(window, { key: "?" });
  fireEvent.keyDown(window, { key: "w" });
  expect(markup(view_.container)).toMatchSnapshot("reader after Tab, ? and a letter");
  for (const mock of Object.values(api)) {
    for (const call of mock.mock.calls) expect(JSON.stringify(call)).not.toMatch(/intent|active_?reading|next_?step/i);
  }
});

it("with Ask open, a selection keeps Ask (today's rule) while reader_intent is off", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true };
  const view_ = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  expect(markup(view_.container)).toMatchSnapshot("ask rail after a selection");
});
