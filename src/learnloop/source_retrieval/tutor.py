"""Question-dependent tutor spans (Slice 2 T6), injected into ``tutor_qa``.

Before T6 a practice, feedback or library question got the same four
learning-object-linked spans whatever it asked. Now:

0. **Check verification first.** If the verification route cannot run (no
   route, a metered route without a price, a provider that is not ready),
   nothing is retrieved or paid for and the tutor keeps the linked spans.
1. **Retrieve** over the teaching scope (the LOs' subjects' sources that have
   teaching authority; every assessment span excluded; in a practice or feedback
   context also every passage linked to the item, whatever the relation, and
   every exercise and solution block): BM25 and dense lists for the
   learner's question alone (never the practice question, whose own worked
   answer would rank first), the LLM-rewritten query when
   ``tutor_query_rewrite`` is on, and the LOs' own linked spans as one more
   ranked list, fused by RRF. In a practice or feedback context a span that
   reproduces the item's expected answer, short numeric answers included, is
   withheld before anyone sees it.
2. **Verify** (consequential path): the LLM listwise rerank judges every
   candidate and picks at most ``tutor_spans``, never a passage that answers
   the practice question in context. Only picked spans reach the tutor, and
   ``tutor_qa``'s citation allowlist keeps its citations inside them.

The candidate pool follows ``source_retrieval.pool``: ``dense_plus_bm25`` (the
dense top ``tutor_candidate_pool``, then the BM25 top ``pool_keyword_extras``
and the linked spans' top ``pool_keyword_extras`` that dense did not return)
or ``hybrid_rrf`` (every list fused by rank, cut to ``tutor_candidate_pool``).
Without a complete dense index the pool is ``hybrid_rrf``.

Timing (owner, 2026-10-12): no deadline cancels the tutor's retrieval.
Every step (rewrite, query embedding, retrieval, verification, total) records
its wall time on the question's receipt (``timings_ms``), and a step over the
``retrieval_timeout_seconds`` soft deadline is named in
``over_soft_deadline``; ``tutor_deadline_cancels = true`` restores the time
box. When verification cannot run, the tutor keeps the LO-linked spans exactly
as before, and the question records why (``source_context.source_retrieval``,
with the span keys it saw, never their text). Spans are context: nothing here
touches evidence, the facet -> LO mapping or scheduling (cited spans are
reveal-accounted by ``tutor_qa``).
"""
from __future__ import annotations

from collections.abc import Sequence
import time
from typing import Any

from learnloop.clock import Clock
from learnloop.content.authoring.practice_leakage import build_cross_source_spans
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.source_retrieval.corpus import teaching_scope
from learnloop.source_retrieval.search import SpanHit, search_spans
from learnloop.source_retrieval.verify import verification_route, verify_spans
from learnloop.tutor.tutor_qa import span_leaks_expected
from learnloop.vault.models import LoadedVault, PracticeItem

SPAN_TEXT_CAP = 600
PROVENANCE_SPANS_PER_LO = 8
#: Contexts bound to a practice item: its answer must never be retrieved.
ITEM_BOUND_CONTEXTS = frozenset({"practice", "feedback"})
#: Extra dense candidates fetched so that withholding a span that leaks the
#: expected answer still leaves ``tutor_candidate_pool`` dense candidates.
WITHHOLD_SPARE = 4
#: The steps a tutor question's receipt times, in milliseconds.
TIMED_STEPS = ("rewrite", "query_embedding", "retrieval", "verification", "total")


def step_timings(search_timings: dict[str, int], *, verification_ms: int, total_ms: int) -> dict[str, int]:
    """Per-step wall times: retrieval is the search minus its paid steps.

    A paid step that did not run (no rewrite asked for, a cached or skipped
    query embedding) is left out rather than timed as zero.
    """

    paid = {step: int(search_timings[step]) for step in ("rewrite", "query_embedding") if step in search_timings}
    search_total = int(search_timings.get("total", 0))
    return {**paid, "retrieval": max(0, search_total - sum(paid.values())),
            "verification": verification_ms, "total": total_ms}


def over_soft_deadline(timings: dict[str, int], seconds: float) -> list[str]:
    """The steps (``total`` included) whose wall time exceeded the soft deadline."""

    return [step for step in TIMED_STEPS if timings.get(step, 0) > seconds * 1000]


def span_context(hit: SpanHit) -> dict[str, Any]:
    """A verified span in the tutor's ``source_spans`` shape."""

    label = hit.source_title if not hit.section else f"{hit.source_title} · {hit.section}"
    text = " ".join(hit.text.split())
    return {
        "extraction_id": hit.extraction_id,
        "span_id": hit.span_id,
        "relation": "retrieved",
        "semantic_authority": False,
        "source_id": hit.source_id,
        "label": label[:120],
        "text": text[:SPAN_TEXT_CAP],
    }


