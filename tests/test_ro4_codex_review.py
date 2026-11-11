"""RO4 Codex review (job 20261105-044310-mIr8Nh): the serving-side findings, each failing on the pre-fix source.

* F1: a slow LLM never suppresses the numeric policy's answer (it is published before any wait on the LLM);
* F5: a mid-block alternative is an ordered sequence of its two blocks, each step its own interface;
* F8: a reading candidate starts from AD's reading-dose position, not zero;
* F9: the LLM policy's forecast for the drawn option reaches RO2's resolver and the report;
* F10: the LLM policy's card names each goal's topics and their effective weights;
* F11: the frozen evaluation population does not depend on candidate support.

Fakes only; no model call.
"""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import math
import threading
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from learnloop.algorithm_versions import ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan import objective_inputs as OI
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import router_objective as store
from learnloop.router_objective import mix
from learnloop.router_objective import value as V
from learnloop.vault.loader import load_vault

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

TAG = ROUTER_OBJECTIVE_ALGORITHM_VERSION
#: The frozen-input builder itself (the spy below wraps it).
BUILD = OI.build


def _spy_builds(monkeypatch) -> list[tuple[tuple, dict, Any]]:
    calls: list[tuple[tuple, dict, Any]] = []

    def spy(*args, **kwargs):
        out = BUILD(*args, **kwargs)
        calls.append((args, kwargs, out))
        return out

    monkeypatch.setattr(OI, "build", spy)
    return calls


def _traces(env) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        return [store.trace(connection, row["decision_id"]) for row in store.traces(connection)]


# -- F1 ----------------------------------------------------------------------------------------------------------


def test_f1_the_numeric_answer_is_published_before_any_wait_on_the_llm(tmp_path, monkeypatch):
    calls = _spy_builds(monkeypatch)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env, steps=2)
    (args, kwargs, _out) = calls[0]
    published: list[OC.NumericPolicy] = []

    def forecasts():
        assert published and published[-1].status == "answered", "published before the LLM is waited for"
        return None  # the LLM is still out: no correction

    result = OC.run_numeric(args[0], args[1], state=kwargs["state"], support=kwargs["support"],
                            candidates=kwargs["candidates"], now_iso=kwargs["now_iso"], seed="f1", deadline=None,
                            forecasts=forecasts, publish=published.append)
    assert result.status == "answered" and not result.corrected
    assert published[0].choice in kwargs["support"]


def test_f1_a_slow_llm_leaves_the_numeric_share_in_place(tmp_path):
    """The LLM never answers inside the serve's wait: only its share falls back; the numeric policy's published
    answer serves, labelled (fails before the fix: the numeric job held its answer for the LLM's)."""

    gate = threading.Event()
    try:
        runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(gate=gate), inline=False)
        env = mixture_env(tmp_path, runtime, version=TAG,
                          toml="[router]\ntimeout_seconds = 3.0\nprefetch_timeout_seconds = 40.0\n")
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        advance(env, serve=True)
        decided = [row for row in rows(env) if row["policy"] == mix.POLICY]
        assert decided
        mixture = decided[0]["detail_json"]["mixture"]
        assert mixture["failed"] == ["llm"], mixture["failed"]
        assert mixture["numeric_choice"] in mixture["support"]
        assert mix.recompute(mixture)[decided[0]["chosen_ref"]] == pytest.approx(decided[0]["propensity"] or 1.0)
        trace = _traces(env)[0]
        assert trace["numeric_status"] == "answered"
        assert trace["trace"]["policies"]["numeric"]["stage"] == "published_uncorrected"
    finally:
        gate.set()


# -- F5 ----------------------------------------------------------------------------------------------------------


def test_f5_mid_block_alternatives_are_ordered_sequences_of_their_own_blocks(tmp_path, monkeypatch):
    calls = _spy_builds(monkeypatch)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env, steps=2)
    args, kwargs, (_inputs, actions, _sources) = calls[0]
    by_id = kwargs["candidates"]
    first, second = [by_id[ref] for ref in kwargs["support"] if ref in by_id][:2]
    _inputs2, built, _ = BUILD(args[0], args[1], state=kwargs["state"], support=["a_then_b", "b_then_a"],
                            candidates={"a_then_b": first, "b_then_a": second}, now_iso=kwargs["now_iso"],
                            sequences={"a_then_b": (first, second), "b_then_a": (second, first)})
    plain = {action.ref: action for action in actions}
    a_then_b, b_then_a = built
    assert a_then_b.kind == b_then_a.kind == V.SEQUENCE
    assert [step.ref for step in a_then_b.steps] == [first.candidate_id, second.candidate_id]
    assert [step.ref for step in b_then_a.steps] == [second.candidate_id, first.candidate_id]
    # Each step keeps its own block's interface (kind, items, minutes), never the first block's.
    for step in (*a_then_b.steps, *b_then_a.steps):
        assert (step.kind, step.item_los, step.minutes) == (plain[step.ref].kind, plain[step.ref].item_los,
                                                            plain[step.ref].minutes)
    assert a_then_b.minutes == pytest.approx(first.est_minutes + second.est_minutes)

    # The restraint gate hands the numeric policy both orders as sequences.
    seen: dict[str, Any] = {}
    monkeypatch.setattr(OC, "run_numeric", lambda *a, **kw: seen.update(kw) or OC.NumericPolicy(status="answered"))
    insert = SimpleNamespace(candidate_id="insert_now")
    cont = SimpleNamespace(candidate_id="continue_current")
    gate = SimpleNamespace(vault=env.vault, repository=env.repository, runtime=fake_runtime())
    OC.ObjectiveRestraintGate._numeric_restraint(gate, kwargs["state"], insert, cont, kwargs["now_iso"], "key")
    assert seen["sequences"] == {"insert_now": (insert, cont), "continue_current": (cont, insert)}
    assert seen["candidates"] == {"insert_now": insert, "continue_current": cont}


