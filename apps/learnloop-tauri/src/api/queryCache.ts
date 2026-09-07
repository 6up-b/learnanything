/**
 * A small stale-while-revalidate store for sidecar reads.
 *
 * Screens unmount on every tab switch and used to refetch everything on
 * mount, queueing behind the single serialized sidecar pipe. This module keeps
 * the last result per (command, args) so a returning screen paints instantly
 * and revalidates in the background. It is framework-free; React binds to it
 * through useCachedQuery.
 *
 * Rules of the store:
 * - one in-flight promise per key (concurrent callers share it);
 * - invalidation marks entries stale but keeps their data;
 * - clear() drops everything (vault switch) and bumps a generation so results
 *   from the old vault that are still in flight are discarded;
 * - a revalidation whose payload is JSON-identical keeps the previous object
 *   reference, so memoised layouts and "select the first item" effects do not
 *   re-run for a no-op refresh.
 */
import type { CommandError } from "./dto";
import { errorMessage, getCommandError } from "../errors";

export type QueryKey = readonly [command: string, ...args: unknown[]];
export type QueryTag = string;

export interface QueryState<T> {
  readonly data: T | undefined;
  readonly error: CommandError | null;
  /** Start time of the fetch that produced `data` (0 = never fetched). */
  readonly updatedAt: number;
  /** Time of the latest invalidation touching this entry (0 = never). */
  readonly invalidatedAt: number;
  readonly fetching: boolean;
}

export interface FetchOptions {
  readonly tags?: readonly QueryTag[];
  /**
   * How long a result stays fresh. 0 (default) revalidates whenever a caller
   * asks (pure stale-while-revalidate); Infinity only refetches on
   * invalidation. Use a positive number for expensive, slow-moving reads.
   */
  readonly staleAfterMs?: number;
  /** Ignore freshness. Still shares an in-flight request. */
  readonly force?: boolean;
}

export type InvalidateTarget =
  | { readonly tags: readonly QueryTag[] }
  | { readonly key: QueryKey }
  | { readonly tagPrefix: string };

interface Entry {
  readonly hash: string;
  readonly tags: Set<QueryTag>;
  readonly listeners: Set<() => void>;
  state: QueryState<unknown>;
  promise: Promise<unknown> | null;
  lastTouched: number;
}

/** Idle entries beyond this count are evicted least-recently-used first. */
const MAX_ENTRIES = 200;

export const EMPTY_STATE: QueryState<never> = Object.freeze({
  data: undefined,
  error: null,
  updatedAt: 0,
  invalidatedAt: 0,
  fetching: false
});

const entries = new Map<string, Entry>();
let generation = 0;

function stableStringify(value: unknown): string {
  if (value === undefined) return "undefined";
  if (value === null || typeof value !== "object") return JSON.stringify(value) ?? "null";
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  const record = value as Record<string, unknown>;
  const keys = Object.keys(record)
    .filter((key) => record[key] !== undefined)
    .sort();
  return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`).join(",")}}`;
}

export function hashKey(key: QueryKey): string {
  const [command, ...args] = key;
  return `${command}:${stableStringify(args)}`;
}

export function isStale(state: QueryState<unknown>, staleAfterMs = 0, now = Date.now()): boolean {
  if (state.data === undefined) return true;
  if (state.invalidatedAt > state.updatedAt) return true;
  if (staleAfterMs === Infinity) return false;
  return now - state.updatedAt > staleAfterMs;
}

function ensure(key: QueryKey): Entry {
  const hash = hashKey(key);
  let entry = entries.get(hash);
  if (entry) {
    entry.lastTouched = Date.now();
    return entry;
  }
  entry = {
    hash,
    tags: new Set(),
    listeners: new Set(),
    state: EMPTY_STATE,
    promise: null,
    lastTouched: Date.now()
  };
  entries.set(hash, entry);
  evictIdleEntries();
  return entry;
}

function evictIdleEntries(): void {
  if (entries.size <= MAX_ENTRIES) return;
  const idle = [...entries.values()]
    .filter((entry) => entry.listeners.size === 0 && entry.promise === null)
    .sort((a, b) => a.lastTouched - b.lastTouched);
  for (const entry of idle) {
    if (entries.size <= MAX_ENTRIES) break;
    entries.delete(entry.hash);
  }
}

function setState(entry: Entry, next: QueryState<unknown>): void {
  entry.state = next;
  for (const listener of entry.listeners) listener();
}

function sameJson(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
}

function toCommandError(error: unknown): CommandError {
  return getCommandError(error) ?? { code: "internal", message: errorMessage(error), retryable: false };
}

/** A timestamp strictly after `updatedAt`, so a same-millisecond invalidation still counts. */
function staleStamp(state: QueryState<unknown>, now: number): number {
  return Math.max(now, state.updatedAt + 1, state.invalidatedAt + 1);
}

