"""The one protected material view AD reads through (spec A8; Codex verify F19-F27, fix round 8).

Every AD operation (a serve, a slot draw, a commission, landing reconciliation,
generation targeting, the replay and its rebuilds, the report, the dose arm, a
forecaster or calibration fit, the reading sweep, the relatedness proposal)
asks the held-out predicate ONCE (:func:`material_view`) and reads items, item
facets and surface families, attempts, Reader questions, reading-opportunity
receipts, plan presentations, reveals and forecast history only through the
readers here. Each reader is already filtered:

* **an item** is withheld when the predicate covers it
  (:meth:`~learnloop.adaptive_difficulty.protection.Protection.covers`: made
  from held-out material, or reserved for a goal's held-out exam now). A
  withheld item's attempts, presentations, reveals, forecasts and receipts are
  withheld with it, and so is any facet only withheld items name;
* **a source span** (a section, a worked example, a Reader question's anchors,
  a tutor exchange's passage) is withheld when held-out material covers it;
* **an AD artefact** (a draw, a receipt, frozen serve inputs, a reading
  receipt, a relatedness run) is read only at the protection epoch it was
  computed under (:attr:`MaterialView.epoch`; ``protected_tables.EPOCH``):
  one of another epoch is ignored, expires, or is computed and recorded
  again (a reading receipt is swept again under the current projection);
  a reading receipt's source is also resolved again.

AD's protection is unconditional: it never reads ``goals.held_out_selection``
or any routine-serving switch, which only govern routine serving.

**Fail closed.** When the predicate cannot be computed the view is
*unavailable*: every item-derived reader is empty and every source is withheld.
The operation then degrades to its incumbent behaviour (the slot serves its
planned item, generation takes the predecessor's target path, the report
discloses zero observations and why), never to unfiltered data and never to an
exception.

**The rules** (the AD23 redesign, Option B). This module is the rules of the AD guard
(:mod:`~learnloop.adaptive_difficulty.operation`): inside an AD operation every SQLite read of a
protected table is refused unless these readers make it, and their SQL carries the rules marker.
Every reader applies the registry's one rule (:meth:`MaterialView.keep` over
``protected_tables.COLUMNS``): a row is withheld when any reference resolves to a withheld entity.
The operation's projected vault and document IR (:meth:`MaterialView.projected_vault`,
:meth:`MaterialView.document_ir`) are built here too.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.logs import warn_failure
import json
import re
import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from learnloop.adaptive_difficulty import protected_tables as _T
from learnloop.adaptive_difficulty import protection as _predicate
from learnloop.adaptive_difficulty.protection import Protection
from learnloop.content.sources.exam_material import reference_keys

LOG = logging.getLogger(__name__)

#: Why a view is empty: the held-out predicate could not be computed.
UNAVAILABLE = "held_out_predicate_unavailable"
_UNSET = object()
_VALUE = _T.VALUE
#: The attempt types that never close a reading window (as the replay reads them, §5.6, D8).
NON_WINDOW_TYPES = ("skip", "self_report")


#: The tutor-question contexts that are reading events (round 8 follow-up): a question asked in
#: the Reader or the library. A practice or feedback question is attempt evidence.
READING_QUESTION_CONTEXTS = frozenset({"reader", "library"})
#: The interaction-event kinds that are reading events (a Reader or library visit, action or answer).
READING_EVENT_PREFIXES = ("reader_", "library_")


def _has_table(connection: Any, table: str) -> bool:
    return connection.execute(
        "/* ad-rules */ SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone() is not None


def _rows(connection: Any, sql: str, args: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(args))
    names = [d[0] for d in cursor.description]
    return [dict(zip(names, raw)) for raw in cursor.fetchall()]


def _json(raw: Any, default: Any) -> Any:
    if not isinstance(raw, str):
        return raw if raw is not None else default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


def _replaced(vault: Any, **fields: Any) -> Any:
    """A copy of ``vault`` with ``fields`` replaced (a ``LoadedVault``, or a test's stand-in)."""

    import copy
    import dataclasses

    if dataclasses.is_dataclass(vault):
        return dataclasses.replace(vault, **fields)
    out = copy.copy(vault)
    for name, value in fields.items():
        if hasattr(vault, name):
            setattr(out, name, value)
    return out


def _select(table: str) -> str:
    """A protected table's columns the rules read and hand out: all but the derived ones
    (``protected_tables.DERIVED``; the guard refuses those outside the derivation scope)."""

    columns = _columns(table)
    if _T.DERIVED not in columns.values():
        return "*"
    return ", ".join(column for column, kind in columns.items() if kind != _T.DERIVED)


def _stamp(row: Mapping[str, Any], rule: str) -> Any:
    """A row's protection epoch, by its table's rule (``column:C`` or ``json:C:K``)."""

    kind, _sep, rest = rule.partition(":")
    if kind == "column":
        return row.get(rest)
    column, _sep, key = rest.partition(":")
    value = _json(_value(row, column), None)
    return value.get(key) if isinstance(value, Mapping) else None


def current_epoch() -> str | None:
    """The epoch of the operation open in this context: what every AD artefact written in it is
    stamped with (an error outside an operation)."""

    return current_view().epoch


def stamped(row: Mapping[str, Any]) -> dict[str, Any]:
    """A row to append to an AD artefact table with a ``protection_epoch`` column, stamped."""

    return {**dict(row), "protection_epoch": current_epoch()}


def _as_rows(found: Any) -> list[dict[str, Any]]:
    if found is None:
        return []
    if isinstance(found, Mapping):
        return [dict(found)]
    return [dict(row) for row in found]


def _columns(table: str) -> Mapping[str, str]:
    """The registry's classification of a protected table's columns (an error for any other)."""

    try:
        return _T.COLUMNS[table]
    except KeyError:
        raise ValueError(f"{table} is not a protected table of the AD registry") from None


def _value(row: Mapping[str, Any], column: str) -> Any:
    """A column's value in a raw row, or in a store's decoded row (``x_json`` decoded as ``x``)."""

    if column in row:
        return row[column]
    if column.endswith("_json"):
        return row.get(column[: -len("_json")])
    return None


#: Reference kinds that name a row of another protected table: ``(table, key column)``.
_ENTITY_TABLES: dict[str, tuple[str, str]] = {
    "attempt": ("practice_attempts", "id"),
    "presentation": ("plan_presentations", "id"),
    "reader_question": ("reader_authored_questions", "id"),
    "question_event": ("question_events", "id"),
    "dose_draw": ("ad_dose_offers", "id"),
    "selection": ("ad_selections", "id"),
    "receipt": ("forecast_receipts", "id"),
    "administration": ("activity_administrations", "id"),
    "surface": ("activity_surfaces", "id"),
}


def _spans(raw: Any) -> list[str]:
    try:
        value = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        return []
    return [str(span) for span in value] if isinstance(value, list) else []


class MaterialView:
    """One operation's view of what AD may read (see the module docstring)."""

    def __init__(self, vault: Any, repository: Any, protected: Protection) -> None:
        self.vault = vault
        self.repository = repository
        self.protection = protected
        self.available = protected.material is not None
        self.reason = None if self.available else UNAVAILABLE
        self._revisions: dict[str, Any] = {}
        self._section_spans: dict[str, dict[str, list[str]]] = {}
        self._touched: frozenset[str] | None = None
        self._universe: set[str] | None = None
        self._answered: dict[str, tuple[str, ...]] | None = None
        self._frozen: dict[str, str] | None = None
        self._protected_only: dict[bool, set[str]] = {}
        self._memo: dict[Any, Any] | None = None
        self._projected: Any = None
        self._epoch: Any = _UNSET


    # -- the protection epoch ----------------------------------------------------------------------

    @property
    def epoch(self) -> str | None:
        """A digest of everything this view's projection withholds (the AD23 redesign, E2; round 2,
        class 3a): the predicate's material (whole extractions and span keys), the exam reservations,
        the protected current items (``Protection.ids``), the withheld revisions (current items' and
        saved snapshots', by content hash), the withheld notes and the facets only withheld material
        names. Equal epochs mean equal projections, so whatever an operation persists or caches is
        stamped or keyed with it. None while the predicate is unavailable (nothing is in force)."""

        if self._epoch is _UNSET:
            self._epoch = self.compute_epoch()
        return self._epoch

    def compute_epoch(self) -> str | None:
        import hashlib
        from contextlib import closing

        from learnloop.adaptive_difficulty.feature_audit import item_revision
        from learnloop.adaptive_difficulty.operation import EPOCH_VERSION
        from learnloop.db.connection import connect

        if not self.available:
            return None
        material = self.protection.material
        with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
            withheld, _visible = self._withheld_and_visible_revisions(connection)
            notes = sorted(str(note_id) for note_id in (getattr(self.vault, "notes", None) or {})
                           if self.note_withheld(connection, note_id))
            facets = sorted(self.protected_only_facets(connection))
        body = {
            "version": EPOCH_VERSION,
            "extractions": sorted(str(value) for value in (getattr(material, "extractions", ()) or ())),
            "spans": sorted([str(key[0]), str(key[1])] for key in (getattr(material, "spans", ()) or ())),
            "reserved": sorted(str(value) for value in (getattr(self.protection, "reserved", ()) or ())),
            "items": sorted(str(value) for value in self.protection.ids),
            "revisions": sorted({item_revision(item)[0] for item in withheld}),
            "notes": notes,
            "facets": facets,
        }
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    # -- the registry's rule (``protected_tables.COLUMNS``) ------------------------------------------

    def rows(self, connection: Any, table: str, where: str = "", args: Iterable[Any] = (), *,
             order: str = "") -> list[dict[str, Any]]:
        """The rows of a protected table AD may read: every column, the rows any of whose references
        resolves to a withheld entity left out (:meth:`keep`), a reading receipt's doses without the
        facets only withheld material names. Empty while unavailable or without the table."""

        if not self.available or not _has_table(connection, table):
            return []
        sql = f"/* ad-rules */ SELECT {_select(table)} FROM {table}" + (f" WHERE {where}" if where else "") + (
            f" ORDER BY {order}" if order else "")
        return self.filter(connection, table, _rows(connection, sql, args))

    def filter(self, connection: Any, table: str, rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """:meth:`rows`' rule over rows a store already read (decoded JSON columns included)."""

        if not self.available:
            return []
        outer = self._memo
        if outer is None:
            # One filter call reads one state of the database: what it resolves is reused within it.
            self._memo = {}
        try:
            return [dict(row) for row in rows if self.keep(connection, table, row)]
        finally:
            if outer is None:
                self._memo = None

    def lookup(self, connection: Any, table: str, where: str, args: Iterable[Any] = (), *,
               stale_as_missing: bool = False) -> tuple[str, dict[str, Any] | None]:
        """An idempotency read of AD's own ledgers: ``("missing", None)``, ``("withheld", None)`` (a
        row exists that AD may not read: its caller writes nothing and reads nothing of it) or
        ``("ok", row)``. Everything is ``withheld`` while unavailable. ``stale_as_missing``: a row of
        another protection epoch counts as missing (its caller records it again under the current
        projection: a reading receipt)."""

        if not _has_table(connection, table):
            return "missing", None
        return self._status(connection, table, _rows(
            connection, f"/* ad-rules */ SELECT {_select(table)} FROM {table} WHERE {where}", args),
            stale_as_missing=stale_as_missing)

    def _status(self, connection: Any, table: str, found: list[dict[str, Any]], *,
                stale_as_missing: bool = False) -> tuple[str, dict[str, Any] | None]:
        if stale_as_missing and self.available:
            found = [row for row in found if self.epoch_current(table, row)]
        if not found:
            return "missing", None
        kept = self.filter(connection, table, found)
        if len(kept) == len(found):
            return "ok", kept[0]
        # Withheld: its caller writes nothing over it and reads nothing of it but its id.
        return "withheld", ({"id": found[0]["id"]} if "id" in found[0] else None)

    def stored(self, connection: Any, table: str, reader: Any, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """A store's (decoded) rows of a protected table, read by the rules and filtered by the rule:
        ``reader(connection, *args, **kwargs)`` returns a row, a list of rows or None."""

        return self.filter(connection, table, _as_rows(reader(connection, *args, **kwargs)))

    def stored_status(self, connection: Any, table: str, reader: Any, *args: Any, **kwargs: Any
                      ) -> tuple[str, dict[str, Any] | None]:
        """:meth:`lookup` over a store's reader: ``missing``, ``withheld`` (with the row's id only) or
        ``ok`` and the (first) row."""

        found = _as_rows(reader(connection, *args, **kwargs))
        return self._status(connection, table, found)

    def keep(self, connection: Any, table: str, row: Mapping[str, Any]) -> bool:
        """The registry's one rule: a row is withheld when any reference column resolves to a withheld
        entity (the kinds: ``protected_tables.COLUMNS``)."""

        if not self.available:
            return False
        if not self.epoch_current(table, row):
            return False
        selfs = False
        for column, kind in _columns(table).items():
            if kind in (_VALUE, "epoch", _T.DERIVED):
                continue
            if kind == "self":
                selfs = True
                continue
            value = _value(row, column)
            if value in (None, "") and not kind.startswith(("source@", "plan_detail@")):
                continue
            if self._ref_withheld(connection, table, row, kind, value):
                return False
        return not (selfs and self._self_withheld(connection, table, row))

    def epoch_current(self, table: str, row: Mapping[str, Any]) -> bool:
        """Whether a row of an AD-owned artefact table was computed at the current protection epoch
        (``protected_tables.EPOCH``; round 2, class 3b). A table with no epoch rule (not an AD
        artefact) or a ``free`` one is always current; a row with no stamp never is."""

        rule = _T.EPOCH.get(table)
        if rule is None or rule.startswith("free:"):
            return True
        epoch = self.epoch
        return epoch is not None and _stamp(row, rule) == epoch

    def _ref_withheld(self, connection: Any, table: str, row: Mapping[str, Any], kind: str, value: Any) -> bool:
        base, _sep, arg = kind.partition("@")
        if base == "entity":
            entity = _T.ENTITY_KINDS.get(str(row.get(arg) or ""))
            return entity is not None and self._ref_withheld(connection, table, row, entity, value)
        if base == "item":
            return self.withheld(value)
        if base == "served_item":
            if self.withheld(value):
                return True
            memo = self._memo if self._memo is not None else {}
            if "serves" not in memo:
                memo["serves"] = self._withheld_serves(connection)
            return (str(row.get(arg)), str(value)) in memo["serves"]
        if base == "revision":
            return self.revision_hash_withheld(connection, value)
        if base == "facet":
            canonical = getattr(self.vault, "canonical_facet_id", lambda v: v)
            return canonical(str(value)) in self.protected_only_facets(connection)
        reading = table in _T.READING
        if base == "extraction":
            # A reading table's row is withheld with its reading (round 8); an item's provenance link
            # by the withheld material itself.
            return self.reading_withheld(value) if reading else self.material_withheld(value)
        if base == "span":
            if reading:
                return self.reading_withheld(row.get(arg))
            return self.keys_withheld(*reference_keys({"extraction_id": row.get(arg), "span_id": value})) \
                or self.material_withheld(row.get(arg), value)
        if base == "section":
            return self.reading_withheld(row.get(arg))
        if base == "spans":
            if reading:
                return self.reading_withheld(row.get(arg))
            spans = value if isinstance(value, list) else _spans(value)
            return any(self.material_withheld(row.get(arg), span) for span in spans) or self.keys_withheld(
                *reference_keys({"extraction_id": row.get(arg), "span_ids": [str(span) for span in spans]}))
        if base == "reading_payload":
            # A Reader event names its reading in its payload (or its locator): it is a reading
            # event of every reading it names (round 8, Option B). Any other event (a practice-time
            # one) is not a reading event, and its payload a value, as before (round 8 follow-up).
            if not str(row.get("kind") or "").startswith(READING_EVENT_PREFIXES):
                return False
            payload = value if isinstance(value, (Mapping, list)) else _json(value, {})
            keys, whole = reference_keys(payload)
            return any(self.reading_withheld(extraction) for extraction, _span in keys) or any(
                self.reading_withheld(extraction) for extraction in whole)
        if base == "note":
            return self._note_ref_withheld(connection, value)
        if base == "source":
            return self._opportunity_withheld(connection, row)
        if base == "plan_detail":
            detail = value if isinstance(value, Mapping) else _json(value, {})
            memo = self._memo if self._memo is not None else {}
            if "plan_events" not in memo:
                memo["plan_events"] = self.plan_event_visible(connection)
            return not memo["plan_events"](str(row.get("kind")), detail, row.get(arg))
        if base in _ENTITY_TABLES:
            return self._entity_withheld(connection, base, value)
        raise ValueError(f"unknown reference kind {kind!r} in {table}")

    def _entity_withheld(self, connection: Any, kind: str, value: Any) -> bool:
        """A reference to a row of another protected table: withheld when that row is (by its own
        table's rule, in dependency order); a row since deleted is merely absent (not withheld)."""

        memo = self._memo if self._memo is not None else {}
        if (kind, str(value)) not in memo:
            table, key = _ENTITY_TABLES[kind]
            found = _rows(connection, f"/* ad-rules */ SELECT {_select(table)} FROM {table} WHERE {key} = ?",
                          (str(value),)) \
                if _has_table(connection, table) else []
            memo[(kind, str(value))] = any(not self.keep(connection, table, row) for row in found)
        return memo[(kind, str(value))]

    def _self_withheld(self, connection: Any, table: str, row: Mapping[str, Any]) -> bool:
        """A row's own identity, by its table's rule."""

        if table == "practice_attempts":
            return self.attempt_withheld(connection, row)
        if table == "plan_presentations":
            return self._presentation_withheld(connection, row)
        if table == "reader_authored_questions":
            return self.question_withheld(row)
        if table == "question_events":
            return self.question_event_withheld(connection, row.get("id"))
        if table == "practice_item_snapshots":
            return self.revision(connection, str(row.get("content_hash"))) is None
        if table == "ad_dose_offers":
            return str(row.get("row_kind")) == "draw" and self.dose_draw_withheld(connection, {
                **dict(row), "content": row.get("content", _json(row.get("content_json"), {}))})
        if table == "activity_administrations":
            # Withheld when it administered only withheld answers (its observations' attempts): with
            # that material absent it would never have been administered.
            if not _has_table(connection, "activity_observations"):
                return False
            attempts = [attempt for (attempt,) in connection.execute(
                "/* ad-rules */ SELECT attempt_id FROM activity_observations WHERE administration_id = ? "
                "AND attempt_id IS NOT NULL", (str(row.get("id")),))]
            return bool(attempts) and all(self._entity_withheld(connection, "attempt", attempt) for attempt in attempts)
        if table == "activity_surfaces":
            # Withheld when every administration of it is (a surface only withheld answers used).
            administrations = _rows(connection, "/* ad-rules */ SELECT * FROM activity_administrations "
                                    "WHERE surface_id = ?", (str(row.get("id")),))
            return bool(administrations) and all(self._self_withheld(connection, "activity_administrations", found)
                                                 for found in administrations)
        if table == "proposed_patch_items":
            return self._proposal_withheld(row)
        raise ValueError(f"no self rule for {table}")

    def _proposal_withheld(self, row: Mapping[str, Any]) -> bool:
        """A proposal is withheld when the item its effective payload (the edit, else the payload)
        creates or changes is: its id withheld, or its own sources (canonical exercise, provenance
        refs) in held-out material, or a withheld item among its source refs (round 2, class 2). An
        unreadable item payload is withheld (fail closed)."""

        from types import SimpleNamespace

        from learnloop.vault.models import CanonicalExercise, SourceRef

        payload = _json(row.get("edited_payload_json"), None) or _json(row.get("payload_json"), None)
        refs = _json(row.get("source_ref_ids_json"), [])
        if str(row.get("item_type") or "") != "practice_item":
            return False
        if not isinstance(payload, Mapping):
            return True
        if payload.get("id") and self.withheld(payload["id"]):
            return True
        try:
            exercise = payload.get("canonical_exercise")
            provenance = payload.get("provenance") or {}
            item = SimpleNamespace(
                id=str(payload.get("id") or ""),
                canonical_exercise=CanonicalExercise.model_validate(exercise) if isinstance(exercise, Mapping) else None,
                provenance=SimpleNamespace(source_refs=[SourceRef.model_validate(ref) for ref in
                                                        (provenance.get("source_refs") or [])]))
        except Exception:  # noqa: BLE001 - an unreadable proposed item is withheld
            return True
        if self.protection.covers(item):
            return True
        # Its source refs name the needs, LOs and source items it was made for: a withheld one withholds it.
        return any(self.withheld(ref) for ref in (refs if isinstance(refs, list) else []) if isinstance(ref, str))

    def _note_ref_withheld(self, connection: Any, note_id: Any) -> bool:
        keys, _whole = reference_keys(str(note_id))
        if keys:
            return self.keys_withheld(keys)
        return self.note_withheld(connection, note_id)

    def administration_item(self, connection: Any, administration_id: Any) -> str | None:
        """The legacy practice item an activity administration served (its surface's), or None."""

        if not administration_id or not _has_table(connection, "activity_administrations"):
            return None
        found = self.rows(connection, "activity_administrations", "id = ?", (str(administration_id),))
        if not found or not found[0].get("surface_id"):
            return None
        surface = self.rows(connection, "activity_surfaces", "id = ?", (str(found[0]["surface_id"]),))
        return str(surface[0]["legacy_practice_item_id"]) if surface and surface[0].get("legacy_practice_item_id") \
            else None

    # -- items -----------------------------------------------------------------------------------

    def withheld(self, practice_item_id: Any) -> bool:
        """Whether an item (by id) is withheld: protected now, or the predicate unavailable."""

        return not self.available or str(practice_item_id) in self.protection.ids

    def covers(self, item: Any) -> bool:
        """Whether a revision (a current item or a snapshot) is withheld, judged by its own sources."""

        return not self.available or self.protection.covers(item)

    @property
    def withheld_item_ids(self) -> frozenset[str]:
        """The current items withheld (ids only: a count for a report, never content)."""

        if not self.available:
            return frozenset(str(item_id) for item_id in (getattr(self.vault, "practice_items", {}) or {}))
        return frozenset(self.protection.ids)

    def item(self, practice_item_id: Any) -> Any:
        """The current item, or None when it is withheld or not in the vault."""

        if practice_item_id is None or self.withheld(practice_item_id):
            return None
        return (getattr(self.vault, "practice_items", {}) or {}).get(str(practice_item_id))

    def items(self, *, learning_object_id: str | None = None, active: bool = False) -> list[Any]:
        """The current items AD may read, sorted by id (all of them empty when unavailable)."""

        if not self.available:
            return []
        out = []
        for item_id, item in sorted((getattr(self.vault, "practice_items", {}) or {}).items()):
            if str(item_id) in self.protection.ids:
                continue
            if learning_object_id is not None and item.learning_object_id != learning_object_id:
                continue
            if active and getattr(item, "status", "active") != "active":
                continue
            out.append(item)
        return out

    def lo_for_item(self, practice_item_id: Any) -> str | None:
        item = self.item(practice_item_id)
        return str(item.learning_object_id) if item is not None else None

    def lo_facets(self, lo: Any) -> list[str]:
        """The LO's authored facets, else the facets its visible active items measure (a facet only
        withheld items name is never AD's: Codex verify F19)."""

        from learnloop.vault.models import learning_object_facet_union

        vault = self.vault
        facets = [vault.canonical_facet_id(str(f)) for f in learning_object_facet_union(lo)]
        if not facets:
            facets = [vault.canonical_facet_id(str(f)) for item in self.items(learning_object_id=lo.id, active=True)
                      for f in item.evidence_facets]
        return sorted(dict.fromkeys(facets))

    def facet_maps(self) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """``(facet -> LOs, LO -> facets)`` for the replay's structure and the reading map."""

        lo_to_facets: dict[str, list[str]] = {}
        facet_to_los: dict[str, list[str]] = {}
        for lo in getattr(self.vault, "learning_objects", {}).values():
            facets = self.lo_facets(lo)
            lo_to_facets[lo.id] = facets
            for facet in facets:
                facet_to_los.setdefault(facet, []).append(lo.id)
        return facet_to_los, lo_to_facets

    def facet_universe(self) -> set[str]:
        """Every facet the view names: the LOs' facets and the visible items' own facets."""

        if self._universe is None:
            universe: set[str] = set()
            for facets in self.facet_maps()[1].values():
                universe.update(facets)
            for item in self.items():
                universe.update(getattr(self.vault, "canonical_facet_id", lambda value: value)(str(f)) for f in item.evidence_facets)
            self._universe = universe
        return self._universe

    def _withheld_and_visible_revisions(self, connection: Any = None) -> tuple[list[Any], list[Any]]:
        """``(withheld items and revisions, visible items and revisions)``: the current items, and
        the saved snapshots when a connection is given (their content judged, never returned)."""

        from learnloop.vault.models import PracticeItem

        current = getattr(self.vault, "practice_items", {}) or {}
        withheld = [item for item_id, item in current.items() if self.withheld(item_id)]
        visible = [item for item_id, item in current.items() if not self.withheld(item_id)]
        if connection is not None and _has_table(connection, "practice_item_snapshots"):
            for content_hash, item_json in connection.execute(
                    "/* ad-rules */ SELECT content_hash, item_json FROM practice_item_snapshots"):
                try:
                    item = PracticeItem.model_validate_json(item_json)
                except ValueError:
                    continue
                (visible if self.revision(connection, str(content_hash)) is not None else withheld).append(item)
        return withheld, visible

    def protected_only_facets(self, connection: Any = None) -> set[str]:
        """Facets that only withheld items or revisions name: named by none of the LOs' authored
        facets, the visible current items or the visible saved revisions (Codex verify F30: a facet
        merely absent from current content is not withheld)."""

        if not self.available:
            return set()
        key = connection is not None  # with a connection the saved revisions are judged too
        if key not in self._protected_only:
            withheld, visible = self._withheld_and_visible_revisions(connection)
            canonical = getattr(self.vault, "canonical_facet_id", lambda value: value)
            named = {canonical(str(f)) for item in withheld for f in (item.evidence_facets or ())}
            kept = set(self.facet_universe()) | {canonical(str(f)) for item in visible
                                                 for f in (item.evidence_facets or ())}
            self._protected_only[key] = named - kept
        return set(self._protected_only[key])

    def request_leaks(self, text: str, connection: Any = None) -> list[str]:
        """What a serialized model request quotes of withheld material (fix round 9, R2): a withheld
        item's id or stem, or a facet or surface family only withheld material names. Empty when
        nothing leaks; everything is a leak while the predicate is unavailable."""

        import re

        if not self.available:
            return ["the held-out predicate is unavailable"]
        withheld, visible = self._withheld_and_visible_revisions(connection)
        visible_ids = {str(getattr(item, "id", "")) for item in visible}
        visible_families = {str(item.surface_family) for item in visible if getattr(item, "surface_family", None)}
        hits: list[str] = []

        def present(token: str) -> bool:
            return bool(token) and re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", text) is not None

        for item in withheld:
            item_id = str(getattr(item, "id", ""))
            if item_id not in visible_ids and present(item_id):
                hits.append(f"item id {item_id}")
            stem = " ".join(str(getattr(item, "prompt", "") or "").split())[:60]
            if len(stem) >= 16 and stem in " ".join(text.split()):
                hits.append(f"the stem of {item_id}")
            family = getattr(item, "surface_family", None)
            if family and str(family) not in visible_families and present(str(family)):
                hits.append(f"surface family {family}")
        for facet in sorted(self.protected_only_facets(connection)):
            if present(facet):
                hits.append(f"facet {facet}")
        return sorted(set(hits))

    def vault_view(self) -> Any:
        """The vault as AD's material view sees it: the same object with only the visible current
        items, for helpers outside AD that read a whole vault (generation's authoring context, its
        contract and contrast reachability; fix round 9, R2), and only the visible notes (a source's
        canonical note is withheld with its source's held-out material; Codex verify F40, fix round
        12). No items and no notes when unavailable."""

        import dataclasses

        visible = {str(item.id): item for item in self.items()}
        notes = getattr(self.vault, "notes", None)
        if notes is None:
            return _replaced(self.vault, practice_items=visible)
        from contextlib import closing

        from learnloop.db.connection import connect

        kept: dict[str, Any] = {}
        if self.available:
            with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
                kept = {note_id: note for note_id, note in notes.items()
                        if not self.note_withheld(connection, note_id)}
        return _replaced(self.vault, practice_items=visible, notes=kept)

    def note_extractions(self, connection: Any, note_id: Any) -> list[str]:
        """The extraction runs of the source revisions a note is the canonical note of."""

        if not (_has_table(connection, "source_revisions") and _has_table(connection, "source_extraction_runs")):
            return []
        return [str(row[0]) for row in connection.execute(
            "/* ad-rules */ SELECT run.id FROM source_extraction_runs AS run JOIN source_revisions AS revision "
            "ON revision.id = run.revision_id WHERE revision.note_id = ? ORDER BY run.id", (str(note_id),))]

    def note_withheld(self, connection: Any, note_id: Any) -> bool:
        """Whether a note may not reach AD (fix round 12, F40): every note while unavailable; a
        source's canonical note when any of its extractions holds held-out material (the note's
        body is the source's text, so a held-out span anywhere in it is in the note). A note no
        source names (a learner's own note) is visible."""

        if not self.available:
            return True
        material = self.protection.material
        if getattr(material, "empty", False):
            return False
        extractions = set(self.note_extractions(connection, note_id))
        if not extractions:
            return False
        held = set(getattr(material, "extractions", ()) or ()) | {
            str(key[0]) for key in (getattr(material, "spans", ()) or ())}
        return bool(extractions & held)

    def visible_commission_results(self, connection: Any) -> list[dict[str, Any]]:
        """``ad_commission_results`` of visible items, revisions and selections (Codex verify F29)."""

        from learnloop.db.stores import ad_serving

        return self.filter(connection, "ad_commission_results", ad_serving.commission_results(connection))

    def dose_extra_withheld(self, connection: Any, variant: Any, content: Any) -> bool:
        """Whether a drawn dose extra's content is withheld now (its question, or its example span)."""

        content = content or {}
        if not self.available:
            return True
        if variant == "extra_question":
            # Withheld when the question is protected now; a question since deleted is merely absent
            # from current content, and the offer record stands (as a frozen dose does, F30).
            return self._entity_withheld(connection, "reader_question", content.get("question_id"))
        if variant == "extra_worked_example":
            return self.reading_withheld(content.get("extraction_id"))
        return False

    def dose_draw_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool:
        """Whether a dose draw is withheld now (Codex verify F47, fix round 14): its ORIGINATING
        section (the boundary it was drawn at) is withheld, or its chosen extra is. Either way it is,
        for AD, a draw never made: out of the budget, the cohort, retrieval and uptake."""

        if not self.available:
            return True
        extraction, section = row.get("extraction_id"), row.get("section_id")
        if extraction and section and self.section_withheld(str(extraction), str(section)):
            return True
        return self.dose_extra_withheld(connection, row.get("chosen_variant"), row.get("content"))

    def dose_rows(self, connection: Any) -> list[dict[str, Any]]:
        """``ad_dose_offers`` rows revalidated now (Codex verify F29, F47): a draw withheld by its
        originating section or its chosen extra, and that draw's uptake rows, are left out."""

        from learnloop.db.stores import ad_serving

        return self.filter(connection, "ad_dose_offers", ad_serving.dose_rows(connection))

    def _proposal_rule(self, connection: Any) -> Any:
        return lambda row: self.keep(connection, "proposed_patch_items", row)

    def open_commissions(self, connection: Any, *, now: str | None = None) -> list[dict[str, Any]]:
        """Open commissions as the view sees them: a result on a withheld item does not land, and a
        commission of a cell whose facet only withheld material names is not open (the same cohort
        as :meth:`selections`, fix round 11)."""

        from learnloop.db.stores import ad_serving

        # Every count, any(), max() and expiry decision runs over what the view reads (round 2,
        # classes 2 and 4): the visible commissions of this epoch, their visible landings, and the
        # visible proposals behind the expiry clock.
        landed = {str(row["selection_id"]) for row in self.visible_commission_results(connection)}
        rows = [row for row in self.stored(connection, ad_serving.SELECTIONS, ad_serving.commissions_in_draw_order)
                if row.get("chosen_point")]
        return ad_serving.open_commissions(connection, now=now, landed=landed, rows=rows,
                                           proposal_visible=self._proposal_rule(connection))

    def landed_after_expiry(self, connection: Any, commission: Mapping[str, Any], landed_at: Any) -> bool:
        """Whether a landing came after its commission expired (the store's expiry clock: the job's
        finish and the review decisions on items proposed for the LO; owner decision 2026-10-19)."""

        from learnloop.db.stores import ad_serving

        return ad_serving.landed_after_expiry(connection, commission, landed_at,
                                              proposal_visible=self._proposal_rule(connection))

    def revision(self, connection: Any, content_hash: str | None) -> Any:
        """A saved revision (``practice_item_snapshots``) as an item, or None when it is missing or
        withheld (its item withheld now, or its own sources held out)."""

        from learnloop.vault.models import PracticeItem

        if not content_hash or not self.available:
            return None
        if content_hash not in self._revisions:
            found = connection.execute(
                "/* ad-rules */ SELECT practice_item_id, item_json FROM practice_item_snapshots WHERE content_hash = ?",
                (content_hash,)).fetchone()
            item = None
            if found is not None and not self.withheld(found[0]):
                try:
                    item = PracticeItem.model_validate_json(found[1])
                except ValueError:
                    item = None
                if item is not None and self.covers(item):
                    item = None
            self._revisions[content_hash] = item
        return self._revisions[content_hash]

    def revisions(self, connection: Any) -> list[tuple[str, Any]]:
        """Every visible saved revision, ``(content_hash, item)``, oldest first."""

        if not self.available or not _has_table(connection, "practice_item_snapshots"):
            return []
        out = []
        for (content_hash,) in connection.execute(
                "/* ad-rules */ SELECT content_hash FROM practice_item_snapshots ORDER BY created_at, content_hash"):
            item = self.revision(connection, str(content_hash))
            if item is not None:
                out.append((str(content_hash), item))
        return out

    def audit_revisions(self, connection: Any) -> tuple[list[tuple[Any, str]], int]:
        """``(item, content_hash)`` for every visible active item's current revision and every visible
        saved revision, and how many revisions were withheld (a count for the backfill's plan)."""

        from learnloop.adaptive_difficulty.feature_audit import item_revision
        from learnloop.vault.models import PracticeItem

        current = getattr(self.vault, "practice_items", {}) or {}
        skipped: set[str] = {f"item:{item_id}" for item_id, item in current.items()
                             if self.withheld(item_id) and getattr(item, "status", "active") == "active"}
        seen: set[str] = set()
        out: list[tuple[Any, str]] = []
        for item in self.items(active=True):
            content_hash = item_revision(item)[0]
            if self.covers(item):
                skipped.add(content_hash)
                continue
            if content_hash not in seen:
                seen.add(content_hash)
                out.append((item, content_hash))
        if not _has_table(connection, "practice_item_snapshots"):
            return out, len(skipped)
        for content_hash, item_id, item_json in connection.execute(
                "/* ad-rules */ SELECT content_hash, practice_item_id, item_json FROM practice_item_snapshots "
                "ORDER BY created_at, content_hash"):
            if content_hash in seen or content_hash in skipped:
                continue
            if self.withheld(item_id):
                skipped.add(str(content_hash))
                continue
            try:
                item = PracticeItem.model_validate_json(item_json)
            except ValueError:
                continue
            # A snapshot audits as the revision it holds, under its stored hash.
            if item_revision(item)[0] != content_hash:
                continue
            if self.covers(item):
                skipped.add(str(content_hash))
                continue
            seen.add(str(content_hash))
            out.append((item, str(content_hash)))
        return out, len(skipped)

    def revision_withheld(self, connection: Any, content_hash: str | None, practice_item_id: Any = None) -> bool:
        """Whether a revision named by hash (and its item id, when known) is withheld now."""

        if not self.available or (practice_item_id is not None and self.withheld(practice_item_id)):
            return True
        if not content_hash:
            return False
        found = connection.execute("/* ad-rules */ SELECT 1 FROM practice_item_snapshots WHERE content_hash = ?",
                                   (content_hash,)).fetchone()
        return found is not None and self.revision(connection, content_hash) is None

    # -- attempts --------------------------------------------------------------------------------

    def _frozen_revisions(self, connection: Any) -> dict[str, str]:
        """Each plan presentation's frozen served revision (``item_serve_inputs``)."""

        if self._frozen is None:
            frozen: dict[str, str] = {}
            if _has_table(connection, "item_serve_inputs"):
                for presentation_id, content_hash in connection.execute(
                        "/* ad-rules */ SELECT plan_presentation_id, content_hash FROM item_serve_inputs "
                        "WHERE plan_presentation_id IS NOT NULL"):
                    frozen.setdefault(str(presentation_id), str(content_hash))
            self._frozen = frozen
        return self._frozen

    def _answered_revisions(self, connection: Any) -> dict[str, tuple[str, ...]]:
        """Each attempt's answered revision(s): the presentation's frozen revision and the revision
        field's own resolution reads (``load_attempt_rows``' ``item_snapshot_hash``). Resolved on the
        raw table once per view, only to decide what is withheld; nothing derived here is used."""

        if self._answered is None:
            from learnloop.field.outcomes import load_attempt_rows

            answered: dict[str, set[str]] = {}
            frozen = self._frozen_revisions(connection)
            for attempt_id, presentation_id in connection.execute(
                    "/* ad-rules */ SELECT id, plan_presentation_id FROM practice_attempts"):
                if presentation_id and str(presentation_id) in frozen:
                    answered.setdefault(str(attempt_id), set()).add(frozen[str(presentation_id)])
            try:
                for row in load_attempt_rows(connection, self.vault):
                    if row.item_snapshot_hash:
                        answered.setdefault(str(row.attempt_id), set()).add(str(row.item_snapshot_hash))
            except Exception:  # noqa: BLE001 - an unresolvable history keeps its frozen revisions only
                warn_failure(LOG, "field revision resolution failed: attempts judged by frozen revisions")
            self._answered = {key: tuple(sorted(values)) for key, values in answered.items()}
        return self._answered

    def item_states(self, connection: Any) -> dict[str, Any]:
        """``practice_item_state`` as AD may read it (fix round 12, F42's audit): visible items only,
        and only their lifecycle (``active``). The fields the incumbent's scheduler derives from
        answers (difficulty, stability, retrievability, due date, last attempt) read as a fresh
        item's, so no answer, a withheld one included, reaches AD through them. Empty while
        unavailable. The incumbent's own reader is unchanged."""

        from dataclasses import replace

        if not self.available or not _has_table(connection, "practice_item_state"):
            return {}
        out: dict[str, Any] = {}
        for state in self.repository.practice_item_states().values():
            if self.withheld(state.practice_item_id):
                continue
            # AD reads an item's lifecycle (``active``) and nothing the incumbent's scheduler derived
            # from answers: its candidates are never-attempted items, so a public one reads exactly
            # this, and an item answered only on withheld material can read nothing else.
            out[state.practice_item_id] = replace(state, difficulty=None, stability=None, retrievability=None,
                                                  due_at=None, last_attempt_at=None)
        return out

    def attempt_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool:
        """Whether an attempt is withheld: its item is withheld now, or a revision it answered is
        (Codex verify F20: a public item's historical revision cut from held-out material)."""

        if self.withheld(row.get("practice_item_id")):
            return True
        return any(self.revision_withheld(connection, content_hash)
                   for content_hash in self._answered_revisions(connection).get(str(row["id"]), ()))

    def attempts(self, connection: Any) -> list[dict[str, Any]]:
        """Every visible ``practice_attempts`` row (all columns, latency included), oldest first.

        Filtered at the source (fix round 9, R1): an attempt on a withheld item, or one whose
        answered revision is withheld, is invisible to everything AD derives (warmth, the
        replay's windows and first surfaces, field rows and their familiarity history, duration
        estimates, the dose moderator, practice minutes, history cards)."""

        return self.rows(connection, "practice_attempts", order="created_at, id")

    def attempted_item_ids(self, connection: Any) -> set[str]:
        return {str(row["practice_item_id"]) for row in self.attempts(connection)}

    def field_rows(self, connection: Any, **kwargs: Any) -> list[Any]:
        """Field's attempt rows derived FROM the view's attempts (``load_attempt_rows`` with
        ``attempt_rows``; Codex verify F24): a withheld answer never enters the familiarity history
        or any other cross-attempt derivation of a row kept."""

        from learnloop.field.outcomes import load_attempt_rows

        if not self.available:
            return []
        return list(load_attempt_rows(connection, self.vault, attempt_rows=self.attempts(connection), **kwargs))

    def held_for_review(self, connection: Any) -> frozenset[str]:
        """The visible attempts whose grade is held for review now (the incumbent's rule,
        ``held_grades.held_for_review_attempts``, asked of the visible attempts only)."""

        from learnloop.held_grades import held_for_review_attempts

        ids = [str(row["id"]) for row in self.attempts(connection)]
        return held_for_review_attempts(connection, ids) if ids else frozenset()

    def assessment_contract(self, connection: Any, contract_version_id: Any) -> dict[str, Any] | None:
        """One assessment contract (``assessment_contract_versions``, whose ``contract_json`` holds
        the item's question, answer and rubric: a content column, ``column_classes``), or None when
        it is missing or withheld (the AD23 redesign round 5). It is withheld when its item is, or
        when an answer graded against it is (an attempt resolves the historical revision it
        answered: ``attempt_withheld``), or a tutor question citing it is. No AD reader needs it
        today; this is the one way one may."""

        if not self.available or not _has_table(connection, "assessment_contract_versions"):
            return None
        found = _rows(connection, "/* ad-rules */ SELECT * FROM assessment_contract_versions WHERE id = ?",
                      (str(contract_version_id),))
        if not found:
            return None
        row = found[0]
        if self.withheld(row.get("practice_item_id")):
            return None
        for table in ("grading_evidence", "question_events"):
            if not _has_table(connection, table):
                continue
            for (attempt,) in connection.execute(
                    f"/* ad-rules */ SELECT DISTINCT attempt_id FROM {table} WHERE assessment_contract_version_id = ? "
                    "AND attempt_id IS NOT NULL", (str(contract_version_id),)).fetchall():
                if self._entity_withheld(connection, "attempt", attempt):
                    return None
        if _has_table(connection, "question_events"):
            for (event,) in connection.execute(
                    "/* ad-rules */ SELECT id FROM question_events WHERE assessment_contract_version_id = ?",
                    (str(contract_version_id),)).fetchall():
                if self.question_event_withheld(connection, event):
                    return None
        return {**row, "contract": _json(row.get("contract_json"), {})}

    def worked_example_spans(self, connection: Any, extraction_id: str) -> set[str]:
        """The extraction's worked-example spans, exactly as the incumbent finds them
        (``source_retrieval.corpus.role_keys``: the stored role through ``effective_hint``), for a
        reading no withheld block touches; none for any other (round 8). The stored role is read
        inside the derivation scope, the one place a derived column is read."""

        from learnloop.adaptive_difficulty.operation import Scope, scoped
        from learnloop.source_retrieval.corpus import role_keys

        if not self.available or self.reading_withheld(extraction_id):
            return set()
        keys = scoped(Scope.DERIVE, lambda: role_keys(connection, [extraction_id], ("worked_example",)))
        return {str(span) for extraction, span in keys if extraction == extraction_id}

    def reading_order(self, extraction_id: str) -> dict[str, int]:
        """The visible reading's spans by their stored ordinal (round 8, F2: candidates are taken in
        reading order, never by span id); empty for a withheld reading."""

        ir = self.document_ir(self.repository, extraction_id)
        return {} if ir is None else {str(block.span_id): int(block.ordinal) for block in ir.blocks}

    def protected_reading_counts(self, connection: Any) -> dict[str, int]:
        """What ``ad report`` says Option B leaves out (round 8): the readings the withheld material
        touches, and the reading events recorded on them that AD does not use."""

        if not self.available:
            return {"readings": 0, "events": 0}
        material = self.protection.material
        touched = sorted(str(extraction) for extraction in getattr(material, "touched", ()) or ())
        if not touched:
            return {"readings": 0, "events": 0}
        marks = ",".join("?" for _ in touched)
        readings = connection.execute(
            f"/* ad-rules */ SELECT COUNT(*) FROM source_extraction_runs WHERE id IN ({marks})", touched).fetchone()[0]
        events = 0
        for table in ("source_exposure_events", "reader_section_progress", "reader_authored_questions"):
            if _has_table(connection, table):
                events += int(connection.execute(
                    f"/* ad-rules */ SELECT COUNT(*) FROM {table} WHERE extraction_id IN ({marks})", touched).fetchone()[0])
        if _has_table(connection, "ad_dose_offers"):
            events += int(connection.execute(
                f"/* ad-rules */ SELECT COUNT(*) FROM ad_dose_offers WHERE row_kind = 'draw' AND extraction_id IN ({marks})",
                touched).fetchone()[0])
        # Reading questions and Reader events name their reading in their recorded context or
        # payload (round 8 follow-up, L2): each one that names a withheld reading is counted once.
        if _has_table(connection, "question_events"):
            contexts = ",".join("?" for _ in READING_QUESTION_CONTEXTS)
            events += sum(1 for (question_id,) in connection.execute(
                f"/* ad-rules */ SELECT id FROM question_events WHERE context IN ({contexts})",
                tuple(READING_QUESTION_CONTEXTS)).fetchall()
                if self._names_withheld_reading(connection, "question_events", question_id))
        if _has_table(connection, "interaction_events"):
            events += sum(1 for row in _rows(
                connection, "/* ad-rules */ SELECT id, kind, payload_json, locator_json FROM interaction_events")
                if str(row.get("kind") or "").startswith(READING_EVENT_PREFIXES)
                and any(self._ref_withheld(connection, "interaction_events", row, "reading_payload", row.get(column))
                        for column in ("payload_json", "locator_json")))
        return {"readings": int(readings), "events": events}

    def _names_withheld_reading(self, connection: Any, table: str, row_id: Any) -> bool:
        """Whether a reading question's recorded anchor or context names a withheld reading."""

        found = connection.execute(
            "/* ad-rules */ SELECT note_id, source_context_json FROM question_events WHERE id = ?",
            (str(row_id),)).fetchone()
        if found is None:
            return False
        from learnloop.ingest.locators import parse_block_span

        parsed = parse_block_span(str(found[0] or ""))
        if parsed is not None and self.reading_withheld(parsed[0]):
            return True
        keys, whole = reference_keys(_json(found[1], {}))
        return any(self.reading_withheld(extraction) for extraction, _span in keys) or any(
            self.reading_withheld(extraction) for extraction in whole)

    def plan_feedback_events(self, connection: Any) -> list[dict[str, Any]]:
        """The plan's ``item_done`` and ``item_served`` events AD's candidate estimates may pair (the
        feedback dwell; Codex verify F28): the registry's plan-event rule (an event naming a withheld
        item, presentation or attempt is absent), in the plan's order."""

        if not _has_table(connection, "attention_blocks"):
            return []
        blocks = {str(row["id"]): str(row["daily_plan_id"]) for row in _rows(
            connection, "/* ad-rules */ SELECT id, daily_plan_id FROM attention_blocks WHERE daily_plan_id IS NOT NULL "
            "AND plan_ordinal IS NOT NULL")}
        events = [{"plan_id": blocks[str(row["block_id"])], "block_id": str(row["block_id"]), "kind": row["kind"],
                   "detail": row["detail_json"], "created_at": row["created_at"], "id": row["id"]}
                  for row in self.rows(connection, "attention_block_events", "kind IN ('item_done', 'item_served')")
                  if str(row["block_id"]) in blocks]
        return sorted(events, key=lambda event: (event["plan_id"], str(event["created_at"]), str(event["id"])))

    def ledger(self, connection: Any) -> dict[str, Mapping[str, Any]]:
        """The authoritative observation ledger by attempt id (visible attempts only)."""

        from learnloop.db.stores.observation_ledger import load_authoritative_observation_ledger

        visible = {str(row["id"]) for row in self.attempts(connection)}
        return {str(entry["attempt_id"]): entry for entry in load_authoritative_observation_ledger(connection)
                if str(entry["attempt_id"]) in visible}

    def graded_counts(self, connection: Any) -> dict[str, int]:
        """Each LO's visible graded answers (the replay's window-closing cohort): the evidence count
        AD's commissioned path gives the rung selection instead of the incumbent's (fix round 10)."""

        ledger = self.ledger(connection)
        counts: dict[str, int] = {}
        for row in self.attempts(connection):
            if closes_window(row, ledger.get(str(row["id"]))):
                lo = str(row.get("learning_object_id"))
                counts[lo] = counts.get(lo, 0) + 1
        return counts

    def window_cutoff(self, connection: Any, learning_object_ids: Sequence[str]) -> str | None:
        """When the reading window of these LOs last closed: their last visible attempt that closes
        a window as the replay reads it (graded, not skipped or a self-report; :func:`closes_window`).
        The dose moderator's cutoff (§5.12; Codex verify F26)."""

        wanted = {str(lo) for lo in learning_object_ids}
        ledger = self.ledger(connection)
        last = None
        for row in self.attempts(connection):
            if str(row.get("learning_object_id")) in wanted and closes_window(row, ledger.get(str(row["id"]))):
                last = str(row["created_at"]) if last is None or str(row["created_at"]) > last else last
        return last

    def practice_minutes(self, connection: Any) -> list[float]:
        """The practice cohort's answer minutes (Codex verify F27): visible attempts that close a
        window (graded practice, not a skip or self-report) with a recorded positive latency."""

        ledger = self.ledger(connection)
        out = []
        for row in self.attempts(connection):
            latency = row.get("latency_seconds")
            if latency is None or float(latency) <= 0 or not closes_window(row, ledger.get(str(row["id"]))):
                continue
            out.append(float(latency) / 60.0)
        return out

    # -- presentations, reveals, forecast history ------------------------------------------------

    def _presentation_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool:
        """A presentation is withheld with its item, or with the revision it froze."""

        if self.withheld(row.get("practice_item_id")):
            return True
        return self.revision_withheld(connection, self._frozen_revisions(connection).get(str(row["id"])))

    def presentations(self, connection: Any) -> dict[str, dict[str, Any]]:
        """Plan presentations of visible items and revisions, by id."""

        return {str(row["id"]): row for row in self.rows(connection, "plan_presentations")}

    def presentation(self, connection: Any, presentation_id: str) -> dict[str, Any] | None:
        found = self.rows(connection, "plan_presentations", "id = ?", (presentation_id,))
        return found[0] if found else None

    def presentation_status(self, connection: Any, presentation_id: str) -> tuple[str, dict[str, Any] | None]:
        """``("ok", row)``, ``("withheld", None)`` (its item is withheld now: a caller reports
        ``protected`` and reads nothing of it) or ``("missing", None)``."""

        status, row = self.lookup(connection, "plan_presentations", "id = ?", (presentation_id,))
        return status, (row if status == "ok" else None)

    def plan_event_visible(self, connection: Any) -> Any:
        """The rule for plan block events AD may read (the feedback dwell of AD's candidate
        estimates; Codex verify F28, fix round 10): an event naming a withheld item, an event of a
        withheld presentation (its block and item), or a completion of a withheld attempt, is
        invisible. Everything is invisible while unavailable."""

        attempts = {str(row["id"]): row for row in _rows(connection, "/* ad-rules */ SELECT * FROM practice_attempts")}
        # A serve is withheld with its presentation (its frozen revision): the plan's events name
        # no presentation, so it is found by its block and item.
        withheld_serves = self._withheld_serves(connection) if self.available else set()

        def visible(kind: str, detail: Mapping[str, Any], block_id: str | None = None) -> bool:
            if not self.available:
                return False
            item_id = detail.get("practice_item_id")
            if item_id and self.withheld(item_id):
                return False
            if item_id and block_id is not None and (str(block_id), str(item_id)) in withheld_serves:
                return False
            attempt = attempts.get(str(detail.get("attempt_id"))) if detail.get("attempt_id") else None
            return attempt is None or not self.attempt_withheld(connection, attempt)

        return visible

    def reveals(self, connection: Any) -> list[dict[str, Any]]:
        """``reveal_events`` rows AD may see (an exposure warms its LO, §5.2): withheld with its item,
        its attempt, or its tutor question (and so that question's attempt): an attempt withheld for
        the revision it answered withholds its reveals too (Codex verify F20, fix round 10)."""

        return self.rows(connection, "reveal_events", order="created_at, id")

    def withheld_reveal_ids(self, connection: Any) -> set[str]:
        """The ``reveal_events`` ids AD may not read (every one while unavailable): for a reader
        outside AD that takes an exclusion list (the recent-reveal exclusion, fix round 11)."""

        if not _has_table(connection, "reveal_events"):
            return set()
        every = {str(row[0]) for row in connection.execute("/* ad-rules */ SELECT id FROM reveal_events")}
        return every - {str(row["id"]) for row in self.reveals(connection)}

    def _withheld_serves(self, connection: Any) -> set[tuple[str, str]]:
        """``(block_id, practice_item_id)`` of every presentation withheld with its frozen revision."""

        if not _has_table(connection, "plan_presentations"):
            return set()
        return {(str(row.get("block_id")), str(row.get("practice_item_id")))
                for row in _rows(connection, "/* ad-rules */ SELECT * FROM plan_presentations")
                if self._presentation_withheld(connection, row)}

    def selections(self, connection: Any, *, kind: str | None = None) -> list[dict[str, Any]]:
        """``ad_selections`` as AD's report may count them (Codex verify F39, fix rounds 11-12): a
        draw whose chosen item or originating slot item is withheld (or in a presentation withheld
        with its frozen revision), whatever its kind (an empty-support draw included), or that
        commissioned a cell whose facet only withheld material names is left out of every
        statistic and window boundary. The ledger itself is never changed. Empty while
        unavailable."""

        from learnloop.db.stores import ad_serving

        if not self.available or not _has_table(connection, ad_serving.SELECTIONS):
            return []
        rows = ad_serving.selections(connection, kind=kind) if kind else ad_serving.selections(connection)
        return self.filter(connection, "ad_selections", rows)

    def revision_hash_withheld(self, connection: Any, content_hash: Any) -> bool:
        """Whether a revision named only by its hash is withheld: a saved revision is judged by its
        own sources, else a current item with that revision by the item. A hash no saved revision
        or current item has is merely unknown (not withheld)."""

        if not self.available:
            return True
        if not content_hash:
            return False
        found = connection.execute("/* ad-rules */ SELECT 1 FROM practice_item_snapshots WHERE content_hash = ?",
                                   (str(content_hash),)).fetchone()
        if found is not None:
            return self.revision(connection, str(content_hash)) is None
        from learnloop.adaptive_difficulty.feature_audit import item_revision

        for item_id, item in (getattr(self.vault, "practice_items", {}) or {}).items():
            if item_revision(item)[0] == str(content_hash):
                return self.withheld(item_id) or self.covers(item)
        return False

    def forecast_receipts(self, connection: Any, *, kind: str) -> list[dict[str, Any]]:
        """Forecast receipts of visible items, revisions, attempts and presentations (Codex verify
        F24: a calibration fit and a forecaster's history never read a withheld item's forecast,
        whatever the current target)."""

        from learnloop.db.stores import forecast_receipts as receipt_store

        if not self.available:
            return []
        return self.filter(connection, "forecast_receipts", receipt_store.list_receipts(connection, kind=kind))

    # -- the Reader's sources --------------------------------------------------------------------

    def material_withheld(self, extraction_id: Any, span_id: Any = None) -> bool:
        """Whether a span (or, with none, the whole extraction) is held out; everything is withheld
        while the predicate is unavailable."""

        if not self.available:
            return True
        material = self.protection.material
        if getattr(material, "empty", False):
            return False
        return bool(material.covers(str(extraction_id), None if span_id is None else str(span_id)))

    def reading_withheld(self, extraction_id: Any) -> bool:
        """Whether a READING (an extraction) is withheld for AD's reading signals (the AD23 redesign
        round 8, Option B): the withheld material touches it, wholly or in one block, or the predicate
        is unavailable (fail closed). Such a reading is, for its structure (blocks, units, sections,
        roles, aliases) and its reading events (exposures, section completions, Reader and tutor
        questions, dose offers), as if it had never been extracted. Practice items made from its
        visible parts are judged by their own sources, as before (``withheld``, ``covers``). It
        reveals one bit per reading, never what or where."""

        if not self.available:
            return True
        material = self.protection.material
        if getattr(material, "empty", False) or extraction_id is None:
            return False
        if self._touched is None:
            self._touched = frozenset(str(extraction) for extraction in material.touched)
        return str(extraction_id) in self._touched

    def document_ir(self, repository: Any, extraction_id: str) -> Any:
        """An extraction's document IR as AD may read it (the operation repository's loader, the one
        chokepoint for reading structure): none for a reading the withheld material touches
        (:meth:`reading_withheld`; the AD23 redesign round 8), else the stored IR exactly as
        ingest wrote it, which is then derived from that reading's own blocks, all visible (the
        Reader's and AD1's reading)."""

        if not self.available or self.reading_withheld(extraction_id):
            return None
        from learnloop.adaptive_difficulty.operation import Scope, scoped

        return scoped(Scope.DERIVE, lambda: repository.load_document_ir(extraction_id))

    def projected_vault(self) -> Any:
        """The vault an AD operation hands its readers (``op.vault``; the AD23 redesign, step 4):
        only the visible current items and notes (:meth:`vault_view`), no facet only withheld
        material names, and no LO or facet provenance reference into withheld material (a span
        list keeps its visible spans; a reference left with none, or to a withheld extraction or
        note, is dropped). Built once per view."""

        if self._projected is None:
            self._projected = self._project_vault()
        return self._projected

    def _project_vault(self) -> Any:
        import dataclasses
        from contextlib import closing

        from learnloop.db.connection import connect

        base = self.vault_view()
        with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
            canonical = getattr(base, "canonical_facet_id", None)
            dropped = self.protected_only_facets(connection) if self.available and canonical is not None else set()

            def refs(provenance: Any) -> Any:
                source_refs = list(getattr(provenance, "source_refs", None) or [])
                kept = [ref for ref in (self._visible_ref(connection, ref) for ref in source_refs) if ref is not None]
                if len(kept) == len(source_refs) and all(a is b for a, b in zip(kept, source_refs)):
                    return provenance
                return provenance.model_copy(update={"source_refs": kept})

            los = {lo_id: (lo if getattr(lo, "provenance", None) is None
                           else lo.model_copy(update={"provenance": refs(lo.provenance)}))
                   for lo_id, lo in (getattr(base, "learning_objects", {}) or {}).items()}
            facets = {}
            for facet_id, facet in (getattr(base, "evidence_facets", {}) or {}).items():
                if canonical is not None and canonical(str(facet_id)) in dropped:
                    continue
                provenance = getattr(facet, "provenance", None)
                facets[facet_id] = facet if provenance is None else facet.model_copy(
                    update={"provenance": refs(provenance)})
        projected = _replaced(base, learning_objects=los, evidence_facets=facets)
        object.__setattr__(projected, "_ad_raw_vault", self.vault)
        return projected

    def _visible_ref(self, connection: Any, ref: Any) -> Any:
        """A provenance reference as AD may read it (None: withheld).

        The reference is located first, through the shared key function (``exam_material.
        reference_keys``, i.e. ``source_ref_keys``: its extraction, its span ids, plain or namespaced,
        AND the span its locator names), and removed whole when ANY key is withheld (the AD23
        redesign round 4). Nothing of a removed reference survives, so its quote or locator can never
        restore its anchor (the Reader's quote fallback then runs over the projected references and
        the projected IR only)."""

        if not self.available:
            return None
        if getattr(ref, "ref_type", None) == "note" and ref.ref_id and self._note_ref_withheld(connection, ref.ref_id):
            return None
        if self.keys_withheld(*reference_keys(ref)):
            return None
        extraction = getattr(ref, "extraction_id", None)
        if extraction and self.material_withheld(extraction):
            return None
        section = getattr(ref, "section_id", None)
        if extraction and section and not getattr(ref, "span_ids", None) and all(
                self.material_withheld(extraction, span)
                for span in self.section_spans(str(extraction), str(section)) or ["?"]):
            return None
        return ref

    def keys_withheld(self, keys: Iterable[tuple[str, str]], whole: Iterable[str] = ()) -> bool:
        """Whether any located key (``exam_material.reference_keys``) is withheld: a block key in
        held-out material, or an extraction named whole that is held out."""

        return any(self.material_withheld(extraction, span) for extraction, span in keys) or any(
            self.material_withheld(extraction) for extraction in whole)

    def span_reanchors(self, repository: Any, from_extraction_id: str, to_extraction_id: str) -> list[dict[str, Any]]:
        """The span aliases AD may use between two readings (the operation repository's
        ``span_reanchors_between``, so the only set a ``SpanTranslator`` inside an operation sees; the
        AD23 redesign round 3).

        * The automatic aliases (``exact_hash``, ``geometry_section``: ``reanchor_spans``) are
          computed again from the two PROJECTED readings (``span_aliases.computed_aliases`` on the
          projected repository, cached per protection epoch). A persisted or incumbent automatic
          alias is never used, even with both endpoints public: its match may have been decided by
          held-out neighbours (a duplicated public block re-anchored by the held-out blocks around it).
        * A ``manual`` alias (the schema allows it; no production path writes one today, only
          ``Repository.insert_span_reanchor``) is an owner's own decision, kept when both its
          endpoints are visible, and it overrides the computed alias of its span."""

        if not self.available or self.reading_withheld(from_extraction_id) or self.reading_withheld(to_extraction_id):
            return []
        from learnloop.content.sources.span_aliases import computed_aliases
        from learnloop.ingest.reanchor import MANUAL

        from learnloop.adaptive_difficulty.projection import project_repository

        raw = getattr(repository, "_ad_raw_repository", repository)
        manual = [row for row in self.filter(None, "source_span_reanchors",
                                             raw.span_reanchors_between(from_extraction_id, to_extraction_id))
                  if str(row.get("match_kind")) == MANUAL]
        overridden = {str(row["from_span_id"]) for row in manual}
        computed = computed_aliases(project_repository(raw, self), from_extraction_id, to_extraction_id)
        return manual + [
            {"from_extraction_id": from_extraction_id, "from_span_id": span, "to_extraction_id": to_extraction_id,
             "to_span_id": to_span, "match_kind": kind, "confidence": confidence}
            for span, (to_span, kind, confidence) in sorted(computed.items()) if span not in overridden]

    def section_spans(self, extraction_id: str, section_id: str) -> list[str]:
        """A Reader section's spans, read only through :meth:`document_ir` (round 8, F3): none for
        a reading the withheld material touches."""

        if extraction_id not in self._section_spans:
            from learnloop.reader.reader_guidance import extraction_sections

            sections: dict[str, list[str]] = {}
            try:
                ir = self.document_ir(self.repository, extraction_id)
                if ir is not None:
                    rows, _blocks, _map = extraction_sections(ir)
                    sections = {str(row["id"]): [str(span) for span in row["span_ids"]] for row in rows}
            except Exception:  # noqa: BLE001 - an unreadable extraction has no spans
                sections = {}
            self._section_spans[extraction_id] = sections
        return self._section_spans[extraction_id].get(section_id, [])

    def section_withheld(self, extraction_id: str, section_id: str) -> bool:
        """A Reader section is withheld with its reading (round 8): a section of a reading no
        withheld block touches has none."""

        return self.reading_withheld(extraction_id)

    def question_event_withheld(self, connection: Any, question_id: Any) -> bool:
        """The one protection reader of a tutor question (``question_events``; Codex verify F46, fix
        round 14), used when the sweep collects it and when its receipt is revalidated. It is withheld
        when ANY part of its complete recorded source context is: its anchor (``note_id``, a span key
        or a canonical note), its item, and every span its ``source_context`` names (the anchor,
        ``source_spans``, ``citations``, retrieval and delivery records: every recorded mapping with an
        extraction id). Everything is withheld while unavailable; an unreadable context is withheld."""

        from learnloop.ingest.locators import parse_block_span

        if not self.available:
            return True
        if not _has_table(connection, "question_events"):
            return False
        columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(question_events)")}
        context_column = "source_context_json" if "source_context_json" in columns else "NULL"
        found = connection.execute(
            f"/* ad-rules */ SELECT note_id, practice_item_id, {context_column}, context FROM question_events "
            "WHERE id = ?", (str(question_id),)).fetchone()
        if found is None:
            return False
        note_id, item_id, raw = found[0], found[1], found[2]
        # Only a READING question (asked in the Reader or the library) is a reading event, withheld
        # with any reading it names (round 8, Option B). A practice or feedback question is attempt
        # evidence (help timing, its reveals): it keeps the block rule (round 8 follow-up, F1).
        reading = str(found[3] or "") in READING_QUESTION_CONTEXTS
        if note_id:
            parsed = parse_block_span(str(note_id))
            if parsed is not None:
                if self.reading_withheld(parsed[0]) if reading else self.material_withheld(parsed[0], parsed[1]):
                    return True
            elif self.note_withheld(connection, note_id):
                return True
        if item_id and self.withheld(item_id):
            return True
        try:
            context = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            return True
        # Every reference shape in it (spans, anchors, locators, hrefs, retrieval keys), located by
        # the one key function (round 4); a context citing a reading the withheld material touches is
        # a reading event of that reading (round 8).
        keys, whole = reference_keys(context)
        if self.keys_withheld(keys, whole):
            return True
        return reading and (any(self.reading_withheld(extraction) for extraction, _span in keys) or any(
            self.reading_withheld(extraction) for extraction in whole))

    def question_withheld(self, row: Mapping[str, Any]) -> bool:
        """A Reader question is withheld when its extraction, or any span it is anchored on or cites,
        is held out (Codex verify F23)."""

        extraction = row.get("extraction_id")
        if extraction is None or self.reading_withheld(extraction):
            return True
        spans = _spans(row.get("anchor_span_ids_json")) + _spans(row.get("span_ids_json"))
        keys, whole = reference_keys({"extraction_id": extraction, "span_ids": spans})
        # A question cites its own reading's spans; one citing another reading is judged by it.
        return any(self.reading_withheld(key_extraction) for key_extraction, _span in keys) or any(
            self.reading_withheld(name) for name in whole)

    def answered_questions(self, connection: Any, styles: Sequence[str]) -> list[dict[str, Any]]:
        """Answered, undismissed Reader questions of these styles that are not withheld."""

        marks = ",".join("?" for _ in styles)
        # The anchors AND the cited spans are judged (Codex verify F31): the registry's self rule.
        return self.rows(connection, "reader_authored_questions",
                         f"answered_at IS NOT NULL AND status != 'dismissed' AND question_style IN ({marks})", styles)

    def question(self, connection: Any, question_id: Any) -> dict[str, Any] | None:
        """One Reader question's row (every column), or None when it is missing or withheld."""

        found = self.rows(connection, "reader_authored_questions", "id = ?", (str(question_id),))
        return found[0] if found else None

    def open_questions(self, connection: Any, extraction_id: str, section_id: str) -> list[dict[str, Any]]:
        """A section's produced, unanswered, undismissed Reader questions that are not withheld."""

        return self.rows(connection, "reader_authored_questions",
                         "extraction_id = ? AND section_id = ? AND answered_at IS NULL AND status != 'dismissed'",
                         (extraction_id, section_id), order="created_at, id")

    def reading_opportunities(self, connection: Any, *, learning_object_ids: Sequence[str] | None = None
                              ) -> list[dict[str, Any]]:
        """``ad_reading_opportunities`` receipts of the current epoch, revalidated now (Codex verify
        F20): a receipt whose source is withheld is invisible. Its doses were mapped under this very
        projection (round 2: a receipt of another epoch is swept again), so they stand as recorded; a
        frozen dose on a facet merely absent from current content stands (Codex verify F30). Oldest
        source first."""

        from learnloop.db.stores import ad_receipts

        wanted = None if learning_object_ids is None else {str(lo) for lo in learning_object_ids}
        return [row for row in self.rows(connection, ad_receipts.READING, order="source_written_at, id")
                if wanted is None or str(row.get("learning_object_id")) in wanted]

    def _opportunity_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool:
        """Resolve a receipt's source again against the current predicate: the source row, by its own
        table's rule. A source row since deleted cannot be resolved and its receipt stands as recorded
        (receipts are frozen: a deleted source leaves them, §5.11; Codex verify F30); one that cannot
        be read is withheld (fail closed)."""

        table, source, kind = str(row.get("source_table")), str(row.get("source_id") or ""), str(row.get("kind"))
        try:
            if table == "reader_section_progress":
                extraction, _sep, _rest = source.partition("/")
                return self.reading_withheld(extraction)
            if table in _T.COLUMNS and table != "ad_reading_opportunities":
                if not _has_table(connection, table):
                    return False
                found = _rows(connection, f"/* ad-rules */ SELECT {_select(table)} FROM {table} WHERE id = ?",
                              (source,))
                return any(not self.keep(connection, table, found_row) for found_row in found)
        except Exception:  # noqa: BLE001 - an unreadable source is withheld (fail closed)
            warn_failure(LOG, "AD reading source %s/%s unresolved: withheld", table, source)
            return True
        return True


def _in_rules(method: Any) -> Any:
    """Run a view reader in the rules' read scope (the AD guard lets the rules read protected
    tables; their SQL carries the rules marker), through the scope's codec: a failure inside it
    leaves as a ``ViewFailure`` of its kind and type only (the final round)."""

    import functools

    from learnloop.adaptive_difficulty.operation import Scope, scoped

    @functools.wraps(method)
    def reader(*args: Any, **kwargs: Any) -> Any:
        return scoped(Scope.VIEW, lambda: method(*args, **kwargs))

    return reader


def _wrap_readers(cls: type) -> None:
    for name, method in list(vars(cls).items()):
        if callable(method) and not name.startswith("__") and not isinstance(method, (staticmethod, classmethod, type)):
            setattr(cls, name, _in_rules(method))


_wrap_readers(MaterialView)


def material_view(vault: Any, repository: Any, protected: Any = None) -> MaterialView:
    """The open operation's view (the AD23 redesign): ``protected`` None returns the view of the
    operation open in this context (:mod:`~learnloop.adaptive_difficulty.operation`); outside an
    operation that is an error, so no AD reader computes a fresh, unguarded view by accident. A
    :class:`MaterialView` is returned as it is; a :class:`Protection` or an id set builds a view on it
    (an id set adds its ids to a fresh predicate)."""

    if isinstance(protected, MaterialView):
        return protected
    if protected is None:
        from learnloop.adaptive_difficulty.operation import current

        op = current()
        if op is None:
            raise RuntimeError("an AD material view was asked for outside an AD operation")
        return op.view
    return detached_view(vault, repository, protected)


def current_view() -> MaterialView:
    """The view of the operation open in this context (an error outside one)."""

    return material_view(None, None)


def detached_view(vault: Any, repository: Any, protected: Any = None) -> MaterialView:
    """A view computed here, outside any operation's guard: for the operation itself, the egress
    guards (which re-read protection afresh by design) and the incumbent's generation boundary (E1).
    ``protected`` as :func:`material_view`'s; None computes the predicate once."""

    # The predicate is read through its module, so it is the one place AD computes it.
    if isinstance(protected, MaterialView):
        return protected
    if protected is None:
        return MaterialView(vault, repository, _predicate.protection(vault, repository))
    return MaterialView(vault, repository, _predicate.guard(vault, repository, protected))


def closes_window(attempt: Mapping[str, Any], ledger_entry: Mapping[str, Any] | None) -> bool:
    """Whether a visible attempt closes its LO's reading windows (§5.6): graded (its ledger entry
    has evidence), and neither a skip nor a self-report (D8). The replay and the dose moderator
    read this one rule."""

    if str(attempt.get("attempt_type") or "") in NON_WINDOW_TYPES:
        return False
    return bool((ledger_entry or {}).get("evidence"))


__all__ = ["MaterialView", "NON_WINDOW_TYPES", "UNAVAILABLE", "closes_window", "current_view", "detached_view",
           "material_view"]