# -- F8 ----------------------------------------------------------------------------------------------------------


def test_f8_ad_reports_the_reading_dose_position_only_when_asked(tmp_path):
    from learnloop.adaptive_difficulty import readiness as RD

    from tests.ad23_fakes import LO, ad23_vault, restamp
    from tests.ad3_reading_helpers import _opportunity

    paths = ad23_vault(tmp_path, items=("pi_r1", "pi_r2", "pi_r3"), config="[router]\nenabled = false\n")
    with closing(connect(paths.sqlite_path)) as connection:
        for key, at in (("o1", "2026-10-12T08:00:00Z"), ("o2", "2026-10-12T08:30:00Z")):
            _opportunity(connection, key=key, kind="reading", subkind="section_read",
                         source_table="reader_section_progress", at=at)
        connection.commit()
    restamp(paths)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    asked = RD.decision_state_fields(vault, repository, [LO], reading_doses=True)
    assert asked["status"] == "live"
    assert asked["los"][LO]["reading_dose"] == pytest.approx(2.0)
    assert "reading_dose" not in RD.decision_state_fields(vault, repository, [LO])["los"][LO]  # RO0's rows unchanged


def test_f8_a_reading_candidate_starts_from_ads_dose_position(tmp_path, monkeypatch):
    calls = _spy_builds(monkeypatch)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env, steps=2)
    args, kwargs, (inputs, _actions, _sources) = calls[0]
    lo = inputs.topics[0].lo

    def ad(vault, repository, los):
        return {"status": "live", "los": {lo: {"p_bar_at_top_raw": 0.6, "untested": False, "cell": ["f", "c"],
                                               "reading_dose": 3.0}}}

    monkeypatch.setattr(OI, "_ad", ad)
    rebuilt, _acts, sources = BUILD(*args, **kwargs)
    topic = next(t for t in rebuilt.topics if t.lo == lo)
    assert topic.reading_count == pytest.approx(3.0)
    assert sources["topics"][lo]["reading_dose"] == "ad_reading_window"
    # The rollout's next dose is AD's increment at n = 3, smaller than the first dose's.
    model = V._Model(rebuilt, 2, "f8")
    state = model.initial()
    before = state.bel[:, model.index[lo]].copy()
    model._read(state, model.index[lo], np.ones(2, dtype=bool))
    from learnloop.adaptive_difficulty.model import dose_increment

    inc = dose_increment(3.0, 1.0)
    learning = rebuilt.learning
    expected = learning.gbar[0][0] * inc[0] + learning.gbar[1][0] * inc[1]
    assert (state.bel[:, model.index[lo]] - before) == pytest.approx([expected, expected])
    first = dose_increment(0.0, 1.0)
    assert expected < learning.gbar[0][0] * first[0] + learning.gbar[1][0] * first[1]


# -- F9 ----------------------------------------------------------------------------------------------------------


