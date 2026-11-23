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
import type { PenSurface } from "../../ReaderScreen";
import { useWindowLifecycle, useWindowPaused } from "../lifecycle";
import { usePenHost, type PenHost } from "./host";
import { PenInput, type PointerLike, type Sample } from "./input";
import { RECOGNIZED_AS, boxOf, recognize, type Box, type Point, type StrokeKind } from "./recognizer";
import {
  distanceToPolyline,
  localRects,
  pageOf,
  passageBeside,
  passagesSpanned,
  rangeBetween,
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

/** The note box's own width (pen.css: 220 px, an 8 px inset and a 2 px edge). */
const NOTE_BOX_WIDTH = 230;

/** Where a margin note's box goes: under its strokes (the mockup's place), moved left as far as it must be to stay
 * inside the window's text, so a note written near the window's edge is never cut off. */
function notePlace(body: HTMLElement, box: Box): Point {
  const at = toLocal(body, box.x0, box.y1 + 4);
  const room = body.clientWidth + body.scrollLeft - NOTE_BOX_WIDTH;
  return { x: Math.max(body.scrollLeft, Math.min(at.x, room)), y: at.y };
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
      h.saveInk({
        owner: { annotationId },
        inkId,
        strokes: mark.strokes,
        pointerMeta: { pointerType: penTypeRef.current, devicePixelRatio: window.devicePixelRatio || 1 },
      });
      update(mark.id, (current) => ({ ...current, annotationId, inkId, state: "saved" }));
      return { annotationId, inkId };
    } catch {
      update(mark.id, (current) => ({ ...current, state: "failed", chip: current.chip ? { ...current.chip, text: "couldn't keep this mark · your ink is still here" } : null }));
      return null;
    }
  }, [surface, update]);

  const finish = useCallback((samples: Sample[], pointerType: "pen" | "mouse") => {
    penTypeRef.current = pointerType;
    const points = samples.map((s) => ({ x: s.x, y: s.y }));
    const recognition = recognize(points, pageOf(body));
    if (!recognition) return;
    const h = hostRef.current;
    const stroke = localStroke(body, samples, h.mintId("stroke"));
    const box = recognition.box;
    const id = h.mintId("mark");
    const chipFor = (kind: MarkKind | "ink", text: string) => {
      const at = chipAt(kind, box);
      const local = toLocal(body, at.x, at.y);
      return { x: local.x, y: local.y, below: toLocal(body, at.x, box.y1 + 8).y, text };
    };
    const base: Mark = { id, kind: "ink", strokes: [stroke], box, rects: [], annotationId: null, inkId: null, state: "local", chip: null };
    // Ink that became no mark stays on the page as the learner's marks: kept for this reading (owner kind
    // "source"), redrawn when the source reopens, erasable; never read and never learner text.
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
          plainInk("ink · nothing inside to select · kept on the page");
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
          plainInk("ink · no words under it · kept on the page");
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
          plainInk("ink · no paragraph beside it · kept on the page");
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
        const beside = passageBeside(body, box);
        if (!beside?.dataset.spanId) {
          plainInk("ink · no passage beside it · kept on the page");
          return;
        }
        const at = notePlace(body, box);
        const mark: Mark = {
          ...base, kind: "note", state: "saving", chip: chipFor("note", RECOGNIZED_AS.note),
          note: { x: at.x, y: at.y, text: "", source: "none", reading: "idle" },
        };
        setMarks((all) => [...all, mark]);
        const nodes: ReaderRawSelectionNode[] = [{ spanId: beside.dataset.spanId, start: 0, end: WHOLE_BLOCK }];
        void persist(mark, nodes, "interpretation", "").then((saved) => {
          if (saved) void readNote(mark.id, saved.inkId);
        });
        return;
      }
      case "ink":
        plainInk("ink · not recognised · kept on the page");
        return;
    }
  // readNote is stable (declared below with useCallback on stable deps)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [body, persist, surface]);

  // The margin note's transcription (spec §10.10): asked once its ink is saved, polled through the central poller.
  const polls = useRef(new Map<string, () => void>());
  const readNote = useCallback(async (markId: string, inkId: string) => {
    const h = hostRef.current;
    update(markId, (mark) => (mark.note ? { ...mark, note: { ...mark.note, reading: "reading" } } : mark));
    if ((await h.settled()) !== "saved") {
      update(markId, (mark) => (mark.note ? { ...mark, note: { ...mark.note, reading: "failed", readingLabel: "your ink is kept on this device until LearnLoop is reachable" } } : mark));
      return;
    }
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
        if (code === "cannot_read_images") {
          return { ...mark, note: { ...note, reading: "cannot", readingLabel: "handwriting can't be read yet · your ink is kept" } };
        }
        return { ...mark, note: { ...note, reading: "failed", readingLabel: `not read (${job.error?.message ?? code}) · your ink is kept` } };
      });
      return true;
    };
    try {
      const first = await h.api.inkTranscribe({ inkId });
      if (apply(first) || !first.jobId) return;
      const jobId = first.jobId;
      const remove = h.poller.register<InkTranscribeJobDto>({
        key: `ink-transcribe:${jobId}`,
        owner: lifecycle.windowId,
        request: () => h.api.inkTranscribeJob({ jobId }),
        onResult: (job) => {
          const done = apply(job);
          if (done) polls.current.delete(markId);
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
  }, [lifecycle.windowId, update]);
  useEffect(() => () => {
    for (const remove of polls.current.values()) remove();
    polls.current.clear();
  }, []);

  /** Erase strokes of plain page ink (the barrel, or its chip's undo): an ink.erase in the write sequence. */
  const eraseStrokes = useCallback((mark: Mark, strokeIds: string[]) => {
    hostRef.current.eraseInk({ owner: { extractionId: surface.identity.extractionId }, eraseId: hostRef.current.mintId("erase"), strokeIds });
    update(mark.id, (current) => {
      const strokes = current.strokes.filter((stroke) => !strokeIds.includes(stroke.strokeId));
      return strokes.length ? { ...current, strokes } : null;
    });
  }, [surface.identity.extractionId, update]);

  const undo = useCallback((mark: Mark) => {
    const h = hostRef.current;
    if (mark.kind === "ink") {
      eraseStrokes(mark, mark.strokes.map((stroke) => stroke.strokeId));
      return;
    }
    polls.current.get(mark.id)?.();
    polls.current.delete(mark.id);
    if (mark.kind === "lasso") body.ownerDocument.getSelection()?.removeAllRanges();
    if (mark.annotationId) void h.api.readerDeleteIntentAnnotation({ annotationId: mark.annotationId, reason: "pen undo" }).catch(() => undefined);
    update(mark.id, () => null);
  }, [body, update, eraseStrokes]);

  const keepNote = useCallback((mark: Mark, text: string) => {
    if (!mark.annotationId) return;
    const words = text.trim();
    update(mark.id, (current) => (current.note ? { ...current, note: { ...current.note, text, source: "yours" } } : current));
    void hostRef.current.api.readerEditAnnotation({ annotationId: mark.annotationId, learnerText: words }).catch(() => undefined);
  }, [update]);

  // The ink this source already holds (its margin notes' and marks' strokes, saved with their annotations), drawn
  // again where it was written, its marks found again by the same geometry on today's layout.
  useEffect(() => {
    let live = true;
    const h = hostRef.current;
    const sourceId = surface.identity.sourceId;
    void Promise.all([h.api.inkList({ sourceId }), h.api.readerSourceAnnotations({ sourceId })]).then(([ink, listed]) => {
      if (!live) return;
      const kinds = new Map<string, { type: string; text: string }>();
      for (const head of listed.annotations as Array<{ annotation?: { id?: string }; version?: { annotationType?: string; learnerText?: string } }>) {
        if (head?.annotation?.id) kinds.set(head.annotation.id, { type: head.version?.annotationType ?? "", text: head.version?.learnerText ?? "" });
      }
      const restored: Mark[] = [];
      for (const owner of ink.owners) {
        if (owner.ownerKind === "source" && owner.ownerId === surface.identity.extractionId && owner.strokes.length) {
          const strokes: InkStroke[] = owner.strokes.map((stroke) => ({ strokeId: stroke.strokeId, points: stroke.points }));
          const box = boxOf(strokes.flatMap((stroke) => stroke.points.map((point) => toClient(body, point[0], point[1]))));
          restored.push({ id: `saved:page:${owner.ownerId}`, kind: "ink", strokes, box, rects: [], annotationId: null, inkId: owner.strokes[0].inkId, state: "saved", chip: null });
          continue;
        }
        if (owner.ownerKind !== "annotation" || !owner.strokes.length) continue;
        const known = kinds.get(owner.ownerId);
        if (!known) continue;
        const strokes: InkStroke[] = owner.strokes.map((stroke) => ({ strokeId: stroke.strokeId, points: stroke.points }));
        const client = strokes.flatMap((stroke) => stroke.points.map((point) => toClient(body, point[0], point[1])));
        const box = boxOf(client);
        const base: Mark = { id: `saved:${owner.ownerId}`, kind: "ink", strokes, box, rects: [], annotationId: owner.ownerId, inkId: owner.strokes[0].inkId, state: "saved", chip: null };
        if (known.type === "interpretation") {
          const at = notePlace(body, box);
          const reading = owner.transcription;
          restored.push({ ...base, kind: "note", note: { x: at.x, y: at.y, text: known.text || (reading?.current ? reading.latexMd : ""), source: known.text ? "yours" : reading?.current ? "reading" : "none", reading: reading?.current ? "read" : "idle", readingLabel: known.text ? "handwritten" : reading?.current ? "transcribed · may be wrong · fix it" : "handwritten" } });
        } else if (known.type === "disposition" || known.type === "highlight") {
          const recognition = recognize(client, pageOf(body));
          if (recognition?.kind === "bracket") {
            restored.push({ ...base, kind: "bracket", rects: localRects(body, passagesSpanned(body, box).map((element) => element.getBoundingClientRect())) });
          } else if (recognition && (recognition.kind === "underline" || recognition.kind === "strike")) {
            const y = recognition.lineY ?? (box.y0 + box.y1) / 2;
            const range = rangeBetween(body, { x: box.x0 + 2, y }, { x: box.x1 - 2, y });
            restored.push({ ...base, kind: known.type === "disposition" ? "strike" : "underline", rects: range ? localRects(body, range.getClientRects()) : [] });
          } else {
            restored.push({ ...base, kind: known.type === "disposition" ? "strike" : "underline" });
          }
        }
      }
      setMarks((all) => [...restored, ...all.filter((mark) => !mark.id.startsWith("saved:"))]);
    }, () => undefined);
    return () => {
      live = false;
    };
  }, [body, surface.identity.sourceId, surface.identity.extractionId]);

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
  }, [body, input, finish, undo, eraseStrokes]);

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
              {mark.kind === "lasso" ? <button type="button" className="askc" onClick={() => hostRef.current.askCompanion()}>ask the tutor · c</button> : null}
              <button type="button" data-undo="" onClick={() => undo(mark)}>undo</button>
              <button type="button" data-x="" aria-label="dismiss" onClick={() => update(mark.id, (current) => ({ ...current, chip: null }))}>✕</button>
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
  useEffect(() => setText(note.text), [note.text]);
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
        onChange={(event) => setText(event.target.value)}
        onBlur={() => {
          // Only the learner's own change is kept on leaving; LearnLoop's reading becomes the note's words only
          // when they keep it (↵), so a model's reading is never stored as the learner's.
          if (text !== note.text) onKeep(mark, text);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onKeep(mark, text);
            (event.target as HTMLTextAreaElement).blur();
          }
        }}
      />
      <span className="ocrl">{label}</span>
    </div>
  );
}

