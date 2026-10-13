// The reconnect line's quick check (reader workbench RW1a; spec §4.1, D43).
//
// One formative question about the inquiry's root passage, written by the
// quick-check producer in the background. The learner answers in their own
// words, then sees the intended answer beside theirs and says how it went:
// matches · partly · no. Never an attempt and never a grade; "add to
// practice" makes it a practice item through the existing escalation. Named
// "quick check", never "check me" (which always means an attempt on your own).
import { useState } from "react";
import type { InquirySelfCheck, ReaderInquiryQuestionDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { PrimaryButton, SecondaryButton } from "../../components/goldenpath/shared";
import { MarkdownMath } from "../../render/MarkdownMath";
import { LearnerVoice, MeaningLabel, ModelVoice } from "./voices";
import { ModelActionState, type ModelActionPhase } from "./ModelActionState";

const linkStyle = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 10,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
} as const;

export interface InquiryQuickCheckProps {
  phase: ModelActionPhase;
  question: ReaderInquiryQuestionDto | null;
  busy?: boolean;
  onAnswer: (response: string) => void;
  onSelfCheck: (value: InquirySelfCheck) => void;
  onDismiss: () => void;
  onEscalate?: () => void;
  escalated?: boolean;
  onRetry?: () => void;
  onShowPassage?: (spanId: string) => void;
}

export function InquiryQuickCheck({
  phase,
  question,
  busy = false,
  onAnswer,
  onSelfCheck,
  onDismiss,
  onEscalate,
  escalated = false,
  onRetry,
  onShowPassage,
}: InquiryQuickCheckProps) {
  const [response, setResponse] = useState("");
  if (!question || phase !== "landed") {
    return (
      <ModelActionState
        phase={phase}
        verb="writing a quick check on this passage"
        failure="Couldn't write a quick check."
        kept="Your inquiry is unchanged."
        capRoute="quick check"
        fallback="Your threads and the passage"
        onRetry={onRetry}
      />
    );
  }
  if (question.status === "dismissed") return null;
  const answered = question.status === "answered" || question.status === "escalated";
  return (
    <section aria-label="Quick check" data-inquiry-check={question.id} style={{ display: "flex", flexDirection: "column", gap: 8, padding: "8px 0", borderTop: `1px solid ${COLOR.border}` }}>
      <MeaningLabel>quick check · optional · formative, never a grade</MeaningLabel>
      <ModelVoice first note="a quick check on this passage">
        <MarkdownMath value={question.questionMd} />
      </ModelVoice>
      {!answered ? (
        <>
          <textarea
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Answer in your own words…"
            aria-label="Your answer"
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && response.trim()) onAnswer(response.trim());
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 64, resize: "vertical" }}
          />
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <PrimaryButton onClick={() => onAnswer(response.trim())} disabled={busy || !response.trim()}>compare with the source ^↵</PrimaryButton>
            <SecondaryButton onClick={onDismiss} disabled={busy}>not now</SecondaryButton>
          </div>
        </>
      ) : (
        <>
          <LearnerVoice>
            <MarkdownMath value={question.responseMd ?? ""} />
          </LearnerVoice>
          <ModelVoice note="the intended answer · compare, don't grade">
            <MarkdownMath value={question.expectedAnswerMd} />
          </ModelVoice>
          {question.selfCheck ? (
            <MeaningLabel>you said: {question.selfCheck === "matches" ? "matches" : question.selfCheck === "partly" ? "partly" : "no"} · noted, never a grade</MeaningLabel>
          ) : (
            <div role="group" aria-label="How did your answer compare?" style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <MeaningLabel>how did yours compare?</MeaningLabel>
              {(["matches", "partly", "no"] as InquirySelfCheck[]).map((value) => (
                <button key={value} type="button" disabled={busy} onClick={() => onSelfCheck(value)} style={linkStyle}>
                  {value}
                </button>
              ))}
            </div>
          )}
          {escalated ? (
            <MeaningLabel style={{ color: COLOR.green }}>✓ added to your practice</MeaningLabel>
          ) : onEscalate && question.escalationLearningObjectId ? (
            <span><button type="button" disabled={busy} onClick={onEscalate} style={linkStyle}>add to practice →</button></span>
          ) : null}
        </>
      )}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {onShowPassage && question.spanIds[0] ? (
          <button type="button" onClick={() => onShowPassage(question.spanIds[0])} style={linkStyle}>show the passage</button>
        ) : null}
        <button type="button" disabled={busy} onClick={onDismiss} style={linkStyle}>don’t bring this back</button>
      </div>
    </section>
  );
}
