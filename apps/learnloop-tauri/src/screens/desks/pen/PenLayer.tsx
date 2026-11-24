// Pen and ink on a source window (spec §10.10): the ink layer inside the window's scroller (so ink scrolls with
// the text), the pen's input, the recognizer's marks and their chips, and the handwritten margin note.
//
// What each recognition persists (the spec's table):
// - an underline: a highlight annotation snapped to the words; a bracket: a highlight on every paragraph spanned;
// - a strike: a disposition annotation, "I disagree / doesn't make sense";
// - a margin stroke: an interpretation annotation (the handwritten note) holding the ink, with its transcription;
// - a closed loop: the words inside become the selection, and the companion's context (nothing is stored).
// A recognized mark's strokes are saved with its annotation (ink.save, the client's one write sequence). Ink the
// recognizer cannot place stays plain ink on the page: kept for the reading it was drawn on (owner kind "source"),
// redrawn when the source reopens, erasable with the barrel, and never a guess: it is the learner's marks, never
// read or emitted as learner text unless they make it a note.
//
// A paused window (offscreen, hidden, a preview) draws and saves nothing: input is refused and a stroke under
// way is dropped.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { InkTranscribeJobDto, ReaderRawSelectionNode } from "../../../api/dto";
import type { PenSurface } from "../source/types";
import { useWindowLifecycle, useWindowPaused } from "../lifecycle";
import { usePenHost, type PenHost } from "./host";
import { inkRefusal } from "./inkCache";
import { PenInput, type PointerLike, type Sample } from "./input";
import { RECOGNIZED_AS, RECOGNIZER, boxOf, recognize, type Box, type Point, type StrokeKind } from "./recognizer";
import {
  distanceToPolyline,
  localRects,
  pageOf,
  passageBeside,
  passages,
  passagesSpanned,
  rangeBetween,
  rangeOfQuote,
  toClient,
  toLocal,
  wordsInLoop,
  type LocalRect,
} from "./geometry";
import "./pen.css";

/** The spec's pen stroke width (§4.2), the eraser's reach either side of a stroke. */
export const PEN_WIDTH = 2.2;
export const STRIKE_WORDS = "I disagree / doesn't make sense";
/** A whole block's end, as the Reader anchors one (ReaderScreen's whole-passage capture). */
const WHOLE_BLOCK = 1_000_000;

type MarkKind = Exclude<StrokeKind, "ink">;

interface InkStroke {
  /** Client-minted; the stroke's id in `ink.save`. */
  strokeId: string;
  /** Points in the scroller's own coordinates (CSS pixels): [x, y, t, pressure, tiltX, tiltY]. */
  points: Array<[number, number, number, number, number, number]>;
}

interface Mark {
  id: string;
  kind: MarkKind | "ink";
  strokes: InkStroke[];
  box: Box;
  /** Highlight boxes (underline), paragraph boxes (bracket), strike lines, the selection's boxes. */
  rects: LocalRect[];
  annotationId: string | null;
  inkId: string | null;
  state: "saving" | "saved" | "failed" | "local";
  /** Where the chip sits (the scroller's coordinates), and where it goes instead when the window's edge is in the way. */
  chip: { x: number; y: number; below: number; text: string } | null;
  note?: NoteState;
}

interface NoteState {
  x: number;
  y: number;
  /** The words shown: the learner's, or LearnLoop's reading until they keep or fix it. */
  text: string;
  /** Where the words came from. */
  source: "none" | "reading" | "yours";
  reading: "idle" | "reading" | "read" | "cannot" | "failed";
  readingLabel?: string;
}

function localStroke(host: HTMLElement, samples: Sample[], id: string): InkStroke {
  return {
    strokeId: id,
    points: samples.map((s) => {
      const at = toLocal(host, s.x, s.y);
      return [round(at.x), round(at.y), round(s.t), s.pressure, s.tiltX, s.tiltY];
    }),
  };
}

/** Coordinates kept to a hundredth of a pixel: the layer's own rounding of the floats it computed, not a
 * thinning (every sample is kept). */
function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function pathOf(points: ReadonlyArray<readonly number[]>): string {
  return points.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
}

const STROKE_CLASS: Record<Mark["kind"], string> = {
  underline: "under", bracket: "bracket", lasso: "lasso", strike: "strike", note: "note", ink: "",
};

/** Where each chip sits beside its stroke (the mockup's offsets), in client coordinates. */
function chipAt(kind: MarkKind | "ink", box: Box): Point {
  switch (kind) {
    case "lasso": return { x: box.x1 + 6, y: box.y0 };
    case "bracket": return { x: box.x0, y: box.y0 - 30 };
    case "note": return { x: box.x0, y: box.y0 - 30 };
    case "strike": return { x: box.x0, y: box.y1 + 8 };
    case "underline": return { x: box.x0 + 40, y: box.y1 + 6 };
    case "ink": return { x: box.x0, y: box.y1 + 8 };
  }
}

/** A chip at its place beside a mark's strokes (the scroller's coordinates). */
function chipOf(body: HTMLElement, kind: MarkKind | "ink", box: Box, text: string): NonNullable<Mark["chip"]> {
  const at = chipAt(kind, box);
  const local = toLocal(body, at.x, at.y);
  return { x: local.x, y: local.y, below: toLocal(body, at.x, box.y1 + 8).y, text };
}

