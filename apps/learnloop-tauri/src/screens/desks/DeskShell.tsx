// The Reader workbench's desks (spec §3.1, §5): the top bar's desk tabs, the stage of windows in
// slots, the shelf, the footer, and the single key router for the workbench.
//
// The workspace model (model/workspace.ts) is the truth on screen; every change the learner makes is
// applied there at once and queued as `desk.apply` ops in the outbox (outbox.ts), which sends them in
// order. A conflict takes the server's state: the shell reads `desk.state` again.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, type CSSProperties, type ReactNode } from "react";
import { flushSync } from "react-dom";
import { api } from "../../api/client";
import { cachedSourceRead } from "../reader/readerCache";
import { poller } from "../../api/poller";
import type { ContentRefDto, DeskApplyDto, DeskApplyInput, DeskStateDto, SourceLibraryCard } from "../../api/dto";
import {
  closeWindow,
  createDesk,
  deskById,
  focusAlong,
  focusPane,
  focusedSlot,
  focusedWindowId,
  moveFocused,
  moveToDesk,
  moveWindowTo,
  openBeside,
  pairFocused,
  renameDesk,
  reorderSlots,
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
  slotWidth,
  softCropMask,
  stepZoom,
  type Rect,
  type Stage,
} from "./geometry";
import {
  IDENTITY,
  OVERVIEW,
  classifyWheel,
  dragProgress,
  dropTarget,
  enteringCamera,
  followSelection,
  moveSelection,
  newZoomGesture,
  normalizedDelta,
  overviewLayout,
  zoomWheel,
  type Camera,
  type ZoomGesture,
  type ZoomSource,
} from "./overview/engine";
import { ANIMATION_FRAMES, ZoomController, cameraTransform, type FrameClock, type SlotElements, type ZoomPlan } from "./overview/controller";
import { CardFace, LinkLayer } from "./overview/Card";
import { DRAWN_RELATIONS, curvedLinks, gatherOrder, relationsOf, type Relation } from "./overview/links";
import { MiniatureBook, cloneForMiniature } from "./overview/miniature";
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
import { WindowScope, isPaused, windowState, type ClaimedScope, type ListenerHub, type ScopeClaims, type WindowLifecycle } from "./lifecycle";
import { clientIdFor, type OutboxTransport } from "./outbox";
import { deskStoreFor } from "./store";
import { Shelf, type ShelfRow } from "./Shelf";
import { SourceWindow, type ReaderPassThrough, type SourceStatus } from "./windows/SourceWindow";
import { LibraryPanel, PANEL_TITLES, PathPanel, RailHostPanel } from "./windows/PanelWindow";
import { ScreenErrorBoundary } from "../../app/ScreenErrorBoundary";
import "../../styles/desk.css";
// The desks' five fonts ship with the app (SIL OFL 1.1, Fontsource packages pinned in package.json): Vite
// bundles their files, so nothing is fetched from a font service.
import "@fontsource-variable/inter";
import "@fontsource-variable/literata";
import "@fontsource-variable/literata/wght-italic.css";
import "@fontsource-variable/source-serif-4";
import "@fontsource-variable/source-serif-4/wght-italic.css";
import "@fontsource-variable/jetbrains-mono";
import "@fontsource-variable/caveat";

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
/** A window's reading place is saved once the learner settles on it. */
const VIEW_SAVE_IDLE_MS = 2_000;
/** A gather to a new desk leaves a placeholder sliver this long (spec §6.6). */
const MOVED_NOTICE_MS = 6_000;

/** What the visual harness may drive directly: the zoom's progress, for the commit-identity check. */
export interface DeskDebugHandle {
  beginZoom(): boolean;
  setZoomProgress(p: number): void;
  finishZoom(goal: 0 | 1): void;
  zoomFrameTimes(): number[];
  overview(): boolean;
}

