// The Reader workbench's desks (spec §3.1, §5): the top bar's desk tabs, the stage of windows in
// slots, the shelf, the footer, and the single key router for the workbench.
//
// The workspace model (model/workspace.ts) is the truth on screen; every change the learner makes is
// applied there at once and queued as `desk.apply` ops in the outbox (outbox.ts), which sends them in
// order. A conflict takes the server's state: the shell reads `desk.state` again.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "../../api/client";
import { cachedSourceRead } from "../reader/readerCache";
import { poller } from "../../api/poller";
import type { ContentRefDto, DeskApplyDto, DeskApplyInput, DeskStateDto, SourceLibraryCard } from "../../api/dto";
import {
  EMPTY_WORKSPACE,
  closeWindow,
  createDesk,
  deskById,
  focusAlong,
  focusPane,
  focusedSlot,
  focusedWindowId,
  fromDeskState,
  moveFocused,
  moveWindowTo,
  openBeside,
  pairFocused,
  renameDesk,
  setFocus,
  setView,
  slotIndexOf,
  swapInView,
  undoClose,
  unpairFocused,
  type DeskWindow,
  type Step,
  type Workspace,
} from "./model/workspace";
import {
  DESK_SIZES,
  FOCUS_MEASURE,
  ensureVisible,
  paneRects,
  rowTop,
  sliverSlots,
  slotRects,
  slotVisibility,
  softCropMask,
  stepZoom,
  type Stage,
} from "./geometry";
import {
  BareAltTracker,
  DESK_BINDINGS,
  ModifierTracker,
  REAL_TIMERS,
  isTypingTarget,
  resolveKey,
  type DeskAction,
  type Timers,
} from "./keys/router";
import { DeskListenerRouter, WINDOW_ATTRIBUTE } from "./keys/listeners";
import { WindowScope, isPaused, windowState, type ListenerHub, type WindowLifecycle } from "./lifecycle";
import { DeskOutbox, clientIdFor, type OutboxTransport } from "./outbox";
import { Shelf, type ShelfRow } from "./Shelf";
import { SourceWindow, type ReaderPassThrough, type SourceStatus } from "./windows/SourceWindow";
import { LibraryPanel, PANEL_TITLES, PathPanel, RailHostPanel } from "./windows/PanelWindow";
import { ScreenErrorBoundary } from "../../app/ScreenErrorBoundary";
import "../../styles/desk.css";

export interface DeskTransport extends OutboxTransport {
  state(): Promise<DeskStateDto>;
  library(): Promise<SourceLibraryCard[]>;
  /** A source's current reading, which a window names (its content reference carries both). */
  resolveExtraction(sourceId: string): Promise<string>;
}

export const LIVE_DESK_TRANSPORT: DeskTransport = {
  state: () => api.deskState(),
  apply: (input: DeskApplyInput): Promise<DeskApplyDto> => api.deskApply(input),
  library: async () => (await api.getSourceLibrary()).sources,
  // The Reader's own cached read: the window that opens next reads it from the cache.
  resolveExtraction: async (sourceId) => (await cachedSourceRead(sourceId, ["reader_render_view", sourceId], () =>
    api.readerRenderView({ extractionId: sourceId }))).extractionId,
};

/** What a pane needs to render its content; tests and the harness may render panes their own way. */
export interface PaneRenderInput {
  window: DeskWindow;
  lifecycle: WindowLifecycle;
  card: SourceLibraryCard | null;
}

/** Undo close stays on the shelf this long (spec §5.2). */
const UNDO_CLOSE_MS = 9_000;
/** A toast stays 2.2 s (spec §4.3). */
const TOAST_MS = 2_200;
/** Ops are sent shortly after the last change, so a burst of moves is one batch. */
const FLUSH_IDLE_MS = 250;
/** A window's reading place is saved once the learner settles on it. */
const VIEW_SAVE_IDLE_MS = 2_000;

export const KIND_GLYPH: Record<string, string> = {
  source: "§",
  video: "▶",
  pad: "›",
  pad_stack: "›",
  lesson: "◇",
  thread: "?",
  compare: "⇄",
  panel: "◇",
  figure_notebook: "◇",
};

const KIND_WORD: Record<string, string> = {
  source: "book",
  video: "video",
  pad: "notes",
  pad_stack: "notes",
  lesson: "lesson",
  thread: "thread",
  compare: "compare",
  panel: "panel",
  figure_notebook: "figure",
};

function defaultMintId(prefix: string): string {
  try {
    return `${prefix}_${crypto.randomUUID()}`;
  } catch {
    return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
  }
}

function shortName(title: string): string {
  const words = title.split(/\s+/).filter(Boolean);
  return words.slice(0, 3).join(" ");
}

function readStored(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* a per-machine convenience */
  }
}

export interface DeskShellProps {
  vaultKey: string;
  onError: (message: string) => void;
  /** Back to the old Reader (it stays reachable until the parity matrix passes, spec §21.1). */
  onLeave?: () => void;
  /** First run: the book the learner read last, for the first desk (spec §5.1). */
  firstSourceId?: string | null;
  transport?: DeskTransport;
  reader?: ReaderPassThrough;
  /** Renders a pane's content; absent, the real windows (source, video, panels). */
  renderPane?: (input: PaneRenderInput) => ReactNode;
  /** The viewport before it is measured (tests; jsdom lays nothing out). */
  initialViewport?: Stage;
  mintId?: (prefix: string) => string;
  timers?: Timers;
}

