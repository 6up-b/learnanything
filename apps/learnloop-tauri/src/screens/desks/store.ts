// One desk store per vault (spec §3.4, §3.5): the workspace the desks show, the outbox that persists it,
// and the reconciling of the two with the server. It outlives the mounted shell: leaving the desks and
// coming back finds the same store, so one client never has two outboxes allocating the same numbers,
// and changes queued before leaving are still sent.
//
// What the learner did is kept as intent (the ops of each queued batch). When a batch comes back with a
// conflict or is rejected for good, the store reads the server's state, rebases every queued op on it
// (re-stamping the versions it expects), and reports the changes that no longer apply, instead of
// dropping everything queued after the failure.
import type { DeskOpDto, DeskStateDto } from "../../api/dto";
import { EMPTY_WORKSPACE, OpRefusal, fromDeskState, restampOp, type Step, type Workspace } from "./model/workspace";
import { DeskOutbox, MemoryOutboxStore, type OutboxTransport } from "./outbox";
import type { Timers } from "./keys/router";

export interface DeskStoreTransport extends OutboxTransport {
  state(): Promise<DeskStateDto>;
}

export type DeskNotice =
  | { kind: "rejected"; message: string }
  | { kind: "conflict"; dropped: number; lost: number }
  | { kind: "offline"; message: string }
  | { kind: "load-failed"; message: string };

/** Ops are sent shortly after the last change, so a burst of moves goes out together. */
export const FLUSH_IDLE_MS = 250;

function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (error && typeof error === "object" && "message" in error) return String((error as { message: unknown }).message);
  return String(error);
}

export class DeskStore {
  ws: Workspace = EMPTY_WORKSPACE;
  loaded = false;
  private listeners = new Set<() => void>();
  private noticeListeners = new Set<(notice: DeskNotice) => void>();
  private flushTimer: unknown = null;
  private loading: Promise<DeskStateDto> | null = null;
  private reconciling: Promise<void> | null = null;
  readonly outbox: DeskOutbox;

  constructor(
    readonly clientId: string,
    private readonly transport: DeskStoreTransport,
    private readonly timers: Timers,
  ) {
    this.outbox = new DeskOutbox(clientId, transport, new MemoryOutboxStore());
  }

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  onNotice(listener: (notice: DeskNotice) => void): () => void {
    this.noticeListeners.add(listener);
    return () => this.noticeListeners.delete(listener);
  }

  getSnapshot = (): Workspace => this.ws;

  private emit(): void {
    for (const listener of [...this.listeners]) listener();
  }

  private notify(notice: DeskNotice): void {
    for (const listener of [...this.noticeListeners]) listener(notice);
  }

  /** Read the server's desks once (a second caller shares the read); later calls return at once. */
  async load(): Promise<DeskStateDto | null> {
    if (this.loaded) return null;
    if (!this.loading) {
      this.loading = this.transport.state().then((state) => {
        this.outbox.syncSeq(state);
        this.ws = fromDeskState(state);
        this.loaded = true;
        this.emit();
        return state;
      });
      this.loading.catch(() => {
        this.loading = null;
      });
    }
    return this.loading;
  }

  /** Apply a step at once and queue its ops. */
  commit(step: Step): void {
    this.ws = step.ws;
    this.emit();
    if (step.ops.length > 0) {
      this.outbox.enqueue(step.ops);
      this.scheduleFlush();
    }
  }

  private scheduleFlush(): void {
    if (this.flushTimer !== null) this.timers.clear(this.flushTimer);
    this.flushTimer = this.timers.set(() => {
      this.flushTimer = null;
      void this.flush();
    }, FLUSH_IDLE_MS);
  }

  /** Send what is queued; reconcile on a conflict or a rejection. Never runs while reconciling. */
  async flush(): Promise<void> {
    if (this.reconciling) await this.reconciling;
    const outcome = await this.outbox.flush();
    if (outcome.kind === "conflict") {
      const dropped = outcome.reply.results.filter((result) => result.status !== "ok").length;
      await this.reconcile((lost) => this.notify({ kind: "conflict", dropped, lost }));
    } else if (outcome.kind === "rejected") {
      this.notify({ kind: "rejected", message: outcome.message });
      await this.reconcile((lost) => (lost > 0 ? this.notify({ kind: "conflict", dropped: 0, lost }) : undefined));
    } else if (outcome.kind === "resync") {
      await this.reconcile(() => undefined, true);
    } else if (outcome.kind === "offline") {
      this.notify({ kind: "offline", message: outcome.message });
    }
  }

  /** The server's state, with every op still queued rebased on it. Ops that no longer apply there are
   * dropped and counted; undo offers for windows that are open there are withdrawn. */
  private reconcile(report: (lost: number) => void, resync = false): Promise<void> {
    if (this.reconciling) return this.reconciling;
    this.reconciling = (async () => {
      let state: DeskStateDto;
      try {
        state = await this.transport.state();
      } catch (error) {
        this.notify({ kind: "load-failed", message: errorText(error) });
        return;
      }
      // Read the queue only now: changes committed while the state was on its way are rebased too.
      const queued = this.outbox.queued();
      const head = state.serverSeq.find((entry) => entry.clientId === this.clientId)?.seq ?? 0;
      let ws: Workspace = { ...fromDeskState(state), closed: {} };
      for (const [deskId, entries] of Object.entries(this.ws.closed)) {
        const still = entries.filter((entry) => !ws.windows[entry.window.windowId] && ws.desks.some((desk) => desk.deskId === deskId));
        if (still.length) ws.closed[deskId] = still;
      }
      let lost = 0;
      const rebased: DeskOpDto[][] = [];
      for (const batch of resync ? [] : queued) {
        const ops: DeskOpDto[] = [];
        for (const op of batch.ops) {
          try {
            const next = restampOp(ws, op);
            ws = next.ws;
            ops.push(next.op);
          } catch (error) {
            if (!(error instanceof OpRefusal)) throw error;
            lost += 1;
          }
        }
        rebased.push(ops);
      }
      if (resync) lost += queued.reduce((count, batch) => count + batch.ops.length, 0);
      this.outbox.requeue(rebased, head + 1);
      this.ws = ws;
      this.emit();
      report(lost);
    })().finally(() => {
      this.reconciling = null;
      if (this.outbox.pending > 0) this.scheduleFlush();
    });
    return this.reconciling;
  }
}

const STORES = new WeakMap<object, Map<string, DeskStore>>();

/** The one store for this vault (and transport): created on first use, kept across mounts. */
export function deskStoreFor(vaultKey: string, transport: DeskStoreTransport, timers: Timers, clientId: () => string): DeskStore {
  let byVault = STORES.get(transport);
  if (!byVault) {
    byVault = new Map();
    STORES.set(transport, byVault);
  }
  let store = byVault.get(vaultKey);
  if (!store) {
    store = new DeskStore(clientId(), transport, timers);
    byVault.set(vaultKey, store);
  }
  return store;
}
