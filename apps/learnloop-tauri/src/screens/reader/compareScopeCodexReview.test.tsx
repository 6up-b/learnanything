// Reader CA3, Codex review (codex-job 20261027-181031-WuQtZY): the frontend findings.
//
// * F1: the selection verb while a problem is open in the workbench runs
//   nothing (the comparing posture is hidden there); a line says so, and the
//   comparison starts once the learner leaves. The payload names the bound
//   workbench session (one key more, for every door).
// * F2: removing every book stops the comparison and keeps the picker; it is
//   never "every book".
// * F5: a library answer's "compare these books" has every door's controls
//   (refine, previous, the tutor about the comparison shown, never the pins).
// * F6: a tutor answer about a comparison is cleared when the books change.
// * F7: the earlier table stays reachable while its replacement is pending,
//   failed or cancelled.
// * F8: at the views' bound nothing is dropped unasked: the learner removes one.
// * F9: an × after a refinement corrects the refinement's reading; "change"
//   still corrects the ask box's.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { CompareScopeReadingDto, CompareTableDto, LibraryAskDto, SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { SCOPE_COPY, comparePayload } from "./useLibraryAsk";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(), readerCompareScope: vi.fn(), readerCompareScopeCorrection: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(), runSourceTool: vi.fn(),
    recordSourceOfferShown: vi.fn(),
    workbenchForSource: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchSaveStep: vi.fn(),
    workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchReopen: vi.fn(),
    workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(), workbenchSubmit: vi.fn(),
    workbenchSessionForAttempt: vi.fn(), readerKeptComparisons: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string; readOnly?: boolean }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} readOnly={p.readOnly} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";
const PROSE = view.blocks[1].markdown;
const LIBRARY = [{ sourceId: "src_axler", title: "Axler" }, { sourceId: "src_strang", title: "Strang" }, { sourceId: "src_lay", title: "Lay" }];

function done<T>(result: T, kind = "compare", jobId = `ljob_${kind}`) {
  return { jobId, kind, askId: "la_c", state: "done" as const, result };
}
function pending(kind: string, jobId: string) {
  return { jobId, kind, askId: "la_c", state: "pending" as const, result: null };
}

function table(extra: Partial<CompareTableDto> = {}): CompareTableDto {
  return {
    askId: "la_c", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
    rows: [
      { sourceId: "src_axler", sourceTitle: "Axler", key: "ext_a:a1", page: 133, isOpenSource: false,
        contributes: [{ line: "no determinant", quote: "without determinants", authorship: "ai" }], assumes: [], differs: [] },
      { sourceId: "src_strang", sourceTitle: "Strang", key: "ext_s:s1", page: 289, isOpenSource: false,
        contributes: [{ line: "roots of det", quote: "det(A - tI) = 0", authorship: "ai" }], assumes: [], differs: [] },
    ],
    alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0,
    scope: { door: "ask_box", question: "eigenvalues", sourceIds: ["src_axler", "src_strang"], anchorKeys: [] },
    library: LIBRARY, ...extra,
  };
}

