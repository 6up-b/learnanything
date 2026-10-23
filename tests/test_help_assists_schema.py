"""Adaptive hints H0's migration 210: ``help_assists`` (G-H17, Reader G64).

The table both specs share is created ONCE with every column and every CHECK
value either writes (spec_adaptive_hints_v1 §9; spec_reader_workbench_v1
§5.7), so no later phase (H1-H5, RW2b, RW2c) rebuilds it: ``hint_kind``'s
twelve kinds, ``assist_kind``'s seven values, ``feedback_shortcut``'s four
(no ``different_approach``), the four surfaces, the chooser's four values,
the four requests, levels 1-5. The upgrade from 209 adds only this table, its
indexes and its triggers; the durability lane runs it with production pragmas.
A binding a surface learns after the row is written (the workbench's practice
session and submission, filled at Submit; the attempt; the submit time) goes
from NULL to a value once and is then fixed (review F3).
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
from tests.test_ad1_migration import AD1_ADDED_OBJECTS, AD1_ALTERED_TABLES
from tests.test_ad23_migration import AD23_ADDED_OBJECTS
from tests.test_figures_migration import RW5A_ADDED_OBJECTS
from tests.test_reader_rw3b_migration import RW3B_ADDED_OBJECTS
from tests.test_reader_rw7a_migration import RW7A_ADDED_OBJECTS

NOW = "2026-10-17T10:00:00.000Z"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_217" / "state.sqlite"

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
#: What binds a row to its attempt and times it (docs/reviews/hints-h0-codex-review.md
#: F1, F2, round 2 V3): the client's submission key, when the submission
#: reached the sidecar before grading (§6.1's "hint shown -> submit"), and the
#: open-to-submit latency that same submission sent (stamped with it).
SUBMISSION_COLUMNS = {"submission_id", "submitted_at", "submit_latency_seconds"}

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
    # Only with its submit time (stamped together), and never negative.
    "submit_latency_seconds": (12.5,),
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
    # Later migrations (adaptive hints H1's 211, approach_maps) follow 210 on the way to head.
    # ... and adaptive difficulty AD1's 213 (its receipts).
    assert {name for name in set(after) - set(before)
            if "approach_maps" not in name and name not in AD1_ADDED_OBJECTS | AD23_ADDED_OBJECTS | RW3B_ADDED_OBJECTS | RW5A_ADDED_OBJECTS | RW7A_ADDED_OBJECTS} == {
        "help_assists", "idx_help_assists_session_item", "idx_help_assists_attempt", "idx_help_assists_submission",
        "idx_help_assists_workbench",
        "idx_help_assists_requested", "help_assists_no_delete", "help_assists_identity_fixed",
    }
    # Adaptive hints H2b's 212 rebuilds the two learner-text tables on the way
    # (their source_kind CHECK only; tests/test_hint_feedback_widening.py).
    # Adaptive difficulty AD1's 213 adds two practice_attempts columns on the way.
    assert {name: sql for name, sql in after.items()
            if name in before and not name.startswith("learner_text_gap") and name not in AD1_ALTERED_TABLES} \
        == {name: sql for name, sql in before.items()
            if not name.startswith("learner_text_gap") and name not in AD1_ALTERED_TABLES}  # nothing else changed
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
        for index, seconds in enumerate((0, 12.5)):
            store.insert_assist(connection, _base(f"ok_latency_{index}", submitted_at=NOW, submit_latency_seconds=seconds))
        with pytest.raises(sqlite3.IntegrityError):
            store.insert_assist(connection, _base("bad_latency_negative", submitted_at=NOW, submit_latency_seconds=-1))
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
    assert set(columns) == HINTS_SPEC_COLUMNS | READER_COLUMNS | LOGGED_COLUMNS | SUBMISSION_COLUMNS
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
                       "practice_session_id = NULL", "requested_at = '2026-01-01T00:00:00Z'", "id = 'ha_2'"):
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


def test_the_workbench_lifecycle_binds_each_deferred_column_once(tmp_path):
    """Review F3: a workbench hint is written before its practice session
    exists (practice_session_id NULL; Reader §5.4, the session opened at
    Submit), its problem may bind an item later, and Submit fills the practice
    session, the submission key, the submit time and the attempt. Each goes
    from NULL to a value once; replacing or clearing a binding is refused."""

    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(connect(database)) as connection:
        # No workbench or attempt rows in the head fixture: stand-in ids, keys off.
        connection.execute("PRAGMA foreign_keys = OFF")
        store.insert_assist(connection, _base(
            "ha_wb", surface="workbench", assist_kind="check", workbench_session_id="wb_1", level=1,
        ))
        row = connection.execute("SELECT practice_item_id, practice_session_id, submission_id, attempt_id "
                                 "FROM help_assists WHERE id = 'ha_wb'").fetchone()
        assert tuple(row) == (None, None, None, None)
        # The import binds the problem to an item; then Submit binds the rest.
        connection.execute("UPDATE help_assists SET practice_item_id = 'pi_1' WHERE id = 'ha_wb'")
        connection.execute(
            "UPDATE help_assists SET practice_session_id = 's1', submission_id = 'sub-1', submitted_at = ?, "
            "submit_latency_seconds = 42 WHERE id = 'ha_wb'", (NOW,))
        connection.execute("UPDATE help_assists SET attempt_id = 'att_1' WHERE id = 'ha_wb'")
        connection.commit()
        row = connection.execute("SELECT practice_session_id, submission_id, submitted_at, attempt_id "
                                 "FROM help_assists WHERE id = 'ha_wb'").fetchone()
        assert tuple(row) == ("s1", "sub-1", NOW, "att_1")
        for change in (
            "practice_session_id = 's2'", "practice_session_id = NULL",
            "submission_id = 'sub-2'", "submission_id = NULL",
            "submitted_at = '2026-10-17T11:00:00.000Z'", "submitted_at = NULL",
            "submit_latency_seconds = 120", "submit_latency_seconds = NULL",
            "workbench_session_id = 'wb_2'", "workbench_session_id = NULL",
            "attempt_id = 'att_2'", "attempt_id = NULL",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="fixed"):
                connection.execute(f"UPDATE help_assists SET {change} WHERE id = 'ha_wb'")
        # A submit time stamped without a latency never gains one later: the
        # two are one submission's (round 2, V3).
        store.insert_assist(connection, _base("ha_late", submission_id="sub-3", submitted_at=NOW))
        with pytest.raises(sqlite3.IntegrityError, match="fixed"):
            connection.execute("UPDATE help_assists SET submit_latency_seconds = 120 WHERE id = 'ha_late'")
        # The rest stays fillable (a later phase's columns).
        connection.execute("UPDATE help_assists SET shown_at = ?, step_verdicts_json = '[]' WHERE id = 'ha_wb'", (NOW,))
        connection.commit()


def test_the_store_attach_matches_the_submission_key_only(tmp_path):
    """Review F1: rows bind to the attempt of their own submission, never to a
    later submission on the same item and session, and the attach is idempotent."""

    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        common = {"practice_session_id": "s1", "practice_item_id": "pi_1"}
        store.insert_assist(connection, _base("ha_a", submission_id="sub-a", **common))
        store.insert_assist(connection, _base("ha_b", submission_id="sub-b", **common))
        store.insert_assist(connection, _base("ha_none", **common))
        assert store.stamp_submitted(
            connection, submission_id="sub-b", practice_item_id="pi_1", submitted_at=NOW, latency_seconds=60
        ) == 1
        assert store.stamp_submitted(
            connection, submission_id="sub-b", practice_item_id="pi_1", submitted_at="2026-10-17T10:05:00.000Z",
            latency_seconds=120,
        ) == 0  # the first stamp stays, time and latency
        assert store.attach_submission(
            connection, submission_id="sub-b", practice_item_id="pi_1", attempt_id="att_b",
            submitted_at="2026-10-17T10:09:00.000Z", latency_seconds=180,
        ) == 1
        assert store.attach_submission(connection, submission_id="sub-b", practice_item_id="pi_1", attempt_id="att_b") == 0
        assert store.attach_submission(connection, submission_id="sub-a", practice_item_id="pi_2", attempt_id="att_x") == 0
        assert store.attach_submission(
            connection, submission_id="sub-a", practice_item_id="pi_1", attempt_id="att_a",
            submitted_at="2026-10-17T10:01:00.000Z", latency_seconds=30,
        ) == 1
        # A recovery attach knows no submit time: it writes no latency either.
        store.insert_assist(connection, _base("ha_c", submission_id="sub-c", **common))
        assert store.attach_submission(
            connection, submission_id="sub-c", practice_item_id="pi_1", attempt_id="att_c", latency_seconds=30
        ) == 1
        # A negative latency is not believed; the submit time is kept.
        store.insert_assist(connection, _base("ha_d", submission_id="sub-d", **common))
        assert store.stamp_submitted(
            connection, submission_id="sub-d", practice_item_id="pi_1", submitted_at=NOW, latency_seconds=-5
        ) == 1
        rows = {row[0]: tuple(row[1:]) for row in connection.execute(
            "SELECT id, attempt_id, submitted_at, submit_latency_seconds FROM help_assists ORDER BY id")}
        assert rows == {
            "ha_a": ("att_a", "2026-10-17T10:01:00.000Z", 30.0),
            "ha_b": ("att_b", NOW, 60.0),
            "ha_c": ("att_c", None, None),
            "ha_d": (None, NOW, None),
            "ha_none": (None, None, None),
        }


def test_the_store_refuses_unknown_columns(tmp_path):
    from learnloop.db.copies import backup_database

    database = tmp_path / "head.sqlite"
    backup_database(HEAD, database)
    with closing(connect(database)) as connection:
        with pytest.raises(ValueError, match="kind"):
            store.insert_assist(connection, _base("ha_x", kind="authored"))


def test_help_assists_is_a_raw_ledger():
    assert role_for_table("help_assists") is TableRole.RAW_LEDGER


def test_the_head_fixture_is_at_head_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 217
    for suffix in ("-wal", "-shm", "-journal"):
        assert not HEAD.with_name(HEAD.name + suffix).exists()
