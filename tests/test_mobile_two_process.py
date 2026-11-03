"""G6b: the desktop and the host, two real processes on one fresh vault (durability lane).

Production pragmas and WAL. The child runs the real host, its two secondary workers and a fake
grader; the parent is the primary desktop sidecar. They submit, read and sync at the same time,
with a leased job beside them, and nothing is lost or run twice.
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path
import threading
import traceback

import pytest

pytestmark = pytest.mark.durability

pytest.importorskip("starlette")

ITEMS = [f"pi_two_process_{index}" for index in range(8)]


def _host_process(root: str, token: str, device_id: str, sessions: list[str], pipe) -> None:
    try:
        import learnloop_sidecar.handlers.practice as practice
        from starlette.testclient import TestClient
        from learnloop_mobile.host import create_app
        from tests.mobile_host_helpers import CountingGrader, Phone, config_for, ReadyRuntime

        grader = CountingGrader()
        practice.ready_grading_provider = lambda vault, override=None: ("fake", ReadyRuntime(), grader)
        app = create_app(config_for(Path(root)))
        with TestClient(app, base_url="https://desktop.tail.ts.net") as client:
            phone = Phone(client, {"token": token, "device_id": device_id})
            pipe.send(("started",))
            while True:
                command = pipe.recv()
                if command == "stop":
                    break
                kind, payload = command
                if kind == "start":
                    pipe.send(("session", phone.start()))
                elif kind == "submit":
                    session_id, submission_id, item = payload
                    response = phone.submit(session_id, submission_id, item=item)
                    # A real interleaving, read as the phone reads: the queue beside its own submit.
                    phone.rpc("get_session", {"sessionId": session_id})
                    pipe.send(("submitted", response.status_code, response.json()))
                elif kind == "workers":
                    runtime = app.state.host.runtime
                    pipe.send(("workers", runtime.rpc_worker.context.secondary, runtime.job_worker.context.secondary,
                               grader.grades))
        pipe.send(("stopped",))
    except BaseException:
        pipe.send(("error", traceback.format_exc()))
    finally:
        pipe.close()


def _receive(pipe, timeout: float = 120):
    assert pipe.poll(timeout), "the host process did not reply"
    result = pipe.recv()
    assert result[0] != "error", result[1]
    return result


def test_the_desktop_and_the_host_coexist_with_no_lost_writes(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    import learnloop_sidecar.handlers  # noqa: F401
    from tests.helpers import add_followup_item
    from tests.mobile_host_helpers import pair, rows, seeded_vault

    paths, repository = seeded_vault(tmp_path / "vault", fresh=True)
    for item in ITEMS:
        add_followup_item(paths.root, item)
        repository.upsert_practice_item_state(
            item, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True,
        )
    device = pair(repository)

    # A leased job of the desktop's, older than anything the host does: never run twice.
    runner = IngestRunner(repository, vault_root=paths.root, worker_id="desktop")
    runner.enqueue_batch("legacy_ingest", [JobSpec("fake")])
    lease = repository.claim_next_ingest_job(
        worker_id="desktop", now_iso="2099-01-01T00:00:00Z", lease_cutoff_iso="2098-12-31T23:58:00Z",
    )
    assert lease is not None

    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(
        target=_host_process, args=(str(paths.root), device["token"], device["device_id"], [], child)
    )
    process.start()
    child.close()
    desktop = SidecarContext()
    stop_sync = threading.Event()
    sync_errors: list[BaseException] = []
    try:
        assert _receive(parent) == ("started",)
        parent.send(("start", None))
        session = _receive(parent)[1]
        sid = session["sessionId"]

        def keep_syncing() -> None:
            # The desktop's content sync, interleaved with the phone's attempts (PR-2).
            vault = load_vault(paths.root)
            try:
                while not stop_sync.is_set():
                    sync_vault_state(vault, repository)
            except BaseException as error:  # noqa: BLE001 - reported on the test's thread
                sync_errors.append(error)

        syncer = threading.Thread(target=keep_syncing)
        syncer.start()
        # The primary's reads and its token, while the host writes.
        desktop.load(paths.root, maintenance=False)
        codes = []
        for index, item in enumerate(ITEMS):
            parent.send(("submit", (sid, f"sub{index}", item)))
            spec = METHOD_REGISTRY["get_session"]
            read = spec.handler(desktop, spec.params_model.model_validate({"sessionId": sid}))
            assert read["sessionId"] == sid
            repository.bump_queue_revision()
            reply = _receive(parent)
            codes.append(reply[1])
        stop_sync.set()
        syncer.join(timeout=60)
        assert sync_errors == []
        assert codes == [200] * len(ITEMS), codes

        attempts = rows(repository, "SELECT submission_id, entry_surface, practice_item_id FROM practice_attempts")
        assert sorted(row["submission_id"] for row in attempts) == sorted(f"sub{index}" for index in range(len(ITEMS)))
        assert {row["entry_surface"] for row in attempts} == {"phone_practice"}
        # PR-2: every attempt's scheduling fields survived the sync beside it.
        for item in ITEMS:
            state = repository.practice_item_state(item)
            assert state.last_attempt_at != "2026-05-16T12:00:00Z", item
        jobs = rows(repository, "SELECT state, boot_attempts FROM mobile_jobs")
        assert jobs == [{"state": "completed", "boot_attempts": 0}] * len(ITEMS)
        parent.send(("workers", None))
        reply = _receive(parent)
        assert reply[1:3] == (True, True)
        assert reply[3] == len(ITEMS)  # one provider call each
        # The desktop's leased job was left alone.
        assert repository.claim_next_ingest_job(
            worker_id="host-would-steal", now_iso="2099-01-01T00:00:30Z", lease_cutoff_iso="2098-12-31T23:58:00Z",
        ) is None
        parent.send("stop")
        assert _receive(parent) == ("stopped",)
        process.join(timeout=30)
        assert process.exitcode == 0
    finally:
        stop_sync.set()
        desktop.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)
        parent.close()
