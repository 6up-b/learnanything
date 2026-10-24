// RW5b Codex review F1: the tutor's "make this explorable" end to end in the
// Reader -- reader.ask's answer (its question event `eventId`, its interaction
// event `readerAnswerEventId`), the press, and reader.figure_request naming the
// QUESTION event as the offer, which is where the server reads the tutor's
// judgment (the interaction event id was refused `not_offered`). The harness is
// tutorReader.test.tsx's.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../../ReaderScreen";
import { setAlgoConfig } from "../../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../../api/dto";
import { resetReaderActivityForTests } from "../activity";
import { OFFER_COPY } from "../TutorOffers";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(), findPractice: vi.fn(), runSourceTool: vi.fn(),
    recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("../readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

/** reader.ask's answer as the sidecar sends it with figure offers on: the
 *  tutor judged the cited block explorable, so its offers carry the button. */
function landed(spanId: string) {
  return {
    eventId: "qe_tutor", readerAnswerEventId: "ia_answer", parentExchangeId: null, model: "fake", answerMd: "Landed answer",
    answerMode: "answer_directly", citations: [{ extractionId: view.extractionId, spanId, label: "the passage" }],
    manifest: { version: "p3-reader-branches-v1" }, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false,
    remaining: 9, learnerGap: { status: "queued", kind: null }, toolRequests: [],
    tutor: {
      modes: ["grounded"], excerpt: null, bridgeMd: null, abstained: false, abstentionLine: null, droppedExcerpt: null,
      droppedBridge: null, intent: "explain", personalized: true, retrieval: { status: "verified", policy: "reading" },
    },
    tutorOffers: { buttons: [{ kind: "make_explorable", extractionId: view.extractionId, spanId, label: "make this explorable", role: "equation" }] },
  };
}

const TUTOR = { retrieval: true, offers: true, anotherWay: true, personalizedDefault: true, tryNextStep: false, manifestIncludes: [] };
const FIGURES = { predictions: true, region: true, revisions: true, offers: true };

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
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "p", items: [] });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [] });
  api.readerFigureRequest.mockResolvedValue({ jobId: "j1", kind: "figure_build", askId: null, state: "pending", result: null });
  api.readerFigureJob.mockResolvedValue({ jobId: "j1", kind: "figure_build", askId: null, state: "pending", result: null });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("pressing the tutor's offer builds with the answer's question event as the offer, not its interaction event", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: TUTOR, figures: FIGURES };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  select(block);
  const spanId = view.blocks[1].spanId ?? "";
  api.readerAsk.mockResolvedValue(landed(spanId));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "what is this?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/ }));
  await screen.findByText("Landed answer");
  const press = await screen.findByRole("button", { name: OFFER_COPY.makeExplorable });
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
  fireEvent.click(press);
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalledTimes(1));
  expect(api.readerFigureRequest).toHaveBeenCalledWith({
    extractionId: view.extractionId, spanIds: [spanId], origin: "tutor", offerRef: "qe_tutor",
  });
});
