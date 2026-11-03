import { useEffect, useRef } from "react";

/** Run `tick` every `ms` while the page is visible, and at once when it comes back. */
export function useVisibleInterval(tick: () => void, ms: number, enabled = true): void {
  const latest = useRef(tick);
  latest.current = tick;
  useEffect(() => {
    if (!enabled) return undefined;
    const run = () => {
      if (document.visibilityState !== "hidden") latest.current();
    };
    run();
    const timer = window.setInterval(run, ms);
    document.addEventListener("visibilitychange", run);
    window.addEventListener("focus", run);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", run);
      window.removeEventListener("focus", run);
    };
  }, [ms, enabled]);
}
