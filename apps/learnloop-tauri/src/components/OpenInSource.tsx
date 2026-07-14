// Open-in-source viewer (§9.2): read-only. Resolves a block_span_v1 locator to
// its geometry + text and records a source_exposure event on every view. No page
// raster is persisted. Local originals are rendered on demand; unavailable PDFs
// use an honest text fallback. HTML/text spans scroll to the block anchor.

import { useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { SpanNeighborDto, SpanViewDto } from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill } from "./term";

export function OpenInSource({
  extractionId,
  spanId,
  context,
  entityType,
  entityId,
  onClose
}: {
  extractionId: string;
  spanId: string;
  context?: string;
  entityType?: string | null;
  entityId?: string | null;
  onClose: () => void;
}) {
  const [currentSpanId, setCurrentSpanId] = useState(spanId);
  const [view, setView] = useState<SpanViewDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .getSpanView({ extractionId, spanId: currentSpanId, context: context ?? "provenance", entityType, entityId })
      .then((res) => {
        if (!cancelled) {
          setView(res.spanView);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [extractionId, currentSpanId, context, entityType, entityId]);

  const heading = view
    ? view.sectionPath.length > 0
      ? view.sectionPath.join(" › ")
      : view.blockType
    : "Open in source";

  return (
    <div style={backdropStyle} onClick={onClose}>
      <div style={panelStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ fontSize: 13, color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {heading}
          </span>
          {view ? <Pill color={view.viewerMode.startsWith("pdf_") ? "amber" : "cyan"}>{view.viewerMode}</Pill> : null}
          <span style={{ marginLeft: "auto", cursor: "pointer", color: COLOR.textFaint, fontSize: 12 }} onClick={onClose}>
            esc ✕
          </span>
        </div>

        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "14px 18px" }}>
          {loading ? <Faint>loading span…</Faint> : null}
          {error ? <div style={{ color: COLOR.red, fontSize: 12 }}>{error}</div> : null}
          {view ? (
            <>
              <div style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO, marginBottom: 8 }}>
                {view.sourceId ? `${view.sourceId} · ` : ""}
                {view.locator} · {view.locatorScheme}
              </div>

              {view.viewerMode === "pdf_text" || view.viewerMode === "pdf_page" ? (
                <div>
                  <Faint style={{ fontSize: 11 }}>
                    {view.pageRender ? "source page" : "text fallback"} — page {view.page ?? "?"}, cited region highlighted
                  </Faint>
                  {view.pageRender ? (
                    <div style={{ position: "relative", marginTop: 8 }}>
                      <img
                        src={view.pageRender}
                        alt={`Source page ${view.page ?? ""}`}
                        style={{ width: "100%", display: "block", border: `1px solid ${COLOR.border}` }}
                      />
                      <PdfRegion bbox={view.bbox} pageSize={view.pageRenderSize} />
                    </div>
                  ) : null}
                  <div style={pageBoxStyle}>
                    <div style={highlightBlockStyle}>{view.text}</div>
                  </div>
                  {view.bbox ? (
                    <div style={{ marginTop: 6 }}>
                      <Faint style={{ fontSize: 11 }}>
                        bbox [{view.bbox.map((n) => Math.round(n)).join(", ")}]
                      </Faint>
                    </div>
                  ) : null}
                  {view.pageSpans.length > 1 ? (
                    <div style={{ marginTop: 4 }}>
                      <Faint style={{ fontSize: 11 }}>{view.pageSpans.length} spans highlighted on this page</Faint>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div>
                  <Faint style={{ fontSize: 11 }}>block anchor {view.spanId}</Faint>
                  <div style={highlightBlockStyle}>{view.text}</div>
                </div>
              )}

              {view.acquisitionKind === "youtube" && view.canonicalUri ? (
                <YouTubeEmbed view={view} />
              ) : null}

              <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}>
                <button
                  style={{ ...navBtn, opacity: view.previousSpans.length ? 1 : 0.4, cursor: view.previousSpans.length ? "pointer" : "default" }}
                  disabled={!view.previousSpans.length}
                  onClick={() => {
                    const prev = view.previousSpans[view.previousSpans.length - 1];
                    if (prev) setCurrentSpanId(prev.spanId);
                  }}
                >
                  ← prev
                </button>
                <button
                  style={{ ...navBtn, opacity: view.nextSpans.length ? 1 : 0.4, cursor: view.nextSpans.length ? "pointer" : "default" }}
                  disabled={!view.nextSpans.length}
                  onClick={() => {
                    const next = view.nextSpans[0];
                    if (next) setCurrentSpanId(next.spanId);
                  }}
                >
                  next →
                </button>
              </div>

              <NeighborList label="before" spans={view.previousSpans} onJump={setCurrentSpanId} />
              <NeighborList label="after" spans={view.nextSpans} onJump={setCurrentSpanId} />
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function PdfRegion({ bbox, pageSize }: { bbox: number[] | null; pageSize: number[] | null }) {
  if (!bbox || bbox.length < 4 || !pageSize || pageSize.length < 2 || pageSize[0] <= 0 || pageSize[1] <= 0) return null;
  const [x0, y0, x1, y1] = bbox;
  const left = Math.max(0, Math.min(100, (x0 / pageSize[0]) * 100));
  const top = Math.max(0, Math.min(100, (y0 / pageSize[1]) * 100));
  const width = Math.max(0.5, Math.min(100 - left, ((x1 - x0) / pageSize[0]) * 100));
  const height = Math.max(0.5, Math.min(100 - top, ((y1 - y0) / pageSize[1]) * 100));
  return (
    <div
      aria-label="cited source region"
      style={{
        position: "absolute",
        left: `${left}%`,
        top: `${top}%`,
        width: `${width}%`,
        height: `${height}%`,
        border: `2px solid ${COLOR.amber}`,
        background: "rgba(245, 166, 35, 0.12)",
        boxShadow: `0 0 0 1px ${COLOR.bg}`,
        pointerEvents: "none"
      }}
    />
  );
}

// ── YouTube embedded player (§9.2) ──────────────────────────────────────────
// media-extended-style: seek the privacy-enhanced (youtube-nocookie.com) IFrame to
// the cited range's start. Loading it is an explicit-action fetch of the already-
// imported public URL — no consent dialog (stated in the privacy copy). Videos that
// disallow embedding fall back to opening externally at the timestamp.

function youtubeVideoId(uri: string): string | null {
  try {
    const url = new URL(uri);
    const host = url.hostname.replace(/^www\./, "");
    if (host === "youtu.be") return url.pathname.slice(1).split("/")[0] || null;
    if (host.endsWith("youtube.com") || host.endsWith("youtube-nocookie.com")) {
      const v = url.searchParams.get("v");
      if (v) return v;
      const parts = url.pathname.split("/").filter(Boolean); // /embed/ID or /v/ID
      const marker = parts.findIndex((p) => p === "embed" || p === "v");
      if (marker >= 0 && parts[marker + 1]) return parts[marker + 1];
    }
  } catch {
    return null;
  }
  return null;
}

/** Parse a time_range_v1 locator (`t=<start>-<end>`, seconds) → [start, end]. The
 *  span-view locator wraps it, e.g. `span:t=12-30` or `t=12.5-30`. */
function timeRange(view: SpanViewDto): { start: number; end: number | null } {
  const raw = (view.locator || "").replace(/^span:(?:[^/]+\/)?/, "");
  const match = /^t=([0-9]+(?:\.[0-9]+)?)-([0-9]+(?:\.[0-9]+)?)$/.exec(raw);
  if (match) return { start: Math.floor(Number(match[1])), end: Math.floor(Number(match[2])) };
  return { start: 0, end: null };
}

function fmtTime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

function YouTubeEmbed({ view }: { view: SpanViewDto }) {
  const uri = view.canonicalUri as string;
  const videoId = youtubeVideoId(uri);
  const { start, end } = timeRange(view);

  if (!videoId) {
    // Non-embeddable / unparseable → external open at the source (existing behavior).
    return (
      <div style={{ marginTop: 12 }}>
        <a href={uri} target="_blank" rel="noreferrer" style={{ color: COLOR.amberLink, fontSize: 12, fontFamily: FONT_MONO }}>
          open externally ↗
        </a>
      </div>
    );
  }

  const src = `https://www.youtube-nocookie.com/embed/${videoId}?start=${start}&rel=0`;
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ position: "relative", paddingTop: "56.25%", background: "#000", border: `1px solid ${COLOR.border}` }}>
        <iframe
          title="source video"
          src={src}
          allow="encrypted-media; picture-in-picture"
          referrerPolicy="strict-origin-when-cross-origin"
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", border: 0 }}
        />
      </div>
      {end !== null ? (
        <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, color: COLOR.amber, fontFamily: FONT_MONO }}>
            {fmtTime(start)}–{fmtTime(end)}
          </span>
          <div style={{ flex: 1, height: 4, background: COLOR.bgInput, position: "relative" }}>
            <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: "100%", background: COLOR.amber, opacity: 0.6 }} />
          </div>
        </div>
      ) : null}
      <Faint style={{ fontSize: 10, marginTop: 6, display: "block" }}>
        Loads YouTube&apos;s embedded player — an explicit fetch of the already-imported public URL
        (privacy-enhanced youtube-nocookie.com); no data leaves your vault.
      </Faint>
      <div style={{ marginTop: 4 }}>
        <a href={uri} target="_blank" rel="noreferrer" style={{ color: COLOR.amberLink, fontSize: 11, fontFamily: FONT_MONO }}>
          open externally ↗
        </a>
      </div>
    </div>
  );
}

