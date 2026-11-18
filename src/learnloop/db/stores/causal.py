"""Causal hypotheses, evidence and probe decisions.

Owns causal classifications, discriminating observations, mechanism taxonomy and probe receipts."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import field  # noqa: F401  Keeps the moved field-shadowing directives valid.
from typing import Any, Iterable, Mapping, Sequence

from learnloop.causal_activity_policy import (
    CAUSAL_ACTIVITY_POLICY_VERSION,
    CONTAMINATION_PRECEDENCE,
    policy_for_class,
)
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import _decode_causal_hypothesis
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid

#: `causal_discriminating_observations.channel` (migration 155). NULL is the
#: legacy encoding of this same value, so readers accept either.
OBSERVATION_CHANNEL_BLIND_PROBE = "blind_probe"


def _decode_diagnosis_adjudication(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["adjudicated_anchor"] = _loads(
        data.pop("adjudicated_anchor_json", None), None
    )
    data["system_snapshot"] = _loads(data.pop("system_snapshot_json"), {})
    data["system_abstained"] = bool(data["system_abstained"])
    return data


def _resolve_causal_activity_classification(
    attempt_id: str, events: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Fold one decoded activity-event history through the policy authority."""

    winning_class = min(
        (str(event["contamination_class"]) for event in events),
        key=CONTAMINATION_PRECEDENCE.index,
    )
    winners = [
        event
        for event in events
        if str(event["contamination_class"]) == winning_class
    ]
    near_clone = any(bool(event["near_clone"]) for event in winners)
    primary = next(
        (event for event in winners if bool(event["near_clone"]) == near_clone),
        winners[0],
    )
    policy = policy_for_class(winning_class, near_clone=near_clone)
    detail: dict[str, Any] = {}
    for event in events:
        detail.update(event.get("detail") or {})
    return {
        "attempt_id": attempt_id,
        **policy.as_dict(),
        "near_clone_basis": primary.get("near_clone_basis"),
        "source": primary.get("source"),
        "detail": detail,
        "created_at": primary.get("created_at"),
        "recorded_classes": sorted(
            {str(event["contamination_class"]) for event in events},
            key=CONTAMINATION_PRECEDENCE.index,
        ),
        "event_count": len(events),
    }


