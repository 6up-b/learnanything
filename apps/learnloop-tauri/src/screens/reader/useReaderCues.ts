// Reader workbench RW3a: the margin cues' controller (spec §6.1-6.2; UX §4.4).
//
// The guide plan carries the cues (already within the learner's density
// budget); this hook decides which are drawn now (cues.ts's restraint rules,
// computed when the text is laid out, never while scrolling), records each
// mark the learner could see once per visit (`cue_shown`), moves focus between
// marks with Alt+↓ / Alt+↑ (the learner's act), and runs the popover's
// actions: open, check me (the shell opens the item as a learner pick, the
// book out of view), not relevant (optional why), fewer marks like this and
// marks off (this book or everywhere), each with an undo until the learner
// leaves the source. Display only: taps are salience-only events and
// learner_card verdicts; nothing here writes evidence.
//
// Codex review (reader-hook-rw3a):
// * F1 moving to a mark is a placement, never reading: every Alt+↓ / Alt+↑
//   goes through the Reader's jump (or, on a transcript, its placement), so
//   the passages a far mark's scroll passes are not read;
// * F2 placement keeps only which marks are drawn; what each says comes from
//   the newest plan, so a diagnosis that lands reaches the popover as it
//   reaches the rail;
// * F3 an answer that arrives after the learner left the source (another
//   book, the Library, the Reader closed) is dropped;
// * F4 each mark set aside keeps its undo until the learner leaves the
//   source; a preference's receipt is the latest one;
// * F5 the original PDF's spacing reads each page's own size (cues.ts);
// * F6 a mark is "shown" when it was in view (MarginMark), not when placed.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type RefObject } from "react";
import { api } from "../../api/client";
import type {
  CueDensity,
  ReaderCueDto,
  ReaderCuesDto,
  ReaderGuidePlanDto,
  ReaderPdfBlockDto,
  ReaderRenderViewDto,
} from "../../api/dto";
import { errorMessage } from "../../errors";
import { logReaderAction } from "./activity";
import {
  CUE_COPY, placeCueMarks, pdfPageTops, pdfPassageTop, stepDown, stepMark,
  type CuePlacement, type CueSuppression, type PdfPageLayout,
} from "./cues";
import type { CueCheckPhase, CueReceipt } from "./MarginMark";

/** What "check me" hands the shell: the item to open, as a learner pick. */
export interface CueCheckMeRequest {
  practiceItemId: string;
  proposalId: string | null;
  spanId: string;
}

/** The source a request was made on (review F3): the shell opens the item
 *  only while that source is the one open. */
export interface CueRequestOrigin {
  sourceId: string;
  extractionId: string;
}

export type CueSurface = "text" | "pdf" | "watch" | "none";

export interface ReaderCuesInput {
  render: ReaderRenderViewDto | null;
  offline: boolean;
  guidePlan: ReaderGuidePlanDto | null;
  /** Re-read the plan after a tap or a preference change. */
  reloadGuidePlan: () => Promise<void>;
  /** Skim mode: no marks. */
  skimming: boolean;
  /** The passage the Reader placed the learner at: no mark there. */
  restoredSpanId: string | null;
  surface: CueSurface;
  pdfBlocks: readonly ReaderPdfBlockDto[] | null;
  /** The original's pages as its pane lays them out (their own sizes); null
   *  until the pane has read them, and then no mark has a place yet. */
  pdfLayout: PdfPageLayout | null;
  bodyRef: RefObject<HTMLDivElement | null>;
  /** Changes when the text's layout may have changed (never on scroll). */
  layoutKey: string;
  /** Reading order of the source's passages, and where the learner reads. */
  spanOrder: ReadonlyMap<string, number>;
  readingSpan: string | null;
  visitPayload: () => { visit_id: string | null; extraction_id: string | null };
  /** The Reader's jump: a placement, never reading (useReadingProgress). */
  jumpToSpan: (spanId: string) => void;
  /** A placement without a jump (a transcript's mark is focused in place). */
  notePlacement: () => void;
  /** Opens the item "check me" found; absent: no check me (W11). */
  onCheckMe?: (request: CueCheckMeRequest, origin: CueRequestOrigin) => void;
  onError: (message: string) => void;
}

