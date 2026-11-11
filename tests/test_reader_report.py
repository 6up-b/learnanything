"""`learnloop reader report`: RW1a's workflow funnel, with denominators (spec §4.1, §15).

Reports, never thresholds: selection -> action -> usable result -> back to
reading; inquiries (opened, depth, breadth, resolved, dismissed, reopened,
still open after 7 days, reconnect answers); detours (return rate and cost);
proactive load per reading hour; waiting behaviour; visits. No model call and
no learner text: the database is opened read-only.
"""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.reader_report import build_reader_report
from tests.helpers import NOW
from tests.reader_fixtures import transcript_source
from tests.reader_dialogue_helpers import _setup
from tests.reader_report_helpers import _at, _log, _seed


def test_the_funnel_reports_workflows_with_denominators(tmp_path):
    vault, repo, _old = _seed(tmp_path)
    report = build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=60))
    funnel = report["selection_to_reading"]
    assert funnel["selections"] == 2
    assert funnel["actions"] == {"total": 2, "by_kind": {"ask": 1, "follow_up": 1}}
    ask = funnel["model_backed"]["ask"]
    assert (ask["queued"], ask["completed"], ask["failed"], ask["cancelled"]) == (1, 1, 0, 0)
    assert ask["latency_ms"] == {"n": 1, "p50": 4000, "p95": 4000}
    assert ask["model_wait_ms"]["p50"] == 3800
    follow = funnel["model_backed"]["follow_up"]
    assert follow["failed"] == 1 and follow["failure_reasons"] == {"provider_unavailable": 1}
    assert funnel["back_to_reading"] == {"count": 1, "of": 1, "share": 1.0}

    inquiry = report["inquiry"]
    assert inquiry["opened"] == 3  # the root, the old one, the dismissed one
    assert inquiry["branches"] == 3
    assert inquiry["depth"]["max"] == 2 and inquiry["breadth"]["max"] == 2
    assert (inquiry["resolved"], inquiry["dismissed"], inquiry["reopened"]) == (1, 1, 1)
    assert inquiry["open_after_7_days"] == 1
    assert inquiry["reconnect_answers"] == {"yes": 1, "still_unclear": 0, "quick_check": 0}
    assert inquiry["quick_checks"] == {"authored": 1, "answered": 1,
                                       "self_check": {"matches": 0, "partly": 1, "no": 0}}

    detours = report["detours"]
    assert (detours["opened"], detours["returned_to_origin"]) == (2, 1)
    assert detours["return_rate"] == {"count": 1, "of": 2, "share": 0.5}
    assert detours["cost_minutes"]["p50"] == 3.0
    assert detours["by_kind"] == {"branch": {"opened": 1, "returned": 1}, "peek": {"opened": 1, "returned": 0}}

    load = report["proactive_load"]
    assert load["shown"] == 2 and load["by_element"] == {"reconnect_line": 1, "quick_check_waiting": 1}
    assert load["reading_hours"] == 0.5 and load["per_reading_hour"] == 4.0

    waiting = report["waiting"]
    assert waiting == {"count": 1, "of": 2, "share": 0.5}

    visits = report["visits"]
    assert visits["visits"] == 1 and visits["active_minutes"] == 30.0
    assert visits["time_to_first_action_seconds"]["p50"] == 90.0
    routes = {(r["job_kind"], r["model"], r["prompt_version"]): r for r in report["routes"]}
    assert routes[("ask", "stub-reader-1", "p3-reader-branches-v1")]["n"] == 1


def test_the_report_carries_no_learner_text(tmp_path):
    _vault, repo, _old = _seed(tmp_path)
    flat = json.dumps(build_reader_report(repo.sqlite_path, now=NOW))
    for words in ("Root", "Child", "Grandchild", "Sibling", "Old", "Gone"):
        assert f'"{words}"' not in flat


def test_since_narrows_the_window(tmp_path):
    _vault, repo, _old = _seed(tmp_path)
    report = build_reader_report(repo.sqlite_path, since=(NOW + timedelta(minutes=5)).isoformat(),
                                 now=NOW + timedelta(minutes=60))
    assert report["selection_to_reading"]["selections"] == 0
    assert report["detours"]["opened"] == 1