function prefersReducedMotion(): boolean {
  try {
    return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/** A slot's key: its desk and the windows in it. */
function slotKey(deskId: string, slot: string[]): string {
  return `${deskId}:${slot.join("+")}`;
}

function intersects(rect: Rect, stage: Stage): boolean {
  return rect.x + rect.w > 0 && rect.x < stage.width && rect.y + rect.h > 0 && rect.y < stage.height;
}

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
  /** The zoom's frames (tests drive them by hand). */
  frameClock?: FrameClock;
  /** Reduced motion; absent, the system's setting. */
  reducedMotion?: boolean;
  /** The harness's handle on the zoom. */
  onDebugHandle?: (handle: DeskDebugHandle) => void;
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
  frameClock = ANIMATION_FRAMES,
  reducedMotion,
  onDebugHandle,
}: DeskShellProps) {
  // The vault's one desk store (store.ts): it outlives this shell, so leaving and coming back never makes a
  // second outbox for the same client.
  const store = useMemo(
    () => deskStoreFor(vaultKey, transport, timers, () => clientIdFor(vaultKey, typeof window === "undefined" ? null : window.localStorage, () => mintId("client"))),
    [vaultKey, transport, timers, mintId],
  );
  const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const [storeReady, setStoreReady] = useState(store.loaded);
  const ws: Workspace | null = storeReady ? storeWs : null;
  const wsRef = useMemo(() => ({ get current(): Workspace { return store.ws; } }), [store]);
  const [library, setLibrary] = useState<SourceLibraryCard[] | null>(null);
  const deskKey = `learnloop.desks.current.${vaultKey}`;
  const [currentDeskId, setCurrentDeskIdState] = useState<string | null>(() => readStored(deskKey));
  const [camX, setCamX] = useState<Record<string, number>>({});
  const [visited, setVisited] = useState<Set<string>>(() => new Set());
  const [focusMode, setFocusMode] = useState(false);
  const [whichKey, setWhichKey] = useState(false);
  const [toast, setToast] = useState<{ text: string; key: number } | null>(null);
  const [undo, setUndo] = useState<{ deskId: string; windowId: string; title: string; until: number } | null>(null);
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
  // The overview (spec §6): the committed view, its camera and selection, and what a zoom needs.
  const [overview, setOverview] = useState(false);
  const [ovCam, setOvCam] = useState<Camera>({ x: 24, y: 70, s: OVERVIEW.scale });
  const [selection, setSelection] = useState<{ deskId: string; windowId: string } | null>(null);
  const [zooming, setZooming] = useState(false);
  // While a zoom leaves the overview: the desk it lands on and its camera, so the soft crop and the
  // slivers it will show are already there on its last frame (the commit then changes nothing).
  const [leaveTarget, setLeaveTarget] = useState<{ deskId: string; cams: Record<string, number> } | null>(null);
  const [showRelations, setShowRelations] = useState(true);
  const [gatherPreview, setGatherPreview] = useState(false);
  const [panEase, setPanEase] = useState(false);
  const [hud, setHud] = useState("");
  const [ungather, setUngather] = useState<{ deskId: string; order: string[][] } | null>(null);
  const [movedNotice, setMovedNotice] = useState<{ deskId: string; title: string; until: number } | null>(null);
  const preOverview = useRef<{ deskId: string; focusId: string | null } | null>(null);
  const worldRef = useRef<HTMLDivElement | null>(null);
  // Each slot's three elements, by slot key. Kept apart because React attaches a parent's ref after its
  // children's, so one record per slot would lose the children on every render.
  const boxEls = useRef(new Map<string, HTMLElement>());
  const innerEls = useRef(new Map<string, HTMLElement>());
  const cardEls = useRef(new Map<string, HTMLElement>());
  const ringEls = useRef(new Map<string, HTMLElement>());
  const slotElements = useCallback((): Map<string, SlotElements> => {
    const out = new Map<string, SlotElements>();
    for (const [key, box] of boxEls.current) out.set(key, { box, inner: innerEls.current.get(key) ?? null, card: cardEls.current.get(key) ?? null });
    return out;
  }, []);
  const lateEls = useRef(new Map<string, HTMLElement>());
  const sliverEls = useRef(new Map<string, HTMLElement>());
  const miniatures = useMemo(() => new MiniatureBook(), []);
  const miniHosts = useRef(new Map<string, HTMLDivElement>());
  const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1) => void>(() => undefined);
  const controller = useMemo(() => new ZoomController(frameClock, (goal, base) => onEndRef.current(goal, base)), [frameClock]);
  const jumps = useRef(new Map<string, (spanId: string) => void>());
  const media = useRef(new Map<string, () => void>());
  const pendingJump = useRef(new Map<string, string>());

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

  const commit = useCallback((step: Step) => {
    store.commit(step);
    if (step.notice) toastNow(step.notice);
  }, [store, toastNow]);

  // What the store could not save, said in one line.
  useEffect(() => store.onNotice((notice) => {
    if (notice.kind === "rejected") toastNow("that change couldn't be saved, and was undone");
    else if (notice.kind === "conflict") {
      const total = notice.dropped + notice.lost;
      if (total > 0) toastNow(`the desk changed elsewhere · ${total} change${total === 1 ? "" : "s"} couldn't be kept`);
    } else if (notice.kind === "offline") toastNow("couldn't save the desk just now · it is kept here until it can be");
    else onError(notice.message);
  }), [store, toastNow, onError]);

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

  useEffect(() => {
    let live = true;
    void (async () => {
      try {
        const [state, cards] = await Promise.all([store.load(), transport.library().catch(() => null)]);
        if (!live) return;
        setLibrary(cards);
        if (state && store.ws.desks.length === 0) store.commit(await firstRun(store.ws, cards));
        if (live) setStoreReady(true);
      } catch (error) {
        if (live) onError(error instanceof Error ? error.message : typeof error === "object" && error && "message" in error ? String((error as { message: unknown }).message) : String(error));
      }
    })();
    // A load that lands after this shell unmounted changes nothing here.
    return () => {
      live = false;
    };
    // Loaded once per store; a conflict reconciles inside the store.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store]);

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
            // In the overview every window is a card (a preview): paused, and it logs no reading.
            state: windowState({ onCurrentDesk: onCurrent, inView: onCurrent && Boolean(visibility[index]?.inView), focused: onCurrent && id === focusId, focusMode, preview: overview }),
          };
        }
      });
    }
    return out;
  }, [ws, deskId, visibility, focusId, focusMode, overview]);
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

  // -- the overview: its layout, a zoom's plan and its commit (spec §6.2, §6.3) -----------------------

  const ovLayout = useMemo(() => (ws ? overviewLayout(ws.desks.map((each) => each.slots.length), slotWidth(stage), stage) : null), [ws, stage]);
  const ovLayoutRef = useRef(ovLayout);
  ovLayoutRef.current = ovLayout;
  const stageNow = useRef(stage);
  stageNow.current = stage;
  const camXRef = useRef(camX);
  camXRef.current = camX;
  const overviewRef = useRef(overview);
  overviewRef.current = overview;
  const ovCamRef = useRef(ovCam);
  ovCamRef.current = ovCam;
  const selectionRef = useRef(selection);
  selectionRef.current = selection;
  const visitedRef = useRef(visited);
  visitedRef.current = visited;
  const showRelationsRef = useRef(showRelations);
  showRelationsRef.current = showRelations;
  const reduced = reducedMotion ?? prefersReducedMotion();
  const pendingLeave = useRef<{ deskId: string; windowId: string | null; cams: Record<string, number>; focusMode: boolean } | null>(null);

  /** Where a window's card is in the overview's world. */
  const cardOf = useCallback((windowId: string | null | undefined): Rect | null => {
    const layout = ovLayoutRef.current;
    const current = wsRef.current;
    if (!layout || !windowId) return null;
    for (const [row, each] of current.desks.entries()) {
      const index = slotIndexOf(each, windowId);
      if (index >= 0) return layout.cards[row]?.[index] ?? null;
    }
    return null;
  }, []);

  /** A slot's reading rect in world coordinates, with `readingDeskId`'s row in view and `cams` each desk's
   * camera: where the reading view lays it out. */
  const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect => {
    const each = current.desks[row];
    const rect = slotRects(each.slots.length, st)[index];
    return { x: rect.x - (cams[each.deskId] ?? 0), y: rect.y + rowTop(row, st) - rowTop(readingRow, st), w: rect.w, h: rect.h };
  }, []);

  const relatedTo = useCallback((windowId: string | null | undefined): Relation[] => (windowId ? relationsOf(wsRef.current, windowId).slice(0, DRAWN_RELATIONS) : []), []);

  /** Whether a slot recedes in the overview: the selection has relations, and this slot is neither it nor one. */
  const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean => {
    if (!relationsOn || !selected || related.length === 0) return false;
    return !slot.includes(selected) && !slot.some((id) => related.some((relation) => relation.windowId === id));
  }, []);

  const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera): ZoomPlan | null => {
    const current = wsRef.current;
    const layout = ovLayoutRef.current;
    const st = stageNow.current;
    if (!layout) return null;
    const readingRow = Math.max(0, current.desks.findIndex((each) => each.deskId === readingDeskId));
    const related = relatedTo(selected);
    const items: ZoomPlan["items"] = [];
    const rings: ZoomPlan["rings"] = [];
    current.desks.forEach((each, row) => each.slots.forEach((slot, index) => {
      const a = readingRectOf(current, row, index, readingRow, cams, st);
      const b = layout.cards[row][index];
      const readingPanes = paneRects(a, slot.length);
      const cardPanes = paneRects(b, slot.length);
      const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st);
      const recede = recedes(slot, selected, related, showRelationsRef.current);
      const focus = selected !== null && slot.includes(selected);
      const isRelated = showRelationsRef.current && slot.some((id) => related.some((relation) => relation.windowId === id));
      slot.forEach((id, pane) => {
        const pa = readingPanes[pane];
        const pb = cardPanes[pane];
        items.push({ key: id, a: pa, b: pb, base: base === 0 ? pa : pb, live, recede, focus: focus && id === selected });
      });
      if (focus || isRelated) rings.push({ key: slotKey(each.deskId, slot), a, b });
    }));
    return { base, A: IDENTITY, B, items, rings };
  }, [readingRectOf, relatedTo, recedes]);

  const zoomTargets = useCallback(() => ({
    world: worldRef.current as HTMLElement,
    slots: slotElements(),
    rings: new Map(ringEls.current),
    late: [...lateEls.current.values()],
    slivers: [...sliverEls.current.values()],
  }), [slotElements]);

  /** Start a zoom from the reading view (into the overview); returns false when one cannot start. */
  const beginEnter = useCallback((): boolean => {
    if (controller.active || overviewRef.current || !worldRef.current) return false;
    const id = deskIdRef.current;
    if (!id) return false;
    if (focusModeRef.current) flushSync(() => setFocusMode(false));
    const selected = focusIdRef.current;
    preOverview.current = { deskId: id, focusId: selected };
    const B = enteringCamera(cardOf(selected), stageNow.current);
    flushSync(() => {
      setZooming(true);
      setSelection(selected ? { deskId: id, windowId: selected } : null);
    });
    const plan = planZoom(0, id, camXRef.current, selected, B);
    if (!plan) return false;
    controller.begin(plan, zoomTargets());
    return true;
  }, [controller, cardOf, planZoom, zoomTargets]);

  /** Start a zoom from the overview back into a desk: the selected card's, or where the overview was
   * entered from. */
  const beginLeave = useCallback((to: { deskId: string; windowId: string | null } | null, focusAfter = false): boolean => {
    if (controller.active || !overviewRef.current || !worldRef.current) return false;
    const target = to ?? preOverview.current ?? (selectionRef.current ? { deskId: selectionRef.current.deskId, focusId: selectionRef.current.windowId } : null);
    if (!target) return false;
    const deskIdTo = target.deskId;
    const windowTo = "windowId" in target ? target.windowId : target.focusId;
    const current = wsRef.current;
    const each = deskById(current, deskIdTo);
    if (!each) return false;
    const cams = { ...camXRef.current };
    const index = windowTo ? slotIndexOf(each, windowTo) : -1;
    cams[deskIdTo] = ensureVisible(cams[deskIdTo] ?? 0, index >= 0 ? index : focusedSlot(current, each), each.slots.length, stageNow.current);
    const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current);
    if (!plan) return false;
    pendingLeave.current = { deskId: deskIdTo, windowId: windowTo, cams, focusMode: focusAfter };
    flushSync(() => {
      setZooming(true);
      setLeaveTarget({ deskId: deskIdTo, cams });
    });
    controller.begin(plan, zoomTargets());
    return true;
  }, [controller, planZoom, zoomTargets]);

  /** The zoom ended: the one commit, whose layout is the zoom's last frame. */
  onEndRef.current = (goal, base) => {
    const plan = controller.plan;
    controller.clean();
    if (goal === base) {
      flushSync(() => {
        setZooming(false);
        setLeaveTarget(null);
      });
      pendingLeave.current = null;
      return;
    }
    if (goal === 1) {
      flushSync(() => {
        setOverview(true);
        if (plan) setOvCam(plan.B);
        setZooming(false);
      });
      return;
    }
    const leave = pendingLeave.current;
    pendingLeave.current = null;
    flushSync(() => {
      setOverview(false);
      // `zooming` stays one more frame: the windows' left/top transitions must not animate the commit's
      // layout from the cards back to the slots it already shows.
      if (leave) {
        setCamX(leave.cams);
        setCurrentDeskId(leave.deskId);
        if (leave.windowId) commit(setFocus(wsRef.current, leave.deskId, leave.windowId));
        if (leave.focusMode) setFocusMode(true);
      }
    });
    frameClock.request(() => frameClock.request(() => {
      setZooming(false);
      setLeaveTarget(null);
    }));
  };

  /** alt+o, o, the button, esc, ↵: the fast eased zoom (a crossfade with reduced motion). */
  const toggleOverview = useCallback((to: { deskId: string; windowId: string | null } | null = null, focusAfter = false) => {
    if (controller.active) {
      controller.go(overviewRef.current ? 1 : 0);
      return;
    }
    if (reduced) {
      // Reduced motion: no zoom, a short crossfade (spec §6.3).
      const world = worldRef.current;
      world?.classList.remove("desk-fadeswap");
      void world?.offsetWidth;
      world?.classList.add("desk-fadeswap");
      if (!overviewRef.current) {
        const id = deskIdRef.current;
        if (!id) return;
        if (focusModeRef.current) setFocusMode(false);
        preOverview.current = { deskId: id, focusId: focusIdRef.current };
        setSelection(focusIdRef.current ? { deskId: id, windowId: focusIdRef.current } : null);
        setOvCam(enteringCamera(cardOf(focusIdRef.current), stageNow.current));
        setOverview(true);
      } else {
        const target = to ?? (preOverview.current ? { deskId: preOverview.current.deskId, windowId: preOverview.current.focusId } : null);
        setOverview(false);
        if (target) {
          setCurrentDeskId(target.deskId);
          if (target.windowId) commit(setFocus(wsRef.current, target.deskId, target.windowId));
        }
        if (focusAfter) setFocusMode(true);
      }
      return;
    }
    if (overviewRef.current) {
      if (beginLeave(to, focusAfter)) controller.go(0);
    } else if (beginEnter()) {
      controller.go(1);
    }
  }, [controller, reduced, beginEnter, beginLeave, cardOf, setCurrentDeskId, commit]);

  /** Move the overview's selection; the camera follows over .2 s, keeping it 48 px inside. */
  const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down") => {
    const layout = ovLayoutRef.current;
    const current = wsRef.current;
    const sel = selectionRef.current;
    if (!layout) return;
    let row = sel ? current.desks.findIndex((each) => each.deskId === sel.deskId) : 0;
    let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0;
    if (row < 0 || slot < 0) {
      row = 0;
      slot = 0;
    }
    const next = moveSelection(layout, { row, slot }, direction);
    const each = current.desks[next.row];
    const windowId = each?.slots[next.slot]?.find((id) => current.windows[id]?.active) ?? each?.slots[next.slot]?.[0];
    if (!each || !windowId) return;
    setSelection({ deskId: each.deskId, windowId });
    setPanEase(true);
    setOvCam((cam) => followSelection(cam, layout.cards[next.row][next.slot], stageNow.current));
  }, []);

  /** Gather around the focus (spec §6.6): linked windows to its right, or to a new desk. */
  const gather = useCallback((toNewDesk: boolean) => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    const focus = focusIdRef.current;
    const each = id ? deskById(current, id) : null;
    if (!id || !focus || !each) return;
    if (!toNewDesk && ungather && ungather.deskId === id) {
      commit(reorderSlots(current, id, ungather.order));
      setUngather(null);
      return;
    }
    const related = relationsOf(current, focus).filter((relation) => current.windows[relation.windowId]?.deskId === id);
    if (related.length === 0) {
      toastNow("nothing on this desk is linked to this window yet");
      return;
    }
    const { order, stayed } = gatherOrder(each.slots, focus, related);
    if (!toNewDesk) {
      setUngather({ deskId: id, order: each.slots.map((slot) => [...slot]) });
      commit(reorderSlots(current, id, order));
      if (stayed > 0) toastNow(`gathered · and ${stayed} more stayed (four move along at most)`);
      return;
    }
    // To a new desk: the focus and its linked windows (four at most), the focus first.
    const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation) => relation.windowId)];
    const newDeskId = mintId("desk");
    const title = `gathered · ${shortName(titleOf(current.windows[focus]))}`;
    let step = createDesk(current, newDeskId, title);
    let after: string | null = null;
    for (const windowId of moving) {
      const next = moveToDesk(step.ws, id, windowId, newDeskId, after);
      step = { ws: next.ws, ops: [...step.ops, ...next.ops] };
      after = windowId;
    }
    const focused = setFocus(step.ws, newDeskId, focus);
    step = { ws: focused.ws, ops: [...step.ops, ...focused.ops] };
    commit(step);
    setMovedNotice({ deskId: id, title, until: timers.now() + MOVED_NOTICE_MS });
    if (related.length > DRAWN_RELATIONS) toastNow(`moved to “${title}” · and ${related.length - DRAWN_RELATIONS} more stayed`);
    setCurrentDeskId(newDeskId);
  }, [commit, mintId, setCurrentDeskId, timers, titleOf, toastNow, ungather]);

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
      case "moveWindow": {
        const sel = overviewRef.current ? selectionRef.current : null;
        if (sel) {
          const each = deskById(current, sel.deskId);
          const index = each ? slotIndexOf(each, sel.windowId) : -1;
          if (each && index >= 0) commit(moveWindowTo(current, sel.deskId, sel.windowId, index + action.direction));
          return true;
        }
        commit(moveFocused(current, id, action.direction));
        return true;
      }
      case "moveToDesk": {
        const sel = selectionRef.current;
        if (!overviewRef.current || !sel) return true;
        const row = current.desks.findIndex((each) => each.deskId === sel.deskId);
        const to = current.desks[row + action.direction];
        const from = current.desks[row];
        if (!to || !from) return true;
        const index = slotIndexOf(from, sel.windowId);
        const afterSlot = to.slots[Math.min(index, to.slots.length) - 1];
        commit(moveToDesk(current, sel.deskId, sel.windowId, to.deskId, afterSlot ? afterSlot[afterSlot.length - 1] : null));
        setSelection({ deskId: to.deskId, windowId: sel.windowId });
        return true;
      }
      case "overview":
        toggleOverview();
        return true;
      case "overviewMove":
        moveOverviewSelection(action.direction);
        return true;
      case "overviewOpen": {
        const sel = selectionRef.current;
        toggleOverview(sel ? { deskId: sel.deskId, windowId: sel.windowId } : null, action.focusMode);
        return true;
      }
      case "leaveOverview":
        toggleOverview(null);
        return true;
      case "toggleRelations":
        setShowRelations((on) => !on);
        return true;
      case "gatherPreview":
        setGatherPreview(true);
        return true;
      case "gather":
        gather(action.toNewDesk);
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
        setUndo({ deskId: id, windowId: focus, title, until: timers.now() + UNDO_CLOSE_MS });
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
  }, [commit, switchDesk, timers, titleOf, toggleOverview, moveOverviewSelection, gather]);
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
        // A pointer press during a zoom settles it at once (spec §6.3).
        if (controller.active) controller.settle();
        return false;
      }
      if (!(event instanceof KeyboardEvent)) return false;
      if (type === "keyup") {
        modifiers.keyup(event);
        if (event.key === "g" || event.key === "G") setGatherPreview(false);
        // Alt held long enough to show which-key: its release belongs to the panel, never to a window's
        // capture-clearing tap.
        return altTracker.release(event) === "hold";
      }
      if (type !== "keydown") return false;
      modifiers.keydown(event);
      altTracker.keydown(event);
      if (event.key === "Alt" || event.key === "Control" || event.key === "Shift" || event.key === "Meta") return false;
      // A key press during a zoom settles it first (spec §6.3); a repeat does not.
      if (controller.active && !event.repeat) controller.settle();
      const open = claimed.current.get(focusIdRef.current ?? "");
      const has = (scope: ClaimedScope) => (open?.get(scope)?.size ?? 0) > 0;
      const resolution = resolveKey(event, {
        typing: isTypingTarget(event.target) || has("typing"),
        menu: has("menu"),
        check: has("check"),
        focus: focusModeRef.current,
        overview: overviewRef.current,
      }, modifiers.read(event));
      if (!resolution || resolution.binding.later) return false;
      if (!runRef.current(resolution.binding.action)) return false;
      event.preventDefault();
      event.stopPropagation();
      return true;
    },
  }), [modifiers, altTracker, commit, controller]);
  useEffect(() => {
    router.ensure("window", "keydown");
    router.ensure("window", "keyup");
    router.ensure("window", "mousedown");
    router.ensure("window", "blur");
    return () => router.dispose();
  }, [router]);
  // The scopes each window's content has open (a Reader's menu, its intent box): the router reads the
  // active window's before the desk's own bindings.
  const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>());
  const claimsByWindow = useRef(new Map<string, ScopeClaims>());
  const claimsFor = useCallback((windowId: string): ScopeClaims => {
    let claims = claimsByWindow.current.get(windowId);
    if (!claims) {
      claims = {
        claim: (scope, owner, open) => {
          const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>();
          const owners = byScope.get(scope) ?? new Set<string>();
          if (open) owners.add(owner);
          else owners.delete(owner);
          byScope.set(scope, owners);
          claimed.current.set(windowId, byScope);
        },
      };
      claimsByWindow.current.set(windowId, claims);
    }
    return claims;
  }, []);
  const hubs = useRef(new Map<string, ListenerHub>());
  const hubFor = useCallback((windowId: string): ListenerHub => {
    let hub = hubs.current.get(windowId);
    if (!hub) {
      hub = router.hubFor(windowId);
      hubs.current.set(windowId, hub);
    }
    return hub;
  }, [router]);

  // -- the world's camera at rest, the wheel router, ctrl+drag, the overview's drags (spec §5.5, §6.2) -------

  // At rest the world's transform is the committed view's camera; a zoom writes it itself.
  useLayoutEffect(() => {
    const world = worldRef.current;
    if (!world || controller.active) return;
    world.style.transform = overview ? cameraTransform(ovCam) : "";
  });

  const mainRef = useRef<HTMLElement | null>(null);
  const gesture = useRef<{ kind: "pan" | "zoom" | "scroll" | "ovpan"; source?: ZoomSource; zoom?: ZoomGesture; timer: unknown; panned: boolean } | null>(null);
  const endGesture = useCallback(() => {
    const g = gesture.current;
    gesture.current = null;
    setHud("");
    if (!g) return;
    if (g.kind === "zoom" && g.zoom && !g.zoom.latch && controller.active) {
      // The fingers lifted mid-zoom: complete past 40 % of the way, else spring back.
      controller.release();
    }
    if (g.kind === "pan" && g.panned) {
      // Snap to the nearest window's left edge and focus it.
      const current = wsRef.current;
      const id = deskIdRef.current;
      const each = id ? deskById(current, id) : null;
      if (!id || !each || each.slots.length === 0) return;
      const st = stageNow.current;
      const rects = slotRects(each.slots.length, st);
      const cam = camXRef.current[id] ?? 0;
      let best = 0;
      rects.forEach((rect, index) => {
        if (Math.abs(rect.x - DESK_SIZES.side - cam) < Math.abs(rects[best].x - DESK_SIZES.side - cam)) best = index;
      });
      const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st);
      setCamX((cams) => ({ ...cams, [id]: snapped }));
      const target = each.slots[best].find((windowId) => current.windows[windowId]?.active) ?? each.slots[best][0];
      commit(setFocus(current, id, target));
    }
  }, [controller, commit]);

  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;
    const onWheel = (event: WheelEvent) => {
      const target = event.target as Element | null;
      if (!target || !target.closest("[data-desk-stage], .desk-shelf, .desk-shelf-rail")) return;
      const st = stageNow.current;
      const now = performance.now();
      let g = gesture.current;
      if (!g) {
        const kind = classifyWheel(event, modifiers.read(event), st.height);
        // In the overview a plain wheel pans its camera; alt or ctrl zooms back in.
        const ovPlain = overviewRef.current && kind.kind !== "zoom";
        g = gesture.current = {
          kind: ovPlain ? "ovpan" : kind.kind,
          source: kind.source,
          zoom: kind.kind === "zoom" && kind.source ? newZoomGesture(kind.source, now) : undefined,
          timer: null,
          panned: false,
        };
      }
      if (g.kind === "scroll") {
        // A plain scroll is the window's own (it never pans the strip).
        timers.clear(g.timer);
        g.timer = timers.set(endGesture, OVERVIEW.gestureIdleMs);
        return;
      }
      event.preventDefault();
      const { dx, dy } = normalizedDelta(event, st.height);
      if (g.kind === "ovpan") {
        setPanEase(false);
        setOvCam((cam) => ({ ...cam, x: cam.x - (event.shiftKey ? dy : dx), y: cam.y - (event.shiftKey ? 0 : dy) }));
        timers.clear(g.timer);
        g.timer = timers.set(endGesture, OVERVIEW.gestureIdleMs);
        return;
      }
      if (g.kind === "pan") {
        if (overviewRef.current || focusModeRef.current) return;
        const id = deskIdRef.current;
        const each = id ? deskById(wsRef.current, id) : null;
        if (!id || !each) return;
        const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy;
        const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect) => Math.max(end, rect.x + rect.w), 0) + DESK_SIZES.side - st.width);
        setCamX((cams) => ({ ...cams, [id]: Math.max(0, Math.min(max, (cams[id] ?? 0) + travel)) }));
        g.panned = true;
        setHud("alt + swipe · moving along the strip · lift to snap");
        timers.clear(g.timer);
        g.timer = timers.set(endGesture, OVERVIEW.panSnapMs);
        return;
      }
      // The zoom: alt + vertical, ctrl + scroll, or a pinch.
      if (!g.zoom) return;
      const result = zoomWheel(g.zoom, dy, now, { active: controller.active, inOverview: overviewRef.current, target: controller.target });
      g.zoom = result.gesture;
      const stepped = result.step;
      if (stepped.kind === "begin-and-target") {
        const began = overviewRef.current ? beginLeave(selectionRef.current ? { deskId: selectionRef.current.deskId, windowId: selectionRef.current.windowId } : null) : beginEnter();
        if (began) controller.setTarget(stepped.target);
      } else if (stepped.kind === "target") {
        controller.setTarget(stepped.target);
      } else if (stepped.kind === "goal") {
        if (!controller.active) {
          const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ? { deskId: selectionRef.current.deskId, windowId: selectionRef.current.windowId } : null);
          if (!began) return;
        }
        controller.go(stepped.goal);
      }
      if (stepped.kind === "target" || stepped.kind === "begin-and-target") {
        const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll";
        setHud(`${how} · zooming ${dy > 0 ? "out" : "in"} · lift to settle`);
      } else {
        setHud("");
      }
      timers.clear(g.timer);
      g.timer = timers.set(endGesture, stepped.armMs);
    };
    main.addEventListener("wheel", onWheel, { passive: false, capture: true });
    return () => main.removeEventListener("wheel", onWheel, { capture: true });
  }, [ws === null, modifiers, timers, controller, beginEnter, beginLeave, endGesture]);

  // Ctrl+drag on the stage background scrubs the zoom (320 px is the whole zoom); in the overview a drag
  // on the background pans, and a card dragged farther than 8 px moves.
  const drag = useRef<{ kind: "scrub" | "pan" | "card"; x: number; y: number; base: 0 | 1; cam: Camera; key?: string; windowId?: string; deskId?: string; moved: boolean } | null>(null);
  const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>) => {
    const target = event.target as Element;
    const onCard = target.closest("[data-desk-slot]");
    const inContent = target.closest(".desk-slot-inner, .desk-sliver, button, input, textarea");
    if (overviewRef.current) {
      if (onCard) {
        const key = onCard.getAttribute("data-desk-slot-key") ?? undefined;
        const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined;
        const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined;
        drag.current = { kind: "card", x: event.clientX, y: event.clientY, base: 1, cam: ovCamRef.current, key, windowId, deskId: deskOf, moved: false };
      } else {
        drag.current = { kind: "pan", x: event.clientX, y: event.clientY, base: 1, cam: ovCamRef.current, moved: false };
      }
      (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
      return;
    }
    if ((event.ctrlKey || modifiers.read().ctrl) && !inContent && !focusModeRef.current) {
      drag.current = { kind: "scrub", x: event.clientX, y: event.clientY, base: 0, cam: IDENTITY, moved: false };
      (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
      event.preventDefault();
    }
  }, [modifiers]);
  const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>) => {
    const d = drag.current;
    if (!d) return;
    const dx = event.clientX - d.x;
    const dy = event.clientY - d.y;
    if (d.kind === "scrub") {
      if (!controller.active && !beginEnter()) {
        drag.current = null;
        return;
      }
      d.moved = true;
      controller.setTarget(dragProgress(d.base, dy));
      setHud("ctrl + drag · zooming · let go to settle");
      return;
    }
    if (d.kind === "pan") {
      d.moved = d.moved || Math.hypot(dx, dy) > 3;
      setPanEase(false);
      setOvCam({ ...d.cam, x: d.cam.x + dx, y: d.cam.y + dy });
      return;
    }
    if (!d.moved && Math.hypot(dx, dy) <= OVERVIEW.cardDragPx) return;
    d.moved = true;
    const element = d.windowId ? boxEls.current.get(d.windowId) : null;
    if (element) {
      element.style.transform = `translate(${dx / d.cam.s}px, ${dy / d.cam.s}px)`;
      element.style.zIndex = "30";
    }
  }, [controller, beginEnter]);
  const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>) => {
    const d = drag.current;
    drag.current = null;
    if (!d) return;
    if (d.kind === "scrub") {
      setHud("");
      if (controller.active) controller.release();
      return;
    }
    if (d.kind !== "card" || !d.windowId || !d.deskId) return;
    const element = d.windowId ? boxEls.current.get(d.windowId) : null;
    if (element) {
      element.style.transform = "";
      element.style.zIndex = "";
    }
    if (!d.moved) {
      // A click on a card opens it.
      setSelection({ deskId: d.deskId, windowId: d.windowId });
      toggleOverview({ deskId: d.deskId, windowId: d.windowId });
      return;
    }
    const layout = ovLayoutRef.current;
    const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect();
    if (!layout) return;
    const point = { x: (event.clientX - stageBox.left - d.cam.x) / d.cam.s, y: (event.clientY - stageBox.top - d.cam.y) / d.cam.s };
    const drop = dropTarget(layout, point);
    const current = wsRef.current;
    const to = drop ? current.desks[drop.row] : null;
    if (!drop || !to) return;
    if (to.deskId === d.deskId) {
      const from = slotIndexOf(to, d.windowId);
      commit(moveWindowTo(current, d.deskId, d.windowId, Math.min(drop.slot > from ? drop.slot - 1 : drop.slot, to.slots.length - 1)));
    } else {
      const afterSlot = to.slots[drop.slot - 1];
      commit(moveToDesk(current, d.deskId, d.windowId, to.deskId, afterSlot ? afterSlot[afterSlot.length - 1] : null));
      setSelection({ deskId: to.deskId, windowId: d.windowId });
    }
  }, [controller, toggleOverview, commit]);

  // Miniatures: after the overview opens, when idle, each opened window's picture is (re)built if it changed.
  useEffect(() => {
    if (!overview) return;
    const handle = timers.set(() => {
      for (const [windowId, host] of miniHosts.current) {
        const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane) => pane.getAttribute("data-desk-window") === windowId) ?? null;
        if (!body) continue;
        if (miniatures.needs(windowId)) {
          const { node, restoreScroll } = cloneForMiniature(body);
          node.style.width = `${body.offsetWidth}px`;
          node.style.height = `${body.offsetHeight}px`;
          miniatures.store(windowId, node);
          host.replaceChildren(node);
          restoreScroll();
        } else if (!host.firstChild) {
          const node = miniatures.get(windowId);
          if (node) host.replaceChildren(node);
        }
        const node = host.firstElementChild as HTMLElement | null;
        if (node && body.offsetWidth > 0) node.style.transform = `scale(${host.clientWidth / body.offsetWidth})`;
      }
    }, 120);
    return () => timers.clear(handle);
  }, [overview, timers, miniatures]);

  // The harness's handle on the zoom (the commit-identity check drives p itself).
  useEffect(() => {
    onDebugHandle?.({
      beginZoom: () => (overviewRef.current ? beginLeave(null) : beginEnter()),
      setZoomProgress: (p) => controller.setProgress(p),
      finishZoom: (goal) => onEndRef.current(goal, controller.plan?.base ?? (goal === 1 ? 0 : 1)),
      zoomFrameTimes: () => [...controller.frameTimes],
      overview: () => overviewRef.current,
    });
  }, [onDebugHandle, controller, beginEnter, beginLeave]);

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
      const handle = timers.set(() => {
        shellTimers.current.delete(handle);
        setEntering((now) => {
          const next = new Set(now);
          next.delete(step.windowId);
          return next;
        });
      }, 450);
      shellTimers.current.add(handle);
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
  const shellTimers = useRef(new Set<unknown>());
  // The shell's own timers (a pending view save, an entering fade) end with it; the store's flush does not.
  useEffect(() => () => {
    for (const handle of viewTimers.current.values()) timers.clear(handle);
    viewTimers.current.clear();
    for (const handle of shellTimers.current) timers.clear(handle);
    shellTimers.current.clear();
  }, [timers]);
  const statusFor = useMemo(() => new Map<string, (next: SourceStatus) => void>(), []);
  const onStatusFor = useCallback((windowId: string) => {
    let handler = statusFor.get(windowId);
    if (!handler) {
      handler = (next: SourceStatus) => {
        setStatus((all) => ({ ...all, [windowId]: { ...all[windowId], ...next } }));
        // The window changed: its card's picture is rebuilt the next time the overview shows it.
        miniatures.invalidate(windowId);
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
  }, [statusFor, timers, commit, miniatures]);

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

  // An undo offer holds only while the window is still closed (a close the server refused is no close).
  const undoShown = undo && undo.deskId === deskId && undo.until > timers.now()
    && (ws?.closed[undo.deskId] ?? []).some((entry) => entry.window.windowId === undo.windowId) ? undo : null;
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

  // The overview's relations, links and gather ghosts for the selection (or, entering, the focus).
  const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null;
  const selectedRelations = relatedTo(linkedFrom);
  const linkRects = new Map<string, Rect>();
  ws.desks.forEach((each, row) => each.slots.forEach((slot, index) => {
    const rect = ovLayout?.cards[row]?.[index];
    if (rect) for (const id of slot) linkRects.set(id, rect);
  }));
  const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null;
  const links = fromCard
    ? curvedLinks(fromCard, selectedRelations.filter((relation) => linkRects.has(relation.windowId)).map((relation) => ({ rect: linkRects.get(relation.windowId) as Rect, relation })))
    : [];
  const ghosts: Array<{ key: string; rect: Rect }> = [];
  if (overview && gatherPreview && selection && ovLayout) {
    const row = ws.desks.findIndex((each) => each.deskId === selection.deskId);
    const each = ws.desks[row];
    if (each) {
      const sameDesk = selectedRelations.filter((relation) => ws.windows[relation.windowId]?.deskId === each.deskId);
      const { order } = gatherOrder(each.slots, selection.windowId, sameDesk);
      order.forEach((slot, index) => {
        // Only the linked cards: where each would go.
        const linked = slot.some((id) => sameDesk.some((relation) => relation.windowId === id));
        if (linked && each.slots[index]?.[0] !== slot[0] && ovLayout.cards[row][index]) ghosts.push({ key: slot.join("+"), rect: ovLayout.cards[row][index] });
      });
    }
  }
  const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null;
  const focusWindow = focusId ? ws.windows[focusId] : undefined;
  const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1;
  // Every window's place: its slot, its pane, its reading rect and its card rect. Rendered in window-id
  // order, so reordering slots moves no element in the DOM (a moved iframe would reload its player).
  const windowPlaces = ws.desks.flatMap((each, rowIndex) => {
    const eachCam = camX[each.deskId] ?? 0;
    const rects = slotRects(each.slots.length, stage);
    const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage);
    return each.slots.flatMap((slot, index) => {
      const slotReading = { x: rects[index].x - eachCam, y: top + rects[index].y, w: rects[index].w, h: rects[index].h };
      const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading;
      const readingPanes = paneRects(slotReading, slot.length);
      const cardPanes = paneRects(slotCard, slot.length);
      return slot.flatMap((id, pane) => {
        const window = ws.windows[id];
        return window ? [{ window, each, rowIndex, index, pane, slot, reading: readingPanes[pane], card: cardPanes[pane] }] : [];
      });
    });
  }).sort((a, b) => (a.window.windowId < b.window.windowId ? -1 : a.window.windowId > b.window.windowId ? 1 : 0));

  // The slivers: the current desk's; while a zoom leaves the overview, the desk it lands on.
  const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk;
  const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam;
  const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) : { left: null, right: null };
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

  const hints = overview
    ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]]
    : focusMode
    ? [["alt+↵ / esc", "leave focus"], ["= − 0", "zoom"], ["alt+h/l", "next window"]]
    : [["alt+h/l", "window"], ["alt+j/k", "pane · desk"], ["alt+[ ]", "move"], ["alt+, .", "share · own slot"], ["alt+↵", "focus"], ["alt+w", "close"]];

  return (
    <div className={`desk-shell${focusMode ? " focus-mode" : ""}${overview ? " overview" : ""}${zooming ? " zooming" : ""}`} data-desk-shell="" data-focus-mode={focusMode ? "on" : "off"} data-overview={overview ? "on" : "off"}>
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
        <button type="button" className="tb" aria-pressed={overview} title="alt+o" onClick={() => toggleOverview()}>o overview</button>
        <button type="button" className="tb" aria-expanded={opener} onClick={() => setOpener((open) => !open)}>+ open beside</button>
        {onLeave ? <button type="button" className="tb" onClick={onLeave}>old Reader</button> : null}
      </header>
      <main className={`desk-main${viewportWidth < DESK_SIZES.shelfFoldBelow ? " rail" : ""}`} ref={mainRef}>
        <Shelf
          rows={shelfRows}
          folded={viewportWidth < DESK_SIZES.shelfFoldBelow}
          undo={undoShown ? { title: undoShown.title, onUndo: () => { commit(undoClose(wsRef.current, undoShown.deskId)); setUndo(null); } } : null}
          onFocus={(id) => {
            if (!deskId) return;
            // In the overview a row's click opens its window (and leaves the overview).
            if (overviewRef.current) toggleOverview({ deskId, windowId: id });
            else commit(setFocus(wsRef.current, deskId, id));
          }}
          onReorder={(id, toSlot) => {
            if (!deskId) return;
            commit(moveWindowTo(wsRef.current, deskId, id, toSlot));
          }}
        />
        <section
          className="desk-stage"
          ref={stageRef}
          data-desk-stage=""
          onPointerDown={onStagePointerDown}
          onPointerMove={onStagePointerMove}
          onPointerUp={onStagePointerUp}
        >
          <div className={`desk-world${panEase && overview ? " pan-ease" : ""}`} ref={worldRef} data-desk-world="">
            {/* One element per window, keyed by the window: pairing, unpairing and focus mode change its
                style, never its place in the tree, so the Reader inside is never remounted (its drafts,
                selection and scroll stay). */}
            {windowPlaces.map((place) => {
              const { window, each, rowIndex, index, pane, slot } = place;
              const id = window.windowId;
              const onCurrent = each.deskId === deskId;
              const opened = visited.has(each.deskId) || onCurrent;
              const full = !overview && onCurrent && focusMode && id === focusId;
              const hiddenInFocus = !overview && onCurrent && focusMode && !full;
              const reading = full ? { x: 0, y: 0, w: stage.width, h: stage.height } : place.reading;
              const card = place.card;
              const box = overview ? card : reading;
              const leavingTo = leaveTarget?.deskId === each.deskId;
              const slotCut = leavingTo
                ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index]
                : onCurrent ? visibility[index] : null;
              const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null;
              const lifecycle = lifecycles[id] ?? { windowId: id, state: "hidden" as const };
              const paused = isPaused(lifecycle.state);
              const paired = slot.length > 1;
              const selected = overview && selection !== null && slot.includes(selection.windowId);
              const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations);
              const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source;
              return (
                <div
                  key={id}
                  ref={(node) => {
                    if (node) boxEls.current.set(id, node);
                    else boxEls.current.delete(id);
                  }}
                  data-desk-slot={`${each.deskId}:${index}:${pane}`}
                  data-desk-slot-key={slotKey(each.deskId, slot)}
                  data-desk-slot-desk={each.deskId}
                  data-desk-slot-window={id}
                  className={`desk-window${!overview && onCurrent && id === focusId ? " focus" : ""}${full ? " focused-full" : ""}${paired && !full ? (pane === 0 ? " pair-top" : " pair-bottom") : ""}${paused ? " paused" : ""}${entering.has(id) ? " entering" : ""}${selected ? " ov-selected" : ""}${receding ? " ov-recede" : ""}`}
                  style={{
                    left: box.x,
                    top: box.y,
                    width: box.w,
                    height: box.h,
                    ...(mask ? { WebkitMaskImage: mask, maskImage: mask } : {}),
                    ...(hiddenInFocus ? { visibility: "hidden" as const } : {}),
                  }}
                >
                  {opened ? (
                    <div
                      className="desk-slot-inner"
                      ref={(node) => {
                        if (node) innerEls.current.set(id, node);
                        else innerEls.current.delete(id);
                      }}
                      style={{ width: reading.w, height: reading.h }}
                    >
                      <div
                        {...{ [WINDOW_ATTRIBUTE]: id }}
                        data-window-state={lifecycle.state}
                        data-window-kind={window.kind}
                        className={`desk-pane${paired && window.active ? " active-pane" : ""}`}
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
                              setUndo({ deskId: each.deskId, windowId: id, title, until: timers.now() + UNDO_CLOSE_MS });
                            }}
                          >
                            ✕
                          </button>
                        </div>
                        <div className="desk-pane-body" data-desk-pane-body="">
                          {/* A window that fails to render fails alone: the desk and its other windows stay. */}
                          <ScreenErrorBoundary resetKey={id}>
                          <WindowScope lifecycle={lifecycle} hub={hubFor(id)} claims={claimsFor(id)}>
                            {/* The measure wrapper is always there (focus mode only restyles it), so entering
                                focus mode never remounts the content. */}
                            <div
                              className="desk-measure"
                              style={{
                                ...(full ? { ["--desk-measure" as string]: `${measure}px`, zoom: focusZoom } : {}),
                                display: "flex",
                                flexDirection: "column",
                                minHeight: 0,
                                height: "100%",
                              } as CSSProperties}
                            >
                              {paneBody(window, lifecycle)}
                            </div>
                          </WindowScope>
                          </ScreenErrorBoundary>
                        </div>
                      </div>
                    </div>
                  ) : null}
                  {/* The card face: laid out at its overview size, scaled to the box it sits in (static per
                      layout; the zoom scales the box). */}
                  <div
                    className="desk-card"
                    ref={(node) => {
                      if (node) cardEls.current.set(id, node);
                      else cardEls.current.delete(id);
                    }}
                    style={{ width: card.w, height: card.h, transform: `scale(${box.w / card.w}, ${box.h / card.h})` }}
                  >
                    <CardFace
                      glyph={KIND_GLYPH[window.kind] ?? "§"}
                      kind={KIND_WORD[window.kind] ?? window.kind}
                      title={titleOf(window)}
                      where={status[id]?.where ?? null}
                      progress={typeof status[id]?.progress === "number" ? status[id].progress as number : null}
                      paper={window.kind === "source" || window.kind === "video"}
                      extra={window.stack ? <div className="desk-card-bands">{window.stack.map((entry, band) => <span key={band}>› {entry.kind === "pad" ? "pad" : "lesson"} {band + 1}</span>)}</div> : undefined}
                      miniatureHost={opened ? (node) => {
                        if (node) miniHosts.current.set(id, node);
                        else miniHosts.current.delete(id);
                      } : null}
                    />
                  </div>
                </div>
              );
            })}
            {overview || zooming ? (
              <>
                {ws.desks.map((each, rowIndex) => (
                  <div
                    key={`label-${each.deskId}`}
                    className="desk-ov-label"
                    ref={(node) => {
                      if (node) lateEls.current.set(`label-${each.deskId}`, node);
                      else lateEls.current.delete(`label-${each.deskId}`);
                    }}
                    style={{ left: ovLayout?.labels[rowIndex]?.x ?? 0, top: (ovLayout?.labels[rowIndex]?.y ?? 0) - 34 }}
                  >
                    {each.title}
                  </div>
                ))}
                {showRelations && links.length > 0 ? (
                  <div className="desk-ov-links" ref={(node) => { if (node) lateEls.current.set("links", node); else lateEls.current.delete("links"); }}>
                    <LinkLayer links={links} rects={linkRects} />
                  </div>
                ) : null}
                {/* Rings around the selection (amber) and its related cards (cyan, the top four): siblings laid
                    out at the cards' rects, so a zoom's last frame draws them exactly as the overview does. */}
                {ws.desks.flatMap((each, rowIndex) => each.slots.map((slot, index) => {
                  const ringId = linkedFrom;
                  const isSel = ringId !== null && slot.includes(ringId);
                  const isRel = !isSel && showRelations && slot.some((id) => selectedRelations.some((relation) => relation.windowId === id));
                  const rect = ovLayout?.cards[rowIndex]?.[index];
                  if ((!isSel && !isRel) || !rect) return null;
                  const key = slotKey(each.deskId, slot);
                  return (
                    <div
                      key={`ring-${key}`}
                      className={`desk-ov-ring ${isSel ? "sel" : "rel"}`}
                      ref={(node) => {
                        if (node) ringEls.current.set(key, node);
                        else ringEls.current.delete(key);
                      }}
                      style={{ left: rect.x, top: rect.y, width: rect.w, height: rect.h }}
                    />
                  );
                }))}
                {overview && gatherPreview ? ghosts.map((ghost) => (
                  <div key={ghost.key} className="desk-ov-ghost" style={{ left: ghost.rect.x, top: ghost.rect.y, width: ghost.rect.w, height: ghost.rect.h }} />
                )) : null}
              </>
            ) : null}
          </div>
          {sliverDesk && slivers.left !== null && (!overview || leaveTarget) ? (
            <Sliver side="l" title={titleOf(ws.windows[sliverDesk.slots[slivers.left][0]])} kind={ws.windows[sliverDesk.slots[slivers.left][0]]?.kind ?? "source"}
              register={(node) => { if (node) sliverEls.current.set("l", node); else sliverEls.current.delete("l"); }}
              onClick={() => commit(setFocus(wsRef.current, sliverDesk.deskId, sliverDesk.slots[slivers.left as number][0]))} />
          ) : null}
          {sliverDesk && slivers.right !== null && (!overview || leaveTarget) ? (
            <Sliver side="r" title={titleOf(ws.windows[sliverDesk.slots[slivers.right][0]])} kind={ws.windows[sliverDesk.slots[slivers.right][0]]?.kind ?? "source"}
              register={(node) => { if (node) sliverEls.current.set("r", node); else sliverEls.current.delete("r"); }}
              onClick={() => commit(setFocus(wsRef.current, sliverDesk.deskId, sliverDesk.slots[slivers.right as number][0]))} />
          ) : null}
          {movedShown && !overview ? (
            <div className="desk-sliver r desk-moved" role="status"><span className="sg">→</span><span className="st">moved to “{movedShown.title}”</span></div>
          ) : null}
          {desk && desk.slots.length === 0 && !overview ? (
            <div className="desk-panel desk-quiet" style={{ position: "absolute", left: DESK_SIZES.side, top: DESK_SIZES.inset }}>
              This desk is empty. <button type="button" onClick={() => setOpener(true)}>open a source beside</button>
            </div>
          ) : null}
          {hud ? <div className="desk-hud" role="status">{hud}</div> : null}
        </section>
      </main>
      <footer className="desk-keys">
        {hints.map(([keys, label]) => <span key={keys}><kbd>{keys}</kbd> {label}</span>)}
        {ungather && ungather.deskId === deskId && !overview ? (
          <button type="button" style={{ color: "var(--desk-cyan)" }} onClick={() => gather(false)}>↺ ungather</button>
        ) : null}
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

function Sliver({ side, title, kind, onClick, register }: { side: "l" | "r"; title: string; kind: string; onClick: () => void; register?: (node: HTMLButtonElement | null) => void }) {
  return (
    <button type="button" ref={register} className={`desk-sliver ${side}`} aria-label={`${side === "l" ? "previous" : "next"} window: ${title}`} onClick={onClick}>
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
        <div className="wkr"><span /><button type="button" style={{ textAlign: "left" }} onClick={() => onOpen(filter.trim() ? { kind: "compare", query: filter.trim() } : { kind: "panel", panel: "library" })}>⇄ compare{filter.trim() ? ` “${filter.trim()}”` : ""}</button></div>
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
