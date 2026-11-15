"""A desktop sidecar already bound to a vault stops serving it when the vault becomes unservable: a reload refused
below the oldest supported tag (ADR-019), or an activation journal another process leaves beside its database.
Handlers (``require_vault``), the post-attempt worker (its supplier) and background jobs (the loaded-vault
provider's admission) are refused until a load of the vault succeeds, and the runners bound at load (ingest, exam
grading, approach-map builds, request-started jobs) stop at the refusal, without a join. No model call.
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from pathlib import Path

import pytest

from learnloop.activation_journal import journal_path
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION, OLDEST_SUPPORTED, SUCCESSOR_CHAIN
from learnloop.content.pipeline.runner import JobSpec
from learnloop.db.scopes import JobOwnershipLost
from learnloop.version_floor import BelowOldestSupported
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.server import _handle

from tests.helpers import create_basic_vault

BELOW = SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(OLDEST_SUPPORTED) - 1]


def _retag(root: Path, tag: str) -> None:
    path = root / "learnloop.toml"
    text, count = re.subn(r'algorithm_version = "[^"]+"', f'algorithm_version = "{tag}"', path.read_text("utf-8"),
                          count=1)
    assert count == 1
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def bound(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    context = SidecarContext()
    context.load(paths.root, maintenance=False)
    assert context.app_snapshot()["vault"]
    yield paths, context
    context.close()


def _rpc(context: SidecarContext, method: str) -> dict:
    return _handle(context, {"jsonrpc": "2.0", "id": 1, "method": method, "params": {}})


def _assert_refused(context: SidecarContext, code: str) -> None:
    generation = context.loaded_vault.generation()
    with pytest.raises(SidecarError) as refused:
        context.app_snapshot()
    assert refused.value.code == code
    assert _rpc(context, "load_vault")["error"]["data"]["code"] == code
    # The worker gets no vault, and a background job's admission of its snapshot fails.
    assert context._worker_target() is None
    assert not context.loaded_vault.admit(generation)


def test_a_reload_refused_below_the_floor_stops_serving_until_a_load_succeeds(bound):
    paths, context = bound
    _retag(paths.root, BELOW)

    response = _rpc(context, "reload_vault")
    assert response["error"]["data"]["code"] == "vault_below_oldest_supported"
    assert OLDEST_SUPPORTED in response["error"]["message"]
    _assert_refused(context, "vault_below_oldest_supported")

    # Still refused while the file stays below the floor.
    with pytest.raises(BelowOldestSupported):
        context.reload(maintenance=False)
    _assert_refused(context, "vault_below_oldest_supported")

    _retag(paths.root, LATEST_ALGORITHM_VERSION)
    assert "result" in _rpc(context, "reload_vault")
    assert context.app_snapshot()["vault"] and context._worker_target() is not None


def test_a_journal_that_appears_while_bound_stops_serving_until_a_load_succeeds(bound):
    paths, context = bound
    journal = journal_path(paths.sqlite_path)
    # Another process's upgrade, published or still running: this context's vault is the predecessor's.
    journal.write_text(json.dumps({"predecessor": OLDEST_SUPPORTED, "target": LATEST_ALGORITHM_VERSION}),
                       encoding="utf-8")
    _assert_refused(context, "vault_upgrade_unfinished")

    # The other process finishes: the journal goes, but the vault this context holds is still the old one.
    journal.unlink()
    _assert_refused(context, "vault_upgrade_unfinished")

    # A watched file change is the moment a load is tried; it succeeds, and the vault is served again.
    result = context.refresh_vault_files(["learnloop.toml"], expected_root=paths.root)
    assert result["mode"] == "full" and result["snapshot"]["vault"]
    assert context.app_snapshot()["vault"] and context._worker_target() is not None


# -- the bound runners stop at the refusal (they were bound with the repository at load) --------------------------


def _journal(paths) -> Path:
    journal = journal_path(paths.sqlite_path)
    journal.write_text(json.dumps({"predecessor": OLDEST_SUPPORTED, "target": LATEST_ALGORITHM_VERSION}),
                       encoding="utf-8")
    return journal


def _rows(paths, table: str) -> list[tuple]:
    # Read past the refusal: the context and ``Repository.attach`` refuse the journalled vault.
    connection = sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)
    try:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    finally:
        connection.close()


def test_a_refusal_stops_the_bound_runners_and_a_load_binds_them_again(bound):
    paths, context = bound
    epoch = context.background_jobs.epoch()
    journal = _journal(paths)
    assert not context.serving()

    # None of them holds the refused vault or admits work on it.
    with pytest.raises(RuntimeError):
        _ = context.ingest_jobs.repository
    assert context.map_builds.admit(paths.sqlite_path) is None
    assert context.background_jobs.closed_since(epoch)
    # The ingest RPCs that reach only the host are refused like every other handler.
    assert _rpc(context, "get_ingest_jobs")["error"]["data"]["code"] == "vault_upgrade_unfinished"

    journal.unlink()
    context.refresh_vault_files(["learnloop.toml"], expected_root=paths.root)
    assert context.ingest_jobs.repository.sqlite_path == context.repository.sqlite_path
    assert context.map_builds.admit(paths.sqlite_path) is not None
    assert not context.background_jobs.closed_since(context.background_jobs.epoch())


def test_an_exam_grading_waiting_for_a_slot_at_the_refusal_never_starts(bound):
    paths, context = bound
    hold, held, holding = threading.Event(), [], threading.Semaphore(0)
    for item in ("i1", "i2"):  # both grading slots busy
        context.exam_grading.submit("s1", item, lambda item=item: (held.append(item), holding.release(), hold.wait(10)))
    # Both hold their slots before the third is submitted: thread start order does not decide who gets a slot.
    assert holding.acquire(timeout=10) and holding.acquire(timeout=10)
    waiting = []
    context.exam_grading.submit("s1", "i3", lambda: waiting.append("ran"))
    _journal(paths)
    assert not context.serving()
    hold.set()
    context.exam_grading.wait_for_session("s1")
    assert sorted(held) == ["i1", "i2"] and waiting == []


def test_an_ingest_job_in_flight_at_the_refusal_writes_nothing_after_it(bound, monkeypatch):
    paths, context = bound
    host = context.ingest_jobs
    runner = host._runner
    runner.heartbeat_interval_seconds = 0.01
    started, release, outcome = threading.Event(), threading.Event(), {}

    def handler(job):
        outcome.setdefault("threads", []).append(threading.current_thread())
        started.set()
        release.wait(10)
        try:
            job.repo.update_ingest_job_payload(job.job["id"], {"late": True})
        except JobOwnershipLost:
            outcome["fenced"] = outcome.get("fenced", 0) + 1
            raise
        outcome["wrote"] = outcome.get("wrote", 0) + 1
        return {}

    beats, renewing = threading.Event(), threading.Condition()
    in_flight = [0]
    real_beat = runner.repo.heartbeat_ingest_job

    def beat(*args, **kwargs):
        with renewing:
            in_flight[0] += 1
        beats.set()
        try:
            return real_beat(*args, **kwargs)
        finally:
            with renewing:
                in_flight[0] -= 1
                renewing.notify_all()

    monkeypatch.setattr(runner.repo, "heartbeat_ingest_job", beat)
    runner.handlers["fake"] = handler
    runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake")])
    host._ensure_worker()
    assert started.wait(10)
    _journal(paths)
    assert not context.serving()
    # The refusal (on this thread, as on a request's) returned with the job still inside its call: it joined nothing.
    assert outcome["threads"][0].is_alive() and not release.is_set()
    # A renewal that began before the refusal still commits; what is compared starts once it has.
    with renewing:
        assert renewing.wait_for(lambda: in_flight[0] == 0, timeout=10)
        beats.clear()
    before = (_rows(paths, "ingest_jobs"), _rows(paths, "ingest_batches"))
    # A renewal would come within a few of its 10 ms periods; none comes once the vault is refused.
    assert not beats.wait(0.5)
    release.set()
    for thread in outcome["threads"]:
        thread.join(10)
        assert not thread.is_alive()
    # The job in flight was fenced at its write, the queued one was never claimed, and nothing else was written.
    assert outcome == {"threads": outcome["threads"], "fenced": 1}
    assert (_rows(paths, "ingest_jobs"), _rows(paths, "ingest_batches")) == before
