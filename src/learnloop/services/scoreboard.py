"""The §3 B5 scoreboard, assembled (implementation_plan_v1.md items 4.1/4.3/4.4).

`spec_diagnostic_augmentation_v1.md` §3 B5 froze a fourteen-metric board before
Phase C begins, extended mid-freeze by `spec_measurement_efficiency_v1.md` §5.7
with the certification/instrument block. Four of those metrics already had
producers; the rest had none, and B5 names that exact defect shape itself
("`tokens_per_resolved_diagnostic_episode` has no producer today ... that is the
same defect shape as 'first-divergence accuracy vs adjudication' being listed in
v1 §12 with nothing producing it"). This module is the assembly point.

WHY A `0.0` WOULD BE WORSE THAN NOTHING
---------------------------------------
`harmful_write_rate`'s target is ~0. A rate over an empty denominator that
renders as 0.0 is therefore indistinguishable from a solved problem, and the
same is true of `false_certification_rate` (§5.7: "the only number that licenses
any speed claim") and of `probe_action_change_rate` on a vault where no probe has
ever been administered. So every metric here carries its **numerator, its
denominator, and an explicit availability arm** from a closed vocabulary, and
`value` is `None` — never `0.0` — whenever the denominator is empty. This mirrors
`diagnosis_adjudication._finalize`, which already refuses to report an abstention
precision of 1.0 over zero abstentions.

WHAT THIS MODULE COMPOSES RATHER THAN COMPUTES
----------------------------------------------
* `first_divergence_anchor_accuracy`, `repair_class_match_rate`,
  `abstention_precision`, `abstention_recall` —
  `diagnosis_adjudication.diagnosis_adjudication_scoreboard(group_by="version")`,
  which already produces all four *and* the grading-prompt-version x grader-model
  slice B5 requires. Recomputing them here would give the vault two abstention
  precisions that could disagree.
* `measurement_rank` — `identifiability.measurement_rank`, over
  `identifiability.build_registry_view`. `subject_registry` publishes the same
  call per subject; this is the vault-wide roll-up of the identical function.
* `false_certification_rate` — `certification_cold_probe.false_certification_rate`
  (plan item 4.2), whose ground truth is the delayed cold probe. Composed, never
  recomputed: it is the one number §5.7 says licenses every speed claim, and a
  second definition of it would be worse than none.
* `planted_vs_adjudicated_agreement` — adjudicated side composed from
  `diagnosis_adjudication.adjudicated_ground_truth`; planted side is Stage 7 (B1).

ORDERING IS LOAD-BEARING
------------------------
B5: "The first two are ordered deliberately. Diagnostic accuracy and learner
outcome correlate but do not track: a system can raise anchor accuracy while
becoming slower and more interrogative, and every remaining metric on this list
would report success. `problems_to_cold_success` is the only one that fails when
the system gets more accurate *and* more annoying." `B5_ORDER` encodes that, and
the CLI prints in it. Do not sort the board alphabetically or by availability.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field, replace
from importlib import import_module
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock, FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault


SCOREBOARD_VERSION = "b5_scoreboard_v1"


# ---------------------------------------------------------------------------
# Availability: the closed vocabulary that keeps an unproduced metric visible
# ---------------------------------------------------------------------------

#: Why a metric has no number. Every arm is a *different* remedy, which is the
#: whole reason this is not one boolean:
#:
#:   available        the denominator is non-empty; ``value`` is a number.
#:   no_data          the producer ran and the denominator is empty. The vault
#:                    has not generated the events yet. Remedy: use the system.
#:   no_producer      nothing in this build produces the metric. Remedy: land the
#:                    producer (Stage 7's planted side, item 4.2's cold probe).
#:   unmeasured       the events exist but the *measurement* was never captured,
#:                    and standing constraint 6 makes it un-backfillable (a NULL
#:                    `latency_seconds`, a grading run that predates migration
#:                    131's token columns). Remedy: capture it from now on.
#:   requires_replay  defined and implemented, but faithful only under the
#:                    opt-in prefix replay (§5.8.1), which is not free.
AVAILABILITY: tuple[str, ...] = (
    "available",
    "no_data",
    "no_producer",
    "unmeasured",
    "requires_replay",
)

UNAVAILABLE: frozenset[str] = frozenset(AVAILABILITY) - {"available"}

#: The frozen B5 order (§3 B5, extended by Meas §5.7 before the freeze).
#: `learner_minutes_to_cold_success` is B5's named *companion* to the primary,
#: not a fifteenth independent metric — see `Metric.companion_of`.
B5_ORDER: tuple[str, ...] = (
    "problems_to_cold_success",
    "learner_minutes_to_cold_success",
    "harmful_write_rate",
    "first_divergence_anchor_accuracy",
    "repair_class_match_rate",
    "abstention_precision",
    "abstention_recall",
    "probe_action_change_rate",
    "tokens_per_resolved_diagnostic_episode",
    "planted_vs_adjudicated_agreement",
    "false_certification_rate",
    "questions_to_certification",
    "certification_regret",
    "cells_cleared_per_question",
    "measurement_rank",
)


@dataclass(frozen=True)
class Metric:
    """One scoreboard row, with the denominator it is a rate over.

    ``numerator``/``denominator`` are reported even when ``availability`` is not
    ``available``: "0 harmful writes over 0 surfaced beliefs" and "0 harmful
    writes over 240 surfaced beliefs" are opposite findings and a row that
    printed only its value could not tell them apart.
    """

    name: str
    availability: str
    value: float | None
    numerator: float | None
    denominator: float | None
    unit: str            # rate | count | questions | minutes | tokens | dimensions
    denominator_label: str
    note: str
    companion_of: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.availability not in AVAILABILITY:
            raise ValueError(f"unknown availability {self.availability!r}")
        # The invariant this module exists to hold. A value on an unavailable
        # arm is exactly the "producer that looks live and is inert" defect.
        if self.availability != "available" and self.value is not None:
            raise ValueError(
                f"{self.name}: {self.availability} may not carry a value "
                f"({self.value!r})"
            )
        if self.availability == "available" and self.value is None:
            raise ValueError(f"{self.name}: available metric carries no value")

    @property
    def available(self) -> bool:
        return self.availability == "available"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "availability": self.availability,
            "available": self.available,
            "value": self.value,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "unit": self.unit,
            "denominator_label": self.denominator_label,
            "note": self.note,
            "companion_of": self.companion_of,
            "detail": dict(self.detail),
        }


def _rate(
    name: str,
    *,
    numerator: float | None,
    denominator: float | None,
    unit: str,
    denominator_label: str,
    note: str,
    empty_note: str | None = None,
    empty_availability: str = "no_data",
    companion_of: str | None = None,
    detail: Mapping[str, Any] | None = None,
) -> Metric:
    """Build a ratio metric, refusing to divide by an empty denominator.

    The single choke point for the module's one hard rule. A caller cannot
    accidentally emit 0.0 for "nothing measured" because there is no code path
    from ``denominator == 0`` to a value.
    """

    detail_map = dict(detail or {})
    if not denominator:
        return Metric(
            name=name,
            availability=empty_availability,
            value=None,
            numerator=numerator,
            denominator=denominator or 0,
            unit=unit,
            denominator_label=denominator_label,
            note=empty_note or f"no {denominator_label} yet",
            companion_of=companion_of,
            detail=detail_map,
        )
    return Metric(
        name=name,
        availability="available",
        value=round((numerator or 0.0) / denominator, 6),
        numerator=numerator,
        denominator=denominator,
        unit=unit,
        denominator_label=denominator_label,
        note=note,
        companion_of=companion_of,
        detail=detail_map,
    )


def _unavailable(
    name: str,
    *,
    availability: str,
    unit: str,
    denominator_label: str,
    note: str,
    numerator: float | None = None,
    denominator: float | None = None,
    companion_of: str | None = None,
    detail: Mapping[str, Any] | None = None,
) -> Metric:
    return Metric(
        name=name,
        availability=availability,
        value=None,
        numerator=numerator,
        denominator=denominator,
        unit=unit,
        denominator_label=denominator_label,
        note=note,
        companion_of=companion_of,
        detail=dict(detail or {}),
    )


# ---------------------------------------------------------------------------
# 4.1 — problems_to_cold_success (PRIMARY) and its minutes companion
# ---------------------------------------------------------------------------
#
# WHAT "COLD" ALREADY MEANS HERE, and why nothing new is invented.
# `causal_activity_policy.attempt_counts_as_assisted(attempt_type=, primed=,
# hints_used=)` is the codebase's single assistance test — the docstring says so
# outright ("One function so the projection and the timeline cannot drift apart
# again"), and both `canonical_projection` and `facet_evidence_timeline` route
# through it. A cold attempt is an attempt that test calls unassisted. Writing a
# second predicate here would give the vault two definitions of cold and let the
# headline metric disagree with the evidence ledger that feeds certification.
#
# WHAT "SUCCESS" MEANS. `causal_probe_coherence`'s fitted probe-policy scope
# already owns a knob literally named for this decision —
# `cold_verification_success_correctness` (default 0.8, "correctness at/above
# which a fresh cross-surface attempt counts as a repair-effect success"). It is
# resolved from the fitted store, not hardcoded, so a later `learnloop fit` moves
# this metric and the cold-verification path together.
#
# WHAT "LEARNING TARGET" MEANS. There is no `learning_target` entity in this
# codebase; the learning object is the unit every attempt is keyed on
# (`practice_attempts.learning_object_id`) and the unit certification decides
# over (`goal_certification.lo_certification`). Learning target := learning
# object, stated here rather than left implicit.

#: Attempts that are not a served problem at all and must not be counted in the
#: denominator of "problems served". A `self_report` is the learner telling us
#: something; a `skip` is a refusal. Charging the system for them would inflate
#: problems-to-cold-success with events that cost the learner no problem-solving.
_NON_PROBLEM_ATTEMPT_TYPES: frozenset[str] = frozenset({"self_report", "skip"})


@dataclass(frozen=True)
class ColdSuccessTrajectory:
    """One learning object's path to its first cold success (or lack of one)."""

    learning_object_id: str
    problems_served: int
    cold_success_attempt_id: str | None
    seconds: float | None       # None => at least one served problem has no latency
    problems_without_latency: int

    @property
    def reached(self) -> bool:
        return self.cold_success_attempt_id is not None


