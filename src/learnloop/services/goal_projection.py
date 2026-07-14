"""Forward projection of facet recall against a goal's due date.

Goals commit to a ``target_recall`` over a facet set by a ``due_at`` (or, for
open-ended goals, the default projection horizon). Deciding whether a facet is
*on track* requires projecting its recall forward to that horizon.

Facet recall states are beta distributions with **no time decay** (the mean is
evidence, not a memory trace). The forgetting information lives on FSRS per
*practice item* (``stability`` + ``last_attempt_at``). So a facet-level forward
projection must be derived from the FSRS states of the items that carry
evidence for that facet.

MVP approximation (documented deliberately, so a later model can replace it):

  * ``current_recall`` is the aggregate facet recall mean.
  * For each active supporting item (an active practice item whose evidence
    weight for the facet is > 0) that has an FSRS ``stability`` and a parseable
    ``last_attempt_at``, we form a *retention ratio* — the FSRS forgetting
    curve at the horizon divided by the curve at ``now`` — and take the
    evidence-weighted mean across items. ``projected_recall`` is
    ``current_recall`` scaled by that mean.
  * When no supporting item carries decay information, ``projected_recall`` is
    just ``current_recall``. This is *no decay information*, which is not the
    same as *no decay* — we simply cannot do better without an FSRS state, so we
    hold recall flat rather than inventing a curve.
  * When there is no aggregate recall state at all, both ``current_recall`` and
    ``projected_recall`` are ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from statistics import median

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import FacetRecallState, MasteryState, PracticeItemState, Repository
from learnloop.numeric import clamp
from learnloop.services.facet_diagnostics import facet_state_label, required_facets
from learnloop.services.facet_state_reader import (
    facet_states_by_lo as read_facet_states_by_lo,
)
from learnloop.services.facet_state_reader import facet_uncertainty_states_for_lo
from learnloop.services.fitted_params import resolve_fsrs_weights
from learnloop.services.fsrs import forgetting_curve
from learnloop.services.recall_coverage import expected_facet_mass_gain
from learnloop.services.selection_rewards import predicted_facet_recall
from learnloop.vault.models import Goal, LoadedVault

# Attempts-to-certify inversion assumes fresh-ish practice: the familiarity
# discount for a distinct item starts at 1.0 and decays toward 0.20 when
# re-drilling; 0.75 is an honest middle for a short remediation run.
_ASSUMED_FRESH_DISCOUNT = 0.75


@dataclass(frozen=True)
class FacetProjection:
    learning_object_id: str
    facet_id: str
    label: str                      # unexamined | uncertain | known_gap | solid
    current_recall: float | None    # aggregate recall_mean; None when no aggregate state
    projected_recall: float | None  # raw mean forward-projected to the horizon; None when no aggregate state
    on_track: bool                  # attainment axis: predicted_at_horizon >= target (and no known gap)
    predicted_current: float        # mastery-blended predicted recall now (predicted_facet_recall)
    predicted_at_horizon: float     # predicted_current x FSRS retention ratio at the horizon
    evidence_mass: float            # aggregate independent evidence mass
    certified: bool                 # coverage axis: label == "solid" (mass gate cleared, no open gap)
    attempts_to_certify: int | None  # ~fresh attempts to clear the mass gate; None = no supporting items

    @property
    def at_risk(self) -> bool:
        """Needs work for the goal: not attained OR not yet certified."""

        return not self.on_track or not self.certified


@dataclass(frozen=True)
class GoalReport:
    goal_id: str
    target_recall: float
    due_at: datetime | None
    horizon: datetime
    facets: list[FacetProjection]

    @property
    def on_track_count(self) -> int:
        return sum(1 for facet in self.facets if facet.on_track)

    @property
    def total(self) -> int:
        return len(self.facets)

    @property
    def certified_count(self) -> int:
        return sum(1 for facet in self.facets if facet.certified)

    @property
    def examined_count(self) -> int:
        return sum(1 for facet in self.facets if facet.label != "unexamined")

    @property
    def at_risk_count(self) -> int:
        return sum(1 for facet in self.facets if facet.at_risk)

    @property
    def attainment_fraction(self) -> float | None:
        """Mean per-facet progress toward target (clamped ratio), the headline %."""

        if not self.facets or self.target_recall <= 0:
            return None
        return sum(
            clamp(facet.predicted_at_horizon / self.target_recall) for facet in self.facets
        ) / len(self.facets)

    @property
    def predicted_recall_mean(self) -> float | None:
        if not self.facets:
            return None
        return sum(facet.predicted_at_horizon for facet in self.facets) / len(self.facets)

    @property
    def attempts_remaining(self) -> int:
        return sum(
            facet.attempts_to_certify
            for facet in self.facets
            if facet.at_risk and facet.attempts_to_certify is not None
        )

    @property
    def attempts_remaining_is_partial(self) -> bool:
        return any(
            facet.attempts_to_certify is None for facet in self.facets if facet.at_risk
        )


@dataclass(frozen=True)
class FrontierEntry:
    facets: set[str]        # facet ids not on track for some active goal, for this LO
    goal_priority: float    # max priority among contributing active goals


@dataclass(frozen=True)
class GoalFrontier:
    by_lo: dict[str, FrontierEntry]
    active_goal_ids: list[str]   # active goals with a non-empty frontier
    quota_floor: float           # resolved queue-composition floor; 0.0 when no active goal has frontier


def resolve_goal_scope(
    vault: LoadedVault,
    goal: Goal,
    repository: Repository,
) -> dict[str, set[str]]:
    """``lo_id -> set of canonical facet ids`` in the goal's scope.

    An active LO whose concept is in ``goal.facet_scope.concepts`` contributes
    all of its (canonicalized) required facets. Each explicit facet id in
    ``goal.facet_scope.facets`` is additionally attached to any active LO whose
    required facets already contain it. LOs that end up with no facets are
    omitted.
    """

    concept_scope = set(goal.facet_scope.concepts)
    explicit_facets = {vault.canonical_facet_id(str(facet)) for facet in goal.facet_scope.facets}
    scope: dict[str, set[str]] = {}
    for learning_object_id, learning_object in vault.learning_objects.items():
        if learning_object.status != "active":
            continue
        required = {
            vault.canonical_facet_id(str(facet))
            for facet in required_facets(vault, learning_object_id, repository)
        }
        if not required:
            continue
        facets: set[str] = set()
        if learning_object.concept in concept_scope:
            facets |= required
        facets |= explicit_facets & required
        if facets:
            scope[learning_object_id] = facets
    return scope


def _supporting_weight(vault: LoadedVault, item, facet_id: str) -> float:
    """The item's evidence weight for ``facet_id`` (0.0 when not a support)."""

    if item.evidence_weights:
        weights = {
            vault.canonical_facet_id(str(facet)): float(weight)
            for facet, weight in item.evidence_weights.items()
        }
    else:
        weights = {vault.canonical_facet_id(str(facet)): 1.0 for facet in item.evidence_facets}
    return max(weights.get(facet_id, 0.0), 0.0)


