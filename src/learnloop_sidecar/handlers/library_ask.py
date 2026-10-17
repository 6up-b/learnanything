"""Reader workbench RW4a RPCs: ask your library, its notes, compare and the tutor.

Desktop only (pinned in tests/test_mobile_allowlist.py). Each composes the
canonical-sources service under a caller the server derives (never one the
frontend names): the Reader's caller (``reading``), a workbench session's
item (``assisted_practice``), a cold administration (``cold_attempt``,
nothing retrieved). Nothing here writes an attempt, evidence, mastery,
certification, FSRS, scheduler state or a plan. "Practice this question" is
the existing ``find_practice`` RPC with a ``reader`` caller (one RPC, DL3's
and RW1c's too). Kill switches: ``library_ask.enabled``,
``library_ask.expand_graph``, ``reader_compare.enabled``; off, every RPC here
refuses and the prompt contract has no ``library_ask`` key.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval.policy import PolicyRefused
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
LIBRARY_ASK_RPCS: tuple[str, ...] = (
    "reader.library_ask",
    "reader.library_ask_notes",
    "reader.library_compare",
    "reader.library_ask_tutor",
)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW4a (absent while off)."""

    if not LA.library_ask_enabled(vault):
        return {}
    settings = vault.config.library_ask
    return {"library_ask": {
        "expand_graph": bool(settings.expand_graph),
        "personalized_default": bool(settings.personalized_default),
        "compare": LA.compare_enabled(vault),
    }}


