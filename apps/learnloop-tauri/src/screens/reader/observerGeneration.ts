// Reader workbench RW3b: one generation of IntersectionObservers (Codex
// verify F21, F22).
//
// An observer the Reader disconnects can still deliver entries the browser
// had buffered before the disconnect. Each generation is built for one cue
// plan, and its callbacks are bound to that plan in the caller's closure. A
// callback from an observer of this generation that was disconnected is
// discarded, never re-labelled: the observer that replaces it measures again
// under its own plan. The passage observers (useCueImpressions) and each
// margin mark's observer (MarginMark) both use this.

export interface ObserverGeneration {
  /** A new observer of this generation watching `targets`. */
  observe(
    targets: Element[],
    threshold: number | number[],
    onEntries: (entries: IntersectionObserverEntry[], observer: IntersectionObserver) => void,
  ): IntersectionObserver;
  /** Disconnect one observer; its later callbacks are discarded. */
  disconnect(observer: IntersectionObserver): void;
  /** Disconnect every observer of this generation. */
  disconnectAll(): void;
}

export function observerGeneration(): ObserverGeneration {
  const live = new Set<IntersectionObserver>();
  let observers: IntersectionObserver[] = [];
  return {
    observe(targets, threshold, onEntries) {
      const observer = new IntersectionObserver((entries) => {
        if (!live.has(observer)) return;  // delivered after its disconnect
        onEntries(entries, observer);
      }, { threshold });
      live.add(observer);
      observers.push(observer);
      for (const target of targets) observer.observe(target);
      return observer;
    },
    disconnect(observer) {
      live.delete(observer);
      observer.disconnect();
    },
    disconnectAll() {
      for (const observer of observers) {
        live.delete(observer);
        observer.disconnect();
      }
      observers = [];
    },
  };
}
