// RW1a Codex review, on the real screen: the queued quick check through
// failure, disconnection, recovery and cancel (F4) and its funnel events (F8);
// the kill switch leaves no hidden return stack across sources (F5); Guide
// passages and library-card openings are detours with a way back (F6); a
// detour walked back to twice is returned once (F7); skim mutes a reconnect
// line already shown (F10); an edited capture is the learner's wording (F12).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { ReaderRenderViewDto, SourceLibraryCard } from "../api/dto";
import { flushReaderActivity, resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRestoreSource: vi.fn(), readerSetInquiryStatus: vi.fn(),
  readerReconnectAnswer: vi.fn(), readerInquiryQuestion: vi.fn(), readerInquiryQuestionAction: vi.fn(),
  resolveQuestionEvent: vi.fn(), readerInvokePreset: vi.fn(), readerEscalateAuthoredQuestion: vi.fn(),
  readerSearchSources: vi.fn(), readerSetMode: vi.fn(), cancelIngestBatch: vi.fn(),
}));
const flags = vi.hoisted(() => ({ inquiry: true, sources: [] as unknown[] }));
const guide = vi.hoisted(() => ({ plan: { sections: [] as unknown[] } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({
  useCachedQuery: (key: string[]) => ({
    data: key[0] === "reader_prompt_contract"
      ? (flags.inquiry ? { readerEnabled: true, inquiryEnabled: true } : { readerEnabled: true })
      : { sources: flags.sources },
    error: null,
  }),
}));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve(guide.plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const cardA = { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const viewB: ReaderRenderViewDto = {
  ...view, sourceId: "src_b", extractionId: "ext_b",
  blocks: [{ ...view.blocks[0], spanId: "b1", displayNodeId: "node-b1", markdown: "Book B explains eigenvalues another way." }],
};
const cardB = { sourceId: "src_b", title: "Book B", canonicalUri: "b.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const root = {
  eventId: "root", parentExchangeId: null, extractionId: view.extractionId, spanId: "span_symmetric_prose",
  questionMd: "Why weighted by p?", answerMd: "Saved answer", answerMode: "answer_directly", citations: [],
  selectionSpanIds: ["span_symmetric_prose"], selectionQuoteMd: "Saved exact selection", selectionSourceQuoteMd: null,
  createdAt: null, questionEventId: "q_root", resolution: "open",
};
const check = {
  id: "raq_1", extractionId: view.extractionId, sectionId: "u1", status: "proposed", questionMd: "Why is the eigenbasis orthonormal?",
  expectedAnswerMd: "Because A is symmetric.", spanIds: ["span_symmetric_prose"], practiceItemId: null, answeredAt: null,
  scopeKind: "inquiry", questionStyle: "recall", anchorSpanIds: ["span_symmetric_prose"], inquiryRootEventId: "root",
  responseMd: null, selfCheck: null, escalationLearningObjectId: null, model: "gpt-5.6-sol",
  promptVersion: "rw1a-reading-passage-check-v1",
};
const store = new Map<string, string>();
let polls: Array<() => void> = [];

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  flags.inquiry = true;
  flags.sources = [cardA, cardB];
  guide.plan = { sections: [] };
  store.clear();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
      key: () => null,
      length: 0,
    },
  });
  // The quick-check poll runs on a 3 s interval: capture it and run it by hand.
  polls = [];
  const realSetInterval = window.setInterval.bind(window);
  vi.spyOn(window, "setInterval").mockImplementation(((handler: TimerHandler, ms?: number, ...args: unknown[]) => {
    if (ms === 3000) {
      polls.push(handler as () => void);
      return 424242;
    }
    return realSetInterval(handler, ms, ...args);
  }) as typeof window.setInterval);
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (input.extractionId === "src_b" ? viewB : view));
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockImplementation(async (extractionId: string) => ({ exchanges: extractionId === view.extractionId ? [root] : [] }));
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRestoreSource.mockResolvedValue({ eventId: "restored" });
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.cancelIngestBatch.mockResolvedValue({ id: "batch_q", status: "cancelled", jobs: [] });
  api.readerAsk.mockResolvedValue({
    eventId: "q_child", readerAnswerEventId: "child", parentExchangeId: "root", answerMd: "Follow-up answer",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" }, model: "stub-model",
  });
  api.readerReconnectAnswer.mockImplementation(async (input: { answer: string }) => ({
    rootExchangeId: "root", questionEventId: "q_root", answer: input.answer, resolution: "open",
    status: input.answer === "quick_check" ? "queued" : null, batchId: input.answer === "quick_check" ? "batch_q" : null,
    message: null, question: null,
  }));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

