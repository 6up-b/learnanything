import type { FirstHintProgress, SelfGradeDisclosureDto, SessionCheckpoint, TeachBackStateDto } from "../api/dto";

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
  /** UX Phase 4 (Codex review F1): the trace frozen before a full answer was
   *  shown, so the draft reopens locked to it. */
  selfGradeDisclosure?: SelfGradeDisclosureDto | null;
  /** Adaptive difficulty AD1 (§11.2): the first-hint progress marker. */
  firstHintProgress?: FirstHintProgress | null;
  /** AD1 fix round 5 (V4): a hint of any kind was seen on this draft. */
  hintSeen?: boolean;
  /** Reader CA1 (Q12): the original page was opened before Submit. */
  pageSeen?: boolean;
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
  /** Codex review F1: the trace a plain self-grade froze before showing a
   *  full answer, under this draft's retry key; null otherwise. */
  selfGradeDisclosure: SelfGradeDisclosureDto | null;
  /** Adaptive difficulty AD1 (§11.2): the marker kept with this draft. */
  firstHintProgress: FirstHintProgress | null;
  /** AD1 fix round 5 (V4): a hint was seen on this draft (false on a legacy
   *  draft that never recorded it, and on a draft with no hint). */
  hintSeen: boolean;
  /** Reader CA1 (Q12): the original page was opened before Submit on this
   *  draft, so it counts as the book (false on a draft that never opened it). */
  pageSeen: boolean;
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
      planPresentationId: localDraft.planPresentationId ?? null,
      selfGradeDisclosure:
        localDraft.selfGradeDisclosure && localDraft.selfGradeDisclosure.submissionId === localDraft.submissionId
          ? localDraft.selfGradeDisclosure
          : null,
      firstHintProgress: localDraft.firstHintProgress ?? null,
      hintSeen: localDraft.hintSeen === true,
      pageSeen: localDraft.pageSeen === true
    };
  }
  if (!checkpoint || checkpoint.currentPracticeItemId !== practiceItemId) {
    return {
      answer: "", hints: 0, submissionId: null, stuck: false, teachBack: null, planPresentationId: null,
      selfGradeDisclosure: null, firstHintProgress: null, hintSeen: false, pageSeen: false
    };
  }
  return {
    answer: checkpoint.currentAnswer ?? "",
    hints: checkpoint.hintsUsed,
    submissionId: checkpoint.submissionId ?? null,
    stuck: checkpoint.declaredStuck === true,
    teachBack: checkpoint.teachBack ?? null,
    planPresentationId: checkpoint.planPresentationId ?? null,
    selfGradeDisclosure:
      checkpoint.selfGradeDisclosure && checkpoint.selfGradeDisclosure.submissionId === checkpoint.submissionId
        ? checkpoint.selfGradeDisclosure
        : null,
    // The sidecar returns it only under the draft's own retry key.
    firstHintProgress: checkpoint.firstHintProgress ?? null,
    hintSeen: checkpoint.hintSeen === true,
    // The sidecar returns it only under the draft's own retry key.
    pageSeen: checkpoint.pageSeen === true
  };
}
