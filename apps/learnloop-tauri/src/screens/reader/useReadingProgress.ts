// Reading progress and the section quick checks' offers (UX Phase 1 and
// reading-hardening), moved out of ReaderScreen by the RW3a hook extraction
// with no behaviour change.
//
// Where the learner is reading (the reading position and how far into a
// page-only passage), whether they have moved the page themselves, how far
// each section was read (saved, retried), the guide's current section and
// the one check-offer rule's offered set (checkOffer.ts stays the single
// offer authority: every offer path reads `offeredCheckSections`), the
// quick-check producer trigger and its poll, and the placements that are not
// reading (a jump, a resume, a seek, the preparing view's hand-over).
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type MutableRefObject,
  type RefObject,
  type SetStateAction,
} from "react";
import { api } from "../../api/client";
import type {
  ReaderGuidePlanDto,
  ReaderGuideSectionDto,
  ReaderPdfViewDto,
  ReaderProgressListDto,
  ReaderRenderBlockDto,
  ReaderRenderViewDto,
  ReaderWatchPlanDto,
} from "../../api/dto";
import type { PassageAlign, PdfReaderPaneHandle } from "../../components/PdfReaderPane";
import { checkOffer, type CheckSurface } from "./checkOffer";
import { useGuideDiagnosisRefresh } from "./guidePlan";
import {
  pagePositionAt,
  resumeSpanFromHistory,
  spanAtPosition,
  spanOnPage,
  type ReadingPosition,
  type SectionHistory,
} from "./readingPosition";

// Following the learner (usability round 1): how long a jump or a resume
// takes to settle before scrolling counts as reading again, and how long
// reading positions gather before they are saved.
export const SEEN_SETTLE_MS = 1500;
export const SEEN_REPORT_MS = 1500;
// Timed retries of a failed progress save (leaving the Reader always retries).
const SEEN_RETRY_LIMIT = 3;
// The reading marker sits 70% of the way down the reading area (as the
// extracted-text view's), and a page-only passage counts as read once the
// marker is this far through it.
export const READING_MARKER = 0.7;
const PAGE_READ_THROUGH = 0.85;
// Usability round 2: reading is the learner moving the page (wheel, keys,
// touch, the scrollbar). A scroll this soon after their own input is theirs;
// any other (pages loading, a jump, a resume) is the view settling.
const USER_SCROLL_MS = 1200;
const SCROLL_KEYS = new Set(["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ", "Spacebar"]);

/** One book's reading-progress saves (round-2 review F3, re-review F7): the
 * newest count per section, the counts the backend acknowledged and the ones
 * on their way, and the book's timed retry. It outlives leaving the book, so a
 * retry set before the learner left sends that book's newest counts. */
interface SeenSave {
  wanted: Record<string, { spansSeen: number; spanCount: number }>;
  acknowledged: Record<string, number>;
  sending: Record<string, number>;
  attempts: number;
  timer: number | null;
}

function seenSaveFor(saves: Map<string, SeenSave>, extractionId: string): SeenSave {
  let save = saves.get(extractionId);
  if (!save) {
    save = { wanted: {}, acknowledged: {}, sending: {}, attempts: 0, timer: null };
    saves.set(extractionId, save);
  }
  return save;
}

/** Send a book's counts that are neither acknowledged nor on their way. A
 * failed save is tried again a few times (a busy database, a restarting
 * sidecar) with whatever the book's newest counts are by then; after that it
 * waits for the next change, or for the learner leaving the book or the Reader. */
function sendSeenCounts(saves: Map<string, SeenSave>, extractionId: string): void {
  const save = saves.get(extractionId);
  if (!save) return;
  for (const [sectionId, { spansSeen, spanCount }] of Object.entries(save.wanted)) {
    if (spansSeen <= Math.max(save.acknowledged[sectionId] ?? 0, save.sending[sectionId] ?? 0)) continue;
    save.sending[sectionId] = spansSeen;
    api.readerNoteReadingProgress({ extractionId, sectionId, spansSeen, spanCount })
      .then(() => {
        save.acknowledged[sectionId] = Math.max(save.acknowledged[sectionId] ?? 0, spansSeen);
        save.attempts = 0;
      })
      .catch(() => {
        if (save.timer !== null || save.attempts >= SEEN_RETRY_LIMIT) return;
        save.attempts += 1;
        save.timer = window.setTimeout(() => {
          save.timer = null;
          sendSeenCounts(saves, extractionId);
        }, SEEN_REPORT_MS * 2 ** save.attempts);
      })
      .finally(() => {
        if (save.sending[sectionId] === spansSeen) delete save.sending[sectionId];
      });
  }
}

export function readingPositionKey(sourceId: string): string {
  return `learnloop.reader.position.${sourceId}`;
}

/** A saved reading place: the passage, and the reading it was saved on (null
 *  for a place saved before places recorded their reading: a bare span id). */
export interface SavedReadingPlace {
  extractionId: string | null;
  spanId: string;
}

/** The stored form of a reading place (re-read safety): the reading travels
 *  with the span, so a place saved before the book was read again is
 *  translated, never taken as a span of the new reading. */
export function encodeReadingPlace(extractionId: string, spanId: string): string {
  return JSON.stringify({ extractionId, spanId });
}

export function decodeReadingPlace(value: string | null): SavedReadingPlace | null {
  if (!value) return null;
  if (value.startsWith("{")) {
    try {
      const parsed = JSON.parse(value) as { extractionId?: unknown; spanId?: unknown };
      if (typeof parsed.spanId !== "string" || !parsed.spanId) return null;
      return { extractionId: typeof parsed.extractionId === "string" ? parsed.extractionId : null, spanId: parsed.spanId };
    } catch {
      return null;
    }
  }
  return { extractionId: null, spanId: value };
}

/** The reading a source opened on, as placing the saved position needs it. */
export interface OpenedReading {
  extractionId: string;
  /** Readings with aliases into this one (reader.render_view's aliasedFrom). */
  aliasedFrom?: string[];
  /** Every other reading of the book (reader.render_view's otherReadings),
   *  aliases or not: the reading history (Codex review F5). */
  otherReadings?: string[];
}

/** Whether a saved place is on the reading the book opened on, so it is used
 *  as it is. A bare span id (saved before places recorded their reading) is
 *  only when the book has no other reading at all: aliases may be missing (a
 *  re-read made before they were recorded, one that matched nothing), so the
 *  reading history decides, never the alias rows (Codex review F5). */
