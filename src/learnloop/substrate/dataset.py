"""Reproducible local datasets from SQLite backups, never a live projection."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.outcome_contract import COLLECTION_VERSION, LABEL_VERSION, retention_exclusions
from learnloop.substrate.data_quality import inspect_collection, rows, table_names

# Tables that are neither ledgers nor receipts but record captured workflow
# inputs a dataset consumer needs to interpret the evidence.
_CAPTURED_WORKFLOW_TABLES = frozenset({
    "proposed_patches",
    "proposed_patch_items",
    "synthesis_runs",
    "model_work_checkpoints",
    "ingest_batches",
    "ingest_jobs",
    "attempt_completion_work",
})

_SPLIT_ATTEMPT_COLUMNS = ("id", "practice_item_id", "learning_object_id", "created_at", "evidence_origin")
_SOURCE_LINK_ENTITY_TYPES = ("practice_item", "learning_object")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _hash_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


# --------------------------------------------------------------------------
# Splits
# --------------------------------------------------------------------------


def _contract_lineage(contract: dict[str, Any]) -> set[str]:
    """Content-lineage keys an assessment contract records.

    `surface_family` is deliberately absent: it names a presentation format
    (for example `verbal_option_recognition`) shared by unrelated content, so
    grouping on it would merge independent material into one family.
    """
    keys: set[str] = set()
    for recipe in contract.get("recipes") or []:
        blueprint = recipe.get("blueprint_id") if isinstance(recipe, dict) else None
        if isinstance(blueprint, str) and blueprint:
            keys.add(f"blueprint:{blueprint}")
    fingerprint = contract.get("evidence_fingerprint") or {}
    for field in ("source_family", "shared_stimulus_id"):
        value = fingerprint.get(field)
        if isinstance(value, str) and value:
            keys.add(f"{field}:{value}")
    return keys


def _source_link_lineage(link: dict[str, Any]) -> str | None:
    """A cited source span, qualified by its source so locators cannot collide."""
    if link.get("status") == "removed" or not link.get("locator"):
        return None
    source = link.get("source_id") or link.get("revision_id") or ""
    return f"source_span:{source}:{link['locator']}"


class _LineageGroups:
    """Union-find whose component root is the lexicographically smallest key.

    Linking the larger root under the smaller one makes each root independent
    of input order, so group hashes are deterministic.
    """

    def __init__(self) -> None:
        self._parents: dict[str, str] = {}

    def find(self, key: str) -> str:
        self._parents.setdefault(key, key)
        root = key
        while self._parents[root] != root:
            root = self._parents[root]
        while self._parents[key] != root:
            self._parents[key], key = root, self._parents[key]
        return root

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        self._parents[max(left_root, right_root)] = min(left_root, right_root)


def _chronological_cutoffs(times: list[datetime]) -> tuple[datetime | None, datetime | None]:
    """The 70% and 85% timestamps. Equal timestamps always share a bucket, so
    an ID tie-break cannot manufacture a holdout from a batch recorded at one instant."""
    distinct = sorted(set(times))
    if not distinct:
        return None, None
    last = len(distinct) - 1
    return distinct[min(last, int(len(distinct) * 0.7))], distinct[min(last, int(len(distinct) * 0.85))]


def _chronological_bucket(when: datetime, first: datetime | None, second: datetime | None) -> str:
    if first and when < first:
        return "train"
    if second and when < second:
        return "validation"
    return "test"


def _split_label(row: dict[str, Any], buckets: dict[str, set[str]]) -> str:
    if row["evidence_origin"] != "human":
        return "unavailable_origin"
    if not row["content_provenance"]:
        return "unavailable_provenance"
    if len(buckets[row["group_hash"]]) > 1:
        return "quarantined_boundary_overlap"
    return row["chronological_split"]


def split_assignments(
    attempts: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    source_links: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Assign attempts to chronological splits without splitting a content family.

    A family is the connected component of items, learning objects, authored
    blueprints, evidence-fingerprint source families or shared stimuli, and
    cited source spans. Only eligible attempts (human origin with content
    provenance) define the time cutoffs and the buckets a family occupies; a
    family whose eligible attempts span a cutoff is quarantined. Ineligible
    attempts stay in the export with an `unavailable_*` split. For one learner
    who revisits the same material over time this can leave no evaluable
    holdout, and the export says so rather than leaking a family across splits.
    """
    lineage_by_item: dict[str, set[str]] = defaultdict(set)
    for contract in contracts:
        lineage_by_item[contract["practice_item_id"]].update(_contract_lineage(json.loads(contract["contract_json"])))
    lineage_by_learning_object: dict[str, set[str]] = defaultdict(set)
    for link in source_links:
        key = _source_link_lineage(link)
        if key is None:
            continue
        if link["entity_type"] == "practice_item":
            lineage_by_item[link["entity_id"]].add(key)
        elif link["entity_type"] == "learning_object":
            lineage_by_learning_object[link["entity_id"]].add(key)

    groups = _LineageGroups()
    content_lineage: dict[str, set[str]] = {}
    for attempt in attempts:
        item_node = f"item:{attempt['practice_item_id']}"
        lineage = lineage_by_item[attempt["practice_item_id"]] | lineage_by_learning_object[attempt["learning_object_id"]]
        content_lineage[attempt["id"]] = lineage
        groups.union(item_node, f"lo:{attempt['learning_object_id']}")
        for key in lineage:
            groups.union(item_node, key)

    def eligible(attempt: dict[str, Any]) -> bool:
        return attempt.get("evidence_origin") == "human" and bool(content_lineage[attempt["id"]])

    first, second = _chronological_cutoffs([_timestamp(attempt["created_at"]) for attempt in attempts if eligible(attempt)])
    assignments = []
    buckets: dict[str, set[str]] = defaultdict(set)
    for attempt in sorted(attempts, key=lambda row: (_timestamp(row["created_at"]), row["id"])):
        group = hashlib.sha256(groups.find(f"item:{attempt['practice_item_id']}").encode()).hexdigest()
        chronological = _chronological_bucket(_timestamp(attempt["created_at"]), first, second)
        if eligible(attempt):
            buckets[group].add(chronological)
        assignments.append({
            "attempt_id": attempt["id"],
            "group_hash": group,
            "chronological_split": chronological,
            "evidence_origin": attempt.get("evidence_origin", "unknown"),
            "content_provenance": bool(content_lineage[attempt["id"]]),
        })
    for row in assignments:
        row["split"] = _split_label(row, buckets)
    return assignments


