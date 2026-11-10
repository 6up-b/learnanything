"""Refactor B7: the attempt chain's decision records, read back through ``learnloop why --json``.

A graded miss leaves a ``grade`` record under the submit's trace; its diagnosis job continues that trace from the
job's ``job_enqueued`` record, so the diagnosis, its model calls and the follow-up job it queues answer under the same
trace. A held grade leaves ``grade_held`` when the hold first applies. Silent steps (a failed forecast, a failed
post-diagnosis step, a rejected probe value) leave a record. Records hold ids, numbers and codes: no answer text.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.attempts import grade_records
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.db.stores import provenance as decision_store
from learnloop.diagnosis import chain_records
from learnloop.followup_serve.gates import SERVING_SURFACE
from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

from tests.followup_serve_helpers import CLOCK, AuthorFake, BlindRivalClient, author_clients, live_shape_vault
from tests.split_live_helpers import submit

ANSWER = "A = U Sigma V wrong because the learner forgot transposes entirely"


def _why(root, target: str) -> dict[str, Any]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", target, "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    assert ANSWER not in result.output and "transposes" not in result.output
    return json.loads(result.output)


def _kinds(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [record for record in payload["records"] if record["kind"] == kind]


def _worker(vault, repository, client, author) -> PostAttemptWorker:
    worker = PostAttemptWorker(autostart=False)
    worker.bind(lambda: (vault, repository.sqlite_path))
    worker.client_factory = lambda _vault: client
    worker.embedding_factory = lambda _vault: None
    worker.followup_clients = lambda _vault: author_clients(author)
    return worker


def _miss(tmp_path, trace: str = "TRACE_SUBMIT"):
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    client = BlindRivalClient()
    with provenance.trace_scope(trace):
        result = submit(vault, repository, client, answer=ANSWER, pipeline=False, when=CLOCK.now())
        outcome = run_post_attempt_pipeline(vault, repository, result=result, followup_surface=SERVING_SURFACE,
                                            clock=CLOCK)
    return paths, vault, repository, client, result, outcome


def test_the_grades_trace_carries_through_the_diagnosis_to_the_follow_up(tmp_path):
    paths, vault, repository, client, result, outcome = _miss(tmp_path)
    worker = _worker(vault, repository, client, AuthorFake())
    with provenance.trace_scope("THE_RPC_THAT_WOKE_THE_WORKER"):
        diagnosed = worker.run_pending("diagnose", clock=CLOCK)
        generated = worker.run_pending("followup", clock=CLOCK)
    assert diagnosed and generated and outcome.workflow_id

    by_attempt = _why(paths.root, f"attempt:{result.attempt_id}")
    grade = _kinds(by_attempt, "grade")
    assert len(grade) == 1
    assert grade[0]["trace_id"] == "TRACE_SUBMIT" and grade[0]["status"] == "chosen"
    assert grade[0]["decided_by"] == "blind_grader" and grade[0]["rule"] in {"partial_credit", "no_credit"}
    assert grade[0]["detail_table"] == "practice_attempts" and grade[0]["detail_id"] == result.attempt_id
    assert grade[0]["facts"]["rubric_score"] == result.rubric_score and grade[0]["facts"]["max_points"]
    assert grade[0]["versions"]["grading_prompt_version"] and grade[0]["versions"]["algorithm_version"]

    trace = _why(paths.root, "TRACE_SUBMIT")
    queued = _kinds(trace, decision_store.JOB_ENQUEUED)
    diagnose_job = [record for record in queued if record["facts"]["job_kind"] == "diagnose"]
    assert len(diagnose_job) == 1 and diagnose_job[0]["facts"]["attempt_id"] == result.attempt_id
    diagnosis = _kinds(trace, chain_records.DIAGNOSIS)
    assert len(diagnosis) == 1 and diagnosis[0]["status"] == "chosen" and diagnosis[0]["rule"] == "completed"
    # The diagnosis is the queued job's child, in the submit's trace, not the worker's or the waking RPC's.
    assert diagnosis[0]["parent_id"] == diagnose_job[0]["id"]
    assert diagnosis[0]["facts"]["job_id"] == diagnose_job[0]["subject_id"]
    assert diagnosis[0]["versions"]["diagnosis_prompt_version"]
    # The diagnosis queued the follow-up's generation in the same trace, and the generation ran under it.
    workflow_job = [record for record in queued if record["facts"].get("workflow_id") == outcome.workflow_id]
    assert workflow_job and workflow_job[0]["parent_id"] == diagnose_job[0]["id"]
    purposes = {call["purpose"] for call in trace["model_calls"]}
    assert any("diagnos" in str(purpose) for purpose in purposes), purposes
    assert len(trace["model_calls"]) > 1
    with repository.connection() as connection:
        assert provenance.read(connection, "THE_RPC_THAT_WOKE_THE_WORKER") == []
        calls = connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE trace_id = ?",
                                   ("THE_RPC_THAT_WOKE_THE_WORKER",)).fetchone()[0]
    assert calls == 0


def test_a_job_with_no_enqueue_record_keeps_a_trace_of_its_own(tmp_path):
    worker = PostAttemptWorker(autostart=False)
    seen: list[str | None] = []

    class Repo:
        def connection(self):
            raise RuntimeError("no database")

    def job():
        decision_store.continue_job_trace(Repo(), "job_without_record")
        seen.append(provenance.current_trace())
        return seen[-1]

    with provenance.trace_scope("RPC"):
        worker._with_busy_retry(job)
        assert provenance.current_trace() == "RPC"
    assert seen[0] and seen[0] != "RPC"
    # Outside any scope, continuing a trace changes nothing (a direct call leaves no trace on the thread).
    assert provenance.continue_trace("ELSEWHERE", cause="x") is None and provenance.current_trace() is None


def test_continue_trace_switches_the_scope_in_place_and_its_exit_restores(tmp_path):
    with provenance.trace_scope("OUTER"):
        with provenance.trace_scope() as inner:
            assert provenance.continue_trace("QUEUED", cause="rec_1") == "QUEUED"
            assert provenance.current_cause() == "rec_1"
            assert provenance.continue_trace(None) == inner and provenance.current_cause() is None
            provenance.continue_trace("QUEUED", cause="rec_1")
        assert provenance.current_trace() == "OUTER" and provenance.current_cause() is None


def test_a_held_grade_gets_a_record_when_the_hold_first_applies(tmp_path):
    from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW

    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    with provenance.trace_scope("TRACE_HELD"):
        grade_id = grade_records.record_grade(
            repository, attempt_id="att_held", practice_item_id="pi_svd_compute_001", learning_object_id=None,
            rubric_score=2, max_points=4, correctness=0.5, grader_confidence=0.9, grading_source="ai",
            grader_mode="blind", manual_review_reason="valid_alternative_unverified:crit_a,crit_b",
            held=True, unverified_criterion_ids=["crit_a", "crit_b"], algorithm_version="mvp-0.57",
        )
    payload = _why(paths.root, "attempt:att_held")
    held = _kinds(payload, grade_records.GRADE_HELD)
    assert len(held) == 1 and held[0]["parent_id"] == grade_id
    assert held[0]["status"] == "deferred" and held[0]["rule"] == GRADE_HELD_FOR_REVIEW
    assert held[0]["facts"]["unverified_criteria"] == ["crit_a", "crit_b"]
    assert held[0]["facts"]["review_reason"] == "valid_alternative_unverified"
    grade = _kinds(payload, grade_records.GRADE)[0]
    assert grade["facts"]["held"] is True and grade["facts"]["review_reason_ids"] == ["crit_a", "crit_b"]
    # An unheld grade leaves no hold record.
    grade_records.record_grade(repository, attempt_id="att_clear", practice_item_id=None, learning_object_id=None,
                               rubric_score=4, max_points=4, correctness=1.0, grader_confidence=1.0,
                               grading_source="self", grader_mode=None, manual_review_reason=None, held=False)
    clear = _why(paths.root, "attempt:att_clear")
    assert [record["kind"] for record in clear["records"]] == ["grade"]
    assert clear["records"][0]["rule"] == "full_credit" and clear["records"][0]["decided_by"] == "self_grade"


def test_a_live_held_attempt_writes_its_hold_record_in_the_attempt_step(tmp_path, monkeypatch):
    """The step's in-flight predicate (``AttemptApplication.grade_held``) is what the record reads."""

    import learnloop.attempts.attempts as attempts_module

    seen: dict[str, Any] = {}
    real = grade_records.record_grade

    def spy(repository, **values):
        seen.update(values)
        return real(repository, **values)

    monkeypatch.setattr(grade_records, "record_grade", spy)
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    original = attempts_module.compute_attempt_application

    def held_application(*args, **kwargs):
        from dataclasses import replace

        return replace(original(*args, **kwargs), grade_held=True)

    monkeypatch.setattr(attempts_module, "compute_attempt_application", held_application)
    with provenance.trace_scope("TRACE_LIVE_HELD"):
        result = submit(vault, repository, BlindRivalClient(), answer=ANSWER, pipeline=False, when=CLOCK.now())
    assert seen["held"] is True and seen["attempt_id"] == result.attempt_id
    payload = _why(paths.root, f"attempt:{result.attempt_id}")
    assert [record["kind"] for record in payload["records"]] == ["grade", "grade_held"]
    assert all(record["trace_id"] == "TRACE_LIVE_HELD" for record in payload["records"])