function NeighborList({ label, spans, onJump }: { label: string; spans: SpanNeighborDto[]; onJump: (id: string) => void }) {
  if (!spans.length) return null;
  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ fontSize: 10, color: COLOR.amber, textTransform: "uppercase", letterSpacing: "0.12em", fontFamily: FONT_MONO, marginBottom: 4 }}>
        {label}
      </div>
      {spans.map((s) => (
        <div
          key={s.spanId}
          onClick={() => onJump(s.spanId)}
          style={{ cursor: "pointer", fontSize: 12, color: COLOR.textDim, padding: "3px 0", borderTop: `1px solid ${COLOR.border}` }}
        >
          {s.text}
          {s.truncated ? "…" : ""}
        </div>
      ))}
    </div>
  );
}

const backdropStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 220,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "6vh 5vw",
  backdropFilter: "blur(2px)"
};

const panelStyle: CSSProperties = {
  width: "min(720px, 100%)",
  maxHeight: "84vh",
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text
};

const headerStyle: CSSProperties = {
  padding: "12px 16px",
  borderBottom: `1px solid ${COLOR.border}`,
  display: "flex",
  alignItems: "center",
  gap: 12,
  flexShrink: 0
};

const pageBoxStyle: CSSProperties = {
  marginTop: 6,
  border: `1px dashed ${COLOR.borderStrong}`,
  background: "#0b0b0b",
  padding: 12,
  minHeight: 120
};

const highlightBlockStyle: CSSProperties = {
  borderLeft: `3px solid ${COLOR.amber}`,
  background: COLOR.bgInput,
  padding: "10px 14px",
  fontSize: 13,
  lineHeight: 1.7,
  color: COLOR.text,
  whiteSpace: "pre-wrap"
};

const navBtn: CSSProperties = {
  padding: "6px 14px",
  border: `1px solid ${COLOR.borderStrong}`,
  background: "transparent",
  color: COLOR.textDim,
  fontFamily: FONT_MONO,
  fontSize: 12
};
