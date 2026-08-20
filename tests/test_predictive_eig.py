"""Predictive facet EIG: information-theoretic sanity properties and
logged-but-inert wiring into the follow-up selector."""

from __future__ import annotations

import pytest

from learnloop.diagnosis.predictive_eig import TargetItemModel, predictive_facet_eig
from learnloop.diagnosis.probes import facet_expected_information_gain

FACET = "f_spectral"
ERROR = "confuses_norms"

UNCERTAIN = {f"facet_solid:{FACET}": 0.5, f"facet_absent:{FACET}": 0.5}
RESOLVED = {f"facet_solid:{FACET}": 0.98, f"facet_absent:{FACET}": 0.02}
WITH_MISCONCEPTION = {
    f"facet_solid:{FACET}": 0.4,
    f"facet_absent:{FACET}": 0.3,
    f"misconception:{ERROR}": 0.3,
}


def _target(item_id="pi_target", support=(FACET,), fatal=()):
    return TargetItemModel(
        item_id=item_id,
        support=frozenset(support),
        fatal_error_ids=frozenset(fatal),
        item_a=1.0,
        item_b=0.0,
    )


def _eig(marginal, *, support=(FACET,), targets=None, fatal=(), candidate_item_id=None):
    return predictive_facet_eig(
        marginal,
        facet_id=FACET,
        candidate_support=set(support),
        candidate_fatal_error_ids=set(fatal),
        candidate_a=1.0,
        candidate_b=0.0,
        targets=targets if targets is not None else [_target()],
        candidate_item_id=candidate_item_id,
    )


def test_uncertain_facet_beats_resolved_facet():
    uncertain = _eig(UNCERTAIN)
    resolved = _eig(RESOLVED)
    assert uncertain.eig_nats > resolved.eig_nats
    assert uncertain.eig_nats > 0.0


def test_unsupported_facet_has_exactly_zero_eig():
    result = _eig(UNCERTAIN, support=("some_other_facet",))
    assert result.eig_nats == 0.0
    assert result.prior_predictive_entropy == result.expected_posterior_entropy


def test_empty_target_set_and_degenerate_prior_are_zero():
    assert _eig(UNCERTAIN, targets=[]).eig_nats == 0.0
    assert _eig({f"facet_solid:{FACET}": 1.0}).eig_nats == 0.0


def test_candidate_excluded_from_its_own_target_set():
    result = _eig(UNCERTAIN, targets=[_target(item_id="pi_self")], candidate_item_id="pi_self")
    assert result.target_item_ids == []
    assert result.eig_nats == 0.0


def test_never_negative_and_bounded_by_prior_entropy():
    result = _eig(WITH_MISCONCEPTION, fatal=(ERROR,))
    assert result.eig_nats >= 0.0
    assert result.eig_nats <= result.prior_predictive_entropy + 1e-9


def test_single_target_data_processing_bound():
    # I(Y_x; Y_t) <= I(Y_x; H): predicting one future answer can never gain
    # more than predicting the hypothesis itself.
    hypothesis_eig = facet_expected_information_gain(
        UNCERTAIN,
        facet_id=FACET,
        candidate_facet_support={FACET},
        fatal_error_ids=set(),
    )
    predictive = _eig(UNCERTAIN, targets=[_target()])
    assert predictive.eig_nats <= hypothesis_eig + 1e-9


def test_more_targets_accumulate():
    one = _eig(UNCERTAIN, targets=[_target("pi_t1")])
    two = _eig(UNCERTAIN, targets=[_target("pi_t1"), _target("pi_t2")])
    assert two.eig_nats > one.eig_nats


def test_deterministic():
    first = _eig(WITH_MISCONCEPTION, fatal=(ERROR,))
    second = _eig(WITH_MISCONCEPTION, fatal=(ERROR,))
    assert first == second


def test_followup_slate_logs_predictive_fields_and_ranking_unchanged_at_weight_zero(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import MasteryState, Repository
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.diagnosis.followups import evaluate_intervention_followup
    from learnloop.vault.loader import load_vault

    from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, add_followup_item, create_basic_vault

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    add_followup_item(vault_root, "pi_svd_define_003")
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    repository.upsert_mastery_state(
        MasteryState("lo_svd_definition", 2.0, 1.0, 3, NOW_ISO, ALGORITHM_VERSION, NOW_ISO)
    )
    result = complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=4, error_type="conceptual_slip"),
        clock=FrozenClock(NOW),
    )
    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=max(result.bayesian_surprise, 0.5),
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.8,
        available_minutes=30,
    )
    assert decision.triggered is True

    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    slate = features["context"]["candidate_slate"]
    assert slate, "slate must be logged"
    for row in slate:
        assert "total_predictive_eig" in row
        assert "predictive_eig_by_facet" in row
        assert row["predictive_eig_weight"] == 0.0
        # Weight 0 ⇒ rank_score must equal the pure hypothesis-EIG formula.
        expected = row["familiarity_discount"] * row["total_facet_eig"] + row["intent_bonus"]
        assert row["rank_score"] == pytest.approx(expected)
    assert features["item_demand_vector"]["total_predictive_eig"] is not None