function reading(extra: Partial<CompareScopeReadingDto> = {}): CompareScopeReadingDto {
  return {
    readingId: "cscp_1", mode: "ask", status: "read", reason: null, intent: "compare",
    sourceIds: ["src_axler", "src_strang"], books: [{ sourceId: "src_axler", title: "Axler" }, { sourceId: "src_strang", title: "Strang" }],
    unmatched: null, topic: "eigenvalues", change: null, judgmentId: "jl_1", library: LIBRARY, ...extra,
  };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword", learningObjectIds: [], extractionId: view.extractionId, anchorSpanIds: [],
  hits: [
    { key: "ext_other:o1", extractionId: "ext_other", spanId: "o1", sourceId: "src_other", sourceTitle: "Other Book", section: "Chapter 5", page: 3, text: "A symmetric matrix equals its transpose.", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source", label: "source-authored" },
    { key: "ext_symmetric:w", extractionId: "ext_symmetric", spanId: "w", sourceId: view.sourceId, sourceTitle: "Matrices", section: "Chapter 5", page: 3, text: "Worked: diagonalize a symmetric matrix.", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source", label: "source-authored" },
  ],
  groups: { sources: [
    { sourceId: "src_other", sourceTitle: "Other Book", groups: [{ group: "Foundation", keys: ["ext_other:o1"] }] },
    { sourceId: view.sourceId, sourceTitle: "Matrices", groups: [{ group: "Foundation", keys: ["ext_symmetric:w"] }] },
  ], expansions: [] },
  expansions: [], expandGraph: false, sourceCount: 2, passageCount: 2,
};

function tutorAnswer(answerMd: string) {
  return { askId: "la_c", eventId: "ev_t", answerMd, citations: [], label: "AI-written" };
}

function wbSession(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: null, stemMd: PROSE, importStatus: "pending", importError: null, origin: "reader",
    entry: "work_through", parentSessionId: null, extractionId: view.extractionId, spanIds: ["span_symmetric_prose"],
    sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open",
    attemptId: null, createdAt: "2026-10-17T09:00:00Z", updatedAt: "2026-10-17T09:00:00Z", closedAt: null, steps: [],
    lastEditedStepId: null, parts: null, sourceId: view.sourceId,
    record: { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null },
    ...overrides,
  };
}

function on(extra: Record<string, unknown> = {}) {
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true, compareScope: true }, ...extra };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  on();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1600 });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerLibraryAsk.mockResolvedValue(done(ASK, "ask"));
  api.readerLibraryAskNotes.mockResolvedValue(done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
  api.readerLibraryCompare.mockResolvedValue(done(table()));
  api.readerCompareScope.mockResolvedValue(done(reading(), "scope"));
  api.readerCompareScopeCorrection.mockResolvedValue({ judgmentId: "jl_2" });
  api.readerLibraryJobCancel.mockResolvedValue({ jobId: "ljob_x", kind: "compare", askId: null, state: "cancelled", result: null });
  api.readerKeptComparisons.mockResolvedValue({ marks: [] });
  api.workbenchForSource.mockResolvedValue({ sessions: [], openSessionDays: 30 });
  api.workbenchOpen.mockResolvedValue({ session: wbSession(), resumed: false });
  api.workbenchRefreshImport.mockResolvedValue({ session: wbSession() });
  api.workbenchLeave.mockResolvedValue({ session: wbSession() });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
  window.getSelection()?.removeAllRanges();
});

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function openAskBox(words: string) {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(view.blocks[1].markdown);
  fireEvent.keyDown(window, { key: "F", ctrlKey: true, shiftKey: true });
  const box = await screen.findByRole("textbox", { name: "ask your library" });
  fireEvent.change(box, { target: { value: words } });
  fireEvent.submit(box.closest("form")!);
  const pane = await screen.findByRole("region", { name: "compare your books" });
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  return pane;
}

async function refineWith(pane: HTMLElement, words: string) {
  const shown = within(pane).queryByRole("textbox", { name: "refine this comparison" });
  if (!shown) fireEvent.click(within(pane).getByRole("button", { name: "/ refine" }));
  const box = within(pane).getByRole("textbox", { name: "refine this comparison" });
  fireEvent.change(box, { target: { value: words } });
  fireEvent.submit(box.closest("form")!);
}

it("F1: the payload names the bound workbench session, for every door", () => {
  expect(comparePayload({ door: "selection" })).toHaveProperty("workbenchSessionId", null);
  expect(comparePayload({ door: "refine", askId: "la_1", workbenchSessionId: "wb1" }).workbenchSessionId).toBe("wb1");
});

it("F1: the selection verb while working runs nothing until the learner leaves the problem", async () => {
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(PROSE);
  select(block);
  await screen.findByText(/^selected ·/);
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  await screen.findByRole("region", { name: "workbench" });

  select(block); // the book's own passage, beside the workbench
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "how do my other books treat this?" }));
  // Nothing is paid for behind the hidden comparing pane; a line says how it starts.
  expect((await screen.findByTestId("workbench-compare-waiting")).textContent).toContain(SCOPE_COPY.waitsForWork);
  expect(api.readerLibraryCompare).not.toHaveBeenCalled();
  expect(screen.queryByRole("region", { name: "compare your books" })).toBeNull();

  fireEvent.click(screen.getByRole("button", { name: /leave for now/ }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompare.mock.calls[0][0]).toMatchObject({ door: "selection", extractionId: view.extractionId, workbenchSessionId: null });
  expect(await screen.findByRole("region", { name: "compare your books" })).toBeTruthy();
});

