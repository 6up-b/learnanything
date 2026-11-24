// The companion's questions (spec §8, the RD3a job contract): each question is a `companion.ask` job,
// polled through the app's one poller until it is done, kept per desk as the desk's thread. Outside React
// so a thread outlives the panel and the shell, and so the contract is tested with plain values.
//
// What the learner sees follows the job honestly: asking (queued or running, with the pieces streamed so
// far when the transport streams), the answer, a failure in its own words, cancelled (and whether the
// answer was kept in the history), or interrupted (the sidecar restarted or the vault closed under it).
// A question waits (shown) until the desk writes it depends on are acknowledged; stopping shows until the
// job resolves; a retry resends the original request whole. The store follows its jobs only while a shell
// shows it (suspend / resume) and never again once its vault is gone (dispose).
import type { CompanionAskInput, CompanionAskJobDto, CompanionAskStatus, CompanionAskSurface, ReaderAnswerDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";

export interface CompanionApi {
  companionAsk(input: CompanionAskInput): Promise<CompanionAskJobDto>;
  companionAskJob(input: { requestId: string }): Promise<CompanionAskJobDto>;
  companionAskCancel(input: { requestId: string }): Promise<CompanionAskJobDto>;
}

export type ExchangeStatus = "waiting" | "asking" | "answered" | "failed" | "cancelled" | "interrupted";

export interface CompanionExchange {
  requestId: string;
  deskId: string | null;
  /** The window it was asked from: its poll waits while that window is paused. */
  windowId: string | null;
  question: string;
  /** The selection it was asked about, if any. */
  quote: string | null;
  extractionId: string;
  spanId: string;
  status: ExchangeStatus;
  jobStatus: CompanionAskStatus | null;
  streamedPieces: number;
  answer: ReaderAnswerDto | null;
  error: { code: string; message: string; retryable: boolean } | null;
  /** The sidecar kept the exchange in the history (said only when it says so). */
  kept: boolean;
  /** Stop was pressed and the job has not resolved yet. */
  stopping: boolean;
  /** The question reached the tutor (a worker took it, or the question was recorded): never read from `kept`. */
  sent: boolean;
  askedAt: number;
  /** What was asked, whole (a retry resends exactly this with a new request id). */
  request: Omit<CompanionAskInput, "requestId">;
}

/** Whether the desk writes a question depends on were acknowledged before it is sent. */
export type DeskWritesSettled = "saved" | "unsaved";

export interface AskRequest {
  deskId: string | null;
  windowId: string | null;
  surface: CompanionAskSurface;
  question: string;
  extractionId: string;
  spanId: string;
  selectionSpanIds?: string[];
  quote?: string | null;
  /** Pad blocks asked about (recorded with the exchange). */
  padBlockIds?: string[];
  /** The exchange this follow-up branches from, when the asker names it (a reconnect's "still unclear" branches
   *  from its question); absent, the thread's last answer about the same reading. */
  parentExchangeId?: string | null;
  /** The answer mode the ask was routed to (a source window's intent box). */
  answerMode?: CompanionAskInput["answerMode"];
  /** RW1c: "another way" (alternative) and "that didn't help" (remediate) under an answer. */
  retrievalIntent?: CompanionAskInput["retrievalIntent"];
  /** RW1c: the personalized chip (absent while the tutor does not look things up). */
  personalized?: boolean;
}

function errorOf(error: unknown): { code: string; message: string; retryable: boolean } {
  if (error && typeof error === "object") {
    const record = error as { code?: unknown; message?: unknown; retryable?: unknown };
    return {
      code: typeof record.code === "string" ? record.code : "error",
      message: typeof record.message === "string" ? record.message : String(error),
      retryable: record.retryable === true,
    };
  }
  return { code: "error", message: String(error), retryable: false };
}

const UNSAVED = {
  code: "desk_not_saved",
  message: "Your question hasn’t been sent. Try again when your desk changes finish saving.",
  retryable: true,
};

export function threadKey(deskId: string | null): string {
  return deskId ?? "(no desk)";
}

export class CompanionAsks {
  private threads = new Map<string, CompanionExchange[]>();
  private listeners = new Set<() => void>();
  private polls = new Map<string, () => void>();
  private owners = new Map<string, string | null>();
  /** Jobs to follow again when a shell resumes the store. */
  private held = new Map<string, string | null>();
  private suspended = false;
  private disposed = false;
  private version = 0;

  constructor(
    private readonly api: CompanionApi,
    private readonly poller: Poller,
    private readonly mintRequestId: () => string,
    private readonly now: () => number = Date.now,
  ) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  /** Changes with every update (a useSyncExternalStore snapshot). */
  getVersion = (): number => this.version;

  thread(deskId: string | null): CompanionExchange[] {
    return this.threads.get(threadKey(deskId)) ?? [];
  }

  private emit(): void {
    this.version += 1;
    for (const listener of [...this.listeners]) listener();
  }

  private update(requestId: string, change: (exchange: CompanionExchange) => CompanionExchange): void {
    for (const [key, list] of this.threads) {
      const index = list.findIndex((exchange) => exchange.requestId === requestId);
      if (index < 0) continue;
      const next = [...list];
      next[index] = change(list[index]);
      this.threads.set(key, next);
      this.emit();
      return;
    }
  }

  /** The exchange to branch from: the thread's last answer about the same reading. */
  private parentFor(request: AskRequest): string | null {
    const list = this.thread(request.deskId);
    for (let index = list.length - 1; index >= 0; index -= 1) {
      const exchange = list[index];
      if (exchange.status !== "answered" || !exchange.answer) continue;
      return exchange.extractionId === request.extractionId ? exchange.answer.readerAnswerEventId || exchange.answer.eventId : null;
    }
    return null;
  }

  /** Ask: the question shows at once, waiting while `ready` (the desk writes it depends on) settles, then
   * asking as it follows its job. Returns the request id. */
  ask(request: AskRequest, ready?: Promise<DeskWritesSettled>): string {
    const parent = request.parentExchangeId !== undefined ? request.parentExchangeId : this.parentFor(request);
    const input: Omit<CompanionAskInput, "requestId"> = {
      surface: request.surface,
      deskId: request.deskId,
      extractionId: request.extractionId,
      spanId: request.spanId,
      question: request.question,
      parentExchangeId: parent,
      ...(request.selectionSpanIds?.length ? { selectionSpanIds: request.selectionSpanIds } : {}),
      ...(request.quote ? { selectionQuote: request.quote } : {}),
      ...(request.padBlockIds?.length ? { padBlockIds: request.padBlockIds } : {}),
      ...(request.answerMode ? { answerMode: request.answerMode } : {}),
      ...(request.retrievalIntent ? { retrievalIntent: request.retrievalIntent } : {}),
      ...(request.personalized !== undefined ? { personalized: request.personalized } : {}),
    };
    return this.send(input, request.windowId, request.quote ?? null, ready);
  }

  private send(input: Omit<CompanionAskInput, "requestId">, windowId: string | null, quote: string | null, ready?: Promise<DeskWritesSettled>): string {
    const requestId = this.mintRequestId();
    const exchange: CompanionExchange = {
      requestId,
      deskId: input.deskId ?? null,
      windowId,
      question: input.question,
      quote,
      extractionId: input.extractionId,
      spanId: input.spanId,
      status: ready ? "waiting" : "asking",
      jobStatus: null,
      streamedPieces: 0,
      answer: null,
      error: null,
      kept: false,
      stopping: false,
      sent: false,
      askedAt: this.now(),
      request: input,
    };
    const key = threadKey(exchange.deskId);
    this.threads.set(key, [...(this.threads.get(key) ?? []), exchange]);
    this.emit();
    const go = () => {
      if (this.disposed) return;
      this.update(requestId, (current) => (current.status === "waiting" ? { ...current, status: "asking" } : current));
      void this.api.companionAsk({ requestId, ...input }).then(
        (job) => {
          if (this.disposed) return;
          this.apply(job);
          if (!job.done) this.watch(requestId, windowId);
        },
        // A refusal at the request (the Reader off, no OK to use AI, a held-out passage): said, no job.
        (error: unknown) => this.update(requestId, (current) => ({ ...current, status: "failed", error: errorOf(error) })),
      );
    };
    if (!ready) go();
    else {
      // The sidecar reads the desk's focus and windows when it records the question: they must be its.
      void ready.then(
        (settled) => {
          if (settled === "saved") go();
          else this.update(requestId, (current) => ({ ...current, status: "failed", error: UNSAVED }));
        },
        () => this.update(requestId, (current) => ({ ...current, status: "failed", error: UNSAVED })),
      );
    }
    return requestId;
  }

  /** The same question again, as a new request: the original request whole, with a new id. */
  retry(requestId: string): string | null {
    const exchange = [...this.threads.values()].flat().find((each) => each.requestId === requestId);
    if (!exchange) return null;
    return this.send(exchange.request, exchange.windowId, exchange.quote);
  }

  cancel(requestId: string): void {
    // "stopping" until the job says how it ended (an already-sent question may still be written).
    this.update(requestId, (current) => ({ ...current, stopping: true }));
    void this.api.companionAskCancel({ requestId }).then(
      (job) => {
        this.apply(job);
        if (job.done) this.unwatch(requestId);
        else this.watch(requestId, this.ownerOf(requestId));
      },
      (error: unknown) => this.update(requestId, (current) => ({ ...current, error: errorOf(error) })),
    );
  }

  private ownerOf(requestId: string): string | null {
    return [...this.threads.values()].flat().find((each) => each.requestId === requestId)?.windowId ?? null;
  }

  private watch(requestId: string, owner: string | null): void {
    if (this.disposed || this.polls.has(requestId)) return;
    if (this.suspended) {
      // Detached from every shell: followed again on resume.
      this.held.set(requestId, owner);
      return;
    }
    const remove = this.poller.register<CompanionAskJobDto>({
      key: `companion-ask:${requestId}`,
      owner,
      request: () => this.api.companionAskJob({ requestId }),
      onResult: (job) => {
        this.apply(job);
        if (job.done) {
          this.polls.delete(requestId);
          this.owners.delete(requestId);
        }
        return { done: job.done };
      },
      onError: (error) => {
        const reason = errorOf(error);
        // The sidecar restarted since: the job is gone (the history has it if it finished).
        if (reason.code === "job_not_found") {
          this.unwatch(requestId);
          this.update(requestId, (current) => ({ ...current, status: "interrupted", error: reason }));
        }
      },
    });
    this.polls.set(requestId, remove);
    this.owners.set(requestId, owner);
  }

  private unwatch(requestId: string): void {
    const remove = this.polls.get(requestId);
    this.polls.delete(requestId);
    this.owners.delete(requestId);
    this.held.delete(requestId);
    remove?.();
  }

  private apply(job: CompanionAskJobDto): void {
    this.update(job.requestId, (current) => {
      // Sent once the sidecar says a model request went out (an older sidecar: once a worker ran it or an answer
      // was kept); the recorded question alone is not a sent request, and nothing is inferred from `kept` missing.
      const sent = current.sent || (job.sent ?? (job.status === "running" || job.status === "done" || job.kept));
      const base = { ...current, jobStatus: job.status, streamedPieces: job.streamedPieces, kept: job.kept, sent };
      // A cancel the sidecar has not resolved yet: still stopping.
      if (!job.done && (job.status === "cancelled" || current.stopping)) return { ...base, status: "asking", stopping: true };
      switch (job.status) {
        case "done":
          return { ...base, status: "answered", answer: job.answer, error: null };
        case "failed":
          return { ...base, status: job.error?.code === "interrupted" ? "interrupted" : "failed", error: job.error ? { code: job.error.code, message: job.error.message, retryable: job.error.retryable } : null };
        case "cancelled":
          return { ...base, status: "cancelled", stopping: false };
        case "expired":
          // Finished and dropped from the sidecar's memory: the exchange is in the history.
          return { ...base, status: "interrupted", error: { code: "expired", message: "This reply is no longer available here. Check History or ask again.", retryable: false } };
        default:
          return { ...base, status: "asking" };
      }
    });
  }

  /** No shell shows this store (it unmounted): its polls stop, remembered for `resume`. */
  suspend(): void {
    this.suspended = true;
    for (const [requestId, remove] of this.polls) {
      this.held.set(requestId, this.owners.get(requestId) ?? null);
      remove();
    }
    this.polls.clear();
    this.owners.clear();
  }

  /** A shell shows it again: the jobs still open are followed again. */
  resume(): void {
    if (this.disposed) return;
    this.suspended = false;
    const held = [...this.held];
    this.held.clear();
    for (const [requestId, owner] of held) this.watch(requestId, owner);
  }

  /** The vault is gone: stop following every job, for good (a late first reply included). */
  dispose(): void {
    this.disposed = true;
    for (const remove of this.polls.values()) remove();
    this.polls.clear();
    this.owners.clear();
    this.held.clear();
  }
}

const STORES = new WeakMap<object, Map<string, CompanionAsks>>();

/** The vault closed: its store is disposed and forgotten (a later mount for it starts afresh). */
export function forgetCompanionAsks(vaultKey: string, owner: object): void {
  const byVault = STORES.get(owner);
  byVault?.get(vaultKey)?.dispose();
  byVault?.delete(vaultKey);
}

/** The vault's one set of companion threads (per transport), kept across the shell's mounts. */
export function companionAsksFor(vaultKey: string, owner: object, make: () => CompanionAsks): CompanionAsks {
  let byVault = STORES.get(owner);
  if (!byVault) {
    byVault = new Map();
    STORES.set(owner, byVault);
  }
  let store = byVault.get(vaultKey);
  if (!store) {
    store = make();
    byVault.set(vaultKey, store);
  }
  return store;
}
