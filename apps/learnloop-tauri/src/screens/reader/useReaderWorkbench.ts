// Reader workbench RW2a in the Reader: the working posture (spec §5.1; UX §3.1,
// §5.1, S1/S2/S6/S7/S13).
//
// The problems worked on this source (open or set aside, never submitted)
// show as ✎ marks beside their passages and as lines in the rail; RW6a's
// recap reads the same list (`workbench.for_source`). "Work through this" on
// a selection opens a session at once with the verbatim selection as the
// stem, while the exercise import binds it in the background; on an imported
// exercise it opens bound. The workbench takes half the window (resizable,
// remembered on this device, at least 480 px), or the whole screen below the
// 1,040 px breakpoint with the book in a sheet. Leave, Submit and Abandon
// collapse back into reading at the problem's passage. "Check me" on a margin
// cue opens here too (D40, UX S7): the shell records the learner pick and
// hands the check over, and it opens in the working posture with the book
// hidden (also on a problem left with the book open), answering the pick's
// own serve, which the problem keeps across a resume. Resuming a problem worked on the
// practice screen moves it here explicitly (review F4).
//
// RW4b ("use this one" on a textbook exercise, spec §7.4): the shell hands the
// exercise over as it hands a check over; once its source is the one open, the
// problem opens at once on the verbatim statement while the import runs (the
// sources service's for a proposal's exercise, the Reader's own for the
// fallback's), book hidden unless the exercise was already seen (the server
// reads that at the pick). When that import has bound the problem to the item
// it wrote and the learner pick of it is still owed (`exercisePick.due`, kept
// on the problem, so a restart or a resume still owes it), the shell is told
// (`onExerciseAdmitted`), so the item becomes a learner pick; the pick's
// hand-off acknowledges it (`admittedSessionId`) only once it succeeded.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  ReaderImportExerciseInput,
  SourceLibraryCard,
  WorkbenchSessionDto,
  WorkbenchSubmitDto,
  WorkbenchSummaryDto,
} from "../../api/dto";
import { errorMessage } from "../../errors";
import {
  SPLIT_STEP,
  clampSplitWidth,
  defaultSplitWidth,
  isNarrow,
  readSplitWidth,
  writeSplitWidth,
} from "../workbench/splitWidth";
import type { ReaderWorkbenchExercise } from "./exerciseCandidates";

/** A margin cue's "check me", picked by the shell (D40): the item and the
 *  serve its answer is to. */
export interface ReaderWorkbenchCheck {
  practiceItemId: string;
  /** The passage the cue sits beside, and the source it is on. */
  spanId: string;
  sourceId: string;
  stemMd: string;
  schedulerCandidateId: string | null;
  planPresentationId: string | null;
  /** RW4b: "practice_this" when the pick is an admitted exercise's (its own
   *  problem resumes with the book as the learner left it); else "check_me". */
  entry?: "check_me" | "practice_this";
  /** RW4b: the exercise problem this pick admits (acknowledged by its open). */
  admitsSessionId?: string;
}

/** RW4b: an exercise's import wrote its item, and the problem is bound to it. */
export interface ReaderExerciseAdmitted {
  practiceItemId: string;
  proposalId: string | null;
  /** The sources service's import (a proposal's exercise); null for the fallback's. */
  importId: string | null;
  sourceId: string;
  /** The source the exercise is in (where back from its feedback returns). */
  card: SourceLibraryCard;
  spanId: string;
  stemMd: string;
  workbenchSessionId: string;
}

export interface ReaderWorkbenchProps {
  /** The app's open practice session, when there is one (the submit uses it). */
  practiceSessionId?: string | null;
  /** RW4b: "use this one" to open once its source is open (the shell picked it). */
  exercise?: ReaderWorkbenchExercise | null;
  /** The exercise's problem opened (the shell forgets it). */
  onExerciseShown?: () => void;
  /** The exercise's import bound the problem and its learner pick is owed:
   *  the shell records the pick. Resolves false when it could not (no
   *  session, a refused pick): nothing was acknowledged, so it is owed still. */
  onExerciseAdmitted?: (admitted: ReaderExerciseAdmitted) => Promise<boolean> | boolean | void;
  /** "Check me" to open in the working posture, book hidden (D40). */
  checkMe?: ReaderWorkbenchCheck | null;
  /** The check opened (the shell forgets it). */
  onCheckMeShown?: () => void;
  /** A submit hands its attempt to the shell, with the way back to its passage. */
  onSubmitted?: (result: WorkbenchSubmitDto, at: { card: SourceLibraryCard; spanId: string }) => void;
  /** Back from feedback: open this attempt's problem read-only (UX S6). */
  initialAttemptId?: string | null;
  /** The read-only problem was shown (the shell forgets the attempt). */
  onInitialAttemptShown?: () => void;
}

