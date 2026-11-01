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
//   when they select there. The palette is the main pane's (Codex re-review
//   F7): *work through this* takes this book to the main pane (the working
//   posture is the open book's) with side by side one step back on the return
//   stack, and *what matters here?* shows this book's reading path in the
//   pane (pathShown, below);
// * its capture target (this book's source, revision and reading), so a
//   preset, a highlight, a note or an exercise import goes to this book;
// * its active reading and its figures, on this reading;
// * its margin cues: the Reader's own cue controller (useReaderCues) on this
//   book's Guide plan, so the pane behaves as the Reader alone on this book
//   (RW3a: the density budget, the restraint rules, the popover's actions
//   and undos, check me, Alt+↓ / Alt+↑ while focus is in the pane; RW3b
//   with discovery on: the background search for this book's missing links,
//   impression receipts, taps with the visit, try this step first), drawn
//   static in the pane's gutter, out of the text column, and placed again
//   when the pane's size changes (Codex review F4-F6, F8, F9). The density
//   setting is one setting: a change from either pane re-reads both plans.
//
// Display and learner-initiated actions only: nothing here writes evidence
// (cue taps and receipts are salience-only, as in the main pane).
// Off (side by side not shown), the hook holds nothing and reads nothing.
import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import type { ReaderGuidePlanDto, ReaderIntentContractDto, SideBySideSectionDto } from "../../api/dto";
import { useFigures, type FiguresContract } from "./figures/useFigures";
import { readGuidePlan } from "./guidePlan";
import type { PaneSelection } from "./SideBySidePane";
import { useActiveReading } from "./useActiveReading";
import { useIntentBox, type IntentCancel, type IntentRunHandle, type IntentRunHow } from "./useIntentBox";
import type { ReaderIntentActionDto } from "../../api/dto";
import { useReaderCues, type CueCheckMeRequest, type CueRequestOrigin } from "./useReaderCues";

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
  /** The book open in the second pane while side by side is open (its
   *  reading), kept while a section loads or the pane is hidden; null once
   *  side by side closes. Cue discovery's open (final verify F11, F12). */
  openBook: string | null;
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
  offline: boolean;
  /** How many of the book's next lines "let me try the next step" folds. */
  foldBlocks: number;
  /** The workbench is on (work through this is offered, as in the main pane). */
  canWorkThrough: boolean;
  /** "check me" on this book's marks: the shell opens the item (absent: no check me). */
  onCheckMe?: (request: CueCheckMeRequest, origin: CueRequestOrigin) => void;
}

const noop = () => undefined;

export function useSidePane(input: SidePaneInput) {
  const { shown, section, openBook, intentContract, muted, notes, hostRef, onRun, onCancelRun, onSelectedHere,
    activeReadingOn, figuresContract, densityKey, reloadMainPlan, visitPayload, onError, offline, foldBlocks, onCheckMe,
    canWorkThrough } = input;
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
    canWorkThrough,
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

  // Codex re-review F7: "what matters here?" in this pane shows THIS book's
  // reading path in the pane (the Guide's card, on this reading), until the
  // learner closes it or the pane's book changes; a second ask brings it
  // into view again.
  const [pathFor, setPathFor] = useState<string | null>(null);
  const [pathFocus, setPathFocus] = useState(0);
  // Kept while the pane moves among this book's sections (its reading is
  // briefly unknown while a section loads); gone when the pane closes or
  // shows another book.
  useEffect(() => {
    if (!shown) setPathFor(null);
    else if (extractionId) setPathFor((current) => (current === extractionId ? current : null));
  }, [shown, extractionId]);
  const showPath = useCallback(() => {
    if (!extractionId) return;
    setPathFor(extractionId);
    setPathFocus((value) => value + 1);
  }, [extractionId]);
  const closePath = useCallback(() => setPathFor(null), []);
  const pathShown = pathFor !== null && pathFor === extractionId;

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
    extractionId, sourceId, openBook, blocks: section?.blocks ?? null, muted, offline, densityKey, hostRef, reloadMainPlan, visitPayload, onError,
    ...(onCheckMe ? { onCheckMe } : {}),
    // RW3b: "try this step first" is RW1b's next-step question at that line, in this pane.
    ...(activeReadingOn ? { onTryFirst: (spanId: string) => void active.start("next_step", [spanId], fold([spanId], foldBlocks)) } : {}),
  });

  return {
    extractionId, section: extractionId ? section : null, selection, noteSelection, releaseKeys, box, target,
    active, figures, fold, marksVersion, marksChanged, cues, pathShown, pathFocus, showPath, closePath,
  };
}

export type SidePane = ReturnType<typeof useSidePane>;

/** Reader CA6b: the second pane's margin cues (RW3a/RW3b), as if it were the
 *  Reader alone: the Reader's own cue controller (useReaderCues) on this
 *  book's plan, surface and passages (Codex review F4-F6, F8, F9). So the
 *  second pane runs RW3b's discovery for this book (its own open id, the
 *  sidecar's per-open call budget, the plan re-read when a job found
 *  something), RW3b's impression receipts (shown, held out and set aside,
 *  under the plan each cue was first seen on, in this book's own cue visit),
 *  taps with that visit, "try this step first" recorded with its tap, "check
 *  me", Alt+↓ / Alt+↑ while focus is in this pane, and placement again
 *  whenever the pane's size changes (the splitter, the window), never on
 *  scroll. */
