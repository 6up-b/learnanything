// RW4d: syntopic reading, kept (spec §7.8; UX §4.5, §4.10, §3.4, W10; gates
// G18, G43, G54): the three voices in separate bands under the table (the
// sources' quoted lines, LearnLoop's inferred relation labelled with its fine
// label, the learner's own take); nothing is kept until "keep comparison ⇄"
// is pressed, then the table says it is kept as proposals and *remove* undoes
// it; the take says where it goes (never read for gaps); the tutor's
// comparison can be kept only once pressed and shown; perspectives are typed
// above the table; a passage with a kept comparison carries ⇄, which reopens
// the table with no model call; a later ask says "you compared these on …".
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { CompareTableDto, KeptComparisonDto, LibraryAskDto, SourceLibraryCard, SourceToolRequestDto } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { CompareKeep, KEEP_COPY, KeptComparisonView } from "./CompareKeep";
import { CompareTable } from "./LibraryAnswer";
import { CompareKeepContext, type CompareKeepContextValue } from "./compareKeepContext";
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
// The original's pane draws its overlay gutter from the marks it is given (Codex review F10).
vi.mock("../../components/PdfReaderPane", async () => {
  const { forwardRef } = await import("react");
  return {
    PdfReaderPane: forwardRef(function FakePane(props: { marks?: ReadonlyMap<string, ReactNode> | null }, _ref) {
      return (
        <div data-testid="pdf-pane">
          {[...(props.marks?.entries() ?? [])].map(([spanId, node]) => <div key={spanId} data-cue-gutter={spanId}>{node}</div>)}
        </div>
      );
    }),
  };
});
vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn(), convertFileSrc: (path: string) => path }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const other = { sourceId: "src_other", title: "Other Book", canonicalUri: "other.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const BOX = "What do you want to do with this?";
const KEEP_SETTINGS = { library: true, tutor: true, perspectives: true, maxPerspectives: 4 };

const TABLE: CompareTableDto = {
  askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
  rows: [
    { sourceId: view.sourceId, sourceTitle: "Matrices", key: "ext_symmetric:span_spectral_worked", page: 3, isOpenSource: true,
      contributes: [{ line: "a worked case", quote: "diagonalize a symmetric matrix", authorship: "ai" }],
      assumes: [{ line: "one assumes real entries", quote: "Worked: diagonalize", relation: "different_assumptions", otherSourceTitle: "Other Book", authorship: "ai" }], differs: [] },
    { sourceId: "src_other", sourceTitle: "Other Book", key: "ext_other:o1", page: 3, isOpenSource: false,
      contributes: [{ line: "the definition", quote: "equals its transpose", authorship: "ai" }],
      assumes: [{ line: "one assumes real entries", quote: "equals its transpose", relation: "different_assumptions", otherSourceTitle: "Matrices", authorship: "ai" }], differs: [] },
  ],
  alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0, kept: null,
};

function kept(extra: Partial<KeptComparisonDto> = {}): KeptComparisonDto {
  return {
    askId: "la_1", keptAt: "2026-10-03T09:00:00Z",
    objects: [{ id: "so_1", key: "ext_symmetric:span_spectral_worked", objectType: "claim", sourceTitle: "Matrices" },
      { id: "so_2", key: "ext_other:o1", objectType: "definition", sourceTitle: "Other Book" }],
    relations: [{ id: "sor_1", relationType: "refines", fine: "different_assumptions" }],
    takes: [], notKept: 0, status: "proposed", label: "kept as proposals · nothing changes your map until you review them", ...extra,
  };
}

function withKeep(node: ReactNode, value: Partial<CompareKeepContextValue> = {}) {
  const ctx: CompareKeepContextValue = { settings: KEEP_SETTINGS, onChanged: vi.fn(), openSourceId: view.sourceId, ...value };
  return { ctx, node: <CompareKeepContext.Provider value={ctx}>{node}</CompareKeepContext.Provider> };
}

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
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true }, compareKeep: KEEP_SETTINGS };
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
  api.readerLibraryAskNotes.mockResolvedValue(done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
  api.recordSourceOfferShown.mockResolvedValue({ interventionId: null, recorded: false });
  api.readerKeptComparisons.mockResolvedValue({ extractionId: view.extractionId, marks: [], label: "a comparison you kept" });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("shows the three voices apart and keeps nothing until the press (G18, W2)", async () => {
  const { node } = withKeep(<CompareKeep table={TABLE} target={{ askId: "la_1" }} />);
  render(node);
  const inferred = document.querySelector("[data-compare-band='inferred']") as HTMLElement;
  expect(within(inferred).getByText(KEEP_COPY.inferred)).toBeTruthy();
  // The pair's relation once, in LearnLoop's voice, labelled as its inference, with the fine label.
  const voices = inferred.querySelectorAll("[data-voice='model']");
  expect(voices).toHaveLength(1);
  expect(voices[0].textContent).toContain("Matrices ⇄ Other Book · different assumptions");
  expect(voices[0].textContent).toContain(KEEP_COPY.inferredNote);
  const takeBand = document.querySelector("[data-compare-band='take']") as HTMLElement;
  expect(within(takeBand).getByText(KEEP_COPY.take)).toBeTruthy();
  // ⓘ where this goes: the learner's own note, never read for gaps (UX §4.10).
  fireEvent.click(within(takeBand).getByRole("button", { name: KEEP_COPY.whereThisGoes }));
  expect(within(takeBand).getByText(/isn't read for gaps — and never grades you/)).toBeTruthy();
  expect(screen.getByRole("button", { name: KEEP_COPY.keep })).toBeTruthy();
  expect(api.readerLibraryCompareKeep).not.toHaveBeenCalled();
  expect(document.body.textContent?.toLowerCase()).not.toContain("consensus");
});

it("keeps on the press with the take on a pair, then removes (G43)", async () => {
  api.readerLibraryCompareKeep.mockResolvedValue({ askId: "la_1", kept: kept({ takes: [{ id: "t1", keys: ["ext_symmetric:span_spectral_worked", "ext_other:o1"], learnerText: "same rule, two framings" }] }), addedTakes: 1, alreadyKept: false });
  api.readerLibraryCompareRemove.mockResolvedValue({ askId: "la_1", kept: null, removed: true });
  const { ctx, node } = withKeep(<CompareKeep table={TABLE} target={{ askId: "la_1" }} />);
  render(node);
  const focused = document.activeElement;
  fireEvent.change(screen.getByRole("textbox", { name: "your take on these passages" }), { target: { value: "same rule, two framings" } });
  expect((screen.getByRole("combobox", { name: "your take is about" }) as HTMLSelectElement).value)
    .toBe("ext_symmetric:span_spectral_worked|ext_other:o1");
  fireEvent.click(screen.getByRole("button", { name: KEEP_COPY.keep }));
  await screen.findByText(KEEP_COPY.kept);
  expect(api.readerLibraryCompareKeep).toHaveBeenCalledWith({
    askId: "la_1", comparisonId: "scmp_1", takes: [{ text: "same rule, two framings", keys: ["ext_symmetric:span_spectral_worked", "ext_other:o1"] }],
  });
  expect(screen.getByText(KEEP_COPY.proposals)).toBeTruthy();
  // The take is the learner's own voice, apart from the model's.
  expect(screen.getByText("same rule, two framings").closest("[data-voice]")?.getAttribute("data-voice")).toBe("learner");
  expect(ctx.onChanged).toHaveBeenCalledTimes(1);
  expect(document.activeElement).toBe(focused); // nothing moves focus (G54)
  fireEvent.click(screen.getByRole("button", { name: KEEP_COPY.remove }));
  await screen.findByText(KEEP_COPY.removed);
  expect(api.readerLibraryCompareRemove).toHaveBeenCalledWith({ askId: "la_1", comparisonId: "scmp_1" });
  expect(screen.getByRole("button", { name: KEEP_COPY.keep })).toBeTruthy();
  expect(ctx.onChanged).toHaveBeenCalledTimes(2);
});

it("a take on one claim names one passage; a refused keep keeps nothing and says why", async () => {
  api.readerLibraryCompareKeep.mockRejectedValue({ code: "exam_material", message: "Part of this comparison is held out for an exam now, so it isn't kept or shown. Nothing was saved." });
  const { ctx, node } = withKeep(<CompareKeep table={TABLE} target={{ askId: "la_1" }} />);
  render(node);
  fireEvent.change(screen.getByRole("textbox", { name: "your take on these passages" }), { target: { value: "only this one says it" } });
  fireEvent.change(screen.getByRole("combobox", { name: "your take is about" }), { target: { value: "ext_other:o1" } });
  fireEvent.click(screen.getByRole("button", { name: KEEP_COPY.keep }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledWith({ askId: "la_1", comparisonId: "scmp_1", takes: [{ text: "only this one says it", keys: ["ext_other:o1"] }] }));
  expect(await screen.findByText(/held out for an exam/)).toBeTruthy();
  expect(screen.queryByText(KEEP_COPY.kept)).toBeNull();
  expect(ctx.onChanged).not.toHaveBeenCalled();
});

it("a comparison that did not compare (too few sources) or with keep off offers no keep", () => {
  const { node } = withKeep(<CompareKeep table={{ ...TABLE, status: "too_few_sources", comparisonId: null }} target={{ askId: "la_1" }} />);
  const { container, unmount } = render(node);
  expect(container.innerHTML).toBe("");
  unmount();
  const off = render(<CompareKeep table={TABLE} target={{ askId: "la_1" }} />);
  expect(off.container.innerHTML).toBe("");
});

const COMPARE: SourceToolRequestDto = { toolCallId: "stc_c", tool: "compare_sources", reason: "Your books differ here", run: "lazy", dropped: [], arguments: {} };
const compareRun = { version: 1, tool: "compare_sources", policy: "reading", toolCallId: "stc_c", runId: "r2", result: { status: "ok", comparisonId: "scmp_2", sources: [
  { ref: "s1", sourceId: "src_book", sourceTitle: "Linear Algebra Notes", extractionId: "ext_book", spanId: "s7", page: 1, passage: "x", label: "source-authored", contributions: [{ contribution: "states the sign rule", quote: "changes sign" }] },
  { ref: "s2", sourceId: "src_text", sourceTitle: "Matrix Theory", extractionId: "ext_text", spanId: "t3", page: 7, passage: "y", label: "source-authored", contributions: [{ contribution: "gives the factor", quote: "times -1" }] },
], relations: [{ leftRef: "s1", rightRef: "s2", relation: "different_notation", statement: "sign vs factor", leftQuote: "changes sign", rightQuote: "times -1" }],
  missingPerspectives: [] } };

it("the tutor's comparison is kept only after it is pressed and shown (G43, G59)", async () => {
  api.runSourceTool.mockResolvedValue(compareRun);
  api.readerLibraryCompareKeep.mockResolvedValue({ askId: "la_t", kept: kept({ askId: "la_t" }), addedTakes: 0, alreadyKept: false, toolCallId: "stc_c" });
  const { node } = withKeep(<TutorOffers exchangeId="a1" extractionId="ext_text" toolRequests={[COMPARE]} />);
  render(node);
  // Before the press: no comparison ran and nothing can be kept.
  expect(api.runSourceTool).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: KEEP_COPY.keep })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  await screen.findByRole("table", { name: "how your sources treat this" });
  expect(screen.getByText(/Linear Algebra Notes ⇄ Matrix Theory · different notation/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: KEEP_COPY.keep }));
  await screen.findByText(KEEP_COPY.kept);
  expect(api.readerLibraryCompareKeep).toHaveBeenCalledWith({ toolCallId: "stc_c", extractionId: "ext_text", takes: [] });
});

it("the tutor's comparison offers no keep while only the library's keep is on", async () => {
  api.runSourceTool.mockResolvedValue(compareRun);
  const { node } = withKeep(<TutorOffers exchangeId="a1" extractionId="ext_text" toolRequests={[COMPARE]} />,
    { settings: { ...KEEP_SETTINGS, tutor: false } });
  render(node);
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.compare }));
  await screen.findByRole("table", { name: "how your sources treat this" });
  expect(screen.queryByRole("button", { name: KEEP_COPY.keep })).toBeNull();
});

