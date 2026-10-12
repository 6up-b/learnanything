"""Hybrid span retrieval: ranked lists fused by reciprocal rank (no thresholds).

Lists, each restricted to the scope before fusion:

* ``keyword``: FTS5 BM25 over ``source_block_fts`` for the query (and context);
* ``substring``: today's library match (``instr``) in document order, when asked;
* ``meaning``: dense ranking of the query vector over the scope's stored
  ``source_block/text`` vectors (deep searches with a complete index);
* ``rewrite_keyword`` / ``rewrite_meaning``: the same two for the LLM-rewritten
  query, when a conceptual question was rewritten;
* caller lists (the tutor adds its learning objects' linked spans).

Fusion is Phase 5b's ``reciprocal_rank_fusion``: ranks only, so no BM25 or
cosine cutoff is ever hand-set (R4). Each hit keeps its rank in every list, and
the result says which kinds of evidence were used (``basis``), so consumers can
label it honestly.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    BlockRow,
    blocks_by_key,
    search_blocks,
    section_header_titles,
)
from learnloop.practice_index.query_vectors import normalize_query
from learnloop.practice_index.text import reciprocal_rank_fusion
from learnloop.source_retrieval.corpus import Scope
from learnloop.source_retrieval.dense import DenseIndex, load_dense_index
from learnloop.source_retrieval.queries import (
    MAX_QUERY_CHARS,
    Rewrite,
    embed_query_texts,
    is_conceptual,
    rewrite_query,
    rewritten_text,
)
from learnloop.source_retrieval.recipes import block_record_id, section_path, split_record_id
from learnloop.vault.models import LoadedVault

#: Each list contributes at most this many candidates to the fusion.
LIST_DEPTH = 200
SpanKey = tuple[str, str]


@dataclass
class SpanHit:
    extraction_id: str
    span_id: str
    source_id: str
    source_title: str
    text: str
    block_type: str
    section_path: list[str]
    page: int | None
    ordinal: int
    ranks: dict[str, int] = field(default_factory=dict)

    @property
    def key(self) -> SpanKey:
        return (self.extraction_id, self.span_id)

    @property
    def record_id(self) -> str:
        return block_record_id(self.extraction_id, self.span_id)

    @property
    def section(self) -> str | None:
        return self.section_path[-1] if self.section_path else None


@dataclass
class SpanSearch:
    query: str
    hits: list[SpanHit] = field(default_factory=list)
    lists: list[str] = field(default_factory=list)
    scope: dict[str, Any] = field(default_factory=dict)
    dense: dict[str, Any] = field(default_factory=dict)
    query_embedding: dict[str, Any] = field(default_factory=dict)
    rewrite: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def basis(self) -> str:
        """Which kinds of evidence ranked the hits: keyword, meaning, rewrite."""

        kinds = []
        if {"keyword", "substring", "rewrite_keyword"} & set(self.lists):
            kinds.append("keyword")
        if {"meaning", "rewrite_meaning"} & set(self.lists):
            kinds.append("meaning")
        if {"rewrite_keyword", "rewrite_meaning"} & set(self.lists):
            kinds.append("rewrite")
        extra = sorted(set(self.lists) - {"keyword", "substring", "meaning",
                                          "rewrite_keyword", "rewrite_meaning"})
        return "+".join(kinds + extra) or "none"

    def describe(self) -> dict[str, Any]:
        return {"basis": self.basis, "lists": list(self.lists), "scope": self.scope,
                "dense": self.dense, "query_embedding": self.query_embedding,
                "rewrite": self.rewrite, "notes": list(self.notes), "hits": len(self.hits)}


def _hit(block: BlockRow, scope: Scope, ranks: Mapping[str, int], titles: Mapping[str, str]) -> SpanHit:
    source = scope.extractions[block.extraction_id]
    return SpanHit(
        extraction_id=block.extraction_id, span_id=block.span_id, source_id=source.source_id,
        source_title=source.title, text=block.text, block_type=block.block_type,
        section_path=section_path(block, titles), page=block.page, ordinal=block.ordinal,
        ranks=dict(ranks),
    )


def search_spans(
    vault: LoadedVault,
    repository: Repository,
    query: str,
    scope: Scope,
    *,
    limit: int = 40,
    deep: bool = True,
    rewrite: bool | None = None,
    context_text: str | None = None,
    include_substring: bool = False,
    prefix_last: bool = False,
    extra_lists: Mapping[str, Sequence[SpanKey]] | None = None,
    embedder: Any | None = None,
    rewrite_client: Any | None = None,
    query_vectors: Mapping[str, np.ndarray] | None = None,
    rewritten: Rewrite | None = None,
    owner_id: str = "",
) -> SpanSearch:
    """Hybrid retrieval over ``scope``; never raises for a paid step's failure.

    ``rewrite`` None follows the config and the conceptual-question gate.
    ``query_vectors`` (``{"query": v, "rewrite": v}``) and ``rewritten`` let a
    benchmark reuse vectors and rewrites it already paid for.
    """

    config = vault.config.source_retrieval
    text = normalize_query(query)[:MAX_QUERY_CHARS]
    result = SpanSearch(query=text, scope=scope.describe())
    if len(text) < 2 or not scope.extractions:
        return result
    retrieval_text = text if not context_text else f"{text} {normalize_query(context_text)}"
    extraction_ids = sorted(scope.extractions)
    lists: dict[str, list[SpanKey]] = {}

    def allowed(keys: Sequence[SpanKey]) -> list[SpanKey]:
        return [key for key in dict.fromkeys(keys) if scope.allows(*key)]

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        keyword = allowed([(m.extraction_id, m.span_id) for m in search_blocks(
            connection, retrieval_text, extraction_ids=extraction_ids, limit=LIST_DEPTH,
            prefix_last=prefix_last)])
        if keyword:
            lists["keyword"] = keyword
    if include_substring:
        rows = repository.search_source_blocks(query=text, extraction_ids=extraction_ids, limit=LIST_DEPTH)
        substring = allowed([(str(row["extraction_id"]), str(row["span_id"])) for row in rows])
        if substring:
            lists["substring"] = substring

    if deep:
        wants_rewrite = (config.query_rewrite and is_conceptual(text)) if rewrite is None else rewrite
        rewrite_result = rewritten
        if wants_rewrite and rewrite_result is None:
            rewrite_result = rewrite_query(vault, repository, text, context=context_text,
                                           client=rewrite_client, owner_id=owner_id)
        if rewrite_result is not None:
            result.rewrite = rewrite_result.describe()
        elif rewrite is None and not config.query_rewrite:
            result.rewrite = {"status": "disabled"}
        else:
            result.rewrite = {"status": "not_needed"}
        if rewrite_result is not None and rewrite_result.ok:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                rewritten_keyword = allowed([(m.extraction_id, m.span_id) for m in search_blocks(
                    connection, rewritten_text(rewrite_result), extraction_ids=extraction_ids,
                    limit=LIST_DEPTH)])
            if rewritten_keyword:
                lists["rewrite_keyword"] = rewritten_keyword
        if query_vectors is None and embedder is None and not vault.config.embedding.enabled:
            # No query can be embedded, so the stored index is not even read.
            index = DenseIndex("disabled", "embeddings are disabled (embedding.enabled = false)")
        else:
            index = load_dense_index(vault, repository, scope)
        result.dense = index.describe()
        if index.ready:
            texts = {"query": retrieval_text}
            if rewrite_result is not None and rewrite_result.ok:
                texts["rewrite"] = rewritten_text(rewrite_result)
            if query_vectors is not None:
                vectors = {key: value for key, value in query_vectors.items() if key in texts}
                result.query_embedding = {"status": "provided"}
            else:
                vectors, result.query_embedding = embed_query_texts(
                    vault, repository, texts, embedder=embedder, owner_id=owner_id)

            def permit(record_id: str) -> bool:
                return scope.allows(*split_record_id(record_id))

            for name, key in (("meaning", "query"), ("rewrite_meaning", "rewrite")):
                vector = vectors.get(key)
                if vector is None:
                    continue
                try:
                    ranked = [split_record_id(record_id) for record_id, _score in
                              index.rank(vector, limit=LIST_DEPTH, allow=permit)]
                except ValueError:  # a query vector of another width: never ranked
                    result.notes.append(f"{name}: the query vector does not match the index width")
                    continue
                if ranked:
                    lists[name] = ranked
        elif index.reason:
            result.notes.append(index.reason)
    for name, keys in (extra_lists or {}).items():
        extra = allowed(list(keys))
        if extra:
            lists[name] = extra

    order, ranks = reciprocal_rank_fusion(
        {name: [block_record_id(*key) for key in keys] for name, keys in lists.items()},
        k=config.rrf_k,
    )
    result.lists = sorted(lists)
    wanted = [split_record_id(record_id) for record_id in order[: max(limit * 2, limit + 20)]]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        blocks = blocks_by_key(connection, wanted)
        titles = {extraction_id: section_header_titles(connection, extraction_id)
                  for extraction_id in sorted({key[0] for key in blocks})}
    for key in wanted:
        block = blocks.get(key)
        if block is None:  # an index row whose block is gone: never shown
            continue
        result.hits.append(_hit(block, scope, ranks[block_record_id(*key)], titles[key[0]]))
        if len(result.hits) >= limit:
            break
    return result


__all__ = ["LIST_DEPTH", "SpanHit", "SpanKey", "SpanSearch", "search_spans"]
