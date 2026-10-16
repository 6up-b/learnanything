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
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
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
  setAlgoConfig({ ui: { practiceFeedback: "simple" }, practice: { stuckPrompt: true } });
  for (const mock of Object.values(api)) mock.mockReset();
  api.getPracticeItem.mockResolvedValue(item());
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.acknowledgePracticeSubmission.mockResolvedValue({ acknowledged: true });
  api.skipPracticeItem.mockResolvedValue({});
  api.submitAttempt.mockResolvedValue({ attemptId: "att_1", learningObjectId: "lo_det" });
  api.recordSelfGradeDisclosure.mockResolvedValue({ version: 1, frozen: true });
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

// Found in the Phase 4 harness walk: a primed retry (after a repair, or from
// feedback) said nothing about being practice with help.
it("labels primed practice quietly as with help", async () => {
  render(<PracticeScreen {...props({ primed: true })} />);
  expect(await screen.findByText("◌ with help")).toBeTruthy();
});

it("never sends an untouched self-grade on a second ^↵: only Got it, Partly or Missed submit", async () => {
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  fireEvent.change(answer, { target: { value: "first row" } });
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  });
  expect(await screen.findByRole("button", { name: "Got it" })).toBeTruthy();
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter", ctrlKey: true });
  });
  expect(api.submitAttempt).not.toHaveBeenCalled();
});

// == Codex review F1: the plain self-grade freezes the whole trace first =====

const ELICIT = { elicit: true, prompt: "Optional, one line: why this approach rather than another?", reason: "decision_point" };

it("F1: freezes the answer and the volunteered line before it shows a full answer, then sends exactly them", async () => {
  api.getPracticeItem.mockResolvedValue(item({ elicitation: ELICIT }));
  let confirm!: (value: unknown) => void;
  api.recordSelfGradeDisclosure.mockReturnValueOnce(new Promise((done) => { confirm = done; }));
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "det(A) = -3" } });
  fireEvent.change(screen.getByRole("textbox", { name: /why this approach/ }), { target: { value: "first row has zeros" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  });
  await waitFor(() => expect(api.recordSelfGradeDisclosure).toHaveBeenCalledOnce());
  const frozen = api.recordSelfGradeDisclosure.mock.calls[0][0];
  expect(frozen).toMatchObject({ sessionId: "s1", practiceItemId: ITEM_ID, answerMd: "det(A) = -3", explanationMd: "first row has zeros" });
  expect(typeof frozen.submissionId).toBe("string");
  // Nothing of the full answer until the freeze is confirmed.
  expect(screen.queryByText("Expand along the first row: det(A) = -3.")).toBeNull();
  await act(async () => confirm({ version: 1, frozen: true }));
  expect(await screen.findByText("Expand along the first row: det(A) = -3.")).toBeTruthy();
  expect((screen.getByRole("textbox", { name: "answer" }) as HTMLTextAreaElement).disabled).toBe(true);
  expect((screen.getByRole("textbox", { name: /why this approach/ }) as HTMLInputElement).disabled).toBe(true);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Got it" }));
  });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  const sent = api.submitAttempt.mock.calls[0][0];
  expect(sent).toMatchObject({ answerMd: "det(A) = -3", explanationMd: "first row has zeros", submissionId: frozen.submissionId });
});

it("F1 (round 3): the self-grade's key shows only once its display row for the pending draft is committed", async () => {
  api.getPracticeItem.mockResolvedValue(item({ elicitation: ELICIT }));
  let release!: (value: unknown) => void;
  api.recordSelfGradeDisclosure
    .mockResolvedValueOnce({ version: 1, frozen: true })
    .mockReturnValueOnce(new Promise((done) => { release = done; }));
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "det(A) = -3" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  });
  await waitFor(() => expect(api.recordSelfGradeDisclosure).toHaveBeenCalledTimes(2));
  const [[freeze], [display]] = api.recordSelfGradeDisclosure.mock.calls;
  expect(freeze.displayId).toBeUndefined();
  expect(display).toMatchObject({ submissionId: freeze.submissionId, answerMd: "det(A) = -3", displayId: expect.stringMatching(/^display_/) });
  expect(screen.queryByText("Expand along the first row: det(A) = -3.")).toBeNull();
  await act(async () => release({ version: 1, frozen: true, recorded: true, recordedAt: new Date().toISOString() }));
  expect(await screen.findByText("Expand along the first row: det(A) = -3.")).toBeTruthy();
});

