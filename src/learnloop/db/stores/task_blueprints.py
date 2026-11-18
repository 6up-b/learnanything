"""Task blueprints and golden-path planning records.

Owns task blueprints, versions and review events; golden-path runs and events."""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.row_serialization import _json
from learnloop.ids import new_ulid


class TaskBlueprintStoreMixin:

    # ------------------------------------------------------------------
    # P2 golden path -- task blueprints (spec_p2 §3.2, migration 081)
    # ------------------------------------------------------------------

    def ensure_task_blueprint(
        self,
        *,
        blueprint_slug: str,
        source_rev: str,
        unit_id: str,
        family_key: str,
        clock: Clock | None = None,
    ) -> str:
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM task_blueprints WHERE blueprint_slug = ?",
                (blueprint_slug,),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            blueprint_id = new_ulid()
            connection.execute(
                """
                INSERT INTO task_blueprints(
                  id, blueprint_slug, source_rev, unit_id, family_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (blueprint_id, blueprint_slug, source_rev, unit_id, family_key, utc_now_iso(clock)),
            )
            connection.commit()
        return blueprint_id

    def register_task_blueprint_version(
        self,
        *,
        blueprint_id: str,
        spec_json: str,
        content_hash: str,
        canonical_hash: str,
        authoring_version: str,
        model_version: str | None,
        provenance_version: str,
        exemplars: Sequence[Mapping[str, Any]],
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Register an immutable, content-addressed draft blueprint version + its
        exemplar link rows + a ``registered`` review event, all in one transaction.
        Idempotent on ``UNIQUE(blueprint_id, content_hash)``."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE blueprint_id = ? AND content_hash = ?",
                (blueprint_id, content_hash),
            ).fetchone()
            if existing is not None:
                connection.execute("ROLLBACK")
                return {"version": dict(existing), "already_exists": True}
            versions = connection.execute(
                "SELECT version FROM task_blueprint_versions WHERE blueprint_id = ?",
                (blueprint_id,),
            ).fetchall()
            next_version = max((row["version"] for row in versions), default=0) + 1
            version_id = new_ulid()
            connection.execute(
                """
                INSERT INTO task_blueprint_versions(
                  id, blueprint_id, version, status, spec_json, content_hash,
                  canonical_hash, authoring_version, model_version, provenance_version,
                  reviewed_at, activated_at, created_at
                )
                VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    version_id, blueprint_id, next_version, spec_json, content_hash,
                    canonical_hash, authoring_version, model_version, provenance_version, now,
                ),
            )
            for exemplar in exemplars:
                connection.execute(
                    """
                    INSERT INTO target_exemplars(
                      id, blueprint_version_id, exemplar_ref, weight, exposure_status,
                      held_out_weight, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(), version_id, exemplar["exemplar_ref"],
                        float(exemplar.get("weight", 1.0)),
                        exemplar.get("exposure_status", "familiar_anchor"),
                        float(exemplar.get("held_out_weight", 0.0)), now,
                    ),
                )
            connection.execute(
                """
                INSERT INTO task_blueprint_review_events(
                  id, blueprint_version_id, kind, detail_json, author, created_at
                )
                VALUES (?, ?, 'registered', ?, ?, ?)
                """,
                (new_ulid(), version_id, detail_json, author, now),
            )
            row = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE id = ?", (version_id,)
            ).fetchone()
            connection.execute("COMMIT")
            return {"version": dict(row), "already_exists": False}
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def transition_task_blueprint_version(
        self,
        *,
        blueprint_version_id: str,
        status: str,
        event_kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Advance a blueprint version's status (reviewed/active/retired) and append
        the matching review event atomically. Returns the updated version row."""

        now = utc_now_iso(clock)
        stamp_column = {
            "reviewed": "reviewed_at",
            "active": "activated_at",
        }.get(status)
        with self.connection() as connection:
            if stamp_column is not None:
                connection.execute(
                    f"UPDATE task_blueprint_versions SET status = ?, {stamp_column} = ? WHERE id = ?",
                    (status, now, blueprint_version_id),
                )
            else:
                connection.execute(
                    "UPDATE task_blueprint_versions SET status = ? WHERE id = ?",
                    (status, blueprint_version_id),
                )
            connection.execute(
                """
                INSERT INTO task_blueprint_review_events(
                  id, blueprint_version_id, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (new_ulid(), blueprint_version_id, event_kind, detail_json, author, now),
            )
            row = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE id = ?", (blueprint_version_id,)
            ).fetchone()
            connection.commit()
        return dict(row) if row is not None else {}

    def append_task_blueprint_review_event(
        self,
        *,
        blueprint_version_id: str,
        kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO task_blueprint_review_events(
                  id, blueprint_version_id, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, blueprint_version_id, kind, detail_json, author, utc_now_iso(clock)),
            )
            connection.commit()
        return event_id

    def task_blueprint_version(self, blueprint_version_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE id = ?", (blueprint_version_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def task_blueprint_versions_for(self, blueprint_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM task_blueprint_versions WHERE blueprint_id = ? ORDER BY version",
                (blueprint_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def target_exemplars_for(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM target_exemplars WHERE blueprint_version_id = ? ORDER BY exemplar_ref",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def task_blueprint_review_events_for(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM task_blueprint_review_events WHERE blueprint_version_id = ? ORDER BY created_at, id",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def reviewed_reading_question_placements(
        self,
        *,
        source_revs: Sequence[str],
        unit_ids: Sequence[str],
        blueprint_version_ids: Sequence[str] = (),
    ) -> list[dict[str, Any]]:
        """Return the reviewed blueprint artifacts that can appear in a Reader.

        P3 deliberately has no hot-path question planner: a question is eligible
        only when an owner placed it on a reviewed/active TaskBlueprint version.
        The optional version ids let an active golden-path contract resolve its
        pinned blueprint even when an older source used a semantic revision slug
        rather than the source-layer revision id.
        """

        source_values = tuple(dict.fromkeys(value for value in source_revs if value))
        unit_values = tuple(dict.fromkeys(value for value in unit_ids if value))
        version_values = tuple(dict.fromkeys(value for value in blueprint_version_ids if value))
        clauses: list[str] = []
        params: list[Any] = []
        if source_values and unit_values:
            source_marks = ", ".join("?" for _ in source_values)
            unit_marks = ", ".join("?" for _ in unit_values)
            clauses.append(f"(tb.source_rev IN ({source_marks}) AND tb.unit_id IN ({unit_marks}))")
            params.extend(source_values)
            params.extend(unit_values)
        if version_values:
            version_marks = ", ".join("?" for _ in version_values)
            clauses.append(f"tbv.id IN ({version_marks})")
            params.extend(version_values)
        if not clauses:
            return []

        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                  e.id AS placement_event_id,
                  e.detail_json AS placement_json,
                  e.created_at AS placement_created_at,
                  tbv.id AS blueprint_version_id,
                  tbv.version AS blueprint_version,
                  tbv.status AS blueprint_status,
                  tbv.spec_json AS blueprint_spec_json,
                  tb.id AS blueprint_id,
                  tb.source_rev,
                  tb.unit_id,
                  tb.family_key
                FROM task_blueprint_review_events e
                JOIN task_blueprint_versions tbv ON tbv.id = e.blueprint_version_id
                JOIN task_blueprints tb ON tb.id = tbv.blueprint_id
                WHERE e.kind = 'reading_question_placed'
                  AND tbv.status IN ('reviewed', 'active')
                  AND ({' OR '.join(clauses)})
                ORDER BY
                  CASE tbv.status WHEN 'active' THEN 0 ELSE 1 END,
                  tbv.version DESC,
                  e.created_at,
                  e.id
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def golden_path_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_runs WHERE id = ?", (run_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def golden_path_run_for_goal(self, goal_id: str) -> dict[str, Any] | None:
        """The earliest golden-path run for a goal (the golden path is one run per
        goal). Used by confirmation to detect a re-confirm that differs only in a
        run-shaping param (C4)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_runs WHERE goal_id = ? ORDER BY created_at, id LIMIT 1",
                (goal_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def golden_path_run_events_for(self, run_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM golden_path_run_events WHERE run_id = ? ORDER BY seq",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def append_golden_path_run_event(
        self,
        *,
        run_id: str,
        to_state: str,
        reason: str,
        expected_head_event_id: str | None = None,
        idempotency_key: str | None = None,
        feasible_alternatives_json: str | None = None,
        evidence_ids_json: str | None = None,
        goal_contract_head_version_id: str | None = None,
        depth_policy_version_id: str | None = None,
        depth_envelope_version_id: str | None = None,
        predecessor_milestone: str | None = None,
        successor_milestone: str | None = None,
        selected_activity_json: str | None = None,
        policy_calibration_json: str | None = None,
        burden_json: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one transition event and update the run's cached head state, in one
        transaction. Fenced on ``expected_head_event_id`` (§4.3 optimistic head) and
        idempotent on ``UNIQUE(run_id, idempotency_key)`` (§12.6 exactly-once). On an
        idempotency-key replay returns the existing event with ``already_exists=True``;
        on a fence mismatch returns ``{"stale": True, ...}`` and writes nothing."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                prior = connection.execute(
                    "SELECT * FROM golden_path_run_events WHERE run_id = ? AND idempotency_key = ?",
                    (run_id, idempotency_key),
                ).fetchone()
                if prior is not None:
                    connection.execute("ROLLBACK")
                    return {"event": dict(prior), "already_exists": True}
            head = connection.execute(
                "SELECT * FROM golden_path_run_events WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            head_id = head["id"] if head is not None else None
            head_seq = head["seq"] if head is not None else 0
            from_state = head["to_state"] if head is not None else None
            if expected_head_event_id is not None and expected_head_event_id != head_id:
                connection.execute("ROLLBACK")
                return {"stale": True, "expected": expected_head_event_id, "actual": head_id}
            event_id = new_ulid()
            next_seq = head_seq + 1
            connection.execute(
                """
                INSERT INTO golden_path_run_events(
                  id, run_id, seq, from_state, to_state, reason,
                  feasible_alternatives_json, evidence_ids_json,
                  goal_contract_head_version_id, depth_policy_version_id,
                  depth_envelope_version_id, predecessor_milestone, successor_milestone,
                  selected_activity_json, policy_calibration_json, burden_json,
                  expected_head_event_id, idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id, run_id, next_seq, from_state, to_state, reason,
                    feasible_alternatives_json, evidence_ids_json,
                    goal_contract_head_version_id, depth_policy_version_id,
                    depth_envelope_version_id, predecessor_milestone, successor_milestone,
                    selected_activity_json, policy_calibration_json, burden_json,
                    expected_head_event_id, idempotency_key, now,
                ),
            )
            connection.execute(
                "UPDATE golden_path_runs SET current_state = ?, updated_at = ? WHERE id = ?",
                (to_state, now, run_id),
            )
            connection.execute("COMMIT")
            row = connection.execute(
                "SELECT * FROM golden_path_run_events WHERE id = ?", (event_id,)
            ).fetchone()
            return {"event": dict(row), "already_exists": False}
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # P2 LEARNING track -- pattern-ladder policy (spec_p2 §7.1, §7.2;
    # migration 084). The ladder POLICY is reviewable DATA; ladder STATE lives on
    # golden_path_run_events (no parallel table).
    # ------------------------------------------------------------------

    def active_ladder_policy(self, policy_slug: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM p2_ladder_policies WHERE policy_slug = ? AND status = 'active' "
                "ORDER BY policy_version DESC LIMIT 1",
                (policy_slug,),
            ).fetchone()
        return dict(row) if row is not None else None

    def ladder_stages_for_policy(self, policy_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM p2_ladder_stages WHERE policy_id = ? ORDER BY ordinal, stage_key",
                (policy_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # P2 PRACTICE track -- rotating practice pool (spec_p2 §7.3, U-028;
    # migration 085).
    # ------------------------------------------------------------------

    def ensure_practice_pool(
        self,
        *,
        pool_slug: str,
        blueprint_version_id: str,
        content_hash: str,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Register/return the stable practice pool row. Idempotent on ``pool_slug``:
        a re-register returns the existing row (``already_exists=True``) so pool
        assembly is deterministic (§7.3)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT * FROM practice_pools WHERE pool_slug = ?", (pool_slug,)
            ).fetchone()
            if existing is not None:
                return {"pool": dict(existing), "already_exists": True}
            pool_id = new_ulid()
            connection.execute(
                """
                INSERT INTO practice_pools(
                  id, pool_slug, blueprint_version_id, status, content_hash, created_at
                )
                VALUES (?, ?, ?, 'draft', ?, ?)
                """,
                (pool_id, pool_slug, blueprint_version_id, content_hash, now),
            )
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, 'registered', ?, 'owner', ?)
                """,
                (new_ulid(), pool_id, _json({"content_hash": content_hash}), now),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM practice_pools WHERE id = ?", (pool_id,)
            ).fetchone()
            return {"pool": dict(row), "already_exists": False}

    def register_practice_pool_surface(
        self,
        *,
        pool_id: str,
        surface_slug: str,
        angle: str,
        content_hash: str,
        provenance: str = "llm_within_bounds",
        surface_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Register a candidate practice surface. Idempotent on
        ``UNIQUE(pool_id, surface_slug)``."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM practice_pool_surfaces WHERE pool_id = ? AND surface_slug = ?",
                (pool_id, surface_slug),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            row_id = new_ulid()
            connection.execute(
                """
                INSERT INTO practice_pool_surfaces(
                  id, pool_id, surface_slug, angle, provenance, surface_id,
                  admission_status, content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'candidate', ?, ?)
                """,
                (row_id, pool_id, surface_slug, angle, provenance, surface_id, content_hash, now),
            )
            connection.commit()
            return row_id

    def set_practice_pool_surface_admission(
        self,
        *,
        pool_id: str,
        surface_slug: str,
        admission_status: str,
        surface_id: str | None = None,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        kind = "admitted" if admission_status == "admitted" else "rejected"
        with self.connection() as connection:
            if surface_id is not None:
                connection.execute(
                    "UPDATE practice_pool_surfaces SET admission_status = ?, surface_id = ? "
                    "WHERE pool_id = ? AND surface_slug = ?",
                    (admission_status, surface_id, pool_id, surface_slug),
                )
            else:
                connection.execute(
                    "UPDATE practice_pool_surfaces SET admission_status = ? "
                    "WHERE pool_id = ? AND surface_slug = ?",
                    (admission_status, pool_id, surface_slug),
                )
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (new_ulid(), pool_id, surface_slug, kind, detail_json, author, now),
            )
            connection.commit()

    def transition_practice_pool(
        self,
        *,
        pool_id: str,
        status: str,
        kind: str,
        detail_json: str | None = None,
        author: str = "owner",
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE practice_pools SET status = ? WHERE id = ?", (status, pool_id)
            )
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?)
                """,
                (new_ulid(), pool_id, kind, detail_json, author, now),
            )
            connection.commit()

    def append_practice_pool_event(
        self,
        *,
        pool_id: str,
        kind: str,
        surface_slug: str | None = None,
        detail_json: str | None = None,
        author: str = "system",
        clock: Clock | None = None,
    ) -> str:
        """Append one pool ledger event (§7.3 audit) -- e.g. ``served`` / ``rotated``
        from ``next_practice_surface``. Pure ledger append; touches no pool status."""

        now = utc_now_iso(clock)
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO practice_pool_events(
                  id, pool_id, surface_slug, kind, detail_json, author, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, pool_id, surface_slug, kind, detail_json, author, now),
            )
            connection.commit()
        return event_id

    def practice_pool(self, pool_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_pools WHERE id = ?", (pool_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def practice_pools_for_blueprint(self, blueprint_version_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_pools WHERE blueprint_version_id = ? ORDER BY created_at, id",
                (blueprint_version_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def practice_pool_surfaces_for(self, pool_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_pool_surfaces WHERE pool_id = ? ORDER BY surface_slug",
                (pool_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def practice_pool_events_for(self, pool_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_pool_events WHERE pool_id = ? ORDER BY created_at, id",
                (pool_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def append_golden_path_artifact(
        self,
        *,
        run_id: str,
        kind: str,
        payload_json: str,
        idempotency_key: str | None = None,
        administration_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one inspectable run artifact (§8.4). Idempotent on
        ``UNIQUE(run_id, idempotency_key)``: a crash/retry collapses to exactly one
        artifact and returns the existing row with ``already_exists=True`` (§12.6)."""

        now = utc_now_iso(clock)
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                prior = connection.execute(
                    "SELECT * FROM golden_path_artifacts WHERE run_id = ? AND idempotency_key = ?",
                    (run_id, idempotency_key),
                ).fetchone()
                if prior is not None:
                    connection.execute("ROLLBACK")
                    return {"artifact": dict(prior), "already_exists": True}
            head = connection.execute(
                "SELECT seq FROM golden_path_artifacts WHERE run_id = ? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            next_seq = (head["seq"] if head is not None else 0) + 1
            artifact_id = new_ulid()
            connection.execute(
                """
                INSERT INTO golden_path_artifacts(
                  id, run_id, seq, kind, administration_id, payload_json,
                  idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id, run_id, next_seq, kind, administration_id,
                    payload_json, idempotency_key, now,
                ),
            )
            connection.execute("COMMIT")
            row = connection.execute(
                "SELECT * FROM golden_path_artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            return {"artifact": dict(row), "already_exists": False}
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            connection.close()

    def golden_path_artifacts_for(
        self, run_id: str, *, kind: str | None = None
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if kind is None:
                rows = connection.execute(
                    "SELECT * FROM golden_path_artifacts WHERE run_id = ? ORDER BY seq",
                    (run_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM golden_path_artifacts WHERE run_id = ? AND kind = ? ORDER BY seq",
                    (run_id, kind),
                ).fetchall()
        return [dict(row) for row in rows]

    def latest_golden_path_artifact(
        self, run_id: str, *, kind: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM golden_path_artifacts WHERE run_id = ? AND kind = ? "
                "ORDER BY seq DESC LIMIT 1",
                (run_id, kind),
            ).fetchone()
        return dict(row) if row is not None else None
