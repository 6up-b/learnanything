"""A4 — contrast pairs (spec_measurement_efficiency_v1 §3.A4). Plan item 6.4.

THE HYPOTHESIS
--------------
"Two prompts differing in exactly one requirement. The *difference* in outcome
identifies the facet with the learner's general ability held constant, which is
why it buys more per minute than two independent items — it removes the nuisance
parameter instead of averaging over it." §3.A4's stated hypothesis:
*facet-level identifiability findings close; per-facet posterior variance falls
faster per question than on matched independent items.*

THE REVERT CRITERION, AND THE CODE THAT MEASURES IT
--------------------------------------------------
"*Revert if:* within-pair outcome differences are dominated by order effects —
check by randomizing which member is served first."

Two pieces ship together, because the criterion is unmeasurable without both:

* :func:`plan_contrast_pair_serving` performs the randomization at the one place
  the order is actually decided (the scheduler's queue) and records the draw,
  the seed, and whether the members ended up separated, in migration 143's
  ``contrast_pair_servings``;
* :func:`contrast_pair_order_effect` reads that store back and reports the
  outcome difference conditioned on serving order, plus the realized balance of
  the randomization itself. A randomization nobody audits is indistinguishable
  from a constant, and the whole control rests on it.

COMMISSIONED, NOT MERELY PERMITTED
----------------------------------
§3.A4: "``identifiability.analyze_identifiability`` already finds facet pairs no
instrument separates, and those findings become contrast-pair authoring
requests." :func:`commission_contrast_pairs` is that turn, and it follows
``services/contract_commissioning`` deliberately — same shape, same discipline:
a typed disposition per finding, deferrals kept **in the queue** with a reason
rather than dropped, and an ``as_dict()`` payload narrow enough to hand an
authoring model. A queue that silently omits its uncommissionable rows is how
§5.8.2's 18 coordination obligations went unnoticed for 43 attempts.

Not every finding is a contrast pair, and saying so is most of the value:

* check 1 (two facets always observed together) and check 3 (two planted
  profiles with identical ideal outcomes) are exactly what a pair separates;
* check 4 (capability confounding within one facet) is a *rung* problem — the
  remedy is an item at the isolated capability, which is item 5.1's commissioning
  path, not a pair;
* a ``coarsen_distinction`` finding says no assessment can separate the two AND
  the repairs are identical. Commissioning a pair there would manufacture a
  distinction D1 has already judged not worth having.

FOUR GATES, NOT FOUR SUGGESTIONS
--------------------------------
§3.A4 lists its non-triviality constraints as "all gates rather than guidance",
and :class:`ContrastPairGate` implements them at the ``row_transform`` seam every
other authoring gate rides:

1. **both members independently in the target difficulty band** — via the
   existing ``practice_generation._success_band_difficulty`` inversion, so the
   band means one thing in this vault;
2. **the manipulation changes the STRUCTURE of the correct answer**, never merely
   its values — checked by masking numerals out of both expected answers and
   requiring what remains to still differ;
3. **exactly one differing component**, declared, and symmetric across members;
4. the §3.0 persona clause (the belief-holder must fail exactly one member) which
   ``services/persona_gate`` already owns and this module does not duplicate.

The non-adjacency rule is a *serving* constraint, not an authoring one, so it
lives in :func:`plan_contrast_pair_serving` with the randomization.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.numeric import binomial_two_sided_p
from learnloop.services.discrimination_profiles import profiles_by_facet
from learnloop.db.repositories import Repository
from learnloop.services.identifiability import (
    IdentifiabilityFinding,
    analyze_identifiability,
    build_registry_view,
)
from learnloop.services.scoreboard import Metric
from learnloop.vault.models import LoadedVault, PracticeItem

CONTRAST_PAIR_VERSION = "contrast_pair_v1"


def pair_key(item_id: str, counterpart_id: str) -> str:
    """The shared key of one pair: the two ids, sorted, joined by ``|``.

    Derived rather than authored so both members compute the same key without
    either naming the pair — see ``persona_gate.contrast_pair_key``, which uses
    the same rule, for why an authored key can silently split a pair in two.
    """

    return "|".join(sorted((str(item_id), str(counterpart_id))))


# ---------------------------------------------------------------------------
# Commissioning: identifiability findings -> contrast-pair authoring requests
# ---------------------------------------------------------------------------


class ContrastPairDisposition(StrEnum):
    """What authoring may do about one identifiability finding.

    ``COMMISSION``
        The finding names two things a contrast pair can separate: two facets no
        criterion tells apart (check 1), or two planted profiles with identical
        ideal outcomes (check 3).
    ``DEFER_RUNG_COMMISSIONING``
        Check 4, capability confounding within one facet. Two capabilities are
        only ever observed together; the remedy is an item authored at the
        isolated capability, which ``services/contract_commissioning`` already
        queues. A pair here would buy a second observation of the confound.
    ``DEFER_COARSENING``
        A ``coarsen_distinction`` finding: no assessment separates the two AND
        the instructional repairs are identical. §D1 says review, never
        auto-merge — and commissioning an instrument to preserve a distinction
        D1 has proposed retiring is spending measurement on vocabulary debt.
    ``DEFER_MISSING_ANCHOR``
        Check 2: a required cell no criterion primarily observes. There is
        nothing to contrast *with* until one instrument exists; the remedy is
        rung-correct commissioning, then a pair.
    ``DEFER_NOT_PAIRABLE``
        Checks 5/6/7 (alternative recipes, component-vs-integration, single
        representation). Real findings with real remedies, none of which is two
        prompts differing in one requirement.
    """

    COMMISSION = "COMMISSION"
    DEFER_RUNG_COMMISSIONING = "DEFER_RUNG_COMMISSIONING"
    DEFER_COARSENING = "DEFER_COARSENING"
    DEFER_MISSING_ANCHOR = "DEFER_MISSING_ANCHOR"
    DEFER_NOT_PAIRABLE = "DEFER_NOT_PAIRABLE"

    @property
    def authorable(self) -> bool:
        return self is ContrastPairDisposition.COMMISSION


#: Typed reason per non-commissionable disposition. Closed vocabulary: a deferral
#: always says *why*, so the backlog is reviewable instead of an unexplained gap.
DEFERRAL_REASON: dict[ContrastPairDisposition, str] = {
    ContrastPairDisposition.DEFER_RUNG_COMMISSIONING: (
        "capability_confound_needs_isolating_item_not_a_pair"
    ),
    ContrastPairDisposition.DEFER_COARSENING: (
        "d1_proposes_coarsening_this_distinction_for_review"
    ),
    ContrastPairDisposition.DEFER_MISSING_ANCHOR: (
        "no_instrument_yet_exists_to_contrast_against"
    ),
    ContrastPairDisposition.DEFER_NOT_PAIRABLE: "finding_class_has_a_different_remedy",
}


def _disposition_for(finding: IdentifiabilityFinding) -> ContrastPairDisposition:
    """Total over the finding vocabulary. See the enum for the argument per arm."""

    if finding.kind == "coarsen_distinction":
        return ContrastPairDisposition.DEFER_COARSENING
    if finding.check == 2:
        return ContrastPairDisposition.DEFER_MISSING_ANCHOR
    if finding.check == 4:
        return ContrastPairDisposition.DEFER_RUNG_COMMISSIONING
    if finding.check in (1, 3) and len(finding.facet_ids) >= 2:
        return ContrastPairDisposition.COMMISSION
    return ContrastPairDisposition.DEFER_NOT_PAIRABLE


@dataclass(frozen=True)
class ContrastPairRequest:
    """One authoring request: separate these two things with one manipulation."""

    #: The finding verbatim — the identity, message and suggested action 3.1's
    #: reachability rows carry for the same reason: the request must be traceable
    #: back to the measurement that asked for it.
    finding: IdentifiabilityFinding
    disposition: ContrastPairDisposition
    #: Position in the commissioning queue. Carried so downstream ordering honours
    #: this queue instead of re-deriving a second priority.
    queue_rank: int
    subject_id: str | None
    reason: str | None
    #: §3.A5's third named consumer, and the reason A4 and A5 interlock: the
    #: authored discrimination profiles standing on this request's facets. Two
    #: profiles on one facet with the same ``fails_criteria`` are exactly the
    #: pair a manipulation should separate, and handing them to the authoring
    #: model turns "these two facets are non-identifiable" into "here is what a
    #: holder of each visibly produces — write the item on which they diverge".
    #: Empty when no item has authored a profile against them.
    profiles: tuple[dict[str, Any], ...] = ()

    @property
    def facet_ids(self) -> tuple[str, ...]:
        return self.finding.facet_ids

    def as_dict(self) -> dict[str, Any]:
        """Payload handed to the authoring model — the request, not the report."""

        payload: dict[str, Any] = {
            "target_key": self.finding.target_key,
            "check": self.finding.check,
            "detail": self.finding.detail,
            "facet_ids": list(self.finding.facet_ids),
            "capability": self.finding.capability,
            "disposition": str(self.disposition),
            "queue_rank": self.queue_rank,
            "subject_id": self.subject_id,
            "profiles": [dict(profile) for profile in self.profiles],
            "why": self.finding.message,
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        if self.disposition.authorable:
            payload["request"] = (
                "Author TWO prompts that differ in exactly one requirement, such "
                f"that a learner who holds {self.finding.facet_ids[0]} but not "
                f"{self.finding.facet_ids[1]} succeeds on one and fails the other. "
                "The manipulation must change the STRUCTURE of the correct answer "
                "(does a precondition hold, is the theorem applicable), never only "
                "its values. Both members must sit in the same target difficulty "
                "band. Set contrast_of and differing_component on BOTH members, and give at "
                "least one member a discrimination_profiles entry for the learner the pair is "
                "meant to catch — §3.0's gate has to plant that learner to check the pair "
                "separates, and a pair it cannot plant does not ship."
            )
        return payload


@dataclass(frozen=True)
class ContrastPairCommissionPlan:
    """The commissioning queue for A4, in finding order, deferrals included."""

    requests: tuple[ContrastPairRequest, ...]

    @property
    def commissioned(self) -> tuple[ContrastPairRequest, ...]:
        return tuple(request for request in self.requests if request.disposition.authorable)

    @property
    def deferred(self) -> tuple[ContrastPairRequest, ...]:
        return tuple(
            request for request in self.requests if not request.disposition.authorable
        )

    def for_subject(self, subject_id: str | None) -> tuple[ContrastPairRequest, ...]:
        return tuple(
            request for request in self.commissioned if request.subject_id == subject_id
        )

    def summary(self) -> dict[str, Any]:
        counts = {str(disposition): 0 for disposition in ContrastPairDisposition}
        for request in self.requests:
            counts[str(request.disposition)] += 1
        return {
            "queue_length": len(self.requests),
            "commissioned": len(self.commissioned),
            "deferred": len(self.deferred),
            "dispositions": counts,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": CONTRAST_PAIR_VERSION,
            "summary": self.summary(),
            "requests": [request.as_dict() for request in self.requests],
        }


def commission_contrast_pairs(
    vault: LoadedVault,
    repository: Repository | None = None,
    *,
    subject_id: str | None = None,
) -> ContrastPairCommissionPlan:
    """Turn identifiability findings into contrast-pair authoring requests.

    Runs the SAME ``analyze_identifiability`` the doctor runs, over the same
    registry view, so a request here and a finding there can never disagree about
    what is non-identifiable. Nothing is scheduled, persisted or applied: this is
    a derivation, exactly as ``contract_commissioning.commission_plan`` is, and
    the review ladder that governs what reaches a learner is unchanged.
    """

    from learnloop.services.identifiability import _load_misconception_records

    subject_ids: list[str | None] = (
        [subject_id] if subject_id else sorted(vault.subjects) or [None]
    )
    requests: list[ContrastPairRequest] = []
    rank = 0
    for sid in subject_ids:
        scoped = {
            lo.id
            for lo in vault.learning_objects.values()
            if sid is None or (lo.subjects and sid in lo.subjects)
        }
        records = (
            _load_misconception_records(vault, repository, scoped)
            if repository is not None
            else []
        )
        view = build_registry_view(vault, sid, misconception_records=records)
        authored_profiles = profiles_by_facet(vault)
        for finding in analyze_identifiability(view):
            disposition = _disposition_for(finding)
            requests.append(
                ContrastPairRequest(
                    finding=finding,
                    disposition=disposition,
                    queue_rank=rank,
                    subject_id=sid,
                    reason=DEFERRAL_REASON.get(disposition),
                    profiles=tuple(
                        profile
                        for facet in finding.facet_ids
                        for profile in authored_profiles.get(
                            vault.canonical_facet_id(str(facet)), ()
                        )
                    ),
                )
            )
            rank += 1
    return ContrastPairCommissionPlan(requests=tuple(requests))


# ---------------------------------------------------------------------------
# The authoring gates
# ---------------------------------------------------------------------------

#: How far outside its band a pair member's difficulty may sit. Deliberately
#: TIGHTER than `_RungGate._DIFFICULTY_BAND_TOLERANCE` (0.10, which tolerates one
#: intentionally-harder transfer item per batch): §3.A4 says "not 'one hard, one
#: easy'", and a pair whose members straddle the band measures nothing on the
#: easy one and wastes the contrast.
PAIR_BAND_TOLERANCE = 0.05  # decision parameter

#: Maximum difficulty gap BETWEEN the two members. The band check alone does not
#: catch a pair at opposite edges of a wide band, which is the same failure at a
#: smaller scale.
MAX_WITHIN_PAIR_DIFFICULTY_GAP = 0.15  # decision parameter


class PairGateReason(StrEnum):
    """Why a pair was refused. One arm per distinct authoring remedy."""

    PAIR_SEPARATES = "pair_separates"
    #: §3.A4 gate 1. One or both members sit outside the target band.
    MEMBER_OUTSIDE_DIFFICULTY_BAND = "member_outside_difficulty_band"
    #: §3.A4 gate 1, the within-pair form: both in band, but far apart in it.
    MEMBERS_DIFFER_IN_DIFFICULTY = "members_differ_in_difficulty"
    #: §3.A4 gate 2. The expected answers differ only in their numbers, so the
    #: manipulation changed values rather than the structure of the answer.
    MANIPULATION_CHANGES_ONLY_VALUES = "manipulation_changes_only_values"
    #: §3.A4's structural requirement. `contrast_of` with no
    #: `differing_component`, or two members declaring different components.
    DIFFERING_COMPONENT_MISSING_OR_ASYMMETRIC = "differing_component_missing_or_asymmetric"
    #: `contrast_of` names an item that is neither in this batch nor in the vault.
    COUNTERPART_UNRESOLVED = "counterpart_unresolved"
    #: More than two rows claim one pair key. §3.A4 is "two prompts differing in
    #: exactly one requirement"; a third makes "the difference" undefined. Judging
    #: the first two and recording their verdict against the rest would admit or
    #: refuse a row on evidence about a different item, so the whole group is
    #: refused with this reason instead.
    PAIR_OVERSUBSCRIBED = "pair_oversubscribed"


_DIGITS = "0123456789"


def answer_skeleton(text: str) -> str:
    """The expected answer with every numeral masked (§3.A4 gate 2's test).

    "The manipulation must change the *structure* of the correct answer — does a
    precondition hold, is the theorem applicable — never merely its values.
    Different numbers is a clone."

    Masking digits and comparing what remains is the cheapest honest test of
    that: two answers whose skeletons are identical differ only in values,
    whatever the prompts say. It under-fires (a structural change expressible
    purely in numbers — "3" vs "no solution" written as "0" — passes), which is
    the right direction for a gate that blocks: a false block costs an author a
    real pair, and §3.0's persona clause still has to separate the members
    afterwards.
    """

    from learnloop.services.diagnostic_gate import normalize_answer

    masked = "".join("#" if character in _DIGITS else character for character in str(text or ""))
    return normalize_answer(masked)


def _expected_text(payload: Mapping[str, Any]) -> str:
    expected = payload.get("expected_answer")
    if isinstance(expected, Mapping):
        return " ".join(str(value) for value in expected.values())
    return str(expected or "")


@dataclass(frozen=True)
class PairVerdict:
    """One pair's authoring verdict, and the numbers that decided it."""

    separates: bool
    reason: PairGateReason
    detail: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": CONTRAST_PAIR_VERSION,
            "separates": self.separates,
            "reason": str(self.reason),
            "detail": dict(self.detail),
        }


