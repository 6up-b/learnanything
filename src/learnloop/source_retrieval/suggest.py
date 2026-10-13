"""A labelled nearest-LO suggestion for a reader span without provenance (T6).

``learning_objects_for_span`` maps a span to the learning objects whose
provenance cites its section, and returns ``[]`` when none does. For such a
span this module ranks active learning objects by two lists fused by RRF:

* ``keyword``: BM25 of the span text over each LO's title, summary and its
  facets' titles and claims (no model);
* ``meaning``: the span's stored ``source_block/text`` vector against the
  stored ``facet/definition`` vectors (both ``retrieval-document``; Phase 1
  mean-centred cosine over the complete current facet index), each LO ranked by
  its best facet. Used only when both vectors exist for ``embedding.model``;
  never a paid call.

Every entry is labelled ``"label": "suggestion"``. A suggestion is display
only: it is never written as a candidate, a promotion target or a filing, so
nothing is grounded or measured on it (R1). The learner chooses.
"""
from __future__ import annotations

from collections.abc import Iterable
from contextlib import closing
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import IncompleteEmbeddingIndex, get_vector, retrieve
from learnloop.db.stores.source_block_fts import blocks_by_key, section_header_titles
from learnloop.practice_index.text import BM25, reciprocal_rank_fusion
from learnloop.reader.reader_progression import learning_objects_for_span
from learnloop.source_retrieval.recipes import (
    DOC_TASK_PREFIX,
    SOURCE_BLOCK_FIELD,
    SOURCE_BLOCK_KIND,
    SOURCE_BLOCK_RECIPE,
    SOURCE_RETRIEVAL_RECIPES,
    block_record_id,
    source_block_text,
)
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES
from learnloop.vault.models import LoadedVault, learning_object_facet_union

DEFAULT_LIMIT = 3


def _active_learning_objects(vault: LoadedVault) -> dict[str, Any]:
    return {lo_id: lo for lo_id, lo in sorted(vault.learning_objects.items()) if lo.status == "active"}


def _facets_by_lo(vault: LoadedVault, learning_objects: dict[str, Any]) -> dict[str, set[str]]:
    return {lo_id: {vault.canonical_facet_id(str(facet)) for facet in learning_object_facet_union(lo)}
            for lo_id, lo in learning_objects.items()}


def _lo_document(vault: LoadedVault, learning_object: Any, facets: Iterable[str]) -> str:
    parts = [learning_object.title or "", getattr(learning_object, "summary", "") or ""]
    for facet_id in sorted(facets):
        facet = vault.evidence_facets.get(facet_id)
        if facet is not None:
            parts.extend([facet.title or "", facet.claim or ""])
    return "\n".join(part for part in parts if part)


def _meaning_ranking(vault: LoadedVault, repository: Repository, block_text: str,
                     record_id: str, facets_by_lo: dict[str, set[str]]) -> tuple[list[str], str]:
    """LOs ranked by their best facet's cosine to the span; ``(ranking, status)``."""

    model_id = vault.config.embedding.model
    recipe = SOURCE_RETRIEVAL_RECIPES[SOURCE_BLOCK_RECIPE]
    facet_recipe = EMBEDDING_RECIPES["facet/definition"]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        vector = get_vector(connection, record_kind=SOURCE_BLOCK_KIND, record_id=record_id,
                            field=SOURCE_BLOCK_FIELD, content_hash=recipe.content_hash(block_text),
                            model_id=model_id, task_prefix=DOC_TASK_PREFIX)
        if vector is None:
            return [], "span_not_embedded"
        manifest = {record.record_id: record.content_hash for record in facet_recipe.records(vault)}
        if not manifest:
            return [], "no_facets"
        try:
            matches = retrieve(connection, record_kind=facet_recipe.record_kind, field=facet_recipe.field,
                               model_id=model_id, task_prefix=DOC_TASK_PREFIX, query=vector,
                               expected_records=manifest, limit=len(manifest))
        except IncompleteEmbeddingIndex:
            return [], "facet_index_incomplete"
        except ValueError:
            return [], "dimension_mismatch"
    facet_rank = {match.record_id: position for position, match in enumerate(matches, start=1)}
    best = {lo_id: min((facet_rank[f] for f in facets if f in facet_rank), default=None)
            for lo_id, facets in facets_by_lo.items()}
    ranked = sorted((rank, lo_id) for lo_id, rank in best.items() if rank is not None)
    return [lo_id for _rank, lo_id in ranked], "used"


def suggest_learning_objects(
    vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Provenance-linked LOs, or (when there are none) labelled nearest-LO suggestions."""

    provenance = learning_objects_for_span(vault, repository, extraction_id=extraction_id, span_id=span_id)
    result: dict[str, Any] = {"extraction_id": extraction_id, "span_id": span_id,
                              "provenance": provenance, "suggestions": []}
    config = vault.config.source_retrieval
    if provenance:
        result["status"] = "provenance"
        return result
    if not config.enabled or not config.suggest_learning_objects:
        result["status"] = "disabled"
        return result
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        block = blocks_by_key(connection, [(extraction_id, span_id)]).get((extraction_id, span_id))
        titles = section_header_titles(connection, extraction_id)
    if block is None or not block.text.strip():
        result["status"] = "span_not_found"
        return result
    learning_objects = _active_learning_objects(vault)
    if not learning_objects:
        result["status"] = "no_learning_objects"
        return result
    facets_by_lo = _facets_by_lo(vault, learning_objects)
    lists: dict[str, list[str]] = {}
    keyword = BM25({lo_id: _lo_document(vault, lo, facets_by_lo[lo_id])
                    for lo_id, lo in learning_objects.items()}).ranking(block.text)
    if keyword:
        lists["keyword"] = keyword
    meaning, meaning_status = _meaning_ranking(
        vault, repository, source_block_text(block, titles), block_record_id(extraction_id, span_id),
        facets_by_lo)
    if meaning:
        lists["meaning"] = meaning
    order, ranks = reciprocal_rank_fusion(lists, k=config.rrf_k)
    result["status"] = "suggested" if order else "no_match"
    result["meaning"] = meaning_status
    result["suggestions"] = [
        {"learning_object_id": lo_id, "title": learning_objects[lo_id].title, "label": "suggestion",
         "basis": sorted(ranks[lo_id])}
        for lo_id in order[: max(0, limit)]
    ]
    return result


def suggested_learning_objects(vault: LoadedVault, repository: Repository, *,
                               extraction_id: str, span_id: str) -> list[dict[str, Any]]:
    """The tutor's injection seam: the labelled suggestions only."""

    return suggest_learning_objects(vault, repository, extraction_id=extraction_id,
                                    span_id=span_id)["suggestions"]


__all__ = ["DEFAULT_LIMIT", "suggest_learning_objects", "suggested_learning_objects"]
