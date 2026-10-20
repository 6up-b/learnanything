"""Reader workbench RW3b, fix round 6 (docs/reviews/reader-rw3b-codex-review.md).

F16: ``cues.max_calls_per_source_per_day`` counts a rolling 24 hours in UTC,
so no timezone or DST rule refills it. Each case runs discovery with the
machine in New York and a frozen clock over receipts already stored: the
fall-back (2026-11-01), the spring-forward (2026-03-08), an ordinary local
midnight, and the window's own edge (a receipt 24 h + 1 s old drops out).
Fakes for every model.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.source_retrieval import passage_cues as PC
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded


@pytest.fixture
def new_york():
    """The machine's local time is New York's for the test (restored after)."""

    before = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"
    time.tzset()
    try:
        yield
    finally:
        if before is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = before
        time.tzset()


def _receipts(repository, started: list[datetime]) -> None:
    """Root receipts of the cue judge for ext_text, as a run writes them."""

    with repository.connection() as connection:
        for index, at in enumerate(started):
            connection.execute(
                "INSERT INTO model_call_receipts (id, parent_call_id, owner_kind, owner_id, purpose, status, "
                "started_at) VALUES (?, NULL, 'passage_cue_judge', ?, 'passage_cue_judge', 'completed', ?)",
                (f"call_r6_{index}", f"ext_text|misconception:seeded_{index}|s", at.astimezone(UTC).isoformat()))
        connection.commit()


def _more_targets(repository, count: int) -> None:
    for index in range(count):
        repository.insert_misconception(id=f"mis_r6_{index}", learning_object_id="lo_matrices", status="active",
                                        statement=f"Swapping rows of a matrix keeps its determinant, variant {index}")


def _run_at(paths, repository, now: datetime) -> CueJudgeFake:
    judge = CueJudgeFake()
    PC.discover(loaded(paths), repository, "ext_text", client=judge, clock=FrozenClock(now.astimezone(UTC)))
    return judge


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone(UTC)


def test_the_fall_back_never_refills_the_allowance(tmp_path, new_york):
    # 36 calls at 00:30 EDT on 2026-11-01 (04:30Z); at 02:00 EST (07:00Z) the
    # old local-midnight rule put midnight at 05:00Z and counted none of them.
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    _receipts(repository, [_utc("2026-11-01T04:30:00+00:00")] * 36)
    judge = _run_at(paths, repository, _utc("2026-11-01T07:00:00+00:00"))
    assert judge.prompts == [], f"{len(judge.prompts)} more calls after the fall-back (36 already in 24 h)"


def test_the_spring_forward_keeps_the_last_24_hours_counted(tmp_path, new_york):
    # 36 calls at 22:50 EST on 2026-03-07 (03:50Z on the 8th); at 03:10 EDT (07:10Z)
    # the old rule put midnight at 04:00Z (the EDT offset) and counted none of them.
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    _receipts(repository, [_utc("2026-03-08T03:50:00+00:00")] * 36)
    judge = _run_at(paths, repository, _utc("2026-03-08T07:10:00+00:00"))
    assert judge.prompts == []


def test_an_ordinary_local_midnight_does_not_refill_the_allowance(tmp_path, new_york):
    # 36 calls at 23:30 EDT on 2026-10-19 (03:30Z on the 20th); at 00:30 EDT on the 20th.
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    _receipts(repository, [_utc("2026-10-20T03:30:00+00:00")] * 36)
    judge = _run_at(paths, repository, _utc("2026-10-20T04:30:00+00:00"))
    assert judge.prompts == []


def test_a_receipt_24_hours_and_a_second_old_drops_out_of_the_window(tmp_path, new_york):
    now = _utc("2026-10-20T16:00:00+00:00")  # noon in New York
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    _more_targets(repository, 3)
    inside = now - timedelta(hours=24) + timedelta(seconds=1)
    outside = now - timedelta(hours=24) - timedelta(seconds=1)
    # 35 calls just inside the window (yesterday morning, local) and one just outside it.
    _receipts(repository, [inside] * 35 + [outside])
    judge = _run_at(paths, repository, now)
    assert len(judge.prompts) == 1, "one call left in the rolling 24 hours"
    assert PC.discovery_calls_last_24h(repository, "ext_text", clock=FrozenClock(now)) == 36
