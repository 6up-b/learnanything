import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { FacetDetailDto, FacetIdentityActionDto } from "../api/dto";
import { FacetInspector, historyLine } from "./FacetInspector";

// Facet identity locks were removed (owner, 2026-10-12). The inspector shows no
// padlock; it shows the facet's version and its history (rewords keep the old
// wording), each entry with its one-tap undo.

const { api } = vi.hoisted(() => ({
  api: {
    getFacetDetail: vi.fn(),
    getFacetEvidenceTimeline: vi.fn(),
    undoFacetIdentityAction: vi.fn()
  }
}));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

const reword: FacetIdentityActionDto = {
  id: "act_r",
  origin: "proposal",
  scope: "vault",
  runId: "run_1",
  proposalId: "prop_1",
  action: "reword",
  absorbAs: null,
  survivor: { id: "facet_svd", claim: "Old claim." },
  retired: [],
  rationale: "",
  evidencedFacets: ["facet_svd"],
  reworded: { from: "Old claim.", to: "New claim.", fromVersion: 1, toVersion: 2, fields: ["claim"] },
  undoLimits: "attempts graded while the new wording stood keep the assessment contract they were graded against",
  judge: "proposal",
  judgeModel: null,
  status: "applied",
  undoable: true,
  createdAt: "2026-10-13T12:00:00Z",
  undoneAt: null
};

function detail(version: number, history: FacetIdentityActionDto[]): FacetDetailDto {
  return {
    version: 1,
    facet: {
      id: "facet_svd", title: "SVD", kind: "definition", claim: version === 2 ? "New claim." : "Old claim.",
      preconditions: [], positiveExamples: [], negativeExamples: [], nonGoals: [], errorSignatures: [],
      aliases: [], status: "reviewed", version
    },
    history,
    membership: [],
    evidence: { ready: null, readyGhost: null, evidenceMass: 0, capabilityLedger: [] },
    sharedWith: []
  };
}

it("shows the version and a reword's old wording, with no lock chip", async () => {
  api.getFacetDetail.mockResolvedValue(detail(2, [reword]));
  api.getFacetEvidenceTimeline.mockReturnValue(new Promise(() => {})); // the receipt stays loading
  await act(async () => {
    render(<FacetInspector facetId="facet_svd" onClose={vi.fn()} onInspect={vi.fn()} />);
  });
  const history = screen.getByTestId("facet-history").textContent ?? "";
  expect(history).toContain("v1 → v2: claim reworded");
  expect(history).toContain("was: Old claim.");
  expect(screen.getByText("v2")).toBeTruthy();
  expect(document.body.textContent).not.toMatch(/\block|padlock/i);
  expect(historyLine({ ...reword, action: "merge", reworded: null, retired: [{ id: "facet_x", claim: "x" }] })).toBe(
    "merged facet_x into this facet"
  );
});

it("undoes a reword from the history and re-reads the facet", async () => {
  api.getFacetDetail.mockResolvedValueOnce(detail(2, [reword]));
  api.getFacetDetail.mockResolvedValueOnce(detail(1, [{ ...reword, status: "undone", undoable: false }]));
  api.getFacetEvidenceTimeline.mockReturnValue(new Promise(() => {})); // the receipt stays loading
  api.undoFacetIdentityAction.mockResolvedValue({ version: 1, status: "undone", action: null });
  await act(async () => {
    render(<FacetInspector facetId="facet_svd" onClose={vi.fn()} onInspect={vi.fn()} />);
  });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "undo" }));
  });
  expect(api.undoFacetIdentityAction).toHaveBeenCalledWith("act_r");
  expect(api.getFacetDetail).toHaveBeenCalledTimes(2);
  expect(screen.getByText("v1")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "undo" })).toBeNull();
});
