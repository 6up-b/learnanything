// Reader CA6b: the second pane as a reader of its own (ux_reader_compare_ask_v1
// §6.4 "Everything else works in both panes"; UX §4.1; the CA6 Codex review's
// F1 remainder).
//
// * Selecting in the second pane shows the intent box exactly as in the main
//   pane: typed intentions routed by reader_intent on that pane's reading and
//   passages, each routed action acting on the second pane's book, revision
//   and selection; "how do my other books treat this?" names the OTHER pane's
//   book as the source.
// * The palette there leaves out the open book's own views (work through
//   this, what matters here?).
// * The second pane's margin cues: that book's plan cues, drawn in its gutter
//   as if it were the Reader alone, switchable from their popover.
// * Keys: the box's rules in the pane that has the selection (`?` focuses it,
//   nothing while a text field has focus), Esc closes the box before the pane,
//   F6 still moves focus; selecting in the main pane gives the keys back to it.
// * Main-pane parity while side by side is open, and the switch off.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { CorrespondentsDto, ReaderCueDto, ReaderCuesDto, SideBySideSectionDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { CUE_COPY } from "./cues";
import { SIDE_PANE_COPY } from "./SideBySidePane";
import { SIDE_BY_SIDE_COPY } from "./useSideBySide";

const SPAN_IDS = view.blocks.map((block) => block.spanId!).filter(Boolean);
const BOX = "What do you want to do with this?";

const { api, plans, state } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(),
    readerCorrespondentDismiss: vi.fn(), readerSideBySideSection: vi.fn(), readerCapture: vi.fn(), readerInvokePreset: vi.fn(),
    readerImportExercise: vi.fn(), readerExerciseImportStatus: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(),
    readerIntentOutcome: vi.fn(), readerActiveQuestion: vi.fn(), readerActiveQuestionStatus: vi.fn(), findSources: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
    readerCueAction: vi.fn(), readerCueTap: vi.fn(), readerSetCuePreferences: vi.fn(), readerCueImpressions: vi.fn(),
    getSpanView: vi.fn(), readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(), readerSaveProgress: vi.fn(), readerCompareScope: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(),
  },
  plans: { main: {} as Record<string, unknown>, side: {} as Record<string, unknown> },
  state: { contract: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({
  useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? state.contract : { sources: [source.card, AXLER] }, error: null }),
}));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({
  readGuidePlan: (_sourceId: string, extractionId: string) => Promise.resolve(extractionId === "ext_axler" ? plans.side : plans.main),
  useGuideDiagnosisRefresh: () => undefined,
}));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const LIBRARY = { expandGraph: false, personalizedDefault: false, compare: true, compareScope: true };
const FIGURES = { predictions: false, region: false, revisions: false };
const ON = {
  readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 }, libraryAsk: LIBRARY, figures: FIGURES,
  correspondence: { enabled: true, findSection: true }, sideBySide: { enabled: true },
};
const source = { card: { sourceId: view.sourceId, title: "Strang", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: SPAN_IDS[1] };
const AXLER = { sourceId: "src_axler", title: "Axler", canonicalUri: "axler.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const SIDE_TEXT = "Axler says self-adjoint operators have real eigenvalues.";

const QUIET: CorrespondentsDto = {
  extractionId: view.extractionId, sectionId: "u1", status: "none", learningObjects: [], search: null, checkableLearningObjectIds: ["lo_sym"],
};
const JUDGED: CorrespondentsDto = {
  ...QUIET, status: "judged",
  learningObjects: [{ learningObjectId: "lo_sym", title: "symmetric matrices", sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [{
    extractionId: "ext_axler", sectionId: "ax7a", title: "7.A Self-adjoint operators", sourceId: "src_axler", sourceTitle: "Axler",
    read: false, jump: { extractionId: "ext_axler", sectionId: "ax7a", spanId: "ax7a_1" }, treatment: "develops", by: "judge" as const,
  }] }] }],
};
const SECTION: SideBySideSectionDto = {
  extractionId: "ext_axler", sectionId: "ax7a", sourceId: "src_axler", sourceTitle: "Axler", title: "7.A Self-adjoint operators",
  jumpSpanId: "ax7a_1", page: 200,
  blocks: [
    { spanId: "ax7a_1", blockType: "Text", page: 200, text: SIDE_TEXT },
    { spanId: "ax7a_2", blockType: "Text", page: 200, text: "Proof: take an eigenvector." },
    { spanId: "ax7a_3", blockType: "Text", page: 200, text: "Then compute the inner product." },
  ],
  previous: null, next: null, exposureEventIds: ["x1"], revisionId: "rev_axler",
};

