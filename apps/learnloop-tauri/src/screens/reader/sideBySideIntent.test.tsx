// Reader CA6b: the second pane as a reader of its own (ux_reader_compare_ask_v1
// §6.4 "Everything else works in both panes"; UX §4.1; the CA6 Codex review's
// F1 remainder).
//
// * Selecting in the second pane shows the intent box exactly as in the main
//   pane: typed intentions routed by reader_intent on that pane's reading and
//   passages, each routed action acting on the second pane's book, revision
//   and selection; "how do my other books treat this?" names the OTHER pane's
//   book as the source.
// * The palette there is the main pane's (Codex re-review F7): work through
//   this takes that book to the main pane (side by side one step back on the
//   return stack), and what matters here? shows that book's reading path in
//   the pane.
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
import { encodeReadingPlace, readingPositionKey } from "./useReadingProgress";

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
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), readerSetInquiryStatus: vi.fn(), readerCueDiscovery: vi.fn(),
    readerCueDiscoveryJob: vi.fn(), readerReadingPath: vi.fn(), workbenchForSource: vi.fn(), workbenchOpen: vi.fn(),
    workbenchRefreshImport: vi.fn(), workbenchGet: vi.fn(), workbenchAdmit: vi.fn(), workbenchLeave: vi.fn(),
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
  api.readerReadingPath.mockResolvedValue({
    extractionId: view.extractionId, status: "ready", depth: "learn_to_use_it", depthLabel: "learn to use it", depthOrigin: "guide",
    intent: null, depths: [], goal: null, goalLine: null, sections: [], next: null,
  });
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

async function openSideBySide(props: { onCheckMe?: (request: unknown) => void } = {}) {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} {...(props.onCheckMe ? { onCheckMe: props.onCheckMe } : {})} />);
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

