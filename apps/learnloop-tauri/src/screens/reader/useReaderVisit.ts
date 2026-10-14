// The Reader's visit and funnel bookkeeping (reader workbench RW1a, moved out
// of ReaderScreen by the RW3a hook extraction; no behaviour change).
//
// One visit per opened source: opened, then closed with its active and idle
// seconds. "Back to reading" after a usable model result, the selection
// record, and the LearnLoop-started elements already counted this visit (the
// report's proactive load). Activity is recorded only while reader_inquiry
// is on (activity.ts holds the switch).
import { useCallback, useEffect, useRef, type MutableRefObject } from "react";
import type { ReaderPdfViewDto, ReaderRenderViewDto } from "../../api/dto";
import {
  flushReaderActivity,
  logReaderAction,
  logReaderActivity,
  newActivityId,
  noteLearnerActivity,
  setReaderActivityEnabled,
} from "./activity";

/** A gap this long without scrolling, selecting or typing counts as idle. */
export const VISIT_IDLE_MS = 120_000;

export interface ReaderVisitInput {
  render: ReaderRenderViewDto | null;
  offline: boolean;
  /** RW1a's switch (reader_inquiry.enabled): the funnel records only while on. */
  inquiry: boolean;
  /** Only labels the visit's surface; a new visit starts per opened source. */
  pdfView: ReaderPdfViewDto | null;
}

export interface ReaderVisit {
  /** The learner did something (scroll, select, type): active time accrues. */
  touchVisit: () => void;
  /** The visit and extraction every funnel event carries. */
  visitPayload: () => { visit_id: string | null; extraction_id: string | null };
  /** First touch of the source after a usable model result ("back to reading"). */
  noteBackToReading: () => void;
  /** A usable model result landed: the next touch of the source is "back to reading". */
  noteUsableResult: (jobId: string, actionKind: string) => void;
  /** A selection was committed (span ids only; never the quoted text). */
  noteSelection: (spanCount: number, surface: string) => void;
  /** Count a LearnLoop-started element once per visit (the report's proactive
   *  load). Returns whether this call counted it. */
  noteProactive: (key: string, element: string) => boolean;
  /** Per-source reset (opening another source, back to the library). */
  resetVisitState: () => void;
  /** The current visit (read-only use; the hook owns it). */
  visitRef: MutableRefObject<{ id: string; extractionId: string; openedAt: number; lastActive: number; active: number; idle: number } | null>;
}

export function useReaderVisit({ render, offline, inquiry, pdfView }: ReaderVisitInput): ReaderVisit {
  // The funnel's visit, the pending "back to reading" after a usable result,
  // and the LearnLoop-started elements already counted this visit.
  const visitRef = useRef<{ id: string; extractionId: string; openedAt: number; lastActive: number; active: number; idle: number } | null>(null);
  const backToReadingRef = useRef<{ jobId: string; actionKind: string; at: number } | null>(null);
  const proactiveSeenRef = useRef<Set<string>>(new Set());

  // The funnel's activity is recorded only while reader_inquiry is on.
  useEffect(() => {
    setReaderActivityEnabled(inquiry && !offline);
  }, [inquiry, offline]);

  // One visit per opened source: opened, then closed with its active and idle
  // seconds (a gap of two minutes or more without scrolling, selecting or
  // typing counts as idle).
  useEffect(() => {
    if (!render || offline || !inquiry) return;
    const now = Date.now();
    const visit = { id: newActivityId(), extractionId: render.extractionId, openedAt: now, lastActive: now, active: 0, idle: 0 };
    visitRef.current = visit;
    logReaderActivity({
      kind: "reader_view_opened",
      payload: { visit_id: visit.id, extraction_id: render.extractionId, source_id: render.sourceId, surface: pdfView ? "pdf" : "text" },
    });
    return () => {
      const at = Date.now();
      const gap = at - visit.lastActive;
      if (gap < VISIT_IDLE_MS) visit.active += gap;
      else visit.idle += gap;
      logReaderActivity({
        kind: "reader_view_closed",
        payload: {
          visit_id: visit.id, extraction_id: visit.extractionId,
          active_seconds: Math.round(visit.active / 1000), idle_seconds: Math.round(visit.idle / 1000),
        },
      });
      flushReaderActivity();
      if (visitRef.current === visit) visitRef.current = null;
    };
    // pdfView only labels the surface; a new visit starts per opened source.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [render?.renderViewId, offline, inquiry]);

  const touchVisit = useCallback(() => {
    const visit = visitRef.current;
    if (!visit) return;
    const now = Date.now();
    const gap = now - visit.lastActive;
    if (gap < VISIT_IDLE_MS) visit.active += gap;
    else visit.idle += gap;
    visit.lastActive = now;
  }, []);
  const visitPayload = useCallback(
    () => ({ visit_id: visitRef.current?.id ?? null, extraction_id: render?.extractionId ?? null }),
    [render],
  );
  const noteBackToReading = useCallback(() => {
    const pending = backToReadingRef.current;
    if (!pending) return;
    backToReadingRef.current = null;
    logReaderAction("back_to_reading", {
      ...visitPayload(), job_id: pending.jobId, action_kind: pending.actionKind,
      seconds_after: Math.round((Date.now() - pending.at) / 1000),
    });
  }, [visitPayload]);
  const noteUsableResult = useCallback((jobId: string, actionKind: string) => {
    backToReadingRef.current = { jobId, actionKind, at: Date.now() };
  }, []);
  const noteSelection = useCallback((spanCount: number, surface: string) => {
    touchVisit();
    noteLearnerActivity("selected");
    logReaderActivity({ kind: "reader_selection", payload: { ...visitPayload(), span_count: spanCount, surface } });
    noteBackToReading();
  }, [touchVisit, visitPayload, noteBackToReading]);
  const noteProactive = useCallback((key: string, element: string) => {
    if (proactiveSeenRef.current.has(key)) return false;
    proactiveSeenRef.current.add(key);
    logReaderAction("proactive_shown", { ...visitPayload(), element });
    return true;
  }, [visitPayload]);
  const resetVisitState = useCallback(() => {
    backToReadingRef.current = null;
    proactiveSeenRef.current = new Set();
  }, []);

  return { touchVisit, visitPayload, noteBackToReading, noteUsableResult, noteSelection, noteProactive, resetVisitState, visitRef };
}