function boxFrom(x0: number, y0: number, x1: number, y1: number): Box {
  return { x0, y0, x1, y1, w: x1 - x0, h: y1 - y0 };
}

function grown(box: Box, by: number): Box {
  return boxFrom(box.x0 - by, box.y0 - by, box.x1 + by, box.y1 + by);
}

function overlaps(a: Box, b: Box): boolean {
  return a.x0 <= b.x1 && b.x0 <= a.x1 && a.y0 <= b.y1 && b.y0 <= a.y1;
}

function union(a: Box, b: Box): Box {
  return boxFrom(Math.min(a.x0, b.x0), Math.min(a.y0, b.y0), Math.max(a.x1, b.x1), Math.max(a.y1, b.y1));
}

/** One rendered text line of a passage, read from the page: its computed line height, else the height of its first
 * character's line box as laid out. */
function lineHeightOf(passage: HTMLElement): number {
  const computed = parseFloat(passage.ownerDocument.defaultView?.getComputedStyle(passage).lineHeight ?? "");
  if (Number.isFinite(computed) && computed > 0) return computed;
  const walker = passage.ownerDocument.createTreeWalker(passage, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode() as Text | null; node; node = walker.nextNode() as Text | null) {
    if (!node.data.trim()) continue;
    const range = passage.ownerDocument.createRange();
    range.setStart(node, 0);
    range.setEnd(node, 1);
    const height = range.getClientRects()[0]?.height ?? 0;
    if (height > 0) return height;
  }
  return 0;
}

/** The note box's own width (pen.css: 220 px, an 8 px inset and a 2 px edge). */
const NOTE_BOX_WIDTH = 230;

/** Where a margin note's box goes: under its strokes (the mockup's place), moved left as far as it must be to stay
 * inside the window's text, so a note written near the window's edge is never cut off. */
function notePlace(body: HTMLElement, box: Box): Point {
  const at = toLocal(body, box.x0, box.y1 + 4);
  const room = body.clientWidth + body.scrollLeft - NOTE_BOX_WIDTH;
  return { x: Math.max(body.scrollLeft, Math.min(at.x, room)), y: at.y };
}

interface ListedRow {
  annotation?: { id?: string };
  version?: { annotationType?: string; learnerText?: string };
  anchor?: { status?: string };
  segments?: Array<{ spanId?: string; exactQuote?: string }>;
  placement?: { state?: string; segments?: Array<{ spanId?: string; exactQuote?: string }> };
}

interface ListedAnnotation {
  type: string;
  text: string;
  /** What the annotation marks on the open reading, or null where that can no longer be vouched for. */
  segments: Array<{ spanId: string; quote: string }> | null;
}

/** An annotation's anchor on the open reading: where the sidecar placed it (here, or moved after a re-read), else its
 * own segments; null when its words changed or it lies on no passage of this reading (nothing is painted there). */
function anchorSegments(row: ListedRow): ListedAnnotation["segments"] {
  const placed = row.placement;
  if (placed && placed.state !== "here" && placed.state !== "moved") return null;
  if (!placed && row.anchor?.status === "needs_reanchor") return null;
  const segments = (placed ? placed.segments : row.segments) ?? [];
  const found = segments.flatMap((segment) => (segment.spanId ? [{ spanId: segment.spanId, quote: segment.exactQuote ?? "" }] : []));
  return found.length ? found : null;
}

