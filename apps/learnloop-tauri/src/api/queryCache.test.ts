import { afterEach, expect, it, vi } from "vitest";
import { clear, getOrFetch, invalidate, isStale, peek, type QueryKey } from "./queryCache";

const KEY: QueryKey = ["get_today_queue", { sessionId: "s1" }];

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

async function settle() {
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
}

afterEach(() => {
  clear();
  vi.restoreAllMocks();
});

// An invalidation that lands while a fetch is in flight makes that fetch's
// result stale the moment it arrives: the store must say so, and follow up.
it.each([
  ["a later millisecond", 1],
  ["the same millisecond as the fetch started", 0]
])("follows up a fetch invalidated in flight (%s)", async (_label, tick) => {
  let now = 1_000;
  vi.spyOn(Date, "now").mockImplementation(() => now);
  const first = deferred<string>();
  const second = deferred<string>();
  const fetcher = vi.fn<() => Promise<string>>()
    .mockReturnValueOnce(first.promise)
    .mockReturnValueOnce(second.promise);

  const request = getOrFetch(KEY, fetcher, { tags: ["queue"] });
  now += tick;
  invalidate({ tags: ["queue"] });
  first.resolve("built before the invalidation");
  expect(await request).toBe("built before the invalidation");
  // The result is on record, but known to predate the invalidation.
  expect(isStale(peek(KEY), Infinity)).toBe(true);

  await settle();
  expect(fetcher).toHaveBeenCalledTimes(2);
  // A caller arriving now shares the follow-up instead of reading the stale result.
  const shared = getOrFetch(KEY, fetcher, { tags: ["queue"], staleAfterMs: Infinity });
  second.resolve("rebuilt");
  expect(await shared).toBe("rebuilt");
  expect(isStale(peek(KEY), Infinity)).toBe(false);
  await settle();
  expect(fetcher).toHaveBeenCalledTimes(2);
});

it("does not follow up a fetch nothing invalidated", async () => {
  const fetcher = vi.fn(() => Promise.resolve("queue"));
  expect(await getOrFetch(KEY, fetcher, { tags: ["queue"] })).toBe("queue");
  await settle();
  expect(fetcher).toHaveBeenCalledOnce();
  expect(isStale(peek(KEY), Infinity)).toBe(false);
});
