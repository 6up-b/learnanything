"""Deliverable curriculum C0a RPCs: section coverage and its read API
(spec_deliverable_curriculum_v1 §6.4–6.5; ux_reader_compare_ask_v1 §6, §12.3).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``reader.correspondents``: from one section, the other books' sections
  whose judged coverage names the same LOs, per LO and per book (no model
  call, no write); with none judged and ``search_fallback`` on, the live
  search hits per book labelled "found by search, not checked" (CA5a's
  pressed action reads them; the Guide's quiet line passes it off).
  RW5d P4a: while ``reader.correspondence.enabled`` and ``figures.enabled``
  are on, a judged correspondent section lists the kept figures anchored in
  it (``figures``; absent when it has none), so a figure follows the section.
* ``curriculum.coverage_correct``: *not about this* / *also about…* (or
  ``none``): a ``learner_card`` verdict and a ``learner`` row, nothing else.
* ``reader.correspondent_peek`` (CA5a): a hit's first blocks, under
  protection read now and restricted to the hit's own section, with one
  ``source_exposure`` event per block shown.
* ``reader.correspondent_dismiss`` (CA5a): *not about this* on an unchecked
  hit (or its undo) as one idempotent operation in one transaction; on a
  judged line (CA5) it names the LOs the line is listed under.
* ``reader.correspondence_preferences`` / ``reader.set_correspondence_preferences``
  (CA5): *hide for this book* / *hide everywhere* on the Guide's *also in
  your books*, kept in the vault's ``[reader.correspondence]`` config (as the
  margin marks' per-book switch is), and Settings bringing it back.

``reader.correspondents`` and the peek read through one library per vault
(``SC.LibraryCache``, CA5): crossing sections reuses the parsed readings
while the vault, protection and readings are unchanged; protection is read
again on every call.

Kill switch ``curriculum.enabled``: off, every RPC here refuses and no call
is made. Reader CA5a's ``reader.correspondence.enabled`` (respecting it) is
the presentation's: off, the Reader's prompt contract has no
``correspondence`` key and the Guide shows no *find this section in my other
books*; the RPCs here keep C0a's behaviour. Display and retrieval context only: nothing here writes a plan,
evidence, mastery, FSRS, scheduler state, provenance or anything served.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from learnloop.router_objective import exposure
from learnloop.figures import service as FS
from learnloop.source_retrieval import section_coverage as SC
from learnloop.reader import reader_dialogue as RD
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
CORRESPONDENT_RPCS: tuple[str, ...] = (
    "reader.correspondents",
    "curriculum.coverage_correct",
)
#: Reader CA5a's own RPCs (the peek and the one-operation *not about this*;
#: pinned desktop-only too). Refused while ``reader.correspondence.enabled``
#: (or ``curriculum.enabled``) is off.
FIND_SECTION_RPCS: tuple[str, ...] = (
    "reader.correspondent_peek",
    "reader.correspondent_dismiss",
)
#: Reader CA5's own RPCs (the line's hide preferences; desktop only).
ALSO_IN_BOOKS_RPCS: tuple[str, ...] = (
    "reader.correspondence_preferences",
    "reader.set_correspondence_preferences",
)
_REGISTRY_LOCK = threading.Lock()


def find_section_enabled(vault: Any) -> bool:
    """Reader CA5a's switch (``reader.correspondence.enabled``), respecting
    ``curriculum.enabled`` (which gates the data) and the Reader itself."""

    reader = getattr(vault.config, "reader", None)
    correspondence = getattr(reader, "correspondence", None)
    return bool(getattr(correspondence, "enabled", False)) and SC.enabled(vault) and RD.reader_enabled(vault)


def figures_follow_enabled(vault: Any) -> bool:
    """RW5d P4a (figures follow the section): CA5's ``reader.correspondence.enabled``
    (respecting ``curriculum.enabled`` and the Reader) with ``figures.enabled``."""

    return find_section_enabled(vault) and FS.enabled(vault)


def hidden_everywhere(vault: Any) -> bool:
    return bool(getattr(vault.config.reader.correspondence, "hide_everywhere", False))


def hidden_sources(vault: Any) -> list[str]:
    return [str(source) for source in getattr(vault.config.reader.correspondence, "hidden_sources", ()) or ()]


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for CA5a and CA5 (absent while
    off, so the Guide is exactly as before): the pressed *find this section
    in my other books* (CA5a, for a section with no judged coverage) and the
    one-line *also in your books* (CA5, for a section with judged coverage),
    with the learner's hide preferences for that line."""

    if not find_section_enabled(vault):
        return {}
    return {"correspondence": {"enabled": True, "find_section": True, "also_in_books": True,
                               "hidden_everywhere": hidden_everywhere(vault),
                               "hidden_sources": hidden_sources(vault)}}


