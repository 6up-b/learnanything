"""SQL for the practice index (Slice 2 §5.9): paid outputs and receipts only.

Callers own transactions and pass a connection, as with ``embedding_vectors``.
Nothing here is evidence; nothing here is derived; rebuild clears none of it.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
import json
import sqlite3
from typing import Any


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,),
    ).fetchone() is not None


# -- facet dossiers -------------------------------------------------------


@dataclass(frozen=True)
class DossierRow:
    id: str
    facet_id: str
    facet_content_hash: str
    source_hash: str
    model_id: str
    prompt_version: str
    scope: str
    moves: str
    errors: str
    contrast: str
    created_at: str

    def field(self, name: str) -> str:
        return {"scope": self.scope, "moves": self.moves,
                "errors": self.errors, "contrast": self.contrast}[name]


_DOSSIER_COLUMNS = (
    "id", "facet_id", "facet_content_hash", "source_hash", "model_id",
    "prompt_version", "scope", "moves", "errors", "contrast", "created_at",
)


def dossier_exists(connection: sqlite3.Connection, *, facet_id: str, facet_content_hash: str,
                   source_hash: str, model_id: str, prompt_version: str) -> bool:
    if not table_exists(connection, "facet_dossiers"):
        return False
    return connection.execute(
        "SELECT 1 FROM facet_dossiers WHERE facet_id=? AND facet_content_hash=? "
        "AND source_hash=? AND model_id=? AND prompt_version=?",
        (facet_id, facet_content_hash, source_hash, model_id, prompt_version),
    ).fetchone() is not None


def insert_dossier(connection: sqlite3.Connection, *, id: str, facet_id: str,
                   facet_content_hash: str, source_hash: str, model_id: str,
                   prompt_version: str, scope: str, moves: str, errors: str,
                   contrast: str, draft: Mapping[str, Any], grounding: Mapping[str, Any],
                   input_hash: str, provider: str | None, billing: str, run_id: str,
                   created_at: str) -> bool:
    """Insert once per key, preserving the first paid result. Returns inserted."""
    cursor = connection.execute(
        "INSERT INTO facet_dossiers (id,facet_id,facet_content_hash,source_hash,model_id,"
        "prompt_version,scope,moves,errors,contrast,draft_json,grounding_json,input_hash,"
        "provider,billing,run_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(facet_id,facet_content_hash,source_hash,model_id,prompt_version) DO NOTHING",
        (id, facet_id, facet_content_hash, source_hash, model_id, prompt_version, scope,
         moves, errors, contrast, json.dumps(draft, sort_keys=True, ensure_ascii=False),
         json.dumps(grounding, sort_keys=True, ensure_ascii=False), input_hash, provider,
         billing, run_id, created_at),
    )
    return cursor.rowcount == 1


def dossier_candidates(connection: sqlite3.Connection,
                       facet_hashes: Mapping[str, str]) -> dict[str, list[DossierRow]]:
    """Every dossier written for each facet's CURRENT content, oldest first.

    A dossier of an older facet revision is never a candidate. Choosing among
    the candidates (by source hash, model and prompt version) is the caller's
    policy: ``practice_index.dossiers.select_dossier``.
    """
    if not facet_hashes or not table_exists(connection, "facet_dossiers"):
        return {}
    rows = connection.execute(
        f"SELECT {','.join(_DOSSIER_COLUMNS)} FROM facet_dossiers ORDER BY created_at, id"
    ).fetchall()
    found: dict[str, list[DossierRow]] = {}
    for row in rows:
        values = DossierRow(*(row[index] for index in range(len(_DOSSIER_COLUMNS))))
        if facet_hashes.get(values.facet_id) == values.facet_content_hash:
            found.setdefault(values.facet_id, []).append(values)
    return found


def dossier_count(connection: sqlite3.Connection) -> int:
    if not table_exists(connection, "facet_dossiers"):
        return 0
    return int(connection.execute("SELECT COUNT(*) FROM facet_dossiers").fetchone()[0])


# -- find_practice proposals ----------------------------------------------


def insert_proposal(connection: sqlite3.Connection, *, id: str, created_at: str, origin: str,
                    query_id: str, query_text: str, constraints: Mapping[str, Any],
                    path: str, path_reason: str, signals: Mapping[str, Any],
                    reranked: bool, rerank_status: str, rerank_model: str | None,
                    proposed: list[Mapping[str, Any]], exclusions: Mapping[str, Any],
                    manifest: Mapping[str, Any], algorithm_version: str,
                    caller: str | None = None, caller_ref: str | None = None,
                    intent: str | None = None,
                    valuation: Mapping[str, Any] | None = None,
                    provisional: Mapping[str, Any] | None = None) -> None:
    """One receipt per call. The canonical-sources columns (migrations 187 and
    190) are written only when given, so a caller that names none writes the
    row Phase 5b wrote."""
    columns = ["id", "created_at", "origin", "query_id", "query_text", "constraints_json",
               "path", "path_reason", "signals_json", "reranked", "rerank_status",
               "rerank_model", "proposed_json", "exclusions_json", "manifest_json",
               "algorithm_version"]
    values: list[Any] = [
        id, created_at, origin, query_id, query_text,
        json.dumps(constraints, sort_keys=True), path, path_reason,
        json.dumps(signals, sort_keys=True), int(reranked), rerank_status, rerank_model,
        json.dumps(list(proposed), sort_keys=True, ensure_ascii=False),
        json.dumps(exclusions, sort_keys=True), json.dumps(manifest, sort_keys=True),
        algorithm_version,
    ]
    extra = {"caller": caller, "caller_ref": caller_ref, "intent": intent,
             "valuation_json": None if valuation is None else json.dumps(valuation, sort_keys=True,
                                                                          ensure_ascii=False),
             "provisional_json": None if provisional is None else json.dumps(
                 provisional, sort_keys=True, ensure_ascii=False)}
    for name, value in extra.items():
        if value is not None:
            columns.append(name)
            values.append(value)
    connection.execute(
        f"INSERT INTO practice_index_proposals ({','.join(columns)}) "
        f"VALUES ({','.join('?' for _ in columns)})",
        tuple(values),
    )


def _proposal(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    for key in ("constraints_json", "signals_json", "proposed_json",
                "exclusions_json", "manifest_json"):
        value[key[:-5]] = json.loads(value.pop(key))
    for key in ("valuation_json", "provisional_json"):
        if key in value:
            raw = value.pop(key)
            value[key[:-5]] = json.loads(raw) if raw else None
    value["reranked"] = bool(value["reranked"])
    return value


def proposal(connection: sqlite3.Connection, proposal_id: str) -> dict[str, Any] | None:
    if not table_exists(connection, "practice_index_proposals"):
        return None
    row = connection.execute(
        "SELECT * FROM practice_index_proposals WHERE id=?", (proposal_id,),
    ).fetchone()
    return None if row is None else _proposal(row)


def proposals(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not table_exists(connection, "practice_index_proposals"):
        return []
    return [_proposal(row) for row in connection.execute(
        "SELECT * FROM practice_index_proposals ORDER BY created_at, id"
    )]


# -- the retrieval evaluation ---------------------------------------------


def eval_queries(connection: sqlite3.Connection,
                 prompt_versions: Collection[str]) -> list[dict[str, Any]]:
    if not table_exists(connection, "practice_eval_queries") or not prompt_versions:
        return []
    marks = ",".join("?" for _ in prompt_versions)
    return [dict(row) for row in connection.execute(
        f"SELECT * FROM practice_eval_queries WHERE prompt_version IN ({marks}) "
        "ORDER BY seed_kind, seed_id, id",
        tuple(prompt_versions),
    )]


def insert_eval_query(connection: sqlite3.Connection, *, id: str, query_text: str,
                      seed_kind: str, seed_id: str, model_id: str | None,
                      prompt_version: str, input_hash: str, run_id: str | None,
                      created_at: str) -> bool:
    cursor = connection.execute(
        "INSERT INTO practice_eval_queries (id,query_text,seed_kind,seed_id,model_id,"
        "prompt_version,input_hash,run_id,created_at) VALUES (?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT DO NOTHING",
        (id, query_text, seed_kind, seed_id, model_id, prompt_version, input_hash,
         run_id, created_at),
    )
    return cursor.rowcount == 1


def insert_evaluation(connection: sqlite3.Connection, *, id: str, created_at: str,
                      winner: str, reason: str, manifest_hash: str,
                      manifest: Mapping[str, Any], metrics: Mapping[str, Any],
                      run_id: str) -> None:
    connection.execute(
        "INSERT INTO practice_index_evaluations (id,created_at,winner,reason,manifest_hash,"
        "manifest_json,metrics_json,run_id) VALUES (?,?,?,?,?,?,?,?)",
        (id, created_at, winner, reason, manifest_hash,
         json.dumps(manifest, sort_keys=True), json.dumps(metrics, sort_keys=True), run_id),
    )


def latest_evaluation(connection: sqlite3.Connection,
                      manifest_hash: str | None = None) -> dict[str, Any] | None:
    """The newest evaluation, optionally only one made on this manifest."""
    if not table_exists(connection, "practice_index_evaluations"):
        return None
    where, parameters = ("WHERE manifest_hash=? ", (manifest_hash,)) if manifest_hash else ("", ())
    row = connection.execute(
        f"SELECT * FROM practice_index_evaluations {where}ORDER BY created_at DESC, id DESC LIMIT 1",
        parameters,
    ).fetchone()
    if row is None:
        return None
    value = dict(row)
    value["manifest"] = json.loads(value.pop("manifest_json"))
    value["metrics"] = json.loads(value.pop("metrics_json"))
    return value


# -- checkpointed paid answers (model_work_checkpoints) -------------------


def checkpointed_keys(connection: sqlite3.Connection, keys: Collection[str]) -> set[str]:
    """Which of these request identities already have a checkpointed answer."""
    if not keys or not table_exists(connection, "model_work_checkpoints"):
        return set()
    found: set[str] = set()
    ordered = sorted(set(keys))
    for start in range(0, len(ordered), 500):
        chunk = ordered[start:start + 500]
        marks = ",".join("?" for _ in chunk)
        found |= {str(row[0]) for row in connection.execute(
            f"SELECT cache_key FROM model_work_checkpoints WHERE cache_key IN ({marks})", tuple(chunk),
        )}
    return found


def checkpoints_for_purpose(connection: sqlite3.Connection, *, prefix: str,
                            purpose: str) -> list[dict[str, Any]]:
    """Checkpointed answers of one paid role, oldest first (crash recovery)."""
    if not table_exists(connection, "model_work_checkpoints"):
        return []
    return [{"cache_key": str(row[0]), "result": json.loads(row[1])} for row in connection.execute(
        "SELECT cache_key, result_json FROM model_work_checkpoints "
        "WHERE purpose=? AND substr(cache_key, 1, ?)=? ORDER BY created_at, cache_key",
        (purpose, len(prefix), prefix),
    )]


def completed_root_receipts(connection: sqlite3.Connection, *, purpose: str,
                            prompt_hash: str | None = None) -> list[dict[str, Any]]:
    """Completed root receipts of one paid role that kept their answer, newest first.

    A receipt's finish commits before the caller checkpoints the answer, so a
    failed checkpoint write leaves the paid answer only here (crash recovery).
    ``resolved_model`` falls back to the newest child receipt that reported one.
    """
    if not table_exists(connection, "model_call_receipts"):
        return []
    where, parameters = "", [purpose]
    if prompt_hash is not None:
        where, parameters = " AND r.prompt_hash=?", [purpose, prompt_hash]
    rows = connection.execute(
        "SELECT r.id, r.prompt_hash, r.schema_hash, r.output_budget_tokens, r.budget_json, "
        "r.output_text, COALESCE(r.resolved_model, (SELECT c.resolved_model FROM "
        "model_call_receipts c WHERE c.parent_call_id=r.id AND c.resolved_model IS NOT NULL "
        "ORDER BY c.started_at DESC, c.id DESC LIMIT 1)) AS resolved_model "
        "FROM model_call_receipts r WHERE r.purpose=? AND r.parent_call_id IS NULL "
        "AND r.status='completed' AND r.output_text IS NOT NULL" + where
        + " ORDER BY r.started_at DESC, r.id DESC",
        tuple(parameters),
    ).fetchall()
    found = []
    for row in rows:
        try:
            declared = json.loads(row[4] or "{}").get("practice_index") or {}
        except (TypeError, ValueError, AttributeError):
            declared = {}
        found.append({"id": str(row[0]), "prompt_hash": row[1], "schema_hash": row[2],
                      "output_budget_tokens": row[3], "declared": declared,
                      "output_text": row[5], "resolved_model": row[6]})
    return found


# -- judgment_ledger reads for this index ---------------------------------


def judgments_by_ids(connection: sqlite3.Connection,
                     ids: Collection[str]) -> dict[str, dict[str, Any]]:
    if not ids or not table_exists(connection, "judgment_ledger"):
        return {}
    found: dict[str, dict[str, Any]] = {}
    ordered = sorted(ids)
    for start in range(0, len(ordered), 500):
        chunk = ordered[start:start + 500]
        marks = ",".join("?" for _ in chunk)
        for row in connection.execute(
            f"SELECT * FROM judgment_ledger WHERE id IN ({marks})", tuple(chunk),
        ):
            found[str(row["id"])] = dict(row)
    return found


def judgments_for_task(connection: sqlite3.Connection, task: str) -> list[dict[str, Any]]:
    if not table_exists(connection, "judgment_ledger"):
        return []
    return [dict(row) for row in connection.execute(
        "SELECT * FROM judgment_ledger WHERE task=? ORDER BY created_at, id", (task,),
    )]


def attempts_after(connection: sqlite3.Connection, *, practice_item_ids: Collection[str],
                   since: str, until: str) -> list[dict[str, Any]]:
    """Attempts on these items in [since, until], oldest first (usage join)."""
    if not practice_item_ids:
        return []
    marks = ",".join("?" for _ in practice_item_ids)
    return [dict(row) for row in connection.execute(
        f"SELECT id, practice_item_id, created_at FROM practice_attempts "
        f"WHERE practice_item_id IN ({marks}) AND created_at >= ? AND created_at <= ? "
        "ORDER BY created_at, id",
        (*sorted(practice_item_ids), since, until),
    )]


def items_revealed_between(connection: sqlite3.Connection, *, since: str,
                           until: str) -> set[str]:
    """Items whose answer the reveal ledger recorded in (since, until]; a
    routine full-answer display by its coverage instead: from the renewal
    grace before ``since``, and also when stamped after ``until`` (the clock
    went back), ``learnloop.reveal_coverage`` (UX Phase 4 round 4)."""
    if not table_exists(connection, "reveal_events"):
        return set()
    from learnloop.reveal_coverage import routine_coverage_sql, routine_window_start

    routine, routine_parameters = routine_coverage_sql(routine_window_start(since))
    return {str(row[0]) for row in connection.execute(
        "SELECT DISTINCT practice_item_id FROM reveal_events "
        f"WHERE (created_at > ? AND created_at <= ?) OR {routine}",
        (since, until, *routine_parameters),
    )}


def stored_vector_hashes(connection: sqlite3.Connection, *, record_kind: str, field: str,
                         model_id: str, task_prefix: str) -> dict[str, set[str]]:
    """Content hashes stored per record for one recipe view (completeness checks)."""
    if not table_exists(connection, "embedding_vectors"):
        return {}
    stored: dict[str, set[str]] = {}
    for row in connection.execute(
        "SELECT record_id, content_hash FROM embedding_vectors "
        "WHERE record_kind=? AND field=? AND model_id=? AND task_prefix=?",
        (record_kind, field, model_id, task_prefix),
    ):
        stored.setdefault(str(row[0]), set()).add(str(row[1]))
    return stored
