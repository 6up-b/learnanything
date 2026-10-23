import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { IntentCheckDto } from "../api/dto";
import { IntentCheckFeedback } from "./IntentCheckFeedback";

afterEach(cleanup);

const back = {
  label: "Back to where you studied this",
  detail: "Mixture CDF → integration bounds",
  inquiryRootEventIds: ["ev_1"],
  anchorSpanIds: ["sp_9"],
  extractionId: "ex_1",
  sourceId: "src_1"
};

it("says the attempt was the check and offers the way back only when the provenance carries it", () => {
  const onOpenStudied = vi.fn();
  const check: IntentCheckDto = { kind: "check_once", commitmentId: "c_1", restoration: back };
  render(<IntentCheckFeedback check={check} onOpenStudied={onOpenStudied} />);
  expect(screen.getByTestId("intent-check-feedback").textContent).toContain("Your check on your own.");
  fireEvent.click(screen.getByText("Back to where you studied this: Mixture CDF → integration bounds"));
  expect(onOpenStudied).toHaveBeenCalledWith(back);
});

it("renders no link without a way back, and nothing for an ordinary attempt", () => {
  const { rerender } = render(
    <IntentCheckFeedback check={{ kind: "check_once", commitmentId: "c_1", restoration: null }} onOpenStudied={vi.fn()} />
  );
  expect(screen.queryByRole("button")).toBeNull();
  rerender(<IntentCheckFeedback check={undefined} onOpenStudied={vi.fn()} />);
  expect(screen.queryByTestId("intent-check-feedback")).toBeNull();
});
