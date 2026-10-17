// Active reading's card in the rail (reader workbench RW1b; spec §4.2; UX §4.3,
// §4.10): the question, the learner's answer box, the book's (or the model's)
// answer beside theirs, the three-way self-check, "reconstruct this later"'s
// receipt with undo, and "another way to see this". Formative only: no grade,
// no attempt; the voices say whose words each line is (W2).
import { useState } from "react";
import type { InquirySelfCheck } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { PrimaryButton, SecondaryButton } from "../../components/goldenpath/shared";
import { MarkdownMath } from "../../render/MarkdownMath";
import { ModelActionState } from "./ModelActionState";
import type { ActiveReadingController } from "./useActiveReading";
import { LearnerVoice, MeaningLabel, ModelVoice, SourceVoice } from "./voices";

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

export const ACTIVE_COPY = {
  next_step: { title: "let me try the next step", box: "Your next step", verb: "writing the question" },
  why_step: { title: "why does this step work?", box: "Your answer", verb: "writing the question" },
  assumptions: { title: "what does this assume?", box: "Your answer", verb: "writing the question" },
  reconstruct: { title: "reconstruct this later", box: "Your answer", verb: "writing the question" },
  formative: "formative · never a grade",
  whereThisGoes: "Kept with this passage. If your answer differed from the book's, LearnLoop's model may read it to name a gap — never to grade you.",
  missed: "Kept with this passage for a second look — never a grade.",
  reconstructDone: "Added to your practice: later you'll be asked to rebuild this derivation without the book.",
  reconstructUndone: "Undone: it won't be asked.",
  addToPractice: "add to practice",
  addedToPractice: "Added to your practice: you'll be asked this later, on your own.",
  addingToPractice: "adding it to your practice",
  notLinked: "This passage isn't linked to a learning objective yet, so it can't become practice.",
  foldedOne: "the next line is folded while you try",
  foldedMany: (n: number) => `the next ${n} lines are folded while you try`,
  writingFolded: "writing the question — the lines stay folded",
} as const;

export function foldLine(count: number): string {
  return count === 1 ? ACTIVE_COPY.foldedOne : ACTIVE_COPY.foldedMany(count);
}

/** The fold's dotted rule with "show" (UX S5), shared by the text view and a
 *  video's transcript so every source kind folds the same way. */
