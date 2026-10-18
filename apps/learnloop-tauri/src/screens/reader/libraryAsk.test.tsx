// RW4a's library ask on the Reader (spec §7.3; UX §4.5, W9, W10; gates G17,
// G18, G54, G56): "where else is this explained?" from a selection opens the
// comparing posture beside the source (the rail steps aside, the source keeps
// its place); the passages land first and each ◇ note when the organizer is
// done; nothing moves focus when a result lands; pins feed a display-only
// compare table (one row per source, no consensus) and the tutor ("answers
// only from these N passages"); the personalized chip asks again; practice
// this question is find_practice with a Reader caller and a pick is a learner
// pick; Esc leaves; on the library page Shift+Enter asks instead of searching.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { LibraryAskDto, LibraryNotesDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(),
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

function hit(key: string, sourceId: string, sourceTitle: string, text: string, extra: Record<string, unknown> = {}) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId, sourceTitle, section: "Chapter 5", page: 3, text, role: "definition",
    group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source" as const, label: "source-authored", ...extra };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword + meaning", learningObjectIds: ["lo_spectral"], extractionId: view.extractionId,
  anchorSpanIds: ["span_symmetric_prose"],
  hits: [
    hit("ext_other:o1", "src_other", "Other Book", "A symmetric matrix equals its transpose."),
    hit("ext_symmetric:span_spectral_worked", view.sourceId, "Matrices", "Worked: diagonalize a symmetric matrix.", { role: "worked_example", group: "Worked example" }),
    hit("ext_other:o9", "src_other", "Other Book", "Vectors and their span.", { expansion: "prerequisites", group: "Prerequisite", learningObjectIds: ["lo_vectors"] }),
  ],
  groups: {
    sources: [
      { sourceId: "src_other", sourceTitle: "Other Book", groups: [{ group: "Foundation", keys: ["ext_other:o1"] }] },
      { sourceId: view.sourceId, sourceTitle: "Matrices", groups: [{ group: "Worked example", keys: ["ext_symmetric:span_spectral_worked"] }] },
    ],
    expansions: [{ expansion: "prerequisites", label: "Prerequisite", keys: ["ext_other:o9"] }],
  },
  expansions: [{ expansion: "prerequisites", label: "Prerequisite", learningObjects: [{ learningObjectId: "lo_vectors", title: "Vector lists", demonstrated: false, keys: ["ext_other:o9"] }] }],
  expandGraph: true, sourceCount: 2, passageCount: 3,
};

