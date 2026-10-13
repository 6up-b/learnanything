"""mvp-0.17: four count caps lifted onto value of information, and the probe
hypothesis lane reading the diagnoser's verdict under split grading.

Part 1 (``voi_stopping.enabled``, a sub-switch per site): a probe episode keeps
asking, a further follow-up is queued, a further teach-back is kept and a due
project probe enters the plan while the next observation's value pays for its
minutes. Part 2 (``diagnosis.probe_lane_reads_diagnosis``): the follow-up
misconception gate's hypothesis set reads the diagnosis overlay and holds out
an event whose diagnosis is pending. Below mvp-0.17, or with a switch off,
serving is mvp-0.16's exactly.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.config.schema import LearnLoopConfig
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.daily_plan.lanes import (
    ScheduledCheck,
    classify_pool,
    register_scheduled_check_provider,
    unregister_scheduled_check_provider,
)
from learnloop.diagnosis.followups import evaluate_intervention_followup
from learnloop.diagnosis.probe_episodes import (
    enter_episode,
    probe_serving_block_reason,
    probe_value_block_reason,
)
from learnloop.diagnosis.probes import build_hypothesis_set
from learnloop.diagnosis import voi_stopping as voi
from learnloop.scheduling.scheduler import OfferTrace, SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import write_yaml

from tests.daily_plan_fakes import make_env, scheduled
from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    admit_probe_instrument_card,
    append_config_toml,
    create_basic_vault,
    create_daily_plan_vault,
    set_algorithm_version,
)
from tests.split_live_helpers import drain_jobs, split_vault, submit
from tests.test_active_errors_overlay import _StatementFake

CLOCK = FrozenClock(NOW)
LO = "lo_svd_definition"


def _config(version: str, **switches) -> LearnLoopConfig:
    config = LearnLoopConfig()
    config.algorithms.algorithm_version = version
    for name, value in switches.items():
        setattr(config.voi_stopping, name, value)
    return config


def _minutes(monkeypatch, minutes: float) -> None:
    """Pin every candidate's expected minutes (the value must pay for them)."""

    monkeypatch.setattr(
        voi.VoiContext,
        "item_minutes",
        lambda self, item, authored_minutes=None: voi.MinutesEstimate(float(minutes), "authored_prior"),
    )


# ── the gates ─────────────────────────────────────────────────────────────────


def test_the_value_gate_needs_the_successor_the_switch_and_the_site():
    for site in voi.SITES:
        assert voi.voi_stopping_active(_config("mvp-0.17"), site)
        assert not voi.voi_stopping_active(_config("mvp-0.17", enabled=False), site)
        assert not voi.voi_stopping_active(_config("mvp-0.17", **{voi.SITE_SWITCH[site]: False}), site)
        for version in ("mvp-0.6", "mvp-0.9", "mvp-0.10", "mvp-0.14", "mvp-0.15", "mvp-0.16"):
            assert not voi.voi_stopping_active(_config(version), site)
    # A sub-switch turns off its own site only.
    config = _config("mvp-0.17", teach_back=False)
    assert voi.voi_stopping_active(config, voi.SITE_PROBE_EPISODE)
    assert not voi.voi_stopping_active(config, voi.SITE_TEACH_BACK)


def test_the_probe_lane_gate_needs_the_successor_and_its_switch():
    assert voi.probe_lane_reads_diagnosis(_config("mvp-0.17"))
    off = _config("mvp-0.17")
    off.diagnosis.probe_lane_reads_diagnosis = False
    assert not voi.probe_lane_reads_diagnosis(off)
    for version in ("mvp-0.10", "mvp-0.15", "mvp-0.16"):
        assert not voi.probe_lane_reads_diagnosis(_config(version))
    # Part 2 does not depend on Part 1's switch.
    assert voi.probe_lane_reads_diagnosis(_config("mvp-0.17", enabled=False))


# ── the value rule ────────────────────────────────────────────────────────────


