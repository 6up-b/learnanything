// RW1a on the real screen (reader_inquiry on): the detour strip and return
// stack (G57), the reconnect line inline and in the rail, inquiry status with
// reopen, a branch marked done, the reconnect quick check with its
// self-check, the static quick-check marker, and the funnel's activity.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../api/dto";
import { flushReaderActivity, resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRestoreSource: vi.fn(), readerSetInquiryStatus: vi.fn(),
  readerReconnectAnswer: vi.fn(), readerInquiryQuestion: vi.fn(), readerInquiryQuestionAction: vi.fn(),
  resolveQuestionEvent: vi.fn(), readerInvokePreset: vi.fn(), readerEscalateAuthoredQuestion: vi.fn(),
}));
const guide = vi.hoisted(() => ({ plan: { sections: [] as unknown[] } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve(guide.plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const root = {
  eventId: "root", parentExchangeId: null, extractionId: view.extractionId, spanId: "span_symmetric_prose",
  questionMd: "Why weighted by p?", answerMd: "Saved answer", answerMode: "answer_directly", citations: [],
  selectionSpanIds: ["span_symmetric_prose"], selectionQuoteMd: "Saved exact selection", createdAt: null,
  questionEventId: "q_root", resolution: "open",
};
const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const check = {
  id: "raq_1", extractionId: view.extractionId, sectionId: "u1", status: "proposed", questionMd: "Why is the eigenbasis orthonormal?",
  expectedAnswerMd: "Because A is symmetric.", spanIds: ["span_symmetric_prose"], practiceItemId: null, answeredAt: null,
  scopeKind: "inquiry", questionStyle: "recall", anchorSpanIds: ["span_symmetric_prose"], inquiryRootEventId: "root",
  responseMd: null, selfCheck: null, escalationLearningObjectId: null,
};

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  guide.plan = { sections: [] };
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [root] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRestoreSource.mockResolvedValue({ eventId: "restored" });
  api.readerAsk.mockResolvedValue({
    eventId: "q_child", readerAnswerEventId: "child", parentExchangeId: "root", answerMd: "Follow-up answer",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" }, model: "stub-model",
  });
  api.readerSetInquiryStatus.mockImplementation(async (input: { resolution: string }) => ({
    rootExchangeId: "root", questionEventId: "q_root", resolution: input.resolution, previousResolution: "open", openCount: 0,
  }));
  api.resolveQuestionEvent.mockResolvedValue({ eventId: "q_child", resolution: "resolved", openCount: 1 });
  api.readerReconnectAnswer.mockImplementation(async (input: { answer: string }) => ({
    rootExchangeId: "root", questionEventId: "q_root", answer: input.answer,
    resolution: input.answer === "yes" ? "resolved" : "open",
    status: input.answer === "quick_check" ? "exists" : null, batchId: null, message: null,
    question: input.answer === "quick_check" ? check : null,
  }));
  api.readerInquiryQuestionAction.mockImplementation(async (input: { action: string; response?: string; selfCheck?: string }) => ({
    question: { ...check, status: "answered", responseMd: "It's symmetric.", selfCheck: input.action === "self_checked" ? input.selfCheck : null },
  }));
});
afterEach(cleanup);

async function openThread() {
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted by p\?/ }));
}

async function askFollowUp(text = "Why does conditioning work?") {
  await openThread();
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up ↵" }));
  await screen.findByText("Follow-up answer");
}

function altArrow(key: "ArrowLeft" | "ArrowRight") {
  act(() => {
    fireEvent.keyDown(window, { key: "Alt", altKey: true });
    fireEvent.keyDown(window, { key, altKey: true });
    fireEvent.keyUp(window, { key, altKey: true });
    fireEvent.keyUp(window, { key: "Alt" });
  });
}

it("a follow-up opens the detour strip and Alt+← walks back to the origin passage and capture", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  // A capture first: it is part of "where I was".
  const block = await screen.findByText(view.blocks[2].markdown);
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  await askFollowUp();
  const strip = await screen.findByRole("navigation", { name: "Detour" });
  const crumbs = within(strip).getAllByRole("button");
  expect(crumbs.map((crumb) => crumb.textContent)).toEqual(["Matrices", "Why weighted by p?", "Why does conditioning work?"]);
  expect(crumbs[2].getAttribute("aria-current")).toBe("location");

  altArrow("ArrowLeft");
  expect(within(screen.getByRole("navigation", { name: "Detour" })).getAllByRole("button")[1].getAttribute("aria-current")).toBe("location");
  expect(screen.queryAllByRole("group", { name: "Does this make sense now?" })).toHaveLength(0);

  altArrow("ArrowLeft");
  // Back at the origin: the capture is restored (K7 kept it through the chord),
  // the source records the restore, and the reconnect line asks inline and in the rail.
  await waitFor(() => expect(api.readerRestoreSource).toHaveBeenCalledTimes(1));
  expect(screen.getAllByText(/^selected ·/).length).toBeGreaterThan(0);
  const lines = screen.getAllByRole("group", { name: "Does this make sense now?" });
  expect(lines.map((line) => line.getAttribute("data-reconnect")).sort()).toEqual(["inline", "rail"]);
  expect(lines[0].textContent).toContain("Why weighted by p?");

  // Alt+→ walks forward again.
  altArrow("ArrowRight");
  expect(within(screen.getByRole("navigation", { name: "Detour" })).getAllByRole("button")[1].getAttribute("aria-current")).toBe("location");
});

