"""What other test files use from ``tests/test_teacher_te2log_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


EPISODES = "lesson_episodes"
INTERVALS = "lesson_activity_intervals"
#: What 247 adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
TE2LOG_ADDED_OBJECTS = frozenset({
    EPISODES, "idx_lesson_episodes_lesson", "idx_lesson_episodes_lo", f"{EPISODES}_close_once",
    f"{EPISODES}_no_delete", f"sqlite_autoindex_{EPISODES}_1", f"sqlite_autoindex_{EPISODES}_2",
    INTERVALS, "idx_lesson_activity_intervals_lesson", f"{INTERVALS}_no_update", f"{INTERVALS}_no_delete",
    f"sqlite_autoindex_{INTERVALS}_1", f"sqlite_autoindex_{INTERVALS}_2",
})
