import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  AnswerMode,
  AskTutorQuestionInput,
  AttemptProgress,
  EarlierThreadDto,
  CommandError,
  LearnerGapQueuedDto,
  LearnerTextGapReversal,
  LearnerTextGapViewDto,
  PromotionIntent,
  QuestionPromotionDto,
  PracticeRequestDto,
  QuestionPromotionRequestDto,
  SourceToolRequestDto,
  SuggestedLearningObjectDto,
  TutorCitationDto,
  TutorQuestionContext,
  TutorQuestionEventDto
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, type PillColor } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";
import { OpenInSource } from "./OpenInSource";
import { notifyQueueChanged } from "../queueEvents";
import { suggestionLine } from "./askSuggestions";
import { SourceOffers } from "./SourceOffers";
import { screenLeavesKey } from "../app/keymap";
import { algoConfig } from "../app/algoConfig";
import {
  ANSWER_MODE_LABEL,
  ASK_COPY,
  ONE_QUESTION_MODES,
  STYLE_ANSWER_MODE,
  StoredHelpStyle,
  answerCountLabel,
  shortDate,
  useStoredHelpStyle
} from "./askPanel";

/**
 * The Reader exchange a continued dialogue attaches to, when the sidecar
 * reports branches (reader_inquiry on: its history carries question ids):
 * the exchange of the question the learner chose (``questionEventId``), so the
 * follow-up inherits that inquiry's saved selection and ancestors and never a
 * sibling's; without a chosen question, the span's newest exchange. Null when
 * branches are off (the Ask goes out exactly as before) or the chosen
 * question has no exchange on this source (a new thread on the span).
 */
async function readerThreadParent(extractionId: string, spanId: string, questionEventId?: string): Promise<string | null> {
  try {
    const history = (api as { readerAskHistory?: (id: string) => Promise<{ exchanges: Array<{ eventId: string; spanId: string; questionEventId?: string | null }> }> }).readerAskHistory;
    if (typeof history !== "function") return null;
    const { exchanges } = await history(extractionId);
    if (!exchanges.some((exchange) => exchange.questionEventId !== undefined)) return null;
    if (questionEventId) {
      return exchanges.find((exchange) => exchange.questionEventId === questionEventId)?.eventId ?? null;
    }
    return exchanges.find((exchange) => exchange.spanId === spanId)?.eventId ?? null;
  } catch {
    return null;
  }
}

export interface AskTarget {
  initialQuestion?: string;
  captureId?: string;
  subjectId?: string;
  context: TutorQuestionContext;
  practiceItemId?: string;
  attemptId?: string;
  noteId?: string;
  sessionId?: string;
  /** Reader threads stay anchored to the exact canonical source span. */
  extractionId?: string;
  spanId?: string;
  /** The reader question the learner chose to continue (its question event
   *  id): its own exchange is the follow-up's parent (RW1a). */
  readerQuestionEventId?: string;
  /** Date.now() when the practice item was opened (practice context only). */
  openedAtMs?: number;
  /** Practice context only: whether the learner had started an answer when
   *  the overlay opened (it is modal, so the draft cannot change while open). */
  attemptProgress?: AttemptProgress;
  /** §12.1: open with the tutor's persisted typed move before the learner
   *  types anything (diagnostic block just routed to tutoring). */
  proactiveOpen?: boolean;
  /** Practice context: the learner's current draft, for "Explain this with
   *  my work" (canonical sources S4). */
  draftMd?: string;
  /** Practice context, in "Work in steps" (owner capture 2026-10-25, B1):
   *  the steps as the learner's work, sent with every question so the tutor
   *  sees what the answer box would have shown it. */
  workMd?: string;
  /** Reader CA2 (K5): the attempt's key; the thread is the attempt's. */
  submissionId?: string;
  /** Reader CA2 (K7, §7.6): asked from Work in Steps, in this workbench
   *  session (the server checks it is the item's), about this step. */
  workbenchSessionId?: string;
  aboutStep?: number;
  /** The steps written so far ("your steps 1–N" on the context line). */
  stepsCount?: number;
  /** Reader CA2 (§7.2): the learner's live draft at send (the answer box or
   *  the steps), read when the question goes, never when the panel opened. */
  readDraft?: () => string;
  /** The question as the context line names it ("Exercise 6.1.12"), or none. */
  itemLabel?: string;
  /** The practice screen serves this as a check on your own (§7.7). */
  coldCheck?: boolean;
}

/** Reader CA2: where the one Ask panel sits (§7.1). "modal" is the overlay
 *  every other context keeps; "docked" sits beside the question on the
 *  practice and feedback screens; "inline" sits under a workbench step. */
export type AskVariant = "modal" | "docked" | "inline";

const CONTEXT_PILL: Record<TutorQuestionContext, PillColor> = {
  library: "cyan",
  practice: "amber",
  feedback: "green",
  reader: "purple"
};

interface ThreadEntry {
  eventId: string | null;
  questionMd: string;
  answerMd: string | null;
  questionType: string | null;
  hintEquivalent: boolean;
  rating: number | null;
  /** Persisted server-side (question_events.saved_note_id, migration 027); survives remount. */
  savedNoteId: string | null;
  /** Persisted promotion ledger row (question_promotions); survives remount (spec §2 idempotency). */
  promotion: QuestionPromotionDto | null;
  promotionRequest: QuestionPromotionRequestDto | null;
  /** §12.1 proactive handoff: a tutor-initiated turn with no learner question.
   *  Ephemeral — never persisted, so it carries no eventId/rate/save/promote. */
  opening?: boolean;
  /** ING M8 (§9.2): source-span citations on the live answer; chips open the
   *  Open-in-source viewer. Ephemeral — absent on transcript-reloaded turns. */
  citations?: TutorCitationDto[];
  /** Slice 2 T6: labelled nearest-LO suggestions for a reader span without
   *  provenance. Ephemeral, like citations. */
  suggestions?: SuggestedLearningObjectDto[];
  /** Learner-text gaps: what the question was read as, once the worker ran
   *  (only a label for something that actually happened), with one-tap undo. */
  gap?: LearnerTextGapViewDto | null;
  /** Canonical sources S0/S4: the answer's offers (practice, passages,
   *  comparison). Ephemeral, like citations. */
  practiceRequest?: PracticeRequestDto | null;
  toolRequests?: SourceToolRequestDto[];
  /** Reader CA2: the mode the answer was written in (live answers only). */
  answerMode?: AnswerMode | null;
  /** Reader CA2 (§7.6): asked from this panel. */
  local?: boolean;
  /** Codex review F5: the workbench and step the question was asked about,
   *  as stored (``sourceContext.attemptKey``), so an inline panel under a
   *  step shows that step's exchanges after a close, a remount or a restart. */
  workbenchSessionId?: string | null;
  aboutStep?: number | null;
  /** Codex review F2 (K9): the answer was worked help, withheld; the take step. */
  takeOffer?: { levels: number[] } | null;
}

/** Codex review F5, F9: what a stored question event restores (its step,
 *  its citations with their excerpts, its mode, a withheld answer's take step). */
