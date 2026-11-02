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

import { Fragment, useCallback, useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";
import { api } from "../api/client";
import { useCachedQuery } from "../api/useCachedQuery";
import { TAG } from "../api/queryTags";
import { setQueryData } from "../api/queryCache";
import type {
  ReaderAnswerMode,
  ReaderDisposition,
  ReaderImportExerciseInput,
  SourceIdentity,
  ReaderGuidePlanDto,
  ReaderGuideSectionDto,
  ReaderPdfViewDto,
  ReaderPromptContractDto,
  LibraryAskEntry,
  LibraryHitDto,
  CorrespondentFigureDto,
  CorrespondentSectionDto,
  ProposedItemDto,
  ReaderRenderBlockDto,
  ReaderRenderViewDto,
  ReaderSourceSearchDto,
  ReaderWatchPlanDto,
  ReaderArcDto,
  ReaderCoachLintDto,
  SourceLibraryCard,
  ReaderAnnotationPlacementDto,
  ReadingPathExerciseDto,
} from "../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, TermSelect } from "../components/term";
import { MarkdownMath } from "../render/MarkdownMath";
import { SecondaryButton } from "../components/goldenpath/shared";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { youtubeVideoId } from "../components/sourceTail";
import { PdfReaderPane, type PdfReaderPaneHandle, type TagMenuRequest } from "../components/PdfReaderPane";
import { highlightFromPlacement, kindLabel, type PdfHighlight } from "../components/pdfSelection/highlights";
import { exactNode } from "../components/pdfSelection/model";
import { RectUnionOverlay } from "../components/RectUnionOverlay";
import { errorMessage, SPAN_MISMATCH_COPY } from "../errors";
import { DoseOffer } from "./reader/DoseOffer";
import { type AuthoredQuestionStatus } from "./reader/authoredQuestion";
import { searchBasisLabel } from "./reader/searchBasis";
import { readGuidePlan } from "./reader/guidePlan";
import { cachedSourceRead } from "./reader/readerCache";
import { PreparingView } from "./reader/PreparingView";
import { readerKeyBarKeys } from "./reader/readerKeys";
import { type ReadingPosition } from "./reader/readingPosition";
import { useBareAltClear } from "./reader/bareAlt";
import { useReaderRequests } from "./reader/useReaderRequests";
import { useReaderVisit } from "./reader/useReaderVisit";
import { useReadingProgress } from "./reader/useReadingProgress";
import { useReaderInquiry } from "./reader/useReaderInquiry";
import { YouTubeWatchPanel, type WatchPanelHandle } from "./reader/YouTubeWatchPanel";
import { useReaderCues, type CueCheckMeRequest, type CueRequestOrigin } from "./reader/useReaderCues";
import { CUE_COPY, type PdfPageLayout } from "./reader/cues";
import { CueFooter, MarginMark } from "./reader/MarginMark";
import type { PassageTarget, ReaderCueDto } from "../api/dto";

import { type AskAbout, type ReaderExchange } from "./reader/ReaderAskBranches";
import { DetourStrip } from "./reader/DetourStrip";
import { InquiryQuickCheck } from "./reader/InquiryQuickCheck";
import { ReconnectLine } from "./reader/ReconnectLine";
import {
  activitySince,
  learnerActivitySnapshot,
  logReaderAction,
  logReaderActivity,
  newActivityId,
} from "./reader/activity";
import { besideTrail, goTo as stackGoTo, type ReturnStack } from "./reader/returnStack";
import { AskRail } from "./reader/AskRail";
import { createTutorOfferStore } from "./reader/TutorOffers";
import { GuideRail, SectionBoundaryOffer } from "./reader/GuideRail";
import { ReadingPathCard } from "./reader/ReadingPathCard";
import { GuidePathSlot } from "./reader/DeliverableSliceCard";
import { readingPathRefreshKey } from "./reader/readingPath";
import { useReaderRecap } from "./reader/useReaderRecap";
import { RecapCard } from "./reader/RecapCard";
import { WrapUpPanel } from "./reader/WrapUpPanel";
import { RECAP_COPY } from "./reader/recapCopy";
import { NotesRail, type ExerciseImportState } from "./reader/NotesRail";
import { IntentBox } from "./reader/IntentBox";
import { useIntentBox, type IntentCancel, type IntentRunHandle, type IntentRunHow } from "./reader/useIntentBox";
import { useActiveReading } from "./reader/useActiveReading";
import { ActiveReadingCard, NextStepFoldLine } from "./reader/ActiveReadingCard";
import { FiguresUnder } from "./reader/figures/FigureInline";
import { useFigures, type FigureRequestOutcome, type FiguresCtl } from "./reader/figures/useFigures";
import type { ShowMeLine } from "./reader/figures/showMe";
import type { FigurePassageDto, FigureViewDto } from "../api/dto";
import { SCOPE_COPY, useLibraryAsk, type CompareRequest } from "./reader/useLibraryAsk";
import { LibraryPane, useComparingStacked } from "./reader/LibraryPane";
import { CompareKeepContext } from "./reader/compareKeepContext";
import { KeptMark } from "./reader/KeptMark";
import { useKeptComparisons } from "./reader/useKeptComparisons";
import { NoteLinkPicker, NoteMarkButton, NOTES_COPY, useNoteMarks } from "./reader/ReaderNotes";
import { ScopeFromPassage } from "./reader/ScopeFromPassage";
import { NotesContext } from "./reader/notesContext";
import { LibraryAnswer } from "./reader/LibraryAnswer";
import type { ReaderIntentActionDto, ReaderPresetReceiptDto } from "../api/dto";
import { algoConfig } from "../app/algoConfig";
import { STYLE_ANSWER_MODE, StoredHelpStyle, useStoredHelpStyle } from "../components/askPanel";
import { useReaderWorkbench, type ReaderWorkbenchProps } from "./reader/useReaderWorkbench";
import { exerciseOpenRequest, type ExerciseCandidate, type ReaderWorkbenchExercise } from "./reader/exerciseCandidates";
import type { ExplorableOutcome, LibraryExercisesProps } from "./reader/LibraryAnswer";
import { ReaderWorkingPosture } from "./reader/ReaderWorkingPosture";
import { FindSection } from "./reader/FindSection";
import { SideBySidePane } from "./reader/SideBySidePane";
import { SIDE_BY_SIDE_COPY, SIDE_BY_SIDE_SCROLL_KEYS, useSideBySide } from "./reader/useSideBySide";
import { clampSplit, crumbLabel, readSplit, targetOf as sideBySideTarget, writeSplit } from "./reader/sideBySide";
import { inSidePane, useSidePane, type PaneCaptureTarget, type SidePane } from "./reader/useSidePane";
import type { AskAnchor } from "./reader/useReaderInquiry";
import { ALSO_COPY, AlsoInBooks, type AlsoPeekCrumb } from "./reader/AlsoInBooks";
import { WORKBENCH_COPY, problemTitle } from "./workbench/stepModel";
import { screenLeavesKey } from "../app/keymap";
import {
  askGroundingSpans,
  clip,
  groundingProtected,
  passageKeys,
  placedSpanIds,
  selectionNodes,
  selectionProtected,
  type AnnotationSegment,
  type MarginAnnotation,
  type ReaderSelection,
} from "./reader/readerShared";

/** A stable empty list for the dose offer before the guide plan loads. */
const NO_SECTIONS: never[] = [];
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

/** How opening a book ended (an offer's press waiting on it settles on this). */
type OpenOutcome = "opened" | "preparing" | "not_opened";

/** RW5b: "make this explorable" pressed on an offer, waiting for its passage's
 *  book; `settle` tells the press how it ended (fix round 2, F9). */
interface OfferedPress {
  fromExtractionId: string | null;
  sourceId: string | null;
  extractionId: string;
  spanId: string;
  origin: "library" | "tutor";
  offerRef: string;
  settle: (outcome: ExplorableOutcome) => void;
}

/** The press's outcome for each way a figure request can end. */
const OFFER_OUTCOME: Record<FigureRequestOutcome, ExplorableOutcome> = {
  shown: "built", not_shown: "not_built", cancelled: "stopped", skipped: "figures_off",
};

// "unknown" just means no health row was computed for this extraction — badging
// it on every block reads as an error state; only suspect/failed warrant a pill.
const BADGED_HEALTH = new Set(["suspect", "failed"]);

/** A highlight the learner just removed: the Reader offers to undo it, on
 *  the reading it was removed from only (Codex review F4). */
interface RemovedAnnotation {
  annotation: MarginAnnotation;
  at: number;
  /** The delete's own event: the undo withdraws that one and no other. */
  deleteEventId: string;
  sourceId: string;
  extractionId: string;
}

/** How long "undo" stays offered after a highlight is removed. */
const UNDO_REMOVE_MS = 10_000;

function newKey(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `cap-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

/** Reader CA6b fix round 5: a render's book, revision and reading. */
function identityOf(view: Pick<ReaderRenderViewDto, "sourceId" | "revisionId" | "extractionId">): SourceIdentity {
  return { sourceId: view.sourceId, revisionId: view.revisionId, extractionId: view.extractionId };
}

/** Reader CA6b fix round 5: side by side's second pane's book, revision and reading. */
function sectionIdentity(section: { sourceId: string; revisionId?: string | null; extractionId: string }): SourceIdentity {
  return { sourceId: section.sourceId, revisionId: section.revisionId ?? null, extractionId: section.extractionId };
}

export interface ReaderOpenSource {
  card: SourceLibraryCard;
  spanId: string | null;
  /** The reading `spanId` was found on (UX Phase 3 fix round 1, F3: Today's
   *  threads): a span of another reading is translated, never opened as one
   *  of the reading the book opens on. Absent: the span is the open one's. */
  reading?: string | null;
  /** Reader CA6b (Codex re-review F8): the return stack to open with, so a
   *  check or a work through started from side by side's second pane keeps
   *  its way back there (Alt+← reopens side by side) across the shell's
   *  practice and feedback screens. Absent: the Reader opens as before. */
  besideTrail?: ReturnStack | null;
}

/** RW3a "check me" on a margin cue: the item to open as an ordinary attempt on
 *  your own, and the passage to come back to after its feedback. */
export interface ReaderCheckMeRequest extends CueCheckMeRequest {
  card: SourceLibraryCard;
  /** RW4b: the sources service's import that wrote the item (an exercise's pick). */
  importId?: string | null;
  /** RW4b: an admitted exercise resumes its own problem ("practice_this"). */
  entry?: "check_me" | "practice_this";
  /** Reader CA6b (Codex re-review F8): the way back to side by side, when the
   *  check came from its second pane (the shell hands it back to the Reader). */
  besideTrail?: ReturnStack | null;
}

/** RW4b "use this one" on a textbook exercise: the problem to open at once
 *  on its verbatim statement, in the source it comes from. */
export type ReaderExerciseRequest = ReaderWorkbenchExercise & { card: SourceLibraryCard };


/** Reader CA6b (Codex re-review F7): the second pane's reading path, in its pane. */
export const SIDE_PATH_COPY = {
  heading: (title: string) => `WHAT MATTERS IN ${title.toUpperCase()}`,
  close: "close",
} as const;

/** Reader CA6b (Codex review F9): the main pane's cue keys are not the
 *  second pane's (focus there moves among that pane's own marks). */
const mainPaneOwnsCueKey = (event: KeyboardEvent): boolean => !inSidePane(event.target);

/** Reader CA6b: what an intent acts on (one router, a context per pane): the
 *  main pane's selection, active reading and figures, or side by side's
 *  second pane's (`side`: its book, reading and capture target). */
interface IntentPane {
  side: SidePane | null;
  spanIds: string[];
  /** The selection's words (an edited capture's, in the main pane). */
  words: string;
  active: ReturnType<typeof useActiveReading>;
  fold: (spanIds: string[]) => string[];
  figures: ReturnType<typeof useFigures>;
  region: { spanId: string; bbox: number[] } | null;
}
export function ReaderScreen({
  onError,
  initialSource = null,
  onSourceChange,
  onOpenLibrary,
  shelf,
  onCheckMe,
  onUseExercise,
  workbench,
  onSkimmingChange,
  askRequest,
}: {
  onError: (message: string) => void;
  /** UX Phase 2: the palette's "Ask the tutor about this" with a book open.
   *  Each new value opens the rail on Ask and focuses its box; the value the
   *  Reader mounts with opens nothing. */
  askRequest?: number;
  /** The source that was open when the Reader last unmounted (hoisted by the shell). */
  initialSource?: ReaderOpenSource | null;
  onSourceChange?: (next: ReaderOpenSource | null) => void;
  /** "← Library" goes to the Library place, the one shelf (spec K5; usability
   *  round 1: the Reader's own list was a second "Library"). */
  onOpenLibrary?: () => void;
  /** With no book open, the Library's own shelf (spec K5, usability round 2:
   *  the Reader's own list read as a second Library). */
  shelf?: ReactNode;
  /** RW3a: open the item a margin cue's "check me" found, as a learner pick
   *  with the book out of view; absent, the cue offers no check me. */
  onCheckMe?: (request: ReaderCheckMeRequest) => void;
  /** RW4b: "use this one" on a textbook exercise, a learner pick the shell
   *  opens in the working posture; absent, the cards offer only the book. */
  onUseExercise?: (request: ReaderExerciseRequest) => void;
  /** RW2a: the workbench's shell wiring (the practice session, the submit's
   *  hand-off to feedback, back from feedback to the problem). The workbench
   *  itself shows only while workbench.enabled is on. */
  workbench?: ReaderWorkbenchProps;
  /** RW6a: whether the Reader is muted by skim (so leaving it while skimming
   *  arms no wrap-up offer where the learner lands; review F9). */
  onSkimmingChange?: (muted: boolean) => void;
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
  // RW7a: bumped by Orient's "what matters here?" (the path card scrolls into view).
  const [pathFocus, setPathFocus] = useState(0);
  const [annotations, setAnnotations] = useState<MarginAnnotation[]>([]);
  const [note, setNote] = useState("");
  const [answerModeChosen, setAnswerMode] = useState<ReaderAnswerMode>("answer_directly");
  // Reader CA2 (§7.4, §15 Q5): while the Ask panel is on, the help style is
  // the answer mode (one vocabulary, one stored preference); the per-source
  // select retires. Off: the per-source mode, exactly as before.
  const askPanelOn = algoConfig().ask !== null;
  const storedStyle = useStoredHelpStyle();
  const answerMode: ReaderAnswerMode = askPanelOn ? STYLE_ANSWER_MODE[storedStyle] : answerModeChosen;
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
  // The highlight just removed, while its undo is offered.
  const [removed, setRemoved] = useState<RemovedAnnotation | null>(null);
  // Bumps whenever the open book changes (resetSourceState): an annotation
  // read or write that answers after it never touches the new book's list.
  const sourceEpochRef = useRef(0);
  // UX Phase 1 (§6.3): a book whose text is still being prepared opens on its
  // original PDF in PreparingView; the full Reader takes over when it is ready.
  const [preparingCard, setPreparingCard] = useState<SourceLibraryCard | null>(null);
  const [railCollapsed, setRailCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem("learnloop.reader.rail-collapsed") === "on";
    } catch {
      return false;
    }
  });
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const railRef = useRef<HTMLDivElement | null>(null);
  const paneRef = useRef<PdfReaderPaneHandle | null>(null);
  const watchRef = useRef<WatchPanelHandle | null>(null);
  const askComposerRef = useRef<HTMLTextAreaElement | null>(null);
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

  // While the contract loads the Reader reads as enabled (new libraries have it
  // on); the "disabled" notice shows only once the config really says so
  // (UX Phase 1, §10 item 1.10: no flash of a config instruction on every open).
  const enabled = contract?.readerEnabled ?? true;
  // RW1a's kill switch (reader_inquiry.enabled): the sidecar names it only when
  // on, so an absent flag (switched off, or an older sidecar) is today's rail.
  const inquiry = contract?.inquiryEnabled === true;
  // Skim is the mute button (UX §3.1): with inquiry on, nothing LearnLoop
  // starts shows while skimming -- no reconnect line, no section offer.
  const muted = inquiry && mode === "skim";
  // RW1b's switches (the sidecar names each only while it is on, and only with
  // reader_inquiry on): the intent box, and active reading.
  const intentContract = inquiry && !offline ? contract?.intent ?? null : null;
  const activeReadingOn = inquiry && !offline && Boolean(contract?.activeReading);
  // RW5a: explorable figures (the contract names them only while figures.enabled is on).
  // RW5d P4a (Codex review F2): following figures from other books lives under CA5's switch.
  const figuresCtl = useFigures({ extractionId: render && !offline ? render.extractionId : null, contract: contract?.figures ?? null,
    followEnabled: Boolean(contract?.correspondence?.alsoInBooks) });
  // RW5b: "make this explorable" pressed on an offer (the library organizer's
  // or the tutor's own judgment; the contract names offers only while
  // figures.offers_enabled is on). The build runs where its passage is: in
  // this book at once, in another once that book is open (a detour).
  const figureOffersOn = Boolean(contract?.figures?.offers) && !offline;
  // RW5d P1: "show me" in the learner's words (the contract names it only while
  // figures.show_me_enabled is on): the intent box's words, the Ask rail's
  // "show me ▸" and the tutor's figure goal.
  const showMeOn = Boolean(contract?.figures?.showMe) && !offline;
  const [showMeLines, setShowMeLines] = useState<ShowMeLine[]>([]);
  useEffect(() => { setShowMeLines([]); }, [render?.extractionId]);
  // A press waiting for its passage's book (`waitingOfferRef` is the one that
  // may still dispatch: a newer press, or a lapse, replaces it).
  const [offeredFigure, setOfferedFigure] = useState<OfferedPress | null>(null);
  const waitingOfferRef = useRef<OfferedPress | null>(null);
  // Codex review F6, fix round 2 F9: the press hears how it ended -- built,
  // or why not (the book did not open, another opened, figures are off, the
  // build was refused) -- so its button never says "building" for a build
  // that will not run or has ended.
  const lapseOffered = useCallback((press: OfferedPress, outcome: ExplorableOutcome) => {
    if (waitingOfferRef.current !== press) return;
    waitingOfferRef.current = null;
    setOfferedFigure((current) => (current === press ? null : current));
    press.settle(outcome);
  }, []);
  useEffect(() => {
    const press = offeredFigure;
    if (!press || waitingOfferRef.current !== press) return;
    const open = render?.extractionId ?? null;
    if (open !== press.extractionId) {
      // Another book opened instead, or the hit's book opened on another
      // reading (its span ids are not this reading's, and the judgment named
      // that reading's block): the press lapses, and says so. With no book
      // on screen (the library page, a book being prepared) the open's own
      // outcome settles it (makeExplorable).
      if (open !== null && open !== press.fromExtractionId) {
        lapseOffered(press, render?.sourceId === press.sourceId ? "another_reading" : "another_book");
      }
      return;
    }
    if (!figuresCtl.enabled || !figuresCtl.contract?.offers) {
      lapseOffered(press, "figures_off");
      return;
    }
    waitingOfferRef.current = null;
    setOfferedFigure(null);
    // Settled on the build's own outcome, not on its dispatch.
    void figuresCtl.request({ spanIds: [press.spanId], origin: press.origin, offerRef: press.offerRef })
      .then((outcome) => press.settle(OFFER_OUTCOME[outcome]));
  }, [offeredFigure, figuresCtl, render, lapseOffered]);
  // RW1c: the tutor that looks things up (absent from the contract while both its switches are off).
  const readerTutor = contract?.readerTutor ?? null;
  // RW1c: the bound workbench session an Ask comes from (set once the workbench hook runs below).
  const askWorkbenchSessionRef = useRef<string | null>(null);
  // RW1c (Codex review F8): the composer's personalized chip, at the vault's
  // default until the learner switches it; sent with every Ask while the
  // tutor looks things up.
  const [askPersonalized, setAskPersonalized] = useState<boolean | null>(null);
  const askPersonalizedOn = askPersonalized ?? readerTutor?.personalizedDefault ?? true;
  const askPersonalizedRef = useRef<boolean | null>(null);
  askPersonalizedRef.current = readerTutor?.retrieval ? askPersonalizedOn : null;
  // Reader CA6b: an empty Enter in side by side's second pane opens the
  // composer on that pane's selection (null: the open book's, as before).
  const [askComposerAnchor, setAskComposerAnchor] = useState<AskAnchor | null>(null);
  const askComposerAnchorRef = useRef<AskAnchor | null>(null);
  askComposerAnchorRef.current = askComposerAnchor;
  // RW1c (Codex review F6): the offers' lookups belong to their exchanges, so
  // collapsing an answer runs nothing again.
  const [tutorOfferStore] = useState(createTutorOfferStore);

  const blocks: ReaderRenderBlockDto[] = useMemo(
    () => (render?.blocks ?? []).filter((b) => !FURNITURE_BLOCK_TYPES.has(b.blockType ?? "")),
    [render],
  );
  const renderBlocksBySpan = useMemo(
    () => new Map(blocks.flatMap((block) => (block.spanId ? [[block.spanId, block] as const] : []))),
    [blocks],
  );

  // The visit and the funnel's bookkeeping (RW1a; screens/reader/useReaderVisit).
  const visit = useReaderVisit({ render, offline, inquiry, pdfView });
  const { visitPayload, noteSelection, resetVisitState } = visit;

  // Reading progress and the section checks' offers (UX Phase 1, reading-
  // hardening; screens/reader/useReadingProgress). checkOffer.ts stays the one
  // offer rule: every offer path below reads `offeredCheckSections`.
  const showGuideRail = useCallback(() => {
    setRailCollapsed(false);
    setRailTab("guide");
  }, []);
  const progress = useReadingProgress({
    render, offline, blocks, guidePlan, setGuidePlan, guideLoading, pdfView, pdfViewPending, surface,
    watch, watchLoading, mode, inquiry, muted, activeSpan, setActiveSpan, bodyRef, railRef, paneRef, watchRef,
    noteProactive: visit.noteProactive, showGuideRail,
  });
  const {
    readingSpan, setReadingSpan, sectionSeen, readingMoved, focusQuickCheck, setHiddenPdfOffers,
    answeredSections, setAnsweredSections, revealedSections, dismissedSections, setDismissedSections,
    completedSections, sectionPromptsEnabled, setSectionPromptsEnabled, boundaryChecksAvailable,
    authoringSections, timedOutSections, guideSectionByEnd, currentGuideSection, currentSectionProgress,
    currentSectionRead, pdfSurfaceActive, offeredCheckSections, openQuestionSections, pendingQuickCheckCount,
    currentQuestionOpen, pdfOfferSection, readingProgress, retryQuickCheck, openQuickCheck, revealSection,
    completeSection, jumpToSpan, noteUserScroll, onPlaybackSpan, onPlaybackSeek, settleOpening, placeAtOpen,
    hydrateProgress, resetProgress,
  } = progress;

  // Adaptive difficulty AD2+AD3: the dose offer's visit (a stable reader of the live visit).
  const doseVisitId = useCallback(() => visit.visitRef.current?.id ?? null, [visit.visitRef]);

  const refreshAnnotations = useCallback(async () => {
    if (!render || offline) return;
    const epoch = sourceEpochRef.current;
    try {
      // With the open reading, each annotation also says where it lands on it
      // (span_aliases decides): the original PDF draws it on its words there.
      const result = await cachedSourceRead(
        render.sourceId,
        ["reader_source_annotations", render.sourceId, render.extractionId],
        () => api.readerSourceAnnotations({ sourceId: render.sourceId, extractionId: render.extractionId }),
      );
      // Another book opened meanwhile: these rows are not its annotations.
      if (epoch !== sourceEpochRef.current) return;
      const rows = (result.annotations as Array<Record<string, unknown>>) ?? [];
      setAnnotations(
        rows.map((r) => {
          const version = (r.version as Record<string, unknown>) ?? {};
          const segments = (r.segments as Array<Record<string, unknown>>) ?? [];
          const anchor = (r.anchor as Record<string, unknown>) ?? {};
          const annotation = (r.annotation as Record<string, unknown>) ?? {};
          const placement = r.placement as ReaderAnnotationPlacementDto | undefined;
          return {
            annotationId: (annotation.id as string) ?? null,
            quote: (segments[0]?.exactQuote as string) ?? "",
            status: (anchor.status as string) ?? null,
            learnerText: (version.learnerText as string) ?? "",
            kind: (version.annotationType as string) ?? "highlight",
            ...(placement ? { placement } : {}),
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

  // RW1a's inquiry: the Ask and its branches, the return stack, the reconnect
  // line, inquiry status and the passage quick check (screens/reader/useReaderInquiry).
  const openSourceRef = useRef<((card: SourceLibraryCard, jumpSpan?: string, options?: { via?: "search" | "restore"; handoff?: ReadingPosition | null; jumpReading?: string | null }) => Promise<OpenOutcome>) | null>(null);
  const {
    question, setQuestion, askComposerVersion, parentExchange, setParentExchange, history, visibleAskHistory,
    normalizedAskFind, collapsedAskIds, setCollapsedAskIds, askFindOpen, setAskFindOpen, askFindQuery,
    setAskFindQuery, askFindInputRef, askPhase, askTabMarked, returnStack, returnStackRef, reconnect,
    inquiryChecks, passageCheckOffered, submitAsk, ask, retryAsk, forgetFailedAsk, seedReturnStack, askAnotherWay, askDidntHelp, cancelAsk,
    setInquiryStatus, markBranchDone, commitInquiry,
    committedFor, openInquiry, startQuickCheck, cancelQuickCheck, dismissInquiryCheck, answerReconnect, inquiryCheckAction,
    escalateInquiryCheck, peekPassage, restoreEntry, onBodyScroll, noteSourceOpened, rememberLeftSource,
    resetInquiryState, pushSideBySide, replaceSideBySide, snapshotSideBySide, dropDetour,
  } = useReaderInquiry({
    render, offline, inquiry, muted, library, sourceTitle, selection, setSelection, setSelectionActions,
    activeSpan, railTab, setRailTab, answerMode, setBusy, onError, annotations, refreshAnnotations, setArc,
    visit, readingSpan,
    guideSectionBySpan: progress.guideSectionBySpan, jumpToSpan, onReadingScroll: progress.onReadingScroll,
    jumpGuardRef: progress.jumpGuardRef, bodyRef, askComposerRef, openSourceRef,
    onRestored: progress.noteRestored,
    workbenchSessionRef: askWorkbenchSessionRef,
    personalizedRef: askPersonalizedRef,
    composerAnchorRef: askComposerAnchorRef,
  });

  // RW3a: margin cues from the Guide's own citations (screens/reader/useReaderCues).
  // The original's pages as its pane lays them out (each page's own size).
  const [pdfLayout, setPdfLayout] = useState<PdfPageLayout | null>(null);
  const openCardRef = useRef<SourceLibraryCard | null>(null);
  // The source open now, for answers that arrive late (RW3a review F3).
  const openExtractionRef = useRef<string | null>(null);
  openExtractionRef.current = render && !offline ? render.extractionId : null;
  const reloadGuidePlan = useCallback(async () => {
    if (!render || offline) return;
    const extractionId = render.extractionId;
    try {
      const plan = await readGuidePlan(render.sourceId, extractionId, { force: true });
      // Only for the source still open: a re-read for a book the learner has
      // left never replaces the open book's plan (review F3).
      if (openExtractionRef.current !== extractionId || plan.extractionId !== extractionId) return;
      if (openCardRef.current && openCardRef.current.sourceId !== render.sourceId) return;
      setGuidePlan((current) => {
        if (current && current.extractionId && current.extractionId !== extractionId) return current;
        return current && current.sections.length > 0 && plan.sections.length === 0 ? current : plan;
      });
    } catch {
      /* The Guide keeps what it had; the next open re-reads. */
    }
  }, [render, offline]);
  const spanOrder = useMemo(
    () => new Map(blocks.flatMap((block, index) => (block.spanId ? [[block.spanId, index] as const] : []))),
    [blocks],
  );
  const cueSurface = watch ? "watch" : pdfView && surface === "pdf" && !offline ? "pdf" : render && !watchLoading ? "text" : "none";
  // The card that goes with a check me is the card of the source it was asked
  // on, and only while that source is still the one open (review F3).
  const checkMeFromCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin) => {
    const card = openCardRef.current;
    if (!card || !onCheckMe) return;
    if (card.sourceId !== origin.sourceId || openExtractionRef.current !== origin.extractionId) return;
    onCheckMe({ ...request, card });
  }, [onCheckMe]);
  // RW2a: the working posture (off: no entry anywhere, the Reader as before).
  // Reader CA6b (Codex re-review F8): a submit made on a book taken from side
  // by side's second pane keeps the way back there for the shell's feedback
  // screen (the return stack, while side by side comes before the current
  // entry); every other submit is handed on exactly as before.
  const wbProps = useMemo<ReaderWorkbenchProps | undefined>(() => {
    const submitted = workbench?.onSubmitted;
    if (!workbench || !submitted) return workbench;
    return {
      ...workbench,
      onSubmitted: (result, at) => {
        const trail = besideTrail(returnStackRef.current);
        submitted(result, trail ? { ...at, besideTrail: trail } : at);
      },
    };
  }, [workbench, returnStackRef]);
  const wbCtl = useReaderWorkbench({
    enabled: algoConfig().workbench && !offline,
    extractionId: render?.extractionId ?? null,
    card: openCardRef.current,
    props: wbProps,
    onError,
  });
  const working = wbCtl.active !== null;
  // Reader CA5: "also in your books" (the contract names it only while
  // reader.correspondence.enabled and curriculum.enabled are on). Shown in skim
  // mode (a table of contents), never in the working posture or offline.
  const alsoOn = Boolean(contract?.correspondence?.alsoInBooks) && !offline;
  // The learner's hide preferences: the contract's, or what was just set here
  // (until the contract itself changes, e.g. Settings brought the line back).
  const [alsoPrefs, setAlsoPrefs] = useState<{ everywhere: boolean; sources: string[] } | null>(null);
  useEffect(() => setAlsoPrefs(null), [contract]);
  const alsoHidden = alsoPrefs
    ? alsoPrefs.everywhere || Boolean(render && alsoPrefs.sources.includes(render.sourceId))
    : Boolean(contract?.correspondence?.hiddenEverywhere)
      || Boolean(render && (contract?.correspondence?.hiddenSources ?? []).includes(render.sourceId));
  const [alsoAvailable, setAlsoAvailable] = useState(false);
  const [alsoExpandToken, setAlsoExpandToken] = useState(0);
  const [alsoClosePeekToken, setAlsoClosePeekToken] = useState(0);
  const [alsoPeek, setAlsoPeek] = useState<AlsoPeekCrumb | null>(null);
  // CA5a's pressed list peeks too (Codex review F4): one display-only crumb for either list.
  const [findPeek, setFindPeek] = useState<AlsoPeekCrumb | null>(null);
  const peekCrumbShown = alsoPeek ?? findPeek;
  const [coverageRefresh, setCoverageRefresh] = useState(0);
  // RW7a (Codex review F3, re-review F3): what the mounted reading-path card
  // re-reads on, a landed progress save included.
  // The Guide being shown again, the plan re-read (a diagnosis landed), a
  // quick check answered, a workbench problem submitted or set aside, and
  // each section read through or finished.
  const [guideShown, setGuideShown] = useState(0);
  useEffect(() => {
    if (railTab === "guide" && !railCollapsed) setGuideShown((value) => value + 1);
  }, [railTab, railCollapsed]);
  const [guideReads, setGuideReads] = useState(0);
  useEffect(() => {
    if (guidePlan) setGuideReads((value) => value + 1);
  }, [guidePlan]);
  const pathRefreshKey = readingPathRefreshKey({
    sections: guidePlan?.sections ?? [],
    completedSections,
    sectionSeen,
    progressSaves: progress.progressSaves,
    signals: [guideShown, guideReads, answeredSections.length,
      wbCtl.sessions.map((entry) => `${entry.sessionId}:${entry.status}`).join(",")],
  });
  // Sent whenever EITHER RW1c switch is on (fix round 4, F3): the server
  // derives the bound item's restriction from it (a cold administration
  // refuses tools and offers), with retrieval off too. `readerTutor` is
  // in the contract only while one of them is on.
  askWorkbenchSessionRef.current = readerTutor && wbCtl.active?.session.practiceItemId
    ? wbCtl.active.session.sessionId : null;
  const tryFirstRef = useRef<((spanId: string) => void) | null>(null);
  const cueCtl = useReaderCues({
    working,
    render, offline, guidePlan, reloadGuidePlan, skimming: mode === "skim", restoredSpanId: progress.restoredSpan,
    surface: cueSurface, pdfBlocks: pdfView?.blocks ?? null, pdfLayout, bodyRef,
    layoutKey: `${render?.renderViewId ?? ""}:${surface}:${guidePlan?.extractionId ?? ""}:${blocks.length}:${railCollapsed ? 1 : 0}`,
    spanOrder, readingSpan, visitPayload, jumpToSpan, notePlacement: progress.notePlacement,
    onCheckMe: onCheckMe ? checkMeFromCue : undefined,
    // RW3b: "try the next step first" is RW1b's next-step question at that line.
    onTryFirst: activeReadingOn ? (spanId: string) => tryFirstRef.current?.(spanId) : undefined, onError,
    // Reader CA6b (Codex review F9): Alt+↓ / Alt+↑ with focus in side by
    // side's second pane are that pane's (its own cue controller).
    ownsKey: mainPaneOwnsCueKey,
  });
  // RW6a: "Last time here" and Wrap up (screens/reader/useReaderRecap). Off
  // (no `recap` key from the sidecar) it asks nothing and renders nothing.
  const recapCtl = useReaderRecap({
    enabled: algoConfig().recap && Boolean(render) && !offline,
    wrapUpEnabled: algoConfig().wrapUp && Boolean(render) && !offline,
    extractionId: render && !offline ? render.extractionId : null,
    visitId: () => visit.visitRef.current?.id ?? null,
    readingMoved,
    activityKey: `${history.length}:${wbCtl.sessions.length}:${wbCtl.active?.session.sessionId ?? ""}`,
    suspended: working,
    // Skim is the mute button (UX §4.12; review F9).
    muted,
    // `w` and the footer open Wrap up where it can be seen (review F6).
    reveal: showGuideRail,
    onError,
  });
  const recapShown = Boolean(recapCtl.recap && !recapCtl.collapsed && !muted && railTab === "guide" && !(inquiry && railCollapsed) && !working);
  // Leaving while skimming offers no wrap-up where the learner lands (F9).
  useEffect(() => {
    onSkimmingChange?.(muted);
  }, [muted, onSkimmingChange]);
  const { noteShown: noteRecapShown } = recapCtl;
  useEffect(() => {
    if (recapShown) noteRecapShown();
  }, [recapShown, noteRecapShown]);
  /** A status chip from the card or Wrap up: the inquiry hook's own call
   *  when the root is in this source's history, so the Ask rail follows. */
  const recapSetStatus = useCallback(async (rootId: string, resolution: "open" | "resolved", trigger: "chip" | "undo" = "chip") => {
    const root = history.find((entry) => entry.id === rootId);
    if (root) await setInquiryStatus(root, resolution);
    else if (render) {
      try {
        await api.readerSetInquiryStatus({ extractionId: render.extractionId, exchangeId: rootId, resolution, trigger });
      } catch (error) {
        onError(errorMessage(error));
      }
    }
    recapCtl.reload();
  }, [history, setInquiryStatus, render, onError, recapCtl]);
  // "revisit once" from the card or Wrap up is the Ask chip's own commitment:
  // one state, one in-flight guard, one idempotency key (review F2).
  const recapRevisited = useCallback((rootId: string) => {
    const root = history.find((entry) => entry.id === rootId);
    return Boolean(root && committedFor(root).has("test_me_later"));
  }, [history, committedFor]);
  const recapRevisit = useCallback(async (rootId: string) => {
    const root = history.find((entry) => entry.id === rootId);
    if (!root || committedFor(root).has("test_me_later")) return;
    await commitInquiry(root, "test_me_later");
    recapCtl.reload();
  }, [history, commitInquiry, committedFor, recapCtl]);
  // "open": that inquiry, expanded and in view on Ask, with its crumb (F5).
  const recapOpenInquiry = useCallback((rootId: string, spanId: string) => {
    openInquiry(rootId, spanId);
  }, [openInquiry]);
  const renderMark = (cue: ReaderCueDto, markSurface: "text" | "pdf" | "watch") => (
    <MarginMark
      key={cue.cueId}
      cue={cue}
      open={cueCtl.openCueId === cue.cueId}
      onOpenChange={(open) => cueCtl.setOpenCueId(open ? cue.cueId : null)}
      surface={markSurface}
      canCheckMe={cueCtl.canCheckMe}
      checkPhase={cueCtl.checkPhase(cue.cueId)}
      onOpenEarlier={() => cueCtl.openEarlier(cue)}
      onCheckMe={() => cueCtl.checkMe(cue)}
      onNotRelevant={(text) => cueCtl.notRelevant(cue, text)}
      onFewer={() => cueCtl.fewerOn(cue)}
      onOffBook={cueCtl.offBook}
      onOffEverywhere={cueCtl.offEverywhere}
      onSeen={(planId) => cueCtl.noteSeen(cue, planId)}
      planId={cueCtl.planId}
      {...(cueCtl.canTryFirst ? { onTryFirst: () => cueCtl.tryFirst(cue) } : {})}
    />
  );
  const cueMarksFor = (markSurface: "pdf" | "watch") =>
    cueCtl.placement.shown.length > 0
      ? new Map(cueCtl.placement.shown.map((cue) => [cue.spanId, renderMark(cue, markSurface)] as const))
      : null;

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

  // Reset per-source panel state so nothing from the previous source leaks over.
  const resetSourceState = useCallback(() => {
    // Leaving a book for another (or for the Library) saves what was read in
    // it first, as closing the Reader does (useReadingProgress).
    resetProgress();
    // The next original reports its own pages (RW3a review F5).
    setPdfLayout(null);
    // The Ask, its history and RW1a's per-source state (the return stack
    // itself survives a detour into another source; openSource decides).
    resetInquiryState();
    setBusy(false);
    setGuidePlan(null);
    setGuideLoading(false);
    setActiveSpan(null);
    setSelection(null);
    setSelectionActions([]);
    setRailTab("guide");
    setAnnotations([]);
    setNote("");
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
    setEditingAnnotationId(null);
    setEditingAnnotationText("");
    // A removal's undo belongs to the book it was removed from.
    setRemoved(null);
    sourceEpochRef.current += 1;
    resetVisitState();
  }, [resetProgress, resetInquiryState, resetVisitState]);

  const openSource = useCallback(
    async (
      card: SourceLibraryCard,
      jumpSpan?: string,
      // jumpReading: the reading jumpSpan was found on (a search hit, a
      // return); another reading's span is translated, never opened as a span
      // of the reading the book opens on now (Codex review F8).
      options: { via?: "search" | "restore"; handoff?: ReadingPosition | null; jumpReading?: string | null } = {},
    ): Promise<OpenOutcome> => {
      const handoff = options.handoff ?? null;
      progress.handoffRef.current = handoff;
      if (card.readiness !== "ready") {
        // Nothing to render yet: show the original while LearnLoop prepares it.
        resetSourceState();
        setRender(null);
        setPreparingCard(card);
        onSourceChange?.({ card, spanId: null });
        return "preparing";
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
        openCardRef.current = card;
        // Opening restores a position: following starts once it has settled.
        settleOpening();
        // RW1a: another source after leaving one is a detour (useReaderInquiry).
        noteSourceOpened(card, jumpSpan && options.jumpReading ? options.jumpReading : view.extractionId, jumpSpan, options.via);
        setRender(view);
        setOffline(false);
        setSourceTitle(card.title);
        // The shell remembers the SOURCE, not the jump: a search hit lands the
        // learner on the passage once; returning to this tab later resumes
        // from the saved reading position, not the original hit.
        onSourceChange?.({ card, spanId: null });
        // The saved place, a search hit's passage over it, or (with neither)
        // the reading history once it is read (useReadingProgress).
        placeAtOpen(
          view.sourceId, jumpSpan, handoff,
          { extractionId: view.extractionId, aliasedFrom: view.aliasedFrom ?? [], otherReadings: view.otherReadings },
          options.jumpReading ?? null,
        );
        setGuideLoading(true);
        readGuidePlan(card.sourceId, view.extractionId)
          .then(setGuidePlan)
          .catch(() => setGuidePlan(null))
          .finally(() => setGuideLoading(false));
        // Hydrate durable reading progress so reveal/completion survive restarts.
        cachedSourceRead(card.sourceId, ["reader_get_progress", view.extractionId], () =>
          api.readerGetProgress({ extractionId: view.extractionId })
        )
          .then((rows) => hydrateProgress(view.extractionId, rows))
          .catch(() => undefined);
        if (youtubeVideoId(card.canonicalUri ?? "") !== null) {
          setWatchLoading(true);
          cachedSourceRead(card.sourceId, ["reader_watch_plan", card.sourceId], () => api.readerWatchPlan(card.sourceId))
            .then(setWatch)
            .catch(() => setWatch(null))
            .finally(() => setWatchLoading(false));
        } else {
          // Original-PDF surface when the originals store has this revision's bytes.
          // Its block geometry is the rendered reading's: a source id would
          // resolve to the book's latest reading, which may have completed
          // since the render, with other span ids (re-read safety, Codex
          // re-review F10's class).
          const pdfRequest = ++pdfViewRequestRef.current;
          const current = () => pdfViewRequestRef.current === pdfRequest;
          setPdfViewPending(true);
          cachedSourceRead(card.sourceId, ["reader_pdf_view", view.extractionId], () =>
            api.readerPdfView({ extractionId: view.extractionId })
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
        return "opened";
      } catch (error) {
        setPreparingCard(null);
        onError(errorMessage(error));
        // A source that no longer opens (deleted, re-extracted away) must not
        // be resumed on every return to this tab.
        onSourceChange?.(null);
        return "not_opened";
      } finally {
        openingRef.current = null;
        setOpening(null);
        setOpeningTitle(null);
      }
    },
    // progress.handoffRef is a stable ref.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [onError, onSourceChange, resetSourceState, settleOpening, noteSourceOpened, placeAtOpen, hydrateProgress],
  );
  openSourceRef.current = openSource;

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
      rememberLeftSource({
        id: newActivityId(), kind: "origin", sourceId: render.sourceId, sourceTitle,
        extractionId: render.extractionId, spanId, selection, railTab, exchangeId: null,
        label: [sourceTitle, section?.label].filter(Boolean).join(" · ") || "where I was",
        openedAt: Date.now(),
      });
    }
    resetSourceState();
    setPreparingCard(null);
    setRender(null);
    setOffline(false);
    setSourceTitle(null);
    onSourceChange?.(null);
  }, [onSourceChange, resetSourceState, render, offline, readingSpan, activeSpan, guidePlan, sourceTitle, selection, railTab, rememberLeftSource]);

  // Resume the source that was open when this tab was last left: the shell
  // keeps the card, the cache keeps the reads, so the return is instant.
  const resumedRef = useRef(false);
  useEffect(() => {
    if (resumedRef.current || !initialSource || render) return;
    resumedRef.current = true;
    const trail = initialSource.besideTrail ?? null;
    void openSource(
      initialSource.card,
      initialSource.spanId ?? undefined,
      initialSource.spanId && initialSource.reading ? { jumpReading: initialSource.reading } : {},
    ).then((outcome) => {
      // Reader CA6b (Codex re-review F8): back from a check or a work through
      // that began in side by side's second pane, the way back there is the
      // stack it left (the current entry is this book; side by side is behind it).
      if (outcome === "opened" && trail && trail.entries[trail.cursor]?.sourceId === initialSource.card.sourceId) seedReturnStack(trail);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeBlock = useMemo(() => blocks.find((block) => block.spanId === activeSpan) ?? null, [blocks, activeSpan]);

  // The learner's highlights and notes on the original PDF, drawn from their
  // anchors on the open reading (reader-pdf-selection): where the sidecar
  // placed each one through span_aliases (here, moved after a re-read, or
  // flagged where its words changed). A capture made just now is drawn from
  // its own offsets until the sidecar's placement arrives. needs_reanchor and
  // annotations on no block of this reading are shown in the rail only: a
  // region we can no longer vouch for is never painted (no false attachment).
  const pdfHighlights: PdfHighlight[] = useMemo(() => {
    const list: PdfHighlight[] = [];
    annotations.forEach((a, index) => {
      if (removed?.annotation === a) return;
      const base = { id: a.annotationId ?? `local-${index}`, kind: a.kind, quote: a.quote, note: a.learnerText };
      if (a.placement) {
        const placed = highlightFromPlacement(base, a.placement);
        if (placed) list.push(placed);
        return;
      }
      if (a.status === "needs_reanchor") return;
      const segments = a.segments.flatMap((s) =>
        typeof s.start === "number" && typeof s.end === "number" ? [{ spanId: s.spanId, start: s.start, end: s.end }] : [],
      );
      if (segments.length) list.push({ ...base, state: "here", segments, flagSpanId: null });
    });
    return list;
  }, [annotations, removed]);
  const annotatedSpans = useMemo(
    () => new Set(annotations.filter((a) => removed?.annotation !== a).flatMap((a) => placedSpanIds(a))),
    [annotations, removed],
  );
  const boundaryBlock = useMemo(() => blocks.find((b) => (b.blockType ?? "") !== "Section") ?? null, [blocks]);

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

  // What the reading's protection holds out (exam_material decides): a
  // selection touching it offers no model action (rule 4 holds a whole
  // reading back until it is marked).
  const protection = (pdfView && pdfView.extractionId === render?.extractionId ? pdfView.protection : null) ?? render?.protection ?? null;
  const protectedSelection = selectionProtected(protection, selection);
  const protectionMessage = protectedSelection ? protection?.message ?? "This passage is held out of LearnLoop's models." : null;
  // The Ask is held back by what it would send now (Codex review F2): an
  // inherited thread's passage, the selection, or with neither the active
  // passage; on a reading held back whole, always.
  const askProtected = groundingProtected(protection, askGroundingSpans(inquiry ? parentExchange : null, selection, activeSpan));
  const askProtectionMessage = askProtected ? protection?.message ?? "This passage is held out of LearnLoop's models." : null;

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
        rawSelection: { extractionId: render.extractionId, nodes: selectionNodes(selection) },
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
  // kept; the listing honors the intent, so the card leaves the rail. Undo
  // (reader-pdf-selection) withdraws the delete: the annotation comes back
  // with its anchor and history, on the page and in the rail.
  const deleteAnnotation = useCallback(async (annotationId: string) => {
    const target = annotations.find((a) => a.annotationId === annotationId);
    const reading = render ? { sourceId: render.sourceId, extractionId: render.extractionId } : null;
    const epoch = sourceEpochRef.current;
    setBusy(true);
    try {
      const { eventId } = await api.readerDeleteIntentAnnotation({ annotationId });
      // Another book opened meanwhile: its list and its undo are its own.
      if (epoch !== sourceEpochRef.current) return;
      setAnnotations((list) => list.filter((a) => a.annotationId !== annotationId));
      if (target && reading && eventId) setRemoved({ annotation: target, at: Date.now(), deleteEventId: eventId, ...reading });
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [annotations, render, onError, refreshAnnotations]);
  const undoRemove = useCallback(async () => {
    const last = removed;
    if (!last?.annotation.annotationId) return;
    setRemoved(null);
    // Only on the reading it was removed from: its placement means nothing
    // on another book's (or another reading's) blocks.
    if (!render || render.sourceId !== last.sourceId || render.extractionId !== last.extractionId) return;
    const epoch = sourceEpochRef.current;
    try {
      const result = await api.readerRestoreAnnotation({ annotationId: last.annotation.annotationId, deleteEventId: last.deleteEventId });
      if (epoch !== sourceEpochRef.current) return;
      // Drawn again at once, unless another delete of it still stands.
      if (result.listed) {
        setAnnotations((list) => (list.some((a) => a.annotationId === last.annotation.annotationId) ? list : [last.annotation, ...list]));
      }
      void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [removed, render, onError, refreshAnnotations]);
  useEffect(() => {
    if (!removed) return;
    const timer = window.setTimeout(() => setRemoved(null), Math.max(0, removed.at + UNDO_REMOVE_MS - Date.now()));
    return () => window.clearTimeout(timer);
  }, [removed]);
  // Ctrl+Z undoes the removal while it is offered (never inside a text field).
  useEffect(() => {
    if (!removed) return;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if (!(event.ctrlKey || event.metaKey) || event.shiftKey || event.key.toLowerCase() !== "z") return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select"))) return;
      event.preventDefault();
      void undoRemove();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [removed, undoRemove]);
  // A highlight's "open note" on the page: its card in Notes, its note open.
  const openAnnotationNote = useCallback((annotationId: string) => {
    const target = annotations.find((a) => a.annotationId === annotationId);
    if (!target) return;
    setRailCollapsed(false);
    setRailTab("notes");
    setEditingAnnotationId(annotationId);
    setEditingAnnotationText(target.learnerText);
  }, [annotations]);

  // Split the live selection into one sub-quote per covered [data-span-id]
  // block, in document order. Anchoring works per block, so a quote must never
  // cross a block boundary — the old single-anchor capture silently failed on
  // any multi-block selection (every transcript selection, in practice).
  const collectSelectionNodes = useCallback((): Array<{ spanId: string; quote: string; start?: number; end?: number }> => {
    const sel = window.getSelection();
    const container = bodyRef.current;
    if (!sel || sel.isCollapsed || sel.rangeCount === 0 || !container) return [];
    const range = sel.getRangeAt(0);
    const nodes: Array<{ spanId: string; quote: string; start?: number; end?: number }> = [];
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
        // The same node the original PDF sends when the quote is found once
        // in the block's own text (one selection model on both views).
        const block = renderBlocksBySpan.get(spanId);
        nodes.push(block && !block.sanitized ? exactNode(block.markdown, { spanId, quote }) : { spanId, quote });
      }
    }
    return nodes;
  }, [renderBlocksBySpan]);

  // RW1b: the intent box on a learner's selection, and active reading. Its
  // actions run through the palette's own handlers (runIntentRef, set below
  // once they exist), so a routed action makes exactly the palette's call.
  const runIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow) => Promise<IntentRunHandle | null> | void>(() => undefined);
  const cancelIntentRunRef = useRef<(cancel: IntentCancel) => void>(() => undefined);
  const selectionSpanIds = useMemo(
    () => (selection ? [...new Set(selectionNodes(selection).map((node) => node.spanId))] : []),
    [selection],
  );
  const intentBox = useIntentBox({
    contract: intentContract,
    extractionId: render && !offline ? render.extractionId : null,
    spanIds: selectionSpanIds,
    quote: selection ? (selection.editedText ?? selection.quote) : "",
    muted,
    protectedSelection,
    notes: openCardRef.current?.acquisitionKind === "textfile",
    canWorkThrough: wbCtl.enabled,
    hostRef: bodyRef,
    onRun: (action, text, how) => runIntentRef.current(action, text, how),
    onCancelRun: (cancel) => cancelIntentRunRef.current(cancel),
  });
  const { noteSelection: noteIntentSelection, noteSelectionCleared: noteIntentCleared } = intentBox;
  const openActiveRail = useCallback(() => {
    setRailCollapsed(false);
    setRailTab("notes");
  }, []);
  const activeCtl = useActiveReading({
    extractionId: activeReadingOn && render ? render.extractionId : null,
    sourceId: render?.sourceId ?? null,
    onError,
    onOpenRail: openActiveRail,
  });
  // RW4a: ask your library, in the comparing posture beside the open source
  // (and in place on the library page). Off (no `libraryAsk` in the contract)
  // nothing renders and no key does anything new.
  const libraryCtl = useLibraryAsk({ contract, openSourceId: render?.sourceId ?? null, onError });
  // RW4d: the ⇄ marks of comparisons the learner kept (off: none, nothing read).
  const keptCtl = useKeptComparisons({ contract, extractionId: render?.extractionId ?? null, sourceId: render?.sourceId ?? null, offline });
  // Curriculum C2: the › marks of the learner's linked notes (off: none, nothing read).
  const notesCtl = useNoteMarks({ settings: contract?.notes, extractionId: render?.extractionId ?? null, offline });
  const [notePicker, setNotePicker] = useState<{ spanId: string; x: number; y: number } | null>(null);
  // RW4d on the original PDF (Codex review F10): the ⇄ marks join the page's
  // overlay gutter beside the cue marks. They are the learner's own marks:
  // added after the cue placement, so the density setting never counts them.
  const pdfMarks = (): ReadonlyMap<string, ReactNode> | null => {
    const cues = cueMarksFor("pdf");
    if (working || (keptCtl.marks.size === 0 && notesCtl.marks.size === 0)) return cues;
    const merged = new Map<string, ReactNode>(cues ?? []);
    for (const [spanId, mark] of keptCtl.marks) {
      const cue = merged.get(spanId);
      merged.set(spanId, <Fragment key={`kept-${spanId}`}>{cue}<KeptMark mark={mark} surface="pdf" below={Boolean(cue)} /></Fragment>);
    }
    // Curriculum C2: the › marks join the gutter too, below a cue and a ⇄ (the learner's own marks).
    for (const [spanId, mark] of notesCtl.marks) {
      const before = merged.get(spanId);
      merged.set(spanId, <Fragment key={`note-${spanId}`}>{before}<NoteMarkButton mark={mark} surface="pdf" below={Boolean(before)} /></Fragment>);
    }
    return merged;
  };
  const [libraryCompose, setLibraryCompose] = useState<string | null>(null);
  const comparing = Boolean(render) && !offline && !working && (libraryCtl.open || libraryCompose !== null);
  // Reader CA4: below the breakpoint the comparing posture stacks (off: RW4a's split).
  const comparingStacked = useComparingStacked(comparing && libraryCtl.byPoint);
  // Reader CA6: side by side (off: no `sideBySide` in the contract, nothing renders and no key does anything new).
  const sbs = useSideBySide({
    enabled: Boolean(contract?.sideBySide?.enabled) && Boolean(render) && !offline && !working,
    main: render ? { sourceId: render.sourceId, sourceTitle: sourceTitle ?? "", extractionId: render.extractionId, sectionId: currentGuideSection?.id ?? null } : null,
    // Follow along moves the main pane once, with no animation (K14): the jump,
    // then the passage put at the top at once (the PDF surface places its page itself).
    jumpMain: (spanId: string) => {
      jumpToSpan(spanId, "start");
      if (pdfSurfaceActive) return;
      const node = bodyRef.current?.querySelector(`[data-span-id="${spanId}"]`);
      if (node instanceof HTMLElement) node.scrollIntoView?.({ behavior: "auto", block: "start" });
    },
    pushCrumb: pushSideBySide,
    replaceCrumb: replaceSideBySide,
    dropCrumb: dropDetour,
    currentEntry: returnStack.entries[returnStack.cursor] ?? null,
    visitPayload,
    onError,
  });
  // The second pane shows while side by side is open in a wide window; a
  // comparison the learner starts takes the right side meanwhile (both are
  // the comparing posture), and side by side comes back when it closes.
  const sbsPanes = sbs.panes && !comparing;
  const sbsPanesRef = useRef(false);
  sbsPanesRef.current = sbsPanes;
  // What the learner sees of side by side now (a comparison hides it): Esc,
  // F6 and Ctrl+Shift+L act only on what is shown, so Esc in a comparison
  // closes the comparison and side by side comes back.
  const sbsShownRef = useRef(false);
  sbsShownRef.current = sbsPanes || (sbs.sheet && !comparing);
  const sbsRef = useRef(sbs);
  sbsRef.current = sbs;
  // Esc never closes the second pane while it is clearing something of the main pane's (a selection, a menu).
  const sbsEscBusyRef = useRef(false);
  sbsEscBusyRef.current = Boolean(selection) || Boolean(tagMenu);
  const sbsPaneRef = useRef<HTMLDivElement | null>(null);
  // Reader CA6b: the second pane's own context -- its selection and intent
  // box, capture target, active reading, figures and margin cues
  // (screens/reader/useSidePane). Its intents run through the same router as
  // the main pane's (runIntentIn, below), with this pane's context.
  const runSideIntentRef = useRef<(action: ReaderIntentActionDto, text: string, how: IntentRunHow) => Promise<IntentRunHandle | null> | void>(() => undefined);
  const cancelSideIntentRunRef = useRef<(cancel: IntentCancel) => void>(() => undefined);
  const sbsSection = sbs.section && sbs.target && sbs.section.sectionId === sbs.target.sectionId ? sbs.section : null;
  // Reader CA6b (Codex re-review F7, F8): what needs the open book -- the
  // working posture of a check or a work through -- takes the second pane's
  // book to the main pane first, at the passage, as a source detour from side
  // by side's crumb (openLibraryHit). The crumb stays one step back, so Alt+←
  // (or the crumb) reopens side by side; the shell keeps that way back across
  // its practice and feedback screens (besideTrail). Once that book is the
  // open one, the handoff runs (the effect below): the check goes to the shell
  // with that book's card, or the work through opens on its selection.
  // Fix round 4 (the second book's identity audit): the same handoff takes
  // that book to the main pane for everything else begun on it that needs
  // the open book -- "work through this" on an exercise imported from it
  // (item), and a tutor offer on an answer about it ("try the next step",
  // "show me") when the second pane does not show that passage -- so nothing
  // begun on the second book is opened or kept under the main one.
  type BesideRun =
    | { kind: "check"; request: CueCheckMeRequest }
    | { kind: "work"; stemMd: string; spanIds: string[]; importRequest: Omit<ReaderImportExerciseInput, "renderViewId" | "clientIdempotencyKey"> }
    | { kind: "item"; practiceItemId: string; stemMd: string; spanIds: string[] }
    | { kind: "next_step"; spanId: string }
    | { kind: "show_me"; goal: string; spanId: string; origin: "tutor" | "show_me"; offerRef: string | null; lineKey: string | null };
  // Fix round 5: the handoff carries the book's identity (the passage's own
  // source, revision and reading), never the main pane's.
  const [besideHandoff, setBesideHandoff] = useState<{ id: number; book: SourceIdentity; run: BesideRun } | null>(null);
  const besideSeq = useRef(0);
  // What runs once the book is open (set below, where the Reader's own
  // controllers are), and what a handoff whose book did not open settles.
  const besideRunRef = useRef<(run: BesideRun) => void>(() => undefined);
  const besideDroppedRef = useRef<(run: BesideRun) => void>(() => undefined);
  const openBesideRef = useRef<(hit: { sourceId: string; extractionId: string; spanId: string }) => Promise<OpenOutcome>>(
    () => Promise.resolve("not_opened"));
  // Final verify F8: the crumb keeps side by side as it is at the handoff --
  // the second pane's section now (moved by hand or by follow along since it
  // opened) at the handoff's passage, and the main pane's passage now -- so
  // the way back, here or after the shell's practice and feedback screens
  // (besideTrail is this stack), reopens that pair, not the one first opened.
  const snapshotBesideRef = useRef<(spanId: string) => void>(() => undefined);
  snapshotBesideRef.current = (spanId: string) => {
    const shown = sbsRef.current.target;
    if (!shown || !sbsRef.current.panes) return;
    snapshotSideBySide(crumbLabel(shown), { ...shown, spanId });
  };
  const takeBesideBook = useCallback((book: SourceIdentity, spanId: string, run: BesideRun) => {
    snapshotBesideRef.current(spanId);
    const id = ++besideSeq.current;
    setBesideHandoff({ id, book, run });
    void openBesideRef.current({ sourceId: book.sourceId, extractionId: book.extractionId, spanId }).then((outcome) => {
      if (outcome !== "opened") {
        setBesideHandoff((current) => (current?.id === id ? null : current));
        besideDroppedRef.current(run);
      }
    });
  }, []);
  // "check me" on the second pane's marks: only while the pane still shows
  // the reading it was asked on; its book comes to the main pane at the
  // mark's passage, and the shell opens the check there (book hidden).
  const sideExtractionRef = useRef<string | null>(null);
  const checkMeFromSideCue = useCallback((request: CueCheckMeRequest, origin: CueRequestOrigin) => {
    if (!onCheckMe || sideExtractionRef.current !== origin.extractionId) return;
    if (!library?.some((entry) => entry.sourceId === origin.sourceId)) return;
    takeBesideBook(origin, request.spanId, { kind: "check", request });
  }, [onCheckMe, library, takeBesideBook]);
  const side = useSidePane({
    shown: sbsPanes,
    section: sbsSection,
    // Final verify F11, F12: the second pane's book while side by side is
    // open (a section loading or a comparison only pauses its discovery).
    openBook: sbs.target?.extractionId ?? null,
    intentContract,
    muted,
    notes: Boolean(sbsSection && library?.find((card) => card.sourceId === sbsSection.sourceId)?.acquisitionKind === "textfile"),
    hostRef: sbsPaneRef,
    onRun: (action, text, how) => runSideIntentRef.current(action, text, how),
    onCancelRun: (cancel) => cancelSideIntentRunRef.current(cancel),
    onSelectedHere: noteIntentCleared,
    activeReadingOn,
    figuresContract: contract?.figures ?? null,
    densityKey: cueCtl.cues ? `${cueCtl.cues.density}:${cueCtl.cues.sourceOff ? 1 : 0}` : null,
    reloadMainPlan: reloadGuidePlan,
    visitPayload,
    onError,
    offline,
    foldBlocks: contract?.activeReading?.foldBlocks ?? 3,
    canWorkThrough: wbCtl.enabled,
    ...(onCheckMe ? { onCheckMe: checkMeFromSideCue } : {}),
  });
  sideExtractionRef.current = side.extractionId;
  // The second book is the open one now: its handoff runs, once.
  // Each handoff runs at most once (fix round 4): clearing it is a state
  // update, which a render already under way (another update of a higher
  // priority) may not see yet, so the effect can run again before it lands.
  const besideRanRef = useRef(0);
  useEffect(() => {
    const handoff = besideHandoff;
    if (!handoff || !render || offline || render.sourceId !== handoff.book.sourceId) return;
    if (besideRanRef.current === handoff.id) return;
    besideRanRef.current = handoff.id;
    setBesideHandoff(null);
    // Everything needs the reading its passages were selected (or asked, or
    // marked) on. Opening the book may have resolved another reading (a newer
    // extraction): then nothing runs, and the learner is told (fix round 5,
    // verify finding 2: a check no longer dispatches before this guard).
    if (render.extractionId !== handoff.book.extractionId) {
      besideDroppedRef.current(handoff.run);
      onError(SPAN_MISMATCH_COPY);
      return;
    }
    if (handoff.run.kind === "check") {
      const card = openCardRef.current;
      if (!card || !onCheckMe || card.sourceId !== handoff.book.sourceId) return;
      const trail = besideTrail(returnStackRef.current);
      onCheckMe({ ...handoff.run.request, reading: handoff.book, card, ...(trail ? { besideTrail: trail } : {}) });
      return;
    }
    if (handoff.run.kind !== "work") {
      besideRunRef.current(handoff.run);
      return;
    }
    if (!wbCtl.enabled) return;
    const work = handoff.run;
    void wbCtl.openSelection({
      stemMd: work.stemMd, spanIds: work.spanIds,
      importRequest: { ...work.importRequest, renderViewId: render.renderViewId, clientIdempotencyKey: newKey() },
    });
  }, [besideHandoff, render, offline, onCheckMe, wbCtl, returnStackRef, onError]);
  // Selecting in the main pane: the second pane's box lets go of its keys (one box answers keys at a time).
  const { releaseKeys: releaseSideKeys } = side;
  // A new composer (the second pane's, or back to the open book's): a failed
  // Ask is not its request, so ↵ there asks it afresh (Codex re-review F10).
  // It is a new composer generation at once, before anything is asked from
  // it, so a request still pending from the old one cannot leave its retry
  // here when it fails later (final verify F10), nor take this composer's
  // thread and draft when it lands (fix round 4, finding 4).
  const openComposer = useCallback((anchor: AskAnchor | null) => {
    forgetFailedAsk();
    setAskComposerAnchor(anchor);
  }, [forgetFailedAsk]);
  useEffect(() => {
    if (!selection) return;
    if (sbsPanesRef.current) releaseSideKeys();
    if (askComposerAnchorRef.current) openComposer(null);
  }, [selection, releaseSideKeys, openComposer]);
  // The composer the second pane opened goes back to the open book once that pane closes or its selection goes.
  useEffect(() => {
    if (!side.selection && askComposerAnchorRef.current) openComposer(null);
  }, [side.selection, openComposer]);
  const [sbsRailOverlay, setSbsRailOverlay] = useState(false);
  useEffect(() => {
    if (!sbsPanes) setSbsRailOverlay(false);
  }, [sbsPanes]);
  const [sbsSplit, setSbsSplit] = useState(readSplit);
  const sbsRowRef = useRef<HTMLDivElement | null>(null);
  const startSbsResize = (event: ReactPointerEvent<HTMLDivElement>) => {
    const row = sbsRowRef.current;
    if (!row) return;
    event.preventDefault();
    const rect = row.getBoundingClientRect();
    const move = (moved: PointerEvent) => {
      if (rect.width > 0) setSbsSplit(clampSplit((moved.clientX - rect.left) / rect.width));
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      setSbsSplit((value) => {
        writeSplit(value);
        return value;
      });
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  // The main pane leads once the learner's hand is on it (scroll, click, select).
  const touchMain = () => {
    if (sbsRef.current.panes) sbsRef.current.touch("main");
  };
  // Side by side's keys (§6.4): Ctrl+\ opens the first correspondent of the
  // section in view (or closes the second pane), Ctrl+Shift+L turns follow
  // along on or off, F6 moves focus between the panes, Esc in a pane closes
  // the second one. Outside text fields; nothing while off.
  useEffect(() => {
    if (!sbs.enabled) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select"))) return;
      const ctl = sbsRef.current;
      const open = ctl.panes || ctl.sheet;
      const shown = sbsShownRef.current;
      const mod = event.ctrlKey || event.metaKey;
      if (mod && !event.altKey && !event.shiftKey && event.key === "\\") {
        event.preventDefault();
        if (open) ctl.close();
        else void ctl.openFirst();
      } else if (mod && event.shiftKey && !event.altKey && event.key.toLowerCase() === "l" && ctl.panes && shown) {
        event.preventDefault();
        ctl.toggleFollow();
      } else if (event.key === "F6" && !mod && !event.altKey && ctl.panes && shown) {
        event.preventDefault();
        const side = sbsPaneRef.current;
        const inSide = target instanceof Element && Boolean(target.closest("[data-side-by-side-pane]"));
        if (inSide) bodyRef.current?.focus({ preventScroll: true });
        else side?.focus({ preventScroll: true });
      } else if (event.key === "Escape" && !mod && !event.altKey && shown && !event.defaultPrevented && !sbsEscBusyRef.current) {
        // Esc closes the second pane when it is aimed at either pane (never a
        // field, a menu or the rail's own Esc).
        const inMain = target instanceof Node && Boolean(bodyRef.current?.contains(target));
        if (target === document.body || inMain) {
          event.preventDefault();
          ctl.close();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sbs.enabled]);
  const askLibraryHere = useCallback((query: string, entry: LibraryAskEntry, spanIds: string[], box = false,
    anchor?: SourceIdentity) => {
    if (!render || offline) return;
    setLibraryCompose(null);
    // Reader CA6b: a palette verb in side by side's second pane is anchored on
    // that pane's reading; the ask keeps that book too (fix round 4), for its
    // comparisons and its practice picks.
    const identity = anchor ?? identityOf(render);
    const request = { query, entry, extractionId: identity.extractionId, spanIds, identity };
    // CA3: the ask box (Ctrl+Shift+F) reads named books first; a palette verb asks as before.
    if (box) void libraryCtl.askBox(request);
    else libraryCtl.ask(request);
  }, [render, offline, libraryCtl]);
  const closeLibrary = useCallback(() => {
    setLibraryCompose(null);
    libraryCtl.close();
  }, [libraryCtl]);
  // Ctrl+Shift+F: ask your library about the selection, else the passage in view.
  useEffect(() => {
    if (!libraryCtl.enabled || !render || offline || working) return;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if (!(event.ctrlKey || event.metaKey) || !event.shiftKey || event.key.toLowerCase() !== "f") return;
      event.preventDefault();
      libraryCtl.close();
      setLibraryCompose(selection ? (selection.editedText ?? selection.quote).slice(0, 400) : "");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [libraryCtl, render, offline, working, selection]);

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
    // exposes the annotation actions. RW1b: with the intent box, selecting
    // never changes the rail tab (UX §3.2, G57); the box appears instead.
    if (intentContract) noteIntentSelection();
    else setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
  }, [collectSelectionNodes, noteSelection, intentContract, noteIntentSelection]);

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
    if (intentContract) noteIntentSelection();
    else setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
  }, [resolveDomBoxes, noteSelection, intentContract, noteIntentSelection]);
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
      if (screenLeavesKey(event, { ownChords: true })) return;
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
  // A node with offsets (the original PDF's selection model, or the
  // extracted text when its quote is found once) is drawn on its words at once.
  const optimisticSegments = useCallback(
    (nodes: string | Array<string | { spanId: string; start?: number; end?: number }>): AnnotationSegment[] => {
      const list = Array.isArray(nodes) ? nodes : [nodes];
      return list.map((node) => {
        const spanId = typeof node === "string" ? node : node.spanId;
        const geometry = pdfView?.blocks.find((b) => b.spanId === spanId);
        const offsets = typeof node === "string" || typeof node.start !== "number" || typeof node.end !== "number"
          ? {}
          : { start: node.start, end: node.end };
        return { spanId, page: geometry?.page ?? null, bbox: geometry?.bbox ?? null, ...offsets };
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
      const optimisticIds = quotedNodes ?? [target.spanId];
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
          rawSelection: { extractionId: render.extractionId, nodes },
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
      if (screenLeavesKey(event, { ownChords: true })) return;
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
    noteIntentCleared();
  }, [noteIntentCleared]);
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


  // Reader CA5's `x`: only while its line is there to open.
  const alsoKeyRef = useRef<() => boolean>(() => false);
  // Not while comparing either (Codex review F5): the comparing posture hides the Guide's rail.
  alsoKeyRef.current = () => alsoOn && alsoAvailable && !alsoHidden && !working && !comparing && !intentBox.open && !side.box.open;
  // Reader-wide keys (UX §3.5), outside text fields: [ and ] move between rail
  // tabs; \ collapses or expands the rail (remembered on this device); x opens
  // "also in your books" (CA5).
  useEffect(() => {
    if (!inquiry || !render) return;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select"))) return;
      const tabs: ReaderRailTab[] = ["guide", "ask", "notes"];
      if (event.key === "[" || event.key === "]") {
        event.preventDefault();
        setRailTab((tab) => tabs[(tabs.indexOf(tab) + (event.key === "]" ? 1 : tabs.length - 1)) % tabs.length]);
      } else if (event.key === "\\") {
        event.preventDefault();
        // Reader CA6: in side by side the rail stays folded to its gutter; \\ opens it as an overlay.
        if (sbsPanesRef.current) setSbsRailOverlay((open) => !open);
        else setRailCollapsed((collapsed) => !collapsed);
      } else if ((event.key === "x" || event.key === "X") && alsoKeyRef.current()) {
        // Reader CA5: open "also in your books" at its first line (off while the
        // intent box shows, in the working posture, or with no line to open).
        event.preventDefault();
        // In side by side (CA6) the rail is an overlay over the gutter: open that.
        if (sbsPanesRef.current) setSbsRailOverlay(true);
        else setRailCollapsed(false);
        setRailTab("guide");
        setAlsoExpandToken((token) => token + 1);
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

  // UX Phase 2 (Codex review F5): the palette's ask opens this Ask, as the
  // learner asked (D41), with its box focused; it never sends a question.
  // Fix round 3 (whole-stage verify 20261021-130232-Uk06Al item 4): from any
  // posture. Comparing hides the rail, so the comparison closes first. The
  // working posture hides it too, and leaving it is the learner's call (Leave
  // for now saves the steps, and can be refused), so a visible line in the
  // workbench says how, and Ask opens once the learner has left.
  const askRequestSeen = useRef(askRequest);
  const [askWaitsForWork, setAskWaitsForWork] = useState(false);
  const revealAskRef = useRef<() => void>(() => undefined);
  revealAskRef.current = () => {
    if (libraryCtl.open || libraryCompose !== null) closeLibrary();
    setRailCollapsed(false);
    setRailTab("ask");
    window.setTimeout(() => askComposerRef.current?.focus({ preventScroll: true }), 0);
  };
  useEffect(() => {
    if (askRequest === undefined || askRequest === askRequestSeen.current) return;
    askRequestSeen.current = askRequest;
    if (working) setAskWaitsForWork(true);
    else revealAskRef.current();
    // `working` is read as it is when the request arrives, not followed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [askRequest]);
  useEffect(() => {
    if (working || !askWaitsForWork) return;
    setAskWaitsForWork(false);
    revealAskRef.current();
  }, [working, askWaitsForWork]);
  // Reader CA3, Codex review F1: the selection verb while a problem is open.
  // The comparing posture is hidden while working, so nothing runs (nothing is
  // paid for) then; a line in the workbench says so, and the comparison opens
  // beside the book once the learner leaves (the same book only).
  const [compareWaitsForWork, setCompareWaitsForWork] = useState<CompareRequest | null>(null);
  const startCompareRef = useRef<(request: CompareRequest) => void>(() => undefined);
  startCompareRef.current = (request) => {
    // Reader CA6b: or the second pane's reading, anchored there (side by side shown).
    const sideAnchor = Boolean(side.extractionId) && side.extractionId === request.extractionId;
    if (!render || offline || (render.extractionId !== request.extractionId && !sideAnchor)) return;
    setLibraryCompose(null);
    libraryCtl.compareFrom(request);
  };
  useEffect(() => {
    if (working || !compareWaitsForWork) return;
    const request = compareWaitsForWork;
    setCompareWaitsForWork(null);
    startCompareRef.current(request);
  }, [working, compareWaitsForWork]);

  // Reader CA6b: a capture on side by side's second pane, on its own book --
  // a preset (reader.invoke_preset) or a highlight or note (reader.capture) --
  // the same calls as the main pane's, with that pane's source, revision,
  // reading and selection. The main pane's margin and capture state are not
  // touched; the second pane re-reads its own marks.
  const sideMarksChanged = side.marksChanged;
  const captureIn = useCallback(async (target: PaneCaptureTarget, what: { preset: string } | { highlight: true }, learnerText: string,
                                       meta?: Record<string, unknown>): Promise<string | null> => {
    if (offline) return null;
    setBusy(true);
    try {
      const common = {
        sourceId: target.sourceId, revisionId: target.revisionId, extractionId: target.extractionId,
        clientIdempotencyKey: newKey(), renderViewId: target.renderViewId,
        rawSelection: { extractionId: target.extractionId, nodes: target.nodes }, learnerText,
      };
      const receipt: ReaderPresetReceiptDto = "preset" in what
        ? await api.readerInvokePreset({ preset: what.preset, ...common, subjectId: target.spanId })
        : await api.readerCapture({ ...common, action: "highlight" });
      logReaderAction("action_invoked", {
        ...visitPayload(), action_kind: "preset" in what ? `preset:${what.preset}` : "highlight",
        target_source_id: target.sourceId, target_extraction_id: target.extractionId, ...(meta ?? {}),
      });
      if ("preset" in what) {
        if (receipt.arc) setArc(receipt.arc);
        // The demand-paged request starts as the main pane's do (a drain failure is a delayed job, not a failed capture).
        try {
          const drained = await api.readerDrainOutbox();
          if (drained.failed.length > 0) {
            onError(`${drained.failed.length} saved Reader request${drained.failed.length === 1 ? " is" : "s are"} still waiting to start.`);
          }
        } catch (error) {
          onError(`Saved locally, but background processing has not started yet: ${errorMessage(error)}`);
        }
        void refreshRequests();
      }
      sideMarksChanged();
      return receipt.annotationId ?? null;
    } catch (error) {
      onError(errorMessage(error));
      return null;
    } finally {
      setBusy(false);
    }
  }, [offline, onError, refreshRequests, sideMarksChanged]);

  // Palette (§5.2): a preset runs the local-first capture transaction. Commit presets
  // also create a commitment; synthesis is enqueued off the hot path (§5.3, §6).
  const invokePreset = useCallback(
    // RW1b: the intent box passes its own words as the annotation's learner
    // text, and names the intention and entry in the funnel event.
    // Reader CA6b: `target` is side by side's second pane (its book, revision,
    // reading and selection); absent, the main pane's, exactly as before.
    async (preset: string, learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null> => {
      if (target) return captureIn(target, { preset }, learnerTextOverride ?? "", meta);
      if (!render || !selection) return null;
      const note_ = learnerTextOverride ?? note;
      const nodes = selectionNodes(selection);
      const editedText = selection.editedText?.trim();
      if (offline) {
        setAnnotations((a) => [
          { annotationId: null, quote: selection.quote, status: "exact", learnerText: note_, kind: preset, segments: optimisticSegments(nodes) },
          ...a,
        ]);
        setSelectionActions((actions) => [...new Set([...actions, preset])]);
        setNote("");
        return null;
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
          rawSelection: editedText ? { extractionId: render.extractionId, nodes, editedText } : { extractionId: render.extractionId, nodes },
          learnerText: note_,
          subjectId: selection.spanId,
        });
        setAnnotations((a) => [
          { annotationId: receipt.annotationId, quote: selection.quote, status: receipt.anchorStatus, learnerText: note_, kind: preset, segments: optimisticSegments(nodes) },
          ...a,
        ]);
        // §10.2 / Journey 2: a commit shows a durable, immediately visible arc.
        if (receipt.arc) setArc(receipt.arc);
        setSelectionActions((actions) => [...new Set([...actions, preset])]);
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: `preset:${preset}`, ...(meta ?? {}) });
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
        return receipt.annotationId ?? null;
      } catch (error) {
        onError(errorMessage(error));
        return null;
      } finally {
        setBusy(false);
      }
    },
    [render, selection, note, offline, onError, refreshAnnotations, refreshRequests, optimisticSegments, captureIn],
  );

  // A plain highlight is a slice-1 CAPTURE action, not one of the nine presets —
  // reader.invoke_preset rejects "highlight" deterministically. Route it through
  // reader.capture so the annotation lands with no commitment and no synthesis.
  const captureHighlight = useCallback(async (learnerTextOverride?: string, meta?: Record<string, unknown>, target?: PaneCaptureTarget): Promise<string | null> => {
    // Reader CA6b: the second pane's selection, to its own book.
    if (target) return captureIn(target, { highlight: true }, learnerTextOverride ?? "", meta);
    if (!render || !selection) return null;
    const note_ = learnerTextOverride ?? note;
    const nodes = selectionNodes(selection);
    if (offline) {
      setAnnotations((a) => [
        { annotationId: null, quote: selection.quote, status: "exact", learnerText: note_, kind: "highlight", segments: optimisticSegments(nodes) },
        ...a,
      ]);
      setSelectionActions((actions) => [...new Set([...actions, "highlight"])]);
      setNote("");
      return null;
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
        rawSelection: { extractionId: render.extractionId, nodes },
        learnerText: note_,
      });
      setAnnotations((a) => [
        { annotationId: receipt.annotationId, quote: selection.quote, status: receipt.anchorStatus ?? "exact", learnerText: note_, kind: "highlight", segments: optimisticSegments(nodes) },
        ...a,
      ]);
      logReaderAction("action_invoked", { ...visitPayload(), action_kind: "highlight", ...(meta ?? {}) });
      setSelectionActions((actions) => [...new Set([...actions, "highlight"])]);
      setNote("");
      void refreshAnnotations();
      return receipt.annotationId ?? null;
    } catch (error) {
      onError(errorMessage(error));
      return null;
    } finally {
      setBusy(false);
    }
  }, [render, selection, note, offline, onError, refreshAnnotations, optimisticSegments, captureIn]);

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
  // Reader CA6b: `target` is side by side's second pane (the exercise is that
  // book's, verbatim); absent, the main pane's selection, exactly as before.
  const importExercise = useCallback(async (target?: PaneCaptureTarget): Promise<string | null> => {
    if (!render || (!selection && !target) || offline) return null;
    const nodes = target ? target.nodes : selectionNodes(selection!);
    const editedText = target ? undefined : selection!.editedText?.trim();
    setBusy(true);
    try {
      const receipt = await api.readerImportExercise(target ? {
        extractionId: target.extractionId,
        sourceId: target.sourceId,
        revisionId: target.revisionId,
        renderViewId: target.renderViewId,
        rawSelection: { extractionId: target.extractionId, nodes },
        clientIdempotencyKey: newKey(),
      } : {
        extractionId: render.extractionId,
        sourceId: render.sourceId,
        revisionId: render.revisionId,
        renderViewId: render.renderViewId,
        // Reader CA1 (§12.4): a region selection keeps its sub-box, so the
        // problem as printed is the learner's crop.
        rawSelection: { extractionId: render.extractionId, ...(editedText ? { nodes, editedText } : { nodes }), ...(selection!.region ? { region: selection!.region } : {}) },
        clientIdempotencyKey: newKey(),
      });
      setExerciseImport({
        batchId: receipt.batchId,
        status: receipt.status || "queued",
        quote: target ? target.quote : editedText ? editedText.replace(/\s+/g, " ") : selection!.quote,
        result: null,
        error: null,
        spanIds: [...new Set(nodes.map((node) => node.spanId))],
        // Fix round 4 (verify finding 1): the book the exercise is from, on
        // the import itself, so its "work through this" opens there.
        identity: target
          ? { sourceId: target.sourceId, revisionId: target.revisionId, extractionId: target.extractionId }
          : { sourceId: render.sourceId, revisionId: render.revisionId, extractionId: render.extractionId },
      });
      if (!target) setSelectionActions((prev) => [...prev, "exercise_import"]);
      logReaderAction("action_invoked", {
        ...visitPayload(), action_kind: "import_exercise",
        ...(target ? { target_source_id: target.sourceId, target_extraction_id: target.extractionId } : {}),
      });
      importJobRef.current = { jobId: receipt.batchId, startedAt: Date.now(), activity: learnerActivitySnapshot() };
      logReaderActivity({ kind: "reader_job_queued", payload: { ...visitPayload(), job_id: receipt.batchId, job_kind: "import_exercise" } });
      return receipt.batchId ?? null;
    } catch (error) {
      onError(errorMessage(error));
      return null;
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
          spanKeys: passageKeys(render.extractionId, [activeSpan]),
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
              else dismissInquiryCheck(root.id);
            }}
            onEscalate={() => void escalateInquiryCheck(root.id)}
            onRetry={() => void startQuickCheck(root.id, "rail")}
            onShowPassage={peekPassage}
          />
        ) : null}
      </div>
    ) : null;
  }, [reconnect, muted, busy, answerReconnect, passageCheckOffered, inquiryChecks, inquiryCheckAction, escalateInquiryCheck, startQuickCheck, cancelQuickCheck, dismissInquiryCheck, peekPassage]);

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

  // RW4a: "open" a library hit: this book jumps to it (a peek crumb); another
  // book opens in the left pane as a detour (Alt+← comes back here). Defined
  // before every early return: the library page (no book open) uses it too,
  // through the exercise cards' actions (RW4b, Codex review F1).
  // It resolves to how the open ended (an offer's press settles on it, F9).
  const openLibraryHit = (hit: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">): Promise<OpenOutcome> => {
    if (render && hit.sourceId === render.sourceId) {
      peekPassage(hit.spanId);
      return Promise.resolve("opened");
    }
    const card = (library ?? []).find((candidate) => candidate.sourceId === hit.sourceId);
    if (!card || opening !== null) return Promise.resolve("not_opened");
    if (render && !offline) {
      const spanId = readingSpan ?? activeSpan;
      rememberLeftSource({
        id: newActivityId(), kind: "origin", sourceId: render.sourceId, sourceTitle,
        extractionId: render.extractionId, spanId, selection, railTab, exchangeId: null,
        label: sourceTitle ?? "where I was", openedAt: Date.now(),
      });
    }
    return openSource(card, hit.spanId, { via: "search", jumpReading: hit.extractionId });
  };
  openBesideRef.current = openLibraryHit;
  // RW5d P4a (figures follow the section): a figure the learner kept in another
  // book's corresponding section, opened from "also in your books", shows here
  // under the passage in view (when it is in this section, else the section's
  // first passage), expanded, its home named. Its own book's listing is read
  // now (protection and switches checked there); nothing is copied.
  const openFollowedFigure = (figure: CorrespondentFigureDto, hit: CorrespondentSectionDto) => {
    if (!render || offline || !currentGuideSection) return;
    const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId;
    void figuresCtl.follow(figure, { sourceTitle: hit.sourceTitle, sectionTitle: hit.title }, here).then((shown) => {
      if (!shown) {
        onError(ALSO_COPY.figureGone);
        return;
      }
      logReaderAction("figure_opened", { figure_id: figure.figureId, extraction_id: figure.extractionId });
      if (here !== readingSpan) peekPassage(here);
    });
  };
  // Reader CA5a: compare a section found in another book with the one in view,
  // through the library compare path (an ask anchored on this section, its
  // title the question, both passages pinned) while CA3 is off; with CA3 on,
  // through CA3's one request (CA3 landing). The passage in view stands for
  // this section when it is in it, else the section's first passage.
  const compareFoundSection = (hit: CorrespondentSectionDto) => {
    if (!render || offline || !currentGuideSection || !hit.jump.spanId) return;
    const here = readingSpan && currentGuideSection.spanIds.includes(readingSpan) ? readingSpan : currentGuideSection.startSpanId;
    setLibraryCompose(null);
    if (libraryCtl.scopeOn) {
      // CA3 on: the same one request as every other door (the selection door):
      // anchored on the passage of this section, the section's title the
      // question, narrowed to the hit's book (pins belong to a library answer,
      // so the hit's book finds its passage by discovery). A retry reruns this
      // request as it was (anchor and book kept).
      libraryCtl.compareFrom({
        door: "selection", question: currentGuideSection.label, extractionId: render.extractionId,
        anchorSpanIds: [here], sourceIds: [hit.sourceId], openSourceId: render.sourceId, identity: identityOf(render),
      });
      return;
    }
    void libraryCtl.compareWith(
      { query: currentGuideSection.label, entry: "where_else_explained", extractionId: render.extractionId, spanIds: [here],
        identity: identityOf(render) },
      [`${render.extractionId}:${here}`, `${hit.jump.extractionId}:${hit.jump.spanId}`],
    );
  };
  // Reader CA5: "hide for this book" / "hide everywhere" on the line, kept in
  // the vault's config (Settings brings it back). The cached contract follows
  // at once, and settles on the sidecar's answer (or goes back on a failure).
  const hideAlsoInBooks = (scope: "book" | "everywhere") => {
    if (!render || !contract?.correspondence) return;
    const before = alsoPrefs ?? {
      everywhere: Boolean(contract.correspondence.hiddenEverywhere), sources: contract.correspondence.hiddenSources ?? [],
    };
    setAlsoPrefs(scope === "book"
      ? { everywhere: before.everywhere, sources: [...new Set([...before.sources, render.sourceId])] }
      : { everywhere: true, sources: before.sources });
    setAlsoPeek(null);
    const base = contract;
    Promise.resolve()
      .then(() => api.readerSetCorrespondencePreferences(scope === "book" ? { sourceId: render.sourceId, hideSource: true } : { hideEverywhere: true }))
      .then((prefs) => {
        // Every Reader reads it from the contract from now on.
        setQueryData(["reader_prompt_contract"], {
          ...base, correspondence: { ...base.correspondence!, hiddenEverywhere: prefs.hideEverywhere,
            hiddenSources: prefs.hiddenSources.map((entry) => entry.sourceId) },
        }, [TAG.reader, TAG.settings]);
      })
      .catch((error) => {
        setAlsoPrefs(before);
        onError(errorMessage(error));
      });
  };
  // RW5b: an offered figure's press (see offeredFigure above). It resolves to
  // how the press ended: built, or why nothing was (fix round 2, F9).
  const makeExplorable = (target: Pick<LibraryHitDto, "sourceId" | "extractionId" | "spanId">, origin: "library" | "tutor", offerRef: string): Promise<ExplorableOutcome> => {
    if (!figureOffersOn) return Promise.resolve("figures_off");
    // A passage of another reading of the book open now: opening it again
    // opens this reading, where the offered block is not (Codex review F6).
    if (render && target.sourceId === render.sourceId && target.extractionId !== render.extractionId) return Promise.resolve("another_reading");
    // An earlier press still waiting for its book is replaced.
    if (waitingOfferRef.current) lapseOffered(waitingOfferRef.current, "replaced");
    let settle: (outcome: ExplorableOutcome) => void = () => undefined;
    const settled = new Promise<ExplorableOutcome>((resolve) => { settle = resolve; });
    const press: OfferedPress = {
      fromExtractionId: render?.extractionId ?? null, sourceId: target.sourceId, extractionId: target.extractionId,
      spanId: target.spanId, origin, offerRef, settle,
    };
    waitingOfferRef.current = press;
    setOfferedFigure(press);
    if (!render || target.extractionId !== render.extractionId) {
      // The detour: a book that did not open (or is still being prepared)
      // lapses the press at once; one that opened builds in the effect above.
      void openLibraryHit(target).then((opened) => {
        if (opened !== "opened") lapseOffered(press, opened);
      });
    }
    return settled;
  };
  // RW2c review F1: a passage the workbench names (a worked example, a picked
  // passage) may be in another book. In this book it is a peek, as before;
  // in another it opens there, as a library hit does (a detour: Alt+← comes
  // back, and the problem keeps its ✎ resume mark).
  const peekWorkbenchPassage = (spanId: string, target?: PassageTarget) => {
    if (target?.sourceId && render && target.sourceId !== render.sourceId) {
      openLibraryHit({ sourceId: target.sourceId, extractionId: target.extractionId ?? "", spanId });
      return;
    }
    peekPassage(spanId);
  };
  // RW4b: the candidate cards (spec §7.4). "Open in the book" is the same
  // detour as a library hit's "open"; "use this one" is a learner pick the
  // shell opens in the working posture, in the exercise's own source (opened
  // as a detour when another book is open, so Alt+← comes back).
  const exerciseSettings = libraryCtl.enabled ? contract?.libraryExercises ?? null : null;
  const exerciseCard = (sourceId: string | null) =>
    (sourceId ? (library ?? []).find((candidate) => candidate.sourceId === sourceId) : undefined)
    ?? (openCardRef.current && (!sourceId || openCardRef.current.sourceId === sourceId) ? openCardRef.current : undefined);
  const [openingExercise, setOpeningExercise] = useState<string | null>(null);
  const useExercise = (candidate: ExerciseCandidate) => {
    const card = exerciseCard(candidate.sourceId ?? render?.sourceId ?? null);
    if (!card || !onUseExercise) return;
    setOpeningExercise(candidate.key);
    window.setTimeout(() => setOpeningExercise((current) => (current === candidate.key ? null : current)), 1500);
    onUseExercise({ ...exerciseOpenRequest(candidate), sourceId: card.sourceId, card });
    if (!render || render.sourceId !== card.sourceId) {
      openLibraryHit({ sourceId: card.sourceId, extractionId: candidate.extractionId, spanId: candidate.spanIds[0] ?? "" });
    }
  };
  const openExerciseInBook = (candidate: ExerciseCandidate) => {
    const sourceId = candidate.sourceId ?? render?.sourceId ?? null;
    if (sourceId) openLibraryHit({ sourceId, extractionId: candidate.extractionId, spanId: candidate.spanIds[0] ?? "" });
  };
  const exerciseProps: LibraryExercisesProps | null = exerciseSettings
    ? {
        settings: exerciseSettings,
        // "Use this one" opens the workbench; without it, only the book is offered.
        onUse: wbCtl.enabled && onUseExercise ? useExercise : null,
        onOpenInBook: openExerciseInBook,
        opening: openingExercise,
      }
    : null;
  // ── A book still being prepared: its original, at once (UX Phase 1, §6.3) ──
  // On the library page no book is open: the pick is the same learner pick,
  // coming back to the answer's first passage (Codex review F10). With the
  // workbench on, the check opens beside that passage, so its book opens too
  // (a detour, as "open" is).
  const pickLibraryPagePractice = (item: ProposedItemDto, proposalId: string | null) => {
    const hit = libraryCtl.state?.ask.value?.hits[0];
    const card = hit ? (library ?? []).find((candidate) => candidate.sourceId === hit.sourceId) : undefined;
    if (!hit || !card || !onCheckMe) return;
    // The hit's own book and reading (its revision is not known here: the sidecar checks the reading).
    onCheckMe({ practiceItemId: item.practiceItemId, proposalId, spanId: hit.spanId, card,
      reading: { sourceId: card.sourceId, revisionId: null, extractionId: hit.extractionId } });
    if (algoConfig().workbench && opening === null) {
      void openSource(card, hit.spanId, { via: "search", jumpReading: hit.extractionId });
    }
  };
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
                    // RW4a: Shift+Enter asks your library (sources first); off, it is Enter.
                    if (e.key === "Enter" && e.shiftKey && libraryCtl.enabled && librarySearch.trim()) {
                      e.preventDefault();
                      // CA3: with compare from anywhere on, the ask box first reads named books.
                      void libraryCtl.askBox({ query: librarySearch.trim(), entry: "library_search", extractionId: null, spanIds: [], identity: null });
                      return;
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
              {libraryCtl.enabled ? <Faint style={{ fontSize: 10 }}>↵ search by meaning · ⇧↵ ask your library</Faint> : null}
              {libraryCtl.open ? (
                // RW4d: keep and reopen work on the library page too (Codex review F3);
                // curriculum C2: so do the notes' your-take band (C2 Codex review F10).
                <NotesContext.Provider value={notesCtl.context}>
                <CompareKeepContext.Provider value={keptCtl.context}>
                <Card style={{ padding: 0 }}>
                  <LibraryAnswer
                    ctl={libraryCtl}
                    onOpenHit={(hit) => {
                      const card = (library ?? []).find((candidate) => candidate.sourceId === hit.sourceId);
                      if (card && opening === null) void openSource(card, hit.spanId, { via: "search", jumpReading: hit.extractionId });
                    }}
                    onPracticePick={onCheckMe ? pickLibraryPagePractice : null}
                    onClose={libraryCtl.close}
                    exercises={exerciseProps}
                    onMakeExplorable={figureOffersOn ? (hit, offerRef) => makeExplorable(hit, "library", offerRef) : null}
                    onReword={libraryCtl.scopeOn ? (words) => { libraryCtl.close(); setLibrarySearch(words); } : null}
                  />
                </Card>
                </CompareKeepContext.Provider>
                </NotesContext.Provider>
              ) : null}
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
                          if (card && opening === null) {
                            const receiptId = searchResults.retrievalReceiptId;
                            if (receiptId) {
                              // Local contextual retrieval P1: the open is a relevance signal (never blocks the open).
                              void api.readerRetrievalOpen({ receiptId, extractionId: hit.extractionId, spanId: hit.spanId }).catch(() => undefined);
                            }
                            void openSource(card, hit.spanId, { via: "search", jumpReading: hit.extractionId });
                          }
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

  // ── RW2a: the working posture ──
  const wbActive = wbCtl.active;
  const wbStacked = working && wbCtl.narrow;
  // The source pane is covered whenever the session's book is not shown:
  // only a shown book counts, so an uncounted one is never in view (review F4).
  const wbBookHidden = Boolean(wbActive && !wbActive.session.sourceVisible);
  const wbSourceShown = !wbStacked || wbCtl.sheetOpen;
  const wbOpenSessions = wbCtl.enabled ? wbCtl.sessions.filter((entry) => entry.sessionId !== wbActive?.session.sessionId) : [];
  const wbResumeBySpan = new Map<string, (typeof wbOpenSessions)[number]>();
  for (const entry of wbOpenSessions) {
    const first = entry.spanIds[0];
    if (first && !wbResumeBySpan.has(first)) wbResumeBySpan.set(first, entry);
  }
  const wbLabel = (stem: string) => {
    const title = problemTitle(stem);
    return title === "this problem" ? clip(stem, 48) : title;
  };
  // RW7a: the reading path's "Try it" -- the exercise in the workbench through
  // the usual import of a selected problem, with the book open.
  const tryPathExercise = (exercise: ReadingPathExerciseDto) => {
    if (!render) return;
    void wbCtl.openSelection({
      stemMd: exercise.statement,
      spanIds: exercise.spanIds,
      importRequest: { ...exercise.importRequest, renderViewId: render.renderViewId, clientIdempotencyKey: newKey() },
    });
  };
  const workThroughSelection = () => {
    if (!render || !selection) return;
    const nodes = selectionNodes(selection);
    const editedText = selection.editedText?.trim();
    void wbCtl.openSelection({
      stemMd: editedText || selection.quote,
      spanIds: [...new Set(nodes.map((node) => node.spanId))],
      importRequest: {
        extractionId: render.extractionId,
        sourceId: render.sourceId,
        revisionId: render.revisionId,
        renderViewId: render.renderViewId,
        rawSelection: { extractionId: render.extractionId, ...(editedText ? { nodes, editedText } : { nodes }), ...(selection.region ? { region: selection.region } : {}) },
        clientIdempotencyKey: newKey(),
      },
    });
  };
  // RW1b: what the intent box runs -- each action through the palette's own
  // handler (the same RPC and payload, G3). The box's words are the question
  // (an ask) or the annotation's learner text (everything else).
  const foldBlocks = contract?.activeReading?.foldBlocks ?? 3;
  const localFold = (spanIds: string[]): string[] => {
    const positions = spanIds.map((spanId) => blocks.findIndex((block) => block.spanId === spanId)).filter((i) => i >= 0);
    if (!positions.length) return [];
    const last = Math.max(...positions);
    return blocks.slice(last + 1, last + 1 + foldBlocks).flatMap((block) => (block.spanId ? [block.spanId] : []));
  };
  // RW3b: a try-first cue opens the next-step question at its line (the same act as RW1c's button).
  tryFirstRef.current = (spanId: string) => void activeCtl.start("next_step", [spanId], localFold([spanId]));
  // Reader CA6b: one router for both panes. The pane context says what an
  // intent acts on -- the main pane's selection, book and reading, or side by
  // side's second pane's -- so a routed action makes the palette's own call
  // with that pane's source (the main pane's path is unchanged).
  const mainPane: IntentPane = {
    side: null,
    spanIds: selectionSpanIds,
    words: selection ? (selection.editedText ?? selection.quote) : "",
    active: activeCtl,
    fold: localFold,
    figures: figuresCtl,
    region: selection?.region ? { spanId: selection.region.spanId, bbox: selection.region.bbox } : null,
  };
  const sidePane: IntentPane | null = side.extractionId ? {
    side,
    spanIds: side.selection?.spanIds ?? [],
    words: side.selection?.quote ?? "",
    active: side.active,
    fold: (spanIds) => side.fold(spanIds, foldBlocks),
    figures: side.figures,
    region: null,
  } : null;
  // "how do my other books treat this?" and the funnel name the book beside.
  const sideMeta = (pane: IntentPane): Record<string, string> => (pane.side?.section
    ? { target_source_id: pane.side.section.sourceId, target_extraction_id: pane.side.section.extractionId } : {});
  const runIntentIn = (pane: IntentPane, action: ReaderIntentActionDto, text: string, how: IntentRunHow): Promise<IntentRunHandle | null> | void => {
    const meta = { intention: action.intention, entry: how.entry, ...sideMeta(pane) };
    const effect = action.effect;
    const sideSection = pane.side?.section ?? null;
    switch (effect.kind) {
      case "ask": {
        if (sideSection && pane.side) {
          // The second pane's Ask is about its own book and selection; the
          // answer lands in the Ask rail (side by side's overlay), labelled so.
          const anchor: AskAnchor = {
            about: {
              extractionId: sideSection.extractionId, sourceId: sideSection.sourceId, revisionId: sideSection.revisionId ?? null,
              label: `${sideSection.sourceTitle} · ${clip(sideSection.title, 48)}`,
            },
            spanId: pane.spanIds[0] ?? sideSection.jumpSpanId,
            selectionSpanIds: pane.spanIds,
            selectionQuote: pane.words.trim() || null,
          };
          setSbsRailOverlay(true);
          setRailTab("ask");
          if (text) {
            if (askComposerAnchorRef.current) openComposer(null);
            void submitAsk(text, null, { answerMode: "answerMode" in effect ? effect.answerMode : undefined, meta, anchor });
          } else {
            // An empty Enter: the composer, on the second pane's selection (no
            // model call), a new thread there: never a follow-up to the open
            // book's thread (Codex review F2).
            setParentExchange(null);
            openComposer(anchor);
            logReaderAction("action_invoked", { ...visitPayload(), action_kind: "ask_opened", ...meta });
            window.requestAnimationFrame(() => askComposerRef.current?.focus({ preventScroll: true }));
          }
          return;
        }
        // A routed Ask opens the Ask tab, because the learner asked (D41).
        setRailCollapsed(false);
        setRailTab("ask");
        if (text) {
          void submitAsk(text, null, { answerMode: "answerMode" in effect ? effect.answerMode : undefined, meta });
        } else {
          // An empty Enter asks with no model call: the composer, on the selection.
          logReaderAction("action_invoked", { ...visitPayload(), action_kind: "ask_opened", ...meta });
          window.requestAnimationFrame(() => askComposerRef.current?.focus({ preventScroll: true }));
        }
        return;
      }
      // A capture or an import resolves to what "change" may undo (F4).
      // In the second pane: its own book (the pane's capture target).
      case "preset":
        if (pane.side) {
          const target = pane.side.target;
          return target ? invokePreset(effect.preset, text, meta, target).then((annotationId) => ({ annotationId })) : undefined;
        }
        return invokePreset(effect.preset, text, meta).then((annotationId) => ({ annotationId }));
      case "highlight":
        if (pane.side) {
          const target = pane.side.target;
          return target ? captureHighlight(text, meta, target).then((annotationId) => ({ annotationId })) : undefined;
        }
        return captureHighlight(text, meta).then((annotationId) => ({ annotationId }));
      case "import_exercise":
        if (pane.side) {
          const target = pane.side.target;
          return target ? importExercise(target).then((importBatchId) => ({ importBatchId })) : undefined;
        }
        return importExercise().then((importBatchId) => ({ importBatchId }));
      case "work_through":
        if (sideSection && pane.side) {
          // Reader CA6b (Codex re-review F7): the working posture is the open
          // book's, so the second pane's book comes to the main pane at this
          // passage (side by side one step back), and the work opens there on
          // this selection, through the usual import.
          const target = pane.side.target;
          if (!target || !wbCtl.enabled) return;
          takeBesideBook({ sourceId: target.sourceId, revisionId: target.revisionId, extractionId: target.extractionId }, target.spanId, {
            kind: "work", stemMd: target.quote, spanIds: [...new Set(target.nodes.map((node) => node.spanId))],
            importRequest: {
              extractionId: target.extractionId, sourceId: target.sourceId, revisionId: target.revisionId,
              rawSelection: { extractionId: target.extractionId, nodes: target.nodes },
            },
          });
          return;
        }
        workThroughSelection();
        return;
      case "active_reading":
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: effect.style, ...meta });
        void pane.active.start(effect.style, pane.spanIds, pane.fold(pane.spanIds));
        return;
      case "another_way":
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: "another_way", ...meta });
        void pane.active.anotherWay(pane.words, pane.spanIds);
        return;
      case "library_ask":
        // RW4a: Orient's and Transfer's library asks, in the comparing posture
        // (the second pane's: anchored on its reading; side by side comes back when it closes).
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: effect.entry, ...meta });
        askLibraryHere(text || pane.words, effect.entry, pane.spanIds, false,
          sideSection ? sectionIdentity(sideSection) : undefined);
        return;
      case "compare":
        // CA3: Transfer's "how do my other books treat this?": a comparison
        // anchored on the selection, every other book, no pins (§4.1).
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: "compare_books", ...meta });
        if (!render || offline) return;
        if (sideSection) {
          // Reader CA6b: in the second pane, anchored there; the source is the other pane's book (§4.1).
          startCompareRef.current({
            door: "selection", question: text || pane.words, extractionId: sideSection.extractionId,
            anchorSpanIds: pane.spanIds, openSourceId: sideSection.sourceId, sourceIds: [render.sourceId],
            workbenchSessionId: null, identity: sectionIdentity(sideSection),
          });
          return;
        }
        {
          // The bound workbench session, when one is active, goes with the
          // request (the server derives its practice policy: Codex review F1).
          const bound = wbCtl.active?.session.practiceItemId ? wbCtl.active.session.sessionId : null;
          const request: CompareRequest = {
            door: "selection", question: text || (selection ? (selection.editedText ?? selection.quote) : ""),
            extractionId: render.extractionId, anchorSpanIds: selectionSpanIds, openSourceId: render.sourceId,
            workbenchSessionId: bound, identity: identityOf(render),
            // Reader CA6: in side by side the source is the other pane's book (§4.1).
            ...(sbsPanes && sbs.target ? { sourceIds: [sbs.target.sourceId] } : {}),
          };
          if (working) {
            // Started once the learner leaves, under the policy then in force.
            setCompareWaitsForWork({ ...request, workbenchSessionId: null });
            return;
          }
          startCompareRef.current(request);
        }
        return;
      case "reading_path":
        if (pane.side) {
          // Reader CA6b (Codex re-review F7): that book's reading path, in its pane.
          if (!contract?.readingPaths) return;
          logReaderAction("action_invoked", { ...visitPayload(), action_kind: "what_matters_here", ...meta });
          pane.side.showPath();
          return;
        }
        // RW7a: Orient's "what matters here?" opens the Guide's reading path.
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: "what_matters_here", ...meta });
        setRailCollapsed(false);
        setRailTab("guide");
        setPathFocus((value) => value + 1);
        return;
      case "figure": {
        // RW5a: built in the background; it lands under its passage.
        logReaderAction("action_invoked", { ...visitPayload(), action_kind: "make_explorable", ...meta });
        const region = pane.region;
        const words = text?.trim();
        if (words && showMeOn) {
          // RW5d P1: "show me…" with words: the selection and the learner's words, jointly.
          pane.figures.request({ spanIds: region ? [] : pane.spanIds, region, goalText: words, origin: "show_me" });
        } else {
          pane.figures.request({ spanIds: region ? [] : pane.spanIds, region });
        }
        return;
      }
    }
  };
  runIntentRef.current = (action, text, how) => runIntentIn(mainPane, action, text, how);
  runSideIntentRef.current = (action, text, how) => (sidePane ? runIntentIn(sidePane, action, text, how) : undefined);
  // ── Fix round 4: the second book's identity audit ─────────────────────────
  // Everything begun on side by side's second book -- in its pane, or on an
  // object that came from it (an exercise imported from it, an answer about
  // it) -- acts on that book: its identity comes from the pane or the object,
  // never from the open book. What needs the open book takes that book to
  // the main pane first (takeBesideBook); what the second pane can show runs
  // there while it shows that passage.
  /** The second pane shows this reading, with this passage in its section. */
  const sideShows = (extractionId: string, spanId: string): boolean =>
    side.extractionId === extractionId && Boolean(side.section?.blocks.some((block) => block.spanId === spanId));
  /** A practice pick on the second book: its check opens in that book (as check me on its marks does). */
  const checkBeside = (book: SourceIdentity, spanId: string, practiceItemId: string, proposalId: string | null) => {
    if (!onCheckMe || !library?.some((entry) => entry.sourceId === book.sourceId)) return;
    takeBesideBook(book, spanId, { kind: "check", request: { practiceItemId, proposalId, spanId, reading: book } });
  };
  /** "work through this" on an imported exercise: in the book it was imported from (verify finding 1). */
  const workThroughImported = (item: { practiceItemId: string; prompt: string }) => {
    const imported = exerciseImport;
    const spanIds = imported?.spanIds ?? (activeSpan ? [activeSpan] : []);
    if (imported && render && imported.identity.extractionId !== render.extractionId) {
      takeBesideBook(imported.identity, spanIds[0] ?? "",
        { kind: "item", practiceItemId: item.practiceItemId, stemMd: item.prompt, spanIds });
      return;
    }
    void wbCtl.openItem({ practiceItemId: item.practiceItemId, stemMd: item.prompt, spanIds });
  };
  const settleShowMeLine = (key: string, patch: Partial<ShowMeLine>) =>
    setShowMeLines((lines) => lines.map((line) => (line.key === key ? { ...line, ...patch } : line)));
  /** A "show me" goal, on the figures of the book it is about. */
  const requestShowMe = (ctl: FiguresCtl, run: Extract<BesideRun, { kind: "show_me" }>) => {
    const key = run.lineKey;
    void ctl.request({
      spanIds: [], goalText: run.goal, origin: run.origin, readingAt: { spanId: run.spanId },
      ...(run.offerRef ? { offerRef: run.offerRef } : {}),
      ...(key ? { onLanded: (figure: FigureViewDto) => settleShowMeLine(key, { state: "landed", figure }) } : {}),
    }).then((outcome) => {
      if (!key || outcome === "shown") return;
      setShowMeLines((lines) => lines.map((line) => (line.key === key && line.state === "pending"
        ? { ...line, state: outcome === "cancelled" || outcome === "skipped" ? "cancelled" : "failed" } : line)));
    });
  };
  /** The second book's "try the next step" / "show me": in its pane when it shows the passage, else in that book. */
  const runOnBook = (about: AskAbout, run: Extract<BesideRun, { kind: "next_step" | "show_me" }>) => {
    if (sideShows(about.extractionId, run.spanId)) {
      if (run.kind === "next_step") void side.active.start("next_step", [run.spanId], side.fold([run.spanId], foldBlocks));
      else requestShowMe(side.figures, run);
      return;
    }
    takeBesideBook({ sourceId: about.sourceId, revisionId: about.revisionId, extractionId: about.extractionId }, run.spanId, run);
  };
  besideRunRef.current = (run) => {
    if (run.kind === "item") {
      if (wbCtl.enabled) void wbCtl.openItem({ practiceItemId: run.practiceItemId, stemMd: run.stemMd, spanIds: run.spanIds });
    } else if (run.kind === "next_step") {
      if (activeReadingOn) void activeCtl.start("next_step", [run.spanId], localFold([run.spanId]));
    } else if (run.kind === "show_me") {
      requestShowMe(figuresCtl, run);
    }
  };
  besideDroppedRef.current = (run) => {
    if (run.kind === "show_me" && run.lineKey) settleShowMeLine(run.lineKey, { state: "failed" });
  };
  // RW5d P1: the Ask rail's "show me ▸": the box's words as a figure goal, landing
  // under the passage the learner was reading (the inquiry's, else the
  // selection's, else the reading position); the thread keeps one line for it.
  // Fix round 4: a thread about the second book, or the composer the second
  // pane opened, is that book's: the figure is built on it.
  const showMeFromAsk = () => {
    const goal = question.trim();
    const about = parentExchange ? parentExchange.about ?? null : askComposerAnchor?.about ?? null;
    const home = parentExchange?.spanId ?? (about ? askComposerAnchor?.spanId : undefined)
      ?? selectionSpanIds[selectionSpanIds.length - 1] ?? readingSpan ?? activeSpan;
    if (!goal || !home || !showMeOn) return;
    const key = `show_me:${newKey()}`;
    setShowMeLines((lines) => [...lines, { key, goal, state: "pending", figure: null }]);
    setQuestion("");
    const run = { kind: "show_me" as const, goal, spanId: home, origin: "show_me" as const, offerRef: null, lineKey: key };
    if (about) runOnBook(about, run);
    else requestShowMe(figuresCtl, run);
  };
  // "change" cancels the routed action (spec §4.2; RW1b review F4): an Ask
  // still pending stops; an active-reading card or "another way" closes (its
  // late result can't reopen it); a capture already made is reverted (its
  // annotation, and a commit preset's commitment and synthesis, through the
  // sidecar); an import still running is cancelled.
  const cancelIntentIn = (pane: IntentPane, cancel: IntentCancel) => {
    const kind = cancel.action.effect.kind;
    if (kind === "ask" && askPhase === "pending") cancelAsk();
    if (kind === "active_reading") pane.active.close();
    if (kind === "another_way") pane.active.closeAnother();
    if (kind === "library_ask" || kind === "compare") closeLibrary();
    void cancel.handle.then(async (handle) => {
      if (handle?.annotationId && cancel.routingId) {
        const annotationId = handle.annotationId;
        try {
          await api.readerIntentOutcome({ routingId: cancel.routingId, outcome: "reverted", annotationId });
          if (pane.side) {
            // The second pane's capture: its own marks re-read (nothing of the main pane's to drop).
            pane.side.marksChanged();
          } else {
            setAnnotations((list) => list.filter((a) => a.annotationId !== annotationId));
            setSelectionActions((actions) => actions.filter((action) => action !== (kind === "preset" && "preset" in cancel.action.effect ? cancel.action.effect.preset : "highlight")));
            void refreshAnnotations();
          }
          void refreshRequests();
        } catch (error) {
          onError(errorMessage(error));
        }
      }
      if (handle?.importBatchId) {
        const batchId = handle.importBatchId;
        try {
          await api.cancelIngestBatch(batchId);
        } catch {
          /* already finished: its card in Notes keeps its own controls */
        }
        setExerciseImport((current) => (current && current.batchId === batchId ? null : current));
      }
    });
  };
  cancelIntentRunRef.current = (cancel) => cancelIntentIn(mainPane, cancel);
  cancelSideIntentRunRef.current = (cancel) => {
    if (sidePane) cancelIntentIn(sidePane, cancel);
  };
  const leaveWorkbench = (session: Parameters<typeof wbCtl.close>[0], abandonedNow = false, generation?: number) => {
    // A stale departure (another problem opened since) returns null: nothing jumps (RW4b fix round 5, R5).
    const spanId = wbCtl.close(session, { abandoned: abandonedNow, ...(generation !== undefined ? { generation } : {}) });
    // Collapse back into ordinary reading at the problem's passage.
    if (spanId) window.setTimeout(() => jumpToSpan(spanId), 0);
  };
  // RW4a: "practice this ▸" is a learner pick the plan serves (the same path as
  // a cue's check me), with the book out of view.
  const pickLibraryPractice = (item: ProposedItemDto, proposalId: string | null) => {
    const card = openCardRef.current;
    if (!card || !onCheckMe || !render) return;
    // Fix round 4: an ask anchored in side by side's second pane is that
    // book's; its pick opens there, at the passage asked on (as check me does).
    const asked = libraryCtl.state?.request;
    if (asked?.identity && asked.identity.extractionId !== render.extractionId) {
      checkBeside(asked.identity, asked.spanIds[0] ?? "", item.practiceItemId, proposalId);
      return;
    }
    onCheckMe({ practiceItemId: item.practiceItemId, proposalId, spanId: readingSpan ?? activeSpan ?? "", card,
      reading: identityOf(render) });
  };
  const resumeMark = (spanId: string | null | undefined) => {
    const entry = spanId ? wbResumeBySpan.get(spanId) : undefined;
    if (!entry || working) return null;
    const verb = entry.status === "abandoned" ? "Reopen" : "Resume";
    return (
      <button
        type="button"
        aria-label={`${verb} this problem: ${wbLabel(entry.stemMd)}`}
        title={`${verb.toLowerCase()} your steps${entry.unfinished ? " · unfinished" : ""}`}
        onClick={(event) => {
          event.stopPropagation();
          void wbCtl.resume(entry.sessionId);
        }}
        style={{ position: "absolute", left: -22, top: 2, border: 0, background: "transparent", color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12, padding: 0, cursor: "pointer" }}
      >
        ✎
      </button>
    );
  };

  return (
    <NotesContext.Provider value={notesCtl.context}>
    <CompareKeepContext.Provider value={keptCtl.context}>
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
          {progress.placeApproximate && !offline ? (
            // Re-read safety: the saved place (or the search hit's passage)
            // was on an earlier reading whose words changed there.
            <Faint style={{ fontSize: 11 }}>
              {progress.placeApproximate === "found"
                ? "This book was read again: you're near the passage you found."
                : "This book was read again: you're near where you left off."}
            </Faint>
          ) : null}
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
          // Reader CA5: a peek at another book's section from the Guide is a crumb
          // only (never a return-stack entry, so Alt+→ never opens that book).
          peek={peekCrumbShown ? {
            label: peekCrumbShown.label,
            origin: currentGuideSection?.label ?? sourceTitle ?? "where I was",
            onClose: () => setAlsoClosePeekToken((token) => token + 1),
          } : null}
        />
      ) : null}
      {sbs.notice ? (
        // Reader CA6: Ctrl+\\ found nothing to open (dim, outside the text column; goes on the next touch).
        <div data-sbs-notice="" style={{ flexShrink: 0, padding: "4px 32px", borderBottom: `1px solid ${COLOR.border}` }}>
          <Faint style={{ fontSize: 11 }}>{sbs.notice}</Faint>
        </div>
      ) : null}
      <div ref={sbsRowRef} style={{ flex: 1, minHeight: 0, display: "flex", overflow: "hidden", ...(working ? { position: "relative" as const, flexDirection: wbStacked ? "column" as const : "row" as const } : {}), ...(comparingStacked ? { flexDirection: "column" as const } : {}), ...(sbs.panes || sbs.sheet ? { position: "relative" as const } : {}) }}>
        <div
          ref={bodyRef}
          role={inquiry ? "main" : undefined}
          aria-label={inquiry ? [sourceTitle, currentGuideSection?.label].filter(Boolean).join(", ") || "Source" : undefined}
          {...(working && wbBookHidden ? { "aria-hidden": true } : {})}
          {...(sbsPanes ? { tabIndex: -1, "data-sbs-main": "" } : {})}
          onMouseDown={(event) => {
            noteUserScroll();
            touchMain();
            if (sbs.notice) sbs.clearNotice();
            onBodyMouseDown(event);
          }}
          onMouseUp={() => {
            if (sbsPanes && !window.getSelection()?.isCollapsed) touchMain();
            onMouseUp();
          }}
          onKeyDown={(event) => {
            // Reader CA6: scrolling the main pane with the keyboard is the learner's hand on it (it leads).
            if (!sbsPanes || event.ctrlKey || event.metaKey || event.altKey || !SIDE_BY_SIDE_SCROLL_KEYS.has(event.key)) return;
            const target = event.target;
            if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select, button"))) return;
            touchMain();
          }}
          onWheel={() => {
            noteUserScroll();
            touchMain();
          }}
          onTouchMove={() => {
            noteUserScroll();
            touchMain();
          }}
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
            ...(wbStacked ? { order: 1, flex: wbSourceShown ? "0 0 50%" : undefined, display: wbSourceShown ? "flex" : "none", borderTop: `1px solid ${COLOR.border}` } : {}),
            // Reader CA4: the comparing posture stacked, the book below the comparison.
            ...(comparingStacked ? { order: 1, flex: "0 0 50%" } : {}),
            // Reader CA6: the two panes share the source area (the split is the learner's, per device).
            ...(sbsPanes ? { flex: `${sbsSplit} 1 0`, minWidth: 0, outline: "none" } : {}),
          }}
        >
          {sbsPanes ? (
            <div data-sbs-main-header="" style={{ position: "sticky", top: -18, zIndex: 9, margin: "-18px -32px 0", padding: "6px 32px", background: COLOR.bg, borderBottom: `1px solid ${COLOR.border}`, display: "flex", alignItems: "baseline", gap: 8, fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
              <span style={{ color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>
                § {sourceTitle ?? "this book"}{currentGuideSection ? ` · ${currentGuideSection.label}` : ""}
              </span>
              {sbs.leader === "main" ? <span data-sbs-lead="" style={{ color: COLOR.amber }}>{SIDE_BY_SIDE_COPY.lead}</span> : null}
              {sbs.staysPut === "main" ? <Faint style={{ fontSize: 10 }}>{SIDE_BY_SIDE_COPY.staysPut}</Faint> : null}
            </div>
          ) : null}
          <IntentBox box={intentBox} />
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
              marks={cueMarksFor("watch")}
              {...(activeCtl.folded.size ? { fold: { spans: activeCtl.folded, line: <NextStepFoldLine ctl={activeCtl} /> } } : {})}
            />
          ) : watchLoading ? (
            <Card style={{ padding: 18 }}><Faint style={{ fontSize: 12 }}>◐ preparing video and synchronized transcript…</Faint></Card>
          ) : null}
          {pdfView && surface === "pdf" && !offline ? (
            <PdfReaderPane
              ref={paneRef}
              fileUrl={convertFileSrc(pdfView.fileName ?? "", "llpdf")}
              blocks={pdfView.blocks}
              highlights={pdfHighlights}
              guidanceSpans={revealedGuidanceSpans}
              selection={selection}
              activeSpan={activeSpan}
              onTextSelection={(sel) => {
                // The payload is the capture itself (its nodes carry exact
                // offsets), so the pane keeps painting the words it drew.
                setSelection(sel);
                setSelectionActions([]);
                setEditingCapture(false);
                setActiveSpan(sel.spanId);
                noteSelection(sel.nodes?.length ?? 1, "pdf");
                if (intentContract) noteIntentSelection();
                else setRailTab((tab) => (tab === "ask" ? "ask" : "notes"));
              }}
              onSelectionCleared={clearSelection}
              onHighlightOpen={openAnnotationNote}
              onHighlightRemove={(id) => void deleteAnnotation(id)}
              onTagMenu={setTagMenu}
              onError={onError}
              inlineNote={inlineReconnect && reconnect ? { spanId: reconnect.spanId, node: inlineReconnect } : null}
              marks={pdfMarks()}
              onPageLayout={setPdfLayout}
              {...(activeCtl.folded.size ? { coveredSpans: activeCtl.folded } : {})}
              {...(figuresCtl.enabled ? {
                inlineNotes: [...new Set([...figuresCtl.figures.map((f) => f.anchorSpanId), ...figuresCtl.pending.map((p) => p.anchorSpanId),
                  ...figuresCtl.followed.map((entry) => entry.figure.anchorSpanId)])]
                  .filter((spanId): spanId is string => Boolean(spanId))
                  .map((spanId) => ({ spanId, node: <FiguresUnder ctl={figuresCtl} spanId={spanId} /> })),
                regionSelection: Boolean(contract?.figures?.region),
              } : {})}
            />
          ) : null}
          {removed ? (
            // A removed highlight's undo (reader-pdf-selection): quiet, at the
            // foot of the reading column, for a few seconds; Ctrl+Z works too.
            <div
              role="status"
              data-undo-remove={removed.annotation.annotationId ?? ""}
              style={{ position: "sticky", bottom: 0, zIndex: 6, background: COLOR.bg, padding: "6px 0", display: "flex", gap: 10, alignItems: "center", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}
            >
              <span>{kindLabel(removed.annotation.kind)} removed.</span>
              <button
                type="button"
                onClick={() => void undoRemove()}
                style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
              >
                undo
              </button>
              <Faint style={{ fontSize: 10 }}>ctrl+z</Faint>
            </div>
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
            const cueMark = block.spanId ? cueCtl.markOn(block.spanId) : null;
            const endSection = block.spanId ? guideSectionByEnd.get(block.spanId) : undefined;
            // The section-break button asks the one check-offer rule too.
            const endQuestionAvailable = Boolean(endSection
              && endSection.question?.readingPhase === "after_section"
              && offeredCheckSections.has(endSection.id));
            // RW1b: the book's next lines fold while the learner tries the next step.
            const folded = Boolean(block.spanId && activeCtl.folded.has(block.spanId));
            const firstFolded = folded && !(i > 0 && blocks[i - 1].spanId && activeCtl.folded.has(blocks[i - 1].spanId ?? ""));
            const offerSection = endSection
              && !muted
              && !dismissedSections.includes(endSection.id)
              && !completedSections.includes(endSection.id)
              && ((endQuestionAvailable && endSection.question !== null) || endSection.suggestedPassages.length > 0);
            return (
              <Fragment key={block.displayNodeId ?? `p${i}`}>
              {firstFolded ? (
                <div data-next-step-fold="">
                  <NextStepFoldLine ctl={activeCtl} />
                </div>
              ) : null}
              <div
                data-span-id={block.spanId ?? undefined}
                {...(folded ? { "data-folded": "" } : {})}
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
                  // RW3a: a margin mark sits in the column's gutter, beside its passage.
                  position: cueMark || (block.spanId && (wbResumeBySpan.has(block.spanId) || keptCtl.marks.has(block.spanId) || notesCtl.marks.has(block.spanId)) && !working) ? "relative" : undefined,
                }}
              >
                {folded ? null : (<>
                {cueMark ? renderMark(cueMark, "text") : null}
                {resumeMark(block.spanId)}
                {block.spanId && !working && keptCtl.marks.get(block.spanId) ? <KeptMark mark={keptCtl.marks.get(block.spanId)!} /> : null}
                {block.spanId && !working && notesCtl.marks.get(block.spanId) ? <NoteMarkButton mark={notesCtl.marks.get(block.spanId)!} /> : null}
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
                </>)}
              </div>
              {inlineReconnect && reconnect && block.spanId === reconnect.spanId ? inlineReconnect : null}
              {figuresCtl.enabled ? <FiguresUnder ctl={figuresCtl} spanId={block.spanId} /> : null}
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

        {sbsPanes ? (
          <>
            <div
              role="separator"
              aria-orientation="vertical"
              aria-label="resize side by side"
              onPointerDown={startSbsResize}
              style={{ width: 5, flexShrink: 0, cursor: "col-resize", background: COLOR.border }}
            />
            <SideBySidePane
              ref={sbsPaneRef}
              ctl={sbs}
              otherTitle={sourceTitle ?? "this book"}
              grow={1 - sbsSplit}
              // Highlights and notes in the second pane go to its own book (§6.4).
              onCaptured={(kind) => logReaderAction("action_invoked", { ...visitPayload(), action_kind: kind === "annotate" ? "note" : "highlight", entry: "side_by_side" })}
              onError={onError}
              // Reader CA6b: the intent box, cue marks, figures, fold and active reading of this pane.
              intent={side.box.enabled ? { box: side.box, onSelection: side.noteSelection } : null}
              marginFor={side.cues.cues ? (spanId) => {
                // The Reader's own mark, with the second pane's own controller (as if it were the Reader alone).
                const cue = side.cues.markOn(spanId);
                return cue ? (
                  <MarginMark
                    key={cue.cueId}
                    cue={cue}
                    open={side.cues.openCueId === cue.cueId}
                    onOpenChange={(open) => side.cues.setOpenCueId(open ? cue.cueId : null)}
                    surface="text"
                    canCheckMe={side.cues.canCheckMe}
                    checkPhase={side.cues.checkPhase(cue.cueId)}
                    onOpenEarlier={() => side.cues.openEarlier(cue)}
                    onCheckMe={() => side.cues.checkMe(cue)}
                    onNotRelevant={(text) => side.cues.notRelevant(cue, text)}
                    onFewer={() => side.cues.fewerOn(cue)}
                    onOffBook={side.cues.offBook}
                    onOffEverywhere={side.cues.offEverywhere}
                    onSeen={(planId) => side.cues.noteSeen(cue, planId)}
                    planId={side.cues.planId}
                    {...(side.cues.canTryFirst ? { onTryFirst: () => side.cues.tryFirst(cue) } : {})}
                  />
                ) : null;
              } : null}
              under={side.figures.enabled ? (spanId) => <FiguresUnder ctl={side.figures} spanId={spanId} /> : null}
              fold={side.active.folded.size ? { spans: side.active.folded, line: <NextStepFoldLine ctl={side.active} /> } : null}
              card={(activeReadingOn && (side.active.active || side.active.another)) || (side.pathShown && sbsSection) ? (
                <>
                  {activeReadingOn && (side.active.active || side.active.another) ? (
                    <ActiveReadingCard ctl={side.active} sourceTitle={sbsSection?.sourceTitle ?? null} onShowPassage={(spanId) => {
                      const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="${spanId}"]`);
                      if (node instanceof HTMLElement) node.scrollIntoView?.({ behavior: "auto", block: "start" });
                    }} />
                  ) : null}
                  {side.pathShown && sbsSection ? (
                    // Reader CA6b (Codex re-review F7): "what matters here?" in
                    // this pane: this book's reading path (the Guide's card, on
                    // this reading). A section opens in this pane; "try it"
                    // takes this book to the main pane for the workbench, as
                    // work through does (side by side one step back).
                    <div data-sbs-path="" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                        <Faint style={{ fontSize: 10 }}>{SIDE_PATH_COPY.heading(sbsSection.sourceTitle)}</Faint>
                        <button type="button" onClick={side.closePath} style={{ marginLeft: "auto", border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2 }}>{SIDE_PATH_COPY.close}</button>
                      </div>
                      <ReadingPathCard
                        extractionId={sbsSection.extractionId}
                        onJump={() => undefined}
                        onJumpSection={(spanId, sectionId) => {
                          if (sectionId !== sbsSection.sectionId) {
                            sbs.goSide(sectionId);
                            return;
                          }
                          const node = sbsPaneRef.current?.querySelector(`[data-sbs-span="${spanId}"]`);
                          if (node instanceof HTMLElement) node.scrollIntoView?.({ behavior: "auto", block: "start" });
                        }}
                        onTryExercise={wbCtl.enabled ? (exercise) => {
                          const { renderViewId: _view, clientIdempotencyKey: _key, ...importRequest } = exercise.importRequest;
                          takeBesideBook({ sourceId: sbsSection.sourceId, revisionId: exercise.importRequest.revisionId, extractionId: exercise.extractionId }, exercise.spanIds[0] ?? sbsSection.jumpSpanId, {
                            kind: "work", stemMd: exercise.statement, spanIds: exercise.spanIds, importRequest,
                          });
                        } : null}
                        onError={onError}
                        focusToken={side.pathFocus}
                      />
                    </div>
                  ) : null}
                </>
              ) : null}
              foot={side.cues.receipts.length ? (
                <span style={{ display: "inline-flex", flexDirection: "column", gap: 2 }}>
                  {side.cues.receipts.map((receipt) => (
                    <span key={receipt.id} style={{ display: "inline-flex", gap: 8, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                      <span>{receipt.label}</span>
                      <button type="button" onClick={receipt.onUndo} style={{ border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2 }}>{CUE_COPY.undo}</button>
                    </span>
                  ))}
                </span>
              ) : null}
              marksVersion={side.marksVersion}
              onCompareSelection={libraryCtl.scopeOn && render ? (picked) => {
                // CA3's selection verb in the second pane: anchored there, the source the main pane's book.
                if (!sbs.section) return;
                logReaderAction("action_invoked", { ...visitPayload(), action_kind: "compare_books", entry: "side_by_side" });
                setLibraryCompose(null);
                libraryCtl.compareFrom({
                  door: "selection", question: picked.quote, extractionId: sbs.section.extractionId,
                  anchorSpanIds: picked.spanIds, openSourceId: sbs.section.sourceId, sourceIds: [render.sourceId],
                  workbenchSessionId: null, identity: sectionIdentity(sbs.section),
                });
              } : null}
            />
          </>
        ) : null}
        {sbs.sheet && !comparing ? (
          <SideBySidePane ctl={sbs} otherTitle={sourceTitle ?? "this book"} onCompareSelection={null} />
        ) : null}
        {working && wbActive ? (
          <ReaderWorkingPosture
            wbCtl={wbCtl}
            active={wbActive}
            stacked={wbStacked}
            bookHidden={wbBookHidden}
            sourceShown={wbSourceShown}
            practiceSessionId={workbench?.practiceSessionId ?? null}
            onLeave={(session, generation) => leaveWorkbench(session, false, generation)}
            onAbandoned={(session, generation) => leaveWorkbench(session, true, generation)}
            onPeekPassage={peekWorkbenchPassage}
            onError={onError}
            askWaiting={askWaitsForWork ? { onDismiss: () => setAskWaitsForWork(false) } : null}
            compareWaiting={compareWaitsForWork ? { text: SCOPE_COPY.waitsForWork, onDismiss: () => setCompareWaitsForWork(null) } : null}
          />
        ) : null}
        {comparing && render ? (
          <LibraryPane
            ctl={libraryCtl}
            compose={libraryCompose}
            onCompose={setLibraryCompose}
            onAsk={(query) => askLibraryHere(query, "reader", selectionSpanIds.length ? selectionSpanIds : [readingSpan ?? activeSpan].filter((span): span is string => Boolean(span)), true)}
            onReword={libraryCtl.scopeOn ? (words) => { libraryCtl.close(); setLibraryCompose(words); } : null}
            onOpenHit={openLibraryHit}
            onPracticePick={onCheckMe ? pickLibraryPractice : null}
            onClose={closeLibrary}
            exercises={exerciseProps}
            onMakeExplorable={figureOffersOn ? (hit, offerRef) => makeExplorable(hit, "library", offerRef) : null}
            stacked={comparingStacked}
          />
        ) : null}
        {/* Right rail: annotation margin + capture + Ask */}
        {((inquiry && railCollapsed) || sbsPanes) && !working && !comparing && !sbsRailOverlay ? (
          <button
            type="button"
            onClick={() => (sbsPanes ? setSbsRailOverlay(true) : setRailCollapsed(false))}
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
            // Reader CA6: side by side folds the rail to its gutter; \\ reopens it as an overlay at the right.
            display: sbsPanes ? (sbsRailOverlay ? undefined : "none") : (inquiry && railCollapsed) || working || comparing ? "none" : undefined,
            ...(sbsPanes && sbsRailOverlay
              ? { position: "absolute" as const, right: 0, top: 0, bottom: 0, zIndex: 25, background: COLOR.bg, boxShadow: "-6px 0 18px rgba(0,0,0,0.18)" }
              : {}),
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
          {wbOpenSessions.length > 0 || wbCtl.abandoned ? (
            // RW2a: the problems worked here and not submitted, each one key to
            // resume (no count: threads to pick up, never a debt, UX U12).
            <div aria-label="your problems here" style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 12 }}>
              {wbCtl.abandoned ? (
                <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                  {WORKBENCH_COPY.abandoned}{" "}
                  <button
                    type="button"
                    onClick={() => void wbCtl.reopenAbandoned()}
                    style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
                  >
                    reopen
                  </button>
                </span>
              ) : null}
              {wbOpenSessions.filter((entry) => entry.sessionId !== wbCtl.abandoned?.sessionId).map((entry) => (
                <button
                  key={entry.sessionId}
                  type="button"
                  onClick={() => void wbCtl.resume(entry.sessionId)}
                  style={{ alignSelf: "flex-start", border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0, cursor: "pointer", textAlign: "left" }}
                >
                  ✎ {wbLabel(entry.stemMd)} · {entry.status === "abandoned" ? "reopen" : entry.unfinished ? "unfinished · resume" : "resume"}
                </button>
              ))}
            </div>
          ) : null}

          {/* Adaptive difficulty AD2+AD3 (§5.12, D21): now and then, one more thing to try at a
              section's end (a randomized offer, logged before it shows). */}
          <DoseOffer
            extractionId={render.extractionId}
            sectionId={completedSections[completedSections.length - 1] ?? null}
            visitId={doseVisitId}
            boundaryChecksAvailable={boundaryChecksAvailable}
            cueDensityOff={cueCtl.cues?.density === "off"}
            skim={mode === "skim"}
            restoredSpanId={progress.restoredSpan ?? null}
            sections={guidePlan?.sections ?? NO_SECTIONS}
            showingQuestionId={guidePlan?.sections.find(
              (section) => section.id === completedSections[completedSections.length - 1],
            )?.question?.authoredQuestionId ?? null}
            onShowExample={(spanId) => jumpToSpan(spanId)}
            onJump={(spanId) => jumpToSpan(spanId)}
          />

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
            path={contract?.readingPaths ? (
              // Curriculum C0b: a deliverable's slice for this book takes the path card
              // (its RPC refuses while curriculum.enabled is off: then RW7a's card, as today).
              <GuidePathSlot
                extractionId={render.extractionId}
                onJump={(spanId) => jumpToSpan(spanId, "start")}
                onError={onError}
                refreshKey={pathRefreshKey}
                readingPathCard={(
                  <ReadingPathCard
                    extractionId={render.extractionId}
                    onJump={(spanId) => jumpToSpan(spanId, "start")}
                    onTryExercise={wbCtl.enabled ? tryPathExercise : null}
                    onError={onError}
                    focusToken={pathFocus}
                    refreshKey={pathRefreshKey}
                  />
                )}
              />
            ) : undefined}
            header={recapCtl.wrapUpOpen || (recapCtl.recap && !muted) ? (
              <>
                {recapCtl.wrapUpOpen ? (
                  <WrapUpPanel
                    wrapUp={recapCtl.wrapUpOpen}
                    where="reader"
                    onClose={recapCtl.closeWrapUp}
                    followups={{
                      onUndo: (commitmentId, reason) => api.readerFollowupUndo({ commitmentId, reason }),
                      onUndoAll: (digestId, reason) => api.readerFollowupUndoAll({ digestId, reason }),
                      onRestore: (commitmentId) => api.readerFollowupRestore({ commitmentId }),
                    }}
                    isDone={(line, action) => action.action === "revisit_once" && recapRevisited(line.rootExchangeId)}
                    onAction={async (line, action) => {
                      const params = (action.params ?? {}) as { resolution?: "open" | "resolved"; trigger?: "chip" | "undo" };
                      if (action.rpc === "reader.set_inquiry_status" && params.resolution) {
                        await recapSetStatus(line.rootExchangeId, params.resolution, params.trigger ?? "chip");
                      } else if (action.rpc === "reader.invoke_preset") {
                        await recapRevisit(line.rootExchangeId);
                      }
                    }}
                  />
                ) : null}
                {recapCtl.recap && !muted ? (
                  <RecapCard
                    recap={recapCtl.recap}
                    collapsed={recapCtl.collapsed}
                    onExpand={recapCtl.expand}
                    onContinue={() => {
                      recapCtl.continueReading();
                      if (progress.restoredSpan) jumpToSpan(progress.restoredSpan);
                    }}
                    onDismiss={() => void recapCtl.dismiss()}
                    onOpenInquiry={recapOpenInquiry}
                    onSetStatus={(rootId, resolution) => void recapSetStatus(rootId, resolution)}
                    onRevisit={(rootId) => void recapRevisit(rootId)}
                    revisited={recapRevisited}
                    onResume={(sessionId) => void wbCtl.resume(sessionId)}
                    // RW6b: the card keeps the undone line ("undone · keep it
                    // after all") until it is next read, so an undo can be taken back.
                    onUndoFollowup={(commitmentId, reason) => api.readerFollowupUndo({ commitmentId, reason })}
                    onUndoAllFollowups={(digestId, reason) => api.readerFollowupUndoAll({ digestId, reason })}
                    onRestoreFollowup={(commitmentId) => api.readerFollowupRestore({ commitmentId })}
                  />
                ) : null}
              </>
            ) : null}
            findSection={contract?.correspondence?.findSection && !offline && !working ? (
              <FindSection
                extractionId={render.extractionId}
                section={currentGuideSection
                  ? { id: currentGuideSection.id, label: currentGuideSection.label, startSpanId: currentGuideSection.startSpanId }
                  : null}
                onGoThere={(target) => void openLibraryHit(target)}
                onCompare={libraryCtl.settings?.compare ? compareFoundSection : null}
                onSideBySide={sbs.enabled ? (hit) => sbs.open(sideBySideTarget(hit), "find_list") : null}
                onError={onError}
                refreshKey={coverageRefresh}
                onPeekChange={setFindPeek}
                closePeekToken={alsoClosePeekToken}
              />
            ) : undefined}
            alsoInBooks={alsoOn && !working ? (
              <AlsoInBooks
                extractionId={render.extractionId}
                section={currentGuideSection
                  ? { id: currentGuideSection.id, label: currentGuideSection.label, startSpanId: currentGuideSection.startSpanId }
                  : null}
                hidden={alsoHidden}
                onHide={hideAlsoInBooks}
                onGoThere={(target) => void openLibraryHit(target)}
                onCompare={libraryCtl.settings?.compare ? compareFoundSection : null}
                // `s` side by side (CA6): the same entry as CA5a's find list's.
                onSideBySide={sbs.enabled ? (hit) => sbs.open(sideBySideTarget(hit), "also_list") : null}
                // RW5d P4a: a kept figure of the line's section, shown here (figures follow the section).
                onOpenFigure={figuresCtl.enabled && !offline ? openFollowedFigure : null}
                onPeekChange={setAlsoPeek}
                onAvailableChange={setAlsoAvailable}
                onCoverageChanged={() => setCoverageRefresh((count) => count + 1)}
                onError={onError}
                expandToken={alsoExpandToken}
                closePeekToken={alsoClosePeekToken}
              />
            ) : undefined}
            footer={cueCtl.cues ? (
              <CueFooter
                density={cueCtl.cues.density}
                bookOff={cueCtl.cues.sourceOff}
                receipts={cueCtl.receipts}
                onDensity={cueCtl.setDensity}
                onTurnOnBook={cueCtl.turnOnBook}
                discovered={cueCtl.discovered}
              />
            ) : null}
          />

          <NotesRail
            {...(activeReadingOn && (activeCtl.active || activeCtl.another) ? {
              header: <ActiveReadingCard ctl={activeCtl} sourceTitle={sourceTitle} onShowPassage={jumpToSpan} />,
            } : {})}
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
            captureHighlight={async () => { await captureHighlight(); }}
            invokePreset={async (preset) => { await invokePreset(preset); }}
            importExercise={async () => { await importExercise(); }}
            onWorkThrough={wbCtl.enabled && selection ? workThroughSelection : undefined}
            onWorkThroughItem={wbCtl.enabled ? workThroughImported : undefined}
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
            protectionMessage={protectionMessage}
            scopeAction={render && selection ? (
              <ScopeFromPassage
                key={render.extractionId}
                extractionId={render.extractionId}
                spanIds={[...new Set(selectionNodes(selection).map((node) => node.spanId))]}
                disabled={busy}
                onError={onError}
              />
            ) : undefined}
            editingAnnotationId={editingAnnotationId}
            setEditingAnnotationId={setEditingAnnotationId}
            editingAnnotationText={editingAnnotationText}
            setEditingAnnotationText={setEditingAnnotationText}
            saveAnnotationEdit={saveAnnotationEdit}
            deleteAnnotation={deleteAnnotation}
          />

          <AskRail
            // Reader CA6b: a composer the second pane opened asks about that pane's (never protected) passage.
            protectionMessage={askComposerAnchor ? null : askProtectionMessage}
            composerAbout={askComposerAnchor ? {
              label: askComposerAnchor.about.label,
              quote: askComposerAnchor.selectionQuote ?? "",
              onClear: () => openComposer(null),
            } : null}
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
            helpStyleControl={askPanelOn ? <StoredHelpStyle onError={onError} /> : undefined}
            enterSends={askPanelOn}
            question={question}
            setQuestion={setQuestion}
            askComposerVersion={askComposerVersion}
            askComposerRef={askComposerRef}
            ask={ask}
            retryAsk={retryAsk}
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
            showMe={showMeOn && figuresCtl.enabled ? {
              lines: showMeLines,
              onShowMe: () => showMeFromAsk(),
              onOpen: (figure: FigureViewDto) => {
                // Fix round 4: a figure built on the second book opens in its pane.
                if (render && figure.extractionId !== render.extractionId) {
                  if (side.extractionId === figure.extractionId) side.figures.setExpanded(figure);
                  return;
                }
                figuresCtl.setExpanded(figure);
                // The learner pressed, so the jump is theirs, with a crumb
                // ("back to where I was") when they had scrolled away (spec
                // §6.2; Codex review F8): the return stack's peek.
                if (figure.anchorSpanId) peekPassage(figure.anchorSpanId);
              },
              // A cited passage peeks in this book, or opens its book as a
              // detour (RW1c's citations, as the tutor's onOpenPassage does).
              onPeekPassage: offline ? null : (passage: FigurePassageDto) => {
                if (render && passage.extractionId === render.extractionId) {
                  peekPassage(passage.spanId);
                  return;
                }
                if (passage.sourceId) {
                  void openLibraryHit({ sourceId: passage.sourceId, spanId: passage.spanId, extractionId: passage.extractionId });
                }
              },
              onDismiss: (key: string) => setShowMeLines((lines) => lines.filter((line) => line.key !== key)),
            } : null}
            {...(readerTutor ? {
              // RW1c: the tutor looks things up; another way, that didn't
              // help and the offers under its answers (absent while off).
              lookingUp: readerTutor.retrieval,
              personalized: readerTutor.retrieval ? { on: askPersonalizedOn, onToggle: setAskPersonalized } : null,
              tutor: {
                anotherWay: readerTutor.anotherWay && inquiry && !offline,
                offers: readerTutor.offers && !offline,
                busy: busy || offline,
                onAnotherWay: askAnotherWay,
                onDidntHelp: askDidntHelp,
                // Fix round 4: an answer about the second book offers that
                // book's practice, next step, figures and passages.
                onPracticePick: onCheckMe ? (item, proposalId, exchange) => {
                  if (exchange?.about) {
                    checkBeside(exchange.about, exchange.spanId, item.practiceItemId, proposalId);
                    return;
                  }
                  pickLibraryPractice({ practiceItemId: item.practiceItemId, prompt: item.prompt } as ProposedItemDto, proposalId);
                } : null,
                onTryNextStep: readerTutor.tryNextStep && activeReadingOn
                  ? (spanId: string, exchange?: ReaderExchange) => {
                    if (exchange?.about) runOnBook(exchange.about, { kind: "next_step", spanId });
                    else void activeCtl.start("next_step", [spanId], localFold([spanId]));
                  }
                  : null,
                // RW5d P1: the tutor's figure goal, pressed: it lands under the
                // passage the question was asked on (the server checks the goal).
                onShowMe: showMeOn && figureOffersOn && render
                  ? (goal: string, offerRef: string, exchange: ReaderExchange) => {
                    const run = { kind: "show_me" as const, goal, spanId: exchange.spanId, origin: "tutor" as const, offerRef, lineKey: null };
                    if (exchange.about) runOnBook(exchange.about, run);
                    else requestShowMe(figuresCtl, run);
                  }
                  : null,
                // RW5b: a cited equation or figure of this book the tutor judged explorable
                // (of the second book, for an answer about it: built there).
                onMakeExplorable: figureOffersOn && render
                  ? (spanId: string, offerRef: string, exchange?: ReaderExchange) => {
                    const book = exchange?.about ?? render;
                    void makeExplorable({ sourceId: book.sourceId, extractionId: book.extractionId, spanId }, "tutor", offerRef);
                  }
                  : null,
                // RW1c (Codex review F9): an excerpt or citation opens where
                // it is (this book peeks; another opens as a detour).
                onOpenPassage: offline ? null : (passage) => {
                  if (render && passage.extractionId === render.extractionId) {
                    peekPassage(passage.spanId);
                    return;
                  }
                  if (passage.sourceId) {
                    openLibraryHit({ sourceId: passage.sourceId, spanId: passage.spanId, extractionId: passage.extractionId });
                  }
                },
                offerStore: tutorOfferStore,
                // CA3: "how do your books treat this?" opens the same comparison beside
                // the book, anchored on the passage the question was asked on (absent
                // while compare from anywhere is off, or while working: today's inline table).
                onCompare: libraryCtl.scopeOn && !offline && !working && render
                  ? (request: { question: string; toolCallId: string | null }, exchange: ReaderExchange) => {
                    setLibraryCompose(null);
                    libraryCtl.compareFrom({
                      door: "tutor_offer", question: request.question, extractionId: exchange.extractionId,
                      anchorSpanIds: exchange.spanId ? [exchange.spanId] : [], toolCallId: request.toolCallId,
                      // Fix rounds 4-5: an answer about the second book leads with that book.
                      openSourceId: exchange.about?.sourceId ?? render.sourceId,
                      identity: exchange.about ?? identityOf(render),
                    });
                  }
                  : null,
                // RW4b: a practice offer's textbook exercises, as RW4a's pane gets them.
                exercises: exerciseProps,
              },
            } : {})}
          />
          {recapCtl.wrapUpOffered && !recapCtl.wrapUpOpen ? (
            // RW6a: offered once the session has activity (D34), never while
            // skimming; `w` too.
            <div style={{ borderTop: `1px solid ${COLOR.border}`, marginTop: 16, paddingTop: 8 }}>
              <button
                type="button"
                onClick={() => void recapCtl.openWrapUp()}
                style={{ border: 0, background: "transparent", padding: 0, cursor: "pointer", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11 }}
              >
                {RECAP_COPY.wrapUpOffer}
              </button>
            </div>
          ) : null}
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
            {notesCtl.enabled && !offline && render ? (
              <div
                data-note-link-entry=""
                onClick={() => {
                  setNotePicker({ spanId: tagMenu.spanId, x: tagMenu.x, y: tagMenu.y });
                  setTagMenu(null);
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = COLOR.bgInput)}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                style={{ padding: "8px 12px", fontSize: 12, color: COLOR.text, cursor: "pointer", borderTop: `1px solid ${COLOR.border}` }}
              >
                <span aria-hidden="true" style={{ color: COLOR.amber }}>› </span>{NOTES_COPY.linkNote}
              </div>
            ) : null}
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

      {notePicker && render && notesCtl.enabled ? (
        // Curriculum C2: link one of your notes to this passage (by hand: yours, never re-judged).
        <div style={{ position: "fixed", left: Math.min(notePicker.x, window.innerWidth - 440), top: Math.min(notePicker.y, window.innerHeight - 360), width: 420, maxHeight: 340, overflowY: "auto", zIndex: 320, boxShadow: "0 16px 48px rgba(0,0,0,0.55)" }}>
          <NoteLinkPicker extractionId={render.extractionId} spanId={notePicker.spanId} onClose={() => setNotePicker(null)} onError={onError} />
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
          // RW3a: the margin marks, when any is drawn (UX §3.5).
          ...(cueCtl.placement.shown.length > 0 ? [{ key: "alt+↓", label: "next mark" }] : []),
          // RW6a: once the session has something to wrap up (UX W1).
          ...(recapCtl.wrapUpOffered && !working ? [{ key: "w", label: "wrap up" }] : []),
          // Reader CA5: while the Guide has its "also in your books" line.
          ...(inquiry && alsoOn && alsoAvailable && !alsoHidden && !working && !comparing ? [{ key: "x", label: "also in your books" }] : []),
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
    </CompareKeepContext.Provider>
    </NotesContext.Provider>
  );
}
