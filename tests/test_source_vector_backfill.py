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


def _repair(runner: IngestRunner, revision_id: str) -> dict:
    batch_id = runner.enqueue_batch("extraction_repair", [JobSpec("extraction_repair", {
        "revision_id": revision_id, "pages": [0], "repair_options": {"force_ocr": True},
        "consent": {"provider": "local", "purpose": "repair"}})])
    runner.drain()
    repair = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert repair["status"] == "completed", repair
    return repair


def test_a_page_repair_queues_the_backfill_its_sources_current_extraction_owes(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    switched_off = text.replace("backfill_enabled = true",
                                "backfill_enabled = true\nbackfill_sources_on_extract = false", 1)
    (paths.root / "learnloop.toml").write_text(switched_off, encoding="utf-8")
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    first = _import(runner, str(tmp_path / "eigen.md"))  # imported while the automatic backfill was off
    assert _backfill_jobs(runner.repo) == []
    (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")
    extractor.texts = SECOND
    repair = _repair(runner, first["revision_id"])
    # A repair composes onto its parent, which stays the current extraction:
    # the parent is what the source is owed.
    jobs = _backfill_jobs(runner.repo)
    assert [job["payload"]["extraction_id"] for job in jobs] == [repair["result"]["repair_extraction_id"]]
    assert jobs[0]["result"]["embedded_extraction_id"] == first["extraction_id"]
    assert jobs[0]["status"] == "completed" and jobs[0]["result"]["embedded"] == 2
    # Another repair of a covered source owes nothing: no job, nothing bought.
    calls = len(extractor.embedder.calls)
    _repair(runner, first["revision_id"])
    assert len(_backfill_jobs(runner.repo)) == 1 and len(extractor.embedder.calls) == calls


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


# -- Codex review F3: the backfill obligation survives an interruption ------------


class _Crash(BaseException):
    """A worker dying mid-job (not an exception the runner classifies)."""


def _later_runner(paths, extractor: _Extractor, minutes: int = 10) -> IngestRunner:
    from datetime import timedelta

    later = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC) + timedelta(minutes=minutes))
    return IngestRunner(Repository(paths.sqlite_path), vault_root=paths.root, worker_id="w2", clock=later,
                        services=extractor.services())


def test_an_interruption_right_after_extraction_completes_still_indexes_the_source_on_retry(tmp_path, monkeypatch):
    import pytest

    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    original = Repository.complete_extraction_run
    crashed: list[str] = []

    def complete_then_die(self, extraction_id, **kwargs):
        result = original(self, extraction_id, **kwargs)
        if not crashed:
            crashed.append(extraction_id)
            raise _Crash()  # the completion is committed; nothing after it ran
        return result

    monkeypatch.setattr(Repository, "complete_extraction_run", complete_then_die)
    batch_id = runner.enqueue_batch("import", [JobSpec("import", {"source": str(tmp_path / "eigen.md")})])
    with pytest.raises(_Crash):
        runner.drain()
    assert crashed and _backfill_jobs(runner.repo) == []
    # The host restarts: the expired lease is recovered and the import retried.
    later = _later_runner(paths, extractor)
    assert later.recover_stale_leases()
    later.resume_batch(batch_id)
    later.drain()
    job = later.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed" and job["result"]["reused_extraction"] is True
    assert job["result"]["extraction_id"] == crashed[0]
    jobs = _backfill_jobs(later.repo)
    assert [(entry["status"], entry["result"]["embedded"]) for entry in jobs] == [("completed", 2)]
    assert _vectors(later.repo, crashed[0]) == 2
    bought = len(extractor.embedder.calls)
    # A further retry of the same import owes nothing: no second job, no purchase.
    _import(later, str(tmp_path / "eigen.md"))
    assert len(_backfill_jobs(later.repo)) == 1 and len(extractor.embedder.calls) == bought


