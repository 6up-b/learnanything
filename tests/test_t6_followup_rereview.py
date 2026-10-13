"""T6 follow-up Codex re-review (2026-10-13): F8, tutor-scoped dense baselines.

The report's verification systems judge the tutor's own pools, built over each
question's teaching scope, which can differ from the library scope (an older
extraction an LO still cites; a library source outside every teaching scope).
Whether those pools are dense, and whether query vectors are paid for, follows
each question's teaching scope, not the library's index: a ``dense_verify``
pool that falls back to ``hybrid_rrf`` is no dense baseline, so it is neither
verified nor scored, its coverage says so and its verdicts are blocked; and an
incomplete library index no longer starves a complete teaching index of query
vectors.
"""
from __future__ import annotations

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
from learnloop.ops.pf_calls import ROLE_TASKS
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.suites import register_suites
from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, _blocks, loaded, seed_source
from tests.test_source_inventory import _persist
from tests.test_source_retrieval_tutor import CitingTutor, ask, setup

QWEN = "qwen/qwen3-embedding-8b"
ROOMY = SpendCaps(max_candidates=10_000, max_pairs=10_000, max_retries=2, max_calls=5_000,
                  max_total_tokens=10**9, max_estimated_usd=10**4)
VERIFYING = ("hybrid_verify", "pool_verify", "dense_verify")
#: An earlier edition of the book: other wording, so no stored vector covers it.
OLD_EDITION = {"ch_old": ("Chapter 5 Eigenvalues (first edition)", [
    ("In the first edition the eigenvalues of a square matrix are found as roots of its characteristic polynomial.", 3),
    ("In the first edition an eigenspace collects every eigenvector of one eigenvalue together with zero.", 3),
])}


@pytest.fixture(autouse=True)
def _fresh():
    clear_cache()
    register_suites(SUITES, role_tasks=ROLE_TASKS)
    yield
    clear_cache()


def _clients(llm):
    return {"source_question_writer": llm, "source_relevance": llm, "source_rewrite": llm, "source_verify": llm}


