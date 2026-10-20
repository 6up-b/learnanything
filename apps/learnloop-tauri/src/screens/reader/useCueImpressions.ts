// Reader workbench RW3b: cue impressions (spec §6.2 item 6, §6.3; G14).
//
// While discovery is on, every cue the Reader could show is a receipt, once
// per visit. The holdout's two arms are measured the same way (Codex review
// F5): a discovered cue counts when its passage is in the learner's view,
// drawn (shown) or held out alike, by one criterion (half the passage, or
// half the reading area for a passage taller than it). A held-out cue counts
// as a control only when the Reader's own rules would have drawn it (placed
// like a mark, cues.ts); one the spacing or the restored line set aside is
// sent with that reason, outside both arms (F4). A density cut, a spaced
// mark or a mark on the restored line is sent with its reason when its
// passage is in view. The original PDF draws no element per passage, so on it
// no discovered cue is recorded in either arm; RW3a's Guide marks keep their
// own "in view" (MarginMark), on every surface. The Reader names only its own
// reasons (spacing, restored_line); the sidecar records the holdout and the
// density cut itself, with the seed, propensity, p_open and density it
// computed. Each queued receipt keeps the source and visit it was seen in, so
// leaving a source sends its receipts to it (F6), and a receipt counts as
// sent only once the sidecar answered. Batched, quiet on failure, never a
// model call.
import { useCallback, useEffect, useRef, type RefObject } from "react";
import { api } from "../../api/client";
import type { ReaderCueDto, ReaderCueImpressionInput, ReaderCuesDto } from "../../api/dto";
import type { CuePlacement } from "./cues";
import { newActivityId } from "./activity";

/** Impressions are sent this long after the last one queued. */
export const IMPRESSION_FLUSH_MS = 800;
/** A batch the sidecar did not take is sent again once, after this long. */
export const IMPRESSION_RETRY_MS = 4_000;
/** At least this share of a passage (or of the reading area) in view counts as seen. */
const SEEN_THRESHOLD = 0.5;
const THRESHOLDS = [0, 0.25, 0.5, 0.75, 1];

export interface CueImpressionsInput {
  extractionId: string | null;
  cues: ReaderCuesDto | null;
  placement: CuePlacement;
  surface: "text" | "pdf" | "watch" | "none";
  bodyRef: RefObject<HTMLDivElement | null>;
  /** The funnel's visit, when RW1a's activity is on. */
  visitId: () => string | null;
}

export interface CueImpressions {
  /** The visit the receipts belong to (the funnel's, else this source's own). */
  visitId: () => string | null;
  /** A drawn mark came into view (MarginMark's rule; a Guide mark's receipt). */
  noteShown: (cue: ReaderCueDto) => void;
  /** "fewer marks like this" on this mark. */
  noteFewer: (cue: ReaderCueDto) => void;
}

interface Queued {
  extractionId: string;
  visitId: string;
  once: string;
  entry: ReaderCueImpressionInput;
  attempts: number;
}

/** In view by one criterion for every arm: half the passage, or half the
 *  reading area when the passage is taller than it. */
export function passageInView(seen: IntersectionObserverEntry): boolean {
  if (!seen.isIntersecting) return false;
  if (seen.intersectionRatio >= SEEN_THRESHOLD) return true;
  const visible = seen.intersectionRect?.height ?? 0;
  const area = seen.rootBounds?.height ?? 0;
  return area > 0 && visible >= SEEN_THRESHOLD * area;
}

const discoveredCue = (cue: ReaderCueDto) => Boolean(cue.linkId);