def _library_cache(ctx: SidecarContext) -> SC.LibraryCache:
    """The open vault's library cache (one per database: after a vault switch nothing of the other is seen)."""

    repository = getattr(ctx, "repository", None)
    database = str(Path(repository.sqlite_path).resolve()) if repository is not None else ""
    with _REGISTRY_LOCK:
        caches = getattr(ctx, "correspondent_libraries", None)
        if not isinstance(caches, dict):
            caches = {}
            ctx.correspondent_libraries = caches  # type: ignore[attr-defined]
        return caches.setdefault(database, SC.LibraryCache())


def _require(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]:
    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop_sidecar.handlers.reader import _require_source_reader, _source_id_for_extraction

    vault, repository = ctx.require_vault()
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    if not SC.enabled(vault):
        raise SidecarError("curriculum_disabled", "Section coverage is off (curriculum.enabled = false).")
    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    return vault, repository, resolved


def _sidecar_error(exc: SC.CoverageError) -> SidecarError:
    return SidecarError(exc.code, str(exc))


# -- reader.correspondents -----------------------------------------------------------------------


class CorrespondentsInput(ParamsModel):
    extraction_id: str
    section_id: str
    #: With no judged correspondent, return the live search hits labelled
    #: unchecked (CA5a's pressed action); False reads judged coverage only
    #: (the Guide's quiet line).
    search_fallback: bool = True


@method("reader.correspondents", CorrespondentsInput)
def reader_correspondents(ctx: SidecarContext, params: CorrespondentsInput) -> dict[str, Any]:
    """The other books' sections that treat this section's LOs (no model call, no write)."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    try:
        view = SC.correspondents(vault, repository, resolved, params.section_id,
                                 search_fallback=params.search_fallback,
                                 embedder=getattr(ctx, "coverage_embedder", None), cache=_library_cache(ctx))
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    if view.get("status") == "judged" and figures_follow_enabled(vault):
        _with_figures(ctx, vault, repository, view)
    # Always null, kept for the answer's shape: no RPC starts a section's coverage job (the CLI's
    # `learnloop curriculum cover` judges a book's sections).
    view["job"] = None
    return versioned(view)


def _with_figures(ctx: SidecarContext, vault: Any, repository: Any, view: dict[str, Any]) -> None:
    """RW5d P4a (spec §10.2): each judged correspondent section lists the kept
    figures anchored in it (``figures``, present only when there is one): a
    figure the learner built reading Strang §6.4 is offered from the section
    of another book that corresponds to it. A read joined through the
    figure's anchor section (nothing is copied, Q8). Protected on both sides:
    the open section has judged correspondents only when it is not protected,
    a correspondent section is in the protected library only when none of its
    spans is withheld, and a figure is listed only while nothing it was built
    from (or lands on) is held out now (:func:`FS.section_figures`). Anything
    unreadable lists no figure; the rest of the read stands."""

    wanted: dict[str, set[str]] = {}
    for group in view.get("learning_objects") or ():
        for source in group.get("sources") or ():
            for section in source.get("sections") or ():
                wanted.setdefault(str(section["extraction_id"]), set()).add(str(section["section_id"]))
    if not wanted:
        return
    found: dict[tuple[str, str], list[dict[str, Any]]] = {}
    try:
        library = _library_cache(ctx).get(vault, repository)
        for extraction_id, section_ids in wanted.items():
            reading = library.reading(extraction_id)
            if reading is None:
                continue

            def section_of(span_id: str, reading: Any = reading) -> str | None:
                # A withheld section (any withheld span) is not one of the reading's sections.
                section_id = reading.all_spans.get(span_id)
                return section_id if section_id in reading.sections else None

            for section_id, refs in FS.section_figures(vault, repository, extraction_id, section_of).items():
                if section_id in section_ids:
                    found[(extraction_id, section_id)] = refs
    except Exception:  # noqa: BLE001 - fail closed and quiet: no figure rather than no correspondents
        LOG.warning("figures follow the section: the figures could not be read", exc_info=True)
        return
    for group in view.get("learning_objects") or ():
        for source in group.get("sources") or ():
            for section in source.get("sections") or ():
                refs = found.get((str(section["extraction_id"]), str(section["section_id"])))
                if refs:
                    section["figures"] = [dict(ref) for ref in refs]


# -- curriculum.coverage_correct -------------------------------------------------------------------


class CoverageCorrectInput(ParamsModel):
    extraction_id: str
    section_id: str
    learning_object_id: str
    #: is_about | not_about | none (clears an earlier correction)
    choice: str
    #: The learner's "also about…" words, kept as typed (bounded).
    text: str | None = None


@method("curriculum.coverage_correct", CoverageCorrectInput)
def curriculum_coverage_correct(ctx: SidecarContext, params: CoverageCorrectInput) -> dict[str, Any]:
    """*Not about this* / *also about…*: kept across re-judgments; marks nothing as known."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    try:
        row = SC.correct(vault, repository, resolved, params.section_id, params.learning_object_id, params.choice,
                         text=params.text)
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    return versioned({"correction": row})


