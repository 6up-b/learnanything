// Reader workbench RW2a: one workbench session's state and its write queue
// (spec §5.1 "saving and resuming"; UX §5.3).
//
// Every change to the work is saved as it is typed, modelled on the practice
// screen's draft checkpoints: a per-step debounce, then one serial queue. Each
// write carries its own idempotency key, and the payload it was first sent
// with is frozen under that key: a retry resends exactly that payload, so a
// write whose response was lost is answered from the row it wrote and nothing
// is saved twice. Text typed while a write is in flight or backing off goes
// in a later write under a new key, and after every acknowledged write the
// step's saved text is compared with the window's, so "saved" always means
// the text on screen is the text stored (review F5).
//
// The book's visibility is a write in the same queue (review F3): the text
// typed with the book shown is flushed and saved before the book's change, so
// the server records the book under which it was written. While a step's
// write stands refused, hiding the book waits behind it (the step was written
// with the book shown, and its corrected text is saved that way first), and
// every later book change waits in order behind the hide (review re-review F3);
// showing it never waits, so new work is never saved as unassisted while the
// book is on screen. A write the server refuses for good (a step too long, a closed problem) is kept as "not
// saved", and nothing that needs the work persisted (Submit, Abandon, a vault
// switch, closing the window) goes ahead until the learner fixes or deletes
// it (review F6, F7). A vault switch freezes editing and waits for the queue
// against the vault the steps belong to; closing the window waits for it too
// (review F8). Nothing a write or a poll returns moves focus (W12).
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  WorkbenchRecordDto,
  WorkbenchSaveStepInput,
  WorkbenchSessionDto,
  WorkbenchStepKind,
  WorkbenchSubmitDto,
  WorkbenchSubmitInput,
} from "../../api/dto";
import { useCloseWithFlush } from "../../app/useCloseWithFlush";
import { registerVaultDraft } from "../../app/vaultTransition";
import { errorMessage, getCommandError } from "../../errors";
import { phaseForError } from "../reader/ModelActionState";
import {
  deleteLocal,
  fromServer,
  insertAfter,
  restoreLocal,
  updateLocal,
  type LocalStep,
  type SaveStatus,
} from "./stepModel";

/** How long a step rests before its text is saved. */
export const EDIT_DEBOUNCE_MS = 600;
const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000];
/** Retries a queue keeps making after the workbench closed (then it stops). */
const RETRIES_AFTER_CLOSE = 5;
/** Refusals a retry cannot fix: kept as "not saved" and the learner told. */
const PERMANENT = new Set(["validation_error", "not_found", "not_open", "already_submitted", "workbench_disabled", "no_book"]);
/** The rejection key of the book's visibility (steps use their own key). */
const BOOK_KEY = "\u0000book";

type StepOpKind = "add" | "edit" | "delete" | "restore";
type StepOp = { kind: StepOpKind; key: string; idem: string; payload?: WorkbenchSaveStepInput };
type BookOp = { kind: "book"; key: typeof BOOK_KEY; idem: string; visible: boolean; payload?: { sessionId: string; visible: boolean } };
type Op = StepOp | BookOp;

function newKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `k${Date.now()}${Math.random()}`;
}

/** A write that has not landed: what Submit, Abandon and a vault switch refuse on. */
export function notSavedError(reason: string | null, action: string): { code: "not_saved"; message: string } {
  return {
    code: "not_saved",
    message: reason
      ? `A step isn't saved (${reason}), so ${action}. Shorten it or delete it, then try again.`
      : `Your latest steps are not saved yet, so ${action}. They're safe in this window.`,
  };
}

export interface WorkbenchSessionControls {
  session: WorkbenchSessionDto;
  steps: LocalStep[];
  record: WorkbenchRecordDto;
  save: SaveStatus;
  /** Something was written on this visit (the book line gives way). */
  started: boolean;
  /** A vault switch is waiting on these steps: editing is paused. */
  frozen: boolean;
  setBody: (key: string, body: string) => void;
  /** A new step after `afterKey` (or at the end); returns its key. */
  addStep: (afterKey: string | null, kind?: WorkbenchStepKind) => string;
  deleteStep: (key: string) => void;
  undoDelete: (key: string) => void;
  /** Send every resting edit now. */
  flushEdits: () => void;
  /** Resolves true once every write has landed, false when one is failing or refused. */
  drained: () => Promise<boolean>;
  setBook: (visible: boolean) => Promise<void>;
  leave: () => Promise<void>;
  abandon: () => Promise<WorkbenchSessionDto | null>;
  reopen: () => Promise<void>;
  retryImport: () => Promise<void>;
  bind: (practiceItemId: string) => Promise<void>;
  submit: (input: Omit<WorkbenchSubmitInput, "sessionId">) => Promise<WorkbenchSubmitDto>;
}

