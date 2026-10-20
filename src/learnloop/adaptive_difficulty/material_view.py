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

from learnloop.adaptive_difficulty import protection as _predicate
from learnloop.adaptive_difficulty.protection import Protection

LOG = logging.getLogger(__name__)

#: Why a view is empty: the held-out predicate could not be computed.
UNAVAILABLE = "held_out_predicate_unavailable"
#: The attempt types that never close a reading window (as the replay reads them, §5.6, D8).
NON_WINDOW_TYPES = ("skip", "self_report")


def _has_table(connection: Any, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone() is not None


def _rows(connection: Any, sql: str, args: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(args))
    names = [d[0] for d in cursor.description]
    return [dict(zip(names, raw)) for raw in cursor.fetchall()]


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

    def revision(self, connection: Any, content_hash: str | None) -> Any:
        """A saved revision (``practice_item_snapshots``) as an item, or None when it is missing or
        withheld (its item withheld now, or its own sources held out)."""

        from learnloop.vault.models import PracticeItem

        if not content_hash or not self.available:
            return None
        if content_hash not in self._revisions:
            found = connection.execute(
                "SELECT practice_item_id, item_json FROM practice_item_snapshots WHERE content_hash = ?",
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
                "SELECT content_hash FROM practice_item_snapshots ORDER BY created_at, content_hash"):
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
                "SELECT content_hash, practice_item_id, item_json FROM practice_item_snapshots "
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
        found = connection.execute("SELECT 1 FROM practice_item_snapshots WHERE content_hash = ?",
                                   (content_hash,)).fetchone()
        return found is not None and self.revision(connection, content_hash) is None

    # -- attempts --------------------------------------------------------------------------------

    def attempts(self, connection: Any) -> list[dict[str, Any]]:
        """Every visible ``practice_attempts`` row (all columns, latency included), oldest first. An
        attempt on a withheld item is invisible: it trains nothing, closes no reading window, takes
        no first surface and warms nothing (Codex verify F20)."""

        if not self.available:
            return []
        return [row for row in _rows(connection, "SELECT * FROM practice_attempts ORDER BY created_at, id")
                if not self.withheld(row.get("practice_item_id"))]

    def attempted_item_ids(self, connection: Any) -> set[str]:
        return {str(row["practice_item_id"]) for row in self.attempts(connection)}

    def field_rows(self, connection: Any, **kwargs: Any) -> list[Any]:
        """Field's attempt rows (``field.outcomes.load_attempt_rows``) on visible items only."""

        from learnloop.field.outcomes import load_attempt_rows

        if not self.available:
            return []
        return [row for row in load_attempt_rows(connection, self.vault, **kwargs)
                if not self.withheld(row.features.item_id)]

    def ledger(self, connection: Any) -> dict[str, Mapping[str, Any]]:
        """The authoritative observation ledger by attempt id (visible attempts only)."""

        from learnloop.db.stores.observation_ledger import load_authoritative_observation_ledger

        visible = {str(row["id"]) for row in self.attempts(connection)}
        return {str(entry["attempt_id"]): entry for entry in load_authoritative_observation_ledger(connection)
                if str(entry["attempt_id"]) in visible}

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

    def presentations(self, connection: Any) -> dict[str, dict[str, Any]]:
        """Plan presentations of visible items, by id."""

        if not self.available or not _has_table(connection, "plan_presentations"):
            return {}
        return {str(row["id"]): row for row in _rows(connection, "SELECT * FROM plan_presentations")
                if not self.withheld(row.get("practice_item_id"))}

    def presentation(self, connection: Any, presentation_id: str) -> dict[str, Any] | None:
        if not self.available or not _has_table(connection, "plan_presentations"):
            return None
        found = _rows(connection, "SELECT * FROM plan_presentations WHERE id = ?", (presentation_id,))
        return found[0] if found and not self.withheld(found[0].get("practice_item_id")) else None

    def presentation_status(self, connection: Any, presentation_id: str) -> tuple[str, dict[str, Any] | None]:
        """``("ok", row)``, ``("withheld", None)`` (its item is withheld now: a caller reports
        ``protected`` and reads nothing of it) or ``("missing", None)``."""

        if not _has_table(connection, "plan_presentations"):
            return "missing", None
        found = connection.execute("SELECT practice_item_id FROM plan_presentations WHERE id = ?",
                                   (presentation_id,)).fetchone()
        if found is None:
            return "missing", None
        if self.withheld(found[0]):
            return "withheld", None
        return "ok", self.presentation(connection, presentation_id)

    def reveals(self, connection: Any) -> list[dict[str, Any]]:
        """``reveal_events`` rows of visible items (an exposure warms its LO, §5.2)."""

        if not self.available or not _has_table(connection, "reveal_events"):
            return []
        return [row for row in _rows(connection, "SELECT * FROM reveal_events ORDER BY created_at, id")
                if not row.get("practice_item_id") or not self.withheld(row.get("practice_item_id"))]

    def forecast_receipts(self, connection: Any, *, kind: str) -> list[dict[str, Any]]:
        """Forecast receipts of visible items and revisions (Codex verify F24: a calibration fit and
        a forecaster's history never read a withheld item's forecast, whatever the current target)."""

        from learnloop.db.stores import forecast_receipts as receipt_store

        if not self.available:
            return []
        return [receipt for receipt in receipt_store.list_receipts(connection, kind=kind)
                if not self.revision_withheld(connection, receipt.get("item_content_hash"),
                                              receipt.get("practice_item_id"))]

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

        if not self.available or not _has_table(connection, "reader_authored_questions"):
            return []
        marks = ",".join("?" for _ in styles)
        return [row for row in _rows(
            connection, "SELECT id, extraction_id, section_id, question_style, anchor_span_ids_json, answered_at "
            f"FROM reader_authored_questions WHERE answered_at IS NOT NULL AND status != 'dismissed' "
            f"AND question_style IN ({marks})", styles) if not self.question_withheld(row)]

    def question(self, connection: Any, question_id: Any) -> dict[str, Any] | None:
        """One Reader question's row (every column), or None when it is missing or withheld."""

        if not self.available or not _has_table(connection, "reader_authored_questions"):
            return None
        found = _rows(connection, "SELECT * FROM reader_authored_questions WHERE id = ?", (str(question_id),))
        return found[0] if found and not self.question_withheld(found[0]) else None

    def open_questions(self, connection: Any, extraction_id: str, section_id: str) -> list[dict[str, Any]]:
        """A section's produced, unanswered, undismissed Reader questions that are not withheld."""

        if not self.available or not _has_table(connection, "reader_authored_questions"):
            return []
        return [row for row in _rows(
            connection, "SELECT * FROM reader_authored_questions WHERE extraction_id = ? AND section_id = ? "
            "AND answered_at IS NULL AND status != 'dismissed' ORDER BY created_at, id", (extraction_id, section_id))
            if not self.question_withheld(row)]

    def reading_opportunities(self, connection: Any, *, learning_object_ids: Sequence[str] | None = None
                              ) -> list[dict[str, Any]]:
        """``ad_reading_opportunities`` receipts revalidated now (Codex verify F20): a receipt whose
        source is withheld is invisible, and its doses keep only facets the view names. Oldest
        source first."""

        from learnloop.db.stores import ad_receipts

        if not self.available or not _has_table(connection, ad_receipts.READING):
            return []
        wanted = None if learning_object_ids is None else {str(lo) for lo in learning_object_ids}
        universe = self.facet_universe()
        out = []
        for row in _rows(connection, f"SELECT * FROM {ad_receipts.READING} ORDER BY source_written_at, id"):
            if wanted is not None and str(row.get("learning_object_id")) not in wanted:
                continue
            if self._opportunity_withheld(connection, row):
                continue
            try:
                doses = json.loads(row.get("facet_doses_json") or "{}")
            except (TypeError, ValueError):
                doses = {}
            if isinstance(doses, Mapping):
                kept = {f: d for f, d in doses.items() if self.vault.canonical_facet_id(str(f)) in universe}
                row = {**row, "facet_doses_json": json.dumps(kept, sort_keys=True)}
            out.append(row)
        return out

    def _opportunity_withheld(self, connection: Any, row: Mapping[str, Any]) -> bool:
        """Resolve a receipt's source again against the current predicate. A source row since
        deleted cannot be resolved and its receipt stands as recorded (receipts are frozen: a
        deleted source leaves them, §5.11); one that cannot be read is withheld (fail closed)."""

        table, source, kind = str(row.get("source_table")), str(row.get("source_id") or ""), str(row.get("kind"))

        def question_withheld(question_id: Any) -> bool:
            found = _rows(connection, "SELECT * FROM reader_authored_questions WHERE id = ?", (str(question_id),)) \
                if _has_table(connection, "reader_authored_questions") else []
            return bool(found) and self.question_withheld(found[0])

        try:
            if table == "reader_section_progress":
                extraction, _sep, rest = source.partition("/")
                if kind == "worked_example":
                    return self.material_withheld(extraction, rest)
                return self.section_withheld(extraction, rest)
            if table == "source_exposure_events":
                found = connection.execute("SELECT extraction_id, span_id FROM source_exposure_events WHERE id = ?",
                                           (source,)).fetchone()
                return found is not None and self.material_withheld(found[0], found[1])
            if table == "question_events":
                from learnloop.ingest.locators import parse_block_span

                found = connection.execute("SELECT note_id, practice_item_id FROM question_events WHERE id = ?",
                                           (source,)).fetchone()
                if found is None:
                    return False
                parsed = parse_block_span(str(found[0])) if found[0] else None
                if parsed is not None and self.material_withheld(parsed[0], parsed[1]):
                    return True
                return bool(found[1]) and self.withheld(found[1])
            if table == "reader_authored_questions":
                return question_withheld(source)
            if table == "judgment_ledger":
                found = connection.execute("SELECT left_id FROM judgment_ledger WHERE id = ?", (source,)).fetchone()
                return found is not None and question_withheld(found[0])
            if table == "interaction_events":
                found = connection.execute(
                    "SELECT s.legacy_practice_item_id FROM interaction_events e "
                    "LEFT JOIN activity_administrations a ON a.id = e.administration_id "
                    "LEFT JOIN activity_surfaces s ON s.id = a.surface_id WHERE e.id = ?", (source,)).fetchone()
                return found is not None and bool(found[0]) and self.withheld(found[0])
        except Exception:  # noqa: BLE001 - an unreadable source is withheld (fail closed)
            LOG.warning("AD reading source %s/%s unresolved: withheld", table, source, exc_info=True)
            return True
        return True


def material_view(vault: Any, repository: Any, protected: Any = None) -> MaterialView:
    """The view for one operation. ``protected``: a :class:`Protection` the operation already
    computed (never recomputed), or an id set added to a fresh one; None computes it once here."""

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


__all__ = ["MaterialView", "NON_WINDOW_TYPES", "UNAVAILABLE", "closes_window", "material_view"]