function restoredEntryFields(event: TutorQuestionEventDto): Partial<ThreadEntry> {
  const context = (event.sourceContext ?? {}) as {
    attemptKey?: { workbenchSessionId?: string; aboutStep?: number };
    citations?: TutorCitationDto[];
    withheld?: { reason?: string; takeLevels?: number[] };
  };
  return {
    workbenchSessionId: context.attemptKey?.workbenchSessionId ?? null,
    aboutStep: context.attemptKey?.aboutStep ?? null,
    citations: context.citations ?? [],
    answerMode: (event.answerMode ?? null) as AnswerMode | null,
    takeOffer: context.withheld?.reason === "worked_help" ? { levels: context.withheld.takeLevels ?? [4, 5] } : null
  };
}

/** How long the overlay waits for a question's gap reading (polls). */
const GAP_POLL_MS = 2000;
const GAP_POLL_LIMIT = 45;

const REVERSAL_LABEL: Record<LearnerTextGapReversal, string> = {
  undo_edge: "undo",
  undo_creation: "undo",
  not_this_belief: "not what I meant"
};

interface SaveNotice {
  eventId: string;
  message: string;
}

/** Result-chip label per route (spec_tutor_promotion.md §2). */
function promotionChipLabel(promotion: QuestionPromotionDto): string {
  switch (promotion.route) {
    case "auto_apply":
      return `added: ${promotion.createdPracticeItemId ?? promotion.createdLearningObjectId ?? "?"}`;
    case "review_required":
      return promotion.proposedPatchId
        ? `queued for review (patch ${promotion.proposedPatchId})`
        : "queued for review";
    case "diagnostic_pending":
      return "gap filed";
    case "existing_item":
      return `ready: ${promotion.existingPracticeItemId ?? "?"}`;
    default:
      return promotion.route;
  }
}

function promotionRequestLabel(request: QuestionPromotionRequestDto): string {
  if (request.status === "failed") {
    return `failed: ${request.errorMessage ?? request.errorCode ?? "unknown error"}`;
  }
  if (request.stage === "review") return "awaiting review";
  return `authoring: ${request.stage}`;
}

function entityIdOf(target: AskTarget): string {
  return target.spanId ?? target.noteId ?? target.attemptId ?? target.practiceItemId ?? "";
}