export function NextStepFoldLine({ ctl }: { ctl: ActiveReadingController }) {
  return (
    <div
      style={{ borderTop: `1px dotted ${COLOR.textDim}`, paddingTop: 4, display: "flex", gap: 8, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}
    >
      <span>{foldLine(ctl.folded.size)}</span>
      <span aria-hidden="true">·</span>
      <button
        type="button"
        onClick={ctl.unfold}
        style={{ border: 0, background: "transparent", color: COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 2 }}
      >
        show
      </button>
      {ctl.active?.phase === "pending" ? (
        <span style={{ marginLeft: 8 }}><span aria-hidden="true">◐</span> {ACTIVE_COPY.writingFolded}</span>
      ) : null}
    </div>
  );
}

export function ActiveReadingCard({ ctl, sourceTitle, onShowPassage }: {
  ctl: ActiveReadingController;
  sourceTitle: string | null;
  onShowPassage?: (spanId: string) => void;
}) {
  if (ctl.another) return <AnotherWayCard ctl={ctl} sourceTitle={sourceTitle} />;
  const active = ctl.active;
  if (!active) return null;
  const copy = ACTIVE_COPY[active.style];
  const question = active.question;
  return (
    <section aria-label={copy.title} data-active-reading={active.style} style={{ display: "flex", flexDirection: "column", gap: 8, padding: "6px 0 10px", borderBottom: `1px solid ${COLOR.border}` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <MeaningLabel>{copy.title} · {ACTIVE_COPY.formative}</MeaningLabel>
        <button type="button" onClick={ctl.close} style={{ ...linkStyle, marginLeft: "auto" }}>close</button>
      </div>
      {!question || active.phase !== "landed" ? (
        <ModelActionState
          phase={active.phase}
          verb={copy.verb}
          failure={active.failure ?? "Couldn't write the question."}
          kept="The book is unchanged."
          capRoute="quick check"
          fallback="Reading, highlights and Ask"
          onCancel={ctl.close}
          onRetry={ctl.retry}
        />
      ) : question.status === "dismissed" ? (
        <MeaningLabel>You set this aside; it won’t come back.</MeaningLabel>
      ) : (
        <QuestionBody key={active.key} ctl={ctl} sourceTitle={sourceTitle} onShowPassage={onShowPassage} />
      )}
    </section>
  );
}

function QuestionBody({ ctl, sourceTitle, onShowPassage }: {
  ctl: ActiveReadingController;
  sourceTitle: string | null;
  onShowPassage?: (spanId: string) => void;
}) {
  const active = ctl.active!;
  const question = active.question!;
  const copy = ACTIVE_COPY[active.style];
  const [response, setResponse] = useState("");
  const answered = question.status === "answered" || question.status === "escalated";
  const escalated = question.status === "escalated";
  const fromBook = question.answerBasis === "source";
  if (active.style === "reconstruct") {
    return (
      <>
        <ModelVoice first note="a question for later">
          <MarkdownMath value={question.questionMd} />
        </ModelVoice>
        {active.reconstruct.phase === "pending" ? (
          <ModelActionState phase="pending" verb="adding it to your practice" />
        ) : active.reconstruct.phase === "done" ? (
          <MeaningLabel>
            {ACTIVE_COPY.reconstructDone}{" "}
            <button type="button" onClick={() => void ctl.undoReconstruct()} style={linkStyle}>undo</button>
          </MeaningLabel>
        ) : active.reconstruct.phase === "undone" ? (
          <MeaningLabel>{active.reconstruct.message ?? ACTIVE_COPY.reconstructUndone}</MeaningLabel>
        ) : active.reconstruct.phase === "failed" ? (
          <MeaningLabel>{active.reconstruct.message}</MeaningLabel>
        ) : null}
      </>
    );
  }
  return (
    <>
      <ModelVoice first note="a question on this passage">
        <MarkdownMath value={question.questionMd} />
      </ModelVoice>
      {!answered ? (
        <>
          <textarea
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Write it in your own words…"
            aria-label={copy.box}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && response.trim()) void ctl.answer(response.trim());
            }}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 56, resize: "vertical" }}
          />
          <MeaningLabel style={{ fontSize: 10 }}>ⓘ {ACTIVE_COPY.whereThisGoes}</MeaningLabel>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <PrimaryButton onClick={() => void ctl.answer(response.trim())} disabled={active.busy || !response.trim()}>
              {fromBook ? "compare with the book ^↵" : "compare with the model's answer ^↵"}
            </PrimaryButton>
            <SecondaryButton onClick={() => void ctl.showMe()} disabled={active.busy}>show me</SecondaryButton>
          </div>
        </>
      ) : (
        <>
          {question.responseMd ? (
            <LearnerVoice>
              <MarkdownMath value={question.responseMd} />
            </LearnerVoice>
          ) : null}
          {fromBook ? (
            <SourceVoice source={sourceTitle} locator={active.style === "next_step" ? "the next step" : null}>
              <MarkdownMath value={question.expectedAnswerMd} />
            </SourceVoice>
          ) : (
            <ModelVoice note={active.style === "assumptions" ? "model's list of assumptions" : "model's justification"}>
              <MarkdownMath value={question.expectedAnswerMd} />
            </ModelVoice>
          )}
          {question.selfCheck ? (
            <MeaningLabel>
              you said: {question.selfCheck}
              {question.missed ? ` · ${ACTIVE_COPY.missed}` : " · noted, never a grade"}
            </MeaningLabel>
          ) : escalated ? null : (
            <div role="group" aria-label="How did yours compare?" style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <MeaningLabel>how did yours compare?</MeaningLabel>
              {(["matches", "partly", "no"] as InquirySelfCheck[]).map((value) => (
                <button key={value} type="button" disabled={active.busy} onClick={() => void ctl.selfCheck(value)} style={linkStyle}>
                  {value}
                </button>
              ))}
            </div>
          )}
        </>
      )}
      {answered ? <PracticeLine ctl={ctl} /> : null}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {onShowPassage && question.anchorSpanIds[0] ? (
          <button type="button" onClick={() => onShowPassage(question.anchorSpanIds[0])} style={linkStyle}>show the passage</button>
        ) : null}
        {escalated ? null : (
          <button type="button" disabled={active.busy} onClick={ctl.dismiss} style={linkStyle}>don’t bring this back</button>
        )}
      </div>
    </>
  );
}

