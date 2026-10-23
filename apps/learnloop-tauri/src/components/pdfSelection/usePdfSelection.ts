// How the learner selects on the original PDF (reader-pdf-selection): one
// interaction model over the selection model (model.ts).
//
// - A plain drag selects words from where it started to where the pointer is,
//   in the extraction's reading order, across columns, blocks and pages; it
//   paints live (no native selection, no jumps through column gaps).
// - A click on a formula, table or figure selects it whole; a click on text
//   places a caret (Shift+arrows extend from it); a double click selects a
//   word, a triple click its block; Shift+click extends. A click keeps the
//   Reader's capture, as on the extracted text (Esc, the rail's "clear" or a
//   new selection replaces it): reading on never loses what was selected.
// - Ctrl (or Cmd) + drag draws boxes, released Ctrl selects the words in
//   their union; Alt + drag sweeps whole blocks (UX §4.1's entry gestures).
// - Shift+arrows extend by a word or a line, Shift+Home/End to a line's ends
//   (from a caret, the first Shift+Left/Right takes the word at it; Home/End
//   go to the line's end at once); Esc clears, and in the middle of a drag or
//   a sweep it ends the gesture too (the release then selects nothing); Ctrl+C
//   copies the extraction's clean text (maths as LaTeX).
// - The Reader is told about a selection once it settles, 150 ms after the
//   mouse is released or the last key (spec §4.2: a drag in progress never
//   flickers the intent box). Nothing here moves focus except the learner's
//   own click on a page, which focuses the pages.

import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { screenLeavesKey } from "../../app/keymap";
import {
  blockAt,
  blockRange,
  hitTest,
  marqueeRanges,
  moveHead,
  onRanges,
  rangesFromNodes,
  samePos,
  selectionPayload,
  type HeadMove,
  type Pos,
  type SelRange,
  type SelectionModel,
  type SelectionPayload,
} from "./model";

/** The Reader waits this long after a mouse-up or the last key before taking
 *  the selection (the intent box's appearance delay, spec §4.2). */
export const SELECTION_SETTLE_MS = 150;

/** A selection the Reader holds (its capture), in the extracted text's shape. */
export interface HeldSelection {
  spanId: string;
  quote: string;
  nodes?: ReadonlyArray<{ spanId: string; quote: string; start?: number; end?: number }>;
}

export interface MarqueeBox {
  page: number;
  rect: number[];
}

/** A drawn box must have real extent: a bare ctrl+click is not a capture. */
const MARQUEE_MIN_EXTENT_PTS = 4;
/** A press that moves less than this is a click, not a drag. */
const DRAG_THRESHOLD_PX = 3;

const KEY_MOVES: Record<string, HeadMove> = {
  ArrowLeft: "left",
  ArrowRight: "right",
  ArrowUp: "up",
  ArrowDown: "down",
  Home: "lineStart",
  End: "lineEnd",
};

export interface PagePoint {
  page: number;
  x: number;
  y: number;
  pageEl: HTMLElement;
}

export interface PdfSelectionOptions {
  model: SelectionModel;
  containerRef: RefObject<HTMLDivElement | null>;
  /** The Reader's capture: painted until it is cleared or replaced. */
  selection: HeldSelection | null;
  activeSpan: string | null;
  /** The page under a client point (pages near the view only). */
  pointAt: (clientX: number, clientY: number) => PagePoint | null;
  onTextSelection: (selection: SelectionPayload) => void;
  onSelectionCleared?: () => void;
  /** A saved highlight under a point, which a click opens instead of clearing. */
  highlightAt?: (point: PagePoint) => string | null;
  /** A click opened a highlight (where it was clicked: its chip goes there),
   *  or closed the open one (null). */
  onHighlightClick?: (id: string | null, point?: PagePoint) => void;
  /** The first page a keyboard selection may start on (the top of the view). */
  firstShownPage?: () => number | null;
  /** Bring a block into view (a keyboard selection moving past the view). */
  revealBlock?: (block: number) => void;
  /** Reader RW5a: the figure a single Ctrl+drag box lies inside, if any. The
   *  box is then a region of that figure (its words, if any, are not taken). */
  regionAt?: (box: MarqueeBox) => { spanId: string; quote: string; end: number } | null;
}

function editable(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || Boolean(target.closest("input, textarea, select")));
}

