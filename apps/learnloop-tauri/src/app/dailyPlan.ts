// Daily-loop DL1: the finite daily plan on the desktop (spec_daily_loop_v1.md §6.5-§6.7, §6.10).
//
// The plan DTO is the only source of every number shown (gate G3): these
// helpers format and route what the sidecar returns and compute nothing new.
// While the plan is off (`enabled: false`), Start, Today and feedback's Next
// behave exactly as DL0 (gate G1).

import { useCallback, useMemo } from "react";
import { api } from "../api/client";
import type { DailyPlanDto, PlanItemStepDto, PlanReadingDto, PlanStepDto, SourceLibraryCard } from "../api/dto";
import { getOrFetch, hashKey, isStale, peek, type QueryKey } from "../api/queryCache";
import { TAG } from "../api/queryTags";
import { useCachedQuery } from "../api/useCachedQuery";

/** "about 8 min": estimates are always labelled as estimates (L1). */
export function aboutMinutes(minutes: number | null | undefined): string {
  const value = Math.max(1, Math.round(minutes ?? 0));
  return `about ${value} min`;
}

/**
 * Minutes a day as computed, rounded honestly (L1): whole minutes from 1 up,
 * one decimal below ("0.3"), never rounded up to 1.
 */
export function minutesPerDay(minutes: number | null | undefined): string {
  const value = Math.max(0, minutes ?? 0);
  if (value >= 1) return String(Math.round(value));
  if (value > 0 && value < 0.05) return "less than 0.1";
  return String(Math.round(value * 10) / 10);
}

/** Whole minutes for actual time ("26 min"), never below zero. */
export function wholeMinutes(minutes: number | null | undefined): number {
  return Math.max(0, Math.round(minutes ?? 0));
}

export function dailyPlanKey(sessionId: string | null | undefined): QueryKey {
  return ["get_daily_plan", sessionId ?? null];
}

/** Today's plan, cached with the queue (attempts and plan writes invalidate it). */
export function useDailyPlan(sessionId: string | null | undefined, enabled = true) {
  const id = sessionId ?? null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const key = useMemo(() => dailyPlanKey(id), [id]);
  // A client without the RPC (an older sidecar) reads as "plan off", never a crash.
  return useCachedQuery<DailyPlanDto>(enabled ? key : null, () => Promise.resolve().then(() => api.getDailyPlan(id)), {
    tags: [TAG.queue]
  });
}

export type PlanStepAction =
  | { type: "practice"; practiceItemId: string; schedulerCandidateId: string | null }
  | { type: "reader"; reading: PlanReadingDto }
  | { type: "plan" };

/**
 * Where a plan step takes the learner. An item inside the current block opens
 * directly (auto-advance, §6.5); the first item of a new block goes through the
 * plan view's block line ("Block 2 of about 3 · …", continue on Enter); a
 * reading step opens the reader at its section; "done" shows the done screen.
 */
export function planStepAction(step: PlanStepDto | null | undefined, { viaBlockLine = true } = {}): PlanStepAction {
  if (!step) return { type: "plan" };
  if (step.kind === "item") {
    if (step.boundary && viaBlockLine) return { type: "plan" };
    return { type: "practice", practiceItemId: step.practiceItemId, schedulerCandidateId: step.schedulerCandidateId ?? null };
  }
  if (step.kind === "reading") {
    if (step.boundary && viaBlockLine) return { type: "plan" };
    return { type: "reader", reading: step.reading };
  }
  return { type: "plan" };
}

/** The library card and span a reading step opens the reader at. */
export function readerTargetForReading(
  reading: PlanReadingDto,
  library: SourceLibraryCard[] | null | undefined
): { card: SourceLibraryCard; spanId: string | null } | null {
  const card = (library ?? []).find((entry) => entry.sourceId === reading.sourceId);
  return card ? { card, spanId: reading.startSpanId ?? null } : null;
}

export interface NextPlanStep {
  /** The prefetched next step (read while feedback shows), when current. */
  readonly step: PlanStepDto | null;
  /** Serve the next step when it continues the current block; otherwise name it. */
  readonly resolve: () => Promise<PlanStepDto | null>;
}

const MAX_STEP_READS = 4;

/**
 * Feedback's Next under the plan (§6.5): the next step is computed while
 * feedback shows (the boundary decision itself happens then, §6.8 rule 5),
 * and Next serves it. Mirrors `useNextQueueItem`: a step read before the latest
 * invalidation (an answer, a regrade, a forced follow-up) names nothing.
 */
export function useNextPlanStep(sessionId: string | null, prefetch: boolean): NextPlanStep {
  const hash = sessionId ? hashKey(["next_plan_item", sessionId]) : null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const key = useMemo<QueryKey | null>(() => (sessionId ? ["next_plan_item", sessionId] : null), [hash]);
  const query = useCachedQuery<DailyPlanDto>(
    prefetch ? key : null,
    () => api.nextPlanItem({ sessionId, serve: false }),
    { tags: [TAG.queue] }
  );
  const current = query.data !== undefined && !query.refreshing;
  const step = current ? query.data?.step ?? null : null;

  const resolve = useCallback(async (): Promise<PlanStepDto | null> => {
    if (!key || !sessionId) return null;
    for (let read = 0; read < MAX_STEP_READS; read += 1) {
      const snapshot = await getOrFetch<DailyPlanDto>(key, () => api.nextPlanItem({ sessionId, serve: false }), {
        tags: [TAG.queue],
        staleAfterMs: Infinity
      });
      const state = peek<DailyPlanDto>(key);
      if (isStale(state, Infinity)) continue;
      const next = (state.data ?? snapshot)?.step ?? null;
      if (next && next.kind === "item" && !next.boundary) {
        // Inside the block: serve it now, with the offer that ranked it.
        const served = await api.nextPlanItem({ sessionId, serve: true });
        return served.step ?? null;
      }
      return next;
    }
    return null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { step, resolve };
}

/** The key bar's promise for Next under the plan. */
export function nextPlanKeyLabel(advancing: boolean, step: PlanStepDto | null): string {
  if (advancing) return "opening next…";
  if (!step) return "next";
  if (step.kind === "done") return "today's plan is done";
  if (step.kind === "reading") return `next: continue reading ${step.reading.sectionTitle ?? ""}`.trim();
  if (step.boundary) return "next block";
  return `next: ${(step as PlanItemStepDto).learningObjectTitle ?? "next item"}`;
}
