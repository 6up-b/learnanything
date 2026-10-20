// Reader workbench RW3b: cue impressions (spec §6.2 item 6, §6.3; G14).
//
// While discovery is on, every cue the Reader could show is a receipt, once
// per visit. The holdout's two arms are measured the same way (Codex review
// F5): a discovered cue counts when its passage is in the learner's view,
// drawn (shown) or held out alike, by one criterion (half the passage, or
// half the reading area for a passage taller than it, that point being an
// observer threshold of its own, F14 of the re-review, worked out again when
// a passage or the reading area changes size, F14 of the verify). A held-out
// cue counts as a control only when the Reader's own rules would have drawn it
// (placed like a mark, cues.ts); one the spacing or the restored line set aside is
// sent with that reason, outside both arms (F4). A density cut, a spaced
// mark or a mark on the restored line is sent with its reason when its
// passage is in view. The original PDF draws no element per passage, so on it
// no discovered cue is recorded in either arm; RW3a's Guide marks keep their
// own "in view" (MarginMark), on every surface. The Reader names only its own
// reasons (spacing, restored_line); the sidecar records the holdout and the
// density cut itself, with the seed, propensity, p_open and density it
// computed. Each queued receipt keeps the source, visit and cue plan it was
// seen in, so leaving a source sends its receipts to it (F6), the sidecar
// resolves each against the plan it was seen on, not the plan as it is by
// the flush (F17 of the verify), and a receipt counts as sent only once the
// sidecar answered. Batched, quiet on failure, never a
// model call.
import { useCallback, useEffect, useRef, type RefObject } from "react";
import { api } from "../../api/client";
import type { ReaderCueDto, ReaderCueImpressionInput, ReaderCuesDto } from "../../api/dto";
import type { CuePlacement } from "./cues";
import { newActivityId } from "./activity";
import { observerGeneration } from "./observerGeneration";

/** Impressions are sent this long after the last one queued. */
export const IMPRESSION_FLUSH_MS = 800;
/** A batch the sidecar did not take is sent again once, after this long. */
export const IMPRESSION_RETRY_MS = 4_000;
/** At least this share of a passage (or of the reading area) in view counts as seen. */
const SEEN_THRESHOLD = 0.5;
const THRESHOLDS = [0, 0.25, 0.5, 0.75, 1];
/** Size changes are let settle this long before the thresholds are worked out again. */
export const CUE_REFLOW_SETTLE_MS = 150;
/** A pixel of rounding between the observer's ratio and the visible height. */
const SEEN_SLACK_PX = 1;

/** The observer thresholds for a passage this tall in a reading area this
 *  tall. A passage taller than the area never reaches half its own height in
 *  view, so the ratio at which half the area is covered by it is a threshold
 *  of its own; without it the observer would not call back when the passage
 *  comes to fill half the area (Codex re-review F14). That ratio is used
 *  exactly as computed (an observer takes any number in [0, 1]), only kept
 *  within (0, 1]: rounded, it could fall more than the pixel of slack below
 *  the crossing, and nothing after it would call back (Codex verify F14: a
 *  24,100 px passage rounded to 0.0124 fired at 298.9 px, then never again). */
export function passageThresholds(passageHeight: number, areaHeight: number): number[] {
  if (!(passageHeight > areaHeight) || !(areaHeight > 0)) return THRESHOLDS;
  const needed = Math.min(1, (SEEN_THRESHOLD * areaHeight) / passageHeight);
  if (!(needed > 0)) return THRESHOLDS;
  return [...new Set([...THRESHOLDS, needed])].sort((a, b) => a - b);
}

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
  /** The plan this cue was first seen on in this visit (its first receipt's),
   *  else the plan served now: a tap names it, so an impression the tap must
   *  create carries that plan's metadata (F17, round 5). */
  planFor: (cue: ReaderCueDto) => string | null;
  /** A drawn mark came into view (MarginMark's rule; a Guide mark's receipt),
   *  under `planId`, the plan its observer generation was built for (F22);
   *  absent: the plan served now. */
  noteShown: (cue: ReaderCueDto, planId?: string | null) => void;
  /** "fewer marks like this" on this mark. */
  noteFewer: (cue: ReaderCueDto) => void;
}

interface Queued {
  extractionId: string;
  visitId: string;
  /** The cue plan the receipt was seen on: the sidecar resolves it against that plan (F17). */
  planId: string;
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
  return area > 0 && visible + SEEN_SLACK_PX >= SEEN_THRESHOLD * area;
}

const discoveredCue = (cue: ReaderCueDto) => Boolean(cue.linkId);

