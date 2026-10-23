// PdfReaderPane — Tier-2 embedded original-PDF reader.
//
// Renders the revision's original PDF (served from the vault's content-addressed
// originals store through the llpdf:// protocol) with pdf.js: a canvas and the
// PDF's own text layer per page, drawn only while the page is near the view and
// released when it leaves (a 600-page book keeps a handful of pages drawn). Only
// pages the extraction covers are shown (a whole textbook may back a
// chapter-scoped ingest), with honest gap markers between non-adjacent pages.
//
// Selection (reader-pdf-selection): one selection model over the extraction's
// blocks in reading order (components/pdfSelection). Words come from the page's
// own text layer where it has one and are placed by estimate inside the layout
// model's boxes where it has none (a scan read by GLM-OCR), so selection works
// on every page; a formula, table or figure is one unit, its LaTeX or Markdown
// the selected text. A plain drag, a double or triple click, Shift+click,
// Shift+arrows, Ctrl+drag boxes and Alt+drag sweeps all move one selection, and
// every selection is sent as each block's exact slice with code-point offsets,
// so it anchors exactly and Ask, the palette, checks, citations and notes act on
// it as on the extracted text. Saved highlights are drawn from their anchors on
// the open reading (never from stored screen boxes), with a keyboard stop each,
// "moved here when the book was read again" when a re-read carried them, and a
// dashed outline where their words changed. The browser's own selection is off
// over the pages: the text layer stays for find and for screen readers.

import { forwardRef, memo, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState, type ReactNode } from "react";
import * as pdfjs from "pdfjs-dist";
import type { PDFDocumentProxy } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import "pdfjs-dist/web/pdf_viewer.css";
import type { ReaderPdfBlockDto } from "../api/dto";
import type { PdfPageLayout } from "../screens/reader/cues";
import { COLOR, Faint, FONT_MONO } from "./term";
import { acquirePdfDocument } from "./pdfDocumentCache";
import { pagesLeftOutLabel, pagesShownLabel, pagesToShow } from "./pdfPages";
import { highlightAt, highlightsOnPage, placeHighlights, type HighlightOnPage, type PdfHighlight } from "./pdfSelection/highlights";
import { operatorWords, type PdfFontInfo } from "./pdfSelection/geometry";
import { blockAt, rangeRects, SelectionModel, type Box, type GlyphItem, type GlyphWord, type SelectionPayload, type TextStyles } from "./pdfSelection/model";
import { PdfSelectionLayer } from "./pdfSelection/PdfSelectionLayer";
import { usePdfSelection, type HeldSelection, type PagePoint } from "./pdfSelection/usePdfSelection";
import { screenLeavesKey } from "../app/keymap";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

interface PageGeometry {
  widthPoints: number;
  heightPoints: number;
}

const NO_HIGHLIGHTS: PdfHighlight[] = [];
const NO_BOXES: Box[] = [];
const NO_PAGE_HIGHLIGHTS: HighlightOnPage[] = [];
const NO_MARQUEE: number[][] = [];

/** A page is drawn while it is within this distance of the view, and its
 *  canvas and text layer are released once it is further away. */
const NEAR_VIEW_MARGIN = "1200px 0px";
/** A pointer this far above or below every shown page is between pages (the
 *  gap, a "pages left out" line), not on one. */
const BETWEEN_PAGES_PX = 48;

/** A right-click tag request: where to show the menu and what it would tag —
 *  a selection's quote, or the whole block when quote is null. */
export interface TagMenuRequest {
  x: number;
  y: number;
  spanId: string;
  quote: string | null;
  /** Ordered source-block fragments for the selection (with code-point
   *  offsets from the original PDF's selection model). */
  nodes?: Array<{ spanId: string; quote: string; start?: number; end?: number; prefix?: string; suffix?: string }>;
}

/** Where a passage lands in the view: centred (a cited or annotated passage,
 *  seen in its context) or at the top (a place to read on from: a resume, a
 *  section from Contents), so the page on screen is the one being read. */
export type PassageAlign = "center" | "start";

/** Imperative surface for the screen: jump to an annotation's page/block. */
export interface PdfReaderPaneHandle {
  scrollToSegment: (page: number, spanId?: string | null, align?: PassageAlign) => void;
  /** Put ``offset`` (0..1) of page ``page`` at the top of the view, exactly;
   *  waits for the page to be laid out (the preparing view's hand-over). */
  scrollToPage: (page: number, offset?: number) => void;
}

// Room left above a passage put at the top: the pane's sticky bar (zoom,
// find) sits there, and a line of what came before keeps the place.
const PASSAGE_TOP_MARGIN_PX = 56;

function alignPassage(box: HTMLElement, align: PassageAlign, smooth: boolean) {
  if (align === "start") box.style.scrollMarginTop = `${PASSAGE_TOP_MARGIN_PX}px`;
  box.scrollIntoView({ ...(smooth ? { behavior: "smooth" as const } : {}), block: align });
}

interface PdfReaderPaneProps {
  fileUrl: string;
  blocks: ReaderPdfBlockDto[];
  /** The learner's highlights and notes placed on the open reading. */
  highlights?: PdfHighlight[];
  /** Personalized second-pass passages revealed by the learner at a section break. */
  guidanceSpans: Set<string>;
  /** The Reader's capture: painted on its words until it is cleared or replaced. */
  selection?: HeldSelection | null;
  activeSpan: string | null;
  /** A selection settled (150 ms after the mouse or the last key). */
  onTextSelection: (selection: SelectionPayload) => void;
  /** Esc on the pages: the learner cleared the selection. */
  onSelectionCleared?: () => void;
  onTagMenu: (request: TagMenuRequest) => void;
  /** A highlight's "open note" (Enter on its keyboard stop). */
  onHighlightOpen?: (id: string) => void;
  /** A highlight's "remove" (Delete on its keyboard stop); the Reader offers undo. */
  onHighlightRemove?: (id: string) => void;
  onError: (message: string) => void;
  /** RW1a: one quiet line under a passage (the reconnect line after a return
   *  the learner started), drawn just below the block on its page. */
  inlineNote?: { spanId: string; node: ReactNode } | null;
  /** Reader RW5a: explorable figures under their passages (the collapsed line;
   *  expanded, the figure), drawn below each block on its page like the inline note. */
  inlineNotes?: ReadonlyArray<{ spanId: string; node: ReactNode }> | null;
  /** Reader RW5a: a single Ctrl+drag box inside a figure selects a region of it. */
  regionSelection?: boolean;
  /** RW3a: margin marks by passage, drawn in an overlay gutter at the left of
   *  the passage's box (only passages with a box have a place to draw). */
  marks?: ReadonlyMap<string, ReactNode> | null;
  /** The shown pages' own sizes and the width they are drawn at, reported
   *  once the sizes are read (with the document, never from drawing) and as
   *  the width changes (zoom, resize): the Reader's one-mark-per-screenful
   *  spacing places marks on this layout (RW3a review F5). */
  onPageLayout?: (layout: PdfPageLayout) => void;
  /** RW1b: blocks covered by an opaque fold while the learner tries the next
   *  step (the original-page view's fold, spec §4.2). */
  coveredSpans?: ReadonlySet<string>;
}

