// The RW4b landing's hook in RW1c's tutor offers (docs/reviews/reader-workbench-RW4b.md
// §5): with library_exercises on, a tutor practice offer shows the proposal's
// textbook exercises through ProposalExercises (the server's exposure view,
// the exposure label, never a check on your own), from the tutor's own
// find_practice and from a find_practice tool run; an exercises-only proposal
// is a result, not "nothing fits". Switched off (no `libraryExercises` in the
// prompt contract), the offer renders exactly as it does for a proposal with
// no exercises, and no RW4b call is made. The harness is tutorReader.test.tsx's.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { EXERCISE_COPY } from "./exerciseCandidates";
import { OFFER_COPY } from "./TutorOffers";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(), findPractice: vi.fn(), runSourceTool: vi.fn(),
    recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
    readerExerciseCandidates: vi.fn(), readerFindExercises: vi.fn(), readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
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

const TUTOR = { retrieval: true, offers: true, anotherWay: true, personalizedDefault: true, tryNextStep: false, manifestIncludes: [] };
const LIBRARY_ASK = { expandGraph: false, personalizedDefault: true, compare: false };
const ON = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR, libraryAsk: LIBRARY_ASK, libraryExercises: { fallback: false } };
const OFF = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR, libraryAsk: LIBRARY_ASK };

const ITEM = { rank: 1, practiceItemId: "pi_1", learningObjectId: "lo", learningObjectTitle: null, practiceMode: "short_answer", prompt: "Show A equals its transpose.", facetIds: [], rationale: null };

function exercise(span: string, statement: string) {
  return { kind: "source_exercise" as const, key: `srcex:ext_text:${span}`, extractionId: "ext_text", spanIds: [span], sourceId: view.sourceId,
    revisionId: "rev_text", sourceTitle: "Matrices", label: `Exercise ${span}`, page: 9, statement, rationale: null, labelLine: "From Matrices, p. 9" };
}
const EX_A = exercise("t6", "1. Show that a symmetric matrix has real eigenvalues.");
const EX_B = exercise("t7", "2. Prove that the transpose of a product reverses its order.");

function practice(items: unknown[], exercises: unknown[]) {
  return { version: 1, status: "ok", proposalId: "prop_1", items, sourceExercises: exercises };
}

const fresh = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own", exposureRuleVersion: "reading_exposure_v1" };
const seen = { exposed: true, reasons: ["source_exposed"], label: "you've recently seen this page or its solution", note: null,
  offeredAs: "practice", exposureRuleVersion: "reading_exposure_v1" };

function exerciseView(entries: Array<[string, typeof fresh | typeof seen]>) {
  const result = { version: 1, proposalId: "prop_1", withheld: 0,
    candidates: entries.map(([key, exposure]) => ({ key, extractionId: "ext_text", spanIds: [], sourceId: view.sourceId, revisionId: "rev_text", exposure })) };
  return { jobId: "ljob_ex", kind: "exercise_candidates", askId: null, state: "done", result };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

function landed(spanId: string, toolRequests: unknown[] = []) {
  return {
    eventId: "q1", readerAnswerEventId: "a1", parentExchangeId: null, model: "fake", answerMd: "Landed answer",
    answerMode: "answer_directly", citations: [{ extractionId: view.extractionId, spanId, label: "the passage" }],
    manifest: { version: "p3-reader-branches-v1" }, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false,
    remaining: 9, learnerGap: { status: "queued", kind: null },
    practiceRequest: { request: { query: "why?", learningObjectIds: ["lo"], facetIds: [], excludeItemIds: [], intent: "practice" }, caller: { kind: "tutor", ref: "q1" }, version: "tutor_practice_request.v1" },
    toolRequests,
    tutor: {
      modes: ["grounded"], bridgeMd: null, abstained: false, abstentionLine: null, droppedExcerpt: null,
      droppedBridge: null, intent: "explain", personalized: true, retrieval: { status: "verified", policy: "reading" }, excerpt: null,
    },
    tutorOffers: { buttons: [] },
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetAnswerMode.mockResolvedValue({ eventId: "m", answerMode: "answer_directly" });
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

/** Ask once, wait for the answer and its eager practice lookup, press "practice this". */
async function askAndPress(toolRequests: unknown[] = []) {
  const utils = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  api.readerAsk.mockResolvedValue(landed(view.blocks[1].spanId ?? "", toolRequests));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "why?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  await waitFor(() => expect(api.findPractice.mock.calls.length + api.runSourceTool.mock.calls.length).toBe(1));
  await Promise.resolve();
  // Nothing of RW4b runs before the press (fetch early, show on press).
  expect(api.readerExerciseCandidates).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: OFFER_COPY.practice }));
  return utils;
}