it("the second pane's palette is the main pane's: work through this and what matters here? are offered there too (re-review F7)", async () => {
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
  api.workbenchForSource.mockResolvedValue({ sessions: [], openSessionDays: 30 });
  state.contract = { ...ON, readingPaths: { enabled: true } };
  await openSideBySide();
  const box = await sideBox();
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(pane()!).findByRole("group", { name: "what do you want to do?" });
  const ids = Array.from(palette.querySelectorAll<HTMLElement>("[data-intent-action]")).map((node) => node.dataset.intentAction);
  expect(ids).toEqual(expect.arrayContaining([
    "work_through", "what_matters_here", "ask_answer_directly", "alt_explanation", "compare_books", "where_else_explained", "highlight", "note", "import_exercise",
  ]));
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

it("skim: no marks in the second pane, its box opens only on `?`, and selecting in the main pane takes the keys (one box answers)", async () => {
  plans.side = { ...plans.side, cues: cues([cue("ax7a_2", 0, { cueId: "cue_side" })]) };
  await openSideBySide();
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='cue_side']")).toBeTruthy());
  const [modeSelect] = screen.getAllByRole("combobox");
  fireEvent.keyDown(modeSelect, { key: "Enter" });
  fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
  // Skim is the mute button in both panes.
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark]")).toBeNull());
  select(sideBlock());
  await new Promise((resolve) => setTimeout(resolve, 200));
  expect(within(pane()!).queryByRole("textbox", { name: BOX })).toBeNull();
  // Then a selection in the main pane: only its box answers `?`.
  const mainBlock = await screen.findByText(view.blocks[1].markdown);
  select(mainBlock);
  fireEvent.keyDown(document.body, { key: "?" });
  const boxes = await screen.findAllByRole("textbox", { name: BOX });
  expect(boxes).toHaveLength(1);
  expect(pane()!.contains(boxes[0])).toBe(false);
  // And back: a selection in the second pane takes the keys from the main pane's box.
  fireEvent.keyDown(boxes[0], { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("textbox", { name: BOX })).toBeNull());
  select(mainBlock);
  select(sideBlock());
  fireEvent.keyDown(document.body, { key: "?" });
  const after = await screen.findAllByRole("textbox", { name: BOX });
  expect(after).toHaveLength(1);
  expect(pane()!.contains(after[0])).toBe(true);
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

// ── Codex review (reader-ca6b-second-pane-intent) ─────────────────────────

it("F1: a thread about the second pane's book keeps its commitments and status on that book (source, revision, reading)", async () => {
  api.readerSetInquiryStatus.mockImplementation(async (input: { resolution: string; exchangeId: string }) => ({
    rootExchangeId: input.exchangeId, questionEventId: "q", resolution: input.resolution, previousResolution: "open", openCount: 0,
  }));
  await openSideBySide();
  await route("ask_help_me_reason");
  await screen.findByText("about Axler · 7.A Self-adjoint operators", undefined, { timeout: 3000 });
  fireEvent.click(await screen.findByRole("button", { name: "revisit once" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalled());
  expect(api.readerInvokePreset.mock.calls[0][0]).toMatchObject({
    preset: "test_me_later", sourceId: "src_axler", revisionId: "rev_axler", extractionId: "ext_axler", renderViewId: null,
    rawSelection: { nodes: [{ spanId: "ax7a_1", start: 0, end: 1_000_000 }] }, subjectId: "ax7a_1",
  });
  fireEvent.click(await screen.findByRole("button", { name: "make it something I can do" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(2));
  expect(api.readerInvokePreset.mock.calls[1][0]).toMatchObject({ preset: "help_me_remember", sourceId: "src_axler", extractionId: "ext_axler" });
  // Its status names that reading too (the sidecar refuses it under the open book's).
  fireEvent.click(await screen.findByRole("button", { name: "resolved" }));
  await waitFor(() => expect(api.readerSetInquiryStatus).toHaveBeenCalled());
  expect(api.readerSetInquiryStatus.mock.calls[0][0]).toMatchObject({ extractionId: "ext_axler", exchangeId: "a_side", resolution: "resolved" });
});

it("F1: dismissing a thread about the second pane's book names that book's reading", async () => {
  api.readerSetInquiryStatus.mockImplementation(async (input: { resolution: string; exchangeId: string }) => ({
    rootExchangeId: input.exchangeId, questionEventId: "q", resolution: input.resolution, previousResolution: "open", openCount: 0,
  }));
  await openSideBySide();
  await route("ask_help_me_reason");
  await screen.findByText("about Axler · 7.A Self-adjoint operators", undefined, { timeout: 3000 });
  fireEvent.click(await screen.findByRole("button", { name: "dismiss" }));
  await waitFor(() => expect(api.readerSetInquiryStatus).toHaveBeenCalled());
  expect(api.readerSetInquiryStatus.mock.calls[0][0]).toMatchObject({ extractionId: "ext_axler", exchangeId: "a_side", resolution: "dismissed" });
});

it("F2: after a main-book Ask, an empty Enter in the second pane starts a new thread about that book (no follow-up to the main thread)", async () => {
  api.readerAsk.mockResolvedValueOnce({
    eventId: "q_main", readerAnswerEventId: "a_main", parentExchangeId: null, answerMd: "Main answer", answerMode: "help_me_reason", citations: [], manifest: {},
  });
  await openSideBySide();
  // A main-pane Ask lands (its thread becomes the reply parent).
  const mainBlock = await screen.findByText(view.blocks[1].markdown);
  select(mainBlock);
  api.readerRouteIntent.mockResolvedValue(routed("ask_help_me_reason"));
  const mainBox = (await screen.findByRole("textbox", { name: BOX })) as HTMLInputElement;
  fireEvent.change(mainBox, { target: { value: "main question" } });
  await act(async () => { fireEvent.keyDown(mainBox, { key: "Enter" }); });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ extractionId: view.extractionId });
  await screen.findByText("Main answer");
  // Then an empty Enter in the second pane, and the composer's question.
  const box = await sideBox();
  await act(async () => { fireEvent.keyDown(box, { key: "Enter" }); });
  await screen.findByText(/ASKING ABOUT YOUR SELECTION IN Axler/);
  const composer = screen.getByPlaceholderText("ask about this passage…");
  fireEvent.change(composer, { target: { value: "what is an operator?" } });
  fireEvent.keyDown(composer, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(2));
  expect(api.readerAsk.mock.calls[1][0]).toMatchObject({
    extractionId: "ext_axler", spanId: "ax7a_1", question: "what is an operator?", parentExchangeId: null, selectionSpanIds: ["ax7a_1"],
  });
});

it("F3: try again after a failed second-pane Ask asks the same request (its book, passage, selection and routed answer mode)", async () => {
  api.readerAsk.mockRejectedValueOnce(new Error("boom"));
  await openSideBySide();
  await route("ask_help_me_reason");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  const retry = await screen.findByRole("button", { name: /try again/ });
  fireEvent.click(retry);
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(2));
  const [first, second] = api.readerAsk.mock.calls.map((call) => call[0]);
  expect(first).toMatchObject({ extractionId: "ext_axler", spanId: "ax7a_1", answerMode: "help_me_reason", selectionSpanIds: ["ax7a_1"], selectionQuote: SIDE_TEXT });
  expect(second).toEqual(first);
});

// Reader CA6b (Codex re-review F7, F8): the second book in the main pane.
const AXLER_VIEW = {
  ...view, renderViewId: "rv_axler", extractionId: "ext_axler", revisionId: "rev_axler", sourceId: "src_axler",
  blocks: SECTION.blocks.map((block) => ({ ...view.blocks[1], displayNodeId: `node-${block.spanId}`, spanId: block.spanId, markdown: block.text })),
};
function axlerOpens(): void {
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (input.extractionId === "src_axler" ? AXLER_VIEW : view));
}
function workbenchOn(): void {
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
  api.workbenchForSource.mockResolvedValue({ sessions: [], openSessionDays: 30 });
  api.workbenchOpen.mockImplementation(async () => { throw new Error("not under test"); });
}
const strip = () => screen.getByRole("navigation", { name: "Detour" });

it("F7: work through this in the second pane takes that book to the main pane at the passage and opens the workbench on that selection; side by side is the crumb before it", async () => {
  workbenchOn();
  axlerOpens();
  await openSideBySide();
  await route("work_through", "go through it");
  // The second book opens in the main pane, at the selected passage.
  await waitFor(() => expect(api.readerRenderView).toHaveBeenCalledWith({ extractionId: "src_axler" }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({
    origin: "reader", entry: "work_through", stemMd: SIDE_TEXT, extractionId: "ext_axler", spanIds: ["ax7a_1"],
    importRequest: { extractionId: "ext_axler", sourceId: "src_axler", revisionId: "rev_axler", renderViewId: "rv_axler", rawSelection: { nodes: NODES } },
  });
  // The routing ran (used, not substituted) and side by side is one step back on the return stack.
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_work_through", outcome: "used" }));
  expect(pane()).toBeNull();
  expect(within(strip()).getByText(/side by side with Axler/)).toBeTruthy();
  // Alt+← walks back to it: the open book again, with the second pane beside it.
  await act(async () => { fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true }); });
  await waitFor(() => expect(within(pane()!).getByText(SIDE_TEXT)).toBeTruthy());
  expect(await screen.findByText(view.blocks[1].markdown)).toBeTruthy();
});

it("F7: what matters here? in the second pane shows that book's reading path in the pane; a section opens in the pane, and it closes", async () => {
  state.contract = { ...ON, readingPaths: { enabled: true } };
  api.readerReadingPath.mockImplementation(async (input: { extractionId: string }) => ({
    extractionId: input.extractionId, status: "ready", depth: "learn_to_use_it", depthLabel: "learn to use it", depthOrigin: "guide",
    intent: null, depths: [], goal: null, goalLine: null,
    sections: [{ sectionId: "ax7b", title: "7.B The spectral theorem", startSpanId: "ax7b_1", label: "core", chip: "core",
      reason: "the next idea", reasonBy: "code", override: null, effectiveLabel: "core", exercise: null, words: 300, learningObjectIds: [] }],
    next: null,
  }));
  await openSideBySide();
  await route("what_matters_here", "what matters?");
  // That book's path (its own reading), in the second pane; the main Guide is not moved.
  await waitFor(() => expect(api.readerReadingPath).toHaveBeenCalledWith({ extractionId: "ext_axler" }));
  const card = await waitFor(() => {
    const node = pane()!.querySelector<HTMLElement>("[data-sbs-path]");
    expect(node).toBeTruthy();
    return node!;
  });
  expect(within(card).getByText("WHAT MATTERS IN AXLER")).toBeTruthy();
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_what_matters_here", outcome: "used" }));
  // A section on the path opens in this pane (the path stays).
  api.readerSideBySideSection.mockClear();
  api.readerSideBySideSection.mockImplementation(async (input: { sectionId: string }) => ({
    section: input.sectionId === "ax7b"
      ? { ...SECTION, sectionId: "ax7b", title: "7.B The spectral theorem", jumpSpanId: "ax7b_1", blocks: [{ spanId: "ax7b_1", blockType: "Text", page: 210, text: "The spectral theorem." }] }
      : SECTION,
  }));
  fireEvent.click(within(card).getByRole("button", { name: "7.B The spectral theorem" }));
  await waitFor(() => expect(api.readerSideBySideSection).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax7b" }));
  await waitFor(() => expect(within(pane()!).getByText("The spectral theorem.")).toBeTruthy());
  expect(pane()!.querySelector("[data-sbs-path]")).toBeTruthy();
  fireEvent.click(within(pane()!).getByRole("button", { name: "close" }));
  await waitFor(() => expect(pane()!.querySelector("[data-sbs-path]")).toBeNull());
});

it("F7: a routed action the box does not offer (work through with the workbench off) runs Ask on that pane's book and records the routing as not used", async () => {
  await openSideBySide();
  await route("work_through", "go through it");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalled());
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ extractionId: "ext_axler", spanId: "ax7a_1", question: "go through it" });
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalled());
  expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_work_through", outcome: "discarded" });
  expect(api.readerIntentOutcome).not.toHaveBeenCalledWith({ routingId: "r_work_through", outcome: "used" });
  expect(within(pane()!).getByText("(that isn't on offer here, so this asks)")).toBeTruthy();
  expect(api.readerRenderView).not.toHaveBeenCalledWith({ extractionId: "src_axler" });
});