def test_replay_writes_no_grade_record(tmp_path):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, vault, repository, _client, result, _outcome = _miss(tmp_path)
    before = _why(paths.root, f"attempt:{result.attempt_id}")["records"]
    rebuild_all_derived_state(vault, repository)
    assert _why(paths.root, f"attempt:{result.attempt_id}")["records"] == before


def test_a_record_that_cannot_be_written_changes_no_grade(tmp_path, monkeypatch, caplog):
    import logging

    paths, vault, repository = live_shape_vault(tmp_path / "a", task_features=False)
    with repository.connection() as connection:  # the table is gone: every record's insert fails
        connection.execute("DROP TABLE decision_records")
        connection.commit()
    with caplog.at_level(logging.WARNING, logger="learnloop.provenance"), provenance.trace_scope("TRACE_BROKEN"):
        broken_result = submit(vault, repository, BlindRivalClient(), answer=ANSWER, pipeline=False,
                               when=CLOCK.now())
    _paths_b, vault_b, repository_b = live_shape_vault(tmp_path / "b", task_features=False)
    kept = submit(vault_b, repository_b, BlindRivalClient(), answer=ANSWER, pipeline=False, when=CLOCK.now())
    for field in ("rubric_score", "correctness", "fsrs_rating", "due_at", "manual_review_reason", "mastery_mean"):
        assert getattr(broken_result, field) == getattr(kept, field), field
    assert repository.fetch_practice_attempt(broken_result.attempt_id) is not None
    assert any("decision record 'grade' not written (trace TRACE_BROKEN)" in record.getMessage()
               for record in caplog.records)