# -- Reader CA5a: peek and "not about this" on an unchecked hit -----------------------------------


def _require_find_section(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]:
    vault, repository, resolved = _require(ctx, extraction_id)
    if not find_section_enabled(vault):
        raise SidecarError("correspondence_disabled",
                           "Finding this section in your other books is off (reader.correspondence.enabled = false).")
    return vault, repository, resolved


class CorrespondentPeekInput(ParamsModel):
    #: The hit's reading and section.
    extraction_id: str
    section_id: str


@method("reader.correspondent_peek", CorrespondentPeekInput)
def reader_correspondent_peek(ctx: SidecarContext, params: CorrespondentPeekInput) -> dict[str, Any]:
    """A hit's first blocks for the Guide's peek (Codex review F1, F2): no model call."""

    from learnloop.reader.span_view import SpanViewError, record_span_exposures

    vault, repository, resolved = _require_find_section(ctx, params.extraction_id)
    try:
        view = SC.peek(vault, repository, resolved, params.section_id, cache=_library_cache(ctx))
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    # Every block shown is a delivered passage, recorded before it is returned.
    try:
        view["exposure_event_ids"] = record_span_exposures(
            repository, resolved, [block["span_id"] for block in view["blocks"]], context="library",
            exposure_fields=exposure.fields(vault.config, repository, context="library"))
    except SpanViewError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned({"peek": view})


class CorrespondentDismissInput(ParamsModel):
    #: The open section.
    extraction_id: str
    section_id: str
    #: The hit.
    target_extraction_id: str
    target_section_id: str
    #: The client's name for this operation (the same id again writes nothing).
    operation_id: str
    #: Undo the operation it names instead.
    undo_of: str | None = None
    #: Reader CA5 (a judged line): the shared LOs the line is listed under;
    #: absent, every LO of the open section (CA5a's unchecked hit).
    learning_object_ids: list[str] | None = None


@method("reader.correspondent_dismiss", CorrespondentDismissInput)
def reader_correspondent_dismiss(ctx: SidecarContext, params: CorrespondentDismissInput) -> dict[str, Any]:
    """*Not about this* on an unchecked hit, or its undo: one transaction (Codex review F3, F6)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id

    vault, repository, origin = _require_find_section(ctx, params.extraction_id)
    target = resolve_extraction_id(repository, params.target_extraction_id)
    if target is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {params.target_extraction_id!r}.")
    try:
        record = SC.dismiss(vault, repository, (origin, params.section_id), (target, params.target_section_id),
                            operation_id=params.operation_id, undo_of=params.undo_of,
                            learning_object_ids=params.learning_object_ids)
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    return versioned({"operation": record})


# -- Reader CA5: the line's hide preferences --------------------------------------------------------


def _preferences(vault: Any, repository: Any) -> dict[str, Any]:
    """What the Reader and Settings show: the switch, and what the learner hid (books by name)."""

    if not find_section_enabled(vault):
        return {"enabled": False, "hide_everywhere": False, "hidden_sources": []}
    from learnloop.source_retrieval.corpus import library_scope

    titles: dict[str, str] = {}
    try:
        for extraction in library_scope(repository).extractions.values():
            titles.setdefault(extraction.source_id, extraction.title)
    except Exception:  # noqa: BLE001 - a title is a label; the preference stands without it
        titles = {}
    return {"enabled": True, "hide_everywhere": hidden_everywhere(vault),
            "hidden_sources": [{"source_id": source_id, "title": titles.get(source_id) or source_id}
                               for source_id in hidden_sources(vault)]}


@method("reader.correspondence_preferences", ParamsModel)
def reader_correspondence_preferences(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    """The line's hide preferences (Settings); reports the switch, like the prompt contract."""

    vault, repository = ctx.require_vault()
    return versioned(_preferences(vault, repository))


