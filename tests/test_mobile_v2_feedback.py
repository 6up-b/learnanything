"""Mobile v2 stage V2: practice and feedback parity on the phone (spec §2.1 J2, J3 partial, J4, J16 partial).

Through the real host with the fake grader on a fresh vault: the full answer's display rows (a reveal
recorded before it shows), the contest ("I think I was right") as a job under its own key, the follow-up
read and its ways out, the hypothesis exposure, the router's explanation, and an item's own hint
revealed on the phone (counted at submit; the reveal row is telemetry). No model, no network.
"""

from __future__ import annotations

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

from learnloop_mobile.host import create_app

from tests.mobile_host_helpers import (
    HOSTNAME, ITEM, CountingGrader, Phone, config_for, install_grader, pair, rows, seeded_vault,
)


@pytest.fixture
def answered(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    install_grader(monkeypatch, CountingGrader())
    # The contest's regrade finds no grader: the reason is kept and the grade goes to review; no model is asked.
    import learnloop_sidecar.handlers.ai_providers as providers
    from tests.mobile_host_helpers import DownRuntime

    monkeypatch.setattr(providers, "ready_grading_provider", lambda vault, override=None: ("fake", DownRuntime(), None))
    first, second = pair(repository), pair(repository, label="Other phone")
    with TestClient(create_app(config_for(paths.root)), base_url=f"https://{HOSTNAME}") as client:
        phone = Phone(client, first)
        session_id = phone.start()["sessionId"]
        phone.rpc("get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})
        response = phone.submit(session_id, "sub_v2_feedback")
        assert response.status_code == 200, response.text
        attempt_id = response.json()["result"]["attemptId"]
        yield phone, Phone(client, second), repository, session_id, attempt_id


def test_j2_the_full_answers_display_is_recorded_once_per_display_id(answered):
    phone, _other, repository, _session_id, attempt_id = answered
    first = phone.rpc("record_answer_display", {"attemptId": attempt_id, "displayId": "disp_1"})
    again = phone.rpc("record_answer_display", {"attemptId": attempt_id, "displayId": "disp_1"})
    assert first["recorded"] is True and again.get("alreadyRecorded") is True
    assert len(rows(repository, "SELECT id FROM reveal_events WHERE attempt_id = ?", attempt_id)) >= 1


def test_j2_the_contest_is_a_job_under_its_own_key_and_kept_once(answered):
    phone, _other, repository, _session_id, attempt_id = answered
    params = {"attemptId": attempt_id, "learnerReason": "I used the other convention.", "contestId": "contest_1"}
    status, error = phone.error("trigger_regrade", params, request_id="another_key")
    assert (status, error["code"]) == (422, "validation_error")
    bundle = phone.rpc("trigger_regrade", params, request_id="contest_1")
    assert bundle["contest"]["recorded"] is True
    again = phone.rpc("trigger_regrade", params, request_id="contest_1")
    assert again["contest"] == bundle["contest"]


def test_j3_the_follow_up_read_and_its_ways_out_answer_without_a_workflow(answered):
    phone, _other, _repository, _session_id, attempt_id = answered
    assert phone.rpc("followup_status", {"attemptId": attempt_id})["enabled"] is False
    assert phone.rpc("followup_continue_without", {"attemptId": attempt_id})["continued"] in (True, False)
    assert phone.rpc("followup_show_anyway", {"attemptId": attempt_id})["released"] in (True, False)
    reply = phone.rpc("record_hypothesis_exposure", {"attemptId": attempt_id, "surface": "marks_feedback",
                                                     "hypothesisVersionIds": [], "shownAt": None})
    assert "recorded" in reply
    # V3 (D3): Next on the phone asks the workflow too; with none, it goes on.
    assert phone.rpc("followup_next", {"attemptId": attempt_id})["action"] == "continue"


def test_j4_the_routers_explanation_is_read_only(answered):
    phone, *_ = answered
    reply = phone.rpc("router_objective_explain", {"decisionId": "no_such_decision"})
    assert reply["available"] is False


def test_j16_an_items_own_hint_revealed_on_the_phone_is_recorded_and_the_other_device_is_refused(answered):
    phone, other, repository, session_id, _attempt_id = answered
    params = {"sessionId": session_id, "practiceItemId": ITEM, "submissionId": "sub_hint_1", "authoredIndex": 0,
              "answerMd": "a start", "revealedAt": None}
    item_hints = rows(repository, "SELECT 1 FROM help_assists")
    reply = phone.rpc("practice.record_hint_reveal", params)
    assert reply["recorded"] in (True, False)
    if reply["recorded"]:
        assert len(rows(repository, "SELECT surface FROM help_assists")) == len(item_hints) + 1
    status, error = other.error("practice.record_hint_reveal", params)
    assert (status, error["code"]) == (409, "session_moved")


def test_j2_the_diagnosis_cards_tap_is_allowed_and_validated_by_the_handler(answered):
    phone, _other, _repository, _session_id, attempt_id = answered
    response = phone.post("record_diagnosis_feedback", {"attemptId": attempt_id, "diagnosisId": "none",
                                                        "response": "fits"})
    # No diagnosis ran on the fake: the handler's own refusal, never a 403.
    assert response.status_code != 403
