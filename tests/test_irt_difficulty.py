"""Behavioral tests for the difficulty-aware IRT mastery & probe update.

Covers the spec_irt_difficulty.md §9 test plan: mean monotonicity in difficulty,
boundary-peaked confidence, boundary-outcome registration, the kill switch,
robustness guards (step cap / mu clamp), difficulty sourcing precedence, and the
difficulty-aware probe conditionals / EIG ordering.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.config import MasteryConfig, MasteryIRTConfig, ProbeIRTConfig
from learnloop.db.repositories import MasteryState
from learnloop.services.mastery import (
    MasteryObservation,
    irt_observation,
    item_irt_params,
    sigmoid,
    update_mastery_traced,
)
from learnloop.services.probes import (
    Hypothesis,
    HypothesisSet,
    conditional_distribution,
    expected_information_gain,
)
from learnloop.vault.models import LearningObject, PracticeItem, Rubric, RubricFatalError

VERSION = "mvp-0.1"
NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)

TRIVIAL_B = -2.0
TARGET_B = 0.0
BRUTAL_B = 2.0


def _prior(mean: float = 0.0, variance: float = 1.0) -> MasteryState:
    # last_evidence_at = None -> days_since = 0 -> P_pred = prior variance.
    return MasteryState("lo", mean, variance, 0, None, VERSION, "2026-05-19T12:00:00Z")


def _obs(score: int) -> MasteryObservation:
    return MasteryObservation(
        rubric_score=score,
        max_points=4,
        evidence_coverage=1.0,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type="independent_attempt",
        observed_at=NOW,
    )


def _delta_mu(score: int, item_b: float, *, prior_mean: float = 0.0, variance: float = 1.0) -> float:
    state, trace = update_mastery_traced(
        _prior(prior_mean, variance), _obs(score), MasteryConfig(), VERSION, item_b=item_b
    )
    return trace.mu_step


# --- Headline: the mean move is monotone in difficulty (§4.2) ---------------


def test_correct_answer_mean_move_is_monotone_increasing_in_difficulty():
    trivial = _delta_mu(4, TRIVIAL_B)
    target = _delta_mu(4, TARGET_B)
    brutal = _delta_mu(4, BRUTAL_B)
    # Acing a harder item moves mu strictly more: "I aced the hard one, I'm good."
    assert trivial < target < brutal
    # Pinned to the exact logit-normal posterior within linearization tolerance (§4.2).
    assert trivial == pytest.approx(0.11, abs=0.02)
    assert target == pytest.approx(0.40, abs=0.02)
    assert brutal == pytest.approx(0.80, abs=0.02)


def test_wrong_answer_mean_move_is_monotone_inverted_in_difficulty():
    trivial = _delta_mu(0, TRIVIAL_B)
    target = _delta_mu(0, TARGET_B)
    brutal = _delta_mu(0, BRUTAL_B)
    # Failing a trivial item is the most damning; failing a brutal one barely counts.
    assert trivial < target < brutal < 0.0
    assert trivial == pytest.approx(-0.80, abs=0.02)
    assert target == pytest.approx(-0.40, abs=0.02)
    assert brutal == pytest.approx(-0.11, abs=0.02)


def test_failing_trivial_equals_acing_symmetric_brutal_in_magnitude():
    failing_trivial = _delta_mu(0, TRIVIAL_B)
    acing_brutal = _delta_mu(4, BRUTAL_B)
    assert failing_trivial == pytest.approx(-acing_brutal, abs=1e-9)


# --- Confidence gain (variance reduction) is boundary-peaked (§4.2) ----------


def _variance_reduction(item_b: float, score: int = 4, prior_mean: float = 0.0) -> float:
    _state, trace = update_mastery_traced(
        _prior(prior_mean), _obs(score), MasteryConfig(), VERSION, item_b=item_b
    )
    return trace.variance_reduction


def test_variance_reduction_peaks_on_target_and_is_symmetric():
    on_target = _variance_reduction(TARGET_B)
    trivial = _variance_reduction(TRIVIAL_B)
    brutal = _variance_reduction(BRUTAL_B)
    # An on-target item pins down ability most; equidistant items reduce it less.
    assert on_target > trivial
    assert on_target > brutal
    # Symmetric in |b - mu|.
    assert trivial == pytest.approx(brutal, abs=1e-9)


def test_variance_reduction_is_outcome_independent():
    # K*H depends only on the item geometry, not whether the answer was right.
    assert _variance_reduction(BRUTAL_B, score=4) == pytest.approx(
        _variance_reduction(BRUTAL_B, score=0), abs=1e-9
    )


def test_variance_reduction_tracks_boundary_distance_for_a_high_prior_learner():
    # For a learner at mu=2, the on-target item is now the b=+2 one.
    reductions = {b: _variance_reduction(b, prior_mean=2.0) for b in (-2.0, 0.0, 2.0, 4.0)}
    assert max(reductions, key=reductions.get) == 2.0


# --- Surprising boundary outcomes still register (§9) ------------------------


def test_surprising_outcome_on_near_certain_item_still_moves_mean():
    # b=+4: p ~ 0.018, acing it is extremely surprising; the gain must not vanish
    # (R_y ∝ p(1-p) cancels the p(1-p) in H, so K stays well-defined as p->0).
    brutal_correct = _delta_mu(4, 4.0)
    assert brutal_correct > 0.5
    # And an *expected* outcome on the same item barely moves mu.
    brutal_wrong = _delta_mu(0, 4.0)
    assert abs(brutal_wrong) < 0.05


def test_kalman_gain_well_defined_at_extreme_difficulty():
    obs = irt_observation(1.0, 6.0, _prior(), _obs(4), MasteryConfig())
    assert obs.p > 0.0  # clipped, never exactly 0
    assert obs.kalman_gain > 0.0
    assert obs.innovation_variance > 0.0


# --- Kill switch: legacy logit-space update, bit-for-bit (§6.2) --------------


def _legacy_config() -> MasteryConfig:
    return MasteryConfig(irt=MasteryIRTConfig(enabled=False))


def test_kill_switch_ignores_difficulty_entirely():
    cfg = _legacy_config()
    easy, _ = update_mastery_traced(_prior(), _obs(4), cfg, VERSION, item_b=-2.0)
    hard, _ = update_mastery_traced(_prior(), _obs(4), cfg, VERSION, item_b=+2.0)
    # Legacy update is in logit space and never reads b -> identical posteriors.
    assert easy.logit_mean == hard.logit_mean
    assert easy.logit_variance == hard.logit_variance


def test_kill_switch_reproduces_logit_kalman_math():
    from math import log

    cfg = _legacy_config()
    state, _ = update_mastery_traced(_prior(0.0, 1.0), _obs(4), cfg, VERSION, item_b=2.0)
    # z_obs = logit(0.98) (the 4/4 clamp), K = P/(P + base/weight) = 1/2.
    y = 0.98
    z_obs = log(y / (1 - y))
    expected_mean = 0.0 + 0.5 * (z_obs - 0.0)
    assert state.logit_mean == pytest.approx(expected_mean)
    assert state.logit_variance == pytest.approx(0.5)


def test_enabled_ekf_differs_from_legacy_on_target():
    ekf, _ = update_mastery_traced(_prior(), _obs(4), MasteryConfig(), VERSION, item_b=0.0)
    legacy, _ = update_mastery_traced(_prior(), _obs(4), _legacy_config(), VERSION, item_b=0.0)
    # Different observation spaces -> different numbers (the §9 re-pin).
    assert ekf.logit_mean != pytest.approx(legacy.logit_mean)


# --- Robustness guards: step cap + mu clamp (§4.4) ---------------------------


def test_step_cap_limits_overshoot_on_broad_prior():
    # Broad prior (P_pred = p_max) + aced hard item overshoots; the cap clamps it.
    capped_cfg = MasteryConfig(irt=MasteryIRTConfig(max_logit_step=2.0))
    _state, trace = update_mastery_traced(
        _prior(0.0, 4.0), _obs(4), capped_cfg, VERSION, item_b=4.0
    )
    assert trace.step_capped is True
    assert trace.mu_step == pytest.approx(2.0, abs=1e-9)


def test_default_step_cap_leaves_normal_attempts_untouched():
    _state, trace = update_mastery_traced(_prior(), _obs(4), MasteryConfig(), VERSION, item_b=0.0)
    assert trace.step_capped is False
    assert trace.mu_clamped is False


def test_mu_clamp_bounds_the_mean():
    clamp_cfg = MasteryConfig(irt=MasteryIRTConfig(mu_abs_max=0.25))
    state, trace = update_mastery_traced(_prior(), _obs(4), clamp_cfg, VERSION, item_b=0.0)
    assert trace.mu_clamped is True
    assert state.logit_mean == pytest.approx(0.25)


def test_sustained_brutal_corrects_do_not_drift_past_mu_abs_max():
    cfg = MasteryConfig()
    state = _prior()
    for _ in range(50):
        state, _trace = update_mastery_traced(state, _obs(4), cfg, VERSION, item_b=4.0)
    assert state.logit_mean <= cfg.irt.mu_abs_max + 1e-9


# --- Difficulty sourcing precedence (§4.3) -----------------------------------


def _lo(difficulty_prior=None) -> LearningObject:
    return LearningObject(
        id="lo",
        title="t",
        subjects=["s"],
        concept="c",
        knowledge_type="concept",
        summary="s",
        difficulty_prior=difficulty_prior,
        created_at="x",
        updated_at="x",
    )


def _pi(difficulty=None) -> PracticeItem:
    return PracticeItem(
        id="pi",
        learning_object_id="lo",
        practice_mode="short_answer",
        prompt="p",
        expected_answer="x",
        difficulty=difficulty,
        created_at="x",
        updated_at="x",
    )


def test_difficulty_resolves_practice_item_first():
    a, b = item_irt_params(_pi(difficulty=0.8), _lo(difficulty_prior=0.2), MasteryConfig())
    assert a == 1.0
    assert b == pytest.approx(2.5 * (0.8 - 0.5) * 2)  # 1.5, from the PI not the LO


def test_difficulty_falls_back_to_learning_object_prior():
    _a, b = item_irt_params(_pi(difficulty=None), _lo(difficulty_prior=0.2), MasteryConfig())
    assert b == pytest.approx(2.5 * (0.2 - 0.5) * 2)  # -1.5


def test_difficulty_defaults_to_zero_when_unset():
    _a, b = item_irt_params(_pi(difficulty=None), _lo(difficulty_prior=None), MasteryConfig())
    assert b == 0.0


def test_difficulty_is_clamped_to_b_abs_max():
    cfg = MasteryConfig(irt=MasteryIRTConfig(difficulty_prior_scale=10.0, b_abs_max=4.0))
    _a, b = item_irt_params(_pi(difficulty=1.0), _lo(), cfg)
    assert b == 4.0  # 10*(1-0.5)*2 = 10, clamped to 4


def test_difficulty_from_prior_toggle_pins_b_to_default():
    cfg = MasteryConfig(irt=MasteryIRTConfig(difficulty_from_prior=False, difficulty_default=0.0))
    _a, b = item_irt_params(_pi(difficulty=0.9), _lo(difficulty_prior=0.9), cfg)
    assert b == 0.0


# --- Difficulty-aware probe conditionals & EIG (§5) --------------------------


def test_conditional_masses_match_spec_table_at_b_zero():
    irt = ProbeIRTConfig()
    mastered = conditional_distribution(
        Hypothesis(label="mastered"), item_a=1.0, item_b=0.0, irt=irt,
        fatal_error_ids=set(), known_error_types=[],
    )
    unfamiliar = conditional_distribution(
        Hypothesis(label="unfamiliar"), item_a=1.0, item_b=0.0, irt=irt,
        fatal_error_ids=set(), known_error_types=[],
    )
    assert mastered[("low", None)] == pytest.approx(0.05, abs=0.01)
    assert mastered[("mid", None)] == pytest.approx(0.22, abs=0.01)
    assert mastered[("high", None)] == pytest.approx(0.73, abs=0.01)
    assert unfamiliar[("low", None)] == pytest.approx(0.73, abs=0.01)
    assert unfamiliar[("mid", None)] == pytest.approx(0.22, abs=0.01)
    assert unfamiliar[("high", None)] == pytest.approx(0.05, abs=0.01)


def test_every_conditional_is_normalized():
    irt = ProbeIRTConfig()
    for b in (-2.0, 0.0, 2.0):
        for hypothesis in (
            Hypothesis(label="mastered"),
            Hypothesis(label="unfamiliar"),
            Hypothesis(label="misconception:slip", error_type="slip"),
        ):
            dist = conditional_distribution(
                hypothesis, item_a=1.0, item_b=b, irt=irt,
                fatal_error_ids={"slip"}, known_error_types=["slip"],
            )
            assert sum(dist.values()) == pytest.approx(1.0)


def test_misconception_overlay_routes_error_fractions_exactly():
    irt = ProbeIRTConfig()
    dist = conditional_distribution(
        Hypothesis(label="misconception:slip", error_type="slip"),
        item_a=1.0, item_b=0.0, irt=irt,
        fatal_error_ids={"slip"}, known_error_types=["slip"],
    )
    # The low/mid buckets split between the E channel and null per err_*_frac.
    low_total = dist[("low", "slip")] + dist[("low", None)]
    mid_total = dist[("mid", "slip")] + dist[("mid", None)]
    assert dist[("low", "slip")] == pytest.approx(low_total * irt.err_low_frac)
    assert dist[("mid", "slip")] == pytest.approx(mid_total * irt.err_mid_frac)
    assert dist[("high", None)] > 0.0  # high stays on null


def _eig_item() -> PracticeItem:
    return PracticeItem(
        id="pi_probe",
        learning_object_id="lo",
        practice_mode="short_answer",
        prompt="p",
        expected_answer="x",
        grading_rubric=Rubric(max_points=4, criteria=[], fatal_errors=[]),
        created_at="x",
        updated_at="x",
    )


# --- difficulty_source: round-trips but is excluded from the content hash (§6.1) ---


def test_difficulty_source_is_excluded_from_content_hash():
    from learnloop.vault.hashes import learning_object_hash, practice_item_hash

    pi = _pi(difficulty=0.6).model_copy(update={"difficulty_source": "llm_estimate"})
    pi_other_source = pi.model_copy(update={"difficulty_source": "author"})
    pi_other_difficulty = pi.model_copy(update={"difficulty": 0.7})
    assert practice_item_hash(pi) == practice_item_hash(pi_other_source)
    assert practice_item_hash(pi) != practice_item_hash(pi_other_difficulty)

    lo = _lo(difficulty_prior=0.6).model_copy(update={"difficulty_source": "llm_estimate"})
    lo_other_source = lo.model_copy(update={"difficulty_source": "author"})
    assert learning_object_hash(lo) == learning_object_hash(lo_other_source)


def test_difficulty_source_round_trips_through_the_writer(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_practice_item

    from tests.helpers import NOW as VAULT_NOW, create_basic_vault

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    upsert_practice_item(
        vault_root,
        {
            "id": "pi_sourced",
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "p",
            "expected_answer": "x",
            "difficulty": 0.8,
            "difficulty_source": "llm_estimate",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "c"}],
                "fatal_errors": [],
            },
        },
        clock=FrozenClock(VAULT_NOW),
    )
    reloaded = load_vault(vault_root)
    item = reloaded.practice_items["pi_sourced"]
    assert item.difficulty == 0.8
    assert item.difficulty_source == "llm_estimate"


def test_eig_prefers_boundary_items_over_trivial_and_impossible():
    # Anchors mastered=+2, unfamiliar=-2; the boundary between them is b=0.
    hset = HypothesisSet(
        learning_object_id="lo",
        hypotheses=[Hypothesis(label="mastered"), Hypothesis(label="unfamiliar")],
        prior={"mastered": 0.5, "unfamiliar": 0.5},
    )
    item = _eig_item()
    irt = ProbeIRTConfig()
    boundary = expected_information_gain(hset, item, item_a=1.0, item_b=0.0, irt=irt)
    trivial = expected_information_gain(hset, item, item_a=1.0, item_b=-2.0, irt=irt)
    impossible = expected_information_gain(hset, item, item_a=1.0, item_b=2.0, irt=irt)
    assert boundary > trivial
    assert boundary > impossible
    assert trivial > 0.0
    assert impossible > 0.0
