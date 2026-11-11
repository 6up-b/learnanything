"""What other test files use from ``tests/test_ro4_traces_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLE = "router_objective_traces"
#: What 246 adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
RO4_ADDED_OBJECTS = frozenset({
    TABLE, "idx_router_objective_traces_local_date", "idx_router_objective_traces_created", f"{TABLE}_no_update",
    f"{TABLE}_no_delete", f"sqlite_autoindex_{TABLE}_1", f"sqlite_autoindex_{TABLE}_2",
})
