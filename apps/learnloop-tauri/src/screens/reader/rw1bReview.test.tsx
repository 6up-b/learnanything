// RW1b's Codex review fixes on the Reader (docs/reviews/reader-rw1b-codex-review.md):
// F4 "change" reverts the routed capture; F6 an undone reconstruction stays
// undone; F8 selection → Tab focuses the palette (arrows and Enter work without
// touching the box); F9 a video transcript folds the next step too; F10 a failed
// verification is not "nothing in your books"; F11 closing "another way" drops a
// late result; F12 every executed routing reports its use and every speculative
// one gets a fate; F13 an answered question can be added to practice.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { ReaderActiveQuestionDto, ReaderRenderViewDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerInvokePreset: vi.fn(), readerCapture: vi.fn(), readerActiveQuestion: vi.fn(), readerActiveQuestionStatus: vi.fn(),
    readerActiveQuestionAction: vi.fn(), readerReconstruct: vi.fn(), readerReconstructUndo: vi.fn(), findSources: vi.fn(),
    readerEscalateAuthoredQuestion: vi.fn(), readerSetMode: vi.fn(), readerWatchPlan: vi.fn(), cancelIngestBatch: vi.fn(),
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

const bookCard = { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const source: { card: SourceLibraryCard; spanId: string | null } = { card: bookCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";
const SELECTED = view.blocks[1];
const NEXT = view.blocks[2];

function routed(action: string, extra: Record<string, unknown> = {}) {
  const found = intent.palette.flatMap((g) => g.actions).find((a) => a.id === action)!;
  return {
    state: "done", routingId: `r_${action}`, speculative: false, action, status: "routed", reason: null,
    intention: found.intention, group: found.group, label: found.label, effect: found.effect, latencyMs: 900, ...extra,
  };
}

function question(over: Partial<ReaderActiveQuestionDto> = {}): ReaderActiveQuestionDto {
  return {
    id: "raq_1", extractionId: view.extractionId, sectionId: "u1", status: "proposed",
    questionMd: "What comes next after this line?", expectedAnswerMd: NEXT.markdown, spanIds: [NEXT.spanId!],
    practiceItemId: null, answeredAt: null, scopeKind: "selection", questionStyle: "next_step",
    anchorSpanIds: [SELECTED.spanId!], responseMd: null, selfCheck: null, answerBasis: "source",
    escalationLearningObjectId: null, missed: false, ...over,
  };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function openBox() {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(SELECTED.markdown);
  select(block);
  const box = await screen.findByRole("textbox", { name: BOX });
  return { block, box: box as HTMLInputElement };
}

async function pickFromPalette(name: string) {
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name }));
}

function deferred<T>() {
  let resolve: (value: T) => void = () => undefined;
  let reject: (error: unknown) => void = () => undefined;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  source.card = bookCard;
  source.spanId = "span_spectral_worked";
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 } };
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
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.readerInvokePreset.mockResolvedValue({ annotationId: "ann_1", anchorStatus: "exact", arc: null });
  api.readerAsk.mockResolvedValue({ eventId: "q", readerAnswerEventId: "a", parentExchangeId: null, answerMd: "Landed answer", answerMode: "help_me_reason", citations: [], manifest: {} });
  api.readerActiveQuestionStatus.mockResolvedValue({ question: null, job: { status: "running" } });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

// -- F8 ------------------------------------------------------------------------------------------

it("F8: selection, then Tab, focuses the palette, so arrows move and Enter is the action's own", async () => {
  await openBox();
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  const buttons = within(palette).getAllByRole("button");
  await waitFor(() => expect(document.activeElement).toBe(buttons[0]));
  fireEvent.keyDown(buttons[0], { key: "ArrowDown" });
  expect(document.activeElement).toBe(buttons[1]);
  const enter = new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true });
  buttons[1].dispatchEvent(enter);
  expect(enter.defaultPrevented).toBe(false); // the button's own press, not an empty Ask
  // The rail did not switch to Ask (no empty Ask ran).
  expect(screen.getByRole("button", { name: "guide" }).getAttribute("aria-pressed")).toBe("true");
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
});

// -- F12 -----------------------------------------------------------------------------------------

it("F12: with speculation off, an Enter routing that runs reports its use", async () => {
  contract.value = { ...contract.value, intent: { ...intent, speculative: false } };
  api.readerRouteIntent.mockResolvedValue(routed("test_me_later"));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "quiz me later" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  expect(api.readerRouteIntent.mock.calls[0][0]).toMatchObject({ speculative: false });
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_test_me_later", outcome: "used" }));
});

