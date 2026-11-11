"""Spec_instruct_handoff_v1 §3a item 2 (IH0): the phone starts a boundary's objective job while feedback shows.

Through the real host (TestClient, the fake grader) on a plan vault at the objective's tag, with the router's models
faked and the process's runtime replaced:

* ``plan_prefetch`` writes nothing: every table's row count is pinned across the call, and it returns no step;
* the serve finds the job by its boundary key and uses its answer, with no second LLM call (the key pin);
* it is idempotent, and a no-op in mid-block, with no model set up, with the plan off and for a moved session;
* it is allowlisted on the phone host, under the plan's kill switch;
* the job runs off the RPC worker: the call returns while the model is out;
* a slow LLM that answers within the router's 40 s wait is served, not fallen back from.
"""

from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
import threading
import time
from typing import Any

import pytest
from tests.instruct_handoff_ih0_helpers import DAY, DECISION_TABLES, ITEMS, JOB_AND_HOST_TABLES
from tests.instruct_handoff_ih0_helpers import make_world  # noqa: F401 - fixtures, used by parameter name

pytest.importorskip("starlette")
from starlette.testclient import TestClient

from learnloop.db.repositories import Repository
from learnloop_mobile.allowlist import ALLOWLIST, PLAN_METHODS
from learnloop_mobile.host import create_app

from tests.helpers import create_daily_plan_vault
from tests.mobile_host_helpers import HOSTNAME, Phone, config_for, pair
from tests.router_model_fakes import FakeLLM
from tests.ro4_objective_serving_helpers import policy_answer

def test_the_prefetch_writes_nothing_and_returns_no_step(make_world):
    world = make_world()
    world.answer(world.next()["step"])
    reply = None
    for _ in range(12):
        before = world.quiet_counts()
        reply = world.prefetch()
        after = world.counts()
        changed = {table for table in after if after[table] != before[table]}
        assert changed <= JOB_AND_HOST_TABLES, changed
        for table in DECISION_TABLES:
            assert table in after and after[table] == before[table], table
        if reply["started"]:
            break
        world.answer(world.next()["step"])
    assert reply["started"] is True and reply["reason"] == "started"
    assert set(reply) == {"version", "started", "reason"}
    # A write would have failed at the database: the walk ran on a read-only attach, and it reached the chooser.
    assert world.llm.requests


def test_the_prefetch_leaves_the_answered_items_plan_events_to_the_serve(make_world):
    """The answer it folds in (``item_done``, ``block_ended``) is only in memory until the serve reconciles."""

    world = make_world()
    world.to_boundary()
    with world.repository.connection() as connection:
        kinds = [row["kind"] for row in connection.execute(
            "SELECT kind FROM attention_block_events ORDER BY created_at, event_ordinal")]
    assert "item_done" not in kinds[-1:] and "block_ended" not in kinds
    world.next()
    with world.repository.connection() as connection:
        kinds = [row["kind"] for row in connection.execute("SELECT kind FROM attention_block_events")]
    assert "item_done" in kinds and "block_ended" in kinds


def test_the_serve_finds_the_job_and_makes_no_second_llm_call(make_world):
    world = make_world()
    reply = world.to_boundary()
    assert reply["started"] is True and reply["reason"] == "started"
    asked = len(world.llm.requests)
    jobs = list(world.runtime._entries)
    assert world.next()["step"] is not None
    # The key pin: the serve's boundary key is the prefetch's, so it starts no job of its own.
    assert list(world.runtime._entries) == jobs
    assert len(world.llm.requests) == asked
    assert world.last_trace()["policies"]["llm"]["status"] == "answered"
    assert world.last_trace()["policies"]["numeric"]["status"] == "answered"


def test_the_key_survives_the_learner_reading_feedback(make_world):
    """Nov 7: about 100 s between the feedback showing and Next. Time passing doesn't change the boundary's key."""

    world = make_world()
    assert world.to_boundary()["started"] is True
    asked, jobs = len(world.llm.requests), list(world.runtime._entries)
    world.now["at"] = DAY + timedelta(seconds=100)
    assert world.next()["step"] is not None
    assert list(world.runtime._entries) == jobs and len(world.llm.requests) == asked
    assert world.last_trace()["policies"]["llm"]["status"] == "answered"


