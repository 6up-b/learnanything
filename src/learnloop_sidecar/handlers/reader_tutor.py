"""Reader workbench RW1c's composition for ``reader.ask`` (spec_reader_workbench_v1 §4.6).

No RPC of its own: ``reader.ask`` gains optional inputs (the retrieval
intent for "another way" and "that didn't help", the personalized toggle, a
workbench session) and this module builds what the tutor needs on the
server, never from the frontend's word:

* the caller, derived as RW4a derives it (``library_ask.reader_caller``: the
  Reader context reads under ``reading``, a workbench session bound to an
  item under ``assisted_practice`` for it, a cold administration under
  ``cold_attempt`` and retrieves nothing);
* the retrieval, the sources service's ``propose_sources`` bound to that
  caller (or, with ``source_service.enabled`` off, the base
  ``find_sources_for_caller`` with intent ``explain``: G53's fallback);
* the inquiry's shown passages (excluded by "another way"), its named gaps
  (``remediate``'s ``target_hypotheses``), the learner's work for the bridge
  (personalized only) and the Reader's own "Try the next step first" buttons.

Kill switches: ``reader_tutor.retrieval_enabled`` (off: no request is built
and the tutor is today's, byte for byte) and ``reader_tutor.offers_enabled``
(off: no ``tutor_offers`` on the wire, so the Reader renders no buttons).
"""
from __future__ import annotations

from typing import Any

from learnloop_sidecar.errors import SidecarError

#: The version of the plain practice request the Reader offers when the
#: sources service is off (§4.6: "Practice this" calls find_practice with the
#: learner's question directly).
FALLBACK_PRACTICE_VERSION = "reader_practice_fallback.v1"


def retrieval_enabled(vault: Any) -> bool:
    section = getattr(vault.config, "reader_tutor", None)
    return bool(getattr(section, "retrieval_enabled", False))


def offers_enabled(vault: Any) -> bool:
    section = getattr(vault.config, "reader_tutor", None)
    return bool(getattr(section, "offers_enabled", False))


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What RW1c adds to the Reader's prompt contract (nothing while both switches are off)."""

    from learnloop.reader import reader_dialogue as RD

    retrieval, offers = retrieval_enabled(vault), offers_enabled(vault)
    if not (retrieval or offers):
        return {}
    inquiry = RD.inquiry_enabled(vault)
    active = inquiry and bool(getattr(getattr(vault.config, "reader_active_reading", None), "enabled", False))
    fields: dict[str, Any] = {"reader_tutor": {
        "retrieval": retrieval,
        "offers": offers,
        # "another way" and "that didn't help" are follow-ups: they need RW1a's branches.
        "another_way": retrieval and inquiry,
        "personalized_default": bool(vault.config.library_ask.personalized_default),
        "try_next_step": offers and active,
        # What the tutor's context adds to the manifest above while retrieval is on.
        "manifest_includes": [
            "passages LearnLoop found in the learner's books for this question (verified; after the selection)",
            "when personalized, the learner's open questions and recent workbench steps on the passage's "
            "learning objects",
        ] if retrieval else [],
    }}
    return fields


def _ancestors(exchanges: list[dict[str, Any]], parent_id: str | None) -> list[dict[str, Any]]:
    by_id = {str(e["event_id"]): e for e in exchanges}
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    current = parent_id
    while current and current in by_id and current not in seen:
        seen.add(current)
        chain.append(by_id[current])
        current = by_id[current].get("parent_exchange_id")
    return list(reversed(chain))


