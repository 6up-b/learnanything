"""SQL for the canonical-sources service (spec_source_practice_and_probes_v1).

Callers own transactions and pass a connection, as with ``practice_index``.
``db`` sits below every domain, so the attempt transaction, the tutor and the
remediation path can record and read here without importing the service
(SC12). Nothing here is evidence; the one DERIVED table (S5's outcome join)
is cleared and rebuilt only by its replayer.
"""
from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
import json
import math
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


#: ``judgment_ledger`` task recording that a replacement grade was read against
#: content whose key is not verified (§7.3a, "Replacement grades").
REFERENCE_BINDING_TASK = "attempt_reference_binding"


def bind_replacement_grade(connection: sqlite3.Connection, *, attempt_id: str, item: Any, gated: bool,
                           grading: str, created_at: str) -> str | None:
    """C3 for a grade that replaces an attempt's grade (§7.3a, "Replacement grades").

    A regrade, or an adjudication against the key, reads the item as it is
    now, so the grade it writes is bound to that content exactly as an
    attempt's first grade is. When the vault is at the gate's tag (``gated``)
    and that content's key is not verified, the attempt's
    ``reference_status`` is lowered to ``unverified`` in the caller's
    transaction, before its replay, so every reader of the column (the
    projection, the evidence timeline, the learner field, rebuilds) gates the
    grade now in force. A ``judgment_ledger`` row keeps the attempt-time status,
    the content's key status and its hash. The status is never raised: a key
    that verifies later does not make an earlier grade certify. Returns
    ``"unverified"`` when it lowered the status, else None.
    """

    if not gated or not column_exists(connection, "practice_attempts", "reference_status"):
        return None
    if reference_status_for_item(connection, item) != "unverified":
        return None
    row = connection.execute("SELECT reference_status FROM practice_attempts WHERE id=?", (attempt_id,)).fetchone()
    if row is None or row[0] == "unverified":
        return None
    from learnloop.db.stores.judgments import append_judgment

    content = reference_content_hash(item)
    connection.execute("UPDATE practice_attempts SET reference_status='unverified' WHERE id=?", (attempt_id,))
    append_judgment(
        connection, task=REFERENCE_BINDING_TASK, left_kind="practice_attempt", left_id=attempt_id,
        right_kind="reference_content", right_id=content, judge="verifier", input_hash=content,
        verdict="unverified", created_at=created_at,
        rationale=(f"grading={grading}; attempt_time_status={row[0]}; "
                   f"key_status={effective_key_status(connection, item)}"),
    )
    return "unverified"


# -- S2b: serve-time independence of a need's source import (§5.4, §8.5 item 4) -------


