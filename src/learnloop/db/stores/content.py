"""Content proposals, apply intents, generation and agent runs.

Owns proposal and content ledgers, synthesis runs and manifests, generation
requests and artifacts, and agent run records."""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable, Mapping, Sequence

from learnloop.ai.usage import TokenUsage
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.records import _decode_proposal_batch, _decode_proposal_item
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid


def _proposal_item_identity(client_item_id: Any, payload: Any, edited_payload: Any) -> str:
    """What a proposal item would create: the edited payload's ``id`` when it
    was edited, else the payload's, else its client id (no ``id`` in either)."""

    effective = edited_payload if isinstance(edited_payload, Mapping) else payload
    if isinstance(effective, Mapping) and isinstance(effective.get("id"), str) and effective["id"]:
        return f"id:{effective['id']}"
    return f"client:{client_item_id or ''}"


def _non_negative_tokens(value: Any) -> int:
    """Coerce a token count for a NOT NULL DEFAULT 0 column (migration 131).

    Token columns are counters that get SUMmed into cost ratios, so a None from
    an unset mapping key, or a float from a provider that reports one, must land
    as a plain non-negative int rather than as NULL or a type error.
    """

    if value is None:
        return 0
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return count if count > 0 else 0


def _decode_synthesis_manifest(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "membership",
        "revision_ids",
        "asset_hashes",
        "extraction_ids",
        "unit_inventory_versions",
        "scope",
        "brief",
        "extractor_versions",
        "token_budget",
        "estimated_usage",
    ):
        data[key] = _loads(data.pop(f"{key}_json", None), None)
    return data


