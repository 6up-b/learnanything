"""Value-of-information stopping (mvp-0.21) composed with main at its merge.

* **Rank 4** of the multi-family EVSI study (``docs/reviews/evsi-multisim.md``
  §6.1), wired at the merge: the value rule's loss table charges the measured
  minutes an unresolved cause costs (EVSI calibration Part C,
  ``scheduling.unresolved_cost``) only behind ``evsi.measured_loss_enabled``
  (off by default). Off, the table is the minutes-only table exactly; on, every
  off-diagonal cell charges the measured cost, and the receipt names the
  regime.
* **EVSI calibration's forecast log**: every value decision the successor
  takes is a ``voi_forecasts`` row where it acts (behind
  ``evsi.forecast_logging``), once per decision, with router R1's selection
  markers; the robust gate's counterfactual evaluation (rank 1) is never
  logged as a gate decision.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.config.schema import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.diagnosis import voi_stopping as voi
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import unresolved_cost as UC
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue

from tests.helpers import create_basic_vault
from tests.test_voi_stopping import (
    CLOCK,
    INFORMATIVE,
    ROUTES,
    _answer_probe,
    _candidate,
    _cap,
    _ctx,
    _followup_setup,
    _further,
    _minutes,
    _probe_vault,
    _teach_back_vault,
)

LABEL_ACTIONS = {"robust_initial_grasp": "review", "unfamiliar": "study"}
PRIOR = {"unfamiliar": 0.5, "robust_initial_grasp": 0.5}


def _forecasts(repository, site=None):
    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM voi_forecasts ORDER BY created_at, id")]
    for row in rows:
        row["forecast"] = json.loads(row.pop("forecast_json"))
        row["versions"] = json.loads(row.pop("versions_json"))
        row["parameters"] = json.loads(row.pop("parameters_json"))
    return [row for row in rows if site is None or row["site"] == site]


# ── rank 4: the measured unresolved cost, behind evsi.measured_loss_enabled ──


def test_rank_four_off_prices_the_minutes_only_table_exactly(monkeypatch):
    """Off (the default) the value rule's table is today's minutes-only table,
    byte for byte, and the unresolved cost is never read."""

    def refuse(*_args, **_kwargs):  # pragma: no cover - must not run
        raise AssertionError("the measured loss is off")

    monkeypatch.setattr(UC, "unresolved_minutes_for_hypotheses", refuse)
    ctx = _ctx(ROUTES)
    assert ctx.measured_loss is False and ctx.loss_regime == voi.LOSS_REGIME_MINUTES
    table = ctx.loss_table(LABEL_ACTIONS)
    routes = [{"reason": label, "first_intervention": action} for label, action in sorted(LABEL_ACTIONS.items())]
    durations = AL.attempt_minutes_by_intervention(sorted(set(LABEL_ACTIONS.values())), repository=ctx.repository)
    today = AL.build_loss_table(
        routes=routes,
        hypotheses=sorted(LABEL_ACTIONS),
        duration_overrides={action: estimate.minutes for action, estimate in durations.items()},
    )
    assert table.table_hash == today.table_hash
    assert not any("unresolved_minutes" in cell.derivation for cell in table.cells.values())
    decision = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior=PRIOR, learning_object_id="lo", former_cap=_cap(),
    )
    body = decision.as_dict()
    assert body["context"]["loss_regime"] == voi.LOSS_REGIME_MINUTES and "unresolved_cost" not in body["context"]
    names = {p["name"]: p for p in body["parameters"]}
    assert names["loss_model"]["value"] == "triage_route_wasted_minutes" and "unresolved_minutes" not in names


class _RoutedRepository:
    """A real repository whose triage routes are the test's."""

    def __init__(self, repository, routes):
        self._repository = repository
        self._routes = routes

    def failure_triage_routes(self):
        return list(self._routes)

    def __getattr__(self, name):
        return getattr(self._repository, name)


def _measured_ctx(tmp_path, enabled):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    config = LearnLoopConfig()
    config.evsi.measured_loss_enabled = enabled
    return voi.VoiContext(SimpleNamespace(config=config), _RoutedRepository(repository, ROUTES)), repository


