"""Failed grade hooks and the stopping rules that a completion passed."""

import json

import pytest

from learnloop import provenance
from tests.why_cases_helpers import of_kind, why


@pytest.mark.parametrize(("module", "function", "step"), [
    ("machine_checks", "sweep_machine_checks", "machine_check_sweep"),
    ("causal_cold_verification", "record_cold_verification_from_task", "cold_verification_wiring"),
    ("causal_discrimination", "auto_classify_pinned_probe", "probe_classification_hook"),
    ("followups", "_consult_common_repair", "common_repair_consultation"),
])
def test_grade_hook_failure_completes_the_attempt(tmp_path, monkeypatch, module, function, step):
    import importlib

    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.attempts.post_attempt import run_post_attempt_pipeline
    from tests.causal_p2_acceptance_helpers import CLOCK, SOURCE_ITEM, _acceptance_vault

    vault, repository, paths = _acceptance_vault(tmp_path)

    def fail(*args, **kwargs):
        raise RuntimeError("private failure message")

    monkeypatch.setattr(importlib.import_module(f"learnloop.diagnosis.{module}"), function, fail)
    if module == "causal_cold_verification":
        monkeypatch.setattr(repository, "consumed_followup_task_for_attempt", lambda *a, **k: {"id": "task_cold"})
    with provenance.trace_scope("TRACE_HOOK"):
        result = complete_self_graded_attempt(vault, repository,
            AttemptDraft(practice_item_id=SOURCE_ITEM, learner_answer_md="answer"),
            SelfGradeInput(criterion_points={criterion.id: criterion.points for criterion in
                vault.rubric_for_item(vault.practice_items[SOURCE_ITEM]).criteria}, confidence=3), clock=CLOCK)
        run_post_attempt_pipeline(vault, repository, result=result, clock=CLOCK)
    assert repository.attempt_completion(result.attempt_id)["status"] == "completed"
    payload = why(paths.root, f"attempt:{result.attempt_id}")
    [record] = [entry for entry in of_kind(payload, "diagnosis_step") if entry["rule"] == step]
    assert record["trace_id"] == "TRACE_HOOK" and record["status"] == "failed"
    assert record["inputs"]["phase"] == "grade_keyed"
    assert record["inputs"]["learning_object_id"] == result.learning_object_id


def test_a_late_completion_lists_only_evaluated_rules_in_order(tmp_path):
    from learnloop.diagnosis.probe_episodes import enter_episode
    from tests.probe_episodes_helpers import CLOCK, LO_ID, _commit, _setup

    _, vault, repository = _setup(tmp_path, extra_item=True, switched_off="[voi_stopping]\nenabled = false")
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    # Apply AI grades so the episode counts the two independent surfaces.
    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt

    for index, item in enumerate(("pi_svd_define_001", "pi_svd_define_002")):
        presentation = _commit(vault, repository, repository.probe_episode(episode.id), item_id=item)
        apply_attempt(vault, repository, ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item, learner_answer_md="answer", attempt_type="diagnostic_probe",
                               probe_presentation_id=presentation.id),
            attempt_id=f"att_stable_{index}", grading_source="ai",
            grade=ResolvedGrade(rubric_score=4, criterion_points={"correctness": 4}, evidence_rows=[],
                                error_attributions=[], grader_confidence=1, confidence=4,
                                manual_review_reason=None)), clock=CLOCK)
    assert repository.probe_episode(episode.id).completion_reason == "decision_stable"
    with repository.connection() as connection:
        detail = json.loads(connection.execute(
            "SELECT completion_detail_json FROM probe_episodes WHERE id = ?", (episode.id,)).fetchone()[0] or "{}")
    assert detail["rules_passed"] == ["observation_budget_exhausted"]


def test_a_value_stop_omits_the_robust_rule_when_its_gate_is_off(tmp_path, monkeypatch):
    from tests.voi_stopping_helpers import _answer_probe, _minutes, _probe_vault

    _, vault, repository = _probe_vault(tmp_path, "mvp-0.21", toml=(
        "[probe.episode]\naction_equivalence_enabled = false\nposterior_stop_threshold = 0.9999\n"
        "minimum_independent_observations = 10\n[probe.block]\ndefault_block_observations = 1\n"))
    _minutes(monkeypatch, 10_000)
    episode = _answer_probe(vault, repository)
    assert episode.completion_reason == "value_of_information_stop"
    with repository.connection() as connection:
        detail = json.loads(connection.execute(
            "SELECT completion_detail_json FROM probe_episodes WHERE id = ?", (episode.id,)).fetchone()[0])
    assert detail["rules_passed"] == ["observation_budget_exhausted"]
    assert "couldnt_reliably_distinguish" not in detail["rules_passed"]
    assert "action_equivalent" not in detail["rules_passed"]


@pytest.mark.parametrize("case", ["unpinned", "own_observation"])
def test_noncausal_or_already_read_answer_is_silent(tmp_path, monkeypatch, case):
    from learnloop.diagnosis.causal_discrimination import auto_classify_pinned_probe
    from tests.probe_records_helpers import declined_answer

    root, vault, repository, result = declined_answer(tmp_path, case, monkeypatch)
    assert auto_classify_pinned_probe(vault, repository, attempt_id=result.attempt_id) is None
    assert not of_kind(why(root, f"attempt:{result.attempt_id}"), "probe_classification")


def test_block_settlement_decline_precedes_grade_and_is_reachable(tmp_path, monkeypatch):
    from learnloop.diagnosis import chain_records
    from tests.causal_p2_acceptance_helpers import CLOCK, PROBE_ITEM, _acceptance_vault, _offered_probe
    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt

    vault, repository, paths = _acceptance_vault(tmp_path, toml=(
        "[probe.block]\ndefault_block_observations = 1\n"))
    _, _, _, _, offer = _offered_probe(vault, repository)
    original = chain_records.record_probe_classification_declined
    seen = []

    def record_before_grade(repository, **values):
        with repository.connection() as connection:
            assert not provenance.read(connection, f"attempt:{values['attempt_id']}", kind="grade")
        seen.append(values["attempt_id"])
        return original(repository, **values)

    monkeypatch.setattr(chain_records, "record_probe_classification_declined", record_before_grade)
    with provenance.trace_scope("TRACE_SETTLEMENT"):
        result = apply_attempt(vault, repository, ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=PROBE_ITEM, learner_answer_md="answer",
                attempt_type="diagnostic_probe", probe_presentation_id=offer.presentation_id),
            attempt_id="att_settlement", grading_source="ai",
            grade=ResolvedGrade(rubric_score=0, criterion_points={"correctness": 0}, evidence_rows=[],
                error_attributions=[], grader_confidence=1, confidence=3, manual_review_reason=None)), clock=CLOCK)
    assert seen == [result.attempt_id]
    payload = why(paths.root, f"attempt:{result.attempt_id}")
    [record] = of_kind(payload, "probe_classification")
    [grade] = of_kind(payload, "grade")
    assert record["rule"] == "declared_features_not_covered"
    assert record["trace_id"] == grade["trace_id"] == "TRACE_SETTLEMENT"
