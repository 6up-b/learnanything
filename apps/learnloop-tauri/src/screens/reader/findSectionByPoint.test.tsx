// Reader CA4 landing, interaction (i): CA5a's "compare" on a found section
// (the Guide footer's "find this section in my other books") under
// reader_compare.by_point on and off, with CA3's compare from anywhere off
// (CA5a's library-ask path, both passages pinned) and on (CA3's selection
// door). By point on, a v2 comparison renders as the table by point; off, the
// sidecar answers v1 and the table is by book exactly as before, with no
// "compare again by point". A failed comparison's "try again" reruns it with
// the same pins (CA5a F5/F8) or, with CA3 on, the same request, and the rerun
// renders by point.
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


const OPEN_KEY = (span: string) => `${view.extractionId}:${span}`;
const HIT_KEY = "ext_axler:a7";
const ASK = {
  askId: "la_1", query: "6.1 Symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: false, basis: "keyword", learningObjectIds: [], extractionId: view.extractionId, anchorSpanIds: [],
  // The section's ask finds both passages (the comparison renders under the answer's hits).
  hits: [
    { key: OPEN_KEY(SPAN_IDS[0]), extractionId: view.extractionId, spanId: SPAN_IDS[0], sourceId: view.sourceId, sourceTitle: "Strang",
      section: null, page: 3, text: "one", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [],
      authorship: "source", label: "source-authored" },
    { key: HIT_KEY, extractionId: "ext_axler", spanId: "a7", sourceId: "src_axler", sourceTitle: "Axler",
      section: null, page: 5, text: "two", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [],
      authorship: "source", label: "source-authored" },
  ],
  groups: { sources: [], expansions: [] }, expansions: [], expandGraph: false, sourceCount: 2, passageCount: 2,
};

function compared(openSpan: string, v2: boolean) {
  const open = OPEN_KEY(openSpan);
  const rows = [
    { sourceId: view.sourceId, sourceTitle: "Strang", key: open, page: 3, isOpenSource: true, contributes: [], assumes: [], differs: [] },
    { sourceId: "src_axler", sourceTitle: "Axler", key: HIT_KEY, page: 5, isOpenSource: false, contributes: [], assumes: [], differs: [] },
  ];
  const base = {
    askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source", rows,
    alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0, kept: null, exposureEventIds: [],
    verification: { status: null, stopped: null, verifiedSources: null },
  };
  if (!v2) return { ...base, contract: "source_compare.v1" };
  return {
    ...base, contract: "source_compare.v2",
    points: [{ id: "p1", label: "why symmetric matrices diagonalize", kind: "point", labelVoice: "model",
      cells: [
        { key: open, status: "quoted", quote: "a symmetric matrix has real eigenvalues", line: "real eigenvalues first", spanKey: open, authorship: "ai" },
        { key: HIT_KEY, status: "quoted", quote: "self-adjoint operators have an orthonormal eigenbasis", line: "the spectral theorem", spanKey: HIT_KEY, authorship: "ai" },
      ],
      relations: [{ leftKey: open, rightKey: HIT_KEY, relation: "different_assumptions", statement: "one is coordinate-free",
        leftQuote: "a symmetric matrix", rightQuote: "self-adjoint operators", authorship: "ai" }] }],
  };
}

function contract(byPoint: boolean, scope: boolean) {
  return { ...ON, libraryAsk: { ...ON.libraryAsk, ...(scope ? { compareScope: true } : {}), ...(byPoint ? { compareByPoint: true } : {}) } };
}

async function pressCompare() {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  fireEvent.click(await screen.findByRole("button", { name: "compare with Axler 5.A Invariant subspaces" }));
}

function anchorOf(call: unknown[]): string {
  const input = call[0] as { pinnedSpanKeys?: string[]; anchorSpanIds?: string[] };
  return input.anchorSpanIds?.length ? input.anchorSpanIds[0] : input.pinnedSpanKeys![0].split(":")[1];
}