def _decode_causal_activity_event(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["near_clone"] = bool(payload["near_clone"])
    payload["closes_pre_intervention_segment"] = bool(
        payload["closes_pre_intervention_segment"]
    )
    payload["eligible_for_fsrs"] = bool(payload["eligible_for_fsrs"])
    payload["eligible_for_certification"] = bool(
        payload["eligible_for_certification"]
    )
    payload["detail"] = _loads(payload.pop("detail_json"), {})
    return payload


def _decode_causal_discriminating_observation(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    for field in (  # noqa: F402  a local loop variable; this function never calls dataclasses.field()
        "blind_bundle_ids",
        "classified_as",
        "observed_features",
        "support_scores",
        "detail",
    ):
        payload[field] = _loads(payload.pop(f"{field}_json"), None)
    for field in (
        "supports_open_set",
        "declared_keys_observed",
        "admitted",
        "resolved_factor",
    ):
        payload[field] = bool(payload[field])
    # Tri-state (migration 155): NULL means "independence was never assessed"
    # (every pre-155 row), which is not the same claim as "assessed and
    # contaminated". Coercing it to False would rewrite silence as a finding.
    raw_admissible = payload.get("admissible_as_independent")
    payload["admissible_as_independent"] = (
        None if raw_admissible is None else bool(raw_admissible)
    )
    return payload


def _decode_causal_mechanism_taxonomy(
    row: sqlite3.Row,
) -> dict[str, Any]:
    payload = dict(row)
    payload["taxonomy"] = _loads(payload.pop("taxonomy_json"), {})
    return payload


class CausalStoreMixin:

    # -- P1 causal hypotheses + diagnosis receipts -----------------------

    def latest_causal_hypothesis_for_episode(
        self, episode_key: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM causal_hypotheses
                 WHERE episode_key = ?
                 ORDER BY version DESC
                 LIMIT 1
                """,
                (episode_key,),
            ).fetchone()
        return _decode_causal_hypothesis(row) if row is not None else None

    def append_causal_hypothesis(
        self,
        *,
        episode_key: str,
        attempt_id: str,
        learning_object_id: str,
        cause_scope: str,
        statement: str,
        statement_normalized: str,
        error_event_id: str | None = None,
        mechanism: str | None = None,
        operation: str | None = None,
        target_ref: Mapping[str, Any] | None = None,
        applicability: Mapping[str, Any] | None = None,
        postdictive_claims: Sequence[Mapping[str, Any]] = (),
        evidence: Mapping[str, Any] | None = None,
        repair_class_id: str | None = None,
        repair_class_basis: str | None = None,
        repair_class_unresolved_reason: str | None = None,
        status: str = "candidate",
        generation_agent_run_id: str | None = None,
        model: str | None = None,
        hypothesis_id: str | None = None,
        provenance: Any = None,
        provenance_writer: str = "causal_hypothesis",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append a changed hypothesis version, or return the identical head.

        ``repair_class_basis`` / ``repair_class_unresolved_reason`` are part of
        the semantic identity: a hypothesis that stops being unmapped (because a
        repair was finally authored for it) is a CHANGED interpretation and earns
        a new version, exactly like a changed statement would.

        Diagnosis input provenance: ``provenance`` (a
        ``db.stores.write_provenance.WriteRecord``, or a function returning
        one, called only when a new version is appended, so an identical
        re-append, as on replay, reads no record) is what the statement was
        written from, recorded with the version in its transaction. Without
        one, a version that keeps its head's statement carries the head's
        record forward (the statement was copied from it); any other version
        records nothing and its statement stays held back from chat.
        """

        statement = statement.strip()
        if not statement:
            raise ValueError("causal hypothesis statement cannot be empty")
        if operation is not None and (
            not operation
            or not operation[0].isalpha()
            or not operation[0].islower()
            or any(
                not (character.islower() or character.isdigit() or character == "_")
                for character in operation
            )
        ):
            raise ValueError("causal hypothesis operation must be snake_case")
        semantic = {
            "attempt_id": attempt_id,
            "error_event_id": error_event_id,
            "learning_object_id": learning_object_id,
            "cause_scope": cause_scope,
            "statement": statement,
            "statement_normalized": statement_normalized,
            "mechanism": mechanism,
            "operation": operation,
            "target_ref": dict(target_ref) if target_ref is not None else None,
            "applicability": dict(applicability or {}),
            "postdictive_claims": [dict(value) for value in postdictive_claims],
            "evidence": dict(evidence or {}),
            "repair_class_id": repair_class_id,
            "repair_class_basis": repair_class_basis,
            "repair_class_unresolved_reason": repair_class_unresolved_reason,
            "status": status,
            "generation_agent_run_id": generation_agent_run_id,
            "model": model,
        }
        latest = self.latest_causal_hypothesis_for_episode(episode_key)
        if latest is not None and all(
            latest.get(key) == value for key, value in semantic.items()
        ):
            return latest
        if callable(provenance):
            provenance = provenance()
        version = int(latest.get("version") or 0) + 1 if latest is not None else 1
        hypothesis_id = hypothesis_id or new_ulid()
        with self.connection() as connection:
            from learnloop.db.stores.write_provenance import closure, record_text_write, stored_record

            carried = None
            if provenance is None and latest is not None and str(latest.get("statement") or "") == statement \
                    and stored_record(connection, "hypothesis", str(latest["id"])) is not None:
                head = ("hypothesis", str(latest["id"]))
                carried = closure(connection, [head], texts={head: statement})
            connection.execute(
                """
                INSERT INTO causal_hypotheses(
                  id, episode_key, version, supersedes_id, attempt_id,
                  error_event_id, learning_object_id, cause_scope, statement,
                  statement_normalized, mechanism, operation, target_ref_json,
                  applicability_json, postdictive_claims_json, evidence_json,
                  repair_class_id, repair_class_basis,
                  repair_class_unresolved_reason, status,
                  generation_agent_run_id, model, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?)
                """,
                (
                    hypothesis_id,
                    episode_key,
                    version,
                    latest.get("id") if latest is not None else None,
                    attempt_id,
                    error_event_id,
                    learning_object_id,
                    cause_scope,
                    statement,
                    statement_normalized,
                    mechanism,
                    operation,
                    _json(semantic["target_ref"])
                    if semantic["target_ref"] is not None
                    else None,
                    _json(semantic["applicability"]),
                    _json(semantic["postdictive_claims"]),
                    _json(semantic["evidence"]),
                    repair_class_id,
                    repair_class_basis,
                    repair_class_unresolved_reason,
                    status,
                    generation_agent_run_id,
                    model,
                    utc_now_iso(clock),
                ),
            )
            if provenance is not None or carried is not None:
                record_text_write(
                    connection, kind="hypothesis", record_id=hypothesis_id, text=statement,
                    writer=provenance_writer if provenance is not None else "causal_hypothesis_version",
                    record=provenance if provenance is not None else carried, clock=clock,
                )
            connection.commit()
        created = self.causal_hypothesis(hypothesis_id)
        assert created is not None
        return created

    def causal_hypothesis(self, hypothesis_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_hypotheses WHERE id = ?",
                (hypothesis_id,),
            ).fetchone()
        return _decode_causal_hypothesis(row) if row is not None else None

    def causal_hypotheses_for_attempt(
        self,
        attempt_id: str,
        *,
        latest_only: bool = True,
    ) -> list[dict[str, Any]]:
        latest_clause = (
            """
            AND h.version = (
              SELECT MAX(head.version)
                FROM causal_hypotheses head
               WHERE head.episode_key = h.episode_key
            )
            """
            if latest_only
            else ""
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT h.* FROM causal_hypotheses h
                 WHERE h.attempt_id = ? {latest_clause}
                 ORDER BY h.created_at, h.id
                """,
                (attempt_id,),
            ).fetchall()
        return [_decode_causal_hypothesis(row) for row in rows]

    def all_causal_hypotheses(
        self,
        *,
        latest_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Return causal-hypothesis rows across episodes in stable order.

        Migration and audit services need a vault-wide view, while ordinary
        runtime consumers should continue to use the attempt/LO-scoped reads.
        """

        latest_clause = (
            """
            WHERE h.version = (
              SELECT MAX(head.version)
                FROM causal_hypotheses head
               WHERE head.episode_key = h.episode_key
            )
            """
            if latest_only
            else ""
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT h.* FROM causal_hypotheses h
                {latest_clause}
                ORDER BY h.created_at, h.id
                """
            ).fetchall()
        return [_decode_causal_hypothesis(row) for row in rows]

    def causal_hypotheses_with_statement(
        self,
        statement_normalized: str,
        *,
        statuses: Sequence[str] = ("candidate", "validated"),
        cause_scope: str | None = "learner_state",
    ) -> list[dict[str, Any]]:
        """Episode heads, vault-wide, of one exact statement class (Slice 2 T1).

        By default only the heads that still stand as a learner belief: a
        head retired or demoted (the cause was refuted, e.g. "That's wrong")
        or scoped to the item, the grader or the session is not a recurrence
        of the learner's belief (second review F8).
        """

        status_list = tuple(statuses)
        if not status_list:
            return []
        placeholders = ",".join("?" for _ in status_list)
        scope_clause = "AND h.cause_scope = ?" if cause_scope is not None else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT h.* FROM causal_hypotheses h
                 WHERE h.statement_normalized = ?
                   AND h.status IN ({placeholders})
                   {scope_clause}
                   AND h.version = (
                     SELECT MAX(head.version)
                       FROM causal_hypotheses head
                      WHERE head.episode_key = h.episode_key
                   )
                 ORDER BY h.created_at, h.id
                """,
                (statement_normalized, *status_list, *((cause_scope,) if cause_scope is not None else ())),
            ).fetchall()
        return [_decode_causal_hypothesis(row) for row in rows]

    def causal_hypotheses_with_operations(
        self, *, latest_only: bool = True, require_operation: bool = True
    ) -> list[dict[str, Any]]:
        """Hypothesis heads for taxonomy minting.

        ``require_operation`` exists because Aug A2 demoted the operation string
        from grouping key to human-readable label: a hypothesis that carries a
        repair class and postdictive claims but no operation string is fully
        clusterable under the new key, and filtering it out would have hidden it
        behind the label it no longer depends on.
        """

        operation_clause = (
            "h.operation IS NOT NULL" if require_operation else "1 = 1"
        )
        latest_clause = (
            """
            AND h.version = (
              SELECT MAX(head.version)
                FROM causal_hypotheses head
               WHERE head.episode_key = h.episode_key
            )
            """
            if latest_only
            else ""
        )
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT h.* FROM causal_hypotheses h
                 WHERE {operation_clause} {latest_clause}
                 ORDER BY h.operation, h.created_at, h.id
                """
            ).fetchall()
        return [_decode_causal_hypothesis(row) for row in rows]

    def insert_missing_vocabulary_notes(
        self,
        notes: Sequence[Mapping[str, Any]],
        *,
        clock: Clock | None = None,
    ) -> int:
        """Append missing-vocabulary notes (migration 134, Aug A5).

        Ids are content-addressed by the caller, so re-recording an abstention
        already captured is a no-op.  Returns the number of NEW notes.
        """

        now = utc_now_iso(clock)
        written = 0
        with self.connection() as connection:
            for note in notes:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO missing_vocabulary_notes(
                      id, source, abstention_reason, learning_object_id,
                      practice_item_id, attempt_id, error_event_id, criterion_id,
                      trace_json, item_context_json, selected_repair_class_id,
                      repair_equivalence_id, grading_prompt_version,
                      decision_policy_version, repair_policy_version,
                      grader_model, grader_provider, grader_provider_revision,
                      agent_run_id, note_version, detail_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(note["id"]),
                        str(note["source"]),
                        str(note["abstention_reason"]),
                        note.get("learning_object_id"),
                        note.get("practice_item_id"),
                        note.get("attempt_id"),
                        note.get("error_event_id"),
                        note.get("criterion_id"),
                        _json(dict(note.get("trace") or {})),
                        _json(dict(note.get("item_context") or {})),
                        note.get("selected_repair_class_id"),
                        note.get("repair_equivalence_id"),
                        note.get("grading_prompt_version"),
                        note.get("decision_policy_version"),
                        note.get("repair_policy_version"),
                        note.get("grader_model"),
                        note.get("grader_provider"),
                        note.get("grader_provider_revision"),
                        note.get("agent_run_id"),
                        str(note["note_version"]),
                        _json(dict(note.get("detail") or {})),
                        now,
                    ),
                )
                written += int(cursor.rowcount or 0)
            connection.commit()
        return written

    def missing_vocabulary_notes(
        self,
        *,
        source: str | None = None,
        learning_object_id: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if source:
            clauses.append("source = ?")
            params.append(source)
        if learning_object_id:
            clauses.append("learning_object_id = ?")
            params.append(learning_object_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        suffix = ""
        if limit is not None:
            suffix = " LIMIT ?"
            params.append(int(limit))
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM missing_vocabulary_notes{where}
                 ORDER BY created_at, id{suffix}
                """,
                tuple(params),
            ).fetchall()
        decoded: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            for field in ("trace", "item_context", "detail"):  # noqa: F402  a local loop variable; this function never calls dataclasses.field()
                payload[field] = _loads(payload.pop(f"{field}_json"), None)
            decoded.append(payload)
        return decoded

    def record_causal_repair_class_definitions(
        self,
        definitions: Sequence[Mapping[str, Any]],
        *,
        clock: Clock | None = None,
    ) -> int:
        """Persist repair-class definitions durably (migration 133, Aug A2).

        The definition previously existed only inside the diagnosis receipt in
        ``attempt_debug_payloads``, which replay rebuilds.  The mechanism
        taxonomy keys on it, so it has to survive a rebuild.  Rows are
        content-addressed on ``repair_class_id``; re-recording an identical
        definition is a no-op, which is what makes this safe to call on every
        materialization.
        """

        now = utc_now_iso(clock)
        recorded = 0
        with self.connection() as connection:
            for definition in definitions:
                repair_class_id = str(definition["repair_class_id"])
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO causal_repair_class_definitions(
                      repair_class_id, repair_equivalence_id, episode_id,
                      operator, repair_policy_version, target_refs_json,
                      preserve_refs_json, expected_minutes,
                      answer_reveal_budget, definition_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        repair_class_id,
                        str(definition["repair_equivalence_id"]),
                        str(definition.get("episode_id") or ""),
                        str(definition.get("operator") or ""),
                        str(definition.get("repair_policy_version") or ""),
                        _json(list(definition.get("target_refs") or [])),
                        _json(list(definition.get("preserve_refs") or [])),
                        definition.get("expected_minutes"),
                        float(definition.get("answer_reveal_budget") or 0.0),
                        _json(dict(definition.get("definition") or {})),
                        now,
                    ),
                )
                recorded += int(cursor.rowcount or 0)
            connection.commit()
        return recorded

    def causal_repair_class_definitions(
        self, repair_class_ids: Sequence[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Durable repair-class definitions keyed by ``repair_class_id``."""

        clause = ""
        params: tuple[Any, ...] = ()
        ids = [str(value) for value in repair_class_ids or [] if value]
        if repair_class_ids is not None:
            if not ids:
                return {}
            placeholders = ", ".join("?" for _ in ids)
            clause = f" WHERE repair_class_id IN ({placeholders})"
            params = tuple(ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM causal_repair_class_definitions{clause}",
                params,
            ).fetchall()
        decoded: dict[str, dict[str, Any]] = {}
        for row in rows:
            payload = dict(row)
            for field in ("target_refs", "preserve_refs", "definition"):  # noqa: F402  a local loop variable; this function never calls dataclasses.field()
                payload[field] = _loads(payload.pop(f"{field}_json"), None)
            decoded[str(payload["repair_class_id"])] = payload
        return decoded

    def retired_causal_mechanism_taxonomy_versions(self) -> dict[str, dict[str, Any]]:
        """Taxonomy versions withdrawn from new receipts, keyed by version id."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM causal_mechanism_taxonomy_retirements
                 ORDER BY retired_at, taxonomy_version_id
                """
            ).fetchall()
        return {str(row["taxonomy_version_id"]): dict(row) for row in rows}

    def retire_causal_mechanism_taxonomy_version(
        self,
        taxonomy_version_id: str,
        *,
        reason: str,
        clock: Clock | None = None,
    ) -> bool:
        """Withdraw a taxonomy version from NEW receipts (migration 133).

        Pinned reads keep resolving, because a receipt that was labelled by this
        taxonomy has to replay against it.  Returns False when the version was
        already retired — retirement is append-only and idempotent.
        """

        if not str(reason).strip():
            raise ValueError("taxonomy retirement requires a reason")
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO causal_mechanism_taxonomy_retirements(
                  taxonomy_version_id, reason, retired_at
                )
                VALUES (?, ?, ?)
                """,
                (taxonomy_version_id, str(reason), utc_now_iso(clock)),
            )
            connection.commit()
            return bool(cursor.rowcount)

    def insert_causal_mechanism_taxonomy_version(
        self,
        *,
        taxonomy_version_id: str,
        algorithm: str,
        min_cluster_size: int,
        source_head_hash: str,
        status: str,
        taxonomy: Mapping[str, Any],
        assignments: Sequence[Mapping[str, str]],
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Insert an immutable taxonomy snapshot and its hypothesis assignments."""

        if status not in {"draft", "active"}:
            raise ValueError("taxonomy status must be draft or active")
        now = utc_now_iso(clock)
        encoded = _json(dict(taxonomy))
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO causal_mechanism_taxonomy_versions(
                  id, algorithm, min_cluster_size, source_head_hash, status,
                  taxonomy_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    taxonomy_version_id,
                    algorithm,
                    min_cluster_size,
                    source_head_hash,
                    status,
                    encoded,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM causal_mechanism_taxonomy_versions
                 WHERE id = ?
                """,
                (taxonomy_version_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("taxonomy version insert did not persist")
            existing = _decode_causal_mechanism_taxonomy(row)
            expected = {
                "algorithm": algorithm,
                "min_cluster_size": min_cluster_size,
                "source_head_hash": source_head_hash,
                "status": status,
                "taxonomy": dict(taxonomy),
            }
            if any(existing.get(key) != value for key, value in expected.items()):
                raise ValueError(
                    "content-addressed taxonomy id refers to different content"
                )
            for assignment in assignments:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO causal_mechanism_taxonomy_assignments(
                      taxonomy_version_id, hypothesis_id, mechanism_id,
                      created_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        taxonomy_version_id,
                        str(assignment["hypothesis_id"]),
                        str(assignment["mechanism_id"]),
                        now,
                    ),
                )
            connection.commit()
        created = self.causal_mechanism_taxonomy_version(
            taxonomy_version_id, include_assignments=True
        )
        assert created is not None
        return created

    def causal_mechanism_taxonomy_version(
        self,
        taxonomy_version_id: str,
        *,
        include_assignments: bool = False,
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM causal_mechanism_taxonomy_versions
                 WHERE id = ?
                """,
                (taxonomy_version_id,),
            ).fetchone()
            if row is None:
                return None
            payload = _decode_causal_mechanism_taxonomy(row)
            if include_assignments:
                assignment_rows = connection.execute(
                    """
                    SELECT hypothesis_id, mechanism_id
                      FROM causal_mechanism_taxonomy_assignments
                     WHERE taxonomy_version_id = ?
                     ORDER BY hypothesis_id
                    """,
                    (taxonomy_version_id,),
                ).fetchall()
                payload["assignments"] = [
                    dict(value) for value in assignment_rows
                ]
        return payload

    def latest_active_causal_mechanism_taxonomy(
        self,
    ) -> dict[str, Any] | None:
        """The taxonomy a NEW receipt may adopt.

        Retired versions (migration 133) are excluded here and only here: a
        receipt that already pinned one still resolves it by id, because replay
        has to see the taxonomy that actually labelled it.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT v.* FROM causal_mechanism_taxonomy_versions v
                 WHERE v.status = 'active'
                   AND NOT EXISTS (
                     SELECT 1 FROM causal_mechanism_taxonomy_retirements r
                      WHERE r.taxonomy_version_id = v.id
                   )
                 ORDER BY v.created_at DESC, v.id DESC
                 LIMIT 1
                """
            ).fetchone()
        return (
            _decode_causal_mechanism_taxonomy(row)
            if row is not None
            else None
        )

    def causal_mechanism_assignment(
        self,
        taxonomy_version_id: str,
        hypothesis_id: str,
    ) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT mechanism_id
                  FROM causal_mechanism_taxonomy_assignments
                 WHERE taxonomy_version_id = ? AND hypothesis_id = ?
                """,
                (taxonomy_version_id, hypothesis_id),
            ).fetchone()
        return str(row["mechanism_id"]) if row is not None else None

    # -- P2 causal probe coherence ---------------------------------------

    def insert_causal_blind_prediction_bundle(
        self,
        *,
        bundle_id: str,
        hypothesis_id: str,
        hypothesis_version: int,
        practice_item_id: str,
        input_hash: str,
        predictions: Mapping[str, Any],
        model_revision: str,
        outcome_schema_version: str,
        blind_input_contract_version: str | None = None,
        generation_agent_run_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Insert one content-addressed, observation-blind prediction bundle."""

        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO causal_blind_prediction_bundles(
                  id, hypothesis_id, hypothesis_version, practice_item_id,
                  input_hash, predictions_json, generated_without_observation,
                  model_revision, outcome_schema_version,
                  blind_input_contract_version, generation_agent_run_id,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """,
                (
                    bundle_id,
                    hypothesis_id,
                    hypothesis_version,
                    practice_item_id,
                    input_hash,
                    _json(dict(predictions)),
                    model_revision,
                    outcome_schema_version,
                    blind_input_contract_version,
                    generation_agent_run_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        bundle = self.causal_blind_prediction_bundle(bundle_id)
        assert bundle is not None
        return bundle

    def causal_blind_prediction_bundle(
        self, bundle_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM causal_blind_prediction_bundles WHERE id = ?
                """,
                (bundle_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["predictions"] = _loads(
            payload.pop("predictions_json"), {}
        )
        payload["generated_without_observation"] = bool(
            payload["generated_without_observation"]
        )
        return payload

    def causal_blind_prediction_bundles(
        self,
        *,
        practice_item_id: str | None = None,
        hypothesis_ids: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        wanted = [str(value) for value in hypothesis_ids or []]
        clauses: list[str] = []
        values: list[Any] = []
        if practice_item_id is not None:
            clauses.append("practice_item_id = ?")
            values.append(practice_item_id)
        if wanted:
            clauses.append(
                "hypothesis_id IN ("
                + ",".join("?" for _ in wanted)
                + ")"
            )
            values.extend(wanted)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id FROM causal_blind_prediction_bundles
                {where}
                ORDER BY created_at, id
                """,
                tuple(values),
            ).fetchall()
        return [
            bundle
            for row in rows
            if (
                bundle := self.causal_blind_prediction_bundle(str(row["id"]))
            )
            is not None
        ]

    def insert_probe_manipulation_audit(
        self,
        *,
        audit_id: str,
        source_kind: str,
        source_item_id: str,
        candidate_item_id: str,
        contract: Mapping[str, Any],
        structural_diff: Mapping[str, Any],
        adversarial_review: Mapping[str, Any] | None,
        status: str,
        generation_agent_run_id: str | None = None,
        reviewer_agent_run_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO probe_manipulation_audits(
                  id, source_kind, source_item_id, candidate_item_id,
                  contract_json, structural_diff_json,
                  adversarial_review_json, status,
                  generation_agent_run_id, reviewer_agent_run_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    source_kind,
                    source_item_id,
                    candidate_item_id,
                    _json(dict(contract)),
                    _json(dict(structural_diff)),
                    (
                        _json(dict(adversarial_review))
                        if adversarial_review is not None
                        else None
                    ),
                    status,
                    generation_agent_run_id,
                    reviewer_agent_run_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        audit = self.probe_manipulation_audit(audit_id)
        assert audit is not None
        return audit

    def probe_manipulation_audit(
        self, audit_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM probe_manipulation_audits WHERE id = ?",
                (audit_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        for key in ("contract", "structural_diff", "adversarial_review"):
            payload[key] = _loads(payload.pop(f"{key}_json"), None)
        return payload

    def insert_causal_probe_candidate(
        self,
        *,
        candidate_id: str,
        factor_id: str,
        practice_item_id: str,
        hypothesis_set_id: str,
        manipulation_audit_id: str,
        measurement_contract: Mapping[str, Any],
        blind_bundle_ids: Sequence[str],
        discrimination: Mapping[str, Any] | None = None,
        blind_input_contract_version: str | None = None,
        status: str = "candidate",
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO causal_probe_candidates(
                  id, factor_id, practice_item_id, hypothesis_set_id,
                  manipulation_audit_id, measurement_contract_json,
                  blind_bundle_ids_json, discrimination_json,
                  blind_input_contract_version, status,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    factor_id,
                    practice_item_id,
                    hypothesis_set_id,
                    manipulation_audit_id,
                    _json(dict(measurement_contract)),
                    _json(list(blind_bundle_ids)),
                    (
                        _json(dict(discrimination))
                        if discrimination is not None
                        else None
                    ),
                    blind_input_contract_version,
                    status,
                    now,
                    now,
                ),
            )
            if cursor.rowcount:
                connection.execute(
                    """
                    INSERT INTO causal_probe_candidate_events(
                      id, candidate_id, seq, from_status, to_status, actor,
                      reason, created_at
                    )
                    VALUES (?, ?, 1, NULL, ?, NULL, ?, ?)
                    """,
                    (
                        new_ulid(),
                        candidate_id,
                        status,
                        "candidate_created",
                        now,
                    ),
                )
            connection.commit()
        candidate = self.causal_probe_candidate(candidate_id)
        assert candidate is not None
        return candidate

    def causal_probe_candidate(
        self, candidate_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_probe_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["measurement_contract"] = _loads(
            payload.pop("measurement_contract_json"), {}
        )
        payload["blind_bundle_ids"] = _loads(
            payload.pop("blind_bundle_ids_json"), []
        )
        payload["discrimination"] = _loads(
            payload.pop("discrimination_json"), None
        )
        return payload

    def update_causal_probe_candidate(
        self,
        candidate_id: str,
        *,
        status: str,
        discrimination: Mapping[str, Any] | None = None,
        reviewer: str | None = None,
        review_reason: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        current = self.causal_probe_candidate(candidate_id)
        if current is None:
            return None
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE causal_probe_candidates
                   SET status = ?,
                       discrimination_json = COALESCE(?, discrimination_json),
                       reviewer = COALESCE(?, reviewer),
                       review_reason = COALESCE(?, review_reason),
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    status,
                    (
                        _json(dict(discrimination))
                        if discrimination is not None
                        else None
                    ),
                    reviewer,
                    review_reason,
                    utc_now_iso(clock),
                    candidate_id,
                ),
            )
            if cursor.rowcount:
                sequence_row = connection.execute(
                    """
                    SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq
                      FROM causal_probe_candidate_events
                     WHERE candidate_id = ?
                    """,
                    (candidate_id,),
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO causal_probe_candidate_events(
                      id, candidate_id, seq, from_status, to_status, actor,
                      reason, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_ulid(),
                        candidate_id,
                        int(sequence_row["next_seq"]),
                        current["status"],
                        status,
                        reviewer,
                        review_reason,
                        utc_now_iso(clock),
                    ),
                )
            connection.commit()
        return (
            self.causal_probe_candidate(candidate_id)
            if cursor.rowcount
            else None
        )

    def causal_probe_candidate_events(
        self, candidate_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM causal_probe_candidate_events
                 WHERE candidate_id = ?
                 ORDER BY seq
                """,
                (candidate_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_causal_activity_classification(
        self,
        *,
        attempt_id: str,
        contamination_class: str,
        near_clone: bool = False,
        closes_pre_intervention_segment: bool | None = None,
        eligible_for_fsrs: bool | None = None,
        eligible_for_certification: bool | None = None,
        near_clone_basis: str | None = None,
        source: str = "unknown",
        detail: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one classification event; NEVER raises on a conflict (§4.2).

        Classification writes happen on the attempt hot path and several honest
        writers can disagree about the same attempt (a primed probe is both a
        repair activity and a diagnostic administration). Both facts are
        recorded; :meth:`causal_activity_classification` derives the winner by
        ``CONTAMINATION_PRECEDENCE``. Restating an identical fact is a no-op, so
        replay does not grow the log.

        The derived flags are recomputed from the policy matrix, so the explicit
        ``closes_pre_intervention_segment`` / ``eligible_*`` arguments are
        accepted for backwards compatibility but are not the authority.
        """

        policy = policy_for_class(contamination_class, near_clone=bool(near_clone))
        with self.connection() as connection:
            # Serialize the read-next-sequence/write pair. A deferred SELECT
            # allowed two connections to observe the same MAX(seq); the later
            # ``INSERT OR IGNORE`` then silently discarded one honest writer on
            # the sequence uniqueness conflict. BEGIN IMMEDIATE acquires the
            # reserved writer lock before reading MAX. If a caller already owns
            # this connection's transaction (the pinned case), its transaction
            # is the serialization boundary and a real uniqueness error remains
            # visible because the INSERT below is deliberately not OR IGNORE.
            if not connection.in_transaction:
                connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT id
                  FROM causal_activity_classification_events
                 WHERE attempt_id = ?
                   AND source = ?
                   AND contamination_class = ?
                   AND near_clone = ?
                """,
                (
                    attempt_id,
                    source,
                    policy.contamination_class,
                    int(policy.near_clone),
                ),
            ).fetchone()
            if existing is not None:
                connection.commit()
                result = self.causal_activity_classification(attempt_id)
                assert result is not None
                return result
            next_seq = connection.execute(
                """
                SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq
                  FROM causal_activity_classification_events
                 WHERE attempt_id = ?
                """,
                (attempt_id,),
            ).fetchone()["next_seq"]
            connection.execute(
                """
                INSERT INTO causal_activity_classification_events(
                  id, attempt_id, seq, contamination_class, near_clone,
                  near_clone_basis, closes_pre_intervention_segment,
                  eligible_for_fsrs, eligible_for_certification, source,
                  policy_version, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_ulid(),
                    attempt_id,
                    int(next_seq),
                    policy.contamination_class,
                    int(policy.near_clone),
                    near_clone_basis,
                    int(policy.closes_pre_intervention_segment),
                    int(policy.eligible_for_fsrs),
                    int(policy.eligible_for_certification),
                    source,
                    CAUSAL_ACTIVITY_POLICY_VERSION,
                    _json(dict(detail or {})),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        result = self.causal_activity_classification(attempt_id)
        assert result is not None
        return result

    def causal_activity_classification_events(
        self, attempt_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM causal_activity_classification_events
                 WHERE attempt_id = ?
                 ORDER BY seq
                """,
                (attempt_id,),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            events.append(_decode_causal_activity_event(row))
        return events

    def causal_activity_classification(
        self, attempt_id: str
    ) -> dict[str, Any] | None:
        """The current classification, DERIVED from the event log (§4.2).

        Most contaminated class wins; within it near_clone fails closed (any
        writer asserting a near clone wins). The eligibility flags are always
        recomputed from the policy matrix so a stored row can never disagree
        with the single authority.
        """

        events = self.causal_activity_classification_events(attempt_id)
        if not events:
            return None
        return _resolve_causal_activity_classification(attempt_id, events)

    def all_causal_activity_classifications(self) -> dict[str, dict[str, Any]]:
        """Resolve every attempt's current activity policy in one DB read.

        Canonical projection and the learner-facing Demonstrated timeline both
        replay the whole attempt ledger. Supplying their policy inputs in the
        same bulk snapshot prevents their eligibility check from reintroducing
        a per-attempt query and guarantees both folds resolve conflicting event
        histories identically.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM causal_activity_classification_events
                ORDER BY attempt_id, seq
                """
            ).fetchall()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            event = _decode_causal_activity_event(row)
            grouped[str(event["attempt_id"])].append(event)
        return {
            attempt_id: _resolve_causal_activity_classification(attempt_id, events)
            for attempt_id, events in grouped.items()
        }

    # -- discriminating observations (migration 130) ------------------------

    def insert_causal_discriminating_observation(
        self,
        *,
        observation_id: str,
        factor_id: str,
        presentation_id: str,
        hypothesis_set_id: str,
        outcome: str,
        classified_as: Sequence[str],
        supports_open_set: bool,
        feature_source: str,
        observed_features: Mapping[str, Any],
        declared_keys_observed: bool,
        admitted: bool,
        admission_reason: str,
        support_scores: Mapping[str, Any],
        resolved_factor: bool,
        detail: Mapping[str, Any],
        decision_policy_version: str,
        formula_version: str,
        blind_bundle_ids: Sequence[str] = (),
        attempt_id: str | None = None,
        probe_attempt_id: str | None = None,
        candidate_id: str | None = None,
        support_authority: str | None = None,
        channel: str | None = None,
        admissible_as_independent: bool | None = None,
        inadmissibility_reason: str | None = None,
        contaminating_reveal_event_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one discriminating-observation receipt (idempotent on id).

        ``observation_id`` is the content hash of the frozen inputs, so
        classifying the same pinned probe against the same observed features
        twice records once; a DIFFERENT feature vector on the same presentation
        appends a second row, because the disagreement is itself the signal.
        """

        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO causal_discriminating_observations(
                  id, factor_id, attempt_id, probe_attempt_id, presentation_id,
                  hypothesis_set_id, candidate_id, blind_bundle_ids_json,
                  outcome, classified_as_json, supports_open_set,
                  feature_source, observed_features_json,
                  declared_keys_observed, admitted, admission_reason,
                  support_authority, support_scores_json, resolved_factor,
                  detail_json, decision_policy_version, formula_version,
                  created_at, channel, admissible_as_independent,
                  inadmissibility_reason, contaminating_reveal_event_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    factor_id,
                    attempt_id,
                    probe_attempt_id,
                    presentation_id,
                    hypothesis_set_id,
                    candidate_id,
                    _json([str(value) for value in blind_bundle_ids]),
                    outcome,
                    _json([str(value) for value in classified_as]),
                    int(bool(supports_open_set)),
                    feature_source,
                    _json(dict(observed_features)),
                    int(bool(declared_keys_observed)),
                    int(bool(admitted)),
                    admission_reason,
                    support_authority,
                    _json(dict(support_scores)),
                    int(bool(resolved_factor)),
                    _json(dict(detail)),
                    decision_policy_version,
                    formula_version,
                    utc_now_iso(clock),
                    channel,
                    (
                        None
                        if admissible_as_independent is None
                        else int(bool(admissible_as_independent))
                    ),
                    inadmissibility_reason,
                    contaminating_reveal_event_id,
                ),
            )
            connection.commit()
        record = self.causal_discriminating_observation(observation_id)
        assert record is not None
        return record

    def causal_discriminating_observation(
        self, observation_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_discriminating_observations WHERE id = ?",
                (observation_id,),
            ).fetchone()
        return (
            _decode_causal_discriminating_observation(row)
            if row is not None
            else None
        )

    def causal_discriminating_observations(
        self,
        *,
        factor_id: str | None = None,
        attempt_id: str | None = None,
        presentation_id: str | None = None,
        admitted_only: bool = False,
        probe_channel_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Observation receipts, oldest first.

        ``probe_channel_only`` restricts to rows produced by a blind-bundle
        classification of an administered probe — ``channel IS NULL`` (every
        row written before migration 155) or the explicit probe channel. Any
        consumer whose denominator is "probes administered" must pass it, or a
        learner-question-embedded prediction inflates a probe metric.
        """

        clauses: list[str] = []
        values: list[Any] = []
        if probe_channel_only:
            clauses.append("(channel IS NULL OR channel = ?)")
            values.append(OBSERVATION_CHANNEL_BLIND_PROBE)
        if factor_id is not None:
            clauses.append("factor_id = ?")
            values.append(factor_id)
        if attempt_id is not None:
            clauses.append("attempt_id = ?")
            values.append(attempt_id)
        if presentation_id is not None:
            clauses.append("presentation_id = ?")
            values.append(presentation_id)
        if admitted_only:
            clauses.append("admitted = 1")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM causal_discriminating_observations
                {where}
                ORDER BY created_at, id
                """,
                values,
            ).fetchall()
        return [_decode_causal_discriminating_observation(row) for row in rows]

    def set_unresolved_cause_hypothesis_refs(
        self,
        factor_id: str,
        refs: Sequence[Mapping[str, Any]],
        *,
        clock: Clock | None = None,
    ) -> None:
        """Replace P0 duplicated candidate prose with P1 hypothesis references."""

        encoded = _json([dict(value) for value in refs])
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE unresolved_cause_factors
                   SET candidate_causes_json = ?, updated_at = ?
                 WHERE id = ? AND status = 'open'
                   AND candidate_causes_json != ?
                """,
                (encoded, utc_now_iso(clock), factor_id, encoded),
            )
            connection.commit()

    def insert_unresolved_cause_factor(
        self,
        *,
        attempt_id: str,
        candidate_causes: Any,
        algorithm_version: str,
        observation_id: str | None = None,
        status: str = "open",
        clock: Clock | None = None,
    ) -> str:
        now = utc_now_iso(clock)
        factor_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO unresolved_cause_factors(
                  id, attempt_id, observation_id, candidate_causes_json,
                  status, resolution_observation_ids_json, algorithm_version,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    factor_id,
                    attempt_id,
                    observation_id,
                    _json(candidate_causes),
                    status,
                    None,
                    algorithm_version,
                    now,
                    now,
                ),
            )
            connection.commit()
        return factor_id

    def refresh_open_unresolved_cause_candidates(
        self,
        observation_id: str,
        candidate_causes: Any,
        *,
        clock: Clock | None = None,
    ) -> bool:
        """Replace an OPEN factor's candidate set when it differs (Slice 1 M2).

        Only the canonical projection calls this, after a blind attempt's
        diagnosis lands; closed factors keep their history.
        """

        encoded = _json(candidate_causes)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE unresolved_cause_factors
                SET candidate_causes_json = ?, updated_at = ?
                WHERE observation_id = ? AND status = 'open'
                  AND candidate_causes_json IS NOT ?
                """,
                (encoded, utc_now_iso(clock), observation_id, encoded),
            )
            connection.commit()
            return cursor.rowcount > 0

    def open_unresolved_cause_observation_ids(self) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT observation_id FROM unresolved_cause_factors
                WHERE status = 'open' AND observation_id IS NOT NULL
                """
            ).fetchall()
        return {str(row["observation_id"]) for row in rows}

    def open_unresolved_cause_factor_attempts(self) -> dict[str, str]:
        """Each open observation-keyed factor's attempt id, by observation id."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT observation_id, attempt_id FROM unresolved_cause_factors
                WHERE status = 'open' AND observation_id IS NOT NULL
                """
            ).fetchall()
        return {str(row["observation_id"]): str(row["attempt_id"]) for row in rows}

    def unresolved_cause_observation_ids(self) -> set[str]:
        """Observation ids the projection sync must NOT (re-)insert a factor for.

        Open or learner-resolved factors, plus any factor closed with a
        bounded-deferral ``resolution_kind`` (migration 148) whatever its
        status: a factor the deferral machinery labeled repair_confirmed /
        escalated_unrepaired / expired_unengaged stays closed even while its
        failure still appears in the projection — re-inserting it would undo
        the deferral bound on the next projection pass.  A factor the sync
        itself retired (no ``resolution_kind``) remains re-insertable when its
        failure reappears, which is the pre-existing reconciliation contract.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT observation_id FROM unresolved_cause_factors
                WHERE observation_id IS NOT NULL
                  AND (status IN ('open', 'resolved')
                       OR resolution_kind IS NOT NULL)
                """
            ).fetchall()
        return {str(row["observation_id"]) for row in rows}

    def unresolved_cause_factors_for_attempt(
        self, attempt_id: str, *, status: str = "open"
    ) -> list[dict[str, Any]]:
        """Open unresolved-cause factors for an attempt (the §9.6 diagnostic card).

        Each row's ``candidate_causes`` is decoded to the list
        ``[{"facet", "capability"}, ...]`` — the ambiguous cause set a short
        diagnostic would discriminate.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT f.id, f.attempt_id, f.observation_id,
                       f.candidate_causes_json, f.status, f.algorithm_version,
                       f.created_at, f.updated_at,
                       r.id AS self_report_id, r.response AS self_report_response,
                       r.candidate_index AS self_report_candidate_index,
                       r.created_at AS self_report_created_at
                FROM unresolved_cause_factors f
                LEFT JOIN causal_attribution_reports r
                  ON r.id = (
                    SELECT latest.id
                    FROM causal_attribution_reports latest
                    WHERE latest.factor_id = f.id
                      -- An answer to an eliciting question is the learner's
                      -- account, not their verdict on the diagnosis: it never
                      -- takes the card's one tap or reads as a contest.
                      AND latest.response != 'eliciting_response'
                    ORDER BY latest.created_at DESC, latest.id DESC
                    LIMIT 1
                  )
                WHERE f.attempt_id = ? AND f.status = ?
                ORDER BY f.created_at, f.id
                """,
                (attempt_id, status),
            ).fetchall()
        factors: list[dict[str, Any]] = []
        for row in rows:
            candidate_causes = _loads(row["candidate_causes_json"], [])
            factors.append(
                {
                    "id": row["id"],
                    "attempt_id": row["attempt_id"],
                    "observation_id": row["observation_id"],
                    "candidate_causes": self._presented_causal_candidates(
                        candidate_causes
                    ),
                    "status": row["status"],
                    "algorithm_version": row["algorithm_version"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "self_report": (
                        {
                            "id": row["self_report_id"],
                            "response": row["self_report_response"],
                            "candidate_index": row["self_report_candidate_index"],
                            "created_at": row["self_report_created_at"],
                        }
                        if row["self_report_id"] is not None
                        else None
                    ),
                }
            )
        return factors

    def _presented_causal_candidates(
        self, candidates: Sequence[Any]
    ) -> list[dict[str, Any]]:
        """Hydrate P1 refs for presentation without duplicating stored claims."""

        presented: list[dict[str, Any]] = []
        for raw in candidates:
            if not isinstance(raw, Mapping):
                continue
            candidate = dict(raw)
            hypothesis_id = candidate.get("hypothesis_id")
            if not hypothesis_id or set(candidate) - {
                "hypothesis_id",
                "version",
                "open_set",
            }:
                presented.append(candidate)
                continue
            hypothesis = self.causal_hypothesis(str(hypothesis_id))
            if hypothesis is None:
                presented.append(candidate)
                continue
            target_ref = hypothesis.get("target_ref")
            presented.append(
                {
                    **candidate,
                    "statement": hypothesis["statement"],
                    "cause_scope": hypothesis["cause_scope"],
                    "target_ref": target_ref,
                    "mechanism": hypothesis.get("mechanism"),
                    "operation": hypothesis.get("operation"),
                    "repair_class_id": hypothesis.get("repair_class_id"),
                    # Provenance rides along so a cause-set classifier can report
                    # WHY a mapping is missing without a second query.
                    "repair_class_basis": hypothesis.get("repair_class_basis"),
                    "repair_class_unresolved_reason": hypothesis.get(
                        "repair_class_unresolved_reason"
                    ),
                    **(
                        {
                            "facet": target_ref.get("facet_id"),
                            "capability": target_ref.get("capability"),
                        }
                        if isinstance(target_ref, Mapping)
                        and target_ref.get("kind") == "facet_capability"
                        else {}
                    ),
                }
            )
        return presented

    def open_unresolved_cause_factors(
        self, *, learning_object_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Open positional-ambiguity factors, optionally one learning object.

        Repair blocking is a per-learning-object question (causal spec §3.9);
        scanning every open factor on every repair start is both slow and wrong
        in intent, so callers pass the scope they actually mean.
        """

        clause = ""
        values: tuple[Any, ...] = ()
        if learning_object_id is not None:
            clause = """
                  AND EXISTS (
                        SELECT 1 FROM causal_hypotheses h
                         WHERE h.attempt_id = unresolved_cause_factors.attempt_id
                           AND h.learning_object_id = ?
                      )
            """
            values = (learning_object_id,)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, attempt_id, observation_id, candidate_causes_json,
                       status, algorithm_version, created_at, updated_at
                FROM unresolved_cause_factors
                WHERE status = 'open'
                {clause}
                ORDER BY created_at, id
                """,
                values,
            ).fetchall()
        return [
            {
                "id": row["id"],
                "attempt_id": row["attempt_id"],
                "observation_id": row["observation_id"],
                "candidate_causes": self._presented_causal_candidates(
                    _loads(row["candidate_causes_json"], [])
                ),
                "status": row["status"],
                "algorithm_version": row["algorithm_version"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def unresolved_cause_factors(
        self, *, status: str | None = "open"
    ) -> list[dict[str, Any]]:
        """Vault-wide unresolved-cause factors (readiness reads; EVSI-2).

        ``status=None`` returns every factor. Rows carry decoded
        ``candidate_causes`` exactly as :meth:`unresolved_cause_factor` does.
        """

        clause = "" if status is None else "WHERE status = ?"
        params: tuple[Any, ...] = () if status is None else (status,)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id FROM unresolved_cause_factors
                {clause}
                ORDER BY created_at, id
                """,
                params,
            ).fetchall()
        return [
            factor
            for row in rows
            if (factor := self.unresolved_cause_factor(str(row["id"]))) is not None
        ]

    def unresolved_cause_factor(self, factor_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT id, attempt_id, observation_id, candidate_causes_json,
                       status, resolution_observation_ids_json, resolution_kind,
                       resolution_detail_json, algorithm_version,
                       created_at, updated_at
                FROM unresolved_cause_factors
                WHERE id = ?
                """,
                (factor_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["candidate_causes"] = self._presented_causal_candidates(
            _loads(payload.pop("candidate_causes_json"), [])
        )
        payload["resolution_observation_ids"] = _loads(
            payload.pop("resolution_observation_ids_json"), []
        )
        payload["resolution_detail"] = _loads(
            payload.pop("resolution_detail_json"), None
        )
        return payload

    def resolve_unresolved_cause_factor(
        self,
        factor_id: str,
        *,
        resolution_observation_ids: Iterable[str],
        clock: Clock | None = None,
    ) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE unresolved_cause_factors
                   SET status = 'resolved',
                       resolution_observation_ids_json = ?,
                       updated_at = ?
                 WHERE id = ? AND status = 'open'
                """,
                (
                    _json(list(dict.fromkeys(str(value) for value in resolution_observation_ids))),
                    utc_now_iso(clock),
                    factor_id,
                ),
            )
            connection.commit()
        return cursor.rowcount > 0

    def insert_causal_attribution_report(
        self,
        *,
        factor_id: str,
        attempt_id: str,
        response: str,
        candidate_index: int | None,
        payload: Mapping[str, Any] | None = None,
        report_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        report_id = report_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO causal_attribution_reports(
                  id, factor_id, attempt_id, response, candidate_index,
                  payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    factor_id,
                    attempt_id,
                    response,
                    candidate_index,
                    _json(dict(payload or {})),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return report_id

    def retire_unresolved_cause_factor(
        self, observation_id: str, *, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE unresolved_cause_factors
                SET status = 'retired', updated_at = ?
                WHERE observation_id = ? AND status = 'open'
                """,
                (now, observation_id),
            )
            connection.commit()

    # -- Bounded factor deferral (migration 148) -----------------------------

    def close_unresolved_cause_factor(
        self,
        factor_id: str,
        *,
        status: str,
        resolution_kind: str,
        resolution_detail: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Close an OPEN factor with an explicit evidence label.

        The bounded-deferral exits (`causal_factor_deferral`) close factors as
        'resolved' (repair_confirmed / escalated_unrepaired) or 'retired'
        (expired_unengaged). Idempotent by construction: only an open factor
        transitions, so re-running a sweep or replaying an attempt against an
        already-closed factor is a no-op (returns False).
        """

        if status not in ("resolved", "retired"):
            raise ValueError("factor close status must be 'resolved' or 'retired'")
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE unresolved_cause_factors
                   SET status = ?,
                       resolution_kind = ?,
                       resolution_detail_json = ?,
                       updated_at = ?
                 WHERE id = ? AND status = 'open'
                """,
                (
                    status,
                    resolution_kind,
                    _json(dict(resolution_detail or {})),
                    utc_now_iso(clock),
                    factor_id,
                ),
            )
            connection.commit()
        return cursor.rowcount > 0

    def causal_attribution_reports_for_factor(
        self, factor_id: str
    ) -> list[dict[str, Any]]:
        """Learner self-reports on one factor's diagnostic card, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM causal_attribution_reports
                 WHERE factor_id = ?
                 ORDER BY created_at, id
                """,
                (factor_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def primed_attempt_exists_for_learning_object(
        self, learning_object_id: str, *, since: str
    ) -> bool:
        """Any primed attempt on the learning object at/after ``since``.

        Engagement probe for the bounded-deferral sweep: a primed attempt is a
        guided redo or the primed half of a repair pair — learner engagement
        even when no remediation episode row exists (an unbound guided redo).
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM practice_attempts
                 WHERE learning_object_id = ? AND primed = 1
                   AND created_at >= ?
                 LIMIT 1
                """,
                (learning_object_id, since),
            ).fetchone()
        return row is not None

    # --- Causal repair orchestration (P2 §6, migration 124) ------------------
    #
    # Owned by ``learnloop.diagnosis.causal_orchestrator``. Three stores: the
    # append-only
    # probe DECISION ledger (every decision, including the negative majority
    # class), the append-only learner PREFERENCE log that makes "Not now"
    # survive the attempt, and the mutable machine-check QUEUE that gives the
    # `deferred_machine_checks` arm a producer and a consumer.

    def insert_causal_probe_decision_receipt(
        self,
        *,
        factor_id: str,
        decision: str,
        reason: str,
        repair_status: str,
        decision_policy_version: str,
        formula_version: str,
        inputs: Mapping[str, Any],
        parameters: Mapping[str, Any],
        hypothesis_ids: Sequence[str] = (),
        repair_class_ids: Sequence[str] = (),
        blind_bundle_ids: Sequence[str] = (),
        machine_check_ids: Sequence[str] = (),
        learning_object_id: str | None = None,
        attempt_id: str | None = None,
        misconception_id: str | None = None,
        candidate_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Append one probe decision.

        Never deduplicated: a repeated identical decision is a repeated
        observation, and its frequency is exactly what the P4 training records
        need.  ``decision_fingerprint`` carries the content hash so a caller can
        still group identical decisions without losing the counts.
        """

        import hashlib

        now = utc_now_iso(clock)
        fingerprint = hashlib.sha256(
            _json(
                {
                    "factor_id": factor_id,
                    "decision": decision,
                    "inputs": dict(inputs),
                    "parameters": dict(parameters),
                    "formula_version": formula_version,
                }
            ).encode("utf-8")
        ).hexdigest()[:32]
        receipt_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO causal_probe_decision_receipts(
                  id, decision_fingerprint, factor_id, learning_object_id,
                  attempt_id, misconception_id, decision, reason, repair_status,
                  decision_policy_version, formula_version, inputs_json,
                  parameters_json, hypothesis_ids_json, repair_class_ids_json,
                  candidate_id, blind_bundle_ids_json, machine_check_ids_json,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    fingerprint,
                    factor_id,
                    learning_object_id,
                    attempt_id,
                    misconception_id,
                    decision,
                    reason,
                    repair_status,
                    decision_policy_version,
                    formula_version,
                    _json(dict(inputs)),
                    _json(dict(parameters)),
                    _json([str(value) for value in hypothesis_ids]),
                    _json([str(value) for value in repair_class_ids]),
                    candidate_id,
                    _json([str(value) for value in blind_bundle_ids]),
                    _json([str(value) for value in machine_check_ids]),
                    now,
                ),
            )
            connection.commit()
        receipt = self.causal_probe_decision_receipt(receipt_id)
        assert receipt is not None
        return receipt

    def _decode_causal_probe_decision_receipt(
        self, row: sqlite3.Row
    ) -> dict[str, Any]:
        payload = dict(row)
        payload["inputs"] = _loads(payload.pop("inputs_json"), {})
        payload["parameters"] = _loads(payload.pop("parameters_json"), {})
        payload["hypothesis_ids"] = _loads(payload.pop("hypothesis_ids_json"), [])
        payload["repair_class_ids"] = _loads(
            payload.pop("repair_class_ids_json"), []
        )
        payload["blind_bundle_ids"] = _loads(
            payload.pop("blind_bundle_ids_json"), []
        )
        payload["machine_check_ids"] = _loads(
            payload.pop("machine_check_ids_json"), []
        )
        return payload

    def causal_probe_decision_receipt(
        self, receipt_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_probe_decision_receipts WHERE id = ?",
                (receipt_id,),
            ).fetchone()
        if row is None:
            return None
        return self._decode_causal_probe_decision_receipt(row)

    def causal_probe_decision_receipts(
        self,
        *,
        factor_id: str | None = None,
        decision: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if factor_id is not None:
            clauses.append("factor_id = ?")
            values.append(factor_id)
        if decision is not None:
            clauses.append("decision = ?")
            values.append(decision)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM causal_probe_decision_receipts
                {where}
                ORDER BY created_at, id
                LIMIT ?
                """,
                (*values, limit),
            ).fetchall()
        return [
            self._decode_causal_probe_decision_receipt(row) for row in rows
        ]

    # ------------------------------------------------------------------
    # Shadow selection receipts (migration 146; decision-value spec §6.6).
    # Append-only: the table's triggers abort any update/delete, and shadow
    # output has zero live authority — no serving path reads these rows.
    # ------------------------------------------------------------------


    def _decode_causal_shadow_selection_receipt(
        self, row: sqlite3.Row
    ) -> dict[str, Any]:
        payload = dict(row)
        payload["baselines"] = _loads(payload.pop("baselines_json"), {})
        payload["body"] = _loads(payload.pop("body_json"), {})
        for flag in (
            "would_change_candidate",
            "would_change_measure_vs_repair",
            "would_change_repair",
        ):
            value = payload.get(flag)
            payload[flag] = None if value is None else bool(value)
        return payload

    def causal_shadow_selection_receipt(
        self, receipt_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_shadow_selection_receipts WHERE id = ?",
                (receipt_id,),
            ).fetchone()
        if row is None:
            return None
        return self._decode_causal_shadow_selection_receipt(row)

    def causal_shadow_selection_receipts(
        self,
        *,
        factor_id: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if factor_id is not None:
            clauses.append("factor_id = ?")
            values.append(factor_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM causal_shadow_selection_receipts
                {where}
                ORDER BY created_at, id
                LIMIT ?
                """,
                (*values, limit),
            ).fetchall()
        return [
            self._decode_causal_shadow_selection_receipt(row) for row in rows
        ]

    def median_attempt_latency_seconds(self) -> tuple[float | None, int]:
        """Pooled median of captured attempt latencies + the sample count.

        The Tauri client is the only latency producer (Stage-4 capture); a
        NULL-latency attempt was never timed and is excluded rather than read
        as zero. Wall-clock presentation-to-submit time, per the column's own
        contract — callers must not relabel it active time.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT latency_seconds FROM practice_attempts "
                "WHERE latency_seconds IS NOT NULL"
            ).fetchall()
        values = sorted(
            float(row["latency_seconds"])
            for row in rows
            if row["latency_seconds"] is not None
        )
        if not values:
            return None, 0
        middle = len(values) // 2
        if len(values) % 2:
            median = values[middle]
        else:
            median = (values[middle - 1] + values[middle]) / 2.0
        return median, len(values)

    def record_causal_probe_preference(
        self,
        *,
        scope: str,
        scope_ref: str,
        preference: str,
        source: str,
        session_id: str | None = None,
        expires_at: str | None = None,
        detail: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Persist one learner probe preference ("Not now" and friends)."""

        now = utc_now_iso(clock)
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO causal_probe_preference_events(
                  id, scope, scope_ref, session_id, preference, source,
                  expires_at, detail_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    scope,
                    scope_ref,
                    session_id,
                    preference,
                    source,
                    expires_at,
                    _json(dict(detail)) if detail is not None else None,
                    now,
                ),
            )
            connection.commit()
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_probe_preference_events WHERE id = ?",
                (event_id,),
            ).fetchone()
        payload = dict(row)
        payload["detail"] = _loads(payload.pop("detail_json"), None)
        return payload

    def causal_probe_preference(
        self,
        *,
        factor_id: str | None = None,
        learning_object_id: str | None = None,
        session_id: str | None = None,
        at: str | None = None,
    ) -> dict[str, Any] | None:
        """The newest applicable, unexpired preference across the given scopes.

        Latest learner intent wins rather than most-specific-forever: a learner
        who declined a factor yesterday and re-enabled diagnostics for today's
        session should not be held to yesterday's answer.
        """

        now = at or utc_now_iso()
        clauses: list[str] = []
        values: list[Any] = []
        if factor_id is not None:
            clauses.append("(scope = 'factor' AND scope_ref = ?)")
            values.append(factor_id)
        if learning_object_id is not None:
            clauses.append("(scope = 'learning_object' AND scope_ref = ?)")
            values.append(learning_object_id)
        if session_id is not None:
            clauses.append("(scope = 'session' AND scope_ref = ?)")
            values.append(session_id)
        if not clauses:
            return None
        with self.connection() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM causal_probe_preference_events
                WHERE ({' OR '.join(clauses)})
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (*values, now),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["detail"] = _loads(payload.pop("detail_json"), None)
        return payload

    def enqueue_causal_machine_check(
        self,
        *,
        check_id: str,
        kind: str,
        payload: Mapping[str, Any],
        source: str,
        learning_object_id: str | None = None,
        factor_id: str | None = None,
        attempt_id: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Queue one machine-side obligation, idempotently.

        ``check_id`` is the content hash of the obligation, so re-sweeping the
        same unresolved mapping does not pile up duplicates.  A previously
        resolved check whose obligation reappears is re-opened.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO causal_machine_checks(
                  id, kind, learning_object_id, factor_id, attempt_id, status,
                  source, payload_json, resolution_json, created_at, updated_at,
                  resolved_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL, ?, ?, NULL)
                ON CONFLICT(id) DO UPDATE SET
                  status = 'pending',
                  payload_json = excluded.payload_json,
                  resolution_json = NULL,
                  resolved_at = NULL,
                  updated_at = excluded.updated_at
                WHERE causal_machine_checks.status != 'pending'
                """,
                (
                    check_id,
                    kind,
                    learning_object_id,
                    factor_id,
                    attempt_id,
                    source,
                    _json(dict(payload)),
                    now,
                    now,
                ),
            )
            connection.commit()
        check = self.causal_machine_check(check_id)
        assert check is not None
        return check

    def causal_machine_check(self, check_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM causal_machine_checks WHERE id = ?", (check_id,)
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["payload"] = _loads(payload.pop("payload_json"), {})
        payload["resolution"] = _loads(payload.pop("resolution_json"), None)
        return payload

    def causal_machine_checks(
        self,
        *,
        status: str | None = "pending",
        learning_object_id: str | None = None,
        factor_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            values.append(status)
        if learning_object_id is not None:
            clauses.append("learning_object_id = ?")
            values.append(learning_object_id)
        if factor_id is not None:
            clauses.append("factor_id = ?")
            values.append(factor_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM causal_machine_checks
                {where}
                ORDER BY created_at, id
                """,
                tuple(values),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["payload"] = _loads(payload.pop("payload_json"), {})
            payload["resolution"] = _loads(payload.pop("resolution_json"), None)
            results.append(payload)
        return results

    def close_causal_machine_check(
        self,
        check_id: str,
        *,
        status: str,
        resolution: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any] | None:
        if status not in {"resolved", "dismissed"}:
            raise ValueError("a machine check closes as resolved or dismissed")
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE causal_machine_checks
                   SET status = ?, resolution_json = ?, resolved_at = ?,
                       updated_at = ?
                 WHERE id = ? AND status = 'pending'
                """,
                (
                    status,
                    _json(dict(resolution)) if resolution is not None else None,
                    now,
                    now,
                    check_id,
                ),
            )
            connection.commit()
        return self.causal_machine_check(check_id)

    def causal_probe_candidates_for_factor(
        self, factor_id: str, *, statuses: Sequence[str] | None = None
    ) -> list[dict[str, Any]]:
        """Probe candidates minted for one unresolved-cause factor.

        Only ``active`` candidates are servable (§6): a candidate that has not
        cleared the review ladder is an unreviewed instrument, and serving it
        would spend learner effort on something no reviewer has admitted.
        """

        clauses = ["factor_id = ?"]
        values: list[Any] = [factor_id]
        if statuses:
            clauses.append(
                f"status IN ({','.join('?' for _ in statuses)})"
            )
            values.extend(statuses)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id FROM causal_probe_candidates
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at, id
                """,
                tuple(values),
            ).fetchall()
        return [
            candidate
            for row in rows
            if (candidate := self.causal_probe_candidate(str(row["id"])))
            is not None
        ]

    # ------------------------------------------------------------------
    # Diagnosis adjudication store (migration 126;
    # spec_diagnostic_augmentation_v1.md §2 A4).  Append-only: no update or
    # delete method exists here because the table's triggers would abort one.
    # ------------------------------------------------------------------

    def insert_diagnosis_adjudication(
        self,
        *,
        values: Mapping[str, Any],
        adjudication_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Append one immutable verdict on a diagnosis (A4).

        The caller owns validation; this method owns persistence only. The SQL
        CHECKs are the backstop that keeps a crossed verdict/abstention cell out
        of the eval set even if a future caller forgets.
        """

        adjudication_id = adjudication_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO diagnosis_adjudications(
                  id, attempt_id, diagnosis_receipt_id, verdict,
                  system_abstained, adjudicated_anchor_json,
                  adjudicated_anchor_kind, adjudicated_repair_md,
                  adjudicated_repair_class_id, queue_reason, learner_report_id,
                  adjudicator_source, rationale, decision_policy_version,
                  repair_policy_version, grading_prompt_version, grader_model,
                  receipt_schema_version, system_snapshot_json, supersedes_id,
                  created_at
                ) VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    adjudication_id,
                    str(values["attempt_id"]),
                    str(values["diagnosis_receipt_id"]),
                    str(values["verdict"]),
                    1 if values.get("system_abstained") else 0,
                    _json(values["adjudicated_anchor"])
                    if values.get("adjudicated_anchor") is not None
                    else None,
                    values.get("adjudicated_anchor_kind"),
                    values.get("adjudicated_repair_md"),
                    values.get("adjudicated_repair_class_id"),
                    str(values["queue_reason"]),
                    values.get("learner_report_id"),
                    str(values["adjudicator_source"]),
                    values.get("rationale"),
                    values.get("decision_policy_version"),
                    values.get("repair_policy_version"),
                    values.get("grading_prompt_version"),
                    values.get("grader_model"),
                    values.get("receipt_schema_version"),
                    _json(dict(values.get("system_snapshot") or {})),
                    values.get("supersedes_id"),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return adjudication_id

    def diagnosis_adjudication(
        self, adjudication_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM diagnosis_adjudications WHERE id = ?",
                (adjudication_id,),
            ).fetchone()
        return _decode_diagnosis_adjudication(row) if row is not None else None

    def diagnosis_adjudications_for_attempt(
        self, attempt_id: str
    ) -> list[dict[str, Any]]:
        """The whole supersession chain for one attempt, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM diagnosis_adjudications
                WHERE attempt_id = ?
                ORDER BY created_at, id
                """,
                (attempt_id,),
            ).fetchall()
        return [_decode_diagnosis_adjudication(row) for row in rows]

    def active_diagnosis_adjudication(
        self, attempt_id: str
    ) -> dict[str, Any] | None:
        """The head of the chain: the row nothing else supersedes."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT a.* FROM diagnosis_adjudications a
                WHERE a.attempt_id = ?
                  AND NOT EXISTS (
                    SELECT 1 FROM diagnosis_adjudications s
                    WHERE s.supersedes_id = a.id
                  )
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT 1
                """,
                (attempt_id,),
            ).fetchone()
        return _decode_diagnosis_adjudication(row) if row is not None else None

    def adjudicated_attempt_ids(self) -> set[str]:
        """Attempts already carrying a verdict — the queue's exclusion set."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT attempt_id FROM diagnosis_adjudications"
            ).fetchall()
        return {str(row["attempt_id"]) for row in rows}

    def list_diagnosis_adjudications(
        self,
        *,
        active_only: bool = True,
        attempt_ids: Sequence[str] | None = None,
        verdicts: Sequence[str] | None = None,
        grading_prompt_version: str | None = None,
        grader_model: str | None = None,
        queue_reasons: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Scoreboard/eval read. ``active_only`` keeps one row per attempt so a
        re-adjudicated case is never double-counted in a rate."""

        clauses: list[str] = []
        values: list[Any] = []
        if active_only:
            clauses.append(
                "NOT EXISTS (SELECT 1 FROM diagnosis_adjudications s "
                "WHERE s.supersedes_id = a.id)"
            )
        if attempt_ids is not None:
            ids = list(attempt_ids)
            if not ids:
                return []
            clauses.append(f"a.attempt_id IN ({','.join('?' for _ in ids)})")
            values.extend(ids)
        if verdicts:
            clauses.append(f"a.verdict IN ({','.join('?' for _ in verdicts)})")
            values.extend(verdicts)
        if grading_prompt_version is not None:
            clauses.append("a.grading_prompt_version = ?")
            values.append(grading_prompt_version)
        if grader_model is not None:
            clauses.append("a.grader_model = ?")
            values.append(grader_model)
        if queue_reasons:
            clauses.append(
                f"a.queue_reason IN ({','.join('?' for _ in queue_reasons)})"
            )
            values.extend(queue_reasons)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        suffix = ""
        if limit is not None:
            suffix = " LIMIT ?"
            values.append(int(limit))
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT a.* FROM diagnosis_adjudications a
                {where}
                ORDER BY a.created_at, a.id
                {suffix}
                """,
                tuple(values),
            ).fetchall()
        return [_decode_diagnosis_adjudication(row) for row in rows]

    def insert_contrast_pair_serving(
        self,
        *,
        pair_key: str,
        practice_item_id: str,
        counterpart_item_id: str,
        serve_position: int,
        randomization_seed: str,
        randomization_value: float,
        separated: bool,
        adjacency_basis: str,
        session_id: str | None = None,
        id: str | None = None,
        clock: Clock | None = None,
    ) -> str | None:
        """Record which member of an A4 pair this session's queue offered first.

        ``None`` on a duplicate ``(practice_item_id, session_id)``:
        ``build_due_queue`` re-plans the same session repeatedly, and the order
        the learner actually saw is the one the first plan chose.
        """

        row_id = id or new_ulid()
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO contrast_pair_servings(
                  id, pair_key, practice_item_id, serve_position, counterpart_item_id,
                  session_id, randomization_seed, randomization_value, separated,
                  adjacency_basis, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    pair_key,
                    practice_item_id,
                    int(serve_position),
                    counterpart_item_id,
                    session_id,
                    randomization_seed,
                    float(randomization_value),
                    1 if separated else 0,
                    adjacency_basis,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id if cursor.rowcount else None

    def contrast_pair_serving_rows(
        self, *, since: str | None = None, pair_key: str | None = None
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if since is not None:
            clauses.append("created_at >= ?")
            values.append(since)
        if pair_key is not None:
            clauses.append("pair_key = ?")
            values.append(pair_key)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM contrast_pair_servings
                {where}
                ORDER BY created_at, id
                """,
                tuple(values),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_error_hunt_outcome(
        self,
        *,
        attempt_id: str,
        practice_item_id: str,
        clean_solution: bool,
        planted_total: int,
        planted_repaired: int,
        planted_flagged_not_repaired: int,
        planted_missed: int,
        false_positive_reports: int,
        misconception_candidate_id: str | None = None,
        facet_failure_suppressed: bool = False,
        grading_prompt_version: str | None = None,
        id: str | None = None,
        clock: Clock | None = None,
    ) -> str | None:
        """Record one A3 attempt's outcome; ``None`` when the attempt already has one."""

        row_id = id or new_ulid()
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO error_hunt_outcomes(
                  id, attempt_id, practice_item_id, clean_solution, planted_total,
                  planted_repaired, planted_flagged_not_repaired, planted_missed,
                  false_positive_reports, misconception_candidate_id,
                  facet_failure_suppressed, grading_prompt_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    attempt_id,
                    practice_item_id,
                    1 if clean_solution else 0,
                    int(planted_total),
                    int(planted_repaired),
                    int(planted_flagged_not_repaired),
                    int(planted_missed),
                    int(false_positive_reports),
                    misconception_candidate_id,
                    1 if facet_failure_suppressed else 0,
                    grading_prompt_version,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id if cursor.rowcount else None

    def error_hunt_outcome_rows(
        self, *, since: str | None = None
    ) -> list[dict[str, Any]]:
        clause = "WHERE created_at >= ?" if since is not None else ""
        values = (since,) if since is not None else ()
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM error_hunt_outcomes
                {clause}
                ORDER BY created_at, id
                """,
                values,
            ).fetchall()
        return [dict(row) for row in rows]

    def error_hunt_outcome(self, attempt_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM error_hunt_outcomes WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return dict(row) if row is not None else None
