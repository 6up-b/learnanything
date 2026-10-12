"""Slice 1 M2 §11/§12.2 through the sidecar: status polling and the card."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository

from tests.split_live_helpers import CitingFake, ReadyRuntime, at, split_vault, submit


class _Sidecar:
    def __init__(self, vault_root, client, monkeypatch):
        from learnloop_sidecar.context import SidecarContext

        monkeypatch.setattr(
            "learnloop_sidecar.handlers.practice.ready_grading_provider",
            lambda *_args, **_kwargs: ("fake", ReadyRuntime(), client),
        )
        self.ctx = SidecarContext()
        # Deterministic: jobs stay queued until the test drains them.
        self.ctx.post_attempt_worker.autostart = False
        self.ctx.post_attempt_worker.client_factory = lambda _vault: client
        self.ctx.post_attempt_worker.embedding_factory = lambda _vault: None
        self.result("initialize", {"vaultPath": str(vault_root)})

    def call(self, method, params=None):
        from learnloop_sidecar.server import _handle

        return _handle(self.ctx, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    def result(self, method, params=None):
        response = self.call(method, params)
        assert "error" not in response, response
        return response["result"]

    def submit(self, session_id, answer="A = U Sigma V wrong", item="pi_svd_compute_001", key="K1"):
        return self.result(
            "submit_attempt",
            {
                "sessionId": session_id,
                "practiceItemId": item,
                "answerMd": answer,
                "attemptType": "independent_attempt",
                "submissionId": key,
            },
        )


@pytest.fixture
def card_setup(tmp_path, monkeypatch):
    paths, _vault, _repository = split_vault(tmp_path)
    client = CitingFake()
    sidecar = _Sidecar(paths.root, client, monkeypatch)
    session_id = sidecar.result("start_session", {})["sessionId"]
    return paths, sidecar, client, session_id


def test_submit_reports_pending_and_the_card_fills_after_the_worker_runs(card_setup):
    paths, sidecar, client, session_id = card_setup
    submitted = sidecar.submit(session_id)
    attempt_id = submitted["attemptId"]

    assert submitted["diagnosisStatus"] == "pending"
    assert client.calls == ["blind_grading"]
    assert sidecar.result("get_feedback", {"attemptId": attempt_id})["diagnosisStatus"] == "pending"
    pending = sidecar.result("diagnosis_status", {"attemptId": attempt_id})
    assert pending["status"] == "pending" and "summaryMd" not in pending

    sidecar.ctx.post_attempt_worker.run_pending("diagnose")
    card = sidecar.result("diagnosis_status", {"attemptId": attempt_id})

    assert card["status"] == "done" and card["cardEnabled"] is True
    assert card["summaryMd"] == "Diagnosis across time."
    assert [row["response"] for row in card["responses"]] == [
        "believed_candidate",
        "partly",
        "slipped",
        "diagnosis_wrong",
        "unsure",
    ]
    assert card["repairSuggestions"] and card["repairSuggestions"][0]["operator"] == "elicit_rule"
    cited = {row["attemptId"] for row in card["madeBefore"]}
    # Only validated citations (S4): same-LO blind-valid failures.
    assert cited == {"att_02_svd_fail", "att_06_svd_fail", "att_07_svd_future"}
    assert card["prerequisiteGap"]["prerequisiteRef"] == "lo_transpose"
    assert card["prerequisiteGap"]["label"] == "possible cause - not yet checked"
    bundle = sidecar.result("get_feedback", {"attemptId": attempt_id, "recordOpen": False})
    assert bundle["diagnosisStatus"] == "done"
    assert bundle["repairSuggestions"][0]["operator"] == "elicit_rule"


def test_card_tap_is_recorded_and_card_only_values_are_not_forwarded(card_setup):
    paths, sidecar, _client, session_id = card_setup
    attempt_id = sidecar.submit(session_id)["attemptId"]
    sidecar.ctx.post_attempt_worker.run_pending("diagnose")
    card = sidecar.result("diagnosis_status", {"attemptId": attempt_id})

    recorded = sidecar.result(
        "record_diagnosis_feedback",
        {"attemptId": attempt_id, "diagnosisId": card["diagnosisId"], "response": "partly"},
    )

    assert recorded["forwardedFactorId"] is None and recorded["forwarding"] == "card_only"
    rows = Repository(paths.sqlite_path).diagnosis_feedback_rows(card["diagnosisId"])
    assert [(row["response"], row["cited_attempt_id"]) for row in rows] == [("partly", None)]
    assert sidecar.result("diagnosis_status", {"attemptId": attempt_id})["recordedResponse"] == "partly"


def test_forwarding_happens_only_with_an_open_factor(card_setup):
    paths, sidecar, _client, session_id = card_setup
    attempt_id = sidecar.submit(session_id)["attemptId"]
    sidecar.ctx.post_attempt_worker.run_pending("diagnose")
    repository = Repository(paths.sqlite_path)
    card = sidecar.result("diagnosis_status", {"attemptId": attempt_id})
    factors = repository.unresolved_cause_factors_for_attempt(attempt_id, status="open")

    recorded = sidecar.result(
        "record_diagnosis_feedback",
        {"attemptId": attempt_id, "diagnosisId": card["diagnosisId"], "response": "slipped"},
    )

    if factors:
        assert recorded["forwardedFactorId"] == factors[0]["id"]
        reports = repository.causal_attribution_reports_for_factor(factors[0]["id"])
        assert [row["response"] for row in reports] == ["slipped"]
    else:
        assert recorded["forwardedFactorId"] is None and recorded["forwarding"] == "no_open_factor"


def test_not_same_mistake_needs_a_validated_citation_and_lands_in_the_ledger(card_setup):
    paths, sidecar, _client, session_id = card_setup
    attempt_id = sidecar.submit(session_id)["attemptId"]
    sidecar.ctx.post_attempt_worker.run_pending("diagnose")
    card = sidecar.result("diagnosis_status", {"attemptId": attempt_id})

    refused = sidecar.call(
        "record_diagnosis_feedback",
        {
            "attemptId": attempt_id,
            "diagnosisId": card["diagnosisId"],
            "response": "not_same_mistake",
            "citedAttemptId": "att_01_transpose_fail",
        },
    )
    assert refused["error"]["data"]["code"] == "validation_error"
    sidecar.result(
        "record_diagnosis_feedback",
        {
            "attemptId": attempt_id,
            "diagnosisId": card["diagnosisId"],
            "response": "not_same_mistake",
            "citedAttemptId": "att_02_svd_fail",
        },
    )
    with Repository(paths.sqlite_path).connection() as connection:
        rows = connection.execute(
            "SELECT judge, verdict, left_id, right_id FROM judgment_ledger WHERE task = 'same_cause' AND judge = 'learner_card'"
        ).fetchall()
    assert [tuple(row) for row in rows] == [("learner_card", "different", attempt_id, "att_02_svd_fail")]
    assert sidecar.result("diagnosis_status", {"attemptId": attempt_id})["notSameMistakeAttemptIds"] == ["att_02_svd_fail"]


def test_repairs_first_displayed_on_the_card_are_debited_once(card_setup):
    paths, sidecar, _client, session_id = card_setup
    attempt_id = sidecar.submit(session_id)["attemptId"]
    # The learner opens the feedback BEFORE the diagnosis lands: nothing to debit.
    sidecar.result("get_feedback", {"attemptId": attempt_id})
    sidecar.ctx.post_attempt_worker.run_pending("diagnose")

    def card_reveals():
        with Repository(paths.sqlite_path).connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM reveal_events WHERE attempt_id = ? AND basis LIKE 'repair_display:diagnosis:%'",
                (attempt_id,),
            ).fetchone()[0]

    sidecar.result("diagnosis_status", {"attemptId": attempt_id})
    assert card_reveals() == 1
    sidecar.result("diagnosis_status", {"attemptId": attempt_id})
    assert card_reveals() == 1


def test_card_kill_switch_hides_the_card_but_its_repairs_still_debit_once(tmp_path, monkeypatch):
    paths, _vault, _repository = split_vault(tmp_path, config="[diagnosis]\ncard_enabled = false")
    client = CitingFake()
    sidecar = _Sidecar(paths.root, client, monkeypatch)
    session_id = sidecar.result("start_session", {})["sessionId"]
    attempt_id = sidecar.submit(session_id)["attemptId"]
    sidecar.result("get_feedback", {"attemptId": attempt_id})
    sidecar.ctx.post_attempt_worker.run_pending("diagnose")

    card = sidecar.result("diagnosis_status", {"attemptId": attempt_id})
    sidecar.result("diagnosis_status", {"attemptId": attempt_id})

    assert card["status"] == "done" and card["cardEnabled"] is False
    # The repairs still reach the feedback view (the bundle carries them).
    with Repository(paths.sqlite_path).connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM reveal_events WHERE basis LIKE 'repair_display:diagnosis:%'"
        ).fetchone()[0] == 1


def test_joint_vault_feedback_carries_no_diagnosis_status(tmp_path, monkeypatch):
    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.9")
    client = CitingFake()
    sidecar = _Sidecar(paths.root, client, monkeypatch)
    session_id = sidecar.result("start_session", {})["sessionId"]
    submitted = sidecar.submit(session_id)

    assert "diagnosisStatus" not in submitted
    assert "diagnosisStatus" not in sidecar.result("get_feedback", {"attemptId": submitted["attemptId"]})
    assert sidecar.ctx.post_attempt_worker.running is False


def test_card_summary_names_earlier_answers_by_date_not_id(tmp_path):
    from learnloop.diagnosis.split.card import plain_summary

    _paths, vault, repository = split_vault(tmp_path)
    earlier = submit(vault, repository, CitingFake(), when=at(20)).attempt_id
    created = str(repository.fetch_practice_attempt(earlier)["created_at"])[:10]

    text = plain_summary(repository, f"You passed in {earlier}; hypothesis 01M4QP6KQCEP5W69B34E2HVHBV is withdrawn.")

    assert text == f"You passed in your answer on {created}; hypothesis an earlier record is withdrawn."
