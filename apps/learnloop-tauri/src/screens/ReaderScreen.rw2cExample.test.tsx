// Reader workbench RW2c, Codex review F1 (spec §5.10, G40; UX §5.6): a worked
// example the workbench shows may be in another book. With two real Reader
// sources, clicking an example from Book B opens Book B at that passage (a
// detour, as a library hit's "open" is), and an example from the open book
// is a peek in it, as before. Only the api is faked; the Reader, the working
// posture, the workbench and the example line are the real components.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import { setAlgoConfig } from "../app/algoConfig";
import type { SourceLibraryCard, WorkbenchHintViewDto, WorkbenchSessionDto, WorkbenchSummaryDto } from "../api/dto";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRestoreSource: vi.fn(),
  workbenchForSource: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchSaveStep: vi.fn(),
  workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchReopen: vi.fn(),
  workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(), workbenchSubmit: vi.fn(),
  workbenchSessionForAttempt: vi.fn(),
  workbenchCheck: vi.fn(), workbenchSuggestHelp: vi.fn(), workbenchRequestHelp: vi.fn(), workbenchHelpJob: vi.fn(),
  workbenchCancelHelp: vi.fn(), workbenchAnswerDiscriminating: vi.fn(), workbenchSetHelpStyle: vi.fn(),
  workbenchHelpState: vi.fn(), workbenchShowExample: vi.fn(), workbenchAnotherPassage: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => () => undefined, destroy: vi.fn() }) }));
const BOOK_A = { sourceId: view.sourceId, title: "Matrices", canonicalUri: "a.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const BOOK_B = { sourceId: "src_b", title: "Probability", canonicalUri: "b.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [BOOK_A, BOOK_B] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string; readOnly?: boolean }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} readOnly={p.readOnly} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));

const VIEW_B = { ...view, sourceId: "src_b", extractionId: "ext_b" };
const RECORD = { bookCounted: false, bookVisible: true, hints: 1, questionHints: 0, ownAttempt: false, line: "with help",
  footer: "book open · help used: 1", stuckNote: null };

function wbSession(): WorkbenchSessionDto {
  return {
    sessionId: "wb_old", practiceItemId: "pi_514", stemMd: "Exercise 5.14 Find the CDF of X.", importStatus: "none", importError: null,
    origin: "reader", entry: "resume", parentSessionId: null, extractionId: view.extractionId, spanIds: ["span_spectral_worked"],
    sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open",
    attemptId: null, createdAt: "2026-10-21T09:00:00Z", updatedAt: "2026-10-21T09:00:00Z", closedAt: null, lastEditedStepId: null,
    steps: [{ stepId: "s1", chainId: "c1", ordinal: 1, kind: "step", bodyMd: "F(x) = p F_Y(x)", deleted: false, createdAt: "x", editedAt: "x", versions: [] }],
    parts: null, sourceId: view.sourceId, record: RECORD,
  } as WorkbenchSessionDto;
}

const summary: WorkbenchSummaryDto = {
  sessionId: "wb_old", status: "open", practiceItemId: "pi_514", stemMd: "Exercise 5.14 Find the CDF of X.", origin: "reader",
  entry: "work_through", extractionId: view.extractionId, spanIds: ["span_spectral_worked"], importStatus: "none",
  sourceVisible: true, stepCount: 1, createdAt: "2026-10-21T09:00:00Z", updatedAt: "2026-10-21T09:00:00Z", unfinished: false,
};

function example(book: "a" | "b") {
  return book === "b"
    ? { assistId: "ha_ex_b", line: "A worked example that takes your route: Probability · §4.1", spanId: "span_b_41",
      extractionId: "ext_b", sourceId: "src_b", label: "Probability · §4.1", verdict: "follows_learner_route",
      trigger: "after_hint", aboutStepId: "c1", hintAssistId: "ha_hint" }
    : { assistId: "ha_ex_a", line: "A worked example that takes your route: Matrices · §2", spanId: "span_symmetric_prose",
      extractionId: view.extractionId, sourceId: view.sourceId, label: "Matrices · §2", verdict: "follows_learner_route",
      trigger: "after_hint", aboutStepId: "c1", hintAssistId: "ha_hint" };
}

function hint(book: "a" | "b"): WorkbenchHintViewDto {
  return {
    assistId: "ha_hint", kind: "worked_parallel", level: 3, hintMd: "Take the CDF first.",
    labels: { origin: "AI-written", kind: "a worked parallel", workedHelp: null, horizon: null } as WorkbenchHintViewDto["labels"],
    aboutStepId: "c1", continueFromStepId: null, stepLine: "about step 1", replies: ["doesnt_connect"], discriminatingAnswer: null,
    bridge: null, claims: [], example: example(book),
  } as WorkbenchHintViewDto;
}

beforeEach(() => {
  vi.resetAllMocks();
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30, help: { enabled: true, bridge: true, symbolic: true, examples: true } },
    hints: { adaptiveEnabled: true, helpStyle: "balanced" } });
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k), clear: () => store.clear(),
    },
  });
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1600 });
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (input.extractionId === "src_b" ? VIEW_B : view));
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRestoreSource.mockResolvedValue({});
  api.workbenchForSource.mockImplementation(async (input: { extractionId: string }) => (
    input.extractionId === view.extractionId ? { sessions: [summary], openSessionDays: 30 } : { sessions: [], openSessionDays: 30 }));
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wbSession() });
  api.workbenchSaveStep.mockResolvedValue({ version: 1, record: RECORD });
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => ({ session: { ...wbSession(), sourceVisible: input.visible } }));
});
afterEach(() => { cleanup(); setAlgoConfig(undefined); });

async function openProblemWith(book: "a" | "b") {
  api.workbenchHelpState.mockResolvedValue({ version: 1, check: null, hints: [hint(book)], helpStyle: null,
    storedHelpStyle: "balanced", hintsEnabled: true, examplesAvailable: true, examples: [] });
  render(<ReaderScreen initialSource={{ card: BOOK_A, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "Resume this problem: Exercise 5.14" }));
  await screen.findByRole("region", { name: "workbench" });
  return screen.findByTestId("workbench-route-example");
}

it("an example from another book opens that book at the passage", async () => {
  const line = await openProblemWith("b");
  expect(api.readerRenderView.mock.calls.map(([input]) => input.extractionId)).toEqual([view.sourceId]);
  fireEvent.click(line);
  await waitFor(() => expect(api.readerRenderView).toHaveBeenCalledWith({ extractionId: "src_b" }));
  // Book B is the book on screen now (the passage was never looked for in Book A).
  await waitFor(() => expect(api.readerGetProgress).toHaveBeenCalledWith({ extractionId: "ext_b" }));
});

it("an example from the open book is a peek in it, as before", async () => {
  const line = await openProblemWith("a");
  fireEvent.click(line);
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.readerRenderView.mock.calls.map(([input]) => input.extractionId)).toEqual([view.sourceId]);
  expect(screen.getByRole("region", { name: "workbench" })).toBeTruthy();
});
