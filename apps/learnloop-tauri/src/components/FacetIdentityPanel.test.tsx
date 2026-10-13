import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { FacetIdentityActionDto, FacetIdentitySummaryDto } from "../api/dto";
import { evidenceLabel, FacetIdentityPanel, facetIdentityOf } from "./FacetIdentityPanel";

const { api } = vi.hoisted(() => ({
  api: { undoFacetIdentityAction: vi.fn(), listFacetIdentityActions: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

function action(overrides: Partial<FacetIdentityActionDto> = {}): FacetIdentityActionDto {
  return {
    id: "act_1",
    origin: "ingest",
    scope: "in_run",
    runId: "run_1",
    proposalId: "prop_1",
    action: "merge",
    absorbAs: null,
    survivor: { id: "facet_a", claim: "A vector space is a set with addition and scalar multiplication." },
    retired: [{ id: "facet_b", claim: "A vector space is a set equipped with addition and scalar multiplication." }],
    rationale: "Both state the vector-space definition.",
    judge: "llm",
    judgeModel: "gpt-6-luna",
    status: "applied",
    undoable: true,
    createdAt: "2026-10-12T12:00:00Z",
    undoneAt: null,
    ...overrides
  };
}

function summary(actions: FacetIdentityActionDto[], status = "judged"): FacetIdentitySummaryDto {
  return { status, groups: 1, groupsJudged: 1, inRunRetired: actions.length, attached: 0, judge: "gpt-6-luna", notes: [], actions };
}

it("lists each merge and undoes it with one tap", async () => {
  api.undoFacetIdentityAction.mockResolvedValue({
    version: 1, status: "undone", action: action({ status: "undone", undoable: false })
  });
  const onError = vi.fn();
  render(<FacetIdentityPanel summary={summary([action()])} onError={onError} />);
  expect(screen.getByTestId("facet-identity").textContent).toContain("merged into");
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "undo" }));
  });
  expect(api.undoFacetIdentityAction).toHaveBeenCalledWith("act_1");
  expect(screen.queryByRole("button", { name: "undo" })).toBeNull();
  expect(screen.getByText("undone")).toBeTruthy();
  expect(onError).not.toHaveBeenCalled();
});

it("never offers an undo for a merge whose proposal is not applied", () => {
  render(<FacetIdentityPanel summary={summary([action({ status: "proposed", undoable: false })])} onError={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "undo" })).toBeNull();
  expect(screen.getByText("applies with the proposal")).toBeTruthy();
});

it("labels a merge that has no undo by construction", () => {
  render(
    <FacetIdentityPanel
      summary={summary([action({ undoable: false, note: "unavailable: the survivor was aliased by the mint gate" })])}
      onError={vi.fn()}
    />
  );
  expect(screen.queryByRole("button", { name: "undo" })).toBeNull();
  expect(screen.getByText("no undo")).toBeTruthy();
  expect(screen.getByTestId("facet-identity").textContent).toContain("aliased by the mint gate");
});

it("says when the duplicate check was skipped", () => {
  render(<FacetIdentityPanel summary={summary([], "judge_unavailable")} onError={vi.fn()} />);
  expect(screen.getByText(/duplicate check skipped/)).toBeTruthy();
});

it("renders nothing for a clean run and reads the job result block", () => {
  const { container } = render(<FacetIdentityPanel summary={summary([])} onError={vi.fn()} />);
  expect(container.innerHTML).toBe("");
  expect(facetIdentityOf({ facetIdentity: summary([]) })?.status).toBe("judged");
  expect(facetIdentityOf({})).toBeNull();
  expect(facetIdentityOf(null)).toBeNull();
});

it("reports an undo refusal", async () => {
  api.undoFacetIdentityAction.mockRejectedValue({ message: "Facet facet_a changed after action act_1" });
  const onError = vi.fn();
  render(<FacetIdentityPanel summary={summary([action()])} onError={onError} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "undo" }));
  });
  expect(onError).toHaveBeenCalledWith("Facet facet_a changed after action act_1");
  expect(screen.getByRole("button", { name: "undo" })).toBeTruthy();
});

// Review F6: the job result is a snapshot; the panel shows the live undo state.

it("re-reads the run's actions when it mounts: an action undone elsewhere shows undone", async () => {
  api.listFacetIdentityActions.mockResolvedValue({
    version: 1, actions: [action({ status: "undone", undoable: false, undoneAt: "2026-10-12T13:00:00Z" })]
  });
  await act(async () => {
    render(<FacetIdentityPanel summary={{ ...summary([action()]), runId: "run_1" }} onError={vi.fn()} />);
  });
  expect(api.listFacetIdentityActions).toHaveBeenCalledWith("run_1");
  expect(screen.queryByRole("button", { name: "undo" })).toBeNull();
  expect(screen.getByText("undone")).toBeTruthy();
});

it("offers the undo once a merge's proposal has been applied since the job ran", async () => {
  api.listFacetIdentityActions.mockResolvedValue({ version: 1, actions: [action()] });
  await act(async () => {
    render(<FacetIdentityPanel summary={summary([action({ status: "proposed", undoable: false })])} onError={vi.fn()} />);
  });
  expect(screen.getByRole("button", { name: "undo" })).toBeTruthy();
  expect(screen.queryByText("applies with the proposal")).toBeNull();
});

it("says whose evidence a merge re-keys and never mentions a lock (facet locks were removed)", () => {
  expect(evidenceLabel(action({ evidencedFacets: ["facet_a"] }))).toBe("re-keys one facet's recorded evidence to the survivor");
  expect(evidenceLabel(action({ evidencedFacets: ["facet_a", "facet_b"] }))).toContain("2 facets");
  expect(evidenceLabel(action())).toBeNull();
  render(<FacetIdentityPanel summary={summary([action({ evidencedFacets: ["facet_a"] })])} onError={vi.fn()} />);
  const text = screen.getByTestId("facet-identity").textContent ?? "";
  expect(text).not.toMatch(/\block|padlock/i);
  expect(text).toContain("re-keys one facet's recorded evidence");
  // Undo is honest about what it does not move back (review F9).
  expect(text).toContain("stays with the survivor");
});

it("shows a reword with both wordings, its versions and its undo", async () => {
  const reword = action({
    id: "act_r", origin: "proposal", scope: "vault", action: "reword", retired: [],
    evidencedFacets: ["facet_a"],
    reworded: { from: "Old claim.", to: "New claim.", fromVersion: 1, toVersion: 2, fields: ["claim"] }
  });
  api.undoFacetIdentityAction.mockResolvedValue({ version: 1, status: "undone", action: { ...reword, status: "undone", undoable: false } });
  render(<FacetIdentityPanel summary={summary([reword])} onError={vi.fn()} />);
  const text = screen.getByTestId("facet-identity").textContent ?? "";
  expect(text).toContain("Old claim.");
  expect(text).toContain("reworded (v1 → v2) to");
  expect(text).toContain("New claim.");
  expect(text).toContain("undo restores the old wording");
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "undo" }));
  });
  expect(api.undoFacetIdentityAction).toHaveBeenCalledWith("act_r");
  expect(screen.getByText("undone")).toBeTruthy();
});

it("marks an interrupted merge and says how to finish it", () => {
  render(<FacetIdentityPanel summary={summary([action({ status: "applying", undoable: false })])} onError={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "undo" })).toBeNull();
  expect(screen.getByText("interrupted")).toBeTruthy();
  expect(screen.getByTestId("facet-identity").textContent).toContain("doctor --fix-state");
});
