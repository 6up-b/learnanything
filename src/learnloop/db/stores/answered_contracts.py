"""The question each answer was graded under (method-explicit-3 review F3).

Read-only: the statement and required method an attempt's assessment
contract froze, for the readers of a recorded answer (exam review,
adjudication, the diagnoser and its history, review exports), which render it
with ``learnloop.vault.required_method.answered_prompt``. The contract is the
one ``learnloop.attempts.attempts.attempt_graded_contract`` reads: the first
its evidence rows cite, superseded rows included (a regrade outside a
method-explicit item writes rows that cite none).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from typing import Any

_CHUNK = 500


def _table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,),
    ).fetchone() is not None


def answered_contracts(
    connection: sqlite3.Connection, attempt_ids: Iterable[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """``{attempt id: {"prompt": ..., "required_method": ...}}`` for each
    attempt (every attempt when ``attempt_ids`` is None) whose evidence cites
    an assessment contract: the frozen statement, and the frozen required
    method (``{"name", "criterion_ids"}``) or None. An attempt graded before
    contracts is absent."""

    if not _table(connection, "grading_evidence") or not _table(connection, "assessment_contract_versions"):
        return {}
    first: dict[str, str] = {}
    sql = ("SELECT attempt_id, assessment_contract_version_id FROM grading_evidence "
           "WHERE assessment_contract_version_id IS NOT NULL")
    order = " ORDER BY attempt_id, created_at, criterion_id"
    if attempt_ids is None:
        for attempt_id, version_id in connection.execute(sql + order):
            first.setdefault(str(attempt_id), str(version_id))
    else:
        ids = sorted({str(value) for value in attempt_ids if value})
        for start in range(0, len(ids), _CHUNK):
            chunk = ids[start:start + _CHUNK]
            marks = ",".join("?" for _ in chunk)
            for attempt_id, version_id in connection.execute(f"{sql} AND attempt_id IN ({marks}){order}", chunk):
                first.setdefault(str(attempt_id), str(version_id))
    versions = sorted(set(first.values()))
    frozen: dict[str, dict[str, Any]] = {}
    for start in range(0, len(versions), _CHUNK):
        chunk = versions[start:start + _CHUNK]
        marks = ",".join("?" for _ in chunk)
        for version_id, prompt, method in connection.execute(
            "SELECT id, json_extract(contract_json, '$.prompt'), json_extract(contract_json, '$.required_method') "
            f"FROM assessment_contract_versions WHERE id IN ({marks})", chunk,
        ):
            try:
                parsed = json.loads(method) if isinstance(method, str) else None
            except ValueError:
                parsed = None
            frozen[str(version_id)] = {
                "prompt": prompt if isinstance(prompt, str) else None,
                "required_method": parsed if isinstance(parsed, dict) and str(parsed.get("name") or "").strip()
                else None,
            }
    return {attempt_id: frozen[version_id] for attempt_id, version_id in first.items() if version_id in frozen}


__all__ = ["answered_contracts"]
