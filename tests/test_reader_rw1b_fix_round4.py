"""RW1b fix round 4 (docs/reviews/reader-rw1b-codex-review.md), after Codex's
verify of round 3 reopened F16 with four interleavings through the real drain.

* landing serializes with binding changes: the binding read, the commitment
  mapping and the completion run in one write transaction, so a revert,
  rebind or revival lands wholly before or wholly after it;
* a revert after completion reconciles: a completed request another capture
  still holds is rebound and its commitment mapping moves to that capture;
* a request a revert cancelled while it ran discards its result on landing;
* a revival compares the row's effective instructions (its bound
  annotation's learner text), so a legacy row keyed before instructions were
  part of the key is never revived by a capture asking something else.

Each interleaving runs the interfering write at a seam of the landing
(``RR._stopped``, ``Repository.get_reader_request``, the model call). The
write runs right there when the database would let another writer commit at
that point, and otherwise right after the landing commits (the probe is a
``BEGIN IMMEDIATE`` with no busy wait). No timing, no sleeps. Every model is
a fake.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop.reader import reader_capture as RC
from learnloop.reader import reader_intent as RI
from learnloop.reader import reader_requests as RR
from tests.test_reader_guidance import _setup
from tests.test_reader_requests import _FakePresetClient

SELECTION = {"nodes": [{"span_id": "s1", "quote": "The singular"}]}
GEOMETRY = "emphasize the geometry"


def _capture(repo, key: str, text: str = GEOMETRY) -> dict:
    return RC.invoke_preset(repo, preset="help_me_remember", source_id="src1", revision_id="rev1",
                            extraction_id="ext1", client_idempotency_key=key, raw_selection=SELECTION,
                            learner_text=text, subject_id="s1")


def _requests(repo) -> list[dict]:
    return repo.reader_requests_for_source("src1")


def _commitment_mappings(repo) -> list[str]:
    return [str(p["target_ref"]) for p in repo.mapping_proposals() if p["target_kind"] == "commitment"]


def _writable_now(repo) -> bool:
    """Whether another writer could commit at this point: no transaction
    holds the write lock. Never waits."""

    probe = sqlite3.connect(repo.sqlite_path, timeout=0, isolation_level=None)
    try:
        probe.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError:
        return False
    else:
        probe.execute("ROLLBACK")
        return True
    finally:
        probe.close()


class _Interleave:
    """Run ``action`` once: at the first seam where another writer could
    commit, else as soon as the landing has committed (``finish``)."""

    def __init__(self, repo, action: Callable[[], Any]) -> None:
        self.repo = repo
        self.action = action
        self.ran_at_seam = False
        self.deferred = False
        self.done = False

    def fire(self) -> None:
        if self.done or self.deferred:
            return
        if _writable_now(self.repo):
            self.done = self.ran_at_seam = True
            self.action()
        else:
            self.deferred = True

    def finish(self) -> None:
        if not self.done:
            self.done = True
            self.action()


class _Client(_FakePresetClient):
    """A fake model whose first call runs ``during`` (the slow model call,
    outside any transaction)."""

    def __init__(self, during: Callable[[], Any] | None = None) -> None:
        super().__init__()
        self.during = during
        self.returned = False

    def run_reader_preset_synthesis(self, context):
        if self.during is not None and not self.calls:
            self.during()
        result = super().run_reader_preset_synthesis(context)
        self.returned = True
        return result


def _assert_serves(repo, request_id: str, live: dict, reverted: dict) -> dict:
    """The request ends bound to the live capture, its commitment has exactly
    one mapping and the reverted capture's stopped commitment has none."""

    row = repo.get_reader_request(request_id)
    assert row["status"] == "complete"
    assert (row["annotation_id"], row["commitment_id"]) == (live["annotation_id"], live["commitment_id"])
    assert C.resolve_disposition(repo, live["commitment_id"]) != "stopped"
    assert C.resolve_disposition(repo, reverted["commitment_id"]) == "stopped"
    mappings = _commitment_mappings(repo)
    assert mappings.count(live["commitment_id"]) == 1
    assert reverted["commitment_id"] not in mappings
    return row


def _shared(repo) -> tuple[dict, dict, dict]:
    first = _capture(repo, "cap-a")
    RC.drain_outbox(repo)
    second = _capture(repo, "cap-b")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    assert request["annotation_id"] == first["annotation_id"]
    return first, second, request


# -- (a), (b): a revert of the bound capture of shared work, during landing -------------------------------


def test_a_revert_after_the_binding_read_still_maps_the_holder(tmp_path, monkeypatch):
    """(a) Landing read A's binding; reverting A rebinds the request to B;
    landing then found its saved A commitment stopped and mapped nothing."""

    _vault, repo = _setup(tmp_path)
    first, second, request = _shared(repo)
    step = _Interleave(repo, lambda: RI.revert_capture(repo, annotation_id=first["annotation_id"]))
    real = RR._stopped

    def stopped(repository, commitment_id):
        step.fire()
        return real(repository, commitment_id)

    monkeypatch.setattr(RR, "_stopped", stopped)
    assert RR.drain_requests(repo)["completed"] == [request["id"]]
    assert step.deferred or step.ran_at_seam  # the seam was reached
    step.finish()
    _assert_serves(repo, request["id"], second, first)


