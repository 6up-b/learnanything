// RW1c in the Reader (spec §4.6; UX §4.2): with reader_tutor on, an Ask's
// answer shows its modes, "another way · that didn't help…" sends the follow-up
// with its retrieval intent, and the offers fetch early and show on press
// (the same harness as tutorSwitchOff.test.tsx).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(), findPractice: vi.fn(), runSourceTool: vi.fn(),
    recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
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

const TUTOR = { retrieval: true, offers: true, anotherWay: true, personalizedDefault: true, tryNextStep: false, manifestIncludes: [] };

function landed(spanId: string) {
  return {
    ...answer(spanId),
    tutor: {
      modes: ["excerpt", "grounded"], bridgeMd: null, abstained: false, abstentionLine: null, droppedExcerpt: null,
      droppedBridge: null, intent: "explain", personalized: true, retrieval: { status: "verified", policy: "reading" },
      excerpt: { extractionId: view.extractionId, spanId, quote: "A symmetric matrix equals its transpose.", label: "Symmetric matrices", relation: "in_view" },
    },
    tutorOffers: { buttons: [] },
    toolRequests: [],
  };
}

it("an answer shows its modes, and its offers fetch early and show on press", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR };
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "prop_1", items: [
    { rank: 1, practiceItemId: "pi_1", learningObjectId: "lo", learningObjectTitle: null, practiceMode: "short_answer", prompt: "Show A equals its transpose.", facetIds: [], rationale: null },
  ] });
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  api.readerAsk.mockResolvedValue(landed(view.blocks[1].spanId ?? ""));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "why?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  expect(screen.getByText("A symmetric matrix equals its transpose.")).toBeTruthy();
  expect(screen.getByText(/from your books · Symmetric matrices/)).toBeTruthy();
  // The practice lookup ran when the answer landed; nothing of it is shown, nothing recorded.
  await waitFor(() => expect(api.findPractice).toHaveBeenCalledTimes(1));
  expect(screen.queryByText(/Show A equals its transpose/)).toBeNull();
  expect(api.recordProposalImpressions).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "practice this" }));
  await screen.findByText(/Show A equals its transpose/);
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledTimes(1));
});

it("another way sends the follow-up with its retrieval intent", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR };
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "p", items: [] });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  api.readerAsk.mockResolvedValue(landed(view.blocks[1].spanId ?? ""));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "why?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  // The first Ask names no retrieval intent (today's request).
  expect(api.readerAsk.mock.calls[0][0]).not.toHaveProperty("retrievalIntent");
  api.readerAsk.mockResolvedValue({ ...landed(view.blocks[1].spanId ?? ""), readerAnswerEventId: "a2", parentExchangeId: "a1", answerMd: "Another answer" });
  fireEvent.click(screen.getByRole("button", { name: "another way" }));
  await screen.findByText("Another answer");
  expect(api.readerAsk.mock.calls[1][0]).toMatchObject({ question: "Explain it another way", parentExchangeId: "a1", retrievalIntent: "alternative" });
  fireEvent.click(screen.getAllByRole("button", { name: "that didn't help…" })[0]);
  fireEvent.change(screen.getByPlaceholderText("optional: what's still unclear…"), { target: { value: "still lost" } });
  api.readerAsk.mockResolvedValue({ ...landed(view.blocks[1].spanId ?? ""), readerAnswerEventId: "a3", parentExchangeId: "a1", answerMd: "Third answer" });
  fireEvent.click(screen.getByRole("button", { name: "ask again · ctrl+↵" }));
  await screen.findByText("Third answer");
  expect(api.readerAsk.mock.calls[2][0]).toMatchObject({ question: "still lost", retrievalIntent: "remediate" });
});