for (const byPoint of [true, false]) {
  it(`CA3 off, by_point ${byPoint ? "on" : "off"}: CA5a's pinned comparison renders ${byPoint ? "by point" : "by book"}; a failed one reruns with the same pins`, async () => {
    state.contract = contract(byPoint, false);
    api.readerLibraryAsk.mockResolvedValue({ jobId: "j_ask", kind: "ask", askId: "la_1", state: "done", result: ASK });
    let here = "";
    api.readerLibraryCompare
      .mockRejectedValueOnce({ code: "internal", message: "the sidecar hiccuped" })
      .mockImplementation(async (input: { pinnedSpanKeys: string[] }) => ({ jobId: "j_cmp", kind: "compare", askId: "la_1", state: "done",
        result: compared(input.pinnedSpanKeys[0].split(":")[1], byPoint) }));
    await pressCompare();
    await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
    here = anchorOf(api.readerLibraryCompare.mock.calls[0]);
    const pins = [OPEN_KEY(here), HIT_KEY];
    expect(api.readerLibraryCompare.mock.calls[0][0]).toMatchObject({ askId: "la_1", pinnedSpanKeys: pins });
    fireEvent.click(await screen.findByRole("button", { name: /try again/ }));
    await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
    expect(api.readerLibraryCompare.mock.calls[1][0]).toMatchObject({ askId: "la_1", pinnedSpanKeys: pins });
    expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1);
    expect(api.readerLibraryAskNotes).not.toHaveBeenCalled();
    if (byPoint) {
      await waitFor(() => expect(document.querySelector("[data-compare-points]")).toBeTruthy());
      expect(screen.getByText("why symmetric matrices diagonalize")).toBeTruthy();
      expect(document.querySelector("[data-compare-table]")).toBeNull();
    } else {
      await waitFor(() => expect(document.querySelector("[data-compare-table]")).toBeTruthy());
      expect(document.querySelector("[data-compare-points]")).toBeNull();
      expect(document.querySelector("[data-compare-again]")).toBeNull();
    }
  });

  it(`CA3 on, by_point ${byPoint ? "on" : "off"}: the selection door's comparison renders ${byPoint ? "by point" : "by book"}; a failed one reruns as the same request`, async () => {
    state.contract = contract(byPoint, true);
    api.readerLibraryCompare
      .mockRejectedValueOnce({ code: "internal", message: "the sidecar hiccuped" })
      .mockImplementation(async (input: { anchorSpanIds: string[] }) => ({ jobId: "j_cmp", kind: "compare", askId: "la_c", state: "done",
        result: { ...compared(input.anchorSpanIds[0], byPoint), askId: "la_c", library: [],
          scope: { door: "selection", question: "6.1 Symmetric matrices", sourceIds: ["src_axler"], anchorKeys: [OPEN_KEY(input.anchorSpanIds[0])] } } }));
    await pressCompare();
    await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
    const first = api.readerLibraryCompare.mock.calls[0][0];
    expect(first).toMatchObject({ door: "selection", askId: null, sourceIds: ["src_axler"], pinnedSpanKeys: [] });
    fireEvent.click(await screen.findByRole("button", { name: /try again/ }));
    await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
    expect(api.readerLibraryCompare.mock.calls[1][0]).toEqual(first);
    expect(api.readerLibraryAsk).not.toHaveBeenCalled();
    if (byPoint) {
      await waitFor(() => expect(document.querySelector("[data-compare-points]")).toBeTruthy());
      expect(screen.getByText("why symmetric matrices diagonalize")).toBeTruthy();
    } else {
      await waitFor(() => expect(document.querySelector("[data-compare-table]")).toBeTruthy());
      expect(document.querySelector("[data-compare-points]")).toBeNull();
      expect(document.querySelector("[data-compare-again]")).toBeNull();
    }
  });
}
