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


def test_m2_report_counts_logical_diagnosis_calls_and_their_turns(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    rows = [
        # A Codex root (no usage) with a first turn and a JSON-repair turn.
        ("root1", None, "diagnosis", None, None),
        ("t1", "root1", "diagnosis:sdk_turn", 100, 10),
        ("t2", "root1", "diagnosis_json_repair:sdk_turn", 120, 12),
        # A provider that reports usage on the root itself.
        ("root2", None, "diagnosis", 50, 5),
        # The hybrid retrieval query embedding: an embedding call, not a diagnosis.
        ("emb", None, "embedding", 7, 0),
    ]
    with repository.connection() as connection:
        for row_id, parent, purpose, tokens_in, tokens_out in rows:
            connection.execute(
                "INSERT INTO model_call_receipts(id, parent_call_id, owner_kind, owner_id, purpose, status, "
                "started_at, input_tokens, output_tokens) VALUES (?, ?, 'attempt_diagnosis', 'a', ?, 'completed', ?, ?, ?)",
                (row_id, parent, purpose, "2026-10-12T00:00:00Z", tokens_in, tokens_out),
            )
        connection.commit()

    e7 = m2_report(vault, repository)["e7_operational"]

    assert e7["diagnosis_calls"] == 2
    assert e7["diagnosis_repair_turns"] == 1
    assert e7["embedding_calls"] == 1
    # (110 + 132) + 55 tokens over the attempts with a diagnosis row (none here: divided by 1).
    assert e7["diagnosis_tokens_per_attempt"] == 297.0


def _fake_route(monkeypatch, client):
    import learnloop.diagnosis.split.jobs as jobs_module

    monkeypatch.setattr(jobs_module, "default_diagnosis_client", lambda _vault: client)


def test_cli_drain_and_retry_plan_and_estimate_before_spending(tmp_path, monkeypatch):
    """Review F5: both commands have a dry run that plans the queue, estimates
    the calls against the caps and changes nothing; a run over its caps is
    refused before any call."""

    paths, vault, repository = split_vault(tmp_path)
    first = submit(vault, repository, ReviewFakeClient(), when=at(20))
    submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(21))
    client = ReviewFakeClient()
    _fake_route(monkeypatch, client)
    runner = CliRunner()
    root = str(paths.root)

    dry = runner.invoke(app, ["diagnose", "drain", "--vault", root, "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    plan = json.loads(dry.output)
    assert plan["status"] == "dry_run"
    assert [job["action"] for job in plan["diagnose"]["jobs"]] == ["diagnose", "diagnose"]
    assert plan["diagnose"]["calls"] == 2 and plan["diagnose"]["estimated_input_tokens"] > 0
    assert plan["diagnose"]["route"]["billing"] == "subscription" and plan["diagnose"]["admissible"] is True
    assert client.calls == []
    assert {job["state"] for job in repository.post_attempt_jobs(kind="diagnose")} == {"queued"}
    assert {job["attempt_count"] for job in repository.post_attempt_jobs(kind="diagnose")} == {0}

    over = runner.invoke(app, ["diagnose", "drain", "--vault", root, "--max-calls", "1", "--json"])
    assert over.exit_code == 1 and json.loads(over.output)["status"] == "over_budget"
    assert client.calls == []

    retry_plan = runner.invoke(app, ["diagnose", "retry", "--vault", root, "--attempt", first.attempt_id, "--dry-run", "--json"])
    assert retry_plan.exit_code == 0, retry_plan.output
    assert json.loads(retry_plan.output)["diagnose"]["calls"] == 1
    assert client.calls == []

    ran = runner.invoke(app, ["diagnose", "drain", "--vault", root, "--kind", "diagnose", "--json"])
    assert ran.exit_code == 0, ran.output
    assert [job["status"] for job in json.loads(ran.output)["jobs"]] == ["completed", "completed"]
    assert json.loads(ran.output)["spend"]["charged"]["calls"] == 2


def _retrieval_vault(tmp_path, monkeypatch):
    """A split vault with S1.4a on, one registry belief to rank, and the fake
    diagnoser (subscription) and embedder (metered) on the command's routes."""

    import learnloop.diagnosis.split.jobs as jobs_module
    from learnloop.vault.loader import load_vault

    from tests.diagnosis_fakes import FakeEmbeddingClient
    from tests.split_live_helpers import enable_embeddings

    paths, _vault, repository = split_vault(tmp_path)
    enable_embeddings(paths.root)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace("dimensions = 4096", "dimensions = 16"), encoding="utf-8")
    vault = load_vault(paths.root)
    repository.insert_misconception(
        learning_object_id="lo_unrelated",
        statement="The learner applies the rule in the wrong order.",
        concept_id="unrelated_topic",
        severity=0.5,
        source_error_event_ids=[repository.raw_error_events_for_attempt("att_02_svd_fail")[0]["id"]],
        clock=FrozenClock(at(9)),
    )
    client, embedder = ReviewFakeClient(), FakeEmbeddingClient()
    _fake_route(monkeypatch, client)
    monkeypatch.setattr(jobs_module, "default_embedding_client", lambda _vault: embedder)
    return paths, vault, repository, client, embedder


def _registry_method(repository, attempt_id):
    diagnosis = repository.latest_attempt_diagnosis(attempt_id)
    return repository.diagnosis_context_receipt(diagnosis["id"])["retrieval"]["registry_retrieval"]["method"]


def test_retrieval_embeddings_are_admitted_and_charged_on_the_command_budget(tmp_path, monkeypatch):
    """Review F12: a drain's registry retrieval embeds on the command's own
    budget. With no metered allowance the subscription diagnosis still runs
    and retrieval falls back to the exact set without a single embedding
    request; with one, the dry run estimates retrieval and the run charges it."""

    paths, vault, repository, client, embedder = _retrieval_vault(tmp_path, monkeypatch)
    first = submit(vault, repository, ReviewFakeClient(), when=at(20))
    runner = CliRunner()
    root = str(paths.root)

    zero = runner.invoke(
        app,
        ["diagnose", "drain", "--vault", root, "--kind", "diagnose", "--max-tokens", "0", "--max-cost-usd", "0", "--json"],
    )

    assert zero.exit_code == 0, zero.output
    payload = json.loads(zero.output)
    assert [job["status"] for job in payload["jobs"]] == ["completed"]
    assert embedder.calls == 0
    assert _registry_method(repository, first.attempt_id) == "exact_fallback"
    charged = payload["spend"]["charged"]
    assert (charged["calls"], charged["metered_total_tokens"], charged["metered_estimated_usd"]) == (1, 0, 0.0)

    second = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(22))
    dry = runner.invoke(app, ["diagnose", "drain", "--vault", root, "--kind", "diagnose", "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    retrieval = json.loads(dry.output)["diagnose"]["retrieval"]
    assert retrieval["calls"] >= 1 and retrieval["estimated_input_tokens"] > 0
    assert retrieval["route"]["billing"] == "metered" and retrieval["fits"] is True
    assert embedder.calls == 0

    ran = runner.invoke(app, ["diagnose", "drain", "--vault", root, "--kind", "diagnose", "--json"])

    assert ran.exit_code == 0, ran.output
    spend = json.loads(ran.output)["spend"]
    assert _registry_method(repository, second.attempt_id) == "knn"
    assert embedder.calls >= 1
    assert spend["routes"]["embedding"]["calls"] == embedder.calls
    assert spend["charged"]["calls"] == 1 + embedder.calls
    assert spend["charged"]["metered_total_tokens"] > 0 and spend["charged"]["metered_estimated_usd"] > 0
    assert embedder.calls <= retrieval["calls"]


def test_retrieval_never_takes_the_call_a_queued_diagnosis_needs(tmp_path, monkeypatch):
    """Review F12: an embedding request is admitted only while every queued
    diagnosis still fits the command's caps after it."""

    paths, vault, repository, client, embedder = _retrieval_vault(tmp_path, monkeypatch)
    submit(vault, repository, ReviewFakeClient(), when=at(20))
    submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(21))

    ran = CliRunner().invoke(
        app, ["diagnose", "drain", "--vault", str(paths.root), "--kind", "diagnose", "--max-calls", "2", "--json"]
    )

    assert ran.exit_code == 0, ran.output
    assert [job["status"] for job in json.loads(ran.output)["jobs"]] == ["completed", "completed"]
    assert embedder.calls == 0


def test_ctrl_c_stops_the_drain_before_the_next_paid_job(tmp_path, monkeypatch):
    """Review F7: SIGINT during a drain stops it before the next job starts."""

    import os
    import signal

    paths, vault, repository = split_vault(tmp_path)
    submit(vault, repository, ReviewFakeClient(), when=at(20))
    second = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(21))

    class Interrupting(ReviewFakeClient):
        def _diagnosis(self, request, context):
            os.kill(os.getpid(), signal.SIGINT)  # the owner presses Ctrl-C mid-call
            return super()._diagnosis(request, context)

    client = Interrupting()
    _fake_route(monkeypatch, client)

    result = CliRunner().invoke(app, ["diagnose", "drain", "--vault", str(paths.root), "--kind", "diagnose", "--json"])

    assert result.exit_code == 0, result.output
    assert client.calls.count("diagnosis") == 1
    assert [job["state"] for job in repository.post_attempt_jobs(attempt_id=second.attempt_id)] == ["queued"]
    assert json.loads(result.output)["status"] == "cancelled"


def test_a_cancelled_job_is_released_unspent(tmp_path):
    """Review F7: cancellation observed after the claim releases the lease."""

    from learnloop.diagnosis.split.jobs import process_next_job

    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, ReviewFakeClient())
    client = ReviewFakeClient()
    checks = iter([False, True])

    outcome = process_next_job(
        vault, repository, kind="diagnose", owner="cli",
        client_factory=lambda: client, embedding_factory=lambda: None,
        cancelled=lambda: next(checks, True),
    )

    assert (outcome.state, outcome.error) == ("released", "cancelled")
    job = repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]
    assert job["state"] == "queued" and job["attempt_count"] == 0
    assert client.calls == []
