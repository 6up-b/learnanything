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

Delivery (tutor delivery fixes, 2026-10-13): a picked or pinned span reaches
the tutor as its complete canonical block (``span_context``; no 600-character
cut), and the numbered blocks it cites ("by Theorem 3.2") join it as
``referenced`` spans when they pass the same rules a retrieved span passes (the
scope, exam material, the item's answer; ``tutor_qa.resolve_references``).
``tutor_qa.context_token_budget`` bounds the whole delivery.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import time
from typing import Any

from learnloop.clock import Clock
from learnloop.content.authoring.practice_leakage import build_cross_source_spans
from learnloop.content.sources.exam_material import exam_material
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import blocks_by_key
from learnloop.ids import new_ulid
from learnloop.source_retrieval.corpus import Scope, exam_withheld, teaching_scope
from learnloop.source_retrieval.find_sources import scope_for, span_keys
from learnloop.source_retrieval.queries import Rewrite
from learnloop.source_retrieval.search import SpanHit, SpanKey, SpanSearch, search_spans
from learnloop.source_retrieval.verify import verification_route, verify_spans
from learnloop.tutor.context_delivery import BlockFilter, BlockSource, follow_references
from learnloop.tutor.tutor_qa import span_leaks_expected
from learnloop.vault.models import LoadedVault, PracticeItem

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
    """A verified span in the tutor's ``source_spans`` shape: the complete
    canonical block (``tutor_qa.context_token_budget`` is the only bound)."""

    label = hit.source_title if not hit.section else f"{hit.source_title} · {hit.section}"
    return {
        "extraction_id": hit.extraction_id,
        "span_id": hit.span_id,
        "relation": "retrieved",
        "semantic_authority": False,
        "source_id": hit.source_id,
        "label": label[:120],
        "text": hit.text,
    }


def reference_filter(vault: LoadedVault, repository: Repository, scope: Scope, *,
                     item: PracticeItem | None) -> BlockFilter:
    """The rules a cited numbered block passes to join a retrieved or pinned
    span: inside the span's scope (an item-bound scope already leaves out the
    item's passages, exercises and solutions), never exam material, never a
    passage that reproduces the practised item's answer."""

    exam: list[Any] = []

    def allow(extraction_id: str, block: Any) -> str | None:
        if not scope.allows(extraction_id, str(block.span_id)):
            return "outside the tutor's sources for this question"
        if not exam:
            exam.append(exam_material(vault, repository))
        if exam[0].covers(extraction_id, str(block.span_id)):
            return "exam material"
        if item is not None and span_leaks_expected(block.text, item.expected_answer):
            return "it reproduces the answer to the item being practised"
        return None

    return allow


def linked_reference_filter(vault: LoadedVault, repository: Repository, *, context: str,
                            learning_object_ids: Sequence[str], item: PracticeItem | None) -> BlockFilter:
    """The rules a numbered block cited by a learning object's linked span
    passes (the tutor's fallback when retrieval keeps the linked spans;
    injected by the adapter as ``ask_question(linked_reference_filter=...)``).

    Exactly a retrieved span's rules (:func:`reference_filter`) over the
    question's own teaching scope (:func:`tutor_scope`): material without
    teaching authority and assessment-linked spans never; in a practice or
    feedback context also every passage linked to the item (its
    ``entity_source_links`` of any relation and its provenance refs, the same
    text in the source's other extractions, the worked example, exercise or
    solution body such a passage leads) and every exercise and solution block
    with its region's body (Codex review F1, tutor delivery fixes). The scope
    is built on the first block asked about."""

    item_bound = context in ITEM_BOUND_CONTEXTS and item is not None
    built: list[BlockFilter] = []

    def allow(extraction_id: str, block: Any) -> str | None:
        if not built:
            scope = tutor_scope(vault, repository, context=context, learning_object_ids=learning_object_ids,
                                item=item)
            built.append(reference_filter(vault, repository, scope, item=item if item_bound else None))
        return built[0](extraction_id, block)

    return allow


def with_references(vault: LoadedVault, repository: Repository, spans: list[dict[str, Any]], scope: Scope, *,
                    item: PracticeItem | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """``spans`` and the numbered blocks they cite (``referenced``), with what
    was followed for the manifest (None when nothing was cited or the
    ``tutor_qa.resolve_references`` kill switch is off)."""

    if not spans or not vault.config.tutor_qa.resolve_references:
        return spans, None

    def extra(extraction_id: str, _block: Any) -> dict[str, Any]:
        found = scope.extractions.get(extraction_id)
        return {"semantic_authority": False, "source_id": found.source_id if found else None}

    found = follow_references(
        BlockSource(repository.sqlite_path), spans, allow=reference_filter(vault, repository, scope, item=item),
        delivered={(str(span["extraction_id"]), str(span["span_id"])) for span in spans}, span_extra=extra,
    )
    return spans + found.spans, (None if found.empty else found.describe())


@dataclass
class TutorPool:
    """The candidates the tutor's verification judges, and how they were found."""

    pool: list[SpanHit]
    search: SpanSearch
    scope: Scope
    #: Hits withheld for reproducing the practice item's expected answer.
    withheld: list[str] = field(default_factory=list)
    #: The practice question shown to the verifier (item-bound contexts only).
    verify_context: str | None = None


def tutor_scope(vault: LoadedVault, repository: Repository, *, context: str,
                learning_object_ids: Sequence[str], item: PracticeItem | None) -> Scope:
    """The scope the tutor's pool searches for one question: the teaching scope
    of its LOs, with the item's exclusions in a practice or feedback context.
    Its dense index, not the library's, decides whether that pool is dense
    (the T6 report reads it per question; review F8)."""

    item_bound = context in ITEM_BOUND_CONTEXTS and item is not None
    lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
    return teaching_scope(vault, repository, lo_ids, item_bound=item_bound, item=item if item_bound else None)


def tutor_pool(
    vault: LoadedVault, repository: Repository, *, context: str, question_md: str,
    learning_object_ids: Sequence[str], item: PracticeItem | None, embedder: Any | None = None,
    rewrite_client: Any | None = None, owner_id: str = "", deadline: float | None = None,
    query_vectors: Mapping[str, Any] | None = None, rewrite: bool | None = None,
    rewritten: Rewrite | None = None, pool: str | None = None, pool_extras: int | None = None,
    extra_lists: Mapping[str, Sequence[SpanKey]] | None = None, scope: Scope | None = None,
) -> TutorPool:
    """The tutor's candidate pool for one question (steps 1 and its withholding).

    The teaching scope of the question's LOs (assessment spans excluded; in a
    practice or feedback context also the item's own passages and every
    exercise and solution block), the LOs' linked spans as the
    ``provenance`` list, the learner's question alone as the query, answer
    overlap withheld, then the pool by ``pool`` (None: ``source_retrieval.pool``).
    The T6 report calls this with ``query_vectors`` (and a ``rewritten``
    query) it already paid for, and ``pool`` / ``pool_extras`` for the pool it
    measures, so it verifies exactly what the tutor would (review F5).
    ``extra_lists`` join the ``provenance`` list (canonical sources S3: a
    remediate intent's correction lists), and ``scope`` reuses a scope the
    caller already built with :func:`tutor_scope`.
    """

    config = vault.config.source_retrieval
    item_bound = context in ITEM_BOUND_CONTEXTS and item is not None
    lo_ids = [lo_id for lo_id in dict.fromkeys(learning_object_ids) if lo_id in vault.learning_objects]
    if scope is None:
        scope = tutor_scope(vault, repository, context=context, learning_object_ids=lo_ids, item=item)
    provenance = [
        (span.extraction_id, span.span_id)
        for lo_id in lo_ids
        for span in build_cross_source_spans(vault, repository, lo_id,
                                             max_spans_per_item=PROVENANCE_SPANS_PER_LO)
    ]
    if rewrite is None:
        rewrite = None if config.tutor_query_rewrite else False
    lists: dict[str, list[SpanKey]] = {"provenance": provenance}
    for name, keys in (extra_lists or {}).items():
        lists.setdefault(name, []).extend(keys)
    # The learner's question alone: the practice question would rank the
    # item's own exercise and solution first (and so would a rewrite of it).
    search = search_spans(
        vault, repository, question_md, scope, limit=config.tutor_candidate_pool * 2,
        deep=True, rewrite=rewrite, extra_lists=lists, embedder=embedder,
        rewrite_client=rewrite_client, owner_id=owner_id, deadline=deadline,
        pool_dense=config.tutor_candidate_pool + WITHHOLD_SPARE, query_vectors=query_vectors,
        rewritten=rewritten, pool=pool, pool_extras=pool_extras,
    )
    hits = list(search.hits)
    withheld: list[str] = []
    if item_bound and item is not None:
        kept = []
        for hit in hits:
            if span_leaks_expected(hit.text, item.expected_answer):
                withheld.append(hit.record_id)
            else:
                kept.append(hit)
        hits = kept
    if any(hit.pool_role for hit in hits):
        # dense_plus_bm25: the dense top-k, then every widening list's top
        # pool_keyword_extras (a spare dense hit that is also in one of
        # those stays, as that list's extra; a remediate intent's correction
        # lists widen it like the linked spans).
        dense = [hit for hit in hits if hit.pool_role == "dense"]
        extras_m = (search.pool or {}).get("extras_m", config.pool_keyword_extras)
        widening = [name for name in ("keyword", "provenance", *sorted(set(lists) - {"provenance"}))
                    if name in search.lists]
        spare = [hit for hit in dense[config.tutor_candidate_pool:]
                 if any(hit.ranks.get(name, extras_m + 1) <= extras_m for name in widening)]
        hits = (dense[: config.tutor_candidate_pool] + spare
                + [hit for hit in hits if hit.pool_role not in (None, "dense")])
    else:
        hits = hits[: config.tutor_candidate_pool]
    return TutorPool(hits, search, scope, withheld,
                     item.prompt if item_bound and item is not None else None)


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
        intent = None
        if self.intent_for is not None:
            try:
                intent = self.intent_for(vault, repository, context=context, item=item if item_bound else None)
            except Exception:  # noqa: BLE001 - an intent hint never blocks grounding
                intent = None
        scope = tutor_scope(vault, repository, context=context, learning_object_ids=learning_object_ids,
                            item=item)
        extra_lists: dict[str, list[SpanKey]] = {}
        if intent and intent.get("intent") == "remediate":
            from learnloop.source_retrieval.find_sources import correction_lists

            for misconception in intent.get("misconceptions") or ():
                lists, _report = correction_lists(vault, repository, misconception, sorted(scope.extractions))
                for name, keys in lists.items():
                    extra_lists.setdefault(name, []).extend(keys)
        built = tutor_pool(vault, repository, context=context, question_md=question_md,
                           learning_object_ids=learning_object_ids, item=item, embedder=self.embedder,
                           rewrite_client=self.rewrite_client, owner_id=owner_id, deadline=deadline,
                           extra_lists=extra_lists, scope=scope)
        search, pool, withheld = built.search, built.pool, built.withheld
        if not config.tutor_query_rewrite:
            search.rewrite = {"status": "disabled", "reason": "source_retrieval.tutor_query_rewrite is false"}
        if intent and intent.get("intent") == "remediate" and pool:
            return self._remediate(vault, repository, question_md=question_md, pool=pool, intent=intent,
                                   item=item if item_bound else None, search=search, withheld=withheld,
                                   owner_id=owner_id, ready=ready, deadline=deadline, started=started,
                                   scope=scope)
        verify_started = time.monotonic()
        verification = verify_spans(
            vault, repository, question=question_md, pool=pool, pick_at_most=config.tutor_spans,
            context=built.verify_context, owner_id=owner_id, clock=self.clock, ready=ready, deadline=deadline,
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
        spans, references = with_references(vault, repository, spans, scope, item=item if item_bound else None)
        return spans, {**manifest, "basis": "retrieved_verified", "spans": len(verification.picks),
                       "span_keys": [hit.record_id for hit in verification.picks],
                       **({"references": references} if references else {})}

    def _remediate(self, vault: LoadedVault, repository: Repository, *, question_md: str, pool: list[SpanHit],
                   intent: dict[str, Any], item: PracticeItem | None, search: SpanSearch, withheld: list[str],
                   owner_id: str, ready: Any, deadline: float | None, started: float,
                   scope: Scope) -> tuple[Any, dict[str, Any]]:
        """The remediate intent: same retrieval, the intent's verification prompt (no extra call).

        Its receipt carries the same timing fields as an explain question's
        (``timings_ms``, ``over_soft_deadline``; the soft deadline unless
        ``tutor_deadline_cancels``)."""

        from learnloop.source_retrieval.find_sources import _verify

        config = vault.config.source_retrieval
        misconceptions = intent.get("misconceptions") or ()
        context: dict[str, Any] = {"misconceptions": [
            {"statement": getattr(m, "statement", ""), "correction": getattr(m, "correction_statement", "")}
            for m in misconceptions]}
        if item is not None:
            context["practice_question"] = " ".join(item.prompt.split())[:700]
        verify_started = time.monotonic()
        status, rows, picks, reason = _verify(
            vault, repository, intent="remediate", question=question_md, pool=pool,
            pick_at_most=config.tutor_spans, context=context, client=ready.client, owner_id=owner_id,
            deadline=deadline, clock=self.clock)
        verification_ms = int(round((time.monotonic() - verify_started) * 1000))
        elapsed_ms = int(round((time.monotonic() - started) * 1000))
        timings = step_timings(search.timings_ms, verification_ms=verification_ms, total_ms=elapsed_ms)
        manifest: dict[str, Any] = {
            "search": search.describe(), "candidates": len(pool), "candidate_keys": [hit.record_id for hit in pool],
            "pool": dict(search.pool),
            "withheld_answer_overlap": len(withheld), "withheld_keys": withheld, "intent": "remediate",
            "verification": {"status": status, "reason": reason, "judged": len(rows), "picked": len(picks)},
            "owner_id": owner_id, "time_box_seconds": config.retrieval_timeout_seconds,
            "deadline": "cancels" if config.tutor_deadline_cancels else "soft",
            "timings_ms": timings,
            "over_soft_deadline": over_soft_deadline(timings, config.retrieval_timeout_seconds),
            "elapsed_ms": elapsed_ms,
        }
        if status not in ("verified", "cached"):
            return None, {**manifest, "basis": "lo_provenance", "reason": f"verification {status}"}
        by_key = {hit.key: hit for hit in pool}
        chosen = [by_key[key] for key in picks if key in by_key]
        spans, references = with_references(vault, repository, [span_context(hit) for hit in chosen], scope,
                                             item=item)
        return spans, {**manifest, "basis": "retrieved_verified", "spans": len(chosen),
                       "span_keys": [hit.record_id for hit in chosen],
                       **({"references": references} if references else {})}


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
        # Exam material is assessment-only (role authority; the sources
        # merge): it never grounds the tutor, whatever the policy. The learner
        # still reads it in the Reader; solutions keep the branch's rule above.
        exam = exam_withheld(vault, repository, keys)
        spans: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []
        for key in keys:
            block = blocks.get(key)
            why = None
            if block is None:
                why = "no such passage"
            elif key in exam:
                why = "it is exam material"
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
        pinned_keys = [f"{s['extraction_id']}:{s['span_id']}" for s in spans]
        pinned = len(spans)
        spans, references = with_references(vault, repository, spans, scope, item=item if item_bound else None)
        return spans, {"basis": "pinned", "policy": policy, "spans": pinned, "span_keys": pinned_keys,
                       "dropped_pins": dropped, **({"references": references} if references else {})}


__all__ = [
    "ITEM_BOUND_CONTEXTS",
    "PROVENANCE_SPANS_PER_LO",
    "PinnedSpanProvider",
    "TIMED_STEPS",
    "TutorPool",
    "TutorSpanProvider",
    "WITHHOLD_SPARE",
    "linked_reference_filter",
    "over_soft_deadline",
    "reference_filter",
    "span_context",
    "step_timings",
    "tutor_pool",
    "tutor_scope",
    "with_references",
]
