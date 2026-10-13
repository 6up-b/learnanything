import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { FacetRewordConfirmDto } from "../api/dto";
import { RewordConfirmList, supportLine, valueText } from "./RewordConfirms";

const { api } = vi.hoisted(() => ({ api: { decideFacetReword: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

function confirm(overrides: Partial<FacetRewordConfirmDto> = {}): FacetRewordConfirmDto {
  return {
    actionId: "act_reword",
    facetId: "facet_svd_factorization",
    title: "SVD",
    fields: ["claim"],
    changes: [{ field: "claim", before: "SVD factorizes into U, Sigma, V^T.", after: "Every real matrix factorizes as U Sigma V^T." }],
    sources: [],
    unresolved: [],
    message: "The proposed new wording of facet facet_svd_factorization (claim) has no textbook … source behind it",
    proposalId: "patch_1",
    proposalItemId: "item_1",
    runId: "run_1",
    createdAt: "2026-10-13T14:00:00Z",
    status: "pending",
    decidedAt: null,
    interrupted: null,
    ...overrides
  };
}

it("shows the wording before and after and says plainly that it cites no source", () => {
  render(<RewordConfirmList confirms={[confirm()]} />);
  const card = screen.getByTestId("reword-confirm").textContent ?? "";
  expect(card).toContain("facet_svd_factorization");
  expect(card).toContain("SVD factorizes into U, Sigma, V^T.");
  expect(card).toContain("Every real matrix factorizes as U Sigma V^T.");
  expect(card).toContain("It cites no source.");
  expect(screen.getByRole("button", { name: "confirm reword" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "keep current wording" })).toBeTruthy();
});

it("confirms with one tap and leaves the list", async () => {
  api.decideFacetReword.mockResolvedValue({ version: 1, status: "applied", actionId: "act_reword" });
  const onDecided = vi.fn();
  render(<RewordConfirmList confirms={[confirm()]} onDecided={onDecided} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "confirm reword" }));
  });
  expect(api.decideFacetReword).toHaveBeenCalledWith("act_reword", "confirm");
  expect(onDecided).toHaveBeenCalledWith(expect.objectContaining({ actionId: "act_reword" }), "confirm");
  expect(screen.queryByTestId("reword-confirm")).toBeNull();
});

it("keeps the current wording with one tap", async () => {
  api.decideFacetReword.mockResolvedValue({ version: 1, status: "kept", actionId: "act_reword" });
  render(<RewordConfirmList confirms={[confirm()]} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "keep current wording" }));
  });
  expect(api.decideFacetReword).toHaveBeenCalledWith("act_reword", "keep");
});

it("reports a refused confirm and keeps the card", async () => {
  api.decideFacetReword.mockRejectedValue({ code: "changed_since", message: "Facet facet_svd_factorization's wording changed" });
  const onError = vi.fn();
  render(<RewordConfirmList confirms={[confirm()]} onError={onError} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "confirm reword" }));
  });
  expect(onError).toHaveBeenCalledWith("Facet facet_svd_factorization's wording changed");
  expect(screen.getByTestId("reword-confirm")).toBeTruthy();
});

it("names each source with its excerpt, and never an exam's text", () => {
  render(
    <RewordConfirmList
      confirms={[
        confirm({
          sources: [
            {
              sourceId: "src_notes", revisionId: "rev_notes", extractionId: "ext_notes", unitId: "unit_notes", spanId: "s1",
              role: "notes", relation: "support", locator: "span:ext_notes/s1", assessmentOnly: false,
              excerpt: "My notes on the SVD."
            },
            {
              sourceId: "src_exam", revisionId: "rev_exam", extractionId: "ext_exam", unitId: "paper_2024", spanId: "s1",
              role: "exam", relation: "assessment_alignment", locator: "span:ext_exam/s1", assessmentOnly: true, excerpt: null
            }
          ]
        })
      ]}
    />
  );
  const card = screen.getByTestId("reword-confirm").textContent ?? "";
  expect(card).toContain("My notes on the SVD.");
  expect(card).toContain("notes · unit_notes");
  expect(card).toContain("text hidden");
  expect(card).toContain("It cites only notes, exam material");
});

it("lists only pending rewords", () => {
  const { container } = render(<RewordConfirmList confirms={[confirm({ status: "kept" })]} />);
  expect(container.textContent).toBe("");
});

it("describes support and values in plain words", () => {
  expect(supportLine(confirm({ unresolved: ["ext_two:s2: span s2 is outside the selected units"] }))).toContain(
    "outside the units you selected"
  );
  expect(valueText(["the matrix is real", "square"])).toBe("the matrix is real\nsquare");
  expect(valueText(null)).toBe("—");
});
