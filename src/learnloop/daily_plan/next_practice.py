"""What comes next, dated: the session's finish and Today say it from this one read.

``next_practice`` reads, at one instant and through a read-only attach of the vault's database:

* the review population the plan admits (:func:`learnloop.daily_plan.engine.review_population`, with the intent view
  the plan's build reads), each item at its effective due, grouped by the local calendar day that due falls on;
* the checks on your own kept for later (open ``followup_tasks`` of the cold kinds), grouped by the day their
  ``not_before`` falls on. A check's chosen question is counted as the check, never again as a review: the routine
  queue holds it back for the check;
* the question work under way, apart from both: topics whose questions are being written, finished sections whose
  writing waits for their book or the desktop, and topics whose written questions wait for a look.

It schedules nothing, builds no plan and writes nothing. The attach is read-only because the reads it shares with
serving have lazy marks on a writable attach (``Repository.due_followup_tasks`` expires and serves follow-up tasks):
on this attach they are skipped, and any other write would fail rather than land.

Days are the plan's (:func:`learnloop.daily_plan.engine.local_date`): the machine's local calendar, each instant
converted with the offset in force at that instant, so a daylight-saving change moves no due onto the wrong day.

Minutes are the plan's own estimates (``daily_plan.estimates``); a day's minutes are left out (``None``) when any of
its items rests on nothing but the estimator's fallback constant (no authored estimate, no answer of the learner's on
it or on its kind of question): the words then name no minutes rather than a number nothing supports.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc

#: The follow-up kinds served as a check on your own (``serve_eligibility.COLD_FOLLOWUP_TASK_KINDS``).
_CHECK_KINDS = ("cold_retry", "certification_cold_probe")
#: An ingest job still going (``add_source._active`` reads the same statuses; ``waiting_for_input`` waits on the
#: learner, so it is not writing).
_WRITING_JOB_STATUSES = ("queued", "running")


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _local_day(moment: datetime) -> date:
    """The plan's calendar day of an instant: the local zone's offset at that instant, not now's."""

    return moment.astimezone().date()


def _day_start(day: date) -> datetime:
    # A naive local midnight resolved in the local zone takes that midnight's own offset (``local_day_start_iso``).
    return datetime.combine(day, time()).astimezone()


def _supported(estimate: Any) -> bool:
    return estimate.prior_source != "fallback" or estimate.n_item > 0 or estimate.n_mode > 0


def next_practice(vault: Any, repository: Any, *, clock: Clock | None = None) -> dict[str, Any]:
    """The dated summary at ``clock``'s now (see the module's docstring). ``repository`` names the database; it is
    read through a read-only attach of the same file, never through ``repository`` itself."""

    from learnloop.daily_plan.engine import review_population
    from learnloop.daily_plan.estimates import Estimator, load_duration_evidence
    from learnloop.db.repositories import Repository
    from learnloop.scheduling.intent.serving import intent_serving
    from learnloop.vault.lifecycle import practice_item_servable

    now = (clock or SystemClock()).now().astimezone(UTC)
    today = _local_day(now)
    reader = Repository.attach(repository.sqlite_path, read_only=True)
    plan_config = vault.config.plan
    estimator = Estimator(
        evidence=load_duration_evidence(reader, latency_cap_minutes=float(plan_config.latency_cap_minutes)),
        read_words_per_minute=int(plan_config.read_words_per_minute),
    )
    estimates: dict[str, Any] = {}

    def minutes(item_id: str) -> float:
        item = vault.practice_items.get(item_id)
        estimates[item_id] = estimator.estimate(
            item_id, getattr(item, "practice_mode", None), getattr(item, "expected_minutes", None)
        )
        return estimator.item_minutes(vault, item_id)

    intent = intent_serving(vault, reader, now=now)
    population = review_population(vault, reader, intent, minutes=minutes)

    checks = _open_checks(reader, now)
    check_items = {str(task["selected_item_id"]) for task in checks if task["selected_item_id"]}

    def learning_object(item_id: str) -> str | None:
        item = vault.practice_items.get(item_id)
        return getattr(item, "learning_object_id", None) if item is not None else None

    reviews: dict[date, list[tuple[str, float]]] = {}
    for review in population:
        if review.practice_item_id in check_items:
            continue
        due = parse_utc(review.due_at)
        if due is None:
            continue
        day = max(_local_day(due), today)
        reviews.setdefault(day, []).append((review.practice_item_id, float(review.est_minutes)))

    check_days: dict[date, list[Mapping[str, Any]]] = {}
    for task in checks:
        item_id = task["selected_item_id"]
        if item_id:
            item = vault.practice_items.get(item_id)
            # A check whose question is gone or retired cannot be served on its day: it is no promise to name.
            if item is None or item.status != "active" or not practice_item_servable(vault, item):
                continue
        not_before = parse_utc(task["not_before"])
        if not_before is None:
            continue
        check_days.setdefault(max(_local_day(not_before), today), []).append(task)

    def group(day: date, entries: list[tuple[str, float]]) -> dict[str, Any]:
        item_ids = [item_id for item_id, _minutes in sorted(entries)]
        supported = all(item_id in estimates and _supported(estimates[item_id]) for item_id in item_ids)
        return {
            "date": day.isoformat(),
            "count": len(item_ids),
            "item_ids": item_ids,
            "learning_object_ids": _unique(learning_object(item_id) for item_id in item_ids),
            "minutes": round(sum(value for _item_id, value in entries), 4) if supported else None,
        }

    def check_group(day: date, tasks: list[Mapping[str, Any]]) -> dict[str, Any]:
        ordered = sorted(tasks, key=lambda task: (str(task["not_before"]), str(task["id"])))
        item_ids = _unique(task["selected_item_id"] for task in ordered)
        return {
            "date": day.isoformat(),
            "count": len(ordered),
            "item_ids": item_ids,
            "learning_object_ids": _unique(
                task["learning_object_id"] or (learning_object(task["selected_item_id"])
                                               if task["selected_item_id"] else None)
                for task in ordered
            ),
            "kinds": _unique(task["kind"] for task in ordered),
        }

    review_groups = [group(day, reviews[day]) for day in sorted(reviews)]
    later = [entry["date"] for entry in review_groups if entry["date"] > today.isoformat()]
    tomorrow = today + timedelta(days=1)
    return {
        "as_of": _iso(now),
        "calendar": {
            "zone": now.astimezone().tzname() or "",
            "today": today.isoformat(),
            "tomorrow": tomorrow.isoformat(),
            "next_day_starts_at": _iso(_day_start(tomorrow)),
        },
        "reviews": review_groups,
        "checks": [check_group(day, check_days[day]) for day in sorted(check_days)],
        "next_review_date": later[0] if later else None,
        **_question_work(reader),
    }