def _retention_ratio(
    vault: LoadedVault,
    learning_object_id: str,
    facet_id: str,
    *,
    now: datetime,
    horizon: datetime,
    item_states: dict[str, PracticeItemState],
    fsrs_weights: tuple[float, ...],
) -> float:
    """Evidence-weighted FSRS retention ratio (horizon vs now) for one facet.

    1.0 when no supporting item carries decay information — *no decay
    information*, which is not the same as *no decay*: we hold recall flat
    rather than inventing a curve.
    """

    numerator = 0.0
    weight_total = 0.0
    for item in vault.practice_items.values():
        if item.learning_object_id != learning_object_id:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        weight = _supporting_weight(vault, item, facet_id)
        if weight <= 0.0:
            continue
        if state is None or state.stability is None:
            continue
        last_attempt = parse_utc(state.last_attempt_at)
        if last_attempt is None:
            continue
        horizon_days = (horizon - last_attempt).total_seconds() / 86400
        now_days = (now - last_attempt).total_seconds() / 86400
        baseline = max(forgetting_curve(state.stability, now_days, fsrs_weights), 1e-6)
        retention_ratio = clamp(forgetting_curve(state.stability, horizon_days, fsrs_weights) / baseline)
        numerator += weight * retention_ratio
        weight_total += weight
    if weight_total <= 0.0:
        return 1.0
    return numerator / weight_total