def test_a_backfill_that_cannot_be_queued_fails_the_import_retryably_and_the_retry_queues_it(tmp_path, monkeypatch):
    from learnloop.content.pipeline.runner import JobContext

    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    original = JobContext.enqueue_batch
    failures: list[str] = []

    def enqueue_once_failing(self, workflow_type, jobs, **kwargs):
        if workflow_type == SOURCE_VECTORS_JOB and not failures:
            failures.append(workflow_type)
            raise RuntimeError("database is locked")
        return original(self, workflow_type, jobs, **kwargs)

    monkeypatch.setattr(JobContext, "enqueue_batch", enqueue_once_failing)
    batch_id = runner.enqueue_batch("import", [JobSpec("import", {"source": str(tmp_path / "eigen.md")})])
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "failed", job  # never a silent omission
    assert job["error"]["code"] == "source_vectors_not_queued" and job["error"]["retryable"] is True
    assert _backfill_jobs(runner.repo) == []
    runner.resume_batch(batch_id)
    runner.drain()
    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed" and job["result"]["reused_extraction"] is True
    assert [entry["status"] for entry in _backfill_jobs(runner.repo)] == ["completed"]
    assert _vectors(runner.repo, job["result"]["extraction_id"]) == 2


# -- Codex review F4: an unsuccessful backfill is not a completed job -------------


def _backfill_job(repository: Repository) -> dict:
    jobs = _backfill_jobs(repository)
    assert len(jobs) == 1, jobs
    return jobs[0]


def test_lock_contention_fails_the_backfill_retryably_and_a_retry_completes_it(tmp_path):
    import fcntl

    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    lock_path = paths.root / ".learnloop" / "embedding-backfill.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)  # an explicit backfill is running
        try:
            result = _import(runner, str(tmp_path / "eigen.md"))
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
    job = _backfill_job(runner.repo)
    assert job["status"] == "failed", job
    assert job["error"]["code"] == "embedding_backfill_busy" and job["error"]["retryable"] is True
    assert _vectors(runner.repo, result["extraction_id"]) == 0 and extractor.embedder.calls == []
    runner.resume_batch(job["batch_id"])
    runner.drain()
    job = _backfill_job(runner.repo)
    assert job["status"] == "completed" and job["result"]["embedded"] == 2
    assert _vectors(runner.repo, result["extraction_id"]) == 2


class _FailingAfterFirst(HashingEmbedder):
    """Embeds one batch, then the provider fails until ``failing`` is cleared."""

    def __init__(self) -> None:
        super().__init__()
        self.failing = True
        self.attempts = 0

    def embed(self, inputs, task_prefix):
        from learnloop.ai.errors import AIProviderUnavailable

        self.attempts += 1
        if self.failing and self.calls:
            raise AIProviderUnavailable("provider down")
        return super().embed(inputs, task_prefix)


def test_a_provider_failure_after_a_saved_batch_fails_retryably_and_the_retry_buys_only_the_rest(
        tmp_path, monkeypatch):
    from learnloop.source_retrieval import source_vectors

    monkeypatch.setattr(source_vectors, "BATCH_SIZE", 1)
    paths = _vault(tmp_path, embeddings=True)
    extractor = _Extractor()
    extractor.embedder = _FailingAfterFirst()
    runner = _runner(paths, extractor)
    result = _import(runner, str(tmp_path / "eigen.md"))
    job = _backfill_job(runner.repo)
    assert job["status"] == "failed", job
    assert job["error"]["code"] == "embedding_provider_failed" and job["error"]["retryable"] is True
    assert job["error"]["details"]["embedded"] == 1 and job["error"]["details"]["remaining"] == 1
    assert _vectors(runner.repo, result["extraction_id"]) == 1  # the paid batch is kept
    extractor.embedder.failing = False
    runner.resume_batch(job["batch_id"])
    runner.drain()
    job = _backfill_job(runner.repo)
    assert job["status"] == "completed" and job["result"]["embedded"] == 1  # only the rest is bought
    assert _vectors(runner.repo, result["extraction_id"]) == 2
    assert [len(texts) for texts, _prefix in extractor.embedder.calls] == [1, 1]


def test_a_backfill_over_its_money_cap_fails_and_names_the_cap(tmp_path):
    paths = _vault(tmp_path, embeddings=True)
    text = (paths.root / "learnloop.toml").read_text(encoding="utf-8")
    text = text.replace("backfill_enabled = true", "backfill_enabled = true\nsource_backfill_max_cost_usd = 0.0", 1)
    (paths.root / "learnloop.toml").write_text(text, encoding="utf-8")
    extractor = _Extractor()
    runner = _runner(paths, extractor)
    _import(runner, str(tmp_path / "eigen.md"))
    job = _backfill_job(runner.repo)
    assert job["status"] == "failed", job
    assert job["error"]["code"] == "over_budget" and job["error"]["retryable"] is False
    assert "embedding.source_backfill_max_cost_usd" in job["error"]["message"]
    assert extractor.embedder.calls == []
