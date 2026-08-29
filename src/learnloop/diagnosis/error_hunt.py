"""A3 — error-hunt items (spec_measurement_efficiency_v1 §3.A3). Plan item 6.4.

THE HYPOTHESIS
--------------
"Present a fully worked solution containing planted errors; the learner finds and
**repairs** them. Every facet the solution touches yields evidence; misses
localize for free, because the planting location is known. Cost is a fraction of
a full derivation." §3.A3's stated hypothesis: *highest
``cells_cleared_per_minute`` of any instrument class; false-positive detections
on clean solutions surface misconceptions that constructed items miss.*

THE REVERT CRITERION, AND THE CODE THAT MEASURES IT
--------------------------------------------------
"*Revert if:* the planted-persona gate passes items that real learners solve by
proofreading — detectable as error-hunt outcomes uncorrelated with the same
learner's constructed-response outcomes on the same facet."

:func:`proofreading_signal` is that measurement. It pairs, per facet, the
learner's error-hunt outcomes against their constructed-response outcomes on the
same facet and reports the agreement rate. An instrument measuring the facet
should agree with the other instrument measuring the same facet; one measuring
carefulness has no reason to. The metric abstains (``no_data``) until both
populations exist on some shared facet, because an agreement rate over one arm is
not one.

FOUR RULES, ENFORCED IN THREE DIFFERENT PLACES
----------------------------------------------
§3.A3 states four non-triviality rules. They are enforced where each is
checkable, not all in one validator:

1. **The plant must be invisible to a holder of the misconception.** Authoring
   time, ``learnloop.content.authoring.persona_gate.error_hunt_verdict`` — the
   §3.0 gate's own
   question, asked of a planted error rather than of an answer.
2. **Plant from the registry, never freehand.** Schema (``PlantedErrorPayload``
   has no ``freehand`` source arm) plus the same gate, which refuses a plant the
   vault cannot corroborate.
3. **Require the repair, not the flag.** Schema (``required_repair`` is
   mandatory) plus this module, which counts *repaired* and *found-but-not-
   repaired* as different outcomes and credits only the first.
4. **Do not declare the error count, and rotate in clean solutions.** The count
   rule is a deterministic prompt check in the gate; the rotation lives here, in
   the clean-solution arm below.

THE CLEAN-SOLUTION ARM IS THE ONE THAT NEEDS ARGUING FOR
--------------------------------------------------------
"A learner who 'finds' an error in a correct solution has just handed you a
misconception directly." §10 turns that into a validation line: *a clean-solution
error-hunt on which the learner reports an error writes a misconception
CANDIDATE, not a facet failure.*

Both halves matter and they pull in opposite directions. The ordinary grading
path would read a false-positive report as a failed criterion and file negative
evidence against whatever facet the item declares — which is wrong twice over:
the learner's *work* on the facet was never observed (they were reading, not
deriving), and the actually-informative content is the belief that made correct
work look wrong. So :func:`suppress_facet_failures_on_clean_solution` strips
facet targets from the attributions on that path and records that it did, and
:func:`record_error_hunt_outcome` mints the candidate through the existing
``misconception_candidates`` store rather than a parallel one.

The suppression is deliberately narrow: it applies ONLY to a clean solution
(there is no planted error to have failed on) and only to facet targets, so a
seeded error-hunt still writes ordinary evidence, and even on a clean solution
the criterion-level grade is untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.diagnostic_gate import normalize_answer
from learnloop.diagnosis.scoreboard import Metric
from learnloop.vault.models import LoadedVault, PlantedError, PracticeItem

#: Stamped into outcomes so a later reader knows which matching rules produced a
#: population. Bumped when the report<->plant matching changes.
ERROR_HUNT_VERSION = "error_hunt_v1"


class PlantOutcome(StrEnum):
    """What became of one planted error on one attempt.

    ``REPAIRED``
        The learner produced the repair the plant requires. The only arm that
        earns credit, per §3.A3's "require the repair, not the flag".
    ``FOUND_NOT_REPAIRED``
        The learner located the error but produced no repair, or a repair that
        does not contain what the plant requires. Kept separate from
        ``REPAIRED`` rather than pooled into "found", because pooling them is
        precisely how a construction instrument decays into a recognition one.
    ``MISSED``
        No report corresponds to this plant.
    """

    REPAIRED = "repaired"
    FOUND_NOT_REPAIRED = "found_not_repaired"
    MISSED = "missed"


@dataclass(frozen=True)
class PlantResult:
    """One plant's outcome, with the report that decided it."""

    planted_error_id: str
    outcome: PlantOutcome
    facet_id: str | None = None
    misconception_id: str | None = None
    #: Index into the grader's ``reported_errors`` list, or ``None`` when missed.
    report_index: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "planted_error_id": self.planted_error_id,
            "outcome": str(self.outcome),
            "facet_id": self.facet_id,
            "misconception_id": self.misconception_id,
            "report_index": self.report_index,
        }


