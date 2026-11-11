"""What other test files use from ``tests/test_learner_notes_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 229 adds (it alters nothing): the earlier migrations' "nothing
#: else changed" diffs on the way to head read these.
C2_ADDED_OBJECTS = frozenset({
    "learner_notes", "sqlite_autoindex_learner_notes_1", "sqlite_autoindex_learner_notes_2",
    "idx_learner_notes_key", "learner_notes_no_update", "learner_notes_no_delete",
    "learner_note_links", "sqlite_autoindex_learner_note_links_1", "idx_learner_note_links_note",
    "idx_learner_note_links_lo", "idx_learner_note_links_reading", "learner_note_links_no_update",
    "learner_note_links_no_delete",
})
