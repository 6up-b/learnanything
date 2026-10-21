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
* **a reading-opportunity receipt** is revalidated against the current
  predicate before replay reads it: its source is resolved again, and its
  doses keep only facets the view still names.

AD's protection is unconditional: it never reads ``goals.held_out_selection``
or any routine-serving switch, which only govern routine serving.

**Fail closed.** When the predicate cannot be computed the view is
*unavailable*: every item-derived reader is empty and every source is withheld.
The operation then degrades to its incumbent behaviour (the slot serves its
planned item, generation takes the predecessor's target path, the report
discloses zero observations and why), never to unfiltered data and never to an
exception.

``tests/test_ad23_material_view.py`` pins the boundary: no module under
``adaptive_difficulty/`` (nor ``daily_plan/ad_slot.py``, the commissioned path
of ``content/authoring/practice_generation.py`` or the sidecar's AD handlers)
reads the raw item, attempt, question, reading-receipt, presentation or reveal
tables, or the vault's item map, except this module, the predicate itself
(``protection.py``) and ``data_check``'s descriptive inventory.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from learnloop.adaptive_difficulty import protected_tables as _T
from learnloop.adaptive_difficulty import protection as _predicate
from learnloop.adaptive_difficulty.protection import Protection

LOG = logging.getLogger(__name__)

#: Why a view is empty: the held-out predicate could not be computed.
UNAVAILABLE = "held_out_predicate_unavailable"
_VALUE = _T.VALUE
#: The attempt types that never close a reading window (as the replay reads them, §5.6, D8).
NON_WINDOW_TYPES = ("skip", "self_report")


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
        self._universe: set[str] | None = None
        self._answered: dict[str, tuple[str, ...]] | None = None
        self._frozen: dict[str, str] | None = None
        self._protected_only: dict[bool, set[str]] = {}
        self._memo: dict[Any, Any] | None = None


    # -- the registry's rule (``protected_tables.COLUMNS``) ------------------------------------------

    def rows(self, connection: Any, table: str, where: str = "", args: Iterable[Any] = (), *,
             order: str = "") -> list[dict[str, Any]]:
        """The rows of a protected table AD may read: every column, the rows any of whose references
        resolves to a withheld entity left out (:meth:`keep`), a reading receipt's doses without the
        facets only withheld material names. Empty while unavailable or without the table."""

        if not self.available or not _has_table(connection, table):
            return []
        _columns(table)
        sql = f"/* ad-rules */ SELECT * FROM {table}" + (f" WHERE {where}" if where else "") + (
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
            return [self._transformed(connection, table, dict(row)) for row in rows
                    if self.keep(connection, table, row)]
        finally:
            if outer is None:
                self._memo = None

    def lookup(self, connection: Any, table: str, where: str, args: Iterable[Any] = ()
               ) -> tuple[str, dict[str, Any] | None]:
        """An idempotency read of AD's own ledgers: ``("missing", None)``, ``("withheld", None)`` (a
        row exists that AD may not read: its caller writes nothing and reads nothing of it) or
        ``("ok", row)``. Everything is ``withheld`` while unavailable."""

        if not _has_table(connection, table):
            return "missing", None
        _columns(table)
        found = _rows(connection, f"/* ad-rules */ SELECT * FROM {table} WHERE {where}", args)
        if not found:
            return "missing", None
        kept = self.filter(connection, table, found)
        return ("ok", kept[0]) if len(kept) == len(found) else ("withheld", None)

    def keep(self, connection: Any, table: str, row: Mapping[str, Any]) -> bool:
        """The registry's one rule: a row is withheld when any reference column resolves to a withheld
        entity (the kinds: ``protected_tables.COLUMNS``)."""

        if not self.available:
            return False
        selfs = False
        for column, kind in _columns(table).items():
            if kind in (_VALUE, "doses"):
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

    def _transformed(self, connection: Any, table: str, row: dict[str, Any]) -> dict[str, Any]:
        if table == "ad_reading_opportunities":
            # The second named exception: a receipt's doses keep only facets the view still names
            # (a frozen dose on a facet merely absent from current content stands, F30).
            dropped = self.protected_only_facets(connection)
            raw = row.get("facet_doses_json")
            try:
                doses = json.loads(raw) if isinstance(raw, str) else (raw or {})
            except (TypeError, ValueError):
                doses = {}
            if isinstance(doses, Mapping):
                kept = {f: d for f, d in doses.items() if self.vault.canonical_facet_id(str(f)) not in dropped}
                row["facet_doses_json"] = json.dumps(kept, sort_keys=True)
        return row

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
        if base == "extraction":
            return self.material_withheld(value)
        if base == "span":
            return self.material_withheld(row.get(arg), value)
        if base == "section":
            return self.section_withheld(str(row.get(arg)), str(value))
        if base == "spans":
            spans = value if isinstance(value, list) else _spans(value)
            return any(self.material_withheld(row.get(arg), span) for span in spans)
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
            found = _rows(connection, f"/* ad-rules */ SELECT * FROM {table} WHERE {key} = ?", (str(value),)) \
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
        raise ValueError(f"no self rule for {table}")

    def _note_ref_withheld(self, connection: Any, note_id: Any) -> bool:
        from learnloop.ingest.locators import parse_block_span

        parsed = parse_block_span(str(note_id))
        if parsed is not None:
            return self.material_withheld(parsed[0], parsed[1])
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
                universe.update(self.vault.canonical_facet_id(str(f)) for f in item.evidence_facets)
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
            canonical = self.vault.canonical_facet_id
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
            return dataclasses.replace(self.vault, practice_items=visible)
        from contextlib import closing

        from learnloop.db.connection import connect

        kept: dict[str, Any] = {}
        if self.available:
            with closing(connect(self.repository.sqlite_path, read_only=True)) as connection:
                kept = {note_id: note for note_id, note in notes.items()
                        if not self.note_withheld(connection, note_id)}
        return dataclasses.replace(self.vault, practice_items=visible, notes=kept)

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
            return self.material_withheld(content.get("extraction_id"), content.get("span_id"))
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

    def open_commissions(self, connection: Any, *, now: str | None = None) -> list[dict[str, Any]]:
        """Open commissions as the view sees them: a result on a withheld item does not land, and a
        commission of a cell whose facet only withheld material names is not open (the same cohort
        as :meth:`selections`, fix round 11)."""

        from learnloop.db.stores import ad_serving

        landed = {str(row["selection_id"]) for row in self.visible_commission_results(connection)}
        facets = self.protected_only_facets(connection)
        canonical = getattr(self.vault, "canonical_facet_id", lambda value: value)
        return [row for row in ad_serving.open_commissions(connection, now=now, landed=landed)
                if not (row.get("cell_facet") and canonical(str(row["cell_facet"])) in facets)]

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
                LOG.warning("field revision resolution failed: attempts judged by frozen revisions", exc_info=True)
            self._answered = {key: tuple(sorted(values)) for key, values in answered.items()}
        return self._answered

    def answered_revision_items(self, connection: Any, attempt_id: Any) -> list[Any]:
        """The saved revisions an attempt answered, as items (to freeze their source identities for
        a later revalidation; fix round 10, R4). Content is never returned to a prompt from here."""

        from learnloop.vault.models import PracticeItem

        out = []
        for content_hash in self._answered_revisions(connection).get(str(attempt_id), ()):
            found = connection.execute("/* ad-rules */ SELECT item_json FROM practice_item_snapshots WHERE content_hash = ?",
                                       (content_hash,)).fetchone()
            if found is None:
                continue
            try:
                out.append(PracticeItem.model_validate_json(found[0]))
            except ValueError:
                continue
        return out

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

    def attempt_withheld_by_id(self, connection: Any, attempt_id: Any) -> bool:
        """Whether an attempt (by id) is withheld now; a missing attempt is withheld (fail closed)."""

        return self.lookup(connection, "practice_attempts", "id = ?", (str(attempt_id),))[0] != "ok"

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

        return self.lookup(connection, "plan_presentations", "id = ?", (presentation_id,))

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

    def visible_loadings(self, connection: Any, content_hash: Any,
                         loadings: Mapping[str, Any] | None) -> dict[str, float]:
        """A revision's relatedness loadings as AD may use them (Codex verify F38, fix round 11):
        none when the revision is withheld (its support), and no loading onto a facet only withheld
        material names. A facet merely absent from current content keeps its loading (as F30's
        frozen dose does)."""

        if not self.available or not loadings or self.revision_hash_withheld(connection, content_hash):
            return {}
        facets = self.protected_only_facets(connection)
        canonical = getattr(self.vault, "canonical_facet_id", lambda value: value)
        return {str(facet): float(score) for facet, score in loadings.items()
                if canonical(str(facet)) not in facets}

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

    def section_spans(self, extraction_id: str, section_id: str) -> list[str]:
        if extraction_id not in self._section_spans:
            from learnloop.reader.reader_guidance import extraction_sections

            sections: dict[str, list[str]] = {}
            try:
                ir = self.repository.load_document_ir(extraction_id)
                if ir is not None:
                    rows, _blocks, _map = extraction_sections(ir)
                    sections = {str(row["id"]): [str(span) for span in row["span_ids"]] for row in rows}
            except Exception:  # noqa: BLE001 - an unreadable extraction has no spans
                sections = {}
            self._section_spans[extraction_id] = sections
        return self._section_spans[extraction_id].get(section_id, [])

    def section_withheld(self, extraction_id: str, section_id: str) -> bool:
        return self.material_withheld(extraction_id) or any(
            self.material_withheld(extraction_id, span) for span in self.section_spans(extraction_id, section_id))

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
            f"/* ad-rules */ SELECT note_id, practice_item_id, {context_column} FROM question_events WHERE id = ?",
            (str(question_id),)).fetchone()
        if found is None:
            return False
        note_id, item_id, raw = found[0], found[1], found[2]
        if note_id:
            parsed = parse_block_span(str(note_id))
            if parsed is not None:
                if self.material_withheld(parsed[0], parsed[1]):
                    return True
            elif self.note_withheld(connection, note_id):
                return True
        if item_id and self.withheld(item_id):
            return True
        try:
            context = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            return True

        def named(value: Any) -> bool:
            if isinstance(value, Mapping):
                extraction = value.get("extraction_id")
                if extraction and self.material_withheld(extraction, value.get("span_id")):
                    return True
                return any(named(child) for child in value.values())
            if isinstance(value, (list, tuple)):
                return any(named(child) for child in value)
            return False

        return named(context)

    def question_withheld(self, row: Mapping[str, Any]) -> bool:
        """A Reader question is withheld when its extraction, or any span it is anchored on or cites,
        is held out (Codex verify F23)."""

        extraction = row.get("extraction_id")
        if extraction is None or self.material_withheld(extraction):
            return True
        spans = _spans(row.get("anchor_span_ids_json")) + _spans(row.get("span_ids_json"))
        return any(self.material_withheld(extraction, span) for span in spans)

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
        """``ad_reading_opportunities`` receipts revalidated now (Codex verify F20): a receipt whose
        source is withheld is invisible, and its doses drop only facets that withheld material alone
        names (:meth:`protected_only_facets`). A frozen dose on a facet merely absent from current
        content stands (Codex verify F30). Oldest source first."""

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
                extraction, _sep, rest = source.partition("/")
                if kind == "worked_example":
                    return self.material_withheld(extraction, rest)
                return self.section_withheld(extraction, rest)
            if table in _T.COLUMNS and table != "ad_reading_opportunities":
                if not _has_table(connection, table):
                    return False
                found = _rows(connection, f"/* ad-rules */ SELECT * FROM {table} WHERE id = ?", (source,))
                return any(not self.keep(connection, table, found_row) for found_row in found)
        except Exception:  # noqa: BLE001 - an unreadable source is withheld (fail closed)
            LOG.warning("AD reading source %s/%s unresolved: withheld", table, source, exc_info=True)
            return True
        return True


def _in_rules(method: Any) -> Any:
    """Run a view reader in the rules' read scope (the AD guard lets the rules read protected
    tables; their SQL carries the rules marker)."""

    import functools

    from learnloop.adaptive_difficulty.operation import rules

    @functools.wraps(method)
    def reader(*args: Any, **kwargs: Any) -> Any:
        with rules("view"):
            return method(*args, **kwargs)

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


__all__ = ["MaterialView", "NON_WINDOW_TYPES", "UNAVAILABLE", "closes_window", "detached_view", "material_view"]
