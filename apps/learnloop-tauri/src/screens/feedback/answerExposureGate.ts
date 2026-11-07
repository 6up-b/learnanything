// The answer exposure gate, pure (no Tauri, no React): the invariant of answerExposure.ts's header,
// shared by the desktop's hook and the phone's feedback (mobile v2 §5.3: the phone imports the
// desktop's pure modules, never its layouts). Moved here unchanged from answerExposure.ts.
import contract from "./exposureContract.json";

/** The numbers the screen and the readers share (a test pins them equal). */
export const EXPOSURE = contract as {
  horizonMs: number;
  renewalGraceMs: number;
  showMarginMs: number;
  renewAfterMs: number;
  tickMs: number;
};

/** What the ledger says about one display row (`record_answer_display`). */
export interface DisplayReceipt {
  recordedAt?: string | null;
  alreadyRecorded?: boolean;
}

export type RecordDisplay = (displayId: string) => Promise<DisplayReceipt | unknown>;

export type ExposureStatus = "shown" | "waiting" | "away" | "unavailable";

interface Row {
  id: string;
  /** The row's stamp (the sidecar's, floored to the second). */
  stampMs: number;
  /** When this display id was first sent (client clock). */
  sentMs: number;
  /** The gate's epoch when it was first sent (round 4: rows from before an
   *  interruption never show the answer again). */
  epoch: number;
  /** The presence count when it was first sent. */
  presence: number;
}

interface Pending {
  id: string;
  firstSentMs: number;
  epoch: number;
  presence: number;
  sending: boolean;
  failures: number;
}

function newDisplayId(): string {
  const random = globalThis.crypto?.randomUUID?.();
  return `display_${random ?? `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`}`;
}

function refused(error: unknown): boolean {
  return Boolean(error && typeof error === "object" && (error as { retryable?: unknown }).retryable === false);
}

/** The gate for one answer on one screen (the clock and the writer are injected). */
export class AnswerExposureGate {
  private latest: Row | null = null;
  private pending: Pending | null = null;
  /** Counts the learner's returns and inputs (never compared with clock times). */
  private presence = 1;
  /** Counts interruptions: a row sent in an earlier epoch never shows the answer. */
  private epoch = 0;
  private lastCheckMs: number | null = null;
  private stopped = false;

  constructor(
    private readonly record: RecordDisplay,
    private readonly now: () => number = () => Date.now(),
    private readonly onChange: () => void = () => undefined
  ) {}

  /** A committed row, sent since the last interruption, covers the answer
   *  being on screen at `at`. A clock that went back since the last check is
   *  never covered (round 4, F1-3: a discontinuity, like a wake). */
  covered(at: number = this.now()): boolean {
    const latest = this.latest;
    if (latest === null || latest.epoch !== this.epoch) return false;
    if (this.lastCheckMs !== null && at < this.lastCheckMs) return false;
    return at >= latest.sentMs - EXPOSURE.tickMs && at < latest.stampMs + EXPOSURE.renewalGraceMs - EXPOSURE.showMarginMs;
  }

  /** The learner is here: input, focus, the page shown, the answer asked for. */
  activity(): void {
    this.presence += 1;
  }

  /** A lifecycle signal that may precede a suspend or a loss of attention
   *  (hidden, pagehide, freeze, blur, minimized), or a clock discontinuity:
   *  the answer is hidden at once and shows again only after a fresh row,
   *  sent after this, is acknowledged (round 4, F1-1). */
  interrupt(): void {
    this.epoch += 1;
  }

  /** The learner was present since the latest row was sent. */
  private present(): boolean {
    return this.latest === null || this.latest.epoch !== this.epoch || this.presence > this.latest.presence;
  }

  /** One check while the answer is wanted on screen (`wanted` false: it is
   *  not, so nothing is written). Starts the write a row needs; returns
   *  whether the answer may be on screen now. */
  check(wanted: boolean): boolean {
    const at = this.now();
    if (this.lastCheckMs !== null && (at < this.lastCheckMs || at - this.lastCheckMs > 3 * EXPOSURE.tickMs)) {
      // The clock went back, or a check long after the last one (the machine
      // waking: no timer ran while it slept). A discontinuity: hide until a
      // fresh row, and count it as a return.
      this.interrupt();
      this.activity();
    }
    this.lastCheckMs = at;
    if (!wanted || this.stopped) return false;
    const covered = this.covered(at);
    const due = !covered || at - (this.latest?.sentMs ?? Number.NEGATIVE_INFINITY) >= EXPOSURE.renewAfterMs;
    if (due && this.present()) this.write(at);
    return covered;
  }

  status(): ExposureStatus {
    if (this.covered()) return "shown";
    if (this.stopped) return "unavailable";
    if (!this.present()) return "away";
    return (this.pending?.failures ?? 0) > 0 ? "unavailable" : "waiting";
  }

  private write(at: number): void {
    if (this.pending !== null && this.pending.epoch !== this.epoch) this.pending = null;
    const pending = this.pending ?? {
      id: newDisplayId(), firstSentMs: at, epoch: this.epoch, presence: this.presence, sending: false, failures: 0
    };
    this.pending = pending;
    if (pending.sending) return;
    pending.sending = true;
    let call: Promise<unknown>;
    try {
      call = Promise.resolve(this.record(pending.id));
    } catch (error) {
      call = Promise.reject(error);
    }
    call
      .then((receipt) => {
        const stampMs = this.stampOf(receipt, pending.firstSentMs);
        if (this.latest === null || pending.epoch > this.latest.epoch || stampMs >= this.latest.stampMs) {
          this.latest = {
            id: pending.id, stampMs, sentMs: pending.firstSentMs, epoch: pending.epoch, presence: pending.presence
          };
        }
        if (this.pending === pending) this.pending = null;
      })
      .catch((error: unknown) => {
        pending.failures += 1;
        // Refused (the self-grade's draft is done with): stop; the answer stays hidden.
        if (refused(error)) this.stopped = true;
      })
      .finally(() => {
        pending.sending = false;
        this.onChange();
      });
  }

  /** The row's stamp: the sidecar's, never later than now on this clock.
   *  Without one (an older sidecar), the id's first send: the row was written
   *  no earlier, so its grace ends no earlier than this says. */
  private stampOf(receipt: unknown, fallbackMs: number): number {
    const at = receipt && typeof receipt === "object" ? (receipt as DisplayReceipt).recordedAt : null;
    const parsed = typeof at === "string" ? Date.parse(at) : Number.NaN;
    return Number.isFinite(parsed) ? Math.min(parsed, this.now()) : fallbackMs;
  }
}
