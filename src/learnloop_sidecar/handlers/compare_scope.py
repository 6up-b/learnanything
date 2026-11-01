"""Reader CA3 RPCs: reading the ask box's words for a comparison, and the learner's change of it.

* ``reader.compare_scope`` -- read one pressed text of the ask box (``mode``
  ``ask``: a comparison or a library question? which books are named? the
  topic) or of a comparison's refine box (``refine``: other books, or a view?)
  with one Decider request over the books the caller's comparison may read
  (:mod:`learnloop.source_retrieval.compare_scope`). It answers at once with a
  library job (``reader.library_job`` reads it; the sidecar is serial, so a
  Decider call never holds the Reader's other requests).
* ``reader.compare_scope_correction`` -- the learner changed the reading's
  books (``×``, *+ add a book*) or reworded it (*change*): one
  ``learner_card`` row superseding it, so the reading's error is measurable.

The comparison itself is ``reader.library_compare`` (one request for every
door). Kill switch ``reader_compare.scope_enabled`` (with the comparison's
own switches): off, both RPCs refuse and the prompt contract has no
``compare_scope`` key. A cold administration reads nothing (nothing is
compared then). Never evidence: ledger rows and receipts only. Desktop only
(pinned in tests/test_mobile_allowlist.py).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from learnloop.ids import new_ulid
from learnloop.source_retrieval import compare_scope as CS
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.library_ask import _require, _start, reader_caller, scope_enabled
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
COMPARE_SCOPE_RPCS: tuple[str, ...] = ("reader.compare_scope", "reader.compare_scope_correction")


def _require_scope(ctx: SidecarContext):
    vault, repository = _require(ctx)
    if not scope_enabled(vault):
        raise SidecarError("reader_compare_scope_disabled",
                           "Comparing from anywhere is switched off (reader_compare.scope_enabled, "
                           "reader_compare.enabled or source_service.compare is false).")
    return vault, repository


def _books(vault: Any, repository: Any, caller: Any) -> list[CS.Book]:
    """The books the caller's comparison may read (its policy's scope)."""

    from learnloop.source_retrieval.find_sources import scope_for
    from learnloop.source_retrieval.policy import derive_policy

    policy, _reason = derive_policy(caller)
    if policy == "cold_attempt":
        return []
    item = vault.practice_items.get(caller.item_id) if caller.item_id else None
    lo_ids = list(caller.learning_object_ids) or ([item.learning_object_id] if item is not None else [])
    scope = scope_for(vault, repository, policy=policy, scope="library", learning_object_ids=lo_ids, item=item)
    return CS.library_books(vault, repository, scope)


def books_payload(vault: Any, repository: Any, caller: Any) -> list[dict[str, Any]]:
    """The library's books for *+ add a book* (titles only)."""

    return [book.as_dict() for book in _books(vault, repository, caller)]


class CompareScopeInput(ParamsModel):
    text: str = Field(min_length=1, max_length=4000)
    mode: Literal["ask", "refine"] = "ask"
    #: The open book (the Reader's caller), when there is one.
    extraction_id: str | None = None
    #: Refine: the books compared now.
    current_source_ids: list[str] = Field(default_factory=list, max_length=40)
    workbench_session_id: str | None = None


@method("reader.compare_scope", CompareScopeInput)
def reader_compare_scope(ctx: SidecarContext, params: CompareScopeInput) -> dict[str, Any]:
    """Read the words for a comparison (one Decider request, off the request path)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.source_retrieval.policy import derive_policy

    vault, repository = _require_scope(ctx)
    extraction_id = None
    if params.extraction_id:
        extraction_id = resolve_extraction_id(repository, params.extraction_id)
        if extraction_id is None:
            raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    caller = reader_caller(vault, repository, extraction_id=extraction_id,
                           workbench_session_id=params.workbench_session_id)
    policy, _reason = derive_policy(caller)
    client_factory = getattr(ctx, "compare_scope_client_factory", None)

    def work(worker_repo: Any) -> dict[str, Any]:
        books = _books(vault, worker_repo, caller)
        library = [book.as_dict() for book in books]
        if policy == "cold_attempt":
            reading = CS.Reading(f"cscp_{new_ulid().lower()}", params.mode, CS.FALLBACK, reason="cold_attempt")
        elif len(books) < 2 and params.mode == "ask":
            # Nothing to compare: no reading is paid for; the ask box asks.
            reading = CS.Reading(f"cscp_{new_ulid().lower()}", params.mode, CS.FALLBACK, reason="too_few_books")
        else:
            reading = CS.read(vault.root, vault.config, worker_repo, text=params.text, books=books,
                              mode=params.mode, current_source_ids=params.current_source_ids,
                              client_factory=client_factory)
        titles = {book["source_id"]: book["title"] for book in library}
        payload = reading.as_dict()
        payload["books"] = [{"source_id": source_id, "title": titles.get(source_id)}
                            for source_id in reading.source_ids]
        payload["library"] = library
        return payload

    return _start(ctx, "scope", None, work)


class CompareScopeCorrectionInput(ParamsModel):
    judgment_id: str
    #: The books the learner compares instead; None: they reworded it (*change*).
    source_ids: list[str] | None = Field(default=None, max_length=40)


@method("reader.compare_scope_correction", CompareScopeCorrectionInput)
def reader_compare_scope_correction(ctx: SidecarContext, params: CompareScopeCorrectionInput) -> dict[str, Any]:
    """The learner's change of a reading (a ``learner_card`` row)."""

    _vault, repository = _require_scope(ctx)
    try:
        judgment_id = CS.record_correction(repository, params.judgment_id, source_ids=params.source_ids)
    except ValueError as exc:
        raise SidecarError("not_found", "That reading is not on record.") from exc
    return versioned({"judgment_id": judgment_id})


__all__ = ["COMPARE_SCOPE_RPCS", "books_payload"]
