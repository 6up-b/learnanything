// RW1c's kill switches on the screen (spec §4.6, §12 "kill-switch parity"):
// with reader_tutor.retrieval_enabled and offers_enabled off the prompt
// contract carries no `readerTutor` key, and an Ask in the Reader renders
// exactly as before RW1c -- the answer in the model's voice, no "From your
// books" excerpt, no "another way · that didn't help…", no offer buttons --
// even though today's sidecar already sends the sources spec's practice
// request and tool requests on the wire. The snapshots in
// __snapshots__/tutorSwitchOff.test.tsx.snap were written on the base commit
// (fab576ac1), before any RW1c frontend code existed; an offer lookup would
// throw here, because the api mocks name only the calls the base code made.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(),
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

/** React's generated ids depend on render order, and a landed answer is
 *  stamped with the clock; the markup is the contract. */
function markup(container: HTMLElement): string {
  return container.innerHTML.replace(/:r[0-9a-z]+:/g, ":r:").replace(/«r[0-9a-z]+»/g, "«r»")
    .replace(/\d{1,2}\/\d{1,2}\/\d{4}, \d{1,2}:\d{2}:\d{2}\s?[AP]M/g, "<time>");
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

/** reader.ask as today's sidecar answers it (S0's practice request and S4's
 *  tool requests are already on the wire; the Reader renders neither). */
function answer(spanId: string) {
  return {
    eventId: "q1", readerAnswerEventId: "a1", parentExchangeId: null, model: "fake", answerMd: "Landed answer",
    answerMode: "answer_directly", citations: [{ extractionId: view.extractionId, spanId, label: "the passage" }],
    manifest: { version: "p3-reader-branches-v1" }, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false,
    remaining: 9, learnerGap: { status: "queued", kind: null },
    practiceRequest: { request: { query: "why?", learningObjectIds: [], facetIds: [], excludeItemIds: [], intent: "practice" }, caller: { kind: "tutor", ref: "q1" }, version: "tutor_practice_request.v1" },
    toolRequests: [
      { toolCallId: "stc_1", tool: "find_sources", reason: "A worked example in your book", run: "eager", dropped: [], arguments: { query: "why", intent: "worked_example" } },
      { toolCallId: "stc_2", tool: "compare_sources", reason: "Your books differ here", run: "lazy", dropped: [], arguments: { query: "why" } },
    ],
  };
}

function noOfferCalls(): void {
  for (const mock of Object.values(api)) {
    for (const call of mock.mock.calls) expect(JSON.stringify(call)).not.toMatch(/find_?practice|findPractice|run_?source_?tool|runSourceTool|impression|offer_?shown|another_way|tutor_offer/i);
  }
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
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

const OFF_CONTRACTS: Array<[string, Record<string, unknown>]> = [
  ["reader_tutor off (inquiry on)", { readerEnabled: true, inquiryEnabled: true }],
  ["reader_inquiry off as well (the flat rail)", { readerEnabled: true }],
];

it.each(OFF_CONTRACTS)("an answer in the Reader is today's with %s", async (_label, value) => {
  contract.value = value;
  const view_ = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  api.readerAsk.mockResolvedValue(answer(view.blocks[1].spanId ?? ""));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "why?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  expect(markup(view_.container)).toMatchSnapshot("ask rail after an answer lands");
  noOfferCalls();
});

it.each(OFF_CONTRACTS)("a saved exchange is today's with %s", async (_label, value) => {
  contract.value = value;
  api.readerAskHistory.mockResolvedValue({ exchanges: [{
    eventId: "a0", parentExchangeId: null, selectionSpanIds: [view.blocks[1].spanId ?? ""], selectionQuoteMd: "the words",
    questionEventId: "q0", resolution: "open", extractionId: view.extractionId, spanId: view.blocks[1].spanId ?? "",
    questionMd: "saved question?", answerMd: "Saved answer", answerMode: "answer_directly", citations: [], createdAt: null,
  }] });
  const view_ = render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  await screen.findAllByText(/saved question\?/);
  expect(markup(view_.container)).toMatchSnapshot("ask rail with a saved exchange");
  noOfferCalls();
});