def cold_success_trajectories(
    repository: Repository,
    *,
    success_correctness: float | None = None,
) -> list[ColdSuccessTrajectory]:
    """Per learning object: problems served up to the first cold success.

    Right-censored trajectories (no cold success yet) are RETURNED, not dropped.
    They are the whole point: a system that gets more accurate and more annoying
    pushes learning objects out of the numerator, and a mean computed only over
    the ones that made it would improve while the learner's experience got worse.
    """

    from learnloop.services.causal_activity_policy import attempt_counts_as_assisted
    from learnloop.services.causal_probe_coherence import (
        resolve_causal_probe_parameters,
    )

    threshold = (
        float(success_correctness)
        if success_correctness is not None
        else float(
            resolve_causal_probe_parameters(repository)[
                "cold_verification_success_correctness"
            ]
        )
    )

    trajectories: list[ColdSuccessTrajectory] = []
    for learning_object_id in repository.learning_object_ids_with_attempts():
        served = 0
        seconds = 0.0
        missing_latency = 0
        reached: str | None = None
        for attempt in repository.list_attempts_by_learning_object(learning_object_id):
            attempt_type = str(attempt.get("attempt_type") or "")
            if attempt_type in _NON_PROBLEM_ATTEMPT_TYPES:
                continue
            served += 1
            latency = attempt.get("latency_seconds")
            if latency is None:
                # Standing constraint 6: an unrecorded latency is not zero
                # latency, and a mean that treated it as zero would report the
                # learner spending no time. Counted, never imputed.
                missing_latency += 1
            else:
                seconds += float(latency)
            correctness = attempt.get("correctness")
            assisted = attempt_counts_as_assisted(
                attempt_type=attempt_type,
                primed=bool(attempt.get("primed")),
                hints_used=int(attempt.get("hints_used") or 0),
            )
            if (
                not assisted
                and correctness is not None
                and float(correctness) >= threshold
            ):
                reached = str(attempt["id"])
                break
        if not served:
            continue
        trajectories.append(
            ColdSuccessTrajectory(
                learning_object_id=learning_object_id,
                problems_served=served,
                cold_success_attempt_id=reached,
                seconds=None if missing_latency else seconds,
                problems_without_latency=missing_latency,
            )
        )
    return trajectories


def cold_success_metrics(
    repository: Repository, *, success_correctness: float | None = None
) -> tuple[Metric, Metric]:
    """`problems_to_cold_success` (B5's PRIMARY) and its minutes companion.

    Returned as a pair because B5 requires both — "learner minutes to cold
    success as its companion" — and a caller that could take one without the
    other would eventually report the problem count alone, which is exactly the
    "more accurate and more annoying" blind spot the pair exists to close.
    """

    trajectories = cold_success_trajectories(
        repository, success_correctness=success_correctness
    )
    reached = [row for row in trajectories if row.reached]
    censored = [row for row in trajectories if not row.reached]
    detail = {
        "learning_objects_with_attempts": len(trajectories),
        "learning_objects_reaching_cold_success": len(reached),
        # Named `censored`, not "failed": the learning object may simply be young.
        # Either way it is excluded from the mean and must stay visible.
        "censored_learning_objects": len(censored),
        "censored_problems_served": sum(row.problems_served for row in censored),
        "cold_success_share": (
            round(len(reached) / len(trajectories), 6) if trajectories else None
        ),
        "per_learning_object": [
            {
                "learning_object_id": row.learning_object_id,
                "problems_served": row.problems_served,
                "cold_success_attempt_id": row.cold_success_attempt_id,
                "seconds": row.seconds,
                "problems_without_latency": row.problems_without_latency,
            }
            for row in sorted(trajectories, key=lambda r: r.learning_object_id)
        ],
    }

    problems = _rate(
        "problems_to_cold_success",
        numerator=sum(row.problems_served for row in reached),
        denominator=len(reached),
        unit="questions",
        denominator_label="learning objects reaching a cold success",
        note=(
            "mean problems served until the first unassisted success; "
            f"{len(censored)} learning object(s) censored (no cold success yet)"
        ),
        empty_note=(
            "no learning object has reached a cold success yet"
            + (
                f"; {sum(row.problems_served for row in censored)} problem(s) "
                f"served across {len(censored)} censored learning object(s)"
                if censored
                else ""
            )
        ),
        detail=detail,
    )

    # A trajectory with ANY unrecorded latency is excluded outright rather than
    # summed over the recorded subset: a partial sum understates the minutes and
    # would read as the system being faster than it is.
    timed = [row for row in reached if row.seconds is not None]
    minutes_detail = {
        **detail,
        "trajectories_with_complete_latency": len(timed),
        "trajectories_missing_latency": len(reached) - len(timed),
    }
    if reached and not timed:
        minutes = _unavailable(
            "learner_minutes_to_cold_success",
            availability="unmeasured",
            unit="minutes",
            denominator_label="learning objects reaching a cold success with full latency capture",
            note=(
                f"{len(reached)} learning object(s) reached a cold success but "
                "every trajectory has at least one attempt with no "
                "latency_seconds; an unrecorded latency is not zero"
            ),
            numerator=None,
            denominator=0,
            companion_of="problems_to_cold_success",
            detail=minutes_detail,
        )
    else:
        minutes = _rate(
            "learner_minutes_to_cold_success",
            numerator=round(sum(row.seconds or 0.0 for row in timed) / 60.0, 6),
            denominator=len(timed),
            unit="minutes",
            denominator_label="learning objects reaching a cold success with full latency capture",
            note=(
                "mean learner minutes until the first unassisted success; "
                f"{len(reached) - len(timed)} trajectory(ies) excluded for "
                "missing latency"
            ),
            empty_note="no learning object has reached a cold success yet",
            companion_of="problems_to_cold_success",
            detail=minutes_detail,
        )
    return problems, minutes


