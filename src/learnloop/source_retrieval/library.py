"""Library search ("where did I read that?") beyond ``instr()`` (Slice 2 T6).

* **While typing** (the default): FTS5 BM25 over every reader-enabled source,
  the last word matched as a prefix, fused (RRF) with today's substring match,
  so every block the old search found can still rank. Local, no model. The
  response says whether pressing Enter would also search by meaning
  (``meaning_search``: the stored index's coverage, cached until the library
  or its vectors change, and the embedding route's readiness, read without
  any call).
* **Deep** (the learner presses Enter): also dense retrieval over the stored
  source-block vectors of every fully embedded source (one cached query
  embedding), and for a conceptual question the LLM-rewritten query, inside
  ``retrieval_timeout_seconds``.

Search results are display only: nothing is verified or written, and the
response says which evidence ranked the hits (``basis``) so the UI never claims
more. ``source_retrieval.enabled = false`` returns today's substring search
exactly. :func:`plan_library_search` is the dry run of a deep search: its
planned calls and cost, with no call and no write.
"""
from __future__ import annotations

import time
from typing import Any

from learnloop.ai.routing import MANUAL_PROVIDER, provider_for_task, runtime_for_provider
from learnloop.ai.spend import SpendBudget, SpendCaps
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import query_terms
from learnloop.practice_index.paid import PaidCalls, estimated_call_tokens, plan_route
from learnloop.ops.embedding_backfill import estimated_tokens
from learnloop.practice_index.query_vectors import cached_query_vectors, normalize_query, query_embedding_price
from learnloop.reader.source_search import MAX_HITS, search_sources
from learnloop.source_retrieval.contracts import QueryRewrite
from learnloop.source_retrieval.corpus import Scope, library_scope
from learnloop.source_retrieval.dense import dense_coverage
from learnloop.source_retrieval.queries import (
    LARGEST_QUERY_TEXT,
    MAX_QUERY_CHARS,
    QUERY_EMBEDDING_CAPS,
    QUERY_RECORD_KIND,
    is_conceptual,
    query_id,
    rewrite_caps,
    rewrite_prompt,
    route_skip,
)
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


def embedding_route_problem(vault: LoadedVault) -> str | None:
    """Why the ``embedding`` route cannot embed a query now, or None (no call).

    The route's readiness as the query embedder will resolve it (embeddings
    never fall back to another provider): a route is configured, and its
    profile is ready (for OpenRouter, the API key is set). A provider that is
    down is only found out by calling it; Enter then says so.
    """

    selection = provider_for_task(vault.config, "embedding")
    provider = selection.provider_name
    if not provider or provider == MANUAL_PROVIDER:
        return "No provider is routed for embedding; set ai.routing.embedding."
    runtime = runtime_for_provider(vault.root, vault.config, provider, task="embedding")
    return None if runtime.ready else (runtime.message or f"{provider} is not ready")


def meaning_search_state(vault: LoadedVault, repository: Repository, scope: Scope, *,
                         embedder: Any | None = None) -> dict[str, Any]:
    """Whether a deep search would rank by meaning, and over how much of the scope.

    No call and no vector bytes: the stored index's per-source coverage, the
    embedding switch, a known query-embedding price and (unless an embedder is
    injected) the embedding route's readiness. ``status`` is ``ready`` or
    ``partial`` exactly when Enter would run a meaning search.
    """

    model_id = vault.config.embedding.model
    if not vault.config.embedding.enabled:
        return {"status": "disabled", "reason": "embeddings are disabled (embedding.enabled = false)",
                "sources": 0, "sources_covered": 0, "blocks": 0, "blocks_covered": 0}
    index = dense_coverage(vault, repository, scope)
    state = {"status": index.status, "reason": index.reason, "sources": index.sources,
             "sources_covered": index.sources_covered, "blocks": index.expected,
             "blocks_covered": index.covered}
    price, _source = query_embedding_price(
        model_id, vault.config.source_retrieval.query_embedding_price_per_million)
    if index.usable and price is None:
        state.update(status="unavailable", reason=(
            f"unknown query-embedding price for {model_id}; set "
            "source_retrieval.query_embedding_price_per_million"))
    elif index.usable and embedder is None:
        problem = embedding_route_problem(vault)
        if problem is not None:
            state.update(status="unavailable", reason=f"the embedding route is not ready: {problem}")
    return state


