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


def test_the_accessor_and_the_overlays_agree_on_the_diagnosis_in_force(tmp_path):
    """Review F9: a newer blind grade, or a failed successor, retires the
    older explanation for ``diagnosis_for_attempt`` exactly as for the overlays."""

    from learnloop.diagnosis.split.jobs import enqueue_diagnosis
    from learnloop.diagnosis.split.live import diagnosis_for_attempt

    _paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\nmax_attempts = 1")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    first = repository.latest_attempt_diagnosis(result.attempt_id)
    assert diagnosis_for_attempt(repository, result.attempt_id)["diagnosis_id"] == first["id"]

    # Stale grade: a regrade appends a newer blind record.
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)
    assert repository.live_causal_view(result.attempt_id) is None
    assert diagnosis_for_attempt(repository, result.attempt_id) is None
    drain_jobs(vault, repository, client)
    second = repository.latest_attempt_diagnosis(result.attempt_id)
    assert diagnosis_for_attempt(repository, result.attempt_id)["diagnosis_id"] == second["id"]
    assert repository.live_causal_view(result.attempt_id)[0] == second["id"]

    # Failed successor: a re-diagnosis of the same grade fails for good.
    assert enqueue_diagnosis(vault, repository, attempt_id=result.attempt_id, rediagnose=True) is not None
    failing = ReviewFakeClient(fail_purposes=("diagnosis",))
    assert [o.state for o in drain_jobs(vault, repository, failing)] == ["failed"]
    assert repository.latest_attempt_diagnosis(result.attempt_id)["status"] == "failed"
    assert repository.live_causal_view(result.attempt_id) is None
    assert diagnosis_for_attempt(repository, result.attempt_id) is None
    assert diagnosis_status(repository, result.attempt_id)["status"] == FAILED


def _regrade_state(repository, attempt_id):
    with repository.connection() as connection:
        canonical = [tuple(row) for row in connection.execute("SELECT * FROM facet_capability_evidence ORDER BY facet_id, capability")]
        jobs = [tuple(row) for row in connection.execute("SELECT id, state FROM post_attempt_jobs WHERE attempt_id = ? ORDER BY id", (attempt_id,))]
    attempt = repository.fetch_practice_attempt(attempt_id)
    return {
        "evidence": [(row.id, row.superseded_at) for row in repository.fetch_grading_evidence(attempt_id, include_superseded=True)],
        "grade": (attempt["rubric_score"], attempt["manual_review_reason"]),
        "blind": repository.latest_blind_grade_record(attempt_id)["id"],
        "jobs": jobs,
        "in_force": (repository.live_causal_view(attempt_id) or (None,))[0],
        "events": [event["id"] for event in repository.raw_error_events_for_attempt(attempt_id)],
        "canonical": canonical,
    }


_PUBLICATION_STEPS = (
    ("repository", "insert_regrade_evidence"),
    ("repository", "update_attempt_grade"),
    ("repository", "insert_blind_grade_record"),
    ("module", "replay_learning_object"),
    ("module", "persist_unknown_error_type_proposals"),
)


@pytest.mark.parametrize("where,step", _PUBLICATION_STEPS)
def test_a_crash_between_regrade_publication_steps_publishes_nothing(tmp_path, monkeypatch, where, step):
    """Review F4: the regrade's grading revision, attempt grade, superseding
    blind record (with its re-diagnosis job) and replayed projection commit
    together; a crash after any one step leaves the old grade and its
    diagnosis exactly in force."""

    from learnloop.attempts import regrade as regrade_module

    _paths, vault, repository = split_vault(tmp_path)
    client = _CorrectOnRegrade()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    before = _regrade_state(repository, result.attempt_id)
    assert before["in_force"] is not None

    target = repository if where == "repository" else regrade_module
    real = getattr(target, step)

    def crash_after(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError(f"process died after {step}")

    monkeypatch.setattr(target, step, crash_after)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    with pytest.raises(RuntimeError, match="process died"):
        regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)
    monkeypatch.setattr(target, step, real)

    assert _regrade_state(repository, result.attempt_id) == before
    with repository.connection() as connection:
        statuses = [row[0] for row in connection.execute("SELECT status FROM agent_runs WHERE purpose = 'grading_regrade'")]
    assert statuses == ["failed"]