function routed(action: string) {
  const found = intent.palette.flatMap((g) => g.actions).find((a) => a.id === action)!;
  return {
    state: "done", routingId: `r_${action}`, speculative: false, action, status: "routed", reason: null,
    intention: found.intention, group: found.group, label: found.label, effect: found.effect, latencyMs: 900,
  };
}

function cue(spanId: string, rank: number, extra: Partial<ReaderCueDto> = {}): ReaderCueDto {
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: "u1", learningObjectId: "lo", learningObjectTitle: "LO",
    targetId: "err_1", rank, sectionRank: rank, note: "n", because: "b", label: `mark on ${spanId}`,
    earlier: { attemptId: null, practiceItemId: null, prompt: null, answer: null, answeredAt: null, answeredOn: null,
      statement: null, statementPending: false },
    ...extra,
  } as ReaderCueDto;
}
function cues(marks: ReaderCueDto[], extra: Partial<ReaderCuesDto> = {}): ReaderCuesDto {
  return { version: "v1", density: "normal", budgetPerSection: 2, onePerViewport: true, sourceOff: false, marks, withheld: {}, ...extra };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1400 });
  plans.main = {
    sourceId: view.sourceId, extractionId: view.extractionId, personalized: true, selectionBasis: "", goalContext: null,
    sections: [{ id: "u1", label: "6.1 Symmetric matrices", startSpanId: SPAN_IDS[0], endSpanId: SPAN_IDS[SPAN_IDS.length - 1],
      spanIds: SPAN_IDS, question: null, suggestedPassages: [] }],
    pendingDiagnosisAttemptIds: [],
  };
  plans.side = { sourceId: "src_axler", extractionId: "ext_axler", personalized: true, selectionBasis: "", goalContext: null, sections: [], pendingDiagnosisAttemptIds: [] };
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
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerFigures.mockResolvedValue({ figures: [] });
  api.readerFigureRequest.mockResolvedValue({ jobId: "fj1", state: "pending" });
  api.readerFigureJob.mockResolvedValue({ jobId: "fj1", state: "pending" });
  api.readerCapture.mockResolvedValue({ annotationId: "ann_side", anchorStatus: "exact" });
  api.readerInvokePreset.mockResolvedValue({ annotationId: "ann_preset", anchorStatus: "exact", arc: null });
  api.readerImportExercise.mockResolvedValue({ batchId: "batch_side", status: "queued" });
  api.readerExerciseImportStatus.mockResolvedValue({ status: "queued" });
  api.readerActiveQuestion.mockResolvedValue({ anchorSpanIds: ["ax7a_1"], foldedSpanIds: [], batchId: null, question: null, status: "pending" });
  api.findSources.mockResolvedValue({ status: "ok", hits: [] });
  api.readerAsk.mockResolvedValue({ eventId: "q", readerAnswerEventId: "a_side", parentExchangeId: null, answerMd: "Side answer", answerMode: "help_me_reason", citations: [], manifest: {} });
  api.readerLibraryAsk.mockResolvedValue({ jobId: "ljob_ask", kind: "ask", askId: "la_1", state: "pending", result: null });
  api.readerLibraryJob.mockResolvedValue({ jobId: "ljob_ask", kind: "ask", askId: "la_1", state: "pending", result: null });
  api.readerLibraryCompare.mockResolvedValue({ jobId: "ljob_compare", kind: "compare", askId: "la_c", state: "pending", result: null });
  api.readerLibraryJobCancel.mockResolvedValue({ jobId: "ljob_x", kind: "compare", askId: null, state: "cancelled", result: null });
  api.readerSetCuePreferences.mockResolvedValue({ density: "normal" });
  api.readerCueAction.mockResolvedValue({ cueId: "c", action: "opened", eventId: "e", verdict: null, ledgerId: null });
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? JUDGED : QUIET));
  api.readerSideBySideSection.mockResolvedValue({ section: SECTION });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

