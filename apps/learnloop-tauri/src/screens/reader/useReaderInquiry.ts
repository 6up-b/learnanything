// RW1a's inquiry orchestration (reader workbench spec §4.1), moved out of
// ReaderScreen by the RW3a hook extraction with no behaviour change.
//
// The Ask and its branches (a follow-up names its parent exchange), the
// durable history, the return stack and its detours (a branch, a peek,
// another source), the reconnect line ("does this make sense now?"), the
// inquiry's status on its root question, the root commitments made from the
// status chips, and the passage-scoped quick check with its durable job and
// poll. The view (the rail, the strip, the inline line) stays in the screen
// and reads what this hook returns.
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
  InquiryResolution,
  InquirySelfCheck,
  ReaderAnswerMode,
  ReaderArcDto,
  ReaderGuideSectionDto,
  ReaderInquiryQuestionDto,
  ReaderRenderViewDto,
  ReaderRetrievalIntent,
  SourceLibraryCard,
} from "../../api/dto";
import type { PassageAlign } from "../../components/PdfReaderPane";
import { TUTOR_COPY } from "./TutorAnswer";
import { errorMessage } from "../../errors";
import {
  activitySince,
  learnerActivitySnapshot,
  logReaderAction,
  logReaderActivity,
  newActivityId,
  noteLearnerActivity,
} from "./activity";
import { checkOffer } from "./checkOffer";
import { phaseForError, type ModelActionPhase } from "./ModelActionState";
import { type AskAbout, type InquiryCommitment, type ReaderExchange } from "./ReaderAskBranches";
import { cachedSourceRead } from "./readerCache";
import { clip, selectionNodes, type MarginAnnotation, type ReaderSelection } from "./readerShared";
import { encodeReadingPlace, readingPositionKey } from "./useReadingProgress";
import type { ReaderVisit } from "./useReaderVisit";
import type { PaneTarget } from "./sideBySide";
import { screenLeavesKey } from "../../app/keymap";
import {
  back as stackBack,
  dropCurrent,
  EMPTY_STACK,
  forward as stackForward,
  hasDetour,
  markReturned,
  replaceCurrent,
  pushDetour,
  stackInquiryExchange,
  unreturnedDetours,
  type RailTab,
  type ReturnEntry,
  type ReturnStack,
} from "./returnStack";

// The passage quick check's poll (F4): every 3 s for at most 10 minutes (the
// Codex turn timeout is 8), then it fails as timed out.
export const INQUIRY_CHECK_POLL_MS = 3000;
export const INQUIRY_CHECK_MAX_POLLS = 200;

/** The failed line for a spend refusal, by which limit stopped it (re-review
 *  F15): no price set for a metered model, or over the per-check limit. */
function spendRefusalLine(refusal: string | null | undefined): string {
  if (refusal === "no_price") return "Couldn't write a quick check: no price is set for this model, so LearnLoop won't spend on it.";
  if (refusal === "over_cap") return "Couldn't write a quick check: it would cost more than the spending limit for one quick check, so LearnLoop didn't send it.";
  return "Couldn't write a quick check: a spending limit stopped it before it was sent.";
}

