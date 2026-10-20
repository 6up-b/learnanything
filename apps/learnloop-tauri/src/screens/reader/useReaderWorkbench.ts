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
// reads that at the pick).
//
// Fix round 4 (orchestrator rulings): the server owns the admission. When the
// import has bound the problem to the item it wrote and its learner pick is
// still owed (`exercisePick.due`, durable on the problem), the hook asks the
// server's one operation, `workbench.admit`, for THAT problem by its id; the
// server makes the pick, serves it and records both on the problem, and a
// submit admits first itself (R1, R2). The hook keeps no hand-off state of its
// own: it renders what admit and open return, after checking that the answer
// is for the problem it asked about. One generation counter (bumped on Leave,
// a book change and unmount) is captured by every async callback (open,
// resume, refresh, admit, submit, check), and a stale one is dropped before
// any state change or shell callback (R5); the newest open wins among opens.
// The shell's queued exercise and check are consumed by identity, so an older
// completion never clears a newer request. A submit goes back to the
// submitted problem's own book (round 3, R3).
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  ReaderImportExerciseInput,
  SessionSnapshot,
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
  /** "practice_this" resumes a problem with the book as the learner left it;
   *  else "check_me" (the book hidden). */
  entry?: "check_me" | "practice_this";
}

export interface ReaderWorkbenchProps {
  /** The app's open practice session, when there is one (the submit and an
   *  exercise's admission use it). */
  practiceSessionId?: string | null;
  /** RW4b: "use this one" to open once its source is open (the shell picked it). */
  exercise?: ReaderWorkbenchExercise | null;
  /** That exercise's problem opened: the shell forgets THIS request (by
   *  identity), never a newer one queued since (fix round 4, F9). */
  onExerciseShown?: (shown: ReaderWorkbenchExercise) => void;
  /** RW4b fix round 4: an exercise's admission started (or resolved) the
   *  practice session its learner pick was made in. */
  onPracticeSession?: (practiceSession: SessionSnapshot) => void;
  /** "Check me" to open in the working posture, book hidden (D40). */
  checkMe?: ReaderWorkbenchCheck | null;
  /** That check opened (or failed): the shell forgets THIS one, by identity. */
  onCheckMeShown?: (shown: ReaderWorkbenchCheck) => void;
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
  /** The book the problem is on (its own source, checked when it was
   *  activated): where back from its feedback returns (round 3, R3). */
  card: SourceLibraryCard;
  /** The generation it was shown in: the workbench's own callbacks (its
   *  import refresh, its submit) carry it back, and a stale one is dropped. */
  generation: number;
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
  /** The session changed inside the workbench (the book, the binding); the
   *  generation the workbench was shown in, when it knows it. */
  update: (session: WorkbenchSessionDto, generation?: number) => void;
  /** Collapse back into reading; returns the passage to return to. A
   *  departure from a workbench (Leave, Abandon) names the problem it leaves
   *  and the generation it was shown in: a stale one changes nothing and
   *  returns null, so nothing jumps (fix round 5, R5). */
  close: (session: WorkbenchSessionDto | null, options?: { abandoned?: boolean; generation?: number }) => string | null;
  submitted: (result: WorkbenchSubmitDto, generation?: number) => void;
}

/** What an async request was sent against: the generation, the open book,
 *  and (for an open) its place among opens. */
interface Ticket {
  generation: number;
  open: number;
  extractionId: string | null;
  sourceId: string | null;
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
  const cardRef = useRef(card);
  cardRef.current = card;
  const activeRef = useRef<ActiveWorkbench | null>(null);
  activeRef.current = active;
  const propsRef = useRef(props);
  propsRef.current = props;

