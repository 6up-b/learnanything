// Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8, X13, X14;
// K15, C10, Q10, Q12).
//
//   From Strang · Exercise 6.1.12 · p.297 · original page ↗ · counts as a hint
//   Find the eigenvalues of the matrix …   (the transcription)
//   ▾ as printed (Strang p.297)                                       − +
//   ┃ (a crop of the exercise's own blocks from the page; nothing around them)
//     doesn't match the page? ▸ the transcription doesn't match the page
//
// What may show is the server's decision (`practice.as_printed`): during a
// check on your own nothing that locates the problem, only the figure it
// needs (Q10); a card written from a phone photo shows *your photo*. The crop
// is the stem the learner already has, so it is free and records nothing;
// the whole page before Submit is the book left open, one hint (Q12), which
// the screen that opens it counts. Collapsed by default, remembered open or
// closed on this device; the image's alt text is the transcribed stem, so a
// screen reader hears the same problem. The image is never re-read by OCR.
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type { AsPrintedViewDto, PrintedCropsDto } from "../api/dto";
import { errorMessage } from "../errors";
import { COLOR, FONT_MONO } from "./term";
import { OpenInSource } from "./OpenInSource";

export const AS_PRINTED_COPY = {
  originalPage: "original page ↗",
  countsAsHint: "counts as a hint",
  asPrinted: "as printed",
  solutionAsPrinted: "the solution as printed",
  pending: "cropping the page…",
  noOriginal: "the page image isn't available for this book · the transcription is above",
  failed: "Couldn't crop the page just now.",
  mismatchAsk: "doesn't match the page?",
  mismatchAction: "the transcription doesn't match the page",
  mismatchPlaceholder: "what differs, if you like (a sign, a subscript, the figure…)",
  mismatchSent: "noted for fixing · the card is unchanged until it's reworded",
  pageCounted: "the original page you opened counts as one hint",
  zoomIn: "zoom in",
  zoomOut: "zoom out",
} as const;

/** The per-device open/closed memory of *as printed* (UX: remembered per device). */
export const AS_PRINTED_OPEN_KEY = "learnloop.asPrinted.open";
/** Display zoom steps inside the frame (presentation only). */
const ZOOMS = [1, 1.5, 2, 3] as const;

const linkStyle: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
};

const toggleStyle: CSSProperties = { ...linkStyle, textDecoration: "none", color: COLOR.textDim };

function rememberedOpen(): boolean {
  try {
    return window.localStorage.getItem(AS_PRINTED_OPEN_KEY) === "1";
  } catch {
    return false;
  }
}

function rememberOpen(open: boolean): void {
  try {
    window.localStorage.setItem(AS_PRINTED_OPEN_KEY, open ? "1" : "0");
  } catch {
    /* a device that cannot remember starts closed */
  }
}

/** A call that may be absent (an older sidecar or a test's partial api). */
function maybe<T>(run: () => Promise<T> | undefined): Promise<T> | null {
  try {
    const promise = run();
    return promise && typeof (promise as Promise<T>).then === "function" ? promise : null;
  } catch {
    return null;
  }
}

/** The item's view (labels and the locator; no images), read once per item. */
export function useAsPrinted(practiceItemId: string | null | undefined): AsPrintedViewDto | null {
  const [state, setState] = useState<{ id: string | null; view: AsPrintedViewDto | null }>({ id: null, view: null });
  useEffect(() => {
    if (!practiceItemId) return;
    let alive = true;
    const promise = maybe(() => api.practiceAsPrinted({ practiceItemId }));
    promise?.then(
      (view) => { if (alive) setState({ id: practiceItemId, view }); },
      () => { if (alive) setState({ id: practiceItemId, view: null }); },
    );
    return () => { alive = false; };
  }, [practiceItemId]);
  return practiceItemId && state.id === practiceItemId && state.view?.enabled ? state.view : null;
}