function discoveredCues(marks: ReaderCueDto[], extra: { heldOut?: ReaderCueDto[]; tryFirst?: boolean; planId?: string } = {}): ReaderCuesDto {
  return cues(marks, {
    discovery: {
      version: "rw3b-discovered-cues-v1", planId: extra.planId ?? "cplan_side", targetsKey: "tk_side", targets: 1, holdoutRate: 0.1,
      valueOrder: true, tryFirst: extra.tryFirst ?? false, heldOut: extra.heldOut ?? [], suppressed: [],
    },
  });
}
const found = (spanId: string, kind: ReaderCueDto["kind"] = "application") =>
  cue(spanId, 0, { cueId: `dcue_${spanId}`, kind, linkId: `plink_${spanId}`, foundBy: "model" } as Partial<ReaderCueDto>);

it("F4: opening the second book runs cue discovery for it (its own open), and its plan is re-read with what was found", async () => {
  plans.side = { ...plans.side, cues: discoveredCues([]) };
  api.readerCueImpressions.mockResolvedValue({ recorded: [] });
  api.readerCueDiscovery.mockImplementation(async () => {
    plans.side = { ...plans.side, cues: discoveredCues([found("ax7a_2")]) };
    return { jobId: "cjob_side", extractionId: "ext_axler", state: "done", result: { status: "done", targetsKey: "tk_side", calls: 1, links: 1 } };
  });
  await openSideBySide();
  // At first the plan has no mark; discovery finds one, and it is drawn in the pane.
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='dcue_ax7a_2']")).toBeTruthy());
  expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1);
  expect(api.readerCueDiscovery.mock.calls[0][0]).toEqual({ extractionId: "ext_axler", sourceOpenId: expect.stringMatching(/^copen_/) });
});

