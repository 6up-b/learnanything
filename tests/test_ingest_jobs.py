"""Durable single-source ingest wrapper (spec §6.2).

These replace the old in-memory/subprocess IngestJobManager tests: the wrapper now
enqueues into the durable queue and reads job state from it. Side effects are
stubbed via RunnerServices so no provider/LLM runs; the wrapper is driven
synchronously (background=False) so there are no threads or sleeps.
"""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit
from learnloop.services.ingest_runner import FetchedBytes, JobSpec, RunnerServices
from learnloop_sidecar.ingest_jobs import ActiveIngestJobError, DurableIngestJobs, IngestJobManager


class _FakeResult:
    codex_calls = 1

    def as_dict(self) -> dict:
        return {
            "proposal_id": "patch_test",
            "source_note_id": "note_test",
            "auto_applied_count": 1,
            "review_required_count": 2,
            "invalid_count": 0,
        }


def _stub_import_services(run_legacy) -> RunnerServices:
    """Stub the import stage's fetch/extract seam (the v2-lite wrapper extracts
    once before synthesis) so no network/marker runs. Synthesis stays stubbed."""

    def fetch(source, category, ctx):
        return FetchedBytes(
            raw_bytes=b"eigenvectors and eigenvalues",
            content_type="text/plain",
            original_uri=source,
            retrieved_at="2026-07-13T12:00:00Z",
        )

    def extract(fetched, category, ctx):
        block = DocumentBlock.build(span_id="s1", block_type="Text", text="An eigenvector of A.", ordinal=1)
        unit = DocumentUnit(unit_id="u1", label="Doc", ordinal=1, semantic_hash="sha256:x", span_ids=["s1"])
        return DocumentIR(extractor="text", extractor_version="1", blocks=[block], units=[unit])

    return RunnerServices(run_legacy_ingest=run_legacy, fetch=fetch, extract=extract)


def _bind(tmp_path, run_legacy) -> DurableIngestJobs:
    jobs = DurableIngestJobs()
    jobs.bind(
        Repository(tmp_path / "state.sqlite"),
        tmp_path,
        services=_stub_import_services(run_legacy),
        background=False,
    )
    return jobs


def test_manager_alias_is_durable():
    assert IngestJobManager is DurableIngestJobs


def test_durable_ingest_job_completes(tmp_path):
    def run_legacy(*, vault_root, source, subject_id, mode, progress, clock, **_):
        progress("authoring", {"current_window": 2, "total_windows": 3})
        return _FakeResult()

    jobs = _bind(tmp_path, run_legacy)
    started = jobs.start(tmp_path, "notes.md", "linear-algebra", "canonical")

    finished = jobs.get(started["id"])
    assert finished["status"] == "completed"
    assert finished["result"]["proposal_id"] == "patch_test"
    assert jobs.needs_reload(started["id"]) is True
    jobs.mark_reloaded(started["id"])
    assert jobs.needs_reload(started["id"]) is False


def test_job_failure_is_recorded(tmp_path):
    def run_legacy(*, vault_root, source, subject_id, mode, progress, clock, **_):
        raise RuntimeError("network unavailable")

    jobs = _bind(tmp_path, run_legacy)
    started = jobs.start(tmp_path, "https://example.invalid", "linear-algebra", "canonical")

    finished = jobs.get(started["id"])
    assert finished["status"] == "failed"
    assert finished["error"]["message"] == "network unavailable"


def _enqueue_queued_job(jobs: DurableIngestJobs, source: str) -> str:
    """Enqueue a legacy job and leave it queued (no drain) for guard/cancel tests."""

    batch_id = jobs._runner.enqueue_batch(
        "legacy_ingest",
        [JobSpec("legacy_ingest", {"source": source, "subject_id": "linear-algebra", "mode": "canonical"})],
    )
    return jobs._runner.repo.ingest_jobs_for_batch(batch_id)[0]["id"]


def test_only_one_ingest_can_write_a_vault_at_once(tmp_path):
    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)
    first_id = _enqueue_queued_job(jobs, "notes.md")

    with pytest.raises(ActiveIngestJobError) as excinfo:
        jobs.start(tmp_path, "other.md", "linear-algebra", "canonical")
    assert excinfo.value.job_id == first_id


def test_cancelled_job_reaches_terminal_state(tmp_path):
    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)
    job_id = _enqueue_queued_job(jobs, "notes.md")

    cancelled = jobs.cancel(job_id)
    assert cancelled["status"] == "cancelled"


def test_list_returns_recent_legacy_jobs(tmp_path):
    def run_legacy(*, vault_root, source, subject_id, mode, progress, clock, **_):
        return _FakeResult()

    jobs = _bind(tmp_path, run_legacy)
    jobs.start(tmp_path, "a.md", "linear-algebra", "canonical")
    jobs.start(tmp_path, "b.md", "linear-algebra", "canonical")

    listed = jobs.list()
    assert {entry["source"] for entry in listed} == {"a.md", "b.md"}
    assert all(entry["status"] == "completed" for entry in listed)
