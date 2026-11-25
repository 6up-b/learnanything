"""Reader annotations, source objects and reading progress.

Owns source annotations and their versions, events and anchors; source objects,
citations and relations; reader requests, authored questions and section progress."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.row_serialization import _json, _loads
from learnloop.ids import new_ulid

#: The undo of one delete intent (reader-pdf-selection): a disposition event
#: naming the delete it withdraws. ``{delete}`` is the delete event's id and
#: ``{annotation}`` the annotation id, as SQL expressions.
_UNDO_OF = (
    "SELECT u.id FROM source_annotation_events u WHERE u.annotation_id = {annotation} "
    "AND u.event_type = 'disposition' AND json_extract(u.payload_json, '$.undo') = 'delete_intent' "
    "AND json_extract(u.payload_json, '$.event_id') = {delete}"
)

#: Whether a delete intent of an annotation stands: one no undo names. An undo
#: withdraws the one delete it names and never another, so a delete written
#: while a restore was under way still hides the annotation (Codex review F3).
#: ``{annotation}`` is the annotation id's SQL expression.
_STANDING_DELETE = (
    "EXISTS (SELECT 1 FROM source_annotation_events d WHERE d.annotation_id = {annotation} "
    "AND d.event_type = 'delete_intent' AND NOT EXISTS ("
    + _UNDO_OF.format(annotation="d.annotation_id", delete="d.id")
    + "))"
)


# What ``reader_section_progress.generation_batch_id`` holds besides NULL (not finished, or not yet stamped) and
# the id of the batch writing a finished section's questions. When each is written is
# ``learnloop.reader.section_generation``'s rule.
#: A section job was being queued (older versions took it before the queueing and replaced it with the batch id
#: after; one whose process died between the two still holds it). Nothing writes it now: the claim, the batch and
#: :data:`SECTION_TOPIC_MANAGED` are one transaction.
SECTION_ENQUEUING = "enqueuing"
#: Finished on the phone host, whose own work never includes model calls: the desktop starts it.
SECTION_DEFERRED_TO_PRIMARY = "deferred_to_primary"
#: Finished before the build that writes its chapter's topics had settled: started when it has.
SECTION_WAITING_FOR_BUILD = "waiting_for_build"
#: Settled with nothing to write: its chapter's build had settled, and no topic citing it needed questions.
SECTION_NONE_NEEDED = "none_needed_after_build"
#: What older versions wrote for "nothing to write", also while the book's topics were not in yet; read as
#: undecided and decided again once.
SECTION_NONE_NEEDED_BEFORE = "none_needed"
#: The section's question work is its topics' claims in ``reader_topic_question_work`` (migration 257), each
#: naming the batch queued with it. Not a batch id (never an ``ingest_batches`` row), and not "finished".
SECTION_TOPIC_MANAGED = "topic_managed"

#: The purpose of a topic's claim: the first set of questions a learner's reading commissions for it.
READER_FIRST_SET = "reader_first_set"

_TOPIC_WORK_JSON = ("passage_ids_json", "source_refs_json", "proposal_ids_json", "model_settings_json")


def _topic_work_row(row: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for name in _TOPIC_WORK_JSON:
        value = out.pop(name)
        out[name.removesuffix("_json")] = json.loads(value) if value is not None else None
    return out


def settle_reviewed_topic_work(connection: sqlite3.Connection, patch_id: str, *, updated_at: str) -> None:
    """A decision on ``patch_id``'s questions (an OK, a refusal, an undone refusal) moves the topic work that wrote
    them between ``held`` and ``written`` by the rule the writing job used: held while any question of its proposals
    waits for a decision. Called on the decision's own connection, inside its transaction, so the two never
    disagree. Work in any other state (queued, running, failed, not needed) is the job's to move and is left."""

    rows = connection.execute(
        "SELECT id, state, proposal_ids_json FROM reader_topic_question_work WHERE owner = 'topic'"
        " AND state IN ('held', 'written')"
        " AND EXISTS (SELECT 1 FROM json_each(proposal_ids_json) WHERE value = ?)",
        (patch_id,),
    ).fetchall()
    for row in rows:
        patches = json.loads(row["proposal_ids_json"] or "[]")
        waiting = connection.execute(
            "SELECT 1 FROM proposed_patch_items WHERE decision = 'pending'"
            f" AND proposed_patch_id IN ({', '.join('?' for _ in patches)}) LIMIT 1",
            patches,
        ).fetchone()
        state = "held" if waiting is not None else "written"
        if state != row["state"]:
            connection.execute(
                "UPDATE reader_topic_question_work SET state = ?, updated_at = ? WHERE id = ?",
                (state, updated_at, row["id"]),
            )


def _completed_sections(connection: sqlite3.Connection, extraction_id: str, section_ids: Sequence[str]) -> set[str]:
    """The sections among ``section_ids`` whose progress row already holds a completion. A completion never clears,
    so a writer that read one here can leave it out of its upsert whatever commits in between."""

    wanted = list(dict.fromkeys(section_ids))
    if not wanted:
        return set()
    placeholders = ", ".join("?" for _ in wanted)
    rows = connection.execute(
        "SELECT section_id FROM reader_section_progress "
        f"WHERE extraction_id = ? AND section_id IN ({placeholders}) AND completed_at IS NOT NULL",
        (extraction_id, *wanted),
    ).fetchall()
    return {str(row[0]) for row in rows}


