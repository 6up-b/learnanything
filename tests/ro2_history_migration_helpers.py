"""What other test files use from ``tests/test_ro2_history_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLE = "ad_history_forecast_draws"
#: What 245 adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
RO2_ADDED_OBJECTS = frozenset({
    TABLE, "idx_ad_history_forecast_draws_presentation", f"{TABLE}_no_update", f"{TABLE}_no_delete",
    f"sqlite_autoindex_{TABLE}_1", f"sqlite_autoindex_{TABLE}_2",
})
