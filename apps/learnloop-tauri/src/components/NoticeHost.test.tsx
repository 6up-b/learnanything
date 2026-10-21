// UX Phase 2 (docs/specs/ux_learnloop_v1.md §7.9, §10 2.3): errors red with
// Try again when retryable, details holding the code; notices neutral, small,
// at the bottom edge and gone after a few seconds; nothing but errors while
// the Reader has a book open, the rest delivered at the next destination.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NOTICE_TTL_MS, addNotice, type ShellNotice } from "../app/notices";
import { NoticeHost } from "./NoticeHost";

beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function Harness({ initial, holding }: { initial: ShellNotice[]; holding: boolean }) {
  const [notices, setNotices] = useState(initial);
  return <NoticeHost notices={notices} holding={holding} onChange={setNotices} />;
}

describe("NoticeHost", () => {
  it("draws an error red, with Try again when it can be retried, and the code under details", () => {
    const retry = vi.fn();
    const initial = addNotice([], { kind: "error", text: "Couldn't open the reader.", code: "sidecar_timeout", retry });
    render(<Harness initial={initial} holding={false} />);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("shell-notice-error");
    expect(alert.textContent).toContain("Couldn't open the reader.");
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(alert.textContent).toContain("sidecar_timeout");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledTimes(1);
    // Trying again clears the error; a new failure would add a new one.
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("offers no Try again without a retry, and an error stays until dismissed", () => {
    const initial = addNotice([], { kind: "error", text: "Vault refresh failed: locked" });
    render(<Harness initial={initial} holding={false} />);
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    act(() => {
      vi.advanceTimersByTime(10 * NOTICE_TTL_MS);
    });
    expect(screen.getByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("draws a notice neutral and lets it go after a few seconds", () => {
    const initial = addNotice([], { kind: "notice", text: "grading → codex" });
    render(<Harness initial={initial} holding={false} />);
    const status = screen.getByRole("status");
    expect(status.className).toContain("shell-notice-notice");
    expect(status.className).not.toContain("error");
    act(() => {
      vi.advanceTimersByTime(NOTICE_TTL_MS + 50);
    });
    expect(screen.queryByText("grading → codex")).toBeNull();
  });

  it("holds a notice while reading and delivers it, in full, at the destination", () => {
    const initial = addNotice(addNotice([], { kind: "notice", text: "Already in your library — opened where you left off." }), {
      kind: "error",
      text: "Couldn't load this."
    });
    const { rerender } = render(<Harness initial={initial} holding />);
    expect(screen.queryByText(/Already in your library/)).toBeNull();
    expect(screen.getByText("Couldn't load this.")).toBeTruthy();
    // Long after the notice was raised, still in the Reader: still held, not lost.
    act(() => {
      vi.advanceTimersByTime(5 * NOTICE_TTL_MS);
    });
    rerender(<Harness initial={initial} holding={false} />);
    expect(screen.getByText(/Already in your library/)).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(NOTICE_TTL_MS - 100);
    });
    expect(screen.getByText(/Already in your library/)).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.queryByText(/Already in your library/)).toBeNull();
  });

  // Codex review F7: shown briefly, then a minute in the Reader, then out:
  // the notice must not expire the moment it is back.
  it("gives a notice its full time again after it was shown and then held", () => {
    const initial = addNotice([], { kind: "notice", text: "grading → codex" });
    function Live() {
      const [notices, setNotices] = useState(initial);
      const [holding, setHolding] = useState(false);
      return (
        <>
          <button type="button" onClick={() => setHolding((value) => !value)}>
            toggle
          </button>
          <NoticeHost notices={notices} holding={holding} onChange={setNotices} />
        </>
      );
    }
    render(<Live />);
    expect(screen.getByText("grading → codex")).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    fireEvent.click(screen.getByRole("button", { name: "toggle" }));
    expect(screen.queryByText("grading → codex")).toBeNull();
    act(() => {
      vi.advanceTimersByTime(60_000);
    });
    fireEvent.click(screen.getByRole("button", { name: "toggle" }));
    expect(screen.getByText("grading → codex")).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(NOTICE_TTL_MS - 200);
    });
    expect(screen.getByText("grading → codex")).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(screen.queryByText("grading → codex")).toBeNull();
  });

  // Codex review F2: an error with Try again stays, and its retry still
  // works, after more notices than fit on screen.
  it("keeps the error's Try again through a burst of notices", () => {
    const retry = vi.fn();
    let initial = addNotice([], { kind: "error", text: "Couldn't open the reader.", code: "sidecar_timeout", retry });
    for (const text of ["one", "two", "three"]) initial = addNotice(initial, { kind: "notice", text });
    render(<Harness initial={initial} holding={false} />);
    expect(screen.getByText("Couldn't open the reader.")).toBeTruthy();
    expect(screen.queryByText("three")).toBeNull();
    act(() => {
      vi.advanceTimersByTime(NOTICE_TTL_MS + 50);
    });
    // The first two have gone; the third has its turn; the error stays.
    expect(screen.getByText("three")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });
});
