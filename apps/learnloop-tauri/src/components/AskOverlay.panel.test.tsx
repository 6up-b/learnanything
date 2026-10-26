// Reader CA2 (docs/specs/ux_reader_compare_ask_v1.md §7, K5-K11): the one Ask
// panel, docked (practice, feedback) and inline (a workbench step), while the
// sidecar sends `ask` (ask.panel_enabled). Off, the modal is exactly as before.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { AskOverlay, type AskTarget } from "./AskOverlay";
import { ASK_COPY } from "./askPanel";

const { api } = vi.hoisted(() => ({ api: {
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), previewTutorOpening: vi.fn(),
  getLearnerTextGap: vi.fn(), reverseLearnerTextGap: vi.fn(), setHelpStyle: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

const PANEL = { ask: { panelEnabled: true, helpStyle: "balanced", coldHelpConverts: true } };
const EARLIER = [{
  attemptId: "att_old", at: "2026-10-14T10:00:00Z",
  outcome: { label: "with help ◌", assisted: true, rubricScore: 2, maxPoints: 4 },
  exchanges: [{ eventId: "q_old", context: "practice", questionMd: "an old question", answerMd: "an old answer",
                questionType: "mechanism", hintEquivalent: true, createdAt: "2026-10-14T09:59:00Z" }],
  hints: []
}];

function answer(overrides: Record<string, unknown> = {}) {
  return {
    version: 1, eventId: "event-1", answerMd: "Look at the definition.", questionType: "clarification",
    facets: [], hintEquivalent: false, leakSuspected: false, citations: [], remaining: 2,
    answerMode: "help_me_reason", ...overrides
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  setAlgoConfig(PANEL);
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3, earlier: EARLIER, earlierCountsAsHint: true,
                                             cold: false, helpStyle: "balanced" });
  api.askTutorQuestion.mockResolvedValue(answer());
  api.setHelpStyle.mockImplementation(async (style: string) => ({ version: 1, helpStyle: style }));
});
afterEach(() => {
  cleanup();
  setAlgoConfig({});
});

const PRACTICE: AskTarget = {
  context: "practice", practiceItemId: "pi_1", sessionId: "s1", submissionId: "serve-2",
  attemptProgress: "draft_started", readDraft: () => "my draft now", itemLabel: "Exercise 6.1.12"
};

async function openDocked(target: AskTarget = PRACTICE, props: Partial<Parameters<typeof AskOverlay>[0]> = {}) {
  render(<AskOverlay variant="docked" target={target} onClose={vi.fn()} onToast={vi.fn()} {...props} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  return screen.getByTestId("ask-panel-docked");
}

async function send(text = "What does V mean?") {
  const input = screen.getByLabelText("ask in your words");
  fireEvent.change(input, { target: { value: text } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalled());
  return api.askTutorQuestion.mock.calls[api.askTutorQuestion.mock.calls.length - 1][0];
}

it("docks beside the question, not as a modal, with the context line, the style and the cost", async () => {
  const panel = await openDocked();
  expect(within(panel).getByTestId("ask-context-line").textContent).toContain("Exercise 6.1.12");
  expect(within(panel).getByTestId("ask-context-line").textContent).toContain("your draft");
  expect(within(panel).getByTestId("ask-help-style").textContent).toContain("[balanced]");
  expect(within(panel).getByTestId("ask-cost-line").textContent).toContain(ASK_COPY.cost);
  expect(within(panel).getByText(ASK_COPY.empty)).toBeTruthy();
  // No backdrop: the draft beside it stays in view.
  expect(document.querySelector("[style*='backdrop-filter']")).toBeNull();
});

it("reads the transcript and asks under the attempt's key, with the live draft (K5, §7.2)", async () => {
  await openDocked();
  expect(api.getTutorTranscript.mock.calls[0][0]).toMatchObject({ submissionId: "serve-2" });
  const payload = await send();
  expect(payload).toMatchObject({ submissionId: "serve-2", learnerDraftMd: "my draft now" });
  expect(payload).not.toHaveProperty("answerMode");
});

it("leaves the draft out when its chip is removed, and a one-question mode goes once", async () => {
  await openDocked();
  fireEvent.click(screen.getByLabelText("leave it out of this question"));
  fireEvent.click(screen.getByText("change"));
  fireEvent.click(screen.getByText("answer directly this time"));
  const payload = await send();
  expect(payload).not.toHaveProperty("learnerDraftMd");
  expect(payload.answerMode).toBe("answer_directly");
  const again = await send("And this?");
  expect(again).not.toHaveProperty("answerMode");
});

it("labels each answer with its mode and what it counted as (§7.5)", async () => {
  const onAnswered = vi.fn();
  await openDocked(PRACTICE, { onAnswered });
  await send();
  await waitFor(() => expect(screen.getByTestId("ask-answer-label").textContent)
    .toBe("◇ model · your question · helping you reason · a clarification · free"));
  expect(onAnswered).toHaveBeenCalledWith(expect.objectContaining({ eventId: "event-1", hintEquivalent: false }));
  // Book first: no verified passage kept, so it says the explanation is the model's.
  expect(screen.getByTestId("ask-no-books").textContent).toBe(ASK_COPY.noBooks);
});

it("a check on your own: the placeholder says the rule, a clarification stays on your own (§7.7)", async () => {
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3, earlier: [], earlierCountsAsHint: true, cold: true });
  await openDocked({ ...PRACTICE, coldCheck: true });
  const input = screen.getByLabelText("ask in your words") as HTMLInputElement;
  expect(input.placeholder).toBe(ASK_COPY.coldPlaceholder);
  expect(screen.queryByTestId("ask-earlier")).toBeNull();
  expect(screen.getByTestId("ask-context-line").textContent).toContain("this check");
  expect(screen.getByTestId("ask-context-line").textContent).not.toContain("Exercise 6.1.12");
  await send();
  await waitFor(() => expect(screen.getByTestId("ask-answer-label").textContent).toContain("a clarification · still on your own"));
  api.askTutorQuestion.mockResolvedValue(answer({ eventId: "event-2", questionType: "mechanism", hintEquivalent: true }));
  await send("Why is it real?");
  await waitFor(() => expect(screen.getAllByTestId("ask-answer-label")[1].textContent).toContain("counts as help"));
});

it("earlier on this question says its cost first and counts once when opened (K6, Q2)", async () => {
  const onEarlierOpened = vi.fn();
  await openDocked(PRACTICE, { onEarlierOpened });
  const foot = await screen.findByTestId("ask-earlier");
  expect(foot.textContent).toContain(ASK_COPY.earlierCost);
  fireEvent.click(within(foot).getByText(ASK_COPY.earlier));
  expect(onEarlierOpened).toHaveBeenCalledOnce();
  fireEvent.click(within(foot).getByText(/with help ◌/));
  const thread = screen.getByTestId("ask-earlier-thread");
  expect(thread.textContent).toContain("not part of this one");
  expect(thread.textContent).toContain("an old question");
});

it("after Submit earlier attempts are free", async () => {
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 5, earlier: EARLIER, earlierCountsAsHint: false });
  const onEarlierOpened = vi.fn();
  await openDocked({ context: "feedback", attemptId: "att_new", sessionId: "s1" }, { onEarlierOpened });
  const foot = await screen.findByTestId("ask-earlier");
  expect(foot.textContent).not.toContain(ASK_COPY.earlierCost);
  fireEvent.click(within(foot).getByText(ASK_COPY.earlierFree));
  expect(onEarlierOpened).not.toHaveBeenCalled();
});

