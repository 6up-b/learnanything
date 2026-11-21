// UX Phase 4.4 (docs/specs/ux_learnloop_v1.md §7.5, session end): one calm,
// dismissible summary in the ○ ◌ ● vocabulary, never a full-screen HUD, with
// none of the decorative telemetry (registration codes, log numbers, a fake
// 0→100% meter). `[ui] practice_feedback = "classic"` restores the HUD.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { SessionEndSummary } from "../api/dto";
import { clear, setQueryData } from "../api/queryCache";
import { setAlgoConfig } from "../app/algoConfig";
import { SessionFinishHud } from "./SessionFinishHud";

const SUMMARY = {
  version: 1,
  sessionId: "01JSESSIONULIDXYZ1234567",
  startedAt: "2026-10-15T10:00:00Z",
  endedAt: "2026-10-15T10:26:10Z",
  attemptsRecorded: 11,
  itemsReviewed: 9,
  followupsQueued: 2,
  coldChecksCompleted: 0,
  coldChecksPassed: 0,
  streak: { current: 3, longest: 7, activeToday: true },
  facetsDemonstrated: 4,
  predictionsMoved: { up: 2, down: 1 },
  corrections: 0,
  misconceptionsTouched: { resolved: 0, returned: 0 },
  topics: [
    { learningObjectId: "lo_cond", title: "Conditional probability", evidence: "on_your_own" },
    { learningObjectId: "lo_mix", title: "Mixtures", evidence: "with_help" }
  ]
} as unknown as SessionEndSummary;

function bodyText(): string {
  return document.body.textContent ?? "";
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => undefined);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

it("is one calm summary: minutes, questions, and what moved in the well's words", () => {
  render(<SessionFinishHud summary={SUMMARY} onDismiss={vi.fn()} />);
  expect(screen.getByText("26 minutes this session · 9 questions")).toBeTruthy();
  const moved = screen.getByTestId("session-moved").textContent ?? "";
  expect(moved).toContain("● Conditional probability (on your own)");
  expect(moved).toContain("◌ Mixtures (with help)");
  const text = bodyText();
  for (const telemetry of ["LL//RUNNER", "LOG #", "K-12", "RLA", "STATUS OK", "FINALIZING", "%", "facets", "predictions", "FOLLOW-UPS"]) {
    expect(text).not.toContain(telemetry);
  }
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("dismisses on Done, Enter or Escape", async () => {
  const onDismiss = vi.fn();
  render(<SessionFinishHud summary={SUMMARY} onDismiss={onDismiss} />);
  fireEvent.click(screen.getByRole("button", { name: /Done/ }));
  expect(onDismiss).toHaveBeenCalledTimes(1);
  await act(async () => {
    fireEvent.keyDown(window, { key: "Escape" });
  });
  expect(onDismiss).toHaveBeenCalledTimes(2);
  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
  expect(onDismiss).toHaveBeenCalledTimes(3);
});

it("says nothing about topics when none moved, and never counts what did not", () => {
  render(<SessionFinishHud summary={{ ...SUMMARY, topics: [] }} onDismiss={vi.fn()} />);
  expect(screen.getByText("26 minutes this session · 9 questions")).toBeTruthy();
  expect(screen.queryByTestId("session-moved")).toBeNull();
});

it("classic restores the full-screen HUD", () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<SessionFinishHud summary={SUMMARY} onDismiss={vi.fn()} />);
  expect(screen.getByRole("dialog", { name: "Session complete" })).toBeTruthy();
});

it("a topic answered partly right on your own and finished with help says both, never only 'on your own' (UX-49)", () => {
  const topics = [
    { learningObjectId: "lo_diag", title: "Construct a diagonalization from an eigenvector basis", evidence: "on_your_own", finishedWithHelp: true },
    { learningObjectId: "lo_cond", title: "Conditional probability", evidence: "on_your_own" },
    { learningObjectId: "lo_mix", title: "Mixtures", evidence: "with_help" }
  ];
  render(<SessionFinishHud summary={{ ...SUMMARY, topics } as unknown as SessionEndSummary} onDismiss={vi.fn()} />);
  const moved = screen.getByTestId("session-moved").textContent ?? "";
  expect(moved).toContain("● Construct a diagonalization from an eigenvector basis (partly on your own, finished with help)");
  expect(moved).not.toContain("Construct a diagonalization from an eigenvector basis (on your own)");
  expect(moved).toContain("● Conditional probability (on your own)");
  expect(moved).toContain("◌ Mixtures (with help)");
});