# ---------------------------------------------------------------------------
# 4.1 — harmful_write_rate
# ---------------------------------------------------------------------------
#
# THE DEFINITION, AND WHY IT IS THE SURFACED ARM.
# Two independent numerators exist now, and they measure different things:
#
#   (a) ADJUDICATED VERDICTS. `wrong_anchor` / `should_have_abstained` on a
#       filled diagnosis (migration 126). This is "the diagnosis was wrong",
#       scored on a deliberately adversarially-selected queue
#       (`adjudication_queue` ranks contests first), over a low-volume sample.
#   (b) SURFACED-THEN-WITHDRAWN. A belief the learner actually SAW
#       (`hypothesis_events.surfaced_to_learner = 1`, migration 132) that was
#       later withdrawn as false (`misconception_disposition_events`).
#
# B5's wording decides it: "Being told something false about your own mind, with
# confidence, is worse than silence." The harm is in the TELLING. A wrong write
# that never reached a viewport cost the learner nothing — it is a hygiene defect,
# and migration 132's own scope guard makes the same argument ("Retiring an
# internal provisional hypothesis nobody was shown is housekeeping"). So (b) is
# the headline and (a) rides alongside as a second arm, because they answer
# different questions and a single number would hide whichever was worse.
#
# The denominator is beliefs SURFACED, not diagnoses written, for the same
# reason: a rate over writes would fall when the system got chattier without
# getting more careful.
#
# WHICH WITHDRAWALS ARE HARM. `surfaced_beliefs.WITHDRAWAL_REASONS` has four
# values. Three assert the belief was false: `contradicted_by_trace` (the
# learner's own work refuted it), `adjudicated` (a review found it wrong),
# `retired_misdiagnosed` (explicitly a misdiagnosis). `superseded` does not — A6
# defines it as "a better-supported diagnosis replaced it", which is the system
# refining a claim rather than having lied about one. Counting supersession as
# harm would penalise exactly the behaviour A6 exists to encourage, so it is
# reported separately and never folded into the headline.

#: Typed withdrawal reasons that assert the surfaced belief was FALSE.
HARMFUL_WITHDRAWAL_REASONS: frozenset[str] = frozenset(
    {"contradicted_by_trace", "adjudicated", "retired_misdiagnosed"}
)

#: A4 verdicts that damage a learner-visible claim: the anchor was wrong, or the
#: diagnosis should not have been made at all. `wrong_repair` is excluded — the
#: adjudication scoreboard's own comment calls it "right place, wrong fix", and
#: it counts as anchor-correct there, so counting it as harm here would put the
#: same verdict on both sides of the ledger.
HARMFUL_VERDICTS: frozenset[str] = frozenset(
    {"wrong_anchor", "should_have_abstained"}
)


def harmful_write_rate(repository: Repository) -> Metric:
    """Wrong-facet damage the learner was actually exposed to (B5, target ~0)."""

    from learnloop.services.diagnosis_adjudication import (
        FILLED_VERDICTS,
        diagnosis_adjudication_scoreboard,
    )
    from learnloop.services.surfaced_beliefs import typed_withdrawal_reason

    surfaced = repository.surfaced_beliefs()
    surfaced_count = len(surfaced)

    harmful_ids: set[str] = set()
    superseded_ids: set[str] = set()
    by_reason: dict[str, int] = {}
    for row in repository.surfaced_belief_withdrawals():
        reason = typed_withdrawal_reason(
            str(row["disposition"]), row.get("reason")
        )
        by_reason[reason] = by_reason.get(reason, 0) + 1
        belief_id = str(row["belief_id"])
        if reason in HARMFUL_WITHDRAWAL_REASONS:
            harmful_ids.add(belief_id)
        else:
            superseded_ids.add(belief_id)

    surfaced_arm = _rate(
        "harmful_write_rate.surfaced_withdrawn",
        numerator=len(harmful_ids),
        denominator=surfaced_count,
        unit="rate",
        denominator_label="beliefs surfaced to the learner",
        note="surfaced beliefs later withdrawn as false, over beliefs surfaced",
        empty_note=(
            "no belief has been surfaced to the learner yet — surfacing is "
            "capture-now (migration 132) and pre-capture presentations are not "
            "backfillable"
        ),
        detail={
            "withdrawals_by_reason": dict(sorted(by_reason.items())),
            "harmful_reasons": sorted(HARMFUL_WITHDRAWAL_REASONS),
            "surfaced_then_superseded": len(superseded_ids),
            "harmful_belief_ids": sorted(harmful_ids),
        },
    )

    # Arm (a): the adjudicated verdicts, composed off the A4 store's own
    # scoreboard so the verdict vocabulary lives in exactly one place.
    board = diagnosis_adjudication_scoreboard(repository, group_by=None)
    verdicts = board["overall"]["by_verdict"]
    filled = sum(verdicts.get(verdict, 0) for verdict in FILLED_VERDICTS)
    adjudicated_arm = _rate(
        "harmful_write_rate.adjudicated_verdicts",
        numerator=sum(verdicts.get(verdict, 0) for verdict in HARMFUL_VERDICTS),
        denominator=filled,
        unit="rate",
        denominator_label="filled diagnoses with an adjudicated verdict",
        note=(
            "wrong_anchor + should_have_abstained over filled adjudications; "
            "the queue is adversarially selected (contests first), so this is "
            "not a vault-wide rate"
        ),
        empty_note="no filled diagnosis has been adjudicated yet",
        detail={"by_verdict": dict(verdicts)},
    )

    detail = {
        "definition": "surfaced_withdrawn",
        "arms": {
            "surfaced_withdrawn": surfaced_arm.as_dict(),
            "adjudicated_verdicts": adjudicated_arm.as_dict(),
        },
        "arms_agree": (
            surfaced_arm.value == adjudicated_arm.value
            if surfaced_arm.available and adjudicated_arm.available
            else None
        ),
        **surfaced_arm.detail,
    }
    return replace(surfaced_arm, name="harmful_write_rate", detail=detail)


# ---------------------------------------------------------------------------
# 4.3 — cells_cleared_per_question
# ---------------------------------------------------------------------------
#
# WHICH CELL VOCABULARY. Two modules speak it:
# `contract_reachability.contract_cells(vault)` and
# `facet_diagnostics.contract_frontier(vault, lo, repository)`. This uses
# **contract_reachability**, deliberately:
#
#   * `ContractCell` carries the LO in its identity; `contract_frontier` returns
#     bare `(facet, capability)` pairs, so two learning objects requiring the
#     same cell would collapse into one and the numerator would undercount.
#   * `contract_frontier` has a legacy item-mode fallback arm (its `authored`
#     flag) that derives the frontier from authoring history when no blueprint
#     declares one. §5.2 is explicit that an item-derived denominator "is an
#     artifact of AUTHORING HISTORY, not an obligation" — admitting it into an
#     instrument-efficiency metric would make the metric move when the system
#     authors an item and the learner does nothing.
#   * `contract_cells` is one vault-wide call; the frontier is per-LO.
#
# WHY THE CURRENT COVERED COUNT *IS* THE LIFETIME TRANSITION COUNT.
# §0's identity is `questions ~ (cells to clear) / (cells cleared per question)`,
# so the numerator wanted is "cells that went uncovered -> covered". Coverage is
# monotone by construction: `facet_capability_evidence` is a pure order-
# independent projection over the immutable observation ledger whose masses
# accumulate additively (migration 037), and the projection DELETEs and rebuilds
# it whole from that ledger (§5.8.1). A cell with mass can therefore never lose
# it while the ledger only grows, so counting currently-covered contract cells
# counts exactly the uncovered->covered transitions — with no per-attempt replay.


