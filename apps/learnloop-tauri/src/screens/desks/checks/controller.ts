// Inline cold checks on the desks (spec §12.6; RD7's frontend half), as an external store (useSyncExternalStore): the
// due checks of the readings in view (their closed markers), the one open administration with its veils, what the
// learner opened, the answer and its reply. Every step is the server's (`check.*`): the desks never decide what is
// veiled or what an answer counts as.
import { api } from "../../../api/client";
import type { CheckCardDto, CheckExposureKind, CheckSubmitDto, CheckVeilRefDto, CheckVisibleDto, ChecksDueDto } from "../../../api/dto";
import { refKey, visibleKey, type CheckReason } from "./model";

export interface CheckTransport {
  dueFor(input: { extractionId: string }): Promise<ChecksDueDto>;
  begin(input: { requestId: string; commitmentId: string; sessionId?: string; visible: CheckVisibleDto }): Promise<CheckCardDto>;
  protectMore(input: { administrationToken: string; visible: CheckVisibleDto }): Promise<{ veilAdditions: CheckVeilRefDto[] }>;
  expose(input: { administrationToken: string; ref: CheckVeilRefDto; kind: CheckExposureKind }): Promise<{ protectionStatus: { exposure: unknown[]; coldNow: boolean } }>;
  submit(input: { administrationToken: string; submissionId: string; answerMd: string }): Promise<CheckSubmitDto>;
  abandon(input: { administrationToken: string }): Promise<unknown>;
  openInline(): Promise<{ administration: CheckCardDto | null }>;
}

export const LIVE_CHECK_TRANSPORT: CheckTransport = {
  dueFor: (input) => api.checksDueFor(input),
  begin: (input) => api.checkBeginInline(input),
  protectMore: (input) => api.checkProtectMore(input),
  expose: (input) => api.checkExpose(input),
  submit: (input) => api.checkSubmitInline(input),
  abandon: (input) => api.checkAbandonInline(input),
  openInline: () => api.checkOpenInline(),
};

export type DueCheck = ChecksDueDto["checks"][number];

export interface OpenCheck {
  card: CheckCardDto;
  phase: "open" | "submitting" | "answered";
  /** Everything veiled so far (the opening's set, then each protect_more's additions). */
  veiled: CheckVeilRefDto[];
  /** The veils the learner opened ("show it anyway"), by ref key. */
  opened: string[];
  /** The groups of the veils opened, in order (the card's "you looked at …"). */
  looked: string[];
  /** Whether the item could still be answered cold after the last opening (the server's word). */
  coldNow: boolean | null;
  /** The answer as typed (kept across a failed submit). */
  answer: string;
  /** The submission's id, minted once per administration: a retry is the same submission. */
  submissionId: string;
  reply: CheckSubmitDto | null;
  /** Where its due row says it sits (null when the check opened from elsewhere, or after a restart). */
  host: DueCheck["host"];
  error: string | null;
}

function messageOf(error: unknown): string {
  return error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error);
}

function codeOf(error: unknown): string | null {
  return error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : null;
}

/** Why a check cannot open now, in the learner's words (the server's refusal codes). */
const REFUSED: Record<string, string> = {
  administration_open: "another check is open · answer it or say not now first",
  being_answered_in_today: "this check is being answered in Today",
  nothing_to_serve: "nothing can be asked for this check right now · it comes back later",
  not_due: "this check isn't due yet",
  below_tag: "checks here arrive with the next update of your vault",
};

/** A window as the server judged it: a window showing another reading than before is judged again. */
function judgedKey(window: CheckVisibleDto["windows"][number]): string {
  return `${window.windowId}|${window.extractionId ?? window.kind}`;
}

/** The group of a window veiled whole while the server judges it (it just came into view during the check). */
export const ARRIVING_GROUP = "just opened";

export class CheckDesk {
  private due = new Map<string, DueCheck[]>();
  private asked = new Set<string>();
  private later = new Set<string>();
  private current: OpenCheck | null = null;
  private lastVisible: string | null = null;
  /** The windows the server has judged for the open check (in its first view or a later protect_more). */
  private judged = new Set<string>();
  /** Windows that came into view and are veiled whole until the server's protect_more answers for them. */
  private arriving: string[] = [];
  private restarted = false;
  private listeners = new Set<() => void>();
  private version = 0;
  /** A line the desks show once (a refused opening), cleared by the next step. */
  notice: string | null = null;

