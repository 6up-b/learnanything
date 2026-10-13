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
from learnloop.clock import FrozenClock
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_inquiry as RI
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader.reader_report import build_reader_report
from tests.helpers import NOW
from tests.reader_fixtures import transcript_source
from tests.test_reader_dialogue import _setup
from tests.test_reader_reconnect import FakeClient


def _at(minutes: float) -> FrozenClock:
    return FrozenClock(NOW + timedelta(minutes=minutes))


def _log(repo, minutes, *entries):
    RI.record_activity(repo, list(entries), clock=_at(minutes))


def _seed(tmp_path):
    vault, repo = _setup(tmp_path)
    client = RD.StubReaderClient()
    # Visit 1: open, select, ask (completed, learner kept reading), branch, return.
    _log(repo, 0, {"kind": "reader_view_opened", "payload": {"visit_id": "v1", "extraction_id": "ext1", "source_kind": "pdf"}})
    _log(repo, 1, {"kind": "reader_selection", "payload": {"visit_id": "v1", "extraction_id": "ext1", "span_count": 1}})
    _log(repo, 1.5, {"kind": "reader_action_invoked", "event": "action_invoked", "payload": {"visit_id": "v1", "action_kind": "ask"}},
         {"kind": "reader_job_queued", "payload": {"visit_id": "v1", "job_id": "j1", "job_kind": "ask"}})
    root = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1", question_md="Root", clock=_at(1.6))
    _log(repo, 1.7, {"kind": "reader_job_completed", "payload": {
        "visit_id": "v1", "job_id": "j1", "job_kind": "ask", "status": "completed", "latency_ms": 4000,
        "model_wait_ms": 3800, "model": "stub-reader-1", "prompt_version": "p3-reader-branches-v1",
        "activity_during_wait": {"scrolled": True}}})
    _log(repo, 2, {"kind": "reader_action_invoked", "event": "back_to_reading", "payload": {"visit_id": "v1", "job_id": "j1", "action_kind": "ask"}})
    _log(repo, 3, {"kind": "reader_selection", "payload": {"visit_id": "v1", "extraction_id": "ext1", "span_count": 2}})
    _log(repo, 3.5, {"kind": "reader_action_invoked", "event": "action_invoked", "payload": {"visit_id": "v1", "action_kind": "follow_up"}},
         {"kind": "reader_job_queued", "payload": {"visit_id": "v1", "job_id": "j2", "job_kind": "follow_up"}},
         {"kind": "reader_action_invoked", "event": "detour_opened", "payload": {"visit_id": "v1", "detour_id": "d1", "detour_kind": "branch"}})
    child = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1", question_md="Child",
                   parent_exchange_id=root["reader_answer_event_id"], clock=_at(3.6))
    RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1", question_md="Grandchild",
           parent_exchange_id=child["reader_answer_event_id"], clock=_at(3.7))
    RD.ask(vault, repo, client, extraction_id="ext1", span_id="s1", question_md="Sibling",
           parent_exchange_id=root["reader_answer_event_id"], clock=_at(3.8))
    _log(repo, 3.9, {"kind": "reader_job_completed", "payload": {
        "visit_id": "v1", "job_id": "j2", "job_kind": "follow_up", "status": "failed", "failure_reason": "provider_unavailable",
        "latency_ms": 9000, "model_wait_ms": 9000, "activity_during_wait": {}}})
    _log(repo, 6.5, {"kind": "reader_action_invoked", "event": "detour_returned", "payload": {
        "visit_id": "v1", "detour_id": "d1", "detour_kind": "branch", "returned_to_origin": True, "seconds_away": 180,
        "model_wait_ms": 9000, "via": "alt_back"}},
         {"kind": "reader_action_invoked", "event": "reconnect_shown", "payload": {"visit_id": "v1", "root_exchange_id": root["reader_answer_event_id"], "placement": "inline"}})
    RI.answer_reconnect(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"], answer="yes",
                        via="inline", clock=_at(7))
    RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=root["reader_answer_event_id"],
                          resolution="open", trigger="chip", clock=_at(8))
    # A second detour (a peek) that never returns.
    _log(repo, 9, {"kind": "reader_action_invoked", "event": "detour_opened", "payload": {"visit_id": "v1", "detour_id": "d2", "detour_kind": "peek"}},
         {"kind": "reader_action_invoked", "event": "proactive_shown", "payload": {"visit_id": "v1", "element": "quick_check_waiting"}})
    _log(repo, 30, {"kind": "reader_view_closed", "payload": {"visit_id": "v1", "active_seconds": 1800, "idle_seconds": 0}})
    # An old inquiry, still open a week later; another dismissed.
    old = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s2", question_md="Old", clock=FrozenClock(NOW - timedelta(days=9)))
    gone = RD.ask(vault, repo, client, extraction_id="ext1", span_id="s0", question_md="Gone", clock=_at(10))
    RI.set_inquiry_status(repo, extraction_id="ext1", exchange_id=gone["reader_answer_event_id"],
                          resolution="dismissed", trigger="chip", clock=_at(11))
    # A reconnect quick check, answered and self-checked.
    row = RQC.author_inquiry_quick_check(repo, FakeClient(), extraction_id="ext1",
                                         inquiry_root_event_id=root["reader_answer_event_id"],
                                         anchor_span_ids=["s1"], clock=_at(12))
    RQC.record_inquiry_action(repo, question_id=row["id"], action="answered", response_md="x", clock=_at(13))
    RQC.record_inquiry_action(repo, question_id=row["id"], action="self_checked", self_check="partly", clock=_at(13))
    return vault, repo, old


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
