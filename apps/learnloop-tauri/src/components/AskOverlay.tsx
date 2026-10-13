import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  AskTutorQuestionInput,
  AttemptProgress,
  CommandError,
  LearnerGapQueuedDto,
  LearnerTextGapReversal,
  LearnerTextGapViewDto,
  PromotionIntent,
  QuestionPromotionDto,
  QuestionPromotionRequestDto,
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
  /** Date.now() when the practice item was opened (practice context only). */
  openedAtMs?: number;
  /** Practice context only: whether the learner had started an answer when
   *  the overlay opened (it is modal, so the draft cannot change while open). */
  attemptProgress?: AttemptProgress;
  /** §12.1: open with the tutor's persisted typed move before the learner
   *  types anything (diagnostic block just routed to tutoring). */
  proactiveOpen?: boolean;
}

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
  onToast
}: {
  target: AskTarget | null;
  onClose: () => void;
  onToast: (message: string) => void;
}) {
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
  const saveNoticeTimerRef = useRef<number | null>(null);
  const promoteNoticeTimerRef = useRef<number | null>(null);
  const routedCaptureRef = useRef<string | null>(null);
  const captureNoteRef = useRef<string | null>(null);
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
    setQuestion(target.initialQuestion ?? "");
    routedCaptureRef.current = null;
    captureNoteRef.current = null;
    // A new capture has no library note yet. Do not request an unscoped
    // library transcript; the server anchors it on the first successful send.
    if (target.captureId && !target.noteId) return;
    api
      .getTutorTranscript({
        context: target.context,
        practiceItemId: target.practiceItemId,
        attemptId: target.attemptId,
        noteId: target.noteId,
        sessionId: target.sessionId
      })
      .then((snapshot) => {
        if (cancelled) return;
        const entries: ThreadEntry[] = snapshot.events.map((event: TutorQuestionEventDto) => ({
          eventId: event.id,
          questionMd: event.questionMd,
          answerMd: event.answerMd,
          questionType: event.questionType,
          hintEquivalent: event.hintEquivalent,
          rating: event.rating,
          savedNoteId: event.savedNoteId,
          promotion: event.promotion,
          promotionRequest: event.promotionRequest ?? null
        }));
        setThread(entries);
        setRemaining(snapshot.remaining);
        setLimitReached(snapshot.remaining <= 0);
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
    target?.proactiveOpen
  ]);

  useEffect(() => clearSaveNoticeTimer, []);
  useEffect(() => clearPromoteNoticeTimer, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [open, onClose]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open, thread.length]);

  useEffect(() => {
    const node = bodyRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [thread, pending]);

  if (!target) return null;

  async function send() {
    if (!target || pending || limitReached) return;
    const text = question.trim();
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
        promotionRequest: null
      }
    ]);
    setQuestion("");
    try {
      let answer: {
        eventId: string;
        answerMd: string;
        questionType: string | null;
        hintEquivalent: boolean;
        citations: TutorCitationDto[];
        suggestions?: SuggestedLearningObjectDto[];
        remaining: number;
        learnerGap?: LearnerGapQueuedDto;
      };
      if (target.context === "reader") {
        if (!target.extractionId || !target.spanId) {
          throw new Error("This reader question is no longer linked to its source span.");
        }
        const readerAnswer = await api.readerAsk({
          extractionId: target.extractionId,
          spanId: target.spanId,
          question: text
        });
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
          learnerGap: tutorAnswer.learnerGap
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
                suggestions: answer.suggestions
              }
            : entry
        )
      );
      setRemaining(answer.remaining);
      if (answer.remaining <= 0) setLimitReached(true);
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
        setQuestion(text);
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

  return (
    <>
    <div style={backdropStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(event) => event.stopPropagation()}>
        {/* ── header ── */}
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

        {/* ── transcript ── */}
        <div ref={bodyRef} style={{ flex: 1, overflowY: "auto", minHeight: 0, padding: "12px 16px" }}>
          {thread.length === 0 && !pending ? (
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
          {thread.map((entry, index) => (
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
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                    {entry.opening ? <Pill color="amber">tutor</Pill> : null}
                    {entry.questionType ? <Pill color="slate">{entry.questionType}</Pill> : null}
                    {entry.hintEquivalent ? <Pill color="amber">counted as hint</Pill> : null}
                  </div>
                  <div className="markdown" style={{ fontSize: 13, lineHeight: 1.6 }}>
                    <MarkdownMath value={entry.answerMd} />
                  </div>
                  {entry.citations && entry.citations.length > 0 ? (
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
        <div style={{ padding: "10px 16px", borderTop: `1px solid ${COLOR.border}`, flexShrink: 0 }}>
          {target.context === "practice" ? (
            <div style={{ marginBottom: 6, fontSize: 11 }}>
              <Faint>substantive questions count as hints</Faint>
            </div>
          ) : null}
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
              limitReached ? "question limit reached" : pending ? "waiting for the tutor …" : "ask a question — enter sends"
            }
            style={{ ...inputStyle, opacity: pending || limitReached ? 0.6 : 1 }}
          />
        </div>

        {/* ── footer ── */}
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
      </div>
    </div>
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
