// RW2a in the Reader (spec §5.1; UX §3.1, §5.1-5.3, W5, W8, W15, S1/S2/S6/S7/
// S13): "work through this" on a selected problem opens the working posture at
// once (half the window, at least 480 px, resizable and remembered; the rail
// folds away), with the book open by default; the book hidden covers the source
// and says why (W8); an unfinished problem shows a ✎ resume mark beside its
// passage and a line in the rail; Leave for now collapses back into reading;
// a narrow window stacks the sides with "show in the book"; a submit hands the
// attempt to the shell; back from feedback shows the submitted problem read-only.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import { setAlgoConfig } from "../app/algoConfig";
import type { SourceLibraryCard, WorkbenchSessionDto, WorkbenchSummaryDto } from "../api/dto";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(),
  workbenchForSource: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchSaveStep: vi.fn(),
  workbenchSetBook: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchReopen: vi.fn(),
  workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn(), workbenchSubmit: vi.fn(),
  workbenchSessionForAttempt: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />
  ),
}));

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

const summary = (overrides: Partial<WorkbenchSummaryDto> = {}): WorkbenchSummaryDto => ({
  sessionId: "wb_old", status: "open", practiceItemId: "pi_514", stemMd: "Exercise 5.14 Find the CDF of X.", origin: "reader",
  entry: "work_through", extractionId: view.extractionId, spanIds: ["span_spectral_worked"], importStatus: "none",
  sourceVisible: true, stepCount: 2, createdAt: "2026-10-16T09:00:00Z", updatedAt: "2026-10-16T09:00:00Z", unfinished: false,
  ...overrides,
});

function setWidth(width: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
}

async function selectProse() {
  const block = await screen.findByText(PROSE);
  const range = document.createRange();
  range.selectNodeContents(block);
  const selection = window.getSelection()!;
  selection.removeAllRanges();
  selection.addRange(range);
  fireEvent.mouseUp(block);
  await screen.findByText(/^selected ·/);
}

beforeEach(() => {
  vi.resetAllMocks();
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30 } });
  // jsdom's storage is shadowed in this Node; give the screen a real one.
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
  setWidth(1600);
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.workbenchForSource.mockResolvedValue({ sessions: [], openSessionDays: 30 });
  api.workbenchOpen.mockResolvedValue({ session: wbSession(), resumed: false });
  api.workbenchRefreshImport.mockResolvedValue({ session: wbSession() });
  api.workbenchLeave.mockResolvedValue({ session: wbSession() });
  api.workbenchSetBook.mockImplementation(async (input: { visible: boolean }) => ({ session: wbSession({ sourceVisible: input.visible }) }));
});
afterEach(() => { cleanup(); setAlgoConfig(undefined); });

it("work through this on a selected problem opens the working posture at once, beside the book", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  const input = api.workbenchOpen.mock.calls[0][0];
  expect(input).toMatchObject({
    origin: "reader", entry: "work_through", extractionId: view.extractionId, spanIds: ["span_symmetric_prose"],
  });
  expect(input.stemMd).toContain("A real symmetric matrix");
  expect(input.importRequest).toMatchObject({ extractionId: view.extractionId, sourceId: view.sourceId });
  expect(input.importRequest.rawSelection.nodes.length).toBeGreaterThan(0);
  const pane = await screen.findByRole("region", { name: "workbench" });
  expect(screen.queryByRole("complementary")).toBeNull();
  const width = Number.parseInt((pane.closest("[data-workbench-pane]") as HTMLElement).style.width, 10);
  expect(width).toBe(800);
  const divider = screen.getByRole("separator", { name: "resize the workbench" });
  expect(divider.getAttribute("aria-valuemin")).toBe("480");
  // The book stays: the source column still shows the passage, beside the stem.
  expect(within(screen.getByRole("main")).getByText(PROSE)).toBeTruthy();
  expect(within(pane).getByText(PROSE)).toBeTruthy();
  expect(screen.queryByText(/The book is hidden/)).toBeNull();
});

it("the split is resizable by keyboard, never under 480 px, and remembered on this device", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  const divider = await screen.findByRole("separator", { name: "resize the workbench" });
  for (let index = 0; index < 30; index += 1) fireEvent.keyDown(divider, { key: "ArrowRight" });
  expect(divider.getAttribute("aria-valuenow")).toBe("480");
  fireEvent.keyDown(divider, { key: "ArrowLeft" });
  const widened = divider.getAttribute("aria-valuenow");
  expect(Number(widened)).toBeGreaterThan(480);
  expect(window.localStorage.getItem("ll.workbench.splitWidth")).toBe(widened);
});

it("with the book hidden the source pane says why and how to bring it back (W8)", async () => {
  api.workbenchOpen.mockResolvedValue({ session: wbSession({ sourceVisible: false, entry: "check_me" }), resumed: false });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  const cover = await screen.findByTestId("workbench-book-cover");
  expect(cover.textContent).toContain("The book is hidden so this can count as your own attempt.");
  expect(cover.textContent).toContain("Show it any time (Ctrl+Shift+B) — it'll count as one hint from then on.");
  expect(screen.getByRole("main", { hidden: true }).getAttribute("aria-hidden")).toBe("true");
});

