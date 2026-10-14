// Reader workbench RW3a: the margin cues' controller (spec §6.1-6.2; UX §4.4).
//
// The guide plan carries the cues (already within the learner's density
// budget); this hook decides which are drawn now (cues.ts's restraint rules,
// computed when the text is laid out, never while scrolling), records each
// mark shown once per visit (`cue_shown`), moves focus between marks with
// Alt+↓ / Alt+↑ (the learner's act), and runs the popover's actions: open,
// check me (the shell opens the item as a learner pick, the book out of
// view), not relevant (optional why), fewer marks like this and marks off
// (this book or everywhere), each with an undo until the learner leaves the
// source. Display only: taps are salience-only events and learner_card
// verdicts; nothing here writes evidence.
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
import { CUE_COPY, placeCueMarks, pdfPassageTop, stepDown, stepMark, type CuePlacement } from "./cues";
import type { CueCheckPhase, CueReceipt } from "./MarginMark";

/** What "check me" hands the shell: the item to open, as a learner pick. */
export interface CueCheckMeRequest {
  practiceItemId: string;
  proposalId: string | null;
  spanId: string;
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
  /** The original's page width in pixels (its pane reports it). */
  pdfPageWidth: number | null;
  bodyRef: RefObject<HTMLDivElement | null>;
  /** Changes when the text's layout may have changed (never on scroll). */
  layoutKey: string;
  /** Reading order of the source's passages, and where the learner reads. */
  spanOrder: ReadonlyMap<string, number>;
  readingSpan: string | null;
  visitPayload: () => { visit_id: string | null; extraction_id: string | null };
  jumpToSpan: (spanId: string) => void;
  /** Opens the item "check me" found; absent: no check me (W11). */
  onCheckMe?: (request: CueCheckMeRequest) => void;
  onError: (message: string) => void;
}

export interface ReaderCues {
  /** The plan's cues; null when cues are switched off (no marks, no control). */
  cues: ReaderCuesDto | null;
  placement: CuePlacement;
  /** The drawn mark on a passage, if any. */
  markOn: (spanId: string) => ReaderCueDto | null;
  openCueId: string | null;
  setOpenCueId: (cueId: string | null) => void;
  checkPhase: (cueId: string) => CueCheckPhase;
  canCheckMe: boolean;
  receipt: CueReceipt | null;
  openEarlier: (cue: ReaderCueDto) => void;
  checkMe: (cue: ReaderCueDto) => void;
  notRelevant: (cue: ReaderCueDto, text: string) => void;
  fewer: () => void;
  offBook: () => void;
  offEverywhere: () => void;
  setDensity: (density: CueDensity) => void;
  turnOnBook: () => void;
}

const EMPTY_PLACEMENT: CuePlacement = { shown: [], suppressed: [] };
const FOCUS_RETRIES = 10;

