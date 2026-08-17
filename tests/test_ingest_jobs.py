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


def test_retry_synthesis_reuses_completed_inventory(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()
    calls = {"inventory": 0, "synthesis": 0}

    def inventory(ctx):
        calls["inventory"] += 1
        return {"inventoried": True}

    def fail_synthesis(ctx):
        calls["synthesis"] += 1
        raise RuntimeError("budget_exceeded: synthesis total-input ceiling")

    runner.handlers["inventory"] = inventory
    runner.handlers["bootstrap_synthesis"] = fail_synthesis
    batch_id = runner.enqueue_batch(
        "bootstrap_synthesis",
        [
            JobSpec("inventory", {"units": [{"unit_id": "u1"}]}),
            JobSpec("bootstrap_synthesis", {"source_set_id": "set_x"}, depends_on=(0,)),
        ],
    )
    runner.drain()

    first = runner.repo.ingest_jobs_for_batch(batch_id)
    assert [job["status"] for job in first] == ["completed", "failed"]

    def complete_synthesis(ctx):
        calls["synthesis"] += 1
        assert ctx.payload["synthesis_budgets"]["synthesis_total_input_ceiling"] == 250_000
        assert ctx.payload["synthesis_budgets"]["synthesis_shard_output_tokens"] == 32_000
        assert ctx.payload["synthesis_budgets"]["synthesis_output_tokens"] == 96_000
        return {"synthesized": True}

    runner.handlers["bootstrap_synthesis"] = complete_synthesis
    retried = jobs.retry_synthesis(
        batch_id,
        synthesis_budgets={
            "synthesis_total_input_ceiling": 250_000,
            "synthesis_shard_output_tokens": 32_000,
            "synthesis_output_tokens": 96_000,
        },
    )

    assert retried["status"] == "completed"
    assert calls == {"inventory": 1, "synthesis": 2}
    final = runner.repo.ingest_jobs_for_batch(batch_id)
    assert final[0]["attempt_count"] == 1
    assert final[1]["attempt_count"] == 2


def test_retry_synthesis_can_remove_local_token_ceilings(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()

    runner.handlers["inventory"] = lambda ctx: {"inventoried": True}

    def fail_synthesis(ctx):
        raise RuntimeError("budget_exceeded")

    runner.handlers["bootstrap_synthesis"] = fail_synthesis
    batch_id = runner.enqueue_batch(
        "bootstrap_synthesis",
        [
            JobSpec("inventory", {"units": [{"unit_id": "u1"}]}),
            JobSpec("bootstrap_synthesis", {"source_set_id": "set_x"}, depends_on=(0,)),
        ],
    )
    runner.drain()

    def complete_synthesis(ctx):
        assert ctx.payload["unlimited_token_budget"] is True
        return {"synthesized": True}

    runner.handlers["bootstrap_synthesis"] = complete_synthesis
    retried = jobs.retry_synthesis(batch_id, unlimited_token_budget=True)
    assert retried["status"] == "completed"


def test_quick_add_marks_inventory_and_synthesis_unlimited(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()
    runner.handlers["inventory"] = lambda ctx: {"inventoried": True}
    runner.handlers["bootstrap_synthesis"] = lambda ctx: {"synthesized": True}

    batch_id = jobs.enqueue_quick_add_build(
        extraction_id="ext_x",
        units=[{"unit_id": "u1", "role": "reference"}],
        source_set_id="set_x",
        output_budget_tokens=1,
        unlimited_token_budget=True,
    )

    inventory, synthesis = runner.repo.ingest_jobs_for_batch(batch_id)
    assert inventory["payload"]["unlimited_token_budget"] is True
    assert synthesis["payload"]["unlimited_token_budget"] is True


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


def test_resume_false_completed_rung_variant_reopens_request(tmp_path):
    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)
    runner = jobs._require_runner()
    request_id = runner.repo.insert_rung_variant_request(
        {
            "source_practice_item_id": "pi_source",
            "learning_object_id": "lo_source",
            "direction": "harder",
            "source_waypoint_slug": "execute",
            "target_waypoint_slug": "select_method",
            "target_rung_json": "{}",
            "status": "pending",
            "attempt_id": "attempt_original",
            "learner_claim_id": "claim_original",
        }
    )
    seen_requests: list[dict] = []

    def legacy_then_success(ctx):
        request = runner.repo.rung_variant_request(request_id)
        seen_requests.append(request)
        if len(seen_requests) == 1:
            runner.repo.update_rung_variant_request(
                request_id,
                status="failed",
                patch_id="patch_stale",
                created_practice_item_id="pi_stale",
                failure_reason="Codex timed out",
            )
            # This is the pre-fix handler contract that produced the false green
            # Activity row now present in existing vaults.
            return {"request_id": request_id, "status": "failed", "deduplicated": True}
        runner.repo.update_rung_variant_request(
            request_id,
            status="applied",
            patch_id="patch_fresh",
            created_practice_item_id="pi_fresh",
        )
        return {"request_id": request_id, "status": "applied"}

    runner.handlers["rung_variant"] = legacy_then_success
    batch_id = runner.enqueue_batch(
        "rung_variant",
        [JobSpec("rung_variant", {"request_id": request_id})],
    )
    runner.repo.update_rung_variant_request(request_id, batch_id=batch_id)
    runner.drain()

    raw_job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert raw_job["status"] == "completed"
    # Simulate the already-persisted false-success batch that prompted this fix.
    runner.repo.update_ingest_batch_status(batch_id, "completed", mark_finished=True)
    assert jobs.get_batch(batch_id)["status"] == "failed"
    legacy_view = jobs.get_batch(batch_id)["jobs"][0]
    assert legacy_view["status"] == "failed"
    assert legacy_view["message"] == "Codex timed out"
    assert legacy_view["error"]["code"] == "rung_variant_failed"
    assert legacy_view["error"]["retryable"] is True
    assert jobs.needs_reload(raw_job["id"]) is False

    retried = jobs.resume_batch(batch_id)

    assert retried["status"] == "completed"
    request = runner.repo.rung_variant_request(request_id)
    assert request["attempt_id"] == "attempt_original"
    assert request["learner_claim_id"] == "claim_original"
    assert request["patch_id"] == "patch_fresh"
    assert request["created_practice_item_id"] == "pi_fresh"
    assert request["failure_reason"] is None
    assert [request["status"] for request in seen_requests] == ["pending", "pending"]
    assert seen_requests[1]["patch_id"] is None
    assert seen_requests[1]["created_practice_item_id"] is None
    assert seen_requests[1]["failure_reason"] is None
    final_job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert final_job["attempt_count"] == 2
    assert final_job["result"]["status"] == "applied"


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


def test_list_batches_bulk_loads_jobs_and_dependencies(tmp_path, monkeypatch):
    """The UI polls this path; reads stay constant as batch/job counts grow."""

    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()
    for index in range(4):
        runner.enqueue_batch(
            f"bulk_{index}",
            [
                JobSpec("import", {"source": f"source_{index}"}),
                JobSpec("inventory", {"source": f"source_{index}"}, depends_on=(0,)),
            ],
        )

    calls = {"jobs": 0, "dependencies": 0}
    original_jobs = runner.repo.ingest_jobs_for_batches
    original_dependencies = runner.repo.ingest_job_dependencies_for_jobs

    def jobs_once(batch_ids):
        calls["jobs"] += 1
        return original_jobs(batch_ids)

    def dependencies_once(job_ids):
        calls["dependencies"] += 1
        return original_dependencies(job_ids)

    monkeypatch.setattr(runner.repo, "ingest_jobs_for_batches", jobs_once)
    monkeypatch.setattr(
        runner.repo, "ingest_job_dependencies_for_jobs", dependencies_once
    )
    monkeypatch.setattr(
        runner.repo,
        "ingest_jobs_for_batch",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("batch polling must not query jobs per batch")
        ),
    )
    monkeypatch.setattr(
        runner.repo,
        "ingest_job_dependency_ids",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("batch polling must not query dependencies per job")
        ),
    )

    views = jobs.list_batches()

    assert len(views) == 4
    assert all(len(view["jobs"]) == 2 for view in views)
    assert all(view["jobs"][1]["depends_on"] for view in views)
    assert calls == {"jobs": 1, "dependencies": 1}


