"""The narrative job against a read snapshot, on a real production rollback-journal open.

``db.migrate.switch_to_wal`` leaves a vault in rollback mode when the linked SQLite has the WAL-reset bug
(``db.connection.wal_unavailable_reason``: below 3.44.6, 3.45.0 to 3.50.6, and 3.51.0 to 3.51.2). There a reader blocks a
commit, which WAL doesn't. A Today build holds AD's read snapshot while its background job commits the narrative
(tests/test_reader_rw6b_p2_landing.py runs that journey under WAL). Here the overlap is controlled: a reader is held
across the job, past the busy timeout (shortened from production's 5 s).
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta
import sqlite3
import threading

import pytest

from learnloop.db import connection as DBC
from learnloop.db import migrate as DBM
from learnloop.db.connection import connect
from learnloop.instructional import reader_digest as RN
from tests.curriculum_c1_plan_follows_path_helpers import _c1
from tests.reader_digest_narrative_helpers import NarrativeFake
from tests.reader_rw6b_p2_landing_helpers import _digest, _digest_row

pytestmark = pytest.mark.durability


@pytest.fixture
def rollback_c1(tmp_path, monkeypatch):
    monkeypatch.setattr(DBM, "wal_unavailable_reason", lambda version=None: "this test's old SQLite")
    c1 = _c1(tmp_path, monkeypatch)
    database = c1.repository.sqlite_path
    with closing(connect(database, read_only=True)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    with closing(connect(database)) as connection:
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2  # production's FULL
    _digest(c1)
    return c1


def _narrate_on_a_thread(c1, fake) -> list[BaseException]:
    failures: list[BaseException] = []

    def run() -> None:
        try:
            RN.narrate_waiting(c1.vault, c1.repository, now=c1.clock.moment, client=fake)
        except BaseException as failure:  # the sidecar's job logs this and retries at the next build
            failures.append(failure)

    thread = threading.Thread(target=run, name="narrative-under-a-reader")
    thread.start()
    thread.join(timeout=60)
    assert not thread.is_alive()
    return failures


def _after(moment: str) -> str:
    return (datetime.fromisoformat(moment.replace("Z", "+00:00")) + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _held_reader(c1):
    reader = connect(c1.repository.sqlite_path, read_only=True)
    reader.execute("BEGIN")
    assert reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] > 0
    return reader


def test_with_no_reader_the_narrative_lands_on_a_rollback_vault(rollback_c1):
    fake = NarrativeFake()
    assert _narrate_on_a_thread(rollback_c1, fake) == []
    assert fake.calls == 1 and _digest_row(rollback_c1)["narrative_md"] == fake.text


def test_a_reader_shorter_than_the_busy_timeout_only_delays_the_narrative(rollback_c1):
    """The commit retries for the busy timeout, so a read that ends within it costs a wait and nothing else."""

    reader = _held_reader(rollback_c1)
    fake = NarrativeFake()
    finished: list[list[BaseException]] = []
    worker = threading.Thread(target=lambda: finished.append(_narrate_on_a_thread(rollback_c1, fake)))
    worker.start()
    # Long enough for the job to reach its first commit, well inside the 5 s timeout.
    threading.Event().wait(0.5)
    reader.rollback()
    reader.close()
    worker.join(timeout=60)
    assert finished == [[]]
    assert fake.calls == 1 and _digest_row(rollback_c1)["narrative_md"] == fake.text


def test_a_reader_past_the_busy_timeout_doesnt_lose_the_narrative(rollback_c1, monkeypatch):
    """The sidecar logs the job's failure and says the next build retries. That build must write it."""

    monkeypatch.setattr(DBC, "BUSY_TIMEOUT_MS", 100)
    reader = _held_reader(rollback_c1)
    first = NarrativeFake()
    failures = _narrate_on_a_thread(rollback_c1, first)
    reader.rollback()
    reader.close()
    assert failures and all(isinstance(failure, sqlite3.OperationalError) for failure in failures), failures
    assert _digest_row(rollback_c1).get("narrative_md") is None
    # The next Today build's job, with the reader gone.
    second = NarrativeFake()
    results = _narrate_on_a_thread(rollback_c1, second)
    assert results == []
    assert second.calls == 1 and _digest_row(rollback_c1)["narrative_md"] == second.text


def test_a_reader_arriving_after_the_claim_delays_the_narrative_by_the_lease_and_doesnt_lose_it(rollback_c1, monkeypatch):
    """The overlap the sidecar actually has: the job holds its claim when a Today build's snapshot starts. Its renewal
    and its release both fail, so the claim stays until its lease lapses. Builds meanwhile get "claimed", no model is
    asked twice, and the first build after the lease writes the narrative. A delay on a rollback vault, not a loss."""

    from learnloop.hints import map_builder as claims

    monkeypatch.setattr(DBC, "BUSY_TIMEOUT_MS", 100)
    real_renew = claims._renew_live
    readers: list[sqlite3.Connection] = []

    def renew_under_a_reader(repository, claim):
        if not readers:
            reader = sqlite3.connect(repository.sqlite_path, check_same_thread=False)
            reader.execute("BEGIN")
            reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
            readers.append(reader)
        return real_renew(repository, claim)

    monkeypatch.setattr(claims, "_renew_live", renew_under_a_reader)
    first = NarrativeFake()
    failures = _narrate_on_a_thread(rollback_c1, first)
    assert [type(failure) for failure in failures] == [sqlite3.OperationalError] and first.calls == 0
    readers[0].rollback()
    readers[0].close()
    monkeypatch.setattr(claims, "_renew_live", real_renew)

    within_the_lease = NarrativeFake()
    results = RN.narrate_waiting(rollback_c1.vault, rollback_c1.repository, now=rollback_c1.clock.moment,
                                 client=within_the_lease)
    assert [result.status for result in results] == ["claimed"] and within_the_lease.calls == 0
    assert _digest_row(rollback_c1).get("narrative_md") is None

    with closing(connect(rollback_c1.repository.sqlite_path, read_only=True)) as connection:
        lease_expires_at = connection.execute("SELECT lease_expires_at FROM judgment_work_claims").fetchone()[0]
    monkeypatch.setattr(claims, "_lease_now", lambda: _after(lease_expires_at))
    after_the_lease = NarrativeFake()
    results = RN.narrate_waiting(rollback_c1.vault, rollback_c1.repository, now=rollback_c1.clock.moment,
                                 client=after_the_lease)
    assert [result.status for result in results] == ["narrated"] and after_the_lease.calls == 1
    assert _digest_row(rollback_c1)["narrative_md"] == after_the_lease.text
