import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { FacetIdentityActionDto, FacetIdentitySummaryDto } from "../api/dto";
import { FacetIdentityPanel, facetIdentityOf } from "./FacetIdentityPanel";

const { api } = vi.hoisted(() => ({ api: { undoFacetIdentityAction: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
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
    locked: false,
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