def build_request(ctx: Any, vault: Any, repository: Any, params: Any) -> Any:
    """The ``ReaderTutorRequest`` for one ``reader.ask``, or None while retrieval is off."""

    if not retrieval_enabled(vault):
        if params.retrieval_intent != "explain":
            raise SidecarError("validation_error",
                               "Another way and that didn't help are switched off (reader_tutor.retrieval_enabled).")
        return None
    from learnloop.reader import reader_dialogue as RD
    from learnloop.source_retrieval import reader_tutor as RT
    from learnloop.source_retrieval.library_ask import open_questions
    from learnloop.source_retrieval.policy import derive_policy
    from learnloop.tutor.reader_modes import ReaderTutorRequest
    from learnloop_sidecar.handlers.library_ask import reader_caller

    intent = params.retrieval_intent
    if intent != "explain" and not params.parent_exchange_id:
        raise SidecarError("validation_error", "Another way and that didn't help follow an answer: name its exchange.")
    caller = reader_caller(vault, repository, extraction_id=params.extraction_id,
                           workbench_session_id=params.workbench_session_id)
    policy = "cold_attempt" if params.cold_active else derive_policy(caller)[0]
    item = vault.practice_items.get(caller.item_id) if caller.item_id else None
    history = RD.ask_history(repository, extraction_id=params.extraction_id, branches=True) \
        if params.parent_exchange_id else []
    ancestors = _ancestors(history, params.parent_exchange_id)
    inquiry = RT.inquiry_exchanges(history, params.parent_exchange_id)
    span_ids = [params.span_id, *params.selection_span_ids]
    if ancestors:
        span_ids = [ancestors[0]["span_id"], *(ancestors[0].get("selection_span_ids") or [])]
    lo_ids = RT.passage_learning_objects(vault, repository, extraction_id=params.extraction_id, span_ids=span_ids)
    personalized = (bool(vault.config.library_ask.personalized_default) if params.personalized is None
                    else bool(params.personalized))
    gaps = open_questions(vault, repository, lo_ids) if personalized and lo_ids else []
    work = RT.learner_work(vault, repository, lo_ids) if personalized else []
    if intent == "alternative" and ancestors:
        # "Another way" looks for the question it is under, not its own words.
        query = RT.reader_query(ancestors[-1]["question_md"], ancestors=ancestors[:-1], gaps=gaps)
    else:
        query = RT.reader_query(params.question, ancestors=ancestors, gaps=gaps)
    shown = RT.shown_span_keys(inquiry) if intent in ("alternative", "remediate") else []
    service = bool(vault.config.source_service.enabled)

    if service:
        from learnloop.instructional.sources import propose_sources

        def find(query_text: str, **kwargs: Any) -> Any:
            return propose_sources(vault, repository, query_text, caller=caller, **kwargs)
    else:
        from learnloop.source_retrieval.find_sources import find_sources_for_caller

        def find(query_text: str, **kwargs: Any) -> Any:
            kwargs.pop("target_hypotheses", None)
            return find_sources_for_caller(vault, repository, query_text, caller=caller, **kwargs)

    lookup = RT.ReaderLookup(
        vault=vault, repository=repository, find=find, policy=policy, query=query, intent=intent,
        learning_object_ids=lo_ids, exclude_span_keys=shown,
        target_hypotheses=RT.named_gap_hypotheses(repository, inquiry) if intent == "remediate" else [],
        shown_source_ids=RT.shown_source_ids(repository, shown) if intent == "alternative" else [],
        personalized=personalized, item=item if policy == "assisted_practice" else None,
        rerank_client=getattr(ctx, "reader_tutor_rerank_client", None), service=service,
    )
    return ReaderTutorRequest(retrieve=lookup, intent=intent if service else "explain", personalized=personalized,
                              learner_work=work, item=item if policy == "assisted_practice" else None)


def item_bound(request: Any) -> bool:
    """A workbench session bound the question to an item (its tools would read wider)."""

    return request is not None and getattr(request, "item", None) is not None


def offers(vault: Any, repository: Any, result: dict[str, Any], *, extraction_id: str) -> dict[str, Any] | None:
    """The Reader's own buttons under an answer (None while ``offers_enabled`` is off)."""

    if not offers_enabled(vault):
        return None
    from learnloop.reader import reader_dialogue as RD
    from learnloop.source_retrieval import reader_tutor as RT

    buttons: list[dict[str, Any]] = []
    active = RD.inquiry_enabled(vault) and bool(
        getattr(getattr(vault.config, "reader_active_reading", None), "enabled", False))
    if active:
        cited = list(result.get("citations") or [])
        excerpt = (result.get("tutor") or {}).get("excerpt")
        if excerpt:
            cited.insert(0, excerpt)
        buttons = RT.next_step_buttons(repository, extraction_id=extraction_id, cited=cited)
    return {"buttons": buttons}


def fallback_practice_request(vault: Any, question: str, event_id: str) -> dict[str, Any] | None:
    """Without the sources service, "Practice this" is a plain ``find_practice``
    on the learner's question (§4.6; the same RPC S0 later fills)."""

    if vault.config.source_service.enabled or not vault.config.practice_index.enabled:
        return None
    query = " ".join(str(question or "").split())[:2000]
    if not query:
        return None
    return {"request": {"query": query}, "caller": {"kind": "reader", "ref": event_id},
            "version": FALLBACK_PRACTICE_VERSION}


def record_excerpt_exposure(repository: Any, result: dict[str, Any]) -> list[str]:
    """The "From your books" excerpt's text is shown: one exposure row (best effort)."""

    excerpt = (result.get("tutor") or {}).get("excerpt")
    if not excerpt:
        return []
    from learnloop.instructional.interventions import record_shown_spans

    try:
        return record_shown_spans(repository, [f"{excerpt['extraction_id']}:{excerpt['span_id']}"],
                                  context="tutor_citation", entity_type="question_event",
                                  entity_id=str(result["event_id"]))
    except Exception:  # noqa: BLE001 - telemetry never fails the answer
        return []


__all__ = [
    "FALLBACK_PRACTICE_VERSION",
    "build_request",
    "fallback_practice_request",
    "item_bound",
    "offers",
    "offers_enabled",
    "prompt_contract_fields",
    "record_excerpt_exposure",
    "retrieval_enabled",
]
