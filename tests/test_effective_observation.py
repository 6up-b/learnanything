"""P0.3 (spec §4.3, §9.2): reliability-aware EffectiveObservation. Lower calibrated
certainty -> less certification mass; uniform -> zero mass; deterministic/adjudicated
-> certainty 1; quarantined -> zero."""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.effective_observation import (
    build_effective_observation,
    effective_observation_from_posterior,
)
from learnloop.services.grade_resolution import append_adjudication, resolve_grade
from learnloop.services.outcome_schemas import COARSE_RESPONSE_SLUG, ensure_builtin_schemas
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"
_SCORE_FRACTION = {"success": 1.0, "partial_success": 0.5, "other": 0.0}


def _env(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    ensure_builtin_schemas(repo, clock=CLOCK)
    return vault, repo


# --- pure core (§9.2 bullets 1-2) ------------------------------------------


def test_uniform_posterior_yields_zero_certification_mass():
    """M2 (§4.3, §9.2): a symmetric uniform joint_alpha, fed through the REAL
    robust ``certainty_lcb`` (not a hardcoded 0.0), yields a certainty LCB of ~0 and
    thus zero effective/positive/negative certification mass end-to-end.

    Before the fix ``certainty_lcb`` only averaged Dirichlet DRAWS, which always
    break the uniform symmetry and report spurious positive certainty, so a uniform
    interpretation leaked positive certification mass."""

    from learnloop.services import robust_composition as rc

    uniform_alpha = {
        z: {f"{g}|high": 1.0 for g in ("success", "partial_success", "other")}
        for z in ("success", "partial_success", "other")
    }
    ctx = rc.decision_context_hash(
        episode_id=None, candidate_card_version=None, resolved_slot_map=None,
        posterior_at_selection={"success": 1 / 3, "partial_success": 1 / 3, "other": 1 / 3},
        projection_algorithm_version="grade_interpretation_v1",
    )
    lcb = rc.certainty_lcb(
        joint_alpha=uniform_alpha, observed_emission="success|high",
        calibration_model_hash="uh", decision_context_hash=ctx,
    )
    assert lcb < 1e-9

    obs = effective_observation_from_posterior(
        observation_id="o",
        posterior={"success": 1 / 3, "partial_success": 1 / 3, "other": 1 / 3},
        score_fraction=_SCORE_FRACTION,
        certainty_lcb=lcb,
        attempt_type_mass=1.0,
    )
    assert obs.certainty == pytest.approx(0.0)
    assert obs.effective_mass == pytest.approx(0.0)
    assert obs.positive_mass == pytest.approx(0.0)
    assert obs.negative_mass == pytest.approx(0.0)


def test_point_posterior_has_certainty_one_and_full_split():
    obs = effective_observation_from_posterior(
        observation_id="o",
        posterior={"success": 1.0, "partial_success": 0.0, "other": 0.0},
        score_fraction=_SCORE_FRACTION,
        certainty_lcb=1.0,
        attempt_type_mass=1.0,
    )
    assert obs.certainty == pytest.approx(1.0)
    assert obs.positive_mass == pytest.approx(1.0)
    assert obs.negative_mass == pytest.approx(0.0)


def test_reliability_never_creates_mass_and_discounts_multiply():
    """P4.2: the mass discount is the epistemic factor ``lcb / certainty`` — the
    aleatoric spread is priced once, through the positive/negative split, not a
    second time through the raw LCB multiplier."""

    posterior = {"success": 0.8, "partial_success": 0.15, "other": 0.05}
    obs = effective_observation_from_posterior(
        observation_id="o",
        posterior=posterior,
        score_fraction=_SCORE_FRACTION,
        certainty_lcb=0.3,
        attempt_type_mass=1.0,
        assistance_discount=0.5,
        familiarity_discount=0.5,
    )
    assert obs.epistemic_factor == pytest.approx(0.3 / obs.certainty)
    assert obs.epistemic_factor < 1.0
    # 1.0 * 0.5 * 0.5 * (0.3 / certainty) -- strictly below attempt_type_mass.
    assert obs.effective_mass == pytest.approx(0.25 * obs.epistemic_factor)
    assert obs.effective_mass < obs.attempt_type_mass


def test_epistemic_factor_strips_aleatoric_double_count():
    """A cold-but-consistent channel (heuristic prior, high-confidence success)
    keeps ~all its mass: the posterior split already hedges 0.85/0.15, so the
    mass-side factor reflects only ensemble (model) doubt — not the posterior
    entropy again. A perfect AI-graded attempt banks ~0.9 of a unit, not ~0.33."""

    posterior = {"success": 0.8, "partial_success": 0.1, "other": 0.1}
    obs = effective_observation_from_posterior(
        observation_id="o",
        posterior=posterior,
        score_fraction=_SCORE_FRACTION,
        certainty_lcb=0.385,  # the observed cold-channel robust bound
        attempt_type_mass=1.0,
    )
    assert 0.85 < obs.epistemic_factor <= 1.0
    assert obs.positive_mass == pytest.approx(obs.effective_mass * 0.85)
    assert obs.positive_mass > 0.7


def test_quarantined_and_unassessable_contribute_zero():
    q = effective_observation_from_posterior(
        observation_id="o", posterior={"success": 1.0}, score_fraction=_SCORE_FRACTION,
        certainty_lcb=1.0, attempt_type_mass=1.0, quarantined=True,
    )
    assert q.effective_mass == 0.0
    u = effective_observation_from_posterior(
        observation_id="o", posterior={"success": 1.0}, score_fraction=_SCORE_FRACTION,
        certainty_lcb=1.0, attempt_type_mass=1.0, unassessable=True,
    )
    assert u.effective_mass == 0.0


# --- from a real P0.2 interpretation (§9.2 bullet 1) -----------------------


def _interp(repo, vault, *, attempt_id, confidence):
    res = resolve_grade(
        vault, repo, item=vault.practice_items[ITEM], purpose="practice",
        grading_source="codex", attempt_id=attempt_id, response_text="an answer",
        rubric_score=4, max_points=4, grader_confidence=confidence, clock=CLOCK,
    )
    return repo.grade_interpretation(res.interpretation_id), res


def test_adjudicated_grade_has_higher_certainty_than_heuristic(tmp_path):
    """A deterministic-key adjudication (point class) yields certainty 1 and thus
    at least as much mass as the wide heuristic interpretation of the same grade
    (§9.2 bullet 1: deterministic/adjudicated >= heuristic)."""

    vault, repo = _env(tmp_path)
    heuristic_interp, res = _interp(repo, vault, attempt_id="att_h", confidence=0.7)
    heuristic_obs = build_effective_observation(
        repo, interpretation=heuristic_interp, score_fraction=_SCORE_FRACTION,
        attempt_type_mass=1.0,
    )

    adj = append_adjudication(
        repo, observation_id=res.observation_id, administration_id=res.administration_id,
        reviewed_raw_event_ids=[res.raw_grade_event_id], adjudicator_source="deterministic_key",
        resolved_class="success", clock=CLOCK,
    )
    adjudicated_interp = repo.grade_interpretation(adj["interpretation_id"])
    adjudicated_obs = build_effective_observation(
        repo, interpretation=adjudicated_interp, score_fraction=_SCORE_FRACTION,
        attempt_type_mass=1.0,
    )

    assert adjudicated_obs.certainty_lcb == pytest.approx(1.0)
    assert adjudicated_obs.certainty_lcb >= heuristic_obs.certainty_lcb
    assert adjudicated_obs.effective_mass >= heuristic_obs.effective_mass
    # The heuristic channel is wide -> its certainty LCB is strictly below 1.
    assert heuristic_obs.certainty_lcb < 1.0


def test_shared_certainty_lcb_agrees_across_mastery_and_certification(tmp_path):
    """H1 (§4.3 final ¶): with a scoped child model present (pooled != leaf), the
    certainty the certification path consumes (EffectiveObservation) must equal the
    certainty the mastery path consumes (response_certainty_lcb) EXACTLY.

    Before the fix the certification path drew the LEAF model's alphas seeded on
    (observation_id, interpretation_id) while mastery drew the POOLED joint alpha
    seeded on (None, item.id): different alphas AND different seed, so the two
    values diverged whenever any descendant model existed. Now both route through
    the one persisted shared_certainty_lcb / shared helper."""

    from learnloop.services.grade_resolution import (
        PROJECTION_ALGORITHM_VERSION,
        response_certainty_lcb,
    )
    from learnloop.services.effective_observation import (
        SHARED_CERTAINTY_PROJECTION_VERSION,
    )

    assert PROJECTION_ALGORITHM_VERSION == SHARED_CERTAINTY_PROJECTION_VERSION

    vault, repo = _env(tmp_path)
    # provider/revision matching a seeded grader_identity model -> the resolved
    # model POOLS global + identity, so leaf alphas != pooled alphas.
    res = resolve_grade(
        vault, repo, item=vault.practice_items[ITEM], purpose="practice",
        grading_source="ai", grader_model_revision="diagnostic_longform_v1",
        attempt_id="att_shared", response_text="an answer",
        rubric_score=3, max_points=4, grader_confidence=0.7, clock=CLOCK,
    )
    interp = repo.grade_interpretation(res.interpretation_id)
    # The row carries more than one contributing model (pooled), proving the
    # leaf-vs-pooled divergence condition is actually exercised.
    assert len(json.loads(interp["reference_prior_ids_json"])) >= 2
    assert interp["shared_certainty_lcb"] is not None

    cert_obs = build_effective_observation(
        repo, interpretation=interp, score_fraction=_SCORE_FRACTION,
        attempt_type_mass=1.0,
    )
    mastery_lcb = response_certainty_lcb(
        vault, repo, item=vault.practice_items[ITEM], grading_source="ai",
        grader_model_revision="diagnostic_longform_v1", rubric_score=3,
        max_points=4, grader_confidence=0.7, response_text="an answer", clock=CLOCK,
    )
    assert cert_obs.certainty_lcb == pytest.approx(mastery_lcb, abs=0.0)
    # And it equals the value persisted at interpretation time (not a re-draw).
    assert cert_obs.certainty_lcb == pytest.approx(interp["shared_certainty_lcb"], abs=0.0)


def test_missing_interpretation_is_zero_mass_never_full_credit(tmp_path):
    vault, repo = _env(tmp_path)
    obs = build_effective_observation(
        repo, interpretation=None, score_fraction=_SCORE_FRACTION, attempt_type_mass=1.0,
    )
    assert obs.effective_mass == 0.0
    assert obs.calibration_status == "missing_interpretation"


def test_quarantined_interpretation_contributes_zero(tmp_path):
    from learnloop.services.grade_resolution import quarantine_observation

    vault, repo = _env(tmp_path)
    _, res = _interp(repo, vault, attempt_id="att_q", confidence=0.7)
    quarantine_observation(
        repo, observation_id=res.observation_id, surface_id=None,
        reason="learner_contest", clock=CLOCK,
    )
    head = repo.active_interpretation_for_observation(res.observation_id)
    obs = build_effective_observation(
        repo, interpretation=head, score_fraction=_SCORE_FRACTION, attempt_type_mass=1.0,
    )
    assert obs.quarantined is True
    assert obs.effective_mass == 0.0
