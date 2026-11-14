// A diagnostic check's teach hand-offs open a Teacher lesson on the check's topic, naming its episode; the tutor's
// proactive opening runs only as the fallback (lessons off, or a lesson that can't open). The review's tutoring route
// (simple and classic, Esc included) and the calibration dialogue's stop are tested here; the practice screen's stop
// in PracticeScreen.phase4.test.tsx, the dialogue panel's in DialogueProbe.test.tsx, the lesson screen's
// onOpenFailed in LessonScreen.test.tsx.
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ProbeBlockEndDto } from "../api/dto";
import type { LessonEntry } from "../screens/LessonScreen";
import { setAlgoConfig } from "./algoConfig";
import { type CheckHandoff, useCheckHandoff } from "./checkHandoff";

const { api, panel } = vi.hoisted(() => ({
  api: { getNextProbeItem: vi.fn(), startGuidedRedo: vi.fn(), getCalibrationSession: vi.fn(), stopCalibrationSession: vi.fn() },
  panel: { props: null as null | Record<string, unknown> }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ ProbeRemintAction: () => null }));
vi.mock("../components/CausalAttribution", () => ({ CausalFeedbackPanel: () => null }));
vi.mock("../components/DialogueProbe", () => ({
  DialogueProbePanel: (props: Record<string, unknown>) => {
    panel.props = props;
    return <div data-testid="dialogue-panel" />;
  }
}));

import { CalibrationScreen } from "../screens/CalibrationScreen";
import { DiagnosticReviewScreen } from "../screens/DiagnosticReviewScreen";

beforeEach(() => {
  setAlgoConfig({ teacher: { lessons: true }, ui: { practiceFeedback: "simple" } });
  api.getNextProbeItem.mockResolvedValue({ active: false });
  panel.props = null;
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setAlgoConfig(undefined);
});

// --- App's side: the lesson, or the fallback --------------------------------------------------------------------

function handoff(fallback = vi.fn()): CheckHandoff {
  return { learningObjectId: "lo_cond", title: "Conditional probability", probeEpisodeId: "ep_7", fallback };
}

function app() {
  const opened: Array<LessonEntry | null> = [];
  const notify = vi.fn();
  const hook = renderHook(({ entry }: { entry: LessonEntry | null }) =>
    useCheckHandoff((next) => { opened.push(next); hook?.rerender({ entry: next }); }, notify, entry),
    { initialProps: { entry: null as LessonEntry | null } });
  return { hook, opened, notify };
}

it("opens a lesson on the check's topic naming its episode, and keeps the tutor for a failed opening", () => {
  const { hook, opened, notify } = app();
  const fallback = vi.fn();
  expect(hook.result.current.openFailed).toBeUndefined();
  act(() => hook.result.current.teachFromCheck(handoff(fallback)));
  expect(opened).toEqual([{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_cond"],
                            title: "Conditional probability", probeEpisodeId: "ep_7" }]);
  expect(fallback).not.toHaveBeenCalled();
  // The lesson can't open (the teacher's route is down, lessons were switched off): the tutor opens, with a notice.
  expect(hook.result.current.openFailed).toBeDefined();
  act(() => hook.result.current.openFailed?.("The ChatGPT plan is unavailable for lessons."));
  expect(opened[opened.length - 1]).toBeNull();
  expect(fallback).toHaveBeenCalledOnce();
  expect(notify).toHaveBeenCalledWith("The ChatGPT plan is unavailable for lessons. The tutor opens instead.");
});

it("with lessons off the tutor opens at once and no lesson does", () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  const { hook, opened } = app();
  const fallback = vi.fn();
  act(() => hook.result.current.teachFromCheck(handoff(fallback)));
  expect(fallback).toHaveBeenCalledOnce();
  expect(opened).toEqual([]);
});

it("a lesson that closes normally drops the fallback", () => {
  const { hook } = app();
  const fallback = vi.fn();
  act(() => hook.result.current.teachFromCheck(handoff(fallback)));
  act(() => hook.rerender({ entry: null }));
  act(() => hook.rerender({ entry: null }));
  expect(hook.result.current.openFailed).toBeUndefined();
  expect(fallback).not.toHaveBeenCalled();
});

// --- the review's tutoring route ---------------------------------------------------------------------------------

function tutoringEnd(): ProbeBlockEndDto {
  return {
    episodeId: "ep_7", status: "complete",
    releasedFeedback: [{ attemptId: "att_1", practiceItemId: "pi_1", rubricScore: 1, maxPoints: 4, feedbackMd: null,
                         fatalErrors: [], heldForReview: false }],
    normalizedMisconceptionIds: [], openSet: null, completionReason: "decision_equivalence", firstErrorStepOrClaim: null,
    route: "tutoring", decision: null
  } as ProbeBlockEndDto;
}

