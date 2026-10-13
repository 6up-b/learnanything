"""SQL for the canonical-sources service (spec_source_practice_and_probes_v1).

Callers own transactions and pass a connection, as with ``practice_index``.
``db`` sits below every domain, so the attempt transaction, the tutor and the
remediation path can record and read here without importing the service
(SC12). Nothing here is evidence; the one DERIVED table (S5's outcome join)
is cleared and rebuilt only by its replayer.
"""
from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from datetime import datetime, timezone
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


def interventions(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not table_exists(connection, "retrieval_interventions"):
        return []
    rows = connection.execute("SELECT * FROM retrieval_interventions ORDER BY created_at, id").fetchall()
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


def _receipt_billing(connection: sqlite3.Connection, receipt_id: str, parent_id: str | None,
                     budget_json: str | None, provider: str | None, cache: dict[str, str | None],
                     subscription_providers: Collection[str]) -> str:
    """``subscription`` or ``metered``: the root receipt's declared budget says
    which (``billing``, ``practice_index.billing``, ``pf.cost_basis``); a root
    with no declared budget falls back to the provider's profile type."""

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


# -- the daily cap's shared reservations (migration 191; Codex re-review F2) ----------


SERVICE_SPEND_TABLE = "source_service_spend"


def service_spend_total(connection: sqlite3.Connection, envelope: str, day: str) -> float:
    """Dollars reserved or charged under ``envelope`` on ``day`` (every process)."""

    if not table_exists(connection, SERVICE_SPEND_TABLE):
        return 0.0
    row = connection.execute(
        "SELECT COALESCE(SUM(charged_usd), 0) FROM source_service_spend WHERE envelope=? AND day=?",
        (envelope, day)).fetchone()
    return float(row[0] or 0.0)


def reserve_service_spend(connection: sqlite3.Connection, *, id: str, envelope: str, day: str, usd: float,
                          cap: float, process: str, now: str, floor_usd: float = 0.0) -> tuple[bool, float]:
    """Admit one request under the shared cap, inside the caller's IMMEDIATE transaction.

    The day's total is the larger of the reservations recorded here and
    ``floor_usd`` (the service's own receipts, which also count spend made
    before this table existed). Returns (admitted, total before this request)."""

    total = max(service_spend_total(connection, envelope, day), float(floor_usd or 0.0))
    if total + float(usd) > float(cap) + 1e-12:
        return False, total
    connection.execute(
        "INSERT INTO source_service_spend (id, envelope, day, reserved_usd, charged_usd, state, process, "
        "created_at, updated_at) VALUES (?,?,?,?,?,'in_flight',?,?,?)",
        (id, envelope, day, float(usd), float(usd), process, now, now))
    return True, total


def charge_service_spend(connection: sqlite3.Connection, id: str, usd: float, now: str) -> None:
    """Reconcile a reservation upward (usage above the estimate); never a refund."""

    if usd > 0:
        connection.execute("UPDATE source_service_spend SET charged_usd = charged_usd + ?, updated_at=? WHERE id=?",
                           (float(usd), now, id))


def settle_service_spend(connection: sqlite3.Connection, id: str, now: str, actual_usd: float | None = None) -> None:
    """The request finished: it counts its reported cost from now on, else its reservation."""

    if actual_usd is None:
        connection.execute("UPDATE source_service_spend SET state='settled', updated_at=? WHERE id=?", (now, id))
    else:
        connection.execute("UPDATE source_service_spend SET state='settled', charged_usd=?, updated_at=? WHERE id=?",
                           (max(0.0, float(actual_usd)), now, id))


def release_service_spend(connection: sqlite3.Connection, id: str) -> None:
    """Remove a reservation whose request was never sent (another cap refused it)."""

    connection.execute("DELETE FROM source_service_spend WHERE id=? AND state='in_flight'", (id,))


def spend_since(connection: sqlite3.Connection, since: str, *,
                owner_kinds: Sequence[str] | None = SERVICE_OWNER_KINDS,
                price_per_million: float | None = None,
                subscription_providers: Collection[str] = ()) -> dict[str, Any]:
    """Spend of physical requests (leaf receipts) since ``since``.

    ``usd`` is METERED dollars, the basis of every money cap: the provider's
    reported cost, else reported tokens at ``price_per_million`` (the owner's
    single upper-bound rate); a metered request with neither is counted in
    ``metered.unpriced_requests``. Subscription (Codex, ChatGPT plan) requests
    have no marginal cost: their tokens (reported, else the receipt's own
    estimate) and owner-priced dollars are reported as ``estimated_only``,
    never capped. ``owner_kinds`` None counts every receipt.
    """

    empty = {"usd": 0.0, "requests": 0, "requests_reporting_cost": 0,
             "metered": {"requests": 0, "usd": 0.0, "unpriced_requests": 0},
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
    for receipt_id, parent_id, provider, cost, input_tokens, output_tokens, usage_json, budget_json in \
            connection.execute(sql, params).fetchall():
        out["requests"] += 1
        tokens = int(input_tokens or 0) + int(output_tokens or 0)
        billing = _receipt_billing(connection, receipt_id, parent_id, budget_json, provider, cache,
                                   subscription_providers)
        if billing == "subscription":
            out["estimated_only"]["requests"] += 1
            try:
                estimate = json.loads(usage_json or "{}") or {}
            except (TypeError, ValueError):
                estimate = {}
            used = tokens or int(estimate.get("estimated_total_tokens") or 0)
            out["estimated_only"]["tokens"] += used
            if out["estimated_only"]["usd"] is not None:
                out["estimated_only"]["usd"] += used * rate if rate is not None else 0.0
            continue
        out["metered"]["requests"] += 1
        if cost is not None:
            out["requests_reporting_cost"] += 1
            value = float(cost)
            if rate is not None and tokens:
                value = max(value, tokens * rate)
        elif rate is not None and tokens:
            value = tokens * rate
        else:
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
    "charge_service_spend",
    "release_service_spend",
    "reserve_service_spend",
    "service_spend_total",
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
