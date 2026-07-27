"""A5 — discrimination profiles on items (spec_measurement_efficiency_v1 §3.A5).

Plan item 6.4, first of the four instrument classes because A3, A4 and Stage 7's
planted-ground-truth harness all consume what this module resolves.

THE HYPOTHESIS
--------------
"Today a wrong answer mostly carries the information 'this criterion failed'. The
*shape* of the wrong answer is where the diagnostic information actually lives,
and it is discarded." §3.A5's stated hypothesis: *first-divergence anchor
accuracy rises on items carrying profiles; abstention **precision** rises (the
model has legitimate candidates to reject rather than a blank space to fill).*

THE REVERT CRITERION, AND THE CODE THAT MEASURES IT
--------------------------------------------------
"*Revert if* ``no_profile_applies`` rate collapses toward zero — that is the
model matching the nearest authored profile rather than reading the trace, and it
is the original disease with better tooling."

:func:`profile_match_fill_rate` is that measurement, and it is deliberately
**two-tailed**, per standing constraint 2 and §3.A5's own sentence: "a profile
that matches ~100% of failures is as suspect as one that never matches." So the
metric reports a verdict over three named arms — the rejection rate collapsing,
a single profile saturating the failure population, and the healthy band —
rather than one number a reader has to interpret. Both tails are computed from
migration 143's ``discrimination_profile_matches``, which records the rejection
arm as a ROW rather than as the absence of one; a schema where "none applied"
were silence would leave the watched tail with no denominator.

The same counts also reach ``grading.causal_attribution_audit_report``, which is
where the vault's existing two-tailed fill/abstention telemetry already lives, so
the rate is visible from the CLI a reader already runs rather than only from a
new one.

WHY A PROFILE MAY NEVER CONSTRAIN A DIAGNOSIS
--------------------------------------------
Causal §0 root cause 8 is an *authoring* failure: a contract demanded structure
in a vocabulary that had no name for what the learner actually did, so authoring
manufactured false structure at mint time. A discrimination profile is also
authored structure about causes — the same shape of risk. Three consequences are
enforced here rather than asserted in prose:

* the profiles handed to the grader are labelled a **prior over candidate
  causes** in the payload itself (:func:`profile_prior_payload`), never a
  required field, an expected answer, or a ranked list;
* ``no_profile_applies`` is a sibling arm of ``matched`` in one closed
  vocabulary (``codex/schemas.DiscriminationProfileMatch``), so rejection cannot
  be confused with silence — :data:`ProfileMatchOutcome` keeps ``NOT_REPORTED``
  as a third, separate arm for exactly that reason;
* a match naming a profile the item does not author is **dropped**, not
  coerced onto the nearest one.

WHAT THE PERSONA GATE TAKES FROM HERE
------------------------------------
§3.A5 says the profile content is "the same content the planted personas consume,
written down once and reused". :func:`payload_profiles` is the one payload reader
both this module and ``services/persona_gate`` use, so the belief a profile
declares and the belief the gate plants can never drift apart. The import runs
one way (``persona_gate`` -> here) so the gate stays the only module that decides
ship/no-ship.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from learnloop.db.repositories import Repository
from learnloop.services.scoreboard import Metric
from learnloop.vault.models import DiscriminationProfile, LoadedVault, PracticeItem

#: Stamped into telemetry so a reader can tell which resolution rules produced a
#: match population. Bumped when the arms or the acceptance rules change.
DISCRIMINATION_PROFILE_VERSION = "discrimination_profile_v1"


class ProfileMatchOutcome(StrEnum):
    """The four arms one graded attempt can land on. Total, and mutually exclusive.

    ``MATCHED``
        The trace matched one authored profile, with a citation.
    ``NO_PROFILE_APPLIES``
        Profiles were offered and the diagnostician rejected all of them. §3.A5's
        first-class outcome, "carrying the same weight as any named match".
    ``NO_PROFILES_OFFERED``
        The item authors none, so no judgement was asked for. Kept apart from
        ``NO_PROFILE_APPLIES`` because pooling them would let an unauthored pool
        masquerade as a healthy rejection rate.
    ``NOT_REPORTED``
        Profiles were offered and nothing came back — an older prompt version, a
        provider that dropped the field, or a match naming an unknown profile id.
        An abstention arm the vocabulary owes itself: silence is not rejection,
        and counting it as one would flatter the metric on the tail it watches.
    """

    MATCHED = "matched"
    NO_PROFILE_APPLIES = "no_profile_applies"
    NO_PROFILES_OFFERED = "no_profiles_offered"
    NOT_REPORTED = "not_reported"


#: The two arms that represent an actual judgement about an offered candidate
#: set. The rejection rate's denominator, and nothing else.
JUDGED_OUTCOMES: frozenset[ProfileMatchOutcome] = frozenset(
    {ProfileMatchOutcome.MATCHED, ProfileMatchOutcome.NO_PROFILE_APPLIES}
)


# ---------------------------------------------------------------------------
# Resolution: the profiles an item actually carries
# ---------------------------------------------------------------------------


def payload_profiles(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Authored profiles off a raw proposal-row payload, normalized and filtered.

    Payload-only and pure, because the persona gate runs over rows before any of
    them is a ``PracticeItem``. A profile missing either load-bearing field
    (``hypothesis``, ``observable_signature``) is dropped here rather than
    downstream: an entry that names a belief but not what its holder writes is
    not an instrument, and letting it through would make the gate abstain
    ("nothing to plant") on an item that looks authored.
    """

    resolved: list[dict[str, Any]] = []
    for index, raw in enumerate(payload.get("discrimination_profiles") or []):
        if not isinstance(raw, Mapping):
            continue
        hypothesis = str(raw.get("hypothesis") or "").strip()
        signature = str(raw.get("observable_signature") or "").strip()
        if not hypothesis or not signature:
            continue
        resolved.append(
            {
                "id": str(raw.get("id") or f"profile_{index}"),
                "hypothesis": hypothesis,
                "observable_signature": signature,
                "misconception_id": raw.get("misconception_id") or None,
                "facet_id": raw.get("facet_id") or None,
                "fails_criteria": [str(value) for value in (raw.get("fails_criteria") or [])],
                "distinguishing_features": [
                    str(value) for value in (raw.get("distinguishing_features") or [])
                ],
                "source": str(raw.get("source") or "authored"),
            }
        )
    return tuple(resolved)


