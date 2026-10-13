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
  InquiryResolution,
  InquirySelfCheck,
  ReaderInquiryQuestionDto,
  ReaderPromptContractDto,
  ReaderRenderBlockDto,
  ReaderRenderViewDto,
  ReaderSourceSearchDto,
  ReaderWatchPlanDto,
  ReaderArcDto,
  ReaderCoachLintDto,
  SourceLibraryCard,
} from "../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, TermSelect } from "../components/term";
import { MarkdownMath } from "../render/MarkdownMath";
import { SecondaryButton } from "../components/goldenpath/shared";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { youtubeVideoId } from "../components/sourceTail";
import { PdfReaderPane, type PassageAlign, type PdfReaderPaneHandle, type TagMenuRequest } from "../components/PdfReaderPane";
import { RectUnionOverlay } from "../components/RectUnionOverlay";
import { errorMessage } from "../errors";
import { type AuthoredQuestionStatus } from "./reader/authoredQuestion";
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
import { useBareAltClear } from "./reader/bareAlt";
import { useReaderRequests } from "./reader/useReaderRequests";

import { type InquiryCommitment, type ReaderExchange } from "./reader/ReaderAskBranches";
import { DetourStrip } from "./reader/DetourStrip";
import { InquiryQuickCheck } from "./reader/InquiryQuickCheck";
import { checkOffer, type CheckSurface } from "./reader/checkOffer";
import { phaseForError, type ModelActionPhase } from "./reader/ModelActionState";
import { ReconnectLine } from "./reader/ReconnectLine";
import {
  activitySince,
  flushReaderActivity,
  learnerActivitySnapshot,
  logReaderAction,
  logReaderActivity,
  newActivityId,
  noteLearnerActivity,
  setReaderActivityEnabled,
} from "./reader/activity";
import {
  back as stackBack,
  EMPTY_STACK,
  forward as stackForward,
  goTo as stackGoTo,
  hasDetour,
  markReturned,
  pushDetour,
  stackInquiryExchange,
  unreturnedDetours,
  type ReturnEntry,
  type ReturnStack,
} from "./reader/returnStack";
import { AskRail } from "./reader/AskRail";
import { GuideRail, SectionBoundaryOffer } from "./reader/GuideRail";
import { NotesRail, type ExerciseImportState } from "./reader/NotesRail";
import {
  clip,
  selectionNodes,
  type AnnotationSegment,
  type MarginAnnotation,
  type ReaderSelection,
} from "./reader/readerShared";

