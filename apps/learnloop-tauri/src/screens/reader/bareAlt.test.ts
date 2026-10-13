// K7 (docs/specs/ux_learnloop_v1.md §12.2): a bare Alt press clears the
// capture, but an Alt *chord* (Alt+←, Alt+drag, Alt+Tab) must never lose it.
import { cleanup, renderHook } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useBareAltClear } from "./bareAlt";

afterEach(cleanup);

function key(type: "keydown" | "keyup", key: string, init: KeyboardEventInit = {}, target: EventTarget = window) {
  target.dispatchEvent(new KeyboardEvent(type, { key, bubbles: true, ...init }));
}

it("a bare Alt press and release clears once, on release", () => {
  const onClear = vi.fn();
  renderHook(() => useBareAltClear(onClear));
  key("keydown", "Alt", { altKey: true });
  expect(onClear).not.toHaveBeenCalled();
  key("keyup", "Alt");
  expect(onClear).toHaveBeenCalledTimes(1);
});

it("an Alt chord with a key never clears", () => {
  const onClear = vi.fn();
  renderHook(() => useBareAltClear(onClear));
  key("keydown", "Alt", { altKey: true });
  key("keydown", "ArrowLeft", { altKey: true });
  key("keyup", "ArrowLeft", { altKey: true });
  key("keyup", "Alt");
  expect(onClear).not.toHaveBeenCalled();
});

it("Alt held through a pointer press (Alt+drag sweep) never clears", () => {
  const onClear = vi.fn();
  renderHook(() => useBareAltClear(onClear));
  key("keydown", "Alt", { altKey: true });
  window.dispatchEvent(new MouseEvent("mousedown", { altKey: true, bubbles: true }));
  key("keyup", "Alt");
  expect(onClear).not.toHaveBeenCalled();
});

it("Alt+Tab away (window blur) never clears", () => {
  const onClear = vi.fn();
  renderHook(() => useBareAltClear(onClear));
  key("keydown", "Alt", { altKey: true });
  window.dispatchEvent(new Event("blur"));
  key("keyup", "Alt");
  expect(onClear).not.toHaveBeenCalled();
});

it("Alt pressed while typing in a field never clears", () => {
  const onClear = vi.fn();
  renderHook(() => useBareAltClear(onClear));
  const box = document.createElement("textarea");
  document.body.appendChild(box);
  key("keydown", "Alt", { altKey: true }, box);
  key("keyup", "Alt", {}, box);
  expect(onClear).not.toHaveBeenCalled();
  box.remove();
});

it("a held Alt's auto-repeat does not count as a chord", () => {
  const onClear = vi.fn();
  renderHook(() => useBareAltClear(onClear));
  key("keydown", "Alt", { altKey: true });
  key("keydown", "Alt", { altKey: true, repeat: true });
  key("keyup", "Alt");
  expect(onClear).toHaveBeenCalledTimes(1);
});