def test_the_serve_reads_the_job_with_the_plan_view_the_prefetch_computed(make_world):
    """``_reconcile_view`` is the record ``reconcile`` leaves: the state the boundary key names."""

    from learnloop.daily_plan.engine import PlanEnv, _reconcile_view, latest_today, reconcile
    from learnloop.vault.loader import load_vault
    world = make_world()
    world.to_boundary()
    env = PlanEnv(vault=load_vault(world.paths.root), repository=world.repository)
    view = _reconcile_view(env, latest_today(env))
    with world.repository.connection() as connection:
        before = connection.execute("SELECT COUNT(*) FROM attention_block_events").fetchone()[0]
    assert view is not None
    record = reconcile(env, latest_today(env))
    with world.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM attention_block_events").fetchone()[0] > before
    assert view.minutes_left() == record.minutes_left()
    assert view.lane_left() == record.lane_left()
    assert view.current_block() is None and record.current_block() is None
    assert view.planned_ids() == record.planned_ids()
    assert [item.resolved for item in view.items()] == [item.resolved for item in record.items()]


def test_it_is_idempotent(make_world):
    world = make_world()
    assert world.to_boundary()["started"] is True
    asked, jobs = len(world.llm.requests), list(world.runtime._entries)
    before = world.quiet_counts()
    assert world.prefetch()["started"] is True
    assert len(world.llm.requests) == asked and list(world.runtime._entries) == jobs
    after = world.counts()
    assert {table for table in after if after[table] != before[table]} <= JOB_AND_HOST_TABLES


def test_a_no_op_in_mid_block(make_world):
    world = make_world()
    assert world.next()["step"]["kind"] == "item"
    asked, jobs = len(world.llm.requests), list(world.runtime._entries)
    reply = world.prefetch()
    assert reply["started"] is False and reply["reason"] == "not_a_boundary"
    assert len(world.llm.requests) == asked and list(world.runtime._entries) == jobs


def test_a_no_op_with_no_model_set_up(make_world):
    world = make_world(models=False)
    world.answer(world.next()["step"])
    reply = world.prefetch()
    assert reply["started"] is False and reply["reason"] == "no_model"
    assert not world.runtime._entries


def test_a_no_op_with_the_plan_off(make_world):
    world = make_world(toml="[plan]\nenabled = false\n")
    reply = world.prefetch()
    assert reply["started"] is False and reply["reason"] == "plan_off"
    assert not world.runtime._entries


def test_a_no_op_with_the_objective_off(make_world):
    world = make_world(toml="[router_objective]\nenabled = false\n")
    reply = world.prefetch()
    assert reply["started"] is False and reply["reason"] == "no_model"


def test_a_no_op_while_the_answers_diagnosis_is_out(make_world, monkeypatch):
    world = make_world()
    world.answer(world.next()["step"])
    monkeypatch.setattr(Repository, "pending_live_diagnoses_for_session", lambda _self, _session: ["attempt_1"])
    jobs = list(world.runtime._entries)
    reply = world.prefetch()
    assert reply["started"] is False and reply["reason"] == "diagnosis_pending"
    assert list(world.runtime._entries) == jobs


def test_a_no_op_for_another_device_and_for_an_unknown_session(make_world):
    world = make_world()
    assert world.next()["step"]["kind"] == "item"
    other = Phone(world.phone.client, pair(world.repository))
    reply = other.rpc("plan_prefetch", {"sessionId": world.session})
    assert reply["started"] is False and reply["reason"] == "session_moved"
    reply = world.phone.rpc("plan_prefetch", {"sessionId": "no_such_session"})
    assert reply["started"] is False and reply["reason"] == "no_session"


