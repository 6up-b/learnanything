// The ink of the pads shown on the desks (spec §10.10, "Freewrite pads"): each pad's ink lines as the server holds
// them (`ink.list`), the strokes written since, and each line's reading (`ink.transcribe`, polled through the central
// poller, cancellable). One cache per desk shell, so a window moved or reopened finds its lines and readings.
//
// A line is read when the learner has finished it: when they start writing on another line, or ask for it ("read
// it"). Never on every stroke: each stroke changes what the line holds, and a reading of strokes still being written
// would be spent and thrown away.
import type { InkOwnerViewDto, InkReadingDto, InkStrokeDto, InkTranscribeJobDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";

export interface InkCacheApi {
  inkList(input: { padId: string }): Promise<{ owners: InkOwnerViewDto[] }>;
  inkTranscribe(input: { inkId: string }): Promise<InkTranscribeJobDto>;
  inkTranscribeJob(input: { jobId: string }): Promise<InkTranscribeJobDto>;
  inkTranscribeCancel(input: { jobId: string }): Promise<InkTranscribeJobDto>;
}

/** What the line says when handwriting could not be sent to text recognition (GLM-OCR, as ingest reads page
 * images), and how to change that; null for any other outcome. Nothing was sent, and the ink is kept. */
export function inkRefusal(code: string): string | null {
  if (code === "unavailable") return "handwriting can't be read yet: text recognition isn't set up · to add it, paste a z.ai API key in Settings, under Ingestion, or run a local GLM-OCR server";
  if (code === "needs_upload_ok") return "reading handwriting sends a picture of it to z.ai, which needs your OK first: say OK on a book's card in the Library";
  return null;
}

export type ReadingStatus = "reading" | "read" | "kept_yours" | "nothing" | "cannot" | "failed" | "cancelled";

export interface LineReading {
  status: ReadingStatus;
  jobId: string | null;
  result: InkReadingDto | null;
  message: string | null;
}

export interface InkLine {
  blockId: string;
  strokes: Array<InkStrokeDto & { inkId: string }>;
  /** The server's hash of the strokes it holds (stale once strokes are written here). */
  contentHash: string | null;
  /** Strokes were written (or erased) since the line was last read. */
  unread: boolean;
  /** Counts the line's local changes: a reading that started at another count read other strokes. */
  revision: number;
  /** The server's reading of the strokes it last held (`ink.list`), kept so an offer survives a restart. */
  transcription: InkOwnerViewDto["transcription"];
}

export interface PadInk {
  loaded: boolean;
  failed: string | null;
  lines: Record<string, InkLine>;
  readings: Record<string, LineReading>;
}

const EMPTY: PadInk = { loaded: false, failed: null, lines: {}, readings: {} };

export interface InkCacheDeps {
  api: InkCacheApi;
  poller: Poller;
  /** Every queued write acknowledged ("unsaved" when it cannot be sent now). */
  settled: () => Promise<"saved" | "unsaved">;
  /** Read a pad again (a reading written into a block moves its head). */
  refreshPad: (padId: string) => Promise<void>;
  /** Why a reading waits now (an inline check is open: a reading would show what its veils hold), or null. */
  held?: () => string | null;
}

function codeOf(error: unknown): string {
  return error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : "failed";
}

function messageOf(error: unknown): string {
  return error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error);
}

export class InkCache {
  private pads: Record<string, PadInk> = {};
  private loads = new Map<string, Promise<void>>();
  private polls = new Map<string, () => void>();
  /** Ink saves queued and not yet known to be acknowledged (a forced read keeps their strokes). */
  private pendingInk = new Set<string>();
  /** Each line's reading attempt: a continuation of an older attempt (cancelled, superseded) does nothing. */
  private attempts = new Map<string, number>();
  /** The line each pad was last written on. */
  private writing = new Map<string, string>();
  private listeners = new Set<() => void>();
  private version = 0;

  constructor(private readonly deps: InkCacheDeps) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = (): number => this.version;

