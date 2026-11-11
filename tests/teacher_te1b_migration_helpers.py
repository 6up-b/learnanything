"""What other test files use from ``tests/test_teacher_te1b_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.teacher_te1_migration_helpers import TE1_ADDED_OBJECTS, TE1_ALTERED_TABLES


TE1B_ADDED_OBJECTS = frozenset({
    "router_suggestion_responses", "idx_router_suggestion_responses_at",
    "router_suggestion_responses_no_update", "router_suggestion_responses_no_delete",
    "sqlite_autoindex_router_suggestion_responses_1",
    # One learner response per decision, and at most one release of a Start's reservation (landing ruling R2).
    "idx_router_suggestion_responses_one_response", "idx_router_suggestion_responses_one_release",
})
#: 236 rebuilds this table (its decision_kind CHECK gains 'lesson_suggestion'); its objects keep their names.
TE1B_ALTERED_TABLES = frozenset({"router_decisions"})
#: What TE1's 234 and TE1b's 236 add and alter on the way to head (the earlier diffs compose these).
TE1_AND_TE1B_ADDED_OBJECTS = TE1_ADDED_OBJECTS | TE1B_ADDED_OBJECTS
TE1_AND_TE1B_ALTERED_TABLES = TE1_ALTERED_TABLES | TE1B_ALTERED_TABLES
#: RO0's 243 adds columns to three older tables (decision_measurement_events is younger than every diff using this), and
#: replaces plan_presentations' update guard with one that allows RO0's fill (landing ruling R1).
TE1_AND_TE1B_ALTERED_TABLES = TE1_AND_TE1B_ALTERED_TABLES | frozenset({
    "question_events", "plan_presentations", "source_exposure_events", "plan_presentations_no_update"})
#: RO1's 244 adds columns to practice_attempts and derived_state_rebuilds (tests/test_ro1_availability.py's
#: RO1_ALTERED_TABLES), and alters nothing else.
TE1_AND_TE1B_ALTERED_TABLES = TE1_AND_TE1B_ALTERED_TABLES | frozenset({"practice_attempts", "derived_state_rebuilds"})
#: Router objective RO4's 246 rebuilds goal_contract_versions (its change class gains 'use_weight_change',
#: tests/test_ro4_traces_migration.py's RO4_ALTERED_TABLE); its indexes keep their names and SQL.
TE1_AND_TE1B_ALTERED_TABLES = TE1_AND_TE1B_ALTERED_TABLES | frozenset({"goal_contract_versions"})