function notes(extra: Partial<LibraryNotesDto> = {}): LibraryNotesDto {
  return {
    askId: "la_1", status: "judged",
    notes: [
      { key: "ext_other:o1", verdict: "contributes", ledgerId: "lac_1", line: "gives the transpose definition", roles: ["definition"], speaksTo: { id: "gap:1", statement: "why eigenvalues are real" }, label: "LearnLoop's model" },
      { key: "ext_symmetric:span_spectral_worked", verdict: "contributes", ledgerId: "lac_2", line: "works one example through", roles: ["worked_example"], speaksTo: null, label: "LearnLoop's model" },
    ],
    order: ["ext_symmetric:span_spectral_worked", "ext_other:o1", "ext_other:o9"], ...extra,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => { resolve = r; });
  return { promise, resolve };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function askFromSelection() {
  const onCheckMe = vi.fn();
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={onCheckMe} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  return { onCheckMe, block };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
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
  api.readerLibraryAsk.mockResolvedValue(ASK);
  api.readerLibraryAskNotes.mockResolvedValue(notes());
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("where else is this explained? opens the comparing posture, passages first, notes when ready (G17)", async () => {
  const late = deferred<LibraryNotesDto>();
  api.readerLibraryAskNotes.mockReturnValue(late.promise);
  await askFromSelection();
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1));
  const request = api.readerLibraryAsk.mock.calls[0][0];
  expect(request.entry).toBe("where_else_explained");
  expect(request.extractionId).toBe(view.extractionId);
  expect(request.spanIds).toEqual([view.blocks[1].spanId]);
  expect(request.personalized).toBe(true);
  const pane = await screen.findByRole("region", { name: "ask your library" });
  // The rail stepped aside; the source is still there.
  expect(screen.queryByRole("complementary", { hidden: true })?.style.display).toBe("none");
  expect(screen.getAllByText(view.blocks[1].markdown).length).toBeGreaterThan(0);
  // The passages show before the notes: excerpts verbatim, the notes pending.
  expect(within(pane).getByText("A symmetric matrix equals its transpose.")).toBeTruthy();
  expect(within(pane).getAllByText(/noting what each contributes/).length).toBeGreaterThan(0);
  expect(within(pane).getByText(/found by keyword \+ meaning · notes by LearnLoop's model/)).toBeTruthy();
  expect(within(pane).getByText(/Prerequisites · from your concept map/)).toBeTruthy();
  expect(within(pane).queryByText("gives the transpose definition")).toBeNull();
  const focused = document.activeElement;
  await act(async () => late.resolve(notes()));
  expect(await within(pane).findByText("gives the transpose definition")).toBeTruthy();
  expect(document.activeElement).toBe(focused); // a landing result never moves focus (G54)
  expect(within(pane).getAllByText(/speaks to your open question about why eigenvalues are real/)).toHaveLength(1);
  // Each note is LearnLoop's model's voice, never the book's.
  const note = within(pane).getByText("gives the transpose definition").closest("[data-voice]");
  expect(note?.getAttribute("data-voice")).toBe("model");
  // No tutor essay until the tutor is asked.
  expect(api.readerLibraryAskTutor).not.toHaveBeenCalled();
});

it("pins two sources and compares them: one row per source, no consensus (G18)", async () => {
  api.readerLibraryCompare.mockResolvedValue({
    askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
    rows: [
      { sourceId: view.sourceId, sourceTitle: "Matrices", key: "ext_symmetric:span_spectral_worked", page: 3, isOpenSource: true,
        contributes: [{ line: "a worked case", quote: "diagonalize a symmetric matrix", authorship: "ai" }], assumes: [], differs: [] },
      { sourceId: "src_other", sourceTitle: "Other Book", key: "ext_other:o1", page: 3, isOpenSource: false,
        contributes: [{ line: "the definition", quote: "equals its transpose", authorship: "ai" }], assumes: [], differs: [] },
    ],
    alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 1,
  });
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  expect(within(pane).getByText(/pin passages from two places to compare them/)).toBeTruthy();
  const pins = within(pane).getAllByRole("button", { name: "pin" });
  fireEvent.click(pins[0]);
  fireEvent.click(pins[1]);
  fireEvent.click(within(pane).getByRole("button", { name: /compare pinned \(2\)/ }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryCompare.mock.calls[0][0]).toEqual({
    askId: "la_1", pinnedSpanKeys: ["ext_other:o1", "ext_symmetric:span_spectral_worked"], openSourceId: view.sourceId,
  });
  const table = await within(pane).findByRole("table", { name: "how your sources treat this" });
  expect(within(table).getAllByRole("row")).toHaveLength(2);
  expect(within(table).getAllByRole("rowheader")[0].textContent).toContain("your passage");
  expect(pane.textContent).toContain("differences kept · each line quotes its own source");
  expect(pane.textContent?.toLowerCase()).not.toMatch(/consensus|summary/);
});

it("the tutor answers only from the pinned passages, when asked", async () => {
  api.readerLibraryAskTutor.mockResolvedValue({
    askId: "la_1", eventId: "q1", answerMd: "From your passages: it equals its transpose.", citations: [{ extractionId: "ext_other", spanId: "o1", label: "Other Book" }],
    groundedKeys: ["ext_other:o1"], droppedPins: [], label: "answers only from this passage", remaining: 5,
  });
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  fireEvent.click(within(pane).getAllByRole("button", { name: "pin" })[0]);
  expect(within(pane).getByText(/answers only from this passage · ↵ ask/)).toBeTruthy();
  const input = within(pane).getByRole("textbox", { name: "your question for the tutor" });
  fireEvent.change(input, { target: { value: "why the transpose?" } });
  fireEvent.submit(input.closest("form")!);
  await waitFor(() => expect(api.readerLibraryAskTutor).toHaveBeenCalledWith({ askId: "la_1", pinnedSpanKeys: ["ext_other:o1"], question: "why the transpose?" }));
  const answer = await within(pane).findByText("From your passages: it equals its transpose.");
  expect(answer.closest("[data-voice]")?.getAttribute("data-voice")).toBe("model");
});

it("the personalized chip asks again with personalization off", async () => {
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  fireEvent.click(within(pane).getByRole("button", { name: "personalized ●" }));
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryAsk.mock.calls[1][0].personalized).toBe(false);
});

it("practice this question proposes through find_practice and a pick is a learner pick", async () => {
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "pp_1", items: [
    { rank: 1, practiceItemId: "pi_1", learningObjectId: "lo_spectral", learningObjectTitle: "Spectral theorem", practiceMode: "short_answer", prompt: "Show a real symmetric matrix has real eigenvalues.", facetIds: [], rationale: null },
  ] });
  const { onCheckMe } = await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  fireEvent.click(within(pane).getByRole("button", { name: /practice this question/ }));
  await waitFor(() => expect(api.findPractice).toHaveBeenCalledTimes(1));
  expect(api.findPractice.mock.calls[0][0]).toMatchObject({ query: "symmetric matrices", learningObjectIds: ["lo_spectral"], caller: { kind: "reader", ref: view.extractionId } });
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledWith(expect.objectContaining({ proposalId: "pp_1", surface: "reader" })));
  fireEvent.click(await within(pane).findByRole("button", { name: /practice this ▸/ }));
  expect(onCheckMe).toHaveBeenCalledWith(expect.objectContaining({ practiceItemId: "pi_1", proposalId: "pp_1" }));
});

