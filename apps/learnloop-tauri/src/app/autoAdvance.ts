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
import { getOrFetch, hashKey, type QueryKey } from "../api/queryCache";
import { TAG } from "../api/queryTags";
import { useCachedQuery } from "../api/useCachedQuery";

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
   * a regrade, a forced follow-up). Shares a request already in flight.
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
    // making rows actionable.
    const snapshot = await getOrFetch<QueueSnapshot>(key, () => api.getTodayQueue(input), {
      tags: [TAG.queue],
      staleAfterMs: Infinity
    });
    return queueHead(snapshot);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { head, empty, resolve };
}