def _cell_has_evidence(evidence: Sequence[Any], capability: str) -> bool:
    """Any observation at all in this cell — positive or negative.

    "Cleared" in §0 means *measured*, not *passed*: a cell where the learner
    reliably fails has been cleared by the instrument (the system now knows
    something), and scoring only successes would make the metric a mastery
    proxy rather than an instrument-efficiency one.
    """

    for row in evidence:
        if str(row.capability) != capability:
            continue
        if (
            row.direct_positive_mass
            or row.direct_negative_mass
            or row.embedded_positive_mass
            or row.embedded_negative_mass
        ):
            return True
    return False


def cells_cleared_per_question(vault: LoadedVault, repository: Repository) -> Metric:
    """Contract cells measured, per question served (Meas §5.7, §0)."""

    from learnloop.services.contract_reachability import contract_cells

    cells, advisory_components = contract_cells(vault)
    evidence_cache: dict[str, Sequence[Any]] = {}
    covered = 0
    uncovered_examples: list[dict[str, str]] = []
    for cell in cells:
        if cell.facet_id not in evidence_cache:
            evidence_cache[cell.facet_id] = repository.facet_capability_evidence_for_facet(
                cell.facet_id
            )
        if _cell_has_evidence(evidence_cache[cell.facet_id], cell.capability):
            covered += 1
        elif len(uncovered_examples) < 20:
            uncovered_examples.append(
                {
                    "learning_object_id": cell.learning_object_id,
                    "facet_id": cell.facet_id,
                    "required_capability": cell.capability,
                }
            )

    questions = repository.attempt_count()
    detail = {
        "cell_vocabulary": "contract_reachability.contract_cells",
        "contract_cells": len(cells),
        "cells_covered": covered,
        "cells_uncovered": len(cells) - covered,
        "advisory_components_excluded": advisory_components,
        "questions_served": questions,
        "uncovered_sample": uncovered_examples,
    }
    if not cells:
        # A zero numerator over a real denominator would read as "the instruments
        # clear nothing", when the truth is that no blueprint declares an
        # obligation to clear. Different finding, different arm.
        return _unavailable(
            "cells_cleared_per_question",
            availability="no_data",
            unit="rate",
            denominator_label="questions served",
            note="no blueprint recipe declares a contract cell in this vault",
            numerator=0,
            denominator=questions,
            detail=detail,
        )
    return _rate(
        "cells_cleared_per_question",
        numerator=covered,
        denominator=questions,
        unit="rate",
        denominator_label="questions served",
        note=(
            f"{covered} of {len(cells)} contract cell(s) measured across "
            f"{questions} question(s) served"
        ),
        empty_note="no question has been served yet",
        detail=detail,
    )


# ---------------------------------------------------------------------------
# 4.3 — questions_to_certification and certification_regret
# ---------------------------------------------------------------------------
#
# WHY THESE TWO ARE NOT PLAIN COUNTERS, AND WHAT THEY COST.
# There is no persisted "certified at attempt N" event in this codebase.
# `goal_certification.lo_certification` is a pure read-side predicate over
# `facet_capability_evidence`, so the system "certifies" precisely when the
# evidence crosses the bar — there is no separate decision moment to log. Both
# metrics therefore need the *earliest prefix of attempts* at which the authority
# would already have said yes.
#
# §5.8.1 is the binding constraint: "Replaying a prefix of the attempts does not
# produce a prefix of the state." `project_canonical_facet_state` rebuilds
# `facet_capability_evidence` WHOLE from the immutable ledger, so a harness that
# replays only the first k attempts still reads a ledger reflecting all n. A
# correct prefix harness must FILTER THE LEDGER on a scratch copy before
# replaying. That is the only faithful route, and it is not free:
#
#   cost per cutoff = copyfile(state.sqlite) + prune attempts after the cutoff
#                     + rebuild_derived_state(whole vault) + one
#                     lo_certification() per learning object
#
# measured at ~1.5-3s per cutoff on `fixtures/linear_algebra` (43 attempts, 21
# learning objects, 15 MB db), which matches §5.8.1's own ~2.5s figure.
#
# §5.8.1 tells callers to "sample a coarse grid of cutoffs rather than every k",
# which would make the answer an upper bound. This harness does better without
# approximating: certification credit is monotone non-decreasing in the prefix
# (`certification_credit` only ever adds non-negative mass, and dropping later
# attempts can only remove observations), so the earliest certifying cutoff can
# be found by BISECTION — O(log n) evaluations instead of O(n), exactly, with
# every evaluation shared across all learning objects. A budget still bounds it;
# when the budget runs out the residual bracket is reported and the metric stays
# on the `requires_replay` arm rather than guessing inside the bracket.
#
# Nothing here is computed unless the caller opts in. Without `replay=True` both
# metrics report `requires_replay` — never a number, and never 0.

#: Bisection evaluations allowed per scoreboard run. 24 is enough to bisect a
#: 43-attempt vault for every learning object with the memo doing most of the
#: work; a vault with thousands of attempts will exhaust it and say so.
DEFAULT_REPLAY_BUDGET = 24


@dataclass(frozen=True)
class CertificationPrefix:
    """The earliest attempt prefix at which one learning object certifies."""

    learning_object_id: str
    #: Questions served for THIS learning object inside the earliest certifying
    #: global prefix. None when the learning object never certifies.
    questions_to_certification: int | None
    #: Questions served for this learning object in the live (full) ledger.
    questions_served: int
    exact: bool
    #: Residual (lower, upper) global cutoff bracket when `exact` is False.
    bracket: tuple[int, int] | None = None

    @property
    def regret(self) -> int | None:
        if self.questions_to_certification is None:
            return None
        return max(0, self.questions_served - self.questions_to_certification)


def _attempt_boundaries(repository: Repository) -> list[tuple[str, str]]:
    """Every attempt as (created_at, id), chronological — the cutoff axis."""

    with repository.connection() as connection:
        return [
            (str(row[0]), str(row[1]))
            for row in connection.execute(
                "SELECT created_at, id FROM practice_attempts "
                "ORDER BY created_at ASC, id ASC"
            )
        ]


def _certified_at_cutoff(
    vault: LoadedVault,
    source_path: Path,
    scratch_dir: Path,
    boundary_iso: str,
    index: int,
) -> frozenset[str]:
    """Learning objects the authority certifies given attempts up to `boundary_iso`.

    Runs the REAL authority (`lo_certification`) against a REAL rebuilt
    projection on a scratch copy. Nothing in here re-implements a certification
    rule, which is the only way the answer can be called faithful.
    """

    # `_prune_rows` walks the FK graph clearing non-cascading referrers. Imported
    # rather than re-written: a second FK walk would drift from the first, and
    # the first is the one `goal_report_series` has been exercising.
    from learnloop.services.goal_certification import lo_certification
    from learnloop.services.goal_series import _prune_rows
    from learnloop.services.replay import rebuild_derived_state

    scratch_path = scratch_dir / f"prefix_{index}.sqlite"
    shutil.copyfile(source_path, scratch_path)
    try:
        scratch = Repository(scratch_path)
        with scratch.pinned():
            with scratch.connection() as connection:
                doomed = [
                    row[0]
                    for row in connection.execute(
                        "SELECT id FROM practice_attempts WHERE created_at > ?",
                        (boundary_iso,),
                    )
                ]
                _prune_rows(connection, "practice_attempts", "id", doomed)
                connection.commit()
            observed = parse_utc(boundary_iso)
            rebuild_derived_state(
                vault,
                scratch,
                clock=FrozenClock(observed) if observed is not None else None,
            )
            return frozenset(
                learning_object_id
                for learning_object_id, learning_object in vault.learning_objects.items()
                if lo_certification(vault, scratch, learning_object).demonstrated
            )
    finally:
        scratch_path.unlink(missing_ok=True)


