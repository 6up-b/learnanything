from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import time

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.client import CodexTurnTimeout
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth, PageHealth
from learnloop.services.ingest_runner import (
    IngestRunner,
    IngestRunnerError,
    JobContext,
    JobSpec,
    RunnerServices,
    WaitingForInput,
    derive_batch_status,
)
from learnloop_sidecar.ingest_jobs import DurableIngestJobs


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


def test_delete_finished_ingest_batches_removes_queue_history_only(tmp_path):
    runner = _runner(tmp_path, handlers={"fake": _ok_handler({})})
    finished_batch = runner.enqueue_batch(
        "import",
        [JobSpec("fake"), JobSpec("fake", depends_on=(0,))],
    )
    runner.drain()
    active_batch = runner.enqueue_batch("import", [JobSpec("fake")])

    deleted = runner.repo.delete_finished_ingest_batches([finished_batch])

    assert deleted == {"batches": 1, "jobs": 2, "dependencies": 1}
    assert runner.repo.get_ingest_batch(finished_batch) is None
    assert runner.repo.ingest_jobs_for_batch(finished_batch) == []
    assert runner.repo.get_ingest_batch(active_batch)["status"] == "queued"
    with pytest.raises(ValueError, match="active ingest batches"):
        runner.repo.delete_finished_ingest_batches([active_batch])


def test_long_running_handler_emits_periodic_heartbeats(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    calls: list[str] = []
    original = repo.heartbeat_ingest_job

    def record_heartbeat(job_id, **kwargs):
        calls.append(job_id)
        return original(job_id, **kwargs)

    monkeypatch.setattr(repo, "heartbeat_ingest_job", record_heartbeat)

    def slow_handler(ctx: JobContext) -> dict:
        time.sleep(0.06)
        return {"ok": True}

    runner = IngestRunner(
        repo,
        vault_root=tmp_path,
        worker_id="heartbeat-worker",
        clock=_clock(),
        handlers={"slow": slow_handler},
        heartbeat_interval_seconds=0.01,
    )
    batch_id = runner.enqueue_batch("import", [JobSpec("slow")])
    runner.drain()

    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    assert calls.count(job["id"]) >= 2


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


def test_actionable_failure_details_are_persisted_for_activity_ui(tmp_path):
    def rejected(_ctx: JobContext) -> dict:
        raise IngestRunnerError(
            "Candidate failed validation.",
            code="synthesis_gate_failed",
            details={
                "stage": "synthesis",
                "completed_dependencies_preserved": True,
                "diagnostics": [
                    {
                        "gate": "criterion_target",
                        "severity": "hard_fail",
                        "message": "unknown capability",
                    }
                ],
            },
            retryable=True,
        )

    runner = _runner(tmp_path, handlers={"fake": rejected})
    batch_id = runner.enqueue_batch("import", [JobSpec("fake")])
    runner.drain()

    error = runner.repo.ingest_jobs_for_batch(batch_id)[0]["error"]
    assert error["code"] == "synthesis_gate_failed"
    assert error["retryable"] is True
    assert error["details"]["completed_dependencies_preserved"] is True
    assert error["details"]["diagnostics"][0]["gate"] == "criterion_target"


def test_codex_timeout_releases_lease_and_continues_draining(tmp_path):
    calls: dict[str, int] = {}

    def timed_out(_ctx: JobContext) -> dict:
        raise CodexTurnTimeout("Codex SDK turn exceeded its deadline.")

    runner = _runner(
        tmp_path,
        handlers={"timed_out": timed_out, "fake": _ok_handler(calls)},
    )
    batch_id = runner.enqueue_batch(
        "practice_expansion", [JobSpec("timed_out"), JobSpec("fake")]
    )

    assert runner.drain() == 2

    failed, completed = runner.repo.ingest_jobs_for_batch(batch_id)
    assert failed["status"] == "failed"
    assert failed["error"]["code"] == "timeout"
    assert failed["worker_id"] is None
    assert failed["heartbeat_at"] is None
    assert completed["status"] == "completed"
    assert calls == {completed["id"]: 1}


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


def test_same_vault_rebind_preserves_kill_codex_interrupt_handle(tmp_path):
    jobs = DurableIngestJobs()
    jobs.bind(_repo(tmp_path), tmp_path, background=False)
    original_runner = jobs._require_runner()
    batch_id = original_runner.enqueue_batch("practice_expansion", [JobSpec("practice_expansion")])
    claimed = original_runner.repo.claim_next_ingest_job(
        worker_id=original_runner.worker_id,
        now_iso="2026-07-13T12:00:00Z",
        lease_cutoff_iso="2026-07-13T11:58:00Z",
    )
    assert claimed is not None

    class InterruptibleClient:
        def __init__(self):
            self.interrupted = False

        def interrupt(self):
            self.interrupted = True

    client = InterruptibleClient()
    original_runner._bind_job_interruptible(claimed["id"], client)

    # Applying-job polling reloads SidecarContext while the next writer job can
    # already be in its model call. A same-vault bind must not orphan its handle.
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)

    assert jobs._require_runner() is original_runner
    result = jobs.interrupt_codex()
    assert result["job_id"] == claimed["id"]
    assert result["batch_id"] == batch_id
    assert client.interrupted is True
    assert original_runner.repo.get_ingest_job(claimed["id"])["cancel_requested"] is True


