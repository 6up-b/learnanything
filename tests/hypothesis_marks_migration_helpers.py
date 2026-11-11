"""What other test files use from ``tests/test_hypothesis_marks_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.table_roles import TableRole


ROLES = {
    "hypothesis_list_exposures": TableRole.RECEIPT,
    "hypothesis_exposure_probe_links": TableRole.RECEIPT,
    "hypothesis_marks": TableRole.RAW_LEDGER,
}
MARKS_ADDED_OBJECTS = frozenset({
    *ROLES,
    "hypothesis_list_exposures_attempt", "hypothesis_list_exposures_no_update", "hypothesis_list_exposures_no_delete",
    "hypothesis_exposure_probe_links_attempt", "hypothesis_exposure_probe_links_no_update",
    "hypothesis_exposure_probe_links_no_delete",
    "hypothesis_marks_attempt", "hypothesis_marks_learning_object", "hypothesis_marks_no_update", "hypothesis_marks_no_delete",
    # Autoindexes of the primary keys and the link's UNIQUE.
    "sqlite_autoindex_hypothesis_list_exposures_1", "sqlite_autoindex_hypothesis_exposure_probe_links_1",
    "sqlite_autoindex_hypothesis_exposure_probe_links_2", "sqlite_autoindex_hypothesis_marks_1",
})
