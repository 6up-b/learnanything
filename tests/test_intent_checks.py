"""Daily-loop DL2: serving "Check once" (§5.2) and the Reader's DL2 requests (§18).

(a) the dated branch reads ``commitment_versions.due_hint`` when present and
falls back to ``capture.test_me_later_days`` otherwise (RW6b depends on it);
(b) the plan's ``check_once`` provider (``test_intent_plan.py`` covers the
minutes bound); (c) a served check on your own: the cold banner, help never
blocked with the ladder's header stating the consequence (D42), a header
that locates nothing until feedback (D46, G61); (d) the way back after the
measurement when the provenance carries inquiry roots or anchor spans.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.intent.checks import (
    COLD_BANNER,
    HELP_LADDER_HEADER,
    answered_check,
    restoration_link,
    served_check,
    settle_answered_checks,
)
from tests.helpers import append_config_toml
from tests.intent_fakes import NOW, make_intent_vault


@pytest.fixture
def iv(tmp_path):
    return make_intent_vault(tmp_path / "vault")


def _reader_check(iv, item_id, *, due_hint=None, provenance=None, at=NOW):
    """A test_me_later commitment another path made (Reader "reconstruct", RW6b follow-ups)."""

    return C.create_commitment(
        iv.repository, action="test_me_later", intent_text="rebuild without the book",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item_id, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key=f"reader_reconstruct:{item_id}",
        due_hint=due_hint, provenance=provenance, clock=FrozenClock(at),
    ).id


def test_a_due_hint_dates_the_check(iv):
    _reader_check(iv, "pi_b1", due_hint=(NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert "pi_b1" not in iv.queue(NOW + timedelta(days=1))
    assert "pi_b1" in iv.queue(NOW + timedelta(days=2, minutes=1))
    check = iv.serving(NOW + timedelta(days=2, minutes=1)).checks
    assert [state.date_source for state in check.values()] == ["due_hint"]


def test_a_date_only_due_hint_means_that_local_day(iv):
    day = (NOW + timedelta(days=3)).astimezone().date()
    _reader_check(iv, "pi_b1", due_hint=day.isoformat())
    (state,) = iv.serving(NOW).checks.values()
    assert state.date.astimezone().date() == day and state.date_source == "due_hint"


def test_without_a_due_hint_the_check_waits_test_me_later_days(iv):
    _reader_check(iv, "pi_b1")
    assert "pi_b1" not in iv.queue(NOW + timedelta(days=6, hours=23))
    assert "pi_b1" in iv.queue(NOW + timedelta(days=7, minutes=1))
    (state,) = iv.serving(NOW).checks.values()
    assert state.date_source == "test_me_later_days"


def test_the_delay_follows_capture_test_me_later_days(iv):
    append_config_toml(iv.root, "[capture]\ntest_me_later_days = 2\n")
    iv.reload()
    _reader_check(iv, "pi_b1")
    assert "pi_b1" in iv.queue(NOW + timedelta(days=2, minutes=1))


def test_settling_writes_the_satisfaction_once_and_only_for_answered_checks(iv):
    answered = _reader_check(iv, "pi_b1")
    waiting = _reader_check(iv, "pi_c1")
    due_day = NOW + timedelta(days=7, minutes=5)
    attempt = iv.answer("pi_b1", due_day)
    clock = FrozenClock(due_day + timedelta(minutes=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=clock) == [answered]
    assert C.resolve_disposition(iv.repository, answered) == "satisfied"
    assert C.resolve_disposition(iv.repository, waiting) == "one_check_pending"
    assert settle_answered_checks(iv.vault, iv.repository, clock=clock) == []
    events = [e for e in iv.repository.commitment_events_for(answered) if e["kind"] == "disposition_changed"]
    assert len(events) == 1 and attempt in events[0]["detail_json"]


def test_an_attempt_before_the_date_does_not_answer_the_check(iv):
    commitment = _reader_check(iv, "pi_b1")
    iv.answer("pi_b1", NOW + timedelta(days=1))
    assert settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(NOW + timedelta(days=2))) == []
    assert C.resolve_disposition(iv.repository, commitment) == "one_check_pending"


def test_a_served_check_is_cold_help_stays_with_its_consequence_and_nothing_locates_it(iv):
    _reader_check(iv, "pi_b1")
    due_day = NOW + timedelta(days=8)
    view = served_check(iv.vault, iv.repository, "pi_b1", now=due_day)
    assert view["banner"] == COLD_BANNER
    assert view["banner"] == "A check on your own. Help is still here — using it makes this practice with help."
    assert "practice with help" in view["help_header"] and view["help_header"] == HELP_LADDER_HEADER
    assert view["locators_hidden"] is True
    assert view["restoration"] is None
    # Not yet due, an uncommitted item, or an answered check: no check view.
    assert served_check(iv.vault, iv.repository, "pi_b1", now=NOW + timedelta(days=1)) is None
    assert served_check(iv.vault, iv.repository, "pi_a1", now=due_day) is None
    iv.answer("pi_b1", due_day)
    assert served_check(iv.vault, iv.repository, "pi_b1", now=due_day + timedelta(minutes=1)) is None


def test_the_way_back_is_rendered_only_when_the_provenance_carries_it(iv):
    assert restoration_link({}) is None
    assert restoration_link({"via": "intent_control"}) is None
    provenance = {
        "via": "reader_followup", "inquiry_root_event_ids": ["ev_1"], "anchor_span_ids": ["sp_9"],
        "extraction_id": "ex_1", "restoration_label": "Mixture CDF → integration bounds",
    }
    link = restoration_link(provenance)
    assert link["label"] == "Back to where you studied this"
    assert link["detail"] == "Mixture CDF → integration bounds"
    assert link["anchor_span_ids"] == ["sp_9"] and link["inquiry_root_event_ids"] == ["ev_1"]
    _reader_check(iv, "pi_b1", provenance=provenance)
    due_day = NOW + timedelta(days=8)
    assert served_check(iv.vault, iv.repository, "pi_b1", now=due_day)["restoration"]["extraction_id"] == "ex_1"
    attempt = iv.answer("pi_b1", due_day)
    settle_answered_checks(iv.vault, iv.repository, clock=FrozenClock(due_day + timedelta(minutes=1)))
    after = answered_check(iv.vault, iv.repository, attempt)
    assert after["kind"] == "check_once" and after["restoration"]["anchor_span_ids"] == ["sp_9"]


def test_an_ordinary_attempt_answers_no_check(iv):
    attempt = iv.answer("pi_a1", NOW)
    assert answered_check(iv.vault, iv.repository, attempt) is None


def test_reader_requests_and_checks_share_one_request_list(iv):
    """A reader check's item is a request only through the dated branch."""

    _reader_check(iv, "pi_b1")
    assert "pi_b1" not in iv.requested(NOW + timedelta(days=1))
    assert "pi_b1" in iv.requested(NOW + timedelta(days=8))
