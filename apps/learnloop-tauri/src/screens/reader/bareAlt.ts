// K7: the bare-Alt "clear capture" gesture, without eating Alt chords.
//
// Clearing used to happen on Alt *keydown*, so every chord that starts with
// Alt (Alt+←/→ for the return stack, Alt+↑/↓ for marks, Alt+drag sweeps,
// Alt+Tab) dropped the learner's capture before the chord's second key
// arrived. The gesture now completes on Alt *keyup*, and only when nothing
// else (a key, a pointer press, the window losing focus) happened while Alt
// was held, and only for a tap: Alt held 400 ms or more shows the desks'
// which-key panel instead and never clears (workbench v2 spec §5.4).
import { useEffect, useRef } from "react";
import { screenLeavesKey } from "../../app/keymap";
import { useListenerHub } from "../desks/lifecycle";
import { WHICH_KEY_HOLD_MS } from "../desks/keys/router";

function editable(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement
    && (target.isContentEditable || target.closest("input, textarea, select") !== null)
  );
}

export function useBareAltClear(onClear: () => void, now: () => number = Date.now): void {
  const onClearRef = useRef(onClear);
  onClearRef.current = onClear;
  const nowRef = useRef(now);
  nowRef.current = now;
  const hub = useListenerHub();
  useEffect(() => {
    // null: Alt is up. Otherwise whether the press may still clear.
    let pending: boolean | null = null;
    let pressedAt = 0;
    const onKeyDown = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if (event.key === "Alt") {
        if (event.repeat) return;
        pending = !editable(event.target);
        pressedAt = nowRef.current();
        return;
      }
      if (pending !== null) pending = false;
    };
    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key !== "Alt") return;
      const tap = nowRef.current() - pressedAt < WHICH_KEY_HOLD_MS;
      const clear = pending === true && tap && !editable(event.target);
      pending = null;
      if (clear) onClearRef.current();
    };
    const cancel = () => {
      if (pending !== null) pending = false;
    };
    const reset = () => {
      pending = null;
    };
    const offs = [
      hub.listen("window", "keydown", onKeyDown, true),
      hub.listen("window", "keyup", onKeyUp, true),
      hub.listen("window", "mousedown", cancel, true),
      hub.listen("window", "blur", reset),
    ];
    return () => offs.forEach((off) => off());
  }, [hub]);
}