it("F5: the second pane's discovered marks write RW3b receipts in that book's own visit; taps name it; try this step first records its tap", async () => {
  const observed: Array<{ callback: IntersectionObserverCallback; targets: Element[] }> = [];
  class FakeObserver {
    callback: IntersectionObserverCallback;
    targets: Element[] = [];
    constructor(callback: IntersectionObserverCallback) { this.callback = callback; observed.push(this); }
    observe(target: Element) { this.targets.push(target); }
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  plans.side = { ...plans.side, cues: discoveredCues([found("ax7a_1", "try_first")], { heldOut: [found("ax7a_3")], tryFirst: true }) };
  api.readerCueImpressions.mockResolvedValue({ recorded: [] });
  api.readerCueDiscovery.mockResolvedValue({ jobId: "cjob_side", extractionId: "ext_axler", state: "done", result: { status: "done", targetsKey: "tk_side", calls: 0, links: 0 } });
  api.readerCueTap.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "ev", verdict: "same", ledgerId: null, check: null, tryFirst: null,
  }));
  await openSideBySide();
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='dcue_ax7a_1']")).toBeTruthy());
  // The held-out cue is never drawn; both passages are measured in view.
  expect(pane()!.querySelector("[data-cue-mark='dcue_ax7a_3']")).toBeNull();
  await waitFor(() => expect(observed.some((entry) => entry.targets.some((target) => (target as HTMLElement).dataset.sbsSpan))).toBe(true));
  await act(async () => {
    for (const entry of observed) {
      entry.callback(entry.targets.map((target) => ({ isIntersecting: true, intersectionRatio: 1, target })) as unknown as IntersectionObserverEntry[], entry as unknown as IntersectionObserver);
    }
    await new Promise((resolve) => setTimeout(resolve, 900));
  });
  const batches = api.readerCueImpressions.mock.calls.map((call) => call[0] as { extractionId: string; visitId: string; planId: string; entries: unknown[] });
  expect(batches.length).toBeGreaterThan(0);
  for (const batch of batches) expect(batch).toMatchObject({ extractionId: "ext_axler", planId: "cplan_side", visitId: expect.stringMatching(/^cues_/) });
  const sent = batches.flatMap((batch) => batch.entries);
  expect(sent).toContainEqual({ cueId: "dcue_ax7a_1", shown: true });
  expect(sent).toContainEqual({ cueId: "dcue_ax7a_3", shown: false });
  const visitId = batches[0].visitId;
  // "try this step first": RW1b's next-step question on this book, and its tap with the visit and the plan.
  fireEvent.click(pane()!.querySelector<HTMLElement>("[data-cue-mark='dcue_ax7a_1']")!);
  fireEvent.click(await within(pane()!).findByRole("button", { name: /try/i }));
  await waitFor(() => expect(api.readerCueTap).toHaveBeenCalledWith({ extractionId: "ext_axler", cueId: "dcue_ax7a_1", action: "try_first", visitId, planId: "cplan_side" }));
  await waitFor(() => expect(api.readerActiveQuestion).toHaveBeenCalledWith({ extractionId: "ext_axler", spanIds: ["ax7a_1"], style: "next_step" }));
  // An "open" tap carries the same visit (its impression's response).
  fireEvent.click(pane()!.querySelector<HTMLElement>("[data-cue-mark='dcue_ax7a_1']")!);
  fireEvent.click(await within(pane()!).findByRole("button", { name: new RegExp(`^${CUE_COPY.open} ·`) }));
  await waitFor(() => expect(api.readerCueTap).toHaveBeenCalledWith(expect.objectContaining({ cueId: "dcue_ax7a_1", action: "opened", visitId, planId: "cplan_side" })));
});