async function poll() {
  const latest = polls[polls.length - 1];
  expect(latest).toBeTypeOf("function");
  await act(async () => {
    latest();
    await Promise.resolve();
  });
}

function altArrow(key: "ArrowLeft" | "ArrowRight") {
  act(() => {
    fireEvent.keyDown(window, { key: "Alt", altKey: true });
    fireEvent.keyDown(window, { key, altKey: true });
    fireEvent.keyUp(window, { key, altKey: true });
    fireEvent.keyUp(window, { key: "Alt" });
  });
}

async function askFollowUp(text = "Why does conditioning work?") {
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted by p\?/ }));
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up ↵" }));
  await screen.findByText("Follow-up answer");
}

async function openQuickCheckFromReconnect() {
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  await askFollowUp();
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  const [line] = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  fireEvent.click(within(line).getByRole("button", { name: "quick check" }));
  await waitFor(() => expect(api.readerReconnectAnswer).toHaveBeenCalledWith(expect.objectContaining({ answer: "quick_check" })));
  await screen.findByText(/writing a quick check on this passage/);
}

// jsdom has no layout: keep the reading-position probe from picking the first
// block, so the reading position is the one the learner jumped to.
function stableGeometry() {
  const rect = (top: number, height: number) => ({ top, bottom: top + height, left: 0, right: 100, width: 100, height, x: 0, y: top, toJSON: () => ({}) });
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    return ((this as HTMLElement).dataset?.spanId ? rect(5000, 10) : rect(0, 500)) as DOMRect;
  });
}

function loggedEvents() {
  flushReaderActivity();
  return api.readerLogActivity.mock.calls.flatMap((call) => call[0].events as Array<{ kind: string; event?: string; payload: Record<string, unknown> }>);
}

async function searchAndOpen(query: string, hit: { sourceId: string; sourceTitle: string; extractionId: string; spanId: string; snippet: string }) {
  api.readerSearchSources.mockResolvedValueOnce({ query, hits: [{ ...hit, section: null, page: null }], searchedSources: 2 });
  fireEvent.change(await screen.findByPlaceholderText("search all sources…"), { target: { value: query } });
  fireEvent.click(await screen.findByText(hit.snippet, {}, { timeout: 3000 }));
}

// -- F4 + F8: the queued quick check ------------------------------------------

