// The four connection states of mobile v2 §4.4, plus a stale app (§5.2), as one small store.
// The transport reports what each exchange showed; the shell shows one quiet line for it.
import { useSyncExternalStore } from "react";

export interface ConnectionState {
  /** No answer from the host: a network error, or Serve's own 502/504 (`OFFLINE`). */
  readonly offline: boolean;
  /** `503 host_busy` or `database_busy`: reachable, and retried per policy. */
  readonly busy: boolean;
  /** `grading_fallback_required`: everything but a new grade still works. */
  readonly gradingDown: boolean;
  /** This build and the host disagree about the allowlist: a reload fixes it (§5.2). */
  readonly stale: boolean;
}

const INITIAL: ConnectionState = { offline: false, busy: false, gradingDown: false, stale: false };
let state: ConnectionState = INITIAL;
const listeners = new Set<() => void>();
const reconnectListeners = new Set<() => void>();

function set(next: Partial<ConnectionState>): void {
  const merged = { ...state, ...next };
  if (Object.keys(merged).every((key) => merged[key as keyof ConnectionState] === state[key as keyof ConnectionState])) return;
  const wasOffline = state.offline;
  state = merged;
  for (const listener of listeners) listener();
  // §4.4's reconnect: the shell runs it once per return from offline.
  if (wasOffline && !state.offline) for (const listener of reconnectListeners) listener();
}

export function connectionState(): ConnectionState {
  return state;
}

/** Any answer the host itself gave: reachable, and not busy unless this answer said so. */
export function markReachable(busy = false): void {
  set({ offline: false, busy });
}

export function markOffline(): void {
  set({ offline: true, busy: false });
}

export function markGradingDown(): void {
  set({ gradingDown: true });
}

export function markGradingUp(): void {
  set({ gradingDown: false });
}

export function markStale(): void {
  set({ stale: true });
}

export function subscribeConnection(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Told when the host answers again after being offline. */
export function onReconnect(listener: () => void): () => void {
  reconnectListeners.add(listener);
  return () => reconnectListeners.delete(listener);
}

export function useConnection(): ConnectionState {
  return useSyncExternalStore(subscribeConnection, connectionState, connectionState);
}

export function resetConnectionForTests(): void {
  state = INITIAL;
  listeners.clear();
  reconnectListeners.clear();
}
