"""Small synthetic journey for the Tauri-facing durable ingest surface."""

from __future__ import annotations

import threading

from learnloop.db.repositories import Repository
from learnloop.content.pipeline.runner import JobSpec
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams
from learnloop_sidecar.handlers.ingest import (
    SourceOutlineInput,
    StartImportBatchInput,
    get_source_library,
    get_source_outline,
    start_import_batch,
)
from learnloop.content.pipeline.jobs import DurableIngestJobs
from tests.helpers import create_basic_vault


def test_synthetic_markdown_import_reaches_ready_library_and_outline(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    source = vault_root / "synthetic-linear-algebra.md"
    source.write_text(
        """
# Eigenvectors

An eigenvector is a nonzero vector whose direction is preserved by a linear map.

# Diagonalization

A matrix is diagonalizable when it has a basis of eigenvectors.
""".strip(),
        encoding="utf-8",
    )

    ctx = SidecarContext()
    ctx.load(vault_root, maintenance=False)
    # Drive the same durable host synchronously so the test has no timing
    # assumptions while retaining the sidecar/Tauri DTO boundary.
    ctx.ingest_jobs.bind(ctx.repository, vault_root, background=False)

    batch = start_import_batch(
        ctx,
        StartImportBatchInput(sources=[str(source)]),
    )
    assert batch["status"] == "completed"
    assert [job["jobType"] for job in batch["jobs"]] == ["import"]
    assert batch["jobs"][0]["phase"] == "extracted"

    library = get_source_library(ctx, EmptyParams())
    assert len(library["sources"]) == 1
    card = library["sources"][0]
    assert card["readiness"] == "ready"
    assert card["unitCount"] >= 1
    assert card["blockCount"] >= 2

    outline = get_source_outline(
        ctx,
        SourceOutlineInput(extraction_ref=card["sourceId"]),
    )
    assert outline["extractionId"]
    assert len(outline["units"]) >= 1


class _ObservedEvent:
    def __init__(self) -> None:
        self._event = threading.Event()
        self.wait_started = threading.Event()

    def set(self) -> None:
        self._event.set()

    def clear(self) -> None:
        self._event.clear()

    def wait(self, timeout=None):
        self.wait_started.set()
        return self._event.wait(timeout)


def test_background_host_wakes_without_waiting_for_poll_timeout(tmp_path):
    jobs = DurableIngestJobs()
    observed = _ObservedEvent()
    jobs._work_available = observed
    jobs.bind(
        Repository(tmp_path / "state.sqlite"),
        tmp_path,
        poll_interval_seconds=30,
        background=True,
    )
    runner = jobs._require_runner()
    first_completed = threading.Event()
    second_completed = threading.Event()

    def probe(ctx):
        if ctx.payload["ordinal"] == 1:
            first_completed.set()
        else:
            second_completed.set()
        return {"ordinal": ctx.payload["ordinal"]}

    runner.handlers["latency_probe"] = probe
    try:
        runner.enqueue_batch(
            "latency_probe",
            [JobSpec("latency_probe", {"ordinal": 1})],
        )
        jobs._ensure_worker()
        assert first_completed.wait(1)
        assert observed.wait_started.wait(1)

        # The worker is now inside a 30-second idle wait. Enqueue notification
        # must wake it immediately rather than relying on that timeout.
        runner.enqueue_batch(
            "latency_probe",
            [JobSpec("latency_probe", {"ordinal": 2})],
        )
        jobs._ensure_worker()
        assert second_completed.wait(1)
    finally:
        jobs.shutdown()
