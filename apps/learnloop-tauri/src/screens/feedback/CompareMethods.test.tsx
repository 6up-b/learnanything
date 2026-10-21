// Reader workbench RW2c (spec §5.10, G40; UX §5.9): "compare methods ▸" after
// a correct workbench Submit. Offered only for a correct, unheld answer the
// server says is a workbench problem; opening it shows the learner's steps
// beside the reference (labelled by where it comes from) and then the
// AI-written lines, labelled; nothing is asked for on a wrong answer.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { COMPARE_COPY, CompareMethods } from "./CompareMethods";

const api = vi.hoisted(() => ({
  workbenchCompareOffer: vi.fn(), workbenchCompareMethods: vi.fn(), workbenchHelpJob: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const COMPARISON = {
  assistId: "ha_cmp", revealId: "rv_1",
  learner: { label: "Your steps", steps: [{ number: 1, kind: "step", bodyMd: "F(x) = x^2" }, { number: 2, kind: "step", bodyMd: "P = F(1/2) = 1/4" }] },
  reference: { kind: "item_key", label: "The item's answer key", text: "Integrate the density from 0 to 1/2." },
  lines: null,
};
const LINES = {
  differences: [{ kind: "method", learnerStep: 1, line: "You started from the CDF; the key integrates the density." }],
  routeLine: "Your route is valid — a different method from the reference.", sameMethod: false, learnerRouteValid: true,
  dropped: 0, label: "AI-written: one line per difference",
};

beforeEach(() => {
  vi.resetAllMocks();
});

afterEach(() => cleanup());

it("is not asked for on a wrong or held answer", async () => {
  const { rerender } = render(<CompareMethods attemptId="att_1" correctness={0.5} held={false} />);
  rerender(<CompareMethods attemptId="att_1" correctness={1} held />);
  await new Promise((resolve) => setTimeout(resolve, 10));
  expect(api.workbenchCompareOffer).not.toHaveBeenCalled();
  expect(screen.queryByTestId("feedback-compare-methods")).toBeNull();
});

it("is shown only when the server offers it", async () => {
  api.workbenchCompareOffer.mockResolvedValue({ version: 1, available: false, reason: "not_a_workbench_submit" });
  render(<CompareMethods attemptId="att_1" correctness={1} held={false} />);
  await waitFor(() => expect(api.workbenchCompareOffer).toHaveBeenCalledWith({ attemptId: "att_1" }));
  expect(screen.queryByText(COMPARE_COPY.offer)).toBeNull();
});

it("opens the two routes side by side, then the labelled lines and the valid-route line", async () => {
  api.workbenchCompareOffer.mockResolvedValue({ version: 1, available: true, reason: null, referenceKind: "item_key", label: "Compare with the book's method" });
  api.workbenchCompareMethods.mockResolvedValue({ version: 1, comparison: COMPARISON, linesJobId: "job_cmp" });
  api.workbenchHelpJob.mockResolvedValue({ version: 1, jobId: "job_cmp", kind: "compare", state: "done",
    result: { status: "ready", assistId: "ha_cmp", lines: LINES } });
  render(<CompareMethods attemptId="att_1" correctness={1} held={false} />);
  fireEvent.click(await screen.findByText(COMPARE_COPY.offer));
  await screen.findByText("P = F(1/2) = 1/4");
  expect(api.workbenchCompareMethods).toHaveBeenCalledWith({ attemptId: "att_1" });
  expect(screen.getByText("The item's answer key")).toBeTruthy();
  expect(screen.getByText("Integrate the density from 0 to 1/2.")).toBeTruthy();
  expect((await screen.findByTestId("compare-route-line")).textContent).toBe(LINES.routeLine);
  expect(screen.getByText(/You started from the CDF/).textContent).toContain("step 1 · ");
  expect(screen.getByText(/AI-written: one line per difference/)).toBeTruthy();
});

it("a book solution is labelled by its source, and a failed comparison keeps the reference", async () => {
  api.workbenchCompareOffer.mockResolvedValue({ version: 1, available: true, reason: null, referenceKind: "book_solution" });
  api.workbenchCompareMethods.mockResolvedValue({ version: 1, linesJobId: "job_cmp", comparison: {
    ...COMPARISON, reference: { kind: "book_solution", label: "The book's solution · Exercise 5.14 · p. 219", text: "By symmetry…", extractionId: "ext", spanIds: ["sol"], page: 219 } } });
  api.workbenchHelpJob.mockResolvedValue({ version: 1, jobId: "job_cmp", kind: "compare", state: "done",
    result: { status: "unavailable", reason: "capped", message: "Today's workbench budget is used; the reference is still shown." } });
  render(<CompareMethods attemptId="att_2" correctness={1} held={false} />);
  fireEvent.click(await screen.findByText(COMPARE_COPY.offer));
  await screen.findByText("By symmetry…");
  expect(screen.getByText(/The book's solution · Exercise 5.14 · p. 219/)).toBeTruthy();
  await screen.findByText("Today's workbench budget is used; the reference is still shown.");
  expect(screen.queryByTestId("compare-route-line")).toBeNull();
});
