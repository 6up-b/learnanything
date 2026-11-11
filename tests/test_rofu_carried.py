"""The follow-up batch, item 4 (RO6's landing open items 1 and 3, on its rulings R12 and R3): the carried valuation
of a decision served before it existed runs in the next boundary's prefetch (the no-model branch: a thread of its
own after the serve), never on the serving path, and a later decision's trace records it (``carried_for``: keyed by
the decision, read as of the carrying trace's own time), so the transition into that decision is no longer censored
``cutoff_unmatched``. Fakes only.
"""

from __future__ import annotations

import threading
import time

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import tail_serve as TS

from tests.router_model_fakes import block_drawing_seed
from tests.ro6_codex_review_helpers import CFG, FAR, STOP, _quiet, _row, _trace, utc  # noqa: F401

TAG = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
WIDTH = len(LT.NAMES)


def _late(decision_id: str, previous_id: str, *, carried_for: list | None = None) -> dict:
    trace = _trace(q={STOP: 0.0, "a": 0.0}, cutoff_days=6.0,
                   previous={"decision_id": previous_id, "cutoff_days": repr(5.0), "status": TS.CARRIED,
                             "q_status": TS.NOT_BEFORE_THE_SERVE,
                             "features": {STOP: [0.2] * WIDTH, "a": [0.3] * WIDTH}})
    trace["versions"] = {"horizon_days": 6.0}
    if carried_for:
        trace["carried_for"] = carried_for
    return trace


def _carrier(for_decision: str, previous_id: str) -> list:
    return [{"decision_id": for_decision,
             "previous": {"decision_id": previous_id, "cutoff_days": repr(5.0), "status": TS.CARRIED,
                          "q_status": "valued", "q": {STOP: 0.7, "a": 0.9},
                          "features": {STOP: [0.2] * WIDTH, "a": [0.3] * WIDTH}}}]


