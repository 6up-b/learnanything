"""Schema facts the code states as constants (refactor step F1).

A reader that used to ask the database whether a column exists now names it. What stays a stated fact (which of the
history card's tables carry ``received_at``) is pinned to the migrated schema here, so a migration that changes it
fails this test instead of silently changing a read.
"""

from __future__ import annotations

from contextlib import closing

from learnloop.adaptive_difficulty import history_card
from learnloop.db.connection import connect

from tests.helpers import create_basic_vault

_READ_BY_THE_CARD = ("practice_attempts", "interaction_events", "question_events", "reader_session_digests",
                     "learner_text_gaps", "reader_authored_questions", "source_exposure_events")


def test_the_history_cards_received_at_tables_are_the_migrated_schemas(tmp_path):
    paths = create_basic_vault(tmp_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        carrying = {
            table for table in _READ_BY_THE_CARD
            if any(column[1] == "received_at" for column in connection.execute(f'PRAGMA table_info("{table}")'))
        }
    assert carrying == set(history_card._RECEIVED_AT_TABLES)
    for table in _READ_BY_THE_CARD:
        expected = "COALESCE(received_at, created_at)" if table in carrying else "created_at"
        assert history_card.available_sql(table) == expected
