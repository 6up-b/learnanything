"""Slice 2 T6: the source_block/text recipe, dense index, hybrid search and its consumers."""
from __future__ import annotations

from contextlib import closing
import json

import numpy as np
import pytest
from typer.testing import CliRunner

from learnloop.ai.spend import SpendCaps
from learnloop.cli import app
from learnloop.content.pipeline.quick_add import rank_units_by_text, select_relevant_units
from learnloop.content.sources.source_outline import build_source_outline
from learnloop.db.connection import connect
from learnloop.db.stores.embedding_vectors import retrieve
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.reader.source_search import search_sources
from learnloop.source_retrieval.corpus import library_scope, teaching_scope
from learnloop.source_retrieval.dense import clear_cache, load_dense_index
from learnloop.source_retrieval.library import search_library
from learnloop.source_retrieval.queries import is_conceptual
from learnloop.source_retrieval.recipes import (
    SOURCE_BLOCK_RECIPE,
    SOURCE_RETRIEVAL_RECIPES,
    scope_manifest,
    split_record_id,
)
from learnloop.source_retrieval.search import search_spans
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, select_recipes
from tests.helpers import append_config_toml
from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, build_retrieval_vault, loaded

CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8,
                 max_estimated_usd=10.0)


@pytest.fixture(autouse=True)
def _fresh_dense_cache():
    clear_cache()
    yield
    clear_cache()


def backfill(paths, embedder=None):
    embedder = embedder or HashingEmbedder()
    report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",),
                                 registry=SOURCE_RETRIEVAL_RECIPES, client_factory=lambda: embedder)
    assert report["status"] == "complete", report
    return report


