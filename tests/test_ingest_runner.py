from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit
from learnloop.services.ingest_runner import (
    IngestRunner,
    JobContext,
    JobSpec,
    RunnerServices,
    WaitingForInput,
    derive_batch_status,
)


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


# --------------------------------------------------------------------------
# Named verification rows (§14)
# --------------------------------------------------------------------------


def test_queue_survives_restart(tmp_path):
    calls: dict[str, int] = {}
    runner = _runner(tmp_path, handlers={"fake": _ok_handler(calls)})
    batch_id = runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake")])

    # "Restart": a brand-new runner over a brand-new Repository on the same file.
    reopened = _runner(tmp_path, handlers={"fake": _ok_handler(calls)}, clock=_clock(1))
    assert reopened.repo.get_ingest_batch(batch_id)["status"] == "queued"
    ran = reopened.drain()

    assert ran == 2
    assert reopened.repo.get_ingest_batch(batch_id)["status"] == "completed"
    assert all(job["status"] == "completed" for job in reopened.repo.ingest_jobs_for_batch(batch_id))


def test_lease_expiry_marks_interrupted(tmp_path):
    runner = _runner(tmp_path, handlers={"fake": _ok_handler({})}, clock=_clock())
    batch_id = runner.enqueue_batch("import", [JobSpec("fake")])

    # Simulate a crash mid-run: claim the job (sets running + heartbeat) but never finish it.
    claimed = runner.repo.claim_next_ingest_job(
        worker_id="w1", now_iso="2026-07-13T12:00:00Z", lease_cutoff_iso="2026-07-13T11:58:00Z"
    )
    assert claimed["status"] == "running"

    # A fresh worker starts well past the lease TTL and recovers the stale lease.
    restarted = _runner(tmp_path, handlers={"fake": _ok_handler({})}, clock=_clock(600))
    recovered = restarted.recover_stale_leases()

    assert recovered == [claimed["id"]]
    job = restarted.repo.get_ingest_job(claimed["id"])
    assert job["status"] == "failed"
    assert job["error"]["code"] == "interrupted"
    assert job["worker_id"] is None


def test_dependency_failure_blocks_downstream(tmp_path):
    def boom(ctx: JobContext) -> dict:
        raise RuntimeError("stage failed")

    calls: dict[str, int] = {}
    runner = _runner(tmp_path, handlers={"boom": boom, "fake": _ok_handler(calls)})
    batch_id = runner.enqueue_batch(
        "import",
        [JobSpec("boom"), JobSpec("fake", depends_on=(0,)), JobSpec("fake", depends_on=(1,))],
    )
    runner.drain()

    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
    assert jobs[0]["status"] == "failed"
    assert jobs[1]["status"] == "blocked"
    assert jobs[2]["status"] == "blocked"  # transitively blocked
    assert calls == {}  # neither downstream job ran
    assert runner.repo.get_ingest_batch(batch_id)["status"] == "failed"


def test_waiting_for_input_holds_no_lease(tmp_path):
    def waiter(ctx: JobContext) -> dict:
        raise WaitingForInput({"kind": "unit_selection"}, message="Choose units")

    calls: dict[str, int] = {}
    runner = _runner(tmp_path, handlers={"wait": waiter, "fake": _ok_handler(calls)})
    batch_id = runner.enqueue_batch("import", [JobSpec("wait"), JobSpec("fake")])
    runner.drain()

    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
    waiting_job, other = jobs[0], jobs[1]
    assert waiting_job["status"] == "waiting_for_input"
    assert waiting_job["worker_id"] is None  # holds NO lease
    assert waiting_job["heartbeat_at"] is None
    assert waiting_job["result"]["waiting_for_input"]["kind"] == "unit_selection"
    # The independent job still drained rather than being blocked behind the wait.
    assert other["status"] == "completed"