def judge_pair(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    *,
    difficulty_band: tuple[float, float] | None,
) -> PairVerdict:
    """§3.A4's three authoring gates over one pair's payloads.

    ``difficulty_band`` is the target's ``recommended_difficulty_band``, produced
    by ``practice_generation._success_band_difficulty`` — the existing inversion
    of the mastery channel's 2PL link, which is what §3.A4 says to enforce with.
    ``None`` (a route with no band, e.g. a hand-authored pair) skips gate 1 and
    says so in the detail rather than inventing a band to check against.
    """

    detail: dict[str, Any] = {
        "difficulty_band": list(difficulty_band) if difficulty_band else None,
        "difficulties": [first.get("difficulty"), second.get("difficulty")],
    }
    components = [first.get("differing_component"), second.get("differing_component")]
    if not all(isinstance(component, Mapping) for component in components):
        return PairVerdict(
            False, PairGateReason.DIFFERING_COMPONENT_MISSING_OR_ASYMMETRIC, detail
        )
    keys = {
        (str(component.get("facet") or ""), str(component.get("capability") or ""))
        for component in components  # type: ignore[union-attr]
    }
    detail["differing_components"] = sorted(f"{facet}#{capability}" for facet, capability in keys)
    if len(keys) != 1 or ("", "") in keys:
        return PairVerdict(
            False, PairGateReason.DIFFERING_COMPONENT_MISSING_OR_ASYMMETRIC, detail
        )
    if difficulty_band is not None:
        low, high = min(difficulty_band), max(difficulty_band)
        values: list[float] = []
        for payload in (first, second):
            declared = payload.get("difficulty")
            if declared is None:
                # A member with no declared difficulty cannot be shown to sit in
                # the band, and §3.A4 requires BOTH to sit in it independently.
                return PairVerdict(
                    False, PairGateReason.MEMBER_OUTSIDE_DIFFICULTY_BAND, detail
                )
            try:
                values.append(float(declared))
            except (TypeError, ValueError):
                return PairVerdict(
                    False, PairGateReason.MEMBER_OUTSIDE_DIFFICULTY_BAND, detail
                )
        for value in values:
            if not (low - PAIR_BAND_TOLERANCE <= value <= high + PAIR_BAND_TOLERANCE):
                return PairVerdict(
                    False, PairGateReason.MEMBER_OUTSIDE_DIFFICULTY_BAND, detail
                )
        gap = abs(values[0] - values[1])
        detail["difficulty_gap"] = round(gap, 6)
        if gap > MAX_WITHIN_PAIR_DIFFICULTY_GAP:
            return PairVerdict(False, PairGateReason.MEMBERS_DIFFER_IN_DIFFICULTY, detail)
    skeletons = [answer_skeleton(_expected_text(first)), answer_skeleton(_expected_text(second))]
    detail["answer_skeletons_differ"] = skeletons[0] != skeletons[1]
    if skeletons[0] == skeletons[1]:
        return PairVerdict(False, PairGateReason.MANIPULATION_CHANGES_ONLY_VALUES, detail)
    return PairVerdict(True, PairGateReason.PAIR_SEPARATES, detail)


