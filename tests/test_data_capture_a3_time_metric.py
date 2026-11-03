"""Data capture A3: calendar time and recorded minutes to a first delayed success.

A first-delayed-success proxy, not goal attainment; unfinished trajectories and coverage visible; active never
blended with elapsed; the goal contract pinned; ``learner_minutes_to_cold_success`` and ``problems_to_cold_success``
renamed for what they measure.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json

import pytest

from learnloop.db.repositories import Repository
from learnloop.diagnosis import scoreboard as SB
from learnloop.router.first_delayed_success import LABEL, METRIC_VERSION, summary, trajectories
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault
from tests.test_router_outcomes import A, B, LO, _reveal

T0 = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
AS_OF = "2026-07-01T00:00:00Z"


def _at(**delta):
    return (T0 + timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    vault.goals = []  # the basic vault's goal would enroll every LO: each test says what enrolls it
    return vault, Repository(paths.sqlite_path)


def _attempt(repository, attempt_id, *, item=A, at, correctness=1.0, latency=120, session="s1", hints=0,
             presentation=None, attempt_type="independent_attempt"):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, hints_used,"
            " correctness, latency_seconds, manual_review, created_at, session_id, primed, evidence_origin, plan_presentation_id)"
            " VALUES (?,?,?,?,?,?,?,?,0,?,?,0,'human',?)",
            (attempt_id, item, LO, "short_answer", attempt_type, hints, correctness, latency, at, session, presentation),
        )
        connection.commit()


def _trajectory(world, lo=LO):
    vault, repository = world
    with repository.connection() as connection:
        rows, facts = trajectories(connection, vault, success_correctness=0.8, as_of=AS_OF)
    return next(row for row in rows if row.learning_object_id == lo), rows, facts


def test_the_first_success_in_the_same_sitting_does_not_qualify(world):
    """Reproduced first: the old metric stopped here, at an unassisted success with no delay at all."""

    _vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4)
    _attempt(repository, "a2", at=_at(minutes=5), correctness=1.0)
    row, _rows, _facts = _trajectory(world)
    assert not row.reached and row.open_calendar_days is not None and row.calendar_days is None
    assert row.attempts == 2

    # The old metric, renamed: it reports a success at minute five, and now says what it measures.
    _problems, minutes = SB.cold_success_metrics(repository, success_correctness=0.8)
    assert minutes.name == "learner_minutes_to_first_unassisted_success"
    assert "no delay" in minutes.note


def test_a_delayed_unassisted_success_ends_the_trajectory_with_calendar_time_and_minutes(world):
    _vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4, latency=60)
    _attempt(repository, "a2", at=_at(days=3), correctness=1.0, latency=90, session="s2")
    _attempt(repository, "a3", at=_at(days=9), correctness=1.0, latency=1000, session="s3")
    row, _rows, _facts = _trajectory(world)
    assert row.success_attempt_id == "a2" and row.success_at == _at(days=3)
    assert row.calendar_days == 3.0 and row.enrollment_source == "first_exposure"
    assert row.active_attempt_seconds == 150 and row.active_minutes == 2.5
    assert row.attempts == 2 and row.complete_latency


def test_requested_help_is_no_qualifying_success_and_a_missing_latency_is_not_zero(world):
    _vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), latency=None)
    _attempt(repository, "a2", at=_at(days=3), hints=1, attempt_type="hinted_attempt", session="s2")
    row, _rows, _facts = _trajectory(world)
    assert not row.reached and row.attempts == 2 and row.attempts_with_latency == 1 and not row.complete_latency


def test_a_seen_answer_is_no_qualifying_success(world):
    _vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4)
    _reveal(repository, "r1", item=B, created_at=_at(days=3, minutes=-5))
    _attempt(repository, "a2", item=B, at=_at(days=3), session="s2")
    assert not _trajectory(world)[0].reached


def test_observed_active_time_is_kept_apart_from_elapsed(world):
    _vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4, latency=60)
    with repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, short_circuit_reason, content_hash, created_at)"
                           " VALUES ('b1', 'practice', 1, '', 'h', ?)", (_at(days=3),))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at)"
                           " VALUES ('p1', 'b1', ?, 'requested', ?)", (A, _at(days=3)))
        connection.commit()
    _attempt(repository, "a2", at=_at(days=3, minutes=10), latency=90, session="s2", presentation="p1")
    row, _rows, _facts = _trajectory(world)
    assert row.reached and row.attempts_bound_to_a_presentation == 1
    assert row.active_attempt_seconds == 150 and row.elapsed_attempt_seconds == 600
    assert row.active_minutes == 2.5 and row.elapsed_minutes == 10.0


def _reader_visit(repository, visit, *, opened, closed, active):
    with repository.connection() as connection:
        for event_id, kind, at, payload in (
                (f"{visit}o", "reader_view_opened", opened, {"visit_id": visit}),
                (f"{visit}c", "reader_view_closed", closed, {"visit_id": visit, "active_seconds": active})):
            connection.execute(
                "INSERT INTO interaction_events(id, kind, payload_json, origin, created_at, occurred_at, received_at)"
                " VALUES (?,?,?,'learner',?,?,?)", (event_id, kind, json.dumps(payload), at, at, at))
        connection.commit()


def test_reader_active_time_joins_when_a_reading_names_the_lo_else_it_is_unattributed(world):
    vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4, latency=60)
    _reader_visit(repository, "v1", opened=_at(days=1), closed=_at(days=1, minutes=30), active=600)
    _reader_visit(repository, "v2", opened=_at(days=2), closed=_at(days=2, minutes=30), active=300)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, context, extraction_id, span_id, entity_type, entity_id, created_at)"
            " VALUES ('e1', 'reader', 'x', 's', 'learning_object', ?, ?)", (LO, _at(days=1, minutes=10)))
        connection.commit()
    _attempt(repository, "a2", at=_at(days=3), latency=90, session="s2")
    row, _rows, facts = _trajectory(world)
    assert row.reached and row.reading_visits == 1
    assert row.active_reading_seconds == 600 and row.elapsed_reading_seconds == 1800
    assert facts["unattributed_active_reading_seconds"] == 300
    assert row.active_minutes == pytest.approx((150 + 600) / 60)


def test_enrollment_is_the_learners_commitment_and_a_system_dated_check_is_none(world):
    from learnloop.curriculum import commitments as C
    from learnloop.clock import FrozenClock, parse_utc

    vault, repository = world
    C.create_commitment(repository, action="test_me_later", intent_text="x",
                        targets=[{"target_kind": "legacy_practice_item", "target_ref": A, "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="m", due_hint="2026-06-01", reason="r",
                        provenance={"via": "measurement"}, clock=FrozenClock(parse_utc(_at(minutes=0))))
    _attempt(repository, "a1", at=_at(days=1), correctness=0.4)
    assert _trajectory(world)[0].enrollment_source == "first_exposure"
    C.create_commitment(repository, action="help_me_remember", intent_text="y",
                        targets=[{"target_kind": "learning_object", "target_ref": LO, "role": "required"}],
                        depth_preset="keep_in_touch", client_idempotency_key="l", reason="r",
                        clock=FrozenClock(parse_utc(_at(hours=2))))
    row = _trajectory(world)[0]
    assert (row.enrollment_source, row.enrolled_at) == ("commitment", _at(hours=2))


def test_the_goal_contract_in_force_is_pinned_and_no_goal_model_is_added(world):
    from types import SimpleNamespace

    vault, repository = world
    goal = SimpleNamespace(id="g1", due_at="2026-06-30T00:00:00Z", created_at=_at(days=-5),
                           facet_scope=SimpleNamespace(concepts=[vault.learning_objects[LO].concept], facets=[]))
    vault.goals = [goal]
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4)
    _attempt(repository, "a2", at=_at(days=3), session="s2")
    row = _trajectory(world)[0]
    assert (row.enrollment_source, row.enrolled_at) == ("goal", _at(days=-5))
    assert row.goal == {"goal_id": "g1", "contract_version_id": None, "version": None, "content_hash": None,
                        "due_at": "2026-06-30T00:00:00Z"}
    with repository.connection() as connection:
        for version, at in ((1, _at(days=-2)), (2, _at(days=30))):
            connection.execute(
                "INSERT INTO goal_contract_versions(id, goal_id, version, contract_json, content_hash, support_hash,"
                " contract_schema_version, change_class, author, created_at) VALUES (?,?,?,?,?,?,1,?,'learner',?)",
                (f"gc{version}", "g1", version, json.dumps({"due_at": f"due-{version}"}), f"c{version}", "s",
                 "confirm" if version == 1 else "metadata", at))
        connection.commit()
    row = _trajectory(world)[0]
    assert row.goal["contract_version_id"] == "gc1" and row.goal["due_at"] == "due-1", "the version in force at the success"
    assert row.enrolled_at == _at(days=-2), "the contract's confirmation is the enrollment"


def test_the_summary_keeps_unfinished_trajectories_and_coverage_visible(world):
    _vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4, latency=None)
    _row, rows, facts = _trajectory(world)
    report = summary(rows, facts)
    assert report["label"] == LABEL and "not goal attainment" in report["label"]
    assert report["metric_version"] == METRIC_VERSION
    assert report["reached"] == 0 and report["unfinished"] == report["learning_objects"] >= 1
    assert report["mean_calendar_days_to_success"] is None
    assert report["coverage"]["attempts"] == 1 and report["coverage"]["attempts_with_latency"] == 0


def test_the_board_carries_the_proxies_as_companions_and_says_so(world):
    vault, repository = world
    _attempt(repository, "a1", at=_at(minutes=0), correctness=0.4, latency=60)
    _attempt(repository, "a2", at=_at(days=3), latency=90, session="s2")
    days, minutes = SB.first_delayed_success_metrics(vault, repository, success_correctness=0.8)
    assert days.name == "calendar_days_to_first_delayed_success_proxy" and days.value == 3.0
    assert minutes.name == "learner_minutes_to_first_delayed_success_proxy" and minutes.value == 2.5
    assert "not goal attainment" in days.note and days.companion_of == "problems_to_first_unassisted_success"
    assert SB.SCOREBOARD_VERSION == "b5_scoreboard_v2"
    assert "learner_minutes_to_cold_success" not in SB.B5_ORDER
    assert "problems_to_cold_success" not in SB.B5_ORDER and SB.B5_ORDER[0] == "problems_to_first_unassisted_success"
    assert SB.SCOREBOARD_VERSION == "b5_scoreboard_v2", "both renames are this one version"


def test_an_empty_board_reports_no_data_never_zero(world):
    vault, repository = world
    days, minutes = SB.first_delayed_success_metrics(vault, repository, success_correctness=0.8)
    assert days.value is None and minutes.value is None and not days.available
