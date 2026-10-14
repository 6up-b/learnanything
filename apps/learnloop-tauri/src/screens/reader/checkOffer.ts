// One rule for whether the Reader offers a quick check (reading-hardening,
// part 2). Codex found, five times, one more path that offered a section's
// check on a resume before the learner read anything: the text view's
// section-break button while the original PDF's manifest was pending, the
// text view's 70 % rule after the manifest failed or was unavailable, an
// auto-authored check the text view opened at once. Every path now asks this
// one predicate: the text view's section-break buttons, the guide's cards (and
// the rail badge counting them), the original PDF's section-break offer, the
// manifest-pending and manifest-error/unavailable fallbacks, auto-authored
// checks, and RW1a's passage-scoped quick check.
//
// The rule: a check left from an earlier visit that the Reader placed the
// learner at (a resume, a reading-history resume, a jump) is offered only once
// the learner has read in this visit: their own movement of the page, or
// playback that moves on (`readingMoved`, reset by every placement). A section
// the learner reaches by reading in this visit follows the normal rules, which
// for a check after a section are: in the original PDF, the reading position's
// page reaches the section's last page (D22); elsewhere, 70 % of the section.
// While the original is still on its way, nothing is offered: the surface the
// section is read on is not known yet. Once offered in a visit a check stays
// offered (pinned) until it is answered or set aside.

export type CheckSurface = "pdf" | "text" | "watch" | "loading";

export type ReadingPhase = "before_section" | "during_section" | "after_section";

/** A section's quick check: written by the owner's placement or by LearnLoop
 *  (auto-authored checks are written after most of a section and placed
 *  `after_section`). */
export interface SectionCheckOffer {
  kind: "section";
  /** The check's phase; `null` when the section has none. */
  readingPhase: ReadingPhase | null;
  /** Quick checks can be offered at all (prompts on, a live source). */
  available: boolean;
  /** Answered to completion or set aside. */
  settled: boolean;
  /** Offered earlier this visit, or asked for by the learner ("quick check
   *  →"): it stays until answered or set aside. */
  pinned: boolean;
  /** Where the section is relative to the reading position. */
  position: "behind" | "current" | "ahead";
  /** The learner's own movement or playback since the Reader last placed the
   *  page (an open, a resume, a jump). */
  readingMoved: boolean;
  /** What the section is read on; `loading` while the original PDF's manifest
   *  is still being asked for. A manifest that failed or is unavailable reads
   *  as `text`. */
  surface: CheckSurface;
  /** How far into the current section the reading marker stands (0..1). */
  progress: number;
  /** The original PDF only: whether the reading position's page reached the
   *  section's last page; `null` without page information. */
  atLastPage: boolean | null;
  /** The share of the current section its first passage is (0..1]. */
  firstPassageShare: number;
}

/** RW1a's passage-scoped quick check, offered on the reconnect line of an
 *  open inquiry the learner raised in this visit (a return to it, a branch
 *  marked done). */
export interface PassageCheckOffer {
  kind: "passage";
  raisedThisVisit: boolean;
  inquiryOpen: boolean;
  /** Skim mode: nothing proactive. */
  muted: boolean;
}

export type CheckOfferInput = SectionCheckOffer | PassageCheckOffer;

export type CheckOfferReason =
  | "offered"
  | "pinned"
  | "no_check"
  | "unavailable"
  | "settled"
  | "surface_loading"
  | "ahead"
  | "not_read_this_visit"
  | "not_at_its_point"
  | "not_raised"
  | "inquiry_closed"
  | "muted";

export interface CheckOfferDecision {
  offer: boolean;
  reason: CheckOfferReason;
}

const DURING_SECTION_AT = 0.45;
const AFTER_SECTION_AT = 0.7;
const BEFORE_SECTION_UNTIL = 0.3;

function decide(offer: boolean, reason: CheckOfferReason): CheckOfferDecision {
  return { offer, reason };
}

/** Whether this check may be offered now, and why (or why not). Pure. */
export function checkOffer(input: CheckOfferInput): CheckOfferDecision {
  if (input.kind === "passage") {
    if (input.muted) return decide(false, "muted");
    if (!input.raisedThisVisit) return decide(false, "not_raised");
    if (!input.inquiryOpen) return decide(false, "inquiry_closed");
    return decide(true, "offered");
  }
  if (!input.available) return decide(false, "unavailable");
  if (input.readingPhase === null) return decide(false, "no_check");
  if (input.settled) return decide(false, "settled");
  if (input.pinned) return decide(true, "pinned");
  // The original is on its way: the section's own rule is not known yet.
  if (input.surface === "loading") return decide(false, "surface_loading");
  if (input.position === "ahead") return decide(false, "ahead");
  if (input.position === "behind") {
    // Left behind the reading position: earned by reading, so offered once the
    // learner is reading in this visit (never on the open or a jump itself).
    return input.readingMoved ? decide(true, "offered") : decide(false, "not_read_this_visit");
  }
  if (input.readingPhase === "before_section") {
    const until = Math.max(BEFORE_SECTION_UNTIL, input.firstPassageShare);
    return input.progress <= until ? decide(true, "offered") : decide(false, "not_at_its_point");
  }
  if (input.readingPhase === "during_section") {
    return input.progress >= DURING_SECTION_AT ? decide(true, "offered") : decide(false, "not_at_its_point");
  }
  // After a section (auto-authored checks too): only for reading done in this visit.
  if (!input.readingMoved) return decide(false, "not_read_this_visit");
  const reached = input.surface === "pdf" && input.atLastPage !== null
    ? input.atLastPage
    : input.progress >= AFTER_SECTION_AT;
  return reached ? decide(true, "offered") : decide(false, "not_at_its_point");
}
