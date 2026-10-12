"""Slice 1 M2 §11 C5: the lease-fenced queue and the sidecar's worker thread."""

from __future__ import annotations

import sqlite3
import time
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.diagnosis.split.jobs import DONE, diagnosis_status
from learnloop_sidecar.post_attempt_worker import PostAttemptWorker

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import at, split_vault, submit


def _worker(vault, repository, client, *, autostart: bool = False) -> PostAttemptWorker:
    worker = PostAttemptWorker(autostart=autostart)
    worker.bind(lambda: (vault, repository.sqlite_path))
    worker.client_factory = lambda _vault: client
    worker.embedding_factory = lambda _vault: None
    return worker


@pytest.mark.durability
def test_lease_expiry_reclaims_and_fences_the_stale_worker(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, ReviewFakeClient(), when=at(20))
    start = FrozenClock(at(21))

    first = repository.lease_next_post_attempt_job(kind="diagnose", owner="a", lease_seconds=60, clock=start)
    assert first is not None and first["state"] == "leased" and first["attempt_count"] == 1
    # Held: nobody else may take it.
    assert repository.lease_next_post_attempt_job(kind="diagnose", owner="b", lease_seconds=60, clock=start) is None
    later = FrozenClock(at(21) + timedelta(minutes=5))
    second = repository.lease_next_post_attempt_job(kind="diagnose", owner="b", lease_seconds=60, clock=later)
    assert second is not None and second["id"] == first["id"]
    assert second["lease_epoch"] == first["lease_epoch"] + 1 and second["attempt_count"] == 2
    # The expired worker's late write is fenced off; the new owner's lands.
    assert repository.finish_post_attempt_job(first["id"], epoch=first["lease_epoch"], state="done") is False
    assert repository.owns_post_attempt_job(first["id"], epoch=first["lease_epoch"]) is False
    assert repository.finish_post_attempt_job(second["id"], epoch=second["lease_epoch"], state="done") is True
    assert repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]["state"] == "done"


def test_provider_not_ready_keeps_the_job_queued_without_spending_an_attempt(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, ReviewFakeClient())
    worker = _worker(vault, repository, None)

    outcomes = worker.run_pending("diagnose")

    assert [(o.state, o.error) for o in outcomes] == [("released", "provider_not_ready")]
    job = repository.post_attempt_jobs(attempt_id=result.attempt_id)[0]
    assert job["state"] == "queued" and job["attempt_count"] == 0
    assert diagnosis_status(repository, result.attempt_id)["status"] == "pending"


def test_busy_database_is_retried_with_backoff(monkeypatch):
    worker = PostAttemptWorker(autostart=False)
    monkeypatch.setattr("learnloop_sidecar.post_attempt_worker.BUSY_BACKOFF_SECONDS", 0.0)
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise sqlite3.OperationalError("database is locked")
        return "ok"

    assert worker._with_busy_retry(flaky) == "ok"
    assert attempts["n"] == 3

    def broken():
        raise sqlite3.OperationalError("no such table: x")

    with pytest.raises(sqlite3.OperationalError):
        worker._with_busy_retry(broken)


def test_worker_thread_drains_in_order_and_records_receipts(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    first = submit(vault, repository, client, when=at(20))
    second = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(21))
    worker = _worker(vault, repository, client, autostart=True)
    try:
        worker.notify()
        remaining, _waited = worker.wait_for(
            lambda: [
                job["attempt_id"]
                for job in repository.post_attempt_jobs(kind="diagnose", states=("queued", "leased"))
            ],
            timeout=30,
        )
    finally:
        worker.shutdown()
    assert remaining == []
    first_diag = repository.latest_attempt_diagnosis(first.attempt_id)
    second_diag = repository.latest_attempt_diagnosis(second.attempt_id)
    assert diagnosis_status(repository, first.attempt_id)["status"] == DONE
    assert (first_diag["created_at"], first_diag["id"]) < (second_diag["created_at"], second_diag["id"])
    with repository.connection() as connection:
        owners = {
            row[0]
            for row in connection.execute(
                "SELECT owner_id FROM model_call_receipts WHERE owner_kind = 'attempt_diagnosis'"
            )
        }
    # The thread's model calls recorded receipts (its context carries the observer).
    assert {first.attempt_id, second.attempt_id} <= owners


def test_wait_for_returns_immediately_when_the_worker_is_not_running(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    submit(vault, repository, ReviewFakeClient())
    worker = _worker(vault, repository, ReviewFakeClient())
    started = time.monotonic()
    remaining, waited = worker.wait_for(lambda: ["pending"], timeout=5)
    assert remaining == ["pending"] and waited == 0.0
    assert time.monotonic() - started < 1.0


def test_notify_never_starts_threads_when_autostart_is_off(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    worker = _worker(vault, repository, ReviewFakeClient())
    worker.notify()
    assert worker.running is False