it("F6: widening the second pane places its marks again (one per screenful), and a scroll never does", async () => {
  const tops: Record<string, number> = { ax7a_1: 0, ax7a_2: 300, ax7a_3: 900 };
  const size = { width: 500 };
  const resized: Array<() => void> = [];
  vi.stubGlobal("ResizeObserver", class {
    callback: () => void;
    constructor(callback: () => void) { this.callback = callback; }
    observe() { resized.push(this.callback); }
    unobserve() {}
    disconnect() {}
  });
  const rect = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    const top = this.dataset.sbsSpan !== undefined ? tops[this.dataset.sbsSpan] ?? 0 : 0;
    return { top, bottom: top + 40, left: 0, right: 500, width: 500, height: 40, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
  Object.defineProperty(HTMLElement.prototype, "clientHeight", { configurable: true, get(this: HTMLElement) { return this.hasAttribute("data-sbs-body") ? 600 : 0; } });
  Object.defineProperty(HTMLElement.prototype, "clientWidth", { configurable: true, get(this: HTMLElement) { return this.hasAttribute("data-sbs-body") ? size.width : 0; } });
  try {
    plans.side = { ...plans.side, cues: cues([cue("ax7a_1", 0, { cueId: "cue_a" }), cue("ax7a_3", 1, { cueId: "cue_b" })]) };
    await openSideBySide();
    // More than a screenful apart: both are drawn.
    await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='cue_b']")).toBeTruthy());
    expect(pane()!.querySelector("[data-cue-mark='cue_a']")).toBeTruthy();
    // A scroll moves nothing (placement never runs on scroll).
    tops.ax7a_3 = 300;
    await act(async () => { fireEvent.scroll(sideBody()); });
    expect(pane()!.querySelector("[data-cue-mark='cue_b']")).toBeTruthy();
    // The splitter widens the pane: its text reflows, the marks now lie within one screenful.
    size.width = 800;
    await act(async () => { for (const callback of resized) callback(); });
    await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='cue_b']")).toBeNull());
    expect(pane()!.querySelector("[data-cue-mark='cue_a']")).toBeTruthy();
  } finally {
    rect.mockRestore();
    // @ts-expect-error -- restore jsdom's own (prototype chain) getters
    delete HTMLElement.prototype.clientHeight;
    // @ts-expect-error -- as above
    delete HTMLElement.prototype.clientWidth;
  }
});

