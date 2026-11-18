"""Learner-model evidence, misconceptions and intervention needs.

Owns error events, misconception state, belief events and the intervention need ledger."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import (
    _decode_error_event,
    _decode_intervention_need,
    _decode_misconception_candidate,
    _decode_scheduler_slate,
)
from learnloop.db.row_serialization import _json, _loads
from learnloop.db.stores.diagnoses import merge_causal_view_into_events
from learnloop.db.stores.grading import _decode_diagnostic_augmentation_receipt
from learnloop.ids import new_ulid
from learnloop.numeric import beta_mean, beta_quantile


@dataclass(frozen=True)
class ActiveErrorEvent:
    id: str
    learning_object_id: str
    error_type: str
    severity: float
    is_misconception: bool
    created_at: str
    misconception_id: str | None = None
    misconception_statement: str | None = None
    #: The attempt that recorded the event (None for an attempt-less event):
    #: mvp-0.21's probe lane holds out an event while its diagnosis is pending.
    attempt_id: str | None = None


@dataclass(frozen=True)
class MisconceptionRecord:
    """A normalized, content-bearing belief scoped to a learning object.

    ``severity`` is the max over source events (decayed by consumers, not here);
    ``source_error_event_ids`` is append-only provenance. See spec §1.1.
    """

    id: str
    learning_object_id: str
    concept_id: str | None
    statement: str
    signature: str | None
    facet_ids: list[str]
    severity: float
    status: str
    source_error_event_ids: list[str]
    created_at: str | None
    updated_at: str | None
    resolved_at: str | None
    # KM4 §10.2 compositional fields (NULL for legacy rows; populated when a
    # mvp-0.7 vault mints a compositional record).
    mechanism: str | None = None
    operation: str | None = None
    target_facet: str | None = None
    confused_with_facet: str | None = None
    trigger_conditions: list[str] = field(default_factory=list)
    expected_signatures: list[str] = field(default_factory=list)
    first_divergence: list[str] = field(default_factory=list)
    non_applicable_controls: list[str] = field(default_factory=list)
    promotion_reason: str | None = None
    correction_statement: str | None = None
    correction_source_span_ids: list[str] = field(default_factory=list)
    # Append-only semantic lifecycle overlay. In particular, P0 invalidated
    # first-error promotions are `demoted`, never learner-resolved.
    lifecycle_disposition: str | None = None


@dataclass(frozen=True)
class ItemMisconceptionDiscrimination:
    """Estimated discrimination of an item's keyed fatal error vs a misconception.

    Beta posteriors over sensitivity = P(fatal fires | learner holds belief) and
    specificity = P(no fire | clean learner). Consumers read the lower bounds
    (``sensitivity_lb`` / ``specificity_lb``) so thin-evidence rows self-limit.
    See spec §1.3.
    """

    practice_item_id: str
    misconception_id: str
    sensitivity_alpha: float
    sensitivity_beta: float
    specificity_alpha: float
    specificity_beta: float
    n_planted_trials: int
    n_clean_trials: int
    source: str | None
    updated_at: str | None

    @property
    def sensitivity_mean(self) -> float:
        return beta_mean(self.sensitivity_alpha, self.sensitivity_beta)

    @property
    def specificity_mean(self) -> float:
        return beta_mean(self.specificity_alpha, self.specificity_beta)

    def sensitivity_lb(self, q: float = 0.25) -> float:
        return beta_quantile(q, self.sensitivity_alpha, self.sensitivity_beta)

    def specificity_lb(self, q: float = 0.25) -> float:
        return beta_quantile(q, self.specificity_alpha, self.specificity_beta)

    @property
    def youden_j(self) -> float:
        """Discrimination power J = E[sens] + E[spec] - 1."""
        return self.sensitivity_mean + self.specificity_mean - 1.0

    def youden_j_lb(self, q: float = 0.25) -> float:
        """Conservative J from the sensitivity/specificity lower bounds."""
        return self.sensitivity_lb(q) + self.specificity_lb(q) - 1.0


def _active_error(row: sqlite3.Row | Mapping[str, Any]) -> ActiveErrorEvent:
    """An :class:`ActiveErrorEvent` from a stored row or a decoded (overlaid) one."""

    keys = row.keys()
    return ActiveErrorEvent(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        error_type=row["error_type"],
        severity=row["severity"],
        is_misconception=bool(row["is_misconception"]),
        created_at=row["created_at"],
        misconception_id=row["misconception_id"] if "misconception_id" in keys else None,
        misconception_statement=row["misconception_statement"] if "misconception_statement" in keys else None,
        attempt_id=(str(row["attempt_id"]) if row["attempt_id"] is not None else None) if "attempt_id" in keys else None,
    )


def _decode_hypothesis_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["response_payload"] = _loads(payload.pop("response_payload_json"), None)
    return payload


def _decode_misconception(row: sqlite3.Row) -> MisconceptionRecord:
    lifecycle_disposition = _row_opt(row, "lifecycle_disposition")
    return MisconceptionRecord(
        id=row["id"],
        learning_object_id=row["learning_object_id"],
        concept_id=row["concept_id"],
        statement=row["statement"],
        signature=row["signature"],
        facet_ids=_loads(row["facet_ids_json"], []),
        severity=row["severity"],
        status=lifecycle_disposition or row["status"],
        source_error_event_ids=_loads(row["source_error_event_ids_json"], []),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        resolved_at=row["resolved_at"],
        mechanism=_row_opt(row, "mechanism"),
        operation=_row_opt(row, "operation"),
        target_facet=_row_opt(row, "target_facet"),
        confused_with_facet=_row_opt(row, "confused_with_facet"),
        trigger_conditions=_loads(_row_opt(row, "trigger_conditions_json"), []),
        expected_signatures=_loads(_row_opt(row, "expected_signatures_json"), []),
        first_divergence=_loads(_row_opt(row, "first_divergence_json"), []),
        non_applicable_controls=_loads(_row_opt(row, "non_applicable_controls_json"), []),
        promotion_reason=_row_opt(row, "promotion_reason"),
        correction_statement=_row_opt(row, "correction_statement"),
        correction_source_span_ids=_loads(
            _row_opt(row, "correction_source_span_ids_json"), []
        ),
        lifecycle_disposition=lifecycle_disposition,
    )


def _row_opt(row: sqlite3.Row, key: str) -> Any:
    """Row value for ``key`` or ``None`` when the column is absent.

    Tolerates rows produced before migration 047 (KM4 additive columns).
    """

    try:
        return row[key]
    except (IndexError, KeyError):
        return None


def _decode_discrimination(row: sqlite3.Row) -> ItemMisconceptionDiscrimination:
    return ItemMisconceptionDiscrimination(
        practice_item_id=row["practice_item_id"],
        misconception_id=row["misconception_id"],
        sensitivity_alpha=row["sensitivity_alpha"],
        sensitivity_beta=row["sensitivity_beta"],
        specificity_alpha=row["specificity_alpha"],
        specificity_beta=row["specificity_beta"],
        n_planted_trials=row["n_planted_trials"],
        n_clean_trials=row["n_clean_trials"],
        source=row["source"],
        updated_at=row["updated_at"],
    )


class LearnerModelStoreMixin:

    def active_error_events(self) -> list[ActiveErrorEvent]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM error_events WHERE status = 'active' ORDER BY created_at DESC"
            ).fetchall()
        return [_active_error(row) for row in rows]

    def active_errors_by_learning_object(self, learning_object_id: str) -> list[ActiveErrorEvent]:
        """The LO's active error events exactly as stored (no diagnosis overlay).

        Serving, scheduling and replay read this. Under the Slice 1 split a
        blind-graded event's causal fields (misconception statement, the
        diagnoser's misconception verdict) are empty here; a display surface
        (and mvp-0.21's probe hypothesis lane) reads
        :meth:`active_errors_by_learning_object_overlaid` instead.
        """

        return [_active_error(row) for row in self._active_error_rows(learning_object_id)]

    def active_errors_by_learning_object_overlaid(self, learning_object_id: str) -> list[ActiveErrorEvent]:
        """The LO's active error events as the diagnosis overlay shows them.

        The per-LO counterpart of :meth:`error_events_for_attempt`: each event of
        a blind-graded attempt whose live diagnosis is in force gets the
        diagnosis's causal fields (``misconception_statement``,
        ``is_misconception``); the grader-owned ones (id, error type,
        severity, timestamps) and the order are unchanged. Events of joint
        grades, of attempts whose diagnosis is pending, failed or superseded,
        and events with no attempt are returned as stored, so a joint-graded
        vault reads exactly what :meth:`active_errors_by_learning_object` reads.

        Display (the Reader Guide, the TUI feedback screen) and, from mvp-0.21
        behind ``diagnosis.probe_lane_reads_diagnosis``, the probe hypothesis
        lane's serving read. Replay never reads it.
        """

        events = [_decode_error_event(row) for row in self._active_error_rows(learning_object_id)]
        views = self.live_causal_views(event.get("attempt_id") for event in events)
        if views:
            overlaid: list[dict[str, Any]] = []
            for event in events:
                view = views.get(str(event.get("attempt_id") or ""))
                if view is None:
                    overlaid.append(event)
                else:
                    overlaid.extend(merge_causal_view_into_events([event], view[1], diagnosis_id=view[0]))
            events = overlaid
        return [_active_error(event) for event in events]

    def active_error_events_overlaid(self) -> list[ActiveErrorEvent]:
        """Every active error event as the diagnosis overlay shows it.

        The all-LO counterpart of :meth:`active_errors_by_learning_object_overlaid`
        (same rule: a blind-graded event whose live diagnosis is in force gets
        the diagnosis's causal fields; everything else is returned as stored, in
        :meth:`active_error_events`'s order). Read by mvp-0.21's neighbour
        probe lane, the ``learnloop misconceptions`` listing and the
        ``decision_features`` receipt; replay never reads it.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM error_events WHERE status = 'active' ORDER BY created_at DESC"
            ).fetchall()
        events = [_decode_error_event(row) for row in rows]
        views = self.live_causal_views(event.get("attempt_id") for event in events)
        if views:
            overlaid: list[dict[str, Any]] = []
            for event in events:
                view = views.get(str(event.get("attempt_id") or ""))
                if view is None:
                    overlaid.append(event)
                else:
                    overlaid.extend(merge_causal_view_into_events([event], view[1], diagnosis_id=view[0]))
            events = overlaid
        return [_active_error(event) for event in events]

    def _active_error_rows(self, learning_object_id: str) -> list[sqlite3.Row]:
        with self.connection() as connection:
            return connection.execute(
                """
                SELECT * FROM error_events
                WHERE status = 'active' AND learning_object_id = ?
                ORDER BY created_at DESC
                """,
                (learning_object_id,),
            ).fetchall()

    def error_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        """The attempt's error events, as the causal consumers read them.

        Slice 1 M2 (spec §6.3): a blind-graded attempt's events carry only the
        grader's localization; once its live diagnosis completes, the causal
        fields (candidate causes, misconception statement, operation,
        postdictive claims, registry match) are laid over them from the
        diagnosis's stored causal view. Joint-graded events are returned as
        stored. Replay snapshots :meth:`raw_error_events_for_attempt` instead,
        so a rebuild rewrites exactly what was recorded.
        """

        events = self.raw_error_events_for_attempt(attempt_id)
        if not events:
            return events
        view = self.live_causal_view(attempt_id)
        if view is None:
            return events
        return merge_causal_view_into_events(events, view[1], diagnosis_id=view[0])

    def raw_error_events_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]:
        """The persisted error-event rows exactly as written (no overlay)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM error_events
                WHERE attempt_id = ?
                ORDER BY created_at, id
                """,
                (attempt_id,),
            ).fetchall()
        return [_decode_error_event(row) for row in rows]

    def all_error_events_by_attempt(self) -> dict[str, list[dict[str, Any]]]:
        """Decode the complete error-event ledger in one ordered scan.

        Whole-vault projections already replay every attempt, so issuing one
        indexed lookup from inside that fold turns a rebuild into an N+1 query
        path. This bulk shape preserves the per-attempt ordering of
        :meth:`error_events_for_attempt` while making the read cost constant,
        and applies the same diagnosis overlay.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM error_events
                ORDER BY attempt_id, created_at, id
                """
            ).fetchall()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row["attempt_id"])].append(_decode_error_event(row))
        views = self.live_causal_views()
        for attempt_id, (diagnosis_id, view) in views.items():
            if attempt_id in grouped:
                grouped[attempt_id] = merge_causal_view_into_events(
                    grouped[attempt_id], view, diagnosis_id=diagnosis_id
                )
        return dict(grouped)

    def attempt_ids_for_misconception(
        self,
        misconception_id: str,
        *,
        event_ids: Sequence[str] = (),
        limit: int = 5,
    ) -> list[str]:
        """Attempt ids whose error events minted/fed this misconception, newest first.

        ``event_ids`` widens the match to the misconception record's own
        ``source_error_event_ids`` provenance, because legacy events predate the
        ``misconception_id`` backlink. The §6.2 cold-verification context uses
        this as its case-level fallback: a clean primed attempt has no diagnosis
        receipt of its own, but the attempts that DIAGNOSED the misconception
        do, and their receipts carry the selected repair class."""

        ids = [str(value) for value in event_ids if value]
        clause = "misconception_id = ?"
        params: list[Any] = [misconception_id]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            clause = f"(misconception_id = ? OR id IN ({placeholders}))"
            params.extend(ids)
        params.append(max(1, limit))
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT attempt_id, MAX(created_at) AS last_at FROM error_events
                WHERE {clause} AND attempt_id IS NOT NULL
                GROUP BY attempt_id
                ORDER BY last_at DESC, attempt_id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [str(row["attempt_id"]) for row in rows]

    def insert_error_event(self, event: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._insert_error_event(connection, event)
            connection.commit()

    def set_error_event_misconception(
        self,
        event_id: str,
        misconception_id: str | None,
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Link (or unlink) an error event to a normalized registry belief."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE error_events SET misconception_id = ?, updated_at = ? WHERE id = ?",
                (misconception_id, now, event_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    # -- Misconception registry (spec §1.1) ---------------------------------

    def insert_misconception(
        self,
        *,
        learning_object_id: str,
        statement: str,
        id: str | None = None,
        concept_id: str | None = None,
        signature: str | None = None,
        facet_ids: Iterable[str] | None = None,
        severity: float = 0.0,
        status: str = "active",
        source_error_event_ids: Iterable[str] | None = None,
        mechanism: str | None = None,
        operation: str | None = None,
        target_facet: str | None = None,
        confused_with_facet: str | None = None,
        trigger_conditions: Iterable[str] | None = None,
        expected_signatures: Iterable[str] | None = None,
        first_divergence: Iterable[str] | None = None,
        non_applicable_controls: Iterable[str] | None = None,
        promotion_reason: str | None = None,
        correction_statement: str | None = None,
        correction_source_span_ids: Iterable[str] | None = None,
        provenance: Any = None,
        correction_provenance: Any = None,
        provenance_writer: str = "misconception",
        clock: Clock | None = None,
    ) -> str:
        """Insert a registry belief. ``provenance`` / ``correction_provenance``
        (``db.stores.write_provenance.WriteRecord``) record what the statement
        and the correction were written from, in this transaction (diagnosis
        input provenance); without one that text stays held back from chat."""

        if status not in {"active", "resolving", "resolved"}:
            raise ValueError("status must be one of active, resolving, resolved")
        misconception_id = id or new_ulid()
        now = utc_now_iso(clock)
        resolved_at = now if status == "resolved" else None
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO misconceptions(
                  id, learning_object_id, concept_id, statement, signature,
                  facet_ids_json, severity, status, source_error_event_ids_json,
                  created_at, updated_at, resolved_at,
                  mechanism, operation, target_facet, confused_with_facet,
                  trigger_conditions_json, expected_signatures_json,
                  first_divergence_json, non_applicable_controls_json,
                  promotion_reason, correction_statement,
                  correction_source_span_ids_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    misconception_id,
                    learning_object_id,
                    concept_id,
                    statement,
                    signature,
                    _json(sorted({str(f) for f in (facet_ids or [])})),
                    float(severity),
                    status,
                    _json([str(e) for e in (source_error_event_ids or [])]),
                    now,
                    now,
                    resolved_at,
                    mechanism,
                    operation,
                    target_facet,
                    confused_with_facet,
                    _json([str(t) for t in (trigger_conditions or [])]),
                    _json([str(s) for s in (expected_signatures or [])]),
                    _json([str(d) for d in (first_divergence or [])]),
                    _json([str(c) for c in (non_applicable_controls or [])]),
                    promotion_reason,
                    correction_statement,
                    _json([str(span) for span in (correction_source_span_ids or [])]),
                ),
            )
            connection.execute(
                """
                INSERT INTO misconception_transition_events(
                  id, misconception_id, from_status, to_status, at, source
                ) VALUES (?, ?, NULL, ?, ?, 'created')
                """,
                (new_ulid(), misconception_id, status, now),
            )
            self._record_text_provenance(
                connection, "misconception", misconception_id, statement, provenance, provenance_writer, clock)
            if correction_statement is not None:
                self._record_text_provenance(
                    connection, "misconception_correction", misconception_id, correction_statement,
                    correction_provenance, f"{provenance_writer}_correction", clock)
            connection.commit()
        return misconception_id

    def misconception(self, misconception_id: str) -> MisconceptionRecord | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT m.*, (
                  SELECT d.disposition
                  FROM misconception_disposition_events d
                  WHERE d.misconception_id = m.id
                  ORDER BY d.created_at DESC, d.id DESC
                  LIMIT 1
                ) AS lifecycle_disposition
                FROM misconceptions m
                WHERE m.id = ?
                """,
                (misconception_id,),
            ).fetchone()
        return _decode_misconception(row) if row is not None else None

    def misconceptions_for_learning_object(
        self,
        learning_object_id: str,
        statuses: Iterable[str] = ("active", "resolving"),
    ) -> list[MisconceptionRecord]:
        status_list = list(statuses)
        placeholders = ",".join("?" for _ in status_list) or "''"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT m.*, (
                  SELECT d.disposition
                  FROM misconception_disposition_events d
                  WHERE d.misconception_id = m.id
                  ORDER BY d.created_at DESC, d.id DESC
                  LIMIT 1
                ) AS lifecycle_disposition
                FROM misconceptions m
                WHERE m.learning_object_id = ?
                  AND COALESCE((
                    SELECT d.disposition
                    FROM misconception_disposition_events d
                    WHERE d.misconception_id = m.id
                    ORDER BY d.created_at DESC, d.id DESC
                    LIMIT 1
                  ), m.status) IN ({placeholders})
                ORDER BY m.created_at DESC, m.id DESC
                """,
                (learning_object_id, *status_list),
            ).fetchall()
        return [_decode_misconception(row) for row in rows]

    def misconceptions_for_concepts(
        self,
        concept_ids: Iterable[str],
        statuses: Iterable[str] = ("active", "resolving"),
    ) -> list[MisconceptionRecord]:
        concept_list = [str(c) for c in concept_ids]
        status_list = list(statuses)
        if not concept_list:
            return []
        concept_placeholders = ",".join("?" for _ in concept_list)
        status_placeholders = ",".join("?" for _ in status_list) or "''"
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT m.*, (
                  SELECT d.disposition
                  FROM misconception_disposition_events d
                  WHERE d.misconception_id = m.id
                  ORDER BY d.created_at DESC, d.id DESC
                  LIMIT 1
                ) AS lifecycle_disposition
                FROM misconceptions m
                WHERE m.concept_id IN ({concept_placeholders})
                  AND COALESCE((
                    SELECT d.disposition
                    FROM misconception_disposition_events d
                    WHERE d.misconception_id = m.id
                    ORDER BY d.created_at DESC, d.id DESC
                    LIMIT 1
                  ), m.status) IN ({status_placeholders})
                ORDER BY m.created_at DESC, m.id DESC
                """,
                (*concept_list, *status_list),
            ).fetchall()
        return [_decode_misconception(row) for row in rows]

    def update_misconception(
        self,
        misconception_id: str,
        *,
        statement: str | None = None,
        signature: str | None = None,
        facet_ids: Iterable[str] | None = None,
        severity: float | None = None,
        status: str | None = None,
        append_source_error_event_ids: Iterable[str] | None = None,
        correction_statement: str | None = None,
        correction_source_span_ids: Iterable[str] | None = None,
        transition_source: str = "repository",
        statement_provenance: Any = None,
        correction_provenance: Any = None,
        clock: Clock | None = None,
    ) -> MisconceptionRecord | None:
        if status is not None and status not in {"active", "resolving", "resolved"}:
            raise ValueError("status must be one of active, resolving, resolved")
        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconceptions WHERE id = ?",
                (misconception_id,),
            ).fetchone()
            if row is None:
                return None
            current = _decode_misconception(row)
            current_storage_status = str(row["status"])
            new_statement = statement if statement is not None else current.statement
            new_signature = signature if signature is not None else current.signature
            new_facets = (
                sorted({str(f) for f in facet_ids})
                if facet_ids is not None
                else current.facet_ids
            )
            new_severity = float(severity) if severity is not None else current.severity
            new_status = status if status is not None else current_storage_status
            new_correction = (
                correction_statement
                if correction_statement is not None
                else current.correction_statement
            )
            new_correction_spans = (
                [str(span) for span in correction_source_span_ids]
                if correction_source_span_ids is not None
                else current.correction_source_span_ids
            )
            source_ids = list(current.source_error_event_ids)
            if append_source_error_event_ids:
                for event_id in append_source_error_event_ids:
                    if event_id not in source_ids:
                        source_ids.append(str(event_id))
            # Resolution stamps resolved_at; any reactivation clears it.
            if new_status == "resolved":
                resolved_at = current.resolved_at or now
            else:
                resolved_at = None
            connection.execute(
                """
                UPDATE misconceptions
                SET statement = ?, signature = ?, facet_ids_json = ?, severity = ?,
                    status = ?, source_error_event_ids_json = ?, updated_at = ?,
                    resolved_at = ?, correction_statement = ?,
                    correction_source_span_ids_json = ?
                WHERE id = ?
                """,
                (
                    new_statement,
                    new_signature,
                    _json(new_facets),
                    new_severity,
                    new_status,
                    _json(source_ids),
                    now,
                    resolved_at,
                    new_correction,
                    _json(new_correction_spans),
                    misconception_id,
                ),
            )
            if new_status != current_storage_status:
                connection.execute(
                    """
                    INSERT INTO misconception_transition_events(
                      id, misconception_id, from_status, to_status, at, source
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(), misconception_id, current_storage_status,
                        new_status, now, transition_source,
                    ),
                )
            # A rewritten statement or correction records what it was written
            # from; one rewritten without a record no longer matches the text
            # its earlier record covers, so it is held back (fail closed).
            if statement is not None and statement != current.statement:
                self._record_text_provenance(connection, "misconception", misconception_id, new_statement,
                                             statement_provenance, f"{transition_source}_statement", clock)
            if correction_statement is not None and correction_statement != current.correction_statement:
                self._record_text_provenance(connection, "misconception_correction", misconception_id,
                                             new_correction, correction_provenance,
                                             f"{transition_source}_correction", clock)
            connection.commit()
        return self.misconception(misconception_id)

    def misconception_transition_events(self, misconception_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM misconception_transition_events
                WHERE misconception_id = ? ORDER BY at, rowid
                """,
                (misconception_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_misconception_candidate(
        self,
        *,
        learning_object_id: str,
        statement: str,
        statement_normalized: str,
        id: str | None = None,
        concept_id: str | None = None,
        signature: str | None = None,
        mechanism: str | None = None,
        operation: str | None = None,
        target_facet: str | None = None,
        confused_with_facet: str | None = None,
        facet_ids: Iterable[str] | None = None,
        source_error_event_ids: Iterable[str] | None = None,
        surface_families: Iterable[str] | None = None,
        item_ids: Iterable[str] | None = None,
        occurrence_count: int = 1,
        severity: float = 0.0,
        provenance: Any = None,
        provenance_writer: str = "misconception_candidate",
        clock: Clock | None = None,
    ) -> str:
        """Insert a holding-pen candidate. ``provenance`` records what its
        statement was written from (diagnosis input provenance)."""

        candidate_id = id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO misconception_candidates(
                  id, learning_object_id, concept_id, statement, statement_normalized,
                  signature, mechanism, operation, target_facet, confused_with_facet,
                  facet_ids_json, source_error_event_ids_json, surface_families_json,
                  item_ids_json, occurrence_count, severity, status,
                  promoted_misconception_id, promotion_reason, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate', NULL, NULL, ?, ?)
                """,
                (
                    candidate_id,
                    learning_object_id,
                    concept_id,
                    statement,
                    statement_normalized,
                    signature,
                    mechanism,
                    operation,
                    target_facet,
                    confused_with_facet,
                    _json(sorted({str(f) for f in (facet_ids or [])})),
                    _json([str(e) for e in (source_error_event_ids or [])]),
                    _json(sorted({str(s) for s in (surface_families or [])})),
                    _json(sorted({str(i) for i in (item_ids or [])})),
                    int(occurrence_count),
                    float(severity),
                    now,
                    now,
                ),
            )
            self._record_text_provenance(connection, "candidate", candidate_id, statement, provenance,
                                         provenance_writer, clock)
            connection.commit()
        return candidate_id

    def misconception_candidate_by_id(self, candidate_id: str) -> dict[str, Any] | None:
        causal = self.causal_hypothesis(candidate_id)
        if causal is not None:
            return next(
                (
                    row
                    for row in self._projected_causal_candidates(
                        str(causal["learning_object_id"])
                    )
                    if candidate_id in row.get("causal_hypothesis_ids", [])
                ),
                None,
            )
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM misconception_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        return _decode_misconception_candidate(row) if row is not None else None

    # -- Item/misconception discrimination (spec §1.3) ----------------------

    def upsert_item_misconception_discrimination(
        self,
        row: ItemMisconceptionDiscrimination,
        *,
        clock: Clock | None = None,
    ) -> None:
        now = row.updated_at or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO item_misconception_discrimination(
                  practice_item_id, misconception_id,
                  sensitivity_alpha, sensitivity_beta,
                  specificity_alpha, specificity_beta,
                  n_planted_trials, n_clean_trials, source, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(practice_item_id, misconception_id) DO UPDATE SET
                  sensitivity_alpha = excluded.sensitivity_alpha,
                  sensitivity_beta = excluded.sensitivity_beta,
                  specificity_alpha = excluded.specificity_alpha,
                  specificity_beta = excluded.specificity_beta,
                  n_planted_trials = excluded.n_planted_trials,
                  n_clean_trials = excluded.n_clean_trials,
                  source = excluded.source,
                  updated_at = excluded.updated_at
                """,
                (
                    row.practice_item_id,
                    row.misconception_id,
                    row.sensitivity_alpha,
                    row.sensitivity_beta,
                    row.specificity_alpha,
                    row.specificity_beta,
                    row.n_planted_trials,
                    row.n_clean_trials,
                    row.source,
                    now,
                ),
            )
            connection.commit()

    def discrimination_row(
        self, practice_item_id: str, misconception_id: str
    ) -> ItemMisconceptionDiscrimination | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM item_misconception_discrimination
                WHERE practice_item_id = ? AND misconception_id = ?
                """,
                (practice_item_id, misconception_id),
            ).fetchone()
        return _decode_discrimination(row) if row is not None else None

    def resolve_error_event(self, event_id: str, *, clock: Clock | None = None) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE error_events
                SET status = 'resolved', updated_at = ?
                WHERE id = ? AND status = 'active'
                """,
                (now, event_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def pending_gap_need_for_facets(self, facet_ids: Iterable[str]) -> dict[str, Any] | None:
        """A pending tutor-gap need already targeting any of ``facet_ids``.

        Need-filing dedup (spec §4b): skip filing a new
        ``tutor_gap_declaration`` intervention_need when a pending one already
        covers one of the attributed facets. Returns the first matching need (by
        priority then age) or ``None``."""

        wanted = {str(facet) for facet in facet_ids}
        if not wanted:
            return None
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE status = 'pending' AND trigger_reason = 'tutor_gap_declaration'
                ORDER BY priority DESC, created_at
                """
            ).fetchall()
        for row in rows:
            targets = {str(facet) for facet in _loads(row["target_facets_json"], [])}
            if targets & wanted:
                return _decode_intervention_need(row)
        return None

    def append_attempt_diagnosis_receipt(
        self,
        attempt_id: str,
        receipt: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Append one immutable P1 decision snapshot to the attempt payload.

        ``attempt_debug_payloads`` is the deliberately reused receipt store from
        §6.2.  Replay may replace the surrounding derived debug trace, so this
        method restores the content-addressed receipt when needed; within one
        payload it never replaces a receipt carrying the same id with different
        content.
        """

        receipt_payload = dict(receipt)
        receipt_id = str(receipt_payload.get("id") or "")
        if not receipt_id:
            raise ValueError("diagnosis receipt requires an id")
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT payload_json, algorithm_version, created_at
                FROM attempt_debug_payloads
                WHERE attempt_id = ?
                """,
                (attempt_id,),
            ).fetchone()
            if row is None:
                raise ValueError("attempt debug payload does not exist")
            payload = _loads(row["payload_json"], {})
            attribution = payload.get("causal_attribution")
            if not isinstance(attribution, dict):
                attribution = {}
                payload["causal_attribution"] = attribution
            receipts = attribution.get("diagnosis_receipts")
            if not isinstance(receipts, list):
                receipts = []
            for existing in receipts:
                if not isinstance(existing, Mapping) or existing.get("id") != receipt_id:
                    continue
                if dict(existing) != receipt_payload:
                    raise ValueError(
                        f"diagnosis receipt {receipt_id} is immutable"
                    )
                attribution["diagnosis_receipt"] = dict(existing)
                connection.execute(
                    """
                    UPDATE attempt_debug_payloads
                       SET payload_json = ?
                     WHERE attempt_id = ?
                    """,
                    (_json(payload), attempt_id),
                )
                connection.commit()
                return dict(existing)
            receipts.append(receipt_payload)
            attribution["diagnosis_receipts"] = receipts
            attribution["diagnosis_receipt"] = receipt_payload
            connection.execute(
                """
                UPDATE attempt_debug_payloads
                   SET payload_json = ?
                 WHERE attempt_id = ?
                """,
                (_json(payload), attempt_id),
            )
            connection.commit()
        return receipt_payload

    def recent_surprise_signals(
        self, *, limit: int = 200, exclude_attempt_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Most recent attempt_surprise signal rows for quantile-threshold
        resolution (newest first)."""

        query = (
            "SELECT attempt_id, bayesian_surprise, surprise_direction, gate_diagnostics_json "
            "FROM attempt_surprise"
        )
        params: tuple[Any, ...] = ()
        if exclude_attempt_id is not None:
            query += " WHERE attempt_id != ?"
            params = (exclude_attempt_id,)
        query += " ORDER BY created_at DESC, attempt_id DESC LIMIT ?"
        params = (*params, limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "bayesian_surprise": row["bayesian_surprise"],
                "surprise_direction": row["surprise_direction"],
                "gate_diagnostics": _loads(row["gate_diagnostics_json"], None),
            }
            for row in rows
        ]

    def upsert_intervention_need(self, need: Mapping[str, Any]) -> str:
        now = str(need["updated_at"])
        target_facets = sorted({str(facet) for facet in need.get("target_facets", [])})
        desired_intent = str(need["desired_intent"])
        learning_object_id = str(need["learning_object_id"])
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE learning_object_id = ?
                  AND desired_intent = ?
                  AND target_facets_json = ?
                  AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (learning_object_id, desired_intent, _json(target_facets)),
            ).fetchone()
            if existing is not None:
                need_id = existing["id"]
                connection.execute(
                    """
                    UPDATE intervention_needs
                    SET attempt_id = ?, practice_item_id = ?, trigger_reason = ?,
                        error_types_json = ?, priority = ?, blocked_reason = ?,
                        candidate_requirements_json = ?, diagnostic_focus_json = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        need.get("attempt_id"),
                        need.get("practice_item_id"),
                        need["trigger_reason"],
                        _json(need.get("error_types", [])),
                        need.get("priority", 0.5),
                        need["blocked_reason"],
                        _json(need.get("candidate_requirements", {})),
                        _json(need.get("diagnostic_focus")) if need.get("diagnostic_focus") is not None else None,
                        now,
                        need_id,
                    ),
                )
            else:
                need_id = str(need.get("id") or new_ulid())
                connection.execute(
                    """
                    INSERT INTO intervention_needs(
                      id, attempt_id, learning_object_id, practice_item_id,
                      desired_intent, trigger_reason, target_facets_json,
                      error_types_json, priority, status, blocked_reason,
                      candidate_requirements_json, diagnostic_focus_json,
                      created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        need_id,
                        need.get("attempt_id"),
                        learning_object_id,
                        need.get("practice_item_id"),
                        desired_intent,
                        need["trigger_reason"],
                        _json(target_facets),
                        _json(need.get("error_types", [])),
                        need.get("priority", 0.5),
                        need.get("status", "pending"),
                        need["blocked_reason"],
                        _json(need.get("candidate_requirements", {})),
                        _json(need.get("diagnostic_focus")) if need.get("diagnostic_focus") is not None else None,
                        need.get("created_at", now),
                        now,
                    ),
                )
            connection.commit()
        return need_id

    def pending_intervention_needs(self, learning_object_id: str | None = None) -> list[dict[str, Any]]:
        clauses = ["status = 'pending'"]
        parameters: list[Any] = []
        if learning_object_id is not None:
            clauses.append("learning_object_id = ?")
            parameters.append(learning_object_id)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM intervention_needs
                WHERE {' AND '.join(clauses)}
                ORDER BY priority DESC, created_at
                """,
                parameters,
            ).fetchall()
        return [_decode_intervention_need(row) for row in rows]

    def intervention_need(self, need_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM intervention_needs WHERE id = ?",
                (need_id,),
            ).fetchone()
        return _decode_intervention_need(row) if row is not None else None

    def update_intervention_need_diagnostic_focus(
        self,
        need_id: str,
        diagnostic_focus: dict[str, Any] | None,
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Replace a need's diagnostic_focus snapshot in place (spec §6 reopen).

        Used to attach the sim gate's ``last_gate_result`` estimates when a
        generated diagnostic is rejected, so the next generation round sees why
        the previous item failed. A direct UPDATE (not upsert) to avoid changing
        the upsert dedup key."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE intervention_needs SET diagnostic_focus_json = ?, updated_at = ? WHERE id = ?",
                (
                    _json(diagnostic_focus) if diagnostic_focus is not None else None,
                    utc_now_iso(clock),
                    need_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def intervention_need_for_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE attempt_id = ?
                ORDER BY updated_at DESC, created_at DESC, id DESC
                LIMIT 1
                """,
                (attempt_id,),
            ).fetchone()
        return _decode_intervention_need(row) if row is not None else None

    def update_intervention_need_status(
        self,
        need_id: str,
        *,
        status: str,
        blocked_reason: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        if status not in {"pending", "fulfilled", "dismissed", "stale"}:
            raise ValueError("status must be one of pending, fulfilled, dismissed, stale")
        now = utc_now_iso(clock)
        assignments = ["status = ?", "updated_at = ?"]
        parameters: list[Any] = [status, now]
        if blocked_reason is not None:
            assignments.append("blocked_reason = ?")
            parameters.append(blocked_reason)
        parameters.append(need_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE intervention_needs SET {', '.join(assignments)} WHERE id = ?",
                parameters,
            )
            connection.commit()
            return cursor.rowcount > 0

    def append_intervention_need_target_facets(
        self,
        need_id: str,
        facets: list[str],
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Union extra facets into an existing need's target_facets in place.

        A direct UPDATE (not upsert): changing target_facets would change the
        upsert dedup key and spawn a duplicate pending need."""

        if not facets:
            return False
        with self.connection() as connection:
            row = connection.execute(
                "SELECT target_facets_json FROM intervention_needs WHERE id = ?",
                (need_id,),
            ).fetchone()
            if row is None:
                return False
            existing = {str(facet) for facet in _loads(row["target_facets_json"], [])}
            merged = sorted(existing | {str(facet) for facet in facets})
            if merged == sorted(existing):
                return False
            cursor = connection.execute(
                "UPDATE intervention_needs SET target_facets_json = ?, updated_at = ? WHERE id = ?",
                (_json(merged), utc_now_iso(clock), need_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def intervention_needs_for_diagnostic_proposal(self, patch_id: str) -> list[dict[str, Any]]:
        prefix = f"diagnostic_proposal_queued:{patch_id}"
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM intervention_needs
                WHERE status = 'fulfilled'
                  AND (blocked_reason = ? OR blocked_reason LIKE ?)
                ORDER BY created_at, id
                """,
                (prefix, f"{prefix}:%"),
            ).fetchall()
        return [_decode_intervention_need(row) for row in rows]

    def upsert_state_belief(
        self,
        *,
        scope_type: str,
        scope_id: str,
        belief_key: str,
        mean: float,
        variance: float,
        evidence_count: int,
        algorithm_version: str,
        subject: str | None = None,
        last_surprise: float | None = None,
        last_evidence_at: str | None = None,
        stale_after_days: int | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert or update a `learner_state_beliefs` row.

        Keyed by the table's unique scope `(subject, scope_type, scope_id,
        belief_key)`. Done as an explicit select/update to avoid relying on an
        `ON CONFLICT` target over the COALESCE-based expression index.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM learner_state_beliefs
                WHERE COALESCE(subject, '') = COALESCE(?, '')
                  AND scope_type = ? AND scope_id = ? AND belief_key = ?
                """,
                (subject, scope_type, scope_id, belief_key),
            ).fetchone()
            if existing is not None:
                belief_id = existing["id"]
                connection.execute(
                    """
                    UPDATE learner_state_beliefs
                    SET mean = ?, variance = ?, evidence_count = ?, last_surprise = ?,
                        last_evidence_at = ?, stale_after_days = ?, algorithm_version = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        mean,
                        variance,
                        evidence_count,
                        last_surprise,
                        last_evidence_at,
                        stale_after_days,
                        algorithm_version,
                        now,
                        belief_id,
                    ),
                )
            else:
                belief_id = new_ulid()
                connection.execute(
                    """
                    INSERT INTO learner_state_beliefs(
                      id, subject, scope_type, scope_id, belief_key, mean, variance,
                      evidence_count, last_surprise, last_evidence_at, stale_after_days,
                      algorithm_version, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        belief_id,
                        subject,
                        scope_type,
                        scope_id,
                        belief_key,
                        mean,
                        variance,
                        evidence_count,
                        last_surprise,
                        last_evidence_at,
                        stale_after_days,
                        algorithm_version,
                        now,
                    ),
                )
            connection.commit()
        return belief_id

    def state_beliefs(
        self,
        *,
        subject: str | None = None,
        scope_type: str | None = None,
        scope_id: str | None = None,
        belief_key: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("subject", subject),
            ("scope_type", scope_type),
            ("scope_id", scope_id),
            ("belief_key", belief_key),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM learner_state_beliefs{where} ORDER BY updated_at DESC, id",
                parameters,
            ).fetchall()
        return [dict(row) for row in rows]

    def all_scheduler_slates(self) -> list[dict[str, Any]]:
        """Every scheduler slate in chronological order (for shadow reports)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM scheduler_slates ORDER BY generated_at ASC, id ASC"
            ).fetchall()
        return [_decode_scheduler_slate(row) for row in rows]

    def misconception_transition_counts_between(
        self, started_at: str, ended_at: str
    ) -> dict[str, int]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT from_status, to_status
                FROM misconception_transition_events
                WHERE at >= ? AND at <= ?
                """,
                (started_at, ended_at),
            ).fetchall()
        return {
            "resolved": sum(row["to_status"] == "resolved" for row in rows),
            "returned": sum(
                row["from_status"] == "resolved"
                and row["to_status"] in {"active", "resolving"}
                for row in rows
            ),
        }

    # -- Typed learner-facing hypothesis events ---------------------------

    def insert_hypothesis_event(
        self,
        *,
        event_type: str,
        claim_class: str,
        claim_type: str,
        claim_ref: str,
        claim_version: str,
        producer_version: str,
        surface: str,
        temperature: str,
        presentation_id: str | None = None,
        visible_at: str | None = None,
        suppression_reason: str | None = None,
        response_payload: Mapping[str, Any] | None = None,
        session_id: str | None = None,
        visit_id: str | None = None,
        claim_text: str | None = None,
        belief_kind: str | None = None,
        belief_id: str | None = None,
        surfaced_to_learner: bool = False,
        id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        event_id = id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO hypothesis_events(
                  id, created_at, presentation_id, event_type, claim_class,
                  claim_type, claim_ref, claim_version, producer_version,
                  surface, temperature, visible_at, suppression_reason,
                  response_payload_json, session_id, visit_id,
                  claim_text_as_shown, belief_kind, belief_id,
                  surfaced_to_learner
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    now,
                    presentation_id,
                    event_type,
                    claim_class,
                    claim_type,
                    claim_ref,
                    claim_version,
                    producer_version,
                    surface,
                    temperature,
                    visible_at,
                    suppression_reason,
                    _json(dict(response_payload)) if response_payload is not None else None,
                    session_id,
                    visit_id,
                    claim_text,
                    belief_kind,
                    belief_id,
                    1 if surfaced_to_learner else 0,
                ),
            )
            connection.commit()
        event = self.hypothesis_event(event_id)
        assert event is not None
        return event

    def hypothesis_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM hypothesis_events WHERE id = ?", (event_id,)
            ).fetchone()
        return _decode_hypothesis_event(row) if row is not None else None

    def find_hypothesis_presentation(
        self,
        *,
        claim_ref: str,
        claim_version: str,
        surface: str,
        session_id: str | None,
        visit_id: str | None,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM hypothesis_events
                WHERE event_type = 'presented'
                  AND claim_ref = ? AND claim_version = ? AND surface = ?
                  AND COALESCE(session_id, '') = COALESCE(?, '')
                  AND COALESCE(visit_id, '') = COALESCE(?, '')
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (claim_ref, claim_version, surface, session_id, visit_id),
            ).fetchone()
        return _decode_hypothesis_event(row) if row is not None else None

    def mark_hypothesis_visible(
        self,
        presentation_id: str,
        visible_at: str,
        *,
        claim_text: str | None = None,
        belief_kind: str | None = None,
        belief_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Patch actual viewport exposure onto a debounced presentation.

        Every write is ``COALESCE``-guarded, so this is idempotent and safe on a
        read path: the FIRST exposure timestamp and the FIRST as-shown wording
        win forever (A6 quotes what the learner saw, not the latest rewrite).
        ``surfaced_to_learner`` flips only for an unsuppressed row that is now
        known-visible — a card the attention budget swallowed was authored, not
        shown, and must never trigger an apology.
        """

        with self.connection() as connection:
            connection.execute(
                """
                UPDATE hypothesis_events
                SET visible_at = COALESCE(visible_at, ?),
                    claim_text_as_shown = COALESCE(claim_text_as_shown, ?),
                    belief_kind = COALESCE(belief_kind, ?),
                    belief_id = COALESCE(belief_id, ?),
                    surfaced_to_learner = CASE
                      WHEN suppression_reason IS NULL
                        AND COALESCE(visible_at, ?) IS NOT NULL THEN 1
                      ELSE surfaced_to_learner
                    END
                WHERE id = ? AND event_type = 'presented'
                """,
                (
                    visible_at,
                    claim_text,
                    belief_kind,
                    belief_id,
                    visible_at,
                    presentation_id,
                ),
            )
            connection.commit()
        return self.hypothesis_event(presentation_id)

    def soliciting_hypothesis_count(
        self, *, session_id: str | None = None, visit_id: str | None = None
    ) -> int:
        if session_id is None and visit_id is None:
            return 0
        column = "session_id" if session_id is not None else "visit_id"
        value = session_id if session_id is not None else visit_id
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT COUNT(*) AS n FROM hypothesis_events
                WHERE event_type = 'presented'
                  AND suppression_reason IS NULL
                  AND {column} = ?
                """,
                (value,),
            ).fetchone()
        return int(row["n"] if row is not None else 0)

    def cold_hypothesis_count_for_visit(self, visit_id: str) -> int:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS n FROM hypothesis_events
                WHERE event_type = 'presented' AND visit_id = ?
                  AND temperature = 'cold' AND suppression_reason IS NULL
                """,
                (visit_id,),
            ).fetchone()
        return int(row["n"] if row is not None else 0)

    def last_hypothesis_response_at(self, claim_ref: str, claim_version: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT created_at FROM hypothesis_events
                WHERE event_type = 'responded'
                  AND claim_ref = ? AND claim_version = ?
                ORDER BY created_at DESC, id DESC LIMIT 1
                """,
                (claim_ref, claim_version),
            ).fetchone()
        return str(row["created_at"]) if row is not None else None

    def list_hypothesis_events(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM hypothesis_events ORDER BY created_at, id"
            ).fetchall()
        return [_decode_hypothesis_event(row) for row in rows]

    def purge_hypothesis_events(self) -> int:
        with self.connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS n FROM hypothesis_events").fetchone()
            count = int(row["n"] if row is not None else 0)
            connection.execute("DELETE FROM hypothesis_events")
            connection.commit()
        return count

    # -- A6 surfaced-belief withdrawals (migration 132) --------------------

    def record_surfaced_belief_presentation(
        self,
        *,
        id: str,
        belief_kind: str,
        belief_id: str,
        claim_text: str,
        surface: str,
        claim_class: str = "diagnosis",
        claim_type: str = "misconception",
        claim_version: str = "surfaced-1",
        producer_version: str = "surfaced_beliefs",
        clock: Clock | None = None,
    ) -> str:
        """Record a belief shown on a surface that does NOT dispatch claims.

        Most diagnoses reach the learner through ``present_claims`` (every Tauri
        ClaimSurface mount). Repair does not: ``handlers/remediation._case_dto``
        prints the belief statement directly, so without this the flag would be
        blind to the one screen whose entire job is that belief.

        ``INSERT OR IGNORE`` on a caller-supplied DETERMINISTIC id is what makes
        this safe on a read path: the surface is polled, and the second through
        n-th call are no-ops at one index probe. The first exposure timestamp
        therefore wins, which is the honest reading of "when the learner met this
        claim".
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO hypothesis_events(
                  id, created_at, presentation_id, event_type, claim_class,
                  claim_type, claim_ref, claim_version, producer_version,
                  surface, temperature, visible_at, suppression_reason,
                  response_payload_json, session_id, visit_id,
                  claim_text_as_shown, belief_kind, belief_id,
                  surfaced_to_learner
                )
                VALUES (
                  ?, ?, NULL, 'presented', ?, ?, ?, ?, ?, ?, 'cold', ?, NULL,
                  NULL, NULL, NULL, ?, ?, ?, 1
                )
                """,
                (
                    id,
                    now,
                    claim_class,
                    claim_type,
                    belief_id,
                    claim_version,
                    producer_version,
                    surface,
                    now,
                    claim_text,
                    belief_kind,
                    belief_id,
                ),
            )
            connection.commit()
        return id

    def insert_misconception_disposition(
        self,
        *,
        misconception_id: str,
        disposition: str,
        reason: str,
        replacement_misconception_id: str | None = None,
        id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one demotion/supersession to the append-only lifecycle stream.

        Migration 116 created the store and backfilled it, but nothing has ever
        WRITTEN to it from service code, so every demotion since has been
        invisible to the semantic authority. This is that writer. The typed
        withdrawal vocabulary lives in ``learnloop.learner.surfaced_beliefs``;
        this
        method stores what it is given and never invents a reason.
        """

        event_id = id or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO misconception_disposition_events(
                  id, misconception_id, disposition, reason, created_at,
                  replacement_misconception_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    misconception_id,
                    disposition,
                    reason,
                    now,
                    replacement_misconception_id,
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM misconception_disposition_events WHERE id = ?",
                (event_id,),
            ).fetchone()
        assert row is not None
        return dict(row)

    def misconception_dispositions(
        self, misconception_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if misconception_id is None:
                rows = connection.execute(
                    """
                    SELECT * FROM misconception_disposition_events
                    ORDER BY created_at, id
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM misconception_disposition_events
                    WHERE misconception_id = ?
                    ORDER BY created_at, id
                    """,
                    (misconception_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    def surfaced_beliefs(self) -> list[dict[str, Any]]:
        """Distinct beliefs the learner was actually SHOWN (migration 132).

        The denominator of `harmful_write_rate` (Aug §3 B5): a rate whose
        numerator is "surfaced beliefs later withdrawn as false" must divide by
        beliefs *surfaced*, not by diagnoses written, or it would fall whenever
        the system got chattier without getting more careful.

        Deduplicated on (kind, id) rather than counting presentations: a belief
        shown on five screens is one thing the learner was told once, and
        `surfaced_belief_withdrawals` already emits one row per disposition
        event regardless of exposure count. Rides the partial index from 132.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT belief_kind,
                       belief_id,
                       MIN(created_at) AS first_surfaced_at,
                       COUNT(*)        AS presentations
                FROM hypothesis_events
                WHERE surfaced_to_learner = 1
                  AND belief_kind IS NOT NULL
                  AND belief_id IS NOT NULL
                GROUP BY belief_kind, belief_id
                ORDER BY first_surfaced_at, belief_kind, belief_id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def surfaced_belief_withdrawals(self) -> list[dict[str, Any]]:
        """The A6 join: dispositions on beliefs the learner was actually SHOWN.

        One row per disposition event, and ONLY for beliefs with at least one
        ``surfaced_to_learner`` presentation dated at or before the disposition
        (migration 132). The scope guard is the WHERE clause: retiring a belief
        nobody saw yields no row at all, which is what keeps housekeeping out of
        the learner's feed.

        Correlated subqueries rather than a GROUP BY join because the projection
        needs THREE different aggregates over the same presentations — the first
        exposure (when the learner met the claim), and the wording plus surface
        of the LAST exposure before withdrawal (the words actually in their
        memory). All three ride the partial index from migration 132.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                  d.id                             AS disposition_event_id,
                  d.misconception_id               AS belief_id,
                  d.disposition                    AS disposition,
                  d.reason                         AS reason,
                  d.created_at                     AS at,
                  d.replacement_misconception_id   AS replacement_belief_id,
                  m.statement                      AS current_statement,
                  m.facet_ids_json                 AS facet_ids_json,
                  m.learning_object_id             AS learning_object_id,
                  r.statement                      AS replacement_statement,
                  (
                    SELECT MIN(h.created_at) FROM hypothesis_events h
                    WHERE h.belief_kind = 'misconception'
                      AND h.belief_id = d.misconception_id
                      AND h.surfaced_to_learner = 1
                      AND h.created_at <= d.created_at
                  ) AS first_surfaced_at,
                  (
                    SELECT h.claim_text_as_shown FROM hypothesis_events h
                    WHERE h.belief_kind = 'misconception'
                      AND h.belief_id = d.misconception_id
                      AND h.surfaced_to_learner = 1
                      AND h.created_at <= d.created_at
                      AND h.claim_text_as_shown IS NOT NULL
                    ORDER BY h.created_at DESC, h.id DESC LIMIT 1
                  ) AS claim_text_as_shown,
                  (
                    SELECT h.surface FROM hypothesis_events h
                    WHERE h.belief_kind = 'misconception'
                      AND h.belief_id = d.misconception_id
                      AND h.surfaced_to_learner = 1
                      AND h.created_at <= d.created_at
                    ORDER BY h.created_at DESC, h.id DESC LIMIT 1
                  ) AS last_surface
                FROM misconception_disposition_events d
                LEFT JOIN misconceptions m ON m.id = d.misconception_id
                LEFT JOIN misconceptions r ON r.id = d.replacement_misconception_id
                WHERE EXISTS (
                  SELECT 1 FROM hypothesis_events h
                  WHERE h.belief_kind = 'misconception'
                    AND h.belief_id = d.misconception_id
                    AND h.surfaced_to_learner = 1
                    AND h.created_at <= d.created_at
                )
                ORDER BY d.created_at, d.id
                """
            ).fetchall()
        withdrawals: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["facet_ids"] = [
                str(facet) for facet in _loads(payload.pop("facet_ids_json"), [])
            ]
            withdrawals.append(payload)
        return withdrawals

    def _insert_error_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO error_events(
              id, attempt_id, learning_object_id, error_type, severity,
              is_misconception, repair_plan_json, status, created_at, updated_at,
              misconception_id, misconception_statement, misconception_consistent_answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("id") or new_ulid(),
                event.get("attempt_id"),
                event["learning_object_id"],
                event["error_type"],
                event["severity"],
                1 if event.get("is_misconception") else 0,
                _json(event.get("repair_plan")) if event.get("repair_plan") is not None else None,
                event.get("status", "active"),
                event["created_at"],
                event.get("updated_at"),
                event.get("misconception_id"),
                event.get("misconception_statement"),
                event.get("misconception_consistent_answer"),
            ),
        )

    def golden_path_runs_all(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM golden_path_runs ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def discrimination_profile_match_rows(
        self, *, since: str | None = None
    ) -> list[dict[str, Any]]:
        """Every recorded A5 judgement, oldest first. ``since`` is ISO-8601."""

        clause = "WHERE created_at >= ?" if since is not None else ""
        values = (since,) if since is not None else ()
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM discrimination_profile_matches
                {clause}
                ORDER BY created_at, id
                """,
                values,
            ).fetchall()
        return [dict(row) for row in rows]

    def diagnostic_augmentation_receipt_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM diagnostic_augmentation_receipts
                ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_diagnostic_augmentation_receipt(row) for row in rows]