  // R5: the one generation counter. Leave, a book change and unmount bump it;
  // every async callback captured it when it was sent and is dropped, before
  // any state change or shell callback, once it is stale. Among opens the
  // newest wins too (`openSeq`), so a slower earlier open never replaces a
  // later one. Only an answer for a problem on the open book is admitted.
  const generation = useRef(0);
  const openSeq = useRef(0);
  const bump = useCallback(() => {
    generation.current += 1;
  }, []);
  useEffect(() => () => bump(), [bump]);
  const ticket = useCallback((isOpen: boolean): Ticket => {
    if (isOpen) openSeq.current += 1;
    return {
      generation: generation.current, open: openSeq.current,
      extractionId: extractionRef.current, sourceId: cardRef.current?.sourceId ?? null,
    };
  }, []);
  const fresh = useCallback((sent: Ticket) => (
    generation.current === sent.generation
      && openSeq.current === sent.open
      && extractionRef.current === sent.extractionId
      && (cardRef.current?.sourceId ?? null) === sent.sourceId
  ), []);
  const onOpenBook = useCallback((session: WorkbenchSessionDto, book: Pick<Ticket, "extractionId" | "sourceId">) => (
    Boolean(book.extractionId) && Boolean(book.sourceId)
      && (!session.extractionId || session.extractionId === book.extractionId)
      && (!session.sourceId || session.sourceId === book.sourceId)
  ), []);
  const admits = useCallback((sent: Ticket, session: WorkbenchSessionDto) => fresh(sent) && onOpenBook(session, sent),
    [fresh, onOpenBook]);

  // The marks' list: the newest request's answer wins (round 5 audit), on the
  // book it was asked for.
  const refreshSeq = useRef(0);
  const refresh = useCallback(async () => {
    const current = extractionRef.current;
    if (!enabled || !current) return;
    refreshSeq.current += 1;
    const asked = refreshSeq.current;
    try {
      const result = await api.workbenchForSource({ extractionId: current });
      if (extractionRef.current === current && refreshSeq.current === asked) setSessions(result.sessions);
    } catch {
      // The marks are a convenience: without them the source still reads.
    }
  }, [enabled]);

  useEffect(() => {
    // Another book: every answer still in flight is for the one left.
    bump();
    setSessions([]);
    setActive(null);
    setAbandoned(null);
    void refresh();
  }, [extractionId, refresh, bump]);

  // Back from feedback (UX S6): the submitted problem, read-only.
  // It opens once the source it belongs to is open, and only once.
  const initialAttemptId = props?.initialAttemptId ?? null;
  const openedAttemptRef = useRef<string | null>(null);
  useEffect(() => {
    if (!enabled || !initialAttemptId || !extractionId || openedAttemptRef.current === initialAttemptId) return;
    openedAttemptRef.current = initialAttemptId;
    const sent = ticket(true);
    void api.workbenchSessionForAttempt({ attemptId: initialAttemptId })
      .then((result) => {
        const session = result.session;
        const shown = cardRef.current;
        if (session && shown && session.extractionId === extractionId && admits(sent, session)) {
          setActive({ session, readOnly: true, autoFocus: false, card: shown, generation: sent.generation });
          propsRef.current?.onInitialAttemptShown?.();
        }
      })
      .catch(() => undefined);
  }, [enabled, initialAttemptId, extractionId, admits, ticket]);

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

  // RW4b fix round 4 (R1): a problem whose exercise pick is owed (the
  // server's durable `exercisePick.due`) is admitted by the server's one
  // operation, for THAT problem by its id. Nothing is remembered here but
  // which admissions are in flight (no two at once for one problem); a
  // failed one stays owed on the server and is asked again on the problem's
  // next sight. The answer is admitted only while its generation is current
  // and it is for the problem asked about; it then refreshes the shown
  // problem (its exposure, its serve) through the workbench's update path.
  const admitting = useRef(new Set<string>());
  const admit = useCallback((session: WorkbenchSessionDto) => {
    const book = { extractionId: extractionRef.current, sourceId: cardRef.current?.sourceId ?? null };
    if (!session.exercisePick?.due || !session.practiceItemId || session.status !== "open") return;
    if (!session.extractionId || !session.sourceId || !onOpenBook(session, book)) return;
    if (admitting.current.has(session.sessionId)) return;
    admitting.current.add(session.sessionId);
    const sentGeneration = generation.current;
    const asked = session.sessionId;
    void api.workbenchAdmit({ sessionId: asked, practiceSessionId: propsRef.current?.practiceSessionId ?? null })
      .then((result) => {
        if (generation.current !== sentGeneration || result.session.sessionId !== asked) return;
        if (!onOpenBook(result.session, { extractionId: extractionRef.current, sourceId: cardRef.current?.sourceId ?? null })) return;
        setActive((current) => (current && current.session.sessionId === asked ? { ...current, session: result.session } : current));
        if (result.practiceSession) propsRef.current?.onPracticeSession?.(result.practiceSession);
      })
      .catch((error) => {
        if (generation.current !== sentGeneration) return;
        onError(errorMessage(error, "Couldn't add this exercise to your practice yet."));
      })
      .finally(() => admitting.current.delete(asked));
  }, [onError, onOpenBook]);