const READER_MODE_OPTIONS = [
  { value: "skim", label: "skim quickly" },
  { value: "anchor", label: "read closely" },
  { value: "incremental", label: "mark for later" },
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

// The passage quick check's poll (F4): every 3 s for at most 10 minutes (the
// Codex turn timeout is 8), then it fails as timed out.
const INQUIRY_CHECK_POLL_MS = 3000;
const INQUIRY_CHECK_MAX_POLLS = 200;

/** The failed line for a spend refusal, by which limit stopped it (re-review
 *  F15): no price set for a metered model, or over the per-check limit. */
function spendRefusalLine(refusal: string | null | undefined): string {
  if (refusal === "no_price") return "Couldn't write a quick check: no price is set for this model, so LearnLoop won't spend on it.";
  if (refusal === "over_cap") return "Couldn't write a quick check: it would cost more than the spending limit for one quick check, so LearnLoop didn't send it.";
  return "Couldn't write a quick check: a spending limit stopped it before it was sent.";
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
  const [selection, setSelection] = useState<ReaderSelection | null>(null);
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
  // A scroll of the learner's own, waiting for the frame that reads where it
  // took them (``onReadingScroll``).
  const movedPendingRef = useRef(false);
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
  // RW1a branches: the exchange a follow-up continues (null starts a new root).
  const [parentExchange, setParentExchange] = useState<ReaderExchange | null>(null);
  const askEpoch = useRef(0);
  const askPending = useRef(false);
  useEffect(() => () => { askEpoch.current += 1; }, []);
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
  const [exerciseImport, setExerciseImport] = useState<ExerciseImportState | null>(null);
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
  // RW1a (reader_inquiry): the return stack and its detour strip; the
  // reconnect line; each inquiry's passage-scoped quick check; the root
  // commitments made from the status chips; a static "•" on the Ask tab
  // when something lands there while the learner is elsewhere.
  const [returnStack, setReturnStack] = useState<ReturnStack>(EMPTY_STACK);
  const returnStackRef = useRef<ReturnStack>(EMPTY_STACK);
  returnStackRef.current = returnStack;
  const lastSourceRef = useRef<ReturnEntry | null>(null);
  // RW1a's switch, readable from callbacks declared before it is (openSource).
  const inquiryRef = useRef(false);
  const settleScrollRef = useRef<number | null>(null);
  const [reconnect, setReconnect] = useState<{
    rootId: string;
    question: string;
    spanId: string;
    inline: boolean;
  } | null>(null);
  // Scroll baselines for "a screen of scrolling" (the reconnect line goes, a
  // walked-back detour settles). An explicit jump moves the page itself, so
  // for a moment after one the baselines follow the page instead of counting.
  const reconnectBaseRef = useRef(0);
  const jumpGuardRef = useRef(0);
  const [inquiryChecks, setInquiryChecks] = useState<Record<string, {
    phase: ModelActionPhase;
    question: ReaderInquiryQuestionDto | null;
    escalated?: boolean;
    /** The durable job writing it (reader.reconnect_answer's batch). */
    batchId?: string | null;
    /** This client wait's generation: a retry can get the same live batch
     *  back, so a poll settles or updates only its own wait (F14). */
    waitId?: string | null;
    /** Polls so far, and rejected polls in a row (the sidecar unreachable). */
    attempts?: number;
    pollErrors?: number;
    /** A failure said in the learner's terms (the failed state's line). */
    failure?: string | null;
  }>>({});
  // The funnel record of each queued quick check (F8): its batch, the visit
  // that asked, when, and the learner's activity snapshot for the wait; and
  // the client wait now watching it (only that wait may settle it).
  const inquiryJobsRef = useRef<Record<string, {
    batchId: string;
    waitId: string;
    startedAt: number;
    activity: ReturnType<typeof learnerActivitySnapshot>;
    visit: { visit_id: string | null; extraction_id: string | null };
  }>>({});
  const [inquiryCommitments, setInquiryCommitments] = useState<Record<string, InquiryCommitment[]>>({});
  const [askTabMarked, setAskTabMarked] = useState(false);
  const [railCollapsed, setRailCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem("learnloop.reader.rail-collapsed") === "on";
    } catch {
      return false;
    }
  });
  // The funnel's visit, the pending "back to reading" after a usable result,
  // and the LearnLoop-started elements already counted this visit.
  const visitRef = useRef<{ id: string; extractionId: string; openedAt: number; lastActive: number; active: number; idle: number } | null>(null);
  const backToReadingRef = useRef<{ jobId: string; actionKind: string; at: number } | null>(null);
  const proactiveSeenRef = useRef<Set<string>>(new Set());
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
    // it first, as closing the Reader does (UX round-2 review F3). Its entry
    // stays: a save still failing is retried with its newest counts (F7).
    if (activeSeenRef.current) sendSeenCounts(seenSavesRef.current, activeSeenRef.current);
    activeSeenRef.current = null;
    askEpoch.current += 1;
    askPending.current = false;
    setBusy(false);
    setParentExchange(null);
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
    movedPendingRef.current = false;
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
    // RW1a per-source state. The return stack itself survives a detour into
    // another source; openSource decides whether it continues or resets.
    setReconnect(null);
    setInquiryChecks({});
    // A check still being written goes on in the background; its wait ends
    // with the source (no outcome is recorded for a wait nobody watched).
    inquiryJobsRef.current = {};
    setInquiryCommitments({});
    setAskTabMarked(false);
    backToReadingRef.current = null;
    proactiveSeenRef.current = new Set();
    settleScrollRef.current = null;
  }, []);

  const openSource = useCallback(
    async (
      card: SourceLibraryCard,
      jumpSpan?: string,
      options: { via?: "search" | "restore"; handoff?: ReadingPosition | null } = {},
    ) => {
      const handoff = options.handoff ?? null;
      handoffRef.current = handoff;
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
        // RW1a (reader_inquiry on): opening another source after leaving one
        // -- a search hit or its library card -- is a detour from the passage
        // left a moment ago (Alt+← goes back to it); a restore walks the stack.
        // Reopening the same source, or the first open of a visit, is reading.
        // Switched off there is no return stack at all (F5).
        const left = lastSourceRef.current;
        if (inquiryRef.current && options.via !== "restore" && left && left.sourceId !== card.sourceId) {
          const entry: ReturnEntry = {
            id: newActivityId(), kind: "source", sourceId: card.sourceId, sourceTitle: card.title,
            extractionId: view.extractionId, spanId: jumpSpan ?? null, selection: null, railTab: "guide",
            exchangeId: null, label: card.title, openedAt: Date.now(),
          };
          const next = pushDetour(returnStackRef.current, left, entry);
          returnStackRef.current = next;
          setReturnStack(next);
          logReaderAction("detour_opened", {
            detour_id: entry.id, detour_kind: "source", origin_span_id: left.spanId,
            target_span_id: entry.spanId, depth: next.entries.length - 1,
            via: options.via === "search" ? "search" : "library",
          });
        } else if (options.via !== "restore") {
          returnStackRef.current = EMPTY_STACK;
          setReturnStack(EMPTY_STACK);
        }
        lastSourceRef.current = null;
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
    // RW1a: remember where the learner was, so a search hit opened from the
    // library is a detour with a way back (Alt+← reopens this passage).
    if (render && !offline) {
      const spanId = readingSpan ?? activeSpan;
      const section = guidePlan?.sections.find((candidate) => spanId && candidate.spanIds.includes(spanId));
      lastSourceRef.current = {
        id: newActivityId(), kind: "origin", sourceId: render.sourceId, sourceTitle,
        extractionId: render.extractionId, spanId, selection, railTab, exchangeId: null,
        label: [sourceTitle, section?.label].filter(Boolean).join(" · ") || "where I was",
        openedAt: Date.now(),
      };
    }
    resetSourceState();
    setPreparingCard(null);
    setRender(null);
    setOffline(false);
    setSourceTitle(null);
    onSourceChange?.(null);
  }, [onSourceChange, resetSourceState, render, offline, readingSpan, activeSpan, guidePlan, sourceTitle, selection, railTab]);

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
  // RW1a's kill switch (reader_inquiry.enabled): the sidecar names it only when
  // on, so an absent flag (switched off, or an older sidecar) is today's rail.
  const inquiry = contract?.inquiryEnabled === true;
  inquiryRef.current = inquiry;
  // Skim is the mute button (UX §3.1): with inquiry on, nothing LearnLoop
  // starts shows while skimming -- no reconnect line, no section offer.
  const muted = inquiry && mode === "skim";

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
      if (gap < 120_000) visit.active += gap;
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

  /** The learner did something (scroll, select, type): active time accrues. */
  const touchVisit = useCallback(() => {
    const visit = visitRef.current;
    if (!visit) return;
    const now = Date.now();
    const gap = now - visit.lastActive;
    if (gap < 120_000) visit.active += gap;
    else visit.idle += gap;
    visit.lastActive = now;
  }, []);
  const visitPayload = useCallback(
    () => ({ visit_id: visitRef.current?.id ?? null, extraction_id: render?.extractionId ?? null }),
    [render],
  );
  /** First touch of the source after a usable model result ("back to reading"). */
  const noteBackToReading = useCallback(() => {
    const pending = backToReadingRef.current;
    if (!pending) return;
    backToReadingRef.current = null;
    logReaderAction("back_to_reading", {
      ...visitPayload(), job_id: pending.jobId, action_kind: pending.actionKind,
      seconds_after: Math.round((Date.now() - pending.at) / 1000),
    });
  }, [visitPayload]);
  /** A selection was committed (span ids only; never the quoted text). */
  const noteSelection = useCallback((spanCount: number, surface: string) => {
    touchVisit();
    noteLearnerActivity("selected");
    logReaderActivity({ kind: "reader_selection", payload: { ...visitPayload(), span_count: spanCount, surface } });
    noteBackToReading();
  }, [touchVisit, visitPayload, noteBackToReading]);
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
          parentExchangeId: exchange.parentExchangeId ?? null,
          extractionId: exchange.extractionId,
          selectionSpanIds: exchange.selectionSpanIds ?? [],
          selectionQuoteMd: exchange.selectionQuoteMd ?? null,
          selectionSourceQuoteMd: exchange.selectionSourceQuoteMd ?? null,
          citations: exchange.citations ?? [],
          questionEventId: exchange.questionEventId ?? null,
          resolution: exchange.resolution ?? null,
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
      const key = `quick_check_waiting:${section.id}`;
      if (proactiveSeenRef.current.has(key)) continue;
      proactiveSeenRef.current.add(key);
      logReaderAction("proactive_shown", { ...visitPayload(), element: "quick_check_waiting" });
    }
  }, [inquiry, boundaryChecksAvailable, openQuestionSections, visitPayload]);
  useEffect(() => {
    if (!inquiry || muted || !currentGuideSection || currentSectionProgress < 0.7) return;
    const section = currentGuideSection;
    if (dismissedSections.includes(section.id) || completedSections.includes(section.id)) return;
    const offered = (offeredCheckSections.has(section.id) && section.question?.readingPhase === "after_section")
      || section.suggestedPassages.length > 0;
    const key = `section_offer:${section.id}`;
    if (!offered || proactiveSeenRef.current.has(key)) return;
    proactiveSeenRef.current.add(key);
    logReaderAction("proactive_shown", { ...visitPayload(), element: "section_offer" });
  }, [inquiry, muted, currentGuideSection, currentSectionProgress, dismissedSections, completedSections, offeredCheckSections, visitPayload]);
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
    // RW1a: while a detour is open, the saved position stays at its root --
    // "where I was" -- so a restart restores the root and nothing else (the
    // return stack is visit state, P3 §12).
    const root = inquiry && hasDetour(returnStack) ? returnStack.entries[0] : null;
    const saved = root && root.sourceId === render.sourceId && root.spanId ? root.spanId : readingSpan;
    try {
      window.localStorage.setItem(readingPositionKey(render.sourceId), saved);
    } catch {
      /* Reading-position persistence is best-effort. */
    }
  }, [inquiry, render, offline, readingSpan, returnStack]);

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
    setRailCollapsed(false);
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
    noteSelection(nodes.length, "text");
    // A selection updates Ask's grounding too. Do not unexpectedly hide an Ask
    // conversation; Guide still yields to Capture so a first-time selection
    // exposes the annotation actions.
    setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
  }, [collectSelectionNodes, noteSelection]);

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
    noteSelection(nodes.length, "text_boxes");
    setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
  }, [resolveDomBoxes, noteSelection]);
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

  // A single bare Alt press is the quick "clear capture" gesture (K7: it
  // completes on release, and never when Alt was part of a chord, so Alt+←,
  // Alt+drag sweeps and Alt+Tab keep the capture). An Alt+drag sweep replaces
  // the capture itself on mouse-up.
  const clearSelection = useCallback(() => {
    setSelection(null);
    setSelectionActions([]);
    setEditingCapture(false);
    setTagMenu(null);
    window.getSelection()?.removeAllRanges();
  }, []);
  useBareAltClear(clearSelection);

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
      if (SCROLL_KEYS.has(event.key)) userScrollAtRef.current = Date.now();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [render]);

  // ── RW1a: the return stack, detours and the reconnect line ─────────────────

  /** "Mixtures ¶3": the passage's guide section and its place in it. */
  const passageLabel = useCallback((spanId: string | null): string => {
    const section = spanId ? guideSectionBySpan.get(spanId) : undefined;
    if (section && spanId) return `${section.label} ¶${section.spanIds.indexOf(spanId) + 1}`;
    return sourceTitle ?? "where I was";
  }, [guideSectionBySpan, sourceTitle]);

  /** The current position as a stack entry (the origin of a first detour). */
  const positionEntry = useCallback((): ReturnEntry | null => {
    if (!render) return null;
    const spanId = readingSpan ?? activeSpan;
    return {
      id: newActivityId(), kind: "origin", sourceId: render.sourceId, sourceTitle,
      extractionId: render.extractionId, spanId, selection, railTab, exchangeId: null,
      label: passageLabel(spanId), openedAt: Date.now(),
    };
  }, [render, readingSpan, activeSpan, sourceTitle, selection, railTab, passageLabel]);

  /** Push detour entries (in order) from the current position and log each. */
  const pushDetours = useCallback((entries: ReturnEntry[]) => {
    if (!inquiry || offline) return;
    const origin = positionEntry();
    if (!origin) return;
    let next = returnStackRef.current;
    for (const entry of entries) {
      const before = next;
      next = pushDetour(next, origin, entry);
      if (next === before) continue;
      logReaderAction("detour_opened", {
        ...visitPayload(), detour_id: entry.id, detour_kind: entry.kind,
        origin_span_id: next.entries[0]?.spanId ?? null, target_span_id: entry.spanId,
        depth: next.entries.length - 1,
      });
    }
    returnStackRef.current = next;
    setReturnStack(next);
    settleScrollRef.current = null;
  }, [inquiry, offline, positionEntry, visitPayload]);

  /** A peek at a passage the Ask rail points to (show passage, a citation). */
  const peekPassage = useCallback((spanId: string) => {
    const here = readingSpan ?? activeSpan;
    if (inquiry && render && spanId !== here) {
      pushDetours([{
        id: newActivityId(), kind: "peek", sourceId: render.sourceId, sourceTitle,
        extractionId: render.extractionId, spanId, selection: null, railTab, exchangeId: null,
        label: passageLabel(spanId), openedAt: Date.now(),
      }]);
    }
    jumpToSpan(spanId);
  }, [inquiry, render, readingSpan, activeSpan, sourceTitle, railTab, passageLabel, pushDetours, jumpToSpan]);

  /** The root of the inquiry an exchange belongs to (walking saved parents). */
  const inquiryRoot = useCallback((exchangeId: string): ReaderExchange | null => {
    const byId = new Map(history.map((exchange) => [exchange.id, exchange]));
    let current = byId.get(exchangeId) ?? null;
    const seen = new Set<string>();
    while (current?.parentExchangeId && byId.has(current.parentExchangeId) && !seen.has(current.id)) {
      seen.add(current.id);
      current = byId.get(current.parentExchangeId) ?? current;
    }
    return current;
  }, [history]);

  /** Ask "does this make sense now?" about an open inquiry. Inline only on a
   *  return the learner started; never while skimming. */
  const showReconnect = useCallback((exchangeId: string, inline: boolean) => {
    if (!inquiry || muted) return;
    const root = inquiryRoot(exchangeId);
    if (!root || (root.resolution ?? "open") !== "open") return;
    reconnectBaseRef.current = bodyRef.current?.scrollTop ?? 0;
    setReconnect({ rootId: root.id, question: root.question, spanId: root.spanId, inline });
    logReaderAction("reconnect_shown", { ...visitPayload(), root_exchange_id: root.id, placement: inline ? "inline" : "rail" });
  }, [inquiry, muted, inquiryRoot, visitPayload]);

  /** Walk the stack to an entry: restore its passage, selection and tab. */
  const restoreEntry = useCallback(async (next: ReturnStack, target: ReturnEntry, via: string) => {
    // The walk moves the page (and may reopen a source): not the learner scrolling.
    jumpGuardRef.current = Date.now() + 1500;
    const previous = returnStackRef.current;
    // Back at the origin, every detour not yet returned completes (once: a
    // walk forward and back again returns nothing new, F7).
    const returning = next.cursor === 0 ? unreturnedDetours(previous) : [];
    const settled = markReturned(next, returning.map((detour) => detour.id));
    returnStackRef.current = settled;
    setReturnStack(settled);
    if (target.sourceId !== render?.sourceId) {
      const card = (library ?? []).find((candidate) => candidate.sourceId === target.sourceId);
      if (card) await openSource(card, target.spanId ?? undefined, { via: "restore" });
    } else if (target.spanId) {
      jumpToSpan(target.spanId);
    }
    setSelection(target.selection);
    setSelectionActions([]);
    setRailTab(target.railTab);
    if (target.exchangeId) {
      setCollapsedAskIds((ids) => {
        const nextIds = new Set(ids);
        nextIds.delete(target.exchangeId as string);
        return nextIds;
      });
    }
    if (next.cursor === 0) {
      // Back where the detour began: each open detour ended at its origin.
      const now = Date.now();
      for (const detour of returning) {
        logReaderAction("detour_returned", {
          ...visitPayload(), detour_id: detour.id, detour_kind: detour.kind, returned_to_origin: true,
          seconds_away: Math.round((now - detour.openedAt) / 1000), via,
        });
      }
      if (target.spanId && render && target.sourceId === render.sourceId && !offline) {
        void Promise.resolve()
          .then(() => api.readerRestoreSource({ extractionId: target.extractionId, spanId: target.spanId as string }))
          .catch(() => undefined);
      }
      const inquiryExchange = stackInquiryExchange(previous);
      if (inquiryExchange) showReconnect(inquiryExchange, true);
      settleScrollRef.current = bodyRef.current?.scrollTop ?? 0;
    }
  }, [render, library, openSource, jumpToSpan, visitPayload, offline, showReconnect]);

  // Scrolling the source: reading position, active time, "back to reading",
  // and the two RW1a things a screen of scrolling ends -- the reconnect line
  // (ignored, nothing recorded) and a detour already walked back to its root.
  const onBodyScroll = useCallback(() => {
    onReadingScroll();
    touchVisit();
    noteLearnerActivity("scrolled");
    noteBackToReading();
    const body = bodyRef.current;
    if (!body) return;
    if (Date.now() < jumpGuardRef.current) {
      // The page is still moving to an explicit jump's target: not the learner.
      reconnectBaseRef.current = body.scrollTop;
      if (settleScrollRef.current !== null) settleScrollRef.current = body.scrollTop;
      return;
    }
    const screen = Math.max(1, body.clientHeight);
    if (reconnect && Math.abs(body.scrollTop - reconnectBaseRef.current) > screen) setReconnect(null);
    const settleFrom = settleScrollRef.current;
    if (settleFrom !== null && returnStackRef.current.cursor === 0 && Math.abs(body.scrollTop - settleFrom) > screen) {
      settleScrollRef.current = null;
      returnStackRef.current = EMPTY_STACK;
      setReturnStack(EMPTY_STACK);
    }
  }, [onReadingScroll, touchVisit, noteBackToReading, reconnect]);

  // Reader-wide keys (UX §3.5), outside text fields: [ and ] move between rail
  // tabs; \ collapses or expands the rail (remembered on this device).
  useEffect(() => {
    if (!inquiry || !render) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select"))) return;
      const tabs: ReaderRailTab[] = ["guide", "ask", "notes"];
      if (event.key === "[" || event.key === "]") {
        event.preventDefault();
        setRailTab((tab) => tabs[(tabs.indexOf(tab) + (event.key === "]" ? 1 : tabs.length - 1)) % tabs.length]);
      } else if (event.key === "\\") {
        event.preventDefault();
        setRailCollapsed((collapsed) => !collapsed);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [inquiry, render]);
  useEffect(() => {
    try {
      window.localStorage.setItem("learnloop.reader.rail-collapsed", railCollapsed ? "on" : "off");
    } catch {
      /* A per-device preference; reading works without it. */
    }
  }, [railCollapsed]);
  useEffect(() => {
    if (railTab === "ask") setAskTabMarked(false);
  }, [railTab]);

  // Alt+← / Alt+→ walk the return stack (UX §3.5; K7 keeps the capture).
  useEffect(() => {
    if (!inquiry || !render) return;
    const onKey = (event: KeyboardEvent) => {
      if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      const stack = returnStackRef.current;
      const moved = event.key === "ArrowLeft" ? stackBack(stack) : stackForward(stack);
      if (!moved.target) return;
      event.preventDefault();
      void restoreEntry(moved.stack, moved.target, event.key === "ArrowLeft" ? "alt_back" : "alt_forward");
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [inquiry, render, restoreEntry]);

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
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: `preset:${preset}` });
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
      logReaderAction("action_invoked", { ...visitPayload(), action_kind: "highlight" });
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
  const importJobRef = useRef<{ jobId: string; startedAt: number; activity: ReturnType<typeof learnerActivitySnapshot> } | null>(null);
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
      logReaderAction("action_invoked", { ...visitPayload(), action_kind: "import_exercise" });
      importJobRef.current = { jobId: receipt.batchId, startedAt: Date.now(), activity: learnerActivitySnapshot() };
      logReaderActivity({ kind: "reader_job_queued", payload: { ...visitPayload(), job_id: receipt.batchId, job_kind: "import_exercise" } });
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
        const job = importJobRef.current;
        if (job && job.jobId === exerciseImportBatchId && (status.status === "completed" || status.status === "failed" || status.status === "cancelled")) {
          importJobRef.current = null;
          const waited = Date.now() - job.startedAt;
          logReaderActivity({
            kind: "reader_job_completed",
            payload: {
              job_id: job.jobId, job_kind: "import_exercise", status: status.status, latency_ms: waited,
              model_wait_ms: waited, failure_reason: status.status === "failed" ? "job_failed" : null,
              activity_during_wait: activitySince(job.activity),
            },
          });
        }
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

  // Ask (and, with reader_inquiry on, a follow-up in a branch). The learner's
  // words stay in the composer until the answer lands; a failure keeps them.
  const [askPhase, setAskPhase] = useState<ModelActionPhase>("idle");
  const askJobRef = useRef<{ jobId: string; kind: string; startedAt: number; activity: ReturnType<typeof learnerActivitySnapshot> } | null>(null);
  const submitAsk = useCallback(async (asked: string, parent: ReaderExchange | null) => {
    // A follow-up keeps its saved anchor even when the current selection moves.
    // New roots use the capture selection (the same selection Notes>Capture
    // acts on), then the jump/resume fallback.
    const groundingSpan = parent?.spanId ?? selection?.spanId ?? activeSpan;
    if (!groundingSpan || !asked || !render || askPending.current) return;
    if (inquiry && offline) return;
    const epoch = askEpoch.current;
    askPending.current = true;
    // The full capture selection widens the tutor's citable context to every
    // selected block, not just the primary one; a follow-up inherits its
    // parent's saved selection instead.
    const selectionSpanIds = parent
      ? parent.selectionSpanIds
      : selection ? [...new Set(selectionNodes(selection).map((n) => n.spanId))] : [];
    const selectionQuote = parent
      ? parent.selectionQuoteMd
      : selection ? (selection.editedText ?? selection.quote).trim() || null : null;
    // An edited capture is the learner's wording: the source's own is sent
    // beside it (reader_inquiry on), so history never shows it as the book's.
    const edited = !parent && selection?.editedText != null && selection.editedText.trim() !== selection.quote.trim();
    const selectionSourceQuote = parent
      ? parent.selectionSourceQuoteMd ?? null
      : edited && selection ? selection.quote.trim() || null : null;
    const jobKind = parent ? "follow_up" : "ask";
    const job = { jobId: newActivityId(), kind: jobKind, startedAt: Date.now(), activity: learnerActivitySnapshot() };
    askJobRef.current = job;
    logReaderAction("action_invoked", { ...visitPayload(), action_kind: jobKind });
    logReaderActivity({ kind: "reader_job_queued", payload: { ...visitPayload(), job_id: job.jobId, job_kind: jobKind } });
    setBusy(true);
    if (inquiry) setAskPhase("pending");
    try {
      const answer = await api.readerAsk({
        extractionId: render.extractionId,
        spanId: groundingSpan,
        question: asked,
        ...(inquiry ? { parentExchangeId: parent?.id ?? null } : {}),
        answerMode,
        selectionSpanIds,
        selectionQuote,
        ...(inquiry && selectionSourceQuote ? { selectionSourceQuote } : {}),
      });
      if (epoch !== askEpoch.current) return;
      const waited = Date.now() - job.startedAt;
      logReaderActivity({
        kind: "reader_job_completed",
        payload: {
          ...visitPayload(), job_id: job.jobId, job_kind: jobKind, status: "completed",
          latency_ms: waited, model_wait_ms: waited, model: answer.model ?? null,
          prompt_version: String((answer.manifest as { version?: unknown } | undefined)?.version ?? "") || null,
          activity_during_wait: activitySince(job.activity),
        },
      });
      backToReadingRef.current = { jobId: job.jobId, actionKind: jobKind, at: Date.now() };
      const exchange: ReaderExchange = {
        id: answer.readerAnswerEventId,
        parentExchangeId: answer.parentExchangeId ?? null,
        extractionId: render.extractionId,
        selectionSpanIds,
        selectionQuoteMd: selectionQuote,
        selectionSourceQuoteMd: inquiry ? selectionSourceQuote : null,
        citations: answer.citations ?? [],
        questionEventId: answer.eventId ?? null,
        resolution: "open",
        spanId: groundingSpan,
        question: asked,
        answerMd: answer.answerMd,
        answerMode: answer.answerMode,
        createdAt: new Date().toISOString(),
      };
      if (inquiry) {
        setParentExchange(exchange);
        setAskPhase("idle");
        if (railTab !== "ask") setAskTabMarked(true);
        if (parent) {
          // A branch is a detour: the strip shows the inquiry's path.
          const branchEntry = (target: ReaderExchange, label: string): ReturnEntry => ({
            id: newActivityId(), kind: "branch", sourceId: render.sourceId, sourceTitle,
            extractionId: render.extractionId, spanId: target.spanId, selection: null, railTab: "ask",
            exchangeId: target.id, label: clip(label, 48), openedAt: Date.now(),
          });
          const pushes: ReturnEntry[] = [];
          if (!returnStackRef.current.entries.some((entry) => entry.exchangeId === parent.id)) {
            pushes.push(branchEntry(parent, parent.question));
          }
          pushes.push(branchEntry(exchange, asked));
          pushDetours(pushes);
        }
      }
      setHistory((items) => [exchange, ...items.filter((item) => item.id !== exchange.id)]);
      setCollapsedAskIds((ids) => {
        const next = new Set(ids);
        next.delete(exchange.id);
        if (parent) next.delete(parent.id);
        return next;
      });
      setQuestion("");
      // WebKit can retain the submitted textarea's stale compositing layer when
      // the completed exchange mounts below it. Remounting gives the next Ask a
      // fresh input surface. A landed answer never moves focus (W12): focus
      // returns to the composer only if the learner was still in it.
      const composerHadFocus = document.activeElement === askComposerRef.current;
      setAskComposerVersion((version) => version + 1);
      // On the Ask tab the answer comes into view (UX finishing pass, re-test
      // #4: it arrived below the fold and the box just emptied), at once, not
      // animated (G54). Focus stays where it was: the composer keeps it only
      // if the learner was still in it, without pulling the view back up.
      const onAskTab = railTab === "ask";
      if (composerHadFocus || onAskTab) {
        window.requestAnimationFrame(() => {
          if (composerHadFocus) askComposerRef.current?.focus({ preventScroll: true });
          if (!onAskTab) return;
          const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find(
            (element) => element.dataset.askId === exchange.id,
          );
          card?.scrollIntoView?.({ block: "start" });
        });
      }
    } catch (error) {
      if (epoch === askEpoch.current) {
        const phase = phaseForError(error);
        logReaderActivity({
          kind: "reader_job_completed",
          payload: {
            ...visitPayload(), job_id: job.jobId, job_kind: jobKind, status: "failed",
            failure_reason: phase === "failed" ? "error" : phase, latency_ms: Date.now() - job.startedAt,
            model_wait_ms: Date.now() - job.startedAt, activity_during_wait: activitySince(job.activity),
          },
        });
        // Model unreachable, capped and sidecar-down render in place (W14). An
        // unexpected failure still reaches the app's error line too: that is
        // the ported branch's contract (its retry test, G1).
        if (inquiry) setAskPhase(phase);
        if (!inquiry || phase === "failed") onError(errorMessage(error));
        // The learner's words stay in the composer for "try again".
        if (inquiry && asked !== question.trim()) setQuestion(asked);
      }
    } finally {
      if (epoch === askEpoch.current) {
        askPending.current = false;
        setBusy(false);
      }
      if (askJobRef.current === job) askJobRef.current = null;
    }
  }, [inquiry, selection, activeSpan, answerMode, render, offline, onError, visitPayload, railTab, sourceTitle, pushDetours, question]);

  const ask = useCallback(() => {
    void submitAsk(question.trim(), inquiry ? parentExchange : null);
  }, [submitAsk, question, inquiry, parentExchange]);

  /** Cancel a pending Ask: its late answer is ignored (it stays in the history
   *  the sidecar keeps), and the learner's words stay in the composer. */
  const cancelAsk = useCallback(() => {
    const job = askJobRef.current;
    askEpoch.current += 1;
    askPending.current = false;
    setBusy(false);
    setAskPhase("idle");
    if (job) {
      logReaderActivity({
        kind: "reader_job_completed",
        payload: {
          ...visitPayload(), job_id: job.jobId, job_kind: job.kind, status: "cancelled",
          latency_ms: Date.now() - job.startedAt, model_wait_ms: Date.now() - job.startedAt,
          activity_during_wait: activitySince(job.activity),
        },
      });
      askJobRef.current = null;
    }
  }, [visitPayload]);

  // ── RW1a: inquiry status, reconnect answers and the passage quick check ───

  const updateExchange = useCallback((id: string, patch: Partial<ReaderExchange>) => {
    setHistory((items) => items.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }, []);

  const setInquiryStatus = useCallback(async (root: ReaderExchange, resolution: InquiryResolution, trigger: "chip" | "key" = "chip") => {
    if (!render || offline) return;
    try {
      const result = await api.readerSetInquiryStatus({ extractionId: render.extractionId, exchangeId: root.id, resolution, trigger });
      updateExchange(result.rootExchangeId, { resolution: result.resolution });
      if (result.resolution !== "open" && reconnect?.rootId === result.rootExchangeId) setReconnect(null);
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [render, offline, updateExchange, reconnect, onError]);

  /** A branch marked done (its own question resolved) asks the reconnect line. */
  const markBranchDone = useCallback(async (branch: ReaderExchange) => {
    if (!branch.questionEventId || offline) return;
    try {
      await api.resolveQuestionEvent(branch.questionEventId, "resolved");
      updateExchange(branch.id, { resolution: "resolved" });
      logReaderAction("action_invoked", { ...visitPayload(), action_kind: "branch_done" });
      showReconnect(branch.id, false);
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [offline, updateExchange, visitPayload, showReconnect, onError]);

  /** "revisit once" / "make it something I can do": the existing test_me_later
   *  and help_me_remember presets on the root's anchor (no new status words). */
  const commitInquiry = useCallback(async (root: ReaderExchange, preset: InquiryCommitment) => {
    if (!render || offline) return;
    const spanIds = root.selectionSpanIds.length ? root.selectionSpanIds : [root.spanId];
    try {
      const receipt = await api.readerInvokePreset({
        preset,
        sourceId: render.sourceId,
        revisionId: render.revisionId,
        extractionId: render.extractionId,
        clientIdempotencyKey: newKey(),
        renderViewId: render.renderViewId,
        rawSelection: { nodes: spanIds.map((spanId) => ({ spanId, start: 0, end: 1_000_000 })) },
        learnerText: "",
        subjectId: root.spanId,
      });
      setInquiryCommitments((done) => ({ ...done, [root.id]: [...new Set([...(done[root.id] ?? []), preset])] }));
      if (receipt.arc) setArc(receipt.arc);
      logReaderAction("action_invoked", { ...visitPayload(), action_kind: `inquiry:${preset}` });
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [render, offline, visitPayload, refreshAnnotations, onError]);

  const committedFor = useCallback((root: ReaderExchange): Set<InquiryCommitment> => {
    const done = new Set<InquiryCommitment>(inquiryCommitments[root.id] ?? []);
    for (const annotation of annotations) {
      if ((annotation.kind === "test_me_later" || annotation.kind === "help_me_remember")
        && annotation.segments.some((segment) => segment.spanId === root.spanId)) {
        done.add(annotation.kind);
      }
    }
    return done;
  }, [inquiryCommitments, annotations]);

  /** End a quick check's wait in the funnel, once (F8): its status, the
   *  route it came from, and what the learner did while it was written.
   *  Only the wait for ``batchId`` *and* ``waitId`` is settled: a late answer
   *  for an earlier batch, or for an earlier wait on the same live batch (a
   *  retry the enqueue handed the same batch), never records or ends the
   *  retry's wait (F14). */
  const settleInquiryJob = useCallback((rootId: string, batchId: string | null, waitId: string | null, status: "completed" | "failed" | "cancelled", extra: {
    failureReason?: string | null; model?: string | null; promptVersion?: string | null;
  } = {}) => {
    const job = inquiryJobsRef.current[rootId];
    if (!job || !batchId || !waitId || job.batchId !== batchId || job.waitId !== waitId) return;
    delete inquiryJobsRef.current[rootId];
    const waited = Date.now() - job.startedAt;
    logReaderActivity({
      kind: "reader_job_completed",
      payload: {
        ...job.visit, job_id: job.batchId, job_kind: "quick_check", status,
        failure_reason: status === "failed" ? extra.failureReason ?? "error" : null,
        latency_ms: waited, model_wait_ms: waited, model: extra.model ?? null,
        prompt_version: extra.promptVersion ?? null, activity_during_wait: activitySince(job.activity),
      },
    });
  }, []);

  /** A model-backed request that never reached the queue still counts. */
  const recordUnqueuedCheck = useCallback((failureReason: string) => {
    const jobId = newActivityId();
    logReaderActivity({ kind: "reader_job_queued", payload: { ...visitPayload(), job_id: jobId, job_kind: "quick_check" } });
    logReaderActivity({
      kind: "reader_job_completed",
      payload: {
        ...visitPayload(), job_id: jobId, job_kind: "quick_check", status: "failed", failure_reason: failureReason,
        latency_ms: 0, model_wait_ms: 0, activity_during_wait: {},
      },
    });
  }, [visitPayload]);

  const startQuickCheck = useCallback(async (rootId: string, via: "inline" | "rail") => {
    if (!render || offline) return;
    setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase: "pending", question: null, attempts: 0, pollErrors: 0, batchId: null } }));
    // This wait's own generation (F14): the enqueue may hand a retry the same
    // live batch, so polls are told apart by the wait, not only the batch.
    const waitId = newKey();
    const visit = visitPayload();
    const startedAt = Date.now();
    const activity = learnerActivitySnapshot();
    try {
      const result = await api.readerReconnectAnswer({ extractionId: render.extractionId, exchangeId: rootId, answer: "quick_check", via });
      if (result.question) {
        // Written earlier: it lands at once, with no wait and no model call.
        setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase: "landed", question: result.question } }));
      } else if (result.status === "queued" && result.batchId) {
        const batchId = result.batchId;
        const tracked = inquiryJobsRef.current[rootId];
        if (!tracked || tracked.batchId !== batchId) {
          inquiryJobsRef.current[rootId] = { batchId, waitId, startedAt, activity, visit };
          logReaderActivity({ kind: "reader_job_queued", payload: { ...visit, job_id: batchId, job_kind: "quick_check" } });
        } else {
          // The batch already being waited on: its funnel record carries on,
          // now settled only by this wait (an older wait's polls go stale).
          tracked.waitId = waitId;
        }
        setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase: "pending", question: null, attempts: 0, pollErrors: 0, batchId, waitId } }));
      } else if (result.status === "provider_unavailable") {
        recordUnqueuedCheck("unreachable");
        setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase: "unreachable", question: null } }));
      } else {
        recordUnqueuedCheck("error");
        setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase: "failed", question: null } }));
      }
    } catch (error) {
      const phase = phaseForError(error);
      recordUnqueuedCheck(phase === "failed" ? "error" : phase);
      setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase, question: null } }));
    }
  }, [render, offline, visitPayload, recordUnqueuedCheck]);

  /** Cancel a pending quick check: its job is cancelled (best effort) and the
   *  wait ends, recorded as cancelled. */
  const cancelQuickCheck = useCallback((rootId: string) => {
    const current = inquiryChecks[rootId];
    const wait = current?.batchId
      ? { batchId: current.batchId, waitId: current.waitId ?? null }
      : inquiryJobsRef.current[rootId] ?? null;
    const batchId = wait?.batchId ?? null;
    settleInquiryJob(rootId, batchId, wait?.waitId ?? null, "cancelled");
    setInquiryChecks((checks) => {
      const { [rootId]: _dropped, ...rest } = checks;
      return rest;
    });
    if (batchId) void Promise.resolve().then(() => api.cancelIngestBatch(batchId)).catch(() => undefined);
  }, [inquiryChecks, settleInquiryJob]);

  const answerReconnect = useCallback(async (answer: "yes" | "still_unclear" | "quick_check", text = "") => {
    const line = reconnect;
    if (!line || !render || offline) return;
    const via = line.inline ? "inline" : "rail";
    setReconnect(null);
    if (answer === "quick_check") {
      if (railTab !== "ask") setAskTabMarked(true);
      await startQuickCheck(line.rootId, via);
      return;
    }
    try {
      const result = await api.readerReconnectAnswer({ extractionId: render.extractionId, exchangeId: line.rootId, answer, via });
      updateExchange(result.rootExchangeId, { resolution: result.resolution });
    } catch (error) {
      onError(errorMessage(error));
      return;
    }
    if (answer === "still_unclear") {
      // "What's still unclear?" starts a branch from the root (W5): with text
      // it is asked now; without, the composer opens on the root.
      const root = history.find((item) => item.id === line.rootId) ?? null;
      if (!root) return;
      setParentExchange(root);
      setRailTab("ask");
      if (text) void submitAsk(text, root);
    }
  }, [reconnect, render, offline, railTab, startQuickCheck, updateExchange, onError, history, submitAsk]);

  // The passage check is written by a durable job: poll its cheap read and
  // the job's own state until it lands, fails (said in place: capped, the
  // model unreachable, refused), is cancelled or times out. A sidecar that
  // stops answering shows as offline and the poll carries on, so the check
  // still lands when it comes back (F4).
  useEffect(() => {
    if (!render || offline) return;
    const watching = Object.entries(inquiryChecks).filter(
      ([, check]) => check.batchId && check.waitId && (check.phase === "pending" || check.phase === "offline"),
    );
    if (watching.length === 0) return;
    const extractionId = render.extractionId;
    const timer = window.setInterval(() => {
      for (const [rootId, check] of watching) {
        const batchId = check.batchId as string;
        const waitId = check.waitId as string;
        const attempts = (check.attempts ?? 0) + 1;
        // Settle or update only this wait: the same batch *and* the same
        // client wait (a retry may be handed the same live batch; F14).
        const same = (checks: typeof inquiryChecks) => checks[rootId]?.batchId === batchId && checks[rootId]?.waitId === waitId;
        const timedOut = () => {
          settleInquiryJob(rootId, batchId, waitId, "failed", { failureReason: "timeout" });
          setInquiryChecks((checks) => (same(checks) ? { ...checks, [rootId]: { phase: "failed", question: null, batchId: null } } : checks));
        };
        void api.readerInquiryQuestion({ extractionId, exchangeId: rootId, batchId })
          .then((result) => {
            const job = result.job ?? null;
            if (result.question) {
              const question = result.question;
              settleInquiryJob(rootId, batchId, waitId, "completed", { model: question.model ?? null, promptVersion: question.promptVersion ?? null });
              setInquiryChecks((checks) => (same(checks) ? { ...checks, [rootId]: { phase: "landed", question } } : checks));
            } else if (job?.status === "cancelled") {
              settleInquiryJob(rootId, batchId, waitId, "cancelled");
              setInquiryChecks((checks) => {
                if (!same(checks)) return checks;
                const { [rootId]: _dropped, ...rest } = checks;
                return rest;
              });
            } else if (job?.status === "failed") {
              const code = job.errorCode ?? "error";
              settleInquiryJob(rootId, batchId, waitId, "failed", { failureReason: code });
              const phase: ModelActionPhase = code === "capped" ? "capped" : code === "provider_unavailable" ? "unreachable" : "failed";
              const failure = code === "spend_refused" ? spendRefusalLine(job.refusal) : null;
              setInquiryChecks((checks) => (same(checks) ? { ...checks, [rootId]: { phase, question: null, failure } } : checks));
            } else if (attempts > INQUIRY_CHECK_MAX_POLLS) {
              timedOut();
            } else {
              setInquiryChecks((checks) => (same(checks)
                ? { ...checks, [rootId]: { ...checks[rootId], phase: "pending", attempts, pollErrors: 0 } }
                : checks));
            }
          })
          .catch((error) => {
            const phase = phaseForError(error);
            if (phase !== "offline") {
              // The read itself was refused (switched off, an unknown inquiry).
              settleInquiryJob(rootId, batchId, waitId, "failed", { failureReason: phase === "failed" ? "error" : phase });
              setInquiryChecks((checks) => (same(checks) ? { ...checks, [rootId]: { phase, question: null } } : checks));
            } else if (attempts > INQUIRY_CHECK_MAX_POLLS) {
              timedOut();
            } else {
              const pollErrors = (check.pollErrors ?? 0) + 1;
              setInquiryChecks((checks) => (same(checks)
                ? { ...checks, [rootId]: { ...checks[rootId], attempts, pollErrors, phase: pollErrors >= 2 ? "offline" : checks[rootId].phase } }
                : checks));
            }
          });
      }
    }, INQUIRY_CHECK_POLL_MS);
    return () => window.clearInterval(timer);
  }, [render, offline, inquiryChecks, settleInquiryJob]);

  const inquiryCheckAction = useCallback(async (rootId: string, action: "answered" | "self_checked" | "dismissed", value?: string) => {
    const check = inquiryChecks[rootId];
    if (!check?.question) return;
    try {
      const result = await api.readerInquiryQuestionAction({
        questionId: check.question.id,
        action,
        response: action === "answered" ? value ?? null : null,
        selfCheck: action === "self_checked" ? (value as InquirySelfCheck) : null,
      });
      setInquiryChecks((checks) => ({ ...checks, [rootId]: { ...checks[rootId], phase: "landed", question: result.question } }));
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [inquiryChecks, onError]);

  const escalateInquiryCheck = useCallback(async (rootId: string) => {
    const check = inquiryChecks[rootId];
    if (!check?.question?.escalationLearningObjectId) return;
    try {
      await api.readerEscalateAuthoredQuestion({ questionId: check.question.id, learningObjectId: check.question.escalationLearningObjectId });
      setInquiryChecks((checks) => ({ ...checks, [rootId]: { ...checks[rootId], escalated: true } }));
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [inquiryChecks, onError]);

  // RW1a's passage-scoped quick check is offered by the same one rule as a
  // section's (screens/reader/checkOffer.ts): only on the reconnect line of an
  // open inquiry the learner raised in this visit (a return to it, a branch
  // marked done), never while skimming. The reconnect line is visit state, so
  // a resume never brings one back.
  const passageCheckOffered = useMemo(() => {
    if (!reconnect) return false;
    const root = history.find((exchange) => exchange.id === reconnect.rootId);
    return checkOffer({
      kind: "passage",
      raisedThisVisit: true,
      inquiryOpen: (root?.resolution ?? "open") === "open",
      muted: Boolean(muted),
    }).offer;
  }, [reconnect, history, muted]);

  /** What sits at the top of an inquiry in the rail: the reconnect line and
   *  the quick check (each only when there is one). */
  const renderInquiryTop = useCallback((root: ReaderExchange) => {
    // Skim mutes the reconnect line at render time, in both places, so one
    // already shown goes when the learner switches to skim (F10).
    const line = reconnect && reconnect.rootId === root.id && !muted ? (
      <ReconnectLine
        placement="rail"
        question={reconnect.question}
        busy={busy}
        onYes={() => void answerReconnect("yes")}
        onStillUnclear={(text) => void answerReconnect("still_unclear", text)}
        onQuickCheck={passageCheckOffered ? () => void answerReconnect("quick_check") : undefined}
      />
    ) : null;
    const check = inquiryChecks[root.id];
    return line || check ? (
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {line}
        {check ? (
          <InquiryQuickCheck
            phase={check.phase}
            question={check.question}
            busy={busy}
            escalated={check.escalated}
            failure={check.failure ?? undefined}
            onCancel={check.batchId ? () => cancelQuickCheck(root.id) : undefined}
            onAnswer={(response) => void inquiryCheckAction(root.id, "answered", response)}
            onSelfCheck={(value) => void inquiryCheckAction(root.id, "self_checked", value)}
            onDismiss={() => {
              if (check.question) void inquiryCheckAction(root.id, "dismissed");
              else setInquiryChecks((checks) => {
                const { [root.id]: _dropped, ...rest } = checks;
                return rest;
              });
            }}
            onEscalate={() => void escalateInquiryCheck(root.id)}
            onRetry={() => void startQuickCheck(root.id, "rail")}
            onShowPassage={peekPassage}
          />
        ) : null}
      </div>
    ) : null;
  }, [reconnect, muted, busy, answerReconnect, passageCheckOffered, inquiryChecks, inquiryCheckAction, escalateInquiryCheck, startQuickCheck, cancelQuickCheck, peekPassage]);

  /** The reconnect line drawn under the root passage (a return the learner started). */
  const inlineReconnect = reconnect && reconnect.inline && !muted ? (
    <ReconnectLine
      placement="inline"
      question={reconnect.question}
      busy={busy}
      onYes={() => void answerReconnect("yes")}
      onStillUnclear={(text) => void answerReconnect("still_unclear", text)}
      onQuickCheck={passageCheckOffered ? () => void answerReconnect("quick_check") : undefined}
    />
  ) : null;

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
          if (openingRef.current !== next.sourceId) void openSource(next, undefined, { handoff: position });
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
                          if (card && opening === null) void openSource(card, hit.spanId, { via: "search" });
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

      {inquiry ? (
        <DetourStrip
          stack={returnStack}
          onGoTo={(index) => {
            const { stack, target } = stackGoTo(returnStackRef.current, index);
            if (target) void restoreEntry(stack, target, index === 0 ? "crumb_origin" : "crumb");
          }}
        />
      ) : null}
      <div style={{ flex: 1, minHeight: 0, display: "flex", overflow: "hidden" }}>
        <div
          ref={bodyRef}
          role={inquiry ? "main" : undefined}
          aria-label={inquiry ? [sourceTitle, currentGuideSection?.label].filter(Boolean).join(", ") || "Source" : undefined}
          onMouseDown={(event) => {
            noteUserScroll();
            onBodyMouseDown(event);
          }}
          onMouseUp={onMouseUp}
          onWheel={noteUserScroll}
          onTouchMove={noteUserScroll}
          onScroll={onBodyScroll}
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
              onSeek={onPlaybackSeek}
              onAskSpan={(spanId) => {
                if (spanId) setActiveSpan(spanId);
              }}
              onTagMenu={openDomTagMenu}
              inlineNote={inlineReconnect && reconnect ? { spanId: reconnect.spanId, node: inlineReconnect } : null}
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
                noteSelection(sel.nodes?.length ?? 1, "pdf");
                setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
              }}
              onTagMenu={setTagMenu}
              onError={onError}
              inlineNote={inlineReconnect && reconnect ? { spanId: reconnect.spanId, node: inlineReconnect } : null}
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
            // The section-break button asks the one check-offer rule too.
            const endQuestionAvailable = Boolean(endSection
              && endSection.question?.readingPhase === "after_section"
              && offeredCheckSections.has(endSection.id));
            const offerSection = endSection
              && !muted
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
              {inlineReconnect && reconnect && block.spanId === reconnect.spanId ? inlineReconnect : null}
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
        {inquiry && railCollapsed ? (
          <button
            type="button"
            onClick={() => setRailCollapsed(false)}
            aria-label={"expand the rail (\\)"}
            title={"expand the rail (\\)"}
            style={{ width: 28, flexShrink: 0, border: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
          >
            ◂
          </button>
        ) : null}
        <div
          ref={railRef}
          role="complementary"
          aria-label={railTab === "guide" ? "Reading guide" : railTab === "ask" ? "Ask" : "Notes"}
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
            display: inquiry && railCollapsed ? "none" : undefined,
          }}
          className="ll-scroll"
        >
          <div style={{ position: "sticky", top: -18, zIndex: 8, margin: "-18px -20px 16px", padding: "12px 20px 10px", background: COLOR.bg, borderBottom: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", gap: 4 }}>
              {(["guide", "ask", "notes"] as ReaderRailTab[]).map((tab) => {
                const active = railTab === tab;
                // The static quick-check marker (UX S12, spec §3.4 item 19): a
                // plain "◆ n" on the Guide tab for every learner. No pulse, no
                // blink and no pinned strip -- nothing in the rail animates.
                const waiting = tab === "guide" && pendingQuickCheckCount > 0;
                const marked = tab === "ask" && askTabMarked && !active;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setRailTab(tab)}
                    aria-pressed={active}
                    aria-label={waiting ? `Guide, ${pendingQuickCheckCount} quick check${pendingQuickCheckCount === 1 ? "" : "s"} waiting` : marked ? "ask, something new" : tab}
                    style={{ flex: 1, display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 6, border: `1px solid ${active ? COLOR.borderFocus : COLOR.border}`, background: active ? COLOR.washAmber : "transparent", color: active ? COLOR.amberLink : COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, padding: "6px 8px", cursor: "pointer", textTransform: "uppercase", letterSpacing: "0.08em" }}
                  >
                    {tab}
                    {waiting ? (
                      <span aria-hidden="true" data-quick-check-marker="" style={{ display: "inline-flex", alignItems: "center", gap: 4, color: COLOR.purpleText }}>
                        ◆ {pendingQuickCheckCount}
                      </span>
                    ) : null}
                    {marked ? <span aria-hidden="true" style={{ color: COLOR.amber }}>•</span> : null}
                    {tab === "notes" && annotations.length > 0 ? <span>{annotations.length}</span> : null}
                  </button>
                );
              })}
            </div>
          </div>

          <GuideRail
            visible={railTab === "guide"}
            extractionId={render.extractionId}
            offline={offline}
            guidePlan={guidePlan}
            guideLoading={guideLoading}
            currentGuideSection={currentGuideSection}
            currentSectionProgress={currentSectionProgress}
            currentSectionRead={currentSectionRead}
            sectionSeen={sectionSeen}
            readingMoved={readingMoved}
            currentQuestionOpen={currentQuestionOpen}
            boundaryChecksAvailable={boundaryChecksAvailable}
            authoringSections={authoringSections}
            timedOutSections={timedOutSections}
            retryQuickCheck={retryQuickCheck}
            revealedSections={revealedSections}
            completedSections={completedSections}
            dismissedSections={dismissedSections}
            answeredSections={answeredSections}
            setAnsweredSections={setAnsweredSections}
            focusQuickCheck={focusQuickCheck}
            annotatedSpans={annotatedSpans}
            openQuestionSections={openQuestionSections}
            setDismissedSections={setDismissedSections}
            jumpToSpan={jumpToSpan}
            peekPassage={peekPassage}
            revealSection={revealSection}
            completeSection={completeSection}
            onError={onError}
            boundaryBlock={boundaryBlock}
            boundarySkipped={boundarySkipped}
            setBoundarySkipped={setBoundarySkipped}
            boundaryAnswered={boundaryAnswered}
            setBoundaryAnswered={setBoundaryAnswered}
            boundaryResponse={boundaryResponse}
            setBoundaryResponse={setBoundaryResponse}
            boundarySubmitted={boundarySubmitted}
            setBoundarySubmitted={setBoundarySubmitted}
            questionControl={questionControl}
            sendQuestionControl={sendQuestionControl}
            disposition={disposition}
            chooseDisposition={chooseDisposition}
          />

          <NotesRail
            visible={railTab === "notes"}
            offline={offline}
            busy={busy}
            pdfSurfaceActive={pdfSurfaceActive}
            activeSpan={activeSpan}
            activeBlock={activeBlock}
            selection={selection}
            selectionActions={selectionActions}
            editingCapture={editingCapture}
            setEditingCapture={setEditingCapture}
            clearSelection={clearSelection}
            editCaptureText={editCaptureText}
            resetCaptureText={resetCaptureText}
            note={note}
            setNote={setNote}
            captureHighlight={captureHighlight}
            invokePreset={invokePreset}
            importExercise={importExercise}
            exerciseImport={exerciseImport}
            setExerciseImport={setExerciseImport}
            exerciseImportActive={exerciseImportActive}
            authoringOpen={authoringOpen}
            setAuthoringOpen={setAuthoringOpen}
            setAuthoringSpanId={setAuthoringSpanId}
            authoringQuote={authoringQuote}
            setAuthoringQuote={setAuthoringQuote}
            authoredQuestion={authoredQuestion}
            setAuthoredQuestion={setAuthoredQuestion}
            authoredAnswer={authoredAnswer}
            setAuthoredAnswer={setAuthoredAnswer}
            authoredCardId={authoredCardId}
            setAuthoredCardId={setAuthoredCardId}
            authoredStatus={authoredStatus}
            authoringBusy={authoringBusy}
            saveOwnQuestion={saveOwnQuestion}
            coach={coach}
            setCoach={setCoach}
            runCoach={runCoach}
            requests={requests}
            requestLoadError={requestLoadError}
            refreshRequests={refreshRequests}
            synthesizedObjects={synthesizedObjects}
            openProposalIds={openProposalIds}
            proposalCount={proposalCount}
            expandedRequests={expandedRequests}
            setExpandedRequests={setExpandedRequests}
            retryRequest={retryRequest}
            decideProposal={decideProposal}
            jumpToSpan={jumpToSpan}
            peekPassage={peekPassage}
            arc={arc}
            pauseArc={pauseArc}
            setArcPolicy={setArcPolicy}
            annotations={annotations}
            jumpToAnnotation={jumpToAnnotation}
            reanchorAnnotation={reanchorAnnotation}
            manualAnchorToSelection={manualAnchorToSelection}
            reanchorNotes={reanchorNotes}
            editingAnnotationId={editingAnnotationId}
            setEditingAnnotationId={setEditingAnnotationId}
            editingAnnotationText={editingAnnotationText}
            setEditingAnnotationText={setEditingAnnotationText}
            saveAnnotationEdit={saveAnnotationEdit}
            deleteAnnotation={deleteAnnotation}
          />

          <AskRail
            visible={railTab === "ask"}
            enabled={enabled}
            inquiry={inquiry}
            offline={offline}
            busy={busy}
            blocks={blocks}
            activeSpan={activeSpan}
            activeBlock={activeBlock}
            selection={selection}
            parentExchange={parentExchange}
            setParentExchange={setParentExchange}
            answerMode={answerMode}
            changeAnswerMode={changeAnswerMode}
            question={question}
            setQuestion={setQuestion}
            askComposerVersion={askComposerVersion}
            askComposerRef={askComposerRef}
            ask={ask}
            history={history}
            visibleAskHistory={visibleAskHistory}
            normalizedAskFind={normalizedAskFind}
            collapsedAskIds={collapsedAskIds}
            setCollapsedAskIds={setCollapsedAskIds}
            askFindOpen={askFindOpen}
            setAskFindOpen={setAskFindOpen}
            askFindQuery={askFindQuery}
            setAskFindQuery={setAskFindQuery}
            askFindInputRef={askFindInputRef}
            jumpToSpan={jumpToSpan}
            peekPassage={peekPassage}
            askPhase={askPhase}
            cancelAsk={cancelAsk}
            onSetStatus={(root, resolution) => void setInquiryStatus(root, resolution)}
            onBranchDone={(branch) => void markBranchDone(branch)}
            onCommit={(root, preset) => void commitInquiry(root, preset)}
            committed={committedFor}
            renderInquiryTop={renderInquiryTop}
          />
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

      <KeyBar
        keys={[
          // In plain words (UX Phase 1 re-test #9).
          ...readerKeyBarKeys(pdfSurfaceActive),
          // RW1a's Reader-wide keys (UX §3.5).
          ...(inquiry
            ? [
                { key: "alt+←", label: "back" },
                { key: "[ ]", label: "tabs" },
                { key: "\\", label: "rail" },
              ]
            : []),
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
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
  /** Every seek this panel makes (a resume, a transcript cue, a jump), told
   *  before the player moves: a seek is a placement, not watching. */
  onSeek: (spanId: string | null) => void;
  onAskSpan: (spanId: string | null) => void;
  onTagMenu: (request: TagMenuRequest) => void;
  /** RW1a: the reconnect line under the transcript passage holding this cue. */
  inlineNote?: { spanId: string; node: ReactNode } | null;
}>(function YouTubeWatchPanel({
  plan,
  blocks,
  annotatedSpans,
  guidanceSpans,
  resumeSpan,
  findShortcutEnabled,
  onPlaybackSpan,
  onSeek,
  onAskSpan,
  onTagMenu,
  inlineNote = null,
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
  const noteSeek = useCallback((spanId: string | null) => {
    seekUntilRef.current = Date.now() + SEEN_SETTLE_MS;
    onSeek(spanId);
  }, [onSeek]);
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
      noteSeek(resumeCue.block.spanId ?? null);
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
    noteSeek(cue.block.spanId ?? null);
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
      noteSeek(spanId);
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
                {inlineNote && section.cues.some((cue) => cue.block.spanId === inlineNote.spanId) ? (
                  <div style={{ gridColumn: "2 / span 1" }}>{inlineNote.node}</div>
                ) : null}
              </div>
            );
          })}
        </div>
        </div>
      </div>
    </Card>
  );
});
