// UX Phase 4.1 (docs/specs/ux_learnloop_v1.md §7.4, W5): the practice card
// shows the question and the answer box. The raw item id, the mode pill,
// "<provider> grading" and the mastery estimate leave the surface (details);
// a method-explicit question keeps its rendered instruction; Hint, I'm stuck,
// Ask and Skip are buttons. With no AI, the learner grades against a full
// answer: Got it · Partly · Missed. `[ui] practice_feedback = "classic"`
// restores the card exactly.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn()
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

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: ITEM_ID, learningObjectId: "lo_det", learningObjectTitle: "Determinants", subject: "linear_algebra",
    subjects: ["linear_algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [
      { kind: "prompt", markdown: "Compute det(A) for the 3x3 matrix A.", label: null },
      { kind: "required_method_instruction", markdown: "Use cofactor expansion in your answer.", label: null }
    ] },
    prompt: "Compute det(A) for the 3x3 matrix A.",
    expectedAnswer: "Expand along the first row: det(A) = -3.",
    hints: ["Start with the first row.", "Watch the signs."],
    hintPolicy: { maxUsefulHints: 2 }, candidateErrorTypes: [], tags: [], sourceRefs: [
      { refId: "src_ladr#s4", refType: "source", displayName: "Axler", locator: "§4.2", path: "sources/axler.md", quote: null }
    ],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 4, criteria: [
      { id: "expansion", description: "Expands along a row with the right signs", points: 2 },
      { id: "value", description: "Gets the value -3", points: 2 }
    ], fatalErrors: [] },
    mastery: { mean: 0.5, variance: 0.18 },
    elicitation: null,
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

function bodyText(): string {
  return document.body.textContent ?? "";
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  api.skipPracticeItem.mockResolvedValue({});
  api.submitAttempt.mockResolvedValue({ attemptId: "att_1", learningObjectId: "lo_det" });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("shows the question and its method instruction, without the item id, mode, grader or mastery estimate", async () => {
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByText("Compute det(A) for the 3x3 matrix A.")).toBeTruthy();
  // Method-explicit: the rendered instruction is part of the question.
  expect(screen.getByText("Use cofactor expansion in your answer.")).toBeTruthy();
  expect(screen.getByText("Determinants")).toBeTruthy();
  const text = bodyText();
  for (const hidden of [ITEM_ID, "constructed_response", "codex grading", "grading", "mastery estimate", "0.50", "chars", "words"]) {
    expect(text.toLowerCase()).not.toContain(hidden.toLowerCase());
  }
});

it("keeps the card's receipts one click away, under details", async () => {
  render(<PracticeScreen {...props()} />);
  await screen.findByText("Compute det(A) for the 3x3 matrix A.");
  fireEvent.click(screen.getByRole("button", { name: /details/ }));
  expect(bodyText()).toContain(ITEM_ID);
  expect(bodyText()).toContain("constructed_response");
});

it("offers Hint, I'm stuck, Ask and Skip as buttons; Skip goes on to the next question", async () => {
  const callbacks = props();
  render(<PracticeScreen {...callbacks} />);
  await screen.findByText("Compute det(A) for the 3x3 matrix A.");
  fireEvent.click(screen.getByRole("button", { name: /^Hint/ }));
  expect(await screen.findByText("Start with the first row.")).toBeTruthy();
  // No "1/2" numbering on a hint.
  expect(bodyText()).not.toMatch(/\b1\/2\b/);
  fireEvent.click(screen.getByRole("button", { name: /^Ask/ }));
  expect(callbacks.onAsk).toHaveBeenCalled();
  expect(screen.getByRole("button", { name: /I'm stuck/ })).toBeTruthy();
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /^Skip/ }));
  });
  expect(api.skipPracticeItem).toHaveBeenCalledWith({ sessionId: "s1", practiceItemId: ITEM_ID });
  expect(callbacks.onBack).toHaveBeenCalled();
});

it("a check on your own says so quietly and offers no hint", async () => {
  api.getPracticeItem.mockResolvedValue(item({ activeFollowupKind: "cold_retry" }));
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByText(/On your own · no hints on this one/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /^Hint/ })).toBeNull();
  expect(bodyText()).not.toMatch(/void|rejected|measurement/i);
});

it("with no AI, locks the answer and grades it against a full answer: Got it submits full marks", async () => {
  const callbacks = props({ gradingReady: false });
  render(<PracticeScreen {...callbacks} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(answer, { target: { value: "det(A) = -3 by the first row" } });
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  expect(await screen.findByText("Expand along the first row: det(A) = -3.")).toBeTruthy();
  expect((screen.getByRole("textbox", { name: "answer" }) as HTMLTextAreaElement).disabled).toBe(true);
  expect(bodyText()).not.toMatch(/fallback|provider_auth_required|AI grading is unavailable/);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Got it" }));
  });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  const sent = api.submitAttempt.mock.calls[0][0];
  expect(sent.selfGrade.criterionPoints).toEqual({ expansion: 2, value: 2 });
  await waitFor(() => expect(callbacks.onFeedback).toHaveBeenCalledWith("att_1"));
});

it("Partly asks which parts the learner got; Missed submits none", async () => {
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(answer, { target: { value: "first row" } });
  fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  fireEvent.click(await screen.findByRole("button", { name: "Partly" }));
  fireEvent.click(screen.getByRole("checkbox", { name: /Expands along a row with the right signs/ }));
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /^Done/ }));
  });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  expect(api.submitAttempt.mock.calls[0][0].selfGrade.criterionPoints).toEqual({ expansion: 2, value: 0 });
});

it("a short check looks like any other question, with one line on when feedback comes", async () => {
  api.getProbeContract.mockResolvedValue({
    version: 1, active: true, presentationId: "pres_1", episodeId: "ep_1", observationNumber: 1, maximumObservations: 3,
    forcedAttemptType: "diagnostic_probe",
    restrictions: { hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true, answerRevealDisabled: true, feedbackDeferred: true }
  });
  render(<PracticeScreen {...props()} />);
  expect(await screen.findByText(/Feedback comes when this short check ends/)).toBeTruthy();
  const text = bodyText();
  expect(text).not.toMatch(/diagnostic|observation|probe/i);
  expect(screen.queryByRole("button", { name: /^Hint/ })).toBeNull();
  expect(screen.getByRole("button", { name: /Teach me instead/ })).toBeTruthy();
});

it("classic restores the card exactly: the item id, the mode pill and the grader", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<PracticeScreen {...props()} />);
  await screen.findByText("Compute det(A) for the 3x3 matrix A.");
  const text = bodyText();
  expect(text).toContain(ITEM_ID);
  expect(text).toContain("constructed_response");
  expect(text).toContain("codex grading");
  expect(text).toContain("mastery estimate");
});
