"""What other test files use from ``tests/test_ingest_runner.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.content.pipeline.runner import IngestRunner, JobContext


def _clock(seconds: int = 0) -> FrozenClock:
    return FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC) + timedelta(seconds=seconds))


def _repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "state.sqlite")


def _runner(tmp_path: Path, *, clock: FrozenClock | None = None, worker_id: str = "w1", handlers=None, services=None, lease_ttl_seconds: int = 120) -> IngestRunner:
    return IngestRunner(
        _repo(tmp_path),
        vault_root=tmp_path,
        worker_id=worker_id,
        clock=clock or _clock(),
        handlers=handlers,
        services=services,
        lease_ttl_seconds=lease_ttl_seconds,
    )


def _ok_handler(recorder: dict[str, int]):
    def handler(ctx: JobContext) -> dict:
        recorder[ctx.job["id"]] = recorder.get(ctx.job["id"], 0) + 1
        ctx.report("acquired")
        return {"ok": True, "job_type": ctx.job["job_type"]}

    return handler
