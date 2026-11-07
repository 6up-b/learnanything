"""Router speed stage 2, item 1: AD's section → LO map held across calls (no successor: every value is the map's).

AD's reading map (:class:`~learnloop.adaptive_difficulty.reading.VaultReadingMap`) maps a completed section, a viewed
span or a question's anchors to the LOs whose provenance cites them (``section_map.learning_objects_for_section_in_ir``
through ``MaterialView.document_ir``). The map was built afresh at every call of the combiner's join (RO2's opportunity
resolve), of the sweep and of the rollouts' reading action, and each section's mapping re-read the reading's run,
revision and source and walked every LO's references over the section's blocks: the landing's profile measured it at
11 ms a call, 3,794 calls in a week on the owner's linear_algebra copy.

Here a section's LOs, and a reading's span → section map, are held process-wide, keyed by:

* the database (its resolved path) and **the vault object** the map reads (the raw vault an AD operation projects,
  held weakly: a reloaded vault is another object, so a vault edit is a new key);
* the operation's **protection epoch** (``MaterialView.epoch``: a digest of everything the view withholds; equal
  epochs mean equal projections, so an exam reservation, a held-out span or a withheld reading is a new key);
* a **digest of the vault's content the mapping reads** (each LO's id, status and references, its facets' canonical
  ids and references, each note's canonical source), so an in-place change is a new key too;
* a **digest of every stored row the mapping reads** (``MaterialView.reading_structure_digest``: the readings'
  metadata, the structure of the reading and of every visible reading of its source, the aliases recorded onto it),
  read at every map, so a new or edited source, a re-read or a new alias is a new key;
* the reading and the section (or span map).

What is never held: the withheld rule. The map asks it of its own operation's view at every call, before any held
value is read (a withheld reading or span maps to nothing, as before), and a reading the view withholds has no
digest, so nothing of it is held or read. A mapping that failed (no IR, an unreadable extraction, a guard refusal) is
not held: the next map computes it again. Pure in-process memory; nothing is written. Its bound is a keep bound.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Hashable
import hashlib
import json
from pathlib import Path
import threading
from typing import Any
import weakref

#: ``keep`` (resource bound): the mappings held per process; past it the oldest is computed again on its next read,
#: never a different value.
_HELD_LIMIT = 4096
_HELD: OrderedDict[Hashable, tuple[Any, Any]] = OrderedDict()
_LOCK = threading.Lock()


def _extras(value: Any) -> dict[str, Any]:
    extra = getattr(value, "model_extra", None)
    return extra if isinstance(extra, dict) else {}


def _dump(ref: Any) -> Any:
    dump = getattr(ref, "model_dump", None)
    return dump(mode="json") if callable(dump) else repr(ref)


def vault_digest(vault: Any) -> str:
    """A digest of everything ``section_map.learning_objects_for_section_in_ir`` reads of ``vault``: every LO's id,
    status and provenance references, each facet of its blueprints' union with its canonical id and that facet's
    references, and every note's id and canonical source (``canonical_note_ids``). Raises when the vault cannot be
    read so (the caller then holds nothing)."""

    from learnloop.vault.models import learning_object_facet_union

    out = hashlib.blake2b(digest_size=20)

    def put(value: Any) -> None:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), default=repr)
        out.update(f"{len(text)}:".encode())
        out.update(text.encode("utf-8", "surrogatepass"))

    facets = getattr(vault, "evidence_facets", {}) or {}
    for key, lo in (getattr(vault, "learning_objects", {}) or {}).items():
        union = []
        for facet_id in learning_object_facet_union(lo):
            canonical = vault.canonical_facet_id(str(facet_id))
            facet = facets.get(canonical)
            union.append([str(facet_id), canonical,
                          None if facet is None else [_dump(ref) for ref in facet.provenance.source_refs]])
        put(["lo", str(key), lo.id, lo.status, [_dump(ref) for ref in lo.provenance.source_refs], union])
    for key, note in (getattr(vault, "notes", {}) or {}).items():
        put(["note", str(key), note.id, _extras(note).get("canonical_source")])
    return out.hexdigest()


def base_key(view: Any, vault: Any, repository: Any, extraction_id: str, *, vault_key: str | None) -> tuple[Any, ...] | None:
    """The key a reading's held values share in one map (see the module docstring), or None: nothing is held (the
    view is unavailable, the reading is withheld, or its rows or the vault cannot be digested)."""

    if vault_key is None or not getattr(view, "available", False):
        return None
    epoch = view.epoch
    if epoch is None:
        return None
    structure = view.reading_structure_digest(extraction_id)
    if structure is None:
        return None
    raw_repository = getattr(repository, "_ad_raw_repository", repository)
    raw_vault = getattr(vault, "_ad_raw_vault", vault)
    return (str(Path(raw_repository.sqlite_path).resolve()), id(raw_vault), hasattr(vault, "_ad_raw_vault"),
            str(epoch), vault_key, structure, str(extraction_id))


def still_current(view: Any, vault: Any, repository: Any, extraction_id: str, base: tuple[Any, ...] | None, *,
                  full: bool) -> bool:
    """Whether a value just computed under ``base`` may be held: its key read again now is still ``base``. ``full``:
    the whole key (the vault digest and the stored structure too); else the metadata and aliases part alone (the
    map's further mappings from an IR whose structure it verified, each re-reading the metadata)."""

    if base is None:
        return False
    if full:
        return base_key(view, vault, repository, extraction_id, vault_key=vault_digest(vault)) == base
    found = view.reading_structure_digest(extraction_id, structure=False)
    return found is not None and str(base[5]).split("/", 1)[0] == found


def structure_key(repository: Any, digest: str | None, extraction_id: str, kind: str) -> tuple[Any, ...] | None:
    """The key of a value derived from a reading's stored structure alone (``MaterialView.section_spans``: no vault,
    no projection), or None when the reading has no digest (withheld, unavailable or unreadable)."""

    if digest is None:
        return None
    raw_repository = getattr(repository, "_ad_raw_repository", repository)
    return (str(Path(raw_repository.sqlite_path).resolve()), "structure", digest, str(extraction_id), kind)


def _owner(vault: Any) -> Any:
    return None if vault is None else getattr(vault, "_ad_raw_vault", vault)


def held(key: Hashable | None, vault: Any) -> Any:
    """The value held under ``key`` for this vault object (None: a value no vault is read for), or None."""

    if key is None:
        return None
    raw_vault = _owner(vault)
    with _LOCK:
        entry = _HELD.get(key)
        if entry is None:
            return None
        owner, value = entry
        if (owner is None) != (raw_vault is None) or (owner is not None and owner() is not raw_vault):
            # Another vault object at a reused address: never this one's.
            _HELD.pop(key, None)
            return None
        _HELD.move_to_end(key)
        return value


def hold(key: Hashable | None, vault: Any, value: Any) -> None:
    """Hold an immutable ``value`` under ``key`` for this vault object (weakly: a vault no longer loaded drops it;
    None: a value no vault is read for)."""

    if key is None:
        return
    raw_vault = _owner(vault)
    try:
        owner = None if raw_vault is None else weakref.ref(raw_vault)
    except TypeError:  # an object that cannot be referenced weakly is never held
        return
    with _LOCK:
        _HELD[key] = (owner, value)
        _HELD.move_to_end(key)
        while len(_HELD) > _HELD_LIMIT:
            _HELD.popitem(last=False)


def clear() -> None:
    """Drop every held mapping (tests; a held value is never stale, so production never needs it)."""

    with _LOCK:
        _HELD.clear()


__all__ = ["base_key", "clear", "held", "hold", "still_current", "structure_key", "vault_digest"]
