"""What other test files use from ``tests/test_source_vector_backfill.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.content.pipeline.runner import FetchedBytes, IngestRunner, JobSpec, RunnerServices
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit
from learnloop.source_retrieval.source_vectors import SOURCE_VECTORS_JOB

from tests.practice_index_fakes import HashingEmbedder


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