export function useWorkbenchSession(
  initial: WorkbenchSessionDto,
  options: { readOnly?: boolean; onSession?: (session: WorkbenchSessionDto) => void; onError: (message: string) => void },
): WorkbenchSessionControls {
  const readOnly = options.readOnly ?? false;
  const [session, setSessionState] = useState(initial);
  const [record, setRecord] = useState(initial.record);
  const [steps, setStepsState] = useState<LocalStep[]>(() => {
    const local = fromServer(initial.steps.filter((step) => !step.deleted));
    // An empty problem opens on its first (empty) step: "1 › _" (UX W8).
    return local.length === 0 && !readOnly ? [{ key: newKey(), serverId: null, kind: "step", body: "", deleted: false, versions: [] }] : local;
  });
  const [save, setSave] = useState<SaveStatus>({ state: "saved", savedAt: initial.updatedAt });
  const [started, setStarted] = useState(() => initial.steps.length > 0);
  const [frozen, setFrozen] = useState(false);

  const sessionRef = useRef(session);
  const stepsRef = useRef(steps);
  const queue = useRef<Op[]>([]);
  const running = useRef(false);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const failures = useRef(0);
  const closed = useRef(false);
  const frozenRef = useRef(false);
  /** Writes the server refused for good, by step key (or the book's), with why. */
  const rejected = useRef(new Map<string, string>());
  const editTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const waiters = useRef<Array<(ok: boolean) => void>>([]);
  const onSessionRef = useRef(options.onSession);
  onSessionRef.current = options.onSession;
  const onErrorRef = useRef(options.onError);
  onErrorRef.current = options.onError;

  const commitSteps = useCallback((next: LocalStep[]) => {
    stepsRef.current = next;
    setStepsState(next);
  }, []);
  const commitSession = useCallback((next: WorkbenchSessionDto, notify = true) => {
    sessionRef.current = next;
    setSessionState(next);
    setRecord(next.record);
    if (notify) onSessionRef.current?.(next);
  }, []);

  const firstRejection = useCallback(() => (rejected.current.size > 0 ? [...rejected.current.values()][0] : null), []);

  const settleWaiters = useCallback((ok: boolean) => {
    const pending = waiters.current;
    waiters.current = [];
    for (const resolve of pending) resolve(ok);
  }, []);

  /** The queue is empty: saved, or "not saved" while a refused write stands. */
  const settleIdle = useCallback(() => {
    const reason = firstRejection();
    // "saved · just now" counts from when this window heard back (the
    // sidecar's clock may differ from this one).
    setSave(reason ? { state: "rejected", savedAt: null, reason } : { state: "saved", savedAt: new Date().toISOString() });
    settleWaiters(reason === null);
  }, [firstRejection, settleWaiters]);

  const stepInput = useCallback((op: StepOp): WorkbenchSaveStepInput | null => {
    const list = stepsRef.current;
    const index = list.findIndex((step) => step.key === op.key);
    const step = list[index];
    if (!step) return null;
    const sessionId = sessionRef.current.sessionId;
    if (op.kind === "add") {
      const before = list.slice(0, index).reverse().find((candidate) => candidate.serverId !== null);
      return { sessionId, clientIdempotencyKey: op.idem, op: "add", kind: step.kind, bodyMd: step.body, afterStepId: before?.serverId ?? null };
    }
    if (step.serverId === null) return null;
    if (op.kind === "edit") return { sessionId, clientIdempotencyKey: op.idem, op: "edit", stepId: step.serverId, bodyMd: step.body };
    return { sessionId, clientIdempotencyKey: op.idem, op: op.kind, stepId: step.serverId };
  }, []);

  const hasUnsentWrite = useCallback((key: string) =>
    queue.current.some((queued) => queued.key === key && (queued.kind === "add" || queued.kind === "edit") && !queued.payload), []);

  /** The next write to send: the queue's head, except that hiding the book
   *  (and every book change after it) waits while a step's write stands
   *  refused, and the step writes behind it go first (re-review F3). */
  const nextOp = useCallback((): Op | undefined => {
    const stepRefused = [...rejected.current.keys()].some((key) => key !== BOOK_KEY);
    const firstBook = queue.current.find((queued) => queued.kind === "book") as BookOp | undefined;
    const holdBook = stepRefused && firstBook !== undefined && !firstBook.payload && !firstBook.visible;
    return holdBook ? queue.current.find((queued) => queued.kind !== "book") : queue.current[0];
  }, []);
  const dequeue = useCallback((op: Op) => {
    queue.current = queue.current.filter((queued) => queued !== op);
  }, []);

  const pump = useCallback(async () => {
    if (running.current || retryTimer.current) return;
    const op = nextOp();
    if (!op) {
      // Empty, or only a held book change: saved, or "not saved" while a
      // refused write stands.
      settleIdle();
      return;
    }
    if (op.kind === "book") {
      op.payload ??= { sessionId: sessionRef.current.sessionId, visible: op.visible };
    } else if (!op.payload) {
      // The payload is read once, when the write is first sent, and then
      // frozen under its key: a retry resends exactly what was sent.
      const input = stepInput(op);
      if (input === null) {
        dequeue(op);
        void pump();
        return;
      }
      op.payload = input;
    }
    running.current = true;
    setSave((previous) => (previous.state === "saved" ? { ...previous, state: "saving" } : previous));
    try {
      if (op.kind === "book") {
        const result = await api.workbenchSetBook(op.payload!);
        dequeue(op);
        rejected.current.delete(BOOK_KEY);
        // A later change of the book is still on its way: keep showing it.
        if (!queue.current.some((queued) => queued.kind === "book")) commitSession(result.session);
        else setRecord(result.session.record);
      } else {
        const result = await api.workbenchSaveStep(op.payload!);
        dequeue(op);
        rejected.current.delete(op.key);
        commitSteps(updateLocal(stepsRef.current, op.key, { serverId: result.step.stepId }));
        setRecord(result.record);
        // "Saved" means the stored text is the text in the window: anything
        // typed since this write was sent goes in a new write of its own.
        const local = stepsRef.current.find((step) => step.key === op.key);
        if (local && !local.deleted && op.kind !== "delete" && local.body !== result.step.bodyMd && !hasUnsentWrite(op.key)) {
          queue.current.push({ kind: "edit", key: op.key, idem: newKey() });
        }
      }
      failures.current = 0;
      running.current = false;
      void pump();
    } catch (error) {
      running.current = false;
      const code = getCommandError(error)?.code ?? "";
      if (PERMANENT.has(code)) {
        // Refused for good: the text stays in the window and counts as not
        // saved until a later write of this step lands or it is deleted.
        dequeue(op);
        rejected.current.set(op.key, errorMessage(error));
        onErrorRef.current(errorMessage(error));
        void pump();
        return;
      }
      setSave((previous) => ({ ...previous, state: phaseForError(error) === "offline" ? "offline" : "retrying" }));
      settleWaiters(false);
      if (closed.current && failures.current >= RETRIES_AFTER_CLOSE) return;
      const delay = RETRY_DELAYS_MS[Math.min(failures.current, RETRY_DELAYS_MS.length - 1)];
      failures.current += 1;
      retryTimer.current = setTimeout(() => {
        retryTimer.current = null;
        void pump();
      }, delay);
    }
  }, [commitSession, commitSteps, dequeue, hasUnsentWrite, nextOp, settleIdle, settleWaiters, stepInput]);

  const enqueue = useCallback((op: Op) => {
    // An unsent write of the step already sends its newest text when it goes.
    if (op.kind === "edit" && hasUnsentWrite(op.key)) return;
    queue.current.push(op);
    void pump();
  }, [hasUnsentWrite, pump]);

  const queueEdit = useCallback((key: string) => {
    const step = stepsRef.current.find((candidate) => candidate.key === key);
    if (!step) return;
    const addQueued = queue.current.some((queued) => queued.kind === "add" && queued.key === key);
    if (step.serverId === null && !addQueued) enqueue({ kind: "add", key, idem: newKey() });
    else enqueue({ kind: "edit", key, idem: newKey() });
  }, [enqueue]);

  const flushEdits = useCallback(() => {
    for (const [key, timer] of editTimers.current) {
      clearTimeout(timer);
      queueEdit(key);
    }
    editTimers.current.clear();
  }, [queueEdit]);

  const setBody = useCallback((key: string, body: string) => {
    if (readOnly || frozenRef.current) return;
    commitSteps(updateLocal(stepsRef.current, key, { body }));
    setStarted(true);
    const timers = editTimers.current;
    const existing = timers.get(key);
    if (existing) clearTimeout(existing);
    timers.set(key, setTimeout(() => {
      timers.delete(key);
      queueEdit(key);
    }, EDIT_DEBOUNCE_MS));
  }, [commitSteps, readOnly, queueEdit]);

  const addStep = useCallback((afterKey: string | null, kind: WorkbenchStepKind = "step") => {
    const key = newKey();
    if (frozenRef.current) return key;
    let list = stepsRef.current;
    if (kind === "stuck") {
      // An empty step the learner never wrote in gives way to "I'm stuck".
      const unwritten = (step: LocalStep) =>
        step.kind === "step" && !step.deleted && step.serverId === null && !step.body.trim()
        && !queue.current.some((queued) => queued.key === step.key);
      while (list.length > 0 && unwritten(list[list.length - 1])) list = list.slice(0, -1);
    }
    commitSteps(insertAfter(list, afterKey, { key, kind }));
    if (kind === "stuck") {
      // "I'm stuck" is itself the learner's work, even before any text.
      setStarted(true);
      enqueue({ kind: "add", key, idem: newKey() });
    }
    return key;
  }, [commitSteps, enqueue]);

  const deleteStep = useCallback((key: string) => {
    if (frozenRef.current) return;
    const step = stepsRef.current.find((candidate) => candidate.key === key);
    if (!step) return;
    const timer = editTimers.current.get(key);
    if (timer) {
      clearTimeout(timer);
      editTimers.current.delete(key);
    }
    const saved = step.serverId !== null || queue.current.some((queued) => queued.kind === "add" && queued.key === key);
    if (!saved) {
      // Never saved: nothing to keep, so it simply goes (and a refusal with it).
      rejected.current.delete(key);
      commitSteps(stepsRef.current.filter((candidate) => candidate.key !== key));
      // A book change it held goes now (or the queue settles as saved).
      void pump();
      return;
    }
    commitSteps(deleteLocal(stepsRef.current, key));
    enqueue({ kind: "delete", key, idem: newKey() });
  }, [commitSteps, enqueue, settleIdle]);

  const undoDelete = useCallback((key: string) => {
    if (frozenRef.current) return;
    commitSteps(restoreLocal(stepsRef.current, key));
    enqueue({ kind: "restore", key, idem: newKey() });
  }, [commitSteps, enqueue]);

  const drained = useCallback(() => {
    // Nothing left to send (a held book change waits on a refusal): settled.
    if (!running.current && !retryTimer.current && nextOp() === undefined) return Promise.resolve(rejected.current.size === 0);
    if (retryTimer.current) return Promise.resolve(false);
    return new Promise<boolean>((resolve) => waiters.current.push(resolve));
  }, [nextOp]);

  /** Every change typed so far, saved, or a typed refusal naming why not. */
  const persist = useCallback(async (action: string) => {
    flushEdits();
    if (!(await drained())) throw notSavedError(firstRejection(), action);
  }, [drained, firstRejection, flushEdits]);

  const setBook = useCallback(async (visible: boolean) => {
    if (readOnly || frozenRef.current) return;
    // The text typed under the current visibility is saved before the change.
    flushEdits();
    commitSession({ ...sessionRef.current, sourceVisible: visible });
    enqueue({ kind: "book", key: BOOK_KEY, idem: newKey(), visible });
  }, [commitSession, enqueue, flushEdits, readOnly]);

  const leave = useCallback(async () => {
    flushEdits();
    try {
      await api.workbenchLeave({ sessionId: sessionRef.current.sessionId });
    } catch {
      // Leaving never fails for the learner: the problem stays open either way.
    }
  }, [flushEdits]);

  const abandon = useCallback(async () => {
    try {
      // "Your steps are kept": every one is saved before the problem closes.
      await persist("this problem was not set aside");
      const result = await api.workbenchAbandon({ sessionId: sessionRef.current.sessionId });
      commitSession(result.session, false);
      return result.session;
    } catch (error) {
      onErrorRef.current(errorMessage(error, "Couldn't set this problem aside."));
      return null;
    }
  }, [commitSession, persist]);

  const reopen = useCallback(async () => {
    try {
      const result = await api.workbenchReopen({ sessionId: sessionRef.current.sessionId });
      commitSession(result.session);
    } catch (error) {
      onErrorRef.current(errorMessage(error, "Couldn't reopen this problem."));
    }
  }, [commitSession]);

  const retryImport = useCallback(async () => {
    try {
      const result = await api.workbenchRetryImport({ sessionId: sessionRef.current.sessionId });
      commitSession(result.session);
    } catch (error) {
      onErrorRef.current(errorMessage(error, "Couldn't try the setup again."));
    }
  }, [commitSession]);

  const bind = useCallback(async (practiceItemId: string) => {
    try {
      const result = await api.workbenchBind({ sessionId: sessionRef.current.sessionId, practiceItemId });
      commitSession(result.session);
    } catch (error) {
      onErrorRef.current(errorMessage(error, "Couldn't choose that part."));
    }
  }, [commitSession]);

  const submit = useCallback(async (input: Omit<WorkbenchSubmitInput, "sessionId">) => {
    await persist("nothing was submitted");
    const result = await api.workbenchSubmit({ sessionId: sessionRef.current.sessionId, ...input });
    commitSession(result.session, false);
    return result;
  }, [commitSession, persist]);

  // A vault switch (review F8): editing pauses and every pending write lands
  // in the vault these steps belong to before the next one is selected; a
  // write that cannot land stops the switch, and editing resumes.
  const flushForTransition = useCallback(async () => {
    if (readOnly) return;
    await persist("the vault was not switched");
  }, [persist, readOnly]);
  useEffect(() => {
    if (readOnly) return undefined;
    return registerVaultDraft({
      freeze: () => {
        frozenRef.current = true;
        setFrozen(true);
      },
      flush: flushForTransition,
      resume: () => {
        frozenRef.current = false;
        setFrozen(false);
      },
    });
  }, [flushForTransition, readOnly]);
  // Closing the window waits for the steps too: React's cleanup does not
  // run before the window goes.
  const flushForClose = useCallback(async () => {
    if (readOnly) return;
    await persist("they may not be saved");
  }, [persist, readOnly]);
  const reportError = useCallback((message: string) => onErrorRef.current(message), []);
  useCloseWithFlush(flushForClose, reportError, "Could not save your steps before closing.");

  // Opening at once (UX S2): wait quietly for the import to bind the item.
  const waiting = !readOnly && session.status !== "submitted" && session.importStatus === "pending" && !session.parts;
  useEffect(() => {
    if (!waiting) return undefined;
    const timer = setInterval(() => {
      void api.workbenchRefreshImport({ sessionId: sessionRef.current.sessionId })
        .then((result) => {
          const next = result.session;
          const current = sessionRef.current;
          if (next.importStatus !== current.importStatus || next.practiceItemId !== current.practiceItemId || (next.parts?.length ?? 0) !== (current.parts?.length ?? 0)) {
            commitSession(next);
          }
        })
        .catch(() => {
          // A poll that fails polls again; the steps are unaffected.
        });
    }, 2000);
    return () => clearInterval(timer);
  }, [waiting, commitSession]);

  // Leaving the screen sends every resting edit; the queue finishes on its
  // own. While a vault switch holds these steps, everything was already
  // saved against their vault, and nothing may be sent to the next one.
  useEffect(() => () => {
    closed.current = true;
    if (frozenRef.current) {
      for (const timer of editTimers.current.values()) clearTimeout(timer);
      editTimers.current.clear();
      return;
    }
    for (const [key, timer] of editTimers.current) {
      clearTimeout(timer);
      queueEdit(key);
    }
    editTimers.current.clear();
  }, [queueEdit]);

  return {
    session, steps, record, save, started, frozen, setBody, addStep, deleteStep, undoDelete, flushEdits, drained,
    setBook, leave, abandon, reopen, retryImport, bind, submit,
  };
}