it("F12: a speculative routing that fell back to Ask is discarded when the text changes", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerRouteIntent
    .mockResolvedValueOnce({ ...routed("ask_answer_directly"), routingId: "r_spec", speculative: true, status: "fallback", reason: "tied" })
    .mockResolvedValueOnce(routed("connect_it", { routingId: "r_enter" }));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "hmm" } });
  await act(async () => { vi.advanceTimersByTime(650); });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalledTimes(1));
  fireEvent.change(box, { target: { value: "connect this to eigenvalues" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_spec", outcome: "discarded" }));
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_enter", outcome: "used" }));
});

it("F12: a speculative routing still in flight when the text changes is discarded too", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerRouteIntent
    .mockResolvedValueOnce({ state: "pending", routingId: "r_slow", speculative: true })
    .mockResolvedValueOnce(routed("connect_it", { routingId: "r_enter" }));
  // The sidecar's read waits (up to 250 ms) before answering "still pending".
  api.readerIntentRouting.mockImplementation(() => new Promise((resolve) => {
    setTimeout(() => resolve({ state: "pending", routingId: "r_slow", speculative: true }), 100);
  }));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "hmm" } });
  await act(async () => { vi.advanceTimersByTime(650); });
  await waitFor(() => expect(api.readerRouteIntent).toHaveBeenCalledTimes(1));
  fireEvent.change(box, { target: { value: "connect this to eigenvalues" } });
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_slow", outcome: "discarded" }));
});

// -- F4 ------------------------------------------------------------------------------------------

