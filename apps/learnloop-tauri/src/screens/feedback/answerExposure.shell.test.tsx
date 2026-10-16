// UX Phase 4 round 6 G (docs/reviews/ux-phase4-feedback-codex-review.md §12):
// the shell hold belongs to the window, not to one answer. A new answer key
// while the hold is pending is asked about again, never stranded.
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useAnswerExposure } from "./answerExposure";

const { shell } = vi.hoisted(() => ({ shell: { window: null as unknown } }));
vi.mock("@tauri-apps/api/window", () => ({
  getCurrentWindow: () => {
    if (!shell.window) throw new Error("not in the shell");
    return shell.window;
  }
}));

const SECOND = 1000;

function fakeShellWindow() {
  const handlers: Record<string, (event: { payload: unknown }) => void> = {};
  const queries: { minimized: ((value: boolean) => void)[]; visible: ((value: boolean) => void)[] } = { minimized: [], visible: [] };
  const listen = (name: string) => (handler: (event: { payload: unknown }) => void) => {
    handlers[name] = handler;
    return Promise.resolve(() => undefined);
  };
  return {
    handlers,
    queries,
    window: {
      onResized: listen("resized"),
      onScaleChanged: listen("scale"),
      onFocusChanged: listen("focus"),
      isMinimized: () => new Promise<boolean>((resolve) => queries.minimized.push(resolve)),
      isVisible: () => new Promise<boolean>((resolve) => queries.visible.push(resolve))
    }
  };
}

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

async function advance(ms: number) {
  await act(async () => {
    vi.advanceTimersByTime(ms);
  });
  await flush();
}

afterEach(() => {
  cleanup();
  shell.window = null;
  vi.useRealTimers();
});

it.each([
  ["before the settle ends", 100],
  ["while the query is in flight", 400]
])("G (round 6): a new answer key during a shell hold (%s) is asked about again, not stranded", async (_name, wait) => {
  vi.useFakeTimers();
  const fake = fakeShellWindow();
  shell.window = fake.window;
  const writes: string[] = [];
  const record = (displayId: string) => {
    writes.push(displayId);
    return Promise.resolve({ recorded: true, recordedAt: new Date(Date.now()).toISOString() });
  };
  const { result, rerender } = renderHook(({ key }) => useAnswerExposure(key, true, record), {
    initialProps: { key: "answer-1" }
  });
  await flush();
  expect(result.current.shown).toBe(true);
  // Resize: held; the key changes before the hold is answered.
  await act(async () => {
    fake.handlers.resized?.({ payload: {} });
  });
  expect(result.current.shown).toBe(false);
  await advance(wait);
  rerender({ key: "answer-2" });
  await flush();
  expect(result.current.shown).toBe(false);
  // The new answer's gate asks the shell again; visible and unminimized
  // releases it (after a fresh row of its own).
  await advance(SECOND);
  const asked = fake.queries.visible.length;
  expect(asked).toBeGreaterThan(0);
  await act(async () => {
    fake.queries.minimized[asked - 1]?.(false);
    fake.queries.visible[asked - 1]?.(true);
  });
  await flush();
  await advance(SECOND);
  expect(result.current.shown).toBe(true);
  expect(writes.length).toBeGreaterThanOrEqual(2);
});