def need_source_import(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None:
    """The source-first import that fulfilled an intervention need with this item
    (its retrieval provenance: need, proposal, book solution), or None."""

    if not table_exists(connection, "source_exercise_imports") \
            or not column_exists(connection, "source_exercise_imports", "need_id"):
        return None
    row = connection.execute(
        "SELECT * FROM source_exercise_imports WHERE practice_item_id=? AND need_id IS NOT NULL "
        "AND status='written' ORDER BY created_at DESC, id DESC LIMIT 1", (practice_item_id,)).fetchone()
    return None if row is None else _import(row)


WORKED_EXAMPLE_LEDGER_TASK = "worked_example_equivalence"


def exercise_key(extraction_id: str, span_ids: Iterable[str]) -> str:
    """A stable identity for an unimported exercise (ledger ids, receipts, impressions)."""

    return "srcex:" + extraction_id + ":" + ",".join(str(span) for span in span_ids)


def serve_time_exposure(connection: sqlite3.Connection, *, practice_item_id: str, family_item_ids: Iterable[str],
                        extraction_id: str | None, span_ids: Iterable[str], solution_span_ids: Iterable[str] = (),
                        candidate_keys: Iterable[str] = (), studied_extraction_ids: Iterable[str] | None = None,
                        since: str) -> dict[str, Any]:
    """The exposure rule's facts at serving time, with no model call (§5.4).

    Rules 1-3 and 5 as the valuation applied them: an attempt on the item, a
    reveal on it or its family, source text shown from its span or its book
    solution, an impression of it from any proposal (a system-initiated check
    has no pick of its own). Rule 4 reads the judge's verdicts from the ledger:
    a worked example studied within the window (shown, or in a section read;
    the stored ``worked_example`` hint, a superset of the effective one) that
    the judge called ``equivalent`` or ``related`` to this candidate excludes
    it, and one never judged against it excludes it too (``unjudged``: never
    assumed unrelated). ``candidate_keys`` are the ids the candidate was
    judged under (the item id, the exercise key it had before import);
    ``studied_extraction_ids`` is the candidate's teaching scope, the scope
    rule 4's shortlist is drawn from at valuation (None: every extraction).
    """

    reasons: list[str] = []
    inputs: dict[str, Any] = {"since": since}
    family = sorted({str(value) for value in family_item_ids} | {practice_item_id})
    if connection.execute("SELECT 1 FROM practice_attempts WHERE practice_item_id=? LIMIT 1",
                          (practice_item_id,)).fetchone() is not None:
        reasons.append("attempted")
    if table_exists(connection, "reveal_events"):
        marks = ",".join("?" for _ in family)
        reveals = connection.execute(
            f"SELECT id, practice_item_id FROM reveal_events WHERE practice_item_id IN ({marks}) AND created_at >= ?",
            (*family, since)).fetchall()
        if reveals:
            reasons.append("revealed" if any(row[1] == practice_item_id for row in reveals) else "family_revealed")
            inputs["reveal_ids"] = [str(row[0]) for row in reveals]
    spans = [str(span) for span in span_ids]
    solution = [str(span) for span in solution_span_ids]
    if extraction_id and (spans or solution) and table_exists(connection, "source_exposure_events"):
        keys = [(extraction_id, span) for span in dict.fromkeys(spans + solution)]
        marks = ",".join("(?, ?)" for _ in keys)
        exposed = connection.execute(
            f"SELECT id FROM source_exposure_events WHERE (extraction_id, span_id) IN (VALUES {marks}) "
            "AND created_at >= ?", (*[value for key in keys for value in key], since)).fetchall()
        if exposed:
            reasons.append("source_exposed")
            inputs["exposure_event_ids"] = [str(row[0]) for row in exposed]
    impressions = impressions_of_item(connection, practice_item_id, since=since)
    if extraction_id and spans:
        impressions += impressions_of_spans(connection, extraction_id, spans, since=since)
    if impressions:
        reasons.append("seen_in_proposal")
        inputs["impression_ids"] = sorted({row["id"] for row in impressions})
    studied: set[tuple[str, str]] = set()
    if table_exists(connection, "source_exposure_events"):
        studied |= {(str(row[0]), str(row[1])) for row in connection.execute(
            "SELECT e.extraction_id, e.span_id FROM source_exposure_events e JOIN source_document_blocks b "
            "ON b.extraction_id = e.extraction_id AND b.span_id = e.span_id "
            "WHERE e.created_at >= ? AND b.role_hint = 'worked_example'", (since,))}
    if table_exists(connection, "reader_section_progress") and table_exists(connection, "source_document_units"):
        for extraction, section in connection.execute(
                "SELECT extraction_id, section_id FROM reader_section_progress WHERE updated_at >= ? AND "
                "(completed_at IS NOT NULL OR (span_count > 0 AND spans_seen >= span_count))", (since,)).fetchall():
            unit = connection.execute(
                "SELECT span_ids_json FROM source_document_units WHERE extraction_id=? AND unit_id=?",
                (extraction, section)).fetchone()
            unit_spans = [str(span) for span in _loads(unit[0], []) if span] if unit is not None else []
            if unit_spans:
                marks = ",".join("?" for _ in unit_spans)
                studied |= {(str(extraction), str(row[0])) for row in connection.execute(
                    f"SELECT span_id FROM source_document_blocks WHERE extraction_id=? AND span_id IN ({marks}) "
                    "AND role_hint = 'worked_example'", (extraction, *unit_spans))}
    if studied_extraction_ids is not None:
        in_scope = {str(value) for value in studied_extraction_ids}
        studied = {key for key in studied if key[0] in in_scope}
    if studied:
        lefts = sorted({practice_item_id, *[str(key) for key in candidate_keys]})
        marks = ",".join("?" for _ in lefts)
        verdicts: dict[str, str] = {}
        for right_id, verdict in connection.execute(
                f"SELECT right_id, verdict FROM judgment_ledger WHERE task=? AND left_id IN ({marks}) "
                "ORDER BY created_at", (WORKED_EXAMPLE_LEDGER_TASK, *lefts)).fetchall():
            verdicts[str(right_id)] = str(verdict)
        judged = {f"{key[0]}:{key[1]}": verdicts.get(f"{key[0]}:{key[1]}") for key in sorted(studied)}
        inputs["studied_worked_examples"] = judged
        found = set(judged.values())
        if "equivalent" in found:
            reasons.append("equivalent_worked_example")
        elif "related" in found:
            reasons.append("related_worked_example")
        elif None in found:
            reasons.append("worked_example_unjudged")
    return {"eligible": not reasons, "reasons": reasons, "inputs": inputs,
            "exposure_rule_version": "reading_exposure_v1", "checked": "serve_time"}


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


# -- S4: source_tool_calls (RECEIPT; append-only) ---------------------------------------

_TOOL_CALL_JSON = {"context_json": ("context", {}), "arguments_json": ("arguments", {}),
                   "dropped_json": ("dropped", []), "result_keys_json": ("result_keys", []),
                   "source_versions_json": ("source_versions", {}), "cost_json": ("cost", None)}


def insert_tool_call(connection: sqlite3.Connection, *, id: str, created_at: str, row_kind: str,
                     caller_kind: str, caller_ref: str | None, context: Mapping[str, Any], policy: str,
                     tool: str, arguments: Mapping[str, Any], status: str, parent_id: str | None = None,
                     dropped: Sequence[Any] = (), ledger_id: str | None = None, result_ref: str | None = None,
                     result_keys: Sequence[Any] = (), source_versions: Mapping[str, Any] | None = None,
                     model: str | None = None, prompt_version: str | None = None, latency_ms: int | None = None,
                     cost: Mapping[str, Any] | None = None) -> str:
    connection.execute(
        "INSERT INTO source_tool_calls (id, parent_id, row_kind, created_at, caller_kind, caller_ref, context_json, "
        "policy, tool, arguments_json, dropped_json, ledger_id, status, result_ref, result_keys_json, "
        "source_versions_json, model, prompt_version, latency_ms, cost_json) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (id, parent_id, row_kind, created_at, caller_kind, caller_ref, _dumps(dict(context)), policy, tool,
         _dumps(dict(arguments)), _dumps(list(dropped)), ledger_id, status, result_ref, _dumps(list(result_keys)),
         _dumps(dict(source_versions or {})), model, prompt_version, latency_ms,
         None if cost is None else _dumps(dict(cost))),
    )
    return id


