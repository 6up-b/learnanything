// PdfReaderPane — Tier-2 embedded original-PDF reader.
//
// Renders the revision's original PDF (served from the vault's content-addressed
// originals store through the llpdf:// protocol) with pdf.js: canvas + selectable
// text layer per page, rendered lazily as pages scroll into view. Only pages the
// extraction actually covers are shown (a whole textbook may back a chapter-scoped
// ingest), with honest gap markers between non-adjacent pages. Block geometry from
// reader.pdf_view (PDF points, origin top-left — marker's bbox space) is overlaid
// per page; a native text selection is hit-tested against that geometry so
// captures land on the same span ids the markdown reader uses, and a click
// selects the containing span for the Ask panel.

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
  activeSpan: string | null;
  onSelectSpan: (spanId: string) => void;
  onTextSelection: (selection: { spanId: string; quote: string }) => void;
  onTagMenu: (request: TagMenuRequest) => void;
  onError: (message: string) => void;
}

interface FindMatch {
  page: number;
  ordinal: number;
}

export const PdfReaderPane = forwardRef<PdfReaderPaneHandle, PdfReaderPaneProps>(function PdfReaderPane(
  { fileUrl, blocks, trails, guidanceSpans, activeSpan, onSelectSpan, onTextSelection, onTagMenu, onError }: PdfReaderPaneProps,
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

  // Native text selection → {spanId, quote} via geometry overlap on the
  // selection's bounding rects. Shared by mouse-up capture and the tag menu.
  const resolveSelection = useCallback((): { spanId: string; quote: string } | null => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;
    const quote = selection.toString().replace(/\s+/g, " ").trim();
    if (!quote) return null;
    const range = selection.getRangeAt(0);
    const pageEl = pageElFor(range.startContainer);
    if (!pageEl) return null;
    const page = Number(pageEl.dataset.pdfPage);
    const widthPoints = Number(pageEl.dataset.widthPoints);
    const pageRect = pageEl.getBoundingClientRect();
    if (!pageRect.width || !widthPoints) return null;
    const scale = pageRect.width / widthPoints;
    // Overlap area per block across all selection rects → best-covered span.
    const overlaps = new Map<string, number>();
    for (const rect of Array.from(range.getClientRects())) {
      const x0 = (rect.left - pageRect.left) / scale;
      const x1 = (rect.right - pageRect.left) / scale;
      const y0 = (rect.top - pageRect.top) / scale;
      const y1 = (rect.bottom - pageRect.top) / scale;
      for (const block of blocksByPage.get(page) ?? []) {
        if (block.bbox.length !== 4) continue;
        const w = Math.min(x1, block.bbox[2]) - Math.max(x0, block.bbox[0]);
        const h = Math.min(y1, block.bbox[3]) - Math.max(y0, block.bbox[1]);
        if (w > 0 && h > 0) overlaps.set(block.spanId, (overlaps.get(block.spanId) ?? 0) + w * h);
      }
    }
    const best = [...overlaps.entries()].sort((a, b) => b[1] - a[1])[0];
    return best ? { spanId: best[0], quote } : null;
  }, [blocksByPage]);

  const onMouseUp = useCallback(() => {
    const resolved = resolveSelection();
    if (resolved) onTextSelection(resolved);
  }, [resolveSelection, onTextSelection]);

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

  const onClick = useCallback(
    (event: React.MouseEvent) => {
      const pageEl = pageElFor(event.target as Node);
      if (!pageEl) return;
      const selection = window.getSelection();
      if (selection && !selection.isCollapsed) return; // finishing a selection, not a click
      const block = blockAtPoint(pageEl, event.clientX, event.clientY);
      if (block) onSelectSpan(block.spanId);
    },
    [blockAtPoint, onSelectSpan],
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
    <div ref={containerRef} onMouseUp={onMouseUp} onClick={onClick} onContextMenu={onContextMenu} style={{ display: "flex", flexDirection: "column", gap: 0 }}>
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
  activeSpan,
  findQuery,
}: {
  doc: PDFDocumentProxy;
  pageIndex: number;
  widthPx: number;
  blocks: ReaderPdfBlockDto[];
  trails: AnnotationTrail[];
  guidanceSpans: Set<string>;
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
              const active = activeSpan === b.spanId;
              const guided = guidanceSpans.has(b.spanId);
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
                    border: active ? `2px solid ${COLOR.amber}` : guided ? `2px dashed ${COLOR.purplePill}` : "2px solid transparent",
                    background: active ? "rgba(245, 166, 35, 0.08)" : guided ? "rgba(90, 77, 138, 0.10)" : "transparent",
                  }}
                />
              );
            })
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
}