def test_a_later_traces_record_lifts_the_censoring_as_of_its_own_time(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2", "d2": "d3"})
    first = TD._logged(None, _row("d1", "2026-10-01T10:00:00Z"), _late("d1", "d0"), CFG, FAR, False)
    second = TD._logged(None, _row("d2", "2026-10-01T11:00:00Z"), _late("d2", "d1"), CFG, FAR, False)
    third = TD._logged(None, _row("d3", "2026-10-01T12:00:00Z"), _late("d3", "d2", carried_for=_carrier("d2", "d1")),
                       CFG, FAR, False)
    # Before the carrying trace is known (read at a moment before d3), d1 -> d2 stays censored.
    early = TD.transitions(None, CFG, TD._with_late_carried([first, second]), at=FAR)
    assert early.transitions == () and early.censored.get(TD.CUTOFF_UNMATCHED) == 1
    rows = TD._with_late_carried([first, second, third])
    assert rows[1].carried_source == "later_prefetch" and rows[1].q_at_previous == {STOP: 0.7, "a": 0.9}
    late = TD.transitions(None, CFG, rows, at=FAR)
    kept = [step for step in late.transitions if step.decision_id == "d1"]
    assert len(kept) == 1 and kept[0].detail["cutoff"] == "previous_cutoff"
    # The same backup as a decision valued in time (its own trace holding the value).
    inline = _late("d2", "d1")
    inline["residual"]["previous"] = _carrier("d2", "d1")[0]["previous"]
    in_time = TD._logged(None, _row("d2", "2026-10-01T11:00:00Z"), inline, CFG, FAR, False)
    reference = TD.transitions(None, CFG, [first, in_time], at=FAR).transitions[0]
    assert (kept[0].reward, kept[0].next_v_tail, kept[0].next_phi) == (
        reference.reward, reference.next_v_tail, reference.next_phi)


def test_a_record_naming_another_earlier_decision_is_ignored(monkeypatch, utc):
    first = TD._logged(None, _row("d1", "2026-10-01T10:00:00Z"), _late("d1", "d0"), CFG, FAR, False)
    second = TD._logged(None, _row("d2", "2026-10-01T11:00:00Z"), _late("d2", "d1"), CFG, FAR, False)
    third = TD._logged(None, _row("d3", "2026-10-01T12:00:00Z"), _late("d3", "d2", carried_for=_carrier("d2", "dX")),
                       CFG, FAR, False)
    assert TD._with_late_carried([first, second, third])[1].q_at_previous is None


def _traces(env) -> list[dict]:
    with env.repository.connection() as connection:
        return [store.trace(connection, row["decision_id"])["trace"] for row in store.traces(connection)
                if row["decision_kind"] == "plan_block"]


def _carried_threads(timeout: float = 30.0) -> None:
    for thread in list(threading.enumerate()):
        if thread.name == "learnloop-objective-carried":
            thread.join(timeout)


def test_the_no_model_branch_defers_its_carried_valuation_off_the_serving_path(tmp_path, monkeypatch):
    """R3's instrumented case, at the tag: the answer returns within its first pass (the carried valuation is not
    run by run_numeric on the serving thread, and a blocked one never holds a serve); after it runs, a later trace
    records it and the transition into that decision reads it."""

    from learnloop.daily_plan import objective_chooser as OC

    from tests.daily_plan_fakes import record_attempt
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import fake_runtime
    from learnloop.daily_plan.engine import advance

    gate = threading.Event()
    real = OC.V.evaluate
    on_serving_thread: list[bool] = []
    serving = threading.current_thread()

    def blocked(*args, **kwargs):
        if kwargs.get("cutoff") is not None:
            on_serving_thread.append(threading.current_thread() is serving)
            gate.wait(60.0)
        return real(*args, **kwargs)

    monkeypatch.setattr(OC.V, "evaluate", blocked)
    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=TAG)
    waits: list[float] = []
    try:
        for _ in range(6):
            started = time.monotonic()
            _record, step = advance(env, serve=True)
            waits.append(time.monotonic() - started)
            if step is None or step["kind"] != "item":
                break
            env.clock.advance(2)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
        traces = _traces(env)
        assert len(traces) >= 2
        assert max(waits) < 30.0, waits  # a blocked carried valuation never held a serve
        assert on_serving_thread and not any(on_serving_thread)
        later = [trace["residual"]["previous"] for trace in traces[1:]]
        assert all(previous["q_status"] == TS.NOT_BEFORE_THE_SERVE and previous["deferred_to"] ==
                   "own_thread_after_the_serve" for previous in later)
    finally:
        gate.set()
    _carried_threads()
    for _ in range(4):
        _record, step = advance(env, serve=True)
        if step is None or step["kind"] != "item":
            break
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _carried_threads()
    traces = _traces(env)
    carried = [entry for trace in traces for entry in trace.get("carried_for") or ()]
    assert carried and all(entry["previous"]["q_status"] == "valued" for entry in carried)
    with env.repository.connection() as connection:
        steps = TD.fits(connection, env.vault.config, at="2100-01-01T00:00:00Z").steps
    assert any(step.detail.get("cutoff") == "previous_cutoff" for step in steps.transitions)


def _step_key(step) -> tuple:
    return (step.decision_id, step.generator, step.reward, step.next_v_tail, step.next_phi,
            step.detail.get("cutoff"))