def test_a_failed_forecast_and_a_failed_post_diagnosis_step_leave_records(tmp_path, monkeypatch):
    from learnloop.diagnosis import followups, voi_forecasting

    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)

    def boom(*_args, **_kwargs):
        raise ValueError("the learner wrote transposes here")

    monkeypatch.setattr(voi_forecasting.VF, "record_forecast", boom)
    monkeypatch.setattr("learnloop.diagnosis.causal_orchestrator.sweep_machine_checks", boom)
    with provenance.trace_scope("TRACE_STEPS"):
        voi_forecasting.record_value_decision_forecast(
            vault, repository, {"decision": "continue", "site": "followup_intervention", "candidates": [],
                                "best": {"ref": "pi_a", "evsi_robust_minutes": 1.0, "cost_minutes": 0.5}},
            receipt_key="followup_value_decision:fvd_1", decision_ref="fvd_1",
        )
        followups.run_post_diagnosis_hooks(vault, repository, attempt_id="att_steps", learning_object_id="lo_x")
    payload = _why(paths.root, "TRACE_STEPS")
    forecast = _kinds(payload, chain_records.VOI_FORECAST)
    steps = _kinds(payload, chain_records.DIAGNOSIS_STEP)
    assert len(forecast) == 1 and forecast[0]["status"] == "failed"
    assert forecast[0]["subject_id"] == "fvd_1" and forecast[0]["facts"]["site"] == "value_decision"
    assert forecast[0]["facts"]["receipt_key"] == "followup_value_decision:fvd_1"
    sweep = [record for record in steps if record["rule"] == "machine_check_sweep"]
    assert len(sweep) == 1 and sweep[0]["status"] == "failed" and sweep[0]["error_type"] == "ValueError"
    assert sweep[0]["error_where"].startswith("tests.test_attempt_chain_records:boom:")
    assert sweep[0]["subject_id"] == "att_steps"


