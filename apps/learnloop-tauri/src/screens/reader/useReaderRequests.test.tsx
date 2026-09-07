import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useReaderRequests } from "./useReaderRequests";

const api = vi.hoisted(() => ({ readerSourceRequests: vi.fn(), readerProposalInbox: vi.fn(), readerSourceObjects: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));
const snapshot = (a: string, b: string) => ({ requests: [{ id: "a", status: a }, { id: "b", status: b }] });
beforeEach(() => {
  vi.useFakeTimers();
  api.readerSourceRequests.mockReset().mockResolvedValue(snapshot("running", "running"));
  api.readerProposalInbox.mockReset().mockResolvedValue({ proposals: [] });
  api.readerSourceObjects.mockReset().mockResolvedValue({ sourceObjects: [] });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });
const tick = async () => act(async () => { await vi.advanceTimersByTimeAsync(2000); });

it("hydrates a completed request while another remains active", async () => {
  const { result } = renderHook(() => useReaderRequests("source", true));
  await act(async () => {});
  api.readerSourceRequests.mockResolvedValue(snapshot("completed", "running"));
  api.readerSourceObjects.mockResolvedValue({ sourceObjects: [{ object: { id: "artifact-a" }, version: { contentJson: '{"content_md":"Ready"}' } }] });
  await tick();
  expect(result.current.synthesizedObjects.get("artifact-a")?.contentMd).toBe("Ready");
  expect(api.readerSourceObjects).toHaveBeenCalledTimes(2);
  await tick();
  expect(api.readerSourceObjects).toHaveBeenCalledTimes(2);
});

it("retries failed final hydration before stopping polling", async () => {
  const { result } = renderHook(() => useReaderRequests("source", true));
  await act(async () => {});
  api.readerSourceRequests.mockResolvedValue(snapshot("completed", "completed"));
  api.readerSourceObjects.mockRejectedValueOnce(new Error("temporary"));
  await tick();
  expect(result.current.loadError).toContain("temporary");
  await tick();
  expect(result.current.loadError).toBeNull();
  expect(result.current.requests.every((request) => request.status === "completed")).toBe(true);
  const calls = api.readerSourceRequests.mock.calls.length;
  await tick();
  expect(api.readerSourceRequests).toHaveBeenCalledTimes(calls);
});

it("does not overlap slow polls or hydrate after unmount", async () => {
  const hook = renderHook(() => useReaderRequests("source", true));
  await act(async () => {});
  let finish!: (value: ReturnType<typeof snapshot>) => void;
  api.readerSourceRequests.mockImplementation(() => new Promise((done) => { finish = done; }));
  await tick();
  await act(async () => { await vi.advanceTimersByTimeAsync(20000); });
  expect(api.readerSourceRequests).toHaveBeenCalledTimes(2);
  hook.unmount();
  await act(async () => finish(snapshot("completed", "completed")));
  expect(api.readerSourceObjects).toHaveBeenCalledTimes(1);
});

it("ignores an old A response after switching A to B to A", async () => {
  let finish!: (value: { sourceObjects: unknown[] }) => void;
  api.readerSourceObjects.mockImplementationOnce(() => new Promise((done) => { finish = done; }));
  const hook = renderHook(({ source }) => useReaderRequests(source, true), { initialProps: { source: "a" } });
  await act(async () => {});
  hook.rerender({ source: "b" });
  await act(async () => {});
  hook.rerender({ source: "a" });
  await act(async () => {});
  await act(async () => finish({ sourceObjects: [{ object: { id: "stale" } }] }));
  expect(hook.result.current.synthesizedObjects.has("stale")).toBe(false);
});