def test_b_a_revert_after_the_stopped_check_moves_the_mapping(tmp_path, monkeypatch):
    """(b) Reverting A right after landing's stopped-check mapped the
    proposal onto stopped A while the request was bound to B."""

    _vault, repo = _setup(tmp_path)
    first, second, request = _shared(repo)
    step = _Interleave(repo, lambda: RI.revert_capture(repo, annotation_id=first["annotation_id"]))
    real = RR._stopped

    def stopped(repository, commitment_id):
        result = real(repository, commitment_id)
        step.fire()
        return result

    monkeypatch.setattr(RR, "_stopped", stopped)
    assert RR.drain_requests(repo)["completed"] == [request["id"]]
    assert step.deferred or step.ran_at_seam  # the seam was reached
    step.finish()
    _assert_serves(repo, request["id"], second, first)


# -- (c): a revival during landing ------------------------------------------------------------------------


def test_c_a_revival_during_landing_ends_mapped_to_the_reviving_capture(tmp_path, monkeypatch):
    """(c) A is reverted while its synthesis runs (the request is flagged).
    B revives it between landing's binding read and its artifact writes.
    It used to complete with no mapping for B."""

    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    captured: dict = {}

    def revive() -> None:
        captured["second"] = _capture(repo, "cap-b")
        RC.drain_outbox(repo)

    step = _Interleave(repo, revive)
    client = _Client(during=lambda: RI.revert_capture(repo, annotation_id=first["annotation_id"]))
    real = Repository.get_reader_request

    def get_reader_request(self, request_id):
        row = real(self, request_id)
        if client.returned:
            step.fire()
        return row

    monkeypatch.setattr(Repository, "get_reader_request", get_reader_request)
    synthesize = RR.model_synthesis(client, source_sets=())
    RR.drain_requests(repo, synthesize=synthesize)
    assert step.deferred or step.ran_at_seam  # the seam was reached
    step.finish()
    # Whatever the revival left runnable runs now.
    RR.drain_requests(repo, synthesize=synthesize)
    (only,) = _requests(repo)
    assert only["id"] == request["id"]
    _assert_serves(repo, request["id"], captured["second"], first)
    assert {call.learner_text for call in client.calls} == {GEOMETRY}


# -- (d): a legacy row (no instructions in its key) ---------------------------------------------------------


def _legacy_capture(repo, monkeypatch, key: str, text: str) -> dict:
    """A capture converted the way rows were keyed before round 3: no
    instructions in the request key."""

    real = RR.request_key
    monkeypatch.setattr(RR, "request_key", lambda **kwargs: real(**{**kwargs, "instructions": ""}))
    try:
        receipt = _capture(repo, key, text)
        RC.drain_outbox(repo)
    finally:
        monkeypatch.setattr(RR, "request_key", real)
    return receipt


def _unhashed_key(row: dict) -> str:
    return RR.request_key(revision_id=row["revision_id"], window=json.loads(row["window_json"]),
                          preset=row["preset"], provider=row["provider"], model=row["model"],
                          config_hash=row["config_hash"], inventory_profile=row["inventory_profile"])


def test_d_a_no_note_capture_never_revives_a_legacy_request_asking_something_else(tmp_path, monkeypatch):
    """(d) A running request keyed without instructions ("matrix algebra") is
    reverted, then a no-note capture with the same key revived it: it landed
    on the new capture with the old instructions."""

    _vault, repo = _setup(tmp_path)
    first = _legacy_capture(repo, monkeypatch, "cap-a", "matrix algebra")
    (legacy,) = _requests(repo)
    assert legacy["request_key"] == _unhashed_key(legacy)
    captured: dict = {}

    def revert_then_capture() -> None:
        RI.revert_capture(repo, annotation_id=first["annotation_id"])
        captured["second"] = _capture(repo, "cap-b", "")
        RC.drain_outbox(repo)

    client = _Client(during=revert_then_capture)
    synthesize = RR.model_synthesis(client, source_sets=())
    RR.drain_requests(repo, synthesize=synthesize)
    RR.drain_requests(repo, synthesize=synthesize)
    second = captured["second"]

    rows = {r["id"]: r for r in _requests(repo)}
    # The incompatible request kept its cancel flag; its result was discarded.
    stale = rows[legacy["id"]]
    assert stale["status"] == "cancelled" and stale["cancel_requested"] == 1
    assert stale["annotation_id"] == first["annotation_id"]
    assert stale["request_key"] == RR.request_key(
        revision_id=legacy["revision_id"], window=json.loads(legacy["window_json"]), preset=legacy["preset"],
        provider=legacy["provider"], model=legacy["model"], config_hash=legacy["config_hash"],
        inventory_profile=legacy["inventory_profile"], instructions="matrix algebra")
    # B got its own request, under the exact no-note key, and the model was
    # given B's (empty) instructions for it.
    (own,) = [r for r in rows.values() if r["id"] != legacy["id"]]
    assert own["request_key"] == legacy["request_key"]
    _assert_serves(repo, own["id"], second, first)
    assert [call.learner_text for call in client.calls] == ["matrix algebra", ""]
    assert len(repo.source_objects_for_source("src1")) == 1


