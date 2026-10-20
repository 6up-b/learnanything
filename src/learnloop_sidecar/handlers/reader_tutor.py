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

Kill switches: ``reader_tutor.retrieval_enabled`` (off: no retrieval request
is built and the tutor's prompt contract is today's) and
``reader_tutor.offers_enabled`` (off: no ``tutor_offers`` on the wire, so the
Reader renders no buttons). Either one on, a workbench-bound question carries
its :func:`bound_ask` (its item, guards and accounting) whatever the retrieval
switch (fix round 5, R1); both off, the Reader is the base's, byte for byte.
"""
from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class ReaderRestriction:
    """What one ``reader.ask`` is restricted to, derived on the server
    whatever the retrieval switch says (Codex re-review F2).

    ``policy`` is the caller's derived policy (``cold_attempt`` when the
    client says cold, or when the server derives a cold administration of the
    bound item); ``item_id`` is the item a workbench session binds the
    question to. ``active`` is False while both RW1c switches are off: the
    Reader is then the base's, byte for byte (only the client's cold flag
    counts, as before RW1c)."""

    caller: Any
    policy: str
    item_id: str | None
    client_cold: bool
    active: bool

    @property
    def cold(self) -> bool:
        return self.policy == "cold_attempt"

    def stored(self) -> dict[str, Any] | None:
        """The restriction persisted on the question (``source_context.reader_caller``),
        so a caller rebuilt from it later is never wider; None when unrestricted."""

        if not self.active or not (self.cold or self.item_id):
            return None
        return {"policy": self.policy, "cold": self.cold, "item_id": self.item_id,
                "derived_from": "client_cold" if self.client_cold else "server"}


def restriction(vault: Any, repository: Any, params: Any) -> ReaderRestriction:
    """The question's restriction (see :class:`ReaderRestriction`)."""

    client_cold = bool(params.cold_active)
    if not (retrieval_enabled(vault) or offers_enabled(vault)):
        return ReaderRestriction(caller=None, policy="cold_attempt" if client_cold else "reading",
                                 item_id=None, client_cold=client_cold, active=False)
    from learnloop.source_retrieval.policy import derive_policy
    from learnloop_sidecar.handlers.library_ask import reader_caller

    caller = reader_caller(vault, repository, extraction_id=params.extraction_id,
                           workbench_session_id=params.workbench_session_id)
    policy = "cold_attempt" if client_cold else derive_policy(caller)[0]
    return ReaderRestriction(caller=caller, policy=policy, item_id=caller.item_id or None,
                             client_cold=client_cold, active=True)


def bound_ask(vault: Any, repository: Any, params: Any, restricted: ReaderRestriction) -> Any:
    """The question's :class:`reader_modes.BoundAsk`, or None when no workbench session binds an item.

    Fix round 5, ruling R1: built whenever either RW1c switch is on and the
    request names a workbench session the server resolves to an item, before
    and apart from the retrieval request (``build_request``, None with
    retrieval off). The item, its guards over the complete delivered context
    and the thread, and its accounting therefore hold with retrieval off,
    cold or not. Both switches off, ``restricted.active`` is False and the
    Reader is the base's, byte for byte.

    The practice session is the workbench's own resolution
    (``handlers.workbench._question_hints``): the session's practice session
    while it is open, else the most recent open one, else none. It is the
    record of where the question was asked; the hint counts in the ITEM's
    window whatever the session (fix round 4, F1:
    ``Repository.count_hint_equivalent_question_events``)."""

    if not restricted.active or not restricted.item_id or not params.workbench_session_id:
        return None
    item = vault.practice_items.get(restricted.item_id)
    if item is None:
        return None
    from learnloop.reader import workbench as WB
    from learnloop.source_retrieval import reader_tutor as RT
    from learnloop.tutor.reader_modes import BoundAsk

    session = WB.session_row(repository, params.workbench_session_id)
    practice_session = session.get("practice_session_id")
    if practice_session:
        row = repository.fetch_session(practice_session)
        if row is None or row.get("ended_at") is not None:
            practice_session = None
    if not practice_session:
        recent = repository.most_recent_open_session()
        practice_session = recent["id"] if recent else None
    guard = RT.ItemBoundGuard(repository, item)
    # ``cold`` is the restriction's (the client's flag or the server's own
    # derivation): a cold Ask is a hint whatever its type, with or without a
    # fetchable cold attempt (``BoundAsk.hint_equivalent``).
    return BoundAsk(item=item, practice_session_id=practice_session, cold=restricted.cold,
                    context_guard=guard, answer_guard=guard.text_leaks, answer_overlap=guard.text_overlap)