@dataclass(frozen=True)
class FalsePositiveReport:
    """An error the learner reported that corresponds to no plant.

    On a seeded solution this is noise. On a CLEAN one it is the informative
    outcome §3.A3 is after, and it becomes a misconception candidate.
    """

    report_index: int
    location: str
    claim_md: str
    repair_md: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_index": self.report_index,
            "location": self.location,
            "claim_md": self.claim_md,
            "repair_md": self.repair_md,
        }


@dataclass(frozen=True)
class ValidatedErrorHunt:
    """One attempt's A3 outcome, as the grading validator resolved it."""

    practice_item_id: str
    clean_solution: bool
    plants: tuple[PlantResult, ...] = ()
    false_positives: tuple[FalsePositiveReport, ...] = ()
    #: Set by :func:`suppress_facet_failures_on_clean_solution` when it actually
    #: removed a facet target. Recorded, not inferred: §10's line is about
    #: something that did NOT happen, and an invariant nobody can query is an
    #: invariant nobody can regression-test.
    facet_failure_suppressed: bool = False
    suppression_events: tuple[dict[str, Any], ...] = ()

    @property
    def planted_total(self) -> int:
        return len(self.plants)

    def count(self, outcome: PlantOutcome) -> int:
        return sum(1 for plant in self.plants if plant.outcome is outcome)

    @property
    def reported_error_on_clean_solution(self) -> bool:
        """The §10 case: correct work, and the learner says something is wrong."""

        return self.clean_solution and bool(self.false_positives)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": ERROR_HUNT_VERSION,
            "practice_item_id": self.practice_item_id,
            "clean_solution": self.clean_solution,
            "planted_total": self.planted_total,
            "repaired": self.count(PlantOutcome.REPAIRED),
            "found_not_repaired": self.count(PlantOutcome.FOUND_NOT_REPAIRED),
            "missed": self.count(PlantOutcome.MISSED),
            "plants": [plant.as_dict() for plant in self.plants],
            "false_positives": [report.as_dict() for report in self.false_positives],
            "facet_failure_suppressed": self.facet_failure_suppressed,
            "suppression_events": [dict(event) for event in self.suppression_events],
        }


# ---------------------------------------------------------------------------
# Matching the learner's reports to the plants they never saw
# ---------------------------------------------------------------------------


def _mentions(haystack: str, needle: str) -> bool:
    """Normalized containment under the shared answer normalizer.

    The one normalizer (``diagnostic_gate.normalize_answer``) rather than a
    second one, for the same reason §3.0/D2 give: three uses of one mechanism
    must not drift apart on what counts as the same text.
    """

    normalized_needle = normalize_answer(needle)
    if not normalized_needle:
        return False
    return normalized_needle in normalize_answer(haystack)


def _match_plant(
    report: Any, plants: Sequence[PlantedError], claimed: set[str]
) -> PlantedError | None:
    """Which plant, if any, this report is about.

    The grader is NOT told where the plants are (see the grading context note),
    so this is the harness's own resolution and it runs in a deliberate order:

    1. an explicit ``matches_planted_error_id``, when the caller supplied the
       plants to the grader — accepted only if it names a real, unclaimed plant;
    2. the plant's ``step_ref`` appearing in the report's location or claim;
    3. the plant's ``error_signature`` appearing in the claim or the repair.

    A plant already claimed by an earlier report is skipped, so two reports about
    the same step do not both credit it — one plant, one repair.
    """

    explicit = str(getattr(report, "matches_planted_error_id", "") or "").strip()
    location = str(getattr(report, "location", "") or "")
    claim = str(getattr(report, "claim_md", "") or "")
    repair = str(getattr(report, "repair_md", "") or "")
    if explicit:
        for plant in plants:
            if plant.id == explicit and plant.id not in claimed:
                return plant
    for plant in plants:
        if plant.id in claimed:
            continue
        if _mentions(f"{location} {claim}", plant.step_ref):
            return plant
    for plant in plants:
        if plant.id in claimed:
            continue
        if _mentions(f"{claim} {repair}", plant.error_signature):
            return plant
    return None


