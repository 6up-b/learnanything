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

from learnloop.daily_plan.lanes import register_scheduled_check_provider, unregister_scheduled_check_provider

from tests.daily_plan_fakes import make_env
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

NOW_PLUS_DAY = __import__("datetime").datetime(2099, 1, 1, tzinfo=__import__("datetime").UTC)

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

    monkeypatch.setattr(UC, "estimate_unresolved_cost", refuse)
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


def _measured_ctx(tmp_path, enabled, repository=None):
    if repository is None:
        paths = create_basic_vault(tmp_path / "vault")
        repository = Repository(paths.sqlite_path)
    config = LearnLoopConfig()
    config.evsi.measured_loss_enabled = enabled
    return voi.VoiContext(SimpleNamespace(config=config), _RoutedRepository(repository, ROUTES)), repository


#: One label of every class, each routed to its own repair.
EVERY_CLASS = {
    "mastered": "advance",
    "robust_initial_grasp": "review",
    "unfamiliar": "study",
    "surface_only": "schema",
    "misconception:mc_adds_first": "contrast@misconception:mc_adds_first",
    "confuses_with:concept_rank": "contrast@confuses_with:concept_rank",
    "other_or_unknown": "triage",
}
CHARGED = {"misconception:mc_adds_first", "confuses_with:concept_rank", "other_or_unknown"}


def test_rank_four_reads_each_label_class_by_part_cs_definition():
    """The value rule's hypotheses are probe labels, not causal_hypotheses
    rows: each class is mapped explicitly (Part C charges a persistent cause)."""

    from learnloop.diagnosis import probe_hypotheses as PH

    # No problem: nothing is left unresolved.
    for label in ("mastered", PH.H_ROBUST):
        assert voi.unresolved_scope_for_label(label) == (voi.SCOPE_NO_PROBLEM, "no_problem_left_unresolved")
    # A gap the next teaching resolves (an absence, not a recurring belief).
    for label in (PH.H_UNFAMILIAR, PH.H_SURFACE_ONLY, PH.H_RECALL_WITHOUT_MECHANISM,
                  PH.H_PROCEDURE_WITHOUT_SELECTION, PH.H_SCHEMA_WITHOUT_TRANSFER):
        assert voi.unresolved_scope_for_label(label) == (voi.SCOPE_KNOWLEDGE_GAP, "gap_resolved_by_next_teaching")
    # Part C's own case: a misconception or a confusion persists.
    for label in (f"{PH.MISCONCEPTION_PREFIX}mc_1", f"{PH.MISCONCEPTION_PREFIX}conceptual_slip",
                  f"{PH.CONFUSES_PREFIX}concept_rank"):
        assert voi.unresolved_scope_for_label(label) == ("learner_state", "persistent_misconception")
    # The open set (and a label the map does not know) is an unknown cause.
    for label in (PH.H_OTHER, "a_label_from_the_future"):
        assert voi.unresolved_scope_for_label(label) == ("unknown", "unknown_cause")
    for label in (*voi.UNRESOLVED_NO_PROBLEM_LABELS, *voi.UNRESOLVED_GAP_LABELS):
        assert label in {"mastered", PH.H_ROBUST, PH.H_UNFAMILIAR, PH.H_SURFACE_ONLY, PH.H_RECALL_WITHOUT_MECHANISM,
                         PH.H_PROCEDURE_WITHOUT_SELECTION, PH.H_SCHEMA_WITHOUT_TRANSFER}


def test_rank_four_off_keeps_todays_table_for_every_label_class(tmp_path, monkeypatch):
    def refuse(*_args, **_kwargs):  # pragma: no cover - must not run
        raise AssertionError("the measured loss is off")

    monkeypatch.setattr(UC, "estimate_unresolved_cost", refuse)
    ctx, repository = _measured_ctx(tmp_path, enabled=False)
    table = ctx.loss_table(EVERY_CLASS)
    routes = [{"reason": label, "first_intervention": action} for label, action in sorted(EVERY_CLASS.items())]
    durations = AL.attempt_minutes_by_intervention(sorted(set(EVERY_CLASS.values())), repository=repository)
    today = AL.build_loss_table(
        routes=routes,
        hypotheses=sorted(EVERY_CLASS),
        duration_overrides={action: estimate.minutes for action, estimate in durations.items()},
    )
    assert table.table_hash == today.table_hash


