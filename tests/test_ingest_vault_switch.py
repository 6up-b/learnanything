"""A vault switch moves the ingest host's loops to the new vault (ledger D-46).

``SidecarContext.load`` with another vault binds the ingest host to a new runner. The drain loop
that was running keeps going (an enqueue on the new vault sees it alive and starts no other), so
it must take its runner from the host each turn, and the previous vault's runner must stop: no
further claim there, and its job in flight fenced at its next write, as at a refusal
(``IngestRunner.halt``). Nothing is joined on the request thread that switched. No model call.
"""

from __future__ import annotations

import sqlite3
import threading
import time

from learnloop.content.pipeline.runner import JobSpec
from learnloop_sidecar.context import SidecarContext

from tests.helpers import create_basic_vault


def _statuses(paths) -> list[str]:
    connection = sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)
    try:
        return [row[0] for row in connection.execute("SELECT status FROM ingest_jobs ORDER BY created_at, id")]
    finally:
        connection.close()


def _eventually(predicate, seconds: float = 10.0) -> bool:
    """Waits for the runner's own write after its handler returns (the handler cannot signal it)."""

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def test_a_vault_switch_drains_the_new_vault_and_claims_nothing_more_in_the_old(tmp_path):
    old = create_basic_vault(tmp_path / "old")
    new = create_basic_vault(tmp_path / "new")
    context = SidecarContext()
    context.load(old.root, maintenance=False)
    try:
        host = context.ingest_jobs
        ran: list[str] = []
        old_started, old_release, new_ran = threading.Event(), threading.Event(), threading.Event()

        def old_handler(job):
            ran.append("old")
            old_started.set()
            old_release.wait(10)
            return {}

        old_runner = host._runner
        old_runner.handlers["fake"] = old_handler
        old_runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake")])
        host._ensure_worker()
        assert old_started.wait(10)
        drain_thread = host._worker_thread

        context.load(new.root, maintenance=False)
        # The switch returned with the old vault's job still inside its call: it joined nothing.
        assert drain_thread.is_alive() and not old_release.is_set()

        def new_handler(job):
            ran.append("new")
            new_ran.set()
            return {}

        host._runner.handlers["fake"] = new_handler
        host._runner.enqueue_batch("import", [JobSpec("fake")])
        host._ensure_worker()  # what every enqueue door does; the drain thread is still alive
        old_release.set()

        assert new_ran.wait(10)
        assert _eventually(lambda: _statuses(new) == ["completed"])
        # The old vault's second job was never claimed, and the one in flight wrote no outcome.
        assert ran == ["old", "new"]
        assert _statuses(old) == ["running", "queued"]
    finally:
        context.close()
