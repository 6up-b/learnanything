// Reader CA5a in the Reader (ux_reader_compare_ask_v1 §6.2, §6.3, §13): with
// `correspondence` in the prompt contract the Guide's footer offers "find
// this section in my other books" for the section in view; compare runs the
// library compare path on both sections' passages; go there opens the other
// book. Without the key (reader.correspondence.enabled or curriculum.enabled
// off) the Guide is exactly as before and nothing is read.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { CorrespondentsDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { FIND_COPY } from "./FindSection";

const SPAN_IDS = view.blocks.map((block) => block.spanId!).filter(Boolean);

const { api, plan, state } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(),
    getSpanView: vi.fn(), readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(), readerSaveProgress: vi.fn(),
  },
  plan: {
    sourceId: "src", extractionId: "ext", personalized: true, selectionBasis: "", goalContext: null,
    sections: [] as unknown[], pendingDiagnosisAttemptIds: [],
  },
  state: { contract: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({
  useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? state.contract : { sources: [source.card, AXLER] }, error: null }),
}));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const ON = {
  readerEnabled: true, inquiryEnabled: true,
  libraryAsk: { expandGraph: false, personalizedDefault: false, compare: true },
  correspondence: { enabled: true, findSection: true },
};
const OFF = { readerEnabled: true, inquiryEnabled: true, libraryAsk: ON.libraryAsk };
const source = { card: { sourceId: view.sourceId, title: "Strang", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: SPAN_IDS[1] };
const AXLER = { sourceId: "src_axler", title: "Axler", canonicalUri: "axler.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;

const HIT = {
  extractionId: "ext_axler", sectionId: "ax5a", title: "5.A Invariant subspaces", sourceId: "src_axler", sourceTitle: "Axler",
  read: false, jump: { extractionId: "ext_axler", sectionId: "ax5a", spanId: "a7" }, treatment: null,
  label: "found by search, not checked", by: "search" as const,
};
const QUIET: CorrespondentsDto = {
  extractionId: view.extractionId, sectionId: "u1", status: "none", learningObjects: [], search: null, checkableLearningObjectIds: ["lo_sym"],
};
const PRESSED: CorrespondentsDto = {
  ...QUIET, status: "unchecked",
  search: { label: "found by search, not checked", correctableLearningObjectIds: ["lo_sym"], sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [HIT] }] },
};

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  plan.extractionId = view.extractionId;
  plan.sourceId = view.sourceId;
  plan.sections = [{ id: "u1", label: "6.1 Symmetric matrices", startSpanId: SPAN_IDS[0], endSpanId: SPAN_IDS[SPAN_IDS.length - 1],
    spanIds: SPAN_IDS, question: null, suggestedPassages: [] }];
  state.contract = ON;
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerSaveProgress.mockResolvedValue({});
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? PRESSED : QUIET));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

it("the Guide's footer offers the action for the section in view, read quietly first", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  expect(await screen.findByRole("button", { name: FIND_COPY.action })).toBeTruthy();
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: view.extractionId, sectionId: "u1", searchFallback: false });
  expect(api.readerCorrespondents).not.toHaveBeenCalledWith(expect.objectContaining({ searchFallback: true }));
  expect(screen.queryByText("found by search, not checked")).toBeNull();
});

it("switched off, nothing is offered and nothing is read", async () => {
  state.contract = OFF;
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 50)); });
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
});

it("hidden when the section has judged coverage", async () => {
  api.readerCorrespondents.mockResolvedValue({ ...QUIET, status: "judged" });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(api.readerCorrespondents).toHaveBeenCalled());
  await act(async () => { await Promise.resolve(); });
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
});

it("compare runs the library compare path on this section's passage and the hit's", async () => {
  const ask = {
    askId: "la_1", query: "6.1 Symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
    personalized: false, basis: "keyword", learningObjectIds: [], extractionId: view.extractionId, anchorSpanIds: [], hits: [],
    groups: { sources: [], expansions: [] }, expansions: [], expandGraph: false, sourceCount: 0, passageCount: 0,
  };
  api.readerLibraryAsk.mockResolvedValue({ jobId: "j_ask", kind: "ask", askId: "la_1", state: "done", result: ask });
  api.readerLibraryCompare.mockResolvedValue({ jobId: "j_cmp", kind: "compare", askId: "la_1", state: "done",
    result: { askId: "la_1", status: "ok", rows: [], exposureEventIds: [] } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  fireEvent.click(await screen.findByRole("button", { name: "compare with Axler 5.A Invariant subspaces" }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalled());
  const askInput = api.readerLibraryAsk.mock.calls[0][0];
  expect(askInput.query).toBe("6.1 Symmetric matrices");
  expect(askInput.entry).toBe("where_else_explained");
  expect(askInput.extractionId).toBe(view.extractionId);
  const here = askInput.spanIds[0];
  expect(SPAN_IDS).toContain(here);
  expect(api.readerLibraryCompare).toHaveBeenCalledWith(expect.objectContaining({
    askId: "la_1", pinnedSpanKeys: [`${view.extractionId}:${here}`, "ext_axler:a7"],
  }));
  // The learner asked to compare: the organizer's notes wait to be asked for.
  expect(api.readerLibraryAskNotes).not.toHaveBeenCalled();
  expect(document.querySelector("[data-comparing-pane]")).toBeTruthy();
});

it("go there opens the other book as a detour", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  const before = api.readerRenderView.mock.calls.length;
  fireEvent.click(await screen.findByRole("button", { name: "go there: Axler 5.A Invariant subspaces" }));
  await waitFor(() => expect(api.readerRenderView.mock.calls.length).toBeGreaterThan(before));
  expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0])).toContainEqual(expect.objectContaining({ extractionId: "src_axler" }));
});

// Reader CA3 landing: with compare from anywhere on (libraryAsk.compareScope),
// compare on a hit is CA3's one request through the selection door: anchored
// on this section's passage, the section's title the question, narrowed to
// the hit's book; no library answer is asked first.
it("with CA3 on, compare is CA3's selection door anchored on this section, narrowed to the hit's book", async () => {
  state.contract = { ...ON, libraryAsk: { ...ON.libraryAsk, compareScope: true } };
  api.readerLibraryCompare.mockResolvedValue({ jobId: "j_cmp", kind: "compare", askId: "la_c", state: "done",
    result: { askId: "la_c", status: "ok", comparisonId: null, rows: [], alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [],
      droppedLineCount: 0, header: "", verification: { status: null, stopped: null, verifiedSources: null }, exposureEventIds: [], library: [] } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  fireEvent.click(await screen.findByRole("button", { name: "compare with Axler 5.A Invariant subspaces" }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalled());
  expect(api.readerLibraryAsk).not.toHaveBeenCalled();
  const input = api.readerLibraryCompare.mock.calls[0][0];
  expect(input).toMatchObject({
    door: "selection", askId: null, question: "6.1 Symmetric matrices", extractionId: view.extractionId,
    sourceIds: ["src_axler"], pinnedSpanKeys: [], openSourceId: view.sourceId,
  });
  expect(input.anchorSpanIds).toHaveLength(1);
  expect(SPAN_IDS).toContain(input.anchorSpanIds[0]);
  expect(api.readerLibraryAskNotes).not.toHaveBeenCalled();
});
