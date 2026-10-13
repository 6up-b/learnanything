/**
 * The Reader Guide's plan read and its refresh while a diagnosis is pending.
 *
 * Under the Slice 1 split a blind-graded error's misconception statement comes
 * from the asynchronous diagnosis. Until it lands, a "Revisit this to
 * resolve" reason names the error type, and the plan lists the attempts it is
 * waiting on (`pendingDiagnosisAttemptIds`). The Reader re-reads the plan
 * while that list is non-empty, so the Guide names the diagnoser's statement
 * without a reopen. RW3a's margin cues read the same plan and refresh with it.
 */
import { useEffect, useRef } from "react";
import { api } from "../../api/client";
import type { ReaderGuidePlanDto } from "../../api/dto";
import { peek, type QueryKey } from "../../api/queryCache";
import { TAG } from "../../api/queryTags";
import { cachedSourceRead } from "./readerCache";

/** First re-read after the plan is seen waiting; later ones back off. */
export const GUIDE_DIAGNOSIS_POLL_MS = 4_000;
/** A diagnosis held up for long (provider off, budget) is re-checked at this pace. */
export const GUIDE_DIAGNOSIS_POLL_MAX_MS = 60_000;

/**
 * Learner state the plan reads besides its source: mastery and items (graph),
 * the active goal (goals), and active errors with the diagnoses laid over
 * them (errors). Attempt mutations invalidate all three; a landed diagnosis
 * invalidates `errors`.
 */
const GUIDE_PLAN_STATE_TAGS = [TAG.graph, TAG.goals, TAG.errors] as const;

export function guidePlanKey(extractionId: string): QueryKey {
  return ["reader_guide_plan", extractionId];
}

/** The attempts whose pending diagnosis can still change one of the plan's reasons. */
export function pendingDiagnoses(plan: ReaderGuidePlanDto | null | undefined): readonly string[] {
  return plan?.pendingDiagnosisAttemptIds ?? [];
}

/**
 * Read a source's Guide plan through the Reader cache. A cached plan that was
 * waiting on a diagnosis is re-read instead of served: the diagnosis may have
 * landed while no Reader was open.
 */
export function readGuidePlan(
  sourceId: string,
  extractionId: string,
  options: { force?: boolean } = {}
): Promise<ReaderGuidePlanDto> {
  const key = guidePlanKey(extractionId);
  const waiting = pendingDiagnoses(peek<ReaderGuidePlanDto>(key).data).length > 0;
  return cachedSourceRead(sourceId, key, () => api.readerGuidePlan({ extractionId }), {
    tags: GUIDE_PLAN_STATE_TAGS,
    force: options.force || waiting
  });
}

/**
 * While the shown plan waits on a diagnosis, re-read it (backing off from
 * GUIDE_DIAGNOSIS_POLL_MS to GUIDE_DIAGNOSIS_POLL_MAX_MS) and hand each fresh
 * plan to `onPlan`. Stops when the plan waits on nothing, on a source change
 * and on unmount; polls never overlap. A failed read is retried at the next
 * step. The plan build is a local read and writes nothing.
 */
export function useGuideDiagnosisRefresh(
  source: { sourceId: string; extractionId: string } | null,
  plan: ReaderGuidePlanDto | null,
  onPlan: (plan: ReaderGuidePlanDto) => void
): void {
  const sourceId = source?.sourceId ?? null;
  const extractionId = source?.extractionId ?? null;
  const waitingOn = plan !== null && plan.extractionId === extractionId ? pendingDiagnoses(plan).join("\n") : "";
  const onPlanRef = useRef(onPlan);
  onPlanRef.current = onPlan;

  useEffect(() => {
    if (!sourceId || !extractionId || !waitingOn) return;
    let cancelled = false;
    let delay = GUIDE_DIAGNOSIS_POLL_MS;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const poll = () => {
      timer = null;
      readGuidePlan(sourceId, extractionId, { force: true })
        .then((next) => {
          if (!cancelled && next.extractionId === extractionId) onPlanRef.current(next);
        })
        .catch(() => undefined)
        .finally(() => {
          if (cancelled) return;
          delay = Math.min(GUIDE_DIAGNOSIS_POLL_MAX_MS, Math.round(delay * 1.5));
          timer = setTimeout(poll, delay);
        });
    };
    timer = setTimeout(poll, delay);
    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [sourceId, extractionId, waitingOn]);
}
