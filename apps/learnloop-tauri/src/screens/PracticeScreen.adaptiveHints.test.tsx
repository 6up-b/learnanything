// Adaptive hints H2b (spec_adaptive_hints_v1 §4.8, §11 H2 vitest list): the
// practice screen's hint panel over H2a's RPCs. The clickable control and its
// shortcut; "Writing a hint for your work…" then the hint; labels; the quiet
// lines and the feedback box with its shortcuts and the draft selection; the
// worked-help picks; the discriminating question's own answer box; cancel and
// the authored offer; status `disabled` keeping today's path; the
// diagnostic block's refusal unchanged; the "⋯" help-style menu. Every RPC is
// a mock (no sidecar).
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { algoConfig, setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn(),
  requestHint: vi.fn(), hintJob: vi.fn(), cancelHint: vi.fn(), answerDiscriminating: vi.fn(), setHelpStyle: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({
  MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean; placeholder?: string }) => (
    <textarea aria-label="answer" placeholder={props.placeholder} value={props.value} disabled={props.disabled}
      onChange={(event) => props.onChange(event.target.value)} />
  )
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => <span>card controls</span> }));

const ITEM_ID = "pi_hints";
const DRAFT = "F(x) = x^2 on [0, 1]\nso P = F(1/2) + 1";
const PICKS = [
  { level: 4, label: "work a piece of it for me", workedHelp: "worked help ◌",
    consequence: "Counts as worked help: this answer will not count as done on your own." },
  { level: 5, label: "show me the worked answer", workedHelp: "worked help ◌",
    consequence: "Counts as worked help: this answer will not count as done on your own." }
];

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: ITEM_ID, learningObjectId: "lo_det", learningObjectTitle: "Determinants", subject: "linear_algebra",
    subjects: ["linear_algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Compute det(A).", label: null }] },
    prompt: "Compute det(A).", expectedAnswer: "det(A) = -3.",
    hints: ["Start with the first row.", "Watch the signs."],
    hintPolicy: { maxUsefulHints: 2 }, candidateErrorTypes: [], tags: [], sourceRefs: [],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 4, criteria: [{ id: "value", description: "Gets -3", points: 4 }], fatalErrors: [] },
    mastery: { mean: 0.5, variance: 0.18 }, elicitation: null,
    ...overrides
  };
}

function ready(overrides: Record<string, unknown> = {}) {
  return {
    status: "ready", assistId: "ha_1", hintMd: "Evaluate your CDF at the point.", kind: "next_step", level: 3,
    labels: { origin: "AI-written", kind: "the next step", workedHelp: null, horizon: null },
    evidence: { countsAsHint: true, primed: false, level: 3 }, replies: ["doesnt_connect", "book_way"],
    picks: PICKS, shown: true, ...overrides
  };
}

const pending = (jobId = "hjob_1") => ({ version: 1, jobId, state: "pending", result: null });
const done = (result: Record<string, unknown>, jobId = "hjob_1") => ({ version: 1, jobId, state: "done", result });

function props(): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn()
  };
}

function adaptiveOn(mode: "simple" | "classic" = "classic", offerAfter = 4) {
  setAlgoConfig({ ui: { practiceFeedback: mode }, hints: { adaptiveEnabled: true, authoredOfferAfterSeconds: offerAfter, helpStyle: "balanced" } });
}

