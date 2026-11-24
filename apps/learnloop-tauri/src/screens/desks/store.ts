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
import type { DeskOpDto, DeskStateDto, PadBlockSubmissionDto, PadOpDto, PadViewDto, WriteOpResultDto } from "../../api/dto";
import { EMPTY_WORKSPACE, OpRefusal, fromDeskState, restampOp, type Step, type Workspace } from "./model/workspace";
import { DeskOutbox, MemoryOutboxStore, type BatchBody, type InkEraseBody, type InkSaveBody, type OutboxTransport, type FlushOutcome } from "./outbox";
import { PadOpRefusal, applyPadOp, fromPadView, restampPadOp, type KeptBothRedirects, type Pads } from "./pads/model";
import type { Timers } from "./keys/router";

export interface DeskStoreTransport extends OutboxTransport {
  state(): Promise<DeskStateDto>;
  /** `pad.get` (absent where no pad is shown). */
  padGet?(input: { padId: string }): Promise<PadViewDto>;
}

export type DeskNotice =
  | { kind: "rejected"; message: string }
  | { kind: "conflict"; dropped: number; lost: number }
  /** Words typed over a version another device had changed: kept as their own block beside the newer ones. */
  | { kind: "kept-both"; count: number }
  | { kind: "offline"; message: string }
  | { kind: "load-failed"; message: string };

/** Ops are sent shortly after the last change, so a burst of moves goes out together. */
export const FLUSH_IDLE_MS = 250;

/** Where each kept-apart edit of a batch went: the version the client made → the block and version it landed in. */
function keptBothRedirects(batch: { pad?: { ops: PadOpDto[] } }, results: WriteOpResultDto[]): KeptBothRedirects {
  const redirects: KeptBothRedirects = new Map();
  batch.pad?.ops.forEach((op, index) => {
    const result = results[index];
    if (op.op === "edit_block" && op.versionId && result?.status === "ok" && result.keptBoth) {
      redirects.set(op.versionId, { blockId: result.keptBoth.blockId, versionId: result.keptBoth.headVersionId });
    }
  });
  return redirects;
}

