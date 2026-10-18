// Adaptive difficulty AD1 (spec §12, D5): the optional "Felt" tap. Never
// preselected, a second tap takes it back, locked once Submit is pressed,
// hidden for the session with one tap (browser storage, per viewer), and it
// still shows when storage is unavailable.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { DifficultyRatingTap } from "./DifficultyRatingTap";
import { useFirstHintProgress } from "./useFirstHintProgress";
import { renderHook, act } from "@testing-library/react";

function stubStorage(): Map<string, string> {
  const stored = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => stored.get(key) ?? null,
    setItem: (key: string, value: string) => void stored.set(key, value),
    removeItem: (key: string) => void stored.delete(key),
    clear: () => stored.clear()
  });
  return stored;
}

beforeEach(() => {
  stubStorage();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("is never preselected and reports a tap, then its retraction", () => {
  const onChange = vi.fn();
  const { rerender } = render(<DifficultyRatingTap sessionId="s1" value={null} onChange={onChange} locked={false} />);
  expect(screen.queryAllByRole("button", { pressed: true })).toHaveLength(0);
  fireEvent.click(screen.getByRole("button", { name: "about right" }));
  expect(onChange).toHaveBeenLastCalledWith("about_right");
  rerender(<DifficultyRatingTap sessionId="s1" value="about_right" onChange={onChange} locked={false} />);
  fireEvent.click(screen.getByRole("button", { name: "about right" }));
  expect(onChange).toHaveBeenLastCalledWith(null);
});

it("is locked once Submit is pressed", () => {
  const onChange = vi.fn();
  render(<DifficultyRatingTap sessionId="s1" value="hard" onChange={onChange} locked />);
  const hard = screen.getByRole("button", { name: "hard" }) as HTMLButtonElement;
  expect(hard.disabled).toBe(true);
  expect(screen.queryByRole("button", { name: "hide this for the session" })).toBeNull();
});

it("hides for the session only, and shows when storage throws", () => {
  const onChange = vi.fn();
  render(<DifficultyRatingTap sessionId="s1" value={null} onChange={onChange} locked={false} />);
  fireEvent.click(screen.getByRole("button", { name: "hide this for the session" }));
  expect(screen.queryByRole("group")).toBeNull();
  cleanup();
  render(<DifficultyRatingTap sessionId="s2" value={null} onChange={onChange} locked={false} />);
  expect(screen.getByRole("group")).toBeTruthy();
  cleanup();
  vi.stubGlobal("localStorage", { getItem: () => { throw new Error("blocked"); }, setItem: () => undefined });
  render(<DifficultyRatingTap sessionId="s1" value={null} onChange={onChange} locked={false} />);
  expect(screen.getByRole("group")).toBeTruthy();
});

it("the marker keeps the first reveal's progress, and nothing while off", () => {
  const on = renderHook(() => useFirstHintProgress({ enabled: true }));
  act(() => on.result.current.mark("draft_started"));
  act(() => on.result.current.mark("no_draft"));
  expect(on.result.current.value).toBe("draft_started");
  const restored = renderHook(() => useFirstHintProgress({ enabled: true, restored: "no_draft" }));
  act(() => restored.result.current.mark("draft_started"));
  expect(restored.result.current.value).toBe("no_draft");
  const off = renderHook(() => useFirstHintProgress({ enabled: false, restored: "no_draft" }));
  act(() => off.result.current.mark("draft_started"));
  expect(off.result.current.value).toBeNull();
});