def item_profiles(item: PracticeItem) -> tuple[DiscriminationProfile, ...]:
    """Authored profiles off a loaded item, filtered by the same two rules."""

    return tuple(
        profile
        for profile in (item.discrimination_profiles or ())
        if str(profile.hypothesis or "").strip()
        and str(profile.observable_signature or "").strip()
    )


def profile_prior_payload(
    profiles: Sequence[DiscriminationProfile],
) -> list[dict[str, Any]]:
    """What the grader is shown: candidate causes, explicitly labelled as a prior.

    Deliberately narrow. ``fails_criteria`` is NOT included: it is analysis input
    for A4's commissioning, and handing the grader a list of criteria the author
    expects a belief-holder to fail is handing it a postdictive claim to confirm
    — which is how a prior becomes a constraint. What the grader gets is the
    belief, what its holder writes, and the cues that separate it from its
    neighbours, all of which are things it can check against the trace in front
    of it.
    """

    return [
        {
            "profile_id": profile.id,
            "hypothesis": profile.hypothesis,
            "observable_signature": profile.observable_signature,
            "distinguishing_features": list(profile.distinguishing_features or ()),
        }
        for profile in profiles
    ]


# ---------------------------------------------------------------------------
# Validation: one typed outcome per graded attempt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidatedProfileMatch:
    """One attempt's profile judgement, as the grading validator resolved it."""

    outcome: ProfileMatchOutcome
    profile_id: str | None = None
    misconception_id: str | None = None
    evidence: str = ""
    #: Why the model's own report was not taken at face value, when it was not.
    #: ``None`` when the report was accepted or none was needed.
    rejected_report_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": DISCRIMINATION_PROFILE_VERSION,
            "outcome": str(self.outcome),
            "profile_id": self.profile_id,
            "misconception_id": self.misconception_id,
            "evidence": self.evidence,
            "rejected_report_reason": self.rejected_report_reason,
        }