def test_allowlisted_on_the_phone_host_under_the_plan_switch(make_world, tmp_path):
    assert ALLOWLIST["plan_prefetch"].kind == "short" and "plan_prefetch" in PLAN_METHODS
    world = make_world()
    # The model declares nothing else, so this is no way to serve.
    assert world.phone.post("plan_prefetch", {"sessionId": world.session, "serve": True}).status_code == 422
    config = config_for(world.paths.root).model_copy(update={"phone_plan": False})
    with TestClient(create_app(config), base_url=f"https://{HOSTNAME}") as client:
        status, error = Phone(client, world.phone.device).error("plan_prefetch", {"sessionId": world.session})
    assert (status, error["code"]) == (409, "phone_plan_off")


def test_the_call_returns_while_the_model_is_out_and_the_serve_waits_for_that_answer(make_world):
    """The job runs off the RPC worker: the call returns with the model out, other short reads answer, and the serve
    that follows waits for the same job (no second call), not a new one."""

    llm = FakeLLM(answer=policy_answer)
    world = make_world(llm=llm, inline=False)
    step = world.next()["step"]
    world.wait_for_job()
    asked = len(llm.requests)
    gate = threading.Event()
    llm.gate = gate
    try:
        assert world.answer_to_boundary(step)["started"] is True
        deadline = time.monotonic() + 10
        while len(llm.requests) == asked and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(llm.requests) == asked + 1
        assert not all(entry.complete for entry in world.runtime._entries.values())
        assert world.phone.rpc("get_session", {"sessionId": world.session})["sessionId"] == world.session
        jobs = list(world.runtime._entries)
        timer = threading.Timer(1.0, gate.set)
        timer.start()
        world.next()
    finally:
        gate.set()
    assert list(world.runtime._entries) == jobs and len(llm.requests) == asked + 1
    assert world.last_trace()["policies"]["llm"]["status"] == "answered"


def test_a_slow_llm_within_the_wait_is_served_and_does_not_fall_back(make_world, monkeypatch):
    """No prefetched job here (Keep going has none to start): the serve starts its own and waits the router's 40 s."""

    from learnloop.daily_plan import objective_chooser

    waits: list[float] = []
    real = objective_chooser._await

    def recording(runtime: Any, entry: Any, *, may_defer: bool, timeout: float) -> None:
        waits.append(timeout)
        real(runtime, entry, may_defer=may_defer, timeout=timeout)

    monkeypatch.setattr(objective_chooser, "_await", recording)
    llm = FakeLLM(answer=policy_answer)
    world = make_world(llm=llm, inline=False)
    assert world.to_boundary()["started"] is True
    world.wait_for_job()
    world.runtime._entries.clear()
    waits.clear()
    gate = threading.Event()
    llm.gate = gate
    timer = threading.Timer(1.0, gate.set)
    timer.start()
    started = time.monotonic()
    try:
        world.next()
    finally:
        gate.set()
    assert time.monotonic() - started >= 0.9
    assert waits == [40.0]
    assert world.last_trace()["policies"]["llm"]["status"] == "answered"


def test_a_read_only_attach_reads_the_due_followup_tasks_and_leaves_them(tmp_path):
    """The one write ``build_due_queue`` makes even with ``persist_explanations`` off: two lazy status marks."""

    from tests.ad23_fakes import cold_followup

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=ITEMS)
    repository = Repository(paths.sqlite_path)
    cold_followup(paths, "pi_a1")

    def statuses() -> list[str]:
        with repository.connection() as connection:
            return [row[0] for row in connection.execute("SELECT status FROM followup_tasks")]

    reader = Repository.attach(paths.sqlite_path, read_only=True)
    read = reader.due_followup_tasks()
    assert statuses() == ["pending"]
    assert [(row["id"], row["status"]) for row in read] == [(row["id"], row["status"])
                                                            for row in repository.due_followup_tasks()]
    assert statuses() == ["served"]


def test_the_contract_files_name_it():
    contract = json.loads((Path(__file__).resolve().parents[1] / "apps/learnloop-mobile/contract/plan_prefetch.json")
                          .read_text(encoding="utf-8"))
    assert contract["requests"][0]["envelope"] == {"method": "plan_prefetch", "params": {"sessionId": "s1"}}
    assert contract["reads"] == []