it("F2: removing the last book stops the comparison and keeps the picker, never every book", async () => {
  const pane = await openAskBox("how do Axler and Strang treat eigenvalues");
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.remove("Strang") }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.remove("Axler") }));
  // No request goes out with no books (the server would read it as every book).
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2);
  expect(pane.querySelector("[data-scope-empty]")?.textContent).toContain(SCOPE_COPY.noBooks);
  expect(pane.querySelector("[data-scope-chip]")).toBeNull();
  expect(within(pane).queryByRole("table", { name: "how your sources treat this" })).toBeNull();
  const picker = within(pane).getByRole("combobox", { name: "add a book to compare" });
  fireEvent.change(picker, { target: { value: "lay" } });
  fireEvent.keyDown(picker, { key: "Enter" });
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(3));
  expect(api.readerLibraryCompare.mock.calls[2][0]).toMatchObject({ door: "refine", askId: "la_c", sourceIds: ["src_lay"] });
});

it("F5: compare these books has refine, previous and the tutor over the compared passages, whatever is pinned", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  select(await screen.findByText(PROSE));
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  const pane = await screen.findByRole("region", { name: "ask your library" });
  // An unrelated pin first.
  fireEvent.click((await within(pane).findAllByRole("button", { name: "pin" }))[0]);
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.compareBooks }));
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  expect(within(pane).getByRole("button", { name: "/ refine" })).toBeTruthy();
  api.readerLibraryAskTutor.mockResolvedValue(done(tutorAnswer("from the compared passages"), "tutor"));
  const tutor = within(pane).getByRole("textbox", { name: "your question for the tutor about this comparison" });
  fireEvent.change(tutor, { target: { value: "which is simpler?" } });
  fireEvent.keyDown(tutor, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerLibraryAskTutor).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryAskTutor.mock.calls[0][0]).toEqual({ askId: "la_c", pinnedSpanKeys: ["ext_a:a1", "ext_s:s1"], question: "which is simpler?" });
  expect(await within(pane).findByText("from the compared passages")).toBeTruthy();

  // Refined (add Lay): previous ▸ shows the earlier table.
  api.readerCompareScope.mockResolvedValue(done(reading({ mode: "refine", intent: "books", change: "add", sourceIds: ["src_lay"], judgmentId: "jl_9" }), "scope"));
  await refineWith(pane, "add Lay");
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  fireEvent.click(await within(pane).findByRole("button", { name: SCOPE_COPY.previous }));
  expect(within(pane).getByLabelText(SCOPE_COPY.previousLabel)).toBeTruthy();
});

it("F5: a comparison's tutor uses every block of an anchor of several blocks", async () => {
  api.readerLibraryCompare.mockResolvedValue(done(table({
    rows: [{ ...table().rows[0], sourceId: view.sourceId, sourceTitle: "Matrices", isOpenSource: true, key: "ext_m:m1", spanKeys: ["ext_m:m1", "ext_m:m2"] }, table().rows[1]],
    scope: { door: "selection", question: "q", sourceIds: [], anchorKeys: ["ext_m:m1", "ext_m:m2"] },
  })));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  select(await screen.findByText(PROSE));
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "how do my other books treat this?" }));
  const pane = await screen.findByRole("region", { name: "compare your books" });
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  api.readerLibraryAskTutor.mockResolvedValue(done(tutorAnswer("both"), "tutor"));
  fireEvent.keyDown(within(pane).getByRole("textbox", { name: "your question for the tutor about this comparison" }), { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerLibraryAskTutor).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryAskTutor.mock.calls[0][0].pinnedSpanKeys).toEqual(["ext_m:m1", "ext_m:m2", "ext_s:s1"]);
});

it("F6: changing the books clears (and cancels) the tutor's answer about the earlier comparison", async () => {
  const pane = await openAskBox("how do Axler and Strang treat eigenvalues");
  api.readerLibraryAskTutor.mockResolvedValue(done(tutorAnswer("an answer about Axler and Strang"), "tutor"));
  fireEvent.keyDown(within(pane).getByRole("textbox", { name: "your question for the tutor about this comparison" }), { key: "Enter", ctrlKey: true });
  expect(await within(pane).findByText("an answer about Axler and Strang")).toBeTruthy();
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.remove("Strang") }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  expect(within(pane).queryByText("an answer about Axler and Strang")).toBeNull();

  // A pending answer is cancelled, and never lands under the new comparison.
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  api.readerLibraryAskTutor.mockResolvedValue(pending("tutor", "ljob_tutor_2"));
  let finish: (value: unknown) => void = () => undefined;
  api.readerLibraryJob.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  fireEvent.keyDown(within(pane).getByRole("textbox", { name: "your question for the tutor about this comparison" }), { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerLibraryAskTutor).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(api.readerLibraryJob).toHaveBeenCalled());
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.addBook }));
  const picker = within(pane).getByRole("combobox", { name: "add a book to compare" });
  fireEvent.change(picker, { target: { value: "lay" } });
  fireEvent.keyDown(picker, { key: "Enter" });
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(3));
  expect(api.readerLibraryJobCancel).toHaveBeenCalledWith({ jobId: "ljob_tutor_2" });
  finish(done(tutorAnswer("a late answer about the old books"), "tutor", "ljob_tutor_2"));
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(within(pane).queryByText("a late answer about the old books")).toBeNull();
});