def test_rank_four_on_charges_only_misconceptions_confusions_and_unknown_causes(tmp_path):
    ctx, repository = _measured_ctx(tmp_path, enabled=False)
    minutes_only = ctx.loss_table(EVERY_CLASS)
    # The switch on, on the same context: the cache is keyed on the regime.
    ctx.vault.config.evsi.measured_loss_enabled = True
    assert ctx.loss_regime == voi.LOSS_REGIME_MEASURED
    measured = ctx.loss_table(EVERY_CLASS)
    assert measured.table_hash != minutes_only.table_hash
    estimate = UC.estimate_unresolved_cost(repository, pseudo_count=LearnLoopConfig().evsi.unresolved_cost_prior_pseudo_count)
    assert estimate.provenance == "population_prior" and estimate.minutes > 0  # no history yet: Eedi's prior
    reasons = {}
    for hypothesis in measured.hypotheses:
        for action in measured.actions:
            charged = measured.loss(hypothesis, action) - minutes_only.loss(hypothesis, action)
            if action == measured.effective_action[hypothesis]:
                assert charged == pytest.approx(0.0)
                continue
            source = measured.cells[(hypothesis, action)].derivation["unresolved_source"]
            reasons[hypothesis] = (source["cause_scope"], source["source"])
            if hypothesis in CHARGED:
                assert charged == pytest.approx(estimate.minutes, abs=1e-6), hypothesis
                assert source["provenance"] == "population_prior"
            else:
                assert charged == pytest.approx(0.0), hypothesis
    assert reasons == {
        "mastered": ("no_problem", "no_problem_left_unresolved"),
        "robust_initial_grasp": ("no_problem", "no_problem_left_unresolved"),
        "unfamiliar": ("knowledge_gap", "gap_resolved_by_next_teaching"),
        "surface_only": ("knowledge_gap", "gap_resolved_by_next_teaching"),
        "misconception:mc_adds_first": ("learner_state", "eedi_population_prior"),
        "confuses_with:concept_rank": ("learner_state", "eedi_population_prior"),
        "other_or_unknown": ("unknown", "eedi_population_prior"),
    }


def test_misconception_labels_are_charged_the_learners_recurrence_measured_cost(tmp_path):
    """With the learner's own recurrence history, the misconception's charge is
    Part C's measured (shrunk) estimate, never a per-label guess."""

    from tests.test_causal_shadow_selection import CLOCK as SHADOW_CLOCK, LO_ID, _vault
    from tests.test_voi_forecasts import _attempt

    _vault_obj, repository = _vault(tmp_path)
    with repository.connection() as connection:
        for index, (when, latency) in enumerate([
            ("2026-01-01T10:00:00Z", 60), ("2026-01-05T10:00:00Z", 120), ("2026-01-09T10:00:00Z", 180),
        ]):
            _attempt(connection, f"att_rep_{index}", when, latency)
        connection.commit()
    for index in range(3):
        repository.append_causal_hypothesis(
            episode_key=f"rep:{index}", attempt_id=f"att_rep_{index}", cause_scope="learner_state",
            statement="Adds before multiplying.", statement_normalized="adds before multiplying",
            learning_object_id=LO_ID, status="candidate", clock=SHADOW_CLOCK,
        )
    ctx, _ = _measured_ctx(tmp_path, enabled=True, repository=repository)
    measured = ctx.loss_table(EVERY_CLASS)
    estimate = UC.estimate_unresolved_cost(repository, pseudo_count=LearnLoopConfig().evsi.unresolved_cost_prior_pseudo_count)
    assert estimate.provenance == "measured" and estimate.personal_classes == 1
    cell = measured.cells[("misconception:mc_adds_first", "study")].derivation
    assert cell["unresolved_minutes"] == pytest.approx(estimate.minutes, abs=1e-6)
    assert cell["unresolved_source"]["provenance"] == "measured"
    assert cell["unresolved_source"]["source"] == "shrunk_personal"
    assert "unresolved_minutes" in measured.cells[("unfamiliar", "advance")].derivation
    assert measured.cells[("unfamiliar", "advance")].derivation["unresolved_minutes"] == 0.0


