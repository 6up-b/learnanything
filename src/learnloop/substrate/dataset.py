"""Reproducible local datasets from SQLite backups, never a live projection."""
from __future__ import annotations

from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.outcome_contract import COLLECTION_VERSION, LABEL_VERSION, retention_exclusions
from learnloop.substrate.data_quality import inspect_collection, rows, table_names


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _hash_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _lineage_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, list):
        for entry in value:
            keys.update(_lineage_keys(entry))
    elif isinstance(value, dict):
        for key, entry in value.items():
            if key in {"surface_family", "family_id", "template_id", "source_id", "source_revision_id", "canonical_uri", "asset_hash"} and isinstance(entry, str) and entry:
                keys.add(f"{key}:{entry}")
            if key == "source_refs" and isinstance(entry, list):
                for reference in entry:
                    if isinstance(reference, dict) and reference.get("path"):
                        keys.add(f"source_path:{str(reference['path']).split('#')[0]}")
            keys.update(_lineage_keys(entry))
    return keys


def split_assignments(attempts: list[dict[str, Any]], contracts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Quarantine groups crossing chronological boundaries; never split a family.

    Unknown origins/provenance remain exported but are ineligible for training.
    This can leave a small n=1 dataset without an evaluable holdout, honestly.
    """
    parents: dict[str, str] = {}
    def find(key):
        parents.setdefault(key, key)
        if parents[key] != key:
            parents[key] = find(parents[key])
        return parents[key]
    def union(left, right):
        a, b = find(left), find(right)
        parents[max(a, b)] = min(a, b)
    lineage_by_item: dict[str, set[str]] = defaultdict(set)
    for contract in contracts:
        lineage_by_item[contract["practice_item_id"]].update(_lineage_keys(json.loads(contract["contract_json"])))
    for attempt in attempts:
        item = f"item:{attempt['practice_item_id']}"
        union(item, f"lo:{attempt['learning_object_id']}")
        for key in lineage_by_item[attempt["practice_item_id"]]:
            union(item, key)
    # Equal timestamps always share a bucket; an ID tie-break cannot manufacture
    # a chronological holdout from a batch recorded at one instant.
    times = sorted({_timestamp(attempt["created_at"]) for attempt in attempts if attempt.get("evidence_origin") == "human"})
    first = times[min(len(times) - 1, int(len(times) * 0.7))] if times else None
    second = times[min(len(times) - 1, int(len(times) * 0.85))] if times else None
    assignments = []
    buckets: dict[str, set[str]] = defaultdict(set)
    for attempt in sorted(attempts, key=lambda row: (_timestamp(row["created_at"]), row["id"])):
        group = hashlib.sha256(find(f"item:{attempt['practice_item_id']}").encode()).hexdigest()
        when = _timestamp(attempt["created_at"])
        chronological = "train" if first and when < first else "validation" if second and when < second else "test"
        buckets[group].add(chronological)
        assignments.append({"attempt_id": attempt["id"], "group_hash": group, "chronological_split": chronological, "evidence_origin": attempt.get("evidence_origin", "unknown"), "source_family_provenance": bool(lineage_by_item[attempt["practice_item_id"]])})
    for row in assignments:
        row["split"] = "unavailable_origin" if row["evidence_origin"] != "human" else "unavailable_provenance" if not row["source_family_provenance"] else "quarantined_boundary_overlap" if len(buckets[row["group_hash"]]) > 1 else row["chronological_split"]
    return assignments


def outcome_records(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    tables = table_names(connection)
    def read(table):
        return rows(connection, table) if table in tables else []
    attempts = read("practice_attempts")
    by_id = {row["id"]: row for row in attempts}
    by_lo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for attempt in attempts:
        by_lo[attempt["learning_object_id"]].append(attempt)
    cold_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    opportunities_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for opportunity in read("cold_measurement_opportunities"):
        opportunities_by_source[opportunity["source_attempt_id"]].append(opportunity)
    decisions = {row["measurement_opportunity_id"]: row for row in read("cold_measurement_opportunity_decisions")}
    terminal_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for terminal in read("causal_cold_outcomes"):
        terminal_by_source[terminal.get("source_attempt_id")].append(terminal)
    for receipt in read("coldness_receipts"):
        if receipt["stage"] == "final":
            cold_by_source[receipt["source_attempt_id"]].append(receipt)
    questions: dict[str, int] = defaultdict(int)
    adjudications = {}
    for row in sorted(read("false_remediation_adjudications"), key=lambda row: (row["created_at"], row["id"])):
        adjudications[row["attempt_id"]] = row
    for question in read("question_events"):
        if question.get("attempt_id"):
            questions[question["attempt_id"]] += 1
    records = []
    for history in by_lo.values():
        history.sort(key=lambda row: (_timestamp(row["created_at"]), row["id"]))
        for index, source in enumerate(history):
            future = history[index + 1] if index + 1 < len(history) else None
            elapsed = int((datetime.fromisoformat(future["created_at"].replace("Z", "+00:00")) - datetime.fromisoformat(source["created_at"].replace("Z", "+00:00"))).total_seconds()) if future else None
            pair = {"label_value": future.get("correctness") if future else None, "elapsed_seconds": elapsed, "outcome_hints_used": future.get("hints_used") if future else None, "outcome_primed": future.get("primed") if future else None, "outcome_manual_review": future.get("manual_review") if future else None, "source_session_id": source.get("session_id"), "outcome_session_id": future.get("session_id") if future else None, "intervening_attempt_count": 0}
            cold_records = []
            for receipt in cold_by_source[source["id"]]:
                derived = json.loads(receipt["derived_json"])
                observed = by_id.get(receipt.get("cold_attempt_id"), {})
                qualified = derived.get("qualifies_as_cold_retrieval") is True
                cold_records.append({"receipt_id": receipt["id"], "status": "observed" if qualified and observed.get("correctness") is not None else derived.get("outcome") or "unqualified", "value": observed.get("correctness") if qualified else None, "qualifications": derived})
            finalized_opportunities = {receipt.get("measurement_opportunity_id") for receipt in cold_by_source[source["id"]]}
            terminal_tasks = {row["followup_task_id"] for row in terminal_by_source[source["id"]] if row["followup_task_id"]}
            for terminal in terminal_by_source[source["id"]]:
                cold_records.append({"causal_outcome_id": terminal["id"], "followup_task_id": terminal["followup_task_id"], "status": terminal["outcome"], "value": None, "verification_id": terminal["cold_verification_id"], "label_kind": "repair_disposition"})
            for opportunity in opportunities_by_source[source["id"]]:
                if opportunity["id"] in finalized_opportunities:
                    continue
                decision = decisions.get(opportunity["id"])
                if decision and decision.get("followup_task_id") in terminal_tasks:
                    continue
                status = "pending" if decision is None or decision["decision"] == "scheduled" else decision["decision"]
                cold_records.append({"opportunity_id": opportunity["id"], "status": status, "value": None, "reason": decision.get("reason") if decision else None})
            records.append({
                "source_attempt_id": source["id"], "submission_id": source.get("submission_id"), "scheduler_candidate_id": source.get("scheduler_candidate_id"), "session_id": source.get("session_id"),
                "collection_version": source.get("collection_version", "legacy-unversioned"), "label_version": LABEL_VERSION, "evidence_origin": source.get("evidence_origin", "unknown"),
                "R_next": {"status": "pending" if future is None else "observed" if future.get("correctness") is not None else "unscorable", "outcome_attempt_id": future["id"] if future else None, "value": future.get("correctness") if future else None, "elapsed_seconds": elapsed, "same_item": source["practice_item_id"] == future["practice_item_id"] if future else None, "retention_exclusions": (retention_exclusions(pair) + (["non_human_outcome"] if future.get("evidence_origin") != "human" else [])) if future else [], "outcome_origin": future.get("evidence_origin", "unknown") if future else None},
                "R_cold": cold_records or [{"status": "unavailable", "value": None, "reason": "no_measurement_opportunity"}],
                "Q": {"value": questions.get(source["id"]), "status": "observed_linked_questions" if source["id"] in questions else "unavailable"},
                "B": {"attempt_latency_seconds": source.get("latency_seconds"), "total_burden_seconds": None, "status": "partial" if source.get("latency_seconds") is not None else "unavailable"},
                "F": {"value": bool(adjudications[source["id"]]["label_value"]), "status": "adjudicated", "adjudication_id": adjudications[source["id"]]["id"], "author_kind": adjudications[source["id"]]["author_kind"], "verifier_version": adjudications[source["id"]]["verifier_version"]} if source["id"] in adjudications else {"value": None, "status": "unavailable", "reason": "No evidence-backed false-remediation adjudication is recorded for this attempt."},
            })
    return sorted(records, key=lambda row: row["source_attempt_id"])


def export_dataset(sqlite_path: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / "snapshot.sqlite"
    started = datetime.now(timezone.utc).isoformat()
    with closing(connect(sqlite_path, read_only=True)) as source, closing(sqlite3.connect(snapshot)) as destination:
        source.backup(destination, pages=256, sleep=0.05)
    artifacts: dict[str, Any] = {}
    def export_rows(name, values):
        target = output / f"{name}.jsonl"
        count = 0
        with target.open("w", encoding="utf-8") as handle:
            for value in values:
                handle.write(_json(value) + "\n")
                count += 1
        artifacts[target.name] = {"rows": count, "sha256": _hash_file(target)}
    with closing(connect(snapshot, read_only=True)) as connection:
        tables = table_names(connection)
        captured_workflows = {"proposed_patches", "proposed_patch_items", "synthesis_runs", "unit_inventories", "model_work_checkpoints", "ingest_batches", "ingest_jobs", "attempt_completion_work"}
        included = sorted(table for table in tables if TABLE_ROLES.get(table) in {TableRole.RAW_LEDGER, TableRole.RECEIPT} or table in captured_workflows)
        for table in included:
            escaped = table.replace('"', '""')
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")')]
            # Stream source/receipt payloads rather than loading a whole table.
            order = '"id"' if "id" in columns else ",".join('"' + key.replace('"', '""') + '"' for key in columns)
            export_rows(table, (dict(row) for row in connection.execute(f'SELECT * FROM "{escaped}" ORDER BY {order}')))
        export_rows("outcome_contract", outcome_records(connection))
        export_rows("split_assignments", split_assignments(rows(connection, "practice_attempts"), rows(connection, "assessment_contract_versions")))
        quality = inspect_collection(connection)
        schema = [dict(row) for row in connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name")]
        versions = sorted(rows(connection, "schema_migrations"), key=lambda row: row["version"]) if "schema_migrations" in tables else []
        asset_hashes = sorted({row[0] for row in connection.execute("SELECT DISTINCT asset_hash FROM source_revisions")}) if "source_revisions" in tables else []
    manifest = {
        "dataset_version": 1, "collection_version": COLLECTION_VERSION, "label_version": LABEL_VERSION,
        "label_code_sha256": {"dataset.py": _hash_file(Path(__file__)), "outcome_contract.py": _hash_file(Path(__file__).parents[1] / "outcome_contract.py")},
        "snapshot_started_at": started, "snapshot_completed_at": datetime.now(timezone.utc).isoformat(),
        "cutoff": "The atomic SQLite backup snapshot; timestamps are retained verbatim.",
        "snapshot_sha256": _hash_file(snapshot), "schema_sha256": hashlib.sha256(_json(schema).encode()).hexdigest(), "schema_migrations": versions,
        "artifacts": artifacts, "source_asset_hashes": asset_hashes,
        "inclusion": {"tables": included, "rejected_and_failed_candidates": True, "projection_tables_are_training_inputs": False, "source_assets": "Referenced by hash; not copied."},
        "splits": "70/15/15 chronological timestamp buckets; union item/LO/source/family groups; groups spanning boundaries are quarantined; unknown origin/provenance is ineligible.",
        "missingness": quality,
    }
    # A manifest is the completion marker. An interrupted export has none.
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest
