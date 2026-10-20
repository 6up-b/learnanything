// Reader workbench RW3b: cue impressions (spec §6.2 item 6, §6.3; G14).
//
// While discovery is on, every cue the Reader could show is a receipt, once
// per visit: a drawn mark when it is in the learner's view (MarginMark says
// so, RW3a's rule), and a cue not drawn -- held out by the holdout, cut by the
// density budget, set aside by the one-per-screenful rule or on the passage
// the learner was restored to -- when its passage is in view, so the shown
// and the withheld are counted the same way. The Reader names only its own
// reasons (spacing, restored_line); the sidecar records the holdout and the
// density cut itself, with the seed, propensity, p_open and density it
// computed. A transcript and the text view observe their passages; the
// original PDF draws no element per passage, so only its drawn marks count.
// Batched, quiet on failure, never a model call.
import { useCallback, useEffect, useRef, type RefObject } from "react";
import { api } from "../../api/client";
import type { ReaderCueDto, ReaderCueImpressionInput, ReaderCuesDto } from "../../api/dto";
import type { CuePlacement } from "./cues";
import { newActivityId } from "./activity";

/** Impressions are sent this long after the last one queued. */
export const IMPRESSION_FLUSH_MS = 800;
/** At least this share of a passage in view counts as seen (MarginMark's rule). */
const SEEN_THRESHOLD = 0.5;

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
  /** A drawn mark came into view. */
  noteShown: (cue: ReaderCueDto) => void;
  /** "fewer marks like this" on this mark. */
  noteFewer: (cue: ReaderCueDto) => void;
}

export function useCueImpressions(input: CueImpressionsInput): CueImpressions {
  const { extractionId, cues, placement, surface, bodyRef, visitId } = input;
  const discovery = cues?.discovery ?? null;
  const localVisitRef = useRef<{ extractionId: string; id: string } | null>(null);
  const sentRef = useRef<Set<string>>(new Set());
  const queueRef = useRef<ReaderCueImpressionInput[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const extractionRef = useRef(extractionId);
  extractionRef.current = extractionId;

  const currentVisit = useCallback((): string | null => {
    if (!extractionId) return null;
    const funnel = visitId();
    if (funnel) return funnel;
    if (localVisitRef.current?.extractionId !== extractionId) {
      localVisitRef.current = { extractionId, id: `cues_${newActivityId()}` };
    }
    return localVisitRef.current.id;
  }, [extractionId, visitId]);

  const flush = useCallback(() => {
    timerRef.current = null;
    const entries = queueRef.current;
    queueRef.current = [];
    const extraction = extractionRef.current;
    const visit = currentVisit();
    if (!entries.length || !extraction || !visit) return;
    void api.readerCueImpressions({ extractionId: extraction, visitId: visit, entries }).catch(() => undefined);
  }, [currentVisit]);

  const queue = useCallback((key: string, entry: ReaderCueImpressionInput) => {
    const visit = currentVisit();
    if (!discovery || !visit) return;
    const once = `${visit}:${key}:${entry.cueId}`;
    if (sentRef.current.has(once)) return;
    sentRef.current.add(once);
    queueRef.current.push(entry);
    if (timerRef.current === null) timerRef.current = setTimeout(flush, IMPRESSION_FLUSH_MS);
  }, [currentVisit, discovery, flush]);

  // Leaving the source sends what is queued for it.
  useEffect(() => () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      flush();
    }
  }, [extractionId, flush]);

  const noteShown = useCallback((cue: ReaderCueDto) => queue("seen", { cueId: cue.cueId, shown: true }), [queue]);
  const noteFewer = useCallback((cue: ReaderCueDto) => queue("fewer", { cueId: cue.cueId, response: "fewer" }), [queue]);

  // The cues not drawn: counted when their passage is in the learner's view.
  const notDrawnKey = [
    ...(discovery?.heldOut ?? []).map((cue) => `h:${cue.cueId}:${cue.spanId}`),
    ...(discovery?.suppressed ?? []).map((cue) => `d:${cue.cueId}:${cue.spanId}`),
    ...placement.suppressed.filter((entry) => entry.reason === "spacing" || entry.reason === "restored_line")
      .map((entry) => `${entry.reason}:${entry.cue.cueId}:${entry.cue.spanId}`),
  ].join("|");
  useEffect(() => {
    if (!discovery || surface === "pdf" || surface === "none" || typeof IntersectionObserver === "undefined") return;
    const body = bodyRef.current;
    if (!body) return;
    const pending: Array<{ cue: ReaderCueDto; entry: ReaderCueImpressionInput }> = [
      ...discovery.heldOut.map((cue) => ({ cue, entry: { cueId: cue.cueId, shown: false } })),
      ...discovery.suppressed.map((cue) => ({ cue, entry: { cueId: cue.cueId, shown: false } })),
      ...placement.suppressed.flatMap(({ cue, reason }) => (reason === "spacing" || reason === "restored_line"
        ? [{ cue, entry: { cueId: cue.cueId, shown: false, reason } as ReaderCueImpressionInput }] : [])),
    ];
    if (pending.length === 0) return;
    const attribute = surface === "watch" ? "data-transcript-span" : "data-span-id";
    const bySpan = new Map<Element, Array<{ cue: ReaderCueDto; entry: ReaderCueImpressionInput }>>();
    for (const item of pending) {
      const element = body.querySelector(`[${attribute}="${item.cue.spanId}"]`);
      if (!element) continue;
      bySpan.set(element, [...(bySpan.get(element) ?? []), item]);
    }
    if (bySpan.size === 0) return;
    const observer = new IntersectionObserver((entries) => {
      for (const seen of entries) {
        if (!seen.isIntersecting || seen.intersectionRatio < SEEN_THRESHOLD) continue;
        for (const item of bySpan.get(seen.target) ?? []) queue("passage", item.entry);
        observer.unobserve(seen.target);
      }
    }, { threshold: SEEN_THRESHOLD });
    for (const element of bySpan.keys()) observer.observe(element);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notDrawnKey, surface, discovery ? discovery.targetsKey : null]);

  return { visitId: currentVisit, noteShown, noteFewer };
}