interface FindMatch {
  page: number;
  ordinal: number;
}

/** Same boxes, same numbers. */
function sameBoxes(a: readonly Box[], b: readonly Box[]): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    const x = a[i];
    const y = b[i];
    if (x[0] !== y[0] || x[1] !== y[1] || x[2] !== y[2] || x[3] !== y[3]) return false;
  }
  return true;
}

function samePageHighlights(a: readonly HighlightOnPage[], b: readonly HighlightOnPage[]): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  return a.every((entry, i) => entry.id === b[i].id && entry.state === b[i].state && entry.kind === b[i].kind && entry.starts === b[i].starts && sameBoxes(entry.rects, b[i].rects));
}

/** The block types a region of a figure can be drawn on (Reader RW5a). */
const FIGURE_BLOCK_TYPES = new Set(["Figure", "FigureGroup", "Picture", "PictureGroup"]);

export const PdfReaderPane = forwardRef<PdfReaderPaneHandle, PdfReaderPaneProps>(function PdfReaderPane(
  {
    fileUrl,
    blocks,
    highlights = NO_HIGHLIGHTS,
    guidanceSpans,
    selection = null,
    activeSpan,
    onTextSelection,
    onSelectionCleared,
    onTagMenu,
    onHighlightOpen,
    onHighlightRemove,
    onError,
    inlineNote = null,
    inlineNotes = null,
    regionSelection = false,
    marks = null,
    onPageLayout,
    coveredSpans,
  }: PdfReaderPaneProps,
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
  const coveredPages = useMemo(() => pagesToShow(blocks, doc ? doc.numPages : null), [blocks, doc]);
  const blocksByPage = useMemo(() => {
    const map = new Map<number, ReaderPdfBlockDto[]>();
    for (const block of blocks) {
      const list = map.get(block.page) ?? [];
      list.push(block);
      map.set(block.page, list);
    }
    return map;
  }, [blocks]);

  // The parsed document (and its page-text cache) lives in pdfDocumentCache
  // and survives this pane unmounting, so returning to the Reader does not
  // re-fetch and re-parse the PDF. Nothing is destroyed here; the cache evicts.
  useEffect(() => {
    let cancelled = false;
    acquirePdfDocument(fileUrl)
      .then((entry) => {
        if (cancelled) return;
        pageTextsRef.current = entry.pageTexts;
        setDoc(entry.doc);
      })
      .catch((error: unknown) => {
        if (!cancelled) onError(`could not load original PDF: ${error instanceof Error ? error.message : String(error)}`);
      });
    return () => {
      cancelled = true;
      setDoc(null);
    };
  }, [fileUrl, onError]);

  // Each shown page's own size, read with the document rather than from
  // drawing it (RW3a review F5): the Reader's mark spacing lays pages out with
  // it, and an undrawn page's placeholder takes it, so the layout the spacing
  // assumes is the layout on screen and nothing moves as pages are drawn while
  // the learner scrolls. Only with block geometry: without boxes no passage
  // has a place for a mark, and a whole book's pages need not be read.
  const [pageSizes, setPageSizes] = useState<{ doc: PDFDocumentProxy; sizes: ReadonlyMap<number, PageGeometry> } | null>(null);
  const hasBoxes = blocks.length > 0;
  useEffect(() => {
    if (!doc || !hasBoxes) return;
    let cancelled = false;
    Promise.all(
      coveredPages.map(async (page) => {
        const base = (await doc.getPage(page + 1)).getViewport({ scale: 1 });
        return [page, { widthPoints: base.width, heightPoints: base.height }] as const;
      }),
    )
      .then((entries) => {
        if (!cancelled) setPageSizes({ doc, sizes: new Map(entries) });
      })
      .catch(() => {
        /* No sizes, no layout: the Reader draws no mark on the original. */
      });
    return () => {
      cancelled = true;
    };
  }, [doc, coveredPages, hasBoxes]);
  const sizes = pageSizes && pageSizes.doc === doc ? pageSizes.sizes : null;

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    const observer = new ResizeObserver(() => setContainerWidth(node.clientWidth));
    observer.observe(node);
    setContainerWidth(node.clientWidth);
    return () => observer.disconnect();
  }, []);

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
      if (screenLeavesKey(event, { ownChords: true })) return;
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
      if (!event.ctrlKey) {
        // The learner is scrolling: a place still waiting for layout is dropped.
        pendingTargetRef.current = null;
        return;
      }
      event.preventDefault();
      setZoom((z) => clampZoom(z * (event.deltaY < 0 ? 1.1 : 0.9)));
    };
    const onTouch = () => {
      pendingTargetRef.current = null;
    };
    node.addEventListener("wheel", onWheel, { passive: false });
    node.addEventListener("touchmove", onTouch, { passive: true });
    return () => {
      node.removeEventListener("wheel", onWheel);
      node.removeEventListener("touchmove", onTouch);
    };
  }, [doc]);

  // A place asked for before it can be reached is kept until it can (review
  // of usability round 2, F4): the document loads, page sizes arrive, then a
  // page near the view is drawn and only then do its passages get boxes. A
  // page offset applies once its page has a size; a passage is centred once
  // its box exists, its page brought into view first so that it is drawn.
  // The newest request replaces an older one (the Reader's resume asks for
  // the page, then the passage), and the learner's own wheel or touch drops
  // it, so a late layout never pulls them back.
  const pendingTargetRef = useRef<{
    page: number;
    offset: number;
    spanId: string | null;
    align: PassageAlign;
    tries: number;
    paged: boolean;
  } | null>(null);
  const [pendingTarget, setPendingTarget] = useState(0);
  const applyPageScroll = useCallback((page: number, offset: number): boolean => {
    const container = containerRef.current;
    const pageEl = container?.querySelector(`[data-pdf-page="${page}"]`);
    if (!(pageEl instanceof HTMLElement)) return false;
    const pageRect = pageEl.getBoundingClientRect();
    if (pageRect.height <= 0) return false;
    let scroller: HTMLElement | null = container?.parentElement ?? null;
    while (scroller && !/(auto|scroll)/.test(window.getComputedStyle(scroller).overflowY)) {
      scroller = scroller.parentElement;
    }
    if (!scroller) {
      pageEl.scrollIntoView({ block: "start" });
      return true;
    }
    scroller.scrollTop += pageRect.top - scroller.getBoundingClientRect().top + offset * pageRect.height;
    return true;
  }, []);
  /** The passage's box on a laid-out page, once that page is drawn. */
  const passageBox = useCallback((page: number, spanId: string): HTMLElement | null => {
    const pageEl = containerRef.current?.querySelector(`[data-pdf-page="${page}"]`);
    if (!(pageEl instanceof HTMLElement) || pageEl.getBoundingClientRect().height <= 0) return null;
    const box = Array.from(pageEl.querySelectorAll<HTMLElement>("[data-span-id]")).find(
      (element) => element.dataset.spanId === spanId,
    );
    return box ?? null;
  }, []);
  const applyTarget = useCallback(
    (target: { page: number; offset: number; spanId: string | null; align: PassageAlign; paged: boolean }): boolean => {
      if (target.spanId === null) return applyPageScroll(target.page, target.offset);
      const box = passageBox(target.page, target.spanId);
      if (box) {
        alignPassage(box, target.align, false);
        return true;
      }
      // Not drawn yet: its page first, once, so that it is drawn.
      if (!target.paged) target.paged = applyPageScroll(target.page, 0);
      return false;
    },
    [applyPageScroll, passageBox],
  );
  const keepTarget = useCallback(
    (page: number, offset: number, spanId: string | null, align: PassageAlign = "center") => {
      const target = { page, offset, spanId, align, tries: 0, paged: false };
      if (applyTarget(target)) {
        pendingTargetRef.current = null;
        return;
      }
      pendingTargetRef.current = target;
      setPendingTarget((tick) => tick + 1);
    },
    [applyTarget],
  );

  const scrollToSegment = useCallback(
    (page: number, spanId?: string | null, align: PassageAlign = "center") => {
      // Ready now (an annotation's card on a drawn page): glide there.
      const box = spanId ? passageBox(page, spanId) : null;
      if (box) {
        pendingTargetRef.current = null;
        alignPassage(box, align, true);
        return;
      }
      keepTarget(page, 0, spanId ?? null, align);
    },
    [passageBox, keepTarget],
  );

  /** Put ``offset`` of page ``page`` at the top of the view, exactly. */
  const scrollToPage = useCallback(
    (page: number, offset = 0) => keepTarget(page, offset, null),
    [keepTarget],
  );
  useEffect(() => {
    if (!doc || !pendingTargetRef.current) return;
    const timer = window.setInterval(() => {
      const pending = pendingTargetRef.current;
      if (!pending) {
        window.clearInterval(timer);
        return;
      }
      pending.tries += 1;
      if (applyTarget(pending) || pending.tries > 80) {
        if (pendingTargetRef.current === pending) pendingTargetRef.current = null;
        window.clearInterval(timer);
      }
    }, 100);
    return () => window.clearInterval(timer);
  }, [doc, containerWidth, pendingTarget, applyTarget]);

  useImperativeHandle(handleRef, () => ({ scrollToSegment, scrollToPage }), [scrollToSegment, scrollToPage]);

  // ---- selection and highlights (reader-pdf-selection) --------------------
  // One selection model over the extraction's blocks in reading order; pages
  // add their words as they are drawn (`modelVersion` repaints).
  const model = useMemo(() => new SelectionModel(blocks), [blocks]);
  const [modelVersion, setModelVersion] = useState(0);
  const onPageText = useCallback(
    (page: number, items: readonly GlyphItem[], transform: readonly number[], styles?: TextStyles | null) => {
      if (model.hasPageText(page)) return;
      model.setPageText(page, items, transform, styles);
      setModelVersion((version) => version + 1);
    },
    [model],
  );
  // Where the page paints each glyph (its operator list): the words move to
  // their exact places once, after the page is first drawn (Codex review F1).
  const onPageGlyphs = useCallback(
    (page: number, words: readonly GlyphWord[]) => {
      if (model.hasPageGlyphs(page)) return;
      model.setPageGlyphs(page, words);
      setModelVersion((version) => version + 1);
    },
    [model],
  );

  // The pages near the view (drawn, with a layer) and every page's element.
  const [nearPages, setNearPages] = useState<ReadonlySet<number>>(() => new Set());
  const nearPagesRef = useRef<ReadonlySet<number>>(nearPages);
  nearPagesRef.current = nearPages;
  const pageEls = useRef(new Map<number, HTMLElement>());
  const registerPage = useCallback((page: number, element: HTMLElement | null) => {
    if (element) pageEls.current.set(page, element);
    else pageEls.current.delete(page);
  }, []);
  const onNearChange = useCallback((page: number, near: boolean) => {
    setNearPages((current) => {
      if (current.has(page) === near) return current;
      const next = new Set(current);
      if (near) next.add(page);
      else next.delete(page);
      return next;
    });
  }, []);

  /** The page under a client point, in its PDF points (clamped onto the
   *  nearest page across the gap between two pages), or null. */
  const pointAt = useCallback((clientX: number, clientY: number): PagePoint | null => {
    const near = nearPagesRef.current;
    const candidates = near.size ? [...near] : [...pageEls.current.keys()];
    let best: { page: number; element: HTMLElement; rect: DOMRect; distance: number } | null = null;
    for (const page of candidates) {
      const element = pageEls.current.get(page);
      if (!element) continue;
      const rect = element.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) continue;
      const distance = clientY < rect.top ? rect.top - clientY : clientY > rect.bottom ? clientY - rect.bottom : 0;
      if (!best || distance < best.distance) best = { page, element, rect, distance };
    }
    if (!best || best.distance > BETWEEN_PAGES_PX) return null;
    const widthPoints = Number(best.element.dataset.widthPoints);
    if (!widthPoints) return null;
    const scale = best.rect.width / widthPoints;
    return {
      page: best.page,
      x: Math.min(Math.max((clientX - best.rect.left) / scale, 0), widthPoints),
      y: Math.min(Math.max((clientY - best.rect.top) / scale, 0), best.rect.height / scale),
      pageEl: best.element,
    };
  }, []);

  const placed = useMemo(() => placeHighlights(model, highlights), [model, highlights]);
  const details = useMemo(() => new Map(highlights.map((highlight) => [highlight.id, highlight] as const)), [highlights]);
  const [hoveredHighlight, setHoveredHighlight] = useState<string | null>(null);
  // The open highlight, and where: the page and point clicked (its chip goes
  // above that part), or the page whose keyboard stop has the focus.
  const [activeHighlight, setActiveHighlight] = useState<ActiveHighlight | null>(null);
  const activeId = activeHighlight?.id ?? null;
  // A removed highlight cannot stay open or lit.
  useEffect(() => {
    if (activeHighlight && !details.has(activeHighlight.id)) setActiveHighlight(null);
    if (hoveredHighlight && !details.has(hoveredHighlight)) setHoveredHighlight(null);
  }, [details, activeHighlight, hoveredHighlight]);
  const onHighlightClick = useCallback((id: string | null, point?: PagePoint) => {
    setActiveHighlight(id && point ? { id, page: point.page, at: { x: point.x, y: point.y } } : null);
  }, []);
  const onHighlightFocus = useCallback((id: string | null, page: number) => {
    setActiveHighlight(id ? { id, page, at: null } : null);
  }, []);

  // Each near page's highlight boxes; an unchanged page keeps its array, so
  // its layer does not redraw.
  const pageHighlightsRef = useRef(new Map<number, HighlightOnPage[]>());
  const pageHighlights = useMemo(() => {
    void modelVersion; // a page's words placed moves its boxes
    const next = new Map<number, HighlightOnPage[]>();
    for (const page of nearPages) {
      const fresh = highlightsOnPage(model, placed, page);
      const previous = pageHighlightsRef.current.get(page);
      next.set(page, previous && samePageHighlights(previous, fresh) ? previous : fresh.length ? fresh : NO_PAGE_HIGHLIGHTS);
    }
    pageHighlightsRef.current = next;
    return next;
  }, [model, placed, nearPages, modelVersion]);

  const highlightAtPoint = useCallback(
    (point: PagePoint): string | null =>
      highlightAt(pageHighlightsRef.current.get(point.page) ?? highlightsOnPage(model, placed, point.page), point.x, point.y),
    [model, placed],
  );

  /** The first page at the top of the view (a keyboard selection with no
   *  caret starts there). */
  const firstShownPage = useCallback((): number | null => {
    const top = containerRef.current?.parentElement?.getBoundingClientRect().top ?? 0;
    let best: { page: number; bottom: number } | null = null;
    for (const page of nearPagesRef.current) {
      const rect = pageEls.current.get(page)?.getBoundingClientRect();
      if (!rect || rect.bottom <= top) continue;
      if (!best || rect.bottom < best.bottom) best = { page, bottom: rect.bottom };
    }
    return best?.page ?? null;
  }, []);

  /** Keep the head of a keyboard selection in view. */
  const revealBlock = useCallback(
    (index: number) => {
      const block = model.blocks[index];
      if (!block) return;
      const box = passageBox(block.page, block.spanId);
      if (box) box.scrollIntoView?.({ block: "nearest" });
      else keepTarget(block.page, 0, block.spanId, "center");
    },
    [model, passageBox, keepTarget],
  );

  // Reader RW5a: a single Ctrl+drag box inside a figure is a region of it
  // (only while the Reader asks for regions; otherwise today's word marquee).
  const regionAt = useCallback(
    (box: { page: number; rect: number[] }) => {
      if (!regionSelection) return null;
      const cx = (box.rect[0] + box.rect[2]) / 2;
      const cy = (box.rect[1] + box.rect[3]) / 2;
      const figure = blocks.find((block) => block.page === box.page && FIGURE_BLOCK_TYPES.has(block.blockType ?? "")
        && block.bbox.length === 4 && cx >= block.bbox[0] && cx <= block.bbox[2] && cy >= block.bbox[1] && cy <= block.bbox[3]);
      // The whole block's words, if it has any (its code points), as a block-snapped selection would.
      const text = figure?.text ?? "";
      return figure ? { spanId: figure.spanId, quote: text.trim() || "the figure", end: text.trim() ? [...text].length : 0 } : null;
    },
    [blocks, regionSelection],
  );

  const sel = usePdfSelection({
    model,
    containerRef,
    selection,
    activeSpan,
    pointAt,
    onTextSelection,
    onSelectionCleared,
    highlightAt: highlightAtPoint,
    onHighlightClick,
    firstShownPage,
    revealBlock,
    ...(regionSelection ? { regionAt } : {}),
  });

  // The painted selection's boxes on each near page (unchanged pages keep
  // their array: a drag redraws only the pages it changes).
  const selectionRectsRef = useRef(new Map<number, Box[]>());
  const selectionRects = useMemo(() => {
    void modelVersion;
    const next = new Map<number, Box[]>();
    if (sel.painted.length) {
      for (const page of nearPages) {
        const fresh = rangeRects(model, sel.painted, page);
        if (!fresh.length) continue;
        const previous = selectionRectsRef.current.get(page);
        next.set(page, previous && sameBoxes(previous, fresh) ? previous : fresh);
      }
    }
    selectionRectsRef.current = next;
    return next;
  }, [model, sel.painted, nearPages, modelVersion]);

  // The active passage's frame steps back while a selection is painted on
  // it: its words already say where the learner is (no whole-paragraph wash).
  const framedSpan = useMemo(() => {
    if (!activeSpan) return null;
    const block = model.blockIndex(activeSpan);
    if (block === undefined) return activeSpan;
    const covered = sel.painted.some((range) => {
      const lo = Math.min(range.anchor.block, range.head.block);
      const hi = Math.max(range.anchor.block, range.head.block);
      return block >= lo && block <= hi;
    });
    return covered ? null : activeSpan;
  }, [activeSpan, model, sel.painted]);

  const caret = useMemo((): { page: number; box: Box } | null => {
    void modelVersion;
    if (!sel.caret) return null;
    const box = model.geometry(sel.caret.block).boxes[sel.caret.unit]?.[0];
    return box ? { page: model.blocks[sel.caret.block].page, box } : null;
  }, [model, sel.caret, modelVersion]);

  const marqueeByPage = useMemo(() => {
    const map = new Map<number, number[][]>();
    for (const box of sel.marqueeBoxes) {
      const list = map.get(box.page) ?? [];
      list.push(box.rect);
      map.set(box.page, list);
    }
    return map;
  }, [sel.marqueeBoxes]);

  // The pointer over the pages: a highlight under it lights, and the cursor
  // says what a click does (a formula or table: select it whole; text: a caret).
  const [cursor, setCursor] = useState<string>("text");
  const onPagesMouseMove = useCallback(
    (event: React.MouseEvent) => {
      if (sel.pressing || sel.sweeping) return;
      const target = event.target as HTMLElement;
      if (target.closest?.("[data-pdf-ui], button, input, textarea, a")) return;
      const point = target.closest?.("[data-pdf-page]") ? pointAt(event.clientX, event.clientY) : null;
      const hovered = point ? highlightAtPoint(point) : null;
      setHoveredHighlight((current) => (current === hovered ? current : hovered));
      let next = "default";
      if (hovered) next = "pointer";
      else if (point) {
        const block = blockAt(model, point.page, point.x, point.y);
        const inside = block !== null && (() => {
          const [x0, y0, x1, y1] = model.blocks[block].bbox;
          return point.x >= x0 - 2 && point.x <= x1 + 2 && point.y >= y0 - 2 && point.y <= y1 + 2;
        })();
        next = inside && block !== null ? (model.blocks[block].atomic ? "pointer" : "text") : "default";
      }
      setCursor((current) => (current === next ? current : next));
    },
    [sel.pressing, sel.sweeping, pointAt, highlightAtPoint, model],
  );

  // The Reader's highlight callbacks through refs: the pages' props stay the
  // same while the Reader re-renders, so no page redraws for it.
  const highlightActions = useRef({ onHighlightOpen, onHighlightRemove });
  highlightActions.current = { onHighlightOpen, onHighlightRemove };
  const removeHighlight = useCallback((id: string) => {
    setActiveHighlight(null);
    setHoveredHighlight(null);
    highlightActions.current.onHighlightRemove?.(id);
    // The keyboard stays on the pages, not on a removed stop.
    containerRef.current?.focus({ preventScroll: true });
  }, []);
  const openHighlight = useCallback((id: string) => highlightActions.current.onHighlightOpen?.(id), []);

  const onPagesKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      const target = event.target as HTMLElement;
      const editing = target.isContentEditable || Boolean(target.closest?.("input, textarea, select"));
      if (!editing && activeId && target === containerRef.current) {
        if (event.key === "Delete" || event.key === "Backspace") {
          event.preventDefault();
          removeHighlight(activeId);
          return;
        }
        if (event.key === "Enter") {
          event.preventDefault();
          openHighlight(activeId);
          return;
        }
        if (event.key === "Escape") {
          event.preventDefault();
          setActiveHighlight(null);
          return;
        }
      }
      sel.onKeyDown(event);
    },
    [activeId, removeHighlight, openHighlight, sel],
  );

  // Right-click → tag menu: on the painted selection it tags the selection;
  // elsewhere on a passage, the whole passage.
  const onContextMenu = useCallback(
    (event: React.MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest?.("[data-pdf-page]") || target.closest?.("[data-pdf-ui]")) return;
      const point = pointAt(event.clientX, event.clientY);
      if (!point) return;
      const under = sel.selectionUnder(point);
      if (under) {
        event.preventDefault();
        onTagMenu({ x: event.clientX, y: event.clientY, spanId: under.spanId, quote: under.quote, nodes: under.nodes });
        return;
      }
      const block = blockAt(model, point.page, point.x, point.y);
      if (block === null) return;
      const [x0, y0, x1, y1] = model.blocks[block].bbox;
      if (point.x < x0 || point.x > x1 || point.y < y0 || point.y > y1) return;
      event.preventDefault();
      onTagMenu({ x: event.clientX, y: event.clientY, spanId: model.blocks[block].spanId, quote: null });
    },
    [pointAt, sel, model, onTagMenu],
  );

  // RW3a: the layout the Reader's mark spacing reads -- each shown page's own
  // size at the width pages are drawn (zoom, resize), with the "pages left
  // out" line where the pane draws one.
  const reportedWidth = Math.max(320, containerWidth - 2) * zoom;
  useEffect(() => {
    if (!onPageLayout || containerWidth <= 0 || !sizes) return;
    const pages = coveredPages.flatMap((page, index) => {
      const size = sizes.get(page);
      return size
        ? [{ page, widthPoints: size.widthPoints, heightPoints: size.heightPoints, leftOutBefore: index > 0 && coveredPages[index - 1] !== page - 1 }]
        : [];
    });
    onPageLayout({ widthPx: reportedWidth, pages });
  }, [reportedWidth, containerWidth, sizes, coveredPages, onPageLayout]);

  if (!doc) {
    return (
      <div ref={containerRef} style={{ padding: 24 }}>
        <Faint style={{ fontSize: 12 }}>◐ loading original PDF…</Faint>
      </div>
    );
  }

  const pageWidth = Math.max(320, containerWidth - 2) * zoom;
  const busy = sel.pressing || sel.sweeping;
  return (
    <div
      ref={containerRef}
      className={["ll-pdf-pages", sel.sweeping ? "ll-block-sweeping" : sel.marqueeArmed || sel.marqueeDraft ? "ll-marquee-armed" : ""].filter(Boolean).join(" ")}
      tabIndex={0}
      role="document"
      aria-label="Original PDF. Drag, or hold Shift and use the arrow keys, to select. Tab reaches your highlights."
      onMouseDown={sel.onMouseDown}
      onMouseMove={onPagesMouseMove}
      onMouseLeave={() => setHoveredHighlight(null)}
      onKeyDown={onPagesKeyDown}
      onContextMenu={onContextMenu}
      style={{ display: "flex", flexDirection: "column", gap: 0, cursor: busy ? "text" : cursor }}
    >
      <div
        data-pdf-ui=""
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "4px 0 10px 0",
          position: "sticky",
          top: -18, // tucks under the scroll container's 18px padding
          zIndex: 5,
          background: COLOR.bg,
          cursor: "default",
        }}
      >
        <Faint style={{ fontSize: 11 }}>{pagesShownLabel(coveredPages.length, doc.numPages)}</Faint>
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
      {/* What the keyboard selected, read out (nothing visible). */}
      <div aria-live="polite" style={VISUALLY_HIDDEN}>{sel.announcement}</div>
      <div style={{ overflowX: zoom > 1 ? "auto" : "hidden", display: "flex", flexDirection: "column", gap: 14 }}>
        {coveredPages.map((page, index) => {
          const onPage = pageHighlights.get(page) ?? NO_PAGE_HIGHLIGHTS;
          return (
            <div key={page}>
              {index > 0 && coveredPages[index - 1] !== page - 1 ? (
                <Faint style={{ fontSize: 10, display: "block", padding: "2px 0 12px 0" }}>
                  {pagesLeftOutLabel(coveredPages[index - 1] + 2, page)}
                </Faint>
              ) : null}
              <PdfPage
                doc={doc}
                pageIndex={page}
                widthPx={pageWidth}
                size={sizes?.get(page) ?? null}
                model={model}
                onPageText={onPageText}
                onPageGlyphs={onPageGlyphs}
                onNearChange={onNearChange}
                registerPage={registerPage}
                blocks={blocksByPage.get(page) ?? NO_BLOCKS}
                guidanceSpans={guidanceSpans}
                {...(coveredSpans ? { coveredSpans } : {})}
                activeSpan={framedSpan}
                findQuery={findOpen ? findQuery.trim() : ""}
                inlineNote={inlineNote}
                {...(inlineNotes && inlineNotes.length ? { inlineNotes } : {})}
                marks={marks}
                selectionRects={selectionRects.get(page) ?? NO_BOXES}
                caret={caret && caret.page === page ? caret.box : null}
                highlights={onPage}
                details={details}
                hovered={hoveredHighlight && onPage.some((entry) => entry.id === hoveredHighlight) ? hoveredHighlight : null}
                active={activeId && onPage.some((entry) => entry.id === activeId) ? activeId : null}
                chip={activeHighlight && activeHighlight.page === page && onPage.some((entry) => entry.id === activeHighlight.id) ? activeHighlight : null}
                marqueeRects={marqueeByPage.get(page) ?? NO_MARQUEE}
                marqueeDraft={sel.marqueeDraft && sel.marqueeDraft.page === page ? sel.marqueeDraft.rect : null}
                onHighlightFocus={onHighlightFocus}
                onHighlightOpen={onHighlightOpen ? openHighlight : undefined}
                onHighlightRemove={onHighlightRemove ? removeHighlight : undefined}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
});

const NO_BLOCKS: ReaderPdfBlockDto[] = [];

const VISUALLY_HIDDEN = {
  position: "absolute" as const,
  width: 1,
  height: 1,
  overflow: "hidden" as const,
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap" as const,
};

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

/** How long a page's operator list waits for one of its fonts. */
const FONT_WAIT_MS = 3_000;

/** The page's words where its glyphs are painted (`operatorWords`), or null
 *  when its operator list cannot be read (the text content's words stay).
 *  Annotations are left out: their appearances are not the page's text. */
async function paintedWords(
  page: { getOperatorList: (options?: { annotationMode?: number }) => Promise<{ fnArray: number[]; argsArray: unknown[] }>; commonObjs?: unknown },
  transform: readonly number[],
): Promise<GlyphWord[] | null> {
  try {
    const ops = (pdfjs as { OPS?: Record<string, number> }).OPS;
    if (!ops) return null;
    const annotationMode = (pdfjs as { AnnotationMode?: { DISABLE?: number } }).AnnotationMode?.DISABLE;
    const opList = await page.getOperatorList(annotationMode === undefined ? undefined : { annotationMode });
    const objects = page.commonObjs as
      | { has: (id: string) => boolean; get: ((id: string) => unknown) & ((id: string, callback: (data: unknown) => void) => unknown) }
      | undefined;
    const fonts = new Map<string, PdfFontInfo | null>();
    for (let index = 0; index < opList.fnArray.length; index++) {
      if (opList.fnArray[index] !== ops.setFont) continue;
      const name = String((opList.argsArray[index] as unknown[] | undefined)?.[0] ?? "");
      if (!name || fonts.has(name)) continue;
      let font: unknown = null;
      if (objects) {
        font = objects.has(name)
          ? objects.get(name)
          : await Promise.race([
              new Promise<unknown>((resolve) => objects.get(name, resolve)),
              new Promise<null>((resolve) => window.setTimeout(() => resolve(null), FONT_WAIT_MS)),
            ]);
      }
      fonts.set(name, font && typeof font === "object" ? (font as PdfFontInfo) : null);
    }
    return operatorWords(opList, ops, (name) => fonts.get(name) ?? null, transform);
  } catch {
    return null;
  }
}

/** The open highlight: where its chip shows (the page, and the point
 *  clicked in it, or null when its keyboard stop there has the focus). */
interface ActiveHighlight {
  id: string;
  page: number;
  at: { x: number; y: number } | null;
}

function isGlyphItem(item: unknown): item is GlyphItem {
  return typeof item === "object" && item !== null && "str" in item && "transform" in item;
}

function isCancelled(error: unknown): boolean {
  return typeof error === "object" && error !== null && (error as { name?: string }).name === "RenderingCancelledException";
}

interface PdfPageProps {
  doc: PDFDocumentProxy;
  pageIndex: number;
  widthPx: number;
  /** The page's own size, read with the document: its placeholder's shape before it is drawn. */
  size: PageGeometry | null;
  model: SelectionModel;
  onPageText: (page: number, items: readonly GlyphItem[], transform: readonly number[], styles?: TextStyles | null) => void;
  onPageGlyphs: (page: number, words: readonly GlyphWord[]) => void;
  onNearChange: (page: number, near: boolean) => void;
  registerPage: (page: number, element: HTMLElement | null) => void;
  blocks: ReaderPdfBlockDto[];
  guidanceSpans: Set<string>;
  coveredSpans?: ReadonlySet<string>;
  activeSpan: string | null;
  findQuery: string;
  inlineNote: { spanId: string; node: ReactNode } | null;
  inlineNotes?: ReadonlyArray<{ spanId: string; node: ReactNode }>;
  marks: ReadonlyMap<string, ReactNode> | null;
  selectionRects: readonly Box[];
  caret: Box | null;
  highlights: readonly HighlightOnPage[];
  details: ReadonlyMap<string, PdfHighlight>;
  hovered: string | null;
  active: string | null;
  chip: ActiveHighlight | null;
  marqueeRects: readonly number[][];
  marqueeDraft: number[] | null;
  onHighlightFocus: (id: string | null, page: number) => void;
  onHighlightOpen?: (id: string) => void;
  onHighlightRemove?: (id: string) => void;
}

const PdfPage = memo(function PdfPage({
  doc,
  pageIndex,
  widthPx,
  size,
  model,
  onPageText,
  onPageGlyphs,
  onNearChange,
  registerPage,
  blocks,
  guidanceSpans,
  coveredSpans,
  activeSpan,
  findQuery,
  inlineNote,
  inlineNotes,
  marks,
  selectionRects,
  caret,
  highlights,
  details,
  hovered,
  active,
  chip,
  marqueeRects,
  marqueeDraft,
  onHighlightFocus,
  onHighlightOpen,
  onHighlightRemove,
}: PdfPageProps) {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const textRef = useRef<HTMLDivElement | null>(null);
  const [near, setNear] = useState(false);
  // Drawn now (released pages are not); the size it was drawn at stays, so a
  // released page keeps its shape even without the document's sizes.
  const [drawn, setDrawn] = useState(false);
  const [measured, setMeasured] = useState<PageGeometry | null>(null);
  const renderedKeyRef = useRef<string | null>(null);

  const setWrapper = useCallback(
    (element: HTMLDivElement | null) => {
      wrapperRef.current = element;
      registerPage(pageIndex, element);
    },
    [registerPage, pageIndex],
  );

  // Near the view: drawn; far from it: released (virtualized pages).
  useEffect(() => {
    const node = wrapperRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((entry) => setNear(entry.isIntersecting)),
      { rootMargin: NEAR_VIEW_MARGIN },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    onNearChange(pageIndex, near);
  }, [near, pageIndex, onNearChange]);
  useEffect(() => () => onNearChange(pageIndex, false), [pageIndex, onNearChange]);

  useEffect(() => {
    if (!near || widthPx <= 0) return;
    const renderKey = `${pageIndex}:${Math.round(widthPx)}`;
    if (renderedKeyRef.current === renderKey && model.hasPageText(pageIndex)) return;
    let cancelled = false;
    let task: { promise: Promise<unknown>; cancel?: () => void } | null = null;
    (async () => {
      try {
        const page = await doc.getPage(pageIndex + 1);
        const base = page.getViewport({ scale: 1 });
        // The page's own text first: the selection model places its words
        // with it, and the text layer is drawn from the same content.
        let content: Awaited<ReturnType<typeof page.getTextContent>> | null = null;
        if (typeof page.getTextContent === "function") {
          try {
            content = await page.getTextContent();
          } catch {
            content = null;
          }
        }
        if (cancelled) return;
        const items: GlyphItem[] = [];
        if (content && Array.isArray(base.transform)) {
          for (const item of content.items as unknown[]) if (isGlyphItem(item)) items.push(item);
          onPageText(pageIndex, items, base.transform, (content as { styles?: TextStyles }).styles ?? null);
        }
        else if (!model.hasPageText(pageIndex)) onPageText(pageIndex, [], base.transform ?? [1, 0, 0, -1, 0, base.height]);
        if (renderedKeyRef.current === renderKey) return;
        const scale = widthPx / base.width;
        const viewport = page.getViewport({ scale });
        const canvas = canvasRef.current;
        const textDiv = textRef.current;
        if (!canvas || !textDiv) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(viewport.width * dpr);
        canvas.height = Math.floor(viewport.height * dpr);
        const context = canvas.getContext("2d");
        if (!context) return;
        task = page.render({
          canvas,
          canvasContext: context,
          viewport,
          transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : undefined,
        });
        await task.promise;
        if (cancelled) return;
        textDiv.replaceChildren();
        const textLayer = new pdfjs.TextLayer({
          textContentSource: content ?? page.streamTextContent(),
          container: textDiv,
          viewport,
        });
        await textLayer.render();
        if (cancelled) return;
        renderedKeyRef.current = renderKey;
        setMeasured((current) =>
          current && current.widthPoints === base.width && current.heightPoints === base.height
            ? current
            : { widthPoints: base.width, heightPoints: base.height },
        );
        setDrawn(true);
        // Drawn: now where each glyph is painted, read once per page. Only a
        // page whose text runs hold several words needs it (a run of one word
        // is already where it is drawn: an OCR'd scan's text layer).
        if (
          !model.hasPageGlyphs(pageIndex) &&
          Array.isArray(base.transform) &&
          typeof page.getOperatorList === "function" &&
          items.some((item) => /\S\s+\S/.test(item.str))
        ) {
          const words = await paintedWords(page, base.transform);
          if (cancelled || !words) return;
          onPageGlyphs(pageIndex, words);
        }
      } catch (error) {
        if (!cancelled && !isCancelled(error)) console.error(`pdf page ${pageIndex} render failed`, error);
      }
    })();
    return () => {
      cancelled = true;
      task?.cancel?.();
    };
  }, [near, doc, pageIndex, widthPx, model, onPageText, onPageGlyphs]);

  // Far from the view: the canvas's pixels and the text layer go (a 600-page
  // book keeps only the pages near the view drawn). Its size stays. What
  // pdf.js read to draw it (its operator lists, the one the words were placed
  // from among them, and its images) goes too, as pdf.js's own viewer lets it
  // go: drawn again, the page is read again; its words stay placed.
  useEffect(() => {
    if (near) return;
    const wasDrawn = renderedKeyRef.current !== null;
    const canvas = canvasRef.current;
    if (canvas && (canvas.width || canvas.height)) {
      canvas.width = 0;
      canvas.height = 0;
    }
    textRef.current?.replaceChildren();
    renderedKeyRef.current = null;
    setDrawn(false);
    if (wasDrawn) {
      void doc
        .getPage(pageIndex + 1)
        .then((page) => (page as { cleanup?: () => unknown }).cleanup?.())
        .catch(() => undefined);
    }
    // Released on leaving the view only (doc and page are fixed for a page).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [near]);

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
  }, [findQuery, drawn]);

  // Drawn (now or before): the page's size; not yet drawn: its size read with
  // the document (RW3a review F5), else a letter-ish placeholder.
  const known = measured ?? size;
  const aspect = known ? known.heightPoints / known.widthPoints : 1.294;
  const scale = known ? widthPx / known.widthPoints : 1;
  return (
    <div
      ref={setWrapper}
      data-pdf-page={pageIndex}
      data-width-points={known?.widthPoints ?? 0}
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
      <div ref={textRef} className="textLayer" style={{ position: "absolute", inset: 0 }} />
      {drawn
        ? blocks
            .filter((b) => b.bbox.length === 4)
            .map((b) => {
              // Where a passage is: the active one's frame, a guided one's
              // dashed frame. A selection paints its own words (the layer).
              const active = activeSpan === b.spanId;
              const guided = guidanceSpans.has(b.spanId);
              // RW1b: the next step's fold on the original page -- an opaque
              // cover over the book's next lines while the learner tries.
              const covered = Boolean(coveredSpans?.has(b.spanId));
              return (
                <div
                  key={b.spanId}
                  data-span-id={b.spanId}
                  title={covered ? "Folded while you try the next step" : guided ? "Worth a second look for your learning path" : undefined}
                  {...(covered ? { "data-folded": "" } : {})}
                  style={{
                    position: "absolute",
                    left: b.bbox[0] * scale,
                    top: b.bbox[1] * scale,
                    width: (b.bbox[2] - b.bbox[0]) * scale,
                    height: (b.bbox[3] - b.bbox[1]) * scale,
                    pointerEvents: "none",
                    border: covered ? `1px dotted ${COLOR.textDim}` : active ? `2px solid ${COLOR.amber}` : guided ? `2px dashed ${COLOR.purplePill}` : "2px solid transparent",
                    background: covered ? COLOR.bg : active ? "rgba(245, 166, 35, 0.06)" : guided ? "rgba(90, 77, 138, 0.10)" : "transparent",
                    // Paint changes are instant, never eased: the Reader does not animate (attention
                    // budget, UX §4.12; gate G54).
                  }}
                />
              );
            })
        : null}
      {near && known ? (
        <PdfSelectionLayer
          page={pageIndex}
          scale={scale}
          selectionRects={selectionRects}
          caret={caret}
          highlights={highlights}
          details={details}
          hovered={hovered}
          active={active}
          chip={chip}
          marqueeRects={marqueeRects}
          marqueeDraft={marqueeDraft}
          onHighlightFocus={onHighlightFocus}
          onHighlightOpen={onHighlightOpen}
          onHighlightRemove={onHighlightRemove}
        />
      ) : null}
      {drawn && inlineNote
        ? blocks
            .filter((b) => b.spanId === inlineNote.spanId && b.bbox.length === 4)
            .slice(0, 1)
            .map((b) => (
              <div
                key={`inline-${b.spanId}`}
                data-inline-note={b.spanId}
                data-pdf-ui=""
                style={{
                  position: "absolute",
                  left: b.bbox[0] * scale,
                  top: b.bbox[3] * scale + 2,
                  width: Math.max(220, (b.bbox[2] - b.bbox[0]) * scale),
                  zIndex: 3,
                  background: COLOR.bg,
                  border: `1px solid ${COLOR.border}`,
                  padding: "2px 6px",
                  cursor: "default",
                }}
              >
                {inlineNote.node}
              </div>
            ))
        : null}
      {drawn && inlineNotes
        ? inlineNotes.flatMap((note) => blocks
            .filter((b) => b.spanId === note.spanId && b.bbox.length === 4)
            .slice(0, 1)
            .map((b) => (
              <div
                key={`figure-${b.spanId}`}
                data-inline-figures={b.spanId}
                data-pdf-ui=""
                style={{
                  position: "absolute",
                  left: b.bbox[0] * scale,
                  top: b.bbox[3] * scale + 2,
                  width: Math.max(320, (b.bbox[2] - b.bbox[0]) * scale),
                  zIndex: 4,
                  background: COLOR.bg,
                  cursor: "default",
                }}
              >
                {note.node}
              </div>
            )))
        : null}
      {drawn && marks && marks.size > 0
        ? blocks
            .filter((b) => marks.has(b.spanId) && b.bbox.length === 4)
            .map((b) => (
              <div
                key={`cue-${b.spanId}`}
                data-cue-gutter={b.spanId}
                data-pdf-ui=""
                style={{ position: "absolute", left: Math.max(0, b.bbox[0] * scale - 24), top: b.bbox[1] * scale, zIndex: 4 }}
              >
                {marks.get(b.spanId)}
              </div>
            ))
        : null}
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
});
