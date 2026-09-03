import { useCallback, useEffect, useRef, useSyncExternalStore } from "react";
import type { CommandError } from "./dto";
import {
  EMPTY_STATE,
  getOrFetch,
  hashKey,
  isStale,
  peek,
  subscribe,
  type FetchOptions,
  type QueryKey,
  type QueryState,
  type QueryTag
} from "./queryCache";

export interface CachedQuery<T> {
  readonly data: T | undefined;
  /** Nothing cached yet and a fetch is (about to be) in flight. */
  readonly loading: boolean;
  /** Data is on screen but expired, invalidated, or being revalidated. */
  readonly stale: boolean;
  readonly error: CommandError | null;
  /** Force a fetch (shares an in-flight request). Rejects when the query is disabled. */
  readonly refetch: () => Promise<T>;
}

export interface CachedQueryOptions {
  readonly tags?: readonly QueryTag[];
  /** `false` (or a null key) reads nothing and never fetches. */
  readonly enabled?: boolean;
  readonly staleAfterMs?: number;
}

/**
 * Read a sidecar result through the query cache with stale-while-revalidate
 * semantics: a cached value renders immediately and a background fetch
 * refreshes it; `loading` is true only when nothing is cached.
 *
 * The store owns the promise and the state, so unmounting simply
 * unsubscribes — there is no setState-after-unmount and StrictMode's double
 * mount costs no extra request. `fetcher` and `options` may be inline: the
 * latest values are read through refs when a fetch actually starts.
 */
export function useCachedQuery<T>(
  key: QueryKey | null,
  fetcher: () => Promise<T>,
  options: CachedQueryOptions = {}
): CachedQuery<T> {
  const enabled = options.enabled ?? true;
  const hash = key ? hashKey(key) : null;
  const keyRef = useRef(key);
  keyRef.current = key;
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const subscribeToKey = useCallback(
    (listener: () => void) => (hash && keyRef.current ? subscribe(keyRef.current, listener) : () => undefined),
    [hash]
  );
  const getSnapshot = useCallback(
    (): QueryState<T> => (hash && keyRef.current ? peek<T>(keyRef.current) : EMPTY_STATE),
    [hash]
  );
  const state = useSyncExternalStore(subscribeToKey, getSnapshot);

  const start = useCallback(
    (force: boolean): Promise<T> => {
      const current = keyRef.current;
      if (!current) return Promise.reject(new Error("query is disabled"));
      const fetchOptions: FetchOptions = {
        tags: optionsRef.current.tags,
        staleAfterMs: optionsRef.current.staleAfterMs,
        force
      };
      return getOrFetch(current, () => fetcherRef.current(), fetchOptions);
    },
    // `hash` stands in for the key contents.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [hash]
  );

  // Fetch on mount / key change, and again whenever the entry is invalidated
  // (the stamp changes). getOrFetch is a no-op when the data is still fresh
  // or a request is already in flight.
  useEffect(() => {
    if (!enabled || !hash) return;
    void start(false).catch(() => undefined);
  }, [enabled, hash, start, state.invalidatedAt]);

  const refetch = useCallback(() => start(true), [start]);

  const loading = enabled && hash !== null && state.data === undefined && state.error === null;
  const stale = state.data !== undefined && (state.fetching || isStale(state, optionsRef.current.staleAfterMs));
  return { data: state.data, loading, stale, error: state.error, refetch };
}
