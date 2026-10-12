"""Slice 1 M2 §11: the router tolerates a late diagnosis."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.clock import FrozenClock

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, at, drain_jobs, split_vault, submit


class _Sidecar:
    def __init__(self, vault_root, client, monkeypatch, *, autostart: bool):
        from learnloop_sidecar.context import SidecarContext

        monkeypatch.setattr(
            "learnloop_sidecar.handlers.practice.ready_grading_provider",
            lambda *_args, **_kwargs: ("fake", ReadyRuntime(), client),
        )
        self.ctx = SidecarContext()
        self.ctx.post_attempt_worker.autostart = autostart
        self.ctx.post_attempt_worker.client_factory = lambda _vault: client
        self.ctx.post_attempt_worker.embedding_factory = lambda _vault: None

    def call(self, method, params=None):
        from learnloop_sidecar.server import _handle

        return _handle(self.ctx, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    def result(self, method, params=None):
        response = self.call(method, params)
        assert "error" not in response, response
        return response["result"]


def _submit(sidecar, session_id, key="K1"):
    return sidecar.result(
        "submit_attempt",
        {
            "sessionId": session_id,
            "practiceItemId": "pi_svd_compute_001",
            "answerMd": "A = U Sigma V wrong",
            "attemptType": "independent_attempt",
            "submissionId": key,
        },
    )


def _serve(sidecar, session_id, item_id="pi_svd_compute_002"):
    return sidecar.result("get_practice_item", {"practiceItemId": item_id, "sessionId": session_id})


def test_next_item_waits_for_the_running_diagnosis(tmp_path, monkeypatch):
    paths, _vault, _repository = split_vault(tmp_path)
    sidecar = _Sidecar(paths.root, ReviewFakeClient(), monkeypatch, autostart=True)
    try:
        sidecar.result("initialize", {"vaultPath": str(paths.root)})
        session_id = sidecar.result("start_session", {})["sessionId"]
        attempt_id = _submit(sidecar, session_id)["attemptId"]
        sidecar.result("get_today_queue", {"sessionId": session_id})
        _serve(sidecar, session_id)
    finally:
        sidecar.ctx.post_attempt_worker.shutdown()
    repository = Repository(paths.sqlite_path)
    receipts = repository.diagnosis_wait_receipts()
    assert len(receipts) == 1
    assert receipts[0]["served_without_diagnosis"] is False
    assert repository.latest_attempt_diagnosis(attempt_id)["status"] == "completed"


def test_a_pick_served_while_the_diagnosis_is_pending_is_receipted(tmp_path, monkeypatch):
    paths, _vault, _repository = split_vault(tmp_path)
    sidecar = _Sidecar(paths.root, ReviewFakeClient(), monkeypatch, autostart=False)
    sidecar.result("initialize", {"vaultPath": str(paths.root)})
    session_id = sidecar.result("start_session", {})["sessionId"]
    attempt_id = _submit(sidecar, session_id)["attemptId"]

    queue = sidecar.result("get_today_queue", {"sessionId": session_id})
    assert "sections" in queue  # the queue is built regardless
    # Review F10: a queue refresh is not a serve; only the served item counts.
    assert Repository(paths.sqlite_path).diagnosis_wait_receipts() == []
    _serve(sidecar, session_id)

    receipts = Repository(paths.sqlite_path).diagnosis_wait_receipts()
    assert [(row["served_without_diagnosis"], row["pending_attempt_ids"]) for row in receipts] == [
        (True, [attempt_id])
    ]


def test_no_wait_and_no_receipt_without_a_pending_diagnosis(tmp_path, monkeypatch):
    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.9")
    sidecar = _Sidecar(paths.root, ReviewFakeClient(), monkeypatch, autostart=False)
    sidecar.result("initialize", {"vaultPath": str(paths.root)})
    session_id = sidecar.result("start_session", {})["sessionId"]
    _submit(sidecar, session_id)
    sidecar.result("get_today_queue", {"sessionId": session_id})
    _serve(sidecar, session_id)
    assert Repository(paths.sqlite_path).diagnosis_wait_receipts() == []


def test_the_lag_rate_is_over_every_serve_that_followed_a_diagnosed_answer(tmp_path, monkeypatch):
    """Review F10: E7's denominator is every serve after a diagnosis-bearing
    answer in the session, including serves that needed no wait; a serve
    whose diagnosis already landed is served WITH it."""

    from learnloop.diagnosis.split.reports import m2_report
    from learnloop.vault.loader import load_vault

    paths, _vault, _repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    sidecar = _Sidecar(paths.root, client, monkeypatch, autostart=False)
    sidecar.result("initialize", {"vaultPath": str(paths.root)})
    session_id = sidecar.result("start_session", {})["sessionId"]
    _submit(sidecar, session_id, key="K1")
    # The first diagnosis lands before the next serve: no wait, served with it.
    assert [o.state for o in sidecar.ctx.post_attempt_worker.run_pending("diagnose")] == ["done"]
    _serve(sidecar, session_id)
    _serve(sidecar, session_id, item_id="pi_transpose_001")
    # The second answer's diagnosis is still pending at the next serve.
    second = _submit(sidecar, session_id, key="K2")["attemptId"]
    _serve(sidecar, session_id)

    repository = Repository(paths.sqlite_path)
    receipts = repository.diagnosis_wait_receipts()
    assert [row["served_without_diagnosis"] for row in receipts] == [False, False, True]
    assert receipts[-1]["pending_attempt_ids"] == [second]
    e7 = m2_report(load_vault(paths.root), repository)["e7_operational"]["served_without_diagnosis"]
    assert (e7["k"], e7["n"]) == (1, 3)


class _Wait:
    def take_wait(self, _session_id):
        return 0.0


class _FlipToCorrect(ReviewFakeClient):
    """Wrong blind grades until ``correct`` is set, then full marks."""

    correct = False

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        if not self.correct:
            return result
        points = {c["id"]: c["points"] for c in context["rubric"]["criteria"]}
        evidence = [row.model_copy(update={"points_awarded": points[row.criterion_id]}) for row in result.criterion_evidence]
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [],
            }
        )


def test_a_failed_or_budget_skipped_diagnosis_is_unavailable_at_the_serve(tmp_path):
    """Review F13: availability is the diagnosis in force, not the job's
    state. A required diagnosis that failed or was skipped for budget leaves
    the serve without one; a not-needed one takes the serve out of E7."""

    from types import SimpleNamespace

    from learnloop.attempts.regrade import regrade_attempt
    from learnloop_sidecar.handlers.queue import record_diagnosis_serve

    _paths, vault, repository = split_vault(
        tmp_path, config="[diagnosis]\nmax_attempts = 1\nmax_calls_per_day = 1"
    )
    ctx = SimpleNamespace(post_attempt_worker=_Wait())
    failing = ReviewFakeClient(fail_purposes=("diagnosis",))

    failed_session = repository.create_session()
    failed = submit(vault, repository, failing, session_id=failed_session, when=at(20))
    assert [(o.state, o.error) for o in drain_jobs(vault, repository, failing)] == [("failed", "AIProviderUnavailable")]

    budget_session = repository.create_session()
    skipped = submit(vault, repository, ReviewFakeClient(), session_id=budget_session, when=at(21))
    assert [(o.state, o.error) for o in drain_jobs(vault, repository, ReviewFakeClient())] == [("skipped", "budget")]

    retired_session = repository.create_session()
    flipping = _FlipToCorrect()
    retired = submit(vault, repository, flipping, session_id=retired_session, when=at(22))
    drain_jobs(vault, repository, flipping)  # over the daily cap: a budget skip
    flipping.correct = True
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(retired.attempt_id),
        runtime=ReadyRuntime(), client=flipping, grading_source="ai", clock=None,
    )
    assert [(o.state, o.error) for o in drain_jobs(vault, repository, flipping)] == [("skipped", "not_needed")]

    for session_id in (failed_session, budget_session, retired_session):
        record_diagnosis_serve(ctx, repository, session_id)

    receipts = repository.diagnosis_wait_receipts()
    assert [(row["session_id"], row["served_without_diagnosis"], row["pending_attempt_ids"]) for row in receipts] == [
        (failed_session, True, [failed.attempt_id]),
        (budget_session, True, [skipped.attempt_id]),
    ]


def test_the_open_factor_takes_the_diagnosis_causes_when_it_lands(tmp_path):
    """§7.1: a blind attempt's factor opens at grade time with only the
    synthesized facet arms; when the diagnosis lands, the still-open factor
    takes exactly the candidate set a rebuild would open it with."""

    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault

    from tests.helpers import set_algorithm_version
    from tests.test_km2_write_path import build_mvp07_vault

    paths = build_mvp07_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.10")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository)
    client = ReviewFakeClient()
    result = submit(vault, repository, client, item_id="pi_svd_ambiguous_001", answer="Something wrong here")

    def statements():
        return [
            [str(cause.get("statement")) for cause in factor.get("candidate_causes") or []]
            for factor in repository.unresolved_cause_factors_for_attempt(result.attempt_id, status="open")
        ]

    before = statements()
    assert before and all(statement.startswith(("Failure of", "Another cause")) for statement in before[0])

    drain_jobs(vault, repository, client)

    after = statements()
    assert after[0][:2] == [
        "The answer goes wrong because the learner misapplies the rule.",
        "A slip while copying.",
    ]
    assert after[0][-1] == "Another cause not represented by the listed hypotheses"
    # The factor's arms are the materialized hypotheses (P1 refs), so a probe
    # set locked on it includes the causes the diagnosis actually claimed.
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id, status="open")[0]
    refs = {str(cause.get("hypothesis_id")) for cause in factor["candidate_causes"] if not cause.get("open_set")}
    heads = {row["id"] for row in repository.causal_hypotheses_for_attempt(result.attempt_id)}
    assert refs and refs <= heads


def test_as_of_cutoff_excludes_attempts_completed_after_the_diagnosed_one(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    first = submit(vault, repository, client, when=at(20), answer="A = U Sigma V first")
    later = submit(
        vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V LATER-ANSWER", when=at(21)
    )

    drain_jobs(vault, repository, client, clock=FrozenClock(at(22)))

    diagnosis = repository.latest_attempt_diagnosis(first.attempt_id)
    receipt = repository.diagnosis_context_receipt(diagnosis["id"])
    shown = {*receipt["failure_attempt_ids"], *receipt["success_attempt_ids"]}
    assert later.attempt_id not in shown
    assert receipt["lagged_attempts"] >= 1
    first_prompt = next(prompt for purpose, prompt in zip(client.calls, client.prompts) if purpose == "diagnosis")
    assert "LATER-ANSWER" not in first_prompt
