"""Question-dependent tutor spans (Slice 2 T6), injected into ``tutor_qa``.

Before T6 a practice, feedback or library question got the same four
learning-object-linked spans whatever it asked. Now:

1. **Retrieve** over the teaching scope (the LOs' subjects' sources, every
   assessment span excluded): BM25 and dense lists for the question plus the
   practice question in context, the LLM-rewritten query for a conceptual
   question, and the LOs' own linked spans as one more ranked list, fused by RRF.
   In the practice context, a span that reproduces the item's expected answer
   is dropped before anyone sees it.
2. **Verify** (consequential path): the LLM listwise rerank judges every
   candidate and picks at most ``tutor_spans``. Only picked spans reach the
   tutor, and ``tutor_qa``'s citation allowlist keeps its citations inside them.

When verification cannot run (switched off, no route, no price, over budget,
failed), the tutor keeps the LO-linked spans exactly as before, and the
question records why (``source_context.source_retrieval``). Spans are context:
nothing here touches evidence, the facet → LO mapping or scheduling.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from learnloop.clock import Clock
from learnloop.content.authoring.practice_leakage import build_cross_source_spans
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.source_retrieval.corpus import teaching_scope
from learnloop.source_retrieval.search import SpanHit, search_spans
from learnloop.source_retrieval.verify import verify_spans
from learnloop.tutor.tutor_qa import answer_leaks_expected
from learnloop.vault.models import LoadedVault, PracticeItem

SPAN_TEXT_CAP = 600
PROVENANCE_SPANS_PER_LO = 8


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
        owner_id = "tq_" + new_ulid()
        lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
        scope = teaching_scope(vault, repository, lo_ids)
        provenance = [
            (span.extraction_id, span.span_id)
            for lo_id in lo_ids
            for span in build_cross_source_spans(vault, repository, lo_id,
                                                 max_spans_per_item=PROVENANCE_SPANS_PER_LO)
        ]
        context_text = item.prompt if item is not None else None
        search = search_spans(
            vault, repository, question_md, scope, limit=config.tutor_candidate_pool * 2,
            deep=True, context_text=context_text, extra_lists={"provenance": provenance},
            embedder=self.embedder, rewrite_client=self.rewrite_client, owner_id=owner_id,
        )
        pool = list(search.hits)
        withheld = 0
        if context == "practice" and item is not None:
            kept = [hit for hit in pool if not answer_leaks_expected(hit.text, item.expected_answer)]
            withheld = len(pool) - len(kept)
            pool = kept
        pool = pool[: config.tutor_candidate_pool]
        verification = verify_spans(
            vault, repository, question=question_md, pool=pool, pick_at_most=config.tutor_spans,
            context=context_text, client=self.rerank_client, owner_id=owner_id, clock=self.clock,
        )
        manifest: dict[str, Any] = {
            "search": search.describe(), "candidates": len(pool),
            "withheld_answer_overlap": withheld, "verification": verification.describe(),
            "owner_id": owner_id,
        }
        if not verification.ran:
            return None, {**manifest, "basis": "lo_provenance",
                          "reason": f"verification {verification.status}"}
        spans = [span_context(hit) for hit in verification.picks]
        return spans, {**manifest, "basis": "retrieved_verified", "spans": len(spans)}


__all__ = ["PROVENANCE_SPANS_PER_LO", "SPAN_TEXT_CAP", "TutorSpanProvider", "span_context"]
