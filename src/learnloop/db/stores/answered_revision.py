"""Which revision of its item an attempt answered, from the stored facts, for every reader.

One answer for the protection view (``adaptive_difficulty.material_view``), the grade-time forecaster and its receipt
writer (``adaptive_difficulty.grade_forecast``), so no reader judges an answer by fewer facts than another. The facts,
in their fixed precedence (the first is what the learner was shown when there are several):

1. the contract frozen when the item was presented (``forecast_item_revision`` of the attempt's first-grade contract,
   or of the draft's own contract before the attempt is stored);
2. the plan presentation's frozen revision (``item_serve_inputs``);
3. the scheduler selection's revision (``decision_features``' ``content_hash`` for the attempt's candidate, recorded
   no later than the answer);
4. the revision the attempt's grade-time receipt names.

A reader deciding protection treats the attempt as withheld when ANY of them is withheld: an answer to held-out
material is never read because a later fact names a public revision. Pure reads; nothing here writes.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

GRADE_RECEIPT_KIND = "item_unassisted_success_at_grade"


def _table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() \
        is not None


def contract_revision(connection: sqlite3.Connection, contract_version_id: Any) -> str | None:
    """The full revision a contract cites (from mvp-0.74), or None."""

    if not contract_version_id or not _table(connection, "assessment_contract_versions"):
        return None
    row = connection.execute("SELECT json_extract(contract_json, '$.forecast_item_revision') "
                             "FROM assessment_contract_versions WHERE id = ?", (str(contract_version_id),)).fetchone()
    return str(row[0]) if row and row[0] else None


def presentation_revision(connection: sqlite3.Connection, plan_presentation_id: Any) -> str | None:
    """The revision a plan presentation froze when it was served, or None."""

    if not plan_presentation_id or not _table(connection, "item_serve_inputs"):
        return None
    row = connection.execute("SELECT content_hash FROM item_serve_inputs WHERE plan_presentation_id = ? "
                             "ORDER BY created_at, id LIMIT 1", (str(plan_presentation_id),)).fetchone()
    return str(row[0]) if row and row[0] else None


def selection_revision(connection: sqlite3.Connection, scheduler_candidate_id: Any, answered_at: Any) -> str | None:
    """The revision the scheduler's selection scored for the attempt's candidate, recorded by the answer, or None."""

    if not scheduler_candidate_id or not _table(connection, "decision_features"):
        return None
    row = connection.execute(
        "SELECT json_extract(item_demand_vector_json, '$.content_hash') FROM decision_features "
        "WHERE decision_type = 'selection' AND decision_id = ? AND (? IS NULL OR created_at <= ?)",
        (str(scheduler_candidate_id), answered_at, answered_at)).fetchone()
    return str(row[0]) if row and row[0] else None


def draft_revisions(connection: sqlite3.Connection, *, contract_version_id: Any = None, plan_presentation_id: Any = None,
                    scheduler_candidate_id: Any = None, answered_at: Any = None) -> tuple[str, ...]:
    """The revisions an answer not yet stored names, in precedence order (facts 1-3)."""

    found = (contract_revision(connection, contract_version_id), presentation_revision(connection, plan_presentation_id),
             selection_revision(connection, scheduler_candidate_id, answered_at))
    return tuple(dict.fromkeys(value for value in found if value))


def _receipt_revision(versions_json: Any, practice_item_id: Any, item_content_hash: Any) -> str | None:
    if item_content_hash:
        return str(item_content_hash)
    try:
        target = (json.loads(versions_json or "{}").get("snapshot") or {}).get("target", {}).get("target") or {}
        return next((str(m["revision"]) for m in target.get("members", ())
                     if m.get("kind") == "item" and m.get("id") == practice_item_id and m.get("revision")), None)
    except (ValueError, TypeError, AttributeError):
        return None


def all_answered_revisions(connection: sqlite3.Connection) -> dict[str, tuple[str, ...]]:
    """Every stored attempt's answered revisions (facts 1-4), in precedence order, one pass per fact."""

    if not _table(connection, "practice_attempts"):
        return {}
    facts: dict[str, list[str]] = {}

    def add(attempt_id: Any, revision: Any) -> None:
        if revision:
            values = facts.setdefault(str(attempt_id), [])
            if str(revision) not in values:
                values.append(str(revision))

    if _table(connection, "grading_evidence") and _table(connection, "assessment_contract_versions"):
        # The presentation's contract: a first grade's rows (a regrade or an adjudication cites the one IT graded).
        for attempt_id, revision in connection.execute(
                "SELECT e.attempt_id, json_extract(c.contract_json, '$.forecast_item_revision') FROM grading_evidence e "
                "JOIN assessment_contract_versions c ON c.id = e.assessment_contract_version_id "
                "WHERE COALESCE(e.grading_revision, 0) = 0 ORDER BY e.attempt_id, e.rowid"):
            add(attempt_id, revision)
    if _table(connection, "item_serve_inputs"):
        for attempt_id, revision in connection.execute(
                "SELECT a.id, s.content_hash FROM practice_attempts a JOIN item_serve_inputs s "
                "ON s.plan_presentation_id = a.plan_presentation_id ORDER BY a.id, s.created_at, s.id"):
            add(attempt_id, revision)
    if _table(connection, "decision_features"):
        for attempt_id, revision in connection.execute(
                "SELECT a.id, json_extract(d.item_demand_vector_json, '$.content_hash') FROM practice_attempts a "
                "JOIN decision_features d ON d.decision_type = 'selection' AND d.decision_id = a.scheduler_candidate_id "
                "AND d.created_at <= a.created_at ORDER BY a.id"):
            add(attempt_id, revision)
    if _table(connection, "forecast_receipts"):
        for attempt_id, versions_json, item_id, item_hash in connection.execute(
                "SELECT source_attempt_id, versions_json, practice_item_id, item_content_hash FROM forecast_receipts "
                "WHERE kind = ? AND source_attempt_id IS NOT NULL", (GRADE_RECEIPT_KIND,)):
            add(attempt_id, _receipt_revision(versions_json, item_id, item_hash))
    return {key: tuple(values) for key, values in facts.items()}


__all__ = ["all_answered_revisions", "contract_revision", "draft_revisions", "presentation_revision",
           "selection_revision"]