const pane = () => document.querySelector<HTMLElement>("[data-side-by-side-pane]");
const sideBody = () => pane()!.querySelector<HTMLElement>("[data-sbs-body]")!;
const sideBlock = (spanId = "ax7a_1") => pane()!.querySelector<HTMLElement>(`[data-sbs-span="${spanId}"]`)!;

function select(node: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(node);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(node);
}

async function openSideBySide() {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  await waitFor(() => expect(within(pane()!).getByText(SIDE_TEXT)).toBeTruthy());
}

/** Select the second pane's first passage; the box shows, unfocused (as in the main pane). */
async function sideBox(): Promise<HTMLInputElement> {
  select(sideBlock());
  return (await within(pane()!).findByRole("textbox", { name: BOX })) as HTMLInputElement;
}

/** Type words in the second pane's box and press Enter; the router answers with `action`. */
async function route(action: string, words = "why is this true?") {
  api.readerRouteIntent.mockResolvedValue(routed(action));
  const box = await sideBox();
  fireEvent.change(box, { target: { value: words } });
  await act(async () => { fireEvent.keyDown(box, { key: "Enter" }); });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalled());
  expect(api.readerRouteIntent).toHaveBeenLastCalledWith({
    extractionId: "ext_axler", spanIds: ["ax7a_1"], text: words, quote: SIDE_TEXT, speculative: false, notes: false,
  });
}

const NODES = [{ spanId: "ax7a_1", quote: SIDE_TEXT }];

it("selecting in the second pane shows the intent box there, in the pane's text; the main pane's stays closed", async () => {
  await openSideBySide();
  const box = await sideBox();
  expect(pane()!.contains(box)).toBe(true);
  expect(sideBody().querySelector("[data-intent-box]")).toBeTruthy();
  // The box is the intent box (its routed line, key row and palette), not CA6's one-line bar.
  expect(pane()!.querySelector("[data-sbs-selection]")).toBeNull();
  expect(screen.getAllByRole("textbox", { name: BOX })).toHaveLength(1);
  expect(document.activeElement).not.toBe(box);
});

it("a routed ask acts on the second pane's book: its reading, passage and words; the answer is labelled with that book", async () => {
  await openSideBySide();
  await route("ask_help_me_reason");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalled());
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({
    extractionId: "ext_axler", spanId: "ax7a_1", question: "why is this true?", answerMode: "help_me_reason",
    selectionSpanIds: ["ax7a_1"], selectionQuote: SIDE_TEXT,
  });
  expect(await screen.findByText("about Axler · 7.A Self-adjoint operators", undefined, { timeout: 3000 })).toBeTruthy();
});

it("an empty Enter in the second pane opens the composer on that pane's selection; its question is about that book", async () => {
  await openSideBySide();
  const box = await sideBox();
  await act(async () => { fireEvent.keyDown(box, { key: "Enter" }); });
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
  const about = await screen.findByText(/ASKING ABOUT YOUR SELECTION IN Axler/);
  expect(about).toBeTruthy();
  const composer = document.querySelector<HTMLTextAreaElement>("textarea")!;
  fireEvent.change(composer, { target: { value: "what is an operator?" } });
  fireEvent.keyDown(composer, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalled());
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ extractionId: "ext_axler", spanId: "ax7a_1", question: "what is an operator?", selectionSpanIds: ["ax7a_1"] });
});