export function useCueImpressions(input: CueImpressionsInput): CueImpressions {
  const { extractionId, cues, placement, surface, bodyRef, visitId } = input;
  const discovery = cues?.discovery ?? null;
  const localVisitRef = useRef<{ extractionId: string; id: string } | null>(null);
  const sentRef = useRef<Set<string>>(new Set());
  const queueRef = useRef<Queued[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const currentVisit = useCallback((): string | null => {
    if (!extractionId) return null;
    const funnel = visitId();
    if (funnel) return funnel;
    if (localVisitRef.current?.extractionId !== extractionId) {
      localVisitRef.current = { extractionId, id: `cues_${newActivityId()}` };
    }
    return localVisitRef.current.id;
  }, [extractionId, visitId]);

  // Each batch names the source and visit its receipts were seen in (F6).
  const flushRef = useRef<() => void>(() => undefined);
  const flush = useCallback(() => {
    timerRef.current = null;
    const items = queueRef.current;
    queueRef.current = [];
    const batches = new Map<string, Queued[]>();
    for (const item of items) {
      const key = `${item.extractionId}\n${item.visitId}`;
      batches.set(key, [...(batches.get(key) ?? []), item]);
    }
    for (const batch of batches.values()) {
      const { extractionId: extraction, visitId: visit } = batch[0];
      void api.readerCueImpressions({ extractionId: extraction, visitId: visit, entries: batch.map((item) => item.entry) })
        .catch(() => {
          // Not taken: sent again once; then left, and free to be seen again.
          const retry = batch.filter((item) => item.attempts < 1).map((item) => ({ ...item, attempts: item.attempts + 1 }));
          for (const item of batch) if (item.attempts >= 1) sentRef.current.delete(item.once);
          if (retry.length === 0) return;
          queueRef.current.push(...retry);
          if (timerRef.current === null) timerRef.current = setTimeout(() => flushRef.current(), IMPRESSION_RETRY_MS);
        });
    }
  }, []);
  flushRef.current = flush;

  const queue = useCallback((key: string, entry: ReaderCueImpressionInput) => {
    const visit = currentVisit();
    if (!discovery || !visit || !extractionId) return;
    const once = `${extractionId}:${visit}:${key}:${entry.cueId}`;
    if (sentRef.current.has(once)) return;
    sentRef.current.add(once);
    queueRef.current.push({ extractionId, visitId: visit, once, entry, attempts: 0 });
    if (timerRef.current === null) timerRef.current = setTimeout(() => flushRef.current(), IMPRESSION_FLUSH_MS);
  }, [currentVisit, discovery, extractionId]);

  // Leaving the source (or the Reader) sends what is queued, each receipt to its own source.
  useEffect(() => () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      flushRef.current();
    }
  }, [extractionId]);

  // A Guide mark's receipt comes from MarginMark; a discovered cue is measured
  // by its passage below (text, transcript), never on the PDF (F5).
  const noteShown = useCallback((cue: ReaderCueDto) => {
    if (discoveredCue(cue)) return;
    queue("seen", { cueId: cue.cueId, shown: true });
  }, [queue]);
  const noteFewer = useCallback((cue: ReaderCueDto) => queue("fewer", { cueId: cue.cueId, response: "fewer" }), [queue]);

  // Every cue measured by its passage: the drawn discovered marks (shown),
  // the held-out cues the Reader would have drawn (the control arm), and the
  // cues set aside by a rule, with their reason.
  type Pending = { cue: ReaderCueDto; entry: ReaderCueImpressionInput };
  const pending: Pending[] = [];
  if (discovery) {
    for (const cue of placement.shown) if (discoveredCue(cue)) pending.push({ cue, entry: { cueId: cue.cueId, shown: true } });
    for (const cue of placement.heldOutPlaced ?? []) pending.push({ cue, entry: { cueId: cue.cueId, shown: false } });
    for (const { cue, reason } of [...placement.suppressed, ...(placement.heldOutSuppressed ?? [])]) {
      if (reason === "spacing" || reason === "restored_line") pending.push({ cue, entry: { cueId: cue.cueId, shown: false, reason } });
    }
    for (const cue of discovery.suppressed) pending.push({ cue, entry: { cueId: cue.cueId, shown: false } });
  }
  const pendingKey = pending.map(({ cue, entry }) => `${cue.cueId}:${cue.spanId}:${entry.shown ? 1 : 0}:${entry.reason ?? ""}`).join("|");
  const pendingRef = useRef(pending);
  pendingRef.current = pending;
  useEffect(() => {
    if (!discovery || surface === "pdf" || surface === "none" || typeof IntersectionObserver === "undefined") return;
    const body = bodyRef.current;
    const items = pendingRef.current;
    if (!body || items.length === 0) return;
    const attribute = surface === "watch" ? "data-transcript-span" : "data-span-id";
    const bySpan = new Map<Element, Pending[]>();
    for (const item of items) {
      const element = body.querySelector(`[${attribute}="${item.cue.spanId}"]`);
      if (!element) continue;
      bySpan.set(element, [...(bySpan.get(element) ?? []), item]);
    }
    if (bySpan.size === 0) return;
    const observer = new IntersectionObserver((entries) => {
      for (const seen of entries) {
        if (!passageInView(seen)) continue;
        for (const item of bySpan.get(seen.target) ?? []) queue("passage", item.entry);
        observer.unobserve(seen.target);
      }
    }, { threshold: THRESHOLDS });
    for (const element of bySpan.keys()) observer.observe(element);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingKey, surface, discovery ? discovery.targetsKey : null]);

  return { visitId: currentVisit, noteShown, noteFewer };
}