class ContrastPairGate:
    """§3.A4's authoring gates as a ``row_transform`` (the seam every gate rides).

    Chained after ``PersonaGate`` in every generation route, and deliberately
    separate from it: the persona gate answers "does the belief-holder fail
    exactly one member", which is a question about beliefs; these three answer
    "is this a pair at all", which is a question about the two payloads. Merging
    them would put a difficulty-band check inside a module about personas.

    A refused pair is marked ``invalid`` on BOTH members, because a contrast pair
    with one member is not an instrument — it is one item with a dangling
    reference, and shipping the survivor would quietly convert a commissioned
    pair into an ordinary item nobody asked for.
    """

    def __init__(
        self,
        vault: LoadedVault,
        *,
        difficulty_band_by_lo: Mapping[str, tuple[float, float]] | None = None,
    ) -> None:
        self._vault = vault
        self._bands = dict(difficulty_band_by_lo or {})
        self.verdicts: dict[str, PairVerdict] = {}
        self.violations: list[str] = []

    def __call__(self, rows: list[dict[str, Any]]) -> None:
        pairs: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            if row.get("item_type") != "practice_item" or row.get("operation") != "create":
                continue
            payload = row.get("payload")
            if not isinstance(payload, Mapping):
                continue
            if not payload.get("contrast_of") and not payload.get("differing_component"):
                continue
            own = str(payload.get("id") or row.get("client_item_id") or "")
            counterpart = str(payload.get("contrast_of") or "")
            key = pair_key(own, counterpart) if counterpart else own
            pairs.setdefault(key, []).append(row)
        for key in sorted(pairs):
            members = pairs[key]
            if len(members) == 1:
                self._resolve_single(key, members[0])
                continue
            if len(members) > 2:
                # §3.A4 is "two prompts differing in exactly one requirement".
                # Three rows claiming one pair key is an authoring error, and
                # judging the first two would silently record someone else's
                # verdict against the extras — a row admitted or refused on
                # evidence about a different item. Refuse the whole group with a
                # reason instead.
                verdict = PairVerdict(
                    separates=False,
                    reason=PairGateReason.PAIR_OVERSUBSCRIBED,
                    detail={"pair_key": key, "member_count": len(members)},
                )
                self.verdicts[key] = verdict
                for row in members:
                    self._record(row, key, verdict)
                continue
            verdict = judge_pair(
                members[0]["payload"],
                members[1]["payload"],
                difficulty_band=self._band_for(members[0]["payload"]),
            )
            self.verdicts[key] = verdict
            for row in members:
                self._record(row, key, verdict)

    def _band_for(self, payload: Mapping[str, Any]) -> tuple[float, float] | None:
        return self._bands.get(str(payload.get("learning_object_id") or ""))

    def _resolve_single(self, key: str, row: dict[str, Any]) -> None:
        """A member whose counterpart is not in this batch.

        Resolvable against the vault (an item authored to pair with an existing
        one is legitimate and is how a commissioned pair completes across two
        batches); otherwise the reference dangles and the row is refused.
        """

        payload = row["payload"]
        counterpart = str(payload.get("contrast_of") or "")
        existing = self._vault.practice_items.get(counterpart) if counterpart else None
        if existing is None:
            verdict = PairVerdict(
                False,
                PairGateReason.COUNTERPART_UNRESOLVED,
                {"contrast_of": counterpart or None},
            )
        else:
            verdict = judge_pair(
                payload,
                _payload_of(existing),
                difficulty_band=self._band_for(payload),
            )
        self.verdicts[key] = verdict
        self._record(row, key, verdict)

    def _record(self, row: dict[str, Any], key: str, verdict: PairVerdict) -> None:
        audit = row.get("audit")
        audit = dict(audit) if isinstance(audit, Mapping) else {}
        audit["contrast_pair_gate"] = {"pair_key": key, **verdict.as_dict()}
        row["audit"] = audit
        if verdict.separates:
            return
        ref = str(row.get("client_item_id") or row["payload"].get("id") or "item")
        self.violations.append(f"{ref}: contrast pair refused ({verdict.reason})")
        row["_auto_apply"] = False
        row["validation_status"] = "invalid"
        errors = list(row.get("validation_errors") or [])
        row["validation_errors"] = [f"contrast_pair_gate: {verdict.reason}", *errors]