it("F8: check me on a second-pane mark takes that book to the main pane at the mark and hands the shell its card, with the way back to side by side", async () => {
  axlerOpens();
  plans.side = { ...plans.side, cues: cues([cue("ax7a_2", 0, { cueId: "cue_side" })]) };
  api.readerCueAction.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "e", verdict: null, ledgerId: null,
    check: input.action === "check_me" ? { status: "found", practiceItemId: "pi_side", proposalId: "prop_side" } : null,
  }));
  const onCheckMe = vi.fn();
  await openSideBySide({ onCheckMe });
  const mark = await waitFor(() => {
    const node = pane()!.querySelector<HTMLElement>("[data-cue-mark='cue_side']");
    expect(node).toBeTruthy();
    return node!;
  });
  fireEvent.click(mark);
  fireEvent.click(await within(pane()!).findByRole("button", { name: new RegExp(`^${CUE_COPY.checkMe} ·`) }));
  await waitFor(() => expect(onCheckMe).toHaveBeenCalledTimes(1));
  expect(api.readerCueAction).toHaveBeenCalledWith({ extractionId: "ext_axler", cueId: "cue_side", action: "check_me", text: null });
  // That book is open in the main pane first (the shell's check opens there, book hidden).
  expect(api.readerRenderView).toHaveBeenCalledWith({ extractionId: "src_axler" });
  const request = onCheckMe.mock.calls[0][0] as { besideTrail: { entries: Array<{ kind: string; sourceId: string }>; cursor: number } };
  expect(request).toMatchObject({ practiceItemId: "pi_side", proposalId: "prop_side", spanId: "ax7a_2", card: AXLER });
  // The way back the shell keeps: this book now, side by side right before it.
  const trail = request.besideTrail;
  expect(trail.entries[trail.cursor]).toMatchObject({ kind: "source", sourceId: "src_axler" });
  expect(trail.entries[trail.cursor - 1]).toMatchObject({ kind: "side_by_side", sourceId: view.sourceId });
  // In the Reader, Alt+← reopens side by side.
  await act(async () => { fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true }); });
  await waitFor(() => expect(within(pane()!).getByText(SIDE_TEXT)).toBeTruthy());
});