def validate_profile_match(
    item: PracticeItem,
    proposal: Any,
) -> ValidatedProfileMatch:
    """Resolve the grader's profile report against the item's authored profiles.

    Total over the four arms. The two ways a report is refused both land on
    ``NOT_REPORTED`` rather than on ``NO_PROFILE_APPLIES``, with the reason kept:

    * ``unknown_profile_id`` — the match names a profile this item does not
      author. Coercing it onto the nearest authored profile is precisely the
      failure §3.A5's revert criterion watches for, at the one place in the code
      where it would be easiest to do;
    * ``match_without_evidence`` — a ``matched`` report with no trace citation.
      A6 already requires a citation for a positive observation and this is a
      strictly stronger claim (a cause, not a use).

    Neither raises. A5 is an *additional* diagnostic channel; failing an
    otherwise-valid grade because a bonus field was malformed would trade a real
    measurement for a cosmetic one.
    """

    profiles = item_profiles(item)
    report = getattr(proposal, "discrimination_profile_match", None)
    if not profiles:
        return ValidatedProfileMatch(outcome=ProfileMatchOutcome.NO_PROFILES_OFFERED)
    if report is None:
        return ValidatedProfileMatch(outcome=ProfileMatchOutcome.NOT_REPORTED)
    outcome = str(getattr(report, "outcome", "") or "")
    if outcome == str(ProfileMatchOutcome.NO_PROFILE_APPLIES):
        return ValidatedProfileMatch(
            outcome=ProfileMatchOutcome.NO_PROFILE_APPLIES,
            evidence=str(getattr(report, "evidence", "") or "").strip(),
        )
    if outcome != str(ProfileMatchOutcome.MATCHED):
        return ValidatedProfileMatch(
            outcome=ProfileMatchOutcome.NOT_REPORTED,
            rejected_report_reason="unknown_outcome_arm",
        )
    profile_id = str(getattr(report, "profile_id", "") or "").strip()
    matched = next((profile for profile in profiles if profile.id == profile_id), None)
    if matched is None:
        return ValidatedProfileMatch(
            outcome=ProfileMatchOutcome.NOT_REPORTED,
            rejected_report_reason="unknown_profile_id",
        )
    evidence = str(getattr(report, "evidence", "") or "").strip()
    if not evidence:
        return ValidatedProfileMatch(
            outcome=ProfileMatchOutcome.NOT_REPORTED,
            rejected_report_reason="match_without_evidence",
        )
    return ValidatedProfileMatch(
        outcome=ProfileMatchOutcome.MATCHED,
        profile_id=matched.id,
        misconception_id=matched.misconception_id,
        evidence=evidence,
    )


def profile_match_telemetry(
    match: "ValidatedProfileMatch | Mapping[str, Any] | None",
) -> dict[str, Any]:
    """The per-attempt counts ``causal_attribution_audit_report`` aggregates.

    Shaped as a tally over the closed arm vocabulary rather than as a single
    outcome string, so the audit report can sum it the same way it sums
    ``resolution_counts`` — and so a new arm shows up as a new key rather than
    silently landing in an ``unknown`` bucket.

    Accepts either the validated object or the persisted mapping, because the
    attempt path holds the second and the grading path holds the first. That is
    the whole reason this is one function: a second copy taking the other shape
    drifts from the arm vocabulary the moment an arm is added, and the arm that
    goes missing is the newest one — which is also the one a reader is watching.
    """

    def _field(key: str) -> Any:
        if match is None:
            return None
        if isinstance(match, Mapping):
            return match.get(key)
        return getattr(match, key, None)

    counts = {str(arm): 0 for arm in ProfileMatchOutcome}
    outcome = str(_field("outcome") or "")
    if outcome in counts:
        counts[outcome] += 1
    return {
        "version": DISCRIMINATION_PROFILE_VERSION,
        "outcome_counts": counts,
        "matched_profile_id": _field("profile_id"),
        "rejected_report_reason": _field("rejected_report_reason"),
    }


# ---------------------------------------------------------------------------
# The revert criterion, both tails
# ---------------------------------------------------------------------------

#: Below this rejection rate the model is plausibly matching the nearest authored
#: profile rather than reading the trace — §3.A5's revert direction. A registered
#: decision parameter, not a tuned one: it is a floor on honest disagreement, and
#: the argument for 0.10 is that a candidate set an author wrote before the
#: learner arrived being right nine times out of ten is not a measurement, it is a
#: coincidence worth investigating.
NO_PROFILE_APPLIES_FLOOR = 0.10  # decision parameter

#: Above this share of MATCHED failures on ONE profile, that profile is behaving
#: like a catch-all. The other tail, per standing constraint 2 and §3.A5's own
#: "a profile that matches ~100% of failures is as suspect as one that never
#: matches".
#:
#: WHY THE DENOMINATOR IS MATCHES AND NOT ALL JUDGED FAILURES. The literal
#: reading — one profile matching ~100% of *judged* failures — is arithmetically
#: the same event as the rejection rate collapsing to zero, so an arm defined
#: that way would be unreachable except inside the arm above it and would report
#: nothing new. The independent failure this tail exists to catch is a candidate
#: *set* that is really one candidate: the model rejects honestly some of the
#: time, and every time it does not, it names the same profile. Both denominators
#: are published (``profile_shares`` over judged failures, ``profile_concentration``
#: over matched ones) so a reader can check either reading.
PROFILE_SATURATION_CEILING = 0.90  # decision parameter