it("an unfinished problem is a ✎ mark beside its passage and a line in the rail, and resumes where it was", async () => {
  api.workbenchForSource.mockResolvedValue({ sessions: [summary()], openSessionDays: 30 });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wbSession({ sessionId: "wb_old", practiceItemId: "pi_514", importStatus: "none", stemMd: "Exercise 5.14 Find the CDF of X.",
    steps: [{ stepId: "s1", chainId: "s1", ordinal: 1, kind: "step", bodyMd: "F(x) = p F_Y(x)", deleted: false, createdAt: "x", editedAt: "x", versions: [] }] }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const mark = await screen.findByRole("button", { name: "Resume this problem: Exercise 5.14" });
  expect(mark.closest("[data-span-id]")?.getAttribute("data-span-id")).toBe("span_spectral_worked");
  const rail = screen.getByRole("complementary");
  expect(within(rail).getByText(/Exercise 5.14/)).toBeTruthy();
  expect(within(rail).queryByText(/\d+ unfinished/)).toBeNull();
  fireEvent.click(mark);
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({
    origin: "reader", entry: "resume", sessionId: "wb_old", extractionId: view.extractionId,
  })));
  expect((await screen.findByRole("textbox", { name: "Step 1" }) as HTMLTextAreaElement).value).toBe("F(x) = p F_Y(x)");
});

it("Leave for now collapses back into reading at the passage, and the problem stays resumable", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  await screen.findByRole("region", { name: "workbench" });
  api.workbenchForSource.mockResolvedValue({ sessions: [summary({ sessionId: "wb1", spanIds: ["span_symmetric_prose"], stemMd: PROSE })], openSessionDays: 30 });
  fireEvent.click(screen.getByRole("button", { name: /leave for now/ }));
  await waitFor(() => expect(screen.queryByRole("region", { name: "workbench" })).toBeNull());
  expect(screen.getByRole("complementary")).toBeTruthy();
  expect(await screen.findByRole("button", { name: /Resume this problem/ })).toBeTruthy();
  expect(api.workbenchLeave).toHaveBeenCalledWith({ sessionId: "wb1" });
});

it("below 1,040 px the sides stack and the book opens in a sheet on request", async () => {
  setWidth(900);
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  const pane = await screen.findByRole("region", { name: "workbench" });
  expect((pane.closest("[data-workbench-pane]") as HTMLElement).dataset.layout).toBe("stacked");
  expect(screen.queryByRole("separator", { name: "resize the workbench" })).toBeNull();
  const main = screen.getByRole("main", { hidden: true });
  expect(main.style.display).toBe("none");
  fireEvent.click(screen.getByRole("button", { name: "show in the book ▾" }));
  expect(main.style.display).not.toBe("none");
});

it("a submit hands the attempt to the shell with the way back to its passage", async () => {
  const bound = wbSession({ practiceItemId: "pi_514", importStatus: "bound",
    steps: [{ stepId: "s1", chainId: "s1", ordinal: 1, kind: "step", bodyMd: "A = U Sigma V^T", deleted: false, createdAt: "x", editedAt: "x", versions: [] }] });
  api.workbenchOpen.mockResolvedValue({ session: bound, resumed: false });
  const result = { version: 1, attempt: { attemptId: "att_1" }, session: { ...bound, status: "submitted", attemptId: "att_1" }, practiceSession: { sessionId: "ps_new" } };
  api.workbenchSubmit.mockResolvedValue(result);
  const onSubmitted = vi.fn();
  render(<ReaderScreen initialSource={source} onError={vi.fn()} workbench={{ practiceSessionId: "ps_app", onSubmitted }} />);
  await selectProse();
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(await screen.findByRole("button", { name: /work through this/ }));
  fireEvent.click(await screen.findByRole("button", { name: /^submit/ }));
  await waitFor(() => expect(api.workbenchSubmit).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "wb1", practiceSessionId: "ps_app" })));
  await waitFor(() => expect(onSubmitted).toHaveBeenCalledWith(result, { card: source.card, spanId: "span_symmetric_prose" }));
});