def next_practice_or_none(vault: Any, repository: Any, *, clock: Clock | None = None) -> dict[str, Any] | None:
    """:func:`next_practice` for a reply that must not fail on it: ``None`` (the screens then say nothing of it)."""

    try:
        return next_practice(vault, repository, clock=clock)
    except Exception:  # noqa: BLE001 - the session's end and Today stand without it
        logging.getLogger(__name__).warning("could not read what comes next", exc_info=True)
        return None


def _unique(values: Iterable[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


def _open_checks(reader: Any, now: datetime) -> list[Mapping[str, Any]]:
    """The checks on your own still to come or open now: not taken, not expired."""

    marks = ", ".join("?" for _ in _CHECK_KINDS)
    with reader.connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, kind, not_before, selected_item_id, learning_object_id FROM followup_tasks
            WHERE kind IN ({marks}) AND status IN ('pending', 'served')
              AND (expires_at IS NULL OR expires_at >= ?)
            """,
            (*_CHECK_KINDS, _iso(now)),
        ).fetchall()
    return [dict(row) for row in rows]


def _question_work(reader: Any) -> dict[str, Any]:
    """The question work under way, by what it waits on: ``writing`` (topics an unfinished writing job has not
    finished: its payload's topics less the parts it wrote or stopped on), ``waiting`` (finished sections whose
    writing waits for their book's topics or for the desktop) and ``held`` (topics whose written questions wait for a
    look). A variant written for adaptive difficulty is no new topic's questions and is not counted."""

    from learnloop.db.stores.reader import (
        SECTION_DEFERRED_TO_PRIMARY,
        SECTION_ENQUEUING,
        SECTION_WAITING_FOR_BUILD,
    )

    statuses = ", ".join("?" for _ in _WRITING_JOB_STATUSES)
    waiting_stamps = (SECTION_WAITING_FOR_BUILD, SECTION_DEFERRED_TO_PRIMARY, SECTION_ENQUEUING)
    stamps = ", ".join("?" for _ in waiting_stamps)
    with reader.connection() as connection:
        jobs = connection.execute(
            f"SELECT payload_json FROM ingest_jobs WHERE job_type = 'practice_expansion' AND status IN ({statuses})"
            " ORDER BY created_at, id",
            _WRITING_JOB_STATUSES,
        ).fetchall()
        waiting = connection.execute(
            f"SELECT COUNT(*) FROM reader_section_progress WHERE completed_at IS NOT NULL"
            f" AND generation_batch_id IN ({stamps})",
            waiting_stamps,
        ).fetchone()[0]
        held = [str(row[0]) for row in connection.execute(
            "SELECT learning_object_id FROM reader_topic_question_work WHERE state = 'held' ORDER BY rowid"
        )]
    writing: list[str] = []
    for row in jobs:
        try:
            payload = json.loads(row[0]) if row[0] else {}
        except ValueError:
            logging.getLogger(__name__).warning("a writing job's payload could not be read")
            continue
        if not isinstance(payload, Mapping) or payload.get("ad_commission_id"):
            continue
        finished = {str(part.get("topic_id")) for part in payload.get("question_parts") or []
                    if isinstance(part, Mapping) and (part.get("patch_id") or part.get("error"))}
        writing.extend(str(lo) for lo in payload.get("learning_object_ids") or [] if str(lo) not in finished)
    writing = _unique(writing)
    held = _unique(held)
    return {
        "writing": {"topic_count": len(writing), "learning_object_ids": writing},
        "waiting": {"section_count": int(waiting)},
        "held": {"topic_count": len(held), "learning_object_ids": held},
    }


__all__ = ["next_practice", "next_practice_or_none"]