@dataclass(frozen=True)
class ReaderInputs:
    """The model-written inputs one lookup builds from, AS READ (fix round 7, R1).

    ``gaps`` are the open-gap and misconception statements on the passage's
    LOs (LearnLoop's reading); ``learner_work`` is the bridge's context built
    from the same ``gaps`` (one copy) and the learner's own workbench steps;
    ``misconceptions`` are, bound under "that didn't help", the remediation
    targets the sources service would put in the verification's context with
    their corrections (resolved here so the service never resolves a copy of
    its own; None otherwise). Nothing is withheld here: bound, the tutor
    reads every model-written text of each model call as one
    (``reader_modes.plan_bound_delivery``) and the lookup builds its query
    from what that plan kept, so no per-source guarded copy is ever
    concatenated with another (round 6's separate guards were bypassable)."""

    gaps: list[dict[str, Any]]
    learner_work: list[dict[str, Any]]
    misconceptions: list[Any] | None = None


def reader_inputs(vault: Any, repository: Any, *, lo_ids: list[str], personalized: bool, intent: str,
                  target_hypotheses: list[dict[str, str]], binding: Any) -> ReaderInputs:
    """The :class:`ReaderInputs` of one lookup."""

    from learnloop.source_retrieval import reader_tutor as RT
    from learnloop.source_retrieval.library_ask import open_questions

    gaps = open_questions(vault, repository, lo_ids) if personalized and lo_ids else []
    work = RT.learner_work(vault, repository, lo_ids, gaps=gaps) if personalized else []
    misconceptions = None
    if binding is not None and intent == "remediate" and vault.config.source_service.enabled:
        from learnloop.instructional.sources import resolve_misconceptions

        misconceptions = list(resolve_misconceptions(repository, target_hypotheses, item=binding.item))
    return ReaderInputs(gaps=gaps, learner_work=work, misconceptions=misconceptions)