  pad(padId: string): PadInk {
    return this.pads[padId] ?? EMPTY;
  }

  private set(padId: string, change: (pad: PadInk) => PadInk): void {
    this.pads = { ...this.pads, [padId]: change(this.pad(padId)) };
    this.version += 1;
    for (const listener of [...this.listeners]) listener();
  }

  /** Read a pad's ink once (a second caller shares the read); `force` reads it again (an erase the server may have
   * refused, a pad shown again), with the strokes written here and not yet acknowledged kept on top. */
  load(padId: string, force = false): Promise<void> {
    if (this.pads[padId]?.loaded && !force) return Promise.resolve();
    const known = this.loads.get(padId);
    if (known) return known;
    const read = this.deps.api.inkList({ padId }).then(
      (out) => {
        this.set(padId, (pad) => {
          const lines: Record<string, InkLine> = {};
          for (const owner of out.owners) {
            if (owner.ownerKind !== "block") continue;
            const local = pad.lines[owner.ownerId];
            lines[owner.ownerId] = { blockId: owner.ownerId, strokes: owner.strokes, contentHash: owner.contentHash, unread: !owner.transcription?.current,
              revision: local?.revision ?? 0, transcription: owner.transcription };
          }
          // Strokes written here and not yet acknowledged stay on top of the server's.
          for (const [blockId, line] of Object.entries(pad.lines)) {
            const pending = line.strokes.filter((s) => this.pendingInk.has(s.inkId));
            const server = lines[blockId];
            if (server) {
              lines[blockId] = { ...server, strokes: [...server.strokes, ...pending.filter((s) => !server.strokes.some((o) => o.strokeId === s.strokeId))], unread: server.unread || pending.length > 0 };
            } else if (pending.length) {
              lines[blockId] = { ...line, strokes: pending };
            }
          }
          // A reading kept beside the learner's correction is offered again after a reload, as when it arrived.
          const readings = { ...pad.readings };
          for (const owner of out.owners) {
            const kept = owner.transcription;
            if (owner.ownerKind !== "block" || !kept?.current || kept.reason !== "kept_your_correction" || readings[owner.ownerId]?.status === "reading") continue;
            readings[owner.ownerId] = { status: "kept_yours", jobId: null, message: null, result: {
              transcriptionId: kept.transcriptionId, ownerKind: "block", ownerId: owner.ownerId, contentHash: kept.contentHash,
              latexMd: kept.latexMd, confidenceLabel: kept.confidenceLabel, model: null, createdAt: kept.createdAt,
              applied: false, reason: kept.reason, headVersionId: null } };
          }
          return { ...pad, loaded: true, failed: null, lines, readings };
        });
      },
      (error: unknown) => {
        this.set(padId, (pad) => ({ ...pad, failed: messageOf(error) }));
      },
    ).finally(() => this.loads.delete(padId));
    this.loads.set(padId, read);
    return read;
  }

  /** Strokes the learner wrote on a line (already queued in the outbox with `inkId`). */
  addStrokes(padId: string, blockId: string, inkId: string, strokes: InkStrokeDto[]): void {
    this.pendingInk.add(inkId);
    this.set(padId, (pad) => {
      const line = pad.lines[blockId] ?? { blockId, strokes: [], contentHash: null, unread: true, revision: 0, transcription: null };
      return { ...pad, lines: { ...pad.lines, [blockId]: { ...line, strokes: [...line.strokes, ...strokes.map((s) => ({ ...s, inkId }))], contentHash: null, unread: true, revision: line.revision + 1 } } };
    });
  }

  /** The outbox acknowledged every queued write: the ink saved here is the server's now; the pad is read again,
   * so an erase or a save it refused shows as the server holds it. */
  async reconcile(padId: string): Promise<void> {
    if ((await this.deps.settled()) !== "saved") return;
    this.pendingInk.clear();
    await this.load(padId, true);
  }

