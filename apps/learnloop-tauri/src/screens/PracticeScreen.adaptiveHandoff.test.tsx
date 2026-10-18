// Adaptive hints H2b, Codex review F1-F3: the hint panel beside "Work in
// steps". A service hint goes with the work into steps (the answer box's
// submission is named, so the server carries its own shown rows into the
// problem); no hint is requested, polled or delivered while the panel is
// hidden, whichever control is pressed, and a request still being written
// is cancelled before the answer box is hidden; the authored offer reveals
// one hint however often it is clicked. Every RPC is a mock (no sidecar).
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import type { WorkbenchSessionDto } from "../api/dto";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn(),
  requestHint: vi.fn(), hintJob: vi.fn(), cancelHint: vi.fn(), answerDiscriminating: vi.fn(), setHelpStyle: vi.fn(),
  workbenchForItem: vi.fn(), workbenchOpen: vi.fn(), workbenchGet: vi.fn(), workbenchReopen: vi.fn(),
  workbenchSaveStep: vi.fn(), workbenchLeave: vi.fn(), workbenchAbandon: vi.fn(), workbenchSubmit: vi.fn(),
  workbenchSetBook: vi.fn(), workbenchRefreshImport: vi.fn(), workbenchBind: vi.fn(), workbenchRetryImport: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({
  MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean }) => (
    <textarea aria-label="answer" value={props.value} disabled={props.disabled}
      onChange={(event) => props.onChange(event.target.value)} />
  )
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => <span>card controls</span> }));
vi.mock("../components/ItemPresentation", () => ({ ItemPresentation: () => <p>Question</p> }));
vi.mock("../render/LiveMarkdownEditor", () => ({
  LiveMarkdownEditor: (p: { value: string; onChange: (value: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={p.ariaLabel} value={p.value} onChange={(event) => p.onChange(event.target.value)} />
  )
}));

const ITEM_ID = "pi_hints";
const DRAFT = "F(x) = x^2 on [0, 1]";

function item() {
  return {
    id: ITEM_ID, learningObjectId: "lo", learningObjectTitle: "Topic", subject: "probability", subjects: ["probability"],
    practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Find P.", label: null }] },
    prompt: "Find P.", expectedAnswer: "1/4", hints: ["Start with the CDF.", "Evaluate it."],
    hintPolicy: { maxUsefulHints: 2 }, candidateErrorTypes: [], tags: [], sourceRefs: [], attempts: [],
    evidenceFacets: [], evidenceWeights: {}, rubric: null, mastery: { mean: 0.5, variance: 0.18 }, elicitation: null
  };
}

function wb(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb_p", practiceItemId: ITEM_ID, stemMd: "Find P.", importStatus: "none", importError: null, origin: "practice",
    entry: "practice_screen", parentSessionId: null, extractionId: null, spanIds: [], sourceVisible: false, sourceHiddenAt: null,
    sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null, createdAt: "x",
    updatedAt: "x", closedAt: null, steps: [], lastEditedStepId: null, parts: null, sourceId: null,
    record: { bookCounted: false, bookVisible: false, hints: 1, questionHints: 0, ownAttempt: false,
      line: "1 hint → practice with help ◌", footer: "book hidden · help used: none", stuckNote: null },
    ...overrides
  };
}

function ready(overrides: Record<string, unknown> = {}) {
  return {
    status: "ready", assistId: "ha_1", hintMd: "Evaluate your CDF at the point.", kind: "next_step", level: 3,
    labels: { origin: "AI-written", kind: "the next step", workedHelp: null, horizon: null },
    evidence: { countsAsHint: true, primed: false, level: 3 }, replies: ["doesnt_connect", "book_way"],
    picks: [], shown: true, ...overrides
  };
}

const pending = (jobId = "hjob_1") => ({ version: 1, jobId, state: "pending", result: null });
const done = (result: Record<string, unknown>, jobId = "hjob_1") => ({ version: 1, jobId, state: "done", result });
const cancelled = { version: 1, jobId: "hjob_1", state: "cancelled", cancelled: true, reason: null };

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function props(): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn()
  };
}

