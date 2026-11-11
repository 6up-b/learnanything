"""What other test files use from ``tests/test_teacher_te2_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


REBUILT = ("followup_generation_jobs", "generated_probe_items", "learner_text_gaps", "learner_text_gap_jobs")
#: What 248 alters (earlier migrations' "nothing else changed" diffs on the way to head read this): the four rebuilt
#: tables, lesson_episodes (its new column) and its close-once trigger. It adds no object.
TE2_ALTERED_TABLES = frozenset({*REBUILT, "lesson_episodes", "lesson_episodes_close_once"})
