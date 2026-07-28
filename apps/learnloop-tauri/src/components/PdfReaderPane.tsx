// PdfReaderPane — Tier-2 embedded original-PDF reader.
//
// Renders the revision's original PDF (served from the vault's content-addressed
// originals store through the llpdf:// protocol) with pdf.js: canvas + selectable
// text layer per page, rendered lazily as pages scroll into view. Only pages the
// extraction actually covers are shown (a whole textbook may back a chapter-scoped
// ingest), with honest gap markers between non-adjacent pages. Block geometry from
// reader.pdf_view (PDF points, origin top-left — marker's bbox space) is overlaid
// per page.
//
// Selection: a plain drag is native browser-style glyph selection over the
// PDF's own embedded text layer — the original text is the quote source, with
// one exception: text falling in an Equation block substitutes the block's
// extraction LaTeX (equation glyphs are junk or absent). Ctrl+drag draws one
// or more marquee boxes; releasing ctrl commits their union as the selection
// (word-clipped glyphs per box, Equation blocks whole, extraction-text
// fallback where no glyphs exist — scanned pages). Alt+drag sweeps whole
// extraction blocks with their extraction text verbatim. Extraction blocks are
// an ingestion artifact: selections anchor onto them behind the scenes, but
// there is no block-level click/hover interaction to learn.

import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import * as pdfjs from "pdfjs-dist";
import type { PDFDocumentProxy } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import "pdfjs-dist/web/pdf_viewer.css";
import type { ReaderPdfBlockDto } from "../api/dto";
import type { AnnotationTrail } from "../screens/ReaderScreen";
import { COLOR, Faint, FONT_MONO } from "./term";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

interface PageGeometry {
  widthPoints: number;
  heightPoints: number;
}

// Trail washes multiply over the white page like marker pen; highlights are
// amber, every other capture kind (asks, commits, marks) reads as violet.
const TRAIL_COLORS: Record<string, { wash: string; edge: string }> = {
  highlight: { wash: "rgba(245, 166, 35, 0.22)", edge: "rgba(215, 135, 15, 0.8)" },
  other: { wash: "rgba(147, 112, 219, 0.18)", edge: "rgba(120, 85, 200, 0.75)" },
};

// Page furniture never joins a sweep: running heads/footers repeat every page
// and would pollute a selection crossing a page boundary.
const FURNITURE_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"]);

function isSelectable(block: ReaderPdfBlockDto): boolean {
  return !FURNITURE_TYPES.has(block.blockType ?? "") && (block.text ?? "").trim().length > 0;
}

// ---- ctrl-marquee union capture helpers -----------------------------------

/** One marquee box, anchored to a page in PDF points (stable across zoom). */
interface MarqueeBox {
  page: number;
  rect: number[]; // [x0, y0, x1, y1]
}

/** A drawn box must have real extent — a bare ctrl+click is not a capture. */
const MARQUEE_MIN_EXTENT_PTS = 4;

function rectOverlap(a: number[], b: number[]): number {
  const w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]);
  const h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]);
  return w > 0 && h > 0 ? w * h : 0;
}

function rectArea(r: number[]): number {
  return Math.max(0, r[2] - r[0]) * Math.max(0, r[3] - r[1]);
}

const EMPTY_SPANS = new Set<string>();

/** A right-click tag request: where to show the menu and what it would tag —
 *  a selection's quote, or the whole block when quote is null. */
export interface TagMenuRequest {
  x: number;
  y: number;
  spanId: string;
  quote: string | null;
}

/** Imperative surface for the screen: jump to an annotation's page/block. */
export interface PdfReaderPaneHandle {
  scrollToSegment: (page: number, spanId?: string | null) => void;
}

interface PdfReaderPaneProps {
  fileUrl: string;
  blocks: ReaderPdfBlockDto[];
  trails: AnnotationTrail[];
  /** Personalized second-pass passages revealed by the learner at a section break. */
  guidanceSpans: Set<string>;
  /** Blocks of the committed selection — stay painted until the capture is cleared. */
  selectedSpans: Set<string>;
  activeSpan: string | null;
  onTextSelection: (selection: {
    spanId: string;
    quote: string;
    nodes: Array<{ spanId: string; quote: string; prefix?: string; suffix?: string }>;
  }) => void;
  onTagMenu: (request: TagMenuRequest) => void;
  onError: (message: string) => void;
}

interface FindMatch {
  page: number;
  ordinal: number;
}

