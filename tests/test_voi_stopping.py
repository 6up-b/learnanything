"""mvp-0.21: four count caps lifted onto value of information, and the probe
hypothesis lane reading the diagnoser's verdict under split grading.

Part 1 (``voi_stopping.enabled``, a sub-switch per site): a probe episode keeps
asking, a further follow-up is queued, a further teach-back is kept and a due
project probe enters the plan while the next observation's value pays for its
minutes. Part 2 (``diagnosis.probe_lane_reads_diagnosis``): the follow-up
misconception gate's hypothesis set reads the diagnosis overlay and holds out
an event whose diagnosis is pending. With a switch off, serving is mvp-0.20's
exactly; with both parts' switches off (``VOI_OFF``) it is mvp-0.20's
everywhere, the state every vault below mvp-0.21 was in.
"""

from __future__ import annotations

import json
from contextlib import closing

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.daily_plan.lanes import (
    classify_pool,
)
from learnloop.diagnosis.probe_episodes import (
    probe_serving_block_reason,
    probe_value_block_reason,
)
from learnloop.diagnosis.probes import build_hypothesis_set
from learnloop.diagnosis import voi_stopping as voi
from learnloop.scheduling.scheduler import OfferTrace, SchedulerSession, build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.daily_plan_fakes import scheduled
from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    create_basic_vault,
)
from tests.split_live_helpers import drain_jobs, split_vault, submit
from tests.active_errors_overlay_helpers import _StatementFake
from tests.voi_stopping_helpers import (
    CLOCK,
    INFORMATIVE,
    LO,
    ROUTES,
    _admission,
    _answer_probe,
    _build,
    _candidate,
    _cap,
    _checks,
    _classify,
    _config,
    _ctx,
    _fingerprint,
    _followup_setup,
    _further,
    _long_probe_vault,
    _minutes,
    _plan_with_probes,
    _probe,
    _probe_items,
    _probe_vault,
    _qualifying,
    _teach_back_vault,
)

#: Both parts' kill switches off: mvp-0.20's serving (each switch's off-branch is the predecessor's code).
VOI_OFF = "[voi_stopping]\nenabled = false\n[diagnosis]\nprobe_lane_reads_diagnosis = false\n"


def _predecessor(config):
    config.voi_stopping.enabled = False
    config.diagnosis.probe_lane_reads_diagnosis = False


# ── the gates ─────────────────────────────────────────────────────────────────


def test_the_value_gate_needs_the_switch_and_the_site():
    for site in voi.SITES:
        assert voi.voi_stopping_active(_config("mvp-0.21"), site)
        assert not voi.voi_stopping_active(_config("mvp-0.21", enabled=False), site)
        assert not voi.voi_stopping_active(_config("mvp-0.21", **{voi.SITE_SWITCH[site]: False}), site)
    # A sub-switch turns off its own site only.
    config = _config("mvp-0.21", teach_back=False)
    assert voi.voi_stopping_active(config, voi.SITE_PROBE_EPISODE)
    assert not voi.voi_stopping_active(config, voi.SITE_TEACH_BACK)


def test_the_probe_lane_gate_needs_its_switch():
    assert voi.probe_lane_reads_diagnosis(_config("mvp-0.21"))
    off = _config("mvp-0.21")
    off.diagnosis.probe_lane_reads_diagnosis = False
    assert not voi.probe_lane_reads_diagnosis(off)
    # Part 2 does not depend on Part 1's switch.
    assert voi.probe_lane_reads_diagnosis(_config("mvp-0.21", enabled=False))


# ── the value rule ────────────────────────────────────────────────────────────


FLAT = {"unfamiliar": {"wrong": 0.5, "right": 0.5}, "robust_initial_grasp": {"wrong": 0.5, "right": 0.5}}


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
    # A near-sure belief: the decision is still at stake across the whole
    # posterior (review F6), and the observation is unlikely to change the
    # repair, so robust EVSI stops it rather than the EIG objective.
    sure = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior={"unfamiliar": 0.97, "robust_initial_grasp": 0.03}, learning_object_id="lo", former_cap=_cap(),
    )
    assert sure.context["decision_at_stake"] is True
    assert sure.context["plausible_hypotheses"] == ["unfamiliar"]  # described, not gating
    assert sure.best.method == voi.METHOD_ROBUST_EVSI and sure.decision == voi.STOP
    costly = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 30.0)],
        prior={"unfamiliar": 0.5, "robust_initial_grasp": 0.5}, learning_object_id="lo", former_cap=_cap(),
    )
    assert costly.decision == voi.STOP and costly.best.reason == "lcb_evsi_below_minutes_cost"


def test_greater_certainty_never_restarts_an_unprofitable_measurement():
    """Review F6: crossing the plausibility cutoff used to switch a near-sure
    belief from robust EVSI (0.06 min, stop) to the EIG objective (8.04 min,
    continue). With a complete loss table EVSI decides across the posterior,
    so more certainty only shrinks the decision value."""

    ctx = _ctx(ROUTES)
    values = []
    for p in (0.85, 0.89, 0.91, 0.95, 0.99):
        decision = voi.value_candidates(
            ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
            prior={"unfamiliar": p, "robust_initial_grasp": 1.0 - p}, learning_object_id="lo", former_cap=_cap(),
        )
        assert decision.context["decision_at_stake"] is True
        assert decision.best.method == voi.METHOD_ROBUST_EVSI
        if p >= 0.89:
            assert decision.decision == voi.STOP
        values.append(decision.best.value_robust_minutes)
    assert values == sorted(values, reverse=True)
    # A missing route still falls back to the EIG objective (no loss table).
    missing = voi.value_candidates(
        _ctx(ROUTES[:1]), voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior={"unfamiliar": 0.91, "robust_initial_grasp": 0.09}, learning_object_id="lo", former_cap=_cap(),
    )
    assert missing.context["decision_at_stake"] is False and missing.best.method == voi.METHOD_EIG_VALUE


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
    for name in ("lambda_time", "burden_cost_minutes", "value_per_nat_minutes", "perturbation_delta", "loss_model"):
        assert names[name]["provenance"] == "heuristic"
    # voi-v2: the multi-family EVSI study's switches, at its recommendations.
    for name in ("robust_quantile", "lookahead_max_checks"):
        assert names[name]["provenance"] == "evsi_multisim"
        assert names[name]["source"] == f"voi_stopping.{name}"
    assert body["former_cap"] == {
        "name": "probe.episode.session_qualifying_observation_cap", "value": 4, "count": 4, "would_bind": True,
    }
    assert body["cap_comparison"] == "later"


def test_former_cap_counterfactuals():
    assert voi.former_cap(voi.SITE_PROBE_EPISODE, value=0, count=9)["would_bind"] is False
    assert voi.former_cap(voi.SITE_TEACH_BACK, value=1, count=1)["would_bind"] is True
    assert voi.former_cap(voi.SITE_PROJECT_PROBE, value=4, count=3)["would_bind"] is False


