// The synthetic workspace's inline cold checks (spec §12.6; RD7): `checks.due_for` and the administration's calls,
// answered as the sidecar answers them, by hand (a fixture, never a model). On the harness's `?checks=1` page one check
// is due, hosted at the book's fifth section ("The gradient"): `checks.due_for` answers its opaque handle and nothing
// else, and the host is named only by the begun card; `?checks=open` also has an administration open on the paper's
// check, whose host passage is not on the desks (its card opens centred near the top, as after a restart).
// The protection set follows the owner's rule: every window but a source's text veiled whole, the companion when open,
// margin notes, and, in a source, the covered passages (the host section's) and their figures. Every call is recorded
// by the fake core. Project-authored text only.
import type { CheckCardDto, CheckVeilRefDto, CheckVisibleDto, ChecksDueDto } from "../../api/dto";
import { FIXTURE_SOURCES } from "./sources";

const { book, paper } = FIXTURE_SOURCES;

const BOOK_CHECK = { commitmentId: "fx_cm_grad", loId: "fx_lo_grad", due: "2026-11-22T00:00:00Z",
  host: { extractionId: book.extractionId, sectionId: "s5", spanId: `${book.extractionId}_s5_1` }, provenance: { via: "ready_check" } };
const PAPER_CHECK = { commitmentId: "fx_cm_scaled", loId: "fx_lo_scaled", due: "2026-11-22T00:00:00Z",
  host: { extractionId: paper.extractionId, sectionId: "s2", spanId: `${paper.extractionId}_s2_1` }, provenance: { via: "test_me_later" } };

const PROMPTS: Record<string, string> = {
  fx_cm_grad: "For a softmax output $p$ and true class $y$, with loss $L = -\\ln p_y$: what is $\\partial L/\\partial h_k$, and why does it come out so simple?",
  fx_cm_scaled: "Why are the attention scores divided by $\\sqrt{d_k}$ before the softmax, and what goes wrong without it?",
};
const FEEDBACK: Record<string, string> = {
  fx_cm_grad: "Right: $\\partial L/\\partial h_k = p_k - [k = y]$, and you named why (the log cancels the exponential).",
  fx_cm_scaled: "Right: without the scaling the scores grow with $d_k$ and the softmax saturates.",
};

function windowGroup(kind: string): string {
  if (kind === "pad_stack" || kind === "pad" || kind === "ink") return "pads";
  if (kind === "thread" || kind === "history" || kind === "companion") return "threads";
  if (kind === "lesson") return "lessons";
  return "windows";
}

/** What opening a ref shows can be measured against the answer key (a passage, a pad's text, a thread's exchanges);
 *  a note, a figure, a lesson, a history with no exchanges or a region the checks do not describe cannot. */
function measured(ref: CheckVeilRefDto): boolean {
  if (ref.kind === "span") return true;
  if (ref.kind === "window") return ref.window_kind === "pad_stack" || ref.window_kind === "pad";
  if (ref.kind === "companion") return Array.isArray(ref.exchange_ids) && ref.exchange_ids.length > 0;
  return false;
}

/** A handle as the sidecar mints one: a keyed hash of (commitment, administrations so far), naming neither. */
function handleOf(commitmentId: string, generation: number): string {
  let hash = 0x811c9dc5;
  for (const ch of `fx-key|${commitmentId}|${generation}`) hash = Math.imul(hash ^ ch.charCodeAt(0), 0x01000193) >>> 0;
  let second = hash;
  for (const ch of `${generation}|${commitmentId}|fx-salt`) second = Math.imul(second ^ ch.charCodeAt(0), 0x01000193) >>> 0;
  return `chk_${hash.toString(16).padStart(8, "0")}${second.toString(16).padStart(8, "0")}`;
}

interface Open {
  token: string;
  commitmentId: string;
  requestId: string | null;
  veiled: CheckVeilRefDto[];
  opened: CheckVeilRefDto[];
  exposures: Map<string, { coldNow: boolean; measured: boolean }>;
  unmeasured: boolean;
  submissionId: string | null;
}

export class FixtureChecks {
  private open: Open | null = null;
  private answered = new Set<string>();
  /** Closed administrations by their begin request (a late retry is refused with what became of it). */
  private closed = new Map<string, { state: string; outcome: string | null }>();
  /** Saved outcomes by submission id (a retry returns the first). */
  private outcomes = new Map<string, Record<string, unknown>>();
  private count = 0;
  private revision = 0;
  /** Administrations so far, per commitment (a begin spends the handle). */
  private generations = new Map<string, number>();

  constructor(private readonly mode: "off" | "due" | "due-paper" | "open") {
    if (mode === "open") {
      this.open = this.fresh("fx_cad_open", PAPER_CHECK.commitmentId, null);
      this.generations.set(PAPER_CHECK.commitmentId, 1);
    }
  }