export interface ActiveWorkbench {
  session: WorkbenchSessionDto;
  readOnly: boolean;
  /** Opened by the learner just now: step 1 takes the caret. */
  autoFocus: boolean;
  /** The serve a "check me" answers (its candidate and plan presentation). */
  schedulerCandidateId?: string | null;
  planPresentationId?: string | null;
}

export interface ReaderWorkbench {
  enabled: boolean;
  sessions: WorkbenchSummaryDto[];
  active: ActiveWorkbench | null;
  /** The receipt after Abandon: "abandoned · your steps are kept · reopen". */
  abandoned: WorkbenchSessionDto | null;
  width: number;
  narrow: boolean;
  sheetOpen: boolean;
  setSheetOpen: (open: boolean) => void;
  resizeBy: (delta: number) => void;
  setWidth: (width: number) => void;
  openSelection: (input: { stemMd: string; spanIds: string[]; importRequest: ReaderImportExerciseInput }) => Promise<void>;
  openItem: (input: { practiceItemId: string; stemMd: string; spanIds: string[] }) => Promise<void>;
  resume: (sessionId: string) => Promise<void>;
  reopenAbandoned: () => Promise<void>;
  /** The session changed inside the workbench (the book, the binding). */
  update: (session: WorkbenchSessionDto) => void;
  /** Collapse back into reading; returns the passage to return to. */
  close: (session: WorkbenchSessionDto | null, options?: { abandoned?: boolean }) => string | null;
  submitted: (result: WorkbenchSubmitDto) => void;
}

function newKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `k${Date.now()}${Math.random()}`;
}

