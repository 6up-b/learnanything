"""Practice state, practice sessions and scheduler records.

Owns item and mastery state, fitted parameters, sessions and checkpoints,
and scheduler explanations and decision features."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.records import (
    ItemParameterState,
    MasteryState,
    PracticeItemState,
    _decode_decision_features,
    _decode_elicitation_event,
    _decode_learning_outcome_label,
    _decode_scheduler_explanation,
    _decode_scheduler_slate,
    _decode_scheduler_slate_candidate,
)
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


@dataclass(frozen=True)
class PracticeItemQualityState:
    practice_item_id: str
    bad_item_suspicion: float
    evidence_count: int
    suspicion_reasons: list[str]
    last_flagged_at: str | None
    algorithm_version: str
    updated_at: str


def _practice_item_state(row: sqlite3.Row) -> PracticeItemState:
    return PracticeItemState(
        practice_item_id=row["practice_item_id"],
        difficulty=row["difficulty"],
        stability=row["stability"],
        retrievability=row["retrievability"],
        due_at=row["due_at"],
        active=bool(row["active"]),
        content_hash=row["content_hash"],
        last_attempt_at=row["last_attempt_at"],
        updated_at=row["updated_at"],
    )


def _mastery_state(row: sqlite3.Row) -> MasteryState:
    return MasteryState(
        learning_object_id=row["learning_object_id"],
        logit_mean=row["logit_mean"],
        logit_variance=row["logit_variance"],
        evidence_count=row["evidence_count"],
        last_evidence_at=row["last_evidence_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _practice_item_quality_state(row: sqlite3.Row) -> PracticeItemQualityState:
    return PracticeItemQualityState(
        practice_item_id=row["practice_item_id"],
        bad_item_suspicion=row["bad_item_suspicion"],
        evidence_count=row["evidence_count"],
        suspicion_reasons=_loads(row["suspicion_reasons_json"], []),
        last_flagged_at=row["last_flagged_at"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


def _decode_ability_transition_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["target_facets"] = _loads(payload.pop("target_facets_json"), [])
    payload["applied_to_belief_counts"] = bool(payload["applied_to_belief_counts"])
    payload["applied_to_mastery"] = bool(payload["applied_to_mastery"])
    payload["applied_to_facet_recall"] = bool(payload["applied_to_facet_recall"])
    return payload


def _decode_fitted_parameters(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["params"] = _loads(payload.pop("params_json"), {})
    payload["metrics"] = _loads(payload.pop("metrics_json"), None)
    payload["active"] = bool(payload["active"])
    return payload


def _decode_item_parameter_state(row: sqlite3.Row) -> ItemParameterState:
    return ItemParameterState(
        practice_item_id=row["practice_item_id"],
        b_mean=row["b_mean"],
        b_var=row["b_var"],
        evidence_count=row["evidence_count"],
        algorithm_version=row["algorithm_version"],
        updated_at=row["updated_at"],
    )


class PracticeStateStoreMixin:

    def practice_item_state(self, practice_item_id: str) -> PracticeItemState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_item_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _practice_item_state(row) if row is not None else None

    def practice_item_states(self) -> dict[str, PracticeItemState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM practice_item_state").fetchall()
        return {row["practice_item_id"]: _practice_item_state(row) for row in rows}

    def initialize_practice_item_state(
        self,
        practice_item_id: str,
        *,
        content_hash: str | None = None,
        active: bool = True,
        clock: Clock | None = None,
    ) -> bool:
        """Insert a fresh scheduling row only when none exists.

        Never touches an existing row (practice already recorded for the item),
        so a retried publication cannot erase scheduling state. Returns whether
        a row was inserted.
        """
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO practice_item_state(
                  practice_item_id, difficulty, stability, retrievability, due_at,
                  active, content_hash, last_attempt_at, updated_at
                )
                VALUES (?, NULL, NULL, NULL, NULL, ?, ?, NULL, ?)
                ON CONFLICT(practice_item_id) DO NOTHING
                """,
                (practice_item_id, 1 if active else 0, content_hash, now),
            )
            connection.commit()
        return cursor.rowcount > 0

    def update_practice_item_content_state(
        self,
        practice_item_id: str,
        *,
        active: bool,
        content_hash: str | None,
        clock: Clock | None = None,
    ) -> bool:
        """Set only ``active`` and ``content_hash`` on an existing row.

        Mobile PR-2: content sync owns these two columns and nothing else, so it
        can never write back a difficulty, stability, retrievability, due date or
        last-attempt time it read before an attempt committed in another process.
        The caller decides ``active`` and calls this inside the same
        ``atomic()`` transaction (``reconcile_practice_item_state``). Returns
        whether a row was updated.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE practice_item_state SET active = ?, content_hash = ?, updated_at = ? "
                "WHERE practice_item_id = ?",
                (1 if active else 0, content_hash, now, practice_item_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def upsert_practice_item_state(
        self,
        practice_item_id: str,
        *,
        difficulty: float | None = None,
        stability: float | None = None,
        retrievability: float | None = None,
        due_at: str | None = None,
        active: bool = True,
        content_hash: str | None = None,
        last_attempt_at: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO practice_item_state(
                  practice_item_id, difficulty, stability, retrievability, due_at,
                  active, content_hash, last_attempt_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(practice_item_id) DO UPDATE SET
                  difficulty = excluded.difficulty,
                  stability = excluded.stability,
                  retrievability = excluded.retrievability,
                  due_at = excluded.due_at,
                  active = excluded.active,
                  content_hash = excluded.content_hash,
                  last_attempt_at = excluded.last_attempt_at,
                  updated_at = excluded.updated_at
                """,
                (
                    practice_item_id,
                    difficulty,
                    stability,
                    retrievability,
                    due_at,
                    1 if active else 0,
                    content_hash,
                    last_attempt_at,
                    now,
                ),
            )
            connection.commit()

    def inactive_practice_item_ids(self, practice_item_ids: Iterable[str]) -> frozenset[str]:
        """The given items whose scheduling row exists and is inactive."""

        ids = sorted({str(value) for value in practice_item_ids})
        if not ids:
            return frozenset()
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT practice_item_id FROM practice_item_state "
                f"WHERE active = 0 AND practice_item_id IN ({placeholders})",
                ids,
            ).fetchall()
        return frozenset(str(row["practice_item_id"]) for row in rows)

    def keep_practice_items_inactive(self, practice_item_ids: Iterable[str]) -> int:
        """Close the given items' rows again after replay rewrote them active.

        Only the flag moves: the replayed scheduling columns and the row's
        stamp stay as replay wrote them. Returns the rows changed.
        """

        ids = sorted({str(value) for value in practice_item_ids})
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE practice_item_state SET active = 0 "
                f"WHERE active = 1 AND practice_item_id IN ({placeholders})",
                ids,
            )
            connection.commit()
        return int(cursor.rowcount)

    def set_practice_item_active(
        self, practice_item_id: str, *, active: bool, clock: Clock | None = None
    ) -> None:
        """Flip only the active flag, preserving scheduling state on the row."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE practice_item_state SET active = ?, updated_at = ? WHERE practice_item_id = ?",
                (1 if active else 0, now, practice_item_id),
            )
            if cursor.rowcount == 0:
                connection.execute(
                    """
                    INSERT INTO practice_item_state(practice_item_id, active, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (practice_item_id, 1 if active else 0, now),
                )
            connection.commit()

    def mastery_state(self, learning_object_id: str) -> MasteryState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM learning_object_mastery WHERE learning_object_id = ?",
                (learning_object_id,),
            ).fetchone()
        return _mastery_state(row) if row is not None else None

    def mastery_states(self) -> dict[str, MasteryState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM learning_object_mastery").fetchall()
        return {row["learning_object_id"]: _mastery_state(row) for row in rows}

    def upsert_mastery_state(
        self,
        mastery: MasteryState,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO learning_object_mastery(
                  learning_object_id, logit_mean, logit_variance, evidence_count,
                  last_evidence_at, algorithm_version, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learning_object_id) DO UPDATE SET
                  logit_mean = excluded.logit_mean,
                  logit_variance = excluded.logit_variance,
                  evidence_count = excluded.evidence_count,
                  last_evidence_at = excluded.last_evidence_at,
                  algorithm_version = excluded.algorithm_version,
                  updated_at = excluded.updated_at
                """,
                (
                    mastery.learning_object_id,
                    mastery.logit_mean,
                    mastery.logit_variance,
                    mastery.evidence_count,
                    mastery.last_evidence_at,
                    mastery.algorithm_version,
                    mastery.updated_at,
                ),
            )
            connection.commit()

    def answer_confidence_presence(self, *, exclude_attempt_ids: Iterable[str] = ()) -> dict[str, int]:
        """How often an ordinary graded attempt carries a pre-answer confidence tap.

        The duel's denominator: graded, unprimed, unhinted ordinary attempts
        (the duel's own exclusions, without its scheduler-candidate match).
        ``exclude_attempt_ids`` are not graded attempts here (the caller's
        held grades).
        """

        excluded = sorted({str(value) for value in exclude_attempt_ids if value})
        exclusion = f" AND a.id NOT IN ({','.join('?' for _ in excluded)})" if excluded else ""
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS graded,
                       COALESCE(SUM(a.answer_confidence IS NOT NULL), 0) AS with_confidence
                FROM practice_attempts a
                WHERE a.correctness IS NOT NULL
                  AND COALESCE(a.primed, 0) = 0
                  AND COALESCE(a.hints_used, 0) = 0
                  AND a.attempt_type NOT IN (
                    'hinted_attempt', 'guided_walkthrough', 'self_report',
                    'dont_know', 'skip'
                  )
                """
                + exclusion,
                excluded,
            ).fetchone()
        return {"graded_attempts": int(row["graded"]), "with_confidence": int(row["with_confidence"])}

    def practice_item_quality_state(self, practice_item_id: str) -> PracticeItemQualityState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM practice_item_quality_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _practice_item_quality_state(row) if row is not None else None

    def practice_item_quality_states(self) -> dict[str, PracticeItemQualityState]:
        """All item-quality projections keyed for a scheduler vault sweep."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM practice_item_quality_state ORDER BY practice_item_id"
            ).fetchall()
        return {
            str(row["practice_item_id"]): _practice_item_quality_state(row)
            for row in rows
        }

    def upsert_practice_item_quality_state(self, state: Mapping[str, Any]) -> None:
        with self.connection() as connection:
            self._upsert_practice_item_quality_state(connection, state)
            connection.commit()

    def ability_transition_event(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ability_transition_events WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _decode_ability_transition_event(row) if row is not None else None

    def prediction_interval_rows(self) -> list[dict[str, Any]]:
        """Per-attempt predicted score distribution joined to the realized
        outcome (`learnloop eval` coverage input), oldest first per LO."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT s.attempt_id, s.predicted_score_dist_json,
                       a.learning_object_id, a.correctness, a.rubric_score,
                       a.attempt_type, a.created_at
                FROM attempt_surprise s
                JOIN practice_attempts a ON a.id = s.attempt_id
                WHERE s.predicted_score_dist_json IS NOT NULL
                  AND a.correctness IS NOT NULL
                ORDER BY a.learning_object_id ASC, a.created_at ASC, a.id ASC
                """
            ).fetchall()
        return [
            {
                "attempt_id": row["attempt_id"],
                "learning_object_id": row["learning_object_id"],
                "predicted_score_dist": _loads(row["predicted_score_dist_json"], None),
                "correctness": row["correctness"],
                "attempt_type": row["attempt_type"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def retention_label_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT l.*, a.primed AS outcome_primed,
                       a.manual_review AS outcome_manual_review,
                       a.manual_review_reason AS outcome_manual_review_reason,
                       a.session_id AS outcome_session_id,
                       source.session_id AS source_session_id
                FROM learning_outcome_labels l
                JOIN practice_attempts a ON a.id=l.outcome_attempt_id
                JOIN practice_attempts source ON source.id=l.source_attempt_id
                WHERE l.label_type = 'same_item_retention'
                ORDER BY l.created_at ASC, l.id ASC
                """
            ).fetchall()
        return [_decode_learning_outcome_label(row) for row in rows]

    def item_attempt_history(self) -> list[dict[str, Any]]:
        """Graded attempts ordered for per-item FSRS replay (`learnloop eval`)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, practice_item_id, rubric_score, hints_used, attempt_type, created_at
                FROM practice_attempts
                WHERE rubric_score IS NOT NULL
                ORDER BY practice_item_id ASC, created_at ASC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def candidate_propensity_rows(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT slate_id, id, selection_propensity, selection_temperature,
                       exploration_flag, chosen_attempt_id, was_returned, propensity_kind
                FROM scheduler_slate_candidates
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_fitted_parameters(
        self,
        *,
        scope: str,
        params: Mapping[str, Any],
        algorithm_version: str,
        training_rows_count: int,
        training_data_through: str | None = None,
        metrics: Mapping[str, Any] | None = None,
        activate: bool = True,
        clock: Clock | None = None,
    ) -> str:
        """Insert a fitted parameter set; when ``activate``, atomically replace
        the currently active set for the scope (history rows are kept)."""

        fitted_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            if activate:
                connection.execute(
                    "UPDATE fitted_parameters SET active = 0, deactivated_at = ? WHERE scope = ? AND active = 1",
                    (now, scope),
                )
            connection.execute(
                """
                INSERT INTO fitted_parameters(
                  id, scope, params_json, fitted_at, algorithm_version,
                  training_rows_count, training_data_through, metrics_json,
                  active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fitted_id,
                    scope,
                    _json(dict(params)),
                    now,
                    algorithm_version,
                    training_rows_count,
                    training_data_through,
                    _json(dict(metrics)) if metrics is not None else None,
                    1 if activate else 0,
                    now,
                ),
            )
            connection.commit()
        return fitted_id

    def active_fitted_parameters(self, scope: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM fitted_parameters
                WHERE scope = ? AND active = 1
                ORDER BY fitted_at DESC, id DESC
                LIMIT 1
                """,
                (scope,),
            ).fetchone()
        return _decode_fitted_parameters(row) if row is not None else None

    def list_fitted_parameters(self, scope: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query = "SELECT * FROM fitted_parameters"
        params: tuple[Any, ...] = ()
        if scope is not None:
            query += " WHERE scope = ?"
            params = (scope,)
        query += " ORDER BY fitted_at DESC, rowid DESC LIMIT ?"
        params = (*params, limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_fitted_parameters(row) for row in rows]

    def deactivate_fitted_parameters(
        self, scope: str, *, fitted_id: str | None = None, clock: Clock | None = None
    ) -> int:
        now = utc_now_iso(clock)
        query = "UPDATE fitted_parameters SET active = 0, deactivated_at = ? WHERE scope = ? AND active = 1"
        params: tuple[Any, ...] = (now, scope)
        if fitted_id is not None:
            query += " AND id = ?"
            params = (*params, fitted_id)
        with self.connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            return cursor.rowcount

    def item_parameter_state(self, practice_item_id: str) -> ItemParameterState | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM item_parameter_state WHERE practice_item_id = ?",
                (practice_item_id,),
            ).fetchone()
        return _decode_item_parameter_state(row) if row is not None else None

    def item_parameter_states(self) -> dict[str, ItemParameterState]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM item_parameter_state").fetchall()
        return {row["practice_item_id"]: _decode_item_parameter_state(row) for row in rows}

    def _upsert_item_parameter_state_record(
        self, connection: sqlite3.Connection, state: ItemParameterState
    ) -> None:
        connection.execute(
            """
            INSERT INTO item_parameter_state(
              practice_item_id, b_mean, b_var, evidence_count, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              b_mean = excluded.b_mean,
              b_var = excluded.b_var,
              evidence_count = excluded.evidence_count,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.b_mean,
                state.b_var,
                state.evidence_count,
                state.algorithm_version,
                state.updated_at,
            ),
        )

    def insert_elicitation_event(self, event: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO elicitation_events(
                  id, session_id, selected_practice_item_id, target_scope_json,
                  policy, candidate_scores_json, entropy_before,
                  expected_information_gain, selected_reason, hypothesis_set_id,
                  hypothesis_set_json, trigger, fallback_outcome, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("session_id"),
                    event.get("selected_practice_item_id"),
                    _json(event.get("target_scope")) if event.get("target_scope") is not None else None,
                    event.get("policy", "probe_eig"),
                    _json(event.get("candidate_scores")) if event.get("candidate_scores") is not None else None,
                    event.get("entropy_before"),
                    event.get("expected_information_gain"),
                    event.get("selected_reason"),
                    event.get("hypothesis_set_id"),
                    _json(event.get("hypothesis_set")) if event.get("hypothesis_set") is not None else None,
                    event.get("trigger"),
                    event.get("fallback_outcome"),
                    now,
                ),
            )
            connection.commit()
        return event_id

    def record_decision_features(
        self,
        *,
        decision_id: str,
        decision_type: str,
        ability_vector: Mapping[str, Any],
        item_demand_vector: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        algorithm_version: str,
        clock: Clock | None = None,
    ) -> str:
        feature_id = new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                """
                SELECT id FROM decision_features
                WHERE decision_id = ? AND decision_type = ?
                """,
                (decision_id, decision_type),
            ).fetchone()
            if existing is not None:
                feature_id = existing["id"]
            connection.execute(
                """
                INSERT INTO decision_features(
                  id, decision_id, decision_type, ability_vector_json,
                  item_demand_vector_json, context_json, algorithm_version, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id, decision_type) DO NOTHING
                """,
                (
                    feature_id,
                    decision_id,
                    decision_type,
                    _json(dict(ability_vector)),
                    _json(dict(item_demand_vector)) if item_demand_vector is not None else None,
                    _json(dict(context or {})),
                    algorithm_version,
                    now,
                ),
            )
            connection.commit()
        return feature_id

    def decision_features(self, *, decision_id: str, decision_type: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM decision_features
                WHERE decision_id = ? AND decision_type = ?
                """,
                (decision_id, decision_type),
            ).fetchone()
        return _decode_decision_features(row) if row is not None else None

    def elicitation_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:
            if session_id is None:
                rows = connection.execute(
                    "SELECT * FROM elicitation_events ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM elicitation_events WHERE session_id = ? ORDER BY created_at DESC",
                    (session_id,),
                ).fetchall()
        return [_decode_elicitation_event(row) for row in rows]

    def insert_scheduler_explanations(
        self,
        explanations: Iterable[dict[str, Any]],
        *,
        session_id: str | None,
        algorithm_version: str,
        retention_limit: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for explanation in explanations:
                connection.execute(
                    """
                    INSERT INTO scheduler_explanations(
                      id, session_id, practice_item_id, selected_mode, priority,
                      components_json, readiness_factor, expected_information_gain,
                      target_scope_json, plain_english_json, algorithm_version, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        session_id,
                        explanation["practice_item_id"],
                        explanation.get("selected_mode", "review"),
                        explanation["priority"],
                        _json(explanation["components"]),
                        explanation.get("readiness_factor"),
                        explanation.get("expected_information_gain"),
                        _json(explanation.get("target_scope")) if explanation.get("target_scope") is not None else None,
                        _json(explanation.get("plain_english")) if explanation.get("plain_english") is not None else None,
                        algorithm_version,
                        now,
                    ),
                )
            if session_id is not None and retention_limit is not None and retention_limit > 0:
                connection.execute(
                    """
                    DELETE FROM scheduler_explanations
                    WHERE session_id = ?
                      AND id NOT IN (
                        SELECT id FROM scheduler_explanations
                        WHERE session_id = ?
                        ORDER BY created_at DESC, priority DESC, practice_item_id ASC, id DESC
                        LIMIT ?
                      )
                    """,
                    (session_id, session_id, retention_limit),
                )
            connection.commit()

    def latest_scheduler_slate_by_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM scheduler_slates
                WHERE session_id = ?
                ORDER BY generated_at DESC, id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return _decode_scheduler_slate(row) if row is not None else None

    def scheduler_slate_candidates(self, slate_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scheduler_slate_candidates
                WHERE slate_id = ?
                ORDER BY rank ASC, id ASC
                """,
                (slate_id,),
            ).fetchall()
        return [_decode_scheduler_slate_candidate(row) for row in rows]

    def latest_scheduler_explanation(self, practice_item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM scheduler_explanations
                WHERE practice_item_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (practice_item_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "practice_item_id": row["practice_item_id"],
            "selected_mode": row["selected_mode"],
            "priority": row["priority"],
            "components": _loads(row["components_json"], {}),
            "readiness_factor": row["readiness_factor"],
            "expected_information_gain": row["expected_information_gain"],
            "target_scope": _loads(row["target_scope_json"], None),
            "plain_english": _loads(row["plain_english_json"], {}),
            "created_at": row["created_at"],
        }

    def latest_scheduler_explanations_by_session(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM scheduler_explanations
                WHERE session_id = ?
                ORDER BY created_at DESC, priority DESC, practice_item_id
                """,
                (session_id,),
            ).fetchall()
        return [_decode_scheduler_explanation(row) for row in rows]

    def create_session(
        self,
        *,
        energy: str | None = None,
        sleep_quality: float | None = None,
        available_minutes: int | None = None,
        notes_md_path: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        session_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions(
                  id, started_at, ended_at, energy, sleep_quality,
                  available_minutes, notes_md_path, updated_at
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                """,
                (session_id, now, energy, sleep_quality, available_minutes, notes_md_path, now),
            )
            connection.commit()
        return session_id

    def fetch_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def most_recent_open_session(self) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM sessions
                WHERE ended_at IS NULL
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row is not None else None

    def latest_session_minutes(self) -> tuple[int, str] | None:
        """``(minutes, started_at)`` of the latest session begun with minutes, or None.

        Daily-loop DL0 (spec_daily_loop_v1.md §6.6): Start remembers the last
        session's budget. Sessions that recorded no minutes (old clients, the
        CLI) are skipped rather than read as "no budget". The start time lets
        a newer choice that recorded no session (the TUI's) win over it.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT available_minutes, started_at FROM sessions
                WHERE available_minutes IS NOT NULL AND available_minutes > 0
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return int(row["available_minutes"]), str(row["started_at"])

    def session_day_streak(self, *, clock: Clock | None = None) -> dict[str, Any]:
        """Consecutive-day study streak derived from session start timestamps.

        Days are counted in the machine's local timezone. ``current`` is the run
        of consecutive days ending today (or yesterday, if today has no session
        yet but the streak is still alive). ``active_today`` reports whether a
        session was already started today, and ``longest`` is the best run ever.
        """
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT started_at FROM sessions WHERE started_at IS NOT NULL"
            ).fetchall()

        days: set[date] = set()
        for row in rows:
            started = parse_utc(row["started_at"])
            if started is not None:
                days.add(started.astimezone().date())

        if not days:
            return {"current": 0, "active_today": False, "longest": 0}

        today = (clock or SystemClock()).now().astimezone().date()
        active_today = today in days

        anchor = today if active_today else today - timedelta(days=1)
        current = 0
        cursor = anchor
        while cursor in days:
            current += 1
            cursor -= timedelta(days=1)

        ordered = sorted(days)
        longest = 1
        run = 1
        for previous, day in zip(ordered, ordered[1:], strict=False):
            run = run + 1 if (day - previous).days == 1 else 1
            longest = max(longest, run)

        return {"current": current, "active_today": active_today, "longest": longest}

    def end_session(self, session_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET ended_at = COALESCE(ended_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (now, now, session_id),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                return None
            row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            connection.commit()
        return dict(row) if row is not None else None

    def session_learner_answers(self, session_id: str) -> list[str]:
        """Every answer body recorded against this session, in submission order.

        Exists for Meas §3.A6's per-session elicitation budget, which has no
        ledger of its own to count: an offer the learner declines is
        deliberately never written down, so the submitted answers are the only
        record of how many extra lines were actually volunteered. Scoped
        strictly to ``session_id`` rather than the started/ended window
        ``session_attempt_counts`` falls back to — a budget that leaked across
        sessions through orphaned attempts would silently tighten itself.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT learner_answer_md FROM practice_attempts
                WHERE session_id = ?
                ORDER BY created_at, id
                """,
                (session_id,),
            ).fetchall()
        return [str(row["learner_answer_md"] or "") for row in rows]

    def update_session_checkpoint(
        self,
        session_id: str,
        *,
        current_practice_item_id: str | None = None,
        current_answer: str | None = None,
        focus_block_state: Mapping[str, Any] | None = None,
        pending_grading_proposal: Mapping[str, Any] | None = None,
        readiness: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO session_checkpoints(
                  session_id, current_practice_item_id, current_answer,
                  focus_block_state_json, pending_grading_proposal_json,
                  readiness_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                  current_practice_item_id = excluded.current_practice_item_id,
                  current_answer = excluded.current_answer,
                  focus_block_state_json = excluded.focus_block_state_json,
                  pending_grading_proposal_json = excluded.pending_grading_proposal_json,
                  readiness_json = excluded.readiness_json,
                  updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    current_practice_item_id,
                    current_answer,
                    _json(focus_block_state) if focus_block_state is not None else None,
                    _json(pending_grading_proposal) if pending_grading_proposal is not None else None,
                    _json(readiness) if readiness is not None else None,
                    now,
                ),
            )
            connection.commit()

    def fetch_session_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["focus_block_state"] = _loads(payload.pop("focus_block_state_json"), None)
        payload["pending_grading_proposal"] = _loads(payload.pop("pending_grading_proposal_json"), None)
        payload["readiness"] = _loads(payload.pop("readiness_json"), None)
        return payload

    def open_session_checkpoints_except(self, session_id: str) -> list[dict[str, Any]]:
        """The checkpoints of every OTHER open session (the ones
        :meth:`end_open_sessions_except` is about to end), decoded like
        :meth:`fetch_session_checkpoint`."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT checkpoint.session_id
                FROM session_checkpoints checkpoint
                JOIN sessions ON sessions.id = checkpoint.session_id
                WHERE sessions.ended_at IS NULL AND sessions.id != ?
                ORDER BY checkpoint.session_id
                """,
                (session_id,),
            ).fetchall()
        checkpoints = [self.fetch_session_checkpoint(str(row["session_id"])) for row in rows]
        return [checkpoint for checkpoint in checkpoints if checkpoint is not None]

    def clear_session_checkpoint(self, session_id: str) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def clear_practice_checkpoint_for_item(self, session_id: str, practice_item_id: str) -> bool:
        """Clear this session's draft only while it still points at this card.

        A card the learner skipped (learner field F2's "I know this") must not
        reopen on restart; a draft the session has since moved to another card
        is left alone. Runs inside the caller's ``atomic()`` when there is one.
        """

        with self.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ? AND current_practice_item_id = ?",
                (session_id, practice_item_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def acknowledge_practice_checkpoint(
        self,
        session_id: str,
        *,
        practice_item_id: str,
        submission_id: str,
    ) -> str:
        """Atomically clear only the practice checkpoint the client received.

        A post-submit route can unmount its Practice screen while a new item is
        already saving a draft in the same session.  A session-id-only DELETE
        lets the stale completion erase that newer checkpoint.  Holding an
        immediate SQLite write lock across compare + delete makes the expected
        item/retry key an acknowledgement token rather than a best-effort read.
        """

        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT current_practice_item_id, focus_block_state_json
                FROM session_checkpoints
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            if row is None:
                return "already_absent"
            focus = _loads(row["focus_block_state_json"], None)
            practice = focus.get("practice") if isinstance(focus, dict) else None
            saved_submission_id = None
            if isinstance(practice, dict):
                saved_submission_id = practice.get("submissionId") or practice.get("submission_id")
            if (
                row["current_practice_item_id"] != practice_item_id
                or saved_submission_id != submission_id
            ):
                return "checkpoint_mismatch"
            cursor = connection.execute(
                "DELETE FROM session_checkpoints WHERE session_id = ?",
                (session_id,),
            )
            return "cleared" if cursor.rowcount > 0 else "checkpoint_mismatch"

    def _record_attempt_practice_item_state(
        self,
        connection: sqlite3.Connection,
        state: PracticeItemState,
    ) -> None:
        """A live attempt's write to its item's scheduling row.

        Mobile PR-4 (the reverse of PR-2's race, ``spec_mobile_tailnet_v1``
        §9.3): content sync owns ``active`` and ``content_hash``, and an
        attempt owns the memory state. The attempt computed both content
        columns from the vault it loaded, which a content sync in another
        process (the desktop's watcher, the phone host's reload) may have
        moved past while the answer was being graded; writing them back would
        reopen an item the sync just closed, or restore an old hash. So an
        existing row takes only the scheduling columns and the last-attempt
        time, and ``active`` can only close: a diagnostic probe's single use
        (``active = 0``) still lands, a non-probe attempt never reopens a row.
        A missing row is inserted whole, as before. Replay keeps the full
        upsert (``replace_attempt_derived_outcome``): it deletes the rows it
        rebuilds first, and re-closes what was closed outside the ledger.
        Without a concurrent writer it also keeps a closed row closed, which
        changes serving (``ATTEMPT_CONTENT_STATE_ALGORITHM_VERSION``).
        """

        connection.execute(
            """
            INSERT INTO practice_item_state(
              practice_item_id, difficulty, stability, retrievability, due_at,
              active, content_hash, last_attempt_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              difficulty = excluded.difficulty,
              stability = excluded.stability,
              retrievability = excluded.retrievability,
              due_at = excluded.due_at,
              active = MIN(practice_item_state.active, excluded.active),
              last_attempt_at = excluded.last_attempt_at,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.difficulty,
                state.stability,
                state.retrievability,
                state.due_at,
                1 if state.active else 0,
                state.content_hash,
                state.last_attempt_at,
                state.updated_at,
            ),
        )

    def _upsert_practice_item_state_record(
        self,
        connection: sqlite3.Connection,
        state: PracticeItemState,
    ) -> None:
        connection.execute(
            """
            INSERT INTO practice_item_state(
              practice_item_id, difficulty, stability, retrievability, due_at,
              active, content_hash, last_attempt_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              difficulty = excluded.difficulty,
              stability = excluded.stability,
              retrievability = excluded.retrievability,
              due_at = excluded.due_at,
              active = excluded.active,
              content_hash = excluded.content_hash,
              last_attempt_at = excluded.last_attempt_at,
              updated_at = excluded.updated_at
            """,
            (
                state.practice_item_id,
                state.difficulty,
                state.stability,
                state.retrievability,
                state.due_at,
                1 if state.active else 0,
                state.content_hash,
                state.last_attempt_at,
                state.updated_at,
            ),
        )

    def _upsert_mastery_state_record(
        self,
        connection: sqlite3.Connection,
        mastery: MasteryState,
    ) -> None:
        connection.execute(
            """
            INSERT INTO learning_object_mastery(
              learning_object_id, logit_mean, logit_variance, evidence_count,
              last_evidence_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learning_object_id) DO UPDATE SET
              logit_mean = excluded.logit_mean,
              logit_variance = excluded.logit_variance,
              evidence_count = excluded.evidence_count,
              last_evidence_at = excluded.last_evidence_at,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                mastery.learning_object_id,
                mastery.logit_mean,
                mastery.logit_variance,
                mastery.evidence_count,
                mastery.last_evidence_at,
                mastery.algorithm_version,
                mastery.updated_at,
            ),
        )

    def _upsert_practice_item_quality_state(self, connection: sqlite3.Connection, state: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO practice_item_quality_state(
              practice_item_id, bad_item_suspicion, evidence_count,
              suspicion_reasons_json, last_flagged_at, algorithm_version, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(practice_item_id) DO UPDATE SET
              bad_item_suspicion = excluded.bad_item_suspicion,
              evidence_count = excluded.evidence_count,
              suspicion_reasons_json = excluded.suspicion_reasons_json,
              last_flagged_at = excluded.last_flagged_at,
              algorithm_version = excluded.algorithm_version,
              updated_at = excluded.updated_at
            """,
            (
                state["practice_item_id"],
                state["bad_item_suspicion"],
                state["evidence_count"],
                _json(state.get("suspicion_reasons", [])),
                state.get("last_flagged_at"),
                state["algorithm_version"],
                state["updated_at"],
            ),
        )

    def _upsert_ability_transition_event(self, connection: sqlite3.Connection, event: Mapping[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO ability_transition_events(
              attempt_id, learning_object_id, practice_item_id, transition_type,
              expected_skill_gain, target_facets_json, reason,
              applied_to_belief_counts, applied_to_mastery, applied_to_facet_recall,
              process_noise, algorithm_version, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
              learning_object_id = excluded.learning_object_id,
              practice_item_id = excluded.practice_item_id,
              transition_type = excluded.transition_type,
              expected_skill_gain = excluded.expected_skill_gain,
              target_facets_json = excluded.target_facets_json,
              reason = excluded.reason,
              applied_to_belief_counts = excluded.applied_to_belief_counts,
              applied_to_mastery = excluded.applied_to_mastery,
              applied_to_facet_recall = excluded.applied_to_facet_recall,
              process_noise = excluded.process_noise,
              algorithm_version = excluded.algorithm_version,
              created_at = excluded.created_at
            """,
            (
                event["attempt_id"],
                event["learning_object_id"],
                event["practice_item_id"],
                event["transition_type"],
                event["expected_skill_gain"],
                _json(event.get("target_facets", [])),
                event["reason"],
                1 if event.get("applied_to_belief_counts") else 0,
                1 if event.get("applied_to_mastery") else 0,
                1 if event.get("applied_to_facet_recall") else 0,
                event.get("process_noise"),
                event["algorithm_version"],
                event["created_at"],
            ),
        )
