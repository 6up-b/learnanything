"""Library search ("where did I read that?") beyond ``instr()`` (Slice 2 T6).

* **While typing** (the default): FTS5 BM25 over every reader-enabled source,
  the last word matched as a prefix, fused (RRF) with today's substring match,
  so every block the old search found can still rank. Local, no model.
* **Deep** (the learner presses Enter): also dense retrieval over the stored
  source-block vectors when that index is complete (one cached query
  embedding), and for a conceptual question the LLM-rewritten query.

Search results are display only: nothing is verified or written, and the
response says which evidence ranked the hits (``basis``) so the UI never claims
more. ``source_retrieval.enabled = false`` returns today's substring search
exactly.
"""
from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import query_terms
from learnloop.reader.source_search import MAX_HITS, search_sources
from learnloop.source_retrieval.corpus import library_scope
from learnloop.source_retrieval.search import search_spans
from learnloop.vault.models import LoadedVault

_SNIPPET_RADIUS = 90


def _snippet(text: str, query: str) -> str:
    """Around the first query term the block contains; else its opening."""

    flat = " ".join(text.split())
    lowered = flat.lower()
    positions = [(lowered.find(term), term) for term in [query.strip().lower(), *query_terms(query)] if term]
    found = [(at, term) for at, term in positions if at >= 0]
    if not found:
        return flat[: 2 * _SNIPPET_RADIUS] + ("…" if len(flat) > 2 * _SNIPPET_RADIUS else "")
    at, term = min(found)
    start = max(0, at - _SNIPPET_RADIUS)
    end = min(len(flat), at + len(term) + _SNIPPET_RADIUS)
    return f"{'…' if start > 0 else ''}{flat[start:end]}{'…' if end < len(flat) else ''}"


def search_library(
    vault: LoadedVault, repository: Repository, *, query: str, limit: int = MAX_HITS,
    deep: bool = False, embedder: Any | None = None, rewrite_client: Any | None = None,
) -> dict[str, Any]:
    """The library search response: today's shape plus ``basis`` and ``retrieval``."""

    config = vault.config.source_retrieval
    if not config.enabled:
        return search_sources(repository, query=query, limit=limit)
    needle = (query or "").strip()
    if len(needle) < 2:
        return {"query": needle, "hits": [], "searched_sources": 0, "basis": "none", "deep": deep}
    scope = library_scope(repository)
    search = search_spans(
        vault, repository, needle, scope, limit=limit, deep=deep, include_substring=True,
        prefix_last=not deep, embedder=embedder, rewrite_client=rewrite_client,
        owner_id="library",
    )
    hits = [{
        "source_id": hit.source_id,
        "source_title": hit.source_title,
        "extraction_id": hit.extraction_id,
        "span_id": hit.span_id,
        "section": hit.section,
        "page": hit.page,
        "snippet": _snippet(hit.text, needle),
        "matched_by": sorted(hit.ranks),
    } for hit in search.hits]
    return {
        "query": needle, "hits": hits, "searched_sources": len(scope.extractions),
        "basis": search.basis, "deep": deep, "retrieval": search.describe(),
    }


__all__ = ["search_library"]
