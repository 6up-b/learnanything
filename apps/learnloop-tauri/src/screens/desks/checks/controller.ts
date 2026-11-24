// Inline cold checks on the desks (spec §12.6; RD7's frontend half), as an external store (useSyncExternalStore): the
// due checks as opaque handles (one unlocated marker per desk: before "check now" nothing says what a check is about or
// where it sits, the owner's decision on RD7-56), the one open administration with its veils, what the learner
// opened, the answer and its reply. Every step is the server's (`check.*`): the desks never decide what is
// veiled or what an answer counts as.
//
// The store belongs to the app, one per vault, not to the desks: an open administration outlives the desks' screen,
// and nothing of the desks (nor any other study screen) is shown before `recover` has said whether one is open.
import { api } from "../../../api/client";
import type { CheckCardDto, CheckExposeReplyDto, CheckExposureKind, CheckProtectReplyDto, CheckSubmitDto, CheckVeilRefDto,
  CheckVisibleDto, ChecksDueDto } from "../../../api/dto";
import { refKey, visibleKey, type CheckReason } from "./model";

export interface CheckTransport {
  dueFor(): Promise<ChecksDueDto>;
  begin(input: { requestId: string; handle: string; sessionId?: string; visible: CheckVisibleDto }): Promise<CheckCardDto>;
  protectMore(input: { administrationToken: string; visible: CheckVisibleDto }): Promise<CheckProtectReplyDto>;
  expose(input: { administrationToken: string; ref: CheckVeilRefDto; kind: CheckExposureKind; exposureId: string }): Promise<CheckExposeReplyDto>;
  submit(input: { administrationToken: string; submissionId: string; answerMd: string; veilsRevision: number }): Promise<CheckSubmitDto>;
  abandon(input: { administrationToken: string }): Promise<unknown>;
  openInline(): Promise<{ administration: CheckCardDto | null }>;
}

export const LIVE_CHECK_TRANSPORT: CheckTransport = {
  dueFor: () => api.checksDueFor(),
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
  /** Everything veiled so far, as the server's standing set last said (opened refs included, to count them). */
  veiled: CheckVeilRefDto[];
  /** The veils the learner opened ("show it anyway"), by ref key. */
  opened: string[];
  /** The groups of the veils opened, in order (the card's "you looked at …"). */
  looked: string[];
  /** Whether the item could still be answered cold after the last opening (the server's word). */
  coldNow: boolean | null;
  /** The answer as typed (kept across a failed submit and a restart). */
  answer: string;
  /** The submission's id: the one the server reserved, else minted once per administration (a retry is the same). */
  submissionId: string;
  reply: CheckSubmitDto | null;
  /** Where the server says the begun check sits (its card's host; null when it has none). */
  host: CheckCardDto["host"];
  error: string | null;
}

/** Whether the store knows if an administration is open: nothing of the desks shows before it does. */
export type CheckRecovery = "pending" | "known" | "failed";

function messageOf(error: unknown): string {
  return error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error);
}

export function codeOf(error: unknown): string | null {
  return error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : null;
}

/** The server refuses a model call, a transcription, Show me or a lesson while an administration is open. */
export const CHECK_OPEN_WORDS = "finish or set aside the check first";

/** A refusal's plain words when the server refused because a check is open, else null (an ordinary error). */
export function checkOpenRefusal(error: unknown): string | null {
  return codeOf(error) === "check_open" ? CHECK_OPEN_WORDS : null;
}

/** Why a check cannot open now, in the learner's words (the server's refusal codes). */
const REFUSED: Record<string, string> = {
  administration_open: "another check is open · answer it or say not now first",
  check_unknown: "no cold check is due now",
  administration_closed: "this check is closed already",
  being_answered_in_today: "this check is being answered in Today",
  nothing_to_serve: "nothing can be asked for this check right now · it comes back later",
  not_due: "this check isn't due yet",
  below_tag: "checks here arrive with the next update of your vault",
  submission_in_flight: "your answer is being sent",
};

/** The ref sent for a region the server does not describe (a shelf, a band, a window's other parts), opened through
 *  show it anyway: the server records it as an unmeasured opening. */
