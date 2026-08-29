from __future__ import annotations

import math
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.goals.goal_projection import (
    _attempts_to_certify,
    build_goal_frontier,
    goal_report,
    resolve_goal_scope,
)
from learnloop.goals.goal_pace import compute_goal_pace
from learnloop.learner.recall_coverage import expected_facet_mass_gain
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
FACET_ID = "recall"


def _loaded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


# The basic vault's only item is `short_answer` on facet "recall", which compiles
# to capability `schema_interpretation`. Cells below are positioned against that
# single instrument on the ladder retrieval(0) < schema_interpretation(1) <
# procedure_execution(2) < method_selection(3) < coordination(4).
INSTRUMENT_CAPABILITY = "schema_interpretation"


def _loaded_with_contract(tmp_path, components):
    """``_loaded`` but ``lo_svd_definition`` first declares a blueprint.

    ``components`` are ``(facet, capability)`` pairs authored as hard ``all_of``
    requirements — i.e. real contract cells that certification must close.
    """

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    data["blueprints"] = [
        {
            "id": "bp1",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "r1",
                    "composition": "conjunctive",
                    "all_of": [
                        {"facet": facet, "capability": capability, "modality": "hard"}
                        for facet, capability in components
                    ],
                }
            ],
        }
    ]
    write_yaml(lo_path, data)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


def _due_iso(days: float) -> str:
    return (NOW + timedelta(days=days)).isoformat()


