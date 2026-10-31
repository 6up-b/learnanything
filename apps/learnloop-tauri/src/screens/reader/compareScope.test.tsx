// Reader CA3: compare from anywhere (ux_reader_compare_ask_v1 §4, X1/X2; K12, K16).
//
// * The selection verb (Transfer's "how do my other books treat this?") opens
//   the comparing posture with a comparison anchored on the selection, no pins.
// * The ask box reads named books first (reader.compare_scope), shows them as
//   chips and compares at once; a library question is today's answer; a
//   reading that failed offers comparing all the books on the words.
// * The chips: × and "+ add a book" re-run the same request with those books
//   (and record the learner's change); "change" reopens the box with the words.
// * The refine box (`/`): other books change the chips; "previous ▸" shows the
//   earlier table.
// * A library answer's "compare these books ▸" compares its books, no pins.
// * The tutor's offer opens the same comparison beside the book.
// * One payload shape for every door; nothing takes focus or animates; off
//   (no libraryAsk.compareScope), every door is today's.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as baseIntent } from "../../fixtures/readerIntentContract";
import type { CompareScopeReadingDto, CompareTableDto, LibraryAskDto, ReaderIntentContractDto, SourceLibraryCard, SourceToolRequestDto } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { TutorOffers, createTutorOfferStore, OFFER_COPY } from "./TutorOffers";
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
const BOX = "What do you want to do with this?";
const LIBRARY = [{ sourceId: "src_axler", title: "Axler" }, { sourceId: "src_strang", title: "Strang" }, { sourceId: "src_lay", title: "Lay" }];

/** The intent contract as the sidecar sends it while CA3 is on (the fixture), and while off. */
const intent: ReaderIntentContractDto = baseIntent;
const intentOff: ReaderIntentContractDto = {
  ...baseIntent,
  palette: baseIntent.palette.map((group) => ({ ...group, actions: group.actions.filter((action) => action.effect.kind !== "compare") })),
};

function done<T>(result: T, kind = "compare") {
  return { jobId: `ljob_${kind}`, kind, askId: "la_c", state: "done" as const, result };
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
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
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
}

const KEYS = Object.keys(comparePayload({ door: "selection" })).sort();