it("F4: change after a routed capture reverts it before the replacement runs", async () => {
  api.readerRouteIntent.mockResolvedValue(routed("test_me_later"));
  const { box } = await openBox();
  fireEvent.change(box, { target: { value: "quiz me later" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
  fireEvent.click(await screen.findByRole("button", { name: "change" }));
  await waitFor(() => expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_test_me_later", outcome: "reverted", annotationId: "ann_1" }));
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  api.readerCapture.mockResolvedValue({ annotationId: "ann_2", anchorStatus: "exact" });
  fireEvent.click(within(palette).getByRole("button", { name: "highlight" }));
  await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
  expect(api.readerIntentOutcome).toHaveBeenCalledWith({ routingId: "r_test_me_later", outcome: "corrected", action: "highlight" });
});

// -- F10 / F11 -----------------------------------------------------------------------------------

it("F10: a verification that failed is not an empty result, and it can be tried again", async () => {
  api.findSources.mockResolvedValue({ intent: "alternative", status: "unverified: unavailable", hits: [], manifest: {} });
  await openBox();
  await pickFromPalette("another way to see this");
  expect(await screen.findByText(/Couldn't reach LearnLoop's model/)).toBeTruthy();
  expect(screen.queryByText("Nothing in your books treats this differently yet.")).toBeNull();
  api.findSources.mockResolvedValue({ intent: "alternative", status: "ok", hits: [], manifest: {} });
  fireEvent.click(screen.getByRole("button", { name: /try again/ }));
  expect(await screen.findByText("Nothing in your books treats this differently yet.")).toBeTruthy();
  expect(api.findSources).toHaveBeenCalledTimes(2);
});

it("F10: a refused verification says it couldn't check", async () => {
  api.findSources.mockResolvedValue({ intent: "alternative", status: "unverified: failed", hits: [], manifest: {} });
  await openBox();
  await pickFromPalette("another way to see this");
  expect(await screen.findByText(/Couldn't check what your books say about this/)).toBeTruthy();
  expect(screen.queryByText("Nothing in your books treats this differently yet.")).toBeNull();
});

it("F11: a late result of a closed 'another way' does not reopen it", async () => {
  const late = deferred<unknown>();
  api.findSources.mockReturnValue(late.promise);
  await openBox();
  await pickFromPalette("another way to see this");
  const card = await screen.findByRole("region", { name: "another way to see this" });
  fireEvent.click(within(card).getByRole("button", { name: "close" }));
  expect(screen.queryByLabelText("another way to see this")).toBeNull();
  await act(async () => { late.resolve({ intent: "alternative", status: "ok", hits: [{ extractionId: "x", spanId: "y", text: "Late passage", sourceId: "s2" }], manifest: {} }); });
  await act(async () => { await Promise.resolve(); });
  expect(screen.queryByLabelText("another way to see this")).toBeNull();
  expect(screen.queryByText("Late passage")).toBeNull();
});

it("F11: a late failure of a cancelled 'another way' does not reopen it", async () => {
  const late = deferred<unknown>();
  api.findSources.mockReturnValue(late.promise);
  await openBox();
  await pickFromPalette("another way to see this");
  fireEvent.click(await screen.findByRole("button", { name: "cancel" }));
  await act(async () => { late.reject(new Error("boom")); });
  await act(async () => { await Promise.resolve(); });
  expect(screen.queryByLabelText("another way to see this")).toBeNull();
});

// -- F6 / F13 ------------------------------------------------------------------------------------

it("F6: reopening an undone reconstruction says it is undone and schedules nothing", async () => {
  api.readerActiveQuestion.mockResolvedValue({
    style: "reconstruct", anchorSpanIds: [SELECTED.spanId], foldedSpanIds: [], status: "exists", batchId: null, message: null,
    question: question({ questionStyle: "reconstruct", status: "escalated", practiceItemId: "pi_reader_sel_x",
      reconstruct: { commitmentId: "cmt_1", practiceItemId: "pi_reader_sel_x", disposition: "stopped" } }),
  });
  await openBox();
  await pickFromPalette("reconstruct this later");
  expect(await screen.findByText(/You undid this reconstruction earlier/)).toBeTruthy();
  expect(screen.queryByText(/Added to your practice/)).toBeNull();
  expect(api.readerReconstruct).not.toHaveBeenCalled();
});

it("F13: an answered question offers 'add to practice', which escalates it once", async () => {
  api.readerActiveQuestion.mockResolvedValue({
    style: "why_step", anchorSpanIds: [SELECTED.spanId], foldedSpanIds: [], status: "exists", batchId: null, message: null,
    question: question({ questionStyle: "why_step", escalationLearningObjectId: "lo_spectral" }),
  });
  api.readerActiveQuestionAction.mockResolvedValue({
    question: question({ questionStyle: "why_step", escalationLearningObjectId: "lo_spectral", status: "answered", responseMd: "because", answeredAt: "t" }),
    formativeJobId: null,
  });
  api.readerEscalateAuthoredQuestion.mockResolvedValue({ practiceItemId: "pi_reader_sel_1", question: {} });
  await openBox();
  await pickFromPalette("why does this step work?");
  expect(screen.queryByRole("button", { name: "add to practice" })).toBeNull(); // not before an answer
  fireEvent.change(await screen.findByRole("textbox", { name: "Your answer" }), { target: { value: "because" } });
  fireEvent.click(screen.getByRole("button", { name: /compare with the book/ }));
  fireEvent.click(await screen.findByRole("button", { name: "add to practice" }));
  await waitFor(() => expect(api.readerEscalateAuthoredQuestion).toHaveBeenCalledWith({ questionId: "raq_1", learningObjectId: "lo_spectral" }));
  expect(await screen.findByText(/Added to your practice/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "add to practice" })).toBeNull();
  expect(api.readerEscalateAuthoredQuestion).toHaveBeenCalledTimes(1);
});

// -- F9 ------------------------------------------------------------------------------------------

it("F9: a video transcript folds the next step while the learner tries it", async () => {
  const transcript: ReaderRenderViewDto = {
    ...view,
    sourceId: "src_video",
    extractionId: "ext_video",
    blocks: [
      ["t1", "t=0.0-4.0", "A mixture picks a component, then samples from it."],
      ["t2", "t=4.0-9.0", "So the density is weighted by the chance of each component."],
    ].map(([spanId, locator, text]) => ({
      displayNodeId: `node-${spanId}`, spanId, blockType: "Caption", extractorBlockId: locator, markdown: text,
      sanitized: false, katexNodes: [], assets: [], health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
    })) as ReaderRenderViewDto["blocks"],
  };
  source.card = { ...bookCard, sourceId: "src_video", canonicalUri: "https://www.youtube.com/watch?v=hvjkcmzfix8" } as SourceLibraryCard;
  source.spanId = null;
  api.readerRenderView.mockResolvedValue(transcript);
  api.readerWatchPlan.mockResolvedValue({ videoId: "hvjkcmzfix8", embedUrl: "https://www.youtube-nocookie.com/embed/x", pausePoints: [] });
  api.readerActiveQuestion.mockResolvedValue({
    style: "next_step", anchorSpanIds: ["t1"], foldedSpanIds: ["t2"], status: "queued", batchId: "batch_1", message: null, question: null,
  });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const cue = await screen.findByText("A mixture picks a component, then samples from it.");
  expect(cue.closest("[data-transcript-scroller]")).not.toBeNull();
  select(cue);
  await screen.findByRole("textbox", { name: BOX });
  await pickFromPalette("let me try the next step");
  await waitFor(() => expect(api.readerActiveQuestion).toHaveBeenCalledWith({ extractionId: "ext_video", spanIds: ["t1"], style: "next_step" }));
  expect(await screen.findByText(/the next line is folded while you try/)).toBeTruthy();
  expect(screen.queryByText("So the density is weighted by the chance of each component.")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "show" }));
  expect(await screen.findByText("So the density is weighted by the chance of each component.")).toBeTruthy();
});