  /** A line lifted out to a pad of its own (`lift_out`): its strokes and reading go with it at once, and the new
   * pad is read from the server once the lift is acknowledged (its strokes then carry the lifted block's saves). */
  lifted(fromPadId: string, blockId: string, toPadId: string, newBlockId: string): void {
    const from = this.pad(fromPadId);
    const line = from.lines[blockId];
    if (!line) return;
    const reading = from.readings[blockId];
    this.set(toPadId, (pad) => ({ ...pad, loaded: true, lines: { ...pad.lines, [newBlockId]: { ...line, blockId: newBlockId } },
      readings: reading && reading.status !== "reading" ? { ...pad.readings, [newBlockId]: reading } : pad.readings }));
    void this.reconcile(toPadId);
  }

  /** The learner wrote on a line: a different line they were writing on before is finished, and is read. */
  wrote(padId: string, blockId: string, owner: string | null): void {
    const before = this.writing.get(padId);
    this.writing.set(padId, blockId);
    if (before && before !== blockId && this.pad(padId).lines[before]?.unread) void this.read(padId, before, owner);
  }

  /** Strokes the barrel erased (the pad's erase_ink is queued by the caller). */
  erase(padId: string, blockId: string, strokeIds: string[]): void {
    this.set(padId, (pad) => {
      const line = pad.lines[blockId];
      if (!line) return pad;
      return { ...pad, lines: { ...pad.lines, [blockId]: { ...line, strokes: line.strokes.filter((s) => !strokeIds.includes(s.strokeId)), contentHash: null, unread: true, revision: line.revision + 1 } } };
    });
  }

  private setReading(padId: string, blockId: string, reading: LineReading): void {
    this.set(padId, (pad) => ({ ...pad, readings: { ...pad.readings, [blockId]: reading } }));
  }

  /** Read a finished line: its strokes as they stand, once they are acknowledged. `owner` pauses its polls. */
  async read(padId: string, blockId: string, owner: string | null): Promise<void> {
    const line = this.pad(padId).lines[blockId];
    const last = line?.strokes[line.strokes.length - 1];
    if (!line || !last) return;
    const current = this.pad(padId).readings[blockId];
    if (current?.status === "reading") return;
    const held = this.deps.held?.() ?? null;
    if (held) {
      this.setReading(padId, blockId, { status: "failed", jobId: null, result: null, message: `read it ${held}` });
      return;
    }
    const attempt = (this.attempts.get(blockId) ?? 0) + 1;
    this.attempts.set(blockId, attempt);
    const stale = () => this.attempts.get(blockId) !== attempt;
    const revision = line.revision;
    this.setReading(padId, blockId, { status: "reading", jobId: null, result: null, message: null });
    if ((await this.deps.settled()) !== "saved") {
      if (stale()) return;
      // The outbox lives in memory (the durable store is the RD-spike's open choice): unsent ink is kept only while the app
      // stays open, and saying "on this device" would promise more.
      this.setReading(padId, blockId, { status: "failed", jobId: null, result: null, message: "Waiting for your handwriting to save. Keep LearnLoop open, then try again." });
      return;
    }
    if (stale()) return;
    // A check may have opened while the ink was saving: the reading waits for it then too.
    const heldNow = this.deps.held?.() ?? null;
    if (heldNow) {
      this.setReading(padId, blockId, { status: "failed", jobId: null, result: null, message: `read it ${heldNow}` });
      return;
    }
    this.pendingInk.clear();
    let first: InkTranscribeJobDto;
    try {
      first = await this.deps.api.inkTranscribe({ inkId: last.inkId });
    } catch (error) {
      if (stale()) return;
      if (codeOf(error) === "check_open") {
        // The server holds model calls while a check is open (whatever this desk knew): a plain word, no error.
        this.setReading(padId, blockId, { status: "failed", jobId: null, result: null, message: "read it after your check · finish or set aside the check first" });
        return;
      }
      this.settle(padId, blockId, { version: 1, jobId: null, status: "failed", done: true, result: null, error: { code: codeOf(error), message: messageOf(error), retryable: true, details: null } }, revision);
      return;
    }
    if (stale()) {
      // Cancelled (or the window closed) before the start answered: the job it started is stopped, never followed.
      if (first.jobId && !first.done) void this.deps.api.inkTranscribeCancel({ jobId: first.jobId }).catch(() => undefined);
      return;
    }
    if (this.settle(padId, blockId, first, revision) || !first.jobId) return;
    const jobId = first.jobId;
    this.setReading(padId, blockId, { status: "reading", jobId, result: null, message: null });
    const remove = this.deps.poller.register<InkTranscribeJobDto>({
      key: `ink-transcribe:${jobId}`,
      owner,
      request: () => this.deps.api.inkTranscribeJob({ jobId }),
      onResult: (job) => {
        const done = this.settle(padId, blockId, job, revision);
        if (done) this.polls.delete(blockId);
        return { done };
      },
      onError: (error) => {
        if (codeOf(error) !== "job_not_found") return;
        this.polls.get(blockId)?.();
        this.polls.delete(blockId);
        this.setReading(padId, blockId, { status: "failed", jobId, result: null, message: "Handwriting conversion stopped. Try again." });
      },
    });
    this.polls.set(blockId, remove);
  }

