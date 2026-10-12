"""SQL for PF-b candidates, solution skeletons and item fingerprints (migration 169).

``pf_candidates`` and ``item_skeletons`` are WORKFLOW: pipeline state and paid
outputs that a rebuild never clears or regenerates. ``item_fingerprints`` is
DERIVED and replaced wholesale by its single replayer. Verdicts never live here;
they are appended to ``judgment_ledger``.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping

_CANDIDATE_COLUMNS = (
    "id", "run_id", "mint_request_id", "round", "tier", "family_id", "parent_item_id",
    "learning_object_id", "generation_path", "declared_relation", "final_relation",
    "proposer_model", "prompt_version", "payload_json", "content_hash", "verification",
    "verification_check", "status", "rejection_filter", "filters_json", "difficulty",
    "difficulty_source", "panel_json", "selection_json", "cost_json", "published_item_id",
    "published_at", "created_at", "updated_at",
)
_UPDATABLE = frozenset(_CANDIDATE_COLUMNS) - {"id", "created_at", "run_id"}


def insert_candidate(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Insert once; a resumed run that regenerates the same id keeps the first row."""
    values = {column: row.get(column) for column in _CANDIDATE_COLUMNS}
    for column, default in (("filters_json", "{}"), ("cost_json", "{}"), ("verification", "unverified")):
        if values[column] is None:
            values[column] = default
    # Only an existing id is tolerated; every CHECK still fails loudly.
    cursor = connection.execute(
        f"INSERT INTO pf_candidates ({','.join(_CANDIDATE_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in _CANDIDATE_COLUMNS)}) ON CONFLICT(id) DO NOTHING",
        tuple(values[column] for column in _CANDIDATE_COLUMNS),
    )
    return cursor.rowcount > 0


def update_candidate(connection: sqlite3.Connection, candidate_id: str, **fields: Any) -> None:
    unknown = set(fields) - _UPDATABLE
    if unknown:
        raise ValueError(f"Not updatable pf_candidates columns: {sorted(unknown)}")
    if not fields:
        return
    assignments = ",".join(f"{column}=?" for column in fields)
    connection.execute(
        f"UPDATE pf_candidates SET {assignments} WHERE id=?",
        (*fields.values(), candidate_id),
    )


def candidate(connection: sqlite3.Connection, candidate_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM pf_candidates WHERE id=?", (candidate_id,)).fetchone()
    return dict(row) if row is not None else None


def candidates(connection: sqlite3.Connection, *, where: str = "1=1",
               params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(
        f"SELECT * FROM pf_candidates WHERE {where} ORDER BY created_at, id", tuple(params),
    )]


def published_count_between(connection: sqlite3.Connection, start_iso: str, end_iso: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) FROM pf_candidates WHERE status='published' "
        "AND published_at >= ? AND published_at < ?",
        (start_iso, end_iso),
    ).fetchone()
    return int(row[0])


def insert_skeleton(connection: sqlite3.Connection, *, skeleton_id: str, content_hash: str,
                    subject_kind: str, subject_id: str, model_id: str, prompt_version: str,
                    techniques: list[str], operations: list[str], checkpoints: list[str],
                    skeleton_text: str, created_at: str) -> None:
    connection.execute(
        "INSERT INTO item_skeletons (id,content_hash,subject_kind,subject_id,model_id,"
        "prompt_version,techniques_json,operations_json,checkpoints_json,skeleton_text,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
        (skeleton_id, content_hash, subject_kind, subject_id, model_id, prompt_version,
         json.dumps(techniques), json.dumps(operations), json.dumps(checkpoints),
         skeleton_text, created_at),
    )


def skeletons_for_hashes(connection: sqlite3.Connection,
                         content_hashes: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
    """Every persisted skeleton per content hash, in a stable order."""
    hashes = sorted(set(content_hashes))
    result: dict[str, list[dict[str, Any]]] = {}
    for start in range(0, len(hashes), 500):
        chunk = hashes[start:start + 500]
        for row in connection.execute(
            f"SELECT * FROM item_skeletons WHERE content_hash IN ({','.join('?' for _ in chunk)}) "
            "ORDER BY content_hash, prompt_version, model_id, id",
            chunk,
        ):
            record = dict(row)
            for key in ("techniques_json", "operations_json", "checkpoints_json"):
                record[key.removesuffix("_json")] = json.loads(record[key])
            result.setdefault(record["content_hash"], []).append(record)
    return result


def replace_item_fingerprints(connection: sqlite3.Connection,
                              rows: Iterable[Mapping[str, Any]]) -> tuple[int, int]:
    """DERIVED replacement: clear, then insert the deterministic rows."""
    cleared = connection.execute("DELETE FROM item_fingerprints").rowcount
    written = 0
    for row in rows:
        connection.execute(
            "INSERT INTO item_fingerprints (practice_item_id,namespace,component,value_hash,"
            "item_content_hash,fingerprint_version) VALUES (?,?,?,?,?,?)",
            (row["practice_item_id"], row["namespace"], row["component"], row["value_hash"],
             row["item_content_hash"], row["fingerprint_version"]),
        )
        written += 1
    return cleared, written


def item_fingerprints(connection: sqlite3.Connection,
                      item_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    if item_ids is None:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM item_fingerprints ORDER BY practice_item_id, namespace, component"
        )]
    ids = sorted(set(item_ids))
    result: list[dict[str, Any]] = []
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        result.extend(dict(row) for row in connection.execute(
            f"SELECT * FROM item_fingerprints WHERE practice_item_id IN ({','.join('?' for _ in chunk)}) "
            "ORDER BY practice_item_id, namespace, component",
            chunk,
        ))
    return result