def build_request(ctx: Any, vault: Any, repository: Any, params: Any, restricted: ReaderRestriction,
                  binding: Any = None) -> Any:
    """The ``ReaderTutorRequest`` for one ``reader.ask``, or None while retrieval is off.

    ``binding`` (:func:`bound_ask`) is built apart and handed to the tutor on
    its own; the request only scopes the lookup and the learner work by it."""

    if not retrieval_enabled(vault):
        if params.retrieval_intent != "explain":
            raise SidecarError("validation_error",
                               "Another way and that didn't help are switched off (reader_tutor.retrieval_enabled).")
        return None
    from learnloop.reader import reader_dialogue as RD
    from learnloop.source_retrieval import reader_tutor as RT
    from learnloop.tutor.reader_modes import ReaderTutorRequest

    intent = params.retrieval_intent
    if intent != "explain" and not params.parent_exchange_id:
        raise SidecarError("validation_error", "Another way and that didn't help follow an answer: name its exchange.")
    caller, policy = restricted.caller, restricted.policy
    item = binding.item if binding is not None else None
    # The tutor's own RW1c fields are read here (the shown passages), so the
    # projection includes them whatever the history RPC's gate (R4).
    history = RD.ask_history(repository, extraction_id=params.extraction_id, branches=True, tutor_views=True) \
        if params.parent_exchange_id else []
    ancestors = _ancestors(history, params.parent_exchange_id)
    inquiry = RT.inquiry_exchanges(history, params.parent_exchange_id)
    span_ids = [params.span_id, *params.selection_span_ids]
    if ancestors:
        span_ids = [ancestors[0]["span_id"], *(ancestors[0].get("selection_span_ids") or [])]
    lo_ids = RT.passage_learning_objects(vault, repository, extraction_id=params.extraction_id, span_ids=span_ids)
    personalized = (bool(vault.config.library_ask.personalized_default) if params.personalized is None
                    else bool(params.personalized))
    hypotheses = RT.named_gap_hypotheses(repository, inquiry) if intent == "remediate" else []
    # The model-written inputs as read (fix round 7, R1): the lookup builds
    # its query from them at call time, from what the tutor's one plan for
    # every model call kept when bound (``reader_modes.plan_bound_delivery``).
    inputs = reader_inputs(vault, repository, lo_ids=lo_ids, personalized=personalized, intent=intent,
                           target_hypotheses=hypotheses, binding=binding)
    if intent == "alternative" and ancestors:
        # "Another way" looks for the question it is under, not its own words.
        question, query_ancestors = ancestors[-1]["question_md"], ancestors[:-1]
    else:
        question, query_ancestors = params.question, ancestors
    shown = list(dict.fromkeys([*RT.shown_span_keys(inquiry), *RT.offer_shown_span_keys(repository, inquiry)])) \
        if intent in ("alternative", "remediate") else []
    service = bool(vault.config.source_service.enabled)

    if service:
        from learnloop.instructional.sources import propose_sources

        def find(query_text: str, **kwargs: Any) -> Any:
            return propose_sources(vault, repository, query_text, caller=caller, **kwargs)
    else:
        from learnloop.source_retrieval.find_sources import find_sources_for_caller

        def find(query_text: str, **kwargs: Any) -> Any:
            kwargs.pop("target_hypotheses", None)
            kwargs.pop("misconceptions", None)  # the base explain resolves none
            return find_sources_for_caller(vault, repository, query_text, caller=caller, **kwargs)

    lookup = RT.ReaderLookup(
        vault=vault, repository=repository, find=find, policy=policy, question=question,
        ancestors=query_ancestors, gaps=inputs.gaps, misconceptions=inputs.misconceptions, intent=intent,
        learning_object_ids=lo_ids, exclude_span_keys=shown,
        target_hypotheses=hypotheses,
        shown_source_ids=RT.shown_source_ids(repository, shown) if intent == "alternative" else [],
        personalized=personalized, item=item if policy == "assisted_practice" else None,
        rerank_client=getattr(ctx, "reader_tutor_rerank_client", None), service=service,
    )
    # The requested intent is the PRESENTATION's (fix round 4, F4): "another
    # way" never repeats a shown passage, with the sources service off too.
    # Only the service's effective retrieval intent falls back to explain,
    # inside the lookup (``ReaderLookup``: G53's base find_sources).
    return ReaderTutorRequest(retrieve=lookup, intent=intent, personalized=personalized,
                              learner_work=inputs.learner_work, gaps=inputs.gaps,
                              misconceptions=inputs.misconceptions, policy=policy,
                              shown_span_keys=shown if intent == "alternative" else ())


def tools_refused(restricted: ReaderRestriction) -> bool:
    """No tool, practice request or offer lookup may run for this question
    (G48, Codex review F2, re-review F2): during a cold administration,
    whether the client says so (``coldActive``) or the server derives it from
    the bound item, and inside a bound session, where a tool's own caller
    would read wider than the session's ``assisted_practice``. Derived from
    the restriction, never from the retrieval switch."""

    return restricted.cold or (restricted.active and restricted.item_id is not None)


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
    "bound_ask",
    "build_request",
    "ReaderRestriction",
    "fallback_practice_request",
    "offers",
    "offers_enabled",
    "prompt_contract_fields",
    "record_excerpt_exposure",
    "restriction",
    "retrieval_enabled",
    "tools_refused",
]