def _decode_synthesis_run(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in (
        "span_request",
        "resolved_span_hashes",
        "coverage_decisions",
        "actual_usage",
        "candidate_output",
    ):
        data[key] = _loads(data.pop(f"{key}_json", None), None)
    return data


def _decode_apply_intent(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["item_ids"] = _loads(data.pop("item_ids_json"), [])
    data["targets"] = _loads(data.pop("targets_json"), [])
    data["db_plan"] = _loads(data.pop("db_plan_json"), [])
    if "conflict_json" in data:
        data["conflicts"] = _loads(data.pop("conflict_json"), [])
    return data


def _content_event_has_source_grounding(row: sqlite3.Row) -> bool:
    payload = _loads(row["_proposal_edited_payload_json"], None)
    if payload is None:
        payload = _loads(row["_proposal_payload_json"], {})
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    if not isinstance(provenance, dict):
        return False
    source_refs = provenance.get("source_refs")
    return isinstance(source_refs, list) and bool(source_refs)


class ContentStoreMixin:

    @staticmethod
    def _record_text_provenance(connection: Any, kind: str, record_id: str, text: Any, record: Any,
                                writer: str, clock: Clock | None) -> None:
        """One write-time provenance row for a text this transaction writes
        (diagnosis input provenance), when its writer passed a record."""

        if record is None or text is None:
            return
        from learnloop.db.stores.write_provenance import record_text_write

        record_text_write(connection, kind=kind, record_id=record_id, text=text, writer=writer, record=record,
                          clock=clock)

    # --- Today queue invalidation (migration 117) ------------------------------

    def queue_revision(self) -> dict[str, Any]:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT revision, updated_at FROM queue_state WHERE singleton = 1"
            ).fetchone()
        return {
            "revision": int(row["revision"]) if row is not None else 0,
            "updated_at": row["updated_at"] if row is not None else None,
        }

    def bump_queue_revision(self, *, clock: Clock | None = None) -> int:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO queue_state(singleton, revision, updated_at)
                VALUES (1, 1, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                  revision = queue_state.revision + 1,
                  updated_at = excluded.updated_at
                """,
                (now,),
            )
            row = connection.execute(
                "SELECT revision FROM queue_state WHERE singleton = 1"
            ).fetchone()
            connection.commit()
        return int(row["revision"])

    # --- rung variant requests (migration 108) --------------------------------

    def insert_rung_variant_request(self, request: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        request_id = str(request.get("id") or new_ulid())
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO rung_variant_requests(
                  id, source_practice_item_id, learning_object_id, direction,
                  source_waypoint_slug, target_waypoint_slug, target_rung_json,
                  status, attempt_id, learner_claim_id, batch_id, patch_id,
                  created_practice_item_id, failure_reason, variant_kind,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    request["source_practice_item_id"],
                    request["learning_object_id"],
                    request["direction"],
                    request["source_waypoint_slug"],
                    request["target_waypoint_slug"],
                    request["target_rung_json"],
                    request.get("status") or "pending",
                    request.get("attempt_id"),
                    request.get("learner_claim_id"),
                    request.get("batch_id"),
                    request.get("patch_id"),
                    request.get("created_practice_item_id"),
                    request.get("failure_reason"),
                    request.get("variant_kind") or request["direction"],
                    now,
                    now,
                ),
            )
            connection.commit()
        return request_id

    def rung_variant_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM rung_variant_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def rung_variant_requests(
        self, request_ids: Iterable[str]
    ) -> dict[str, dict[str, Any]]:
        """Bulk-load rung requests used by ingest progress views."""

        ids = sorted({str(request_id) for request_id in request_ids if request_id})
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM rung_variant_requests WHERE id IN ({placeholders})",
                ids,
            ).fetchall()
        return {str(row["id"]): dict(row) for row in rows}

    def update_rung_variant_request(
        self, request_id: str, *, clock: Clock | None = None, **fields: Any
    ) -> bool:
        allowed = {
            "status", "attempt_id", "learner_claim_id", "batch_id", "patch_id",
            "created_practice_item_id", "failure_reason", "variant_kind",
        }
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return False
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE rung_variant_requests SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), utc_now_iso(clock), request_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def retry_failed_rung_variant_request(
        self, request_id: str, *, clock: Clock | None = None
    ) -> bool:
        """Return one failed generation request to its pre-generation state.

        The learner attempt and claim are evidence from the original request and
        deliberately survive retries. Generation-owned output pointers and the
        prior failure are cleared so the same durable request can author again.
        """

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE rung_variant_requests
                   SET status = 'pending',
                       patch_id = NULL,
                       created_practice_item_id = NULL,
                       failure_reason = NULL,
                       updated_at = ?
                 WHERE id = ? AND status = 'failed'
                """,
                (utc_now_iso(clock), request_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def pending_rung_variant_requests(self, source_practice_item_id: str) -> list[dict[str, Any]]:
        """Non-terminal requests for one item — the per-item request lock."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM rung_variant_requests
                WHERE source_practice_item_id = ? AND status IN ('pending', 'generating')
                ORDER BY created_at, id
                """,
                (source_practice_item_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Concept animations (spec_fork_features §2)
    # ------------------------------------------------------------------

    _CONCEPT_ANIMATION_FIELDS = {
        "status", "scene_code", "scene_class", "title", "narration_md",
        "video_hash", "video_file_name", "duration_seconds", "provider",
        "model", "prompt_version", "quality", "repair_attempted",
        "failure_stage", "failure_reason", "render_stderr", "batch_id",
        "completed_at", "renderer", "storyboard_json", "video_job_ids",
    }

    def insert_concept_animation(self, row: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        animation_id = str(row.get("id") or new_ulid())
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO concept_animations(
                  id, concept_id, learning_object_id, status, scene_code,
                  scene_class, title, narration_md, video_hash, video_file_name,
                  duration_seconds, provider, model, prompt_version, quality,
                  repair_attempted, failure_stage, failure_reason, render_stderr,
                  batch_id, created_at, updated_at, completed_at, renderer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    animation_id,
                    row["concept_id"],
                    row.get("learning_object_id"),
                    row.get("status") or "queued",
                    row.get("scene_code"),
                    row.get("scene_class"),
                    row.get("title"),
                    row.get("narration_md"),
                    row.get("video_hash"),
                    row.get("video_file_name"),
                    row.get("duration_seconds"),
                    row.get("provider"),
                    row.get("model"),
                    row.get("prompt_version"),
                    row.get("quality"),
                    int(row.get("repair_attempted") or 0),
                    row.get("failure_stage"),
                    row.get("failure_reason"),
                    row.get("render_stderr"),
                    row.get("batch_id"),
                    now,
                    now,
                    row.get("completed_at"),
                    row.get("renderer") or "manim",
                ),
            )
            connection.commit()
        return animation_id

    def concept_animation(self, animation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM concept_animations WHERE id = ?", (animation_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def update_concept_animation(
        self, animation_id: str, *, clock: Clock | None = None, **fields: Any
    ) -> bool:
        updates = {key: value for key, value in fields.items() if key in self._CONCEPT_ANIMATION_FIELDS}
        if not updates:
            return False
        assignments = ", ".join(f"{key} = ?" for key in updates)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE concept_animations SET {assignments}, updated_at = ? WHERE id = ?",
                (*updates.values(), utc_now_iso(clock), animation_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def concept_animations_for_concept(self, concept_id: str, limit: int = 10) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM concept_animations
                WHERE concept_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (concept_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def pending_concept_animations(self, concept_id: str) -> list[dict[str, Any]]:
        """Non-terminal animations for one concept — the per-concept lock."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM concept_animations
                WHERE concept_id = ? AND status IN ('queued', 'generating', 'validating', 'rendering')
                ORDER BY created_at, id
                """,
                (concept_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # --- synthesis-time generate-discriminator needs (ING M6, §8.7) ----------

    def upsert_synthesis_generation_need(
        self,
        *,
        subject_id: str,
        need_kind: str,
        target_key: str,
        missing_capability: str,
        facet_ids: list[str] | None = None,
        source_set_id: str | None = None,
        synthesis_run_id: str | None = None,
        detail: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Record one deduplicated synthesis-time generation/coarsen need.

        Mirrors ``upsert_probe_generation_need`` but synthesis-scoped: deduped on
        (subject_id, need_kind, target_key) since there is no probe episode yet.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM synthesis_generation_needs "
                "WHERE subject_id = ? AND need_kind = ? AND target_key = ?",
                (subject_id, need_kind, target_key),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            need_id = new_ulid()
            connection.execute(
                """
                INSERT INTO synthesis_generation_needs(
                  id, subject_id, source_set_id, synthesis_run_id, need_kind,
                  target_key, missing_capability, facet_ids_json, detail, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    need_id,
                    subject_id,
                    source_set_id,
                    synthesis_run_id,
                    need_kind,
                    target_key,
                    missing_capability,
                    _json(list(facet_ids or [])),
                    detail,
                    now,
                ),
            )
            connection.commit()
        return need_id

    def synthesis_generation_needs(
        self,
        *,
        subject_id: str | None = None,
        status: str | None = None,
        need_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        for column, value in (
            ("subject_id", subject_id),
            ("status", status),
            ("need_kind", need_kind),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM synthesis_generation_needs{where} ORDER BY created_at, id",
                parameters,
            ).fetchall()
        return [
            {
                "id": row["id"],
                "subject_id": row["subject_id"],
                "source_set_id": row["source_set_id"],
                "synthesis_run_id": row["synthesis_run_id"],
                "need_kind": row["need_kind"],
                "target_key": row["target_key"],
                "missing_capability": row["missing_capability"],
                "facet_ids": _loads(row["facet_ids_json"], []),
                "detail": row["detail"],
                "status": row["status"],
                "created_at": row["created_at"],
                "resolved_at": row["resolved_at"],
            }
            for row in rows
        ]

    def resolve_synthesis_generation_need(
        self, need_id: str, *, status: str = "resolved", clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE synthesis_generation_needs SET status = ?, resolved_at = ? WHERE id = ?",
                (status, now, need_id),
            )
            connection.commit()

    def insert_agent_run(self, run: Mapping[str, Any]) -> str:
        run_id = str(run.get("id") or new_ulid())
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO agent_runs(
                  id, purpose, model, provider, prompt_template, prompt_version,
                  sdk_version, codex_revision, provider_type, provider_revision,
                  input_context_hash, output_schema, started_at, completed_at,
                  status, error_message, est_input_tokens, est_output_tokens
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    run["purpose"],
                    run.get("model"),
                    run.get("provider", "codex"),
                    run.get("prompt_template"),
                    run.get("prompt_version"),
                    run.get("sdk_version"),
                    run.get("codex_revision"),
                    run.get("provider_type"),
                    run.get("provider_revision"),
                    run.get("input_context_hash"),
                    run.get("output_schema"),
                    run["started_at"],
                    run.get("completed_at"),
                    run.get("status", "running"),
                    run.get("error_message"),
                    # A7 (spec_diagnostic_augmentation_v1.md §2): the pre-flight
                    # budget, 0 when the caller does not estimate. Actuals are
                    # written at completion, where the provider has reported them.
                    _non_negative_tokens(run.get("est_input_tokens")),
                    _non_negative_tokens(run.get("est_output_tokens")),
                ),
            )
            connection.commit()
        return run_id

    def complete_agent_run(
        self,
        run_id: str,
        *,
        status: str = "completed",
        error_message: str | None = None,
        usage: TokenUsage | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Finalize a run, optionally recording what the provider charged for it.

        `usage` is what the client accumulated over every model call this run
        made (A7 / migration 131) — extended here rather than split into a
        second `record_agent_run_usage` method because usage is known exactly
        when the run ends, on both the success and the failure arm, and a
        separate call would double the writes and let the two drift apart.
        `usage=None` leaves the actual_* columns untouched, so a caller with no
        client in scope (or a second, redundant completion of the same run)
        cannot zero out a cost already recorded.
        """

        now = utc_now_iso(clock)
        with self.connection() as connection:
            if usage is None:
                cursor = connection.execute(
                    """
                    UPDATE agent_runs
                    SET completed_at = ?, status = ?, error_message = ?
                    WHERE id = ?
                    """,
                    (now, status, error_message, run_id),
                )
            else:
                cursor = connection.execute(
                    """
                    UPDATE agent_runs
                    SET completed_at = ?, status = ?, error_message = ?,
                        actual_input_tokens = ?, actual_output_tokens = ?
                    WHERE id = ?
                    """,
                    (
                        now,
                        status,
                        error_message,
                        _non_negative_tokens(usage.input_tokens),
                        _non_negative_tokens(usage.output_tokens),
                        run_id,
                    ),
                )
            connection.commit()
            return cursor.rowcount > 0

    def add_agent_run_usage(self, run_id: str, usage: TokenUsage) -> bool:
        """Add tokens to a run that was already finalized (A7).

        For the one shape `complete_agent_run` cannot express: a billed call that
        happens *after* the run is closed. `generate_authoring_proposal` closes
        its run before the best-effort item-repair pass, deliberately — a repair
        interrupt must not reopen a completed authoring run — but the repair
        still costs tokens that belong to that run's cost, not to whatever the
        client does next. Additive, so it is safe to call after any drain.
        """

        if usage.input_tokens <= 0 and usage.output_tokens <= 0:
            return False
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE agent_runs
                SET actual_input_tokens = actual_input_tokens + ?,
                    actual_output_tokens = actual_output_tokens + ?
                WHERE id = ?
                """,
                (
                    _non_negative_tokens(usage.input_tokens),
                    _non_negative_tokens(usage.output_tokens),
                    run_id,
                ),
            )
            connection.commit()
            return cursor.rowcount > 0

    def completed_agent_run_by_context(self, purpose: str, input_context_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM agent_runs
                WHERE purpose = ? AND input_context_hash = ? AND status = 'completed'
                ORDER BY completed_at DESC, started_at DESC
                LIMIT 1
                """,
                (purpose, input_context_hash),
            ).fetchone()
        return dict(row) if row is not None else None

    def agent_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM agent_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def proposal_batch_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM proposed_patches
                WHERE agent_run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (agent_run_id,),
            ).fetchone()
        return _decode_proposal_batch(row) if row is not None else None

    def proposal_batch(self, patch_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM proposed_patches WHERE id = ?",
                (patch_id,),
            ).fetchone()
        return _decode_proposal_batch(row) if row is not None else None

    def persist_proposal_batch(
        self,
        batch: Mapping[str, Any],
        items: Iterable[Mapping[str, Any]],
        *,
        join_pending: Mapping[str, Any] | None = None,
    ) -> str:
        """Write one proposal batch and its items.

        ``join_pending`` (a source ref) proposes each item once, however many
        callers name it (UX Phase 2, Codex review of ux-phase2-shell F6; Phase
        1 usability round 1: "Proposals grows on every practice, with
        duplicate error-type proposals"). An item whose ``item_type``,
        ``operation`` and effective identity already wait (a ``pending`` item;
        the identity is the edited payload's ``id`` when the item was edited,
        else the payload's, else the ``client_item_id``) is not written
        again: the ref joins the waiting item's batch's source refs instead,
        so that proposal keeps every caller that named it. The check and the
        write run under one write lock, so two callers at once cannot both
        write. Returns the new batch's id, or, when every item already waits,
        the first waiting batch the ref joined. Proposal tables are WORKFLOW:
        nothing replays or grades from them, so no persisted meaning changes.
        """

        batch_id = str(batch.get("id") or new_ulid())
        item_rows = list(items)
        client_ids = [str(item.get("client_item_id") or "") for item in item_rows]
        client_id_counts: dict[str, int] = {}
        for client_id in client_ids:
            client_id_counts[client_id] = client_id_counts.get(client_id, 0) + 1
        duplicate_client_ids = sorted(
            client_id
            for client_id, count in client_id_counts.items()
            if client_id and count > 1
        )
        if duplicate_client_ids:
            raise ValueError(
                "proposal contains duplicate client_item_id values: "
                + ", ".join(duplicate_client_ids)
            )
        with self.connection() as connection:
            if join_pending is not None:
                if not connection.in_transaction:
                    # Take the write lock BEFORE reading so the check-and-insert
                    # is one atomic step even across connections.
                    connection.execute("BEGIN IMMEDIATE")
                fresh: list[Mapping[str, Any]] = []
                joined: list[str] = []
                for item in item_rows:
                    # Match by what each waiting item would now create (fix
                    # round 2, verify 20261021-114726-Jrt7sA item 5): the
                    # payload editor can change a waiting item's ``id`` while
                    # its ``client_item_id`` keeps the old one, so the stale
                    # client id would join the wrong proposal (or miss the
                    # renamed one). Read under the same write lock as the insert.
                    identity = _proposal_item_identity(
                        item.get("client_item_id"), item.get("payload"), item.get("edited_payload")
                    )
                    waiting = next(
                        (
                            row
                            for row in connection.execute(
                                """
                                SELECT proposed_patch_id, client_item_id, payload_json, edited_payload_json
                                  FROM proposed_patch_items
                                 WHERE item_type = ? AND operation = ? AND decision = 'pending'
                                 ORDER BY created_at, id
                                """,
                                (item["item_type"], item["operation"]),
                            ).fetchall()
                            if _proposal_item_identity(
                                row["client_item_id"],
                                _loads(row["payload_json"], None),
                                _loads(row["edited_payload_json"], None),
                            )
                            == identity
                        ),
                        None,
                    )
                    if waiting is None:
                        fresh.append(item)
                    elif str(waiting["proposed_patch_id"]) not in joined:
                        joined.append(str(waiting["proposed_patch_id"]))
                ref = dict(join_pending)
                for patch_id in joined:
                    current = connection.execute(
                        "SELECT source_refs_json FROM proposed_patches WHERE id = ?", (patch_id,)
                    ).fetchone()
                    refs = _loads(current["source_refs_json"], []) if current is not None else []
                    if ref not in refs:
                        connection.execute(
                            "UPDATE proposed_patches SET source_refs_json = ?, updated_at = ? WHERE id = ?",
                            (_json([*refs, ref]), batch.get("updated_at", batch["created_at"]), patch_id),
                        )
                if joined and not fresh:
                    connection.commit()
                    return joined[0]
                item_rows = fresh
            connection.execute(
                """
                INSERT INTO proposed_patches(
                  id, agent_run_id, purpose, source_refs_json, summary,
                  status_cache, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    batch["agent_run_id"],
                    batch["purpose"],
                    _json(batch.get("source_refs", [])),
                    batch.get("summary"),
                    batch.get("status_cache", "pending"),
                    batch["created_at"],
                    batch.get("updated_at", batch["created_at"]),
                ),
            )
            # client_item_id -> DB id, so LLM-declared depends_on_client_item_ids
            # normalize into the dependency table (source-ingestion §10.2).
            client_to_db_id: dict[str, str] = {}
            dependency_edges: list[tuple[str, list[str]]] = []
            for item in item_rows:
                item_db_id = item.get("id") or new_ulid()
                client_to_db_id[str(item["client_item_id"])] = item_db_id
                depends_on = list(item.get("depends_on_client_item_ids") or [])
                if depends_on:
                    dependency_edges.append((item_db_id, [str(dep) for dep in depends_on]))
                connection.execute(
                    """
                    INSERT INTO proposed_patch_items(
                      id, proposed_patch_id, client_item_id, item_type, operation,
                      target_entity_type, target_entity_id, payload_json,
                      source_ref_ids_json, audit_json, edited_payload_json,
                      decision, validation_status, validation_errors_json,
                      applied_change_batch_id, decided_at, decided_by,
                      created_at, updated_at, dependency_status,
                      dependency_block_reason_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_db_id,
                        batch_id,
                        item["client_item_id"],
                        item["item_type"],
                        item["operation"],
                        item.get("target_entity_type"),
                        item.get("target_entity_id"),
                        _json(item["payload"]),
                        _json(item.get("source_ref_ids", [])),
                        _json(item.get("audit")) if item.get("audit") is not None else None,
                        _json(item.get("edited_payload")) if item.get("edited_payload") is not None else None,
                        item.get("decision", "pending"),
                        item.get("validation_status", "valid"),
                        _json(item.get("validation_errors", [])),
                        item.get("applied_change_batch_id"),
                        item.get("decided_at"),
                        item.get("decided_by"),
                        item["created_at"],
                        item.get("updated_at", item["created_at"]),
                        item.get("dependency_status", "pending"),
                        _json(item.get("dependency_block_reason"))
                        if item.get("dependency_block_reason") is not None
                        else None,
                    ),
                )
            for item_db_id, depends_on in dependency_edges:
                for client_dep in depends_on:
                    dep_db_id = client_to_db_id.get(client_dep)
                    if dep_db_id is None or dep_db_id == item_db_id:
                        # An unknown or self-referential dependency is dropped
                        # rather than persisted as a dangling edge; the item's
                        # dependency_status carries any blocking reason.
                        continue
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO proposed_patch_item_dependencies(
                          proposed_patch_item_id, depends_on_patch_item_id
                        )
                        VALUES (?, ?)
                        """,
                        (item_db_id, dep_db_id),
                    )
            self._refresh_proposal_status(connection, batch_id, updated_at=batch.get("updated_at", batch["created_at"]))
            connection.commit()
        return batch_id

    def proposal_item_dependencies(self, item_id: str) -> list[str]:
        """DB ids this proposal item depends on (source-ingestion §10.2)."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT depends_on_patch_item_id
                FROM proposed_patch_item_dependencies
                WHERE proposed_patch_item_id = ?
                ORDER BY depends_on_patch_item_id
                """,
                (item_id,),
            ).fetchall()
        return [row["depends_on_patch_item_id"] for row in rows]

    def set_proposal_item_dependency_status(
        self,
        item_id: str,
        *,
        dependency_status: str,
        block_reason: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET dependency_status = ?, dependency_block_reason_json = ?
                WHERE id = ?
                """,
                (
                    dependency_status,
                    _json(block_reason) if block_reason is not None else None,
                    item_id,
                ),
            )
            connection.commit()

    # ------------------------------------------------------------------
    # Vault epigraphs (migration 158): model-authored quotes/haiku about the
    # material, one batch per completed synthesis. Append-only history; the
    # Start screen reads the newest N.
    # ------------------------------------------------------------------

    def insert_vault_epigraphs(
        self,
        *,
        subject_id: str,
        source_set_id: str | None,
        synthesis_run_id: str | None,
        mode: str,
        epigraphs: Sequence[Mapping[str, Any]],
        prompt_version: str,
        provider: str | None,
        model: str | None,
        clock: Clock | None = None,
    ) -> list[str]:
        """Persist one synthesis's batch. ``epigraphs`` entries carry ``kind``
        and ``text`` (haiku lines already "\n"-joined). The batch shares one
        ``created_at``; ``ordinal`` records model order because ULIDs minted
        in one millisecond do not sort by insertion."""

        now = utc_now_iso(clock)
        ids: list[str] = []
        with self.connection() as connection:
            for ordinal, entry in enumerate(epigraphs):
                epigraph_id = f"vep_{new_ulid()}"
                connection.execute(
                    "INSERT INTO vault_epigraphs("
                    "  id, subject_id, source_set_id, synthesis_run_id, mode, kind,"
                    "  text, prompt_version, provider, model, ordinal, created_at"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        epigraph_id,
                        subject_id,
                        source_set_id,
                        synthesis_run_id,
                        mode,
                        str(entry["kind"]),
                        str(entry["text"]),
                        prompt_version,
                        provider,
                        model,
                        ordinal,
                        now,
                    ),
                )
                ids.append(epigraph_id)
            connection.commit()
        return ids

    def recent_vault_epigraphs(
        self, *, subject_id: str | None = None, limit: int = 12
    ) -> list[dict[str, Any]]:
        """Newest first; ``subject_id=None`` spans the whole vault."""

        sql = "SELECT * FROM vault_epigraphs"
        params: list[Any] = []
        if subject_id:
            sql += " WHERE subject_id = ?"
            params.append(subject_id)
        sql += " ORDER BY created_at DESC, ordinal DESC, id DESC LIMIT ?"
        params.append(int(limit))
        with self.connection() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def proposal_batches(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM proposed_patches ORDER BY created_at DESC"
            ).fetchall()
        return [_decode_proposal_batch(row) for row in rows]

    def proposal_items(self, patch_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM proposed_patch_items
                WHERE proposed_patch_id = ?
                ORDER BY created_at, client_item_id
                """,
                (patch_id,),
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def persona_gate_audit_rows(self, *, since: str | None = None) -> list[dict[str, Any]]:
        """Every proposal item carrying a §3.0 persona-gate audit (plan item 5.3).

        The projection is deliberately narrow — the gate's typed verdict fields
        plus the reviewer's later ``decision`` — because its one consumer
        (``persona_gate.gate_precision``) is a rate over gate predictions and must
        not accidentally acquire a second definition of the verdict by re-deriving
        it from the payload. ``decision`` is returned as ``reviewer_decision`` to
        keep it from colliding with the gate's own ``decision`` arm.
        """

        clauses = ["json_extract(audit_json, '$.persona_gate') IS NOT NULL"]
        parameters: list[Any] = []
        if since is not None:
            clauses.append("created_at >= ?")
            parameters.append(since)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id AS proposal_item_id,
                       proposed_patch_id AS patch_id,
                       client_item_id,
                       created_at,
                       decision AS reviewer_decision,
                       json_extract(audit_json, '$.persona_gate.instrument_class') AS instrument_class,
                       json_extract(audit_json, '$.persona_gate.tier') AS tier,
                       json_extract(audit_json, '$.persona_gate.decision') AS decision,
                       json_extract(audit_json, '$.persona_gate.reason') AS reason
                  FROM proposed_patch_items
                 WHERE {' AND '.join(clauses)}
                 ORDER BY created_at, id
                """,
                tuple(parameters),
            ).fetchall()
        return [dict(row) for row in rows]

    def proposal_item(self, item_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        return _decode_proposal_item(row) if row is not None else None

    def proposal_items_by_client_id(self, client_item_id: str) -> list[dict[str, Any]]:
        """All proposal items sharing a ``client_item_id`` (used to dedupe re-proposals)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM proposed_patch_items WHERE client_item_id = ?",
                (client_item_id,),
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def pending_invalid_proposal_items(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM proposed_patch_items
                WHERE decision = 'pending' AND validation_status = 'invalid'
                ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def update_proposal_item_edited_payload(
        self,
        item_id: str,
        *,
        edited_payload: Mapping[str, Any],
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET edited_payload_json = ?,
                    validation_status = ?,
                    validation_errors_json = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (_json(edited_payload), validation_status, _json(validation_errors), now, item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def update_proposal_item_validation(
        self,
        item_id: str,
        *,
        validation_status: str,
        validation_errors: list[str],
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE proposed_patch_items
                SET validation_status = ?,
                    validation_errors_json = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'pending'
                """,
                (validation_status, _json(validation_errors), now, item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def pending_proposal_items(self, patch_id: str, item_ids: list[str] | None = None) -> list[dict[str, Any]]:
        parameters: list[Any] = [patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM proposed_patch_items
                WHERE proposed_patch_id = ? AND decision = 'pending'{item_filter}
                ORDER BY created_at, client_item_id
                """,
                parameters,
            ).fetchall()
        return [_decode_proposal_item(row) for row in rows]

    def record_applied_proposal_item(
        self,
        *,
        proposal_item_id: str,
        change_batch: Mapping[str, Any],
        content_events: Iterable[Mapping[str, Any]],
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO change_batches(
                  id, proposed_patch_item_id, reason, origin, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    change_batch["id"],
                    proposal_item_id,
                    change_batch.get("reason", "proposal_accept"),
                    change_batch.get("origin", "codex"),
                    change_batch.get("summary"),
                    change_batch["created_at"],
                ),
            )
            for event in content_events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["id"],
                        change_batch["id"],
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status", "accepted"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET decision = 'accepted',
                    applied_change_batch_id = ?,
                    decided_at = ?,
                    decided_by = 'learner',
                    updated_at = ?
                WHERE id = ?
                """,
                (change_batch["id"], now, now, proposal_item_id),
            )
            patch_row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (proposal_item_id,),
            ).fetchone()
            if patch_row is not None:
                self._refresh_proposal_status(connection, patch_row["proposed_patch_id"], updated_at=now)
            connection.commit()

    def record_content_events(self, events: Iterable[Mapping[str, Any]]) -> int:
        count = 0
        with self.connection() as connection:
            for event in events:
                connection.execute(
                    """
                    INSERT INTO content_events(
                      id, change_batch_id, event_type, subject, entity_type,
                      entity_id, origin, review_status, summary, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.get("id") or new_ulid(),
                        event.get("change_batch_id"),
                        event["event_type"],
                        event.get("subject"),
                        event["entity_type"],
                        event["entity_id"],
                        event.get("origin", "codex"),
                        event.get("review_status"),
                        event.get("summary"),
                        event["created_at"],
                    ),
                )
                count += 1
            connection.commit()
        return count

    def content_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM content_events
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def active_source_events_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT
                  content_events.rowid AS _rowid,
                  content_events.*,
                  proposed_patch_items.payload_json AS _proposal_payload_json,
                  proposed_patch_items.edited_payload_json AS _proposal_edited_payload_json
                FROM content_events
                LEFT JOIN change_batches ON change_batches.id = content_events.change_batch_id
                LEFT JOIN proposed_patch_items ON proposed_patch_items.id = change_batches.proposed_patch_item_id
                WHERE content_events.entity_type = ? AND content_events.entity_id = ?
                ORDER BY content_events.rowid
                """,
                (entity_type, entity_id),
            ).fetchall()
        last_grounding_rowid = 0
        for row in rows:
            if (
                row["event_type"] in {"created", "updated"}
                and row["review_status"] == "accepted"
                and _content_event_has_source_grounding(row)
            ):
                last_grounding_rowid = max(last_grounding_rowid, int(row["_rowid"]))
        active = []
        for row in rows:
            if row["event_type"] not in {"source_span_changed", "source_span_removed"}:
                continue
            if int(row["_rowid"]) <= last_grounding_rowid:
                continue
            payload = dict(row)
            payload.pop("_rowid", None)
            payload.pop("_proposal_payload_json", None)
            payload.pop("_proposal_edited_payload_json", None)
            active.append(payload)
        return active

    def reject_applied_proposal_item(
        self,
        proposal_item_id: str,
        *,
        content_event: Mapping[str, Any],
        decided_by: str = "learner",
        clock: Clock | None = None,
    ) -> bool:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            item_row = connection.execute(
                """
                SELECT proposed_patch_id FROM proposed_patch_items
                WHERE id = ? AND decision = 'accepted'
                """,
                (proposal_item_id,),
            ).fetchone()
            if item_row is None:
                return False
            connection.execute(
                """
                INSERT INTO content_events(
                  id, change_batch_id, event_type, subject, entity_type,
                  entity_id, origin, review_status, summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_event.get("id") or new_ulid(),
                    content_event.get("change_batch_id"),
                    content_event["event_type"],
                    content_event.get("subject"),
                    content_event["entity_type"],
                    content_event["entity_id"],
                    content_event.get("origin", "codex"),
                    content_event.get("review_status", "rejected"),
                    content_event.get("summary"),
                    content_event["created_at"],
                ),
            )
            connection.execute(
                """
                UPDATE proposed_patch_items
                SET decision = 'rejected',
                    decided_at = ?,
                    decided_by = ?,
                    updated_at = ?
                WHERE id = ? AND decision = 'accepted'
                """,
                (now, decided_by, now, proposal_item_id),
            )
            self._refresh_proposal_status(connection, item_row["proposed_patch_id"], updated_at=now)
            connection.commit()
        return True

    def set_proposal_item_decision(
        self,
        patch_id: str,
        decision: str,
        item_ids: list[str] | None = None,
        *,
        decided_by: str = "learner",
        clock: Clock | None = None,
    ) -> int:
        now = utc_now_iso(clock)
        parameters: list[Any] = [decision, now, decided_by, now, patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE proposed_patch_items
                SET decision = ?, decided_at = ?, decided_by = ?, updated_at = ?
                WHERE proposed_patch_id = ? AND decision = 'pending'{item_filter}
                """,
                parameters,
            )
            self._refresh_proposal_status(connection, patch_id, updated_at=now)
            connection.commit()
            return cursor.rowcount

    def delete_proposal_item(self, item_id: str, *, clock: Clock | None = None) -> bool:
        """Permanently remove a proposal item row, refreshing its batch status."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT proposed_patch_id FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                return False
            cursor = connection.execute(
                "DELETE FROM proposed_patch_items WHERE id = ?",
                (item_id,),
            )
            self._refresh_proposal_status(connection, row["proposed_patch_id"], updated_at=now)
            connection.commit()
            return cursor.rowcount > 0

    def reset_proposal_item_decision(
        self,
        patch_id: str,
        item_ids: list[str] | None = None,
        *,
        clock: Clock | None = None,
    ) -> int:
        """Reset a decided item back to ``pending`` — the inbox "undo" action.

        Scoped to the only reversible-without-side-effects case: a ``rejected`` item
        that was never applied to disk (``applied_change_batch_id IS NULL``). Accepted
        items (and rejected-after-revert items) carry a change batch and are excluded,
        so undo can never resurrect a proposal whose entity has already been written
        and would collide on re-accept.
        """

        now = utc_now_iso(clock)
        parameters: list[Any] = [now, patch_id]
        item_filter = ""
        if item_ids:
            placeholders = ",".join("?" for _ in item_ids)
            item_filter = f" AND id IN ({placeholders})"
            parameters.extend(item_ids)
        with self.connection() as connection:
            cursor = connection.execute(
                f"""
                UPDATE proposed_patch_items
                SET decision = 'pending', decided_at = NULL, decided_by = NULL, updated_at = ?
                WHERE proposed_patch_id = ?
                  AND decision = 'rejected'
                  AND applied_change_batch_id IS NULL{item_filter}
                """,
                parameters,
            )
            self._refresh_proposal_status(connection, patch_id, updated_at=now)
            connection.commit()
            return cursor.rowcount

    def _refresh_proposal_status(self, connection: sqlite3.Connection, patch_id: str, *, updated_at: str) -> None:
        rows = connection.execute(
            """
            SELECT decision, validation_status, COUNT(*) AS count
            FROM proposed_patch_items
            WHERE proposed_patch_id = ?
            GROUP BY decision, validation_status
            """,
            (patch_id,),
        ).fetchall()
        if not rows:
            return
        total = sum(row["count"] for row in rows)
        accepted = sum(row["count"] for row in rows if row["decision"] == "accepted")
        rejected = sum(row["count"] for row in rows if row["decision"] == "rejected")
        pending = sum(row["count"] for row in rows if row["decision"] == "pending")
        invalid = sum(row["count"] for row in rows if row["validation_status"] == "invalid")
        if invalid == total:
            status = "invalid"
        elif accepted == total:
            status = "accepted"
        elif rejected == total:
            status = "rejected"
        elif accepted > 0 or rejected > 0:
            status = "partially_accepted"
        elif pending == total:
            status = "pending"
        else:
            status = "pending"
        connection.execute(
            "UPDATE proposed_patches SET status_cache = ?, updated_at = ? WHERE id = ?",
            (status, updated_at, patch_id),
        )

    def insert_synthesis_manifest(self, manifest: Mapping[str, Any]) -> str:
        """Persist an immutable synthesis manifest (§8.4). Idempotent on
        ``manifest_hash`` — an identical manifest returns the existing id and is
        never re-inserted."""

        manifest_hash = str(manifest["manifest_hash"])
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id FROM synthesis_manifests WHERE manifest_hash = ?",
                (manifest_hash,),
            ).fetchone()
            if existing is not None:
                return existing["id"]
            row_id = str(manifest.get("id") or new_ulid())
            connection.execute(
                """
                INSERT INTO synthesis_manifests(
                  id, manifest_hash, source_set_id, membership_json,
                  revision_ids_json, asset_hashes_json, extraction_ids_json,
                  unit_inventory_versions_json, scope_json, brief_json,
                  prompt_version, schema_version, provider, model,
                  extractor_versions_json, curriculum_snapshot_hash,
                  facet_registry_hash, task_graph_hash, assessment_schema_version,
                  learner_model_contract_version, lock_fingerprint,
                  token_budget_json, estimated_usage_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    manifest_hash,
                    manifest.get("source_set_id"),
                    _json(manifest.get("membership")),
                    _json(manifest.get("revision_ids")),
                    _json(manifest.get("asset_hashes")),
                    _json(manifest.get("extraction_ids")),
                    _json(manifest.get("unit_inventory_versions")),
                    _json(manifest.get("scope")),
                    _json(manifest.get("brief")),
                    manifest.get("prompt_version"),
                    manifest.get("schema_version"),
                    manifest.get("provider"),
                    manifest.get("model"),
                    _json(manifest.get("extractor_versions")),
                    manifest.get("curriculum_snapshot_hash"),
                    manifest.get("facet_registry_hash"),
                    manifest.get("task_graph_hash"),
                    manifest.get("assessment_schema_version"),
                    manifest.get("learner_model_contract_version"),
                    manifest.get("lock_fingerprint"),
                    _json(manifest.get("token_budget")),
                    _json(manifest.get("estimated_usage")),
                    manifest.get("created_at") or utc_now_iso(),
                ),
            )
            connection.commit()
        return row_id

    def synthesis_manifest(self, manifest_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_manifests WHERE id = ?",
                (manifest_id,),
            ).fetchone()
        return _decode_synthesis_manifest(row) if row is not None else None

    def synthesis_manifest_by_hash(self, manifest_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_manifests WHERE manifest_hash = ?",
                (manifest_hash,),
            ).fetchone()
        return _decode_synthesis_manifest(row) if row is not None else None

    def completed_synthesis_manifests(self, source_set_id: str) -> list[dict[str, Any]]:
        """The manifest of each completed synthesis run of a source set, oldest
        first, with the run's ``proposal_id`` beside it."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT m.*, r.proposal_id AS proposal_id
                FROM synthesis_runs r JOIN synthesis_manifests m ON m.id = r.manifest_id
                WHERE m.source_set_id = ? AND r.status = 'completed'
                ORDER BY r.created_at, r.id
                """,
                (source_set_id,),
            ).fetchall()
        return [_decode_synthesis_manifest(row) for row in rows]

    def insert_synthesis_run(
        self,
        *,
        manifest_id: str,
        mode: str,
        agent_run_id: str | None = None,
        proposal_id: str | None = None,
        span_request: Any = None,
        status: str = "created",
        run_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = run_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO synthesis_runs(
                  id, manifest_id, mode, agent_run_id, proposal_id,
                  span_request_json, resolved_span_hashes_json,
                  coverage_decisions_json, actual_usage_json, status,
                  created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    manifest_id,
                    mode,
                    agent_run_id,
                    proposal_id,
                    _json(span_request) if span_request is not None else None,
                    None,
                    None,
                    None,
                    status,
                    utc_now_iso(clock),
                    None,
                ),
            )
            connection.commit()
        return row_id

    def complete_synthesis_run(
        self,
        run_id: str,
        *,
        status: str,
        proposal_id: str | None = None,
        resolved_span_hashes: Any = None,
        coverage_decisions: Any = None,
        actual_usage: Any = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE synthesis_runs
                   SET status = ?,
                       proposal_id = COALESCE(?, proposal_id),
                       resolved_span_hashes_json = COALESCE(?, resolved_span_hashes_json),
                       coverage_decisions_json = COALESCE(?, coverage_decisions_json),
                       actual_usage_json = COALESCE(?, actual_usage_json),
                       completed_at = ?
                 WHERE id = ?
                """,
                (
                    status,
                    proposal_id,
                    _json(resolved_span_hashes) if resolved_span_hashes is not None else None,
                    _json(coverage_decisions) if coverage_decisions is not None else None,
                    _json(actual_usage) if actual_usage is not None else None,
                    utc_now_iso(clock),
                    run_id,
                ),
            )
            connection.commit()

    def synthesis_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_runs WHERE id = ?", (run_id,)
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def synthesis_run_for_agent_run(self, agent_run_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_runs WHERE agent_run_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (agent_run_id,),
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def save_synthesis_candidate(self, run_id: str, candidate: Mapping[str, Any]) -> None:
        """Stage model output before gates and proposal persistence."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE synthesis_runs SET candidate_output_json = ? WHERE id = ?",
                (_json(dict(candidate)), run_id),
            )
            connection.commit()

    def save_synthesis_shard_result(
        self,
        *,
        shard_key: str,
        shard_ordinal: int,
        shard_count: int,
        result: Mapping[str, Any],
        manifest_hash: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Persist one completed synthesis shard's model output (durable checkpoint).

        Keyed by the request key of the shard's first pass (what it sends), so a
        retried synthesis reuses finished shards at zero model cost, including
        retries whose revised token ceilings mint a different manifest."""

        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO synthesis_shard_results(
                  shard_key, manifest_hash, shard_ordinal, shard_count, output_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(shard_key) DO UPDATE SET
                  manifest_hash = excluded.manifest_hash,
                  shard_ordinal = excluded.shard_ordinal,
                  shard_count = excluded.shard_count,
                  output_json = excluded.output_json
                """,
                (
                    shard_key,
                    manifest_hash,
                    shard_ordinal,
                    shard_count,
                    _json(dict(result)),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def synthesis_shard_result(self, shard_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM synthesis_shard_results WHERE shard_key = ?", (shard_key,)
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["output"] = _loads(data.pop("output_json", None), None)
        return data

    def discard_synthesis_shard_result(self, shard_key: str, *, output: Mapping[str, Any] | None = None) -> None:
        """Delete one shard's saved output, so the next synthesis pays for a
        fresh answer instead of replaying one the quality gates rejected.

        With ``output`` (the output that was judged), only while the row still
        holds it: another run may have saved a fresh one under the key since.
        Compared on the stored text, which :meth:`save_synthesis_shard_result`
        writes with the same serialization."""

        with self.connection() as connection:
            if output is None:
                connection.execute("DELETE FROM synthesis_shard_results WHERE shard_key = ?", (shard_key,))
            else:
                connection.execute(
                    "DELETE FROM synthesis_shard_results WHERE shard_key = ? AND output_json = ?",
                    (shard_key, _json(dict(output))),
                )
            connection.commit()

    def finalize_stale_synthesis_runs(
        self, *, before_iso: str, clock: Clock | None = None
    ) -> list[str]:
        """Mark abandoned non-terminal synthesis runs failed (startup hygiene).

        Historical error paths did not always finalize the run row, leaving
        'created'/'running' rows behind forever. Only rows created before
        ``before_iso`` are touched, so a currently-executing synthesis (whose
        worker holds a live job lease) is never finalized under it. Preserved
        candidates stay in place — only the status/completed_at are stamped."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id FROM synthesis_runs
                 WHERE status IN ('created', 'running') AND created_at < ?
                 ORDER BY created_at, id
                """,
                (before_iso,),
            ).fetchall()
            run_ids = [row["id"] for row in rows]
            if run_ids:
                now = utc_now_iso(clock)
                connection.executemany(
                    "UPDATE synthesis_runs SET status = 'failed', completed_at = ? WHERE id = ?",
                    [(now, run_id) for run_id in run_ids],
                )
            connection.commit()
        return run_ids

    def synthesis_run_introducing_entity(
        self, entity_type: str, entity_id: str
    ) -> dict[str, Any] | None:
        """The synthesis run whose proposal introduced an entity (patch -> run ->
        manifest lineage, §9.2). Resolved via the entity's applied content event's
        change batch -> proposal item -> proposed_patch -> synthesis_runs.proposal_id.
        """

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT synthesis_runs.*
                  FROM content_events
                  JOIN change_batches
                    ON change_batches.id = content_events.change_batch_id
                  JOIN proposed_patch_items
                    ON proposed_patch_items.id = change_batches.proposed_patch_item_id
                  JOIN synthesis_runs
                    ON synthesis_runs.proposal_id = proposed_patch_items.proposed_patch_id
                 WHERE content_events.entity_type = ?
                   AND content_events.entity_id = ?
                   AND content_events.event_type = 'created'
                 ORDER BY content_events.created_at
                 LIMIT 1
                """,
                (entity_type, entity_id),
            ).fetchone()
        return _decode_synthesis_run(row) if row is not None else None

    def insert_apply_intent(
        self,
        *,
        proposed_patch_id: str,
        item_ids: list[str],
        targets: list[Mapping[str, Any]],
        db_plan: list[Mapping[str, Any]],
        intent_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Durably commit the write-ahead apply intent BEFORE any YAML is staged
        (§10.2). Returns the intent id."""

        row_id = intent_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO apply_intents(
                  id, proposed_patch_id, item_ids_json, targets_json,
                  db_plan_json, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (
                    row_id,
                    proposed_patch_id,
                    _json(list(item_ids)),
                    _json([dict(t) for t in targets]),
                    _json([dict(p) for p in db_plan]),
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def mark_apply_intent_applied(self, intent_id: str, *, clock: Clock | None = None) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'applied', applied_at = ? WHERE id = ?",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def pending_apply_intents(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM apply_intents WHERE status = 'pending' ORDER BY created_at, id"
            ).fetchall()
        return [_decode_apply_intent(row) for row in rows]

    def outstanding_apply_intents(self) -> list[dict[str, Any]]:
        """Intents that refuse the next accept: ``pending`` (mid-flight) and ``conflicted`` (K3.5).

        Below migration 255 the table has no ``conflicted`` rows, so this is the pending list there.
        """

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM apply_intents WHERE status IN ('pending', 'conflicted') ORDER BY created_at, id"
            ).fetchall()
        return [_decode_apply_intent(row) for row in rows]

    def apply_intent(self, intent_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM apply_intents WHERE id = ?", (intent_id,)).fetchone()
        return _decode_apply_intent(row) if row is not None else None

    def mark_apply_intent_conflicted(
        self, intent_id: str, conflicts: list[Mapping[str, Any]], *, clock: Clock | None = None
    ) -> None:
        """Recovery found target files changed since the intent (K3.5): nothing was written."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'conflicted', conflict_json = ?, conflicted_at = ? "
                "WHERE id = ? AND status IN ('pending', 'conflicted')",
                (_json([dict(c) for c in conflicts]), utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def mark_apply_intent_rolled_back(self, intent_id: str, *, clock: Clock | None = None) -> None:
        """The accept stopped before writing any file (K3.5: a target changed under it)."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE apply_intents SET status = 'rolled_back', rolled_back_at = ? WHERE id = ? AND status = 'pending'",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()

    def mark_apply_intent_set_aside(self, intent_id: str, *, clock: Clock | None = None) -> bool:
        """The owner kept the files as they are (K3.5); True when a conflicted intent was settled."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE apply_intents SET status = 'set_aside', set_aside_at = ? WHERE id = ? AND status = 'conflicted'",
                (utc_now_iso(clock), intent_id),
            )
            connection.commit()
        return cursor.rowcount == 1