export function regionRef(region: string, windowId: string | null): CheckVeilRefDto {
  const inWindow = region.startsWith("window:");
  return { group: inWindow ? "this window's other parts" : region, kind: "surface", surface: inWindow ? "window" : region,
    ...(windowId ? { window_id: windowId } : {}) };
}

/** Where drafts are kept by administration token (the server stores no draft). Absent or throwing storage keeps none. */
export interface DraftStore {
  get(token: string): string | null;
  set(token: string, text: string | null): void;
}

const DRAFT_PREFIX = "learnloop.checks.draft.";

export const BROWSER_DRAFTS: DraftStore = {
  get(token) {
    try {
      return globalThis.localStorage?.getItem(DRAFT_PREFIX + token) ?? null;
    } catch {
      return null;
    }
  },
  set(token, text) {
    try {
      if (text === null || text === "") globalThis.localStorage?.removeItem(DRAFT_PREFIX + token);
      else globalThis.localStorage?.setItem(DRAFT_PREFIX + token, text);
    } catch {
      // A draft that cannot be kept is only lost on a restart.
    }
  },
};

export class CheckDesk {
  private due: DueCheck[] = [];
  private dueRead: "none" | "asking" | "known" = "none";
  private later = false;
  /** When the next check falls due: the due checks are read again then. */
  private nextDueTimer: ReturnType<typeof setTimeout> | null = null;
  /** A begin sent and not settled: the desks hold everything meanwhile (the server may have opened the check while the
   *  reply is lost), and a retry sends the same request (the server returns that administration, recording nothing). */
  private opening: { requestId: string; inFlight: boolean } | null = null;
  private current: OpenCheck | null = null;
  private lastVisible: string | null = null;
  /** The passages the server has judged for the open check, per window and reading (a reply covered the request that
   *  listed them). A passage not judged yet stays held. */
  private judged = new Map<string, Set<string>>();
  /** The veil sets' sequence number the desks applied last (sent with the answer). */
  private revision = 0;
  /** Protect requests sent and not answered yet. */
  private pending = 0;
  /** Regions opened through show it anyway, with what they showed then (a change shows something new: held again). */
  private regions = new Map<string, string>();
  /** Named veils opened, with what they showed then (by ref key). */
  private openedPrints = new Map<string, string>();
  /** Exposure ids minted for an opening not yet recorded (a retry sends the same id). */
  private exposureIds = new Map<string, string>();
  private recoveryState: CheckRecovery = "pending";
  private recovering = false;
  private listeners = new Set<() => void>();
  private version = 0;
  /** What is visible now (the desks' inventory), for a refused answer whose veils were stale. */
  private visibleSource: (() => CheckVisibleDto) | null = null;
  /** A line the desks show once (a refused opening), cleared by the next step. */
  notice: string | null = null;

