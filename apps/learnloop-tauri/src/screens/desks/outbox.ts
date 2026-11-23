// The client's write outbox for desk and pad ops (spec §3.4, §3.5): batches numbered by one `seq` per client
// (desk batches and pad batches share it, as the server keeps one sequence a client), sent in order, each kept
// until the server's receipt for its `seq` comes back.
//
// This is the in-memory outbox. The durable local store (IndexedDB, or a SQLite file through a Rust
// command) is chosen by the RD-spike, so everything here sits behind `OutboxStore`, which that store
// replaces; until then an op queued and not yet acknowledged is lost if the app closes, and the desks
// say nothing is saved on this device. A conflict (a stale head) takes the server's state, as §3.5
// says for moves and pairs: the shell reloads `desk.state` and re-renders.
import type { DeskApplyDto, DeskApplyInput, DeskOpDto, DeskStateDto, InkSaveDto, InkSaveInput, PadApplyDto, PadApplyInput, PadOpDto } from "../../api/dto";

/** One ink save (spec §10.10, RD8a): it shares the client's numbering with desk and pad batches (one outbox). */
export type InkSaveBody = Omit<InkSaveInput, "clientId" | "seq">;

/** One batch: desk ops, or (with `pad`) ops on one pad sent by `pad.apply`, or (with `ink`) one `ink.save`. */
export interface Batch {
  seq: number;
  ops: DeskOpDto[];
  pad?: { padId: string; ops: PadOpDto[] };
  ink?: InkSaveBody;
}

/** What a batch carries, before it has a number. */
export type BatchBody = { ops: DeskOpDto[]; pad?: { padId: string; ops: PadOpDto[] }; ink?: InkSaveBody };

function emptyBody(body: BatchBody): boolean {
  if (body.ink) return false;
  return body.pad ? body.pad.ops.length === 0 : body.ops.length === 0;
}

/** Where unacknowledged batches live. The RD-spike's durable store implements this same interface. */
export interface OutboxStore {
  readonly durable: boolean;
  load(): Batch[];
  put(batch: Batch): void;
  remove(seq: number): void;
}

export class MemoryOutboxStore implements OutboxStore {
  readonly durable = false;
  private batches = new Map<number, Batch>();

  load(): Batch[] {
    return [...this.batches.values()].sort((a, b) => a.seq - b.seq);
  }

  put(batch: Batch): void {
    this.batches.set(batch.seq, batch);
  }

  remove(seq: number): void {
    this.batches.delete(seq);
  }
}

export interface OutboxTransport {
  apply(input: DeskApplyInput): Promise<DeskApplyDto>;
  /** `pad.apply` (absent where no pad is written, as in the desks' early tests). */
  applyPad?(input: PadApplyInput): Promise<PadApplyDto>;
  /** `ink.save` (absent where no ink is written). */
  applyInk?(input: InkSaveInput): Promise<InkSaveDto>;
}

export type FlushOutcome =
  | { kind: "idle" }
  | { kind: "applied"; reply: DeskApplyDto | PadApplyDto | InkSaveDto }
  /** At least one op of `batch` hit a stale head or was refused: the server's state wins for those ops.
   * The batches queued after it stay queued, to be rebased on the server's state (`requeue`). */
  | { kind: "conflict"; reply: DeskApplyDto | PadApplyDto | InkSaveDto; batch: Batch }
  /** The server refused the whole batch for good (its request is invalid, so it will never apply): it is
   * dropped, and the batches after it stay queued, to be rebased. Never retried. */
  | { kind: "rejected"; message: string; batch: Batch }
  /** The batch applied, and an edit in it met a newer head: the server kept that head and put the edit's words
   * in a block of their own. The batches after it may build on the version the client thought it made: they wait
   * to be rebased onto where the words went. */
  | { kind: "kept-both"; reply: PadApplyDto; batch: Batch }
  /** The server refused the batch number (a gap or a reuse): resynchronise the sequence and reload. */
  | { kind: "resync"; message: string }
  /** The sidecar could not be reached: the batch stays, and is sent again on the next flush. */
  | { kind: "offline"; message: string };

/** Errors that mean the request itself is wrong: sending it again can never succeed. Anything else
 * (an unreachable or restarting sidecar, a busy database) is a transport failure and is retried. */
const PERMANENT_REFUSALS = new Set(["validation_error", "stale_sidecar_schema"]);

export function isPermanentRefusal(code: string): boolean {
  return PERMANENT_REFUSALS.has(code);
}

function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

/** A stable id for this installation and vault, kept per machine. The server keeps each client's
 * last applied `seq`, so a client that comes back continues where it stopped. */
export function clientIdFor(vaultKey: string, storage: Pick<Storage, "getItem" | "setItem"> | null, mint: () => string): string {
  const key = `learnloop.desks.client.${vaultKey}`;
  try {
    const stored = storage?.getItem(key);
    if (stored) return stored;
    const minted = mint();
    storage?.setItem(key, minted);
    return minted;
  } catch {
    return mint();
  }
}

export class DeskOutbox {
  private nextSeq = 1;
  private sending: Promise<FlushOutcome> | null = null;

  constructor(
    readonly clientId: string,
    private readonly transport: OutboxTransport,
    private readonly store: OutboxStore = new MemoryOutboxStore(),
  ) {}

