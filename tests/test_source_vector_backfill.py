"""Tutor delivery fixes, item 4: source-block vectors follow (re-)extraction.

With both embedding switches on, a completed extraction (an import, a
re-extraction, a page repair: whatever extractor ran) queues the
``source_block/text`` backfill of its source's current extraction through the
existing spend and receipt path; with either off nothing is queued or sent.
``learnloop doctor`` shows dense coverage per source.
"""
from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.content.pipeline.runner import FetchedBytes, IngestRunner, JobSpec, RunnerServices
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit
from learnloop.source_retrieval.source_vectors import SOURCE_VECTORS_JOB, source_coverage
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault
from tests.practice_index_fakes import HashingEmbedder, enable_practice_index

CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))

FIRST = [
    "Eigenvalues are the roots of the characteristic polynomial of a square matrix.",
    "An eigenvector v satisfies Av = tv for its eigenvalue t.",
    "Short.",  # under MIN_BLOCK_CHARS: never embedded
]
SECOND = [
    "A re-extraction reads the eigenvalue chapter again with another engine.",
    "Its blocks differ, so the old vectors no longer cover this source.",
    "Real symmetric matrices have real eigenvalues and orthogonal eigenvectors.",
]


def _ir(texts: list[str], version: str) -> DocumentIR:
    blocks = [DocumentBlock.build(span_id=f"s{index}", block_type="Text", text=text, ordinal=index, page=1)
              for index, text in enumerate(texts, start=1)]
    unit = DocumentUnit(unit_id="u1", label="Chapter 5", ordinal=0, semantic_hash=f"sha256:{version}",
                        page_start=1, page_end=1, span_ids=[block.span_id for block in blocks])
    return DocumentIR(extractor="text", extractor_version=version, blocks=blocks, units=[unit])


class _Extractor:
    """Stub fetch/extract seams; ``texts``/``version`` change between runs."""

    def __init__(self) -> None:
        self.texts, self.version = FIRST, "1"
        self.embedder = HashingEmbedder()

    def services(self) -> RunnerServices:
        def fetch(source, category, ctx):
            return FetchedBytes(raw_bytes=b"eigen chapter bytes", content_type="text/plain", original_uri=source,
                                retrieved_at="2026-10-13T12:00:00Z")

        def extract(fetched, category, ctx):
            return _ir(self.texts, self.version)

        def identity(fetched, category, ctx):
            return {"extractor": "text", "extractor_version": self.version}

        return RunnerServices(fetch=fetch, extract=extract, describe_extraction=identity,
                              embedding_client_factory=lambda _ctx: self.embedder)


def _vault(tmp_path, *, embeddings: bool):
    paths = create_basic_vault(tmp_path / "vault")
    if embeddings:
        enable_practice_index(paths, embeddings=True)
    return paths


def _runner(paths, extractor: _Extractor) -> IngestRunner:
    return IngestRunner(Repository(paths.sqlite_path), vault_root=paths.root, worker_id="w1", clock=CLOCK,
                        services=extractor.services())


