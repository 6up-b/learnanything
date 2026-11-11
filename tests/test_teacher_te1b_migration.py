"""Teacher TE1b: migration 236 (spec_teacher_v1 §15.1, §18.1; renumbered at landing if 236 is taken).

``router_suggestion_responses`` (RAW_LEDGER, append-only, one response per decision) and
``router_decisions`` rebuilt so its ``decision_kind`` CHECK admits ``lesson_suggestion``, every row
and id kept. The head fixture is at 236 in rollback mode with an empty response table. The earlier
migrations' "nothing else changed" diffs on the way to head read ``TE1_AND_TE1B_ADDED_OBJECTS`` and
``TE1_AND_TE1B_ALTERED_TABLES`` (TE1's 234 and this 236).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TableRole, role_for_table
from tests.helpers import MIGRATION_HEAD_FIXTURE, migration_head
from tests.teacher_te1b_migration_helpers import TE1B_ADDED_OBJECTS

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"

_DECISION = (
    "INSERT INTO router_decisions(id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, "
    "log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, propensity, "
    "propensity_kind, detail_json, created_at) VALUES (?, ?, ?, 'today_card', 'mixture', 'lesson_suggestion_v1', "
    "'mvp-0.43', 'router_decisions_v1', 'h', '[]', '{}', 1, ?, 0.5, 'exact', '{}', '2026-11-02T09:00:00Z')"
)


def test_236_is_te1bs_migration_and_its_table_is_classified():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[236] == "236_router_lesson_suggestions.sql"
    assert role_for_table("router_suggestion_responses") == TableRole.RAW_LEDGER
    assert role_for_table("router_decisions") == TableRole.RAW_LEDGER
    # Like the router's other tables, AD never reads it (unclassified: refused inside an AD operation).
    assert PT.role("router_suggestion_responses") is None and PT.role("router_decisions") is None


def _upgrade(tmp_path: Path) -> Path:
    database = tmp_path / "state.sqlite"
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    return database


def test_the_head_fixture_is_at_236_in_rollback_mode_with_no_response():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert TE1B_ADDED_OBJECTS <= names
        assert connection.execute("SELECT COUNT(*) FROM router_suggestion_responses").fetchone()[0] == 0


def _check(database: Path) -> None:
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(_DECISION, ("d1", "lesson_suggestion:2026-11-02", "lesson_suggestion", "lesson:lo_a"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_DECISION, ("d2", "x:1", "nobody", "lesson:lo_a"))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE router_decisions SET mode = 'staged' WHERE id = 'd1'")
        insert = ("INSERT INTO router_suggestion_responses(id, decision_id, response, candidate_ref, "
                  "learning_object_ids_json, lesson_id, responded_at, created_at) VALUES (?, ?, ?, ?, '[]', ?, "
                  "'2026-11-02T09:01:00Z', '2026-11-02T09:01:00Z')")
        connection.execute(insert, ("r1", "d1", "accepted", "lesson:lo_a", "les_1"))
        with pytest.raises(sqlite3.IntegrityError):  # one response per decision
            connection.execute(insert, ("r2", "d1", "declined", "lesson:lo_a", None))
        # Landing ruling R2: the reservation is let go by one more row (released or expired), at most one.
        connection.execute(insert, ("r1b", "d1", "released", "lesson:lo_a", None))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(insert, ("r1c", "d1", "expired", "lesson:lo_a", None))
        with pytest.raises(sqlite3.IntegrityError):  # a release names its lesson in detail_json, not lesson_id
            connection.execute(_DECISION, ("d4", "lesson_suggestion:2026-11-04", "lesson_suggestion", "lesson:lo_c"))
            connection.execute(insert, ("r6", "d4", "expired", "lesson:lo_c", "les_4"))
        with pytest.raises(sqlite3.IntegrityError):  # a decline opens no lesson
            connection.execute(_DECISION, ("d3", "lesson_suggestion:2026-11-03", "lesson_suggestion", "lesson:lo_b"))
            connection.execute(insert, ("r3", "d3", "declined", "lesson:lo_b", "les_2"))
        with pytest.raises(sqlite3.IntegrityError):  # an unknown response
            connection.execute(insert, ("r4", "d3", "maybe", "lesson:lo_b", None))
        with pytest.raises(sqlite3.IntegrityError):  # the decision must exist
            connection.execute(insert, ("r5", "nope", "declined", "lesson:lo_b", None))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE router_suggestion_responses SET response = 'declined' WHERE id = 'r1'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM router_suggestion_responses WHERE id = 'r1'")


def test_236_widens_the_kind_check_and_keeps_both_ledgers_append_only(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_236_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_236_keeps_every_router_decision_row(tmp_path):
    """Every migration through 235, a recorded decision and a payload naming it, then 236: the rebuild keeps
    the row, its id and its reference, and the foreign keys still resolve."""

    from learnloop.db.migrate import discover_migrations as discover

    every = discover()
    before = tmp_path / "through_235"
    before.mkdir()
    for migration in every:
        if migration.version <= 235:
            (before / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database, migrations_dir=before)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(_DECISION.replace("'lesson_suggestion_v1'", "'lane_quota_v1'"),
                           ("d_keep", "plan_block:b1", "plan_block", "pi_1"))
        connection.execute(
            "INSERT INTO router_decision_payloads(id, decision_id, kind, format_version, content_hash, created_at) "
            "VALUES ('p1', 'd_keep', 'card', 'v', 'h', '2026-11-02T09:00:00Z')")
        connection.commit()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied] == list(range(236, migration_head() + 1))
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT id, decision_kind, chosen_ref FROM router_decisions").fetchall() == [
            ("d_keep", "plan_block", "pi_1")]
        assert connection.execute("SELECT decision_id FROM router_decision_payloads").fetchall() == [("d_keep",)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
