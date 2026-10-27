import { useCloseWithFlush } from "../app/useCloseWithFlush";
import { registerVaultDraft } from "../app/vaultTransition";
import { type ReactNode, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  AttemptProgress,
  AttemptResultDto,
  AttemptType,
  CandidateErrorTypeDto,
  GuidedRedoDto,
  PracticeItemDetail,
  ProbeBlockEndDto,
  ProbeContractDto,
  RubricCriterionDto,
  SelfGradeErrorAttributionDto,
  SelfGradeDisclosureDto,
  SelfGradeInputDto,
  SessionSnapshot,
  TeachBackStateDto,
  TeachBackTurnDto
} from "../api/dto";
import { Card, EntityLink, KeyBar, Pill, SectionHeader } from "../components/ui";
import { CardControls } from "../components/CardControls";
import { ItemPresentation } from "../components/ItemPresentation";
import { BlockBar, COLOR, Faint, FONT_MONO, modePillColor, TermSelect } from "../components/term";
import { algoConfig, masteryTone, setAdaptiveHelpStyle, STUCK_PROMPT_TEXT } from "../app/algoConfig";
import { isTypingTarget } from "../app/keyboard";
import { MarkdownMath } from "../render/MarkdownMath";
import { MathLiveEditor } from "../render/MathLiveEditor";
import { errorMessage, getCommandError } from "../errors";
import { expectedAnswerText, simplePracticeFeedback } from "../app/practiceFeedback";
import { DetailsToggle, PrimaryAction, QuietAction, VoicePanel, quietLine, quietLink } from "../components/PlainParts";
import { useAnswerExposure, type RecordDisplay } from "./feedback/answerExposure";
import { AnswerWaiting } from "./feedback/FeedbackSurface";
import type { WorkbenchSessionDto, WorkbenchSummaryDto } from "../api/dto";
import { Workbench } from "./workbench/Workbench";
import { HintPanel } from "./practice/HintPanel";
import { useAdaptiveHints } from "./practice/useAdaptiveHints";
import { DifficultyRatingTap } from "./practice/DifficultyRatingTap";
import { WhyThisItem } from "./practice/WhyThisItem";
import { useFirstHintProgress } from "./practice/useFirstHintProgress";
import type { DifficultyRating, FirstHintProgress, HelpRecordDto } from "../api/dto";
import { screenLeavesKey } from "../app/keymap";
import { AS_PRINTED_COPY, AsPrinted, OriginalPageLink, printedPageLabel, useAsPrinted } from "../components/AsPrinted";
import { OpenInSource } from "../components/OpenInSource";
import { AskOverlay, type AskTarget } from "../components/AskOverlay";
import { ASK_COPY } from "../components/askPanel";
import { DockedAsk } from "../components/DockedAsk";

/** RW2a (D9): "Work in steps", remembered once chosen, on this device. */
const WORK_IN_STEPS_KEY = "ll.workbench.workInSteps";
function rememberedWorkInSteps(): boolean {
  try {
    return window.localStorage.getItem(WORK_IN_STEPS_KEY) === "1";
  } catch {
    return false;
  }
}
function rememberWorkInSteps(on: boolean): void {
  try {
    if (on) window.localStorage.setItem(WORK_IN_STEPS_KEY, "1");
    else window.localStorage.removeItem(WORK_IN_STEPS_KEY);
  } catch {
    // A convenience only: the button still works without storage.
  }
}

type CommittedAttemptRecovery = {
  attemptId: string;
  attemptType: string | null;
  message: string;
};

type PracticeCheckpointIdentity = {
  practiceItemId: string;
  submissionId: string;
};

function committedAttemptRecovery(error: unknown): CommittedAttemptRecovery | null {
  const command = getCommandError(error);
  if (command?.code !== "submission_committed" || !command.details || typeof command.details !== "object") {
    return null;
  }
  const details = command.details as {
    attempt_id?: unknown;
    attemptId?: unknown;
    attempt_type?: unknown;
    attemptType?: unknown;
  };
  const attemptId = details.attempt_id ?? details.attemptId;
  if (typeof attemptId !== "string" || !attemptId.trim()) return null;
  const attemptType = details.attempt_type ?? details.attemptType;
  return {
    attemptId: attemptId.trim(),
    attemptType: typeof attemptType === "string" ? attemptType : null,
    message: command.message
  };
}

/** Runtime guard for the measurement contract. TypeScript only checks compile
 * time; a stale/malformed sidecar response must never silently enable hints or
 * ordinary submission during a diagnostic serve. */
function activeProbeContract(contract: ProbeContractDto): ProbeContractDto | null {
  if (
    !contract ||
    typeof contract !== "object" ||
    !Number.isInteger(contract.version) ||
    typeof contract.active !== "boolean"
  ) {
    throw new Error("The diagnostic safety contract was malformed. Retry before answering.");
  }
  if (!contract.active) return null;
  const restrictions = contract.restrictions;
  if (
    typeof contract.presentationId !== "string" ||
    !contract.presentationId.trim() ||
    contract.forcedAttemptType !== "diagnostic_probe" ||
    !restrictions ||
    restrictions.hintsDisabled !== true ||
    restrictions.askTutorDisabled !== true ||
    restrictions.workedExampleDisabled !== true ||
    restrictions.answerRevealDisabled !== true ||
    restrictions.feedbackDeferred !== true
  ) {
    throw new Error("The diagnostic safety contract was incomplete. Retry before answering.");
  }
  return contract;
}