def _plant_outcome(report: Any, plant: PlantedError) -> PlantOutcome:
    """Repaired, or merely found. The distinction §3.A3 makes load-bearing."""

    repair = str(getattr(report, "repair_md", "") or "").strip()
    if not repair:
        return PlantOutcome.FOUND_NOT_REPAIRED
    if _mentions(repair, plant.required_repair):
        return PlantOutcome.REPAIRED
    # A repair was attempted but does not produce what the plant requires. This
    # is NOT credited: the learner located the error without correcting it, which
    # is the recognition half of the instrument.
    return PlantOutcome.FOUND_NOT_REPAIRED


def validate_error_hunt_report(
    item: PracticeItem, proposal: Any
) -> ValidatedErrorHunt | None:
    """Resolve the grader's A3 report against the item's plants.

    ``None`` when the item is not an error hunt — the common case, and the reason
    this returns an optional rather than an empty result: an empty outcome would
    write a row for every ordinary attempt and make the A3 population
    uncountable.

    An error-hunt item with **no report at all** still produces an outcome: every
    plant is ``MISSED``, which is the honest reading (the learner repaired
    nothing) and keeps the denominator of the revert criterion whole.
    """

    contract = item.error_hunt
    if contract is None:
        return None
    plants = list(contract.planted_errors or ())
    report = getattr(proposal, "error_hunt_report", None)
    reports = list(getattr(report, "reported_errors", None) or []) if report else []
    claimed: set[str] = set()
    results: dict[str, PlantResult] = {}
    false_positives: list[FalsePositiveReport] = []
    for index, entry in enumerate(reports):
        matched = _match_plant(entry, plants, claimed)
        if matched is None:
            false_positives.append(
                FalsePositiveReport(
                    report_index=index,
                    location=str(getattr(entry, "location", "") or ""),
                    claim_md=str(getattr(entry, "claim_md", "") or ""),
                    repair_md=str(getattr(entry, "repair_md", "") or ""),
                )
            )
            continue
        claimed.add(matched.id)
        results[matched.id] = PlantResult(
            planted_error_id=matched.id,
            outcome=_plant_outcome(entry, matched),
            facet_id=matched.facet_id,
            misconception_id=matched.misconception_id,
            report_index=index,
        )
    ordered = tuple(
        results.get(
            plant.id,
            PlantResult(
                planted_error_id=plant.id,
                outcome=PlantOutcome.MISSED,
                facet_id=plant.facet_id,
                misconception_id=plant.misconception_id,
            ),
        )
        for plant in plants
    )
    return ValidatedErrorHunt(
        practice_item_id=item.id,
        clean_solution=contract.is_clean,
        plants=ordered,
        false_positives=tuple(false_positives),
    )


# ---------------------------------------------------------------------------
# §10: a clean-solution false positive writes a CANDIDATE, not a facet failure
# ---------------------------------------------------------------------------


#: The ``negative_evidence_blocked`` reason a clean-solution false positive
#: stamps onto the observation ledger (§10). Distinct from
#: ``machine_review_scope``: that one means "the machine owes a decision here",
#: this one means "the learner never exercised the facet at all".
CLEAN_SOLUTION_FALSE_POSITIVE = "clean_solution_false_positive"


