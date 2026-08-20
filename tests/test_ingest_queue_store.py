from __future__ import annotations

import ast
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.db.stores.ingest_queue import IngestQueueStoreMixin


_QUEUE_TABLES = (
    "ingest_batches",
    "ingest_jobs",
    "ingest_job_dependencies",
)

_QUEUE_API = (
    "insert_ingest_batch",
    "get_ingest_batch",
    "list_ingest_batches",
    "update_ingest_batch_status",
    "request_ingest_batch_cancel",
    "clear_ingest_batch_cancel_requested",
    "insert_ingest_job",
    "add_ingest_job_dependency",
    "get_ingest_job",
    "ingest_jobs_for_batch",
    "ingest_jobs_for_batches",
    "ingest_job_dependency_ids",
    "ingest_job_dependencies_for_jobs",
    "ingest_job_dependents",
    "claim_next_ingest_job",
    "heartbeat_ingest_job",
    "finish_ingest_job",
    "requeue_ingest_job",
    "delete_finished_ingest_batches",
    "update_ingest_job_payload",
    "set_ingest_job_cancel_requested",
    "ingest_jobs_by_types",
    "active_ingest_jobs",
    "expired_running_ingest_jobs",
    "rung_variant_batch_dead",
    "concept_animation_batch_dead",
    "rung_variant_pending_source_ids",
)


def test_ingest_queue_sql_has_one_persistence_owner() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "db"
    repository_path = source_root / "repositories.py"
    store_path = source_root / "stores" / "ingest_queue.py"

    repository_source = repository_path.read_text(encoding="utf-8")
    repository_tree = ast.parse(repository_source)
    repository_literals = {
        node.value
        for node in ast.walk(repository_tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for table in _QUEUE_TABLES:
        assert table not in repository_source
        assert not any(table in literal for literal in repository_literals)

    store_source = store_path.read_text(encoding="utf-8")
    store_tree = ast.parse(store_source)
    store_literals = {
        node.value
        for node in ast.walk(store_tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for table in _QUEUE_TABLES:
        assert any(table in literal for literal in store_literals)

    sql_owners: set[Path] = set()
    package_root = source_root.parent
    for python_path in package_root.rglob("*.py"):
        tree = ast.parse(python_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            literal = " ".join(node.value.lower().split())
            if any(table in literal for table in _QUEUE_TABLES) and any(
                marker in literal
                for marker in ("select ", "insert ", "update ", "delete ", "join ")
            ):
                sql_owners.add(python_path)
    assert sql_owners == {store_path}


def test_repository_queue_api_is_composed_from_the_store() -> None:
    for method_name in _QUEUE_API:
        assert method_name not in Repository.__dict__
        assert getattr(Repository, method_name) is getattr(
            IngestQueueStoreMixin, method_name
        )
