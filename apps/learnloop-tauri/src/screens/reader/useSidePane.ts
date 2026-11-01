// Reader CA6b: side by side's second pane as a reader of its own
// (ux_reader_compare_ask_v1 §6.4 "Everything else works in both panes"; UX
// §4.1, §4.4; Codex review of CA6, F1).
//
// The pane context for the second pane. The Reader runs every intent through
// one router (ReaderScreen's runIntentIn) with a pane context; this hook holds
// what is the second pane's own:
//
// * its selection and its intent box: selecting in the pane shows the box
//   exactly as in the main pane (useIntentBox, hosted in the pane's body), its
//   typed intentions routed by reader_intent on THIS pane's reading and
//   passages. The box's keys apply in the pane that has the selection: the
//   main pane's box is disarmed when the learner selects here, and this one
//   when they select there. The palette leaves out what the open book alone
//   can run (work through this: the working posture closes side by side;
//   what matters here?: the Guide's reading path is the open book's);
// * its capture target (this book's source, revision and reading), so a
//   preset, a highlight, a note or an exercise import goes to this book;
// * its active reading and its figures, on this reading;
// * its margin cues: this book's Guide plan cues (RW3a, with RW3b's when the
//   plan carries discovery), already within the learner's density budget for
//   this book, placed by the same restraint rules as the Reader alone
//   (cues.ts, computed when the text is laid out, never while scrolling),
//   drawn static in the pane's gutter, out of the text column, and
//   switchable from their popover (fewer, off for this book, off everywhere,
//   each with an undo). The density setting is one setting: a change from
//   either pane re-reads both plans.
//
// Display and learner-initiated actions only: nothing here writes evidence.
// Off (side by side not shown), the hook holds nothing and reads nothing.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type RefObject } from "react";
import { api } from "../../api/client";
import type { CueDensity, ReaderCueDto, ReaderCuesDto, ReaderIntentContractDto, SideBySideSectionDto } from "../../api/dto";
import { errorMessage } from "../../errors";
import { logReaderAction } from "./activity";
import { CUE_COPY, placeCueMarks, stepDown } from "./cues";
import { useFigures, type FiguresContract } from "./figures/useFigures";
import { readGuidePlan } from "./guidePlan";
import type { PaneSelection } from "./SideBySidePane";
import { useActiveReading } from "./useActiveReading";
import { useIntentBox, type IntentCancel, type IntentRunHandle, type IntentRunHow } from "./useIntentBox";
import type { ReaderIntentActionDto } from "../../api/dto";
import type { CueReceipt } from "./MarginMark";

/** What the second pane's palette leaves out: the open book's own views (U13: absent, never disabled). */
export const SIDE_PANE_HIDDEN_KINDS: ReadonlyArray<string> = ["work_through", "reading_path"];

/** A selection's capture target: the book, revision and reading it goes to. */
export interface PaneCaptureTarget {
  sourceId: string;
  revisionId: string;
  extractionId: string;
  renderViewId: string | null;
  /** The selection's first passage (a preset's subject). */
  spanId: string;
  quote: string;
  nodes: Array<{ spanId: string; quote: string }>;
}

export interface SidePaneInput {
  /** Side by side's two panes are shown (a comparison or a narrow window hides the second). */
  shown: boolean;
  /** The section the second pane shows (null while it loads). */
  section: SideBySideSectionDto | null;
  intentContract: ReaderIntentContractDto | null;
  /** Skim mode: the box opens only on `?` or Tab, and no marks are drawn (as in the main pane). */
  muted: boolean;
  /** The second pane's book is the learner's own notes (only the anchor-free actions). */
  notes: boolean;
  hostRef: RefObject<HTMLDivElement | null>;
  onRun: (action: ReaderIntentActionDto, text: string, how: IntentRunHow) => Promise<IntentRunHandle | null> | void;
  onCancelRun: (cancel: IntentCancel) => void;
  /** The main pane's box: disarmed when the learner selects here. */
  onSelectedHere: () => void;
  activeReadingOn: boolean;
  figuresContract: FiguresContract | null;
  /** The Reader's cue density now (the main plan's): a change re-reads this book's plan. */
  densityKey: string | null;
  /** Re-read the main pane's plan after a preference changed here (density is one setting). */
  reloadMainPlan: () => Promise<void> | void;
  visitPayload: () => { visit_id: string | null; extraction_id: string | null };
  onError: (message: string) => void;
}

const noop = () => undefined;

export function useSidePane(input: SidePaneInput) {
  const { shown, section, intentContract, muted, notes, hostRef, onRun, onCancelRun, onSelectedHere,
    activeReadingOn, figuresContract, densityKey, reloadMainPlan, visitPayload, onError } = input;
  const extractionId = shown && section ? section.extractionId : null;
  const sourceId = shown && section ? section.sourceId : null;
  const sectionKey = extractionId && section ? `${extractionId}::${section.sectionId}` : null;
  const [selection, setSelection] = useState<PaneSelection | null>(null);

  const box = useIntentBox({
    contract: extractionId ? intentContract : null,
    extractionId,
    spanIds: selection?.spanIds ?? [],
    quote: selection?.quote ?? "",
    muted,
    // The pane never shows protected text (reader.side_by_side_section refuses it).
    protectedSelection: false,
    notes,
    canWorkThrough: false,
    hiddenKinds: SIDE_PANE_HIDDEN_KINDS,
    hostRef,
    onRun,
    onCancelRun,
  });
  const { noteSelection: noteBoxSelection, noteSelectionCleared: noteBoxCleared } = box;

  /** The learner's selection in the pane (from its mouse-up), or none. */
  const noteSelection = useCallback((picked: PaneSelection | null) => {
    setSelection(picked);
    if (picked) {
      onSelectedHere();
      noteBoxSelection();
    } else noteBoxCleared();
  }, [onSelectedHere, noteBoxSelection, noteBoxCleared]);
  /** The learner selected in the main pane: this box lets go of its keys. */
  const releaseKeys = useCallback(() => noteBoxCleared(), [noteBoxCleared]);

  // Another section or book, or the pane hidden: nothing carries over.
  useEffect(() => {
    setSelection(null);
  }, [sectionKey]);

  const active = useActiveReading({
    extractionId: activeReadingOn ? extractionId : null, sourceId, onError, onOpenRail: noop,
  });
  const figures = useFigures({ extractionId, contract: figuresContract });

  const target: PaneCaptureTarget | null = section && extractionId && selection && section.revisionId ? {
    sourceId: section.sourceId, revisionId: section.revisionId, extractionId, renderViewId: null,
    spanId: selection.spanIds[0], quote: selection.quote, nodes: selection.nodes,
  } : null;

  // The pane's own fold for "let me try the next step" (the book's next lines
  // in this section, as the main pane folds the next lines of its reading).
  const fold = useCallback((spanIds: string[], foldBlocks: number): string[] => {
    const blocks = section?.blocks ?? [];
    const positions = spanIds.map((spanId) => blocks.findIndex((block) => block.spanId === spanId)).filter((i) => i >= 0);
    if (!positions.length) return [];
    const last = Math.max(...positions);
    return blocks.slice(last + 1, last + 1 + foldBlocks).map((block) => block.spanId);
  }, [section]);

  // A capture made through the box: the pane's own margin marks re-read.
  const [marksVersion, setMarksVersion] = useState(0);
  const marksChanged = useCallback(() => setMarksVersion((value) => value + 1), []);

  const cues = useSidePaneCues({
    extractionId, sourceId, blocks: section?.blocks ?? null, muted, densityKey, hostRef, reloadMainPlan, visitPayload, onError,
  });

  return {
    extractionId, section: extractionId ? section : null, selection, noteSelection, releaseKeys, box, target,
    active, figures, fold, marksVersion, marksChanged, cues,
  };
}

export type SidePane = ReturnType<typeof useSidePane>;

/** Reader CA6b: the second pane's margin cues (RW3a/RW3b), as if it were the Reader alone. */
function useSidePaneCues({
  extractionId, sourceId, blocks, muted, densityKey, hostRef, reloadMainPlan, visitPayload, onError,
}: {
  extractionId: string | null;
  sourceId: string | null;
  blocks: SideBySideSectionDto["blocks"] | null;
  muted: boolean;
  densityKey: string | null;
  hostRef: RefObject<HTMLDivElement | null>;
  reloadMainPlan: () => Promise<void> | void;
  visitPayload: () => { visit_id: string | null; extraction_id: string | null };
  onError: (message: string) => void;
}) {
  const [cues, setCues] = useState<ReaderCuesDto | null>(null);
  const [shown, setShown] = useState<string[]>([]);
  const [openCueId, setOpenCueId] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<CueReceipt | null>(null);
  const [tick, setTick] = useState(0);
  const [resizeTick, setResizeTick] = useState(0);
  const loggedRef = useRef<Set<string>>(new Set());
  const generation = useRef(0);

  // This book's plan (a local read through the Reader's cache), re-read when
  // the density changes anywhere or a preference changed here.
  const readFor = useRef<string | null>(null);
  useEffect(() => {
    generation.current += 1;
    const mine = generation.current;
    // A re-read of the same reading keeps the marks drawn until it lands (no flicker) and skips the cache.
    const again = readFor.current === extractionId && extractionId !== null;
    readFor.current = extractionId;
    if (!again) setCues(null);
    if (!extractionId || !sourceId) return;
    void Promise.resolve()
      .then(() => readGuidePlan(sourceId, extractionId, again ? { force: true } : {}))
      .then((plan) => {
        if (generation.current !== mine) return;
        // Only this reading's own cues (a plan for another reading is not this pane's).
        setCues(plan && plan.extractionId === extractionId && plan.cues ? plan.cues : null);
      })
      .catch(() => undefined);
  }, [extractionId, sourceId, densityKey, tick]);

  // Per book: the marks counted this visit, the open popover, the receipt.
  useEffect(() => {
    loggedRef.current = new Set();
    setOpenCueId(null);
    setReceipt(null);
  }, [extractionId]);

  useEffect(() => {
    const onResize = () => setResizeTick((value) => value + 1);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Which marks are drawn: the Reader's restraint rules, computed when the
  // pane's text is laid out (a layout effect), never while scrolling.
  const marksKey = (cues?.marks ?? []).map((cue) => `${cue.cueId}:${cue.rank}`).join("|");
  const blocksKey = (blocks ?? []).map((block) => block.spanId).join("|");
  useLayoutEffect(() => {
    const body = hostRef.current;
    if (!cues || cues.marks.length === 0 || !body || !blocks) {
      setShown((current) => (current.length === 0 ? current : []));
      return;
    }
    const placed = placeCueMarks({
      marks: cues.marks,
      muted,
      working: false,
      restoredSpanId: null,
      onePerViewport: cues.onePerViewport,
      positionOf: (spanId) => {
        const element = Array.from(body.querySelectorAll<HTMLElement>("[data-sbs-span]")).find((node) => node.dataset.sbsSpan === spanId);
        return element ? element.getBoundingClientRect().top : null;
      },
      viewportHeight: body.clientHeight,
    });
    const ids = placed.shown.map((cue) => cue.cueId);
    setShown((current) => (current.length === ids.length && current.every((id, i) => id === ids[i]) ? current : ids));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marksKey, blocksKey, cues?.onePerViewport, muted, resizeTick]);

  const byId = useMemo(() => new Map((cues?.marks ?? []).map((cue) => [cue.cueId, cue])), [cues]);
  const bySpan = useMemo(() => {
    const map = new Map<string, ReaderCueDto>();
    for (const cueId of shown) {
      const cue = byId.get(cueId);
      if (cue && !map.has(cue.spanId)) map.set(cue.spanId, cue);
    }
    return map;
  }, [shown, byId]);
  const markOn = useCallback((spanId: string) => bySpan.get(spanId) ?? null, [bySpan]);

  const cuesRef = useRef(cues);
  cuesRef.current = cues;
  // Each mark the learner could see counts once per visit, as the main pane's (this book's reading named).
  const noteSeen = useCallback((cue: ReaderCueDto) => {
    const current = cuesRef.current;
    if (!current || !extractionId || loggedRef.current.has(cue.cueId)) return;
    loggedRef.current.add(cue.cueId);
    logReaderAction("cue_shown", {
      ...visitPayload(), target_source_id: sourceId, target_extraction_id: extractionId, cue_id: cue.cueId, span_id: cue.spanId,
      cue_kind: cue.kind, density: current.density, element: "margin_mark", entry: "side_by_side",
    });
  }, [extractionId, sourceId, visitPayload]);

  const tap = useCallback((cue: ReaderCueDto, action: "opened" | "not_relevant" | "not_relevant_undone", text?: string) => {
    if (!extractionId) return Promise.reject(new Error("no reading"));
    const planId = cuesRef.current?.discovery?.planId;
    if (planId) return api.readerCueTap({ extractionId, cueId: cue.cueId, action, text: text || null, planId });
    return api.readerCueAction({ extractionId, cueId: cue.cueId, action, text: text || null });
  }, [extractionId]);

  const reloadBoth = useCallback(async () => {
    setTick((value) => value + 1);
    await reloadMainPlan();
  }, [reloadMainPlan]);

  const setPreferences = useCallback(async (change: { density?: CueDensity; sourceOff?: boolean }, via: "fewer" | "popover" | "undo") => {
    if (!extractionId || !sourceId) return;
    try {
      await api.readerSetCuePreferences({
        extractionId, sourceId, via, density: change.density ?? null, sourceOff: change.sourceOff ?? null,
      });
      await reloadBoth();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [extractionId, sourceId, reloadBoth, onError]);

  const density: CueDensity = cues?.density ?? "normal";
  const openEarlier = useCallback((cue: ReaderCueDto) => {
    void tap(cue, "opened").catch(() => undefined);
  }, [tap]);
  const notRelevant = useCallback((cue: ReaderCueDto, text: string) => {
    setOpenCueId(null);
    void tap(cue, "not_relevant", text)
      .then(() => {
        setReceipt({
          id: `not_relevant:${cue.cueId}`, label: CUE_COPY.receiptNotRelevant, detail: cue.learningObjectTitle,
          onUndo: () => {
            setReceipt(null);
            void tap(cue, "not_relevant_undone").then(() => setTick((value) => value + 1)).catch((error) => onError(errorMessage(error)));
          },
        });
        setTick((value) => value + 1);
      })
      .catch((error) => onError(errorMessage(error)));
  }, [tap, onError]);
  const fewer = useCallback(() => {
    const previous = density;
    const next = stepDown(previous);
    setOpenCueId(null);
    setReceipt({ id: "preference", label: `${CUE_COPY.receiptDensity} ${next}.`, onUndo: () => {
      setReceipt(null);
      void setPreferences({ density: previous }, "undo");
    } });
    void setPreferences({ density: next }, "fewer");
  }, [density, setPreferences]);
  const offBook = useCallback(() => {
    setOpenCueId(null);
    setReceipt({ id: "preference", label: CUE_COPY.receiptBookOff, onUndo: () => {
      setReceipt(null);
      void setPreferences({ sourceOff: false }, "undo");
    } });
    void setPreferences({ sourceOff: true }, "popover");
  }, [setPreferences]);
  const offEverywhere = useCallback(() => {
    const previous = density;
    setOpenCueId(null);
    setReceipt({ id: "preference", label: CUE_COPY.receiptEverywhereOff, onUndo: () => {
      setReceipt(null);
      void setPreferences({ density: previous }, "undo");
    } });
    void setPreferences({ density: "off" }, "popover");
  }, [density, setPreferences]);

  return {
    cues: extractionId ? cues : null, markOn, noteSeen, openCueId, setOpenCueId, receipt,
    openEarlier, notRelevant, fewer, offBook, offEverywhere,
  };
}