def _payload_of(item: PracticeItem) -> dict[str, Any]:
    """A persisted item rendered as the payload shape the gates read."""

    return {
        "id": item.id,
        "learning_object_id": item.learning_object_id,
        "expected_answer": item.expected_answer,
        "difficulty": item.difficulty,
        "contrast_of": item.contrast_of,
        "differing_component": (
            item.differing_component.model_dump(mode="json")
            if item.differing_component is not None
            else None
        ),
        "surface_family": item.surface_family,
    }


# ---------------------------------------------------------------------------
# Serving: randomize the order, separate the members, record both
# ---------------------------------------------------------------------------


class AdjacencyBasis(StrEnum):
    """Why the two members were or were not served adjacent (§3.A4)."""

    SEPARATED_BY_INTERLEAVING = "separated_by_interleaving"
    #: §3.A4's own exception: "unless the surfaces differ enough that the
    #: manipulation is not salient". Read off `surface_family`, the vault's
    #: existing surface identity, rather than a fresh judgement.
    SURFACES_DIFFER_SUFFICIENTLY = "surfaces_differ_sufficiently"
    #: The queue had nothing to interleave with. A real state, not a policy.
    QUEUE_TOO_SHORT_TO_SEPARATE = "queue_too_short_to_separate"
    UNKNOWN = "unknown"