RIVAL_MISCONCEPTIONS = {
    "misconception:mc_adds_first": {"wrong": 0.9, "right": 0.1},
    "misconception:mc_drops_sign": {"wrong": 0.1, "right": 0.9},
}
MISCONCEPTION_OR_GAP = {
    "unfamiliar": {"wrong": 0.9, "right": 0.1},
    "misconception:mc_adds_first": {"wrong": 0.1, "right": 0.9},
}
NO_PERSISTENT_CAUSE = {
    "unfamiliar": {"wrong": 0.9, "right": 0.1},
    "robust_initial_grasp": {"wrong": 0.1, "right": 0.9},
}


def test_rank_four_on_prices_the_decision_only_where_a_persistent_cause_is_at_stake(tmp_path):
    ctx, _repository = _measured_ctx(tmp_path, enabled=False)

    def decide(members):
        prior = {label: 0.5 for label in members}
        return voi.value_candidates(
            ctx, voi.SITE_PROBE_EPISODE, [_candidate("q", members, 0.5)],
            prior=prior, learning_object_id="lo", former_cap=_cap(),
        )

    off = {name: decide(members) for name, members in (
        ("rivals", RIVAL_MISCONCEPTIONS), ("split", MISCONCEPTION_OR_GAP), ("none", NO_PERSISTENT_CAUSE))}
    ctx.vault.config.evsi.measured_loss_enabled = True
    on = {name: decide(members) for name, members in (
        ("rivals", RIVAL_MISCONCEPTIONS), ("split", MISCONCEPTION_OR_GAP), ("none", NO_PERSISTENT_CAUSE))}
    for decision in (*off.values(), *on.values()):
        assert decision.best.method == voi.METHOD_ROBUST_EVSI
    # Two rival misconceptions: whichever is missed stays and recurs, so every
    # wrong repair costs U more and telling them apart is worth more.
    assert on["rivals"].best.value_point_minutes > off["rivals"].best.value_point_minutes
    # A gap against a lapse of a robust grasp: nothing persists, today's value.
    assert on["none"].best.value_point_minutes == pytest.approx(off["none"].best.value_point_minutes)
    assert on["none"].best.value_robust_minutes == pytest.approx(off["none"].best.value_robust_minutes)
    # A misconception against a gap: only missing the misconception costs U,
    # so before any answer the misconception's repair is the safer action.
    split = on["split"].as_dict()
    assert split["best"]["forecast"]["current_action"] == "contrast@misconception:mc_adds_first"
    assert on["split"].best.value_point_minutes != pytest.approx(off["split"].best.value_point_minutes)
    assert split["context"]["loss_regime"] == voi.LOSS_REGIME_MEASURED
    assert split["context"]["unresolved_scopes"] == {
        "misconception:mc_adds_first": "learner_state", "unfamiliar": "knowledge_gap",
    }
    names = {p["name"]: p for p in split["parameters"]}
    assert names["loss_model"]["value"] == voi.LOSS_REGIME_MEASURED
    assert names["unresolved_minutes"]["provenance"] == "population_prior"
    assert off["split"].as_dict()["context"]["loss_regime"] == voi.LOSS_REGIME_MINUTES
    assert "unresolved_scopes" not in off["split"].as_dict()["context"]


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


# ── the live calibration report scores the four sites, by exact receipts ────


def _joined(vault, repository, site):
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores import voi_forecasts as store
    from learnloop.evsi_calibration import live_report as LR

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        forecasts = [row for row in store.list_forecasts(connection) if row["site"] == site]
        adapters = [LR.RouterOutcomeAdapter(connection), LR.LedgerOutcomeAdapter(connection)]
        return [(row, LR._join(connection, vault, row, adapters)) for row in forecasts]


