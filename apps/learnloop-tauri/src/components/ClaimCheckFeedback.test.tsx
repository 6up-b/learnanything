import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import type { ClaimCheckDto } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { ClaimCheckFeedback } from "./ClaimCheckFeedback";

afterEach(cleanup);

it("says once, quietly, that the review checked what you marked as known", () => {
  const check: ClaimCheckDto = {
    claim: "marked_known",
    check: "missed",
    line: "You marked this as known; this check: missed."
  };
  render(<ClaimCheckFeedback check={check} />);
  const line = screen.getByTestId("claim-check-feedback");
  expect(line.textContent).toBe("You marked this as known; this check: missed.");
  expect(findJargon(line.textContent ?? "")).toEqual([]);
  expect(line.textContent).not.toMatch(/%|score|calibrat|overconfident|accurate/i);
});

it("renders nothing on a review that resolved no claim", () => {
  render(<ClaimCheckFeedback check={undefined} />);
  expect(screen.queryByTestId("claim-check-feedback")).toBeNull();
});
