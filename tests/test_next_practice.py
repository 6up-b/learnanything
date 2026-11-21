"""What comes next, dated (the first evening's step 7): one read-only summary the session's finish and Today share.

The learner could not find when their answered questions would return. ``daily_plan.next_practice`` says, at one
instant, which reviews are due on which day of the plan's calendar (each at its effective due), when each check on
your own becomes available, and what question work is still under way, and it changes nothing: the database is the
same, byte for byte, after the read, even where the shared reads mark follow-ups on a writable attach.

The fixture is ``tests/next_practice_helpers.py``'s evening (Saturday 31 October 2026, New York, the night daylight
saving ends).
"""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.next_practice_helpers import (
    AS_OF,
    CLOCK,
    EXPECTED,
    database_fingerprint,
    evening_vault,
    lapsing_followups,
    wait_for_build,
)
from tests.next_practice_helpers import new_york  # noqa: F401 - a fixture, used by parameter name


def _summary(paths, repository, clock=CLOCK):
    from learnloop.daily_plan.next_practice import next_practice

    return next_practice(load_vault(paths.root), repository, clock=clock)


def test_the_evening_summary_dates_every_review_check_and_work_under_way(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault")

    assert _summary(paths, repository) == EXPECTED


def test_a_due_after_the_clocks_go_back_stays_on_its_own_day(tmp_path, new_york):
    """Sunday 1 November is 25 hours long in New York. A due at 23:30 that Sunday (04:30 UTC on Monday) is Sunday's,
    though now's offset (UTC-4) would put it at 00:30 on Monday; and the next day starts at its own midnight."""

    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)

    summary = _summary(paths, repository)
    tomorrow = summary["reviews"][0]
    assert (tomorrow["date"], tomorrow["item_ids"]) == ("2026-11-01", ["pi_dst", "pi_tomorrow"])
    assert summary["calendar"]["next_day_starts_at"] == "2026-11-01T04:00:00Z"  # midnight EDT

    # Read during that long Sunday: the next day starts at midnight EST, 25 hours after Sunday's began.
    sunday = _summary(paths, repository, FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC)))
    assert sunday["calendar"] == {"zone": "EST", "today": "2026-11-01", "tomorrow": "2026-11-02",
                                  "next_day_starts_at": "2026-11-02T05:00:00Z"}
    assert [(group["date"], group["count"]) for group in sunday["reviews"]][:2] == [("2026-11-01", 2),
                                                                                    ("2026-11-04", 1)]