it("a queued quick check that fails says why in place and records the failure", async () => {
  await openQuickCheckFromReconnect();
  api.readerInquiryQuestion.mockResolvedValueOnce({ question: null, job: { status: "running", errorCode: null, message: null } });
  await poll();
  expect(api.readerInquiryQuestion).toHaveBeenLastCalledWith(expect.objectContaining({ exchangeId: "root", batchId: "batch_q" }));
  expect(screen.getByText(/writing a quick check on this passage/)).toBeTruthy();
  api.readerInquiryQuestion.mockResolvedValueOnce({ question: null, job: { status: "failed", errorCode: "capped", message: "Today's quick checks (100) are used." } });
  await poll();
  expect(await screen.findByText(/Today's quick check budget/)).toBeTruthy();
  expect(screen.queryByText(/writing a quick check on this passage/)).toBeNull();
  const done = loggedEvents().filter((e) => e.kind === "reader_job_completed" && e.payload.job_kind === "quick_check");
  expect(done).toHaveLength(1);
  expect(done[0].payload).toMatchObject({ status: "failed", failure_reason: "capped", job_id: "batch_q" });
});

it("a lost sidecar shows offline instead of waiting forever, and the check lands when it comes back", async () => {
  await openQuickCheckFromReconnect();
  const down = { code: "sidecar_unavailable", message: "The sidecar is not running." };
  api.readerInquiryQuestion.mockRejectedValueOnce(down).mockRejectedValueOnce(down);
  await poll();
  await poll();
  expect(await screen.findByText(/background service isn't responding/)).toBeTruthy();
  // It recovers: the next poll reaches the sidecar and the check has landed.
  api.readerInquiryQuestion.mockResolvedValueOnce({ question: check, job: { status: "completed", errorCode: null, message: null } });
  await poll();
  expect(await screen.findByText("Why is the eigenbasis orthonormal?")).toBeTruthy();
  const events = loggedEvents();
  const queued = events.filter((e) => e.kind === "reader_job_queued" && e.payload.job_kind === "quick_check");
  const completed = events.filter((e) => e.kind === "reader_job_completed" && e.payload.job_kind === "quick_check");
  expect(queued).toHaveLength(1);
  expect(queued[0].payload).toMatchObject({ job_id: "batch_q" });
  expect(queued[0].payload.visit_id).toBeTruthy();
  expect(completed).toHaveLength(1);
  expect(completed[0].payload).toMatchObject({
    status: "completed", job_id: "batch_q", visit_id: queued[0].payload.visit_id,
    model: "gpt-5.6-sol", prompt_version: "rw1a-reading-passage-check-v1",
  });
  expect(typeof completed[0].payload.latency_ms).toBe("number");
  expect(completed[0].payload.activity_during_wait).toBeTypeOf("object");
});

it("a pending quick check can be cancelled: the job is cancelled and the wait recorded", async () => {
  await openQuickCheckFromReconnect();
  fireEvent.click(screen.getByRole("button", { name: "cancel" }));
  await waitFor(() => expect(api.cancelIngestBatch).toHaveBeenCalledWith("batch_q"));
  expect(screen.queryByText(/writing a quick check on this passage/)).toBeNull();
  const done = loggedEvents().filter((e) => e.kind === "reader_job_completed" && e.payload.job_kind === "quick_check");
  expect(done.map((e) => e.payload.status)).toEqual(["cancelled"]);
});

it("a check the model can't be reached for is said in place and recorded as unreachable", async () => {
  api.readerReconnectAnswer.mockImplementation(async (input: { answer: string }) => ({
    rootExchangeId: "root", questionEventId: "q_root", answer: input.answer, resolution: "open",
    status: "provider_unavailable", batchId: null, message: "Codex is not signed in.", question: null,
  }));
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  await askFollowUp();
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  const [line] = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  fireEvent.click(within(line).getByRole("button", { name: "quick check" }));
  expect(await screen.findByText(/Couldn't reach LearnLoop's model/)).toBeTruthy();
  const done = loggedEvents().filter((e) => e.kind === "reader_job_completed" && e.payload.job_kind === "quick_check");
  expect(done.map((e) => [e.payload.status, e.payload.failure_reason])).toEqual([["failed", "unreachable"]]);
});

// -- Re-review F14 + F15: a retry's wait, and which spend refusal it was -------

it("a late poll for an earlier batch never settles the retry's wait", async () => {
  await openQuickCheckFromReconnect();
  let answerLate: (value: unknown) => void = () => undefined;
  api.readerInquiryQuestion.mockReturnValueOnce(new Promise((resolve) => { answerLate = resolve; }));
  await poll(); // batch_q's first poll is still outstanding
  api.readerInquiryQuestion.mockResolvedValueOnce({ question: null, job: { status: "failed", errorCode: "provider_unavailable", message: "down", refusal: null } });
  await poll();
  expect(await screen.findByText(/Couldn't reach LearnLoop's model/)).toBeTruthy();
  // The learner tries again, into batch_b.
  api.readerReconnectAnswer.mockImplementation(async (input: { answer: string }) => ({
    rootExchangeId: "root", questionEventId: "q_root", answer: input.answer, resolution: "open",
    status: "queued", batchId: "batch_b", message: null, question: null,
  }));
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  await screen.findByText(/writing a quick check on this passage/);
  // batch_q's late answer arrives.
  await act(async () => {
    answerLate({ question: null, job: { status: "failed", errorCode: "provider_unavailable", message: "down", refusal: null } });
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  expect(screen.getByText(/writing a quick check on this passage/)).toBeTruthy();
  const settled = (jobId: string) => loggedEvents()
    .filter((e) => e.kind === "reader_job_completed" && e.payload.job_id === jobId)
    .map((e) => e.payload.status);
  expect(settled("batch_b")).toEqual([]);
  // batch_b lands: its own outcome is recorded, once.
  api.readerInquiryQuestion.mockResolvedValueOnce({ question: check, job: { status: "completed", errorCode: null, message: null, refusal: null } });
  await poll();
  expect(await screen.findByText("Why is the eigenbasis orthonormal?")).toBeTruthy();
  const done = loggedEvents().filter((e) => e.kind === "reader_job_completed" && e.payload.job_kind === "quick_check");
  expect(done.map((e) => [e.payload.job_id, e.payload.status])).toEqual([["batch_q", "failed"], ["batch_b", "completed"]]);
});

// Final verification F14: the retry gets the same live batch back (the enqueue
// reuses it), so batch identity alone can't tell the waits apart.
it("a stale timed-out poll never fails a retry that got the same live batch back", async () => {
  await openQuickCheckFromReconnect();
  const running = { question: null, job: { status: "running", errorCode: null, message: null, refusal: null } };
  api.readerInquiryQuestion.mockResolvedValue(running);
  for (let i = 0; i < 200; i += 1) await poll(); // the wait reaches its polling limit
  expect(screen.getByText(/writing a quick check on this passage/)).toBeTruthy();
  // Two polls go out past the limit and stay outstanding.
  const outstanding: Array<(value: unknown) => void> = [];
  api.readerInquiryQuestion.mockImplementation(() => new Promise((resolve) => { outstanding.push(resolve); }));
  const tick = polls[polls.length - 1];
  await act(async () => {
    tick();
    tick();
    await Promise.resolve();
  });
  expect(outstanding).toHaveLength(2);
  // The first answers "running": this wait times out.
  await act(async () => {
    outstanding[0](running);
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  expect(await screen.findByRole("button", { name: "try again ↵" })).toBeTruthy();
  // Try again: the backend hands back the same live batch_q, and a fresh wait starts.
  api.readerInquiryQuestion.mockResolvedValue(running);
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  await screen.findByText(/writing a quick check on this passage/);
  // The older outstanding poll answers "running" with its exhausted counter.
  await act(async () => {
    outstanding[1](running);
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  expect(screen.getByText(/writing a quick check on this passage/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "try again ↵" })).toBeNull();
  const settled = () => loggedEvents()
    .filter((e) => e.kind === "reader_job_completed" && e.payload.job_kind === "quick_check")
    .map((e) => [e.payload.job_id, e.payload.status, e.payload.failure_reason]);
  expect(settled()).toEqual([["batch_q", "failed", "timeout"]]);
  // The retry's own wait still polls and settles once when the check lands.
  api.readerInquiryQuestion.mockResolvedValueOnce({ question: check, job: { status: "completed", errorCode: null, message: null, refusal: null } });
  await poll();
  expect(await screen.findByText("Why is the eigenbasis orthonormal?")).toBeTruthy();
  expect(settled()).toEqual([["batch_q", "failed", "timeout"], ["batch_q", "completed", null]]);
});

it("a check over its per-check spending limit says so, and a missing price says that", async () => {
  await openQuickCheckFromReconnect();
  api.readerInquiryQuestion.mockResolvedValueOnce({
    question: null, job: { status: "failed", errorCode: "spend_refused", message: "estimated_usd exceeds max_estimated_usd", refusal: "over_cap" },
  });
  await poll();
  expect(await screen.findByText(/would cost more than the spending limit for one quick check/)).toBeTruthy();
  expect(screen.queryByText(/no price is set/)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  await screen.findByText(/writing a quick check on this passage/);
  api.readerInquiryQuestion.mockResolvedValueOnce({
    question: null, job: { status: "failed", errorCode: "spend_refused", message: "no price is set", refusal: "no_price" },
  });
  await poll();
  expect(await screen.findByText(/no price is set for this model/)).toBeTruthy();
  expect(screen.queryByText(/spending limit for one quick check/)).toBeNull();
});

// -- F5: the switch off keeps no return stack ---------------------------------

it("with the switch off, a search into another passage of a source left earlier lands and is saved there", async () => {
  flags.inquiry = false;
  stableGeometry();
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_symmetric_prose" }} onError={vi.fn()} />);
  await screen.findAllByText(view.blocks[1].markdown);
  await waitFor(() => expect(store.get(`learnloop.reader.position.${view.sourceId}`)).toBe("span_symmetric_prose"));
  fireEvent.click(screen.getByText("← library"));
  await searchAndOpen("eigen", { sourceId: "src_b", sourceTitle: "Book B", extractionId: "ext_b", spanId: "b1", snippet: "another way" });
  await screen.findAllByText("Book B explains eigenvalues another way.");
  fireEvent.click(screen.getByText("← library"));
  await searchAndOpen("spectral", { sourceId: view.sourceId, sourceTitle: "Matrices", extractionId: view.extractionId, spanId: "span_spectral_worked", snippet: "the spectral hit" });
  await screen.findAllByText(view.blocks[2].markdown);
  await waitFor(() => expect(store.get(`learnloop.reader.position.${view.sourceId}`)).toBe("span_spectral_worked"));
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
  expect(api.readerLogActivity).not.toHaveBeenCalled();
});

// -- F6: every detour has a way back -------------------------------------------

it("a Guide 'worth a second look' passage is a detour: Alt+← restores the passage and the capture", async () => {
  guide.plan = { sections: [{
    id: "u1", label: "Symmetric matrices", startSpanId: view.blocks[0].spanId, endSpanId: view.blocks[2].spanId,
    spanIds: view.blocks.map((b) => b.spanId), question: null,
    suggestedPassages: [{ spanId: view.blocks[0].spanId, quote: "A worth-a-second-look quote", reason: "You missed this.", learningObjectId: "lo", learningObjectTitle: "Symmetry", learnerSignal: "new_material" }],
  }] };
  api.readerGetProgress.mockResolvedValue({ sections: [{ sectionId: "u1", revealedAt: "2026-10-13T00:00:00Z", completedAt: null }] });
  stableGeometry();
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[2].markdown);
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  // The rail opens on the Guide tab.
  fireEvent.click(await screen.findByText(/A worth-a-second-look quote/));
  const strip = await screen.findByRole("navigation", { name: "Detour" });
  // The first crumb is where the learner was: that passage of its section.
  expect(within(strip).getAllByRole("button")[0].textContent).toContain("Symmetric matrices ¶3");
  altArrow("ArrowLeft");
  await waitFor(() => expect(api.readerRestoreSource).toHaveBeenCalledWith(expect.objectContaining({ spanId: "span_spectral_worked" })));
  expect(screen.getAllByText(/^selected ·/).length).toBeGreaterThan(0);
});

it("opening another book from its library card after leaving one leaves a way back", async () => {
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  await screen.findAllByText(view.blocks[2].markdown);
  fireEvent.click(screen.getByText("← library"));
  fireEvent.click(await screen.findByText("Book B"));
  await screen.findAllByText("Book B explains eigenvalues another way.");
  const strip = await screen.findByRole("navigation", { name: "Detour" });
  expect(within(strip).getAllByRole("button").map((b) => b.textContent)).toEqual([expect.stringContaining("Matrices"), "Book B"]);
  altArrow("ArrowLeft");
  await screen.findAllByText(view.blocks[2].markdown);
  await waitFor(() => expect(api.readerRenderView).toHaveBeenLastCalledWith({ extractionId: view.sourceId }));
});

// -- F7: a detour walked back to twice is returned once ------------------------

it("returning, walking forward and returning again records each detour's return once", async () => {
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  await askFollowUp();
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  await screen.findAllByRole("group", { name: "Does this make sense now?" });
  altArrow("ArrowRight");
  altArrow("ArrowRight");
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  await waitFor(() => expect(api.readerRestoreSource).toHaveBeenCalledTimes(2));
  const events = loggedEvents();
  const opened = events.filter((e) => e.event === "detour_opened").map((e) => e.payload.detour_id);
  const returned = events.filter((e) => e.event === "detour_returned").map((e) => e.payload.detour_id);
  expect(opened).toHaveLength(2);
  expect([...returned].sort()).toEqual([...opened].sort());
});

// -- F10: skim mutes a reconnect line already shown ---------------------------

it("choosing skim after the reconnect line appeared hides it in both places", async () => {
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  await askFollowUp();
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  expect((await screen.findAllByRole("group", { name: "Does this make sense now?" })).length).toBe(2);
  const [modeSelect] = screen.getAllByRole("combobox");
  fireEvent.keyDown(modeSelect, { key: "Enter" });
  fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
  await waitFor(() => expect(screen.queryAllByRole("group", { name: "Does this make sense now?" })).toHaveLength(0));
});

// -- F12: an edited capture is the learner's wording ---------------------------

it("an Ask about an edited capture keeps the book's wording apart from the learner's", async () => {
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerAsk.mockResolvedValue({
    eventId: "q_new", readerAnswerEventId: "new", parentExchangeId: null, answerMd: "Answer about the fix",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" }, model: "stub-model",
  });
  render(<ReaderScreen initialSource={{ card: cardA, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  fireEvent.click(await screen.findByRole("button", { name: "edit" }));
  fireEvent.change(screen.getByDisplayValue(view.blocks[1].markdown), { target: { value: "My corrected wording" } });
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  fireEvent.change(await screen.findByPlaceholderText("ask about this passage…"), { target: { value: "Is my fix right?" } });
  fireEvent.click(screen.getByRole("button", { name: "ask ↵" }));
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ selectionQuote: "My corrected wording", selectionSourceQuote: view.blocks[1].markdown });
  await screen.findByText("Answer about the fix");
  const source = document.querySelectorAll('[data-voice="source"]');
  for (const element of Array.from(source)) expect(element.textContent).not.toContain("My corrected wording");
  const learner = Array.from(document.querySelectorAll('[data-voice="learner"]')).map((e) => e.textContent ?? "");
  expect(learner.some((text) => text.includes("edited capture") && text.includes("My corrected wording"))).toBe(true);
});