export function useReaderWorkbench(input: {
  enabled: boolean;
  extractionId: string | null;
  card: SourceLibraryCard | null;
  props?: ReaderWorkbenchProps;
  onError: (message: string) => void;
}): ReaderWorkbench {
  const { enabled, extractionId, card, onError } = input;
  const props = input.props;
  const [sessions, setSessions] = useState<WorkbenchSummaryDto[]>([]);
  const [active, setActive] = useState<ActiveWorkbench | null>(null);
  const [abandoned, setAbandoned] = useState<WorkbenchSessionDto | null>(null);
  const [windowWidth, setWindowWidth] = useState(() => (typeof window === "undefined" ? 1600 : window.innerWidth));
  const [width, setWidthState] = useState(() => clampSplitWidth(readSplitWidth() ?? defaultSplitWidth(windowWidth), windowWidth));
  const [sheetOpen, setSheetOpen] = useState(false);
  const extractionRef = useRef(extractionId);
  extractionRef.current = extractionId;

  const refresh = useCallback(async () => {
    const current = extractionRef.current;
    if (!enabled || !current) return;
    try {
      const result = await api.workbenchForSource({ extractionId: current });
      if (extractionRef.current === current) setSessions(result.sessions);
    } catch {
      // The marks are a convenience: without them the source still reads.
    }
  }, [enabled]);

  useEffect(() => {
    setSessions([]);
    setActive(null);
    setAbandoned(null);
    void refresh();
  }, [extractionId, refresh]);

  // Back from feedback (UX S6): the submitted problem, read-only.
  // It opens once the source it belongs to is open, and only once.
  const initialAttemptId = props?.initialAttemptId ?? null;
  const openedAttemptRef = useRef<string | null>(null);
  useEffect(() => {
    if (!enabled || !initialAttemptId || !extractionId || openedAttemptRef.current === initialAttemptId) return;
    openedAttemptRef.current = initialAttemptId;
    void api.workbenchSessionForAttempt({ attemptId: initialAttemptId })
      .then((result) => {
        const session = result.session;
        if (session && extractionRef.current === extractionId && session.extractionId === extractionId) {
          setActive({ session, readOnly: true, autoFocus: false });
          props?.onInitialAttemptShown?.();
        }
      })
      .catch(() => undefined);
  }, [enabled, initialAttemptId, extractionId]);

  useEffect(() => {
    if (!enabled) return undefined;
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [enabled]);

  const setWidth = useCallback((next: number) => {
    const clamped = clampSplitWidth(next, window.innerWidth);
    setWidthState(clamped);
    writeSplitWidth(clamped);
  }, []);
  const resizeBy = useCallback((delta: number) => {
    setWidthState((current) => {
      const clamped = clampSplitWidth(current + delta, window.innerWidth);
      writeSplitWidth(clamped);
      return clamped;
    });
  }, []);

  // RW4b: a problem whose exercise pick is owed (the server's durable
  // `exercisePick.due`, Codex review F2) is handed to the shell, one hand-off
  // in flight at a time. The server acknowledges it only when the pick's
  // hand-off opens the problem; a hand-off that failed is released, so the
  // next sight of the problem (this visit or after a restart) tries again.
  // The shell's hand-off resolves once the pick is made and served, so the
  // acknowledging open (the "check me" below naming `admitsSessionId`) holds
  // the hand-off until it settles, and releases it when it fails (re-review
  // F2): nothing was acknowledged, and the next pick brings its own serve.
  const admitting = useRef(new Set<string>());
  const onAdmittedRef = useRef(props?.onExerciseAdmitted);
  onAdmittedRef.current = props?.onExerciseAdmitted;
  const cardRef = useRef(card);
  cardRef.current = card;
  const noteAdmission = useCallback((session: WorkbenchSessionDto) => {
    const owed = session.exercisePick;
    const open = cardRef.current;
    if (!owed?.due || !session.practiceItemId || !open || admitting.current.has(session.sessionId)) return;
    // The pick names the book the exercise is in (re-review F6): a late
    // answer for a problem on another book (an import refresh still in flight
    // when the learner moved on), or a moment when the open card and the
    // open extraction disagree, admits nothing. The pick stays owed on the
    // problem until its own book is open again.
    if (!session.extractionId || session.extractionId !== extractionRef.current) return;
    if (!session.sourceId || session.sourceId !== open.sourceId) return;
    const handOff = onAdmittedRef.current;
    if (!handOff) return;
    admitting.current.add(session.sessionId);
    const release = () => admitting.current.delete(session.sessionId);
    Promise.resolve()
      .then(() => handOff({
        practiceItemId: session.practiceItemId as string,
        proposalId: owed.proposalId,
        importId: session.sourceExercise?.importId ?? null,
        sourceId: open.sourceId,
        card: open,
        spanId: session.spanIds[0] ?? "",
        stemMd: session.stemMd,
        workbenchSessionId: session.sessionId,
      }))
      .then((delivered) => {
        if (delivered === false) release();
      })
      .catch(release);
  }, []);

  const begin = useCallback((session: WorkbenchSessionDto, readOnly = false, serve?: { schedulerCandidateId: string | null; planPresentationId: string | null }) => {
    setAbandoned(null);
    setSheetOpen(false);
    setActive({ session, readOnly, autoFocus: !readOnly, ...(serve ?? {}) });
    noteAdmission(session);
  }, [noteAdmission]);

  const openSelection = useCallback(async (request: { stemMd: string; spanIds: string[]; importRequest: ReaderImportExerciseInput }) => {
    if (!enabled || !extractionId) return;
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", stemMd: request.stemMd, extractionId,
        spanIds: request.spanIds, importRequest: request.importRequest, clientIdempotencyKey: newKey(),
      });
      begin(result.session);
    } catch (error) {
      onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [begin, enabled, extractionId, onError]);

  const openItem = useCallback(async (request: { practiceItemId: string; stemMd: string; spanIds: string[] }) => {
    if (!enabled || !extractionId) return;
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", practiceItemId: request.practiceItemId, stemMd: request.stemMd,
        extractionId, spanIds: request.spanIds, clientIdempotencyKey: newKey(),
      });
      begin(result.session);
    } catch (error) {
      onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [begin, enabled, extractionId, onError]);

  const resume = useCallback(async (sessionId: string) => {
    try {
      // One explicit resume: reopened when set aside, and moved into the
      // Reader (its anchors here, the book hidden once steps exist) when it
      // was worked on the practice screen (review F4).
      const result = await api.workbenchOpen({ origin: "reader", entry: "resume", sessionId, extractionId: extractionRef.current });
      begin(result.session);
    } catch (error) {
      onError(errorMessage(error, "Couldn't reopen this problem."));
    }
  }, [begin, onError]);

  // "Check me" (D40): once its source is the one open, the check opens in the
  // working posture with the book hidden, as the pick's own serve.
  const checkMe = props?.checkMe ?? null;
  const openedCheckRef = useRef<ReaderWorkbenchCheck | null>(null);
  useEffect(() => {
    if (!enabled || !checkMe || !extractionId || !card || card.sourceId !== checkMe.sourceId) return;
    if (openedCheckRef.current === checkMe) return;
    openedCheckRef.current = checkMe;
    const wanted = extractionId;
    void api.workbenchOpen({
      origin: "reader", entry: checkMe.entry ?? "check_me", practiceItemId: checkMe.practiceItemId, stemMd: checkMe.stemMd,
      extractionId: wanted, spanIds: [checkMe.spanId], clientIdempotencyKey: newKey(),
      // The pick's serve goes on the problem itself, so leaving and resuming
      // it still submits as that serve (review F13); the server also hides
      // the book on a reused problem, keeping what it counted (F14).
      schedulerCandidateId: checkMe.schedulerCandidateId, planPresentationId: checkMe.planPresentationId,
      // RW4b: the exercise problem this pick admits, acknowledged by the
      // server now that the pick and its serve succeeded.
      ...(checkMe.admitsSessionId ? { admittedSessionId: checkMe.admitsSessionId } : {}),
    })
      .then((result) => {
        props?.onCheckMeShown?.();
        if (extractionRef.current !== wanted) return;
        begin(result.session, false, {
          schedulerCandidateId: checkMe.schedulerCandidateId, planPresentationId: checkMe.planPresentationId,
        });
      })
      .catch((error) => {
        // Not acknowledged: the exercise's pick is owed still, so its
        // hand-off is released for the next sight of the problem (F2).
        if (checkMe.admitsSessionId) admitting.current.delete(checkMe.admitsSessionId);
        props?.onCheckMeShown?.();
        onError(errorMessage(error, "Couldn't open the check."));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, checkMe, extractionId, card?.sourceId]);

  // RW4b: "use this one" (the shell picked it): once its source is open, the
  // problem opens at once on the verbatim statement while its import runs.
  const exercise = props?.exercise ?? null;
  const openedExerciseRef = useRef<ReaderWorkbenchExercise | null>(null);
  useEffect(() => {
    if (!enabled || !exercise || !extractionId || !card || card.sourceId !== exercise.sourceId) return;
    if (openedExerciseRef.current === exercise) return;
    openedExerciseRef.current = exercise;
    const wanted = extractionId;
    void api.workbenchOpen({
      origin: "reader", entry: exercise.entry, stemMd: exercise.stemMd, extractionId: exercise.extractionId,
      spanIds: exercise.spanIds, clientIdempotencyKey: newKey(),
      ...(exercise.sourceExercise
        ? { sourceExercise: exercise.sourceExercise }
        : { importRequest: exercise.importRequest ?? null, ...(exercise.exercisePick ? { exercisePick: exercise.exercisePick } : {}) }),
    })
      .then((result) => {
        props?.onExerciseShown?.();
        if (extractionRef.current !== wanted) return;
        begin(result.session);
      })
      .catch((error) => {
        props?.onExerciseShown?.();
        onError(errorMessage(error, "Couldn't open this exercise."));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, exercise, extractionId, card?.sourceId]);

  const reopenAbandoned = useCallback(async () => {
    if (!abandoned) return;
    await resume(abandoned.sessionId);
  }, [abandoned, resume]);

  const update = useCallback((session: WorkbenchSessionDto) => {
    setActive((current) => (current && current.session.sessionId === session.sessionId ? { ...current, session } : current));
    noteAdmission(session);
  }, [noteAdmission]);

  const close = useCallback((session: WorkbenchSessionDto | null, options?: { abandoned?: boolean }) => {
    const target = session ?? active?.session ?? null;
    setActive(null);
    setSheetOpen(false);
    setAbandoned(options?.abandoned && target ? target : null);
    void refresh();
    return target?.spanIds[0] ?? null;
  }, [active, refresh]);

  const submitted = useCallback((result: WorkbenchSubmitDto) => {
    const spanId = result.session.spanIds[0] ?? active?.session.spanIds[0] ?? "";
    setActive(null);
    void refresh();
    if (card && props?.onSubmitted) props.onSubmitted(result, { card, spanId });
  }, [active, card, props, refresh]);

  return {
    enabled,
    sessions,
    active,
    abandoned,
    width: clampSplitWidth(width, windowWidth),
    narrow: isNarrow(windowWidth),
    sheetOpen,
    setSheetOpen,
    resizeBy,
    setWidth,
    openSelection,
    openItem,
    resume,
    reopenAbandoned,
    update,
    close,
    submitted,
  };
}

export { SPLIT_STEP };
