// UX Phase 4.2: the feedback surface (docs/specs/ux_learnloop_v1.md §7.5, W5b).
//
// Was I right? What does a full answer look like next to mine? What is the one
// thing to do now? Then Next. The surface holds a verdict in words, the
// question, the learner's answer beside a full answer, the criteria as plain
// ✓ / ✗ lines, one sentence on what went wrong (the diagnosis when it lands,
// the grader's note until then, updated in place), ONE next step and Next.
// Everything else (the score in numbers, what the grader looked for, the
// diagnosis, causal attribution, provenance) is one click away, behind
// "details ▸", which the screen renders below.
//
// A grade held for review is the grader's provisional score and counts for
// nothing: it says "Held for review" and never shows a score.
//
// The question is the one the learner was given. The full answer and the
// criteria are the ones the grade stands on: the assessment contract its
// grading epoch cites when the bundle carries it (Codex review F5), never
// today's key beside an older grade, nor the original key beside a regrade
// that read the corrected item (re-review F9). Showing the full answer is an
// exposure: the screen charges the reveal ledger on every visit
// (`onFullAnswerShown`, Codex review F1, re-review F1).
import { useRef, useEffect } from "react";
import type { CriterionEvidenceRowDto, FeedbackBundle, PracticeItemDetail } from "../../api/dto";
import { criterionAssessed } from "../../api/dto";
import type { DiagnosisCardState } from "../../components/DiagnosisCard";
import { ItemPresentation } from "../../components/ItemPresentation";
import { DetailsToggle, PrimaryAction, QuietAction, VoicePanel, quietLine, quietLink } from "../../components/PlainParts";
import { COLOR } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import {
  expectedAnswerText,
  type FeedbackOrigin,
  ORIGIN_LABEL,
  VERDICT_TEXT,
  type Verdict
} from "../../app/practiceFeedback";

/** The one next step the surface offers besides Next (§7.5). */
export interface FeedbackNextStep {
  label: string;
  busy?: boolean;
  onRun: () => void;
}

/** "I think I was right": a one-line box, and the regrade in place. */
export interface FeedbackContest {
  available: boolean;
  open: boolean;
  reason: string;
  busy: boolean;
  note: string | null;
  onOpen: () => void;
  onCancel: () => void;
  onReason: (reason: string) => void;
  onSend: () => void;
}

export interface FeedbackWhy {
  open: boolean;
  onToggle: () => void;
  causes: string[];
  showed: string[];
  mechanism: string | null;
  madeBefore: { attemptId: string; date: string | null; quote: string | null }[];
  /** "this doesn't sound right": the single diagnosis verdict. */
  onNotRight: (() => void) | null;
  notRightRecorded: boolean;
}

function fmtDay(iso: string | null): string {
  if (!iso) return "earlier";
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? "earlier"
    : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** The full answer the grade stands on: the key of the contract its grading
 *  epoch cites when the bundle carries one, else the item's (an answer graded
 *  before contracts, or regraded under the item as it is now: Codex
 *  re-review F9). */
export function answeredFullAnswer(f: FeedbackBundle, item: PracticeItemDetail | null): string {
  const frozen = f.answeredExpectedAnswer;
  if (frozen !== undefined && frozen !== null) return expectedAnswerText(frozen).trim();
  return item ? expectedAnswerText(item.expectedAnswer).trim() : "";
}

/** The criteria rows with the descriptions and points the grading contract
 *  froze (Codex review F5); a criterion the contract does not name keeps the
 *  row's own. Matched on the id each frozen row carries (re-review F8). */
export function answeredCriterionRows(f: FeedbackBundle): CriterionEvidenceRowDto[] {
  const frozen = f.answeredCriteria;
  if (!frozen) return f.criterionEvidence;
  const byId = new Map(frozen.map((criterion) => [criterion.criterionId, criterion]));
  return f.criterionEvidence.map((row) => {
    const criterion = byId.get(row.criterionId);
    return criterion
      ? { ...row, criterionDescription: criterion.description, pointsPossible: criterion.pointsPossible }
      : row;
  });
}

