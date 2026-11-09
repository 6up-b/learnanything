"""Router objective RO1 §5.3: availability time, migration 244.

* ``practice_attempts.received_at`` (nullable) and ``received_at_source`` are additive; the head fixture
  holds them, empty; the migration backfills imported exam rows from the id's ULID time, marked
  ``inferred``, and leaves an id that is not a ULID null;
* exam seeding (whose ``created_at`` is the exam's past instant) records the import's time, ``recorded``;
  replay keeps the column;
* ``available_at(row) = coalesce(received_at, created_at)``; the router card's decision-time reads use it
  at the tag with ``[router_objective] available_at_reads`` on, and ``created_at`` below it or switched off.

Fakes only; no model call.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.ids import _decode_ulid, new_ulid
from learnloop.router_objective_switches import AVAILABLE_AT_SQL, attempt_time_sql, available_at
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml, set_algorithm_version
from tests.test_exam_seeding import EXAM_DATE, _exam_vault, _outcomes

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_251" / "state.sqlite"
TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
IMPORTED_AT = datetime(2026, 5, 19, 15, 30, 7, tzinfo=UTC)
NEW_COLUMNS = {"practice_attempts": {"received_at", "received_at_source"},
               "derived_state_rebuilds": {"projection_switches_json"}}
#: What 244 alters (no object is added): earlier migrations' "nothing else changed" diffs on the way to head
#: read this.
RO1_ALTERED_TABLES = frozenset(NEW_COLUMNS)


def _columns(connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def test_244_is_the_head_and_the_head_fixture_holds_its_empty_columns():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[244] == "244_availability_time.sql" and max(names) == 251
    assert TABLE_ROLES["practice_attempts"] is TableRole.RAW_LEDGER
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == 251
    with closing(sqlite3.connect(HEAD)) as connection:
        for table, columns in NEW_COLUMNS.items():
            assert columns <= _columns(connection, table)
        assert connection.execute(
            "SELECT COUNT(*) FROM practice_attempts WHERE received_at IS NOT NULL OR received_at_source IS NOT NULL"
        ).fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        for table, columns in NEW_COLUMNS.items():
            for column in sorted(columns):
                connection.execute(f"ALTER TABLE {table} DROP COLUMN {column}")
        connection.execute("DELETE FROM schema_migrations WHERE version = 244")
        connection.commit()


def test_244_adds_exactly_its_columns_and_changes_nothing_else(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        before_columns = {table: _columns(connection, table) for table in NEW_COLUMNS}
        rows_before = connection.execute("SELECT * FROM practice_attempts ORDER BY id").fetchall()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [244]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        for table, columns in NEW_COLUMNS.items():
            assert _columns(connection, table) - before_columns[table] == columns
        rows_after = connection.execute(
            "SELECT * FROM practice_attempts ORDER BY id").fetchall()
    assert set(after) == set(before)
    assert {name for name, sql in before.items() if after[name] != sql} == set(NEW_COLUMNS)
    # The head's six attempts are not exam imports: nothing is backfilled, nothing else moves.
    assert [row[:-2] for row in rows_after] == rows_before and all(row[-2:] == (None, None) for row in rows_after)


@pytest.mark.durability
def test_244_on_the_durability_lane(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [244]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _ulid_iso(value: str) -> str:
    milliseconds, _random = _decode_ulid(value)
    return datetime.fromtimestamp(milliseconds // 1000, tz=UTC).isoformat().replace("+00:00", "Z")


def test_the_backfill_reads_an_imported_exam_rows_ulid_time_and_leaves_bad_ids_null(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    good = new_ulid()
    lower = new_ulid().lower()
    rows = {
        good: "exam_evidence",
        lower: "exam_evidence",
        "exam-import-1": "exam_evidence",            # not a ULID
        "8" + good[1:]: "exam_evidence",              # overflows 128 bits: not a ULID
        good[:-1] + "U": "exam_evidence",             # U is no Crockford character
        new_ulid(): "independent_attempt",            # not an exam import
    }
    with closing(sqlite3.connect(database)) as connection:
        template = connection.execute("SELECT * FROM practice_attempts LIMIT 1").fetchone()
        names = [row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)")]
        for attempt_id, attempt_type in rows.items():
            values = dict(zip(names, template, strict=True))
            values.update(id=attempt_id, attempt_type=attempt_type, created_at="2026-05-01T12:00:00Z",
                          submission_id=None, plan_presentation_id=None, probe_presentation_id=None)
            connection.execute(
                f"INSERT INTO practice_attempts({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",
                list(values.values()))
        connection.commit()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        apply_migrations(database)
    with closing(sqlite3.connect(database)) as connection:
        got = {row[0]: (row[1], row[2]) for row in connection.execute(
            "SELECT id, received_at, received_at_source FROM practice_attempts")}
    assert got[good] == (_ulid_iso(good), "inferred")
    assert got[lower] == (_ulid_iso(lower), "inferred")
    for attempt_id in rows:
        if attempt_id not in (good, lower):
            assert got[attempt_id] == (None, None), attempt_id


def test_the_check_refuses_another_source(tmp_path):
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE practice_attempts SET received_at_source = 'guessed'")


def test_available_at_is_received_at_else_created_at():
    assert available_at({"created_at": "2026-05-01T12:00:00Z", "received_at": "2026-05-19T15:30:07Z"}) == (
        "2026-05-19T15:30:07Z")
    assert available_at({"created_at": "2026-05-01T12:00:00Z", "received_at": None}) == "2026-05-01T12:00:00Z"
    assert available_at({"created_at": None}) is None
    assert AVAILABLE_AT_SQL == "COALESCE(received_at, created_at)"


def _seeded(tmp_path, version: str | None = None, toml: str | None = None):
    vault_root, loaded, repository = _exam_vault(tmp_path)
    if version is not None:
        set_algorithm_version(loaded_paths(vault_root), version)
    if toml:
        append_config_toml(vault_root, toml)
    loaded = load_vault(vault_root)
    seed_exam_attempts(loaded, repository, outcomes=_outcomes(), clock=FrozenClock(IMPORTED_AT))
    return vault_root, load_vault(vault_root), repository


def loaded_paths(vault_root):
    from learnloop.vault.paths import VaultPaths

    vault = load_vault(vault_root)
    return VaultPaths(vault.root, vault.config)


def test_exam_seeding_records_the_import_time_and_replay_keeps_it(tmp_path):
    _root, loaded, repository = _seeded(tmp_path)
    attempts = repository.list_attempts_by_learning_object("lo_svd_definition")
    assert len(attempts) == 3
    for attempt in attempts:
        assert attempt["created_at"].startswith(EXAM_DATE)
        assert (attempt["received_at"], attempt["received_at_source"]) == ("2026-05-19T15:30:07Z", "recorded")
        assert available_at(attempt) == "2026-05-19T15:30:07Z"
    rebuild_derived_state(loaded, repository)
    again = repository.list_attempts_by_learning_object("lo_svd_definition")
    assert [(a["id"], a["received_at"], a["received_at_source"]) for a in again] == [
        (a["id"], a["received_at"], a["received_at_source"]) for a in attempts]
    # FSRS and mastery keep the exam's own date.
    assert repository.mastery_state("lo_svd_definition").last_evidence_at.startswith(EXAM_DATE)
    assert repository.practice_item_state("pi_exam_q1").last_attempt_at.startswith(EXAM_DATE)


def test_an_ordinary_attempt_records_no_received_at(tmp_path):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    _root, loaded, repository = _exam_vault(tmp_path)
    result = complete_self_graded_attempt(
        loaded, repository, AttemptDraft(practice_item_id="pi_exam_q1", learner_answer_md="An answer."),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=FrozenClock(IMPORTED_AT))
    row = repository.fetch_practice_attempt(result.attempt_id)
    assert (row["received_at"], row["received_at_source"]) == (None, None)


#: A decision after the exam's date and before the import: the router could not have known the exam then.
DECISION_AT = "2026-05-10T09:00:00Z"


@pytest.mark.parametrize("version, toml, sees_exam", [
    (TAG, None, False),
    (TAG, "[router_objective]\navailable_at_reads = false\n", True),
    (PREDECESSOR, None, True),
], ids=["tag", "off", "below"])
def test_the_router_cards_decision_time_reads_use_availability_at_the_tag(tmp_path, version, toml, sees_exam):
    from learnloop.daily_plan.router_card import CardGatherer

    root, loaded, repository = _seeded(tmp_path, version, toml)
    gatherer = CardGatherer(loaded, repository)
    with repository.connection() as connection:
        rows = gatherer._attempts(connection, ["lo_svd_definition"], DECISION_AT)
        known = attempt_time_sql(loaded.config, connection)
    assert bool(rows) is sees_exam
    assert known == ("created_at" if sees_exam else AVAILABLE_AT_SQL)
    # After the import every gate reads the same rows, in the same order (by when they happened).
    with repository.connection() as connection:
        later = gatherer._attempts(connection, ["lo_svd_definition"], "2026-05-20T00:00:00Z")
    assert [row["practice_item_id"] for row in later] == ["pi_exam_q3", "pi_exam_q2", "pi_exam_q1"]


def _card_inputs(loaded, repository, now_iso: str):
    from learnloop.daily_plan.router_card import CardGatherer
    from learnloop.daily_plan.types import BlockCandidate, PlanState

    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    feasible = [BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None,
        learning_object_ids=("lo_svd_definition",), item_ids=("pi_exam_q1",), reading=None, est_minutes=4.0,
        planner_value=1.0, reason="review", annotations={"reason_code": "review", "reversible": True},
    )]
    return CardGatherer(loaded, repository, session_id="s1").inputs(state, feasible, now_iso=now_iso)


#: Inside the exam's week, before its import (codex review F1): the card's week of activity is by when
#: the work happened, and at the tag it counts only what was known at the decision.
WEEK_OF_THE_EXAM = "2026-05-05T09:00:00Z"


@pytest.mark.parametrize("version, toml, sees_exam", [
    (TAG, None, False),
    (TAG, "[router_objective]\navailable_at_reads = false\n", True),
    (PREDECESSOR, None, True),
], ids=["tag", "off", "below"])
def test_the_whole_card_reads_no_exam_before_its_import_at_the_tag(tmp_path, version, toml, sees_exam):
    _root, loaded, repository = _seeded(tmp_path, version, toml)
    before = _card_inputs(loaded, repository, WEEK_OF_THE_EXAM)
    exam = before.learning_objects["lo_svd_definition"]
    if sees_exam:
        # The predecessor, and the switch off: the exam rows enter the week's activity and the evidence.
        assert (before.interaction_7d["attempts"], before.interaction_7d["active_days"]) == (3, 1)
        assert exam["evidence"]["attempts"] == 3 and before.decision["as_of_attempt_id"] is not None
    else:
        # The tag: nothing the router could not have known reaches the card.
        assert (before.interaction_7d["attempts"], before.interaction_7d["sessions"],
                before.interaction_7d["active_days"], before.interaction_7d["hints_used"],
                before.interaction_7d["assisted_redos"]) == (0, 0, 0, 0, 0)
        assert exam["evidence"] == {} and exam["last_attempt_at"] is None
        assert before.decision["as_of_attempt_id"] is None and before.recent_work == []
    # After the import every gate reads the exam as evidence, dated when it happened: its week is over,
    # so the week's activity counts none of it, under every gate alike.
    after = _card_inputs(loaded, repository, "2026-05-20T00:00:00Z")
    assert after.learning_objects["lo_svd_definition"]["evidence"]["attempts"] == 3
    assert after.learning_objects["lo_svd_definition"]["last_attempt_at"].startswith(EXAM_DATE)
    assert after.interaction_7d["attempts"] == 0 and after.interaction_7d["active_days"] == 0


def test_the_weeks_activity_counts_an_import_inside_its_week_once_it_is_known(tmp_path):
    """The window stays by occurrence time: an exam imported within its week counts on the day it
    happened, once the decision is after the import."""

    from learnloop.daily_plan.router_card import CardGatherer

    vault_root, loaded, repository = _exam_vault(tmp_path)
    set_algorithm_version(loaded_paths(vault_root), TAG)
    seed_exam_attempts(load_vault(vault_root), repository, outcomes=_outcomes(),
                       clock=FrozenClock(datetime(2026, 5, 3, 12, 0, tzinfo=UTC)))
    loaded = load_vault(vault_root)
    gatherer = CardGatherer(loaded, repository)
    with repository.connection() as connection:
        between = gatherer._interaction(connection, "2026-05-02T12:00:00Z", [])
        known = gatherer._interaction(connection, "2026-05-04T12:00:00Z", [])
    assert between["attempts"] == 0
    assert (known["attempts"], known["active_days"]) == (3, 1)