def _seed_aggregate_facet(
    repository,
    *,
    mean: float,
    mass: float = 2.0,
    facet_id: str = FACET_ID,
    last_attempt_at: str = "2026-05-16T12:00:00Z",
) -> None:
    """Directly seed an aggregate (practice_item_id NULL) facet recall row.

    Beta recall states carry no time decay, so seeding the mean/mass gives us
    a deterministic ``current_recall`` and diagnostic label to project from.
    """

    with repository.connection() as connection:
        repository._upsert_facet_recall_state(
            connection,
            {
                "learning_object_id": LO_ID,
                "facet_id": facet_id,
                "practice_item_id": None,
                "recall_alpha": mean * 10.0,
                "recall_beta": (1.0 - mean) * 10.0,
                "recall_mean": mean,
                "recall_variance": 0.01,
                "independent_evidence_mass": mass,
                "raw_coverage_mass": mass,
                "last_attempt_at": last_attempt_at,
                "last_error_at": None,
                "consecutive_failures": 0,
                "algorithm_version": ALGORITHM_VERSION,
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
        )


def _recall_projection(report):
    return next(facet for facet in report.facets if facet.facet_id == FACET_ID)


def test_unexamined_facet_is_on_frontier_and_not_on_track(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    assert projection.label == "unexamined"
    assert projection.current_recall is None
    assert projection.projected_recall is None
    assert projection.on_track is False
    assert report.on_track_count == 0
    assert report.total == 1

    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert LO_ID in frontier.by_lo
    assert FACET_ID in frontier.by_lo[LO_ID].facets
    assert frontier.by_lo[LO_ID].goal_priority == pytest.approx(0.8)
    assert frontier.active_goal_ids == [vault.goals[0].id]


def test_solid_facet_above_target_no_decay_info_is_on_track(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.95)
    # No FSRS stability => no decay information => projection holds recall flat.
    repository.upsert_practice_item_state(
        ITEM_ID,
        difficulty=5.0,
        stability=None,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    assert projection.label == "solid"
    assert projection.current_recall == pytest.approx(0.95)
    assert projection.projected_recall == pytest.approx(0.95)
    assert projection.on_track is True

    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert LO_ID not in frontier.by_lo
    assert frontier.active_goal_ids == []
    assert frontier.quota_floor == 0.0


def test_solid_facet_decays_below_target_lands_on_frontier(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.9)
    # Low stability so recall erodes over a distant horizon.
    repository.upsert_practice_item_state(
        ITEM_ID,
        difficulty=5.0,
        stability=1.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )
    vault.goals[0].due_at = _due_iso(120)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    assert projection.label == "solid"
    # Current recall is above target, but the projection at the due date is not.
    assert projection.current_recall >= vault.goals[0].target_recall
    assert projection.projected_recall < vault.goals[0].target_recall
    assert projection.on_track is False

    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert FACET_ID in frontier.by_lo[LO_ID].facets


def test_projection_is_monotonically_non_increasing_with_horizon(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.9)  # stability 2.0 from seed_due_item

    previous = None
    for days in (1, 10, 30, 90, 365):
        vault.goals[0].due_at = _due_iso(days)
        report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
        projected = _recall_projection(report).projected_recall
        assert projected is not None
        if previous is not None:
            assert projected <= previous + 1e-9
        previous = projected


def test_high_mastery_low_mass_is_on_track_but_uncertified_and_at_risk(tmp_path):
    """The two axes are independent: attainment can lead certification."""

    vault, _paths, repository = _loaded(tmp_path)
    vault.goals[0].due_at = _due_iso(1)  # near horizon: negligible FSRS decay
    _seed_aggregate_facet(repository, mean=0.6, mass=0.2)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=2.5,
            logit_variance=0.5,
            evidence_count=6,
            last_evidence_at=NOW_ISO,
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    assert projection.predicted_current > 0.85
    assert projection.on_track is True
    assert projection.certified is False  # mass 0.2 < 0.5 gate
    assert projection.at_risk is True
    assert report.on_track_count == 1
    assert report.certified_count == 0
    assert report.at_risk_count == 1

    # Still on the frontier: the scheduler keeps driving toward certification.
    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert FACET_ID in frontier.by_lo[LO_ID].facets


def test_attempts_to_certify_inverts_the_mass_equation(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    assert projection.evidence_mass == 0.0

    item = vault.practice_items[ITEM_ID]
    gain = expected_facet_mass_gain(item, vault.rubric_for_item(item), vault.config.evidence)[
        FACET_ID
    ]
    min_mass = vault.config.recall_coverage.min_facet_evidence_mass
    expected = math.ceil((min_mass + 1e-6) / (0.75 * gain))
    assert projection.attempts_to_certify == expected

    # Certified AND attained facets need nothing further. Mass well past the gate
    # and a near horizon keep both axes quiet, so 0 here really does mean 0.
    vault.goals[0].due_at = _due_iso(1)
    _seed_aggregate_facet(repository, mean=0.99, mass=8.0)
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    settled = _recall_projection(report)
    assert settled.at_risk is False
    assert settled.attempts_to_certify == 0
    assert settled.attempts_is_lower_bound is False
    assert report.attempts_remaining_is_partial is False


def test_attempts_to_certify_inversion_edge_cases():
    # No supporting items covering the facet: the count is unknowable.
    assert _attempts_to_certify("facet", 0.0, {}, 0.5) is None
    assert _attempts_to_certify("facet", 0.0, {"other": [0.25]}, 0.5) is None
    # Mass gate already cleared: nothing further needed.
    assert _attempts_to_certify("facet", 0.6, {"facet": [0.25]}, 0.5) == 0
    # Median of gains drives the estimate, capped at 99.
    assert _attempts_to_certify("facet", 0.0, {"facet": [0.2, 0.3]}, 0.5) == math.ceil(
        (0.5 + 1e-6) / (0.75 * 0.25)
    )
    assert _attempts_to_certify("facet", 0.0, {"facet": [1e-9]}, 0.5) == 99


def _pace(vault, repository, report):
    return compute_goal_pace(
        vault, repository, vault.goals[0], report, clock=FrozenClock(NOW)
    )


def test_unreachable_contract_cell_makes_attempts_unknowable(tmp_path):
    """A cell no instrument can observe has no attempt count — only the fiction.

    ``recall`` is required at ``coordination`` and the vault's single item
    observes it at ``schema_interpretation``: MISMATCH_BELOW, and dominance only
    propagates downward, so no amount of practice closes the cell. The mass
    inversion would happily quote a number anyway (it only knows about evidence
    mass), which is the dishonesty: attempts that can never certify.
    """

    vault, _paths, repository = _loaded_with_contract(
        tmp_path, [("recall", "coordination")]
    )
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)

    assert projection.at_risk is True
    assert projection.certification_reachable is False
    assert projection.attempts_to_certify is None
    assert report.attempts_remaining == 0
    assert report.attempts_remaining_is_partial is True

    # The honest arm of the pace read-model: unknowable, not "done".
    pace = _pace(vault, repository, report)
    assert pace.attempts_remaining is None
    assert pace.needed_per_day is None
    assert pace.on_pace is None


def test_one_uncloseable_rung_abstains_for_the_whole_facet(tmp_path):
    """Both unreachable verdicts abstain, and a reachable sibling cell cannot rescue.

    ``recall`` carries a reachable cell *and* an uncloseable one — the LO's hard
    components are conjunctive, so having somewhere to put evidence is not the
    same as being able to certify, and the facet abstains. ``uninstrumented`` has
    nothing observing it at any capability (NO_INSTRUMENT) and abstains too.
    """

    vault, _paths, repository = _loaded_with_contract(
        tmp_path,
        [
            ("recall", INSTRUMENT_CAPABILITY),   # REACHABLE
            ("recall", "coordination"),          # MISMATCH_BELOW
            ("uninstrumented", "procedure_execution"),  # NO_INSTRUMENT
        ],
    )
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    by_facet = {facet.facet_id: facet for facet in report.facets}
    assert set(by_facet) == {"recall", "uninstrumented"}

    for facet_id in ("recall", "uninstrumented"):
        assert by_facet[facet_id].certification_reachable is False
        assert by_facet[facet_id].attempts_to_certify is None
    assert report.attempts_remaining_is_partial is True


def test_fully_reachable_contract_keeps_the_legacy_estimate(tmp_path):
    """A contract every cell of which is closeable changes nothing at all."""

    legacy_vault, _legacy_paths, legacy_repository = _loaded(tmp_path / "legacy")
    legacy = _recall_projection(
        goal_report(
            legacy_vault, legacy_repository, legacy_vault.goals[0], clock=FrozenClock(NOW)
        )
    )

    vault, _paths, repository = _loaded_with_contract(
        tmp_path / "contracted", [("recall", INSTRUMENT_CAPABILITY)]
    )
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)

    assert projection.certification_reachable is True
    assert projection.attempts_to_certify == legacy.attempts_to_certify
    assert projection.attempts_to_certify is not None
    assert report.attempts_remaining == legacy.attempts_to_certify
    assert report.attempts_remaining_is_partial is False


def test_legacy_lo_without_a_contract_is_untouched(tmp_path):
    """No blueprint, no cells: reachability has nothing to say, so it says nothing."""

    vault, _paths, repository = _loaded(tmp_path)
    assert vault.learning_objects[LO_ID].blueprints == []

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)

    item = vault.practice_items[ITEM_ID]
    gain = expected_facet_mass_gain(item, vault.rubric_for_item(item), vault.config.evidence)[
        FACET_ID
    ]
    min_mass = vault.config.recall_coverage.min_facet_evidence_mass
    assert projection.certification_reachable is True
    assert projection.attempts_to_certify == math.ceil((min_mass + 1e-6) / (0.75 * gain))
    assert report.attempts_remaining_is_partial is False


def test_mismatch_above_is_not_treated_as_unreachable(tmp_path):
    """The evidence exists one rung up: the remedy is projection, not attempts.

    Abstaining here would overstate the gap — §5.8.2's B1 downward-dominance
    propagation closes these cells without a single new instrument.
    """

    vault, _paths, repository = _loaded_with_contract(tmp_path, [("recall", "retrieval")])
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)

    assert projection.certification_reachable is True
    assert projection.attempts_to_certify is not None
    assert report.attempts_remaining_is_partial is False


