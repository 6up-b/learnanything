// The synthetic workspace's inline cold checks (spec §12.6; RD7): `checks.due_for` and the administration's calls,
// answered as the sidecar answers them, by hand (a fixture, never a model). On the harness's `?checks=1` page one check
// is due before the book's fifth section ("The gradient"); `?checks=open` also has an administration open on the
// paper's check, whose host passage is not on the desks (its card opens centred near the top, as after a restart).
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

export class FixtureChecks {
  private open: { token: string; commitmentId: string; veiled: CheckVeilRefDto[]; opened: CheckVeilRefDto[] } | null = null;
  private answered = new Set<string>();
  private count = 0;

  constructor(private readonly mode: "off" | "due" | "open") {
    if (mode === "open") this.open = { token: "fx_cad_open", commitmentId: PAPER_CHECK.commitmentId, veiled: [], opened: [] };
  }

  dueFor(input: { extractionId: string }): ChecksDueDto {
    if (this.mode === "off") return { version: 1, checks: [] };
    const rows = [BOOK_CHECK, PAPER_CHECK].filter((check) => check.host.extractionId === input.extractionId && !this.answered.has(check.commitmentId));
    return { version: 1, checks: rows.map((row) => ({ ...row, beingAnswered: this.open?.commitmentId === row.commitmentId })) } as ChecksDueDto;
  }

  /** The covered sections: the check's host section (the LO's primary path section). */
  private covered(commitmentId: string): { extractionId: string; prefix: string } {
    const check = commitmentId === PAPER_CHECK.commitmentId ? PAPER_CHECK : BOOK_CHECK;
    return { extractionId: check.host.extractionId, prefix: `${check.host.extractionId}_${check.host.sectionId}_` };
  }

  private protection(commitmentId: string, visible: CheckVisibleDto): CheckVeilRefDto[] {
    const covered = this.covered(commitmentId);
    const veiled: CheckVeilRefDto[] = [];
    for (const window of visible.windows ?? []) {
      if (window.kind === "source" || window.kind === "video") {
        const protectedSpan = (spanId: string | null | undefined) => Boolean(spanId && window.extractionId === covered.extractionId && spanId.startsWith(covered.prefix));
        for (const spanId of window.spanIds ?? []) {
          if (protectedSpan(spanId)) veiled.push({ group: "source passages", kind: "span", window_id: window.windowId, extraction_id: window.extractionId, span_id: spanId });
        }
        for (const figure of window.figures ?? []) {
          if (protectedSpan(figure.spanId)) veiled.push({ group: "figures", kind: "figure", window_id: window.windowId, figure_id: figure.figureId });
        }
        for (const noteId of window.noteIds ?? []) veiled.push({ group: "notes", kind: "note", window_id: window.windowId, note_id: noteId });
        continue;
      }
      veiled.push({ group: windowGroup(window.kind), kind: "window", window_id: window.windowId, window_kind: window.kind,
        ...(window.padBlockIds?.length ? { pad_block_ids: window.padBlockIds } : {}) });
    }
    if (visible.companionOpen) veiled.push({ group: "the companion", kind: "companion", exchange_ids: [...(visible.companionExchangeIds ?? [])] });
    return veiled;
  }

  private card(commitmentId: string, token: string): CheckCardDto {
    const open = this.open;
    return {
      version: 1, administrationToken: token, commitmentId, itemRef: `fx_pi_${commitmentId}`, contractHash: "fx_contract", cold: true, state: "open",
      protection: { veilSetId: `fx_cvs_${this.count}`, method: "structural+notes_by_default", veiled: open?.veiled ?? [], opened: open?.opened ?? [],
        groups: [...new Set((open?.veiled ?? []).map((ref) => ref.group))] },
      prompt: { prompt: PROMPTS[commitmentId] ?? "" },
      practiceSession: { sessionId: "fx_ps_1" } as never,
    };
  }

  begin(input: { commitmentId: string; visible: CheckVisibleDto }): CheckCardDto {
    if (this.open) throw { code: "administration_open", message: "Another check is open; answer it or say not now first.", retryable: false };
    this.count += 1;
    this.open = { token: `fx_cad_${this.count}`, commitmentId: input.commitmentId, veiled: this.protection(input.commitmentId, input.visible), opened: [] };
    return this.card(input.commitmentId, this.open.token);
  }

  protectMore(input: { administrationToken: string; visible: CheckVisibleDto }): { veilAdditions: CheckVeilRefDto[] } {
    const open = this.open;
    if (!open || open.token !== input.administrationToken) throw { code: "administration_closed", message: "That check is closed.", retryable: false };
    const known = new Set(open.veiled.map((ref) => JSON.stringify(ref)));
    const additions = this.protection(open.commitmentId, input.visible).filter((ref) => !known.has(JSON.stringify(ref)));
    open.veiled.push(...additions);
    return { veilAdditions: additions };
  }

  expose(input: { administrationToken: string; ref: CheckVeilRefDto }): { protectionStatus: { exposure: unknown[]; coldNow: boolean } } {
    const open = this.open;
    if (!open || open.token !== input.administrationToken) throw { code: "administration_closed", message: "That check is closed.", retryable: false };
    open.opened.push(input.ref);
    // A covered passage states what the answer says (the overlap primes the item); anything else says nothing of it.
    const primes = open.opened.some((ref) => ref.kind === "span");
    return { protectionStatus: { exposure: open.opened.map((ref) => ({ kind: "opened_veil", ref })), coldNow: !primes } };
  }

  submit(input: { administrationToken: string; submissionId: string; answerMd: string }) {
    const open = this.open;
    if (!open || open.token !== input.administrationToken) throw { code: "administration_closed", message: "That check is closed.", retryable: false };
    const cold = !open.opened.some((ref) => ref.kind === "span");
    this.answered.add(open.commitmentId);
    const commitmentId = open.commitmentId;
    this.open = null;
    return { version: 1, administrationToken: input.administrationToken, attemptId: `fx_at_${this.count}`, cold, reason: cold ? "on_your_own" : "primed",
      feedbackMd: FEEDBACK[commitmentId] ?? "" };
  }

  abandon(input: { administrationToken: string }): Record<string, never> {
    if (this.open?.token === input.administrationToken) this.open = null;
    return {};
  }

  openInline(): { administration: CheckCardDto | null } {
    if (!this.open) return { administration: null };
    if (!this.open.veiled.length) this.open.veiled = [{ group: "pads", kind: "window", window_id: "fx_w_pads", window_kind: "pad_stack" }];
    return { administration: this.card(this.open.commitmentId, this.open.token) };
  }
}
