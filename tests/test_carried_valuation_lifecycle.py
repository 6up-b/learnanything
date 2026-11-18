"""A deferred carried valuation's life: started and listed in one step, stopped when its session closes or a new plan
replaces its plan, and recorded only by a later decision of the session and plan that deferred it.

The carried valuation of a decision served before it existed runs off the serving path (the next boundary's job, or,
with no models, a thread of its own; ``daily_plan.objective_job``). Every interleaving here is held by a barrier
(``threading.Event``), never by a sleep.
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import objective_job as J
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.daily_plan.router_chooser import _NoModels
from learnloop.router_objective import tail_serve
from learnloop_sidecar.context import SidecarContext

from tests.daily_plan_fakes import record_attempt
from tests.helpers import RANDOMIZED_CHECKS_OFF
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import fake_runtime

VALUED = {"previous": {"q_status": "valued", "q": {"blk": 0.5}, "draws": 1, "elapsed_ms": 0}}
CONFIG = SimpleNamespace(router=SimpleNamespace(timeout_seconds=30.0))


def _numeric(compute) -> J.NumericPolicy:
    return J.NumericPolicy(status="answered", carried=compute,
                           residual={"previous": {"q_status": tail_serve.NOT_BEFORE_THE_SERVE}})


def _no_model_entry() -> _NoModels:
    return _NoModels("key", {}, 0.0)


def _blocking_compute():
    """A carried valuation that runs until it is told to stop (it honours its ``stop`` as the production one does)."""

    started, stopped = threading.Event(), threading.Event()

    def compute(deadline=None, stop=None):
        started.set()
        assert stop is not None and stop.wait(30), "the valuation was never told to stop"
        stopped.set()
        return {"previous": {"q_status": "not_valued_within_the_budget"}}

    return compute, started, stopped


def test_a_carry_thread_is_listed_in_the_same_hold_of_the_lock_that_starts_it(tmp_path, monkeypatch):
    """Started outside the lock, a thread could run before it was listed, and ``join_carried`` would then say none is
    running while it read the database. The thread checks, as its first act, whether the lock is still held by the
    start (its listing then lands before anyone can look), and asks ``join_carried`` itself."""

    path = tmp_path / "state.sqlite"
    probe: dict = {}
    checked, release = threading.Event(), threading.Event()
    real_thread = J.threading.Thread

    class StartWaitsForTheProbe(real_thread):
        def start(self):
            super().start()
            assert checked.wait(30), "the carry thread never ran"

    def drain(sqlite_path, *, deadline=None):
        free = J._CARRY_LOCK.acquire(blocking=False)
        if free:
            J._CARRY_LOCK.release()
        probe["lock_free_at_start"] = free
        checked.set()
        probe["none_running"] = J.join_carried(timeout=0)
        release.wait(30)
        return 0

    monkeypatch.setattr(J, "threading", SimpleNamespace(**{**vars(threading), "Thread": StartWaitsForTheProbe}))
    monkeypatch.setattr(J, "drain_carry", drain)
    try:
        J.defer_carry(_numeric(lambda **_: dict(VALUED)), _no_model_entry(), "d1",
                      runtime=SimpleNamespace(clock=time.monotonic), sqlite_path=path, config=CONFIG,
                      session_id="s1", plan_id="p1")
        assert checked.wait(30)
        release.set()
        assert J.join_carried(timeout=30)
    finally:
        release.set()
        J.stop_carries(path)
    assert probe == {"lock_free_at_start": False, "none_running": False}


def test_stopping_a_running_carry_ends_it_joins_it_and_no_later_trace_records_it(tmp_path):
    path = tmp_path / "state.sqlite"
    compute, started, stopped = _blocking_compute()
    J.defer_carry(_numeric(compute), _no_model_entry(), "d1", runtime=SimpleNamespace(clock=time.monotonic),
                  sqlite_path=path, config=CONFIG, session_id="s1", plan_id="p1")
    assert started.wait(30)
    assert J.stop_carries(path, timeout=30) is True
    assert stopped.is_set() and J.join_carried(timeout=0)
    repository = SimpleNamespace(sqlite_path=path)
    assert J.carried_for(repository, "d2", session_id="s1", plan_id="p1") == []


def test_closing_the_sidecar_stops_and_joins_its_vaults_carries(tmp_path):
    path = tmp_path / "state.sqlite"
    other = tmp_path / "other.sqlite"
    compute, started, stopped = _blocking_compute()
    J.defer_carry(_numeric(compute), _no_model_entry(), "d1", runtime=SimpleNamespace(clock=time.monotonic),
                  sqlite_path=path, config=CONFIG, session_id="s1", plan_id="p1")
    J.defer_carry(_numeric(lambda **_: dict(VALUED)), object(), "d9", runtime=SimpleNamespace(clock=time.monotonic),
                  sqlite_path=other, config=CONFIG, session_id="s1", plan_id="p1")
    try:
        assert started.wait(30)
        context = SidecarContext()
        context.repository = SimpleNamespace(sqlite_path=path)
        context.close()
        assert stopped.is_set() and J.join_carried(timeout=0)
        assert J.carried_for(SimpleNamespace(sqlite_path=path), "d2", session_id="s1", plan_id="p1") == []
        # Another vault's carries are its own context's to stop.
        J.drain_carry(other, deadline=time.monotonic() + 30)
        [kept] = J.carried_for(SimpleNamespace(sqlite_path=other), "d10", session_id="s1", plan_id="p1")
        assert kept["decision_id"] == "d9"
    finally:
        J.stop_carries(path)
        J.stop_carries(other)


def test_a_carry_is_recorded_only_by_a_later_decision_of_its_own_session_and_plan(tmp_path):
    path = tmp_path / "state.sqlite"
    repository = SimpleNamespace(sqlite_path=path)
    J.defer_carry(_numeric(lambda **_: dict(VALUED)), object(), "d1", runtime=SimpleNamespace(clock=time.monotonic),
                  sqlite_path=path, config=CONFIG, session_id="s1", plan_id="p1")
    try:
        assert J.drain_carry(path, deadline=time.monotonic() + 30) == 1
        assert J.carried_for(repository, "d2", session_id="s1", plan_id="p2") == []
        assert J.carried_for(repository, "d2", session_id="s2", plan_id="p1") == []
        [recorded] = J.carried_for(repository, "d2", session_id="s1", plan_id="p1")
        assert recorded["decision_id"] == "d1" and recorded["previous"] == VALUED["previous"]
    finally:
        J.stop_carries(path)


def test_a_new_plan_stops_and_joins_the_carries_its_predecessors_left(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=LATEST_ALGORITHM_VERSION, toml=RANDOMIZED_CHECKS_OFF)
    path = env.repository.sqlite_path
    compute, started, stopped = _blocking_compute()
    J.defer_carry(_numeric(compute), _no_model_entry(), "d_old", runtime=SimpleNamespace(clock=time.monotonic),
                  sqlite_path=path, config=CONFIG, session_id=env.session_id, plan_id="plan_before")
    try:
        assert started.wait(30)
        # The plan stands without its first block, so no carry of its own is running when it is checked.
        plan = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip", first_block=False)
        assert stopped.is_set() and J.join_carried(timeout=0)
        assert J.carried_for(env.repository, "d_new", session_id=env.session_id, plan_id="plan_before") == []
        assert J.carried_for(env.repository, "d_new", session_id=env.session_id, plan_id=plan.id) == []
    finally:
        J.stop_carries(path)


def test_the_production_valuation_ends_once_told_to_stop(tmp_path, monkeypatch):
    """The carried valuation the numeric policy hands over (a no-model serve's) values its candidates when let run,
    and ends unvalued, as at a deadline, when its stop is set: the rollouts read the clock past any deadline."""

    env = mixture_env(tmp_path, fake_runtime(), version=LATEST_ALGORITHM_VERSION, toml=RANDOMIZED_CHECKS_OFF)
    handed: list = []
    real = J.defer_carry

    def capture(numeric, *args, **kwargs):
        if numeric.carried is not None:
            handed.append(numeric.carried)
        out = real(numeric, *args, **kwargs)
        J.join_carried()
        return out

    monkeypatch.setattr(J, "defer_carry", capture)
    try:
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        for _ in range(4):
            if handed:
                break
            _record, step = advance(env, serve=True)
            if step is None or step.get("kind") != "item":
                break
            env.clock.advance(2)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
            env.clock.advance(1)
        assert handed, "no serve handed over a carried valuation"
        compute = handed[0]
        let_run = compute(deadline=time.monotonic() + 60, stop=threading.Event())
        assert let_run["previous"]["q_status"] == "valued"
        told = threading.Event()
        told.set()
        stopped = compute(deadline=time.monotonic() + 60, stop=told)
        assert stopped["previous"]["q_status"] == "not_valued_within_the_budget"
    finally:
        J.stop_carries(env.repository.sqlite_path)
