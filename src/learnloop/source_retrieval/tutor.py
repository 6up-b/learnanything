"""Question-dependent tutor spans (Slice 2 T6), injected into ``tutor_qa``.

Before T6 a practice, feedback or library question got the same four
learning-object-linked spans whatever it asked. Now:

0. **Check verification first.** If the verification route cannot run (no
   route, a metered route without a price, a provider that is not ready),
   nothing is retrieved or paid for and the tutor keeps the linked spans.
1. **Retrieve** over the teaching scope (the LOs' subjects' sources that have
   teaching authority; every assessment span excluded; in a practice or feedback
   context also every exercise and solution block): BM25 and dense lists for the
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

The whole step runs inside ``retrieval_timeout_seconds``: each paid request
carries the time left as its timeout. When verification cannot run or runs
out of time, the tutor keeps the LO-linked spans exactly as before, and the
question records why (``source_context.source_retrieval``, with the span keys
it saw, never their text). Spans are context: nothing here touches evidence,
the facet -> LO mapping or scheduling (cited spans are reveal-accounted by
``tutor_qa``).
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
        deadline = started + config.retrieval_timeout_seconds
        ready = verification_route(vault, self.rerank_client)
        if not ready.ready:
            # Nothing is retrieved (or paid for) when verification cannot run.
            return None, {"basis": "lo_provenance",
                          "reason": f"verification {ready.skip}" + (f" ({ready.reason})" if ready.reason else ""),
                          "verification": {"status": ready.skip, "reason": ready.reason}}
        owner_id = "tq_" + new_ulid()
        item_bound = context in ITEM_BOUND_CONTEXTS and item is not None
        lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
        scope = teaching_scope(vault, repository, lo_ids, item_bound=item_bound)
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
        pool = pool[: config.tutor_candidate_pool]
        verification = verify_spans(
            vault, repository, question=question_md, pool=pool, pick_at_most=config.tutor_spans,
            context=item.prompt if item_bound and item is not None else None, owner_id=owner_id,
            clock=self.clock, ready=ready, deadline=deadline,
        )
        manifest: dict[str, Any] = {
            "search": search.describe(), "candidates": len(pool),
            "candidate_keys": [hit.record_id for hit in pool],
            "withheld_answer_overlap": len(withheld), "withheld_keys": withheld,
            "verification": verification.describe(), "owner_id": owner_id,
            "time_box_seconds": config.retrieval_timeout_seconds,
            "elapsed_ms": int(round((time.monotonic() - started) * 1000)),
        }
        if not verification.ran:
            return None, {**manifest, "basis": "lo_provenance",
                          "reason": f"verification {verification.status}"}
        spans = [span_context(hit) for hit in verification.picks]
        return spans, {**manifest, "basis": "retrieved_verified", "spans": len(spans),
                       "span_keys": [hit.record_id for hit in verification.picks]}


__all__ = ["ITEM_BOUND_CONTEXTS", "PROVENANCE_SPANS_PER_LO", "SPAN_TEXT_CAP", "TutorSpanProvider", "span_context"]