def test_a_checks_question_is_counted_once_as_the_check(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault")

    summary = _summary(paths, repository)
    reviewed = [item for group in summary["reviews"] for item in group["item_ids"]]
    checked = [item for group in summary["checks"] for item in group["item_ids"]]
    assert "pi_checked" in checked
    assert "pi_checked" not in reviewed  # due Tuesday on its own schedule, but the routine queue keeps it for the check
    assert len(reviewed) + len(checked) == len(set(reviewed) | set(checked))
    assert sum(group["count"] for group in summary["reviews"]) == len(reviewed)


def test_what_has_no_day_is_given_none(tmp_path, new_york):
    """Never answered, retired, held for review: none is given a day it does not have."""

    paths, repository = evening_vault(tmp_path / "vault")

    summary = _summary(paths, repository)
    days = {item: group["date"] for group in summary["reviews"] for item in group["item_ids"]}
    assert "pi_new" not in days  # no due date: no invented one
    assert "pi_retired" not in days  # due tomorrow, but never served
    # Answered this evening with a grade held for review: no review happened, so it keeps the day it had.
    assert days["pi_held"] == "2026-11-04"
    # Questions still being written have topics, never a date.
    assert set(summary["writing"]) == {"topic_count", "learning_object_ids"}


def test_minutes_only_where_an_estimate_supports_them(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)

    minutes = {group["date"]: group["minutes"] for group in _summary(paths, repository)["reviews"]}
    # Authored estimates (1 minute each) plus the plan's half minute of feedback.
    assert minutes["2026-11-01"] == 3.0
    # No authored estimate and no answer of that kind on record: the estimator's fallback constant is not named.
    assert minutes["2026-11-05"] is None


def test_nothing_due_tomorrow_names_the_nearest_later_day(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)
    with repository.connection() as connection:
        connection.execute("UPDATE practice_item_state SET due_at = '2026-11-09T15:00:00Z'"
                           " WHERE practice_item_id IN ('pi_tomorrow', 'pi_dst')")
        connection.commit()

    summary = _summary(paths, repository)
    assert [group["date"] for group in summary["reviews"]][0] == "2026-11-04"
    assert summary["next_review_date"] == "2026-11-04"
    assert summary["calendar"]["tomorrow"] not in [group["date"] for group in summary["reviews"]]


def test_whats_due_now_or_later_today_is_todays(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)
    with repository.connection() as connection:
        connection.execute("UPDATE practice_item_state SET due_at = '2026-10-29T15:00:00Z'"
                           " WHERE practice_item_id = 'pi_tomorrow'")
        connection.execute("UPDATE practice_item_state SET due_at = '2026-11-01T02:00:00Z'"
                           " WHERE practice_item_id = 'pi_dst'")  # 22:00 EDT this evening
        connection.commit()

    summary = _summary(paths, repository)
    assert summary["reviews"][0]["date"] == "2026-10-31"
    assert summary["reviews"][0]["item_ids"] == ["pi_dst", "pi_tomorrow"]
    assert summary["next_review_date"] == "2026-11-04"


def test_a_check_open_now_is_todays_and_an_expired_one_is_gone(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)
    lapsing_followups(repository)

    checks = _summary(paths, repository)["checks"]
    assert [(group["date"], group["item_ids"]) for group in checks] == [
        ("2026-10-31", ["pi_fallback"]),  # its day came yesterday: available now
        ("2026-11-14", ["pi_checked"]),
    ]


def test_sections_waiting_for_their_book_are_counted_apart(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)
    wait_for_build(repository)

    summary = _summary(paths, repository)
    assert summary["waiting"] == {"section_count": 1}
    assert summary["writing"] == {"topic_count": 0, "learning_object_ids": []}
    assert summary["held"] == {"topic_count": 0, "learning_object_ids": []}


def test_the_read_leaves_the_database_byte_identical(tmp_path, new_york):
    """The proof: the file's bytes and a full dump are the same after the read, with follow-ups a writable read of
    the due queue marks (an expired one, a due one) in the vault."""

    paths, repository = evening_vault(tmp_path / "vault")
    lapsing_followups(repository)
    before = database_fingerprint(paths.sqlite_path)

    _summary(paths, repository)

    assert database_fingerprint(paths.sqlite_path) == before


def test_a_writable_read_of_the_due_queue_would_have_changed_it(tmp_path, new_york):
    """Why the summary attaches read-only: the due queue's own read marks those follow-ups on a writable attach."""

    from learnloop.scheduling.scheduler import read_due_queue

    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)
    lapsing_followups(repository)
    before = database_fingerprint(paths.sqlite_path)

    read_due_queue(load_vault(paths.root), repository, clock=CLOCK)

    assert database_fingerprint(paths.sqlite_path) != before
    statuses = {task["case_ref"]: task["status"] for task in repository.followup_tasks_of_kind("cold_retry")}
    assert statuses == {"case_checked": "pending", "case_lapsed": "expired", "case_due": "served"}


def test_it_reads_nothing_through_the_callers_repository(tmp_path, new_york):
    """The caller's (writable) repository is used only for its path: a read through it could mark something."""

    paths, repository = evening_vault(tmp_path / "vault")

    class PathOnly:
        sqlite_path = repository.sqlite_path

    from learnloop.daily_plan.next_practice import next_practice

    assert next_practice(load_vault(paths.root), PathOnly(), clock=CLOCK) == EXPECTED


def test_as_of_is_the_instant_read(tmp_path, new_york):
    paths, repository = evening_vault(tmp_path / "vault", held=False, writing=False)
    assert _summary(paths, repository)["as_of"] == AS_OF.strftime("%Y-%m-%dT%H:%M:%SZ")
