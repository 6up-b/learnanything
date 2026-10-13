// ReaderScreen (P3 slice 1: spec_p3_reader_integration §3-§5; spec_tauri_ui §3 P3).
//
// The reading front door. Opens with a picker over the real source library
// (ready sources only); choosing a source fetches its live marker-markdown
// render view (blocks + per-block health) from `reader.render_view`, which
// resolves the source id to its latest completed extraction. The deterministic
// offline fixture survives only as an explicitly labeled demo, used when the
// sidecar is unreachable or on request (U-031) — offline captures are local to
// the window and honestly labeled as such. A text selection over a block is
// captured LOCALLY through `reader.capture` -> ONE durable annotation + outbox
// row (§5.3) before any model job, and shown in the annotation margin with its
// anchor status (`needs_reanchor` surfaces an "anchor needs review" note, never
// a false attachment). The P2 Ask panel (mode toggle) is preserved; the
// reviewed TaskBlueprint placements appear as optional real-source quick checks;
// the hard-coded demo question remains confined to the offline fixture.

import { Fragment, forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState, type ReactNode } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";
import { api } from "../api/client";
import { useCachedQuery } from "../api/useCachedQuery";
import { TAG } from "../api/queryTags";
import type {
  ReaderAnswerMode,
  ReaderDisposition,
  ReaderGuidePlanDto,
  ReaderGuideSectionDto,
  ReaderPdfViewDto,
  ReaderPromptContractDto,
  ReaderRenderBlockDto,
  ReaderRenderViewDto,
  ReaderSourceSearchDto,
  ReaderWatchPlanDto,
  ReaderArcDto,
  ReaderCoachLintDto,
  ReaderExerciseImportResult,
  SourceLibraryCard,
} from "../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader, TermSelect } from "../components/term";
import { MarkdownMath } from "../render/MarkdownMath";
import { AffectTap, DispositionPicker, PrimaryButton, SecondaryButton } from "../components/goldenpath/shared";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { youtubeVideoId } from "../components/sourceTail";
import { PdfReaderPane, type PassageAlign, type PdfReaderPaneHandle, type TagMenuRequest } from "../components/PdfReaderPane";
import { RectUnionOverlay } from "../components/RectUnionOverlay";
import { errorMessage } from "../errors";
import { authoredQuestionMessage, type AuthoredQuestionStatus } from "./reader/authoredQuestion";
import { searchBasisLabel } from "./reader/searchBasis";
import { readGuidePlan, useGuideDiagnosisRefresh } from "./reader/guidePlan";
import { cachedSourceRead } from "./reader/readerCache";
import { PreparingView } from "./reader/PreparingView";
import { readerKeyBarKeys } from "./reader/readerKeys";
import {
  pagePositionAt,
  resumeSpanFromHistory,
  spanAtPosition,
  spanOnPage,
  type ReadingPosition,
  type SectionHistory,
} from "./reader/readingPosition";
import {
  parseRequestError,
  parseRequestResult,
  useReaderRequests,
} from "./reader/useReaderRequests";

const ANSWER_MODE_OPTIONS = [
  { value: "answer_directly", label: "answer directly" },
  { value: "help_me_reason", label: "help me reason" },
  { value: "ask_me_first", label: "ask me first" },
];

/** The answer style in the learner's words, never its internal name (round 2). */
function answerModeLabel(mode: string): string {
  return ANSWER_MODE_OPTIONS.find((option) => option.value === mode)?.label ?? mode.replace(/_/g, " ");
}

const READER_MODE_OPTIONS = [
  { value: "skim", label: "skim quickly" },
  { value: "anchor", label: "read closely" },
  { value: "incremental", label: "mark for later" },
];

// The three visible primitives / nine presets (§5.2). Only the three commit presets
// are P1 commit-class; Ask and Mark never create commitments (§15.2).
// Naming: the "request" group runs in the BACKGROUND (demand-paged synthesis,
// results land in this rail) — deliberately distinct from the ask tab, which
// answers immediately about the selected span.
const PALETTE: Array<{ group: string; presets: Array<{ preset: string; label: string }> }> = [
  {
    group: "Request · answered in background",
    presets: [
      { preset: "ask", label: "research this" },
      { preset: "worked_example", label: "worked example" },
      { preset: "alt_explanation", label: "explain differently" },
      { preset: "why_matters", label: "why this matters" },
    ],
  },
  {
    group: "Remember later",
    presets: [
      { preset: "test_me_later", label: "test me later" },
      { preset: "help_me_remember", label: "help me remember" },
      { preset: "connect_it", label: "connect it" },
    ],
  },
  {
    group: "Mark",
    presets: [
      { preset: "mark_confusing", label: "mark confusing" },
      { preset: "not_worth_remembering", label: "not worth remembering" },
    ],
  },
];

const QUESTION_CONTROLS: Array<{ value: string; label: string }> = [
  { value: "too_easy", label: "too easy" },
  { value: "too_intrusive", label: "bad moment" },
  { value: "ask_me_differently", label: "ask differently" },
  { value: "dont_bring_this_back", label: "don’t ask this again" },
  { value: "i_dont_understand", label: "I don’t understand" },
];

// Right-click tag menu: the five plain capture actions. Each is a pure local
// annotation (action name == annotation_type in the sidecar's _ACTION_MAP) —
// no commitment, no synthesis job. Anchor statuses like "needs review" are
// computed by anchoring, never hand-tagged.
const TAG_ACTIONS: Array<{ action: string; label: string }> = [
  { action: "highlight", label: "highlight" },
  { action: "question", label: "question" },
  { action: "confusion", label: "confusing" },
  { action: "interpretation", label: "my interpretation" },
  { action: "disposition", label: "not worth remembering" },
];

const WHOLE_BLOCK_QUOTE = "(whole block)";