def randomization_draw(seed: str) -> float:
    """A deterministic uniform draw in [0, 1) from a seed string.

    Deterministic on purpose. ``build_due_queue`` must produce the same slate
    twice for the same session — the scheduler already relies on this for its
    seeded exploration — and a nondeterministic coin would make the queue
    unreproducible for the sake of a control that exists to REMOVE a nuisance
    parameter. The seed carries the session id, so the draw still varies across
    sessions, which is where the balance is supposed to accumulate.
    """

    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / float(1 << 32)


@dataclass(frozen=True)
class PairServingDecision:
    """One pair's serving decision, before it is written or applied to a queue."""

    pair_key: str
    first_item_id: str
    second_item_id: str
    seed: str
    value: float
    separated: bool
    adjacency_basis: AdjacencyBasis

    def as_dict(self) -> dict[str, Any]:
        return {
            "pair_key": self.pair_key,
            "first_item_id": self.first_item_id,
            "second_item_id": self.second_item_id,
            "randomization_seed": self.seed,
            "randomization_value": self.value,
            "separated": self.separated,
            "adjacency_basis": str(self.adjacency_basis),
        }


def plan_contrast_pair_serving(
    vault: LoadedVault,
    ordered_item_ids: Sequence[str],
    *,
    session_id: str | None,
) -> list[PairServingDecision]:
    """Decide, for every pair in a queue, which member goes first and whether
    the two are separated.

    Pure: it reads a queue and returns decisions. The scheduler applies them and
    :func:`record_contrast_pair_servings` persists them, so this function is
    testable without a database and without a scheduler.

    The separation test is positional and honest: members are "separated" when at
    least one other item sits between them in the served order, OR when their
    ``surface_family`` values differ (§3.A4's own exception — a manipulation is
    not salient across two different surfaces). A queue with nothing else in it
    reports ``QUEUE_TOO_SHORT_TO_SEPARATE`` rather than pretending it separated
    them.
    """

    positions = {item_id: index for index, item_id in enumerate(ordered_item_ids)}
    seen: set[str] = set()
    decisions: list[PairServingDecision] = []
    for item_id in ordered_item_ids:
        item = vault.practice_items.get(item_id)
        if item is None or not item.contrast_of:
            continue
        counterpart_id = str(item.contrast_of)
        if counterpart_id not in positions:
            # Only one member is in this queue: there is no order to randomize
            # and no adjacency to avoid.
            continue
        key = pair_key(item_id, counterpart_id)
        if key in seen:
            continue
        seen.add(key)
        seed = f"{session_id or 'no_session'}|{key}"
        value = randomization_draw(seed)
        members = sorted((item_id, counterpart_id))
        first, second = (members[0], members[1]) if value < 0.5 else (members[1], members[0])
        gap = abs(positions[item_id] - positions[counterpart_id])
        counterpart = vault.practice_items.get(counterpart_id)
        surfaces_differ = bool(
            item.surface_family
            and counterpart is not None
            and counterpart.surface_family
            and item.surface_family != counterpart.surface_family
        )
        if gap > 1:
            basis = AdjacencyBasis.SEPARATED_BY_INTERLEAVING
            separated = True
        elif surfaces_differ:
            basis = AdjacencyBasis.SURFACES_DIFFER_SUFFICIENTLY
            separated = True
        elif len(ordered_item_ids) <= 2:
            basis = AdjacencyBasis.QUEUE_TOO_SHORT_TO_SEPARATE
            separated = False
        else:
            basis = AdjacencyBasis.UNKNOWN
            separated = False
        decisions.append(
            PairServingDecision(
                pair_key=key,
                first_item_id=first,
                second_item_id=second,
                seed=seed,
                value=value,
                separated=separated,
                adjacency_basis=basis,
            )
        )
    return decisions


