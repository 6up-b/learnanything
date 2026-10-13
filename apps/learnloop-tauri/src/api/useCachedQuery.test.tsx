// A disabled query is a state, never an error (UX Phase 1 usability round 2):
// Today's plan view disables its full-list read, and a background "refresh the
// list" on that disabled read surfaced as a red "query is disabled" banner that
// stayed on every tab until a restart.
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { clear } from "./queryCache";
import { useCachedQuery } from "./useCachedQuery";

afterEach(() => {
  cleanup();
  clear();
});

it("refetching a query with no key fetches nothing and does not fail", async () => {
  const fetcher = vi.fn(async () => "fresh");
  const { result } = renderHook(() => useCachedQuery<string>(null, fetcher));

  let value: string | undefined = "unset";
  await act(async () => {
    value = await result.current.refetch();
  });

  expect(value).toBeUndefined();
  expect(fetcher).not.toHaveBeenCalled();
  expect(result.current.error).toBeNull();
});

it("refetching a query turned off with enabled: false fetches nothing either", async () => {
  const fetcher = vi.fn(async () => "fresh");
  const { result } = renderHook(() => useCachedQuery<string>(["get_today_queue", { off: true }], fetcher, { enabled: false }));

  let value: string | undefined = "unset";
  await act(async () => {
    value = await result.current.refetch();
  });

  expect(value).toBeUndefined();
  expect(fetcher).not.toHaveBeenCalled();
});

it("refetching an enabled query still fetches", async () => {
  const fetcher = vi.fn(async () => "fresh");
  const { result } = renderHook(() => useCachedQuery<string>(["get_today_queue", { on: true }], fetcher));

  let value: string | undefined;
  await act(async () => {
    value = await result.current.refetch();
  });

  expect(value).toBe("fresh");
});
