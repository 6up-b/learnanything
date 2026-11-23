// The window lifecycle contract (spec §3.6): every window kind reads its state here.
//
// - States: active (focused), visible (in view), offscreen (on this desk, out of view), hidden
//   (another desk) and preview (a card or miniature).
// - Only the active window owns keyboard input, the selection and the capture target: window-level
//   listeners go through the listener hub, which DeskShell's router fills, never straight onto
//   `window` or `document` (N windows never mean N handlers).
// - Offscreen and hidden windows pause effects, timers, polling and media.
// - Previews and programmatic moves generate no reading activity.
//
// Outside the desks (the old Reader, every other screen) nothing provides these contexts, and the
// defaults are the single-surface behaviour the app had before: active, never paused, listeners
// registered directly.
import { createContext, useContext, useEffect, useId, useRef, type ReactNode } from "react";

export type WindowState = "active" | "visible" | "offscreen" | "hidden" | "preview";

export interface WindowLifecycle {
  /** Null outside the desks. */
  windowId: string | null;
  state: WindowState;
}

const SINGLE_SURFACE: WindowLifecycle = { windowId: null, state: "active" };

export const WindowLifecycleContext = createContext<WindowLifecycle>(SINGLE_SURFACE);

export function useWindowLifecycle(): WindowLifecycle {
  return useContext(WindowLifecycleContext);
}

/** Paused windows run no timers, polling or media (offscreen, hidden and preview windows). */
export function isPaused(state: WindowState): boolean {
  return state === "offscreen" || state === "hidden" || state === "preview";
}

/** Reading activity (`reader.log_activity`, section progress, exposure) is attributed only to active
 * or visible windows; programmatic moves are told apart by the shell (`useProgrammaticMove`). */
export function mayLogReading(state: WindowState): boolean {
  return state === "active" || state === "visible";
}

export function useWindowPaused(): boolean {
  return isPaused(useWindowLifecycle().state);
}

/** Whether this surface may log reading activity now. Always true outside the desks. */
export function useReadingActivityAllowed(): boolean {
  return mayLogReading(useWindowLifecycle().state);
}

/** A ref that follows the reading-activity permission, for logging calls made from callbacks. */
export function useReadingActivityRef(): { readonly current: boolean } {
  const allowed = useReadingActivityAllowed();
  const ref = useRef(allowed);
  ref.current = allowed;
  return ref;
}

export interface WindowStateInput {
  onCurrentDesk: boolean;
  inView: boolean;
  /** This window is the desk's focus (the active pane of the focused slot). */
  focused: boolean;
  preview?: boolean;
  /** Focus mode shows only the focused window: every other window is offscreen. */
  focusMode?: boolean;
}

export function windowState(input: WindowStateInput): WindowState {
  if (input.preview) return "preview";
  if (!input.onCurrentDesk) return "hidden";
  if (input.focused) return "active";
  if (input.focusMode) return "offscreen";
  return input.inView ? "visible" : "offscreen";
}

// -- the listener hub -------------------------------------------------------------------------------

export type ListenTarget = "window" | "document";

export interface ListenerHub {
  /** Register a window- or document-level listener; returns its removal. */
  listen<E extends Event = Event>(target: ListenTarget, type: string, handler: (event: E) => void, options?: boolean | AddEventListenerOptions): () => void;
}

/** One surface, one set of listeners: registered on the real target, as before the desks. */
export const DIRECT_HUB: ListenerHub = {
  listen(target, type, handler, options) {
    const node: EventTarget = target === "window" ? window : document;
    const listener = handler as EventListener;
    node.addEventListener(type, listener, options);
    return () => node.removeEventListener(type, listener, options);
  },
};

export const ListenerHubContext = createContext<ListenerHub>(DIRECT_HUB);

export function useListenerHub(): ListenerHub {
  return useContext(ListenerHubContext);
}

/** A window-level listener through the hub, for the simple case of one handler kept current. */
export function useHubListener<E extends Event = Event>(
  target: ListenTarget,
  type: string,
  handler: (event: E) => void,
  options?: { capture?: boolean; passive?: boolean; enabled?: boolean },
): void {
  const hub = useListenerHub();
  const handlerRef = useRef(handler);
  handlerRef.current = handler;
  const capture = options?.capture ?? false;
  const passive = options?.passive;
  const enabled = options?.enabled ?? true;
  useEffect(() => {
    if (!enabled) return;
    const onEvent = (event: E) => handlerRef.current(event);
    return hub.listen<E>(target, type, onEvent, passive === undefined ? capture : { capture, passive });
  }, [hub, target, type, capture, passive, enabled]);
}

// -- scopes the hosted content claims (spec §5.4's matrix) ----------------------------------------

/** A key scope a window's content opens: an open menu or overlay, a check card, or a place that takes
 * typed text without having the DOM focus (the Reader's intent box over a selection). */
export type ClaimedScope = "menu" | "check" | "typing";

export interface ScopeClaims {
  claim(scope: ClaimedScope, owner: string, open: boolean): void;
}

const NO_CLAIMS: ScopeClaims = { claim: () => undefined };

export const ScopeClaimsContext = createContext<ScopeClaims>(NO_CLAIMS);

/** Tell the desk's key router that this content has `scope` open: while it is, the router resolves keys
 * as that scope does (the content's own keys first) before the desk's reading or focus bindings. Outside
 * the desks it does nothing. */
export function useScopeClaim(scope: ClaimedScope, open: boolean): void {
  const claims = useContext(ScopeClaimsContext);
  const owner = useId();
  useEffect(() => {
    claims.claim(scope, owner, open);
    return () => claims.claim(scope, owner, false);
  }, [claims, scope, owner, open]);
}

export function WindowScope({ lifecycle, hub, claims = NO_CLAIMS, children }: { lifecycle: WindowLifecycle; hub: ListenerHub; claims?: ScopeClaims; children: ReactNode }) {
  return (
    <WindowLifecycleContext.Provider value={lifecycle}>
      <ListenerHubContext.Provider value={hub}>
        <ScopeClaimsContext.Provider value={claims}>{children}</ScopeClaimsContext.Provider>
      </ListenerHubContext.Provider>
    </WindowLifecycleContext.Provider>
  );
}
