// One desk store per vault (spec §3.4, §3.5): the workspace the desks show, the outbox that persists it,
// and the reconciling of the two with the server. It outlives the mounted shell: leaving the desks and
// coming back finds the same store, so one client never has two outboxes allocating the same numbers,
// and changes queued before leaving are still sent.
//
// What the learner did is kept as intent (the ops of each queued batch). When a batch comes back with a
// conflict or is rejected for good, the store reads the server's state, rebases every queued op on it
// (re-stamping the versions it expects), and reports the changes that no longer apply, instead of
// dropping everything queued after the failure.
//
// Pads live here too (spec §10.5): a pad is read once (`pad.get`) and then changed locally op by op through the
// pad model, its batches queued in the same outbox (one numbering a client), reconciled the same way.
import type { DeskOpDto, DeskStateDto, PadBlockSubmissionDto, PadOpDto, PadViewDto } from "../../api/dto";
import { EMPTY_WORKSPACE, OpRefusal, fromDeskState, restampOp, type Step, type Workspace } from "./model/workspace";
import { DeskOutbox, MemoryOutboxStore, type BatchBody, type OutboxTransport } from "./outbox";
import { PadOpRefusal, applyPadOp, fromPadView, restampPadOp, type Pads } from "./pads/model";
import type { Timers } from "./keys/router";

export interface DeskStoreTransport extends OutboxTransport {
  state(): Promise<DeskStateDto>;
  /** `pad.get` (absent where no pad is shown). */
  padGet?(input: { padId: string }): Promise<PadViewDto>;
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
  /** The pads read so far, as the client shows them (the server's, with what is queued applied). */
  pads: Pads = {};
  private padReads = new Map<string, Promise<void>>();
  private padFailures: Record<string, string> = {};
  private padVersion = 0;

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

  /** Changes with every pad change (a useSyncExternalStore snapshot). */
  getPadVersion = (): number => this.padVersion;

  padFailure(padId: string): string | null {
    return this.padFailures[padId] ?? null;
  }

  private emitPads(): void {
    this.padVersion += 1;
    this.emit();
  }

  /** Read a pad once (a second caller shares the read). */
  loadPad(padId: string): Promise<void> {
    if (this.pads[padId]) return Promise.resolve();
    const known = this.padReads.get(padId);
    if (known) return known;
    if (!this.transport.padGet) return Promise.resolve();
    const read = this.transport.padGet({ padId }).then(
      (view) => {
        // Ops queued before the read landed (on a pad created here) stay applied on top.
        if (!this.pads[padId]) this.pads = { ...this.pads, [padId]: fromPadView(view) };
        delete this.padFailures[padId];
        this.emitPads();
      },
      (error: unknown) => {
        this.padReads.delete(padId);
        this.padFailures = { ...this.padFailures, [padId]: errorText(error) };
        this.emitPads();
      },
    );
    this.padReads.set(padId, read);
    return read;
  }

  /** A submission the server recorded (its "submitted · …" tag), shown at once without reading the pad again. */
  noteSubmission(padId: string, blockId: string, submission: PadBlockSubmissionDto): void {
    const state = this.pads[padId];
    if (!state) return;
    const blocks = state.blocks.map((block) => (block.blockId === blockId ? { ...block, submissions: [...block.submissions.map((each) => ({ ...each, current: false })), submission] } : block));
    this.pads = { ...this.pads, [padId]: { ...state, blocks } };
    this.emitPads();
  }

  /** Apply ops to a pad at once and queue them; a refused op is not applied and its refusal is returned. */
  commitPad(padId: string, ops: PadOpDto[], now: string = new Date().toISOString()): PadOpRefusal | null {
    let pads = this.pads;
    try {
      for (const op of ops) pads = applyPadOp(pads, padId, op, now);
    } catch (error) {
      if (error instanceof PadOpRefusal) return error;
      if (error instanceof Error) return new PadOpRefusal("conflict", error.message);
      throw error;
    }
    this.pads = pads;
    this.emitPads();
    this.outbox.enqueuePad(padId, ops);
    this.scheduleFlush();
    return null;
  }

  private emit(): void {
    for (const listener of [...this.listeners]) listener();
  }

  private notify(notice: DeskNotice): void {
    for (const listener of [...this.noticeListeners]) listener(notice);
  }

