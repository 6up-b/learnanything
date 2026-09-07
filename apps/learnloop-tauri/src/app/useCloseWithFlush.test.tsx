import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useCloseWithFlush } from "./useCloseWithFlush";

const windowApi = vi.hoisted(() => ({ onCloseRequested: vi.fn(), destroy: vi.fn() }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => windowApi }));
afterEach(cleanup);

it("disposes a registration that resolves after unmount and ignores its stale callback", async () => {
  let resolve!: (listener: () => void) => void;
  windowApi.onCloseRequested.mockReturnValue(new Promise<() => void>((done) => { resolve = done; }));
  const flush = vi.fn();
  const hook = renderHook(() => useCloseWithFlush(flush, vi.fn()));
  const callback = windowApi.onCloseRequested.mock.calls[0][0];
  hook.unmount();
  const unlisten = vi.fn();
  await act(async () => resolve(unlisten));
  await callback({ preventDefault: vi.fn() });
  expect(unlisten).toHaveBeenCalledTimes(1);
  expect(flush).not.toHaveBeenCalled();
  expect(windowApi.destroy).not.toHaveBeenCalled();
});

it("finishes saving before destroying the window and coalesces close events", async () => {
  windowApi.onCloseRequested.mockResolvedValue(vi.fn());
  let finish!: () => void;
  const flush = vi.fn(() => new Promise<void>((done) => { finish = done; }));
  const onError = vi.fn();
  renderHook(() => useCloseWithFlush(flush, onError));
  const callback = windowApi.onCloseRequested.mock.calls[0][0];
  const event = { preventDefault: vi.fn() };
  const closing = callback(event);
  await callback(event);
  expect(flush).toHaveBeenCalledTimes(1);
  expect(windowApi.destroy).not.toHaveBeenCalled();
  await act(async () => { finish(); await closing; });
  expect(windowApi.destroy).toHaveBeenCalledTimes(1);
});