/** Current state for a key without triggering a fetch (stable reference until it changes). */
export function peek<T>(key: QueryKey): QueryState<T> {
  const entry = entries.get(hashKey(key));
  return (entry?.state as QueryState<T> | undefined) ?? EMPTY_STATE;
}

/**
 * Resolve with cached data when fresh, otherwise run `fetcher` once and share
 * the promise with every concurrent caller of the same key.
 */
export function getOrFetch<T>(key: QueryKey, fetcher: () => Promise<T>, options: FetchOptions = {}): Promise<T> {
  const entry = ensure(key);
  for (const tag of options.tags ?? []) entry.tags.add(tag);
  if (entry.promise) return entry.promise as Promise<T>;
  const state = entry.state as QueryState<T>;
  if (!options.force && !isStale(state, options.staleAfterMs)) {
    return Promise.resolve(state.data as T);
  }
  const startedAt = Date.now();
  const startedIn = generation;
  setState(entry, { ...state, fetching: true });
  const promise: Promise<T> = fetcher()
    .then(
      (result) => {
        // The cache was cleared while this request was in flight (vault
        // switch): the result belongs to the old vault and must not land.
        if (startedIn !== generation) return result;
        const current = entry.state as QueryState<T>;
        // Reference preservation only matters to a mounted subscriber's memos;
        // skip the (potentially multi-MB) stringify when nobody is listening.
        const keepReference =
          entry.listeners.size > 0 && current.data !== undefined && sameJson(current.data, result);
        const data = keepReference ? (current.data as T) : result;
        setState(entry, {
          data,
          error: null,
          updatedAt: startedAt,
          invalidatedAt: current.invalidatedAt,
          fetching: false
        });
        if (current.invalidatedAt > startedAt) {
          // Invalidated while this request was in flight (a mutation resolved
          // off the primary pipe): the result is already stale, so follow up
          // once. The follow-up starts after the stamp, so it cannot loop.
          void getOrFetch(key, fetcher, { ...options, force: true }).catch(() => undefined);
        }
        return data;
      },
      (error: unknown) => {
        if (startedIn === generation) {
          setState(entry, { ...entry.state, error: toCommandError(error), fetching: false });
        }
        throw error;
      }
    )
    .finally(() => {
      if (entry.promise === promise) entry.promise = null;
    });
  entry.promise = promise;
  return promise;
}

/** Seed or overwrite a key from data already in hand (e.g. a mutation's returned snapshot). */
export function setQueryData<T>(key: QueryKey, data: T, tags: readonly QueryTag[] = []): void {
  const entry = ensure(key);
  for (const tag of tags) entry.tags.add(tag);
  setState(entry, {
    data,
    error: null,
    updatedAt: Date.now(),
    invalidatedAt: entry.state.invalidatedAt,
    fetching: entry.state.fetching
  });
}

function markStale(entry: Entry, now: number): void {
  // Nothing to refresh: never fetched and not fetching. An entry whose fetch
  // FAILED is included, so an invalidation gives it another try.
  if (entry.state.data === undefined && entry.state.error === null && entry.promise === null) return;
  setState(entry, { ...entry.state, invalidatedAt: staleStamp(entry.state, now) });
}

/** Mark matching entries stale; their data stays available for an instant paint. */
export function invalidate(target: InvalidateTarget): void {
  const now = Date.now();
  const matches = (entry: Entry): boolean => {
    if ("key" in target) return entry.hash === hashKey(target.key);
    if ("tagPrefix" in target) {
      for (const tag of entry.tags) {
        if (tag.startsWith(target.tagPrefix)) return true;
      }
      return false;
    }
    return target.tags.some((tag) => entry.tags.has(tag));
  };
  for (const entry of entries.values()) {
    if (matches(entry)) markStale(entry, now);
  }
}

/** Mark everything stale (vault files changed on disk). */
export function invalidateAll(): void {
  const now = Date.now();
  for (const entry of entries.values()) markStale(entry, now);
}

/** Drop every result (vault switch). Subscribed entries are emptied, not deleted. */
export function clear(): void {
  generation += 1;
  const now = Date.now();
  for (const entry of [...entries.values()]) {
    entry.promise = null;
    if (entry.listeners.size === 0) {
      entries.delete(entry.hash);
      continue;
    }
    // A fresh stamp makes subscribers' fetch effects re-run for the new vault.
    setState(entry, { ...EMPTY_STATE, invalidatedAt: staleStamp(entry.state, now) });
  }
}

export function subscribe(key: QueryKey, listener: () => void): () => void {
  const entry = ensure(key);
  entry.listeners.add(listener);
  return () => {
    entry.listeners.delete(listener);
  };
}