async function open(callbacks = props()) {
  render(<PracticeScreen {...callbacks} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  fireEvent.change(answer, { target: { value: DRAFT } });
  return callbacks;
}

function pressHint() {
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.recordHintReveal.mockResolvedValue({ version: 1, recorded: true, reason: null, assistId: "ha_client" });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("makes ^h hint a control with the same label and key: a click and Ctrl+H both ask the service, after flushing the draft", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValue(done(ready()));
  await open();
  const control = screen.getByRole("button", { name: "^h hint" });
  expect(control.className).toBe("keybar-control");
  fireEvent.click(control);
  await screen.findByText("Evaluate your CDF at the point.");
  expect(api.savePracticeDraft).toHaveBeenCalled();
  const flushes = api.savePracticeDraft.mock.invocationCallOrder;
  const flushedAt = flushes[flushes.length - 1];
  expect(flushedAt).toBeLessThan(api.requestHint.mock.invocationCallOrder[0]);
  expect(api.requestHint.mock.calls[0][0]).toMatchObject({
    sessionId: "s1", practiceItemId: ITEM_ID, request: "more", answerMd: DRAFT
  });
  expect(typeof api.requestHint.mock.calls[0][0].submissionId).toBe("string");
  api.requestHint.mockResolvedValue(done(ready({ assistId: "ha_2", hintMd: "Second." })));
  pressHint();
  await screen.findByText("Second.");
  expect(api.requestHint).toHaveBeenCalledTimes(2);
  // The client counts no service hint: no telemetry reveal was recorded.
  expect(api.recordHintReveal).not.toHaveBeenCalled();
});

it("offers the hint on an item with no authored hints too, in the plain card's key bar and its Hint button", async () => {
  adaptiveOn("simple");
  api.getPracticeItem.mockResolvedValue(item({ hints: [], hintPolicy: { maxUsefulHints: 0 } }));
  api.requestHint.mockResolvedValue(done(ready()));
  await open();
  expect(screen.getByRole("button", { name: "^h hint" })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Hint" }));
  await screen.findByText("Evaluate your CDF at the point.");
  expect(screen.getByRole("button", { name: "Hint again" })).toBeTruthy();
});

it("shows 'Writing a hint for your work…' while the job is pending, then exactly the hint the read delivered", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValue(pending());
  api.hintJob.mockResolvedValueOnce(pending()).mockResolvedValue(done(ready()));
  await open();
  pressHint();
  expect(await screen.findByText("Writing a hint for your work…")).toBeTruthy();
  await screen.findByText("Evaluate your CDF at the point.", undefined, { timeout: 3000 });
  expect(screen.queryByText("Writing a hint for your work…")).toBeNull();
  expect(api.hintJob).toHaveBeenCalledTimes(2);
  expect(api.hintJob).toHaveBeenCalledWith("hjob_1");
  expect(screen.getByTestId("hint-labels").textContent).toBe("AI-written · the next step");
});

it("labels each hint honestly and keeps earlier hints in order", async () => {
  adaptiveOn();
  api.requestHint
    .mockResolvedValueOnce(done(ready({ assistId: "ha_w", kind: "waypoint", hintMd: "Aim for F(1/2).",
      labels: { origin: "AI-written", kind: "a goal to aim for", horizon: "about two steps ahead", workedHelp: null },
      replies: ["smaller_step", "doesnt_connect", "book_way"] })))
    .mockResolvedValueOnce(done(ready({ assistId: "ha_a", kind: "authored", authoredIndex: 0, hintMd: "Start with the first row.",
      labels: { origin: "from the item", kind: "from the item", horizon: null, workedHelp: null } })))
    .mockResolvedValueOnce(done(ready({ assistId: "ha_c", kind: "continuation", level: 4, hintMd: "Integrate the density.",
      labels: { origin: "AI-written", kind: "the next part, written for you", horizon: null, workedHelp: "worked help ◌" } })));
  await open();
  for (const text of ["Aim for F(1/2).", "Start with the first row.", "Integrate the density."]) {
    pressHint();
    await screen.findByText(text);
  }
  const labels = screen.getAllByTestId("hint-labels").map((node) => node.textContent);
  expect(labels).toEqual([
    "AI-written · a goal to aim for · about two steps ahead",
    "from the item",
    "AI-written · the next part, written for you · worked help ◌"
  ]);
  // Under a goal to aim for, first "a smaller step toward this goal".
  const [waypointLine, authoredLine] = screen.getAllByTestId("hint-replies");
  expect(waypointLine.textContent).toBe("a smaller step toward this goal · this doesn't connect to my work… · show me the book's way");
  expect(authoredLine.textContent).toBe("this doesn't connect to my work… · show me the book's way");
});

it("asks for the book's way and a smaller step on the answered hint", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_w", kind: "waypoint", hintMd: "Aim for F(1/2).",
    labels: { origin: "AI-written", kind: "a goal to aim for", horizon: "about two steps ahead" },
    replies: ["smaller_step", "doesnt_connect", "book_way"] })));
  await open();
  pressHint();
  await screen.findByText("Aim for F(1/2).");
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_s", hintMd: "Smaller." })));
  fireEvent.click(screen.getByRole("button", { name: "a smaller step toward this goal" }));
  await screen.findByText("Smaller.");
  expect(api.requestHint.mock.calls[1][0]).toMatchObject({ request: "smaller_step", answeredAssistId: "ha_w" });
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_b", hintMd: "The book's." })));
  fireEvent.click(within(screen.getAllByTestId("hint-entry")[1]).getByRole("button", { name: "show me the book's way" }));
  await screen.findByText("The book's.");
  expect(api.requestHint.mock.calls[2][0]).toMatchObject({ request: "book_way", answeredAssistId: "ha_s" });
});