function offerMarkup(container: HTMLElement): string {
  const offer = container.querySelector('[data-offer="practice"], [data-offer-empty="practice"]');
  return (offer?.outerHTML ?? "").replace(/:r[0-9a-z]+:/g, ":r:").replace(/«r[0-9a-z]+»/g, "«r»");
}

it("on: a tutor practice offer shows the proposal's textbook exercises with the exposure label", async () => {
  contract.value = ON;
  api.findPractice.mockResolvedValue(practice([ITEM], [EX_A, EX_B]));
  api.readerExerciseCandidates.mockResolvedValue(exerciseView([[EX_A.key, fresh], [EX_B.key, seen]]));
  await askAndPress();
  await screen.findByText(/Show A equals its transpose/);
  await screen.findByText(EX_A.statement);
  expect(api.readerExerciseCandidates).toHaveBeenCalledWith({ proposalId: "prop_1", keys: [
    { extractionId: "ext_text", spanIds: ["t6"] }, { extractionId: "ext_text", spanIds: ["t7"] },
  ] });
  expect(screen.getByText(EX_B.statement)).toBeTruthy();
  expect(screen.getAllByTestId("exercise-candidate")).toHaveLength(2);
  // The exposed one says why, and that it is practice beside the book.
  expect(screen.getByText(new RegExp(`you've recently seen this page or its solution · ${EXERCISE_COPY.practiceNotCheck}`))).toBeTruthy();
  expect(screen.getAllByText(new RegExp(EXERCISE_COPY.practiceNotCheck))).toHaveLength(1);
  // Both shown exercises are the Reader's impressions of the proposal (with its item's).
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledWith({
    proposalId: "prop_1", surface: "reader", keys: [
      { kind: "source_exercise", extractionId: "ext_text", spanIds: ["t6"] }, { kind: "source_exercise", extractionId: "ext_text", spanIds: ["t7"] },
    ],
  }));
  expect(screen.queryByText(OFFER_COPY.nothing)).toBeNull();
});

it("on: a proposal of exercises only is a result, and a find_practice tool run shows its exercises too", async () => {
  contract.value = ON;
  const tool = { toolCallId: "stc_fp", tool: "find_practice", reason: "An exercise in your book", run: "eager", dropped: [], arguments: {} };
  api.runSourceTool.mockResolvedValue({ version: 1, tool: "find_practice", policy: "reading", toolCallId: "stc_fp", runId: "r1", result: {
    status: "ok", proposalId: "prop_1", items: [],
    sourceExercises: [{ key: EX_A.key, spanKeys: ["ext_text:t6"], sourceLabel: "Matrices", page: 9, statement: EX_A.statement, rationale: null }],
  } });
  api.readerExerciseCandidates.mockResolvedValue(exerciseView([[EX_A.key, fresh]]));
  await askAndPress([tool]);
  await screen.findByText(EX_A.statement);
  expect(api.findPractice).not.toHaveBeenCalled();
  expect(api.readerExerciseCandidates).toHaveBeenCalledWith({ proposalId: "prop_1", keys: [{ extractionId: "ext_text", spanIds: ["t6"] }] });
  expect(screen.queryByText(OFFER_COPY.nothing)).toBeNull();
  expect(screen.queryByText(new RegExp(EXERCISE_COPY.practiceNotCheck))).toBeNull();
});

it("switched off, a tutor practice offer with exercises renders exactly as one without, and makes no RW4b call", async () => {
  contract.value = OFF;
  api.findPractice.mockResolvedValue(practice([ITEM], []));
  const plain = await askAndPress();
  await screen.findByText(/Show A equals its transpose/);
  const expected = offerMarkup(plain.container);
  cleanup();
  resetReaderActivityForTests();

  api.findPractice.mockReset();
  api.findPractice.mockResolvedValue(practice([ITEM], [EX_A, EX_B]));
  const withExercises = await askAndPress();
  await screen.findByText(/Show A equals its transpose/);
  await Promise.resolve();
  expect(offerMarkup(withExercises.container)).toBe(expected);
  expect(screen.queryByText(EX_A.statement)).toBeNull();
  expect(screen.queryByText(new RegExp(EXERCISE_COPY.use))).toBeNull();
  expect(api.readerExerciseCandidates).not.toHaveBeenCalled();
  expect(api.readerFindExercises).not.toHaveBeenCalled();
});

it("switched off, a proposal of exercises only is still RW1c's nothing-fits line", async () => {
  contract.value = OFF;
  api.findPractice.mockResolvedValue(practice([], [EX_A]));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  api.readerAsk.mockResolvedValue(landed(view.blocks[1].spanId ?? ""));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "why?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  await screen.findByText(OFFER_COPY.nothing);
  expect(screen.queryByText(EX_A.statement)).toBeNull();
  expect(api.readerExerciseCandidates).not.toHaveBeenCalled();
});
