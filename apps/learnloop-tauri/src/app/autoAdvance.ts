// Daily-loop P2 auto-advance (spec_daily_loop_v1.md §6.5, phase DL0).
//
// "Next" on feedback opens the head of the live queue directly: the item Today
// would focus first, served with the candidate id of the slate that ranked it.
// The queue is read while feedback shows, through the same cache entry Today
// reads, so going back to the list (Esc / b) repaints from it instead of
// waiting on a second scheduler pass.

import { useCallback, useMemo } from "react";
import { api } from "../api/client";
import type { QueueInput, QueueSnapshot, ScheduledItemDto, SessionSnapshot } from "../api/dto";
import { getOrFetch, hashKey, isStale, peek, type QueryKey } from "../api/queryCache";
import { TAG } from "../api/queryTags";
import { useCachedQuery } from "../api/useCachedQuery";

/** Reads `resolve` makes before giving up on a queue that keeps being invalidated. */
const MAX_HEAD_READS = 4;

/** The exact get_today_queue input Today sends for a session. Sharing it shares the cache key. */
export function todayQueueInput(session: SessionSnapshot | null): QueueInput {
  return {
    sessionId: session?.sessionId ?? null,
    availableMinutes: session?.availableMinutes ?? null,
    energy: session?.energy ?? null
  };
}

export function todayQueueKey(input: QueueInput): QueryKey {
  return ["get_today_queue", input];
}

/** The item Today focuses first: the top row of the first section that has one. */
export function queueHead(snapshot: QueueSnapshot | null | undefined): ScheduledItemDto | null {
  for (const section of snapshot?.sections ?? []) {
    if (section.items.length > 0) return section.items[0];
  }
  return null;
}

export interface NextQueueItem {
  /** Head of the current queue; null while unknown, refreshing, or empty. */
  readonly head: ScheduledItemDto | null;
  /** A queue has been read and it holds nothing to serve. */
  readonly empty: boolean;
  /**
   * The head of a queue built after the latest queue invalidation (an attempt,
   * a regrade, a forced follow-up, a vault change). Shares a request already
   * in flight, but never returns its result if an invalidation landed while it
   * was out; null when the queue is empty or keeps being invalidated.
   */
  readonly resolve: () => Promise<ScheduledItemDto | null>;
}

/**
 * Read Today's queue for `input` while `prefetch` is true, and resolve its head
 * on demand. A null input disables both (no session, or a flow that must keep
 * returning to its own screen).
 */
export function useNextQueueItem(input: QueueInput | null, prefetch: boolean): NextQueueItem {
  // Keyed by content, not identity: a new but equal input object is the same query.
  const hash = input ? hashKey(todayQueueKey(input)) : null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const key = useMemo(() => (input ? todayQueueKey(input) : null), [hash]);
  const query = useCachedQuery<QueueSnapshot>(
    prefetch ? key : null,
    () => api.getTodayQueue(input as QueueInput),
    { tags: [TAG.queue] }
  );
  // Like Today's rows, a queue known to predate an invalidation names nothing.
  const current = query.data !== undefined && !query.refreshing;
  const head = current ? queueHead(query.data) : null;
  const empty = current && head === null;

  const resolve = useCallback(async (): Promise<ScheduledItemDto | null> => {
    if (!key || !input) return null;
    // Infinity: cached data counts as current unless an invalidation landed
    // after the fetch that produced it, which is exactly Today's rule for
    // making rows actionable. A request already in flight is shared, and it
    // may have been invalidated before it answered (a write or a vault change
    // landing mid-read), so its result is checked against the latest
    // invalidation once it arrives, and read again when it predates one.
    for (let read = 0; read < MAX_HEAD_READS; read += 1) {
      const snapshot = await getOrFetch<QueueSnapshot>(key, () => api.getTodayQueue(input), {
        tags: [TAG.queue],
        staleAfterMs: Infinity
      });
      const state = peek<QueueSnapshot>(key);
      if (!isStale(state, Infinity)) return queueHead(state.data ?? snapshot);
    }
    // Still invalidated faster than it can be read: open nothing, and let the
    // list show the queue once it settles.
    return null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { head, empty, resolve };
}