def test_sidecar_and_cli_never_drain_concurrently(tmp_path):
    calls: dict[str, int] = {}
    sidecar = _runner(tmp_path, worker_id="sidecar", handlers={"fake": _ok_handler(calls)})
    batch_id = sidecar.enqueue_batch("import", [JobSpec("fake")])

    # The sidecar claims the job and holds a live lease (in-progress).
    claimed = sidecar.repo.claim_next_ingest_job(
        worker_id="sidecar", now_iso="2026-07-13T12:00:00Z", lease_cutoff_iso="2026-07-13T11:58:00Z"
    )
    assert claimed is not None

    # A CLI worker sharing the same lease row cannot drain while the lease is live.
    cli = _runner(tmp_path, worker_id="cli", handlers={"fake": _ok_handler(calls)})
    assert cli.run_next() is False
    assert cli.drain() == 0


def test_cancel_resume_runs_only_unfinished_jobs(tmp_path):
    calls: dict[str, int] = {}
    runner = _runner(tmp_path, handlers={"fake": _ok_handler(calls)})
    batch_id = runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake"), JobSpec("fake")])

    # Run only the first job, then cancel the rest of the batch.
    runner.drain(max_jobs=1)
    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
    first_completed = jobs[0]["id"]
    assert calls[first_completed] == 1

    runner.cancel_batch(batch_id)
    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
    assert jobs[0]["status"] == "completed"  # partial success preserved
    assert jobs[1]["status"] == "cancelled"
    assert jobs[2]["status"] == "cancelled"

    runner.resume_batch(batch_id)
    runner.drain()

    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
    assert all(job["status"] == "completed" for job in jobs)
    # The already-completed job did NOT run a second time; only the two unfinished did.
    assert calls[first_completed] == 1
    assert sum(calls.values()) == 3


# --------------------------------------------------------------------------
# Checkpoint ladder, usage accumulation, partial success
# --------------------------------------------------------------------------


def test_checkpoint_ladder_and_window_counts_are_recorded(tmp_path):
    def laddered(ctx: JobContext) -> dict:
        ctx.report("acquired", current_window=1, total_windows=3)
        ctx.report("registered", current_window=2, total_windows=3)
        ctx.report("extracted", current_window=3, total_windows=3)
        return {}

    runner = _runner(tmp_path, handlers={"fake": laddered})
    batch_id = runner.enqueue_batch("import", [JobSpec("fake")])
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["phase"] == "extracted"
    assert job["current_window"] == 3
    assert job["total_windows"] == 3


def test_retry_usage_accumulates_across_attempts(tmp_path):
    attempts: list[int] = []

    def flaky(ctx: JobContext) -> dict:
        attempts.append(1)
        ctx.record_usage({"input_tokens": 10, "output_tokens": 5})
        if len(attempts) == 1:
            raise RuntimeError("transient")
        return {}

    runner = _runner(tmp_path, handlers={"fake": flaky})
    batch_id = runner.enqueue_batch("import", [JobSpec("fake")])
    runner.drain()
    assert runner.repo.ingest_jobs_for_batch(batch_id)[0]["status"] == "failed"

    runner.resume_batch(batch_id)
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    assert job["attempt_count"] == 2
    # Usage is a deterministic sum over attempts — the failed attempt stays visible.
    assert job["usage"]["input_tokens"] == 20
    assert job["usage"]["output_tokens"] == 10


def test_partial_success_preserved_on_batch_failure(tmp_path):
    calls: dict[str, int] = {}

    def maybe(ctx: JobContext) -> dict:
        if ctx.job["ordinal"] == 1:
            raise RuntimeError("second job fails")
        return _ok_handler(calls)(ctx)

    runner = _runner(tmp_path, handlers={"fake": maybe})
    batch_id = runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake")])
    runner.drain()

    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["result"]["ok"] is True  # completed artifact retained
    assert jobs[1]["status"] == "failed"
    assert runner.repo.get_ingest_batch(batch_id)["status"] == "failed"


