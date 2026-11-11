"""What other test files use from ``tests/test_followup_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.table_roles import TableRole


ROLES = {
    "followup_workflows": TableRole.WORKFLOW,
    "followup_generation_jobs": TableRole.WORKFLOW,
    "followup_workflow_events": TableRole.RECEIPT,
    "generated_probe_items": TableRole.RAW_LEDGER,
    "generated_probe_burns": TableRole.RAW_LEDGER,
    "router_decision_bindings": TableRole.RECEIPT,
}
FOLLOWUP_ADDED_OBJECTS = frozenset({
    *ROLES,
    "followup_workflows_state", "followup_workflows_session", "followup_workflows_item",
    "followup_workflow_events_workflow", "followup_workflow_events_no_update", "followup_workflow_events_no_delete",
    "followup_generation_jobs_order", "generated_probe_items_workflow", "generated_probe_items_no_delete",
    "generated_probe_items_no_update", "generated_probe_burns_no_update", "generated_probe_burns_no_delete",
    "router_decision_bindings_item", "router_decision_bindings_no_update", "router_decision_bindings_no_delete",
    # Autoindexes of the UNIQUE constraints.
    "sqlite_autoindex_followup_workflows_1", "sqlite_autoindex_followup_workflows_2",
    "sqlite_autoindex_followup_workflow_events_1", "sqlite_autoindex_followup_generation_jobs_1",
    "sqlite_autoindex_followup_generation_jobs_2", "sqlite_autoindex_generated_probe_items_1",
    "sqlite_autoindex_generated_probe_burns_1", "sqlite_autoindex_generated_probe_burns_2",
    "sqlite_autoindex_router_decision_bindings_1", "sqlite_autoindex_router_decision_bindings_2",
})
