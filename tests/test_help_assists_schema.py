"""Adaptive hints H0's migration 210: ``help_assists`` (G-H17, Reader G64).

The table both specs share is created ONCE with every column and every CHECK
value either writes (spec_adaptive_hints_v1 §9; spec_reader_workbench_v1
§5.7), so no later phase (H1-H5, RW2b, RW2c) rebuilds it: ``hint_kind``'s
twelve kinds, ``assist_kind``'s seven values, ``feedback_shortcut``'s four
(no ``different_approach``), the four surfaces, the chooser's four values,
the four requests, levels 1-5. The upgrade from 209 adds only this table, its
indexes and its triggers; the durability lane runs it with production pragmas.
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
from learnloop.db.stores import help_assists as store
from learnloop.db.table_roles import TableRole, role_for_table

NOW = "2026-10-17T10:00:00.000Z"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_210" / "state.sqlite"

#: spec_adaptive_hints_v1 §9, "This spec's columns".
HINTS_SPEC_COLUMNS = {
    "id", "surface", "practice_item_id", "practice_item_hash", "practice_session_id", "attempt_id", "hint_kind",
    "level", "horizon", "route_id", "from_node_id", "target_node_id", "map_id", "strategy", "body_md",
    "authored_index", "work_hash", "work_chars", "placement_json", "chooser", "options_json", "probabilities_json",
    "propensity", "seed", "policy_version", "request", "feedback_text", "feedback_shortcut",
    "contract_failures_json", "leak_flags_json", "shown", "counted_by", "model", "prompt_version", "input_hash",
    "latency_ms", "requested_at", "shown_at",
}
#: spec_adaptive_hints_v1 §9 "The Reader's columns" = spec_reader_workbench_v1 §5.7's workbench columns.
READER_COLUMNS = {
    "workbench_session_id", "assist_kind", "offered_level", "level_source", "step_snapshot_json",
    "step_verdicts_json", "first_questionable_step_id", "error_kind_guess", "about_step_id",
    "continue_from_step_id", "rivals_json", "predicted_answers_json", "eig_nats", "feedback_step_id",
    "cited_span_ids_json", "retrieval_manifest_json", "alternatives_json",
}
#: What §6.2 (hints) and §5.5 (Reader) log on the row that neither §9 list
#: names (docs/reviews/adaptive-hints-H0.md §3): the drawn option kept apart
#: from the served kind, and the question-set version and state hash.
LOGGED_COLUMNS = {"drawn_option_json", "question_set_version", "state_hash"}

CHECKED_VALUES = {
    "surface": ("practice", "workbench", "guided_redo", "tutor"),
    "assist_kind": ("hint", "check", "discriminate_answer", "bridge", "example", "compare_methods", "feedback"),
    "hint_kind": (
        "approach_question", "discriminating", "localize", "waypoint", "subgoal_plan", "next_step",
        "error_specific", "worked_parallel", "authored", "continuation", "worked_chunk", "walkthrough",
    ),
    "chooser": ("decider", "fallback", "learner_pick", "none"),
    "request": ("more", "feedback", "book_way", "smaller_step"),
    "feedback_shortcut": ("not_where_stuck", "too_big", "learner_route", "notation"),
    "level_source": ("offered", "learner_pick"),
    "counted_by": ("client", "server"),
    "level": (1, 2, 3, 4, 5),
    "offered_level": (1, 2, 3, 4, 5),
    "shown": (0, 1),
}
REJECTED_VALUES = {
    "surface": ("reader", "mobile"),
    "assist_kind": ("discriminate", "source"),
    "hint_kind": ("kind", "discriminate", "worked_example"),
    "chooser": ("model", "random"),
    "request": ("again",),
    # The first draft's value, withdrawn because it read the opposite way.
    "feedback_shortcut": ("different_approach",),
    "level_source": ("chooser",),
    "counted_by": ("none", "both"),
    "level": (0, 6),
    "offered_level": (0, 6),
    "shown": (2,),
    "horizon": (0,),
    "authored_index": (-1,),
    "work_chars": (-1,),
    "propensity": (-0.1, 1.5),
    "latency_ms": (-1,),
}
NULLABLE_CHECKED = ("hint_kind", "request", "feedback_shortcut", "level_source", "counted_by", "level", "offered_level")


def _base(row_id: str, **columns) -> dict:
    return {"id": row_id, "surface": "practice", "assist_kind": "hint", "chooser": "none", "shown": 1,
            "requested_at": NOW, **columns}


def _database_at_209(tmp_path: Path) -> Path:
    through = tmp_path / "through_209"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 209:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 209
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at_209(tmp_path)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied][0] == 210
    after = _schema(database)
    assert set(after) - set(before) == {
        "help_assists", "idx_help_assists_session_item", "idx_help_assists_attempt", "idx_help_assists_workbench",
        "idx_help_assists_requested", "help_assists_no_delete", "help_assists_identity_fixed",
    }
    assert {name: sql for name, sql in after.items() if name in before} == before  # nothing else changed
    return database


def _columns(database: Path) -> list[str]:
    with closing(sqlite3.connect(database)) as connection:
        return [row[1] for row in connection.execute("PRAGMA table_info(help_assists)")]


def _check_constraints(database: Path) -> None:
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for column, values in CHECKED_VALUES.items():
            for index, value in enumerate(values):
                row = _base(f"ok_{column}_{index}", **{column: value})
                store.insert_assist(connection, row)
        for column in NULLABLE_CHECKED:
            store.insert_assist(connection, _base(f"null_{column}", **{column: None}))
        for column, values in REJECTED_VALUES.items():
            for index, value in enumerate(values):
                with pytest.raises(sqlite3.IntegrityError):
                    store.insert_assist(connection, _base(f"bad_{column}_{index}", **{column: value}))
        for required in ("surface", "assist_kind", "chooser", "shown", "requested_at"):
            row = _base(f"missing_{required}")
            del row[required]
            with pytest.raises(sqlite3.IntegrityError):
                store.insert_assist(connection, row)
        # Foreign keys: an attempt and a workbench session must exist.
        for column in ("attempt_id", "workbench_session_id"):
            with pytest.raises(sqlite3.IntegrityError):
                store.insert_assist(connection, _base(f"fk_{column}", **{column: "missing"}))
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        connection.commit()


def test_every_column_both_specs_write_is_created_once():
    columns = _columns(HEAD)
    assert len(columns) == len(set(columns))
    assert set(columns) == HINTS_SPEC_COLUMNS | READER_COLUMNS | LOGGED_COLUMNS
    assert tuple(columns) == store.COLUMNS


def test_every_check_value_either_spec_writes_is_admitted_and_nothing_else(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    _check_constraints(database)


def test_210_adds_help_assists_and_nothing_else(tmp_path):
    database = _upgrade(tmp_path)
    assert tuple(_columns(database)) == store.COLUMNS
    _check_constraints(database)


@pytest.mark.durability
def test_210_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check_constraints(database)


def test_the_ledger_keeps_rows_and_an_attached_attempt(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(connect(database)) as connection:
        store.insert_assist(connection, _base("ha_1", practice_session_id="s1", practice_item_id="pi_1"))
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM help_assists WHERE id = 'ha_1'")
        for change in ("surface = 'tutor'", "assist_kind = 'check'", "practice_session_id = 's2'",
                       "requested_at = '2026-01-01T00:00:00Z'", "id = 'ha_2'"):
            with pytest.raises(sqlite3.IntegrityError, match="fixed"):
                connection.execute(f"UPDATE help_assists SET {change} WHERE id = 'ha_1'")
        # A later phase may fill in what it learns (a workbench binding, the
        # time shown); the attempt is set once and then fixed.
        connection.execute("UPDATE help_assists SET practice_item_id = 'pi_2', shown_at = ? WHERE id = 'ha_1'", (NOW,))
        connection.commit()
        # No attempt rows in the head fixture: a stand-in id, keys off.
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("UPDATE help_assists SET attempt_id = 'att_1' WHERE id = 'ha_1'")
        with pytest.raises(sqlite3.IntegrityError, match="fixed"):
            connection.execute("UPDATE help_assists SET attempt_id = 'att_2' WHERE id = 'ha_1'")
        with pytest.raises(sqlite3.IntegrityError, match="fixed"):
            connection.execute("UPDATE help_assists SET attempt_id = NULL WHERE id = 'ha_1'")


def test_the_store_refuses_unknown_columns(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(connect(database)) as connection:
        with pytest.raises(ValueError, match="kind"):
            store.insert_assist(connection, _base("ha_x", kind="authored"))


def test_help_assists_is_a_raw_ledger():
    assert role_for_table("help_assists") is TableRole.RAW_LEDGER


def test_the_head_fixture_is_at_210_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 210
    for suffix in ("-wal", "-shm", "-journal"):
        assert not HEAD.with_name(HEAD.name + suffix).exists()