def suppress_facet_failures_on_clean_solution(
    hunt: ValidatedErrorHunt | None,
    error_attributions: list[Any],
    repair_suggestions: list[dict[str, Any]],
) -> tuple[list[Any], list[dict[str, Any]], ValidatedErrorHunt | None]:
    """Strip facet targets from a clean-solution error hunt's attributions.

    §10: "A clean-solution error-hunt on which the learner reports an error
    writes a misconception candidate, not a facet failure."

    WHY THIS IS NOT THE PASSED-FACET FIREWALL. That firewall (causal §1 principle
    5) blocks a negative write against a facet the learner *demonstrated* on this
    attempt. This blocks a negative write against a facet the learner was never
    observed exercising at all: on a clean solution the learner read correct work
    and disagreed with it, which says something about their beliefs and nothing
    about their ability to do the work. Naming a facet here would be smearing of
    the same kind under a different cause, so the guard is the same shape and the
    audit events use the same reporting channel.

    Deliberately narrow, in three ways:

    * only on a **clean** solution — a seeded hunt's misses localize to the
      plant's own facet, which is real evidence and the entire cost argument for
      the instrument;
    * only **facet** targets — the criterion-level grade and the rubric score are
      untouched, because the learner really did report a nonexistent error;
    * the attribution itself **survives** with its statement intact. Deleting it
      would lose the belief, which is the whole point of the rotation.

    Returns the filtered lists plus the hunt with ``facet_failure_suppressed``
    and its audit events recorded, or the inputs unchanged when the guard does
    not apply.
    """

    if hunt is None or not hunt.reported_error_on_clean_solution:
        return error_attributions, repair_suggestions, hunt
    events: list[dict[str, Any]] = []
    suppressed = False
    for index, attribution in enumerate(error_attributions):
        targets = list(getattr(attribution, "target_evidence_families", None) or [])
        if not targets:
            continue
        suppressed = True
        events.append(
            {
                "kind": "clean_solution_false_positive_facet_write_blocked",
                "source": "error_attribution",
                "attribution_index": index,
                "targets": sorted(str(target) for target in targets),
            }
        )
        try:
            object.__setattr__(attribution, "target_evidence_families", [])
            # The typed reason travels WITH the emptied list. Without it the
            # attribution reaches the observation ledger indistinguishable from
            # one the grader simply never filled, and the projection's
            # single-target fallback attributes the whole failure to the
            # criterion's own target — banking the exact facet failure §10 says
            # a clean-solution false positive must not write.
            object.__setattr__(
                attribution, "facet_write_blocked", CLEAN_SOLUTION_FALSE_POSITIVE
            )
        except Exception:  # pragma: no cover - defensive on a non-dataclass shape
            attribution.target_evidence_families = []
            attribution.facet_write_blocked = CLEAN_SOLUTION_FALSE_POSITIVE
    filtered_repairs: list[dict[str, Any]] = []
    for index, suggestion in enumerate(repair_suggestions or []):
        targets = list(suggestion.get("target_evidence_families") or [])
        if targets:
            suppressed = True
            events.append(
                {
                    "kind": "clean_solution_false_positive_facet_write_blocked",
                    "source": "repair_suggestion",
                    "suggestion_index": index,
                    "targets": sorted(str(target) for target in targets),
                }
            )
            suggestion = {**suggestion, "target_evidence_families": []}
        filtered_repairs.append(suggestion)
    from dataclasses import replace as _replace

    return (
        error_attributions,
        filtered_repairs,
        _replace(
            hunt,
            facet_failure_suppressed=suppressed,
            suppression_events=tuple(events),
        ),
    )