export function AskOverlay({
  target,
  onClose,
  onToast,
  onOpenPractice,
  variant = "modal",
  onAnswered,
  onEarlierOpened,
  onTakeWorked
}: {
  target: AskTarget | null;
  onClose: () => void;
  onToast: (message: string) => void;
  /** The open-list path for a picked offer while the daily plan is off; the
   *  proposal it came from rides along so opening it records its delivery. */
  onOpenPractice?: (practiceItemId: string, origin?: { proposalId: string; importId: string | null }) => void;
  /** Reader CA2: where the panel sits (default: the modal, as before). */
  variant?: AskVariant;
  /** Reader CA2 (§7.7, K8): an answer landed, with what it counted as (the
   *  host's help record and the cold banner read it). */
  onAnswered?: (answer: { eventId: string; questionMd: string; hintEquivalent: boolean; questionType: string | null }) => void;
  /** Reader CA2 (K6, Q2): the learner opened *earlier on this question*
   *  before Submit; the host counts it as one hint, once per attempt. */
  onEarlierOpened?: () => void;
  /** Codex review F2 (K9, §7.5): the host's ladder, to take worked help at
   *  rung 4 or 5 when an answer was withheld (recorded as that rung only if
   *  taken). Absent: the take step points at the host's Hint. */
  onTakeWorked?: (level: 4 | 5) => void;
}) {
  // Reader CA2: the panel's own parts render only on a panel host while the
  // sidecar sends `ask` (ask.panel_enabled); off, every host is the modal.
  const panelOn = algoConfig().ask !== null;
  const panel = panelOn && variant !== "modal";
  const helpStyle = useStoredHelpStyle();
  const [earlier, setEarlier] = useState<EarlierThreadDto[]>([]);
  const [earlierCountsAsHint, setEarlierCountsAsHint] = useState(false);
  // Codex review F1: the server's word that this attempt already opened one.
  const [earlierAlreadyOpened, setEarlierAlreadyOpened] = useState(false);
  const [serverCold, setServerCold] = useState(false);
  const [earlierOpen, setEarlierOpen] = useState(false);
  const [earlierShown, setEarlierShown] = useState<string | null>(null);
  const [sentOpen, setSentOpen] = useState(false);
  const [dropDraft, setDropDraft] = useState(false);
  const [oneMode, setOneMode] = useState<AnswerMode | null>(null);
  const [changeOpen, setChangeOpen] = useState(false);
  const [thread, setThread] = useState<ThreadEntry[]>([]);
  // ING M8 (§9.2): the citation span currently open in the source viewer.
  const [openCitation, setOpenCitation] = useState<TutorCitationDto | null>(null);
  const [remaining, setRemaining] = useState<number | null>(null);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [savingNote, setSavingNote] = useState<string | null>(null);
  const [saveNotice, setSaveNotice] = useState<SaveNotice | null>(null);
  const [promoteChoiceEventId, setPromoteChoiceEventId] = useState<string | null>(null);
  const [promotingEventId, setPromotingEventId] = useState<string | null>(null);
  const [promoteNotice, setPromoteNotice] = useState<SaveNotice | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const boxRef = useRef<HTMLTextAreaElement | null>(null);
  const saveNoticeTimerRef = useRef<number | null>(null);
  const promoteNoticeTimerRef = useRef<number | null>(null);
  const routedCaptureRef = useRef<string | null>(null);
  const captureNoteRef = useRef<string | null>(null);
  // Reader workbench RW1a: with reader_inquiry on, an Ask with no parent starts
  // a new thread that sees no earlier exchange. Continuing a reader question
  // from here continues its span's newest exchange instead (the overlay shows
  // that span's conversation), then each answer this overlay receives.
  const readerParentRef = useRef<string | null | undefined>(undefined);
  const gapTimersRef = useRef<number[]>([]);

  useEffect(
    () => () => {
      for (const timer of gapTimersRef.current) window.clearTimeout(timer);
      gapTimersRef.current = [];
    },
    [target]
  );

  function setEntryGap(eventId: string, gap: LearnerTextGapViewDto | null) {
    setThread((prev) => prev.map((entry) => (entry.eventId === eventId ? { ...entry, gap } : entry)));
  }

  function watchGap(eventId: string, queued: LearnerGapQueuedDto | undefined, attempt = 0) {
    if (queued?.status !== "queued" || attempt >= GAP_POLL_LIMIT) return;
    const timer = window.setTimeout(async () => {
      try {
        const result = await api.getLearnerTextGap({ sourceKind: "tutor_question", sourceId: eventId });
        if (result.status === "done") {
          setEntryGap(eventId, result.gap);
          if (result.gap?.label) notifyQueueChanged();
          return;
        }
        if (result.status === "pending") watchGap(eventId, queued, attempt + 1);
      } catch {
        // The answer stands without its gap reading.
      }
    }, GAP_POLL_MS);
    gapTimersRef.current.push(timer);
  }

  async function reverseGap(eventId: string, gapId: string, reversal: LearnerTextGapReversal) {
    try {
      const result = await api.reverseLearnerTextGap({ gapId, reversal });
      setEntryGap(eventId, result.gap);
      notifyQueueChanged();
    } catch (error) {
      onToast((error as CommandError).message);
    }
  }

  const open = target !== null;

  function clearSaveNoticeTimer() {
    if (saveNoticeTimerRef.current !== null) {
      window.clearTimeout(saveNoticeTimerRef.current);
      saveNoticeTimerRef.current = null;
    }
  }

  function showSaveNotice(notice: SaveNotice) {
    clearSaveNoticeTimer();
    setSaveNotice(notice);
    saveNoticeTimerRef.current = window.setTimeout(() => {
      setSaveNotice(null);
      saveNoticeTimerRef.current = null;
    }, 30_000);
  }

  function clearPromoteNoticeTimer() {
    if (promoteNoticeTimerRef.current !== null) {
      window.clearTimeout(promoteNoticeTimerRef.current);
      promoteNoticeTimerRef.current = null;
    }
  }

  function showPromoteNotice(notice: SaveNotice) {
    clearPromoteNoticeTimer();
    setPromoteNotice(notice);
    promoteNoticeTimerRef.current = window.setTimeout(() => {
      setPromoteNotice(null);
      promoteNoticeTimerRef.current = null;
    }, 8_000);
  }

  function saveNoteLabel(entry: ThreadEntry) {
    if (entry.eventId !== null && savingNote === entry.eventId) return "saving…";
    if (entry.savedNoteId) return "saved";
    return "save as note";
  }

  function canSaveNote(entry: ThreadEntry) {
    return savingNote === null && !entry.savedNoteId;
  }

  useEffect(() => {
    if (!target) return;
    let cancelled = false;
    setThread([]);
    setRemaining(null);
    setLimitReached(false);
    setInlineError(null);
    setSaveNotice(null);
    clearSaveNoticeTimer();
    setPromoteNotice(null);
    clearPromoteNoticeTimer();
    setPromoteChoiceEventId(null);
    setEarlier([]);
    setEarlierCountsAsHint(false);
    setEarlierAlreadyOpened(false);
    setServerCold(false);
    setEarlierOpen(false);
    setEarlierShown(null);
    setSentOpen(false);
    setDropDraft(false);
    setOneMode(null);
    setChangeOpen(false);
    setQuestion(target.initialQuestion ?? "");
    routedCaptureRef.current = null;
    captureNoteRef.current = null;
    readerParentRef.current = undefined;
    // A new capture has no library note yet. Do not request an unscoped
    // library transcript; the server anchors it on the first successful send.
    if (target.captureId && !target.noteId) return;
    api
      .getTutorTranscript({
        context: target.context,
        practiceItemId: target.practiceItemId,
        attemptId: target.attemptId,
        noteId: target.noteId,
        sessionId: target.sessionId,
        ...(panelOn && target.submissionId ? { submissionId: target.submissionId } : {}),
        // Codex review F6: the unfinished workbench the thread belongs to.
        ...(panelOn && target.context === "practice" && target.workbenchSessionId
          ? { workbenchSessionId: target.workbenchSessionId } : {})
      })
      .then((snapshot) => {
        if (cancelled) return;
        // Reader CA2 (K6): earlier attempts' help, never current; absent on a
        // check on your own (the server's word, and the screen's).
        setEarlier(snapshot.earlier ?? []);
        setEarlierCountsAsHint(snapshot.earlierCountsAsHint === true);
        setServerCold(snapshot.cold === true);
        setEarlierAlreadyOpened(snapshot.helpRecord?.earlierOpened === true);
        const entries: ThreadEntry[] = snapshot.events.map((event: TutorQuestionEventDto) => ({
          eventId: event.id,
          questionMd: event.questionMd,
          answerMd: event.answerMd,
          questionType: event.questionType,
          hintEquivalent: event.hintEquivalent,
          rating: event.rating,
          savedNoteId: event.savedNoteId,
          promotion: event.promotion,
          promotionRequest: event.promotionRequest ?? null,
          ...(panelOn ? restoredEntryFields(event) : {})
        }));
        setThread(entries);
        setRemaining(snapshot.remaining);
        // Codex review F8: no bound (null) on a subscription route.
        setLimitReached(snapshot.remaining !== null && snapshot.remaining <= 0);
        // §12.1 proactive handoff: greet with the persisted typed transition
        // move before the learner has to type anything. Ephemeral — never
        // merged into the persisted thread's budget/hint accounting.
        if (target.proactiveOpen && target.practiceItemId && entries.length === 0) {
          api
            .previewTutorOpening({ practiceItemId: target.practiceItemId, sessionId: target.sessionId })
            .then((opening) => {
              if (cancelled || opening.openingMd == null) return;
              setThread((prev) =>
                prev.length === 0
                  ? [
                      {
                        eventId: null,
                        questionMd: "",
                        answerMd: opening.openingMd,
                        questionType: null,
                        hintEquivalent: false,
                        rating: null,
                        savedNoteId: null,
                        promotion: null,
                        promotionRequest: null,
                        opening: true
                      }
                    ]
                  : prev
              );
            })
            .catch(() => {
              // best-effort — falls back to the ordinary empty-overlay state.
            });
        }
      })
      .catch((error: CommandError) => {
        if (!cancelled) setInlineError(error.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    target?.captureId,
    target?.initialQuestion,
    target?.context,
    target?.practiceItemId,
    target?.attemptId,
    target?.noteId,
    target?.sessionId,
    target?.extractionId,
    target?.spanId,
    target?.proactiveOpen,
    target?.submissionId,
    target?.workbenchSessionId
  ]);

  useEffect(() => clearSaveNoticeTimer, []);
  useEffect(() => clearPromoteNoticeTimer, []);

  useEffect(() => {
    if (!open || variant !== "modal") return;
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { modal: true })) return;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open, onClose, variant]);

  // The modal keeps the box focused as answers land; a panel takes focus
  // only when it opens, never when a result lands (K16, G54).
  const focusOnLand = variant === "modal" ? thread.length : 0;
  useEffect(() => {
    if (open) (boxRef.current ?? inputRef.current)?.focus();
  }, [open, focusOnLand, target?.aboutStep]);

  useEffect(() => {
    const node = bodyRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [thread, pending]);

  if (!target) return null;

  async function send(pinned?: { text: string; spanKeys: string[] }) {
    if (!target || pending || limitReached) return;
    const text = (pinned?.text ?? question).trim();
    if (!text) return;
    setPending(true);
    setInlineError(null);
    setThread((prev) => [
      ...prev,
      {
        eventId: null,
        questionMd: text,
        answerMd: null,
        questionType: null,
        hintEquivalent: false,
        rating: null,
        savedNoteId: null,
        promotion: null,
        promotionRequest: null,
        local: true,
        workbenchSessionId: target.workbenchSessionId ?? null,
        aboutStep: target.aboutStep ?? null
      }
    ]);
    if (!pinned) setQuestion("");
    try {
      let answer: {
        eventId: string;
        answerMd: string;
        questionType: string | null;
        hintEquivalent: boolean;
        citations: TutorCitationDto[];
        suggestions?: SuggestedLearningObjectDto[];
        remaining: number | null;
        learnerGap?: LearnerGapQueuedDto;
        practiceRequest?: PracticeRequestDto | null;
        toolRequests?: SourceToolRequestDto[];
        answerMode?: AnswerMode | null;
        takeOffer?: { levels: number[] } | null;
      };
      if (target.context === "reader") {
        if (!target.extractionId || !target.spanId) {
          throw new Error("This reader question is no longer linked to its source span.");
        }
        if (readerParentRef.current === undefined) {
          readerParentRef.current = await readerThreadParent(target.extractionId, target.spanId, target.readerQuestionEventId);
        }
        const readerAnswer = await api.readerAsk({
          extractionId: target.extractionId,
          spanId: target.spanId,
          question: text,
          // Present only while reader_inquiry is on (absent: today's request).
          ...(readerParentRef.current !== null ? { parentExchangeId: readerParentRef.current } : {})
        });
        if (readerParentRef.current !== null && readerAnswer.parentExchangeId !== undefined) {
          readerParentRef.current = readerAnswer.readerAnswerEventId;
        }
        answer = {
          eventId: readerAnswer.eventId,
          answerMd: readerAnswer.answerMd,
          questionType: null,
          hintEquivalent: readerAnswer.hintEquivalent,
          citations: readerAnswer.citations,
          suggestions: readerAnswer.suggestedLearningObjects,
          remaining: readerAnswer.remaining ?? 0,
          learnerGap: readerAnswer.learnerGap
        };
      } else {
        const input: AskTutorQuestionInput = {
          captureId: routedCaptureRef.current === target.captureId ? undefined : target.captureId,
          subjectId: target.subjectId,
          context: target.context,
          question: text,
          practiceItemId: target.practiceItemId,
          attemptId: target.attemptId,
          noteId: captureNoteRef.current ?? target.noteId,
          sessionId: target.sessionId
        };
        if (target.context === "practice" && target.openedAtMs) {
          input.secondsIntoAttempt = Math.max(0, (Date.now() - target.openedAtMs) / 1000);
        }
        // Elapsed time is fractional, so it never says "before any work" by
        // itself; the explicit draft state does.
        if (target.context === "practice" && target.attemptProgress) {
          input.attemptProgress = target.attemptProgress;
        }
        if (pinned) {
          // "Explain this with my work": a normal tutor question grounded in
          // the passage the learner chose, with their current draft.
          input.pinnedSpanKeys = pinned.spanKeys;
          if (target.draftMd?.trim()) input.learnerDraftMd = target.draftMd;
        }
        if (target.context === "practice" && target.workMd?.trim()) {
          // B1: in steps the work is the steps, on every question.
          input.learnerDraftMd = target.workMd;
        }
        if (panel && target.context === "practice") {
          // Reader CA2 (§7.2, K5, K7): the attempt's key, the workbench the
          // question comes from and its step, and the live draft read now
          // (the context line's "your draft ×" leaves it out).
          if (target.submissionId) input.submissionId = target.submissionId;
          if (target.workbenchSessionId) input.workbenchSessionId = target.workbenchSessionId;
          if (target.aboutStep) input.aboutStep = target.aboutStep;
          const draft = target.readDraft?.() ?? target.workMd ?? "";
          if (dropDraft) delete input.learnerDraftMd;
          else if (draft.trim()) input.learnerDraftMd = draft;
        }
        if (panel && oneMode && (target.context === "practice" || target.context === "feedback")) {
          input.answerMode = oneMode;
        }
        const tutorAnswer = await api.askTutorQuestion(input);
        routedCaptureRef.current = target.captureId ?? null;
        captureNoteRef.current = tutorAnswer.noteId ?? null;
        answer = {
          eventId: tutorAnswer.eventId,
          answerMd: tutorAnswer.answerMd,
          questionType: tutorAnswer.questionType,
          hintEquivalent: tutorAnswer.hintEquivalent,
          citations: tutorAnswer.citations,
          remaining: tutorAnswer.remaining,
          learnerGap: tutorAnswer.learnerGap,
          practiceRequest: tutorAnswer.practiceRequest ?? null,
          toolRequests: tutorAnswer.toolRequests ?? [],
          answerMode: tutorAnswer.answerMode ?? null,
          takeOffer: tutorAnswer.takeOffer ?? null
        };
      }
      setThread((prev) =>
        prev.map((entry, index) =>
          index === prev.length - 1
            ? {
                eventId: answer.eventId,
                questionMd: text,
                answerMd: answer.answerMd,
                questionType: answer.questionType,
                hintEquivalent: answer.hintEquivalent,
                rating: null,
                savedNoteId: null,
                promotion: null,
                promotionRequest: null,
                citations: answer.citations,
                suggestions: answer.suggestions,
                practiceRequest: answer.practiceRequest ?? null,
                toolRequests: answer.toolRequests ?? [],
                answerMode: answer.answerMode ?? null,
                takeOffer: answer.takeOffer ?? null,
                local: true,
                workbenchSessionId: target.workbenchSessionId ?? null,
                aboutStep: target.aboutStep ?? null
              }
            : entry
        )
      );
      // A one-question mode is for this question only (§7.4).
      setOneMode(null);
      onAnswered?.({ eventId: answer.eventId, questionMd: text, hintEquivalent: answer.hintEquivalent,
                     questionType: answer.questionType });
      setRemaining(answer.remaining);
      if (answer.remaining !== null && answer.remaining <= 0) setLimitReached(true);
      watchGap(answer.eventId, answer.learnerGap);
    } catch (error) {
      const commandError = error as CommandError;
      setThread((prev) => prev.slice(0, -1));
      if (commandError.code === "question_limit_reached") {
        setLimitReached(true);
        setInlineError(commandError.message);
        setRemaining(0);
      } else {
        setInlineError(commandError.message);
        if (!pinned) setQuestion(text);
      }
    } finally {
      setPending(false);
    }
  }

  async function rate(eventId: string, useful: boolean) {
    try {
      await api.rateTutorAnswer(eventId, useful);
      setThread((prev) =>
        prev.map((entry) => (entry.eventId === eventId ? { ...entry, rating: useful ? 1 : 0 } : entry))
      );
    } catch (error) {
      onToast((error as CommandError).message);
    }
  }

  async function saveAsNote(eventId: string) {
    setSavingNote(eventId);
    try {
      const result = await api.saveTutorAnswerNote(eventId);
      setThread((prev) =>
        prev.map((entry) =>
          entry.eventId === eventId ? { ...entry, savedNoteId: result.noteId ?? entry.savedNoteId } : entry
        )
      );
      const noteName = result.noteId ? ` ${result.noteId}` : "";
      showSaveNotice({
        eventId,
        message: `Saved note${noteName} at ${result.path}`
      });
    } catch (error) {
      onToast((error as CommandError).message);
    } finally {
      setSavingNote(null);
    }
  }

  async function promote(eventId: string, intent: PromotionIntent) {
    setPromoteChoiceEventId(null);
    setPromotingEventId(eventId);
    try {
      const result = await api.promoteTutorQuestion(eventId, intent);
      setThread((prev) =>
        prev.map((entry) =>
          entry.eventId === eventId
            ? {
                ...entry,
                promotion: result.promotion,
                promotionRequest: result.request
              }
            : entry
        )
      );
      notifyQueueChanged();
    } catch (error) {
      showPromoteNotice({ eventId, message: (error as CommandError).message });
    } finally {
      setPromotingEventId(null);
    }
  }

  // §7.7: a check on your own, by the screen's word or the server's.
  const cold = Boolean(target.coldCheck) || serverCold;
  /** Codex review F5 (§7.6): an inline panel under a step shows that step's
   *  exchanges, by their stored step (asked here or restored); the panel at
   *  the foot of the steps is the whole problem's, the attempt's thread. */
  function inlineShows(entry: ThreadEntry): boolean {
    if (!target?.aboutStep) return true;
    return entry.aboutStep === target.aboutStep
      && (!entry.workbenchSessionId || !target.workbenchSessionId || entry.workbenchSessionId === target.workbenchSessionId);
  }
  // Reader CA2 (§7.1): the context line, what the answer will see, each part
  // a chip; "your draft ×" leaves the draft out of this question.
  const hasDraft = target.context === "practice" && Boolean((target.readDraft?.() ?? target.workMd ?? "").trim());
  const aboutChips: string[] = target.context === "feedback"
    ? ["your attempt", "its feedback"]
    : target.aboutStep
      ? [`step ${target.aboutStep}`, ...(target.stepsCount ? [`your steps 1–${target.stepsCount}`] : [])]
      : [cold ? "this check" : (target.itemLabel ?? "this question")];
  const sentList = [
    target.context === "feedback" ? "the attempt you submitted, its grade and feedback" : "the question",
    ...(hasDraft && !dropDraft ? [target.workbenchSessionId ? "your steps, as you have them now" : "your draft, as it is now"] : []),
    ...(target.aboutStep ? [`which step you are asking about (step ${target.aboutStep})`] : []),
    "this attempt's earlier questions (never an earlier attempt's)",
    "the passages LearnLoop's books link to this topic"
  ];
  const panelHeader = panel ? (
    <div style={{ padding: variant === "inline" ? "6px 10px" : "10px 14px", borderBottom: `1px solid ${COLOR.border}`, display: "flex", flexDirection: "column", gap: 6, flexShrink: 0 }}>
      {variant === "docked" ? (
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{ color: COLOR.text, fontSize: 12, letterSpacing: "0.08em" }}>ASK</span>
          <span style={{ flex: 1 }} />
          <button type="button" onClick={onClose} aria-label="close ask"
            style={{ border: 0, background: "transparent", color: COLOR.textDim, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 12 }}>
            esc
          </button>
        </div>
      ) : null}
      <div data-testid="ask-context-line" style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "baseline", fontSize: 11, color: COLOR.textDim }}>
        <span>about ›</span>
        {aboutChips.map((chip) => (
          <span key={chip} style={{ border: `1px solid ${COLOR.border}`, padding: "0 5px", color: COLOR.text }}>{chip}</span>
        ))}
        {hasDraft ? (
          dropDraft ? (
            <button type="button" onClick={() => setDropDraft(false)}
              style={{ border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
              + {target.workbenchSessionId ? "your steps" : "your draft"}
            </button>
          ) : (
            <span style={{ border: `1px solid ${COLOR.border}`, padding: "0 5px", color: COLOR.text }}>
              {target.workbenchSessionId ? "your steps" : "your draft"}{" "}
              <button type="button" aria-label="leave it out of this question" onClick={() => setDropDraft(true)}
                style={{ border: 0, background: "transparent", color: COLOR.textDim, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
                ×
              </button>
            </span>
          )
        ) : null}
        <button type="button" aria-expanded={sentOpen} onClick={() => setSentOpen((value) => !value)}
          style={{ border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
          {ASK_COPY.whatsSent}
        </button>
      </div>
      {sentOpen ? (
        <ul data-testid="ask-whats-sent" style={{ margin: 0, paddingLeft: 16, fontSize: 11, color: COLOR.textDim }}>
          {sentList.map((line) => <li key={line}>{line}</li>)}
        </ul>
      ) : null}
      {variant === "docked" && (target.context === "practice" || target.context === "feedback") ? (
        <StoredHelpStyle onError={onToast} />
      ) : null}
    </div>
  ) : null;

  const earlierEntry = earlier.find((entry) => entry.attemptId === earlierShown) ?? null;
  const panelFoot = panel && variant === "docked" && !cold && earlier.length > 0 ? (
    <div data-testid="ask-earlier" style={{ padding: "6px 14px", borderTop: `1px solid ${COLOR.border}`, fontSize: 11, color: COLOR.textDim, flexShrink: 0 }}>
      <button type="button" aria-expanded={earlierOpen}
        onClick={() => {
          if (!earlierOpen && earlierCountsAsHint && !earlierAlreadyOpened) {
            onEarlierOpened?.();
            setEarlierAlreadyOpened(true);
          }
          setEarlierOpen((value) => !value);
        }}
        style={{ border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
        {target.context === "feedback" ? ASK_COPY.earlierFree : ASK_COPY.earlier}
      </button>
      {earlierCountsAsHint && !earlierOpen ? <span> · {earlierAlreadyOpened ? ASK_COPY.earlierCounted : ASK_COPY.earlierCost}</span> : null}
      {earlierOpen ? (
        <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 4 }}>
          {earlier.map((entry) => (
            <button type="button" key={entry.attemptId} onClick={() => setEarlierShown(entry.attemptId === earlierShown ? null : entry.attemptId)}
              aria-expanded={entry.attemptId === earlierShown}
              style={{ textAlign: "left", border: 0, background: "transparent", color: COLOR.text, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
              {shortDate(entry.at)} · {entry.outcome.label}
            </button>
          ))}
          {earlierEntry ? (
            <div data-testid="ask-earlier-thread" style={{ borderLeft: `2px solid ${COLOR.border}`, paddingLeft: 8, opacity: 0.85 }}>
              <div style={{ color: COLOR.textDim, marginBottom: 4 }}>{ASK_COPY.earlierHeader(shortDate(earlierEntry.at))}</div>
              {earlierEntry.hints.map((hint, index) => (
                <div key={`hint-${index}`} style={{ marginBottom: 4 }}>
                  <div style={{ color: COLOR.textDim }}>◇ a hint{hint.level ? ` (L${hint.level})` : ""}</div>
                  <div className="markdown"><MarkdownMath value={hint.bodyMd} /></div>
                </div>
              ))}
              {earlierEntry.exchanges.map((exchange) => (
                <div key={exchange.eventId} style={{ marginBottom: 4 }}>
                  <div style={{ color: COLOR.text }}>› <MarkdownMath value={exchange.questionMd} /></div>
                  {exchange.answerMd ? <div className="markdown" style={{ color: COLOR.textDim }}><MarkdownMath value={exchange.answerMd} /></div> : null}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  ) : null;

  const content = (
    <>
        {panel ? panelHeader : (
        /* ── header ── */
        <div style={headerStyle}>
          <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
          <span style={{ color: COLOR.text, fontSize: 13 }}>
            learnloop <span style={{ color: COLOR.amber }}>ask</span>
          </span>
          <Pill color={CONTEXT_PILL[target.context]}>{target.context}</Pill>
          <Faint>·</Faint>
          <span style={{ color: COLOR.amberLink, fontSize: 13, fontFamily: FONT_MONO }}>
            {entityIdOf(target)}
          </span>
          <span style={{ flex: 1 }} />
          {remaining !== null ? (
            <Pill color={remaining > 0 ? "slate" : "red"}>{remaining} left</Pill>
          ) : null}
          <span
            onClick={onClose}
            style={{ color: COLOR.textDim, cursor: "pointer", fontSize: 13, marginLeft: 6 }}
          >
            esc
          </span>
        </div>
        )}

        {/* ── transcript ── */}
        <div ref={bodyRef} style={{ flex: 1, overflowY: "auto", minHeight: 0, padding: "12px 16px" }}>
          {panel && thread.length === 0 && !pending ? (
            variant === "docked" ? <Faint>{ASK_COPY.empty}</Faint> : null
          ) : thread.length === 0 && !pending ? (
            <Faint>
              ask the tutor about this{" "}
              {target.context === "library"
                ? "note"
                : target.context === "reader"
                  ? "source passage"
                  : "item"}{" "}
              …
            </Faint>
          ) : null}
          {(variant === "inline" && panel ? thread.filter((entry) => inlineShows(entry)) : thread).map((entry, index) => (
            <div key={entry.eventId ?? `pending-${index}`} style={{ marginBottom: 16 }}>
              {!entry.opening ? (
                <div style={{ color: COLOR.text, fontSize: 13, display: "flex", alignItems: "baseline", gap: 6 }}>
                  <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯</span>
                  <div className="markdown ask-user-message" style={{ flex: 1, minWidth: 0 }}>
                    <MarkdownMath value={entry.questionMd} />
                  </div>
                </div>
              ) : null}
              {entry.answerMd === null ? (
                <div style={{ marginTop: 6 }}>
                  <Faint>thinking …</Faint>
                </div>
              ) : (
                <div style={{ marginTop: entry.opening ? 0 : 6 }}>
                  {panel && !entry.opening ? (
                    // Reader CA2 (§7.5, §7.7, K16): one voice label, saying the
                    // mode it was written in and what it counted as.
                    <div data-testid="ask-answer-label" style={{ fontSize: 11, color: COLOR.textDim, marginBottom: 4 }}>
                      {["◇ model",
                        (entry.aboutStep ?? target.aboutStep) ? `about step ${entry.aboutStep ?? target.aboutStep}` : "your question",
                        entry.answerMode ? ANSWER_MODE_LABEL[entry.answerMode] : null,
                        target.context === "practice" || target.context === "feedback"
                          ? answerCountLabel({ hintEquivalent: entry.hintEquivalent, context: target.context, cold })
                          : null].filter(Boolean).join(" · ")}
                    </div>
                  ) : (
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                    {entry.opening ? <Pill color="amber">tutor</Pill> : null}
                    {entry.questionType ? <Pill color="slate">{entry.questionType}</Pill> : null}
                    {entry.hintEquivalent ? <Pill color="amber">counted as hint</Pill> : null}
                  </div>
                  )}
                  {panel && !entry.opening ? (
                    // K11: book first. The cited passages lead; with none
                    // kept, the explanation says it is the model's own.
                    entry.takeOffer ? null : entry.citations && entry.citations.length > 0 ? (
                      <div data-testid="ask-book-first" style={{ marginBottom: 6 }}>
                      {/* K11 (Codex review F9): the verified excerpt first, the
                          books' own words, then the chips that open it. */}
                      {entry.citations.find((citation) => citation.excerpt) ? (
                        <blockquote data-testid="ask-book-excerpt" style={{ margin: "0 0 4px", paddingLeft: 8, borderLeft: `2px solid ${COLOR.border}`, fontSize: 12, color: COLOR.text }}>
                          <MarkdownMath value={entry.citations.find((citation) => citation.excerpt)?.excerpt ?? ""} />
                        </blockquote>
                      ) : null}
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                        <span style={{ fontSize: 11, color: COLOR.textDim }}>{ASK_COPY.fromBooks}</span>
                        {entry.citations.map((citation) => (
                          <button type="button" key={`${citation.extractionId}:${citation.spanId}`}
                            onClick={() => setOpenCitation(citation)} title="Open in source"
                            style={{ cursor: "pointer", fontSize: 11, fontFamily: FONT_MONO, color: COLOR.amberLink,
                              border: `1px solid ${COLOR.border}`, background: "transparent", padding: "1px 6px" }}>
                            § {citation.label ?? citation.spanId}
                          </button>
                        ))}
                      </div>
                      </div>
                    ) : entry.eventId ? (
                      <div data-testid="ask-no-books" style={{ fontSize: 11, color: COLOR.textDim, marginBottom: 4 }}>{ASK_COPY.noBooks}</div>
                    ) : null
                  ) : null}
                  {panel && !entry.opening && entry.citations && entry.citations.length > 0 ? (
                    <div style={{ fontSize: 11, color: COLOR.textDim, marginBottom: 2 }}>{ASK_COPY.explanation}</div>
                  ) : null}
                  {panel && entry.takeOffer ? (
                    // Codex review F2 (K9, §7.5): worked help is never served
                    // on the spot; the ladder's take step, inline in the thread.
                    <div data-testid="ask-take-step" style={{ fontSize: 13, display: "flex", flexDirection: "column", gap: 4 }}>
                      <span style={{ color: COLOR.text }}>{ASK_COPY.takeStep}</span>
                      {onTakeWorked ? (
                        <span style={{ display: "flex", gap: 10, flexWrap: "wrap", fontSize: 12 }}>
                          <button type="button" onClick={() => onTakeWorked(4)}
                            style={{ border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, padding: 0 }}>
                            {ASK_COPY.takePiece}
                          </button>
                          <button type="button" onClick={() => onTakeWorked(5)}
                            style={{ border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, padding: 0 }}>
                            {ASK_COPY.takeWorked}
                          </button>
                          <button type="button" onClick={() => (boxRef.current ?? inputRef.current)?.focus()}
                            style={{ border: 0, background: "transparent", color: COLOR.textDim, cursor: "pointer", fontFamily: FONT_MONO, padding: 0 }}>
                            {ASK_COPY.takeSmaller}
                          </button>
                        </span>
                      ) : (
                        <span style={{ fontSize: 12, color: COLOR.textDim }}>{ASK_COPY.takeFromLadder}</span>
                      )}
                    </div>
                  ) : (
                  <div className="markdown" style={{ fontSize: 13, lineHeight: 1.6 }}>
                    <MarkdownMath value={entry.answerMd} />
                  </div>
                  )}
                  {!panel && entry.citations && entry.citations.length > 0 ? (
                    <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
                      <span style={{ fontSize: 10, color: COLOR.textFaint, fontFamily: FONT_MONO }}>sources:</span>
                      {entry.citations.map((citation) => (
                        <span
                          key={`${citation.extractionId}:${citation.spanId}`}
                          onClick={() => setOpenCitation(citation)}
                          title="Open in source"
                          style={{
                            cursor: "pointer",
                            fontSize: 11,
                            fontFamily: FONT_MONO,
                            color: COLOR.amberLink,
                            border: `1px solid ${COLOR.border}`,
                            borderRadius: 3,
                            padding: "1px 6px"
                          }}
                        >
                          ❯ {citation.label ?? citation.spanId}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  {entry.eventId && target.context !== "reader" &&
                  (entry.practiceRequest || (entry.toolRequests ?? []).length > 0) ? (
                    <SourceOffers
                      answer={{
                        eventId: entry.eventId,
                        practiceRequest: entry.practiceRequest,
                        toolRequests: entry.toolRequests
                      }}
                      sessionId={target.sessionId}
                      onToast={onToast}
                      onOpenPractice={onOpenPractice}
                      onExplainWithWork={(spanKey) =>
                        void send({ text: "Explain this passage using my work.", spanKeys: [spanKey] })
                      }
                    />
                  ) : null}
                  {suggestionLine(entry.suggestions) ? (
                    <div style={{ marginTop: 6, fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO }}>
                      {suggestionLine(entry.suggestions)}
                    </div>
                  ) : null}
                  {entry.eventId && entry.gap?.label ? (
                    <div
                      data-testid="learner-gap"
                      style={{ display: "flex", gap: 10, marginTop: 6, fontSize: 12, alignItems: "center", flexWrap: "wrap" }}
                    >
                      <span style={{ color: COLOR.textDim }}>{entry.gap.label}</span>
                      {entry.gap.allowedReversals.map((reversal) => (
                        <span
                          key={reversal}
                          onClick={() => void reverseGap(entry.eventId as string, entry.gap!.gapId, reversal)}
                          style={{ cursor: "pointer", color: COLOR.amberLink }}
                        >
                          {REVERSAL_LABEL[reversal]}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  {entry.eventId ? (
                    <div style={{ display: "flex", gap: 14, marginTop: 6, fontSize: 12, flexWrap: "wrap", alignItems: "center" }}>
                      {/* CSS `color` has no effect on color-emoji glyphs, so the
                          selected state needs a background/opacity cue instead. */}
                      <span
                        onClick={() => void rate(entry.eventId as string, true)}
                        style={{
                          cursor: "pointer",
                          padding: "1px 5px",
                          borderRadius: 4,
                          opacity: entry.rating === 0 ? 0.35 : 1,
                          background: entry.rating === 1 ? "rgba(227, 160, 99, 0.25)" : "transparent",
                          outline: entry.rating === 1 ? `1px solid ${COLOR.amber}` : "none"
                        }}
                      >
                        👍
                      </span>
                      <span
                        onClick={() => void rate(entry.eventId as string, false)}
                        style={{
                          cursor: "pointer",
                          padding: "1px 5px",
                          borderRadius: 4,
                          opacity: entry.rating === 1 ? 0.35 : 1,
                          background: entry.rating === 0 ? "rgba(227, 160, 99, 0.25)" : "transparent",
                          outline: entry.rating === 0 ? `1px solid ${COLOR.amber}` : "none"
                        }}
                      >
                        👎
                      </span>
                      <span
                        onClick={() => {
                          if (canSaveNote(entry)) void saveAsNote(entry.eventId as string);
                        }}
                        style={{
                          cursor: canSaveNote(entry) ? "pointer" : "default",
                          color: entry.savedNoteId ? COLOR.textDim : COLOR.amberLink
                        }}
                      >
                        {saveNoteLabel(entry)}
                      </span>
                      {/* → practice: promote this socratic question (spec_tutor_promotion.md §2). */}
                      {entry.promotionRequest?.status === "failed" ? (
                        <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <span
                            style={{
                              color:
                                entry.promotionRequest.status === "failed"
                                  ? COLOR.red
                                  : COLOR.textDim
                            }}
                          >
                            {promotionRequestLabel(entry.promotionRequest)}
                          </span>
                          {entry.promotionRequest.retryable ? (
                            <span
                              onClick={() =>
                                void promote(entry.eventId as string, entry.promotionRequest!.intent)
                              }
                              style={{ cursor: "pointer", color: COLOR.amberLink }}
                            >
                              retry
                            </span>
                          ) : null}
                        </span>
                      ) : entry.promotion ? (
                        <span style={{ color: COLOR.textDim }}>{promotionChipLabel(entry.promotion)}</span>
                      ) : entry.promotionRequest ? (
                        <span style={{ color: COLOR.textDim }}>
                          {promotionRequestLabel(entry.promotionRequest)}
                        </span>
                      ) : promotingEventId === entry.eventId ? (
                        <span style={{ color: COLOR.textDim }}>promoting…</span>
                      ) : promoteChoiceEventId === entry.eventId ? (
                        <span style={{ display: "flex", gap: 10, alignItems: "center" }}>
                          <span
                            onClick={() => void promote(entry.eventId as string, "practice")}
                            style={{ cursor: "pointer", color: COLOR.amberLink }}
                          >
                            add to practice
                          </span>
                          {target.context === "practice" || target.context === "feedback" ? (
                            <span
                              onClick={() => void promote(entry.eventId as string, "gap")}
                              style={{ cursor: "pointer", color: COLOR.amberLink }}
                            >
                              this exposed a gap
                            </span>
                          ) : null}
                          <span
                            onClick={() => setPromoteChoiceEventId(null)}
                            style={{ cursor: "pointer", color: COLOR.textDim }}
                          >
                            cancel
                          </span>
                        </span>
                      ) : (
                        <span
                          onClick={() => setPromoteChoiceEventId(entry.eventId)}
                          style={{ cursor: "pointer", color: COLOR.amberLink }}
                        >
                          → practice
                        </span>
                      )}
                    </div>
                  ) : null}
                  {saveNotice?.eventId === entry.eventId ? (
                    <div style={saveNoticeStyle}>{saveNotice.message}</div>
                  ) : null}
                  {promoteNotice?.eventId === entry.eventId ? (
                    <div style={saveNoticeStyle}>{promoteNotice.message}</div>
                  ) : null}
                </div>
              )}
            </div>
          ))}
          {inlineError ? (
            <div style={{ color: COLOR.red, fontSize: 12, marginTop: 4 }}>{inlineError}</div>
          ) : null}
        </div>

        {/* ── input ── */}
        <div style={{ padding: panel && variant === "inline" ? "6px 10px" : "10px 16px", borderTop: `1px solid ${COLOR.border}`, flexShrink: 0 }}>
          {target.context === "practice" && !panel ? (
            <div style={{ marginBottom: 6, fontSize: 11 }}>
              <Faint>substantive questions count as hints</Faint>
            </div>
          ) : null}
          {panel ? (
          // Codex review F11 (§7.1): one multiline box on every panel host:
          // ↵ sends, ⇧↵ a new line, ^↵ sends too; a send never reaches the
          // screen's own ^↵ (Submit).
          <textarea
            ref={boxRef}
            value={question}
            rows={Math.min(6, Math.max(1, question.split("\n").length))}
            disabled={pending || limitReached}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key !== "Enter") return;
              event.stopPropagation();
              if (event.shiftKey && !event.ctrlKey && !event.metaKey) return;
              event.preventDefault();
              void send();
            }}
            placeholder={
              limitReached
                ? "Today's question budget for this one is used"
                : pending
                  ? "looking in your books… then writing"
                  : cold ? ASK_COPY.coldPlaceholder : ASK_COPY.placeholder
            }
            aria-label={target.aboutStep ? `ask about step ${target.aboutStep}` : "ask in your words"}
            style={{ ...inputStyle, resize: "none", opacity: pending || limitReached ? 0.6 : 1 }}
          />
          ) : (
          <input
            ref={inputRef}
            value={question}
            disabled={pending || limitReached}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void send();
              }
            }}
            placeholder={
              limitReached
                ? panel ? "Today's question budget for this one is used" : "question limit reached"
                : pending
                  ? panel ? "looking in your books… then writing" : "waiting for the tutor …"
                  : panel ? (cold ? ASK_COPY.coldPlaceholder : ASK_COPY.placeholder) : "ask a question — enter sends"
            }
            aria-label={panel ? (target.aboutStep ? `ask about step ${target.aboutStep}` : "ask in your words") : undefined}
            style={{ ...inputStyle, opacity: pending || limitReached ? 0.6 : 1 }}
          />
          )}
          {panel && (target.context === "practice" || target.context === "feedback") ? (
            // §7.1 item 4: the cost, said before sending; §7.4: "change" picks
            // another mode for this one question.
            <div data-testid="ask-cost-line" style={{ marginTop: 6, fontSize: 11, color: COLOR.textDim, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "baseline" }}>
              <span>{target.context === "feedback" ? ASK_COPY.costFeedback : cold ? "" : ASK_COPY.cost}</span>
              <span style={{ flex: 1 }} />
              <span>{ANSWER_MODE_LABEL[oneMode ?? STYLE_ANSWER_MODE[helpStyle]]}</span>
              <button type="button" aria-expanded={changeOpen} onClick={() => setChangeOpen((value) => !value)}
                style={{ border: 0, background: "transparent", color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
                change
              </button>
              {changeOpen ? (
                <span role="group" aria-label="answer mode for this question" style={{ flexBasis: "100%", display: "flex", gap: 10, flexWrap: "wrap" }}>
                  {ONE_QUESTION_MODES.map((option) => (
                    <button type="button" key={option.value} aria-pressed={oneMode === option.value}
                      onClick={() => {
                        setOneMode(option.value === STYLE_ANSWER_MODE[helpStyle] ? null : option.value);
                        setChangeOpen(false);
                      }}
                      style={{ border: 0, background: "transparent", color: oneMode === option.value ? COLOR.text : COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11, padding: 0 }}>
                      {option.label}
                    </button>
                  ))}
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        {panelFoot}

        {/* ── footer ── */}
        {panel ? (cold && variant === "docked" ? (
          <div style={{ ...footerStyle, padding: "4px 14px" }}><span>{ASK_COPY.keepOnMyOwn}</span></div>
        ) : null) : (
        <div style={footerStyle}>
          <span>
            <span style={{ color: COLOR.text }}>↵</span> send
          </span>
          <span>
            <span style={{ color: COLOR.text }}>esc</span> close
          </span>
          <span style={{ flex: 1 }} />
          <span>
            tutor answers are logged{target.context === "practice" ? " · never reveals the answer" : ""}
          </span>
        </div>
        )}
    </>
  );

  const shell = !panel ? (
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(event) => event.stopPropagation()}>
        {content}
      </div>
    </div>
  ) : (
    <section
      role="region"
      aria-label={variant === "inline" ? (target.aboutStep ? `ask about step ${target.aboutStep}` : "ask about this problem") : "ask"}
      data-testid={`ask-panel-${variant}`}
      onKeyDown={(event) => {
        // Esc closes the panel and returns focus to where it was (§7.1).
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
          onClose();
        }
      }}
      style={variant === "docked" ? dockedStyle : inlineStyle}
    >
      {content}
    </section>
  );

  return (
    <>
    {shell}
    {openCitation ? (
      <OpenInSource
        extractionId={openCitation.extractionId}
        spanId={openCitation.spanId}
        context="tutor_citation"
        entityType={null}
        entityId={null}
        onClose={() => setOpenCitation(null)}
      />
    ) : null}
    </>
  );
}

// Reader CA2 (§7.1): docked beside the question, the host sizes the column.
const dockedStyle: CSSProperties = {
  height: "100%",
  minHeight: 0,
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text,
  background: COLOR.bg
};

// Inline under a workbench step, where a hint would sit (§7.6).
const inlineStyle: CSSProperties = {
  border: `1px solid ${COLOR.border}`,
  margin: "4px 0",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text,
  maxHeight: 420
};

const backdropStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 210,
  background: "rgba(8, 8, 13, 0.78)",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "8vh 5vw",
  backdropFilter: "blur(2px)"
};

const modalStyle: CSSProperties = {
  width: "min(760px, 100%)",
  maxHeight: "80vh",
  minHeight: 320,
  background: COLOR.bg,
  border: `1px solid ${COLOR.borderStrong}`,
  boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
  display: "flex",
  flexDirection: "column",
  fontFamily: FONT_MONO,
  color: COLOR.text
};

const headerStyle: CSSProperties = {
  padding: "12px 16px",
  borderBottom: `1px solid ${COLOR.border}`,
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexShrink: 0
};

const inputStyle: CSSProperties = {
  width: "100%",
  background: COLOR.bgInput,
  color: COLOR.text,
  border: `1px solid ${COLOR.borderFocus}`,
  padding: "8px 12px",
  fontSize: 13,
  fontFamily: FONT_MONO,
  outline: "none"
};

const footerStyle: CSSProperties = {
  borderTop: `1px solid ${COLOR.border}`,
  padding: "6px 14px",
  fontSize: 11,
  color: COLOR.textDim,
  display: "flex",
  gap: 18,
  flexShrink: 0,
  alignItems: "center"
};

const saveNoticeStyle: CSSProperties = {
  marginTop: 8,
  border: `1px solid ${COLOR.amber}`,
  background: "#241d12",
  color: COLOR.amber,
  padding: "7px 9px",
  fontSize: 12,
  lineHeight: 1.4
};