  constructor(private readonly transport: CheckTransport, private readonly mintId: (prefix: string) => string) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = (): number => this.version;

  private emit(): void {
    this.version += 1;
    for (const listener of this.listeners) listener();
  }

  open(): OpenCheck | null {
    return this.current;
  }

  /** Whether a check holds the desks now (open or being submitted; an answered card lifts the veils). */
  holding(): boolean {
    return this.current !== null && this.current.phase !== "answered";
  }

  /** Why a verb that would reveal or send veiled material waits, or null when no check is open. */
  heldReason(): string | null {
    return this.holding() ? "after your check · it is open on this desk" : null;
  }

  /** The veils standing now: everything veiled but what the learner opened (none once answered). */
  veils(): CheckVeilRefDto[] {
    const open = this.current;
    if (!open || open.phase === "answered") return [];
    const opened = new Set(open.opened);
    return [...open.veiled.filter((ref) => !opened.has(refKey(ref))),
      ...this.arriving.map((windowId): CheckVeilRefDto => ({ group: ARRIVING_GROUP, kind: "window", window_id: windowId }))];
  }

  /** A veil on a window the server has not judged yet: it cannot be opened until it has. */
  arrivingVeil(ref: CheckVeilRefDto): boolean {
    return ref.group === ARRIVING_GROUP && typeof ref.window_id === "string" && this.arriving.includes(ref.window_id);
  }

  // -- the due checks and their closed markers ---------------------------------------------------------------------

  /** Read the due checks of these readings (once each; again after an answer). */
  readings(extractionIds: readonly string[]): void {
    for (const extractionId of new Set(extractionIds)) {
      if (this.asked.has(extractionId)) continue;
      this.asked.add(extractionId);
      void Promise.resolve().then(() => this.transport.dueFor({ extractionId })).then((out) => {
        this.due.set(extractionId, out.checks.filter((check) => check.host?.extractionId === extractionId));
        if (this.current && !this.current.host) this.current = { ...this.current, host: this.hostOf(this.current.card.commitmentId) };
        this.emit();
      }, () => this.asked.delete(extractionId));
    }
  }

  private hostOf(commitmentId: string): DueCheck["host"] {
    return [...this.due.values()].flat().find((check) => check.commitmentId === commitmentId)?.host ?? null;
  }

  /** The due checks whose host passage is this span of this reading (a closed marker sits before it). */
  dueAt(extractionId: string, spanId: string): DueCheck[] {
    return (this.due.get(extractionId) ?? []).filter((check) => check.host?.spanId === spanId);
  }

  /** "later" on a closed marker: folded for this session (the check stays due, and "check now" is still offered). */
  defer(commitmentId: string): void {
    this.later.add(commitmentId);
    this.emit();
  }

  deferred(commitmentId: string): boolean {
    return this.later.has(commitmentId);
  }

  undefer(commitmentId: string): void {
    if (this.later.delete(commitmentId)) this.emit();
  }

  // -- the administration -----------------------------------------------------------------------------------------

  /** After a restart: the open administration, its card and veils, as the server kept them. */
  restart(): void {
    if (this.restarted) return;
    this.restarted = true;
    void Promise.resolve().then(() => this.transport.openInline()).then((out) => {
      if (!out.administration || this.current) return;
      // Its host passage, once the due checks of a reading on the desks name it (the card then opens there).
      this.current = this.fresh(out.administration, this.hostOf(out.administration.commitmentId));
      this.lastVisible = null;
      this.judged = new Set();
      this.arriving = [];
      this.emit();
    }, () => undefined);
  }

  private fresh(card: CheckCardDto, host: DueCheck["host"]): OpenCheck {
    return {
      card, phase: "open", veiled: [...card.protection.veiled], opened: card.protection.opened.map(refKey), looked: [],
      coldNow: null, answer: "", submissionId: this.mintId("csub"), reply: null, host, error: null,
    };
  }

  /** "check now": the server opens the administration and names the veils; the prompt comes back only then. */
  async begin(commitmentId: string, sessionId: string | null, visible: CheckVisibleDto): Promise<boolean> {
    this.notice = null;
    if (this.current && this.current.phase !== "answered") {
      this.notice = REFUSED.administration_open;
      this.emit();
      return false;
    }
    const host = this.hostOf(commitmentId);
    try {
      // With no session yet, the server opens the answer in the most recent open one or a new one (the card says which).
      const card = await this.transport.begin({ requestId: this.mintId("creq"), commitmentId, ...(sessionId ? { sessionId } : {}), visible });
      this.current = this.fresh(card, host);
      this.lastVisible = visibleKey(visible);
      this.judged = new Set(visible.windows.map(judgedKey));
      this.arriving = [];
      this.later.delete(commitmentId);
    } catch (error) {
      this.notice = REFUSED[codeOf(error) ?? ""] ?? `couldn't open the check · ${messageOf(error)}`;
    }
    this.emit();
    return this.current?.card.commitmentId === commitmentId;
  }

