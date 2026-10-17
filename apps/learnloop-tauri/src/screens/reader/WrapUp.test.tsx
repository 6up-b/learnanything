// RW6a's Wrap up (spec §9.1, D34; UX §4.8, S11): the three lists with one
// action per line (the chips' own RPCs; keep open writes nothing), one key
// closes it; the rail's offer only after activity, `w` opens it; and after
// leaving a source, the one dim self-dismissing line where the learner lands
// (Today or the library), never in the Reader being closed, never blocking.
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderWrapUpActionDto, ReaderWrapUpDto } from "../../api/dto";
import { setAlgoConfig } from "../../app/algoConfig";
import { wrapUpOfferArmed } from "../../app/wrapUpOffer";
import { WrapUpOffer } from "./WrapUpOffer";
import { WrapUpPanel } from "./WrapUpPanel";
import { useReaderRecap } from "./useReaderRecap";

const api = vi.hoisted(() => ({
  readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn(), readerWrapUpOffer: vi.fn(),
  readerSetInquiryStatus: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));

function wrapUp(overrides: Partial<ReaderWrapUpDto> = {}): ReaderWrapUpDto {
  const status = (action: ReaderWrapUpActionDto["action"], resolution: string, trigger: string): ReaderWrapUpActionDto => ({
    action, rpc: "reader.set_inquiry_status",
    params: { extractionId: "ext1", exchangeId: action === "undo" ? "r1" : "r2", resolution, trigger },
  });
  return {
    version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-14T21:10:00Z", endedAt: "2026-10-14T21:50:00Z", minutes: 40 },
    resolved: [{ rootExchangeId: "r1", questionMd: "why weighted by p?", actions: [status("undo", "open", "undo")] }],
    stillOpen: [{ rootExchangeId: "r2", questionMd: "density of a sum?", spanIds: ["s2"], actions: [
      status("resolve", "resolved", "chip"),
      { action: "revisit_once", rpc: "reader.invoke_preset", params: { preset: "test_me_later", spanIds: ["s2"] }, where: "reader" },
      { action: "keep_open" },
    ] }],
    worthReinforcing: [{ kind: "with_help", marker: "◌", sessionId: "wb1", title: "Exercise 5.14", status: "submitted", helpLine: "help so far: the book" }],
    ...overrides,
  };
}

beforeEach(() => { vi.resetAllMocks(); setAlgoConfig(undefined); });
afterEach(() => { cleanup(); setAlgoConfig(undefined); });

it("shows resolved, still open and worth reinforcing, each line with one action", () => {
  const onAction = vi.fn().mockResolvedValue(undefined);
  render(<WrapUpPanel wrapUp={wrapUp()} where="reader" onAction={onAction} onClose={vi.fn()} />);
  const panel = screen.getByRole("region", { name: "Wrap up" });
  for (const heading of ["Resolved", "Still open", "Worth reinforcing"]) expect(within(panel).getByText(heading).textContent).toBe(heading);
  expect(panel.textContent).toContain("why weighted by p?");
  expect(panel.textContent).toContain("◌ Exercise 5.14 · with help · help so far: the book");
  fireEvent.click(within(panel).getByRole("button", { name: "undo" }));
  expect(onAction).toHaveBeenCalledWith(expect.objectContaining({ rootExchangeId: "r1" }), expect.objectContaining({ action: "undo" }));
  expect(within(panel).getByRole("button", { name: "revisit once" })).toBeTruthy();
  fireEvent.click(within(panel).getByRole("button", { name: "keep open" }));
  expect(onAction).toHaveBeenCalledTimes(1); // keep open writes nothing
  expect(panel.textContent).toContain("kept open");
  expect(panel.textContent?.toLowerCase()).not.toMatch(/overdue|\d+ open/);
});

it("at the destination it offers only what works there, and one key closes it", () => {
  const onClose = vi.fn();
  render(<WrapUpPanel wrapUp={wrapUp()} where="destination" onAction={vi.fn()} onClose={onClose} />);
  expect(screen.queryByRole("button", { name: "revisit once" })).toBeNull();
  expect(screen.getByRole("button", { name: "resolve" })).toBeTruthy();
  fireEvent.keyDown(window, { key: "Escape" });
  expect(onClose).toHaveBeenCalled();
});

// -- the rail's offer and `w` -----------------------------------------------------------------

function hookProps(overrides: Record<string, unknown> = {}) {
  return { enabled: false, wrapUpEnabled: true, extractionId: "ext1", visitId: () => "v1", readingMoved: false,
           activityKey: "0", onError: vi.fn(), ...overrides };
}

it("the rail offers Wrap up only after activity, and w opens it", async () => {
  api.readerWrapUp.mockResolvedValueOnce(wrapUp({ available: false, resolved: [], stillOpen: [], worthReinforcing: [] }));
  const { result, rerender } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps() });
  await waitFor(() => expect(api.readerWrapUp).toHaveBeenCalledTimes(1));
  expect(result.current.wrapUpAvailable).toBe(false);
  api.readerWrapUp.mockResolvedValue(wrapUp());
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "wrap_up_opened" });
  rerender(hookProps({ activityKey: "1" })); // an Ask landed
  await waitFor(() => expect(result.current.wrapUpAvailable).toBe(true));
  await act(async () => { fireEvent.keyDown(window, { key: "w" }); });
  await waitFor(() => expect(result.current.wrapUpOpen).not.toBeNull());
  expect(api.readerRecapEvent).toHaveBeenCalledWith({ extractionId: "ext1", visitId: "v1", event: "wrap_up_opened" });
  act(() => result.current.closeWrapUp());
  expect(result.current.wrapUpOpen).toBeNull();
});