export interface ReaderCues {
  /** The plan's cues; null when cues are switched off (no marks, no control). */
  cues: ReaderCuesDto | null;
  /** The marks drawn now, each with the newest plan's content. */
  placement: CuePlacement;
  /** The drawn mark on a passage, if any. */
  markOn: (spanId: string) => ReaderCueDto | null;
  /** A mark came into the learner's view: counted once per visit. */
  noteSeen: (cue: ReaderCueDto) => void;
  openCueId: string | null;
  setOpenCueId: (cueId: string | null) => void;
  checkPhase: (cueId: string) => CueCheckPhase;
  canCheckMe: boolean;
  /** Every undo still open: each mark set aside, then the latest preference. */
  receipts: CueReceipt[];
  openEarlier: (cue: ReaderCueDto) => void;
  checkMe: (cue: ReaderCueDto) => void;
  notRelevant: (cue: ReaderCueDto, text: string) => void;
  fewer: () => void;
  offBook: () => void;
  offEverywhere: () => void;
  setDensity: (density: CueDensity) => void;
  turnOnBook: () => void;
}

/** Which marks are drawn, by id: their content is always the newest plan's. */
interface PlacedIds {
  shown: string[];
  suppressed: Array<{ cueId: string; reason: CueSuppression }>;
}

const NO_PLACEMENT: PlacedIds = { shown: [], suppressed: [] };
const FOCUS_RETRIES = 10;

function samePlacement(a: PlacedIds, b: PlacedIds): boolean {
  return a.shown.length === b.shown.length
    && a.shown.every((cueId, index) => cueId === b.shown[index])
    && a.suppressed.length === b.suppressed.length
    && a.suppressed.every((entry, index) => entry.cueId === b.suppressed[index].cueId && entry.reason === b.suppressed[index].reason);
}