def test_decayed_certified_facet_reports_a_floor_not_zero(tmp_path):
    """The retention axis of ``at_risk`` may not report "nothing outstanding".

    Mass-certified but projected below target: the mass inversion has nothing
    left to ask for, and its plain ``0`` reads as "all facets certified — hold
    the line" for a facet that is demonstrably losing the line.
    """

    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.9, mass=2.0)
    repository.upsert_practice_item_state(
        ITEM_ID,
        difficulty=5.0,
        stability=1.0,
        due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z",
        active=True,
    )
    vault.goals[0].due_at = _due_iso(120)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)

    assert projection.certified is True         # mass gate cleared
    assert projection.on_track is False         # attainment axis is not
    assert projection.at_risk is True
    assert projection.attempts_to_certify == 1  # a floor, deliberately not a forecast
    assert projection.attempts_is_lower_bound is True
    assert report.attempts_remaining == 1
    assert report.attempts_remaining_is_partial is True

    # A lower bound is still a number: the pace sentence keeps its "at least"
    # arm rather than collapsing to the unknowable one.
    pace = _pace(vault, repository, report)
    assert pace.attempts_remaining == 1


def test_attainment_aggregates(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.9, mass=2.0)

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    target = vault.goals[0].target_recall
    expected_attainment = sum(
        min(facet.predicted_at_horizon / target, 1.0) for facet in report.facets
    ) / len(report.facets)
    assert report.attainment_fraction == pytest.approx(expected_attainment)
    assert report.predicted_recall_mean == pytest.approx(
        sum(facet.predicted_at_horizon for facet in report.facets) / len(report.facets)
    )
    assert 0.0 < report.attainment_fraction <= 1.0
    assert projection.predicted_at_horizon <= projection.predicted_current