it("a routed preset (explain differently) goes to the second pane's book, revision and reading", async () => {
  await openSideBySide();
  await route("alt_explanation", "with a picture");
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalled());
  expect(api.readerInvokePreset.mock.calls[0][0]).toMatchObject({
    preset: "alt_explanation", sourceId: "src_axler", revisionId: "rev_axler", extractionId: "ext_axler", renderViewId: null,
    rawSelection: { nodes: NODES }, learnerText: "with a picture", subjectId: "ax7a_1",
  });
  // The pane re-reads its own marks (its own book's annotations).
  await waitFor(() => expect(api.readerSourceAnnotations.mock.calls.filter((call) => call[0].sourceId === "src_axler").length).toBeGreaterThan(1));
});

it("a routed highlight and an exercise import go to the second pane's book", async () => {
  await openSideBySide();
  await route("highlight", "key fact");
  await waitFor(() => expect(api.readerCapture).toHaveBeenCalled());
  expect(api.readerCapture.mock.calls[0][0]).toMatchObject({
    action: "highlight", sourceId: "src_axler", revisionId: "rev_axler", extractionId: "ext_axler", renderViewId: null,
    rawSelection: { nodes: NODES }, learnerText: "key fact",
  });
  // The palette's exercise import, from the box's Tab.
  const box = await sideBox();
  fireEvent.keyDown(box, { key: "Tab" });
  fireEvent.click(await within(pane()!).findByRole("button", { name: "add this exercise to practice" }));
  await waitFor(() => expect(api.readerImportExercise).toHaveBeenCalled());
  expect(api.readerImportExercise.mock.calls[0][0]).toMatchObject({
    extractionId: "ext_axler", sourceId: "src_axler", revisionId: "rev_axler", renderViewId: null, rawSelection: { nodes: NODES },
  });
});

it("where else is this explained? asks the library anchored on the second pane's reading", async () => {
  await openSideBySide();
  await route("where_else_explained", "other books");
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalled());
  expect(api.readerLibraryAsk.mock.calls[0][0]).toMatchObject({ entry: "where_else_explained", extractionId: "ext_axler", spanIds: ["ax7a_1"], query: "other books" });
});

it("how do my other books treat this? in the second pane is anchored there and names the OTHER pane's book as the source", async () => {
  await openSideBySide();
  await route("compare_books", "compare");
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalled());
  expect(api.readerLibraryCompare.mock.calls[0][0]).toMatchObject({
    door: "selection", extractionId: "ext_axler", anchorSpanIds: ["ax7a_1"], openSourceId: "src_axler", sourceIds: [view.sourceId],
  });
});

it("active reading and another way run on the second pane's reading; the card shows in that pane", async () => {
  await openSideBySide();
  await route("why_step", "why?");
  await waitFor(() => expect(api.readerActiveQuestion).toHaveBeenCalled());
  expect(api.readerActiveQuestion).toHaveBeenCalledWith({ extractionId: "ext_axler", spanIds: ["ax7a_1"], style: "why_step" });
  await waitFor(() => expect(pane()!.querySelector("[data-sbs-card] [data-active-reading='why_step']")).toBeTruthy());
  // "let me try the next step" folds this book's next lines in this pane.
  api.readerActiveQuestion.mockResolvedValue({ anchorSpanIds: ["ax7a_1"], foldedSpanIds: ["ax7a_2", "ax7a_3"], batchId: null, question: null, status: "pending" });
  await route("next_step", "next");
  await waitFor(() => expect(api.readerActiveQuestion).toHaveBeenLastCalledWith({ extractionId: "ext_axler", spanIds: ["ax7a_1"], style: "next_step" }));
  await waitFor(() => expect(sideBlock("ax7a_2").hasAttribute("data-folded")).toBe(true));
  expect(pane()!.querySelector("[data-next-step-fold]")).toBeTruthy();
  await route("another_way", "another view");
  await waitFor(() => expect(api.findSources).toHaveBeenCalled());
  expect(api.findSources.mock.calls[0][0]).toMatchObject({ caller: { kind: "reader", ref: "ext_axler" }, excludeSpanKeys: ["ext_axler:ax7a_1"] });
});

