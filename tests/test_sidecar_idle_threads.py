"""An idle desktop sidecar's background threads sleep, and stop when it closes
(test-thread-leak).

In the landing full suite one xdist worker collected ~800 threads that tests
had started and never stopped, some of them polling their vaults, until the
machine's load average passed 400. These pin the production half of the fix:

* a loaded sidecar's background owners (the reading sweep, the post-attempt
  worker's slots) block on their wake events while there is no work: over a
  quiet window they use no CPU;
* ``SidecarContext.close`` (the ``shutdown`` RPC and EOF) stops every one of
  these idle owners within its bounded join (jobs in flight, the Reader's and
  the gaps slot's, are cancelled too: tests/test_sidecar_close_cancels_jobs.py);
* the source service's lease heartbeat ends as soon as its last lease is
  dropped, not a whole beat later.

Per-thread CPU is read from ``/proc/self/task/<tid>/stat`` (Linux).
"""
from __future__ import annotations

import os
import threading
import time

import pytest

from tests.helpers import create_basic_vault
from tests.recap_fixtures import call, context

pytestmark = pytest.mark.skipif(not os.path.isdir("/proc/self/task"), reason="per-thread CPU is read from /proc")

# A quiet window this long with less CPU than this is "idle" (a test bound:
# a thread busy-polling a vault burns a large fraction of a core in it).
WINDOW_SECONDS = 1.0
IDLE_CPU_SECONDS = 0.05


def _cpu_seconds(threads: list[threading.Thread]) -> float:
    total = 0.0
    for thread in threads:
        try:
            with open(f"/proc/self/task/{thread.native_id}/stat", encoding="ascii") as handle:
                fields = handle.read().rsplit(")", 1)[1].split()
        except OSError:  # the thread ended
            continue
        total += (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
    return total


def _background(ctx) -> list[threading.Thread]:
    threads = [ctx.ingest_jobs._reading_sweep_thread, *ctx.post_attempt_worker._threads.values()]
    return [thread for thread in threads if thread is not None and thread.is_alive()]


def _goes_quiet(threads: list[threading.Thread], attempts: int = 10) -> list[float]:
    """CPU used over successive quiet windows, until one is idle. A thread that
    starts with a pass of work goes quiet after it; a busy-polling one never."""

    used = []
    for _ in range(attempts):
        before = _cpu_seconds(threads)
        time.sleep(WINDOW_SECONDS)
        used.append(round(_cpu_seconds(threads) - before, 3))
        if used[-1] < IDLE_CPU_SECONDS:
            break
    return used


def test_an_idle_sidecars_background_threads_sleep_and_stop_on_close(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = context(paths.root)
    ctx.post_attempt_worker.notify()  # its three slots start and find nothing queued
    threads = _background(ctx)
    names = sorted(thread.name for thread in threads)
    assert names == ["learnloop-post-attempt-diagnose", "learnloop-post-attempt-embed",
                     "learnloop-post-attempt-gaps", "learnloop-reading-sweep"]

    used = _goes_quiet(threads)
    assert used[-1] < IDLE_CPU_SECONDS, f"idle background threads kept using CPU: {used}"

    started = time.monotonic()
    ctx.close()
    assert [thread.name for thread in threads if thread.is_alive()] == []
    assert time.monotonic() - started < 5.0


def test_the_shutdown_rpc_stops_the_idle_background_owners(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = context(paths.root)
    ctx.post_attempt_worker.notify()
    threads = _background(ctx)
    assert len(threads) == 4

    assert call(ctx, "shutdown", {}) == {"ok": True}

    assert ctx.shutdown_requested
    assert [thread.name for thread in threads if thread.is_alive()] == []


def test_the_sidecars_eof_closes_its_context(monkeypatch):
    import io

    from learnloop_sidecar import server

    closed = []

    class Recording(server.SidecarContext):
        def close(self) -> None:
            closed.append(self)
            super().close()

    monkeypatch.setattr(server, "SidecarContext", Recording)
    server.serve(io.StringIO(""), io.StringIO())
    assert len(closed) == 1


def test_the_lease_heartbeat_ends_when_its_last_lease_is_dropped(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.source_retrieval import service_spend as SS

    repository = Repository(create_basic_vault(tmp_path / "vault").sqlite_path)
    keeper = SS._Leases()
    keeper.hold(repository, "first")
    keeper.hold(repository, "second")
    thread = keeper._thread
    assert thread is not None and thread.is_alive()

    keeper.drop(repository, "first")
    thread.join(0.5)
    assert thread.is_alive()  # a lease is still held: it keeps beating

    keeper.drop(repository, "second")
    thread.join(5.0)  # well inside one beat (HEARTBEAT_SECONDS)
    assert not thread.is_alive() and keeper._thread is None
    assert SS.HEARTBEAT_SECONDS > 5.0