class _Repo:
    """Just enough repository for a VoiContext: no latencies, seeded routes."""

    def __init__(self, routes):
        self._routes = routes

    def failure_triage_routes(self):
        return list(self._routes)

    def connection(self):
        import sqlite3

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute(
            "CREATE TABLE practice_attempts (practice_item_id TEXT, practice_mode TEXT, latency_seconds REAL)"
        )
        connection.execute(
            "CREATE TABLE interaction_events (kind TEXT, attempt_duration_ms INTEGER)"
        )
        return closing(connection)


def _ctx(routes=()):
    from types import SimpleNamespace

    return voi.VoiContext(SimpleNamespace(config=LearnLoopConfig()), _Repo(routes))


ROUTES = [
    {"reason": "unfamiliar_or_missing_knowledge", "first_intervention": "study", "active": 1},
    {"reason": "memory_lapse", "first_intervention": "review", "active": 1},
    {"reason": "false_belief_or_confusion", "first_intervention": "contrast", "active": 1},
]
INFORMATIVE = {"unfamiliar": {"wrong": 0.9, "right": 0.1}, "robust_initial_grasp": {"wrong": 0.1, "right": 0.9}}
FLAT = {"unfamiliar": {"wrong": 0.5, "right": 0.5}, "robust_initial_grasp": {"wrong": 0.5, "right": 0.5}}


def _candidate(ref, members, minutes):
    return voi.Candidate(ref=ref, minutes=voi.MinutesEstimate(minutes, "authored_prior"), members=(members,))


def _cap():
    return voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=0)


def test_with_no_routes_the_robust_eig_in_minutes_must_pay_for_the_minutes():
    ctx = _ctx()
    prior = {"unfamiliar": 0.5, "robust_initial_grasp": 0.5}
    decision = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE,
        [_candidate("informative", INFORMATIVE, 2.0), _candidate("flat", FLAT, 0.5)],
        prior=prior, learning_object_id="lo", former_cap=_cap(),
    )
    informative, flat = decision.value_for("informative"), decision.value_for("flat")
    assert informative.method == flat.method == voi.METHOD_EIG_VALUE
    assert informative.continues and not flat.continues
    assert flat.eig_nats == pytest.approx(0.0) and flat.reason == voi.REASON_EIG_BELOW
    # 60 minutes a nat (robust_composition's heuristic scale) against 2 minutes.
    assert informative.value_robust_minutes == pytest.approx(60.0 * informative.eig_robust_nats)
    assert informative.cost_minutes == pytest.approx(2.0)
    assert decision.decision == voi.CONTINUE and decision.best.ref == "informative"


def test_where_routes_differ_robust_evsi_and_rank_feasibles_stop_rule_decide():
    ctx = _ctx(ROUTES)
    spread = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior={"unfamiliar": 0.5, "robust_initial_grasp": 0.5}, learning_object_id="lo", former_cap=_cap(),
    )
    assert spread.context["decision_at_stake"] is True
    assert spread.context["label_actions"] == {"robust_initial_grasp": "review", "unfamiliar": "study"}
    value = spread.best
    assert value.method == voi.METHOD_ROBUST_EVSI and value.continues
    assert value.reason == voi.REASON_EVSI_CLEARS and spread.rank["verdict"] == "measure"
    # A perfectly sure belief: the observation cannot change the repair.
    sure = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior={"unfamiliar": 0.97, "robust_initial_grasp": 0.03}, learning_object_id="lo", former_cap=_cap(),
    )
    assert sure.context["decision_at_stake"] is False  # one plausible hypothesis
    costly = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 30.0)],
        prior={"unfamiliar": 0.5, "robust_initial_grasp": 0.5}, learning_object_id="lo", former_cap=_cap(),
    )
    assert costly.decision == voi.STOP and costly.best.reason == "lcb_evsi_below_minutes_cost"


def test_rival_misconceptions_are_rival_repairs():
    ctx = _ctx(ROUTES)
    actions = ctx.label_actions(["misconception:a", "misconception:b"])
    assert actions == {"misconception:a": "contrast@misconception:a", "misconception:b": "contrast@misconception:b"}
    # A label whose triage reason has no route: no loss table, no EVSI.
    assert _ctx(ROUTES[:1]).label_actions(["misconception:a"]) is None


