"""What earlier migrations' upgrade diffs use from the seen-passages migration (``tests/test_reader_seen_spans_migration.py``),
kept here because a test file never imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


SEEN_SPANS = "reader_seen_spans"
SECTION_ENDS = "reader_section_ends"
OBJECTS = frozenset({
    SEEN_SPANS, "idx_reader_seen_spans_section", "reader_seen_spans_no_update", "reader_seen_spans_no_delete",
    SECTION_ENDS, "reader_section_ends_no_update", "reader_section_ends_no_delete",
})
#: What the migration adds (with each table's own autoindex): earlier migrations' "nothing else changed" diffs on the
#: way to head read this.
SEEN_SPANS_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{SEEN_SPANS}_1", f"sqlite_autoindex_{SECTION_ENDS}_1"}
