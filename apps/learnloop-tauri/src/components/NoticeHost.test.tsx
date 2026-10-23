// UX Phase 2 (docs/specs/ux_learnloop_v1.md §7.9, §10 2.3): errors red with
// Try again when retryable, details holding the code; notices neutral, small,
// at the bottom edge and gone after a few seconds; nothing but errors while
// the Reader has a book open, the rest delivered at the next destination.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NOTICE_TTL_MS, addNotice, type ShellNotice } from "../app/notices";
import { NoticeHost } from "./NoticeHost";
import { RETRY_RAN, type RetryRan } from "../errors";

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
  it("draws an error red, with Try again when it can be retried, and the code under details", async () => {
    let settle: () => void = () => undefined;
    const retry = vi.fn(() => new Promise<RetryRan>((resolve) => (settle = () => resolve(RETRY_RAN))));
    const initial = addNotice([], { kind: "error", text: "Couldn't open the reader.", code: "sidecar_timeout", retry, source: "q:reader" });
    render(<Harness initial={initial} holding={false} />);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("shell-notice-error");
    expect(alert.textContent).toContain("Couldn't open the reader.");
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(alert.textContent).toContain("sidecar_timeout");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledTimes(1);
    // Fix round 2: the error stays while the retry runs (no second click) …
    const trying = screen.getByRole("button", { name: "Trying again…" }) as HTMLButtonElement;
    expect(trying.disabled).toBe(true);
    // … and goes once it has succeeded.
    await act(async () => {
      settle();
      await Promise.resolve();
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  // Fix round 2: the shell owns the retry, so its failure is shown whoever
  // raised the error, with the new failure's code and a new Try again.
  it("shows a retry's failure itself, under the same source, with a new Try again", async () => {
    const retry = vi.fn(async () => {
      throw { code: "sidecar_busy", message: "Still busy.", retryable: true };
    });
    const initial = addNotice([], { kind: "error", text: "Couldn't load this.", code: "sidecar_timeout", retry, source: "q:map" });
    render(<Harness initial={initial} holding={false} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      await Promise.resolve();
    });
    const alerts = screen.getAllByRole("alert");
    expect(alerts).toHaveLength(1);
    expect(alerts[0].textContent).toContain("Still busy.");
    fireEvent.click(screen.getByRole("button", { name: "details ▸" }));
    expect(screen.getByRole("alert").textContent).toContain("sidecar_busy");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      await Promise.resolve();
    });
    expect(retry).toHaveBeenCalledTimes(2);
  });

  // Fix round 3: a retry that did not run a request (resolved with anything
  // but RETRY_RAN) keeps the error and its Try again.
  it("keeps the error when the retry resolves without having run a request", async () => {
    const retry = vi.fn(async () => undefined as never);
    const initial = addNotice([], { kind: "error", text: "Couldn't load this.", code: "sidecar_timeout", retry, source: "q:history" });
    render(<Harness initial={initial} holding={false} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      await Promise.resolve();
    });
    expect(retry).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert").textContent).toContain("Couldn't load this.");
    expect((screen.getByRole("button", { name: "Try again" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("offers no new Try again when the retry's failure is not retryable", async () => {
    const retry = vi.fn(async () => {
      throw { code: "invalid_input", message: "That map is gone.", retryable: false };
    });
    const initial = addNotice([], { kind: "error", text: "Couldn't load this.", code: "sidecar_timeout", retry, source: "q:map" });
    render(<Harness initial={initial} holding={false} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      await Promise.resolve();
    });
    expect(screen.getByRole("alert").textContent).toContain("That map is gone.");
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
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
    const retry = vi.fn(async () => RETRY_RAN);
    let initial = addNotice([], { kind: "error", text: "Couldn't open the reader.", code: "sidecar_timeout", retry, source: "q:reader" });
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