def test_forecast_failure_is_recorded_when_the_forecast_runs(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    try:
        raise KeyError("the learner wrote transposes here")
    except KeyError as exc:
        with provenance.trace_scope("TRACE_FORECAST"):
            chain_records.record_forecast_failed(repository, site="probe_selection", exc=exc, decision_ref="pp_1")
    record = _kinds(_why(paths.root, "TRACE_FORECAST"), chain_records.VOI_FORECAST)[0]
    assert record["rule"] == "forecast_not_recorded" and record["subject_kind"] == "decision"
    assert record["error_type"] == "KeyError" and record["facts"]["site"] == "probe_selection"


def test_a_rejected_probe_value_and_a_learner_lane_offer_are_recorded(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    decision = {
        "forecast_version": "voi-v1", "site": "probe_episode", "decision": "stop", "recommended_ref": None,
        "candidate_count": 2, "cap_comparison": "earlier",
        "candidates": [{"ref": "pi_a", "evsi_robust_minutes": 0.1, "cost_minutes": 2.0, "reason": "value_below_cost"},
                       {"ref": "pi_b", "evsi_robust_minutes": 0.05, "cost_minutes": 3.0, "reason": "value_below_cost"}],
        "subject_ref": "pi_a", "subject": {"evsi_robust_minutes": 0.1, "cost_minutes": 2.0},
        "context": {"note": "the learner wrote transposes here"},
    }
    offer = SimpleNamespace(accepted=False, reason="no_reviewed_active_candidate", factor_id="fac_1",
                            episode_id=None, presentation_id=None, practice_item_id=None, candidate_id=None,
                            hypothesis_set_id=None, blind_bundle_ids=())
    with provenance.trace_scope("TRACE_PROBE"):
        chain_records.record_probe_value(repository, practice_item_id="pi_a", episode_id="ep_1",
                                         reason="value_below_minutes_cost", decision=decision)
        chain_records.record_probe_offer(repository, offer=offer, decision_receipt_id="cpr_1",
                                         router_decision_id=None, followup_workflow_id=None)
    payload = _why(paths.root, "TRACE_PROBE")
    value = _kinds(payload, chain_records.PROBE_VALUE)[0]
    assert value["status"] == "excluded" and value["rule"] == "value_below_minutes_cost"
    assert value["subject_kind"] == "item" and value["subject_id"] == "pi_a"
    assert value["facts"]["item_cost_minutes"] == 2.0 and value["facts"]["cap_comparison"] == "earlier"
    assert [alt["ref"] for alt in value["alternatives"]] == ["pi_a", "pi_b"]
    offered = _kinds(payload, chain_records.PROBE_OFFER)[0]
    assert offered["decided_by"] == "learner_lane" and offered["status"] == "refused"
    assert offered["facts"]["causal_receipt_id"] == "cpr_1" and offered["facts"]["router_decision_id"] is None
    assert _why(paths.root, "factor:fac_1")["records"][0]["kind"] == chain_records.PROBE_OFFER


def test_the_sidecar_records_a_rejected_probe_value(tmp_path, monkeypatch):
    """The real door: ``start_probe_attempt`` refused by value writes ``probe_value`` and still answers inactive."""

    import learnloop_sidecar.handlers.practice as practice

    from tests.test_voi_stopping import LO, _minutes, _probe_vault

    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)  # no observation pays for ten thousand minutes
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda _vault, override=None: ("test", SimpleNamespace(ready=True), object()))
    ctx = SimpleNamespace(grading_provider_override=None)
    item = vault.practice_items["pi_svd_define_001"]
    with provenance.trace_scope("TRACE_DOOR"):
        reply = practice._probe_contract(ctx, vault, repository, item,
                                         practice.ProbeContractInput(practice_item_id=item.id, session_id="sess"))
    assert reply["active"] is False and reply["reason"] == "value_below_minutes_cost"
    (record,) = _kinds(_why(paths.root, "TRACE_DOOR"), chain_records.PROBE_VALUE)
    assert record["subject_id"] == item.id and record["facts"]["episode_id"] == repository.open_probe_episode(LO).id
    assert record["facts"]["decision"] == "stop" and record["facts"]["item_cost_minutes"] == 10_000.0


