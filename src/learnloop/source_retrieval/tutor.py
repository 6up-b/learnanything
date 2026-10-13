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
from contextlib import closing
import time
from typing import Any

from learnloop.clock import Clock
from learnloop.content.authoring.practice_leakage import build_cross_source_spans
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import blocks_by_key
from learnloop.ids import new_ulid
from learnloop.source_retrieval.corpus import teaching_scope
from learnloop.source_retrieval.find_sources import scope_for, span_keys
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
                 rerank_client: Any | None = None, clock: Clock | None = None,
                 intent_for: Any | None = None) -> None:
        self.embedder = embedder
        self.rewrite_client = rewrite_client
        self.rerank_client = rerank_client
        self.clock = clock
        # Canonical sources S3 (§9.5): ``intent_for(vault, repository, context=,
        # item=)`` -> ``{"intent": "remediate", "misconceptions": [...]}`` or
        # None (explain). Injected by the adapter; None keeps T6's behaviour.
        self.intent_for = intent_for

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
        scope = teaching_scope(vault, repository, lo_ids, item_bound=item_bound,
                               item=item if item_bound else None)
        provenance = [
            (span.extraction_id, span.span_id)
            for lo_id in lo_ids
            for span in build_cross_source_spans(vault, repository, lo_id,
                                                 max_spans_per_item=PROVENANCE_SPANS_PER_LO)
        ]
        intent = None
        if self.intent_for is not None:
            try:
                intent = self.intent_for(vault, repository, context=context, item=item if item_bound else None)
            except Exception:  # noqa: BLE001 - an intent hint never blocks grounding
                intent = None
        extra_lists: dict[str, Any] = {"provenance": provenance}
        if intent and intent.get("intent") == "remediate":
            from learnloop.source_retrieval.find_sources import correction_lists

            for misconception in intent.get("misconceptions") or ():
                lists, _report = correction_lists(vault, repository, misconception, sorted(scope.extractions))
                for name, keys in lists.items():
                    extra_lists.setdefault(name, []).extend(keys)
        # The learner's question alone: the practice question would rank the
        # item's own exercise and solution first (and so would a rewrite of it).
        search = search_spans(
            vault, repository, question_md, scope, limit=config.tutor_candidate_pool * 2,
            deep=True, rewrite=None if config.tutor_query_rewrite else False,
            extra_lists=extra_lists, embedder=self.embedder,
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
        if intent and intent.get("intent") == "remediate" and pool:
            return self._remediate(vault, repository, question_md=question_md, pool=pool, intent=intent,
                                   item=item if item_bound else None, search=search, withheld=withheld,
                                   owner_id=owner_id, ready=ready, deadline=deadline, started=started)
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

    def _remediate(self, vault: LoadedVault, repository: Repository, *, question_md: str, pool: list[SpanHit],
                   intent: dict[str, Any], item: PracticeItem | None, search: Any, withheld: list[str],
                   owner_id: str, ready: Any, deadline: float, started: float) -> tuple[Any, dict[str, Any]]:
        """The remediate intent: same retrieval, the intent's verification prompt (no extra call)."""

        from learnloop.source_retrieval.find_sources import _verify

        config = vault.config.source_retrieval
        misconceptions = intent.get("misconceptions") or ()
        context: dict[str, Any] = {"misconceptions": [
            {"statement": getattr(m, "statement", ""), "correction": getattr(m, "correction_statement", "")}
            for m in misconceptions]}
        if item is not None:
            context["practice_question"] = " ".join(item.prompt.split())[:700]
        status, rows, picks, reason = _verify(
            vault, repository, intent="remediate", question=question_md, pool=pool,
            pick_at_most=config.tutor_spans, context=context, client=ready.client, owner_id=owner_id,
            deadline=deadline, clock=self.clock)
        manifest: dict[str, Any] = {
            "search": search.describe(), "candidates": len(pool), "candidate_keys": [hit.record_id for hit in pool],
            "withheld_answer_overlap": len(withheld), "withheld_keys": withheld, "intent": "remediate",
            "verification": {"status": status, "reason": reason, "judged": len(rows), "picked": len(picks)},
            "owner_id": owner_id, "time_box_seconds": config.retrieval_timeout_seconds,
            "elapsed_ms": int(round((time.monotonic() - started) * 1000)),
        }
        if status not in ("verified", "cached"):
            return None, {**manifest, "basis": "lo_provenance", "reason": f"verification {status}"}
        by_key = {hit.key: hit for hit in pool}
        chosen = [by_key[key] for key in picks if key in by_key]
        spans = [span_context(hit) for hit in chosen]
        return spans, {**manifest, "basis": "retrieved_verified", "spans": len(spans),
                       "span_keys": [hit.record_id for hit in chosen]}


class PinnedSpanProvider:
    """"Explain this with my work" (canonical sources S4, §10.3): the tutor is
    grounded in the passages the learner chose, through the same filters any
    retrieved span passes (an item-bound question never receives an exercise,
    a solution, a span linked to its item or one that reproduces its answer).

    ``cold`` (decided by the adapter from the caller) grounds in nothing."""

    def __init__(self, span_keys: Sequence[Any], *, cold: bool = False) -> None:
        self.span_keys = list(span_keys)
        self.cold = cold

    def __call__(self, vault: LoadedVault, repository: Repository, *, context: str,
                 question_md: str, learning_object_ids: Sequence[str],
                 item: PracticeItem | None) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
        if self.cold:
            return [], {"basis": "pinned", "policy": "cold_attempt", "spans": 0,
                        "reason": "nothing is grounded during a cold administration"}
        item_bound = context in ITEM_BOUND_CONTEXTS and item is not None
        policy = "assisted_practice" if item_bound else "reading"
        lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
        scope = scope_for(vault, repository, policy=policy, scope="library", learning_object_ids=lo_ids,
                          item=item if item_bound else None)
        keys = sorted(span_keys(self.span_keys))
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            blocks = blocks_by_key(connection, keys)
        spans: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []
        for key in keys:
            block = blocks.get(key)
            why = None
            if block is None:
                why = "no such passage"
            elif not scope.allows(*key):
                why = "not available while you're practising this item" if item_bound else "not in your sources"
            elif item_bound and span_leaks_expected(block.text, item.expected_answer):
                why = "it reproduces the answer to the item you are practising"
            if why is not None:
                dropped.append({"extraction_id": key[0], "span_id": key[1], "reason": why})
                continue
            extraction = scope.extractions[key[0]]
            spans.append(span_context(SpanHit(
                extraction_id=key[0], span_id=key[1], source_id=extraction.source_id,
                source_title=extraction.title, text=block.text, block_type=block.block_type, section_path=[],
                page=block.page, ordinal=block.ordinal, ranks={"pinned": 1})))
        return spans, {"basis": "pinned", "policy": policy, "spans": len(spans),
                       "span_keys": [f"{s['extraction_id']}:{s['span_id']}" for s in spans],
                       "dropped_pins": dropped}


__all__ = ["ITEM_BOUND_CONTEXTS", "PROVENANCE_SPANS_PER_LO", "SPAN_TEXT_CAP", "PinnedSpanProvider",
           "TutorSpanProvider", "span_context"]