/** "From Strang · Exercise 6.1.12 · p.297": the page part of the header locator. */
export function printedPageLabel(view: AsPrintedViewDto | null): string | null {
  return view?.kind === "page" && view.locator?.pageLabel ? `p.${view.locator.pageLabel}` : null;
}

/** *original page ↗*, labelled with its cost before Submit (Q12). */
export function OriginalPageLink({
  view,
  costs,
  onOpen,
}: {
  view: AsPrintedViewDto | null;
  /** Before Submit and not yet counted: say first that it counts as a hint. */
  costs: boolean;
  onOpen: (target: { extractionId: string; spanId: string; outlineSpanIds: string[] }) => void;
}) {
  if (!view || view.kind !== "page" || !view.originalPage) return null;
  const target = view.originalPage;
  return (
    <button type="button" data-testid="original-page" style={linkStyle} onClick={() => onOpen(target)}>
      {AS_PRINTED_COPY.originalPage}
      {costs ? ` · ${AS_PRINTED_COPY.countsAsHint}` : ""}
    </button>
  );
}

type Crop = { image: string | null };

function PrintedFrame({ crops, alt, status }: { crops: Crop[]; alt: string; status?: string }) {
  const [zoom, setZoom] = useState(0);
  const images = crops.filter((crop) => crop.image);
  if (images.length === 0) {
    return (
      <div role="status" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
        {status === "no_original" || status === "no_geometry" || status === "not_found" ? AS_PRINTED_COPY.noOriginal : AS_PRINTED_COPY.failed}
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", fontFamily: FONT_MONO, fontSize: 11 }}>
        <button type="button" aria-label={AS_PRINTED_COPY.zoomOut} style={toggleStyle} disabled={zoom === 0}
          onClick={() => setZoom((value) => Math.max(0, value - 1))}>−</button>
        <button type="button" aria-label={AS_PRINTED_COPY.zoomIn} style={toggleStyle} disabled={zoom === ZOOMS.length - 1}
          onClick={() => setZoom((value) => Math.min(ZOOMS.length - 1, value + 1))}>+</button>
      </div>
      <div data-testid="as-printed-frame" style={{ borderLeft: `1px solid ${COLOR.borderStrong}`, paddingLeft: 8, overflow: "auto", maxWidth: "100%" }}>
        <span aria-hidden="true" style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textFaint }}>§</span>
        {images.map((crop, index) => (
          <img
            key={index}
            src={crop.image as string}
            alt={index === 0 ? alt : `${alt} (continued)`}
            style={{ display: "block", width: `${ZOOMS[zoom] * 100}%`, maxWidth: zoom === 0 ? "100%" : "none", marginTop: index === 0 ? 0 : 6, background: "#fff" }}
          />
        ))}
      </div>
    </div>
  );
}