export function useReaderCues(input: ReaderCuesInput): ReaderCues {
  const {
    render, offline, guidePlan, reloadGuidePlan, skimming, restoredSpanId, surface, pdfBlocks, pdfLayout,
    bodyRef, layoutKey, spanOrder, readingSpan, visitPayload, jumpToSpan, notePlacement, onCheckMe, onError,
  } = input;
  const cues = render && !offline && guidePlan?.cues && guidePlan.extractionId === render.extractionId ? guidePlan.cues : null;
  const [placedIds, setPlacedIds] = useState<PlacedIds>(NO_PLACEMENT);
  const [openCueId, setOpenCueId] = useState<string | null>(null);
  const [checkPhases, setCheckPhases] = useState<Record<string, CueCheckPhase>>({});
  // Each mark set aside keeps its undo until the learner leaves the source
  // (review F4); a preference's undo is the latest preference's.
  const [dismissals, setDismissals] = useState<CueReceipt[]>([]);
  const [preferenceReceipt, setPreferenceReceipt] = useState<CueReceipt | null>(null);
  const [resizeTick, setResizeTick] = useState(0);
  const loggedRef = useRef<Set<string>>(new Set());
  const marksKey = (cues?.marks ?? []).map((cue) => `${cue.cueId}:${cue.rank}`).join("|");

  // The visit a request belongs to (review F3): it changes when the learner
  // leaves the source (another book, the Library) and when the Reader closes,
  // before anything else can run, so an answer that arrives after is dropped.
  const extractionId = render?.extractionId ?? null;
  const visitRef = useRef(0);
  useLayoutEffect(() => {
    visitRef.current += 1;
    return () => {
      visitRef.current += 1;
    };
  }, [extractionId]);
  const sameVisit = useCallback((visit: number) => visitRef.current === visit, []);

  // Per source: the marks seen this visit, the open popover, the receipts.
  useEffect(() => {
    loggedRef.current = new Set();
    setOpenCueId(null);
    setCheckPhases({});
    setDismissals([]);
    setPreferenceReceipt(null);
  }, [extractionId]);

  useEffect(() => {
    const onResize = () => setResizeTick((tick) => tick + 1);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Which marks are drawn: computed when the text is laid out (a layout
  // effect, before paint), never while scrolling.
  useLayoutEffect(() => {
    if (!cues || cues.marks.length === 0) {
      setPlacedIds((current) => (current.shown.length === 0 && current.suppressed.length === 0 ? current : NO_PLACEMENT));
      return;
    }
    const body = bodyRef.current;
    let viewportHeight = body?.clientHeight ?? 0;
    let positionOf: (spanId: string) => number | null = () => null;
    if (surface === "text" && body) {
      positionOf = (spanId) => {
        const element = body.querySelector(`[data-span-id="${spanId}"]`);
        return element instanceof HTMLElement ? element.getBoundingClientRect().top : null;
      };
    } else if (surface === "pdf" && pdfLayout) {
      // Each page's own size at the pane's width (review F5): stable from the
      // moment the document is read, whatever has been drawn.
      const tops = pdfPageTops(pdfLayout);
      positionOf = (spanId) => {
        const block = (pdfBlocks ?? []).find((entry) => entry.spanId === spanId && entry.bbox.length === 4);
        return block ? pdfPassageTop(tops, block.page, block.bbox[1]) : null;
      };
    } else if (surface === "watch" && body) {
      const scroller = body.querySelector("[data-transcript-scroller]");
      viewportHeight = scroller instanceof HTMLElement ? scroller.clientHeight : viewportHeight;
      positionOf = (spanId) => {
        const element = body.querySelector(`[data-transcript-span="${spanId}"]`);
        return element instanceof HTMLElement ? element.getBoundingClientRect().top : null;
      };
    }
    const next = placeCueMarks({
      marks: cues.marks,
      muted: skimming,
      working: false,
      restoredSpanId,
      onePerViewport: cues.onePerViewport,
      positionOf,
      viewportHeight,
    });
    const ids: PlacedIds = {
      shown: next.shown.map((cue) => cue.cueId),
      suppressed: next.suppressed.map(({ cue, reason }) => ({ cueId: cue.cueId, reason })),
    };
    setPlacedIds((current) => (samePlacement(current, ids) ? current : ids));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marksKey, cues?.onePerViewport, skimming, restoredSpanId, surface, pdfLayout, pdfBlocks, layoutKey, resizeTick]);

  // What each drawn mark says comes from the newest plan (review F2): a
  // diagnosis that lands, or any other change to a cue's content, shows at
  // once in its popover, without moving any mark.
  const placement = useMemo<CuePlacement>(() => {
    const byId = new Map((cues?.marks ?? []).map((cue) => [cue.cueId, cue]));
    return {
      shown: placedIds.shown.flatMap((cueId) => byId.get(cueId) ?? []),
      suppressed: placedIds.suppressed.flatMap(({ cueId, reason }) => {
        const cue = byId.get(cueId);
        return cue ? [{ cue, reason }] : [];
      }),
    };
  }, [placedIds, cues]);

  // Each mark the learner could see counts once per visit (the report's
  // proactive load): MarginMark says when it came into view (review F6).
  const cuesRef = useRef(cues);
  cuesRef.current = cues;
  const noteSeen = useCallback((cue: ReaderCueDto) => {
    const current = cuesRef.current;
    if (!current || loggedRef.current.has(cue.cueId)) return;
    loggedRef.current.add(cue.cueId);
    logReaderAction("cue_shown", {
      ...visitPayload(), cue_id: cue.cueId, span_id: cue.spanId, cue_kind: cue.kind,
      density: current.density, element: "margin_mark",
    });
  }, [visitPayload]);

  const shownBySpan = useMemo(() => new Map(placement.shown.map((cue) => [cue.spanId, cue])), [placement]);
  const markOn = useCallback((spanId: string) => shownBySpan.get(spanId) ?? null, [shownBySpan]);

  // Alt+↓ / Alt+↑: the next or previous mark, in reading order (UX §3.5). With
  // no mark focused, the first at or after (or before) the reading position.
  // Moving to a mark is a placement, never reading (review F1): the page goes
  // there through the Reader's jump, so the passages between are not read;
  // the mark then takes focus without a second scroll. A transcript's mark is
  // focused in place (the video is not moved), as a placement too.
  const shownRef = useRef<ReaderCueDto[]>([]);
  shownRef.current = placement.shown;
  const focusMark = useCallback((cue: ReaderCueDto) => {
    const find = () => document.querySelector<HTMLElement>(`[data-cue-mark="${cue.cueId}"]`);
    if (surface === "watch") {
      notePlacement();
      find()?.focus();
      return;
    }
    jumpToSpan(cue.spanId);
    const present = find();
    if (present) {
      present.focus({ preventScroll: true });
      return;
    }
    // A page not drawn yet: the jump takes the page there; focus once it is.
    let tries = 0;
    const retry = () => {
      tries += 1;
      const element = find();
      if (element) element.focus({ preventScroll: true });
      else if (tries < FOCUS_RETRIES) window.setTimeout(retry, 100);
    };
    window.setTimeout(retry, 100);
  }, [surface, jumpToSpan, notePlacement]);
  useEffect(() => {
    if (!cues || !render) return;
    const onKey = (event: KeyboardEvent) => {
      if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select"))) return;
      const shown = shownRef.current;
      if (shown.length === 0) return;
      const direction = event.key === "ArrowDown" ? 1 : -1;
      const focused = (document.activeElement as HTMLElement | null)?.dataset?.cueMark ?? null;
      let from = focused ? shown.findIndex((cue) => cue.cueId === focused) : -1;
      if (from < 0) {
        const here = spanOrder.get(readingSpan ?? "") ?? -1;
        const order = shown.map((cue) => spanOrder.get(cue.spanId) ?? 0);
        const at = direction === 1 ? order.findIndex((index) => index >= here) : order.map((index) => index <= here).lastIndexOf(true);
        from = at < 0 ? -1 : at - direction;
      }
      const next = stepMark(shown.length, from, direction);
      if (next === null) return;
      event.preventDefault();
      focusMark(shown[next]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cues, render, spanOrder, readingSpan, focusMark]);

  const tap = useCallback(async (cue: ReaderCueDto, action: "opened" | "check_me" | "not_relevant" | "not_relevant_undone", text?: string) => {
    if (!render) throw new Error("no source");
    return api.readerCueAction({ extractionId: render.extractionId, cueId: cue.cueId, action, text: text || null });
  }, [render]);

  const setPreferences = useCallback(async (change: { density?: CueDensity; sourceOff?: boolean }, via: "footer" | "fewer" | "popover" | "undo") => {
    if (!render) return;
    const visit = visitRef.current;
    try {
      await api.readerSetCuePreferences({
        extractionId: render.extractionId, sourceId: render.sourceId, via,
        density: change.density ?? null, sourceOff: change.sourceOff ?? null,
      });
      if (sameVisit(visit)) await reloadGuidePlan();
    } catch (error) {
      if (sameVisit(visit)) onError(errorMessage(error));
    }
  }, [render, reloadGuidePlan, onError, sameVisit]);

  const openEarlier = useCallback((cue: ReaderCueDto) => {
    void tap(cue, "opened").catch(() => undefined);
  }, [tap]);

  const checkMe = useCallback((cue: ReaderCueDto) => {
    if (!onCheckMe || !render) return;
    const visit = visitRef.current;
    const origin: CueRequestOrigin = { sourceId: render.sourceId, extractionId: render.extractionId };
    setCheckPhases((phases) => ({ ...phases, [cue.cueId]: "finding" }));
    void tap(cue, "check_me")
      .then((result) => {
        // Answered after the learner left this source: dropped (review F3).
        if (!sameVisit(visit)) return;
        const check = result.check;
        if (check?.status === "found" && check.practiceItemId) {
          setCheckPhases((phases) => ({ ...phases, [cue.cueId]: "idle" }));
          setOpenCueId(null);
          onCheckMe({ practiceItemId: check.practiceItemId, proposalId: check.proposalId ?? null, spanId: cue.spanId }, origin);
        } else {
          setCheckPhases((phases) => ({ ...phases, [cue.cueId]: check?.status === "none" ? "none" : "failed" }));
        }
      })
      .catch(() => {
        if (sameVisit(visit)) setCheckPhases((phases) => ({ ...phases, [cue.cueId]: "failed" }));
      });
  }, [tap, onCheckMe, render, sameVisit]);

  const notRelevant = useCallback((cue: ReaderCueDto, text: string) => {
    const visit = visitRef.current;
    setOpenCueId(null);
    void tap(cue, "not_relevant", text)
      .then(async () => {
        if (!sameVisit(visit)) return;
        const receipt: CueReceipt = {
          id: `not_relevant:${cue.cueId}`,
          label: CUE_COPY.receiptNotRelevant,
          detail: cue.learningObjectTitle,
          onUndo: () => {
            setDismissals((current) => current.filter((entry) => entry.id !== receipt.id));
            void tap(cue, "not_relevant_undone")
              .then(() => (sameVisit(visit) ? reloadGuidePlan() : undefined))
              .catch((error) => {
                if (sameVisit(visit)) onError(errorMessage(error));
              });
          },
        };
        setDismissals((current) => [...current.filter((entry) => entry.id !== receipt.id), receipt]);
        await reloadGuidePlan();
      })
      .catch((error) => {
        if (sameVisit(visit)) onError(errorMessage(error));
      });
  }, [tap, reloadGuidePlan, onError, sameVisit]);

  const density = cues?.density ?? "normal";
  const fewer = useCallback(() => {
    const previous = density;
    const next = stepDown(previous);
    setOpenCueId(null);
    setPreferenceReceipt({
      id: "preference",
      label: `${CUE_COPY.receiptDensity} ${next}.`,
      onUndo: () => {
        setPreferenceReceipt(null);
        void setPreferences({ density: previous }, "undo");
      },
    });
    void setPreferences({ density: next }, "fewer");
  }, [density, setPreferences]);

  const offBook = useCallback(() => {
    setOpenCueId(null);
    setPreferenceReceipt({
      id: "preference",
      label: CUE_COPY.receiptBookOff,
      onUndo: () => {
        setPreferenceReceipt(null);
        void setPreferences({ sourceOff: false }, "undo");
      },
    });
    void setPreferences({ sourceOff: true }, "popover");
  }, [setPreferences]);

  const offEverywhere = useCallback(() => {
    const previous = density;
    setOpenCueId(null);
    setPreferenceReceipt({
      id: "preference",
      label: CUE_COPY.receiptEverywhereOff,
      onUndo: () => {
        setPreferenceReceipt(null);
        void setPreferences({ density: previous }, "undo");
      },
    });
    void setPreferences({ density: "off" }, "popover");
  }, [density, setPreferences]);

  // The footer's own controls supersede a preference's undo, never a mark's.
  const setDensity = useCallback((next: CueDensity) => {
    if (next === density) return;
    setPreferenceReceipt(null);
    void setPreferences({ density: next }, "footer");
  }, [density, setPreferences]);

  const turnOnBook = useCallback(() => {
    setPreferenceReceipt(null);
    void setPreferences({ sourceOff: false }, "footer");
  }, [setPreferences]);

  const checkPhase = useCallback((cueId: string) => checkPhases[cueId] ?? "idle", [checkPhases]);
  const receipts = useMemo(
    () => (preferenceReceipt ? [...dismissals, preferenceReceipt] : dismissals),
    [dismissals, preferenceReceipt],
  );

  return {
    cues, placement, markOn, noteSeen, openCueId, setOpenCueId, checkPhase, canCheckMe: Boolean(onCheckMe), receipts,
    openEarlier, checkMe, notRelevant, fewer, offBook, offEverywhere, setDensity, turnOnBook,
  };
}
