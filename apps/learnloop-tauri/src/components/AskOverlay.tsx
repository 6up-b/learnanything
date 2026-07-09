import { useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  AskTutorQuestionInput,
  CommandError,
  TutorQuestionContext,
  TutorQuestionEventDto
} from "../api/dto";
import { COLOR, Faint, FONT_MONO, Pill, type PillColor } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

export interface AskTarget {
  context: TutorQuestionContext;
  practiceItemId?: string;
  attemptId?: string;
  noteId?: string;
  sessionId?: string;
  /** Date.now() when the practice item was opened (practice context only). */
  openedAtMs?: number;
}

const CONTEXT_PILL: Record<TutorQuestionContext, PillColor> = {
  library: "cyan",
  practice: "amber",
  feedback: "green"
};

interface ThreadEntry {
  eventId: string | null;
  questionMd: string;
  answerMd: string | null;
  questionType: string | null;
  hintEquivalent: boolean;
  rating: number | null;
}

interface SaveNotice {
  eventId: string;
  message: string;
}

function entityIdOf(target: AskTarget): string {
  return target.noteId ?? target.attemptId ?? target.practiceItemId ?? "";
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
  const [remaining, setRemaining] = useState<number | null>(null);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [savingNote, setSavingNote] = useState<string | null>(null);
  const [savedNoteEventIds, setSavedNoteEventIds] = useState<string[]>([]);
  const [saveNotice, setSaveNotice] = useState<SaveNotice | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const saveNoticeTimerRef = useRef<number | null>(null);

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

  function saveNoteLabel(eventId: string) {
    if (savingNote === eventId) return "saving…";
    if (savedNoteEventIds.includes(eventId)) return "saved";
    return "save as note";
  }

  function canSaveNote(eventId: string) {
    return savingNote === null && !savedNoteEventIds.includes(eventId);
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
    setQuestion("");
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
        setThread(
          snapshot.events.map((event: TutorQuestionEventDto) => ({
            eventId: event.id,
            questionMd: event.questionMd,
            answerMd: event.answerMd,
            questionType: event.questionType,
            hintEquivalent: event.hintEquivalent,
            rating: event.rating
          }))
        );
        setRemaining(snapshot.remaining);
        setLimitReached(snapshot.remaining <= 0);
      })
      .catch((error: CommandError) => {
        if (!cancelled) setInlineError(error.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    target?.context,
    target?.practiceItemId,
    target?.attemptId,
    target?.noteId,
    target?.sessionId
  ]);

  useEffect(() => clearSaveNoticeTimer, []);

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
      { eventId: null, questionMd: text, answerMd: null, questionType: null, hintEquivalent: false, rating: null }
    ]);
    setQuestion("");
    const input: AskTutorQuestionInput = {
      context: target.context,
      question: text,
      practiceItemId: target.practiceItemId,
      attemptId: target.attemptId,
      noteId: target.noteId,
      sessionId: target.sessionId
    };
    if (target.context === "practice" && target.openedAtMs) {
      input.secondsIntoAttempt = Math.max(0, (Date.now() - target.openedAtMs) / 1000);
    }
    try {
      const answer = await api.askTutorQuestion(input);
      setThread((prev) =>
        prev.map((entry, index) =>
          index === prev.length - 1
            ? {
                eventId: answer.eventId,
                questionMd: text,
                answerMd: answer.answerMd,
                questionType: answer.questionType,
                hintEquivalent: answer.hintEquivalent,
                rating: null
              }
            : entry
        )
      );
      setRemaining(answer.remaining);
      if (answer.remaining <= 0) setLimitReached(true);
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
      setSavedNoteEventIds((current) => (current.includes(eventId) ? current : [...current, eventId]));
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

  return (
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
            <Faint>ask the tutor about this {target.context === "library" ? "note" : "item"} …</Faint>
          ) : null}
          {thread.map((entry, index) => (
            <div key={entry.eventId ?? `pending-${index}`} style={{ marginBottom: 16 }}>
              <div style={{ color: COLOR.text, fontSize: 13 }}>
                <span style={{ color: COLOR.amber, fontWeight: 700 }}>❯ </span>
                {entry.questionMd}
              </div>
              {entry.answerMd === null ? (
                <div style={{ marginTop: 6 }}>
                  <Faint>thinking …</Faint>
                </div>
              ) : (
                <div style={{ marginTop: 6 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                    {entry.questionType ? <Pill color="slate">{entry.questionType}</Pill> : null}
                    {entry.hintEquivalent ? <Pill color="amber">counted as hint</Pill> : null}
                  </div>
                  <div className="markdown" style={{ fontSize: 13, lineHeight: 1.6 }}>
                    <MarkdownMath value={entry.answerMd} />
                  </div>
                  {entry.eventId ? (
                    <div style={{ display: "flex", gap: 14, marginTop: 6, fontSize: 12 }}>
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
                          if (canSaveNote(entry.eventId as string)) void saveAsNote(entry.eventId as string);
                        }}
                        style={{
                          cursor: canSaveNote(entry.eventId) ? "pointer" : "default",
                          color: savedNoteEventIds.includes(entry.eventId) ? COLOR.textDim : COLOR.amberLink
                        }}
                      >
                        {saveNoteLabel(entry.eventId)}
                      </span>
                    </div>
                  ) : null}
                  {saveNotice?.eventId === entry.eventId ? (
                    <div style={saveNoticeStyle}>{saveNotice.message}</div>
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