export function PracticeScreen({
  session,
  practiceItemId,
  schedulerCandidateId = null,
  proposalOrigin = null,
  planPresentationId = null,
  gradingReady,
  gradingProvider,
  restoredAnswer,
  restoredHints,
  restoredSubmissionId,
  restoredStuck = false,
  restoredTeachBack,
  restoredDisclosure = null,
  restoredFirstHintProgress = null,
  restoredHintSeen = false,
  restoredPageSeen = false,
  onFeedback,
  onBlockEnd,
  onContinueDiagnostic,
  onBack,
  onCheckpointCleared,
  onDraftSaved,
  onTeachBackActive,
  onAskAvailabilityChange,
  onInspect,
  onAsk,
  onAskState,
  onAskOpener,
  onError,
  primed = false,
  redo = null
}: {
  session: SessionSnapshot;
  practiceItemId: string;
  schedulerCandidateId?: string | null;
  /** Router R2a: the daily-plan presentation this serve answers (sent on submit). */
  planPresentationId?: string | null;
  /** The proposal a plan-off pick of this item came from: this serve records
   *  the pick's delivery (canonical sources, Codex re-review F10). */
  proposalOrigin?: { proposalId: string; importId: string | null } | null;
  /** This item is a primed retry launched from the feedback source panel. */
  primed?: boolean;
  /** Fix 3 guided partial redo: the preserved learner work is rendered locked
   *  above the editor and the learner rewrites only the failed portion; the
   *  submit composes prefix + redo text as the primed answer. */
  redo?: GuidedRedoDto | null;
  gradingReady: boolean;
  gradingProvider: string;
  restoredAnswer?: string;
  restoredHints?: number;
  restoredSubmissionId?: string | null;
  /** mvp-0.13 (review F2): the restored draft was being written after "I'm
   *  stuck", so it reopens in stuck mode and submits as a stuck answer. */
  restoredStuck?: boolean;
  restoredTeachBack?: TeachBackStateDto | null;
  /** UX Phase 4 (Codex review F1): the trace a plain self-grade froze before
   *  it showed a full answer. The draft reopens locked to it. */
  restoredDisclosure?: SelfGradeDisclosureDto | null;
  /** Adaptive difficulty AD1 (§11.2): the restored draft's first-hint marker. */
  restoredFirstHintProgress?: FirstHintProgress | null;
  /** AD1 fix round 5 (V4): the restored draft saw a hint of some kind. */
  restoredHintSeen?: boolean;
  /** Reader CA1 (Q12): the restored draft opened the original page before Submit. */
  restoredPageSeen?: boolean;
  onFeedback: (attemptId: string) => void;
  /** §5.7: a diagnostic block just closed — releasedFeedback covers every
   *  attempt in it, not just the one that closed it. */
  onBlockEnd: (blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string) => void;
  /** §5.7 continuity: jump straight to the next observation in an open
   *  episode with no visible queue round-trip. */
  onContinueDiagnostic: (practiceItemId: string) => void;
  onBack: () => void;
  onCheckpointCleared: (identity?: PracticeCheckpointIdentity) => void;
  /** Mirror of the last flushed draft, so App can restore it if this item is
   *  re-opened before the backend checkpoint is reloaded. */
  onDraftSaved: (draft: {
    practiceItemId: string;
    answerMd: string;
    hintsUsed: number;
    submissionId: string;
    declaredStuck: boolean;
    /** Router R2a (review F5): restored with the draft. */
    planPresentationId: string | null;
    /** Codex review F1: the frozen trace, when a full answer was shown. */
    selfGradeDisclosure?: SelfGradeDisclosureDto | null;
    /** Adaptive difficulty AD1 (§11.2): the first-hint progress marker. */
    firstHintProgress?: FirstHintProgress | null;
    /** AD1 fix round 5 (V4): a hint of any kind was seen on this draft. */
    hintSeen?: boolean;
    /** Reader CA1 (Q12): the original page was opened before Submit. */
    pageSeen?: boolean;
  }) => void;
  onTeachBackActive: (active: boolean) => void;
  /** Gate App-level Ask commands while the probe contract is loading or active. */
  onAskAvailabilityChange: (allowed: boolean) => void;
  onInspect: (id: string) => void;
  onAsk: (target: {
    context: "practice";
    practiceItemId: string;
    sessionId: string;
    openedAtMs: number;
    attemptProgress: AttemptProgress;
    proactiveOpen?: boolean;
    draftMd?: string;
    workMd?: string;
  }) => void;
  /** Registers a reader of this screen's ask state (when the item opened, and
   *  whether an answer was started) so App's command-palette ask carries the
   *  same state the in-screen ask does; null when the screen unmounts. */
  onAskState?: (reader: (() => { openedAtMs: number; attemptProgress: AttemptProgress; workMd?: string }) | null) => void;
  /** Reader CA2: registers this screen's own Ask opener, so App's palette
   *  Ask opens the docked panel (or the inline one in steps) instead of the
   *  overlay while the panel is on; null when the screen unmounts. */
  onAskOpener?: (open: (() => void) | null) => void;
  onError: (message: string) => void;
}) {
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [answer, setAnswer] = useState(restoredAnswer ?? "");
  // Meas §3.A6: the optional one-line justification, when this serve elicits
  // one. Held apart from `answer` on purpose — it must never reach the draft
  // checkpoint, because a restored draft that silently contained a "[Why this
  // approach]" block would make the learner's line un-retractable.
  const [whyLine, setWhyLine] = useState("");
  const [hintsUsed, setHintsUsed] = useState(restoredHints ?? 0);
  // RW2a review F2: a book a problem in steps counted comes back to the
  // answer box with the learner, and counts there as the one hint it was.
  const [bookLeft, setBookLeft] = useState(false);
  // Reader CA1 (ux_reader_compare_ask_v1 §8.3, Q12): the original page opened
  // before Submit is the book left open: one hint-equivalent, in the same
  // book component a book counted in steps uses (never counted twice), kept
  // with the draft so a restart still counts it.
  const [pageSeen, setPageSeen] = useState(restoredPageSeen === true);
  const [originalPage, setOriginalPage] = useState<{ extractionId: string; spanId: string; outlineSpanIds: string[] } | null>(null);
  const originalPageOpen = useRef(false);
  originalPageOpen.current = originalPage !== null;
  const [submitting, setSubmitting] = useState(false);
  // mvp-0.13: "I'm stuck" replaces "I don't know". One tap turns the answer
  // box into "write what you can, or what's confusing you"; the same Submit
  // sends it, empty or not. The sidecar decides whether this vault offers it.
  const stuckPrompt = algoConfig().stuckPrompt;
  // Restored with the draft (review F2): a navigation or restart before the
  // grade commits must not turn a stuck answer into an ordinary one.
  const [stuck, setStuck] = useState(Boolean(restoredStuck) && stuckPrompt);
  // Probe redesign §12: when the LO has an in-progress diagnostic episode, the
  // sidecar commits a presentation and this contract enforces measurement
  // conditions — forced diagnostic_probe, no hints, no ask-tutor, deferred
  // feedback, and a "stop diagnosing" escape into tutoring.
  const [probe, setProbe] = useState<ProbeContractDto | null>(null);
  const [probeLoadState, setProbeLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [itemLoadError, setItemLoadError] = useState<string | null>(null);
  const [probeLoadError, setProbeLoadError] = useState<string | null>(null);
  const [loadRevision, setLoadRevision] = useState(0);
  const [committedRecovery, setCommittedRecovery] = useState<CommittedAttemptRecovery | null>(null);
  // §7.1: the learner's committed answer confidence (1–5) during a diagnostic
  // block. Logged-only — it never changes grading or scheduling.
  const [answerConfidence, setAnswerConfidence] = useState<number | null>(null);
  // Adaptive difficulty AD1 (§12): the optional "Felt" tap, sent only when tapped.
  const ratingTap = algoConfig().ratingTap;
  const [difficultyRating, setDifficultyRating] = useState<DifficultyRating | null>(null);
  // AD1 (§11.2): the first-hint progress marker, kept with the draft.
  // A restored draft that saw a hint (fix round 5, V4: any kind, saved with
  // the draft as `hintSeen`; a legacy draft without it: its counted hints)
  // with no saved marker: that hint's timing is unknown, so this attempt
  // records none (fix round 4, V4; §5.3).
  const firstHint = useFirstHintProgress({ enabled: algoConfig().firstHintProgress, restored: restoredFirstHintProgress,
                                           hintsBefore: restoredHintSeen === true || (restoredHints ?? 0) > 0 });
  const firstHintRef = useRef(firstHint.value);
  firstHintRef.current = firstHint.value;
  // AD1 fix round 5 (V4): whether a hint of any kind (an authored reveal, a
  // delivered hint, a carried hint or book) was seen on this draft, saved
  // with it whatever the switches. Persistence only: hintsUsed and the
  // assistance count are unchanged.
  const [hintSeen, setHintSeen] = useState(restoredHintSeen === true);
  const hintSeenRef = useRef(hintSeen);
  hintSeenRef.current = hintSeen;
  const seeHint = useCallback(() => setHintSeen(true), []);
  const [fallbackRequired, setFallbackRequired] = useState(!gradingReady);
  // The self-grade panel is only revealed once the learner clicks Submit (and
  // grading actually needs a self-grade), never while they are still answering.
  const [selfGradeVisible, setSelfGradeVisible] = useState(false);
  const [selfGrade, setSelfGrade] = useState<SelfGradeInputDto>({
    criterionPoints: {},
    confidence: 3,
    fatalErrors: [],
    notes: "",
    errorAttributions: []
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  // UX Phase 4 (§7.4): the plain card, unless the library's
  // `[ui] practice_feedback = "classic"` restores the card exactly.
  const simple = simplePracticeFeedback();
  const [cardDetailsOpen, setCardDetailsOpen] = useState(false);
  const [controlsOpen, setControlsOpen] = useState(false);
  const [checkWhyOpen, setCheckWhyOpen] = useState(false);
  // The plain self-grade: "Partly" asks which parts the learner got.
  const [partlyOpen, setPartlyOpen] = useState(false);
  // Codex review F1: the whole trace (the answer as Submit sends it and the
  // volunteered line) frozen in the session checkpoint BEFORE the plain
  // self-grade shows a full answer. While it is set the answer and the line
  // are locked, across a remount or a restart, and Submit sends exactly it.
  const [disclosed, setDisclosed] = useState<{ answerMd: string; explanationMd: string | null } | null>(
    restoredDisclosure ? { answerMd: restoredDisclosure.answerMd, explanationMd: restoredDisclosure.explanationMd } : null
  );
  const disclosedRef = useRef(disclosed);
  disclosedRef.current = disclosed;
  // The freeze failed: the self-grade goes on without the full answer.
  const [disclosureFailed, setDisclosureFailed] = useState(false);
  const [partsGot, setPartsGot] = useState<Record<string, boolean>>({});
  const [selfGradeDetailsOpen, setSelfGradeDetailsOpen] = useState(false);
  const mountedRef = useRef(true);
  // Read at serve time, not an effect dependency: the item's serve happens once.
  const proposalOriginRef = useRef(proposalOrigin);
  proposalOriginRef.current = proposalOrigin;
  const submissionId = useRef(restoredSubmissionId?.trim() || crypto.randomUUID());
  const latestDraft = useRef({
    sessionId: session.sessionId,
    practiceItemId,
    answerMd: answer,
    hintsUsed,
    submissionId: submissionId.current,
    schedulerCandidateId,
    declaredStuck: stuck,
    // Router R2a (review F5): saved with the draft so a draft resumed after a
    // restart still submits bound to its plan presentation.
    planPresentationId,
    ...(firstHint.value ? { firstHintProgress: firstHint.value } : {}),
    ...(hintSeen ? { hintSeen: true } : {}),
    ...(pageSeen ? { pageSeen: true } : {}),
    // Codex review F1: set once an earlier attempt's help is opened.
    ...({} as { earlierOpened?: boolean })
  });
  const suppressDraftFlush = useRef(false);
  const vaultFrozen = useRef(false);
  // Set when a load gave up because a vault switch froze the screen. If that
  // switch fails, resume must restart the load or the screen never leaves its
  // loading state.
  const reloadOnResume = useRef(false);
  const [vaultChanging, setVaultChanging] = useState(false);
  const draftWrites = useRef<Promise<unknown>>(Promise.resolve());
  const isTeachBack = item?.practiceMode === "teach_back";
  // Teach-back conversations own the checkpoint (the sidecar stores the
  // conversation envelope in current_answer); the plain draft flush must never
  // overwrite it. Start closed until item detail proves this is ordinary
  // practice; this also protects a new teach-back whose mode call is slow.
  const teachBackRef = useRef(true);
  // Report the mode upward: App's command-palette ask path must refuse to open
  // the tutor during a teach-back conversation. Until the item detail loads,
  // fall back to the restored checkpoint (a resumed conversation is already
  // teach-back). The cleanup resets the flag on unmount/item switch.
  const teachBackActive = item ? item.practiceMode === "teach_back" : Boolean(restoredTeachBack);
  useEffect(() => {
    onTeachBackActive(teachBackActive);
    return () => onTeachBackActive(false);
  }, [teachBackActive, onTeachBackActive]);
  // When this item was opened — the ask overlay reports secondsIntoAttempt
  // from it, and the submitted attempt reports `latencySeconds` from it.
  const openedAtMs = useRef(Date.now());
  // Wall-clock seconds from presentation to submission. Deliberately NOT
  // idle-adjusted: subtracting time the learner "wasn't really working" would be
  // a fabrication, and the metric that consumes this (B5's
  // `learner_minutes_to_cold_success`) is denominated in the learner's actual
  // elapsed experience.
  const elapsedSeconds = () =>
    Math.max(0, Math.round((Date.now() - openedAtMs.current) / 1000));
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);
  useEffect(() => {
    openedAtMs.current = Date.now();
    submissionId.current = restoredSubmissionId?.trim() || crypto.randomUUID();
    setAnswerConfidence(null);
    setDifficultyRating(null);
  }, [practiceItemId, restoredSubmissionId]);
  // The command-palette ask (App) reads the same state at the moment it opens.
  const attemptProgressRef = useRef<AttemptProgress>("no_draft");
  attemptProgressRef.current = answer.trim() || whyLine.trim() ? "draft_started" : "no_draft";
  // Owner capture 2026-10-25 (B1): in "Work in steps" the work is the steps
  // (the workbench reports them as they change); null on the answer box.
  const stepsWorkRef = useRef<string | null>(null);
  const onStepsWork = useCallback((workMd: string) => { stepsWorkRef.current = workMd; }, []);
  const askState = (): { openedAtMs: number; attemptProgress: AttemptProgress; workMd?: string } => {
    const steps = stepsWorkRef.current;
    if (steps !== null) {
      return { openedAtMs: openedAtMs.current, attemptProgress: steps.trim() ? "draft_started" : "no_draft",
               ...(steps.trim() ? { workMd: steps } : {}) };
    }
    return { openedAtMs: openedAtMs.current, attemptProgress: attemptProgressRef.current };
  };
  const askStateRef = useRef(askState);
  askStateRef.current = askState;
  useEffect(() => {
    if (!onAskState) return undefined;
    onAskState(() => askStateRef.current());
    return () => onAskState(null);
  }, [onAskState]);
  // Reader CA2 (ux_reader_compare_ask_v1 §7): the one Ask panel, while the
  // sidecar sends `ask` (ask.panel_enabled). Docked beside the question on the
  // answer box; inline under the focused step in Work in Steps. Off (null),
  // every path below is the overlay's, exactly as before.
  const panelOn = algoConfig().ask !== null;
  const [dockedAsk, setDockedAsk] = useState<AskTarget | null>(null);
  const [stepAskSignal, setStepAskSignal] = useState(0);
  // §7.7: a substantive question made this check practice with help.
  const [askConverted, setAskConverted] = useState(false);
  // K8: the questions this attempt asked, in order, with what they counted as.
  const [askRecord, setAskRecord] = useState<Array<{ eventId: string; hintEquivalent: boolean }>>([]);
  // K6, Q2: *earlier on this question* opened before Submit, counted once per
  // attempt (its submission key). Codex review F1: recorded on the draft's
  // checkpoint and counted by the submit's server side (any surface, after a
  // restart too); the screen only shows it.
  const [earlierCountedFor, setEarlierCountedFor] = useState<string | null>(null);
  // Codex review F7 (K8): the help record as Submit will fold it, read from
  // the server (stored state), so the footer never says less than Submit.
  const [serverRecord, setServerRecord] = useState<HelpRecordDto | null>(null);
  const openAsk = (options?: { proactiveOpen?: boolean }) => {
    if (panelOn && !options?.proactiveOpen) {
      if (stepsShown.current) {
        // §7.6: Ask about the focused step, under it.
        setStepAskSignal((value) => value + 1);
        return;
      }
      setDockedAsk(practiceAskTarget());
      return;
    }
    onAsk({
      context: "practice",
      practiceItemId,
      sessionId: session.sessionId,
      // "No work yet" is logged explicitly: nothing typed in the answer or the
      // why-line when the learner asks (hints revealed are help, not work);
      // in steps, no step written yet.
      ...askState(),
      // Canonical sources S4: "Explain this with my work" grounds the tutor in
      // a chosen passage and this draft.
      ...(stepsWorkRef.current === null && answer.trim() ? { draftMd: answer } : {}),
      ...options
    });
  };
  const openAskRef = useRef(openAsk);
  openAskRef.current = openAsk;
  useEffect(() => {
    if (!onAskOpener || !panelOn) return undefined;
    onAskOpener(() => openAskRef.current());
    return () => onAskOpener(null);
  }, [onAskOpener, panelOn]);
  // The editor grows with its content but is capped so the answer card never
  // pushes the Submit button (or anything below the editor) off-screen — once it
  // hits the cap it scrolls internally instead. The cap is "viewport below the
  // editor's top, minus whatever sits beneath it (counts, hints, panel, submit)
  // and the key bar". Those sibling heights don't depend on the editor height,
  // so there's no feedback loop.
  const editorSlotRef = useRef<HTMLDivElement>(null);
  const belowRef = useRef<HTMLDivElement>(null);
  const [editorMaxHeight, setEditorMaxHeight] = useState(0);

  const recomputeEditorMax = useCallback(() => {
    const slot = editorSlotRef.current;
    if (!slot) return;
    const top = slot.getBoundingClientRect().top;
    const below = belowRef.current?.offsetHeight ?? 0;
    const keybar = (document.querySelector(".keybar") as HTMLElement | null)?.offsetHeight ?? 36;
    const next = Math.max(140, Math.floor(window.innerHeight - top - below - keybar - 28));
    setEditorMaxHeight(next);
  }, []);

  useEffect(() => {
    latestDraft.current = {
      sessionId: session.sessionId,
      practiceItemId,
      answerMd: answer,
      hintsUsed,
      submissionId: submissionId.current,
      schedulerCandidateId,
      declaredStuck: stuck,
      planPresentationId,
      ...(firstHint.value ? { firstHintProgress: firstHint.value } : {}),
      ...(hintSeen ? { hintSeen: true } : {}),
      ...(pageSeen ? { pageSeen: true } : {}),
      // Codex review F1: kept with the draft's retry key, server-side.
      ...(earlierCountedFor !== null && earlierCountedFor === submissionId.current ? { earlierOpened: true } : {})
    };
    suppressDraftFlush.current = false;
  }, [answer, hintsUsed, planPresentationId, practiceItemId, restoredSubmissionId, schedulerCandidateId, session.sessionId, stuck, firstHint.value, hintSeen, pageSeen, earlierCountedFor]);

  const draftSavingDisabled = () => suppressDraftFlush.current || teachBackRef.current;

  /** Queue a save of the latest draft behind any save already in flight. */
  const saveDraft = useCallback(() => {
    const draft = latestDraft.current;
    const write = draftWrites.current.catch(() => undefined).then(() => api.savePracticeDraft(draft));
    draftWrites.current = write;
    return write;
  }, []);

  /** Debounce, unmount, submit and window-close path. */
  const flushDraft = useCallback(async () => {
    // While a vault switch holds the screen, the switch's own save carries the
    // latest draft; wait for it instead of writing again.
    if (vaultFrozen.current) {
      await draftWrites.current;
      return;
    }
    if (draftSavingDisabled()) return;
    await saveDraft();
  }, [saveDraft]);

  /** The save a vault switch waits on before selecting the next vault. */
  const settleDraftForVaultSwitch = useCallback(async () => {
    if (draftSavingDisabled()) {
      await draftWrites.current;
      return;
    }
    await saveDraft();
  }, [saveDraft]);

  // Adaptive hints H2b (spec_adaptive_hints_v1 §4.8): hints written for the
  // learner's work, while the sidecar says they are on (`hints` in the app
  // snapshot's config). Off, `adaptive` is null and every path below is the
  // base's, byte for byte (G-H1).
  const adaptive = algoConfig().adaptiveHints;
  const [helpStyle, setHelpStyle] = useState(adaptive?.helpStyle ?? "balanced");
  const answerRef = useRef(answer);
  answerRef.current = answer;
  const adaptiveHints = useAdaptiveHints({
    enabled: adaptive !== null,
    sessionId: session.sessionId,
    practiceItemId,
    submissionId: () => submissionId.current,
    answer: () => answerRef.current,
    flushDraft,
    secondsOnItem: elapsedSeconds,
    authoredHints: item?.hints ?? [],
    hintsUsed,
    authoredOfferAfterSeconds: adaptive?.authoredOfferAfterSeconds ?? 4,
    onDisabled: () => revealAuthoredHint(),
    onAuthoredReveal: (index) => revealAuthoredAt(index),
    onHelpStyleSaved: (style) => {
      setAdaptiveHelpStyle(style);
      setHelpStyle(style);
    },
    onError
  });
  // Adaptive difficulty AD1: a hint the panel delivered is a first hint too.
  const deliveredHints = adaptiveHints.entries.length;
  useEffect(() => {
    if (deliveredHints > 0) {
      firstHint.mark(attemptProgressRef.current);
      seeHint();
    }
  }, [deliveredHints, firstHint.mark, seeHint]);

  useEffect(() => registerVaultDraft({
    freeze: () => {
      vaultFrozen.current = true;
      setVaultChanging(true);
    },
    flush: settleDraftForVaultSwitch,
    resume: () => {
      vaultFrozen.current = false;
      setVaultChanging(false);
      if (reloadOnResume.current) {
        reloadOnResume.current = false;
        setLoadRevision((value) => value + 1);
      }
    }
  }), [settleDraftForVaultSwitch]);

  useEffect(() => {
    setAnswer(restoredAnswer ?? "");
    setHintsUsed(restoredHints ?? 0);
    setBookLeft(false);
    setFallbackRequired(!gradingReady);
    // A draft whose full answer was already shown reopens locked to the
    // trace it froze, at the self-grade when it is still needed (F1).
    const frozen = restoredDisclosure
      ? { answerMd: restoredDisclosure.answerMd, explanationMd: restoredDisclosure.explanationMd }
      : null;
    setDisclosed(frozen);
    setDisclosureFailed(false);
    setSelfGradeVisible(Boolean(frozen) && simple && !gradingReady);
    setPartlyOpen(false);
    setPartsGot({});
    setSelfGradeDetailsOpen(false);
    setCardDetailsOpen(false);
    setControlsOpen(false);
    setCheckWhyOpen(false);
    setFieldErrors({});
    setSubmitting(false);
    setWhyLine(frozen?.explanationMd ?? "");
    setStuck(Boolean(restoredStuck) && stuckPrompt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gradingReady, practiceItemId, restoredAnswer, restoredHints, restoredStuck, stuckPrompt, restoredDisclosure]);

  useEffect(() => {
    let cancelled = false;
    setItem(null);
    setItemLoadError(null);
    setProbe(null);
    setProbeLoadState("loading");
    setProbeLoadError(null);
    setCommittedRecovery(null);
    teachBackRef.current = true;
    reloadOnResume.current = false;

    // True when this load must stop: the screen moved on, or a vault switch
    // froze it (in which case a failed switch restarts the load on resume).
    const abandonLoad = () => {
      if (cancelled) return true;
      if (!vaultFrozen.current) return false;
      reloadOnResume.current = true;
      return true;
    };

    const recoverOrLoad = async () => {
      const retryKey = restoredSubmissionId?.trim();
      if (retryKey) {
        try {
          const recovery = await api.recoverPracticeSubmission({
            sessionId: session.sessionId,
            practiceItemId,
            submissionId: retryKey
          });
          if (abandonLoad()) return;
          if (recovery.status === "recovered" && recovery.result) {
            // The exact original payload carries deferred/block-end routing and
            // does not require the now-single-use item to still be active.
            suppressDraftFlush.current = true;
            const recoveredItem = await api.getPracticeItem(practiceItemId).catch(() => null);
            // The screen may have unmounted while the optional title lookup was
            // in flight. Never route a stale result; retain its retry key so the
            // still-current surface can recover it authoritatively.
            if (abandonLoad()) return;
            const routed = await routeAfterAttempt(recovery.result, recoveredItem, abandonLoad);
            if (!routed) return;
            // Route first, then acknowledge. If routing mounts a new item and
            // it saves before this call lands, the sidecar's atomic key compare
            // preserves that newer checkpoint instead of deleting by session.
            await acknowledgeCheckpoint(practiceItemId, retryKey);
            return;
          }
          if (recovery.status !== "pending" || recovery.result !== null) {
            throw new Error("The saved submission recovery response was malformed.");
          }
        } catch (error) {
          if (cancelled) return;
          const recovery = committedAttemptRecovery(error);
          if (recovery) setCommittedRecovery(recovery);
          else setItemLoadError(errorMessage(error, "Could not verify the saved submission before reopening practice."));
          return;
        }
      }

      // No committed result exists, so this really is an item serve. The
      // session id lets the sidecar decide (and bound) the §3.A6 elicitation;
      // a plan-off pick's proposal records its delivery with this serve.
      api.getPracticeItem(practiceItemId, session.sessionId, proposalOriginRef.current)
        .then((detail) => {
          if (cancelled) return;
          teachBackRef.current = detail.practiceMode === "teach_back";
          setItem(detail);
          setSelfGrade((current) => ({
            ...current,
            criterionPoints: Object.fromEntries((detail.rubric?.criteria ?? []).map((criterion) => [criterion.id, 0])),
            errorAttributions: []
          }));
        })
        .catch((error) => {
          if (!cancelled) setItemLoadError(errorMessage(error, "Could not load this practice item."));
        });
      // Committing the presentation is the serve event (§5.1). Only a
      // successful `active:false` response means ordinary practice.
      api.getProbeContract(practiceItemId, session.sessionId)
        .then((contract) => {
          if (cancelled) return;
          setProbe(activeProbeContract(contract));
          setProbeLoadState("ready");
        })
        .catch((error) => {
          if (cancelled) return;
          setProbe(null);
          setProbeLoadError(errorMessage(error, "Could not verify whether this is a diagnostic item."));
          setProbeLoadState("error");
        });
    };
    void recoverOrLoad();
    return () => { cancelled = true; };
  }, [loadRevision, practiceItemId, restoredSubmissionId, session.sessionId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void flushDraft().catch((error) => onError(errorMessage(error, "Could not save the practice draft.")));
    }, 350);
    return () => clearTimeout(timer);
  }, [answer, flushDraft, hintsUsed, hintSeen, pageSeen, onError, practiceItemId, session.sessionId, stuck]);

  useEffect(() => {
    return () => {
      void flushDraft().catch((error) => onError(errorMessage(error, "Could not save the practice draft.")));
      // Reported only on unmount — reporting on every debounced flush would
      // loop the draft back through restoredAnswer while the user is typing.
      // Also reported while a vault switch is freezing the screen: if the
      // switch then fails, App restores this item from the mirror; if it
      // succeeds, App drops the mirror with the rest of the old vault's state.
      if (!draftSavingDisabled()) {
        const { practiceItemId: id, answerMd, hintsUsed: hints, submissionId: retryKey, declaredStuck,
                planPresentationId: presentation } = latestDraft.current;
        const frozen = disclosedRef.current;
        onDraftSaved({ practiceItemId: id, answerMd, hintsUsed: hints, submissionId: retryKey, declaredStuck,
                       planPresentationId: presentation,
                       selfGradeDisclosure: frozen ? { submissionId: retryKey, ...frozen } : null,
                       firstHintProgress: firstHintRef.current, hintSeen: hintSeenRef.current,
                       ...(latestDraft.current.pageSeen ? { pageSeen: true } : {}) });
      }
    };
  }, [flushDraft, onError, onDraftSaved]);

  useCloseWithFlush(flushDraft, onError);

  const practiceReady = item !== null && probeLoadState === "ready";
  const probeActive = Boolean(probe?.active && probe.presentationId);
  const interactionReady = practiceReady && committedRecovery === null && !vaultChanging;

  // RW2a: "Work in steps" on an ordinary serve (never a diagnostic check, a
  // teach-back, a guided redo or a primed retry), behind workbench.enabled.
  // An open workbench stays mounted through a vault switch's freeze: it
  // registers its own steps with the switch and pauses itself (review F8).
  const workbenchAvailable = algoConfig().workbench && practiceReady && committedRecovery === null && !probeActive && !isTeachBack && !redo && !primed;
  const workbenchOffered = workbenchAvailable && !vaultChanging;
  const [wbSession, setWbSession] = useState<WorkbenchSessionDto | null>(null);
  // The item's problems in steps, looked up for this item (final
  // verification F2): Submit waits for the lookup, and a failed one is never
  // read as "no assistance" (the server folds a problem's assistance in
  // either way; this is what the learner is shown before Submit).
  const [wbItems, setWbItems] = useState<{ itemId: string | null; sessions: WorkbenchSummaryDto[]; state: "pending" | "ready" | "failed" }>(
    { itemId: null, sessions: [], state: "pending" },
  );
  const wbAutoOpened = useRef(false);
  const wbOrigin = planPresentationId ? "plan" : "practice";
  const wbEntry = wbOrigin === "plan" ? "plan" : "practice_screen";
  // The hints already shown on the answer box go with the work into steps,
  // and come back from it (review F2): the session holds the count, so the
  // record line and the submit read one durable number.
  const hintsUsedRef = useRef(hintsUsed);
  hintsUsedRef.current = hintsUsed;
  // The answer box's assistance as steps take it over: its hints, and a book
  // a problem counted (the server counts a book once, so it is never doubled).
  const carriedRef = useRef({ hints: hintsUsed, book: false });
  // The serve this screen answers goes on the problem, so a resume elsewhere
  // still submits as it (review F13).
  const serveRef = useRef({ schedulerCandidateId: schedulerCandidateId ?? null, planPresentationId: planPresentationId ?? null });
  serveRef.current = { schedulerCandidateId: schedulerCandidateId ?? null, planPresentationId: planPresentationId ?? null };
  // Adaptive hints H2b (review F2; fix round 3, ruling R2): before the
  // answer box is hidden, the hints still being written are held (cancelled,
  // or read once when shown first; a job whose outcome is unknown is kept and
  // read when the answer box is back) and every poll stops, so none is
  // delivered where the learner cannot see it. Nothing about the hints goes
  // with the work: the problem's submit folds the hints the server showed on
  // the answer box itself (ruling R1). Off, the hold is a no-op.
  const enteringSteps = useRef(false);
  // Fix round 4, F11: one answer box -> steps transition at a time. A second
  // open or resume while one is in flight is ignored, and a failed one
  // gives the hints back only when it is still the latest transition and
  // the answer box is the surface showing.
  const transition = useRef({ token: 0, busy: false });
  const stepsShown = useRef(false);
  const beginTransition = useCallback((): number | null => {
    if (transition.current.busy) return null;
    transition.current = { token: transition.current.token + 1, busy: true };
    return transition.current.token;
  }, []);
  const endTransition = useCallback((token: number) => {
    if (transition.current.token === token) transition.current = { ...transition.current, busy: false };
  }, []);
  const handOff = useCallback(async (): Promise<number> => {
    enteringSteps.current = true;
    await adaptiveHints.hold();
    return adaptiveHints.holdGeneration();
  }, [adaptiveHints.hold, adaptiveHints.holdGeneration]);
  const handOffFailed = useCallback((token: number, heldAt: number | undefined) => {
    if (token !== transition.current.token || stepsShown.current) return;
    enteringSteps.current = false;
    adaptiveHints.resume(heldAt);
  }, [adaptiveHints.resume]);
  const showSteps = useCallback((next: WorkbenchSessionDto) => {
    stepsShown.current = true;
    setWbSession(next);
  }, []);
  const openWorkbench = useCallback(async () => {
    if (!item) return;
    const token = beginTransition();
    if (token === null) return;
    let heldAt: number | undefined;
    try {
      heldAt = await handOff();
      const result = await api.workbenchOpen({
        origin: wbOrigin, entry: wbEntry, practiceItemId: item.id, stemMd: item.prompt,
        carriedHints: carriedRef.current.hints, carriedBook: carriedRef.current.book, ...serveRef.current,
        practiceSessionId: session.sessionId ?? null,
        // Astra batch review: the draft's key, so its Ask thread and budget
        // stay this attempt's when the steps are resumed in the Reader.
        submissionId: submissionId.current,
      });
      showSteps(result.session);
    } catch (error) {
      handOffFailed(token, heldAt);
      onError(errorMessage(error, "Couldn't open the step workbench."));
    } finally {
      endTransition(token);
    }
  }, [beginTransition, endTransition, handOff, handOffFailed, item, onError, session.sessionId, showSteps, wbEntry, wbOrigin]);
  const resumeWorkbench = useCallback(async (entry: WorkbenchSummaryDto) => {
    const token = beginTransition();
    if (token === null) return;
    let heldAt: number | undefined;
    try {
      heldAt = await handOff();
      // One explicit resume: reopened when set aside, and moved here when it
      // was worked in the Reader (no book on this screen; review F4).
      const result = await api.workbenchOpen({
        origin: wbOrigin, entry: wbEntry, sessionId: entry.sessionId,
        carriedHints: carriedRef.current.hints, carriedBook: carriedRef.current.book, ...serveRef.current,
        practiceSessionId: session.sessionId ?? null,
        submissionId: submissionId.current,
      });
      showSteps(result.session);
    } catch (error) {
      handOffFailed(token, heldAt);
      onError(errorMessage(error, "Couldn't reopen your steps."));
    } finally {
      endTransition(token);
    }
  }, [beginTransition, endTransition, handOff, handOffFailed, onError, session.sessionId, showSteps, wbEntry, wbOrigin]);
  const backToAnswerBox = useCallback((closing: WorkbenchSessionDto | null) => {
    // The authored hints revealed, and only those: the answer box's reveal
    // index (fix F15: an earlier attempt's help is never one of them).
    const carried = closing?.carriedHints ?? 0;
    // Hints seen count as seen, even when the item shows fewer today (the
    // authored hints changed since): never clamped to the list (final F2).
    if (carried > 0) setHintsUsed((value) => Math.max(value, carried));
    // Every assist the problem held comes back: its hints and its book (F2).
    if (closing?.record.bookCounted) setBookLeft(true);
    // Fix F15: an earlier attempt's help the problem carries comes back as
    // itself (the panel says it is counted; the server's submit counts it).
    const earlier = closing?.earlierOpened === true;
    if (earlier) setEarlierCountedFor(submissionId.current);
    if (carried > 0 || closing?.record.bookCounted || earlier) {
      // AD1 fix round 5 (V4): carried hints arrive untimed; with no marker
      // yet, this attempt's first hint is behind it, timing unknown.
      firstHint.noteUntimedHint();
      seeHint();
    }
    stepsWorkRef.current = null;
    setWbSession(null);
  }, [item, firstHint.noteUntimedHint, seeHint]);
  const refreshWbItemSessions = useCallback(() => {
    if (!item) return;
    const itemId = item.id;
    // A refresh of a lookup that landed keeps showing what it found; a first
    // lookup (or a retry of a failed one) holds Submit until it answers.
    setWbItems((current) => (current.itemId !== itemId
      ? { itemId, sessions: [], state: "pending" }
      : current.state === "failed" ? { ...current, state: "pending" } : current));
    void api.workbenchForItem({ practiceItemId: itemId })
      .then((result) => setWbItems((current) => (current.itemId === itemId ? { itemId, sessions: result.sessions, state: "ready" } : current)))
      .catch(() => setWbItems((current) => (current.itemId === itemId && current.state !== "ready" ? { ...current, state: "failed" } : current)));
  }, [item]);
  useEffect(() => {
    if (!workbenchOffered) return;
    refreshWbItemSessions();
    if (!wbAutoOpened.current && rememberedWorkInSteps()) {
      wbAutoOpened.current = true;
      void openWorkbench();
    }
  }, [workbenchOffered, refreshWbItemSessions, openWorkbench]);
  const wbItemSessions = item && wbItems.itemId === item.id ? wbItems.sessions : [];
  // Submit waits while this item's problems are being looked up.
  const assistPending = workbenchOffered && item !== null && (wbItems.itemId !== item.id || wbItems.state === "pending");
  const assistLookupFailed = workbenchOffered && item !== null && wbItems.itemId === item.id && wbItems.state === "failed";
  const assistPendingRef = useRef(assistPending);
  assistPendingRef.current = assistPending;
  const wbOpenEntry = wbItemSessions.find((entry) => entry.status === "open") ?? wbItemSessions.find((entry) => entry.status === "abandoned") ?? null;
  const stepsMode = workbenchAvailable && wbSession !== null;
  stepsShown.current = stepsMode;
  // H2b review F2: hints are asked for again once the answer box is back.
  useEffect(() => {
    if (stepsMode) {
      enteringSteps.current = false;
    } else if (!enteringSteps.current) {
      adaptiveHints.resume();
    }
  }, [stepsMode, adaptiveHints.resume]);
  // A book counted on this problem, in steps left this visit or on its open
  // problem (after a restart too), counts on the answer box as one hint.
  const bookCarried = bookLeft || wbItemSessions.some((entry) => entry.status === "open" && entry.bookCounted === true);
  // Reader CA1 (Q12): the original page opened before Submit is the same
  // book, so it joins the book component (one hint-equivalent however many
  // ways the book was seen); it goes into steps as a carried book too.
  const bookCounts = bookCarried || pageSeen;
  // Reader CA2 (K6, Q2): an earlier attempt's help opened before Submit is
  // one hint-equivalent. Codex review F1: the submit counts it server-side,
  // from the draft's checkpoint, so it is never in the client's count.
  const earlierCounted = earlierCountedFor !== null && earlierCountedFor === submissionId.current;
  const answerHints = hintsUsed + (bookCounts ? 1 : 0);
  carriedRef.current = { hints: hintsUsed, book: bookCounts };
  // A carried book is a hint the marker never timed (fix round 4, V4).
  if (bookCarried) firstHint.noteUntimedHint();
  useEffect(() => {
    if (bookCarried) seeHint();
  }, [bookCarried, seeHint]);

  useEffect(() => {
    onAskAvailabilityChange(interactionReady && !probeActive && !isTeachBack);
    return () => onAskAvailabilityChange(false);
  }, [interactionReady, isTeachBack, onAskAvailabilityChange, probeActive]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if (vaultFrozen.current) return;
      // Reader CA1: the original page is a modal; it owns the keys (its Esc closes it).
      if (originalPageOpen.current) return;
      // RW2a: in steps, the workbench owns the keys (Esc twice is Leave for now).
      // Owner capture 2026-10-25 (B1): Ask's `?` still opens the tutor (the
      // workbench handles it when it has focus; here when nothing does).
      if (stepsMode) {
        if (event.key === "?" && !event.ctrlKey && !event.metaKey && !event.defaultPrevented
            && !isTypingTarget(event.target) && interactionReady) {
          event.preventDefault();
          openAsk();
        }
        return;
      }
      if (committedRecovery) {
        if (event.key.toLowerCase() === "r") {
          event.preventDefault();
          setLoadRevision((value) => value + 1);
        }
        return;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        onBack();
        return;
      }
      // Until both the item and its diagnostic contract are verified, all
      // actions except leaving the screen remain closed.
      if (!interactionReady) return;
      const ctrl = event.ctrlKey || event.metaKey;
      if (ctrl && event.key === "Enter") {
        // Teach-back conversations handle ^enter themselves (send turn).
        if (!isTeachBack) {
          event.preventDefault();
          void submit();
        }
      } else if (ctrl && event.key.toLowerCase() === "h") {
        event.preventDefault();
        if (!isTeachBack) revealHint();
      } else if (ctrl && event.key.toLowerCase() === "d") {
        event.preventDefault();
        if (!isTeachBack) {
          if (stuckPrompt) pressStuck();
          else void dontKnow();
        }
      } else if (ctrl && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void skip();
      } else if (event.key === "?" && !ctrl && !isTypingTarget(event.target)) {
        event.preventDefault();
        if (isTeachBack) {
          // No hints in teach-back: the tutor could leak what the naive
          // student is probing for.
          onError("ask-tutor is disabled during a teach-back conversation.");
        } else if (probeActive) {
          // §5.5: Ask Tutor is disabled during a diagnostic block; the escape
          // hatch is the explicit stop-and-teach action, which ends measurement.
          onError("ask-tutor is disabled during a diagnostic check — use “stop diagnosing & teach me” instead.");
        } else {
          openAsk();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // Recompute the editor cap whenever the layout around it can shift: content
  // (which can rewrap the prompt), hint reveals, the self-grade panel, item
  // swaps, and window resizes. A ResizeObserver catches everything else.
  useLayoutEffect(() => {
    recomputeEditorMax();
  }, [answer, hintsUsed, fallbackRequired, selfGradeVisible, item, recomputeEditorMax]);

  useEffect(() => {
    const onResize = () => recomputeEditorMax();
    window.addEventListener("resize", onResize);
    const observer = new ResizeObserver(() => recomputeEditorMax());
    if (belowRef.current) observer.observe(belowRef.current);
    return () => {
      window.removeEventListener("resize", onResize);
      observer.disconnect();
    };
  }, [recomputeEditorMax]);

  const scorePreview = useMemo(() => {
    if (!item?.rubric) return 0;
    let score = Math.round(Object.values(selfGrade.criterionPoints).reduce((sum, value) => sum + Number(value || 0), 0));
    score = Math.max(0, Math.min(item.rubric.maxPoints, score));
    for (const fatalId of selfGrade.fatalErrors ?? []) {
      const fatal = item.rubric.fatalErrors.find((candidate) => candidate.id === fatalId);
      if (fatal) score = Math.min(score, fatal.maxGrade);
    }
    return score;
  }, [item, selfGrade]);

  // A check on your own: a hint would void it (apply_attempt rejects a hinted
  // or primed cold retry), so the plain card offers none and says why.
  const onYourOwnCheck =
    item?.activeFollowupKind === "cold_retry" || item?.activeFollowupKind === "certification_cold_probe";

  // Daily-loop DL2: a due "Check once" is a check on your own (Reader §9.3
  // item 10). Help is never blocked: the first press opens the help ladder,
  // whose header states the consequence before anything is shown; taking a
  // rung (its button, or the hint key again) is the ladder's ordinary
  // choose-then-take step, with no confirmation dialog (D42). Until feedback
  // the header names the book and nothing that locates the exercise (D46).
  // DL2 fix round 4 (F15): an item served as a diagnostic probe is measured
  // under the probe's duty; the contract carries the check's view for it
  // (chosen server-side: no help promised, no ladder header).
  const intentCheck = (probeActive ? probe?.intentCheck : undefined) ?? item?.intentCheck ?? null;

  // Reader CA1 (ux_reader_compare_ask_v1 §8): the problem as printed, as the
  // server allows it (D46: during a check on your own only the figure it
  // needs). The original page is the book left open: offered only where a
  // hint may be taken (never in a diagnostic block or on a cold follow-up,
  // which a hint would void) and not in steps, where this screen has no book
  // (UX §5.1: hidden while the book is hidden).
  const asPrinted = useAsPrinted(item?.id);
  const originalPageOffered = !probeActive && !onYourOwnCheck && !isTeachBack && !intentCheck?.locatorsHidden;
  function openOriginalPage(target: { extractionId: string; spanId: string; outlineSpanIds: string[] }) {
    if (!pageSeen && !bookCounts) firstHint.mark(attemptProgressRef.current);
    setPageSeen(true);
    seeHint();
    setOriginalPage(target);
  }
  const [checkHelpOpen, setCheckHelpOpen] = useState(false);
  useEffect(() => setCheckHelpOpen(false), [item?.id]);
  // Reader CA2 (§15 Q4): a cold follow-up the server serves with the take
  // step (its view carries the ladder header) offers help like any check on
  // your own; without it, the predecessor's "no hints on this one" stands.
  const coldTakeStep = onYourOwnCheck && Boolean(intentCheck?.helpHeader);
  const coldCheck = Boolean(intentCheck?.cold) || onYourOwnCheck;

  /** Reader CA2: the practice Ask's target, the attempt's key and the live
   *  draft read at send (§7.2), never the draft as it was when it opened. */
  function practiceAskTarget(extra?: Partial<AskTarget>): AskTarget {
    return {
      context: "practice",
      practiceItemId,
      sessionId: session.sessionId,
      ...askState(),
      submissionId: submissionId.current,
      readDraft: () => stepsWorkRef.current ?? answerRef.current,
      // The context line names the exercise, never during a check on your
      // own (D46: nothing that locates it).
      itemLabel: item?.canonicalExercise && !intentCheck?.locatorsHidden ? item.canonicalExercise.label : undefined,
      coldCheck,
      ...extra
    };
  }

  function onAskAnswered(answered: { eventId: string; hintEquivalent: boolean }) {
    setAskRecord((record) => (record.some((entry) => entry.eventId === answered.eventId) ? record : [...record, answered]));
    // §7.7: only a question about the maths changes the banner.
    if (coldCheck && answered.hintEquivalent) setAskConverted(true);
    refreshHelpRecord();
  }

  /** Codex review F7: read the attempt's help record (the server's fold). */
  const refreshHelpRecord = useCallback(() => {
    if (!panelOn || !session.sessionId || !practiceItemId) return;
    const key = submissionId.current;
    Promise.resolve(api.getTutorTranscript?.({ context: "practice", practiceItemId, sessionId: session.sessionId, submissionId: key }))
      .then((snapshot) => {
        if (!mountedRef.current || key !== submissionId.current || !snapshot?.helpRecord) return;
        setServerRecord(snapshot.helpRecord);
        if (snapshot.helpRecord.earlierOpened) setEarlierCountedFor(key);
      })
      .catch(() => undefined);
  }, [panelOn, practiceItemId, session.sessionId]);
  useEffect(() => {
    setServerRecord(null);
    setEarlierCountedFor(null);
    refreshHelpRecord();
  }, [refreshHelpRecord, restoredSubmissionId]);
  const shownHintCount = adaptiveHints.entries.length;
  useEffect(() => {
    if (shownHintCount > 0) refreshHelpRecord();
  }, [shownHintCount, refreshHelpRecord]);

  /** Codex review F2 (K9): take worked help from the ladder after an Ask
   *  answer was withheld (recorded as that rung only if taken). */
  const takeWorkedFromAsk = adaptive && !probeActive && !isTeachBack
    ? (level: 4 | 5) => { void adaptiveHints.takeWorked(level); }
    : undefined;

  // Esc returns focus to where it was when the panel opened (§7.1).
  const askReturnFocus = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (dockedAsk) askReturnFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  }, [dockedAsk]);
  function closeDockedAsk() {
    setDockedAsk(null);
    const back = askReturnFocus.current;
    askReturnFocus.current = null;
    window.setTimeout(() => back?.focus(), 0);
  }

  function onEarlierOpened() {
    if (earlierCountedFor === submissionId.current) return;
    const key = submissionId.current;
    setEarlierCountedFor(key);
    seeHint();
    // Codex review F1: recorded on the draft at once (its checkpoint is what
    // the submit counts), then the record is read back.
    latestDraft.current = { ...latestDraft.current, submissionId: key, earlierOpened: true };
    void saveDraft().catch(() => undefined).then(() => refreshHelpRecord());
  }

  function revealHint() {
    if (!practiceReady) return;
    if (simple && onYourOwnCheck && !coldTakeStep) {
      onError("No hints on this one: it's a check on your own.");
      return;
    }
    if (intentCheck?.helpHeader && !checkHelpOpen) {
      // D42: open the ladder first; its header says what taking help means.
      // Only on a check served cold: an item whose answer was seen is
      // practice already (Codex review F3), so help is taken as usual.
      setCheckHelpOpen(true);
      return;
    }
    if (probeActive) {
      // §5.5: authored hints are disabled during a diagnostic block.
      onError("hints are disabled during a diagnostic check — answer with what you know, or stop diagnosing.");
      return;
    }
    if (adaptive) {
      // Adaptive hints H2b: the press asks for a hint written for this work,
      // only where its panel is shown (review F2: never in steps, whichever
      // control was pressed).
      if (stepsMode || enteringSteps.current) return;
      void adaptiveHints.press();
      return;
    }
    revealAuthoredHint();
  }

  /** Today's authored path, exactly (with adaptive hints off, or when the
   *  sidecar answers that they are). */
  function revealAuthoredHint() {
    // Adaptive difficulty AD1: the first hint seen sets the progress marker.
    if (item && hintsUsed < item.hints.length) {
      firstHint.mark(attemptProgressRef.current);
      seeHint();
    }
    // Adaptive hints H0: the hint this press shows (none past the last one).
    if (item && session.sessionId && hintsUsed < item.hints.length) {
      recordHintReveal({ sessionId: session.sessionId, practiceItemId: item.id, submissionId: submissionId.current, authoredIndex: hintsUsed, answerMd: answer, revealedAt: new Date().toISOString() });
    }
    setHintsUsed((value) => Math.min(item?.hints.length ?? 0, value + 1));
  }

  /** Adaptive hints H2b: the item's hint `index`, taken instead of a hint
   *  still being written (the request was cancelled first): the client's
   *  own reveal, client-counted as before. Resolves to its telemetry row. */
  async function revealAuthoredAt(index: number): Promise<string | null> {
    if (!item || !session.sessionId) return null;
    firstHint.mark(attemptProgressRef.current);
    seeHint();
    // Counted at once for a hand-off into steps that reads it before the
    // next render (review F1); the render sets the ref from the state.
    carriedRef.current = { ...carriedRef.current, hints: carriedRef.current.hints + 1 };
    setHintsUsed((value) => value + 1);
    try {
      const recorded = await Promise.resolve(api.recordHintReveal?.({
        sessionId: session.sessionId, practiceItemId: item.id, submissionId: submissionId.current,
        authoredIndex: index, answerMd: answer, revealedAt: new Date().toISOString()
      }));
      return recorded?.assistId ?? null;
    } catch {
      return null;
    }
  }

  async function stopDiagnosing() {
    if (!item) return;
    try {
      await api.stopProbeDiagnosing(item.id);
      setProbe(null);
      // §3: measurement ends and tutoring begins. The typed transition
      // decision is already persisted, so the tutor opens proactively.
      openAsk({ proactiveOpen: true });
    } catch (error) {
      onError(errorMessage(error, "Could not stop the diagnostic check."));
    }
  }

  async function routeAfterAttempt(
    result: AttemptResultDto,
    recoveredItem: PracticeItemDetail | null = item,
    cancelled: () => boolean = () => false,
  ): Promise<boolean> {
    if (cancelled()) return false;
    const learningObjectId = recoveredItem?.learningObjectId ?? result.learningObjectId;
    const learningObjectTitle = recoveredItem?.learningObjectTitle ?? result.learningObjectId;
    // §5.7: the block just closed — the unified review covers every attempt
    // in it (releasedFeedback), not just the one that closed it.
    if (result.probeBlockEnd) {
      onBlockEnd(result.probeBlockEnd, learningObjectId, learningObjectTitle);
      return true;
    }
    // §5.6: feedback stays deferred while the diagnostic block is still
    // measuring — stay inside the block by jumping straight to whatever the
    // episode serves next, instead of round-tripping through the queue.
    if (result.probeEpisode?.feedbackDeferred) {
      try {
        const next = await api.getNextProbeItem(learningObjectId);
        if (cancelled()) return false;
        if (next.active && next.practiceItemId) {
          onContinueDiagnostic(next.practiceItemId);
          return true;
        }
      } catch (error) {
        if (cancelled()) return false;
        onError(errorMessage(error, "Could not open the next diagnostic item."));
      }
      if (cancelled()) return false;
      onBack();
      return true;
    }
    if (cancelled()) return false;
    onFeedback(result.attemptId);
    return true;
  }

  /** "I'm stuck": one tap opens the answer box with the stuck prompt. Nothing
   *  is recorded until Submit. */
  function pressStuck() {
    if (!practiceReady || isTeachBack) return;
    setStuck(true);
    const editor = editorSlotRef.current?.querySelector<HTMLElement>("[role=textbox]");
    editor?.focus();
  }

  /** Phase 4's plain self-grade shows a full answer: freeze the whole trace
   *  first (Codex review F1), and grade without the answer when the freeze is
   *  not confirmed. Every way into the plain self-grade goes through here. */
  async function freezeBeforeSelfGrade(itemId: string, key: string): Promise<void> {
    if (!item || !simple || disclosed || probeActive || !expectedAnswerText(item.expectedAnswer).trim()) return;
    const frozen = {
      answerMd: redo ? composeRedoAnswer(redo.learnerWorkPrefix, answer) : answer,
      explanationMd: whyLine.trim() || null
    };
    setSubmitting(true);
    try {
      await flushDraft();
      await api.recordSelfGradeDisclosure({ sessionId: session.sessionId, practiceItemId: itemId, submissionId: key, ...frozen });
      if (!mountedRef.current) return;
      setDisclosed(frozen);
      setDisclosureFailed(false);
    } catch {
      if (!mountedRef.current) return;
      setDisclosureFailed(true);
    } finally {
      if (mountedRef.current) setSubmitting(false);
    }
  }

  async function submit(gradeOverride?: SelfGradeInputDto) {
    if (!item || !interactionReady || submitting || assistPendingRef.current) return;
    const submittedItemId = item.id;
    const submittedKey = submissionId.current;
    // The plain self-grade's Got it / Partly / Missed submit the grade they
    // set, not the one state holds until the next render.
    const grade = gradeOverride ?? selfGrade;
    // An empty stuck answer has nothing to grade: it is scored 0 at once, so
    // it never asks for a self-grade either.
    const emptyStuck = stuck && !answer.trim() && !whyLine.trim() && !redo;
    // First Submit click when a self-grade is required only reveals the panel;
    // the actual attempt is submitted on the next click once it's been graded.
    if (fallbackRequired && !selfGradeVisible && !emptyStuck) {
      await freezeBeforeSelfGrade(submittedItemId, submittedKey);
      if (!mountedRef.current) return;
      setSelfGradeVisible(true);
      return;
    }
    // Phase 4's plain self-grade submits only through Got it / Partly /
    // Missed (or the detailed numbers): a second ^↵ must never send the
    // untouched all-zero grade as if the learner had chosen "Missed".
    if (simple && fallbackRequired && !gradeOverride && !selfGradeDetailsOpen && !emptyStuck) return;
    const validation = emptyStuck ? {} : validateSelfGrade(item, grade, fallbackRequired);
    setFieldErrors(validation);
    if (Object.keys(validation).length) return;
    setSubmitting(true);
    try {
      // The retry key must be durable before grading begins. If the app or
      // sidecar disappears after the attempt commits but before the response,
      // the restarted screen reuses this exact key and recovers the attempt.
      await flushDraft();
      if (!mountedRef.current) return;
      const result = await api.submitAttempt({
        sessionId: session.sessionId,
        practiceItemId: submittedItemId,
        // A guided redo submits the COMPOSED answer: the preserved (locked)
        // prefix plus the learner's rewritten portion, separated by a paragraph
        // break — mirroring repair_splice's end-append join. The grader sees
        // one whole answer; only the redo text was written now. A trace frozen
        // before a full answer was shown is sent exactly as frozen (F1).
        answerMd: disclosed ? disclosed.answerMd : redo ? composeRedoAnswer(redo.learnerWorkPrefix, answer) : answer,
        // Meas §3.A6 rule 3 made structural, and made structural on the WIRE:
        // the volunteered line is its own field, and the sidecar joins it into
        // the single trace the grader reads. The client never learns the
        // heading that delimits the line; the sidecar owns it. A
        // blank line is submitted as nothing at all; there is no representation
        // for "declined", so nothing can turn an empty field into a hint, a
        // skip, or a failure.
        explanationMd: disclosed ? disclosed.explanationMd : whyLine.trim() || null,
        // §12: an active diagnostic block forces the recording attempt type.
        attemptType: probeActive ? "diagnostic_probe" : chooseAttemptType(item.attemptTypesAllowed, answerHints),
        // The answer box's hints and a book counted in steps (review F2).
        hintsUsed: answerHints,
        // RW2b fix round 5: the authored reveals on their own; the server
        // adds the book and the workbench's help from its own records, once.
        authoredHints: hintsUsed,
        // Fix round 12: whether that count holds a book (its own component);
        // Reader CA1: the original page opened before Submit is that book.
        bookCounted: bookCounts,
        latencySeconds: elapsedSeconds(),
        primed,
        probePresentationId: probeActive ? probe?.presentationId : null,
        answerConfidence,
        assessmentContractVersionId: item.assessmentContractVersionId,
        submissionId: submittedKey,
        schedulerCandidateId,
        planPresentationId,
        // Drop attributions for any criterion the learner ultimately left at full
        // credit, so a restored score never ships a stale error tag.
        selfGrade:
          fallbackRequired && !emptyStuck
            ? { ...grade, errorAttributions: prunedAttributions(item, grade) }
            : null,
        // mvp-0.13: written after "I'm stuck" (it may be empty).
        ...(stuck ? { declaredStuck: true } : {}),
        // Adaptive difficulty AD1: only when tapped / set (logged only).
        ...(difficultyRating ? { difficultyRating } : {}),
        ...(firstHint.value ? { firstHintProgress: firstHint.value } : {})
      });
      suppressDraftFlush.current = true;
      if (!mountedRef.current) return;
      const routed = await routeAfterAttempt(result, item, () => !mountedRef.current);
      if (routed) await acknowledgeCheckpoint(submittedItemId, submittedKey);
    } catch (error) {
      const recovery = committedAttemptRecovery(error);
      if (recovery) {
        // An attempt id does not carry the authoritative post-submit route. In
        // particular, a diagnostic may still defer feedback or may have closed
        // a block. Keep the checkpoint/key and fail closed rather than opening
        // feedback or advancing from incomplete information.
        setCommittedRecovery(recovery);
        return;
      }
      const command = getCommandError(error);
      if (command?.code === "grading_fallback_required") {
        setFallbackRequired(true);
        // The grader went away mid-submit: the plain self-grade opens the
        // same way as the first Submit, frozen before any full answer (F1).
        if (!emptyStuck) await freezeBeforeSelfGrade(submittedItemId, submittedKey);
        if (!mountedRef.current) return;
        setSelfGradeVisible(true);
        // The plain self-grade says so itself ("AI grading isn't available
        // right now"); the raw reason is not a learner's notice.
        if (!simple) onError(command.message);
      } else {
        onError(errorMessage(error, "Could not submit this attempt."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function dontKnow() {
    if (!item || !interactionReady || submitting || assistPendingRef.current) return;
    const submittedItemId = item.id;
    const submittedKey = submissionId.current;
    setSubmitting(true);
    try {
      await flushDraft();
      if (!mountedRef.current) return;
      const result = await api.submitDontKnow({
        sessionId: session.sessionId,
        practiceItemId: submittedItemId,
        hintsUsed: answerHints,
        authoredHints: hintsUsed,
        bookCounted: bookCounts,
        latencySeconds: elapsedSeconds(),
        probePresentationId: probeActive ? probe?.presentationId : null,
        answerConfidence,
        assessmentContractVersionId: item.assessmentContractVersionId,
        submissionId: submittedKey,
        schedulerCandidateId,
        planPresentationId,
        ...(difficultyRating ? { difficultyRating } : {}),
        ...(firstHint.value ? { firstHintProgress: firstHint.value } : {})
      });
      suppressDraftFlush.current = true;
      if (!mountedRef.current) return;
      const routed = await routeAfterAttempt(result, item, () => !mountedRef.current);
      if (routed) await acknowledgeCheckpoint(submittedItemId, submittedKey);
    } catch (error) {
      const recovery = committedAttemptRecovery(error);
      if (recovery) {
        setCommittedRecovery(recovery);
      } else {
        onError(errorMessage(error, "Could not record “I don't know”."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function skip() {
    if (!item || !interactionReady) return;
    const skippedIdentity = { practiceItemId: item.id, submissionId: submissionId.current };
    try {
      await api.skipPracticeItem({ sessionId: session.sessionId, practiceItemId: item.id });
      if (!mountedRef.current) return;
      suppressDraftFlush.current = true;
      // skip_practice_item owns its checkpoint delete; only mirror that clear
      // locally when this is still the item/key App knows about.
      onCheckpointCleared(skippedIdentity);
      onBack();
    } catch (error) {
      onError(errorMessage(error, "Could not skip this practice item."));
    }
  }

  async function acknowledgeCheckpoint(practiceItemId: string, expectedSubmissionId: string): Promise<boolean> {
    if (vaultFrozen.current) return false;
    try {
      const result = await api.acknowledgePracticeSubmission({
        sessionId: session.sessionId,
        practiceItemId,
        submissionId: expectedSubmissionId,
      });
      if (!result.acknowledged || result.status === "checkpoint_mismatch") return false;
      onCheckpointCleared({ practiceItemId, submissionId: expectedSubmissionId });
      return true;
    } catch (error) {
      onError(errorMessage(error, "Could not acknowledge the saved practice result."));
      return false;
    }
  }

  const loadError = itemLoadError ?? probeLoadError;
  if (committedRecovery && simple) {
    // §7.4 "Submission needs recovery": one plain line and one action; the
    // attempt id and the raw message go in details.
    return (
      <div className="screen">
        <div className="screen-scroll">
          <Card focused>
            <div style={{ lineHeight: 1.6 }}>Your answer is saved. LearnLoop is finishing the grading.</div>
            <div className="form-row" style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center" }}>
              <PrimaryAction hotkey="r" disabled={submitting} onClick={() => setLoadRevision((value) => value + 1)}>Try again</PrimaryAction>
              <DetailsToggle open={cardDetailsOpen} onToggle={() => setCardDetailsOpen((open) => !open)} />
            </div>
            {cardDetailsOpen ? (
              <div style={{ ...quietLine, fontFamily: FONT_MONO, marginTop: 8 }}>
                attempt {committedRecovery.attemptId} · {committedRecovery.message}
              </div>
            ) : null}
          </Card>
        </div>
        <KeyBar keys={[{ key: "r", label: "try again" }]} />
      </div>
    );
  }

  if (committedRecovery) {
    const diagnostic = committedRecovery.attemptType === "diagnostic_probe" || probeActive;
    return (
      <div className="screen">
        <div className="screen-scroll">
          <SectionHeader>Attempt recorded · route recovery required</SectionHeader>
          <Card focused>
            <div style={{ color: COLOR.amber, lineHeight: 1.6 }}>
              Your answer was recorded once. LearnLoop kept its saved submission key and will not grade it again.
            </div>
            <div style={{ color: COLOR.textDim, lineHeight: 1.6, marginTop: 8 }}>
              {diagnostic
                ? "The diagnostic result did not include enough durable routing information to decide whether feedback is still deferred or the block ended. Feedback and block advancement remain locked."
                : "The full completion route could not be recovered, so LearnLoop has not opened feedback or advanced the session."}
            </div>
            <div style={{ color: COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 11, marginTop: 8 }}>
              attempt {committedRecovery.attemptId} · {committedRecovery.message}
            </div>
            <div className="form-row" style={{ marginTop: 14 }}>
              <button
                className="queue-row focused"
                type="button"
                disabled={submitting}
                onClick={() => setLoadRevision((value) => value + 1)}
              >
                <span className="queue-title">{submitting ? "Recovering..." : "Retry safe recovery"}</span>
              </button>
            </div>
          </Card>
        </div>
        <KeyBar keys={[{ key: "r", label: "retry same saved submission" }]} />
      </div>
    );
  }

  if (loadError && simple) {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <Card focused>
            <div style={{ lineHeight: 1.6 }} role="alert">This question isn't available any more.</div>
            <div className="form-row" style={{ marginTop: 14 }}>
              <PrimaryAction onClick={onBack}>Next question</PrimaryAction>
              <QuietAction onClick={() => setLoadRevision((value) => value + 1)}>Try again</QuietAction>
            </div>
          </Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "back" }]} />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="screen">
        <div className="screen-scroll">
          <SectionHeader>Practice item unavailable</SectionHeader>
          <Card focused>
            <div style={{ color: COLOR.red, lineHeight: 1.6 }}>{loadError}</div>
            <div className="form-row" style={{ marginTop: 14 }}>
              <button className="queue-row focused" type="button" onClick={() => setLoadRevision((value) => value + 1)}>
                <span className="queue-title">Retry loading</span>
              </button>
              <button className="queue-row" type="button" onClick={onBack}>
                <span className="queue-title">Back to Today</span>
              </button>
            </div>
          </Card>
        </div>
        <KeyBar keys={[{ key: "esc", label: "today" }]} />
      </div>
    );
  }

  if (vaultChanging) {
    return <div className="screen-scroll"><Card>Saving practice before opening the next vault...</Card></div>;
  }

  if (!practiceReady || !item) {
    return (
      <div className="screen-scroll">
        <Card>{simple ? "Loading the question…" : item ? "Verifying diagnostic safeguards..." : "Loading practice item..."}</Card>
      </div>
    );
  }

  const dockedPanel = dockedAsk && panelOn && !stepsMode ? (
    <AskOverlay
      variant="docked"
      target={dockedAsk}
      onClose={closeDockedAsk}
      onToast={onError}
      onAnswered={onAskAnswered}
      onEarlierOpened={onEarlierOpened}
      onTakeWorked={takeWorkedFromAsk}
    />
  ) : null;

  return (
    <div className="screen">
      <DockedAsk panel={dockedPanel}>
      <div className="screen-scroll">
        {simple ? null : <SectionHeader>Practice item</SectionHeader>}
        <Card focused>
          {simple ? (
            // §7.4 W5: the topic, and ⋯ for the card's controls. The item id,
            // the mode, the grader and the estimate are receipts (details).
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, fontSize: 13 }}>
              <span style={{ color: COLOR.textDim }}>{item.learningObjectTitle}</span>
              {/* An honest label, quiet (§4.2): a primed retry or a redo is
                  practice with help. */}
              {primed && !onYourOwnCheck ? <span style={quietLine}>◌ with help</span> : null}
              <span style={{ flex: 1 }} />
              {!probeActive ? (
                <button
                  type="button"
                  style={quietLink}
                  aria-expanded={controlsOpen}
                  aria-label="more for this question"
                  onClick={() => setControlsOpen((open) => !open)}
                >
                  ⋯
                </button>
              ) : null}
            </div>
          ) : (
          <div className="queue-meta">
            <EntityLink id={item.id} onInspect={onInspect} />
            <EntityLink id={item.learningObjectId} onInspect={onInspect}>{item.learningObjectTitle}</EntityLink>
            <Pill tone={modePillColor(item.practiceMode)}>{item.practiceMode}</Pill>
            {item.subject ? <Pill tone="slate">{item.subject}</Pill> : null}
            {fallbackRequired ? <Pill tone="amber">self-grade required</Pill> : <Pill tone="green">{gradingProvider} grading</Pill>}
          </div>
          )}
          {probeActive && simple ? (
            // §7.4: a short check looks like any other question, with one
            // line on when feedback comes and the way out into teaching.
            <div style={{ ...quietLine, marginTop: 8, display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
              <span>Feedback comes when this short check ends · hints are off for now</span>
              <button type="button" style={quietLink} onClick={() => setCheckWhyOpen((open) => !open)} aria-expanded={checkWhyOpen}>
                why? {checkWhyOpen ? "▾" : "▸"}
              </button>
              <span style={{ flex: 1 }} />
              <QuietAction onClick={() => void stopDiagnosing()}>Teach me instead</QuietAction>
              {checkWhyOpen ? (
                <div style={{ flexBasis: "100%" }}>To see which of two things to help with next. Answer with what you know.</div>
              ) : null}
            </div>
          ) : probeActive ? (
            <div className="hint-banner" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <Pill tone="cyan">Diagnostic check</Pill>
                {probe?.valueStopping ? (
                  <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
                    question {probe?.observationNumber ?? 1} · continues while the next question is worth your time
                  </span>
                ) : (
                  <>
                    <BlockBar
                      value={(probe?.observationNumber ?? 1) - 1}
                      max={probe?.maximumObservations ?? 4}
                      width={probe?.maximumObservations ?? 4}
                      color={COLOR.cyan}
                    />
                    <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
                      question {probe?.observationNumber ?? 1} of up to {probe?.maximumObservations ?? 4}
                    </span>
                  </>
                )}
                <span style={{ fontSize: 12, opacity: 0.75 }}>
                  Answer with what you know — this helps find exactly where to focus next. Full
                  feedback arrives once this short check wraps up; hints and ask-tutor are paused
                  for now.
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="queue-row"
                  style={{ marginLeft: "auto" }}
                  onClick={() => void stopDiagnosing()}
                  title="end the diagnostic block and start tutoring"
                >
                  stop diagnosing &amp; teach me
                </button>
              </div>
            </div>
          ) : null}
          {/* 1f: a cold-lane follow-up (repair cold retry / certification cold
              probe) is one delayed unassisted measurement. apply_attempt hard-
              rejects it hinted or primed ("a cold retry must be unassisted and
              unprimed"), so say that HERE, next to where the hint key lives,
              before the learner voids it.

              The marker is deliberately PROVENANCE-FREE: naming the repair (or
              the factor) this check verifies would point the learner straight at
              the material the check exists to measure them retrieving unaided.
              What it verifies is said afterwards, in the feedback banner. */}
          {intentCheck?.banner ? (
            // DL2: the cold banner (Reader §9.3 item 10), provenance-free.
            // Reader CA2 (§7.7): it changes only after a question about the
            // maths; a clarification leaves it as it was.
            <div className="hint-banner" role="status" data-testid="intent-check-banner" style={{ borderColor: COLOR.amber }}>
              {askConverted ? ASK_COPY.convertedBanner : intentCheck.banner}
            </div>
          ) : null}
          {coldTakeStep ? null : simple && onYourOwnCheck ? (
            // The quiet line (§7.4, Reader doc U11), provenance-free: naming
            // what it checks would hand over the material it measures.
            <div style={{ ...quietLine, marginTop: 8 }}>
              {primed
                ? "On your own · this one can't count when it's opened from feedback. Go back and open it from Today."
                : "On your own · no hints on this one"}
            </div>
          ) : item.activeFollowupKind === "cold_retry" || item.activeFollowupKind === "certification_cold_probe" ? (
            <div className="hint-banner" style={{ borderColor: COLOR.amber }}>
              <Pill tone="amber">unassisted check</Pill>{" "}
              {primed
                ? "this question is due as an unassisted check, but it was opened primed — the attempt will be rejected. Go back and open it from the queue instead."
                : "hints will void this measurement and the attempt will be rejected. Answer with what you can retrieve on your own."}
            </div>
          ) : null}
          {item.mastery != null && !simple ? (
            <div className="queue-meta" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <Faint style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>mastery estimate</Faint>
              <BlockBar value={item.mastery.mean} width={10} color={masteryTone(item.mastery.mean, COLOR)} />
              <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{item.mastery.mean.toFixed(2)}</span>
              <Faint>±{Math.sqrt(item.mastery.variance).toFixed(2)}</Faint>
            </div>
          ) : null}
          {/* Meas §3.A2/§3.A3: the whole stimulus, not just the prompt. An
              error hunt's worked solution and a laddered-stem part's shared
              setup are as load-bearing as the question itself, and this is the
              renderer both practice and exams mount so a surface cannot carry
              one and forget the other. */}
          {/* In steps, the problem as the session froze it (RW2a review F1):
              the statement and required method it is graded against. */}
          <ItemPresentation presentation={stepsMode && wbSession?.presentation ? wbSession.presentation : item.presentation} />
          {/* Reader CA1: the problem as printed, free (its own blocks only). */}
          <AsPrinted key={`${item.id}:${asPrinted?.kind ?? "none"}`} view={asPrinted} practiceItemId={item.id} altText={item.prompt} />
          {/* Adaptive difficulty AD2+AD3 (§12): why the plan's draw chose this item, one quiet line. */}
          <WhyThisItem planPresentationId={planPresentationId} />
          {item.canonicalExercise && intentCheck?.locatorsHidden ? (
            // DL2 (D46, G61): during a check on your own, the book's name only:
            // no exercise number, page, section, link or why until feedback.
            <div className="queue-meta" data-testid="canonical-exercise" style={{ fontSize: 11 }}>
              <Faint>From {item.canonicalExercise.sourceTitle?.trim() || "your book"}</Faint>
            </div>
          ) : item.canonicalExercise ? (
            // Canonical sources S1: where this exercise comes from and how far
            // its answer key has been checked, said plainly.
            <div className="queue-meta" data-testid="canonical-exercise" style={{ fontSize: 11 }}>
              <Faint>
                From {item.canonicalExercise.sourceTitle?.trim() || "your book"}
                {item.canonicalExercise.label?.trim() ? `: ${item.canonicalExercise.label.trim()}` : ""}
                {item.canonicalExercise.relation === "variant_of" ? " (a variant)" : ""}
                {printedPageLabel(asPrinted) ? ` · ${printedPageLabel(asPrinted)}` : ""}
                {item.canonicalExercise.keyLabel ? ` · ${item.canonicalExercise.keyLabel}` : ""}
              </Faint>
              {originalPageOffered && !stepsMode ? (
                <>
                  {" · "}
                  <OriginalPageLink view={asPrinted} costs={!bookCounts} onOpen={openOriginalPage} />
                </>
              ) : null}
            </div>
          ) : asPrinted?.kind === "page" && asPrinted.locator && !intentCheck?.locatorsHidden ? (
            // Reader CA1 (Codex review F4): a problem imported from a Reader
            // selection has no canonical exercise, but its page is the book's:
            // the same locator and original page, as the server allows them.
            <div className="queue-meta" data-testid="printed-locator" style={{ fontSize: 11 }}>
              <Faint>From {asPrinted.locator.sourceTitle?.trim() || "your book"} · {printedPageLabel(asPrinted)}</Faint>
              {originalPageOffered && !stepsMode ? (
                <>
                  {" · "}
                  <OriginalPageLink view={asPrinted} costs={!bookCounts} onOpen={openOriginalPage} />
                </>
              ) : null}
            </div>
          ) : null}
          {!probeActive && (!simple || controlsOpen) ? (
            <CardControls
              key={`${item.id}:${item.prompt}`}
              practiceItemId={item.id}
              prompt={item.prompt}
              expectedAnswer={null}
              onError={onError}
              onChanged={() => {
                api.getPracticeItem(item.id, session.sessionId)
                  .then(setItem)
                  .catch((error) => onError(errorMessage(error, "The card changed, but its updated practice view could not be loaded.")));
              }}
              onRetired={() => {
                // Retirement already clears the durable checkpoint server-side.
                // Suppress the unmount flush so this screen cannot recreate a
                // draft pointing at the card that was just retired.
                suppressDraftFlush.current = true;
                onCheckpointCleared();
                onBack();
              }}
              onTeachBack={isTeachBack ? undefined : onContinueDiagnostic}
              sessionId={session.sessionId}
              onKnowThis={
                item.placementActive
                  ? () => {
                      // The LO is now assumed known (not tested): its new items
                      // leave the queue, and its first review checks it. The
                      // report already cleared this card's durable draft in its
                      // own transaction; suppress the unmount flush so this
                      // screen cannot recreate it.
                      suppressDraftFlush.current = true;
                      onCheckpointCleared();
                      onBack();
                    }
                  : undefined
              }
            />
          ) : null}
          {item.sourceRefs.length > 0 && !simple && !intentCheck?.locatorsHidden ? (
            <div style={{ marginTop: 6, fontSize: 11, color: COLOR.textFaint, lineHeight: 1.6 }}>
              {item.sourceRefs.map((ref, index) => (
                <div
                  key={`${ref.refId}:${index}`}
                  title={[ref.refId, ref.quote].filter(Boolean).join("\n\n")}
                  style={{ display: "flex", gap: 8, alignItems: "baseline" }}
                >
                  <span style={{ color: COLOR.textDim }}>{ref.displayName}</span>
                  <span style={{ fontFamily: FONT_MONO }}>
                    {ref.locator ?? ref.path ?? ref.refType}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
          {isTeachBack ? (
            <TeachBackConversation
              key={item.id}
              session={session}
              item={item}
              schedulerCandidateId={schedulerCandidateId}
              restoredState={
                restoredTeachBack && restoredTeachBack.practiceItemId === item.id ? restoredTeachBack : null
              }
              onFeedback={onFeedback}
              onCheckpointCleared={onCheckpointCleared}
              markSubmitted={() => {
                suppressDraftFlush.current = true;
              }}
            />
          ) : (
          <>
          {redo && simple ? (
            // Redo the part you missed (§7.5): what to fix, and the learner's
            // correct work kept above the box. The step ids and the
            // measurement bookkeeping are receipts, not the learner's.
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 13, color: COLOR.text }}>Redo the part you missed</div>
              {redo.redoInstruction ? (
                <div style={{ ...quietLine, marginTop: 4 }}>What to fix: <span style={{ color: COLOR.text }}>{redo.redoInstruction}</span></div>
              ) : null}
              <div
                aria-label="your work so far, kept"
                style={{
                  borderLeft: `3px solid ${COLOR.green}`,
                  padding: "8px 12px",
                  marginTop: 8,
                  fontSize: 13,
                  lineHeight: 1.6,
                  opacity: 0.85
                }}
              >
                <div style={{ ...quietLine, fontSize: 11 }}>Your work so far, kept</div>
                <MarkdownMath value={redo.learnerWorkPrefix} />
              </div>
              {redo.episodeId && redo.coldItemId ? (
                <div style={{ ...quietLine, marginTop: 6 }}>A check on your own comes back on another day.</div>
              ) : null}
            </div>
          ) : redo ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <Pill tone="amber">guided redo</Pill>
                <span style={{ fontSize: 12, color: COLOR.textDim }}>
                  your correct work is kept below — rewrite only the part that went wrong
                </span>
              </div>
              {redo.redoInstruction ? (
                <div style={{ marginTop: 6, fontSize: 12, color: COLOR.text, lineHeight: 1.55 }}>
                  <Faint>what to fix:</Faint> {redo.redoInstruction}
                </div>
              ) : null}
              {redo.failedCheckpointIds.length > 0 ? (
                <div style={{ marginTop: 4, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                  <Faint style={{ fontSize: 11 }}>failed steps</Faint>
                  {redo.failedCheckpointIds.map((checkpointId) => (
                    <Pill key={checkpointId} tone="red">{checkpointId}</Pill>
                  ))}
                </div>
              ) : null}
              <div
                aria-label="your preserved work (read-only)"
                style={{
                  borderLeft: `3px solid ${COLOR.green}`,
                  background: "rgba(255,255,255,0.03)",
                  padding: "8px 12px",
                  marginTop: 8,
                  fontSize: 13,
                  lineHeight: 1.6,
                  opacity: 0.85
                }}
              >
                <Faint style={{ display: "block", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>
                  your work so far — kept
                </Faint>
                <MarkdownMath value={redo.learnerWorkPrefix} />
              </div>
              {/* Cold-retry status for the bound episode — the same honesty
                  RepairScreen renders: only a scheduled independent cold retry
                  converts this repair to Demonstrated credit. */}
              {redo.episodeId ? (
                redo.coldItemId ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8, fontSize: 12, color: COLOR.textDim }}>
                    <Pill tone="green">cold retry scheduled</Pill>
                    <span>
                      an unassisted cold retry on a different question is scheduled for a later session
                      (tomorrow or later) — only that converts to Demonstrated credit
                    </span>
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8, fontSize: 12, color: COLOR.textDim }}>
                    <Pill tone="red">not measurable</Pill>
                    <span>
                      {redo.coldUnmeasurableReason === "no_independent_surface"
                        ? "no independent question exists on this topic yet, so no unassisted cold retry can be scheduled — this repair cannot convert to Demonstrated credit until another surface is authored"
                        : redo.coldUnmeasurableReason === "case_unresolvable"
                        ? "the diagnosed cause behind this repair could no longer be resolved, so no unassisted cold retry can be scheduled — this redo counts as primed practice only"
                        : "no unassisted cold retry could be scheduled for this repair, so it cannot convert to Demonstrated credit"}
                    </span>
                  </div>
                )
              ) : null}
            </div>
          ) : null}
          {workbenchOffered && !stepsMode ? (
            // RW2a (D9): a remembered choice, beside the answer box, never instead of it.
            <div style={{ display: "flex", gap: 12, alignItems: "baseline", marginTop: 6, flexWrap: "wrap" }}>
              <button
                type="button"
                className="queue-row"
                style={{ padding: "0 7px" }}
                onClick={() => {
                  rememberWorkInSteps(true);
                  void openWorkbench();
                }}
              >
                Work in steps
              </button>
              {wbOpenEntry ? (
                <button type="button" style={quietLink} onClick={() => void resumeWorkbench(wbOpenEntry)}>
                  {wbOpenEntry.status === "abandoned" ? "reopen your steps" : "resume your steps"}
                </button>
              ) : null}
            </div>
          ) : null}
          {stepsMode && wbSession ? (
            <div data-workbench-pane="" data-layout="full" style={{ marginTop: 10 }}>
              {item.hints.slice(0, hintsUsed).map((hint, index) => (
                // The hints shown before working in steps stay in view (they count).
                <div className="hint-banner" key={hint}>
                  {simple ? <Pill tone="amber">hint</Pill> : <Pill tone="amber">hint {index + 1}/{item.hints.length}</Pill>} {hint}
                </div>
              ))}
              <Workbench
                key={wbSession.sessionId}
                initial={wbSession}
                layout="full"
                hideProblem
                autoFocus
                practiceSessionId={session.sessionId}
                // This screen's serve, always named as one pair (review F15).
                schedulerCandidateId={schedulerCandidateId ?? null}
                planPresentationId={planPresentationId ?? null}
                onLeave={(closing) => {
                  backToAnswerBox(closing);
                  refreshWbItemSessions();
                }}
                onAbandoned={(closing) => {
                  backToAnswerBox(closing);
                  refreshWbItemSessions();
                }}
                onAnswerBox={(closing) => {
                  rememberWorkInSteps(false);
                  backToAnswerBox(closing);
                  refreshWbItemSessions();
                }}
                onSubmitted={(result) => {
                  // Owner capture 2026-10-25 (B3, B4): the steps answered the
                  // item, so the answer box's draft (its retry key, its hints,
                  // its offer binding) is superseded: never saved again on
                  // unmount nor restored when the item is served again (the
                  // sidecar's submit cleared its checkpoint).
                  suppressDraftFlush.current = true;
                  onCheckpointCleared({ practiceItemId: item.id, submissionId: submissionId.current });
                  onFeedback(result.attempt.attemptId);
                }}
                onAsk={() => openAsk()}
                // Reader CA2 (§7.6): Ask about the focused step, inline under
                // it; a whole-problem question at the foot of the steps.
                {...(panelOn ? {
                  askSignal: stepAskSignal,
                  askRecordLine: askRecord.length ? helpRecordLine({ hints: 0, book: false, earlier: false, questions: askRecord })
                    .replace(/^help used: /, "") : undefined,
                  renderAsk: ({ stepNumber, stepsCount, onClose, onTakeWorked }: { stepNumber: number | null; stepsCount: number; onClose: () => void; onTakeWorked?: (level: 4 | 5) => void }) => (
                    <AskOverlay
                      variant="inline"
                      target={practiceAskTarget({
                        workbenchSessionId: wbSession.sessionId,
                        ...(stepNumber !== null ? { aboutStep: stepNumber } : {}),
                        stepsCount
                      })}
                      onClose={onClose}
                      onToast={onError}
                      onAnswered={onAskAnswered}
                      onTakeWorked={onTakeWorked}
                    />
                  )
                } : {})}
                onWorkChange={onStepsWork}
                onError={onError}
              />
            </div>
          ) : (<>
          <div className="answer-editor-slot" ref={editorSlotRef}>
            <MathLiveEditor
              value={answer}
              onChange={setAnswer}
              // Phase 4: grading yourself against a full answer locks the
              // answer first, so seeing the answer cannot change it; the lock
              // is the frozen trace's, so it outlives a remount (F1).
              disabled={submitting || disclosed !== null || (simple && fallbackRequired && selfGradeVisible)}
              placeholder={
                stuck
                  ? STUCK_PROMPT_TEXT
                  : redo
                    ? "continue from your kept work — rewrite only the failed part"
                    : simple
                      ? "Write what you can — $math$ works."
                      : "type your answer — $math$ renders as you type"
              }
              maxHeight={editorMaxHeight}
              ariaLabel={redo ? "redo the failed part" : "answer"}
            />
          </div>
          <div ref={belowRef}>
            {simple && disclosed && !selfGradeVisible ? (
              // A resumed draft whose full answer was already shown (F1).
              <div style={{ ...quietLine, marginTop: 6 }} data-testid="frozen-answer-note">
                You've seen a full answer, so your answer stays as you wrote it.
              </div>
            ) : null}
            {stuck ? (
              <div className="hint-banner" role="status" aria-label="stuck prompt" style={{ borderColor: COLOR.amber }}>
                <Pill tone="amber">I'm stuck</Pill> {STUCK_PROMPT_TEXT}.{" "}
                <Faint>
                  {probeActive
                    ? "An empty answer is fine."
                    : "An empty answer is fine: Submit takes you to the feedback."}
                </Faint>{" "}
                <button
                  type="button"
                  className="queue-row"
                  style={{ padding: "0 7px", opacity: 0.7 }}
                  onClick={() => setStuck(false)}
                  disabled={submitting}
                >
                  never mind
                </button>
              </div>
            ) : null}
            {simple ? null : (
              <div className="queue-meta">{answer.length} chars · {answer.split(/\s+/).filter(Boolean).length} words</div>
            )}
            {/* §4.6 calibration duel — predicting the correctness of the answer
                they just composed (not the prompt). Shown only once the draft is
                non-empty; a 1–5 tap that is stored as-is (never mapped to a
                probability in the UI). Locked once Submit is pressed (pre-reveal),
                always skippable, never gates submission, absence is unscored — no
                nagging. Selection is marked by the focused class + a caret, not by
                color alone. */}
            {answer.trim() ? (
              <div
                role="group"
                aria-label="How likely is this answer to be correct? (optional, 1 unlikely to 5 certain)"
                style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11 }}
              >
                <Faint>How likely is this answer to be correct? (optional)</Faint>
                {[1, 2, 3, 4, 5].map((level) => {
                  const on = answerConfidence === level;
                  const locked = submitting || selfGradeVisible;
                  return (
                    <button
                      key={level}
                      type="button"
                      // Phase 4: small inline buttons (the queue-row grid
                      // stretched each one across the card).
                      className={simple ? (on ? "plain-action primary" : "plain-action") : on ? "queue-row focused" : "queue-row"}
                      style={simple
                        ? { padding: "1px 8px", fontSize: 11, fontFamily: FONT_MONO, opacity: on ? 1 : 0.7 }
                        : { padding: "0 7px", fontFamily: FONT_MONO, opacity: on ? 1 : 0.55 }}
                      onClick={() => setAnswerConfidence(on ? null : level)}
                      disabled={locked}
                      aria-pressed={on}
                      aria-label={`answer confidence ${level} of 5`}
                    >
                      {on ? "▸" : ""}{level}
                    </button>
                  );
                })}
                {answerConfidence != null && !submitting && !selfGradeVisible ? (
                  <button
                    type="button"
                    className={simple ? "plain-action" : "queue-row"}
                    style={{ padding: "0 7px", opacity: 0.55 }}
                    onClick={() => setAnswerConfidence(null)}
                    aria-label="clear answer confidence"
                  >
                    clear
                  </button>
                ) : null}
              </div>
            ) : null}
            {/* Meas §3.A6 elicitation — one line at a decision point, offered
                only where the answer underdetermines the reasoning, and only
                while the per-session budget lasts. It is a field, not a step:
                it never gates Submit, it is never validated, and a blank one
                is submitted as nothing at all (see withElicitedExplanation). */}
            {item.elicitation?.elicit && item.elicitation.prompt ? (
              <div style={{ marginTop: 10 }}>
                <label
                  htmlFor="elicitation-line"
                  style={{ display: "block", fontSize: 11, marginBottom: 4, color: COLOR.textDim }}
                >
                  {item.elicitation.prompt}{" "}
                  <Faint>· skipping this costs nothing</Faint>
                </label>
                <input
                  id="elicitation-line"
                  type="text"
                  className="text-input"
                  value={whyLine}
                  onChange={(event) => setWhyLine(event.target.value)}
                  // Frozen with the answer before a full answer is shown (F1).
                  disabled={submitting || disclosed !== null || (simple && fallbackRequired && selfGradeVisible)}
                  placeholder="one line — or leave it blank"
                  style={{ width: "100%", fontSize: 12 }}
                />
              </div>
            ) : null}
            {item.hints.slice(0, hintsUsed - adaptiveHints.clientRevealCount).map((hint, index) => (
              <div className="hint-banner" key={hint}>
                {simple ? <Pill tone="amber">hint</Pill> : <Pill tone="amber">hint {index + 1}/{item.hints.length}</Pill>} {hint}
              </div>
            ))}
            {intentCheck?.helpHeader && checkHelpOpen && hintsUsed === 0 && adaptiveHints.entries.length === 0 ? (
              // DL2 (D42): the help ladder's header states the consequence;
              // nothing is shown until a rung is taken.
              <div className="hint-banner" data-testid="intent-check-help" style={{ display: "grid", gap: 6 }}>
                <div>{intentCheck.helpHeader}</div>
                <div>
                  <QuietAction onClick={revealHint} disabled={submitting || adaptiveHints.pending}>
                    Take a hint
                  </QuietAction>
                </div>
              </div>
            ) : null}
            {adaptive ? <HintPanel hints={adaptiveHints} answer={answer} helpStyle={helpStyle} /> : null}
            {panelOn && !isTeachBack && !probeActive ? (
              // Reader CA2 (§7.5, K8): one help record for the attempt, in
              // order, each with its cost; Submit counts the same things.
              <div data-testid="help-record" style={{ ...quietLine, marginTop: 8 }}>
                {helpRecordLine({
                  hints: adaptive ? adaptiveHints.entries.length : hintsUsed,
                  entries: adaptive
                    ? adaptiveHints.entries.map((entry) => ({ assistId: entry.result.assistId ?? null, level: entry.result.level ?? null }))
                    : undefined,
                  book: bookCarried,
                  earlier: earlierCounted,
                  questions: askRecord,
                  server: serverRecord
                })}
              </div>
            ) : null}
            {hintsUsed > item.hints.length ? (
              // Hints seen in steps that the item no longer shows still count (final F2).
              <div className="hint-banner" data-testid="hints-carried">
                <Pill tone="amber">hint</Pill> {hintsUsed - item.hints.length} hint{hintsUsed - item.hints.length === 1 ? "" : "s"} you saw earlier on this problem {hintsUsed - item.hints.length === 1 ? "counts" : "count"}
              </div>
            ) : null}
            {bookCarried ? (
              <div className="hint-banner" data-testid="book-carried">
                <Pill tone="amber">book</Pill> the book you had open while working in steps counts as one hint
              </div>
            ) : pageSeen ? (
              <div className="hint-banner" data-testid="page-counted">
                <Pill tone="amber">page</Pill> {AS_PRINTED_COPY.pageCounted}
              </div>
            ) : null}
            {assistLookupFailed ? (
              <div style={{ ...quietLine, marginTop: 6 }} data-testid="assist-lookup-failed">
                Couldn't check this problem's earlier steps. Any help they counted still counts when you submit.{" "}
                <button type="button" style={quietLink} onClick={refreshWbItemSessions}>check again</button>
              </div>
            ) : null}
            {submitting ? <div className="grading-panel">{simple ? "Reading your answer…" : "grading attempt..."}</div> : null}
            {fallbackRequired && selfGradeVisible && simple ? (
              <PlainSelfGrade
                item={item}
                answer={disclosed ? disclosed.answerMd : redo ? composeRedoAnswer(redo.learnerWorkPrefix, answer) : answer}
                // A short check withholds the answer until it ends (its
                // contract's answerRevealDisabled): grade without it there.
                // Elsewhere it shows only once the trace is frozen (F1).
                showFullAnswer={!probeActive && disclosed !== null && !disclosureFailed}
                exposureKey={submissionId.current}
                recordDisplay={
                  disclosed
                    ? (displayId) =>
                        api.recordSelfGradeDisclosure({
                          sessionId: session.sessionId,
                          practiceItemId: item.id,
                          submissionId: submissionId.current,
                          answerMd: disclosed.answerMd,
                          explanationMd: disclosed.explanationMd,
                          displayId
                        })
                    : undefined
                }
                submitting={submitting}
                partlyOpen={partlyOpen}
                partsGot={partsGot}
                onGotIt={() => void submit(gradeFromParts(item, selfGrade, () => true))}
                onMissed={() => void submit(gradeFromParts(item, selfGrade, () => false))}
                onPartly={() => setPartlyOpen(true)}
                onTogglePart={(criterionId) => setPartsGot((current) => ({ ...current, [criterionId]: !current[criterionId] }))}
                onDonePartly={() => void submit(gradeFromParts(item, selfGrade, (criterionId) => Boolean(partsGot[criterionId])))}
                detailsOpen={selfGradeDetailsOpen}
                onToggleDetails={() => setSelfGradeDetailsOpen((open) => !open)}
                details={
                  <SelfGradePanel
                    item={item}
                    value={selfGrade}
                    setValue={setSelfGrade}
                    scorePreview={scorePreview}
                    fieldErrors={fieldErrors}
                    plain
                  />
                }
              />
            ) : fallbackRequired && selfGradeVisible ? (
              <SelfGradePanel
                item={item}
                value={selfGrade}
                setValue={setSelfGrade}
                scorePreview={scorePreview}
                fieldErrors={fieldErrors}
              />
            ) : null}
            {simple ? (
              // §7.4: Hint, I'm stuck, Ask and Skip are buttons (they keep
              // their keys). A short check offers neither hints nor Ask; a
              // check on your own offers no hint.
              <div className="form-row" style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                {fallbackRequired && selfGradeVisible && !selfGradeDetailsOpen ? null : (
                  <PrimaryAction hotkey="^↵" onClick={() => void submit()} disabled={submitting || assistPending}>Submit</PrimaryAction>
                )}
                {ratingTap && !isTeachBack ? (
                  <DifficultyRatingTap sessionId={session.sessionId} value={difficultyRating}
                                       onChange={setDifficultyRating} locked={submitting || selfGradeVisible} />
                ) : null}
                {!probeActive && (!onYourOwnCheck || coldTakeStep) && (adaptive || hintsUsed < item.hints.length) && !selfGradeVisible ? (
                  <QuietAction onClick={revealHint} disabled={submitting || adaptiveHints.pending}>
                    {hintsUsed > 0 || adaptiveHints.entries.length > 0 ? "Hint again" : "Hint"}
                  </QuietAction>
                ) : null}
                {stuckPrompt && !stuck && !selfGradeVisible ? (
                  <QuietAction onClick={pressStuck} disabled={submitting}>I'm stuck</QuietAction>
                ) : null}
                {!probeActive && !selfGradeVisible ? (
                  <QuietAction onClick={() => openAsk()} disabled={submitting}>Ask</QuietAction>
                ) : null}
                {!selfGradeVisible ? (
                  <QuietAction onClick={() => void skip()} disabled={submitting}>Skip</QuietAction>
                ) : null}
                <span style={{ flex: 1 }} />
                <DetailsToggle open={cardDetailsOpen} onToggle={() => setCardDetailsOpen((open) => !open)} />
              </div>
            ) : (
            <div className="form-row" style={{ marginTop: 16 }}>
              <button className="queue-row focused" type="button" onClick={() => void submit()} disabled={submitting || assistPending}>
                <span className="queue-hotkey">^↵</span>
                <span className="queue-title">Submit</span>
                <span className="queue-score">
                  {selfGradeVisible ? `${scorePreview}/${item.rubric?.maxPoints ?? 4}` : ""}
                </span>
              </button>
              {stuckPrompt && !stuck ? (
                <button className="queue-row" type="button" onClick={pressStuck} disabled={submitting}>
                  <span className="queue-hotkey">^d</span>
                  <span className="queue-title">I'm stuck</span>
                </button>
              ) : null}
              {ratingTap && !isTeachBack ? (
                <DifficultyRatingTap sessionId={session.sessionId} value={difficultyRating}
                                     onChange={setDifficultyRating} locked={submitting || selfGradeVisible} />
              ) : null}
            </div>
            )}
            {simple && cardDetailsOpen ? (
              // The card's receipts (§4.3): the question's id (opens the
              // inspector, which keeps an unanswered question's answer to
              // itself), the mode, the grader, the estimate, the counts and
              // where the question came from.
              <div style={{ ...quietLine, marginTop: 10, display: "grid", gap: 3 }} data-testid="practice-details">
                <div>
                  question <EntityLink id={item.id} onInspect={onInspect} /> · {item.practiceMode}
                  {item.subject ? ` · ${item.subject}` : ""}
                </div>
                <div>{fallbackRequired ? "graded by you" : "graded by AI"}</div>
                {item.mastery != null ? (
                  <div>likely to recall now: {item.mastery.mean.toFixed(2)} ±{Math.sqrt(item.mastery.variance).toFixed(2)}</div>
                ) : null}
                <div>{answer.length} chars · {answer.split(/\s+/).filter(Boolean).length} words</div>
                {intentCheck?.locatorsHidden ? null : item.sourceRefs.map((ref, index) => (
                  <div key={`${ref.refId}:${index}`}>
                    from {ref.displayName} {ref.locator ?? ref.path ?? ref.refType}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          </>)}
          </>
          )}
        </Card>
      </div>
      </DockedAsk>
      {originalPage && item ? (
        // Reader CA1: the whole page, the problem's blocks outlined; the view
        // records its exposure (get_span_view), and it counted as the book above.
        <OpenInSource
          extractionId={originalPage.extractionId}
          spanId={originalPage.spanId}
          outlineSpanIds={originalPage.outlineSpanIds}
          context="provenance"
          entityType="practice_item"
          entityId={item.id}
          onClose={() => setOriginalPage(null)}
        />
      ) : null}
      <KeyBar keys={simple && !isTeachBack ? [
        { key: "^enter", label: "submit" },
        ...(probeActive || (onYourOwnCheck && !coldTakeStep) || (item.hints.length === 0 && !adaptive) ? []
          : [adaptive && !stepsMode ? { key: "^h", label: "hint", onClick: revealHint } : { key: "^h", label: "hint" }]),
        { key: "^d", label: stuckPrompt ? "I'm stuck" : "don't know" },
        { key: "^s", label: "skip" },
        // Reader CA2 (§7.6): in steps the key asks about the focused step.
        ...(probeActive ? [] : [{ key: "?", label: panelOn && stepsMode ? "ask about this step" : "ask" }]),
        { key: "esc", label: "back" }
      ] : isTeachBack ? [
        { key: "^enter", label: "send" },
        { key: "^s", label: "skip" },
        { key: "esc", label: "today" }
      ] : probeActive ? [
        { key: "^enter", label: "submit" },
        { key: "^d", label: stuckPrompt ? "I'm stuck" : "don't know" },
        { key: "^s", label: "skip" },
        { key: "esc", label: "today" }
      ] : [
        { key: "^enter", label: "submit" },
        adaptive && !stepsMode ? { key: "^h", label: "hint", onClick: revealHint } : { key: "^h", label: "hint" },
        { key: "^d", label: stuckPrompt ? "I'm stuck" : "don't know" },
        { key: "^s", label: "skip" },
        { key: "?", label: "ask tutor" },
        { key: "esc", label: "today" }
      ]} />
    </div>
  );
}

// ── Teach-back conversation ──────────────────────────────────────────────────
// The learner teaches; the AI plays a curious naive student that never
// confirms, corrects, or reveals. The transcript replaces the answer box and
// the whole conversation is graded as one attempt when the question budget is
// exhausted (or the learner finishes early). The sidecar owns the state via
// the session checkpoint; `restoredState` rehydrates it after a restart.
function TeachBackConversation({
  session,
  item,
  schedulerCandidateId,
  restoredState,
  onFeedback,
  onCheckpointCleared,
  markSubmitted
}: {
  session: SessionSnapshot;
  item: PracticeItemDetail;
  // The queue offer the item was opened from; the sidecar links the graded
  // attempt to it, so both conversation calls carry it.
  schedulerCandidateId: string | null;
  restoredState: TeachBackStateDto | null;
  onFeedback: (attemptId: string) => void;
  onCheckpointCleared: () => void;
  markSubmitted: () => void;
}) {
  const [turns, setTurns] = useState<TeachBackTurnDto[]>(restoredState?.turns ?? []);
  const [asked, setAsked] = useState(restoredState?.askedCount ?? 0);
  const [budget, setBudget] = useState<number | null>(restoredState ? restoredState.planned.length : null);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  // Guards the mount-time start against a double mount (same idiom as
  // startupStartedRef in App.tsx); the retry button bypasses it on purpose.
  const startedRef = useRef(false);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  const lastRole = turns.length > 0 ? turns[turns.length - 1].role : null;
  // Resume gap: the answer was checkpointed but the next question was never
  // generated — "continue" works without new text, and anything typed is
  // appended server-side to the pending learner turn.
  const needsText = turns.length === 0 || lastRole === "ai";

  const start = useCallback(() => {
    setInlineError(null);
    setStartFailed(false);
    api
      .startTeachBack({ sessionId: session.sessionId, practiceItemId: item.id, schedulerCandidateId })
      .then((result) => {
        // start is idempotent server-side and returns the authoritative
        // conversation state (the in-progress one when checkpointed, empty
        // otherwise). The locally restored snapshot can be stale — App only
        // reads the checkpoint at startup — so the server's copy always wins.
        setBudget(result.budget);
        setTurns(result.state.turns);
        setAsked(result.state.askedCount);
      })
      .catch((error) => {
        setStartFailed(true);
        setInlineError(errorMessage(error, "Could not start the teach-back conversation."));
      });
  }, [session.sessionId, item.id, schedulerCandidateId]);

  useEffect(() => {
    // Always sync with the server on mount; the restored snapshot (seeded into
    // state above) only bridges the gap while the call is in flight or if it
    // fails.
    if (startedRef.current) return;
    startedRef.current = true;
    start();
  }, [start]);

  useEffect(() => {
    const node = transcriptRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [turns.length, pending]);

  async function send(finish = false) {
    if (pending || startFailed) return;
    const text = input.trim();
    if (needsText && !text && !finish) return;
    setPending(true);
    setFinishing(finish);
    setInlineError(null);
    try {
      const result = await api.submitTeachBackTurn({
        sessionId: session.sessionId,
        practiceItemId: item.id,
        schedulerCandidateId,
        answerMd: text,
        finish
      });
      if (result.done) {
        markSubmitted();
        onCheckpointCleared();
        onFeedback(result.attemptId);
      } else {
        setTurns(result.state.turns);
        setAsked(result.asked);
        setBudget(result.budget);
        setInput("");
      }
    } catch (error) {
      setInlineError(errorMessage(error, "Could not send this teach-back turn."));
    } finally {
      setPending(false);
      setFinishing(false);
    }
  }

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (screenLeavesKey(event, { ownChords: true })) return;
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        void send();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const submitLabel =
    turns.length === 0 ? "Start teaching" : lastRole === "learner" ? "Continue" : "Send answer";
  const questionsAnswered = asked > 0 && lastRole === "learner";

  return (
    <div style={{ marginTop: 12 }}>
      <div className="queue-meta" style={{ alignItems: "center", gap: 8 }}>
        <Pill tone="amber">teach-back</Pill>
        {budget !== null ? (
          <Pill>{asked > 0 ? `question ${Math.min(asked, budget)} of ${budget}` : `${budget} follow-up question${budget === 1 ? "" : "s"} planned`}</Pill>
        ) : null}
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          the AI plays a student — it will not confirm or correct
        </span>
      </div>
      {item.teachBackSource?.questConnection === "connected" &&
      item.teachBackSource.questSentence ? (
        <div
          style={{
            marginTop: 9,
            borderLeft: `3px solid ${COLOR.cyan}`,
            background: COLOR.bgElev,
            color: COLOR.textDim,
            fontSize: 12,
            lineHeight: 1.5,
            padding: "8px 11px"
          }}
        >
          This transfer question connects to:{" "}
          <span style={{ color: COLOR.text }}>
            {item.teachBackSource.questSentence}
          </span>
        </div>
      ) : null}

      {/* transcript */}
      <div
        ref={transcriptRef}
        style={{ maxHeight: "44vh", overflowY: "auto", margin: "10px 0", display: "flex", flexDirection: "column", gap: 10 }}
      >
        {turns.map((turn, index) => (
          <div
            key={`${index}-${turn.role}`}
            style={
              turn.role === "learner"
                ? { alignSelf: "flex-end", maxWidth: "85%", border: "1px solid #7a5a2a", borderLeft: "3px solid #e3a063", background: "#1c1710", padding: "8px 12px" }
                : { alignSelf: "flex-start", maxWidth: "85%", border: "1px solid #2a2a2a", borderLeft: "3px solid #3a3a3a", background: "#141414", padding: "8px 12px" }
            }
          >
            <div style={{ fontSize: 10, opacity: 0.6, marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>
              {turn.role === "learner" ? (index === 0 ? "you · opening explanation" : "you") : "student"}
            </div>
            <div className="markdown" style={{ fontSize: 13, lineHeight: 1.6 }}>
              <MarkdownMath value={turn.contentMd} />
            </div>
          </div>
        ))}
        {pending ? (
          <div style={{ alignSelf: "flex-start", opacity: 0.6, fontSize: 12 }}>
            {finishing || (budget !== null && asked >= budget && lastRole === "ai") ? "grading the conversation …" : "the student is thinking …"}
          </div>
        ) : null}
      </div>

      {inlineError ? (
        <div className="hint-banner" style={{ borderColor: "#e07e7e" }}>
          <Pill tone="red">error</Pill> {inlineError}
          {startFailed ? (
            <button type="button" className="queue-row" style={{ marginLeft: 10 }} onClick={start}>
              retry
            </button>
          ) : null}
        </div>
      ) : null}

      {/* input */}
      {!startFailed ? (
        <>
          <MathLiveEditor
            value={input}
            onChange={setInput}
            disabled={pending}
            placeholder={
              turns.length === 0
                ? "teach the concept in your own words — $math$ renders as you type"
                : lastRole === "learner"
                  ? "add to your previous answer (optional), then continue"
                  : "answer the student's question"
            }
            maxHeight={220}
            ariaLabel="teach-back answer"
          />
          <div className="queue-meta">{input.length} chars · {input.split(/\s+/).filter(Boolean).length} words</div>
          <div className="form-row" style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12 }}>
            <button className="queue-row focused" type="button" onClick={() => void send()} disabled={pending}>
              <span className="queue-hotkey">^↵</span>
              <span className="queue-title">{submitLabel}</span>
              <span className="queue-score">{budget !== null ? `${asked}/${budget}` : ""}</span>
            </button>
            {questionsAnswered || turns.length > 0 ? (
              <button
                type="button"
                className="queue-row"
                onClick={() => void send(true)}
                disabled={pending || turns.length === 0}
                title="stop here and grade the conversation so far"
              >
                finish &amp; grade now
              </button>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}

/** Got it / Missed set every criterion to full or none; Partly the ones
 *  the learner ticked. Fatal errors and attributions are left to details. */
function gradeFromParts(
  item: PracticeItemDetail,
  base: SelfGradeInputDto,
  got: (criterionId: string) => boolean
): SelfGradeInputDto {
  return {
    ...base,
    criterionPoints: Object.fromEntries(
      (item.rubric?.criteria ?? []).map((criterion) => [criterion.id, got(criterion.id) ? criterion.points : 0])
    ),
    fatalErrors: [],
    errorAttributions: []
  };
}

// UX Phase 4 (§7.4): with no AI, the learner grades against a full answer.
// The answer is locked first; three choices, Got it · Partly · Missed, and
// "Partly" asks which parts. The per-criterion numbers, fatal errors and
// attribution chips are details (the classic panel, with "out of N").
function PlainSelfGrade({
  item,
  answer,
  showFullAnswer,
  exposureKey,
  recordDisplay,
  submitting,
  partlyOpen,
  partsGot,
  onGotIt,
  onMissed,
  onPartly,
  onTogglePart,
  onDonePartly,
  detailsOpen,
  onToggleDetails,
  details
}: {
  item: PracticeItemDetail;
  answer: string;
  showFullAnswer: boolean;
  /** The draft's retry key: the key's display rows belong to it. */
  exposureKey: string;
  /** One display row for the key on this pending draft (round 3 F1). */
  recordDisplay?: RecordDisplay;
  submitting: boolean;
  partlyOpen: boolean;
  partsGot: Record<string, boolean>;
  onGotIt: () => void;
  onMissed: () => void;
  onPartly: () => void;
  onTogglePart: (criterionId: string) => void;
  onDonePartly: () => void;
  detailsOpen: boolean;
  onToggleDetails: () => void;
  details: ReactNode;
}) {
  const criteria = item.rubric?.criteria ?? [];
  const fullAnswer = expectedAnswerText(item.expectedAnswer).trim();
  // The key is an exposure from the moment it shows (round 3 F1): on screen
  // only while a committed row covers it, written while the draft is pending
  // so every other production is judged against it; this draft's own
  // frozen trace is exempt.
  const exposure = useAnswerExposure(exposureKey, showFullAnswer && Boolean(fullAnswer), recordDisplay);
  return (
    <div style={{ marginTop: 14 }} data-testid="plain-self-grade">
      <div style={{ fontSize: 13, color: COLOR.text }}>Grade this one yourself</div>
      <div style={quietLine}>AI grading isn't available right now.</div>
      {showFullAnswer && fullAnswer ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 10, marginTop: 10 }}>
          <VoicePanel mark="›" title="You wrote">
            {answer.trim() ? <MarkdownMath value={answer} /> : <span style={{ color: COLOR.textDim }}>(nothing written)</span>}
          </VoicePanel>
          <VoicePanel mark="◇" title="A full answer">
            {exposure.shown ? (
              <MarkdownMath value={fullAnswer} />
            ) : (
              <AnswerWaiting status={exposure.status} onShow={exposure.show} />
            )}
          </VoicePanel>
        </div>
      ) : null}
      {criteria.length > 0 ? (
        <>
          <div style={{ ...quietLine, marginTop: 10 }}>How did you do?</div>
          <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
            <QuietAction onClick={onGotIt} disabled={submitting}>Got it</QuietAction>
            <QuietAction onClick={onPartly} disabled={submitting}>Partly</QuietAction>
            <QuietAction onClick={onMissed} disabled={submitting}>Missed</QuietAction>
          </div>
          {partlyOpen ? (
            <div style={{ marginTop: 10 }}>
              <div style={quietLine}>Which parts did you get?</div>
              {criteria.map((criterion) => (
                <label key={criterion.id} style={{ display: "flex", gap: 8, alignItems: "baseline", fontSize: 13, marginTop: 4 }}>
                  <input
                    type="checkbox"
                    checked={Boolean(partsGot[criterion.id])}
                    onChange={() => onTogglePart(criterion.id)}
                    disabled={submitting}
                  />
                  <span>{criterion.description}</span>
                </label>
              ))}
              <div style={{ marginTop: 8 }}>
                <PrimaryAction onClick={onDonePartly} disabled={submitting}>Done</PrimaryAction>
              </div>
            </div>
          ) : null}
        </>
      ) : null}
      <div style={{ marginTop: 8 }}>
        <DetailsToggle open={detailsOpen || criteria.length === 0} onToggle={onToggleDetails} label="grade it in detail" />
      </div>
      {detailsOpen || criteria.length === 0 ? details : null}
    </div>
  );
}

function SelfGradePanel({
  item,
  value,
  setValue,
  scorePreview,
  fieldErrors,
  plain = false
}: {
  item: PracticeItemDetail;
  value: SelfGradeInputDto;
  setValue: (next: SelfGradeInputDto) => void;
  scorePreview: number;
  fieldErrors: Record<string, string>;
  /** Phase 4's details: no outage banner (the plain grade says it), and each
   *  criterion says what it is out of (usability round 1, m12). */
  plain?: boolean;
}) {
  return (
    <div className="self-grade-panel">
      {plain ? (
        <div>
          Your grade so far: {scorePreview} out of {item.rubric?.maxPoints ?? 4}
        </div>
      ) : (
      <div>
        <b>AI grading is unavailable</b> · grade your answer to continue · live score{" "}
        {scorePreview}/{item.rubric?.maxPoints ?? 4}
      </div>
      )}
      <div className="self-grade-grid">
        {item.rubric?.criteria.map((criterion) => {
          const awarded = value.criterionPoints[criterion.id] ?? 0;
          const docked = awarded < criterion.points;
          return (
            <div className="criterion-block" key={criterion.id}>
              <label className="criterion-row">
                <span>
                  {criterion.description}
                  {plain ? <span style={{ color: COLOR.textDim }}> (out of {criterion.points})</span> : null}
                </span>
                <input
                  className="number-input"
                  type="number"
                  min={0}
                  max={criterion.points}
                  step={0.25}
                  value={awarded}
                  onChange={(event) => {
                    const points = Number(event.target.value);
                    const stillDocked = points < criterion.points;
                    setValue({
                      ...value,
                      criterionPoints: { ...value.criterionPoints, [criterion.id]: points },
                      // Restoring a criterion to full credit retracts its attributions.
                      errorAttributions: stillDocked
                        ? value.errorAttributions ?? []
                        : (value.errorAttributions ?? []).filter((a) => a.criterionId !== criterion.id)
                    });
                  }}
                />
              </label>
              {fieldErrors[criterion.id] ? <span className="field-error">{fieldErrors[criterion.id]}</span> : null}
              {docked ? (
                <CriterionErrorPicker criterion={criterion} candidates={item.candidateErrorTypes} value={value} setValue={setValue} />
              ) : null}
            </div>
          );
        })}
        {item.rubric?.fatalErrors.length ? (
          <label>
            fatal errors
            <select
              className="text-input"
              multiple
              value={value.fatalErrors ?? []}
              onChange={(event) => setValue({
                ...value,
                fatalErrors: Array.from(event.currentTarget.selectedOptions).map((option) => option.value)
              })}
            >
              {item.rubric.fatalErrors.map((fatal) => (
                <option key={fatal.id} value={fatal.id}>{fatal.id} caps at {fatal.maxGrade}</option>
              ))}
            </select>
          </label>
        ) : null}
        <label>
          confidence
          <TermSelect
            value={String(value.confidence)}
            options={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: String(n) }))}
            onChange={(v) => setValue({ ...value, confidence: Number(v) })}
            width={110}
          />
          {fieldErrors.confidence ? <span className="field-error">{fieldErrors.confidence}</span> : null}
        </label>
        <label>
          notes
          <textarea
            className="self-grade-notes"
            value={value.notes ?? ""}
            onChange={(event) => setValue({ ...value, notes: event.target.value })}
          />
        </label>
      </div>
    </div>
  );
}

// Spawned beneath a rubric criterion the learner scored below full credit: a
// multi-select of error types they can attribute to that specific criterion.
// Concept-relevant types lead; the rest follow after a divider. Selections are
// optional and mirror Codex error attributions once resolved server-side.
function CriterionErrorPicker({
  criterion,
  candidates,
  value,
  setValue
}: {
  criterion: RubricCriterionDto;
  candidates: CandidateErrorTypeDto[];
  value: SelfGradeInputDto;
  setValue: (next: SelfGradeInputDto) => void;
}) {
  const selected = new Set(
    (value.errorAttributions ?? []).filter((a) => a.criterionId === criterion.id).map((a) => a.errorType)
  );
  const toggle = (errorType: string) => {
    const list = value.errorAttributions ?? [];
    const exists = list.some((a) => a.criterionId === criterion.id && a.errorType === errorType);
    setValue({
      ...value,
      errorAttributions: exists
        ? list.filter((a) => !(a.criterionId === criterion.id && a.errorType === errorType))
        : [...list, { errorType, criterionId: criterion.id }]
    });
  };
  const relevant = candidates.filter((c) => c.relevant);
  const others = candidates.filter((c) => !c.relevant);
  const chip = (c: CandidateErrorTypeDto) => (
    <button
      type="button"
      key={c.id}
      className={[
        "attribution-chip",
        c.relevant ? "relevant" : "",
        selected.has(c.id) ? "on" : "",
        c.isMisconception ? "misconception" : ""
      ].filter(Boolean).join(" ")}
      onClick={() => toggle(c.id)}
      title={c.isMisconception ? "misconception" : undefined}
    >
      {c.isMisconception ? <span className="attribution-chip-mark">◆</span> : null}
      {c.title}
    </button>
  );
  return (
    <div className="attribution-box">
      <div className="attribution-head">
        attribute error(s) <span className="attribution-optional">· optional</span>
      </div>
      {candidates.length === 0 ? (
        <div className="attribution-empty">no error types defined in this vault</div>
      ) : (
        <div className="attribution-chips">
          {relevant.map(chip)}
          {relevant.length > 0 && others.length > 0 ? <span className="attribution-divider">others</span> : null}
          {others.map(chip)}
        </div>
      )}
    </div>
  );
}

// Keep only attributions whose criterion is still below full credit (or that
// aren't tied to a criterion), so a restored score never ships a stale tag.
function prunedAttributions(item: PracticeItemDetail, grade: SelfGradeInputDto): SelfGradeErrorAttributionDto[] {
  const docked = new Set(
    (item.rubric?.criteria ?? [])
      .filter((criterion) => (grade.criterionPoints[criterion.id] ?? 0) < criterion.points)
      .map((criterion) => criterion.id)
  );
  return (grade.errorAttributions ?? []).filter((a) => a.criterionId == null || docked.has(a.criterionId));
}

// These mirror learnloop.attempt_types so the client only ever submits an
// attempt type the item actually permits. An empty allow-list means the
// backend imposes no per-item restriction (every supported type is fine).
const NON_RECORDING_ATTEMPT_TYPES: ReadonlySet<AttemptType> = new Set(["guided_walkthrough", "skip"]);

function defaultAttemptType(allowed: readonly AttemptType[]): AttemptType {
  if (allowed.length === 0) return "independent_attempt";
  if (allowed.includes("independent_attempt")) return "independent_attempt";
  for (const candidate of allowed) {
    if (!NON_RECORDING_ATTEMPT_TYPES.has(candidate)) return candidate;
  }
  return "independent_attempt";
}

// Guided redo (Fix 3): compose the preserved prefix and the learner's rewritten
// portion into one answer. A paragraph break separates them unless one is
// already there — the same end-append junction rule repair_splice enforces
// server-side, so the graded text never runs the redo into the kept sentence.
function composeRedoAnswer(prefix: string, redoText: string): string {
  const suffix = redoText.replace(/^[ \t]+/, "");
  if (!prefix.trim()) return redoText;
  if (/\n[ \t]*\n[ \t]*$/.test(prefix) || /^[ \t]*\n/.test(redoText)) return prefix + redoText;
  return `${prefix}\n\n${suffix}`;
}

// Adaptive hints H0: one telemetry row per authored hint revealed. Fire and
// forget: never awaited, any failure (a sidecar without the RPC included)
// ignored, and nothing rendered depends on it; submit still sends the count.
function recordHintReveal(input: Parameters<typeof api.recordHintReveal>[0]): void {
  try {
    void Promise.resolve(api.recordHintReveal(input)).catch(() => undefined);
  } catch {
    // Telemetry never blocks or alters the reveal.
  }
}

// Prefer hinted_attempt when hints were used and the item allows it; otherwise
// fall back to the item's default recording attempt type.
/** Reader CA2 (§7.5, K8): the attempt's help record in one line, in the
 *  learner's words, each part with its cost ("help used: nothing yet"). */
export function helpRecordLine({ hints, entries, book, earlier, questions, server }: {
  hints: number;
  /** Codex re-review F14: the screen's hint entries (adaptive hints), by
   *  identity and level, so worked help is never also counted as a hint and
   *  an entry the server lists is never counted twice. */
  entries?: ReadonlyArray<{ assistId: string | null; level: number | null }>;
  book: boolean;
  earlier: boolean;
  questions: ReadonlyArray<{ hintEquivalent: boolean; eventId?: string }>;
  /** Codex review F7: the server's record, in order (what Submit folds);
   *  absent until read, then the screen's own items fill only what the
   *  server does not hold (the authored hints it counts, the book). */
  server?: HelpRecordDto | null;
}): string {
  const parts: string[] = [];
  if (!server) {
    // Fix round F14: with no record read (the transcript is unavailable),
    // the screen's entries are still classified by level: L4-L5 is worked
    // help (it primes, never a hint), the rest are hints.
    const worked = (entries ?? []).filter((entry) => (entry.level ?? 0) >= 4).map((entry) => entry.level as number);
    const plain = Math.max(0, hints - worked.length);
    if (plain > 0) parts.push(plain === 1 ? "a hint" : `${plain} hints`);
    for (const level of worked) parts.push(`worked help (L${level}) · practice with help`);
    if (book) parts.push("the book left open (counts as a hint)");
    if (earlier) parts.push("an earlier attempt's help (counts as a hint)");
    for (const question of questions) {
      parts.push(question.hintEquivalent ? "a question (counts as a hint)" : "a clarification (free)");
    }
    return `help used: ${parts.length ? parts.join(" · ") : "nothing yet"}`;
  }
  // The hints the server holds rows for (the hint service's, and authored
  // reveals' telemetry) are listed in order; the client's own count covers
  // the authored hints the server has no row for.
  let clientOnly: number;
  let clientWorked: number[] = [];
  if (entries) {
    // By identity (re-review F14): an entry the server lists is the
    // server's; of the rest, worked help (levels 4-5) primes and is listed
    // as worked help, never as a hint.
    const listedIds = new Set(server.items.map((entry) => entry.assistId).filter((id): id is string => Boolean(id)));
    const unlisted = entries.filter((entry) => !(entry.assistId && listedIds.has(entry.assistId)));
    clientWorked = unlisted.filter((entry) => (entry.level ?? 0) >= 4).map((entry) => entry.level as number);
    clientOnly = unlisted.length - clientWorked.length;
  } else {
    const serverHints = server.items.filter((entry) => entry.kind === "hint" || entry.kind === "check").length;
    clientOnly = Math.max(0, hints - serverHints);
  }
  if (clientOnly > 0) parts.push(clientOnly === 1 ? "a hint" : `${clientOnly} hints`);
  const listed = new Set<string>();
  for (const entry of server.items) {
    if (entry.kind === "question") {
      if (entry.eventId) listed.add(entry.eventId);
      if (!entry.counts) parts.push("a clarification (free)");
      else parts.push(entry.thisAttempt === false ? "a question from before this serve (counts as a hint)" : "a question (counts as a hint)");
    } else if (entry.kind === "hint") {
      parts.push(entry.level ? `a hint (L${entry.level})` : "a hint");
    } else if (entry.kind === "check") {
      parts.push("a check");
    } else if (entry.kind === "worked") {
      parts.push(`worked help${entry.level ? ` (L${entry.level})` : ""} · practice with help`);
    } else if (entry.kind === "earlier") {
      listed.add("earlier");
      parts.push("an earlier attempt's help (counts as a hint)");
    }
  }
  // Answers this visit has that the record has not read back yet.
  for (const question of questions) {
    if (question.eventId && listed.has(question.eventId)) continue;
    parts.push(question.hintEquivalent ? "a question (counts as a hint)" : "a clarification (free)");
  }
  for (const level of clientWorked) parts.push(`worked help (L${level}) · practice with help`);
  if (earlier && !listed.has("earlier")) parts.push("an earlier attempt's help (counts as a hint)");
  if (book) parts.push("the book left open (counts as a hint)");
  return `help used: ${parts.length ? parts.join(" · ") : "nothing yet"}`;
}

function chooseAttemptType(allowed: readonly AttemptType[], hintsUsed: number): AttemptType {
  const allows = (type: AttemptType) => allowed.length === 0 || allowed.includes(type);
  if (hintsUsed > 0 && allows("hinted_attempt")) return "hinted_attempt";
  return defaultAttemptType(allowed);
}

function validateSelfGrade(
  item: PracticeItemDetail,
  value: SelfGradeInputDto,
  required: boolean
): Record<string, string> {
  if (!required) return {};
  const errors: Record<string, string> = {};
  for (const criterion of item.rubric?.criteria ?? []) {
    const points = value.criterionPoints[criterion.id];
    if (!Number.isFinite(points) || points < 0 || points > criterion.points) {
      errors[criterion.id] = `0..${criterion.points}`;
    }
  }
  if (!Number.isInteger(value.confidence) || value.confidence < 1 || value.confidence > 5) {
    errors.confidence = "1..5";
  }
  return errors;
}