export function useCueImpressions(input: CueImpressionsInput): CueImpressions {
  const { extractionId, cues, placement, surface, bodyRef, visitId } = input;
  const discovery = cues?.discovery ?? null;
  const localVisitRef = useRef<{ extractionId: string; id: string } | null>(null);
  const sentRef = useRef<Set<string>>(new Set());
  // The plan each cue's first receipt of a visit was queued on (F17, round 5).
  const firstPlanRef = useRef<Map<string, string>>(new Map());
  const queueRef = useRef<Queued[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // The cue visit (the funnel's or a fallback) ends on every source transition,
  // leaving for the Library (null) included, whether or not anything called
  // for it meanwhile (Codex verify F27): coming back to a source is a new
  // visit, with its own first-seen plans and dedupe (both keyed by the visit
  // id). Receipts already queued keep the visit and plan they were seen in.
  const visitSourceRef = useRef<string | null>(extractionId);
  if (visitSourceRef.current !== extractionId) {
    visitSourceRef.current = extractionId;
    localVisitRef.current = null;
  }

  // One cue visit per source-open lifetime (Codex verify F28): at its first
  // use it takes the funnel's visit if there is one, else a fallback of its
  // own, and keeps that id until the source changes or the Reader unmounts,
  // whether a funnel visit appears or goes away meanwhile. So a cue's
  // impression, its response and its first-seen plan stay in one visit.
  const currentVisit = useCallback((): string | null => {
    if (!extractionId) return null;
    if (localVisitRef.current?.extractionId !== extractionId) {
      localVisitRef.current = { extractionId, id: visitId() || `cues_${newActivityId()}` };
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
      const key = `${item.extractionId}\n${item.visitId}\n${item.planId}`;
      batches.set(key, [...(batches.get(key) ?? []), item]);
    }
    for (const batch of batches.values()) {
      const { extractionId: extraction, visitId: visit, planId } = batch[0];
      void api.readerCueImpressions({ extractionId: extraction, visitId: visit, planId,
        entries: batch.map((item) => item.entry) })
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

  const queue = useCallback((key: string, entry: ReaderCueImpressionInput, seenOn?: string | null) => {
    const visit = currentVisit();
    if (!discovery || !visit || !extractionId) return;
    // Every receipt goes to the plan the cue was first seen on this visit
    // (Codex verify F26): a sighting on its mark before its passage counted,
    // or a receipt whose sends failed, keeps that plan. Only a cue not seen
    // before takes the plan of the sighting (an observer generation's own,
    // else the plan served now), which becomes its first-seen plan.
    const seenKey = `${extractionId}:${visit}:${entry.cueId}`;
    const planId = firstPlanRef.current.get(seenKey) ?? seenOn ?? discovery.planId;
    if (!planId) return;
    const once = `${extractionId}:${visit}:${key}:${entry.cueId}`;
    if (sentRef.current.has(once)) return;
    sentRef.current.add(once);
    if (!firstPlanRef.current.has(seenKey)) firstPlanRef.current.set(seenKey, planId);
    queueRef.current.push({ extractionId, visitId: visit, planId, once, entry, attempts: 0 });
    if (timerRef.current === null) timerRef.current = setTimeout(() => flushRef.current(), IMPRESSION_FLUSH_MS);
  }, [currentVisit, discovery, extractionId]);

  // Leaving the source (or the Reader) sends what is queued, each receipt to its own source.
  useEffect(() => () => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      flushRef.current();
    }
  }, [extractionId]);

  const servedPlanId = discovery?.planId ?? null;
  // The plan each cue was first seen or touched under this visit, whether or
  // not that sighting is an automatic impression (Codex verify F25: a
  // discovered mark on the PDF, or on the text before its passage is in view,
  // is never one, yet its taps must name the plan it was seen on).
  const rememberSeen = useCallback((cue: ReaderCueDto, planId?: string | null) => {
    const visit = currentVisit();
    const plan = planId ?? servedPlanId;
    if (!discovery || !plan || !visit || !extractionId) return;
    const seenKey = `${extractionId}:${visit}:${cue.cueId}`;
    if (!firstPlanRef.current.has(seenKey)) firstPlanRef.current.set(seenKey, plan);
  }, [currentVisit, discovery, extractionId, servedPlanId]);
  const planFor = useCallback((cue: ReaderCueDto): string | null => {
    const visit = currentVisit();
    const first = visit && extractionId ? firstPlanRef.current.get(`${extractionId}:${visit}:${cue.cueId}`) : undefined;
    return first ?? servedPlanId;
  }, [currentVisit, extractionId, servedPlanId]);

  // A Guide mark's receipt comes from MarginMark; a discovered cue is measured
  // by its passage below (text, transcript), never on the PDF (F5). Either
  // way the plan it was seen under is remembered first (F25).
  const noteShown = useCallback((cue: ReaderCueDto, planId?: string | null) => {
    rememberSeen(cue, planId);
    if (discoveredCue(cue)) return;
    queue("seen", { cueId: cue.cueId, shown: true }, planId);
  }, [queue, rememberSeen]);
  // "Fewer marks like this" goes to the plan the cue was first seen on, never
  // simply the plan served now (Codex verify F24).
  const noteFewer = useCallback((cue: ReaderCueDto) => {
    rememberSeen(cue);
    queue("fewer", { cueId: cue.cueId, response: "fewer" }, planFor(cue));
  }, [queue, rememberSeen, planFor]);

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
    const elements = [...bySpan.keys()];
    // Passages already in view this run: never observed again, so a rebuild
    // cannot count them twice (the receipt is once per cue per visit anyway).
    const counted = new Set<Element>();
    // The observer's root is the viewport, so the reading area is its height.
    const thresholdsOf = (element: Element) =>
      passageThresholds(element.getBoundingClientRect().height, window.innerHeight);
    // This generation's queue, bound to the plan it was built for (Codex
    // verify F21): an entry its observers measured is sent with this plan,
    // never with a later one.
    const queueForPlan = queue;
    // A callback an observer delivers after it was disconnected (entries the
    // browser had buffered) is discarded, and the replacement observer
    // measures the passage again under its own plan (observerGeneration).
    const generation = observerGeneration();
    let keyOf = new Map<Element, string>();
    // One observer per set of thresholds: a passage taller than the reading
    // area adds the ratio at which it fills half of it (F14).
    const build = () => {
      generation.disconnectAll();
      keyOf = new Map();
      const byThresholds = new Map<string, { thresholds: number[]; elements: Element[] }>();
      for (const element of elements) {
        if (counted.has(element)) continue;
        const thresholds = thresholdsOf(element);
        const key = thresholds.join(",");
        keyOf.set(element, key);
        const group = byThresholds.get(key) ?? { thresholds, elements: [] };
        group.elements.push(element);
        byThresholds.set(key, group);
      }
      for (const { thresholds, elements: group } of byThresholds.values()) {
        generation.observe(group, thresholds, (entries, observer) => {
          for (const seen of entries) {
            if (counted.has(seen.target) || !passageInView(seen)) continue;
            counted.add(seen.target);
            for (const item of bySpan.get(seen.target) ?? []) queueForPlan("passage", item.entry);
            observer.unobserve(seen.target);
          }
        });
      }
    };
    build();
    // A passage's thresholds depend on its height and the area's, and either
    // can change without the other: narrowing the window reflows a passage
    // from 2,000 to 6,000 px at the same area height, and its old thresholds
    // then lie above any ratio it can reach (Codex verify F14). So passages
    // and the reading container are watched for size changes (and the window
    // for the area's), and once they settle the observers are rebuilt if any
    // uncounted passage's threshold set changed.
    let settle: ReturnType<typeof setTimeout> | null = null;
    const recheck = () => {
      settle = null;
      for (const [element, key] of keyOf) {
        if (!counted.has(element) && thresholdsOf(element).join(",") !== key) {
          build();
          return;
        }
      }
    };
    const scheduleRecheck = () => {
      if (settle !== null) clearTimeout(settle);
      settle = setTimeout(recheck, CUE_REFLOW_SETTLE_MS);
    };
    const resizes = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(scheduleRecheck);
    if (resizes) {
      resizes.observe(body);
      for (const element of elements) resizes.observe(element);
    }
    window.addEventListener("resize", scheduleRecheck);
    return () => {
      if (settle !== null) clearTimeout(settle);
      window.removeEventListener("resize", scheduleRecheck);
      resizes?.disconnect();
      generation.disconnectAll();
    };
    // A new plan (its planId) starts a new generation of observers bound to
    // that plan's queue even when the placement and the targets are unchanged
    // (a density or holdout-rate change that moves no mark): a passage first
    // seen under it is sent with its id (Codex verify F20), and the old
    // generation's late callbacks are discarded (F21). Receipts already
    // queued keep the plan they were seen on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingKey, surface, discovery ? discovery.targetsKey : null, servedPlanId]);

  return { visitId: currentVisit, planFor, noteShown, noteFewer };
}
