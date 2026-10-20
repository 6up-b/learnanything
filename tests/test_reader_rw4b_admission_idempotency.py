"""Reader RW4b fix round 5, ruling R1 (Codex final verify F2, reopened): a
picked exercise's admission is idempotent across a failure, not only across a
success. The learner pick carries a durable identity derived from the
workbench session id (``admission_key``), stored with the pick's plan
receipt; a retry finds that pick and its serve and completes only the missing
admission write. With an injected ``database is locked`` on the final write,
the plan holds one receipt and one presentation for the pick.

Daily-plan vaults (the plan live), fakes only; no model call.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any

import pytest

from learnloop.daily_plan.engine import build_plan, learner_pick, stop_today
from learnloop.db.connection import connect
from learnloop.reader import workbench as WB
from learnloop_sidecar.handlers import workbench as handler
from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault

ITEM = "pi_m1c"
LOS = {"lo_m1": [("pi_m1a", 2.0), ("pi_m1b", 2.0), ("pi_m1c", 2.0)]}


def _items():
    return [scheduled(item, "lo_m1", forgetting_risk=0.6) for item in ("pi_m1a", "pi_m1b", "pi_m1c")]


def _env(tmp_path):
    from datetime import UTC, datetime

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=LOS, version="mvp-0.22")
    clock = MovableClock()
    env = make_env(paths.root, _items(), clock=clock, session_id="s1")
    for item in ("pi_m1a", "pi_m1b", "pi_m1c"):
        seed_due(env.repository, item, due=datetime(2026, 10, 1, 9, tzinfo=UTC), last=datetime(2026, 9, 20, 9, tzinfo=UTC))
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id, started_at, available_minutes) VALUES ('s1', ?, 30)",
                           (iso(clock.now()),))
        connection.commit()
    return paths, env


def _receipts(repository, key: str) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM attention_block_events WHERE kind = 'block_chosen' "
            "AND json_extract(detail_json, '$.idempotency_key') = ?", (key,)).fetchone()[0]


def _all_receipts(repository) -> int:
    """Every learner-pick receipt the plan holds (keyed or not)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute("SELECT COUNT(*) FROM attention_block_events WHERE kind = 'block_chosen'").fetchone()[0]


def _presentations(repository, item: str = ITEM) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute("SELECT COUNT(*) FROM plan_presentations WHERE practice_item_id = ?",
                                  (item,)).fetchone()[0]


@pytest.mark.parametrize("closed", [False, True], ids=["plan_open", "plan_closed"])
def test_a_pick_made_under_a_key_is_made_once(tmp_path, closed):
    _paths, env = _env(tmp_path)
    build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    if closed:
        stop_today(env)
    _record, first = learner_pick(env, ITEM, idempotency_key="workbench_admission:wbs_1")
    _record, again = learner_pick(env, ITEM, idempotency_key="workbench_admission:wbs_1")
    assert first["presentation_id"] and again["presentation_id"] == first["presentation_id"]
    assert _receipts(env.repository, "workbench_admission:wbs_1") == 1
    assert _presentations(env.repository) == 1


# -- the admission itself, through the sidecar -------------------------------------------------------