def test_d_a_legacy_rekey_that_collides_takes_a_key_no_enqueue_computes(tmp_path, monkeypatch):
    _vault, repo = _setup(tmp_path)
    first = _legacy_capture(repo, monkeypatch, "cap-a", "matrix algebra")
    (legacy,) = _requests(repo)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    # A capture after round 3 asking the same thing holds the hashed key.
    third = _capture(repo, "cap-c", "matrix algebra")
    RC.drain_outbox(repo)
    hashed = [r for r in _requests(repo) if r["id"] != legacy["id"]]
    assert len(hashed) == 1 and hashed[0]["annotation_id"] == third["annotation_id"]
    second = _capture(repo, "cap-b", "")
    RC.drain_outbox(repo)
    rows = {r["id"]: r for r in _requests(repo)}
    assert len(rows) == 3
    assert rows[legacy["id"]]["status"] == "cancelled"
    assert rows[legacy["id"]]["request_key"] == f"{hashed[0]['request_key']}#legacy:{legacy['id']}"
    assert rows[hashed[0]["id"]]["request_key"] == hashed[0]["request_key"]
    (fresh,) = [r for r in rows.values() if r["annotation_id"] == second["annotation_id"]]
    assert fresh["status"] == "queued" and fresh["request_key"] == legacy["request_key"]


def test_d_a_compatible_no_note_revival_keeps_its_exact_key(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a", "")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    assert request["request_key"] == _unhashed_key(request)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    second = _capture(repo, "cap-b", "")
    RC.drain_outbox(repo)
    (revived,) = _requests(repo)
    assert revived["id"] == request["id"] and revived["request_key"] == request["request_key"]
    assert revived["status"] == "queued" and revived["annotation_id"] == second["annotation_id"]
    RR.drain_requests(repo)
    _assert_serves(repo, request["id"], second, first)


# -- ruling 2: a revert after completion reconciles -------------------------------------------------------


def test_a_revert_of_a_completed_shared_request_moves_its_commitment_mapping(tmp_path):
    _vault, repo = _setup(tmp_path)
    first, second, request = _shared(repo)
    assert RR.drain_requests(repo)["completed"] == [request["id"]]
    (before,) = [p for p in repo.mapping_proposals() if p["target_kind"] == "commitment"]
    assert before["target_ref"] == first["commitment_id"]
    result_before = repo.get_reader_request(request["id"])["result_json"]
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    row = _assert_serves(repo, request["id"], second, first)
    (after,) = [p for p in repo.mapping_proposals() if p["target_kind"] == "commitment"]
    assert after["id"] == before["id"]  # repointed, not duplicated
    assert row["result_json"] == result_before
    # A second revert changes nothing.
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    _assert_serves(repo, request["id"], second, first)


def test_a_revert_of_a_completed_request_nobody_else_holds_leaves_it(tmp_path):
    _vault, repo = _setup(tmp_path)
    first = _capture(repo, "cap-a")
    RC.drain_outbox(repo)
    (request,) = _requests(repo)
    RR.drain_requests(repo)
    RI.revert_capture(repo, annotation_id=first["annotation_id"])
    row = repo.get_reader_request(request["id"])
    assert row["status"] == "complete" and row["annotation_id"] == first["annotation_id"]


# -- base behaviour kept --------------------------------------------------------------------------------


def test_an_explicit_cancel_of_a_running_request_still_lands(tmp_path):
    """Only a request a revert cancelled discards its result: an explicit
    cancel while it runs (no capture reverted) lands as before."""

    _vault, repo = _setup(tmp_path)
    enqueued = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                                  span_id="s1", preset="worked_example")

    def synthesize(repository, request, clock):
        RR.cancel_request(repository, request_id=request["id"])
        return RR._deterministic_synthesis(repository, request, clock)

    assert RR.drain_requests(repo, synthesize=synthesize)["completed"] == [enqueued["request_id"]]
    row = repo.get_reader_request(enqueued["request_id"])
    assert row["status"] == "complete" and row["cancel_requested"] == 1
    assert json.loads(row["result_json"])["proposals"]


def test_the_landing_writes_the_drains_result(tmp_path):
    """The landing completes the request with the row the drain used to write."""

    _vault, repo = _setup(tmp_path)
    enqueued = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                                  span_id="s1", preset="worked_example")
    returned: dict = {}

    def synthesize(repository, request, clock):
        returned["result"] = RR._deterministic_synthesis(repository, request, clock)
        return returned["result"]

    RR.drain_requests(repo, synthesize=synthesize)
    row = repo.get_reader_request(enqueued["request_id"])
    assert json.loads(row["result_json"]) == returned["result"]
    assert row["actual_input_tokens"] == returned["result"]["tokens_in"]
    assert row["actual_output_tokens"] == returned["result"]["tokens_out"]
    assert row["lease_owner"] is None and row["completed_at"] is not None