  /** Continue the sequence the server holds for this client (`desk.state`'s `serverSeq`). */
  syncSeq(state: Pick<DeskStateDto, "serverSeq">): void {
    const head = state.serverSeq.find((entry) => entry.clientId === this.clientId)?.seq ?? 0;
    const pending = this.store.load();
    const maxPending = pending.length ? pending[pending.length - 1].seq : 0;
    this.nextSeq = Math.max(head, maxPending) + 1;
    // Batches the server already applied leave the outbox.
    for (const batch of pending) if (batch.seq <= head) this.store.remove(batch.seq);
  }

  get pending(): number {
    return this.store.load().length;
  }

  /** The queued batches, oldest first (for rebasing after a conflict or a rejection). */
  queued(): Batch[] {
    return this.store.load();
  }

  /** Replace every queued batch with `batches` (rebased ops), numbered from `fromSeq`. */
  requeue(batches: Array<DeskOpDto[] | BatchBody>, fromSeq: number): void {
    for (const stale of this.store.load()) this.store.remove(stale.seq);
    let seq = fromSeq;
    for (const each of batches) {
      const body: BatchBody = Array.isArray(each) ? { ops: each } : each;
      if (emptyBody(body)) continue;
      this.store.put({ seq, ...body });
      seq += 1;
    }
    this.nextSeq = seq;
  }

  /** Resolves once no batch is being sent. */
  async idle(): Promise<void> {
    while (this.sending) await this.sending.catch(() => undefined);
  }

  /** The number the next batch takes. */
  get next(): number {
    return this.nextSeq;
  }

  get durable(): boolean {
    return this.store.durable;
  }

  enqueue(ops: DeskOpDto[]): number | null {
    if (ops.length === 0) return null;
    const seq = this.nextSeq;
    this.nextSeq += 1;
    this.store.put({ seq, ops });
    return seq;
  }

  /** Queue one ink save (sent by `ink.save`, in the same numbering as desk and pad batches). */
  enqueueInk(ink: InkSaveBody): number {
    const seq = this.nextSeq;
    this.nextSeq += 1;
    this.store.put({ seq, ops: [], ink });
    return seq;
  }

  /** Queue ops on one pad (sent by `pad.apply`, in the same numbering as desk batches). */
  enqueuePad(padId: string, ops: PadOpDto[]): number | null {
    if (ops.length === 0) return null;
    const seq = this.nextSeq;
    this.nextSeq += 1;
    this.store.put({ seq, ops: [], pad: { padId, ops } });
    return seq;
  }

  /** Send the oldest unacknowledged batch, then the next, until the outbox is empty or a batch comes
   * back with a conflict. One flush at a time: a second call waits for the first. */
  flush(): Promise<FlushOutcome> {
    if (this.sending) return this.sending.then(() => this.flush());
    this.sending = this.drain().finally(() => {
      this.sending = null;
    });
    return this.sending;
  }

  private async drain(): Promise<FlushOutcome> {
    let last: FlushOutcome = { kind: "idle" };
    for (;;) {
      const [batch] = this.store.load();
      if (!batch) return last;
      let reply: DeskApplyDto | PadApplyDto | InkSaveDto;
      try {
        if (batch.ink) {
          if (!this.transport.applyInk) throw { code: "validation_error", message: "ink writes are not available here" };
          reply = await this.transport.applyInk({ clientId: this.clientId, seq: batch.seq, ...batch.ink });
        } else if (batch.pad) {
          if (!this.transport.applyPad) throw { code: "validation_error", message: "pad writes are not available here" };
          reply = await this.transport.applyPad({ clientId: this.clientId, seq: batch.seq, padId: batch.pad.padId, ops: batch.pad.ops });
        } else {
          reply = await this.transport.apply({ clientId: this.clientId, seq: batch.seq, ops: batch.ops });
        }
      } catch (error) {
        const message = errorText(error);
        const code = error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : "";
        if (code === "seq_gap" || code === "seq_reused") {
          // The numbering is the server's to keep: drop what it refused and let the shell reload.
          for (const stale of this.store.load()) this.store.remove(stale.seq);
          return { kind: "resync", message };
        }
        if (isPermanentRefusal(code)) {
          // The server consumed no number for a request it refused at validation: the rest move up one.
          this.store.remove(batch.seq);
          const rest = this.store.load().map((each): BatchBody => (each.ink ? { ops: [], ink: each.ink } : each.pad ? { ops: [], pad: each.pad } : { ops: each.ops }));
          this.requeue(rest, batch.seq);
          return { kind: "rejected", message, batch };
        }
        return { kind: "offline", message };
      }
      this.store.remove(batch.seq);
      if (batch.pad && reply.results.some((result) => result.status === "ok" && result.keptBoth)) {
        this.nextSeq = Math.max(this.nextSeq, reply.appliedSeq + 1);
        if (!reply.results.some((result) => result.status !== "ok")) return { kind: "kept-both", reply: reply as PadApplyDto, batch };
      }
      if (reply.results.some((result) => result.status !== "ok")) {
        // The ops queued after it expected heads that may no longer hold: they wait to be rebased.
        this.nextSeq = Math.max(this.nextSeq, reply.appliedSeq + 1);
        return { kind: "conflict", reply, batch };
      }
      last = { kind: "applied", reply };
    }
  }
}