class ReaderStoreMixin:

    def insert_source_exposure_event(
        self, event: Mapping[str, Any], *, clock: Clock | None = None
    ) -> str:
        """Record one Open-in-source view (§9.2). Called on every span view.

        RO0 row 4's initiator fields (``router_objective.exposure``) are never in
        the row's insert (landing ruling R1): they follow in their own savepoint,
        so a refused receipt leaves the opening and its coldness exposure."""

        from learnloop.db.stores import router_objective as receipts

        event, receipt = receipts.split_receipt("source_exposure_events", event)
        event_id = str(event.get("id") or new_ulid())
        now = event.get("created_at") or utc_now_iso(clock)
        section_path = event.get("section_path") or []
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_exposure_events(
                  id, context, extraction_id, span_id, revision_id, source_id,
                  entity_type, entity_id, page, locator, section_path_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("context") or "other",
                    event["extraction_id"],
                    event["span_id"],
                    event.get("revision_id"),
                    event.get("source_id"),
                    event.get("entity_type"),
                    event.get("entity_id"),
                    event.get("page"),
                    event.get("locator"),
                    _json(list(section_path)),
                    now,
                ),
            )
            # RO0 row 4, after the row: who initiated it, only where that was read.
            receipts.fill_receipt(connection, "source_exposure_events", event_id, receipt)
            connection.commit()
        return event_id

    def source_exposure_events(
        self,
        *,
        extraction_id: str | None = None,
        span_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        after: str | None = None,
        before: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if extraction_id is not None:
            clauses.append("extraction_id = ?")
            params.append(extraction_id)
        if span_id is not None:
            clauses.append("span_id = ?")
            params.append(span_id)
        if entity_type is not None:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if entity_id is not None:
            clauses.append("entity_id = ?")
            params.append(entity_id)
        if after is not None:
            clauses.append("created_at > ?")
            params.append(after)
        if before is not None:
            clauses.append("created_at < ?")
            params.append(before)
        query = "SELECT * FROM source_exposure_events"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            raw = data.pop("section_path_json", None)
            data["section_path"] = json.loads(raw) if raw else []
            events.append(data)
        return events

    # ------------------------------------------------------------------
    # P3 reader integration (spec_p3_reader_integration slice 1)
    # ------------------------------------------------------------------

    # -- render views + crosswalk (§3.2) --

    def insert_render_view(self, view: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        view_id = view.get("id") or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_render_views(
                  id, source_id, revision_id, extraction_id, renderer, renderer_version,
                  model_version, config_version, schema_version, content_hash,
                  asset_manifest_hash, status, health_summary_json, predecessor_view_id,
                  predecessor_reason, output_ref, request_hash, result_hash,
                  created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    view_id,
                    view["source_id"],
                    view["revision_id"],
                    view["extraction_id"],
                    view.get("renderer", "marker_markdown"),
                    view["renderer_version"],
                    view.get("model_version"),
                    view.get("config_version"),
                    view["schema_version"],
                    view["content_hash"],
                    view.get("asset_manifest_hash"),
                    view.get("status", "ready"),
                    _json(view.get("health_summary", {})),
                    view.get("predecessor_view_id"),
                    view.get("predecessor_reason"),
                    view.get("output_ref"),
                    view["request_hash"],
                    view.get("result_hash"),
                    now,
                    view.get("completed_at", now),
                ),
            )
            connection.commit()
        return view_id

    def get_render_view(self, render_view_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_render_views WHERE id = ?", (render_view_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def render_view_by_request_hash(self, request_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_render_views WHERE request_hash = ?", (request_hash,)
            ).fetchone()
        return dict(row) if row is not None else None

    def insert_render_crosswalk_nodes(
        self, render_view_id: str, nodes: Sequence[Mapping[str, Any]], *, clock: Clock | None = None
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            for ordinal, node in enumerate(nodes):
                connection.execute(
                    """
                    INSERT INTO source_render_block_crosswalk(
                      id, render_view_id, display_node_id, display_ordinal, extraction_id,
                      span_id, block_content_hash, block_ordinal, display_start, display_end,
                      katex_node_ids_json, asset_ids_json, status, reason, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        node.get("id") or new_ulid(),
                        render_view_id,
                        node["display_node_id"],
                        node.get("display_ordinal", ordinal),
                        node["extraction_id"],
                        node.get("span_id"),
                        node.get("block_content_hash"),
                        node.get("block_ordinal"),
                        node.get("display_start"),
                        node.get("display_end"),
                        _json(node.get("katex_node_ids", [])),
                        _json(node.get("asset_ids", [])),
                        node.get("status", "mapped"),
                        node.get("reason"),
                        now,
                    ),
                )
            connection.commit()

    def render_crosswalk(self, render_view_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_render_block_crosswalk WHERE render_view_id = ? "
                "ORDER BY display_ordinal, id",
                (render_view_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # -- block health (§3.4) --

    def upsert_block_health(self, health: Mapping[str, Any], *, clock: Clock | None = None) -> str:
        health_id = health.get("id") or new_ulid()
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_block_health(
                  id, extraction_id, span_id, analyzer_version, status, reason_flags_json,
                  signal_provenance_json, confidence, page_health_flags_json,
                  recommended_view, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(extraction_id, span_id, analyzer_version) DO UPDATE SET
                  status = excluded.status,
                  reason_flags_json = excluded.reason_flags_json,
                  signal_provenance_json = excluded.signal_provenance_json,
                  confidence = excluded.confidence,
                  page_health_flags_json = excluded.page_health_flags_json,
                  recommended_view = excluded.recommended_view
                """,
                (
                    health_id,
                    health["extraction_id"],
                    health["span_id"],
                    health["analyzer_version"],
                    health.get("status", "unknown"),
                    _json(health.get("reason_flags", [])),
                    _json(health.get("signal_provenance", {})),
                    health.get("confidence"),
                    _json(health.get("page_health_flags", [])),
                    health.get("recommended_view", "derived"),
                    now,
                ),
            )
            connection.commit()
        return health_id

    def block_health(self, extraction_id: str, span_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_block_health WHERE extraction_id = ? AND span_id = ? "
                "ORDER BY analyzer_version DESC, created_at DESC LIMIT 1",
                (extraction_id, span_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def block_health_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_block_health WHERE extraction_id = ? ORDER BY span_id",
                (extraction_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # -- annotations (§4) --

    def create_annotation(self, *, source_id: str, clock: Clock | None = None) -> str:
        annotation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_annotations(id, source_id, created_at) VALUES (?, ?, ?)",
                (annotation_id, source_id, utc_now_iso(clock)),
            )
            connection.commit()
        return annotation_id

    def next_annotation_version_ordinal(self, annotation_id: str) -> int:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(version_ordinal), 0) AS m FROM source_annotation_versions "
                "WHERE annotation_id = ?",
                (annotation_id,),
            ).fetchone()
        return int(row["m"]) + 1

    def annotation_head(self, annotation_id: str) -> dict[str, Any] | None:
        """Rebuildable annotation-head projection: the latest version + anchor + segments."""

        with self.connection() as connection:
            ann = connection.execute(
                "SELECT * FROM source_annotations WHERE id = ?", (annotation_id,)
            ).fetchone()
            if ann is None:
                return None
            version = connection.execute(
                "SELECT * FROM source_annotation_versions WHERE annotation_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (annotation_id,),
            ).fetchone()
            anchor = connection.execute(
                "SELECT * FROM source_annotation_anchor_versions WHERE annotation_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (annotation_id,),
            ).fetchone()
            segments: list[dict[str, Any]] = []
            if anchor is not None:
                seg_rows = connection.execute(
                    "SELECT * FROM source_annotation_anchor_segments WHERE anchor_version_id = ? "
                    "ORDER BY segment_ordinal",
                    (anchor["id"],),
                ).fetchall()
                segments = [dict(row) for row in seg_rows]
        return {
            "annotation": dict(ann),
            "version": dict(version) if version is not None else None,
            "anchor": dict(anchor) if anchor is not None else None,
            "segments": segments,
        }

    def annotations_for_source(self, source_id: str) -> list[dict[str, Any]]:
        """Annotation heads for a source, omitting delete-intended annotations.

        Deletion is a tombstone disposition event (§4.1) — history keeps every
        version and event, but the reading-surface listing honors the learner's
        delete intent. An undo (a disposition event withdrawing one delete by
        its id, reader-pdf-selection) lists it again once no other delete of it
        stands."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT a.id FROM source_annotations a WHERE a.source_id = ? AND NOT "
                + _STANDING_DELETE.format(annotation="a.id")
                + " ORDER BY a.created_at, a.id",
                (source_id,),
            ).fetchall()
        return [self.annotation_head(row["id"]) for row in rows]

    def standing_annotation_ids(self) -> set[str]:
        """Every annotation the Reader lists (no standing delete intent): curriculum C2b's
        vault notes read the learner's annotations by this rule."""

        with self.connection() as connection:
            if connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'source_annotations'").fetchone() is None:
                return set()
            return {str(row[0]) for row in connection.execute(
                "SELECT a.id FROM source_annotations a WHERE NOT " + _STANDING_DELETE.format(annotation="a.id"))}

    def withdraw_annotation_delete(
        self, *, annotation_id: str, delete_event_id: str, clock: Clock | None = None
    ) -> tuple[str, str | None, bool]:
        """Undo one delete intent of an annotation: checked and written in one
        immediate transaction, so no other write lands between the check and
        the undo. Returns ``(outcome, undo_event_id, listed)``: ``restored``
        with the new undo's id; ``already_withdrawn`` (a retry: an undo names
        it already) or ``not_a_delete`` (no such delete of this annotation)
        with no id; ``listed`` is whether no delete of it stands afterwards."""

        standing = "SELECT " + _STANDING_DELETE.format(annotation="?") + " AS hidden"
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")

            def listed() -> bool:
                return not connection.execute(standing, (annotation_id,)).fetchone()["hidden"]

            delete = connection.execute(
                "SELECT id FROM source_annotation_events WHERE id = ? AND annotation_id = ? "
                "AND event_type = 'delete_intent'",
                (delete_event_id, annotation_id),
            ).fetchone()
            if delete is None:
                return ("not_a_delete", None, listed())
            undone = connection.execute(_UNDO_OF.format(annotation="?", delete="?") + " LIMIT 1",
                                        (annotation_id, delete_event_id)).fetchone()
            if undone is not None:
                return ("already_withdrawn", None, listed())
            event_id = new_ulid()
            connection.execute(
                "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, annotation_id, "disposition",
                 _json({"undo": "delete_intent", "event_id": delete_event_id}), utc_now_iso(clock)),
            )
            return ("restored", event_id, listed())

    def annotation_history(self, annotation_id: str) -> dict[str, Any]:
        with self.connection() as connection:
            versions = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM source_annotation_versions WHERE annotation_id = ? "
                    "ORDER BY version_ordinal",
                    (annotation_id,),
                ).fetchall()
            ]
            anchors = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM source_annotation_anchor_versions WHERE annotation_id = ? "
                    "ORDER BY version_ordinal",
                    (annotation_id,),
                ).fetchall()
            ]
            events = [
                dict(r)
                for r in connection.execute(
                    "SELECT * FROM source_annotation_events WHERE annotation_id = ? "
                    "ORDER BY created_at, id",
                    (annotation_id,),
                ).fetchall()
            ]
        return {"versions": versions, "anchors": anchors, "events": events}

    def append_annotation_event(
        self, *, annotation_id: str, event_type: str, payload: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        event_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, annotation_id, event_type, _json(dict(payload or {})), utc_now_iso(clock)),
            )
            connection.commit()
        return event_id

    def _write_annotation_version(
        self, connection: sqlite3.Connection, *, annotation_id: str, version_ordinal: int,
        version: Mapping[str, Any], now: str,
    ) -> str:
        version_id = new_ulid()
        connection.execute(
            """
            INSERT INTO source_annotation_versions(
              id, annotation_id, version_ordinal, annotation_type, learner_text,
              what_i_think_is_going_on, privacy_locality, authorship,
              client_idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                annotation_id,
                version_ordinal,
                version["annotation_type"],
                version.get("learner_text", ""),
                version.get("what_i_think_is_going_on"),
                version.get("privacy_locality", "local_private"),
                version.get("authorship", "learner"),
                version.get("client_idempotency_key"),
                now,
            ),
        )
        return version_id

    def _write_anchor_version(
        self, connection: sqlite3.Connection, *, annotation_id: str, version_ordinal: int,
        anchor: Mapping[str, Any], now: str,
    ) -> str:
        anchor_id = new_ulid()
        connection.execute(
            """
            INSERT INTO source_annotation_anchor_versions(
              id, annotation_id, version_ordinal, source_id, revision_id, extraction_id,
              render_view_id, status, algo_version, confidence, raw_selection_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                anchor_id,
                annotation_id,
                version_ordinal,
                anchor["source_id"],
                anchor["revision_id"],
                anchor["extraction_id"],
                anchor.get("render_view_id"),
                anchor["status"],
                anchor.get("algo_version", "anchor-v1"),
                anchor.get("confidence"),
                _json(anchor["raw_selection"]) if anchor.get("raw_selection") is not None else None,
                now,
            ),
        )
        for seg_ordinal, seg in enumerate(anchor.get("segments", [])):
            connection.execute(
                """
                INSERT INTO source_annotation_anchor_segments(
                  id, anchor_version_id, segment_ordinal, span_id, block_content_hash,
                  codepoint_start, codepoint_end, exact_quote, prefix, suffix,
                  geometry_json, section_path_json, neighbor_hashes_json,
                  selection_text_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_ulid(),
                    anchor_id,
                    seg_ordinal,
                    seg["span_id"],
                    seg["block_content_hash"],
                    seg["codepoint_start"],
                    seg["codepoint_end"],
                    seg["exact_quote"],
                    seg.get("prefix", ""),
                    seg.get("suffix", ""),
                    _json(seg["geometry"]) if seg.get("geometry") is not None else None,
                    _json(seg.get("section_path", [])),
                    _json(seg.get("neighbor_hashes", [])),
                    seg["selection_text_hash"],
                    now,
                ),
            )
        return anchor_id

    def append_annotation_version(
        self, *, annotation_id: str, version: Mapping[str, Any], anchor: Mapping[str, Any],
        event_type: str = "edit", event_payload: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> dict[str, str]:
        now = utc_now_iso(clock)
        ordinal = self.next_annotation_version_ordinal(annotation_id)
        with self.connection() as connection:
            version_id = self._write_annotation_version(
                connection, annotation_id=annotation_id, version_ordinal=ordinal, version=version, now=now
            )
            anchor_id = self._write_anchor_version(
                connection, annotation_id=annotation_id, version_ordinal=ordinal, anchor=anchor, now=now
            )
            event_id = new_ulid()
            connection.execute(
                "INSERT INTO source_annotation_events(id, annotation_id, event_type, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, annotation_id, event_type, _json(dict(event_payload or {})), now),
            )
            connection.commit()
        return {"version_id": version_id, "anchor_id": anchor_id, "event_id": event_id, "version_ordinal": str(ordinal)}

    # -- capture outbox (§5.3) --

    def capture_by_client_key(self, client_idempotency_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE client_idempotency_key = ?",
                (client_idempotency_key,),
            ).fetchone()
        return dict(row) if row is not None else None

    def pending_capture_outbox(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE state = 'pending' "
                "ORDER BY created_at, id LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def recoverable_capture_outbox(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Rows a drain may claim: `pending` plus stale `draining` rows left behind
        by a crash mid-drain. Reclaiming a `draining` row is safe because conversion
        is idempotent (§15.2)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE state IN ('pending', 'draining') "
                "ORDER BY created_at, id LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_capture_outbox(self, outbox_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_capture_outbox WHERE id = ?", (outbox_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def mark_capture_outbox(
        self, outbox_id: str, *, state: str, target_ref: str | None = None,
        last_error: str | None = None, bump_attempts: bool = False, clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        drained = now if state == "done" else None
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE reader_capture_outbox
                SET state = ?, target_ref = COALESCE(?, target_ref), last_error = ?,
                    attempts = attempts + ?, updated_at = ?,
                    drained_at = COALESCE(?, drained_at)
                WHERE id = ?
                """,
                (state, target_ref, last_error, 1 if bump_attempts else 0, now, drained, outbox_id),
            )
            connection.commit()

    # ------------------------------------------------------------------
    # P3 slice 2: reader_background_requests (demand-paged synthesis, §6).
    # Fenced-lease durable queue -- mirrors the migration-080 surface-mint
    # precedent (lease_epoch bumped on claim; guarded writes fenced on it).
    # ------------------------------------------------------------------

    _READER_REQUEST_TERMINAL = ("complete", "failed", "cancelled", "obsolete")

    def enqueue_reader_request(
        self, *, request_key: str, fields: Mapping[str, Any], revive_cancelled: bool = False,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Idempotent enqueue keyed on ``request_key`` (§6.2): the same contract reuses
        the standing row; a material version change has a different key -> a new row.

        ``revive_cancelled`` (a capture's conversion, Codex re-review of RW1b, F15):
        a standing row that was cancelled, or flagged for cancellation while it
        ran, is made runnable again instead of reused dead, because a new
        capture asks for that work. The row keeps its id and its first
        capture; a completed, failed or obsolete row is reused as before.

        A revival rebinds the row to the reviving capture (its annotation and
        commitment), so the model sees the live capture's inputs and the result
        maps to its commitment, never the reverted capture's stopped one (Codex
        final verify of RW1b, F16). The key carries the capture's instructions,
        so a revival only ever happens between captures asking the same thing."""

        existing = self.reader_request_by_key(request_key)
        if existing is not None:
            if revive_cancelled and (existing["status"] == "cancelled" or (
                    existing["cancel_requested"] and existing["status"] in ("queued", "running"))):
                rebind = fields.get("annotation_id") is not None
                with self.connection() as connection:
                    connection.execute(
                        "UPDATE reader_background_requests "
                        "SET cancel_requested = 0, updated_at = ?, "
                        "    annotation_id = CASE WHEN ? THEN ? ELSE annotation_id END, "
                        "    commitment_id = CASE WHEN ? THEN ? ELSE commitment_id END, "
                        "    lease_owner = CASE WHEN status = 'cancelled' THEN NULL ELSE lease_owner END, "
                        "    lease_expires_at = CASE WHEN status = 'cancelled' THEN NULL ELSE lease_expires_at END, "
                        "    completed_at = CASE WHEN status = 'cancelled' THEN NULL ELSE completed_at END, "
                        "    status = CASE WHEN status = 'cancelled' THEN 'queued' ELSE status END "
                        "WHERE id = ? AND (status = 'cancelled' OR "
                        "      (cancel_requested = 1 AND status IN ('queued', 'running')))",
                        (utc_now_iso(clock), int(rebind), fields.get("annotation_id"),
                         int(rebind), fields.get("commitment_id"), existing["id"]),
                    )
                    connection.commit()
                revived = self.get_reader_request(existing["id"]) or existing
                return {"id": existing["id"], "deduplicated": True, "status": revived["status"], "revived": True}
            return {"id": existing["id"], "deduplicated": True, "status": existing["status"]}
        now = utc_now_iso(clock)
        request_id = new_ulid()
        cols = {
            "id": request_id,
            "request_key": request_key,
            "source_id": fields["source_id"],
            "revision_id": fields["revision_id"],
            "extraction_id": fields["extraction_id"],
            "span_id": fields.get("span_id", ""),
            "window_json": _json(fields.get("window", {})),
            "preset": fields.get("preset", ""),
            "action": fields.get("action", ""),
            "inventory_profile": fields.get("inventory_profile", "semantic"),
            "inventory_schema_version": fields.get("inventory_schema_version", ""),
            "synthesis_schema_version": fields.get("synthesis_schema_version", ""),
            "prompt_version": fields.get("prompt_version", ""),
            "provider": fields.get("provider", ""),
            "model": fields.get("model", ""),
            "config_hash": fields.get("config_hash", ""),
            "priority_band": int(fields.get("priority_band", 0)),
            "est_input_tokens": int(fields.get("est_input_tokens", 0)),
            "est_output_tokens": int(fields.get("est_output_tokens", 0)),
            "token_cap": int(fields.get("token_cap", 0)),
            "cache_hit": 1 if fields.get("cache_hit") else 0,
            "reason": fields.get("reason"),
            "annotation_id": fields.get("annotation_id"),
            "commitment_id": fields.get("commitment_id"),
            "client_idempotency_key": fields.get("client_idempotency_key"),
            "created_at": now,
            "updated_at": now,
        }
        placeholders = ", ".join("?" for _ in cols)
        try:
            with self.connection() as connection:
                connection.execute(
                    f"INSERT INTO reader_background_requests({', '.join(cols)}) VALUES ({placeholders})",
                    tuple(cols.values()),
                )
                connection.commit()
        except sqlite3.IntegrityError:
            existing = self.reader_request_by_key(request_key)
            if existing is not None:
                return {"id": existing["id"], "deduplicated": True, "status": existing["status"]}
            raise
        return {"id": request_id, "deduplicated": False, "status": "queued"}

    def has_queued_reader_requests(self) -> bool:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM reader_background_requests WHERE status = 'queued' LIMIT 1"
            ).fetchone()
        return row is not None

    def reader_request_by_key(self, request_key: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_background_requests WHERE request_key = ?", (request_key,)
            ).fetchone()
        return dict(row) if row is not None else None

    def get_reader_request(self, request_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_background_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def reader_requests_for_source(self, source_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_background_requests WHERE source_id = ? "
                "ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def claim_next_reader_request(
        self, *, worker_id: str, now_iso: str, lease_expires_at: str, lease_cutoff_iso: str
    ) -> dict[str, Any] | None:
        """Claim the highest-priority runnable request under a fenced lease. Bumps
        ``lease_epoch`` so a stale worker's later write is rejected. Only one live
        lease at a time (BEGIN IMMEDIATE + live-lease guard)."""

        connection = self.connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            live = connection.execute(
                "SELECT 1 FROM reader_background_requests "
                "WHERE status = 'running' AND lease_expires_at IS NOT NULL AND lease_expires_at >= ? LIMIT 1",
                (lease_cutoff_iso,),
            ).fetchone()
            if live is not None:
                connection.rollback()
                return None
            row = connection.execute(
                "SELECT * FROM reader_background_requests "
                "WHERE cancel_requested = 0 AND (status = 'queued' OR "
                "      (status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < ?))) "
                "ORDER BY priority_band DESC, created_at, id LIMIT 1",
                (lease_cutoff_iso,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return None
            connection.execute(
                "UPDATE reader_background_requests "
                "SET status = 'running', lease_owner = ?, lease_expires_at = ?, "
                "    lease_epoch = lease_epoch + 1, attempt_count = attempt_count + 1, updated_at = ? "
                "WHERE id = ?",
                (worker_id, lease_expires_at, now_iso, row["id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM reader_background_requests WHERE id = ?", (row["id"],)
            ).fetchone()
            connection.commit()
            return dict(claimed)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def resolve_reader_request(
        self, *, request_id: str, status: str, result: Mapping[str, Any] | None = None,
        error: Mapping[str, Any] | None = None, actual_input_tokens: int = 0,
        actual_output_tokens: int = 0, cache_hit: bool = False,
        expected_lease_epoch: int | None = None, clock: Clock | None = None,
    ) -> bool:
        """Terminal/complete transition; releases the lease. A stale-epoch write (the
        job was re-claimed by another worker) matches zero rows and returns False."""

        now = utc_now_iso(clock)
        completed = now if status in self._READER_REQUEST_TERMINAL else None
        clauses = ["id = ?", "status = 'running'"]
        params: list[Any] = [
            status, _json(result or {}), _json(error) if error is not None else None,
            int(actual_input_tokens), int(actual_output_tokens), 1 if cache_hit else 0, now, completed,
            request_id,
        ]
        if expected_lease_epoch is not None:
            clauses.append("lease_epoch = ?")
            params.append(expected_lease_epoch)
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE reader_background_requests "
                "SET status = ?, result_json = ?, error_json = ?, "
                "    actual_input_tokens = ?, actual_output_tokens = ?, cache_hit = ?, "
                "    lease_owner = NULL, lease_expires_at = NULL, updated_at = ?, completed_at = ? "
                f"WHERE {' AND '.join(clauses)}",
                tuple(params),
            )
            connection.commit()
            return cursor.rowcount > 0

    def cancel_reader_request(self, request_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        """Request cancellation. Never touches the local capture (§6.2). A non-terminal
        request flips to ``cancelled``; a running one is flagged so the worker stops."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE reader_background_requests "
                "SET cancel_requested = 1, "
                "    status = CASE WHEN status IN ('queued') THEN 'cancelled' ELSE status END, "
                "    updated_at = ? WHERE id = ? AND status NOT IN ('complete','failed','cancelled','obsolete')",
                (now, request_id),
            )
            connection.commit()
        return self.get_reader_request(request_id)

    def reader_request_still_held(self, request_id: str, *, releasing_annotation_id: str) -> bool:
        """Whether a synthesis request is still wanted once the capture
        ``releasing_annotation_id`` lets go of it (Codex re-review of RW1b,
        F15). Requests dedupe by passage and preset, not by capture, so one
        row can serve several captures: those whose outbox row converted onto
        it (``target_ref``) and the capture that first made it. It is held
        while any of them other than the releasing one is not deleted, and
        always when no capture made it (an explicit enqueue)."""

        with self.connection() as connection:
            request = connection.execute(
                "SELECT annotation_id FROM reader_background_requests WHERE id = ?", (request_id,)
            ).fetchone()
            if request is None:
                return False
            if request["annotation_id"] is None:
                return True
            held = connection.execute(
                "SELECT 1 FROM (SELECT o.annotation_id FROM reader_capture_outbox o WHERE o.target_ref = ? "
                "UNION SELECT ?) h WHERE h.annotation_id IS NOT NULL AND h.annotation_id != ? AND NOT "
                + _STANDING_DELETE.format(annotation="h.annotation_id") + " LIMIT 1",
                (request_id, request["annotation_id"], releasing_annotation_id),
            ).fetchone()
        return held is not None

    def reader_request_standing_holder(
        self, request_id: str, *, releasing_annotation_id: str
    ) -> dict[str, Any] | None:
        """The latest capture other than ``releasing_annotation_id`` whose
        outbox row converted onto this request and whose annotation has no
        standing delete: the capture a request is rebound to when the capture
        it is bound to is reverted while another still holds it (Codex final
        verify of RW1b, F16). ``None`` when there is none."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT o.annotation_id, o.commitment_id FROM reader_capture_outbox o "
                "WHERE o.target_ref = ? AND o.annotation_id IS NOT NULL AND o.annotation_id != ? AND NOT "
                + _STANDING_DELETE.format(annotation="o.annotation_id")
                + " ORDER BY o.created_at DESC, o.id DESC LIMIT 1",
                (request_id, releasing_annotation_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def rebind_reader_request(
        self, request_id: str, *, annotation_id: str, commitment_id: str | None, clock: Clock | None = None
    ) -> None:
        """Bind a request to the capture it now serves (F16): the annotation
        whose instructions the model reads and the commitment its result maps to."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE reader_background_requests SET annotation_id = ?, commitment_id = ?, updated_at = ? "
                "WHERE id = ?",
                (annotation_id, commitment_id, utc_now_iso(clock), request_id),
            )
            connection.commit()

    def rekey_reader_request(
        self, request_id: str, *, request_key: str, clock: Clock | None = None
    ) -> str:
        """Move a request to the key its own instructions give it, freeing the
        key it held for a capture asking something else (Codex verify of RW1b
        fix round 3, F16 legacy rows). The caller runs this inside the write
        transaction that enqueues. When another row already holds that key the
        request takes ``<key>#legacy:<request id>``, a key no enqueue computes,
        so it is never reused or revived again. Returns the key it now holds."""

        with self.connection() as connection:
            taken = connection.execute(
                "SELECT 1 FROM reader_background_requests WHERE request_key = ? AND id != ?",
                (request_key, request_id),
            ).fetchone()
            key = f"{request_key}#legacy:{request_id}" if taken is not None else request_key
            connection.execute(
                "UPDATE reader_background_requests SET request_key = ?, updated_at = ? WHERE id = ?",
                (key, utc_now_iso(clock), request_id),
            )
            connection.commit()
        return key

    def append_reader_request_proposal(self, request_id: str, proposal: Mapping[str, Any]) -> None:
        """Record one more proposal in a completed request's result: the
        commitment mapping a rebind adds when the result had none to move
        (Codex verify of RW1b fix round 3, F16)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT result_json FROM reader_background_requests WHERE id = ?", (request_id,)
            ).fetchone()
            if row is None:
                return
            result = _loads(row["result_json"], {}) or {}
            result["proposals"] = [*(result.get("proposals") or []), dict(proposal)]
            connection.execute(
                "UPDATE reader_background_requests SET result_json = ? WHERE id = ?",
                (_json(result), request_id),
            )
            connection.commit()

    def capture_reverted(self, annotation_id: str, *, reason: str) -> bool:
        """Whether a delete of the annotation with this ``reason`` stands (one
        no undo names): the capture was reverted, so its outbox row converts
        to no work (Codex re-review of RW1b, F14). The revert reads the same
        predicate before it tombstones, so a revert after an undone one writes
        a new tombstone (Codex final verify of RW1b, F14)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM source_annotation_events d WHERE d.annotation_id = ? "
                "AND d.event_type = 'delete_intent' AND json_extract(d.payload_json, '$.reason') = ? "
                "AND NOT EXISTS (" + _UNDO_OF.format(annotation="d.annotation_id", delete="d.id") + ") LIMIT 1",
                (annotation_id, reason),
            ).fetchone()
        return row is not None

    def retry_reader_request(self, request_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
        """Reset a failed request to ``queued`` for another drain."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE reader_background_requests "
                "SET status = 'queued', cancel_requested = 0, lease_owner = NULL, "
                "    lease_expires_at = NULL, error_json = NULL, updated_at = ? "
                "WHERE id = ? AND status = 'failed'",
                (now, request_id),
            )
            connection.commit()
        return self.get_reader_request(request_id)

    # ------------------------------------------------------------------
    # Reader quick-check producer: AI-authored section-boundary questions
    # (migration 105). The row is the record — statuses live here, never on
    # new interaction-event kinds; answering never touches attempts/mastery.
    # ------------------------------------------------------------------

    def insert_reader_authored_question(
        self, *, fields: Mapping[str, Any], clock: Clock | None = None
    ) -> str:
        """Insert one authored question. Section rows (the default) write the
        same columns as before migration 185 and take its defaults; scoped rows
        (RW1a's inquiry checks) also carry their scope, style and anchors."""

        now = utc_now_iso(clock)
        question_id = f"raq_{new_ulid()}"
        columns = [
            "id", "extraction_id", "section_id", "source_id", "question_md",
            "expected_answer_md", "span_ids_json", "prompt_version", "provider",
            "model", "status", "created_at", "updated_at",
        ]
        values: list[Any] = [
            question_id,
            fields["extraction_id"],
            fields["section_id"],
            fields.get("source_id"),
            fields["question_md"],
            fields["expected_answer_md"],
            _json(list(fields.get("span_ids") or [])),
            fields.get("prompt_version", ""),
            fields.get("provider"),
            fields.get("model"),
            "proposed",
            now,
            now,
        ]
        scope_kind = fields.get("scope_kind") or "section"
        if scope_kind == "section":
            with self.connection() as connection:
                connection.execute(
                    f"INSERT INTO reader_authored_questions({', '.join(columns)}) "
                    f"VALUES ({', '.join('?' for _ in columns)})",
                    tuple(values),
                )
                connection.commit()
            return question_id
        columns += ["scope_kind", "question_style", "anchor_span_ids_json", "inquiry_root_event_id"]
        values += [
            scope_kind,
            fields.get("question_style") or "recall",
            _json(list(fields.get("anchor_span_ids") or [])),
            fields.get("inquiry_root_event_id"),
        ]
        if scope_kind == "selection":
            # RW1b (migration 208): whose words the expected answer is, and the
            # selection reuse key the database keeps unique.
            columns.append("answer_basis")
            values.append(fields.get("answer_basis"))
        # An inquiry row's reuse key (root exchange, prompt version) is unique
        # (migration 185): a second insert for the key writes nothing and the
        # row already there -- the one the learner may have answered -- wins.
        with self.connection() as connection:
            inserted = connection.execute(
                f"INSERT INTO reader_authored_questions({', '.join(columns)}) "
                f"VALUES ({', '.join('?' for _ in columns)}) ON CONFLICT DO NOTHING",
                tuple(values),
            ).rowcount
            connection.commit()
        if inserted:
            return question_id
        if scope_kind == "selection":
            existing = self.selection_reader_authored_question(
                extraction_id=str(fields["extraction_id"]),
                anchor_span_ids=list(fields.get("anchor_span_ids") or []),
                question_style=str(fields.get("question_style") or "recall"),
                prompt_version=str(fields.get("prompt_version", "")),
            )
        else:
            existing = self.inquiry_reader_authored_question(
                inquiry_root_event_id=str(fields.get("inquiry_root_event_id") or ""),
                prompt_version=str(fields.get("prompt_version", "")),
            )
        if existing is None:
            raise sqlite3.IntegrityError("reader_authored_questions refused a scoped row")
        return str(existing["id"])

    def inquiry_reader_authored_question(
        self, *, inquiry_root_event_id: str, prompt_version: str
    ) -> dict[str, Any] | None:
        """RW1a: the newest inquiry-scoped question for one root exchange and
        prompt version, any status -- its reuse key (a dismissed row suppresses
        re-authoring for its own key)."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_authored_questions "
                "WHERE scope_kind = 'inquiry' AND inquiry_root_event_id = ? AND prompt_version = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (inquiry_root_event_id, prompt_version),
            ).fetchone()
        return dict(row) if row is not None else None

    def selection_reader_authored_question(
        self, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...], question_style: str,
        prompt_version: str,
    ) -> dict[str, Any] | None:
        """RW1b: the selection-scoped question for one reuse key (extraction,
        anchor spans in reading order, style, prompt version), any status --
        a dismissed row suppresses re-authoring for its own key."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_authored_questions WHERE scope_kind = 'selection' AND extraction_id = ? "
                "AND anchor_span_ids_json = ? AND question_style = ? AND prompt_version = ? LIMIT 1",
                (extraction_id, _json(list(anchor_span_ids)), question_style, prompt_version),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_reader_authored_question(self, question_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_authored_questions WHERE id = ?", (question_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    # --- reader section progress (migration 106; reader-first seeding) --------

    def upsert_reader_section_progress(
        self,
        *,
        extraction_id: str,
        section_id: str,
        spans_seen: int | None = None,
        span_count: int | None = None,
        revealed: bool = False,
        completed: bool = False,
        keep_ahead_request: bool = False,
        seen_span_ids: Sequence[str] = (),
        end_span_id: str | None = None,
        observed_by: str | None = None,
        completion_cause: str | None = None,
        completion_version: str | None = None,
        clock: Clock | None = None,
    ) -> dict[str, Any]:
        """Monotone upsert: spans_seen/span_count only grow; revealed_at /
        completed_at stamp once and never clear; generation_batch_id untouched.

        ``completion_cause`` and ``completion_version`` (migration 259) are
        written with the completion that first stamps ``completed_at`` and never
        after: a later report, whatever it carries, keeps the original
        completion, its cause and its tag.

        ``keep_ahead_request`` also records this section as the book's reading
        request (``record_reading_request``) in the same transaction, so a
        saved report never loses the "keep one chapter ahead" it asked for
        (UX Phase 1 finishing pass, F8).

        ``seen_span_ids`` (passages of this section observed by the learner's
        own reading) and ``end_span_id`` (its last readable passage, so
        observed) are appended in the same transaction, by ``observed_by``
        (``desktop`` or ``phone``): a passage or an end already recorded keeps
        its first time and origin, so reports union and a smaller one removes
        nothing. The caller checks them against the reading
        (``learnloop.reader.seen_passages``)."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            if keep_ahead_request:
                self._record_reading_request_for_extraction(connection, extraction_id, section_id, now)
            if seen_span_ids or end_span_id is not None:
                if observed_by not in ("desktop", "phone"):
                    raise ValueError(f"a seen passage needs its origin, not {observed_by!r}")
                connection.executemany(
                    "INSERT INTO reader_seen_spans(extraction_id, span_id, section_id, first_seen_at, origin) "
                    "VALUES (?, ?, ?, ?, ?) ON CONFLICT(extraction_id, span_id) DO NOTHING",
                    [(extraction_id, str(span_id), section_id, now, observed_by) for span_id in dict.fromkeys(seen_span_ids)],
                )
                if end_span_id is not None:
                    connection.execute(
                        "INSERT INTO reader_section_ends(extraction_id, section_id, span_id, first_seen_at, origin) "
                        "VALUES (?, ?, ?, ?, ?) ON CONFLICT(extraction_id, section_id) DO NOTHING",
                        (extraction_id, section_id, end_span_id, now, observed_by),
                    )
            # A completion the row already holds is not sent again: it would be kept anyway, and the writer
            # fence's insert trigger (migration 276) fires before the conflict turns the insert into an update.
            stamps = completed and section_id not in _completed_sections(connection, extraction_id, [section_id])
            connection.execute(
                """
                INSERT INTO reader_section_progress(
                  extraction_id, section_id, spans_seen, span_count,
                  revealed_at, completed_at, generation_batch_id, updated_at,
                  completion_cause, completion_algorithm_version
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                ON CONFLICT(extraction_id, section_id) DO UPDATE SET
                  spans_seen = MAX(reader_section_progress.spans_seen, excluded.spans_seen),
                  span_count = MAX(reader_section_progress.span_count, excluded.span_count),
                  revealed_at = COALESCE(reader_section_progress.revealed_at, excluded.revealed_at),
                  completed_at = COALESCE(reader_section_progress.completed_at, excluded.completed_at),
                  -- Read against the row as it was: only the completion that stamps completed_at names its cause.
                  completion_cause = CASE WHEN reader_section_progress.completed_at IS NULL
                    THEN excluded.completion_cause ELSE reader_section_progress.completion_cause END,
                  completion_algorithm_version = CASE WHEN reader_section_progress.completed_at IS NULL
                    THEN excluded.completion_algorithm_version
                    ELSE reader_section_progress.completion_algorithm_version END,
                  updated_at = excluded.updated_at
                """,
                (
                    extraction_id,
                    section_id,
                    int(spans_seen or 0),
                    int(span_count or 0),
                    now if revealed else None,
                    now if stamps else None,
                    now,
                    completion_cause if stamps else None,
                    completion_version if stamps else None,
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM reader_section_progress WHERE extraction_id = ? AND section_id = ?",
                (extraction_id, section_id),
            ).fetchone()
        return dict(row)

    def reader_section_progress_row(self, extraction_id: str, section_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_section_progress WHERE extraction_id = ? AND section_id = ?",
                (extraction_id, section_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def reader_section_progress_for(self, extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_section_progress WHERE extraction_id = ? ORDER BY section_id",
                (extraction_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def reader_seen_spans_for(self, extraction_id: str) -> list[dict[str, Any]]:
        """The passages of one reading recorded as seen (migration 256), oldest first.
        Read only through ``learnloop.reader.seen_passages``."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_seen_spans WHERE extraction_id = ? ORDER BY first_seen_at, span_id",
                (extraction_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def reader_seen_spans_marker(self) -> tuple[int, int]:
        """How many passages are recorded as seen in every reading, and the newest row: it changes whenever one is
        added (the table is append-only). Read only through ``learnloop.reader.seen_passages``."""

        with self.connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS n, COALESCE(MAX(rowid), 0) AS last FROM reader_seen_spans"
                                     ).fetchone()
        return int(row["n"]), int(row["last"])

    def reader_seen_readings(self) -> list[str]:
        """The readings with any passage recorded as seen. Read only through ``learnloop.reader.seen_passages``."""

        with self.connection() as connection:
            rows = connection.execute("SELECT DISTINCT extraction_id FROM reader_seen_spans ORDER BY extraction_id"
                                      ).fetchall()
        return [str(row["extraction_id"]) for row in rows]

    def reader_section_ends_for(self, extraction_id: str) -> list[dict[str, Any]]:
        """The sections of one reading whose last passage was recorded as seen (migration 256).
        Read only through ``learnloop.reader.seen_passages``."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_section_ends WHERE extraction_id = ? ORDER BY section_id",
                (extraction_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def carry_reader_section_progress(
        self, extraction_id: str, rows: Iterable[Mapping[str, Any]], *, clock: Clock | None = None
    ) -> int:
        """Carry section progress onto a new reading of the same book (re-read
        safety, 2026-10-14). Each row names ``section_id``, ``spans_seen``,
        ``span_count``, ``revealed_at``, ``completed_at`` and
        ``generation_batch_id`` (and, for a carried completion, its
        ``completion_cause`` and ``completion_algorithm_version``); the same monotone rules as
        :meth:`upsert_reader_section_progress` apply, and a carried generation
        stamp keeps a section from building its questions twice."""

        now = utc_now_iso(clock)
        rows = list(rows)
        if not rows:
            return 0
        with self.connection() as connection:
            # As in upsert_reader_section_progress: a completion the row already holds is not sent again.
            complete = _completed_sections(connection, extraction_id, [str(row["section_id"]) for row in rows])
            values = []
            for row in rows:
                section_id = str(row["section_id"])
                completed_at = None if section_id in complete else row.get("completed_at")
                values.append((
                    extraction_id, section_id, int(row.get("spans_seen") or 0),
                    int(row.get("span_count") or 0), row.get("revealed_at"), completed_at,
                    row.get("generation_batch_id"), now,
                    row.get("completion_cause") if completed_at else None,
                    row.get("completion_algorithm_version") if completed_at else None,
                ))
            connection.executemany(
                """
                INSERT INTO reader_section_progress(
                  extraction_id, section_id, spans_seen, span_count,
                  revealed_at, completed_at, generation_batch_id, updated_at,
                  completion_cause, completion_algorithm_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(extraction_id, section_id) DO UPDATE SET
                  spans_seen = MAX(reader_section_progress.spans_seen, excluded.spans_seen),
                  span_count = MAX(reader_section_progress.span_count, excluded.span_count),
                  revealed_at = COALESCE(reader_section_progress.revealed_at, excluded.revealed_at),
                  completed_at = COALESCE(reader_section_progress.completed_at, excluded.completed_at),
                  completion_cause = CASE WHEN reader_section_progress.completed_at IS NULL
                    THEN excluded.completion_cause ELSE reader_section_progress.completion_cause END,
                  completion_algorithm_version = CASE WHEN reader_section_progress.completed_at IS NULL
                    THEN excluded.completion_algorithm_version
                    ELSE reader_section_progress.completion_algorithm_version END,
                  generation_batch_id = COALESCE(reader_section_progress.generation_batch_id,
                                                 excluded.generation_batch_id),
                  updated_at = excluded.updated_at
                """,
                values,
            )
            connection.commit()
        return len(values)

    def mark_section_generation(
        self, *, extraction_id: str, section_id: str, batch_id: str, clock: Clock | None = None
    ) -> bool:
        """Stamp the generation batch id exactly once. Returns False when a
        stamp already exists (the trigger's idempotence check)."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE reader_section_progress
                SET generation_batch_id = ?, updated_at = ?
                WHERE extraction_id = ? AND section_id = ? AND generation_batch_id IS NULL
                """,
                (batch_id, utc_now_iso(clock), extraction_id, section_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def swap_section_generation(
        self, *, extraction_id: str, section_id: str, from_batch_id: str, batch_id: str,
        clock: Clock | None = None,
    ) -> bool:
        """Mobile v2 D6: move a section's generation stamp from ``from_batch_id`` to
        ``batch_id``, once: False when the stamp is no longer ``from_batch_id`` (another
        process took it). The deferred stamp's claim, as :meth:`mark_section_generation`
        is the untriggered one's."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE reader_section_progress
                SET generation_batch_id = ?, updated_at = ?
                WHERE extraction_id = ? AND section_id = ? AND generation_batch_id = ?
                """,
                (batch_id, utc_now_iso(clock), extraction_id, section_id, from_batch_id),
            )
            connection.commit()
        return cursor.rowcount > 0

    def deferred_section_generations(self, stamp: str, *, extraction_id: str | None = None) -> list[dict[str, Any]]:
        """The completed sections whose generation stamp is ``stamp`` (one left for the primary by the
        phone host, one waiting for its book's build, ...), oldest first, with when each was finished."""

        sql = ("SELECT extraction_id, section_id, completed_at FROM reader_section_progress "
               "WHERE generation_batch_id = ? AND completed_at IS NOT NULL")
        args: list[Any] = [stamp]
        if extraction_id is not None:
            sql += " AND extraction_id = ?"
            args.append(extraction_id)
        with self.connection() as connection:
            rows = connection.execute(sql + " ORDER BY completed_at, extraction_id, section_id", args).fetchall()
        return [dict(row) for row in rows]

    # --- topic question work (migration 257) ----------------------------------

    def topic_question_work_for(
        self, learning_object_ids: Iterable[str], *, purpose: str = READER_FIRST_SET
    ) -> dict[str, dict[str, Any]]:
        """The claims of these topics (topic work and section jobs' topics alike), by topic."""

        ids = sorted({str(lo) for lo in learning_object_ids})
        if not ids:
            return {}
        marks = ", ".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM reader_topic_question_work WHERE purpose = ? AND learning_object_id IN ({marks})",
                (purpose, *ids),
            ).fetchall()
        return {str(row["learning_object_id"]): _topic_work_row(row) for row in rows}

    def topic_question_work_rows(
        self, *, extraction_id: str | None = None, section_id: str | None = None, source_id: str | None = None,
        batch_id: str | None = None, owner: str | None = None,
    ) -> list[dict[str, Any]]:
        """Claims filtered by origin, batch or owner, in the order they were made."""

        where, args = [], []
        for column, value in (("extraction_id", extraction_id), ("section_id", section_id),
                              ("source_id", source_id), ("batch_id", batch_id), ("owner", owner)):
            if value is not None:
                where.append(f"{column} = ?")
                args.append(value)
        sql = "SELECT * FROM reader_topic_question_work"
        if where:
            sql += " WHERE " + " AND ".join(where)
        with self.connection() as connection:
            rows = connection.execute(sql + " ORDER BY rowid", args).fetchall()
        return [_topic_work_row(row) for row in rows]

    def insert_topic_question_work(self, rows: Sequence[Mapping[str, Any]], *, clock: Clock | None = None) -> None:
        """Claim topics: one row each, owner ``topic``. A topic claimed already makes the whole insert fail
        (the identity is unique), never a second owner."""

        now = utc_now_iso(clock)
        values = [
            (str(row.get("id") or new_ulid()), str(row["learning_object_id"]), str(row.get("purpose") or READER_FIRST_SET),
             row.get("source_id"), row.get("extraction_id"), row.get("section_id"), row["trigger_event"],
             _json(list(row.get("passage_ids") or [])), _json(list(row.get("source_refs") or [])),
             row.get("requested_count"), str(row["work_key"]), str(row["batch_id"]), row.get("job_id"), now, now)
            for row in rows
        ]
        if not values:
            return
        with self.connection() as connection:
            connection.executemany(
                """
                INSERT INTO reader_topic_question_work(
                  id, learning_object_id, purpose, owner, source_id, extraction_id, section_id, trigger_event,
                  passage_ids_json, source_refs_json, requested_count, work_key, batch_id, job_id, state,
                  claimed_at, updated_at
                )
                VALUES (?, ?, ?, 'topic', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)
                """,
                values,
            )
            connection.commit()

    def index_section_job_topics(self, rows: Sequence[Mapping[str, Any]], *, clock: Clock | None = None) -> None:
        """Record topics a section job named before topic work existed as that job's (owner ``section_job``, state
        ``legacy``): a topic nobody owns gains a row; a row the same job already owns has its proposal references
        brought up to date; a topic anyone else owns is left as it is."""

        now = utc_now_iso(clock)
        values = [
            (new_ulid(), str(row["learning_object_id"]), row.get("source_id"), row.get("extraction_id"),
             row.get("section_id"), _json(list(row.get("source_refs") or [])), str(row["batch_id"]), row.get("job_id"),
             _json(list(row.get("proposal_ids") or [])), now, now)
            for row in rows
        ]
        if not values:
            return
        with self.connection() as connection:
            connection.executemany(
                f"""
                INSERT INTO reader_topic_question_work(
                  id, learning_object_id, purpose, owner, source_id, extraction_id, section_id, source_refs_json,
                  batch_id, job_id, proposal_ids_json, state, claimed_at, updated_at
                )
                VALUES (?, ?, '{READER_FIRST_SET}', 'section_job', ?, ?, ?, ?, ?, ?, ?, 'legacy', ?, ?)
                ON CONFLICT(learning_object_id, purpose) DO UPDATE SET
                  proposal_ids_json = excluded.proposal_ids_json,
                  updated_at = excluded.updated_at
                WHERE reader_topic_question_work.owner = 'section_job'
                  AND reader_topic_question_work.batch_id = excluded.batch_id
                  AND reader_topic_question_work.proposal_ids_json <> excluded.proposal_ids_json
                """,
                values,
            )
            connection.commit()

    def update_topic_question_work(
        self, work_id: str, *, state: str | None = None, error: str | None = None, clear_error: bool = False,
        proposal_ids: Sequence[str] | None = None, model_settings: Mapping[str, Any] | None = None,
        requested_count: int | None = None, clock: Clock | None = None,
    ) -> None:
        """Move one topic's work along. ``model_settings`` and ``requested_count`` are kept from the first run
        that names them (the run that froze its request); later runs leave them."""

        sets, args = ["updated_at = ?"], [utc_now_iso(clock)]
        if state is not None:
            sets.append("state = ?")
            args.append(state)
        if error is not None or clear_error:
            sets.append("error = ?")
            args.append(error)
        if proposal_ids is not None:
            sets.append("proposal_ids_json = ?")
            args.append(_json(list(proposal_ids)))
        if model_settings is not None:
            sets.append("model_settings_json = COALESCE(model_settings_json, ?)")
            args.append(_json(dict(model_settings)))
        if requested_count is not None:
            sets.append("requested_count = COALESCE(requested_count, ?)")
            args.append(int(requested_count))
        with self.connection() as connection:
            connection.execute(
                f"UPDATE reader_topic_question_work SET {', '.join(sets)} WHERE id = ? AND owner = 'topic'",
                (*args, work_id),
            )
            connection.commit()

    def reader_authored_questions_for_extraction(
        self, extraction_id: str
    ) -> list[dict[str, Any]]:
        """All authored questions for an extraction, newest first per section."""

        # Section rows only (migration 185): a passage-scoped row never stands
        # in for its section's quick check.
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM reader_authored_questions WHERE extraction_id = ? "
                "AND scope_kind = 'section' "
                "ORDER BY section_id, created_at DESC, id DESC",
                (extraction_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def latest_reader_authored_question(
        self, *, extraction_id: str, section_id: str
    ) -> dict[str, Any] | None:
        """The newest authored question for one section, any status — the
        idempotency anchor: a dismissed row suppresses re-authoring. Section
        rows only (migration 185): an inquiry row carries its anchor's section
        but must never shadow the section's own quick check."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM reader_authored_questions "
                "WHERE extraction_id = ? AND section_id = ? AND scope_kind = 'section' "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (extraction_id, section_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def transition_reader_authored_question(
        self,
        *,
        question_id: str,
        status: str,
        response_md: str | None = None,
        practice_item_id: str | None = None,
        self_check: str | None = None,
        clock: Clock | None = None,
    ) -> bool:
        """Row-status transition (proposed -> answered | dismissed | escalated).
        ``answered`` stamps the response; ``escalated`` pins the minted item;
        ``self_check`` (RW1a) records the learner's own verdict and leaves the
        status and answer time as they are."""

        now = utc_now_iso(clock)
        sets = ["status = ?", "updated_at = ?"]
        params: list[Any] = [status, now]
        if response_md is not None:
            sets.append("response_md = ?")
            params.append(response_md)
        if self_check is not None:
            sets.append("self_check = ?")
            params.append(self_check)
        elif status == "answered":
            sets.append("answered_at = ?")
            params.append(now)
        if practice_item_id is not None:
            sets.append("practice_item_id = ?")
            params.append(practice_item_id)
        params.append(question_id)
        with self.connection() as connection:
            cursor = connection.execute(
                f"UPDATE reader_authored_questions SET {', '.join(sets)} WHERE id = ?",
                tuple(params),
            )
            connection.commit()
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # P3 slice 2: source objects, relations, canonical mapping proposals (§7).
    # ------------------------------------------------------------------

    def create_source_object(self, *, source_id: str, clock: Clock | None = None) -> str:
        object_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_objects(id, source_id, created_at) VALUES (?, ?, ?)",
                (object_id, source_id, utc_now_iso(clock)),
            )
            connection.commit()
        return object_id

    def append_source_object_version(
        self, *, source_object_id: str, version: Mapping[str, Any],
        citations: list[Mapping[str, Any]] | None = None, clock: Clock | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso(clock)
        version_id = new_ulid()
        connection = self.connection()
        try:
            # IMMEDIATE: the next ordinal is read under the write lock.
            connection.execute("BEGIN IMMEDIATE")
            ordinal_row = connection.execute(
                "SELECT COALESCE(MAX(version_ordinal), 0) AS m FROM source_object_versions "
                "WHERE source_object_id = ?",
                (source_object_id,),
            ).fetchone()
            version_ordinal = int(ordinal_row["m"]) + 1
            connection.execute(
                """
                INSERT INTO source_object_versions(
                  id, source_object_id, version_ordinal, revision_id, object_type,
                  authorial_role, salience_proposal, exact_text, content_json,
                  authorship, model_provenance_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id, source_object_id, version_ordinal, version["revision_id"],
                    version["object_type"], version.get("authorial_role"),
                    version.get("salience_proposal"), version.get("exact_text", ""),
                    _json(version.get("content", {})), version.get("authorship", "ai"),
                    _json(version["model_provenance"]) if version.get("model_provenance") is not None else None,
                    version.get("status", "proposed"), now,
                ),
            )
            for i, cite in enumerate(citations or [], start=1):
                connection.execute(
                    "INSERT INTO source_object_citations("
                    "id, source_object_version_id, citation_ordinal, revision_id, span_id, "
                    "block_content_hash, exact_quote, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        new_ulid(), version_id, i, cite.get("revision_id", version["revision_id"]),
                        cite["span_id"], cite.get("block_content_hash"), cite.get("exact_quote"),
                        # A copied citation keeps when it was made: its reading
                        # is read from that (re-read safety, Codex review F3).
                        cite.get("created_at") or now,
                    ),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {"version_id": version_id, "version_ordinal": version_ordinal}

    def source_object_head(self, source_object_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            obj = connection.execute(
                "SELECT * FROM source_objects WHERE id = ?", (source_object_id,)
            ).fetchone()
            if obj is None:
                return None
            version = connection.execute(
                "SELECT * FROM source_object_versions WHERE source_object_id = ? "
                "ORDER BY version_ordinal DESC LIMIT 1",
                (source_object_id,),
            ).fetchone()
            citations: list[dict[str, Any]] = []
            if version is not None:
                citations = [
                    dict(r)
                    for r in connection.execute(
                        "SELECT * FROM source_object_citations WHERE source_object_version_id = ? "
                        "ORDER BY citation_ordinal",
                        (version["id"],),
                    ).fetchall()
                ]
        return {
            "object": dict(obj),
            "version": dict(version) if version is not None else None,
            "citations": citations,
        }

    def source_objects_for_source(self, source_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id FROM source_objects WHERE source_id = ? ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [self.source_object_head(r["id"]) for r in rows]

    def create_source_object_relation(
        self, *, source_object_id: str, related_object_id: str | None, relation_type: str,
        learner_text: str | None = None, authorship: str = "learner",
        review_status: str = "proposed", clock: Clock | None = None, version_ordinal: int = 1,
    ) -> str:
        relation_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO source_object_relations("
                "id, source_object_id, related_object_id, version_ordinal, relation_type, "
                "learner_text, authorship, review_status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    relation_id, source_object_id, related_object_id, int(version_ordinal), relation_type,
                    learner_text, authorship, review_status, utc_now_iso(clock),
                ),
            )
            connection.commit()
        return relation_id

    def source_object_relation(self, relation_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_object_relations WHERE id = ?", (relation_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def create_mapping_proposal(
        self, *, source_object_id: str | None = None, annotation_id: str | None = None,
        target_kind: str, target_ref: str | None = None, confidence: float | None = None,
        rationale: str | None = None, provenance: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> str:
        proposal_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO canonical_mapping_proposals("
                "id, source_object_id, annotation_id, target_kind, target_ref, confidence, "
                "status, rationale, provenance_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?)",
                (
                    proposal_id, source_object_id, annotation_id, target_kind, target_ref,
                    confidence, rationale, _json(provenance or {}), utc_now_iso(clock),
                ),
            )
            connection.commit()
        return proposal_id

    def mapping_proposals(
        self, *, status: str | None = None, source_object_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if source_object_id is not None:
            clauses.append("source_object_id = ?")
            params.append(source_object_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM canonical_mapping_proposals{where} ORDER BY created_at, id",
                tuple(params),
            ).fetchall()
        return [dict(r) for r in rows]

    def decide_mapping_proposal(
        self, *, proposal_id: str, status: str, clock: Clock | None = None
    ) -> dict[str, Any] | None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                "UPDATE canonical_mapping_proposals SET status = ?, decided_at = ? "
                "WHERE id = ? AND status = 'proposed'",
                (status, now, proposal_id),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM canonical_mapping_proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def repoint_mapping_proposal(self, proposal_id: str, *, target_ref: str) -> bool:
        """Point an undecided mapping proposal at another target: a completed
        synthesis request rebound to the capture that still holds it moves its
        commitment mapping to that capture's commitment (Codex verify of RW1b
        fix round 3, F16). A decided proposal is the learner's and never moves."""

        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE canonical_mapping_proposals SET target_ref = ? WHERE id = ? AND status = 'proposed'",
                (target_ref, proposal_id),
            )
            connection.commit()
            return cursor.rowcount > 0

    def set_source_object_status(
        self, *, source_object_id: str, status: str, clock: Clock | None = None
    ) -> dict[str, Any]:
        """Append a status-only successor version carrying the head content forward.

        The head is read and its successor appended in one ``BEGIN IMMEDIATE``
        transaction, so a concurrent proposal version lands wholly before or
        after the review, never between its read and its write (RW4e Codex
        review F1)."""

        with self.atomic():
            return self._set_source_object_status(source_object_id=source_object_id, status=status, clock=clock)

    def _set_source_object_status(
        self, *, source_object_id: str, status: str, clock: Clock | None = None
    ) -> dict[str, Any]:
        head = self.source_object_head(source_object_id)
        if head is None or head["version"] is None:
            raise ValueError(f"unknown source object: {source_object_id!r}")
        prev = head["version"]
        result = self.append_source_object_version(
            source_object_id=source_object_id,
            version={
                "revision_id": prev["revision_id"],
                "object_type": prev["object_type"],
                "authorial_role": prev.get("authorial_role"),
                "salience_proposal": prev.get("salience_proposal"),
                "exact_text": prev.get("exact_text", ""),
                "content": json.loads(prev.get("content_json") or "{}"),
                "authorship": prev.get("authorship", "ai"),
                "status": status,
            },
            citations=[
                {"revision_id": c["revision_id"], "span_id": c["span_id"],
                 "block_content_hash": c.get("block_content_hash"), "exact_quote": c.get("exact_quote"),
                 "created_at": c.get("created_at")}
                for c in head["citations"]
            ],
            clock=clock,
        )
        return {"source_object_id": source_object_id, "status": status, **result}