function fold(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

function moved(strokes: InkStroke[], dx: number, dy: number): InkStroke[] {
  if (!dx && !dy) return strokes;
  return strokes.map((stroke) => ({ ...stroke, points: stroke.points.map(([x, y, ...rest]) => [round(x + dx), round(y + dy), ...rest] as InkStroke["points"][number]) }));
}

/** A recognized mark saved with its annotation, drawn again: its marks from the annotation's anchor, its ink where
 * it was written while that still marks the same words (or passage), else moved beside what the anchor names. The
 * kind is the annotation's (a strike is a disposition), a bracket told from an underline by its ink's shape alone,
 * which no layout changes. */
function restoreMark(body: HTMLElement, surface: PenSurface, annotationId: string, strokes: InkStroke[], annotation: ListedAnnotation): Omit<Mark, "inkId"> | null {
  const client = (list: InkStroke[]) => list.flatMap((stroke) => stroke.points.map((point) => toClient(body, point[0], point[1])));
  const box = boxOf(client(strokes));
  const base = { id: `saved:${annotationId}`, annotationId, state: "saved" as const, chip: null };
  const segments = annotation.segments;
  const element = (spanId: string) => passages(body).find((each) => each.dataset.spanId === spanId) ?? null;
  const place = (kind: Mark["kind"], dx: number, dy: number, rects: LocalRect[]) => {
    const shifted = moved(strokes, dx, dy);
    return { ...base, kind, strokes: shifted, box: dx || dy ? boxOf(client(shifted)) : box, rects };
  };
  if (annotation.type === "interpretation") {
    const anchored = segments ? element(segments[0].spanId) : null;
    if (!anchored || passageBeside(body, box) === anchored) return place("note", 0, 0, []);
    return place("note", 0, anchored.getBoundingClientRect().top - box.y0, []);
  }
  if (annotation.type !== "highlight" && annotation.type !== "disposition") return null;
  const tall = box.y1 - box.y0 >= RECOGNIZER.bracket.minHeight && box.x1 - box.x0 <= RECOGNIZER.bracket.maxWidth;
  if (tall && annotation.type === "highlight") {
    const spanned = (segments ?? []).flatMap((segment) => element(segment.spanId) ?? []);
    const rects = localRects(body, spanned.map((each) => each.getBoundingClientRect()));
    const today = passagesSpanned(body, box);
    const same = spanned.length === today.length && spanned.every((each, index) => today[index] === each);
    return place("bracket", 0, same || !spanned.length ? 0 : spanned[0].getBoundingClientRect().top - box.y0, rects);
  }
  const kind = annotation.type === "disposition" ? "strike" : "underline";
  const ranges = (segments ?? []).flatMap((segment) => rangeOfQuote(body, segment.spanId, segment.quote) ?? []);
  const rects = ranges.flatMap((range) => localRects(body, range.getClientRects()));
  const first = ranges[0]?.getClientRects()[0];
  if (!first) return place(kind, 0, 0, rects);
  // Drawn today, would the ink mark the same words? Then it stays where it was written.
  const middle = (box.y0 + box.y1) / 2;
  const lineY = kind === "strike" ? middle : middle - RECOGNIZER.underlineAbove;
  const today = rangeBetween(body, { x: box.x0 + 2, y: lineY }, { x: box.x1 - 2, y: lineY });
  const todayText = today ? fold(today.toString()) : "";
  if (todayText && (segments ?? []).every((segment) => todayText.includes(fold(segment.quote)))) return place(kind, 0, 0, rects);
  const target = first.top + first.height / 2 + (kind === "strike" ? 0 : RECOGNIZER.underlineAbove);
  return place(kind, first.left - box.x0, target - middle, rects);
}

export function PenLayer({ surface }: { surface: PenSurface | null }) {
  const host = usePenHost();
  if (!host || !surface) return null;
  return <PenLayerOn host={host} surface={surface} />;
}

function PenLayerOn({ host, surface }: { host: PenHost; surface: PenSurface }) {
  const body = surface.body;
  const lifecycle = useWindowLifecycle();
  const paused = useWindowPaused();
  const [marks, setMarks] = useState<Mark[]>([]);
  const [live, setLive] = useState<InkStroke | null>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const hostRef = useRef(host);
  hostRef.current = host;
  const pausedRef = useRef(paused);
  pausedRef.current = paused;
  const marksRef = useRef(marks);
  marksRef.current = marks;
  const input = useMemo(() => new PenInput(() => hostRef.current.simulate), []);

  const update = useCallback((id: string, change: (mark: Mark) => Mark | null) => {
    setMarks((all) => all.flatMap((mark) => {
      if (mark.id !== id) return [mark];
      const next = change(mark);
      return next ? [next] : [];
    }));
  }, []);

  // The layer spans the whole scrolled text; marks sit under the words, ink over them.
  useEffect(() => {
    const previous = body.style.isolation;
    body.style.isolation = "isolate";
    body.dataset.penHost = "";
    const measure = () => setSize({ w: body.scrollWidth, h: body.scrollHeight });
    measure();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure);
    observer?.observe(body);
    return () => {
      observer?.disconnect();
      body.style.isolation = previous;
      delete body.dataset.penHost;
    };
  }, [body]);

  const penTypeRef = useRef<"pen" | "mouse">("pen");
  /** The margin note still being written: its passage, its strokes and their box (client coordinates). */
  const openNote = useRef<{ markId: string; passage: HTMLElement; box: Box; strokes: InkStroke[] } | null>(null);
  /** End the open note: keep it and read it (assigned once readNote exists, below). */
  const endNoteRef = useRef<(learnerText?: string) => void>(() => undefined);
  /** Marks taken back (undo, the barrel) while their annotation was still being made: it is removed once made. */
  const undone = useRef(new Set<string>());
  /** The window closed: a reply arriving later changes nothing and starts nothing. */
  const disposed = useRef(false);
  useEffect(() => {
    disposed.current = false;
    return () => {
      disposed.current = true;
    };
  }, []);

  /** Remove a mark's annotation; a removal that fails puts the mark back, saying so, for another undo. */
  const removeAnnotation = useCallback((mark: Mark, annotationId: string) => {
    void hostRef.current.api.readerDeleteIntentAnnotation({ annotationId, reason: "pen undo" }).catch(() => {
      if (disposed.current) return;
      const text = "couldn't take this mark back · undo to try again";
      setMarks((all) => [...all.filter((each) => each.id !== mark.id), { ...mark, annotationId, state: "failed", chip: mark.chip ? { ...mark.chip, text } : chipOf(body, mark.kind, mark.box, text) }]);
    });
  }, [body]);

  const persist = useCallback(async (mark: Mark, nodes: ReaderRawSelectionNode[], action: "highlight" | "disposition" | "interpretation", learnerText: string) => {
    const h = hostRef.current;
    const inkId = h.mintId("ink");
    try {
      const receipt = await h.api.readerCapture({
        ...surface.identity,
        action,
        clientIdempotencyKey: h.mintId("pen"),
        rawSelection: { extractionId: surface.identity.extractionId, nodes },
        learnerText,
      });
      const annotationId = receipt.annotationId;
      if (!annotationId) throw new Error("no annotation was made");
      if (undone.current.delete(mark.id)) {
        // Taken back while it was being made: the annotation goes, and its ink is never saved.
        removeAnnotation(mark, annotationId);
        return null;
      }
      h.saveInk({
        owner: { annotationId },
        inkId,
        strokes: mark.strokes,
        pointerMeta: { pointerType: penTypeRef.current, devicePixelRatio: window.devicePixelRatio || 1 },
      });
      update(mark.id, (current) => ({ ...current, annotationId, inkId, state: "saved" }));
      return { annotationId, inkId };
    } catch {
      if (undone.current.delete(mark.id)) return null;
      update(mark.id, (current) => ({ ...current, state: "failed", chip: current.chip ? { ...current.chip, text: "Couldn’t save this mark. You can draw it again." } : null }));
      return null;
    }
  }, [surface, update, removeAnnotation]);

  const finish = useCallback((samples: Sample[], pointerType: "pen" | "mouse") => {
    penTypeRef.current = pointerType;
    const points = samples.map((s) => ({ x: s.x, y: s.y }));
    const recognition = recognize(points, pageOf(body));
    if (!recognition) return;
    const h = hostRef.current;
    const stroke = localStroke(body, samples, h.mintId("stroke"));
    const box = recognition.box;
    const id = h.mintId("mark");
    const chipFor = (kind: MarkKind | "ink", text: string) => chipOf(body, kind, box, text);
    const base: Mark = { id, kind: "ink", strokes: [stroke], box, rects: [], annotationId: null, inkId: null, state: "local", chip: null };
    // Ink that became no mark stays on the page as the learner's marks: kept for this reading (owner kind
    // "source"), redrawn when the source reopens, erasable; never read and never learner text.
    // A margin stroke beside the open note's passage, overlapping its strokes grown by one rendered line, is more of
    // that note; anything else ends it first (it is then kept and read, once, as a whole).
    const open = openNote.current;
    const beside = recognition.kind === "note" ? passageBeside(body, box) : null;
    if (open && recognition.kind === "note" && beside === open.passage && overlaps(box, grown(open.box, lineHeightOf(open.passage)))) {
      open.strokes = [...open.strokes, stroke];
      open.box = union(open.box, box);
      const at = notePlace(body, open.box);
      const grownBox = open.box;
      update(open.markId, (mark) => ({ ...mark, strokes: [...mark.strokes, stroke], box: grownBox, note: mark.note ? { ...mark.note, x: at.x, y: at.y } : mark.note }));
      return;
    }
    endNoteRef.current();
    const plainInk = (why: string) => {
      const inkId = h.mintId("ink");
      h.saveInk({ owner: { extractionId: surface.identity.extractionId }, inkId, strokes: [stroke],
        pointerMeta: { pointerType, devicePixelRatio: window.devicePixelRatio || 1 } });
      setMarks((all) => [...all, { ...base, inkId, state: "saved", chip: chipFor("ink", why) }]);
    };
    switch (recognition.kind) {
      case "lasso": {
        const range = wordsInLoop(body, points);
        if (!range) {
          plainInk("Ink on the page. Circle some words to select them.");
          return;
        }
        const selection = body.ownerDocument.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range);
        setMarks((all) => [...all, { ...base, kind: "lasso", rects: localRects(body, range.getClientRects()), chip: chipFor("lasso", RECOGNIZED_AS.lasso) }]);
        return;
      }
      case "underline":
      case "strike": {
        const y = recognition.lineY ?? (box.y0 + box.y1) / 2;
        const range = rangeBetween(body, { x: box.x0 + 2, y }, { x: box.x1 - 2, y });
        if (!range) {
          plainInk("Ink on the page. Draw across the words you want to mark.");
          return;
        }
        const kind = recognition.kind;
        const mark: Mark = { ...base, kind, rects: localRects(body, range.getClientRects()), state: "saving", chip: chipFor(kind, RECOGNIZED_AS[kind]) };
        setMarks((all) => [...all, mark]);
        void persist(mark, surface.nodesFor(range), kind === "strike" ? "disposition" : "highlight", kind === "strike" ? STRIKE_WORDS : "");
        return;
      }
      case "bracket": {
        const spanned = passagesSpanned(body, box);
        if (!spanned.length) {
          plainInk("Ink on the page. Draw the bracket next to a paragraph.");
          return;
        }
        const mark: Mark = { ...base, kind: "bracket", rects: localRects(body, spanned.map((element) => element.getBoundingClientRect())), state: "saving", chip: chipFor("bracket", RECOGNIZED_AS.bracket) };
        setMarks((all) => [...all, mark]);
        // Whole passages, anchored as the Reader anchors a block (every character of it).
        const nodes: ReaderRawSelectionNode[] = spanned.flatMap((element) => (element.dataset.spanId ? [{ spanId: element.dataset.spanId, start: 0, end: WHOLE_BLOCK }] : []));
        void persist(mark, nodes, "highlight", "");
        return;
      }
      case "note": {
        if (!beside?.dataset.spanId) {
          plainInk("Ink on the page. Write in the margin beside a passage.");
          return;
        }
        // The note stays open for more strokes; it is kept (one annotation) and read (one reading) when it ends.
        const at = notePlace(body, box);
        const mark: Mark = {
          ...base, kind: "note", state: "local", chip: chipFor("note", RECOGNIZED_AS.note),
          note: { x: at.x, y: at.y, text: "", source: "none", reading: "idle" },
        };
        openNote.current = { markId: mark.id, passage: beside, box, strokes: [stroke] };
        setMarks((all) => [...all, mark]);
        return;
      }
      case "ink":
        plainInk("Ink on the page. Draw over or beside text to make a mark.");
        return;
    }
  // readNote is stable (declared below with useCallback on stable deps)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [body, persist, surface, update]);

  // The margin note's transcription (spec §10.10): asked once its ink is saved, polled through the central poller.
  const polls = useRef(new Map<string, () => void>());
  /** Each note's reading job on the server, stopped when the note is taken back or the window closes. */
  const jobs = useRef(new Map<string, string>());
  const gone = (markId: string) => disposed.current || undone.current.has(markId) || !marksRef.current.some((mark) => mark.id === markId);
  const readNote = useCallback(async (markId: string, inkId: string) => {
    const h = hostRef.current;
    update(markId, (mark) => (mark.note ? { ...mark, note: { ...mark.note, reading: "reading" } } : mark));
    if ((await h.settled()) !== "saved") {
      // The outbox lives in memory (the durable store is the RD-spike's open choice): unsent ink is kept only while the
      // app stays open, and saying "on this device" would promise more.
      update(markId, (mark) => (mark.note ? { ...mark, note: { ...mark.note, reading: "failed", readingLabel: "Waiting for your handwriting to save. Keep LearnLoop open. You can type your note here." } } : mark));
      return;
    }
    if (gone(markId)) return;
    const apply = (job: InkTranscribeJobDto): boolean => {
      if (!job.done) return false;
      update(markId, (mark) => {
        if (!mark.note) return mark;
        const note = mark.note;
        if (job.status === "done" && job.result) {
          const words = job.result.latexMd;
          const nothing = job.result.confidenceLabel === "nothing_read";
          return { ...mark, note: { ...note, reading: "read", text: note.source === "yours" ? note.text : words, source: note.source === "yours" ? "yours" : nothing ? "none" : "reading",
            readingLabel: nothing ? "nothing read · write your note here" : "transcribed · may be wrong · fix it" } };
        }
        const code = job.error?.code ?? job.status;
        const refusal = inkRefusal(code);
        if (refusal) {
          return { ...mark, note: { ...note, reading: "cannot", readingLabel: `${refusal} · your ink is kept` } };
        }
        return { ...mark, note: { ...note, reading: "failed", readingLabel: "Couldn’t convert the handwriting. You can type your note here." } };
      });
      return true;
    };
    try {
      const first = await h.api.inkTranscribe({ inkId });
      if (gone(markId)) {
        // Taken back, or the window closed, before the start answered: the job it started is stopped, not followed.
        if (first.jobId && !first.done) void h.api.inkTranscribeCancel({ jobId: first.jobId }).catch(() => undefined);
        return;
      }
      if (apply(first) || !first.jobId) return;
      const jobId = first.jobId;
      jobs.current.set(markId, jobId);
      const remove = h.poller.register<InkTranscribeJobDto>({
        key: `ink-transcribe:${jobId}`,
        owner: lifecycle.windowId,
        request: () => h.api.inkTranscribeJob({ jobId }),
        onResult: (job) => {
          const done = apply(job);
          if (done) {
            polls.current.delete(markId);
            jobs.current.delete(markId);
          }
          return { done };
        },
        onError: () => {
          apply({ version: 1, jobId, status: "failed", done: true, result: null, error: { code: "interrupted", message: "the reading stopped", retryable: true, details: null } });
          polls.current.get(markId)?.();
          polls.current.delete(markId);
        },
      });
      polls.current.set(markId, remove);
    } catch (error) {
      const code = error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : "failed";
      apply({ version: 1, jobId: null, status: "failed", done: true, result: null, error: { code, message: code, retryable: false, details: null } });
    }
  // gone reads refs only
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lifecycle.windowId, update]);
  /** Stop a note's reading: its polls, and its job on the server (whose next model request is then refused). */
  const stopReading = useCallback((markId: string) => {
    polls.current.get(markId)?.();
    polls.current.delete(markId);
    const jobId = jobs.current.get(markId);
    jobs.current.delete(markId);
    if (jobId) void hostRef.current.api.inkTranscribeCancel({ jobId }).catch(() => undefined);
  }, []);
  useEffect(() => () => {
    for (const markId of [...polls.current.keys(), ...jobs.current.keys()]) stopReading(markId);
  }, [stopReading]);

  // The open note ends: one annotation holding all its strokes, then one reading of them.
  endNoteRef.current = (learnerText = "") => {
    const open = openNote.current;
    if (!open) return;
    openNote.current = null;
    const mark = marksRef.current.find((each) => each.id === open.markId);
    if (!mark || !open.passage.dataset.spanId) return;
    const kept: Mark = { ...mark, strokes: open.strokes, box: open.box, state: "saving" };
    update(mark.id, (current) => ({ ...current, state: "saving" }));
    const nodes: ReaderRawSelectionNode[] = [{ spanId: open.passage.dataset.spanId, start: 0, end: WHOLE_BLOCK }];
    void persist(kept, nodes, "interpretation", learnerText).then((saved) => {
      if (saved) void readNote(mark.id, saved.inkId);
    });
  };
  // ↵ (outside a text field), leaving pen mode, pausing or closing the window ends the open note.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Enter" || !openNote.current) return;
      const target = event.target as Element | null;
      if (target?.closest?.("input, textarea, select, [contenteditable]")) return;
      endNoteRef.current();
    };
    const doc = body.ownerDocument;
    doc.addEventListener("keydown", onKey);
    return () => doc.removeEventListener("keydown", onKey);
  }, [body]);
  useEffect(() => {
    if (!host.on || paused) endNoteRef.current();
  }, [host.on, paused]);
  useEffect(() => () => endNoteRef.current(), []);

  /** Erase strokes of plain page ink (the barrel, or its chip's undo): an ink.erase in the write sequence. */
  const eraseStrokes = useCallback((mark: Mark, strokeIds: string[]) => {
    hostRef.current.eraseInk({ owner: { extractionId: surface.identity.extractionId }, eraseId: hostRef.current.mintId("erase"), strokeIds });
    update(mark.id, (current) => {
      const strokes = current.strokes.filter((stroke) => !strokeIds.includes(stroke.strokeId));
      return strokes.length ? { ...current, strokes } : null;
    });
  }, [surface.identity.extractionId, update]);

  /** Take strokes out of the note still being written (nothing of it was saved yet); the note goes with its last. */
  const dropFromOpenNote = useCallback((mark: Mark, strokeIds: string[]) => {
    const open = openNote.current;
    if (!open || open.markId !== mark.id) return;
    open.strokes = open.strokes.filter((stroke) => !strokeIds.includes(stroke.strokeId));
    if (!open.strokes.length) {
      openNote.current = null;
      update(mark.id, () => null);
      return;
    }
    open.box = boxOf(open.strokes.flatMap((stroke) => stroke.points.map((point) => toClient(body, point[0], point[1]))));
    const strokes = open.strokes;
    const box = open.box;
    update(mark.id, (current) => ({ ...current, strokes, box }));
  }, [body, update]);

  const undo = useCallback((mark: Mark) => {
    if (mark.kind === "ink") {
      eraseStrokes(mark, mark.strokes.map((stroke) => stroke.strokeId));
      return;
    }
    const open = openNote.current;
    if (open && open.markId === mark.id) {
      // A note still being written: undo takes its last stroke back, the whole note with its only one.
      dropFromOpenNote(mark, [open.strokes[open.strokes.length - 1].strokeId]);
      return;
    }
    stopReading(mark.id);
    if (mark.kind === "lasso") body.ownerDocument.getSelection()?.removeAllRanges();
    if (mark.annotationId) removeAnnotation(mark, mark.annotationId);
    else if (mark.state === "saving") undone.current.add(mark.id);
    update(mark.id, () => null);
  }, [body, update, eraseStrokes, stopReading, removeAnnotation, dropFromOpenNote]);

  const keepNote = useCallback((mark: Mark, text: string) => {
    const words = text.trim();
    update(mark.id, (current) => (current.note ? { ...current, note: { ...current.note, text, source: "yours" } } : current));
    if (openNote.current?.markId === mark.id) {
      // Words typed into a note still being written end it: it is kept with them as the learner's.
      endNoteRef.current(words);
      return;
    }
    if (!mark.annotationId) return;
    void hostRef.current.api.readerEditAnnotation({ annotationId: mark.annotationId, learnerText: words }).catch(() => undefined);
  }, [update]);

  // The ink this source already holds (its margin notes' and marks' strokes, saved with their annotations), drawn
  // again. A recognized mark is drawn from its annotation's anchor, what it means, never found again from the pixels
  // it was drawn at: at another window width those pixels lie over other words. Its ink is drawn where it was written
  // while that still marks the same words, else moved beside them.
  useEffect(() => {
    let live = true;
    const h = hostRef.current;
    const { sourceId, extractionId } = surface.identity;
    void Promise.all([h.api.inkList({ sourceId }), h.api.readerSourceAnnotations({ sourceId, extractionId })]).then(([ink, listed]) => {
      if (!live) return;
      const known = new Map<string, ListedAnnotation>();
      for (const row of listed.annotations as ListedRow[]) {
        const id = row?.annotation?.id;
        if (id) known.set(id, { type: row.version?.annotationType ?? "", text: row.version?.learnerText ?? "", segments: anchorSegments(row) });
      }
      const restored: Mark[] = [];
      for (const owner of ink.owners) {
        if (owner.ownerKind === "source" && owner.ownerId === extractionId && owner.strokes.length) {
          const strokes: InkStroke[] = owner.strokes.map((stroke) => ({ strokeId: stroke.strokeId, points: stroke.points }));
          const box = boxOf(strokes.flatMap((stroke) => stroke.points.map((point) => toClient(body, point[0], point[1]))));
          restored.push({ id: `saved:page:${owner.ownerId}`, kind: "ink", strokes, box, rects: [], annotationId: null, inkId: owner.strokes[0].inkId, state: "saved", chip: null });
          continue;
        }
        if (owner.ownerKind !== "annotation" || !owner.strokes.length) continue;
        const annotation = known.get(owner.ownerId);
        if (!annotation) continue;
        const saved = restoreMark(body, surface, owner.ownerId, owner.strokes.map((stroke) => ({ strokeId: stroke.strokeId, points: stroke.points })), annotation);
        if (!saved) continue;
        const mark: Mark = { ...saved, inkId: owner.strokes[0].inkId };
        if (mark.kind === "note") {
          const at = notePlace(body, mark.box);
          const reading = owner.transcription;
          mark.note = { x: at.x, y: at.y, text: annotation.text || (reading?.current ? reading.latexMd : ""), source: annotation.text ? "yours" : reading?.current ? "reading" : "none", reading: reading?.current ? "read" : "idle", readingLabel: annotation.text ? "handwritten" : reading?.current ? "transcribed · may be wrong · fix it" : "handwritten" };
        }
        restored.push(mark);
      }
      setMarks((all) => [...restored, ...all.filter((mark) => !mark.id.startsWith("saved:"))]);
    }, () => undefined);
    return () => {
      live = false;
    };
  }, [body, surface]);

  // The pen's input on this window's text.
  useEffect(() => {
    const asPointer = (event: PointerEvent): PointerLike => event as unknown as PointerLike;
    const erased = new Set<string>();
    const onDown = (event: PointerEvent) => {
      if (pausedRef.current) return;
      erased.clear();
      const target = event.target as Element | null;
      if (target?.closest("button, input, textarea, select, [contenteditable], .desk-pen-note, .desk-pen-chip")) return;
      const outcome = input.down(asPointer(event), hostRef.current.on);
      if (outcome.kind === "pass") return;
      if (outcome.turnOn) hostRef.current.setOn(true);
      event.preventDefault();
      try {
        body.setPointerCapture?.(event.pointerId);
      } catch {
        // A pointer the platform no longer tracks: the stroke still ends on its pointerup.
      }
      if (outcome.kind === "draw") setLive(localStroke(body, [{ x: event.clientX, y: event.clientY, t: 0, pressure: 0.5, tiltX: 0, tiltY: 0 }], "live"));
    };
    const onMove = (event: PointerEvent) => {
      if (pausedRef.current) {
        input.cancel();
        setLive(null);
        return;
      }
      const samples = input.move(asPointer(event));
      if (!samples.length) return;
      if (input.erasing) {
        erase(samples);
        return;
      }
      setLive((current) => current ? { ...current, points: [...current.points, ...localStroke(body, samples, "live").points] } : current);
    };
    const onUp = (event: PointerEvent) => {
      const stroke = input.up(asPointer(event));
      setLive(null);
      if (!stroke || pausedRef.current) return;
      finish(stroke.samples, stroke.pointerType);
    };
    const onCancel = () => {
      input.cancel();
      setLive(null);
    };
    const erase = (samples: Sample[]) => {
      for (const sample of samples) {
        const at = toLocal(body, sample.x, sample.y);
        for (const mark of marksRef.current) {
          // Each stroke and mark is erased once a gesture, though the eraser passes over it again before re-rendering.
          const hit = mark.strokes.filter((stroke) => !erased.has(stroke.strokeId)
            && distanceToPolyline(at, stroke.points.map((p) => ({ x: p[0], y: p[1] }))) <= PEN_WIDTH);
          if (!hit.length || erased.has(mark.id)) continue;
          // Plain page ink loses the strokes passed over; a recognized mark's ink belongs to its annotation, and
          // erasing it takes the mark back, as its undo does.
          if (mark.kind === "ink") {
            for (const stroke of hit) erased.add(stroke.strokeId);
            eraseStrokes(mark, hit.map((stroke) => stroke.strokeId));
          } else if (openNote.current?.markId === mark.id) {
            // A note still being written loses the strokes passed over (all of them: the note goes).
            for (const stroke of hit) erased.add(stroke.strokeId);
            dropFromOpenNote(mark, hit.map((stroke) => stroke.strokeId));
          } else {
            erased.add(mark.id);
            undo(mark);
          }
        }
      }
    };
    body.addEventListener("pointerdown", onDown, true);
    body.addEventListener("pointermove", onMove, true);
    body.addEventListener("pointerup", onUp, true);
    body.addEventListener("pointercancel", onCancel, true);
    return () => {
      body.removeEventListener("pointerdown", onDown, true);
      body.removeEventListener("pointermove", onMove, true);
      body.removeEventListener("pointerup", onUp, true);
      body.removeEventListener("pointercancel", onCancel, true);
    };
  }, [body, input, finish, undo, eraseStrokes, dropFromOpenNote]);

  // A lasso's words are the selection (the companion reads it) and show as the mark under them, not as the native
  // selection's paint.
  const lassoShown = marks.some((mark) => mark.kind === "lasso");
  useEffect(() => {
    if (lassoShown) body.dataset.penLasso = "";
    else delete body.dataset.penLasso;
  }, [body, lassoShown]);

  // Pausing drops a stroke under way.
  useEffect(() => {
    if (paused) {
      input.cancel();
      setLive(null);
    }
  }, [paused, input]);

  const layer: ReactNode = (
    <>
      <div className="desk-pen-marks" aria-hidden="true" style={{ width: size.w, height: size.h }}>
        {marks.flatMap((mark) => mark.rects.map((rect, index) => (
          <div
            key={`${mark.id}:${index}`}
            className={`desk-pen-mark ${mark.kind}`}
            data-pen-mark={mark.kind}
            style={{ left: rect.x, top: rect.y, width: rect.w, height: rect.h }}
          />
        )))}
      </div>
      <svg className="desk-pen-ink" aria-hidden="true" width={size.w} height={size.h} style={{ height: size.h }}>
        {marks.flatMap((mark) => mark.strokes.map((stroke) => (
          <path key={`${mark.id}:${stroke.strokeId}`} className={`stroke ${STROKE_CLASS[mark.kind]}`} data-pen-stroke={mark.kind} d={pathOf(stroke.points)} />
        )))}
        {live ? <path className="stroke" data-pen-stroke="live" d={pathOf(live.points)} /> : null}
      </svg>
      {marks.map((mark) => (
        <div key={`${mark.id}:over`}>
          {mark.kind === "strike" ? mark.rects.map((rect, index) => (
            <div key={index} className="desk-pen-strike" style={{ left: rect.x, top: rect.y + rect.h * 0.5, width: rect.w }} />
          )) : null}
          {mark.chip ? (
            <Chip body={body} kind={mark.kind} x={mark.chip.x} y={mark.chip.y} below={mark.chip.below}>
              <span>{mark.chip.text}</span>
              {mark.kind === "lasso" ? <button type="button" className="askc" onClick={() => hostRef.current.askCompanion()}>ask in the companion · c</button> : null}
              <button type="button" data-undo="" onClick={() => undo(mark)}>undo</button>
              <button type="button" data-x="" aria-label="Hide pen message" title="Hide pen message" onClick={() => update(mark.id, (current) => ({ ...current, chip: null }))}>✕</button>
            </Chip>
          ) : null}
          {mark.note ? <NoteBox mark={mark} onKeep={keepNote} /> : null}
        </div>
      ))}
    </>
  );
  return createPortal(<div className="desk-pen-layer" data-pen-layer="" data-pen-on={host.on ? "on" : "off"}>{layer}</div>, body);
}