def _attempts_to_certify(
    facet_id: str,
    evidence_mass: float,
    mass_gain_by_facet: dict[str, list[float]],
    min_mass: float,
) -> int | None:
    """Invert the mass equation into a coarse fresh-attempt count (None = no items)."""

    gap = max(0.0, min_mass + 1e-6 - evidence_mass)
    if gap <= 0.0:
        return 0
    gains = mass_gain_by_facet.get(facet_id)
    if not gains:
        return None
    delta = _ASSUMED_FRESH_DISCOUNT * median(gains)
    if delta <= 0.0:
        return None
    return min(ceil(gap / delta), 99)


def _lo_mass_gains(
    vault: LoadedVault,
    learning_object_id: str,
    item_states: dict[str, PracticeItemState],
) -> dict[str, list[float]]:
    """Per canonical facet id, the nominal mass gain of each active item covering it."""

    gains: dict[str, list[float]] = {}
    for item in vault.practice_items.values():
        if item.learning_object_id != learning_object_id:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        gain_map = expected_facet_mass_gain(item, vault.rubric_for_item(item), vault.config.evidence)
        for facet, gain in gain_map.items():
            if gain <= 0.0:
                continue
            gains.setdefault(vault.canonical_facet_id(str(facet)), []).append(gain)
    return gains


def _facet_projections(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    now: datetime,
    horizon: datetime,
    item_states: dict[str, PracticeItemState],
    facet_states_by_lo: dict[str, list[FacetRecallState]],
    mastery_states: dict[str, MasteryState],
    fsrs_weights: tuple[float, ...],
) -> list[FacetProjection]:
    scope = resolve_goal_scope(vault, goal, repository)
    min_mass = vault.config.recall_coverage.min_facet_evidence_mass
    blend_count = vault.config.recall_coverage.facet_blend_evidence_count
    projections: list[FacetProjection] = []
    for learning_object_id in sorted(scope):
        # Keyed by canonical facet id; alias rows fold onto the canonical entry
        # (highest evidence mass wins, matching the aggregate's intent).
        recall_by_facet: dict[str, FacetRecallState] = {}
        for state in facet_states_by_lo.get(learning_object_id, []):
            if state.practice_item_id is not None:
                continue
            key = vault.canonical_facet_id(state.facet_id)
            existing = recall_by_facet.get(key)
            if existing is None or state.independent_evidence_mass > existing.independent_evidence_mass:
                recall_by_facet[key] = state
        uncertainty_by_facet = {
            vault.canonical_facet_id(state.facet_id): state
            for state in facet_uncertainty_states_for_lo(vault, repository, learning_object_id)
        }
        mastery = mastery_states.get(learning_object_id)
        mass_gain_by_facet = _lo_mass_gains(vault, learning_object_id, item_states)
        for facet_id in sorted(scope[learning_object_id]):
            recall_state = recall_by_facet.get(facet_id)
            uncertainty_state = uncertainty_by_facet.get(facet_id)
            label = facet_state_label(facet_id, uncertainty_state, recall_state, min_mass)
            current_recall = recall_state.recall_mean if recall_state is not None else None
            evidence_mass = (
                max(recall_state.independent_evidence_mass, 0.0) if recall_state is not None else 0.0
            )
            retention = _retention_ratio(
                vault,
                learning_object_id,
                facet_id,
                now=now,
                horizon=horizon,
                item_states=item_states,
                fsrs_weights=fsrs_weights,
            )
            projected_recall = current_recall * retention if current_recall is not None else None
            predicted_current = predicted_facet_recall(
                mastery.logit_mean if mastery is not None else None,
                mastery.evidence_count if mastery is not None else 0,
                current_recall,
                evidence_mass,
                blend_count,
            )
            predicted_at_horizon = clamp(predicted_current * retention)
            certified = label == "solid"
            on_track = predicted_at_horizon >= goal.target_recall and label != "known_gap"
            projections.append(
                FacetProjection(
                    learning_object_id=learning_object_id,
                    facet_id=facet_id,
                    label=label,
                    current_recall=current_recall,
                    projected_recall=projected_recall,
                    on_track=on_track,
                    predicted_current=predicted_current,
                    predicted_at_horizon=predicted_at_horizon,
                    evidence_mass=evidence_mass,
                    certified=certified,
                    attempts_to_certify=_attempts_to_certify(
                        facet_id, evidence_mass, mass_gain_by_facet, min_mass
                    ),
                )
            )
    return projections


