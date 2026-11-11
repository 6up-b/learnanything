"""What other test files use from ``tests/test_ad1_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 213 adds and alters: the earlier migrations' "nothing else changed"
#: diffs on the way to head read these (tests/test_approach_maps_schema.py,
#: test_help_assists_schema.py, test_library_asks_migration.py).
AD1_ADDED_OBJECTS = frozenset({
    "item_serve_inputs", "ad_reading_opportunities", "item_forecast_payloads",
    "idx_item_serve_inputs_item", "idx_item_serve_inputs_plan", "item_serve_inputs_no_update",
    "item_serve_inputs_no_delete", "idx_ad_reading_opportunities_lo", "idx_ad_reading_opportunities_written",
    "ad_reading_opportunities_no_update", "ad_reading_opportunities_no_delete", "idx_item_forecast_payloads_created",
})
#: ``question_events`` gains ``answered_at`` (Codex review F4) and ``answer_mode`` (fix round 4, V5).
AD1_ALTERED_TABLES = frozenset({"practice_attempts", "question_events"})
