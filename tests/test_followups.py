from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.diagnosis.followups import (
    evaluate_intervention_followup,
    evaluate_negative_surprise_followup,
)
from learnloop.scheduling.scheduler import read_due_queue

from tests.helpers import NOW, add_followup_item, create_basic_vault
from tests.followups_helpers import _surprising_attempt
from tests.voi_stopping_helpers import _minutes


def _evaluate(loaded, repository, result, *, available_minutes=30):
    return evaluate_negative_surprise_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
        available_minutes=available_minutes,
    )


def test_negative_surprise_inserts_followup_when_item_exists(tmp_path, monkeypatch):
    # D2a: from mvp-0.21 (voi_stopping) a follow-up is queued only while its value pays for its
    # minutes; pin the candidates' minutes low (as test_voi_stopping does) so it pays here.
    _minutes(monkeypatch, 0.01)
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    assert result.surprise_direction == "negative"

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is True
    assert decision.practice_item_id == "pi_svd_define_002"
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["triggered_actions"] == [
        "intervention_followup:negative_surprise:pi_svd_define_001",
        "intervention_followup:queued:pi_svd_define_002",
    ]
    assert surprise["suppressed_actions"] == []
    queue = read_due_queue(loaded, repository, clock=FrozenClock(NOW))
    assert queue[0].practice_item_id == "pi_svd_define_002"
    assert queue[0].components["intervention_followup"] == 1.0
    assert queue[0].plain_english[0] == "intervention follow-up"


def test_negative_surprise_followup_stops_forcing_after_followup_attempt(tmp_path, monkeypatch):
    # D2a: from mvp-0.21 (voi_stopping) a follow-up is queued only while its value pays for its
    # minutes; pin the candidates' minutes low (as test_voi_stopping does) so it pays here.
    _minutes(monkeypatch, 0.01)
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = _evaluate(loaded, repository, result)
    assert decision.triggered is True

    later = FrozenClock(NOW + timedelta(days=1))
    complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_002", learner_answer_md="follow-up answer"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=later,
    )

    assert repository.pending_followup_practice_item_ids() == []
    queue = read_due_queue(loaded, repository, clock=later)
    assert not queue or queue[0].components.get("intervention_followup") is None


def test_manual_override_forces_followup_when_gate_silent(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    # Inputs that the automatic gate would ignore: positive direction, no
    # surprise, confident grade, and no error event.
    gate_inputs = dict(
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="positive",
        bayesian_surprise=0.0,
        grader_confidence=0.95,
        error_event_written=False,
        available_minutes=30,
    )

    silent = evaluate_intervention_followup(loaded, repository, **gate_inputs)
    assert silent.triggered is False
    # Score mode (default): a silent gate reports the counterfactual margin;
    # cascade mode reports "no_trigger".
    assert silent.reason in ("no_trigger", "gate_score_below_threshold")

    forced = evaluate_intervention_followup(loaded, repository, manual_override=True, **gate_inputs)
    assert forced.triggered is True
    assert forced.practice_item_id == "pi_svd_define_002"
    # The decision reports what the automatic policy would have done, for tuning.
    assert forced.gate_diagnostics is not None
    assert forced.gate_diagnostics["would_auto_fire"] is False
    assert forced.gate_diagnostics["natural_trigger_reasons"] == []
    assert {"no_trigger", "gate_score_below_threshold"} & set(forced.gate_diagnostics["would_suppress"])

    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert "intervention_followup:manual_trigger:pi_svd_define_001" in surprise["triggered_actions"]
    assert "intervention_followup:queued:pi_svd_define_002" in surprise["triggered_actions"]

    queue = read_due_queue(loaded, repository, clock=FrozenClock(NOW))
    assert queue[0].practice_item_id == "pi_svd_define_002"


def test_manual_override_records_need_when_no_suitable_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    forced = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="positive",
        bayesian_surprise=0.0,
        grader_confidence=0.95,
        error_event_written=False,
        available_minutes=30,
        manual_override=True,
    )

    assert forced.triggered is False
    assert forced.need_id is not None
    assert forced.gate_diagnostics is not None
    need = repository.intervention_need_for_attempt(result.attempt_id)
    assert need is not None
    assert need["status"] == "pending"


def test_negative_surprise_suppressed_when_no_suitable_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = _evaluate(loaded, repository, result)

    assert decision.triggered is False
    assert decision.reason.startswith("intervention_followup:no_suitable_item:")
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert len(surprise["suppressed_actions"]) == 1
    assert surprise["suppressed_actions"][0].startswith("intervention_followup:no_suitable_item:")


def test_negative_surprise_suppressed_when_out_of_time(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = _evaluate(loaded, repository, result, available_minutes=0)

    assert decision.triggered is False
    assert decision.reason == "intervention_followup:no_time"
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["suppressed_actions"] == ["intervention_followup:no_time"]


def test_followup_gate_skips_non_negative_surprise(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)

    decision = evaluate_negative_surprise_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="none",
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        available_minutes=30,
    )

    assert decision.triggered is False
    assert decision.reason in ("no_trigger", "gate_score_below_threshold")
    surprise = repository.latest_attempt_surprise(result.attempt_id)
    assert surprise["triggered_actions"] == []
    assert surprise["suppressed_actions"] == []