it("make this explorable builds a figure on the second pane's reading", async () => {
  await openSideBySide();
  await route("make_explorable", "explore it");
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalled());
  expect(api.readerFigureRequest).toHaveBeenCalledWith({ extractionId: "ext_axler", spanIds: ["ax7a_1"], region: null });
});

it("the second pane's palette leaves out the open book's own views (work through this, what matters here?)", async () => {
  state.contract = { ...ON, readingPaths: { enabled: true } };
  await openSideBySide();
  const box = await sideBox();
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(pane()!).findByRole("group", { name: "what do you want to do?" });
  const ids = Array.from(palette.querySelectorAll<HTMLElement>("[data-intent-action]")).map((node) => node.dataset.intentAction);
  expect(ids).not.toContain("work_through");
  expect(ids).not.toContain("what_matters_here");
  expect(ids).toEqual(expect.arrayContaining(["ask_answer_directly", "alt_explanation", "compare_books", "where_else_explained", "highlight", "note", "import_exercise"]));
});

it("keys: `?` focuses the second pane's box; Esc closes the box before the pane; F6 still moves focus", async () => {
  await openSideBySide();
  const box = await sideBox();
  sideBody().focus();
  fireEvent.keyDown(sideBody(), { key: "?" });
  expect(document.activeElement).toBe(box);
  // Esc in the box closes the box, not side by side.
  fireEvent.keyDown(box, { key: "Escape" });
  await waitFor(() => expect(within(pane()!).queryByRole("textbox", { name: BOX })).toBeNull());
  expect(pane()).toBeTruthy();
  // F6 moves focus between the panes as before.
  sideBody().focus();
  fireEvent.keyDown(sideBody(), { key: "F6" });
  expect(document.activeElement).toBe(document.querySelector("[data-sbs-main]"));
  // With the box gone, Esc in the pane closes side by side.
  fireEvent.keyDown(sideBody(), { key: "Escape" });
  await waitFor(() => expect(pane()).toBeNull());
});

it("keys: with a text field focused, typing never reaches the second pane's box", async () => {
  await openSideBySide();
  const box = await sideBox();
  const field = document.createElement("input");
  document.body.appendChild(field);
  field.focus();
  fireEvent.keyDown(field, { key: "a" });
  expect(box.value).toBe("");
  expect(document.activeElement).toBe(field);
  field.remove();
  // On the pane's text the first printable key goes into the box.
  sideBody().focus();
  fireEvent.keyDown(sideBody(), { key: "w" });
  expect(box.value).toBe("w");
});

it("selecting in the main pane gives the keys back to it: its box routes on the main book while side by side stays open", async () => {
  await openSideBySide();
  await sideBox();
  // A mouse-down elsewhere closes the second pane's box (as the main pane's).
  const mainBlock = await screen.findByText(view.blocks[1].markdown);
  fireEvent.mouseDown(mainBlock);
  select(mainBlock);
  const box = (await screen.findByRole("textbox", { name: BOX })) as HTMLInputElement;
  expect(pane()!.contains(box)).toBe(false);
  expect(screen.getAllByRole("textbox", { name: BOX })).toHaveLength(1);
  api.readerRouteIntent.mockResolvedValue(routed("compare_books"));
  fireEvent.change(box, { target: { value: "compare" } });
  await act(async () => { fireEvent.keyDown(box, { key: "Enter" }); });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalled());
  expect(api.readerRouteIntent.mock.calls[0][0]).toMatchObject({ extractionId: view.extractionId, spanIds: [SPAN_IDS[1]] });
  // The main pane's verb names the second pane's book (CA6), anchored on the main book.
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalled());
  expect(api.readerLibraryCompare.mock.calls[0][0]).toMatchObject({ extractionId: view.extractionId, openSourceId: view.sourceId, sourceIds: ["src_axler"] });
});