  /** New windows or passages came into view: the server veils what it must before it is read. */
  async protectMore(visible: CheckVisibleDto): Promise<void> {
    const open = this.current;
    if (!open || open.phase !== "open") return;
    const key = visibleKey(visible);
    if (key === this.lastVisible) return;
    this.lastVisible = key;
    // A window the server has not judged is veiled whole at once and stays so until its answer: what it shows is
    // never readable before the server has said whether it is protected.
    const unjudged = visible.windows.filter((window) => !this.judged.has(judgedKey(window)));
    const fresh = unjudged.map((window) => window.windowId).filter((windowId) => !this.arriving.includes(windowId));
    if (fresh.length) {
      this.arriving = [...this.arriving, ...fresh];
      this.emit();
    }
    try {
      const out = await this.transport.protectMore({ administrationToken: open.card.administrationToken, visible });
      if (this.current?.card.administrationToken !== open.card.administrationToken) return;
      for (const window of unjudged) this.judged.add(judgedKey(window));
      this.arriving = this.arriving.filter((windowId) => !fresh.includes(windowId));
      const now = this.current;
      const known = new Set(now.veiled.map(refKey));
      this.current = { ...now, veiled: [...now.veiled, ...out.veilAdditions.filter((ref) => !known.has(refKey(ref)))] };
      this.emit();
    } catch {
      // Unchanged veils stay (an arriving window stays veiled whole); the next change in view asks again.
      this.lastVisible = null;
    }
  }

  /** "show it anyway" on a veil: the exposure is recorded at once, then the veil lifts. */
  async expose(ref: CheckVeilRefDto): Promise<void> {
    const open = this.current;
    if (!open || open.phase !== "open") return;
    try {
      const out = await this.transport.expose({ administrationToken: open.card.administrationToken, ref, kind: "opened_veil" });
      if (this.current?.card.administrationToken !== open.card.administrationToken) return;
      const now = this.current;
      this.current = { ...now, opened: [...now.opened, refKey(ref)], looked: [...now.looked, ref.group], coldNow: out.protectionStatus.coldNow, error: null };
    } catch (error) {
      this.current = { ...open, error: `couldn't open it · ${messageOf(error)}` };
    }
    this.emit();
  }

  setAnswer(answer: string): void {
    if (!this.current || this.current.phase !== "open") return;
    this.current = { ...this.current, answer };
    this.emit();
  }

  /** "answer ↵": the attempt through the attempt service; the reply says whether it settled the check. */
  async submit(): Promise<void> {
    const open = this.current;
    if (!open || open.phase !== "open" || !open.answer.trim()) return;
    this.current = { ...open, phase: "submitting", error: null };
    this.emit();
    try {
      const reply = await this.transport.submit({ administrationToken: open.card.administrationToken, submissionId: open.submissionId, answerMd: open.answer });
      this.current = { ...open, phase: "answered", reply };
      if (open.host?.extractionId) {
        // The check's markers are read again (an answered check has none).
        this.asked.delete(open.host.extractionId);
        this.readings([open.host.extractionId]);
      }
    } catch (error) {
      this.current = { ...open, phase: "open", error: `couldn't send your answer · ${messageOf(error)} · it is kept here` };
    }
    this.emit();
  }

  /** "not now": closed with no attempt; the duty stays pending and its marker stays. */
  async abandon(): Promise<void> {
    const open = this.current;
    if (!open || open.phase === "answered") return;
    try {
      await this.transport.abandon({ administrationToken: open.card.administrationToken });
      this.current = null;
    } catch (error) {
      this.current = { ...open, error: `couldn't close the check · ${messageOf(error)}` };
    }
    this.emit();
  }

  /** The answered card's "close". */
  close(): void {
    if (this.current?.phase !== "answered") return;
    this.current = null;
    this.emit();
  }

  reason(): CheckReason | null {
    return (this.current?.reply?.reason as CheckReason | undefined) ?? null;
  }
}