it("F7: the earlier table stays reachable when its replacement fails or is cancelled", async () => {
  const pane = await openAskBox("how do Axler and Strang treat eigenvalues");
  api.readerCompareScope.mockResolvedValue(done(reading({ mode: "refine", intent: "books", change: "add", sourceIds: ["src_lay"], judgmentId: "jl_9" }), "scope"));
  api.readerLibraryCompare.mockRejectedValue(new Error("boom"));
  await refineWith(pane, "add Lay");
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  await within(pane).findByText(/Couldn't compare these books/);
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.previous }));
  const earlier = within(pane).getByLabelText(SCOPE_COPY.previousLabel);
  expect(within(earlier).getAllByRole("row")).toHaveLength(2);
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.hidePrevious }));

  // Cancelled while pending: the earlier table is still one key away.
  api.readerLibraryCompare.mockResolvedValue(pending("compare", "ljob_compare_3"));
  api.readerLibraryJob.mockImplementation(() => new Promise(() => undefined));
  fireEvent.click(within(pane).getByRole("button", { name: /try again/ }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(3));
  expect(within(pane).getByRole("button", { name: SCOPE_COPY.previous })).toBeTruthy(); // reachable while pending
  fireEvent.click(await within(pane).findByRole("button", { name: "cancel" }));
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.previous }));
  expect(within(within(pane).getByLabelText(SCOPE_COPY.previousLabel)).getAllByRole("row")).toHaveLength(2);
});

it("F8: a view past the bound waits for the learner to remove one; nothing is dropped unasked", async () => {
  on({ compareKeep: { library: true, tutor: false, perspectives: true, maxPerspectives: 4 } });
  const pane = await openAskBox("how do Axler and Strang treat eigenvalues");
  for (const [index, view] of ["v1", "v2", "v3", "v4"].entries()) {
    api.readerCompareScope.mockResolvedValue(done(reading({ mode: "refine", intent: "views", change: null, sourceIds: [], judgmentId: `jl_v${index}` }), "scope"));
    await refineWith(pane, view);
    await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(index + 2));
    await within(pane).findByRole("table", { name: "how your sources treat this" });
  }
  expect(api.readerLibraryCompare.mock.calls[4][0].requestedPerspectives).toEqual(["v1", "v2", "v3", "v4"]);
  await refineWith(pane, "v5");
  const limit = await within(pane).findByRole("group", { name: "choose a view to remove" });
  expect(limit.textContent).toContain(SCOPE_COPY.viewLimit(4));
  expect(api.readerLibraryCompare).toHaveBeenCalledTimes(5); // nothing re-run, nothing evicted
  fireEvent.click(within(limit).getByRole("button", { name: SCOPE_COPY.removeView("v2", "v5") }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(6));
  expect(api.readerLibraryCompare.mock.calls[5][0].requestedPerspectives).toEqual(["v1", "v3", "v4", "v5"]);
});

it("F9: after a refinement, an × corrects the refinement's reading and change the ask box's", async () => {
  const pane = await openAskBox("how do Axler and Strang treat eigenvalues");
  api.readerCompareScope.mockResolvedValue(done(reading({ mode: "refine", intent: "books", change: "add", sourceIds: ["src_lay"], judgmentId: "jl_9" }), "scope"));
  await refineWith(pane, "add Lay");
  await waitFor(() => expect(pane.querySelector("[data-scope-chip='src_lay']")).not.toBeNull());
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.remove("Strang") }));
  await waitFor(() => expect(api.readerCompareScopeCorrection).toHaveBeenCalledWith({ judgmentId: "jl_9", sourceIds: ["src_axler", "src_lay"] }));
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.change }));
  await waitFor(() => expect(api.readerCompareScopeCorrection).toHaveBeenLastCalledWith({ judgmentId: "jl_1", sourceIds: null }));
});