export function placeIsOnReading(saved: SavedReadingPlace, reading: OpenedReading | undefined): boolean {
  if (!reading) return true;
  if (saved.extractionId) return saved.extractionId === reading.extractionId;
  return (reading.otherReadings ?? reading.aliasedFrom ?? []).length === 0;
}

/** Imperative handle of the watch panel the jumps seek. */
export interface WatchSeekHandle {
  seekToSpan: (spanId: string) => boolean;
}

export interface ReadingProgressInput {
  render: ReaderRenderViewDto | null;
  offline: boolean;
  /** The source's readable blocks (page furniture dropped). */
  blocks: ReaderRenderBlockDto[];
  guidePlan: ReaderGuidePlanDto | null;
  setGuidePlan: Dispatch<SetStateAction<ReaderGuidePlanDto | null>>;
  guideLoading: boolean;
  pdfView: ReaderPdfViewDto | null;
  pdfViewPending: boolean;
  surface: "pdf" | "text";
  watch: ReaderWatchPlanDto | null;
  watchLoading: boolean;
  /** The reading depth ("skim" | "anchor" | "incremental"). */
  mode: string;
  /** RW1a's switch (reader_inquiry.enabled). */
  inquiry: boolean;
  /** Skim with inquiry on: nothing LearnLoop starts shows. */
  muted: boolean;
  activeSpan: string | null;
  setActiveSpan: Dispatch<SetStateAction<string | null>>;
  bodyRef: RefObject<HTMLDivElement | null>;
  railRef: RefObject<HTMLDivElement | null>;
  paneRef: RefObject<PdfReaderPaneHandle | null>;
  watchRef: RefObject<WatchSeekHandle | null>;
  /** Count a LearnLoop-started element once per visit (useReaderVisit). */
  noteProactive: (key: string, element: string) => boolean;
  /** Open the rail on the Guide tab (a check the learner asked to open). */
  showGuideRail: () => void;
}

export interface ReadingProgress {
  readingSpan: string | null;
  setReadingSpan: Dispatch<SetStateAction<string | null>>;
  readingOffset: number | null;
  /** The passage the Reader placed the learner at (a resume, a search hit,
   *  the reading history, the preparing view's hand-over, a walk back): RW3a
   *  never puts a margin mark there. */
  restoredSpan: string | null;
  /** A walk of the return stack landed the learner on this passage. */
  noteRestored: (spanId: string | null) => void;
  sectionSeen: Record<string, number>;
  readingMoved: boolean;
  focusQuickCheck: string | null;
  hiddenPdfOffers: string[];
  setHiddenPdfOffers: Dispatch<SetStateAction<string[]>>;
  answeredSections: string[];
  setAnsweredSections: Dispatch<SetStateAction<string[]>>;
  revealedSections: string[];
  dismissedSections: string[];
  setDismissedSections: Dispatch<SetStateAction<string[]>>;
  completedSections: string[];
  sectionPromptsEnabled: boolean;
  setSectionPromptsEnabled: Dispatch<SetStateAction<boolean>>;
  /** Section checks are on: reading closely with quick checks on. */
  boundaryChecksAvailable: boolean;
  authoringSections: string[];
  timedOutSections: string[];
  guideSectionBySpan: Map<string, ReaderGuideSectionDto>;
  guideSectionByEnd: Map<string, ReaderGuideSectionDto>;
  currentGuideSection: ReaderGuideSectionDto | null;
  currentSectionProgress: number;
  currentSectionRead: number;
  pdfSurfaceActive: boolean;
  /** The original PDF without block geometry: passages know only their page. */
  pageMode: boolean;
  checkSurface: CheckSurface;
  /** The ONE check-offer rule's verdict for every section (checkOffer.ts). */
  offeredCheckSections: Set<string>;
  openQuestionSections: ReaderGuideSectionDto[];
  pendingQuickCheckCount: number;
  currentQuestionOpen: boolean;
  pdfOfferSection: ReaderGuideSectionDto | null;
  readingProgress: number;
  retryQuickCheck: (sectionId: string) => void;
  openQuickCheck: (sectionId: string) => void;
  revealSection: (sectionId: string) => void;
  completeSection: (sectionId: string) => void;
  jumpToSpan: (spanId: string, align?: PassageAlign) => void;
  /** The view is about to move without a jump (focus brings a transcript's
   *  margin mark into view): a placement, like a jump -- the learner's
   *  movement resets and nothing it passes counts as read (RW3a review F1). */
  notePlacement: () => void;
  revealSegment: (page: number, spanId: string, align?: PassageAlign) => void;
  onReadingScroll: () => void;
  noteUserScroll: () => void;
  onPlaybackSpan: (spanId: string | null, advancing: boolean) => void;
  onPlaybackSeek: (spanId: string | null) => void;
  /** Opening, a jump and a resume move the view without being reading. */
  settleUntilRef: MutableRefObject<number>;
  /** Where the learner was in the original when the text became ready. */
  handoffRef: MutableRefObject<ReadingPosition | null>;
  /** An explicit jump is moving the page until this time (not the learner). */
  jumpGuardRef: MutableRefObject<number>;
  /** Opening a source restores a position: following starts once it settles. */
  settleOpening: () => void;
  /** Place the reading position a source opens at: the saved place, or a
   *  search hit's passage over it; with neither (and no hand-over) the
   *  reading history decides once it is read. */
  placeAtOpen: (
    sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading,
    jumpReading?: string | null,
  ) => void;
  /** The saved place (``"saved"``) or a search hit's passage (``"found"``)
   *  was translated onto a reading whose text changed there (re-read safety):
   *  the Reader says the place is approximate. False: it is exact. */
  placeApproximate: false | "saved" | "found";
  /** Hydrate durable reading progress so reveal/completion survive restarts. */
  hydrateProgress: (extractionId: string, progress: ReaderProgressListDto) => void;
  /** Per-source reset; leaving a book saves what was read in it first. */
  resetProgress: () => void;
}