/** The maximum the grade is out of: the grading contract's when the bundle
 *  carries one (re-review F9), else the bundle's (the item's rubric). */
export function answeredMaxPoints(f: FeedbackBundle): number {
  return typeof f.answeredMaxPoints === "number" ? f.answeredMaxPoints : f.maxPoints;
}

/** The quiet honesty lines that qualify the grade, in a few plain words. */
function honestyLines(f: FeedbackBundle): string[] {
  const lines: string[] = [];
  if (f.autoPrimed) {
    lines.push("Counted as practice with help: the tutor had already shown part of this answer.");
  } else if (f.primed) {
    lines.push("◌ Practice with help.");
  }
  const check = f.coldCheckResult;
  if (check) {
    const when = fmtDay(check.instructedAt);
    lines.push(
      check.claim === "repair_confirmed"
        ? `This was the check on your own for the fix from ${when}: it held.`
        : check.claim === "escalated_unrepaired"
          ? `This was the check on your own for the fix from ${when}: it didn't hold yet, so the fix comes back with more support.`
          : check.claim === "downgraded"
            ? `This was the check on your own for the fix from ${when}: it's recorded, but it can't confirm the fix. Another check comes later.`
            : `This was the check on your own for the fix from ${when}: no verdict this time.`
    );
  }
  return lines;
}

