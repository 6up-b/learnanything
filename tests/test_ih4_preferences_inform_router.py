"""Instruct hand-off IH4 (docs/specs/spec_instruct_handoff_v1.md §7, §10): how preferences inform the non-LLM parts.

"I would take this" is about acceptance: a request for a lesson updates TE1b's acceptance model, flagged unprompted, through
the model. "This would help me" is a claim to check against outcomes: a choice model frozen as a sensor, entering the value
through one coefficient, ``w_pref``, starting at 0 and fitted on the mix's randomized draws, never on a pick. Staged reads
nothing. The LLM's card carries the learner's own statements within its budget, with nothing protected. Off, or below the
tag, as IH3 left it. Fakes only; no model call.
"""

from __future__ import annotations

import ast
import json
import pathlib
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.config.schema import LearnLoopConfig
from learnloop.daily_plan import learner_action as LA
from learnloop.daily_plan import lesson_offer as LO
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.daily_plan import objective_card as OCARD
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.staged_frame import StagedChooser
from learnloop.db.stores import router as router_store
from learnloop.db.stores import router_objective as trace_store
from learnloop.db.stores import router_suggestions as SUG
from learnloop.ops.capture_report import build_report, lines
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import mix
from learnloop.router_objective import preference_report as PR
from learnloop.router_objective import preferences as PF
from learnloop.router_objective import scores as S
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective_switches import preferences_inform_router_on
from learnloop.scheduling.device_eligibility import PlanStepFilter
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import record_attempt
from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version
from tests.router_mixture_helpers import join_carried_valuations, mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.test_ih_numeric_seed import spy  # noqa: F401 - the fixture
from tests.test_instruct_handoff_ih0 import make_world  # noqa: F401 - the fixture
from tests.test_ro4_objective_serving import policy_answer
from tests.test_rospeed2_connections import _canon
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
QUIET = "[router_objective]\nstop_coin = 0.0\n"
OFF = QUIET + "preferences_inform_router = false\n"
EXTERIOR_NOTE = "softmax against argmax is what I keep mixing up"


@pytest.fixture
def draw(monkeypatch):
    """The mix serves the first of ``draw.prefer`` in the support (its probability the exact ``μ``)."""

    real = mix.draw
    control = SimpleNamespace(prefer=())

    def fake(support, parts, weights, epsilon, seed):
        drawn = real(support, parts, weights, epsilon, seed)
        for ref in control.prefer:
            match = next((option for option in support if str(option).startswith(ref)), None)
            if match is not None:
                return replace(drawn, chosen=match, propensity=drawn.pi[match])
        return drawn

    monkeypatch.setattr(mix, "draw", fake)
    return control


def _env(tmp_path, *, version: str = TAG, toml: str = QUIET, runtime=None):
    return mixture_env(tmp_path, runtime or fake_runtime(), version=version, toml=toml, session_id="s1")


def _open_offer(env, draw) -> dict[str, Any]:
    draw.prefer = (OFFER,)
    for _ in range(8):
        _record, step = advance(env, serve=True)
        assert step is not None and step["kind"] == "item"
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _record, step = advance(env, serve=False)
        if any(row["policy"] == mix.POLICY for row in rows(env)):
            assert step["kind"] == "lesson_offer"
            return step
    raise AssertionError("the objective never decided a boundary")


FEATURES = {"local_hour": 9.0, "minutes_left": 30.0, "last_miss": 1.0}


def _offered(*kinds: str, drawn: bool = False, pick: str | None = None, features: Any = FEATURES) -> str:
    body: dict[str, Any] = {"version": LA.PREFERENCE_VERSION, "drawn": drawn, "device": "desktop",
                            "router_pick": {"kind": pick, "ref": "x", "propensity": 0.5} if pick else None,
                            "options": [{"kind": kind, "ref": f"ref:{kind}"} for kind in kinds]}
    if features is not None:
        body[PF.FEATURES_KEY] = features
    return json.dumps(body)


def _insert(env, pid: str, kind: str, *, at: str | None = None, decision: str | None = None, served: str | None = None,
            attempt: str | None = None, note: str | None = None, offered: str | None = None) -> None:
    row = {"id": pid, "decision_id": decision, "attempt_id": attempt, "session_id": env.session_id, "surface": "feedback",
           "offered_json": offered or _offered(*LA.KINDS), "chosen_kind": kind, "chosen_ref": f"ref:{kind}", "note_md": note,
           "served_decision_id": served, "algorithm_version": TAG, "created_at": at or env.now_iso()}
    with env.repository.atomic(), env.repository.connection() as connection:
        assert router_store.insert_learner_preference(connection, row)


def _preferences(env) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        return router_store.learner_preference_rows(connection)


def _traces(env) -> list[dict[str, Any]]:
    with env.repository.connection() as connection:
        return [trace_store.trace(connection, row["decision_id"])["trace"] for row in trace_store.traces(connection)
                if row["decision_kind"] == "plan_block"]


def _pin(monkeypatch) -> Any:
    """RO5's method: the plan's and the attempt's fresh ids and the version out of the key, so twin plans seed alike."""

    real_hash = OC._hash
    monkeypatch.setattr(OC, "_hash", lambda value: real_hash(
        {k: v for k, v in value.items() if k not in ("version", "plan_id")} if isinstance(value, dict) else value))
    monkeypatch.setattr(OC, "_latest_attempt", lambda _repository: "pinned-attempt")
    return lambda _key, _decision: "pinned-seed"


def _numbers(trace: dict[str, Any]) -> dict[str, Any]:
    return {"candidates": {ref: entry.get("terms") for ref, entry in trace["candidates"].items()},
            "mu": trace["mixing"]["mu"], "numeric": {key: trace["policies"]["numeric"][key] for key in ("choice", "tie")},
            "residual": {key: (trace.get("residual") or {}).get(key) for key in ("w_hat", "fit", "candidates")}}


# -- the switch --------------------------------------------------------------------------------------------------------