def test_the_switch_turned_off_after_carriers_exist_reads_the_predecessors_transitions(tmp_path, monkeypatch):
    """Codex review F1: carriers are in the log, then the owner sets ``carried_in_prefetch = false``: the late
    records are no longer read (no transition is admitted that mvp-0.49 censors), so eligibility and the fits equal
    the predecessor's reading of the same traces (``_with_late_carried`` as the identity) exactly."""

    from learnloop.daily_plan.engine import advance

    from tests.daily_plan_fakes import record_attempt
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import fake_runtime

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=TAG)
    for _ in range(8):
        _record, step = advance(env, serve=True)
        _carried_threads()
        if step is None or step["kind"] != "item":
            break
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
    assert any(trace.get("carried_for") for trace in _traces(env)), "carriers exist"
    on = env.vault.config
    off = on.model_copy(update={"router_objective": on.router_objective.model_copy(
        update={"carried_in_prefetch": False})})
    at = "2100-01-01T00:00:00Z"
    with env.repository.connection() as connection:
        with_carriers = TD.fits(connection, on, at=at)
        assert any(row.carried_source == "later_prefetch" for row in TD.logged(connection, on, at=at))
        assert any(step.detail.get("cutoff") == "previous_cutoff" for step in with_carriers.steps.transitions)
        switched_off = TD.fits(connection, off, at=at)
        assert all(row.carried_source == "own_trace" for row in TD.logged(connection, off, at=at))
        monkeypatch.setattr(TD, "_with_late_carried", lambda rows: rows)
        predecessor = TD.fits(connection, on, at=at)
    assert [_step_key(step) for step in switched_off.steps.transitions] == [
        _step_key(step) for step in predecessor.steps.transitions]
    assert dict(switched_off.steps.censored) == dict(predecessor.steps.censored)
    assert dict(switched_off.steps.censored) != dict(with_carriers.steps.censored)
    assert repr(switched_off.by_generator) == repr(predecessor.by_generator)


def test_below_the_tag_the_no_model_branch_is_r3s(tmp_path):
    from tests.router_mixture_helpers import mixture_env, run
    from tests.router_model_fakes import fake_runtime

    env = mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    run(env, steps=8)
    traces = _traces(env)
    assert len(traces) >= 2
    assert all(trace["residual"]["previous"]["q_status"] == TS.NOT_ON_THE_SERVING_PATH for trace in traces[1:])
    assert not any("carried_for" in trace for trace in traces)


def test_with_models_the_wait_returns_and_the_next_prefetch_runs_it(tmp_path, monkeypatch):
    """R12's event-controlled case, at the tag: every evaluation at a carried cutoff blocked; the chooser's wait
    returns on the published answer, the carried valuation never runs in its own decision's job, and the next
    boundary's prefetch runs it once released."""

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.daily_plan.engine import advance

    from tests.daily_plan_fakes import record_attempt
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
    from tests.ro4_objective_serving_helpers import policy_answer

    gate, reached = threading.Event(), threading.Event()
    real = OC.V.evaluate

    def blocked(*args, **kwargs):
        if kwargs.get("cutoff") is not None:
            reached.set()
            gate.wait(60.0)
        return real(*args, **kwargs)

    monkeypatch.setattr(OC.V, "evaluate", blocked)
    timeout = 20.0
    try:
        runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer), inline=False,
                               seed=block_drawing_seed())
        env = mixture_env(tmp_path, runtime, version=TAG,
                          toml=f"[router]\ntimeout_seconds = {timeout}\nprefetch_timeout_seconds = 60.0\n")
        waits: list[float] = []
        for _ in range(16):
            started = time.monotonic()
            _record, step = advance(env, serve=True)
            waits.append(time.monotonic() - started)
            if len(_traces(env)) >= 3 or step is None or step["kind"] != "item":
                break
            env.clock.advance(2)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
        traces = _traces(env)
        assert len(traces) >= 2 and max(waits) < timeout / 2, waits
        previous = traces[1]["residual"]["previous"]
        assert previous["q_status"] == TS.NOT_BEFORE_THE_SERVE and previous["deferred_to"] == "next_prefetch"
    finally:
        gate.set()


def _join_jobs(timeout: float = 60.0) -> None:
    for thread in list(threading.enumerate()):
        if thread.name.startswith(("learnloop-router-", "learnloop-objective-")):
            thread.join(timeout)