def test_cli_prints_json_and_leaves_the_database_untouched(tmp_path):
    vault, repo, _old = _seed(tmp_path)
    digest = hashlib.sha256(repo.sqlite_path.read_bytes()).hexdigest()
    result = CliRunner().invoke(app, ["reader", "report", "--vault", str(vault.root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["version"] == "reader-report-v1"
    assert payload["inquiry"]["opened"] == 3
    assert hashlib.sha256(repo.sqlite_path.read_bytes()).hexdigest() == digest


def test_transcript_inquiries_count_like_any_other(tmp_path):
    vault, repo = _setup(tmp_path)
    fixture = transcript_source(repo)
    RD.ask(vault, repo, RD.StubReaderClient(), extraction_id=fixture["extraction_id"],
           span_id=fixture["span_id"], question_md="Why weighted?", clock=_at(1))
    report = build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=5))
    assert report["inquiry"]["opened"] == 1


def _detour(minutes, event, detour_id, kind="branch", **payload):
    return {"kind": "reader_action_invoked", "event": event,
            "payload": {"visit_id": "v1", "detour_id": detour_id, "detour_kind": kind, **payload}}


def test_a_detour_returned_to_again_counts_once_so_the_rate_never_exceeds_one(tmp_path):
    """Codex review F7: returning, walking forward, and returning again (or a
    client that reports the same return twice) is one completed detour."""
    _vault, repo = _setup(tmp_path)
    _log(repo, 1, _detour(1, "detour_opened", "d1"), _detour(1, "detour_opened", "d2", "peek"))
    for minutes in (2, 4, 6):
        _log(repo, minutes, _detour(minutes, "detour_returned", "d1", returned_to_origin=True, seconds_away=60),
             _detour(minutes, "detour_returned", "d2", "peek", returned_to_origin=True, seconds_away=60))
    detours = build_reader_report(repo.sqlite_path, now=NOW + timedelta(minutes=30))["detours"]
    assert (detours["opened"], detours["returned_to_origin"]) == (2, 2)
    assert detours["return_rate"] == {"count": 2, "of": 2, "share": 1.0}
    assert detours["by_kind"] == {"branch": {"opened": 1, "returned": 1}, "peek": {"opened": 1, "returned": 1}}
    assert detours["cost_minutes"]["n"] == 2


def test_a_return_whose_opening_is_outside_the_window_is_not_counted(tmp_path):
    """The window counts detours opened in it, and their first return."""
    _vault, repo = _setup(tmp_path)
    _log(repo, 1, _detour(1, "detour_opened", "early"))
    _log(repo, 20, _detour(20, "detour_opened", "late"))
    _log(repo, 25, _detour(25, "detour_returned", "early", returned_to_origin=True, seconds_away=1440),
         _detour(25, "detour_returned", "late", returned_to_origin=True, seconds_away=300),
         _detour(25, "detour_returned", "unknown", returned_to_origin=True, seconds_away=5))
    detours = build_reader_report(repo.sqlite_path, since=(NOW + timedelta(minutes=10)).isoformat(),
                                  now=NOW + timedelta(minutes=30))["detours"]
    assert detours["return_rate"] == {"count": 1, "of": 1, "share": 1.0}
    assert detours["cost_minutes"]["p50"] == 5.0


def test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel(tmp_path, monkeypatch):
    """Codex review F8: the events the Reader records for a reconnect quick
    check (sent through reader.log_activity, as the screen sends them) land in
    the funnel with its route, failure reasons and cancellations."""
    from types import SimpleNamespace

    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop_sidecar.handlers import reader
    from tests.sidecar_reader_helpers import _init, _rpc, _setup as _rpc_setup

    root_dir = _rpc_setup(tmp_path)
    monkeypatch.setattr(reader, "ready_tutor_qa_provider", lambda vault: ("stub", SimpleNamespace(ready=True), RD.StubReaderClient()))
    visit = {"visitId": "v9", "extractionId": "ext1", "sourceKind": "pdf"}
    events = [
        {"kind": "reader_job_queued", "payload": {**visit, "jobId": "batch_1", "jobKind": "quick_check"}},
        {"kind": "reader_job_completed", "payload": {
            **visit, "jobId": "batch_1", "jobKind": "quick_check", "status": "completed", "latencyMs": 21000,
            "modelWaitMs": 21000, "model": "gpt-5.6-sol", "promptVersion": RQC.INQUIRY_PROMPT_VERSION,
            "activityDuringWait": {"scrolled": True}}},
        {"kind": "reader_job_queued", "payload": {**visit, "jobId": "batch_2", "jobKind": "quick_check"}},
        {"kind": "reader_job_completed", "payload": {
            **visit, "jobId": "batch_2", "jobKind": "quick_check", "status": "failed", "failureReason": "capped",
            "latencyMs": 3000, "modelWaitMs": 3000, "activityDuringWait": {}}},
        {"kind": "reader_job_queued", "payload": {**visit, "jobId": "batch_3", "jobKind": "quick_check"}},
        {"kind": "reader_job_completed", "payload": {
            **visit, "jobId": "batch_3", "jobKind": "quick_check", "status": "cancelled", "latencyMs": 2000,
            "modelWaitMs": 2000, "activityDuringWait": {"typed": True}}},
    ]
    recorded = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.log_activity",
                                       "params": {"events": events}}])[1]["result"]
    assert recorded["recorded"] == 6
    loaded = load_vault(root_dir)
    report = build_reader_report(Repository(VaultPaths(loaded.root, loaded.config).sqlite_path).sqlite_path)
    check = report["selection_to_reading"]["model_backed"]["quick_check"]
    assert (check["queued"], check["completed"], check["failed"], check["cancelled"]) == (3, 1, 1, 1)
    assert check["failure_reasons"] == {"capped": 1}
    assert check["latency_ms"]["p50"] == 21000
    routes = {(r["job_kind"], r["model"], r["prompt_version"]) for r in report["routes"]}
    assert ("quick_check", "gpt-5.6-sol", RQC.INQUIRY_PROMPT_VERSION) in routes
    assert report["waiting"] == {"count": 2, "of": 3, "share": 0.6667}