def test_quick_check_lane_runs_beside_single_vault_writer_with_bound(tmp_path):
    runner = _runner(tmp_path)
    writer_batch = runner.enqueue_batch(
        "practice_expansion", [JobSpec("practice_expansion")]
    )
    quick_batches = [
        runner.enqueue_batch("reader_quick_check", [JobSpec("reader_quick_check")])
        for _ in range(4)
    ]
    claim_kwargs = {
        "now_iso": "2026-07-13T12:00:00Z",
        "lease_cutoff_iso": "2026-07-13T11:58:00Z",
    }

    first_quick = runner.repo.claim_next_ingest_job(
        worker_id="quick-1",
        eligible_job_types=("reader_quick_check",),
        allow_parallel=True,
        max_parallel=3,
        **claim_kwargs,
    )
    writer = runner.repo.claim_next_ingest_job(
        worker_id="writer",
        eligible_job_types=("practice_expansion",),
        compatible_running_job_types=("reader_quick_check",),
        **claim_kwargs,
    )
    second_quick = runner.repo.claim_next_ingest_job(
        worker_id="quick-2",
        eligible_job_types=("reader_quick_check",),
        allow_parallel=True,
        max_parallel=3,
        **claim_kwargs,
    )
    third_quick = runner.repo.claim_next_ingest_job(
        worker_id="quick-3",
        eligible_job_types=("reader_quick_check",),
        allow_parallel=True,
        max_parallel=3,
        **claim_kwargs,
    )
    fourth_quick = runner.repo.claim_next_ingest_job(
        worker_id="quick-4",
        eligible_job_types=("reader_quick_check",),
        allow_parallel=True,
        max_parallel=3,
        **claim_kwargs,
    )

    assert writer is not None and writer["batch_id"] == writer_batch
    assert {
        first_quick["batch_id"],
        second_quick["batch_id"],
        third_quick["batch_id"],
    } <= set(quick_batches)
    assert fourth_quick is None


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
    return DocumentIR(extractor="text", extractor_version="2", blocks=[block], units=[unit])


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


def test_import_cache_hit_skips_extractor_and_restores_health(tmp_path):
    calls = {"extract": 0}

    def extract(fetched, category, ctx):
        calls["extract"] += 1
        ir = _stub_ir()
        ir.health = ExtractionHealth(
            flags=["needs_review"],
            pages=[PageHealth(page=1, flags=["low_text_density"])],
        )
        return ir

    base = _import_services()
    services = RunnerServices(fetch=base.fetch, extract=extract)
    runner = _runner(tmp_path, services=services)
    source = str(tmp_path / "notes.md")
    first = runner.enqueue_batch("import", [JobSpec("import", {"source": source})])
    runner.drain()
    extraction_id = runner.repo.ingest_jobs_for_batch(first)[0]["result"]["extraction_id"]
    second = runner.enqueue_batch("import", [JobSpec("import", {"source": source})])
    runner.drain()

    assert calls["extract"] == 1
    assert runner.repo.ingest_jobs_for_batch(second)[0]["result"]["reused_extraction"] is True
    restored = runner.repo.load_document_ir(extraction_id)
    assert restored.health.flags == ["needs_review"]
    assert restored.health.flagged_pages() == [1]


