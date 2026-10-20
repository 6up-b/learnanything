// RW4b: the textbook exercises of one practice proposal, wherever the Reader
// lists practice proposals (spec §7.4; UX §4.5, §4.6). Self-contained so a
// surface adds it with one element after its items: RW4a's "practice this
// question" (LibraryAnswer) today; RW1c's tutor offers at the landing
// (docs/reviews/reader-workbench-RW4b.md, "The RW1c hook").
//
// It asks the server which of the proposal's exercises may be shown and how
// (the sources service's exposure rule; held-out material left out), shows
// them as candidate cards, and, when nothing fits (no item shown and no
// exercise), offers "find an exercise in my sources" while the fallback is
// on. Nothing here takes focus, animates or opens a modal.
import type { CSSProperties } from "react";
import type { FindPracticeResultDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { ExerciseCandidates } from "./ExerciseCandidates";
import { EXERCISE_COPY, type ExerciseCandidate } from "./exerciseCandidates";
import { ModelActionState } from "./ModelActionState";
import { useLibraryExercises, type LibraryExercisesSettings } from "./useLibraryExercises";
import { MeaningLabel } from "./voices";

/** The candidate view's settings and the Reader's two actions on a card. */
export interface LibraryExercisesProps {
  settings: LibraryExercisesSettings;
  /** "Use this one" (a learner pick: the workbench opens at once on the stem). */
  onUse: ((candidate: ExerciseCandidate) => void) | null;
  /** "Open in the book" (a detour). */
  onOpenInBook: ((candidate: ExerciseCandidate) => void) | null;
  /** The candidate whose problem is opening. */
  opening?: string | null;
}

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

const headStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.12em", color: COLOR.textDim, textTransform: "uppercase" };

export function ProposalExercises({
  practice,
  itemsShown,
  exercises,
  query,
  learningObjectIds,
  extractionId,
}: {
  /** The landed find_practice result whose exercises these are. */
  practice: FindPracticeResultDto;
  /** How many of its items the surface showed (0: "nothing fits" may apply). */
  itemsShown: number;
  exercises: LibraryExercisesProps;
  /** The request, for the fallback search (the question and its learning objects). */
  query: string;
  learningObjectIds: string[];
  /** The source the Reader has open (the caller's reference). */
  extractionId: string | null;
}) {
  const view = useLibraryExercises({ settings: exercises.settings, practice, query, learningObjectIds, extractionId });
  const nothing = itemsShown === 0 && view.candidates.length === 0 && view.viewPhase !== "pending";
  return (
    <>
      {view.candidates.length ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={headStyle}>{EXERCISE_COPY.heading}</span>
          <ExerciseCandidates candidates={view.candidates} onUse={exercises.onUse} onOpenInBook={exercises.onOpenInBook} opening={exercises.opening ?? null} />
        </div>
      ) : null}
      {view.viewPhase === "pending" ? (
        <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> checking your books' exercises…</MeaningLabel>
      ) : null}
      {view.viewPhase === "failed" ? <MeaningLabel style={{ fontSize: 11 }}>{EXERCISE_COPY.unavailable}</MeaningLabel> : null}
      {nothing ? (
        <MeaningLabel style={{ fontSize: 11 }}>
          {exercises.settings.fallback && view.fallbackPhase === "idle" ? (
            <>
              {EXERCISE_COPY.nothing.replace(/\.$/, "")} ·{" "}
              <button type="button" onClick={view.findInSources} style={linkStyle}>{EXERCISE_COPY.find} ▸</button>
            </>
          ) : (
            EXERCISE_COPY.nothing
          )}
        </MeaningLabel>
      ) : null}
      {view.fallbackPhase !== "idle" ? (
        <ModelActionState
          phase={view.fallbackPhase}
          verb={EXERCISE_COPY.finding}
          failure={view.fallbackFailure ?? undefined}
          onRetry={view.findInSources}
        >
          {view.fallbackCandidates.length ? (
            <ExerciseCandidates candidates={view.fallbackCandidates} onUse={exercises.onUse} onOpenInBook={exercises.onOpenInBook} opening={exercises.opening ?? null} />
          ) : (
            <MeaningLabel style={{ fontSize: 11 }}>{EXERCISE_COPY.foundNone}</MeaningLabel>
          )}
        </ModelActionState>
      ) : null}
    </>
  );
}