def test_known_gap_facet_is_never_on_track(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.95, mass=2.0)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )
    _seed_aggregate_facet(repository, mean=0.95, mass=2.0)  # re-pin after the attempt's update
    # Resolved uncertainty whose winning hypothesis is NOT facet_solid => known_gap.
    repository.upsert_facet_uncertainty_state(
        {
            "learning_object_id": LO_ID,
            "facet_id": FACET_ID,
            "hypothesis_marginal": {f"facet_absent:{FACET_ID}": 0.9, f"facet_solid:{FACET_ID}": 0.1},
            "uncertainty": 0.05,
            "status": "resolved",
            "opened_by_attempt_id": attempt.attempt_id,
            "opened_reason": "low_facet_outcome",
            "last_evidence_at": NOW_ISO,
            "algorithm_version": ALGORITHM_VERSION,
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )

    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _recall_projection(report)
    assert projection.label == "known_gap"
    assert projection.on_track is False
    assert projection.at_risk is True
    # The other false zero: mass is past the gate, so the inversion has nothing
    # left to ask for — but the gap is open and certification is refused, so a
    # plain 0 would read as "done". Report the floor and say it is one.
    assert projection.attempts_to_certify == 1
    assert projection.attempts_is_lower_bound is True
    assert report.attempts_remaining_is_partial is True


def test_quota_floor_open_ended_goal_uses_floor_min(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)  # goal due_at is None, facet unexamined
    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert frontier.quota_floor == pytest.approx(vault.config.scheduler.goal_quota_floor_min)


def test_quota_floor_interpolates_within_ramp_window(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    scheduler = vault.config.scheduler
    remaining = scheduler.goal_quota_ramp_days / 2  # halfway through the ramp
    vault.goals[0].due_at = _due_iso(remaining)

    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    ramp = (scheduler.goal_quota_ramp_days - remaining) / scheduler.goal_quota_ramp_days
    expected = scheduler.goal_quota_floor_min + (
        scheduler.goal_quota_floor_max - scheduler.goal_quota_floor_min
    ) * ramp
    assert frontier.quota_floor == pytest.approx(expected)


def test_quota_floor_past_due_uses_floor_max(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    vault.goals[0].due_at = _due_iso(-1)

    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert frontier.quota_floor == pytest.approx(vault.config.scheduler.goal_quota_floor_max)


def test_quota_floor_zero_when_no_active_frontier(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    vault.goals[0].status = "paused"

    frontier = build_goal_frontier(vault, repository, clock=FrozenClock(NOW))
    assert frontier.quota_floor == 0.0
    assert frontier.active_goal_ids == []
    assert frontier.by_lo == {}


def test_legacy_v1_goal_converts_and_scope_resolves(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 1,
            "goals": [
                {
                    "id": "goal_legacy",
                    "title": "Legacy goal",
                    "status": "active",
                    "concept_anchors": ["singular_value_decomposition"],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)

    goal = vault.goals[0]
    assert goal.facet_scope.concepts == ["singular_value_decomposition"]
    scope = resolve_goal_scope(vault, goal, repository)
    assert scope.get(LO_ID) == {FACET_ID}


def test_explicit_facet_scope_adds_facet_without_listing_concept(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 2,
            "goals": [
                {
                    "id": "goal_facet_only",
                    "title": "Facet-only goal",
                    "status": "active",
                    "facet_scope": {"concepts": [], "facets": [FACET_ID]},
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                }
            ],
        },
    )
    repository = seed_due_item(paths)
    vault = load_vault(vault_root)

    goal = vault.goals[0]
    assert goal.facet_scope.concepts == []
    scope = resolve_goal_scope(vault, goal, repository)
    assert scope.get(LO_ID) == {FACET_ID}
