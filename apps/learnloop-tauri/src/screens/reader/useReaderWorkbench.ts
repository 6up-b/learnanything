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
//
// Fix round 3 (orchestrator rulings R1-R3): what each problem is owed is kept
// per problem (`owed`, session id -> its hand-off), so no other problem's pick
// can displace it; every answer (an open, a resume, a check, an import
// refresh, a submit) is checked against the request it answers before
// anything changes (`issue`/`admits`), so no problem is activated on a book
// that is not the open one; and a submit goes back to the submitted problem's
// own book (`ActiveWorkbench.card`).
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
   *  the shell records and serves the pick, and resolves the served check,
   *  which this problem keeps until its own acknowledging open (R1). Resolves
   *  false or null when it could not (no session, a refused pick): nothing
   *  was acknowledged, so it is owed still. `true` means the shell hands the
   *  check over through `checkMe` instead (it is then kept the same way). */
  onExerciseAdmitted?: (admitted: ReaderExerciseAdmitted) => Promise<ReaderWorkbenchCheck | boolean | null> | ReaderWorkbenchCheck | boolean | null | void;
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
  /** The book the problem is on (its own source, checked when it was
   *  activated): where back from its feedback returns (R3). */
  card: SourceLibraryCard;
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

/** R2: what a request was sent against (its token, and the open book). */
interface Ticket {
  seq: number;
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