function config(adaptive: boolean, offerAfter = 4) {
  setAlgoConfig({
    ui: { practiceFeedback: "classic" }, workbench: { enabled: true, openSessionDays: 30 },
    ...(adaptive ? { hints: { adaptiveEnabled: true, authoredOfferAfterSeconds: offerAfter, helpStyle: "balanced" } } : {})
  });
}

async function open() {
  render(<PracticeScreen {...props()} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  fireEvent.change(answer, { target: { value: DRAFT } });
  await screen.findByRole("button", { name: /work in steps/i });
}

async function intoSteps() {
  fireEvent.click(screen.getByRole("button", { name: /work in steps/i }));
  await screen.findByRole("region", { name: "workbench" });
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear()
    }
  });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.recordHintReveal.mockResolvedValue({ version: 1, recorded: true, reason: null, assistId: "ha_client" });
  api.workbenchForItem.mockResolvedValue({ sessions: [] });
  api.workbenchOpen.mockResolvedValue({ session: wb(), resumed: false });
  api.workbenchLeave.mockResolvedValue({ session: wb() });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("F1: names the answer box's submission when the work moves into steps, so the server carries its shown hints", async () => {
  config(true);
  api.requestHint.mockResolvedValue(done(ready()));
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  await screen.findByText("Evaluate your CDF at the point.");
  const key = api.requestHint.mock.calls[0][0].submissionId as string;
  await intoSteps();
  expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({
    carriedSubmissionId: key, carriedSessionId: "s1", carriedHints: 0
  }));
});

it("F1: the item's hint taken instead goes with the work as the client's own count", async () => {
  config(true, 0.05);
  api.requestHint.mockResolvedValue(pending());
  api.hintJob.mockResolvedValue(pending());
  api.cancelHint.mockResolvedValue(cancelled);
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  fireEvent.click(await screen.findByRole("button", { name: "use the item's hint instead" }));
  await screen.findByText("Start with the CDF.");
  await intoSteps();
  expect(api.workbenchOpen).toHaveBeenCalledWith(expect.objectContaining({ carriedHints: 1, carriedSessionId: "s1" }));
});

it("F1: with adaptive hints off nothing more is sent (the base's hand-off)", async () => {
  config(false);
  await open();
  await intoSteps();
  const sent = api.workbenchOpen.mock.calls[0][0];
  expect(sent).not.toHaveProperty("carriedSubmissionId");
  expect(sent).not.toHaveProperty("carriedSessionId");
});

it("F2: in steps neither the key bar's ^h nor Ctrl+H asks for a hint", async () => {
  config(true);
  api.requestHint.mockResolvedValue(done(ready()));
  await open();
  await intoSteps();
  const control = screen.queryByRole("button", { name: "^h hint" });
  if (control) fireEvent.click(control);
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.requestHint).not.toHaveBeenCalled();
  expect(api.hintJob).not.toHaveBeenCalled();
});

it("F2: a hint still being written is cancelled before the answer box is hidden, and never read or shown", async () => {
  config(true);
  api.requestHint.mockResolvedValue(pending());
  api.hintJob.mockResolvedValue(done(ready({ hintMd: "Delivered while hidden." })));
  api.cancelHint.mockResolvedValue(cancelled);
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  await screen.findByText("Writing a hint for your work…");
  const polledBefore = api.hintJob.mock.calls.length;
  fireEvent.click(screen.getByRole("button", { name: /work in steps/i }));
  await screen.findByRole("region", { name: "workbench" });
  expect(api.cancelHint).toHaveBeenCalledWith("hjob_1");
  expect(api.cancelHint.mock.invocationCallOrder[0]).toBeLessThan(api.workbenchOpen.mock.invocationCallOrder[0]);
  await new Promise((resolve) => setTimeout(resolve, 900));
  expect(api.hintJob.mock.calls.length).toBe(polledBefore);
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  await screen.findByRole("textbox", { name: "answer" });
  expect(screen.queryByText("Delivered while hidden.")).toBeNull();
  // Back on the answer box, a press asks again.
  api.requestHint.mockResolvedValue(done(ready({ assistId: "ha_2", hintMd: "Asked again." })));
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  await screen.findByText("Asked again.");
});