def test_the_source_recipe_is_never_in_the_default_backfill(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    assert SOURCE_BLOCK_RECIPE not in EMBEDDING_RECIPES
    assert all(recipe.record_kind != "source_block" for recipe in select_recipes(None))
    vault = loaded(paths)
    expected = list(SOURCE_RETRIEVAL_RECIPES[SOURCE_BLOCK_RECIPE].records(vault))
    runner = CliRunner()
    planned = runner.invoke(app, ["embeddings", "backfill", "--vault", str(paths.root), "--record-kind",
                                  "source_block", "--dry-run", "--json"])
    report = json.loads(planned.stdout)
    assert planned.exit_code == 0, planned.output
    assert report["recipes"] == [SOURCE_BLOCK_RECIPE] and report["records"] == len(expected) > 0
    default = json.loads(runner.invoke(app, ["embeddings", "backfill", "--vault", str(paths.root),
                                             "--dry-run", "--json"]).stdout)
    assert SOURCE_BLOCK_RECIPE not in default["recipes"]
    mixed = runner.invoke(app, ["embeddings", "backfill", "--vault", str(paths.root), "--record-kind",
                                "source_block", "--record-kind", "item", "--dry-run", "--json"])
    assert mixed.exit_code == 1 and "on its own" in json.loads(mixed.stdout)["reason"]


def test_recipe_text_resolves_section_headers_and_skips_furniture(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    records = {record.record_id: record for record in
               SOURCE_RETRIEVAL_RECIPES[SOURCE_BLOCK_RECIPE].records(loaded(paths))}
    assert records["ext_book/s2"].text == (
        "Section: Chapter 5 Eigenvalues\nEigenvalues are the roots of the characteristic polynomial "
        "det(A - tI) of a square matrix.")
    assert "ext_book/s999" not in records  # page furniture
    assert "ext_book/s1" not in records  # "Chapter 5 Eigenvalues" is under 20 characters


def test_dense_ranking_is_the_phase_1_mean_centred_cosine(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    embedder = HashingEmbedder()
    backfill(paths, embedder)
    vault = loaded(paths)
    scope = library_scope(repository)
    index = load_dense_index(vault, repository, scope)
    assert index.ready and index.expected == index.covered
    query = np.asarray(embedder.embed(["real eigenvalues of symmetric matrices"], "retrieval-query")[0])
    excluded = {"ext_book/s4"}
    ranked = index.rank(query, limit=50, allow=lambda record_id: record_id not in excluded)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        manifest = scope_manifest(connection, repository.sqlite_path, scope.extractions)
        phase1 = retrieve(connection, record_kind="source_block", field="text",
                          model_id=vault.config.embedding.model, task_prefix="retrieval-document",
                          query=query, expected_records=manifest, limit=50,
                          candidate_ids=set(manifest) - excluded)
    assert [record_id for record_id, _ in ranked] == [match.record_id for match in phase1]
    assert np.allclose([score for _, score in ranked], [match.score for match in phase1], atol=1e-5)


def test_without_a_complete_index_search_is_keyword_only_and_says_so(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    embedder = HashingEmbedder()
    result = search_spans(loaded(paths), repository, "determinant swapped rows", library_scope(repository),
                          deep=True, rewrite=False, embedder=embedder)
    assert result.dense["status"] == "incomplete"
    assert any("--record-kind source_block" in note for note in result.notes)
    assert result.lists == ["keyword"] and result.basis == "keyword"
    assert embedder.calls == []  # no query embedding is bought for an unusable index
    assert result.hits[0].key == ("ext_book", "s7")


def test_deep_search_fuses_keyword_and_meaning_with_one_cached_query_embedding(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    backfill(paths)
    vault = loaded(paths)
    embedder = HashingEmbedder()
    first = search_library(vault, repository, query="orthogonal vectors basis", deep=True, embedder=embedder)
    assert first["basis"] == "keyword+meaning" and first["deep"] is True
    assert [call[1] for call in embedder.calls] == ["retrieval-query"]
    assert first["hits"][0]["span_id"] in {"s12", "s13"}
    assert first["hits"][0]["section"] == "Chapter 6 Orthogonality"  # header text, not a block ref
    again = search_library(vault, repository, query="orthogonal vectors basis", deep=True, embedder=embedder)
    assert len(embedder.calls) == 1 and again["hits"] == first["hits"]


def test_only_conceptual_questions_are_rewritten(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    backfill(paths)
    vault = loaded(paths)
    llm = FakeSourceLLM()
    scope = library_scope(repository)
    assert is_conceptual("Why do symmetric matrices have real eigenvalues?")
    assert not is_conceptual("eigenvalue")
    conceptual = search_spans(vault, repository, "Why do symmetric matrices have real eigenvalues?", scope,
                              deep=True, embedder=HashingEmbedder(), rewrite_client=llm)
    assert {"rewrite_keyword", "rewrite_meaning"} <= set(conceptual.lists)
    assert conceptual.basis == "keyword+meaning+rewrite" and conceptual.rewrite["status"] == "rewritten"
    keyword = search_spans(vault, repository, "eigenvalue", scope, deep=True, embedder=HashingEmbedder(),
                           rewrite_client=llm)
    assert keyword.rewrite["status"] == "not_needed"
    assert [purpose for purpose, _ in llm.calls] == ["source_query_rewrite"]


def test_a_metered_rewrite_without_a_price_is_skipped_not_guessed(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    llm = FakeSourceLLM(provider_type="openrouter")
    result = search_spans(loaded(paths), repository, "Why is the determinant zero?",
                          library_scope(repository), deep=True, rewrite_client=llm, embedder=HashingEmbedder())
    assert result.rewrite["status"].startswith("skipped: metered route")
    assert llm.calls == [] and "rewrite_keyword" not in result.lists


def test_a_failed_rewrite_degrades_to_the_unrewritten_search(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    result = search_spans(loaded(paths), repository, "Why is the determinant zero?",
                          library_scope(repository), deep=True, rewrite_client=FakeSourceLLM(fail=True),
                          embedder=HashingEmbedder())
    assert result.rewrite["status"] == "failed" and result.hits


def test_typing_search_beats_instr_on_stems_and_prefixes_and_keeps_substring_hits(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    vault = loaded(paths)
    today = search_sources(repository, query="determinants")
    assert {hit["span_id"] for hit in today["hits"]} == {"s6"}  # only the header says "Determinants"
    typed = search_library(vault, repository, query="determinants")
    assert {"s6", "s7", "s8", "s9"} <= {hit["span_id"] for hit in typed["hits"]}
    assert typed["basis"] == "keyword" and typed["deep"] is False
    partial = search_library(vault, repository, query="cofactor expan")
    assert partial["hits"][0]["span_id"] == "s8"
    phrase = search_library(vault, repository, query="dot product is zero")
    assert phrase["hits"][0]["span_id"] == "s12"
    assert "substring" in phrase["hits"][0]["matched_by"]


def test_the_kill_switch_restores_todays_search_exactly(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    append_config_toml(paths.root, "[source_retrieval]\nenabled = false\n")
    vault = loaded(paths)
    for query in ("determinants", "dot product", "Why are eigenvalues real?"):
        assert search_library(vault, repository, query=query, deep=True) == search_sources(repository, query=query)


def test_teaching_scope_excludes_every_assessment_span(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    vault = loaded(paths)
    scope = teaching_scope(vault, repository, ["lo_matrices"])
    assert set(scope.extractions) == {"ext_book", "ext_exam"}
    assert {key for key in scope.excluded if key[0] == "ext_exam"} >= {("ext_exam", "s1"), ("ext_exam", "s2")}
    found = search_spans(vault, repository, "compute the eigenvalues of the matrix", scope, deep=False)
    assert found.hits and all(hit.extraction_id == "ext_book" for hit in found.hits)
    library = search_spans(vault, repository, "compute the eigenvalues of the matrix",
                           library_scope(repository), deep=False)
    assert any(hit.extraction_id == "ext_exam" for hit in library.hits)  # the library still shows it


def test_quick_add_ranks_units_by_their_text_not_only_their_labels(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    outline = build_source_outline(repository, "ext_book")
    keywords = {"spectral"}
    ranked = rank_units_by_text(repository, outline, "ext_book", query_text="symmetric matrices real spectrum",
                                keywords=keywords)
    assert ranked[0] == "ch_eigen"
    total = sum(unit.approx_tokens for unit in outline.units)
    cap = total - 1  # forces a subset
    by_label = select_relevant_units(outline, keywords=keywords, cap_tokens=cap)
    by_text = select_relevant_units(outline, keywords=keywords, cap_tokens=cap, ranked_unit_ids=ranked)
    assert "ch_eigen" in by_text[0]
    assert by_label[0][0] == "ch_eigen"  # no label matches: the leading chapters, in order
    assert by_text[0] == sorted(by_text[0], key=[u.unit_id for u in outline.units].index)
    assert rank_units_by_text(repository, outline, "ext_book", query_text="", keywords=set()) == []


def test_split_record_id_round_trips():
    assert split_record_id("ext_1/s2") == ("ext_1", "s2")
