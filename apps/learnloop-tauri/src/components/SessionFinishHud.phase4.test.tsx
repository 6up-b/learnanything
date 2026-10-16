// UX Phase 4.4 (docs/specs/ux_learnloop_v1.md §7.5, session end): one calm,
// dismissible summary in the ○ ◌ ● vocabulary, never a full-screen HUD, with
// none of the decorative telemetry (registration codes, log numbers, a fake
// 0→100% meter). `[ui] practice_feedback = "classic"` restores the HUD.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { SessionEndSummary } from "../api/dto";
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
  expect(screen.getByText("26 minutes · 9 questions")).toBeTruthy();
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
  expect(screen.getByText("26 minutes · 9 questions")).toBeTruthy();
  expect(screen.queryByTestId("session-moved")).toBeNull();
});

it("classic restores the full-screen HUD", () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  render(<SessionFinishHud summary={SUMMARY} onDismiss={vi.fn()} />);
  expect(screen.getByRole("dialog", { name: "Session complete" })).toBeTruthy();
});