#: Matched failures below which no saturation claim is made. Separate from
#: :data:`MIN_JUDGED_FOR_VERDICT` because the concentration statistic has its own,
#: smaller denominator: "one profile took all four matches" is not a finding.
MIN_MATCHES_FOR_SATURATION = 8  # decision parameter

#: Judged failures below which neither tail is claimed. A ratio over three
#: attempts is not a rate; reporting one would be the confident-wrongness the
#: scoreboard's availability arms exist to prevent.
MIN_JUDGED_FOR_VERDICT = 10  # decision parameter

#: Metric name. Not on `scoreboard.B5_ORDER` (that list is frozen); composed the
#: way `persona_gate.gate_precision` is.
PROFILE_REJECTION_METRIC = "discrimination_profile_rejection_rate"


class ProfileTailVerdict(StrEnum):
    """Which tail, if either, the population is sitting in."""

    WITHIN_BAND = "within_band"
    #: Revert direction 1: rejection collapsed toward zero.
    REJECTION_RATE_COLLAPSED = "rejection_rate_collapsed"
    #: Revert direction 2: one profile matches nearly every judged failure.
    PROFILE_SATURATED = "profile_saturated"
    #: Not enough judged failures to claim either.
    INSUFFICIENT_VOLUME = "insufficient_volume"


def profile_match_fill_rate(
    repository: Repository, *, since: str | None = None
) -> Metric:
    """``discrimination_profile_rejection_rate``: A5's two-tailed revert producer.

    DEFINITION
    ----------
    ``rate = |no_profile_applies| / (|matched| + |no_profile_applies|)`` over
    **failed** attempts on profile-bearing items.

    Three choices in that definition, each load-bearing:

    * **Failures only.** A profile describes what a WRONG answer looks like, so a
      correct attempt is not a case where it could have applied. Including
      successes would inflate the rejection rate exactly as authoring quality
      fell, which is backwards.
    * **``not_reported`` and ``no_profiles_offered`` are excluded from the
      denominator** and reported alongside. Silence is not rejection; an
      unauthored item is not a rejection either. Folding either in would let the
      watched tail be padded by items that never asked the question.
    * **The verdict is named, not inferred.** ``detail.verdict`` is one of
      :class:`ProfileTailVerdict`, so a reader is told which tail the population
      is in rather than handed a float and a threshold to remember. Both tails
      are computed: the second reads ``detail.profile_shares``.

    AVAILABILITY (the module-wide discipline in ``services/scoreboard``)
    ------------------------------------------------------------------
    * no judged failures yet -> ``no_data`` (remedy: author profiles, grade
      failures on those items);
    * judged failures present -> ``available``.

    There is no ``no_producer`` arm: unlike gate precision, this rate needs no
    external ground truth — it is a property of the diagnostician's own behaviour
    over an authored candidate set, which is the whole reason §3.A5 chose it as
    the revert criterion.
    """

    rows = repository.discrimination_profile_match_rows(since=since)
    counts = {str(arm): 0 for arm in ProfileMatchOutcome}
    failed_counts = {str(arm): 0 for arm in ProfileMatchOutcome}
    per_profile: dict[str, int] = {}
    for row in rows:
        outcome = str(row.get("outcome") or "")
        if outcome in counts:
            counts[outcome] += 1
        if not bool(row.get("attempt_failed")):
            continue
        if outcome in failed_counts:
            failed_counts[outcome] += 1
        if outcome == str(ProfileMatchOutcome.MATCHED) and row.get("profile_id"):
            profile_id = str(row["profile_id"])
            per_profile[profile_id] = per_profile.get(profile_id, 0) + 1
    matched = failed_counts[str(ProfileMatchOutcome.MATCHED)]
    rejected = failed_counts[str(ProfileMatchOutcome.NO_PROFILE_APPLIES)]
    judged = matched + rejected
    shares = {
        profile_id: round(count / judged, 6)
        for profile_id, count in sorted(per_profile.items())
    } if judged else {}
    concentration = {
        profile_id: round(count / matched, 6)
        for profile_id, count in sorted(per_profile.items())
    } if matched else {}
    detail: dict[str, Any] = {
        "version": DISCRIMINATION_PROFILE_VERSION,
        "outcome_counts": counts,
        "failed_outcome_counts": failed_counts,
        "judged_failures": judged,
        # The second tail, per profile, under both readings (see
        # PROFILE_SATURATION_CEILING). `profile_shares` is over judged failures —
        # the literal reading — and `profile_concentration` is over matched ones,
        # which is what the verdict uses. Both as shares rather than counts, so a
        # reader does not have to divide by a denominator stated elsewhere.
        "profile_shares": shares,
        "profile_concentration": concentration,
        "no_profile_applies_floor": NO_PROFILE_APPLIES_FLOOR,
        "profile_saturation_ceiling": PROFILE_SATURATION_CEILING,
        "min_judged_for_verdict": MIN_JUDGED_FOR_VERDICT,
        "min_matches_for_saturation": MIN_MATCHES_FOR_SATURATION,
    }
    if judged == 0:
        detail["verdict"] = str(ProfileTailVerdict.INSUFFICIENT_VOLUME)
        return Metric(
            name=PROFILE_REJECTION_METRIC,
            availability="no_data",
            value=None,
            numerator=None,
            denominator=0,
            unit="rate",
            denominator_label="failed attempts on items authoring discrimination profiles",
            note=(
                "no failed attempt has yet been judged against an authored profile "
                "set; not_reported and no_profiles_offered are excluded from the "
                "denominator by design"
            ),
            detail=detail,
        )
    rate = rejected / judged
    detail["verdict"] = str(_tail_verdict(rate, judged, matched, concentration))
    return Metric(
        name=PROFILE_REJECTION_METRIC,
        availability="available",
        value=round(rate, 6),
        numerator=float(rejected),
        denominator=float(judged),
        unit="rate",
        denominator_label="failed attempts judged against an authored profile set",
        note=(
            f"{rejected}/{judged} judged failures rejected every authored profile; "
            f"verdict {detail['verdict']}"
        ),
        detail=detail,
    )