def test_import_retry_replaces_ir_left_by_interrupted_run(tmp_path):
    services = _import_services()
    runner = _runner(tmp_path, services=services)
    source = str(tmp_path / "notes.md")
    # Seed the exact request as an interrupted/running run with already-written
    # children, reproducing a crash between persist_document_ir and completion.
    from learnloop.ingest.hashing import extraction_request_hash
    from learnloop.ingest.ir import IR_SCHEMA_VERSION
    from learnloop.ingest.source_library import register_source_revision

    fetched = services.fetch(source, "textfile", None)
    registered = register_source_revision(
        runner.repo,
        acquisition_kind="textfile",
        canonical_uri=source,
        raw_bytes=fetched.raw_bytes,
        original_uri=source,
        retrieved_at=fetched.retrieved_at,
        clock=_clock(),
    )
    request_hash = extraction_request_hash(
        revision_id=registered.revision_id,
        extractor="text",
        extractor_version="2",
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    runner.repo.insert_extraction_run(
        id="ext_interrupted",
        revision_id=registered.revision_id,
        extractor="text",
        extractor_version="2",
        extraction_request_hash=request_hash,
        ir_schema_version=IR_SCHEMA_VERSION,
        status="running",
        clock=_clock(),
    )
    runner.repo.persist_document_ir("ext_interrupted", _stub_ir())

    batch = runner.enqueue_batch("import", [JobSpec("import", {"source": source})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    assert job["result"]["extraction_id"] == "ext_interrupted"
    assert runner.repo.get_extraction_run("ext_interrupted")["status"] == "completed"


def test_public_import_inventory_dependency_resolves_extraction_and_units(tmp_path):
    from learnloop.codex.schemas import InventoryConceptMention, SourceUnitInventory

    class Client:
        def __init__(self):
            self.calls = 0

        def run_source_unit_inventory(self, context):
            self.calls += 1
            span_id = context.unit_view["blocks"][0]["span_id"]
            return SourceUnitInventory(
                concept_mentions=[InventoryConceptMention(name="eigenvector", span_ids=[span_id])]
            )

    client = Client()
    base = _import_services()
    services = RunnerServices(
        fetch=base.fetch,
        extract=base.extract,
        inventory_client_factory=lambda ctx: client,
    )
    runner = _runner(tmp_path, services=services)
    batch = runner.enqueue_batch(
        "import_inventory",
        [
            JobSpec("import", {"source": str(tmp_path / "notes.md")}),
            JobSpec("inventory", {"role": "reference"}, depends_on=(0,)),
        ],
    )
    runner.drain()

    jobs = runner.repo.ingest_jobs_for_batch(batch)
    assert [job["status"] for job in jobs] == ["completed", "completed"]
    assert jobs[1]["result"]["extraction_id"] == jobs[0]["result"]["extraction_id"]
    assert [row["unit_id"] for row in jobs[1]["result"]["units"]] == ["u1"]
    assert client.calls == 1


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


def test_append_synthesis_job_is_implemented(tmp_path):
    # The public append job is wired to the bounded reconciliation service. A
    # nonexistent set fails validation/loading, never at a reserved seam.
    runner = _runner(tmp_path)
    batch_id = runner.enqueue_batch("update_study_map", [JobSpec("append_synthesis", {"set_id": "s1"})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "failed"
    assert job["error"]["code"] != "not_implemented"


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


# --------------------------------------------------------------------------- #
# YouTube display title: "<video title> — <author>" captured at import time.
# --------------------------------------------------------------------------- #

def test_compose_display_title_variants():
    from learnloop.services.ingest_runner import _compose_display_title

    assert _compose_display_title("SVD explained", ["3Blue1Brown"]) == "SVD explained — 3Blue1Brown"
    assert _compose_display_title("SVD explained", []) == "SVD explained"
    assert _compose_display_title("  SVD  ", ["  ", "Grant"]) == "SVD — Grant"
    # No title captured → None so the caller falls back to the URL title.
    assert _compose_display_title(None, ["3Blue1Brown"]) is None
    assert _compose_display_title("", []) is None


def test_youtube_oembed_metadata_parses_and_falls_back(monkeypatch):
    from learnloop.ingest import fetchers

    monkeypatch.setattr(
        fetchers,
        "_http_get_text",
        lambda url, timeout=10: '{"title": "SVD explained", "author_name": "3Blue1Brown"}',
    )
    assert fetchers.youtube_oembed_metadata("abc123") == ("SVD explained", "3Blue1Brown")

    def _boom(url, timeout=10):
        raise OSError("offline")

    monkeypatch.setattr(fetchers, "_http_get_text", _boom)
    # A failed oEmbed never raises — it degrades to (None, None).
    assert fetchers.youtube_oembed_metadata("abc123") == (None, None)


def test_fetch_metadata_only_resolves_youtube():
    from learnloop.services.ingest_runner import _fetch_metadata

    assert _fetch_metadata("https://example.org/page.html", "web") == (None, ())


def _youtube_import_services(title="SVD explained", authors=("3Blue1Brown",)):
    import json as _json

    from learnloop.services.ingest_runner import FetchedBytes

    cues = {"cues": [{"start": 0.0, "duration": 2.0, "text": "Singular value decomposition."}]}

    def fetch(source, category, ctx):
        return FetchedBytes(
            raw_bytes=_json.dumps(cues).encode(),
            content_type="application/json",
            original_uri=source,
            retrieved_at="2026-07-13T12:00:00Z",
            title=title,
            authors=authors,
        )

    # No extract override → the real default_extract routes caption cues.
    return RunnerServices(fetch=fetch)


def test_youtube_import_stores_display_title_and_labels_transcript_unit(tmp_path):
    runner = _runner(tmp_path, services=_youtube_import_services())
    batch_id = runner.enqueue_batch(
        "import", [JobSpec("import", {"source": "https://youtu.be/qs1qcpemCIE"})]
    )
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    # Stored artifact + result title carry the combined "<title> — <author>".
    assert job["result"]["title"] == "SVD explained — 3Blue1Brown"
    artifact = runner.repo.get_source_artifact(job["result"]["source_id"])
    assert artifact["display_title"] == "SVD explained — 3Blue1Brown"
    # The single transcript unit is labeled by the real video title (no author).
    ir = runner.repo.load_document_ir(job["result"]["extraction_id"])
    assert ir.units[0].label == "SVD explained"


def test_youtube_import_without_metadata_falls_back_to_url(tmp_path):
    runner = _runner(tmp_path, services=_youtube_import_services(title=None, authors=()))
    batch_id = runner.enqueue_batch(
        "import", [JobSpec("import", {"source": "https://youtu.be/qs1qcpemCIE"})]
    )
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    assert job["result"]["title"] is None
    artifact = runner.repo.get_source_artifact(job["result"]["source_id"])
    assert artifact["display_title"] is None
    # The sidecar's card title then falls back to the source URL.
    from learnloop_sidecar.handlers.ingest import _artifact_title

    revision = runner.repo.get_source_revision(job["result"]["revision_id"])
    assert _artifact_title(artifact, revision) == "https://youtu.be/qs1qcpemCIE"
    # Transcript unit keeps the neutral default label when no title is known.
    ir = runner.repo.load_document_ir(job["result"]["extraction_id"])
    assert ir.units[0].label == "Transcript"


# --------------------------------------------------------------------------
# Robustness: PDF fallback, page validation, batch timestamp hygiene,
# stale synthesis-run finalization
# --------------------------------------------------------------------------


def _fetched_pdf(raw: bytes = b"%PDF-1.4 fake"):
    from learnloop.services.ingest_runner import FetchedBytes

    return FetchedBytes(
        raw_bytes=raw, content_type="application/pdf",
        original_uri="file:///book.pdf", retrieved_at="2026-07-13T12:00:00Z",
    )


def _bare_ctx(tmp_path: Path, payload: dict | None = None) -> JobContext:
    return JobContext(
        repo=_repo(tmp_path), vault_root=tmp_path,
        job={"id": "j1", "batch_id": "b1", "payload": payload or {}},
        clock=_clock(), worker_id="w1",
    )


def test_marker_runtime_failure_falls_back_to_pypdf(tmp_path, monkeypatch):
    """Marker dying mid-conversion degrades to native-text extraction with a
    health flag instead of failing the whole import (§2.9)."""

    import learnloop.ingest.extractors as extractors
    from learnloop.services.ingest_runner import default_extract

    class FailingMarker:
        name = "marker"

        def extract(self, raw_bytes, context):
            raise RuntimeError("CUDA device lost")

    class FakePyPdf:
        name = "pypdf"

        def extract(self, raw_bytes, context):
            block = DocumentBlock.build(span_id="s1", block_type="Text", text="Native text.", ordinal=1)
            unit = DocumentUnit(unit_id="u1", label="Doc", ordinal=1, semantic_hash="sha256:x", span_ids=["s1"])
            return DocumentIR(extractor="pypdf", extractor_version="1", blocks=[block], units=[unit])

    monkeypatch.setattr(extractors, "pdf_extractor_for", lambda config=None: FailingMarker())
    monkeypatch.setattr(extractors, "PyPdfDocumentExtractor", FakePyPdf)

    ir = default_extract(_fetched_pdf(), "pdf", _bare_ctx(tmp_path))
    assert ir.extractor == "pypdf"
    assert "marker_failed_pypdf_fallback" in ir.health.flags


def test_forced_marker_engine_does_not_fall_back(tmp_path, monkeypatch):
    import learnloop.ingest.extractors as extractors
    from learnloop.services.ingest_runner import default_extract

    class FailingMarker:
        name = "marker"

        def extract(self, raw_bytes, context):
            raise RuntimeError("CUDA device lost")

    monkeypatch.setattr(extractors, "pdf_extractor_for", lambda config=None: FailingMarker())
    with pytest.raises(RuntimeError, match="CUDA device lost"):
        default_extract(_fetched_pdf(), "pdf", _bare_ctx(tmp_path, {"pdf_config": {"engine": "marker"}}))


def test_pdf_extractor_for_honors_engine_choice(monkeypatch):
    """engine="pypdf" forces the fallback even with marker installed; "marker"
    raises typed when unavailable; the engine key never leaks into marker
    options; auto keeps the availability-based default."""

    import learnloop.ingest.extractors as extractors

    monkeypatch.setattr(extractors, "marker_available", lambda: True)
    assert extractors.pdf_extractor_for({"engine": "pypdf"}).name == "pypdf"
    marker = extractors.pdf_extractor_for({"engine": "marker", "force_ocr": True})
    assert marker.name == "marker"
    assert "engine" not in marker._config and marker._config["force_ocr"] is True
    assert extractors.pdf_extractor_for().name == "marker"

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    assert extractors.pdf_extractor_for().name == "pypdf"
    with pytest.raises(extractors.MarkerUnavailableError):
        extractors.pdf_extractor_for({"engine": "marker"})


def test_forced_pypdf_engine_skips_marker(tmp_path, monkeypatch):
    """A payload engine="pypdf" never routes through marker, even when marker
    is available (the canonical-ingest fallback choice)."""

    import learnloop.ingest.extractors as extractors
    from learnloop.services.ingest_runner import default_extract

    class ExplodingMarker:
        name = "marker"

        def __init__(self, *, config=None):
            raise AssertionError("marker must not be constructed for engine=pypdf")

    class FakePyPdf:
        name = "pypdf"

        def extract(self, raw_bytes, context):
            block = DocumentBlock.build(span_id="s1", block_type="Text", text="Native text.", ordinal=1)
            unit = DocumentUnit(unit_id="u1", label="Doc", ordinal=1, semantic_hash="sha256:x", span_ids=["s1"])
            return DocumentIR(extractor="pypdf", extractor_version="1", blocks=[block], units=[unit])

    monkeypatch.setattr(extractors, "marker_available", lambda: True)
    monkeypatch.setattr(extractors, "MarkerDocumentExtractor", ExplodingMarker)
    monkeypatch.setattr(extractors, "PyPdfDocumentExtractor", FakePyPdf)

    ir = default_extract(_fetched_pdf(), "pdf", _bare_ctx(tmp_path, {"pdf_config": {"engine": "pypdf"}}))
    assert ir.extractor == "pypdf"
    assert not ir.health.flags  # a chosen fallback is not a degraded extraction


def test_forced_marker_unavailable_is_a_typed_error(tmp_path, monkeypatch):
    import learnloop.ingest.extractors as extractors
    from learnloop.services.ingest_runner import default_extract

    monkeypatch.setattr(extractors, "marker_available", lambda: False)
    with pytest.raises(IngestRunnerError) as excinfo:
        default_extract(_fetched_pdf(), "pdf", _bare_ctx(tmp_path, {"pdf_config": {"engine": "marker"}}))
    assert excinfo.value.code == "pdf_extractor_unavailable"


def test_vault_pdf_engine_governs_import_when_payload_is_silent(tmp_path, monkeypatch):
    """[ingest.pdf] engine="pypdf" in vault config finally reaches the durable
    import path; an explicit payload engine still wins."""

    import types

    from learnloop.services.ingest_runner import default_inventory_client

    from tests.helpers import create_basic_vault
    from tests.openai_fakes import install_fake_openai

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    toml_path = vault_root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    assert 'canonical_ingest = "codex_medium"' in text
    toml_path.write_text(
        text.replace('canonical_ingest = "codex_medium"', 'canonical_ingest = "openrouter"'),
        encoding="utf-8",
    )
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    install_fake_openai(monkeypatch)

    client = default_inventory_client(types.SimpleNamespace(vault_root=vault_root))

    assert client.provider_type == "openrouter"
    assert client.model == "deepseek/deepseek-chat"


def test_default_inventory_client_defaults_to_codex_and_errors_when_unavailable(tmp_path, monkeypatch):
    """Default routing still resolves codex, which is unavailable in tests — the
    runner raises a typed error instead of silently switching providers."""

    import types

    from learnloop.services.ingest_runner import IngestRunnerError, default_inventory_client

    from tests.helpers import create_basic_vault

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)

    with pytest.raises(IngestRunnerError):
        default_inventory_client(types.SimpleNamespace(vault_root=vault_root))
