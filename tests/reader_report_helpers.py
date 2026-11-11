"""What other test files use from ``tests/test_reader_report.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import reader_inquiry as RI
from learnloop.reader import reader_quick_check as RQC

from tests.helpers import NOW
from tests.reader_dialogue_helpers import _setup
from tests.reader_reconnect_helpers import FakeClient


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