def _import(runner: IngestRunner, source: str) -> dict:
    batch_id = runner.enqueue_batch("import", [JobSpec("import", {"source": source})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed", job
    return job["result"]


def _backfill_jobs(repository: Repository) -> list[dict]:
    return [job for job in repository.ingest_jobs_by_types((SOURCE_VECTORS_JOB,))]


def _vectors(repository: Repository, extraction_id: str) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM embedding_vectors WHERE record_kind = 'source_block' AND record_id LIKE ?",
            (extraction_id + "/%",)).fetchone()[0]


def _receipts(repository: Repository) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'embedding_backfill'").fetchone()[0]


def test_an_import_queues_the_source_block_backfill_and_its_source_becomes_dense(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    result = _import(runner, str(tmp_path / "eigen.md"))
    jobs = _backfill_jobs(runner.repo)
    assert [job["status"] for job in jobs] == ["completed"]
    report = jobs[0]["result"]
    assert report["status"] == "complete" and report["embedded_extraction_id"] == result["extraction_id"]
    assert report["embedded"] == 2  # the two substantive blocks; "Short." is never embedded
    assert _vectors(runner.repo, result["extraction_id"]) == 2
    assert _receipts(runner.repo) >= 1  # the existing spend/receipt path
    assert "Eigenvalues" not in json.dumps(report)  # aggregate only, never block text
    coverage = source_coverage(load_vault(paths.root), runner.repo)
    assert [(source["status"], source["covered"], source["blocks"]) for source in coverage["sources"]] == [
        ("complete", 2, 2)]
    assert coverage["effective"] is True and coverage["auto_backfill"] == "on"


def test_with_embeddings_off_nothing_is_queued_or_sent(tmp_path):
    paths = _vault(tmp_path, embeddings=False)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    _import(runner, str(tmp_path / "eigen.md"))
    assert _backfill_jobs(runner.repo) == []
    assert extractor.embedder.calls == [] and _receipts(runner.repo) == 0


def test_the_kill_switch_keeps_the_explicit_backfill_only(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    text = text.replace("backfill_enabled = true", "backfill_enabled = true\nbackfill_sources_on_extract = false", 1)
    (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    _import(runner, str(tmp_path / "eigen.md"))
    assert _backfill_jobs(runner.repo) == [] and extractor.embedder.calls == []


def test_a_re_extraction_queues_the_backfill_of_the_new_current_extraction(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    first = _import(runner, str(tmp_path / "eigen.md"))
    extractor.texts, extractor.version = SECOND, "2"  # another engine, the same bytes
    second = _import(runner, str(tmp_path / "eigen.md"))
    assert second["reused_revision"] is True and second["extraction_id"] != first["extraction_id"]
    jobs = {job["payload"]["extraction_id"]: job["result"] for job in _backfill_jobs(runner.repo)}
    assert {key: result["embedded_extraction_id"] for key, result in jobs.items()} == {
        first["extraction_id"]: first["extraction_id"], second["extraction_id"]: second["extraction_id"]}
    assert jobs[second["extraction_id"]]["embedded"] == 3
    coverage = source_coverage(load_vault(paths.root), runner.repo)
    assert [(source["extraction_id"], source["status"]) for source in coverage["sources"]] == [
        (second["extraction_id"], "complete")]


def test_a_page_repair_queues_the_backfill_of_its_sources_current_extraction(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    first = _import(runner, str(tmp_path / "eigen.md"))
    extractor.texts = SECOND
    batch_id = runner.enqueue_batch("extraction_repair", [JobSpec("extraction_repair", {
        "revision_id": first["revision_id"], "pages": [0], "repair_options": {"force_ocr": True},
        "consent": {"provider": "local", "purpose": "repair"}})])
    runner.drain()
    repair = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert repair["status"] == "completed", repair
    jobs = {job["payload"]["extraction_id"]: job["result"] for job in _backfill_jobs(runner.repo)}
    assert set(jobs) == {first["extraction_id"], repair["result"]["repair_extraction_id"]}
    # A repair composes onto its parent, which stays the current extraction
    # (already embedded: nothing is bought again).
    queued = jobs[repair["result"]["repair_extraction_id"]]
    assert queued["embedded_extraction_id"] == first["extraction_id"]
    assert queued["status"] == "complete" and queued["embedded"] == 0


def test_a_job_queued_before_the_switch_went_off_sends_nothing(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    first = _import(runner, str(tmp_path / "eigen.md"))
    calls = len(extractor.embedder.calls)
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    (paths.root / "learnloop.toml").write_text(text.replace("backfill_enabled = true", "backfill_enabled = false"),
                                               encoding="utf-8")
    batch_id = runner.enqueue_batch(SOURCE_VECTORS_JOB, [JobSpec(SOURCE_VECTORS_JOB,
                                                                 {"extraction_id": first["extraction_id"]})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed" and job["result"]["status"] == "disabled"
    assert len(extractor.embedder.calls) == calls


def test_doctor_shows_dense_coverage_per_source(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    _import(runner, str(tmp_path / "eigen.md"))
    cli = CliRunner()
    result = cli.invoke(app, ["doctor", "--vault", str(paths.root), "--json"])
    payload = json.loads(result.stdout)
    dense = payload["dense_retrieval"]
    assert [(source["status"], source["covered"], source["blocks"]) for source in dense["sources"]] == [
        ("complete", 2, 2)]
    assert dense["auto_backfill"] == "on"
    text = cli.invoke(app, ["doctor", "--vault", str(paths.root)])
    assert "Dense source retrieval:" in text.stdout and "1 of 1 sources complete" in text.stdout
