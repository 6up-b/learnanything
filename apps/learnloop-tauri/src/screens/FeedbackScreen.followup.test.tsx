// FG1 §6: the feedback screen while a follow-up workflow owns the attempt: the hold, the
// wait on Next, Continue without it, Show anyway, the failure line and the router's line.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, FollowupDto } from "../api/dto";
import { clear } from "../api/queryCache";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value?: string }) => (value?.startsWith("CAUSE:") ? <span>{value}</span> : null) }));
vi.mock("../components/ClaimSurface", () => ({ ClaimSurface: () => null, mintVisitId: () => "visit" }));
vi.mock("../components/KnowledgeModel", () => ({ AttemptTraceView: () => null, UnresolvedCauseCard: () => null }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/RepairTrace", () => ({ RepairTraceBlocks: () => null }));
vi.mock("../components/RepairAffordances", () => ({ CommonRepairCard: () => null, GuidedRedoAffordance: () => null }));

import { FeedbackScreen } from "./FeedbackScreen";

const HELD: FollowupDto = {
  workflowId: "fw_1", state: "pending", held: true, line: "Preparing a question on this…", canShowAnyway: true,
  canContinueWithout: true, shownAnyway: false,
};

const BUNDLE = {
  version: 1, attemptId: "att_1", practiceItemId: "pi_1", learningObjectId: "lo", learningObjectTitle: "Eigenvalues",
  rubricScore: 0, maxPoints: 4, correctness: 0, graderConfidence: 0.9, gradingSource: "ai", fallbackReason: null,
  manualReviewReason: null, fsrsRating: "again", nextDueAt: "2026-10-20T00:00:00Z", criterionEvidence: [], fatalErrors: [],
  errorAttributions: [],
  surprise: { predictiveSurprise: null, bayesianSurprise: null, surpriseDirection: null, fsrsIntervalFactor: null,
    followupThresholdNats: null, triggeredActions: [], suppressedActions: [], gateDiagnostics: null },
  masteryBefore: null, masteryAfter: null, masteryStep: null, feedbackMd: null, repairSuggestions: [],
  guidedRedoAvailable: false, interventionNeed: null, primed: false, sourceRefs: [], followupQueued: false,
} as unknown as FeedbackBundle;

let status: Record<string, unknown>;
let nextAnswers: Array<Record<string, unknown>>;
let displayed: number;
beforeEach(() => {
  status = { version: 1, enabled: true, ...HELD };
  nextAnswers = [];
  displayed = 0;
  invoke.mockImplementation(async (command: string) => {
    switch (command) {
      case "get_feedback":
        return { ...BUNDLE, followup: HELD };
      case "get_practice_item":
        return { id: "pi_1", prompt: "Q", expectedAnswer: "THE ANSWER", evidenceFacets: [] };
      case "followup_status":
        return status;
      case "followup_next":
        return nextAnswers.shift() ?? { version: 1, action: "continue", line: null, practiceItemId: null, presentationId: null };
      case "followup_show_anyway":
        return { released: true };
      case "followup_continue_without":
        return { continued: true };
      case "record_answer_display":
        displayed += 1;
        return { recordedAt: new Date().toISOString(), alreadyRecorded: false };
      default:
        return null;
    }
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

function show(extra: Record<string, unknown> = {}) {
  const callbacks = { onNext: vi.fn(), onOpenNext: vi.fn() };
  render(
    <FeedbackScreen attemptId="att_1" sessionId="s1" onOpenNext={callbacks.onOpenNext} onNext={callbacks.onNext}
      onBack={vi.fn()} onOpenNotes={vi.fn()} onPrimedRetry={vi.fn()} onInspect={vi.fn()} onAsk={vi.fn()} onError={vi.fn()}
      {...extra} />
  );
  return callbacks;
}

it("says it is preparing a question, holds the answer and records no display", async () => {
  show();
  expect(await screen.findByTestId("followup-line")).toBeTruthy();
  expect(screen.getByTestId("followup-held")).toBeTruthy();
  expect(screen.queryByText("THE ANSWER")).toBeNull();
  await act(async () => { await Promise.resolve(); });
  expect(displayed).toBe(0);
});

it("waits on Next with the same words, and offers Continue without it", async () => {
  nextAnswers = [{ version: 1, action: "wait", line: "Preparing a question on this…", practiceItemId: null, presentationId: null }];
  const callbacks = show();
  await screen.findByTestId("followup-line");
  await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
  const leave = await screen.findByText("Continue without it");
  expect(callbacks.onNext).not.toHaveBeenCalled();
  status = { version: 1, enabled: true, ...HELD, state: "skipped", held: false, line: null, canContinueWithout: false, canShowAnyway: false };
  await act(async () => { fireEvent.click(leave); });
  await waitFor(() => expect(invoke.mock.calls.some(([command]) => command === "followup_continue_without")).toBe(true));
  await waitFor(() => expect(callbacks.onNext).toHaveBeenCalled());
});

it("opens the probe when Next says so", async () => {
  nextAnswers = [{ version: 1, action: "open", line: null, practiceItemId: "pi_generated", presentationId: "pp" }];
  const callbacks = show();
  await screen.findByTestId("followup-line");
  await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
  await waitFor(() => expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_generated", null));
});

it("Show anyway asks once, and what was held comes back through a fresh read", async () => {
  show();
  const link = await screen.findByText("Show anyway");
  status = { version: 1, enabled: true, ...HELD, state: "ready", held: false, canShowAnyway: false, shownAnyway: true };
  await act(async () => { fireEvent.click(link); });
  await waitFor(() => expect(invoke.mock.calls.filter(([command]) => command === "get_feedback").length).toBeGreaterThan(1));
  expect(invoke.mock.calls.filter(([command]) => command === "followup_show_anyway").length).toBe(1);
});

it("shows the router's decision line with details on demand", async () => {
  invoke.mockImplementation(async (command: string) => {
    if (command === "get_feedback") {
      return { ...BUNDLE, followup: { ...HELD, state: "settled", held: false, line: null, routerDecision: {
        decisionId: "d1", line: "Router: no question · drawn by LLM · ask now 62%, no question 38% · floor 5%",
        details: { cardSummary: "card", models: [{ name: "LLM", status: "answered", answer: { a: 1 } }], rationale: "because", fallback: null },
      } } };
    }
    return null;
  });
  show();
  expect((await screen.findByTestId("router-decision")).textContent).toContain("Router: no question");
  fireEvent.click(within(screen.getByTestId("router-decision")).getByText("details"));
  expect(screen.getByTestId("router-decision-details").textContent).toContain("because");
});

it("while the causes are held, details says the rest comes later and shows no card", async () => {
  invoke.mockImplementation(async (command: string) => {
    if (command === "get_feedback") {
      return { ...BUNDLE, followup: { ...HELD, routerDecision: {
        decisionId: "d1", line: "Router: ask now · drawn by LLM · ask now 62%, wait 38% · floor 5%",
        details: { held: true, cardSummary: null, models: [{ name: "LLM", status: "answered", answer: { a: 1 } }], rationale: null, fallback: null },
      } } };
    }
    return null;
  });
  show();
  fireEvent.click(within(await screen.findByTestId("router-decision")).getByText("details"));
  const details = screen.getByTestId("router-decision-details").textContent ?? "";
  expect(details).toContain("comes after the question");
  expect(details).not.toContain("Why:");
  expect(invoke.mock.calls.some(([command]) => command === "followup_show_anyway")).toBe(false);
});

it("with no workflow the screen is what it was", async () => {
  invoke.mockImplementation(async (command: string) => (command === "get_feedback" ? BUNDLE : null));
  show();
  await screen.findByTestId("feedback-surface");
  expect(screen.queryByTestId("followup-panel")).toBeNull();
  expect(invoke.mock.calls.some(([command]) => String(command).startsWith("followup_"))).toBe(false);
});

// F22, R13: a reply to Next from the poll goes through the same path as the first press.
const WAITING = { version: 1, action: "wait", line: "Preparing a question on this…", practiceItemId: null, presentationId: null };

async function pressNextAndWait() {
  const callbacks = show();
  await screen.findByTestId("followup-line");
  await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
  await screen.findByText("Continue without it");
  return callbacks;
}

it("goes on when the poll's Next says continue, though the workflow is still pending", async () => {
  // The router chose to wait while Next was waiting: the answer is released, the question is still being written.
  nextAnswers = [WAITING, { version: 1, action: "continue", line: null, practiceItemId: null, presentationId: null }];
  const callbacks = await pressNextAndWait();
  status = { version: 1, enabled: true, ...HELD, state: "pending", held: false };
  await waitFor(() => expect(callbacks.onNext).toHaveBeenCalledTimes(1), { timeout: 4000 });
  expect(callbacks.onOpenNext).not.toHaveBeenCalled();
});

it("opens the probe when the poll's Next says open", async () => {
  nextAnswers = [WAITING, { version: 1, action: "open", line: null, practiceItemId: "pi_generated", presentationId: "pp" }];
  const callbacks = await pressNextAndWait();
  await waitFor(() => expect(callbacks.onOpenNext).toHaveBeenCalledWith("pi_generated", null), { timeout: 4000 });
  expect(callbacks.onOpenNext).toHaveBeenCalledTimes(1);
  expect(callbacks.onNext).not.toHaveBeenCalled();
});

it("keeps waiting when the poll's Next says wait, and asks again", async () => {
  nextAnswers = [WAITING, WAITING, WAITING, WAITING];
  const callbacks = await pressNextAndWait();
  const asked = () => invoke.mock.calls.filter(([command]) => command === "followup_next").length;
  await waitFor(() => expect(asked()).toBeGreaterThanOrEqual(2), { timeout: 4000 });
  expect(callbacks.onNext).not.toHaveBeenCalled();
  expect(callbacks.onOpenNext).not.toHaveBeenCalled();
  expect(screen.getByText("Continue without it")).toBeTruthy();
});

it("goes on in plan mode through the plan's step when the poll's Next says continue", async () => {
  nextAnswers = [WAITING, { version: 1, action: "continue", line: null, practiceItemId: null, presentationId: null }];
  const onPlanStep = vi.fn();
  const callbacks = show({ nextPlan: { sessionId: "s1" }, onPlanStep });
  await screen.findByTestId("followup-line");
  await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
  await waitFor(() => expect(onPlanStep).toHaveBeenCalledTimes(1), { timeout: 4000 });
  expect(callbacks.onNext).not.toHaveBeenCalled();
});

// FG1c §7: the marks follow §6.0. Hidden while held, on the screen once released; Next stays free.
const MARKS = {
  attemptId: "att_1", surface: "marks_feedback", orderSeed: "seed", probeAnswered: false, replacesCardTap: true,
  hypotheses: [{ hypothesisVersionId: "h1", statement: "CAUSE: the first", mark: null },
               { hypothesisVersionId: "h2", statement: "CAUSE: the second", mark: null }],
  noneOfThese: false, noneOfTheseText: null,
};
const OPEN: FollowupDto = { ...HELD, state: "settled", held: false, line: null, canShowAnyway: false, canContinueWithout: false };

function withBundle(bundle: Record<string, unknown>, status2?: Record<string, unknown>) {
  invoke.mockImplementation(async (command: string) => {
    switch (command) {
      case "get_feedback":
        return bundle;
      case "followup_status":
        return status2 ?? { version: 1, enabled: false };
      case "record_hypothesis_exposure":
        return { version: 1, recorded: true };
      case "record_hypothesis_mark":
        return { version: 1, recorded: true, marks: MARKS };
      default:
        return null;
    }
  });
}

it("held, there is no list and nothing is receipted, and the way out says why", async () => {
  show();
  await screen.findByTestId("followup-held");
  expect(screen.queryByTestId("hypothesis-marks")).toBeNull();
  expect(screen.getByTestId("followup-held").textContent).toContain("possible causes come after the question");
  await act(async () => { await Promise.resolve(); });
  expect(invoke.mock.calls.some(([command]) => command === "record_hypothesis_exposure")).toBe(false);
});

it("Show anyway brings the list back through the fresh read, and it is receipted when shown", async () => {
  let shown = false;
  invoke.mockImplementation(async (command: string) => {
    switch (command) {
      case "get_feedback":
        return shown ? { ...BUNDLE, followup: { ...HELD, state: "ready", held: false, shownAnyway: true }, hypothesisMarks: MARKS }
          : { ...BUNDLE, followup: HELD };
      case "followup_status":
        return { version: 1, enabled: true, ...HELD, state: "ready", held: !shown ? true : false, shownAnyway: shown };
      case "followup_show_anyway":
        shown = true;
        return { released: true };
      case "record_hypothesis_exposure":
        return { version: 1, recorded: true };
      default:
        return null;
    }
  });
  show();
  fireEvent.click(await screen.findByText("Show anyway"));
  expect(await screen.findByTestId("hypothesis-marks")).toBeTruthy();
  await waitFor(() => expect(invoke.mock.calls.filter(([command]) => command === "record_hypothesis_exposure").length).toBe(1));
});

it("with no probe the list is on the feedback screen, and marking never waits on or blocks Next", async () => {
  withBundle({ ...BUNDLE, followup: { ...OPEN, state: "settled" }, hypothesisMarks: { ...MARKS, replacesCardTap: false } });
  const callbacks = show();
  fireEvent.click((await screen.findAllByText("Not it"))[0]);
  await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
  await waitFor(() => expect(callbacks.onNext).toHaveBeenCalled());
});

it("an answer to the probe shows the earlier miss's list and receipts it under the miss", async () => {
  withBundle({ ...BUNDLE, attemptId: "att_probe", heldFeedbackAttemptId: "att_1",
               hypothesisMarks: { ...MARKS, surface: "marks_probe_feedback", probeAnswered: true } });
  show({ attemptId: "att_probe" });
  await screen.findByTestId("hypothesis-marks");
  await waitFor(() => expect(invoke.mock.calls.some(([command]) => command === "record_hypothesis_exposure")).toBe(true));
  const event = invoke.mock.calls.find(([command]) => command === "record_hypothesis_exposure");
  expect(JSON.stringify(event)).toContain('"attemptId":"att_1"');
  expect(JSON.stringify(event)).toContain('"surface":"marks_probe_feedback"');
  // The probe's own lists aren't the miss's, so nothing else is receipted for them.
  expect(invoke.mock.calls.filter(([command]) => command === "record_hypothesis_exposure").length).toBe(1);
});

it("the switch off, or nothing to mark, leaves no panel and no call", async () => {
  withBundle({ ...BUNDLE, followup: OPEN });
  show();
  await screen.findByTestId("followup-panel");
  await act(async () => { await Promise.resolve(); });
  expect(screen.queryByTestId("hypothesis-marks")).toBeNull();
  expect(invoke.mock.calls.some(([command]) => String(command).includes("hypothesis"))).toBe(false);
});

const CARD = {
  version: 1, status: "done", attemptId: "att_1", cardEnabled: true, diagnosisId: "d1", summaryMd: "A summary.",
  repairSuggestions: [], madeBefore: [], prerequisiteGap: null, escalation: null, recordedResponse: null,
  notSameMistakeAttemptIds: [], responses: [{ response: "believed_candidate", label: "That's it" }, { response: "diagnosis_wrong", label: "That's wrong" }],
};

it.each([
  ["on the probe lane the marks replace the card's tap", true],
  ["elsewhere the card's tap stays", false],
])("%s", async (_name, replaces) => {
  invoke.mockImplementation(async (command: string) => {
    switch (command) {
      case "get_feedback":
        return { ...BUNDLE, diagnosisStatus: "done", followup: OPEN, hypothesisMarks: { ...MARKS, replacesCardTap: replaces } };
      case "diagnosis_status":
        return CARD;
      case "record_hypothesis_exposure":
        return { version: 1, recorded: true };
      default:
        return null;
    }
  });
  show();
  await screen.findByTestId("hypothesis-marks");
  fireEvent.keyDown(window, { key: "." });
  await screen.findByTestId("diagnosis-card");
  expect(screen.queryByTestId("diagnosis-taps") !== null).toBe(!replaces);
});

it("each other list of the attempt's causes is receipted when it is on screen, in its own order", async () => {
  invoke.mockImplementation(async (command: string) => {
    switch (command) {
      case "get_feedback":
        return { ...BUNDLE, followup: OPEN, hypothesisMarks: MARKS, causalFeedback: {
          causalHypotheses: [{ hypothesisId: "h9", label: "Possible", statement: "CAUSE: a", causeScope: "learner_state", supportScore: null }],
          demonstratedCriteria: [], unverified: [], verifiedCorrection: null, proposedNextAction: null,
          contestAction: { available: false, reasons: [], factorId: null },
        } };
      case "record_hypothesis_exposure":
        return { version: 1, recorded: true };
      default:
        return null;
    }
  });
  show();
  await screen.findByTestId("hypothesis-marks");
  const surfaces = () => invoke.mock.calls.filter(([command]) => command === "record_hypothesis_exposure").map((call) => JSON.stringify(call));
  await waitFor(() => expect(surfaces().length).toBe(1));
  expect(surfaces().some((row) => row.includes('"surface":"why"'))).toBe(false);
  fireEvent.click(await screen.findByText(/why\?/));
  await waitFor(() => expect(surfaces().some((row) => row.includes('"surface":"why"') && row.includes('"hypothesisVersionIds":["h9"]'))).toBe(true));
});