  /** Read the server's desks once (a second caller shares the read). Once loaded (the desks shown again
   * after leaving them), the server's state is read again and what is still queued is rebased on it. */
  async load(): Promise<DeskStateDto | null> {
    if (this.loaded) {
      await this.reconcile((lost) => (lost > 0 ? this.notify({ kind: "conflict", dropped: 0, lost }) : undefined));
      return null;
    }
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

  private flushChain: Promise<void> = Promise.resolve();

  /** Send what is queued; reconcile on a conflict or a rejection. One flush at a time, each with its
   * reconcile: a second flush started while the first's conflict is being reconciled would otherwise send
   * the batches queued after the conflict with heads that no longer hold, before they are rebased. */
  flush(): Promise<void> {
    const run = this.flushChain.then(() => this.flushOnce());
    this.flushChain = run.catch(() => undefined);
    return run;
  }

  private async flushOnce(): Promise<void> {
    if (this.reconciling) await this.reconciling;
    const outcome = await this.outbox.flush();
    if (outcome.kind === "conflict") {
      // A pad op that met a newer head is the learner's words: it is rebased with the queue, not dropped (the
      // other device's version stays in the block's history). A desk op that conflicted takes the server's.
      const pad = outcome.batch.pad;
      const carried = pad ? pad.ops.filter((_op, index) => outcome.reply.results[index]?.status === "conflict") : [];
      const dropped = outcome.reply.results.filter((result) => result.status !== "ok").length - carried.length;
      await this.reconcile((lost) => this.notify({ kind: "conflict", dropped, lost }), false, pad && carried.length ? { ops: [], pad: { padId: pad.padId, ops: carried } } : null);
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
  private reconcile(report: (lost: number) => void, resync = false, first: BatchBody | null = null): Promise<void> {
    if (this.reconciling) return this.reconciling;
    this.reconciling = (async () => {
      // A batch on its way finishes first: the state read below then includes it.
      await this.outbox.idle();
      let state: DeskStateDto;
      try {
        state = await this.transport.state();
      } catch (error) {
        this.notify({ kind: "load-failed", message: errorText(error) });
        return;
      }
      // Read the queue only now: changes committed while the state was on its way are rebased too.
      const queued: BatchBody[] = [...(first ? [first] : []), ...this.outbox.queued()];
      const head = state.serverSeq.find((entry) => entry.clientId === this.clientId)?.seq ?? 0;
      let ws: Workspace = { ...fromDeskState(state), closed: {} };
      for (const [deskId, entries] of Object.entries(this.ws.closed)) {
        const still = entries.filter((entry) => !ws.windows[entry.window.windowId] && ws.desks.some((desk) => desk.deskId === deskId));
        if (still.length) ws.closed[deskId] = still;
      }
      // The pads shown are read again, so queued pad ops rebase on the server's heads.
      let pads: Pads = {};
      const padIds = [...new Set([...Object.keys(this.pads), ...queued.flatMap((batch) => (batch.pad ? [batch.pad.padId] : []))])];
      if (this.transport.padGet) {
        const reads = await Promise.all(padIds.map((padId) => this.transport.padGet!({ padId }).then((view) => [padId, view] as const, () => [padId, null] as const)));
        for (const [padId, view] of reads) if (view) pads[padId] = fromPadView(view);
      } else {
        pads = { ...this.pads };
      }
      const now = new Date().toISOString();
      let lost = 0;
      const rebased: BatchBody[] = [];
      for (const batch of resync ? [] : queued) {
        if (batch.pad) {
          const padOps: PadOpDto[] = [];
          for (const op of batch.pad.ops) {
            try {
              const next = restampPadOp(pads, batch.pad.padId, op, now);
              pads = next.pads;
              padOps.push(next.op);
            } catch (error) {
              if (!(error instanceof PadOpRefusal)) throw error;
              lost += 1;
            }
          }
          rebased.push({ ops: [], pad: { padId: batch.pad.padId, ops: padOps } });
          continue;
        }
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
        rebased.push({ ops });
      }
      if (resync) lost += queued.reduce((count, batch) => count + (batch.pad ? batch.pad.ops.length : batch.ops.length), 0);
      this.outbox.requeue(rebased, head + 1);
      this.ws = ws;
      // A pad that could not be read again keeps what the client had.
      for (const padId of padIds) if (!pads[padId] && this.pads[padId]) pads[padId] = this.pads[padId];
      this.pads = pads;
      this.padVersion += 1;
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
