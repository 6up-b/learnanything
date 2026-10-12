"""Slice 1 M2 §7/§11: the split post-attempt pipeline with the async diagnoser."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.diagnosis.split import jobs as jobs_module
from learnloop.diagnosis.split.contract import RegistryMatch
from learnloop.diagnosis.split.jobs import (
    DONE,
    FAILED,
    NOT_NEEDED,
    PENDING,
    diagnosis_status,
)
from learnloop.ops.doctor import run_doctor
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, append_config, at, drain_jobs, split_vault, submit


def _causal_keys(event):
    plan = event.get("repair_plan") or {}
    return {key for key in ("candidate_causes", "operation", "postdictive_claims") if plan.get(key)}


@pytest.mark.durability
def test_blind_grade_carries_no_causal_fields_and_queues_a_diagnosis(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)

    assert client.calls == ["blind_grading"]
    assert all(client.isolated)
    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record is not None and record["record"]["grader_mode"] == "blind"
    events = repository.raw_error_events_for_attempt(result.attempt_id)
    assert events and not any(_causal_keys(event) for event in events)
    assert all(not event["misconception_statement"] for event in events)
    assert repository.raw_attempt_feedback_metadata(result.attempt_id)["repair_suggestions"] == []
    assert repository.causal_hypotheses_for_attempt(result.attempt_id) == []
    receipt = repository.diagnostic_augmentation_receipt_for_attempt(result.attempt_id)
    assert receipt["grader_mode"] == "blind" and receipt["c4_history_attempt_ids"] == []
    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING
    jobs = repository.post_attempt_jobs(attempt_id=result.attempt_id)
    assert [(job["kind"], job["state"]) for job in jobs] == [("diagnose", "queued")]


@pytest.mark.durability
def test_diagnosis_materializes_hypotheses_from_the_diagnosis(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)

    outcomes = drain_jobs(vault, repository, client)

    assert [(o.kind, o.state, o.status) for o in outcomes] == [("diagnose", "done", "completed")]
    assert client.calls == ["blind_grading", "diagnosis"]
    assert "misconception_match" not in client.calls
    status = diagnosis_status(repository, result.attempt_id)
    assert status["status"] == DONE
    diagnosis = repository.attempt_diagnosis(status["diagnosis_id"])
    hypotheses = repository.causal_hypotheses_for_attempt(result.attempt_id)
    statements = {row["statement"] for row in hypotheses}
    assert "The answer goes wrong because the learner misapplies the rule." in statements
    assert {row["generation_agent_run_id"] for row in hypotheses} == {diagnosis["agent_run_id"]}
    # The overlay: causal fields come from the diagnosis on read; the raw row is unchanged.
    overlaid = repository.error_events_for_attempt(result.attempt_id)
    assert all("candidate_causes" in _causal_keys(event) for event in overlaid)
    assert not any(_causal_keys(event) for event in repository.raw_error_events_for_attempt(result.attempt_id))
    repairs = repository.fetch_attempt_feedback_metadata(result.attempt_id)["repair_suggestions"]
    assert repairs and repairs[0]["operator"] == "elicit_rule"
    assert repairs[0]["id"] == f"diagnosis:{diagnosis['id']}:0"
    with repository.connection() as connection:
        receipts = connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'attempt_diagnosis' AND owner_id = ?",
            (result.attempt_id,),
        ).fetchone()[0]
        run = connection.execute("SELECT purpose, status FROM agent_runs WHERE id = ?", (diagnosis["agent_run_id"],)).fetchone()
    assert receipts >= 1
    assert tuple(run) == ("diagnosis", "completed")


def test_correct_answer_needs_no_diagnosis(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client, answer="A = U Sigma V^T")

    assert diagnosis_status(repository, result.attempt_id)["status"] == NOT_NEEDED
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id) == []


def test_correct_answers_are_sampled_in_shadow_only(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\ncorrect_answer_sample_rate = 1.0")
    client = ReviewFakeClient()
    result = submit(vault, repository, client, answer="A = U Sigma V^T")

    job = repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]
    assert job["payload"]["mode"] == "shadow"
    drain_jobs(vault, repository, client)
    shadow = repository.latest_attempt_diagnosis(result.attempt_id, mode="shadow")
    assert shadow is not None and shadow["causal_view"] is None
    assert diagnosis_status(repository, result.attempt_id)["status"] == NOT_NEEDED
    assert repository.causal_hypotheses_for_attempt(result.attempt_id) == []


def test_failed_diagnosis_backs_off_then_fails_and_leaves_the_grade(tmp_path):
    paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\nmax_attempts = 2")
    client = ReviewFakeClient(fail_purposes=("diagnosis",))
    when = at(20)
    result = submit(vault, repository, client, when=when)
    score = repository.fetch_practice_attempt(result.attempt_id)["rubric_score"]

    first = drain_jobs(vault, repository, client, clock=FrozenClock(when))
    assert [o.state for o in first] == ["released"]
    job = repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]
    assert job["state"] == "queued" and job["not_before"] is not None
    # Still backing off: nothing runs.
    assert drain_jobs(vault, repository, client, clock=FrozenClock(when + timedelta(seconds=5))) == []
    second = drain_jobs(vault, repository, client, clock=FrozenClock(when + timedelta(hours=1)))
    assert [(o.state, o.status) for o in second] == [("failed", "failed")]

    status = diagnosis_status(repository, result.attempt_id)
    assert status["status"] == FAILED
    assert repository.latest_attempt_diagnosis(result.attempt_id)["status"] == "failed"
    assert repository.causal_hypotheses_for_attempt(result.attempt_id) == []
    assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] == score
    codes = {issue.code for issue in run_doctor(paths.root).issues}
    assert "diagnosis:diagnose_job_failed" in codes


def test_budget_exhausted_skips_the_diagnosis_not_the_grade(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\nmax_calls_per_day = 0")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)

    outcomes = drain_jobs(vault, repository, client)

    assert [(o.state, o.error) for o in outcomes] == [("skipped", "budget")]
    assert client.calls == ["blind_grading"]
    row = repository.latest_attempt_diagnosis(result.attempt_id)
    assert row["status"] == "skipped" and row["error"] == "budget"
    assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] is not None


def test_diagnose_jobs_run_in_attempt_order(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    first = submit(vault, repository, client, when=at(20))
    second = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(21))

    # The head of the line blocks everything behind it.
    assert repository.lease_next_post_attempt_job(
        kind="diagnose", owner="t", lease_seconds=60, attempt_id=second.attempt_id
    ) is None
    outcomes = drain_jobs(vault, repository, client)
    assert [o.attempt_id for o in outcomes] == [first.attempt_id, second.attempt_id]


def test_resume_after_a_crash_between_diagnosis_and_settle_makes_no_second_call(tmp_path, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    when = at(20)
    result = submit(vault, repository, client, when=when)

    real_apply = jobs_module.apply_diagnosis

    def crash(*args, **kwargs):
        raise RuntimeError("process died after the diagnosis committed")

    monkeypatch.setattr(jobs_module, "apply_diagnosis", crash)
    with pytest.raises(RuntimeError):
        drain_jobs(vault, repository, client, clock=FrozenClock(when))
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]["state"] == "leased"
    monkeypatch.setattr(jobs_module, "apply_diagnosis", real_apply)
    # A live lease blocks a second worker; once it expires the job is reclaimed.
    assert drain_jobs(vault, repository, client, clock=FrozenClock(when + timedelta(seconds=10))) == []
    resumed = drain_jobs(vault, repository, client, clock=FrozenClock(when + timedelta(hours=2)))

    assert [o.state for o in resumed] == ["done"]
    assert client.calls.count("diagnosis") == 1
    assert len(repository.attempt_diagnoses_for_attempt(result.attempt_id)) == 1
    assert repository.causal_hypotheses_for_attempt(result.attempt_id)


def test_completion_resume_enqueues_the_diagnosis_once(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client, pipeline=False)
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id) == []

    run_post_attempt_pipeline(vault, repository, result=result)
    run_post_attempt_pipeline(vault, repository, result=result)

    assert len(repository.post_attempt_jobs(attempt_id=result.attempt_id)) == 1


def test_kill_switch_restores_joint_grading(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\nsplit_enabled = false")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)

    assert client.calls == ["grading"]
    assert repository.latest_blind_grade_record(result.attempt_id) is None
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id) == []
    receipt = repository.diagnostic_augmentation_receipt_for_attempt(result.attempt_id)
    assert receipt["grader_mode"] is None  # null reads as joint (§10)
    assert repository.causal_hypotheses_for_attempt(result.attempt_id)


def test_kill_switch_holds_queued_live_diagnoses(tmp_path):
    paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    append_config(paths.root, "[diagnosis]\nsplit_enabled = false")
    vault = load_vault(paths.root)

    outcomes = drain_jobs(vault, repository, client)

    assert [(o.state, o.error) for o in outcomes] == [("released", "split_disabled")]
    assert client.calls == ["blind_grading"]
    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING


class _RegistryFake(ReviewFakeClient):
    """Diagnoses every event as the first durable registry belief it is offered."""

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        durable = [row for row in context.get("registry_candidates") or [] if row.get("kind") == "durable"]
        events = []
        for event in result.event_diagnoses:
            update = {"misconception_statement": "Transposing changes nothing."}
            if durable:
                update["registry_match"] = RegistryMatch(kind="durable", id=durable[0]["id"])
            events.append(event.model_copy(update=update))
        return result.model_copy(update={"event_diagnoses": events})


def test_registry_match_links_a_durable_belief_without_misconception_match(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    # A durable belief sourced from an earlier failure (the as-of view only
    # offers registry rows whose source attempt precedes the diagnosed one).
    source_event = repository.raw_error_events_for_attempt("att_02_svd_fail")[0]["id"]
    misconception_id = repository.insert_misconception(
        learning_object_id="lo_svd_compute",
        statement="The learner treats V and V transpose as identical.",
        concept_id="singular_value_decomposition",
        severity=0.6,
        source_error_event_ids=[source_event],
        clock=FrozenClock(at(9)),
    )
    client = _RegistryFake()
    result = submit(vault, repository, client, when=at(20))
    drain_jobs(vault, repository, client)

    assert "misconception_match" not in client.calls
    linked = {event["misconception_id"] for event in repository.raw_error_events_for_attempt(result.attempt_id)}
    assert linked == {misconception_id}


def test_shadow_diagnosis_on_a_joint_vault_changes_nothing_live(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.9", config="[diagnosis]\nshadow = true")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    hypotheses_before = repository.causal_hypotheses_for_attempt(result.attempt_id)
    events_before = repository.error_events_for_attempt(result.attempt_id)

    drain_jobs(vault, repository, client)

    shadow = repository.latest_attempt_diagnosis(result.attempt_id, mode="shadow")
    assert shadow is not None and shadow["status"] == "completed" and shadow["causal_view"] is None
    assert repository.error_events_for_attempt(result.attempt_id) == events_before
    assert repository.causal_hypotheses_for_attempt(result.attempt_id) == hypotheses_before
    assert diagnosis_status(repository, result.attempt_id)["status"] == NOT_NEEDED


def test_blind_regrade_supersedes_the_record_and_rediagnoses(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    first_record = repository.latest_blind_grade_record(result.attempt_id)
    first = repository.latest_attempt_diagnosis(result.attempt_id)

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)

    second_record = repository.latest_blind_grade_record(result.attempt_id)
    assert second_record["supersedes_id"] == first_record["id"]
    assert client.calls.count("blind_grading") == 2 and "grading" not in client.calls
    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING
    # The old explanation no longer applies to the new grade.
    assert repository.live_causal_view(result.attempt_id) is None
    drain_jobs(vault, repository, client)
    second = repository.latest_attempt_diagnosis(result.attempt_id)
    assert second["id"] != first["id"] and second["supersedes_id"] == first["id"]


class _CorrectOnRegrade(ReviewFakeClient):
    """Wrong on the first blind grade, full marks when regraded."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        if self.calls.count("blind_grading") < 2:
            return result
        evidence = [
            row.model_copy(update={"points_awarded": next(c["points"] for c in context["rubric"]["criteria"] if c["id"] == row.criterion_id)})
            for row in result.criterion_evidence
        ]
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [],
            }
        )


def test_regrade_to_full_marks_retires_the_diagnosis(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = _CorrectOnRegrade()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)
    outcomes = drain_jobs(vault, repository, client)

    assert [(o.state, o.error) for o in outcomes] == [("skipped", "not_needed")]
    assert client.calls.count("diagnosis") == 1
    assert diagnosis_status(repository, result.attempt_id)["status"] == NOT_NEEDED
    assert repository.live_causal_view(result.attempt_id) is None
    assert repository.fetch_attempt_feedback_metadata(result.attempt_id)["repair_suggestions"] == []
