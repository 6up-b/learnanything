// Adaptive difficulty AD2+AD3 (§5.12, §12; D21): the dose offer appears only
// when the sidecar's draw offers an extra, is recorded delivered once shown,
// taken or dismissed with one key, says why it appeared, decides each section
// once, and shows nothing when the arm is off.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

const offer = vi.fn();
const event = vi.fn();
vi.mock("../../api/client", () => ({
  api: {
    readerDoseOffer: (input: unknown) => offer(input),
    readerDoseOfferEvent: (input: unknown) => event(input)
  }
}));

import { DoseOffer } from "./DoseOffer";

const SECTIONS = [{ id: "u1", label: "One", startSpanId: "s1", endSpanId: "s2", spanIds: ["s1", "s2"], question: null,
  suggestedPassages: [] }];

function renderOffer(overrides: Record<string, unknown> = {}) {
  const props = { extractionId: "ext1", sectionId: "u1", visitId: () => "visit1", boundaryChecksAvailable: true,
    cueDensityOff: false, skim: false, restoredSpanId: null, sections: SECTIONS, ...overrides };
  return render(<DoseOffer {...(props as any)} />);
}

afterEach(() => {
  cleanup();
  offer.mockReset();
  event.mockReset();
});

const EXTRA = { version: 1, eligible: true, reason: null, drawId: "d1",
  offer: { drawId: "d1", variant: "extra_worked_example", text: "One more worked example on this?",
    why: "Offered at random, to learn how much of this helps you", content: { extractionId: "ext1", spanId: "we2" } } };

it("shows the offer, records it delivered, and takes it", async () => {
  offer.mockResolvedValue(EXTRA);
  event.mockResolvedValue({ version: 1, rowId: "r", event: "x" });
  const onShowExample = vi.fn();
  renderOffer({ onShowExample });
  await waitFor(() => expect(screen.getByTestId("dose-offer").textContent).toContain("One more worked example"));
  expect(offer).toHaveBeenCalledWith(expect.objectContaining({ extractionId: "ext1", sectionId: "u1", visitId: "visit1",
    restoredSection: false }));
  await waitFor(() => expect(event).toHaveBeenCalledWith({ drawId: "d1", event: "delivered" }));
  fireEvent.click(screen.getByRole("button", { name: "why?" }));
  expect(screen.getByTestId("dose-offer-why").textContent).toBe("Offered at random, to learn how much of this helps you");
  fireEvent.click(screen.getByRole("button", { name: "yes" }));
  expect(event).toHaveBeenLastCalledWith({ drawId: "d1", event: "taken" });
  expect(onShowExample).toHaveBeenCalledWith("we2");
  expect(screen.queryByTestId("dose-offer")).toBeNull();
});

it("is dismissed with one key", async () => {
  offer.mockResolvedValue(EXTRA);
  event.mockResolvedValue({});
  renderOffer();
  await waitFor(() => screen.getByTestId("dose-offer"));
  fireEvent.keyDown(screen.getByTestId("dose-offer"), { key: "Escape" });
  expect(event).toHaveBeenLastCalledWith({ drawId: "d1", event: "dismissed" });
  expect(screen.queryByTestId("dose-offer")).toBeNull();
});

it("shows nothing when nothing is offered, and decides a section once", async () => {
  offer.mockResolvedValue({ version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null });
  const view = renderOffer();
  await waitFor(() => expect(offer).toHaveBeenCalledTimes(1));
  expect(screen.queryByTestId("dose-offer")).toBeNull();
  view.rerender(<DoseOffer extractionId="ext1" sectionId="u1" visitId={() => "visit1"} boundaryChecksAvailable
    cueDensityOff={false} skim={false} restoredSpanId={null} sections={SECTIONS as any} />);
  expect(offer).toHaveBeenCalledTimes(1);
  expect(event).not.toHaveBeenCalled();
});

it("tells the sidecar when the section is the restored passage's", async () => {
  offer.mockResolvedValue({ version: 1, eligible: false, reason: "restored_section", drawId: null, offer: null });
  renderOffer({ restoredSpanId: "s2" });
  await waitFor(() => expect(offer).toHaveBeenCalledWith(expect.objectContaining({ restoredSection: true })));
});
