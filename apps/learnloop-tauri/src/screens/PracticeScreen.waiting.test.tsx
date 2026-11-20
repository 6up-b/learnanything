// "Waiting you can see" (docs/reviews/ux-waiting.md) on the practice screen of
// the simple shell: the question's own read (the end of the owner's case 1)
// and Submit until the grade is back (case 2). Each: nothing before the
// indicator's delay, the line after it, gone when the screen arrives.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { WAIT_LATER_MS } from "../components/Waiting";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn()
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

const ITEM_ID = "pi_01JZZQ8Y7W6V5T4S3R2Q1P0N9M";

function item() {
  return {
    id: ITEM_ID, learningObjectId: "lo_det", learningObjectTitle: "Determinants", subject: "linear_algebra",
    subjects: ["linear_algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Compute det(A) for the 3x3 matrix A.", label: null }] },
    prompt: "Compute det(A) for the 3x3 matrix A.",
    expectedAnswer: "Expand along the first row: det(A) = -3.",
    hints: ["Start with the first row."], hintPolicy: { maxUsefulHints: 1 }, candidateErrorTypes: [], tags: [], sourceRefs: [],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 2, criteria: [{ id: "value", description: "Gets the value -3", points: 2 }], fatalErrors: [] },
    mastery: { mean: 0.5, variance: 0.18 }, elicitation: null,
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

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

async function advance(ms: number) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

beforeEach(() => {
  vi.useFakeTimers();
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  api.submitAttempt.mockResolvedValue({ attemptId: "att_1", learningObjectId: "lo_det" });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("the question's read: nothing before the delay, then 'Opening the question…', gone when the question shows", async () => {
  const read = deferred<ReturnType<typeof item>>();
  api.getPracticeItem.mockReturnValue(read.promise);
  render(<PracticeScreen {...props()} />);
  await advance(300);
  expect(screen.queryByText(/Opening the question…/)).toBeNull();
  await advance(100);
  expect(screen.getByTestId("question-wait").textContent).toBe("◐ Opening the question…");
  read.resolve(item());
  await advance(0);
  expect(screen.getByText("Compute det(A) for the 3x3 matrix A.")).toBeTruthy();
  expect(screen.queryByTestId("question-wait")).toBeNull();
});

it("Submit: 'Checking your answer…' after the delay, the second line after a few seconds, gone when feedback opens", async () => {
  const graded = deferred<{ attemptId: string; learningObjectId: string }>();
  api.submitAttempt.mockReturnValue(graded.promise);
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await advance(0);
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "det(A) = -3" } });
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await advance(300);
  expect(screen.queryByText(/Checking your answer…/)).toBeNull();
  await advance(100);
  const line = screen.getByTestId("grading-wait");
  expect(line.getAttribute("role")).toBe("status");
  expect(line.textContent).toBe("◐ Checking your answer…");
  await advance(WAIT_LATER_MS);
  expect(screen.getByTestId("grading-wait-later").textContent).toBe("This can take a minute.");
  graded.resolve({ attemptId: "att_1", learningObjectId: "lo_det" });
  await advance(0);
  expect(callbacks.onFeedback).toHaveBeenCalledWith("att_1");
  expect(screen.queryByTestId("grading-wait")).toBeNull();
});

it("Submit with no AI grading says the answer is saved, not checked, and claims no time", async () => {
  const graded = deferred<{ attemptId: string; learningObjectId: string }>();
  api.recordSelfGradeDisclosure.mockReturnValue(graded.promise);
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  await advance(0);
  fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "det(A) = -3" } });
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  await advance(400);
  expect(screen.getByTestId("grading-wait").textContent).toBe("◐ Saving your answer…");
  await advance(WAIT_LATER_MS);
  expect(screen.queryByTestId("grading-wait-later")).toBeNull();
});
