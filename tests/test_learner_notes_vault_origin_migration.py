"""Curriculum C2b's migration 233 (spec_deliverable_curriculum_v1 §10 as built).

``learner_notes`` is rebuilt temp-then-rename under ``PRAGMA foreign_keys = OFF`` (the precedent
of 208, 212 and 231): ``origin`` gains ``vault``; ``path`` and ``line`` become nullable; the new
``vault_ref_kind`` (``annotation`` | ``capture``) and ``vault_ref_id`` carry a vault note's
reference, with CHECKs that a ``vault`` row has its reference and any other row its path and line.
Every C2-era row (``tend`` / ``pocket_notes``) survives with its id and values and stays readable;
``learner_note_links`` still resolves to the rebuilt table; the append-only triggers and the index
are back. No table is new; the head fixture holds 233. The durability lane runs it with
production pragmas (WAL, ``synchronous=FULL``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)
from learnloop.db.table_roles import TableRole, role_for_table

NOW = "2026-11-01T10:00:00Z"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_240" / "state.sqlite"
#: The objects 233 redefines (rebuilt in place, same name; it adds nothing).
C2B_ALTERED_TABLES = frozenset({"learner_notes"})


def _database_at_232(tmp_path: Path) -> Path:
    # RW5d P3's 232 landed first (233 kept its number at C2b's landing).
    through = tmp_path / "through_232"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 232:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 232
    return database


def _seed(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for index, origin in enumerate(("tend", "pocket_notes")):
            connection.execute(
                "INSERT INTO learner_notes (id, note_key, path, heading_path, line, content_hash, title, heading, "
                "captured_on, origin, text_md, truncated, created_at) VALUES "
                "(?, ?, ?, 'Eigen', 2, ?, 'Linear algebra', 'Eigen', '2026-10-03', ?, 'Av = lv', 0, ?)",
                (f"ln_{index}", f"/n/{index}.org#Eigen", f"/n/{index}.org", f"h{index}", origin, NOW))
        connection.execute(
            "INSERT INTO learner_note_links (id, note_id, note_key, target_kind, target_key, learning_object_id, "
            "extraction_id, section_id, span_id, goal_id, authorship, status, created_at) VALUES "
            "('nl_0', 'ln_0', '/n/0.org#Eigen', 'passage', 'passage:ext/sec/s1', NULL, 'ext', 'sec', 's1', NULL, "
            "'learner', 'accepted', ?)", (NOW,))
        connection.commit()


def _rows(database: Path, table: str) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


def _objects(database: Path, table: str) -> dict[tuple[str, str], str | None]:
    with closing(sqlite3.connect(database)) as connection:
        return {(row[0], row[1]): row[2] for row in connection.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger')",
            (table,))}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at_232(tmp_path)
    _seed(database)
    notes = _rows(database, "learner_notes")
    links = _rows(database, "learner_note_links")
    objects = _objects(database, "learner_notes")
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    # Teacher TE1's 234 (its own tables and source_tool_calls, none read here), follow-ups Nov 2's 235
    # (learner_text_gap_reversals) and teacher TE1b's 236 (router tables), none read here, follow on the way to head.
    assert [migration.version for migration in applied] == [233, 234, 235, 236, 237, 238, 240]
    # Every row survives (two new columns, NULL for the C2-era rows).
    assert [row[:13] for row in _rows(database, "learner_notes")] == notes
    assert all(row[13:] == (None, None) for row in _rows(database, "learner_notes"))
    assert _rows(database, "learner_note_links") == links
    assert _objects(database, "learner_notes") == objects  # the index and triggers are back, unchanged
    return database


def _check(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        connection.execute("PRAGMA foreign_keys = ON")
        columns = [row[1] for row in connection.execute("PRAGMA table_info(learner_notes)")]
        assert columns[-2:] == ["vault_ref_kind", "vault_ref_id"]
        connection.execute(
            "INSERT INTO learner_notes (id, note_key, path, heading_path, line, content_hash, title, heading, "
            "captured_on, origin, text_md, truncated, created_at, vault_ref_kind, vault_ref_id) VALUES "
            "('ln_v', 'annotation:a1', NULL, '', NULL, 'text:x', 'Book', 'Ch 5', '2026-11-01', 'vault', 'mine', 0, ?, "
            "'annotation', 'a1')", (NOW,))
        connection.execute(
            "INSERT INTO learner_note_links (id, note_id, note_key, target_kind, target_key, extraction_id, "
            "section_id, span_id, authorship, status, created_at) VALUES ('nl_v', 'ln_v', 'annotation:a1', "
            "'passage', 'passage:ext/sec/s2', 'ext', 'sec', 's2', 'learner', 'accepted', ?)", (NOW,))
        bad_rows = [
            # a vault row without its reference
            ("ln_b1", "capture:c1", None, None, "vault", None, None),
            # a C2-era row without its path and line
            ("ln_b2", "/n/x.org#X", None, None, "tend", None, None),
            # an unknown origin, an unknown reference kind
            ("ln_b3", "capture:c3", None, None, "phone_photo", "capture", "c3"),
            ("ln_b4", "file:x", None, None, "vault", "file", "x"),
        ]
        for row_id, key, path, line, origin, ref_kind, ref_id in bad_rows:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO learner_notes (id, note_key, path, line, content_hash, title, origin, text_md, "
                    "created_at, vault_ref_kind, vault_ref_id) VALUES (?, ?, ?, ?, 'h', 't', ?, 'x', ?, ?, ?)",
                    (row_id, key, path, line, origin, NOW, ref_kind, ref_id))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE learner_notes SET text_md = 'changed' WHERE id = 'ln_0'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM learner_notes WHERE id = 'ln_1'")
        with pytest.raises(sqlite3.IntegrityError):  # the links still name the rebuilt table
            connection.execute(
                "INSERT INTO learner_note_links (id, note_id, note_key, target_kind, target_key, extraction_id, "
                "section_id, authorship, status, created_at) VALUES ('nl_x', 'ln_missing', 'k', 'passage', 't', "
                "'ext', 'sec', 'learner', 'accepted', ?)", (NOW,))
        connection.rollback()


def test_233_widens_origin_adds_the_vault_reference_and_keeps_every_row(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_233_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_233_classifies_nothing_new():
    assert role_for_table("learner_notes") is TableRole.RAW_LEDGER
    sql = next(m for m in discover_migrations() if m.version == 233).path.read_text()
    created = {line.split()[2] for line in sql.splitlines() if line.startswith("CREATE TABLE")}
    assert created == {"learner_notes__233"}  # renamed onto the old name
    from learnloop.adaptive_difficulty import protected_tables as PT

    assert PT.role("learner_notes") == PT.PROTECTED


def test_the_head_fixture_holds_233_in_rollback_mode():
    # The head is teacher TE1's 234 (rebuilt from this 233 head with only 234 applied); it holds 233.
    assert 233 in applied_versions(HEAD)
    with open(HEAD, "rb") as handle:
        header = handle.read(20)
    assert (header[18], header[19]) == (1, 1)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'learner_notes'").fetchone()[0]
    assert "'vault'" in sql and "vault_ref_kind" in sql