it("F8: the Reader opened again with that way back (after the shell's practice or feedback screen) is on the check's book, and Alt+← reopens side by side", async () => {
  axlerOpens();
  const onCheckMe = vi.fn();
  plans.side = { ...plans.side, cues: cues([cue("ax7a_2", 0, { cueId: "cue_side" })]) };
  api.readerCueAction.mockImplementation(async (input: { cueId: string; action: string }) => ({
    cueId: input.cueId, action: input.action, eventId: "e", verdict: null, ledgerId: null,
    check: input.action === "check_me" ? { status: "found", practiceItemId: "pi_side", proposalId: null } : null,
  }));
  await openSideBySide({ onCheckMe });
  const mark = await waitFor(() => {
    const node = pane()!.querySelector<HTMLElement>("[data-cue-mark='cue_side']");
    expect(node).toBeTruthy();
    return node!;
  });
  fireEvent.click(mark);
  fireEvent.click(await within(pane()!).findByRole("button", { name: new RegExp(`^${CUE_COPY.checkMe} ·`) }));
  await waitFor(() => expect(onCheckMe).toHaveBeenCalledTimes(1));
  const { card, spanId, besideTrail } = onCheckMe.mock.calls[0][0] as { card: SourceLibraryCard; spanId: string; besideTrail: unknown };
  // The shell unmounts the Reader for the check, then opens it again at the passage with the trail.
  cleanup();
  render(<ReaderScreen initialSource={{ card, spanId, besideTrail } as never} onError={vi.fn()} />);
  await screen.findByText(SIDE_TEXT);
  expect(pane()).toBeNull();
  expect(within(strip()).getByText(/side by side with Axler/)).toBeTruthy();
  await act(async () => { fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true }); });
  await waitFor(() => expect(within(pane()!).getByText(SIDE_TEXT)).toBeTruthy());
  expect(await screen.findByText(view.blocks[1].markdown)).toBeTruthy();
});

it("F9: Alt+down / Alt+up move among the focused pane's own marks (each pane its own set)", async () => {
  plans.main = { ...plans.main, cues: cues([cue(SPAN_IDS[2], 0, { cueId: "cue_main" })]) };
  plans.side = { ...plans.side, cues: cues([cue("ax7a_2", 0, { cueId: "cue_side" })]) };
  await openSideBySide();
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='cue_side']")).toBeTruthy());
  await waitFor(() => expect(document.querySelector("[data-cue-mark='cue_main']")).toBeTruthy());
  // Focus in the second pane: its own mark.
  sideBody().focus();
  await act(async () => { fireEvent.keyDown(sideBody(), { key: "ArrowDown", altKey: true }); });
  await waitFor(() => expect(document.activeElement?.getAttribute("data-cue-mark")).toBe("cue_side"));
  await act(async () => { fireEvent.keyDown(document.activeElement!, { key: "ArrowUp", altKey: true }); });
  expect(document.activeElement?.getAttribute("data-cue-mark")).toBe("cue_side");
  // Focus in the main pane: the main pane's mark.
  const main = document.querySelector<HTMLElement>("[data-sbs-main]")!;
  main.focus();
  await act(async () => { fireEvent.keyDown(main, { key: "ArrowDown", altKey: true }); });
  await waitFor(() => expect(document.activeElement?.getAttribute("data-cue-mark")).toBe("cue_main"));
});

it("F9: with marks only in the second pane, Alt+down there moves to them", async () => {
  plans.side = { ...plans.side, cues: cues([cue("ax7a_3", 0, { cueId: "cue_only" })]) };
  await openSideBySide();
  await waitFor(() => expect(pane()!.querySelector("[data-cue-mark='cue_only']")).toBeTruthy());
  sideBody().focus();
  await act(async () => { fireEvent.keyDown(sideBody(), { key: "ArrowDown", altKey: true }); });
  await waitFor(() => expect(document.activeElement?.getAttribute("data-cue-mark")).toBe("cue_only"));
});