class TutorSpanProvider:
    """``(vault, repository, *, context, question_md, learning_object_ids, item)``
    -> ``(spans or None, manifest or None)``. ``None`` spans keep today's spans;
    a ``None`` manifest (kill switch off) records nothing."""

    def __init__(self, *, embedder: Any | None = None, rewrite_client: Any | None = None,
                 rerank_client: Any | None = None, clock: Clock | None = None) -> None:
        self.embedder = embedder
        self.rewrite_client = rewrite_client
        self.rerank_client = rerank_client
        self.clock = clock

    def __call__(self, vault: LoadedVault, repository: Repository, *, context: str,
                 question_md: str, learning_object_ids: Sequence[str],
                 item: PracticeItem | None) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
        config = vault.config.source_retrieval
        if not config.enabled:
            return None, None
        if not config.tutor_rerank:
            return None, {"basis": "lo_provenance",
                          "reason": "source_retrieval.tutor_rerank is false"}
        started = time.monotonic()
        # A soft deadline unless the owner restores the time box.
        deadline = started + config.retrieval_timeout_seconds if config.tutor_deadline_cancels else None
        ready = verification_route(vault, self.rerank_client)
        if not ready.ready:
            # Nothing is retrieved (or paid for) when verification cannot run.
            return None, {"basis": "lo_provenance",
                          "reason": f"verification {ready.skip}" + (f" ({ready.reason})" if ready.reason else ""),
                          "verification": {"status": ready.skip, "reason": ready.reason}}
        owner_id = "tq_" + new_ulid()
        item_bound = context in ITEM_BOUND_CONTEXTS and item is not None
        lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
        scope = teaching_scope(vault, repository, lo_ids, item_bound=item_bound,
                               item=item if item_bound else None)
        provenance = [
            (span.extraction_id, span.span_id)
            for lo_id in lo_ids
            for span in build_cross_source_spans(vault, repository, lo_id,
                                                 max_spans_per_item=PROVENANCE_SPANS_PER_LO)
        ]
        # The learner's question alone: the practice question would rank the
        # item's own exercise and solution first (and so would a rewrite of it).
        search = search_spans(
            vault, repository, question_md, scope, limit=config.tutor_candidate_pool * 2,
            deep=True, rewrite=None if config.tutor_query_rewrite else False,
            extra_lists={"provenance": provenance}, embedder=self.embedder,
            rewrite_client=self.rewrite_client, owner_id=owner_id, deadline=deadline,
            pool_dense=config.tutor_candidate_pool + WITHHOLD_SPARE,
        )
        if not config.tutor_query_rewrite:
            search.rewrite = {"status": "disabled", "reason": "source_retrieval.tutor_query_rewrite is false"}
        pool = list(search.hits)
        withheld: list[str] = []
        if item_bound and item is not None:
            kept = []
            for hit in pool:
                if span_leaks_expected(hit.text, item.expected_answer):
                    withheld.append(hit.record_id)
                else:
                    kept.append(hit)
            pool = kept
        if any(hit.pool_role for hit in pool):
            # dense_plus_bm25: the dense top-k, then every widening list's top
            # pool_keyword_extras (a spare dense hit that is also in one of
            # those stays, as that list's extra).
            dense = [hit for hit in pool if hit.pool_role == "dense"]
            extras_m = (search.pool or {}).get("extras_m", config.pool_keyword_extras)
            widening = [name for name in ("keyword", "provenance") if name in search.lists]
            spare = [hit for hit in dense[config.tutor_candidate_pool:]
                     if any(hit.ranks.get(name, extras_m + 1) <= extras_m for name in widening)]
            pool = (dense[: config.tutor_candidate_pool] + spare
                    + [hit for hit in pool if hit.pool_role not in (None, "dense")])
        else:
            pool = pool[: config.tutor_candidate_pool]
        verify_started = time.monotonic()
        verification = verify_spans(
            vault, repository, question=question_md, pool=pool, pick_at_most=config.tutor_spans,
            context=item.prompt if item_bound and item is not None else None, owner_id=owner_id,
            clock=self.clock, ready=ready, deadline=deadline,
        )
        verification_ms = int(round((time.monotonic() - verify_started) * 1000))
        elapsed_ms = int(round((time.monotonic() - started) * 1000))
        timings = step_timings(search.timings_ms, verification_ms=verification_ms, total_ms=elapsed_ms)
        manifest: dict[str, Any] = {
            "search": search.describe(), "candidates": len(pool),
            "candidate_keys": [hit.record_id for hit in pool],
            "pool": dict(search.pool),
            "withheld_answer_overlap": len(withheld), "withheld_keys": withheld,
            "verification": verification.describe(), "owner_id": owner_id,
            "time_box_seconds": config.retrieval_timeout_seconds,
            "deadline": "cancels" if config.tutor_deadline_cancels else "soft",
            "timings_ms": timings,
            "over_soft_deadline": over_soft_deadline(timings, config.retrieval_timeout_seconds),
            "elapsed_ms": elapsed_ms,
        }
        if not verification.ran:
            return None, {**manifest, "basis": "lo_provenance",
                          "reason": f"verification {verification.status}"}
        spans = [span_context(hit) for hit in verification.picks]
        return spans, {**manifest, "basis": "retrieved_verified", "spans": len(spans),
                       "span_keys": [hit.record_id for hit in verification.picks]}


__all__ = [
    "ITEM_BOUND_CONTEXTS",
    "PROVENANCE_SPANS_PER_LO",
    "SPAN_TEXT_CAP",
    "TIMED_STEPS",
    "TutorSpanProvider",
    "over_soft_deadline",
    "span_context",
    "step_timings",
]
