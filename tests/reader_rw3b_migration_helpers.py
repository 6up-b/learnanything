"""What other test files use from ``tests/test_reader_rw3b_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 215 adds: the earlier migrations' "nothing else changed" diffs on the
#: way to head read these.
RW3B_ADDED_OBJECTS = frozenset({
    "passage_links", "idx_passage_links_extraction", "idx_passage_links_target", "passage_links_no_update",
    "passage_links_no_delete", "reader_cue_impressions", "idx_reader_cue_impressions_link",
    "idx_reader_cue_impressions_created", "reader_cue_impressions_response_once", "reader_cue_impressions_no_delete",
    "sqlite_autoindex_passage_links_1", "sqlite_autoindex_passage_links_2",
    "sqlite_autoindex_reader_cue_impressions_1", "sqlite_autoindex_reader_cue_impressions_2",
})