def test_regrade_replay_never_reads_the_superseded_diagnosis(tmp_path, monkeypatch):
    """Review F4: the new blind record is in before replay reads the grade."""

    from learnloop.attempts import regrade as regrade_module

    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    real = regrade_module.replay_learning_object
    seen = []

    def watching(*args, **kwargs):
        seen.append(
            (
                repository.live_causal_view(result.attempt_id),
                repository.latest_blind_grade_record(result.attempt_id)["supersedes_id"] is not None,
                [job["state"] for job in repository.post_attempt_jobs(attempt_id=result.attempt_id) if job["state"] == "queued"],
            )
        )
        return real(*args, **kwargs)

    monkeypatch.setattr(regrade_module, "replay_learning_object", watching)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)

    assert seen == [(None, True, ["queued"])]


def _enable_split(paths):
    path = paths.root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    assert "split_enabled = false" in text
    path.write_text(text.replace("split_enabled = false", "split_enabled = true"), encoding="utf-8")
    return load_vault(paths.root)


def test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated(tmp_path):
    """Review F2: a new grading execution in a split vault is blind and
    isolated, even for an attempt first graded jointly; the attempt then
    carries a blind record (replay reads its mode from that ledger) and its
    diagnosis is queued in the same publication."""

    paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\nsplit_enabled = false")
    client = ReviewFakeClient()
    result = submit(vault, repository, client)
    assert client.calls == ["grading"]
    assert repository.latest_blind_grade_record(result.attempt_id) is None
    vault = _enable_split(paths)

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=client, grading_source="ai", clock=None)

    assert client.calls == ["grading", "blind_grading"]
    assert client.isolated == [False, True]
    record = repository.latest_blind_grade_record(result.attempt_id)
    assert record is not None and record["supersedes_id"] is None and record["record"]["regrade"] is True
    assert diagnosis_status(repository, result.attempt_id)["status"] == PENDING
    assert [o.status for o in drain_jobs(vault, repository, client)] == ["completed"]
    assert diagnosis_status(repository, result.attempt_id)["status"] == DONE


def test_a_self_graded_fallback_is_regraded_blind_and_queues_its_diagnosis(tmp_path):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.attempts.regrade import run_deferred_ai_regrades

    _paths, vault, repository = split_vault(tmp_path, seed=False)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_compute_001", learner_answer_md="A = U Sigma V wrong"),
        SelfGradeInput(criterion_points={"setup": 1, "result": 0}, confidence=3),
        fallback_reason="provider_timeout",
    )
    client = ReviewFakeClient()

    outcome = run_deferred_ai_regrades(vault, repository, runtime=ReadyRuntime(), ai_client=client)

    assert outcome.regraded == 1
    assert client.calls == ["blind_grading"] and client.isolated == [True]
    assert repository.latest_blind_grade_record(attempt.attempt_id) is not None
    assert diagnosis_status(repository, attempt.attempt_id)["status"] == PENDING


def test_non_practice_graders_use_the_blind_contract_in_an_isolated_turn(tmp_path):
    """Review F2: teach-back, exams, the probe audit and the taxonomy regrade
    share one door; in a split vault it is the blind, isolated contract."""

    from learnloop.attempts.grading import build_grading_context, request_vault_grading_proposal
    from learnloop.diagnosis.taxonomy_regrade import run_taxonomy_regrade_checks

    _paths, vault, repository = split_vault(tmp_path)
    item = vault.practice_items["pi_svd_compute_001"]
    context = build_grading_context(vault, item, attempt_id="exam_answer", learner_answer_md="A = U Sigma V wrong")
    client = ReviewFakeClient()
    proposal = request_vault_grading_proposal(vault, client, context)
    assert client.calls == ["blind_grading"] and client.isolated == [True]
    assert proposal.repair_suggestions == []
    assert all(not attribution.candidate_causes for attribution in proposal.error_attributions)

    report = run_taxonomy_regrade_checks(vault, repository, client, limit=2)
    assert report["checked"] >= 1 and report["prompt_version"] == "mvp-2.0-blind-local-grader"
    assert set(client.calls) == {"blind_grading"} and all(client.isolated)

    joint_paths, joint_vault, _joint_repository = split_vault(tmp_path / "joint", version="mvp-0.9")
    joint_client = ReviewFakeClient()
    request_vault_grading_proposal(joint_vault, joint_client, context)
    assert joint_client.calls == ["grading"]


def test_only_the_joint_doors_call_the_joint_grading_operation():
    """Review F2 guard: every other grader goes through the vault door."""

    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src"
    callers = {
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if re.search(r"\brequest_grading_proposal\(", path.read_text(encoding="utf-8"))
    }
    assert callers == {
        "learnloop/attempts/grading.py",  # the definition and the vault door's joint branch
        "learnloop/diagnosis/diagnostic_augmentation.py",  # joint practice grading (split inactive)
        "learnloop/diagnosis/offline_review/runner.py",  # M1's joint baseline, on a scratch copy
    }
