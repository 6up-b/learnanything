import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useCloseWithFlush } from "./useCloseWithFlush";

type CloseEvent = { preventDefault: () => void };
type CloseHandler = (event: CloseEvent) => Promise<void>;

const windowApi = vi.hoisted(() => ({ onCloseRequested: vi.fn(), destroy: vi.fn() }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => windowApi }));
afterEach(cleanup);

/**
 * Mirrors `onCloseRequested` in @tauri-apps/api/window.js: after the handler settles,
 * the window is destroyed unless the handler called `preventDefault`.
 */
function emitCloseRequest(handler: CloseHandler): Promise<void> {
  let prevented = false;
  const event: CloseEvent = { preventDefault: () => { prevented = true; } };
  return handler(event).then(async () => {
    if (!prevented) await windowApi.destroy();
  });
}

it("disposes a registration that resolves after unmount and ignores its stale callback", async () => {
  let resolve!: (listener: () => void) => void;
  windowApi.onCloseRequested.mockReturnValue(new Promise<() => void>((done) => { resolve = done; }));
  const flush = vi.fn();
  const hook = renderHook(() => useCloseWithFlush(flush, vi.fn()));
  const handler: CloseHandler = windowApi.onCloseRequested.mock.calls[0][0];
  hook.unmount();
  const unlisten = vi.fn();
  await act(async () => resolve(unlisten));
  await handler({ preventDefault: vi.fn() });
  expect(unlisten).toHaveBeenCalledTimes(1);
  expect(flush).not.toHaveBeenCalled();
  expect(windowApi.destroy).not.toHaveBeenCalled();
});

it("keeps the window open through repeated close requests until the pending save lands", async () => {
  windowApi.onCloseRequested.mockResolvedValue(vi.fn());
  let finish!: () => void;
  const flush = vi.fn(() => new Promise<void>((done) => { finish = done; }));
  renderHook(() => useCloseWithFlush(flush, vi.fn()));
  const handler: CloseHandler = windowApi.onCloseRequested.mock.calls[0][0];

  const firstClose = emitCloseRequest(handler);
  await emitCloseRequest(handler);

  expect(flush).toHaveBeenCalledTimes(1);
  expect(windowApi.destroy).not.toHaveBeenCalled();
  await act(async () => { finish(); await firstClose; });
  expect(windowApi.destroy).toHaveBeenCalledTimes(1);
});
