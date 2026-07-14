"""B3 forecast ledger: idempotent issuance, censoring over practiced intervals,
and pace resolution at the first pass beyond the horizon (spec §6.3)."""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.forecast_ledger import issue_forecast, resolve_due_forecasts

from tests.helpers import NOW, create_basic_vault

GOAL_ID = "goal_linear_algebra_ml"
LO_ID = "lo_svd_definition"


def _repository(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def _iso(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _issue(repository, *, kind="decay", snapshot="hash-1", horizon_days=3, predicted=0.7):
    return issue_forecast(
        repository,
        goal_id=GOAL_ID,
        kind=kind,
        input_snapshot_hash=snapshot,
        algorithm_version="mvp-0.7",
        horizon=_iso(NOW + timedelta(days=horizon_days)),
        target_metric="cold_correctness" if kind == "decay" else "qualifying_attempts_per_day",
        predicted_value=predicted,
        model_coverage={"learning_object_ids": [LO_ID], "facet_ids": ["recall"]},
        clock=FrozenClock(NOW),
    )


def _insert_attempt(repository, attempt_id, *, created_at, attempt_type="independent_attempt", correctness=1.0, hints_used=0, primed=0):
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode,
              attempt_type, rubric_score, correctness, hints_used, primed, created_at
            )
            VALUES (?, 'pi_svd_define_001', ?, 'short_answer', ?, 4, ?, ?, ?, ?)
            """,
            (attempt_id, LO_ID, attempt_type, correctness, hints_used, primed, created_at),
        )
        connection.commit()


# -- Idempotency ----------------------------------------------------------------


def test_same_goal_kind_snapshot_issues_exactly_one_row(tmp_path):
    repository = _repository(tmp_path)
    first = _issue(repository, snapshot="hash-1")
    second = _issue(repository, snapshot="hash-1")
    assert second["id"] == first["id"]
    assert len(repository.list_forecasts(GOAL_ID)) == 1

    # A materially changed input snapshot is a new forecast.
    third = _issue(repository, snapshot="hash-2")
    assert third["id"] != first["id"]
    assert len(repository.list_forecasts(GOAL_ID)) == 2


# -- Censoring -------------------------------------------------------------------


def test_do_nothing_forecast_is_censored_when_scope_was_practiced(tmp_path):
    repository = _repository(tmp_path)
    forecast = _issue(repository, kind="decay", horizon_days=3, predicted=0.9)
    # The learner practiced the scoped LO inside the forecast interval. Grading
    # the do-nothing projection against post-intervention reality would punish
    # exactly the learners who follow the plan (spec §6.3).
    _insert_attempt(repository, "att_interval", created_at=_iso(NOW + timedelta(days=1)))
    # Also give the post-horizon window a cold outcome that would grade the
    # forecast badly wrong if censoring were skipped.
    _insert_attempt(
        repository, "att_cold", created_at=_iso(NOW + timedelta(days=4)), correctness=0.0
    )

    resolved = resolve_due_forecasts(repository, clock=FrozenClock(NOW + timedelta(days=5)))
    assert [row["id"] for row in resolved] == [forecast["id"]]
    row = repository.forecast(forecast["id"])
    assert row["status"] == "censored"
    assert row["resolved_value"] is None


def test_unpracticed_decay_forecast_resolves_against_cold_outcomes_only(tmp_path):
    repository = _repository(tmp_path)
    forecast = _issue(repository, kind="decay", horizon_days=3, predicted=0.9)
    # Post-horizon outcomes: one clean cold attempt, plus assisted/primed
    # attempts that must not count as reality.
    _insert_attempt(repository, "att_cold", created_at=_iso(NOW + timedelta(days=4)), correctness=1.0)
    _insert_attempt(
        repository,
        "att_hinted",
        created_at=_iso(NOW + timedelta(days=4, hours=1)),
        attempt_type="hinted_attempt",
        correctness=0.0,
    )
    _insert_attempt(
        repository,
        "att_primed",
        created_at=_iso(NOW + timedelta(days=4, hours=2)),
        primed=1,
        correctness=0.0,
    )

    resolve_due_forecasts(repository, clock=FrozenClock(NOW + timedelta(days=5)))
    row = repository.forecast(forecast["id"])
    assert row["status"] == "resolved"
    assert row["resolved_value"] == 1.0


# -- Pace resolution ---------------------------------------------------------------


def test_pace_forecast_resolves_on_first_pass_beyond_horizon(tmp_path):
    repository = _repository(tmp_path)
    forecast = _issue(repository, kind="pace", horizon_days=7, predicted=1.0)
    _insert_attempt(repository, "att_1", created_at=_iso(NOW + timedelta(days=1)))
    _insert_attempt(repository, "att_2", created_at=_iso(NOW + timedelta(days=2)))

    # Before the horizon the row stays open — resolve_due_forecasts is the
    # session-start hook, so this models a session inside the window.
    assert resolve_due_forecasts(repository, clock=FrozenClock(NOW + timedelta(days=6))) == []
    assert repository.forecast(forecast["id"])["status"] == "open"

    # The first session past the horizon resolves it against realized pace.
    resolved = resolve_due_forecasts(repository, clock=FrozenClock(NOW + timedelta(days=8)))
    assert [row["id"] for row in resolved] == [forecast["id"]]
    row = repository.forecast(forecast["id"])
    assert row["status"] == "resolved"
    assert row["resolved_value"] == 2 / 7

    # A second resolution pass is a no-op: the row resolves exactly once.
    assert resolve_due_forecasts(repository, clock=FrozenClock(NOW + timedelta(days=9))) == []