def certification_prefixes(
    vault: LoadedVault,
    repository: Repository,
    *,
    budget: int = DEFAULT_REPLAY_BUDGET,
) -> tuple[list[CertificationPrefix], dict[str, Any]]:
    """Bisect the earliest certifying prefix for every learning object.

    Returns (prefixes, trace). The trace records the evaluations spent and
    whether the budget bound the answer, because a bounded search that did not
    say so would be indistinguishable from an exact one.
    """

    boundaries = _attempt_boundaries(repository)
    total = len(boundaries)
    # Each learning object's 1-based positions on the same global chronological
    # axis the cutoffs run over, so "questions served inside the certifying
    # prefix" is a count, not a second query per cutoff.
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT learning_object_id FROM practice_attempts "
            "ORDER BY created_at ASC, id ASC"
        ).fetchall()
    served: dict[str, list[int]] = {}
    for position, row in enumerate(rows, start=1):
        served.setdefault(str(row[0]), []).append(position)

    trace: dict[str, Any] = {
        "attempts": total,
        "evaluations": 0,
        "budget": budget,
        "budget_exhausted": False,
        "seconds": None,
    }
    if not total:
        return [], trace

    memo: dict[int, frozenset[str]] = {}
    started = perf_counter()

    with tempfile.TemporaryDirectory(prefix="learnloop-cert-prefix-") as scratch:
        scratch_dir = Path(scratch)

        def certified(cutoff: int) -> frozenset[str] | None:
            """Certified set at global cutoff `cutoff` (1-based, 0 == no attempts)."""

            if cutoff <= 0:
                return frozenset()
            if cutoff in memo:
                return memo[cutoff]
            if trace["evaluations"] >= budget:
                trace["budget_exhausted"] = True
                return None
            trace["evaluations"] = int(trace["evaluations"]) + 1
            memo[cutoff] = _certified_at_cutoff(
                vault,
                Path(repository.sqlite_path),
                scratch_dir,
                boundaries[cutoff - 1][0],
                cutoff,
            )
            return memo[cutoff]

        final = certified(total)
        prefixes: list[CertificationPrefix] = []
        if final is None:
            trace["seconds"] = round(perf_counter() - started, 3)
            return [], trace

        for learning_object_id in sorted(served):
            positions = served[learning_object_id]
            questions_served = len(positions)
            if learning_object_id not in final:
                prefixes.append(
                    CertificationPrefix(
                        learning_object_id=learning_object_id,
                        questions_to_certification=None,
                        questions_served=questions_served,
                        exact=True,
                    )
                )
                continue
            # Monotone in the cutoff, so bisect: `low` never certifies, `high`
            # always does.
            low, high = 0, total
            exact = True
            while high - low > 1:
                middle = (low + high) // 2
                verdict = certified(middle)
                if verdict is None:
                    exact = False
                    break
                if learning_object_id in verdict:
                    high = middle
                else:
                    low = middle
            questions = (
                sum(1 for position in positions if position <= high) if exact else None
            )
            prefixes.append(
                CertificationPrefix(
                    learning_object_id=learning_object_id,
                    questions_to_certification=questions,
                    questions_served=questions_served,
                    exact=exact,
                    bracket=None if exact else (low, high),
                )
            )
    trace["seconds"] = round(perf_counter() - started, 3)
    return prefixes, trace


def certification_efficiency_metrics(
    vault: LoadedVault,
    repository: Repository,
    *,
    replay: bool = False,
    budget: int = DEFAULT_REPLAY_BUDGET,
) -> tuple[Metric, Metric]:
    """`questions_to_certification` and `certification_regret` (Meas §5.7).

    Both are gated on `replay`. The cheap arm reports how many learning objects
    are certified *now* (free — `lo_certification` is a pure read), because that
    is the honest thing available without the prefix harness, and it is reported
    as a count, never as either of the two rates it is not.
    """

    from learnloop.services.goal_certification import lo_certification

    certified_now = sorted(
        learning_object_id
        for learning_object_id, learning_object in vault.learning_objects.items()
        if lo_certification(vault, repository, learning_object).demonstrated
    )
    shared_detail: dict[str, Any] = {
        "certified_learning_objects_now": len(certified_now),
        "certified_learning_object_ids": certified_now,
        "learning_objects": len(vault.learning_objects),
        "replay_cost_note": (
            "one copyfile + ledger prune + rebuild_derived_state + one "
            "lo_certification per learning object, per cutoff (~1.5-3s each on "
            "fixtures/linear_algebra); bisected, so O(log attempts) cutoffs"
        ),
    }

    if not replay:
        note = (
            "requires the §5.8.1 prefix replay (filter the observation ledger on "
            "a scratch copy, then rebuild); pass replay=True / --replay"
        )
        return (
            _unavailable(
                "questions_to_certification",
                availability="requires_replay",
                unit="questions",
                denominator_label="learning objects with a certifying prefix",
                note=note,
                detail=shared_detail,
            ),
            _unavailable(
                "certification_regret",
                availability="requires_replay",
                unit="questions",
                denominator_label="learning objects with a certifying prefix",
                note=note,
                detail=shared_detail,
            ),
        )

    prefixes, trace = certification_prefixes(vault, repository, budget=budget)
    exact = [
        row
        for row in prefixes
        if row.exact and row.questions_to_certification is not None
    ]
    inexact = [row for row in prefixes if not row.exact]
    detail = {
        **shared_detail,
        "replay": trace,
        "learning_objects_certifying": len(
            [row for row in prefixes if row.questions_to_certification is not None]
            + inexact
        ),
        "learning_objects_bounded_by_budget": len(inexact),
        "per_learning_object": [
            {
                "learning_object_id": row.learning_object_id,
                "questions_to_certification": row.questions_to_certification,
                "questions_served": row.questions_served,
                "regret": row.regret,
                "exact": row.exact,
                "bracket": list(row.bracket) if row.bracket else None,
            }
            for row in prefixes
        ],
    }
    empty_note = (
        "no learning object certifies at any attempt prefix"
        if not inexact
        else (
            f"{len(inexact)} learning object(s) exhausted the {budget}-evaluation "
            "replay budget; raise --replay-budget"
        )
    )
    empty_availability = "no_data" if not inexact else "requires_replay"
    questions = _rate(
        "questions_to_certification",
        numerator=sum(row.questions_to_certification or 0 for row in exact),
        denominator=len(exact),
        unit="questions",
        denominator_label="learning objects with a certifying prefix",
        note=(
            "mean questions served on a learning object up to the earliest "
            "prefix at which the authority certifies it"
        ),
        empty_note=empty_note,
        empty_availability=empty_availability,
        detail=detail,
    )
    regret = _rate(
        "certification_regret",
        numerator=sum(row.regret or 0 for row in exact),
        denominator=len(exact),
        unit="questions",
        denominator_label="learning objects with a certifying prefix",
        note=(
            "mean questions served AFTER the evidence already supported "
            "certifying (Meas §5.7)"
        ),
        empty_note=empty_note,
        empty_availability=empty_availability,
        detail=detail,
    )
    return questions, regret