def test_every_decision_is_a_logged_forecast_with_heuristic_parameters():
    ctx = _ctx(ROUTES)
    decision = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior={"unfamiliar": 0.5, "robust_initial_grasp": 0.5}, learning_object_id="lo",
        former_cap=voi.former_cap(voi.SITE_PROBE_EPISODE, value=4, count=4),
    )
    body = decision.as_dict()
    json.dumps(body)  # serializable as logged
    assert body["forecast_version"] == voi.FORECAST_VERSION and body["calibration_label"] == "heuristic"
    forecast = body["best"]["forecast"]
    assert sum(forecast["predicted_outcomes"].values()) == pytest.approx(1.0)
    assert set(forecast["action_by_emission"]) == {"right", "wrong"}
    assert forecast["action_proxy"] == "triage_route_repair"
    assert 0.0 <= forecast["p_action_change"] <= 1.0 and forecast["eig_nats"] > 0
    for key in ("evsi_point_minutes", "evsi_robust_minutes", "eig_nats", "cost_minutes"):
        assert key in body["best"]
    names = {p["name"]: p for p in body["parameters"]}
    for name in ("lambda_time", "burden_cost_minutes", "value_per_nat_minutes", "robust_quantile",
                 "perturbation_delta", "loss_model"):
        assert names[name]["provenance"] == "heuristic"
    assert body["former_cap"] == {
        "name": "probe.episode.session_qualifying_observation_cap", "value": 4, "count": 4, "would_bind": True,
    }
    assert body["cap_comparison"] == "later"


def test_former_cap_counterfactuals():
    assert voi.former_cap(voi.SITE_PROBE_EPISODE, value=0, count=9)["would_bind"] is False
    assert voi.former_cap(voi.SITE_TEACH_BACK, value=1, count=1)["would_bind"] is True
    assert voi.former_cap(voi.SITE_PROJECT_PROBE, value=4, count=3)["would_bind"] is False


# ── (a) probe episodes: every next observation pays for its minutes ──────────


def _probe_vault(tmp_path, version: str, *, toml: str = ""):
    """Two never-seen items bound to an in-progress re-probe episode (router
    R1's fixture): the queue's only candidates are the two probes."""

    paths = create_basic_vault(tmp_path / version.replace(".", "_"))
    write_yaml(paths.goals_path, {"schema_version": 1, "goals": []})
    add_followup_item(paths.root, "pi_svd_define_002")
    set_algorithm_version(paths, version)
    append_config_toml(paths.root, "[plan]\nenabled = false\n" + toml)
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "err_conceptual_slip", "learning_object_id": LO,
            "error_type": "conceptual_slip", "severity": 0.7, "is_misconception": True,
            "status": "active", "created_at": NOW_ISO, "updated_at": NOW_ISO,
        }
    )
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    admit_probe_instrument_card(repository, items=("pi_svd_define_001", "pi_svd_define_002"))
    enter_episode(vault, repository, LO, trigger="misconception", clock=CLOCK)
    return paths, load_vault(paths.root), repository


def _session_spent(monkeypatch, repository, count=4):
    """The session already holds ``count`` qualifying observations."""

    monkeypatch.setattr(repository, "qualifying_probe_observation_count_for_session", lambda _sid: count)


def _fingerprint(queue):
    return [
        (s.practice_item_id, round(s.priority, 12), sorted((k, round(v, 12)) for k, v in s.components.items()))
        for s in queue
    ]


def _build(vault, repository, *, session_id="sess", trace=None):
    return build_due_queue(
        vault, repository, clock=CLOCK, session=SchedulerSession(session_id=session_id),
        persist_explanations=False, offer_trace=trace,
    )