def _cite_an_older_extraction(repository: Repository) -> None:
    """Every LO cites an extraction of the book's earlier revision (not current, not embedded)."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            ("rev_book_old", "src_book", "sha256:src_book_old", "2025-01-01T00:00:00Z"))
        connection.commit()
    header, rows = OLD_EDITION["ch_old"]
    blocks, span_ids = _blocks("ch_old", header, rows, 1)
    unit = DocumentUnit(unit_id="ch_old", label=header, ordinal=0, semantic_hash="sha256:ch_old",
                        page_start=3, page_end=3, span_ids=span_ids)
    _persist(repository, DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks,
                                    assets=[], health=ExtractionHealth()),
             revision_id="rev_book_old", extraction_id="ext_book_old")
    for lo_id in ("lo_matrices", "lo_vectors", "lo_inner"):
        repository.insert_entity_source_link(
            entity_type="learning_object", entity_id=lo_id, locator="span:ext_book_old/s2", relation="primary",
            source_id="src_book", revision_id="rev_book_old", extraction_id="ext_book_old")


def _report(paths, tmp_path, llm, views):
    report = run_compare(loaded(paths), request=CompareRequest(suite="source_retrieval",
                                                               output_dir=tmp_path / "out", max_cases=8,
                                                               views=views),
                         caps=ROOMY, price_per_million=1.0, clients=_clients(llm),
                         embedding_clients={QWEN: HashingEmbedder()})
    assert report["status"] == "complete", report.get("reason")
    return report


def test_a_dense_baseline_whose_teaching_pool_falls_back_is_neither_verified_nor_scored(tmp_path):
    paths, repository = setup(tmp_path)
    _cite_an_older_extraction(repository)
    ask(paths, repository, CitingTutor())  # a logged practice question on an LO that cites the old edition
    report = _report(paths, tmp_path, FakeSourceLLM(), VERIFYING)
    results = report["results"]
    assert results["dense_index"]["status"] == "ready"  # the library's index is complete
    verification = results["verification"]
    fell_back = verification["pool_modes"]["dense_verify"].get("hybrid_rrf", 0)
    assert fell_back > 0, "an LO-bound question's teaching scope holds the unembedded old edition"
    coverage = verification["coverage"]["dense_verify"]
    # Not a dense pool, so not verified as dense_verify: counted, never asked, never scored.
    assert coverage["unavailable"] == fell_back
    assert coverage["verified"] == coverage["questions"] - fell_back
    assert coverage["failed"] == 0
    assert verification["statuses"]["dense_verify"].get("unavailable") == fell_back
    assert verification["systems"]["dense_verify"]["questions"] <= coverage["verified"]
    for name in ("pool_verify - dense_verify", "dense_verify - hybrid_verify"):
        assert results["verdicts"][name] is False
        assert "dense_verify" in results["verdict_blocks"][name]
        assert "hybrid_rrf" in results["verdict_blocks"][name]
    # pool_verify's fallback is the tutor's own (production) behaviour: it stays scored.
    assert verification["coverage"]["pool_verify"]["verified"] == verification["coverage"]["pool_verify"]["questions"]
    markdown = (tmp_path / "out" / report["report_files"][1]).read_text(encoding="utf-8")
    assert "pool_verify - dense_verify blocked:" in markdown
    assert f"- dense_verify: {fell_back} pool(s) fell back" in markdown


def test_an_incomplete_library_index_does_not_starve_a_complete_teaching_index(tmp_path):
    paths, repository = setup(tmp_path)
    # A reader-enabled source in no source set and cited by nothing, added after
    # the backfill: the library's index is partial, every teaching scope complete.
    seed_source(repository, source_id="src_extra", revision_id="rev_extra", extraction_id="ext_extra",
                title="Unplaced notes", units={"extra": ("Loose notes", [
                    ("Unplaced notes about matrices that no learning object cites and no source set holds.", 1),
                ])}, furniture=False)
    ask(paths, repository, CitingTutor())
    report = _report(paths, tmp_path, FakeSourceLLM(), ("meaning", *VERIFYING))
    results = report["results"]
    assert results["dense_index"]["status"] == "partial"
    assert report["usage"]["calls_by_role"].get("embedding", 0) > 0  # the tutor pools' query vectors
    assert "meaning" in results["unavailable_systems"]  # the library's dense list needs the library's index
    assert "dense_verify" in results["systems"]
    verification = results["verification"]
    asked = verification["coverage"]["pool_verify"]["questions"]
    assert asked > 0
    # The tutor's pools are dense: query vectors were paid for their teaching scopes.
    assert verification["pool_modes"]["pool_verify"] == {"dense_plus_bm25": asked}
    assert verification["pool_modes"]["dense_verify"] == {"dense_plus_bm25": asked}
    coverage = verification["coverage"]["dense_verify"]
    assert coverage["verified"] == coverage["questions"] == asked and coverage["unavailable"] == 0
    assert "pool_verify - dense_verify" not in results["verdict_blocks"]


def test_dense_verify_is_unavailable_only_when_no_teaching_scope_can_be_dense(tmp_path):
    paths, repository = setup(tmp_path, embed=False)
    report = _report(paths, tmp_path, FakeSourceLLM(), ("meaning", *VERIFYING))
    results = report["results"]
    assert set(results["unavailable_systems"]) == {"meaning", "dense_verify"}
    assert "teaching scope" in results["unavailable_systems"]["dense_verify"]
    assert results["systems"] == ["hybrid_verify", "pool_verify"]
    verification = results["verification"]
    assert set(verification["teaching_dense_index"]) == {"incomplete"}
    # No index can rank, so no query vector is paid for; the pools are the tutor's fallback.
    assert report["usage"]["calls_by_role"].get("embedding", 0) == 0
    assert verification["pool_modes"]["pool_verify"] == {"hybrid_rrf": verification["coverage"]["pool_verify"]["questions"]}