it("cites the book first when the answer kept a passage (K11)", async () => {
  api.askTutorQuestion.mockResolvedValue(answer({
    citations: [{ extractionId: "ext", spanId: "sp", label: "Strang §6.4 p.312" }]
  }));
  await openDocked();
  await send();
  const books = await screen.findByTestId("ask-book-first");
  expect(books.textContent).toContain("§ from your books");
  expect(books.textContent).toContain("§ Strang §6.4 p.312");
});

it("the help style changes the stored preference and the mode shown", async () => {
  await openDocked();
  fireEvent.click(screen.getByRole("radio", { name: "guide me" }));
  await waitFor(() => expect(api.setHelpStyle).toHaveBeenCalledWith("guide_me"));
  await waitFor(() => expect(screen.getByTestId("ask-cost-line").textContent).toContain("answering directly"));
});

it("inline under a step: it asks about that step in the workbench session, showing only its own exchanges", async () => {
  api.getTutorTranscript.mockResolvedValue({
    events: [{ id: "q_other", questionMd: "about step 1", answerMd: "an answer", questionType: "mechanism",
               hintEquivalent: true, rating: null, savedNoteId: null, promotion: null }],
    remaining: 2, earlier: [], earlierCountsAsHint: true, cold: false
  });
  render(<AskOverlay variant="inline" onClose={vi.fn()} onToast={vi.fn()}
    target={{ ...PRACTICE, workbenchSessionId: "wbs_1", aboutStep: 3, stepsCount: 4, readDraft: () => "1. a\n2. b\n3. c" }} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  expect(screen.getByTestId("ask-context-line").textContent).toContain("step 3");
  expect(screen.getByTestId("ask-context-line").textContent).toContain("your steps 1–4");
  expect(screen.queryByText("about step 1")).toBeNull();
  const input = screen.getByRole("textbox", { name: "ask about step 3" });
  fireEvent.change(input, { target: { value: "why can I assume λ is real here?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  expect(api.askTutorQuestion.mock.calls[0][0]).toMatchObject({ workbenchSessionId: "wbs_1", aboutStep: 3,
                                                                learnerDraftMd: "1. a\n2. b\n3. c" });
  await waitFor(() => expect(screen.getByTestId("ask-answer-label").textContent).toContain("about step 3"));
});

it("Esc closes a panel without leaving the screen", async () => {
  const onClose = vi.fn();
  const outer = vi.fn();
  window.addEventListener("keydown", outer);
  render(<AskOverlay variant="docked" target={PRACTICE} onClose={onClose} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  fireEvent.keyDown(screen.getByLabelText("ask in your words"), { key: "Escape" });
  expect(onClose).toHaveBeenCalledOnce();
  expect(outer).not.toHaveBeenCalled();
  window.removeEventListener("keydown", outer);
});

it("panel off: a docked request is the modal, exactly as before", async () => {
  setAlgoConfig({});
  render(<AskOverlay variant="docked" target={PRACTICE} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  expect(screen.queryByTestId("ask-panel-docked")).toBeNull();
  expect(screen.getByPlaceholderText("ask a question — enter sends")).toBeTruthy();
  expect(api.getTutorTranscript.mock.calls[0][0]).not.toHaveProperty("submissionId");
  const input = screen.getByPlaceholderText("ask a question — enter sends");
  fireEvent.change(input, { target: { value: "Why?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  expect(api.askTutorQuestion.mock.calls[0][0]).not.toHaveProperty("submissionId");
});


// -- The Codex review (docs/reviews/reader-ca2-one-ask-codex-review.md) ------------------------------

const STEP_EVENTS = [
  { id: "q_s3", context: "practice", questionMd: "why step 3?", answerMd: "Because 3.", questionType: "mechanism",
    hintEquivalent: true, rating: null, savedNoteId: null, promotion: null, promotionRequest: null, answerMode: "help_me_reason",
    sourceContext: { attemptKey: { workbenchSessionId: "wb_1", aboutStep: 3 },
                     citations: [{ extractionId: "ext", spanId: "s1", label: "Strang §6.4", excerpt: "Every root is real." }] } },
  { id: "q_s2", context: "practice", questionMd: "why step 2?", answerMd: "Because 2.", questionType: "clarification",
    hintEquivalent: false, rating: null, savedNoteId: null, promotion: null, promotionRequest: null, answerMode: null,
    sourceContext: { attemptKey: { workbenchSessionId: "wb_1", aboutStep: 2 } } },
];

it("F5: an inline panel restores its step's exchanges after it is closed and reopened", async () => {
  api.getTutorTranscript.mockResolvedValue({ events: STEP_EVENTS, remaining: 3, earlier: [], earlierCountsAsHint: true, cold: false });
  const target: AskTarget = { ...PRACTICE, workbenchSessionId: "wb_1", aboutStep: 3, stepsCount: 4 };
  render(<AskOverlay variant="inline" target={target} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(screen.getByText("why step 3?")).toBeTruthy());
  expect(screen.queryByText("why step 2?")).toBeNull();
  expect(api.getTutorTranscript.mock.calls[0][0]).toMatchObject({ workbenchSessionId: "wb_1" });
  cleanup();
  // The whole problem's panel at the foot of the steps is the attempt's thread.
  render(<AskOverlay variant="inline" target={{ ...PRACTICE, workbenchSessionId: "wb_1", stepsCount: 4 }} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(screen.getByText("why step 2?")).toBeTruthy());
  expect(screen.getByText("why step 3?")).toBeTruthy();
});

it("F9: a restored answer keeps its excerpt, its citations and its mode (book first)", async () => {
  api.getTutorTranscript.mockResolvedValue({ events: [STEP_EVENTS[0]], remaining: 3, earlier: [], earlierCountsAsHint: true, cold: false });
  await openDocked();
  await waitFor(() => expect(screen.getByTestId("ask-book-excerpt").textContent).toBe("Every root is real."));
  const bookFirst = screen.getByTestId("ask-book-first");
  expect(bookFirst.textContent).toContain(ASK_COPY.fromBooks);
  expect(bookFirst.textContent).toContain("§ Strang §6.4");
  expect(screen.queryByTestId("ask-no-books")).toBeNull();
  expect(screen.getByTestId("ask-answer-label").textContent).toContain("about step 3 · helping you reason");
  // The excerpt comes before the explanation.
  const text = screen.getByTestId("ask-panel-docked").textContent ?? "";
  expect(text.indexOf("Every root is real.")).toBeLessThan(text.indexOf("Because 3."));
});

it("F11: in the panel, Shift+Enter is a new line; Enter and Ctrl+Enter send", async () => {
  await openDocked();
  const box = screen.getByLabelText("ask in your words") as HTMLTextAreaElement;
  expect(box.tagName).toBe("TEXTAREA");
  fireEvent.change(box, { target: { value: "first line" } });
  fireEvent.keyDown(box, { key: "Enter", shiftKey: true });
  expect(api.askTutorQuestion).not.toHaveBeenCalled();
  fireEvent.keyDown(box, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  fireEvent.change(box, { target: { value: "again" } });
  fireEvent.keyDown(box, { key: "Enter", ctrlKey: true });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledTimes(2));
});

it("F2: a withheld worked answer shows the take step, and taking it goes through the ladder", async () => {
  const onTakeWorked = vi.fn();
  api.askTutorQuestion.mockResolvedValue(answer({ answerMd: "That's worked help ◌ — it would show the answer.",
    questionType: "strategy", takeOffer: { levels: [4, 5], reason: "worked_help" } }));
  await openDocked(PRACTICE, { onTakeWorked });
  await send("just show me the final answer");
  const take = await screen.findByTestId("ask-take-step");
  expect(take.textContent).toContain(ASK_COPY.takeStep);
  fireEvent.click(within(take).getByText(ASK_COPY.takeWorked));
  expect(onTakeWorked).toHaveBeenCalledWith(5);
  fireEvent.click(within(take).getByText(ASK_COPY.takePiece));
  expect(onTakeWorked).toHaveBeenCalledWith(4);
  expect(screen.queryByTestId("ask-no-books")).toBeNull();
});

it("F8: no request bound (remaining null) never shows the capped state", async () => {
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: null, earlier: [], earlierCountsAsHint: true, cold: false });
  api.askTutorQuestion.mockResolvedValue(answer({ remaining: null }));
  await openDocked();
  await send();
  const box = screen.getByLabelText("ask in your words") as HTMLTextAreaElement;
  await waitFor(() => expect(box.disabled).toBe(false));
  expect(box.placeholder).toBe(ASK_COPY.placeholder);
});