class SetCorrespondencePreferencesInput(ParamsModel):
    #: The book the line was hidden (or shown again) for.
    source_id: str | None = None
    hide_source: bool | None = None
    hide_everywhere: bool | None = None


@method("reader.set_correspondence_preferences", SetCorrespondencePreferencesInput)
def reader_set_correspondence_preferences(ctx: SidecarContext,
                                          params: SetCorrespondencePreferencesInput) -> dict[str, Any]:
    """*Hide for this book* / *hide everywhere* (or Settings bringing it back).

    Remembered in the vault's ``[reader.correspondence]`` config, so it holds
    across devices, as the margin marks' per-book switch is. It hides the
    Guide's line only: the data and CA5a's pressed action are unchanged. No
    change, no write."""

    from learnloop.ops.settings_store import SettingsStoreError, apply_config_updates
    from learnloop.vault_lock import VaultLockError, vault_mutation_lock

    vault, repository = ctx.require_vault()
    if not find_section_enabled(vault):
        raise SidecarError("correspondence_disabled",
                           "Also in your books is off (reader.correspondence.enabled = false).")
    source_id = str(params.source_id or "").strip()
    if params.hide_source is not None and not source_id:
        raise SidecarError("validation_error", "Hiding the line for a book names the book.")
    config_path = vault.root / "learnloop.toml"
    try:
        # The change applies to the config as it is on disk now, under the
        # vault's mutation lock (Codex review F2): another sidecar, a CLI or
        # Settings may have hidden or shown a book since this context loaded,
        # and a stale in-memory list must never overwrite it.
        with vault_mutation_lock(vault.root, purpose="reader_correspondence_preferences"):
            current, everywhere = _on_disk_preferences(config_path)
            updates: dict[tuple[str, ...], Any] = {}
            if params.hide_source is not None:
                if params.hide_source and source_id not in current:
                    updates[("reader", "correspondence", "hidden_sources")] = [*current, source_id]
                elif not params.hide_source and source_id in current:
                    updates[("reader", "correspondence", "hidden_sources")] = [
                        entry for entry in current if entry != source_id]
            if params.hide_everywhere is not None and bool(params.hide_everywhere) != everywhere:
                updates[("reader", "correspondence", "hide_everywhere")] = bool(params.hide_everywhere)
            if updates:
                apply_config_updates(config_path, updates)
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except VaultLockError as exc:
        raise SidecarError("vault_busy", f"The vault is busy; try again ({exc}).") from exc
    # Reloaded whenever the file may differ from this context's copy (another
    # writer's change shows here too), not only after this call's own write.
    if updates or current != hidden_sources(vault) or everywhere != hidden_everywhere(vault):
        ctx.reload(maintenance=False)
        vault, repository = ctx.require_vault()
    return versioned(_preferences(vault, repository))


def _on_disk_preferences(config_path: Any) -> tuple[list[str], bool]:
    """``[reader.correspondence]``'s hide keys as the file holds them now (absent: the defaults)."""

    import tomllib

    from learnloop.ops.settings_store import SettingsStoreError

    try:
        document = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SettingsStoreError("config_missing", f"{config_path} does not exist") from exc
    except tomllib.TOMLDecodeError as exc:
        raise SettingsStoreError("config_unreadable", f"{config_path} is not valid TOML: {exc}") from exc
    reader = document.get("reader")
    section = reader.get("correspondence") if isinstance(reader, dict) else None
    section = section if isinstance(section, dict) else {}
    sources = section.get("hidden_sources") or []
    listed = [str(entry) for entry in sources] if isinstance(sources, list) else []
    return list(dict.fromkeys(listed)), bool(section.get("hide_everywhere", False))


__all__ = ["ALSO_IN_BOOKS_RPCS", "CORRESPONDENT_RPCS", "FIND_SECTION_RPCS", "figures_follow_enabled",
           "find_section_enabled", "prompt_contract_fields"]
