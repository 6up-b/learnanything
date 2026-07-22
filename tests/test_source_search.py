"""Across-source text search (reader library): deterministic, reader-gated,
span-addressed hits."""

from __future__ import annotations

from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services.source_search import search_sources
from tests.test_source_inventory import _persist, _register_revision


def _ingest_source(repo: Repository, *, source_id: str, revision_id: str,
                   extraction_id: str, texts: list[str], title: str) -> None:
    _register_revision(repo, source_id=source_id, revision_id=revision_id)
    blocks = [
        DocumentBlock.build(span_id=f"s{i}", block_type="Text", text=text,
                            ordinal=i, page=i, section_path=["Ch1", f"Sec {i}"])
        for i, text in enumerate(texts, start=1)
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="Ch1", ordinal=0, semantic_hash="sha256:x",
                            span_ids=[b.span_id for b in blocks])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repo, ir, revision_id=revision_id, extraction_id=extraction_id)


def test_search_finds_hits_across_sources_with_span_addresses(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest_source(repo, source_id="srcA", revision_id="revA", extraction_id="extA",
                   texts=["Symmetric matrices have real eigenvalues.",
                          "Unrelated prose about geometry."], title="Linear Algebra")
    _ingest_source(repo, source_id="srcB", revision_id="revB", extraction_id="extB",
                   texts=["Eigenvalues of a Markov chain govern mixing."], title="Probability")

    result = search_sources(repo, query="eigenvalues")
    assert result["searched_sources"] == 2
    assert {hit["source_id"] for hit in result["hits"]} == {"srcA", "srcB"}
    first = next(hit for hit in result["hits"] if hit["source_id"] == "srcA")
    assert first["span_id"] == "s1"
    assert first["section"] == "Sec 1"
    assert "eigenvalues" in first["snippet"].lower()


def test_search_skips_reader_disabled_sources_and_short_queries(tmp_path: Path) -> None:
    repo = Repository(tmp_path / "s.sqlite")
    _ingest_source(repo, source_id="srcA", revision_id="revA", extraction_id="extA",
                   texts=["Symmetric matrices have real eigenvalues."], title="A")
    _ingest_source(repo, source_id="srcB", revision_id="revB", extraction_id="extB",
                   texts=["Eigenvalues appear here too."], title="B")
    repo.set_source_reader_enabled("srcB", False)

    result = search_sources(repo, query="eigenvalues")
    assert {hit["source_id"] for hit in result["hits"]} == {"srcA"}
    assert search_sources(repo, query="e")["hits"] == []