it("yes on the reconnect line resolves the root, a self-report", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await askFollowUp();
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  const [line] = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  fireEvent.click(within(line).getByRole("button", { name: "yes" }));
  await waitFor(() => expect(api.readerReconnectAnswer).toHaveBeenCalledWith(expect.objectContaining({ exchangeId: "root", answer: "yes" })));
  await waitFor(() => expect(screen.queryAllByRole("group", { name: "Does this make sense now?" })).toHaveLength(0));
  expect(await screen.findByText("status: resolved")).toBeTruthy();
});

it("status chips set the inquiry's status on its root, and reopen brings it back", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await openThread();
  const chips = screen.getByRole("group", { name: "Inquiry status" });
  expect(within(chips).getByText("status: open")).toBeTruthy();
  fireEvent.click(within(chips).getByRole("button", { name: "resolved" }));
  await waitFor(() => expect(api.readerSetInquiryStatus).toHaveBeenCalledWith(expect.objectContaining({ exchangeId: "root", resolution: "resolved", trigger: "chip" })));
  fireEvent.click(await screen.findByRole("button", { name: "reopen" }));
  await waitFor(() => expect(api.readerSetInquiryStatus).toHaveBeenLastCalledWith(expect.objectContaining({ resolution: "open" })));
  expect(await screen.findByText("status: open")).toBeTruthy();
});

it("revisit once is the existing test_me_later preset on the root's anchor", async () => {
  api.readerInvokePreset.mockResolvedValue({ annotationId: "ann", anchorStatus: "exact", arc: null });
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await openThread();
  fireEvent.click(screen.getByRole("button", { name: "revisit once" }));
  await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledWith(expect.objectContaining({
    preset: "test_me_later", rawSelection: { nodes: [{ spanId: "span_symmetric_prose", start: 0, end: 1_000_000 }] },
  })));
  expect(await screen.findByRole("button", { name: "revisit once ✓" })).toBeTruthy();
});

it("a branch marked done asks the reconnect line in the rail only", async () => {
  api.readerAskHistory.mockResolvedValue({ exchanges: [
    { ...root, eventId: "child", parentExchangeId: "root", questionMd: "Coin flip?", questionEventId: "q_child" }, root,
  ] });
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await openThread();
  fireEvent.click(await screen.findByRole("button", { name: /▸ Coin flip\?/ }));
  fireEvent.click(screen.getByRole("button", { name: "done" }));
  await waitFor(() => expect(api.resolveQuestionEvent).toHaveBeenCalledWith("q_child", "resolved"));
  const lines = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  expect(lines.map((line) => line.getAttribute("data-reconnect"))).toEqual(["rail"]);
});

it("the reconnect quick check lands in the rail, then compares and records the self-check", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  await askFollowUp();
  altArrow("ArrowLeft");
  altArrow("ArrowLeft");
  const [line] = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  fireEvent.click(within(line).getByRole("button", { name: "quick check" }));
  const card = await screen.findByRole("region", { name: "Quick check" });
  expect(within(card).getByText("Why is the eigenbasis orthonormal?")).toBeTruthy();
  fireEvent.change(within(card).getByLabelText("Your answer"), { target: { value: "It's symmetric." } });
  fireEvent.click(within(card).getByRole("button", { name: /compare with the source/ }));
  await waitFor(() => expect(api.readerInquiryQuestionAction).toHaveBeenCalledWith(expect.objectContaining({ action: "answered", response: "It's symmetric." })));
  fireEvent.click(await within(screen.getByRole("region", { name: "Quick check" })).findByRole("button", { name: "partly" }));
  await waitFor(() => expect(api.readerInquiryQuestionAction).toHaveBeenLastCalledWith(expect.objectContaining({ action: "self_checked", selfCheck: "partly" })));
  expect(await screen.findByText(/you said: partly/)).toBeTruthy();
});

it("the quick-check marker on the Guide tab is static: no pulse, no blink, no pinned strip", async () => {
  guide.plan = { sections: [{
    id: "u1", label: "Symmetric matrices", startSpanId: view.blocks[0].spanId, endSpanId: view.blocks[2].spanId,
    spanIds: view.blocks.map((b) => b.spanId), suggestedPassages: [],
    question: { authoredQuestionId: "raq_s", placement: "auto_authored", readingPhase: "after_section", prompt: "Q?", expectedAnswer: "A.", spanIds: [], reason: "r" },
  }] };
  const { container } = render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  const guideTab = await screen.findByRole("button", { name: /^Guide, 1 quick check waiting$/ });
  expect(guideTab.textContent).toContain("◆ 1");
  expect(container.querySelector(".ll-reader-guide-alert, .ll-qc-blink, .ll-reader-qc-strip")).toBeNull();
  expect(screen.queryByText(/quick check ready/i)).toBeNull();
});

it("records the funnel: a visit, the selection, the ask and its job, never the learner's words", async () => {
  const { unmount } = render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  await askFollowUp("My private words");
  unmount();
  flushReaderActivity();
  const events = api.readerLogActivity.mock.calls.flatMap((call) => call[0].events as Array<{ kind: string; event?: string; payload: Record<string, unknown> }>);
  const kinds = events.map((e) => `${e.kind}${e.event ? `:${e.event}` : ""}`);
  for (const expected of [
    "reader_view_opened", "reader_selection", "reader_action_invoked:action_invoked",
    "reader_job_queued", "reader_job_completed", "reader_action_invoked:detour_opened", "reader_view_closed",
  ]) expect(kinds).toContain(expected);
  const completed = events.find((e) => e.kind === "reader_job_completed")!;
  expect(completed.payload).toMatchObject({ job_kind: "follow_up", status: "completed", model: "stub-model", prompt_version: "p3-reader-branches-v1" });
  expect(JSON.stringify(events)).not.toContain("My private words");
  expect(JSON.stringify(events)).not.toContain(view.blocks[1].markdown);
});