it("w in a text field types a w", async () => {
  api.readerWrapUp.mockResolvedValue(wrapUp());
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps() });
  await waitFor(() => expect(result.current.wrapUpAvailable).toBe(true));
  const input = document.createElement("textarea");
  document.body.appendChild(input);
  fireEvent.keyDown(input, { key: "w" });
  expect(result.current.wrapUpOpen).toBeNull();
  expect(api.readerRecapEvent).not.toHaveBeenCalled();
  input.remove();
});

// -- the destination line ---------------------------------------------------------------------

it("arms the line only when the learner lands on Today or the library from the Reader", () => {
  expect(wrapUpOfferArmed("reader", "today")).toBe(true);
  expect(wrapUpOfferArmed("reader", "library")).toBe(true);
  expect(wrapUpOfferArmed("reader", "reader")).toBe(false);
  expect(wrapUpOfferArmed("today", "library")).toBe(false);
  expect(wrapUpOfferArmed("reader", "graph")).toBe(false);
});

it("where the learner lands: one dim line, opened in place, writing only wrap_up_opened", async () => {
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  api.readerWrapUpOffer.mockResolvedValue({ version: 1, offer: { extractionId: "ext1", sourceId: "src1", session: wrapUp().session } });
  api.readerWrapUp.mockResolvedValue(wrapUp());
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "wrap_up_opened" });
  api.readerSetInquiryStatus.mockResolvedValue({ rootExchangeId: "r2", resolution: "resolved" });
  const before = document.activeElement;
  render(<WrapUpOffer armed onError={vi.fn()} />);
  const line = await screen.findByRole("button", { name: /Reading wrap-up ready — under a minute/ });
  expect(document.activeElement).toBe(before); // never takes focus
  expect(screen.queryByRole("dialog")).toBeNull();
  fireEvent.click(line);
  await screen.findByRole("region", { name: "Wrap up" });
  expect(api.readerRecapEvent).toHaveBeenCalledWith({ extractionId: "ext1", event: "wrap_up_opened" });
  expect(api.readerWrapUp).toHaveBeenCalledWith({ extractionId: "ext1" });
  fireEvent.click(screen.getByRole("button", { name: "resolve" }));
  await waitFor(() => expect(api.readerSetInquiryStatus).toHaveBeenCalledWith({ extractionId: "ext1", exchangeId: "r2", resolution: "resolved", trigger: "chip" }));
  fireEvent.keyDown(window, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("region", { name: "Wrap up" })).toBeNull());
});

it("no line when nothing is offered, when not armed, or switched off", async () => {
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  api.readerWrapUpOffer.mockResolvedValue({ version: 1, offer: null });
  const { container, unmount } = render(<WrapUpOffer armed onError={vi.fn()} />);
  await waitFor(() => expect(api.readerWrapUpOffer).toHaveBeenCalled());
  expect(container.innerHTML).toBe("");
  unmount();
  api.readerWrapUpOffer.mockClear();
  const notArmed = render(<WrapUpOffer armed={false} onError={vi.fn()} />);
  expect(notArmed.container.innerHTML).toBe("");
  notArmed.unmount();
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: false } });
  const off = render(<WrapUpOffer armed onError={vi.fn()} />);
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(off.container.innerHTML).toBe("");
  expect(api.readerWrapUpOffer).not.toHaveBeenCalled();
});

it("w waits while the workbench hides the rail", async () => {
  api.readerWrapUp.mockResolvedValue(wrapUp());
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps({ suspended: true }) });
  await waitFor(() => expect(result.current.wrapUpAvailable).toBe(true));
  fireEvent.keyDown(window, { key: "w" });
  expect(result.current.wrapUpOpen).toBeNull();
  expect(api.readerRecapEvent).not.toHaveBeenCalled();
});