def test_below_the_successor_the_spent_session_cap_blocks_probes(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.16")
    _session_spent(monkeypatch, repository)
    assert probe_serving_block_reason(vault, repository, session_id="sess") == "session_cap_reached"
    queue = _build(vault, repository)
    assert all(item.components.get("probe_eig", 0.0) == 0.0 for item in queue)


def test_at_the_successor_value_keeps_asking_past_the_former_cap(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.17")
    _session_spent(monkeypatch, repository)
    assert probe_serving_block_reason(vault, repository, session_id="sess") is None
    trace = OfferTrace()
    queue = _build(vault, repository, trace=trace)
    probes = [item for item in queue if item.components.get("probe_eig", 0.0) > 0.0]
    assert probes, "the observation's value pays for its minutes"
    assert all(item.components["voi_value_minutes"] > item.components["voi_cost_minutes"] for item in probes)
    (decision,) = [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    assert decision["decision"] == voi.CONTINUE
    assert decision["former_cap"]["would_bind"] is True and decision["cap_comparison"] == "later"


def test_at_the_successor_value_stops_an_episode_whose_next_observation_does_not_pay(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.17")
    _minutes(monkeypatch, 10_000.0)
    trace = OfferTrace()
    queue = _build(vault, repository, trace=trace)
    assert all(item.components.get("probe_eig", 0.0) == 0.0 for item in queue)
    assert all(item.components.get("voi_stop") == 1.0 for item in queue)
    (decision,) = [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    assert decision["decision"] == voi.STOP
    # The session had spent nothing: the cap would not have bound.
    assert decision["former_cap"]["would_bind"] is False and decision["cap_comparison"] == "earlier"
    # The sidecar and TUI door applies the same rule to a new commit.
    episode = repository.open_probe_episode(LO)
    reason, body = probe_value_block_reason(vault, repository, episode, "pi_svd_define_001", session_id="sess")
    assert reason == "value_below_minutes_cost" and body["decision"] == voi.STOP
    # A calibration session (the learner's explicit opt-in) lifts the gate.
    assert probe_value_block_reason(
        vault, repository, episode, "pi_svd_define_001", session_id="sess", cap_lifted=True
    ) == (None, None)


@pytest.mark.parametrize("toml", ["[voi_stopping]\nenabled = false\n", "[voi_stopping]\nprobe_episodes = false\n"])
def test_the_kill_switch_serves_mvp016s_probe_queue_exactly(tmp_path, monkeypatch, toml):
    _bp, base_vault, base_repo = _probe_vault(tmp_path / "base", "mvp-0.16")
    _op, off_vault, off_repo = _probe_vault(tmp_path / "off", "mvp-0.17", toml=toml)
    for spent in (0, 4):
        _session_spent(monkeypatch, base_repo, spent)
        _session_spent(monkeypatch, off_repo, spent)
        base_trace, off_trace = OfferTrace(), OfferTrace()
        assert _fingerprint(_build(off_vault, off_repo, trace=off_trace)) == _fingerprint(
            _build(base_vault, base_repo, trace=base_trace)
        )
        assert off_trace.voi_decisions == base_trace.voi_decisions == ()
        # The teach-back site keeps its own sub-switch.
        assert off_trace.teach_back_exclusion_reason == (
            "teach_back_session_cap" if "enabled" in toml else "teach_back_value_below_minutes_cost"
        )


def test_the_continue_decision_rides_on_the_committed_presentation_and_the_offer(tmp_path):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.17")
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session_id}))
    with repository.connection() as connection:
        row = dict(connection.execute("SELECT * FROM router_decisions").fetchone())
    detail = json.loads(row["detail_json"])
    (decision,) = detail["voi_decisions"]
    assert decision["site"] == voi.SITE_PROBE_EPISODE and decision["decision"] == voi.CONTINUE
    assert decision["best"]["forecast"]["predicted_outcomes"]
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None
    assert presentation.selection_components["voi_stopping"]["decision"] == voi.CONTINUE


def test_below_the_successor_the_offer_logs_no_value_decisions(tmp_path):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.16")
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session_id}))
    with repository.connection() as connection:
        row = dict(connection.execute("SELECT * FROM router_decisions").fetchone())
    assert "voi_decisions" not in json.loads(row["detail_json"])
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None and "voi_stopping" not in presentation.selection_components


