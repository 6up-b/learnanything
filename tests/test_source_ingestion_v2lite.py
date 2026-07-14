"""ING M3.5 — v2-lite end-to-end smoke tests (spec_source_ingestion_v2 §15).

The v2-lite journey wires the M1–M3 stack (durable import → Document IR →
unit selection) into the *legacy* single-source synthesis: a durable batch runs
``import`` (extract once into an IR) then ``legacy_ingest``, and synthesis builds
its chunk context from the IR's deterministic display rendering instead of a
separate legacy extraction. Sources without an IR keep the legacy path
byte-for-byte.

No network, no marker, no LLM: fetch/extract are stubbed RunnerServices and the
codex client is the house ``_FakeCanonicalClient``.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.extractors.normalizers import markdown_to_ir
from learnloop.ingest.ir import render_ir_markdown
from learnloop.services.ingest_runner import (
    FetchedBytes,
    IngestRunner,
    JobSpec,
    RunnerServices,
)
from learnloop.services.source_ingestion import ingest_canonical_source
from learnloop.services.source_unit_selection import save_unit_selection

from tests.helpers import NOW, create_basic_vault
from tests.test_source_ingestion import _FakeCanonicalClient, _source_file

# Distinct, long-enough (> min_content_chars) sentinels per unit so we can prove
# which units reached synthesis.
SENTINEL_A = ("EigenSentinelAlpha. " + "An eigenvector of A keeps its direction under A. " * 12).strip()
SENTINEL_B = ("SingularSentinelBeta. " + "Singular values scale orthogonal directions. " * 12).strip()

_IR_MARKDOWN = (
    f"# Eigenvalues\n\n{SENTINEL_A}\n\n# Singular Values\n\n{SENTINEL_B}\n"
)


def _two_unit_ir():
    """A trivial IR with two heading-derived units (u1 = Eigenvalues, u2 = SVD)."""

    return markdown_to_ir(_IR_MARKDOWN, title="Linear algebra chapter", extractor_name="text")


def _v2lite_services(fake_client: _FakeCanonicalClient) -> RunnerServices:
    """Stub the import fetch/extract seam and route legacy synthesis through the
    fake codex client while forwarding the IR rendering the runner computed."""

    def fetch(source, category, ctx):
        return FetchedBytes(
            raw_bytes=b"raw source bytes",
            content_type="text/html",
            original_uri=source,
            retrieved_at=NOW,
        )

    def extract(fetched, category, ctx):
        return _two_unit_ir()

    def run_legacy(*, vault_root, source, subject_id, mode, progress, clock, ir_markdown=None, **_):
        return ingest_canonical_source(
            vault_root,
            source,
            fake_client,
            subject_id=subject_id,
            ir_markdown=ir_markdown,
            clock=clock,
            progress=progress,
        )

    return RunnerServices(fetch=fetch, extract=extract, run_legacy_ingest=run_legacy)


def _chunk_texts(fake_client: _FakeCanonicalClient) -> str:
    assert fake_client.calls, "synthesis was never invoked"
    return "\n".join(chunk.text for chunk in fake_client.calls[0].chunks)


# ---------------------------------------------------------------------------


def test_render_ir_markdown_honors_sections_and_unit_selection():
    ir = _two_unit_ir()

    full = render_ir_markdown(ir)
    assert "# eigenvalues" in full  # section-path heading emitted
    assert SENTINEL_A in full and SENTINEL_B in full

    unit_ids = [unit.unit_id for unit in ir.units]
    assert len(unit_ids) == 2
    selected = render_ir_markdown(ir, selected_unit_ids=[unit_ids[1]])
    assert SENTINEL_B in selected
    assert SENTINEL_A not in selected  # selected units only


def test_v2lite_batch_persists_ir_and_synthesizes_over_its_rendering(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    source = str(_source_file(tmp_path))
    fake_client = _FakeCanonicalClient()

    runner = IngestRunner(
        Repository(vault_root / "state.sqlite"),
        vault_root=vault_root,
        worker_id="w1",
        clock=FrozenClock(NOW),
        services=_v2lite_services(fake_client),
    )
    batch_id = runner.enqueue_batch(
        "legacy_ingest",
        [
            JobSpec("import", {"source": source, "subject_id": "linear-algebra"}),
            JobSpec(
                "legacy_ingest",
                {"source": source, "subject_id": "linear-algebra", "mode": "canonical"},
                depends_on=(0,),
            ),
        ],
        subject_id="linear-algebra",
    )
    runner.drain()

    jobs = {job["job_type"]: job for job in runner.repo.ingest_jobs_for_batch(batch_id)}
    assert jobs["import"]["status"] == "completed"
    assert jobs["legacy_ingest"]["status"] == "completed"

    # IR was persisted by the import stage and is reloadable.
    extraction_id = jobs["import"]["result"]["extraction_id"]
    persisted = runner.repo.load_document_ir(extraction_id)
    assert persisted is not None and len(persisted.units) == 2

    # Synthesis saw the IR-rendered markdown (both sentinels), and a proposal was made.
    context_text = _chunk_texts(fake_client)
    assert SENTINEL_A in context_text
    assert SENTINEL_B in context_text
    assert jobs["legacy_ingest"]["result"]["proposal_id"]

    repository = Repository(vault_root / "state.sqlite")
    batch = repository.proposal_batch_for_agent_run(jobs["legacy_ingest"]["result"]["agent_run_id"])
    assert batch["purpose"] == "canonical_ingest"


def test_v2lite_synthesis_respects_persisted_unit_selection(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    source = str(_source_file(tmp_path))
    fake_client = _FakeCanonicalClient()

    runner = IngestRunner(
        Repository(vault_root / "state.sqlite"),
        vault_root=vault_root,
        worker_id="w1",
        clock=FrozenClock(NOW),
        services=_v2lite_services(fake_client),
    )
    runner.enqueue_batch(
        "legacy_ingest",
        [
            JobSpec("import", {"source": source, "subject_id": "linear-algebra"}),
            JobSpec(
                "legacy_ingest",
                {"source": source, "subject_id": "linear-algebra", "mode": "canonical"},
                depends_on=(0,),
            ),
        ],
        subject_id="linear-algebra",
    )

    # Run the import stage first, persist a selection of the SVD unit only, then
    # let synthesis run — it must see only the selected unit's content.
    assert runner.run_next() is True
    import_job = next(
        job for job in runner.repo.ingest_jobs_by_types(("import",), limit=5)
    )
    extraction_id = import_job["result"]["extraction_id"]
    ir = runner.repo.load_document_ir(extraction_id)
    svd_unit = ir.units[1].unit_id
    save_unit_selection(runner.repo, extraction_id, [svd_unit], clock=FrozenClock(NOW))

    assert runner.run_next() is True  # legacy_ingest now eligible

    context_text = _chunk_texts(fake_client)
    assert SENTINEL_B in context_text
    assert SENTINEL_A not in context_text  # unit selection filtered it out


def test_legacy_path_without_ir_unchanged(tmp_path):
    """A synthesis with no import dependency (legacy call path) is byte-identical
    to calling ingest_canonical_source directly — no IR rendering is injected."""

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    source = str(_source_file(tmp_path))

    # Oracle: the direct legacy call.
    oracle_client = _FakeCanonicalClient()
    ingest_canonical_source(
        vault_root,
        source,
        oracle_client,
        subject_id="linear-algebra",
        clock=FrozenClock(NOW),
    )
    oracle_chunks = [chunk.text for chunk in oracle_client.calls[0].chunks]

    # A legacy_ingest batch with NO import dependency must produce the same context.
    fresh_root = tmp_path / "vault2"
    create_basic_vault(fresh_root)
    runner_client = _FakeCanonicalClient()

    def run_legacy(*, vault_root, source, subject_id, mode, progress, clock, ir_markdown=None, **_):
        assert ir_markdown is None  # no import dependency → legacy path stays intact
        return ingest_canonical_source(
            vault_root,
            source,
            runner_client,
            subject_id=subject_id,
            ir_markdown=ir_markdown,
            clock=clock,
            progress=progress,
        )

    runner = IngestRunner(
        Repository(fresh_root / "state.sqlite"),
        vault_root=fresh_root,
        worker_id="w1",
        clock=FrozenClock(NOW),
        services=RunnerServices(run_legacy_ingest=run_legacy),
    )
    runner.enqueue_batch(
        "legacy_ingest",
        [JobSpec("legacy_ingest", {"source": source, "subject_id": "linear-algebra", "mode": "canonical"})],
    )
    runner.drain()

    runner_chunks = [chunk.text for chunk in runner_client.calls[0].chunks]
    assert runner_chunks == oracle_chunks
