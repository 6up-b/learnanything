"""Reader workbench RW4d RPCs: keep a comparison, remove it, reopen it, its marks.

Desktop only (pinned in tests/test_mobile_allowlist.py). No model call:
each reads the stored comparison (the sources spec's ``source_comparisons``
row) and writes, on the learner's press only, source-object proposals through
``reader.source_objects`` (``source_retrieval.kept_comparisons``). Nothing here
writes a concept edge, facet merge, prerequisite, LO change, attempt,
evidence, mastery, FSRS, scheduler state or a plan.

Kill switch ``reader_compare.keep_enabled``: off, every RPC here refuses,
the prompt contract has no ``compare_keep`` key, and RW4a's compare and RW1c's
tutor offers are as they were. A follow-up on a library ask is bound by the
ask's stored caller (RW4a's ``follow_up_caller``): while a cold administration
of its item is open nothing is kept or reopened; a tutor comparison likewise
by its request's stored item.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.source_retrieval import kept_comparisons as KC
from learnloop.source_retrieval import library_ask as LA
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
KEPT_COMPARISON_RPCS: tuple[str, ...] = (
    "reader.library_compare_keep",
    "reader.library_compare_remove",
    "reader.library_compare_reopen",
    "reader.kept_comparisons",
)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW4d (absent while off)."""

    library = KC.keep_enabled(vault)
    tutor = KC.tutor_keep_enabled(vault)
    if not (library or tutor):
        return {}
    return {"compare_keep": {"library": library, "tutor": tutor, "perspectives": library,
                             "max_perspectives": KC.MAX_PERSPECTIVES}}


def _require(ctx: SidecarContext, *, tutor: bool = False):
    vault, repository = ctx.require_vault()
    enabled = KC.tutor_keep_enabled(vault) if tutor else KC.keep_enabled(vault)
    if not enabled:
        raise SidecarError("reader_compare_keep_disabled",
                           "Keeping comparisons is switched off (reader_compare.keep_enabled, reader_compare.enabled "
                           "or source_service.compare is false).")
    return vault, repository


def _error(exc: LA.LibraryAskError) -> SidecarError:
    return SidecarError(exc.code, str(exc))


def _cold_guard(vault: Any, repository: Any, ask_id: str) -> None:
    """Refuse while the ask's (or the tutor request's) item has a cold administration open."""

    from learnloop.instructional.policy import cold_administration_open
    from learnloop.source_retrieval.policy import derive_policy
    from learnloop_sidecar.handlers.library_ask import follow_up_caller

    try:
        row = LA.ask_row(repository, ask_id)
    except LA.LibraryAskError as exc:
        raise _error(exc) from exc
    caller = (row.get("manifest") or {}).get("caller") or {}
    item_id = caller.get("item_id") if isinstance(caller, dict) else None
    if (row.get("manifest") or {}).get("tool_call_id"):
        if item_id and cold_administration_open(repository, item_id):
            raise SidecarError("cold_attempt", "Nothing from your books is kept or shown while a cold attempt is open.")
        return
    policy, _reason = derive_policy(follow_up_caller(vault, repository, row))
    if policy == "cold_attempt":
        raise SidecarError("cold_attempt", "Nothing from your books is kept or shown while a cold attempt is open.")


class TakeInput(ParamsModel):
    text: str = Field(min_length=1, max_length=KC.MAX_TAKE_CHARS)
    #: One passage key (a claim) or two (a pair), as the table's rows name them.
    keys: list[str] = Field(min_length=1, max_length=2)


class KeepInput(ParamsModel):
    #: A library ask whose comparison is shown, or the tutor's comparison request.
    ask_id: str | None = None
    tool_call_id: str | None = None
    #: The reading the tutor's answer was in (a tutor keep's mark sits there too).
    extraction_id: str | None = None
    takes: list[TakeInput] = Field(default_factory=list, max_length=KC.MAX_TAKES)


@method("reader.library_compare_keep", KeepInput)
def reader_library_compare_keep(ctx: SidecarContext, params: KeepInput) -> dict[str, Any]:
    """Keep this comparison: its claims and relations as proposals, with the
    learner's take (spec §7.8; G43). A second press adds only new takes."""

    if (params.ask_id is None) == (params.tool_call_id is None):
        raise SidecarError("validation_error", "Name the library question or the tutor's comparison to keep.")
    takes = [take.model_dump() for take in params.takes]
    if params.tool_call_id is not None:
        from learnloop.instructional.policy import cold_administration_open

        vault, repository = _require(ctx, tutor=True)
        try:
            found = KC.tutor_comparison(repository, params.tool_call_id)
        except LA.LibraryAskError as exc:
            raise _error(exc) from exc
        item_id = (found["request"].get("context") or {}).get("item_id")
        if item_id and cold_administration_open(repository, item_id):
            raise SidecarError("cold_attempt", "Nothing from your books is kept while a cold attempt is open.")
        try:
            return versioned(KC.keep_tutor(vault, repository, params.tool_call_id,
                                           extraction_id=params.extraction_id, takes=takes))
        except LA.LibraryAskError as exc:
            raise _error(exc) from exc
    vault, repository = _require(ctx)
    _cold_guard(vault, repository, str(params.ask_id))
    try:
        return versioned(KC.keep(vault, repository, str(params.ask_id), takes=takes))
    except LA.LibraryAskError as exc:
        raise _error(exc) from exc


class KeptAskInput(ParamsModel):
    ask_id: str
    open_source_id: str | None = None


@method("reader.library_compare_remove", KeptAskInput)
def reader_library_compare_remove(ctx: SidecarContext, params: KeptAskInput) -> dict[str, Any]:
    """Remove: the keep's proposals are superseded, never deleted."""

    vault, repository = ctx.require_vault()
    if not (KC.keep_enabled(vault) or KC.tutor_keep_enabled(vault)):
        _require(ctx)
    try:
        return versioned(KC.remove(vault, repository, params.ask_id))
    except LA.LibraryAskError as exc:
        raise _error(exc) from exc


@method("reader.library_compare_reopen", KeptAskInput)
def reader_library_compare_reopen(ctx: SidecarContext, params: KeptAskInput) -> dict[str, Any]:
    """A kept comparison's table again (from ``⇄``), from the stored row; no model call."""

    vault, repository = ctx.require_vault()
    if not (KC.keep_enabled(vault) or KC.tutor_keep_enabled(vault)):
        _require(ctx)
    _cold_guard(vault, repository, params.ask_id)
    try:
        return versioned(KC.reopen(vault, repository, params.ask_id, open_source_id=params.open_source_id))
    except LA.LibraryAskError as exc:
        raise _error(exc) from exc


class KeptMarksInput(ParamsModel):
    extraction_id: str


@method("reader.kept_comparisons", KeptMarksInput)
def reader_kept_comparisons(ctx: SidecarContext, params: KeptMarksInput) -> dict[str, Any]:
    """The ``⇄`` marks for the open reading (the learner's own; outside the cue budget)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id

    vault, repository = ctx.require_vault()
    if not (KC.keep_enabled(vault) or KC.tutor_keep_enabled(vault)):
        _require(ctx)
    extraction_id = resolve_extraction_id(repository, params.extraction_id) or params.extraction_id
    return versioned(KC.kept_marks(vault, repository, extraction_id))


__all__ = ["KEPT_COMPARISON_RPCS", "prompt_contract_fields"]