/** "add to practice" (spec §4.2): the answered question becomes one practice
 *  item through the quick check's own escalation; answering alone makes none. */
function PracticeLine({ ctl }: { ctl: ActiveReadingController }) {
  const active = ctl.active!;
  const question = active.question!;
  if (question.status === "escalated" || active.practice.phase === "done") {
    return <MeaningLabel>{ACTIVE_COPY.addedToPractice}</MeaningLabel>;
  }
  if (active.practice.phase === "pending") return <ModelActionState phase="pending" verb={ACTIVE_COPY.addingToPractice} />;
  if (!question.escalationLearningObjectId) return <MeaningLabel style={{ fontSize: 10 }}>{ACTIVE_COPY.notLinked}</MeaningLabel>;
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
      <button type="button" disabled={active.busy} onClick={() => void ctl.addToPractice()} style={linkStyle}>{ACTIVE_COPY.addToPractice}</button>
      {active.practice.phase === "failed" && active.practice.message ? <MeaningLabel style={{ fontSize: 10 }}>{active.practice.message}</MeaningLabel> : null}
    </div>
  );
}

function AnotherWayCard({ ctl, sourceTitle }: { ctl: ActiveReadingController; sourceTitle: string | null }) {
  const another = ctl.another!;
  return (
    <section aria-label="another way to see this" style={{ display: "flex", flexDirection: "column", gap: 8, padding: "6px 0 10px", borderBottom: `1px solid ${COLOR.border}` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <MeaningLabel>another way to see this · from your books</MeaningLabel>
        <button type="button" onClick={ctl.closeAnother} style={{ ...linkStyle, marginLeft: "auto" }}>close</button>
      </div>
      {another.phase !== "landed" ? (
        <ModelActionState
          phase={another.phase}
          verb="looking in your books"
          failure={another.failure ?? "Couldn't look in your books."}
          kept="The book is unchanged."
          capRoute="checking your books"
          fallback="Reading, highlights and Ask"
          onCancel={ctl.closeAnother}
          onRetry={ctl.retryAnother}
        />
      ) : another.hits.length === 0 ? (
        <MeaningLabel>Nothing in your books treats this differently yet.</MeaningLabel>
      ) : (
        another.hits.map((hit) => {
          const otherBook = Boolean(hit.sourceId && ctl.sourceId && hit.sourceId !== ctl.sourceId);
          const label = otherBook ? "from a different book" : hit.role === "worked_example" ? "a worked example instead" : "elsewhere in this book";
          return (
            <div key={`${hit.extractionId}:${hit.spanId}`} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <MeaningLabel style={{ fontSize: 10 }}>{label}</MeaningLabel>
              <SourceVoice source={hit.sourceTitle ?? (otherBook ? null : sourceTitle)}>
                <MarkdownMath value={hit.text} />
              </SourceVoice>
              {hit.rationale ? (
                <ModelVoice note="why this one">{hit.rationale}</ModelVoice>
              ) : null}
            </div>
          );
        })
      )}
    </section>
  );
}
