// The companion's questions (spec §8, the RD3a job contract): each question is a `companion.ask` job,
// polled through the app's one poller until it is done, kept per desk as the desk's thread. Outside React
// so a thread outlives the panel and the shell, and so the contract is tested with plain values.
//
// What the learner sees follows the job honestly: asking (queued or running, with the pieces streamed so
// far when the transport streams), the answer, a failure in its own words, cancelled (and whether the
// answer was kept in the history), or interrupted (the sidecar restarted or the vault closed under it).
import type { CompanionAskInput, CompanionAskJobDto, CompanionAskStatus, CompanionAskSurface, ReaderAnswerDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";

export interface CompanionApi {
  companionAsk(input: CompanionAskInput): Promise<CompanionAskJobDto>;
  companionAskJob(input: { requestId: string }): Promise<CompanionAskJobDto>;
  companionAskCancel(input: { requestId: string }): Promise<CompanionAskJobDto>;
}

export type ExchangeStatus = "asking" | "answered" | "failed" | "cancelled" | "interrupted";

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
  /** Cancelled after the request was sent: the exchange is in the history, the answer not delivered. */
  kept: boolean;
  askedAt: number;
}

export interface AskRequest {
  deskId: string | null;
  windowId: string | null;
  surface: CompanionAskSurface;
  question: string;
  extractionId: string;
  spanId: string;
  selectionSpanIds?: string[];
  quote?: string | null;
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

export function threadKey(deskId: string | null): string {
  return deskId ?? "(no desk)";
}

export class CompanionAsks {
  private threads = new Map<string, CompanionExchange[]>();
  private listeners = new Set<() => void>();
  private polls = new Map<string, () => void>();
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

  /** Ask: the question shows at once (asking), then follows its job. Returns the request id. */
  ask(request: AskRequest): string {
    const requestId = this.mintRequestId();
    const exchange: CompanionExchange = {
      requestId,
      deskId: request.deskId,
      windowId: request.windowId,
      question: request.question,
      quote: request.quote ?? null,
      extractionId: request.extractionId,
      spanId: request.spanId,
      status: "asking",
      jobStatus: null,
      streamedPieces: 0,
      answer: null,
      error: null,
      kept: false,
      askedAt: this.now(),
    };
    const parent = this.parentFor(request);
    const key = threadKey(request.deskId);
    this.threads.set(key, [...(this.threads.get(key) ?? []), exchange]);
    this.emit();
    const input: CompanionAskInput = {
      requestId,
      surface: request.surface,
      deskId: request.deskId,
      extractionId: request.extractionId,
      spanId: request.spanId,
      question: request.question,
      parentExchangeId: parent,
      ...(request.selectionSpanIds?.length ? { selectionSpanIds: request.selectionSpanIds } : {}),
      ...(request.quote ? { selectionQuote: request.quote } : {}),
    };
    void this.api.companionAsk(input).then(
      (job) => {
        this.apply(job);
        if (!job.done) this.watch(requestId, request.windowId);
      },
      // A refusal at the request (the Reader off, no OK to use AI, a held-out passage): said, no job.
      (error: unknown) => this.update(requestId, (current) => ({ ...current, status: "failed", error: errorOf(error) })),
    );
    return requestId;
  }

  /** The same question again, as a new request (an interrupted or failed one). */
  retry(requestId: string): string | null {
    const exchange = [...this.threads.values()].flat().find((each) => each.requestId === requestId);
    if (!exchange) return null;
    return this.ask({
      deskId: exchange.deskId,
      windowId: exchange.windowId,
      surface: exchange.deskId ? "desk" : "reader",
      question: exchange.question,
      extractionId: exchange.extractionId,
      spanId: exchange.spanId,
      quote: exchange.quote,
    });
  }

  cancel(requestId: string): void {
    void this.api.companionAskCancel({ requestId }).then(
      (job) => {
        this.apply(job);
        if (job.done) this.unwatch(requestId);
      },
      (error: unknown) => this.update(requestId, (current) => ({ ...current, error: errorOf(error) })),
    );
  }

  private watch(requestId: string, owner: string | null): void {
    if (this.polls.has(requestId)) return;
    const remove = this.poller.register<CompanionAskJobDto>({
      key: `companion-ask:${requestId}`,
      owner,
      request: () => this.api.companionAskJob({ requestId }),
      onResult: (job) => {
        this.apply(job);
        if (job.done) this.polls.delete(requestId);
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
  }

  private unwatch(requestId: string): void {
    const remove = this.polls.get(requestId);
    this.polls.delete(requestId);
    remove?.();
  }

  private apply(job: CompanionAskJobDto): void {
    this.update(job.requestId, (current) => {
      const base = { ...current, jobStatus: job.status, streamedPieces: job.streamedPieces, kept: job.kept };
      switch (job.status) {
        case "done":
          return { ...base, status: "answered", answer: job.answer, error: null };
        case "failed":
          return { ...base, status: job.error?.code === "interrupted" ? "interrupted" : "failed", error: job.error ? { code: job.error.code, message: job.error.message, retryable: job.error.retryable } : null };
        case "cancelled":
          return { ...base, status: "cancelled" };
        case "expired":
          // Finished and dropped from the sidecar's memory: the exchange is in the history.
          return { ...base, status: "interrupted", error: { code: "expired", message: "This finished while the panel was away; it is in your history.", retryable: false } };
        default:
          return { ...base, status: "asking" };
      }
    });
  }

  /** Stop following every job (the vault closes). */
  dispose(): void {
    for (const remove of this.polls.values()) remove();
    this.polls.clear();
  }
}

const STORES = new WeakMap<object, Map<string, CompanionAsks>>();

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