  // R2: every request that can change what the workbench shows takes a
  // ticket (the request token, and the book and extraction open when it was
  // sent). Its answer is admitted only while it is still the newest request
  // and the same book is open, and only for a problem on that book; anything
  // else is dropped before any state changes, and the problem stays
  // resumable (and owed, if its pick is).
  const requestSeq = useRef(0);
  const issue = useCallback((): Ticket => {
    requestSeq.current += 1;
    return { seq: requestSeq.current, extractionId: extractionRef.current, sourceId: cardRef.current?.sourceId ?? null };
  }, []);
  const stillOpen = useCallback((ticket: Ticket) => (
    requestSeq.current === ticket.seq
      && extractionRef.current === ticket.extractionId
      && (cardRef.current?.sourceId ?? null) === ticket.sourceId
  ), []);
  const onOpenBook = useCallback((session: WorkbenchSessionDto, ticket: Pick<Ticket, "extractionId" | "sourceId">) => (
    Boolean(ticket.extractionId) && Boolean(ticket.sourceId)
      && (!session.extractionId || session.extractionId === ticket.extractionId)
      && (!session.sourceId || session.sourceId === ticket.sourceId)
  ), []);
  const admits = useCallback((ticket: Ticket, session: WorkbenchSessionDto) => stillOpen(ticket) && onOpenBook(session, ticket), [onOpenBook, stillOpen]);

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
    // Another book: every answer still in flight is for the one left (R2).
    requestSeq.current += 1;
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
    const ticket = issue();
    void api.workbenchSessionForAttempt({ attemptId: initialAttemptId })
      .then((result) => {
        const session = result.session;
        const shown = cardRef.current;
        if (session && shown && session.extractionId === extractionId && admits(ticket, session)) {
          setActive({ session, readOnly: true, autoFocus: false, card: shown });
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
  // `exercisePick.due`, Codex review F2) is handed to the shell, which makes
  // and serves the pick; the server acknowledges it only when that pick's own
  // open (`admittedSessionId`) succeeds.
  //
  // R1 (fix round 3): what each problem is owed is kept here per problem
  // (session id -> its hand-off), never in one shared slot:
  // - "picking": the shell is making and serving the pick;
  // - "served": the served check, kept until this problem's own book is open
  //   and the problem is seen (opened, resumed, refreshed), when it is opened
  //   as that pick; a pick served while another book is open, or after the
  //   learner moved on, waits here, and no other problem's pick displaces it;
  // - "opening": its acknowledging open is in flight;
  // - "delivered": that open succeeded (acknowledged), so this visit never
  //   hands it over again, even if a late answer still calls it due.
  // A failed pick or a failed acknowledging open removes the entry: nothing
  // was acknowledged, so the next sight of the problem (this visit, or after
  // a restart, from the server's `due`) hands it over again, with a new
  // serve. Nothing retries at once.
  type Owed =
    | { phase: "picking"; ticket: Ticket }
    | { phase: "served"; check: ReaderWorkbenchCheck; ticket: Ticket | null }
    | { phase: "opening" }
    | { phase: "delivered" };
  const owed = useRef(new Map<string, Owed>());
  const onAdmittedRef = useRef(props?.onExerciseAdmitted);
  onAdmittedRef.current = props?.onExerciseAdmitted;
  const beginRef = useRef<(session: WorkbenchSessionDto, ticket: Ticket, readOnly?: boolean, serve?: Serve) => void>(() => undefined);

  // The served pick opens its problem as that pick's serve, acknowledging it.
  const deliver = useCallback((sessionId: string, check: ReaderWorkbenchCheck) => {
    const ticket = issue();
    owed.current.set(sessionId, { phase: "opening" });
    void api.workbenchOpen({
      origin: "reader", entry: check.entry ?? "check_me", practiceItemId: check.practiceItemId, stemMd: check.stemMd,
      extractionId: ticket.extractionId, spanIds: [check.spanId], clientIdempotencyKey: newKey(),
      schedulerCandidateId: check.schedulerCandidateId, planPresentationId: check.planPresentationId,
      admittedSessionId: sessionId,
    })
      .then((result) => {
        // Acknowledged by its own open, whether or not it is still shown.
        owed.current.set(sessionId, { phase: "delivered" });
        if (!admits(ticket, result.session)) return;
        beginRef.current(result.session, ticket, false, {
          schedulerCandidateId: check.schedulerCandidateId, planPresentationId: check.planPresentationId,
        });
      })
      .catch((error) => {
        // Not acknowledged: owed still, handed over again on its next sight.
        owed.current.delete(sessionId);
        onError(errorMessage(error, "Couldn't open the check."));
      });
  }, [admits, issue, onError]);

  // A served check for a problem: kept; opened now only when it answers the
  // newest request on the problem's own book (else on the problem's next sight).
  const served = useCallback((sessionId: string, check: ReaderWorkbenchCheck, ticket: Ticket | null) => {
    owed.current.set(sessionId, { phase: "served", check, ticket });
    const now = ticket ? stillOpen(ticket) : true;
    if (now && cardRef.current?.sourceId === check.sourceId) deliver(sessionId, check);
  }, [deliver, stillOpen]);

  const noteAdmission = useCallback((session: WorkbenchSessionDto) => {
    const open = cardRef.current;
    // The pick names the book the exercise is in (re-review F6): a problem on
    // another book than the open one (or while the open card and extraction
    // disagree) admits nothing; it stays owed until its own book is open.
    const book = { extractionId: extractionRef.current, sourceId: open?.sourceId ?? null };
    if (!open || !session.extractionId || !session.sourceId || !onOpenBook(session, book)) return;
    const entry = owed.current.get(session.sessionId);
    if (entry?.phase === "served") {
      deliver(session.sessionId, entry.check);
      return;
    }
    if (entry) return; // picking, opening or delivered
    const due = session.exercisePick;
    if (!due?.due || !session.practiceItemId) return;
    const handOff = onAdmittedRef.current;
    if (!handOff) return;
    const ticket: Ticket = { seq: requestSeq.current, ...book };
    owed.current.set(session.sessionId, { phase: "picking", ticket });
    const release = () => {
      if (owed.current.get(session.sessionId)?.phase === "picking") owed.current.delete(session.sessionId);
    };
    Promise.resolve()
      .then(() => handOff({
        practiceItemId: session.practiceItemId as string,
        proposalId: due.proposalId,
        importId: session.sourceExercise?.importId ?? null,
        sourceId: open.sourceId,
        card: open,
        spanId: session.spanIds[0] ?? "",
        stemMd: session.stemMd,
        workbenchSessionId: session.sessionId,
      }))
      .then((outcome) => {
        if (outcome && typeof outcome === "object") {
          if (owed.current.get(session.sessionId)?.phase === "picking") served(session.sessionId, outcome, ticket);
          return;
        }
        // `true`: the check comes through `checkMe` (kept below); else owed.
        if (outcome !== true) release();
      })
      .catch(release);
  }, [deliver, onOpenBook, served]);

  type Serve = { schedulerCandidateId: string | null; planPresentationId: string | null };
  // Only an admitted answer begins a problem (its ticket was checked, so the
  // open card is the problem's own book).
  const begin = useCallback((session: WorkbenchSessionDto, _ticket: Ticket, readOnly = false, serve?: Serve) => {
    const shown = cardRef.current;
    if (!shown) return;
    setAbandoned(null);
    setSheetOpen(false);
    setActive({ session, readOnly, autoFocus: !readOnly, card: shown, ...(serve ?? {}) });
    noteAdmission(session);
  }, [noteAdmission]);
  beginRef.current = begin;

  const openSelection = useCallback(async (request: { stemMd: string; spanIds: string[]; importRequest: ReaderImportExerciseInput }) => {
    if (!enabled || !extractionId) return;
    const ticket = issue();
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", stemMd: request.stemMd, extractionId,
        spanIds: request.spanIds, importRequest: request.importRequest, clientIdempotencyKey: newKey(),
      });
      if (admits(ticket, result.session)) begin(result.session, ticket);
    } catch (error) {
      onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [admits, begin, enabled, extractionId, issue, onError]);

  const openItem = useCallback(async (request: { practiceItemId: string; stemMd: string; spanIds: string[] }) => {
    if (!enabled || !extractionId) return;
    const ticket = issue();
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", practiceItemId: request.practiceItemId, stemMd: request.stemMd,
        extractionId, spanIds: request.spanIds, clientIdempotencyKey: newKey(),
      });
      if (admits(ticket, result.session)) begin(result.session, ticket);
    } catch (error) {
      onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [admits, begin, enabled, extractionId, issue, onError]);

  const resume = useCallback(async (sessionId: string) => {
    const ticket = issue();
    try {
      // One explicit resume: reopened when set aside, and moved into the
      // Reader (its anchors here, the book hidden once steps exist) when it
      // was worked on the practice screen (review F4).
      const result = await api.workbenchOpen({ origin: "reader", entry: "resume", sessionId, extractionId: ticket.extractionId });
      // R2: an answer for a book no longer open, or overtaken by a newer
      // request, changes nothing; the problem stays resumable (and owed).
      if (admits(ticket, result.session)) begin(result.session, ticket);
    } catch (error) {
      onError(errorMessage(error, "Couldn't reopen this problem."));
    }
  }, [admits, begin, issue, onError]);

  // "Check me" (D40): once its source is the one open, the check opens in the
  // working posture with the book hidden, as the pick's own serve. An
  // exercise's pick handed over this way (`admitsSessionId`) leaves the
  // shell's slot at once and is kept with its problem (R1), so a later check
  // replacing the slot cannot displace it.
  const checkMe = props?.checkMe ?? null;
  const openedCheckRef = useRef<ReaderWorkbenchCheck | null>(null);
  useEffect(() => {
    if (!enabled || !checkMe || openedCheckRef.current === checkMe) return;
    if (checkMe.admitsSessionId) {
      openedCheckRef.current = checkMe;
      const entry = owed.current.get(checkMe.admitsSessionId);
      props?.onCheckMeShown?.();
      if (entry?.phase === "opening" || entry?.phase === "delivered") return;
      served(checkMe.admitsSessionId, checkMe, entry?.phase === "picking" ? entry.ticket : null);
      return;
    }
    if (!extractionId || !card || card.sourceId !== checkMe.sourceId) return;
    openedCheckRef.current = checkMe;
    const ticket = issue();
    void api.workbenchOpen({
      origin: "reader", entry: checkMe.entry ?? "check_me", practiceItemId: checkMe.practiceItemId, stemMd: checkMe.stemMd,
      extractionId: ticket.extractionId, spanIds: [checkMe.spanId], clientIdempotencyKey: newKey(),
      // The pick's serve goes on the problem itself, so leaving and resuming
      // it still submits as that serve (review F13); the server also hides
      // the book on a reused problem, keeping what it counted (F14).
      schedulerCandidateId: checkMe.schedulerCandidateId, planPresentationId: checkMe.planPresentationId,
    })
      .then((result) => {
        props?.onCheckMeShown?.();
        if (!admits(ticket, result.session)) return;
        begin(result.session, ticket, false, {
          schedulerCandidateId: checkMe.schedulerCandidateId, planPresentationId: checkMe.planPresentationId,
        });
      })
      .catch((error) => {
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
    const ticket = issue();
    void api.workbenchOpen({
      origin: "reader", entry: exercise.entry, stemMd: exercise.stemMd, extractionId: exercise.extractionId,
      spanIds: exercise.spanIds, clientIdempotencyKey: newKey(),
      ...(exercise.sourceExercise
        ? { sourceExercise: exercise.sourceExercise }
        : { importRequest: exercise.importRequest ?? null, ...(exercise.exercisePick ? { exercisePick: exercise.exercisePick } : {}) }),
    })
      .then((result) => {
        props?.onExerciseShown?.();
        if (!admits(ticket, result.session)) return;
        begin(result.session, ticket);
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

  // An import refresh (or any change inside the workbench) answers the problem
  // shown: one for a problem on a book no longer open changes nothing (R2).
  const update = useCallback((session: WorkbenchSessionDto) => {
    const book = { extractionId: extractionRef.current, sourceId: cardRef.current?.sourceId ?? null };
    if (!onOpenBook(session, book)) return;
    setActive((current) => (current && current.session.sessionId === session.sessionId ? { ...current, session } : current));
    noteAdmission(session);
  }, [noteAdmission, onOpenBook]);

  const close = useCallback((session: WorkbenchSessionDto | null, options?: { abandoned?: boolean }) => {
    const target = session ?? active?.session ?? null;
    requestSeq.current += 1; // leaving overtakes an open still in flight
    setActive(null);
    setSheetOpen(false);
    setAbandoned(options?.abandoned && target ? target : null);
    void refresh();
    return target?.spanIds[0] ?? null;
  }, [active, refresh]);

  // A submit answers the problem it was made on. R2: when that problem is no
  // longer the one shown (another book's extraction opened, or another
  // problem took its place), the answer is dropped: it closes nothing and
  // leaves for no feedback (the attempt is kept, and the marks refresh).
  // R3: the way back is the submitted problem's own book and passage, as it
  // was checked when the problem was activated, never the card shown now
  // (the open card can run ahead of the extraction while a book opens).
  const submitted = useCallback((result: WorkbenchSubmitDto) => {
    const current = activeRef.current;
    const shown = current !== null
      && current.session.sessionId === result.session.sessionId
      && (!result.session.extractionId || result.session.extractionId === extractionRef.current);
    void refresh();
    if (!current || !shown) return;
    requestSeq.current += 1; // an open still in flight does not reopen over feedback
    const spanId = result.session.spanIds[0] ?? current.session.spanIds[0] ?? "";
    setActive(null);
    props?.onSubmitted?.(result, { card: current.card, spanId });
  }, [props, refresh]);

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
