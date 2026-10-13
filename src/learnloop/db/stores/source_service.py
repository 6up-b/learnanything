"""SQL for the canonical-sources service (spec_source_practice_and_probes_v1).

Callers own transactions and pass a connection, as with ``practice_index``.
``db`` sits below every domain, so the attempt transaction, the tutor and the
remediation path can record and read here without importing the service
(SC12). Nothing here is evidence; the one DERIVED table (S5's outcome join)
is cleared and rebuilt only by its replayer.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import json
import sqlite3
from typing import Any

import hashlib


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,),
    ).fetchone() is not None


def column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    if not table_exists(connection, table):
        return False
    return any(row[1] == column for row in connection.execute(f'PRAGMA table_info("{table}")'))


def _plain(value: Any) -> Any:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return {str(key): _plain(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_plain(inner) for inner in value]
    return value


def reference_content_hash(item: Any) -> str:
    """What an answer-key check verified: the prompt, the expected answer and
    the grading rubric (canonical sources S1, §7.3a).

    A check verifies one revision of an item, not its id: ``edit_item``
    rewrites these in place under the same id. Hints are not part of the key,
    so a hints-only edit keeps a verification. ``vault.hashes`` re-exports this
    one definition (``db`` sits below ``vault`` and must not import it).
    """

    fields = {"prompt": item.prompt, "expected_answer": item.expected_answer,
              "grading_rubric": item.grading_rubric}
    payload = json.dumps(_plain(fields), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _loads(raw: Any, default: Any = None) -> Any:
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


# -- S0: impressions (migration 184) ----------------------------------------


IMPRESSION_SURFACES = ("tutor_strip", "plan", "dl3_box", "reader", "other")


def insert_impression(connection: sqlite3.Connection, *, id: str, created_at: str, surface: str,
                      caller_kind: str | None, caller_ref: str | None, proposal_id: str,
                      candidate_kind: str, practice_item_id: str | None,
                      extraction_id: str | None, span_ids: Sequence[str],
                      shown_fields: Mapping[str, Any], session_id: str | None) -> None:
    connection.execute(
        "INSERT INTO instructional_impressions (id,created_at,surface,caller_kind,caller_ref,"
        "proposal_id,candidate_kind,practice_item_id,extraction_id,span_ids_json,"
        "shown_fields_json,session_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (id, created_at, surface, caller_kind, caller_ref, proposal_id, candidate_kind,
         practice_item_id, extraction_id, _dumps(list(span_ids)), _dumps(dict(shown_fields)),
         session_id),
    )


def _impression(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value["span_ids"] = _loads(value.pop("span_ids_json"), [])
    value["shown_fields"] = _loads(value.pop("shown_fields_json"), {})
    return value


def impressions_for_proposal(connection: sqlite3.Connection, proposal_id: str) -> list[dict[str, Any]]:
    if not table_exists(connection, "instructional_impressions"):
        return []
    return [_impression(row) for row in connection.execute(
        "SELECT * FROM instructional_impressions WHERE proposal_id=? ORDER BY created_at, id",
        (proposal_id,),
    )]


def impressions_of_item(connection: sqlite3.Connection, practice_item_id: str, *,
                        since: str | None = None) -> list[dict[str, Any]]:
    if not table_exists(connection, "instructional_impressions"):
        return []
    sql = "SELECT * FROM instructional_impressions WHERE practice_item_id=?"
    params: list[Any] = [practice_item_id]
    if since is not None:
        sql += " AND created_at >= ?"
        params.append(since)
    return [_impression(row) for row in connection.execute(sql + " ORDER BY created_at, id", params)]


def impressions_of_spans(connection: sqlite3.Connection, extraction_id: str,
                         span_ids: Iterable[str], *, since: str | None = None) -> list[dict[str, Any]]:
    """Impressions of a source exercise whose shown spans overlap ``span_ids``."""

    if not table_exists(connection, "instructional_impressions"):
        return []
    wanted = set(span_ids)
    sql = "SELECT * FROM instructional_impressions WHERE extraction_id=?"
    params: list[Any] = [extraction_id]
    if since is not None:
        sql += " AND created_at >= ?"
        params.append(since)
    rows = [_impression(row) for row in connection.execute(sql + " ORDER BY created_at, id", params)]
    return [row for row in rows if wanted & set(row["span_ids"])]


# -- S1: source-exercise imports and answer-key checks (migration 185) -------


#: Key statuses a finished check can record.
CHECK_STATUSES = ("book_solution", "checked", "panel_agrees", "panel_agrees_unconfirmed",
                  "model_answer", "disputed")
#: The statuses that verify a key (PF §5.3): only these certify (C3) and only
#: these qualify an item for the value intents and S2b.
VERIFIED_STATUSES = frozenset({"book_solution", "checked", "panel_agrees"})
#: How the effective status reads to a learner (honest labels, SC5).
KEY_STATUS_LABELS = {
    "book_solution": "Answer from the book's solution",
    "checked": "Checked: independent solvers and a symbolic check agree",
    "panel_agrees": "Independent model solvers agree",
    "panel_agrees_unconfirmed": "Independent model solvers agree; the symbolic check couldn't run here",
    "checking": "Being checked",
    "model_answer": "Model's answer, not checked",
    "disputed": "LearnLoop's check disagrees with this answer key",
    "changed_since_check": "Answer key changed since it was checked",
    "not_applicable": "",
}
READER_IMPORT_MECHANISM = "reader_exercise_import"


def insert_import(connection: sqlite3.Connection, *, id: str, created_at: str, caller: str,
                  extraction_id: str, span_ids: Sequence[str], status: str,
                  proposal_id: str | None = None, source_id: str | None = None,
                  revision_id: str | None = None, label: str | None = None,
                  practice_item_id: str | None = None, content_hash: str | None = None,
                  key_status: str | None = None, verification: Mapping[str, Any] | None = None,
                  validation: Mapping[str, Any] | None = None, facet_basis: str | None = None,
                  family_proposal_id: str | None = None, reason: str | None = None,
                  need_id: str | None = None) -> None:
    columns = ["id", "proposal_id", "extraction_id", "span_ids_json", "source_id", "revision_id", "label",
               "practice_item_id", "content_hash", "key_status", "verification_json", "validation_json",
               "facet_basis", "family_proposal_id", "status", "reason", "caller", "created_at", "updated_at"]
    values: list[Any] = [id, proposal_id, extraction_id, _dumps(list(span_ids)), source_id, revision_id, label,
                         practice_item_id, content_hash, key_status, _dumps(dict(verification or {})),
                         _dumps(dict(validation or {})), facet_basis, family_proposal_id, status, reason, caller,
                         created_at, created_at]
    if need_id is not None:
        columns.append("need_id")
        values.append(need_id)
    connection.execute(
        f"INSERT INTO source_exercise_imports ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
        tuple(values),
    )


_IMPORT_FIELDS = {
    "practice_item_id", "content_hash", "key_status", "verification", "validation", "facet_basis",
    "family_proposal_id", "status", "reason", "label", "need_id",
}


def update_import(connection: sqlite3.Connection, import_id: str, *, updated_at: str, **fields: Any) -> None:
    unknown = set(fields) - _IMPORT_FIELDS
    if unknown:
        raise ValueError(f"unknown import fields: {', '.join(sorted(unknown))}")
    sets, values = ["updated_at=?"], [updated_at]
    for name, value in fields.items():
        if name in ("verification", "validation"):
            sets.append(f"{name}_json=?")
            values.append(_dumps(dict(value or {})))
        else:
            sets.append(f"{name}=?")
            values.append(value)
    values.append(import_id)
    connection.execute(f"UPDATE source_exercise_imports SET {', '.join(sets)} WHERE id=?", tuple(values))


def _import(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value["span_ids"] = _loads(value.pop("span_ids_json"), [])
    value["verification"] = _loads(value.pop("verification_json"), {})
    value["validation"] = _loads(value.pop("validation_json"), {})
    return value


def import_row(connection: sqlite3.Connection, import_id: str) -> dict[str, Any] | None:
    if not table_exists(connection, "source_exercise_imports"):
        return None
    row = connection.execute("SELECT * FROM source_exercise_imports WHERE id=?", (import_id,)).fetchone()
    return None if row is None else _import(row)


def imports_for_item(connection: sqlite3.Connection, practice_item_id: str) -> list[dict[str, Any]]:
    if not table_exists(connection, "source_exercise_imports"):
        return []
    return [_import(row) for row in connection.execute(
        "SELECT * FROM source_exercise_imports WHERE practice_item_id=? ORDER BY created_at, id",
        (practice_item_id,))]


def imports(connection: sqlite3.Connection, *, status: str | None = None) -> list[dict[str, Any]]:
    if not table_exists(connection, "source_exercise_imports"):
        return []
    sql, params = "SELECT * FROM source_exercise_imports", []
    if status is not None:
        sql += " WHERE status=?"
        params.append(status)
    return [_import(row) for row in connection.execute(sql + " ORDER BY created_at, id", params)]


def imported_regions(connection: sqlite3.Connection) -> list[tuple[str, list[str]]]:
    """Every written import's (extraction, spans)."""

    if not table_exists(connection, "source_exercise_imports"):
        return []
    return [(str(row["extraction_id"]), _loads(row["span_ids_json"], []))
            for row in connection.execute(
                "SELECT extraction_id, span_ids_json FROM source_exercise_imports WHERE status='written'")]