  /** Stop a reading: its next model request is refused; one already sent finishes and is kept on the server. */
  cancel(padId: string, blockId: string): void {
    const reading = this.pad(padId).readings[blockId];
    // A reading whose start has not answered yet is stopped when it answers (`read`'s attempt check).
    this.attempts.set(blockId, (this.attempts.get(blockId) ?? 0) + 1);
    this.polls.get(blockId)?.();
    this.polls.delete(blockId);
    if (reading?.status !== "reading") return;
    if (reading.jobId) void this.deps.api.inkTranscribeCancel({ jobId: reading.jobId }).catch(() => undefined);
    this.setReading(padId, blockId, { status: "cancelled", jobId: reading.jobId, result: null, message: null });
  }

  /** Cancel every reading of these pads (their window closed). */
  cancelAll(padIds: string[]): void {
    for (const padId of padIds) for (const blockId of Object.keys(this.pad(padId).readings)) this.cancel(padId, blockId);
  }

  /** A finished job's outcome as the line's reading; false while it is still running. */
  private settle(padId: string, blockId: string, job: InkTranscribeJobDto, revision: number): boolean {
    if (!job.done) return false;
    if (job.status === "done" && job.result) {
      const result = job.result;
      const status: ReadingStatus = result.confidenceLabel === "nothing_read" ? "nothing" : result.applied ? "read" : result.reason === "kept_your_correction" ? "kept_yours" : "read";
      this.setReading(padId, blockId, { status, jobId: job.jobId, result, message: null });
      this.set(padId, (pad) => {
        const line = pad.lines[blockId];
        // Strokes written or erased while it was read (here, or on another device: the server says
        // strokes_changed): it read other strokes, and the line stays unread.
        if (!line || line.revision !== revision || result.reason === "strokes_changed") return pad;
        return { ...pad, lines: { ...pad.lines, [blockId]: { ...line, contentHash: result.contentHash, unread: false } } };
      });
      // The reading became the block's next version: the pad is read again so its head is the server's.
      if (result.applied) void this.deps.refreshPad(padId);
      return true;
    }
    const code = job.error?.code ?? job.status;
    if (job.status === "cancelled" || code === "cancelled") {
      this.setReading(padId, blockId, { status: "cancelled", jobId: job.jobId, result: null, message: null });
    } else if (inkRefusal(code)) {
      this.setReading(padId, blockId, { status: "cannot", jobId: job.jobId, result: null, message: inkRefusal(code) });
    } else {
      this.setReading(padId, blockId, { status: "failed", jobId: job.jobId, result: null, message: job.error?.message ?? "Couldn’t convert the handwriting. Try again." });
    }
    return true;
  }
}