def test_list_batches_bulk_loads_failed_rung_requests(tmp_path, monkeypatch):
    """Legacy false-green rung jobs must not reintroduce one read per job."""

    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)
    runner = jobs._require_runner()

    def legacy_failure(ctx):
        request_id = str(ctx.payload["request_id"])
        runner.repo.update_rung_variant_request(
            request_id,
            status="failed",
            failure_reason=f"failed {request_id}",
        )
        return {"request_id": request_id, "status": "failed", "deduplicated": True}

    runner.handlers["rung_variant"] = legacy_failure
    request_ids: list[str] = []
    for index in range(4):
        request_id = runner.repo.insert_rung_variant_request(
            {
                "source_practice_item_id": f"pi_{index}",
                "learning_object_id": f"lo_{index}",
                "direction": "harder",
                "source_waypoint_slug": "execute",
                "target_waypoint_slug": "select_method",
                "target_rung_json": "{}",
                "status": "pending",
            }
        )
        request_ids.append(request_id)
        batch_id = runner.enqueue_batch(
            "rung_variant",
            [JobSpec("rung_variant", {"request_id": request_id})],
        )
        runner.repo.update_rung_variant_request(request_id, batch_id=batch_id)
    runner.drain()

    calls = 0
    original_bulk = runner.repo.rung_variant_requests

    def requests_once(ids):
        nonlocal calls
        calls += 1
        return original_bulk(ids)

    monkeypatch.setattr(runner.repo, "rung_variant_requests", requests_once)
    monkeypatch.setattr(
        runner.repo,
        "rung_variant_request",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("batch polling must not query a rung request per job")
        ),
    )

    views = jobs.list_batches()

    assert calls == 1
    assert len(views) == 4
    assert {
        view["jobs"][0]["message"]
        for view in views
    } == {f"failed {request_id}" for request_id in request_ids}