# ── (a) probe episodes: every next observation pays for its minutes ──────────


def _session_spent(monkeypatch, repository, count=4):
    """The session already holds ``count`` qualifying observations."""

    monkeypatch.setattr(repository, "qualifying_probe_observation_count_for_session", lambda _sid: count)


def test_with_the_switches_off_the_spent_session_cap_blocks_probes(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21", toml=VOI_OFF)
    _session_spent(monkeypatch, repository)
    assert probe_serving_block_reason(vault, repository, session_id="sess") == "session_cap_reached"
    queue = _build(vault, repository)
    assert all(item.components.get("probe_eig", 0.0) == 0.0 for item in queue)


def test_at_the_successor_value_keeps_asking_past_the_former_cap(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
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
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
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
def test_the_kill_switch_serves_mvp020s_probe_queue_exactly(tmp_path, monkeypatch, toml):
    _bp, base_vault, base_repo = _probe_vault(tmp_path / "base", "mvp-0.20", toml=VOI_OFF)
    _op, off_vault, off_repo = _probe_vault(tmp_path / "off", "mvp-0.21", toml=toml)
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
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
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


def test_with_the_switches_off_the_offer_logs_no_value_decisions(tmp_path):
    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21", toml=VOI_OFF)
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


def test_with_the_switches_off_a_further_follow_up_is_suppressed_by_count(tmp_path):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _predecessor(loaded.config)
    decision = _further(loaded, repository, result)
    assert decision.triggered is False
    assert decision.reason == f"intervention_followup:session_cap_reached:{LO}"
    assert "voi_stopping" not in (decision.gate_diagnostics or {})


def test_at_the_successor_a_further_follow_up_is_queued_while_its_value_pays(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
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
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
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


def _first(loaded, repository, result, **kwargs):
    return _further(loaded, repository, result, **{"session_interventions_for_lo": 0, **kwargs})


def test_the_first_follow_up_in_a_session_is_valued_too(tmp_path, monkeypatch):
    """Review F7: the former per-LO cap is neither a cap nor a floor. The first
    follow-up is valued like any other, and stops where value does not pay."""

    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    first = _first(loaded, repository, result)
    assert first.triggered is False
    assert first.reason == f"intervention_followup:voi_value_below_minutes_cost:{LO}"
    body = first.gate_diagnostics["voi_stopping"]
    assert body["decision"] == voi.STOP
    # The cap would have allowed it: value stops earlier.
    assert body["former_cap"]["would_bind"] is False and body["cap_comparison"] == "earlier"
    _minutes(monkeypatch, 0.01)
    queued = _first(loaded, repository, result)
    assert queued.triggered is True and queued.gate_diagnostics["voi_stopping"]["decision"] == voi.CONTINUE


def test_a_cheaper_follow_up_that_pays_is_queued_when_the_old_winner_does_not(tmp_path, monkeypatch):
    """Review F4: the whole eligible slate is valued. The slate ranking's pick
    costs too much; a comparable half-minute alternative pays and is queued."""

    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    root = tmp_path / "mvp-0_21"
    add_followup_item(root, "pi_svd_define_003")
    loaded = load_vault(root)
    loaded.config.algorithms.algorithm_version = "mvp-0.21"
    _minutes(monkeypatch, 0.01)
    ranking_pick = _further(loaded, repository, result).gate_diagnostics["voi_stopping"]["context"][
        "slate_ranking_pick"
    ]
    other = ({"pi_svd_define_002", "pi_svd_define_003"} - {ranking_pick}).pop()
    monkeypatch.setattr(
        voi.VoiContext,
        "item_minutes",
        lambda self, item, authored_minutes=None: voi.MinutesEstimate(
            10_000.0 if item.id == ranking_pick else 0.5, "authored_prior"
        ),
    )
    decision = _further(loaded, repository, result)
    assert decision.triggered is True and decision.practice_item_id == other
    body = decision.gate_diagnostics["voi_stopping"]
    assert body["candidate_count"] == 2 and body["context"]["slate_ranking_pick"] == ranking_pick
    assert body["recommended_ref"] == body["served_ref"] == body["chosen_ref"] == other
    assert body["served"]["ref"] == other and body["served"]["forecast"]["likelihood"]
    assert {c["ref"]: c["decision"] for c in body["candidates"]} == {other: voi.CONTINUE, ranking_pick: voi.STOP}
    # Only when the best remaining candidate fails does the follow-up stop.
    _minutes(monkeypatch, 10_000.0)
    stopped = _further(loaded, repository, result)
    assert stopped.triggered is False and stopped.gate_diagnostics["voi_stopping"]["candidate_count"] == 2


def _receipts(repository, attempt_id):
    return [
        (row["decision_ordinal"], row["decision_outcome"], row["verdict"], row["manual_override"], row["served_ref"])
        for row in voi.followup_receipts(repository, attempt_id)
    ]


def _rebuild_and_replay(loaded, repository, learning_object_id):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.substrate.replay import replay_learning_object

    rebuild_all_derived_state(loaded, repository, clock=CLOCK)
    rebuild_all_derived_state(loaded, repository, clock=CLOCK)
    replay_learning_object(loaded, repository, learning_object_id)


def test_each_follow_up_decision_keeps_its_own_receipt_through_rebuilds(tmp_path, monkeypatch):
    """Review F1: the decision-time forecast lives on an immutable receipt of
    its own (``followup_value_decisions``, one row per decision with its
    source-attempt link), which neither a rebuild nor a regrade's LO replay
    clears, and which a later decision on the same attempt never overwrites."""

    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    decision = _further(loaded, repository, result)
    assert decision.triggered is True
    (first,) = voi.followup_receipts(repository, result.attempt_id)
    assert first["decision"] == decision.gate_diagnostics["voi_stopping"]
    assert first["decision"]["served"]["forecast"]["predicted_outcomes"]
    assert (first["source_attempt_id"], first["decision_ordinal"], first["verdict"]) == (
        result.attempt_id, 1, voi.CONTINUE,
    )
    _rebuild_and_replay(loaded, repository, result.learning_object_id)
    # The derived copy is gone (attempt_surprise is rebuilt without it) ...
    assert "voi_stopping" not in (repository.latest_attempt_surprise(result.attempt_id).get("gate_diagnostics") or {})
    # ... the receipt is not.
    assert voi.followup_receipts(repository, result.attempt_id) == [first]
    # A later decision on the same attempt is a new receipt; the first stays.
    _minutes(monkeypatch, 10_000.0)
    later = _further(loaded, repository, result)
    assert later.gate_diagnostics["voi_stopping"]["decision"] == voi.STOP
    receipts = voi.followup_receipts(repository, result.attempt_id)
    assert receipts[0] == first and len(receipts) == 2
    assert receipts[1]["decision"] == later.gate_diagnostics["voi_stopping"] and receipts[1]["id"] != first["id"]
    assert voi.followup_receipt(repository, result.attempt_id) == receipts[1]["decision"]
    # Immutable: the table refuses an update or a delete.
    with repository.connection() as connection, pytest.raises(Exception, match="immutable"):
        connection.execute("UPDATE followup_value_decisions SET verdict = 'stop'")
    with repository.connection() as connection, pytest.raises(Exception, match="immutable"):
        connection.execute("DELETE FROM followup_value_decisions")


def test_a_need_then_a_queue_on_one_attempt_keeps_both_decisions(tmp_path, monkeypatch):
    """Review F1 reopened: a generation need is recorded (no candidate), a
    candidate becomes available, the follow-up is queued. The queue's forecast
    is durable across rebuilds, beside the need's receipt."""

    from tests.followups_helpers import _surprising_attempt

    root = tmp_path / "need"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)
    loaded, result = _surprising_attempt(root, repository)
    loaded.config.algorithms.algorithm_version = "mvp-0.21"
    _minutes(monkeypatch, 0.01)
    need = _further(loaded, repository, result)
    assert need.triggered is False and need.need_id is not None
    add_followup_item(root)
    loaded = load_vault(root)
    loaded.config.algorithms.algorithm_version = "mvp-0.21"
    queued = _further(loaded, repository, result)
    assert queued.triggered is True and queued.practice_item_id == "pi_svd_define_002"
    _rebuild_and_replay(loaded, repository, result.learning_object_id)
    assert _receipts(repository, result.attempt_id) == [
        (1, "created_need_for_generation", None, False, None),
        (2, "queued_non_diagnostic_review", voi.CONTINUE, False, "pi_svd_define_002"),
    ]
    rows = voi.followup_receipts(repository, result.attempt_id)
    assert rows[0]["need_id"] == need.need_id and rows[0]["decision"] is None
    assert rows[1]["decision"] == queued.gate_diagnostics["voi_stopping"]
    assert rows[1]["decision"]["served"]["forecast"]["likelihood"]
    assert voi.followup_receipt(repository, result.attempt_id) == rows[1]["decision"]


def test_an_automatic_suppression_then_a_manual_follow_up_keeps_both_decisions(tmp_path, monkeypatch):
    """Review F1 reopened: value suppresses the automatic follow-up, then the
    learner asks for one. Both decisions keep their receipts across rebuilds,
    and the manual one's features row is written (the suppression no longer
    takes the attempt's one decision_features slot)."""

    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    auto = _further(loaded, repository, result)
    assert auto.triggered is False
    assert repository.decision_features(decision_id=result.attempt_id, decision_type="followup") is None
    forced = _further(loaded, repository, result, manual_override=True)
    assert forced.triggered is True
    _rebuild_and_replay(loaded, repository, result.learning_object_id)
    assert _receipts(repository, result.attempt_id) == [
        (1, "suppressed_voi_value_below_minutes_cost", voi.STOP, False, None),
        (2, "queued_non_diagnostic_review", voi.STOP, True, forced.practice_item_id),
    ]
    suppression, manual = (row["decision"] for row in voi.followup_receipts(repository, result.attempt_id))
    assert suppression == auto.gate_diagnostics["voi_stopping"] and suppression["best"]["forecast"]
    assert manual["served_by"] == {"mechanism": "manual_override"} and manual["served"]["forecast"]["likelihood"]
    features = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    assert features["context"]["decision_outcome"] == "queued_non_diagnostic_review"
    assert "voi_stopping" not in features["context"]


def test_a_value_suppressed_follow_up_keeps_its_receipt(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    decision = _further(loaded, repository, result)
    assert decision.triggered is False
    receipt = voi.followup_receipt(repository, result.attempt_id)
    assert receipt is not None and receipt["decision"] == voi.STOP and receipt["best"]["forecast"]
    assert _receipts(repository, result.attempt_id) == [
        (1, "suppressed_voi_value_below_minutes_cost", voi.STOP, False, None),
    ]


def test_with_the_switches_off_no_follow_up_receipt_carries_a_value_decision(tmp_path):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _predecessor(loaded.config)
    _first(loaded, repository, result)
    row = repository.decision_features(decision_id=result.attempt_id, decision_type="followup")
    assert row is not None and "voi_stopping" not in row["context"]
    assert voi.followup_receipt(repository, result.attempt_id) is None
    assert voi.followup_receipts(repository, result.attempt_id) == []


def test_value_suppressions_never_label_the_trigger(tmp_path, monkeypatch):
    """Review F9: a trigger that fired and was then outvalued says nothing
    about trigger quality: neither a silent negative nor, under a manual
    override, a gate false negative."""

    from learnloop.diagnosis.gate_fit import assemble_gate_training_set

    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    suppressed = _further(loaded, repository, result)
    assert suppressed.gate_diagnostics["decisive_reason"] == voi.VOI_VALUE_SUPPRESSION
    assert not [e for e in assemble_gate_training_set(repository, loaded.config) if e.attempt_id == result.attempt_id]
    forced = _further(loaded, repository, result, manual_override=True)
    assert forced.gate_diagnostics["would_suppress"] == [voi.VOI_VALUE_SUPPRESSION]
    assert forced.gate_diagnostics["would_auto_fire"] is False  # honest: value would have stopped it
    assert not [e for e in assemble_gate_training_set(repository, loaded.config) if e.attempt_id == result.attempt_id]
    # Valuation suppressions are the only reasons the fitter learns to ignore.
    assert voi.VALUATION_SUPPRESSION_REASONS == {voi.VOI_VALUE_SUPPRESSION}


@pytest.mark.parametrize("switch", ["enabled", "followups"])
def test_the_kill_switch_restores_the_follow_up_count_cap(tmp_path, switch):
    base, base_repo, base_result = _followup_setup(tmp_path / "base", "mvp-0.20")
    _predecessor(base.config)
    off, off_repo, off_result = _followup_setup(tmp_path / "off", "mvp-0.21")
    setattr(off.config.voi_stopping, switch, False)
    expected = _further(base, base_repo, base_result)
    actual = _further(off, off_repo, off_result)
    assert (actual.triggered, actual.reason, actual.suppressed_actions) == (
        expected.triggered, expected.reason, expected.suppressed_actions,
    )
    assert actual.gate_diagnostics == expected.gate_diagnostics


# ── (c) further teach-backs ──────────────────────────────────────────────────


def _teach_backs(queue):
    return [entry.practice_item_id for entry in queue if entry.selected_mode == "teach_back"]


def _teach_back_decisions(trace):
    return {d["subject_ref"]: d for d in trace.voi_decisions if d["site"] == voi.SITE_TEACH_BACK}


def test_teach_backs_stay_while_their_conditional_value_pays(tmp_path, monkeypatch):
    base_vault, base_repo = _teach_back_vault(tmp_path, "mvp-0.20")
    _predecessor(base_vault.config)
    vault, repository = _teach_back_vault(tmp_path, "mvp-0.21")
    assert len(_teach_backs(_build(base_vault, base_repo, session_id="sess_1"))) == 1
    _minutes(monkeypatch, 0.01)
    trace = OfferTrace()
    queue = _build(vault, repository, session_id="sess_1", trace=trace)
    assert len(_teach_backs(queue)) == 2
    decisions = sorted(_teach_back_decisions(trace).values(), key=lambda d: d["greedy_step"])
    assert len(decisions) == 2 and all(d["decision"] == voi.CONTINUE and d["admitted"] for d in decisions)
    assert [d["former_cap"]["would_bind"] for d in decisions] == [False, True]
    assert trace.teach_back_exclusion_reason == "teach_back_value_below_minutes_cost"
    # The second is valued given the first (the reward body reproduces the
    # logged total, so the decomposition is available), and is worth less.
    first, second = (d["subject"] for d in decisions)
    assert first["detail"]["conditioning"] == "none_chosen"
    assert second["detail"]["conditioning"] == "chosen_before"
    assert second["eig_nats"] < second["detail"]["unconditioned_eig_nats"]
    assert first["eig_nats"] == pytest.approx(first["detail"]["unconditioned_eig_nats"])


def test_a_second_teach_back_that_tells_the_same_thing_is_not_admitted(tmp_path, monkeypatch):
    """Review F2: two teach-backs on the same uncertainty each clear their
    minutes alone; once the first is admitted the second adds too little, so
    it is not (the greedy conditional rule, reader spec §9.3 item 3)."""

    vault, repository = _teach_back_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    trace = OfferTrace()
    _build(vault, repository, session_id="sess_1", trace=trace)
    second = max(_teach_back_decisions(trace).values(), key=lambda d: d["greedy_step"])["subject"]
    alone = voi.VALUE_PER_NAT_MINUTES * second["detail"]["unconditioned_eig_nats"]
    given_first = second["evsi_robust_minutes"]
    assert given_first < alone
    _minutes(monkeypatch, (alone + given_first) / 2.0)  # each alone pays; the second given the first does not
    trace = OfferTrace()
    queue = _build(vault, repository, session_id="sess_1", trace=trace)
    assert len(_teach_backs(queue)) == 1
    decisions = _teach_back_decisions(trace)
    dropped = [d for d in decisions.values() if not d["admitted"]]
    assert len(dropped) == 1 and dropped[0]["decision"] == voi.STOP
    assert dropped[0]["subject"]["detail"]["conditioning"] == "chosen_before"
    assert dropped[0]["subject"]["detail"]["unconditioned_eig_nats"] * voi.VALUE_PER_NAT_MINUTES > (
        dropped[0]["subject"]["cost_minutes"]
    )


def test_a_teach_back_whose_value_does_not_pay_is_dropped_the_first_included(tmp_path, monkeypatch):
    """Review F7: the former cap is not a floor."""

    vault, repository = _teach_back_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    trace = OfferTrace()
    queue = _build(vault, repository, session_id="sess_1", trace=trace)
    assert _teach_backs(queue) == []
    decisions = list(_teach_back_decisions(trace).values())
    assert len(decisions) == 2 and all(d["decision"] == voi.STOP for d in decisions)
    # The cap would have kept the first: value stopped earlier.
    assert all(d["former_cap"]["would_bind"] is False and d["cap_comparison"] == "earlier" for d in decisions)


def test_a_sole_teach_back_is_valued_and_receipted(tmp_path, monkeypatch):
    """Review F7: a sole teach-back used to survive under the cap with no
    receipt; now it is valued like any other."""

    from tests.teach_back_helpers import _seed_lo_evidence, _setup

    _root, vault, repository = _setup(tmp_path / "sole")
    _seed_lo_evidence(repository)
    vault.config.algorithms.algorithm_version = "mvp-0.21"
    _minutes(monkeypatch, 10_000.0)
    trace = OfferTrace()
    assert _teach_backs(_build(vault, repository, session_id="sess_1", trace=trace)) == []
    (receipt,) = _teach_back_decisions(trace).values()
    assert receipt["decision"] == voi.STOP and receipt["subject"]["forecast"]
    _minutes(monkeypatch, 0.01)
    trace = OfferTrace()
    assert len(_teach_backs(_build(vault, repository, session_id="sess_1", trace=trace))) == 1
    (receipt,) = _teach_back_decisions(trace).values()
    assert receipt["decision"] == voi.CONTINUE


@pytest.mark.parametrize("switch", ["enabled", "teach_back"])
def test_the_kill_switch_serves_mvp020s_teach_back_queue_exactly(tmp_path, monkeypatch, switch):
    base_vault, base_repo = _teach_back_vault(tmp_path / "base", "mvp-0.20")
    _predecessor(base_vault.config)
    vault, repository = _teach_back_vault(tmp_path / "off", "mvp-0.21")
    setattr(vault.config.voi_stopping, switch, False)
    _minutes(monkeypatch, 0.01)
    assert _fingerprint(_build(vault, repository, session_id="sess_1")) == _fingerprint(
        _build(base_vault, base_repo, session_id="sess_1")
    )


# ── (d) project probes in the daily plan ─────────────────────────────────────


def _lanes(pool):
    return {item.practice_item_id: item.lane for item in pool}


def test_valued_project_probes_have_no_count_cap_and_are_planned_in_value_order():
    items = [_probe(f"pi_probe_{i}", f"lo_{i}", {f"facet_{i}": 1.0}) for i in range(5)]
    items[2] = _probe("pi_probe_2", "lo_2", {"facet_2": 1.0}, lo_variance=2.0, facet_variance=0.25, mass=0.0)
    pool = _classify(items)
    assert list(_lanes(pool).values()).count("maintain") == 5  # the fifth is no longer "later"
    probes = [item for item in pool if item.check_kind == "project_probe"]
    assert probes[0].practice_item_id == "pi_probe_2"  # the most information per minute first
    assert [item.plan_rank for item in probes] == [0, 1, 2, 3, 4]  # the plan ranks by value
    assert [item.voi["former_cap"]["would_bind"] for item in pool].count(True) == 1
    # Independent probes (different LOs and facets) lose nothing to each other.
    assert all(
        item.voi["subject"]["eig_nats"] == pytest.approx(item.voi["subject"]["detail"]["unconditioned_eig_nats"])
        for item in pool
    )


def test_a_project_probe_whose_value_does_not_pay_stays_later():
    pool = _classify(_probe_items(eig=0.001), checks=_checks())
    assert set(_lanes(pool).values()) == {None}
    assert {item.reason for item in pool} == {"a due project probe whose value does not pay for its minutes today"}
    # Value stopped probes the cap would have allowed, the first included.
    assert sum(1 for item in pool if not item.voi["former_cap"]["would_bind"]) == 5
    assert all(item.voi["decision"] == voi.STOP for item in pool)


def test_a_project_probe_that_duplicates_an_admitted_one_is_not_admitted():
    """Review F2: two probes on the same uncertainty each clear their minutes
    alone; given the first, the second adds too little and is not admitted,
    while an independent probe still is."""

    items = [
        _probe("pi_a", "lo_same", {"facet_x": 1.0}),
        _probe("pi_b", "lo_same", {"facet_x": 1.0}),
        _probe("pi_c", "lo_other", {"facet_y": 1.0}, lo_variance=0.6),
    ]
    alone = voi.VALUE_PER_NAT_MINUTES * items[1].components["probe_eig_total"]
    probe = {item.practice_item_id: item for item in _classify(items, minutes=0.01)}
    given_first = probe["pi_b"].voi["subject"]["evsi_robust_minutes"]
    assert probe["pi_b"].voi["subject"]["detail"]["conditioning"] == "chosen_before"
    assert given_first < alone
    minutes = (alone + given_first) / 2.0  # each alone pays; the second given the first does not
    pool = {item.practice_item_id: item for item in _classify(items, minutes=minutes)}
    assert pool["pi_a"].lane == pool["pi_c"].lane == "maintain"
    assert pool["pi_b"].lane is None and pool["pi_b"].voi["decision"] == voi.STOP
    assert pool["pi_b"].voi["subject"]["detail"]["unconditioned_eig_nats"] * voi.VALUE_PER_NAT_MINUTES > minutes


# Four equally likely hypotheses over two bits: a check reveals bit 1 or bit 2.
_FOUR = {"h00": 0.25, "h01": 0.25, "h10": 0.25, "h11": 0.25}


def _bit(index, *, accuracy=1.0):
    """Likelihood rows of a check that reports bit ``index`` (noisily below 1)."""

    return {
        label: {"one": accuracy if label[1 + index] == "1" else 1.0 - accuracy,
                "zero": 1.0 - accuracy if label[1 + index] == "1" else accuracy}
        for label in _FOUR
    }


def _channel(likelihood, belief="episode_1"):
    return {"belief_key": belief, "prior": dict(_FOUR), "likelihood": likelihood, "objective": "hypothesis_eig"}


def _bit_terms(likelihood, *, term=None, lo="lo_bits"):
    """A check whose only information is its hypothesis term (``term`` as the
    reward logs it; the check's EIG in nats when None)."""

    hypothesis = voi.expected_information_gain(likelihood, _FOUR) if term is None else term
    return voi.InformationTerms(
        learning_object_id=lo, hypothesis_nats=hypothesis, lo_prior_variance=1.0, lo_posterior_variance=1.0,
        discount=1.0, facets=(),
        hypothesis=voi.HypothesisChannel.from_mapping(_channel(likelihood), hypothesis_term=hypothesis),
    )


def test_hypothesis_information_is_valued_over_the_expected_posterior_branches():
    """Review F2 reopened: four equally likely hypotheses; two checks that
    reveal independent bits each keep ln 2 after the other; a check repeating
    an earlier one adds nothing; a noisy earlier check leaves the expected
    residual entropy of its bit."""

    import math

    bit1, bit2 = _bit_terms(_bit(0)), _bit_terms(_bit(1))
    assert bit1.conditional_nats(voi.InformationState())["hypothesis"] == pytest.approx(math.log(2))
    after_bit1 = voi.InformationState().after(bit1)
    assert bit2.conditional_nats(after_bit1)["hypothesis"] == pytest.approx(math.log(2))  # independent
    assert bit1.conditional_nats(after_bit1)["hypothesis"] == pytest.approx(0.0, abs=1e-12)  # the same bit
    after_both = after_bit1.after(bit2)
    assert bit2.conditional_nats(after_both)["hypothesis"] == pytest.approx(0.0, abs=1e-12)
    # A 90%-accurate report of bit 1 leaves h(0.1) nats about it.
    noisy = _bit_terms(_bit(0, accuracy=0.9))
    residual = -(0.9 * math.log(0.9) + 0.1 * math.log(0.1))
    assert bit1.conditional_nats(voi.InformationState().after(noisy))["hypothesis"] == pytest.approx(residual)
    # The reward's own scale (here a normalized term of 0.5 for ln 2 nats) is
    # kept: the first check reproduces its logged term, the second scales.
    scaled1, scaled2 = _bit_terms(_bit(0), term=0.5), _bit_terms(_bit(1), term=0.5)
    state = voi.InformationState().after(scaled1)
    assert scaled1.conditional_nats(voi.InformationState())["hypothesis"] == pytest.approx(0.5)
    assert scaled2.conditional_nats(state)["hypothesis"] == pytest.approx(0.5)
    assert scaled1.conditional_nats(state)["hypothesis"] == pytest.approx(0.0, abs=1e-12)
    # Checks on another hypothesis variable (another episode) are independent.
    other = voi.InformationTerms(
        learning_object_id="lo_bits", hypothesis_nats=math.log(2), lo_prior_variance=1.0,
        lo_posterior_variance=1.0, discount=1.0, facets=(),
        hypothesis=voi.HypothesisChannel.from_mapping(_channel(_bit(0), "episode_2"), hypothesis_term=math.log(2)),
    )
    assert other.conditional_nats(after_bit1)["hypothesis"] == pytest.approx(math.log(2))


def test_past_the_branch_bound_posteriors_merge_and_the_receipt_says_so(monkeypatch):
    """The bound is on arithmetic, never on checks: past it the expected
    posteriors merge at fewer decimals (keeping total probability and the
    mean belief) and later receipts label the coarse merge."""

    monkeypatch.setattr(voi, "_MAX_BELIEF_BRANCHES", 2)
    noisy = [_bit_terms(_bit(index % 2, accuracy=accuracy)) for index, accuracy in enumerate((0.9, 0.8, 0.7))]
    state = voi.InformationState()
    for terms in noisy:
        state = state.after(terms)
    branches = state.beliefs["episode_1"]
    assert "episode_1" in state.coarse_beliefs
    assert sum(weight for weight, _posterior in branches) == pytest.approx(1.0)
    mean = {label: sum(weight * dict(posterior)[label] for weight, posterior in branches) for label in _FOUR}
    assert mean == pytest.approx(_FOUR)  # merging keeps the prior as the mean posterior
    entries = [
        voi.InformationEntry(
            ref=f"pi_noisy_{index}", learning_object_id="lo_bits", eig_nats=terms.hypothesis_nats,
            minutes=voi.MinutesEstimate(0.01, "authored_prior"), terms=terms,
        )
        for index, terms in enumerate(noisy + [_bit_terms(_bit(0))])
    ]
    admission = voi.greedy_information_admission(_ctx(), voi.SITE_PROJECT_PROBE, entries, cap_value=4)
    assert len(admission.steps) >= 3
    labels = [value.detail.get("hypothesis_branches") for value in admission.steps[-1].candidates]
    assert labels and set(labels) == {"coarsely_merged"}
    assert all(
        value.detail.get("hypothesis_branches") is None for step in admission.steps[:2] for value in step.candidates
    )


def test_greedy_admission_keeps_independent_checks_and_drops_a_repeat():
    import math

    def entry(ref, likelihood):
        terms = _bit_terms(likelihood)
        return voi.InformationEntry(
            ref=ref, learning_object_id="lo_bits", eig_nats=terms.hypothesis_nats,
            minutes=voi.MinutesEstimate(1.0, "authored_prior"), terms=terms,
        )

    admission = voi.greedy_information_admission(
        _ctx(), voi.SITE_PROJECT_PROBE,
        [entry("pi_bit1", _bit(0)), entry("pi_bit1_again", _bit(0)), entry("pi_bit2", _bit(1))],
        cap_value=4,
    )
    assert set(admission.admitted) == {"pi_bit1", "pi_bit2"}
    second = admission.receipt_for(admission.admitted[1])["subject"]
    assert second["eig_nats"] == pytest.approx(math.log(2))
    assert second["detail"]["hypothesis_conditioning"] == "expected_posterior_branches"
    dropped = admission.receipt_for("pi_bit1_again")
    assert dropped["decision"] == voi.STOP and dropped["subject"]["eig_nats"] == pytest.approx(0.0, abs=1e-12)


def test_the_plan_values_probes_on_one_episode_over_its_hypotheses():
    """Review F2 reopened, through the plan's admission: two project probes on
    one open episode revealing independent bits are both admitted; one that
    repeats an admitted probe's bit is not (each alone pays)."""

    import math

    def probe(item_id, likelihood):
        return _probe(item_id, "lo_bits", {}, lo_variance=1.0, hypothesis_eig=math.log(2), channel=_channel(likelihood))

    items = [probe("pi_bit1", _bit(0)), probe("pi_bit1_again", _bit(0)), probe("pi_bit2", _bit(1))]
    pool = {item.practice_item_id: item for item in _classify(items, minutes=1.0)}
    assert pool["pi_bit1"].lane == pool["pi_bit2"].lane == "maintain"
    assert pool["pi_bit1_again"].lane is None
    assert pool["pi_bit1_again"].voi["subject"]["detail"]["unconditioned_eig_nats"] * voi.VALUE_PER_NAT_MINUTES > 1.0
    later = pool["pi_bit2"].voi["subject"]
    assert later["detail"]["conditioning"] == "chosen_before"
    assert later["detail"]["conditional_parts_nats"]["hypothesis"] == pytest.approx(math.log(2))


def test_the_scheduler_hands_an_in_episode_probe_its_likelihood_rows(tmp_path):
    """The rows the conditional valuation needs ride on the scheduled item at
    the successor (never persisted); the decomposed terms still reproduce the
    reward's total. With the switches off nothing is attached."""

    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    probes = [item for item in _build(vault, repository) if item.components.get("probe_eig", 0.0) > 0.0]
    assert probes
    episode = repository.open_probe_episode(LO)
    for item in probes:
        channel = item.hypothesis_channel
        assert channel["belief_key"] == episode.id and set(channel["likelihood"]) <= set(channel["prior"])
        terms = voi.InformationTerms.from_reward_debug(
            item.learning_object_id, item.reward_debug,
            total_nats=item.components["probe_eig_total"], hypothesis_channel=channel,
        )
        assert terms is not None and terms.hypothesis is not None
        assert terms.hypothesis_conditioning.startswith("expected_posterior_branches")
    _old, old_vault, old_repository = _probe_vault(tmp_path / "old", "mvp-0.21", toml=VOI_OFF)
    assert all(item.hypothesis_channel is None for item in _build(old_vault, old_repository))


def test_a_probe_the_plan_cannot_fit_neither_takes_a_slot_nor_discounts_another():
    """Review F10: five minutes to spend. Probe A (twelve minutes) is worth
    more per minute but cannot fit; B (five minutes) pays alone but adds little
    after A. Feasibility is part of the greedy selection, so A is not admitted
    (labelled), B is valued without A, and the plan has its five-minute block."""

    from learnloop.daily_plan.lanes import LegacyLanesSource
    from learnloop.daily_plan.types import LANES, PlanState

    items = [
        _probe("pi_a", "lo_same", {"facet_x": 2.0, "facet_y": 1.0}, mass=0.0),
        _probe("pi_b", "lo_same", {"facet_x": 1.0}, mass=0.0),
    ]
    minutes = {"pi_a": 12.0, "pi_b": 5.0}.__getitem__
    unbounded = {item.practice_item_id: item for item in _classify(items, minutes=minutes)}
    # Without the plan's minutes, A is admitted first and B no longer pays.
    assert unbounded["pi_a"].lane == "maintain" and unbounded["pi_b"].lane is None
    pool = _classify(items, minutes=minutes, admission=_admission(minutes_budget=5.0))
    by_id = {item.practice_item_id: item for item in pool}
    assert by_id["pi_a"].lane is None and by_id["pi_a"].reason == "a due project probe that does not fit today's minutes"
    assert by_id["pi_a"].voi["reason"] == voi.REASON_DOES_NOT_FIT
    assert by_id["pi_b"].lane == "maintain" and by_id["pi_b"].voi["subject"]["detail"]["conditioning"] == "none_chosen"
    state = PlanState(
        plan_id="p", kind="normal", minutes_budget=5.0, minutes_left=5.0,
        lane_minutes_left={lane: 5.0 if lane == "maintain" else 0.0 for lane in LANES},
        days_since_last_activity=0, streak_days=0, current_block_id=None,
    )
    assert [c.item_ids for c in LegacyLanesSource(pool=pool).candidates(state)] == [("pi_b",)]
    # The admitted probes' minutes are spent from the budget: two one-minute
    # probes and a two-minute budget plan two, never a third.
    three = [_probe(f"pi_{i}", f"lo_{i}", {f"facet_{i}": 1.0}) for i in range(3)]
    fitted = _classify(three, minutes=1.0, admission=_admission(minutes_budget=2.0))
    assert [item.lane for item in fitted].count("maintain") == 2
    (left,) = [item for item in fitted if item.lane is None]
    assert left.voi["reason"] == voi.REASON_DOES_NOT_FIT and left.voi["context"]["minutes_admitted"] == 2.0


def test_the_block_chooser_plans_the_best_probe_per_minute_first():
    """Review F5: two five-minute probes worth 12 and 60 minutes, five minutes
    to spend. The scheduler ranked the 12-minute one first; the plan's block
    score and the chooser must follow the value order, re-entry included."""

    from learnloop.daily_plan.chooser import LaneQuotaChooser
    from learnloop.daily_plan.lanes import LegacyLanesSource, reentry_order
    from learnloop.daily_plan.types import LANES, PlanState

    items = [scheduled("pi_low", "lo_a", probe_eig_total=0.2), scheduled("pi_high", "lo_b", probe_eig_total=1.0)]
    pool = _classify(items, minutes=5.0)
    by_id = {item.practice_item_id: item for item in pool}
    assert by_id["pi_high"].voi["subject"]["evsi_robust_minutes"] == pytest.approx(60.0)
    assert by_id["pi_low"].voi["subject"]["evsi_robust_minutes"] == pytest.approx(12.0)
    state = PlanState(
        plan_id="p", kind="normal", minutes_budget=5.0, minutes_left=5.0,
        lane_minutes_left={lane: 5.0 if lane == "maintain" else 0.0 for lane in LANES},
        days_since_last_activity=0, streak_days=0, current_block_id=None,
    )
    for ordered in (pool, reentry_order(pool)):
        candidates = LegacyLanesSource(pool=ordered).candidates(state)
        choice = LaneQuotaChooser().choose(state, candidates)
        chosen = next(c for c in candidates if c.candidate_id == choice.candidate_id)
        assert chosen.item_ids == ("pi_high",)
    # Below the successor the scheduler's rank still decides (no plan rank).
    old = classify_pool(
        items, item_states={}, requested_ids=[], now=NOW, estimate=lambda _id: 5.0,
        checks=_checks(["pi_low", "pi_high"]), probe_cap_left=4,
    )
    assert all(item.plan_rank is None for item in old)


def test_the_plan_values_project_probes_and_counts_them_with_the_switches_off(tmp_path):
    before, before_details = _plan_with_probes(tmp_path / "before", "mvp-0.21", VOI_OFF)
    after, after_details = _plan_with_probes(tmp_path, "mvp-0.21")
    off, off_details = _plan_with_probes(tmp_path / "off", "mvp-0.21", "[voi_stopping]\nproject_probes = false\n")
    assert len(before) == len(off) == 4
    assert len(after) == 5
    assert not any("voi_decisions" in detail for detail in before_details + off_details)
    logged = [d for detail in after_details for d in detail.get("voi_decisions", [])]
    assert logged and {d["site"] for d in logged} == {voi.SITE_PROJECT_PROBE}
    # Review F10: the plan's own minutes bound the admission.
    assert {d["context"]["minutes_budget"] for d in logged} == {40.0}


# ── Part 2: the probe hypothesis lane reads the diagnoser's verdict ──────────


def _lane_labels(vault, repository):
    return {h.label for h in build_hypothesis_set(vault, repository, "lo_svd_compute").hypotheses}


def test_a_slip_the_diagnoser_ruled_out_leaves_the_lane(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.21", seed=False)
    client = _StatementFake(causal_class="transient_execution")
    result = submit(vault, repository, client)
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    assert raw and all(event["is_misconception"] for event in raw)  # the taxonomy prior
    prior_labels = {f"misconception:{event['error_type']}" for event in raw}
    drain_jobs(vault, repository, client)
    labels = _lane_labels(vault, repository)
    assert not (prior_labels & labels)


def test_the_lane_switch_restores_the_stored_flag(tmp_path):
    _paths, vault, repository = split_vault(
        tmp_path, version="mvp-0.21", seed=False, config="[diagnosis]\nprobe_lane_reads_diagnosis = false"
    )
    client = _StatementFake(causal_class="transient_execution")
    result = submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    assert {f"misconception:{event['error_type']}" for event in raw} <= _lane_labels(vault, repository)


@pytest.mark.parametrize(
    "reads,pending,held_out",
    [("false", "hold_out", False), ("true", "hold_out", True), ("true", "keep_prior", False)],
)
def test_a_pending_diagnosis_holds_the_event_out_of_the_lane(tmp_path, reads, pending, held_out):
    _paths, vault, repository = split_vault(
        tmp_path, version="mvp-0.21", seed=False,
        config=f'[diagnosis]\nprobe_lane_pending = "{pending}"\nprobe_lane_reads_diagnosis = {reads}',
    )
    client = _StatementFake()
    result = submit(vault, repository, client)  # the diagnosis job is queued, not drained
    assert repository.pending_live_diagnoses_for_active_errors(["lo_svd_compute"]) == [result.attempt_id]
    raw = repository.raw_error_events_for_attempt(result.attempt_id)
    labels = _lane_labels(vault, repository)
    prior_labels = {f"misconception:{event['error_type']}" for event in raw}
    assert bool(prior_labels & labels) is (not held_out)


def test_a_joint_vault_lane_is_unchanged(tmp_path):
    # A joint vault: the split's kill switch (no vault that opens is below the split's tag).
    _paths, vault, repository = split_vault(
        tmp_path, version="mvp-0.9", config="[diagnosis]\nshadow = true\nsplit_enabled = false",
    )
    client = _StatementFake(causal_class="transient_execution")
    submit(vault, repository, client)
    drain_jobs(vault, repository, client)
    before = _lane_labels(vault, repository)
    vault.config.algorithms.algorithm_version = "mvp-0.21"
    # The overlay changes only blind-graded events: a joint vault at the
    # successor reads exactly what it read.
    assert _lane_labels(vault, repository) == before


# ── display and logging: the CLI and the decision_features receipt ───────────


def test_the_misconceptions_cli_lists_by_the_diagnosers_verdict_and_adds_fields(tmp_path):
    paths, vault, repository = split_vault(tmp_path, version="mvp-0.20", seed=False)
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
    _paths, vault, repository = split_vault(tmp_path, version="mvp-0.20", seed=False)
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


# ── (a) continued: a value stop ends the episode, with its decision ──────────


@pytest.mark.parametrize("switches", ["on", "off"])
def test_a_value_stop_ends_the_episode_only_with_the_switch_on(tmp_path, monkeypatch, switches):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21", toml=VOI_OFF if switches == "off" else "")
    _minutes(monkeypatch, 10_000.0)  # after one answer, nothing pays for its minutes
    episode = _answer_probe(vault, repository)
    if switches == "off":
        assert episode.completion_reason != "value_of_information_stop"
        return
    assert episode.status == "complete" and episode.completion_reason == "value_of_information_stop"
    with repository.connection() as connection:
        detail = json.loads(
            connection.execute(
                "SELECT completion_detail_json FROM probe_episodes WHERE id = ?", (episode.id,)
            ).fetchone()[0]
        )
    assert detail["site"] == voi.SITE_PROBE_EPISODE and detail["decision"] == voi.STOP
    assert detail["context"]["session_id"] == "sess" and detail["best"]["forecast"]["predicted_outcomes"]


def test_while_the_next_observation_pays_the_episode_keeps_asking(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.0001)
    episode = _answer_probe(vault, repository)
    assert episode.completion_reason != "value_of_information_stop"


def test_value_carries_one_episode_past_its_former_maximum(tmp_path, monkeypatch):
    """Review F3: ``probe.episode.maximum_observations`` (4) is lifted with the
    session cap. A real fifth observation is served and recorded within the
    same episode while its value pays; the receipt keeps the count's
    counterfactual."""

    vault, repository = _long_probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.0001)
    episode_id = repository.open_probe_episode(LO).id
    for index in range(5):
        # Mixed answers keep the rival hypotheses open, so each next one pays.
        episode = _answer_probe(vault, repository, score=4 if index % 2 else 0)
        assert episode.id == episode_id and episode.status == "in_progress", episode.completion_reason
    assert _qualifying(repository, episode_id) == 5 > episode.maximum_observations == 4
    reason, body = probe_value_block_reason(vault, repository, episode, "pi_svd_define_007", session_id="sess")
    assert reason is None and body["served_ref"] == "pi_svd_define_007"
    assert body["former_cap"]["episode_maximum"] == {
        "name": voi.EPISODE_MAXIMUM_CAP, "value": 4, "count": 5, "would_bind": True,
    }
    assert body["cap_comparison"] == "later"


@pytest.mark.parametrize(
    "version,toml", [("mvp-0.21", VOI_OFF), ("mvp-0.21", "[voi_stopping]\nprobe_episodes = false\n")]
)
def test_the_episode_maximum_still_ends_an_episode_off_the_value_rule(tmp_path, monkeypatch, version, toml):
    vault, repository = _long_probe_vault(tmp_path, version, toml)
    _minutes(monkeypatch, 0.0001)
    for _ in range(4):
        episode = _answer_probe(vault, repository)
    assert episode.status == "complete" and episode.completion_reason == "observation_budget_exhausted"
    assert _qualifying(repository, episode.id) == 4


def test_a_calibration_session_keeps_the_episode_maximum(tmp_path, monkeypatch):
    from learnloop.diagnosis import calibration_sessions

    vault, repository = _long_probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.0001)
    monkeypatch.setattr(calibration_sessions, "calibration_cap_lifted", lambda _repository, _session_id: True)
    for _ in range(4):
        episode = _answer_probe(vault, repository)
    assert episode.completion_reason == "observation_budget_exhausted"


@pytest.mark.parametrize("switches", ["on", "off"])
def test_the_probe_contract_says_value_decides_only_with_the_switch_on(tmp_path, switches):
    from learnloop.diagnosis.probe_episodes import episode_contract

    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21", toml=VOI_OFF if switches == "off" else "")
    contract = episode_contract(vault, repository, LO)
    assert contract["maximum_observations"] == 4
    assert contract.get("value_stopping", False) is (switches == "on")


def test_an_explored_probe_carries_its_own_forecast(tmp_path, monkeypatch):
    """Review F8: router R1's seeded exploration serves a probe other than
    value's pick. The committed presentation names both, and carries the
    SERVED probe's complete forecast with the exploration propensity."""

    from learnloop.scheduling import scheduler as S

    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    trace = OfferTrace()
    _build(vault, repository, session_id=session_id, trace=trace)
    (decision,) = [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    recommended = decision["recommended_ref"]
    other = ({"pi_svd_define_001", "pi_svd_define_002"} - {recommended}).pop()
    assert decision["decision"] == voi.CONTINUE and other in {c["ref"] for c in decision["candidates"]}

    def support(queue, session, config):
        # The seeded draw's design puts a quarter on ``other`` and the roll
        # below lands there, so the realized outcome matches the design.
        target = next((item for item in queue[1:] if item.practice_item_id == other), None)
        return None if target is None else (0.25, [target])

    monkeypatch.setattr(S, "_exploration_support", support)
    monkeypatch.setattr(S, "_exploration_draws", lambda queue, session, now, alternatives: (0.0, 0.0))
    S.build_due_queue(
        vault, repository, clock=CLOCK, session=S.SchedulerSession(session_id=session_id),
    )
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None and presentation.practice_item_id == other
    body = presentation.selection_components["voi_stopping"]
    assert body["recommended_ref"] == recommended and body["served_ref"] == body["chosen_ref"] == other
    assert body["served_is_recommended"] is False
    served = body["served"]
    assert served["ref"] == other and served["decision"] == voi.CONTINUE
    assert served["forecast"]["likelihood"] and sum(served["forecast"]["predicted_outcomes"].values()) == pytest.approx(1.0)
    assert body["served_by"]["mechanism"] == "scheduler_seeded_exploration"
    assert body["served_by"]["exploration_rate"] == 0.25
    assert body["served_by"]["selection_propensity"] == pytest.approx(0.25)
    assert body["served_by"]["selection_propensity_kind"] == "composed_outcomes"
    assert body["served_by"]["base_draw_propensity"] == pytest.approx(0.25)


def test_a_served_probe_records_its_probability_over_the_composed_queue(tmp_path, monkeypatch):
    """Review F11: exploration off, a teach-back heads the greedy order (draw
    probability one) and the probe follows (zero). Value drops the teach-back,
    so the probe is served deterministically: its receipt records probability
    one over the composed outcomes, and keeps the draw's zero apart."""

    from learnloop.scheduling import scheduler as S
    from tests.teach_back_helpers import _teach_item_payload

    paths, vault, repository = _probe_vault(
        tmp_path, "mvp-0.21", toml="[scheduler]\nselection_exploration_rate = 0.0\n"
    )
    upsert_practice_item(paths.root, _teach_item_payload("pi_svd_teach_001"), clock=CLOCK)
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    monkeypatch.setattr(
        voi.VoiContext,
        "item_minutes",
        lambda self, item, authored_minutes=None: voi.MinutesEstimate(
            10_000.0 if item.id == "pi_svd_teach_001" else 0.01, "authored_prior"
        ),
    )
    trace = OfferTrace()
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    queue = S.build_due_queue(
        vault, repository, clock=CLOCK, session=S.SchedulerSession(session_id=session_id), offer_trace=trace,
    )
    assert trace.greedy_item_ids[0] == "pi_svd_teach_001"  # the draw's sure pick
    assert "pi_svd_teach_001" not in [item.practice_item_id for item in queue]  # value dropped it
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None and presentation.practice_item_id == queue[0].practice_item_id
    served_by = presentation.selection_components["voi_stopping"]["served_by"]
    assert served_by["mechanism"] == "scheduler_greedy_order"
    assert served_by["selection_propensity"] == 1.0 and served_by["selection_propensity_kind"] == "composed_outcomes"
    assert served_by["base_draw_propensity"] == 0.0 and served_by["greedy_item_id"] == "pi_svd_teach_001"
    # The same probability the offer-trace machinery gives the composed head.
    assert sum(
        outcome.probability for outcome in trace.outcomes
        if outcome.composed and outcome.composed[0].practice_item_id == presentation.practice_item_id
    ) == served_by["selection_propensity"]
