"""RW1b's fixes after Codex's final verify (docs/reviews/reader-rw1b-codex-review.md,
fix round 3).

* F14 a revert asks whether a revert tombstone *stands* (the predicate the
      outbox conversion reads, which honours an undo), so a revert after an
      undone one writes a new tombstone and the capture converts to no work;
* F16 a capture's instructions are part of its synthesis request's identity:
      captures asking different things never share or revive one request, a
      revival rebinds the request to the reviving capture, and a stopped
      commitment never receives a mapping.

Every model is a fake.
"""

from __future__ import annotations

from learnloop.reader import annotations as ANN
from learnloop.reader import reader_capture as RC
from learnloop.reader import reader_intent as RI
from learnloop.reader import reader_requests as RR
from tests.test_reader_guidance import _setup
from tests.test_reader_requests import _FakePresetClient

SELECTION = {"nodes": [{"span_id": "s1", "quote": "The singular"}]}


def _capture(repo, key: str, text: str = "remember this", preset: str = "help_me_remember") -> dict:
    return RC.invoke_preset(repo, preset=preset, source_id="src1", revision_id="rev1", extraction_id="ext1",
                            client_idempotency_key=key, raw_selection=SELECTION, learner_text=text,
                            subject_id="s1")


def _requests(repo) -> list[dict]:
    return repo.reader_requests_for_source("src1")


def _live(repo) -> list[dict]:
    return [r for r in _requests(repo) if r["status"] not in ("cancelled", "obsolete")]


def _revert_tombstones(repo, annotation_id: str) -> list[str]:
    with repo.connection() as connection:
        return [str(row[0]) for row in connection.execute(
            "SELECT id FROM source_annotation_events WHERE annotation_id = ? AND event_type = 'delete_intent' "
            "AND json_extract(payload_json, '$.reason') = ? ORDER BY created_at, id",
            (annotation_id, RI.REVERT_REASON),
        )]


def _restore(repo, annotation_id: str) -> None:
    ANN.restore_annotation(repo, annotation_id=annotation_id,
                           delete_event_id=_revert_tombstones(repo, annotation_id)[-1])


def _commitment_mappings(repo) -> list[str]:
    return [str(p["target_ref"]) for p in repo.mapping_proposals() if p["target_kind"] == "commitment"]


# -- F14: revert reads the standing tombstone --------------------------------------------------------


def test_f14_a_revert_after_an_undone_revert_converts_to_no_work(tmp_path):
    """Codex's repro: capture, revert, restore naming that delete, revert again, drain."""

    _vault, repo = _setup(tmp_path)
    receipt = _capture(repo, "cap-1")
    annotation_id = receipt["annotation_id"]
    RI.revert_capture(repo, annotation_id=annotation_id)
    _restore(repo, annotation_id)
    assert not repo.capture_reverted(annotation_id, reason=RI.REVERT_REASON)
    RI.revert_capture(repo, annotation_id=annotation_id)
    assert len(_revert_tombstones(repo, annotation_id)) == 2
    assert repo.capture_reverted(annotation_id, reason=RI.REVERT_REASON)
    RC.drain_outbox(repo)
    assert _live(repo) == []
    assert repo.get_capture_outbox(receipt["outbox_id"])["state"] == "done"


def test_f14_revert_restore_revert_restore_converts(tmp_path):
    _vault, repo = _setup(tmp_path)
    receipt = _capture(repo, "cap-1")
    annotation_id = receipt["annotation_id"]
    for _ in range(2):
        RI.revert_capture(repo, annotation_id=annotation_id)
        _restore(repo, annotation_id)
    assert not repo.capture_reverted(annotation_id, reason=RI.REVERT_REASON)
    RC.drain_outbox(repo)
    (request,) = _live(repo)
    assert request["status"] == "queued" and request["cancel_requested"] == 0
    # The first revert retired the capture's commitment, and a restore does
    # not bring it back: the stopped commitment gets no mapping (F16).
    RR.drain_requests(repo)
    assert receipt["commitment_id"] not in _commitment_mappings(repo)


def test_f14_revert_restore_revert_then_a_retried_conversion_enqueues_nothing(tmp_path, monkeypatch):
    _vault, repo = _setup(tmp_path)
    receipt = _capture(repo, "cap-1")
    annotation_id = receipt["annotation_id"]
    real = RR.enqueue_request

    def boom(*_args, **_kwargs):
        raise RuntimeError("drain crashed")

    monkeypatch.setattr(RR, "enqueue_request", boom)
    RC.drain_outbox(repo)
    assert repo.get_capture_outbox(receipt["outbox_id"])["state"] == "failed"
    monkeypatch.setattr(RR, "enqueue_request", real)
    RI.revert_capture(repo, annotation_id=annotation_id)
    _restore(repo, annotation_id)
    RI.revert_capture(repo, annotation_id=annotation_id)
    RC.retry_outbox(repo, outbox_id=receipt["outbox_id"])
    RC.drain_outbox(repo)
    assert _live(repo) == []