def record_error_hunt_outcome(
    repository: Repository,
    hunt: ValidatedErrorHunt,
    *,
    attempt_id: str,
    learning_object_id: str,
    grading_prompt_version: str | None = None,
    vault: Any = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Persist the outcome and, on the §10 path, mint the misconception candidate.

    The candidate goes into the EXISTING ``misconception_candidates`` store (the
    one the abstention-clustering and promotion machinery already reads), not a
    parallel A3 store. A belief surfaced by an error hunt is the same kind of
    object as one surfaced by a constructed response; giving it its own table
    would make it invisible to every consumer that already knows how to review,
    promote and retire beliefs.

    Only the FIRST false positive on an attempt mints a candidate. A learner who
    disputes three steps of a correct solution has one belief about that
    solution far more often than three, and minting per report would inflate the
    store with near-duplicates that the normalization key cannot merge.
    """

    candidate_id: str | None = None
    if hunt.reported_error_on_clean_solution:
        report = hunt.false_positives[0]
        statement = _candidate_statement(report)
        normalized = normalize_answer(statement)
        existing = repository.misconception_candidate_by_normalized(
            learning_object_id=learning_object_id, statement_normalized=normalized
        )
        if existing is not None:
            candidate_id = str(existing["id"])
            repository.update_misconception_candidate(
                candidate_id,
                occurrence_count=int(existing.get("occurrence_count") or 0) + 1,
                add_item_ids=[hunt.practice_item_id],
            )
        else:
            candidate_id = repository.insert_misconception_candidate(
                learning_object_id=learning_object_id,
                statement=statement,
                statement_normalized=normalized,
                # The learner's own claim about the correct work IS the signature:
                # it is what a holder of the belief says when shown that work.
                signature=report.claim_md.strip() or None,
                mechanism="clean_solution_false_positive",
                item_ids=[hunt.practice_item_id],
                clock=clock,
            )
    promoted_misconception_id: str | None = None
    if candidate_id is not None and vault is not None:
        # §5.6 arm (b), through the one door. Without this the candidate's
        # occurrence count rises on every repeat and the lifecycle never
        # completes: repeated INDEPENDENT error-hunt evidence would accumulate
        # forever without ever becoming the durable belief it evidences.
        # Independence is counted with `surface_group_id` (augmentation §8), so
        # three false positives on one worked solution stay one observation.
        from learnloop.diagnosis.misconceptions import promote_candidate_if_independent

        promoted_misconception_id = promote_candidate_if_independent(
            vault, repository, candidate_id, clock=clock
        )
    repository.insert_error_hunt_outcome(
        attempt_id=attempt_id,
        practice_item_id=hunt.practice_item_id,
        clean_solution=hunt.clean_solution,
        planted_total=hunt.planted_total,
        planted_repaired=hunt.count(PlantOutcome.REPAIRED),
        planted_flagged_not_repaired=hunt.count(PlantOutcome.FOUND_NOT_REPAIRED),
        planted_missed=hunt.count(PlantOutcome.MISSED),
        false_positive_reports=len(hunt.false_positives),
        misconception_candidate_id=candidate_id,
        facet_failure_suppressed=hunt.facet_failure_suppressed,
        grading_prompt_version=grading_prompt_version,
        clock=clock,
    )
    return {
        "attempt_id": attempt_id,
        "misconception_candidate_id": candidate_id,
        "promoted_misconception_id": promoted_misconception_id,
        **hunt.as_dict(),
    }


def _candidate_statement(report: FalsePositiveReport) -> str:
    """The belief, phrased as a belief, from a false-positive report.

    Phrased in learner-model terms ("believes ...") for the same reason spec §2.1
    G1 requires it of ``misconception_statement``: a description of the wrong
    answer is not a belief, and the promotion machinery downstream compares
    beliefs.
    """

    claim = " ".join(str(report.claim_md or "").split())
    location = " ".join(str(report.location or "").split())
    where = f" at {location}" if location else ""
    return f"believes correct work is wrong{where}: {claim}".strip()


# ---------------------------------------------------------------------------
# The revert criterion
# ---------------------------------------------------------------------------

#: Metric name. Not on `scoreboard.B5_ORDER` (frozen); composed the way
#: `persona_gate.gate_precision` is.
PROOFREADING_SIGNAL_METRIC = "error_hunt_constructed_response_agreement"

#: Paired facets below which no agreement claim is made. A correlation over one
#: facet is a coincidence, and the availability arms exist to say so.
MIN_PAIRED_FACETS = 3  # decision parameter

#: Agreement at or below chance means the two instruments are measuring different
#: things — §3.A3's revert direction ("error-hunt outcomes uncorrelated with the
#: same learner's constructed-response outcomes on the same facet").
AGREEMENT_FLOOR = 0.50  # decision parameter


def proofreading_signal(
    vault: LoadedVault, repository: Repository, *, since: str | None = None
) -> Metric:
    """``error_hunt_constructed_response_agreement``: A3's revert producer.

    DEFINITION
    ----------
    For each facet observed by BOTH an error-hunt item and a constructed-response
    item, take the learner's success rate on each side and score the facet as
    agreeing when the two land on the same side of 0.5. The metric is the share
    of paired facets that agree.

    WHY A COARSE PER-FACET AGREEMENT AND NOT A CORRELATION. A single-learner vault
    (standing constraint 1) does not have the sample for a correlation
    coefficient, and reporting one would be exactly the confident-wrongness the
    scoreboard's availability arms exist to prevent. Same-side agreement over
    facets is the weakest statistic that can still answer the question asked:
    does the instrument that claims to measure this facet move with the other
    instrument that measures it?

    AVAILABILITY
    ------------
    * fewer than :data:`MIN_PAIRED_FACETS` facets observed by both -> ``no_data``
      (remedy: author error hunts on facets that already have constructed items,
      which is also the right authoring advice);
    * enough paired facets -> ``available``, with ``detail.verdict`` naming
      whether agreement sits below :data:`AGREEMENT_FLOOR`.

    ``detail.by_facet`` carries the two rates per facet, because the aggregate
    hides the one thing an author can act on: which facet's error hunt is
    behaving like a proofreading exercise.
    """

    hunt_items = {
        item.id: item
        for item in vault.practice_items.values()
        if item.error_hunt is not None
    }
    hunt_stats: dict[str, list[int]] = {}
    other_stats: dict[str, list[int]] = {}
    for attempt in repository.list_all_attempts():
        if since is not None and str(attempt.get("created_at") or "") < since:
            continue
        item_id = str(attempt.get("practice_item_id") or "")
        item = vault.practice_items.get(item_id)
        if item is None:
            continue
        correctness = attempt.get("correctness")
        if correctness is None:
            continue
        target = hunt_stats if item_id in hunt_items else other_stats
        success = 1 if float(correctness) >= 0.5 else 0
        for facet in item.evidence_facets or ():
            bucket = target.setdefault(vault.canonical_facet_id(str(facet)), [0, 0])
            bucket[0] += success
            bucket[1] += 1
    paired = sorted(set(hunt_stats) & set(other_stats))
    by_facet: dict[str, dict[str, Any]] = {}
    agreeing = 0
    for facet in paired:
        hunt_rate = hunt_stats[facet][0] / hunt_stats[facet][1]
        other_rate = other_stats[facet][0] / other_stats[facet][1]
        agrees = (hunt_rate >= 0.5) == (other_rate >= 0.5)
        agreeing += 1 if agrees else 0
        by_facet[facet] = {
            "error_hunt_rate": round(hunt_rate, 6),
            "error_hunt_attempts": hunt_stats[facet][1],
            "constructed_rate": round(other_rate, 6),
            "constructed_attempts": other_stats[facet][1],
            "agrees": agrees,
        }
    detail: dict[str, Any] = {
        "version": ERROR_HUNT_VERSION,
        "error_hunt_items": len(hunt_items),
        "paired_facets": len(paired),
        "by_facet": by_facet,
        "min_paired_facets": MIN_PAIRED_FACETS,
        "agreement_floor": AGREEMENT_FLOOR,
    }
    if len(paired) < MIN_PAIRED_FACETS:
        detail["verdict"] = "insufficient_paired_facets"
        return Metric(
            name=PROOFREADING_SIGNAL_METRIC,
            availability="no_data",
            value=None,
            numerator=None,
            denominator=len(paired),
            unit="rate",
            denominator_label="facets observed by both an error hunt and a constructed item",
            note=(
                f"{len(paired)} paired facet(s); {MIN_PAIRED_FACETS} needed before "
                "an agreement rate says anything about proofreading"
            ),
            detail=detail,
        )
    rate = agreeing / len(paired)
    detail["verdict"] = (
        "agreement_at_or_below_chance" if rate <= AGREEMENT_FLOOR else "within_band"
    )
    return Metric(
        name=PROOFREADING_SIGNAL_METRIC,
        availability="available",
        value=round(rate, 6),
        numerator=float(agreeing),
        denominator=float(len(paired)),
        unit="rate",
        denominator_label="facets observed by both an error hunt and a constructed item",
        note=(
            f"{agreeing}/{len(paired)} facets where the error hunt and the "
            f"constructed item agree; verdict {detail['verdict']}"
        ),
        detail=detail,
    )


def error_hunt_outcome_summary(
    repository: Repository, *, since: str | None = None
) -> dict[str, Any]:
    """Descriptive counts over recorded A3 outcomes, including the clean rotation.

    Report-only. The rotation share is here because it is the one number an
    author can act on directly: §3.A3's "there is always an error" strategy
    reappears the moment clean solutions stop being served.
    """

    rows = repository.error_hunt_outcome_rows(since=since)
    clean = sum(1 for row in rows if row.get("clean_solution"))
    return {
        "version": ERROR_HUNT_VERSION,
        "attempts": len(rows),
        "clean_solution_attempts": clean,
        "clean_rotation_share": round(clean / len(rows), 6) if rows else None,
        "planted_total": sum(int(row.get("planted_total") or 0) for row in rows),
        "planted_repaired": sum(int(row.get("planted_repaired") or 0) for row in rows),
        "planted_found_not_repaired": sum(
            int(row.get("planted_flagged_not_repaired") or 0) for row in rows
        ),
        "planted_missed": sum(int(row.get("planted_missed") or 0) for row in rows),
        "false_positive_reports": sum(
            int(row.get("false_positive_reports") or 0) for row in rows
        ),
        "misconception_candidates_written": sum(
            1 for row in rows if row.get("misconception_candidate_id")
        ),
        "facet_failures_suppressed": sum(
            1 for row in rows if row.get("facet_failure_suppressed")
        ),
    }
