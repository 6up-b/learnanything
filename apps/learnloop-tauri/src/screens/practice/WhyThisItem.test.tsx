// Adaptive difficulty AD2+AD3 (§12): "why this item" shows the draw's one line,
// and nothing when no AD draw chose the item or the sidecar has no such RPC.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

const whyItem = vi.fn();
vi.mock("../../api/client", () => ({ api: { adaptiveDifficultyWhyItem: (input: unknown) => whyItem(input) } }));

import { WhyThisItem } from "./WhyThisItem";

afterEach(() => {
  cleanup();
  whyItem.mockReset();
});

it("shows the band line for an item the band draw chose", async () => {
  whyItem.mockResolvedValue({ version: 1, why: "Picked to be challenging but doable for you (about a 3 in 4 chance)", mode: "band" });
  render(<WhyThisItem planPresentationId="pp1" />);
  await waitFor(() => expect(screen.getByTestId("why-this-item").textContent).toContain("about a 3 in 4 chance"));
  expect(whyItem).toHaveBeenCalledWith({ planPresentationId: "pp1" });
});

it("shows nothing without a draw, without a presentation, or with an older sidecar", async () => {
  whyItem.mockResolvedValue({ version: 1, why: null, mode: null });
  render(<WhyThisItem planPresentationId="pp2" />);
  await waitFor(() => expect(whyItem).toHaveBeenCalled());
  expect(screen.queryByTestId("why-this-item")).toBeNull();
  cleanup();
  whyItem.mockReset();
  render(<WhyThisItem planPresentationId={null} />);
  expect(whyItem).not.toHaveBeenCalled();
  cleanup();
  whyItem.mockRejectedValue({ code: "stale_app_binary", message: "old" });
  render(<WhyThisItem planPresentationId="pp3" />);
  await waitFor(() => expect(whyItem).toHaveBeenCalled());
  expect(screen.queryByTestId("why-this-item")).toBeNull();
});
