// RW4d's switch off (reader_compare.keep_enabled = false: no `compareKeep` in
// the prompt contract) leaves RW4a's compare table and RW1c's tutor
// comparison exactly as they were (spec §7.8, §12). The snapshots were
// written on the base frontend (3988cf778, before any RW4d frontend code) and
// must not change; nothing here asks for kept comparisons or their marks.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { LibraryAskDto, SourceLibraryCard, SourceToolRequestDto } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { defaultTutorOfferStore, OFFER_COPY, TutorOffers } from "./TutorOffers";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(),
    runSourceTool: vi.fn(), recordSourceOfferShown: vi.fn(),
    // RW4d's (absent on the base): never called while the switch is off.
    readerKeptComparisons: vi.fn(), readerLibraryCompareKeep: vi.fn(), readerLibraryCompareRemove: vi.fn(),
    readerLibraryCompareReopen: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card, other] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const other = { sourceId: "src_other", title: "Other Book", canonicalUri: "other.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const BOX = "What do you want to do with this?";

function hit(key: string, sourceId: string, sourceTitle: string, text: string) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId, sourceTitle, section: "Chapter 5", page: 3, text, role: "definition",
    group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source" as const, label: "source-authored" };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword + meaning", learningObjectIds: ["lo_spectral"], extractionId: view.extractionId,
  anchorSpanIds: ["span_symmetric_prose"],
  hits: [
    hit("ext_other:o1", "src_other", "Other Book", "A symmetric matrix equals its transpose."),
    hit("ext_symmetric:span_spectral_worked", view.sourceId, "Matrices", "Worked: diagonalize a symmetric matrix."),
  ],
  groups: {
    sources: [
      { sourceId: "src_other", sourceTitle: "Other Book", groups: [{ group: "Foundation", keys: ["ext_other:o1"] }] },
      { sourceId: view.sourceId, sourceTitle: "Matrices", groups: [{ group: "Foundation", keys: ["ext_symmetric:span_spectral_worked"] }] },
    ],
    expansions: [],
  },
  expansions: [], expandGraph: true, sourceCount: 2, passageCount: 2,
};

const TABLE = {
  askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
  rows: [
    { sourceId: view.sourceId, sourceTitle: "Matrices", key: "ext_symmetric:span_spectral_worked", page: 3, isOpenSource: true,
      contributes: [{ line: "a worked case", quote: "diagonalize a symmetric matrix", authorship: "ai" }], assumes: [],
      differs: [{ line: "one works it, one defines it", quote: "Worked: diagonalize", relation: "different_assumptions", otherSourceTitle: "Other Book", authorship: "ai" }] },
    { sourceId: "src_other", sourceTitle: "Other Book", key: "ext_other:o1", page: 3, isOpenSource: false,
      contributes: [{ line: "the definition", quote: "equals its transpose", authorship: "ai" }], assumes: [], differs: [] },
  ],
  alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0,
};

function done<T>(result: T, kind = "ask") {
  return { jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result };
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
  defaultTutorOfferStore.clear();
  // Library ask and compare on; no compareKeep (RW4d's switch off).
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true } };
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerLibraryAsk.mockResolvedValue(done(ASK));
  api.readerLibraryAskNotes.mockResolvedValue(done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
  api.readerLibraryCompare.mockResolvedValue(done(TABLE, "compare"));
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
  api.recordSourceOfferShown.mockResolvedValue({ interventionId: null, recorded: false });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

function rw4dNeverCalled() {
  for (const name of ["readerKeptComparisons", "readerLibraryCompareKeep", "readerLibraryCompareRemove", "readerLibraryCompareReopen"] as const) {
    expect(api[name]).not.toHaveBeenCalled();
  }
}

it("keep off: the compare table in the comparing posture is RW4a's, byte for byte", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  const pane = await screen.findByRole("region", { name: "ask your library" });
  const pins = await within(pane).findAllByRole("button", { name: "pin" });
  fireEvent.click(pins[0]);
  fireEvent.click(pins[1]);
  fireEvent.click(within(pane).getByRole("button", { name: /compare pinned \(2\)/ }));
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  expect(api.readerLibraryCompare.mock.calls[0][0]).toEqual({
    askId: "la_1", pinnedSpanKeys: ["ext_other:o1", "ext_symmetric:span_spectral_worked"], openSourceId: view.sourceId,
  });
  expect(pane.innerHTML).toMatchSnapshot("comparing posture with the table");
  // The reading surface carries no kept-comparison mark.
  expect(document.body.textContent).not.toContain("⇄");
  rw4dNeverCalled();
});

const COMPARE: SourceToolRequestDto = { toolCallId: "stc_c", tool: "compare_sources", reason: "Your books differ here", run: "lazy", dropped: [], arguments: {} };
const compareRun = { version: 1, tool: "compare_sources", policy: "reading", toolCallId: "stc_c", runId: "r2", result: { status: "ok", comparisonId: "scmp_2", sources: [
  { ref: "s1", sourceId: "src_book", sourceTitle: "Linear Algebra Notes", extractionId: "ext_book", spanId: "s7", page: 1, passage: "x", label: "source-authored", contributions: [{ contribution: "states the sign rule", quote: "changes sign" }] },
  { ref: "s2", sourceId: "src_text", sourceTitle: "Matrix Theory", extractionId: "ext_text", spanId: "t3", page: 7, passage: "y", label: "source-authored", contributions: [{ contribution: "gives the factor", quote: "times -1" }] },
], relations: [{ leftRef: "s1", rightRef: "s2", relation: "different_notation", statement: "sign vs factor", leftQuote: "changes sign", rightQuote: "times -1" }],
  missingPerspectives: [] } };

it("keep off: the tutor's comparison is RW1c's, byte for byte", async () => {
  api.runSourceTool.mockResolvedValue(compareRun);
  const { container } = render(<TutorOffers exchangeId="a1" extractionId="ext_text" toolRequests={[COMPARE]} />);
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  await screen.findByRole("table", { name: "how your sources treat this" });
  await waitFor(() => expect(api.recordSourceOfferShown).toHaveBeenCalledTimes(1));
  expect(container.innerHTML).toMatchSnapshot("tutor comparison pressed");
  rw4dNeverCalled();
});
