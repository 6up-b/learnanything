// The one client poller (spec §3.6): every job poll goes through it, at one cadence with backoff,
// with requests for the same job coalesced, and with the polls of a paused window (offscreen, hidden,
// a preview) skipped until it is shown again.
//
// A poll is registered under a key (the job it watches). Two registrations of one key share one
// request per tick and each gets the result. A poll that answers `done` is removed; one whose request
// fails backs off (one tick, then two, four, … up to `maxBackoffTicks`) and resumes its cadence on the
// next success.

export interface PollResult {
  /** The job settled: stop polling it. */
  done: boolean;
}

export interface PollRegistration<T> {
  key: string;
  request: () => Promise<T>;
  onResult: (value: T) => PollResult | void;
  onError?: (error: unknown) => void;
  /** Whose poll this is (a desk window id), so a paused owner's polls wait. */
  owner?: string | null;
}

interface Entry {
  key: string;
  request: () => Promise<unknown>;
  listeners: Set<PollRegistration<unknown>>;
  failures: number;
  /** Ticks to skip before the next request (the backoff). */
  wait: number;
  inFlight: boolean;
}

export interface PollerOptions {
  tickMs?: number;
  maxBackoffTicks?: number;
  setInterval?: (fn: () => void, ms: number) => unknown;
  clearInterval?: (handle: unknown) => void;
}

export class Poller {
  readonly tickMs: number;
  private readonly maxBackoffTicks: number;
  private readonly entries = new Map<string, Entry>();
  private paused = new Set<string>();
  private handle: unknown = null;
  private readonly setTimer: (fn: () => void, ms: number) => unknown;
  private readonly clearTimer: (handle: unknown) => void;

  constructor(options: PollerOptions = {}) {
    this.tickMs = options.tickMs ?? 1500;
    this.maxBackoffTicks = options.maxBackoffTicks ?? 16;
    this.setTimer = options.setInterval ?? ((fn, ms) => globalThis.setInterval(fn, ms));
    this.clearTimer = options.clearInterval ?? ((handle) => globalThis.clearInterval(handle as ReturnType<typeof setInterval>));
  }

  /** Register a poll; returns its removal. */
  register<T>(registration: PollRegistration<T>): () => void {
    const reg = registration as unknown as PollRegistration<unknown>;
    let entry = this.entries.get(registration.key);
    if (!entry) {
      entry = { key: registration.key, request: registration.request, listeners: new Set(), failures: 0, wait: 0, inFlight: false };
      this.entries.set(registration.key, entry);
    }
    entry.listeners.add(reg);
    this.ensureRunning();
    return () => this.unregister(registration.key, reg);
  }

  setOwnerPaused(owner: string, paused: boolean): void {
    if (paused) this.paused.add(owner);
    else this.paused.delete(owner);
  }

  get size(): number {
    return this.entries.size;
  }

  get running(): boolean {
    return this.handle !== null;
  }

  /** One round: exposed for tests and for a caller that wants an immediate check. */
  async tick(): Promise<void> {
    const work: Promise<void>[] = [];
    for (const entry of [...this.entries.values()]) {
      if (entry.inFlight) continue;
      const live = [...entry.listeners].filter((listener) => !listener.owner || !this.paused.has(listener.owner));
      if (live.length === 0) continue;
      if (entry.wait > 0) {
        entry.wait -= 1;
        continue;
      }
      entry.inFlight = true;
      work.push(
        entry.request().then(
          (value) => {
            entry.inFlight = false;
            entry.failures = 0;
            let done = false;
            for (const listener of [...entry.listeners]) {
              const result = listener.onResult(value);
              if (result && result.done) done = true;
            }
            if (done) this.entries.delete(entry.key);
          },
          (error: unknown) => {
            entry.inFlight = false;
            entry.failures += 1;
            entry.wait = Math.min(this.maxBackoffTicks, 2 ** (entry.failures - 1));
            for (const listener of entry.listeners) listener.onError?.(error);
          },
        ),
      );
    }
    await Promise.all(work);
    if (this.entries.size === 0) this.stop();
  }

  private unregister(key: string, registration: PollRegistration<unknown>): void {
    const entry = this.entries.get(key);
    if (!entry) return;
    entry.listeners.delete(registration);
    if (entry.listeners.size === 0) this.entries.delete(key);
    if (this.entries.size === 0) this.stop();
  }

  private ensureRunning(): void {
    if (this.handle !== null) return;
    this.handle = this.setTimer(() => void this.tick(), this.tickMs);
  }

  private stop(): void {
    if (this.handle === null) return;
    this.clearTimer(this.handle);
    this.handle = null;
  }
}

/** The app's one poller. */
export const poller = new Poller();