function TranscriptionReport({ practiceItemId }: { practiceItemId: string }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [state, setState] = useState<{ kind: "idle" | "sending" | "sent" } | { kind: "error"; message: string }>({ kind: "idle" });
  const send = async () => {
    if (state.kind === "sending") return;
    setState({ kind: "sending" });
    try {
      await api.reportTranscription({ practiceItemId, note: note.trim() || null });
      setState({ kind: "sent" });
      setOpen(false);
    } catch (error) {
      setState({ kind: "error", message: errorMessage(error, "Couldn't send the report.") });
    }
  };
  if (state.kind === "sent") {
    return <div role="status" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>{AS_PRINTED_COPY.mismatchSent}</div>;
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
      <span>
        {AS_PRINTED_COPY.mismatchAsk}{" "}
        <button type="button" style={linkStyle} aria-expanded={open} onClick={() => setOpen((value) => !value)}>
          {AS_PRINTED_COPY.mismatchAction} {open ? "▾" : "▸"}
        </button>
      </span>
      {open ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <textarea
            aria-label={AS_PRINTED_COPY.mismatchPlaceholder}
            placeholder={AS_PRINTED_COPY.mismatchPlaceholder}
            value={note}
            rows={2}
            onChange={(event) => setNote(event.target.value)}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 6, resize: "vertical", width: "100%" }}
          />
          <span>
            <button type="button" style={linkStyle} disabled={state.kind === "sending"} onClick={() => void send()}>
              {state.kind === "sending" ? "…" : "send ↵"}
            </button>
          </span>
          {state.kind === "error" ? <span role="alert" style={{ color: COLOR.red }}>{state.message}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

function photoDate(capturedAt: string | null | undefined): string | null {
  if (!capturedAt) return null;
  const date = new Date(capturedAt);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/** *▸ as printed* under the stem (or *the figure, as printed*, or *your photo*). */
export function AsPrinted({
  view,
  practiceItemId,
  altText,
}: {
  view: AsPrintedViewDto | null;
  practiceItemId: string;
  /** The transcribed stem: the image's alt text. */
  altText: string;
}) {
  // The figure a check needs is part of the stimulus: open from the start.
  const [open, setOpen] = useState(() => view?.kind === "figure" || rememberedOpen());
  const [crops, setCrops] = useState<{ status: "idle" | "pending" | "ready" | "failed"; view: AsPrintedViewDto | null }>({ status: "idle", view: null });
  const asked = useRef<string | null>(null);
  const kind = view?.kind ?? "none";
  const figure = kind === "figure";
  useEffect(() => {
    if (figure) setOpen(true);
  }, [figure]);
  useEffect(() => {
    if (!open || !view || (kind !== "page" && kind !== "figure")) return;
    const key = `${practiceItemId}:${kind}`;
    if (asked.current === key) return;
    asked.current = key;
    setCrops({ status: "pending", view: null });
    const promise = maybe(() => api.practiceAsPrinted({ practiceItemId, render: true }));
    if (!promise) {
      setCrops({ status: "failed", view: null });
      return;
    }
    promise.then(
      (rendered) => setCrops({ status: "ready", view: rendered }),
      () => setCrops({ status: "failed", view: null }),
    );
  }, [open, view, kind, practiceItemId]);
  if (!view || kind === "none") return null;

  const toggle = () => {
    setOpen((value) => {
      if (!figure) rememberOpen(!value);
      return !value;
    });
  };
  const taken = kind === "photo" ? photoDate(view.photo?.capturedAt) : null;
  const label = kind === "photo"
    ? `${view.label ?? "your photo"}${taken ? ` (${taken})` : ""}`
    : view.label ?? AS_PRINTED_COPY.asPrinted;
  // A rendered view that changed kind (a check began) is never shown.
  const rendered = crops.view && crops.view.kind === kind ? crops.view : null;
  return (
    <div data-testid="as-printed" data-kind={kind} style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 6 }}>
      <button type="button" style={toggleStyle} aria-expanded={open} onClick={toggle}>
        {open ? "▾" : "▸"} {label}
      </button>
      {open && kind === "photo" && view.photo ? <PhotoFrame captureId={view.photo.captureId} /> : null}
      {open && (kind === "page" || kind === "figure") ? (
        crops.status === "pending" || crops.status === "idle" ? (
          <div role="status" aria-live="polite" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
            <span aria-hidden="true">◐</span> {AS_PRINTED_COPY.pending}
          </div>
        ) : (
          <PrintedFrame crops={(rendered?.crops ?? []) as Crop[]} alt={altText} status={rendered?.status ?? "failed"} />
        )
      ) : null}
      {open && kind === "page" && view.transcriptionReport ? <TranscriptionReport practiceItemId={practiceItemId} /> : null}
    </div>
  );
}

function PhotoFrame({ captureId }: { captureId: string }) {
  const [media, setMedia] = useState<{ dataUrl: string } | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let alive = true;
    const promise = maybe(() => api.getCaptureMedia(captureId));
    if (!promise) {
      setFailed(true);
      return;
    }
    promise.then((value) => { if (alive) setMedia(value); }, () => { if (alive) setFailed(true); });
    return () => { alive = false; };
  }, [captureId]);
  if (failed) return <div role="status" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>Couldn't load your photo.</div>;
  if (!media) return <div role="status" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>loading your photo…</div>;
  return (
    <div style={{ borderLeft: `2px solid var(--amber-mid)`, paddingLeft: 8 }}>
      <img src={media.dataUrl} alt="your photo of this problem" style={{ display: "block", maxWidth: "100%", maxHeight: 420 }} />
    </div>
  );
}

