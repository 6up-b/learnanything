"""Source documents, extraction runs and entity links.

Owns source artifacts, revisions, document blocks, units and assets, extraction
runs, inventories, selections, source conflicts and entity links."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.row_serialization import _json, _loads
from learnloop.db.stores.held_out_signals import is_exam_role, qualify_unrecorded_signals
from learnloop.ids import new_ulid
from learnloop.ingest.ir import DocumentAsset, DocumentBlock, DocumentIR, DocumentUnit
from learnloop.ingest.locators import detect_locator_scheme


def _decode_source_conflict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["resolution"] = _loads(data.pop("resolution_json", None), None)
    return data


def _decode_extraction_run(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["model_versions"] = _loads(payload.pop("model_versions_json", None), {})
    payload["config"] = _loads(payload.pop("config_json", None), {})
    payload["page_selection"] = _loads(payload.pop("page_selection_json", None), None)
    payload["health"] = _loads(payload.pop("health_json", None), {})
    return payload


def _decode_unit_selection(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["selected_unit_ids"] = _loads(payload.pop("selected_unit_ids_json", None), [])
    payload["boundary_overrides"] = _loads(payload.pop("boundary_overrides_json", None), [])
    payload["needs_review"] = _loads(payload.pop("needs_review_json", None), [])
    payload["exam_use_modes"] = _loads(payload.pop("exam_use_modes_json", None), {})
    payload["exam_paper_metadata"] = _loads(payload.pop("exam_paper_metadata_json", None), {})
    return payload


def _decode_unit_inventory(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["inventory"] = _loads(payload.pop("inventory_json", None), {})
    payload["usage"] = _loads(payload.pop("usage_json", None), {})
    return payload


def _decode_exam_profile(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["profile"] = _loads(payload.pop("profile_json", None), {})
    return payload


def _decode_document_block(row: sqlite3.Row) -> DocumentBlock:
    return DocumentBlock(
        span_id=row["span_id"],
        extractor_block_id=row["extractor_block_id"],
        block_type=row["block_type"],
        role_hint=row["role_hint"],
        page=row["page"],
        bbox=_loads(row["bbox_json"], None),
        polygon=_loads(row["polygon_json"], None),
        section_path=_loads(row["section_path_json"], []),
        text=row["text"],
        content_hash=row["content_hash"],
        asset_ids=_loads(row["asset_ids_json"], []),
        ordinal=row["ordinal"],
    )


def _decode_document_unit(row: sqlite3.Row) -> DocumentUnit:
    return DocumentUnit(
        unit_id=row["unit_id"],
        parent_unit_id=row["parent_unit_id"],
        label=row["label"],
        ordinal=row["ordinal"],
        locator=_loads(row["locator_json"], {}),
        semantic_hash=row["semantic_hash"],
        page_start=row["page_start"],
        page_end=row["page_end"],
        span_ids=_loads(row["span_ids_json"], []),
    )


def _decode_document_asset(row: sqlite3.Row) -> DocumentAsset:
    return DocumentAsset(
        id=row["id"],
        media_type=row["media_type"],
        content_hash=row["content_hash"],
        path=row["path"],
        caption=row["caption"],
        page=row["page"],
        geometry=_loads(row["geometry_json"], None),
        neighboring_span_ids=_loads(row["neighboring_span_ids_json"], []),
    )


class SourceDocumentStoreMixin:

    def search_source_blocks(
        self, *, query: str, extraction_ids: Sequence[str], limit: int = 80
    ) -> list[dict[str, Any]]:
        """Case-insensitive substring search over document blocks of the given
        extractions (no FTS index exists; ``instr`` over ``text`` is adequate at
        local-vault scale). Ordered by extraction then document order."""

        needle = (query or "").strip().lower()
        ids = tuple(dict.fromkeys(extraction_id for extraction_id in extraction_ids if extraction_id))
        if not needle or not ids:
            return []
        marks = ", ".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT extraction_id, span_id, text, section_path_json, ordinal, page "
                f"FROM source_document_blocks WHERE extraction_id IN ({marks}) "
                "AND block_type NOT IN ('PageHeader', 'PageFooter', 'TableOfContents') "
                "AND instr(lower(text), ?) > 0 "
                "ORDER BY extraction_id, ordinal LIMIT ?",
                (*ids, needle, int(limit)),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------ #
    # Source layer v2 (spec_source_ingestion_v2 §2 / migration 032).
    # ------------------------------------------------------------------ #

    def upsert_source_artifact(
        self,
        *,
        id: str,
        acquisition_kind: str,
        canonical_uri: str | None = None,
        work_id: str | None = None,
        current_revision_id: str | None = None,
        display_title: str | None = None,
        reader_enabled: bool | None = None,
        clock: Clock | None = None,
    ) -> None:
        # ``reader_enabled=None`` means "no opinion": new rows default ON, and a
        # re-import that omits the flag never clobbers an explicit earlier choice.
        reader_flag = None if reader_enabled is None else int(reader_enabled)
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_artifacts(
                  id, acquisition_kind, canonical_uri, work_id,
                  current_revision_id, display_title, reader_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, COALESCE(?, 1), ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  acquisition_kind = excluded.acquisition_kind,
                  canonical_uri = excluded.canonical_uri,
                  work_id = excluded.work_id,
                  current_revision_id = COALESCE(excluded.current_revision_id, source_artifacts.current_revision_id),
                  display_title = COALESCE(excluded.display_title, source_artifacts.display_title),
                  reader_enabled = COALESCE(?, source_artifacts.reader_enabled),
                  updated_at = excluded.updated_at
                """,
                (
                    id, acquisition_kind, canonical_uri, work_id, current_revision_id,
                    display_title, reader_flag, now, now, reader_flag,
                ),
            )
            connection.commit()

    def set_source_reader_enabled(
        self, source_id: str, enabled: bool, *, clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE source_artifacts SET reader_enabled = ?, updated_at = ? WHERE id = ?",
                (int(enabled), utc_now_iso(clock), source_id),
            )
            connection.commit()

    def sources_with_retired_keep_local(self) -> list[str]:
        """Books that still carry the retired "Keep this book on this
        computer" (``source_artifacts.keep_local``, migration 198; retired by
        the owner 2026-10-13): nothing consults the column now (generic
        ``SELECT *`` reads still fetch it), ``learnloop doctor`` names them."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id FROM source_artifacts WHERE keep_local != 0 ORDER BY id"
            ).fetchall()
        return [str(row["id"]) for row in rows]

    def get_source_artifact(self, source_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_artifacts WHERE id = ?", (source_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def source_artifact_by_uri(self, acquisition_kind: str, canonical_uri: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_artifacts WHERE acquisition_kind = ? AND canonical_uri = ?",
                (acquisition_kind, canonical_uri),
            ).fetchone()
        return dict(row) if row is not None else None

    def set_source_current_revision(
        self, source_id: str, revision_id: str, *, clock: Clock | None = None
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE source_artifacts SET current_revision_id = ?, updated_at = ? WHERE id = ?",
                (revision_id, utc_now_iso(clock), source_id),
            )
            connection.commit()

    def insert_source_revision(
        self,
        *,
        id: str,
        source_id: str,
        asset_hash: str,
        note_id: str | None = None,
        original_uri: str | None = None,
        retrieved_at: str | None = None,
        supersedes_revision_id: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_revisions(
                  id, source_id, asset_hash, note_id, original_uri,
                  retrieved_at, supersedes_revision_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id,
                    source_id,
                    asset_hash,
                    note_id,
                    original_uri,
                    retrieved_at,
                    supersedes_revision_id,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def get_source_revision(self, revision_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_revisions WHERE id = ?", (revision_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def source_revision_by_asset_hash(self, source_id: str, asset_hash: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_revisions WHERE source_id = ? AND asset_hash = ?",
                (source_id, asset_hash),
            ).fetchone()
        return dict(row) if row is not None else None

    def source_revisions_for(self, source_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_revisions WHERE source_id = ? ORDER BY created_at, id",
                (source_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def all_source_artifacts(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_artifacts ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def extraction_runs_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_extraction_runs WHERE revision_id = ? ORDER BY created_at, id",
                (revision_id,),
            ).fetchall()
        return [_decode_extraction_run(row) for row in rows]

    def document_ir_counts(self, extraction_id: str) -> dict[str, int]:
        with self.connection() as connection:
            units = connection.execute(
                "SELECT COUNT(*) AS n FROM source_document_units WHERE extraction_id = ?",
                (extraction_id,),
            ).fetchone()["n"]
            blocks = connection.execute(
                "SELECT COUNT(*) AS n FROM source_document_blocks WHERE extraction_id = ?",
                (extraction_id,),
            ).fetchone()["n"]
        return {"unit_count": units, "block_count": blocks}

    def insert_extraction_run(
        self,
        *,
        id: str,
        revision_id: str,
        extractor: str,
        extractor_version: str,
        extraction_request_hash: str,
        ir_schema_version: str,
        model_versions: Mapping[str, str] | None = None,
        config: Mapping[str, Any] | None = None,
        page_selection: Iterable[int] | None = None,
        parent_extraction_id: str | None = None,
        status: str = "queued",
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_extraction_runs(
                  id, revision_id, parent_extraction_id, extractor, extractor_version,
                  model_versions_json, config_json, page_selection_json, ir_schema_version,
                  extraction_request_hash, extraction_result_hash, status,
                  created_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL)
                """,
                (
                    id,
                    revision_id,
                    parent_extraction_id,
                    extractor,
                    extractor_version,
                    _json(dict(sorted((model_versions or {}).items()))),
                    _json(dict(config or {})),
                    _json(sorted(page_selection) if page_selection is not None else None),
                    ir_schema_version,
                    extraction_request_hash,
                    status,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def get_extraction_run(self, extraction_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_extraction_runs WHERE id = ?", (extraction_id,)
            ).fetchone()
        return _decode_extraction_run(row) if row is not None else None

    def extraction_run_by_request_hash(
        self, revision_id: str, extraction_request_hash: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_extraction_runs WHERE revision_id = ? AND extraction_request_hash = ?",
                (revision_id, extraction_request_hash),
            ).fetchone()
        return _decode_extraction_run(row) if row is not None else None

    def complete_extraction_run(
        self,
        extraction_id: str,
        *,
        extraction_result_hash: str,
        status: str = "completed",
        health: Mapping[str, Any] | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE source_extraction_runs
                   SET extraction_result_hash = ?, status = ?,
                       health_json = COALESCE(?, health_json), completed_at = ?
                 WHERE id = ?
                """,
                (
                    extraction_result_hash,
                    status,
                    _json(dict(health)) if health is not None else None,
                    utc_now_iso(clock),
                    extraction_id,
                ),
            )
            connection.commit()

    def persist_document_ir(self, extraction_id: str, ir: DocumentIR) -> None:
        with self.connection() as connection:
            # A worker may stop after persisting some/all IR but before marking
            # the run complete. Replacing the run-local children makes that
            # retry converge instead of colliding on primary keys or retaining
            # stale blocks from the interrupted output.
            connection.execute(
                "DELETE FROM source_document_assets WHERE extraction_id = ?",
                (extraction_id,),
            )
            connection.execute(
                "DELETE FROM source_document_blocks WHERE extraction_id = ?",
                (extraction_id,),
            )
            connection.execute(
                "DELETE FROM source_document_units WHERE extraction_id = ?",
                (extraction_id,),
            )
            connection.execute(
                "UPDATE source_extraction_runs SET health_json = ? WHERE id = ?",
                (_json(ir.health.model_dump(mode="json")), extraction_id),
            )
            for unit in ir.units:
                connection.execute(
                    """
                    INSERT INTO source_document_units(
                      extraction_id, unit_id, parent_unit_id, label, ordinal,
                      locator_json, semantic_hash, page_start, page_end, span_ids_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        extraction_id,
                        unit.unit_id,
                        unit.parent_unit_id,
                        unit.label,
                        unit.ordinal,
                        _json(unit.locator),
                        unit.semantic_hash,
                        unit.page_start,
                        unit.page_end,
                        _json(unit.span_ids),
                    ),
                )
            for block in ir.blocks:
                connection.execute(
                    """
                    INSERT INTO source_document_blocks(
                      extraction_id, span_id, extractor_block_id, block_type, role_hint,
                      page, bbox_json, polygon_json, section_path_json, text,
                      content_hash, asset_ids_json, ordinal
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        extraction_id,
                        block.span_id,
                        block.extractor_block_id,
                        block.block_type,
                        block.role_hint,
                        block.page,
                        _json(block.bbox),
                        _json(block.polygon),
                        _json(block.section_path),
                        block.text,
                        block.content_hash,
                        _json(block.asset_ids),
                        block.ordinal,
                    ),
                )
            for asset in ir.assets:
                connection.execute(
                    """
                    INSERT INTO source_document_assets(
                      id, extraction_id, media_type, content_hash, path,
                      caption, page, geometry_json, neighboring_span_ids_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.id,
                        extraction_id,
                        asset.media_type,
                        asset.content_hash,
                        asset.path,
                        asset.caption,
                        asset.page,
                        _json(asset.geometry),
                        _json(asset.neighboring_span_ids),
                    ),
                )
            connection.commit()

    def block_content_hashes(self, extraction_id: str) -> dict[str, str]:
        """``{span_id: content_hash}`` of a reading's blocks in reading order,
        without loading its IR (the Reader asks on every annotation refresh)."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT span_id, content_hash FROM source_document_blocks WHERE extraction_id = ? ORDER BY ordinal",
                (extraction_id,),
            ).fetchall()
        return {str(row["span_id"]): str(row["content_hash"]) for row in rows}

    def document_blocks(self, extraction_id: str, span_ids: Sequence[str]) -> list[DocumentBlock]:
        """The named blocks of one extraction in reading order (ordinal), without
        loading its IR; ids it lacks are left out (Reader CA1, the problem as printed)."""

        wanted = list(dict.fromkeys(str(span) for span in span_ids))
        if not wanted:
            return []
        marks = ",".join("?" for _ in wanted)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM source_document_blocks WHERE extraction_id = ? AND span_id IN ({marks}) "
                "ORDER BY ordinal",
                (extraction_id, *wanted),
            ).fetchall()
        return [_decode_document_block(row) for row in rows]

    def document_blocks_on_pages(self, extraction_id: str, pages: Sequence[int]) -> list[DocumentBlock]:
        """Every block of one extraction on the given pages, in reading order."""

        wanted = sorted({int(page) for page in pages})
        if not wanted:
            return []
        marks = ",".join("?" for _ in wanted)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM source_document_blocks WHERE extraction_id = ? AND page IN ({marks}) "
                "ORDER BY ordinal",
                (extraction_id, *wanted),
            ).fetchall()
        return [_decode_document_block(row) for row in rows]

    def load_document_ir(self, extraction_id: str) -> DocumentIR | None:
        run = self.get_extraction_run(extraction_id)
        if run is None:
            return None
        with self.connection() as connection:
            unit_rows = connection.execute(
                "SELECT * FROM source_document_units WHERE extraction_id = ? ORDER BY ordinal",
                (extraction_id,),
            ).fetchall()
            block_rows = connection.execute(
                "SELECT * FROM source_document_blocks WHERE extraction_id = ? ORDER BY ordinal",
                (extraction_id,),
            ).fetchall()
            asset_rows = connection.execute(
                "SELECT * FROM source_document_assets WHERE extraction_id = ? ORDER BY id",
                (extraction_id,),
            ).fetchall()
        from learnloop.ingest.ir import ExtractionHealth

        return DocumentIR(
            ir_schema_version=run["ir_schema_version"],
            extractor=run["extractor"],
            extractor_version=run["extractor_version"],
            blocks=[_decode_document_block(row) for row in block_rows],
            units=[_decode_document_unit(row) for row in unit_rows],
            assets=[_decode_document_asset(row) for row in asset_rows],
            health=ExtractionHealth.model_validate(run.get("health") or {}),
        )

    def insert_span_reanchor(
        self,
        *,
        from_extraction_id: str,
        from_span_id: str,
        to_extraction_id: str,
        to_span_id: str,
        match_kind: str,
        confidence: float | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_span_reanchors(
                  from_extraction_id, from_span_id, to_extraction_id, to_span_id,
                  match_kind, confidence, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    from_extraction_id,
                    from_span_id,
                    to_extraction_id,
                    to_span_id,
                    match_kind,
                    confidence,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def span_reanchors_from(self, from_extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_span_reanchors WHERE from_extraction_id = ? ORDER BY from_span_id",
                (from_extraction_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_span_reanchors(
        self,
        from_extraction_id: str,
        to_extraction_id: str,
        aliases: Iterable[tuple[str, str, str, float | None]],
        *,
        clock: Clock | None = None,
    ) -> int:
        """Persist one re-read's span aliases ``(from span, to span, match
        kind, confidence)`` in one transaction. Idempotent on the primary key:
        an alias already recorded is kept as it was (re-read safety, 2026-10-14)."""

        now = utc_now_iso(clock)
        rows = [
            (from_extraction_id, str(from_span), to_extraction_id, str(to_span), str(kind), confidence, now)
            for from_span, to_span, kind, confidence in aliases
        ]
        if not rows:
            return 0
        with self.connection() as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO source_span_reanchors(
                  from_extraction_id, from_span_id, to_extraction_id, to_span_id,
                  match_kind, confidence, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            connection.commit()
            return connection.total_changes - before

    def span_reanchors_between(self, from_extraction_id: str, to_extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_span_reanchors WHERE from_extraction_id = ? AND to_extraction_id = ? "
                "ORDER BY from_span_id",
                (from_extraction_id, to_extraction_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def span_reanchor_origins(self, to_extraction_id: str) -> list[str]:
        """The readings with recorded aliases into ``to_extraction_id``, the
        most recently recorded first."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT from_extraction_id, MAX(created_at) AS at FROM source_span_reanchors "
                "WHERE to_extraction_id = ? GROUP BY from_extraction_id ORDER BY at DESC, from_extraction_id DESC",
                (to_extraction_id,),
            ).fetchall()
        return [str(row["from_extraction_id"]) for row in rows]

    def backfill_locator_schemes(
        self, locators: Iterable[str], *, clock: Clock | None = None
    ) -> dict[str, str]:
        """Shape-detect and stamp a declared scheme onto each existing ref."""

        now = utc_now_iso(clock)
        stamped: dict[str, str] = {}
        with self.connection() as connection:
            for locator in locators:
                existing = connection.execute(
                    "SELECT scheme FROM source_locator_schemes WHERE locator = ?",
                    (locator,),
                ).fetchone()
                if existing is not None:
                    stamped[locator] = existing["scheme"]
                    continue
                scheme = detect_locator_scheme(locator)
                if scheme is None:
                    continue
                connection.execute(
                    "INSERT INTO source_locator_schemes"
                    "(locator, scheme, detected_at) VALUES (?, ?, ?)",
                    (locator, scheme, now),
                )
                stamped[locator] = scheme
            connection.commit()
        return stamped

    def locator_scheme(self, locator: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT scheme FROM source_locator_schemes WHERE locator = ?",
                (locator,),
            ).fetchone()
        if row is not None:
            return row["scheme"]
        return detect_locator_scheme(locator)

    # ------------------------------------------------------------------
    # Unit selections (spec_source_ingestion_v2 §5.3, migration 040)
    # ------------------------------------------------------------------

    def upsert_unit_selection(
        self,
        *,
        extraction_id: str,
        source_id: str | None,
        revision_id: str | None,
        selected_unit_ids: list[str],
        boundary_overrides: list[dict] | None = None,
        needs_review: list[str] | None = None,
        exam_use_modes: Mapping[str, str] | None = None,
        exam_paper_metadata: Mapping[str, Any] | None = None,
        role_override: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            previous = connection.execute(
                "SELECT s.role_override, COALESCE(s.source_id, revision.source_id) FROM source_unit_selections AS s "
                "LEFT JOIN source_extraction_runs AS run ON run.id = s.extraction_id "
                "LEFT JOIN source_revisions AS revision ON revision.id = run.revision_id WHERE s.extraction_id = ?",
                (extraction_id,),
            ).fetchone()
            if previous is not None and is_exam_role(previous[0]) and not is_exam_role(role_override):
                # An outline exam pick changed: the book's held-out signals
                # whose role was not recorded are recorded as exam material
                # first, so the change never releases them (exam protection
                # by extraction identity, Codex review F3).
                qualify_unrecorded_signals(connection, [previous[1], source_id], created_at=now)
            connection.execute(
                """
                INSERT INTO source_unit_selections(
                  extraction_id, source_id, revision_id, selected_unit_ids_json,
                  boundary_overrides_json, needs_review_json,
                  exam_use_modes_json, exam_paper_metadata_json, role_override,
                  created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(extraction_id) DO UPDATE SET
                  source_id = excluded.source_id,
                  revision_id = excluded.revision_id,
                  selected_unit_ids_json = excluded.selected_unit_ids_json,
                  boundary_overrides_json = excluded.boundary_overrides_json,
                  needs_review_json = excluded.needs_review_json,
                  exam_use_modes_json = excluded.exam_use_modes_json,
                  exam_paper_metadata_json = excluded.exam_paper_metadata_json,
                  role_override = excluded.role_override,
                  updated_at = excluded.updated_at
                """,
                (
                    extraction_id,
                    source_id,
                    revision_id,
                    _json(list(selected_unit_ids)),
                    _json(list(boundary_overrides or [])),
                    _json(list(needs_review or [])),
                    _json(dict(exam_use_modes or {})),
                    _json(dict(exam_paper_metadata or {})),
                    role_override,
                    now,
                    now,
                ),
            )
            connection.commit()

    def get_unit_selection(self, extraction_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_unit_selections WHERE extraction_id = ?", (extraction_id,)
            ).fetchone()
        return _decode_unit_selection(row) if row is not None else None

    # ------------------------------------------------------------------
    # Role-specific unit inventories (spec_source_ingestion_v2 §7)
    # ------------------------------------------------------------------

    def insert_unit_inventory(
        self,
        *,
        id: str,
        source_revision_id: str,
        extraction_id: str,
        unit_id: str,
        unit_semantic_hash: str,
        inventory_profile: str,
        inventory_schema_version: int,
        prompt_version: str,
        provider: str,
        model: str,
        inventory: Mapping[str, Any],
        usage: Mapping[str, Any] | None = None,
        made_as_role: str | None = None,
        reused_from_inventory_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Write one cached inventory (§7) and, for a model run on
        ``extraction_id`` (not a reuse), its held-out signals into the
        append-only ``source_held_out_signal_marks`` ledger, in one
        transaction (exam protection by extraction identity).

        The cache row is keyed per revision, so a reuse for another reading
        of the revision rebinds it there; exam protection never reads that
        binding. ``reused_from_inventory_id`` names the inventory a reuse
        re-anchored (recorded in ``usage`` as ``rebound_from_inventory_id``,
        as before): a reuse writes no ledger row, so it never marks the
        reading it is bound to, and the origin's ledger row stays.
        ``made_as_role`` is the role the model run was made under.

        Returns the id of the row now holding the key: ``id``, or the existing
        row's when the key was already there (the update keeps that row's id), so
        every reference to the inventory names a row that exists."""

        now = utc_now_iso(clock)
        usage_row = dict(usage or {})
        if reused_from_inventory_id:
            usage_row.setdefault("rebound_from_inventory_id", reused_from_inventory_id)
        reused = bool(reused_from_inventory_id or usage_row.get("rebound_from_inventory_id"))
        held_out_spans = sorted({
            str(span)
            for signal in (dict(inventory).get("assessment_signals") or [])
            if isinstance(signal, Mapping) and signal.get("held_out")
            for span in (signal.get("span_ids") or [])
            if span
        })
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_unit_inventories(
                  id, source_revision_id, extraction_id, unit_id, unit_semantic_hash,
                  inventory_profile, inventory_schema_version, prompt_version,
                  provider, model, inventory_json, usage_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_revision_id, unit_id, unit_semantic_hash,
                            inventory_profile, inventory_schema_version,
                            prompt_version, provider, model)
                  DO UPDATE SET
                    inventory_json = excluded.inventory_json,
                    usage_json = excluded.usage_json,
                    extraction_id = excluded.extraction_id
                """,
                (
                    id,
                    source_revision_id,
                    extraction_id,
                    unit_id,
                    unit_semantic_hash,
                    inventory_profile,
                    inventory_schema_version,
                    prompt_version,
                    provider,
                    model,
                    _json(dict(inventory)),
                    _json(usage_row),
                    now,
                ),
            )
            stored_id = connection.execute(
                """
                SELECT id FROM source_unit_inventories
                WHERE source_revision_id = ? AND unit_id = ? AND unit_semantic_hash = ?
                  AND inventory_profile = ? AND inventory_schema_version = ?
                  AND prompt_version = ? AND provider = ? AND model = ?
                """,
                (source_revision_id, unit_id, unit_semantic_hash, inventory_profile,
                 inventory_schema_version, prompt_version, provider, model),
            ).fetchone()["id"]
            if held_out_spans and not reused:
                spans_json = _json(held_out_spans)
                digest = hashlib.sha256(
                    _json([source_revision_id, extraction_id, unit_id, made_as_role, held_out_spans]).encode()
                ).hexdigest()[:32]
                connection.execute(
                    "INSERT OR IGNORE INTO source_held_out_signal_marks(id, revision_id, extraction_id, unit_id, "
                    "inventory_id, made_as_role, span_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (f"hos_{digest}", source_revision_id, extraction_id, unit_id, stored_id, made_as_role, spans_json, now),
                )
            connection.commit()
        return str(stored_id)

    def held_out_signal_marks(self) -> list[dict[str, Any]]:
        """Every row of the held-out signal ledger (exam protection by
        extraction identity), with its book's source id, oldest first."""

        with self.connection() as connection:
            rows = connection.execute(
                "SELECT m.*, r.source_id AS source_id FROM source_held_out_signal_marks AS m "
                "LEFT JOIN source_revisions AS r ON r.id = m.revision_id ORDER BY m.created_at, m.id"
            ).fetchall()
        return [{**dict(row), "span_ids": _loads(row["span_ids_json"], [])} for row in rows]

    def reusable_unit_inventories(
        self,
        *,
        source_revision_id: str,
        unit_id: str,
        unit_semantic_hash: str,
        inventory_schema_version: int,
        prompt_version: str,
        provider: str,
        model: str,
        request_key: str,
    ) -> list[dict[str, Any]]:
        """Cached rows sharing the non-profile semantic identity (§7).

        A row that records the request it was paid under (``usage.request_key``)
        matches only that request, whatever its prompt label, provider or model
        column says; a row from before matches those columns, so it is not
        orphaned.

        ``source_revision_id`` is a binding preference, not part of the reusable
        artifact identity.  An unchanged normalized unit may move to a new source
        revision; the inventory service deterministically re-anchors its cited
        spans and writes a binding row for the new revision before returning the
        hit.  Same-revision rows sort first so the common path remains a direct
        lookup.
        """

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_unit_inventories
                 WHERE unit_id = ? AND unit_semantic_hash = ?
                   AND inventory_schema_version = ?
                   AND CASE WHEN json_extract(usage_json, '$.request_key') IS NULL
                            THEN prompt_version = ? AND provider = ? AND model = ?
                            ELSE json_extract(usage_json, '$.request_key') = ? END
                 ORDER BY CASE WHEN source_revision_id = ? THEN 0 ELSE 1 END,
                          created_at
                """,
                (
                    unit_id,
                    unit_semantic_hash,
                    inventory_schema_version,
                    prompt_version,
                    provider,
                    model,
                    request_key,
                    source_revision_id,
                ),
            ).fetchall()
        return [_decode_unit_inventory(row) for row in rows]

    def get_unit_inventory(self, inventory_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_unit_inventories WHERE id = ?", (inventory_id,)
            ).fetchone()
        return _decode_unit_inventory(row) if row is not None else None

    def unit_inventories_for_extraction(self, extraction_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_unit_inventories WHERE extraction_id = ? ORDER BY unit_id, created_at",
                (extraction_id,),
            ).fetchall()
        return [_decode_unit_inventory(row) for row in rows]

    def unit_inventories_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_unit_inventories WHERE source_revision_id = ? ORDER BY unit_id, created_at",
                (revision_id,),
            ).fetchall()
        return [_decode_unit_inventory(row) for row in rows]

    def source_unit_inventory_claims(self) -> list[dict[str, Any]]:
        """Facet-candidate harvesting seam (knowledge-model §3.3).

        Flattens every inventory row's claims/concept mentions into
        {text, unit_id, refs} candidates. Candidates only — never canonical."""

        candidates: list[dict[str, Any]] = []
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT id, unit_id, inventory_json FROM source_unit_inventories ORDER BY unit_id, id"
            ).fetchall()
        for row in rows:
            inventory = _loads(row["inventory_json"], {})
            unit_id = row["unit_id"]
            for claim in inventory.get("claims", []):
                statement = (claim.get("statement") or "").strip()
                if statement:
                    candidates.append(
                        {"text": statement, "unit_id": unit_id, "refs": [row["id"], claim.get("claim_id", "")]}
                    )
            for mention in inventory.get("concept_mentions", []):
                name = (mention.get("name") or "").strip()
                if name:
                    candidates.append(
                        {"text": name, "unit_id": unit_id, "refs": [row["id"], mention.get("mention_id", "")]}
                    )
        return candidates

    # ------------------------------------------------------------------
    # Contested legacy state.  Keep these APIs attached until owner-vault
    # telemetry has proved the tables empty (S6.1a must precede S6.1c).
    # ------------------------------------------------------------------

    def upsert_exam_profile(
        self,
        *,
        id: str,
        scope_kind: str,
        scope_id: str,
        profile_hash: str,
        profile: Mapping[str, Any],
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_exam_profiles(
                  id, scope_kind, scope_id, profile_hash, profile_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scope_kind, scope_id, profile_hash) DO UPDATE SET
                  profile_json = excluded.profile_json
                """,
                (id, scope_kind, scope_id, profile_hash, _json(dict(profile)), now),
            )
            connection.commit()

    def get_exam_profile(
        self, scope_kind: str, scope_id: str
    ) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM source_exam_profiles
                 WHERE scope_kind = ? AND scope_id = ?
                 ORDER BY created_at DESC LIMIT 1
                """,
                (scope_kind, scope_id),
            ).fetchone()
        return _decode_exam_profile(row) if row is not None else None

    # ------------------------------------------------------------------
    # --- ING M5: provenance, manifests, write-ahead apply intents -----------

    def insert_entity_source_link(
        self,
        *,
        entity_type: str,
        entity_id: str,
        locator: str,
        relation: str,
        source_id: str | None = None,
        revision_id: str | None = None,
        locator_scheme: str | None = None,
        extraction_id: str | None = None,
        asset_hash: str | None = None,
        span_hash: str | None = None,
        patch_id: str | None = None,
        status: str = "current",
        link_id: str | None = None,
        created_at: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Insert an entity_source_links row (§9.1). Idempotent on the UNIQUE key
        ``(entity_type, entity_id, revision_id, locator, relation)`` so recovery /
        re-application never duplicates provenance.
        """

        row_id = link_id or new_ulid()
        now = created_at or utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO entity_source_links(
                  id, entity_type, entity_id, source_id, revision_id,
                  locator, locator_scheme, relation, extraction_id, asset_hash,
                  span_hash, patch_id, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    entity_type,
                    entity_id,
                    source_id,
                    revision_id,
                    locator,
                    locator_scheme,
                    relation,
                    extraction_id,
                    asset_hash,
                    span_hash,
                    patch_id,
                    status,
                    now,
                ),
            )
            connection.commit()
        return row_id

    def entity_source_links(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM entity_source_links
                 WHERE entity_type = ? AND entity_id = ?
                 ORDER BY created_at, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def entity_source_links_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM entity_source_links WHERE revision_id = ? ORDER BY id",
                (revision_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_notation_mapping(
        self,
        *,
        entity_type: str,
        entity_id: str,
        canonical_notation: str,
        alternate_notation: str,
        subject_id: str | None = None,
        context: str | None = None,
        source_id: str | None = None,
        revision_id: str | None = None,
        locator: str | None = None,
        patch_id: str | None = None,
        status: str = "active",
        mapping_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = mapping_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO notation_mappings(
                  id, subject_id, entity_type, entity_id, canonical_notation,
                  alternate_notation, context, source_id, revision_id, locator,
                  patch_id, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    subject_id,
                    entity_type,
                    entity_id,
                    canonical_notation,
                    alternate_notation,
                    context,
                    source_id,
                    revision_id,
                    locator,
                    patch_id,
                    status,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()
        return row_id

    def notation_mappings_for_entity(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM notation_mappings
                 WHERE entity_type = ? AND entity_id = ?
                 ORDER BY created_at, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_source_conflict(
        self,
        *,
        entity_type: str,
        entity_id: str,
        statement: str,
        subject_id: str | None = None,
        left_source_id: str | None = None,
        left_revision_id: str | None = None,
        left_locator: str | None = None,
        right_source_id: str | None = None,
        right_revision_id: str | None = None,
        right_locator: str | None = None,
        status: str = "open",
        resolution: Any = None,
        patch_id: str | None = None,
        conflict_id: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        row_id = conflict_id or new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_conflicts(
                  id, subject_id, entity_type, entity_id,
                  left_source_id, left_revision_id, left_locator,
                  right_source_id, right_revision_id, right_locator,
                  statement, status, resolution_json, patch_id, created_at, resolved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    subject_id,
                    entity_type,
                    entity_id,
                    left_source_id,
                    left_revision_id,
                    left_locator,
                    right_source_id,
                    right_revision_id,
                    right_locator,
                    statement,
                    status,
                    _json(resolution) if resolution is not None else None,
                    patch_id,
                    utc_now_iso(clock),
                    None,
                ),
            )
            connection.commit()
        return row_id

    def source_conflicts_for_entity(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_conflicts
                 WHERE entity_type = ? AND entity_id = ?
                 ORDER BY created_at, id
                """,
                (entity_type, entity_id),
            ).fetchall()
        return [_decode_source_conflict(row) for row in rows]

    def entity_source_links_for_sources(
        self, source_ids: list[str]
    ) -> list[dict[str, Any]]:
        """All entity_source_links whose ``source_id`` is in ``source_ids``.

        Used by append affected-neighborhood selection (§10.1 source scope): every
        entity the appended source already touches is a high-signal neighbor."""

        if not source_ids:
            return []
        placeholders = ",".join("?" for _ in source_ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM entity_source_links WHERE source_id IN ({placeholders}) ORDER BY id",
                tuple(source_ids),
            ).fetchall()
        return [dict(row) for row in rows]

    def stale_entity_source_links(
        self, statuses: tuple[str, ...] = ("stale", "needs_reanchor")
    ) -> list[dict[str, Any]]:
        """Links whose spans went stale / need re-anchoring (§10.4 revision refresh)."""

        placeholders = ",".join("?" for _ in statuses)
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM entity_source_links WHERE status IN ({placeholders}) ORDER BY id",
                statuses,
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_entity_source_link_status(
        self,
        link_id: str,
        *,
        status: str,
        superseded_by_link_id: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE entity_source_links
                   SET status = ?, stale_at = ?, superseded_by_link_id = ?
                 WHERE id = ?
                """,
                (
                    status,
                    utc_now_iso(clock) if status in {"stale", "removed", "needs_reanchor"} else None,
                    superseded_by_link_id,
                    link_id,
                ),
            )
            connection.commit()

    def all_notation_mappings(self, status: str | None = "active") -> list[dict[str, Any]]:
        query = "SELECT * FROM notation_mappings"
        params: tuple[Any, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def source_conflict(self, conflict_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_conflicts WHERE id = ?", (conflict_id,)
            ).fetchone()
        return _decode_source_conflict(row) if row else None

    def source_conflicts_by_status(self, status: str = "open") -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM source_conflicts WHERE status = ? ORDER BY created_at, id",
                (status,),
            ).fetchall()
        return [_decode_source_conflict(row) for row in rows]

    def resolve_source_conflict(
        self,
        conflict_id: str,
        *,
        status: str,
        resolution: Any,
        resolution_kind: str,
        actor: str | None = None,
        rationale: str | None = None,
        clock: Clock | None = None,
    ) -> str:
        """Persist a conflict resolution + an immutable audit row (§10.2).

        The conflict row's status/resolution advance; ``source_conflict_resolutions``
        preserves every decision so audit history is never overwritten. Both
        evidence locators stay on the conflict row untouched."""

        now = utc_now_iso(clock)
        audit_id = new_ulid()
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE source_conflicts
                   SET status = ?, resolution_json = ?, resolved_at = ?
                 WHERE id = ?
                """,
                (status, _json(resolution), now if status in {"resolved", "dismissed"} else None, conflict_id),
            )
            connection.execute(
                """
                INSERT INTO source_conflict_resolutions(
                  id, conflict_id, resolution_kind, resolution_json, actor, rationale, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (audit_id, conflict_id, resolution_kind, _json(resolution), actor, rationale, now),
            )
            connection.commit()
        return audit_id

    def source_conflict_resolutions(self, conflict_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_conflict_resolutions
                 WHERE conflict_id = ? ORDER BY created_at, id
                """,
                (conflict_id,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            data = dict(row)
            data["resolution"] = _loads(data.pop("resolution_json", None), None)
            out.append(data)
        return out
