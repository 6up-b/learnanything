"""Reader CA6: side by side (ux_reader_compare_ask_v1 §6.4, X9, K14, C5).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``reader.side_by_side_section``: one section of the other book for the
  second pane: the whole section from its jump locator, under protection read
  now (a reading or section that is exam or held-out material is refused,
  never shown), with its neighbouring readable sections so the pane can move
  on. Every block returned is a delivered passage: one ``source_exposure`` row
  each (context ``library``, as CA5a's peek), recorded before the text is
  returned (``span_view.record_span_exposures``). It also names the reading's
  revision, so a highlight or note made in the second pane goes to its own
  book through the ordinary ``reader.capture``.

Which section the pane opens on and where *follow along* takes it are the
Reader's, from ``reader.correspondents`` (judged coverage only for following:
an unchecked search hit never moves a pane). The Reader records
``side_by_side_opened`` and ``follow_along_moved`` (and CA5a's deferred
``corresponding_section_peeked`` / ``corresponding_section_opened``) through
``reader.log_activity`` as salience-only ``reader_action_invoked`` events.

Kill switch ``reader.side_by_side.enabled`` (respecting ``curriculum.enabled``,
which gates the data, and the Reader itself): off, the Reader's prompt
contract has no ``side_by_side`` key, nothing here answers and the Reader is
exactly as before CA6. No model call; nothing here writes a plan, evidence,
mastery, FSRS, scheduler state, provenance or anything served.
"""
from __future__ import annotations

from typing import Any

from learnloop.reader import reader_dialogue as RD
from learnloop.source_retrieval import section_coverage as SC
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
SIDE_BY_SIDE_RPCS: tuple[str, ...] = (
    "reader.side_by_side_section",
)


def side_by_side_enabled(vault: Any) -> bool:
    """Reader CA6's switch (``reader.side_by_side.enabled``), respecting
    ``curriculum.enabled`` (which gates the correspondence data) and the Reader."""

    reader = getattr(vault.config, "reader", None)
    side_by_side = getattr(reader, "side_by_side", None)
    return bool(getattr(side_by_side, "enabled", False)) and SC.enabled(vault) and RD.reader_enabled(vault)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for CA6 (absent while off, so the
    Reader is exactly as before): side by side may be opened."""

    if not side_by_side_enabled(vault):
        return {}
    return {"side_by_side": {"enabled": True}}


class SideBySideSectionInput(ParamsModel):
    #: The other book's reading and the section to show.
    extraction_id: str
    section_id: str


@method("reader.side_by_side_section", SideBySideSectionInput)
def reader_side_by_side_section(ctx: SidecarContext, params: SideBySideSectionInput) -> dict[str, Any]:
    """One section of the other book for the second pane (no model call)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.reader.span_view import SpanViewError, record_span_exposures
    from learnloop_sidecar.handlers.reader import _require_source_reader, _source_id_for_extraction

    vault, repository = ctx.require_vault()
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    if not side_by_side_enabled(vault):
        raise SidecarError("side_by_side_disabled",
                           "Side by side is off (reader.side_by_side.enabled or curriculum.enabled = false).")
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {params.extraction_id!r}.")
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    try:
        view = SC.section_text(vault, repository, resolved, params.section_id)
    except SC.CoverageError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    # The reading's revision, so a highlight or note made in the second pane
    # goes to its own book (reader.capture needs it; Codex review F1).
    run = repository.get_extraction_run(resolved)
    view["revision_id"] = run.get("revision_id") if run else None
    # Every block shown is a delivered passage, recorded before it is returned.
    try:
        view["exposure_event_ids"] = record_span_exposures(
            repository, resolved, [block["span_id"] for block in view["blocks"]], context="library")
    except SpanViewError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned({"section": view})


__all__ = ["SIDE_BY_SIDE_RPCS", "prompt_contract_fields", "side_by_side_enabled"]