def test_the_gate_reads_off_below_the_tag_switched_off_and_with_the_objective_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not preferences_inform_router_on(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert preferences_inform_router_on(load_vault(paths.root).config)
    for n, toml in enumerate(("[router_objective]\npreferences_inform_router = false\n",
                              "[router_objective]\nenabled = false\n")):
        other = create_basic_vault(tmp_path / f"off{n}")
        set_algorithm_version(other, TAG)
        append_config_toml(other.root, toml)
        assert not preferences_inform_router_on(load_vault(other.root).config), toml
    assert LearnLoopConfig().router_objective.preferences_inform_router is True
    rule = classify_config_path("router_objective.preferences_inform_router")
    assert rule is not None and "kill switch" in rule.rationale and "IH4" in rule.rationale


def test_the_key_names_the_switch_only_while_it_serves_and_the_seed_never(tmp_path):
    on = _env(tmp_path / "on")
    off = _env(tmp_path / "off", toml=OFF)
    below = _env(tmp_path / "below", version=OLD, toml=QUIET)
    named = OC.objective_settings(on.vault.config)
    assert named["preferences_inform_router"] is True
    assert "preferences_inform_router" not in OC.objective_settings(off.vault.config)
    assert "preferences_inform_router" not in OC.objective_settings(below.vault.config)
    identity = {"kind": "objective_block", "objective": named, "as_of": "x", "preferences": {"n": 3, "latest": "y"}}
    without = {"kind": "objective_block", "as_of": "x",
               "objective": {key: value for key, value in named.items() if key != "preferences_inform_router"}}
    assert OC.numeric_seed(identity) == OC.numeric_seed(without)
    assert OC._hash(identity) != OC._hash(without)


# -- acceptance --------------------------------------------------------------------------------------------------------


CONTEXT = LS.Context(local_hour=9.0, minutes_left=30.0, reentry=False, days_since_last=None)
CANDIDATE = LS.Candidate(ref="lesson:x", learning_object_ids=("x",), reason="new_goal", predicted_success=0.4)


def _request(at: str = "2026-11-01T00:00:00Z") -> LS.Observation:
    return LS.Observation(CONTEXT, CANDIDATE, True, at, unprompted=True)


def test_with_no_request_the_model_is_te1bs_exactly():
    answered = [LS.Observation(CONTEXT, CANDIDATE, value, f"2026-11-0{n + 1}T00:00:00Z")
                for n, value in enumerate((True, False, False))]
    state = LS.replay(LS.with_unprompted(answered, []))
    plain = LS.AcceptanceState()
    for row in answered:
        plain.observe(row.context, row.candidate, row.accepted)
    assert state.p_accept(CONTEXT, CANDIDATE) == plain.p_accept(CONTEXT, CANDIDATE)
    for bank, other in zip(state.banks, plain.banks):
        assert bank.mean.shape == (len(LS.TERMS),) and bank.mean.tobytes() == other.mean.tobytes()
        assert bank.cov.tobytes() == other.cov.tobytes()
    assert state.summary() == plain.summary()
    assert "unprompted_updates" not in state.summary() and state.priors_version == LS.PRIORS_VERSION


def test_a_request_is_flagged_and_moves_the_offer_only_through_its_posterior():
    state = LS.replay([_request()])
    assert state.unprompted_updates == 1 and state.updates == 1 and state.priors_version == LS.UNPROMPTED_PRIORS_VERSION
    summary = state.summary()
    assert summary["unprompted_updates"] == 1 and set(summary["means"]) == {*LS.TERMS, LS.UNPROMPTED_TERM}
    # It moves the offer's prediction, and the offset takes a share of the step: there is no weight to set.
    prior = LS.AcceptanceState().p_accept(CONTEXT, CANDIDATE)
    assert state.p_accept(CONTEXT, CANDIDATE) > prior
    assert summary["means"][LS.UNPROMPTED_TERM] > 0.0
    # An offer's prediction never sets the offset's slot.
    bank = state.banks[0]
    assert state.design(bank, CONTEXT, CANDIDATE)[-1] == 0.0
    assert state.design(bank, CONTEXT, CANDIDATE, unprompted=True)[-1] == 1.0


def test_the_more_offers_have_said_the_more_a_request_goes_to_its_own_offset():
    """The split is the posterior's: no hand-set weight stands between a request and a response. Offers pin the effects
    an offer reads, so a later request moves them less and its own offset takes more of the step."""

    answered = [LS.Observation(CONTEXT, CANDIDATE, n % 2 == 0, f"2026-10-{n + 1:02d}T00:00:00Z") for n in range(20)]

    def steps(rows_: list[LS.Observation]) -> tuple[float, float]:
        before = LS.replay(rows_).summary()["means"]
        after = LS.replay([*rows_, _request()]).summary()["means"]
        return after["intercept"] - before["intercept"], after[LS.UNPROMPTED_TERM]

    few_shared, few_own = steps(answered[:1])
    many_shared, many_own = steps(answered)
    assert 0.0 < many_shared < few_shared
    assert many_own / many_shared > few_own / few_shared
    # And a request can't stand in for an answered offer: it moves the prediction less than a Start would.
    many = LS.replay(answered).p_accept(CONTEXT, CANDIDATE)
    asked = LS.replay([*answered, _request()]).p_accept(CONTEXT, CANDIDATE)
    started = LS.replay([*answered, LS.Observation(CONTEXT, CANDIDATE, True, "2026-11-01T00:00:00Z")])
    assert many < asked < started.p_accept(CONTEXT, CANDIDATE)


def test_the_requests_join_the_ledgers_order_and_a_tie_keeps_the_response_first():
    answered = [LS.Observation(CONTEXT, CANDIDATE, True, "2026-11-01T00:00:00Z"),
                LS.Observation(CONTEXT, CANDIDATE, False, "2026-11-03T00:00:00Z")]
    merged = LS.with_unprompted(answered, [_request("2026-11-01T00:00:00Z"), _request("2026-11-02T00:00:00Z")])
    assert [(row.at[:10], row.unprompted) for row in merged] == [
        ("2026-11-01", False), ("2026-11-01", True), ("2026-11-02", True), ("2026-11-03", False)]


@pytest.mark.usefixtures("offerable")
def test_a_learner_asked_lesson_reaches_p_accept_flagged_unprompted(tmp_path, draw):
    env = _env(tmp_path)
    advance(env, serve=True)
    live = LA.options(env)
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    before = LO.build(env.vault, env.repository, today=env.today(), now_iso=env.now_iso(), local_hour=9.0, minutes_left=30.0,
                      reentry=False, forced=False, learner_asked=True).candidate
    result = LA.choose(env, kind=LA.LESSON, ref=lesson.ref, surface="feedback", attempt_id=None, note_md=None,
                       preference_id="p1")
    assert result.outcome == "lesson"
    row = _preferences(env)[0]
    assert row["decision_id"] is None and json.loads(row["offered_json"])[LS.LESSON_INPUTS]["candidate"]["reason"]
    requests = LS.unprompted_observations([row], at=env.now_iso())
    assert len(requests) == 1 and requests[0].unprompted and requests[0].accepted
    env.clock.advance(1)
    after = LO.build(env.vault, env.repository, today=env.today(), now_iso=env.now_iso(), local_hour=9.0, minutes_left=30.0,
                     reentry=False, forced=False, learner_asked=True).candidate
    old_record, new_record = LO.card(before), LO.card(after)
    assert new_record["model"]["unprompted_updates"] == 1 and "unprompted_updates" not in old_record["model"]
    assert new_record["priors_version"] == LS.UNPROMPTED_PRIORS_VERSION
    assert new_record["p_accept"]["mean"] > old_record["p_accept"]["mean"]
    # Exactly the model's posterior for this context and candidate: nothing else touches the number.
    state = LS.replay(requests)
    context = LS.Context.from_dict(new_record["context"])
    scored = LS.Candidate.from_dict(new_record["card"]["candidates"][0])
    mean, _sd = LO.accept_moments(state, context, scored)
    assert new_record["p_accept"]["mean"] == pytest.approx(mean, abs=1e-8)
    # TE1b's own daily draw reads nothing of it: where it runs, the objective doesn't serve the plan.
    with env.repository.connection() as connection:
        assert SG._model(connection, with_offers=True)[0].unprompted_updates == 0


@pytest.mark.usefixtures("offerable")
def test_choosing_the_offer_the_plan_drew_is_no_request(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    live = LA.options(env)
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    assert lesson.plans_pick
    result = LA.choose(env, kind=LA.LESSON, ref=lesson.ref, surface="today", attempt_id=None, note_md=None,
                       preference_id="agreed")
    assert result.outcome == "agreed"
    assert LS.unprompted_observations(_preferences(env), at=env.now_iso()) == []


@pytest.mark.usefixtures("offerable")
def test_a_row_written_with_the_switch_off_froze_nothing_and_is_not_read(tmp_path, draw):
    env = _env(tmp_path, toml=OFF)
    advance(env, serve=True)
    live = LA.options(env)
    offered = live.offered()
    assert PF.FEATURES_KEY not in offered and LS.LESSON_INPUTS not in offered
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    LA.choose(env, kind=LA.LESSON, ref=lesson.ref, surface="feedback", attempt_id=None, note_md=None, preference_id="p1")
    rows_ = _preferences(env)
    assert LS.unprompted_observations(rows_) == []
    state, counts = PF.replay(rows_)
    assert state.updates == 0 and counts == {"on_record": 1, "read": 0, "no_frozen_features": 1, "agreed": 0, "no_draw": 0}


# -- the choice model --------------------------------------------------------------------------------------------------


def _row(kind: str, n: int, *, parent: str | None = None, served: str | None = None, offered: str | None = None) -> dict[str, Any]:
    return {"id": f"p{n}", "created_at": f"2026-11-01T00:{n:02d}:00Z", "chosen_kind": kind, "decision_id": parent,
            "served_decision_id": served, "offered_json": offered or _offered(*LA.KINDS)}


def test_the_kinds_are_the_plans_own_names():
    """The leaf keeps its own copies of the plan's names, since ``router_objective`` sits below the plan."""

    from learnloop.daily_plan.types import LESSON_OFFER_PREFIX, LESSON_OFFER_SUBTYPE, STOP_FOR_TODAY
    from learnloop.router_objective.stop_coin import STOP as COIN_STOP

    assert PF._LESSON_SUBTYPE == LESSON_OFFER_SUBTYPE and PR.OFFER_PREFIX == LESSON_OFFER_PREFIX
    assert COIN_STOP == STOP_FOR_TODAY
    assert PF.kind_of(reading=None, subtype=LESSON_OFFER_SUBTYPE, lane="new") == LA.LESSON
    assert LA.kind_of is PF.kind_of and LS.LESSON_KIND == LA.LESSON


def test_with_nothing_on_record_every_kind_is_equal():
    state, counts = PF.replay([])
    features = PF.Features(9.0, 30.0, 1.0)
    p = state.predict(features, list(LA.KINDS))
    assert state.updates == 0 and counts["on_record"] == 0
    assert len(set(p.values())) == 1 and sum(p.values()) == pytest.approx(1.0)
    # One in six at the reference: the seeded centre, TE1b's construction.
    raw = PF.gaussian_sigmoid_mean(float(PF._prior()[0][0]), 2.0)
    assert raw == pytest.approx(1.0 / len(LA.KINDS), abs=1e-9)


def test_the_kind_chosen_rises_and_nothing_reads_a_decision_where_the_link_was_not_used():
    features = PF.Features(9.0, 30.0, 1.0)
    state, counts = PF.replay([_row(LA.LESSON, 1), _row(LA.LESSON, 2)])
    assert state.updates == 2 and counts["read"] == 2
    p = state.predict(features, list(LA.KINDS))
    assert p[LA.LESSON] == max(p.values()) and p[LA.LESSON] > 1.0 / 6.0
    # The only input is the ledger: a thousand served decisions add no row and move nothing.
    again, _ = PF.replay([_row(LA.LESSON, 1), _row(LA.LESSON, 2)])
    assert again.predict(features, list(LA.KINDS)) == p
    # A kind offered and passed over does not fall below one that was never offered in the model's reading of it.
    limited = _offered(LA.LESSON, LA.QUESTION, LA.STOP)
    other, _ = PF.replay([_row(LA.LESSON, 1, offered=limited)])
    read = other.predict(features, [LA.LESSON, LA.QUESTION, LA.READ])
    assert read[LA.LESSON] > read[LA.READ] > 0.0 and read[LA.READ] >= read[LA.QUESTION]


def _phone_agrees(env, draw):
    """A phone's "learn this" on the offer the desktop drew: nothing on its screen showed it (second review, R2-m3)."""

    step = _open_offer(env, draw)
    desktop = env.device
    env.device = PlanStepFilter(device_filter=None)
    made = LA.choose(env, kind=LA.LESSON, ref=None, surface="phone_feedback", attempt_id=None, note_md=None,
                     preference_id="phone_agrees")
    env.device = desktop
    assert made.outcome == LA.WAITS_ON_DESKTOP and made.served_decision_id == step["offer"]["decision_id"]
    return step


def _requests(env, *, at=None):
    with env.repository.connection() as connection:
        return LS.unprompted_observations(router_store.learner_preference_rows(connection), at=at or env.now_iso(),
                                          responses=SUG.responses(connection))


def _answers(env):
    with env.repository.connection() as connection:
        details = {str(row["id"]): row["detail"] for row in SUG.all_decisions(connection)}
        return [row.accepted for row in LS.observations(details, SUG.responses(connection))]


def test_the_phone_surfaces_are_the_same_list_in_both_modules():
    assert LS.PHONE_SURFACES == LA.PHONE_SURFACES


@pytest.mark.usefixtures("offerable")
def test_a_phone_agreement_is_a_request_it_reaches_the_model_on_the_drawn_offers_card(tmp_path, draw):
    env = _env(tmp_path)
    step = _phone_agrees(env, draw)
    (request,) = _requests(env)
    assert request.accepted and request.unprompted
    assert request.candidate.ref == step["offer"]["suggestion"]["ref"]
    # The desktop never rendered it: the offer ends as the plan's act, and the request is still the learner's word.
    env.clock.advance(60 * 26)
    with env.repository.atomic(), env.repository.connection() as connection:
        LO.sweep_ignored(connection, config=env.vault.config, today=env.today(), now_iso=env.now_iso())
    assert _answers(env) == [] and len(_requests(env)) == 1


@pytest.mark.usefixtures("offerable")
@pytest.mark.parametrize("response, seen", [("accepted", [True]), ("declined", [False])])
def test_an_answer_on_the_desktop_to_what_the_phone_asked_for_counts_once(tmp_path, draw, response, seen):
    env = _env(tmp_path)
    step = _phone_agrees(env, draw)
    before = env.now_iso()
    env.clock.advance(1)
    SG.respond(env.vault, env.repository, decision_id=step["offer"]["decision_id"], response=response, clock=env.clock)
    assert _answers(env) == seen and _requests(env) == []
    # As of before the answer, the request was all there was.
    assert len(_requests(env, at=before)) == 1


@pytest.mark.usefixtures("offerable")
def test_a_card_passed_over_is_no_answer_so_the_phones_request_still_counts(tmp_path, draw):
    env = _env(tmp_path)
    step = _phone_agrees(env, draw)
    LO.record_shown(env.repository, block_id=step["block_id"], surface="today", session_id=env.session_id)
    env.clock.advance(60 * 26)
    with env.repository.atomic(), env.repository.connection() as connection:
        LO.sweep_ignored(connection, config=env.vault.config, today=env.today(), now_iso=env.now_iso())
    assert _answers(env) == [False] and len(_requests(env)) == 1


def test_an_agreement_and_a_preference_with_no_draw_each_count_as_a_choice():
    agreed = _row(LA.QUESTION, 1, parent="d1", served="d1")
    no_draw = _row(LA.REVIEW, 2)
    overridden = _row(LA.NEW, 3, parent="d2", served="pick")
    state, counts = PF.replay([agreed, no_draw, overridden])
    assert state.updates == 3
    assert counts == {"on_record": 3, "read": 3, "no_frozen_features": 0, "agreed": 1, "no_draw": 1}


def test_the_replay_reads_only_what_was_known_at_the_moment():
    rows_ = [_row(LA.QUESTION, 1), _row(LA.QUESTION, 30)]
    state, counts = PF.replay(rows_, at="2026-11-01T00:10:00Z")
    assert state.updates == 1 and counts["on_record"] == 1


def test_no_module_of_this_stage_branches_on_a_score_or_a_stuck_flag():
    from tests.test_ih2_lessons_compete import EVIDENCE_WORDS, _names_in

    root = pathlib.Path(PF.__file__).resolve().parents[1]
    for relative in ("router_objective/preferences.py", "router_objective/preference_report.py"):
        tree = ast.parse((root / relative).read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
                assert not _names_in(node.test) & set(EVIDENCE_WORDS), relative


# -- the sensor, frozen in the trace -----------------------------------------------------------------------------------


def test_with_no_preference_the_trace_gains_nothing_and_the_numbers_are_the_predecessors(tmp_path, monkeypatch):
    join_carried_valuations(monkeypatch)  # review 3, m5: the twins compare residual numbers across serves
    pinned = _pin(monkeypatch)
    on = mixture_env(tmp_path / "on", fake_runtime(seed=pinned), version=TAG, toml=QUIET, session_id="s1")
    off = mixture_env(tmp_path / "off", fake_runtime(seed=pinned), version=TAG, toml=OFF, session_id="s1")
    run(on), run(off)
    on_traces, off_traces = _traces(on), _traces(off)
    assert on_traces and len(on_traces) == len(off_traces)
    assert all("preference" not in trace and "learner_statements" not in trace for trace in on_traces)
    assert [_numbers(trace) for trace in on_traces] == [_numbers(trace) for trace in off_traces]


def _twins_with_one_slow_carry(tmp_path, monkeypatch, *, joined: bool) -> tuple[list[Any], list[Any]]:
    """The reviewer's reproduction (review 3, m5): one twin's carried-valuation thread runs late, as a loaded machine
    would schedule it; the draw count is untouched."""

    import time

    real = OC._drain_carry

    def slow(sqlite_path, *, deadline=None):
        if "/on/" in str(sqlite_path):
            time.sleep(1.5)
        return real(sqlite_path, deadline=deadline)

    monkeypatch.setattr(OC, "_drain_carry", slow)
    if joined:
        join_carried_valuations(monkeypatch)
    pinned = _pin(monkeypatch)
    on = mixture_env(tmp_path / "on", fake_runtime(seed=pinned), version=TAG, toml=QUIET, session_id="s1")
    off = mixture_env(tmp_path / "off", fake_runtime(seed=pinned), version=TAG, toml=OFF, session_id="s1")
    run(on), run(off)
    return [_numbers(trace) for trace in _traces(on)], [_numbers(trace) for trace in _traces(off)]


def test_a_late_carry_thread_in_one_twin_no_longer_moves_the_comparison(tmp_path, monkeypatch):
    """With the carry joined after each serve, a carry thread delayed in one twin only leaves the twins' numbers equal
    (unjoined, decision 4's residual fit and every ``v_residual`` differ: the race the two twin tests above had)."""

    on, off = _twins_with_one_slow_carry(tmp_path, monkeypatch, joined=True)
    assert on and on == off


def test_the_sensor_is_frozen_in_the_trace_and_w_pref_starts_at_zero(tmp_path):
    env = _env(tmp_path)
    _insert(env, "p1", LA.QUESTION)
    env.clock.advance(1)
    run(env)
    traces = _traces(env)
    assert traces
    sensor = traces[-1]["preference"]
    assert sensor["status"] == "applied" and sensor["version"] == PF.VERSION and sensor["w_pref"] == 0.0
    choice = sensor["choice"]
    assert choice["version"] == PF.CHOICE_VERSION and choice["priors_version"] == PF.PRIORS_VERSION
    assert choice["updates"] == 1 and choice["self_selected"] is True and "link" in choice["basis"]
    assert set(choice["features"]) == {"local_hour", "minutes_left", "last_miss"}
    assert sensor["weight"]["n"] == 0 and sensor["weight"]["source"].startswith("prior:")
    support = traces[-1]["mixing"]["mu"]
    assert set(sensor["candidates"]) == set(support)
    assert all(entry["kind"] in PF.KINDS and isinstance(entry["v_pref"], str) for entry in sensor["candidates"].values())
    assert sum(choice["p"].values()) == pytest.approx(1.0, abs=1e-5)


def test_v_pref_is_on_the_tails_scale_and_zero_with_no_spread():
    value = PF.scaled({"a": 0.5, "b": 0.3, "c": 0.2}, {"a": 0.1, "b": 0.2, "c": 0.6})
    assert sum(value.values()) == pytest.approx(0.0, abs=1e-12) and value["a"] > value["b"] > value["c"]
    import statistics

    assert statistics.pstdev(value.values()) == pytest.approx(statistics.pstdev((0.1, 0.2, 0.6)))
    assert PF.scaled({"a": 0.5, "b": 0.5}, {"a": 0.1, "b": 0.2}) == {"a": 0.0, "b": 0.0}
    assert PF.scaled({"a": 0.5, "b": 0.3}, {"a": 0.2, "b": 0.2}) == {"a": 0.0, "b": 0.0}


def test_w_pref_at_zero_changes_nothing_bit_for_bit_with_preferences_on_record(tmp_path, monkeypatch):
    """The same boundary with the switch on and off, preferences on record: the sensor is in the trace, and every value,
    the choice, its tie rule and the mix are the same bits. (A lesson request is another channel: the next test.)"""

    join_carried_valuations(monkeypatch)  # review 3, m5: the twins compare residual numbers across serves
    pinned = _pin(monkeypatch)
    envs = {name: mixture_env(tmp_path / name, fake_runtime(seed=pinned), version=TAG, toml=toml, session_id="s1")
            for name, toml in (("on", QUIET), ("off", OFF))}
    for env in envs.values():
        _insert(env, "p1", LA.QUESTION, note="more questions please")
        _insert(env, "p2", LA.STOP)
        env.clock.advance(1)
        run(env)
    on, off = _traces(envs["on"]), _traces(envs["off"])
    assert on and len(on) == len(off)
    assert all(trace["preference"]["w_pref"] == 0.0 for trace in on) and all("preference" not in trace for trace in off)
    assert [_canon(_numbers(trace)) for trace in on] == [_canon(_numbers(trace)) for trace in off]


@pytest.mark.usefixtures("offerable")
def test_at_w_pref_zero_only_the_acceptance_channel_moves_a_lesson_offers_value(tmp_path, draw, monkeypatch):
    """§7 item 1 and item 3 kept apart: a lesson request reaches the offer's ``Q̄`` through ``P(accept)`` and nothing else
    (the offer's Beta, its branches); no other candidate's value and no block moves."""

    pinned = _pin(monkeypatch)
    envs = {name: mixture_env(tmp_path / name, fake_runtime(seed=pinned), version=TAG, toml=toml, session_id="s1")
            for name, toml in (("on", QUIET), ("off", OFF))}
    frozen = {"context": CONTEXT.as_dict(), "candidate": CANDIDATE.as_dict()}
    offered = json.loads(_offered(*LA.KINDS))
    offered[LS.LESSON_INPUTS] = frozen
    for env in envs.values():
        _insert(env, "asked", LA.LESSON, offered=json.dumps(offered))
        env.clock.advance(1)
        _open_offer(env, draw)
    on, off = _traces(envs["on"])[0], _traces(envs["off"])[0]
    assert on["candidates"][OFFER]["offer"]["sensors"]["p_accept"]["unprompted_updates"] == 1
    assert "unprompted_updates" not in off["candidates"][OFFER]["offer"]["sensors"]["p_accept"]
    assert on["candidates"][OFFER]["offer"]["sensors"]["p_accept"]["mean"] > off["candidates"][OFFER]["offer"]["sensors"]["p_accept"]["mean"]
    assert on["preference"]["w_pref"] == 0.0
    for ref in on["candidates"]:
        if ref != OFFER:
            assert on["candidates"][ref]["sensors"] == off["candidates"][ref]["sensors"]


def test_a_planted_w_pref_moves_the_argmax_and_leaves_the_tails_values(tmp_path, monkeypatch):
    """The channel works once data supports it: the choice runs on ``Ṽ``, the tie rule says so, ``Q̄`` stays the tail's."""

    def planted(_connection, _config, _rows, *, at):
        fit = LT.WeightFit(w_hat=1.0, slope_mean=1.0, slope_sd=0.1, tail_slope=None, n=9, forced=9, rank=0.9, p_rank=1.0,
                           sigma2=0.01, prior_sd=1.0, source="planted")
        return fit, {"n": 9}

    monkeypatch.setattr(PF, "weight", planted)
    pinned = _pin(monkeypatch)
    twin = {}
    for name, toml in (("on", QUIET), ("off", OFF)):
        env = mixture_env(tmp_path / name, fake_runtime(seed=pinned), version=TAG, toml=toml, session_id="s1")
        # The learner keeps choosing what the numeric policy doesn't: stop.
        for n in range(6):
            _insert(env, f"p{n}", LA.STOP, at=env.now_iso())
            env.clock.advance(1)
        run(env)
        twin[name] = _traces(env)
    moved = [(a, b) for a, b in zip(twin["on"], twin["off"]) if a["policies"]["numeric"]["choice"] != b["policies"]["numeric"]["choice"]]
    first = twin["on"][0]
    assert first["preference"]["w_pref"] == 1.0
    tie = first["policies"]["numeric"]["tie"]
    assert tie["on"] == "v_tail + w_hat * v_residual + w_pref * v_pref" and "before_preferences_argmax" in tie
    # ``Q̄`` is the tail's in every candidate's terms, whatever moved.
    assert {ref: entry["terms"]["q"] for ref, entry in first["candidates"].items()} == {
        ref: entry["terms"]["q"] for ref, entry in twin["off"][0]["candidates"].items()}
    # Its shift follows the frozen numbers exactly.
    sensor = first["preference"]["candidates"]
    assert PF.scaled({ref: float(entry["p"]) for ref, entry in sensor.items()},
                     {ref: entry["terms"]["q"] for ref, entry in first["candidates"].items()}).keys() == sensor.keys()
    assert moved, "the planted coefficient moved no choice in this run"


def test_a_failed_sensor_leaves_the_numeric_policy_as_it_was(tmp_path, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("no")

    monkeypatch.setattr(PF, "weight", broken)
    env = _env(tmp_path)
    _insert(env, "p1", LA.QUESTION)
    env.clock.advance(1)
    run(env)
    traces = _traces(env)
    assert traces and traces[0]["preference"]["status"] == "failed"
    assert traces[0]["policies"]["numeric"]["status"] == "answered"


def test_with_the_learned_tail_off_the_sensor_freezes_and_w_pref_is_not_fitted(tmp_path):
    env = _env(tmp_path, toml=QUIET + "learned_tail = false\n")
    _insert(env, "p1", LA.QUESTION)
    env.clock.advance(1)
    run(env)
    sensor = _traces(env)[0]["preference"]
    assert sensor["status"] == "applied" and sensor["w_pref"] == 0.0 and sensor["weight"] is None


# -- w_pref: what it reads and can't --------------------------------------------------------------------------------


def _contrast(n: int, *, b: float, served: str = "a", found: S.Bounded | None = None) -> LT.Contrast:
    p = {"a": 0.5 + 0.01 * (n % 7), "b": 0.3, "c": 0.2 - 0.01 * (n % 7)}
    q = {"a": 0.1 + 0.02 * (n % 5), "b": 0.2, "c": 0.3}
    values = PF.scaled(p, q)
    return PF.contrast(decision_id=f"d{n}", decided_at="2026-11-01T00:00:00Z", window_closes_at="2026-11-15T00:00:00Z",
                       served=served, distribution={"a": 0.4, "b": 0.3, "c": 0.3}, values=values, tail=q,
                       found=found if found is not None else S.Bounded(value=q[served] + b * values[served]))


def _draws(n: int, *, b: float, noise: float, rng: Any) -> list[LT.Contrast]:
    """``n`` decisions with their own model reading, tail and mix; the served action drawn from the mix."""

    out = []
    for i in range(n):
        refs = ["a", "b", "c"]
        raw = [rng.uniform(0.05, 0.6) for _ in refs]
        p = {ref: value / sum(raw) for ref, value in zip(refs, raw)}
        q = {ref: rng.gauss(0.0, 0.2) for ref in refs}
        weights = [rng.random() + 0.05 for _ in refs]
        pi = {ref: value / sum(weights) for ref, value in zip(refs, weights)}
        served = rng.choices(refs, [pi[ref] for ref in refs])[0]
        values = PF.scaled(p, q)
        found = S.Bounded(value=q[served] + b * values[served] + rng.gauss(0.0, noise))
        one = PF.contrast(decision_id=f"d{i}", decided_at="t", window_closes_at="t", served=served, distribution=pi,
                          values=values, tail=q, found=found)
        if one is not None:
            out.append(one)
    return out


def test_no_contrast_is_exactly_zero():
    fit = PF.fitted([], prior_sd=1.0)
    assert fit.w_hat == 0.0 and fit.n == 0 and fit.version == PF.WEIGHT_VERSION and fit.source.startswith("prior:")


def test_one_draw_moves_nothing_where_a_fit_through_it_would():
    one = _contrast(1, b=1.0)
    fit = PF.fitted([one], prior_sd=1.0)
    assert fit.n == 1 and fit.w_hat == 0.0
    # RO6's estimate on the same row reports no noise, and so drops the prior.
    assert LT.residual_weight([one], prior_sd=1.0).sigma2 < fit.sigma2


def test_a_real_effect_in_the_randomized_draws_moves_it_and_the_null_much_less():
    import random
    import statistics

    rng = random.Random(7)
    real = [PF.fitted(_draws(300, b=0.5, noise=0.1, rng=rng), prior_sd=1.0).w_hat for _ in range(20)]
    null = [PF.fitted(_draws(300, b=0.0, noise=0.1, rng=rng), prior_sd=1.0).w_hat for _ in range(20)]
    assert statistics.mean(real) > 0.3
    assert statistics.mean(null) < 0.1
    assert all(0.0 <= value <= 1.0 for value in (*real, *null))


def test_missing_terms_are_read_at_the_fill_least_favourable_to_it():
    found = S.Bounded(value=0.2, lo=-5.0, hi=5.0, missing=3, reason="no_draw_day:3")
    rows_ = [_contrast(n, b=0.0, served="abc"[n % 3], found=found) for n in range(30)]
    assert all(row.missing == 3 and row.realized_lo < row.realized_hi for row in rows_)
    fit = PF.fitted(rows_, prior_sd=1.0)
    assert fit.bound == LT.LEAST_FAVOURABLE and fit.w_hat == 0.0


def test_a_decision_of_one_kind_has_nothing_to_test():
    assert PF.contrast(decision_id="d", decided_at="t", window_closes_at="t", served="a",
                       distribution={"a": 0.5, "b": 0.5}, values={"a": 0.0, "b": 0.0}, tail={"a": 0.1, "b": 0.2},
                       found=S.Bounded(value=1.0)) is None


def test_picks_are_never_in_its_cohort_and_an_overridden_draw_is(tmp_path, draw):
    """Only rows that aren't self-selected: a ``learner_pick`` has no trace and no propensity; the draw it overrode stays,
    as what was drawn."""

    env = _env(tmp_path)
    _insert(env, "seed", LA.STOP)
    env.clock.advance(1)
    draw.prefer = ("",)  # the first of the support, never the stop that would close the plan
    _record, step = advance(env, serve=True)
    # Answer until the feedback read draws a decision with a frozen sensor, then override what it drew.
    for _ in range(8):
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _record, step = advance(env, serve=False)
        if _traces(env):
            break
        _record, step = advance(env, serve=True)
    assert _traces(env)[-1]["preference"]["choice"]["updates"] == 1
    parent = rows(env)[-1]
    assert parent["policy"] == mix.POLICY
    live = LA.options(env)
    assert live.decision_id == parent["id"]
    pick = next(option for option in live.options if not option.plans_pick and option.candidate is not None)
    result = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="today", attempt_id=None, note_md=None, preference_id="over")
    assert result.outcome == "served"
    picks = {row["id"] for row in rows(env, "learner_pick")}
    assert picks and all(row["propensity"] is None for row in rows(env, "learner_pick"))
    later = "2027-06-01T00:00:00Z"
    with env.repository.connection() as connection:
        logged = TD.logged(connection, env.vault.config, at=later)
        found, record = PF.contrasts(connection, env.vault.config, logged, at=later)
    assert not {row.decision_id for row in logged} & picks
    assert not {row.decision_id for row in found} & picks
    # The overridden draw is in the cohort as what the mix drew, with its logged distribution (intention to treat).
    assert parent["id"] in {row.decision_id for row in found} and record["cohort"] >= 1


def test_w_itself_never_reads_a_preference_or_a_pick(tmp_path):
    """``w``'s scores come from the traces alone: preferences and override picks on record change no score and no ``w``."""

    env = _env(tmp_path)
    run(env)
    later = "2027-06-01T00:00:00Z"

    def weights() -> Any:
        with env.repository.connection() as connection:
            details = S.scores(connection, env.vault.config, at=later)
        w, record = OC.current_weight(env.repository, env.vault.config, at=later)
        return [(d.scored.decision_id, d.scored.value, d.scored.reason) for d in details], w, record["posterior"]

    before = weights()
    parent = rows(env)[-1]["id"]
    _insert(env, "p1", LA.NEW, decision=parent, note="something new")
    _insert(env, "p2", LA.STOP)
    with env.repository.atomic(), env.repository.connection() as connection:
        router_store.insert_router_decision(connection, {
            "id": "pick1", "receipt_key": f"{router_store.OVERRIDE_KEY_PREFIX}p1", "decision_kind": "learner_pick",
            "surface": "today", "mode": "daily_plan", "policy": "learner", "algorithm_version": TAG,
            "log_version": router_store.ROUTER_LOG_VERSION, "parent_decision_id": parent, "snapshot_hash": "x",
            "candidates_json": "[]",
            "exclusions_json": "{}", "candidate_count": 0, "chosen_ref": "x", "propensity": None, "propensity_kind": "none",
            "learner_pick": 1, "detail_json": "{}", "created_at": env.now_iso()})
    assert weights() == before
    root = pathlib.Path(S.__file__).parent
    for relative in ("scores.py", "weight.py", "mix.py", "value.py"):
        text = (root / relative).read_text()
        assert "learner_preference" not in text and "router_learner_preferences" not in text, relative


# -- staged reads nothing ------------------------------------------------------------------------------------------


def test_staged_reads_nothing(tmp_path, monkeypatch):
    """Static, and by every reader of the ledger failing the test if a staged path reaches it."""

    root = pathlib.Path(PF.__file__).resolve().parents[1]
    for relative in ("scheduling/staged_policy.py", "daily_plan/staged_frame.py"):
        text = (root / relative).read_text()
        for word in ("learner_preference", "preferences", "note_md", "w_pref"):
            assert word not in text, f"{relative} names {word}"

    def refused(*_args, **_kwargs):
        raise AssertionError("staged read the preference ledger")

    env = mixture_env(tmp_path, fake_runtime(), version=TAG, toml="[router_objective]\nenabled = false\n", session_id="s1")
    _insert(env, "p1", LA.LESSON, note="teach me")
    assert not preferences_inform_router_on(env.vault.config)
    for name in ("learner_preference_rows", "recent_learner_preferences"):
        monkeypatch.setattr(router_store, name, refused)
    run(env)
    assert rows(env)


def test_the_staged_pick_inside_the_objective_is_the_same_with_preferences_on_record(tmp_path, monkeypatch):
    seen: list[Any] = []
    real = StagedChooser.choose

    def spying(self, state, feasible):
        choice = real(self, state, feasible)
        seen.append(choice.candidate_id)
        return choice

    monkeypatch.setattr(StagedChooser, "choose", spying)
    pinned = _pin(monkeypatch)
    twin: dict[str, list[Any]] = {}
    for name in ("with", "without"):
        seen.clear()
        env = mixture_env(tmp_path / name, fake_runtime(seed=pinned), version=TAG, toml=QUIET, session_id="s1")
        if name == "with":
            for n in range(4):
                _insert(env, f"p{n}", LA.STOP)
        run(env)
        twin[name] = list(seen)
        assert all((trace["policies"]["staged"]["advice"]) for trace in _traces(env))
    assert twin["with"] == twin["without"] and twin["with"]


# -- the LLM's card --------------------------------------------------------------------------------------------------


def _card(env, budget: int = 48_000) -> dict[str, Any]:
    return OCARD.decision_card(env.vault, env.repository, [], served_at=env.now_iso(), goals={}, session={}, budget=budget)


def test_the_card_carries_the_learners_own_statements(tmp_path):
    env = _env(tmp_path)
    assert _card(env)["state"]["card"] == OCARD.CARD_VERSION and OCARD.STATEMENTS not in _card(env)["state"]["history"]
    _insert(env, "p1", LA.LESSON, note=EXTERIOR_NOTE, offered=_offered(*LA.KINDS, drawn=True, pick=LA.QUESTION))
    card = _card(env)
    state = card["state"]
    assert state["card"] == OCARD.CARD_VERSION_STATEMENTS and card["statements"] == 1
    assert "learner's own statement" in state["learner_statements_are"]
    entry = state["history"][OCARD.STATEMENTS][0]
    assert entry["source"] == "the learner's own statement" and entry["note"] == EXTERIOR_NOTE
    assert entry["said_would_help"] == "Learn this" and entry["plan_had_chosen"] == "Another question"
    assert entry["evidence_id"] == "preference:p1" and "preference:p1" in card["evidence_ids"]


def test_with_the_switch_off_or_none_on_record_the_card_is_the_predecessors_bytes(tmp_path):
    def dumped(env) -> str:
        return json.dumps(_card(env)["state"], sort_keys=True, ensure_ascii=False, default=str)

    fresh = _env(tmp_path / "fresh")
    off = _env(tmp_path / "off", toml=OFF)
    below = _env(tmp_path / "below", version=OLD)
    for env in (off, below):
        _insert(env, "p1", LA.LESSON, note=EXTERIOR_NOTE)
    assert OCARD.STATEMENTS not in dumped(fresh) and json.loads(dumped(fresh))["card"] == OCARD.CARD_VERSION
    assert dumped(fresh).replace(fresh.now_iso(), "t") == dumped(off).replace(off.now_iso(), "t")
    assert EXTERIOR_NOTE not in dumped(off) and EXTERIOR_NOTE not in dumped(below)
    assert json.loads(dumped(below))["card"] == OCARD.CARD_VERSION


def test_the_budget_holds_oldest_first_and_says_what_it_left_out(tmp_path):
    env = _env(tmp_path)
    for n in range(40):
        _insert(env, f"p{n:02d}", LA.QUESTION, at=f"2026-01-01T00:{n:02d}:00Z", note=f"note {n:02d} " + "x" * 400)
    whole = _card(env, budget=400_000)
    assert whole["statements"] == 40 and whole["left_out"] == {}
    trimmed = _card(env, budget=6_000)
    assert trimmed["bytes"] <= 6_000
    entries = trimmed["state"]["history"].get(OCARD.STATEMENTS) or []
    assert 0 < len(entries) < 40
    assert trimmed["left_out"][OCARD.STATEMENTS]["entries"] == 40 - len(entries)
    assert entries[-1]["evidence_id"] == "preference:p39" and entries[0]["evidence_id"] != "preference:p00"


def test_the_read_is_bounded_by_the_card_questions_limit_and_says_so(tmp_path):
    from learnloop.adaptive_difficulty.history_card import ROW_LIMITS

    env = _env(tmp_path)
    limit = ROW_LIMITS["questions"]
    for n in range(limit + 2):
        _insert(env, f"p{n:04d}", LA.STOP, at=f"2026-01-{1 + n // 60:02d}T{n % 24:02d}:00:00Z")
    card = _card(env, budget=400_000)
    assert card["statements"] == limit and OCARD.STATEMENTS in card["state"]["row_limits_reached"]


def test_a_note_on_a_protected_attempt_shows_nothing_and_says_why(tmp_path):
    env = _env(tmp_path)
    item = next(iter(env.vault.practice_items.values()))
    open_attempt = record_attempt(env.repository, item.id, item.learning_object_id, env.clock.now())
    env.clock.advance(1)
    exam = record_attempt(env.repository, item.id, item.learning_object_id, env.clock.now())
    with env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET attempt_type = 'exam_attempt' WHERE id = ?", (exam,))
        connection.commit()
    _insert(env, "shown", LA.QUESTION, attempt=open_attempt, note="about an open answer")
    _insert(env, "hidden", LA.QUESTION, attempt=exam, note="question three of the exam said")
    _insert(env, "gone", LA.QUESTION, attempt="no_such_attempt", note="about something unknown")
    _insert(env, "plain", LA.QUESTION, note="no attempt behind this")
    card = _card(env)
    by_id = {entry["evidence_id"]: entry for entry in card["state"]["history"][OCARD.STATEMENTS]}
    assert by_id["preference:shown"]["note"] == "about an open answer"
    assert by_id["preference:plain"]["note"] == "no attempt behind this"
    assert "note" not in by_id["preference:hidden"] and by_id["preference:hidden"]["note_withheld"]
    assert "note" not in by_id["preference:gone"] and by_id["preference:gone"]["note_withheld"]
    text = json.dumps(card["state"])
    assert "question three of the exam" not in text and "about something unknown" not in text
    # The chosen kind stays: what they said would help is no text of the exam.
    assert by_id["preference:hidden"]["said_would_help"] == "Another question"


def test_protection_unreadable_hides_every_note(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP

    env = _env(tmp_path)
    _insert(env, "plain", LA.QUESTION, note="no attempt behind this")
    monkeypatch.setattr(LP, "withheld_items", lambda _vault, _repository: LP.Withheld(available=False, unknowns=()))
    with env.repository.connection() as connection:
        entries, _limited = OCARD.learner_statements(env.vault, env.repository, connection, served_at=env.now_iso())
    assert "note" not in entries[0] and entries[0]["note_withheld"] == LP.WITHHELD_UNREADABLE


def test_the_mid_block_request_carries_them_for_the_llm_alone(tmp_path):
    env = _env(tmp_path)
    assert OCARD.statement_lines(env.vault, env.repository, served_at=env.now_iso(), budget=48_000) == []
    _insert(env, "p1", LA.LESSON, note=EXTERIOR_NOTE)
    text = OCARD.statement_lines(env.vault, env.repository, served_at=env.now_iso(), budget=48_000)
    assert text[0] == "# The learner's own statements" and EXTERIOR_NOTE in "\n".join(text)
    assert OCARD.statement_lines(env.vault, env.repository, served_at=env.now_iso(), budget=10) == []
    gate = OC.ObjectiveRestraintGate(env.vault, env.repository, fake_runtime(), frame=None, card_builder=None,
                                     session_id="s1", clock=env.clock, may_defer=False)
    card = SimpleNamespace(text="the card", json={})
    options = [SimpleNamespace(ref="a", description="option a")]
    shared = "the shared state"
    assert EXTERIOR_NOTE in gate._policy_state(card, options, ["a fact"], shared)
    off = _env(tmp_path / "off", toml=OFF)
    _insert(off, "p1", LA.LESSON, note=EXTERIOR_NOTE)
    gate = OC.ObjectiveRestraintGate(off.vault, off.repository, fake_runtime(), frame=None, card_builder=None,
                                     session_id="s1", clock=off.clock, may_defer=False)
    assert gate._policy_state(card, options, ["a fact"], shared) is shared


def test_the_llm_reads_the_card_and_the_trace_names_it(tmp_path):
    prompts: list[str] = []

    def answer(request):
        prompts.append(str(getattr(request, "state", "") or request))
        return policy_answer(request)

    env = _env(tmp_path, runtime=fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=answer)))
    _insert(env, "p1", LA.REVIEW, note=EXTERIOR_NOTE)
    env.clock.advance(1)
    run(env)
    trace = _traces(env)[-1]
    assert trace["learner_statements"]["card"] == OCARD.CARD_VERSION_STATEMENTS and trace["learner_statements"]["entries"] == 1
    assert any(EXTERIOR_NOTE in prompt for prompt in prompts)


# -- the prefetch key --------------------------------------------------------------------------------------------------


def _world_insert(world, pid: str, kind: str = LA.QUESTION, *, at: str, note: str | None = None) -> None:
    row = {"id": pid, "decision_id": None, "attempt_id": None, "session_id": world.session, "surface": "phone_today",
           "offered_json": _offered(*LA.KINDS), "chosen_kind": kind, "chosen_ref": f"ref:{kind}", "note_md": note,
           "served_decision_id": None, "algorithm_version": TAG, "created_at": at}
    with world.repository.atomic(), world.repository.connection() as connection:
        assert router_store.insert_learner_preference(connection, row)


def test_the_start_only_prefetch_and_its_serve_compute_one_key_with_preferences_on_record(make_world, spy):
    world = make_world()
    _world_insert(world, "p1", at="2026-01-01T00:00:00Z", note=EXTERIOR_NOTE)
    reply = world.to_boundary()
    assert reply["started"] is True and reply["reason"] == "started"
    at_prefetch = [found for found in spy.identities if found["kind"] == "objective_block"][-1]
    assert at_prefetch["preferences"] == {"n": 1, "latest": "2026-01-01T00:00:00Z p1"}
    key, seed = OC._hash(at_prefetch), OC.numeric_seed(at_prefetch)
    world.wait_for_job()
    runs, jobs, known = len(spy.runs), list(world.runtime._entries), len(spy.identities)
    assert world.next()["step"] is not None
    at_serve = [found for found in spy.identities[known:] if found["kind"] == "objective_block"]
    assert at_serve and OC._hash(at_serve[0]) == key and OC.numeric_seed(at_serve[0]) == seed
    assert list(world.runtime._entries) == jobs and len(spy.runs) == runs
    trace = world.last_trace()
    assert trace["preference"]["choice"]["updates"] == 1
    assert trace["learner_statements"]["entries"] == 1


def test_a_new_preference_starts_a_new_job_and_moves_no_seed(make_world, spy):
    world = make_world()
    reply = world.to_boundary()
    assert reply["started"] is True
    world.wait_for_job()
    before = [found for found in spy.identities if found["kind"] == "objective_block"][-1]
    assert "preferences" not in before
    jobs = list(world.runtime._entries)
    _world_insert(world, "p1", at="2026-01-01T00:00:00Z")
    known = len(spy.identities)
    reply = world.prefetch()
    assert reply["started"] is True and reply["reason"] == "started"
    after = [found for found in spy.identities[known:] if found["kind"] == "objective_block"][-1]
    assert after["preferences"]["n"] == 1
    assert OC._hash(after) != OC._hash(before) and OC.numeric_seed(after) == OC.numeric_seed(before)
    assert len(world.runtime._entries) == len(jobs) + 1


# -- a read IH7 left outside the availability predicate ------------------------------------------------------------------


def test_the_miss_a_lesson_reads_is_what_was_known_at_the_decision(tmp_path):
    """IH7's ``_miss`` (``test_ro1_availability_reads``): an answer imported after the decision, dated before it, isn't it."""

    from learnloop.teacher.diagnosed_sources import _miss

    env = _env(tmp_path)
    item = next(iter(env.vault.practice_items.values()))
    lo = item.learning_object_id
    known = record_attempt(env.repository, item.id, lo, env.clock.now())
    env.clock.advance(5)
    backdated = record_attempt(env.repository, item.id, lo, env.clock.now())
    env.clock.advance(5)
    decided = env.now_iso()
    env.clock.advance(60)
    with env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET received_at = ? WHERE id = ?", (env.now_iso(), backdated))
        connection.commit()
        assert _miss(connection, env.vault.config, [lo], decided)["attempt_id"] == known


# -- the report --------------------------------------------------------------------------------------------------------


def _report(env) -> dict[str, Any]:
    with env.repository.connection() as connection:
        return build_report(connection, env.vault, env.repository, as_of=env.now_iso(), success_correctness=0.8)


@pytest.mark.usefixtures("offerable")
def test_the_report_section_says_each_thing_and_labels_it_self_selected(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    live = LA.options(env)
    lesson = next(option for option in live.options if option.kind == LA.LESSON)
    LA.choose(env, kind=LA.LESSON, ref=lesson.ref, surface="today", attempt_id=None, note_md=None, preference_id="agreed")
    pick = next(option for option in LA.options(env).options if option.kind not in (LA.LESSON, LA.STOP) and option.candidate)
    served = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="today", attempt_id=None, note_md="I want this",
                       preference_id="over")
    assert served.outcome == "served" and served.step["kind"] == "item"
    env.clock.advance(2)
    record_attempt(env.repository, served.step["practice_item_id"], served.step["learning_object_id"], env.clock.now(),
                   session_id=env.session_id)
    with env.repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET correctness = 1.0 WHERE id = (SELECT id FROM practice_attempts "
                           "ORDER BY created_at DESC, id DESC LIMIT 1)")
        connection.commit()
    report = _report(env)["learner_preferences"]
    assert report["available"] and report["version"] == PR.VERSION and report["preferences"] == 2
    assert "self-selected" in report["label"]
    for section in ("agreement_by_kind", "override_rate", "follow_through", "later_cold_results"):
        assert "self-selected" in report[section]["label"], section
    assert "never counted as agreeing" in report["agreement_by_kind"]["label"]
    assert "never counted as agreeing" in report["override_rate"]["label"]
    assert report["agreement_by_kind"]["agreed"] == 1
    assert report["agreement_by_kind"]["router_drew_learner_chose"][LA.LESSON] == {LA.LESSON: 1, pick.kind: 1}
    rate = report["override_rate"]
    assert rate["overrides"] == 1 and rate["of_preferences_with_a_draw"] == 0.5
    assert rate["plan_decisions_since_the_first"] == 0 or rate["of_plan_decisions_since_the_first"] is not None
    assert report["follow_through"]["by_kind"][pick.kind] == {"followed": 1}
    assert report["follow_through"]["by_kind"][LA.LESSON]["not_followed"] == 1
    cold = report["later_cold_results"]["by_kind"][pick.kind]
    assert cold["override"]["n"] == 1 and cold["override"]["mean"] == 1.0 and "router_draw" in cold
    assert "self-selected" in report["later_cold_results"]["label"] and "neither column" in report["later_cold_results"]["label"]
    assert report["w_pref"]["w_pref"] == 0.0 and "never on a pick" in report["w_pref"]["what_moves_it"]
    text = "\n".join(lines(_report(env)))
    for needle in ("Learner preferences (", "router drew / learner chose (self-selected)", "override rate (self-selected)",
                   "follow-through (self-selected)", "later cold results (self-selected)", "w_pref 0.0"):
        assert needle in text


def test_the_report_with_nothing_on_record_and_with_the_switch_off(tmp_path):
    report = _report(_env(tmp_path / "on"))["learner_preferences"]
    assert report["preferences"] == 0 and report["override_rate"]["of_preferences_with_a_draw"] is None
    off = _report(_env(tmp_path / "off", toml=OFF))
    below = _report(_env(tmp_path / "below", version=OLD))
    assert "learner_preferences" not in off and "learner_preferences" not in below
    assert "Learner preferences" not in "\n".join(lines(off))


def test_a_preference_with_no_draw_is_counted_apart(tmp_path):
    env = _env(tmp_path)
    _insert(env, "p1", LA.REVIEW, offered=json.dumps({**json.loads(_offered(*LA.KINDS)), "no_draw": "mid_block"}))
    report = _report(env)["learner_preferences"]
    assert report["no_draw"] == 1 and report["with_a_draw"] == 0 and report["no_draw_reasons"] == {"mid_block": 1}
    assert report["agreement_by_kind"]["router_drew_learner_chose"] == {}
    assert report["agreement_by_kind"]["by_learner_kind"][LA.REVIEW]["no_draw"] == 1


# -- what the override leaves on record, end to end -------------------------------------------------------------------


@pytest.mark.usefixtures("offerable")
def test_a_real_choice_freezes_its_inputs_and_the_next_decision_reads_it(tmp_path, draw):
    env = _env(tmp_path)
    _open_offer(env, draw)
    live = LA.options(env)
    assert live.frozen[PF.FEATURES_KEY]["minutes_left"] is not None
    pick = next(option for option in live.options if option.kind not in (LA.LESSON, LA.STOP) and option.candidate)
    served = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="today", attempt_id=None, note_md=EXTERIOR_NOTE,
                       preference_id="over")
    row = _preferences(env)[0]
    offered = json.loads(row["offered_json"])
    assert offered[PF.FEATURES_KEY] == live.frozen[PF.FEATURES_KEY]
    state, counts = PF.replay([row])
    assert state.updates == 1 and counts["read"] == 1
    step = served.step
    draw.prefer = ()
    known = len(_traces(env))
    for _ in range(8):
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        _record, step = advance(env, serve=True)
        if len(_traces(env)) > known or step is None or step["kind"] != "item":
            break
    fresh = _traces(env)[known:]
    assert fresh and fresh[0]["preference"]["choice"]["updates"] == 1
    assert fresh[0]["preference"]["choice"]["rows"]["read"] == 1
