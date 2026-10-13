// The Guide plan's own refresh rules (guide-overlay Codex review F1), without
// the Reader's open-time outbox drain that also marks every per-source read
// stale: a plan waiting on a diagnosis is re-read, attempt and diagnosis
// changes invalidate the cached plan, and a mounted Guide re-reads until the
// diagnosis lands. Real api client and query cache over a fake sidecar.
import { act, cleanup, render, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { api } from "../../api/client";
import type { ReaderGuidePlanDto } from "../../api/dto";
import { clear } from "../../api/queryCache";
import { DiagnosisCard } from "../../components/DiagnosisCard";
import {
  GUIDE_DIAGNOSIS_POLL_MAX_MS,
  GUIDE_DIAGNOSIS_POLL_MS,
  readGuidePlan,
  useGuideDiagnosisRefresh
} from "./guidePlan";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));

const SOURCE = { sourceId: "src1", extractionId: "ext1" };
/** `"absent"`: a sidecar that predates the pending list. */
const backend = { pending: ["att_1"] as string[] | "absent", guidePlanCalls: 0 };

function plan(pending: string[] | "absent" = backend.pending): ReaderGuidePlanDto {
  return {
    version: 1,
    sourceId: SOURCE.sourceId,
    extractionId: SOURCE.extractionId,
    personalized: true,
    selectionBasis: "",
    goalContext: null,
    sections: [],
    ...(pending === "absent" ? {} : { pendingDiagnosisAttemptIds: pending })
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  clear();
  backend.pending = ["att_1"];
  backend.guidePlanCalls = 0;
  invoke.mockReset().mockImplementation(async (command: string) => {
    switch (command) {
      case "reader_guide_plan":
        backend.guidePlanCalls += 1;
        return plan();
      case "submit_attempt":
        return { version: 1, attemptId: "att_2" };
      case "diagnosis_status":
        return { version: 1, attemptId: "att_1", status: "done", cardEnabled: false, responses: [], diagnosisId: "diag_1" };
      default:
        throw { code: "not_mocked", message: `${command} is not mocked`, retryable: false };
    }
  });
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

async function flush(ms = 0) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

it("re-reads a cached plan that waits on a diagnosis, and serves a settled one from the cache", async () => {
  expect((await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId)).pendingDiagnosisAttemptIds).toEqual(["att_1"]);
  backend.pending = [];
  expect((await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId)).pendingDiagnosisAttemptIds).toEqual([]);
  expect(backend.guidePlanCalls).toBe(2);

  // Settled: within the Reader's freshness window the cache answers.
  await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId);
  expect(backend.guidePlanCalls).toBe(2);
});

it("an attempt mutation invalidates the cached plan", async () => {
  backend.pending = [];
  await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId);
  await api.submitAttempt({} as Parameters<typeof api.submitAttempt>[0]);
  await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId);
  expect(backend.guidePlanCalls).toBe(2);
});

it("a diagnosis landing on the feedback screen invalidates the cached plan", async () => {
  // A sidecar that predates the pending list: only the invalidation helps.
  backend.pending = "absent";
  await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId);
  render(<DiagnosisCard attemptId="att_1" initialStatus="pending" onError={() => undefined} />);
  await flush();
  await readGuidePlan(SOURCE.sourceId, SOURCE.extractionId);
  expect(backend.guidePlanCalls).toBe(2);
});

it("a mounted Guide re-reads until the diagnosis lands, then stops", async () => {
  const onPlan = vi.fn();
  const { rerender } = renderHook(({ shown }) => useGuideDiagnosisRefresh(SOURCE, shown, onPlan), {
    initialProps: { shown: plan(["att_1"]) }
  });
  await flush(GUIDE_DIAGNOSIS_POLL_MS - 1);
  expect(backend.guidePlanCalls).toBe(0);

  backend.pending = [];
  await flush(1);
  expect(backend.guidePlanCalls).toBe(1);
  expect(onPlan).toHaveBeenLastCalledWith(plan([]));

  rerender({ shown: onPlan.mock.lastCall![0] as ReaderGuidePlanDto });
  await flush(10 * GUIDE_DIAGNOSIS_POLL_MAX_MS);
  expect(backend.guidePlanCalls).toBe(1);
});

it("backs off while the diagnosis stays pending, and stops on unmount", async () => {
  const onPlan = vi.fn();
  const hook = renderHook(() => useGuideDiagnosisRefresh(SOURCE, plan(["att_1"]), onPlan));
  await flush(60_000);
  // 4 s, then ×1.5 per step: 4, 10, 19, 32.5, 52.75 s into the minute.
  expect(backend.guidePlanCalls).toBe(5);
  await flush(10 * GUIDE_DIAGNOSIS_POLL_MAX_MS);
  expect(backend.guidePlanCalls).toBeGreaterThanOrEqual(13);
  expect(backend.guidePlanCalls).toBeLessThanOrEqual(16);

  const calls = backend.guidePlanCalls;
  hook.unmount();
  await flush(10 * GUIDE_DIAGNOSIS_POLL_MAX_MS);
  expect(backend.guidePlanCalls).toBe(calls);
});

it("does not poll for a plan that waits on nothing or for another source", async () => {
  const onPlan = vi.fn();
  renderHook(() => useGuideDiagnosisRefresh(SOURCE, plan("absent"), onPlan));
  renderHook(() => useGuideDiagnosisRefresh(SOURCE, plan([]), onPlan));
  renderHook(() => useGuideDiagnosisRefresh({ sourceId: "src2", extractionId: "ext2" }, plan(["att_1"]), onPlan));
  renderHook(() => useGuideDiagnosisRefresh(null, plan(["att_1"]), onPlan));
  await flush(10 * GUIDE_DIAGNOSIS_POLL_MAX_MS);
  expect(backend.guidePlanCalls).toBe(0);
  expect(onPlan).not.toHaveBeenCalled();
});
