// The intent box's behaviour (reader workbench RW1b; spec §4.2; UX §4.1, W2, S3, S4).
//
// A learner's selection on the reading surface shows the box about 150 ms after
// mouse-up, UNFOCUSED: scroll keys keep scrolling, Ctrl+C copies, and the first
// printable key focuses it and is typed into it; Enter and Tab work without
// typing; `?` focuses it. While it shows, the Reader's single-key shortcuts are
// off. Typing that pauses for `speculateAfterMs` starts a routing (speculative,
// off with reader_intent.speculative_enabled), so Enter usually finds the
// routing already made; a changed text discards it and Enter routes again. An
// empty Enter asks with no model call. A routed action runs at once, through
// the palette's own handler, and shows as one line with "change", which cancels
// it -- what is still running stops, and a capture it already made is reverted
// (RW1b review F4) -- and opens the palette with the text kept; the pick is the
// learner's correction. Every executed routing reports its use, and every
// speculative routing gets a fate (used or discarded), even one still in
// flight (F12). Tab from the reading surface opens the palette with its first
// action focused, so the arrows and Enter work at once (F8). The box closes on
// Esc or a click elsewhere, recording nothing. Nothing here moves focus on its
// own, animates or opens a modal (W12): focus moves only on the learner's key.
import { useCallback, useEffect, useRef, useState, type RefObject } from "react";
import { api } from "../../api/client";
import type { ReaderIntentActionDto, ReaderIntentContractDto, ReaderIntentRoutingDto } from "../../api/dto";
import { paletteActions, visiblePalette } from "./intentPalette";
import { phaseForError, type ModelActionPhase } from "./ModelActionState";
import { screenLeavesKey } from "../../app/keymap";

/** How long after mouse-up the box appears, so a drag never flickers it. */
export const SHOW_AFTER_MS = 150;
/** One read of a routing in flight waits this long at most (a poll). */
const POLL_WAIT_MS = 250;
const BOX_WIDTH = 360;
const BOX_HEIGHT = 86;

export type IntentRunHow = { entry: "box" | "palette"; routingId?: string | null };

/** What a run made that "change" can undo: a capture's annotation, an import's batch. */
export interface IntentRunHandle {
  annotationId?: string | null;
  importBatchId?: string | null;
}

/** "change" on a routed action: what to cancel or revert. */
export interface IntentCancel {
  action: ReaderIntentActionDto;
  routingId: string | null;
  handle: Promise<IntentRunHandle | null>;
}

export interface IntentBoxPosition {
  top: number;
  left: number;
  above: boolean;
}

/** The fallback when the Decider gives no action: Ask, in the learner's own answer mode. */
export const FALLBACK_ASK: ReaderIntentActionDto = {
  id: "ask", group: "understand", intention: "understand", label: "ask", effect: { kind: "ask" } as ReaderIntentActionDto["effect"], model: true,
};

interface Speculation {
  text: string;
  /** The routing's id once the sidecar answered (null: none was made). */
  started: Promise<string | null>;
  result: Promise<ReaderIntentRoutingDto | null>;
}

export interface UseIntentBoxArgs {
  contract: ReaderIntentContractDto | null;
  extractionId: string | null;
  spanIds: string[];
  quote: string;
  /** Skim mode: the box opens only on `?` or Tab after a selection. */
  muted: boolean;
  protectedSelection: boolean;
  notes: boolean;
  canWorkThrough: boolean;
  hostRef: RefObject<HTMLDivElement | null>;
  /** Run an action; a capture or import resolves to what "change" may undo. */
  onRun: (action: ReaderIntentActionDto, text: string, how: IntentRunHow) => Promise<IntentRunHandle | null> | void;
  /** "change": cancel the routed action -- stop what runs, revert what it made. */
  onCancelRun: (cancel: IntentCancel) => void;
}

function isEditable(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || Boolean(target.closest("input, textarea, select")));
}