def test_batch_completion_triggers_one_vault_reload(tmp_path):
    """A durable synthesis batch that applies content in the background must
    refresh the sidecar's in-memory vault exactly once via the batch-polling
    RPCs — otherwise Today/knowledge screens serve the pre-apply snapshot."""

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers.ingest import ListIngestBatchesInput, list_ingest_batches

    from tests.helpers import create_basic_vault

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    ctx = SidecarContext()
    ctx.load(vault_root, maintenance=False)
    ctx.ingest_jobs.bind(ctx.repository, vault_root, background=False)
    runner = ctx.ingest_jobs._require_runner()
    runner.handlers["bootstrap_synthesis"] = lambda _ctx: {"applied": True}

    reloads: list[bool] = []
    ctx.reload = lambda *, maintenance=True: reloads.append(maintenance)  # type: ignore[method-assign]

    runner.enqueue_batch(
        "bootstrap_synthesis",
        [JobSpec("bootstrap_synthesis", {"source_set_id": "set_x", "apply": True})],
    )
    runner.drain()

    list_ingest_batches(ctx, ListIngestBatchesInput(limit=10))
    assert reloads == [False]
    # Subsequent polls of the same completed batch never re-reload.
    list_ingest_batches(ctx, ListIngestBatchesInput(limit=10))
    assert reloads == [False]


def test_bind_premarks_previously_completed_apply_jobs(tmp_path):
    """Jobs that completed before this process bound are reflected in the bind's
    accompanying vault load — a fresh bind must not schedule a redundant reload."""

    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)
    runner = jobs._require_runner()
    runner.handlers["bootstrap_synthesis"] = lambda _ctx: {"applied": True}
    batch_id = runner.enqueue_batch(
        "bootstrap_synthesis",
        [JobSpec("bootstrap_synthesis", {"source_set_id": "set_x", "apply": True})],
    )
    runner.drain()
    job_id = runner.repo.ingest_jobs_for_batch(batch_id)[0]["id"]
    assert jobs.needs_reload(job_id) is True

    fresh = DurableIngestJobs()
    fresh.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)
    assert fresh.needs_reload(job_id) is False


def _failed_synthesis_batch(jobs: DurableIngestJobs, *, details: dict) -> str:
    from learnloop.services.ingest_runner import IngestRunnerError

    runner = jobs._require_runner()
    runner.handlers["inventory"] = lambda _ctx: {"inventoried": True}

    def fail_synthesis(_ctx):
        raise IngestRunnerError(
            "gates failed", code="synthesis_gate_failed", details=details, retryable=True
        )

    runner.handlers["bootstrap_synthesis"] = fail_synthesis
    batch_id = runner.enqueue_batch(
        "bootstrap_synthesis",
        [
            JobSpec("inventory", {"units": [{"unit_id": "u1"}]}),
            JobSpec("bootstrap_synthesis", {"source_set_id": "set_x", "apply": True}, depends_on=(0,)),
        ],
    )
    runner.drain()
    return batch_id


