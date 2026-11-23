// The batch card offers what the sidecar says the host takes (a desktop copy of
// the retry rule offered "resume", not retry, for a cancelled synthesis), with
// the handler's own budget bounds, and an outline link only for a real import.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import type { IngestBatchDto, IngestJobView } from "../api/dto";
import { IngestActivityStack } from "./IngestActivity";

const api = vi.hoisted(() => ({
  listIngestBatches: vi.fn(),
  getIngestBatch: vi.fn(),
  getSettings: vi.fn(),
  getSynthesisCandidate: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));

const BOUNDS = {
  inventoryInputTokens: { min: 1_000, max: 2_000_000 },
  inventoryOutputTokens: { min: 1_000, max: 100_000 },
  synthesisShardInputTokens: { min: 10_000, max: 2_000_000 },
  synthesisShardOutputTokens: { min: 1_000, max: 200_000 },
  synthesisTotalInputCeiling: { min: 10_000, max: 2_000_000 },
  synthesisOutputTokens: { min: 1_000, max: 200_000 }
};

function job(id: string, jobType: string, status: IngestJobView["status"], extra: Partial<IngestJobView> = {}): IngestJobView {
  return {
    id, batchId: "batch_1", ordinal: 1, jobType, status, phase: null, message: null, currentWindow: null,
    totalWindows: null, attemptCount: 1, checkpointLadder: [], usage: {}, estimate: {}, source: null, result: null,
    error: null, waitingForInput: null, ...extra
  } as IngestJobView;
}

function batch(overrides: Partial<IngestBatchDto>): IngestBatchDto {
  return {
    id: "batch_1",
    workflowType: "bootstrap_synthesis",
    subjectId: null,
    sourceSetId: null,
    status: "cancelled",
    cancelRequested: true,
    createdAt: "2026-11-20T10:00:00Z",
    startedAt: "2026-11-20T10:00:00Z",
    finishedAt: "2026-11-20T10:05:00Z",
    jobs: [],
    canRetrySynthesis: false,
    retrySynthesisJobId: null,
    retrySynthesisRefusal: "no_unfinished_synthesis",
    canReuseCandidate: false,
    reuseCandidateRefusal: "no_unfinished_synthesis",
    ...overrides
  };
}

function show(value: IngestBatchDto) {
  api.listIngestBatches.mockResolvedValue({ batches: [value] });
  render(<IngestActivityStack focusBatchId={value.id} initialBatch={value} onOpenOutline={vi.fn()} />);
}

beforeEach(() => {
  clear();
  Element.prototype.scrollIntoView = vi.fn();
  for (const fn of Object.values(api)) fn.mockReset();
  api.getSettings.mockResolvedValue({ ingest: { budgetBounds: BOUNDS } });
  api.getSynthesisCandidate.mockResolvedValue({ synthesisRunId: "run_1", itemCounts: { concepts: 2 }, summary: null });
});

afterEach(() => cleanup());

const CANCELLED_SYNTHESIS = batch({
  jobs: [job("j_inv", "inventory", "completed"), job("j_syn", "bootstrap_synthesis", "cancelled")],
  canRetrySynthesis: true,
  retrySynthesisJobId: "j_syn",
  retrySynthesisRefusal: null,
  reuseCandidateRefusal: "no_preserved_candidate"
});

it("offers a synthesis-only retry for a cancelled synthesis the host would retry, not a resume", async () => {
  show(CANCELLED_SYNTHESIS);
  expect(await screen.findByRole("button", { name: "↻ retry synthesis" })).toBeTruthy();
  expect(screen.queryByText("↻ resume")).toBeNull();
});

it("offers a resume, and no retry, when the host would refuse the retry", async () => {
  show(batch({
    status: "failed",
    jobs: [job("j_inv", "inventory", "failed"), job("j_syn", "bootstrap_synthesis", "blocked")],
    retrySynthesisRefusal: "inventory_incomplete"
  }));
  expect(await screen.findByText("↻ resume")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "↻ retry synthesis" })).toBeNull();
});

it("validates the retry ceilings with the handler's bounds from settings", async () => {
  api.getSettings.mockResolvedValue({
    ingest: { budgetBounds: { ...BOUNDS, synthesisTotalInputCeiling: { min: 10_000, max: 50_000 } } }
  });
  show(CANCELLED_SYNTHESIS);
  // The suggested ceiling (100,000) is over this vault's handler maximum.
  const retry = (await screen.findByRole("button", { name: "↻ retry synthesis" })) as HTMLButtonElement;
  await waitFor(() => expect(retry.disabled).toBe(true));
});

it("offers no candidate revalidation when the host says the preserved candidate is gone", async () => {
  show(batch({
    status: "failed",
    jobs: [
      job("j_inv", "inventory", "completed"),
      job("j_syn", "bootstrap_synthesis", "failed", {
        error: { code: "synthesis_gate_failed", message: "gates", retryable: true,
                 details: { candidate_preserved: true, synthesis_run_id: "run_1" } }
      } as Partial<IngestJobView>)
    ],
    canRetrySynthesis: true,
    retrySynthesisJobId: "j_syn",
    retrySynthesisRefusal: null,
    canReuseCandidate: false,
    reuseCandidateRefusal: "candidate_gone"
  }));
  await screen.findByRole("button", { name: "↻ retry synthesis" });
  expect(screen.queryByText("↻ revalidate candidate (no new model run)")).toBeNull();
  expect(api.getSynthesisCandidate).not.toHaveBeenCalled();
});

it("links the outline for a finished import, and not for an exercise import whose workflow says import", async () => {
  const exercises = batch({
    id: "batch_ex",
    workflowType: "source_exercise_import",
    status: "completed",
    jobs: [job("j_ex", "source_exercise_import", "completed", { result: { sourceId: "src_ex" } } as Partial<IngestJobView>)]
  });
  show(exercises);
  await screen.findAllByText("source_exercise_import");
  expect(screen.queryByText("outline & select →")).toBeNull();
  cleanup();

  show(batch({
    id: "batch_imp",
    workflowType: "import",
    status: "completed",
    jobs: [job("j_imp", "import", "completed", { result: { sourceId: "src_book" } } as Partial<IngestJobView>)]
  }));
  expect(await screen.findByText("outline & select →")).toBeTruthy();
});
