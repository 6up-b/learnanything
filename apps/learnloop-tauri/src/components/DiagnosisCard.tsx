import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { invalidate } from "../api/queryCache";
import { TAG } from "../api/queryTags";
import type {
  DiagnosisCardDto,
  DiagnosisCardResponse,
  DiagnosisStatusValue,
  EscalationResponse,
} from "../api/dto";
import { COLOR, FONT_MONO, Faint } from "./term";
import { Pill } from "./ui";

/** Slice 1 §11: poll every 2.5 s while the asynchronous diagnosis is pending. */
export const DIAGNOSIS_POLL_MS = 2500;

function fmtDay(iso: string | null | undefined): string {
  if (!iso) return "earlier";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "earlier";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const box = {
  marginTop: 14,
  padding: "10px 12px",
  background: COLOR.bgElev,
  borderLeft: `3px solid ${COLOR.cyan}`,
  fontFamily: FONT_MONO,
  fontSize: 12,
  lineHeight: 1.6,
} as const;

const link = { color: COLOR.amberLink, textDecoration: "underline", cursor: "pointer" } as const;

/**
 * The M2 diagnosis card (§12.2). Fills in place when the asynchronous
 * diagnosis arrives: the summary, the repair suggestion(s), "You've made this
 * mistake before" (validated citations only) and any prerequisite-gap
 * hypothesis, labelled as unchecked. At most one optional tap, in a fixed
 * neutral order; a per-citation "not the same mistake" tap. Nothing here is
 * evidence: taps are eval-only.
 *
 * Slice 2 T1 (mvp-0.12): when the cause has recurred K times the card leads
 * with the escalated repair, its earlier answers (each openable) and its own
 * one-tap usefulness rating. The headline says "trying a different approach"
 * only when the backend found a repair whose operator differs from the ones
 * shown before; otherwise it says so plainly. The repair is shown whole (its
 * representation, practice mode and question); it is also the feedback
 * screen's lead repair suggestion, so an eliciting question is answered in
 * the "one question, unaided" box right below this card.
 */
/** The card's state and its one recording action, polled while pending. */
export interface DiagnosisCardState {
  card: DiagnosisCardDto | null;
  status: DiagnosisStatusValue | null;
  recording: boolean;
  record: (
    response: DiagnosisCardResponse | EscalationResponse | "not_same_mistake",
    citedAttemptId?: string | null,
  ) => Promise<void>;
}

/**
 * The polling and the one recording action behind the card, apart from its
 * rendering: UX Phase 4's feedback surface reads the diagnosis as its one
 * sentence on what went wrong (in place, when it lands) and mounts the card
 * itself only under details, with this same state, so the diagnosis is
 * polled once. `initialStatus` null or absent polls nothing.
 */
export function useDiagnosisCard(
  attemptId: string,
  initialStatus: DiagnosisStatusValue | null | undefined,
  onDiagnosisReady: (() => void) | undefined,
  onError: (message: string) => void,
): DiagnosisCardState {
  const [card, setCard] = useState<DiagnosisCardDto | null>(null);
  const [status, setStatus] = useState<DiagnosisStatusValue | null>(initialStatus ?? null);
  const [recording, setRecording] = useState(false);
  const shownAt = useRef<string | null>(null);
  const readyFired = useRef(false);

  useEffect(() => {
    setCard(null);
    setStatus(initialStatus ?? null);
    readyFired.current = initialStatus === "done";
  }, [attemptId, initialStatus]);

  useEffect(() => {
    if (!initialStatus || initialStatus === "not_needed") return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const poll = () => {
      api
        .diagnosisStatus(attemptId)
        .then((result) => {
          if (cancelled) return;
          setCard(result);
          setStatus(result.status);
          if (result.status === "pending") {
            timer = setTimeout(poll, DIAGNOSIS_POLL_MS);
            return;
          }
          if (result.status === "done") {
            if (shownAt.current === null) shownAt.current = new Date().toISOString();
            if (!readyFired.current) {
              readyFired.current = true;
              // The diagnosis overlay changed: cached reads that show it (the
              // Reader Guide's reasons) re-read on their next open.
              invalidate({ tags: [TAG.errors] });
              onDiagnosisReady?.();
            }
          }
        })
        .catch(() => {
          // Best effort: a stale sidecar or a transient error leaves the card
          // out rather than raising a toast over the learner's feedback.
          if (!cancelled) timer = setTimeout(poll, DIAGNOSIS_POLL_MS * 2);
        });
    };
    poll();
    return () => {
      cancelled = true;
      if (timer !== null) clearTimeout(timer);
    };
  }, [attemptId, initialStatus, onDiagnosisReady]);

  const record = useCallback(
    async (
      response: DiagnosisCardResponse | EscalationResponse | "not_same_mistake",
      citedAttemptId: string | null = null,
    ) => {
      if (!card?.diagnosisId || recording) return;
      setRecording(true);
      try {
        await api.recordDiagnosisFeedback({
          attemptId,
          diagnosisId: card.diagnosisId,
          response,
          citedAttemptId,
          shownAt: shownAt.current,
        });
        setCard((current) => {
          if (current === null) return current;
          if (response === "not_same_mistake") {
            return {
              ...current,
              notSameMistakeAttemptIds: [...(current.notSameMistakeAttemptIds ?? []), citedAttemptId ?? ""],
            };
          }
          if (response.startsWith("escalation:")) {
            return current.escalation
              ? { ...current, escalation: { ...current.escalation, recordedResponse: response as EscalationResponse } }
              : current;
          }
          return { ...current, recordedResponse: response as DiagnosisCardResponse };
        });
      } catch (error) {
        onError(error instanceof Error ? error.message : "Your answer could not be recorded.");
      } finally {
        setRecording(false);
      }
    },
    [attemptId, card, onError, recording],
  );

  return { card, status, recording, record };
}

export function DiagnosisCard({
  attemptId,
  initialStatus,
  onDiagnosisReady,
  onOpenAttempt,
  onError,
  state,
}: {
  attemptId: string;
  /** From the feedback bundle; absent means no diagnosis was queued. */
  initialStatus: DiagnosisStatusValue | null | undefined;
  /** Called once when the diagnosis lands, so the screen can reload the
   *  repair suggestions and guided-redo entry point it carries. */
  onDiagnosisReady?: () => void;
  /** Open a cited earlier answer and its blind grade. */
  onOpenAttempt?: (attemptId: string) => void;
  onError: (message: string) => void;
  /** State a screen already polls (`useDiagnosisCard`); the card then polls
   *  nothing itself. */
  state?: DiagnosisCardState;
}) {
  const own = useDiagnosisCard(attemptId, state ? null : initialStatus, onDiagnosisReady, onError);
  const { card, status, record } = state ?? own;

  if (!status || status === "not_needed") return null;
  if (status === "pending") {
    return (
      <div style={box} data-testid="diagnosis-pending">
        <Faint>analyzing your pattern…</Faint>
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div style={box} data-testid="diagnosis-failed">
        <Faint>The pattern analysis for this answer did not complete; your grade above stands.</Faint>
      </div>
    );
  }
  if (!card || card.cardEnabled === false) return null;
  const escalation = card.escalation ?? null;
  const escalatedRepair = escalation?.repair ?? null;
  // The escalated repair is shown in its own block, not again in the list.
  const repairs = (card.repairSuggestions ?? []).filter(
    (repair) => !(escalatedRepair?.id && repair.id === escalatedRepair.id),
  );
  const madeBefore = card.madeBefore ?? [];
  const disowned = new Set(card.notSameMistakeAttemptIds ?? []);
  return (
    <div style={box} data-testid="diagnosis-card">
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <Pill tone="cyan">diagnosis</Pill>
        <Faint>why this went wrong, across your answers</Faint>
      </div>
      {escalation ? (
        <div
          style={{ marginBottom: 10, paddingBottom: 8, borderBottom: `1px solid ${COLOR.border}` }}
          data-testid="diagnosis-escalation"
        >
          <div style={{ color: COLOR.text, fontWeight: 600 }} data-testid="escalation-headline">
            {escalation.headline}
          </div>
          {escalation.earlierAnswers.length > 0 ? (
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "baseline" }}>
              <Faint>earlier answers</Faint>
              {escalation.earlierAnswers.map((answer) => (
                <span
                  key={answer.attemptId}
                  style={link}
                  onClick={() => onOpenAttempt?.(answer.attemptId)}
                  data-testid="escalation-earlier-answer"
                >
                  {fmtDay(answer.date)}
                </span>
              ))}
            </div>
          ) : null}
          {escalatedRepair ? (
            <div data-testid="escalation-repair">
              <div style={{ color: COLOR.text }}>· {escalatedRepair.rationale}</div>
              {escalatedRepair.representation || escalatedRepair.practiceMode ? (
                <div data-testid="escalation-repair-mode">
                  <Faint>
                    {[escalatedRepair.representation, escalatedRepair.practiceMode]
                      .filter((value) => value && value !== "unspecified")
                      .join(" · ")}
                  </Faint>
                </div>
              ) : null}
              {escalatedRepair.elicitingQuestion?.trim() ? (
                <div style={{ color: COLOR.text }} data-testid="escalation-repair-question">
                  {escalatedRepair.elicitingQuestion}{" "}
                  <Faint>(answer it in "one question, unaided" below)</Faint>
                </div>
              ) : null}
            </div>
          ) : null}
          {escalation.approachNote ? <Faint>{escalation.approachNote}</Faint> : null}
          <div style={{ marginTop: 6, display: "flex", gap: 14, flexWrap: "wrap" }} data-testid="escalation-taps">
            <Faint>was this repair useful?</Faint>
            {escalation.responses.map((option) => {
              const chosen = escalation.recordedResponse === option.response;
              const done = escalation.recordedResponse != null;
              return (
                <span
                  key={option.response}
                  data-testid={`escalation-tap-${option.response.split(":")[1]}`}
                  style={
                    done
                      ? { color: chosen ? COLOR.text : COLOR.textFaint, fontWeight: chosen ? 600 : 400 }
                      : { ...link, color: COLOR.textDim }
                  }
                  onClick={done ? undefined : () => void record(option.response)}
                >
                  {option.label}
                </span>
              );
            })}
          </div>
        </div>
      ) : null}
      {card.summaryMd ? (
        <div style={{ color: COLOR.text, whiteSpace: "pre-wrap" }} data-testid="diagnosis-summary">
          {card.summaryMd}
        </div>
      ) : null}
      {repairs.length > 0 ? (
        <div style={{ marginTop: 8 }} data-testid="diagnosis-repairs">
          <Faint>repair</Faint>
          {repairs.map((repair, index) => (
            <div key={index} style={{ color: COLOR.text }}>
              · {repair.rationale}
            </div>
          ))}
        </div>
      ) : null}
      {madeBefore.length > 0 ? (
        <div style={{ marginTop: 8 }} data-testid="diagnosis-made-before">
          <Faint>You've made this mistake before</Faint>
          {madeBefore.map((citation) => (
            <div key={citation.attemptId} style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
              <span
                style={link}
                onClick={() => onOpenAttempt?.(citation.attemptId)}
                data-testid="diagnosis-citation"
              >
                {fmtDay(citation.date)}
              </span>
              {citation.quote ? <span style={{ color: COLOR.textDim }}>“{citation.quote}”</span> : null}
              {disowned.has(citation.attemptId) ? (
                <Faint>noted: not the same</Faint>
              ) : (
                <span
                  style={{ ...link, color: COLOR.textDim }}
                  onClick={() => void record("not_same_mistake", citation.attemptId)}
                >
                  not the same mistake
                </span>
              )}
            </div>
          ))}
        </div>
      ) : null}
      {card.prerequisiteGap ? (
        <div style={{ marginTop: 8 }} data-testid="diagnosis-prerequisite">
          <Pill tone="slate">{card.prerequisiteGap.label}</Pill>{" "}
          <span style={{ color: COLOR.text }}>{card.prerequisiteGap.title}</span>
        </div>
      ) : null}
      <div style={{ marginTop: 10, display: "flex", gap: 14, flexWrap: "wrap" }} data-testid="diagnosis-taps">
        {card.responses.map((option) => {
          const chosen = card.recordedResponse === option.response;
          const done = card.recordedResponse != null;
          return (
            <span
              key={option.response}
              data-testid={`diagnosis-tap-${option.response}`}
              style={
                done
                  ? { color: chosen ? COLOR.text : COLOR.textFaint, fontWeight: chosen ? 600 : 400 }
                  : { ...link, color: COLOR.textDim }
              }
              onClick={done ? undefined : () => void record(option.response)}
            >
              {option.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