function useSidePaneCues({
  extractionId, sourceId, openBook, blocks, muted, offline, densityKey, hostRef, reloadMainPlan, visitPayload, onError,
  onCheckMe, onTryFirst,
}: {
  extractionId: string | null;
  sourceId: string | null;
  openBook: string | null;
  blocks: SideBySideSectionDto["blocks"] | null;
  muted: boolean;
  offline: boolean;
  densityKey: string | null;
  hostRef: RefObject<HTMLDivElement | null>;
  reloadMainPlan: () => Promise<void> | void;
  visitPayload: () => { visit_id: string | null; extraction_id: string | null };
  onError: (message: string) => void;
  onCheckMe?: (request: CueCheckMeRequest, origin: CueRequestOrigin) => void;
  onTryFirst?: (spanId: string) => void;
}) {
  const [plan, setPlan] = useState<ReaderGuidePlanDto | null>(null);
  const generation = useRef(0);

  // This book's plan (a local read through the Reader's cache), re-read when
  // the density changes anywhere; a re-read of the same reading keeps the
  // marks drawn until it lands (no flicker) and skips the cache.
  const readFor = useRef<string | null>(null);
  const read = useCallback(async (force: boolean) => {
    generation.current += 1;
    const mine = generation.current;
    if (!extractionId || !sourceId) return;
    try {
      const next = await readGuidePlan(sourceId, extractionId, force ? { force: true } : {});
      // Only this reading's own plan (a plan for another reading is not this pane's).
      if (generation.current === mine) setPlan(next && next.extractionId === extractionId ? next : null);
    } catch {
      /* The marks the pane has stay; the next change re-reads. */
    }
  }, [extractionId, sourceId]);
  useEffect(() => {
    const again = readFor.current === extractionId && extractionId !== null;
    readFor.current = extractionId;
    if (!again) setPlan(null);
    void Promise.resolve().then(() => read(again));
  }, [extractionId, densityKey, read]);
  const reloadPlan = useCallback(() => read(true), [read]);
  // The density is one vault-wide setting (with a per-book off): a change
  // made here re-reads both panes' plans.
  const reloadBoth = useCallback(async () => {
    await read(true);
    await reloadMainPlan();
  }, [read, reloadMainPlan]);

  // The pane's text is laid out again when its size changes (the splitter,
  // the rail's overlay, the window): placement then runs again. Never on
  // scroll (a scroll changes no size).
  const [geometry, setGeometry] = useState(0);
  useEffect(() => {
    const body = hostRef.current;
    if (!extractionId || !body || typeof ResizeObserver === "undefined") return;
    let last: string | null = null;
    const observer = new ResizeObserver(() => {
      const size = `${body.clientWidth}x${body.clientHeight}`;
      if (size === last) return;
      last = size;
      setGeometry((value) => value + 1);
    });
    observer.observe(body);
    return () => observer.disconnect();
  }, [extractionId, hostRef]);

  const render = useMemo(() => (extractionId && sourceId ? { extractionId, sourceId } : null), [extractionId, sourceId]);
  const spanOrder = useMemo(
    () => new Map((blocks ?? []).map((block, index) => [block.spanId, index] as const)), [blocks]);
  const blocksKey = (blocks ?? []).map((block) => block.spanId).join("|");
  // A mark moved to by Alt+↓ / Alt+↑ is placed in this pane (a placement, never reading).
  const jumpToSpan = useCallback((spanId: string) => {
    const node = Array.from(hostRef.current?.querySelectorAll<HTMLElement>("[data-sbs-span]") ?? [])
      .find((element) => element.dataset.sbsSpan === spanId);
    node?.scrollIntoView?.({ behavior: "auto", block: "center" });
  }, [hostRef]);
  // Alt+↓ / Alt+↑ are this pane's while focus is in it (the main pane's controller leaves them).
  const ownsKey = useCallback((event: KeyboardEvent) => inSidePane(event.target), []);
  // The funnel names the book beside (its source and reading) on each mark it counts.
  const sideVisitPayload = useCallback(() => ({
    ...visitPayload(), target_source_id: sourceId, target_extraction_id: extractionId, entry: "side_by_side",
  }), [visitPayload, sourceId, extractionId]);
  // RW3b's receipts for this book belong to this book's own cue visit (one per open of it).
  const ownVisit = useCallback(() => null, []);

  const cueCtl = useReaderCues({
    render, working: false, offline, guidePlan: plan, reloadGuidePlan: reloadPlan, reloadAfterPreference: reloadBoth,
    skimming: muted, restoredSpanId: null, surface: render ? "text" : "none", pdfBlocks: null, pdfLayout: null,
    bodyRef: hostRef, layoutKey: `${blocksKey}:${geometry}`, spanOrder, readingSpan: null,
    visitPayload: sideVisitPayload, jumpToSpan, notePlacement: noop, onError,
    spanAttribute: "data-sbs-span", ownsKey, cueVisitId: ownVisit,
    // Final verify F11, F12: discovery's open is the book's, not the section's:
    // moving among its sections (by hand or follow along) pauses discovery and
    // keeps the open id, what was asked and its budget; closing ends it.
    discoveryOpenKey: openBook,
    ...(onCheckMe ? { onCheckMe } : {}), ...(onTryFirst ? { onTryFirst } : {}),
  });
  return cueCtl;
}

/** Whether a key event happened in side by side's second pane. */
export function inSidePane(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest("[data-side-by-side-pane]") !== null;
}