def search_library(
    vault: LoadedVault, repository: Repository, *, query: str, limit: int = MAX_HITS,
    deep: bool = False, embedder: Any | None = None, rewrite_client: Any | None = None,
    budget: SpendBudget | None = None,
) -> dict[str, Any]:
    """The library search response: today's shape plus ``basis``, ``meaning_search``
    and ``retrieval``. ``budget`` puts a deep search's paid steps under one
    caller's caps (``learnloop sources search``)."""

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
        owner_id="library", deadline=(time.monotonic() + config.retrieval_timeout_seconds) if deep else None,
        budget=budget, consumer="library",
    )
    # Local contextual retrieval P1 (Codex review F9): the results shown are
    # this consumer's delivery (nothing is logged while no new space is on).
    from learnloop.source_retrieval.feedback import deliver

    shown = [search.hits[index] for index in deliver(vault, repository, search, [hit.key for hit in search.hits])]
    hits = [{
        "source_id": hit.source_id,
        "source_title": hit.source_title,
        "extraction_id": hit.extraction_id,
        "span_id": hit.span_id,
        "section": hit.section,
        "page": hit.page,
        "snippet": _snippet(hit.text, needle),
        "matched_by": sorted(hit.ranks),
    } for hit in shown]
    response = {
        "query": needle, "hits": hits, "searched_sources": len(scope.extractions),
        "basis": search.basis, "deep": deep,
        "meaning_search": meaning_search_state(vault, repository, scope, embedder=embedder),
        "retrieval": search.describe(),
    }
    receipt = (search.space_selection or {}).get("receipt_id")
    if receipt and (search.space_selection or {}).get("logged"):
        # The result's receipt, sent back when the learner opens a hit
        # (``reader.retrieval_open``; Codex review F11). Absent unless a new
        # embedding space is on and the search was logged.
        response["retrieval_receipt_id"] = receipt
    return response


#: structural: the texts a deep search embeds per query encoder (the question and its rewrite).
QUERY_TEXTS = 2


def deep_search_caps(*, max_calls: int, max_tokens: int, max_cost_usd: float) -> SpendCaps:
    """One budget for a deep search's paid steps: the rewrite (and its retry) and
    each paid query encoder's embedding of the question and its rewrite.

    The candidate allowance is structural, sized for every paid query encoder
    the resolver may ask (Qwen's and the hosted fallback's; Codex re-review
    F17): the caller's explicit limits (calls, tokens, dollars) are what bound
    the search."""

    from learnloop.source_retrieval.spaces import PAID_QUERY_SPACES

    return SpendCaps(max_candidates=1 + QUERY_TEXTS * len(PAID_QUERY_SPACES), max_pairs=0, max_retries=1,
                     max_calls=max_calls, max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd)


