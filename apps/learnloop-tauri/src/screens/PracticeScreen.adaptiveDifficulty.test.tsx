// Adaptive difficulty AD1 (spec_adaptive_difficulty_v1 §12, §11.2, G-AD1-3,
// G-AD1-10): the practice screen's optional "Felt" tap beside Submit, and the
// first-hint progress marker. The tap is never preselected, never required,
// sent only when tapped and locked once Submit is pressed. The marker is the
// tutor-question marker read at the first hint the learner sees (an item's own
// hint or one the H2b panel delivered), kept in the saved draft and sent on
// submit; a restored draft keeps it. With the sidecar's switches off the
// screen renders and sends exactly what it did before AD1. Every RPC is a mock.
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
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

const ITEM_ID = "pi_ad1";
const AD_ON = { ratingTap: true, firstHintProgress: true };

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

function props(overrides: Partial<ComponentProps<typeof PracticeScreen>> = {}): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn(),
    ...overrides
  };
}

async function open(callbacks = props()) {
  render(<PracticeScreen {...callbacks} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  return { answer, callbacks };
}

function pressHint() {
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
}

async function submitted() {
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  return api.submitAttempt.mock.calls[0][0];
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  api.recordHintReveal.mockResolvedValue({ version: 1, recorded: true, reason: null, assistId: "ha_1" });
  api.submitAttempt.mockResolvedValue({ attemptId: "att-1", learningObjectId: "lo_det", probeEpisode: { feedbackDeferred: false } });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  const stored = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => stored.get(key) ?? null,
    setItem: (key: string, value: string) => void stored.set(key, value),
    removeItem: (key: string) => void stored.delete(key)
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("offers the rating beside Submit, unselected, and a submit without a tap sends none", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" }, adaptiveDifficulty: AD_ON });
  const { answer } = await open();
  const group = screen.getByRole("group", { name: /How did this one feel/ });
  expect(within(group).queryAllByRole("button", { pressed: true })).toHaveLength(0);
  expect(within(group).getByRole("button", { name: "about right" })).toBeTruthy();
  fireEvent.change(answer, { target: { value: "det(A) = -3" } });
  const payload = await submitted();
  expect(payload).not.toHaveProperty("difficultyRating");
  expect(payload).not.toHaveProperty("firstHintProgress");
});

it("sends the tap when tapped, and a second tap takes it back", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON });
  const { answer } = await open();
  fireEvent.change(answer, { target: { value: "det(A) = -3" } });
  const hard = screen.getByRole("button", { name: "hard" });
  fireEvent.click(screen.getByRole("button", { name: "easy" }));
  fireEvent.click(screen.getByRole("button", { name: "easy" }));
  expect(screen.getByRole("button", { name: "easy" }).getAttribute("aria-pressed")).toBe("false");
  fireEvent.click(hard);
  expect(hard.getAttribute("aria-pressed")).toBe("true");
  const payload = await submitted();
  expect(payload.difficultyRating).toBe("hard");
});

it("hides the tap for the session with one tap, remembered for the next item", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" }, adaptiveDifficulty: AD_ON });
  await open();
  fireEvent.click(screen.getByRole("button", { name: "hide this for the session" }));
  expect(screen.queryByRole("group", { name: /How did this one feel/ })).toBeNull();
  cleanup();
  await open();
  expect(screen.queryByRole("group", { name: /How did this one feel/ })).toBeNull();
});

it("marks no_draft when the first hint is revealed on an empty answer, and keeps it in the draft", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON });
  const { answer } = await open();
  pressHint();
  await screen.findByText("Start with the first row.");
  fireEvent.change(answer, { target: { value: "det(A) = -3" } });
  pressHint();
  await screen.findByText("Watch the signs.");
  await waitFor(() => expect(api.savePracticeDraft).toHaveBeenCalledWith(
    expect.objectContaining({ firstHintProgress: "no_draft" })));
  const payload = await submitted();
  expect(payload.firstHintProgress).toBe("no_draft");
});

it("marks draft_started when the answer was begun before the first hint", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON });
  const { answer } = await open();
  fireEvent.change(answer, { target: { value: "expand along row 1" } });
  pressHint();
  await screen.findByText("Start with the first row.");
  const payload = await submitted();
  expect(payload.firstHintProgress).toBe("draft_started");
});

it("a restored draft keeps its marker", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON });
  api.recoverPracticeSubmission.mockResolvedValue({ status: "pending", result: null });
  await open(props({ restoredAnswer: "det(A) = -3", restoredHints: 1, restoredSubmissionId: "k1",
                     restoredFirstHintProgress: "no_draft" }));
  const payload = await submitted();
  expect(payload.firstHintProgress).toBe("no_draft");
});

it("marks the first hint the adaptive panel delivered", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" }, adaptiveDifficulty: AD_ON,
                  hints: { adaptiveEnabled: true, authoredOfferAfterSeconds: 4, helpStyle: "balanced" } });
  api.requestHint.mockResolvedValue({ version: 1, jobId: "hjob_1", state: "done", result: {
    status: "ready", assistId: "ha_1", hintMd: "Evaluate the determinant row by row.", kind: "next_step", level: 3,
    labels: { origin: "AI-written", kind: "the next step", workedHelp: null, horizon: null },
    evidence: { countsAsHint: true, primed: false, level: 3 }, replies: [], picks: [], shown: true
  } });
  const { answer } = await open();
  pressHint();
  await screen.findByText("Evaluate the determinant row by row.");
  fireEvent.change(answer, { target: { value: "det(A) = -3" } });
  const payload = await submitted();
  expect(payload.firstHintProgress).toBe("no_draft");
});

it("with the switches off renders no tap and sends neither field", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  const { answer } = await open();
  expect(screen.queryByRole("group", { name: /How did this one feel/ })).toBeNull();
  pressHint();
  await screen.findByText("Start with the first row.");
  fireEvent.change(answer, { target: { value: "det(A) = -3" } });
  const payload = await submitted();
  expect(payload).not.toHaveProperty("difficultyRating");
  expect(payload).not.toHaveProperty("firstHintProgress");
  for (const [draft] of api.savePracticeDraft.mock.calls) expect(draft).not.toHaveProperty("firstHintProgress");
});