/** The mark on words kept beside newer ones (what the learner reads on the block). */
function keptLabel(now: string): string {
  const at = new Date(now);
  const time = Number.isNaN(at.getTime()) ? "" : ` · ${at.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
  return `your words, written over an older version${time}`;
}

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
        if (!this.pads[padId]) {
          this.pads = { ...this.pads, [padId]: fromPadView(view) };
          this.changed([padId]);
        }
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

  /** A pad a desk op is creating (the running pad ensure_running_pad makes): known here at once, empty, so its
   * window shows it before the server has answered (nothing is queued for it: the desk op creates it). */
  noteCreatedPad(padId: string, kind: "running" | "named", title: string, homeDeskId: string | null, now: string = new Date().toISOString()): void {
    if (this.pads[padId]) return;
    this.pads = applyPadOp(this.pads, padId, { op: "create_pad", kind, title, homeDeskId }, now);
    this.changed([padId]);
    this.emitPads();
  }

  /** A submission the server recorded (its "submitted · …" tag), shown at once without reading the pad again. */
  noteSubmission(padId: string, blockId: string, submission: PadBlockSubmissionDto): void {
    const state = this.pads[padId];
    if (!state) return;
    const blocks = state.blocks.map((block) => (block.blockId === blockId ? { ...block, submissions: [...block.submissions.map((each) => ({ ...each, current: false })), submission] } : block));
    this.pads = { ...this.pads, [padId]: { ...state, blocks } };
    this.changed([padId]);
    this.emitPads();
  }

  /** Apply ops to a pad at once and queue them; a refused op is not applied and its refusal is returned. */
  commitPad(padId: string, ops: PadOpDto[], now: string = new Date().toISOString()): PadOpRefusal | null {
    // Every edit says what to do if its head has moved on elsewhere: keep the newer words and land these as their
    // own block (the server's conflict policy), never overwrite them.
    ops = ops.map((op) => (op.op === "edit_block" && !op.keepBoth
      ? { ...op, keepBoth: { blockId: this.mintKept(), ...(op.versionId ? { versionId: `${op.versionId}.kb` } : {}), label: keptLabel(now) } }
      : op));
    let pads = this.pads;
    try {
      for (const op of ops) pads = applyPadOp(pads, padId, op, now);
    } catch (error) {
      if (error instanceof PadOpRefusal) return error;
      if (error instanceof Error) return new PadOpRefusal("conflict", error.message);
      throw error;
    }
    this.pads = pads;
    this.changed([padId]);
    this.emitPads();
    this.outbox.enqueuePad(padId, ops);
    this.scheduleFlush();
    return null;
  }

  /** Read a pad again from the server (a reading LearnLoop wrote into one of its blocks moved that block's head),
   * once every queued write is acknowledged; a pad with changes still queued keeps what the client has. */
  async refreshPad(padId: string): Promise<void> {
    await this.settled();
    if (!this.transport.padGet || this.outbox.queued().some((batch) => batch.pad?.padId === padId)) return;
    // A change made here while the read was out (even one acknowledged before it answered) is newer than what
    // the read saw: the read is then dropped, not laid over it.
    const before = this.padChanges.get(padId) ?? 0;
    try {
      const view = await this.transport.padGet({ padId });
      if (this.outbox.queued().some((batch) => batch.pad?.padId === padId) || (this.padChanges.get(padId) ?? 0) !== before) return;
      this.pads = { ...this.pads, [padId]: fromPadView(view) };
      this.emitPads();
    } catch {
      // The pad keeps what the client has; the next change reconciles it.
    }
  }

  /** Queue one ink save (pen and ink, RD8a): sent after the batches before it, retried until the server's
   * receipt; a resent ink id with the same strokes is a no-op on the server. */
  commitInk(ink: InkSaveBody): void {
    this.outbox.enqueueInk(ink);
    this.scheduleFlush();
  }

  /** Queue one ink erase (an annotation's or a reading's ink), in the same sequence. */
  commitInkErase(inkErase: InkEraseBody): void {
    this.outbox.enqueueInkErase(inkErase);
    this.scheduleFlush();
  }

  /** Each pad's local changes, counted (a pad read that started before one is older than it). */
  private padChanges = new Map<string, number>();

  private changed(padIds: Iterable<string>): void {
    for (const padId of padIds) this.padChanges.set(padId, (this.padChanges.get(padId) ?? 0) + 1);
  }

  private keptCount = 0;

  /** A block id for an edit's words, should they have to be kept apart. */
  private mintKept(): string {
    this.keptCount += 1;
    return `${this.clientId}.kb.${Date.now().toString(36)}.${this.keptCount}`;
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
    return this.flushReporting().then(() => undefined);
  }

  private flushReporting(): Promise<FlushOutcome["kind"]> {
    const run = this.flushChain.then(() => this.flushOnce());
    this.flushChain = run.then(() => undefined, () => undefined);
    return run;
  }

  /** Every desk (and pad) write queued so far, acknowledged by the server: sent now, not at the idle flush.
   * "unsaved" when they cannot be sent (offline) or keep failing; a companion question waits on this, because
   * the sidecar reads the desk's focus and windows when it records the question. */
  async settled(): Promise<"saved" | "unsaved"> {
    for (let pass = 0; pass < 4; pass += 1) {
      if (this.reconciling) await this.reconciling;
      if (this.outbox.pending === 0) return "saved";
      if (this.flushTimer !== null) {
        this.timers.clear(this.flushTimer);
        this.flushTimer = null;
      }
      const kind = await this.flushReporting();
      if (kind === "offline") return "unsaved";
    }
    if (this.reconciling) await this.reconciling;
    return this.outbox.pending === 0 ? "saved" : "unsaved";
  }

  private async flushOnce(): Promise<FlushOutcome["kind"]> {
    if (this.reconciling) await this.reconciling;
    const outcome = await this.outbox.flush();
    if (outcome.kind === "conflict") {
      // The server's state wins for the ops that conflicted: a desk op takes the server's, and a stale pad op (a
      // remove, move or lift of a block changed elsewhere) is dropped and said, never retried onto the newer
      // words. Edits do not conflict: their words are kept beside the newer ones (keepBoth).
      const redirects = keptBothRedirects(outcome.batch, outcome.reply.results);
      const kept = redirects.size;
      const dropped = outcome.reply.results.filter((result) => result.status !== "ok").length;
      await this.reconcile((lost) => this.notify({ kind: "conflict", dropped, lost }), false, null, redirects);
      if (kept) this.notify({ kind: "kept-both", count: kept });
    } else if (outcome.kind === "kept-both") {
      // The edits' words landed beside the newer ones: read the pad again, and rebase what was typed on top.
      const redirects = keptBothRedirects(outcome.batch, outcome.reply.results);
      // Counted now: the rebase below adds the queued edits it moves into the kept blocks.
      const kept = redirects.size;
      await this.reconcile((lost) => (lost > 0 ? this.notify({ kind: "conflict", dropped: 0, lost }) : undefined), false, null, redirects);
      this.notify({ kind: "kept-both", count: kept });
    } else if (outcome.kind === "rejected") {
      this.notify({ kind: "rejected", message: outcome.message });
      await this.reconcile((lost) => (lost > 0 ? this.notify({ kind: "conflict", dropped: 0, lost }) : undefined));
    } else if (outcome.kind === "resync") {
      await this.reconcile(() => undefined, true);
    } else if (outcome.kind === "offline") {
      this.notify({ kind: "offline", message: outcome.message });
    }
    return outcome.kind;
  }

  /** The server's state, with every op still queued rebased on it. Ops that no longer apply there are
   * dropped and counted; undo offers for windows that are open there are withdrawn. */
  private reconcile(report: (lost: number) => void, resync = false, first: BatchBody | null = null, redirects: KeptBothRedirects = new Map()): Promise<void> {
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
      const snapshot = this.outbox.queued();
      const taken = new Set(snapshot.map((batch) => batch.seq));
      const queued: BatchBody[] = [...(first ? [first] : []), ...snapshot];
      const head = state.serverSeq.find((entry) => entry.clientId === this.clientId)?.seq ?? 0;
      let ws: Workspace = { ...fromDeskState(state), closed: {} };
      for (const [deskId, entries] of Object.entries(this.ws.closed)) {
        const still = entries.filter((entry) => !ws.windows[entry.window.windowId] && ws.desks.some((desk) => desk.deskId === deskId));
        if (still.length) ws.closed[deskId] = still;
      }
      // The pads shown are read again, so queued pad ops rebase on the server's heads.
      let pads: Pads = {};
      const padIds = [...new Set([...Object.keys(this.pads), ...queued.flatMap((batch) => (batch.pad ? [batch.pad.padId] : []))])];
      const read = async (ids: string[]) => {
        const reads = await Promise.all(ids.map((padId) => this.transport.padGet!({ padId }).then((view) => [padId, view] as const, () => [padId, null] as const)));
        for (const [padId, view] of reads) if (view) pads[padId] = fromPadView(view);
      };
      if (this.transport.padGet) await read(padIds);
      else pads = { ...this.pads };
      // Batches queued while the pads were read (the learner kept writing) join the rebase, after the ones
      // taken first; a pad they name that was not read yet is read too. Nothing is awaited after the last look,
      // so no commit can land between it and the requeue below.
      for (;;) {
        const tail = this.outbox.queued().filter((batch) => !taken.has(batch.seq));
        if (tail.length === 0) break;
        for (const batch of tail) taken.add(batch.seq);
        queued.push(...tail);
        const unread = [...new Set(tail.flatMap((batch) => (batch.pad ? [batch.pad.padId] : [])))].filter((padId) => !padIds.includes(padId));
        padIds.push(...unread);
        if (unread.length && this.transport.padGet) await read(unread);
        else if (unread.length) for (const padId of unread) if (this.pads[padId]) pads[padId] = this.pads[padId];
      }
      const now = new Date().toISOString();
      let lost = 0;
      const rebased: BatchBody[] = [];
      for (const batch of resync ? [] : queued) {
        if (batch.inkErase) {
          rebased.push({ ops: [], inkErase: batch.inkErase });
          continue;
        }
        if (batch.ink) {
          // An ink save names no head: it goes again as it was (its ink id makes a resend a no-op).
          rebased.push({ ops: [], ink: batch.ink });
          continue;
        }
        if (batch.pad) {
          const padOps: PadOpDto[] = [];
          for (const op of batch.pad.ops) {
            try {
              const next = restampPadOp(pads, batch.pad.padId, op, now, redirects);
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
      if (resync) lost += queued.reduce((count, batch) => count + (batch.ink || batch.inkErase ? 1 : batch.pad ? batch.pad.ops.length : batch.ops.length), 0);
      this.outbox.requeue(rebased, head + 1);
      this.ws = ws;
      // A pad that could not be read again keeps what the client had.
      for (const padId of padIds) if (!pads[padId] && this.pads[padId]) pads[padId] = this.pads[padId];
      this.pads = pads;
      this.changed(padIds);
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