def _tool_call(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    for column, (key, default) in _TOOL_CALL_JSON.items():
        value[key] = _loads(value.pop(column), default)
    return value


def tool_call(connection: sqlite3.Connection, call_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM source_tool_calls WHERE id=?", (call_id,)).fetchone()
    return None if row is None else _tool_call(row)


def tool_call_runs(connection: sqlite3.Connection, request_id: str) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM source_tool_calls WHERE parent_id=? ORDER BY created_at, id",
                              (request_id,)).fetchall()
    return [_tool_call(row) for row in rows]


def tool_calls(connection: sqlite3.Connection, *, caller_kind: str | None = None,
               caller_ref: str | None = None) -> list[dict[str, Any]]:
    clauses, parameters = [], []
    if caller_kind is not None:
        clauses.append("caller_kind=?")
        parameters.append(caller_kind)
    if caller_ref is not None:
        clauses.append("caller_ref=?")
        parameters.append(caller_ref)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(f"SELECT * FROM source_tool_calls{where} ORDER BY created_at, id", parameters).fetchall()
    return [_tool_call(row) for row in rows]


# -- S5: retrieval_interventions (RAW_LEDGER) and their outcome join (DERIVED) ----------

INTERVENTION_KINDS = ("source_passage", "source_exercise", "practice_pick", "comparison", "remediation_passage")
_INTERVENTION_JSON = {"assets_json": ("assets", {}), "targets_json": ("targets", {}),
                      "state_ref_json": ("state_ref", {}), "valuation_json": ("valuation", None),
                      "exposure_event_ids_json": ("exposure_event_ids", []),
                      "impression_ids_json": ("impression_ids", []), "eligibility_json": ("eligibility", None)}


def insert_intervention(connection: sqlite3.Connection, *, id: str, created_at: str, kind: str,
                        caller_kind: str | None = None, caller_ref: str | None = None, intent: str | None = None,
                        policy: str | None = None, tool_call_id: str | None = None,
                        proposal_id: str | None = None, question_event_id: str | None = None,
                        remediation_episode_id: str | None = None, router_decision_id: str | None = None,
                        assets: Mapping[str, Any] | None = None, targets: Mapping[str, Any] | None = None,
                        state_ref: Mapping[str, Any] | None = None, valuation: Mapping[str, Any] | None = None,
                        exposure_event_ids: Sequence[Any] = (), impression_ids: Sequence[Any] = (),
                        reading_exposure_label: str | None = None, eligibility: Mapping[str, Any] | None = None,
                        seconds_since_related_exposure: float | None = None, session_id: str | None = None,
                        attempt_id: str | None = None, algorithm_version: str | None = None) -> str:
    if kind not in INTERVENTION_KINDS:
        raise ValueError(f"kind must be one of {', '.join(INTERVENTION_KINDS)}")
    connection.execute(
        "INSERT INTO retrieval_interventions (id, created_at, kind, caller_kind, caller_ref, intent, policy, "
        "tool_call_id, proposal_id, question_event_id, remediation_episode_id, router_decision_id, assets_json, "
        "targets_json, state_ref_json, valuation_json, exposure_event_ids_json, impression_ids_json, "
        "reading_exposure_label, eligibility_json, seconds_since_related_exposure, session_id, attempt_id, "
        "algorithm_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (id, created_at, kind, caller_kind, caller_ref, intent, policy, tool_call_id, proposal_id,
         question_event_id, remediation_episode_id, router_decision_id, _dumps(dict(assets or {})),
         _dumps(dict(targets or {})), _dumps(dict(state_ref or {})),
         None if valuation is None else _dumps(dict(valuation)), _dumps(list(exposure_event_ids)),
         _dumps(list(impression_ids)), reading_exposure_label, None if eligibility is None else _dumps(dict(eligibility)),
         seconds_since_related_exposure, session_id, attempt_id, algorithm_version),
    )
    return id


def _intervention(row: sqlite3.Row) -> dict[str, Any]:
    value = dict(row)
    for column, (key, default) in _INTERVENTION_JSON.items():
        value[key] = _loads(value.pop(column), default)
    return value


def interventions(connection: sqlite3.Connection, *, proposal_id: str | None = None) -> list[dict[str, Any]]:
    if not table_exists(connection, "retrieval_interventions"):
        return []
    if proposal_id is None:
        rows = connection.execute("SELECT * FROM retrieval_interventions ORDER BY created_at, id").fetchall()
    else:
        rows = connection.execute("SELECT * FROM retrieval_interventions WHERE proposal_id=? ORDER BY created_at, id",
                                  (proposal_id,)).fetchall()
    return [_intervention(row) for row in rows]


OUTCOME_COLUMNS = ("intervention_id", "as_of", "next_attempt_id", "next_correctness", "next_assisted",
                   "next_window", "cold_attempt_id", "cold_outcome_state", "cold_correctness", "observed_bucket",
                   "predicted_outcomes_json", "predicted_minutes", "actual_minutes", "hypothesis_movement_json",
                   "learner_signals_json", "action_before", "action_after", "action_flipped", "outcome_version")