def insert_key_check(connection: sqlite3.Connection, *, id: str, practice_item_id: str,
                     content_hash: str, key_status: str, rung: str, trigger: str, started_at: str,
                     created_at: str, import_id: str | None = None,
                     verification: Mapping[str, Any] | None = None,
                     ledger_ids: Sequence[str] = ()) -> None:
    if key_status not in CHECK_STATUSES:
        raise ValueError(f"key_status must be one of {', '.join(CHECK_STATUSES)}")
    connection.execute(
        "INSERT INTO reference_key_checks (id,practice_item_id,import_id,content_hash,key_status,rung,"
        "verification_json,ledger_ids_json,trigger,started_at,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (id, practice_item_id, import_id, content_hash, key_status, rung,
         _dumps(dict(verification or {})), _dumps(list(ledger_ids)), trigger, started_at, created_at),
    )


def _check(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    value["verification"] = _loads(value.pop("verification_json"), {})
    value["ledger_ids"] = _loads(value.pop("ledger_ids_json"), [])
    return value


def key_checks_for_item(connection: sqlite3.Connection, practice_item_id: str) -> list[dict[str, Any]]:
    if not table_exists(connection, "reference_key_checks"):
        return []
    return [_check(row) for row in connection.execute(
        "SELECT * FROM reference_key_checks WHERE practice_item_id=? ORDER BY created_at, rowid",
        (practice_item_id,))]


def is_reader_import(connection: sqlite3.Connection, practice_item_id: str) -> bool:
    """A historical Reader import, from its append-only ``learner_item_authored`` event.

    ``canonical_extract`` provenance alone does not identify an exercise
    import: AI authoring proposals over canonical sources share that origin.
    """

    if not table_exists(connection, "interaction_events"):
        return False
    for row in connection.execute(
        "SELECT payload_json FROM interaction_events WHERE kind='learner_item_authored' "
        "AND subject_type='practice_item' AND subject_id=?", (practice_item_id,),
    ):
        payload = _loads(row[0], {}) or {}
        if payload.get("mechanism") == READER_IMPORT_MECHANISM:
            return True
    return False


def is_exercise_import(connection: sqlite3.Connection, item: Any) -> bool:
    if getattr(item, "canonical_exercise", None) is not None:
        return True
    if imports_for_item(connection, item.id):
        return True
    return is_reader_import(connection, item.id)


def effective_key_status(connection: sqlite3.Connection, item: Any) -> str:
    """The item's key status now: the latest check of its CURRENT content.

    ``not_applicable`` for an item that is not an exercise import; else the
    latest check whose ``content_hash`` matches the item as it is, or
    ``changed_since_check`` (a check exists for another revision), ``checking``
    (an import still running its ladder) or ``model_answer``.
    """

    if not is_exercise_import(connection, item):
        return "not_applicable"
    current = reference_content_hash(item)
    checks = key_checks_for_item(connection, item.id)
    matching = [check for check in checks if check["content_hash"] == current]
    if matching:
        return str(matching[-1]["key_status"])
    if checks:
        return "changed_since_check"
    rows = imports_for_item(connection, item.id)
    if rows and rows[-1].get("key_status") == "checking" and rows[-1].get("content_hash") == current:
        return "checking"
    return "model_answer"


def exercise_import_ids(connection: sqlite3.Connection, items: Iterable[Any]) -> set[str]:
    """Every exercise import among ``items``, read in three bulk queries."""

    ids = {item.id for item in items if getattr(item, "canonical_exercise", None) is not None}
    if table_exists(connection, "source_exercise_imports"):
        ids |= {str(row[0]) for row in connection.execute(
            "SELECT DISTINCT practice_item_id FROM source_exercise_imports WHERE practice_item_id IS NOT NULL")}
    if table_exists(connection, "interaction_events"):
        for row in connection.execute(
            "SELECT subject_id, payload_json FROM interaction_events WHERE kind='learner_item_authored' "
            "AND subject_type='practice_item'"
        ):
            if (_loads(row[1], {}) or {}).get("mechanism") == READER_IMPORT_MECHANISM:
                ids.add(str(row[0]))
    return ids


def unverified_import_ids(connection: sqlite3.Connection, items: Iterable[Any], *, gated: bool) -> set[str]:
    """Exercise imports whose CURRENT key is not verified (C3, §7.3a).

    Certification cold probes and exam pools leave them out, as DL3 keeps
    unverified captures out. ``gated`` is whether the vault is at or above the
    gate's tag; below it nothing is excluded."""

    if not gated:
        return set()
    items = list(items)
    candidates = exercise_import_ids(connection, items)
    return {item.id for item in items
            if item.id in candidates and reference_status_for_item(connection, item) == "unverified"}


def reference_status_for_item(connection: sqlite3.Connection, item: Any) -> str:
    """The attempt-time gate's value: ``not_applicable``, ``verified`` or ``unverified``."""

    status = effective_key_status(connection, item)
    if status == "not_applicable":
        return "not_applicable"
    return "verified" if status in VERIFIED_STATUSES else "unverified"


# -- S3: comparisons (migration 186) -------------------------------------------


def insert_comparison(connection: sqlite3.Connection, *, id: str, created_at: str, query_hash: str, query_md: str,
                      requested_perspectives: Sequence[str], counterpart_keys: Sequence[Any],
                      comparison: Mapping[str, Any], dropped_lines: Sequence[Any], dropped_pins: Sequence[Any],
                      unverified_sources: Sequence[Any], policy: str, caller_context: Mapping[str, Any],
                      model: str | None, prompt_version: str, ledger_ids: Sequence[str], caller: str,
                      caller_ref: str | None) -> None:
    connection.execute(
        "INSERT INTO source_comparisons (id,query_hash,query_md,requested_perspectives_json,counterpart_keys_json,"
        "comparison_json,dropped_lines_json,dropped_pins_json,unverified_sources_json,policy,caller_context_json,"
        "model,prompt_version,ledger_ids_json,caller,caller_ref,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (id, query_hash, query_md, _dumps(list(requested_perspectives)), _dumps(list(counterpart_keys)),
         _dumps(dict(comparison)), _dumps(list(dropped_lines)), _dumps(list(dropped_pins)),
         _dumps(list(unverified_sources)), policy, _dumps(dict(caller_context)), model, prompt_version,
         _dumps(list(ledger_ids)), caller, caller_ref, created_at),
    )