export function DeskShell({
  vaultKey,
  onError,
  onLeave,
  firstSourceId = null,
  transport = LIVE_DESK_TRANSPORT,
  reader,
  renderPane,
  initialViewport,
  mintId = defaultMintId,
  timers = REAL_TIMERS,
}: DeskShellProps) {
  const [ws, setWs] = useState<Workspace | null>(null);
  const wsRef = useRef<Workspace>(EMPTY_WORKSPACE);
  const [library, setLibrary] = useState<SourceLibraryCard[] | null>(null);
  const deskKey = `learnloop.desks.current.${vaultKey}`;
  const [currentDeskId, setCurrentDeskIdState] = useState<string | null>(() => readStored(deskKey));
  const [camX, setCamX] = useState<Record<string, number>>({});
  const [visited, setVisited] = useState<Set<string>>(() => new Set());
  const [focusMode, setFocusMode] = useState(false);
  const [whichKey, setWhichKey] = useState(false);
  const [toast, setToast] = useState<{ text: string; key: number } | null>(null);
  const [undo, setUndo] = useState<{ deskId: string; title: string; until: number } | null>(null);
  const [status, setStatus] = useState<Record<string, SourceStatus>>({});
  const [entering, setEntering] = useState<Set<string>>(() => new Set());
  const [renaming, setRenaming] = useState<string | null>(null);
  const [opener, setOpener] = useState(false);
  const [badge, setBadge] = useState<number | null>(null);
  const [railHosts, setRailHosts] = useState<Record<string, HTMLElement | null>>({});
  const [railClaims, setRailClaims] = useState<Record<string, string>>({});
  const stageRef = useRef<HTMLElement | null>(null);
  const [stage, setStage] = useState<Stage>(() => {
    const viewport = initialViewport ?? { width: window.innerWidth, height: window.innerHeight };
    const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf;
    return { width: viewport.width - shelf, height: viewport.height - DESK_SIZES.topBar - DESK_SIZES.footer };
  });
  const [viewportWidth, setViewportWidth] = useState(() => (initialViewport ?? { width: window.innerWidth }).width);
  const jumps = useRef(new Map<string, (spanId: string) => void>());
  const media = useRef(new Map<string, () => void>());
  const pendingJump = useRef(new Map<string, string>());

  const outbox = useMemo(
    () => new DeskOutbox(clientIdFor(vaultKey, typeof window === "undefined" ? null : window.localStorage, () => mintId("client")), transport),
    [vaultKey, transport, mintId],
  );

  const toastNow = useCallback((text: string) => setToast({ text, key: Date.now() }), []);
  useEffect(() => {
    if (!toast) return;
    const handle = timers.set(() => setToast(null), TOAST_MS);
    return () => timers.clear(handle);
  }, [toast, timers]);

  // -- loading and persisting ----------------------------------------------------------------------

  const setCurrentDeskId = useCallback((deskId: string | null) => {
    setCurrentDeskIdState(deskId);
    if (deskId) writeStored(deskKey, deskId);
  }, [deskKey]);

  const flushTimer = useRef<unknown>(null);
  const reloadRef = useRef<() => Promise<void>>(async () => undefined);
  const scheduleFlush = useCallback(() => {
    if (flushTimer.current !== null) timers.clear(flushTimer.current);
    flushTimer.current = timers.set(() => {
      flushTimer.current = null;
      void outbox.flush().then((outcome) => {
        if (outcome.kind === "conflict" || outcome.kind === "resync") void reloadRef.current();
        else if (outcome.kind === "offline") toastNow("couldn't save the desk just now · it is kept here until it can be");
      });
    }, FLUSH_IDLE_MS);
  }, [outbox, timers, toastNow]);

  const commit = useCallback((step: Step) => {
    wsRef.current = step.ws;
    setWs(step.ws);
    if (step.notice) toastNow(step.notice);
    if (step.ops.length > 0) {
      outbox.enqueue(step.ops);
      scheduleFlush();
    }
  }, [outbox, scheduleFlush, toastNow]);

  const chain = useCallback((first: Step, next: (ws: Workspace) => Step): Step => {
    const second = next(first.ws);
    return { ws: second.ws, ops: [...first.ops, ...second.ops], notice: second.notice ?? first.notice };
  }, []);

  const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step> => {
    const card = firstSourceId ? cards?.find((entry) => entry.sourceId === firstSourceId) ?? null : null;
    const deskId = mintId("desk");
    const created = createDesk(base, deskId, card ? `new desk · ${shortName(card.title)}` : "new desk");
    if (!card || card.readiness !== "ready") return created;
    const extractionId = await transport.resolveExtraction(card.sourceId).catch(() => null);
    if (!extractionId) return created;
    return chain(created, (next) => openBeside(next, deskId, contentForCard(card, extractionId), () => mintId("win")));
  }, [chain, firstSourceId, mintId, transport]);

  const load = useCallback(async () => {
    try {
      const [state, cards] = await Promise.all([transport.state(), transport.library().catch(() => null)]);
      setLibrary(cards);
      outbox.syncSeq(state);
      const loaded = fromDeskState(state);
      if (loaded.desks.length === 0) {
        commit(await firstRun(loaded, cards));
      } else {
        // Keep the closed windows this session can still undo.
        commit({ ws: { ...loaded, closed: wsRef.current.closed }, ops: [] });
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : typeof error === "object" && error && "message" in error ? String((error as { message: unknown }).message) : String(error));
    }
  }, [transport, outbox, commit, firstRun, onError]);
  reloadRef.current = load;

  useEffect(() => {
    void load();
    // Loaded once per vault; a conflict reloads through reloadRef.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vaultKey]);

  // -- the current desk, focus and camera ------------------------------------------------------------

  const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null;
  const deskId = desk?.deskId ?? null;
  const focusId = ws && desk ? focusedWindowId(ws, desk) : null;
  const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1;
  useEffect(() => {
    if (deskId && deskId !== currentDeskId) setCurrentDeskId(deskId);
  }, [deskId, currentDeskId, setCurrentDeskId]);
  useEffect(() => {
    if (deskId) setVisited((seen) => (seen.has(deskId) ? seen : new Set([...seen, deskId])));
  }, [deskId]);

  const slotCount = desk?.slots.length ?? 0;
  const keepPrevious = useRef(false);
  useLayoutEffect(() => {
    if (!deskId) return;
    setCamX((cams) => {
      const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current);
      keepPrevious.current = false;
      return cams[deskId] === next ? cams : { ...cams, [deskId]: next };
    });
  }, [deskId, focusSlotIndex, slotCount, stage]);

  // The stage's size: the window's, less the chrome (or all of it, in focus mode).
  useEffect(() => {
    const node = stageRef.current;
    const measure = () => {
      if (node && node.clientWidth > 0 && node.clientHeight > 0) setStage({ width: node.clientWidth, height: node.clientHeight });
      // The shelf folds by the desks' own width (the Reader place), not the window's.
      const shell = node?.closest(".desk-shell") as HTMLElement | null;
      if (shell && shell.clientWidth > 0) setViewportWidth(shell.clientWidth);
    };
    measure();
    const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure);
    if (observer && node) observer.observe(node);
    window.addEventListener("resize", measure);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [ws === null]);

  const cam = deskId ? camX[deskId] ?? 0 : 0;
  const visibility = useMemo(() => slotVisibility(cam, slotCount, stage), [cam, slotCount, stage]);
  const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0;

  // -- the lifecycle of every window ---------------------------------------------------------------

  const lifecycles = useMemo(() => {
    const out: Record<string, WindowLifecycle> = {};
    if (!ws) return out;
    for (const each of ws.desks) {
      const onCurrent = each.deskId === deskId;
      each.slots.forEach((slot, index) => {
        for (const id of slot) {
          out[id] = {
            windowId: id,
            state: windowState({ onCurrentDesk: onCurrent, inView: onCurrent && Boolean(visibility[index]?.inView), focused: onCurrent && id === focusId, focusMode }),
          };
        }
      });
    }
    return out;
  }, [ws, deskId, visibility, focusId, focusMode]);
  const lifecyclesRef = useRef(lifecycles);
  lifecyclesRef.current = lifecycles;
  const focusIdRef = useRef(focusId);
  focusIdRef.current = focusId;
  useEffect(() => {
    for (const [id, lifecycle] of Object.entries(lifecycles)) poller.setOwnerPaused(id, isPaused(lifecycle.state));
  }, [lifecycles]);

  // -- actions -------------------------------------------------------------------------------------

  const focusModeRef = useRef(focusMode);
  focusModeRef.current = focusMode;

  const switchDesk = useCallback((direction: -1 | 1): boolean => {
    const current = wsRef.current;
    const index = current.desks.findIndex((each) => each.deskId === deskIdRef.current);
    const next = current.desks[index + direction];
    if (!next) return false;
    setCurrentDeskId(next.deskId);
    return true;
  }, [setCurrentDeskId]);
  const deskIdRef = useRef(deskId);
  deskIdRef.current = deskId;

  const titleOf = useCallback((window: DeskWindow | undefined): string => {
    if (!window) return "";
    const known = status[window.windowId]?.title;
    if (known) return known;
    const content = window.content;
    if (!content) return "notes";
    if (content.kind === "source" || content.kind === "video") return library?.find((card) => card.sourceId === content.sourceId)?.title ?? "source";
    if (content.kind === "panel") return PANEL_TITLES[content.panel];
    if (content.kind === "compare") return content.query ? `compare · ${content.query}` : "compare";
    return KIND_WORD[content.kind] ?? content.kind;
  }, [status, library]);

  const run = useCallback((action: DeskAction): boolean => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    if (!id) return false;
    const focus = focusIdRef.current;
    switch (action.kind) {
      case "focusAlong":
        commit(focusAlong(current, id, action.direction));
        return true;
      case "paneOrDesk": {
        const step = focusPane(current, id, action.direction);
        if (step) commit(step);
        else switchDesk(action.direction);
        return true;
      }
      case "moveWindow":
        commit(moveFocused(current, id, action.direction));
        return true;
      case "pair":
        commit(pairFocused(current, id));
        return true;
      case "unpair":
        commit(unpairFocused(current, id));
        return true;
      case "closeWindow": {
        if (!focus) return true;
        const title = titleOf(current.windows[focus]);
        commit(closeWindow(current, id, focus));
        setUndo({ deskId: id, title, until: timers.now() + UNDO_CLOSE_MS });
        return true;
      }
      case "toggleFocusMode":
        if (!focus) return true;
        setFocusMode((on) => !on);
        setBadge(timers.now());
        return true;
      case "leaveFocusMode":
        setFocusMode(false);
        return true;
      case "docZoom": {
        if (!focus) return true;
        const window = current.windows[focus];
        const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1;
        const next = stepZoom(zoom, action.direction);
        commit(setView(current, id, focus, { ...(window?.view ?? {}), zoom: next }));
        setBadge(timers.now());
        return true;
      }
      case "swap": {
        const desk = deskById(current, id);
        if (!desk || !focus) return true;
        const index = slotIndexOf(desk, focus);
        const shown = visibilityRef.current.filter((slot) => slot.inView).map((slot) => slot.index);
        const other = shown.find((slot) => slot !== index);
        if (other !== undefined) commit(swapInView(current, id, other));
        return true;
      }
      case "playPause": {
        const toggle = focus ? media.current.get(focus) : undefined;
        if (!toggle) return false;
        toggle();
        return true;
      }
      default:
        return false;
    }
  }, [commit, switchDesk, timers, titleOf]);
  const visibilityRef = useRef(visibility);
  visibilityRef.current = visibility;
  const runRef = useRef(run);
  runRef.current = run;

  // -- the key router: one capture listener, the matrix, the bare-Alt rule --------------------------

  const modifiers = useMemo(() => new ModifierTracker(), []);
  const altTracker = useMemo(
    () => new BareAltTracker(timers, () => setWhichKey(true), () => setWhichKey(false)),
    [timers],
  );
  const router = useMemo(() => new DeskListenerRouter({
    activeWindowId: () => focusIdRef.current,
    isPaused: (windowId) => isPaused(lifecyclesRef.current[windowId]?.state ?? "hidden"),
    onPointerWindow: (windowId) => {
      const current = wsRef.current;
      const id = deskIdRef.current;
      if (!id || focusIdRef.current === windowId) return;
      const owner = current.windows[windowId];
      if (!owner || owner.deskId !== id) return;
      focusIdRef.current = windowId;
      commit(setFocus(current, id, windowId));
    },
    intercept: (type, phase, event) => {
      if (phase !== "capture") return false;
      if (type === "blur") {
        modifiers.blur();
        altTracker.cancel();
        altTracker.reset();
        return false;
      }
      if (type === "mousedown") {
        altTracker.cancel();
        return false;
      }
      if (!(event instanceof KeyboardEvent)) return false;
      if (type === "keyup") {
        modifiers.keyup(event);
        // Alt held long enough to show which-key: its release belongs to the panel, never to a window's
        // capture-clearing tap.
        return altTracker.release(event) === "hold";
      }
      if (type !== "keydown") return false;
      modifiers.keydown(event);
      altTracker.keydown(event);
      if (event.key === "Alt" || event.key === "Control" || event.key === "Shift" || event.key === "Meta") return false;
      const resolution = resolveKey(event, { typing: isTypingTarget(event.target), focus: focusModeRef.current }, modifiers.read(event));
      if (!resolution || resolution.binding.later) return false;
      if (!runRef.current(resolution.binding.action)) return false;
      event.preventDefault();
      event.stopPropagation();
      return true;
    },
  }), [modifiers, altTracker, commit]);
  useEffect(() => {
    router.ensure("window", "keydown");
    router.ensure("window", "keyup");
    router.ensure("window", "mousedown");
    router.ensure("window", "blur");
    return () => router.dispose();
  }, [router]);
  const hubs = useRef(new Map<string, ListenerHub>());
  const hubFor = useCallback((windowId: string): ListenerHub => {
    let hub = hubs.current.get(windowId);
    if (!hub) {
      hub = router.hubFor(windowId);
      hubs.current.set(windowId, hub);
    }
    return hub;
  }, [router]);

  // -- opening windows -------------------------------------------------------------------------------

  const openContent = useCallback((content: ContentRefDto, options: { spanId?: string | null } = {}) => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    if (!id) return;
    const step = openBeside(current, id, content, () => mintId("win"), {
      spanId: options.spanId ?? null,
      view: options.spanId ? { spanId: options.spanId } : {},
    });
    keepPrevious.current = !step.existed;
    commit(step);
    if (step.existed && options.spanId) {
      const jump = jumps.current.get(step.windowId);
      if (jump) jump(options.spanId);
      else pendingJump.current.set(step.windowId, options.spanId);
    }
    if (!step.existed) {
      setEntering((now) => new Set([...now, step.windowId]));
      timers.set(() => setEntering((now) => {
        const next = new Set(now);
        next.delete(step.windowId);
        return next;
      }), 450);
    }
    setOpener(false);
  }, [commit, mintId, timers]);

  const openHit = useCallback((hit: { sourceId: string | null; extractionId: string; spanId: string }) => {
    if (!hit.sourceId) return;
    const card = library?.find((entry) => entry.sourceId === hit.sourceId);
    const kind = card && isVideoCard(card) ? "video" : "source";
    openContent({ kind, sourceId: hit.sourceId, extractionId: hit.extractionId } as ContentRefDto, { spanId: hit.spanId });
  }, [library, openContent]);

  // -- window status from inside (title, reading place, rail hosts, media) ------------------------

  const viewTimers = useRef(new Map<string, unknown>());
  const statusFor = useMemo(() => new Map<string, (next: SourceStatus) => void>(), []);
  const onStatusFor = useCallback((windowId: string) => {
    let handler = statusFor.get(windowId);
    if (!handler) {
      handler = (next: SourceStatus) => {
        setStatus((all) => ({ ...all, [windowId]: { ...all[windowId], ...next } }));
        // The reading place, saved as the window's scroll anchor by passage once the learner settles
        // (spec §3.5: span-based, never pixels), and only for the window the learner is reading.
        if (next.readingSpan && focusIdRef.current === windowId) {
          const previous = viewTimers.current.get(windowId);
          if (previous !== undefined) timers.clear(previous);
          viewTimers.current.set(windowId, timers.set(() => {
            viewTimers.current.delete(windowId);
            const current = wsRef.current;
            const window = current.windows[windowId];
            if (!window || window.view?.spanId === next.readingSpan) return;
            commit(setView(current, window.deskId, windowId, { ...window.view, spanId: next.readingSpan }));
          }, VIEW_SAVE_IDLE_MS));
        }
      };
      statusFor.set(windowId, handler);
    }
    return handler;
  }, [statusFor, timers, commit]);

  const jumpReadyFor = useMemo(() => new Map<string, (jump: ((spanId: string) => void) | null) => void>(), []);
  const onJumpReadyFor = useCallback((windowId: string) => {
    let handler = jumpReadyFor.get(windowId);
    if (!handler) {
      handler = (jump) => {
        if (!jump) {
          jumps.current.delete(windowId);
          return;
        }
        jumps.current.set(windowId, jump);
        const pending = pendingJump.current.get(windowId);
        if (pending) {
          pendingJump.current.delete(windowId);
          jump(pending);
        }
      };
      jumpReadyFor.set(windowId, handler);
    }
    return handler;
  }, [jumpReadyFor]);

  const mediaReadyFor = useMemo(() => new Map<string, (toggle: (() => void) | null) => void>(), []);
  const onMediaReadyFor = useCallback((windowId: string) => {
    let handler = mediaReadyFor.get(windowId);
    if (!handler) {
      handler = (toggle) => {
        if (toggle) media.current.set(windowId, toggle);
        else media.current.delete(windowId);
      };
      mediaReadyFor.set(windowId, handler);
    }
    return handler;
  }, [mediaReadyFor]);

  const railNodeFor = useMemo(() => new Map<string, (node: HTMLElement | null) => void>(), []);
  const onRailNode = useCallback((windowId: string) => {
    let handler = railNodeFor.get(windowId);
    if (!handler) {
      handler = (node) => setRailHosts((hosts) => (hosts[windowId] === node ? hosts : { ...hosts, [windowId]: node }));
      railNodeFor.set(windowId, handler);
    }
    return handler;
  }, [railNodeFor]);

  /** Per desk and book, the panel window that shows the book's rail: the claimed one, else the first. */
  const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null => {
    if (!ws) return null;
    const desk = deskById(ws, deskOf);
    if (!desk) return null;
    const panels = desk.slots.flat().filter((id) => {
      const content = ws.windows[id]?.content;
      return content?.kind === "panel" && (content.panel === "guide" || content.panel === "notes") && content.extractionId === extractionId;
    });
    const claimed = railClaims[`${deskOf}:${extractionId}`];
    return claimed && panels.includes(claimed) ? claimed : panels[0] ?? null;
  }, [ws, railClaims]);

  const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null => {
    if (!ws) return null;
    const desk = deskById(ws, deskOf);
    if (!desk) return null;
    return desk.slots.flat().find((id) => {
      const content = ws.windows[id]?.content;
      return (content?.kind === "source" || content?.kind === "video") && content.extractionId === extractionId;
    }) ?? null;
  }, [ws]);

  // -- rendering ------------------------------------------------------------------------------------

  const undoShown = undo && undo.deskId === deskId && undo.until > timers.now() ? undo : null;
  useEffect(() => {
    if (!undo) return;
    const handle = timers.set(() => setUndo(null), Math.max(0, undo.until - timers.now()));
    return () => timers.clear(handle);
  }, [undo, timers]);

  if (!ws) {
    return (
      <div className="desk-shell" data-desk-shell="">
        <header className="desk-top"><span className="desk-brand">◇ LearnLoop</span></header>
        <main className="desk-main"><aside className="desk-shelf" /><section className="desk-stage" ref={stageRef} /></main>
        <footer className="desk-keys"><span className="note">◐ opening your desks…</span></footer>
      </div>
    );
  }

  const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode => {
    const content = window.content;
    const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry) => entry.sourceId === content.sourceId) ?? null : null;
    if (renderPane) return renderPane({ window, lifecycle, card });
    if (!content) return <div className="desk-panel desk-quiet">Scratchpads open here once they are built (they are stored, and kept).</div>;
    switch (content.kind) {
      case "source":
      case "video": {
        const railPanel = railPanelOf(window.deskId, content.extractionId);
        const railNode = railPanel ? railHosts[railPanel] ?? null : null;
        const railContent = railPanel ? ws.windows[railPanel]?.content : null;
        const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide";
        return (
          <SourceWindow
            content={content}
            card={card}
            libraryLoaded={library !== null}
            startSpan={typeof window.view?.spanId === "string" ? (window.view.spanId as string) : null}
            railHost={railNode ? { node: railNode, tab: railTab } : null}
            onStatus={onStatusFor(window.windowId)}
            onJumpReady={onJumpReadyFor(window.windowId)}
            onMediaReady={onMediaReadyFor(window.windowId)}
            onError={onError}
            reader={reader}
          />
        );
      }
      case "panel": {
        if (content.panel === "guide" || content.panel === "notes") {
          const extractionId = content.extractionId ?? "";
          const owner = railPanelOf(window.deskId, extractionId);
          return (
            <RailHostPanel
              panel={content.panel}
              bound={Boolean(extractionId && sourceWindowOf(window.deskId, extractionId))}
              claimed={owner !== null && owner !== window.windowId}
              onNode={onRailNode(window.windowId)}
              onClaim={() => setRailClaims((claims) => ({ ...claims, [`${window.deskId}:${extractionId}`]: window.windowId }))}
            />
          );
        }
        if (content.panel === "path") {
          return (
            <PathPanel
              extractionId={content.extractionId ?? null}
              onError={onError}
              onJump={(spanId) => {
                const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null;
                if (!target) return;
                commit(setFocus(wsRef.current, window.deskId, target));
                const jump = jumps.current.get(target);
                if (jump) jump(spanId);
              }}
            />
          );
        }
        return <LibraryPanel query={null} onOpenHit={openHit} onClose={() => run({ kind: "closeWindow" })} onError={onError} />;
      }
      case "compare":
        return <LibraryPanel query={content.query ?? null} onOpenHit={openHit} onClose={() => run({ kind: "closeWindow" })} onError={onError} />;
      default:
        return <div className="desk-panel desk-quiet">This window opens here once its kind is built.</div>;
    }
  };

  const focusWindow = focusId ? ws.windows[focusId] : undefined;
  const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1;
  const slivers = desk && !focusMode ? sliverSlots(cam, slotCount, stage) : { left: null, right: null };
  const shelfRows: ShelfRow[] = desk
    ? desk.slots.flatMap((slot, index) => slot.map((id) => {
      const window = ws.windows[id];
      const kind = window?.kind ?? "source";
      return {
        windowId: id,
        slot: index,
        glyph: KIND_GLYPH[kind] ?? "§",
        kind: KIND_WORD[kind] ?? kind,
        title: titleOf(window),
        state: id === focusId ? "focus" as const : visibility[index]?.inView ? "in view" as const : null,
        progress: typeof status[id]?.progress === "number" ? status[id].progress as number : null,
        where: status[id]?.where ?? null,
      };
    }))
    : [];

  const hints = focusMode
    ? [["alt+↵ / esc", "leave focus"], ["= − 0", "zoom"], ["alt+h/l", "next window"]]
    : [["alt+h/l", "window"], ["alt+j/k", "pane · desk"], ["alt+[ ]", "move"], ["alt+, .", "share · own slot"], ["alt+↵", "focus"], ["alt+w", "close"]];

  return (
    <div className={`desk-shell${focusMode ? " focus-mode" : ""}`} data-desk-shell="" data-focus-mode={focusMode ? "on" : "off"}>
      <header className="desk-top">
        <span className="desk-brand">◇ LearnLoop</span>
        <nav className="desk-tabs" aria-label="desks">
          {ws.desks.map((each) => (
            renaming === each.deskId ? (
              <input
                key={each.deskId}
                aria-label="desk name"
                defaultValue={each.title}
                autoFocus
                onBlur={() => setRenaming(null)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    const title = (event.target as HTMLInputElement).value.trim();
                    if (title && title !== each.title) commit(renameDesk(wsRef.current, each.deskId, title));
                    setRenaming(null);
                  } else if (event.key === "Escape") {
                    setRenaming(null);
                  }
                }}
              />
            ) : (
              <button
                key={each.deskId}
                type="button"
                aria-current={each.deskId === deskId ? "true" : "false"}
                title="double-click to rename"
                onClick={() => setCurrentDeskId(each.deskId)}
                onDoubleClick={() => setRenaming(each.deskId)}
              >
                {each.title}
              </button>
            )
          ))}
          <button
            type="button"
            aria-label="new desk"
            title="a new desk"
            onClick={() => {
              const id = mintId("desk");
              commit(createDesk(wsRef.current, id, "new desk"));
              setCurrentDeskId(id);
            }}
          >
            +
          </button>
        </nav>
        <span className="grow" />
        <button type="button" className="tb" aria-expanded={opener} onClick={() => setOpener((open) => !open)}>+ open beside</button>
        {onLeave ? <button type="button" className="tb" onClick={onLeave}>old Reader</button> : null}
      </header>
      <main className={`desk-main${viewportWidth < DESK_SIZES.shelfFoldBelow ? " rail" : ""}`}>
        <Shelf
          rows={shelfRows}
          folded={viewportWidth < DESK_SIZES.shelfFoldBelow}
          undo={undoShown ? { title: undoShown.title, onUndo: () => { commit(undoClose(wsRef.current, undoShown.deskId)); setUndo(null); } } : null}
          onFocus={(id) => deskId && commit(setFocus(wsRef.current, deskId, id))}
          onReorder={(id, toSlot) => {
            if (!deskId) return;
            commit(moveWindowTo(wsRef.current, deskId, id, toSlot));
          }}
        />
        <section className="desk-stage" ref={stageRef} data-desk-stage="">
          {ws.desks.map((each, rowIndex) => {
            if (!visited.has(each.deskId) && each.deskId !== deskId) return null;
            const onCurrent = each.deskId === deskId;
            const eachCam = camX[each.deskId] ?? 0;
            const rects = slotRects(each.slots.length, stage);
            const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage);
            const eachVisibility = onCurrent ? visibility : slotVisibility(eachCam, each.slots.length, stage);
            return each.slots.map((slot, index) => {
              const rect = rects[index];
              const full = onCurrent && focusMode && slot.includes(focusId ?? "");
              const left = full ? 0 : rect.x - eachCam;
              const style = full
                ? { left: 0, top: 0, width: stage.width, height: stage.height }
                : { left, top: top + rect.y, width: rect.w, height: rect.h };
              const mask = !full && onCurrent && !focusMode ? softCropMask(eachVisibility[index], rect.w) : null;
              const slotPaused = slot.every((id) => isPaused(lifecycles[id]?.state ?? "hidden"));
              const panes = full ? slot.filter((id) => id === focusId) : slot;
              return (
                <div
                  key={slot.join("+")}
                  data-desk-slot={`${each.deskId}:${index}`}
                  className={`desk-window${onCurrent && slot.includes(focusId ?? "") ? " focus" : ""}${full ? " focused-full" : ""}${slotPaused ? " paused" : ""}${slot.some((id) => entering.has(id)) ? " entering" : ""}`}
                  style={{
                    ...style,
                    ...(mask ? { WebkitMaskImage: mask, maskImage: mask } : {}),
                    ...(onCurrent && focusMode && !full ? { visibility: "hidden" as const } : {}),
                  }}
                >
                  {panes.map((id, pane) => {
                    const window = ws.windows[id];
                    if (!window) return null;
                    const lifecycle = lifecycles[id] ?? { windowId: id, state: "hidden" as const };
                    const paired = panes.length > 1;
                    const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source;
                    return (
                      <div
                        key={id}
                        {...{ [WINDOW_ATTRIBUTE]: id }}
                        data-window-state={lifecycle.state}
                        data-window-kind={window.kind}
                        className={`desk-pane${paired && window.active ? " active-pane" : ""}`}
                        style={paired ? { flex: `0 0 ${paneRects({ x: 0, y: 0, w: rect.w, h: style.height as number }, 2)[pane].h}px` } : undefined}
                      >
                        <div className="desk-pane-head">
                          <span className="g">{KIND_GLYPH[window.kind] ?? "§"}</span>
                          <span className="t">{titleOf(window)}</span>
                          {status[id]?.where ? <span className="loc">{status[id]?.where}</span> : null}
                          {paired ? <span className="hint">{window.active ? "alt+. gives it its own slot" : "click or alt+j/k"}</span> : null}
                          <button
                            type="button"
                            className="x"
                            aria-label={`close ${titleOf(window)}`}
                            title="close (alt+w)"
                            style={paired ? undefined : { marginLeft: "auto" }}
                            onClick={(event) => {
                              event.stopPropagation();
                              const title = titleOf(window);
                              commit(closeWindow(wsRef.current, each.deskId, id));
                              setUndo({ deskId: each.deskId, title, until: timers.now() + UNDO_CLOSE_MS });
                            }}
                          >
                            ✕
                          </button>
                        </div>
                        <div className="desk-pane-body" data-desk-pane-body="">
                          {/* A window that fails to render fails alone: the desk and its other windows stay. */}
                          <ScreenErrorBoundary resetKey={id}>
                          <WindowScope lifecycle={lifecycle} hub={hubFor(id)}>
                            {full ? (
                              <div
                                className="desk-measure"
                                style={{ ["--desk-measure" as string]: `${measure}px`, zoom: focusZoom, display: "flex", flexDirection: "column", minHeight: 0, height: "100%" } as React.CSSProperties}
                              >
                                {paneBody(window, lifecycle)}
                              </div>
                            ) : paneBody(window, lifecycle)}
                          </WindowScope>
                          </ScreenErrorBoundary>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            });
          })}
          {desk && slivers.left !== null ? (
            <Sliver side="l" title={titleOf(ws.windows[desk.slots[slivers.left][0]])} kind={ws.windows[desk.slots[slivers.left][0]]?.kind ?? "source"}
              onClick={() => commit(setFocus(wsRef.current, desk.deskId, desk.slots[slivers.left as number][0]))} />
          ) : null}
          {desk && slivers.right !== null ? (
            <Sliver side="r" title={titleOf(ws.windows[desk.slots[slivers.right][0]])} kind={ws.windows[desk.slots[slivers.right][0]]?.kind ?? "source"}
              onClick={() => commit(setFocus(wsRef.current, desk.deskId, desk.slots[slivers.right as number][0]))} />
          ) : null}
          {desk && desk.slots.length === 0 ? (
            <div className="desk-panel desk-quiet" style={{ position: "absolute", left: DESK_SIZES.side, top: DESK_SIZES.inset }}>
              This desk is empty. <button type="button" onClick={() => setOpener(true)}>open a source beside</button>
            </div>
          ) : null}
        </section>
      </main>
      <footer className="desk-keys">
        {hints.map(([keys, label]) => <span key={keys}><kbd>{keys}</kbd> {label}</span>)}
        {undoShown && viewportWidth < DESK_SIZES.shelfFoldBelow ? (
          // With the shelf folded to its rail, its undo line moves here.
          <button type="button" style={{ color: "var(--desk-amber)" }} onClick={() => { commit(undoClose(wsRef.current, undoShown.deskId)); setUndo(null); }}>
            ↺ undo close {undoShown.title}
          </button>
        ) : null}
        <span className="desk-dots" aria-label="windows on this desk">
          {desk?.slots.flatMap((slot, index) => slot.map((id) => (
            <button
              key={id}
              type="button"
              aria-label={titleOf(ws.windows[id])}
              className={id === focusId ? "f" : visibility[index]?.inView ? "in" : ""}
              style={focusMode ? (id === focusId ? { width: 46, height: 5 } : { opacity: 0.45 }) : undefined}
              onClick={() => commit(setFocus(wsRef.current, desk.deskId, id))}
            />
          )))}
        </span>
        <span className="note">hold <kbd>alt</kbd> for navi hints</span>
      </footer>
      {opener ? (
        <OpenBeside
          library={library}
          focus={focusWindow ?? null}
          focusTitle={titleOf(focusWindow)}
          onOpen={openContent}
          onOpenCard={(card) => {
            void transport.resolveExtraction(card.sourceId)
              .then((extractionId) => openContent(contentForCard(card, extractionId)))
              .catch(() => toastNow("that source didn't open"));
          }}
          onClose={() => setOpener(false)}
        />
      ) : null}
      {whichKey ? <WhichKey /> : null}
      {toast ? <div key={toast.key} className="desk-toast" role="status">{toast.text}</div> : null}
      {focusMode && badge !== null ? (
        <div key={badge} className="desk-zoom-badge fade" role="status">
          {Math.round(focusZoom * 100)}% · alt+↵ or esc to leave · = − to zoom
        </div>
      ) : null}
    </div>
  );
}

export function isVideoCard(card: SourceLibraryCard): boolean {
  return card.kindNoun === "video" || /youtube\.com|youtu\.be/.test(card.canonicalUri ?? "");
}

export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto {
  return isVideoCard(card)
    ? { kind: "video", sourceId: card.sourceId, extractionId }
    : { kind: "source", sourceId: card.sourceId, extractionId, view: "render" };
}

function Sliver({ side, title, kind, onClick }: { side: "l" | "r"; title: string; kind: string; onClick: () => void }) {
  return (
    <button type="button" className={`desk-sliver ${side}`} aria-label={`${side === "l" ? "previous" : "next"} window: ${title}`} onClick={onClick}>
      <span className="sg">{side === "l" ? "‹" : "›"}</span>
      <span className="sgl">{KIND_GLYPH[kind] ?? "§"}</span>
      <span className="st">{title}</span>
    </button>
  );
}

function WhichKey() {
  const groups: Array<{ id: NonNullable<(typeof DESK_BINDINGS)[number]["group"]>; title: string }> = [
    { id: "move", title: "move" },
    { id: "windows", title: "windows" },
    { id: "pads", title: "pads" },
    { id: "media", title: "media" },
  ];
  return (
    <div className="desk-whichkey" role="dialog" aria-label="alt keys">
      <div className="wkh">alt +</div>
      <div className="wkg">
        {groups.map((group) => {
          const rows = DESK_BINDINGS.filter((binding) => binding.group === group.id && !binding.later);
          if (rows.length === 0) return null;
          return (
            <div key={group.id}>
              <div className="wkt">{group.title}</div>
              {rows.map((binding) => (
                <div key={binding.id} className="wkr"><kbd>{binding.keys.replace(/^alt\+/, "")}</kbd><span>{binding.label}</span></div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/** "+ open beside": a source from the library, or a panel for the focused book. Until search lands
 * (spec §9.3) this list is how a window is opened on a desk. */
function OpenBeside({
  library,
  focus,
  focusTitle,
  onOpen,
  onOpenCard,
  onClose,
}: {
  library: SourceLibraryCard[] | null;
  focus: DeskWindow | null;
  focusTitle: string;
  onOpen: (content: ContentRefDto) => void;
  onOpenCard: (card: SourceLibraryCard) => void;
  onClose: () => void;
}) {
  const [filter, setFilter] = useState("");
  const words = filter.trim().toLowerCase();
  const sources = (library ?? []).filter((card) => card.readerEnabled !== false && (!words || card.title.toLowerCase().includes(words)));
  const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null;
  return (
    <div
      role="dialog"
      aria-label="open beside"
      data-desk-typing=""
      className="desk-whichkey"
      style={{ top: 48, bottom: "auto", width: 460 }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          onClose();
        }
      }}
    >
      <div className="wkh">open beside</div>
      <input
        autoFocus
        aria-label="find a source"
        placeholder="a source by its title…"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        style={{ width: "100%", boxSizing: "border-box", font: "12px var(--desk-mono)", background: "#1d1d21", color: "var(--desk-t)", border: "1px solid var(--desk-line2)", borderRadius: 4, padding: "4px 8px", marginBottom: 8 }}
      />
      <div style={{ maxHeight: 280, overflowY: "auto" }}>
        {book ? (
          <div style={{ marginBottom: 8 }}>
            <div className="wkt">for {focusTitle}</div>
            {(["guide", "notes", "path"] as const).map((panel) => (
              <div key={panel} className="wkr">
                <span />
                <button type="button" style={{ textAlign: "left" }} onClick={() => onOpen({ kind: "panel", panel, extractionId: book.extractionId })}>
                  ◇ {PANEL_TITLES[panel]}
                </button>
              </div>
            ))}
          </div>
        ) : null}
        <div className="wkt">the library</div>
        <div className="wkr"><span /><button type="button" style={{ textAlign: "left" }} onClick={() => onOpen({ kind: "panel", panel: "library" })}>◇ ask across the library</button></div>
        <div className="wkr"><span /><button type="button" style={{ textAlign: "left" }} onClick={() => onOpen({ kind: "compare", query: filter.trim() || undefined })}>⇄ compare{filter.trim() ? ` “${filter.trim()}”` : ""}</button></div>
        <div className="wkt" style={{ marginTop: 8 }}>sources</div>
        {library === null ? <div className="desk-quiet">◐ reading the library…</div> : null}
        {sources.map((card) => (
          <div key={card.sourceId} className="wkr">
            <span>{isVideoCard(card) ? "▶" : "§"}</span>
            <button type="button" style={{ textAlign: "left" }} onClick={() => onOpenCard(card)}>{card.title}</button>
          </div>
        ))}
      </div>
    </div>
  );
}
