"""Read-only dataset diagnostics over a consistent SQLite read transaction."""
from __future__ import annotations

from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Any

from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
from learnloop.outcome_contract import COLLECTION_VERSION, LABEL_VERSION, PFC_REVIEW_REASON, retention_exclusions


_ATTEMPT_COLUMNS = (
    "id", "practice_item_id", "session_id", "scheduler_slate_id", "scheduler_candidate_id", "submission_id",
    "correctness", "latency_seconds", "primed", "manual_review", "manual_review_reason", "collection_version",
    "entry_surface", "evidence_origin",
)
_CANDIDATE_COLUMNS = ("id", "slate_id", "practice_item_id", "was_returned", "chosen_attempt_id", "selection_propensity")


def table_names(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def rows(connection: sqlite3.Connection, table: str, *, columns: tuple[str, ...] | None = None, where: str = "") -> list[dict[str, Any]]:
    """Read a table as dicts, optionally narrowed to the named columns.

    Requested columns absent from an older schema are omitted from the dicts,
    so callers keep their `.get(..., default)` fallbacks. Table names and
    `where` clauses only come from SQLite's own catalog or constant callers.
    """
    if columns is None:
        selected = "*"
    else:
        present = {row[1] for row in connection.execute(f"PRAGMA table_info({_quote(table)})")}
        selected = ",".join(_quote(column) for column in columns if column in present)
    query = f"SELECT {selected} FROM {_quote(table)}"
    if where:
        query += f" WHERE {where}"
    return [dict(row) for row in connection.execute(query)]


def data_quality_report(sqlite_path: Path) -> dict[str, Any]:
    with closing(connect(sqlite_path, read_only=True)) as connection:
        connection.execute("BEGIN")
        return inspect_collection(connection)


def inspect_collection(connection: sqlite3.Connection, *, splits: dict[str, Any] | None = None) -> dict[str, Any]:
    """Coverage report over one connection.

    `splits` is the per-label count summary of a dataset export, named by its
    split policy; split assignment depends on export options, so a report
    produced outside an export carries no `splits` entry.
    """
    tables = table_names(connection)
    def read(table, columns=None, where=""):
        return rows(connection, table, columns=columns, where=where) if table in tables else []
    attempts = read("practice_attempts", _ATTEMPT_COLUMNS)
    # Only candidates an attempt links to can be checked, and the full table
    # carries a JSON component blob per candidate.
    candidates = {row["id"]: row for row in read("scheduler_slate_candidates", _CANDIDATE_COLUMNS, "id IN (SELECT scheduler_candidate_id FROM practice_attempts)")}
    slates = {row["id"]: row for row in read("scheduler_slates", ("id", "session_id"))}
    intents = {row["submission_id"]: row for row in read("submission_intents", ("submission_id", "scheduler_candidate_id"))}
    work = {row["attempt_id"]: row for row in read("attempt_completion_work", ("attempt_id", "status"))}
    grades = read("grading_evidence", ("attempt_id", "assessment_contract_version_id"))
    graded = {row["attempt_id"] for row in grades}
    contracts = {row["attempt_id"] for row in grades if row.get("assessment_contract_version_id")}
    cohorts: dict[tuple[str, str, str], Counter] = {}
    for attempt in attempts:
        version = attempt.get("collection_version", "legacy-unversioned")
        cohort = cohorts.setdefault((version, attempt.get("entry_surface", "unknown"), attempt.get("evidence_origin", "unknown")), Counter())
        cohort["attempts"] += 1
        scored = attempt.get("correctness") is not None
        cohort["scored_attempts"] += scored
        cohort["scored_attempts_missing_grade_link"] += scored and attempt["id"] not in graded
        cohort["duration_observed"] += attempt.get("latency_seconds") is not None
        cohort["grading_evidence_observed"] += attempt["id"] in graded
        cohort["assessment_contract_observed"] += attempt["id"] in contracts
        candidate = candidates.get(attempt.get("scheduler_candidate_id"))
        intent = intents.get(attempt.get("submission_id"))
        offered = bool(intent and intent.get("scheduler_candidate_id"))
        cohort["explicit_offer_intents"] += offered
        if candidate:
            slate = slates.get(candidate["slate_id"], {})
            exact = (candidate["practice_item_id"] == attempt["practice_item_id"] and candidate["slate_id"] == attempt.get("scheduler_slate_id") and slate.get("session_id") == attempt.get("session_id") and candidate.get("was_returned") == 1 and candidate.get("chosen_attempt_id") == attempt["id"])
            cohort["exact_offer_links"] += exact
            cohort["invalid_offer_links"] += not exact
            propensity = candidate.get("selection_propensity")
            cohort["chosen_propensity_observed"] += propensity is not None
            cohort["invalid_chosen_propensity"] += propensity is not None and not 0 < propensity <= 1
        elif offered:
            cohort["missing_explicit_offer_links"] += 1
        else:
            cohort["offer_not_captured_or_direct_selection"] += 1
        if version == COLLECTION_VERSION:
            completion = work.get(attempt["id"])
            cohort["completion_missing"] += completion is None
            cohort["completion_pending"] += bool(completion and completion["status"] != "completed")
    calls = []
    if "model_call_receipts" in tables:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(model_call_receipts)")}
        fields = "id,parent_call_id,collection_version,provider,model,purpose,status,input_tokens,output_tokens,cached_input_tokens,reasoning_tokens,cost,finished_at"
        fields += ",cache_write_tokens" if "cache_write_tokens" in columns else ",NULL AS cache_write_tokens"
        calls = [dict(row) for row in connection.execute(f"SELECT {fields} FROM model_call_receipts")]
    parents = {row["parent_call_id"] for row in calls if row["parent_call_id"]}
    call_cohorts: dict[tuple, Counter] = {}
    for call in calls:
        if call["id"] in parents:
            continue  # Physical request/SDK turn receipts own the numerator.
        key = (call["collection_version"], call["provider"], call["model"], call["purpose"])
        cohort = call_cohorts.setdefault(key, Counter())
        cohort["receipts"] += 1
        cohort[call["status"]] += 1
        for field in ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens", "reasoning_tokens", "cost"):
            cohort[f"{field}_observed"] += call[field] is not None
        cohort["duration_observed"] += call["finished_at"] is not None
    attempt_by_id = {row["id"]: row for row in attempts}
    # PF-c: the review reason is informational once the grade is over the
    # assessed criteria; whether any were assessed is read from the evidence.
    from learnloop.substrate.canonical_projection import pfc_assessments

    pfc_states = (
        pfc_assessments(
            connection,
            (row["id"] for row in attempts if row.get("manual_review_reason") == PFC_REVIEW_REASON),
        )
        if "grading_evidence" in tables
        else {}
    )
    label_rejections: Counter = Counter()
    eligible_labels = total_labels = 0
    for label in read("learning_outcome_labels"):
        if label["label_type"] != "same_item_retention":
            continue
        total_labels += 1
        outcome = attempt_by_id.get(label["outcome_attempt_id"], {})
        source = attempt_by_id.get(label["source_attempt_id"], {})
        label.update(metadata=json.loads(label["metadata_json"]), outcome_primed=outcome.get("primed"), outcome_manual_review=outcome.get("manual_review"), outcome_manual_review_reason=outcome.get("manual_review_reason"), outcome_pfc_assessment=pfc_states.get(label["outcome_attempt_id"]), source_session_id=source.get("session_id"), outcome_session_id=outcome.get("session_id"))
        exclusions = retention_exclusions(label)
        eligible_labels += not exclusions
        label_rejections.update(exclusions)
    opportunities = read("cold_measurement_opportunities")
    decisions = read("cold_measurement_opportunity_decisions")
    cold = read("coldness_receipts")
    decided = {row["measurement_opportunity_id"] for row in decisions}
    administered = {row.get("measurement_opportunity_id") for row in cold if row["stage"] == "administration"}
    finalized = {row.get("measurement_opportunity_id") for row in cold if row["stage"] == "final"}
    adjudicated_attempts = [row["attempt_id"] for row in read("false_remediation_adjudications", ("attempt_id",))]
    current = [dict(counts) for key, counts in cohorts.items() if key[0] == COLLECTION_VERSION]
    violations = {name: sum(cohort.get(name, 0) for cohort in current) for name in ("invalid_offer_links", "missing_explicit_offer_links", "invalid_chosen_propensity", "completion_missing")}
    report = {
        "report_version": 1, "collection_version": COLLECTION_VERSION, "label_version": LABEL_VERSION,
        "schema_versions": sorted(row["version"] for row in read("schema_migrations")),
        "false_remediation_adjudications": {"records": len(adjudicated_attempts), "attempts": len(set(adjudicated_attempts))},
        "generated_at": utc_now_iso(), "current_version_violations": violations,
        "attempt_cohorts": [dict(collection_version=key[0], entry_surface=key[1], evidence_origin=key[2], **dict(counts)) for key, counts in sorted(cohorts.items())],
        "model_call_cohorts": [dict(collection_version=key[0], provider=key[1], model=key[2], purpose=key[3], **dict(counts)) for key, counts in sorted(call_cohorts.items(), key=lambda entry: str(entry[0]))],
        "retention_labels": {"candidate_pairs": total_labels, "eligible_pairs": eligible_labels, "rejections": dict(label_rejections)},
        "cold_opportunities": {"opportunities": len(opportunities), "decided": sum(row["id"] in decided for row in opportunities), "administered": sum(row["id"] in administered for row in opportunities), "finalized": sum(row["id"] in finalized for row in opportunities), "decisions": dict(Counter(row["decision"] for row in decisions))},
        "cold_terminal_dispositions": dict(Counter(row["outcome"] for row in read("causal_cold_outcomes"))),
        "scope": {"current_version_only_alerts": True, "missing_measurements_are_zero": False, "viewing": "A draft or delivery receipt does not establish learner attention.", "retention": "Delayed unassisted observational retention; coldness requires a separate qualified receipt.", "legacy_provider_usage": "Agent-run zero counters do not establish zero cost."},
    }
    if splits is not None:
        report["splits"] = splits
    return report
