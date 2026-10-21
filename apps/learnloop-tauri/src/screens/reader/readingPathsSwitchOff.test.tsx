// RW7a's kill switch on the screens (spec §10.1, §12; orchestrator note 6):
// with reading_paths.enabled off the prompt contract carries no
// `readingPaths` key, and the Reader renders exactly what it rendered before
// RW7a -- the Guide's goal card, no path card, no reading-path call. The
// snapshots in __snapshots__/readingPathsSwitchOff.test.tsx.snap were written
// on the base commit (a76c8358a), before any RW7a frontend code existed; the
// api mocks name only the calls the base code made, so a reading-path call
// would fail here.
import { cleanup, render, screen } from "@testing-library/react";
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
const plan = vi.hoisted(() => ({
  sourceId: "src", extractionId: "ext", personalized: true, selectionBasis: "reviewed boundary placements",
  goalContext: { goalId: "goal_mix", title: "Derive mixture distributions", goldenPathRunId: null, targetContractVersionId: null },
  sections: [], pendingDiagnosisAttemptIds: [],
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
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

it("switched off (no readingPaths in the contract), the Reader and its Guide are the base's byte for byte", async () => {
  setAlgoConfig({ practice: { stuckPrompt: true }, ui: { practiceFeedback: "simple" } });
  const onError = vi.fn();
  const view = render(<ReaderScreen initialSource={source} onError={onError} />);
  await screen.findAllByText(/symmetric/i);
  await screen.findByText("Derive mixture distributions");
  expect(screen.getByText("Reading toward your active goal")).toBeTruthy();
  expect(markup(view.container)).toMatchSnapshot("reader guide, reading paths switched off");
  expect(onError).not.toHaveBeenCalled();
  for (const mock of Object.values(api)) {
    for (const call of mock.mock.calls) expect(JSON.stringify(call)).not.toMatch(/reading_?path/i);
  }
});