it("Ctrl+Shift+F asks about the passage, and Esc goes back to reading", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(view.blocks[1].markdown);
  fireEvent.keyDown(window, { key: "F", ctrlKey: true, shiftKey: true });
  const box = await screen.findByRole("textbox", { name: "ask your library" });
  await waitFor(() => expect(document.activeElement).toBe(box)); // the learner's key: the box takes the cursor
  fireEvent.change(box, { target: { value: "why are eigenvalues real?" } });
  fireEvent.submit(box.closest("form")!);
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1));
  expect(api.readerLibraryAsk.mock.calls[0][0]).toMatchObject({ query: "why are eigenvalues real?", entry: "reader", extractionId: view.extractionId });
  await screen.findByRole("region", { name: "ask your library" });
  fireEvent.keyDown(window, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("region", { name: "ask your library" })).toBeNull());
  expect(screen.getByRole("complementary").style.display).not.toBe("none");
});

it("a capped organizer keeps the passages and names the budget (G56)", async () => {
  api.readerLibraryAskNotes.mockResolvedValue(notes({ status: "capped", reason: "library_ask.max_daily_cost_usd ($1.00)", notes: [], order: [] }));
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  expect(await within(pane).findByText(/Today's library notes budget \(\$1\.00\) is used\. Reading the passages still works\./)).toBeTruthy();
  expect(within(pane).getByText("A symmetric matrix equals its transpose.")).toBeTruthy();
});

it("a failed ask keeps the question and offers try again", async () => {
  api.readerLibraryAsk.mockRejectedValueOnce(new Error("boom"));
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  expect(await within(pane).findByText(/Couldn't look in your books\. Your question is kept\./)).toBeTruthy();
  fireEvent.click(within(pane).getByRole("button", { name: /try again/ }));
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(2));
});

it("Shift+Enter in the library search asks your library instead of searching", async () => {
  render(<ReaderScreen onError={vi.fn()} />);
  const search = await screen.findByPlaceholderText("search all sources…");
  fireEvent.change(search, { target: { value: "symmetric matrices" } });
  api.readerSearchSources.mockResolvedValue({ query: "x", deep: false, searchedSources: 1, basis: "keyword", rewritten: null, hits: [] });
  fireEvent.keyDown(search, { key: "Enter", shiftKey: true });
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledWith(expect.objectContaining({ query: "symmetric matrices", entry: "library_search", extractionId: null })));
  expect(await screen.findByText("A symmetric matrix equals its transpose.")).toBeTruthy();
  expect(api.readerSearchSources).not.toHaveBeenCalledWith(expect.objectContaining({ deep: true }));
});

it("the comparing keys work only inside the answer (UX §3.5)", async () => {
  api.getSpanView.mockResolvedValue({ spanView: { extractionId: "ext_other", spanId: "o1", page: 3, text: "A symmetric matrix equals its transpose.",
    previousSpans: [{ spanId: "o0", blockType: "Text", page: 3, ordinal: 1, text: "Before it.", truncated: false }], nextSpans: [] } });
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  const first = pane.querySelector<HTMLElement>("[data-library-hit]")!;
  first.focus();
  fireEvent.keyDown(first, { key: "p" });
  expect(within(pane).getByRole("button", { name: "pinned ✓" })).toBeTruthy();
  fireEvent.keyDown(first, { key: "ArrowDown" });
  expect(document.activeElement).not.toBe(first);
  fireEvent.keyDown(document.activeElement!, { key: "p" });
  fireEvent.keyDown(document.activeElement!, { key: " " });
  await waitFor(() => expect(api.getSpanView).toHaveBeenCalledWith(expect.objectContaining({ context: "library" })));
  expect(await within(pane).findByText("Before it.")).toBeTruthy();
  // Esc peels the peek first, then the posture.
  fireEvent.keyDown(window, { key: "Escape" });
  await waitFor(() => expect(within(pane).queryByText("Before it.")).toBeNull());
  expect(screen.getByRole("region", { name: "ask your library" })).toBeTruthy();
});