// The finish says what comes next, dated, from the summary read at the session's end.
const NEXT = {
  asOf: "2026-10-31T23:00:00Z",
  calendar: { zone: "EDT", today: "2026-10-31", tomorrow: "2026-11-01", nextDayStartsAt: "2026-11-01T04:00:00Z" },
  reviews: [
    { date: "2026-11-01", count: 2, itemIds: ["pi_dst", "pi_tomorrow"], learningObjectIds: ["lo_tomorrow"], minutes: 3.0 },
    { date: "2026-11-09", count: 1, itemIds: ["pi_nine"], learningObjectIds: ["lo_nine"], minutes: 2.5 }
  ],
  checks: [{ date: "2026-11-14", count: 1, itemIds: ["pi_checked"], learningObjectIds: ["lo_checked"], kinds: ["cold_retry"] }],
  nextReviewDate: "2026-11-01",
  writing: { topicCount: 3, learningObjectIds: ["lo_b", "lo_c", "lo_d"] },
  waiting: { sectionCount: 0 },
  held: { topicCount: 0, learningObjectIds: [] }
};

it("says what comes next, dated: tomorrow's questions, the check's first day, what is still being written", () => {
  render(<SessionFinishHud summary={{ ...SUMMARY, nextPractice: NEXT } as unknown as SessionEndSummary} onDismiss={vi.fn()} />);
  const next = screen.getByTestId("session-next").textContent ?? "";
  expect(next).toContain("Tomorrow: 2 questions you answered come back · about 3 minutes.");
  expect(next).toContain("A check on your own is available from 14 November.");
  expect(next).toContain("Questions on 3 more topics are still being written.");
});

it("with nothing due tomorrow names the next day, and says what is still due today", () => {
  const next = {
    ...NEXT,
    reviews: [{ date: "2026-10-31", count: 1, itemIds: ["pi_left"], learningObjectIds: ["lo_left"], minutes: null }, NEXT.reviews[1]],
    nextReviewDate: "2026-11-09",
    checks: [],
    writing: { topicCount: 0, learningObjectIds: [] }
  };
  render(<SessionFinishHud summary={{ ...SUMMARY, nextPractice: next } as unknown as SessionEndSummary} onDismiss={vi.fn()} />);
  expect(screen.getByTestId("session-next").textContent).toBe(
    "Still due today: 1 question.1 more question you answered comes back on 9 November."
  );
});

// UX-69 (the live walk partread-3): a question Today offered from the reading, kept after an answer for a check on the
// learner's own, is named as that question where the books are known (Today and feedback read them before the finish).
it("names a question from the reading kept for a check, with its day, in place of the bare check line", () => {
  setQueryData(["get_source_library"], { version: 1, pending: [], sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readerEnabled: true,
    statusLine: { text: "", tone: "quiet", action: null, details: null,
      questions: { count: 2, itemIds: ["pi_checked", "pi_dst"], sections: ["Document"], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 1 } } }] });
  render(<SessionFinishHud summary={{ ...SUMMARY, nextPractice: NEXT } as unknown as SessionEndSummary} onDismiss={vi.fn()} />);
  const next = screen.getByTestId("session-next").textContent ?? "";
  expect(next).toContain("1 question from your reading is kept for a check on your own, available from 14 November.");
  expect(next).not.toContain("A check on your own is available from 14 November.");
  clear();
});

it("says nothing of what comes next when the summary is missing or holds nothing", () => {
  render(<SessionFinishHud summary={{ ...SUMMARY, nextPractice: null } as unknown as SessionEndSummary} onDismiss={vi.fn()} />);
  expect(screen.queryByTestId("session-next")).toBeNull();
  cleanup();
  render(<SessionFinishHud summary={SUMMARY} onDismiss={vi.fn()} />);
  expect(screen.queryByTestId("session-next")).toBeNull();
});