def test_rank_four_on_charges_the_measured_unresolved_cost(tmp_path):
    ctx, repository = _measured_ctx(tmp_path, enabled=False)
    minutes_only = ctx.loss_table(LABEL_ACTIONS)
    off = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior=PRIOR, learning_object_id="lo", former_cap=_cap(),
    )

    # The switch on, on the same context: the cache is keyed on the regime.
    ctx.vault.config.evsi.measured_loss_enabled = True
    assert ctx.loss_regime == voi.LOSS_REGIME_MEASURED
    measured = ctx.loss_table(LABEL_ACTIONS)
    assert measured.table_hash != minutes_only.table_hash
    estimate = UC.estimate_unresolved_cost(repository, pseudo_count=LearnLoopConfig().evsi.unresolved_cost_prior_pseudo_count)
    # A label is no causal hypothesis row, so its scope reads unknown: a
    # persistent cause, charged the estimate (here Eedi's population prior).
    assert estimate.provenance == "population_prior" and estimate.minutes > 0
    for hypothesis in measured.hypotheses:
        for action in measured.actions:
            charged = measured.loss(hypothesis, action) - minutes_only.loss(hypothesis, action)
            if action == measured.effective_action[hypothesis]:
                assert charged == pytest.approx(0.0)
            else:
                assert charged == pytest.approx(estimate.minutes, abs=1e-6)
                derivation = measured.cells[(hypothesis, action)].derivation
                assert derivation["unresolved_source"]["provenance"] == "population_prior"

    on = voi.value_candidates(
        ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", INFORMATIVE, 0.5)],
        prior=PRIOR, learning_object_id="lo", former_cap=_cap(),
    )
    assert on.best.method == off.best.method == voi.METHOD_ROBUST_EVSI
    # A wrong repair now also leaves the cause unresolved, so telling the
    # hypotheses apart is worth more.
    assert on.best.value_point_minutes > off.best.value_point_minutes
    body = on.as_dict()
    assert body["context"]["loss_regime"] == voi.LOSS_REGIME_MEASURED
    assert body["context"]["unresolved_cost"]["minutes"] == pytest.approx(estimate.minutes, abs=1e-6)
    names = {p["name"]: p for p in body["parameters"]}
    assert names["loss_model"]["value"] == voi.LOSS_REGIME_MEASURED
    assert names["unresolved_minutes"]["provenance"] == "population_prior"
    assert off.as_dict()["context"]["loss_regime"] == voi.LOSS_REGIME_MINUTES


def test_rank_four_is_off_by_default():
    assert LearnLoopConfig().evsi.measured_loss_enabled is False


# ── the forecast log: every value decision, once, where it acts ─────────────


def _sidecar_offer(paths, repository):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    spec = METHOD_REGISTRY["get_today_queue"]
    spec.handler(ctx, spec.params_model.model_validate({"sessionId": session_id}))
    return session_id


def test_a_committed_probe_logs_its_value_decision_once_beside_the_selection_forecast(tmp_path):
    from learnloop.diagnosis.probe_episodes import record_presentation_forecast

    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    session_id = _sidecar_offer(paths, repository)
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None
    (value,) = _forecasts(repository, "probe_episode_value_decision")
    assert value["receipt_key"] == f"probe_episode_value_decision:{presentation.id}"
    assert value["verdict"] == "measure" and value["presentation_id"] == presentation.id
    assert value["probe_episode_id"] == presentation.probe_episode_id
    assert value["chosen_practice_item_id"] == presentation.practice_item_id
    assert value["scheduler_candidate_id"] == presentation.scheduler_candidate_id
    forecast = value["forecast"]
    assert forecast["forecast_of"] == "committed" and forecast["described_ref"] == presentation.practice_item_id
    assert forecast["value_decision"] == presentation.selection_components["voi_stopping"]
    assert sum(forecast["predicted_outcomes"].values()) == pytest.approx(1.0)
    assert value["versions"]["value_decision_forecast_version"] == voi.FORECAST_VERSION
    assert value["evsi_point_minutes"] is not None and value["algorithm_version"] == "mvp-0.21"
    # The coarse provenance vocabulary: the study's values read heuristic.
    assert {p["provenance"] for p in value["parameters"]} <= {"measured", "population_prior", "heuristic", "structural"}
    assert any(p.get("fine_provenance") == voi.STUDY_PROVENANCE for p in value["parameters"])
    # Main's own selection forecast of the same presentation is its own site.
    (selection,) = _forecasts(repository, "probe_selection")
    assert selection["presentation_id"] == presentation.id
    # Logged once: a second pass over the presentation adds nothing.
    record_presentation_forecast(vault, repository, presentation, learning_object_id=presentation.probe_episode_id)
    assert len(_forecasts(repository, "probe_episode_value_decision")) == 1
    assert len(_forecasts(repository, "probe_selection")) == 1


