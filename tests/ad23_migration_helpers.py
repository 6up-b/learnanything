"""What other test files use from ``tests/test_ad23_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


NEW_TABLES = {"ad_selections", "ad_commission_results", "ad_dose_offers", "ad_relatedness_runs",
              "ad_coupling_versions", "ad_state", "ad_attempt_trace", "item_forecast_scores"}
#: What 214 adds (the earlier migrations' "nothing else changed" diffs on the way to head read it).
AD23_ADDED_OBJECTS = frozenset(NEW_TABLES | {
    "ad_selections_no_update", "ad_selections_no_delete", "idx_ad_selections_cell", "idx_ad_selections_block",
    "ad_commission_results_no_update", "ad_commission_results_no_delete",
    "ad_dose_offers_no_update", "ad_dose_offers_no_delete", "idx_ad_dose_offers_draw", "idx_ad_dose_offers_created",
    "ad_relatedness_runs_no_update", "ad_relatedness_runs_no_delete", "idx_ad_relatedness_runs_subject",
    "ad_coupling_versions_no_update", "ad_coupling_versions_no_delete",
    "sqlite_autoindex_ad_selections_1", "sqlite_autoindex_ad_selections_2",
    "sqlite_autoindex_ad_commission_results_1", "sqlite_autoindex_ad_commission_results_2",
    "sqlite_autoindex_ad_dose_offers_1", "sqlite_autoindex_ad_dose_offers_2",
    "sqlite_autoindex_ad_relatedness_runs_1", "sqlite_autoindex_ad_relatedness_runs_2",
    "sqlite_autoindex_ad_coupling_versions_1", "sqlite_autoindex_ad_coupling_versions_2",
    "sqlite_autoindex_ad_state_1", "sqlite_autoindex_ad_attempt_trace_1", "sqlite_autoindex_item_forecast_scores_1",
})
