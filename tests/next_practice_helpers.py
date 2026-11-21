"""The dated next-practice summary's fixture, shared by ``tests/test_next_practice.py`` and the session finish's tests
in ``tests/test_ux_phase4_feedback.py`` (a test file never imports another).

The learner's evening is Saturday 31 October 2026, 19:00 in New York (EDT, UTC-4); daylight saving ends at 02:00 the
next morning, so Sunday 1 November is 25 hours long. The vault holds:

* ``pi_tomorrow``: due Sunday 09:00 EST;
* ``pi_dst``: due Sunday 23:30 EST, 28.5 hours on: still Sunday, though a fixed UTC-4 offset would put it on Monday;
* ``pi_checked``: due Tuesday, but kept for a check on your own from Saturday 14 November (fourteen days on);
* ``pi_held``: due Wednesday; answered this evening with a grade held for review (no review: it keeps its day);
* ``pi_fallback``: due Thursday, with no authored estimate and no answer of its kind (no minutes to name);
* ``pi_nine``: due Monday 9 November (nine days on);
* ``pi_new``: never answered (no due date); ``pi_retired``: due Sunday, but retired (not served);
* a writing job with four topics, one of them written (three still being written), a variant job for adaptive
  difficulty and a finished job (neither counted), and one topic whose written questions wait for a look.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.helpers import create_daily_plan_vault, write_yaml

ZONE = "America/New_York"
AS_OF = datetime(2026, 10, 31, 23, 0, tzinfo=UTC)
CLOCK = FrozenClock(AS_OF)

DUE = {
    "pi_tomorrow": "2026-11-01T14:00:00Z",
    "pi_dst": "2026-11-02T04:30:00Z",
    "pi_checked": "2026-11-03T15:00:00Z",
    "pi_held": "2026-11-04T15:00:00Z",
    "pi_fallback": "2026-11-05T15:00:00Z",
    "pi_nine": "2026-11-09T15:00:00Z",
    "pi_retired": "2026-11-01T14:00:00Z",
}
CHECK_NOT_BEFORE = "2026-11-14T15:00:00Z"

LEARNING_OBJECTS = {
    "lo_tomorrow": [("pi_tomorrow", 1.0), ("pi_dst", 1.0)],
    "lo_checked": [("pi_checked", 1.0)],
    "lo_held": [("pi_held", 1.0)],
    "lo_fallback": [("pi_fallback", None)],
    "lo_nine": [("pi_nine", 2.0)],
    "lo_new": [("pi_new", 1.0)],
    "lo_retired": [("pi_retired", 1.0)],
}


@pytest.fixture
def new_york():
    """The plan's calendar is the machine's local one: New York, for every test that reads days."""

    earlier = os.environ.get("TZ")
    os.environ["TZ"] = ZONE
    time.tzset()
    try:
        yield
    finally:
        if earlier is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = earlier
        time.tzset()


def retire(paths, item_id: str) -> None:
    path = paths.practice_item_path("linear-algebra", item_id)
    data = load_vault(paths.root).practice_items[item_id].model_dump(mode="json", exclude_none=True)
    data["status"] = "retired"
    write_yaml(path, data)


def evening_vault(root: Path, *, held: bool = True, writing: bool = True):
    """The vault above; returns ``(paths, repository)``."""

    from learnloop.db.repositories import Repository

    paths = create_daily_plan_vault(root, learning_objects=LEARNING_OBJECTS)
    retire(paths, "pi_retired")
    repository = Repository(paths.sqlite_path)
    for item_id, due in DUE.items():
        repository.upsert_practice_item_state(item_id, difficulty=5.0, stability=4.0, due_at=due,
                                              last_attempt_at="2026-10-28T15:00:00Z", active=True)
    repository.create_followup_task(kind="cold_retry", case_kind="misconception", case_ref="case_checked",
                                    not_before=CHECK_NOT_BEFORE, selected_item_id="pi_checked",
                                    learning_object_id="lo_checked", clock=CLOCK)
    if held:
        from tests.held_grade_evidence_helpers import _held_apply

        _held_apply(load_vault(paths.root), repository, "pi_held", {"correctness": 0.0},
                    attempt_id="att_held", when=datetime(2026, 10, 31, 22, 30, tzinfo=UTC))
    if writing:
        question_work(repository)
    return paths, repository


def question_work(repository) -> None:
    """Three topics still being written, two jobs that are not, and one topic whose questions wait for a look."""

    jobs = (
        ("job_writing", "running", {"learning_object_ids": ["lo_a", "lo_b", "lo_c", "lo_d"], "reason": "reader",
                                    "question_parts": [{"topic_id": "lo_a", "patch_id": "patch_a"}]}),
        ("job_variant", "queued", {"learning_object_ids": ["lo_e"], "ad_commission_id": "commission_1"}),
        ("job_done", "completed", {"learning_object_ids": ["lo_f"], "reason": "reader"}),
    )
    for job_id, status, payload in jobs:
        batch_id = f"batch_{job_id}"
        repository.insert_ingest_batch(id=batch_id, workflow_type="practice_expansion", clock=CLOCK)
        repository.insert_ingest_job(id=job_id, batch_id=batch_id, ordinal=0, job_type="practice_expansion",
                                     payload=payload, clock=CLOCK)
        with repository.connection() as connection:
            connection.execute("UPDATE ingest_jobs SET status = ? WHERE id = ?", (status, job_id))
            connection.commit()
    repository.insert_topic_question_work([{
        "id": "work_held", "learning_object_id": "lo_g", "trigger_event": "section_finished", "work_key": "key_g",
        "batch_id": "batch_job_done", "source_id": "src_1", "extraction_id": "ext_1", "section_id": "sec_1",
    }], clock=CLOCK)
    repository.update_topic_question_work("work_held", state="held", clock=CLOCK)


def wait_for_build(repository, section_id: str = "sec_waiting") -> None:
    """A finished section whose questions wait for its book's topics."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO reader_section_progress(extraction_id, section_id, spans_seen, span_count, completed_at,"
            " generation_batch_id, updated_at) VALUES ('ext_1', ?, 3, 3, ?, 'waiting_for_build', ?)",
            (section_id, "2026-10-31T22:00:00Z", "2026-10-31T22:00:00Z"),
        )
        connection.commit()