# ---------------------------------------------------------------------------
# 4.4 — tokens_per_resolved_diagnostic_episode
# ---------------------------------------------------------------------------
#
# Unblocked by plan item 1.2 (migration 131 + `learnloop.token_usage` +
# `agent_runs.finish_agent_run`), and producible only because BOTH grading paths
# in `services/attempts.py` now carry tokens.
#
# EPISODE. One graded attempt that produced causal-attribution telemetry
# (`attempt_debug_payloads.causal_attribution`) — the same record
# `missing_vocabulary_report` and `diagnosis_adjudication._abstention_state`
# read, so "episode" means one thing in the vault.
#
# RESOLVED. `resolution_counts["resolved"] >= 1`. B5's ratio is per *resolved*
# episode: an episode that abstained produced no diagnosis to be worth anything,
# and dividing by it would make abstention look cheap. Abstention volume is
# reported alongside, because C1's watched failure is abstention recall
# collapsing and a cost metric that hid it would be complicit.
#
# 0 TOKENS vs UNKNOWN TOKENS. Migration 131 says 0 is "unreported or free, never
# unknown", and that is true *of a run written after the columns existed*. Three
# populations must not be collapsed:
#   * NO MODEL RUN. No grading agent_run at all (the deterministic grading path,
#     `agent_run_id=None`) — genuinely free. In the denominator at 0 tokens.
#   * METERED RUN. A run reporting non-zero tokens. In the denominator.
#   * UNMETERED RUN. A run row reporting 0/0 — either a provider that exposes no
#     usage (the local app-server adapter) or a run predating migration 131.
#     Un-backfillable (standing constraint 6), so EXCLUDED from the denominator
#     rather than dragging the mean to 0.
#
# AND ONE MORE GUARD, which the linear_algebra fixture immediately needed. If
# every model-graded episode is unmetered and the only measurable episodes are
# the free ones, the surviving sample contains no model cost at all — the ratio
# would render 0.0 tokens per resolved episode for a loop that demonstrably calls
# a grader. That is `unmeasured`, not a cost of zero. A vault where NOTHING was
# model-graded is different: there the loop really did cost nothing, and 0.0 is
# the honest answer.


