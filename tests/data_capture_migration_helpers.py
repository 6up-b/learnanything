"""What other test files use from ``tests/test_data_capture_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


TABLES = ("prefilter_payloads", "prefilter_receipts", "decision_objectives", "decision_measurement_events",
          "reading_exposure_receipts")
#: What 240 adds (its tables, autoindexes, indexes and triggers).
DATA_CAPTURE_ADDED_OBJECTS = frozenset({
    *TABLES,
    "sqlite_autoindex_prefilter_payloads_1",
    "sqlite_autoindex_prefilter_receipts_1", "sqlite_autoindex_prefilter_receipts_2",
    "sqlite_autoindex_decision_objectives_1",
    "sqlite_autoindex_decision_measurement_events_1", "sqlite_autoindex_decision_measurement_events_2",
    "prefilter_receipts_created", "decision_objectives_lo", "decision_objectives_commitment",
    "decision_measurement_events_decision",
    "sqlite_autoindex_reading_exposure_receipts_1", "sqlite_autoindex_reading_exposure_receipts_2",
    "reading_exposure_receipts_source_time",
    *(f"{table}_no_{verb}" for table in TABLES for verb in ("update", "delete")),
})