/** *▸ as printed* for a problem known by its blocks (a Reader exercise
 *  candidate, the book's solution in *compare methods*): the multi-block form
 *  of the crop RPC. The caller shows it only where nothing is hidden. */
export function BlocksAsPrinted({
  extractionId,
  spanIds,
  label = AS_PRINTED_COPY.asPrinted,
  altText,
}: {
  extractionId: string;
  spanIds: string[];
  label?: string;
  altText: string;
}) {
  const [open, setOpen] = useState(false);
  const [result, setResult] = useState<{ status: "idle" | "pending" | "ready" | "failed"; crops: PrintedCropsDto | null }>({ status: "idle", crops: null });
  const key = `${extractionId}:${spanIds.join(",")}`;
  const asked = useRef<string | null>(null);
  useEffect(() => {
    if (!open || asked.current === key) return;
    asked.current = key;
    setResult({ status: "pending", crops: null });
    const promise = maybe(() => api.readerProblemCrops({ extractionId, spanIds }));
    if (!promise) {
      setResult({ status: "failed", crops: null });
      return;
    }
    promise.then((crops) => setResult({ status: "ready", crops }), () => setResult({ status: "failed", crops: null }));
  }, [open, key, extractionId, spanIds]);
  if (spanIds.length === 0) return null;
  return (
    <div data-testid="blocks-as-printed" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <button type="button" style={{ ...toggleStyle, fontSize: 10 }} aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        {open ? "▾" : "▸"} {label}
      </button>
      {open ? (
        result.status === "ready" && result.crops ? (
          <PrintedFrame crops={result.crops.crops} alt={altText} status={result.crops.status} />
        ) : result.status === "failed" ? (
          <PrintedFrame crops={[]} alt={altText} status="failed" />
        ) : (
          <div role="status" aria-live="polite" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
            <span aria-hidden="true">◐</span> {AS_PRINTED_COPY.pending}
          </div>
        )
      ) : null}
    </div>
  );
}

/** After feedback (UX §4.6, §4.9): the full locator, *original page ↗* (free,
 *  unlabelled) and *▸ as printed*, for any problem that came from a page or a
 *  photo; the server still hides them while a check on your own is due. */
export function PrintedAfterFeedback({ practiceItemId, altText }: { practiceItemId: string | null | undefined; altText: string }) {
  const view = useAsPrinted(practiceItemId);
  const [page, setPage] = useState<{ extractionId: string; spanId: string; outlineSpanIds: string[] } | null>(null);
  if (!view || !practiceItemId || view.kind === "none") return null;
  const locator = view.kind === "page" && view.locator
    ? [view.locator.exerciseLabel, `${view.locator.sourceTitle ?? "your book"} p.${view.locator.pageLabel}`].filter(Boolean).join(" · ")
    : null;
  return (
    <div data-testid="feedback-as-printed" style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 10, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
      {locator ? (
        <span>
          {locator}
          {view.originalPage ? <>{" · "}<OriginalPageLink view={view} costs={false} onOpen={setPage} /></> : null}
        </span>
      ) : null}
      <AsPrinted key={`${practiceItemId}:${view.kind}`} view={view} practiceItemId={practiceItemId} altText={altText} />
      {page ? (
        <OpenInSource extractionId={page.extractionId} spanId={page.spanId} outlineSpanIds={page.outlineSpanIds}
          context="provenance" entityType="practice_item" entityId={practiceItemId} onClose={() => setPage(null)} />
      ) : null}
    </div>
  );
}
