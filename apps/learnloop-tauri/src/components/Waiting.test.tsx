// The shared waiting indicator's rules (docs/reviews/ux-waiting.md): nothing
// before the delay, the mark and the line after it, the second line only for a
// long wait, a polite status region, a hidden mark, and a still mark under
// reduced motion or in the Reader posture.
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { WAIT_DELAY_MS, WAIT_LATER_MS, Waiting } from "./Waiting";

const original = window.matchMedia;

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  window.matchMedia = original;
});

function reduceMotion(on: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: on && query.includes("reduce"), media: query, onchange: null,
    addListener: () => undefined, removeListener: () => undefined,
    addEventListener: () => undefined, removeEventListener: () => undefined, dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

it("says nothing before the delay, then the mark and the line in a polite status region", () => {
  render(<Waiting line="Checking your answer…" />);
  const region = screen.getByRole("status");
  expect(region.getAttribute("aria-live")).toBe("polite");
  expect(region.textContent).toBe("");
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS - 1); });
  expect(screen.queryByText(/Checking your answer…/)).toBeNull();
  act(() => { vi.advanceTimersByTime(1); });
  expect(screen.getByRole("status").textContent).toBe("◐ Checking your answer…");
  const mark = screen.getByText("◐");
  expect(mark.getAttribute("aria-hidden")).toBe("true");
  expect(mark.getAttribute("data-motion")).toBe("moving");
});

it("adds the quieter second line only once a long wait passes a few seconds", () => {
  render(<Waiting line="Writing a reply…" later="This can take a minute." />);
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS); });
  expect(screen.getByText(/Writing a reply…/)).toBeTruthy();
  expect(screen.queryByText("This can take a minute.")).toBeNull();
  act(() => { vi.advanceTimersByTime(WAIT_LATER_MS - WAIT_DELAY_MS); });
  expect(screen.getByText("This can take a minute.")).toBeTruthy();
});

it("a wait without a second line never grows one", () => {
  render(<Waiting line="Choosing what's next…" />);
  act(() => { vi.advanceTimersByTime(WAIT_LATER_MS * 4); });
  expect(screen.getByRole("status").textContent).toBe("◐ Choosing what's next…");
});

it("is gone the moment it unmounts, and its timers with it", () => {
  const { rerender } = render(<div><Waiting line="Choosing what's next…" /></div>);
  rerender(<div />);
  expect(vi.getTimerCount()).toBe(0);
  expect(screen.queryByRole("status")).toBeNull();
});

it("under reduced motion the mark is still, and the words are unchanged", () => {
  reduceMotion(true);
  render(<Waiting line="Checking your answer…" />);
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS); });
  expect(screen.getByText("◐").getAttribute("data-motion")).toBe("still");
  expect(screen.getByText(/Checking your answer…/)).toBeTruthy();
});

it("in the Reader posture the mark is still whatever the preference", () => {
  reduceMotion(false);
  render(<Waiting line="Writing a reply…" still />);
  act(() => { vi.advanceTimersByTime(WAIT_DELAY_MS); });
  expect(screen.getByText("◐").getAttribute("data-motion")).toBe("still");
});