def _require(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not LA.library_ask_enabled(vault):
        raise SidecarError("library_ask_disabled",
                           "Ask your library is switched off (library_ask.enabled, source_service.enabled or "
                           "reader_inquiry.enabled is false).")
    return vault, repository


def reader_caller(vault: Any, repository: Any, *, extraction_id: str | None,
                  workbench_session_id: str | None = None) -> Any:
    """The Reader's caller context, built on the server (spec §7.2, G19).

    The Reader context is ``reading``. Asked from inside a workbench session
    whose problem is bound to an item, it is that item's practice context
    (``assisted_practice``); while a cold administration of that item is
    open, ``cold_attempt`` (nothing is retrieved)."""

    from learnloop.instructional.policy import caller_for
    from learnloop.reader import workbench as WB

    item_id = None
    if workbench_session_id:
        try:
            session = WB.session_row(repository, workbench_session_id)
        except Exception as exc:  # noqa: BLE001 - an unknown session is the frontend's mistake
            raise SidecarError("not_found", f"Unknown workbench session {workbench_session_id}.") from exc
        item_id = session.get("practice_item_id") or None
        if item_id is not None and item_id not in vault.practice_items:
            item_id = None
    return caller_for(repository, "reader", extraction_id, item_id=item_id,
                      context="practice" if item_id else None)


def _caller_record(caller: Any) -> dict[str, Any]:
    from learnloop.source_retrieval.policy import derive_policy

    policy, reason = derive_policy(caller)
    return {"kind": caller.kind, "ref": caller.ref, "context": caller.context, "item_id": caller.item_id,
            "policy": policy, "derived_from": reason}


class LibraryAskInput(ParamsModel):
    query: str = Field(min_length=1, max_length=4000)
    entry: str = "reader"
    extraction_id: str | None = None
    #: The passage the question is about: the selection, or the reading passage.
    span_ids: list[str] = Field(default_factory=list, max_length=40)
    learning_object_ids: list[str] = Field(default_factory=list, max_length=20)
    personalized: bool | None = None
    expand: list[str] | None = None
    workbench_session_id: str | None = None


@method("reader.library_ask", LibraryAskInput)
def reader_library_ask(ctx: SidecarContext, params: LibraryAskInput) -> dict[str, Any]:
    """Passages from the learner's library for a question, sources first (spec §7.3)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.instructional.interventions import record_shown_spans
    from learnloop.instructional.sources import propose_sources

    vault, repository = _require(ctx)
    extraction_id = None
    if params.extraction_id:
        extraction_id = resolve_extraction_id(repository, params.extraction_id)
        if extraction_id is None:
            raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    caller = reader_caller(vault, repository, extraction_id=extraction_id,
                           workbench_session_id=params.workbench_session_id)

    def find(query: str, **kwargs: Any) -> Any:
        return propose_sources(vault, repository, query, caller=caller, **kwargs)

    def shown(keys: Any, ask_id: str) -> list[str]:
        return record_shown_spans(repository, list(keys), context="library", entity_type="library_ask",
                                  entity_id=ask_id)

    try:
        result = LA.ask_library(
            vault, repository, params.query, find=find, caller=_caller_record(caller), record_shown=shown,
            entry=params.entry, extraction_id=extraction_id, anchor_span_ids=params.span_ids,
            learning_object_ids=params.learning_object_ids, personalized=params.personalized,
            expand=params.expand,
        )
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except PolicyRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(result)


class LibraryAskIdInput(ParamsModel):
    ask_id: str


@method("reader.library_ask_notes", LibraryAskIdInput)
def reader_library_ask_notes(ctx: SidecarContext, params: LibraryAskIdInput) -> dict[str, Any]:
    """The organizer's line per passage (one listwise call; cached per ask)."""

    vault, repository = _require(ctx)
    try:
        result = LA.organize(vault, repository, params.ask_id,
                             client=getattr(ctx, "library_organizer_client", None))
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(result)


class LibraryCompareInput(ParamsModel):
    ask_id: str
    pinned_span_keys: list[str] = Field(min_length=2, max_length=20)
    #: The open source, whose passage leads the table when it is pinned.
    open_source_id: str | None = None
    workbench_session_id: str | None = None


@method("reader.library_compare", LibraryCompareInput)
def reader_library_compare(ctx: SidecarContext, params: LibraryCompareInput) -> dict[str, Any]:
    """How the pinned passages' sources treat the question (display only until RW4d)."""

    from learnloop.instructional.sources import propose_comparison

    vault, repository = _require(ctx)
    if not LA.compare_enabled(vault):
        raise SidecarError("reader_compare_disabled",
                           "Comparing sources is switched off (reader_compare.enabled or source_service.compare).")
    try:
        row = LA.ask_row(repository, params.ask_id)
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    caller = reader_caller(vault, repository, extraction_id=row["extraction_id"],
                           workbench_session_id=params.workbench_session_id)

    def bound_compare(query: str, **kwargs: Any) -> Any:
        return propose_comparison(vault, repository, query, caller=caller, **kwargs)

    try:
        result = LA.compare(vault, repository, params.ask_id, pinned_keys=params.pinned_span_keys,
                            compare_sources=bound_compare, open_source_id=params.open_source_id)
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except PolicyRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(result)


class LibraryAskTutorInput(ParamsModel):
    ask_id: str
    pinned_span_keys: list[str] = Field(min_length=1, max_length=20)
    question: str | None = Field(default=None, max_length=4000)


@method("reader.library_ask_tutor", LibraryAskTutorInput)
def reader_library_ask_tutor(ctx: SidecarContext, params: LibraryAskTutorInput) -> dict[str, Any]:
    """The tutor on request, answering only from the pinned passages (§3.4 item 11)."""

    from learnloop.ai.errors import CodexUnavailable
    from learnloop.source_retrieval.tutor import PinnedSpanProvider
    from learnloop.tutor.tutor_qa import HeldOutMaterialRefused, QuestionLimitReached, TutorQAError
    from learnloop_sidecar.handlers.ai_providers import provider_label, ready_tutor_qa_provider

    vault, repository = _require(ctx)
    provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError("provider_unavailable",
                           f"{provider_label(provider_name)} is unavailable for the tutor.", retryable=True)
    try:
        result = LA.ask_tutor(vault, repository, client, params.ask_id, pinned_keys=params.pinned_span_keys,
                              question_md=params.question,
                              span_provider=PinnedSpanProvider(params.pinned_span_keys))
    except LA.LibraryAskError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except HeldOutMaterialRefused as exc:
        raise SidecarError("exam_material", str(exc)) from exc
    except QuestionLimitReached as exc:
        raise SidecarError("question_limit_reached", str(exc),
                           details={"limit": exc.limit, "used": exc.used, "context": exc.context}) from exc
    except TutorQAError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except (CodexUnavailable, TimeoutError) as exc:
        raise SidecarError("provider_unavailable",
                           f"{provider_label(provider_name)} is unavailable for the tutor.", retryable=True) from exc
    return versioned(result)


__all__ = ["LIBRARY_ASK_RPCS", "prompt_contract_fields", "reader_caller"]