it("F2: a request still being sent is waited for, then cancelled, before the problem opens", async () => {
  config(true);
  const sent = deferred<ReturnType<typeof pending>>();
  api.requestHint.mockReturnValue(sent.promise);
  api.cancelHint.mockResolvedValue(cancelled);
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  await waitFor(() => expect(api.requestHint).toHaveBeenCalled());
  fireEvent.click(screen.getByRole("button", { name: /work in steps/i }));
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(api.workbenchOpen).not.toHaveBeenCalled();
  sent.resolve(pending());
  await screen.findByRole("region", { name: "workbench" });
  expect(api.cancelHint).toHaveBeenCalledWith("hjob_1");
  expect(api.cancelHint.mock.invocationCallOrder[0]).toBeLessThan(api.workbenchOpen.mock.invocationCallOrder[0]);
  expect(api.hintJob).not.toHaveBeenCalled();
});

it("F2: a hint shown before the cancel is read once and kept for the answer box", async () => {
  config(true);
  api.requestHint.mockResolvedValue(pending());
  let delivered = false;
  api.hintJob.mockImplementation(async () => (delivered ? done(ready({ hintMd: "Shown first." })) : pending()));
  api.cancelHint.mockImplementation(async () => {
    delivered = true;
    return { version: 1, jobId: "hjob_1", state: "done", cancelled: false, reason: "already_shown" };
  });
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  await screen.findByText("Writing a hint for your work…");
  await intoSteps();
  fireEvent.click(screen.getByRole("button", { name: "answer box instead" }));
  expect(await screen.findByText("Shown first.")).toBeTruthy();
});

it("F3: a double click on the item's hint instead reveals one hint and counts one", async () => {
  config(true, 0.05);
  api.requestHint.mockResolvedValue(pending());
  api.hintJob.mockResolvedValue(pending());
  const cancel = deferred<typeof cancelled>();
  api.cancelHint.mockReturnValue(cancel.promise);
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  const offer = await screen.findByRole("button", { name: "use the item's hint instead" });
  fireEvent.click(offer);
  fireEvent.click(offer);
  cancel.resolve(cancelled);
  await screen.findByText("Start with the CDF.");
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.cancelHint).toHaveBeenCalledTimes(1);
  expect(api.recordHintReveal).toHaveBeenCalledTimes(1);
  expect(screen.getAllByText("Start with the CDF.")).toHaveLength(1);
  api.submitAttempt.mockResolvedValue({ attemptId: "att-1", learningObjectId: "lo", probeEpisode: { feedbackDeferred: false } });
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  expect(api.submitAttempt.mock.calls[0][0].hintsUsed).toBe(1);
});

it("F3: an offer whose request a poll already settled reveals nothing", async () => {
  config(true, 0.05);
  api.requestHint.mockResolvedValue(pending());
  let deliver = false;
  api.hintJob.mockImplementation(async () => (deliver ? done(ready({ hintMd: "Written." })) : pending()));
  const cancel = deferred<typeof cancelled>();
  api.cancelHint.mockReturnValue(cancel.promise);
  await open();
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  fireEvent.click(await screen.findByRole("button", { name: "use the item's hint instead" }));
  deliver = true;
  await screen.findByText("Written.", undefined, { timeout: 3000 });
  // The server answered "cancelled" to a request the poll already settled.
  cancel.resolve(cancelled);
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(api.recordHintReveal).not.toHaveBeenCalled();
  expect(screen.queryByText("Start with the CDF.")).toBeNull();
});