  /** The due checks: the book's, and the paper's when an administration holds it. */
  private dueRows(): Array<typeof BOOK_CHECK | typeof PAPER_CHECK> {
    if (this.mode === "off") return [];
    const rows = this.mode === "open" ? [BOOK_CHECK, PAPER_CHECK] : this.mode === "due-paper" ? [PAPER_CHECK] : [BOOK_CHECK];
    return rows.filter((check) => !this.answered.has(check.commitmentId));
  }

  private handle(commitmentId: string): string {
    return handleOf(commitmentId, this.generations.get(commitmentId) ?? 0);
  }

  private fresh(token: string, commitmentId: string, requestId: string | null): Open {
    return { token, commitmentId, requestId, veiled: [], opened: [], exposures: new Map(), unmeasured: false, submissionId: null };
  }

  dueFor(): ChecksDueDto {
    const rows = this.dueRows().map((row) => ({ handle: this.handle(row.commitmentId), beingAnswered: this.open?.commitmentId === row.commitmentId }));
    return { version: 1, checks: rows.sort((a, b) => a.handle.localeCompare(b.handle)) };
  }

  /** The check a handle names now (or the open one's spent handle: a lost reply's retry), else null. */
  private resolve(handle: string): string | null {
    for (const row of this.dueRows()) {
      if (this.handle(row.commitmentId) === handle) return row.commitmentId;
      const spent = (this.generations.get(row.commitmentId) ?? 0) - 1;
      if (this.open?.commitmentId === row.commitmentId && spent >= 0 && handleOf(row.commitmentId, spent) === handle) return row.commitmentId;
    }
    return null;
  }

  /** The covered sections: the check's host section (the LO's primary path section). */
  private covered(commitmentId: string): { extractionId: string; prefix: string } {
    const check = commitmentId === PAPER_CHECK.commitmentId ? PAPER_CHECK : BOOK_CHECK;
    return { extractionId: check.host.extractionId, prefix: `${check.host.extractionId}_${check.host.sectionId}_` };
  }

  private protection(commitmentId: string, visible: CheckVisibleDto): CheckVeilRefDto[] {
    const covered = this.covered(commitmentId);
    const veiled: CheckVeilRefDto[] = [];
    const add = (ref: CheckVeilRefDto) => veiled.push({ ...ref, measured: measured(ref) });
    for (const window of visible.windows ?? []) {
      if (window.kind === "source" || window.kind === "video") {
        const protectedSpan = (spanId: string | null | undefined) => Boolean(spanId && window.extractionId === covered.extractionId && spanId.startsWith(covered.prefix));
        for (const spanId of window.spanIds ?? []) {
          if (protectedSpan(spanId)) add({ group: "source passages", kind: "span", window_id: window.windowId, extraction_id: window.extractionId, span_id: spanId });
        }
        for (const figure of window.figures ?? []) {
          if (protectedSpan(figure.spanId)) add({ group: "figures", kind: "figure", window_id: window.windowId, figure_id: figure.figureId });
        }
        for (const noteId of window.noteIds ?? []) add({ group: "notes", kind: "note", window_id: window.windowId, note_id: noteId });
        continue;
      }
      add({ group: windowGroup(window.kind), kind: "window", window_id: window.windowId, window_kind: window.kind,
        ...(window.padBlockIds?.length ? { pad_block_ids: window.padBlockIds } : {}) });
    }
    if (visible.companionOpen) add({ group: "the companion", kind: "companion", exchange_ids: [...(visible.companionExchangeIds ?? [])] });
    return veiled;
  }

  private standing(open: Open): CheckVeilRefDto[] {
    const opened = new Set(open.opened.map((ref) => JSON.stringify(ref)));
    return open.veiled.filter((ref) => !opened.has(JSON.stringify(ref)));
  }

  private card(open: Open, replayed = false): CheckCardDto {
    return {
      version: 1, administrationToken: open.token, commitmentId: open.commitmentId, itemRef: `fx_pi_${open.commitmentId}`, contractHash: "fx_contract", cold: true, state: "open",
      protection: { veilSetId: `fx_cvs_${this.count}`, method: "structural+notes_by_default", veiled: open.veiled, opened: open.opened, standing: this.standing(open),
        groups: [...new Set(open.veiled.map((ref) => ref.group))] },
      prompt: { practiceItemId: `fx_pi_${open.commitmentId}`, prompt: PROMPTS[open.commitmentId] ?? "",
        presentation: { practiceItemId: `fx_pi_${open.commitmentId}`, blocks: [{ kind: "prompt", markdown: PROMPTS[open.commitmentId] ?? "", label: null }] } },
      practiceSession: { sessionId: "fx_ps_1" } as never,
      submissionId: open.submissionId, eligibility: null, revision: this.revision, ...(replayed ? { replayed: true } : {}),
      host: (open.commitmentId === PAPER_CHECK.commitmentId ? PAPER_CHECK : BOOK_CHECK).host,
    };
  }

  private closedError(): never {
    throw { code: "administration_closed", message: "That check is closed.", retryable: false };
  }