// ── Codex re-review (F10, F11) ─────────────────────────────────────────────

it("F10: a failed second-pane Ask is forgotten when another book opens: the same words then ask about the open book", async () => {
  const stored = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => stored.get(key) ?? null, setItem: (key: string, value: string) => void stored.set(key, value),
    removeItem: (key: string) => void stored.delete(key),
  });
  api.readerAsk.mockRejectedValueOnce(new Error("boom"));
  await openSideBySide();
  await route("ask_help_me_reason");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  await screen.findByRole("button", { name: /try again/ });
  // The learner leaves for the library and opens a book there (a source reset),
  // which resumes at its saved place (no selection, no reply parent).
  window.localStorage.setItem(readingPositionKey(view.sourceId), encodeReadingPlace(view.extractionId, SPAN_IDS[1]));
  fireEvent.click(screen.getByRole("button", { name: "← Library" }));
  fireEvent.click(await screen.findByText("Strang"));
  await screen.findAllByText("6.1 Symmetric matrices");
  // The Ask tab, on the reading position (no selection: nothing else forgets the failed request).
  fireEvent.click(screen.getByRole("button", { name: /^ask/ }));
  const composer = await screen.findByPlaceholderText("ask about this passage…");
  fireEvent.change(composer, { target: { value: "why is this true?" } });
  fireEvent.keyDown(composer, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(2));
  const second = api.readerAsk.mock.calls[1][0] as Record<string, unknown>;
  expect(second).toMatchObject({ extractionId: view.extractionId, question: "why is this true?" });
  expect(second.answerMode).not.toBe("help_me_reason");
  expect(second.selectionSpanIds).not.toEqual(["ax7a_1"]);
});

it("F10: a new composer opened in the second pane is not the failed request: its question asks with the new composer's grounding", async () => {
  api.readerAsk.mockRejectedValueOnce(new Error("boom"));
  await openSideBySide();
  await route("ask_help_me_reason");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  await screen.findByRole("button", { name: /try again/ });
  // An empty Enter opens a fresh composer on the pane's selection; the same words are a new question there.
  const box = await sideBox();
  fireEvent.change(box, { target: { value: "" } });
  await act(async () => { fireEvent.keyDown(box, { key: "Enter" }); });
  await screen.findByText(/ASKING ABOUT YOUR SELECTION IN Axler/);
  const composer = screen.getByPlaceholderText("ask about this passage…");
  fireEvent.change(composer, { target: { value: "why is this true?" } });
  fireEvent.keyDown(composer, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(2));
  // Not the routed mode of the failed request: an ordinary question from the composer.
  expect((api.readerAsk.mock.calls[1][0] as Record<string, unknown>).answerMode).not.toBe("help_me_reason");
});

it("F11: closing the second pane and opening the same book again is a fresh discovery (a new open, asked again for unchanged targets)", async () => {
  plans.side = { ...plans.side, cues: discoveredCues([]) };
  api.readerCueImpressions.mockResolvedValue({ recorded: [] });
  api.readerCueDiscovery.mockResolvedValue({
    jobId: "cjob_side", extractionId: "ext_axler", state: "done", result: { status: "done", targetsKey: "tk_side", calls: 0, links: 0 },
  });
  await openSideBySide();
  await waitFor(() => expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1));
  // Close side by side, then open it again on the same book (its targets unchanged).
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  await waitFor(() => expect(pane()).toBeNull());
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  await waitFor(() => expect(within(pane()!).getByText(SIDE_TEXT)).toBeTruthy());
  await waitFor(() => expect(api.readerCueDiscovery).toHaveBeenCalledTimes(2));
  const [first, second] = api.readerCueDiscovery.mock.calls.map((call) => call[0] as { extractionId: string; sourceOpenId: string });
  expect(second.extractionId).toBe("ext_axler");
  expect(second.sourceOpenId).toMatch(/^copen_/);
  expect(second.sourceOpenId).not.toBe(first.sourceOpenId);
});