def test_batch_status_derivation():
    assert derive_batch_status([], None) == "queued"
    assert derive_batch_status([{"status": "queued"}], None) == "queued"
    assert derive_batch_status([{"status": "running"}, {"status": "queued"}], None) == "running"
    assert derive_batch_status([{"status": "completed"}, {"status": "queued"}], None) == "running"
    assert derive_batch_status([{"status": "completed"}, {"status": "completed"}], None) == "completed"
    assert derive_batch_status([{"status": "completed"}, {"status": "failed"}], None) == "failed"
    assert derive_batch_status([{"status": "completed"}, {"status": "waiting_for_input"}], None) == "waiting_for_input"


# --------------------------------------------------------------------------
# import + legacy_ingest handlers (stubbed side effects — no network/LLM/marker)
# --------------------------------------------------------------------------


def _stub_ir() -> DocumentIR:
    block = DocumentBlock.build(span_id="s1", block_type="Text", text="An eigenvector of A is a vector v.", ordinal=1, page=1)
    unit = DocumentUnit(unit_id="u1", label="Chapter 1", ordinal=1, semantic_hash="sha256:x", page_start=1, page_end=1, span_ids=["s1"])
    return DocumentIR(extractor="text", extractor_version="1", blocks=[block], units=[unit])


def _import_services():
    from learnloop.services.ingest_runner import FetchedBytes

    def fetch(source, category, ctx):
        return FetchedBytes(raw_bytes=b"eigen bytes", content_type="text/plain", original_uri=source, retrieved_at="2026-07-13T12:00:00Z")

    def extract(fetched, category, ctx):
        return _stub_ir()

    return RunnerServices(fetch=fetch, extract=extract)


def test_import_handler_registers_revision_and_extraction(tmp_path):
    runner = _runner(tmp_path, services=_import_services())
    batch_id = runner.enqueue_batch("import", [JobSpec("import", {"source": str(tmp_path / "notes.md")})])
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    result = job["result"]
    assert result["reused_revision"] is False
    assert result["unit_count"] == 1
    assert result["block_count"] == 1
    revision = runner.repo.get_source_revision(result["revision_id"])
    assert revision is not None
    run = runner.repo.get_extraction_run(result["extraction_id"])
    assert run["status"] == "completed"
    assert run["extraction_result_hash"]


def test_import_retry_reuses_revision_and_extraction(tmp_path):
    services = _import_services()
    runner = _runner(tmp_path, services=services)
    source = str(tmp_path / "notes.md")
    runner.enqueue_batch("import", [JobSpec("import", {"source": source})])
    runner.drain()

    # A second import of the identical source reuses the revision + extraction run.
    batch2 = runner.enqueue_batch("import", [JobSpec("import", {"source": source})])
    runner.drain()
    result2 = runner.repo.ingest_jobs_for_batch(batch2)[0]["result"]
    assert result2["reused_revision"] is True
    assert result2["reused_extraction"] is True

    with runner.repo.connection() as connection:
        artifacts = connection.execute("SELECT COUNT(*) AS n FROM source_artifacts").fetchone()["n"]
        revisions = connection.execute("SELECT COUNT(*) AS n FROM source_revisions").fetchone()["n"]
        runs = connection.execute("SELECT COUNT(*) AS n FROM source_extraction_runs").fetchone()["n"]
    assert (artifacts, revisions, runs) == (1, 1, 1)