it("opens the feedback box: the four shortcuts say what they do, 'not where I'm stuck' picks lines of the draft", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done(ready()));
  await open();
  pressHint();
  await screen.findByText("Evaluate your CDF at the point.");
  fireEvent.click(screen.getByRole("button", { name: "this doesn't connect to my work…" }));
  const box = screen.getByTestId("hint-feedback");
  const shortcuts = within(box).getByRole("group", { name: "what didn't connect" });
  expect(within(shortcuts).getAllByRole("button").map((node) => node.textContent)).toEqual([
    "that's not where I'm stuck — the next hint moves to the part you pick, starting from what stands before it",
    "too big a jump — the next hint takes a smaller step: a nearer goal, or the next step itself",
    "I'm using a different approach — the next hint stays on your route and says which part of your work it builds on",
    "the notation — the next hint says the same thing again in your symbols"
  ]);
  fireEvent.click(within(shortcuts).getAllByRole("button")[0]);
  const lines = within(box).getByTestId("hint-feedback-lines");
  fireEvent.click(within(lines).getByRole("button", { name: "so P = F(1/2) + 1" }));
  fireEvent.change(within(box).getByRole("textbox", { name: "say more (optional)" }), { target: { value: "the +1 part" } });
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_2", hintMd: "Moved." })));
  fireEvent.click(within(box).getByRole("button", { name: "↵ next hint" }));
  await screen.findByText("Moved.");
  expect(api.requestHint.mock.calls[1][0]).toMatchObject({
    request: "feedback", answeredAssistId: "ha_1", feedbackShortcut: "not_where_stuck",
    feedbackSelection: "so P = F(1/2) + 1", feedbackText: "the +1 part"
  });
  expect(screen.queryByTestId("hint-feedback")).toBeNull();
});

it("allows an empty reply: the next hint is requested at once with no shortcut and no text", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done(ready()));
  await open();
  pressHint();
  await screen.findByText("Evaluate your CDF at the point.");
  fireEvent.click(screen.getByRole("button", { name: "this doesn't connect to my work…" }));
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_2", hintMd: "Again." })));
  fireEvent.keyDown(screen.getByRole("textbox", { name: "say more (optional)" }), { key: "Enter" });
  await screen.findByText("Again.");
  const sent = api.requestHint.mock.calls[1][0];
  expect(sent).toMatchObject({ request: "feedback", answeredAssistId: "ha_1" });
  expect(sent).not.toHaveProperty("feedbackShortcut");
  expect(sent).not.toHaveProperty("feedbackText");
  expect(sent).not.toHaveProperty("feedbackSelection");
});

it("offers worked help only as labelled picks in the panel, the consequence stated before it is taken", async () => {
  adaptiveOn();
  await open();
  expect(screen.queryByTestId("hint-picks")).toBeNull();
  api.requestHint.mockResolvedValueOnce(done(ready()));
  pressHint();
  await screen.findByText("Evaluate your CDF at the point.");
  const picks = screen.getByTestId("hint-picks");
  expect(picks.textContent).toContain("work a piece of it for me · worked help ◌ — Counts as worked help");
  expect(picks.textContent).toContain("show me the worked answer · worked help ◌ — Counts as worked help");
  // A plain press never asks for a level.
  expect(api.requestHint.mock.calls[0][0]).not.toHaveProperty("takenLevel");
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_4", kind: "worked_chunk", level: 4, hintMd: "A piece." })));
  fireEvent.click(within(picks).getByRole("button", { name: "work a piece of it for me · worked help ◌" }));
  await screen.findByText("A piece.");
  expect(api.requestHint.mock.calls[1][0]).toMatchObject({ request: "more", takenLevel: 4 });
});

