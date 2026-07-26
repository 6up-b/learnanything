"""A6: the system must be able to say it was wrong.

``spec_diagnostic_augmentation_v1.md`` §2 A6 (plan item 1.4). v1 already gives
the learner a contest action (§5.6 ``doesnt_fit``) and already gives the system a
demotion lifecycle (``misconception_disposition_events``, migration 116). The two
were never connected in the learner's direction: a diagnosis could be asserted to
the learner, retired later as a misdiagnosis, and the learner would keep holding a
false claim about their own mind. This module is the connection, in two halves:

  CAPTURE (``resolve_belief_reference``) — normalizes the belief a presented claim
  is *about*, so ``hypothesis_events`` rows carry an explicit belief reference and
  the as-shown wording. Called from ``hypothesis_claims.present_claims``, the one
  choke point every Tauri claim surface goes through.

  NARRATION (``surfaced_belief_corrections``) — projects the join of surfaced
  presentations against disposition events into learner-facing withdrawal
  entries. Read-only and deterministic: the feed is rebuilt on every read
  (``learner_review_feed``), so idempotency has to come from the entry's identity
  rather than from an emission ledger. One entry per disposition EVENT, keyed on
  that event's id, regardless of how many times the belief was shown.

Standing constraint 6 is why the capture half exists at all: which claims a
learner actually saw cannot be reconstructed after the fact, so the flag is
written at presentation time and never backfilled.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository


# ── Which claims are BELIEFS ────────────────────────────────────────────────
#
# A6 apologises for diagnoses about the learner's mind, not for estimates,
# schedule choices, or ledger facts. A recomputed mastery number is a
# `recalibration` entry (§4.9); a withdrawn regrade is a ledger correction. Only
# a claim that named a false belief can be a misdiagnosis, so this map is
# deliberately narrow and grows one claim_type at a time.
BELIEF_CLAIM_TYPES: Mapping[str, str] = {
    "misconception": "misconception",
}

# Keys a caller may use to name the misconception inside a structured claim_ref.
# ReviewScreen sends a bare id; FeedbackScreen sends {"attemptId", "misconceptionId"}
# — camelCase survives the sidecar because `claim_ref` is typed `Any` and is never
# alias-converted. Both snake and camel spellings are accepted so a Python caller
# reads naturally and the UI keeps working unchanged.
_BELIEF_ID_KEYS: tuple[str, ...] = (
    "misconceptionId",
    "misconception_id",
    "beliefId",
    "belief_id",
    "id",
)


# ── The typed withdrawal vocabulary ─────────────────────────────────────────
#
# A6 names exactly four things the learner may be told: contradicted by trace /
# superseded / adjudicated / retired as misdiagnosed. Migration 116's
# `disposition` CHECK admits only ('demoted', 'superseded') and its table is
# guarded by no-update/no-delete triggers, so the four live in the `reason`
# column with `disposition` as the coarse arm (see migration 132's note). This
# module is the single validator; nothing else may invent a reason.
WITHDRAWAL_REASONS: tuple[str, ...] = (
    "contradicted_by_trace",
    "superseded",
    "adjudicated",
    "retired_misdiagnosed",
)

# `superseded` is the only reason that maps to the `superseded` disposition arm;
# the other three are demotions. Deriving the arm here keeps callers from having
# to know migration 116's enum at all.
_DISPOSITION_FOR_REASON: Mapping[str, str] = {
    "contradicted_by_trace": "demoted",
    "superseded": "superseded",
    "adjudicated": "demoted",
    "retired_misdiagnosed": "demoted",
}

# Legacy free-text reasons, mapped EXPLICITLY rather than by substring guesswork.
# Migration 116 backfilled exactly one, and its text contains the word "trace"
# while its meaning is the opposite of a trace contradiction: the first-error
# promotion had no durable authority to begin with, i.e. it was a misdiagnosis.
# A `"trace" in reason` heuristic would have told every one of those learners
# their own work refuted a claim it never touched.
_LEGACY_REASON_ALIASES: Mapping[str, str] = {
    "first_error_trace_had_no_durable_promotion_authority": "retired_misdiagnosed",
}

# The withdrawal clause, per typed reason. Terse and in the register of the
# existing system-authored entries ("estimates recomputed — your evidence
# unchanged"). Every one of these leads with the word "withdrawn": A6 forbids a
# softened restatement standing in for the retraction.
WITHDRAWAL_WORDING: Mapping[str, str] = {
    "contradicted_by_trace": (
        "That is withdrawn — your own work contradicted it."
    ),
    "superseded": (
        "That is withdrawn — a better-supported diagnosis replaced it."
    ),
    "adjudicated": (
        "That is withdrawn — a review of the diagnosis found it wrong."
    ),
    "retired_misdiagnosed": (
        "That is withdrawn — it was a misdiagnosis and should not have been "
        "shown to you."
    ),
}

FEED_ENTRY_KIND = "belief_withdrawn"


class SurfacedBeliefError(ValueError):
    pass


@dataclass(frozen=True)
class BeliefReference:
    """The belief a presented claim is about, normalized at capture time."""

    kind: str
    id: str


@dataclass(frozen=True)
class SurfacedBeliefWithdrawal:
    """One learner-visible retraction of one belief the learner was shown.

    ``withdrawn_claim_text`` is what A6 calls "the words the learner was shown".
    ``claim_text_source`` records whether that is literally true: ``as_shown``
    means it came off the presentation row, ``current_statement`` means the
    presentation predates capture (migration 132) and the live statement is
    standing in — an honesty marker, not decoration.
    """

    disposition_event_id: str
    belief_kind: str
    belief_id: str
    at: str
    disposition: str
    raw_reason: str
    withdrawal_reason: str
    withdrawn_claim_text: str
    claim_text_source: str
    statement: str
    surfaced_at: str | None
    surfaced_on: str | None
    learning_object_id: str | None
    facet_ids: tuple[str, ...]
    replacement_belief_id: str | None
    replacement_statement: str | None

    @property
    def entry_id(self) -> str:
        # Keyed on the disposition EVENT, which is unique and belongs to exactly
        # one belief. That is the whole idempotency argument: rebuilding the feed
        # regenerates the same id, and a belief shown five times still withdraws
        # once per disposition.
        return f"{FEED_ENTRY_KIND}:{self.disposition_event_id}"


def resolve_belief_reference(
    claim_type: str, claim_ref: Any
) -> BeliefReference | None:
    """Normalize (claim_type, claim_ref) into the belief the claim asserts.

    Returns ``None`` for every non-belief claim — that is the common case and is
    not an error. Accepts the two shapes production actually sends (bare id
    string, mapping carrying a misconception id) plus an already-canonicalized
    JSON string, because ``canonical_claim_ref`` may have run first.
    """

    kind = BELIEF_CLAIM_TYPES.get(str(claim_type))
    if kind is None:
        return None

    value: Any = claim_ref
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.startswith("{"):
            # A pre-canonicalized structured ref. Parsing it here is what keeps
            # the Feedback surface joinable; failing to parse is not fatal, the
            # raw string is still a usable key.
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                return BeliefReference(kind=kind, id=text)
        else:
            return BeliefReference(kind=kind, id=text)

    if isinstance(value, Mapping):
        for key in _BELIEF_ID_KEYS:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return BeliefReference(kind=kind, id=candidate.strip())
    return None


def mark_belief_surfaced(
    repository: Repository,
    *,
    belief_id: str,
    claim_text: str | None,
    surface: str,
    belief_kind: str = "misconception",
    clock: Clock | None = None,
) -> str | None:
    """Flag a belief as shown on a surface that does not dispatch typed claims.

    ``present_claims`` covers every Tauri ClaimSurface mount (Feedback's
    diagnosis card, Review's working hypotheses). Repair does not: it renders
    ``case.statement`` straight into the page, and A6's scope guard is only as
    good as the set of surfaces that report to it.

    Idempotent and O(1): the row id is a deterministic digest over
    (kind, id, surface, wording), so re-reads of a polled screen collapse onto
    the same row and the FIRST exposure timestamp stands. Returns ``None`` when
    there is no wording to record — a claim we cannot quote is a claim A6 cannot
    withdraw, and inventing a row for it would only produce an unnameable
    apology later.
    """

    text = str(claim_text or "").strip()
    if not text or not str(belief_id).strip():
        return None
    digest = hashlib.sha256(
        "".join([belief_kind, str(belief_id), surface, text]).encode("utf-8")
    ).hexdigest()[:32]
    return repository.record_surfaced_belief_presentation(
        id=f"surfaced_{digest}",
        belief_kind=belief_kind,
        belief_id=str(belief_id),
        claim_text=text,
        surface=surface,
        claim_type=belief_kind,
        clock=clock,
    )


def record_belief_withdrawal(
    repository: Repository,
    *,
    belief_id: str,
    reason: str,
    replacement_belief_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Withdraw a belief, with a reason from A6's four-value vocabulary.

    The disposition arm is derived, never passed: a caller that had to choose
    between 'demoted' and 'superseded' would eventually record a supersession as
    a demotion and the learner would be told the wrong thing about why.

    ``replacement_belief_id`` is recorded, never substituted. A6: "never quietly
    re-state it as a weaker belief instead" — the successor rides ALONGSIDE the
    retraction so the feed narrates the withdrawal first and the replacement
    second.
    """

    typed = str(reason).strip()
    if typed not in WITHDRAWAL_REASONS:
        raise SurfacedBeliefError(
            f"withdrawal reason must be one of {WITHDRAWAL_REASONS}, got {reason!r}"
        )
    if replacement_belief_id is not None and replacement_belief_id == belief_id:
        # Replacing a belief with itself is the in-place rewrite A6 forbids: it
        # would let a weakened statement inherit the retracted claim's identity
        # and leave nothing to apologise for.
        raise SurfacedBeliefError("a belief cannot supersede itself")
    return repository.insert_misconception_disposition(
        misconception_id=belief_id,
        disposition=_DISPOSITION_FOR_REASON[typed],
        reason=typed,
        replacement_misconception_id=replacement_belief_id,
        clock=clock,
    )


def typed_withdrawal_reason(disposition: str, reason: str | None) -> str:
    """Map a stored (disposition, reason) pair onto A6's four values.

    New writes go through ``record_belief_withdrawal`` and store the typed token
    directly, so this is a no-op for them. Legacy rows resolve through the
    explicit alias table and then fall back on the coarse disposition arm — never
    on substring matching against free text.
    """

    text = str(reason or "").strip()
    if text in WITHDRAWAL_REASONS:
        return text
    alias = _LEGACY_REASON_ALIASES.get(text)
    if alias is not None:
        return alias
    if str(disposition) == "superseded":
        return "superseded"
    return "retired_misdiagnosed"


def _withdrawal_statement(
    *, claim_text: str, withdrawal_reason: str, replacement_statement: str | None
) -> str:
    """Name the claim, then withdraw it, then (only then) mention a successor.

    Order is load-bearing. A6's third bullet — "never quietly re-state it as a
    weaker belief instead" — is violated by any rendering in which the learner
    reads the replacement without reading the retraction, so the retraction
    clause is unconditional and always precedes the replacement clause.
    """

    clause = WITHDRAWAL_WORDING[withdrawal_reason]
    # Authored claim statements usually end in their own punctuation; adding a
    # second full stop outside the quote reads as a typo in the apology.
    quoted = f"“{claim_text}”" + ("" if claim_text.rstrip()[-1:] in ".!?" else ".")
    statement = f"We told you: {quoted} {clause}"
    if replacement_statement:
        statement += (
            " A separate claim now stands in its place — "
            f"“{replacement_statement}” — and the claim above is "
            "withdrawn regardless."
        )
    return statement


def surfaced_belief_corrections(
    repository: Repository,
) -> list[SurfacedBeliefWithdrawal]:
    """Every withdrawal the learner is owed, oldest first.

    The scope guard lives in the repository join: beliefs with no surfaced
    presentation produce no row, so retiring an internal provisional hypothesis
    stays housekeeping. A row whose claim can be named by neither the
    presentation nor the live belief is skipped — A6 requires naming the previous
    claim, and an entry that says "we withdrew something, we cannot say what" is
    the noise the scope guard exists to prevent.
    """

    corrections: list[SurfacedBeliefWithdrawal] = []
    for row in repository.surfaced_belief_withdrawals():
        as_shown = row.get("claim_text_as_shown")
        if as_shown:
            claim_text = str(as_shown)
            claim_text_source = "as_shown"
        elif row.get("current_statement"):
            claim_text = str(row["current_statement"])
            claim_text_source = "current_statement"
        else:
            continue
        withdrawal_reason = typed_withdrawal_reason(
            str(row["disposition"]), row.get("reason")
        )
        replacement_statement = row.get("replacement_statement")
        corrections.append(
            SurfacedBeliefWithdrawal(
                disposition_event_id=str(row["disposition_event_id"]),
                belief_kind="misconception",
                belief_id=str(row["belief_id"]),
                at=str(row["at"]),
                disposition=str(row["disposition"]),
                raw_reason=str(row.get("reason") or ""),
                withdrawal_reason=withdrawal_reason,
                withdrawn_claim_text=claim_text,
                claim_text_source=claim_text_source,
                statement=_withdrawal_statement(
                    claim_text=claim_text,
                    withdrawal_reason=withdrawal_reason,
                    replacement_statement=(
                        str(replacement_statement) if replacement_statement else None
                    ),
                ),
                surfaced_at=(
                    str(row["first_surfaced_at"])
                    if row.get("first_surfaced_at")
                    else None
                ),
                surfaced_on=(
                    str(row["last_surface"]) if row.get("last_surface") else None
                ),
                learning_object_id=(
                    str(row["learning_object_id"])
                    if row.get("learning_object_id")
                    else None
                ),
                facet_ids=tuple(row.get("facet_ids") or ()),
                replacement_belief_id=(
                    str(row["replacement_belief_id"])
                    if row.get("replacement_belief_id")
                    else None
                ),
                replacement_statement=(
                    str(replacement_statement) if replacement_statement else None
                ),
            )
        )
    return corrections
