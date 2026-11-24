"""Migration 269 (pen and ink, fix round): `ink_transcriptions`' replacing-INSERT guard refuses an insert meeting either
key (the primary key, or the owner and strokes), so a reading's receipt cannot be replaced; nothing else changes. The
number is the file name alone (``MIGRATION``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.reader_rd8a_migration_helpers import GUARD_267, undo_269

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "ink_transcriptions_guard")
_READING = ("INSERT{verb} INTO ink_transcriptions(transcription_id, owner_kind, owner_id, content_hash, latex_md, "
            "confidence_label, task, prompt_version, created_at) VALUES (?, 'block', 'blk_1', 'h', ?, 'may_be_wrong', "
            "'ink_transcription', 'v', 't')")


def _copy(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    return database


def test_it_changes_the_guard_alone_and_keeps_every_row(tmp_path):
    database = _copy(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        undo_269(connection)
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.execute(_READING.format(verb=""), ("it_1", "kept"))
        connection.commit()
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    assert GUARD_267 in before["ink_transcriptions_no_replace"]
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT transcription_id, latex_md FROM ink_transcriptions").fetchall() == [("it_1", "kept")]
    assert set(after) == set(before)
    assert {name for name in before if before[name] != after[name]} == {"ink_transcriptions_no_replace"}
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        assert after == {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}


@pytest.mark.parametrize("verb", ["", " OR REPLACE"])
def test_neither_key_can_be_met_again(tmp_path, verb):
    with closing(sqlite3.connect(_copy(tmp_path), isolation_level=None)) as connection:
        connection.execute(_READING.format(verb=""), ("it_1", "kept"))
        for transcription_id in ("it_1", "it_2"):  # the same id, or a fresh one with the same owner and strokes
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(_READING.format(verb=verb), (transcription_id, "forged"))
        assert connection.execute("SELECT transcription_id, latex_md FROM ink_transcriptions").fetchall() == [("it_1", "kept")]