def apply_serving_decisions(
    ordered_item_ids: Sequence[str], decisions: Sequence[PairServingDecision]
) -> list[str]:
    """Reorder a queue so each pair's randomized first member precedes the other.

    Swaps the two members' SLOTS rather than moving either item, so every other
    item keeps its position and the scheduler's own priority order survives the
    control. A control that reshuffled the queue would confound the thing it
    exists to remove.
    """

    order = list(ordered_item_ids)
    positions = {item_id: index for index, item_id in enumerate(order)}
    for decision in decisions:
        first, second = decision.first_item_id, decision.second_item_id
        if first not in positions or second not in positions:
            continue
        if positions[first] < positions[second]:
            continue
        slot_a, slot_b = positions[first], positions[second]
        order[slot_a], order[slot_b] = order[slot_b], order[slot_a]
        positions[first], positions[second] = slot_b, slot_a
    return order


def record_contrast_pair_servings(
    repository: Repository,
    decisions: Iterable[PairServingDecision],
    *,
    session_id: str | None,
    clock: Clock | None = None,
) -> int:
    """Persist the serving decisions; returns rows written.

    Idempotent per ``(item, session)``: the scheduler re-plans the same session
    on every call, and the order the learner actually saw is the one the first
    plan chose.
    """

    written = 0
    for decision in decisions:
        for position, (item_id, counterpart) in enumerate(
            ((decision.first_item_id, decision.second_item_id),
             (decision.second_item_id, decision.first_item_id))
        ):
            row_id = repository.insert_contrast_pair_serving(
                pair_key=decision.pair_key,
                practice_item_id=item_id,
                counterpart_item_id=counterpart,
                serve_position=position,
                randomization_seed=decision.seed,
                randomization_value=decision.value,
                separated=decision.separated,
                adjacency_basis=str(decision.adjacency_basis),
                session_id=session_id,
                clock=clock,
            )
            written += 1 if row_id else 0
    return written