def plan_library_search(vault: LoadedVault, repository: Repository, *, query: str, deep: bool,
                        caps: SpendCaps | None = None) -> dict[str, Any]:
    """Dry run of :func:`search_library`: what a search would call, and at what cost.

    Read-only: no client is built, nothing is sent or written. A typing search
    (``deep`` false) calls nothing. A deep search may make the rewrite call (and
    one retry) and one query embedding; each is planned at its worst case.
    """

    config = vault.config.source_retrieval
    needle = normalize_query(query or "")[:MAX_QUERY_CHARS]
    plan: dict[str, Any] = {"query": needle, "deep": deep, "dry_run": True,
                            "keyword": "local FTS5 BM25 and substring (no call)"}
    if not config.enabled:
        return {**plan, "status": "retrieval_off", "calls": 0, "estimated_usd": 0.0,
                "note": "source_retrieval.enabled = false: today's substring search, no call"}
    scope = library_scope(repository)
    plan["meaning_search"] = meaning_search_state(vault, repository, scope)
    if not deep or len(needle) < 2:
        return {**plan, "status": "no_paid_step", "calls": 0, "estimated_usd": 0.0}
    rewrite: dict[str, Any]
    total_usd: float | None = 0.0
    calls = 0
    if not config.query_rewrite:
        rewrite = {"status": "disabled", "calls": 0}
    elif not is_conceptual(needle):
        rewrite = {"status": "not_needed", "calls": 0, "reason": "not a conceptual question"}
    else:
        route = plan_route(vault, "source_query_rewrite")
        skip = route_skip(route, config.llm_price_per_million, injected=False)
        if skip is not None:
            rewrite = {"status": skip, "calls": 0, "route": route.as_dict()}
        else:
            tokens = estimated_call_tokens(rewrite_prompt(needle, None), QueryRewrite, route.output_tokens)
            paid = PaidCalls(route=route, budget=SpendBudget(caps or rewrite_caps(vault, route.output_tokens)),
                             price_per_million=config.llm_price_per_million, repository=None,
                             owner_kind="source_query_rewrite", owner_id="dry_run")
            view = paid.plan([tokens], candidates=1)
            # Worst case: the call, then one retry at twice the output budget
            # (a truncation retry; output_budget policy).
            retry = paid.plan([tokens + route.output_tokens])
            rewrite = {"status": "would_call", "route": route.as_dict(), "billing": view["billing"],
                       "cost_basis": view["cost_basis"], "calls": 1, "max_calls_with_retry": 2,
                       "output_tokens": route.output_tokens, "reasoning_effort": route.reasoning_effort,
                       "estimated_tokens": view["estimated_tokens"], "estimated_usd": view["estimated_usd"],
                       "marginal_usd": view["marginal_usd"]}
            calls += 2
            total_usd = (None if view["marginal_usd"] is None or retry["marginal_usd"] is None
                         else total_usd + view["marginal_usd"] + retry["marginal_usd"])
    plan["rewrite"] = rewrite
    meaning = plan["meaning_search"]
    # The rewrite's text is unknown until it runs: each query embedding plans
    # it at its largest encoding and never as a cached text (Codex re-review F2).
    unknown = 1 if rewrite.get("status") == "would_call" else 0
    if meaning["status"] in {"ready", "partial"}:
        texts = {query_id(needle): needle}
        model_id = vault.config.embedding.model
        cached = cached_query_vectors(repository, model_id, texts, record_kind=QUERY_RECORD_KIND)
        pending = {key: text for key, text in texts.items() if key not in cached}
        tokens = sum(estimated_tokens(text) for text in pending.values()) + unknown * estimated_tokens(
            LARGEST_QUERY_TEXT)
        texts_count, pending_count = len(texts) + unknown, len(pending) + unknown
        price, price_source = query_embedding_price(model_id, config.query_embedding_price_per_million)
        embedding = {"status": "would_call" if pending_count else "cached", "model_id": model_id,
                     "texts": texts_count, "pending": pending_count, "calls": 1 if pending_count else 0,
                     "estimated_tokens": tokens,
                     "estimated_usd": (tokens * price / 1_000_000 if price is not None
                                       else (0.0 if not pending_count else None)),
                     "price_per_million": price, "price_source": price_source}
        calls += int(embedding["calls"])
        if total_usd is not None:
            total_usd = None if embedding["estimated_usd"] is None else total_usd + embedding["estimated_usd"]
    else:
        embedding = {"status": "unused", "calls": 0, "reason": meaning.get("reason")}
    plan["query_embedding"] = embedding
    # Codex review F2: the hosted fallback space's query is a paid request of
    # the same search, planned at its worst case (queried whenever it serves a
    # source in scope) under the same caller budget.
    from learnloop.source_retrieval.spaces import resolver_active

    if resolver_active(vault.config):
        from learnloop.source_retrieval.fallback_space import plan_query

        fallback_query = plan_query(vault, repository, {"query": needle}, unknown=unknown)
        plan["fallback_query_embedding"] = fallback_query
        calls += int(fallback_query["calls"])
        if total_usd is not None:
            total_usd += float(fallback_query["estimated_usd"])
    plan["caps"] = (caps.as_dict() if caps is not None else
                    {"rewrite": rewrite_caps(vault).as_dict(), "query_embedding": QUERY_EMBEDDING_CAPS.as_dict()})
    plan["time_box_seconds"] = config.retrieval_timeout_seconds
    return {**plan, "status": "planned", "calls": calls, "estimated_usd": total_usd}


__all__ = ["deep_search_caps", "embedding_route_problem", "meaning_search_state", "plan_library_search",
           "search_library"]