it("back from feedback opens the submitted problem read-only; Esc returns to reading at its passage", async () => {
  api.workbenchSessionForAttempt.mockResolvedValue({ session: wbSession({ status: "submitted", attemptId: "att_1", practiceItemId: "pi_514", importStatus: "bound",
    steps: [{ stepId: "s1", chainId: "s1", ordinal: 1, kind: "step", bodyMd: "A = U Sigma V^T", deleted: false, createdAt: "x", editedAt: "x", versions: [] }] }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} workbench={{ practiceSessionId: null, initialAttemptId: "att_1" }} />);
  await waitFor(() => expect(api.workbenchSessionForAttempt).toHaveBeenCalledWith({ attemptId: "att_1" }));
  const pane = await screen.findByRole("region", { name: "workbench" });
  expect(within(pane).getByText("A = U Sigma V^T")).toBeTruthy();
  expect(within(pane).queryByRole("textbox")).toBeNull();
  await act(async () => { fireEvent.keyDown(pane, { key: "Escape" }); });
  await waitFor(() => expect(screen.queryByRole("region", { name: "workbench" })).toBeNull());
  expect(screen.getByRole("complementary")).toBeTruthy();
});

// Review F4: only a shown book counts, so an unshown one is never in view,
// whatever surface the session came from.
it("a resumed problem whose book is not shown has the source covered, whatever its origin", async () => {
  api.workbenchForSource.mockResolvedValue({ sessions: [summary()], openSessionDays: 30 });
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wbSession({ sessionId: "wb_old", origin: "practice", sourceVisible: false,
    practiceItemId: "pi_514", importStatus: "none" }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "Resume this problem: Exercise 5.14" }));
  await screen.findByRole("region", { name: "workbench" });
  expect(screen.getByTestId("workbench-book-cover")).toBeTruthy();
});

// Review F12 (D40, UX S7): "check me" opens in the Reader's working posture,
// book hidden, answering the pick's own serve.
it("check me opens in the working posture with the book hidden and submits as the pick's serve", async () => {
  const onCheckMeShown = vi.fn();
  const check = {
    practiceItemId: "pi_check", spanId: "span_spectral_worked", sourceId: view.sourceId, stemMd: "Is A^T A symmetric?",
    schedulerCandidateId: "cand_pick", planPresentationId: "pres_pick",
  };
  api.workbenchOpen.mockResolvedValue({ resumed: false, session: wbSession({ sessionId: "wb_check", practiceItemId: "pi_check",
    importStatus: "none", entry: "check_me", sourceVisible: false, stemMd: "Is A^T A symmetric?", spanIds: ["span_spectral_worked"],
    steps: [{ stepId: "s1", chainId: "s1", ordinal: 1, kind: "step", bodyMd: "yes", deleted: false, createdAt: "x", editedAt: "x", versions: [] }] }) });
  api.workbenchSubmit.mockResolvedValue({ version: 1, attempt: { attemptId: "att_c" }, session: wbSession({ sessionId: "wb_check", status: "submitted", attemptId: "att_c" }), practiceSession: null });
  const onSubmitted = vi.fn();
  render(<ReaderScreen initialSource={source} onError={vi.fn()} workbench={{ practiceSessionId: "s1", checkMe: check, onCheckMeShown, onSubmitted }} />);
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({
    origin: "reader", entry: "check_me", practiceItemId: "pi_check", extractionId: view.extractionId, spanIds: ["span_spectral_worked"],
  });
  // The book's default for a check is hidden (the server's rule): the client sends no choice.
  expect(api.workbenchOpen.mock.calls[0][0].sourceVisible).toBeUndefined();
  await screen.findByRole("region", { name: "workbench" });
  expect(screen.getByTestId("workbench-book-cover")).toBeTruthy();
  expect(onCheckMeShown).toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: /^submit/ }));
  await waitFor(() => expect(api.workbenchSubmit).toHaveBeenCalledWith(expect.objectContaining({
    sessionId: "wb_check", practiceSessionId: "s1", schedulerCandidateId: "cand_pick", planPresentationId: "pres_pick",
  })));
  await waitFor(() => expect(onSubmitted).toHaveBeenCalled());
});

// Re-review F13: the pick's serve goes on the problem when "check me" opens
// it, so a resume after leaving (which knows nothing of the pick) still
// submits as that serve; F14: the server hides the book on a reused problem.
it("check me puts the pick's serve on the problem, so it survives leaving and resuming", async () => {
  const check = {
    practiceItemId: "pi_check", spanId: "span_spectral_worked", sourceId: view.sourceId, stemMd: "Is A^T A symmetric?",
    schedulerCandidateId: "cand_pick", planPresentationId: "pres_pick",
  };
  api.workbenchOpen.mockResolvedValue({ resumed: true, session: wbSession({ sessionId: "wb_check", practiceItemId: "pi_check",
    importStatus: "none", entry: "work_through", sourceVisible: false, sourceShownAt: "2026-10-17T08:00:00Z",
    schedulerCandidateId: "cand_pick", planPresentationId: "pres_pick", spanIds: ["span_spectral_worked"] }) });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} workbench={{ practiceSessionId: "s1", checkMe: check, onCheckMeShown: vi.fn() }} />);
  await waitFor(() => expect(api.workbenchOpen).toHaveBeenCalledTimes(1));
  expect(api.workbenchOpen.mock.calls[0][0]).toMatchObject({
    entry: "check_me", schedulerCandidateId: "cand_pick", planPresentationId: "pres_pick",
  });
  // A reused problem left with the book open comes back with it covered.
  await screen.findByRole("region", { name: "workbench" });
  expect(screen.getByTestId("workbench-book-cover")).toBeTruthy();
});
