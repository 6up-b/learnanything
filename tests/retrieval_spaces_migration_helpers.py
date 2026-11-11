"""What other test files use from ``tests/test_retrieval_spaces_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: Every schema object 220 adds: the earlier migrations' "nothing else" diffs on the way to head read this.
P1_ADDED_OBJECTS = frozenset({
    "embedding_spaces", "sqlite_autoindex_embedding_spaces_1",
    "retrieval_feedback", "sqlite_autoindex_retrieval_feedback_1", "retrieval_feedback_receipt",
    "retrieval_feedback_owner", "retrieval_feedback_no_update", "retrieval_feedback_no_delete",
    "retrieval_fusion_posteriors", "sqlite_autoindex_retrieval_fusion_posteriors_1",
})