def test_grade_records_hold_no_prose():
    record = grade_records.grade_record(
        attempt_id="att 1 with spaces", practice_item_id="pi_x", learning_object_id="lo_x", rubric_score=1,
        max_points=3, correctness=1 / 3, grader_confidence=0.5, grading_source="ai", grader_mode=None,
        manual_review_reason="the grader said something long", fallback_reason="Provider failed: timeout talking",
        error_types=["e_one", "an error with spaces"],
    )
    assert record.rule == "partial_credit" and record.status == "fallback"
    assert record.facts["review_reason"] == "unnamed" and record.facts["fallback_reason"] == "unnamed"
    assert record.facts["error_types"] == ["e_one"] and record.facts["error_types_n"] == 2
    assert provenance.check_no_prose(record) == ["subject_id", "detail_id"]  # the free-form attempt id; write drops it


@pytest.mark.parametrize(("score", "maximum", "kind", "expected"), [
    (0, 4, "independent_attempt", "no_credit"), (4, 4, "independent_attempt", "full_credit"),
    (2, 4, "independent_attempt", "partial_credit"), (0, 4, "dont_know", "dont_know"),
])
def test_verdict_classes(score, maximum, kind, expected):
    assert grade_records.verdict_class(rubric_score=score, max_points=maximum, correctness=None, attempt_type=kind,
                                       declared_dont_know=False, declared_stuck=False) == expected


# -- blindness: no grader context can read decision_records -----------------------------------------------------

#: The grader's prompt builders and context assembly (every grading prompt is built in these modules).
_GRADER_ROOTS = ("learnloop.attempts.blind_grading", "learnloop.attempts.grading_support",
                 "learnloop.attempts.grading", "learnloop.attempts.ai_contracts",
                 "learnloop.attempts.grading_admission", "learnloop.attempts.grader_calibration")
