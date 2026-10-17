// RW6a's "Last time here" card (spec §9.1; UX §4.8, W1, W12, S10): its
// sections and their sources, headings with no counts, nothing overdue, the
// well's markers only; collapse, "last time ▸" to reopen, dismiss; and the
// hook's rules -- the first scroll or "continue" collapses it, recap_shown is
// recorded once per visit, dismiss hides it until the next session, nothing
// takes focus.
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderRecapCardDto } from "../../api/dto";
import { RecapCard, shortDay } from "./RecapCard";
import { useReaderRecap } from "./useReaderRecap";

const api = vi.hoisted(() => ({ readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const MON = "2026-10-12T09:00:00Z";

function card(overrides: Partial<ReaderRecapCardDto> = {}): ReaderRecapCardDto {
  return {
    recapVersion: "rw6a-recap-v1",
    extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 },
    continueAt: { sectionId: "u54", label: "5.4 Mixtures" },
    stillOpen: [{ rootExchangeId: "r1", questionEventId: "q1", questionMd: "why is the density of a sum a convolution?", spanId: "s1", anchorSpanIds: ["s1"], openedAt: "2026-10-09T20:05:00Z" }],
    unfinished: [{ sessionId: "wb1", title: "Exercise 5.14: write the CDF", stepCount: 4, help: { bookCounted: true, hints: 0 }, helpLine: "help so far: the book", unfinished: false, spanIds: ["s9"], updatedAt: "2026-10-09T20:30:00Z" }],
    worthASecondLook: [{ kind: "still_unclear", rootExchangeId: "r2", spanId: "s2", questionMd: "why weighted by p?", observedAt: "2026-10-09T20:10:00Z", sourceEventIds: ["e1"] }],
    sinceLastTime: { demonstrated: [{ learningObjectId: "lo_cp", title: "conditional probability", demonstratedOn: MON, attemptId: "a1" }], checksRetired: [] },
    ...overrides,
  };
}

function handlers() {
  return {
    onExpand: vi.fn(), onContinue: vi.fn(), onDismiss: vi.fn(), onOpenInquiry: vi.fn(), onSetStatus: vi.fn(),
    onRevisit: vi.fn(), onResume: vi.fn(),
  };
}

beforeEach(() => { vi.resetAllMocks(); });
afterEach(cleanup);

it("shows each section from its source, in the learner's words, with no counts", () => {
  render(<RecapCard recap={card()} collapsed={false} now={new Date("2026-10-14T21:10:00Z")} {...handlers()} />);
  const region = screen.getByRole("region", { name: "Last time here" });
  for (const heading of ["Still open", "Unfinished", "Worth a second look", "Since last time"]) {
    const node = within(region).getByText(heading);
    expect(node.textContent).toBe(heading); // no "2 open questions"
  }
  expect(region.textContent).toContain("why is the density of a sum a convolution?");
  expect(region.textContent).toContain("Exercise 5.14: write the CDF · 4 steps · help so far: the book");
  expect(within(region).getByRole("button", { name: /Resume this problem/ })).toBeTruthy();
  expect(region.textContent).toContain("your question “why weighted by p?” — still unclear when you came back to it");
  expect(region.textContent).toContain(`● conditional probability — demonstrated on your own (${shortDay(MON, new Date("2026-10-14T21:10:00Z"))})`);
  expect(region.textContent).toContain("continue at 5.4 Mixtures");
  expect(region.textContent?.toLowerCase()).not.toMatch(/overdue|%|\bdue\b/);
});

it("leaves out a section with nothing in it", () => {
  render(<RecapCard recap={card({ unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] } })} collapsed={false} {...handlers()} />);
  expect(screen.queryByText("Unfinished")).toBeNull();
  expect(screen.queryByText("Worth a second look")).toBeNull();
  expect(screen.queryByText("Since last time")).toBeNull();
  expect(screen.getByText("Still open")).toBeTruthy();
});