function clip(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

// The wire nodes for a selection: one per covered block (atomic-unit captures
// also carry glyph context for backend disambiguation), falling back to the
// single primary block for selections made outside the DOM capture path.
export interface SelectionNode {
  spanId: string;
  quote: string;
  prefix?: string;
  suffix?: string;
  /** Learner edited this quote (OCR fix) — the backend prefers it over the
   *  extraction slice as the exercise surface. */
  edited?: boolean;
}

function selectionNodes(sel: {
  spanId: string;
  quote: string;
  nodes?: SelectionNode[];
}): SelectionNode[] {
  return sel.nodes && sel.nodes.length ? sel.nodes : [{ spanId: sel.spanId, quote: sel.quote }];
}

interface ReaderExchange {
  id: string;
  spanId: string;
  question: string;
  answerMd: string;
  answerMode: ReaderAnswerMode;
  createdAt: string | null;
}

type ReaderRailTab = "guide" | "ask" | "notes";

const HEALTH_COLOR: Record<string, "green" | "amber" | "pink" | "slate"> = {
  ok: "green",
  suspect: "amber",
  failed: "pink",
  unknown: "slate",
};

// Page furniture is real extraction data but noise in a reading flow: running
// heads repeat every page and the book's own ToC interleaves mid-prose.
const FURNITURE_BLOCK_TYPES = new Set(["PageHeader", "PageFooter", "TableOfContents"]);

// "unknown" just means no health row was computed for this extraction — badging
// it on every block reads as an error state; only suspect/failed warrant a pill.
const BADGED_HEALTH = new Set(["suspect", "failed"]);
// Following the learner (usability round 1): how long a jump or a resume
// takes to settle before scrolling counts as reading again, and how long
// reading positions gather before they are saved.
const SEEN_SETTLE_MS = 1500;
const SEEN_REPORT_MS = 1500;
// Timed retries of a failed progress save (leaving the Reader always retries).
const SEEN_RETRY_LIMIT = 3;
// The reading marker sits 70% of the way down the reading area (as the
// extracted-text view's), and a page-only passage counts as read once the
// marker is this far through it.
const READING_MARKER = 0.7;
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

interface AnnotationSegment {
  spanId: string;
  page: number | null;
  bbox: number[] | null;
}

interface MarginAnnotation {
  annotationId: string | null;
  quote: string;
  status: string | null;
  learnerText: string;
  kind: string;
  segments: AnnotationSegment[];
}

/** A durably painted annotation region in the PDF surface (one per anchored
 *  segment with geometry). needs_reanchor annotations are never painted. */
export interface AnnotationTrail {
  annotationId: string | null;
  kind: string;
  spanId: string;
  page: number;
  bbox: number[];
}

function newKey(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `cap-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

function readingPositionKey(sourceId: string): string {
  return `learnloop.reader.position.${sourceId}`;
}

export interface ReaderOpenSource {
  card: SourceLibraryCard;
  spanId: string | null;
}

export function ReaderScreen({
  onError,
  initialSource = null,
  onSourceChange,
  onOpenLibrary,
  shelf
}: {
  onError: (message: string) => void;
  /** The source that was open when the Reader last unmounted (hoisted by the shell). */
  initialSource?: ReaderOpenSource | null;
  onSourceChange?: (next: ReaderOpenSource | null) => void;
  /** "← Library" goes to the Library place, the one shelf (spec K5; usability
   *  round 1: the Reader's own list was a second "Library"). */
  onOpenLibrary?: () => void;
  /** With no book open, the Library's own shelf (spec K5, usability round 2:
   *  the Reader's own list read as a second Library). */
  shelf?: ReactNode;
}) {
  // The prompt contract only changes with settings, so it is cached until a
  // settings mutation invalidates it; the picker's library list is shared with
  // the Ingest sidebar. Both repaint at once when the learner returns here.
  const contractQuery = useCachedQuery(["reader_prompt_contract"], () => api.readerPromptContract(), {
    tags: [TAG.reader, TAG.settings],
    staleAfterMs: Infinity
  });
  const contract: ReaderPromptContractDto | null = contractQuery.data ?? null;
  const [render, setRender] = useState<ReaderRenderViewDto | null>(null);
  const [guidePlan, setGuidePlan] = useState<ReaderGuidePlanDto | null>(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [offline, setOffline] = useState(false);
  // Source picker state: the real library (ready sources are openable), whether
  // the sidecar answered at all, and the title of whatever is open.
  // If the sidecar is unreachable the demo fixture stays available, clearly
  // labeled (U-031) — it is never silently substituted for a real source.
  const libraryQuery = useCachedQuery(["get_source_library"], () => api.getSourceLibrary(), { tags: [TAG.sources] });
  const sidecarDown = libraryQuery.data === undefined && libraryQuery.error !== null;
  const library: SourceLibraryCard[] | null = libraryQuery.data?.sources ?? (sidecarDown ? [] : null);
  const [sourceTitle, setSourceTitle] = useState<string | null>(null);
  const [opening, setOpening] = useState<string | null>(null);
  // The book being opened, named while its text loads (usability round 2: the
  // Reader showed a second list of books with "opening…" in it meanwhile).
  const [openingTitle, setOpeningTitle] = useState<string | null>(null);
  const openingRef = useRef<string | null>(null);
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  // A selection may span several blocks (transcript cues are sentence
  // fragments, so in watch mode it almost always does). `nodes` carries one
  // per-block sub-quote per covered block, whether it came from a native
  // selection, a ctrl-marquee union, or a block sweep.
  const [selection, setSelection] = useState<{
    spanId: string;
    quote: string;
    nodes?: SelectionNode[];
    /** Learner-edited combined passage (capture editor). The nodes keep
     *  anchoring the original blocks; this overrides the exercise surface. */
    editedText?: string;
  } | null>(null);
  const [selectionActions, setSelectionActions] = useState<string[]>([]);
  // Capture editor: the learner can fix OCR mishaps in the captured text
  // before acting on it; edited nodes are flagged so the backend prefers the
  // fixed text as the exercise surface.
  const [editingCapture, setEditingCapture] = useState(false);
  const [railTab, setRailTab] = useState<ReaderRailTab>("guide");
  const [readingSpan, setReadingSpan] = useState<string | null>(null);
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
  // Reading history from before the Reader saved places (usability round 2):
  // where a book with no saved place reopens.
  const [readingHistory, setReadingHistory] = useState<SectionHistory[] | null>(null);
  const historyResumeRef = useRef(false);
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
  const [annotations, setAnnotations] = useState<MarginAnnotation[]>([]);
  const [note, setNote] = useState("");
  const [question, setQuestion] = useState("");
  const [askComposerVersion, setAskComposerVersion] = useState(0);
  const [answerMode, setAnswerMode] = useState<ReaderAnswerMode>("answer_directly");
  const [history, setHistory] = useState<ReaderExchange[]>([]);
  const [collapsedAskIds, setCollapsedAskIds] = useState<Set<string>>(new Set());
  const [askFindOpen, setAskFindOpen] = useState(false);
  const [askFindQuery, setAskFindQuery] = useState("");
  const [disposition, setDisposition] = useState<ReaderDisposition | null>(null);
  const [boundarySkipped, setBoundarySkipped] = useState(false);
  const [boundaryAnswered, setBoundaryAnswered] = useState(false);
  const [boundaryResponse, setBoundaryResponse] = useState("");
  const [boundarySubmitted, setBoundarySubmitted] = useState(false);
  const [mode, setMode] = useState<string>("anchor");
  const [expandedRequests, setExpandedRequests] = useState<Set<string>>(new Set());
  const [questionControl, setQuestionControl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // P3 slice 3: the commitment arc shown immediately after a commit (§10.2), plus a
  // non-blocking formulation coach lint for learner-authored Q+A (§9.2).
  const [arc, setArc] = useState<ReaderArcDto | null>(null);
  // YouTube watch mode: embed + tutor pause points (reader.watch_plan).
  const [watch, setWatch] = useState<ReaderWatchPlanDto | null>(null);
  const [watchLoading, setWatchLoading] = useState(false);
  // Tier-2 embedded PDF: originals-store manifest + which surface is showing.
  const [pdfView, setPdfView] = useState<ReaderPdfViewDto | null>(null);
  // The manifest is still being asked for: the book may open in its original,
  // so it is not read as the text view meanwhile (finish re-review F2). Only
  // the newest request settles it.
  const [pdfViewPending, setPdfViewPending] = useState(false);
  const pdfViewRequestRef = useRef(0);
  const [surface, setSurface] = useState<"pdf" | "text">("pdf");
  // Right-click tag menu (selection or whole-block), on either surface.
  const [tagMenu, setTagMenu] = useState<TagMenuRequest | null>(null);
  const [coach, setCoach] = useState<ReaderCoachLintDto | null>(null);
  const [authoringOpen, setAuthoringOpen] = useState(false);
  const [authoredQuestion, setAuthoredQuestion] = useState("");
  const [authoredAnswer, setAuthoredAnswer] = useState("");
  const [authoredCardId, setAuthoredCardId] = useState<string | null>(null);
  const [authoredStatus, setAuthoredStatus] = useState<AuthoredQuestionStatus | undefined>(undefined);
  const [authoringSpanId, setAuthoringSpanId] = useState<string | null>(null);
  const [authoringQuote, setAuthoringQuote] = useState("");
  const [authoringBusy, setAuthoringBusy] = useState(false);
  // Exact-exercise slice: one background import job per "add exercise to
  // practice" click; the panel survives clearing the selection so the learner
  // can keep reading while it authors.
  const [exerciseImport, setExerciseImport] = useState<{
    batchId: string;
    status: string;
    quote: string;
    result: ReaderExerciseImportResult | null;
    error: string | null;
  } | null>(null);
  // Across-source search on the library screen ("where did I read that?").
  const [librarySearch, setLibrarySearch] = useState("");
  // Enter asks for a deep search (meaning + rewritten question); typing resets it.
  const [searchDeep, setSearchDeep] = useState(false);
  const [searchResults, setSearchResults] = useState<ReaderSourceSearchDto | null>(null);
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  // Inline annotation maintenance (edit note / delete tombstone) in the rail.
  const [editingAnnotationId, setEditingAnnotationId] = useState<string | null>(null);
  const [editingAnnotationText, setEditingAnnotationText] = useState("");
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
  // UX Phase 1 (§6.3): a book whose text is still being prepared opens on its
  // original PDF in PreparingView; the full Reader takes over when it is ready.
  const [preparingCard, setPreparingCard] = useState<SourceLibraryCard | null>(null);
  // Where the learner was in the original when the text became ready: the full
  // Reader opens there, not at the top (review F8).
  const handoffRef = useRef<ReadingPosition | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const railRef = useRef<HTMLDivElement | null>(null);
  const paneRef = useRef<PdfReaderPaneHandle | null>(null);
  const watchRef = useRef<WatchPanelHandle | null>(null);
  const askFindInputRef = useRef<HTMLInputElement | null>(null);
  const askComposerRef = useRef<HTMLTextAreaElement | null>(null);
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
  const modeSaveVersionRef = useRef(0);
  const answerModeSaveVersionRef = useRef(0);
  // Background synthesis is its own lifecycle: the hook keeps global proposal
  // hydration off the two-second status-poll hot path and rejects stale source
  // responses when the learner switches documents.
  const {
    requests,
    proposalCount,
    synthesizedObjects,
    openProposalIds,
    loadError: requestLoadError,
    refresh: refreshRequests,
  } = useReaderRequests(render?.sourceId ?? null, Boolean(render && !offline));

  // Captures commit locally before synthesis is queued. Reopening a real source
  // retries any durable outbox rows left behind by a transient drain failure.
  useEffect(() => {
    if (!render || offline) return;
    let cancelled = false;
    void api.readerDrainOutbox()
      .then((result) => {
        if (cancelled) return;
        if (result.failed.length > 0) {
          onError(`${result.failed.length} saved Reader request${result.failed.length === 1 ? " is" : "s are"} still waiting to start.`);
        }
        // The request hook is already hydrating this source on entry. Re-read
        // only when the drain actually changed (or tried to change) outbox work.
        if (result.drained.length > 0 || result.failed.length > 0) void refreshRequests();
      })
      .catch((error) => {
        if (!cancelled) {
          onError(`Saved Reader requests are still waiting to start: ${errorMessage(error)}`);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [render?.renderViewId, offline, onError, refreshRequests]);

  useEffect(() => {
    if (contractQuery.error) onError(errorMessage(contractQuery.error, "Could not load Reader settings."));
  }, [contractQuery.error, onError]);

  // The rail's content can lose a lot of height in one frame (a quick check is
  // answered and collapses to one line, a card is dismissed, a tab switches).
  // WebKitGTK does not always pull the scroll offset back to the new maximum
  // when that happens: the offset stays where the tall content left it while
  // scrollHeight now reports there is nothing to scroll, so the wheel is dead
  // and the rail is stuck below its own content with no way back up. Clamp the
  // offset ourselves whenever a rail panel changes size.
  useEffect(() => {
    const scroller = railRef.current;
    if (!scroller || typeof ResizeObserver === "undefined") return;
    const clamp = () => {
      const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
      if (scroller.scrollTop > max) scroller.scrollTop = max;
    };
    const observer = new ResizeObserver(clamp);
    // The rail's direct children (sticky header + one div per tab) are static
    // for the life of an open source, so observing them once covers every
    // panel's growth and collapse.
    for (const child of Array.from(scroller.children)) observer.observe(child);
    return () => observer.disconnect();
  }, [render]);

  // Debounced across-source search (library screen only; deterministic, local).
  useEffect(() => {
    if (render || sidecarDown) return;
    const query = librarySearch.trim();
    if (query.length < 2) {
      setSearchResults(null);
      setSearchBusy(false);
      setSearchError(null);
      return;
    }
    let cancelled = false;
    setSearchBusy(true);
    setSearchError(null);
    const timer = window.setTimeout(() => {
      api
        .readerSearchSources({ query, deep: searchDeep })
        .then((result) => {
          if (!cancelled) setSearchResults(result);
        })
        .catch((error) => {
          if (!cancelled) {
            setSearchResults(null);
            setSearchError(errorMessage(error, "Could not search the source library."));
          }
        })
        .finally(() => {
          if (!cancelled) setSearchBusy(false);
        });
    }, searchDeep ? 0 : 300);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [librarySearch, searchDeep, render, sidecarDown]);

  useEffect(() => {
    try {
      window.localStorage.setItem("learnloop.reader.section-prompts", sectionPromptsEnabled ? "on" : "off");
    } catch {
      /* A denied storage write should not interrupt reading. */
    }
  }, [sectionPromptsEnabled]);

  // Reset per-source panel state so nothing from the previous source leaks over.
  const resetSourceState = useCallback(() => {
    // Leaving a book for another (or for the Library) saves what was read in
    // it first, as closing the Reader does (round-2 review F3). Its entry
    // stays: a save still failing is retried with its newest counts (F7).
    if (activeSeenRef.current) sendSeenCounts(seenSavesRef.current, activeSeenRef.current);
    activeSeenRef.current = null;
    setGuidePlan(null);
    setGuideLoading(false);
    setActiveSpan(null);
    setReadingSpan(null);
    setReadingOffset(null);
    setSectionSeen({});
    lastReadRef.current = null;
    setFocusQuickCheck(null);
    setHiddenPdfOffers([]);
    setReadingMoved(false);
    userScrollAtRef.current = 0;
    lastPlaybackSpanRef.current = null;
    setReadingHistory(null);
    historyResumeRef.current = false;
    setAnsweredSections([]);
    setSelection(null);
    setSelectionActions([]);
    setRailTab("guide");
    setRevealedSections([]);
    setDismissedSections([]);
    setCompletedSections([]);
    setAnnotations([]);
    setNote("");
    setQuestion("");
    setAskComposerVersion(0);
    setHistory([]);
    setCollapsedAskIds(new Set());
    setAskFindOpen(false);
    setAskFindQuery("");
    setDisposition(null);
    setBoundarySkipped(false);
    setBoundaryAnswered(false);
    setBoundaryResponse("");
    setBoundarySubmitted(false);
    setExpandedRequests(new Set());
    setQuestionControl(null);
    setArc(null);
    setCoach(null);
    setAuthoringOpen(false);
    setAuthoredQuestion("");
    setAuthoredAnswer("");
    setAuthoredCardId(null);
    setAuthoringSpanId(null);
    setAuthoringQuote("");
    setAuthoringBusy(false);
    setWatch(null);
    setWatchLoading(false);
    setPdfView(null);
    setPdfViewPending(false);
    pdfViewRequestRef.current += 1;
    setSurface("pdf");
    setTagMenu(null);
    setAuthoringSections([]);
    setTimedOutSections([]);
    authorRequestedRef.current = new Set();
    setStickyQuestionSections([]);
    setEditingAnnotationId(null);
    setEditingAnnotationText("");
  }, []);

  const openSource = useCallback(
    async (card: SourceLibraryCard, jumpSpan?: string, handoff?: ReadingPosition | null) => {
      handoffRef.current = handoff ?? null;
      if (card.readiness !== "ready") {
        // Nothing to render yet: show the original while LearnLoop prepares it.
        resetSourceState();
        setRender(null);
        setPreparingCard(card);
        onSourceChange?.({ card, spanId: null });
        return;
      }
      // A book handed over from the preparing view keeps its original on screen
      // until the full Reader is ready (usability round 2: a list of books
      // with "opening…" flashed in between).
      openingRef.current = card.sourceId;
      setOpening(card.sourceId);
      setOpeningTitle(card.title);
      try {
        // reader.render_view resolves a source id to its latest completed extraction.
        const view = await cachedSourceRead(card.sourceId, ["reader_render_view", card.sourceId], () =>
          api.readerRenderView({ extractionId: card.sourceId })
        );
        resetSourceState();
        setPreparingCard(null);
        // Opening restores a position: following starts once it has settled.
        settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
        setRender(view);
        setOffline(false);
        setSourceTitle(card.title);
        // The shell remembers the SOURCE, not the jump: a search hit lands the
        // learner on the passage once; returning to this tab later resumes
        // from the saved reading position, not the original hit.
        onSourceChange?.({ card, spanId: null });
        let placed = Boolean(handoff);
        try {
          const savedSpan = window.localStorage.getItem(readingPositionKey(view.sourceId));
          if (savedSpan) {
            setReadingSpan(savedSpan);
            setActiveSpan(savedSpan);
            placed = true;
          }
        } catch {
          /* Reading still works when storage is unavailable. */
        }
        // A search hit overrides the resume position: the learner asked to land
        // on the matching passage, not where they left off.
        if (jumpSpan) {
          setReadingSpan(jumpSpan);
          setActiveSpan(jumpSpan);
          placed = true;
        }
        // No saved place: the reading history decides, once it is read (below).
        historyResumeRef.current = !placed;
        setGuideLoading(true);
        readGuidePlan(card.sourceId, view.extractionId)
          .then(setGuidePlan)
          .catch(() => setGuidePlan(null))
          .finally(() => setGuideLoading(false));
        // Hydrate durable reading progress so reveal/completion survive restarts.
        cachedSourceRead(card.sourceId, ["reader_get_progress", view.extractionId], () =>
          api.readerGetProgress({ extractionId: view.extractionId })
        )
          .then((progress) => {
            // How far each section was read survives a restart (usability round 1, U3).
            const seen: Record<string, number> = {};
            for (const row of progress.sections) if (row.spansSeen > 0) seen[row.sectionId] = row.spansSeen;
            const acknowledged = seenSaveFor(seenSavesRef.current, view.extractionId).acknowledged;
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
          })
          .catch(() => undefined);
        if (youtubeVideoId(card.canonicalUri ?? "") !== null) {
          setWatchLoading(true);
          cachedSourceRead(card.sourceId, ["reader_watch_plan", card.sourceId], () => api.readerWatchPlan(card.sourceId))
            .then(setWatch)
            .catch(() => setWatch(null))
            .finally(() => setWatchLoading(false));
        } else {
          // Original-PDF surface when the originals store has this revision's bytes.
          const pdfRequest = ++pdfViewRequestRef.current;
          const current = () => pdfViewRequestRef.current === pdfRequest;
          setPdfViewPending(true);
          cachedSourceRead(card.sourceId, ["reader_pdf_view", card.sourceId], () =>
            api.readerPdfView({ extractionId: card.sourceId })
          )
            .then((manifest) => {
              if (current()) setPdfView(manifest.available ? manifest : null);
            })
            .catch(() => {
              if (current()) setPdfView(null);
            })
            .finally(() => {
              if (current()) setPdfViewPending(false);
            });
        }
      } catch (error) {
        setPreparingCard(null);
        onError(errorMessage(error));
        // A source that no longer opens (deleted, re-extracted away) must not
        // be resumed on every return to this tab.
        onSourceChange?.(null);
      } finally {
        openingRef.current = null;
        setOpening(null);
        setOpeningTitle(null);
      }
    },
    [onError, onSourceChange, resetSourceState],
  );

  const openFixture = useCallback(() => {
    resetSourceState();
    setRender(readerRenderViewFixture);
    setOffline(true);
    setSourceTitle("demo chapter (fixture)");
    onSourceChange?.(null);
  }, [onSourceChange, resetSourceState]);

  const backToLibrary = useCallback(() => {
    resetSourceState();
    setPreparingCard(null);
    setRender(null);
    setOffline(false);
    setSourceTitle(null);
    onSourceChange?.(null);
  }, [onSourceChange, resetSourceState]);

  // Resume the source that was open when this tab was last left: the shell
  // keeps the card, the cache keeps the reads, so the return is instant.
  const resumedRef = useRef(false);
  useEffect(() => {
    if (resumedRef.current || !initialSource || render) return;
    resumedRef.current = true;
    void openSource(initialSource.card, initialSource.spanId ?? undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // While the contract loads the Reader reads as enabled (new libraries have it
  // on); the "disabled" notice shows only once the config really says so
  // (UX Phase 1, §10 item 1.10: no flash of a config instruction on every open).
  const enabled = contract?.readerEnabled ?? true;
  const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled;

  // Reader Ask answers already live durably in interaction_events. Rehydrate
  // them whenever a source opens so changing tabs, reopening the source, or
  // restarting the app cannot erase the conversation.
  useEffect(() => {
    if (!render || offline) return;
    let cancelled = false;
    void cachedSourceRead(render.sourceId, ["reader_ask_history", render.extractionId], () =>
      api.readerAskHistory(render.extractionId)
    )
      .then((result) => {
        if (cancelled) return;
        const restored: ReaderExchange[] = result.exchanges.map((exchange) => ({
          id: exchange.eventId,
          spanId: exchange.spanId,
          question: exchange.questionMd,
          answerMd: exchange.answerMd,
          answerMode: exchange.answerMode,
          createdAt: exchange.createdAt,
        }));
        setHistory((current) => {
          const live = new Map(current.map((exchange) => [exchange.id, exchange]));
          for (const exchange of restored) if (!live.has(exchange.id)) live.set(exchange.id, exchange);
          return [...live.values()].sort((a, b) => (b.createdAt ?? "").localeCompare(a.createdAt ?? ""));
        });
        setCollapsedAskIds((ids) => new Set([...ids, ...restored.map((exchange) => exchange.id)]));
      })
      .catch(() => {
        /* Ask remains usable when history hydration is temporarily unavailable. */
      });
    return () => {
      cancelled = true;
    };
  }, [render, offline]);

  const blocks: ReaderRenderBlockDto[] = useMemo(
    () => (render?.blocks ?? []).filter((b) => !FURNITURE_BLOCK_TYPES.has(b.blockType ?? "")),
    [render],
  );
  const activeBlock = useMemo(() => blocks.find((block) => block.spanId === activeSpan) ?? null, [blocks, activeSpan]);

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

  // Durable annotation trails for the PDF surface: one painted region per
  // anchored segment with geometry. needs_reanchor is shown in the rail only —
  // a region we can no longer vouch for is never painted (no false attachment).
  const trails: AnnotationTrail[] = useMemo(() => {
    const list: AnnotationTrail[] = [];
    for (const a of annotations) {
      if (a.status === "needs_reanchor") continue;
      for (const s of a.segments) {
        if (s.page !== null && s.bbox && s.bbox.length === 4) {
          list.push({ annotationId: a.annotationId, kind: a.kind, spanId: s.spanId, page: s.page, bbox: s.bbox });
        }
      }
    }
    return list;
  }, [annotations]);
  const annotatedSpans = useMemo(
    () => new Set(annotations.filter((a) => a.status !== "needs_reanchor").flatMap((a) => a.segments.map((s) => s.spanId))),
    [annotations],
  );
  const boundaryBlock = useMemo(() => blocks.find((b) => (b.blockType ?? "") !== "Section") ?? null, [blocks]);

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
  const atSectionBreak = useMemo(() => {
    if (!currentGuideSection || !readingMoved) return false;
    const here = pageBySpan.get(readingSpan ?? activeSpan ?? "");
    const last = pageBySpan.get(currentGuideSection.endSpanId);
    if (here === undefined || last === undefined) return currentSectionProgress >= 0.7;
    return here >= last;
  }, [currentGuideSection, readingMoved, pageBySpan, readingSpan, activeSpan, currentSectionProgress]);
  const currentQuestionDue = useMemo(() => {
    const question = currentGuideSection?.question;
    const phase = question?.readingPhase;
    if (!phase || pdfSurfaceLoading) return false;
    if (phase === "before_section") {
      const firstSpan = 1 / Math.max(1, currentGuideSection?.spanIds.length ?? 1);
      return currentSectionProgress <= Math.max(0.3, firstSpan);
    }
    if (phase === "during_section") return currentSectionProgress >= 0.45;
    if (pdfSurfaceActive) return atSectionBreak;
    return currentSectionProgress >= 0.7;
  }, [currentGuideSection, currentSectionProgress, pdfSurfaceActive, pdfSurfaceLoading, atSectionBreak]);

  // Pin a question the moment it becomes due; it stays pinned (and rendered)
  // until answered or dismissed, however far playback or scrolling moves on.
  useEffect(() => {
    if (!boundaryChecksAvailable || !currentGuideSection?.question || !currentQuestionDue) return;
    const sectionId = currentGuideSection.id;
    if (dismissedSections.includes(sectionId) || completedSections.includes(sectionId)) return;
    setStickyQuestionSections((ids) => (ids.includes(sectionId) ? ids : [...ids, sectionId]));
  }, [boundaryChecksAvailable, currentGuideSection, currentQuestionDue, dismissedSections, completedSections]);

  // A quick check is open once it has been *earned*, not only while the
  // learner stands in its section: pinned when due (above), or already behind
  // the reading position, or auto-authored — the producer only writes those
  // after ~60% of the section, so their phase gate is spent by construction.
  // Without the latter two, a video (one IR unit for the whole transcript, so
  // one 200+ span section) counted a check in the rail badge that the Guide
  // tab refused to render until 70% of playback; passed-over sections in a PDF
  // failed the same way. The rail badge counts exactly what the tab renders.
  const openQuestionSections = useMemo(() => {
    const sections = guidePlan?.sections ?? [];
    const currentIndex = sections.findIndex((section) => section.id === currentGuideSection?.id);
    return sections.filter(
      (section, index) =>
        section.question !== null
        && !dismissedSections.includes(section.id)
        && !completedSections.includes(section.id)
        && (
          // In the original PDF the section being read waits for its break
          // (it is pinned from then on, below); elsewhere a written check is
          // open at once, as before.
          (section.question.placement === "auto_authored" && ((!pdfSurfaceActive && !pdfSurfaceLoading) || index !== currentIndex))
          || stickyQuestionSections.includes(section.id)
          || (currentIndex >= 0 && index < currentIndex)
        ),
    );
  }, [stickyQuestionSections, guidePlan, currentGuideSection, dismissedSections, completedSections, pdfSurfaceActive, pdfSurfaceLoading]);
  // A check the learner answered is not waiting any more, though its card
  // stays open to compare (usability round 2).
  const pendingQuickCheckCount = boundaryChecksAvailable
    ? openQuestionSections.filter((section) => !answeredSections.includes(section.id)).length
    : 0;
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

  useEffect(() => {
    if (!render || offline || !readingSpan) return;
    try {
      window.localStorage.setItem(readingPositionKey(render.sourceId), readingSpan);
    } catch {
      /* Reading-position persistence is best-effort. */
    }
  }, [render, offline, readingSpan]);

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
    setRailTab("guide");
    setStickyQuestionSections((ids) => (ids.includes(sectionId) ? ids : [...ids, sectionId]));
    setHiddenPdfOffers((ids) => (ids.includes(sectionId) ? ids : [...ids, sectionId]));
    setFocusQuickCheck(sectionId);
  }, []);
  useEffect(() => {
    if (!focusQuickCheck) return;
    const frame = window.requestAnimationFrame(() => {
      const card = railRef.current?.querySelector(`[data-quick-check="${focusQuickCheck}"]`);
      if (card instanceof HTMLElement) card.scrollIntoView({ block: "nearest" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [focusQuickCheck]);

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
  }, [render, offline, authoringSections.length]);

  // A "Revisit this to resolve" reason names the error type until the
  // attempt's diagnosis lands; re-read the plan while it waits on one so the
  // Guide names the diagnoser's statement without a reopen. Like the
  // authoring poll, a refresh never blanks a complete Guide.
  const refreshGuidePlan = useCallback((plan: ReaderGuidePlanDto) => {
    setGuidePlan((current) => (current && current.sections.length > 0 && plan.sections.length === 0 ? current : plan));
  }, []);
  useGuideDiagnosisRefresh(render && !offline ? render : null, guidePlan, refreshGuidePlan);

  const revealedPassages = useMemo(() => {
    const revealed = new Set(revealedSections);
    const map = new Map<string, { section: ReaderGuideSectionDto; reason: string }>();
    for (const section of guidePlan?.sections ?? []) {
      if (!revealed.has(section.id)) continue;
      for (const passage of section.suggestedPassages) {
        if (!annotatedSpans.has(passage.spanId)) map.set(passage.spanId, { section, reason: passage.reason });
      }
    }
    return map;
  }, [guidePlan, revealedSections, annotatedSpans]);
  const revealedGuidanceSpans = useMemo(() => new Set(revealedPassages.keys()), [revealedPassages]);

  // Blocks of the committed selection, painted in the PDF pane until cleared.
  const selectedSpanSet = useMemo(
    () => new Set((selection ? selectionNodes(selection) : []).map((node) => node.spanId)),
    [selection],
  );

  // Rewrite the captured passage as one combined text (OCR fix). The per-block
  // nodes stay untouched — they keep anchoring the original blocks — while the
  // edited passage overrides the exercise surface.
  const editCaptureText = useCallback((text: string) => {
    setSelection((sel) => (sel ? { ...sel, editedText: text } : sel));
  }, []);
  const resetCaptureText = useCallback(() => {
    setSelection((sel) => {
      if (!sel) return sel;
      const { editedText: _dropped, ...rest } = sel;
      return rest;
    });
  }, []);

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
  }, []);

  const onReadingScroll = useCallback(() => {
    const now = Date.now();
    if (now >= settleUntilRef.current && now - userScrollAtRef.current < USER_SCROLL_MS) setReadingMoved(true);
    if (readingRafRef.current !== null) return;
    readingRafRef.current = window.requestAnimationFrame(() => {
      readingRafRef.current = null;
      updateReadingPosition();
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

  const refreshAnnotations = useCallback(async () => {
    if (!render || offline) return;
    try {
      const result = await cachedSourceRead(render.sourceId, ["reader_source_annotations", render.sourceId], () =>
        api.readerSourceAnnotations({ sourceId: render.sourceId })
      );
      const rows = (result.annotations as Array<Record<string, unknown>>) ?? [];
      setAnnotations(
        rows.map((r) => {
          const version = (r.version as Record<string, unknown>) ?? {};
          const segments = (r.segments as Array<Record<string, unknown>>) ?? [];
          const anchor = (r.anchor as Record<string, unknown>) ?? {};
          const annotation = (r.annotation as Record<string, unknown>) ?? {};
          return {
            annotationId: (annotation.id as string) ?? null,
            quote: (segments[0]?.exactQuote as string) ?? "",
            status: (anchor.status as string) ?? null,
            learnerText: (version.learnerText as string) ?? "",
            kind: (version.annotationType as string) ?? "highlight",
            segments: segments.map((s) => {
              // geometry_json rides as a JSON string: {"page": n, "bbox": [x0,y0,x1,y1]}.
              let page: number | null = null;
              let bbox: number[] | null = null;
              try {
                const geometry = s.geometryJson ? (JSON.parse(String(s.geometryJson)) as { page?: number; bbox?: number[] }) : null;
                page = typeof geometry?.page === "number" ? geometry.page : null;
                bbox = Array.isArray(geometry?.bbox) ? geometry.bbox : null;
              } catch {
                /* geometry-less segment stays rail-only */
              }
              return { spanId: String(s.spanId ?? ""), page, bbox };
            }),
          };
        }),
      );
    } catch {
      /* keep local receipts */
    }
  }, [render, offline]);

  useEffect(() => {
    void refreshAnnotations();
  }, [refreshAnnotations]);

  const saveAnnotationEdit = useCallback(async () => {
    if (!editingAnnotationId) return;
    setBusy(true);
    try {
      await api.readerEditAnnotation({ annotationId: editingAnnotationId, learnerText: editingAnnotationText });
      setAnnotations((list) =>
        list.map((a) => (a.annotationId === editingAnnotationId ? { ...a, learnerText: editingAnnotationText } : a)),
      );
      setEditingAnnotationId(null);
      setEditingAnnotationText("");
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [editingAnnotationId, editingAnnotationText, onError, refreshAnnotations]);

  // needs_reanchor repair: re-run deterministic anchoring onto the current
  // extraction; if that still fails, the learner can hand-pick a passage
  // (manual anchor, §4.4) via the current selection.
  const [reanchorNotes, setReanchorNotes] = useState<Record<string, string>>({});
  const reanchorAnnotation = useCallback(async (annotationId: string) => {
    if (!render) return;
    setBusy(true);
    try {
      const result = await api.readerReanchor({ annotationId, newExtractionId: render.extractionId });
      if (result.status === "needs_reanchor") {
        setReanchorNotes((notes) => ({
          ...notes,
          [annotationId]: "couldn’t re-anchor automatically — select the passage in the text, then use “anchor to selection”.",
        }));
      } else {
        setReanchorNotes((notes) => ({ ...notes, [annotationId]: "✓ re-anchored." }));
      }
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [render, onError, refreshAnnotations]);

  const manualAnchorToSelection = useCallback(async (annotationId: string) => {
    if (!render || !selection) return;
    setBusy(true);
    try {
      await api.readerManualAnchor({
        annotationId,
        extractionId: render.extractionId,
        rawSelection: { nodes: selectionNodes(selection) },
        renderViewId: render.renderViewId,
      });
      setReanchorNotes((notes) => ({ ...notes, [annotationId]: "✓ anchored to your selection." }));
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [render, selection, onError, refreshAnnotations]);

  // Deletion is a tombstone disposition event server-side (§4.1) — history is
  // kept; the listing honors the intent, so the card leaves the rail.
  const deleteAnnotation = useCallback(async (annotationId: string) => {
    setBusy(true);
    try {
      await api.readerDeleteIntentAnnotation({ annotationId });
      setAnnotations((list) => list.filter((a) => a.annotationId !== annotationId));
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [onError, refreshAnnotations]);

  // Split the live selection into one sub-quote per covered [data-span-id]
  // block, in document order. Anchoring works per block, so a quote must never
  // cross a block boundary — the old single-anchor capture silently failed on
  // any multi-block selection (every transcript selection, in practice).
  const collectSelectionNodes = useCallback((): Array<{ spanId: string; quote: string }> => {
    const sel = window.getSelection();
    const container = bodyRef.current;
    if (!sel || sel.isCollapsed || sel.rangeCount === 0 || !container) return [];
    const range = sel.getRangeAt(0);
    const nodes: Array<{ spanId: string; quote: string }> = [];
    const seen = new Set<string>();
    for (const el of Array.from(container.querySelectorAll<HTMLElement>("[data-span-id]"))) {
      const spanId = el.dataset.spanId;
      if (!spanId || seen.has(spanId)) continue;
      let intersects = false;
      try {
        intersects = range.intersectsNode(el);
      } catch {
        continue;
      }
      if (!intersects) continue;
      const sub = document.createRange();
      sub.selectNodeContents(el);
      if (sub.compareBoundaryPoints(Range.START_TO_START, range) < 0) {
        sub.setStart(range.startContainer, range.startOffset);
      }
      if (sub.compareBoundaryPoints(Range.END_TO_END, range) > 0) {
        sub.setEnd(range.endContainer, range.endOffset);
      }
      const quote = sub.toString().replace(/\s+/g, " ").trim();
      if (quote) {
        seen.add(spanId);
        nodes.push({ spanId, quote });
      }
    }
    return nodes;
  }, []);

  const onMouseUp = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const quote = sel.toString().replace(/\s+/g, " ").trim();
    if (!quote) return;
    const nodes = collectSelectionNodes();
    if (!nodes.length) return;
    // A fresh native selection replaces any marquee boxes still painted.
    if (domBoxesRef.current.length) {
      domBoxesRef.current = [];
      setDomBoxes([]);
    }
    setSelection({ spanId: nodes[0].spanId, quote, nodes });
    setSelectionActions([]);
    setEditingCapture(false);
    setActiveSpan(nodes[0].spanId);
    // A selection updates Ask's grounding too. Do not unexpectedly hide an Ask
    // conversation; Guide still yields to Capture so a first-time selection
    // exposes the annotation actions.
    setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
  }, [collectSelectionNodes]);

  // ---- ctrl-marquee union capture (markdown + transcript surfaces) --------
  // Hold ctrl (or cmd) and drag any number of boxes over the reading column;
  // releasing ctrl commits their union as one selection — the same gesture the
  // PDF pane implements page-anchored. Boxes live in bodyRef content
  // coordinates so they scroll with the text; words are clipped per box
  // against each [data-span-id] block. Escape cancels.
  const [domBoxes, setDomBoxes] = useState<number[][]>([]);
  const [domDraft, setDomDraft] = useState<number[] | null>(null);
  const [domArmed, setDomArmed] = useState(false);
  const domBoxesRef = useRef<number[][]>([]);
  const domDragRef = useRef<{ x0: number; y0: number } | null>(null);

  const domPointFromClient = useCallback((clientX: number, clientY: number): [number, number] | null => {
    const host = bodyRef.current;
    if (!host) return null;
    const rect = host.getBoundingClientRect();
    return [clientX - rect.left + host.scrollLeft, clientY - rect.top + host.scrollTop];
  }, []);

  const onBodyMouseDown = useCallback(
    (event: React.MouseEvent) => {
      if (pdfSurfaceActive) return; // the PDF pane runs its own page-anchored marquee
      if (event.button !== 0 || !(event.ctrlKey || event.metaKey)) return;
      const target = event.target as Node;
      if (target instanceof HTMLElement && target.closest("button, input, textarea, select, a, iframe")) return;
      const point = domPointFromClient(event.clientX, event.clientY);
      if (!point) return;
      // The marquee owns this drag — no native selection underneath.
      event.preventDefault();
      window.getSelection()?.removeAllRanges();
      setDomArmed(true);
      domDragRef.current = { x0: point[0], y0: point[1] };
      setDomDraft([point[0], point[1], point[0], point[1]]);
    },
    [pdfSurfaceActive, domPointFromClient],
  );

  const domDrafting = domDraft !== null;
  useEffect(() => {
    if (!domDrafting) return;
    const rectFrom = (drag: { x0: number; y0: number }, point: [number, number]): number[] => [
      Math.min(drag.x0, point[0]),
      Math.min(drag.y0, point[1]),
      Math.max(drag.x0, point[0]),
      Math.max(drag.y0, point[1]),
    ];
    const onMove = (event: MouseEvent) => {
      const drag = domDragRef.current;
      if (!drag) return;
      const point = domPointFromClient(event.clientX, event.clientY);
      if (point) setDomDraft(rectFrom(drag, point));
    };
    const onUp = (event: MouseEvent) => {
      const drag = domDragRef.current;
      domDragRef.current = null;
      setDomDraft(null);
      if (!drag) return;
      const point = domPointFromClient(event.clientX, event.clientY);
      if (!point) return;
      const rect = rectFrom(drag, point);
      // A bare ctrl+click is not a box.
      if (rect[2] - rect[0] < 6 || rect[3] - rect[1] < 6) return;
      const next = [...domBoxesRef.current, rect];
      domBoxesRef.current = next;
      setDomBoxes(next);
      // Ctrl already released mid-drag: this box completes the gesture.
      if (!(event.ctrlKey || event.metaKey)) commitDomBoxesRef.current();
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [domDrafting, domPointFromClient]);

  // Boxes → per-block nodes: word-level clipping against every [data-span-id]
  // block (markdown paragraphs, transcript cues), in document order. Hidden
  // text (KaTeX MathML mirrors) drops out via the zero-rect filter.
  const resolveDomBoxes = useCallback((boxes: number[][]): Array<{ spanId: string; quote: string }> => {
    const host = bodyRef.current;
    if (!host || !boxes.length) return [];
    const hostRect = host.getBoundingClientRect();
    const clientBoxes = boxes.map((b) => [
      b[0] + hostRect.left - host.scrollLeft,
      b[1] + hostRect.top - host.scrollTop,
      b[2] + hostRect.left - host.scrollLeft,
      b[3] + hostRect.top - host.scrollTop,
    ]);
    const nodes: Array<{ spanId: string; quote: string }> = [];
    const seen = new Set<string>();
    for (const el of Array.from(host.querySelectorAll<HTMLElement>("[data-span-id]"))) {
      const spanId = el.dataset.spanId;
      if (!spanId || seen.has(spanId)) continue;
      const elRect = el.getBoundingClientRect();
      const touches = clientBoxes.some(
        (b) => b[0] < elRect.right && b[2] > elRect.left && b[1] < elRect.bottom && b[3] > elRect.top,
      );
      if (!touches) continue;
      const words: string[] = [];
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const text = node as Text;
        const wordPattern = /\S+/g;
        let match: RegExpExecArray | null;
        while ((match = wordPattern.exec(text.data))) {
          const range = document.createRange();
          range.setStart(text, match.index);
          range.setEnd(text, match.index + match[0].length);
          const rects = Array.from(range.getClientRects()).filter((r) => r.width > 0.5 && r.height > 0.5);
          if (!rects.length) continue;
          const cx = (Math.min(...rects.map((r) => r.left)) + Math.max(...rects.map((r) => r.right))) / 2;
          const cy = (Math.min(...rects.map((r) => r.top)) + Math.max(...rects.map((r) => r.bottom))) / 2;
          if (clientBoxes.some((b) => cx >= b[0] && cx <= b[2] && cy >= b[1] && cy <= b[3])) words.push(match[0]);
        }
      }
      const quote = words.join(" ").replace(/\s+/g, " ").trim();
      if (quote) {
        seen.add(spanId);
        nodes.push({ spanId, quote });
      }
    }
    return nodes;
  }, []);

  const commitDomBoxes = useCallback(() => {
    const boxes = domBoxesRef.current;
    if (!boxes.length) return;
    const nodes = resolveDomBoxes(boxes);
    if (!nodes.length) {
      domBoxesRef.current = [];
      setDomBoxes([]);
      return;
    }
    const quote = nodes.map((n) => n.quote).join(" ");
    setSelection({ spanId: nodes[0].spanId, quote, nodes });
    setSelectionActions([]);
    setEditingCapture(false);
    setActiveSpan(nodes[0].spanId);
    setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
  }, [resolveDomBoxes]);
  const commitDomBoxesRef = useRef(commitDomBoxes);
  useEffect(() => {
    commitDomBoxesRef.current = commitDomBoxes;
  }, [commitDomBoxes]);

  // Releasing ctrl commits the union; Escape abandons it. Armed state drives
  // the crosshair affordance while ctrl/cmd is down.
  useEffect(() => {
    const clearDomBoxes = () => {
      domDragRef.current = null;
      domBoxesRef.current = [];
      setDomDraft(null);
      setDomBoxes([]);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Control" || event.key === "Meta") setDomArmed(true);
      if (event.key === "Escape" && (domBoxesRef.current.length || domDragRef.current)) clearDomBoxes();
    };
    const onKeyUp = (event: KeyboardEvent) => {
      if (event.key !== "Control" && event.key !== "Meta") return;
      setDomArmed(false);
      // A drag still in flight commits from its own mouseup instead.
      if (!domDragRef.current) commitDomBoxesRef.current();
    };
    const onBlur = () => setDomArmed(false);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", onBlur);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      window.removeEventListener("blur", onBlur);
    };
  }, []);

  // The capture was cleared — drop the painted boxes with it.
  useEffect(() => {
    if (selection === null && domBoxesRef.current.length) {
      domBoxesRef.current = [];
      setDomBoxes([]);
    }
  }, [selection]);

  // The text/transcript marquee also has no native DOM selection after commit.
  // A context click inside its retained union targets the complete committed
  // selection, matching the PDF surface's right-click semantics.
  const openDomTagMenu = useCallback(
    (request: TagMenuRequest) => {
      const point = domPointFromClient(request.x, request.y);
      const insideCommittedBox = point !== null && domBoxesRef.current.some(
        (box) =>
          point[0] >= box[0] &&
          point[0] <= box[2] &&
          point[1] >= box[1] &&
          point[1] <= box[3],
      );
      if (!pdfSurfaceActive && selection && insideCommittedBox) {
        setTagMenu({
          ...request,
          spanId: selection.spanId,
          quote: selection.quote,
          nodes: selectionNodes(selection),
        });
        return;
      }
      setTagMenu(request);
    },
    [domPointFromClient, pdfSurfaceActive, selection],
  );

  const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject") => {
    setBusy(true);
    try {
      if (decision === "accept") await api.readerAcceptProposal(proposalId);
      else await api.readerRejectProposal(proposalId);
      void refreshRequests();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [onError, refreshRequests]);

  const retryRequest = useCallback(async (requestId: string) => {
    try {
      await api.readerRetryRequest(requestId);
      void refreshRequests();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [onError, refreshRequests]);

  // Optimistic segment for a just-captured annotation: geometry from the pdf
  // manifest (when open) makes the trail paint immediately; the authoritative
  // segments arrive with the next refreshAnnotations.
  const optimisticSegments = useCallback(
    (spanIds: string | string[]): AnnotationSegment[] => {
      const ids = Array.isArray(spanIds) ? spanIds : [spanIds];
      return ids.map((spanId) => {
        const geometry = pdfView?.blocks.find((b) => b.spanId === spanId);
        return { spanId, page: geometry?.page ?? null, bbox: geometry?.bbox ?? null };
      });
    },
    [pdfView],
  );

  // Right-click tag: one plain capture. A selection tags its quote; a bare
  // right-click tags the whole block (server-side offset clamping turns
  // start=0/end=huge into the full block text).
  const tagCapture = useCallback(
    async (action: string, target: TagMenuRequest) => {
      setTagMenu(null);
      if (!render) return;
      const displayQuote = target.quote ?? WHOLE_BLOCK_QUOTE;
      // A quoted tag re-splits the live selection per block (it may span many
      // transcript cues). PDF native/marquee selections already carry their
      // resolved nodes because a committed marquee has no DOM Selection.
      // A bare right-click tags the whole single block.
      const quotedNodes = (() => {
        if (target.quote === null) return null;
        if (target.nodes?.length) return target.nodes;
        const multi = collectSelectionNodes();
        return multi.length ? multi : [{ spanId: target.spanId, quote: target.quote }];
      })();
      const optimisticIds = quotedNodes ? quotedNodes.map((n) => n.spanId) : [target.spanId];
      if (offline) {
        setAnnotations((a) => [
          { annotationId: null, quote: displayQuote, status: "exact", learnerText: "", kind: action, segments: optimisticSegments(optimisticIds) },
          ...a,
        ]);
        return;
      }
      setBusy(true);
      try {
        const nodes = quotedNodes ?? [{ spanId: target.spanId, start: 0, end: 1_000_000 }];
        const receipt = await api.readerCapture({
          sourceId: render.sourceId,
          revisionId: render.revisionId,
          extractionId: render.extractionId,
          action,
          clientIdempotencyKey: newKey(),
          renderViewId: render.renderViewId,
          rawSelection: { nodes },
          learnerText: "",
        });
        setAnnotations((a) => [
          { annotationId: receipt.annotationId, quote: displayQuote, status: receipt.anchorStatus ?? "exact", learnerText: "", kind: action, segments: optimisticSegments(optimisticIds) },
          ...a,
        ]);
        setActiveSpan(target.spanId);
        void refreshAnnotations();
      } catch (error) {
        onError(errorMessage(error));
      } finally {
        setBusy(false);
      }
    },
    [render, offline, onError, refreshAnnotations, optimisticSegments, collectSelectionNodes],
  );

  useEffect(() => {
    if (!tagMenu) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") setTagMenu(null);
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [tagMenu]);

  // A single Alt press is the quick "clear capture" gesture. It also composes
  // with Alt+drag block sweeping: the key press clears the old capture first,
  // then the drag commits its replacement on mouse-up.
  const clearSelection = useCallback(() => {
    setSelection(null);
    setSelectionActions([]);
    setEditingCapture(false);
    setTagMenu(null);
    window.getSelection()?.removeAllRanges();
  }, []);
  useEffect(() => {
    const onAltClear = (event: KeyboardEvent) => {
      if (event.key !== "Alt" || event.repeat) return;
      const target = event.target;
      if (
        target instanceof HTMLElement &&
        (target.isContentEditable || target.closest("input, textarea, select"))
      ) return;
      clearSelection();
    };
    window.addEventListener("keydown", onAltClear, true);
    return () => window.removeEventListener("keydown", onAltClear, true);
  }, [clearSelection]);

  // Rail card click → jump to the annotation on the current surface: the PDF
  // pane scrolls to its page/block; the text surface scrolls to its block.
  const jumpToAnnotation = useCallback(
    (a: MarginAnnotation) => {
      const segment = a.segments.find((s) => s.page !== null) ?? a.segments[0];
      if (!segment) return;
      setActiveSpan(segment.spanId);
      if (pdfView && surface === "pdf" && !offline && segment.page !== null) {
        paneRef.current?.scrollToSegment(segment.page, segment.spanId);
        return;
      }
      const el = bodyRef.current?.querySelector(`[data-span-id="${segment.spanId}"]`);
      // (Optional call: a jump made before layout, as the reading-history resume
      // can be, must not throw where scrolling is unavailable.)
      if (el instanceof HTMLElement) el.scrollIntoView?.({ behavior: "smooth", block: "center" });
    },
    [pdfView, surface, offline],
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
  }, []);

  const jumpToSpan = useCallback(
    (spanId: string, align: PassageAlign = "center") => {
      // A jump is not reading: the sections it passes are not ticked, and
      // nothing is asked about where it lands until the learner reads on.
      settleUntilRef.current = Date.now() + SEEN_SETTLE_MS;
      setReadingMoved(false);
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
      // (Optional call: a jump made before layout, as the reading-history resume
      // can be, must not throw where scrolling is unavailable.)
      if (el instanceof HTMLElement) el.scrollIntoView?.({ behavior: "smooth", block: "center" });
    },
    [pdfView, surface, offline, pageOfSpan, revealSegment],
  );

  // A book with no saved place but reading history from before the Reader
  // saved places reopens where that history leaves off, as Today's reading
  // step does (usability round 2: Axler, read for months, opened at its first
  // page while Contents ticked sections into 1C). Once, when both are read.
  useEffect(() => {
    if (!historyResumeRef.current || !render || offline || !guidePlan || readingHistory === null) return;
    if (guidePlan.extractionId && guidePlan.extractionId !== render.extractionId) return;
    historyResumeRef.current = false;
    const spanId = resumeSpanFromHistory(guidePlan.sections, readingHistory);
    if (spanId) jumpToSpan(spanId, "start");
  }, [render, offline, guidePlan, readingHistory, jumpToSpan]);

  // The learner's own hand on the page: what makes a scroll reading (round 2).
  const noteUserScroll = useCallback(() => {
    userScrollAtRef.current = Date.now();
  }, []);
  // Watching is reading too: playback that moves past the cue a video
  // resumed at counts, as the learner's own scrolling does on a page. A seek
  // (a jump, a resume, a click in the transcript) only sets the cue playback
  // starts from, and nothing counts while the video is paused (round-2
  // review F5: a paused video taken to a short section counted as watched).
  const lastPlaybackSpanRef = useRef<string | null>(null);
  const onPlaybackSpan = useCallback((spanId: string | null, advancing: boolean) => {
    const last = lastPlaybackSpanRef.current;
    lastPlaybackSpanRef.current = spanId;
    if (advancing && spanId && last && spanId !== last && Date.now() >= settleUntilRef.current) setReadingMoved(true);
    setReadingSpan(spanId);
  }, []);
  useEffect(() => {
    if (!render) return;
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
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
    }
    paneRef.current?.scrollToPage(position.page, position.offset);
  }, [render, offline, pdfView]);

  // Palette (§5.2): a preset runs the local-first capture transaction. Commit presets
  // also create a commitment; synthesis is enqueued off the hot path (§5.3, §6).
  const invokePreset = useCallback(
    async (preset: string) => {
      if (!render || !selection) return;
      const nodes = selectionNodes(selection);
      const editedText = selection.editedText?.trim();
      const nodeSpanIds = nodes.map((n) => n.spanId);
      if (offline) {
        setAnnotations((a) => [
          { annotationId: null, quote: selection.quote, status: "exact", learnerText: note, kind: preset, segments: optimisticSegments(nodeSpanIds) },
          ...a,
        ]);
        setSelectionActions((actions) => [...new Set([...actions, preset])]);
        setNote("");
        return;
      }
      setBusy(true);
      try {
        const receipt = await api.readerInvokePreset({
          preset,
          sourceId: render.sourceId,
          revisionId: render.revisionId,
          extractionId: render.extractionId,
          clientIdempotencyKey: newKey(),
          renderViewId: render.renderViewId,
          rawSelection: editedText ? { nodes, editedText } : { nodes },
          learnerText: note,
          subjectId: selection.spanId,
        });
        setAnnotations((a) => [
          { annotationId: receipt.annotationId, quote: selection.quote, status: receipt.anchorStatus, learnerText: note, kind: preset, segments: optimisticSegments(nodeSpanIds) },
          ...a,
        ]);
        // §10.2 / Journey 2: a commit shows a durable, immediately visible arc.
        if (receipt.arc) setArc(receipt.arc);
        setSelectionActions((actions) => [...new Set([...actions, preset])]);
        setNote("");
        // Drain the local outbox so the demand-paged request is enqueued + visible.
        // The capture is already durable at this point, so a drain failure is a
        // delayed background job—not a failed capture and not a reason to repeat it.
        try {
          const drained = await api.readerDrainOutbox();
          if (drained.failed.length > 0) {
            onError(`${drained.failed.length} saved Reader request${drained.failed.length === 1 ? " is" : "s are"} still waiting to start.`);
          }
        } catch (error) {
          onError(`Saved locally, but background processing has not started yet: ${errorMessage(error)}`);
        }
        void refreshAnnotations();
        void refreshRequests();
      } catch (error) {
        onError(errorMessage(error));
      } finally {
        setBusy(false);
      }
    },
    [render, selection, note, offline, onError, refreshAnnotations, refreshRequests, optimisticSegments],
  );

  // A plain highlight is a slice-1 CAPTURE action, not one of the nine presets —
  // reader.invoke_preset rejects "highlight" deterministically. Route it through
  // reader.capture so the annotation lands with no commitment and no synthesis.
  const captureHighlight = useCallback(async () => {
    if (!render || !selection) return;
    const nodes = selectionNodes(selection);
    const nodeSpanIds = nodes.map((n) => n.spanId);
    if (offline) {
      setAnnotations((a) => [
        { annotationId: null, quote: selection.quote, status: "exact", learnerText: note, kind: "highlight", segments: optimisticSegments(nodeSpanIds) },
        ...a,
      ]);
      setSelectionActions((actions) => [...new Set([...actions, "highlight"])]);
      setNote("");
      return;
    }
    setBusy(true);
    try {
      const receipt = await api.readerCapture({
        sourceId: render.sourceId,
        revisionId: render.revisionId,
        extractionId: render.extractionId,
        action: "highlight",
        clientIdempotencyKey: newKey(),
        renderViewId: render.renderViewId,
        rawSelection: { nodes },
        learnerText: note,
      });
      setAnnotations((a) => [
        { annotationId: receipt.annotationId, quote: selection.quote, status: receipt.anchorStatus ?? "exact", learnerText: note, kind: "highlight", segments: optimisticSegments(nodeSpanIds) },
        ...a,
      ]);
      setSelectionActions((actions) => [...new Set([...actions, "highlight"])]);
      setNote("");
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [render, selection, note, offline, onError, refreshAnnotations, optimisticSegments]);

  // §10.2 arc controls: pause or change depth policy. Neither widens the envelope.
  const pauseArc = useCallback(async () => {
    if (!arc || offline || !enabled) return;
    try {
      await api.readerPauseArc({ arcId: arc.arcId });
      const next = await api.readerArc({ arcId: arc.arcId });
      setArc(next);
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [arc, offline, enabled, onError]);

  const setArcPolicy = useCallback(
    async (policy: string) => {
      if (!arc || offline || !enabled) return;
      try {
        await api.readerSetDepthPolicy({ arcId: arc.arcId, policy });
        const next = await api.readerArc({ arcId: arc.arcId });
        setArc(next);
      } catch (error) {
        onError(errorMessage(error));
      }
    },
    [arc, offline, enabled, onError],
  );

  // Exact-exercise slice: send the ordered per-block selection segments to one
  // background authoring job. The exercise text stays verbatim (source-owned);
  // AI completes the answer, rubric, facets, hints, and depth-rung metadata.
  const importExercise = useCallback(async () => {
    if (!render || !selection || offline) return;
    const nodes = selectionNodes(selection);
    const editedText = selection.editedText?.trim();
    setBusy(true);
    try {
      const receipt = await api.readerImportExercise({
        extractionId: render.extractionId,
        sourceId: render.sourceId,
        revisionId: render.revisionId,
        renderViewId: render.renderViewId,
        rawSelection: editedText ? { nodes, editedText } : { nodes },
        clientIdempotencyKey: newKey(),
      });
      setExerciseImport({
        batchId: receipt.batchId,
        status: receipt.status || "queued",
        quote: editedText ? editedText.replace(/\s+/g, " ") : selection.quote,
        result: null,
        error: null,
      });
      setSelectionActions((prev) => [...prev, "exercise_import"]);
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [render, selection, offline, onError]);

  // Poll the import job while it is in flight; completion carries the written
  // card summaries (and reloads the vault sidecar-side so they schedule).
  const exerciseImportBatchId = exerciseImport?.batchId ?? null;
  const exerciseImportActive =
    exerciseImport != null && ["queued", "running", "blocked"].includes(exerciseImport.status);
  useEffect(() => {
    if (!exerciseImportBatchId || !exerciseImportActive || offline) return;
    const timer = setInterval(async () => {
      try {
        const status = await api.readerExerciseImportStatus({ batchId: exerciseImportBatchId });
        setExerciseImport((prev) =>
          prev && prev.batchId === exerciseImportBatchId
            ? {
                ...prev,
                status: status.status,
                result: status.result ?? prev.result,
                error: status.error?.message ?? status.message ?? null,
              }
            : prev,
        );
      } catch {
        // transient poll failure: keep polling; the job is durable.
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [exerciseImportBatchId, exerciseImportActive, offline]);

  const saveOwnQuestion = useCallback(async () => {
    if (!render || !authoredQuestion.trim() || !authoredAnswer.trim()) return;
    setAuthoringBusy(true);
    try {
      if (offline) {
        setAuthoredStatus("offline_demo");
        setAuthoredCardId("offline-demo-card");
      } else {
        const saved = await api.readerAuthorQA({
          question: authoredQuestion.trim(),
          answer: authoredAnswer.trim(),
          sourceId: render.sourceId,
          revisionId: render.revisionId,
          subjectId: authoringSpanId ? `span:${render.extractionId}/${authoringSpanId}` : render.sourceId,
          clientIdempotencyKey: newKey(),
        });
        setAuthoredStatus(saved.practiceStatus);
        setAuthoredCardId(saved.cardId);
      }
      setCoach(null);
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setAuthoringBusy(false);
    }
  }, [render, authoredQuestion, authoredAnswer, offline, authoringSpanId, onError]);

  // The optional wording help appears only after the learner's exact Q+A has
  // been saved, preserving the authored-before-assistance contract.
  const runCoach = useCallback(async () => {
    if (offline || !enabled || !authoredCardId) return;
    try {
      const lint = await api.readerCoachLint({
        question: authoredQuestion,
        answer: authoredAnswer,
        level: "expert",
      });
      setCoach(lint);
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [authoredQuestion, authoredAnswer, authoredCardId, offline, enabled, onError]);

  const changeMode = useCallback(
    async (next: string) => {
      const previous = mode;
      setMode(next);
      if (!render || offline || !enabled) return;
      const version = ++modeSaveVersionRef.current;
      try {
        await api.readerSetMode({ mode: next, extractionId: render.extractionId });
      } catch (error) {
        if (modeSaveVersionRef.current === version) setMode(previous);
        onError(errorMessage(error, "Could not save the reading mode."));
      }
    },
    [mode, render, offline, enabled, onError],
  );

  const changeAnswerMode = useCallback(
    async (next: string) => {
      const answerModeNext = next as ReaderAnswerMode;
      const previous = answerMode;
      setAnswerMode(answerModeNext);
      if (!render || !activeSpan || offline) return;
      const version = ++answerModeSaveVersionRef.current;
      try {
        await api.readerSetAnswerMode({
          extractionId: render.extractionId,
          spanId: activeSpan,
          answerMode: answerModeNext,
        });
      } catch (error) {
        if (answerModeSaveVersionRef.current === version) setAnswerMode(previous);
        onError(errorMessage(error, "Could not save the answer mode."));
      }
    },
    [answerMode, render, activeSpan, offline, onError],
  );

  const sendQuestionControl = useCallback(
    async (control: string) => {
      setQuestionControl(control);
      if (!render || offline || !enabled) return;
      try {
        await api.readerQuestionControl({ control, subjectId: boundaryBlock?.spanId ?? undefined });
      } catch (error) {
        onError(errorMessage(error));
      }
    },
    [render, offline, enabled, boundaryBlock, onError],
  );

  const ask = useCallback(async () => {
    // Grounding span = the capture selection's primary block (the same
    // selection Notes>Capture acts on); activeSpan is the jump/resume fallback.
    const groundingSpan = selection?.spanId ?? activeSpan;
    if (!groundingSpan || !question.trim() || !render) return;
    const asked = question.trim();
    setBusy(true);
    try {
      const answer = await api.readerAsk({
        extractionId: render.extractionId,
        spanId: groundingSpan,
        question: asked,
        answerMode,
        // The full capture selection widens the tutor's citable context to
        // every selected block, not just the primary one.
        selectionSpanIds: selection ? [...new Set(selectionNodes(selection).map((n) => n.spanId))] : [],
        selectionQuote: selection ? (selection.editedText ?? selection.quote).trim() || null : null,
      });
      const exchange: ReaderExchange = {
        id: answer.readerAnswerEventId,
        spanId: groundingSpan,
        question: asked,
        answerMd: answer.answerMd,
        answerMode: answer.answerMode,
        createdAt: new Date().toISOString(),
      };
      setHistory((items) => [exchange, ...items.filter((item) => item.id !== exchange.id)]);
      setCollapsedAskIds((ids) => {
        const next = new Set(ids);
        next.delete(exchange.id);
        return next;
      });
      setQuestion("");
      // WebKit can retain the submitted textarea's stale compositing layer when
      // the completed exchange mounts below it. Remounting gives the next Ask a
      // fresh input surface; focus restoration makes repeated questions fluid.
      setAskComposerVersion((version) => version + 1);
      // The answer comes into view (finishing pass, re-test #4: it arrived
      // below the fold and the box just emptied). The composer keeps focus
      // without pulling the view back up; typing brings it into view again.
      window.requestAnimationFrame(() => {
        askComposerRef.current?.focus({ preventScroll: true });
        const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find(
          (element) => element.dataset.askId === exchange.id,
        );
        card?.scrollIntoView?.({ behavior: "smooth", block: "start" });
      });
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [selection, activeSpan, question, answerMode, render, onError]);

  const chooseDisposition = useCallback(
    async (d: ReaderDisposition) => {
      setDisposition(d);
      if (!enabled || !boundaryBlock) return;
      try {
        await api.readerChooseDisposition({ disposition: d, subjectId: boundaryBlock.spanId ?? "", subjectType: "reader_span" });
      } catch (error) {
        onError(errorMessage(error));
      }
    },
    [enabled, boundaryBlock, onError],
  );

  const normalizedAskFind = askFindQuery.trim().toLowerCase();
  const visibleAskHistory = useMemo(
    () => history.filter((exchange) => {
      if (!normalizedAskFind) return true;
      return `${exchange.question}\n${exchange.answerMd}`.toLowerCase().includes(normalizedAskFind);
    }),
    [history, normalizedAskFind],
  );

  // In video mode the transcript owns Ctrl/Cmd+F everywhere except while the
  // Ask tab is active. Ask then provides a source-local index over durable
  // questions and answers, including text hidden inside collapsed exchanges.
  useEffect(() => {
    if (railTab !== "ask") return;
    const onFind = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
        event.preventDefault();
        event.stopImmediatePropagation();
        setAskFindOpen(true);
        window.setTimeout(() => askFindInputRef.current?.focus(), 0);
      } else if (event.key === "Escape" && askFindOpen) {
        setAskFindOpen(false);
        setAskFindQuery("");
      }
    };
    window.addEventListener("keydown", onFind, { capture: true });
    return () => window.removeEventListener("keydown", onFind, { capture: true });
  }, [railTab, askFindOpen]);

  // ── A book still being prepared: its original, at once (UX Phase 1, §6.3) ──
  if (!render && preparingCard) {
    return (
      <PreparingView
        key={preparingCard.sourceId}
        card={preparingCard}
        onBack={onOpenLibrary ?? backToLibrary}
        onReady={(next, position) => {
          // The preparing view stays up through the hand-over and keeps polling.
          if (openingRef.current !== next.sourceId) void openSource(next, undefined, position);
        }}
        onError={onError}
      />
    );
  }

  // ── A book being opened: named, not a second list of books (round 2) ──
  if (!render && opening && openingTitle) {
    return (
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>READER</span>
            <Meta>{openingTitle}</Meta>
          </div>
          <Faint style={{ fontSize: 12 }}>◐ Opening {openingTitle}…</Faint>
        </div>
      </div>
    );
  }

  // ── Source picker: the Reader's front door is the real library ──
  if (!render) {
    // Every book is listed and openable; one still being prepared opens on its
    // original (UX Phase 1) instead of hiding behind "still getting ready".
    const readySources = library ?? [];
    // The one shelf, when the shell provides it (spec K5): search stays here.
    const useShelf = Boolean(shelf) && !sidecarDown;
    return (
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>
              {useShelf ? "READER" : "READER · LIBRARY"}
            </span>
            {sidecarDown ? <Pill color="amber">offline</Pill> : null}
          </div>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
            {useShelf ? "Pick a book to read, or search them all." : "Pick up where you left off, or open something new."}
          </span>
        </div>
        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: useShelf ? "18px 0 0" : "18px 32px", display: "flex", flexDirection: "column", gap: 10, maxWidth: useShelf ? undefined : 720 }}>
          {enabled && !sidecarDown ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: useShelf ? "0 32px" : undefined, maxWidth: 720 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  value={librarySearch}
                  onChange={(e) => {
                    setLibrarySearch(e.target.value);
                    setSearchDeep(false);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      setLibrarySearch("");
                      setSearchDeep(false);
                    }
                    if (e.key === "Enter") setSearchDeep(true);
                  }}
                  placeholder="search all sources…"
                  style={{ fontFamily: FONT_MONO, fontSize: 12, width: 280, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 10px" }}
                />
                {searchBusy ? <Faint style={{ fontSize: 11 }}>◐ searching…</Faint> : searchResults ? (
                  <Faint style={{ fontSize: 11 }}>
                    {searchResults.hits.length} hit{searchResults.hits.length === 1 ? "" : "s"} across {searchResults.searchedSources} source{searchResults.searchedSources === 1 ? "" : "s"}
                    {searchBasisLabel(searchResults)}
                  </Faint>
                ) : null}
              </div>
              {searchError ? (
                <div role="alert" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.red }}>
                  {searchError} Edit the search to retry.
                </div>
              ) : null}
              {searchResults && searchResults.hits.length > 0 ? (
                <div className="ll-scroll" style={{ maxHeight: 320, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
                  {searchResults.hits.map((hit) => {
                    const card = (library ?? []).find((c) => c.sourceId === hit.sourceId);
                    return (
                      <Card
                        key={`${hit.extractionId}/${hit.spanId}`}
                        onClick={() => {
                          if (card && opening === null) void openSource(card, hit.spanId);
                        }}
                        style={{ display: "flex", flexDirection: "column", gap: 4, cursor: card ? "pointer" : "default" }}
                      >
                        <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
                          <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink }}>{clip(hit.sourceTitle, 60)}</span>
                          {hit.section ? <Faint style={{ fontSize: 10 }}>· {clip(hit.section, 50)}</Faint> : null}
                          {hit.page !== null ? <Faint style={{ fontSize: 10 }}>· p.{hit.page}</Faint> : null}
                        </div>
                        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim, lineHeight: 1.5 }}>{hit.snippet}</span>
                      </Card>
                    );
                  })}
                </div>
              ) : searchResults && !searchBusy ? (
                <Faint style={{ fontSize: 11 }}>no matches — this searches the text of every book that is ready.</Faint>
              ) : null}
            </div>
          ) : null}
          {contract !== null && !enabled && !sidecarDown ? (
            <Card style={{ borderStyle: "dashed", display: "flex", flexDirection: "column", gap: 6 }}>
              <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
                the reader is disabled in this vault's config (new vaults have it on by default). Set <Dim>tutor_qa.reader_enabled = true</Dim>
                in learnloop.toml to read and annotate real sources; the demo chapter below works without it.
              </Faint>
            </Card>
          ) : null}
          {useShelf ? (
            shelf
          ) : library === null ? (
            <Faint style={{ fontSize: 12 }}>◐ loading source library…</Faint>
          ) : readySources.length === 0 ? (
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              {sidecarDown
                ? "the sidecar is unreachable — only the offline demo chapter is available."
                : "Nothing to read yet. Add a book, paper or video from the Library."}
            </Faint>
          ) : (
            readySources.map((card) => {
              const cardOpenable = enabled && card.readerEnabled !== false;
              const isVideo = youtubeVideoId(card.canonicalUri ?? "") !== null;
              return (
                <Card
                  key={card.sourceId}
                  onClick={() => {
                    if (cardOpenable && opening === null) void openSource(card);
                  }}
                  style={{ display: "flex", flexDirection: "column", gap: 4, cursor: cardOpenable ? "pointer" : "default", opacity: cardOpenable ? 1 : 0.55 }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }} title={card.title}>
                      {card.title}
                    </span>
                    {card.readerEnabled === false ? (
                      <Pill color="slate">reader off · set at ingest</Pill>
                    ) : (
                      <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2 }}>
                        {opening === card.sourceId ? "opening…" : isVideo ? "watch →" : "read →"}
                      </span>
                    )}
                  </div>
                  <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
                    {card.readiness === "ready" ? `${card.unitCount} sections` : card.statusLine?.text ?? "Getting this ready"}
                  </Faint>
                </Card>
              );
            })
          )}
          {/* The demo chapter is for when LearnLoop's background service is
              down, not a book on the main path (spec §7.3; usability round 1). */}
          {sidecarDown ? (
            <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 10 }}>
              <SecondaryButton onClick={openFixture}>open demo chapter (fixture)</SecondaryButton>
              <Faint style={{ fontSize: 11 }}>offline demo — captures are not persisted.</Faint>
            </div>
          ) : null}
        </div>
        <KeyBar keys={[{ key: "click", label: "open source" }]} right={{ key: "^p", label: "palette" }} />
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>READER</span>
          <button
            type="button"
            onClick={onOpenLibrary ?? backToLibrary}
            style={{ background: "none", border: "none", padding: 0, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
          >
            ← Library
          </button>
          <Meta>{sourceTitle ?? "Untitled source"}</Meta>
          {offline ? <Pill color="amber">offline demo</Pill> : null}
          {pdfView && !offline ? (
            <span
              onClick={() => setSurface((s) => (s === "pdf" ? "text" : "pdf"))}
              style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
            >
              {surface === "pdf" ? "extracted text →" : "original pdf →"}
            </span>
          ) : null}
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <Faint style={{ fontSize: 11 }}>I want to</Faint>
            <TermSelect value={mode} options={READER_MODE_OPTIONS} onChange={changeMode} width={150} />
          </div>
        </div>
        <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
          {offline
            ? "offline demo — captures live only in this window and are not persisted."
            : "Select a passage to ask about it, mark it, or make your own practice."}
        </span>
        {!offline ? (
          <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
            <Faint style={{ fontSize: 11, flexShrink: 0 }}>
              {currentGuideSection?.label ?? "reading"}
            </Faint>
            <div style={{ height: 3, flex: 1, maxWidth: 280, background: COLOR.border, overflow: "hidden" }} aria-label={`${Math.round(readingProgress * 100)}% read`}>
              <div style={{ height: "100%", width: `${Math.max(2, readingProgress * 100)}%`, background: COLOR.amber }} />
            </div>
            <Faint style={{ fontSize: 10 }}>{Math.round(readingProgress * 100)}%</Faint>
            <button
              type="button"
              onClick={() => setSectionPromptsEnabled((value) => !value)}
              aria-pressed={sectionPromptsEnabled}
              disabled={mode !== "anchor"}
              style={{ marginLeft: "auto", border: 0, background: "transparent", color: boundaryChecksAvailable ? COLOR.amberLink : COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 11, cursor: mode === "anchor" ? "pointer" : "default", padding: 0 }}
            >
              {mode !== "anchor" ? "quick checks while reading closely" : sectionPromptsEnabled ? "quick checks on" : "quick checks off"}
            </button>
          </div>
        ) : null}
      </div>

      <div style={{ flex: 1, minHeight: 0, display: "flex", overflow: "hidden" }}>
        <div
          ref={bodyRef}
          onMouseDown={(event) => {
            noteUserScroll();
            onBodyMouseDown(event);
          }}
          onMouseUp={onMouseUp}
          onWheel={noteUserScroll}
          onTouchMove={noteUserScroll}
          onScroll={onReadingScroll}
          className="ll-scroll"
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "18px 32px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            position: "relative",
            cursor: domArmed && !pdfSurfaceActive ? "crosshair" : undefined,
          }}
        >
          {!pdfSurfaceActive && (domBoxes.length > 0 || domDraft) ? (
            <div aria-hidden="true" style={{ position: "absolute", left: 0, top: 0, width: 0, height: 0, pointerEvents: "none" }}>
              {!domArmed && !domDraft ? (
                <RectUnionOverlay rects={domBoxes} />
              ) : (
                domBoxes.map((b, i) => (
                  <div
                    key={`dom-box-${i}`}
                    style={{
                      position: "absolute",
                      left: b[0] - 2,
                      top: b[1] - 1.5,
                      width: b[2] - b[0] + 4,
                      height: b[3] - b[1] + 3,
                      background: "rgba(245, 166, 35, 0.14)",
                      border: "1.5px solid rgba(215, 135, 15, 0.85)",
                      borderRadius: 3,
                    }}
                  />
                ))
              )}
              {domDraft ? (
                <div
                  style={{
                    position: "absolute",
                    left: domDraft[0] - 2,
                    top: domDraft[1] - 1.5,
                    width: domDraft[2] - domDraft[0] + 4,
                    height: domDraft[3] - domDraft[1] + 3,
                    background: "rgba(245, 166, 35, 0.08)",
                    border: "1.5px dashed rgba(215, 135, 15, 0.75)",
                    borderRadius: 3,
                  }}
                />
              ) : null}
            </div>
          ) : null}
          {watch ? (
            <YouTubeWatchPanel
              ref={watchRef}
              plan={watch}
              blocks={blocks}
              annotatedSpans={annotatedSpans}
              guidanceSpans={revealedGuidanceSpans}
              resumeSpan={readingSpan}
              findShortcutEnabled={railTab !== "ask"}
              onPlaybackSpan={onPlaybackSpan}
              onAskSpan={(spanId) => {
                if (spanId) setActiveSpan(spanId);
              }}
              onTagMenu={openDomTagMenu}
            />
          ) : watchLoading ? (
            <Card style={{ padding: 18 }}><Faint style={{ fontSize: 12 }}>◐ preparing video and synchronized transcript…</Faint></Card>
          ) : null}
          {pdfView && surface === "pdf" && !offline ? (
            <PdfReaderPane
              ref={paneRef}
              fileUrl={convertFileSrc(pdfView.fileName ?? "", "llpdf")}
              blocks={pdfView.blocks}
              trails={trails}
              guidanceSpans={revealedGuidanceSpans}
              selectedSpans={selectedSpanSet}
              activeSpan={activeSpan}
              onTextSelection={(sel) => {
                setSelection(sel);
                setSelectionActions([]);
                setEditingCapture(false);
                setActiveSpan(sel.spanId);
                setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
              }}
              onTagMenu={setTagMenu}
              onError={onError}
            />
          ) : null}
          {pdfOfferSection ? (
            // The original PDF's own section break (usability round 1, U5): the
            // same quiet offer the text view puts between sections, held at
            // the foot of the page while the check is open.
            <div style={{ position: "sticky", bottom: 0, zIndex: 5, background: COLOR.bg, paddingTop: 4 }}>
              <SectionBoundaryOffer
                section={pdfOfferSection}
                allowQuestion
                onOpen={() => openQuickCheck(pdfOfferSection.id)}
                onReveal={() => {
                  revealSection(pdfOfferSection.id);
                  setHiddenPdfOffers((ids) => [...new Set([...ids, pdfOfferSection.id])]);
                  setRailTab("guide");
                }}
                onDismiss={() => setHiddenPdfOffers((ids) => [...new Set([...ids, pdfOfferSection.id])])}
              />
            </div>
          ) : null}
          {(pdfView && surface === "pdf" && !offline) || watch || watchLoading ? null : blocks.map((block, i) => {
            const isSection = (block.blockType ?? "") === "Section";
            const active = activeSpan === block.spanId;
            const guidePassage = block.spanId ? revealedPassages.get(block.spanId) : undefined;
            const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined;
            const endQuestionAvailable = boundaryChecksAvailable
              && endSection?.question?.readingPhase === "after_section";
            const offerSection = endSection
              && !dismissedSections.includes(endSection.id)
              && !completedSections.includes(endSection.id)
              && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0);
            return (
              <Fragment key={block.displayNodeId ?? `p${i}`}>
              <div
                data-span-id={block.spanId ?? undefined}
                data-extraction-id={render?.extractionId}
                onContextMenu={(e) => {
                  if (!block.spanId) return;
                  e.preventDefault();
                  const sel = window.getSelection();
                  const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : "";
                  openDomTagMenu({ x: e.clientX, y: e.clientY, spanId: block.spanId, quote: quote || null });
                }}
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: isSection ? 15 : 13,
                  color: isSection ? COLOR.amber : COLOR.text,
                  lineHeight: 1.7,
                  borderLeft: `3px solid ${active ? COLOR.amber : block.spanId && annotatedSpans.has(block.spanId) ? "rgba(245, 166, 35, 0.35)" : guidePassage ? COLOR.purplePill : "transparent"}`,
                  background: block.spanId && annotatedSpans.has(block.spanId) ? "rgba(245, 166, 35, 0.04)" : guidePassage ? COLOR.washPurple : undefined,
                  paddingLeft: 12,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  {guidePassage ? <Pill color="purple">worth a second look</Pill> : null}
                  {BADGED_HEALTH.has(block.health.status) ? (
                    <Pill color={HEALTH_COLOR[block.health.status] ?? "slate"}>
                      {block.health.status} · {block.health.recommendedView}
                    </Pill>
                  ) : null}
                  {block.sanitized ? <Faint style={{ fontSize: 10 }}>sanitized</Faint> : null}
                </div>
                <MarkdownMath value={block.markdown} />
                {block.health.status === "failed" ? (
                  pdfView && !offline && block.spanId ? (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setReadingSpan(block.spanId);
                        setActiveSpan(block.spanId);
                        setSurface("pdf");
                      }}
                      style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                    >
                      extracted text unreliable — view original →
                    </button>
                  ) : (
                    <Faint style={{ fontSize: 10 }}>extracted text unreliable — view original region</Faint>
                  )
                ) : null}
              </div>
              {offerSection ? (
                <SectionBoundaryOffer
                  section={endSection}
                  allowQuestion={endQuestionAvailable}
                  onOpen={() => openQuickCheck(endSection.id)}
                  onReveal={() => {
                    revealSection(endSection.id);
                    setRailTab("guide");
                  }}
                  onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, endSection.id])])}
                />
              ) : null}
              </Fragment>
            );
          })}
        </div>

        {/* Right rail: annotation margin + capture + Ask */}
        <div
          ref={railRef}
          style={{
            width: 360,
            height: "100%",
            minHeight: 0,
            flexShrink: 0,
            borderLeft: `1px solid ${COLOR.border}`,
            padding: "18px 20px",
            overflowX: "hidden",
            overflowY: "auto",
            overscrollBehaviorY: "contain",
            scrollbarGutter: "stable",
          }}
          className="ll-scroll"
        >
          <div style={{ position: "sticky", top: -18, zIndex: 8, margin: "-18px -20px 16px", padding: "12px 20px 10px", background: COLOR.bg, borderBottom: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", gap: 4 }}>
              {(["guide", "ask", "notes"] as ReaderRailTab[]).map((tab) => {
                const active = railTab === tab;
                const guideAlert = tab === "guide" && pendingQuickCheckCount > 0;
                return (
                  <button
                    key={tab}
                    type="button"
                    className={guideAlert && !active ? "ll-reader-guide-alert" : undefined}
                    onClick={() => setRailTab(tab)}
                    aria-pressed={active}
                    aria-label={guideAlert ? `Guide, ${pendingQuickCheckCount} quick check${pendingQuickCheckCount === 1 ? "" : "s"} ready` : tab}
                    style={{ flex: 1, display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 6, border: `1px solid ${guideAlert ? COLOR.pink : active ? COLOR.borderFocus : COLOR.border}`, background: guideAlert ? (active ? COLOR.washPurple : undefined) : active ? COLOR.washAmber : "transparent", color: guideAlert ? COLOR.purpleText : active ? COLOR.amberLink : COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, padding: "6px 8px", cursor: "pointer", textTransform: "uppercase", letterSpacing: "0.08em" }}
                  >
                    {tab}
                    {guideAlert ? (
                      <span aria-hidden="true" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                        <span className="ll-qc-blink">◆</span>
                        {pendingQuickCheckCount}
                      </span>
                    ) : null}
                    {tab === "notes" && annotations.length > 0 ? <span>{annotations.length}</span> : null}
                  </button>
                );
              })}
            </div>
            {pendingQuickCheckCount > 0 && railTab !== "guide" ? (
              <button
                type="button"
                className="ll-reader-qc-strip"
                onClick={() => setRailTab("guide")}
                style={{ fontFamily: FONT_MONO }}
              >
                <span className="ll-qc-blink" aria-hidden="true">◆</span>
                <span>{pendingQuickCheckCount === 1 ? "quick check ready" : `${pendingQuickCheckCount} quick checks ready`}</span>
                <span className="ll-qc-strip-go" aria-hidden="true">guide →</span>
              </button>
            ) : null}
          </div>

          <div style={{ display: railTab === "guide" ? "block" : "none" }}>
            <SectionHeader style={{ marginTop: 0 }}>Reading guide</SectionHeader>
            {guidePlan?.goalContext ? (
              <Card style={{ display: "flex", flexDirection: "column", gap: 5, marginBottom: 10, background: COLOR.washCyan }}>
                <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>YOUR PATH</Faint>
                <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{guidePlan.goalContext.title}</span>
                <Faint style={{ fontSize: 10 }}>
                  Reading toward your active goal
                </Faint>
              </Card>
            ) : null}
            {currentGuideSection ? (
              <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Pill color="slate">section</Pill>
                  <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{currentGuideSection.label}</span>
                </div>
                <div
                  role="progressbar"
                  aria-label="Read of this section"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(currentSectionRead * 100)}
                  style={{ height: 3, background: COLOR.border }}
                >
                  <div style={{ height: "100%", width: `${currentSectionRead * 100}%`, background: COLOR.cyan }} />
                </div>
                <Faint style={{ fontSize: 10 }}>
                  {boundaryChecksAvailable && currentGuideSection.question && currentQuestionOpen
                    ? answeredSections.includes(currentGuideSection.id)
                      ? "You answered this section's quick check: compare below, then keep reading."
                      : currentGuideSection.question.placement === "auto_authored"
                      ? "A quick check on this section is ready, just below."
                      : currentGuideSection.question.readingPhase === "before_section"
                        ? "There’s an optional question before you begin this section."
                        : currentGuideSection.question.readingPhase === "during_section"
                          ? "There’s an optional question at this point in the section."
                          : "You’re near the section break. Take a quick check or keep reading."
                    : authoringSections.includes(currentGuideSection.id)
                      ? "◐ writing a quick check for this section…"
                      : timedOutSections.includes(currentGuideSection.id)
                        ? (
                          <>
                            Couldn't write a check for this section ·{" "}
                            <button
                              type="button"
                              onClick={() => retryQuickCheck(currentGuideSection.id)}
                              style={{ background: "none", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer", textDecoration: "underline", fontFamily: FONT_MONO, fontSize: 10 }}
                            >
                              Try again
                            </button>
                          </>
                        )
                      : readingMoved && currentSectionProgress >= 0.7
                        ? "You’re near the section break. Keep going, or revisit a useful passage."
                        : "Keep reading at your own pace."}
                </Faint>
              </Card>
            ) : guideLoading ? (
              <Faint style={{ fontSize: 12 }}>◐ connecting this source to your learning path…</Faint>
            ) : guidePlan === null ? (
              <Faint style={{ fontSize: 12 }}>No personalized guide is available for this source yet.</Faint>
            ) : null}

            {/* Open quick checks come first, right under the section they are
                about, never below the whole Contents list (usability round 1, U5). */}
            {boundaryChecksAvailable
              ? openQuestionSections.map((section) => (
                  <div key={section.id} data-quick-check={section.id}>
                    {section.question?.placement === "auto_authored" ? (
                      <AuthoredQuestionCard
                        section={section}
                        autoStart={focusQuickCheck === section.id}
                        onJump={jumpToSpan}
                        onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, section.id])])}
                        onComplete={() => completeSection(section.id)}
                        onAnswered={() => setAnsweredSections((ids) => [...new Set([...ids, section.id])])}
                        onError={onError}
                      />
                    ) : (
                      <SectionQuestionCard
                        section={section}
                        autoStart={focusQuickCheck === section.id}
                        extractionId={render.extractionId}
                        onReveal={() => revealSection(section.id)}
                        onJump={jumpToSpan}
                        onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, section.id])])}
                        onComplete={() => completeSection(section.id)}
                        onAnswered={() => setAnsweredSections((ids) => [...new Set([...ids, section.id])])}
                        onError={onError}
                      />
                    )}
                  </div>
                ))
              : null}

            {(guidePlan?.sections.length ?? 0) > 1 ? (
              <>
                <SectionHeader>Contents</SectionHeader>
                {/* The rail owns vertical scrolling. A nested Contents scroller
                    traps wheel events at its edges in WebKitGTK/Tauri. */}
                <div style={{ display: "flex", flexDirection: "column", marginBottom: 4 }}>
                  {guidePlan!.sections.map((section) => {
                    // Ticked only when read through (or its check done), never
                    // because the learner jumped past it (usability round 1, U3).
                    const readThrough = completedSections.includes(section.id)
                      || (sectionSeen[section.id] ?? 0) >= section.spanIds.length;
                    const state = section.id === currentGuideSection?.id ? "current" : readThrough ? "read" : "upcoming";
                    const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·";
                    return (
                      <button
                        key={section.id}
                        type="button"
                        onClick={() => jumpToSpan(section.startSpanId, "start")}
                        title={section.question ? `${section.label} · quick check available` : section.label}
                        style={{
                          display: "flex", alignItems: "baseline", gap: 8, textAlign: "left",
                          border: 0, borderLeft: `3px solid ${state === "current" ? COLOR.amber : "transparent"}`,
                          background: state === "current" ? COLOR.washAmber : "transparent",
                          padding: "3px 8px", cursor: "pointer", fontFamily: FONT_MONO,
                        }}
                      >
                        <span style={{ flexShrink: 0, fontSize: 10, color: state === "read" ? COLOR.green : state === "current" ? COLOR.amber : COLOR.textFaint }}>
                          {glyph}
                        </span>
                        <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 11, color: state === "current" ? COLOR.text : COLOR.textDim }}>
                          {section.label}
                        </span>
                        {/* Said in words, and only while the check is still to do
                            (usability round 2: an unexplained "?" sat after ✓). */}
                        {section.question && !completedSections.includes(section.id) && !dismissedSections.includes(section.id)
                          && !answeredSections.includes(section.id) ? (
                          <span style={{ flexShrink: 0, fontSize: 9, color: COLOR.purpleText }}>quick check</span>
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              </>
            ) : null}

            {currentGuideSection && revealedSections.includes(currentGuideSection.id) ? (
              <>
                <SectionHeader>Worth a second look</SectionHeader>
                {currentGuideSection.suggestedPassages.length === 0 ? (
                  <Faint style={{ fontSize: 11 }}>No missed passages were identified in this section.</Faint>
                ) : currentGuideSection.suggestedPassages
                    .filter((passage) => !annotatedSpans.has(passage.spanId))
                    .map((passage) => (
                      <Card key={passage.spanId} onClick={() => jumpToSpan(passage.spanId)} style={{ display: "flex", flexDirection: "column", gap: 5, marginBottom: 7, cursor: "pointer", background: COLOR.washPurple }}>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                          <Pill color={passage.learnerSignal === "recent_misunderstanding" ? "pink" : "purple"}>
                            {passage.learnerSignal === "recent_misunderstanding" ? "repair" : "important"}
                          </Pill>
                          <Faint style={{ fontSize: 10 }}>{passage.learningObjectTitle}</Faint>
                        </div>
                        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>“{clip(passage.quote, 150)}”</span>
                        <Faint style={{ fontSize: 10, lineHeight: 1.45 }}>{passage.reason}</Faint>
                      </Card>
                    ))}
              </>
            ) : null}

            {currentGuideSection && completedSections.includes(currentGuideSection.id) ? (
              <Card style={{ marginTop: 10, background: COLOR.washGreen }}>
                <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.green }}>✓ quick check complete — keep going.</span>
              </Card>
            ) : null}
          </div>

          <div style={{ display: railTab === "notes" ? "block" : "none" }}>
          <SectionHeader style={{ marginTop: 0 }}>Capture</SectionHeader>
          {selection ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Faint style={{ fontSize: 11 }}>
                    selected · {selection.nodes && selection.nodes.length > 1 ? `${selection.nodes.length} passages` : selection.spanId}
                  </Faint>
                  <button
                    type="button"
                    onClick={() => setEditingCapture((v) => !v)}
                    style={{ marginLeft: "auto", border: 0, background: "transparent", color: editingCapture ? COLOR.amberLink : COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer" }}
                  >
                    {editingCapture ? "done" : "edit"}
                  </button>
                  <button type="button" onClick={clearSelection} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer" }}>clear</button>
                </div>
                {editingCapture ? (
                  // OCR-mishap repair: the whole selection edits as ONE
                  // combined passage (block fragments joined in reading
                  // order); the edited text becomes the practice surface while
                  // the anchors stay on the source blocks.
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <textarea
                      value={selection.editedText ?? selectionNodes(selection).map((n) => n.quote).join("\n\n")}
                      onChange={(e) => editCaptureText(e.target.value)}
                      autoFocus
                      style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${selection.editedText != null ? COLOR.amberLink : COLOR.border}`, color: COLOR.text, padding: 6, minHeight: 110, resize: "vertical" }}
                    />
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Faint style={{ fontSize: 10 }}>
                        fix any OCR mishaps — the edited passage becomes the practice surface; anchors stay on the source blocks.
                      </Faint>
                      {selection.editedText != null ? (
                        <button
                          type="button"
                          onClick={resetCaptureText}
                          style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                        >
                          reset
                        </button>
                      ) : null}
                    </div>
                  </div>
                ) : selection.editedText != null ? (
                  <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                    “{clip(selection.editedText.replace(/\s+/g, " ").trim(), 360)}”
                    <Faint style={{ fontSize: 10, color: COLOR.amberLink }}> (edited)</Faint>
                  </span>
                ) : selection.nodes && selection.nodes.length > 1 ? (
                  // Per-block anchor preview: exactly what each capture will
                  // ground to, so an over-wide sweep is visible before acting.
                  <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    {selection.nodes.map((node, index) => (
                      <span key={`${node.spanId}-${index}`} style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.text }}>
                        <Faint style={{ fontSize: 10 }}>[{index + 1}]</Faint> “{clip(node.quote, 110)}”
                      </span>
                    ))}
                  </div>
                ) : (
                  <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>“{clip(selection.quote, 360)}”</span>
                )}
                {selectionActions.length > 0 ? (
                  <Faint style={{ fontSize: 10, color: COLOR.green }}>✓ saved · choose another action or select another passage</Faint>
                ) : null}
              </Card>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="your note (optional)…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 54, resize: "vertical" }}
              />
              <PrimaryButton onClick={() => captureHighlight()} disabled={busy || selectionActions.includes("highlight")}>
                {selectionActions.includes("highlight") ? "highlighted ✓" : "highlight"}
              </PrimaryButton>
              {!offline ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>EXERCISES</Faint>
                  <PrimaryButton
                    onClick={() => void importExercise()}
                    disabled={busy || exerciseImportActive || selectionActions.includes("exercise_import")}
                  >
                    {selectionActions.includes("exercise_import") ? "exercise queued ✓" : "add exercise to practice"}
                  </PrimaryButton>
                  <Faint style={{ fontSize: 10 }}>
                    the exercise text stays verbatim — AI completes the answer, rubric, hints, and depth.
                  </Faint>
                </div>
              ) : null}
              {PALETTE.map((grp) => (
                <div key={grp.group} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <Faint style={{ fontSize: 10, letterSpacing: "0.14em" }}>{grp.group.toUpperCase()}</Faint>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {grp.presets.map((p) => (
                      <SecondaryButton key={p.preset} onClick={() => invokePreset(p.preset)} disabled={busy || selectionActions.includes(p.preset)}>
                        {p.label}{selectionActions.includes(p.preset) ? " ✓" : ""}
                      </SecondaryButton>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Faint style={{ fontSize: 12 }}>
              {pdfSurfaceActive
                ? "drag to select text like a browser · hold ctrl and drag one or more boxes, release ctrl to capture their union (best for exercises) · alt+drag to sweep whole blocks · right-click to tag."
                : "select text to capture it · hold ctrl and drag one or more boxes, release ctrl to capture their union."}
            </Faint>
          )}

          {exerciseImport ? (
            <>
              <SectionHeader>Exercise import</SectionHeader>
              <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {exerciseImportActive ? (
                  <Faint style={{ fontSize: 11 }}>
                    ◐ authoring practice from “{clip(exerciseImport.quote, 90)}” — keep reading, the cards land here.
                  </Faint>
                ) : exerciseImport.status === "completed" && exerciseImport.result ? (
                  <>
                    {exerciseImport.result.items.map((item) => (
                      <div key={item.practiceItemId} style={{ display: "flex", flexDirection: "column", gap: 3, borderBottom: `1px solid ${COLOR.border}`, paddingBottom: 6 }}>
                        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.green }}>
                          ✓ {item.title || clip(item.prompt, 80)}
                        </span>
                        <Faint style={{ fontSize: 10 }}>→ {item.learningObjectTitle}</Faint>
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                          {item.capability ? (
                            <Pill color="purple">{item.capability.replace(/_/g, " ")}</Pill>
                          ) : (
                            <Pill color="slate">depth unclassified</Pill>
                          )}
                          {typeof item.taskFeatures.span === "string" ? (
                            <Pill color="cyan">{String(item.taskFeatures.span).replace(/_/g, " ")}</Pill>
                          ) : null}
                          {item.difficulty != null ? (
                            <Pill color="amber">difficulty {Math.round(item.difficulty * 100) / 100}</Pill>
                          ) : null}
                        </div>
                        <Faint style={{ fontSize: 10 }}>
                          verbatim from the source · {item.evidenceFacets.length} facet{item.evidenceFacets.length === 1 ? "" : "s"} · {item.hintCount} hint{item.hintCount === 1 ? "" : "s"} · scheduled as practice
                        </Faint>
                        {item.classificationReason ? (
                          <Faint style={{ fontSize: 10 }}>{item.classificationReason}</Faint>
                        ) : null}
                      </div>
                    ))}
                    {exerciseImport.result.skipped.map((skip, index) => (
                      <Faint key={index} style={{ fontSize: 10 }}>
                        skipped{skip.title ? ` ${skip.title}` : ""}: {skip.reason}
                      </Faint>
                    ))}
                    {exerciseImport.result.warnings.slice(0, 4).map((warning, index) => (
                      <Faint key={index} style={{ fontSize: 10, color: COLOR.amberLink }}>⚠ {warning}</Faint>
                    ))}
                  </>
                ) : (
                  <Faint style={{ fontSize: 11, color: COLOR.red }}>
                    ✗ {exerciseImport.error || "the exercise import did not complete."}
                  </Faint>
                )}
                {!exerciseImportActive ? (
                  <button
                    type="button"
                    onClick={() => setExerciseImport(null)}
                    style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                  >
                    dismiss
                  </button>
                ) : null}
              </Card>
            </>
          ) : null}

          {(selection || activeSpan || authoringOpen) ? (
            <>
              <SectionHeader>Make your own practice</SectionHeader>
              {!authoringOpen ? (
                <SecondaryButton onClick={() => {
                  const spanId = selection?.spanId ?? activeSpan;
                  setAuthoringSpanId(spanId);
                  setAuthoringQuote(selection?.quote ?? activeBlock?.markdown.replace(/\s+/g, " ") ?? "");
                  setAuthoringOpen(true);
                  setAuthoredCardId(null);
                  setCoach(null);
                }}>
                  write my own question
                </SecondaryButton>
              ) : (
                <Card style={{ display: "flex", flexDirection: "column", gap: 8, background: COLOR.bgElev }}>
                  {authoringQuote ? (
                    <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textFaint }}>From “{clip(authoringQuote, 120)}”</span>
                  ) : null}
                  <textarea
                    value={authoredQuestion}
                    disabled={authoredCardId !== null}
                    onChange={(event) => setAuthoredQuestion(event.target.value)}
                    placeholder="Write a question future-you should answer…"
                    style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 64, resize: "vertical" }}
                  />
                  <textarea
                    value={authoredAnswer}
                    disabled={authoredCardId !== null}
                    onChange={(event) => setAuthoredAnswer(event.target.value)}
                    placeholder="Write the answer in your own words…"
                    style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 72, resize: "vertical" }}
                  />
                  {authoredQuestion.trim() || authoredAnswer.trim() ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, borderTop: `1px solid ${COLOR.border}`, paddingTop: 6 }}>
                      <Faint style={{ fontSize: 10 }}>PREVIEW</Faint>
                      {authoredQuestion.trim() ? (
                        <div className="markdown" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                          <MarkdownMath value={authoredQuestion} />
                        </div>
                      ) : null}
                      {authoredAnswer.trim() ? (
                        <div className="markdown" style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }}>
                          <MarkdownMath value={authoredAnswer} />
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                  {authoredCardId ? (
                    <>
                      <Faint style={{ fontSize: 11, color: authoredQuestionMessage(authoredStatus).scheduled ? COLOR.green : COLOR.textDim }}>
                        {authoredQuestionMessage(authoredStatus).text}
                      </Faint>
                      {!offline ? <SecondaryButton onClick={() => void runCoach()}>check the wording</SecondaryButton> : null}
                      {coach ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                          {coach.suggestions.length === 0 ? (
                            <Faint style={{ fontSize: 11 }}>The wording looks clear as written.</Faint>
                          ) : coach.suggestions.map((suggestion, index) => (
                            <Faint key={index} style={{ fontSize: 11 }}>• {suggestion.prompt}</Faint>
                          ))}
                          {coach.suggestions.length > 0 ? (
                            <Faint style={{ fontSize: 10 }}>Your saved wording stays unchanged. Use “write another” below to make a revised card.</Faint>
                          ) : null}
                        </div>
                      ) : null}
                      <button
                        type="button"
                        onClick={() => {
                          setAuthoredQuestion("");
                          setAuthoredAnswer("");
                          setAuthoredCardId(null);
                          setCoach(null);
                        }}
                        style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                      >
                        write another
                      </button>
                    </>
                  ) : (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <PrimaryButton onClick={() => void saveOwnQuestion()} disabled={authoringBusy || !authoredQuestion.trim() || !authoredAnswer.trim()}>
                        save for practice
                      </PrimaryButton>
                      <SecondaryButton onClick={() => setAuthoringOpen(false)} disabled={authoringBusy}>cancel</SecondaryButton>
                    </div>
                  )}
                </Card>
              )}
            </>
          ) : null}

          {requestLoadError ? (
            <Card status="error" style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              <div role="alert" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.red }}>
                Some Reader request data is unavailable.
              </div>
              <Faint style={{ fontSize: 10 }}>{requestLoadError}</Faint>
              <button
                type="button"
                onClick={() => void refreshRequests()}
                style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
              >
                retry request data
              </button>
            </Card>
          ) : null}

          {requests.length > 0 ? (
            <>
              <SectionHeader>Your requests</SectionHeader>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {requests.map((request) => {
                  const { sourceObjectId, proposalId } = parseRequestResult(request.resultJson);
                  const requestError = parseRequestError(request.errorJson);
                  const result = sourceObjectId ? synthesizedObjects.get(sourceObjectId) : undefined;
                  const expanded = expandedRequests.has(request.id);
                  const proposalOpen = proposalId !== null && openProposalIds.has(proposalId);
                  return (
                    <Card
                      key={request.id}
                      status={request.status === "complete" ? "done" : request.status === "failed" ? "error" : "running"}
                      style={{ display: "flex", flexDirection: "column", gap: 6 }}
                    >
                      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                        <Pill color={request.status === "complete" ? "green" : request.status === "failed" ? "pink" : request.status === "partial" ? "amber" : "slate"}>
                          {request.status === "complete" ? "ready" : request.status === "failed" ? "needs retry" : "working"}
                        </Pill>
                        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                          {request.preset.replace(/_/g, " ")}
                        </span>
                        {request.status === "complete" && result ? (
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedRequests((ids) => {
                                const next = new Set(ids);
                                if (next.has(request.id)) next.delete(request.id);
                                else next.add(request.id);
                                return next;
                              })
                            }
                            style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                          >
                            {expanded ? "▾ hide" : "▸ view result"}
                          </button>
                        ) : request.status === "failed" ? (
                          <button
                            type="button"
                            onClick={() => void retryRequest(request.id)}
                            style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                          >
                            retry
                          </button>
                        ) : null}
                      </div>
                      {request.status === "failed" && requestError ? (
                        <Faint style={{ fontSize: 10, color: COLOR.red }}>{requestError}</Faint>
                      ) : null}
                      {expanded && result ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          {result.contentMd ? (
                            <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>
                              <MarkdownMath value={result.contentMd} />
                            </div>
                          ) : (
                            <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>“{clip(result.exactText, 260)}”</span>
                          )}
                          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                            {result.spanId ? (
                              <button
                                type="button"
                                onClick={() => jumpToSpan(result.spanId!)}
                                style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                              >
                                show the passage
                              </button>
                            ) : null}
                            {proposalOpen && proposalId ? (
                              <>
                                <button
                                  type="button"
                                  onClick={() => void decideProposal(proposalId, "accept")}
                                  disabled={busy}
                                  style={{ border: 0, background: "transparent", color: COLOR.green, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                                >
                                  keep it
                                </button>
                                <button
                                  type="button"
                                  onClick={() => void decideProposal(proposalId, "reject")}
                                  disabled={busy}
                                  style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                                >
                                  dismiss
                                </button>
                              </>
                            ) : proposalId ? (
                              <Faint style={{ fontSize: 10, color: COLOR.green }}>✓ reviewed</Faint>
                            ) : null}
                          </div>
                        </div>
                      ) : null}
                    </Card>
                  );
                })}
                {proposalCount > 0 ? <Faint style={{ fontSize: 10 }}>{proposalCount} idea{proposalCount === 1 ? " is" : "s are"} awaiting your review above.</Faint> : null}
              </div>
            </>
          ) : null}

          {arc ? (
            <>
              <SectionHeader>You’ll see this again</SectionHeader>
              <Card style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                  {arc.paused
                    ? "Paused. This passage will stay saved until you resume."
                    : "Saved. LearnLoop will bring this idea back as short practice and adjust only from your answers."}
                </span>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <SecondaryButton onClick={pauseArc} disabled={arc.paused}>pause reminders</SecondaryButton>
                  <SecondaryButton onClick={() => setArcPolicy("hold_at_target")}>keep it at this level</SecondaryButton>
                  <SecondaryButton onClick={() => setArcPolicy("suggest_next")}>deepen when I’m ready</SecondaryButton>
                </div>
              </Card>
            </>
          ) : null}

          <SectionHeader>Annotations</SectionHeader>
          {annotations.length === 0 ? (
            <Faint style={{ fontSize: 12 }}>no annotations yet.</Faint>
          ) : (
            annotations.map((a, i) => (
              <Card
                key={a.annotationId ?? i}
                onClick={() => jumpToAnnotation(a)}
                style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 6, cursor: a.segments.length ? "pointer" : "default" }}
              >
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                  <Pill color="cyan">{a.kind}</Pill>
                  {a.status === "needs_reanchor" ? <Pill color="amber">anchor needs review</Pill> : <Faint style={{ fontSize: 10 }}>{a.status}</Faint>}
                </div>
                <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>“{clip(a.quote, 180)}”</span>
                {a.status === "needs_reanchor" && a.annotationId && !offline ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }} onClick={(e) => e.stopPropagation()}>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      <button
                        type="button"
                        onClick={() => void reanchorAnnotation(a.annotationId!)}
                        disabled={busy}
                        style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                      >
                        re-anchor to this version
                      </button>
                      {selection ? (
                        <button
                          type="button"
                          onClick={() => void manualAnchorToSelection(a.annotationId!)}
                          disabled={busy}
                          style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                        >
                          anchor to selection
                        </button>
                      ) : null}
                    </div>
                    {reanchorNotes[a.annotationId] ? (
                      <Faint style={{ fontSize: 10 }}>{reanchorNotes[a.annotationId]}</Faint>
                    ) : null}
                  </div>
                ) : null}
                {editingAnnotationId !== null && editingAnnotationId === a.annotationId ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }} onClick={(e) => e.stopPropagation()}>
                    <textarea
                      autoFocus
                      value={editingAnnotationText}
                      onChange={(e) => setEditingAnnotationText(e.target.value)}
                      placeholder="your note…"
                      onKeyDown={(e) => {
                        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") void saveAnnotationEdit();
                        if (e.key === "Escape") setEditingAnnotationId(null);
                      }}
                      style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 54, resize: "vertical" }}
                    />
                    <div style={{ display: "flex", gap: 8 }}>
                      <PrimaryButton onClick={() => void saveAnnotationEdit()} disabled={busy}>save ↵</PrimaryButton>
                      <SecondaryButton onClick={() => setEditingAnnotationId(null)} disabled={busy}>cancel</SecondaryButton>
                    </div>
                  </div>
                ) : (
                  <>
                    {a.learnerText ? <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>{a.learnerText}</span> : null}
                    {a.annotationId && !offline ? (
                      <div style={{ display: "flex", gap: 10 }} onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingAnnotationId(a.annotationId);
                            setEditingAnnotationText(a.learnerText);
                          }}
                          disabled={busy}
                          style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                        >
                          {a.learnerText ? "edit note" : "add note"}
                        </button>
                        <button
                          type="button"
                          onClick={() => void deleteAnnotation(a.annotationId!)}
                          disabled={busy}
                          style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                        >
                          delete
                        </button>
                      </div>
                    ) : null}
                  </>
                )}
              </Card>
            ))
          )}
          </div>

          {/* The boundary question below is fixture content (its text is authored for
              the demo chapter) — it renders only in the offline demo, never over a
              real source it does not belong to. */}
          <div style={{ display: railTab === "guide" ? "block" : "none" }}>
          {offline && boundaryBlock ? (
            <>
              <SectionHeader>Quick check</SectionHeader>
              <Card status="probe" style={{ background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 8 }}>
                <Faint style={{ fontSize: 11 }}>optional · not a test</Faint>
                <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                  Before executing: which decomposition reads off the variance here, and why?
                </span>
                {boundarySkipped ? (
                  <Faint style={{ fontSize: 11 }}>Skipped. Keep reading.</Faint>
                ) : !boundaryAnswered ? (
                  <>
                    <div style={{ display: "flex", gap: 8 }}>
                      <PrimaryButton onClick={() => setBoundaryAnswered(true)}>respond ↵</PrimaryButton>
                      <SecondaryButton onClick={() => { setBoundarySkipped(true); void sendQuestionControl("skip"); }}>skip</SecondaryButton>
                    </div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {QUESTION_CONTROLS.map((option) => (
                        <SecondaryButton key={option.value} onClick={() => sendQuestionControl(option.value)}>{option.label}</SecondaryButton>
                      ))}
                    </div>
                    {questionControl === "i_dont_understand" ? (
                      <Faint style={{ fontSize: 11 }}>Let’s return to the passage that supports this question.</Faint>
                    ) : questionControl ? (
                      <Faint style={{ fontSize: 11 }}>Got it. This changes how quick checks appear for you.</Faint>
                    ) : null}
                  </>
                ) : !boundarySubmitted ? (
                  <>
                    <textarea
                      autoFocus
                      value={boundaryResponse}
                      onChange={(event) => setBoundaryResponse(event.target.value)}
                      onKeyDown={(event) => {
                        if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && boundaryResponse.trim()) {
                          setBoundarySubmitted(true);
                        }
                      }}
                      placeholder="Answer in your own words…"
                      style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 76, resize: "vertical" }}
                    />
                    <div style={{ display: "flex", gap: 8 }}>
                      <PrimaryButton onClick={() => setBoundarySubmitted(true)} disabled={!boundaryResponse.trim()}>record answer · ctrl+↵</PrimaryButton>
                      <SecondaryButton onClick={() => setBoundaryAnswered(false)}>back</SecondaryButton>
                    </div>
                  </>
                ) : (
                  <DispositionPicker value={disposition} onChoose={chooseDisposition} />
                )}
              </Card>
            </>
          ) : null}
          </div>

          <div style={{ display: railTab === "ask" ? "block" : "none" }}>
          <SectionHeader style={{ marginTop: 0 }}>Ask</SectionHeader>
          <Faint style={{ fontSize: 10, display: "block", margin: "2px 0 8px" }}>
            answers now, grounded in the selected passage · background requests live under notes
          </Faint>
          {!enabled ? (
            <Card style={{ borderStyle: "dashed", display: "flex", flexDirection: "column", gap: 6 }}>
              <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
                the reader Ask is disabled in this vault's config (on by default for new vaults). Set <Dim>tutor_qa.reader_enabled = true</Dim> to ask span-grounded questions.
              </Faint>
            </Card>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {activeSpan ? (
                <>
                  {/* The Ask grounding is the SAME selection Capture uses —
                      the learner never targets extraction blocks directly. */}
                  {selection ? (
                    <Card style={{ display: "flex", flexDirection: "column", gap: 4, background: COLOR.bgElev }}>
                      <Faint style={{ fontSize: 10 }}>ASKING ABOUT YOUR SELECTION</Faint>
                      <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                        <MarkdownMath value={clip((selection.editedText ?? selection.quote).replace(/\s+/g, " ").trim(), 300)} />
                      </div>
                    </Card>
                  ) : activeBlock ? (
                    <Card style={{ display: "flex", flexDirection: "column", gap: 4, background: COLOR.bgElev }}>
                      <Faint style={{ fontSize: 10 }}>ASKING ABOUT</Faint>
                      <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                        <MarkdownMath value={clip(activeBlock.markdown.replace(/\s+/g, " "), 150)} />
                      </div>
                    </Card>
                  ) : null}
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Faint style={{ fontSize: 11 }}>mode</Faint>
                    <TermSelect
                      value={answerMode}
                      options={ANSWER_MODE_OPTIONS}
                      onChange={changeAnswerMode}
                      width={160}
                    />
                  </div>
                  <textarea
                    key={`${activeSpan}:${askComposerVersion}`}
                    ref={askComposerRef}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="ask about this passage…"
                    onKeyDown={(e) => {
                      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                        e.preventDefault();
                        void ask();
                      }
                    }}
                    style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 70, resize: "vertical" }}
                  />
                  <PrimaryButton onClick={ask} disabled={busy || !question.trim()}>ask · ctrl+↵</PrimaryButton>
                </>
              ) : (
                <Faint style={{ fontSize: 12 }}>select a passage (drag, or ctrl+drag boxes) to ask about it.</Faint>
              )}

              <SectionHeader>Previous asks</SectionHeader>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Faint style={{ fontSize: 10 }}>{history.length} saved</Faint>
                {!askFindOpen ? (
                  <button
                    type="button"
                    onClick={() => { setAskFindOpen(true); window.setTimeout(() => askFindInputRef.current?.focus(), 0); }}
                    title="find in previous asks (ctrl+f)"
                    aria-label="find in previous asks"
                    style={{ marginLeft: "auto", width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
                  >
                    ⌕
                  </button>
                ) : (
                  <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
                    <input
                      ref={askFindInputRef}
                      value={askFindQuery}
                      onChange={(event) => setAskFindQuery(event.target.value)}
                      placeholder="find in asks…"
                      style={{ width: 170, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, fontFamily: FONT_MONO, fontSize: 11, padding: "4px 6px" }}
                    />
                    <Faint style={{ fontSize: 10 }}>{visibleAskHistory.length}/{history.length}</Faint>
                    <button type="button" onClick={() => { setAskFindOpen(false); setAskFindQuery(""); }} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer", padding: 0 }}>×</button>
                  </div>
                )}
              </div>
              {history.length === 0 ? (
                <Faint style={{ fontSize: 11 }}>No saved asks for this source yet.</Faint>
              ) : visibleAskHistory.length === 0 ? (
                <Faint style={{ fontSize: 11 }}>No questions or answers match “{askFindQuery}”.</Faint>
              ) : visibleAskHistory.map((exchange) => {
                const expanded = normalizedAskFind.length > 0 || !collapsedAskIds.has(exchange.id);
                return (
                  <div key={exchange.id} data-ask-id={exchange.id}>
                  <Card status="running" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <button
                      type="button"
                      onClick={() => setCollapsedAskIds((ids) => {
                        const next = new Set(ids);
                        if (next.has(exchange.id)) next.delete(exchange.id); else next.add(exchange.id);
                        return next;
                      })}
                      aria-expanded={expanded}
                      style={{ display: "flex", alignItems: "baseline", gap: 7, width: "100%", border: 0, background: "transparent", color: COLOR.text, fontFamily: FONT_MONO, padding: 0, textAlign: "left", cursor: "pointer" }}
                    >
                      <span style={{ color: COLOR.purpleText, flexShrink: 0 }}>{expanded ? "▼" : "▶"}</span>
                      {/* The question once (usability round 2: it was printed
                          twice): plain and clipped while collapsed — clipping
                          mid-$ would break KaTeX — and in full, with its maths,
                          when open. */}
                      <span style={{ fontSize: 11, flex: 1 }}>
                        {expanded ? <MarkdownMath value={exchange.question} /> : clip(exchange.question, 130)}
                      </span>
                    </button>
                    {expanded ? (
                      <>
                        <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
                          <Pill color="cyan">{answerModeLabel(exchange.answerMode)}</Pill>
                          <button type="button" onClick={() => jumpToSpan(exchange.spanId)} style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}>show passage</button>
                          {exchange.createdAt ? <Faint style={{ fontSize: 9, marginLeft: "auto" }}>{new Date(exchange.createdAt).toLocaleString()}</Faint> : null}
                        </div>
                        <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                          <MarkdownMath value={exchange.answerMd} />
                        </div>
                      </>
                    ) : null}
                  </Card>
                  </div>
                );
              })}
              <AffectTap />
            </div>
          )}
          </div>
        </div>
      </div>

      {tagMenu ? (
        <div
          style={{ position: "fixed", inset: 0, zIndex: 320 }}
          onClick={() => setTagMenu(null)}
          onContextMenu={(e) => {
            e.preventDefault();
            setTagMenu(null);
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: "fixed",
              left: Math.min(tagMenu.x, window.innerWidth - 210),
              top: Math.min(tagMenu.y, window.innerHeight - 220),
              minWidth: 190,
              background: COLOR.bg,
              border: `1px solid ${COLOR.borderStrong}`,
              boxShadow: "0 16px 48px rgba(0,0,0,0.55)",
              fontFamily: FONT_MONO,
            }}
          >
            <div style={{ padding: "7px 12px", fontSize: 10, color: COLOR.textFaint, borderBottom: `1px solid ${COLOR.border}`, maxWidth: 260 }}>
              tag {tagMenu.quote !== null ? `“${clip(tagMenu.quote, 48)}”` : "whole block"} as
            </div>
            {TAG_ACTIONS.map((t) => (
              <div
                key={t.action}
                onClick={() => void tagCapture(t.action, tagMenu)}
                onMouseEnter={(e) => (e.currentTarget.style.background = COLOR.bgInput)}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                style={{ padding: "8px 12px", fontSize: 12, color: COLOR.text, cursor: "pointer" }}
              >
                {t.label}
              </div>
            ))}
            {pdfView && !offline && surface !== "pdf" ? (
              <div
                onClick={() => {
                  setReadingSpan(tagMenu.spanId);
                  setActiveSpan(tagMenu.spanId);
                  setSurface("pdf");
                  setTagMenu(null);
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = COLOR.bgInput)}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                style={{ padding: "8px 12px", fontSize: 12, color: COLOR.textDim, cursor: "pointer", borderTop: `1px solid ${COLOR.border}` }}
              >
                view original →
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      <KeyBar keys={readerKeyBarKeys(pdfSurfaceActive)} right={{ key: "^p", label: "palette" }} />
    </div>
  );
}

function SectionBoundaryOffer({
  section,
  allowQuestion,
  onOpen,
  onReveal,
  onDismiss,
}: {
  section: ReaderGuideSectionDto;
  allowQuestion: boolean;
  onOpen: () => void;
  onReveal: () => void;
  onDismiss: () => void;
}) {
  return (
    <Card status="probe" style={{ margin: "8px 0 18px", padding: 14, background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <Pill color="purple">section break</Pill>
        <Faint style={{ fontSize: 10 }}>optional · usually under a minute</Faint>
      </div>
      <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
        {allowQuestion && section.question
          ? `Before moving on, would you like to check what landed from “${section.label}”?`
          : `A few passages from “${section.label}” may be worth another look.`}
      </span>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {allowQuestion && section.question ? <PrimaryButton onClick={onOpen}>quick check →</PrimaryButton> : null}
        {section.suggestedPassages.length > 0 ? (
          <SecondaryButton onClick={onReveal}>
            show {section.suggestedPassages.length} passage{section.suggestedPassages.length === 1 ? "" : "s"} I may have missed
          </SecondaryButton>
        ) : null}
        <SecondaryButton onClick={onDismiss}>keep reading</SecondaryButton>
      </div>
    </Card>
  );
}

function AuthoredQuestionCard({
  section,
  autoStart = false,
  onJump,
  onDismiss,
  onComplete,
  onAnswered,
  onError,
}: {
  section: ReaderGuideSectionDto;
  /** Opened from a section break: start at once, ready to answer. */
  autoStart?: boolean;
  onJump: (spanId: string) => void;
  onDismiss: () => void;
  onComplete: () => void;
  /** The learner compared their answer (the guide stops calling it waiting). */
  onAnswered?: () => void;
  onError: (message: string) => void;
}) {
  const question = section.question;
  const [started, setStarted] = useState(false);
  const [response, setResponse] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [escalatedItemId, setEscalatedItemId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const questionId = question?.authoredQuestionId ?? null;
  const sourceSpan = question?.spanIds?.[0] ?? null;
  useEffect(() => {
    if (autoStart) setStarted(true);
  }, [autoStart]);

  const submit = useCallback(async () => {
    if (!questionId || !response.trim()) return;
    setBusy(true);
    try {
      await api.readerAuthoredQuestionAction({ questionId, action: "answered", response: response.trim() });
      setSubmitted(true);
      onAnswered?.();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [questionId, response, onError, onAnswered]);

  const dismissForever = useCallback(async () => {
    if (!questionId) return;
    setBusy(true);
    try {
      await api.readerAuthoredQuestionAction({ questionId, action: "dismissed" });
      onDismiss();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [questionId, onDismiss, onError]);

  const escalate = useCallback(async () => {
    if (!questionId || !question?.escalationLearningObjectId) return;
    setBusy(true);
    try {
      const result = await api.readerEscalateAuthoredQuestion({
        questionId,
        learningObjectId: question.escalationLearningObjectId,
      });
      setEscalatedItemId(result.practiceItemId);
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [questionId, question, onError]);

  if (!question) return null;

  return (
    <Card status="probe" style={{ marginTop: 10, background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 9 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
        <Pill color="purple">quick check</Pill>
        <Pill color="slate">AI-written</Pill>
        <Faint style={{ fontSize: 10 }}>optional · self-check, never a grade</Faint>
      </div>
      <Faint style={{ fontSize: 10, lineHeight: 1.5 }}>{question.reason}</Faint>
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>
        <MarkdownMath value={question.prompt} />
      </div>
      {!started ? (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <PrimaryButton onClick={() => setStarted(true)}>think it through →</PrimaryButton>
          <SecondaryButton onClick={onDismiss}>keep reading</SecondaryButton>
        </div>
      ) : !submitted ? (
        <>
          <textarea
            autoFocus
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Answer in your own words…"
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") void submit();
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 82, resize: "vertical" }}
          />
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {/* Enter is a new line (answers can need several); the button
                names the key that really sends (usability round 1, U6). */}
            <PrimaryButton onClick={() => void submit()} disabled={busy || !response.trim()}>compare with the source · ctrl+↵</PrimaryButton>
            <SecondaryButton onClick={onDismiss} disabled={busy}>skip</SecondaryButton>
          </div>
        </>
      ) : (
        <>
          {/* The learner's own answer stays beside the intended one: there is
              something to compare (usability round 1, U6). */}
          <div style={{ borderLeft: `3px solid ${COLOR.border}`, paddingLeft: 10, display: "flex", flexDirection: "column", gap: 4 }}>
            <Faint style={{ fontSize: 10, letterSpacing: "0.1em" }}>YOUR ANSWER</Faint>
            <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{response.trim()}</div>
          </div>
          <div style={{ borderLeft: `3px solid ${COLOR.green}`, paddingLeft: 10, display: "flex", flexDirection: "column", gap: 4 }}>
            <Faint style={{ fontSize: 10, letterSpacing: "0.1em" }}>INTENDED ANSWER — COMPARE, DON’T GRADE</Faint>
            <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>
              <MarkdownMath value={question.expectedAnswer ?? ""} />
            </div>
          </div>
          {escalatedItemId ? (
            <Faint style={{ fontSize: 11, color: COLOR.green }}>✓ Added to your practice collection.</Faint>
          ) : null}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {!escalatedItemId && question.escalationLearningObjectId ? (
              <PrimaryButton onClick={() => void escalate()} disabled={busy}>add to practice →</PrimaryButton>
            ) : null}
            <SecondaryButton onClick={onComplete}>done for now</SecondaryButton>
          </div>
        </>
      )}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 2 }}>
        {sourceSpan ? (
          <button
            type="button"
            onClick={() => onJump(sourceSpan)}
            disabled={busy}
            style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
          >
            show me the passage
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => void dismissForever()}
          disabled={busy}
          style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
        >
          don’t bring this back
        </button>
      </div>
    </Card>
  );
}

function SectionQuestionCard({
  section,
  autoStart = false,
  extractionId,
  onReveal,
  onJump,
  onDismiss,
  onComplete,
  onAnswered,
  onError,
}: {
  section: ReaderGuideSectionDto;
  /** Opened from a section break: start at once, ready to answer. */
  autoStart?: boolean;
  extractionId: string;
  onReveal: () => void;
  onJump: (spanId: string) => void;
  onDismiss: () => void;
  onComplete: () => void;
  /** The learner's answer was recorded (the guide stops calling it waiting). */
  onAnswered?: () => void;
  onError: (message: string) => void;
}) {
  const question = section.question;
  const [administrationId, setAdministrationId] = useState<string | null>(null);
  const [response, setResponse] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [disposition, setDisposition] = useState<ReaderDisposition | null>(null);
  const [busy, setBusy] = useState(false);
  const [controlMessage, setControlMessage] = useState<string | null>(null);

  const begin = useCallback(async () => {
    if (!question?.practiceItemId || administrationId) return;
    setBusy(true);
    try {
      const opened = await api.readerPresentQuestion({
        practiceItemId: question.practiceItemId,
        readingPhase: question.readingPhase,
        goalId: question.goalId,
        targetContractVersionId: question.targetContractVersionId,
      });
      setAdministrationId(String(opened.administrationId ?? ""));
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [question, administrationId, onError]);

  useEffect(() => {
    if (autoStart) void begin();
    // Only the request to open it starts it; begin() itself is idempotent.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart]);

  const submit = useCallback(async () => {
    if (!administrationId || !response.trim()) return;
    setBusy(true);
    try {
      await api.readerSubmitQuestion({
        administrationId,
        response: response.trim(),
        targetKey: question?.targetContractVersionId ?? undefined,
        outcomeClass: "unknown",
      });
      setSubmitted(true);
      onAnswered?.();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [administrationId, response, question, onError, onAnswered]);

  const skip = useCallback(async () => {
    try {
      if (administrationId) {
        await api.readerSkipQuestion(administrationId);
      } else if (question?.placementEventId) {
        await api.readerQuestionControl({
          control: "skip",
          subjectId: question.placementEventId,
          subjectType: "reader_question_placement",
        });
      }
    } catch (error) {
      onError(errorMessage(error));
      return;
    }
    onDismiss();
  }, [administrationId, question, onDismiss, onError]);

  const control = useCallback(async (value: string) => {
    if (!question?.placementEventId) return;
    setBusy(true);
    try {
      await api.readerQuestionControl({
        control: value,
        administrationId,
        subjectId: question.placementEventId,
        subjectType: "reader_question_placement",
      });
      if (value === "i_dont_understand") {
        setControlMessage("Let’s return to the passage that best supports this question.");
        if (section.suggestedPassages[0]) {
          await api.readerRestoreSource({
            extractionId,
            spanId: section.suggestedPassages[0].spanId,
          });
          onReveal();
          onJump(section.suggestedPassages[0].spanId);
        }
      } else if (value === "ask_me_differently") {
        setControlMessage("Got it. We’ll vary the wording next time; you can keep reading now.");
      } else {
        setControlMessage("Got it. This only changes how checks appear for you.");
      }
      if (["too_easy", "too_intrusive", "dont_bring_this_back"].includes(value)) onDismiss();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [question, administrationId, section.suggestedPassages, extractionId, onReveal, onJump, onDismiss, onError]);

  const choose = useCallback(async (next: ReaderDisposition) => {
    if (!question?.learningObjectId) return;
    setDisposition(next);
    try {
      await api.readerChooseDisposition({
        disposition: next,
        subjectId: question.learningObjectId,
        subjectType: "learning_object",
        goalId: question.goalId,
      });
      onComplete();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [question, onComplete, onError]);

  if (!question) {
    return section.suggestedPassages.length > 0 ? (
      <Card status="probe" style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8, background: COLOR.washPurple }}>
        <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>Take a quick second pass before moving on?</span>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <PrimaryButton onClick={onReveal}>show important passages</PrimaryButton>
          <SecondaryButton onClick={onDismiss}>not now</SecondaryButton>
        </div>
      </Card>
    ) : null;
  }

  return (
    <Card status="probe" style={{ marginTop: 10, background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 9 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
        <Pill color="purple">quick check</Pill>
        {question.goalTitle ? <Pill color="cyan">for {question.goalTitle}</Pill> : null}
        <Faint style={{ fontSize: 10 }}>optional · not a test</Faint>
      </div>
      <Faint style={{ fontSize: 10, lineHeight: 1.5 }}>{question.reason}</Faint>
      <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text, lineHeight: 1.6 }}>
        <MarkdownMath value={question.prompt} />
      </div>
      {!administrationId ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <PrimaryButton onClick={() => void begin()} disabled={busy}>think it through →</PrimaryButton>
            <SecondaryButton onClick={() => void skip()} disabled={busy}>keep reading</SecondaryButton>
          </div>
          {section.suggestedPassages.length > 0 ? (
            <SecondaryButton onClick={() => {
              onReveal();
              onJump(section.suggestedPassages[0].spanId);
            }}>
              show the most relevant passage first
            </SecondaryButton>
          ) : null}
        </div>
      ) : !submitted ? (
        <>
          <textarea
            autoFocus
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Answer in your own words…"
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") void submit();
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 82, resize: "vertical" }}
          />
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <PrimaryButton onClick={() => void submit()} disabled={busy || !response.trim()}>record answer · ctrl+↵</PrimaryButton>
            <SecondaryButton onClick={() => void skip()} disabled={busy}>skip</SecondaryButton>
          </div>
        </>
      ) : (
        <>
          <Faint style={{ fontSize: 11, color: COLOR.green }}>✓ Answer recorded. This was for understanding, not a grade.</Faint>
          <Faint style={{ fontSize: 10 }}>What should LearnLoop do with this idea?</Faint>
          <DispositionPicker value={disposition} onChoose={(next) => void choose(next)} />
          <SecondaryButton onClick={onComplete}>done for now</SecondaryButton>
        </>
      )}
      {!submitted ? (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 2 }}>
          {QUESTION_CONTROLS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => void control(option.value)}
              disabled={busy}
              style={{ border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : null}
      {controlMessage ? <Faint style={{ fontSize: 10 }}>{controlMessage}</Faint> : null}
    </Card>
  );
}

// ── YouTube watch mode (owner request 2026-07-20) ───────────────────────────
// Embedded privacy-enhanced player (CSP already allows youtube-nocookie.com;
// controlled via the widget postMessage protocol — no external script). Playback
// drives the transcript position; the learner may pause and ask at any moment.
// Reviewed section checks remain in the stable Guide rail and never interrupt
// playback on their own.

const YT_ORIGIN = "https://www.youtube-nocookie.com";

function parseTimeLocator(value?: string | null): [number, number] | null {
  if (!value) return null;
  const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim());
  return match ? [parseFloat(match[1]), parseFloat(match[2])] : null;
}

function formatClock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const sec = total % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}` : `${m}:${String(sec).padStart(2, "0")}`;
}

interface TranscriptCue {
  block: ReaderRenderBlockDto;
  start: number;
  end: number;
}

interface TranscriptSection {
  cues: TranscriptCue[];
  start: number;
  end: number;
  characters: number;
}

// Raw YouTube captions are often only a few words long. Keep their individual
// spans for timing, seeking, and annotation, but render adjacent cues together
// as readable transcript paragraphs.
function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[] {
  const sections: TranscriptSection[] = [];
  for (const cue of cues) {
    const textLength = cue.block.markdown.trim().length;
    const current = sections[sections.length - 1];
    if (!current) {
      sections.push({ cues: [cue], start: cue.start, end: cue.end, characters: textLength });
      continue;
    }

    const previous = current.cues[current.cues.length - 1];
    const gap = cue.start - previous.end;
    const projectedDuration = Math.max(current.end, cue.end) - current.start;
    const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim());
    const shouldStartSection =
      gap >= 3 ||
      projectedDuration > 18 ||
      current.characters + textLength + 1 > 260 ||
      (previous.end - current.start >= 10 && previousEndsSentence);

    if (shouldStartSection) {
      sections.push({ cues: [cue], start: cue.start, end: cue.end, characters: textLength });
      continue;
    }
    current.cues.push(cue);
    current.end = Math.max(current.end, cue.end);
    current.characters += textLength + 1;
  }
  return sections;
}

export interface WatchPanelHandle {
  /** Seek the video (and transcript) to the cue backing a span id. */
  seekToSpan: (spanId: string) => boolean;
}

const YouTubeWatchPanel = forwardRef<WatchPanelHandle, {
  plan: ReaderWatchPlanDto;
  blocks: ReaderRenderBlockDto[];
  annotatedSpans: Set<string>;
  guidanceSpans: Set<string>;
  resumeSpan: string | null;
  findShortcutEnabled: boolean;
  /** The cue playback is at; ``advancing`` is false for a seek's landing
   *  and while the player is paused (only playing on is watching). */
  onPlaybackSpan: (spanId: string | null, advancing: boolean) => void;
  onAskSpan: (spanId: string | null) => void;
  onTagMenu: (request: TagMenuRequest) => void;
}>(function YouTubeWatchPanel({
  plan,
  blocks,
  annotatedSpans,
  guidanceSpans,
  resumeSpan,
  findShortcutEnabled,
  onPlaybackSpan,
  onAskSpan,
  onTagMenu,
}, ref) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [followTranscript, setFollowTranscript] = useState(true);
  const [playerReady, setPlayerReady] = useState(false);
  const resumeSpanRef = useRef(resumeSpan);
  // Whether the player is playing (YouTube's playerState 1), once it says;
  // and until when a seek's landing (and the late reports around it) is not
  // playback.
  const playingRef = useRef<boolean | null>(null);
  const seekUntilRef = useRef(0);
  const noteSeek = useCallback(() => {
    seekUntilRef.current = Date.now() + SEEN_SETTLE_MS;
  }, []);
  // ctrl/cmd+F transcript find (mirrors the PDF pane's find conventions).
  const [findOpen, setFindOpen] = useState(false);
  const [findQuery, setFindQuery] = useState("");
  const [matchIdx, setMatchIdx] = useState(0);
  const findInputRef = useRef<HTMLInputElement | null>(null);

  const transcriptCues = useMemo<TranscriptCue[]>(() => {
    const cues: TranscriptCue[] = [];
    for (const block of blocks) {
      const range = parseTimeLocator(block.extractorBlockId);
      if (!range || !block.spanId) continue;
      cues.push({ block, start: range[0], end: range[1] });
    }
    return cues.sort((a, b) => a.start - b.start || a.end - b.end);
  }, [blocks]);

  const transcriptSections = useMemo(() => groupTranscriptCues(transcriptCues), [transcriptCues]);

  const activeCue = useMemo(() => {
    let active: TranscriptCue | null = null;
    // Auto-generated captions commonly overlap. The previous implementation
    // stopped at the first cue whose end still covered the playback time, which
    // left an older phrase highlighted while a newer one was being spoken.
    // The cue with the latest start at/before playback is the visible phrase.
    for (const cue of transcriptCues) {
      if (cue.start > currentTime + 0.15) break;
      active = cue;
    }
    return active;
  }, [transcriptCues, currentTime]);

  const post = useCallback((func: string, args: unknown[] = []) => {
    iframeRef.current?.contentWindow?.postMessage(JSON.stringify({ event: "command", func, args }), YT_ORIGIN);
  }, []);

  // Widget handshake: subscribing makes the iframe stream infoDelivery
  // (currentTime / playerState) back to this window.
  const handshake = useCallback(() => {
    iframeRef.current?.contentWindow?.postMessage(JSON.stringify({ event: "listening", id: "llwatch", channel: "widget" }), YT_ORIGIN);
    const resumeCue = transcriptCues.find((cue) => cue.block.spanId === resumeSpanRef.current);
    if (resumeCue && resumeCue.start > 0) {
      noteSeek();
      post("seekTo", [resumeCue.start, true]);
      setCurrentTime(resumeCue.start);
    }
    setPlayerReady(true);
  }, [post, transcriptCues, noteSeek]);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (event.origin !== YT_ORIGIN) return;
      let data: { event?: string; info?: number | { currentTime?: number; playerState?: number } };
      try {
        data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      } catch {
        return;
      }
      // The widget reports only what changed: the player's state when it
      // changes (also as onStateChange), the time as it moves.
      if (data?.event === "onStateChange" && typeof data.info === "number") {
        playingRef.current = data.info === 1;
      }
      if (data?.event === "infoDelivery" && typeof data.info === "object" && data.info !== null) {
        if (typeof data.info.playerState === "number") playingRef.current = data.info.playerState === 1;
        if (typeof data.info.currentTime === "number") setCurrentTime(data.info.currentTime);
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  // Keep playback anchored in a dedicated transcript scroller, rather than
  // scrolling the whole Reader and pushing the video out of view. A learner who
  // wheels/touches the transcript pauses follow-mode until they explicitly
  // resume it.
  useEffect(() => {
    if (!playerReady) return;
    const spanId = activeCue?.block.spanId ?? null;
    onPlaybackSpan(spanId, playingRef.current !== false && Date.now() >= seekUntilRef.current);
    if (!spanId || !followTranscript) return;
    const scroller = transcriptRef.current;
    const cue = scroller?.querySelector(`[data-transcript-span="${spanId}"]`);
    if (!(scroller instanceof HTMLElement) || !(cue instanceof HTMLElement)) return;
    // offsetTop is measured from the cue's offset parent, which is not
    // necessarily this scroller. Mixing that document-relative value with the
    // scroller's height can jump past the active caption into later ones. Use
    // viewport-relative rectangles to derive the cue's position inside the
    // scroller, then place its center at the scroller's midpoint.
    const scrollerRect = scroller.getBoundingClientRect();
    const cueRect = cue.getBoundingClientRect();
    const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2;
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }, [activeCue, followTranscript, onPlaybackSpan, playerReady]);

  // Map playback time → the caption span whose cue window contains it (cue
  // t= locators stamped by captions_to_ir v2 / transcript_to_ir).
  const pauseAndAsk = useCallback(() => {
    post("pauseVideo");
    let best: string | null = null;
    for (const block of blocks) {
      const range = parseTimeLocator(block.extractorBlockId);
      if (!range || !block.spanId) continue;
      if (range[0] <= currentTime) best = block.spanId;
      else break;
    }
    onAskSpan(best ?? blocks.find((b) => b.spanId)?.spanId ?? null);
  }, [blocks, currentTime, onAskSpan, post]);

  const seekToCue = useCallback((cue: TranscriptCue) => {
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed) return;
    noteSeek();
    post("seekTo", [cue.start, true]);
    post("playVideo");
    setFollowTranscript(true);
    onAskSpan(cue.block.spanId);
  }, [onAskSpan, post, noteSeek]);

  // ── transcript find ──
  const findNeedle = findQuery.trim().toLowerCase();
  const findMatches = useMemo(() => {
    if (!findOpen || findNeedle.length < 2) return [];
    return transcriptCues.filter((cue) =>
      (cue.block.markdown ?? "").toLowerCase().includes(findNeedle),
    );
  }, [transcriptCues, findOpen, findNeedle]);

  useEffect(() => {
    setMatchIdx(0);
  }, [findNeedle]);

  const scrollToFindMatch = useCallback((index: number) => {
    const cue = findMatches[index];
    const scroller = transcriptRef.current;
    if (!cue || !scroller) return;
    // Searching is scanning, not watching: stop follow so the scroller stays
    // on the hit. Clicking a hit cue still seeks the video as usual.
    setFollowTranscript(false);
    const el = scroller.querySelector(`[data-transcript-span="${cue.block.spanId}"]`);
    if (!(el instanceof HTMLElement)) return;
    const scrollerRect = scroller.getBoundingClientRect();
    const rect = el.getBoundingClientRect();
    const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2;
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }, [findMatches]);

  const gotoFindMatch = useCallback((delta: number) => {
    if (!findMatches.length) return;
    setMatchIdx((i) => (i + delta + findMatches.length) % findMatches.length);
  }, [findMatches]);

  useEffect(() => {
    if (findOpen && findMatches.length) scrollToFindMatch(matchIdx);
  }, [findOpen, findMatches, matchIdx, scrollToFindMatch]);

  const openFind = useCallback(() => {
    setFindOpen(true);
    window.setTimeout(() => findInputRef.current?.focus(), 0);
  }, []);

  const closeFind = useCallback(() => {
    setFindOpen(false);
    setFindQuery("");
  }, []);

  useEffect(() => {
    if (!findShortcutEnabled) return;
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
        event.preventDefault();
        openFind();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [findShortcutEnabled, openFind]);

  // Imperative jump for the guide rail (contents outline, quick-check "show me
  // the passage", suggested passages): seek the video to the cue's start
  // without forcing playback, and resume transcript follow so the scroller
  // lands on it. Returns false when the span is not a transcript cue.
  useImperativeHandle(ref, () => ({
    seekToSpan: (spanId: string) => {
      const cue = transcriptCues.find((c) => c.block.spanId === spanId);
      if (!cue) return false;
      noteSeek();
      post("seekTo", [cue.start, true]);
      setCurrentTime(cue.start);
      setFollowTranscript(true);
      return true;
    },
  }), [transcriptCues, post, noteSeek]);

  return (
    <Card style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <Pill color="cyan">watch mode</Pill>
        <Meta>{plan.videoId}</Meta>
        <Faint style={{ fontSize: 11 }}>{formatClock(currentTime)}</Faint>
        <span style={{ marginLeft: "auto" }}>
          <SecondaryButton onClick={pauseAndAsk}>pause &amp; ask about this moment</SecondaryButton>
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 10, alignItems: "start" }}>
        <iframe
          ref={iframeRef}
          src={plan.embedUrl}
          title={`watch ${plan.videoId}`}
          style={{ width: "100%", aspectRatio: "16 / 9", border: 0, background: "#000" }}
          allow="encrypted-media; picture-in-picture"
          onLoad={handshake}
        />
        <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgInput }}>
        <div style={{ height: 30, padding: "0 10px", display: "flex", alignItems: "center", gap: 8, borderBottom: `1px solid ${COLOR.border}` }}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>TRANSCRIPT</Faint>
          <Faint style={{ fontSize: 10 }}>{transcriptSections.length} passages</Faint>
          {findOpen ? (
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
              <input
                ref={findInputRef}
                value={findQuery}
                onChange={(event) => setFindQuery(event.target.value)}
                placeholder="find in transcript…"
                onKeyDown={(event) => {
                  if (event.key === "Enter") gotoFindMatch(event.shiftKey ? -1 : 1);
                  if (event.key === "Escape") {
                    event.stopPropagation();
                    closeFind();
                  }
                }}
                style={{ fontFamily: FONT_MONO, fontSize: 11, width: 150, background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "2px 6px" }}
              />
              <Faint style={{ fontSize: 10 }}>{findMatches.length ? `${matchIdx + 1}/${findMatches.length}` : "0/0"}</Faint>
              {([["↑", () => gotoFindMatch(-1)], ["↓", () => gotoFindMatch(1)], ["✕", closeFind]] as Array<[string, () => void]>).map(([label, onClick]) => (
                <button
                  key={label}
                  type="button"
                  onClick={onClick}
                  style={{ width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", padding: 0 }}
                >
                  {label}
                </button>
              ))}
            </div>
          ) : (
            <button
              type="button"
              onClick={openFind}
              title="find in transcript (ctrl+f)"
              style={{ marginLeft: "auto", width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
            >
              ⌕
            </button>
          )}
          <button
            type="button"
            onClick={() => setFollowTranscript((value) => !value)}
            aria-pressed={followTranscript}
            style={{ marginLeft: findOpen ? 0 : 8, border: 0, background: "transparent", color: followTranscript ? COLOR.green : COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", padding: 0 }}
          >
            {followTranscript ? "● following video" : "○ resume follow"}
          </button>
        </div>
        <div
          ref={transcriptRef}
          className="ll-scroll"
          tabIndex={0}
          onWheel={() => setFollowTranscript(false)}
          onTouchStart={() => setFollowTranscript(false)}
          onMouseDown={() => setFollowTranscript(false)}
          onKeyDown={(event) => {
            if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End"].includes(event.key)) setFollowTranscript(false);
          }}
          style={{ maxHeight: 230, overflowY: "auto", scrollBehavior: "smooth", padding: "8px 0" }}
          aria-live="off"
        >
          {transcriptCues.length === 0 ? (
            <Faint style={{ display: "block", padding: "10px 12px", fontSize: 11 }}>No timestamped transcript was extracted for this video.</Faint>
          ) : transcriptSections.map((section) => {
            const activeSpanId = activeCue?.block.spanId;
            const active = section.cues.some((cue) => cue.block.spanId === activeSpanId);
            const annotated = section.cues.some((cue) => annotatedSpans.has(cue.block.spanId ?? ""));
            const guided = section.cues.some((cue) => guidanceSpans.has(cue.block.spanId ?? ""));
            const sectionKey = section.cues[0].block.spanId ?? `t-${section.start}`;
            return (
              <div
                key={sectionKey}
                aria-label={`Transcript from ${formatClock(section.start)} to ${formatClock(section.end)}`}
                style={{ display: "grid", gridTemplateColumns: "48px minmax(0, 1fr)", gap: 8, padding: "8px 10px", borderLeft: `3px solid ${active ? COLOR.amber : annotated ? COLOR.greenSoft : guided ? COLOR.purplePill : "transparent"}`, background: guided && !active ? COLOR.washPurple : "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, lineHeight: 1.65 }}
              >
                <span style={{ color: active ? COLOR.amberLink : COLOR.textFaint }}>{formatClock(section.start)}</span>
                <span>
                  {section.cues.map((cue, index) => {
                    const spanId = cue.block.spanId ?? "";
                    const cueActive = activeSpanId === spanId;
                    const cueAnnotated = annotatedSpans.has(spanId);
                    const cueGuided = guidanceSpans.has(spanId);
                    const cueFindHit = findOpen && findNeedle.length >= 2
                      && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle);
                    const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId;
                    return (
                      <Fragment key={spanId}>
                        <span
                          data-span-id={spanId}
                          data-transcript-span={spanId}
                          onClick={() => seekToCue(cue)}
                          onContextMenu={(event) => {
                            event.preventDefault();
                            const sel = window.getSelection();
                            const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : "";
                            onTagMenu({ x: event.clientX, y: event.clientY, spanId, quote: quote || null });
                          }}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              seekToCue(cue);
                            }
                          }}
                          style={{ cursor: "pointer", padding: "1px 2px", background: cueFindHit ? "rgba(255, 213, 79, 0.18)" : cueActive ? COLOR.washAmber : cueGuided ? COLOR.washPurple : "transparent", outline: cueCurrentFind ? `1px solid ${COLOR.amber}` : undefined, color: cueActive || cueFindHit ? COLOR.text : COLOR.textDim, borderBottom: cueAnnotated ? `1px solid ${COLOR.greenSoft}` : "1px solid transparent", boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone" }}
                        >
                          {cue.block.markdown}
                        </span>
                        {index < section.cues.length - 1 ? " " : null}
                      </Fragment>
                    );
                  })}
                </span>
              </div>
            );
          })}
        </div>
        </div>
      </div>
    </Card>
  );
});
