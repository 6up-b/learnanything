"""What other test files use from ``tests/test_learner_note_source_kind_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: The objects 231 redefines (rebuilt in place, same names; it adds nothing): the earlier
#: migrations' "nothing else changed" diffs on the way to head read these.
C5_ALTERED_TABLES = frozenset({"learner_text_gaps", "learner_text_gap_jobs"})