def test_retry_synthesis_reuse_candidate_wires_recovery_payload(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()
    batch_id = _failed_synthesis_batch(
        jobs, details={"candidate_preserved": True, "synthesis_run_id": "run_1"}
    )

    seen: dict = {}

    def succeed(ctx):
        seen.update(ctx.payload)
        return {"revalidated": True}

    runner.handlers["bootstrap_synthesis"] = succeed
    runner.repo.synthesis_run = lambda run_id: {"id": run_id, "candidate_output": {"summary": "s"}}

    retried = jobs.retry_synthesis(batch_id, reuse_candidate=True)
    assert retried["status"] == "completed"
    assert seen["reuse_candidate"] is True
    assert seen["synthesis_run_id"] == "run_1"
    # A later plain retry must NOT silently reuse the stale candidate flags.
    runner.handlers["bootstrap_synthesis"] = lambda ctx: (_ for _ in ()).throw(RuntimeError("x"))
    # (only asserting payload hygiene through the wrapper's cleanup path)


def test_retry_synthesis_reuse_candidate_requires_preserved_candidate(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    batch_id = _failed_synthesis_batch(jobs, details={})
    with pytest.raises(ValueError, match="preserved no candidate"):
        jobs.retry_synthesis(batch_id, reuse_candidate=True)


def test_retry_synthesis_repair_flags_flow_into_payload(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()
    batch_id = _failed_synthesis_batch(
        jobs, details={"candidate_preserved": True, "synthesis_run_id": "run_1"}
    )
    seen: dict = {}

    def succeed(ctx):
        seen.update(ctx.payload)
        return {"revalidated": True}

    runner.handlers["bootstrap_synthesis"] = succeed
    runner.repo.synthesis_run = lambda run_id: {"id": run_id, "candidate_output": {"summary": "s"}}

    ops = [{"op": "drop_dependency", "item_client_id": "p", "dep": "shard_1__crit"}]
    jobs.retry_synthesis(batch_id, reuse_candidate=True, repair_candidate=True, repair_ops=ops)
    assert seen["repair_candidate"] is True
    assert seen["repair_ops"] == ops


def test_retry_synthesis_repair_requires_reuse_candidate(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    batch_id = _failed_synthesis_batch(
        jobs, details={"candidate_preserved": True, "synthesis_run_id": "run_1"}
    )
    with pytest.raises(ValueError, match="requires reuse_candidate"):
        jobs.retry_synthesis(batch_id, repair_candidate=True)


def test_plain_retry_clears_candidate_recovery_flags(tmp_path):
    jobs = _bind(tmp_path, lambda **_: _FakeResult())
    runner = jobs._require_runner()
    batch_id = _failed_synthesis_batch(
        jobs, details={"candidate_preserved": True, "synthesis_run_id": "run_1"}
    )
    runner.repo.synthesis_run = lambda run_id: {"id": run_id, "candidate_output": {"summary": "s"}}

    from learnloop.services.ingest_runner import IngestRunnerError

    def fail_again(_ctx):
        raise IngestRunnerError("still failing", code="synthesis_gate_failed",
                                details={"candidate_preserved": True, "synthesis_run_id": "run_2"})

    runner.handlers["bootstrap_synthesis"] = fail_again
    jobs.retry_synthesis(batch_id, reuse_candidate=True)

    seen: dict = {}

    def succeed(ctx):
        seen.update(ctx.payload)
        return {"ok": True}

    runner.handlers["bootstrap_synthesis"] = succeed
    jobs.retry_synthesis(batch_id, synthesis_budgets={"synthesis_total_input_ceiling": 250_000})
    assert "reuse_candidate" not in seen
    assert "synthesis_run_id" not in seen
    assert seen["synthesis_budgets"]["synthesis_total_input_ceiling"] == 250_000


def test_kick_reader_drain_runs_model_synthesis_foreground(tmp_path):
    """The sidecar worker (foreground in tests) drains queued demand-paged reader
    requests with the injected client — the loop that previously never ran."""

    from learnloop.services import reader_requests as RR
    from tests.test_reader_requests import _FakePresetClient, _ingest

    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                       span_id="s1", preset="worked_example")

    client = _FakePresetClient()
    jobs = DurableIngestJobs()
    jobs.bind(repo, tmp_path, background=False, reader_synth_client_factory=lambda: client)
    jobs.kick_reader_drain()

    assert len(client.calls) == 1
    objs = repo.source_objects_for_source("src1")
    assert len(objs) == 1 and objs[0]["version"]["status"] == "proposed"
    # A second kick finds nothing queued and never re-runs the model.
    jobs.kick_reader_drain()
    assert len(client.calls) == 1


def test_kick_reader_drain_leaves_requests_queued_without_provider(tmp_path):
    from learnloop.services import reader_requests as RR
    from tests.test_reader_requests import _ingest

    repo = Repository(tmp_path / "state.sqlite")
    _ingest(repo)
    res = RR.enqueue_request(repo, source_id="src1", revision_id="rev1", extraction_id="ext1",
                             span_id="s1", preset="ask")
    jobs = DurableIngestJobs()
    jobs.bind(repo, tmp_path, background=False, reader_synth_client_factory=lambda: None)
    jobs.kick_reader_drain()
    # Provider unavailable -> the infrastructure never fails the request.
    row = repo.get_reader_request(res["request_id"])
    assert row["status"] == "queued"


def test_reader_drain_client_routes_via_canonical_ingest(tmp_path, monkeypatch):
    """The no-factory reader drain resolves through canonical_ingest routing, so
    an openrouter-routed vault drains preset requests without a codex runtime."""

    import types

    from tests.helpers import create_basic_vault
    from tests.openai_fakes import install_fake_openai

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
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

    repo = Repository(paths.sqlite_path)
    jobs = DurableIngestJobs()
    jobs.bind(repo, vault_root, background=False)

    client = jobs._resolve_reader_client(types.SimpleNamespace(vault_root=vault_root))

    assert client is not None
    assert client.provider_type == "openrouter"
    assert callable(getattr(client, "run_reader_preset_synthesis", None))


def test_import_batch_is_not_a_build_and_its_ladder_says_so(tmp_path):
    """Regression for the build-plan screen's old "start batch" (§8.6.2).

    An import batch carries a single `import` job — no inventory, no synthesis —
    and for an already-imported source it finishes on the extraction cache with
    ZERO model calls. Its checkpoint ladder must therefore stop at `extracted`,
    or the Activity card renders the inventoried/synthesized/applied rungs it can
    never reach and reads as a completed study-map build.
    """

    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)

    batch_id = jobs.enqueue_import(["notes.md"], subject_id="linear-algebra")
    batch = jobs.get_batch(batch_id)

    assert [job["job_type"] for job in batch["jobs"]] == ["import"]
    assert batch["jobs"][0]["checkpoint_ladder"] == ["acquired", "registered", "extracted"]


def test_source_set_build_enqueues_inventory_then_synthesis_with_budgets(tmp_path):
    """The build-plan screen's "start build" path: the batch that actually spends
    tokens is [inventory per member -> bootstrap_synthesis], with any per-run
    ceilings snapshotted onto the synthesis job's payload (§1/§8)."""

    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)

    batch_id = jobs.enqueue_source_set_build(
        members=[{"extraction_id": "ext_a", "units": [{"unit_id": "u_a", "role": "primary_textbook"}]}],
        source_set_id="set_x",
        subject_id="linear-algebra",
        input_budget_tokens=15_000,
        output_budget_tokens=4_000,
        synthesis_budgets={"synthesis_total_input_ceiling": 120_000},
    )
    batch = jobs.get_batch(batch_id)
    runner = jobs._require_runner()
    rows = {job["job_type"]: job for job in runner.repo.ingest_jobs_for_batch(batch_id)}

    assert [job["job_type"] for job in batch["jobs"]] == ["inventory", "bootstrap_synthesis"]
    # Synthesis waits on the inventory it reads, so gates run once.
    assert runner.repo.ingest_job_dependency_ids(rows["bootstrap_synthesis"]["id"]) == [
        rows["inventory"]["id"]
    ]
    assert rows["inventory"]["payload"]["input_budget_tokens"] == 15_000
    assert rows["inventory"]["payload"]["output_budget_tokens"] == 4_000
    assert rows["bootstrap_synthesis"]["payload"]["synthesis_budgets"] == {
        "synthesis_total_input_ceiling": 120_000
    }
    # The synthesis job can reach every rung, so it keeps the full ladder.
    synthesis_view = next(j for j in batch["jobs"] if j["job_type"] == "bootstrap_synthesis")
    assert synthesis_view["checkpoint_ladder"][-1] == "applied"


def test_source_set_append_snapshots_budget_overrides(tmp_path):
    jobs = DurableIngestJobs()
    jobs.bind(Repository(tmp_path / "state.sqlite"), tmp_path, background=False)

    batch_id = jobs.enqueue_source_set_append(
        members=[],
        source_set_id="set_x",
        subject_id="linear-algebra",
        synthesis_budgets={"synthesis_shard_output_tokens": 20_000},
    )
    rows = jobs._require_runner().repo.ingest_jobs_for_batch(batch_id)

    assert [job["job_type"] for job in rows] == ["append_synthesis"]
    assert rows[0]["payload"]["synthesis_budgets"] == {"synthesis_shard_output_tokens": 20_000}
