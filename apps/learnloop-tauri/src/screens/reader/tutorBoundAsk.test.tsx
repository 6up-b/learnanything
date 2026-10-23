// RW1c fix round 4 (F3): an Ask from a bound workbench session names the
// session whenever EITHER RW1c switch is on, so the server derives the item's
// restriction (a cold administration refuses tools and offers). With only
// offers on, the desktop used to drop the binding and the server read the
// question as plain reading. The request's keys are the shared fixture's; the
// backend half replays them through the handler
// (tests/test_reader_rw1c_review.py::test_the_desktops_offers_only_bound_ask_refuses_tools_when_cold).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import boundAsk from "../../fixtures/readerBoundOffersOnlyAsk.json";
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(), findPractice: vi.fn(), runSourceTool: vi.fn(),
    recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
    workbenchForSource: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchSaveStep: vi.fn(),
    workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchReopen: vi.fn(),
    workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(), workbenchSubmit: vi.fn(),
    workbenchSessionForAttempt: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string; readOnly?: boolean }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} readOnly={p.readOnly} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const PROSE = view.blocks[1].markdown;

function boundSession(): WorkbenchSessionDto {
  return {
    sessionId: "wb_bound", practiceItemId: "pi_determinant_2", stemMd: PROSE, importStatus: "bound", importError: null, origin: "reader",
    entry: "work_through", parentSessionId: null, extractionId: view.extractionId, spanIds: [view.blocks[1].spanId ?? ""],
    sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open",
    attemptId: null, createdAt: "2026-10-17T09:00:00Z", updatedAt: "2026-10-17T09:00:00Z", closedAt: null, steps: [],
    lastEditedStepId: null, parts: null, sourceId: view.sourceId,
    record: { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null },
  };
}

/** What the handler answers for this request while the bound item is cold (the backend half pins it). */
function refused() {
  return {
    eventId: "q1", readerAnswerEventId: "a1", parentExchangeId: null, model: "fake", answerMd: "Landed answer",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" }, warmedSurfaceIds: [],
    burnedSurfaceIds: [], hintEquivalent: false, remaining: 9, learnerGap: { status: "queued", kind: null },
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
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
  api.workbenchForSource.mockResolvedValue({ sessions: [], openSessionDays: 30 });
  api.workbenchOpen.mockResolvedValue({ session: boundSession(), resumed: false });
  api.workbenchRefreshImport.mockResolvedValue({ session: boundSession() });
  api.workbenchGet.mockResolvedValue({ session: boundSession() });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

async function askFromTheWorkbench(): Promise<Record<string, unknown>> {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(PROSE);
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  await screen.findByText(/^selected ·/);
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  await screen.findByRole("region", { name: "workbench" });
  api.readerAsk.mockResolvedValue(refused());
  // The rail's composer (folded away beside the workbench, still the one Ask path).
  fireEvent.click(screen.getByRole("button", { name: "ask", hidden: true }));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "how do I start?" } });
  fireEvent.click(screen.getByRole("button", { name: /^ask (follow-up )?· ctrl\+↵$/, hidden: true }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  return api.readerAsk.mock.calls[0][0] as Record<string, unknown>;
}

it("offers on and retrieval off, an Ask from a bound workbench names its session (the fixture's keys)", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, readerTutor: boundAsk.readerTutor };
  const request = await askFromTheWorkbench();
  expect(request.workbenchSessionId).toBe("wb_bound");
  expect(Object.keys(request).sort()).toEqual([...boundAsk.requestKeys].sort());
  // The handler refuses tools and offers for it (the backend half): nothing eager runs.
  await screen.findByText("Landed answer");
  expect(api.findPractice).not.toHaveBeenCalled();
  expect(api.runSourceTool).not.toHaveBeenCalled();
  expect(api.recordProposalImpressions).not.toHaveBeenCalled();
});

it("both RW1c switches off, the Ask is the base's: no binding is sent", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true };
  const request = await askFromTheWorkbench();
  expect(request).not.toHaveProperty("workbenchSessionId");
});
