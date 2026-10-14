// Daily-loop DL1: routing plan steps (§6.5, §6.10), the reader banner, and
// feedback's Next under the plan, through the real client and query cache.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { PlanStepDto, SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));

import { minutesPerDay, nextPlanKeyLabel, planStepAction, readerTargetForReading } from "./dailyPlan";
import { PlanReadingBanner } from "../components/PlanReadingBanner";

afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

const ITEM: PlanStepDto = {
  kind: "item", planId: "p", blockId: "b", blockOrdinal: 1, practiceItemId: "pi_1", learningObjectId: "lo",
  learningObjectTitle: "Eigenvalues", origin: "chooser", schedulerCandidateId: "cand_1", boundary: false
};
const READING: PlanStepDto = {
  kind: "reading", planId: "p", blockId: "b2", blockOrdinal: 2, estMinutes: 12, boundary: false,
  reading: { sourceId: "src_book", extractionId: "ext", sectionId: "s3", sectionTitle: "§3.2", wordsLeft: 1440, partial: false, startSpanId: "span_9" }
};

it("routes an item in the block straight to practice and a new block through the plan", () => {
  expect(planStepAction(ITEM)).toEqual({
    type: "practice", practiceItemId: "pi_1", schedulerCandidateId: "cand_1", planPresentationId: null
  });
  // Router R2a: a served step carries its presentation, the receipt the answer binds to.
  expect(planStepAction({ ...ITEM, presentationId: "pres_1" })).toMatchObject({ planPresentationId: "pres_1" });
  expect(planStepAction({ ...ITEM, boundary: true })).toEqual({ type: "plan" });
  // The plan view's own Continue serves a new block's first item directly.
  expect(planStepAction({ ...ITEM, boundary: true }, { viaBlockLine: false }).type).toBe("practice");
  expect(planStepAction({ kind: "done", planId: "p", status: "complete", stopReason: null })).toEqual({ type: "plan" });
  expect(planStepAction(null)).toEqual({ type: "plan" });
});

it("opens a reading step in the reader at its section's first span", () => {
  const action = planStepAction(READING);
  expect(action.type).toBe("reader");
  const card = { sourceId: "src_book", title: "Book" } as SourceLibraryCard;
  const target = readerTargetForReading((action as { reading: (typeof READING & { kind: "reading" })["reading"] }).reading, [card]);
  expect(target).toEqual({ card, spanId: "span_9" });
  expect(readerTargetForReading(READING.kind === "reading" ? READING.reading : (null as never), [])).toBeNull();
});

it("names what Next will do under the plan", () => {
  expect(nextPlanKeyLabel(false, ITEM)).toBe("next: Eigenvalues");
  expect(nextPlanKeyLabel(false, { ...ITEM, boundary: true })).toBe("next block");
  expect(nextPlanKeyLabel(false, READING)).toBe("next: continue reading §3.2");
  expect(nextPlanKeyLabel(false, { kind: "done", planId: "p", status: "complete", stopReason: null })).toBe("today's plan is done");
  expect(nextPlanKeyLabel(true, ITEM)).toBe("opening next…");
});

it("returns to the plan from the reader and records that the learner left it", async () => {
  invoke.mockResolvedValue({ version: 1, enabled: true, plan: null });
  const onBack = vi.fn();
  render(
    <PlanReadingBanner
      reading={READING.kind === "reading" ? READING.reading : (null as never)}
      estMinutes={12}
      sessionId="s1"
      onBack={onBack}
      onError={vi.fn()}
    />
  );
  expect(screen.getByTestId("plan-reading-banner").textContent).toContain("Reading for today's plan · §3.2 · about 12 min");
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Back to today's plan" }));
  });
  await waitFor(() => expect(onBack).toHaveBeenCalledOnce());
  expect(invoke).toHaveBeenCalledWith("plan_reading_ended", { input: { outcome: "left_reader", sessionId: "s1" } });
});

it("rounds minutes a day honestly: whole from 1, a decimal below, never up to 1", () => {
  expect(minutesPerDay(3.75)).toBe("4");
  expect(minutesPerDay(1)).toBe("1");
  expect(minutesPerDay(0.32)).toBe("0.3");
  expect(minutesPerDay(0.96)).toBe("1");
  expect(minutesPerDay(0.02)).toBe("less than 0.1");
  expect(minutesPerDay(0)).toBe("0");
});