def _sidecar(tmp_path, monkeypatch):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import library_exercises as LX

    paths, env = _env(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    # Today's plan, closed (Codex's reproduction): a pick is an open-list pick receipt.
    from learnloop_sidecar.handlers import daily_plan

    required = daily_plan._require(ctx, "s1")
    assert required is not None, "the plan is live at this version"
    build_plan(required[2], kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    stop_today(required[2])
    # A picked exercise bound to the item its import wrote (the fallback's
    # shape: no proposal), its region readable.
    row, _resumed = WB.open_session(
        repository, origin="reader", entry="practice_this", stem_md="Solve the exercise.", extraction_id="ext_x",
        span_ids=["s1"], import_status="pending",
        import_request={"extraction_id": "ext_x", "raw_selection": {"nodes": [{"span_id": "s1", "start": 0, "end": 5}]},
                        WB.EXERCISE_PICK_KEY: {"proposal_id": None, "extraction_id": "ext_x", "span_ids": ["s1"],
                                               "admitted_at": None}})
    WB.bind(repository, row["id"], ITEM)
    # The region is not a real book here: the statement gate is not under test.
    monkeypatch.setattr(WB, "statement_cleared", lambda vault, repository, session: True, raising=False)
    monkeypatch.setattr(handler, "_refuse_withheld_exercise", lambda vault, repository, row: None)
    monkeypatch.setattr(LX, "pick_exposure", lambda vault, repository, pick, practice_item_id=None: {
        "exposed": False, "reasons": [], "label": None, "note": None, "offered_as": "check_on_your_own",
        "exposure_rule_version": "test"})
    return ctx, repository, row["id"]


def _fail_once(monkeypatch, target: Any, name: str) -> list[int]:
    real = getattr(target, name)
    calls: list[int] = []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError("database is locked")
        return real(*args, **kwargs)

    monkeypatch.setattr(target, name, flaky)
    return calls


def test_r1_a_retry_after_a_locked_final_write_makes_no_second_pick(tmp_path, monkeypatch):
    ctx, repository, session_id = _sidecar(tmp_path, monkeypatch)
    before = _all_receipts(repository)
    _fail_once(monkeypatch, WB, "admit_exercise_pick")
    with pytest.raises(sqlite3.OperationalError):
        handler._admit(ctx, session_id, "s1")
    assert WB.exercise_pick_due(WB.session_row(repository, session_id))  # still owed
    handler._admit(ctx, session_id, "s1")  # the retry, no restart
    # One learner pick: one receipt, one presentation (Codex: two and two).
    assert (_presentations(repository), _all_receipts(repository) - before) == (1, 1)
    pick = WB.exercise_pick(WB.session_row(repository, session_id))
    assert pick["admitted_at"]
    key = handler.admission_key(session_id)
    assert _receipts(repository, key) == 1
    row = WB.session_row(repository, session_id)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        [presentation] = [r[0] for r in connection.execute(
            "SELECT id FROM plan_presentations WHERE practice_item_id = ?", (ITEM,))]
    assert row["plan_presentation_id"] == presentation


def test_r1_a_lost_pick_record_is_found_by_its_key_in_the_plans_receipt(tmp_path, monkeypatch):
    ctx, repository, session_id = _sidecar(tmp_path, monkeypatch)
    _fail_once(monkeypatch, WB, "record_admission_stage")  # the pick commits; its record on the problem fails
    with pytest.raises(sqlite3.OperationalError):
        handler._admit(ctx, session_id, "s1")
    handler._admit(ctx, session_id, "s1")
    assert WB.exercise_pick(WB.session_row(repository, session_id))["admitted_at"]
    assert _receipts(repository, handler.admission_key(session_id)) == 1
    assert _presentations(repository) == 1


def test_r1_a_lost_serve_record_repeats_no_pick_and_no_presentation(tmp_path, monkeypatch):
    """The pick and its serve commit; the problem's record of the serve
    (``served``) fails. The retry makes no second pick and no second
    presentation; it repeats only the open-list serve, whose proposal records
    are idempotent (the usage signal, the delivery deduped by
    ``_pick_delivery``)."""

    ctx, repository, session_id = _sidecar(tmp_path, monkeypatch)
    real = WB.record_admission_stage
    calls: list[dict[str, Any]] = []

    def flaky(repository, session_id, stage):
        calls.append(dict(stage))
        if stage.get("served") and sum(1 for call in calls if call.get("served")) == 1:
            raise sqlite3.OperationalError("database is locked")
        return real(repository, session_id, stage)

    monkeypatch.setattr(WB, "record_admission_stage", flaky)
    with pytest.raises(sqlite3.OperationalError):
        handler._admit(ctx, session_id, "s1")
    assert WB.exercise_pick_due(WB.session_row(repository, session_id))
    handler._admit(ctx, session_id, "s1")
    assert WB.exercise_pick(WB.session_row(repository, session_id))["admitted_at"]
    assert _receipts(repository, handler.admission_key(session_id)) == 1
    assert _presentations(repository) == 1
    assert len([call for call in calls if "picked" in call]) == 1  # the pick was kept once, never made again
