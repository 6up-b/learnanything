// The phone's waiting indicator (docs/reviews/ux-waiting.md): nothing before
// the delay, the mark and the line after it, the second line only for a long
// wait, a polite status region, a hidden mark, and a still mark under reduced motion.
import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { WAIT_DELAY_MS, WAIT_LATER_MS, Waiting } from "./Waiting";

const original = window.matchMedia;
beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => { vi.useRealTimers(); window.matchMedia = original; });

it("says nothing before the delay, then the mark and the line in a polite status region", () => {
  render(<Waiting line="Checking your answer…" />);
  const region = screen.getByRole("status");
  expect(region.getAttribute("aria-live")).toBe("polite");
  expect(region.textContent).toBe("");
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS - 1); });
  expect(screen.queryByText(/Checking your answer…/)).toBeNull();
  act(() => { vi.advanceTimersByTime(1); });
  expect(region.textContent).toBe("◐ Checking your answer…");
  expect(screen.getByText("◐").getAttribute("aria-hidden")).toBe("true");
  expect(screen.getByText("◐").getAttribute("data-motion")).toBe("moving");
});

it("adds the second line only once a long wait passes a few seconds", () => {
  render(<Waiting line="Writing a reply…" later="This can take a minute." />);
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS); });
  expect(screen.queryByText("This can take a minute.")).toBeNull();
  act(() => { vi.advanceTimersByTime(WAIT_LATER_MS - WAIT_DELAY_MS); });
  expect(screen.getByText("This can take a minute.")).toBeTruthy();
});

it("under reduced motion the mark is still and the words are unchanged", () => {
  window.matchMedia = ((query: string) => ({
    matches: query.includes("reduce"), media: query, onchange: null, addListener: () => undefined, removeListener: () => undefined,
    addEventListener: () => undefined, removeEventListener: () => undefined, dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
  render(<Waiting line="Checking your answer…" />);
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS); });
  expect(screen.getByText("◐").getAttribute("data-motion")).toBe("still");
  expect(screen.getByText(/Checking your answer…/)).toBeTruthy();
});

it("leaves no timer behind when it unmounts", () => {
  const { unmount } = render(<Waiting line="Choosing what's next…" later="x" />);
  unmount();
  expect(vi.getTimerCount()).toBe(0);
});