function review(overrides: Partial<ComponentProps<typeof DiagnosticReviewScreen>> = {}) {
  const props: ComponentProps<typeof DiagnosticReviewScreen> = {
    blockEnd: tutoringEnd(), learningObjectId: "lo_cond", learningObjectTitle: "Conditional probability", sessionId: "s1",
    onContinueDiagnostic: vi.fn(), onAsk: vi.fn(), onTeachFromCheck: vi.fn(), onBack: vi.fn(), onError: vi.fn(),
    ...overrides
  };
  render(<DiagnosticReviewScreen {...props} />);
  return props;
}

function sentHandoff(onTeach: unknown): CheckHandoff {
  return (onTeach as ReturnType<typeof vi.fn>).mock.calls[0][0] as CheckHandoff;
}

it("the simple review's next step is \"Teach me this\": a lesson on the topic with the check's episode", () => {
  const props = review();
  fireEvent.click(screen.getByRole("button", { name: /Teach me this/ }));
  expect(props.onTeachFromCheck).toHaveBeenCalledWith(expect.objectContaining({
    learningObjectId: "lo_cond", title: "Conditional probability", probeEpisodeId: "ep_7" }));
  expect(props.onAsk).not.toHaveBeenCalled();
  expect(props.onBack).toHaveBeenCalledOnce();
  // Its fallback is today's proactive tutor opening on the block's first question.
  sentHandoff(props.onTeachFromCheck).fallback();
  expect(props.onAsk).toHaveBeenCalledWith({ context: "practice", practiceItemId: "pi_1", sessionId: "s1", proactiveOpen: true });
  expect(screen.queryByText(/tutor/i)).toBeNull();
});

it("the classic review says the same, and Esc (its continue) opens the lesson", async () => {
  setAlgoConfig({ teacher: { lessons: true }, ui: { practiceFeedback: "classic" } });
  const props = review();
  expect(screen.getByRole("button", { name: /Teach me this/ })).toBeTruthy();
  expect(screen.queryByText(/Start tutoring session/)).toBeNull();
  await act(async () => { fireEvent.keyDown(window, { key: "Escape" }); });
  expect(props.onTeachFromCheck).toHaveBeenCalledWith(expect.objectContaining({ learningObjectId: "lo_cond", probeEpisodeId: "ep_7" }));
  expect(props.onAsk).not.toHaveBeenCalled();
});

it("with lessons off the step says the tutor, on both screens", () => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  review();
  expect(screen.getByRole("button", { name: /Learn it with the tutor/ })).toBeTruthy();
  cleanup();
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  review();
  expect(screen.getByRole("button", { name: /Learn it with the tutor/ })).toBeTruthy();
});

// --- the calibration dialogue's stop (TH-1) ---------------------------------------------------------------------

it("the calibration dialogue's stop hands its topic to a lesson and returns to calibration's progress", async () => {
  api.getCalibrationSession.mockResolvedValue({
    version: 1, calibrationSessionId: "cal1", sessionId: "s1", goalId: null, status: "active", timeBudgetMinutes: 8,
    elapsedMinutes: 1, remainingMinutes: 7, blocksCompleted: 0, blocksPlanned: 2, episodes: [],
    nextTarget: { episodeId: null, learningObjectId: "lo_diag", practiceItemId: "pi_diag", selectionObjective: "conditional_gain",
                  entropy: null },
    quickCheck: null
  });
  const onTeachFromCheck = vi.fn();
  const onAsk = vi.fn();
  await act(async () => {
    render(<CalibrationScreen calibrationSessionId="cal1" onPractice={vi.fn()} onExit={vi.fn()} onError={vi.fn()}
                              onTeachFromCheck={onTeachFromCheck} onAsk={onAsk} />);
  });
  fireEvent.click(screen.getByText(/Diagnostic dialogue · lo_diag/));
  expect(screen.getByTestId("dialogue-panel")).toBeTruthy();
  expect(panel.props?.onTeachFromCheck).toBe(onTeachFromCheck);
  expect(panel.props?.onAsk).toBe(onAsk);
  // The panel hands off, then reports its block done: the screen is back on its progress, under the lesson.
  await act(async () => { (panel.props?.onDone as (end: null) => void)(null); });
  expect(screen.queryByTestId("dialogue-panel")).toBeNull();
  expect(screen.getByText(/Diagnostic dialogue · lo_diag/)).toBeTruthy();
  expect(api.getCalibrationSession).toHaveBeenCalledTimes(2);
});
