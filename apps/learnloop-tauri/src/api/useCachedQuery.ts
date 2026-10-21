import { useCallback, useEffect, useRef, useSyncExternalStore } from "react";
import type { CommandError } from "./dto";
import { RETRY_RAN, type ErrorReport, type NoticeRetry } from "../errors";
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
  /**
   * The data on screen predates an invalidation and its replacement is in
   * flight: what is shown is known to be out of date (not merely aged out).
   * Screens whose rows trigger actions gate keyboard shortcuts on this.
   */
  readonly refreshing: boolean;
  readonly error: CommandError | null;
  /**
   * Force a fetch (shares an in-flight request). A disabled query (a null key,
   * or `enabled: false`) fetches nothing and resolves with whatever is cached,
   * usually `undefined`: being turned off is a state, never an error
   * (UX Phase 1 usability round 2: a refresh of Today's turned-off full list
   * surfaced as a red "query is disabled" banner on every tab).
   */
  readonly refetch: () => Promise<T | undefined>;
  /**
   * What the shell needs to retry this query after it failed (UX Phase 2 fix
   * round 3): its identity (`query:` plus the key's hash) and a self-contained
   * retry. The retry is bound when this is called, to the key, fetcher and
   * options of that render, and forces a fetch through the cache for that key.
   * It ignores whether the hook is enabled, which view is showing and whether
   * the screen is still mounted. `refetch`, by contrast, resolves without a
   * request while the query is turned off. It resolves `RETRY_RAN` once that
   * request succeeded and rejects with the request's error otherwise. Null
   * without a key.
   */
  readonly retryReport: () => { source: string; retry: NoticeRetry } | null;
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
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;

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
    (force: boolean): Promise<T | undefined> => {
      const current = keyRef.current;
      if (!current || !enabledRef.current) {
        return Promise.resolve(current ? peek<T>(current).data : undefined);
      }
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
  const retryReport = useCallback((): { source: string; retry: NoticeRetry } | null => {
    const failedKey = keyRef.current;
    if (!failedKey) return null;
    const fetcherNow = fetcherRef.current;
    const { tags, staleAfterMs } = optionsRef.current;
    return {
      source: `query:${hashKey(failedKey)}`,
      retry: () => getOrFetch(failedKey, () => fetcherNow(), { tags, staleAfterMs, force: true }).then(() => RETRY_RAN)
    };
  }, []);

  const loading = enabled && hash !== null && state.data === undefined && state.error === null;
  const stale = state.data !== undefined && (state.fetching || isStale(state, optionsRef.current.staleAfterMs));
  const refreshing = state.data !== undefined && state.fetching && state.invalidatedAt > state.updatedAt;
  return { data: state.data, loading, stale, refreshing, error: state.error, refetch, retryReport };
}

/**
 * Hand a query's failure to the shell as one actionable error (UX Phase 2 fix
 * round 3): the error itself (its code, whether it is retryable), its identity
 * (the query) and the query's self-contained retry (`retryReport`), bound
 * when the failure is reported. Every screen wiring a read's failure to
 * Try again goes through here, so none can hand over a retry that depends
 * on the screen's mode or on its still being mounted.
 */
export function useReportQueryError(
  query: Pick<CachedQuery<unknown>, "error" | "retryReport">,
  onError: (message: string, report?: ErrorReport) => void,
  /** False in the classic shell, where the screen keeps base's one aggregated
   *  report instead (fix round 4). */
  enabled = true
): void {
  const queryRef = useRef(query);
  queryRef.current = query;
  const error = query.error;
  useEffect(() => {
    if (!enabled || !error) return;
    const report = queryRef.current.retryReport();
    onError(error.message, report ? { error, ...report } : { error });
  }, [error, onError, enabled]);
}
