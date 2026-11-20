// "Waiting you can see" (docs/reviews/ux-waiting.md, the owner's case 3): a hint
// being written for the learner's work says so through the shared waiting line,
// with what is normal for a long wait, and the item's own hint stays offered
// from the first moment.
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { WAIT_LATER_MS } from "../../components/Waiting";
import { HintPanel } from "./HintPanel";
import type { AdaptiveHints } from "./useAdaptiveHints";

vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

function hints(overrides: Partial<AdaptiveHints> = {}): AdaptiveHints {
  return {
    entries: [], pending: true, notice: null, offer: null, offerBusy: false, picks: [],
    takeAuthoredInstead: vi.fn(), saveHelpStyle: vi.fn(), takeWorked: vi.fn(),
    ...overrides,
  } as unknown as AdaptiveHints;
}

beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => { cleanup(); vi.useRealTimers(); });

it("nothing before the delay, then the writing line, the second line after a few seconds, gone when the hint lands", () => {
  const { rerender } = render(<HintPanel hints={hints()} answer="" helpStyle="balanced" />);
  act(() => { vi.advanceTimersByTime(300); });
  expect(screen.queryByText("Writing a hint for your work…")).toBeNull();
  act(() => { vi.advanceTimersByTime(100); });
  const line = screen.getByTestId("hint-writing");
  expect(line.getAttribute("role")).toBe("status");
  expect(line.textContent).toBe("◐ Writing a hint for your work…");
  act(() => { vi.advanceTimersByTime(WAIT_LATER_MS); });
  expect(screen.getByTestId("hint-writing-later").textContent).toBe("This can take up to half a minute.");
  rerender(<HintPanel hints={hints({ pending: false, notice: { message: "A hint landed." } as AdaptiveHints["notice"] })} answer="" helpStyle="balanced" />);
  expect(screen.queryByTestId("hint-writing")).toBeNull();
});

it("the item's own hint is offered from the first moment of the wait", () => {
  render(<HintPanel hints={hints({ offer: {} as AdaptiveHints["offer"] })} answer="" helpStyle="balanced" />);
  expect(screen.getByRole("button", { name: "use the item's hint instead" })).toBeTruthy();
  expect(screen.queryByText("Writing a hint for your work…")).toBeNull();
});