  constructor(private readonly transport: CheckTransport, private readonly mintId: (prefix: string) => string,
              private readonly drafts: DraftStore = BROWSER_DRAFTS) {}

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
    return this.opening !== null || (this.current !== null && this.current.phase !== "answered");
  }

  /** Whether "check now" was sent and has no answer yet. */
  openingNow(): boolean {
    return Boolean(this.opening?.inFlight);
  }

  /** Why a verb that would reveal or send veiled material waits, or null when no check is open. */
  heldReason(): string | null {
    return this.holding() ? "after your check · it is open on this desk" : null;
  }

  /** The veils standing now: the server's standing set less what the learner opened (none once answered). */
  veils(): CheckVeilRefDto[] {
    const open = this.current;
    if (!open || open.phase === "answered") return [];
    const opened = new Set(open.opened);
    return open.veiled.filter((ref) => !opened.has(refKey(ref)));
  }

  /** The named veils the learner opened, by key, with what they showed when opened. */
  openedNamed(): ReadonlyMap<string, string> {
    return this.openedPrints;
  }

  /** The regions opened through show it anyway, with what they showed when opened. */
  openedRegions(): ReadonlyMap<string, string> {
    return this.regions;
  }

  /** Whether the server has judged this passage (a reply covered a request that listed it). */
  passageJudged(windowId: string, extractionId: string | null, spanId: string): boolean {
    return this.judged.get(`${windowId}|${extractionId ?? ""}`)?.has(spanId) ?? false;
  }

  /** Whether a protect request is on its way (new passages wait for it). */
  judging(): boolean {
    return this.pending > 0;
  }

  /** The recovery read's state: until it is known, nothing of the desks shows. */
  recovery(): CheckRecovery {
    return this.recoveryState;
  }

  setVisibleSource(source: (() => CheckVisibleDto) | null): void {
    this.visibleSource = source;
  }

  // -- the due checks and the desk's marker ------------------------------------------------------------------------

  /** Read the due checks (every one in the vault, as handles; again after a check closes, and when a handle is found
   *  dead). The request names nothing: asking about a reading or a passage would itself be answered with where a check
   *  is. */
  readDue(): void {
    if (this.dueRead === "asking") return;
    this.dueRead = "asking";
    void Promise.resolve().then(() => this.transport.dueFor()).then((out) => {
      this.due = out.checks;
      this.dueRead = "known";
      this.scheduleNextDue(out.nextDue ?? null);
      this.emit();
    }, () => {
      this.dueRead = "none";
    });
  }

  /** A check that falls due while the desks stay open is offered then: the due checks are read again at that time. */
  private scheduleNextDue(at: string | null): void {
    if (this.nextDueTimer !== null) clearTimeout(this.nextDueTimer);
    this.nextDueTimer = null;
    const when = at ? Date.parse(at) : Number.NaN;
    if (Number.isNaN(when)) return;
    // setTimeout's longest delay; a later boundary is read on the next mount or close.
    const wait = Math.min(Math.max(when - Date.now(), 0) + 1000, 2_147_000_000);
    this.nextDueTimer = setTimeout(() => {
      this.nextDueTimer = null;
      this.readDue();
    }, wait);
  }

  /** The checks due now that the desk's marker offers (none is named: a handle each, in the server's order). */
  dueChecks(): DueCheck[] {
    return this.due.filter((check) => !check.beingAnswered);
  }

  /** "later" on the marker: folded for this session (the checks stay due, and "check now" is still offered). */
  defer(): void {
    this.later = true;
    this.emit();
  }

  deferred(): boolean {
    return this.later;
  }

  undefer(): void {
    if (!this.later) return;
    this.later = false;
    this.emit();
  }

  // -- the administration -----------------------------------------------------------------------------------------

  /** The recovery read (once): whether an administration is open, and if so its card and veils, as the server kept
   *  them. Until it answers nothing of the desks shows; a failure says so and offers to try again (fail closed). */
  recover(): void {
    if (this.recoveryState !== "pending" || this.recovering) return;
    this.recovering = true;
    void Promise.resolve().then(() => this.transport.openInline()).then((out) => {
      this.recovering = false;
      this.recoveryState = "known";
      if (out.administration && !this.holding()) this.adopt(out.administration, out.administration.host ?? null);
      this.emit();
    }, (error) => {
      this.recovering = false;
      // A vault below the inline-check tag has no administration to recover.
      this.recoveryState = codeOf(error) === "below_tag" ? "known" : "failed";
      this.emit();
    });
  }

  /** "try again" after a failed recovery read. */
  retryRecovery(): void {
    if (this.recoveryState !== "failed") return;
    this.recoveryState = "pending";
    this.emit();
    this.recover();
  }

  /** The desks' own mount: the recovery read, once. */
  restart(): void {
    this.recover();
    this.readDue();
  }

  private adopt(card: CheckCardDto, host: CheckCardDto["host"], judgedFrom: CheckVisibleDto | null = null): void {
    const draft = this.drafts.get(card.administrationToken) ?? "";
    const seen = new Set<string>();
    // Every ref veiled so far, once (the server's `veiled` includes the opened ones; an older card's did not).
    const veiled = [...card.protection.veiled, ...card.protection.opened].filter((ref) => {
      const key = refKey(ref);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    this.current = {
      card, phase: "open", veiled, opened: card.protection.opened.map(refKey), looked: [],
      coldNow: null, answer: draft, submissionId: card.submissionId ?? this.mintId("csub"), reply: null, host, error: null,
    };
    this.revision = card.revision ?? 0;
    this.lastVisible = judgedFrom ? visibleKey(judgedFrom) : null;
    this.judged = new Map();
    if (judgedFrom) this.judge(judgedFrom);
    this.regions = new Map();
    this.openedPrints = new Map(card.protection.opened.map((ref) => [refKey(ref), ""]));
    this.exposureIds = new Map();
  }

  /** A begin with no answer: the restart read decides. An open administration is adopted (veils judged anew); none
   *  releases the desks; no answer either keeps them held, and "check now" sends the same request again. */
  private async settleOpening(requestId: string, why: string): Promise<void> {
    try {
      const out = await this.transport.openInline();
      this.opening = null;
      if (out.administration) {
        this.adopt(out.administration, out.administration.host ?? null);
        return;
      }
      this.notice = `couldn't open the check · ${why}`;
    } catch {
      this.opening = { requestId, inFlight: false };
      this.notice = "couldn't reach LearnLoop · everything stays hidden until the check is known · check now again";
    }
  }

  private judge(visible: CheckVisibleDto): void {
    for (const window of visible.windows) {
      if (!window.spanIds?.length) continue;
      const key = `${window.windowId}|${window.extractionId ?? ""}`;
      const spans = this.judged.get(key) ?? new Set<string>();
      for (const spanId of window.spanIds) spans.add(spanId);
      this.judged.set(key, spans);
    }
  }

  /** "check now": the server resolves the handle, opens the administration and names the veils; the prompt (and where
   *  the check sits) comes back only then. A lost reply's retry (another click) gets the same administration back. A
   *  dead handle (the sidecar restarted, or the check moved) is read again once and the check now due is opened: the
   *  marker never named which check it was, so the learner is not stranded on a stale one. */
  async begin(handle: string | null, sessionId: string | null, visible: CheckVisibleDto): Promise<boolean> {
    this.notice = null;
    if (this.opening?.inFlight) return false;
    if (this.current && this.holding()) {
      this.notice = REFUSED.administration_open;
      this.emit();
      return false;
    }
    let chosen = handle ?? this.dueChecks()[0]?.handle ?? null;
    // The same request until it is settled: a retry after a lost reply gets the administration it opened.
    const requestId = this.opening?.requestId ?? this.mintId("creq");
    this.opening = { requestId, inFlight: true };
    this.emit();
    const open = (each: string) => this.transport.begin({ requestId, handle: each, ...(sessionId ? { sessionId } : {}), visible });
    try {
      if (!chosen) throw Object.assign(new Error("no cold check is due"), { code: "check_unknown" });
      let card: CheckCardDto;
      try {
        // With no session yet, the server opens the answer in the most recent open one or a new one (the card says which).
        card = await open(chosen);
      } catch (error) {
        if (codeOf(error) !== "check_unknown") throw error;
        this.due = (await this.transport.dueFor()).checks;
        this.dueRead = "known";
        chosen = this.dueChecks()[0]?.handle ?? null;
        if (!chosen) throw error;
        card = await open(chosen);
      }
      // A replayed card's veils were judged on an earlier view: this view's passages wait for a protect request.
      this.adopt(card, card.host ?? null, card.replayed ? null : visible);
      this.opening = null;
      this.later = false;
    } catch (error) {
      const code = codeOf(error);
      if (!code) {
        // No answer: the server may have opened the check. The desks stay held until the restart read says.
        await this.settleOpening(requestId, messageOf(error));
        this.emit();
        return this.holding() && this.current !== null;
      }
      this.opening = null;
      this.notice = REFUSED[code ?? ""] ?? `couldn't open the check · ${messageOf(error)}`;
      // Another commitment's administration is open and the desks did not know it: adopt it (its card says so).
      if (code === "administration_open" && !this.current) {
        this.recoveryState = "pending";
        this.recover();
      }
    }
    this.emit();
    return this.holding();
  }

  /** New windows or passages came into view: the server veils what it must before it is read. Its reply carries the
   *  whole standing set: the desks replace theirs with it, so a lost reply's retry loses no veil. */
  async protectMore(visible: CheckVisibleDto): Promise<void> {
    const open = this.current;
    if (!open || open.phase !== "open") return;
    const key = visibleKey(visible);
    if (key === this.lastVisible) return;
    this.lastVisible = key;
    this.pending += 1;
    this.emit();
    try {
      const out = await this.transport.protectMore({ administrationToken: open.card.administrationToken, visible });
      const now = this.current;
      if (!now || now.card.administrationToken !== open.card.administrationToken) return;
      const revision = typeof out.revision === "number" ? out.revision : this.revision;
      if (revision >= this.revision) {
        const opened = new Set(now.opened);
        const openedRefs = now.veiled.filter((ref) => opened.has(refKey(ref)));
        const standing = out.standing ?? [...now.veiled.filter((ref) => !opened.has(refKey(ref))), ...out.veilAdditions];
        const seen = new Set<string>();
        const veiled = [...openedRefs, ...standing].filter((ref) => {
          const each = refKey(ref);
          if (seen.has(each)) return false;
          seen.add(each);
          return true;
        });
        // A standing ref the learner had opened is veiled again by the server's word (it shows something new).
        const reveiled = standing.map(refKey).filter((each) => opened.has(each));
        this.current = { ...now, veiled, opened: now.opened.filter((each) => !reveiled.includes(each)) };
        for (const each of reveiled) this.openedPrints.delete(each);
        this.revision = revision;
      }
      // The passages this request listed are judged once its reply (whatever its order) is applied.
      this.judge(visible);
    } catch {
      // Unjudged passages stay held; the next change in view asks again.
      if (this.lastVisible === key) this.lastVisible = null;
    } finally {
      this.pending -= 1;
      this.emit();
    }
  }

  /** "show it anyway" on a named veil: the exposure is recorded at once, then the veil lifts. A refusal or failure
   *  records nothing and the veil stays. `print` is what the veiled thing showed (a change later holds it again). */
  async expose(ref: CheckVeilRefDto, print = ""): Promise<boolean> {
    const key = refKey(ref);
    const ok = await this.record(key, ref, "opened_veil");
    const now = this.current;
    if (!ok || !now) return false;
    this.openedPrints.set(key, print);
    if (!now.opened.includes(key)) this.current = { ...now, opened: [...now.opened, key], looked: [...now.looked, ref.group] };
    this.emit();
    return true;
  }

  /** "show it anyway" on a region the server does not describe (a shelf, a band, a window's other parts): recorded
   *  as an unmeasured opening (`left`, the kind for a surface the veils do not cover), so the answer counts as
   *  practice. */
  async exposeRegion(region: string, windowId: string | null, print: string): Promise<boolean> {
    const ref = regionRef(region, windowId);
    const ok = await this.record(`region:${region}`, ref, "left");
    const now = this.current;
    if (!ok || !now) return false;
    this.regions.set(region, print);
    this.current = { ...now, looked: [...now.looked, ref.group] };
    this.emit();
    return true;
  }

  /** What a named veil opened before a restart shows now (its print was not known then). */
  notePrint(key: string, print: string): void {
    if (this.openedPrints.get(key) === "") this.openedPrints.set(key, print);
  }

  /** The named veils the learner opened, with what they showed then (the hold keeps them open while unchanged). */
  openedRefs(): Array<{ ref: CheckVeilRefDto; print: string }> {
    const open = this.current;
    if (!open || open.phase === "answered") return [];
    const opened = new Set(open.opened);
    return open.veiled.filter((ref) => opened.has(refKey(ref))).map((ref) => ({ ref, print: this.openedPrints.get(refKey(ref)) ?? "" }));
  }

  /** A named veil (by ref key) or a region opened earlier shows something new now: it is held again. */
  rehold(key: string): void {
    let changed = this.regions.delete(key);
    if (this.openedPrints.delete(key) && this.current) {
      this.current = { ...this.current, opened: this.current.opened.filter((each) => each !== key) };
      changed = true;
    }
    if (changed) this.emit();
  }

  private async record(key: string, ref: CheckVeilRefDto, kind: CheckExposureKind): Promise<boolean> {
    const open = this.current;
    if (!open || open.phase !== "open") return false;
    const exposureId = this.exposureIds.get(key) ?? this.mintId("cexp");
    this.exposureIds.set(key, exposureId);
    try {
      const out = await this.transport.expose({ administrationToken: open.card.administrationToken, ref, kind, exposureId });
      const now = this.current;
      if (!now || now.card.administrationToken !== open.card.administrationToken) return false;
      this.exposureIds.delete(key);
      this.current = { ...now, coldNow: out.protectionStatus.coldNow, error: null };
      return true;
    } catch (error) {
      const now = this.current;
      if (now && now.card.administrationToken === open.card.administrationToken) {
        this.current = { ...now, error: `couldn't open it · ${REFUSED[codeOf(error) ?? ""] ?? messageOf(error)} · it stays hidden` };
        this.emit();
      }
      return false;
    }
  }

  setAnswer(answer: string): void {
    if (!this.current || this.current.phase !== "open") return;
    this.current = { ...this.current, answer };
    this.drafts.set(this.current.card.administrationToken, answer);
    this.emit();
  }

  /** "answer ↵": the attempt through the attempt service; the reply says whether it settled the check. The answer
   *  carries the veils' revision the desks applied: a stale one is refused, the standing set is read again, and the
   *  same submission is sent once more. */
  async submit(): Promise<void> {
    const open = this.current;
    if (!open || open.phase !== "open" || !open.answer.trim()) return;
    this.current = { ...open, phase: "submitting", error: null };
    this.emit();
    const send = () => this.transport.submit({ administrationToken: open.card.administrationToken, submissionId: open.submissionId,
      answerMd: open.answer, veilsRevision: this.revision });
    try {
      let reply: CheckSubmitDto;
      try {
        reply = await send();
      } catch (error) {
        if (codeOf(error) !== "veils_stale" || !this.visibleSource) throw error;
        await this.refreshStanding();
        reply = await send();
      }
      this.current = { ...(this.current ?? open), phase: "answered", reply };
      this.drafts.set(open.card.administrationToken, null);
      // The due checks are read again (an answered check is not due; a begun one's handle is spent).
      this.readDue();
    } catch (error) {
      const now = this.current ?? open;
      this.current = { ...now, phase: "open", error: `couldn't send your answer · ${REFUSED[codeOf(error) ?? ""] ?? messageOf(error)} · it is kept here` };
    }
    this.emit();
  }

  /** The standing set again, whatever the last view was (a stale answer's retry). */
  private async refreshStanding(): Promise<void> {
    const visible = this.visibleSource?.();
    if (!visible || !this.current) return;
    this.current = { ...this.current, phase: "open" };
    this.lastVisible = null;
    await this.protectMore(visible);
    if (this.current) this.current = { ...this.current, phase: "submitting" };
  }

  /** "not now": closed with no attempt; the duty stays pending and its marker stays. Not while the answer is on its
   *  way (the server refuses it then, and the button is disabled). */
  async abandon(): Promise<void> {
    const open = this.current;
    if (!open || open.phase !== "open") return;
    try {
      await this.transport.abandon({ administrationToken: open.card.administrationToken });
      this.drafts.set(open.card.administrationToken, null);
      this.current = null;
      this.regions = new Map();
      this.openedPrints = new Map();
      // Still due, under a new handle (the begin spent the old one).
      this.readDue();
    } catch (error) {
      this.current = { ...open, error: `couldn't close the check · ${REFUSED[codeOf(error) ?? ""] ?? messageOf(error)}` };
    }
    this.emit();
  }

  /** The answered card's "close". */
  close(): void {
    if (this.current?.phase !== "answered") return;
    this.current = null;
    this.regions = new Map();
    this.openedPrints = new Map();
    this.emit();
  }

  reason(): CheckReason | null {
    return (this.current?.reply?.reason as CheckReason | undefined) ?? null;
  }
}
