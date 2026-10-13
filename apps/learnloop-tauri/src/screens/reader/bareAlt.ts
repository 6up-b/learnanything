// K7: the bare-Alt "clear capture" gesture, without eating Alt chords.
//
// Clearing used to happen on Alt *keydown*, so every chord that starts with
// Alt (Alt+←/→ for the return stack, Alt+↑/↓ for marks, Alt+drag sweeps,
// Alt+Tab) dropped the learner's capture before the chord's second key
// arrived. The gesture now completes on Alt *keyup*, and only when nothing
// else (a key, a pointer press, the window losing focus) happened while Alt
// was held.
import { useEffect, useRef } from "react";

function editable(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement
    && (target.isContentEditable || target.closest("input, textarea, select") !== null)
  );
}

export function useBareAltClear(onClear: () => void): void {
  const onClearRef = useRef(onClear);
  onClearRef.current = onClear;
  useEffect(() => {
    // null: Alt is up. Otherwise whether the press may still clear.
    let pending: boolean | null = null;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Alt") {
        if (event.repeat) return;
        pending = !editable(event.target);
        return;
      }
      if (pending !== null) pending = false;
    };
    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key !== "Alt") return;
      const clear = pending === true && !editable(event.target);
      pending = null;
      if (clear) onClearRef.current();
    };
    const cancel = () => {
      if (pending !== null) pending = false;
    };
    const reset = () => {
      pending = null;
    };
    window.addEventListener("keydown", onKeyDown, true);
    window.addEventListener("keyup", onKeyUp, true);
    window.addEventListener("mousedown", cancel, true);
    window.addEventListener("blur", reset);
    return () => {
      window.removeEventListener("keydown", onKeyDown, true);
      window.removeEventListener("keyup", onKeyUp, true);
      window.removeEventListener("mousedown", cancel, true);
      window.removeEventListener("blur", reset);
    };
  }, []);
}