def test_an_explored_probe_value_forecast_carries_router_r1s_marker(tmp_path, monkeypatch):
    from learnloop.scheduling import scheduler as S

    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    probes = {"pi_svd_define_001", "pi_svd_define_002"}

    def support(queue, session, config):
        target = next((item for item in queue[1:] if item.practice_item_id in probes), None)
        return None if target is None else (0.25, [target])

    monkeypatch.setattr(S, "_exploration_support", support)
    monkeypatch.setattr(S, "_exploration_draws", lambda queue, session, now, alternatives: (0.0, 0.0))
    S.build_due_queue(
        vault, repository, clock=CLOCK, session=S.SchedulerSession(session_id=session_id), persist_explanations=True,
    )
    presentation = repository.active_probe_presentation_for_session(session_id)
    assert presentation is not None
    marker = presentation.selection_components.get("scheduler_exploration")
    if marker is None:
        pytest.skip("the draw did not move a probe forward in this vault")
    (value,) = _forecasts(repository, "probe_episode_value_decision")
    assert value["forecast"]["selection"]["scheduler_exploration"] == marker
    assert value["forecast"]["selection"]["served_by"]["mechanism"] == "scheduler_seeded_exploration"
    (selection,) = _forecasts(repository, "probe_selection")
    assert selection["forecast"]["selection"]["scheduler_exploration"] == marker


