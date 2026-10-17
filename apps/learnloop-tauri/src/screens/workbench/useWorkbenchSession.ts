// Reader workbench RW2a: one workbench session's state and its write queue
// (spec §5.1 "saving and resuming"; UX §5.3).
//
// Every change to the work is saved as it is typed, modelled on the practice
// screen's draft checkpoints: a per-step debounce, then one serial queue. Each
// write carries its own idempotency key, kept across retries, so a retried
// write is answered from the row it wrote and nothing is saved twice. A write
// reads the step's text when it runs, so a queue that fell behind sends the
// newest text. A failing write keeps the text in the window and retries; a
// sidecar that is down keeps the steps here until it is back. Nothing a
// write or a poll returns moves focus (W12).
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
import { errorMessage, getCommandError } from "../../errors";
import { phaseForError } from "../reader/ModelActionState";
import {
  deleteLocal,
  fromServer,
  insertAfter,
  restoreLocal,
  updateLocal,
  type LocalStep,
  type SaveState,
} from "./stepModel";

/** How long a step rests before its text is saved. */
export const EDIT_DEBOUNCE_MS = 600;
const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000];
/** Retries a queue keeps making after the workbench closed (then it stops). */
const RETRIES_AFTER_CLOSE = 5;
/** Refusals a retry cannot fix: the write is dropped and the learner told. */
const PERMANENT = new Set(["validation_error", "not_found", "not_open", "already_submitted", "workbench_disabled"]);

type Op =
  | { kind: "add"; key: string; idem: string }
  | { kind: "edit"; key: string; idem: string }
  | { kind: "delete"; key: string; idem: string }
  | { kind: "restore"; key: string; idem: string };

function newKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `k${Date.now()}${Math.random()}`;
}

export interface WorkbenchSessionControls {
  session: WorkbenchSessionDto;
  steps: LocalStep[];
  record: WorkbenchRecordDto;
  save: { state: SaveState; savedAt: string | null };
  /** Something was written on this visit (the book line gives way). */
  started: boolean;
  setBody: (key: string, body: string) => void;
  /** A new step after `afterKey` (or at the end); returns its key. */
  addStep: (afterKey: string | null, kind?: WorkbenchStepKind) => string;
  deleteStep: (key: string) => void;
  undoDelete: (key: string) => void;
  /** Send every resting edit now. */
  flushEdits: () => void;
  /** Resolves true once every write has landed, false when one is failing. */
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
  const [session, setSessionState] = useState(initial);
  const [record, setRecord] = useState(initial.record);
  const [steps, setStepsState] = useState<LocalStep[]>(() => {
    const local = fromServer(initial.steps.filter((step) => !step.deleted));
    // An empty problem opens on its first (empty) step: "1 › _" (UX W8).
    return local.length === 0 && !options.readOnly ? [{ key: newKey(), serverId: null, kind: "step", body: "", deleted: false, versions: [] }] : local;
  });
  const [save, setSave] = useState<{ state: SaveState; savedAt: string | null }>({ state: "saved", savedAt: initial.updatedAt });
  const [started, setStarted] = useState(() => initial.steps.length > 0);

  const sessionRef = useRef(session);
  const stepsRef = useRef(steps);
  const queue = useRef<Op[]>([]);
  const running = useRef(false);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const failures = useRef(0);
  const closed = useRef(false);
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

  const settleWaiters = useCallback((ok: boolean) => {
    const pending = waiters.current;
    waiters.current = [];
    for (const resolve of pending) resolve(ok);
  }, []);

