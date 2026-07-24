const QUEUE_CHANGED_EVENT = "learnloop:queue-changed";

export function notifyQueueChanged(): void {
  window.dispatchEvent(new Event(QUEUE_CHANGED_EVENT));
}

export function subscribeQueueChanged(listener: () => void): () => void {
  window.addEventListener(QUEUE_CHANGED_EVENT, listener);
  return () => window.removeEventListener(QUEUE_CHANGED_EVENT, listener);
}
