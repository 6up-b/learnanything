"""Degenerate difficulty-band guards — the residual pre-101474c paths.

101474c floored the practice-expansion band after the authoring model pinned
32/55 fixture items to ``difficulty: 0.0``: at a pessimistic ability estimate
the success-band inversion collapses to ``[0.0, 0.0]`` — "author the easiest
item expressible" — whose outcome the model already predicts, so it yields no
information and can never correct the estimate that produced it. Two paths
kept the collapse: the diagnostic-probe plan (deliberately unfloored, because
a probe band must stay on the learner's boundary) and the tutor-promotion band
(a practice band that simply never received the floor). These tests pin the
invariant: no path hands the authoring model a zero-width band.
"""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.content.authoring.practice_generation import (
    ability_logit,
    _guard_degenerate_band,
    success_band_difficulty,
    build_diagnostic_practice_plan,
)
from learnloop.tutor.promotions import _recommended_difficulty_band
from learnloop.vault.loader import load_vault

from tests.helpers import ALGORITHM_VERSION, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"

# config defaults the production call sites pass
# (``learnloop.config.schema.PracticeGenerationConfig``).
PRACTICE_BAND = (0.70, 0.85)
PROBE_BAND = (0.45, 0.55)
FLOOR = 0.15
MIN_WIDTH = 0.10


# -- the guard itself -------------------------------------------------------------


def test_guard_widens_a_floor_collapsed_band_away_from_the_clamp():
    assert _guard_degenerate_band((0.0, 0.0), min_band_width=MIN_WIDTH) == (0.0, 0.10)


def test_guard_widens_a_ceiling_collapsed_band_downward():
    assert _guard_degenerate_band((1.0, 1.0), min_band_width=MIN_WIDTH) == (0.90, 1.0)


def test_guard_never_touches_a_band_with_width():
    assert _guard_degenerate_band((0.46, 0.54), min_band_width=MIN_WIDTH) == (0.46, 0.54)


def test_guard_is_inert_at_zero_min_width():
    assert _guard_degenerate_band((0.0, 0.0), min_band_width=0.0) == (0.0, 0.0)


# -- the probe band ---------------------------------------------------------------


def test_probe_band_collapses_unguarded_and_stays_boundary_centred_guarded():
    """The probe band keeps no floor — only the zero-width collapse is repaired.

    At a pessimistic ability the raw inversion clamps both edges to 0.0. The
    guard restores width upward from the clamp; it must NOT re-centre the band
    onto the practice floor, or the probe stops sitting on the learner's
    boundary and measures the wrong place.
    """

    pessimistic = ability_logit(0.02)
    raw = success_band_difficulty(
        pessimistic, PROBE_BAND, discrimination=1.0, difficulty_scale=2.5
    )
    assert raw == (0.0, 0.0)

    guarded = _guard_degenerate_band(raw, min_band_width=MIN_WIDTH)
    practice = success_band_difficulty(
        pessimistic,
        PRACTICE_BAND,
        discrimination=1.0,
        difficulty_scale=2.5,
        difficulty_floor=FLOOR,
        min_band_width=MIN_WIDTH,
    )
    assert guarded == (0.0, 0.10)
    # Boundary-centred: the probe band starts BELOW the practice floor and is
    # no wider than the floored practice band.
    assert guarded[0] < practice[0]
    assert (guarded[1] - guarded[0]) <= (practice[1] - practice[0])


def test_diagnostic_plan_band_is_never_degenerate(tmp_path):
    # End-to-end through build_diagnostic_practice_plan: a learner whose target
    # facet sits at recall_mean 0.02 used to receive a [0.0, 0.0] band.
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_intervention_need(
        {
            "id": "need_svd_recall",
            "attempt_id": "attempt_svd_recall_gap",
            "learning_object_id": LO_ID,
            "practice_item_id": "pi_svd_define_001",
            "desired_intent": "probe",
            "trigger_reason": "severe_error_event",
            "target_facets": ["recall"],
            "error_types": ["recall_failure"],
            "priority": 0.95,
            "status": "pending",
            "blocked_reason": "no_suitable_item",
            "candidate_requirements": {},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    with repository.connection() as connection:
        repository._upsert_facet_recall_state(
            connection,
            {
                "learning_object_id": LO_ID,
                "facet_id": "recall",
                "practice_item_id": None,
                "recall_alpha": 0.2,
                "recall_beta": 9.8,
                "recall_mean": 0.02,
                "recall_variance": 0.01,
                "independent_evidence_mass": 4.0,
                "raw_coverage_mass": 4.0,
                "last_attempt_at": NOW_ISO,
                "last_error_at": None,
                "consecutive_failures": 0,
                "algorithm_version": ALGORITHM_VERSION,
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
        )

    plan = build_diagnostic_practice_plan(vault, repository)
    (target,) = plan.targets
    low, high = target.recommended_difficulty_band
    assert (low, high) == (0.0, 0.10)
    assert high - low > 0.0


# -- the promotion band -----------------------------------------------------------


def test_promotion_band_is_floored_like_the_expansion_planner(tmp_path):
    # promotions._recommended_difficulty_band is a *practice* band ("reuses the
    # expansion planner math"), so it carries the same floor/min-width — at a
    # pessimistic mastery estimate it lands exactly on the floored band instead
    # of [0.0, 0.0].
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert _recommended_difficulty_band(vault, 0.02) == (0.15, 0.25)


def test_promotion_band_unchanged_at_ordinary_mastery(tmp_path):
    # The floor binds only when the raw inversion falls below it; a mid-band
    # learner's promotion band is untouched by the fix.
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    band = _recommended_difficulty_band(vault, 0.5)
    raw = success_band_difficulty(
        ability_logit(0.5), PRACTICE_BAND, discrimination=1.0, difficulty_scale=2.5
    )
    assert band == raw