export function FeedbackSurface({
  feedback: f,
  item,
  verdict,
  origin,
  diagnosis,
  matchedCorrection,
  onBack,
  nextLabel,
  advancing,
  onNext,
  step,
  contest,
  why,
  provisional,
  onShowProvisional,
  detailsOpen,
  onToggleDetails,
  onFullAnswerShown
}: {
  feedback: FeedbackBundle;
  item: PracticeItemDetail | null;
  verdict: Verdict;
  origin: FeedbackOrigin;
  diagnosis: DiagnosisCardState;
  /** A matched mix-up's authored correction, when one is matched. */
  matchedCorrection: string | null;
  onBack: () => void;
  /** Where Next goes (the plan's next step, the next item, the book). */
  nextLabel: string;
  advancing: boolean;
  onNext: () => void;
  step: FeedbackNextStep | null;
  contest: FeedbackContest;
  why: FeedbackWhy;
  provisional: boolean;
  onShowProvisional: () => void;
  detailsOpen: boolean;
  onToggleDetails: () => void;
  /** The full answer is on screen (once per attempt and answer). */
  onFullAnswerShown?: () => void;
}) {
  const held = verdict === "held";
  const presentation = f.answeredPresentation ?? item?.presentation ?? null;
  const fullAnswer = answeredFullAnswer(f, item);
  const criteria = answeredCriterionRows(f);
  const learnerAnswer = (f.learnerAnswerMd ?? "").trim();
  const shownCallback = useRef(onFullAnswerShown);
  shownCallback.current = onFullAnswerShown;
  useEffect(() => {
    if (fullAnswer) shownCallback.current?.();
  }, [f.attemptId, fullAnswer]);
  const diagnosisSummary =
    diagnosis.status === "done" && diagnosis.card?.cardEnabled !== false ? diagnosis.card?.summaryMd?.trim() || null : null;
  const sentence = diagnosisSummary
    ?? (matchedCorrection ? `You may be mixing two ideas up. ${matchedCorrection}` : null)
    ?? (f.feedbackMd?.trim() || null);
  const prerequisite = diagnosis.status === "done" ? diagnosis.card?.prerequisiteGap ?? null : null;
  const whyHasContent =
    why.causes.length > 0 ||
    why.showed.length > 0 ||
    Boolean(why.mechanism) ||
    why.madeBefore.length > 0 ||
    why.onNotRight !== null ||
    why.notRightRecorded;
  const contestBox = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (contest.open) contestBox.current?.focus();
  }, [contest.open]);
  const tone = verdict === "right" ? COLOR.green : verdict === "partly" ? COLOR.amber : COLOR.text;

  return (
    <div style={{ maxWidth: 900 }} data-testid="feedback-surface">
      {/* The header: where the attempt came from, and the topic. */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 16, fontSize: 13 }}>
        <button type="button" onClick={onBack} style={{ ...quietLink, fontSize: 13, color: COLOR.amberLink }}>
          ← {ORIGIN_LABEL[origin]}
        </button>
        <span style={{ flex: 1 }} />
        <span style={{ color: COLOR.textDim }}>{f.learningObjectTitle}</span>
      </div>

      {/* The verdict in words, and who graded it. */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap" }}>
        <div style={{ fontSize: 24, fontWeight: 600, color: tone }} data-testid="feedback-verdict">
          {VERDICT_TEXT[verdict]}
        </div>
        <span style={{ flex: 1 }} />
        {f.gradingSource === "self" ? (
          <span style={quietLine}>graded by you</span>
        ) : (
          <span style={{ ...quietLine, display: "inline-flex", gap: 6, alignItems: "baseline" }}>
            <span>◇ graded by AI</span>
            {contest.available && !contest.open ? (
              <>
                <span aria-hidden="true">·</span>
                <button type="button" style={quietLink} onClick={contest.onOpen}>I think I was right ▸</button>
              </>
            ) : null}
          </span>
        )}
      </div>
      {held ? (
        <div style={{ ...quietLine, marginTop: 6 }}>
          The grader couldn't check the way you answered, so this answer doesn't count either way until it's reviewed.
        </div>
      ) : null}
      {provisional ? (
        <div style={{ marginTop: 6 }}>
          <button type="button" style={quietLink} onClick={onShowProvisional}>
            This grade may change after one question ▸
          </button>
        </div>
      ) : null}
      {honestyLines(f).map((line) => (
        <div key={line} style={{ ...quietLine, marginTop: 4 }}>{line}</div>
      ))}

      {/* "I think I was right": one line, the regrade in place. */}
      {contest.open ? (
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 10, flexWrap: "wrap" }}>
          <input
            ref={contestBox}
            className="text-input"
            aria-label="Why you think you were right (optional)"
            placeholder="Why? One line, optional"
            value={contest.reason}
            disabled={contest.busy}
            onChange={(event) => contest.onReason(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                contest.onSend();
              } else if (event.key === "Escape") {
                event.preventDefault();
                contest.onCancel();
              }
            }}
            style={{ flex: "1 1 320px", fontSize: 13 }}
          />
          <QuietAction onClick={contest.onSend} disabled={contest.busy}>
            {contest.busy ? "Looking again…" : "Look again"}
          </QuietAction>
          <button type="button" style={quietLink} onClick={contest.onCancel} disabled={contest.busy}>never mind</button>
        </div>
      ) : null}
      {contest.note ? <div style={{ ...quietLine, marginTop: 8 }} role="status">{contest.note}</div> : null}

      {/* The question, as it was given. */}
      {presentation ? (
        <div style={{ marginTop: 16, color: COLOR.textDim, fontSize: 13 }} data-testid="feedback-question">
          <ItemPresentation presentation={presentation} />
        </div>
      ) : null}

      {/* The learner's answer beside a full answer. */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 12,
          marginTop: 14
        }}
      >
        <VoicePanel mark="›" title="You wrote">
          {learnerAnswer ? <MarkdownMath value={learnerAnswer} /> : <span style={{ color: COLOR.textDim }}>(nothing written)</span>}
          {f.learnerExplanationMd ? (
            <div style={{ marginTop: 6, color: COLOR.textDim, fontSize: 12 }}>
              Why: <MarkdownMath value={f.learnerExplanationMd} />
            </div>
          ) : null}
        </VoicePanel>
        {fullAnswer ? (
          <VoicePanel mark="◇" title="A full answer">
            <MarkdownMath value={fullAnswer} />
          </VoicePanel>
        ) : null}
      </div>

      {/* The criteria as plain ✓ / ✗ lines; a criterion the answer's route
          never exercised is a quiet "·" line. */}
      {!held && criteria.length > 0 ? (
        <div style={{ marginTop: 14, display: "grid", gap: 4, fontSize: 13 }}>
          {criteria.map((row) => {
            const assessed = criterionAssessed(row);
            const full = row.pointsAwarded >= row.pointsPossible;
            const some = row.pointsAwarded > 0;
            const mark = !assessed ? "·" : full ? "✓" : some ? "◐" : "✗";
            const color = !assessed ? COLOR.textFaint : full ? COLOR.green : some ? COLOR.amber : COLOR.red;
            return (
              <div key={row.criterionId} data-criterion={row.criterionId} style={{ display: "flex", gap: 10 }}>
                <span aria-hidden="true" style={{ color, width: 14, textAlign: "center" }}>{mark}</span>
                <span style={{ color: assessed ? COLOR.text : COLOR.textDim }}>
                  {row.criterionDescription}
                  {!assessed ? <span style={{ color: COLOR.textFaint }}> · not judged</span> : null}
                </span>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* One sentence on what went wrong; it updates in place when the
          diagnosis lands. */}
      {sentence || prerequisite || (whyHasContent && verdict !== "right") ? (
        <div style={{ marginTop: 14, fontSize: 13, lineHeight: 1.6, color: COLOR.text }} data-testid="feedback-sentence">
          {sentence ? <MarkdownMath value={sentence} /> : null}
          {prerequisite ? <div style={{ marginTop: 4 }}>This needs {prerequisite.title} first.</div> : null}
          {whyHasContent ? (
            <div style={{ marginTop: 4 }}>
              <DetailsToggle open={why.open} onToggle={why.onToggle} label="why?" />
            </div>
          ) : null}
        </div>
      ) : null}
      {why.open && whyHasContent ? (
        <div style={{ marginTop: 8, padding: "10px 14px", borderLeft: `2px solid ${COLOR.border}`, ...quietLine }}>
          {why.causes.length > 0 ? (
            <div>
              <div>Possible causes</div>
              {why.causes.map((cause) => <div key={cause} style={{ color: COLOR.text }}>· {cause}</div>)}
            </div>
          ) : null}
          {why.showed.length > 0 ? (
            <div style={{ marginTop: 6 }}>
              <div>What you already showed</div>
              {why.showed.map((line) => <div key={line} style={{ color: COLOR.text }}>✓ {line}</div>)}
            </div>
          ) : null}
          {why.mechanism ? (
            <div style={{ marginTop: 6 }}>How it happens: <span style={{ color: COLOR.text }}>{why.mechanism}</span></div>
          ) : null}
          {why.madeBefore.length > 0 ? (
            <div style={{ marginTop: 6 }}>
              <div>You've made this mistake before</div>
              {why.madeBefore.map((citation) => (
                <div key={citation.attemptId}>
                  {fmtDay(citation.date)}
                  {citation.quote ? <span style={{ color: COLOR.text }}> “{citation.quote}”</span> : null}
                </div>
              ))}
            </div>
          ) : null}
          {why.onNotRight || why.notRightRecorded ? (
            <div style={{ marginTop: 8 }}>
              {why.notRightRecorded || !why.onNotRight ? (
                <span>Noted. Thanks.</span>
              ) : (
                <button type="button" style={quietLink} onClick={why.onNotRight}>this doesn't sound right</button>
              )}
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Next, the one next step, and details. */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 20, flexWrap: "wrap" }}>
        <PrimaryAction hotkey="↵" onClick={onNext} disabled={advancing}>
          {advancing ? "Opening…" : "Next"}
        </PrimaryAction>
        {step ? (
          <QuietAction onClick={step.onRun} disabled={step.busy}>
            {step.busy ? "One moment…" : step.label}
          </QuietAction>
        ) : null}
        <span style={{ ...quietLine, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {nextLabel}
        </span>
        <span style={{ flex: 1 }} />
        <DetailsToggle open={detailsOpen} onToggle={onToggleDetails} />
      </div>
    </div>
  );
}