export const PdfReaderPane = forwardRef<PdfReaderPaneHandle, PdfReaderPaneProps>(function PdfReaderPane(
  { fileUrl, blocks, trails, guidanceSpans, selectedSpans, activeSpan, onTextSelection, onTagMenu, onError }: PdfReaderPaneProps,
  handleRef,
) {
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null);
  const [zoom, setZoom] = useState(1);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);
  // Ctrl+F find state: matches are computed from pdf.js text content per covered
  // page (cached after first search); text-layer spans containing the query get
  // a .ll-find-hit wash once their page renders.
  const [findOpen, setFindOpen] = useState(false);
  const [findQuery, setFindQuery] = useState("");
  const [matches, setMatches] = useState<FindMatch[]>([]);
  const [matchIdx, setMatchIdx] = useState(0);
  const pageTextsRef = useRef<Map<number, string>>(new Map());
  const findInputRef = useRef<HTMLInputElement | null>(null);

  const clampZoom = (value: number) => Math.min(2.5, Math.max(0.5, Math.round(value * 100) / 100));
  const zoomIn = useCallback(() => setZoom((z) => clampZoom(z + 0.15)), []);
  const zoomOut = useCallback(() => setZoom((z) => clampZoom(z - 0.15)), []);

  const openFind = useCallback(() => {
    setFindOpen(true);
    requestAnimationFrame(() => findInputRef.current?.select());
  }, []);
  const closeFind = useCallback(() => {
    setFindOpen(false);
    setFindQuery("");
  }, []);

  // Pages the extraction covers, ascending (block.page is the 0-based index
  // into the full original PDF; pdf.js pages are 1-based).
  const coveredPages = useMemo(
    () => [...new Set(blocks.map((b) => b.page))].sort((a, b) => a - b),
    [blocks],
  );
  const blocksByPage = useMemo(() => {
    const map = new Map<number, ReaderPdfBlockDto[]>();
    for (const block of blocks) {
      const list = map.get(block.page) ?? [];
      list.push(block);
      map.set(block.page, list);
    }
    return map;
  }, [blocks]);
  const trailsByPage = useMemo(() => {
    const map = new Map<number, AnnotationTrail[]>();
    for (const trail of trails) {
      const list = map.get(trail.page) ?? [];
      list.push(trail);
      map.set(trail.page, list);
    }
    return map;
  }, [trails]);

  useEffect(() => {
    let cancelled = false;
    let task: ReturnType<typeof pdfjs.getDocument> | null = null;
    (async () => {
      try {
        const response = await fetch(fileUrl);
        if (!response.ok) throw new Error(`originals store returned ${response.status}`);
        const data = new Uint8Array(await response.arrayBuffer());
        task = pdfjs.getDocument({ data });
        const loaded = await task.promise;
        if (!cancelled) setDoc(loaded);
      } catch (error) {
        if (!cancelled) onError(`could not load original PDF: ${error instanceof Error ? error.message : String(error)}`);
      }
    })();
    return () => {
      cancelled = true;
      void task?.destroy();
      setDoc(null);
    };
  }, [fileUrl, onError]);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    const observer = new ResizeObserver(() => setContainerWidth(node.clientWidth));
    observer.observe(node);
    setContainerWidth(node.clientWidth);
    return () => observer.disconnect();
  }, []);

  // The document changed: page-text search cache is stale.
  useEffect(() => {
    pageTextsRef.current = new Map();
  }, [doc]);

  // Compute find matches (debounced) over the covered pages' text content.
  useEffect(() => {
    if (!doc || !findQuery.trim()) {
      setMatches([]);
      setMatchIdx(0);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      const query = findQuery.trim().toLowerCase();
      const found: FindMatch[] = [];
      for (const page of coveredPages) {
        let text = pageTextsRef.current.get(page);
        if (text === undefined) {
          try {
            const pdfPage = await doc.getPage(page + 1);
            const content = await pdfPage.getTextContent();
            text = content.items
              .map((item) => ("str" in item ? item.str : ""))
              .join(" ")
              .replace(/\s+/g, " ")
              .toLowerCase();
          } catch {
            text = "";
          }
          pageTextsRef.current.set(page, text);
        }
        if (cancelled) return;
        let from = 0;
        let ordinal = 0;
        while (true) {
          const at = text.indexOf(query, from);
          if (at === -1) break;
          found.push({ page, ordinal });
          ordinal += 1;
          from = at + Math.max(1, query.length);
        }
      }
      if (!cancelled) {
        setMatches(found);
        setMatchIdx(0);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [doc, findQuery, coveredPages]);

  const scrollToMatch = useCallback((match: FindMatch) => {
    const pageEl = containerRef.current?.querySelector(`[data-pdf-page="${match.page}"]`);
    if (!(pageEl instanceof HTMLElement)) return;
    // Prefer the nth marked text-layer hit when the page has rendered.
    const hits = pageEl.querySelectorAll(".ll-find-hit");
    const target = hits[Math.min(match.ordinal, Math.max(0, hits.length - 1))];
    (target instanceof HTMLElement ? target : pageEl).scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  useEffect(() => {
    const current = matches[matchIdx];
    if (current) scrollToMatch(current);
  }, [matchIdx, matches, scrollToMatch]);

  const gotoMatch = useCallback(
    (delta: number) => {
      setMatchIdx((i) => (matches.length ? (i + delta + matches.length) % matches.length : 0));
    },
    [matches.length],
  );

  // Standard chrome keys while the pane is mounted: ctrl+f find, ctrl+±/0 zoom.
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const modifier = event.ctrlKey || event.metaKey;
      if (modifier && event.key.toLowerCase() === "f") {
        event.preventDefault();
        openFind();
        return;
      }
      const editing = event.target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(event.target.tagName);
      if (editing || !modifier) return;
      if (event.key === "=" || event.key === "+") {
        event.preventDefault();
        zoomIn();
      } else if (event.key === "-") {
        event.preventDefault();
        zoomOut();
      } else if (event.key === "0") {
        event.preventDefault();
        setZoom(1);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [openFind, zoomIn, zoomOut]);

  // Ctrl+wheel zoom needs a non-passive listener to preventDefault.
  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    const onWheel = (event: WheelEvent) => {
      if (!event.ctrlKey) return;
      event.preventDefault();
      setZoom((z) => clampZoom(z * (event.deltaY < 0 ? 1.1 : 0.9)));
    };
    node.addEventListener("wheel", onWheel, { passive: false });
    return () => node.removeEventListener("wheel", onWheel);
  }, [doc]);

  const scrollToSegment = useCallback((page: number, spanId?: string | null) => {
    const pageEl = containerRef.current?.querySelector(`[data-pdf-page="${page}"]`);
    if (!(pageEl instanceof HTMLElement)) return;
    // The block overlay exists once the page has rendered; otherwise the lazy
    // page placeholder is close enough and rendering catches up on arrival.
    const target = spanId ? pageEl.querySelector(`[data-span-id="${spanId}"]`) : null;
    (target instanceof HTMLElement ? target : pageEl).scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  useImperativeHandle(handleRef, () => ({ scrollToSegment }), [scrollToSegment]);

  // Map a DOM point inside a page wrapper to PDF points and hit-test blocks.
  const blockAtPoint = useCallback(
    (pageEl: HTMLElement, clientX: number, clientY: number): ReaderPdfBlockDto | null => {
      const page = Number(pageEl.dataset.pdfPage);
      const widthPoints = Number(pageEl.dataset.widthPoints);
      const rect = pageEl.getBoundingClientRect();
      if (!rect.width || !widthPoints) return null;
      const scale = rect.width / widthPoints;
      const x = (clientX - rect.left) / scale;
      const y = (clientY - rect.top) / scale;
      const candidates = (blocksByPage.get(page) ?? []).filter(
        (b) => b.bbox.length === 4 && x >= b.bbox[0] && x <= b.bbox[2] && y >= b.bbox[1] && y <= b.bbox[3],
      );
      if (candidates.length === 0) return null;
      // Smallest containing region wins (a figure block can enclose a caption).
      candidates.sort(
        (a, b) =>
          (a.bbox[2] - a.bbox[0]) * (a.bbox[3] - a.bbox[1]) - (b.bbox[2] - b.bbox[0]) * (b.bbox[3] - b.bbox[1]),
      );
      return candidates[0];
    },
    [blocksByPage],
  );

  const pageElFor = (node: Node | null): HTMLElement | null => {
    let current: Node | null = node;
    while (current) {
      if (current instanceof HTMLElement && current.dataset.pdfPage !== undefined) return current;
      current = current.parentNode;
    }
    return null;
  };

  // ---- block-snapped sweep selection -------------------------------------
  // `blocks` arrives in reading order (sidecar sorts by ordinal), so a sweep is
  // just an index range; page boundaries need no special casing.
  const indexBySpan = useMemo(() => new Map(blocks.map((b, i) => [b.spanId, i] as const)), [blocks]);
  const blockBySpan = useMemo(() => new Map(blocks.map((b) => [b.spanId, b] as const)), [blocks]);

  // Forgiving hit target while sweeping: the containing selectable block, else
  // the nearest selectable block on the page (margins/gutters keep tracking).
  const blockNearPoint = useCallback(
    (pageEl: HTMLElement, clientX: number, clientY: number): ReaderPdfBlockDto | null => {
      const direct = blockAtPoint(pageEl, clientX, clientY);
      if (direct && isSelectable(direct)) return direct;
      const page = Number(pageEl.dataset.pdfPage);
      const widthPoints = Number(pageEl.dataset.widthPoints);
      const rect = pageEl.getBoundingClientRect();
      if (!rect.width || !widthPoints) return null;
      const scale = rect.width / widthPoints;
      const x = (clientX - rect.left) / scale;
      const y = (clientY - rect.top) / scale;
      let best: ReaderPdfBlockDto | null = null;
      let bestDistance = Infinity;
      for (const block of blocksByPage.get(page) ?? []) {
        if (block.bbox.length !== 4 || !isSelectable(block)) continue;
        const dx = x < block.bbox[0] ? block.bbox[0] - x : x > block.bbox[2] ? x - block.bbox[2] : 0;
        const dy = y < block.bbox[1] ? block.bbox[1] - y : y > block.bbox[3] ? y - block.bbox[3] : 0;
        const distance = dy * 4 + dx; // reading flows vertically: track lines, not columns
        if (distance < bestDistance) {
          bestDistance = distance;
          best = block;
        }
      }
      return best;
    },
    [blockAtPoint, blocksByPage],
  );

  const [sweep, setSweep] = useState<{ anchor: number; head: number } | null>(null);
  const sweepRef = useRef<{ anchor: number; head: number; startX: number; startY: number; moved: boolean } | null>(null);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const sweeping = sweep !== null;

  // Ctrl-marquee state: committed boxes plus the box being dragged. Boxes are
  // page-anchored PDF points; the ref mirrors state for window-level handlers.
  const [marqueeBoxes, setMarqueeBoxes] = useState<MarqueeBox[]>([]);
  const [marqueeDraft, setMarqueeDraft] = useState<MarqueeBox | null>(null);
  const [marqueeArmed, setMarqueeArmed] = useState(false);
  const marqueeBoxesRef = useRef<MarqueeBox[]>([]);
  const marqueeDragRef = useRef<{ pageEl: HTMLElement; page: number; x0: number; y0: number } | null>(null);
  const clearMarquee = useCallback(() => {
    marqueeDragRef.current = null;
    marqueeBoxesRef.current = [];
    setMarqueeDraft(null);
    setMarqueeBoxes([]);
  }, []);

  const sweepSpans = useMemo(() => {
    if (!sweep) return null;
    const lo = Math.min(sweep.anchor, sweep.head);
    const hi = Math.max(sweep.anchor, sweep.head);
    return new Set(blocks.slice(lo, hi + 1).filter(isSelectable).map((b) => b.spanId));
  }, [sweep, blocks]);

  const onSweepMouseDown = useCallback(
    (event: React.MouseEvent) => {
      // Only alt+drag sweeps blocks. A plain drag is native glyph selection
      // (the PDF's own text layer is the primary quote source); ctrl/meta
      // drags are handled by the marquee mousedown before this runs.
      if (event.button !== 0 || !event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target as Node;
      if (target instanceof HTMLElement && target.closest("button, input")) return;
      const pageEl = pageElFor(target);
      if (!pageEl) return;
      const block = blockNearPoint(pageEl, event.clientX, event.clientY);
      const idx = block ? indexBySpan.get(block.spanId) : undefined;
      if (idx === undefined) return;
      // The sweep owns this drag: suppress the native glyph selection so the
      // block-snapped range stays crisp.
      event.preventDefault();
      window.getSelection()?.removeAllRanges();
      sweepRef.current = { anchor: idx, head: idx, startX: event.clientX, startY: event.clientY, moved: false };
      lastPointRef.current = { x: event.clientX, y: event.clientY };
      setSweep({ anchor: idx, head: idx });
    },
    [blockNearPoint, indexBySpan],
  );

  // While a sweep is live: track the head block under the pointer (window-level,
  // so leaving the pane doesn't drop the drag) and commit on mouseup.
  useEffect(() => {
    if (!sweeping) return;
    const updateHead = (clientX: number, clientY: number) => {
      const state = sweepRef.current;
      if (!state) return;
      const pageEl = pageElFor(document.elementFromPoint(clientX, clientY));
      if (!pageEl) return; // between pages / outside: head keeps its last block
      const block = blockNearPoint(pageEl, clientX, clientY);
      const idx = block ? indexBySpan.get(block.spanId) : undefined;
      if (idx !== undefined && idx !== state.head) {
        state.head = idx;
        setSweep({ anchor: state.anchor, head: idx });
      }
    };
    const onMove = (event: MouseEvent) => {
      const state = sweepRef.current;
      if (!state) return;
      lastPointRef.current = { x: event.clientX, y: event.clientY };
      if (Math.abs(event.clientX - state.startX) + Math.abs(event.clientY - state.startY) > 5) state.moved = true;
      updateHead(event.clientX, event.clientY);
    };
    const onUp = () => {
      const state = sweepRef.current;
      sweepRef.current = null;
      setSweep(null);
      if (!state || !(state.moved || state.anchor !== state.head)) return; // plain click: onClick selects the span
      const lo = Math.min(state.anchor, state.head);
      const hi = Math.max(state.anchor, state.head);
      const covered = blocks.slice(lo, hi + 1).filter(isSelectable);
      if (!covered.length) return;
      // A block sweep replaces any marquee boxes still painted.
      clearMarquee();
      // The quote per block is the extraction text verbatim — downstream
      // anchoring matches it exactly, and exercise text keeps its LaTeX.
      const nodes = covered.map((b) => ({ spanId: b.spanId, quote: b.text ?? "" }));
      const display = nodes.map((n) => n.quote.replace(/\s+/g, " ").trim()).join(" ");
      onTextSelection({ spanId: nodes[0].spanId, quote: display, nodes });
    };
    // Auto-scroll when the pointer parks near the scroll container's edge; the
    // head re-resolves at the parked pointer as content slides underneath.
    const scroller = (() => {
      let node: HTMLElement | null = containerRef.current?.parentElement ?? null;
      while (node) {
        const style = window.getComputedStyle(node);
        if (/(auto|scroll)/.test(style.overflowY)) return node;
        node = node.parentElement;
      }
      return null;
    })();
    const timer = window.setInterval(() => {
      const point = lastPointRef.current;
      if (!point || !scroller) return;
      const rect = scroller.getBoundingClientRect();
      const zone = 48;
      const delta =
        point.y < rect.top + zone
          ? -Math.ceil((rect.top + zone - point.y) / 3)
          : point.y > rect.bottom - zone
            ? Math.ceil((point.y - (rect.bottom - zone)) / 3)
            : 0;
      if (delta !== 0) {
        scroller.scrollTop += delta;
        updateHead(point.x, point.y);
      }
    }, 40);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [sweeping, blocks, blockNearPoint, indexBySpan, onTextSelection, clearMarquee]);

  // ---- ctrl-marquee union capture -----------------------------------------
  // Hold ctrl (or cmd) and drag any number of boxes over the page(s); releasing
  // ctrl commits their union as one selection. Words from the PDF's own text
  // layer are clipped per box (the embedded text is the quote source); an
  // Equation block joins whole with its extraction LaTeX; a box over glyph-free
  // geometry (scanned pages) falls back to extraction text. Escape cancels.

  const pdfPointFromClient = (pageEl: HTMLElement, clientX: number, clientY: number): [number, number] | null => {
    const widthPoints = Number(pageEl.dataset.widthPoints);
    const rect = pageEl.getBoundingClientRect();
    if (!rect.width || !widthPoints) return null;
    const scale = rect.width / widthPoints;
    const x = Math.min(Math.max((clientX - rect.left) / scale, 0), widthPoints);
    const y = Math.min(Math.max((clientY - rect.top) / scale, 0), rect.height / scale);
    return [x, y];
  };

  const blockForRect = useCallback(
    (page: number, rect: number[]): ReaderPdfBlockDto | null => {
      let best: ReaderPdfBlockDto | null = null;
      let bestArea = 0;
      for (const block of blocksByPage.get(page) ?? []) {
        if (block.bbox.length !== 4 || !isSelectable(block)) continue;
        const w = Math.min(rect[2], block.bbox[2]) - Math.max(rect[0], block.bbox[0]);
        const h = Math.min(rect[3], block.bbox[3]) - Math.max(rect[1], block.bbox[1]);
        if (w > 0 && h > 0 && w * h > bestArea) {
          bestArea = w * h;
          best = block;
        }
      }
      return best;
    },
    [blocksByPage],
  );

  const onMarqueeMouseDown = useCallback((event: React.MouseEvent): boolean => {
    if (event.button !== 0 || !(event.ctrlKey || event.metaKey)) return false;
    const target = event.target as Node;
    if (target instanceof HTMLElement && target.closest("button, input")) return false;
    const pageEl = pageElFor(target);
    if (!pageEl) return false;
    const point = pdfPointFromClient(pageEl, event.clientX, event.clientY);
    if (!point) return false;
    // The marquee owns this drag — no native selection underneath.
    event.preventDefault();
    window.getSelection()?.removeAllRanges();
    const page = Number(pageEl.dataset.pdfPage);
    marqueeDragRef.current = { pageEl, page, x0: point[0], y0: point[1] };
    setMarqueeDraft({ page, rect: [point[0], point[1], point[0], point[1]] });
    return true;
  }, []);

  // While a box is being dragged: window-level tracking so leaving the pane
  // doesn't drop the gesture; mouseup banks the box and waits for more (or for
  // the ctrl release that commits the union).
  const marqueeDrafting = marqueeDraft !== null;
  useEffect(() => {
    if (!marqueeDrafting) return;
    const draftRect = (drag: { x0: number; y0: number }, point: [number, number]): number[] => [
      Math.min(drag.x0, point[0]),
      Math.min(drag.y0, point[1]),
      Math.max(drag.x0, point[0]),
      Math.max(drag.y0, point[1]),
    ];
    const onMove = (event: MouseEvent) => {
      const drag = marqueeDragRef.current;
      if (!drag) return;
      const point = pdfPointFromClient(drag.pageEl, event.clientX, event.clientY);
      if (point) setMarqueeDraft({ page: drag.page, rect: draftRect(drag, point) });
    };
    const onUp = (event: MouseEvent) => {
      const drag = marqueeDragRef.current;
      marqueeDragRef.current = null;
      setMarqueeDraft(null);
      if (!drag) return;
      const point = pdfPointFromClient(drag.pageEl, event.clientX, event.clientY);
      if (!point) return;
      const rect = draftRect(drag, point);
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

  // Boxes → wire nodes. Words come from the text layer clipped per box, in
  // layer (reading) order, grouped one node per covered block; Equation blocks
  // contribute their extraction LaTeX whole; a block a box substantially
  // covers but that yielded no glyphs falls back to its extraction text.
  const resolveMarquee = useCallback(
    (boxes: MarqueeBox[]): Array<{ spanId: string; quote: string }> => {
      const container = containerRef.current;
      if (!container || !boxes.length) return [];
      interface Gather {
        index: number;
        isEquation: boolean;
        block: ReaderPdfBlockDto;
        words: Array<{ order: number; text: string }>;
        geometricHit: boolean;
      }
      const gathered = new Map<string, Gather>();
      const entryFor = (block: ReaderPdfBlockDto): Gather => {
        let entry = gathered.get(block.spanId);
        if (!entry) {
          entry = {
            index: indexBySpan.get(block.spanId) ?? 0,
            isEquation: (block.blockType ?? "") === "Equation",
            block,
            words: [],
            geometricHit: false,
          };
          gathered.set(block.spanId, entry);
        }
        return entry;
      };
      const pages = [...new Set(boxes.map((b) => b.page))].sort((a, b) => a - b);
      let order = 0;
      for (const page of pages) {
        const pageBoxes = boxes.filter((b) => b.page === page).map((b) => b.rect);
        const pageEl = container.querySelector(`[data-pdf-page="${page}"]`);
        if (!(pageEl instanceof HTMLElement)) continue;
        // Geometry pass: a box substantially covering a block registers it even
        // with no glyphs underneath (equation art, scanned pages).
        for (const block of blocksByPage.get(page) ?? []) {
          if (block.bbox.length !== 4 || !isSelectable(block)) continue;
          for (const rect of pageBoxes) {
            const overlap = rectOverlap(rect, block.bbox);
            if (overlap > 0.25 * Math.min(rectArea(rect), rectArea(block.bbox))) {
              entryFor(block).geometricHit = true;
              break;
            }
          }
        }
        // Glyph pass: word-level clipping against the page's text layer.
        const widthPoints = Number(pageEl.dataset.widthPoints);
        const pageRect = pageEl.getBoundingClientRect();
        const layer = pageEl.querySelector(".textLayer");
        if (!layer || !pageRect.width || !widthPoints) continue;
        const scale = pageRect.width / widthPoints;
        const walker = document.createTreeWalker(layer, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          const text = node as Text;
          const wordPattern = /\S+/g;
          let match: RegExpExecArray | null;
          while ((match = wordPattern.exec(text.data))) {
            const wordRange = document.createRange();
            wordRange.setStart(text, match.index);
            wordRange.setEnd(text, match.index + match[0].length);
            const rects = Array.from(wordRange.getClientRects()).filter((r) => r.width > 0.5 && r.height > 0.5);
            if (!rects.length) continue;
            const union = rects.reduce(
              (acc, r) => [
                Math.min(acc[0], (r.left - pageRect.left) / scale),
                Math.min(acc[1], (r.top - pageRect.top) / scale),
                Math.max(acc[2], (r.right - pageRect.left) / scale),
                Math.max(acc[3], (r.bottom - pageRect.top) / scale),
              ],
              [Infinity, Infinity, -Infinity, -Infinity],
            );
            const cx = (union[0] + union[2]) / 2;
            const cy = (union[1] + union[3]) / 2;
            const hit = pageBoxes.some(
              (rect) =>
                (cx >= rect[0] && cx <= rect[2] && cy >= rect[1] && cy <= rect[3]) ||
                rectOverlap(rect, union) >= 0.5 * rectArea(union),
            );
            if (!hit) continue;
            const block = blockForRect(page, union);
            if (!block) continue;
            const entry = entryFor(block);
            if (entry.isEquation) entry.geometricHit = true;
            else entry.words.push({ order: order++, text: match[0] });
          }
        }
      }
      return [...gathered.values()]
        .sort((a, b) => a.index - b.index)
        .map((entry) => ({
          spanId: entry.block.spanId,
          quote:
            entry.isEquation || entry.words.length === 0
              ? entry.geometricHit
                ? (entry.block.text ?? "").trim()
                : ""
              : entry.words
                  .sort((a, b) => a.order - b.order)
                  .map((w) => w.text)
                  .join(" "),
        }))
        .filter((node) => node.quote.length > 0);
    },
    [blocksByPage, blockForRect, indexBySpan],
  );

  const commitMarquee = useCallback(() => {
    const boxes = marqueeBoxesRef.current;
    if (!boxes.length) return;
    const nodes = resolveMarquee(boxes);
    if (!nodes.length) {
      clearMarquee();
      return;
    }
    const display = nodes.map((n) => n.quote.replace(/\s+/g, " ").trim()).join(" ");
    onTextSelection({ spanId: nodes[0].spanId, quote: display, nodes });
  }, [resolveMarquee, clearMarquee, onTextSelection]);
  const commitMarqueeRef = useRef(commitMarquee);
  useEffect(() => {
    commitMarqueeRef.current = commitMarquee;
  }, [commitMarquee]);

  // Releasing ctrl commits the union; Escape abandons it. Armed state drives
  // the crosshair affordance while ctrl/cmd is down.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Control" || event.key === "Meta") setMarqueeArmed(true);
      if (event.key === "Escape" && (marqueeBoxesRef.current.length || marqueeDragRef.current)) clearMarquee();
    };
    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key !== "Control" && event.key !== "Meta") return;
      setMarqueeArmed(false);
      // A drag still in flight commits from its own mouseup instead.
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

  // The parent cleared the capture (clear button) — drop the painted boxes. A
  // fresh commit in the same batch keeps selectedSpans non-empty, so this only
  // fires on a true clear.
  useEffect(() => {
    if (selectedSpans.size === 0 && marqueeBoxesRef.current.length > 0) clearMarquee();
  }, [selectedSpans, clearMarquee]);

  const marqueeByPage = useMemo(() => {
    const map = new Map<number, number[][]>();
    for (const box of marqueeBoxes) {
      const list = map.get(box.page) ?? [];
      list.push(box.rect);
      map.set(box.page, list);
    }
    return map;
  }, [marqueeBoxes]);

  // Single mousedown dispatcher: ctrl/cmd → marquee, alt → block sweep,
  // plain → native glyph selection (no handler).
  const onPaneMouseDown = useCallback(
    (event: React.MouseEvent) => {
      if (onMarqueeMouseDown(event)) return;
      onSweepMouseDown(event);
    },
    [onMarqueeMouseDown, onSweepMouseDown],
  );


  // Native text selection → ordered per-block {spanId, quote} segments via
  // geometry: each selected text-layer node is clipped to the selection, its
  // rects are hit-tested against block bboxes, and its text accrues to the
  // best-covered block. One selection sweeping several extraction blocks (e.g.
  // consecutive textbook exercises) yields one node per block, in reading
  // order, so downstream anchoring stays exercise-precise instead of
  // collapsing to a single oversized block. Shared by mouse-up capture and
  // the tag menu.
  const resolveSelection = useCallback((): {
    spanId: string;
    quote: string;
    nodes: Array<{ spanId: string; quote: string }>;
  } | null => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;
    const quote = selection.toString().replace(/\s+/g, " ").trim();
    if (!quote) return null;
    const range = selection.getRangeAt(0);

    // Selected text nodes in document order (pdf.js text layer reading order).
    const root = range.commonAncestorContainer;
    const textNodes: Node[] = [];
    if (root.nodeType === Node.TEXT_NODE) {
      textNodes.push(root);
    } else {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        if (range.intersectsNode(node)) textNodes.push(node);
      }
    }

    // Accumulate each node's clipped text onto its best-overlap block; nodes
    // whose rects miss every bbox (inter-block glue) continue the previous
    // segment rather than dropping learner-selected text.
    const segments: Array<{ spanId: string; pieces: string[] }> = [];
    const bySpan = new Map<string, { spanId: string; pieces: string[] }>();
    const append = (spanId: string, text: string) => {
      let segment = bySpan.get(spanId);
      if (!segment) {
        segment = { spanId, pieces: [] };
        bySpan.set(spanId, segment);
        segments.push(segment);
      }
      segment.pieces.push(text);
    };
    for (const node of textNodes) {
      const sub = document.createRange();
      sub.selectNodeContents(node);
      if (node === range.startContainer) sub.setStart(node, range.startOffset);
      if (node === range.endContainer) sub.setEnd(node, range.endOffset);
      const text = sub.toString().replace(/\s+/g, " ");
      if (!text.trim()) continue;
      const pageEl = pageElFor(node);
      if (!pageEl) continue;
      const page = Number(pageEl.dataset.pdfPage);
      const widthPoints = Number(pageEl.dataset.widthPoints);
      const pageRect = pageEl.getBoundingClientRect();
      if (!pageRect.width || !widthPoints) continue;
      const scale = pageRect.width / widthPoints;
      const overlaps = new Map<string, number>();
      for (const rect of Array.from(sub.getClientRects())) {
        const x0 = (rect.left - pageRect.left) / scale;
        const x1 = (rect.right - pageRect.left) / scale;
        const y0 = (rect.top - pageRect.top) / scale;
        const y1 = (rect.bottom - pageRect.top) / scale;
        for (const block of blocksByPage.get(page) ?? []) {
          // Furniture (running heads, footers) is real geometry but never part
          // of a capture — swept-past glyphs must not pollute the quote.
          if (block.bbox.length !== 4 || FURNITURE_TYPES.has(block.blockType ?? "")) continue;
          const w = Math.min(x1, block.bbox[2]) - Math.max(x0, block.bbox[0]);
          const h = Math.min(y1, block.bbox[3]) - Math.max(y0, block.bbox[1]);
          if (w > 0 && h > 0) overlaps.set(block.spanId, (overlaps.get(block.spanId) ?? 0) + w * h);
        }
      }
      const best = [...overlaps.entries()].sort((a, b) => b[1] - a[1])[0];
      // Glyphs hitting no block (page numbers, margin decorations) are dropped
      // rather than glued onto the previous segment — glue was a steady source
      // of overselected quotes.
      if (best) append(best[0], text);
    }

    const nodes = segments
      .map((segment) => {
        const block = blockBySpan.get(segment.spanId);
        // Equation glyphs are junk or absent in the text layer — the block's
        // extraction LaTeX is the only faithful quote for math.
        if (block && (block.blockType ?? "") === "Equation") {
          return { spanId: segment.spanId, quote: (block.text ?? "").trim() };
        }
        return { spanId: segment.spanId, quote: segment.pieces.join(" ").replace(/\s+/g, " ").trim() };
      })
      .filter((segment) => segment.quote.length > 0);
    if (nodes.length === 0) return null;
    // Primary span = the block carrying most of the selected text, so a stray
    // sliver from an adjacent block never claims the active highlight.
    const primary = [...nodes].sort((a, b) => b.quote.length - a.quote.length)[0];
    return { spanId: primary.spanId, quote, nodes };
  }, [blocksByPage, blockBySpan]);

  const onMouseUp = useCallback(() => {
    const resolved = resolveSelection();
    if (resolved) {
      // A fresh native selection replaces any marquee boxes still painted.
      if (marqueeBoxesRef.current.length) clearMarquee();
      onTextSelection(resolved);
    }
  }, [resolveSelection, clearMarquee, onTextSelection]);

  // Right-click → tag menu: a live selection tags the selection; otherwise the
  // block under the cursor is tagged whole.
  const onContextMenu = useCallback(
    (event: React.MouseEvent) => {
      const resolved = resolveSelection();
      if (resolved) {
        event.preventDefault();
        onTagMenu({ x: event.clientX, y: event.clientY, spanId: resolved.spanId, quote: resolved.quote });
        return;
      }
      const pageEl = pageElFor(event.target as Node);
      if (!pageEl) return;
      const block = blockAtPoint(pageEl, event.clientX, event.clientY);
      if (!block) return;
      event.preventDefault();
      onTagMenu({ x: event.clientX, y: event.clientY, spanId: block.spanId, quote: null });
    },
    [resolveSelection, blockAtPoint, onTagMenu],
  );

  if (!doc) {
    return (
      <div ref={containerRef} style={{ padding: 24 }}>
        <Faint style={{ fontSize: 12 }}>◐ loading original PDF…</Faint>
      </div>
    );
  }

  const pageWidth = Math.max(320, containerWidth - 2) * zoom;
  return (
    <div
      ref={containerRef}
      className={sweeping ? "ll-block-sweeping" : marqueeArmed || marqueeDrafting ? "ll-marquee-armed" : undefined}
      onMouseDown={onPaneMouseDown}
      onMouseUp={onMouseUp}
      onContextMenu={onContextMenu}
      style={{ display: "flex", flexDirection: "column", gap: 0 }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "4px 0 10px 0",
          position: "sticky",
          top: -18, // tucks under the scroll container's 18px padding
          zIndex: 5,
          background: COLOR.bg,
        }}
      >
        <Faint style={{ fontSize: 11 }}>
          original pdf · {coveredPages.length} ingested page{coveredPages.length === 1 ? "" : "s"}
        </Faint>
        <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
          {findOpen ? (
            <>
              <input
                ref={findInputRef}
                value={findQuery}
                onChange={(e) => setFindQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    gotoMatch(e.shiftKey ? -1 : 1);
                  } else if (e.key === "Escape") {
                    e.stopPropagation();
                    closeFind();
                  }
                }}
                placeholder="find in pdf…"
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  width: 170,
                  background: COLOR.bgInput,
                  border: `1px solid ${COLOR.border}`,
                  color: COLOR.text,
                  padding: "3px 8px",
                }}
              />
              <Faint style={{ fontSize: 11, minWidth: 40, textAlign: "center" }}>
                {matches.length ? `${matchIdx + 1}/${matches.length}` : findQuery.trim() ? "0/0" : ""}
              </Faint>
              <ZoomButton label="↑" onClick={() => gotoMatch(-1)} />
              <ZoomButton label="↓" onClick={() => gotoMatch(1)} />
              <ZoomButton label="✕" onClick={closeFind} />
            </>
          ) : (
            <ZoomButton label="⌕" onClick={openFind} />
          )}
          <ZoomButton label="−" onClick={zoomOut} />
          <Faint style={{ fontSize: 11, minWidth: 38, textAlign: "center" }}>{Math.round(zoom * 100)}%</Faint>
          <ZoomButton label="+" onClick={zoomIn} />
        </span>
      </div>
      <div style={{ overflowX: zoom > 1 ? "auto" : "hidden", display: "flex", flexDirection: "column", gap: 14 }}>
        {coveredPages.map((page, index) => (
          <div key={page}>
            {index > 0 && coveredPages[index - 1] !== page - 1 ? (
              <Faint style={{ fontSize: 10, display: "block", padding: "2px 0 12px 0" }}>
                ⋯ pages {coveredPages[index - 1] + 2}–{page} of the original were not ingested
              </Faint>
            ) : null}
            <PdfPage
              doc={doc}
              pageIndex={page}
              widthPx={pageWidth}
              blocks={blocksByPage.get(page) ?? []}
              trails={trailsByPage.get(page) ?? []}
              guidanceSpans={guidanceSpans}
              selectedSpans={marqueeBoxes.length ? EMPTY_SPANS : selectedSpans}
              sweepSpans={sweepSpans}
              marqueeRects={marqueeByPage.get(page) ?? []}
              marqueeDraftRect={marqueeDraft && marqueeDraft.page === page ? marqueeDraft.rect : null}
              activeSpan={activeSpan}
              findQuery={findOpen ? findQuery.trim() : ""}
            />
          </div>
        ))}
      </div>
    </div>
  );
});

function ZoomButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      style={{
        fontFamily: FONT_MONO,
        fontSize: 12,
        width: 24,
        height: 20,
        lineHeight: "18px",
        background: "transparent",
        border: `1px solid ${COLOR.border}`,
        color: COLOR.textDim,
        cursor: "pointer",
        padding: 0,
      }}
    >
      {label}
    </button>
  );
}

function PdfPage({
  doc,
  pageIndex,
  widthPx,
  blocks,
  trails,
  guidanceSpans,
  selectedSpans,
  sweepSpans,
  marqueeRects,
  marqueeDraftRect,
  activeSpan,
  findQuery,
}: {
  doc: PDFDocumentProxy;
  pageIndex: number;
  widthPx: number;
  blocks: ReaderPdfBlockDto[];
  trails: AnnotationTrail[];
  guidanceSpans: Set<string>;
  selectedSpans: Set<string>;
  sweepSpans: Set<string> | null;
  marqueeRects: number[][];
  marqueeDraftRect: number[] | null;
  activeSpan: string | null;
  findQuery: string;
}) {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const textRef = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);
  const [geometry, setGeometry] = useState<PageGeometry | null>(null);
  const renderedKeyRef = useRef<string | null>(null);

  useEffect(() => {
    const node = wrapperRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => entry.isIntersecting && setVisible(true)),
      { rootMargin: "600px 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || widthPx <= 0) return;
    const renderKey = `${pageIndex}:${Math.round(widthPx)}`;
    if (renderedKeyRef.current === renderKey) return;
    let cancelled = false;
    (async () => {
      try {
        const page = await doc.getPage(pageIndex + 1);
        const base = page.getViewport({ scale: 1 });
        const scale = widthPx / base.width;
        const viewport = page.getViewport({ scale });
        const canvas = canvasRef.current;
        const textDiv = textRef.current;
        if (!canvas || !textDiv || cancelled) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(viewport.width * dpr);
        canvas.height = Math.floor(viewport.height * dpr);
        const context = canvas.getContext("2d");
        if (!context) return;
        await page.render({
          canvas,
          canvasContext: context,
          viewport,
          transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : undefined,
        }).promise;
        if (cancelled) return;
        textDiv.replaceChildren();
        const textLayer = new pdfjs.TextLayer({
          textContentSource: page.streamTextContent(),
          container: textDiv,
          viewport,
        });
        await textLayer.render();
        if (cancelled) return;
        renderedKeyRef.current = renderKey;
        setGeometry({ widthPoints: base.width, heightPoints: base.height });
      } catch (error) {
        if (!cancelled) console.error(`pdf page ${pageIndex} render failed`, error);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [visible, doc, pageIndex, widthPx]);

  // Mark text-layer spans containing the find query (case-insensitive). The
  // marks re-apply whenever the query changes or the layer (re)renders; a match
  // that straddles two layout spans is counted by the toolbar but not washed.
  useEffect(() => {
    const textDiv = textRef.current;
    if (!textDiv) return;
    const query = findQuery.toLowerCase();
    for (const span of Array.from(textDiv.querySelectorAll("span"))) {
      const hit = query.length > 0 && (span.textContent ?? "").toLowerCase().includes(query);
      span.classList.toggle("ll-find-hit", hit);
    }
  }, [findQuery, geometry]);

  const aspect = geometry ? geometry.heightPoints / geometry.widthPoints : 1.294; // letter-ish placeholder
  const scale = geometry ? widthPx / geometry.widthPoints : 1;
  return (
    <div
      ref={wrapperRef}
      data-pdf-page={pageIndex}
      data-width-points={geometry?.widthPoints ?? 0}
      style={{
        position: "relative",
        width: widthPx,
        height: widthPx * aspect,
        background: "#fff",
        border: `1px solid ${COLOR.border}`,
        // pdf.js text layer positions glyphs via this variable.
        ["--scale-factor" as string]: String(scale),
      }}
    >
      <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
      {geometry
        ? trails
            .filter((t) => t.bbox.length === 4)
            .map((t, i) => {
              const color = TRAIL_COLORS[t.kind] ?? TRAIL_COLORS.other;
              return (
                <div
                  key={`${t.annotationId ?? "local"}-${t.spanId}-${i}`}
                  title={t.kind.replace(/_/g, " ")}
                  style={{
                    position: "absolute",
                    left: t.bbox[0] * scale,
                    top: t.bbox[1] * scale,
                    width: (t.bbox[2] - t.bbox[0]) * scale,
                    height: (t.bbox[3] - t.bbox[1]) * scale,
                    pointerEvents: "none",
                    background: color.wash,
                    borderLeft: `3px solid ${color.edge}`,
                    mixBlendMode: "multiply",
                  }}
                />
              );
            })
        : null}
      <div ref={textRef} className="textLayer" style={{ position: "absolute", inset: 0 }} />
      {geometry
        ? blocks
            .filter((b) => b.bbox.length === 4)
            .map((b) => {
              // Paint precedence: live sweep > committed selection > active
              // span > guidance.
              const swept = sweepSpans?.has(b.spanId) ?? false;
              const selected = selectedSpans.has(b.spanId);
              const active = activeSpan === b.spanId;
              const guided = guidanceSpans.has(b.spanId);
              const border = swept
                ? `2px solid ${COLOR.amber}`
                : selected
                  ? "2px solid rgba(215, 135, 15, 0.75)"
                  : active
                    ? `2px solid ${COLOR.amber}`
                    : guided
                      ? `2px dashed ${COLOR.purplePill}`
                      : "2px solid transparent";
              const background = swept
                ? "rgba(245, 166, 35, 0.20)"
                : selected
                  ? "rgba(245, 166, 35, 0.13)"
                  : active
                    ? "rgba(245, 166, 35, 0.08)"
                    : guided
                      ? "rgba(90, 77, 138, 0.10)"
                      : "transparent";
              return (
                <div
                  key={b.spanId}
                  data-span-id={b.spanId}
                  title={guided ? "Worth a second look for your learning path" : undefined}
                  style={{
                    position: "absolute",
                    left: b.bbox[0] * scale,
                    top: b.bbox[1] * scale,
                    width: (b.bbox[2] - b.bbox[0]) * scale,
                    height: (b.bbox[3] - b.bbox[1]) * scale,
                    pointerEvents: "none",
                    border,
                    background,
                    mixBlendMode: swept || selected ? "multiply" : undefined,
                    transition: swept ? "none" : "background 120ms ease, border-color 120ms ease",
                  }}
                />
              );
            })
        : null}
      {geometry
        ? marqueeRects.map((r, i) => (
            <div
              key={`marquee-${i}`}
              style={{
                position: "absolute",
                left: r[0] * scale - 2,
                top: r[1] * scale - 1.5,
                width: (r[2] - r[0]) * scale + 4,
                height: (r[3] - r[1]) * scale + 3,
                pointerEvents: "none",
                background: "rgba(245, 166, 35, 0.18)",
                border: "1.5px solid rgba(215, 135, 15, 0.9)",
                borderRadius: 3,
                mixBlendMode: "multiply",
              }}
            />
          ))
        : null}
      {geometry && marqueeDraftRect ? (
        <div
          style={{
            position: "absolute",
            left: marqueeDraftRect[0] * scale - 2,
            top: marqueeDraftRect[1] * scale - 1.5,
            width: (marqueeDraftRect[2] - marqueeDraftRect[0]) * scale + 4,
            height: (marqueeDraftRect[3] - marqueeDraftRect[1]) * scale + 3,
            pointerEvents: "none",
            background: "rgba(245, 166, 35, 0.10)",
            border: "1.5px dashed rgba(215, 135, 15, 0.8)",
            borderRadius: 3,
            mixBlendMode: "multiply",
          }}
        />
      ) : null}
      <span
        style={{
          position: "absolute",
          right: 6,
          bottom: 4,
          fontFamily: FONT_MONO,
          fontSize: 10,
          color: "rgba(0,0,0,0.45)",
          pointerEvents: "none",
        }}
      >
        p.{pageIndex + 1}
      </span>
    </div>
  );
}