def _report_site(vault, site):
    from learnloop.evsi_calibration import live_report as LR

    report = LR.calibration_report(vault)
    assert report["report_version"] == "voi_calibration_report_v6"
    return report["sites"][site]


def _answer_presentation(vault, repository, presentation, session_id, *, score=4):
    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
    from learnloop.diagnosis.probe_episodes import serve_presentation
    from learnloop.ids import new_ulid

    from datetime import UTC, datetime, timedelta

    from learnloop.clock import FrozenClock

    # The sidecar offer was built on the wall clock: answer after it.
    later = FrozenClock(datetime.now(UTC) + timedelta(minutes=1))
    serve_presentation(repository, presentation.id, clock=later)
    attempt_id = new_ulid()
    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=presentation.practice_item_id, learner_answer_md="answer",
                attempt_type="diagnostic_probe", session_id=session_id,
                probe_presentation_id=presentation.id,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=score, criterion_points={"correctness": float(score)}, evidence_rows=[],
                error_attributions=[], grader_confidence=1.0, confidence=4, manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=later,
    )
    return attempt_id


def test_the_report_scores_a_probe_continue_through_its_committed_presentation(tmp_path):
    from learnloop.vault.loader import load_vault

    paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    session_id = _sidecar_offer(paths, repository)
    presentation = repository.active_probe_presentation_for_session(session_id)
    (before,) = _joined(vault, repository, "probe_episode_value_decision")
    assert before[1]["status"] == "pending"  # committed, not answered yet: right-censored
    attempt_id = _answer_presentation(load_vault(paths.root), repository, presentation, session_id)
    joined = {row["receipt_key"]: result for row, result in _joined(vault, repository, "probe_episode_value_decision")}
    result = joined[f"probe_episode_value_decision:{presentation.id}"]
    assert result["attempt_id"] == attempt_id and result["status"] == "realized"
    (row,) = [r for r, _ in _joined(vault, repository, "probe_episode_value_decision")
              if r["receipt_key"] == f"probe_episode_value_decision:{presentation.id}"]
    assert result["emission"] in row["forecast"]["emission_alphabet"]
    site = _report_site(vault, "probe_episode_value_decision")
    assert site["outcome_reliability"]["realized_forecasts"] >= 1


def test_a_value_stop_is_never_joined_to_a_later_answer(tmp_path, monkeypatch):
    _paths, vault, repository = _probe_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    _answer_probe(vault, repository)  # the answer that let value stop the episode
    _answer_probe_after_stop = [result for row, result in _joined(vault, repository, "probe_episode_value_decision")
                                if row["verdict"] == "stop"]
    assert _answer_probe_after_stop and all(
        result["status"] == "not_administered" and "attempt_id" not in result for result in _answer_probe_after_stop
    )


def _followup_queue_offer_and_answer(repository, result, item, *, correctness_score=4):
    """The follow-up's own offer: a slate built after its queue offers the item
    as an intervention follow-up, and the answer is bound to that candidate."""

    from datetime import datetime, timedelta

    with repository.connection() as connection:
        queued_at = connection.execute(
            "SELECT created_at FROM attempt_surprise WHERE attempt_id = ?", (result.attempt_id,)
        ).fetchone()[0]
    at = datetime.fromisoformat(queued_at.replace("Z", "+00:00"))
    from learnloop.clock import FrozenClock

    slate = repository.record_scheduler_slate(
        [{"practice_item_id": item, "priority": 1.0, "components": {"selected": 1.0, "intervention_followup": 1.0}}],
        session_id="sess", algorithm_version="mvp-0.21", clock=FrozenClock(at + timedelta(minutes=1)),
    )
    with repository.connection() as connection:
        candidate = connection.execute(
            "SELECT id FROM scheduler_slate_candidates WHERE slate_id = ? AND practice_item_id = ?", (slate, item)
        ).fetchone()[0]
        answer_at = (at + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "rubric_score, correctness, scheduler_candidate_id, created_at) "
            "VALUES ('att_followup_answer', ?, ?, 'short_answer', 'independent_attempt', ?, ?, ?, ?)",
            (item, result.learning_object_id, correctness_score, correctness_score / 4.0, candidate, answer_at),
        )
        connection.commit()
    return "att_followup_answer"