function isUi(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && Boolean(target.closest("button, input, textarea, select, a, [data-pdf-ui]"));
}

export function usePdfSelection(options: PdfSelectionOptions) {
  const { model, containerRef, selection, activeSpan, pointAt, onTextSelection, onSelectionCleared, highlightAt, onHighlightClick, firstShownPage, revealBlock, regionAt } = options;
  const pressRef = useRef<{
    point: PagePoint;
    pos: Pos | null;
    clientX: number;
    clientY: number;
    clicks: number;
    moved: boolean;
    anchor: Pos | null;
    highlight: string | null;
  } | null>(null);
  // The live selection (a drag, keys, a settling commit); null shows the
  // Reader's capture.
  const [live, setLive] = useState<SelRange[] | null>(null);
  const liveRef = useRef<SelRange[] | null>(null);
  const [caret, setCaret] = useState<Pos | null>(null);
  const caretRef = useRef<Pos | null>(null);
  const goalXRef = useRef<number | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const settleRef = useRef<number | null>(null);
  // The ranges behind the last selection handed over, by identity.
  const committedRef = useRef<{ payload: SelectionPayload; ranges: SelRange[] } | null>(null);
  const callbacks = useRef({ onTextSelection, onSelectionCleared, onHighlightClick, highlightAt, pointAt, firstShownPage, revealBlock, regionAt });
  callbacks.current = { onTextSelection, onSelectionCleared, onHighlightClick, highlightAt, pointAt, firstShownPage, revealBlock, regionAt };

  const held = useMemo<SelRange[]>(() => {
    if (!selection) return [];
    const committed = committedRef.current;
    if (committed && (committed.payload === selection || committed.payload.nodes === selection.nodes)) return committed.ranges;
    return rangesFromNodes(model, selection.nodes && selection.nodes.length ? selection.nodes : [{ spanId: selection.spanId }]);
  }, [selection, model]);

  const painted = live ?? held;
  const paintedRef = useRef(painted);
  paintedRef.current = painted;

  const showLive = useCallback((ranges: SelRange[] | null) => {
    liveRef.current = ranges;
    setLive(ranges);
  }, []);

  const placeCaret = useCallback((pos: Pos | null) => {
    caretRef.current = pos;
    setCaret(pos);
  }, []);

  const cancelSettle = useCallback(() => {
    if (settleRef.current !== null) {
      window.clearTimeout(settleRef.current);
      settleRef.current = null;
    }
  }, []);

  /** Hand the selection over once it settles. */
  const settle = useCallback(
    (ranges: SelRange[]) => {
      cancelSettle();
      settleRef.current = window.setTimeout(() => {
        settleRef.current = null;
        const payload = selectionPayload(model, ranges);
        if (!payload) return;
        committedRef.current = { payload, ranges };
        const words = payload.quote.split(/\s+/).filter(Boolean);
        setAnnouncement(`Selected: ${words.slice(0, 12).join(" ")}${words.length > 12 ? "…" : ""}`);
        showLive(null);
        callbacks.current.onTextSelection(payload);
      }, SELECTION_SETTLE_MS);
    },
    [model, cancelSettle, showLive],
  );

  const clear = useCallback(
    (notify = true) => {
      cancelSettle();
      const had = paintedRef.current.length > 0;
      committedRef.current = null;
      showLive(selection ? [] : null);
      if (had) setAnnouncement("Selection cleared");
      if (notify && had) callbacks.current.onSelectionCleared?.();
    },
    [cancelSettle, showLive, selection],
  );

  // The Reader cleared, replaced or restored its capture (a return, an edit):
  // show its own, unless the learner is in the middle of a selection.
  useEffect(() => {
    if (!pressRef.current && settleRef.current === null) showLive(null);
  }, [selection, showLive]);

  useEffect(() => () => cancelSettle(), [cancelSettle]);

  // ---- the pointer ----------------------------------------------------------------

  const [pressing, setPressing] = useState(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const frameRef = useRef<number | null>(null);
  // An Alt + drag's first block (declared here: Esc ends it with a press).
  const sweepRef = useRef<{ anchor: number } | null>(null);
  const [sweeping, setSweeping] = useState(false);

  /** End a press or a sweep in progress (Esc, Codex review F6): no frame
   *  still to draw, no auto-scroll, and the release that follows selects
   *  nothing. */
  const cancelGesture = useCallback((): boolean => {
    const active = pressRef.current !== null || sweepRef.current !== null;
    pressRef.current = null;
    sweepRef.current = null;
    lastPointRef.current = null;
    if (frameRef.current !== null) {
      window.cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    setPressing(false);
    setSweeping(false);
    return active;
  }, []);

  const extendTo = useCallback(
    (anchor: Pos, clientX: number, clientY: number) => {
      const point = callbacks.current.pointAt(clientX, clientY);
      if (!point) return; // between pages: the head keeps its place
      const head = hitTest(model, point.page, point.x, point.y);
      if (!head) return;
      const current = liveRef.current?.[0];
      if (current && samePos(current.anchor, anchor) && samePos(current.head, head) && liveRef.current?.length === 1) return;
      showLive([{ anchor, head }]);
    },
    [model, showLive],
  );

  const onPlainMouseDown = useCallback(
    (event: React.MouseEvent): boolean => {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.altKey || isUi(event.target)) return false;
      const point = callbacks.current.pointAt(event.clientX, event.clientY);
      if (!point) return false;
      // The pages own this press: no native selection, and the learner's
      // click brings the keyboard to the pages (nothing else moves focus).
      event.preventDefault();
      window.getSelection()?.removeAllRanges();
      containerRef.current?.focus({ preventScroll: true });
      cancelSettle();
      const pos = hitTest(model, point.page, point.x, point.y);
      // Shift+click extends from the caret a click left, else from what is painted.
      const from = caretRef.current ?? (paintedRef.current.length ? paintedRef.current[paintedRef.current.length - 1].anchor : null);
      if (event.shiftKey && from && pos) {
        // Shift+click extends what is there.
        pressRef.current = { point, pos, clientX: event.clientX, clientY: event.clientY, clicks: 1, moved: true, anchor: from, highlight: null };
        showLive([{ anchor: from, head: pos }]);
      } else {
        pressRef.current = {
          point,
          pos,
          clientX: event.clientX,
          clientY: event.clientY,
          clicks: event.detail || 1,
          moved: false,
          anchor: pos,
          highlight: callbacks.current.highlightAt?.(point) ?? null,
        };
      }
      lastPointRef.current = { x: event.clientX, y: event.clientY };
      setPressing(true);
      return true;
    },
    [model, containerRef, cancelSettle, showLive],
  );

  useEffect(() => {
    if (!pressing) return;
    const flushMove = () => {
      frameRef.current = null;
      const press = pressRef.current;
      const point = lastPointRef.current;
      if (!press || !point || !press.anchor) return;
      extendTo(press.anchor, point.x, point.y);
    };
    const onMove = (event: MouseEvent) => {
      const press = pressRef.current;
      if (!press) return;
      lastPointRef.current = { x: event.clientX, y: event.clientY };
      if (!press.moved) {
        if (Math.abs(event.clientX - press.clientX) + Math.abs(event.clientY - press.clientY) <= DRAG_THRESHOLD_PX) return;
        press.moved = true;
        if (!press.anchor) {
          // Pressed in a margin: the drag starts at the first word it reaches.
          const point = callbacks.current.pointAt(event.clientX, event.clientY);
          press.anchor = point ? hitTest(model, point.page, point.x, point.y) : null;
        }
        placeCaret(null);
        callbacks.current.onHighlightClick?.(null);
      }
      // One update per frame however fast the pointer moves.
      if (frameRef.current === null) frameRef.current = window.requestAnimationFrame(flushMove);
    };
    const onUp = () => {
      const press = pressRef.current;
      pressRef.current = null;
      setPressing(false);
      if (frameRef.current !== null) {
        window.cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
      if (!press) return;
      if (press.moved) {
        if (press.anchor && lastPointRef.current) extendTo(press.anchor, lastPointRef.current.x, lastPointRef.current.y);
        const ranges = liveRef.current;
        if (ranges && ranges.length) settle(ranges);
        return;
      }
      // A click.
      const pos = press.pos;
      if (press.clicks >= 3 && pos) {
        const range = blockRange(model, pos.block);
        showLive([range]);
        settle([range]);
        return;
      }
      if (press.clicks === 2 && pos) {
        const range = { anchor: pos, head: pos };
        showLive([range]);
        settle([range]);
        return;
      }
      if (press.highlight) {
        callbacks.current.onHighlightClick?.(press.highlight, press.point);
        return;
      }
      if (pos && model.blocks[pos.block].atomic) {
        // A formula, table or figure: one click selects it whole.
        const range = { anchor: pos, head: pos };
        placeCaret(null);
        showLive([range]);
        settle([range]);
        return;
      }
      callbacks.current.onHighlightClick?.(null);
      placeCaret(pos);
      goalXRef.current = null;
      // A selection still settling is dropped; the Reader's capture stays.
      if (liveRef.current !== null) showLive(null);
    };
    // Auto-scroll while the pointer rests near the scroller's edge.
    const scroller = (() => {
      let node: HTMLElement | null = containerRef.current?.parentElement ?? null;
      while (node) {
        if (/(auto|scroll)/.test(window.getComputedStyle(node).overflowY)) return node;
        node = node.parentElement;
      }
      return null;
    })();
    const timer = window.setInterval(() => {
      const point = lastPointRef.current;
      const press = pressRef.current;
      if (!point || !scroller || !press?.moved || !press.anchor) return;
      const rect = scroller.getBoundingClientRect();
      const zone = 48;
      const delta =
        point.y < rect.top + zone ? -Math.ceil((rect.top + zone - point.y) / 3) : point.y > rect.bottom - zone ? Math.ceil((point.y - (rect.bottom - zone)) / 3) : 0;
      if (delta !== 0) {
        scroller.scrollTop += delta;
        extendTo(press.anchor, point.x, point.y);
      }
    }, 40);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [pressing, model, containerRef, extendTo, settle, showLive, placeCaret]);

  // ---- Alt + drag: whole blocks ---------------------------------------------------

  const onSweepMouseDown = useCallback(
    (event: React.MouseEvent): boolean => {
      if (event.button !== 0 || !event.altKey || event.ctrlKey || event.metaKey || isUi(event.target)) return false;
      const point = callbacks.current.pointAt(event.clientX, event.clientY);
      if (!point) return false;
      const block = blockAt(model, point.page, point.x, point.y);
      if (block === null) return false;
      event.preventDefault();
      window.getSelection()?.removeAllRanges();
      cancelSettle();
      sweepRef.current = { anchor: block };
      lastPointRef.current = { x: event.clientX, y: event.clientY };
      const range = { anchor: { block, unit: 0 }, head: blockRange(model, block).head };
      showLive([range]);
      setSweeping(true);
      return true;
    },
    [model, cancelSettle, showLive],
  );

  useEffect(() => {
    if (!sweeping) return;
    const onMove = (event: MouseEvent) => {
      const sweep = sweepRef.current;
      if (!sweep) return;
      const point = callbacks.current.pointAt(event.clientX, event.clientY);
      if (!point) return;
      const block = blockAt(model, point.page, point.x, point.y);
      if (block === null) return;
      const lo = Math.min(sweep.anchor, block);
      const hi = Math.max(sweep.anchor, block);
      showLive([{ anchor: { block: lo, unit: 0 }, head: blockRange(model, hi).head }]);
    };
    const onUp = () => {
      // Ended already (Esc): the release selects nothing.
      if (!sweepRef.current) return;
      sweepRef.current = null;
      setSweeping(false);
      const ranges = liveRef.current;
      if (ranges && ranges.length) settle(ranges);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [sweeping, model, settle, showLive]);

  // ---- Ctrl + drag: boxes ----------------------------------------------------------

  const [marqueeBoxes, setMarqueeBoxes] = useState<MarqueeBox[]>([]);
  const [marqueeDraft, setMarqueeDraft] = useState<MarqueeBox | null>(null);
  const [marqueeArmed, setMarqueeArmed] = useState(false);
  const marqueeBoxesRef = useRef<MarqueeBox[]>([]);
  const marqueeDragRef = useRef<{ page: number; pageEl: HTMLElement; x0: number; y0: number } | null>(null);
  const clearMarquee = useCallback(() => {
    marqueeDragRef.current = null;
    marqueeBoxesRef.current = [];
    setMarqueeDraft(null);
    setMarqueeBoxes([]);
  }, []);

  const commitMarquee = useCallback(() => {
    const boxes = marqueeBoxesRef.current;
    if (!boxes.length) return;
    clearMarquee();
    // Reader RW5a: one box inside a figure is a region of that figure.
    const region = boxes.length === 1 ? callbacks.current.regionAt?.(boxes[0]) ?? null : null;
    if (region) {
      const box = boxes[0];
      cancelSettle();
      settleRef.current = window.setTimeout(() => {
        settleRef.current = null;
        setAnnouncement(`Selected a region of ${region.quote || "the figure"}`);
        showLive(null);
        callbacks.current.onTextSelection({
          spanId: region.spanId, quote: region.quote, nodes: [{ spanId: region.spanId, quote: region.quote, start: 0, end: region.end }],
          text: region.quote, region: { spanId: region.spanId, page: box.page, bbox: [...box.rect] },
        });
      }, SELECTION_SETTLE_MS);
      return;
    }
    const ranges = marqueeRanges(model, boxes);
    if (!ranges.length) return;
    showLive(ranges);
    settle(ranges);
  }, [model, clearMarquee, showLive, settle, cancelSettle]);
  const commitMarqueeRef = useRef(commitMarquee);
  commitMarqueeRef.current = commitMarquee;

  const onMarqueeMouseDown = useCallback(
    (event: React.MouseEvent): boolean => {
      if (event.button !== 0 || !(event.ctrlKey || event.metaKey) || isUi(event.target)) return false;
      const point = callbacks.current.pointAt(event.clientX, event.clientY);
      if (!point) return false;
      event.preventDefault();
      window.getSelection()?.removeAllRanges();
      cancelSettle();
      setMarqueeArmed(true);
      marqueeDragRef.current = { page: point.page, pageEl: point.pageEl, x0: point.x, y0: point.y };
      setMarqueeDraft({ page: point.page, rect: [point.x, point.y, point.x, point.y] });
      return true;
    },
    [cancelSettle],
  );

  const marqueeDrafting = marqueeDraft !== null;
  useEffect(() => {
    if (!marqueeDrafting) return;
    const toPage = (drag: { pageEl: HTMLElement }, clientX: number, clientY: number): [number, number] | null => {
      const widthPoints = Number(drag.pageEl.dataset.widthPoints);
      const rect = drag.pageEl.getBoundingClientRect();
      if (!rect.width || !widthPoints) return null;
      const scale = rect.width / widthPoints;
      return [Math.min(Math.max((clientX - rect.left) / scale, 0), widthPoints), Math.min(Math.max((clientY - rect.top) / scale, 0), rect.height / scale)];
    };
    const draft = (drag: { x0: number; y0: number }, point: [number, number]) => [
      Math.min(drag.x0, point[0]),
      Math.min(drag.y0, point[1]),
      Math.max(drag.x0, point[0]),
      Math.max(drag.y0, point[1]),
    ];
    const onMove = (event: MouseEvent) => {
      const drag = marqueeDragRef.current;
      if (!drag) return;
      const point = toPage(drag, event.clientX, event.clientY);
      if (point) setMarqueeDraft({ page: drag.page, rect: draft(drag, point) });
    };
    const onUp = (event: MouseEvent) => {
      const drag = marqueeDragRef.current;
      marqueeDragRef.current = null;
      setMarqueeDraft(null);
      if (!drag) return;
      const point = toPage(drag, event.clientX, event.clientY);
      if (!point) return;
      const rect = draft(drag, point);
      if (rect[2] - rect[0] < MARQUEE_MIN_EXTENT_PTS || rect[3] - rect[1] < MARQUEE_MIN_EXTENT_PTS) return;
      const next = [...marqueeBoxesRef.current, { page: drag.page, rect }];
      marqueeBoxesRef.current = next;
      setMarqueeBoxes(next);
      // Ctrl already released mid-drag: this box completes the gesture.
      if (!(event.ctrlKey || event.metaKey)) commitMarqueeRef.current();
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [marqueeDrafting]);

  // Releasing Ctrl commits the union; Esc abandons it.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if (event.key === "Control" || event.key === "Meta") setMarqueeArmed(true);
      if (event.key === "Escape" && (marqueeBoxesRef.current.length || marqueeDragRef.current)) clearMarquee();
    };
    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key !== "Control" && event.key !== "Meta") return;
      setMarqueeArmed(false);
      if (!marqueeDragRef.current) commitMarqueeRef.current();
    };
    const onBlur = () => setMarqueeArmed(false);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", onBlur);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      window.removeEventListener("blur", onBlur);
    };
  }, [clearMarquee]);

  // ---- keys ---------------------------------------------------------------------

  const keyboardStart = useCallback((): Pos | null => {
    if (caretRef.current) return caretRef.current;
    const active = activeSpan ? model.blockIndex(activeSpan) : undefined;
    if (active !== undefined && model.unitCount(active) > 0) return { block: active, unit: 0 };
    const page = callbacks.current.firstShownPage?.() ?? null;
    const onPage = page !== null ? model.blocksOnPage(page) : [];
    const first = onPage.find((block) => model.unitCount(block) > 0) ?? (model.blocks.length ? 0 : undefined);
    return first === undefined ? null : { block: first, unit: 0 };
  }, [model, activeSpan]);

  // Esc in the middle of a drag or a sweep ends it, wherever the keyboard is
  // (an Alt + drag never moved it to the pages), before anything else sees
  // the key: the release that follows selects nothing.
  useEffect(() => {
    if (!pressing && !sweeping) return;
    const onEscape = (event: KeyboardEvent) => {
      if (screenLeavesKey(event)) return;
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      cancelGesture();
      clear();
    };
    window.addEventListener("keydown", onEscape, true);
    return () => window.removeEventListener("keydown", onEscape, true);
  }, [pressing, sweeping, cancelGesture, clear]);

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (editable(event.target)) return;
      if (event.key === "Escape") {
        const gesture = cancelGesture();
        if (gesture || paintedRef.current.length) {
          event.preventDefault();
          clear();
        }
        return;
      }
      const move = KEY_MOVES[event.key];
      if (!move || !event.shiftKey || event.altKey || event.ctrlKey || event.metaKey) return;
      event.preventDefault();
      // A caret placed by a click starts a new selection there (the capture
      // stays until it is replaced); otherwise the painted one extends.
      const current = caretRef.current ? [] : paintedRef.current;
      const last = current[current.length - 1];
      const anchor = last ? last.anchor : keyboardStart();
      if (!anchor) return;
      const vertical = move === "up" || move === "down";
      let head: Pos;
      if (!last && (move === "left" || move === "right")) {
        // The first Shift+Left/Right from a caret selects the word at it
        // (Shift+Home/End go to the line's end at once, Codex review F7).
        head = anchor;
        goalXRef.current = null;
      } else {
        const moved = moveHead(model, last ? last.head : anchor, move, vertical ? goalXRef.current : null);
        head = moved.pos;
        goalXRef.current = vertical ? moved.goalX : null;
      }
      const ranges = [{ anchor, head }];
      placeCaret(null);
      showLive(ranges);
      settle(ranges);
      callbacks.current.revealBlock?.(head.block);
    },
    [model, clear, cancelGesture, keyboardStart, placeCaret, showLive, settle],
  );

  // Ctrl+C copies the extraction's text of what is painted, unless the
  // learner has a native selection elsewhere (the rail, a text field).
  useEffect(() => {
    const onCopy = (event: ClipboardEvent) => {
      const ranges = paintedRef.current;
      if (!ranges.length || editable(document.activeElement)) return;
      const native = window.getSelection();
      if (native && !native.isCollapsed && native.toString().trim()) return;
      const payload = selectionPayload(model, ranges);
      if (!payload || !event.clipboardData) return;
      event.clipboardData.setData("text/plain", payload.text);
      event.preventDefault();
    };
    document.addEventListener("copy", onCopy);
    return () => document.removeEventListener("copy", onCopy);
  }, [model]);

  /** The selection a right-click lands in (for the tag menu), else null. */
  const selectionUnder = useCallback(
    (point: PagePoint): SelectionPayload | null => {
      const ranges = paintedRef.current;
      if (!ranges.length || !onRanges(model, ranges, point.page, point.x, point.y)) return null;
      return selectionPayload(model, ranges);
    },
    [model],
  );

  const onMouseDown = useCallback(
    (event: React.MouseEvent) => {
      if (onMarqueeMouseDown(event)) return;
      if (onSweepMouseDown(event)) return;
      onPlainMouseDown(event);
    },
    [onMarqueeMouseDown, onSweepMouseDown, onPlainMouseDown],
  );

  return {
    painted,
    caret,
    announcement,
    pressing,
    sweeping,
    marqueeBoxes,
    marqueeDraft,
    marqueeArmed,
    onMouseDown,
    onKeyDown,
    selectionUnder,
    clear,
  };
}