it("F1 (round 3): a display refused because the draft is done with keeps the key hidden, with no retry", async () => {
  api.recordSelfGradeDisclosure
    .mockResolvedValueOnce({ version: 1, frozen: true })
    .mockRejectedValueOnce({ code: "disclosure_not_pending", message: "no longer open", retryable: false });
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "-3" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  });
  expect(await screen.findByText(/can't be shown right now/)).toBeTruthy();
  expect(screen.queryByText("Expand along the first row: det(A) = -3.")).toBeNull();
  expect(api.recordSelfGradeDisclosure).toHaveBeenCalledTimes(2);
});

it("F1: a freeze that is not confirmed grades without showing the full answer", async () => {
  api.recordSelfGradeDisclosure.mockRejectedValueOnce(new Error("sidecar gone"));
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "-3" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  });
  expect(await screen.findByRole("button", { name: "Got it" })).toBeTruthy();
  expect(screen.queryByText("Expand along the first row: det(A) = -3.")).toBeNull();
});

it("F1: a resumed draft whose full answer was shown reopens locked to its frozen trace", async () => {
  api.getPracticeItem.mockResolvedValue(item({ elicitation: ELICIT }));
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  const onDraftSaved = vi.fn();
  const disclosure = { submissionId: "key_1", answerMd: "det(A) = -3", explanationMd: "first row has zeros" };
  const { unmount } = render(
    <PracticeScreen
      {...props({ gradingReady: false, onDraftSaved, restoredAnswer: "det(A) = -3", restoredSubmissionId: "key_1", restoredDisclosure: disclosure })}
    />
  );
  // Straight back to the self-grade, the answer and the line locked; no new freeze.
  expect(await screen.findByText("Expand along the first row: det(A) = -3.")).toBeTruthy();
  expect((screen.getByRole("textbox", { name: "answer" }) as HTMLTextAreaElement).disabled).toBe(true);
  const line = screen.getByRole("textbox", { name: /why this approach/ }) as HTMLInputElement;
  expect(line.disabled).toBe(true);
  expect(line.value).toBe("first row has zeros");
  // No new freeze: only the key's display row for the draft already frozen
  // (round 3 F1), before the key showed.
  expect(api.recordSelfGradeDisclosure.mock.calls.length).toBeGreaterThan(0);
  for (const [input] of api.recordSelfGradeDisclosure.mock.calls) {
    expect(input).toMatchObject({ submissionId: "key_1", answerMd: "det(A) = -3", displayId: expect.stringMatching(/^display_/) });
  }
  unmount();
  // The in-memory mirror carries the frozen trace for the next remount.
  expect(onDraftSaved).toHaveBeenCalledWith(expect.objectContaining({ selfGradeDisclosure: disclosure }));
});

it("F1: a resumed frozen draft stays locked when the grader is back, and submits the frozen trace", async () => {
  const disclosure = { submissionId: "key_1", answerMd: "det(A) = -3", explanationMd: null };
  api.recoverPracticeSubmission.mockResolvedValue({ version: 1, status: "pending", result: null });
  render(<PracticeScreen {...props({ restoredAnswer: "det(A) = -3", restoredSubmissionId: "key_1", restoredDisclosure: disclosure })} />);
  expect(await screen.findByTestId("frozen-answer-note")).toBeTruthy();
  expect((screen.getByRole("textbox", { name: "answer" }) as HTMLTextAreaElement).disabled).toBe(true);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  });
  await waitFor(() => expect(api.submitAttempt).toHaveBeenCalledOnce());
  expect(api.submitAttempt.mock.calls[0][0]).toMatchObject({ answerMd: "det(A) = -3", explanationMd: null, submissionId: "key_1" });
});

it("F1: a short check never freezes or shows a full answer", async () => {
  api.getProbeContract.mockResolvedValue({
    version: 1, active: true, presentationId: "pres_1", episodeId: "ep_1", observationNumber: 1, maximumObservations: 3,
    forcedAttemptType: "diagnostic_probe",
    restrictions: { hintsDisabled: true, askTutorDisabled: true, workedExampleDisabled: true, answerRevealDisabled: true, feedbackDeferred: true }
  });
  render(<PracticeScreen {...props({ gradingReady: false })} />);
  fireEvent.change(await screen.findByRole("textbox", { name: "answer" }), { target: { value: "-3" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: /Submit/ }));
  });
  expect(await screen.findByRole("button", { name: "Got it" })).toBeTruthy();
  expect(api.recordSelfGradeDisclosure).not.toHaveBeenCalled();
  expect(screen.queryByText("Expand along the first row: det(A) = -3.")).toBeNull();
});