def insert_outcomes(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        values = []
        for column in OUTCOME_COLUMNS:
            value = row.get(column.removesuffix("_json")) if column.endswith("_json") else row.get(column)
            if column.endswith("_json"):
                value = None if value is None and column == "predicted_outcomes_json" else _dumps(
                    value if value is not None else ({} if column == "hypothesis_movement_json" else []))
            values.append(value)
        connection.execute(f"INSERT INTO retrieval_intervention_outcomes ({', '.join(OUTCOME_COLUMNS)}) "
                           f"VALUES ({', '.join('?' for _ in OUTCOME_COLUMNS)})", values)
        count += 1
    return count


def replace_outcomes(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> tuple[int, int]:
    """The replayer's write: clear and refill inside the caller's transaction."""

    cleared = connection.execute("DELETE FROM retrieval_intervention_outcomes").rowcount
    return cleared, insert_outcomes(connection, rows)


def outcomes(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not table_exists(connection, "retrieval_intervention_outcomes"):
        return {}
    found = {}
    for row in connection.execute("SELECT * FROM retrieval_intervention_outcomes ORDER BY intervention_id"):
        value = dict(row)
        for column in ("predicted_outcomes_json", "hypothesis_movement_json", "learner_signals_json"):
            value[column.removesuffix("_json")] = _loads(value.pop(column), None)
        found[value["intervention_id"]] = value
    return found


def _root_budget(connection: sqlite3.Connection, parent_id: str | None, budget_json: str | None,
                 cache: dict[str, str | None]) -> dict[str, Any]:
    """The budget the receipt's root call declared (``budget_json``), or {}."""

    current, budget = parent_id, budget_json
    seen = 0
    while current is not None and seen < 16:
        seen += 1
        if current not in cache:
            row = connection.execute(
                "SELECT parent_call_id, budget_json FROM model_call_receipts WHERE id = ?", (current,)).fetchone()
            cache[current] = None if row is None else json.dumps([row[0], row[1]])
        cached = cache[current]
        if cached is None:
            break
        current, budget = json.loads(cached)
    try:
        declared = json.loads(budget or "{}") or {}
    except (TypeError, ValueError):
        declared = {}
    return declared if isinstance(declared, dict) else {}


def _receipt_billing(declared: Mapping[str, Any], provider: str | None, subscription_providers: Collection[str]) -> str:
    """``subscription`` or ``metered``: the root receipt's declared budget says
    which (``billing``, ``practice_index.billing``, ``pf.cost_basis``); a root
    with no declared budget falls back to the provider's profile type."""

    if declared.get("billing") == "subscription" \
            or (declared.get("practice_index") or {}).get("billing") == "subscription" \
            or (declared.get("pf") or {}).get("cost_basis") == "estimated_only":
        return "subscription"
    if declared:
        return "metered"
    return "subscription" if provider and provider in subscription_providers else "metered"


def receipt_time_floor(since: str) -> str:
    """``since`` as the earliest string a receipt stamp of that UTC second sorts at or after.

    Receipts are stamped ``…52.822906+00:00`` and run starts ``…52Z``; compared
    as strings, ``.`` sorts before ``Z``, so a request in a run's first second
    went uncounted. The floor is the second itself with no suffix, which every
    stamp of that second (any fraction, ``Z`` or ``+00:00``) sorts at or after.
    It may count a request from earlier in the same second, never miss one.
    """

    try:
        moment = datetime.fromisoformat(since.strip().replace("Z", "+00:00"))
    except ValueError:
        return since
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment.replace(microsecond=0).isoformat(timespec="seconds")


# -- the daily cap's shared reservations (migrations 191-192) ---------------------------------------
#
# One accounting function (``service_spend_accounting``) is the daily cap's
# total for admission, recovery and every report (sources-spend-accounting:
# Codex F2 reopened, F14, and the stage review's F1 and F2). Each request
# counts once, except where a legacy row's identity is ambiguous (below):
#
# * a reservation whose owner is alive (its lease unexpired) counts the larger
#   of its own charge (the estimate, reconciled upward) and what the receipts
#   naming it show: a worker that dies after its receipt is written but before
#   it reconciles leaves both, and the receipt is the durable one;
# * a reconciled (``settled``) reservation counts what its receipts show: their
#   reported cost when every one reports it, else the larger of that and its
#   reconciled charge (which bounds a receipt whose finish was lost);
# * an orphan (in flight, its owner's lease run out) is what recovery makes
#   of it: reconciled with its receipts, or released (nothing) when it has
#   none, since every request writes its receipt before it is sent;
# * a released reservation counts what its receipts show (an owner presumed
#   dead that sent anyway);
# * a legacy row (written before receipts named reservations, migration 192)
#   counts its own charge. An unlinked receipt is taken for its request's, and
#   not counted again, only when the two are correlated beyond doubt: the
#   receipt started during the row's lifetime, the row settled at exactly
#   what the receipt shows, and neither has another such partner. Where that
#   identity is ambiguous both count (conservatively, never less than was
#   spent) and the report says how much may be counted twice
#   (``legacy.uncertain_usd``);
# * a receipt naming no reservation of the envelope (spend before the ledger,
#   or another path) counts once by its own cost.
#
# "What its receipts show": each linked leaf receipt's reported cost, exactly,
# whatever its tokens; a receipt that reports no cost is priced at the rate
# its request recorded when it was admitted, else (none recorded) at the
# owner's service rate; an unfinished or unpriced one is bounded by the
# reservation's admitted estimate, never free. ``pricing`` counts the basis
# each receipt was priced on.


SERVICE_SPEND_TABLE = "source_service_spend"


#: A root receipt's ``budget_json`` key naming the ledger reservations its
#: request was admitted under (``SpendEnvelope.reservation_ref``).
RESERVATIONS_KEY = "envelope_reservations"

#: How a metered receipt's dollars were found (the accounting's ``pricing``).
PRICING_BASES = ("reported", "recorded_rate", "owner_rate", "unpriced")

#: Money comparisons tolerate float summation noise, never a real amount.
_EPSILON = 1e-12

_LEDGER_COLUMNS = ("id", "day", "reserved_usd", "charged_usd", "state", "legacy", "process", "lease_expires_at",
                   "resolved_by", "created_at", "updated_at")


def _moment(value: Any) -> datetime | None:
    """An ISO stamp (``Z``, an offset, or naive UTC) as an aware UTC datetime; None if unreadable."""

    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def ledger_stamp(moment: datetime | str) -> str:
    """The ledger's stamp: UTC to the second with ``Z`` (``utc_now_iso``'s
    form), so stored leases compare with it as strings."""

    parsed = _moment(moment)
    if parsed is None:
        raise ValueError(f"not a timestamp: {moment!r}")
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _recorded_rate(declared: Mapping[str, Any]) -> float | None:
    """The per-token rate a request recorded on its root receipt when it was
    admitted (``practice_index.price_per_million``: ``PaidCalls`` and query
    embeddings; ``pf.price_per_million``: ``PFCaller``), or None."""

    for block in ("practice_index", "pf"):
        section = declared.get(block)
        if not isinstance(section, Mapping):
            continue
        try:
            price = float(section.get("price_per_million"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(price) and price > 0:
            return price / 1_000_000
    return None


def _metered_cost(cost: Any, tokens: int, recorded_rate: float | None,
                  owner_rate: float | None) -> tuple[float | None, str]:
    """A metered leaf receipt's dollars, and their basis (``PRICING_BASES``).

    ``reported``: the provider's reported cost, exactly, whatever its tokens:
    a paid request is never repriced. ``recorded_rate``: no reported cost; its
    tokens at the rate its request recorded when it was admitted.
    ``owner_rate``: no reported cost and no recorded rate; its tokens at the
    owner's service rate (the fallback). ``unpriced``: None, the dollars are
    unknown (unfinished, or no cost and no priced tokens)."""

    if cost is not None:
        return float(cost), "reported"
    if tokens and recorded_rate is not None:
        return tokens * recorded_rate, "recorded_rate"
    if tokens and owner_rate is not None:
        return tokens * owner_rate, "owner_rate"
    return None, "unpriced"


def _legacy_settlements(cost: Any, tokens: int, rates: Iterable[float | None]) -> list[float]:
    """What a legacy owner can have settled this receipt's request at. Every
    metered path of that era reconciled its reservation with the reported
    cost, or with the larger of it and the reported tokens at its price
    (``PaidCalls``, ``PFCaller``, the import's authoring); one that reported
    nothing settled at its estimate, which no receipt shows."""

    values = [] if cost is None else [float(cost)]
    for rate in rates:
        if rate is not None and tokens:
            priced = tokens * rate
            values.append(priced if cost is None else max(float(cost), priced))
    return values


def _estimated_tokens(tokens: int, usage_json: Any) -> int:
    """A subscription receipt's tokens: reported, else its own estimate."""

    if tokens:
        return tokens
    try:
        estimate = json.loads(usage_json or "{}") or {}
    except (TypeError, ValueError):
        estimate = {}
    return int(estimate.get("estimated_total_tokens") or 0) if isinstance(estimate, dict) else 0


def _ledger_rows(connection: sqlite3.Connection, envelope: str, day: str) -> tuple[list[dict[str, Any]], bool]:
    """The envelope's reservations on ``day``, and whether the table has
    migration 192's columns (a database read without migrating has not)."""

    present = {row[1] for row in connection.execute(f'PRAGMA table_info("{SERVICE_SPEND_TABLE}")')}
    select = ", ".join(column if column in present else f"NULL AS {column}" for column in _LEDGER_COLUMNS)
    rows = [dict(zip(_LEDGER_COLUMNS, tuple(row))) for row in connection.execute(
        f"SELECT {select} FROM {SERVICE_SPEND_TABLE} WHERE envelope=? AND day=? ORDER BY created_at, id",
        (envelope, day))]
    return rows, "legacy" in present


def _named_reservations(connection: sqlite3.Connection, envelope: str, refs: Collection[str]) -> set[str]:
    """Which of ``refs`` are reservations of ``envelope`` (on any day)."""

    found: set[str] = set()
    ordered = sorted(refs)
    for start in range(0, len(ordered), 500):
        chunk = ordered[start:start + 500]
        found.update(row[0] for row in connection.execute(
            f"SELECT id FROM {SERVICE_SPEND_TABLE} WHERE envelope=? AND id IN ({','.join('?' for _ in chunk)})",
            (envelope, *chunk)))
    return found


def _lifetime(created_at: Any, updated_at: Any) -> tuple[datetime, datetime] | None:
    """A legacy row's lifetime, as far as its stamps (to the second) tell: from
    the second it was reserved in to the end of the second it last changed in."""

    start, end = _moment(created_at), _moment(updated_at)
    if start is None or end is None:
        return None
    return start.replace(microsecond=0), end.replace(microsecond=0) + timedelta(seconds=1)


def _legacy_rows(connection: sqlite3.Connection, envelope: str, since: datetime) -> list[dict[str, Any]]:
    """The envelope's legacy rows (on any day) whose lifetime reaches ``since``."""

    found = []
    for handle, charged, created_at, updated_at in connection.execute(
            f"SELECT id, charged_usd, created_at, updated_at FROM {SERVICE_SPEND_TABLE} "
            "WHERE envelope=? AND legacy=1 ORDER BY created_at, id", (envelope,)):
        window = _lifetime(created_at, updated_at)
        if window is not None and window[1] > since:
            found.append({"id": handle, "charged": float(charged or 0.0), "window": window})
    return found


def _correlate_legacy(legacy: Sequence[Mapping[str, Any]], receipts: Sequence[Mapping[str, Any]]) -> dict[int, str]:
    """The unlinked receipts that are a legacy row's own request, beyond doubt
    (receipt index -> row id).

    Nothing names a legacy row, and its stamps are to the second, so a
    receipt that merely started during its lifetime may be another request's
    (one from before the ledger, another path, an overlapping request). A
    receipt is the row's own only when the row settled at exactly what it
    shows (``_legacy_settlements``), it started during the row's lifetime,
    and neither has another partner that fits: it is the row's one candidate,
    and the row is its one. Two receipts of the row's cost in its lifetime,
    or a row settled at its estimate, are ambiguous: nothing is covered."""

    candidates: dict[str, list[int]] = {}
    rows_of: dict[int, list[str]] = {}
    for row in legacy:
        start, end = row["window"]
        for index, receipt in enumerate(receipts):
            started = receipt["started"]
            if receipt["refs"] or receipt["billing"] != "metered" or started is None \
                    or not start <= started < end:
                continue
            if any(math.isclose(value, row["charged"], rel_tol=1e-9, abs_tol=_EPSILON)
                   for value in receipt["settlements"]):
                candidates.setdefault(row["id"], []).append(index)
                rows_of.setdefault(index, []).append(row["id"])
    return {indexes[0]: handle for handle, indexes in candidates.items()
            if len(indexes) == 1 and len(rows_of[indexes[0]]) == 1}


def _second_floor(moment: datetime) -> str:
    """``moment``'s second as the receipt scan's lower bound (``receipt_time_floor``'s form)."""

    return moment.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0).isoformat(timespec="seconds")


def service_spend_accounting(connection: sqlite3.Connection, *, envelope: str, day: str, since: str,
                             now: datetime | str, price_per_million: float | None = None,
                             subscription_providers: Collection[str] = (),
                             owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS) -> dict[str, Any]:
    """The daily cap's total for ``envelope`` on ``day`` (receipts since ``since``),
    as of ``now``: the one function admission, recovery and every report read.

    ``usd`` is every reservation of that day counted once (see the rules
    above) plus the service's receipts that name no reservation of the
    envelope, counted by their own cost (``owner_kinds``: the service's
    receipts; a receipt naming a reservation that no longer exists counts
    too). ``price_per_million`` is the owner's service rate, the fallback for
    a receipt that reports no cost and whose request recorded no rate
    (``pricing`` counts each basis). Subscription receipts are reported as
    ``estimated_only``, never capped. ``recovery`` lists what recovery would
    do to each orphan; the total already counts each orphan that way, so a
    report agrees with the admission that will recover it. ``legacy`` says
    which receipts legacy rows cover and how much of the total may be a
    legacy request counted twice (``uncertain_usd``).
    """

    stamp = ledger_stamp(now)
    current = _moment(stamp)
    floor = receipt_time_floor(since)
    floor_at = _moment(floor) or current
    rate = None if price_per_million is None else float(price_per_million) / 1_000_000
    out: dict[str, Any] = {
        "envelope": envelope, "day": day, "since": since, "as_of": stamp,
        "usd": 0.0, "reservations_usd": 0.0, "unlinked_receipts_usd": 0.0,
        "requests": 0, "requests_reporting_cost": 0,
        "metered": {"requests": 0, "usd": 0.0, "unpriced_requests": 0, "linked_requests": 0,
                    "legacy_covered_requests": 0},
        "pricing": {basis: 0 for basis in PRICING_BASES},
        "estimated_only": {"requests": 0, "tokens": 0, "usd": 0.0 if rate is not None else None},
        "reservations": {"rows": 0, "in_flight": 0, "orphaned": 0, "settled": 0, "released": 0, "legacy": 0},
        "legacy": {"rows": 0, "correlated": 0, "uncorrelated": 0, "covered_requests": 0,
                   "uncertain_requests": 0, "uncertain_usd": 0.0},
        "recovery": [],
    }
    ledger = table_exists(connection, SERVICE_SPEND_TABLE)
    rows, upgraded = _ledger_rows(connection, envelope, day) if ledger else ([], True)
    legacy = _legacy_rows(connection, envelope, floor_at) if ledger and upgraded else []
    leaves: list[tuple[Any, ...]] = []
    if table_exists(connection, "model_call_receipts"):
        # A receipt starts after its reservation was made: reading from the
        # earliest of today's reservations finds every receipt naming one, and
        # from the earliest legacy lifetime every receipt that could be its own.
        scan_from = min([floor] + [receipt_time_floor(row["created_at"]) for row in rows if row["created_at"]]
                        + [_second_floor(row["window"][0]) for row in legacy])
        columns = {row[1] for row in connection.execute("PRAGMA table_info(model_call_receipts)")}
        usage = "r.usage_json" if "usage_json" in columns else "NULL"
        budget = "r.budget_json" if "budget_json" in columns else "NULL"
        leaves = connection.execute(
            f"SELECT r.parent_call_id, r.owner_kind, r.provider, r.started_at, r.cost, r.input_tokens, "
            f"r.output_tokens, {usage}, {budget} FROM model_call_receipts r WHERE r.started_at >= ? AND NOT EXISTS "
            "(SELECT 1 FROM model_call_receipts c WHERE c.parent_call_id = r.id)", (scan_from,)).fetchall()
    cache: dict[str, str | None] = {}
    receipts: list[dict[str, Any]] = []
    refs_seen: set[str] = set()
    for parent_id, owner_kind, provider, started_at, cost, input_tokens, output_tokens, usage_json, budget_json in leaves:
        declared = _root_budget(connection, parent_id, budget_json, cache)
        refs = [str(ref) for ref in (declared.get(RESERVATIONS_KEY) or ()) if isinstance(ref, str)]
        refs_seen.update(refs)
        tokens = int(input_tokens or 0) + int(output_tokens or 0)
        recorded = _recorded_rate(declared)
        receipts.append({
            "refs": refs, "owner_kind": owner_kind, "started": _moment(started_at), "cost": cost,
            "tokens": tokens, "usage_json": usage_json, "recorded_rate": recorded,
            "billing": _receipt_billing(declared, provider, subscription_providers),
            "settlements": _legacy_settlements(cost, tokens, (recorded, rate)),
        })
    named = _named_reservations(connection, envelope, refs_seen) if ledger and refs_seen else set()
    linked: dict[str, dict[str, float]] = {row["id"]: {"priced": 0.0, "unknown": 0, "unreported": 0, "receipts": 0}
                                           for row in rows}
    if not upgraded:  # migration 192's rule, read without migrating: a row no receipt names is legacy
        for row in rows:
            row["legacy"] = 0 if row["id"] in named else 1
            window = _lifetime(row["created_at"], row["updated_at"]) if row["legacy"] else None
            if window is not None:
                legacy.append({"id": row["id"], "charged": float(row["charged_usd"] or 0.0), "window": window})
    own = _correlate_legacy(legacy, receipts) if legacy else {}
    covering = set(own.values())
    uncertain = [row["window"] for row in legacy if row["id"] not in covering]
    out["legacy"].update(rows=len(legacy), correlated=len(covering), uncorrelated=len(legacy) - len(covering))
    for index, receipt in enumerate(receipts):
        refs, started, cost = receipt["refs"], receipt["started"], receipt["cost"]
        in_window = started is not None and started >= floor_at
        service = bool(refs) or owner_kinds is None or receipt["owner_kind"] in owner_kinds
        if receipt["billing"] == "subscription":
            if service and in_window:
                used = _estimated_tokens(receipt["tokens"], receipt["usage_json"])
                out["requests"] += 1
                out["estimated_only"]["requests"] += 1
                out["estimated_only"]["tokens"] += used
                if rate is not None:
                    out["estimated_only"]["usd"] += used * rate
            continue
        value, basis = _metered_cost(cost, receipt["tokens"], receipt["recorded_rate"], rate)
        owner = next((ref for ref in refs if ref in named), None)
        if owner is not None:
            # Its reservation counts it, on the reservation's own day.
            if owner in linked:
                linked[owner]["receipts"] += 1
                linked[owner]["unreported"] += int(cost is None)
                if value is None:
                    linked[owner]["unknown"] += 1
                else:
                    linked[owner]["priced"] += value
                out["requests"] += 1
                out["metered"]["linked_requests"] += 1
                out["requests_reporting_cost"] += int(cost is not None)
                out["pricing"][basis] += 1
            continue
        if not service or not in_window:
            continue
        if index in own:
            out["metered"]["legacy_covered_requests"] += 1  # its legacy row counts it
            out["legacy"]["covered_requests"] += 1
            continue
        out["requests"] += 1
        out["metered"]["requests"] += 1
        out["requests_reporting_cost"] += int(cost is not None)
        out["pricing"][basis] += 1
        if value is None:
            out["metered"]["unpriced_requests"] += 1
        else:
            out["metered"]["usd"] += value
        if not refs and any(start <= started < end for start, end in uncertain):
            # It may be an uncorrelated legacy row's own request, counted twice.
            out["legacy"]["uncertain_requests"] += 1
            out["legacy"]["uncertain_usd"] += value or 0.0
    reserved_total = 0.0
    for row in rows:
        view = linked[row["id"]]
        charged = float(row["charged_usd"] or 0.0)
        reserved = float(row["reserved_usd"] or 0.0)
        priced = float(view["priced"])
        shown = max(priced, reserved) if view["unknown"] else priced  # what its receipts show
        if row["legacy"]:
            kind, cost = "legacy", max(charged, priced)
        elif row["state"] == "in_flight":
            lease = _moment(row["lease_expires_at"])
            if lease is not None and lease > current:
                kind, cost = "in_flight", max(charged, priced)
            else:  # an orphan: its owner is terminal
                kind = "orphaned"
                # An upward charge is the owner's own reconciled cost: durable too.
                upward = charged if charged > reserved + _EPSILON else 0.0
                action, cost = ("reconcile", max(shown, upward)) if view["receipts"] else ("release", 0.0)
                out["recovery"].append({"id": row["id"], "action": action, "charged_usd": cost})
        elif row["state"] == "settled":
            # Reconciled: its receipts' reported cost when every one reports
            # it (the durable truth, even when the owner settled without it);
            # else its reconciled charge bounds what the receipts leave open.
            exact = view["receipts"] and not view["unreported"]
            kind, cost = "settled", (priced if exact else max(charged, priced))
        else:
            kind, cost = "released", shown
        out["reservations"]["rows"] += 1
        out["reservations"][kind] += 1
        reserved_total += cost
    out["reservations_usd"] = reserved_total
    out["unlinked_receipts_usd"] = out["metered"]["usd"]
    out["usd"] = reserved_total + out["metered"]["usd"]
    return out


def recover_service_spend(connection: sqlite3.Connection, accounting: Mapping[str, Any], *,
                          now: datetime | str) -> dict[str, int]:
    """Write what ``service_spend_accounting`` found for each orphan, inside the
    caller's BEGIN IMMEDIATE transaction (the one that computed it, so no
    receipt was written between): reconcile it with its receipts, or release
    one with none. Each write is compare-and-set on a still-expired lease, so
    a renewal or the owner's own settlement wins."""

    stamp = ledger_stamp(now)
    expired = "state='in_flight' AND legacy=0 AND (lease_expires_at IS NULL OR lease_expires_at <= ?)"
    done = {"reconciled": 0, "released": 0}
    for entry in accounting.get("recovery") or ():
        if entry["action"] == "reconcile":
            cursor = connection.execute(
                f"UPDATE {SERVICE_SPEND_TABLE} SET state='settled', charged_usd=?, resolved_by='recovery', "
                f"lease_expires_at=NULL, updated_at=? WHERE id=? AND {expired}",
                (max(0.0, float(entry["charged_usd"])), stamp, entry["id"], stamp))
            done["reconciled"] += max(0, cursor.rowcount)
        else:
            cursor = connection.execute(
                f"UPDATE {SERVICE_SPEND_TABLE} SET state='released', charged_usd=0, resolved_by='recovery', "
                f"lease_expires_at=NULL, updated_at=? WHERE id=? AND {expired}",
                (stamp, entry["id"], stamp))
            done["released"] += max(0, cursor.rowcount)
    return done


def reserve_service_spend(connection: sqlite3.Connection, *, id: str, envelope: str, day: str, since: str,
                          usd: float, cap: float, process: str, now: datetime | str, lease_seconds: float,
                          price_per_million: float | None = None, subscription_providers: Collection[str] = (),
                          owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS) -> tuple[bool, float]:
    """Admit one request under the shared cap, inside the caller's BEGIN IMMEDIATE transaction.

    The day's total is ``service_spend_accounting``'s; orphans are recovered
    in the same transaction, and the request is admitted only when the total
    plus its estimate fits the cap. The reservation's lease runs
    ``lease_seconds`` (its owner renews it while it lives). Returns
    (admitted, the total before this request)."""

    accounting = service_spend_accounting(
        connection, envelope=envelope, day=day, since=since, now=now, price_per_million=price_per_million,
        subscription_providers=subscription_providers, owner_kinds=owner_kinds)
    recover_service_spend(connection, accounting, now=now)
    total = float(accounting["usd"])
    if total + float(usd) > float(cap) + _EPSILON:
        return False, total
    stamp = ledger_stamp(now)
    lease = ledger_stamp(_moment(stamp) + timedelta(seconds=float(lease_seconds)))
    connection.execute(
        f"INSERT INTO {SERVICE_SPEND_TABLE} (id, envelope, day, reserved_usd, charged_usd, state, legacy, process, "
        "lease_expires_at, resolved_by, created_at, updated_at) VALUES (?,?,?,?,?,'in_flight',0,?,?,NULL,?,?)",
        (id, envelope, day, float(usd), float(usd), process, lease, stamp, stamp))
    return True, total


def renew_service_spend_leases(connection: sqlite3.Connection, ids: Collection[str], *, process: str,
                               until: datetime | str) -> int:
    """The owner's heartbeat: extend its in-flight reservations' leases. A
    reservation recovery has resolved stays resolved."""

    stamp = ledger_stamp(until)
    renewed = 0
    ordered = sorted(ids)
    for start in range(0, len(ordered), 500):
        chunk = ordered[start:start + 500]
        cursor = connection.execute(
            f"UPDATE {SERVICE_SPEND_TABLE} SET lease_expires_at=? WHERE process=? AND state='in_flight' "
            f"AND id IN ({','.join('?' for _ in chunk)})", (stamp, process, *chunk))
        renewed += max(0, cursor.rowcount)
    return renewed


def _owned(process: str | None) -> tuple[str, tuple[str, ...]]:
    return (" AND process=?", (process,)) if process is not None else ("", ())


def charge_service_spend(connection: sqlite3.Connection, id: str, usd: float, now: datetime | str, *,
                         process: str | None = None) -> None:
    """Reconcile an in-flight reservation upward (usage above the estimate); never a refund."""

    if usd > 0:
        owned, params = _owned(process)
        connection.execute(
            f"UPDATE {SERVICE_SPEND_TABLE} SET charged_usd = charged_usd + ?, updated_at=? "
            f"WHERE id=? AND state='in_flight'{owned}", (float(usd), ledger_stamp(now), id, *params))


def settle_service_spend(connection: sqlite3.Connection, id: str, now: datetime | str,
                         actual_usd: float | None = None, *, process: str | None = None) -> None:
    """The owner's reconciliation: the request finished and counts its
    reported cost from now on, else its charge (at least its estimate).

    A reported cost applies to a reservation recovery already resolved too
    (an owner presumed dead that was only stalled): what the owner paid is
    the truth. Without one, a resolved reservation keeps recovery's
    resolution: its receipts already bound it, and a released one whose
    request was fenced out (``ReservationReleased``) was never sent."""

    owned, params = _owned(process)
    stamp = ledger_stamp(now)
    if actual_usd is None:
        connection.execute(
            f"UPDATE {SERVICE_SPEND_TABLE} SET state='settled', resolved_by='owner', lease_expires_at=NULL, "
            f"charged_usd=MAX(charged_usd, reserved_usd), updated_at=? WHERE id=? AND legacy=0 "
            f"AND state='in_flight'{owned}", (stamp, id, *params))
    else:
        connection.execute(
            f"UPDATE {SERVICE_SPEND_TABLE} SET state='settled', resolved_by='owner', lease_expires_at=NULL, "
            f"charged_usd=?, updated_at=? WHERE id=? AND legacy=0{owned}",
            (max(0.0, float(actual_usd)), stamp, id, *params))


class ReservationReleased(RuntimeError):
    """A request's shared reservation was released by recovery (its owner was
    presumed terminal): its receipt cannot start, so the request is never sent.

    The fence for recovery's release: the receipt's start and this check
    commit in one transaction, and recovery releases only a reservation no
    receipt names, so either the receipt started first (and recovery
    reconciles instead) or the release did (and the request is refused)."""

    #: A spend refusal raised below the AI layer, which ``SpendBudget.request``
    #: re-raises as ``SpendLimitExceeded`` (this layer cannot import it).
    spend_refused = True


def released_reservations(connection: sqlite3.Connection, budget_json: Any) -> list[str]:
    """The reservations a root receipt's declared budget names that recovery released."""

    try:
        declared = json.loads(budget_json or "{}") or {}
    except (TypeError, ValueError):
        return []
    refs = [str(ref) for ref in (declared.get(RESERVATIONS_KEY) or ()) if isinstance(ref, str)] \
        if isinstance(declared, dict) else []
    if not refs or not column_exists(connection, SERVICE_SPEND_TABLE, "resolved_by"):
        return []
    return [row[0] for row in connection.execute(
        f"SELECT id FROM {SERVICE_SPEND_TABLE} WHERE state='released' AND id IN ({','.join('?' for _ in refs)})",
        refs)]


def release_service_spend(connection: sqlite3.Connection, id: str, *, process: str | None = None) -> None:
    """Remove a reservation whose request was never sent (another cap refused it)."""

    owned, params = _owned(process)
    connection.execute(f"DELETE FROM {SERVICE_SPEND_TABLE} WHERE id=? AND state='in_flight'{owned}", (id, *params))


def spend_since(connection: sqlite3.Connection, since: str, *,
                owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS,
                price_per_million: float | None = None,
                subscription_providers: Collection[str] = ()) -> dict[str, Any]:
    """Spend of physical requests (leaf receipts) since ``since``, by their receipts alone.

    ``usd`` is METERED dollars, priced as the daily cap prices them: the
    provider's reported cost, exactly; else reported tokens at the rate the
    request recorded when it was admitted; else at ``price_per_million`` (the
    owner's service rate, the fallback). ``pricing`` counts each basis; a
    metered request with none is counted in ``metered.unpriced_requests``.
    Subscription (Codex, ChatGPT plan) requests have no marginal cost: their
    tokens (reported, else the receipt's own estimate) and owner-priced
    dollars are reported as ``estimated_only``, never capped. ``owner_kinds``
    None counts every receipt. A batch's report reads this; the daily cap
    reads ``service_spend_accounting``, which adds its reservations.
    """

    empty = {"usd": 0.0, "requests": 0, "requests_reporting_cost": 0,
             "metered": {"requests": 0, "usd": 0.0, "unpriced_requests": 0},
             "pricing": {basis: 0 for basis in PRICING_BASES},
             "estimated_only": {"requests": 0, "tokens": 0, "usd": 0.0 if price_per_million is not None else None}}
    if not table_exists(connection, "model_call_receipts"):
        return empty
    since = receipt_time_floor(since)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(model_call_receipts)")}
    usage = "r.usage_json" if "usage_json" in columns else "NULL"
    budget = "r.budget_json" if "budget_json" in columns else "NULL"
    sql = (f"SELECT r.id, r.parent_call_id, r.provider, r.cost, r.input_tokens, r.output_tokens, {usage}, {budget} "
           "FROM model_call_receipts r WHERE r.started_at >= ? AND NOT EXISTS "
           "(SELECT 1 FROM model_call_receipts c WHERE c.parent_call_id = r.id)")
    params: list[Any] = [since]
    if owner_kinds is not None:
        sql += f" AND r.owner_kind IN ({','.join('?' for _ in owner_kinds)})"
        params.extend(owner_kinds)
    out = json.loads(json.dumps(empty))
    cache: dict[str, str | None] = {}
    rate = None if price_per_million is None else float(price_per_million) / 1_000_000
    for _receipt_id, parent_id, provider, cost, input_tokens, output_tokens, usage_json, budget_json in \
            connection.execute(sql, params).fetchall():
        out["requests"] += 1
        tokens = int(input_tokens or 0) + int(output_tokens or 0)
        declared = _root_budget(connection, parent_id, budget_json, cache)
        if _receipt_billing(declared, provider, subscription_providers) == "subscription":
            used = _estimated_tokens(tokens, usage_json)
            out["estimated_only"]["requests"] += 1
            out["estimated_only"]["tokens"] += used
            if out["estimated_only"]["usd"] is not None:
                out["estimated_only"]["usd"] += used * rate if rate is not None else 0.0
            continue
        out["metered"]["requests"] += 1
        out["requests_reporting_cost"] += int(cost is not None)
        value, basis = _metered_cost(cost, tokens, _recorded_rate(declared), rate)
        out["pricing"][basis] += 1
        if value is None:
            out["metered"]["unpriced_requests"] += 1
            value = 0.0
        out["metered"]["usd"] += value
    out["usd"] = out["metered"]["usd"]
    return out


__all__ = [
    "comparison_row",
    "find_comparison",
    "insert_comparison",
    "SERVICE_OWNER_KINDS",
    "SERVICE_SPEND_TABLE",
    "PRICING_BASES",
    "RESERVATIONS_KEY",
    "ReservationReleased",
    "charge_service_spend",
    "ledger_stamp",
    "recover_service_spend",
    "release_service_spend",
    "released_reservations",
    "renew_service_spend_leases",
    "reserve_service_spend",
    "service_spend_accounting",
    "settle_service_spend",
    "spend_since",
    "receipt_time_floor",
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
    "exercise_key",
    "need_source_import",
    "serve_time_exposure",
    "key_checks_for_item",
    "reference_status_for_item",
    "REFERENCE_BINDING_TASK",
    "bind_replacement_grade",
    "update_import",
    "IMPRESSION_SURFACES",
    "column_exists",
    "impressions_for_proposal",
    "impressions_of_item",
    "impressions_of_spans",
    "insert_impression",
    "table_exists",
]
