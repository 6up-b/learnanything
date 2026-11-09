"""Doctor's model route health (Decider v1.2 review, docs/reviews/decider-v1-2.md).

A route is a call purpose; doctor reports its last completed call and the
failures since, and flags it only when it failed since its provider/model
last changed with nothing completed since, or never completed. No threshold.
"""
from __future__ import annotations

from contextlib import closing
import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.ops.doctor import run_doctor
from learnloop.ops.model_routes import FINDING_CODE, route_health

from tests.helpers import create_basic_vault

OLD, NEW = "perplexity/pplx-decider-v1.1-27b", "perplexity/pplx-decider-v1.2"


def row(purpose, status, at, *, model=OLD, provider="openrouter_decider", reason=None, text=None):
    return {"purpose": purpose, "provider": provider, "model": model, "status": status,
            "started_at": f"2026-11-0{at}T00:00:00+00:00", "finish_reason": reason,
            "error_type": "DecisionRequestFailed" if status == "failed" else None, "failure_text": text}


def by_purpose(routes):
    return {route.purpose: route for route in routes}


def test_a_route_that_never_completed_is_flagged_with_its_last_error():
    routes = by_purpose(route_health([
        row("learner_gap_kind", "failed", 4, reason="http_404", text="No endpoints found for " + OLD),
        row("learner_gap_kind", "failed", 5, reason="http_404", text="No endpoints found for " + OLD),
    ]))
    route = routes["learner_gap_kind"]
    assert route.flagged and route.last_completed_at is None and route.failures_since_completed == 2
    assert route.first_failure_since_completed_at.startswith("2026-11-04")
    assert (route.last_failure_reason, route.last_failure_error_type) == ("http_404", "DecisionRequestFailed")
    assert "never completed" in route.message() and "No endpoints found" in route.message()


def test_failures_after_a_completed_call_on_the_same_model_are_reported_not_flagged():
    route = by_purpose(route_health([
        row("hint_chooser", "completed", 1), row("hint_chooser", "failed", 2), row("hint_chooser", "failed", 3),
    ]))["hint_chooser"]
    assert not route.flagged and route.failures_since_completed == 2
    assert route.last_completed_at.startswith("2026-11-01")


def test_a_model_change_restarts_the_judgment_both_ways():
    # Completed on the old model, then the new model only fails: flagged since the change.
    failing = by_purpose(route_health([
        row("reader_intent", "completed", 1), row("reader_intent", "failed", 2, model=NEW),
    ]))["reader_intent"]
    assert failing.flagged and failing.current_since.startswith("2026-11-02")
    assert failing.last_completed_model == OLD and failing.model == NEW
    assert "since this provider/model was first used" in failing.message()
    # Failed on the old model, then completed on the new one: healthy, nothing since.
    repaired = by_purpose(route_health([
        row("reader_intent", "failed", 1), row("reader_intent", "completed", 2, model=NEW),
    ]))["reader_intent"]
    assert not repaired.flagged and repaired.failures_since_completed == 0
    assert repaired.last_failure_at is None


def test_a_configured_model_change_waits_for_the_next_call():
    route = by_purpose(route_health(
        [row("ad_item_forecast", "failed", 4)], {"openrouter_decider": NEW},
    ))["ad_item_forecast"]
    assert route.model_changed_since and not route.flagged and route.configured_model == NEW
    same = by_purpose(route_health([row("ad_item_forecast", "failed", 4)], {"openrouter_decider": OLD}))
    assert same["ad_item_forecast"].flagged


def test_started_interrupted_and_truncated_calls_are_neither_failures_nor_completions():
    routes = by_purpose(route_health([
        row("a", "started", 1), row("a", "interrupted", 2), row("a", "truncated", 3),
    ]))
    assert routes["a"].calls == 3 and not routes["a"].flagged and routes["a"].failures_since_completed == 0


def _receipt(connection, call_id, purpose, status, at, *, model=OLD, parent=None, reason=None, output=None):
    connection.execute(
        "INSERT INTO model_call_receipts (id, parent_call_id, owner_kind, owner_id, purpose, provider, model, "
        "status, started_at, finish_reason, error_type, output_text) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (call_id, parent, "test", "t", purpose, "openrouter_decider", model, status,
         f"2026-11-0{at}T00:00:00+00:00", reason, "DecisionRequestFailed" if status == "failed" else None, output),
    )


def test_doctor_reports_routes_in_json_and_text_and_flags_the_dead_one(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with closing(connect(paths.sqlite_path)) as connection, connection:
        _receipt(connection, "c1", "learner_gap_kind", "failed", 4, reason="http_404",
                 output="No endpoints found for " + OLD)
        _receipt(connection, "c2", "learner_gap_kind", "failed", 5, reason="http_404",
                 output="No endpoints found for " + OLD)
        # A malformed paid answer's text never reaches the report.
        _receipt(connection, "c3", "grading", "completed", 1, model="m")
        _receipt(connection, "c4", "grading", "failed", 2, model="m", reason="stop", output="learner answer text")
        # Child receipts belong to their root's route.
        _receipt(connection, "c5", "grading:sdk_turn", "failed", 2, model="m", parent="c4")
    report = run_doctor(paths.root)
    routes = {route["purpose"]: route for route in report.model_routes}
    assert set(routes) == {"learner_gap_kind", "grading"}
    assert routes["learner_gap_kind"]["last_failure_text"] == "No endpoints found for " + OLD
    assert routes["learner_gap_kind"]["failures_since_completed"] == 2
    assert routes["grading"]["flagged"] is False and routes["grading"]["last_failure_text"] is None
    # The code-default decider profile now names v1.2, so a route whose receipts
    # name v1.1 counts as changed by config and waits for its next call.
    assert routes["learner_gap_kind"]["configured_model"] == NEW
    assert routes["learner_gap_kind"]["model_changed_since"] is True
    assert routes["learner_gap_kind"]["flagged"] is False
    assert not [issue for issue in report.issues if issue.code == FINDING_CODE]

    runner = CliRunner()
    payload = json.loads(runner.invoke(app, ["doctor", "--vault", str(paths.root), "--json"]).stdout)
    assert {route["purpose"] for route in payload["model_routes"]} == {"learner_gap_kind", "grading"}
    text = runner.invoke(app, ["doctor", "--vault", str(paths.root)]).stdout
    assert "model route learner_gap_kind (openrouter_decider, " in text and "2 failed since" in text
    assert "model routes: 2 with receipts, 2 failed since their last completed call, 0 not" in text
    assert "learner answer text" not in text and "learner answer text" not in json.dumps(payload)


def test_doctor_flags_a_route_whose_current_model_never_completed(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with closing(connect(paths.sqlite_path)) as connection, connection:
        _receipt(connection, "c1", "router_decision", "failed", 4, model=NEW, reason="http_503",
                 output="provider overloaded")
    report = run_doctor(paths.root)
    (issue,) = [issue for issue in report.issues if issue.code == FINDING_CODE]
    assert issue.severity == "warning" and issue.entity_id == "router_decision"
    assert "http_503" in issue.message and "provider overloaded" in issue.message
    assert issue.details["flagged"] is True and issue.details["model"] == NEW
