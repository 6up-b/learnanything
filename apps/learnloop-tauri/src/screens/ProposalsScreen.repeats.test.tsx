// UX Phase 2, a finding Phase 1's usability round 1 deferred here (M-h,
// docs/reviews/ux-phase1.md): "Proposals grows on every practice, with
// duplicate error-type proposals." The duplicates are real rows: every grading
// that names an error type the vault doesn't have yet writes a new proposal
// batch for it, even while an earlier one waits (a data issue, recorded in
// docs/reviews/ux-phase2.md; its fix changes what grading writes, so it is not
// this display-only stage's). The display says so: the first waiting proposal
// of an entity shows how many times it was proposed, each later one is marked
// as a repeat. The classic shell shows the list as before.
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import type { ProposalBatchDto, ProposalItemDto, ProposalsSnapshot } from "../api/dto";

function item(id: string, entity: string, overrides: Partial<ProposalItemDto> = {}): ProposalItemDto {
  return {
    id,
    clientItemId: `error_type:${entity}`,
    itemType: "error_type",
    operation: "create",
    decision: "pending",
    proposedEntityId: entity,
    targetEntityType: null,
    targetEntityId: null,
    reviewRoute: "review_required",
    validationStatus: "valid",
    validationErrors: [],
    edited: false,
    applied: false,
    rationale: "Proposed error taxonomy entries from grading.",
    sourceRefs: [],
    payloadLines: [],
    payloadJson: "{}",
    ...overrides
  };
}

function batch(id: string, items: ProposalItemDto[]): ProposalBatchDto {
  return {
    id,
    summary: "Proposed error taxonomy entries from grading.",
    purpose: "grading_error_type",
    status: "open",
    createdAt: null,
    updatedAt: null,
    agentRun: { id: `run_${id}`, model: null, provider: null, purpose: "grading_error_type", codexRevision: null, startedAt: null, durationS: null, status: "done" } as ProposalBatchDto["agentRun"],
    counts: { pending: items.length, accepted: 0, rejected: 0 } as ProposalBatchDto["counts"],
    items
  };
}

const snapshot: ProposalsSnapshot = {
  version: 1,
  batches: [
    batch("b3", [item("i3", "conceptual_schema_error")]),
    batch("b2", [item("i2", "conceptual_schema_error")]),
    batch("b1", [item("i1", "local_slip")]),
    batch("b0", [item("i0", "conceptual_schema_error", { decision: "rejected" })])
  ],
  totals: { pending: 3, accepted: 0, rejected: 1 } as ProposalsSnapshot["totals"],
  batchCount: 4,
  rewordConfirms: []
};

vi.mock("../api/client", () => ({
  api: new Proxy({} as Record<string, unknown>, {
    get: (_target, name: string) => (name === "getProposals" ? async () => snapshot : () => new Promise(() => undefined))
  })
}));

import { ProposalsScreen, repeatedPendingProposals } from "./ProposalsScreen";
import { clear as clearQueryCache } from "../api/queryCache";

afterEach(() => {
  cleanup();
  clearQueryCache();
  setAlgoConfig({});
});

describe("repeatedPendingProposals", () => {
  it("counts the waiting proposals of one entity, first shown first, rejected ones aside", () => {
    const repeats = repeatedPendingProposals(snapshot.batches);
    expect(repeats.get("i3")).toEqual({ firstItemId: "i3", count: 2 });
    expect(repeats.get("i2")).toEqual({ firstItemId: "i3", count: 2 });
    expect(repeats.has("i1")).toBe(false);
    expect(repeats.has("i0")).toBe(false);
  });
});

function rowOf(itemId: string): HTMLElement {
  return screen.getByText(itemId).closest("[data-proposal-item-id]") as HTMLElement;
}

describe("the Proposals list (Under the hood → Study-map changes)", () => {
  it("says how many times a waiting proposal was made, and marks the repeats", async () => {
    setAlgoConfig({});
    render(<ProposalsScreen authoringReady={false} authoringProvider="codex" onInspect={() => undefined} onError={() => undefined} />);
    await screen.findAllByText("conceptual_schema_error");
    expect(within(rowOf("i3")).getByText("proposed 2×")).toBeTruthy();
    expect(within(rowOf("i2")).getByText("repeat")).toBeTruthy();
    expect(within(rowOf("i1")).queryByText(/repeat|proposed/)).toBeNull();
  });

  it("shows the list as before in the classic shell", async () => {
    setAlgoConfig({ ui: { shell: "classic" } });
    render(<ProposalsScreen authoringReady={false} authoringProvider="codex" onInspect={() => undefined} onError={() => undefined} />);
    await screen.findAllByText("conceptual_schema_error");
    expect(screen.queryByText("proposed 2×")).toBeNull();
    expect(screen.queryByText("repeat")).toBeNull();
  });
});
