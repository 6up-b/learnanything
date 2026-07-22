"""ING M3 — outline, unit selection, acquisition preview, build plan, and
consent-gated extraction repair (spec_source_ingestion_v2 §3/§5.3/§8.6, §14 rows:
outline determinism, consent, token budgets)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.clock import FrozenClock
from learnloop.config import IngestProviderLimits, LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.hashing import (
    extraction_request_hash,
    extraction_result_hash,
    semantic_hash,
)
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, DocumentUnit, PageHealth, ExtractionHealth
from learnloop.ingest.source_library import register_source_revision
from learnloop.services.acquisition_preview import build_acquisition_preview
from learnloop.services.build_plan import build_build_plan, route_create_or_update
from learnloop.services.extraction_health import analyze_extraction_health
from learnloop.services.ingest_runner import (
    FetchedBytes,
    IngestRunner,
    JobSpec,
    RunnerServices,
)
from learnloop.services.source_outline import approx_token_count, build_source_outline
from learnloop.services.source_unit_selection import (
    SelectionValidationError,
    reanchor_selection,
    save_unit_selection,
    validate_unit_selection,
)

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "state.sqlite")


def _persist(repo: Repository, ir: DocumentIR, *, revision_id: str, extraction_id: str, page_selection=None) -> str:
    request_hash = extraction_request_hash(
        revision_id=revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        page_selection=page_selection,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    repo.insert_extraction_run(
        id=extraction_id,
        revision_id=revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash,
        ir_schema_version=IR_SCHEMA_VERSION,
        page_selection=page_selection,
        status="running",
        clock=_CLOCK,
    )
    repo.persist_document_ir(extraction_id, ir)
    repo.complete_extraction_run(
        extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir), clock=_CLOCK
    )
    return extraction_id


def _markdown_extraction(repo: Repository, markdown: str, *, uri="file:///book.md", extraction_id="ext1") -> tuple[str, str]:
    reg = register_source_revision(
        repo, acquisition_kind="textfile", canonical_uri=uri, raw_bytes=markdown.encode(), original_uri=uri, clock=_CLOCK
    )
    ir = markdown_to_ir(markdown, title="Book", extractor_name="text")
    _persist(repo, ir, revision_id=reg.revision_id, extraction_id=extraction_id)
    return reg.revision_id, extraction_id


_TEXTBOOK_MD = """# Vectors
A vector is an element of a vector space.

# Worked Examples
Example 1. Compute the norm of a vector.

Example 2. Normalize a vector.

