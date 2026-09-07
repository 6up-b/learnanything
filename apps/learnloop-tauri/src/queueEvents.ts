import { invalidate } from "./api/queryCache";
import { TAG } from "./api/queryTags";

const QUEUE_CHANGED_EVENT = "learnloop:queue-changed";

/**
 * Broadcast that the practice queue (or something feeding it) changed. Cached
 * queue reads are marked stale first, so screens reading through the query
 * cache refetch, then the legacy window listeners run.
 */
export function notifyQueueChanged(): void {
  invalidate({ tags: [TAG.queue] });
  window.dispatchEvent(new Event(QUEUE_CHANGED_EVENT));
}

export function subscribeQueueChanged(listener: () => void): () => void {
  window.addEventListener(QUEUE_CHANGED_EVENT, listener);
  return () => window.removeEventListener(QUEUE_CHANGED_EVENT, listener);
}
