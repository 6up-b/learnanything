// RW1b's active reading on the Reader (spec §4.2; UX §4.3, S5; gates G4, G51):
// "let me try the next step" folds the book's following blocks under a dotted
// rule at once (before the question is written), with "show" one press away;
// the learner writes their attempt, then sees the book's step beside it, the
// fold opens, and they self-check (matches · partly · no). Never an attempt.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { ReaderActiveQuestionDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerActiveQuestion: vi.fn(), readerActiveQuestionStatus: vi.fn(), readerActiveQuestionAction: vi.fn(),
    readerReconstruct: vi.fn(), readerReconstructUndo: vi.fn(), findSources: vi.fn(),
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
const SELECTED = view.blocks[1];
const NEXT = view.blocks[2];

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

async function tryNextStep() {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(SELECTED.markdown);
  select(block);
  await screen.findByRole("textbox", { name: "What do you want to do with this?" });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "let me try the next step" }));
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
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
  api.readerActiveQuestion.mockResolvedValue({
    style: "next_step", anchorSpanIds: [SELECTED.spanId], foldedSpanIds: [NEXT.spanId], status: "queued",
    batchId: "batch_1", message: null, question: null,
  });
  api.readerActiveQuestionStatus.mockResolvedValue({ question: null, job: { status: "running" } });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("the next lines fold at once, before the question is written, with show one press away", async () => {
  await tryNextStep();
  await waitFor(() => expect(api.readerActiveQuestion).toHaveBeenCalledWith({ extractionId: view.extractionId, spanIds: [SELECTED.spanId], style: "next_step" }));
  expect(await screen.findByText(/the next line is folded while you try/)).toBeTruthy();
  expect(screen.queryByText(NEXT.markdown)).toBeNull();
  expect(screen.getByText(/writing the question — the lines stay folded/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "show" }));
  expect(await screen.findByText(NEXT.markdown)).toBeTruthy();
  // No attempt is ever written from here.
  expect(JSON.stringify(api.readerActiveQuestion.mock.calls)).not.toMatch(/attempt/i);
});

it("an answer shows the book's step beside it, opens the fold and asks for the self-check", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerActiveQuestionStatus.mockResolvedValue({ question: question(), job: { status: "completed" } });
  api.readerActiveQuestionAction
    .mockResolvedValueOnce({ question: question({ status: "answered", responseMd: "the eigenvalues are 3 and 1", answeredAt: "t" }), formativeJobId: null })
    .mockResolvedValueOnce({ question: question({ status: "answered", responseMd: "the eigenvalues are 3 and 1", answeredAt: "t", selfCheck: "partly", missed: true }), formativeJobId: "ltgj_1" });
  await tryNextStep();
  await act(async () => { vi.advanceTimersByTime(2500); });
  expect(await screen.findByText("What comes next after this line?")).toBeTruthy();
  expect(screen.queryByText(NEXT.markdown)).toBeNull();
  fireEvent.change(screen.getByRole("textbox", { name: "Your next step" }), { target: { value: "the eigenvalues are 3 and 1" } });
  fireEvent.click(screen.getByRole("button", { name: /compare with the book/ }));
  await waitFor(() => expect(api.readerActiveQuestionAction).toHaveBeenCalledWith({ questionId: "raq_1", action: "answered", response: "the eigenvalues are 3 and 1" }));
  // The book's own step (source voice) beside the learner's, and the fold is open.
  const step = await screen.findAllByText(NEXT.markdown);
  expect(step.length).toBe(2);
  expect(screen.queryByText(/folded while you try/)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "partly" }));
  await waitFor(() => expect(api.readerActiveQuestionAction).toHaveBeenLastCalledWith({ questionId: "raq_1", action: "self_checked", selfCheck: "partly" }));
  expect(await screen.findByText(/kept with this passage/i)).toBeTruthy();
});

it("show me reveals the book's step without an answer", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  api.readerActiveQuestionStatus.mockResolvedValue({ question: question(), job: { status: "completed" } });
  api.readerActiveQuestionAction.mockResolvedValue({ question: question({ status: "answered", answeredAt: "t" }), formativeJobId: null });
  await tryNextStep();
  await act(async () => { vi.advanceTimersByTime(2500); });
  fireEvent.click(await screen.findByRole("button", { name: "show me" }));
  await waitFor(() => expect(api.readerActiveQuestionAction).toHaveBeenCalledWith({ questionId: "raq_1", action: "answered", response: null }));
});

it("with active reading switched off its actions are absent from the palette", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent: {
    ...intent,
    palette: intent.palette.map((g) => ({ ...g, actions: g.actions.filter((a) => a.effect.kind !== "active_reading" && a.effect.kind !== "another_way") })),
  } };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  select(await screen.findByText(SELECTED.markdown));
  await screen.findByRole("textbox", { name: "What do you want to do with this?" });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  expect(within(palette).queryByRole("button", { name: "let me try the next step" })).toBeNull();
  expect(within(palette).queryByRole("button", { name: /disabled/ })).toBeNull();
});