  const inputFor = useCallback((op: Op): WorkbenchSaveStepInput | null => {
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

  const pump = useCallback(async () => {
    if (running.current || retryTimer.current) return;
    const op = queue.current[0];
    if (!op) {
      settleWaiters(true);
      return;
    }
    const input = inputFor(op);
    if (input === null) {
      queue.current.shift();
      void pump();
      return;
    }
    running.current = true;
    setSave((previous) => (previous.state === "saved" ? { ...previous, state: "saving" } : previous));
    try {
      const result = await api.workbenchSaveStep(input);
      queue.current.shift();
      failures.current = 0;
      commitSteps(updateLocal(stepsRef.current, op.key, { serverId: result.step.stepId }));
      setRecord(result.record);
      running.current = false;
      if (queue.current.length === 0) {
        // "saved · just now" counts from when this window heard back (the
        // sidecar's clock may differ from this one).
        setSave({ state: "saved", savedAt: new Date().toISOString() });
        settleWaiters(true);
      } else {
        void pump();
      }
    } catch (error) {
      running.current = false;
      const code = getCommandError(error)?.code ?? "";
      if (PERMANENT.has(code)) {
        queue.current.shift();
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
  }, [commitSteps, inputFor, settleWaiters]);

  const enqueue = useCallback((op: Op) => {
    // One resting edit per step is enough: it sends the newest text when it runs.
    if (op.kind === "edit" && queue.current.some((queued, index) => queued.kind === "edit" && queued.key === op.key && !(index === 0 && running.current))) {
      return;
    }
    queue.current.push(op);
    void pump();
  }, [pump]);

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
    if (options.readOnly) return;
    commitSteps(updateLocal(stepsRef.current, key, { body }));
    setStarted(true);
    const timers = editTimers.current;
    const existing = timers.get(key);
    if (existing) clearTimeout(existing);
    timers.set(key, setTimeout(() => {
      timers.delete(key);
      queueEdit(key);
    }, EDIT_DEBOUNCE_MS));
  }, [commitSteps, options.readOnly, queueEdit]);

  const addStep = useCallback((afterKey: string | null, kind: WorkbenchStepKind = "step") => {
    const key = newKey();
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
    const step = stepsRef.current.find((candidate) => candidate.key === key);
    if (!step) return;
    const timer = editTimers.current.get(key);
    if (timer) {
      clearTimeout(timer);
      editTimers.current.delete(key);
    }
    const saved = step.serverId !== null || queue.current.some((queued) => queued.kind === "add" && queued.key === key);
    if (!saved) {
      // Never saved: nothing to keep, so it simply goes.
      commitSteps(stepsRef.current.filter((candidate) => candidate.key !== key));
      return;
    }
    commitSteps(deleteLocal(stepsRef.current, key));
    enqueue({ kind: "delete", key, idem: newKey() });
  }, [commitSteps, enqueue]);

  const undoDelete = useCallback((key: string) => {
    commitSteps(restoreLocal(stepsRef.current, key));
    enqueue({ kind: "restore", key, idem: newKey() });
  }, [commitSteps, enqueue]);

  const drained = useCallback(() => {
    if (!running.current && !retryTimer.current && queue.current.length === 0) return Promise.resolve(true);
    if (retryTimer.current) return Promise.resolve(false);
    return new Promise<boolean>((resolve) => waiters.current.push(resolve));
  }, []);

  const setBook = useCallback(async (visible: boolean) => {
    try {
      const result = await api.workbenchSetBook({ sessionId: sessionRef.current.sessionId, visible });
      commitSession(result.session);
    } catch (error) {
      onErrorRef.current(errorMessage(error, "Couldn't change the book's visibility."));
    }
  }, [commitSession]);

  const leave = useCallback(async () => {
    flushEdits();
    try {
      await api.workbenchLeave({ sessionId: sessionRef.current.sessionId });
    } catch {
      // Leaving never fails for the learner: the problem stays open either way.
    }
  }, [flushEdits]);

  const abandon = useCallback(async () => {
    flushEdits();
    try {
      const result = await api.workbenchAbandon({ sessionId: sessionRef.current.sessionId });
      commitSession(result.session, false);
      return result.session;
    } catch (error) {
      onErrorRef.current(errorMessage(error, "Couldn't set this problem aside."));
      return null;
    }
  }, [commitSession, flushEdits]);

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
    flushEdits();
    const ok = await drained();
    if (!ok) throw { code: "not_saved", message: "Your latest steps are not saved yet, so nothing was submitted." };
    const result = await api.workbenchSubmit({ sessionId: sessionRef.current.sessionId, ...input });
    commitSession(result.session, false);
    return result;
  }, [commitSession, drained, flushEdits]);

  // Opening at once (UX S2): wait quietly for the import to bind the item.
  const waiting = !options.readOnly && session.status !== "submitted" && session.importStatus === "pending" && !session.parts;
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

  // Leaving the screen sends every resting edit; the queue finishes on its own.
  useEffect(() => () => {
    closed.current = true;
    for (const [key, timer] of editTimers.current) {
      clearTimeout(timer);
      queueEdit(key);
    }
    editTimers.current.clear();
  }, [queueEdit]);

  return {
    session, steps, record, save, started, setBody, addStep, deleteStep, undoDelete, flushEdits, drained,
    setBook, leave, abandon, reopen, retryImport, bind, submit,
  };
}
