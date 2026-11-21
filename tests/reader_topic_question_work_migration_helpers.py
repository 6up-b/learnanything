"""What earlier migrations' upgrade diffs use from the topic-work migration (``tests/test_reader_topic_question_work_migration.py``),
kept here because a test file never imports another (``tests/test_test_layout.py``)."""

from __future__ import annotations


TOPIC_WORK = "reader_topic_question_work"
OBJECTS = frozenset({
    TOPIC_WORK, "idx_reader_topic_question_work_section", "idx_reader_topic_question_work_source",
    "idx_reader_topic_question_work_batch",
})
#: What the migration adds (with the table's autoindexes: its primary key and its one claim per topic): earlier
#: migrations' "nothing else changed" diffs on the way to head read this.
TOPIC_WORK_ADDED_OBJECTS = OBJECTS | {f"sqlite_autoindex_{TOPIC_WORK}_1", f"sqlite_autoindex_{TOPIC_WORK}_2"}