def test_an_early_publication_served_keeps_its_carried_valuation(tmp_path, monkeypatch):
    """Codex review F3: the LLM is slow, so the serve's wait runs out and the numeric job's early, uncorrected
    publication serves (``published_uncorrected``) before the job's completion installs anything. The publication
    carries its own carried valuation (frozen to its own inputs: no LLM correction), so the serve hands it to the next
    boundary's prefetch; once the job and the next prefetch run, a later trace records it and the transition into the
    published decision is valued at ``previous_cutoff`` instead of censored ``cutoff_unmatched``."""

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.daily_plan.engine import advance

    from tests.daily_plan_fakes import record_attempt
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    real = OC.V.evaluate
    at_cutoff: list[tuple[bool, dict]] = []

    def spy(*args, **kwargs):
        out = real(*args, **kwargs)
        if kwargs.get("cutoff") is not None and out.complete:
            at_cutoff.append((args[0].effect is None, {row.ref: float(row.q) for row in out.valued}))
        return out

    monkeypatch.setattr(OC.V, "evaluate", spy)
    gate = threading.Event()
    # Router speed, item 4: the serve's wait runs out right after the numeric job's early publication, by events,
    # never by a real 3 s wait against a publication that takes about 2.2 s (later than 3 s on a loaded machine, so
    # the serve found nothing published). A prefetch with no numeric component, and every serve once the LLM is
    # released, waits as before.
    from learnloop.daily_plan import router_runtime as RR

    real_wait = RR.Prefetch.wait

    def wait_for_the_publication(self, timeout: float) -> None:
        if OC.NUMERIC not in self.events or gate.is_set():
            real_wait(self, timeout)
            return
        deadline = time.monotonic() + 120.0
        while time.monotonic() < deadline and not self.complete:
            with self.lock:
                if self.material.get(OC.PUBLISHED) is not None:
                    return
            self.events[OC.NUMERIC].wait(0.01)

    monkeypatch.setattr(RR.Prefetch, "wait", wait_for_the_publication)

    def step_once(env):
        _record, step = advance(env, serve=True)
        if step is not None and step["kind"] == "item":
            env.clock.advance(2)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
        return step

    try:
        runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(gate=gate), inline=False,
                               seed=block_drawing_seed())
        env = mixture_env(tmp_path, runtime, version=TAG,
                          toml="[router]\ntimeout_seconds = 3.0\nprefetch_timeout_seconds = 40.0\n")
        for _ in range(4):
            step = step_once(env)
            if len(_traces(env)) >= 2 or step is None or step["kind"] != "item":
                break
        traces = _traces(env)
        assert len(traces) >= 2
        published = traces[1]
        assert published["policies"]["numeric"]["stage"] == "published_uncorrected"
        previous = published["residual"]["previous"]
        assert previous["status"] == TS.CARRIED
        assert previous.get("q_status") == TS.NOT_BEFORE_THE_SERVE, previous.get("q_status")
        assert previous["deferred_to"] == "next_prefetch"
    finally:
        gate.set()
    _join_jobs()
    with env.repository.connection() as connection:
        decided = [str(row["decision_id"]) for row in store.traces(connection) if row["decision_kind"] == "plan_block"]
    first, served = decided[0], decided[1]
    for _ in range(6):
        step = step_once(env)
        _join_jobs()
        if any(entry["decision_id"] == served for trace in _traces(env) for entry in trace.get("carried_for") or ()):
            break
        if step is None or step["kind"] != "item":
            break
    carried = [entry for trace in _traces(env) for entry in trace.get("carried_for") or ()
               if entry["decision_id"] == served]
    assert carried and carried[0]["previous"]["q_status"] == "valued"
    # Frozen to the publication's own inputs (uncorrected: no LLM effect slope), not the job's later corrected ones.
    assert any(uncorrected and q.keys() == carried[0]["previous"]["q"].keys()
               and all(round(value, 6) == carried[0]["previous"]["q"][ref] for ref, value in q.items())
               for uncorrected, q in at_cutoff), at_cutoff
    with env.repository.connection() as connection:
        steps = TD.fits(connection, env.vault.config, at="2100-01-01T00:00:00Z").steps
    into = [step for step in steps.transitions if step.decision_id == first]
    assert len(into) == 1 and into[0].detail["cutoff"] == "previous_cutoff"