# ---------------------------------------------------------------------------
# The revert criterion
# ---------------------------------------------------------------------------

#: Metric name. Not on `scoreboard.B5_ORDER` (frozen).
ORDER_EFFECT_METRIC = "contrast_pair_order_effect"

#: Completed pairs below which no order claim is made.
MIN_COMPLETED_PAIRS = 5  # decision parameter

#: Above this share of the within-pair outcome difference attributable to serving
#: order, the pair is measuring order rather than the manipulation — §3.A4's
#: revert direction.
ORDER_DOMINANCE_CEILING = 0.50  # decision parameter

#: Significance level the order-effect deviation must clear before the revert
#: verdict fires. Not a second threshold on the same quantity: the ceiling says
#: how big the effect must be, this says how sure we must be it is an effect at
#: all — and without it the metric's null distribution straddles its own ceiling.
ORDER_EFFECT_ALPHA = 0.05


def contrast_pair_order_effect(
    vault: LoadedVault, repository: Repository, *, since: str | None = None
) -> Metric:
    """``contrast_pair_order_effect``: A4's revert producer.

    DEFINITION
    ----------
    Over pairs where the learner attempted BOTH members:

    * ``manipulation_wins`` — the member that failed is the one the
      ``differing_component`` predicts is harder, regardless of order;
    * ``order_wins`` — the member that failed is the one served SECOND (or
      first), consistently, regardless of which member it is.

    The value is ``order_wins / completed_pairs``: the share of within-pair
    differences explained by serving order alone. §3.A4's revert direction is
    this rising above :data:`ORDER_DOMINANCE_CEILING`.

    ``detail.randomization_balance`` is the second half, and it is not optional:
    the whole control rests on the order being random, so the realized share of
    pairs whose first member was the lexicographically-smaller id is reported
    beside the effect. A balance far from 0.5 invalidates the effect number
    rather than merely qualifying it, and a reader must be able to see that
    without running a second command.

    AVAILABILITY
    ------------
    * fewer than :data:`MIN_COMPLETED_PAIRS` completed pairs -> ``no_data``;
    * enough pairs -> ``available``.
    """

    servings = repository.contrast_pair_serving_rows(since=since)
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in servings:
        by_pair.setdefault(str(row["pair_key"]), {})[str(row["practice_item_id"])] = row
    outcomes: dict[str, list[dict[str, Any]]] = {}
    for attempt in repository.list_all_attempts():
        if since is not None and str(attempt.get("created_at") or "") < since:
            continue
        outcomes.setdefault(str(attempt.get("practice_item_id") or ""), []).append(attempt)
    completed = 0
    order_wins = 0
    manipulation_wins = 0
    ties = 0
    first_is_lower = 0
    rows_detail: list[dict[str, Any]] = []
    for key in sorted(by_pair):
        members = by_pair[key]
        if len(members) != 2:
            continue
        served_first = [
            item_id for item_id, row in members.items() if int(row["serve_position"]) == 0
        ]
        if len(served_first) != 1:
            continue
        first_id = served_first[0]
        second_id = next(item_id for item_id in members if item_id != first_id)
        if first_id == min(members):
            first_is_lower += 1
        first_outcome = _latest_correctness(outcomes.get(first_id) or [])
        second_outcome = _latest_correctness(outcomes.get(second_id) or [])
        if first_outcome is None or second_outcome is None:
            continue
        completed += 1
        if first_outcome == second_outcome:
            ties += 1
            verdict = "tie"
        elif second_outcome < first_outcome:
            # The later-served member fared worse: consistent with order (fatigue,
            # carry-over) as much as with the manipulation.
            order_wins += 1
            verdict = "second_served_worse"
        else:
            manipulation_wins += 1
            verdict = "first_served_worse"
        rows_detail.append(
            {
                "pair_key": key,
                "first_item_id": first_id,
                "second_item_id": second_id,
                "first_correctness": first_outcome,
                "second_correctness": second_outcome,
                "verdict": verdict,
            }
        )
    balance = round(first_is_lower / len(by_pair), 6) if by_pair else None
    detail: dict[str, Any] = {
        "version": CONTRAST_PAIR_VERSION,
        "pairs_served": len(by_pair),
        "completed_pairs": completed,
        "second_served_worse": order_wins,
        "first_served_worse": manipulation_wins,
        "ties": ties,
        # The audit of the randomization itself. 0.5 is the target; a value far
        # from it means the effect number below is measuring the draw, not order.
        "randomization_balance": balance,
        "adjacency": _adjacency_tally(servings),
        "min_completed_pairs": MIN_COMPLETED_PAIRS,
        "order_dominance_ceiling": ORDER_DOMINANCE_CEILING,
        "pairs": rows_detail,
    }
    if completed < MIN_COMPLETED_PAIRS:
        detail["verdict"] = "insufficient_completed_pairs"
        return Metric(
            name=ORDER_EFFECT_METRIC,
            availability="no_data",
            value=None,
            numerator=None,
            denominator=completed,
            unit="rate",
            denominator_label="contrast pairs where the learner attempted both members",
            note=(
                f"{completed} completed pair(s); {MIN_COMPLETED_PAIRS} needed before "
                "an order effect can be distinguished from noise"
            ),
            detail=detail,
        )
    rate = order_wins / completed
    # The metric's NULL value IS its threshold, so a bare comparison is a coin
    # flip. Order is randomized precisely so that a pool driven entirely by the
    # manipulation and not at all by order produces a rate distributed around
    # 0.5 — meaning the naive rule flags pure-manipulation data about half the
    # time, and the number cannot separate the two effects it exists to separate.
    # The verdict therefore requires the deviation from 0.5 to be surprising
    # under an exact two-sided binomial test, not merely present.
    significance = binomial_two_sided_p(order_wins, completed, 0.5)
    detail["order_effect_p_value"] = round(significance, 6)
    detail["order_effect_alpha"] = ORDER_EFFECT_ALPHA
    detail["verdict"] = (
        "order_effects_dominate"
        if rate > ORDER_DOMINANCE_CEILING and significance <= ORDER_EFFECT_ALPHA
        else "within_band"
    )
    return Metric(
        name=ORDER_EFFECT_METRIC,
        availability="available",
        value=round(rate, 6),
        numerator=float(order_wins),
        denominator=float(completed),
        unit="rate",
        denominator_label="contrast pairs where the learner attempted both members",
        note=(
            f"{order_wins}/{completed} pairs where the later-served member fared "
            f"worse (two-sided binomial p={significance:.3f} against a fair coin); "
            f"randomization balance {balance}; verdict {detail['verdict']}"
        ),
        detail=detail,
    )


def _latest_correctness(attempts: Sequence[Mapping[str, Any]]) -> float | None:
    """The most recent scored correctness on one item, or ``None``.

    Most recent rather than first: a pair's contrast is about the learner's
    current state, and an old attempt from before a repair would compare two
    different learners.
    """

    for attempt in sorted(
        attempts, key=lambda row: str(row.get("created_at") or ""), reverse=True
    ):
        value = attempt.get("correctness")
        if value is not None:
            return float(value)
    return None


def _adjacency_tally(servings: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    tally = {str(basis): 0 for basis in AdjacencyBasis}
    for row in servings:
        key = str(row.get("adjacency_basis") or AdjacencyBasis.UNKNOWN)
        tally[key] = tally.get(key, 0) + 1
    return tally
