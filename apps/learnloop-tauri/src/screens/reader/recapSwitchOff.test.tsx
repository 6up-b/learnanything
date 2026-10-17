// RW6a's kill switches on the screens (spec §9.6, §12 "kill-switch parity"):
// with recap.enabled and recap.wrap_up_enabled off the config DTO carries no
// `recap` key, and the Reader renders exactly what it rendered before RW6a --
// no "Last time here" card, no "last time ▸", no Wrap up in the rail footer.
// The snapshots in __snapshots__/recapSwitchOff.test.tsx.snap were written on
// the base commit (e182f3ec8), before any RW6a frontend code existed; a recap
// call would throw here, because the api mocks name only the calls the base
// code made.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../api/dto";

const { api } = vi.hoisted(() => ({ api: {
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
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

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
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
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

const OFF_CONFIGS: Array<[string, unknown]> = [
  ["the config before RW6a (no recap key)", { practice: { stuckPrompt: true }, ui: { practiceFeedback: "simple" } }],
  ["recap.enabled and recap.wrap_up_enabled = false", { practice: { stuckPrompt: true }, ui: { practiceFeedback: "simple" }, recap: { enabled: false, wrapUpEnabled: false } }],
];

it.each(OFF_CONFIGS)("the Reader, its Guide and its rail are byte-identical with %s", async (_label, config) => {
  setAlgoConfig(config);
  const view = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText(/symmetric/i);
  expect(markup(view.container)).toMatchSnapshot("reader guide, recap switched off");
  fireEvent.keyDown(window, { key: "w" });
  expect(markup(view.container)).toMatchSnapshot("reader after w, recap switched off");
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  expect(markup(view.container)).toMatchSnapshot("reader ask rail, recap switched off");
  for (const mock of Object.values(api)) {
    for (const call of mock.mock.calls) expect(JSON.stringify(call)).not.toMatch(/recap|wrap_?up/i);
  }
});