# ── (b) further follow-ups on an LO in a session ─────────────────────────────


def _followup_setup(tmp_path, version):
    from tests.test_followups import _surprising_attempt

    vault_root = tmp_path / version.replace(".", "_")
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(vault_root, repository)
    loaded.config.algorithms.algorithm_version = version
    return loaded, repository, result


def _further(loaded, repository, result, **kwargs):
    return evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
        available_minutes=30,
        session_id="sess",
        session_interventions_for_lo=1,
        **kwargs,
    )


def test_below_the_successor_a_further_follow_up_is_suppressed_by_count(tmp_path):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.16")
    decision = _further(loaded, repository, result)
    assert decision.triggered is False
    assert decision.reason == f"intervention_followup:session_cap_reached:{LO}"
    assert "voi_stopping" not in (decision.gate_diagnostics or {})


def test_at_the_successor_a_further_follow_up_is_queued_while_its_value_pays(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.17")
    _minutes(monkeypatch, 0.01)
    decision = _further(loaded, repository, result)
    assert decision.triggered is True and decision.practice_item_id == "pi_svd_define_002"
    body = decision.gate_diagnostics["voi_stopping"]
    assert body["site"] == voi.SITE_FOLLOWUP and body["decision"] == voi.CONTINUE
    assert body["former_cap"]["would_bind"] is True and body["cap_comparison"] == "later"
    assert body["best"]["forecast"]["predicted_outcomes"]
    stored = repository.latest_attempt_surprise(result.attempt_id)
    assert stored["gate_diagnostics"]["voi_stopping"]["decision"] == voi.CONTINUE


def test_at_the_successor_a_further_follow_up_whose_value_does_not_pay_is_suppressed(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.17")
    _minutes(monkeypatch, 10_000.0)
    decision = _further(loaded, repository, result)
    assert decision.triggered is False
    assert decision.reason == f"intervention_followup:voi_value_below_minutes_cost:{LO}"
    assert decision.gate_diagnostics["voi_stopping"]["decision"] == voi.STOP
    # The learner's own request still wins (the manual override), and the log
    # says what value would have done.
    forced = _further(loaded, repository, result, manual_override=True)
    assert forced.triggered is True
    assert "voi_value_below_minutes_cost" in forced.gate_diagnostics["would_suppress"]


def test_the_first_follow_up_in_a_session_is_not_valued(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.17")
    _minutes(monkeypatch, 10_000.0)
    first = evaluate_intervention_followup(
        loaded, repository, attempt_id=result.attempt_id, learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id, surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise, grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids), available_minutes=30, session_id="sess",
        session_interventions_for_lo=0,
    )
    assert first.triggered is True and "voi_stopping" not in first.gate_diagnostics


@pytest.mark.parametrize("switch", ["enabled", "followups"])
def test_the_kill_switch_restores_the_follow_up_count_cap(tmp_path, switch):
    base, base_repo, base_result = _followup_setup(tmp_path / "base", "mvp-0.16")
    off, off_repo, off_result = _followup_setup(tmp_path / "off", "mvp-0.17")
    setattr(off.config.voi_stopping, switch, False)
    expected = _further(base, base_repo, base_result)
    actual = _further(off, off_repo, off_result)
    assert (actual.triggered, actual.reason, actual.suppressed_actions) == (
        expected.triggered, expected.reason, expected.suppressed_actions,
    )
    assert actual.gate_diagnostics == expected.gate_diagnostics


# ── (c) further teach-backs ──────────────────────────────────────────────────


def _teach_back_vault(tmp_path, version):
    from tests.test_teach_back import _seed_lo_evidence, _setup, _teach_item_payload

    _root, vault, repository = _setup(tmp_path / version.replace(".", "_"),
                                      extra_items=[_teach_item_payload("pi_svd_teach_002")])
    _seed_lo_evidence(repository)
    vault.config.algorithms.algorithm_version = version
    return vault, repository


def _teach_backs(queue):
    return [entry.practice_item_id for entry in queue if entry.selected_mode == "teach_back"]


def test_further_teach_backs_stay_while_their_value_pays(tmp_path, monkeypatch):
    base_vault, base_repo = _teach_back_vault(tmp_path, "mvp-0.16")
    vault, repository = _teach_back_vault(tmp_path, "mvp-0.17")
    assert len(_teach_backs(_build(base_vault, base_repo, session_id="sess_1"))) == 1
    _minutes(monkeypatch, 0.01)
    trace = OfferTrace()
    queue = _build(vault, repository, session_id="sess_1", trace=trace)
    assert len(_teach_backs(queue)) == 2
    decisions = [d for d in trace.voi_decisions if d["site"] == voi.SITE_TEACH_BACK]
    assert len(decisions) == 2 and all(d["decision"] == voi.CONTINUE for d in decisions)
    assert [d["former_cap"]["would_bind"] for d in decisions] == [False, True]
    assert trace.teach_back_exclusion_reason == "teach_back_value_below_minutes_cost"


def test_a_further_teach_back_whose_value_does_not_pay_is_dropped_and_the_first_kept(tmp_path, monkeypatch):
    vault, repository = _teach_back_vault(tmp_path, "mvp-0.17")
    _minutes(monkeypatch, 10_000.0)
    trace = OfferTrace()
    queue = _build(vault, repository, session_id="sess_1", trace=trace)
    assert len(_teach_backs(queue)) == 1  # the former cap's allowance stays
    decisions = [d for d in trace.voi_decisions if d["site"] == voi.SITE_TEACH_BACK]
    assert all(d["decision"] == voi.STOP for d in decisions)


@pytest.mark.parametrize("switch", ["enabled", "teach_back"])
def test_the_kill_switch_serves_mvp016s_teach_back_queue_exactly(tmp_path, monkeypatch, switch):
    base_vault, base_repo = _teach_back_vault(tmp_path / "base", "mvp-0.16")
    vault, repository = _teach_back_vault(tmp_path / "off", "mvp-0.17")
    setattr(vault.config.voi_stopping, switch, False)
    _minutes(monkeypatch, 0.01)
    assert _fingerprint(_build(vault, repository, session_id="sess_1")) == _fingerprint(
        _build(base_vault, base_repo, session_id="sess_1")
    )


# ── (d) project probes in the daily plan ─────────────────────────────────────


def _probe_items(eig=0.2):
    return [scheduled(f"pi_probe_{i}", "lo_repo", probe_eig_total=eig) for i in range(5)]


def _checks():
    return {f"pi_probe_{i}": ScheduledCheck("project_probe", priority=1 if i == 4 else 0) for i in range(5)}


def _lanes(pool):
    return {item.practice_item_id: item.lane for item in pool}


def _valuer(minutes_cost_scale=1.0):
    ctx = voi.VoiContext(type("V", (), {"config": LearnLoopConfig()})(), None)

    def value(item, est_minutes, order):
        return voi.adapter_information_decision(
            ctx, voi.SITE_PROJECT_PROBE, ref=item.practice_item_id, learning_object_id=item.learning_object_id,
            eig_nats=float(item.components.get("probe_eig_total", 0.0)),
            minutes=voi.MinutesEstimate(est_minutes * minutes_cost_scale, "plan_estimate"),
            predicted_correct=None, cap_value=4, cap_count=order,
        ).as_dict()

    return value


def test_valued_project_probes_have_no_count_cap_and_order_by_value_per_minute():
    items = _probe_items()
    items[2] = scheduled("pi_probe_2", "lo_repo", probe_eig_total=0.9)
    pool = classify_pool(
        items, item_states={}, requested_ids=[], now=NOW, estimate=lambda _id: 3.0, checks=_checks(),
        probe_cap_left=4, project_probe_value=_valuer(),
    )
    assert list(_lanes(pool).values()).count("maintain") == 5  # the fifth is no longer "later"
    probes = [item.practice_item_id for item in pool if item.check_kind == "project_probe"]
    assert probes[0] == "pi_probe_2"  # the most information per minute first
    assert [item.voi["former_cap"]["would_bind"] for item in pool].count(True) == 1


def test_a_project_probe_whose_value_does_not_pay_stays_later():
    pool = classify_pool(
        _probe_items(eig=0.001), item_states={}, requested_ids=[], now=NOW, estimate=lambda _id: 3.0,
        checks=_checks(), probe_cap_left=4, project_probe_value=_valuer(),
    )
    assert set(_lanes(pool).values()) == {None}
    assert {item.reason for item in pool} == {"a due project probe whose value does not pay for its minutes today"}
    # Value stopped probes the cap would have allowed.
    assert sum(1 for item in pool if not item.voi["former_cap"]["would_bind"]) == 4


def _plan_with_probes(tmp_path, version, toml=""):
    from tests.test_daily_plan_build import _run_to_end
    from learnloop.daily_plan.engine import build_plan

    paths = create_daily_plan_vault(
        tmp_path / version.replace(".", "_"),
        learning_objects={"lo_repo": [(f"pi_probe_{i}", 1.0) for i in range(5)]},
        version=version,
        plan_toml=toml or None,
    )
    probe_ids = {f"pi_probe_{i}" for i in range(5)}

    def provider(_vault, _repository, item_ids):
        return {item_id: ScheduledCheck("project_probe") for item_id in item_ids if item_id in probe_ids}

    register_scheduled_check_provider(provider)
    try:
        env = make_env(paths.root, _probe_items())
        build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
        record, _ = _run_to_end(env)
        planned = {item.practice_item_id for item in record.items()} & probe_ids
        with env.repository.connection() as connection:
            details = [
                json.loads(row[0])
                for row in connection.execute(
                    "SELECT detail_json FROM router_decisions WHERE decision_kind = 'plan_block'"
                )
            ]
        return planned, details
    finally:
        unregister_scheduled_check_provider(provider)


def test_the_plan_values_project_probes_at_the_successor_and_counts_them_below(tmp_path):
    before, before_details = _plan_with_probes(tmp_path, "mvp-0.16")
    after, after_details = _plan_with_probes(tmp_path, "mvp-0.17")
    off, off_details = _plan_with_probes(tmp_path / "off", "mvp-0.17", "[voi_stopping]\nproject_probes = false\n")
    assert len(before) == len(off) == 4
    assert len(after) == 5
    assert not any("voi_decisions" in detail for detail in before_details + off_details)
    logged = [d for detail in after_details for d in detail.get("voi_decisions", [])]
    assert logged and {d["site"] for d in logged} == {voi.SITE_PROJECT_PROBE}


# ── Part 2: the probe hypothesis lane reads the diagnoser's verdict ──────────


def _lane_labels(vault, repository):
    return {h.label for h in build_hypothesis_set(vault, repository, "lo_svd_compute").hypotheses}


@pytest.mark.parametrize("version", ["mvp-0.16", "mvp-0.17"])
def test_a_slip_the_diagnoser_ruled_out_leaves_the_lane_only_at_the_successor(tmp_path, version):
    _paths, vault, repository = split_vault(tmp_path, version=version, seed=False)
    client = _StatementFake(causal_class="transient_execution")
    result = submit(vault, repository, client)
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    assert raw and all(event["is_misconception"] for event in raw)  # the taxonomy prior
    prior_labels = {f"misconception:{event['error_type']}" for event in raw}
    drain_jobs(vault, repository, client)
    labels = _lane_labels(vault, repository)
    if version == "mvp-0.16":
        assert prior_labels <= labels
    else:
        assert not (prior_labels & labels)


def test_the_lane_switch_restores_the_stored_flag(tmp_path):
    _paths, vault, repository = split_vault(
        tmp_path, version="mvp-0.17", seed=False, config="[diagnosis]\nprobe_lane_reads_diagnosis = false"
    )
    client = _StatementFake(causal_class="transient_execution")
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    assert {f"misconception:{event['error_type']}" for event in raw} <= _lane_labels(vault, repository)


@pytest.mark.parametrize(
    "version,pending,held_out",
    [("mvp-0.16", "hold_out", False), ("mvp-0.17", "hold_out", True), ("mvp-0.17", "keep_prior", False)],
)
def test_a_pending_diagnosis_holds_the_event_out_of_the_lane(tmp_path, version, pending, held_out):
    _paths, vault, repository = split_vault(
        tmp_path, version=version, seed=False, config=f'[diagnosis]\nprobe_lane_pending = "{pending}"'
    )
    client = _StatementFake()
    result = submit(vault, repository, client)  # the diagnosis job is queued, not drained
    assert repository.pending_live_diagnoses_for_active_errors(["lo_svd_compute"]) == [result.attempt_id]
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    labels = _lane_labels(vault, repository)
    prior_labels = {f"misconception:{event['error_type']}" for event in raw}
    assert bool(prior_labels & labels) is (not held_out)


def test_a_joint_vault_lane_is_unchanged(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.9", config="[diagnosis]\nshadow = true")
    client = _StatementFake(causal_class="transient_execution")
    submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    before = _lane_labels(vault, repository)
    vault.config.algorithms.algorithm_version = "mvp-0.17"
    # The overlay changes only blind-graded events: a joint vault at the
    # successor reads exactly what it read.
    assert _lane_labels(vault, repository) == before


# ── display and logging: the CLI and the decision_features receipt ───────────


def test_the_misconceptions_cli_lists_by_the_diagnosers_verdict_and_adds_fields(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.16", seed=False)
    client = _StatementFake(causal_class="transient_execution")
    result = submit(vault, repository, client)
    runner = CliRunner()
    pending = json.loads(runner.invoke(app, ["misconceptions", "--json", "--vault", str(paths.root)]).output)
    assert pending["version"] == 1
    assert {row["verdict_source"] for row in pending["misconceptions"]} == {"diagnosis_pending"}
    drain_jobs(vault, repository, client)
    listed = json.loads(runner.invoke(app, ["misconceptions", "--json", "--vault", str(paths.root)]).output)
    # The diagnoser ruled the slip out: the default listing drops it.
    assert listed["misconceptions"] == []
    every = json.loads(
        runner.invoke(app, ["misconceptions", "--all-errors", "--json", "--vault", str(paths.root)]).output
    )
    rows = [row for row in every["misconceptions"] if row["id"] in {
        e["id"] for e in repository.raw_error_events_for_attempt(result.attempt_id)
    }]
    assert rows and all(
        row["is_misconception"] is True  # the stored meaning, unchanged
        and row["misconception_verdict"] is False
        and row["verdict_source"] == "diagnosis"
        for row in rows
    )


def test_the_misconceptions_cli_on_a_joint_vault_only_gains_fields(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {"id": "err_a", "learning_object_id": LO, "error_type": "conceptual_slip", "severity": 0.7,
         "is_misconception": True, "status": "active", "created_at": NOW_ISO, "updated_at": NOW_ISO}
    )
    result = CliRunner().invoke(app, ["misconceptions", "--json", "--vault", str(paths.root)])
    (row,) = json.loads(result.output)["misconceptions"]
    assert row["is_misconception"] is row["misconception_verdict"] is True and row["verdict_source"] == "stored"
    text = CliRunner().invoke(app, ["misconceptions", "--vault", str(paths.root)]).output
    assert "err_a conceptual_slip (misconception) severity=0.70" in text


def test_the_decision_features_receipt_reads_the_overlay_and_says_so(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.16", seed=False)
    client = _StatementFake(causal_class="transient_execution")
    submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    build_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=session_id))
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT ability_vector_json, context_json FROM decision_features WHERE decision_type = 'selection'"
        ).fetchall()
    assert rows
    compute = 0
    for ability_json, context_json in rows:
        assert json.loads(context_json)["error_events"] == "diagnosis_overlay"
        ability = json.loads(ability_json)
        if ability.get("learning_object_id") == "lo_svd_compute":
            compute += 1
            # The diagnoser called it a slip: no misconception posterior (the
            # stored taxonomy prior would have logged one).
            assert not ability.get("misconception_posterior_by_error_type")
    assert compute