# -- F16: instructions are part of a request's identity ------------------------------------------------


def test_f16_captures_with_different_instructions_never_share_or_revive(tmp_path):
    """Codex's repro: A asks for the matrix algebra, is drained and reverted;
    B selects the same passage and preset asking for the geometry."""

    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a", "emphasize the matrix algebra")
    RC.drain_outbox(repo)
    (request_a,) = _requests(repo)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    second = _capture(repo, "cap-b", "emphasize the geometry")
    RC.drain_outbox(repo)
    client = _FakePresetClient()
    RR.drain_requests(repo, synthesize=RR.model_synthesis(client, source_sets=()))

    requests = {r["id"]: r for r in _requests(repo)}
    assert len(requests) == 2
    assert requests[request_a["id"]]["status"] == "cancelled"
    assert requests[request_a["id"]]["annotation_id"] == first["annotation_id"]
    (request_b,) = [r for r in requests.values() if r["id"] != request_a["id"]]
    assert request_b["status"] == "complete"
    assert request_b["annotation_id"] == second["annotation_id"]
    assert request_b["commitment_id"] == second["commitment_id"]
    assert [call.learner_text for call in client.calls] == ["emphasize the geometry"]
    assert _commitment_mappings(repo) == [second["commitment_id"]]
    assert first["commitment_id"] not in _commitment_mappings(repo)


def test_f16_a_same_instruction_revival_rebinds_to_the_reviving_capture(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a", "emphasize the geometry")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    # The same instructions, spaced differently: the same request.
    second = _capture(repo, "cap-b", "  emphasize   the geometry ")
    RC.drain_outbox(repo)
    (revived,) = _requests(repo)
    assert revived["id"] == request["id"]
    assert revived["status"] == "queued" and revived["cancel_requested"] == 0
    assert revived["annotation_id"] == second["annotation_id"]
    assert revived["commitment_id"] == second["commitment_id"]
    client = _FakePresetClient()
    assert RR.drain_requests(repo, synthesize=RR.model_synthesis(client, source_sets=()))["completed"] == [request["id"]]
    assert [call.learner_text for call in client.calls] == ["  emphasize   the geometry "]
    assert _commitment_mappings(repo) == [second["commitment_id"]]


def test_f16_a_running_revival_lands_on_the_reviving_capture(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a", "emphasize the geometry")
    RC.drain_outbox(repo)
    claimed = repo.claim_next_reader_request(worker_id="w", now_iso="2026-10-17T00:00:00Z",
                                             lease_expires_at="2999-01-01T00:00:00Z",
                                             lease_cutoff_iso="2026-10-17T00:00:00Z")
    assert claimed is not None and claimed["annotation_id"] == first["annotation_id"]
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    second = _capture(repo, "cap-b", "emphasize the geometry")
    RC.drain_outbox(repo)
    row = repo.get_reader_request(claimed["id"])
    assert row["status"] == "running" and row["cancel_requested"] == 0
    # The worker lands with the row it claimed (bound to A): the result maps
    # to the capture the request serves now.
    RR._deterministic_synthesis(repo, claimed, None)
    assert _commitment_mappings(repo) == [second["commitment_id"]]


def test_f16_reverting_the_bound_capture_of_shared_work_rebinds_it(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a", "emphasize the geometry")
    RC.drain_outbox(repo)
    second = _capture(repo, "cap-b", "emphasize the geometry")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    assert request["annotation_id"] == first["annotation_id"]
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    row = repo.get_reader_request(request["id"])
    assert row["status"] == "queued"
    assert (row["annotation_id"], row["commitment_id"]) == (second["annotation_id"], second["commitment_id"])
    RR.drain_requests(repo)
    assert _commitment_mappings(repo) == [second["commitment_id"]]


def test_f16_a_key_without_instructions_is_unchanged():
    window = {"span_ids": ["s1"], "selected_span_ids": ["s1"], "selected_text": "x"}
    base = RR.request_key(revision_id="rev1", window=window, preset="p", provider="stub", model="m",
                          config_hash="")
    assert RR.request_key(revision_id="rev1", window=window, preset="p", provider="stub", model="m",
                          config_hash="", instructions="  \n ") == base
    assert RR.request_key(revision_id="rev1", window=window, preset="p", provider="stub", model="m",
                          config_hash="", instructions="emphasize the geometry") != base