def lapsing_followups(repository) -> None:
    """Follow-ups a writable read of the due queue marks: one expired (``expired``), one due (``served``)."""

    repository.create_followup_task(kind="cold_retry", case_kind="misconception", case_ref="case_lapsed",
                                    not_before="2026-10-20T15:00:00Z", expires_at="2026-10-25T15:00:00Z",
                                    selected_item_id="pi_nine", clock=CLOCK)
    repository.create_followup_task(kind="cold_retry", case_kind="misconception", case_ref="case_due",
                                    not_before="2026-10-30T15:00:00Z", selected_item_id="pi_fallback", clock=CLOCK)


def database_fingerprint(sqlite_path: Path) -> tuple[str, list[str]]:
    """The database file's bytes and its write-ahead log's, if any (hashed), and every row of every table, dumped."""

    import sqlite3

    digest = hashlib.sha256()
    for path in (Path(sqlite_path), Path(f"{sqlite_path}-wal")):
        digest.update(path.read_bytes() if path.exists() else b"")
    connection = sqlite3.connect(f"{Path(sqlite_path).resolve().as_uri()}?mode=ro", uri=True)
    try:
        dump = list(connection.iterdump())
    finally:
        connection.close()
    return digest.hexdigest(), dump


#: The summary of the evening above, as the sidecar says it before camel case.
EXPECTED = {
    "as_of": "2026-10-31T23:00:00Z",
    "calendar": {"zone": "EDT", "today": "2026-10-31", "tomorrow": "2026-11-01",
                 "next_day_starts_at": "2026-11-01T04:00:00Z"},
    "reviews": [
        {"date": "2026-11-01", "count": 2, "item_ids": ["pi_dst", "pi_tomorrow"],
         "learning_object_ids": ["lo_tomorrow"], "minutes": 3.0},
        {"date": "2026-11-04", "count": 1, "item_ids": ["pi_held"], "learning_object_ids": ["lo_held"],
         "minutes": 1.5},
        {"date": "2026-11-05", "count": 1, "item_ids": ["pi_fallback"], "learning_object_ids": ["lo_fallback"],
         "minutes": None},
        {"date": "2026-11-09", "count": 1, "item_ids": ["pi_nine"], "learning_object_ids": ["lo_nine"],
         "minutes": 2.5},
    ],
    "checks": [
        {"date": "2026-11-14", "count": 1, "item_ids": ["pi_checked"], "learning_object_ids": ["lo_checked"],
         "kinds": ["cold_retry"]},
    ],
    "next_review_date": "2026-11-01",
    "writing": {"topic_count": 3, "learning_object_ids": ["lo_b", "lo_c", "lo_d"]},
    "waiting": {"section_count": 0},
    "held": {"topic_count": 1, "learning_object_ids": ["lo_g"]},
}


def as_json(value) -> str:
    return json.dumps(value, sort_keys=True)
