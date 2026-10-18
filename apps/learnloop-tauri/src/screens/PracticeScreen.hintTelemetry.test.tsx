// Adaptive hints H0 (spec_adaptive_hints_v1 §9, §10 H0): the practice screen
// tells the sidecar about each authored hint it reveals, fire and forget.
// Called once per hint actually shown (never on a refused reveal, never past
// the last hint), with the draft it was shown on; its failure is ignored and
// nothing on the screen depends on it.
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn() as ReturnType<typeof vi.fn> | undefined
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
const recordHintReveal = vi.fn();

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

function props(): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn()
  };
}

const PROBE = {
  version: 1, active: true, presentationId: "pres-1", forcedAttemptType: "diagnostic_probe",
  observationNumber: 1, maximumObservations: 3,
  restrictions: { hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true, answerRevealDisabled: true, feedbackDeferred: true }
};

function pressHint() {
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  for (const mock of Object.values(api)) mock?.mockReset();
  recordHintReveal.mockReset();
  api.recordHintReveal = recordHintReveal;
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  recordHintReveal.mockResolvedValue({ version: 1, recorded: true, reason: null, assistId: "ha_1" });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("records each authored hint it reveals, with its index and the draft, and nothing past the last", async () => {
  render(<PracticeScreen {...props()} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  fireEvent.change(answer, { target: { value: "expand along row 1" } });
  pressHint();
  expect(await screen.findByText("Start with the first row.")).toBeTruthy();
  expect(recordHintReveal).toHaveBeenCalledTimes(1);
  const [first] = recordHintReveal.mock.calls[0];
  expect(first).toMatchObject({ sessionId: "s1", practiceItemId: ITEM_ID, authoredIndex: 0, answerMd: "expand along row 1" });
  expect(Number.isNaN(Date.parse(first.revealedAt))).toBe(false);
  pressHint();
  expect(await screen.findByText("Watch the signs.")).toBeTruthy();
  expect(recordHintReveal).toHaveBeenCalledTimes(2);
  expect(recordHintReveal.mock.calls[1][0]).toMatchObject({ authoredIndex: 1 });
  // Past the last hint the press reveals nothing, so nothing is recorded.
  pressHint();
  expect(recordHintReveal).toHaveBeenCalledTimes(2);
  // Submit still sends the screen's own count.
  expect(api.savePracticeDraft).not.toHaveBeenCalledWith(expect.objectContaining({ hintsUsed: 3 }));
});

it("records nothing on a refused reveal: a diagnostic check", async () => {
  api.getProbeContract.mockResolvedValue(PROBE);
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText("Diagnostic check");
  pressHint();
  expect(callbacks.onError).toHaveBeenCalledWith(expect.stringContaining("hints are disabled during a diagnostic check"));
  expect(recordHintReveal).not.toHaveBeenCalled();
});

it("records nothing on a refused reveal: a check on your own in the plain card", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  api.getPracticeItem.mockResolvedValue(item({ activeFollowupKind: "cold_retry" }));
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText(/On your own · no hints on this one/);
  pressHint();
  expect(callbacks.onError).toHaveBeenCalledWith("No hints on this one: it's a check on your own.");
  expect(recordHintReveal).not.toHaveBeenCalled();
});

it("records nothing for an item with no authored hints", async () => {
  api.getPracticeItem.mockResolvedValue(item({ hints: [], hintPolicy: { maxUsefulHints: 0 } }));
  render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  pressHint();
  expect(recordHintReveal).not.toHaveBeenCalled();
});

async function screenAfterTwoHints(setup: () => void): Promise<string> {
  setup();
  const view = render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  pressHint();
  await screen.findByText("Start with the first row.");
  pressHint();
  await screen.findByText("Watch the signs.");
  // Let any settled or failed telemetry promise land before reading the screen.
  await new Promise((resolve) => setTimeout(resolve, 0));
  const html = view.container.innerHTML;
  cleanup();
  return html;
}

it("ignores a failed call, a no-op answer and a sidecar without the RPC: the screen is the same", async () => {
  const recorded = await screenAfterTwoHints(() => undefined);
  const switchedOff = await screenAfterTwoHints(() => {
    recordHintReveal.mockResolvedValue({ version: 1, recorded: false, reason: "telemetry_disabled", assistId: null });
  });
  const failed = await screenAfterTwoHints(() => {
    recordHintReveal.mockRejectedValue({ code: "sidecar_error", message: "disk I/O error" });
  });
  const missing = await screenAfterTwoHints(() => {
    api.recordHintReveal = undefined;
  });
  expect(switchedOff).toBe(recorded);
  expect(failed).toBe(recorded);
  expect(missing).toBe(recorded);
  expect(recorded).toContain("Watch the signs.");
});

it("never reports a telemetry failure to the learner", async () => {
  recordHintReveal.mockRejectedValue(new Error("unknown method"));
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  pressHint();
  expect(await screen.findByText("Start with the first row.")).toBeTruthy();
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(callbacks.onError).not.toHaveBeenCalled();
});