  begin(input: { requestId?: string; handle: string; visible: CheckVisibleDto }): CheckCardDto {
    const done = input.requestId ? this.closed.get(input.requestId) : undefined;
    if (done) throw { code: "administration_closed", message: "That check is closed.", retryable: false, details: done };
    const commitmentId = this.resolve(input.handle);
    if (!commitmentId) throw { code: "check_unknown", message: "This check changed since the desk last looked. Look again.", retryable: false };
    if (this.open) {
      // A lost reply's retry (or another click) for the same commitment gets its card back.
      if (this.open.commitmentId === commitmentId) return this.card(this.open, true);
      throw { code: "administration_open", message: "Another check is open; answer it or say not now first.", retryable: false,
        details: { administrationToken: this.open.token, commitmentId: this.open.commitmentId } };
    }
    this.count += 1;
    this.revision += 1;
    this.generations.set(commitmentId, (this.generations.get(commitmentId) ?? 0) + 1);
    this.open = this.fresh(`fx_cad_${this.count}`, commitmentId, input.requestId ?? null);
    this.open.veiled = this.protection(commitmentId, input.visible);
    return this.card(this.open);
  }

  protectMore(input: { administrationToken: string; visible: CheckVisibleDto }): { veilAdditions: CheckVeilRefDto[]; standing: CheckVeilRefDto[]; revision: number } {
    const open = this.open;
    if (!open || open.token !== input.administrationToken) this.closedError();
    const known = new Set(open.veiled.map((ref) => JSON.stringify(ref)));
    const additions = this.protection(open.commitmentId, input.visible).filter((ref) => !known.has(JSON.stringify(ref)));
    open.veiled.push(...additions);
    if (additions.length) this.revision += 1;
    return { veilAdditions: additions, standing: this.standing(open), revision: this.revision };
  }

  expose(input: { administrationToken: string; ref: CheckVeilRefDto; kind?: string; exposureId?: string }) {
    const open = this.open;
    if (!open || open.token !== input.administrationToken) this.closedError();
    if (open.submissionId && this.outcomes.has(open.submissionId)) throw { code: "submission_in_flight", message: "The answer is on its way.", retryable: false };
    const again = input.exposureId ? open.exposures.get(input.exposureId) : undefined;
    if (!again) {
      const unmeasured = input.kind === "left" || input.ref.measured === false || input.ref.kind === "surface";
      if (input.kind !== "left") open.opened.push(input.ref);
      if (unmeasured) open.unmeasured = true;
      // A covered passage states what the answer says (the overlap primes the item); an unmeasured opening always
      // counts as practice; anything else measured says nothing of it.
      const coldNow = !open.unmeasured && !open.opened.some((ref) => ref.kind === "span");
      if (input.exposureId) open.exposures.set(input.exposureId, { coldNow, measured: !unmeasured });
    }
    const status = input.exposureId ? open.exposures.get(input.exposureId)! : { coldNow: !open.unmeasured, measured: true };
    return { protectionStatus: { exposure: open.opened.map((ref) => ({ kind: "opened_veil", ref })), coldNow: status.coldNow, measured: status.measured, eligibility: null } };
  }

  submit(input: { administrationToken: string; submissionId: string; answerMd: string; veilsRevision?: number }) {
    const saved = this.outcomes.get(input.submissionId);
    if (saved) return saved;
    const open = this.open;
    if (!open || open.token !== input.administrationToken) this.closedError();
    if (typeof input.veilsRevision === "number" && input.veilsRevision < this.revision) {
      throw { code: "veils_stale", message: "New veils were added; apply them and send again.", retryable: true };
    }
    const primedBySpan = open.opened.some((ref) => ref.kind === "span");
    const byNote = open.opened.some((ref) => ref.kind === "note");
    const cold = !primedBySpan && !open.unmeasured;
    this.answered.add(open.commitmentId);
    const commitmentId = open.commitmentId;
    if (open.requestId) this.closed.set(open.requestId, { state: "submitted", outcome: cold ? "on_your_own" : "primed" });
    this.open = null;
    const outcome = { version: 1, administrationToken: input.administrationToken, attemptId: `fx_at_${this.count}`, cold, reason: cold ? "on_your_own" : "primed",
      ...(!cold && !primedBySpan ? { primedBy: byNote ? "unmeasured_note" : "unmeasured" } : {}), eligibility: null,
      feedbackMd: FEEDBACK[commitmentId] ?? "" };
    this.outcomes.set(input.submissionId, outcome);
    return outcome;
  }

  abandon(input: { administrationToken: string }): Record<string, never> {
    if (this.open?.token === input.administrationToken) {
      if (this.open.requestId) this.closed.set(this.open.requestId, { state: "abandoned", outcome: null });
      this.open = null;
    }
    return {};
  }

  openInline(): { administration: CheckCardDto | null } {
    if (!this.open) return { administration: null };
    if (!this.open.veiled.length) this.open.veiled = [{ group: "pads", kind: "window", window_id: "fx_w_pads", window_kind: "pad_stack", measured: true }];
    return { administration: this.card(this.open) };
  }
}
