// FG1 §6: the feedback screen while a follow-up workflow owns the attempt: the hold, the
// wait on Next, Continue without it, Show anyway, the failure line and the router's line.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, FollowupDto } from "../api/dto";
import { clear } from "../api/queryCache";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
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