#: The read side of the record: the leaf's reads and the store's.
_LEAF_READS = frozenset({"read", "read_naming"})
_STORE_READS = frozenset({"trace_model_calls", "discarded_calls", "unclaimed_calls", "continue_job_trace"})
#: The job processors continue the trace that queued their job: the read gives the ContextVar a trace id and the cause
#: a record id, never a record's content, and they are the diagnoser's and the gap reader's jobs, not the grader's.
_TRACE_CONTINUERS = frozenset({"learnloop.diagnosis.split.jobs", "learnloop.diagnosis.text_gaps.jobs"})
_REGISTRIES = frozenset({"learnloop.db.table_roles", "learnloop.adaptive_difficulty.protected_tables",
                         "learnloop.adaptive_difficulty.column_classes"})


def test_no_grader_context_can_read_decision_records():
    import ast
    from pathlib import Path

    import grimp

    src = Path(__file__).resolve().parents[1] / "src"
    graph = grimp.build_graph("learnloop", cache_dir=None)
    closure: set[str] = set()
    for root in _GRADER_ROOTS:
        closure |= {root} | set(graph.find_upstream_modules(root))
        # The prompt builders and context assembly import neither the leaf nor the store.
        direct = graph.find_modules_directly_imported_by(root)
        assert "learnloop.provenance" not in direct and decision_store.__name__ not in direct, root
    assert len(closure) > 100
    naming, reading = [], []
    for module in sorted(closure - {"learnloop.provenance", decision_store.__name__} - _REGISTRIES):
        base = src.joinpath(*module.split("."))
        path = base / "__init__.py" if base.is_dir() else base.with_suffix(".py")
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "decision_records" in text:
            naming.append(module)
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and node.module == "learnloop.provenance":
                reading += [f"{module}:{a.name}" for a in node.names if a.name in _LEAF_READS]
            if isinstance(node, ast.ImportFrom) and node.module == decision_store.__name__:
                reading += [f"{module}:{a.name}" for a in node.names if a.name in _STORE_READS]
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "provenance" and node.attr in _LEAF_READS:
                    reading.append(f"{module}:provenance.{node.attr}")
                if node.attr in _STORE_READS and not (node.attr == "continue_job_trace"
                                                      and module in _TRACE_CONTINUERS):
                    reading.append(f"{module}:{node.value.id}.{node.attr}")
    assert naming == [] and reading == []


def test_a_grading_call_with_records_present_sees_none_of_them(tmp_path):
    _paths, vault, repository, client, _first, _outcome = _miss(tmp_path, trace="TRACE_FIRST")
    _worker(vault, repository, client, AuthorFake()).run_pending("diagnose", clock=CLOCK)
    planted = provenance.DecisionRecord(
        kind="grade", status="chosen", subject_kind="item", subject_id="pi_svd_compute_001",
        chosen_ref="PLANTED_REF_9F3", decided_by="PLANTED_BY_9F3", rule="PLANTED_RULE_9F3",
        facts={"marker": "PLANTED_FACT_9F3"}, versions={"v": "PLANTED_VERSION_9F3"}, trace_id="PLANTED_TRACE_9F3",
    )
    assert decision_store.write_decision(repository, planted)
    with repository.connection() as connection:
        rows = connection.execute("SELECT id, trace_id FROM decision_records").fetchall()
    tokens = {"PLANTED_REF_9F3", "PLANTED_BY_9F3", "PLANTED_RULE_9F3", "PLANTED_FACT_9F3", "PLANTED_VERSION_9F3",
              "PLANTED_TRACE_9F3", "TRACE_FIRST"} | {str(row[0]) for row in rows}
    assert len(rows) >= 4  # the first attempt's grade, its job, its diagnosis, and the planted one
    grader = BlindRivalClient()
    with provenance.trace_scope("TRACE_SECOND"):
        submit(vault, repository, grader, answer=ANSWER, pipeline=False, when=CLOCK.now())
    grading_prompts = [prompt for purpose, prompt in zip(grader.calls, grader.prompts, strict=True)
                       if "grad" in purpose]
    assert grading_prompts
    for prompt in grading_prompts:
        assert not [token for token in tokens if token in prompt]
        assert "decision_records" not in prompt
