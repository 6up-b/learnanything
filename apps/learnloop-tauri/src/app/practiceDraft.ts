import type { SessionCheckpoint, TeachBackStateDto } from "../api/dto";

/** In-memory mirror of the practice draft, reported by PracticeScreen when it
 *  unmounts (the backend checkpoint is only reloaded at startup). */
export type PracticeDraftMirror = {
  practiceItemId: string;
  answerMd: string;
  hintsUsed: number;
  submissionId: string;
  /** mvp-0.13: the draft was being written after "I'm stuck". */
  declaredStuck: boolean;
  /** Router R2a (review F5): the daily-plan presentation the draft answers. */
  planPresentationId?: string | null;
};

export type RestoredPracticeDraft = {
  answer: string;
  hints: number;
  submissionId: string | null;
  /** mvp-0.13 (review F2): reopen in stuck mode, so the recovered text still
   *  submits as a stuck answer. */
  stuck: boolean;
  teachBack: TeachBackStateDto | null;
  /** Router R2a (review F5): the daily-plan presentation the draft answers,
   *  so a resumed draft still submits bound to it. */
  planPresentationId: string | null;
};

/** What a practice screen for `practiceItemId` restores: the in-memory mirror
 *  first (mid-session navigation), else the session checkpoint (restart). */
export function restoredPracticeDraft(
  practiceItemId: string | null,
  localDraft: PracticeDraftMirror | null,
  checkpoint: SessionCheckpoint | null | undefined
): RestoredPracticeDraft {
  if (localDraft && localDraft.practiceItemId === practiceItemId) {
    return {
      answer: localDraft.answerMd,
      hints: localDraft.hintsUsed,
      submissionId: localDraft.submissionId,
      stuck: localDraft.declaredStuck,
      teachBack: null,
      planPresentationId: localDraft.planPresentationId ?? null
    };
  }
  if (!checkpoint || checkpoint.currentPracticeItemId !== practiceItemId) {
    return { answer: "", hints: 0, submissionId: null, stuck: false, teachBack: null, planPresentationId: null };
  }
  return {
    answer: checkpoint.currentAnswer ?? "",
    hints: checkpoint.hintsUsed,
    submissionId: checkpoint.submissionId ?? null,
    stuck: checkpoint.declaredStuck === true,
    teachBack: checkpoint.teachBack ?? null,
    planPresentationId: checkpoint.planPresentationId ?? null
  };
}