it("cue marks: the second pane draws its own book's marks in its gutter, as if it were the Reader alone, beside the main pane's", async () => {
  // (Not the restored line, which never carries a mark.)
  plans.main = { ...plans.main, cues: cues([cue(SPAN_IDS[2], 0)]) };
  plans.side = { ...plans.side, cues: cues([cue("ax7a_2", 0, { cueId: "cue_side" })]) };
  await openSideBySide();
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='cue_side']")).toBeTruthy());
  // In the second pane's own passage, out of the text column (the gutter), and static.
  expect(sideBlock("ax7a_2").querySelector("[data-cue-mark='cue_side']")).toBeTruthy();
  // The main pane keeps its own mark: each pane is placed on its own.
  expect(document.querySelector(`[data-span-id="${SPAN_IDS[2]}"] [data-cue-mark]`)).toBeTruthy();
});

it("cue marks follow the density setting per pane: none when this book's plan has none (density off), and off for this book from the popover", async () => {
  plans.side = { ...plans.side, cues: cues([], { density: "off" }) };
  await openSideBySide();
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(pane()!.querySelector("[data-cue-mark]")).toBeNull();
  cleanup();
  plans.side = { ...plans.side, cues: cues([cue("ax7a_1", 0, { cueId: "cue_side" })]) };
  await openSideBySide();
  const mark = await waitFor(() => {
    const found = pane()!.querySelector<HTMLElement>("[data-cue-mark='cue_side']");
    expect(found).toBeTruthy();
    return found!;
  });
  fireEvent.click(mark);
  plans.side = { ...plans.side, cues: cues([], { sourceOff: true }) };
  fireEvent.click(await within(pane()!).findByRole("button", { name: CUE_COPY.offBook }));
  await waitFor(() => expect(api.readerSetCuePreferences).toHaveBeenCalledWith({
    extractionId: "ext_axler", sourceId: "src_axler", via: "popover", density: null, sourceOff: true,
  }));
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark]")).toBeNull());
  // The receipt, with its undo, in the pane.
  expect(within(pane()!).getByText(CUE_COPY.receiptBookOff)).toBeTruthy();
});

it("cue marks are not drawn for another reading's plan (only this book's own cues)", async () => {
  plans.side = { ...plans.side, extractionId: "ext_other", cues: cues([cue("ax7a_1", 0, { cueId: "cue_other" })]) };
  await openSideBySide();
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(pane()!.querySelector("[data-cue-mark]")).toBeNull();
});

it("with the intent box off (no reader_intent), the second pane keeps CA6's one-line bar", async () => {
  const { intent: _off, ...withoutIntent } = ON;
  state.contract = withoutIntent;
  await openSideBySide();
  select(sideBlock());
  expect(await within(pane()!).findByRole("button", { name: SIDE_PANE_COPY.highlight })).toBeTruthy();
  expect(within(pane()!).queryByRole("textbox", { name: BOX })).toBeNull();
});

it("switched off (reader.side_by_side.enabled off): no second pane, no second box, and the main pane's box is as before", async () => {
  const { sideBySide: _off, ...withoutSideBySide } = ON;
  state.contract = withoutSideBySide;
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  expect(pane()).toBeNull();
  expect(api.readerSideBySideSection).not.toHaveBeenCalled();
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  const box = (await screen.findByRole("textbox", { name: BOX })) as HTMLInputElement;
  api.readerRouteIntent.mockResolvedValue(routed("compare_books"));
  fireEvent.change(box, { target: { value: "compare" } });
  await act(async () => { fireEvent.keyDown(box, { key: "Enter" }); });
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalled());
  const payload = api.readerLibraryCompare.mock.calls[0][0];
  expect(payload).toMatchObject({ extractionId: view.extractionId, openSourceId: view.sourceId });
  // Every other book, as before CA6 (no source named).
  expect(payload.sourceIds ?? []).toEqual([]);
  expect(screen.queryByText(SIDE_BY_SIDE_COPY.lead)).toBeNull();
});