# --------------------------------------------------------------------------
# Outcome labels
# --------------------------------------------------------------------------


def _index_by(values: Iterable[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    index: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for value in values:
        index[value.get(key)].append(value)
    return index


def _cold_receipt_status(derived: dict[str, Any], observed: dict[str, Any]) -> str:
    """Label status of one final coldness receipt.

    A qualified, scored cold attempt is observed. Otherwise the receipt's own
    terminal disposition (`derived["outcome"]`, such as `cold_failure`,
    `indeterminate` or `right_censored_expired`) is the status. A receipt that
    records no disposition falls back to its qualification, so a qualified but
    unscored receipt reads as unscorable rather than unqualified.
    """
    qualified = derived.get("qualifies_as_cold_retrieval")
    if qualified is True and observed.get("correctness") is not None:
        return "observed"
    outcome = derived.get("outcome")
    if isinstance(outcome, str) and outcome:
        return outcome
    if qualified is True:
        return "unscorable"
    if qualified is False:
        return "unqualified"
    return "unknown"


def _r_next(source: dict[str, Any], future: dict[str, Any] | None) -> dict[str, Any]:
    if future is None:
        return {"status": "pending", "outcome_attempt_id": None, "value": None, "elapsed_seconds": None, "same_item": None, "retention_exclusions": [], "outcome_origin": None}
    elapsed = int((_timestamp(future["created_at"]) - _timestamp(source["created_at"])).total_seconds())
    pair = {
        "label_value": future.get("correctness"),
        "elapsed_seconds": elapsed,
        "outcome_hints_used": future.get("hints_used"),
        "outcome_primed": future.get("primed"),
        "outcome_manual_review": future.get("manual_review"),
        "source_session_id": source.get("session_id"),
        "outcome_session_id": future.get("session_id"),
        "intervening_attempt_count": 0,
    }
    exclusions = retention_exclusions(pair)
    if future.get("evidence_origin") != "human":
        exclusions = exclusions + ["non_human_outcome"]
    return {
        "status": "observed" if future.get("correctness") is not None else "unscorable",
        "outcome_attempt_id": future["id"],
        "value": future.get("correctness"),
        "elapsed_seconds": elapsed,
        "same_item": source["practice_item_id"] == future["practice_item_id"],
        "retention_exclusions": exclusions,
        "outcome_origin": future.get("evidence_origin", "unknown"),
    }


def _f_label(adjudication: dict[str, Any] | None) -> dict[str, Any]:
    if adjudication is None:
        return {"value": None, "status": "unavailable", "reason": "No evidence-backed false-remediation adjudication is recorded for this attempt."}
    return {
        "value": bool(adjudication["label_value"]),
        "status": "adjudicated",
        "adjudication_id": adjudication["id"],
        "author_kind": adjudication["author_kind"],
        "verifier_version": adjudication["verifier_version"],
    }


def outcome_records(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    tables = table_names(connection)

    def read(table: str) -> list[dict[str, Any]]:
        return rows(connection, table) if table in tables else []

    attempts = read("practice_attempts")
    attempt_by_id = {row["id"]: row for row in attempts}
    history_by_learning_object = _index_by(attempts, "learning_object_id")
    final_receipts_by_source = _index_by((row for row in read("coldness_receipts") if row["stage"] == "final"), "source_attempt_id")
    opportunities_by_source = _index_by(read("cold_measurement_opportunities"), "source_attempt_id")
    terminal_by_source = _index_by(read("causal_cold_outcomes"), "source_attempt_id")
    decisions = {row["measurement_opportunity_id"]: row for row in read("cold_measurement_opportunity_decisions")}
    question_counts: dict[str, int] = defaultdict(int)
    for question in read("question_events"):
        if question.get("attempt_id"):
            question_counts[question["attempt_id"]] += 1
    # Corrections append; the latest adjudication for an attempt wins.
    latest_adjudication = {}
    for row in sorted(read("false_remediation_adjudications"), key=lambda row: (row["created_at"], row["id"])):
        latest_adjudication[row["attempt_id"]] = row

    def cold_records(source_id: str) -> list[dict[str, Any]]:
        records = []
        final_receipts = final_receipts_by_source.get(source_id, [])
        for receipt in final_receipts:
            derived = json.loads(receipt["derived_json"])
            observed = attempt_by_id.get(receipt.get("cold_attempt_id"), {})
            qualified = derived.get("qualifies_as_cold_retrieval") is True
            records.append({
                "receipt_id": receipt["id"],
                "status": _cold_receipt_status(derived, observed),
                "value": observed.get("correctness") if qualified else None,
                "qualifications": derived,
            })
        terminals = terminal_by_source.get(source_id, [])
        for terminal in terminals:
            records.append({"causal_outcome_id": terminal["id"], "followup_task_id": terminal["followup_task_id"], "status": terminal["outcome"], "value": None, "verification_id": terminal["cold_verification_id"], "label_kind": "repair_disposition"})
        finalized_opportunities = {receipt.get("measurement_opportunity_id") for receipt in final_receipts}
        terminal_tasks = {terminal["followup_task_id"] for terminal in terminals if terminal["followup_task_id"]}
        for opportunity in opportunities_by_source.get(source_id, []):
            if opportunity["id"] in finalized_opportunities:
                continue
            decision = decisions.get(opportunity["id"])
            if decision and decision.get("followup_task_id") in terminal_tasks:
                continue
            status = "pending" if decision is None or decision["decision"] == "scheduled" else decision["decision"]
            records.append({"opportunity_id": opportunity["id"], "status": status, "value": None, "reason": decision.get("reason") if decision else None})
        return records or [{"status": "unavailable", "value": None, "reason": "no_measurement_opportunity"}]

    records = []
    for history in history_by_learning_object.values():
        history.sort(key=lambda row: (_timestamp(row["created_at"]), row["id"]))
        for index, source in enumerate(history):
            future = history[index + 1] if index + 1 < len(history) else None
            source_id = source["id"]
            records.append({
                "source_attempt_id": source_id,
                "submission_id": source.get("submission_id"),
                "scheduler_candidate_id": source.get("scheduler_candidate_id"),
                "session_id": source.get("session_id"),
                "collection_version": source.get("collection_version", "legacy-unversioned"),
                "label_version": LABEL_VERSION,
                "evidence_origin": source.get("evidence_origin", "unknown"),
                "R_next": _r_next(source, future),
                "R_cold": cold_records(source_id),
                "Q": {"value": question_counts.get(source_id), "status": "observed_linked_questions" if source_id in question_counts else "unavailable"},
                "B": {"attempt_latency_seconds": source.get("latency_seconds"), "total_burden_seconds": None, "status": "partial" if source.get("latency_seconds") is not None else "unavailable"},
                "F": _f_label(latest_adjudication.get(source_id)),
            })
    return sorted(records, key=lambda row: row["source_attempt_id"])


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------


def _write_jsonl(target: Path, values: Iterable[Any]) -> dict[str, Any]:
    """Write, hash and fsync one artifact in a single pass."""
    digest = hashlib.sha256()
    count = 0
    with target.open("wb") as handle:
        for value in values:
            line = (_json(value) + "\n").encode("utf-8")
            handle.write(line)
            digest.update(line)
            count += 1
        handle.flush()
        os.fsync(handle.fileno())
    return {"rows": count, "sha256": digest.hexdigest()}


def _write_manifest(output: Path, manifest: dict[str, Any]) -> None:
    """Publish the manifest atomically, after every artifact is durable.

    The manifest is the completion marker, so it appears under its final name
    only as a complete, fsynced file.
    """
    temporary = output / "manifest.json.tmp"
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, output / "manifest.json")
    _fsync_directory(output)


def _ordered_table_rows(connection: sqlite3.Connection, table: str) -> Iterable[dict[str, Any]]:
    """Stream a table in a stable order rather than loading it whole."""
    escaped = table.replace('"', '""')
    columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")')]
    order = '"id"' if "id" in columns else ",".join('"' + column.replace('"', '""') + '"' for column in columns)
    return (dict(row) for row in connection.execute(f'SELECT * FROM "{escaped}" ORDER BY {order}'))


def _split_source_links(connection: sqlite3.Connection, tables: set[str]) -> list[dict[str, Any]]:
    if "entity_source_links" not in tables:
        return []
    placeholders = ",".join("?" for _ in _SOURCE_LINK_ENTITY_TYPES)
    query = f"SELECT entity_type,entity_id,source_id,revision_id,locator,status FROM entity_source_links WHERE entity_type IN ({placeholders})"
    return [dict(row) for row in connection.execute(query, _SOURCE_LINK_ENTITY_TYPES)]


def _export_snapshot(snapshot: Path, output: Path) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}

    def export_rows(name: str, values: Iterable[Any]) -> None:
        target = output / f"{name}.jsonl"
        artifacts[target.name] = _write_jsonl(target, values)

    with closing(connect(snapshot, read_only=True)) as connection:
        tables = table_names(connection)
        included = sorted(table for table in tables if TABLE_ROLES.get(table) in {TableRole.RAW_LEDGER, TableRole.RECEIPT} or table in _CAPTURED_WORKFLOW_TABLES)
        for table in included:
            export_rows(table, _ordered_table_rows(connection, table))
        export_rows("outcome_contract", outcome_records(connection))
        attempts = rows(connection, "practice_attempts", columns=_SPLIT_ATTEMPT_COLUMNS)
        contracts = rows(connection, "assessment_contract_versions", columns=("practice_item_id", "contract_json")) if "assessment_contract_versions" in tables else []
        export_rows("split_assignments", split_assignments(attempts, contracts, _split_source_links(connection, tables)))
        quality = inspect_collection(connection)
        schema = [dict(row) for row in connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name")]
        versions = sorted(rows(connection, "schema_migrations"), key=lambda row: row["version"]) if "schema_migrations" in tables else []
        asset_hashes = sorted({row[0] for row in connection.execute("SELECT DISTINCT asset_hash FROM source_revisions")}) if "source_revisions" in tables else []
    return {
        "artifacts": artifacts,
        "included": included,
        "quality": quality,
        "schema_sha256": hashlib.sha256(_json(schema).encode()).hexdigest(),
        "schema_migrations": versions,
        "source_asset_hashes": asset_hashes,
    }


def export_dataset(sqlite_path: Path, output: Path) -> dict[str, Any]:
    """Back up `sqlite_path` into a new `output` directory and export from the copy.

    `manifest.json` is written last and atomically, so its presence marks a
    complete export. On any failure the partially written directory is removed.
    """
    output.mkdir(parents=True, exist_ok=False)
    try:
        return _export_into(sqlite_path, output)
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def _export_into(sqlite_path: Path, output: Path) -> dict[str, Any]:
    snapshot = output / "snapshot.sqlite"
    started = datetime.now(timezone.utc).isoformat()
    with closing(connect(sqlite_path, read_only=True)) as source, closing(sqlite3.connect(snapshot)) as destination:
        source.backup(destination, pages=256, sleep=0.05)
    exported = _export_snapshot(snapshot, output)
    _fsync_file(snapshot)
    manifest = {
        "dataset_version": 1,
        "collection_version": COLLECTION_VERSION,
        "label_version": LABEL_VERSION,
        "label_code_sha256": {"dataset.py": _hash_file(Path(__file__)), "outcome_contract.py": _hash_file(Path(__file__).parents[1] / "outcome_contract.py")},
        "snapshot_started_at": started,
        "snapshot_completed_at": datetime.now(timezone.utc).isoformat(),
        "cutoff": "The atomic SQLite backup snapshot; timestamps are retained verbatim.",
        "snapshot_sha256": _hash_file(snapshot),
        "schema_sha256": exported["schema_sha256"],
        "schema_migrations": exported["schema_migrations"],
        "artifacts": exported["artifacts"],
        "source_asset_hashes": exported["source_asset_hashes"],
        "inclusion": {"tables": exported["included"], "rejected_and_failed_candidates": True, "projection_tables_are_training_inputs": False, "source_assets": "Referenced by hash; not copied."},
        "splits": (
            "70/15/15 chronological timestamp buckets over eligible attempts (human origin with content provenance); "
            "families join items, learning objects, blueprints, fingerprint source families and shared stimuli, and cited source spans; "
            "a family spanning a boundary is quarantined; surface_family is a format label and never joins families."
        ),
        "missingness": exported["quality"],
    }
    _write_manifest(output, manifest)
    return manifest
