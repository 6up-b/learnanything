"""§4 misconception discrimination routing (spec_misconception_diagnostics.md)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import ItemMisconceptionDiscrimination, Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.diagnosis.followups import evaluate_intervention_followup
from learnloop.vault.loader import load_vault

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, add_followup_item, create_basic_vault
from learnloop.db.repositories import MasteryState


def _surprising_attempt(vault_root, repository):
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
    return loaded, result


def _seed_active_misconception(repository, result, *, facet_ids=("recall",)):
    mc_id = repository.insert_misconception(
        learning_object_id="lo_svd_definition",
        statement="believes Q maps standard vectors to eigenbasis coefficients (reverses Q / Q^T)",
        signature="Q^T x is the coordinate vector",
        facet_ids=list(facet_ids),
        severity=0.9,
        status="active",
        clock=FrozenClock(NOW),
    )
    events = repository.error_events_for_attempt(result.attempt_id)
    assert events, "surprising attempt should have written an error event"
    repository.set_error_event_misconception(events[0]["id"], mc_id, clock=FrozenClock(NOW))
    return mc_id


def _evaluate(loaded, repository, result):
    return evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
        max_error_severity=0.9,
        available_minutes=30,
    )


def test_active_mc_without_discriminator_routes_to_need(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)  # facet-eligible paraphrase, no discrimination
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)
    mc_id = _seed_active_misconception(repository, result)

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is False
    assert decision.need_id is not None
    # The facet-eligible paraphrase is NOT queued as a consolation.
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert not any("queued" in action for action in surprise["triggered_actions"])
    # Need carries the belief ids/statements in diagnostic_focus.
    need = repository.intervention_need(decision.need_id)
    focus = need["diagnostic_focus"]
    assert focus["misconception_ids"] == [mc_id]
    assert mc_id in focus["misconception_statements"]
    assert "demonstrated_facets" in focus
    assert focus["source_practice_item_id"] == "pi_svd_define_001"
    # Decision-features outcome is the discriminator-specific one.
    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    assert features["context"]["decision_outcome"] == "created_need_no_discriminator"
    # The demoted paraphrase carries the discrimination filter reason.
    slate = features["context"]["candidate_slate"]
    paraphrase = next(row for row in slate if row["practice_item_id"] == "pi_svd_define_002")
    assert paraphrase["filtered_reason"] == "no_misconception_discrimination"
    assert paraphrase["discriminates_target_misconception"] is False


def test_active_mc_with_discriminator_queues_it(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)
    mc_id = _seed_active_misconception(repository, result)
    # Seed a strong discrimination row for the paraphrase item vs the belief.
    repository.upsert_item_misconception_discrimination(
        ItemMisconceptionDiscrimination(
            practice_item_id="pi_svd_define_002",
            misconception_id=mc_id,
            sensitivity_alpha=20.0,
            sensitivity_beta=1.0,
            specificity_alpha=20.0,
            specificity_beta=1.0,
            n_planted_trials=20,
            n_clean_trials=20,
            source="sim",
            updated_at=NOW_ISO,
        )
    )

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_svd_define_002"
    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    slate = features["context"]["candidate_slate"]
    row = next(r for r in slate if r["practice_item_id"] == "pi_svd_define_002")
    assert row["discriminates_target_misconception"] is True
    assert row["gate_passed"] is True


def test_no_active_misconception_is_unchanged(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)
    # No registry misconception seeded.

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_svd_define_002"


def test_config_flag_off_keeps_paraphrase(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)
    _seed_active_misconception(repository, result)
    loaded.config.scheduler.followup.require_misconception_discrimination = False

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_svd_define_002"
