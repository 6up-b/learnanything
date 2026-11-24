// Shared parameters (spec §13.1): every instance of one figure shares its parameters, so dragging the temperature
// in one (the book window's inset, the companion's widget) updates the others. Held per figure id for this run of
// the app; a figure's first instance starts at its defaults. A new version of a figure is a new id, with its own.
import { useCallback, useSyncExternalStore } from "react";

const values = new Map<string, Record<string, number>>();
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The figure's parameters (its defaults until any instance changes one) and the setter every instance shares. */
export function useSharedParams(figureId: string, defaults: () => Record<string, number>):
  [Record<string, number>, (change: (current: Record<string, number>) => Record<string, number>) => void] {
  const stored = useSyncExternalStore(subscribe, () => values.get(figureId) ?? null);
  const params = stored ?? defaultsFor(figureId, defaults);
  const set = useCallback((change: (current: Record<string, number>) => Record<string, number>) => {
    values.set(figureId, change(values.get(figureId) ?? defaultsFor(figureId, defaults)));
    emit();
  }, [figureId, defaults]);
  return [params, set];
}

// The defaults object is kept per figure, so an instance that has not changed anything renders a stable value.
const defaultsSeen = new Map<string, Record<string, number>>();
function defaultsFor(figureId: string, defaults: () => Record<string, number>): Record<string, number> {
  let seen = defaultsSeen.get(figureId);
  if (!seen) {
    seen = defaults();
    defaultsSeen.set(figureId, seen);
  }
  return seen;
}

/** Tests only. */
export function resetSharedParamsForTests(): void {
  values.clear();
  defaultsSeen.clear();
  emit();
}
