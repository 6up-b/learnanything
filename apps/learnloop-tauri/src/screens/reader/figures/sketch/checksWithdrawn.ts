// Reader RW5d P2, fix round 4 (the independent sandbox review, finding 1): a
// sketch's code-owned checks, withdrawn for the session once the page's own
// run disagrees with the run verification checked.
//
// The desktop computes the digest of every read it makes; at a state the
// verifier tested (its parameters, the verified seed, a checked step) a
// different digest means what is drawn is not what was checked. The checks
// are then withdrawn for that figure, everywhere it shows (the collapsed
// line's badge and the open sketch), until the Reader is reloaded: the figure
// shows as an illustration ("nothing in it checked"), failing closed.
import { useSyncExternalStore } from "react";

const withdrawn = new Set<string>();
const listeners = new Set<() => void>();

export function withdrawChecks(figureId: string): void {
  if (withdrawn.has(figureId)) return;
  withdrawn.add(figureId);
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function checksWithdrawn(figureId: string): boolean {
  return withdrawn.has(figureId);
}

export function useChecksWithdrawn(figureId: string): boolean {
  return useSyncExternalStore(subscribe, () => withdrawn.has(figureId), () => withdrawn.has(figureId));
}

/** Tests only: forget every withdrawal. */
export function resetWithdrawnChecks(): void {
  withdrawn.clear();
  for (const listener of listeners) listener();
}
