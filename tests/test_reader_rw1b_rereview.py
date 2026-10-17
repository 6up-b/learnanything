"""RW1b's Codex re-review fixes (docs/reviews/reader-rw1b-codex-review.md, re-review).

* F14 a capture "change" reverted before its outbox row converted never
      enqueues synthesis later: the conversion reads the revert inside the
      write transaction that enqueues, and the revert cancels inside one;
* F15 synthesis shared by captures of the same passage and preset is
      cancelled only when no retained capture still holds it, and a later
      capture revives a cancelled request instead of reusing it dead.

Every model is a fake.
"""

from __future__ import annotations

import threading

from learnloop.reader import reader_capture as RC
from learnloop.reader import reader_intent as RI
from learnloop.reader import reader_requests as RR
from tests.test_reader_guidance import _setup

SELECTION = {"nodes": [{"span_id": "s1", "quote": "The singular"}]}


def _capture(repo, key: str, preset: str = "help_me_remember") -> dict:
    return RC.invoke_preset(repo, preset=preset, source_id="src1", revision_id="rev1", extraction_id="ext1",
                            client_idempotency_key=key, raw_selection=SELECTION, learner_text="remember this",
                            subject_id="s1")


def _requests(repo) -> list[dict]:
    return repo.reader_requests_for_source("src1")


# -- F14: a reverted capture never enqueues later ----------------------------------------------------


def test_f14_a_capture_reverted_before_its_drain_enqueues_nothing(tmp_path):
    _vault, repo = _setup(tmp_path)
    receipt = _capture(repo, "cap-1")
    # The drain RPC failed before converting: the outbox row is still pending.
    assert repo.get_capture_outbox(receipt["outbox_id"])["state"] == "pending"
    RI.revert_capture(repo, annotation_id=receipt["annotation_id"])
    RC.drain_outbox(repo)
    assert [r for r in _requests(repo) if r["status"] not in ("cancelled", "obsolete")] == []
    assert repo.get_capture_outbox(receipt["outbox_id"])["state"] == "done"


def test_f14_a_failed_conversion_retried_after_the_revert_enqueues_nothing(tmp_path, monkeypatch):
    _vault, repo = _setup(tmp_path)
    receipt = _capture(repo, "cap-1")
    real = RR.enqueue_request

    def boom(*_args, **_kwargs):
        raise RuntimeError("drain crashed")

    monkeypatch.setattr(RR, "enqueue_request", boom)
    RC.drain_outbox(repo)
    assert repo.get_capture_outbox(receipt["outbox_id"])["state"] == "failed"
    RI.revert_capture(repo, annotation_id=receipt["annotation_id"])
    monkeypatch.setattr(RR, "enqueue_request", real)
    RC.retry_outbox(repo, outbox_id=receipt["outbox_id"])
    RC.drain_outbox(repo)
    assert [r for r in _requests(repo) if r["status"] not in ("cancelled", "obsolete")] == []


def test_f14_a_revert_racing_a_drain_waits_for_it_and_cancels_what_it_enqueued(tmp_path, monkeypatch):
    _vault, repo = _setup(tmp_path)
    receipt = _capture(repo, "cap-1")
    real = RR.neighborhood
    reverted: dict = {}
    thread: list[threading.Thread] = []

    def revert() -> None:
        reverted["result"] = RI.revert_capture(repo, annotation_id=receipt["annotation_id"])

    def racing_neighborhood(*args, **kwargs):
        # The conversion has read that the capture stands; a revert starts now.
        if not thread:
            thread.append(threading.Thread(target=revert))
            thread[0].start()
            thread[0].join(1.0)
        return real(*args, **kwargs)

    monkeypatch.setattr(RR, "neighborhood", racing_neighborhood)
    RC.drain_outbox(repo)
    thread[0].join(10)
    assert not thread[0].is_alive()
    (request,) = _requests(repo)
    assert reverted["result"]["request_id"] == request["id"]
    assert request["status"] == "cancelled"


# -- F15: shared synthesis -----------------------------------------------------------------------------


def _two_sharing(repo) -> tuple[dict, dict, dict]:
    first = _capture(repo, "cap-1")
    RC.drain_outbox(repo)
    second = _capture(repo, "cap-2")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    return first, second, request


def test_f15_reverting_the_original_capture_keeps_work_another_capture_holds(tmp_path):
    _vault, repo = _setup(tmp_path)
    first, second, request = _two_sharing(repo)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    assert repo.get_reader_request(request["id"])["status"] == "queued"
    reverted = RI.revert_capture(repo, annotation_id=second["annotation_id"])
    assert reverted["request_id"] == request["id"]
    assert repo.get_reader_request(request["id"])["status"] == "cancelled"


def test_f15_reverting_the_sharing_capture_keeps_the_original_and_cancels_last(tmp_path):
    _vault, repo = _setup(tmp_path)
    first, second, request = _two_sharing(repo)
    RI.revert_capture(repo, annotation_id=second["annotation_id"])
    assert repo.get_reader_request(request["id"])["status"] == "queued"
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    assert repo.get_reader_request(request["id"])["status"] == "cancelled"


def test_f15_a_later_capture_revives_cancelled_work(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-1")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    assert repo.get_reader_request(request["id"])["status"] == "cancelled"
    _capture(repo, "cap-2")
    RC.drain_outbox(repo)
    (revived,) = _requests(repo)
    assert revived["id"] == request["id"]
    assert revived["status"] == "queued" and revived["cancel_requested"] == 0
    result = RR.drain_requests(repo)
    assert result["completed"] == [request["id"]]


def test_f15_a_later_capture_keeps_running_work_its_revert_flagged(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-1")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    with repo.connection() as connection:
        connection.execute("UPDATE reader_background_requests SET status = 'running' WHERE id = ?",
                           (request["id"],))
        connection.commit()
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    assert repo.get_reader_request(request["id"])["cancel_requested"] == 1
    _capture(repo, "cap-2")
    RC.drain_outbox(repo)
    row = repo.get_reader_request(request["id"])
    assert row["status"] == "running" and row["cancel_requested"] == 0
