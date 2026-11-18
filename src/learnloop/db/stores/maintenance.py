"""Maintenance notices and the parameter registry.

Owns notices, registry manifests, sensitivity certificates and parameter binds."""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


def _decode_maintenance_notice(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["detail"] = _loads(data.pop("detail_json", None), None)
    data["action"] = _loads(data.pop("action_json", None), {})
    return data


class MaintenanceStoreMixin:

    # ------------------------------------------------------------------
    # P0.5 parameter registry (migration 069). SQL-only; the definition and
    # projection logic live in ``learnloop.params.parameter_registry``.
    # ------------------------------------------------------------------

    def upsert_parameter_registry_entry(self, *, entry: dict[str, Any], clock: Clock | None = None) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_registry(
                  path, kind, param_class, effective_value_json, effective_value_hash,
                  source, status, lifecycle, rationale, scope, owner,
                  sensitivity_certificate_id, evidence_manifest_id, redundancy_proof_id,
                  promotion_evidence_id, last_review_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                  kind = excluded.kind,
                  param_class = excluded.param_class,
                  effective_value_json = excluded.effective_value_json,
                  effective_value_hash = excluded.effective_value_hash,
                  source = excluded.source,
                  status = excluded.status,
                  lifecycle = excluded.lifecycle,
                  rationale = excluded.rationale,
                  scope = excluded.scope,
                  owner = excluded.owner,
                  sensitivity_certificate_id = excluded.sensitivity_certificate_id,
                  evidence_manifest_id = excluded.evidence_manifest_id,
                  redundancy_proof_id = excluded.redundancy_proof_id,
                  promotion_evidence_id = excluded.promotion_evidence_id,
                  last_review_at = excluded.last_review_at,
                  updated_at = excluded.updated_at
                """,
                (
                    entry["path"],
                    entry["kind"],
                    entry["param_class"],
                    _json(entry["effective_value"]),
                    entry["effective_value_hash"],
                    entry["source"],
                    entry["status"],
                    entry["lifecycle"],
                    entry["rationale"],
                    entry["scope"],
                    entry["owner"],
                    entry.get("sensitivity_certificate_id"),
                    entry.get("evidence_manifest_id"),
                    entry.get("redundancy_proof_id"),
                    entry.get("promotion_evidence_id"),
                    entry.get("last_review_at"),
                    now,
                ),
            )
            connection.commit()

    def parameter_registry_entry(self, path: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM parameter_registry WHERE path = ?", (path,)
            ).fetchone()
        return dict(row) if row is not None else None

    def parameter_registry_entries(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_registry ORDER BY path"
            ).fetchall()
        return [dict(r) for r in rows]

    def insert_parameter_registry_manifest(
        self,
        *,
        algorithm_version: str,
        manifest_hash: str,
        entries: dict[str, Any],
        clock: Clock | None = None,
    ) -> str | None:
        """Freeze one immutable manifest per algorithm version. Idempotent: a
        second freeze of the same version is a no-op (returns None)."""

        manifest_id = new_ulid()
        frozen_at = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM parameter_registry_manifests WHERE algorithm_version = ?",
                (algorithm_version,),
            ).fetchone()
            if existing is not None:
                return None
            connection.execute(
                """
                INSERT INTO parameter_registry_manifests(
                  id, algorithm_version, manifest_hash, entries_json, frozen_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (manifest_id, algorithm_version, manifest_hash, _json(entries), frozen_at),
            )
            connection.commit()
        return manifest_id

    def parameter_registry_manifest(self, algorithm_version: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM parameter_registry_manifests WHERE algorithm_version = ?",
                (algorithm_version,),
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_sensitivity_certificate(self, *, certificate: dict[str, Any], clock: Clock | None = None) -> str:
        cert_id = certificate.get("id") or new_ulid()
        produced_at = certificate.get("produced_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_sensitivity_certificates(
                  id, path, covered_value_hash, plausible_range_json, flip_points_json,
                  decision_stable, scenario_json, sim_report_hash, produced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cert_id,
                    certificate["path"],
                    certificate["covered_value_hash"],
                    _json(certificate["plausible_range"]),
                    _json(certificate["flip_points"]),
                    1 if certificate["decision_stable"] else 0,
                    _json(certificate["scenario"]),
                    certificate["sim_report_hash"],
                    produced_at,
                ),
            )
            connection.commit()
        return cert_id

    def sensitivity_certificates_for_path(self, path: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_sensitivity_certificates WHERE path = ? ORDER BY produced_at DESC",
                (path,),
            ).fetchall()
        return [dict(r) for r in rows]

    def record_parameter_bind_event(
        self,
        *,
        path: str,
        bound_context: dict[str, Any],
        observation_ref: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        created_at = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO parameter_bind_events(
                  id, path, bound_context_json, observation_ref, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, path, _json(bound_context), observation_ref, created_at),
            )
            connection.commit()
        return event_id

    def parameter_bind_events_for_path(self, path: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM parameter_bind_events WHERE path = ? ORDER BY created_at",
                (path,),
            ).fetchall()
        return [dict(r) for r in rows]

    # --- maintenance feed (§11) --------------------------------------------

    def upsert_maintenance_notice(
        self,
        *,
        notice_type: str,
        dedup_key: str,
        title: str,
        action: Mapping[str, Any],
        aging_policy: str,
        severity: str = "info",
        subject_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        detail: Any = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert or refresh a notice (idempotent on ``(notice_type, dedup_key)``).

        A live notice keeps its id, snooze_count, and snoozed_until across
        regeneration; only ``last_seen_at`` (and severity/detail) refresh, so
        deterministic re-generation never duplicates or resets a notice."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM maintenance_notices WHERE notice_type = ? AND dedup_key = ?",
                (notice_type, dedup_key),
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE maintenance_notices
                       SET title = ?, action_json = ?, severity = ?, detail_json = ?,
                           last_seen_at = ?,
                           status = CASE WHEN status IN ('dismissed','resolved','expired','snoozed')
                                         THEN status ELSE 'active' END
                     WHERE id = ?
                    """,
                    (title, _json(action), severity, _json(detail), now, existing["id"]),
                )
                connection.commit()
                return existing["id"]
            row_id = new_ulid()
            connection.execute(
                """
                INSERT INTO maintenance_notices(
                  id, subject_id, notice_type, dedup_key, severity, aging_policy,
                  entity_type, entity_id, title, detail_json, action_json, status,
                  snooze_count, snoozed_until, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, NULL, ?, ?)
                """,
                (
                    row_id, subject_id, notice_type, dedup_key, severity, aging_policy,
                    entity_type, entity_id, title, _json(detail), _json(action), now, now,
                ),
            )
            connection.commit()
            return row_id

    def maintenance_notices(
        self, *, subject_id: str | None = None, include_hidden: bool = False
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM maintenance_notices"
        clauses: list[str] = []
        params: list[Any] = []
        if not include_hidden:
            clauses.append("status IN ('active', 'snoozed')")
        if subject_id is not None:
            clauses.append("(subject_id = ? OR subject_id IS NULL)")
            params.append(subject_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY severity DESC, first_seen_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [_decode_maintenance_notice(row) for row in rows]

    def maintenance_notice(self, notice_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM maintenance_notices WHERE id = ?", (notice_id,)
            ).fetchone()
        return _decode_maintenance_notice(row) if row else None

    def set_maintenance_notice_status(
        self,
        notice_id: str,
        *,
        status: str,
        snoozed_until: str | None = None,
        bump_snooze: bool = False,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                f"""
                UPDATE maintenance_notices
                   SET status = ?, snoozed_until = ?,
                       snooze_count = snooze_count + {1 if bump_snooze else 0},
                       resolved_at = CASE WHEN ? IN ('resolved','expired','dismissed') THEN ? ELSE resolved_at END
                 WHERE id = ?
                """,
                (status, snoozed_until, status, now, notice_id),
            )
            connection.commit()

    def resolve_maintenance_notice_if_detail(
        self, notice_id: str, *, detail_key: str, expected: Any, clock: Clock | None = None
    ) -> bool:
        """Resolve a live notice only while its stored ``detail[detail_key]``
        is still ``expected`` (one guarded statement: a write that changed the
        detail since the caller read it keeps the notice). Reader CA1's
        transcription reports resolve this way (Codex review F8). Returns
        whether it was resolved."""

        if not detail_key.isidentifier():
            raise ValueError(f"not a detail key: {detail_key!r}")
        now = utc_now_iso(clock)
        with self.connection() as connection:
            changed = connection.execute(
                f"""
                UPDATE maintenance_notices
                   SET status = 'resolved', resolved_at = ?
                 WHERE id = ? AND status IN ('active', 'snoozed')
                   AND json_extract(detail_json, '$.{detail_key}') IS ?
                """,
                (now, notice_id, expected),
            ).rowcount
            connection.commit()
        return bool(changed)