  type Serve = { schedulerCandidateId: string | null; planPresentationId: string | null };
  // Only an admitted answer begins a problem (its ticket was checked, so the
  // open card is the problem's own book).
  const begin = useCallback((session: WorkbenchSessionDto, sent: Ticket, readOnly = false, serve?: Serve) => {
    const shown = cardRef.current;
    if (!shown) return;
    setAbandoned(null);
    setSheetOpen(false);
    setActive({ session, readOnly, autoFocus: !readOnly, card: shown, generation: sent.generation, ...(serve ?? {}) });
    admit(session);
  }, [admit]);

  const openSelection = useCallback(async (request: { stemMd: string; spanIds: string[]; importRequest: ReaderImportExerciseInput }) => {
    if (!enabled || !extractionId) return;
    const sent = ticket(true);
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", stemMd: request.stemMd, extractionId,
        spanIds: request.spanIds, importRequest: request.importRequest, clientIdempotencyKey: newKey(),
      });
      if (admits(sent, result.session)) begin(result.session, sent);
    } catch (error) {
      if (fresh(sent)) onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [admits, begin, enabled, extractionId, fresh, onError, ticket]);

  const openItem = useCallback(async (request: { practiceItemId: string; stemMd: string; spanIds: string[] }) => {
    if (!enabled || !extractionId) return;
    const sent = ticket(true);
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", practiceItemId: request.practiceItemId, stemMd: request.stemMd,
        extractionId, spanIds: request.spanIds, clientIdempotencyKey: newKey(),
      });
      if (admits(sent, result.session)) begin(result.session, sent);
    } catch (error) {
      if (fresh(sent)) onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [admits, begin, enabled, extractionId, fresh, onError, ticket]);

  const resume = useCallback(async (sessionId: string) => {
    const sent = ticket(true);
    try {
      // One explicit resume, by the problem's id (round 4, R3): reopened when
      // set aside, and moved into the Reader (its anchors here, the book
      // hidden once steps exist) when it was worked on the practice screen
      // (review F4). The answer must be that problem, on the open book.
      const result = await api.workbenchOpen({ origin: "reader", entry: "resume", sessionId, extractionId: sent.extractionId });
      if (result.session.sessionId === sessionId && admits(sent, result.session)) begin(result.session, sent);
    } catch (error) {
      if (fresh(sent)) onError(errorMessage(error, "Couldn't reopen this problem."));
    }
  }, [admits, begin, fresh, onError, ticket]);

  // "Check me" (D40): once its source is the one open, the check opens in the
  // working posture with the book hidden, as the pick's own serve. The shell
  // forgets this check (by identity) once it opened or failed, never a newer
  // one; an answer gone stale changes nothing, and the check is opened again
  // when it can be (a later generation).
  const checkMe = props?.checkMe ?? null;
  const openedCheckRef = useRef<{ check: ReaderWorkbenchCheck; generation: number } | null>(null);
  useEffect(() => {
    if (!enabled || !checkMe || !extractionId || !card || card.sourceId !== checkMe.sourceId) return;
    if (openedCheckRef.current?.check === checkMe && openedCheckRef.current.generation === generation.current) return;
    openedCheckRef.current = { check: checkMe, generation: generation.current };
    const sent = ticket(true);
    void api.workbenchOpen({
      origin: "reader", entry: checkMe.entry ?? "check_me", practiceItemId: checkMe.practiceItemId, stemMd: checkMe.stemMd,
      extractionId: sent.extractionId, spanIds: [checkMe.spanId], clientIdempotencyKey: newKey(),
      // The pick's serve goes on the problem itself, so leaving and resuming
      // it still submits as that serve (review F13); the server also hides
      // the book on a reused problem, keeping what it counted (F14).
      schedulerCandidateId: checkMe.schedulerCandidateId, planPresentationId: checkMe.planPresentationId,
    })
      .then((result) => {
        if (!admits(sent, result.session)) return;
        propsRef.current?.onCheckMeShown?.(checkMe);
        begin(result.session, sent, false, {
          schedulerCandidateId: checkMe.schedulerCandidateId, planPresentationId: checkMe.planPresentationId,
        });
      })
      .catch((error) => {
        if (!fresh(sent)) return;
        propsRef.current?.onCheckMeShown?.(checkMe);
        onError(errorMessage(error, "Couldn't open the check."));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, checkMe, extractionId, card?.sourceId]);

  // RW4b: "use this one" (the shell picked it): once its source is open, the
  // problem opens at once on the verbatim statement while its import runs.
  // Consumed by identity (round 4, F9): an older open's answer never clears a
  // newer exercise the learner chose since.
  const exercise = props?.exercise ?? null;
  const openedExerciseRef = useRef<{ exercise: ReaderWorkbenchExercise; generation: number } | null>(null);
  useEffect(() => {
    if (!enabled || !exercise || !extractionId || !card || card.sourceId !== exercise.sourceId) return;
    if (openedExerciseRef.current?.exercise === exercise && openedExerciseRef.current.generation === generation.current) return;
    openedExerciseRef.current = { exercise, generation: generation.current };
    const sent = ticket(true);
    void api.workbenchOpen({
      origin: "reader", entry: exercise.entry, stemMd: exercise.stemMd, extractionId: exercise.extractionId,
      spanIds: exercise.spanIds, clientIdempotencyKey: newKey(),
      ...(exercise.sourceExercise
        ? { sourceExercise: exercise.sourceExercise }
        : { importRequest: exercise.importRequest ?? null, ...(exercise.exercisePick ? { exercisePick: exercise.exercisePick } : {}) }),
    })
      .then((result) => {
        if (!admits(sent, result.session)) return;
        propsRef.current?.onExerciseShown?.(exercise);
        begin(result.session, sent);
      })
      .catch((error) => {
        if (!fresh(sent)) return;
        propsRef.current?.onExerciseShown?.(exercise);
        onError(errorMessage(error, "Couldn't open this exercise."));
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, exercise, extractionId, card?.sourceId]);

  const reopenAbandoned = useCallback(async () => {
    if (!abandoned) return;
    await resume(abandoned.sessionId);
  }, [abandoned, resume]);

  // A change inside the shown workbench (its book, its import refresh). R5:
  // one from a workbench shown in an earlier generation (left, another book,
  // unmounted), or for a problem that is not the one shown, changes nothing
  // and admits nothing (Codex final verify F8).
  const update = useCallback((session: WorkbenchSessionDto, shownIn?: number) => {
    if (shownIn !== undefined && shownIn !== generation.current) return;
    const current = activeRef.current;
    if (!current || current.session.sessionId !== session.sessionId) return;
    if (!onOpenBook(session, { extractionId: extractionRef.current, sourceId: cardRef.current?.sourceId ?? null })) return;
    setActive((now) => (now && now.session.sessionId === session.sessionId ? { ...now, session } : now));
    admit(session);
  }, [admit, onOpenBook]);

  const close = useCallback((session: WorkbenchSessionDto | null, options?: { abandoned?: boolean; generation?: number }) => {
    // R5: a departure (Leave, Abandon) that completes after another problem
    // was opened, or after its own workbench went, closes nothing, sets no
    // receipt and jumps nowhere.
    const shown = activeRef.current;
    if (options?.generation !== undefined && options.generation !== generation.current) return null;
    if (session && (!shown || shown.session.sessionId !== session.sessionId)) return null;
    const target = session ?? shown?.session ?? null;
    bump(); // Leave: everything still in flight for the problem left is stale
    setActive(null);
    setSheetOpen(false);
    setAbandoned(options?.abandoned && target ? target : null);
    void refresh();
    return target?.spanIds[0] ?? null;
  }, [bump, refresh]);

  // A submit answers the problem it was made on. When that problem is no
  // longer the one shown (left, another book, another problem took its
  // place, a stale generation), the answer is dropped: it closes nothing and
  // leaves for no feedback (the attempt is kept, and the marks refresh). The
  // way back is the submitted problem's own book and passage, as checked
  // when it was activated, never the card shown now (round 3, R3).
  const submitted = useCallback((result: WorkbenchSubmitDto, shownIn?: number) => {
    const current = activeRef.current;
    const shown = current !== null
      && (shownIn === undefined || shownIn === generation.current)
      && current.session.sessionId === result.session.sessionId
      && (!result.session.extractionId || result.session.extractionId === extractionRef.current);
    void refresh();
    if (!current || !shown) return;
    bump(); // an open still in flight does not reopen over feedback
    const spanId = result.session.spanIds[0] ?? current.session.spanIds[0] ?? "";
    setActive(null);
    propsRef.current?.onSubmitted?.(result, { card: current.card, spanId });
  }, [bump, refresh]);

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