def _tail_verdict(
    rate: float, judged: int, matched: int, concentration: Mapping[str, float]
) -> ProfileTailVerdict:
    """Which tail the population sits in. Order matters, and says which is worse.

    Collapse is checked first: a rejection rate at zero means the channel has
    stopped disagreeing at all, which subsumes any statement about an individual
    profile's share. Saturation is the milder finding — the model is still
    rejecting sometimes, but every time it does not, it names the same profile,
    so the candidate *set* is really one candidate.
    """

    if judged < MIN_JUDGED_FOR_VERDICT:
        return ProfileTailVerdict.INSUFFICIENT_VOLUME
    if rate < NO_PROFILE_APPLIES_FLOOR:
        return ProfileTailVerdict.REJECTION_RATE_COLLAPSED
    if matched >= MIN_MATCHES_FOR_SATURATION and any(
        share >= PROFILE_SATURATION_CEILING for share in concentration.values()
    ):
        return ProfileTailVerdict.PROFILE_SATURATED
    return ProfileTailVerdict.WITHIN_BAND


def profile_coverage(vault: LoadedVault) -> dict[str, Any]:
    """How much of the item pool carries profiles at all, by source.

    The companion the rejection rate needs to be read honestly: a healthy
    rejection rate over four items says very little. Report-only; nothing reads
    this to gate anything.
    """

    total = 0
    with_profiles = 0
    profiles = 0
    by_source: dict[str, int] = {}
    for item in vault.practice_items.values():
        total += 1
        resolved = item_profiles(item)
        if not resolved:
            continue
        with_profiles += 1
        profiles += len(resolved)
        for profile in resolved:
            key = str(profile.source)
            by_source[key] = by_source.get(key, 0) + 1
    return {
        "version": DISCRIMINATION_PROFILE_VERSION,
        "practice_items": total,
        "items_with_profiles": with_profiles,
        "profiles": profiles,
        "profiles_by_source": dict(sorted(by_source.items())),
        # `authored` is legitimate (a novel candidate is real) but it is the arm
        # A4 commissioning tries to replace, because a registry-linked profile can
        # be corroborated from evidence elsewhere in the vault.
        "unlinked_authored_profiles": by_source.get("authored", 0),
    }


def profiles_by_facet(
    vault: LoadedVault, items: Iterable[PracticeItem] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Canonical facet id -> the profiles authored against it, across the pool.

    A4's commissioning input: two profiles on one facet with the same
    ``fails_criteria`` are identifiability check 3's "equivalent planted
    profiles", and the pair that separates them is exactly what §3.A4 says the
    findings should commission.
    """

    pool = items if items is not None else vault.practice_items.values()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in pool:
        for profile in item_profiles(item):
            facet = profile.facet_id or ""
            if not facet:
                continue
            canonical = vault.canonical_facet_id(str(facet))
            grouped.setdefault(canonical, []).append(
                {
                    "practice_item_id": item.id,
                    "profile_id": profile.id,
                    "hypothesis": profile.hypothesis,
                    "misconception_id": profile.misconception_id,
                    "fails_criteria": sorted(profile.fails_criteria or ()),
                }
            )
    return {facet: rows for facet, rows in sorted(grouped.items())}