def test_the_report_scores_a_queued_follow_up_through_its_receipt_and_offer(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    assert _further(loaded, repository, result).triggered is True
    (receipt,) = voi.followup_receipts(repository, result.attempt_id)
    attempt_id = _followup_queue_offer_and_answer(repository, result, receipt["served_ref"])
    ((row, joined),) = _joined(loaded, repository, "followup_value_decision")
    assert joined["attempt_id"] == attempt_id and joined["status"] == "realized"
    assert joined["emission"] in row["forecast"]["emission_alphabet"]
    assert joined["emission"].startswith("high|")  # a full-score answer, no error channel


def test_a_follow_up_decided_again_on_its_attempt_is_superseded(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    assert _further(loaded, repository, result).triggered is True
    assert _further(loaded, repository, result).triggered is True  # a second queue on the same attempt
    receipts = voi.followup_receipts(repository, result.attempt_id)
    _followup_queue_offer_and_answer(repository, result, receipts[1]["served_ref"])
    by_receipt = {row["decision_ref"]: joined for row, joined in _joined(loaded, repository, "followup_value_decision")}
    assert by_receipt[receipts[0]["id"]]["status"] == "superseded"
    assert by_receipt[receipts[1]["id"]]["status"] == "realized"


def test_a_suppression_revokes_the_queue_and_administers_nothing(tmp_path, monkeypatch):
    loaded, repository, result = _followup_setup(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    assert _further(loaded, repository, result).triggered is True
    _minutes(monkeypatch, 10_000.0)
    assert _further(loaded, repository, result).triggered is False  # a value suppression rewrites the queue
    receipts = voi.followup_receipts(repository, result.attempt_id)
    _followup_queue_offer_and_answer(repository, result, receipts[0]["served_ref"])
    by_receipt = {row["decision_ref"]: joined for row, joined in _joined(loaded, repository, "followup_value_decision")}
    assert by_receipt[receipts[0]["id"]]["status"] == "superseded"
    assert by_receipt[receipts[1]["id"]]["status"] == "not_administered"


def test_the_report_scores_a_kept_teach_back_through_its_offers_candidate(tmp_path, monkeypatch):
    vault, repository = _teach_back_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 0.01)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    build_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=session_id),
                    persist_explanations=True)
    rows = _joined(vault, repository, "teach_back_value_decision")
    assert rows and all(joined["status"] == "pending" for _row, joined in rows)  # none answered yet
    kept, _ = rows[0]
    with repository.connection() as connection:
        # An answer to the same item NOT bound to this offer is never its outcome.
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "rubric_score, correctness, created_at) VALUES ('att_unbound', ?, ?, 'teach_back', 'teach_back', 4, 1.0, "
            "'2099-01-01T00:00:00Z')",
            (kept["chosen_ref"], kept["learning_object_id"]),
        )
        connection.commit()
    assert {joined["status"] for row, joined in _joined(vault, repository, "teach_back_value_decision")
            if row["id"] == kept["id"]} == {"pending"}
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "rubric_score, correctness, scheduler_candidate_id, created_at) VALUES ('att_bound', ?, ?, 'teach_back', "
            "'teach_back', 1, 0.25, ?, '2099-01-02T00:00:00Z')",
            (kept["chosen_ref"], kept["learning_object_id"], kept["scheduler_candidate_id"]),
        )
        connection.commit()
    joined = {row["id"]: result for row, result in _joined(vault, repository, "teach_back_value_decision")}[kept["id"]]
    assert joined["attempt_id"] == "att_bound" and joined["status"] == "realized" and joined["emission"] == "incorrect"
    assert set(kept["forecast"]["emission_alphabet"]) == {"correct", "incorrect"}


def test_a_dropped_teach_back_is_not_administered(tmp_path, monkeypatch):
    vault, repository = _teach_back_vault(tmp_path, "mvp-0.21")
    _minutes(monkeypatch, 10_000.0)
    session_id = repository.create_session(energy=None, sleep_quality=None, available_minutes=30, notes_md_path=None)
    build_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=session_id),
                    persist_explanations=True)
    rows = _joined(vault, repository, "teach_back_value_decision")
    assert rows and {row["verdict"] for row, _ in rows} == {"stop"}
    assert {joined["status"] for _row, joined in rows} == {"not_administered"}


