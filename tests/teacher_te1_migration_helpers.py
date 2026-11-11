"""What other test files use from ``tests/test_teacher_te1_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.table_roles import TableRole


TE1_TABLES = {
    "lessons": TableRole.RAW_LEDGER, "lesson_turns": TableRole.RAW_LEDGER, "lesson_plans": TableRole.RAW_LEDGER,
    "lesson_turn_payloads": TableRole.WORKFLOW, "lesson_checks": TableRole.RECEIPT,
    "lesson_receipts": TableRole.RECEIPT, "lesson_weight_state": TableRole.DERIVED,
    "lesson_weight_trace": TableRole.DERIVED, "confidence_calibration_state": TableRole.DERIVED,
}
TE1_ADDED_OBJECTS = frozenset({
    *TE1_TABLES,
    "idx_lesson_checks_lesson", "idx_lesson_checks_lo", "idx_lesson_turn_payloads_lesson",
    "idx_lesson_weight_trace_check", "idx_lessons_opened",
    "lesson_checks_no_delete", "lesson_checks_no_update", "lesson_plans_no_delete", "lesson_plans_no_update",
    "lesson_receipts_no_delete", "lesson_receipts_no_update", "lesson_turns_no_delete", "lesson_turns_no_update",
    "lessons_close_once", "lessons_no_delete",
    "sqlite_autoindex_confidence_calibration_state_1", "sqlite_autoindex_lesson_checks_1",
    "sqlite_autoindex_lesson_checks_2", "sqlite_autoindex_lesson_plans_1", "sqlite_autoindex_lesson_plans_2",
    "sqlite_autoindex_lesson_receipts_1", "sqlite_autoindex_lesson_turn_payloads_1",
    "sqlite_autoindex_lesson_turns_1", "sqlite_autoindex_lesson_turns_2", "sqlite_autoindex_lesson_weight_state_1",
    "sqlite_autoindex_lesson_weight_trace_1", "sqlite_autoindex_lesson_weight_trace_2", "sqlite_autoindex_lessons_1",
})
#: 234 rebuilds this table (its caller_kind CHECK gains 'teacher'); its objects keep their names.
TE1_ALTERED_TABLES = frozenset({"source_tool_calls"})