export function useReaderCues(input: ReaderCuesInput): ReaderCues {
  const {
    render, offline, guidePlan, reloadGuidePlan, skimming, restoredSpanId, surface, pdfBlocks, pdfPageWidth,
    bodyRef, layoutKey, spanOrder, readingSpan, visitPayload, jumpToSpan, onCheckMe, onError,
  } = input;
  const cues = render && !offline && guidePlan?.cues && guidePlan.extractionId === render.extractionId ? guidePlan.cues : null;
  const [placement, setPlacement] = useState<CuePlacement>(EMPTY_PLACEMENT);
  const [openCueId, setOpenCueId] = useState<string | null>(null);
  const [checkPhases, setCheckPhases] = useState<Record<string, CueCheckPhase>>({});
  const [receipt, setReceipt] = useState<CueReceipt | null>(null);
  const [resizeTick, setResizeTick] = useState(0);
  const loggedRef = useRef<Set<string>>(new Set());
  const marksKey = (cues?.marks ?? []).map((cue) => `${cue.cueId}:${cue.rank}`).join("|");

  // Per source: the marks shown this visit, the open popover, the receipts.
  const extractionId = render?.extractionId ?? null;
  useEffect(() => {
    loggedRef.current = new Set();
    setOpenCueId(null);
    setCheckPhases({});
    setReceipt(null);
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
      setPlacement((current) => (current.shown.length === 0 && current.suppressed.length === 0 ? current : EMPTY_PLACEMENT));
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
    } else if (surface === "pdf") {
      const width = pdfPageWidth ?? Math.max(320, (body?.clientWidth ?? 0) - 66);
      positionOf = (spanId) => {
        const block = (pdfBlocks ?? []).find((entry) => entry.spanId === spanId && entry.bbox.length === 4);
        return block ? pdfPassageTop(block.page, block.bbox[1], width) : null;
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
    setPlacement((current) => {
      const same = current.shown.length === next.shown.length
        && current.shown.every((cue, index) => cue.cueId === next.shown[index].cueId)
        && current.suppressed.length === next.suppressed.length;
      return same ? current : next;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marksKey, cues?.onePerViewport, skimming, restoredSpanId, surface, pdfPageWidth, pdfBlocks, layoutKey, resizeTick]);

  // Each mark shown counts once per visit (the report's proactive load).
  useEffect(() => {
    if (!cues) return;
    for (const cue of placement.shown) {
      if (loggedRef.current.has(cue.cueId)) continue;
      loggedRef.current.add(cue.cueId);
      logReaderAction("cue_shown", {
        ...visitPayload(), cue_id: cue.cueId, span_id: cue.spanId, cue_kind: cue.kind,
        density: cues.density, element: "margin_mark",
      });
    }
  }, [placement, cues, visitPayload]);

  const shownBySpan = useMemo(() => new Map(placement.shown.map((cue) => [cue.spanId, cue])), [placement]);
  const markOn = useCallback((spanId: string) => shownBySpan.get(spanId) ?? null, [shownBySpan]);

  // Alt+↓ / Alt+↑: the next or previous mark, in reading order (UX §3.5). With
  // no mark focused, the first at or after (or before) the reading position.
  const shownRef = useRef<ReaderCueDto[]>([]);
  shownRef.current = placement.shown;
  const focusMark = useCallback((cue: ReaderCueDto) => {
    const find = () => document.querySelector<HTMLElement>(`[data-cue-mark="${cue.cueId}"]`);
    const present = find();
    if (present) {
      present.focus();
      return;
    }
    // A page not drawn yet: take the page there, then focus once it is.
    jumpToSpan(cue.spanId);
    let tries = 0;
    const retry = () => {
      tries += 1;
      const element = find();
      if (element) element.focus();
      else if (tries < FOCUS_RETRIES) window.setTimeout(retry, 100);
    };
    window.setTimeout(retry, 100);
  }, [jumpToSpan]);
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
    try {
      await api.readerSetCuePreferences({
        extractionId: render.extractionId, sourceId: render.sourceId, via,
        density: change.density ?? null, sourceOff: change.sourceOff ?? null,
      });
      await reloadGuidePlan();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [render, reloadGuidePlan, onError]);

  const openEarlier = useCallback((cue: ReaderCueDto) => {
    void tap(cue, "opened").catch(() => undefined);
  }, [tap]);

  const checkMe = useCallback((cue: ReaderCueDto) => {
    if (!onCheckMe) return;
    setCheckPhases((phases) => ({ ...phases, [cue.cueId]: "finding" }));
    void tap(cue, "check_me")
      .then((result) => {
        const check = result.check;
        if (check?.status === "found" && check.practiceItemId) {
          setCheckPhases((phases) => ({ ...phases, [cue.cueId]: "idle" }));
          setOpenCueId(null);
          onCheckMe({ practiceItemId: check.practiceItemId, proposalId: check.proposalId ?? null, spanId: cue.spanId });
        } else {
          setCheckPhases((phases) => ({ ...phases, [cue.cueId]: check?.status === "none" ? "none" : "failed" }));
        }
      })
      .catch(() => setCheckPhases((phases) => ({ ...phases, [cue.cueId]: "failed" })));
  }, [tap, onCheckMe]);

  const notRelevant = useCallback((cue: ReaderCueDto, text: string) => {
    setOpenCueId(null);
    void tap(cue, "not_relevant", text)
      .then(async () => {
        setReceipt({
          label: CUE_COPY.receiptNotRelevant,
          onUndo: () => {
            setReceipt(null);
            void tap(cue, "not_relevant_undone").then(() => reloadGuidePlan()).catch((error) => onError(errorMessage(error)));
          },
        });
        await reloadGuidePlan();
      })
      .catch((error) => onError(errorMessage(error)));
  }, [tap, reloadGuidePlan, onError]);

  const density = cues?.density ?? "normal";
  const fewer = useCallback(() => {
    const previous = density;
    const next = stepDown(previous);
    setOpenCueId(null);
    setReceipt({
      label: `${CUE_COPY.receiptDensity} ${next}.`,
      onUndo: () => {
        setReceipt(null);
        void setPreferences({ density: previous }, "undo");
      },
    });
    void setPreferences({ density: next }, "fewer");
  }, [density, setPreferences]);

  const offBook = useCallback(() => {
    setOpenCueId(null);
    setReceipt({
      label: CUE_COPY.receiptBookOff,
      onUndo: () => {
        setReceipt(null);
        void setPreferences({ sourceOff: false }, "undo");
      },
    });
    void setPreferences({ sourceOff: true }, "popover");
  }, [setPreferences]);

  const offEverywhere = useCallback(() => {
    const previous = density;
    setOpenCueId(null);
    setReceipt({
      label: CUE_COPY.receiptEverywhereOff,
      onUndo: () => {
        setReceipt(null);
        void setPreferences({ density: previous }, "undo");
      },
    });
    void setPreferences({ density: "off" }, "popover");
  }, [density, setPreferences]);

  const setDensity = useCallback((next: CueDensity) => {
    if (next === density) return;
    setReceipt(null);
    void setPreferences({ density: next }, "footer");
  }, [density, setPreferences]);

  const turnOnBook = useCallback(() => {
    setReceipt(null);
    void setPreferences({ sourceOff: false }, "footer");
  }, [setPreferences]);

  const checkPhase = useCallback((cueId: string) => checkPhases[cueId] ?? "idle", [checkPhases]);

  return {
    cues, placement, markOn, openCueId, setOpenCueId, checkPhase, canCheckMe: Boolean(onCheckMe), receipt,
    openEarlier, checkMe, notRelevant, fewer, offBook, offEverywhere, setDensity, turnOnBook,
  };
}
