"""G6a: a real secondary process, real WAL, no desktop startup machinery."""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
import multiprocessing
from pathlib import Path
import sys
import traceback

import pytest


def _host_process(root: str, token: str, pipe) -> None:
    try:
        from starlette.testclient import TestClient
        from learnloop_mobile.config import MobileConfig
        from learnloop_mobile.host import create_app

        config = MobileConfig(
            enabled=True, vault=Path(root), hostname="desktop.test.ts.net",
            owner_login="owner@example.com",
        )
        with TestClient(create_app(config), base_url="https://desktop.test.ts.net") as client:
            assert "learnloop_sidecar.context" not in sys.modules
            assert "learnloop.vault.loader" not in sys.modules
            pipe.send(("started", client.get("/healthz").status_code))
            while True:
                command = pipe.recv()
                if command == "stop":
                    break
                response = client.post(
                    "/api/v1/capture",
                    headers={
                        "Tailscale-User-Login": "owner@example.com",
                        "Authorization": f"Bearer {token}",
                    },
                    json={
                        "client_capture_id": f"01ARZ3NDEKTSV4RRFFQ69G5F{command:02d}",
                        "kind": "text", "text": f"Reference {command}",
                        "captured_at": "2026-10-11T12:00:00Z",
                    },
                )
                pipe.send(("capture", response.status_code, response.json()))
        pipe.send(("stopped",))
    except BaseException:
        pipe.send(("error", traceback.format_exc()))
    finally:
        pipe.close()


def _receive(pipe):
    assert pipe.poll(60), "Mobile child did not reply within 60 seconds"
    result = pipe.recv()
    assert result[0] != "error", result
    return result


def _snapshot(database: Path) -> dict:
    from learnloop.db.connection import connect

    with closing(connect(database, read_only=True)) as connection:
        tables = [
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {
            table: sorted(
                [tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')],
                key=repr,
            )
            for table in tables
        }


@pytest.mark.durability
def test_capture_host_coexists_without_primary_startup_work(tmp_path):
    from learnloop.capture import create_pairing, exchange_pairing, list_captures
    from learnloop.clock import FrozenClock
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.content.synthesis.synthesis_manifests import build_manifest, persist_manifest
    from learnloop.db.connection import connect
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository.attach(paths.sqlite_path)
    old = FrozenClock(datetime(2020, 1, 1, tzinfo=UTC))
    manifest = persist_manifest(
        repository, build_manifest(load_vault(paths.root), source_set_id="ss1"),
    )
    synchronous_run = repository.insert_synthesis_run(
        manifest_id=manifest, mode="bootstrap", clock=old,
    )
    runner = IngestRunner(repository, vault_root=paths.root, worker_id="desktop", clock=old)
    runner.enqueue_batch("legacy_ingest", [JobSpec("fake")])
    lease = repository.claim_next_ingest_job(
        worker_id="desktop", now_iso="2099-01-01T00:00:00Z",
        lease_cutoff_iso="2098-12-31T23:58:00Z",
    )
    assert lease is not None
    pairing = create_pairing(repository, label="test", scope="capture")
    device = exchange_pairing(repository, secret=pairing["secret"], device_label="test")
    before = _snapshot(paths.sqlite_path)
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=_host_process, args=(str(paths.root), device["token"], child))
    process.start()
    child.close()
    try:
        assert _receive(parent) == ("started", 200)
        assert _snapshot(paths.sqlite_path) == before
        revision = repository.queue_revision()["revision"]
        for index in range(10):
            # Each primary write is in flight alongside a secondary HTTP receipt.
            parent.send(index)
            repository.bump_queue_revision()
            assert _receive(parent)[1] == 201
        assert repository.queue_revision()["revision"] == revision + 10
        assert len(list_captures(repository)) == 10
        assert repository.synthesis_run(synchronous_run)["status"] == "created"
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        parent.send("stop")
        assert _receive(parent) == ("stopped",)
        process.join(timeout=10)
        assert process.exitcode == 0
        after = _snapshot(paths.sqlite_path)
        for table, rows in before.items():
            if table not in {
                "capture_inbox", "capture_routes", "mobile_devices",
                "mobile_request_log", "queue_state",
            }:
                assert after[table] == rows, table
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)
        parent.close()