# Exercises
Problem 1. Prove the triangle inequality.
"""


# --------------------------------------------------------------------------
# §14 "Outline determinism: same extraction run → identical outline, zero agent runs"
# --------------------------------------------------------------------------


def test_outline_determinism_zero_agent_runs(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)

    first = build_source_outline(repo, extraction_id)
    second = build_source_outline(repo, extraction_id)
    dumped_first = json.dumps(first.model_dump(mode="json"), sort_keys=True)
    dumped_second = json.dumps(second.model_dump(mode="json"), sort_keys=True)
    assert dumped_first == dumped_second  # byte-identical outline

    # Zero agent runs: outlining creates no agent_runs rows.
    with repo.connection() as connection:
        agent_runs = connection.execute("SELECT COUNT(*) AS n FROM agent_runs").fetchone()["n"]
    assert agent_runs == 0
    assert first.unit_count >= 3


def test_outline_reports_structural_signals_and_token_sizes(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    outline = build_source_outline(repo, extraction_id)

    labels = {unit.label: unit for unit in outline.units}
    assert labels["worked-examples"].structural_signals["examples"] == 2
    assert labels["exercises"].structural_signals["exercises"] == 1
    for unit in outline.units:
        assert unit.approx_tokens >= 0
        assert unit.inventory == {"inventoried": False, "inventory_profile": None}
    assert outline.approx_tokens == sum(unit.approx_tokens for unit in outline.units)


def test_approx_token_count_is_chars_over_four():
    assert approx_token_count("") == 0
    assert approx_token_count("abcd") == 1
    assert approx_token_count("abcde") == 2


# --------------------------------------------------------------------------
# Unit selection persistence + re-anchor survival (§5.3)
# --------------------------------------------------------------------------


def test_unit_selection_persists_and_validates(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    outline = build_source_outline(repo, extraction_id)
    chosen = [outline.units[0].unit_id, outline.units[2].unit_id]

    saved = save_unit_selection(repo, extraction_id, chosen)
    assert saved["selected_unit_ids"] == chosen
    assert repo.get_unit_selection(extraction_id)["selected_unit_ids"] == chosen

    ir = repo.load_document_ir(extraction_id)
    with pytest.raises(SelectionValidationError):
        validate_unit_selection(ir, ["u_missing"])


def test_boundary_override_camelcase_keys_are_normalized(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    outline = build_source_outline(repo, extraction_id)
    unit_id = outline.units[0].unit_id
    # The frontend sends camelCase override dicts; they must validate and store
    # canonically (snake_case) so re-anchoring reads a single key set.
    saved = save_unit_selection(
        repo,
        extraction_id,
        [unit_id],
        boundary_overrides=[{"op": "merge_with_next", "unitId": unit_id}],
    )
    assert saved["boundary_overrides"] == [{"op": "merge_with_next", "unit_id": unit_id}]


def test_selection_survives_reextraction_via_reanchor(tmp_path):
    repo = _repo(tmp_path)
    revision_id, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    outline = build_source_outline(repo, extraction_id)
    selected = [unit.unit_id for unit in outline.units[:2]]
    save_unit_selection(repo, extraction_id, selected)

    from_ir = repo.load_document_ir(extraction_id)
    # A re-extraction with the same content: units re-anchor by semantic hash.
    to_ir = markdown_to_ir(_TEXTBOOK_MD, title="Book", extractor_name="text")
    reanchored = reanchor_selection(from_ir, to_ir, selected, [])
    assert len(reanchored.selected_unit_ids) == 2
    assert reanchored.needs_review == []


def test_reanchor_flags_unresolved_units_for_review(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    from_ir = repo.load_document_ir(extraction_id)
    selected = [unit.unit_id for unit in from_ir.units]

    # A completely different document: nothing re-anchors, everything is flagged.
    to_ir = markdown_to_ir("# Unrelated\nTotally different content here.\n", title="Other", extractor_name="text")
    reanchored = reanchor_selection(from_ir, to_ir, selected, [])
    assert reanchored.selected_unit_ids == []
    assert set(reanchored.needs_review) == set(selected)  # never silently dropped


# --------------------------------------------------------------------------
# Acquisition preview (§8.6.1) — no downloads/extraction/LLM
# --------------------------------------------------------------------------


def test_acquisition_preview_reports_recognition_dupes_and_existing(tmp_path):
    repo = _repo(tmp_path)
    register_source_revision(
        repo, acquisition_kind="youtube", canonical_uri="https://youtube.com/watch?v=abc", raw_bytes=b"x", clock=_CLOCK
    )
    config = LearnLoopConfig()

    preview = build_acquisition_preview(
        repo,
        config,
        [
            "https://youtube.com/watch?v=abc",
            "https://youtube.com/watch?v=abc",  # duplicate within the batch
            "https://arxiv.org/abs/2401.00001",
            "@@ not a source @@",
        ],
    )
    items = preview.items
    assert items[0].existing_source_id is not None
    assert items[0].existing_revision_count == 1
    assert items[1].duplicate_of_input == "https://youtube.com/watch?v=abc"
    assert items[2].recognized and items[2].category == "arxiv"
    assert items[3].recognized is False and items[3].error
    assert preview.recognized_count == 3


def test_acquisition_preview_flags_potential_external_consent(tmp_path):
    repo = _repo(tmp_path)
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 scanned")
    config = LearnLoopConfig()
    config.ingest.pdf.use_llm = True
    config.ingest.pdf.llm_base_url = "http://127.0.0.1:8000/v1"

    preview = build_acquisition_preview(repo, config, [str(pdf)])
    item = preview.items[0]
    assert item.is_local and item.file_size_bytes == len(b"%PDF-1.4 scanned")
    assert item.potential_external and item.potential_external[0]["kind"] == "pdf_llm_extraction"
    assert preview.needs_consent_count == 1


# --------------------------------------------------------------------------
# Build plan (§8.6.2) — §14 "Token budgets: preflight emits per-stage estimates"
# --------------------------------------------------------------------------


def _config_with_provider(context_tokens=None, max_output_tokens=None) -> LearnLoopConfig:
    config = LearnLoopConfig()
    # Canonical ingest now routes to the workload-specific "codex_medium" profile.
    config.ingest.providers["codex_medium"] = IngestProviderLimits(
        context_tokens=context_tokens, max_output_tokens=max_output_tokens
    )
    return config


def test_token_budgets_preflight_emits_per_stage_estimates(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    config = _config_with_provider(context_tokens=30000, max_output_tokens=8000)
    vault = SimpleNamespace(learning_objects={})

    plan = build_build_plan(
        repo, config, vault, subject_id=None, selections=[{"extraction_id": extraction_id, "selected_unit_ids": []}]
    )
    stage_names = {stage.stage for stage in plan.stages}
    assert {"inventory", "synthesis"} <= stage_names
    for stage in plan.stages:
        # Every stage emits input / cached / max-output / call estimates.
        assert stage.calls >= 0
        assert stage.input_tokens >= 0
        assert stage.cached_tokens >= 0
        assert stage.max_output_tokens >= 0
        assert stage.ceiling > 0
    payload = plan.as_dict()
    assert payload["totals"]["calls"] == sum(stage.calls for stage in plan.stages)
    assert payload["provider"] == "codex_medium"


def test_build_plan_routes_create_vs_update(tmp_path):
    repo = _repo(tmp_path)
    _, extraction_id = _markdown_extraction(repo, _TEXTBOOK_MD)
    config = _config_with_provider()
    lo = SimpleNamespace(subjects=["algebra"])

    empty_vault = SimpleNamespace(learning_objects={})
    mapped_vault = SimpleNamespace(learning_objects={"lo1": lo})
    assert route_create_or_update(empty_vault, "algebra") == "create"
    assert route_create_or_update(mapped_vault, "algebra") == "update"

    create_plan = build_build_plan(
        repo, config, empty_vault, subject_id="algebra", selections=[{"extraction_id": extraction_id}]
    )
    update_plan = build_build_plan(
        repo, config, mapped_vault, subject_id="algebra", selections=[{"extraction_id": extraction_id}]
    )
    assert create_plan.routing == "create"
    assert "append" not in {s.stage for s in create_plan.stages}
    assert update_plan.routing == "update"
    assert "append" in {s.stage for s in update_plan.stages}


def test_build_plan_warns_when_stage_exceeds_provider_context(tmp_path):
    repo = _repo(tmp_path)
    big = "# Chapter\n" + ("word " * 4000) + "\n"
    _, extraction_id = _markdown_extraction(repo, big)
    config = _config_with_provider(context_tokens=100)  # tiny context → over ceiling
    vault = SimpleNamespace(learning_objects={})

    plan = build_build_plan(repo, config, vault, subject_id=None, selections=[{"extraction_id": extraction_id}])
    assert any(stage.exceeds_ceiling for stage in plan.stages)
    assert plan.warnings


# --------------------------------------------------------------------------
# Extraction health analysis (§2.5)
# --------------------------------------------------------------------------


def test_extraction_health_flags_image_only_and_replacement_chars():
    blocks = [
        DocumentBlock.build(span_id="s1", block_type="Text", text="Readable page one.", ordinal=1, page=1),
        DocumentBlock.build(span_id="s2", block_type="Figure", text="scan artifact", ordinal=2, page=2),
        DocumentBlock.build(span_id="s3", block_type="Text", text="garbled �� text", ordinal=3, page=3),
    ]
    ir = DocumentIR(extractor="marker", extractor_version="1", blocks=blocks)
    report = analyze_extraction_health(ir)
    reasons = {page: fp.reasons for fp in report.flagged_pages for page in range(fp.page_range[0], fp.page_range[1] + 1)}
    assert "image_only" in reasons.get(2, [])
    assert "replacement_chars" in reasons.get(3, [])
    assert report.difficult_page_count >= 2


def test_extraction_health_flags_method_differs_from_neighbors():
    blocks = [
        DocumentBlock.build(span_id=f"s{p}", block_type="Text", text=f"page {p} text body", ordinal=p, page=p)
        for p in (1, 2, 3)
    ]
    health = ExtractionHealth(
        pages=[
            PageHealth(page=1, text_extraction_method="pdftext"),
            PageHealth(page=2, text_extraction_method="ocr"),
            PageHealth(page=3, text_extraction_method="pdftext"),
        ]
    )
    ir = DocumentIR(extractor="marker", extractor_version="1", blocks=blocks, health=health)
    report = analyze_extraction_health(ir)
    reasons = {page: fp.reasons for fp in report.flagged_pages for page in range(fp.page_range[0], fp.page_range[1] + 1)}
    assert "method_differs" in reasons.get(2, [])


# --------------------------------------------------------------------------
# Consent-gated extraction repair (§2.5) — §14 consent rows
# --------------------------------------------------------------------------


def _paged_pdf_setup(repo: Repository, tmp_path: Path):
    (tmp_path / "book.pdf").write_bytes(b"%PDF-parent")
    reg = register_source_revision(
        repo,
        acquisition_kind="pdf",
        canonical_uri="file:///book.pdf",
        raw_bytes=b"%PDF-parent",
        original_uri=str(tmp_path / "book.pdf"),
        clock=_CLOCK,
    )
    pb = [
        DocumentBlock.build(span_id="s1", block_type="Text", text="Clean page one about vectors.", ordinal=1, page=1),
        DocumentBlock.build(span_id="s2", block_type="Text", text="Broken � page two.", ordinal=2, page=2),
    ]
    u1 = DocumentUnit(unit_id="u1", label="Ch1", ordinal=1, semantic_hash=semantic_hash([pb[0]]), page_start=1, page_end=1, span_ids=["s1"])
    u2 = DocumentUnit(unit_id="u2", label="Ch2", ordinal=2, semantic_hash=semantic_hash([pb[1]]), page_start=2, page_end=2, span_ids=["s2"])
    parent = DocumentIR(extractor="text", extractor_version="1", blocks=pb, units=[u1, u2])
    _persist(repo, parent, revision_id=reg.revision_id, extraction_id="ext_parent")
    return reg.revision_id, parent, u1.semantic_hash


def _repair_services(repair_ir: DocumentIR) -> RunnerServices:
    def fetch(source, category, ctx):
        return FetchedBytes(raw_bytes=b"%PDF-parent", content_type="application/pdf", original_uri=source, retrieved_at="t")

    def extract(fetched, category, ctx):
        return repair_ir

    return RunnerServices(fetch=fetch, extract=extract)


def test_targeted_repair_records_consent_and_preserves_unaffected_hashes(tmp_path):
    repo = _repo(tmp_path)
    revision_id, _parent, u1_hash = _paged_pdf_setup(repo, tmp_path)
    rblocks = [DocumentBlock.build(span_id="s1", block_type="Text", text="Fixed clean page two about matrices.", ordinal=1, page=2)]
    ru = DocumentUnit(unit_id="u2", label="Ch2", ordinal=1, semantic_hash=semantic_hash(rblocks), page_start=2, page_end=2, span_ids=["s1"])
    repair_ir = DocumentIR(extractor="text", extractor_version="1", blocks=rblocks, units=[ru])

    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w", clock=_CLOCK, services=_repair_services(repair_ir))
    consent = {"provider": "local", "purpose": "extraction_repair", "pages": ["2"], "cached": False}
    batch = runner.enqueue_batch(
        "extraction_repair",
        [JobSpec("extraction_repair", {"revision_id": revision_id, "pages": ["2"], "repair_options": {"force_ocr": True}, "consent": consent})],
    )
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"
    result = job["result"]
    assert result["consent"] == consent  # provider/pages/consent recorded
    assert result["repaired_pages"] == [2]
    # The child run links back to the parent (§2.3).
    child = runner.repo.get_extraction_run(result["repair_extraction_id"])
    assert child["parent_extraction_id"] == result["parent_extraction_id"]
    # Unaffected unit keeps its hash; the repaired unit gets a fresh one.
    assert result["unaffected_unit_hashes"]["u1"] == u1_hash
    assert result["affected_unit_hashes"]["u2"] != _parent_hash_for(repo, "ext_parent", "u2")


def _parent_hash_for(repo: Repository, extraction_id: str, unit_id: str) -> str:
    ir = repo.load_document_ir(extraction_id)
    return next(unit.semantic_hash for unit in ir.units if unit.unit_id == unit_id)


def test_repair_requires_explicit_consent(tmp_path):
    repo = _repo(tmp_path)
    revision_id, _parent, _hash = _paged_pdf_setup(repo, tmp_path)
    repair_ir = DocumentIR(extractor="text", extractor_version="1", blocks=[], units=[])
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w", clock=_CLOCK, services=_repair_services(repair_ir))
    batch = runner.enqueue_batch(
        "extraction_repair",
        [JobSpec("extraction_repair", {"revision_id": revision_id, "pages": ["2"]})],  # no consent
    )
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "failed"
    assert job["error"]["code"] == "invalid_job"


def test_declining_repair_leaves_a_usable_flagged_extraction(tmp_path):
    # If the user declines repair, no repair job runs; the flagged parent extraction
    # is still fully usable (outline builds, health flags remain).
    repo = _repo(tmp_path)
    revision_id, parent, _hash = _paged_pdf_setup(repo, tmp_path)
    outline = build_source_outline(repo, "ext_parent")
    assert outline.unit_count == 2  # usable despite flags
    report = analyze_extraction_health(parent)
    assert report.difficult_page_count >= 1  # page two flagged (replacement char)
    # No repair runs were created by declining.
    runs = repo.extraction_runs_for_revision(revision_id)
    assert all(run.get("parent_extraction_id") is None for run in runs)


def test_plain_import_performs_no_external_egress(tmp_path):
    # §14 consent row: plain Import must be reachable with NO external/repair path.
    # We drain an import batch through services that raise if any external LLM /
    # repair egress is attempted, and assert it still succeeds.
    class _Tripwire(RuntimeError):
        pass

    def fetch(source, category, ctx):
        return FetchedBytes(raw_bytes=b"eigen text", content_type="text/plain", original_uri=source, retrieved_at="t")

    def extract(fetched, category, ctx):
        # An import must never carry a consent record or an external LLM config.
        payload = ctx.payload
        if payload.get("consent") is not None:
            raise _Tripwire("import must not carry a consent record")
        pdf_config = payload.get("pdf_config") or {}
        if pdf_config.get("use_llm"):
            raise _Tripwire("import must not enable external LLM extraction")
        return markdown_to_ir(fetched.raw_bytes.decode(), title=None, extractor_name="text")

    repo = _repo(tmp_path)
    (tmp_path / "notes.md").write_text("# N\nbody\n")
    runner = IngestRunner(repo, vault_root=tmp_path, worker_id="w", clock=_CLOCK, services=RunnerServices(fetch=fetch, extract=extract))
    batch = runner.enqueue_batch("import", [JobSpec("import", {"source": str(tmp_path / "notes.md")})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed"


def test_import_snapshots_build_plan_estimate_into_payload(tmp_path):
    # When a batch is started from a plan, the estimate snapshots into the job
    # payload (§8.6.2 / §6.2). Exercised via the durable-jobs wrapper.
    from learnloop_sidecar.ingest_jobs import DurableIngestJobs

    repo = _repo(tmp_path)
    (tmp_path / "notes.md").write_text("# N\nbody text\n")

    def fetch(source, category, ctx):
        return FetchedBytes(raw_bytes=b"# N\nbody text\n", content_type="text/plain", original_uri=source, retrieved_at="t")

    def extract(fetched, category, ctx):
        return markdown_to_ir(fetched.raw_bytes.decode(), title=None, extractor_name="text")

    jobs = DurableIngestJobs()
    jobs.bind(repo, tmp_path, clock=_CLOCK, services=RunnerServices(fetch=fetch, extract=extract), background=False)
    estimate = {"stages": [{"stage": "inventory", "calls": 1}], "totals": {"calls": 1}}
    batch_id = jobs.enqueue_import([str(tmp_path / "notes.md")], estimate=estimate)
    jobs.drain_foreground()
    batch = jobs.get_batch(batch_id)
    assert batch["jobs"][0]["estimate"] == estimate


def test_import_snapshots_pdf_page_selection_into_payload(tmp_path):
    from learnloop_sidecar.ingest_jobs import DurableIngestJobs

    repo = _repo(tmp_path)
    jobs = DurableIngestJobs()
    jobs.bind(repo, tmp_path, clock=_CLOCK, background=False)
    batch_id = jobs.enqueue_import([str(tmp_path / "textbook.pdf")], page_selection=[9, 10, 11])

    job = repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["payload"]["page_selection"] == [9, 10, 11]


def test_import_snapshots_pdf_engine_choice_into_payload(tmp_path):
    """An explicit marker/pypdf choice rides the import payload; "auto" (or
    None) stays implicit so unchanged sources keep their extraction identity."""

    from learnloop_sidecar.ingest_jobs import DurableIngestJobs

    repo = _repo(tmp_path)
    jobs = DurableIngestJobs()
    jobs.bind(repo, tmp_path, clock=_CLOCK, background=False)

    forced = jobs.enqueue_import([str(tmp_path / "scan.pdf")], pdf_engine="pypdf")
    assert repo.ingest_jobs_for_batch(forced)[0]["payload"]["pdf_config"] == {"engine": "pypdf"}

    auto = jobs.enqueue_import([str(tmp_path / "scan.pdf")], pdf_engine="auto")
    assert "pdf_config" not in repo.ingest_jobs_for_batch(auto)[0]["payload"]


def test_multi_source_import_assigns_page_selection_per_source(tmp_path):
    from learnloop_sidecar.ingest_jobs import DurableIngestJobs

    repo = _repo(tmp_path)
    jobs = DurableIngestJobs()
    jobs.bind(repo, tmp_path, clock=_CLOCK, background=False)
    first = str(tmp_path / "volume-one.pdf")
    second = str(tmp_path / "volume-two.pdf")
    batch_id = jobs.enqueue_import(
        [first, second],
        page_selections={first: [9, 10, 11], second: [49, 50]},
    )

    queued = repo.ingest_jobs_for_batch(batch_id)
    assert queued[0]["payload"]["page_selection"] == [9, 10, 11]
    assert queued[1]["payload"]["page_selection"] == [49, 50]