def _comparison(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    for key in ("requested_perspectives", "counterpart_keys", "dropped_lines", "dropped_pins",
                "unverified_sources", "ledger_ids"):
        value[key] = _loads(value.pop(f"{key}_json"), [])
    value["comparison"] = _loads(value.pop("comparison_json"), {})
    value["caller_context"] = _loads(value.pop("caller_context_json"), {})
    return value


def comparison_row(connection: sqlite3.Connection, comparison_id: str) -> dict[str, Any] | None:
    if not table_exists(connection, "source_comparisons"):
        return None
    row = connection.execute("SELECT * FROM source_comparisons WHERE id=?", (comparison_id,)).fetchone()
    return None if row is None else _comparison(row)


def find_comparison(connection: sqlite3.Connection, *, query_hash: str, policy: str,
                    counterpart_keys: Sequence[Any]) -> dict[str, Any] | None:
    """A stored comparison of the same question over the same counterparts under the same policy."""

    if not table_exists(connection, "source_comparisons"):
        return None
    wanted = _dumps(list(counterpart_keys))
    row = connection.execute(
        "SELECT * FROM source_comparisons WHERE query_hash=? AND policy=? AND counterpart_keys_json=? "
        "ORDER BY created_at DESC LIMIT 1", (query_hash, policy, wanted)).fetchone()
    return None if row is None else _comparison(row)


# -- spend ---------------------------------------------------------------------


#: Receipt owner kinds the service's paid steps record under (the daily cap).
SERVICE_OWNER_KINDS = ("source_exercise_import", "source_solution_match", "source_compare",
                       "exercise_discrimination", "worked_example_equivalence")


def spend_since(connection: sqlite3.Connection, since: str, *,
                owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS) -> dict[str, Any]:
    """Provider-reported cost and count of physical requests (leaf receipts) since ``since``.

    ``owner_kinds`` None counts every receipt (an owner-run batch that runs
    alone). Subscription (Codex) requests report no marginal cost: they are
    counted, never priced (``estimated_only``).
    """

    if not table_exists(connection, "model_call_receipts"):
        return {"usd": 0.0, "requests": 0, "requests_reporting_cost": 0}
    sql = ("SELECT COUNT(*), COUNT(r.cost), COALESCE(SUM(r.cost), 0) FROM model_call_receipts r "
           "WHERE r.started_at >= ? AND NOT EXISTS "
           "(SELECT 1 FROM model_call_receipts c WHERE c.parent_call_id = r.id)")
    params: list[Any] = [since]
    if owner_kinds is not None:
        sql += f" AND r.owner_kind IN ({','.join('?' for _ in owner_kinds)})"
        params.extend(owner_kinds)
    requests, reporting, usd = connection.execute(sql, params).fetchone()
    return {"usd": float(usd or 0.0), "requests": int(requests or 0), "requests_reporting_cost": int(reporting or 0)}


__all__ = [
    "comparison_row",
    "find_comparison",
    "insert_comparison",
    "SERVICE_OWNER_KINDS",
    "spend_since",
    "CHECK_STATUSES",
    "KEY_STATUS_LABELS",
    "VERIFIED_STATUSES",
    "effective_key_status",
    "reference_content_hash",
    "exercise_import_ids",
    "unverified_import_ids",
    "import_row",
    "imported_regions",
    "imports",
    "imports_for_item",
    "insert_import",
    "insert_key_check",
    "is_exercise_import",
    "is_reader_import",
    "key_checks_for_item",
    "reference_status_for_item",
    "update_import",
    "IMPRESSION_SURFACES",
    "column_exists",
    "impressions_for_proposal",
    "impressions_of_item",
    "impressions_of_spans",
    "insert_impression",
    "table_exists",
]
