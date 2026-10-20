"""Reader RW4b fix round 6 (Codex verify ``20261020-123459-EZlKv5``; the
orchestrator's rulings).

1. **F2, the planned branch.** A keyed learner pick of an item already in
   today's plan records its key against that EXISTING presentation, in the
   serve's transaction (``PICK_KEYED``), and ``picked_under`` finds it under
   a later plan: the retry returns the original presentation and makes none.
2. **F13, partial writes.** A keyed pick writes its block, its serve, its
   keyed receipt and its proposal's delivery in ONE transaction: a failure
   after the block and before the serve, or after the serve and before the
   delivery, leaves nothing, and the retry makes each exactly once. The
   admission's own serve and its ``served`` record share one transaction too.
3. **F7, kept jobs.** A finished workbench help job is delivered only while
   its problem's statement may be shown (the library's exercise jobs are
   pinned in ``test_library_exercises.py``).

Daily-plan vaults and fakes only; no model call.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

import learnloop.clock as clock_module
from learnloop.daily_plan import engine as E
from learnloop.daily_plan.engine import build_plan, learner_pick
from learnloop.db.connection import connect
from learnloop.reader import workbench as WB
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import daily_plan as plan_handler
from learnloop_sidecar.handlers import workbench as handler
from tests.daily_plan_fakes import NOW, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.test_learner_pick_proposal import _call, _draw, _interventions, ctx  # noqa: F401 - the proposal fixture

#: The keyed receipt's kind (``engine.PICK_KEYED``), named here so the
#: fail-before run reads counts, not a missing name.
PICK_KEYED = "pick_keyed"
PLANNED = "pi_m1a"  # the item the one-block plan below plans (greedy)
LOS = {"lo_m1": [("pi_m1a", 2.0), ("pi_m1b", 2.0), ("pi_m1c", 2.0)]}


def _items():
    return [scheduled(item, "lo_m1", forgetting_risk=0.6) for item in ("pi_m1a", "pi_m1b", "pi_m1c")]


def _seed(env, clock_now: datetime) -> None:
    for item in ("pi_m1a", "pi_m1b", "pi_m1c"):
        seed_due(env.repository, item, due=datetime(2026, 10, 1, 9, tzinfo=UTC),
                 last=datetime(2026, 9, 20, 9, tzinfo=UTC))
    with env.repository.connection() as connection:
        connection.execute("INSERT INTO sessions(id, started_at, available_minutes) VALUES ('s1', ?, 30)",
                           (iso(clock_now),))
        connection.commit()


def _count(repository, sql: str, *args: Any) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(sql, args).fetchone()[0]


def _presentations(repository, item: str) -> int:
    return _count(repository, "SELECT COUNT(*) FROM plan_presentations WHERE practice_item_id = ?", item)


def _keyed(repository, key: str) -> int:
    return _count(repository, "SELECT COUNT(*) FROM attention_block_events WHERE kind = ? "
                              "AND json_extract(detail_json, '$.idempotency_key') = ?", PICK_KEYED, key)


# -- 1. F2: the planned branch, retried under a later plan -------------------------------------------


def test_f2_a_keyed_pick_of_a_planned_item_is_found_under_a_later_plan(tmp_path):
    from tests.daily_plan_fakes import MovableClock

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=LOS, version="mvp-0.22")
    clock = MovableClock()
    env = make_env(paths.root, _items(), clock=clock, session_id="s1")
    _seed(env, clock.now())
    first_plan = build_plan(env, kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    assert PLANNED in [item.practice_item_id for item in first_plan.items()]  # the planned branch
    _record, first = learner_pick(env, PLANNED, idempotency_key="workbench_admission:wbs_1")
    assert first["presentation_id"]
    # The learner comes back the next day: a later plan plans the item again.
    clock.advance(24 * 60)
    later = E.get_or_create_today(env)
    assert later is not None and later.id != first_plan.id
    assert PLANNED in [item.practice_item_id for item in later.items()]
    _record, again = learner_pick(env, PLANNED, idempotency_key="workbench_admission:wbs_1")
    assert (_presentations(env.repository, PLANNED), again["presentation_id"]) == (1, first["presentation_id"])
    assert _keyed(env.repository, "workbench_admission:wbs_1") == 1


def _planned_sidecar(tmp_path, monkeypatch):
    """A sidecar over a daily-plan vault whose plan is open and plans
    ``PLANNED``; a picked exercise bound to it, owed its admission. The
    clock is movable (``state['now']``)."""

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers import library_exercises as LX
    from tests.daily_plan_fakes import MovableClock

    state = {"now": NOW}
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: state["now"])
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=LOS, version="mvp-0.22")
    seeded = make_env(paths.root, _items(), clock=MovableClock(), session_id="s1")
    _seed(seeded, NOW)
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    required = plan_handler._require(ctx, "s1")
    assert required is not None, "the plan is live at this version"
    plan = build_plan(required[2], kind="normal", budget=4.0, remembered=4, minutes_source="chip")
    assert PLANNED in [item.practice_item_id for item in plan.items()]
    row, _resumed = WB.open_session(
        repository, origin="reader", entry="practice_this", stem_md="Solve the exercise.", extraction_id="ext_x",
        span_ids=["s1"], import_status="pending",
        import_request={"extraction_id": "ext_x", "raw_selection": {"nodes": [{"span_id": "s1", "start": 0, "end": 5}]},
                        WB.EXERCISE_PICK_KEY: {"proposal_id": None, "extraction_id": "ext_x", "span_ids": ["s1"],
                                               "admitted_at": None}})
    WB.bind(repository, row["id"], PLANNED)
    # The region is not a real book here: the statement gate is not under test.
    monkeypatch.setattr(WB, "statement_cleared", lambda vault, repository, session: True, raising=False)
    monkeypatch.setattr(handler, "_refuse_withheld_exercise", lambda vault, repository, row: None)
    monkeypatch.setattr(LX, "pick_exposure", lambda vault, repository, pick, practice_item_id=None: {
        "exposed": False, "reasons": [], "label": None, "note": None, "offered_as": "check_on_your_own",
        "exposure_rule_version": "test"})
    return ctx, repository, row["id"], state


def test_f2_verify_sequence_planned_pick_locked_picked_write_retry_under_a_later_plan(tmp_path, monkeypatch):
    """Codex's sequence: the item is already planned; the admission's
    ``picked`` write meets ``database is locked``; the learner comes back
    under a later plan and the admission is retried. One presentation."""

    ctx, repository, session_id, state = _planned_sidecar(tmp_path, monkeypatch)
    real = WB.record_admission_stage
    calls: list[int] = []

    def locked_once(repo, sid, stage):
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError("database is locked")
        return real(repo, sid, stage)

    monkeypatch.setattr(WB, "record_admission_stage", locked_once)
    with pytest.raises(sqlite3.OperationalError):
        handler._admit(ctx, session_id, "s1")
    assert _presentations(repository, PLANNED) == 1
    state["now"] = NOW + timedelta(days=1)  # a later plan
    handler._admit(ctx, session_id, "s1")
    row = WB.session_row(repository, session_id)
    assert WB.exercise_pick(row)["admitted_at"]
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        presentations = [r[0] for r in connection.execute(
            "SELECT id FROM plan_presentations WHERE practice_item_id = ?", (PLANNED,))]
    assert len(presentations) == 1
    assert row["plan_presentation_id"] == presentations[0]


# -- 2. F13: one transaction for the keyed pick, its serve and its delivery ----------------------------


def _fail_once(monkeypatch, target: Any, name: str, error: BaseException) -> list[int]:
    real = getattr(target, name)
    calls: list[int] = []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise error
        return real(*args, **kwargs)

    monkeypatch.setattr(target, name, flaky)
    return calls


def _learner_pick_blocks(repository) -> int:
    return _count(repository, "SELECT COUNT(*) FROM attention_block_events WHERE kind = 'block_chosen' "
                              "AND json_extract(detail_json, '$.chosen_by') = 'learner_pick'")


def _pick(context, session_id: str) -> dict[str, Any]:
    return _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                                "proposalId": "pp_test", "idempotencyKey": "workbench_admission:wbs_9"})


@pytest.mark.parametrize("promoted", [None, "pi_svd_define_001"], ids=["planned", "new_block"])
def test_f13_a_failure_after_the_block_and_before_the_serve_leaves_nothing_and_the_retry_makes_all_once(
        ctx, monkeypatch, promoted):
    _draw(monkeypatch, promoted)
    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    _vault, repository = context.require_vault()
    _fail_once(monkeypatch, E, "_serve", sqlite3.OperationalError("database is locked"))
    with pytest.raises(sqlite3.OperationalError):
        _pick(context, session_id)
    # Nothing reserved: no keyed receipt, no presentation, no delivery, and
    # no learner-pick block left without its serve.
    assert _keyed(repository, "workbench_admission:wbs_9") == 0
    assert _presentations(repository, "pi_extra_1") == 0
    assert _interventions(repository) == []
    assert _learner_pick_blocks(repository) == 0
    result = _pick(context, session_id)
    assert result["step"]["presentationId"]
    assert _keyed(repository, "workbench_admission:wbs_9") == 1
    assert _presentations(repository, "pi_extra_1") == 1
    [row] = _interventions(repository)
    assert result["proposalPick"]["interventionId"] == row["id"]


@pytest.mark.parametrize("promoted", [None, "pi_svd_define_001"], ids=["planned", "new_block"])
def test_f13_a_failure_after_the_serve_and_before_the_delivery_leaves_nothing_and_the_retry_makes_all_once(
        ctx, monkeypatch, promoted):
    _draw(monkeypatch, promoted)
    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    _vault, repository = context.require_vault()
    _fail_once(monkeypatch, plan_handler, "_proposal_delivery", sqlite3.OperationalError("database is locked"))
    with pytest.raises(sqlite3.OperationalError):
        _pick(context, session_id)
    assert _keyed(repository, "workbench_admission:wbs_9") == 0
    assert _presentations(repository, "pi_extra_1") == 0
    assert _interventions(repository) == []
    result = _pick(context, session_id)
    assert _keyed(repository, "workbench_admission:wbs_9") == 1
    assert _presentations(repository, "pi_extra_1") == 1
    [row] = _interventions(repository)
    assert row["router_decision_id"] == result["proposalPick"]["routerDecisionId"]
    # And a third call (the pick already made) records nothing again.
    _pick(context, session_id)
    assert (_keyed(repository, "workbench_admission:wbs_9"), _presentations(repository, "pi_extra_1"),
            len(_interventions(repository))) == (1, 1, 1)


def test_f13_an_unkeyed_pick_keeps_its_own_transactions():
    """Only a keyed pick takes the one transaction; ``within`` without a key is refused."""

    assert E.PICK_KEYED == PICK_KEYED

    class _Env:
        vault = type("V", (), {"practice_items": {"pi": object()}})()

    with pytest.raises(ValueError):
        learner_pick(_Env(), "pi", within=lambda record, step: None)  # type: ignore[arg-type]


def test_f13_the_admissions_serve_and_its_served_record_share_one_transaction(tmp_path, monkeypatch):
    """The admission's serve (``get_practice_item``) and its ``served``
    record commit together: a lost ``served`` write rolls the serve back, so
    the retry's serve is the only one."""

    ctx, repository, session_id, _state = _planned_sidecar(tmp_path, monkeypatch)
    from learnloop_sidecar.handlers import practice as practice_handler

    served: list[str] = []
    real_serve = practice_handler.get_practice_item

    def counting_serve(context, params):
        result = real_serve(context, params)
        with repository.connection() as connection:
            # A row the serve writes, inside its transaction: visible only if it commits.
            connection.execute("CREATE TABLE IF NOT EXISTS _probe_serves(id INTEGER PRIMARY KEY, item TEXT)")
            connection.execute("INSERT INTO _probe_serves(item) VALUES (?)", (params.practice_item_id,))
        served.append(params.practice_item_id)
        return result

    monkeypatch.setattr(practice_handler, "get_practice_item", counting_serve)
    real = WB.record_admission_stage

    def lose_served(repo, sid, stage):
        if stage.get("served") and len(served) == 1:
            raise sqlite3.OperationalError("database is locked")
        return real(repo, sid, stage)

    monkeypatch.setattr(WB, "record_admission_stage", lose_served)
    with pytest.raises(sqlite3.OperationalError):
        handler._admit(ctx, session_id, "s1")
    handler._admit(ctx, session_id, "s1")
    assert WB.exercise_pick(WB.session_row(repository, session_id))["admitted_at"]
    assert len(served) == 2  # served twice, but the first rolled back with its lost record
    assert _count(repository, "SELECT COUNT(*) FROM _probe_serves") == 1


# -- 3. F7: a kept help job is delivered only while its problem may be shown ---------------------------


def test_f7_a_finished_help_job_on_a_problem_held_out_since_is_never_delivered(tmp_path, monkeypatch, grader):
    from tests.workbench_help_fakes import call, open_problem, sidecar

    _paths, wctx, _session = sidecar(tmp_path)
    wb, _chains = open_problem(wctx)
    started = call(wctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 4})
    assert started.get("jobId"), started
    assert wctx.workbench_help_jobs.get(started["jobId"]).done.wait(30)
    # The problem's region is held out after the job finished.
    held_out = {"now": True}
    real = WB.statement_cleared
    monkeypatch.setattr(WB, "statement_cleared",
                        lambda vault, repository, session: not held_out["now"] and real(vault, repository, session))
    with pytest.raises(SidecarError) as caught:
        call(wctx, "workbench.help_job", {"jobId": started["jobId"]})
    assert caught.value.code == "exercise_withheld"
    assert "P(X" not in caught.value.message
    # The gate is the only reason: cleared again, the kept job reads as before.
    held_out["now"] = False
    assert call(wctx, "workbench.help_job", {"jobId": started["jobId"]})["state"] == "done"