const ASK: LibraryAskDto = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword + meaning", learningObjectIds: ["lo_spectral"], extractionId: view.extractionId,
  anchorSpanIds: ["span_symmetric_prose"],
  hits: [
    { key: "ext_other:o1", extractionId: "ext_other", spanId: "o1", sourceId: "src_other", sourceTitle: "Other Book", section: "Chapter 5", page: 3, text: "A symmetric matrix equals its transpose.", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source", label: "source-authored" },
    { key: "ext_symmetric:span_spectral_worked", extractionId: "ext_symmetric", spanId: "span_spectral_worked", sourceId: view.sourceId, sourceTitle: "Matrices", section: "Chapter 5", page: 3, text: "Worked: diagonalize a symmetric matrix.", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source", label: "source-authored" },
  ],
  groups: { sources: [
    { sourceId: "src_other", sourceTitle: "Other Book", groups: [{ group: "Foundation", keys: ["ext_other:o1"] }] },
    { sourceId: view.sourceId, sourceTitle: "Matrices", groups: [{ group: "Foundation", keys: ["ext_symmetric:span_spectral_worked"] }] },
  ], expansions: [] },
  expansions: [], expandGraph: true, sourceCount: 2, passageCount: 2,
  comparedOn: [{ askId: "la_0", keptAt: "2026-10-03T09:00:00Z", keys: ["ext_other:o1"] }],
};

async function openAnswer() {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  return screen.findByRole("region", { name: "ask your library" });
}

it("perspectives go with the comparison, and the table says which no source covers", async () => {
  api.readerLibraryAsk.mockResolvedValue(done(ASK));
  api.readerLibraryCompare.mockResolvedValue(done({ ...TABLE, requestedPerspectives: ["a geometric view", "an application"], missingPerspectives: ["an application"] }, "compare"));
  const pane = await openAnswer();
  const pins = await within(pane).findAllByRole("button", { name: "pin" });
  fireEvent.click(pins[0]);
  fireEvent.click(pins[1]);
  fireEvent.change(within(pane).getByRole("textbox", { name: "perspectives to compare" }), { target: { value: "a geometric view, an application" } });
  fireEvent.click(within(pane).getByRole("button", { name: /compare pinned \(2\)/ }));
  await within(pane).findByRole("table", { name: "how your sources treat this" });
  expect(api.readerLibraryCompare.mock.calls[0][0]).toEqual({
    askId: "la_1", pinnedSpanKeys: ["ext_other:o1", "ext_symmetric:span_spectral_worked"], openSourceId: view.sourceId,
    requestedPerspectives: ["a geometric view", "an application"],
  });
  expect(within(pane).getByText("not found in your library: an application")).toBeTruthy();
  expect(within(pane).getByRole("button", { name: KEEP_COPY.keep })).toBeTruthy();
});

it("a later ask says when these passages were compared and reopens it with no model call", async () => {
  api.readerLibraryAsk.mockResolvedValue(done(ASK));
  api.readerLibraryCompareReopen.mockResolvedValue({ ...TABLE, askId: "la_0", kept: kept({ askId: "la_0" }), query: "symmetric vs transpose" });
  const pane = await openAnswer();
  const line = await within(pane).findByText(/you compared these on 3 Oct/);
  fireEvent.click(within(line).getByRole("button", { name: KEEP_COPY.reopen }));
  await within(pane).findByText("“symmetric vs transpose”");
  expect(api.readerLibraryCompareReopen).toHaveBeenCalledWith({ askId: "la_0", openSourceId: view.sourceId });
  expect(api.readerLibraryCompare).not.toHaveBeenCalled();
  expect(within(pane).getByText(KEEP_COPY.kept)).toBeTruthy();
});

it("⇄ marks a passage with a kept comparison (the learner's own mark) and reopens its table", async () => {
  const span = view.blocks[1].spanId!;
  api.readerKeptComparisons.mockResolvedValue({ extractionId: view.extractionId, label: "a comparison you kept",
    marks: [{ spanId: span, askIds: ["la_0"], keptAt: "2026-10-03T09:00:00Z", otherSources: ["Other Book"] }] });
  api.readerLibraryCompareReopen.mockResolvedValue({ ...TABLE, askId: "la_0", kept: kept({ askId: "la_0" }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={vi.fn()} />);
  await screen.findByText(view.blocks[1].markdown);
  await waitFor(() => expect(api.readerKeptComparisons).toHaveBeenCalledWith({ extractionId: view.extractionId }));
  const mark = await screen.findByRole("button", { name: /a comparison you kept with Other Book on 3 Oct: reopen it/ });
  expect(mark.textContent).toBe("⇄");
  // The mark sits beside its own passage.
  expect(mark.closest("[data-span-id]")?.getAttribute("data-span-id")).toBe(span);
  const focused = document.activeElement;
  await act(async () => { fireEvent.click(mark); });
  const table = await screen.findByRole("table", { name: "how your sources treat this" });
  expect(within(table).getAllByRole("row")).toHaveLength(2);
  expect(api.readerLibraryCompareReopen).toHaveBeenCalledWith({ askId: "la_0", openSourceId: view.sourceId });
  expect(document.activeElement).toBe(focused);
  expect(screen.getByRole("button", { name: KEEP_COPY.remove })).toBeTruthy();
});

// -- review fixes (reader-rw4d Codex review F2, F3, F8, F9, F10) ---------------------------------

it("a take added to a reopened comparison names that comparison (F2)", async () => {
  api.readerLibraryCompareReopen.mockResolvedValue({ ...TABLE, askId: "la_0", comparisonId: "scmp_old", kept: kept({ askId: "la_0" }) });
  api.readerLibraryCompareKeep.mockResolvedValue({ askId: "la_0", kept: kept({ askId: "la_0", takes: [{ id: "t1", keys: ["ext_other:o1"], learnerText: "later" }] }), addedTakes: 1, alreadyKept: true });
  const { node } = withKeep(<KeptComparisonView askId="la_0" onClose={vi.fn()} Table={CompareTable} />);
  render(node);
  await screen.findByText(KEEP_COPY.kept);
  fireEvent.change(screen.getByRole("textbox", { name: "your take on these passages" }), { target: { value: "later" } });
  fireEvent.change(screen.getByRole("combobox", { name: "your take is about" }), { target: { value: "ext_other:o1" } });
  fireEvent.click(screen.getByRole("button", { name: KEEP_COPY.addTake }));
  await waitFor(() => expect(api.readerLibraryCompareKeep).toHaveBeenCalledWith({ askId: "la_0", comparisonId: "scmp_old", takes: [{ text: "later", keys: ["ext_other:o1"] }] }));
});

it("a kept comparison that retained one source keeps its takes and its remove (F8)", async () => {
  const one: CompareTableDto = { ...TABLE, askId: "la_0", rows: [TABLE.rows[0]],
    kept: kept({ askId: "la_0", objects: [kept().objects[0]], relations: [], takes: [{ id: "t1", keys: ["ext_symmetric:span_spectral_worked"], learnerText: "my note" }] }) };
  api.readerLibraryCompareRemove.mockResolvedValue({ askId: "la_0", kept: null, removed: true });
  const { node } = withKeep(<CompareKeep table={one} target={{ askId: "la_0" }} />);
  render(node);
  expect(screen.getByText("my note").closest("[data-voice]")?.getAttribute("data-voice")).toBe("learner");
  fireEvent.click(screen.getByRole("button", { name: KEEP_COPY.remove }));
  await screen.findByText(KEEP_COPY.removed);
  expect(api.readerLibraryCompareRemove).toHaveBeenCalledWith({ askId: "la_0", comparisonId: "scmp_1" });
  cleanup();
  // A new one-source comparison still offers no keep.
  const fresh = withKeep(<CompareKeep table={{ ...one, kept: null }} target={{ askId: "la_0" }} />);
  const { container } = render(fresh.node);
  expect(container.innerHTML).toBe("");
});

it("keep and reopen work on the library page with no book open (F3)", async () => {
  api.readerSearchSources.mockResolvedValue({ query: "x", deep: false, searchedSources: 1, basis: "keyword", rewritten: null, hits: [] });
  api.readerLibraryAsk.mockResolvedValue(done({ ...ASK, extractionId: null, anchorSpanIds: [] }));
  api.readerLibraryCompare.mockResolvedValue(done(TABLE, "compare"));
  api.readerLibraryCompareReopen.mockResolvedValue({ ...TABLE, askId: "la_0", kept: kept({ askId: "la_0" }), query: "symmetric vs transpose" });
  render(<ReaderScreen onError={vi.fn()} />);
  const search = await screen.findByPlaceholderText("search all sources…");
  fireEvent.change(search, { target: { value: "symmetric matrices" } });
  fireEvent.keyDown(search, { key: "Enter", shiftKey: true });
  const pane = await screen.findByRole("region", { name: "ask your library" });
  // "you compared these on …" reopens a table that can be removed.
  const line = await within(pane).findByText(/you compared these on 3 Oct/);
  fireEvent.click(within(line).getByRole("button", { name: KEEP_COPY.reopen }));
  await within(pane).findByText("“symmetric vs transpose”");
  expect(within(pane).getByRole("button", { name: KEEP_COPY.remove })).toBeTruthy();
  // A new comparison here can be kept.
  const pins = await within(pane).findAllByRole("button", { name: "pin" });
  fireEvent.click(pins[0]);
  fireEvent.click(pins[1]);
  fireEvent.click(within(pane).getByRole("button", { name: /compare pinned \(2\)/ }));
  await waitFor(() => expect(within(pane).getAllByRole("table", { name: "how your sources treat this" }).length).toBeGreaterThan(1));
  expect(within(pane).getByRole("button", { name: KEEP_COPY.keep })).toBeTruthy();
});

it("a passage in two kept comparisons lists both and opens the one picked (F9)", async () => {
  const span = view.blocks[1].spanId!;
  api.readerKeptComparisons.mockResolvedValue({ extractionId: view.extractionId, label: "a comparison you kept",
    marks: [{ spanId: span, askIds: ["la_new", "la_old"], keptAt: "2026-10-05T09:00:00Z", otherSources: ["Other Book"],
      comparisons: [
        { askId: "la_new", keptAt: "2026-10-05T09:00:00Z", query: "the newer question", otherSources: ["Other Book"] },
        { askId: "la_old", keptAt: "2026-10-03T09:00:00Z", query: "the older question", otherSources: ["Third Book"] },
      ] }] });
  api.readerLibraryCompareReopen.mockResolvedValue({ ...TABLE, askId: "la_old", kept: kept({ askId: "la_old" }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={vi.fn()} />);
  await screen.findByText(view.blocks[1].markdown);
  const mark = await screen.findByRole("button", { name: /2 comparisons you kept on this passage: choose one/ });
  await act(async () => { fireEvent.click(mark); });
  const choices = document.querySelector("[data-kept-choices]") as HTMLElement;
  expect(within(choices).getByRole("button", { name: /“the newer question” · with Other Book · 5 Oct/ })).toBeTruthy();
  expect(api.readerLibraryCompareReopen).not.toHaveBeenCalled();
  fireEvent.click(within(choices).getByRole("button", { name: /“the older question” · with Third Book · 3 Oct/ }));
  await screen.findByRole("table", { name: "how your sources treat this" });
  expect(api.readerLibraryCompareReopen).toHaveBeenCalledWith({ askId: "la_old", openSourceId: view.sourceId });
});

it("⇄ marks the original PDF too, beside the cue marks and outside their count (F10)", async () => {
  const span = view.blocks[1].spanId!;
  api.readerPdfView.mockResolvedValue({ version: 1, available: true, fileName: "sha256-x", extractionId: view.extractionId, sourceId: view.sourceId,
    revisionId: "rev", blocks: view.blocks.map((block, page) => ({ spanId: block.spanId, page, bbox: [72, 100, 540, 160], blockType: "Text", text: block.markdown })),
    pageSpans: view.blocks.map((block, page) => ({ spanId: block.spanId, page })), protection: { withheld: false, heldOutSpanIds: [], message: null } });
  api.readerKeptComparisons.mockResolvedValue({ extractionId: view.extractionId, label: "a comparison you kept",
    marks: [{ spanId: span, askIds: ["la_0"], keptAt: "2026-10-03T09:00:00Z", otherSources: ["Other Book"] }] });
  api.readerLibraryCompareReopen.mockResolvedValue({ ...TABLE, askId: "la_0", kept: kept({ askId: "la_0" }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={vi.fn()} />);
  await screen.findByTestId("pdf-pane");
  const mark = await screen.findByRole("button", { name: /a comparison you kept with Other Book on 3 Oct: reopen it/ });
  expect(mark.closest("[data-cue-gutter]")?.getAttribute("data-cue-gutter")).toBe(span);
  expect(document.querySelectorAll("[data-cue-mark]")).toHaveLength(0); // no cue was placed; ⇄ is not one
  await act(async () => { fireEvent.click(mark); });
  await screen.findByRole("table", { name: "how your sources treat this" });
  expect(api.readerLibraryCompareReopen).toHaveBeenCalledWith({ askId: "la_0", openSourceId: view.sourceId });
});