it("asks a discriminating question in its own one-line box, never the answer draft, then shows what it settled", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done(ready({
    assistId: "ha_d", kind: "discriminating", level: 1, hintMd: "What does your formula give at x = 0?",
    labels: { origin: "AI-written", kind: "a question that tells apart two explanations" },
    discriminating: { rivals: [{ id: "r1", status: "candidate" }, { id: "r2", status: "candidate" }],
      predictedAnswers: [{ rivalId: "r1", answer: "0" }, { rivalId: "r2", answer: "1" }], eigNats: 0.69,
      weightsBasis: "uniform", answerBox: true }
  })));
  api.answerDiscriminating.mockResolvedValue({ version: 1, recorded: true, assistId: "ha_ans", settled: true,
    message: "That fits one reading more than the other; the next hint uses it." });
  await open();
  pressHint();
  await screen.findByText("What does your formula give at x = 0?");
  expect(screen.getByTestId("hint-labels").textContent).toBe(
    "AI-written · a question that tells apart two explanations · not graded · counts as a hint");
  const entry = screen.getByTestId("hint-entry");
  expect(within(entry).getByText("↵ answer")).toBeTruthy();
  expect(within(entry).getByText("skip to a hint")).toBeTruthy();
  const box = within(entry).getByRole("textbox", { name: "your answer to this question" });
  fireEvent.change(box, { target: { value: "1" } });
  fireEvent.keyDown(box, { key: "Enter" });
  await screen.findByText("That fits one reading more than the other; the next hint uses it.");
  expect(api.answerDiscriminating).toHaveBeenCalledWith({
    sessionId: "s1", practiceItemId: ITEM_ID, submissionId: expect.any(String), questionAssistId: "ha_d", answerMd: "1"
  });
  // The answer draft is untouched, and no draft save ever carried the answer.
  expect((screen.getByRole("textbox", { name: "answer" }) as HTMLTextAreaElement).value).toBe(DRAFT);
  for (const [draft] of api.savePracticeDraft.mock.calls) expect(draft.answerMd).not.toBe("1");
  // "skip to a hint" asks for the next hint instead.
});

it("skip to a hint asks for the next hint without answering", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done(ready({
    assistId: "ha_d", kind: "discriminating", level: 1, hintMd: "Q?",
    labels: { origin: "AI-written", kind: "a question that tells apart two explanations" },
    discriminating: { rivals: [], predictedAnswers: [], eigNats: 0.5, weightsBasis: "uniform", answerBox: true }
  })));
  await open();
  pressHint();
  await screen.findByText("Q?");
  api.requestHint.mockResolvedValueOnce(done(ready({ assistId: "ha_n", hintMd: "Next." })));
  fireEvent.click(screen.getByRole("button", { name: "skip to a hint" }));
  await screen.findByText("Next.");
  expect(api.requestHint.mock.calls[1][0]).toMatchObject({ request: "more" });
  expect(api.answerDiscriminating).not.toHaveBeenCalled();
});

it("offers the item's own hint after the offer time: cancel first, then the client's reveal; one hint recorded", async () => {
  adaptiveOn("classic", 0.05);
  api.requestHint.mockResolvedValue(pending());
  api.hintJob.mockResolvedValue(pending());
  api.cancelHint.mockResolvedValue({ version: 1, jobId: "hjob_1", state: "cancelled", cancelled: true, reason: null });
  await open();
  pressHint();
  const offer = await screen.findByRole("button", { name: "use the item's hint instead" });
  fireEvent.click(offer);
  await screen.findByText("Start with the first row.");
  expect(api.cancelHint).toHaveBeenCalledWith("hjob_1");
  expect(api.cancelHint.mock.invocationCallOrder[0]).toBeLessThan(api.recordHintReveal.mock.invocationCallOrder[0]);
  expect(api.recordHintReveal).toHaveBeenCalledTimes(1);
  expect(api.recordHintReveal.mock.calls[0][0]).toMatchObject({ authoredIndex: 0, sessionId: "s1", practiceItemId: ITEM_ID });
  expect(screen.queryByText("Writing a hint for your work…")).toBeNull();
  expect(screen.getByTestId("hint-labels").textContent).toBe("from the item");
  // Shown once (in the panel), never also as a legacy banner.
  expect(screen.getAllByText("Start with the first row.")).toHaveLength(1);
  const polls = api.hintJob.mock.calls.length;
  await new Promise((resolve) => setTimeout(resolve, 900));
  expect(api.hintJob.mock.calls.length).toBe(polls);
  // The client counts it at submit, as before.
  api.submitAttempt.mockResolvedValue({ attemptId: "att-1", learningObjectId: "lo_det", probeEpisode: { feedbackDeferred: false } });
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  expect(api.submitAttempt.mock.calls[0][0].hintsUsed).toBe(1);
});