export function useReadingProgress(input: ReadingProgressInput): ReadingProgress {
  const {
    render, offline, blocks, guidePlan, setGuidePlan, guideLoading, pdfView, pdfViewPending, surface,
    watch, watchLoading, mode, inquiry, muted, activeSpan, setActiveSpan, bodyRef, railRef, paneRef,
    watchRef, noteProactive, showGuideRail,
  } = input;
  const [readingSpan, setReadingSpan] = useState<string | null>(null);
  const [restoredSpan, setRestoredSpan] = useState<string | null>(null);
  // How far into the reading passage's page the reading marker is, when the
  // original PDF only knows each passage's page (usability round 1, U2).
  const [readingOffset, setReadingOffset] = useState<number | null>(null);
  // How many of each section's passages the learner has read (monotone),
  // hydrated from and saved to reader.mark_section_progress: a section is
  // ticked when it was read through, never because the learner jumped past it.
  const [sectionSeen, setSectionSeen] = useState<Record<string, number>>({});
  // The quick check the learner asked to open from a section break: shown
  // above Contents, scrolled to and started (usability round 1, U5).
  const [focusQuickCheck, setFocusQuickCheck] = useState<string | null>(null);
  // Section-break offers on the original PDF the learner set aside.
  const [hiddenPdfOffers, setHiddenPdfOffers] = useState<string[]>([]);
  // Usability round 2: whether the learner has moved the page themselves since
  // the book opened (or since their last jump). Until then nothing counts as
  // read and no quick check is written: a paper opened on its first page was
  // asked about its Introduction before a word was read.
  const [readingMoved, setReadingMoved] = useState(false);
  const userScrollAtRef = useRef(0);
  // A scroll of the learner's own, waiting for the frame that reads where it
  // took them (``onReadingScroll``).
  const movedPendingRef = useRef(false);
  // Reading history from before the Reader saved places (usability round 2):
  // where a book with no saved place reopens.
  const [readingHistory, setReadingHistory] = useState<SectionHistory[] | null>(null);
  const historyResumeRef = useRef(false);
  // Re-read safety: a place saved on an earlier reading of the book, once the
  // sidecar has translated it (null: none waiting), and a nudge for the
  // history resume when it could not be.
  const [translatedPlace, setTranslatedPlace] = useState<
    { spanId: string; approximate: false | "saved" | "found" } | null
  >(null);
  const [placeApproximate, setPlaceApproximate] = useState<false | "saved" | "found">(false);
  const [historyKick, setHistoryKick] = useState(0);
  const placeRequestRef = useRef(0);
  // Quick checks the learner answered this visit: the guide stops calling them
  // "ready, just below" (usability round 2).
  const [answeredSections, setAnsweredSections] = useState<string[]>([]);
  const [revealedSections, setRevealedSections] = useState<string[]>([]);
  const [dismissedSections, setDismissedSections] = useState<string[]>([]);
  const [completedSections, setCompletedSections] = useState<string[]>([]);
  const [sectionPromptsEnabled, setSectionPromptsEnabled] = useState(() => {
    try {
      return window.localStorage.getItem("learnloop.reader.section-prompts") !== "off";
    } catch {
      return true;
    }
  });
  // Quick checks stay visible once due: a section whose question became due is
  // pinned here until answered or dismissed, so playback/scroll moving the
  // "current" section (constant in watch mode) never hides an open check.
  const [stickyQuestionSections, setStickyQuestionSections] = useState<string[]>([]);
  // Quick-check producer: sections whose authoring job is in flight (guide
  // plan polls until the question lands), and a per-source once-only guard.
  const [authoringSections, setAuthoringSections] = useState<string[]>([]);
  const authorRequestedRef = useRef<Set<string>>(new Set());
  // UX Phase 1 (§10 item 1.10): sections whose check took too long to write.
  // They say so, with Try again, instead of the line silently disappearing.
  const [timedOutSections, setTimedOutSections] = useState<string[]>([]);
  const authoringRef = useRef<string[]>([]);
  authoringRef.current = authoringSections;
  // Where the learner was in the original when the text became ready: the full
  // Reader opens there, not at the top (review F8).
  const handoffRef = useRef<ReadingPosition | null>(null);
  // Scroll baseline guard (RW1a): an explicit jump moves the page itself, so
  // for a moment after one scrolling is not the learner's.
  const jumpGuardRef = useRef(0);
  const readingRafRef = useRef<number | null>(null);
  // Following the learner (usability round 1, U2/U3): opening a book, a jump
  // and a resume move the view without being reading. For a moment after one
  // the position they set stands (the first layout pass must not overwrite a
  // restored place) and no section counts as read.
  const settleUntilRef = useRef(0);
  // How far each section was read, per book (extraction): the newest counts,
  // the ones the backend acknowledged and the ones on their way (round-2
  // review F3: a save that failed was counted as reported and never sent
  // again). A book's entry is kept after the learner leaves it, so its retry
  // still sends its newest counts (re-review F7), and a late answer lands in
  // that book's entry.
  const seenSavesRef = useRef(new Map<string, SeenSave>());
  // The book being read now, which leaving it saves first.
  const activeSeenRef = useRef<string | null>(null);
  const lastReadRef = useRef<{ id: string; index: number; progress: number } | null>(null);
  const pageModeRef = useRef(false);
  const pageSpansRef = useRef<Array<{ spanId: string; page: number }>>([]);
  // Watching is reading too (see onPlaybackSpan): the cue playback was last at.
  const lastPlaybackSpanRef = useRef<string | null>(null);

  useEffect(() => {
    try {
      window.localStorage.setItem("learnloop.reader.section-prompts", sectionPromptsEnabled ? "on" : "off");
    } catch {
      /* A denied storage write should not interrupt reading. */
    }
  }, [sectionPromptsEnabled]);

  const resetProgress = useCallback(() => {
    // Leaving a book for another (or for the Library) saves what was read in
    // it first, as closing the Reader does (UX round-2 review F3). Its entry
    // stays: a save still failing is retried with its newest counts (F7).
    if (activeSeenRef.current) sendSeenCounts(seenSavesRef.current, activeSeenRef.current);
    activeSeenRef.current = null;
    setReadingSpan(null);
    setRestoredSpan(null);
    setReadingOffset(null);
    setSectionSeen({});
    lastReadRef.current = null;
    setFocusQuickCheck(null);
    setHiddenPdfOffers([]);
    setReadingMoved(false);
    movedPendingRef.current = false;
    userScrollAtRef.current = 0;
    lastPlaybackSpanRef.current = null;
    setReadingHistory(null);
    historyResumeRef.current = false;
    placeRequestRef.current += 1;
    setTranslatedPlace(null);
    setPlaceApproximate(false);
    setAnsweredSections([]);
    setRevealedSections([]);
    setDismissedSections([]);
    setCompletedSections([]);
    setAuthoringSections([]);
    setTimedOutSections([]);
    authorRequestedRef.current = new Set();
    setStickyQuestionSections([]);
  }, []);

  const settleOpening = useCallback(() => {
    settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
  }, []);

  const placeAtOpen = useCallback((
    sourceId: string, jumpSpan: string | undefined, handoff: ReadingPosition | null, reading?: OpenedReading,
    jumpReading?: string | null,
  ) => {
    let placed = Boolean(handoff);
    let translating = false;
    // A place on another reading of the book (a saved place, or a search hit
    // found before the book was read again): translated through the re-read's
    // aliases by the sidecar, never taken as a span of this reading (re-read
    // safety). Stale or unknown: the reading history decides.
    const translate = (place: SavedReadingPlace, kind: "saved" | "found") => {
      translating = true;
      const request = ++placeRequestRef.current;
      api
        .readerSavedPlace({ sourceId, spanId: place.spanId, extractionId: place.extractionId })
        .then((landed) => {
          if (placeRequestRef.current !== request) return;
          if (landed.spanId && landed.status !== "stale") {
            setTranslatedPlace({ spanId: landed.spanId, approximate: landed.status === "needs_reanchor" ? kind : false });
          } else {
            historyResumeRef.current = true;
            setHistoryKick((value) => value + 1);
          }
        })
        .catch(() => {
          if (placeRequestRef.current !== request) return;
          historyResumeRef.current = true;
          setHistoryKick((value) => value + 1);
        });
    };
    // A search hit (or a return) names its own reading (Codex review F8): one
    // on another reading is translated like a saved place.
    const jump: SavedReadingPlace | null = jumpSpan ? { extractionId: jumpReading ?? null, spanId: jumpSpan } : null;
    const jumpHere = jump !== null && (!jump.extractionId || placeIsOnReading(jump, reading));
    try {
      const saved = decodeReadingPlace(window.localStorage.getItem(readingPositionKey(sourceId)));
      if (saved && placeIsOnReading(saved, reading)) {
        setReadingSpan(saved.spanId);
        setActiveSpan(saved.spanId);
        setRestoredSpan(saved.spanId);
        placed = true;
      } else if (saved && !handoff && !jump) {
        translate(saved, "saved");
      }
    } catch {
      /* Reading still works when storage is unavailable. */
    }
    // A search hit overrides the resume position: the learner asked to land
    // on the matching passage, not where they left off.
    if (jump && jumpHere) {
      setReadingSpan(jump.spanId);
      setActiveSpan(jump.spanId);
      setRestoredSpan(jump.spanId);
      placed = true;
    } else if (jump && !handoff) {
      translate(jump, "found");
    }
    // No saved place: the reading history decides, once it is read (below).
    historyResumeRef.current = !placed && !translating;
  }, [setActiveSpan]);

  const hydrateProgress = useCallback((extractionId: string, progress: ReaderProgressListDto) => {
    // How far each section was read survives a restart (usability round 1, U3).
    const seen: Record<string, number> = {};
    for (const row of progress.sections) if (row.spansSeen > 0) seen[row.sectionId] = row.spansSeen;
    const acknowledged = seenSaveFor(seenSavesRef.current, extractionId).acknowledged;
    for (const [id, count] of Object.entries(seen)) acknowledged[id] = Math.max(acknowledged[id] ?? 0, count);
    setSectionSeen((current) => {
      const next = { ...current };
      for (const [id, count] of Object.entries(seen)) next[id] = Math.max(next[id] ?? 0, count);
      return next;
    });
    setRevealedSections((ids) => [
      ...new Set([...ids, ...progress.sections.filter((s) => s.revealedAt).map((s) => s.sectionId)])
    ]);
    setCompletedSections((ids) => [
      ...new Set([...ids, ...progress.sections.filter((s) => s.completedAt).map((s) => s.sectionId)])
    ]);
    setReadingHistory(progress.sections);
  }, []);

  // The original PDF without block geometry (a text-only extraction): each
  // passage still knows its page, and that is how the Reader jumps to,
  // follows and resumes the learner's place (usability round 1, U2).
  const pageSpans = useMemo(
    () => (pdfView && pdfView.blocks.length === 0 ? pdfView.pageSpans ?? [] : []),
    [pdfView],
  );
  const pageOfSpan = useMemo(() => new Map(pageSpans.map((entry) => [entry.spanId, entry.page])), [pageSpans]);
  const pageMode = Boolean(pdfView && surface === "pdf" && !offline && pageSpans.length > 0);
  pageModeRef.current = pageMode;
  pageSpansRef.current = pageSpans;

  const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled;

  const guideSectionBySpan = useMemo(() => {
    const map = new Map<string, ReaderGuideSectionDto>();
    for (const section of guidePlan?.sections ?? []) {
      for (const spanId of section.spanIds) map.set(spanId, section);
    }
    return map;
  }, [guidePlan]);
  const guideSectionByEnd = useMemo(
    () => new Map((guidePlan?.sections ?? []).map((section) => [section.endSpanId, section])),
    [guidePlan],
  );
  const currentGuideSection = useMemo(() => {
    const positioned = guideSectionBySpan.get(readingSpan ?? activeSpan ?? "");
    return positioned ?? guidePlan?.sections[0] ?? null;
  }, [guideSectionBySpan, readingSpan, activeSpan, guidePlan]);
  const currentSectionProgress = useMemo(() => {
    if (!currentGuideSection) return 0;
    const at = currentGuideSection.spanIds.indexOf(readingSpan ?? activeSpan ?? "");
    // A page-only passage is read as the marker moves down its page.
    const withinPassage = pageMode && readingOffset !== null ? readingOffset : 1;
    return at < 0 ? 0 : (at + withinPassage) / Math.max(1, currentGuideSection.spanIds.length);
  }, [currentGuideSection, readingSpan, activeSpan, pageMode, readingOffset]);
  // How much of the current section the learner has read (not where the
  // marker stands): the guide's bar under the section's name (finishing pass,
  // re-test #7: the bar was full on arriving at an unread one-page section).
  const currentSectionRead = useMemo(() => {
    if (!currentGuideSection) return 0;
    if (completedSections.includes(currentGuideSection.id)) return 1;
    const count = Math.max(1, currentGuideSection.spanIds.length);
    return Math.min(1, (sectionSeen[currentGuideSection.id] ?? 0) / count);
  }, [currentGuideSection, completedSections, sectionSeen]);
  // The original PDF's section break is at the section's last page, reached
  // by the learner's own reading this visit (finishing pass, re-test #8: a
  // check came a page before "the table on the next page"; #2: a resume into
  // Axler's 1.36 offered 1.36's leftover check before it was read again).
  const pdfSurfaceActive = Boolean(pdfView && surface === "pdf" && !offline);
  // Whether the original is still on its way: no check is due, and none is
  // open in the section being read, until the surface it is read on is known
  // (finish re-review F2: a resume pinned the check by the text view's rule
  // while the manifest was pending, and the original then offered it).
  const pdfSurfaceLoading = Boolean(!pdfView && pdfViewPending && surface === "pdf" && !offline);
  const pageBySpan = useMemo(() => {
    const pages = new Map<string, number>();
    for (const entry of pdfView?.pageSpans ?? []) pages.set(entry.spanId, entry.page);
    for (const block of pdfView?.blocks ?? []) if (block.spanId && !pages.has(block.spanId)) pages.set(block.spanId, block.page);
    return pages;
  }, [pdfView]);
  // The original PDF: whether the reading position's page reached the
  // current section's last page (D22); null without page information.
  const atLastPage = useMemo(() => {
    if (!currentGuideSection) return null;
    const here = pageBySpan.get(readingSpan ?? activeSpan ?? "");
    const last = pageBySpan.get(currentGuideSection.endSpanId);
    if (here === undefined || last === undefined) return null;
    return here >= last;
  }, [currentGuideSection, pageBySpan, readingSpan, activeSpan]);
  // What a section is read on, for the check-offer rule: the original PDF,
  // the original still on its way (the manifest is pending), a video, or the
  // text view (also where a manifest that failed or is unavailable leaves it).
  const checkSurface: CheckSurface = watch || watchLoading
    ? "watch"
    : pdfSurfaceActive ? "pdf" : pdfSurfaceLoading ? "loading" : "text";

  // ONE rule decides whether a section's quick check is offered (reading-
  // hardening, part 2; screens/reader/checkOffer.ts): the guide's cards and
  // the rail badge, the original PDF's section-break offer and the text
  // view's section-break buttons all read this set. A check left from an
  // earlier visit that a resume or a jump placed the learner at waits for the
  // learner's own reading in this visit; a section reached by reading follows
  // the normal rules; nothing is offered while the original is on its way.
  // Once offered a check is pinned (below) until answered or set aside, so
  // playback or scrolling moving the "current" section never hides it.
  const offeredCheckSections = useMemo(() => {
    const sections = guidePlan?.sections ?? [];
    const currentIndex = sections.findIndex((section) => section.id === currentGuideSection?.id);
    const offered = new Set<string>();
    sections.forEach((section, index) => {
      const decision = checkOffer({
        kind: "section",
        readingPhase: section.question?.readingPhase ?? null,
        available: boundaryChecksAvailable,
        settled: dismissedSections.includes(section.id) || completedSections.includes(section.id),
        pinned: stickyQuestionSections.includes(section.id),
        position: index === currentIndex ? "current" : currentIndex >= 0 && index < currentIndex ? "behind" : "ahead",
        readingMoved,
        surface: checkSurface,
        progress: index === currentIndex ? currentSectionProgress : 0,
        atLastPage: index === currentIndex ? atLastPage : null,
        firstPassageShare: 1 / Math.max(1, section.spanIds.length),
      });
      if (decision.offer) offered.add(section.id);
    });
    return offered;
  }, [guidePlan, currentGuideSection, boundaryChecksAvailable, dismissedSections, completedSections,
    stickyQuestionSections, readingMoved, checkSurface, currentSectionProgress, atLastPage]);

  // Pin a check the moment it is offered; it stays offered until answered or
  // dismissed, however far playback or scrolling (or a jump) moves on.
  useEffect(() => {
    const unpinned = [...offeredCheckSections].filter((id) => !stickyQuestionSections.includes(id));
    if (unpinned.length === 0) return;
    setStickyQuestionSections((ids) => [...new Set([...ids, ...unpinned])]);
  }, [offeredCheckSections, stickyQuestionSections]);

  // The open checks, in the guide's order: the rail's cards and badge count
  // exactly what is offered.
  const openQuestionSections = useMemo(
    () => (guidePlan?.sections ?? []).filter((section) => section.question !== null && offeredCheckSections.has(section.id)),
    [guidePlan, offeredCheckSections],
  );
  // A check the learner answered is not waiting any more, though its card
  // stays open to compare (usability round 2).
  const pendingQuickCheckCount = boundaryChecksAvailable
    ? openQuestionSections.filter((section) => !answeredSections.includes(section.id)).length
    : 0;

  // Proactive load (UX §9.2): each LearnLoop-started element counts once per
  // visit -- a quick check waiting on the Guide tab, a section-boundary offer
  // the learner reached.
  useEffect(() => {
    if (!inquiry || !boundaryChecksAvailable) return;
    for (const section of openQuestionSections) {
      noteProactive(`quick_check_waiting:${section.id}`, "quick_check_waiting");
    }
  }, [inquiry, boundaryChecksAvailable, openQuestionSections, noteProactive]);
  useEffect(() => {
    if (!inquiry || muted || !currentGuideSection || currentSectionProgress < 0.7) return;
    const section = currentGuideSection;
    if (dismissedSections.includes(section.id) || completedSections.includes(section.id)) return;
    const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section")
      || section.suggestedPassages.length > 0;
    if (!offered) return;
    noteProactive(`section_offer:${section.id}`, "section_offer");
  }, [inquiry, muted, currentGuideSection, currentSectionProgress, dismissedSections, completedSections, offeredCheckSections, noteProactive]);
  const currentQuestionOpen = useMemo(
    () => openQuestionSections.some((section) => section.id === currentGuideSection?.id),
    [openQuestionSections, currentGuideSection],
  );
  // The open check the original PDF offers at its section break: the latest
  // one at or behind the reading position the learner has not set aside.
  const pdfOfferSection = useMemo(() => {
    if (!pdfView || surface !== "pdf" || offline || !boundaryChecksAvailable) return null;
    const sections = guidePlan?.sections ?? [];
    const currentIndex = sections.findIndex((section) => section.id === currentGuideSection?.id);
    const offered = openQuestionSections.filter((section) => {
      const index = sections.findIndex((entry) => entry.id === section.id);
      return index >= 0 && index <= currentIndex && !hiddenPdfOffers.includes(section.id) && section.id !== focusQuickCheck;
    });
    return offered[offered.length - 1] ?? null;
  }, [pdfView, surface, offline, boundaryChecksAvailable, guidePlan, currentGuideSection, openQuestionSections, hiddenPdfOffers, focusQuickCheck]);
  const readingProgress = useMemo(() => {
    const at = blocks.findIndex((block) => block.spanId === (readingSpan ?? activeSpan));
    return at < 0 ? 0 : (at + 1) / Math.max(1, blocks.length);
  }, [blocks, readingSpan, activeSpan]);

  // How far each section was read (usability round 1, U3). Scrolling through a
  // section counts its passages up to the reading marker; leaving it forward
  // after most of it counts it whole. A jump or a resume moves the view
  // without being reading, so it never ticks the sections it passes.
  useEffect(() => {
    if (!render || offline || !currentGuideSection) return;
    const sections = guidePlan?.sections ?? [];
    const index = sections.findIndex((section) => section.id === currentGuideSection.id);
    const at = currentGuideSection.spanIds.indexOf(readingSpan ?? "");
    const last = lastReadRef.current;
    lastReadRef.current = { id: currentGuideSection.id, index, progress: currentSectionProgress };
    if (Date.now() < settleUntilRef.current || at < 0 || !readingMoved) return;
    const count = currentGuideSection.spanIds.length;
    const seenHere = pageMode ? at + ((readingOffset ?? 0) >= PAGE_READ_THROUGH ? 1 : 0) : at + 1;
    setSectionSeen((current) => {
      const next = { ...current };
      let changed = false;
      const raise = (id: string, value: number) => {
        if (value > (next[id] ?? 0)) {
          next[id] = value;
          changed = true;
        }
      };
      if (seenHere > 0) raise(currentGuideSection.id, Math.min(count, seenHere));
      if (last && last.id !== currentGuideSection.id && last.index >= 0 && index === last.index + 1 && last.progress >= 0.6) {
        raise(sections[last.index].id, sections[last.index].spanIds.length);
      }
      return changed ? next : current;
    });
  }, [render, offline, guidePlan, currentGuideSection, readingSpan, readingOffset, pageMode, currentSectionProgress, readingMoved]);

  // Save how far each section was read, gathered for a moment, and once more
  // when the Reader closes: Today's reading step and the next open read it.
  // A count is reported only once the backend has it; a failed save is tried
  // again a few times, and again when the learner leaves the book or the
  // Reader (round-2 review F3). The newest counts are kept in the book's own
  // entry at once, so every retry and every leaving sends them (F7).
  useEffect(() => {
    if (!render || offline) return;
    const extractionId = render.extractionId;
    const saves = seenSavesRef.current;
    const save = seenSaveFor(saves, extractionId);
    const counts = new Map((guidePlan?.sections ?? []).map((section) => [section.id, section.spanIds.length]));
    for (const [sectionId, spansSeen] of Object.entries(sectionSeen)) {
      const spanCount = counts.get(sectionId);
      if (spanCount === undefined) continue;
      if (spansSeen > (save.wanted[sectionId]?.spansSeen ?? 0)) save.wanted[sectionId] = { spansSeen, spanCount };
    }
    activeSeenRef.current = extractionId;
    const timer = window.setTimeout(() => sendSeenCounts(saves, extractionId), SEEN_REPORT_MS);
    return () => window.clearTimeout(timer);
  }, [render, offline, guidePlan, sectionSeen]);
  useEffect(() => {
    const saves = seenSavesRef.current;
    // Closing the Reader saves every book it still holds counts for.
    return () => {
      for (const extractionId of saves.keys()) sendSeenCounts(saves, extractionId);
    };
  }, []);

  // Quick-check producer trigger: approaching a section's end while reading
  // closely (anchor mode, prompts on) with no question placed for it enqueues
  // authoring once per section. The RPC only enqueues a durable job — reading
  // never waits on a model — and a failure is silent (the boundary card simply
  // stays passage-only).
  useEffect(() => {
    if (!render || offline || !boundaryChecksAvailable || guideLoading) return;
    const section = currentGuideSection;
    if (!section || section.question || authorRequestedRef.current.has(section.id)) return;
    if (dismissedSections.includes(section.id) || completedSections.includes(section.id)) return;
    // Only where the learner has read: never on the page a book opened at,
    // nor where a jump has only just landed.
    if (!readingMoved || currentSectionProgress < 0.6 || Date.now() < settleUntilRef.current) return;
    authorRequestedRef.current.add(section.id);
    const extractionId = render.extractionId;
    void (async () => {
      try {
        const result = await api.readerAuthorSectionQuestion({ extractionId, sectionId: section.id });
        if (result.status === "queued" || result.question?.status === "proposed") {
          setAuthoringSections((ids) => [...new Set([...ids, section.id])]);
        }
      } catch {
        /* Authoring is best-effort (provider may be off); never interrupt reading. */
      }
    })();
  }, [render, offline, boundaryChecksAvailable, guideLoading, currentGuideSection, currentSectionProgress, dismissedSections, completedSections, readingMoved]);

  // "Try again" on a section whose check took too long (UX Phase 1, 1.10).
  const retryQuickCheck = useCallback(
    (sectionId: string) => {
      if (!render || offline) return;
      setTimedOutSections((ids) => ids.filter((id) => id !== sectionId));
      authorRequestedRef.current.add(sectionId);
      const extractionId = render.extractionId;
      setAuthoringSections((ids) => [...new Set([...ids, sectionId])]);
      void api.readerAuthorSectionQuestion({ extractionId, sectionId }).catch(() => {
        setAuthoringSections((ids) => ids.filter((id) => id !== sectionId));
        setTimedOutSections((ids) => [...new Set([...ids, sectionId])]);
      });
    },
    [render, offline],
  );

  // "quick check →" at a section break opens that check: the Guide, the check
  // at the top of it, scrolled to and started (usability round 1, U5: the
  // button did nothing and the check sat below the whole Contents list).
  const openQuickCheck = useCallback((sectionId: string) => {
    // A rail the learner collapsed (RW1a's backslash key) opens for the check they asked for.
    showGuideRail();
    setStickyQuestionSections((ids) => (ids.includes(sectionId) ? ids : [...ids, sectionId]));
    setHiddenPdfOffers((ids) => (ids.includes(sectionId) ? ids : [...ids, sectionId]));
    setFocusQuickCheck(sectionId);
  }, [showGuideRail]);
  useEffect(() => {
    if (!focusQuickCheck) return;
    const frame = window.requestAnimationFrame(() => {
      const card = railRef.current?.querySelector(`[data-quick-check="${focusQuickCheck}"]`);
      if (card instanceof HTMLElement) card.scrollIntoView({ block: "nearest" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [focusQuickCheck, railRef]);

  // While authoring is in flight, re-fetch the guide plan (a cheap local read)
  // until the section gains its question or a bounded number of polls passes.
  useEffect(() => {
    if (!render || offline || authoringSections.length === 0) return;
    const extractionId = render.extractionId;
    let attempts = 0;
    const timer = window.setInterval(() => {
      attempts += 1;
      if (attempts > 45) {
        const stalled = authoringRef.current;
        setTimedOutSections((timedOut) => [...new Set([...timedOut, ...stalled])]);
        setAuthoringSections([]);
        return;
      }
      void api
        .readerGuidePlan({ extractionId })
        .then((plan) => {
          // Keep the last complete guide visible if a poll races the author's
          // write and transiently returns an empty projection. A quick-check
          // refresh must never blank the stable Guide/Ask/Notes rail.
          setGuidePlan((current) => {
            if (plan.extractionId !== extractionId) return current;
            if (current && current.sections.length > 0 && plan.sections.length === 0) return current;
            return plan;
          });
          setAuthoringSections((ids) =>
            ids.filter((id) => !plan.sections.find((s) => s.id === id)?.question),
          );
        })
        .catch(() => {
          /* Keep polling; the sidecar may be busy with the authoring job. */
        });
    }, 4000);
    return () => window.clearInterval(timer);
  }, [render, offline, authoringSections.length, setGuidePlan]);

  // A "Revisit this to resolve" reason names the error type until the
  // attempt's diagnosis lands; re-read the plan while it waits on one so the
  // Guide names the diagnoser's statement without a reopen. Like the
  // authoring poll, a refresh never blanks a complete Guide.
  const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto) => {
    setGuidePlan((current) => (current && current.sections.length > 0 && plan.sections.length === 0 ? current : plan));
  }, [setGuidePlan]);
  useGuideDiagnosisRefresh(render && !offline ? render : null, guidePlan, refreshGuidePlan);

  const updateReadingPosition = useCallback(() => {
    const container = bodyRef.current;
    if (!container || Date.now() < settleUntilRef.current) return;
    if (pageModeRef.current) {
      // The original PDF with page-only passages: the page under the marker.
      const position = pagePositionAt(container, READING_MARKER);
      const spanId = position ? spanOnPage(pageSpansRef.current, position) : null;
      if (position && spanId) {
        setReadingSpan(spanId);
        setReadingOffset(position.offset);
      }
      return;
    }
    const containerRect = container.getBoundingClientRect();
    const markerY = containerRect.top + containerRect.height * READING_MARKER;
    const nodes = Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"));
    let best: HTMLElement | null = null;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (const node of nodes) {
      const rect = node.getBoundingClientRect();
      if (rect.bottom < containerRect.top || rect.top > containerRect.bottom) continue;
      const distance = Math.abs(Math.min(Math.max(markerY, rect.top), rect.bottom) - markerY);
      if (distance < bestDistance) {
        best = node;
        bestDistance = distance;
      }
    }
    if (best?.dataset.spanId) setReadingSpan(best.dataset.spanId);
  }, [bodyRef]);

  const onReadingScroll = useCallback(() => {
    const now = Date.now();
    if (now >= settleUntilRef.current && now - userScrollAtRef.current < USER_SCROLL_MS) movedPendingRef.current = true;
    if (readingRafRef.current !== null) return;
    readingRafRef.current = window.requestAnimationFrame(() => {
      readingRafRef.current = null;
      updateReadingPosition();
      // The learner's movement counts together with where it took them, in
      // one render: never as reading at the place a resume or jump left the
      // page (reading-hardening, part 2: a first scroll away from a resumed
      // section's last page offered that section's check).
      if (movedPendingRef.current) {
        movedPendingRef.current = false;
        setReadingMoved(true);
      }
    });
  }, [updateReadingPosition]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(updateReadingPosition);
    return () => {
      window.cancelAnimationFrame(frame);
      if (readingRafRef.current !== null) window.cancelAnimationFrame(readingRafRef.current);
      readingRafRef.current = null;
    };
  }, [updateReadingPosition, render, surface, guidePlan]);

  const revealSection = useCallback(
    (sectionId: string) => {
      setRevealedSections((ids) => [...new Set([...ids, sectionId])]);
      if (render && !offline) {
        api
          .readerMarkSectionProgress({ extractionId: render.extractionId, sectionId, revealed: true })
          .catch(() => undefined);
      }
    },
    [render, offline]
  );

  // Completion persists durably and — first time only — triggers progressive
  // practice generation for the section's learning objects (items-off seeding).
  const completeSection = useCallback(
    (sectionId: string) => {
      setCompletedSections((ids) => [...new Set([...ids, sectionId])]);
      if (render && !offline) {
        api
          .readerMarkSectionProgress({ extractionId: render.extractionId, sectionId, completed: true })
          .catch(() => undefined);
      }
    },
    [render, offline]
  );

  // A passage with boxes: the pane keeps it until the document is laid out
  // and its page drawn, then centres it (usability round 2: a resume asked to
  // centre a block on a page that did not exist yet; round-2 review F4: only
  // a delayed page-top scroll survived). A place to read on from (a resume, a
  // section from Contents) goes to the top of the view instead, so the page
  // on screen is the one the header names (finishing pass, re-test #2: Axler
  // reopened on "1.36" with the 1.35 examples filling the screen above it).
  const revealSegment = useCallback((page: number, spanId: string, align: PassageAlign = "center") => {
    paneRef.current?.scrollToSegment(page, spanId, align);
  }, [paneRef]);

  const jumpToSpan = useCallback(
    (spanId: string, align: PassageAlign = "center") => {
      jumpGuardRef.current = Date.now() + 1200;
      // A jump is not reading (UX Phase 1): the sections it passes are not
      // ticked, and nothing is asked about where it lands until the learner
      // reads on.
      settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
      setReadingMoved(false);
      movedPendingRef.current = false;
      setActiveSpan(spanId);
      setReadingSpan(spanId);
      // Watch mode: a jump means "take the video there" — seek the player (the
      // transcript follows), never just scroll a nested list.
      if (watchRef.current?.seekToSpan(spanId)) return;
      if (pdfView && surface === "pdf" && !offline) {
        const geometry = pdfView.blocks.find((block) => block.spanId === spanId);
        if (geometry) {
          revealSegment(geometry.page, spanId, align);
          return;
        }
        // No boxes, only the passage's page (usability round 1, U2).
        const page = pageOfSpan.get(spanId);
        if (page !== undefined) {
          setReadingOffset(0);
          paneRef.current?.scrollToPage(page, 0);
          return;
        }
      }
      const el = bodyRef.current?.querySelector(`[data-span-id="${spanId}"]`);
      // An explicit jump; instant under reduced motion (UX §7.3). (Optional
      // call: a jump made before layout, as the reading-history resume can be,
      // must not throw where scrolling is unavailable.)
      const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (el instanceof HTMLElement) el.scrollIntoView?.({ behavior: reduced ? "auto" : "smooth", block: "center" });
    },
    [pdfView, surface, offline, pageOfSpan, revealSegment, setActiveSpan, watchRef, paneRef, bodyRef],
  );

  const notePlacement = useCallback(() => {
    jumpGuardRef.current = Date.now() + 1200;
    settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
    setReadingMoved(false);
    movedPendingRef.current = false;
  }, []);

  // A book with no saved place but reading history from before the Reader
  // saved places reopens where that history leaves off, as Today's reading
  // step does (usability round 2: Axler, read for months, opened at its first
  // page while Contents ticked sections into 1C). Once, when both are read.
  useEffect(() => {
    if (!historyResumeRef.current || !render || offline || !guidePlan || readingHistory === null) return;
    if (guidePlan.extractionId && guidePlan.extractionId !== render.extractionId) return;
    historyResumeRef.current = false;
    const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory);
    if (spanId) {
      setRestoredSpan(spanId);
      jumpToSpan(spanId, "start");
    }
  }, [render, offline, guidePlan, readingHistory, jumpToSpan, historyKick]);

  // A saved place translated from an earlier reading (re-read safety): the
  // Reader goes there once, saying so when the words there changed.
  useEffect(() => {
    if (!translatedPlace || !render || offline) return;
    setTranslatedPlace(null);
    setPlaceApproximate(translatedPlace.approximate);
    setRestoredSpan(translatedPlace.spanId);
    jumpToSpan(translatedPlace.spanId, "start");
  }, [translatedPlace, render, offline, jumpToSpan]);

  // The learner's own hand on the page: what makes a scroll reading (round 2).
  const noteUserScroll = useCallback(() => {
    userScrollAtRef.current = Date.now();
  }, []);
  // Watching is reading too: playback that moves past the cue a video
  // resumed at counts, as the learner's own scrolling does on a page. A seek
  // (a jump, a resume, a click in the transcript) only sets the cue playback
  // starts from, and nothing counts while the video is paused (round-2
  // review F5: a paused video taken to a short section counted as watched).
  const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean) => {
    const last = lastPlaybackSpanRef.current;
    lastPlaybackSpanRef.current = spanId;
    if (advancing && spanId && last && spanId !== last && Date.now() >= settleUntilRef.current) setReadingMoved(true);
    setReadingSpan(spanId);
  }, []);
  // Every seek the watch panel makes is a placement, like a jump on a page
  // (reading-hardening verify, N1: a click on a transcript cue past 70 % of an
  // unread section carried the watching done before it there, and offered and
  // pinned that section's check unwatched). The movement is reset in the
  // same render that moves the position, so no render judges the new place
  // by the old watching. Checks already offered stay pinned.
  const onPlaybackSeek = useCallback((spanId: string | null) => {
    settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
    setReadingMoved(false);
    movedPendingRef.current = false;
    lastPlaybackSpanRef.current = spanId;
    if (spanId) setReadingSpan(spanId);
  }, []);
  useEffect(() => {
    if (!render) return;
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      // An Alt chord is never a scroll key: Alt+↓ / Alt+↑ move between margin
      // marks (RW3a), and a mark brought into view is a placement, not reading.
      if (event.altKey) return;
      if (SCROLL_KEYS.has(event.key)) userScrollAtRef.current = Date.now();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [render]);

  // Resume the last stable span after the chosen surface has mounted. The
  // position is local to the source and never becomes learner evidence.
  useEffect(() => {
    if (!render || offline || !readingSpan || handoffRef.current) return;
    settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
    const frame = window.requestAnimationFrame(() => {
      if (pdfView && surface === "pdf") {
        const geometry = pdfView.blocks.find((block) => block.spanId === readingSpan);
        if (geometry) {
          revealSegment(geometry.page, readingSpan, "start");
          return;
        }
        // The page the learner left off on (usability round 1, U2).
        const page = (pdfView.pageSpans ?? []).find((entry) => entry.spanId === readingSpan)?.page;
        if (page !== undefined) paneRef.current?.scrollToPage(page, 0);
        return;
      }
      const element = bodyRef.current?.querySelector(`[data-span-id="${readingSpan}"]`);
      if (element instanceof HTMLElement) element.scrollIntoView({ block: "center" });
    });
    return () => window.cancelAnimationFrame(frame);
    // This is a mount/resurface effect. Normal scrolling must not repeatedly
    // scroll itself back to the marker it just recorded.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [render?.renderViewId, pdfView?.available, surface, offline]);

  // The hand-over from the preparing view (UX Phase 1 review F8): the same
  // page and viewport offset, and the passage there becomes the reading
  // position, so it is also where the book reopens next time.
  useEffect(() => {
    const position = handoffRef.current;
    if (!render || offline || !position || !pdfView?.available) return;
    handoffRef.current = null;
    const spanId = spanAtPosition(pdfView.blocks, position) ?? spanOnPage(pdfView.pageSpans ?? [], position);
    if (spanId) {
      setReadingSpan(spanId);
      setActiveSpan(spanId);
      setRestoredSpan(spanId);
    }
    paneRef.current?.scrollToPage(position.page, position.offset);
  }, [render, offline, pdfView, setActiveSpan, paneRef]);

  const noteRestored = useCallback((spanId: string | null) => {
    if (spanId) setRestoredSpan(spanId);
  }, []);

  return {
    readingSpan, setReadingSpan, readingOffset, restoredSpan, noteRestored, sectionSeen, readingMoved, focusQuickCheck,
    hiddenPdfOffers, setHiddenPdfOffers, answeredSections, setAnsweredSections, revealedSections,
    dismissedSections, setDismissedSections, completedSections, sectionPromptsEnabled, setSectionPromptsEnabled,
    boundaryChecksAvailable, authoringSections, timedOutSections, guideSectionBySpan, guideSectionByEnd,
    currentGuideSection, currentSectionProgress, currentSectionRead, pdfSurfaceActive, pageMode, checkSurface,
    offeredCheckSections, openQuestionSections, pendingQuickCheckCount, currentQuestionOpen, pdfOfferSection,
    readingProgress, retryQuickCheck, openQuickCheck, revealSection, completeSection, jumpToSpan, notePlacement, revealSegment,
    onReadingScroll, noteUserScroll, onPlaybackSpan, onPlaybackSeek, settleUntilRef, handoffRef, jumpGuardRef,
    settleOpening, placeAtOpen, placeApproximate, hydrateProgress, resetProgress,
  };
}