it("the selection verb compares the selection with the other books, no pins (X1)", async () => {
  api.readerLibraryCompare.mockResolvedValue(done(table({
    rows: [{ ...table().rows[0], sourceId: view.sourceId, sourceTitle: "Matrices", isOpenSource: true }, table().rows[1]],
    scope: { door: "selection", question: "q", sourceIds: [], anchorKeys: ["x"] },
  })));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  const transfer = within(palette).getAllByRole("button").map((button) => button.textContent);
  expect(transfer.indexOf("how do my other books treat this?")).toBe(transfer.indexOf("where else is this explained?") + 1);
  fireEvent.click(within(palette).getByRole("button", { name: "how do my other books treat this?" }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  const payload = api.readerLibraryCompare.mock.calls[0][0];
  expect(Object.keys(payload).sort()).toEqual(KEYS);
  expect(payload).toMatchObject({ door: "selection", askId: null, pinnedSpanKeys: [], sourceIds: [], extractionId: view.extractionId,
    openSourceId: view.sourceId });
  expect(payload.anchorSpanIds.length).toBeGreaterThan(0);
  expect(api.readerCompareScope).not.toHaveBeenCalled(); // the door knows its scope: no reading is paid for
  const pane = await screen.findByRole("region", { name: "compare your books" });
  const line = pane.querySelector("[data-scope-line]") as HTMLElement;
  expect(line.textContent).toContain(SCOPE_COPY.yourPassage);
  expect(line.textContent).toContain("Strang"); // the books it found, by name
  expect(line.textContent).not.toMatch(/\d+ (books|sources)/); // names, not counts (C4)
  expect(await within(pane).findByRole("table", { name: "how your sources treat this" })).toBeTruthy();
  expect(pane.contains(document.activeElement)).toBe(false); // a landing takes no focus
});

it("the ask box reads named books, shows them as chips and compares at once (X2)", async () => {
  api.readerCompareScope.mockResolvedValue(done(reading({ unmatched: "Hoffman" }), "scope"));
  await openAskBox("how do Axler, Strang and Hoffman treat eigenvalues");
  await waitFor(() => expect(api.readerCompareScope).toHaveBeenCalledWith({
    text: "how do Axler, Strang and Hoffman treat eigenvalues", mode: "ask", extractionId: view.extractionId }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  const payload = api.readerLibraryCompare.mock.calls[0][0];
  expect(Object.keys(payload).sort()).toEqual(KEYS);
  expect(payload).toMatchObject({ door: "ask_box", question: "eigenvalues", sourceIds: ["src_axler", "src_strang"], askId: null });
  expect(api.readerLibraryAsk).not.toHaveBeenCalled();
  const pane = await screen.findByRole("region", { name: "compare your books" });
  expect(pane.querySelector("[data-scope-chip='src_axler']")?.textContent).toContain("Axler");
  expect(pane.textContent).toContain("on: eigenvalues");
  expect(pane.textContent).toContain(SCOPE_COPY.notInLibrary("Hoffman"));
});

it("× and + add a book re-run the same request with those books, and say the learner changed it", async () => {
  await openAskBox("how do Axler and Strang treat eigenvalues");
  const pane = await screen.findByRole("region", { name: "compare your books" });
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.remove("Strang") }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompare.mock.calls[1][0]).toMatchObject({ door: "refine", askId: "la_c", sourceIds: ["src_axler"] });
  expect(Object.keys(api.readerLibraryCompare.mock.calls[1][0]).sort()).toEqual(KEYS);
  expect(api.readerCompareScopeCorrection).toHaveBeenCalledWith({ judgmentId: "jl_1", sourceIds: ["src_axler"] });
  fireEvent.click(await within(pane).findByRole("button", { name: SCOPE_COPY.addBook }));
  const picker = within(pane).getByRole("combobox", { name: "add a book to compare" });
  expect(document.activeElement).toBe(picker); // the learner's press: the picker takes the cursor
  fireEvent.change(picker, { target: { value: "la" } });
  expect(within(pane).getAllByRole("option").map((option) => option.textContent)).toEqual(["Lay"]);
  fireEvent.keyDown(picker, { key: "Enter" });
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(3));
  expect(api.readerLibraryCompare.mock.calls[2][0]).toMatchObject({ door: "refine", sourceIds: ["src_axler", "src_lay"] });
});

it("change reopens the ask box with the words kept", async () => {
  await openAskBox("how do Axler and Strang treat eigenvalues");
  const pane = await screen.findByRole("region", { name: "compare your books" });
  fireEvent.click(within(pane).getByRole("button", { name: SCOPE_COPY.change }));
  const box = await screen.findByRole("textbox", { name: "ask your library" });
  expect((box as HTMLInputElement).value).toBe("how do Axler and Strang treat eigenvalues");
  expect(api.readerCompareScopeCorrection).toHaveBeenCalledWith({ judgmentId: "jl_1", sourceIds: null });
});

it("the refine box adds a book in words, and previous ▸ shows the earlier table", async () => {
  await openAskBox("how do Axler and Strang treat eigenvalues");
  const pane = await screen.findByRole("region", { name: "compare your books" });
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  api.readerCompareScope.mockResolvedValue(done(reading({ mode: "refine", intent: "books", change: "add", sourceIds: ["src_lay"], judgmentId: "jl_9" }), "scope"));
  api.readerLibraryCompare.mockResolvedValue(done(table({ rows: [...table().rows, { ...table().rows[0], sourceId: "src_lay", sourceTitle: "Lay", key: "ext_l:l1" }] })));
  fireEvent.keyDown(within(pane).getByRole("table", { name: "how your sources treat this" }), { key: "/" });
  const box = within(pane).getByRole("textbox", { name: "refine this comparison" });
  expect(document.activeElement).toBe(box);
  fireEvent.change(box, { target: { value: "add Lay" } });
  fireEvent.submit(box.closest("form")!);
  await waitFor(() => expect(api.readerCompareScope).toHaveBeenLastCalledWith({
    text: "add Lay", mode: "refine", extractionId: view.extractionId, currentSourceIds: ["src_axler", "src_strang"] }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryCompare.mock.calls[1][0]).toMatchObject({ door: "refine", askId: "la_c", sourceIds: ["src_axler", "src_strang", "src_lay"] });
  await waitFor(() => expect(pane.querySelector("[data-scope-chip='src_lay']")).not.toBeNull());
  fireEvent.click(await within(pane).findByRole("button", { name: SCOPE_COPY.previous }));
  const earlier = within(pane).getByLabelText(SCOPE_COPY.previousLabel);
  expect(within(earlier).getAllByRole("row")).toHaveLength(2);
  expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2); // shown again, never paid for twice
});

it("a library question gets today's answer, and a failed reading offers comparing every book", async () => {
  api.readerCompareScope.mockResolvedValue(done(reading({ intent: "ask", sourceIds: [], books: [] }), "scope"));
  await openAskBox("what is an eigenvalue?");
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompare).not.toHaveBeenCalled();
  cleanup();
  api.readerCompareScope.mockResolvedValue(done(reading({ status: "fallback", reason: "unavailable", intent: null, sourceIds: [], books: [] }), "scope"));
  await openAskBox("how do Axler and Strang treat eigenvalues");
  const pane = await screen.findByRole("region", { name: "ask your library" });
  const offer = await within(pane).findByRole("button", { name: SCOPE_COPY.compareAll("how do Axler and Strang treat eigenvalues") });
  expect(api.readerLibraryCompare).not.toHaveBeenCalled(); // nothing paid for until pressed
  fireEvent.click(offer);
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompare.mock.calls[0][0]).toMatchObject({ door: "ask_box", question: "how do Axler and Strang treat eigenvalues", sourceIds: [] });
});

