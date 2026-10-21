"""Hybrid span retrieval: ranked lists fused by reciprocal rank (no thresholds).

Lists, each restricted to the scope before fusion:

* ``keyword``: FTS5 BM25 over ``source_block_fts`` for the query (and context);
* ``substring``: today's library match (``instr``) in document order, when asked;
* ``meaning``: dense ranking of the query vector over the scope's stored
  ``source_block/text`` vectors (deep searches; the extractions whose every
  block is embedded, labelled ``partial`` when that is not all of them);
* ``rewrite_keyword`` / ``rewrite_meaning``: the same two for the LLM-rewritten
  query, when a conceptual question was rewritten;
* caller lists (the tutor adds its learning objects' linked spans).

Two ways to turn the lists into one candidate pool (``source_retrieval.pool``,
owner 2026-10-12):

* ``hybrid_rrf``: Phase 5b's ``reciprocal_rank_fusion`` of every list: ranks
  only, so no BM25 or cosine cutoff is ever hand-set (R4).
* ``dense_plus_bm25``: the dense top ``k`` (``meaning``, fused with
  ``rewrite_meaning`` when the question was rewritten), then the BM25 top ``m``
  that dense did not already return, then the same for each caller list (the
  tutor's linked spans). Ranked dense first for display; BM25 only widens the
  pool, and on consequential paths the verification picks from all of it. The
  T6 evaluation found dense alone at least as good as the fusion on generated
  questions; BM25's job is the exact terms dense can miss. When the scope's
  dense index is not complete (or no query vector exists) the search falls
  back to ``hybrid_rrf`` and says so.

Each hit keeps its rank in every list, and the result says which kinds of
evidence were used (``basis``) and how the pool was built (``pool``), so
consumers can label it honestly. Paid steps are timed (``timings_ms``).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import time
from typing import Any

import numpy as np

from learnloop.ai.spend import SpendBudget
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
from learnloop.source_retrieval.corpus import Scope, role_keys, role_proposal_keys
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
#: Candidate-pool modes (``source_retrieval.pool``).
POOL_HYBRID_RRF = "hybrid_rrf"
POOL_DENSE_PLUS_BM25 = "dense_plus_bm25"
POOL_MODES = (POOL_DENSE_PLUS_BM25, POOL_HYBRID_RRF)
#: Lists that never widen a dense_plus_bm25 pool (they are the dense side, or
#: the typing search's literal match).
_NON_WIDENING = frozenset({"meaning", "rewrite_meaning", "rewrite_keyword", "substring"})


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
    #: In a dense_plus_bm25 pool: ``dense``, or the list that widened it with
    #: this hit (``keyword``, a caller list such as ``provenance``). None in a
    #: hybrid_rrf pool.
    pool_role: str | None = None

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
    #: How the candidate pool was built: mode, fallback reason, counts.
    pool: dict[str, Any] = field(default_factory=dict)
    #: Wall time of each step in milliseconds (rewrite, query_embedding, total).
    timings_ms: dict[str, int] = field(default_factory=dict)
    #: Per list, whether it reached its source's end at the depth asked
    #: (canonical sources §8.3.4: paging ends only on exhaustion).
    list_ends: dict[str, bool] = field(default_factory=dict)
    #: The whole pool's order: in a hybrid_rrf pool every key any list ranked
    #: (the fused order), in a dense_plus_bm25 pool the pool itself; not just
    #: the hits.
    fused_keys: list[SpanKey] = field(default_factory=list)
    #: The depth each list was asked for.
    list_depths: dict[str, int] = field(default_factory=dict)
    roles: list[str] = field(default_factory=list)
    #: With ``roles``: how many spans each kind of role evidence admitted
    #: (ingest hints, RW4e proposals, low-confidence proposals).
    role_basis: dict[str, int] = field(default_factory=dict)

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
        value = {"basis": self.basis, "lists": list(self.lists), "scope": self.scope,
                 "dense": self.dense, "query_embedding": self.query_embedding,
                 "rewrite": self.rewrite, "notes": list(self.notes), "hits": len(self.hits),
                 "pool": dict(self.pool), "timings_ms": dict(self.timings_ms)}
        if self.roles:
            value["roles"] = list(self.roles)
            value["role_basis"] = dict(self.role_basis)
        return value


def _hit(block: BlockRow, scope: Scope, ranks: Mapping[str, int], titles: Mapping[str, str],
         pool_role: str | None = None) -> SpanHit:
    source = scope.extractions[block.extraction_id]
    return SpanHit(
        extraction_id=block.extraction_id, span_id=block.span_id, source_id=source.source_id,
        source_title=source.title, text=block.text, block_type=block.block_type,
        section_path=section_path(block, titles), page=block.page, ordinal=block.ordinal,
        ranks=dict(ranks), pool_role=pool_role,
    )


def _ms(started: float) -> int:
    return int(round((time.monotonic() - started) * 1000))


def dense_plus_bm25(
    lists: Mapping[str, Sequence[str]], *, dense_k: int, extras_m: int, rrf_k: int,
    widening: Sequence[str] = ("keyword",),
) -> tuple[list[str], dict[str, str], dict[str, dict[str, int]]]:
    """The dense top ``dense_k`` then each widening list's top ``extras_m`` not
    already in the pool (deduplicated), in that order.

    Returns ``(order, roles, ranks)``: the pool's record ids, each id's pool
    role (``dense`` or the list that added it) and its rank in every list.
    The dense side is ``meaning``, fused by rank with ``rewrite_meaning`` when
    both exist.
    """

    dense_lists = {name: lists[name] for name in ("meaning", "rewrite_meaning") if lists.get(name)}
    if len(dense_lists) > 1:
        dense_order, _ = reciprocal_rank_fusion(dense_lists, k=rrf_k)
    else:
        dense_order = list(next(iter(dense_lists.values()), []))
    order = list(dict.fromkeys(dense_order))[: max(0, dense_k)]
    roles = {record_id: "dense" for record_id in order}
    seen = set(order)
    for name in widening:
        for record_id in list(lists.get(name) or [])[: max(0, extras_m)]:
            if record_id not in seen:
                seen.add(record_id)
                order.append(record_id)
                roles[record_id] = name
    ranks: dict[str, dict[str, int]] = {}
    for name, ranking in sorted(lists.items()):
        for position, record_id in enumerate(ranking, start=1):
            if record_id in seen:
                ranks.setdefault(record_id, {}).setdefault(name, position)
    return order, roles, ranks


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
    deadline: float | None = None,
    budget: SpendBudget | None = None,
    pool: str | None = None,
    pool_dense: int | None = None,
    pool_extras: int | None = None,
    roles: Sequence[str] = (),
    list_depth: int | Mapping[str, int] = LIST_DEPTH,
) -> SpanSearch:
    """Hybrid retrieval over ``scope``; never raises for a paid step's failure.

    ``rewrite`` None follows the config and the conceptual-question gate.
    ``query_vectors`` (``{"query": v, "rewrite": v}``) and ``rewritten`` let a
    benchmark reuse vectors and rewrites it already paid for. ``deadline``
    (``time.monotonic()``) time-boxes the paid steps: the rewrite's and the
    query embedding's requests carry the remaining time as their timeout, and
    neither starts after it.
    ``budget`` puts both paid steps under one caller's caps.

    ``pool`` (None: ``source_retrieval.pool``) chooses how the lists become
    one pool; a ``dense_plus_bm25`` pool takes the dense top ``pool_dense``
    (default ``limit`` minus the extras) and up to ``pool_extras`` (default
    ``source_retrieval.pool_keyword_extras``) from each widening list. It
    needs a deep search over a complete dense index, else it falls back to
    ``hybrid_rrf`` (``result.pool["fallback"]`` says why).

    Canonical sources S1: ``roles`` is a positive filter (every list keeps only
    blocks whose effective role hint is one of them); ``list_depth`` (one depth,
    or one per list name) deepens recall, which ``limit`` never does, and the
    result says per list whether it reached its source's end (``list_ends``)
    and gives the whole pool's order (``fused_keys``). The defaults keep every
    existing caller byte-identical. A caller that pages by list exhaustion or
    walks the whole fused order passes ``pool="hybrid_rrf"``: a
    ``dense_plus_bm25`` pool is cut to its dense top and extras whatever the
    depth asked.
    """

    config = vault.config.source_retrieval
    started = time.monotonic()
    text = normalize_query(query)[:MAX_QUERY_CHARS]
    result = SpanSearch(query=text, scope=scope.describe(), roles=list(roles))
    if len(text) < 2 or not scope.extractions:
        return result
    retrieval_text = text if not context_text else f"{text} {normalize_query(context_text)}"
    extraction_ids = sorted(scope.extractions)
    lists: dict[str, list[SpanKey]] = {}

    def depth(name: str) -> int:
        if isinstance(list_depth, Mapping):
            return int(list_depth.get(name, LIST_DEPTH))
        return int(list_depth)

    permitted_roles: set[SpanKey] | None = None
    if roles:
        # Ingest's effective hints and the Reader's RW4e role proposals; a
        # low-confidence proposal only when nothing better exists (§9.1).
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            hinted = role_keys(connection, extraction_ids, roles)
        proposed, low = role_proposal_keys(vault, repository, extraction_ids, roles)
        permitted_roles = hinted | proposed
        result.role_basis = {"hints": len(hinted), "proposals": len(proposed - hinted), "low_confidence": 0}
        # "Better" is a confident passage this scope can return (Codex review F3).
        if low and not any(scope.allows(*key) for key in permitted_roles):
            permitted_roles = set(low)
            result.role_basis["low_confidence"] = len(low)

    def keep(key: SpanKey) -> bool:
        return scope.allows(*key) and (permitted_roles is None or key in permitted_roles)

    def allowed(keys: Sequence[SpanKey]) -> list[SpanKey]:
        return [key for key in dict.fromkeys(keys) if keep(key)]

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        raw = search_blocks(connection, retrieval_text, extraction_ids=extraction_ids, limit=depth("keyword"),
                            prefix_last=prefix_last)
        result.list_depths["keyword"] = depth("keyword")
        # Counted before the scope filter: fewer rows than asked means the
        # keyword source itself has no more matches.
        result.list_ends["keyword"] = len(raw) < depth("keyword")
        keyword = allowed([(m.extraction_id, m.span_id) for m in raw])
        if keyword:
            lists["keyword"] = keyword
    if include_substring:
        rows = repository.search_source_blocks(query=text, extraction_ids=extraction_ids,
                                               limit=depth("substring"))
        result.list_depths["substring"] = depth("substring")
        result.list_ends["substring"] = len(rows) < depth("substring")
        substring = allowed([(str(row["extraction_id"]), str(row["span_id"])) for row in rows])
        if substring:
            lists["substring"] = substring

    if deep:
        wants_rewrite = (config.query_rewrite and is_conceptual(text)) if rewrite is None else rewrite
        rewrite_result = rewritten
        if wants_rewrite and rewrite_result is None:
            step = time.monotonic()
            rewrite_result = rewrite_query(vault, repository, text, context=context_text,
                                           client=rewrite_client, owner_id=owner_id,
                                           deadline=deadline, budget=budget)
            result.timings_ms["rewrite"] = _ms(step)
        if rewrite_result is not None:
            result.rewrite = rewrite_result.describe()
        elif rewrite is None and not config.query_rewrite:
            result.rewrite = {"status": "disabled"}
        else:
            result.rewrite = {"status": "not_needed"}
        if rewrite_result is not None and rewrite_result.ok:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                raw_rewrite = search_blocks(connection, rewritten_text(rewrite_result),
                                            extraction_ids=extraction_ids, limit=depth("rewrite_keyword"))
            result.list_depths["rewrite_keyword"] = depth("rewrite_keyword")
            result.list_ends["rewrite_keyword"] = len(raw_rewrite) < depth("rewrite_keyword")
            rewritten_keyword = allowed([(m.extraction_id, m.span_id) for m in raw_rewrite])
            if rewritten_keyword:
                lists["rewrite_keyword"] = rewritten_keyword
        if query_vectors is None and embedder is None and not vault.config.embedding.enabled:
            # No query can be embedded, so the stored index is not even read.
            index = DenseIndex("disabled", "embeddings are disabled (embedding.enabled = false)")
        else:
            index = load_dense_index(vault, repository, scope)
        result.dense = index.describe()
        if index.usable:
            if index.status == "partial" and index.reason:
                result.notes.append(index.reason)
            texts = {"query": retrieval_text}
            if rewrite_result is not None and rewrite_result.ok:
                texts["rewrite"] = rewritten_text(rewrite_result)
            if query_vectors is not None:
                vectors = {key: value for key, value in query_vectors.items() if key in texts}
                result.query_embedding = {"status": "provided"}
            elif deadline is not None and time.monotonic() >= deadline:
                vectors = {}
                result.query_embedding = {"status": "timed_out", "reason": "the retrieval time box ran out"}
            else:
                step = time.monotonic()
                vectors, result.query_embedding = embed_query_texts(
                    vault, repository, texts, embedder=embedder, owner_id=owner_id, budget=budget,
                    deadline=deadline)
                result.timings_ms["query_embedding"] = _ms(step)

            def permit(record_id: str) -> bool:
                return keep(split_record_id(record_id))

            for name, key in (("meaning", "query"), ("rewrite_meaning", "rewrite")):
                vector = vectors.get(key)
                if vector is None:
                    continue
                try:
                    ranked = [split_record_id(record_id) for record_id, _score in
                              index.rank(vector, limit=depth(name), allow=permit)]
                except ValueError:  # a query vector of another width: never ranked
                    result.notes.append(f"{name}: the query vector does not match the index width")
                    continue
                # The dense rank applies the scope filter before counting.
                result.list_depths[name] = depth(name)
                result.list_ends[name] = len(ranked) < depth(name)
                if ranked:
                    lists[name] = ranked
        elif index.reason:
            result.notes.append(index.reason)
    for name, keys in (extra_lists or {}).items():
        extra = allowed(list(keys))
        result.list_ends[name] = True  # complete as passed
        if extra:
            lists[name] = extra

    by_id = {name: [block_record_id(*key) for key in keys] for name, keys in lists.items()}
    mode = pool or config.pool
    if mode not in POOL_MODES:
        raise ValueError(f"Unknown source_retrieval pool {mode!r}; expected one of {', '.join(POOL_MODES)}")
    fallback = None
    if mode == POOL_DENSE_PLUS_BM25 and deep:  # a typing search is keyword only either way
        dense_status = (result.dense or {}).get("status")
        if dense_status != "ready":
            fallback = f"the dense index is {dense_status or 'unused'}, not complete"
        elif not by_id.get("meaning"):
            fallback = "no query vector, so no meaning list"
    pool_roles: dict[str, str] = {}
    if mode == POOL_DENSE_PLUS_BM25 and deep and fallback is None:
        extras_m = config.pool_keyword_extras if pool_extras is None else pool_extras
        dense_k = pool_dense if pool_dense is not None else max(1, limit - extras_m)
        widening = ["keyword", *sorted(name for name in by_id if name not in _NON_WIDENING | {"keyword"})]
        order, pool_roles, ranks = dense_plus_bm25(by_id, dense_k=dense_k, extras_m=extras_m,
                                                   rrf_k=config.rrf_k, widening=widening)
        result.pool = {"mode": POOL_DENSE_PLUS_BM25, "fallback": None, "dense_k": dense_k,
                       "extras_m": extras_m, "dense": sum(1 for role in pool_roles.values() if role == "dense"),
                       "extras": {name: sum(1 for role in pool_roles.values() if role == name)
                                  for name in widening if any(role == name for role in pool_roles.values())}}
        wanted_ids = order
    else:
        order, ranks = reciprocal_rank_fusion(by_id, k=config.rrf_k)
        result.pool = {"mode": POOL_HYBRID_RRF, "requested": mode,
                       "fallback": fallback if mode == POOL_DENSE_PLUS_BM25 else None}
        wanted_ids = order[: max(limit * 2, limit + 20)]
    result.lists = sorted(lists)
    result.fused_keys = [split_record_id(record_id) for record_id in order]
    wanted = [split_record_id(record_id) for record_id in wanted_ids]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        blocks = blocks_by_key(connection, wanted)
        titles = {extraction_id: section_header_titles(connection, extraction_id)
                  for extraction_id in sorted({key[0] for key in blocks})}
    cap = len(wanted) if pool_roles else limit
    for key in wanted:
        block = blocks.get(key)
        if block is None:  # an index row whose block is gone: never shown
            continue
        record_id = block_record_id(*key)
        result.hits.append(_hit(block, scope, ranks[record_id], titles[key[0]], pool_roles.get(record_id)))
        if len(result.hits) >= cap:
            break
    result.timings_ms["total"] = _ms(started)
    return result


__all__ = [
    "LIST_DEPTH",
    "POOL_DENSE_PLUS_BM25",
    "POOL_HYBRID_RRF",
    "POOL_MODES",
    "SpanHit",
    "SpanKey",
    "SpanSearch",
    "dense_plus_bm25",
    "search_spans",
]