def _horizon(vault: LoadedVault, goal: Goal, now: datetime) -> tuple[datetime | None, datetime]:
    due_at = parse_utc(goal.due_at)
    if due_at is not None:
        return due_at, due_at
    horizon = now + timedelta(days=vault.config.goals.default_projection_horizon_days)
    return None, horizon


def goal_report(
    vault: LoadedVault,
    repository: Repository,
    goal: Goal,
    *,
    clock: Clock | None = None,
) -> GoalReport:
    now = (clock or SystemClock()).now().astimezone(UTC)
    due_at, horizon = _horizon(vault, goal, now)
    item_states = repository.practice_item_states()
    facet_states_by_lo = read_facet_states_by_lo(vault, repository)
    mastery_states = repository.mastery_states()
    fsrs_weights = resolve_fsrs_weights(repository)
    facets = _facet_projections(
        vault,
        repository,
        goal,
        now=now,
        horizon=horizon,
        item_states=item_states,
        facet_states_by_lo=facet_states_by_lo,
        mastery_states=mastery_states,
        fsrs_weights=fsrs_weights,
    )
    return GoalReport(
        goal_id=goal.id,
        target_recall=goal.target_recall,
        due_at=due_at,
        horizon=horizon,
        facets=facets,
    )


def _quota_floor_for_goal(goal: Goal, config, now: datetime) -> float:
    scheduler = config.scheduler
    floor_min = scheduler.goal_quota_floor_min
    floor_max = scheduler.goal_quota_floor_max
    ramp_days = scheduler.goal_quota_ramp_days
    due_at = parse_utc(goal.due_at)
    if due_at is None:
        return floor_min
    remaining_days = (due_at - now).total_seconds() / 86400
    if remaining_days <= 0:
        return floor_max
    ramp = clamp((ramp_days - remaining_days) / ramp_days) if ramp_days else 1.0
    return floor_min + (floor_max - floor_min) * ramp


def build_goal_frontier(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
    item_states: dict[str, PracticeItemState] | None = None,
    facet_states_by_lo: dict[str, list[FacetRecallState]] | None = None,
    mastery_states: dict[str, MasteryState] | None = None,
) -> GoalFrontier:
    now = (clock or SystemClock()).now().astimezone(UTC)
    if item_states is None:
        item_states = repository.practice_item_states()
    if facet_states_by_lo is None:
        facet_states_by_lo = read_facet_states_by_lo(vault, repository)
    if mastery_states is None:
        mastery_states = repository.mastery_states()
    fsrs_weights = resolve_fsrs_weights(repository)

    by_lo: dict[str, FrontierEntry] = {}
    active_goal_ids: list[str] = []
    quota_floor = 0.0
    for goal in vault.goals:
        if goal.status != "active":
            continue
        _, horizon = _horizon(vault, goal, now)
        projections = _facet_projections(
            vault,
            repository,
            goal,
            now=now,
            horizon=horizon,
            item_states=item_states,
            facet_states_by_lo=facet_states_by_lo,
            mastery_states=mastery_states,
            fsrs_weights=fsrs_weights,
        )
        # Frontier keeps every facet needing work on either axis: unattained
        # (predicted below target) or unattained certification (mass gate) —
        # so the scheduler still drives certified-but-unattained and
        # attained-but-uncertified facets alike.
        at_risk = [projection for projection in projections if projection.at_risk]
        if not at_risk:
            continue
        active_goal_ids.append(goal.id)
        quota_floor = max(quota_floor, _quota_floor_for_goal(goal, vault.config, now))
        for projection in at_risk:
            existing = by_lo.get(projection.learning_object_id)
            if existing is None:
                by_lo[projection.learning_object_id] = FrontierEntry(
                    facets={projection.facet_id},
                    goal_priority=goal.priority,
                )
            else:
                by_lo[projection.learning_object_id] = FrontierEntry(
                    facets=existing.facets | {projection.facet_id},
                    goal_priority=max(existing.goal_priority, goal.priority),
                )
    return GoalFrontier(by_lo=by_lo, active_goal_ids=active_goal_ids, quota_floor=quota_floor)