/** A recognition's chip at the mockup's place beside its stroke, moved left as far as it must be to stay inside the
 * window's text (its width is its words', so it is measured once drawn). */
function Chip({ body, kind, x, y, below, children }: { body: HTMLElement; kind: Mark["kind"]; x: number; y: number; below: number; children: ReactNode }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [place, setPlace] = useState({ left: x, top: y });
  useLayoutEffect(() => {
    const width = ref.current?.offsetWidth ?? 0;
    const left = Math.max(body.scrollLeft, Math.min(x, body.clientWidth + body.scrollLeft - width));
    // Moved in from the edge, it would lie over the words it marks: it goes under the stroke instead.
    const top = left < x ? Math.max(y, below) : y;
    setPlace((now) => (now.left === left && now.top === top ? now : { left, top }));
  }, [body, x, y, below, children]);
  return <div ref={ref} className="desk-pen-chip" data-pen-chip={kind} style={place}>{children}</div>;
}

function NoteBox({ mark, onKeep }: { mark: Mark; onKeep: (mark: Mark, text: string) => void }) {
  const note = mark.note!;
  const [text, setText] = useState(note.text);
  // Typed into since it last showed the note's words: a reading arriving then is offered beside the draft, never
  // written over it.
  const [dirty, setDirty] = useState(false);
  const dirtyRef = useRef(dirty);
  dirtyRef.current = dirty;
  useEffect(() => {
    if (!dirtyRef.current) setText(note.text);
  }, [note.text]);
  const offered = dirty && note.source === "reading" && note.text && note.text !== text ? note.text : null;
  const keep = (words: string) => {
    setDirty(false);
    onKeep(mark, words);
  };
  const label = note.readingLabel ?? (note.reading === "reading" ? "reading your handwriting…" : mark.state === "saving" ? "keeping your note…" : "handwritten");
  return (
    <div className="desk-pen-note" data-pen-note={note.reading} style={{ left: note.x, top: note.y }}>
      <span className="who">› your note · handwritten</span>
      <textarea
        className="ocr"
        aria-label="your note's words"
        rows={2}
        value={text}
        placeholder={note.reading === "cannot" ? "type it here" : ""}
        data-desk-typing=""
        onChange={(event) => {
          setText(event.target.value);
          setDirty(true);
        }}
        onBlur={() => {
          // Only the learner's own change is kept on leaving; LearnLoop's reading becomes the note's words only
          // when they keep it (↵), so a model's reading is never stored as the learner's.
          if (dirty && text !== note.text) keep(text);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            keep(text);
            (event.target as HTMLTextAreaElement).blur();
          }
        }}
      />
      {offered ? (
        <span className="ocrl" data-pen-note-offer="">LearnLoop reads: {offered} (may be wrong) · <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => {
          setText(offered);
          keep(offered);
        }}>use it</button></span>
      ) : null}
      <span className="ocrl">{label}</span>
    </div>
  );
}