def test_the_report_scores_a_project_probe_through_r1s_plan_block(tmp_path):
    from learnloop.daily_plan.engine import advance, build_plan
    from learnloop.daily_plan.lanes import ScheduledCheck as Check
    from learnloop.db.stores import daily_plans as plan_store
    from learnloop.ids import new_ulid
    from tests.daily_plan_fakes import record_attempt
    from tests.helpers import create_daily_plan_vault
    from tests.test_voi_stopping import _probe_items

    paths = create_daily_plan_vault(
        tmp_path / "plan", learning_objects={"lo_repo": [(f"pi_probe_{i}", 1.0) for i in range(5)]},
        version="mvp-0.21",
    )
    probe_ids = {f"pi_probe_{i}" for i in range(5)}

    def provider(_vault, _repository, item_ids):
        return {item_id: Check("project_probe") for item_id in item_ids if item_id in probe_ids}

    register_scheduled_check_provider(provider)
    try:
        env = make_env(paths.root, _probe_items())
        build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
        advance(env, serve=False)
    finally:
        unregister_scheduled_check_provider(provider)
    repository = env.repository
    rows = _joined(env.vault, repository, "project_probe_value_decision")
    assert rows
    with repository.connection() as connection:
        planned = {
            (str(row["block_id"]), json.loads(row["detail_json"])["practice_item_id"])
            for row in connection.execute("SELECT block_id, detail_json FROM attention_block_events WHERE kind = 'item_planned'")
        }
        decision_refs = {str(row["id"]): str(row["decision_ref"]) for row in connection.execute(
            "SELECT id, decision_ref FROM attention_blocks")}
    admitted = [(row, joined) for row, joined in rows if row["verdict"] == "measure"]
    in_block = [(row, joined) for row, joined in admitted
                if (row["forecast"]["extra"]["plan_block_id"], row["chosen_ref"]) in planned]
    assert in_block, "an admitted probe is planned in the block its decision chose"
    row, joined = in_block[0]
    block_id = row["forecast"]["extra"]["plan_block_id"]
    assert row["decision_ref"] == decision_refs[block_id]  # R1's plan_block row names the block
    assert joined["status"] == "pending"  # planned, not served yet
    # An attempt on the probe with no serving receipt binds nothing (no session rule).
    record_attempt(repository, row["chosen_ref"], "lo_repo", NOW_PLUS_DAY)
    assert {j["status"] for r, j in _joined(env.vault, repository, "project_probe_value_decision")
            if r["id"] == row["id"]} == {"pending"}
    with repository.connection() as connection:
        plan_store.append_block_event(
            connection, event_id=new_ulid(), block_id=block_id, kind="item_served",
            detail={"practice_item_id": row["chosen_ref"], "scheduler_candidate_id": "cand_probe", "session_id": "s1"},
            created_at="2099-01-01T00:00:00Z",
        )
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "rubric_score, correctness, scheduler_candidate_id, created_at) VALUES ('att_probe', ?, 'lo_repo', "
            "'short_answer', 'independent_attempt', 4, 1.0, 'cand_probe', '2099-01-01T00:01:00Z')",
            (row["chosen_ref"],),
        )
        connection.commit()
    result = {r["id"]: j for r, j in _joined(env.vault, repository, "project_probe_value_decision")}[row["id"]]
    assert result["attempt_id"] == "att_probe" and result["status"] == "realized" and result["emission"] == "correct"
    # A probe its decision admitted but planned elsewhere is another decision's.
    elsewhere = [(r, j) for r, j in admitted if (r["forecast"]["extra"]["plan_block_id"], r["chosen_ref"]) not in planned]
    assert all(j["status"] == "not_planned_in_this_block" for _r, j in elsewhere)
    held_back = [j for r, j in rows if r["verdict"] == "stop"]
    assert all(j["status"] == "not_administered" for j in held_back)