def test_legacy_ingest_handler_wraps_pipeline_with_stub_client(tmp_path):
    class _FakeResult:
        codex_calls = 2

        def as_dict(self):
            return {"proposal_id": "patch_1", "auto_applied_count": 1, "review_required_count": 0}

    seen = {}

    def run_legacy(*, vault_root, source, subject_id, mode, progress, clock, **_):
        seen.update({"source": source, "subject_id": subject_id, "mode": mode})
        progress("authoring", {"current_window": 1, "total_windows": 1})
        return _FakeResult()

    runner = _runner(tmp_path, services=RunnerServices(run_legacy_ingest=run_legacy))
    batch_id = runner.enqueue_batch(
        "legacy_ingest",
        [JobSpec("legacy_ingest", {"source": "notes.md", "subject_id": "linear-algebra", "mode": "canonical"})],
    )
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    assert job["result"]["proposal_id"] == "patch_1"
    assert job["usage"]["calls"] == 2
    assert seen == {"source": "notes.md", "subject_id": "linear-algebra", "mode": "canonical"}


def test_reserved_job_types_fail_with_not_implemented_seam(tmp_path):
    # `inventory` landed in ING M4 and `bootstrap_synthesis` in ING M6;
    # `append_synthesis` remains a reserved seam for M7.
    runner = _runner(tmp_path)
    batch_id = runner.enqueue_batch("update_study_map", [JobSpec("append_synthesis", {"set_id": "s1"})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "failed"
    assert job["error"]["code"] == "not_implemented"


def test_bootstrap_synthesis_job_validates_payload(tmp_path):
    # `bootstrap_synthesis` landed in ING M6: a missing source_set_id is a
    # validation failure, not a not_implemented seam.
    runner = _runner(tmp_path)
    batch_id = runner.enqueue_batch("create_study_map", [JobSpec("bootstrap_synthesis", {})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "failed"
    assert job["error"]["code"] != "not_implemented"


def _extract_ctx(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.clock import FrozenClock
    from learnloop.services.ingest_runner import JobContext

    return JobContext(
        repo=None,  # default_extract never touches the repository
        vault_root=tmp_path,
        job={"payload": {}},
        clock=FrozenClock("2026-07-14T00:00:00Z"),
        worker_id="w-test",
    )


def test_web_import_routes_html_normalizer_not_raw_text(tmp_path):
    # Dogfood regression: a real HTML page was stored as ONE 216kB raw-HTML
    # block because default_extract fell through to the text normalizer.
    from learnloop.services.ingest_runner import FetchedBytes, default_extract

    html = (
        "<!DOCTYPE html><html><head><title>Symmetric matrices</title></head><body>"
        "<h1>Symmetric matrices</h1><p>A symmetric matrix equals its transpose.</p>"
        "<h1>Variance</h1><p>The covariance matrix is symmetric.</p>"
        "</body></html>"
    )
    fetched = FetchedBytes(
        raw_bytes=html.encode(),
        content_type="text/html",
        original_uri="https://example.org/sec-symmetric-matrices.html",
        retrieved_at="2026-07-14T00:00:00Z",
    )
    ir = default_extract(fetched, "web", _extract_ctx(tmp_path))
    assert ir.extractor == "html"
    joined = " ".join(block.text for block in ir.blocks)
    assert "symmetric matrix equals its transpose" in joined
    assert "<html" not in joined.lower() and "doctype" not in joined.lower()


def test_youtube_import_routes_caption_cues_to_time_range_ir(tmp_path):
    # Dogfood regression: caption-cue JSON was stored verbatim as one text block.
    import json as _json

    from learnloop.services.ingest_runner import FetchedBytes, default_extract

    cues = {"cues": [
        {"start": 0.48, "duration": 4.84, "text": "Singular value decomposition is one of"},
        {"start": 5.4, "duration": 3.1, "text": "the most useful matrix factorizations."},
    ]}
    fetched = FetchedBytes(
        raw_bytes=_json.dumps(cues).encode(),
        content_type=None,
        original_uri="https://youtu.be/qs1qcpemCIE",
        retrieved_at="2026-07-14T00:00:00Z",
    )
    ir = default_extract(fetched, "youtube", _extract_ctx(tmp_path))
    assert ir.extractor == "youtube"
    assert len(ir.blocks) == 2
    assert ir.blocks[0].text.startswith("Singular value decomposition")
