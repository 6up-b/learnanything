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

  /** Read a pad's ink once (a second caller shares the read). */
  load(padId: string): Promise<void> {
    if (this.pads[padId]?.loaded) return Promise.resolve();
    const known = this.loads.get(padId);
    if (known) return known;
    const read = this.deps.api.inkList({ padId }).then(
      (out) => {
        this.set(padId, (pad) => {
          const lines: Record<string, InkLine> = {};
          for (const owner of out.owners) {
            if (owner.ownerKind !== "block") continue;
            lines[owner.ownerId] = { blockId: owner.ownerId, strokes: owner.strokes, contentHash: owner.contentHash, unread: !owner.transcription?.current };
          }
          // Strokes written here before the read landed stay on top of the server's.
          for (const [blockId, line] of Object.entries(pad.lines)) {
            const server = lines[blockId];
            lines[blockId] = server ? { ...server, strokes: [...server.strokes, ...line.strokes.filter((s) => !server.strokes.some((o) => o.strokeId === s.strokeId))], unread: server.unread || line.unread } : line;
          }
          return { ...pad, loaded: true, failed: null, lines };
        });
      },
      (error: unknown) => {
        this.loads.delete(padId);
        this.set(padId, (pad) => ({ ...pad, failed: messageOf(error) }));
      },
    );
    this.loads.set(padId, read);
    return read;
  }

  /** Strokes the learner wrote on a line (already queued in the outbox with `inkId`). */
  addStrokes(padId: string, blockId: string, inkId: string, strokes: InkStrokeDto[]): void {
    this.set(padId, (pad) => {
      const line = pad.lines[blockId] ?? { blockId, strokes: [], contentHash: null, unread: true };
      return { ...pad, lines: { ...pad.lines, [blockId]: { ...line, strokes: [...line.strokes, ...strokes.map((s) => ({ ...s, inkId }))], contentHash: null, unread: true } } };
    });
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
      return { ...pad, lines: { ...pad.lines, [blockId]: { ...line, strokes: line.strokes.filter((s) => !strokeIds.includes(s.strokeId)), contentHash: null, unread: true } } };
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
    this.setReading(padId, blockId, { status: "reading", jobId: null, result: null, message: null });
    if ((await this.deps.settled()) !== "saved") {
      this.setReading(padId, blockId, { status: "failed", jobId: null, result: null, message: "your ink is kept on this device until LearnLoop is reachable" });
      return;
    }
    let first: InkTranscribeJobDto;
    try {
      first = await this.deps.api.inkTranscribe({ inkId: last.inkId });
    } catch (error) {
      this.settle(padId, blockId, { version: 1, jobId: null, status: "failed", done: true, result: null, error: { code: codeOf(error), message: messageOf(error), retryable: true, details: null } });
      return;
    }
    if (this.settle(padId, blockId, first) || !first.jobId) return;
    const jobId = first.jobId;
    this.setReading(padId, blockId, { status: "reading", jobId, result: null, message: null });
    const remove = this.deps.poller.register<InkTranscribeJobDto>({
      key: `ink-transcribe:${jobId}`,
      owner,
      request: () => this.deps.api.inkTranscribeJob({ jobId }),
      onResult: (job) => {
        const done = this.settle(padId, blockId, job);
        if (done) this.polls.delete(blockId);
        return { done };
      },
      onError: (error) => {
        if (codeOf(error) !== "job_not_found") return;
        this.polls.get(blockId)?.();
        this.polls.delete(blockId);
        this.setReading(padId, blockId, { status: "failed", jobId, result: null, message: "the reading stopped (LearnLoop restarted) · read it again" });
      },
    });
    this.polls.set(blockId, remove);
  }

  /** Stop a reading: its next model request is refused; one already sent finishes and is kept on the server. */
  cancel(padId: string, blockId: string): void {
    const reading = this.pad(padId).readings[blockId];
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
  private settle(padId: string, blockId: string, job: InkTranscribeJobDto): boolean {
    if (!job.done) return false;
    if (job.status === "done" && job.result) {
      const result = job.result;
      const status: ReadingStatus = result.confidenceLabel === "nothing_read" ? "nothing" : result.applied ? "read" : result.reason === "kept_your_correction" ? "kept_yours" : "read";
      this.setReading(padId, blockId, { status, jobId: job.jobId, result, message: null });
      this.set(padId, (pad) => {
        const line = pad.lines[blockId];
        return line ? { ...pad, lines: { ...pad.lines, [blockId]: { ...line, contentHash: result.contentHash, unread: false } } } : pad;
      });
      // The reading became the block's next version: the pad is read again so its head is the server's.
      if (result.applied) void this.deps.refreshPad(padId);
      return true;
    }
    const code = job.error?.code ?? job.status;
    if (job.status === "cancelled" || code === "cancelled") {
      this.setReading(padId, blockId, { status: "cancelled", jobId: job.jobId, result: null, message: null });
    } else if (code === "cannot_read_images") {
      this.setReading(padId, blockId, { status: "cannot", jobId: job.jobId, result: null, message: job.error?.message ?? null });
    } else {
      this.setReading(padId, blockId, { status: "failed", jobId: job.jobId, result: null, message: job.error?.message ?? code });
    }
    return true;
  }
}