def test_a_value_stop_is_logged_once_at_the_completion(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    episode = _answer_probe(vault, repository)
    assert episode.completion_reason == "value_of_information_stop"
    (stop,) = [
        row for row in _forecasts(repository, "probe_episode_value_decision")
        if row["receipt_key"] == f"probe_episode_value_decision:{episode.id}:value_of_information_stop"
    ]
    assert stop["verdict"] == "stop" and stop["probe_episode_id"] == episode.id and stop["decision_ref"] == episode.id
    assert stop["forecast"]["forecast_of"] == "nominal_best" and stop["chosen_practice_item_id"] is None
    with repository.connection() as connection:
        detail = json.loads(
            connection.execute("SELECT completion_detail_json FROM probe_episodes WHERE id = ?", (episode.id,)).fetchone()[0]
        )
    assert stop["forecast"]["value_decision"] == detail


def test_the_robust_gates_counterfactual_is_never_logged_as_a_gate_decision(tmp_path, monkeypatch):
    """Rank 1: while value decides an episode the robust gate is evaluated only
    as a counterfactual on the value receipts, so ``voi_forecasts`` holds no
    ``probe_robust_selection`` row for it; where the gate decides (the switch
    on) its forecast is logged as on main."""

    from tests import voi_restore_scenarios as S

    rows = {}
    for name, toml in (("value_decides", ""), ("gate_decides", "[voi_stopping]\nrobust_gate_with_value = true\n")):
        with monkeypatch.context() as patch:
            _minutes(patch, 0.02)
            vault, repository = S._gate_probe_vault(tmp_path / name, toml)
            for index in range(4):
                episode = repository.open_probe_episode("lo_svd_definition")
                if episode is None:
                    break
                answered = _answer_probe(vault, repository, score=4 if index % 2 else 0)
                if answered.status != "in_progress":
                    break
            rows[name] = _forecasts(repository, "probe_robust_selection")
    assert rows["value_decides"] == []
    assert rows["gate_decides"], "the gate decided and logged its forecast"


def test_each_follow_up_value_decision_is_one_forecast(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    queued = _further(loaded, repository, result)
    assert queued.triggered is True
    _minutes(monkeypatch, 10_000.0)
    stopped = _further(loaded, repository, result)
    assert stopped.triggered is False
    receipts = voi.followup_receipts(repository, result.attempt_id)
    rows = _forecasts(repository, "followup_value_decision")
    assert [row["receipt_key"] for row in rows] == [f"followup_value_decision:{r['id']}" for r in receipts]
    first, second = rows
    assert (first["verdict"], first["forecast"]["forecast_of"]) == ("measure", "committed")
    assert first["chosen_practice_item_id"] == receipts[0]["served_ref"]
    assert (second["verdict"], second["forecast"]["forecast_of"]) == ("stop", "nominal_best")
    assert {row["source_attempt_id"] for row in rows} == {result.attempt_id}
    assert [row["decision_ref"] for row in rows] == [r["id"] for r in receipts]
    # Main's follow-up selection forecast (the queued item's target facet)
    # stays its own site, written once for the queue.
    assert len(_forecasts(repository, "followup_selection")) <= 1


def test_forecast_logging_off_records_no_value_decision(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    loaded.config.evsi.forecast_logging = False
    _minutes(monkeypatch, 0.01)
    assert _further(loaded, repository, result).triggered is True
    assert voi.followup_receipts(repository, result.attempt_id)  # the successor's own receipt stays
    assert _forecasts(repository) == []


def test_teach_back_offers_log_one_forecast_per_teach_back_per_offer(tmp_path, monkeypatch):
    vault, repository = _teach_back_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)

    def offer():
        return build_due_queue(
            vault, repository, clock=CLOCK, session=SchedulerSession(session_id=session_id), persist_explanations=True,
        )

    queue = offer()
    first = _forecasts(repository, "teach_back_value_decision")
    teach_backs = [item for item in queue if item.selected_mode == "teach_back"]
    assert len(first) == 2 and {row["chosen_ref"] for row in first} == {"pi_svd_teach_001", "pi_svd_teach_002"}
    slate = teach_backs[0].scheduler_slate_id
    assert {row["decision_ref"] for row in first} == {slate}
    assert {row["receipt_key"] for row in first} == {f"teach_back_value_decision:{slate}:{row['chosen_ref']}" for row in first}
    by_ref = {item.practice_item_id: item.scheduler_candidate_id for item in teach_backs}
    for row in first:
        assert row["verdict"] == "measure" and row["forecast"]["forecast_of"] == "subject"
        assert row["scheduler_candidate_id"] == by_ref[row["chosen_ref"]]
    # Each offer is a decision (router R1's grain): a new build is a new slate.
    offer()
    assert len(_forecasts(repository, "teach_back_value_decision")) == 4


def test_plan_blocks_log_project_probe_value_decisions_with_r1s_decision_ref(tmp_path):
    from tests.test_voi_stopping import _plan_with_probes

    planned, details = _plan_with_probes(tmp_path, "mvp-0.21")
    assert len(planned) == 5
    vault_root = tmp_path / "mvp-0_21"
    repository = Repository(vault_root / "state.sqlite")
    rows = _forecasts(repository, "project_probe_value_decision")
    assert rows and {row["verdict"] for row in rows} <= {"measure", "stop"}
    with repository.connection() as connection:
        plan_blocks = {
            row[0]: json.loads(row[1])
            for row in connection.execute("SELECT id, detail_json FROM router_decisions WHERE decision_kind = 'plan_block'")
        }
    # Each forecast names router R1's plan_block row of the decision it came with.
    assert {row["decision_ref"] for row in rows} <= set(plan_blocks)
    for row in rows:
        logged = [
            d for d in plan_blocks[row["decision_ref"]].get("voi_decisions", [])
            if d.get("subject_ref") == row["chosen_ref"]
        ]
        assert logged and row["forecast"]["value_decision"] == logged[0]
        assert row["forecast"]["forecast_of"] == "subject"
    # A probe the plan already holds is conditioned on, not a value decision.
    assert not any(row["forecast"]["value_decision"].get("reason") == voi.REASON_ALREADY_PLANNED for row in rows)