function newKey(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `cap-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

/** The reconnect line: an open inquiry's root, asked "does this make sense now?". */
/** Reader CA6b: an Ask anchored on side by side's second pane (its book, its selection). */
export interface AskAnchor {
  about: AskAbout;
  spanId: string;
  selectionSpanIds: string[];
  selectionQuote: string | null;
}

/** What a submitted Ask may override: RW1b's routed answer mode and funnel
 *  names, RW1c's retrieval intent, and (Reader CA6b) the second pane's anchor. */
export interface AskOverride {
  answerMode?: ReaderAnswerMode;
  meta?: Record<string, unknown>;
  retrievalIntent?: ReaderRetrievalIntent;
  anchor?: AskAnchor;
}

export interface ReconnectState {
  rootId: string;
  question: string;
  spanId: string;
  inline: boolean;
}

/** One inquiry's passage-scoped quick check, as the rail shows it. */
export interface InquiryCheckState {
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
}

export interface ReaderInquiryInput {
  render: ReaderRenderViewDto | null;
  offline: boolean;
  /** RW1a's switch (reader_inquiry.enabled). */
  inquiry: boolean;
  /** Skim with inquiry on: no reconnect line. */
  muted: boolean;
  library: SourceLibraryCard[] | null;
  sourceTitle: string | null;
  selection: ReaderSelection | null;
  setSelection: Dispatch<SetStateAction<ReaderSelection | null>>;
  setSelectionActions: Dispatch<SetStateAction<string[]>>;
  activeSpan: string | null;
  railTab: RailTab;
  setRailTab: Dispatch<SetStateAction<RailTab>>;
  answerMode: ReaderAnswerMode;
  setBusy: Dispatch<SetStateAction<boolean>>;
  onError: (message: string) => void;
  annotations: MarginAnnotation[];
  refreshAnnotations: () => Promise<void>;
  setArc: Dispatch<SetStateAction<ReaderArcDto | null>>;
  visit: ReaderVisit;
  readingSpan: string | null;
  guideSectionBySpan: Map<string, ReaderGuideSectionDto>;
  jumpToSpan: (spanId: string, align?: PassageAlign) => void;
  onReadingScroll: () => void;
  /** An explicit jump is moving the page until this time (useReadingProgress). */
  jumpGuardRef: MutableRefObject<number>;
  bodyRef: RefObject<HTMLDivElement | null>;
  askComposerRef: RefObject<HTMLTextAreaElement | null>;
  /** A walk of the return stack landed the learner on this passage (RW3a:
   *  no margin mark greets them there). */
  onRestored?: (spanId: string | null) => void;
  /** RW1c: the bound workbench session the learner is working in, if any, so
   *  the tutor's retrieval reads as that item's practice (never wider). */
  workbenchSessionRef?: MutableRefObject<string | null>;
  /** RW1c: the composer's personalized chip while the tutor looks things up
   *  (null: retrieval off, nothing sent and the server's default holds). */
  personalizedRef?: MutableRefObject<boolean | null>;
  /** Reader CA6b: an empty Enter in side by side's second pane: the composer's
   *  next new question is anchored there (null: the open book, as before). */
  composerAnchorRef?: MutableRefObject<AskAnchor | null>;
  /** The screen's openSource (a restore may reopen the source a detour left). */
  openSourceRef: MutableRefObject<
    ((card: SourceLibraryCard, jumpSpan?: string,
      options?: { via?: "search" | "restore"; jumpReading?: string | null }) => Promise<unknown>) | null
  >;
}

export interface ReaderInquiry {
  question: string;
  setQuestion: Dispatch<SetStateAction<string>>;
  askComposerVersion: number;
  parentExchange: ReaderExchange | null;
  setParentExchange: Dispatch<SetStateAction<ReaderExchange | null>>;
  history: ReaderExchange[];
  visibleAskHistory: ReaderExchange[];
  normalizedAskFind: string;
  collapsedAskIds: Set<string>;
  setCollapsedAskIds: Dispatch<SetStateAction<Set<string>>>;
  askFindOpen: boolean;
  setAskFindOpen: Dispatch<SetStateAction<boolean>>;
  askFindQuery: string;
  setAskFindQuery: Dispatch<SetStateAction<string>>;
  askFindInputRef: MutableRefObject<HTMLInputElement | null>;
  askPhase: ModelActionPhase;
  askTabMarked: boolean;
  returnStack: ReturnStack;
  returnStackRef: MutableRefObject<ReturnStack>;
  reconnect: ReconnectState | null;
  inquiryChecks: Record<string, InquiryCheckState>;
  passageCheckOffered: boolean;
  submitAsk: (asked: string, parent: ReaderExchange | null, override?: AskOverride) => Promise<void>;
  ask: () => void;
  /** Reader CA6b (re-review F8): the stack handed back across a remount. */
  seedReturnStack: (stack: ReturnStack) => void;
  /** "try again": the request that just failed (re-review F10). */
  retryAsk: () => void;
  /** A new composer opened: a failed request is not its own (re-review F10). */
  forgetFailedAsk: () => void;
  /** RW1c: "another way" and "that didn't help…" under an answer. */
  askAnotherWay: (exchange: ReaderExchange) => void;
  askDidntHelp: (exchange: ReaderExchange, text: string) => void;
  cancelAsk: () => void;
  setInquiryStatus: (root: ReaderExchange, resolution: InquiryResolution, trigger?: "chip" | "key") => Promise<void>;
  markBranchDone: (branch: ReaderExchange) => Promise<void>;
  commitInquiry: (root: ReaderExchange, preset: InquiryCommitment) => Promise<void>;
  committedFor: (root: ReaderExchange) => Set<InquiryCommitment>;
  /** Open an inquiry named elsewhere (the recap card, Wrap up). */
  openInquiry: (rootId: string, fallbackSpanId?: string | null) => void;
  startQuickCheck: (rootId: string, via: "inline" | "rail") => Promise<void>;
  cancelQuickCheck: (rootId: string) => void;
  dismissInquiryCheck: (rootId: string) => void;
  answerReconnect: (answer: "yes" | "still_unclear" | "quick_check", text?: string) => Promise<void>;
  inquiryCheckAction: (rootId: string, action: "answered" | "self_checked" | "dismissed", value?: string) => Promise<void>;
  escalateInquiryCheck: (rootId: string) => Promise<void>;
  /** "Mixtures ¶3": the passage's guide section and its place in it. */
  passageLabel: (spanId: string | null) => string;
  /** A peek at a passage the Ask rail points to (show passage, a citation). */
  peekPassage: (spanId: string) => void;
  /** Walk the stack to an entry: restore its passage, selection and tab. */
  restoreEntry: (next: ReturnStack, target: ReturnEntry, via: string) => Promise<void>;
  /** Scrolling the source (reading position, the visit, the RW1a ends). */
  onBodyScroll: () => void;
  /** openSource: a detour from the source left a moment ago, or reading. */
  noteSourceOpened: (card: SourceLibraryCard, extractionId: string, jumpSpan: string | undefined, via: "search" | "restore" | undefined) => void;
  /** backToLibrary: where the learner was, so a search hit opened next is a detour. */
  rememberLeftSource: (entry: ReturnEntry) => void;
  /** Per-source reset (the return stack itself survives a detour into another source). */
  resetInquiryState: () => void;
  /** Reader CA6: push side by side's crumb from the reading position, carrying
   *  its second pane; its entry id (null: no return stack). */
  pushSideBySide: (label: string, target: PaneTarget) => string | null;
  /** Reader CA6: another section opened beside the same passage: the current
   *  crumb now names it (same entry id); false when it is not the current entry. */
  replaceSideBySide: (entryId: string, label: string, target: PaneTarget) => boolean;
  /** Reader CA6b (final verify F8): side by side's crumb, while it is the
   *  current entry, takes the pair as it is now (the second pane's section
   *  and passage) and the main pane's passage now; false when it is not. */
  snapshotSideBySide: (label: string, target: PaneTarget) => boolean;
  /** Reader CA6: the learner closed side by side; its crumb goes if it is the current entry (nothing moves). */
  dropDetour: (entryId: string) => void;
}

export function useReaderInquiry(input: ReaderInquiryInput): ReaderInquiry {
  const {
    render, offline, inquiry, muted, library, sourceTitle, selection, setSelection, setSelectionActions,
    activeSpan, railTab, setRailTab, answerMode, setBusy, onError, annotations, refreshAnnotations, setArc,
    visit, readingSpan, guideSectionBySpan, jumpToSpan, onReadingScroll, jumpGuardRef, bodyRef,
    askComposerRef, openSourceRef, onRestored, workbenchSessionRef, personalizedRef, composerAnchorRef,
  } = input;
  const { visitPayload, touchVisit, noteBackToReading, noteUsableResult } = visit;
  const [question, setQuestion] = useState("");
  const [askComposerVersion, setAskComposerVersion] = useState(0);
  // RW1a branches: the exchange a follow-up continues (null starts a new root).
  const [parentExchange, setParentExchange] = useState<ReaderExchange | null>(null);
  const askEpoch = useRef(0);
  const askPending = useRef(false);
  useEffect(() => () => { askEpoch.current += 1; }, []);
  const [history, setHistory] = useState<ReaderExchange[]>([]);
  // Reader CA6b (Codex review F1): an inquiry about the book beside lives in
  // that book's history, so its status, checks and reconnect answers name
  // that reading (the sidecar refuses an exchange under another reading).
  const historyRef = useRef(history);
  historyRef.current = history;
  const [collapsedAskIds, setCollapsedAskIds] = useState<Set<string>>(new Set());
  const [askFindOpen, setAskFindOpen] = useState(false);
  const [askFindQuery, setAskFindQuery] = useState("");
  const askFindInputRef = useRef<HTMLInputElement | null>(null);
  // RW1a (reader_inquiry): the return stack and its detour strip; the
  // reconnect line; each inquiry's passage-scoped quick check; the root
  // commitments made from the status chips; a static "•" on the Ask tab
  // when something lands there while the learner is elsewhere.
  const [returnStack, setReturnStack] = useState<ReturnStack>(EMPTY_STACK);
  const returnStackRef = useRef<ReturnStack>(EMPTY_STACK);
  returnStackRef.current = returnStack;
  const lastSourceRef = useRef<ReturnEntry | null>(null);
  // The switch, readable from the stable callbacks openSource calls.
  const inquiryRef = useRef(false);
  inquiryRef.current = inquiry;
  const settleScrollRef = useRef<number | null>(null);
  const [reconnect, setReconnect] = useState<ReconnectState | null>(null);
  // Scroll baselines for "a screen of scrolling" (the reconnect line goes, a
  // walked-back detour settles).
  const reconnectBaseRef = useRef(0);
  const [inquiryChecks, setInquiryChecks] = useState<Record<string, InquiryCheckState>>({});
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

  // Reader CA6b (Codex review F3): the request that just failed, so "try
  // again" asks it with the same grounding -- its parent, its anchor (the
  // book beside's passage) and its routed answer mode -- whatever the open
  // book's selection is now. It is the failed request of THIS source and
  // composer only (Codex re-review F10): a source reset or a new composer
  // forgets it.
  const failedAskRef = useRef<{ asked: string; parent: ReaderExchange | null; override?: AskOverride } | null>(null);
  // The composer's generation (final verify F10): every new composer, source
  // reset, selection or thread is a new retry generation. A request
  // remembers the generation it was asked from, and its failure may leave a
  // retry only while that generation is still the current one, so a failure
  // landing after a new composer opened never gives that composer its
  // grounding.
  const composerGenRef = useRef(0);
  // Fix round 4 (verify finding 4): the composer itself -- a new composer (the
  // second pane's, or back to the open book's) or a source reset, not a
  // selection or thread change. A request's answer becomes the thread to
  // follow up, and empties the box, only while the composer it was asked
  // from is still the one open; a late answer after a new composer opened
  // goes into history and leaves that composer's thread and draft alone.
  const composerOpenRef = useRef(0);
  const resetInquiryState = useCallback(() => {
    askEpoch.current += 1;
    askPending.current = false;
    failedAskRef.current = null;
    composerGenRef.current += 1;
    composerOpenRef.current += 1;
    setParentExchange(null);
    setQuestion("");
    setAskComposerVersion(0);
    setHistory([]);
    setCollapsedAskIds(new Set());
    setAskFindOpen(false);
    setAskFindQuery("");
    // RW1a per-source state. The return stack itself survives a detour into
    // another source; openSource decides whether it continues or resets.
    setReconnect(null);
    setInquiryChecks({});
    // A check still being written goes on in the background; its wait ends
    // with the source (no outcome is recorded for a wait nobody watched).
    inquiryJobsRef.current = {};
    setInquiryCommitments({});
    setAskTabMarked(false);
    settleScrollRef.current = null;
  }, []);

  const noteSourceOpened = useCallback((
    card: SourceLibraryCard,
    extractionId: string,
    jumpSpan: string | undefined,
    via: "search" | "restore" | undefined,
  ) => {
    // RW1a (reader_inquiry on): opening another source after leaving one
    // -- a search hit or its library card -- is a detour from the passage
    // left a moment ago (Alt+← goes back to it); a restore walks the stack.
    // Reopening the same source, or the first open of a visit, is reading.
    // Switched off there is no return stack at all (F5).
    const left = lastSourceRef.current;
    if (inquiryRef.current && via !== "restore" && left && left.sourceId !== card.sourceId) {
      const entry: ReturnEntry = {
        id: newActivityId(), kind: "source", sourceId: card.sourceId, sourceTitle: card.title,
        extractionId, spanId: jumpSpan ?? null, selection: null, railTab: "guide",
        exchangeId: null, label: card.title, openedAt: Date.now(),
      };
      const next = pushDetour(returnStackRef.current, left, entry);
      returnStackRef.current = next;
      setReturnStack(next);
      logReaderAction("detour_opened", {
        detour_id: entry.id, detour_kind: "source", origin_span_id: left.spanId,
        target_span_id: entry.spanId, depth: next.entries.length - 1,
        via: via === "search" ? "search" : "library",
      });
    } else if (via !== "restore") {
      returnStackRef.current = EMPTY_STACK;
      setReturnStack(EMPTY_STACK);
    }
    lastSourceRef.current = null;
  }, []);

  const rememberLeftSource = useCallback((entry: ReturnEntry) => {
    lastSourceRef.current = entry;
  }, []);

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
          // RW1c: the answer's modes (absent on exchanges before RW1c).
          ...(exchange.tutor ? { tutor: exchange.tutor } : {}),
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

  useEffect(() => {
    if (!render || offline || !readingSpan) return;
    // RW1a: while a detour is open, the saved position stays at its root --
    // "where I was" -- so a restart restores the root and nothing else (the
    // return stack is visit state, P3 §12).
    const root = inquiry && hasDetour(returnStack) ? returnStack.entries[0] : null;
    const saved = root && root.sourceId === render.sourceId && root.spanId ? root.spanId : readingSpan;
    try {
      // The reading travels with the place (re-read safety).
      window.localStorage.setItem(readingPositionKey(render.sourceId), encodeReadingPlace(render.extractionId, saved));
    } catch {
      /* Reading-position persistence is best-effort. */
    }
  }, [inquiry, render, offline, readingSpan, returnStack]);

  // ── RW1a: the return stack, detours and the reconnect line ─────────────────

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

  const pushSideBySide = useCallback((label: string, target: PaneTarget): string | null => {
    if (!inquiry || offline || !render) return null;
    const entry: ReturnEntry = {
      id: newActivityId(), kind: "side_by_side", sourceId: render.sourceId, sourceTitle,
      extractionId: render.extractionId, spanId: readingSpan ?? activeSpan, selection: null, railTab,
      exchangeId: null, label, openedAt: Date.now(), sideBySide: target,
    };
    const before = returnStackRef.current;
    pushDetours([entry]);
    return returnStackRef.current !== before ? entry.id : null;
  }, [inquiry, offline, render, sourceTitle, readingSpan, activeSpan, railTab, pushDetours]);

  const replaceSideBySide = useCallback((entryId: string, label: string, target: PaneTarget): boolean => {
    const next = replaceCurrent(returnStackRef.current, entryId, { label, sideBySide: target });
    if (next === returnStackRef.current) return false;
    returnStackRef.current = next;
    setReturnStack(next);
    return true;
  }, []);

  /** Reader CA6b (final verify F8): the crumb as side by side is now, just
   *  before a handoff leaves it (check me, work through). The pair in the
   *  crumb was the one first opened or replaced: moving the second pane
   *  (by hand or follow along) or reading on in the main pane did not change
   *  it, so walking back would have reopened where side by side began. */
  const snapshotSideBySide = useCallback((label: string, target: PaneTarget): boolean => {
    const stack = returnStackRef.current;
    const current = stack.entries[stack.cursor];
    if (!current || current.kind !== "side_by_side") return false;
    const next = replaceCurrent(stack, current.id, { label, sideBySide: target, spanId: readingSpan ?? activeSpan ?? current.spanId });
    if (next === stack) return false;
    returnStackRef.current = next;
    setReturnStack(next);
    return true;
  }, [readingSpan, activeSpan]);

  /** Reader CA6b (Codex re-review F8): the trail back to side by side the
   *  Reader was handed when it opened again (besideTrail), as the stack. */
  const seedReturnStack = useCallback((stack: ReturnStack) => {
    if (!inquiry) return;
    returnStackRef.current = stack;
    setReturnStack(stack);
  }, [inquiry]);

  const dropDetour = useCallback((entryId: string) => {
    const next = dropCurrent(returnStackRef.current, entryId);
    if (next === returnStackRef.current) return;
    returnStackRef.current = next;
    setReturnStack(next);
  }, []);

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
  }, [inquiry, muted, inquiryRoot, visitPayload, bodyRef]);

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
      const openSource = openSourceRef.current;
      if (card && openSource) {
        await openSource(card, target.spanId ?? undefined, { via: "restore", jumpReading: target.extractionId });
      }
    } else if (target.spanId) {
      jumpToSpan(target.spanId);
    }
    onRestored?.(target.spanId);
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
  }, [render, library, openSourceRef, jumpToSpan, visitPayload, offline, showReconnect, jumpGuardRef,
    setSelection, setSelectionActions, setRailTab, bodyRef, onRestored]);

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
  }, [onReadingScroll, touchVisit, noteBackToReading, reconnect, bodyRef, jumpGuardRef]);

  useEffect(() => {
    if (railTab === "ask") setAskTabMarked(false);
  }, [railTab]);

  // Alt+← / Alt+→ walk the return stack (UX §3.5; K7 keeps the capture).
  useEffect(() => {
    if (!inquiry || !render) return;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
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

  // Ask (and, with reader_inquiry on, a follow-up in a branch). The learner's
  // words stay in the composer until the answer lands; a failure keeps them.
  const [askPhase, setAskPhase] = useState<ModelActionPhase>("idle");
  const askJobRef = useRef<{ jobId: string; kind: string; startedAt: number; activity: ReturnType<typeof learnerActivitySnapshot> } | null>(null);
  const submitAsk = useCallback(async (
    asked: string,
    parent: ReaderExchange | null,
    // RW1b: a routed Ask runs in its routed answer mode, and its funnel event
    // names the intention and the entry (the intent box or its palette).
    override?: AskOverride,
  ) => {
    // A follow-up keeps its saved anchor even when the current selection moves.
    // New roots use the capture selection (the same selection Notes>Capture
    // acts on), then the jump/resume fallback.
    // Reader CA6b: a new root asked in the second pane is anchored there (its
    // book and selection); a follow-up keeps the book its thread was about.
    const anchor = parent ? null : override?.anchor ?? null;
    const about = parent ? parent.about ?? null : anchor?.about ?? null;
    const groundingSpan = parent?.spanId ?? anchor?.spanId ?? selection?.spanId ?? activeSpan;
    if (!groundingSpan || !asked || !render || askPending.current) return;
    if (inquiry && offline) return;
    const epoch = askEpoch.current;
    const composer = composerGenRef.current;
    const composerOpen = composerOpenRef.current;
    askPending.current = true;
    failedAskRef.current = null;
    // The full capture selection widens the tutor's citable context to every
    // selected block, not just the primary one; a follow-up inherits its
    // parent's saved selection instead.
    const selectionSpanIds = parent
      ? parent.selectionSpanIds
      : anchor ? anchor.selectionSpanIds
      : selection ? [...new Set(selectionNodes(selection).map((n) => n.spanId))] : [];
    const selectionQuote = parent
      ? parent.selectionQuoteMd
      : anchor ? anchor.selectionQuote
      : selection ? (selection.editedText ?? selection.quote).trim() || null : null;
    // An edited capture is the learner's wording: the source's own is sent
    // beside it (reader_inquiry on), so history never shows it as the book's.
    const edited = !parent && !anchor && selection?.editedText != null && selection.editedText.trim() !== selection.quote.trim();
    const selectionSourceQuote = parent
      ? parent.selectionSourceQuoteMd ?? null
      : edited && selection ? selection.quote.trim() || null : null;
    const jobKind = parent ? "follow_up" : "ask";
    const job = { jobId: newActivityId(), kind: jobKind, startedAt: Date.now(), activity: learnerActivitySnapshot() };
    askJobRef.current = job;
    logReaderAction("action_invoked", { ...visitPayload(), action_kind: jobKind, ...(override?.meta ?? {}) });
    logReaderActivity({ kind: "reader_job_queued", payload: { ...visitPayload(), job_id: job.jobId, job_kind: jobKind } });
    setBusy(true);
    if (inquiry) setAskPhase("pending");
    try {
      const answer = await api.readerAsk({
        extractionId: about?.extractionId ?? render.extractionId,
        spanId: groundingSpan,
        question: asked,
        ...(inquiry ? { parentExchangeId: parent?.id ?? null } : {}),
        answerMode: override?.answerMode ?? answerMode,
        selectionSpanIds,
        selectionQuote,
        ...(inquiry && selectionSourceQuote ? { selectionSourceQuote } : {}),
        // RW1c: inside a bound workbench session the retrieval reads as its item's practice.
        ...(workbenchSessionRef?.current ? { workbenchSessionId: workbenchSessionRef.current } : {}),
        // RW1c (Codex review F8): the visible personalized chip, for every
        // question and follow-up (another way and that didn't help included).
        ...(personalizedRef && personalizedRef.current !== null ? { personalized: personalizedRef.current } : {}),
        // RW1c: "another way" / "that didn't help" (only sent from their buttons).
        ...(override?.retrievalIntent && override.retrievalIntent !== "explain"
          ? { retrievalIntent: override.retrievalIntent } : {}),
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
      noteUsableResult(job.jobId, jobKind);
      const exchange: ReaderExchange = {
        id: answer.readerAnswerEventId,
        parentExchangeId: answer.parentExchangeId ?? null,
        extractionId: about?.extractionId ?? render.extractionId,
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
        // RW1c: the answer's modes and, while offers are on, its offers (this visit only).
        ...(answer.tutor ? { tutor: answer.tutor } : {}),
        ...(answer.tutorOffers ? {
          offers: {
            practiceRequest: answer.practiceRequest ?? null,
            toolRequests: answer.toolRequests ?? [],
            buttons: answer.tutorOffers.buttons ?? [],
          },
        } : {}),
        ...(about ? { about } : {}),
      };
      // Fix round 4 (finding 4): still the composer it was asked from?
      const ownComposer = composerOpen === composerOpenRef.current;
      if (inquiry) {
        if (ownComposer) setParentExchange(exchange);
        setAskPhase("idle");
        if (railTab !== "ask") setAskTabMarked(true);
        // A thread about the book beside (CA6b) is no detour of the open book's.
        if (parent && !about) {
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
      // A late answer (another composer open now): in history, and nothing else.
      if (!ownComposer) return;
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
        // The learner's words stay in the composer for "try again", which
        // asks them with this request's grounding (Codex review F3).
        // Not into another composer opened meanwhile (fix round 4): its draft is its own.
        if (inquiry && asked !== question.trim() && composerOpen === composerOpenRef.current) setQuestion(asked);
        // Only while the composer it was asked from is still the one open
        // (final verify F10): otherwise ↵ and "try again" ask afresh there.
        if (composer === composerGenRef.current) failedAskRef.current = { asked, parent, ...(override ? { override } : {}) };
      }
    } finally {
      if (epoch === askEpoch.current) {
        askPending.current = false;
        setBusy(false);
      }
      if (askJobRef.current === job) askJobRef.current = null;
    }
  }, [inquiry, selection, activeSpan, answerMode, render, offline, onError, visitPayload, railTab, sourceTitle,
    pushDetours, question, setBusy, noteUsableResult, askComposerRef]);

  const ask = useCallback(() => {
    // ↵ on the words that just failed (still in the composer): the same
    // request (Codex review F3), while that failure is still this source's
    // and this composer's (re-review F10).
    const failed = failedAskRef.current;
    if (failed && failed.asked === question.trim()) {
      void submitAsk(failed.asked, failed.parent, failed.override);
      return;
    }
    // Reader CA6b: a new question from the composer the second pane opened is about that pane's selection.
    const anchor = composerAnchorRef?.current ?? null;
    if (anchor && !(inquiry && parentExchange)) {
      void submitAsk(question.trim(), null, { anchor });
      return;
    }
    void submitAsk(question.trim(), inquiry ? parentExchange : null);
  }, [submitAsk, question, inquiry, parentExchange, composerAnchorRef]);

  /** "try again": the request that failed, explicitly (re-review F10); with none, an ordinary ask. */
  const retryAsk = useCallback(() => {
    const failed = failedAskRef.current;
    if (failed) {
      void submitAsk(failed.asked, failed.parent, failed.override);
      return;
    }
    ask();
  }, [submitAsk, ask]);
  /** A new composer (the second pane's, or back to the open book's): the failed request is not its own. */
  const forgetFailedAsk = useCallback(() => {
    failedAskRef.current = null;
    composerGenRef.current += 1;
    composerOpenRef.current += 1;
  }, []);

  // Another selection or thread: "try again" is no longer that request.
  useEffect(() => {
    failedAskRef.current = null;
    composerGenRef.current += 1;
  }, [selection, parentExchange]);

  /** RW1c: "another way" under an answer -- a follow-up that retrieves with
   *  intent alternative, every passage the inquiry showed excluded (server-side). */
  const askAnotherWay = useCallback((exchange: ReaderExchange) => {
    void submitAsk(TUTOR_COPY.anotherWayQuestion, exchange, {
      retrievalIntent: "alternative", meta: { action_kind: "tutor_another_way" },
    });
  }, [submitAsk]);

  /** RW1c: "that didn't help…" -- its text (optional) starts a branch that
   *  retrieves with intent remediate for the inquiry's named gaps. */
  const askDidntHelp = useCallback((exchange: ReaderExchange, text: string) => {
    void submitAsk(text || TUTOR_COPY.didntHelpDefault, exchange, {
      retrievalIntent: "remediate", meta: { action_kind: "tutor_didnt_help" },
    });
  }, [submitAsk]);

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
  }, [visitPayload, setBusy]);

  // ── RW1a: inquiry status, reconnect answers and the passage quick check ───

  /** The reading an inquiry was asked in (the book beside's, for a thread about it). */
  const extractionOf = useCallback((rootId: string): string => (
    historyRef.current.find((item) => item.id === rootId)?.extractionId || render?.extractionId || ""
  ), [render]);

  const updateExchange = useCallback((id: string, patch: Partial<ReaderExchange>) => {
    setHistory((items) => items.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }, []);

  const setInquiryStatus = useCallback(async (root: ReaderExchange, resolution: InquiryResolution, trigger: "chip" | "key" = "chip") => {
    if (!render || offline) return;
    try {
      const result = await api.readerSetInquiryStatus({ extractionId: root.extractionId || render.extractionId, exchangeId: root.id, resolution, trigger });
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

  // One commitment per inquiry and preset, whichever surface asks (the Ask
  // chip, the recap card, Wrap up; RW6a review F2): a request in flight
  // refuses a second, and a retry after an uncertain result reuses its key so
  // the server keeps one commitment.
  const commitPendingRef = useRef<Set<string>>(new Set());
  const commitKeysRef = useRef<Record<string, string>>({});

  /** "revisit once" / "make it something I can do": the existing test_me_later
   *  and help_me_remember presets on the root's anchor (no new status words). */
  const commitInquiry = useCallback(async (root: ReaderExchange, preset: InquiryCommitment) => {
    if (!render || offline) return;
    const slot = `${root.id}:${preset}`;
    if (commitPendingRef.current.has(slot) || committedFor(root).has(preset)) return;
    commitPendingRef.current.add(slot);
    const key = commitKeysRef.current[slot] ?? (commitKeysRef.current[slot] = newKey());
    const spanIds = root.selectionSpanIds.length ? root.selectionSpanIds : [root.spanId];
    // Reader CA6b (Codex review F1): a thread about the book beside commits
    // on that book, its revision and reading, never the open one's.
    const about = root.about ?? null;
    if (about && !about.revisionId) {
      onError("That book's passage can't be kept from here; open the book to keep it.");
      return;
    }
    try {
      const receipt = await api.readerInvokePreset({
        preset,
        sourceId: about ? about.sourceId : render.sourceId,
        revisionId: about ? about.revisionId as string : render.revisionId,
        extractionId: about ? about.extractionId : render.extractionId,
        clientIdempotencyKey: key,
        renderViewId: about ? null : render.renderViewId,
        rawSelection: { extractionId: about ? about.extractionId : render.extractionId,
          nodes: spanIds.map((spanId) => ({ spanId, start: 0, end: 1_000_000 })) },
        learnerText: "",
        subjectId: root.spanId,
      });
      delete commitKeysRef.current[slot];
      setInquiryCommitments((done) => ({ ...done, [root.id]: [...new Set([...(done[root.id] ?? []), preset])] }));
      if (receipt.arc) setArc(receipt.arc);
      logReaderAction("action_invoked", {
        ...visitPayload(), action_kind: `inquiry:${preset}`,
        ...(about ? { target_source_id: about.sourceId, target_extraction_id: about.extractionId } : {}),
      });
      if (!about) void refreshAnnotations();
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      commitPendingRef.current.delete(slot);
    }
  }, [render, offline, committedFor, visitPayload, refreshAnnotations, onError, setArc]);

  /** "open" on an inquiry named elsewhere (the recap card, Wrap up; RW6a
   *  review F5): the Ask rail with that inquiry expanded and in view, any find
   *  filter that could hide it cleared, its passage shown, and a crumb on the
   *  detour strip for the way back. An id not in this source's history falls
   *  back to a peek at the passage. */
  const openInquiry = useCallback((rootId: string, fallbackSpanId?: string | null) => {
    const root = history.find((exchange) => exchange.id === rootId) ?? null;
    if (!root || !render) {
      if (fallbackSpanId) peekPassage(fallbackSpanId);
      return;
    }
    setAskFindQuery("");
    setAskFindOpen(false);
    setCollapsedAskIds((ids) => {
      if (!ids.has(root.id)) return ids;
      const next = new Set(ids);
      next.delete(root.id);
      return next;
    });
    pushDetours([{
      id: newActivityId(), kind: "branch", sourceId: render.sourceId, sourceTitle,
      extractionId: render.extractionId, spanId: root.spanId, selection: null, railTab: "ask",
      exchangeId: root.id, label: clip(root.question, 48), openedAt: Date.now(),
    }]);
    jumpToSpan(root.spanId);
    setRailTab("ask");
    setAskTabMarked(false);
    window.requestAnimationFrame(() => {
      const card = Array.from(document.querySelectorAll<HTMLElement>("[data-ask-id]")).find(
        (element) => element.dataset.askId === root.id,
      );
      card?.scrollIntoView?.({ block: "start" });
    });
  }, [history, render, peekPassage, pushDetours, sourceTitle, jumpToSpan, setRailTab]);

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
    const visitIds = visitPayload();
    const startedAt = Date.now();
    const activity = learnerActivitySnapshot();
    try {
      const result = await api.readerReconnectAnswer({ extractionId: extractionOf(rootId), exchangeId: rootId, answer: "quick_check", via });
      if (result.question) {
        // Written earlier: it lands at once, with no wait and no model call.
        setInquiryChecks((checks) => ({ ...checks, [rootId]: { phase: "landed", question: result.question } }));
      } else if (result.status === "queued" && result.batchId) {
        const batchId = result.batchId;
        const tracked = inquiryJobsRef.current[rootId];
        if (!tracked || tracked.batchId !== batchId) {
          inquiryJobsRef.current[rootId] = { batchId, waitId, startedAt, activity, visit: visitIds };
          logReaderActivity({ kind: "reader_job_queued", payload: { ...visitIds, job_id: batchId, job_kind: "quick_check" } });
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
  }, [render, offline, visitPayload, recordUnqueuedCheck, extractionOf]);

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

  /** Put away a check that never landed (the learner's "not now"). */
  const dismissInquiryCheck = useCallback((rootId: string) => {
    setInquiryChecks((checks) => {
      const { [rootId]: _dropped, ...rest } = checks;
      return rest;
    });
  }, []);

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
      const result = await api.readerReconnectAnswer({ extractionId: extractionOf(line.rootId), exchangeId: line.rootId, answer, via });
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
  }, [reconnect, render, offline, railTab, startQuickCheck, updateExchange, onError, history, submitAsk, setRailTab, extractionOf]);

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
        void api.readerInquiryQuestion({ extractionId: extractionOf(rootId), exchangeId: rootId, batchId })
          .then((result) => {
            const job = result.job ?? null;
            if (result.question) {
              const landedQuestion = result.question;
              settleInquiryJob(rootId, batchId, waitId, "completed", { model: landedQuestion.model ?? null, promptVersion: landedQuestion.promptVersion ?? null });
              setInquiryChecks((checks) => (same(checks) ? { ...checks, [rootId]: { phase: "landed", question: landedQuestion } } : checks));
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
  }, [render, offline, inquiryChecks, settleInquiryJob, extractionOf]);

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
      if (screenLeavesKey(event, { ownChords: true })) return;
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

  return {
    question, setQuestion, askComposerVersion, parentExchange, setParentExchange, history, visibleAskHistory,
    normalizedAskFind, collapsedAskIds, setCollapsedAskIds, askFindOpen, setAskFindOpen, askFindQuery,
    setAskFindQuery, askFindInputRef, askPhase, askTabMarked, returnStack, returnStackRef, reconnect,
    inquiryChecks, passageCheckOffered, submitAsk, ask, retryAsk, forgetFailedAsk, seedReturnStack, askAnotherWay, askDidntHelp, cancelAsk, setInquiryStatus,
    markBranchDone,
    commitInquiry, committedFor, openInquiry, startQuickCheck, cancelQuickCheck, dismissInquiryCheck, answerReconnect,
    inquiryCheckAction, escalateInquiryCheck, passageLabel, peekPassage, restoreEntry, onBodyScroll,
    noteSourceOpened, rememberLeftSource, resetInquiryState, pushSideBySide, replaceSideBySide, snapshotSideBySide, dropDetour,
  };
}