it("keeps the adaptive hint when the cancel answers already_shown, and reveals nothing else", async () => {
  adaptiveOn("classic", 0.05);
  api.requestHint.mockResolvedValue(pending());
  let deliver = false;
  api.hintJob.mockImplementation(async () => (deliver ? done(ready({ hintMd: "Written." })) : pending()));
  api.cancelHint.mockImplementation(async () => {
    deliver = true;
    return { version: 1, jobId: "hjob_1", state: "done", cancelled: false, reason: "already_shown" };
  });
  await open();
  pressHint();
  fireEvent.click(await screen.findByRole("button", { name: "use the item's hint instead" }));
  await screen.findByText("Written.", undefined, { timeout: 3000 });
  expect(api.recordHintReveal).not.toHaveBeenCalled();
  expect(screen.queryByText("Start with the first row.")).toBeNull();
});

it("makes no offer on an item with no authored hint left", async () => {
  adaptiveOn("classic", 0.05);
  api.getPracticeItem.mockResolvedValue(item({ hints: [], hintPolicy: { maxUsefulHints: 0 } }));
  api.requestHint.mockResolvedValue(pending());
  api.hintJob.mockResolvedValue(pending());
  await open();
  pressHint();
  await screen.findByText("Writing a hint for your work…");
  await new Promise((resolve) => setTimeout(resolve, 300));
  expect(screen.queryByRole("button", { name: "use the item's hint instead" })).toBeNull();
});

it("keeps today's authored path exactly when the sidecar answers disabled", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValue(done({ status: "disabled", reason: "adaptive_disabled" }, null as unknown as string));
  await open();
  pressHint();
  await screen.findByText("Start with the first row.");
  expect(api.recordHintReveal).toHaveBeenCalledTimes(1);
  expect(api.recordHintReveal.mock.calls[0][0]).toMatchObject({ authoredIndex: 0 });
  expect(screen.queryByTestId("hint-panel")).toBeNull();
});

it("shows a withheld or unavailable hint's own line, and worked help after a withheld one", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done({ status: "withheld", assistId: "ha_w",
    message: "this hint would give the answer away; take a worked piece instead? (worked help ◌)", picks: PICKS }));
  await open();
  pressHint();
  await screen.findByText("this hint would give the answer away; take a worked piece instead? (worked help ◌)");
  expect(screen.getByTestId("hint-picks")).toBeTruthy();
  api.requestHint.mockResolvedValueOnce(done({ status: "unavailable", assistId: "ha_u", reason: "codex_refused",
    message: "Hints for your work aren't written on Codex (too slow); the item has no hint left.", picks: PICKS }));
  pressHint();
  await screen.findByText("Hints for your work aren't written on Codex (too slow); the item has no hint left.");
  expect(screen.queryByTestId("hint-picks")).toBeNull();
});

it("leaves the diagnostic block's refusal unchanged: no request reaches the sidecar", async () => {
  adaptiveOn();
  api.getProbeContract.mockResolvedValue({
    version: 1, active: true, presentationId: "pres-1", forcedAttemptType: "diagnostic_probe",
    observationNumber: 1, maximumObservations: 3,
    restrictions: { hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true, answerRevealDisabled: true, feedbackDeferred: true }
  });
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText("Diagnostic check");
  pressHint();
  expect(callbacks.onError).toHaveBeenCalledWith(expect.stringContaining("hints are disabled during a diagnostic check"));
  expect(api.requestHint).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: "^h hint" })).toBeNull();
});

it("edits the one stored help style from the panel's ⋯ menu", async () => {
  adaptiveOn();
  api.requestHint.mockResolvedValueOnce(done(ready()));
  api.setHelpStyle.mockResolvedValue({ version: 1, helpStyle: "guide_me" });
  await open();
  pressHint();
  await screen.findByText("Evaluate your CDF at the point.");
  fireEvent.click(screen.getByRole("button", { name: "help style" }));
  const menu = screen.getByTestId("hint-style-menu");
  expect(within(menu).getAllByRole("button").map((node) => [node.textContent, node.getAttribute("aria-pressed")])).toEqual([
    ["let me struggle — offers the lightest help first: questions and goals to aim for", "false"],
    ["balanced — LearnLoop picks from your history", "true"],
    ["guide me — offers more specific help sooner: next steps, then worked steps", "false"]
  ]);
  fireEvent.click(within(menu).getAllByRole("button")[2]);
  await waitFor(() => expect(api.setHelpStyle).toHaveBeenCalledWith("guide_me"));
  await waitFor(() => expect(algoConfig().adaptiveHints?.helpStyle).toBe("guide_me"));
  fireEvent.click(screen.getByRole("button", { name: "help style" }));
  expect(within(screen.getByTestId("hint-style-menu")).getAllByRole("button")[2].getAttribute("aria-pressed")).toBe("true");
});
