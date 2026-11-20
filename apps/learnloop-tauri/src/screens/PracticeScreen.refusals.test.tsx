// UX fix stage 3 (item 5; stage 1's UX-6 sweep): a refusal that explains is
// said in place, in plain words, as a status line on the card, never as the
// shell's sticky red error. Errors stay errors only where something failed.
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";
import { findJargon } from "../copy/denyList";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), stopProbeDiagnosing: vi.fn(), startTeachBack: vi.fn(),
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

function refusal(): HTMLElement {
  return screen.getByTestId("practice-refusal");
}

function plainNotice(element: HTMLElement) {
  expect(element.getAttribute("role")).toBe("status");
  expect(element.textContent).not.toMatch(/diagnostic check|ask-tutor|learning objects?/i);
  expect(findJargon(element.textContent ?? "")).toEqual([]);
}

it("a check on your own: no hints on this one, said on the card, never an error", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  api.getPracticeItem.mockResolvedValue(item({ activeFollowupKind: "cold_retry" }));
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText(/On your own · no hints on this one/);
  pressHint();
  expect(refusal().textContent).toBe("No hints on this one: it's a check on your own.");
  plainNotice(refusal());
  expect(callbacks.onError).not.toHaveBeenCalled();
});

it("a short check: no hints, and how to be taught instead, in plain words", async () => {
  api.getProbeContract.mockResolvedValue(PROBE);
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText("Diagnostic check");
  pressHint();
  expect(refusal().textContent).toBe("No hints during this short check. Answer with what you know, or choose “Stop diagnosing and teach me”.");
  plainNotice(refusal());
  expect(callbacks.onError).not.toHaveBeenCalled();
});

it("a short check: Ask is paused, and how to be taught instead", async () => {
  api.getProbeContract.mockResolvedValue(PROBE);
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText("Diagnostic check");
  fireEvent.keyDown(window, { key: "?" });
  expect(refusal().textContent).toBe("Ask is paused during this short check. To be taught instead, choose “Stop diagnosing and teach me”.");
  plainNotice(refusal());
  expect(callbacks.onError).not.toHaveBeenCalled();
  expect(callbacks.onAsk).not.toHaveBeenCalled();
});

it("teaching it back: Ask is paused, and why", async () => {
  api.getPracticeItem.mockResolvedValue(item({ practiceMode: "teach_back", attemptTypesAllowed: ["teach_back"], hints: [] }));
  api.startTeachBack.mockResolvedValue({
    version: 1, practiceItemId: ITEM_ID, prompt: "Teach it", learningObjectTitle: "Determinants", budget: 2,
    state: { version: 1, practiceItemId: ITEM_ID, planned: [], turns: [], askedCount: 0 }
  });
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await waitFor(() => expect(api.startTeachBack).toHaveBeenCalled());
  await screen.findByRole("textbox", { name: "answer" });
  fireEvent.keyDown(window, { key: "?" });
  await waitFor(() => expect(screen.getByTestId("practice-refusal")).toBeTruthy());
  expect(refusal().textContent).toBe("Ask is paused while you teach this one back, so the tutor can't give the answer away.");
  plainNotice(refusal());
  expect(callbacks.onError).not.toHaveBeenCalled();
});

it("an ordinary question has no such line", async () => {
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  pressHint();
  await screen.findByText("Start with the first row.");
  expect(screen.queryByTestId("practice-refusal")).toBeNull();
});