it("each line acts through the chips the Reader already has", () => {
  const h = handlers();
  render(<RecapCard recap={card()} collapsed={false} {...h} />);
  const line = screen.getByText(/density of a sum/).closest("li") as HTMLElement;
  fireEvent.click(within(line).getByRole("button", { name: "open" }));
  expect(h.onOpenInquiry).toHaveBeenCalledWith("r1", "s1");
  fireEvent.click(within(line).getByRole("button", { name: "resolved" }));
  expect(h.onSetStatus).toHaveBeenCalledWith("r1", "resolved");
  fireEvent.click(within(line).getByRole("button", { name: "revisit once" }));
  expect(h.onRevisit).toHaveBeenCalledWith("r1");
  fireEvent.click(within(line).getByRole("button", { name: "keep open" }));
  expect(h.onSetStatus).toHaveBeenCalledTimes(1); // keep open writes nothing
  fireEvent.click(screen.getByRole("button", { name: /Resume this problem/ }));
  expect(h.onResume).toHaveBeenCalledWith("wb1");
  fireEvent.click(screen.getByRole("button", { name: "continue" }));
  expect(h.onContinue).toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "dismiss" }));
  expect(h.onDismiss).toHaveBeenCalled();
});

it("collapsed, it is one line that reopens it", () => {
  const h = handlers();
  render(<RecapCard recap={card()} collapsed {...h} />);
  expect(screen.queryByText("Still open")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: /last time ▸/ }));
  expect(h.onExpand).toHaveBeenCalled();
});

// -- the hook --------------------------------------------------------------------------------

function hookProps(overrides: Record<string, unknown> = {}) {
  return {
    enabled: true, wrapUpEnabled: false, extractionId: "ext1", visitId: () => "v_now", readingMoved: false,
    activityKey: "0", onError: vi.fn(), ...overrides,
  };
}

it("loads the card, records recap_shown once per visit and takes no focus", async () => {
  api.readerRecap.mockResolvedValue({ version: 1, recap: card(), dismissed: false });
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "recap_shown" });
  const before = document.activeElement;
  const { result, rerender } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps() });
  await waitFor(() => expect(result.current.recap).not.toBeNull());
  expect(api.readerRecap).toHaveBeenCalledWith({ extractionId: "ext1", visitId: "v_now" });
  act(() => result.current.noteShown());
  act(() => result.current.noteShown());
  rerender(hookProps({ activityKey: "1" }));
  expect(api.readerRecapEvent).toHaveBeenCalledTimes(1);
  expect(api.readerRecapEvent).toHaveBeenCalledWith({ extractionId: "ext1", visitId: "v_now", event: "recap_shown" });
  expect(document.activeElement).toBe(before);
});

it("the first scroll or continue collapses it, and last time reopens it", async () => {
  api.readerRecap.mockResolvedValue({ version: 1, recap: card(), dismissed: false });
  const { result, rerender } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps() });
  await waitFor(() => expect(result.current.recap).not.toBeNull());
  expect(result.current.collapsed).toBe(false);
  rerender(hookProps({ readingMoved: true }));
  expect(result.current.collapsed).toBe(true);
  act(() => result.current.expand());
  expect(result.current.collapsed).toBe(false);
  // Only the first scroll: reading on does not fold it again.
  rerender(hookProps({ readingMoved: false }));
  rerender(hookProps({ readingMoved: true }));
  expect(result.current.collapsed).toBe(false);
  act(() => result.current.continueReading());
  expect(result.current.collapsed).toBe(true);
});

it("dismiss records it and hides the card and its link for this source", async () => {
  api.readerRecap.mockResolvedValue({ version: 1, recap: card(), dismissed: false });
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "recap_dismissed" });
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps() });
  await waitFor(() => expect(result.current.recap).not.toBeNull());
  await act(async () => { await result.current.dismiss(); });
  expect(api.readerRecapEvent).toHaveBeenCalledWith({ extractionId: "ext1", visitId: "v_now", event: "recap_dismissed" });
  expect(result.current.recap).toBeNull();
});

it("switched off it asks the sidecar nothing", async () => {
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps({ enabled: false }) });
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(result.current.recap).toBeNull();
  expect(api.readerRecap).not.toHaveBeenCalled();
  expect(api.readerWrapUp).not.toHaveBeenCalled();
});
