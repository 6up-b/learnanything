// UX Phase 2 fix round 3 (whole-stage verify 20261021-130232-Uk06Al, item 4):
// the palette's "Ask the tutor about this" from every Reader posture.
// - Reading: Ask opens, its box focused (round 1's F5; pinned again here).
// - Comparing (Ctrl+Shift+F, the library ask): the rail is hidden while
//   comparing, so the request closes the comparison and then opens Ask.
//   Before, Ask was selected behind `display: none` and nothing showed.
// - Working (a problem open in the workbench): the rail is hidden too.
//   Leaving can be refused and saves the steps, so it stays the learner's
//   call: a visible line says how. Nothing is discarded or left, and Ask
//   opens once the learner leaves.
// Nothing is ever sent.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { WORKING_ASK_WAITS } from "./ReaderWorkingPosture";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetAnswerMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
    findPractice: vi.fn(), runSourceTool: vi.fn(), recordProposalImpressions: vi.fn(), recordSourceOfferShown: vi.fn(),
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

function wbSession(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb1", practiceItemId: null, stemMd: PROSE, importStatus: "pending", importError: null, origin: "reader",
    entry: "work_through", parentSessionId: null, extractionId: view.extractionId, spanIds: ["span_symmetric_prose"],
    sourceVisible: true, sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open",
    attemptId: null, createdAt: "2026-10-17T09:00:00Z", updatedAt: "2026-10-17T09:00:00Z", closedAt: null, steps: [],
    lastEditedStepId: null, parts: null, sourceId: view.sourceId,
    record: { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null },
    ...overrides,
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1600 });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.recordProposalImpressions.mockResolvedValue({ recorded: 0 });
  api.workbenchForSource.mockResolvedValue({ sessions: [], openSessionDays: 30 });
  api.workbenchOpen.mockResolvedValue({ session: wbSession(), resumed: false });
  api.workbenchRefreshImport.mockResolvedValue({ session: wbSession() });
  api.workbenchLeave.mockResolvedValue({ session: wbSession() });
  contract.value = { readerEnabled: true, inquiryEnabled: true };
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
  window.getSelection()?.removeAllRanges();
});

function rail(): HTMLElement | null {
  return screen.queryByRole("complementary", { hidden: true });
}

function askShown(): boolean {
  const element = rail();
  return Boolean(element) && element!.style.display !== "none" && screen.getByRole("button", { name: "ask" }).getAttribute("aria-pressed") === "true";
}

describe("the palette's ask, from each Reader posture", () => {
  it("reading: opens Ask", async () => {
    const { rerender } = render(<ReaderScreen initialSource={source} onError={vi.fn()} askRequest={0} />);
    await screen.findByText(PROSE);
    expect(askShown()).toBe(false);
    await act(async () => {
      rerender(<ReaderScreen initialSource={source} onError={vi.fn()} askRequest={1} />);
    });
    expect(askShown()).toBe(true);
    expect(api.readerAsk).not.toHaveBeenCalled();
  });

  it("comparing: leaves the comparison and opens Ask", async () => {
    contract.value = { readerEnabled: true, inquiryEnabled: true, libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true } };
    const { rerender } = render(<ReaderScreen initialSource={source} onError={vi.fn()} askRequest={0} />);
    await screen.findByText(PROSE);
    await act(async () => {
      fireEvent.keyDown(window, { key: "F", ctrlKey: true, shiftKey: true });
    });
    expect(await screen.findByRole("textbox", { name: "ask your library" })).toBeTruthy();
    expect(rail()?.style.display).toBe("none");
    await act(async () => {
      rerender(<ReaderScreen initialSource={source} onError={vi.fn()} askRequest={1} />);
    });
    expect(screen.queryByRole("textbox", { name: "ask your library" })).toBeNull();
    expect(askShown()).toBe(true);
    expect(api.readerAsk).not.toHaveBeenCalled();
    expect(api.readerLibraryAsk).not.toHaveBeenCalled();
  });

  it("working: keeps the problem open, says how to reach Ask, and opens Ask once the learner leaves", async () => {
    setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
    const { rerender } = render(<ReaderScreen initialSource={source} onError={vi.fn()} askRequest={0} />);
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

    await act(async () => {
      rerender(<ReaderScreen initialSource={source} onError={vi.fn()} askRequest={1} />);
    });
    // Nothing left or discarded: the problem is still open, with a visible line.
    expect(screen.getByRole("region", { name: "workbench" })).toBeTruthy();
    expect(screen.getByTestId("workbench-ask-waiting").textContent).toContain(WORKING_ASK_WAITS);
    expect(api.workbenchLeave).not.toHaveBeenCalled();
    expect(api.workbenchAbandon).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /leave for now/ }));
    await waitFor(() => expect(screen.queryByRole("region", { name: "workbench" })).toBeNull());
    await waitFor(() => expect(askShown()).toBe(true));
    expect(api.readerAsk).not.toHaveBeenCalled();
  });
});
