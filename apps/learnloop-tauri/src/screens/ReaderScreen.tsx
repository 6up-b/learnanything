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

import { Fragment, forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import { convertFileSrc } from "@tauri-apps/api/core";
import { api } from "../api/client";
import type {
  CommandError,
  ReaderAnswerDto,
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
  SourceLibraryCard,
} from "../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader, TermSelect } from "../components/term";
import { MarkdownMath } from "../render/MarkdownMath";
import { AffectTap, DispositionPicker, PrimaryButton, SecondaryButton } from "../components/goldenpath/shared";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { youtubeVideoId } from "../components/sourceTail";
import { PdfReaderPane, type PdfReaderPaneHandle, type TagMenuRequest } from "../components/PdfReaderPane";

const ANSWER_MODE_OPTIONS = [
  { value: "answer_directly", label: "answer directly" },
  { value: "help_me_reason", label: "help me reason" },
  { value: "ask_me_first", label: "ask me first" },
];

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

// The wire nodes for a selection: one per covered block, falling back to the
// single primary block for selections made outside the DOM capture path (the
// PDF pane reports one block).
function selectionNodes(sel: {
  spanId: string;
  quote: string;
  nodes?: Array<{ spanId: string; quote: string }>;
}): Array<{ spanId: string; quote: string }> {
  return sel.nodes && sel.nodes.length ? sel.nodes : [{ spanId: sel.spanId, quote: sel.quote }];
}

interface BackgroundRequest {
  id: string;
  status: string;
  preset: string;
  resultJson?: string | null;
}

/** One synthesized source object head (reader.source_objects), flattened for the rail. */
interface SynthesizedObject {
  objectId: string;
  objectType: string;
  status: string;
  contentMd: string;
  exactText: string;
  spanId: string | null;
}

function parseRequestResult(resultJson: string | null | undefined): { sourceObjectId: string | null; proposalId: string | null } {
  try {
    // result_json rides the wire as an opaque JSON string — its keys stay
    // snake_case (only top-level DTO keys are camelized).
    const parsed = JSON.parse(resultJson ?? "") as { proposals?: Array<Record<string, unknown>> };
    const objectRow = (parsed.proposals ?? []).find((p) => p.kind === "source_object");
    const mappingRow = (parsed.proposals ?? []).find((p) => p.kind === "canonical_mapping");
    return {
      sourceObjectId: (objectRow?.source_object_id as string) ?? null,
      proposalId: (mappingRow?.proposal_id as string) ?? null,
    };
  } catch {
    return { sourceObjectId: null, proposalId: null };
  }
}

interface ReaderExchange {
  question: string;
  answer: ReaderAnswerDto;
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

export function ReaderScreen({ onError }: { onError: (message: string) => void }) {
  const [contract, setContract] = useState<ReaderPromptContractDto | null>(null);
  const [render, setRender] = useState<ReaderRenderViewDto | null>(null);
  const [guidePlan, setGuidePlan] = useState<ReaderGuidePlanDto | null>(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [offline, setOffline] = useState(false);
  // Source picker state: the real library (ready sources are openable), whether
  // the sidecar answered at all, and the title of whatever is open.
  const [library, setLibrary] = useState<SourceLibraryCard[] | null>(null);
  const [sidecarDown, setSidecarDown] = useState(false);
  const [sourceTitle, setSourceTitle] = useState<string | null>(null);
  const [opening, setOpening] = useState<string | null>(null);
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  // A selection may span several blocks (transcript cues are sentence
  // fragments, so in watch mode it almost always does). `nodes` carries one
  // per-block sub-quote per covered block; absent for single-block sources
  // (e.g. the PDF pane's own selection callback).
  const [selection, setSelection] = useState<{
    spanId: string;
    quote: string;
    nodes?: Array<{ spanId: string; quote: string }>;
  } | null>(null);
  const [selectionActions, setSelectionActions] = useState<string[]>([]);
  const [railTab, setRailTab] = useState<ReaderRailTab>("guide");
  const [readingSpan, setReadingSpan] = useState<string | null>(null);
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
  const [answerMode, setAnswerMode] = useState<ReaderAnswerMode>("answer_directly");
  const [history, setHistory] = useState<Record<string, ReaderExchange[]>>({});
  const [disposition, setDisposition] = useState<ReaderDisposition | null>(null);
  const [boundarySkipped, setBoundarySkipped] = useState(false);
  const [boundaryAnswered, setBoundaryAnswered] = useState(false);
  const [boundaryResponse, setBoundaryResponse] = useState("");
  const [boundarySubmitted, setBoundarySubmitted] = useState(false);
  const [mode, setMode] = useState<string>("anchor");
  const [requests, setRequests] = useState<BackgroundRequest[]>([]);
  const [proposalCount, setProposalCount] = useState<number>(0);
  // Demand-paged synthesis results: source objects by id + which mapping
  // proposals are still open, so ready requests render their content with
  // non-modal accept/dismiss (spec §6.4 — never a modal interruption).
  const [synthesizedObjects, setSynthesizedObjects] = useState<Map<string, SynthesizedObject>>(new Map());
  const [openProposalIds, setOpenProposalIds] = useState<Set<string>>(new Set());
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
  const [surface, setSurface] = useState<"pdf" | "text">("pdf");
  // Right-click tag menu (selection or whole-block), on either surface.
  const [tagMenu, setTagMenu] = useState<TagMenuRequest | null>(null);
  const [coach, setCoach] = useState<ReaderCoachLintDto | null>(null);
  const [authoringOpen, setAuthoringOpen] = useState(false);
  const [authoredQuestion, setAuthoredQuestion] = useState("");
  const [authoredAnswer, setAuthoredAnswer] = useState("");
  const [authoredCardId, setAuthoredCardId] = useState<string | null>(null);
  const [authoringSpanId, setAuthoringSpanId] = useState<string | null>(null);
  const [authoringQuote, setAuthoringQuote] = useState("");
  const [authoringBusy, setAuthoringBusy] = useState(false);
  // Across-source search on the library screen ("where did I read that?").
  const [librarySearch, setLibrarySearch] = useState("");
  const [searchResults, setSearchResults] = useState<ReaderSourceSearchDto | null>(null);
  const [searchBusy, setSearchBusy] = useState(false);
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
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const paneRef = useRef<PdfReaderPaneHandle | null>(null);
  const watchRef = useRef<WatchPanelHandle | null>(null);
  const readingRafRef = useRef<number | null>(null);

  useEffect(() => {
    api.readerPromptContract().then(setContract).catch((error) => onError((error as CommandError).message));
  }, [onError]);

  // Debounced across-source search (library screen only; deterministic, local).
  useEffect(() => {
    if (render || sidecarDown) return;
    const query = librarySearch.trim();
    if (query.length < 2) {
      setSearchResults(null);
      setSearchBusy(false);
      return;
    }
    setSearchBusy(true);
    const timer = window.setTimeout(() => {
      api
        .readerSearchSources({ query })
        .then((result) => setSearchResults(result))
        .catch(() => setSearchResults(null))
        .finally(() => setSearchBusy(false));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [librarySearch, render, sidecarDown]);

  useEffect(() => {
    try {
      window.localStorage.setItem("learnloop.reader.section-prompts", sectionPromptsEnabled ? "on" : "off");
    } catch {
      /* A denied storage write should not interrupt reading. */
    }
  }, [sectionPromptsEnabled]);

  // Load the real source library for the picker. If the sidecar is unreachable
  // the demo fixture stays available, clearly labeled (U-031) — it is never
  // silently substituted for a real source.
  useEffect(() => {
    api
      .getSourceLibrary()
      .then((snapshot) => {
        setLibrary(snapshot.sources);
        setSidecarDown(false);
      })
      .catch(() => {
        setLibrary([]);
        setSidecarDown(true);
      });
  }, []);

  // Reset per-source panel state so nothing from the previous source leaks over.
  const resetSourceState = useCallback(() => {
    setGuidePlan(null);
    setGuideLoading(false);
    setActiveSpan(null);
    setReadingSpan(null);
    setSelection(null);
    setSelectionActions([]);
    setRailTab("guide");
    setRevealedSections([]);
    setDismissedSections([]);
    setCompletedSections([]);
    setAnnotations([]);
    setNote("");
    setQuestion("");
    setHistory({});
    setDisposition(null);
    setBoundarySkipped(false);
    setBoundaryAnswered(false);
    setBoundaryResponse("");
    setBoundarySubmitted(false);
    setRequests([]);
    setSynthesizedObjects(new Map());
    setOpenProposalIds(new Set());
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
    setSurface("pdf");
    setTagMenu(null);
    setAuthoringSections([]);
    authorRequestedRef.current = new Set();
    setStickyQuestionSections([]);
    setEditingAnnotationId(null);
    setEditingAnnotationText("");
  }, []);

  const openSource = useCallback(
    async (card: SourceLibraryCard, jumpSpan?: string) => {
      setOpening(card.sourceId);
      try {
        // reader.render_view resolves a source id to its latest completed extraction.
        const view = await api.readerRenderView({ extractionId: card.sourceId });
        resetSourceState();
        setRender(view);
        setOffline(false);
        setSourceTitle(card.title);
        try {
          const savedSpan = window.localStorage.getItem(readingPositionKey(view.sourceId));
          if (savedSpan) {
            setReadingSpan(savedSpan);
            setActiveSpan(savedSpan);
          }
        } catch {
          /* Reading still works when storage is unavailable. */
        }
        // A search hit overrides the resume position: the learner asked to land
        // on the matching passage, not where they left off.
        if (jumpSpan) {
          setReadingSpan(jumpSpan);
          setActiveSpan(jumpSpan);
        }
        setGuideLoading(true);
        api.readerGuidePlan({ extractionId: view.extractionId })
          .then(setGuidePlan)
          .catch(() => setGuidePlan(null))
          .finally(() => setGuideLoading(false));
        // Hydrate durable reading progress so reveal/completion survive restarts.
        api
          .readerGetProgress({ extractionId: view.extractionId })
          .then((progress) => {
            setRevealedSections((ids) => [
              ...new Set([...ids, ...progress.sections.filter((s) => s.revealedAt).map((s) => s.sectionId)])
            ]);
            setCompletedSections((ids) => [
              ...new Set([...ids, ...progress.sections.filter((s) => s.completedAt).map((s) => s.sectionId)])
            ]);
          })
          .catch(() => undefined);
        if (youtubeVideoId(card.canonicalUri ?? "") !== null) {
          setWatchLoading(true);
          api.readerWatchPlan(card.sourceId)
            .then(setWatch)
            .catch(() => setWatch(null))
            .finally(() => setWatchLoading(false));
        } else {
          // Original-PDF surface when the originals store has this revision's bytes.
          api
            .readerPdfView({ extractionId: card.sourceId })
            .then((manifest) => setPdfView(manifest.available ? manifest : null))
            .catch(() => setPdfView(null));
        }
      } catch (error) {
        onError((error as CommandError).message);
      } finally {
        setOpening(null);
      }
    },
    [onError, resetSourceState],
  );

  const openFixture = useCallback(() => {
    resetSourceState();
    setRender(readerRenderViewFixture);
    setOffline(true);
    setSourceTitle("demo chapter (fixture)");
  }, [resetSourceState]);

  const backToLibrary = useCallback(() => {
    resetSourceState();
    setRender(null);
    setOffline(false);
    setSourceTitle(null);
  }, [resetSourceState]);

  const enabled = contract?.readerEnabled ?? false;
  const boundaryChecksAvailable = mode === "anchor" && sectionPromptsEnabled;
  const blocks: ReaderRenderBlockDto[] = useMemo(
    () => (render?.blocks ?? []).filter((b) => !FURNITURE_BLOCK_TYPES.has(b.blockType ?? "")),
    [render],
  );
  const activeBlock = useMemo(() => blocks.find((block) => block.spanId === activeSpan) ?? null, [blocks, activeSpan]);

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
    return at < 0 ? 0 : (at + 1) / Math.max(1, currentGuideSection.spanIds.length);
  }, [currentGuideSection, readingSpan, activeSpan]);
  const currentQuestionDue = useMemo(() => {
    const phase = currentGuideSection?.question?.readingPhase;
    if (!phase) return false;
    if (phase === "before_section") {
      const firstSpan = 1 / Math.max(1, currentGuideSection?.spanIds.length ?? 1);
      return currentSectionProgress <= Math.max(0.3, firstSpan);
    }
    if (phase === "during_section") return currentSectionProgress >= 0.45;
    return currentSectionProgress >= 0.7;
  }, [currentGuideSection, currentSectionProgress]);

  // Pin a question the moment it becomes due; it stays pinned (and rendered)
  // until answered or dismissed, however far playback or scrolling moves on.
  useEffect(() => {
    if (!boundaryChecksAvailable || !currentGuideSection?.question || !currentQuestionDue) return;
    const sectionId = currentGuideSection.id;
    if (dismissedSections.includes(sectionId) || completedSections.includes(sectionId)) return;
    setStickyQuestionSections((ids) => (ids.includes(sectionId) ? ids : [...ids, sectionId]));
  }, [boundaryChecksAvailable, currentGuideSection, currentQuestionDue, dismissedSections, completedSections]);

  const openQuestionSections = useMemo(
    () =>
      stickyQuestionSections
        .map((id) => guidePlan?.sections.find((section) => section.id === id))
        .filter(
          (section): section is ReaderGuideSectionDto =>
            !!section
            && section.question !== null
            && !dismissedSections.includes(section.id)
            && !completedSections.includes(section.id),
        ),
    [stickyQuestionSections, guidePlan, dismissedSections, completedSections],
  );
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
    if (currentSectionProgress < 0.6) return;
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
  }, [render, offline, boundaryChecksAvailable, guideLoading, currentGuideSection, currentSectionProgress, dismissedSections, completedSections]);

  // While authoring is in flight, re-fetch the guide plan (a cheap local read)
  // until the section gains its question or a bounded number of polls passes.
  useEffect(() => {
    if (!render || offline || authoringSections.length === 0) return;
    const extractionId = render.extractionId;
    let attempts = 0;
    const timer = window.setInterval(() => {
      attempts += 1;
      if (attempts > 45) {
        setAuthoringSections([]);
        return;
      }
      void api
        .readerGuidePlan({ extractionId })
        .then((plan) => {
          setGuidePlan(plan);
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

  const updateReadingPosition = useCallback(() => {
    const container = bodyRef.current;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    const markerY = containerRect.top + containerRect.height * 0.7;
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
      const result = await api.readerSourceAnnotations({ sourceId: render.sourceId });
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
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
    setSelection({ spanId: nodes[0].spanId, quote, nodes });
    setSelectionActions([]);
    setActiveSpan(nodes[0].spanId);
    setRailTab("notes");
  }, [collectSelectionNodes]);

  const refreshRequests = useCallback(async () => {
    if (!render || offline) return;
    try {
      const [reqs, inbox, objects] = await Promise.all([
        api.readerSourceRequests(render.sourceId),
        api.readerProposalInbox({ status: "proposed" }),
        api.readerSourceObjects(render.sourceId),
      ]);
      setRequests((reqs.requests as BackgroundRequest[]) ?? []);
      const proposals = (inbox.proposals as Array<Record<string, unknown>>) ?? [];
      setProposalCount(proposals.length);
      setOpenProposalIds(new Set(proposals.map((p) => String(p.id))));
      const flattened = new Map<string, SynthesizedObject>();
      for (const head of (objects.sourceObjects as Array<Record<string, unknown>>) ?? []) {
        const object = (head.object as Record<string, unknown>) ?? {};
        const version = (head.version as Record<string, unknown>) ?? {};
        const citations = (head.citations as Array<Record<string, unknown>>) ?? [];
        let contentMd = "";
        try {
          const content = JSON.parse(String(version.contentJson ?? "")) as { content_md?: string };
          contentMd = content.content_md ?? "";
        } catch {
          /* stub-era objects carry no content_md; exactText still renders */
        }
        flattened.set(String(object.id ?? ""), {
          objectId: String(object.id ?? ""),
          objectType: String(version.objectType ?? "claim"),
          status: String(version.status ?? "proposed"),
          contentMd,
          exactText: String(version.exactText ?? ""),
          spanId: citations.length ? String(citations[0].spanId ?? "") || null : null,
        });
      }
      setSynthesizedObjects(flattened);
    } catch {
      /* status is best-effort */
    }
  }, [render, offline]);

  const decideProposal = useCallback(async (proposalId: string, decision: "accept" | "reject") => {
    setBusy(true);
    try {
      if (decision === "accept") await api.readerAcceptProposal(proposalId);
      else await api.readerRejectProposal(proposalId);
      void refreshRequests();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [onError, refreshRequests]);

  const retryRequest = useCallback(async (requestId: string) => {
    try {
      await api.readerRetryRequest(requestId);
      void refreshRequests();
    } catch (error) {
      onError((error as CommandError).message);
    }
  }, [onError, refreshRequests]);

  useEffect(() => {
    void refreshRequests();
  }, [refreshRequests]);

  useEffect(() => {
    if (!requests.some((request) => ["queued", "running", "pending"].includes(request.status))) return;
    const timer = window.setInterval(() => void refreshRequests(), 2000);
    return () => window.clearInterval(timer);
  }, [requests, refreshRequests]);

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
      // transcript cues); a bare right-click tags the whole single block.
      const quotedNodes = (() => {
        if (target.quote === null) return null;
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
          { annotationId: receipt.annotationId, quote: displayQuote, status: receipt.anchorStatus ?? "exact", learnerText: "", kind: action, segments: optimisticSegments(target.spanId) },
          ...a,
        ]);
        setActiveSpan(target.spanId);
        void refreshAnnotations();
      } catch (error) {
        onError((error as CommandError).message);
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
      if (el instanceof HTMLElement) el.scrollIntoView({ behavior: "smooth", block: "center" });
    },
    [pdfView, surface, offline],
  );

  const jumpToSpan = useCallback(
    (spanId: string) => {
      setActiveSpan(spanId);
      setReadingSpan(spanId);
      // Watch mode: a jump means "take the video there" — seek the player (the
      // transcript follows), never just scroll a nested list.
      if (watchRef.current?.seekToSpan(spanId)) return;
      if (pdfView && surface === "pdf" && !offline) {
        const geometry = pdfView.blocks.find((block) => block.spanId === spanId);
        if (geometry) {
          paneRef.current?.scrollToSegment(geometry.page, spanId);
          return;
        }
      }
      const el = bodyRef.current?.querySelector(`[data-span-id="${spanId}"]`);
      if (el instanceof HTMLElement) el.scrollIntoView({ behavior: "smooth", block: "center" });
    },
    [pdfView, surface, offline],
  );

  // Resume the last stable span after the chosen surface has mounted. The
  // position is local to the source and never becomes learner evidence.
  useEffect(() => {
    if (!render || offline || !readingSpan) return;
    const frame = window.requestAnimationFrame(() => {
      if (pdfView && surface === "pdf") {
        const geometry = pdfView.blocks.find((block) => block.spanId === readingSpan);
        if (geometry) paneRef.current?.scrollToSegment(geometry.page, readingSpan);
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

  // Palette (§5.2): a preset runs the local-first capture transaction. Commit presets
  // also create a commitment; synthesis is enqueued off the hot path (§5.3, §6).
  const invokePreset = useCallback(
    async (preset: string) => {
      if (!render || !selection) return;
      const nodes = selectionNodes(selection);
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
          rawSelection: { nodes },
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
        await api.readerDrainOutbox().catch(() => {});
        void refreshAnnotations();
        void refreshRequests();
      } catch (error) {
        onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
        onError((error as CommandError).message);
      }
    },
    [arc, offline, enabled, onError],
  );

  const saveOwnQuestion = useCallback(async () => {
    if (!render || !authoredQuestion.trim() || !authoredAnswer.trim()) return;
    setAuthoringBusy(true);
    try {
      if (offline) {
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
        setAuthoredCardId(saved.cardId);
      }
      setCoach(null);
    } catch (error) {
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
    }
  }, [authoredQuestion, authoredAnswer, authoredCardId, offline, enabled, onError]);

  const changeMode = useCallback(
    async (next: string) => {
      setMode(next);
      if (!render || offline || !enabled) return;
      api.readerSetMode({ mode: next, extractionId: render.extractionId }).catch(() => {});
    },
    [render, offline, enabled],
  );

  const sendQuestionControl = useCallback(
    async (control: string) => {
      setQuestionControl(control);
      if (!render || offline || !enabled) return;
      try {
        await api.readerQuestionControl({ control, subjectId: boundaryBlock?.spanId ?? undefined });
      } catch (error) {
        onError((error as CommandError).message);
      }
    },
    [render, offline, enabled, boundaryBlock, onError],
  );

  const ask = useCallback(async () => {
    if (!activeSpan || !question.trim() || !render) return;
    const asked = question.trim();
    setBusy(true);
    try {
      const answer = await api.readerAsk({
        extractionId: render.extractionId,
        spanId: activeSpan,
        question: asked,
        answerMode,
      });
      setHistory((h) => ({ ...h, [activeSpan]: [...(h[activeSpan] ?? []), { question: asked, answer }] }));
      setQuestion("");
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [activeSpan, question, answerMode, render, onError]);

  const chooseDisposition = useCallback(
    async (d: ReaderDisposition) => {
      setDisposition(d);
      if (!enabled || !boundaryBlock) return;
      try {
        await api.readerChooseDisposition({ disposition: d, subjectId: boundaryBlock.spanId ?? "", subjectType: "reader_span" });
      } catch (error) {
        onError((error as CommandError).message);
      }
    },
    [enabled, boundaryBlock, onError],
  );

  // ── Source picker: the Reader's front door is the real library ──
  if (!render) {
    const readySources = (library ?? []).filter((c) => c.readiness === "ready");
    const pendingCount = (library ?? []).length - readySources.length;
    return (
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>READER · LIBRARY</span>
            {sidecarDown ? <Pill color="amber">offline</Pill> : null}
          </div>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
            Pick up where you left off, or open something new.
          </span>
        </div>
        <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 32px", display: "flex", flexDirection: "column", gap: 10, maxWidth: 720 }}>
          {enabled && !sidecarDown ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  value={librarySearch}
                  onChange={(e) => setLibrarySearch(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") setLibrarySearch("");
                  }}
                  placeholder="search all sources…"
                  style={{ fontFamily: FONT_MONO, fontSize: 12, width: 280, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 10px" }}
                />
                {searchBusy ? <Faint style={{ fontSize: 11 }}>◐ searching…</Faint> : searchResults ? (
                  <Faint style={{ fontSize: 11 }}>
                    {searchResults.hits.length} hit{searchResults.hits.length === 1 ? "" : "s"} across {searchResults.searchedSources} source{searchResults.searchedSources === 1 ? "" : "s"}
                  </Faint>
                ) : null}
              </div>
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
                <Faint style={{ fontSize: 11 }}>no matches — this searches the extracted text of every ready source.</Faint>
              ) : null}
            </div>
          ) : null}
          {!enabled && !sidecarDown ? (
            <Card style={{ borderStyle: "dashed", display: "flex", flexDirection: "column", gap: 6 }}>
              <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
                the reader is disabled in this vault's config (new vaults have it on by default). Set <Dim>tutor_qa.reader_enabled = true</Dim>
                in learnloop.toml to read and annotate real sources; the demo chapter below works without it.
              </Faint>
            </Card>
          ) : null}
          {library === null ? (
            <Faint style={{ fontSize: 12 }}>◐ loading source library…</Faint>
          ) : readySources.length === 0 ? (
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              {sidecarDown
                ? "the sidecar is unreachable — only the offline demo chapter is available."
                : "no ready sources yet — ingest a source in the Ingest tab, then return here to read it."}
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
                  <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>{card.unitCount} sections</Faint>
                </Card>
              );
            })
          )}
          {pendingCount > 0 ? (
            <Faint style={{ fontSize: 11 }}>{pendingCount} source{pendingCount === 1 ? " is" : "s are"} still getting ready.</Faint>
          ) : null}
          <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 10 }}>
            <SecondaryButton onClick={openFixture}>open demo chapter (fixture)</SecondaryButton>
            <Faint style={{ fontSize: 11 }}>offline demo — captures are not persisted.</Faint>
          </div>
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
          <span
            onClick={backToLibrary}
            style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: "pointer" }}
          >
            ← library
          </span>
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

      <div style={{ flex: 1, minHeight: 0, display: "flex" }}>
        <div
          ref={bodyRef}
          onMouseUp={onMouseUp}
          onScroll={onReadingScroll}
          className="ll-scroll"
          style={{ flex: 1, overflowY: "auto", padding: "18px 32px", display: "flex", flexDirection: "column", gap: 12 }}
        >
          {watch ? (
            <YouTubeWatchPanel
              ref={watchRef}
              plan={watch}
              blocks={blocks}
              annotatedSpans={annotatedSpans}
              guidanceSpans={revealedGuidanceSpans}
              resumeSpan={readingSpan}
              onPlaybackSpan={setReadingSpan}
              onAskSpan={(spanId) => {
                if (spanId) setActiveSpan(spanId);
              }}
              onTagMenu={setTagMenu}
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
              activeSpan={activeSpan}
              onSelectSpan={setActiveSpan}
              onTextSelection={(sel) => {
                setSelection(sel);
                setSelectionActions([]);
                setActiveSpan(sel.spanId);
                setRailTab("notes");
              }}
              onTagMenu={setTagMenu}
              onError={onError}
            />
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
                onClick={() => setActiveSpan(block.spanId)}
                onContextMenu={(e) => {
                  if (!block.spanId) return;
                  e.preventDefault();
                  const sel = window.getSelection();
                  const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : "";
                  setTagMenu({ x: e.clientX, y: e.clientY, spanId: block.spanId, quote: quote || null });
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
                  onOpen={() => setRailTab("guide")}
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
        <div style={{ width: 360, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, padding: "18px 20px", overflowY: "auto" }} className="ll-scroll">
          <div style={{ position: "sticky", top: -18, zIndex: 8, margin: "-18px -20px 16px", padding: "12px 20px 10px", background: COLOR.bg, borderBottom: `1px solid ${COLOR.border}`, display: "flex", gap: 4 }}>
            {(["guide", "ask", "notes"] as ReaderRailTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setRailTab(tab)}
                aria-pressed={railTab === tab}
                style={{ flex: 1, border: `1px solid ${railTab === tab ? COLOR.borderFocus : COLOR.border}`, background: railTab === tab ? COLOR.washAmber : "transparent", color: railTab === tab ? COLOR.amberLink : COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, padding: "6px 8px", cursor: "pointer", textTransform: "uppercase", letterSpacing: "0.08em" }}
              >
                {tab}{tab === "notes" && annotations.length > 0 ? ` ${annotations.length}` : ""}
              </button>
            ))}
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
                <div style={{ height: 3, background: COLOR.border }}>
                  <div style={{ height: "100%", width: `${currentSectionProgress * 100}%`, background: COLOR.cyan }} />
                </div>
                <Faint style={{ fontSize: 10 }}>
                  {boundaryChecksAvailable && currentGuideSection.question && currentQuestionDue
                    ? currentGuideSection.question.readingPhase === "before_section"
                      ? "There’s an optional question before you begin this section."
                      : currentGuideSection.question.readingPhase === "during_section"
                        ? "There’s an optional question at this point in the section."
                        : "You’re near the section break. Take a quick check or keep reading."
                    : authoringSections.includes(currentGuideSection.id)
                      ? "◐ writing a quick check for this section…"
                      : currentSectionProgress >= 0.7
                        ? "You’re near the section break. Keep going, or revisit a useful passage."
                        : "Keep reading at your own pace."}
                </Faint>
              </Card>
            ) : guideLoading ? (
              <Faint style={{ fontSize: 12 }}>◐ connecting this source to your learning path…</Faint>
            ) : guidePlan === null ? (
              <Faint style={{ fontSize: 12 }}>No personalized guide is available for this source yet.</Faint>
            ) : null}

            {(guidePlan?.sections.length ?? 0) > 1 ? (
              <>
                <SectionHeader>Contents</SectionHeader>
                <div className="ll-scroll" style={{ maxHeight: 220, overflowY: "auto", display: "flex", flexDirection: "column", marginBottom: 4 }}>
                  {guidePlan!.sections.map((section, index) => {
                    const currentIndex = guidePlan!.sections.findIndex((s) => s.id === currentGuideSection?.id);
                    const state = index < currentIndex ? "read" : index === currentIndex ? "current" : "upcoming";
                    const glyph = state === "read" ? "✓" : state === "current" ? "◐" : "·";
                    return (
                      <button
                        key={section.id}
                        type="button"
                        onClick={() => jumpToSpan(section.startSpanId)}
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
                        {section.question ? (
                          <span style={{ flexShrink: 0, fontSize: 10, color: COLOR.purpleText }} aria-label="quick check available">?</span>
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

            {boundaryChecksAvailable
              ? openQuestionSections.map((section) =>
                  section.question?.placement === "auto_authored" ? (
                    <AuthoredQuestionCard
                      key={section.id}
                      section={section}
                      onJump={jumpToSpan}
                      onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, section.id])])}
                      onComplete={() => completeSection(section.id)}
                      onError={onError}
                    />
                  ) : (
                    <SectionQuestionCard
                      key={section.id}
                      section={section}
                      extractionId={render.extractionId}
                      onReveal={() => revealSection(section.id)}
                      onJump={jumpToSpan}
                      onDismiss={() => setDismissedSections((ids) => [...new Set([...ids, section.id])])}
                      onComplete={() => completeSection(section.id)}
                      onError={onError}
                    />
                  ),
                )
              : null}
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
                  <button type="button" onClick={() => { setSelection(null); setSelectionActions([]); }} style={{ marginLeft: "auto", border: 0, background: "transparent", color: COLOR.textFaint, fontFamily: FONT_MONO, cursor: "pointer" }}>clear</button>
                </div>
                <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>“{selection.quote}”</span>
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
            <Faint style={{ fontSize: 12 }}>select text in the reading column to capture it.</Faint>
          )}

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
                      <Faint style={{ fontSize: 11, color: COLOR.green }}>✓ Saved in your exact words. It will return as personal practice.</Faint>
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

          {requests.length > 0 ? (
            <>
              <SectionHeader>Your requests</SectionHeader>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {requests.map((request) => {
                  const { sourceObjectId, proposalId } = parseRequestResult(request.resultJson);
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
                      placeholder="Answer in your own words…"
                      style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.borderFocus}`, color: COLOR.text, padding: 8, minHeight: 76, resize: "vertical" }}
                    />
                    <div style={{ display: "flex", gap: 8 }}>
                      <PrimaryButton onClick={() => setBoundarySubmitted(true)} disabled={!boundaryResponse.trim()}>record answer ↵</PrimaryButton>
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
          ) : !activeSpan ? (
            <Faint style={{ fontSize: 12 }}>select a paragraph to ask about it.</Faint>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {activeBlock ? (
                <Card style={{ display: "flex", flexDirection: "column", gap: 4, background: COLOR.bgElev }}>
                  <Faint style={{ fontSize: 10 }}>ASKING ABOUT</Faint>
                  <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>“{clip(activeBlock.markdown.replace(/\s+/g, " "), 150)}”</span>
                </Card>
              ) : null}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Faint style={{ fontSize: 11 }}>mode</Faint>
                <TermSelect
                  value={answerMode}
                  options={ANSWER_MODE_OPTIONS}
                  onChange={(v) => {
                    const mode = v as ReaderAnswerMode;
                    setAnswerMode(mode);
                    if (render && activeSpan) {
                      api.readerSetAnswerMode({ extractionId: render.extractionId, spanId: activeSpan, answerMode: mode }).catch(() => {});
                    }
                  }}
                  width={160}
                />
              </div>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="ask about this span…"
                style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 70, resize: "vertical" }}
              />
              <PrimaryButton onClick={ask} disabled={busy || !question.trim()}>ask ↵</PrimaryButton>
              {(history[activeSpan] ?? []).map((exchange, i) => (
                <Card key={i} status="running" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <Faint style={{ fontSize: 10 }}>YOU ASKED</Faint>
                  <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
                    <MarkdownMath value={exchange.question} />
                  </div>
                  <Pill color="cyan">{exchange.answer.answerMode}</Pill>
                  <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
                    <MarkdownMath value={exchange.answer.answerMd} />
                  </div>
                </Card>
              ))}
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

      <KeyBar keys={[{ key: "select", label: "capture text" }, { key: "right-click", label: "tag" }]} right={{ key: "^p", label: "palette" }} />
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
  onJump,
  onDismiss,
  onComplete,
  onError,
}: {
  section: ReaderGuideSectionDto;
  onJump: (spanId: string) => void;
  onDismiss: () => void;
  onComplete: () => void;
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

  const submit = useCallback(async () => {
    if (!questionId || !response.trim()) return;
    setBusy(true);
    try {
      await api.readerAuthoredQuestionAction({ questionId, action: "answered", response: response.trim() });
      setSubmitted(true);
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [questionId, response, onError]);

  const dismissForever = useCallback(async () => {
    if (!questionId) return;
    setBusy(true);
    try {
      await api.readerAuthoredQuestionAction({ questionId, action: "dismissed" });
      onDismiss();
    } catch (error) {
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
            <PrimaryButton onClick={() => void submit()} disabled={busy || !response.trim()}>compare with the source ↵</PrimaryButton>
            <SecondaryButton onClick={onDismiss} disabled={busy}>skip</SecondaryButton>
          </div>
        </>
      ) : (
        <>
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
  extractionId,
  onReveal,
  onJump,
  onDismiss,
  onComplete,
  onError,
}: {
  section: ReaderGuideSectionDto;
  extractionId: string;
  onReveal: () => void;
  onJump: (spanId: string) => void;
  onDismiss: () => void;
  onComplete: () => void;
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
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [question, administrationId, onError]);

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
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [administrationId, response, question, onError]);

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
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
      onError((error as CommandError).message);
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
            <PrimaryButton onClick={() => void submit()} disabled={busy || !response.trim()}>record answer ↵</PrimaryButton>
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
  onPlaybackSpan: (spanId: string | null) => void;
  onAskSpan: (spanId: string | null) => void;
  onTagMenu: (request: TagMenuRequest) => void;
}>(function YouTubeWatchPanel({
  plan,
  blocks,
  annotatedSpans,
  guidanceSpans,
  resumeSpan,
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
      post("seekTo", [resumeCue.start, true]);
      setCurrentTime(resumeCue.start);
    }
    setPlayerReady(true);
  }, [post, transcriptCues]);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (event.origin !== YT_ORIGIN) return;
      let data: { event?: string; info?: { currentTime?: number } };
      try {
        data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      } catch {
        return;
      }
      if (data?.event === "infoDelivery" && typeof data.info?.currentTime === "number") {
        setCurrentTime(data.info.currentTime);
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
    onPlaybackSpan(spanId);
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
    post("seekTo", [cue.start, true]);
    post("playVideo");
    setFollowTranscript(true);
    onAskSpan(cue.block.spanId);
  }, [onAskSpan, post]);

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
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
        event.preventDefault();
        openFind();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [openFind]);

  // Imperative jump for the guide rail (contents outline, quick-check "show me
  // the passage", suggested passages): seek the video to the cue's start
  // without forcing playback, and resume transcript follow so the scroller
  // lands on it. Returns false when the span is not a transcript cue.
  useImperativeHandle(ref, () => ({
    seekToSpan: (spanId: string) => {
      const cue = transcriptCues.find((c) => c.block.spanId === spanId);
      if (!cue) return false;
      post("seekTo", [cue.start, true]);
      setCurrentTime(cue.start);
      setFollowTranscript(true);
      return true;
    },
  }), [transcriptCues, post]);

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
