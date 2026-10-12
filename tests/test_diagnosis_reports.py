"""Slice 1 M2 reports (E5, E7, §12.3) and the PF-c before/after command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.diagnosis.split.card import record_card_tap
from learnloop.diagnosis.split.pfc_report import plan_pfc, run_pfc
from learnloop.diagnosis.split.reports import m2_report, render_markdown

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import CitingFake, at, drain_jobs, split_vault, submit


def test_m2_report_aggregates_without_learner_text(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = CitingFake()
    result = submit(vault, repository, client, when=at(20), answer="A = U Sigma V SECRET-ANSWER")
    drain_jobs(vault, repository, client, clock=FrozenClock(at(21)))
    diagnosis = repository.latest_attempt_diagnosis(result.attempt_id)
    record_card_tap(vault, repository, attempt_id=result.attempt_id, diagnosis_id=diagnosis["id"], response="partly")
    record_card_tap(
        vault, repository, attempt_id=result.attempt_id, diagnosis_id=diagnosis["id"],
        response="not_same_mistake", cited_attempt_id="att_02_svd_fail",
    )
    repository.insert_diagnosis_wait_receipt(
        session_id="s", pending_attempt_ids=[result.attempt_id], waited_seconds=10.0, served_without_diagnosis=True
    )

    report = m2_report(vault, repository)
    text = json.dumps(report, default=str) + render_markdown(report)

    assert "SECRET-ANSWER" not in text and "Diagnosis across time." not in text
    assert report["manifest"]["blind_graded_attempts"] == 1
    assert report["e7_operational"]["served_without_diagnosis"]["k"] == 1
    assert report["e7_operational"]["diagnoses_by_status"] == {"live:completed": 1}
    assert report["learner_signals"]["card_responses"] == {"partly": 1}
    assert report["learner_signals"]["not_same_mistake_per_citation"]["k"] == 1
    assert report["e5_recurrence_shadow"]["same_cause_verdicts_by_judge"]["learner_card"] == {"different": 1}
    assert report["e5_recurrence_shadow"]["same_cause_verdicts_by_judge"]["diagnoser"]["same"] >= 1


class _ArmFake(ReviewFakeClient):
    """Marks every answer down under mvp-2.0 and grades it on the merits under
    PF-c's mvp-2.1 - the valid-alternative false rejection the report measures."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        if "reference_policy" in context:
            return result
        evidence = [row.model_copy(update={"points_awarded": 0}) for row in result.criterion_evidence]
        return result.model_copy(update={"criterion_evidence": evidence, "rubric_score": 0})


def test_pfc_report_compares_before_and_after_and_records_verdicts(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    plan = plan_pfc(vault, repository, max_items=3, max_real=0, seed=1)
    assert len(plan["items"]) == 3
    client = _ArmFake()

    report = run_pfc(vault, repository, plan=plan, generator_client=client, grading_client=client)

    before = report["arms"]["before"]["valid_alternative_false_rejection"]
    after = report["arms"]["after"]["valid_alternative_false_rejection"]
    verified = report["statuses"].get("alternative_verified", 0)
    assert verified >= 1
    assert before["k"] == verified and after["k"] == 0
    assert report["paired_transitions"] == {"rejected->accepted": verified}
    with repository.connection() as connection:
        tasks = dict(connection.execute(
            "SELECT task, COUNT(*) FROM judgment_ledger WHERE task IN ('reference_verified', 'valid_alternative_grade') GROUP BY task"
        ).fetchall())
    assert tasks["reference_verified"] == 3 and tasks["valid_alternative_grade"] == 2 * verified


def test_cli_status_drain_retry_and_reports(tmp_path):
    paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, ReviewFakeClient())
    runner = CliRunner()

    status = runner.invoke(app, ["diagnose", "status", "--vault", str(paths.root), "--attempt", result.attempt_id, "--json"])
    assert status.exit_code == 0, status.output
    assert json.loads(status.output)["status"] == "pending"
    # No diagnosis provider is ready in tests: the drain leaves it queued.
    drained = runner.invoke(app, ["diagnose", "drain", "--vault", str(paths.root), "--json"])
    assert drained.exit_code == 0, drained.output
    assert [job["state"] for job in json.loads(drained.output)["jobs"]] == ["released"]
    report = runner.invoke(app, ["diagnose", "m2-report", "--vault", str(paths.root), "--json"])
    assert report.exit_code == 0 and json.loads(report.output)["report_version"]
    dry = runner.invoke(app, ["diagnose", "pfc-report", "--vault", str(paths.root), "--dry-run", "--max-items", "2", "--max-real", "0", "--json"])
    assert dry.exit_code == 0, dry.output
    plan = json.loads(dry.output)
    assert plan["status"] == "dry_run" and plan["estimate"]["calls"] == {"diagnosis_generator": 2, "grading": 4}


def test_cli_retry_requeues_a_failed_diagnosis(tmp_path):
    paths, vault, repository = split_vault(tmp_path, config="[diagnosis]\nmax_attempts = 1")
    client = ReviewFakeClient(fail_purposes=("diagnosis",))
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]["state"] == "failed"

    retried = CliRunner().invoke(
        app, ["diagnose", "retry", "--vault", str(paths.root), "--attempt", result.attempt_id, "--queue-only", "--json"]
    )

    assert retried.exit_code == 0, retried.output
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]["state"] == "queued"
    drain_jobs(vault, repository, ReviewFakeClient())
    assert repository.latest_attempt_diagnosis(result.attempt_id)["status"] == "completed"