it("a library answer compares its books with no pins", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  const pane = await screen.findByRole("region", { name: "ask your library" });
  fireEvent.click(await within(pane).findByRole("button", { name: SCOPE_COPY.compareBooks }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  const payload = api.readerLibraryCompare.mock.calls[0][0];
  expect(Object.keys(payload).sort()).toEqual(KEYS);
  expect(payload).toMatchObject({ door: "library_answer", askId: "la_1", pinnedSpanKeys: [], sourceIds: ["src_other", view.sourceId] });
  expect(pane.textContent).not.toContain("pin passages from two places");
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  expect(pane.querySelector("[data-scope-chip='src_other']")).not.toBeNull();
});

it("the tutor's offer opens the same comparison beside the book; without it, today's inline table", async () => {
  const request: SourceToolRequestDto = { toolCallId: "stc_c", tool: "compare_sources", reason: "two routes", run: "lazy", dropped: [],
    arguments: { query: "why eigenvalues exist", facetIds: [] } };
  const onCompare = vi.fn();
  render(<TutorOffers exchangeId="a1" extractionId="ext_text" toolRequests={[request]} store={createTutorOfferStore()} onCompare={onCompare} />);
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  expect(onCompare).toHaveBeenCalledWith({ question: "why eigenvalues exist", toolCallId: "stc_c" });
  expect(api.runSourceTool).not.toHaveBeenCalled();
  expect(await screen.findByRole("button", { name: OFFER_COPY.compareOpened })).toBeTruthy();
});

it("switched off, the ask box and the palette are today's", async () => {
  on({ libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true }, intent: intentOff });
  await openAskBox("how do Axler and Strang treat eigenvalues");
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1));
  expect(api.readerCompareScope).not.toHaveBeenCalled();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("A symmetric matrix equals its transpose.");
  expect(within(pane).queryByRole("button", { name: SCOPE_COPY.compareBooks })).toBeNull();
  expect(within(pane).getByText(/pin passages from two places to compare them/)).toBeTruthy();
});

it("switched off, the selection's palette has no comparison verb", async () => {
  on({ libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true }, intent: intentOff });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  select(await screen.findByText(view.blocks[1].markdown));
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  expect(within(palette).queryByRole("button", { name: "how do my other books treat this?" })).toBeNull();
  expect(within(palette).getByRole("button", { name: "where else is this explained?" })).toBeTruthy();
});

it("every door builds the same payload keys (C1)", () => {
  const doors = [
    comparePayload({ door: "selection", question: "q", extractionId: "e", anchorSpanIds: ["s"] }),
    comparePayload({ door: "ask_box", question: "q", sourceIds: ["a", "b"] }),
    comparePayload({ door: "tutor_offer", question: "q", extractionId: "e", anchorSpanIds: ["s"], toolCallId: "t" }),
    comparePayload({ door: "library_answer", askId: "la_1", sourceIds: ["a", "b"] }),
    comparePayload({ door: "pins", askId: "la_1", pinnedSpanKeys: ["x:1", "y:2"] }),
  ];
  for (const payload of doors) expect(Object.keys(payload).sort()).toEqual(KEYS);
  expect(doors.every((payload) => !("policy" in payload))).toBe(true); // the server derives the policy
});