export function useIntentBox(args: UseIntentBoxArgs) {
  const { contract, extractionId, spanIds, quote, muted, protectedSelection, notes, canWorkThrough, hostRef, onRun, onCancelRun } = args;
  const enabled = contract !== null && extractionId !== null;
  const [open, setOpen] = useState(false);
  const [armed, setArmed] = useState(false);
  const [position, setPosition] = useState<IntentBoxPosition | null>(null);
  const [text, setTextState] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [phase, setPhase] = useState<ModelActionPhase>("idle");
  const [routed, setRouted] = useState<{ action: ReaderIntentActionDto; routingId: string | null; reason: string | null } | null>(null);
  const [correcting, setCorrecting] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const boxRef = useRef<HTMLDivElement | null>(null);
  const showTimer = useRef<number | null>(null);
  const specTimer = useRef<number | null>(null);
  const speculation = useRef<Speculation | null>(null);
  const lastRun = useRef<Promise<IntentRunHandle | null>>(Promise.resolve(null));
  const focusPalette = useRef(false);
  const epoch = useRef(0);
  const latest = useRef({ extractionId, spanIds, quote, notes });
  latest.current = { extractionId, spanIds, quote, notes };

  const groups = contract ? visiblePalette(contract, { notes, protectedSelection, canWorkThrough }) : [];
  const actionsRef = useRef<ReaderIntentActionDto[]>([]);
  actionsRef.current = paletteActions(groups);

  const clearTimers = useCallback(() => {
    if (showTimer.current !== null) window.clearTimeout(showTimer.current);
    if (specTimer.current !== null) window.clearTimeout(specTimer.current);
    showTimer.current = null;
    specTimer.current = null;
  }, []);

  /** A speculative routing Enter did not take: its fate is discarded, whatever
   *  it routed to and even while it still runs (the sidecar records a fate
   *  asked in flight when the routing lands). */
  const discard = useCallback((spec: Speculation | null) => {
    if (!spec) return;
    void spec.started.then((routingId) => {
      if (routingId) void api.readerIntentOutcome({ routingId, outcome: "discarded" }).catch(() => undefined);
    });
  }, []);
  const discardSpeculation = useCallback(() => {
    const spec = speculation.current;
    speculation.current = null;
    discard(spec);
  }, [discard]);

  const reset = useCallback(() => {
    clearTimers();
    discardSpeculation();
    epoch.current += 1;
    setOpen(false);
    setPaletteOpen(false);
    setTextState("");
    setPhase("idle");
    setRouted(null);
    setCorrecting(null);
  }, [clearTimers, discardSpeculation]);

  const close = useCallback(() => {
    if (correcting) {
      // "change" without a pick: the learner's correction is "none of these".
      void api.readerIntentOutcome({ routingId: correcting, outcome: "corrected", action: null }).catch(() => undefined);
    }
    reset();
    setArmed(false);
  }, [correcting, reset]);

  const place = useCallback(() => {
    const host = hostRef.current;
    if (!host) return setPosition({ top: 0, left: 0, above: false });
    const hostRect = host.getBoundingClientRect();
    let rect: DOMRect | null = null;
    const sel = window.getSelection();
    if (sel && !sel.isCollapsed && sel.rangeCount > 0 && host.contains(sel.anchorNode)) {
      const range = sel.getRangeAt(0);
      rect = typeof range.getBoundingClientRect === "function" ? range.getBoundingClientRect() : null;
    }
    if (!rect || (rect.width === 0 && rect.height === 0)) {
      const last = latest.current.spanIds[latest.current.spanIds.length - 1];
      const element = last
        ? Array.from(host.querySelectorAll<HTMLElement>("[data-span-id]")).find((node) => node.dataset.spanId === last) ?? null
        : null;
      rect = element instanceof HTMLElement ? element.getBoundingClientRect() : null;
    }
    if (!rect) return setPosition({ top: host.scrollTop + 8, left: 8, above: false });
    const above = rect.bottom + BOX_HEIGHT + 8 > hostRect.bottom && rect.top - BOX_HEIGHT - 8 > hostRect.top;
    const top = (above ? rect.top - BOX_HEIGHT - 6 : rect.bottom + 6) - hostRect.top + host.scrollTop;
    const maxLeft = Math.max(8, host.clientWidth - BOX_WIDTH - 8);
    const left = Math.min(Math.max(8, rect.left - hostRect.left + host.scrollLeft), maxLeft);
    setPosition({ top, left, above });
  }, [hostRef]);

  const show = useCallback(() => {
    reset();
    place();
    setOpen(true);
  }, [place, reset]);

  /** The Reader's learner-made selection on the reading surface. */
  const noteSelection = useCallback(() => {
    if (!enabled) return;
    clearTimers();
    reset();
    setArmed(true);
    if (muted) return; // skim: only `?` or Tab opens it
    showTimer.current = window.setTimeout(() => {
      showTimer.current = null;
      show();
    }, SHOW_AFTER_MS);
  }, [enabled, muted, clearTimers, reset, show]);

  const noteSelectionCleared = useCallback(() => {
    reset();
    setArmed(false);
  }, [reset]);

  /** Read a routing until it lands, or until the box's time is up (then null). */
  const settle = useCallback(async (first: ReaderIntentRoutingDto): Promise<ReaderIntentRoutingDto | null> => {
    const deadline = Date.now() + ((contract?.timeoutSeconds ?? 4) + 1) * 1000;
    let current = first;
    while (current.state === "pending" && Date.now() < deadline) {
      current = await api.readerIntentRouting({ routingId: current.routingId, waitMs: POLL_WAIT_MS });
    }
    return current.state === "done" ? current : null;
  }, [contract]);

  const speculate = useCallback((words: string) => {
    const where = latest.current;
    if (!contract?.speculative || !where.extractionId || protectedSelection || !words) return;
    const first = api
      .readerRouteIntent({ extractionId: where.extractionId, spanIds: where.spanIds, text: words, quote: where.quote, speculative: true, notes: where.notes })
      .then((answer) => (answer.status === "not_made" ? null : answer))
      .catch(() => null);
    const started = first.then((answer) => answer?.routingId || null);
    const result = first.then((answer) => (answer ? settle(answer) : null)).catch(() => null);
    speculation.current = { text: words, started, result };
  }, [contract, protectedSelection, settle]);

  const setText = useCallback((value: string) => {
    setTextState(value);
    if (specTimer.current !== null) window.clearTimeout(specTimer.current);
    specTimer.current = null;
    const words = value.trim();
    if (speculation.current && speculation.current.text !== words) discardSpeculation();
    if (!contract?.speculative || !words || speculation.current?.text === words) return;
    specTimer.current = window.setTimeout(() => {
      specTimer.current = null;
      speculate(words);
    }, contract.speculateAfterMs);
  }, [contract, discardSpeculation, speculate]);

  const actionFor = useCallback((routing: ReaderIntentRoutingDto | null): ReaderIntentActionDto => {
    if (!routing || routing.status !== "routed" || !routing.action) return FALLBACK_ASK;
    return actionsRef.current.find((action) => action.id === routing.action) ?? FALLBACK_ASK;
  }, []);

  const submit = useCallback(async () => {
    const words = text.trim();
    if (protectedSelection && words) return; // held out: nothing is sent; the box says so
    if (!words) {
      // An empty Enter asks, with no model call (G3).
      const ask = actionsRef.current.find((action) => action.effect.kind === "ask") ?? FALLBACK_ASK;
      onRun({ ...FALLBACK_ASK, label: ask.label }, "", { entry: "box" });
      reset();
      setArmed(false);
      return;
    }
    if (specTimer.current !== null) window.clearTimeout(specTimer.current);
    specTimer.current = null;
    const mine = ++epoch.current;
    setPhase("pending");
    setPaletteOpen(false);
    let routing: ReaderIntentRoutingDto | null = null;
    try {
      const spec = speculation.current;
      if (spec && spec.text === words) {
        speculation.current = null;
        routing = await spec.result;
        // A speculation that did not land in time is not taken: discarded.
        if (!routing) discard(spec);
      }
      if (!routing) {
        discardSpeculation();
        const where = latest.current;
        const first = await api.readerRouteIntent({
          extractionId: where.extractionId ?? "", spanIds: where.spanIds, text: words, quote: where.quote, speculative: false, notes: where.notes,
        });
        routing = await settle(first);
      }
    } catch (error) {
      if (mine !== epoch.current) return;
      // Model unreachable, the sidecar down: Ask runs, the box says why (W14).
      setPhase(phaseForError(error) === "offline" ? "offline" : "landed");
      routing = null;
    }
    if (mine !== epoch.current) return;
    // Every routing whose action runs reports its use, Enter-only and
    // speculative alike (the report's correction denominator, F12).
    if (routing?.routingId && (routing.status === "routed" || routing.status === "fallback")) {
      void api.readerIntentOutcome({ routingId: routing.routingId, outcome: "used" }).catch(() => undefined);
    }
    const action = actionFor(routing);
    setRouted({ action, routingId: routing?.status === "routed" ? routing.routingId : null, reason: routing?.reason ?? (routing ? null : "unavailable") });
    setPhase("landed");
    lastRun.current = Promise.resolve(onRun(action, words, { entry: "box", routingId: routing?.routingId ?? null }) ?? null).catch(() => null);
  }, [text, protectedSelection, onRun, reset, discard, discardSpeculation, settle, actionFor]);

  const openPalette = useCallback(() => {
    if (!open) show();
    setPaletteOpen(true);
  }, [open, show]);

  // Tab from the reading surface opened the palette: its first action takes
  // focus (the learner's key), so the arrows and Enter act on the palette.
  useEffect(() => {
    if (!paletteOpen || !focusPalette.current) return;
    focusPalette.current = false;
    boxRef.current?.querySelector<HTMLButtonElement>("[data-intent-action]")?.focus({ preventScroll: true });
  }, [paletteOpen, open]);

  /** "change": cancel it (stop or revert); the palette, with the text kept. */
  const change = useCallback(() => {
    if (routed) onCancelRun({ action: routed.action, routingId: routed.routingId, handle: lastRun.current });
    lastRun.current = Promise.resolve(null);
    setCorrecting(routed?.routingId ?? null);
    setRouted(null);
    setPhase("idle");
    setPaletteOpen(true);
  }, [onCancelRun, routed]);

  const pick = useCallback((action: ReaderIntentActionDto) => {
    if (correcting) {
      void api.readerIntentOutcome({ routingId: correcting, outcome: "corrected", action: action.id }).catch(() => undefined);
    }
    const words = text.trim();
    discardSpeculation();
    onRun(action, words, { entry: "palette" });
    setCorrecting(null);
    reset();
    setArmed(false);
  }, [correcting, text, discardSpeculation, onRun, reset]);

  // Keys while the box shows (or, in skim mode, after a selection): printable
  // keys go to the box; Enter, Tab, `?` and Esc are its own; scroll and copy
  // keys are untouched.
  useEffect(() => {
    if (!enabled || !(open || armed)) return;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      const input = inputRef.current;
      const inBox = input !== null && event.target === input;
      // The palette's own buttons: arrows move between them, Enter and Space
      // press them (native), Esc closes the box.
      const onPaletteButton = event.target instanceof HTMLButtonElement && (boxRef.current?.contains(event.target) ?? false);
      if (paletteOpen && (inBox || onPaletteButton) && ["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(event.key)) {
        const buttons = Array.from(boxRef.current?.querySelectorAll<HTMLButtonElement>("[data-intent-action]") ?? []);
        if (buttons.length) {
          event.preventDefault();
          event.stopPropagation();
          const at = onPaletteButton ? buttons.indexOf(event.target as HTMLButtonElement) : -1;
          const step = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : -1;
          buttons[(at + step + buttons.length) % buttons.length].focus({ preventScroll: true });
        }
        return;
      }
      if (onPaletteButton && event.key !== "Escape") return;
      if (!inBox && isEditable(event.target)) return;
      // Only keys meant for the reading surface: a key on a rail button or
      // anywhere else keeps its own meaning.
      const target = event.target;
      const onReading = !(target instanceof Element) || target === document.body
        || (hostRef.current?.contains(target) ?? false);
      if (!inBox && !onReading) return;
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (!open) {
        // Skim mode: only `?` or Tab opens the box on the selection.
        if (event.key === "?" || event.key === "Tab") {
          event.preventDefault();
          event.stopPropagation();
          show();
          if (event.key === "Tab") {
            focusPalette.current = true;
            setPaletteOpen(true);
          } else window.requestAnimationFrame(() => inputRef.current?.focus({ preventScroll: true }));
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        if (paletteOpen && !inBox && correcting === null) {
          setPaletteOpen(false);
          return;
        }
        close();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        event.stopPropagation();
        void submit();
        return;
      }
      if (event.key === "Tab") {
        event.preventDefault();
        event.stopPropagation();
        // From the reading surface (focus not in the box), the palette's
        // first action takes focus so arrows and Enter choose (F8).
        if (!paletteOpen && !inBox) focusPalette.current = true;
        setPaletteOpen((value) => !value);
        return;
      }
      if (inBox) return;
      if (event.key === "?") {
        event.preventDefault();
        event.stopPropagation();
        input?.focus({ preventScroll: true });
        return;
      }
      if (event.key.length === 1 && event.key !== " ") {
        // The first printable key focuses the box and is typed into it.
        event.preventDefault();
        event.stopPropagation();
        setText(text + event.key);
        input?.focus({ preventScroll: true });
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [enabled, open, armed, paletteOpen, correcting, text, show, close, submit, setText, hostRef]);

  // A click elsewhere closes it, recording nothing.
  useEffect(() => {
    if (!open) return;
    const onDown = (event: MouseEvent) => {
      if (boxRef.current && event.target instanceof Node && boxRef.current.contains(event.target)) return;
      close();
    };
    document.addEventListener("mousedown", onDown, true);
    return () => document.removeEventListener("mousedown", onDown, true);
  }, [open, close]);

  useEffect(() => () => clearTimers(), [clearTimers]);
  // Another book: nothing carries over.
  useEffect(() => {
    reset();
    setArmed(false);
  }, [extractionId, reset]);

  return {
    enabled, open: enabled && open, position, text, setText, inputRef, boxRef, groups, paletteOpen, setPaletteOpen,
    phase, routed, correcting: correcting !== null, protectedSelection,
    noteSelection, noteSelectionCleared, submit, pick, change, close, openPalette,
  };
}

export type IntentBoxController = ReturnType<typeof useIntentBox>;