def tokens_per_resolved_diagnostic_episode(repository: Repository) -> Metric:
    """Grading tokens per resolved diagnostic episode (B5; C3's revert criterion)."""

    episodes = 0
    resolved_episodes = 0
    abstained_episodes = 0
    metered_runs = 0
    unmetered_runs = 0
    no_model_run = 0
    input_tokens = 0
    output_tokens = 0

    for attempt in repository.list_all_attempts():
        attempt_id = str(attempt["id"])
        debug = repository.attempt_debug_payload(attempt_id) or {}
        telemetry = debug.get("causal_attribution")
        if not isinstance(telemetry, Mapping):
            continue
        episodes += 1
        counts = telemetry.get("resolution_counts")
        counts = counts if isinstance(counts, Mapping) else {}
        if int(counts.get("abstained") or 0) and not int(counts.get("resolved") or 0):
            abstained_episodes += 1
        if not int(counts.get("resolved") or 0):
            continue
        resolved_episodes += 1
        metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
        run_id = metadata.get("agent_run_id")
        run = repository.agent_run(str(run_id)) if run_id else None
        if run is None:
            # No run row at all: the deterministic grading path, or a run whose
            # record is gone. Either way no model was billed through this
            # episode's grading.
            no_model_run += 1
            continue
        run_input = int(run.get("actual_input_tokens") or 0)
        run_output = int(run.get("actual_output_tokens") or 0)
        if not (run_input or run_output):
            unmetered_runs += 1
            continue
        metered_runs += 1
        input_tokens += run_input
        output_tokens += run_output

    denominator = metered_runs + no_model_run
    detail = {
        "diagnostic_episodes": episodes,
        "resolved_episodes": resolved_episodes,
        "abstained_episodes": abstained_episodes,
        "episodes_with_metered_run": metered_runs,
        "episodes_with_unmetered_run": unmetered_runs,
        "episodes_with_no_model_run": no_model_run,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    if unmetered_runs and not metered_runs:
        return _unavailable(
            "tokens_per_resolved_diagnostic_episode",
            availability="unmeasured",
            unit="tokens",
            denominator_label="resolved diagnostic episodes with a known token cost",
            note=(
                f"{unmetered_runs} of {resolved_episodes} resolved episode(s) "
                "were model-graded by a run reporting 0/0 tokens, which "
                "migration 131 cannot distinguish from a pre-131 run; the "
                f"remaining {no_model_run} called no model, so no model cost is "
                "measurable"
            ),
            numerator=input_tokens + output_tokens,
            denominator=denominator,
            detail=detail,
        )
    return _rate(
        "tokens_per_resolved_diagnostic_episode",
        numerator=input_tokens + output_tokens,
        denominator=denominator,
        unit="tokens",
        denominator_label="resolved diagnostic episodes with a known token cost",
        note=(
            f"grading tokens over {denominator} resolved episode(s) with a known "
            f"cost ({metered_runs} metered, {no_model_run} called no model); "
            f"{unmetered_runs} excluded as unmetered"
        ),
        empty_note="no diagnostic episode has reached a resolution yet",
        detail=detail,
    )


# ---------------------------------------------------------------------------
# 4.4 — probe_action_change_rate
# ---------------------------------------------------------------------------
#
# DENOMINATOR: probes ADMINISTERED, i.e. classified discriminating observations
# (`causal_discriminating_observations`, migration 130 — one row per probe
# response that was classified). Not `causal_probe_decision_receipts` with
# `decision='probe_now'`: that counts probes OFFERED, and an offered-but-never-
# answered probe changed no action because it never happened.
#
# NUMERATOR: observations that were `admitted` AND `resolved_factor`. Migration
# 130 admits only `matched_single` as resolving, and the orchestrator resolves
# BEFORE recording so the receipt states truthfully whether it was this
# observation that closed the factor. Closing the factor is what changes the
# selected repair: the orchestrator only buys a probe when the candidates are NOT
# action-equivalent (`skip_action_equivalent` is the majority skip verb), so a
# resolution over a non-action-equivalent candidate set moves the action by
# construction. An unadmitted observation grants no authority and migration 130's
# own CHECK forbids it resolving anything.
#
# EXPECT A ZERO NUMERATOR TODAY, AND SAY WHY. Migration 130's writer only became
# reachable when Stage 2.1 landed a probe-candidate producer
# (`causal_probe_commissioning`: "`causal_discriminating_observations` could never
# be written"), so current vaults have no rows at all. That is "no probes
# administered yet" — availability `no_data` — and emphatically not "probes never
# change anything", which is what a 0.0 would assert.

#: The offer-side decision verb, kept for the offered/administered comparison.
_PROBE_NOW_DECISION = "probe_now"

#: Generous cap on the offer-side read (`causal_probe_decision_receipts` defaults
#: to `limit=200`, which would silently truncate a rate).
_PROBE_RECEIPT_LIMIT = 100_000


def probe_action_change_rate(repository: Repository) -> Metric:
    """Probes whose outcome changed the selected repair, over probes administered."""

    observations = repository.causal_discriminating_observations()
    administered = len(observations)
    changed = sum(
        1
        for row in observations
        if row.get("admitted") and row.get("resolved_factor")
    )
    by_outcome: dict[str, int] = {}
    for row in observations:
        outcome = str(row.get("outcome") or "unknown")
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

    offered = len(
        repository.causal_probe_decision_receipts(
            decision=_PROBE_NOW_DECISION, limit=_PROBE_RECEIPT_LIMIT
        )
    )
    decisions = len(
        repository.causal_probe_decision_receipts(limit=_PROBE_RECEIPT_LIMIT)
    )
    detail = {
        "probes_administered": administered,
        "probes_offered": offered,
        "probe_decisions_recorded": decisions,
        "observations_by_outcome": dict(sorted(by_outcome.items())),
        "admitted_observations": sum(
            1 for row in observations if row.get("admitted")
        ),
    }
    return _rate(
        "probe_action_change_rate",
        numerator=changed,
        denominator=administered,
        unit="rate",
        denominator_label="probes administered",
        note=(
            f"{changed} of {administered} administered probe(s) resolved the "
            f"factor and moved the repair; {offered} offered"
        ),
        empty_note=(
            "no probe has been administered yet"
            + (
                f" ({offered} offered, {decisions} probe decision(s) recorded)"
                if decisions
                else " — migration 130's writer became reachable only at Stage 2.1"
            )
        ),
        detail=detail,
    )


# ---------------------------------------------------------------------------
# 4.4 — planted_vs_adjudicated_agreement (scaffold)
# ---------------------------------------------------------------------------
#
# §3 B4: "Report agreement between the two on the overlap as a first-class
# metric. It is the only thing that licenses using the synthetic set to make
# decisions." The adjudicated side exists today
# (`diagnosis_adjudication.adjudicated_ground_truth`, which returns labels in the
# same shape a planted one must take, precisely so the planted harness never
# re-derives verdict semantics). The planted side is Stage 7 / B1.
#
# THE SEAM RETURNS `None`, NOT `{}`. An empty dict would flow through the
# comparison and produce "0 overlap", which renders as an available metric with
# an empty denominator — the exact confusion this module exists to prevent. A
# missing producer is a different fact from an empty producer and gets its own
# arm (`no_producer`).


def planted_ground_truth(repository: Repository) -> dict[str, dict[str, Any]] | None:
    """Licensed B1 labels keyed by attempt, or ``None`` without a license.

    A diagnostic-eval row counts only when B3 used different model families and
    B2's blind matcher found that generator's personas indistinguishable from
    real traces.  Unlicensed synthetic labels remain auditable in migration
    144, but deliberately look like no producer to every decision metric.
    """

    runs = repository.diagnostic_eval_run_rows()
    if not any(row.get("status") == "licensed" for row in runs):
        return None
    labels: dict[str, dict[str, Any]] = {}
    for row in repository.diagnostic_eval_case_rows(licensed_only=True):
        attempt_id = row.get("attempt_id")
        if not attempt_id:
            continue
        labels[str(attempt_id)] = {
            "should_abstain": bool(row.get("planted_should_abstain")),
            "anchor_key": str(row.get("planted_anchor_key") or "none"),
            "repair_class_id": row.get("planted_repair_class_id"),
            "repair_equivalence_id": row.get(
                "planted_repair_equivalence_id"
            ),
            "run_id": row.get("run_id"),
            "case_key": row.get("case_key"),
        }
    return labels


def planted_vs_adjudicated_agreement(repository: Repository) -> Metric:
    """B4 agreement on the planted/adjudicated overlap."""

    from learnloop.services.diagnosis_adjudication import adjudicated_ground_truth

    adjudicated = adjudicated_ground_truth(repository)
    planted = planted_ground_truth(repository)
    if planted is None:
        eval_runs = repository.diagnostic_eval_run_rows()
        if eval_runs:
            producer_note = (
                f"{len(eval_runs)} planted run(s) exist but none is licensed by "
                "both B2 realism and B3 cross-model separation"
            )
        else:
            producer_note = "the planted side has no Stage-7 B1 producer run"
        return _unavailable(
            "planted_vs_adjudicated_agreement",
            availability="no_producer",
            unit="rate",
            denominator_label="attempts labelled by both ground truths",
            note=(
                f"{producer_note}; "
                f"{len(adjudicated)} adjudicated label(s) are ready to join "
                "against"
            ),
            detail={
                "adjudicated_labels": len(adjudicated),
                "planted_labels": None,
                "overlap": None,
            },
        )

    overlap = sorted(set(planted) & set(adjudicated))
    agreements = 0
    disagreements: list[dict[str, Any]] = []
    for attempt_id in overlap:
        left, right = planted[attempt_id], adjudicated[attempt_id]
        same_abstention = bool(left.get("should_abstain")) == bool(
            right.get("should_abstain")
        )
        same_anchor = str(left.get("anchor_key") or "") == str(
            right.get("anchor_key") or ""
        )
        # Repair class is compared only when BOTH sides name one: a planted set
        # that declines to plant a repair must not be scored as disagreeing.
        left_repair = left.get("repair_class_id")
        right_repair = right.get("repair_class_id")
        same_repair = (
            str(left_repair) == str(right_repair)
            if left_repair and right_repair
            else True
        )
        if same_abstention and same_anchor and same_repair:
            agreements += 1
        elif len(disagreements) < 50:
            disagreements.append(
                {
                    "attempt_id": attempt_id,
                    "abstention_agrees": same_abstention,
                    "anchor_agrees": same_anchor,
                    "repair_agrees": same_repair,
                }
            )
    return _rate(
        "planted_vs_adjudicated_agreement",
        numerator=agreements,
        denominator=len(overlap),
        unit="rate",
        denominator_label="attempts labelled by both ground truths",
        note=(
            f"{agreements} of {len(overlap)} overlapping attempt(s) agree on "
            "abstention, anchor and (when both name one) repair class"
        ),
        empty_note=(
            f"no attempt carries both labels ({len(planted)} planted, "
            f"{len(adjudicated)} adjudicated)"
        ),
        detail={
            "adjudicated_labels": len(adjudicated),
            "planted_labels": len(planted),
            "overlap": len(overlap),
            "disagreements": disagreements,
        },
    )


# ---------------------------------------------------------------------------
# Composition seams: metrics other producers own
# ---------------------------------------------------------------------------
#
# `false_certification_rate` belongs to plan item 4.2, whose ground truth is the
# delayed cold probe (Meas §5.7: "one held-out-surface item per certified LO at
# +2-3 weeks ... in a single-learner vault the only external validity check
# available"). Reimplementing it here would produce a second, weaker definition
# of the one number §5.7 says licenses every speed claim — and §5.7 orders it
# first for the same reason B5 orders `problems_to_cold_success` first.
#
# So this is a seam, not a producer. Until 4.2 lands the metric reports
# `no_producer`: for a *false*-certification rate, a 0.0 would read as "no
# certificate has ever failed a delayed probe", which is the strongest possible
# claim the system could make and is exactly backwards.

#: Item 4.2's producer. `certification_cold_probe.false_certification_rate`
#: returns a `FalseCertificationRate`, which implements `keys()`/`__getitem__`
#: for exactly this seam — so `dict(...)` is the whole B5 entry and the seam
#: needs no adapter that could pick up a partial view of the metric.
#:
#: Resolved through `import_module` rather than a module-level `import` for one
#: reason: this module must stay importable if 4.2 is ever reverted, and the
#: refusal arm must be `no_producer` rather than an ImportError at collection
#: time. The name is exact — no candidate guessing.
_FALSE_CERTIFICATION_PRODUCER: tuple[str, str] = (
    "learnloop.services.certification_cold_probe",
    "false_certification_rate",
)


def _resolve_false_certification_producer() -> Callable[..., Any] | None:
    module_name, attribute = _FALSE_CERTIFICATION_PRODUCER
    try:
        module = import_module(module_name)
    except ImportError:  # pragma: no cover - only if 4.2 is reverted
        return None
    producer = getattr(module, attribute, None)
    return producer if callable(producer) else None


def false_certification_rate(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> Metric:
    """Composed from item 4.2's producer (Meas §5.7).

    `vault` is accepted and unused: 4.2's metric is deliberately repository-only
    ("the whole metric is readable from the probe queue plus the append-only
    outcome store"), and the one arm that needs a vault — certified but with no
    held-out surface to probe with — is an authoring finding that lives in
    `certification_cold_probe_report`, not in the rate. Keeping the parameter
    keeps this producer's signature uniform with the rest of the board.

    `clock` IS threaded, because 4.2 splits `awaiting_probe` from `probe_expired`
    on the current time — so a board rendered under a frozen clock must see the
    same split its own tests pinned.
    """

    _ = vault
    producer = _resolve_false_certification_producer()
    if producer is None:  # pragma: no cover - only if 4.2 is reverted
        return _unavailable(
            "false_certification_rate",
            availability="no_producer",
            unit="rate",
            denominator_label="certificates with a scored delayed cold probe",
            note=(
                "plan item 4.2 owns this producer (delayed cold probe, Meas "
                "§5.7); not present in this build. A 0.0 here would assert no "
                "certificate has ever failed"
            ),
            detail={"seam": ".".join(_FALSE_CERTIFICATION_PRODUCER)},
        )
    produced = producer(repository, clock=clock)
    if isinstance(produced, Metric):
        return replace(produced, name="false_certification_rate")
    payload = dict(produced)
    # 4.2 already holds the same discipline (`rate` is None, never 0.0, over an
    # empty denominator), so the empty arm here is a re-statement of its verdict
    # rather than a second decision — and its `unavailable_reason` is carried
    # through verbatim so the board does not paraphrase the producer.
    return _rate(
        "false_certification_rate",
        numerator=payload.get("numerator"),
        denominator=payload.get("denominator"),
        unit="rate",
        denominator_label=str(
            payload.get("denominator_definition")
            or "certificates with a scored delayed cold probe"
        ),
        note=str(payload.get("note") or "composed from item 4.2's producer"),
        empty_note=(
            "no certificate has a scored delayed cold probe yet"
            + (
                f" ({payload['unavailable_reason']})"
                if payload.get("unavailable_reason")
                else ""
            )
        ),
        detail={
            "composed_from": ".".join(_FALSE_CERTIFICATION_PRODUCER),
            **payload,
        },
    )


def _adjudication_metrics(repository: Repository) -> tuple[list[Metric], dict[str, Any]]:
    """The four metrics the A4 store already produces, composed not recomputed.

    `diagnosis_adjudication_scoreboard` returns all four *and* the
    grading-prompt-version x grader-model grouping B5 requires, and it already
    holds the empty-denominator discipline (`None`, never 1.0). Its `groups` ride
    through untouched so a reader can see whether one grader model is dragging
    the pooled number.
    """

    from learnloop.services.diagnosis_adjudication import (
        diagnosis_adjudication_scoreboard,
    )

    report = diagnosis_adjudication_scoreboard(repository, group_by="version")
    overall = report["overall"]
    confusion = overall["abstention_confusion"]
    predicted = confusion["tp"] + confusion["fp"]
    actual = confusion["tp"] + confusion["fn"]

    def composed(
        name: str,
        *,
        key: str,
        numerator: float,
        denominator: float,
        denominator_label: str,
        note: str,
        empty_note: str,
    ) -> Metric:
        metric = _rate(
            name,
            numerator=numerator,
            denominator=denominator,
            unit="rate",
            denominator_label=denominator_label,
            note=note,
            empty_note=empty_note,
            detail={
                "composed_from": (
                    "diagnosis_adjudication.diagnosis_adjudication_scoreboard"
                ),
                "producer_value": overall[key],
                "records": overall["records"],
                "groups": report["groups"],
            },
        )
        # The composition is only real if it agrees with the producer. A silent
        # reimplementation would drift here and nowhere else.
        assert metric.value == (
            round(overall[key], 6) if overall[key] is not None else None
        ), f"{name} disagrees with {report['store_version']}"
        return metric

    metrics = [
        composed(
            "first_divergence_anchor_accuracy",
            key="first_divergence_anchor_accuracy",
            numerator=overall["anchor_correct"],
            denominator=overall["anchor_scored"],
            denominator_label="adjudications that scored the system's anchor",
            note="adjudicated anchor matched the system's first-divergence anchor",
            empty_note="no adjudication has scored an anchor yet",
        ),
        composed(
            "repair_class_match_rate",
            key="repair_class_match_rate",
            numerator=overall["by_verdict"]["correct"],
            denominator=overall["anchor_scored"],
            denominator_label="adjudications that scored the system's anchor",
            note="verdict `correct` — the only one asserting the repair was right",
            empty_note="no adjudication has scored a repair yet",
        ),
        composed(
            "abstention_precision",
            key="abstention_precision",
            numerator=confusion["tp"],
            denominator=predicted,
            denominator_label="cases where the system abstained",
            note="the system abstained and the adjudicator agreed it should",
            empty_note=(
                "the system has never abstained on an adjudicated case — a "
                "precision of 1.0 over zero abstentions is false comfort"
            ),
        ),
        composed(
            "abstention_recall",
            key="abstention_recall",
            numerator=confusion["tp"],
            denominator=actual,
            denominator_label="cases where abstention was the right call",
            note="of the cases that warranted abstention, the system abstained",
            empty_note="no adjudicated case has warranted abstention yet",
        ),
    ]
    return metrics, report


def measurement_rank_metric(vault: LoadedVault) -> Metric:
    """Independent dimensions the item pool can resolve, vs facets declared.

    Composed from `identifiability.measurement_rank` over
    `identifiability.build_registry_view(vault, None)` — the vault-wide roll-up of
    the very call `subject_registry` already publishes per subject (plan 3.4).
    """

    from learnloop.services.identifiability import (
        build_registry_view,
        measurement_rank,
    )

    rank = measurement_rank(build_registry_view(vault, None))
    payload = rank.as_dict()
    return _rate(
        "measurement_rank",
        numerator=rank.independent_dimensions,
        denominator=rank.facets_declared,
        unit="dimensions",
        denominator_label="facets declared",
        note=(
            f"{rank.independent_dimensions} independent dimension(s) over "
            f"{rank.facets_declared} declared facet(s); deficit {rank.deficit} "
            f"({rank.deficit_from_unobserved} unobserved, "
            f"{rank.deficit_from_collapse} collapsed)"
        ),
        empty_note="no facet is declared in this vault",
        detail={
            "composed_from": "identifiability.measurement_rank",
            **payload,
        },
    )


# ---------------------------------------------------------------------------
# The board
# ---------------------------------------------------------------------------


def scoreboard(
    vault: LoadedVault,
    repository: Repository,
    *,
    replay: bool = False,
    replay_budget: int = DEFAULT_REPLAY_BUDGET,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The whole §3 B5 board, in B5's frozen order.

    Read-only with one exception the caller opts into: `replay=True` copies the
    sqlite file into a temporary directory and mutates the COPY. The live vault
    is never written.
    """

    problems, minutes = cold_success_metrics(repository)
    questions, regret = certification_efficiency_metrics(
        vault, repository, replay=replay, budget=replay_budget
    )
    adjudication, adjudication_report = _adjudication_metrics(repository)

    metrics: dict[str, Metric] = {
        metric.name: metric
        for metric in [
            problems,
            minutes,
            harmful_write_rate(repository),
            *adjudication,
            probe_action_change_rate(repository),
            tokens_per_resolved_diagnostic_episode(repository),
            planted_vs_adjudicated_agreement(repository),
            false_certification_rate(vault, repository, clock=clock),
            questions,
            regret,
            cells_cleared_per_question(vault, repository),
            measurement_rank_metric(vault),
        ]
    }
    missing = set(B5_ORDER) - set(metrics)
    if missing:  # pragma: no cover - guards the frozen list against drift
        raise AssertionError(f"B5 board is missing producers for {sorted(missing)}")
    extra = set(metrics) - set(B5_ORDER)
    if extra:  # pragma: no cover
        raise AssertionError(f"metrics not on the frozen B5 board: {sorted(extra)}")

    ordered = [metrics[name] for name in B5_ORDER]
    return {
        "scoreboard_version": SCOREBOARD_VERSION,
        "order": list(B5_ORDER),
        # The ordering argument, carried in the payload so a consumer that
        # re-sorts the board has to do it against a stated reason.
        "order_rationale": (
            "Aug §3 B5: problems_to_cold_success and harmful_write_rate lead "
            "because a system can raise anchor accuracy while becoming slower "
            "and more interrogative, and every other metric would report "
            "success. Meas §5.7 orders false_certification_rate ahead of the "
            "rest of its block for the same reason."
        ),
        "metrics": [metric.as_dict() for metric in ordered],
        "availability_counts": {
            arm: sum(1 for metric in ordered if metric.availability == arm)
            for arm in AVAILABILITY
        },
        "available": sum(1 for metric in ordered if metric.available),
        "unavailable": [
            {"name": metric.name, "availability": metric.availability, "note": metric.note}
            for metric in ordered
            if not metric.available
        ],
        "adjudication_report": adjudication_report,
    }
