// Reader workbench RW4b: the candidate card (spec §7.4; UX §4.6), shared by
// every Reader surface that lists practice proposals (RW4a's "practice this
// question" today; RW1c's tutor offers at the landing, one line).
//
// Each card: the exercise's own words (a § source passage, verbatim, never its
// solution), source and page, the honest line (verbatim · the answer is
// completed by LearnLoop's model · the key's status), the exposure label when
// the sources service's rule marks it (then "use this one" is practice beside
// the book, never a check on your own), "open in the book" and "use this one".
// Nothing here takes focus, animates or opens a modal.
import type { CSSProperties } from "react";
import { COLOR, FONT_MONO } from "../../components/term";
import { MarkdownMath } from "../../render/MarkdownMath";
import { EXERCISE_COPY, exerciseLocator, keyStatusLine, type ExerciseCandidate } from "./exerciseCandidates";
import { MeaningLabel, SourceVoice } from "./voices";

const linkStyle: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 10,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
};

function clip(text: string, limit = 600): string {
  const flat = text.split(/\s+/).join(" ").trim();
  return flat.length <= limit ? flat : `${flat.slice(0, limit - 1).trimEnd()}…`;
}

export function ExerciseCandidates({
  candidates,
  onUse,
  onOpenInBook,
  opening = null,
}: {
  candidates: ExerciseCandidate[];
  /** "Use this one": a learner pick; the workbench opens at once on the stem. */
  onUse: ((candidate: ExerciseCandidate) => void) | null;
  /** Open the exercise's page (a detour: Alt+← comes back). */
  onOpenInBook: ((candidate: ExerciseCandidate) => void) | null;
  /** The candidate whose problem is opening now. */
  opening?: string | null;
}) {
  if (candidates.length === 0) return null;
  return (
    <ul aria-label="exercises from your books" style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
      {candidates.map((candidate) => (
        <li key={candidate.key} data-testid="exercise-candidate" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <SourceVoice source={null} locator={exerciseLocator(candidate) || null}>
            <MarkdownMath value={clip(candidate.statement)} />
          </SourceVoice>
          <MeaningLabel style={{ fontSize: 10 }}>{keyStatusLine(null)}</MeaningLabel>
          {candidate.exposure.exposed && candidate.exposure.label ? (
            <MeaningLabel style={{ fontSize: 11 }}>
              <span aria-hidden="true">◌ </span>
              {candidate.exposure.label} · {EXERCISE_COPY.practiceNotCheck}
            </MeaningLabel>
          ) : candidate.exposure.note ? (
            <MeaningLabel style={{ fontSize: 11 }}>
              <span aria-hidden="true">◌ </span>
              {candidate.exposure.note}
            </MeaningLabel>
          ) : null}
          <span style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "baseline" }}>
            {onOpenInBook ? (
              <button type="button" style={linkStyle} onClick={() => onOpenInBook(candidate)}>
                {EXERCISE_COPY.openInBook} ↗
              </button>
            ) : null}
            {onUse ? (
              opening === candidate.key ? (
                <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>opening…</span>
              ) : (
                <button
                  type="button"
                  style={linkStyle}
                  onClick={() => onUse(candidate)}
                  aria-label={`${EXERCISE_COPY.use}: ${exerciseLocator(candidate) || "this exercise"}${candidate.exposure.exposed ? `, ${EXERCISE_COPY.practiceNotCheck}` : ""}`}
                >
                  {EXERCISE_COPY.use} ▸
                </button>
              )
            ) : null}
          </span>
        </li>
      ))}
    </ul>
  );
}
