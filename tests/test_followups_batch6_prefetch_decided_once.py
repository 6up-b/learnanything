"""Follow-ups batch 6, landing step 0: a candidate is decided once for its trigger.

A decision's horizon closing took away the only thing that kept its candidate from being decided
again (the open request key), while a plan trigger went on offering the plan's reading after the
plan had ended. So every ``get_daily_plan`` read after the end decided each unbuilt candidate again:
a new row and a fresh Thompson draw per read, and repeated draws until one builds, which makes the
logged propensity understate the real chance of a build. The same held for a ``section`` trigger
once the next section was marked read: every progress report on the earlier one decided again.

Now an ended plan offers nothing (the same instant ``horizon_at`` closes its decisions on), and a
candidate already decided for its trigger is not decided again. Fakes for the judge and the author;
the real pass, its real model and real ``daily_plans`` and ``reader_section_progress`` rows.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.figures import prefetch as PF
from learnloop.figures import prefetch_model as PM
from learnloop.figures import service as FS
from tests.figure_fixtures import EXTRACTION, AuthorFake
from tests.test_figures_prefetch import TWO, JudgeFake, count, decisions, env_for, make_vault, mains, plan_record  # noqa: F401

NOON = datetime(2099, 1, 15, 12, 0, tzinfo=UTC)
PLAN = "dp_1"


def _clock(hours: float = 0.0) -> FrozenClock:
    return FrozenClock(NOON + timedelta(hours=hours))


def _plan_row(repository: Any, env: PF.PrefetchEnv, plan_id: str = PLAN) -> None:
    with repository.connection() as connection:
        at = NOON.isoformat()
        connection.execute(
            "INSERT INTO daily_plans(id, local_date, kind, minutes_budget, remembered_minutes, minutes_source, "
            "split_json, admission_json, estimator_version, source, chooser, status, algorithm_version, config_hash, "
            "created_at, updated_at) VALUES (?, ?, 'normal', 60, 60, 'chip', '{}', '{}', 'x', 'x', 'x', 'open', "
            "'mvp-0.43', 'h', ?, ?)", (plan_id, env.today(), at, at))
        connection.commit()


def _end_plan(repository: Any, status: str, *, plan_id: str = PLAN, hours: float = 1.0) -> None:
    at = (NOON + timedelta(hours=hours)).isoformat()
    with repository.connection() as connection:
        connection.execute("UPDATE daily_plans SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
                           (status, at, at, plan_id))
        connection.commit()


def _reopen_plan(repository: Any, *, plan_id: str = PLAN, hours: float = 1.5) -> None:
    """As the engine reopens one (a raised budget, RW7b's path reading): status open, no completion."""

    with repository.connection() as connection:
        connection.execute("UPDATE daily_plans SET status = 'open', completed_at = NULL, stop_reason = NULL, "
                           "updated_at = ? WHERE id = ?", ((NOON + timedelta(hours=hours)).isoformat(), plan_id))
        connection.commit()


@pytest.fixture
def skips(monkeypatch):
    """The real model's real draw, its verdict turned to skip so the candidate stays unbuilt (a built
    one is kept out by ``already_built``, which hid this). Records every decision made."""

    made: list[Any] = []
    real = PM.Model.decide

    def decide(self: Any, candidate: Any, rng: Any) -> Any:
        made.append(candidate)
        return replace(real(self, candidate, rng), build=False)

    monkeypatch.setattr(PM.Model, "decide", decide)
    return made


def _passes(vault: Any, repository: Any, trigger: PF.Trigger, *, hours: float, n: int = 3, judge: Any = None,
            author: Any = None) -> PF.PrefetchEnv:
    """``n`` passes at the clock's hour, one generator through them (as one sidecar's reads)."""

    env = env_for(vault, repository, clock=_clock(hours), judge=judge, author=author)
    for _ in range(n):
        PF.run_trigger(env, trigger)
    return env


def _unchanged_by(vault: Any, repository: Any, trigger: PF.Trigger, skips: list[Any], *, hours: float) -> None:
    """Further passes add no decision row and no draw."""

    rows, made = count(repository, "figure_prefetch_decisions"), len(skips)
    env = env_for(vault, repository, clock=_clock(hours))
    state = env.rng.bit_generator.state
    for _ in range(3):
        result = PF.run_trigger(env, trigger)
        assert result.decisions == []
    assert count(repository, "figure_prefetch_decisions") == rows
    assert len(skips) == made
    assert env.rng.bit_generator.state == state


@pytest.mark.parametrize("status", ["complete", "stopped", "abandoned"])
def test_passes_before_and_after_a_plan_ends_decide_once(tmp_path, monkeypatch, skips, status):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    _plan_row(repository, env_for(vault, repository, clock=_clock()))
    trigger = PF.Trigger("plan", PLAN)

    _passes(vault, repository, trigger, hours=0)  # the first decides; the rest find its key open
    (row,) = decisions(repository)
    assert row["decision"] == "skip" and row["outcome"] is None and len(skips) == 1
    _unchanged_by(vault, repository, trigger, skips, hours=0.5)

    _end_plan(repository, status)
    # The pass that closes the decision adds none, nor does any after it (one read per 30 s, before).
    _unchanged_by(vault, repository, trigger, skips, hours=1.5)
    (closed,) = decisions(repository)
    assert closed["id"] == row["id"] and closed["outcome"] == "neither"
    _unchanged_by(vault, repository, trigger, skips, hours=2)


def test_a_plan_whose_day_ended_still_open_decides_nothing_more(tmp_path, monkeypatch, skips):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    _plan_row(repository, env_for(vault, repository, clock=_clock()))
    trigger = PF.Trigger("plan", PLAN)
    _passes(vault, repository, trigger, hours=0)
    _unchanged_by(vault, repository, trigger, skips, hours=48)  # status still 'open', its local day over
    (row,) = decisions(repository)
    assert row["outcome"] == "neither"
    _unchanged_by(vault, repository, trigger, skips, hours=49)


def test_a_plan_that_ended_before_any_decision_calls_and_builds_nothing(tmp_path, monkeypatch):
    # Nothing judged while it was open (on battery all day, say): no judge call and no build for it now.
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    _plan_row(repository, env_for(vault, repository, clock=_clock()))
    _end_plan(repository, "complete")
    judge, author = JudgeFake(), AuthorFake()
    _passes(vault, repository, PF.Trigger("plan", PLAN), hours=2, judge=judge, author=author)
    assert decisions(repository) == []
    assert judge.calls == 0 and author.calls == 0


def test_a_built_decision_is_not_built_again_for_an_ended_plan(tmp_path, monkeypatch):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    _plan_row(repository, env_for(vault, repository, clock=_clock()))
    judge, author = JudgeFake(), AuthorFake()
    _passes(vault, repository, PF.Trigger("plan", PLAN), hours=0, judge=judge, author=author)
    (row,) = decisions(repository)
    assert row["decision"] == "build" and author.calls == 1
    _end_plan(repository, "complete")
    _passes(vault, repository, PF.Trigger("plan", PLAN), hours=2, judge=judge, author=author)
    assert [item["id"] for item in decisions(repository)] == [row["id"]]
    assert judge.calls == 1 and author.calls == 1


def test_a_reopened_plan_keeps_its_decision(tmp_path, monkeypatch, skips):
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    _plan_row(repository, env_for(vault, repository, clock=_clock()))
    trigger = PF.Trigger("plan", PLAN)
    _passes(vault, repository, trigger, hours=0)
    _end_plan(repository, "complete")
    _unchanged_by(vault, repository, trigger, skips, hours=1.2)
    _reopen_plan(repository)
    _unchanged_by(vault, repository, trigger, skips, hours=2)
    (row,) = decisions(repository)
    assert row["outcome"] == "neither"  # set once; reopening does not undo it


def test_the_next_plan_decides_for_itself(tmp_path, monkeypatch, skips):
    # A candidate is decided once per plan, not once ever: a later plan is a new trigger.
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    env = env_for(vault, repository, clock=_clock())
    _plan_row(repository, env)
    _passes(vault, repository, PF.Trigger("plan", PLAN), hours=0)
    _end_plan(repository, "stopped")
    _unchanged_by(vault, repository, PF.Trigger("plan", PLAN), skips, hours=1.2)

    plan_record(monkeypatch, plan_id="dp_2")
    _plan_row(repository, env, plan_id="dp_2")
    _passes(vault, repository, PF.Trigger("plan", "dp_2"), hours=2)
    assert sorted(row["trigger_ref"] for row in decisions(repository)) == [PLAN, "dp_2"]
    assert len(skips) == 2
    _unchanged_by(vault, repository, PF.Trigger("plan", "dp_2"), skips, hours=3)


def test_section_passes_after_the_next_section_is_read_decide_nothing_more(tmp_path, skips):
    # The learner has read s2 and is back in s1: every progress report on s1 is this trigger.
    _paths, repository, vault = make_vault(tmp_path, two=True)
    trigger = PF.Trigger("section", f"{TWO}:s1", extraction_id=TWO, section_id="s1")
    _passes(vault, repository, trigger, hours=0)
    (row,) = decisions(repository)
    assert row["trigger_ref"] == f"{TWO}:s2" and row["outcome"] is None
    repository.upsert_reader_section_progress(extraction_id=TWO, section_id="s2", spans_seen=3, span_count=3,
                                              completed=True)
    _unchanged_by(vault, repository, trigger, skips, hours=1)
    (closed,) = decisions(repository)
    assert closed["id"] == row["id"] and closed["outcome"] == "neither"
    _unchanged_by(vault, repository, trigger, skips, hours=2)


def test_a_passage_released_after_a_void_decision_may_be_decided(tmp_path, monkeypatch, skips):
    # ``void`` reports a passage withheld, not a decision the candidate can keep: it is changed input.
    _paths, repository, vault = make_vault(tmp_path)
    plan_record(monkeypatch)
    _plan_row(repository, env_for(vault, repository, clock=_clock()))
    trigger = PF.Trigger("plan", PLAN)
    _passes(vault, repository, trigger, hours=0)
    (row,) = decisions(repository)
    spans = {str(span) for span in json.loads(row["anchor_json"])["span_ids"]}
    real = FS.withheld_message
    with monkeypatch.context() as held:
        held.setattr(FS, "withheld_message",
                     lambda v, r, e, ids: "held out" if e == EXTRACTION and spans & {str(i) for i in ids}
                     else real(v, r, e, ids))
        assert PF.close_horizons(env_for(vault, repository, clock=_clock(0.5))) == 1
    assert decisions(repository)[0]["outcome"] == "void"
    _passes(vault, repository, trigger, hours=0.6)
    assert sorted(item["outcome"] or "" for item in decisions(repository)) == ["", "void"]
    assert len(skips) == 2
    _unchanged_by(vault, repository, trigger, skips, hours=0.7)