def test_f9_the_drawn_options_forecast_is_resolved_and_reported(tmp_path):
    from learnloop.router_objective import forecast_resolve as FR
    from learnloop.router_objective import objective_report
    from learnloop.router_objective import trace as T

    from tests.ro2_history_resolve_helpers import _attempt, _iso

    from tests.ad_fakes import ad_plan_vault, plan_env
    from tests.ad_fakes import rows as ad_rows

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    pid = step["presentation_id"]
    presentation = ad_rows(paths.sqlite_path, "SELECT * FROM plan_presentations WHERE id = ?", (pid,))[0]
    decision_id = presentation["router_decision_id"]
    assert decision_id, "the served block has its router decision"
    start = clock.now()
    _attempt(paths, "att_block", presentation["practice_item_id"], _iso(start + timedelta(minutes=2)), presentation=pid)
    lo = step["learning_object_id"]
    body = {"candidates": {"blk": {"main_lo": lo, "sensors": {"llm_forecast": {"p_cold_1": 0.7, "p_cold_7": 0.6,
                                                                                "p_cold_30": 0.5}}},
                           "stop_for_today": {"main_lo": None, "sensors": {}}},
            "policies": {"llm": {"status": "answered", "model": "fake-router-llm"}, "numeric": {"status": "answered"}},
            "mixing": {"chosen": "blk", "drawn_component": "llm", "propensity": 0.5, "w": 0.8},
            "versions": {"objective": V.OBJECTIVE_VERSION, "llm_schema": "router_llm_choice_v3", "card": "c"},
            "evaluation": {}, "session": {}, "stop_in_support": True}
    with closing(connect(paths.sqlite_path)) as connection:
        assert store.insert_trace(connection, T.assemble(body, decision_id=decision_id, decision_kind="plan_block",
                                                          decision_state_id=None, algorithm_version=TAG,
                                                          local_date="2026-10-12", session_id=None,
                                                          created_at=_iso(start)))
        connection.commit()
    unseen = next(item for item in ("pi_m1a", "pi_m1b", "pi_m1c") if item != presentation["practice_item_id"])
    cold = _attempt(paths, "att_cold", unseen, _iso(start + timedelta(days=3)))
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    now = _iso(start + timedelta(days=4))
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        from learnloop.adaptive_difficulty.history_resolve import resolve_curves

        resolved = FR.resolve(connection, vault, repository, now=now, resolve_curves=resolve_curves)
        report = objective_report.build(connection, now=now, forecasts=resolved)
    found = [row for row in resolved["rows"] if row["forecaster"] == FR.FORECASTER]
    assert {row["binding"] for row in found} == {"per_protocol", "intention_to_treat"}
    for row in found:
        assert row["status"] == "scored" and row["attempt_id"] == cold and row["y"] == 1.0
        assert row["p"] == pytest.approx(0.7 - 0.1 * math.log(row["lag_days"]) / math.log(7))
        assert row["binding_version"] == FR.BINDING_VERSION and row["decision_id"] == decision_id
    forecast = report["forecast"]
    assert forecast["forecaster"] == FR.FORECASTER and forecast["unique_assessments"] == 1
    assert {row["binding"]: row["scored"] for row in forecast["comparators"]} == {"per_protocol": 1,
                                                                                  "intention_to_treat": 1}
    assert "never enters w" in forecast["label"]
    assert any("forecast (" in line for line in objective_report.lines(report))


# -- F10 ---------------------------------------------------------------------------------------------------------


def test_f10_the_policy_card_names_each_goals_topics_and_their_weights(tmp_path):
    from learnloop.daily_plan.objective_card import decision_card

    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    titles = {lo_id: lo.title for lo_id, lo in env.vault.learning_objects.items()}
    a, b = "lo_m1", "lo_p1"

    def card(per_lo):
        goals = {"g": {"due_at": "2026-12-01T00:00:00Z", "days_to_date": 20.0, "dated": 1.0, "undated_density": 1 / 90,
                       "per_lo": per_lo, "source": "contract", "scope": 2, "los": [a, b]}}
        return decision_card(env.vault, env.repository, [], served_at="2026-11-05T10:00:00Z", goals=goals, session={},
                             budget=48_000)["state"]["goals"]["g"]

    one, other = card({a: 100.0, b: 0.0}), card({a: 0.0, b: 100.0})
    assert one != other
    assert set(one["topics"]) == {titles[a], titles[b]}
    assert one["topic_weights"] == {titles[a]: 100.0, titles[b]: 0.0}


# -- F11 ---------------------------------------------------------------------------------------------------------


def test_f11_the_evaluation_population_does_not_depend_on_candidate_support(tmp_path, monkeypatch):
    calls = _spy_builds(monkeypatch)
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    def candidate_only(sources):
        return {lo for lo, source in sources["topics"].items() if source["density"] == "candidate_only"}

    found = [(args, kwargs, out) for args, kwargs, out in calls if candidate_only(out[2])]
    assert found, "some decision valued a candidate topic outside every goal and retention commitment"
    args, kwargs, (_inputs, _actions, sources) = found[0]
    assert not candidate_only(sources) & set(sources["population"]["los"])
    _i, _a, stop_only = BUILD(*args, **{**kwargs, "support": ["stop_for_today"]})
    assert stop_only["population"] == sources["population"]
    # With no model set up each decision builds once, in order: its trace's uses are its population.
    traces = _traces(env)
    assert len(traces) == len(calls)
    for (_args, _kwargs, (_inputs, _actions, built)), trace in zip(calls, traces, strict=True):
        uses = trace["trace"]["evaluation"]["uses"]
        assert uses["population_basis"]
        assert {use["lo"] for use in uses["topics"]} == {lo for lo, c in built["population"]["los"].items() if c > 0}
        assert not {use["lo"] for use in uses["topics"]} & candidate_only(built)
