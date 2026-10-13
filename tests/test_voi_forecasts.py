"""EVSI calibration Parts B and C: the live forecast log, its report, the measured loss.

Part B: every live value-of-information decision writes a ``voi_forecasts``
receipt beside it (logging only, kill switch ``evsi.forecast_logging``), and
``learnloop evsi calibration`` joins realized outcomes (R1's router tables when
present, else the ledgers) and independent later truth.

Part C: ``evsi.measured_loss_enabled`` (default off) charges the measured
minutes an unresolved persistent cause costs; off, every table is byte-identical.
"""

from __future__ import annotations

import dataclasses
import json
import sqlite3
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.db.stores import voi_forecasts as store
from learnloop.diagnosis import causal_diagnostic_selector as CDS
from learnloop.diagnosis import probe_robust as pr
from learnloop.diagnosis import voi_forecasting as DV
from learnloop.diagnosis.causal_probe_coherence import lock_causal_hypothesis_set
from learnloop.diagnosis.causal_probe_commissioning import commission_probe_instrument
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.evsi_calibration import live_report as LR
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import unresolved_cost as UC
from learnloop.scheduling import voi_forecasts as VF
from learnloop.vault.loader import load_vault

from tests.helpers import append_config_toml
from tests.test_causal_shadow_selection import CLOCK, LO_ID, PASSING_REVIEW, _seed_factor, _vault
from tests.test_probe_robust_cutover import _contrast_instrument, _load, _record_full_score_probe


def _forecasts(repository: Repository) -> list[dict]:
    with repository.connection() as connection:
        return store.list_forecasts(connection)


# -- the ledger --------------------------------------------------------------------------------


def test_the_ledger_is_append_only_and_idempotent(tmp_path):
    _vault_obj, repository = _vault(tmp_path)
    body = {"eig_nats": 0.5, "p_action_change": 0.25, "predicted_outcomes": {"a": 1.0}}
    first = VF.record_forecast(repository, site="probe_selection", receipt_key="probe_selection:x",
                               verdict="measure", forecast=body, parameters=[], clock=CLOCK)
    again = VF.record_forecast(repository, site="probe_selection", receipt_key="probe_selection:x",
                               verdict="measure", forecast=body, parameters=[], clock=CLOCK)
    assert first is not None and again is None
    rows = _forecasts(repository)
    assert len(rows) == 1 and rows[0]["eig_nats"] == 0.5 and rows[0]["p_action_change"] == 0.25
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE voi_forecasts SET verdict = 'stop'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM voi_forecasts")


def test_logging_never_raises_and_respects_the_kill_switch(tmp_path):
    vault, repository = _vault(tmp_path)
    # An unknown site is a logging bug, not a serving failure: swallowed.
    assert VF.record_forecast(repository, site="not_a_site", receipt_key="k", verdict="measure",
                              forecast={}, parameters=[]) is None
    off = SimpleNamespace(config=SimpleNamespace(evsi=SimpleNamespace(forecast_logging=False)))
    assert VF.record_forecast(repository, vault=off, site="probe_selection", receipt_key="k2",
                              verdict="measure", forecast={}, parameters=[]) is None
    read_only = Repository.attach(repository.sqlite_path, read_only=True)
    assert VF.record_forecast(read_only, site="probe_selection", receipt_key="k3", verdict="measure",
                              forecast={}, parameters=[]) is None
    assert _forecasts(repository) == []
    with pytest.raises(ValueError):
        VF.parameter("x", 1, "guess")


def test_forecast_block_predicts_answers_information_and_action_change():
    likelihood = {"h1": {"e1": 1.0}, "h2": {"e2": 1.0}}
    block = VF.forecast_block(
        likelihood, {"h1": 0.7, "h2": 0.3},
        action_of=lambda belief: "a1" if belief.get("h1", 0) >= belief.get("h2", 0) else "a2",
        action_proxy="test",
    )
    assert block["predicted_outcomes"] == {"e1": 0.7, "e2": 0.3}
    assert block["current_action"] == "a1"
    assert block["action_by_emission"] == {"e1": "a1", "e2": "a2"}
    # A noiseless check changes the action exactly when h2 is true.
    assert block["p_action_change"] == pytest.approx(0.3)
    assert block["eig_nats"] == pytest.approx(VF.entropy({"h1": 0.7, "h2": 0.3}))


# -- the live sites ------------------------------------------------------------------------------


def test_probe_selection_forecast_joins_its_realized_answer(tmp_path):
    loaded, repository = _load(tmp_path)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=CLOCK)
    presentation, attempt_id = _record_full_score_probe(loaded, repository, episode)

    rows = [r for r in _forecasts(repository) if r["site"] == "probe_selection"]
    assert len(rows) == 1
    row = rows[0]
    assert row["presentation_id"] == presentation.id
    assert row["eig_nats"] == pytest.approx(presentation.expected_information_gain)
    forecast = row["forecast"]
    assert abs(sum(forecast["predicted_outcomes"].values()) - 1.0) < 1e-6
    assert set(forecast["action_by_emission"]) == set(forecast["emission_alphabet"])
    provenances = {p["name"]: p["provenance"] for p in row["parameters"]}
    assert provenances["probe_families.ORDINAL_VOCABULARY"] == "heuristic"

    report = LR.calibration_report(loaded)
    site = report["sites"]["probe_selection"]
    assert site["forecasts"] == 1
    assert site["join_status"] == {"realized": 1}
    assert site["adapters"] == {"ledgers": 1}
    assert site["outcome_reliability"]["realized_forecasts"] == 1
    assert site["information"]["n"] == 1
    assert report["outcome_adapter"].startswith("ledgers")


def test_robust_gate_forecast_records_the_eig_paths_minutes(tmp_path):
    loaded, repository = _load(tmp_path)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=CLOCK)
    channel = pr.load_pinned_channel(repository, episode.calibration_model_hash)
    instrument = _contrast_instrument()
    labels = list(instrument.rows)
    posterior = {label: 1.0 / len(labels) for label in labels}
    slot_map = {label: label for label in labels}
    candidates = [pr.RobustCandidate("pi_svd_define_001", instrument, slot_map, 45.0)]
    decision = pr.robust_selection(channel, candidates, posterior, episode_id=episode.id)
    ensemble, _dch = pr.instrument_ensemble(channel, instrument, slot_map, posterior, episode_id=episode.id)
    forecast_id = DV.record_robust_selection_forecast(
        loaded, repository, episode=episode, decision=decision, candidates=candidates,
        ensembles={"pi_svd_define_001": ensemble}, posterior=posterior, observations=2, clock=CLOCK,
    )
    assert forecast_id is not None
    row = [r for r in _forecasts(repository) if r["site"] == "probe_robust_selection"][0]
    assert row["verdict"] == decision.verdict
    body = row["forecast"]
    assert body["evsi_from_eig_minutes"] == pytest.approx(60.0 * body["robust_eig_nats"], rel=1e-6)
    names = {p["name"] for p in row["parameters"]}
    assert "robust_composition.VALUE_PER_NAT_MINUTES" in names


def test_robust_completion_override_logs_its_forecast(tmp_path):
    from learnloop.diagnosis import probe_episodes as pe

    loaded, repository = _load(tmp_path)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=CLOCK)
    posterior = pe.episode_posterior(loaded, repository, episode)
    open_episode = dataclasses.replace(episode, minimum_independent_observations=0)
    pe._robust_completion_override(loaded, repository, open_episode, posterior)
    rows = [r for r in _forecasts(repository) if r["site"] == "probe_robust_selection"]
    assert len(rows) == 1 and rows[0]["probe_episode_id"] == episode.id


def test_followup_forecast_uses_the_facet_model(tmp_path):
    vault, repository = _vault(tmp_path)
    item = vault.practice_items["pi_svd_define_001"]
    marginal = {"facet_solid:recall": 0.5, "facet_absent:recall": 0.3, "misconception:conceptual_slip": 0.2}
    selection = SimpleNamespace(
        candidate=item,
        slate=[{"practice_item_id": item.id, "rank_score": 0.4, "total_facet_eig": 0.3,
                "facet_eig_by_facet": {"recall": 0.3}, "predictive_eig_by_facet": {}}],
        diagnostic_focus={"primary_target_facet": "recall", "target_facet_marginals": {"recall": marginal}},
        dominant_target_facet="recall",
        eligible_slate_size=1,
    )
    assert DV.record_followup_forecast(vault, repository, attempt_id="att_1", learning_object_id=LO_ID,
                                       selection=selection, clock=CLOCK) is not None
    row = _forecasts(repository)[0]
    assert row["site"] == "followup_selection" and row["chosen_practice_item_id"] == item.id
    assert row["eig_nats"] == pytest.approx(0.3)
    body = row["forecast"]
    assert abs(sum(body["predicted_outcomes"].values()) - 1.0) < 1e-6
    assert "low|conceptual_slip" in body["emission_alphabet"]


def _arm_b_shadow(tmp_path, *, measured: bool):
    vault, repository = _vault(tmp_path, probe_item=True)
    if measured:
        append_config_toml(vault.root, "\n[evsi]\nmeasured_loss_enabled = true\n")
        vault = load_vault(vault.root)
    factor_id, first_id, second_id = _seed_factor(repository, with_targets=True)
    result = commission_probe_instrument(
        vault, repository, factor_id=factor_id, adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate", reviewer_agent_run_id="agent_review", clock=CLOCK,
    )
    assert result["outcome"] == "commissioned"
    candidate = repository.causal_probe_candidate(result["candidate_id"])
    locked = lock_causal_hypothesis_set(
        repository, factor_id, probe_phase_id="phase_voi", algorithm_version="test",
        support_scores={first_id: 0.55, second_id: 0.45}, clock=CLOCK,
    )
    decision_receipt = {
        "id": f"receipt_voi_{int(measured)}", "factor_id": factor_id, "decision": "probe_now", "reason": "test",
        "inputs": {"probe_burden_minutes": 1.5, "common_repair_covers": False},
        "repair_class_ids": ["repair:recall", "repair:method"], "learning_object_id": LO_ID,
        "attempt_id": "att_shadow",
    }
    shadow = CDS.record_shadow_selection(
        repository, decision_receipt=decision_receipt, candidates=(),
        chosen_candidate={**candidate, "hypothesis_set_id": locked.id},
        repair_class_by_hypothesis={first_id: "repair:recall", second_id: "repair:method"},
        common_repair_class_id="repair:recall", vault=vault, clock=CLOCK,
    )
    return vault, repository, shadow, factor_id, (first_id, second_id)


def test_causal_shadow_records_its_formal_evsi_forecast(tmp_path):
    vault, repository, shadow, factor_id, (first_id, second_id) = _arm_b_shadow(tmp_path, measured=False)
    assert shadow["likelihood_regime"] == "arm_b_noiseless_partition"
    assert shadow["loss_table_regime"] == CDS.LOSS_TABLE_REGIME_SHADOW_V1
    rows = [r for r in _forecasts(repository) if r["site"] == "causal_shadow_selection"]
    assert len(rows) == 1
    row = rows[0]
    assert row["factor_id"] == factor_id
    assert row["evsi_point_minutes"] is not None and row["evsi_lcb_minutes"] is not None
    body = row["forecast"]
    # Noiseless partition: the check changes the action with the prior mass of
    # the hypothesis whose route is not the current action.
    assert row["p_action_change"] == pytest.approx(0.45, abs=1e-6)
    assert body["loss"]["effective_action"] == {first_id: "repair:recall", second_id: "repair:method"}
    by_name = {p["name"]: p for p in row["parameters"]}
    assert by_name["minutes[repair:recall]"]["provenance"] == "heuristic"
    assert by_name["minutes[repair:recall]"]["source"] == "heuristic_default"
    assert by_name["robust_composition.LAMBDA_TIME"]["provenance"] == "structural"
    assert not any(name.startswith("unresolved_minutes") for name in by_name)


def test_measured_loss_switch_charges_unresolved_minutes_in_the_shadow(tmp_path):
    vault, repository, shadow, _factor, (first_id, _second) = _arm_b_shadow(tmp_path, measured=True)
    assert shadow["loss_table_regime"] == CDS.LOSS_TABLE_REGIME_MEASURED_V1
    table = shadow["body"]["loss_table"]["table"]
    off_diagonal = [c for c in table["cells"] if c["minutes"] > 0]
    assert off_diagonal and all("unresolved_minutes" in c["derivation"] for c in off_diagonal)
    estimate = shadow["body"]["loss_table"]["unresolved_cost"]
    # No history in a fresh vault: the Eedi prior alone, with heuristic minutes per repeat.
    assert estimate["provenance"] == "population_prior"
    assert estimate["minutes"] == pytest.approx(
        UC.EEDI_EXCESS_REPEAT_RATE * UC.ENCOUNTERS_UNTIL_CAUGHT * AL.DEFAULT_INTERVENTION_MINUTES
    )
    row = [r for r in _forecasts(repository) if r["site"] == "causal_shadow_selection"][0]
    by_name = {p["name"]: p for p in row["parameters"]}
    assert by_name[f"unresolved_minutes[{first_id}]"]["provenance"] == "population_prior"


# -- the report's adapters and truth ------------------------------------------------------------


def _router_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE router_decisions (id TEXT PRIMARY KEY, chosen_scheduler_candidate_id TEXT, created_at TEXT);
        CREATE TABLE router_outcomes (decision_id TEXT PRIMARY KEY, action_status TEXT, action_attempt_id TEXT);
        INSERT INTO router_decisions VALUES ('d1', 'cand_1', '2026-05-19T12:00:00Z');
        INSERT INTO router_outcomes VALUES ('d1', 'taken', 'att_router');
        """
    )


def test_router_outcomes_are_preferred_when_r1_is_present():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    absent = LR.RouterOutcomeAdapter(connection)
    assert absent.available is False and absent.attempt_for({"scheduler_candidate_id": "cand_1"}) is None
    _router_tables(connection)
    adapter = LR.RouterOutcomeAdapter(connection)
    assert adapter.attempt_for({"scheduler_candidate_id": "cand_1"}) == ("att_router", "taken")
    assert adapter.attempt_for({"scheduler_candidate_id": "other"}) is None
    assert adapter.attempt_for({}) is None


def test_regret_counts_only_independent_truth():
    loss = {"minutes": {"h1": {"a1": 0.0, "a2": 6.0}, "h2": {"a1": 6.0, "a2": 0.0}},
            "effective_action": {"h1": "a1", "h2": "a2"}}
    forecast = {
        "site": "causal_shadow_selection", "verdict": "measure", "eig_nats": 0.6, "p_action_change": 0.3,
        "evsi_point_minutes": 1.8, "created_at": "2026-05-19T12:00:00Z",
        "forecast": {
            "prior": {"h1": 0.7, "h2": 0.3}, "likelihood": {"h1": {"e1": 1.0}, "h2": {"e2": 1.0}},
            "predicted_outcomes": {"e1": 0.7, "e2": 0.3}, "emission_alphabet": ["e1", "e2"],
            "current_action": "a1", "action_by_emission": {"e1": "a1", "e2": "a2"}, "loss": loss,
        },
    }
    rows = [
        (forecast, {"status": "realized", "adapter": "ledgers", "emission": "e2"},
         {"confirmed": ["h2"], "ruled_out": [], "sources": ["cold_verification"]}),
        (forecast, {"status": "pending", "adapter": "ledgers"}, None),
        # A repair that worked is repair effect, not truth about the cause.
        (forecast, {"status": "pending", "adapter": "ledgers"},
         {"confirmed": [], "ruled_out": [], "sources": [], "repair_effect": [{"success": True}]}),
    ]
    report = LR.summarize_joined(rows)
    site = report["sites"]["causal_shadow_selection"]
    assert site["forecasts"] == 3
    assert site["repair_effect"] == {"success": 1, "failure": 0}
    assert site["action_change"]["realized_rate"] == 1.0
    truth = site["truth"]
    assert truth["forecasts_with_truth"] == 1
    # The realized e2 moved the action to a2, the confirmed h2's repair: no regret.
    assert truth["mean_regret_minutes"] == 0.0
    assert truth["mean_probability_on_truth"] == 1.0


def _cold_verification(connection, verification_id: str, *, repair_class: str, hypothesis_ids: list[str],
                       success: bool, support: dict | None = None) -> None:
    connection.execute(
        "INSERT INTO causal_cold_verifications (id, source_attempt_id, cold_attempt_id, repair_class_id, "
        "hypothesis_ids_json, source_surface_family, cold_surface_family, avoided_affordances_json, success, "
        "capability_update_json, diagnosis_support_update_json, repair_effect_support_json, created_at) "
        "VALUES (?, 'a1', ?, ?, ?, 'f1', 'f2', '[]', ?, '{}', ?, '{}', '2026-05-20T12:00:00Z')",
        (verification_id, f"cold_{verification_id}", repair_class, json.dumps(hypothesis_ids), 1 if success else 0,
         json.dumps(support or {"delta": 0.0, "reason": "repair success does not retroactively prove the diagnosis"})),
    )


_TRUTH_FORECAST = {"created_at": "2026-05-19T12:00:00Z", "forecast": {
    "prior": {"h1": 0.5, "h2": 0.5}, "loss": {"effective_action": {"h1": "repair:a", "h2": "repair:b"}}}}


def test_repair_outcomes_are_not_diagnostic_truth(tmp_path):
    # Review F1: a cold check succeeding (or failing) on a repair class says the
    # repair worked (or not), not which cause was true; and a verification that
    # names other hypotheses (another episode) is not about this forecast at all.
    _vault_obj, repository = _vault(tmp_path)
    with repository.connection() as connection:
        assert LR.truth_for(connection, _TRUTH_FORECAST) is None
        # Another episode's hypotheses, sharing only the repair class route.
        _cold_verification(connection, "cv_other", repair_class="repair:b", hypothesis_ids=["h_elsewhere"],
                           success=True)
        assert LR.truth_for(connection, _TRUTH_FORECAST) is None
        # This forecast's own hypothesis, repaired successfully, then a failed repair:
        # repair effect only, never confirmed or ruled out.
        _cold_verification(connection, "cv_success", repair_class="repair:b", hypothesis_ids=["h2"], success=True)
        _cold_verification(connection, "cv_failure", repair_class="repair:a", hypothesis_ids=["h1"], success=False)
        truth = LR.truth_for(connection, _TRUTH_FORECAST)
    assert truth is not None
    assert truth["confirmed"] == [] and truth["ruled_out"] == []
    assert sorted((e["hypothesis_ids"], e["success"]) for e in truth["repair_effect"]) == [
        (["h1"], False), (["h2"], True)
    ]


def test_cold_verification_with_independent_diagnostic_support_is_truth(tmp_path):
    _vault_obj, repository = _vault(tmp_path)
    with repository.connection() as connection:
        _cold_verification(connection, "cv_supported", repair_class="repair:b", hypothesis_ids=["h2"], success=True,
                           support={"delta": 0.4, "basis": "blind_probe_match", "observation_id": "obs_blind_1"})
        _cold_verification(connection, "cv_refuted", repair_class="repair:a", hypothesis_ids=["h1"], success=True,
                           support={"delta": -0.3, "basis": "adjudication", "observation_id": "obs_adj_1"})
        # A support delta with no admitted basis is not evidence.
        _cold_verification(connection, "cv_unbased", repair_class="repair:a", hypothesis_ids=["h1"], success=True,
                           support={"delta": 0.5, "basis": "repair_success"})
        truth = LR.truth_for(connection, _TRUTH_FORECAST)
    assert truth["confirmed"] == ["h2"] and truth["ruled_out"] == ["h1"]
    assert truth["sources"] == ["cold_verification_diagnosis_support"]


def _discriminating_observation(connection, observation_id: str, *, probe_attempt_id: str, classified: list[str],
                                outcome: str = "matched_single", admitted: bool = True) -> None:
    connection.execute(
        "INSERT INTO causal_discriminating_observations (id, factor_id, attempt_id, probe_attempt_id, "
        "presentation_id, hypothesis_set_id, blind_bundle_ids_json, outcome, classified_as_json, supports_open_set, "
        "feature_source, observed_features_json, declared_keys_observed, admitted, admission_reason, "
        "support_scores_json, resolved_factor, detail_json, decision_policy_version, formula_version, created_at) "
        "VALUES (?, 'factor_x', 'att_src', ?, 'pres_x', 'hs_x', '[]', ?, ?, 0, 'deterministic', '{}', 1, ?, 'test', "
        "'{}', ?, '{}', 'v', 'v', '2026-05-20T12:00:00Z')",
        (observation_id, probe_attempt_id, outcome, json.dumps(classified), int(admitted), int(admitted)),
    )


def test_factor_resolution_by_repair_is_repair_effect_and_by_observation_is_truth(tmp_path):
    # Review F1, factor adapter: `repair_confirmed` / `escalated_unrepaired` are
    # repair outcomes. A factor closed by an admitted discriminating observation
    # is diagnostic evidence, unless that observation IS the forecast's own
    # realized answer (then it is not independent of the forecast).
    _vault_obj, repository = _vault(tmp_path)
    forecast = {**_TRUTH_FORECAST, "factor_id": "factor_x"}
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO unresolved_cause_factors (id, attempt_id, candidate_causes_json, status, algorithm_version, "
            "created_at, updated_at, resolution_kind, resolution_detail_json) VALUES ('factor_x', 'att_src', '[]', "
            "'resolved', 'test', '2026-05-19T00:00:00Z', '2026-05-21T00:00:00Z', 'repair_confirmed', ?)",
            (json.dumps({"cold_verification_id": "cv", "repair_class_id": "repair:b"}),),
        )
        truth = LR.truth_for(connection, forecast)
        assert truth is not None and truth["confirmed"] == [] and truth["ruled_out"] == []
        assert truth["repair_effect"] == [
            {"source": "factor_resolution", "resolution_kind": "repair_confirmed", "repair_class_id": "repair:b",
             "success": True}
        ]
        _discriminating_observation(connection, "obs_own", probe_attempt_id="att_probe", classified=["h2"])
        _discriminating_observation(connection, "obs_unadmitted", probe_attempt_id="att_other", classified=["h1"],
                                    admitted=False)
        _discriminating_observation(connection, "obs_ambiguous", probe_attempt_id="att_other2",
                                    classified=["h1", "h2"], outcome="matched_multiple")
        own = LR.truth_for(connection, forecast, realized_attempt_id="att_probe")
        assert own["confirmed"] == []
        later = LR.truth_for(connection, forecast, realized_attempt_id="att_something_else")
    assert later["confirmed"] == ["h2"] and later["sources"] == ["discriminating_observation"]


def test_cli_calibration_reports_read_only(tmp_path):
    loaded, repository = _load(tmp_path)
    episode = enter_episode(loaded, repository, "lo_svd_definition", clock=CLOCK)
    _record_full_score_probe(loaded, repository, episode)
    result = CliRunner().invoke(app, ["evsi", "calibration", "--vault", str(loaded.root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ok" and payload["forecasts"] >= 1
    assert payload["measured_loss_enabled"] is False
    # Part C's estimate is shown before anyone turns it on.
    assert payload["unresolved_cost_estimate"]["provenance"] == "population_prior"
    later = CliRunner().invoke(app, ["evsi", "calibration", "--vault", str(loaded.root), "--json",
                                     "--since", "2999-01-01T00:00:00Z"])
    assert json.loads(later.output)["forecasts"] == 0


# -- Part C ---------------------------------------------------------------------------------------


def test_loss_table_is_byte_identical_without_unresolved_minutes():
    routes = [{"reason": "h1", "first_intervention": "a1"}, {"reason": "h2", "first_intervention": "a2"}]
    plain = AL.build_loss_table(routes=routes, duration_overrides={"a1": 3.0, "a2": 3.0})
    again = AL.build_loss_table(routes=routes, duration_overrides={"a1": 3.0, "a2": 3.0}, unresolved_minutes=None)
    assert plain.table_hash == again.table_hash
    measured = AL.build_loss_table(
        routes=routes, duration_overrides={"a1": 3.0, "a2": 3.0},
        unresolved_minutes={"h1": {"minutes": 4.0, "provenance": "measured"}},
    )
    assert measured.table_hash != plain.table_hash
    assert measured.loss("h1", "a2") == pytest.approx(10.0)
    assert measured.loss("h2", "a1") == pytest.approx(6.0)
    assert measured.loss("h1", "a1") == 0.0
    AL.assert_derived(measured)


def _attempt(connection, attempt_id: str, created_at: str, latency: int | None) -> None:
    connection.execute(
        "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
        "latency_seconds, created_at) VALUES (?, 'pi_svd_define_001', ?, 'short_answer', 'independent_attempt', ?, ?)",
        (attempt_id, LO_ID, latency, created_at),
    )


def test_unresolved_cost_shrinks_the_eedi_prior_toward_personal_history(tmp_path):
    _vault_obj, repository = _vault(tmp_path)
    empty = UC.estimate_unresolved_cost(repository, pseudo_count=5.0)
    assert empty.provenance == "population_prior" and empty.personal_classes == 0
    assert empty.minutes_per_repeat_source == "heuristic_default"

    with repository.connection() as connection:
        for index, (when, latency) in enumerate([
            ("2026-01-01T10:00:00Z", 60), ("2026-01-05T10:00:00Z", 120), ("2026-01-09T10:00:00Z", 180),
        ]):
            _attempt(connection, f"att_rep_{index}", when, latency)
        _attempt(connection, "att_once", "2026-02-01T10:00:00Z", 60)
        _attempt(connection, "att_late", "2026-05-01T10:00:00Z", 60)
        connection.commit()
    common = {"learning_object_id": LO_ID, "status": "candidate", "clock": CLOCK}
    for index in range(3):  # one statement class recurring three times
        repository.append_causal_hypothesis(
            episode_key=f"rep:{index}", attempt_id=f"att_rep_{index}", cause_scope="learner_state",
            statement="Adds before multiplying.", statement_normalized="adds before multiplying", **common,
        )
    repository.append_causal_hypothesis(
        episode_key="once", attempt_id="att_once", cause_scope="learner_state",
        statement="Drops the sign.", statement_normalized="drops the sign", **common,
    )
    slip = repository.append_causal_hypothesis(
        episode_key="slip", attempt_id="att_late", cause_scope="transient_execution",
        statement="A typo.", statement_normalized="a typo", **common,
    )
    estimate = UC.estimate_unresolved_cost(repository, pseudo_count=2.0)
    assert estimate.provenance == "measured"
    assert estimate.personal_classes == 2  # the transient slip is not a persistent cause
    # Class one repeated twice (2 + 3 minutes); class two never repeated.
    assert estimate.personal_mean_minutes == pytest.approx(2.5)
    # Five timed attempts are too few to trust a wall-clock median.
    assert estimate.minutes_per_repeat_source == "heuristic_default"
    assert estimate.prior_weight == pytest.approx(0.5)
    assert estimate.minutes == pytest.approx(0.5 * estimate.prior_minutes + 0.5 * 2.5)
    with repository.connection() as connection:
        for index in range(UC.MIN_TIMED_ATTEMPTS):
            _attempt(connection, f"att_timed_{index}", "2026-03-01T10:00:00Z", 3600)  # an hour-long "attempt"
        connection.commit()
    timed = UC.estimate_unresolved_cost(repository, pseudo_count=2.0)
    assert timed.minutes_per_repeat_source == "pooled_attempt_latency"
    # A break is not repeated-error time: one attempt counts at most the cap.
    assert timed.minutes_per_repeat == pytest.approx(UC.LATENCY_CAP_MINUTES)
    per_hypothesis, _ = UC.unresolved_minutes_for_hypotheses(repository, [slip["id"]], pseudo_count=2.0)
    assert per_hypothesis[slip["id"]]["minutes"] == 0.0
    assert per_hypothesis[slip["id"]]["source"] == "not_a_persistent_cause"


def _bound_attempt(connection, attempt_id: str, item: str, created_at: str, candidate_id: str | None) -> None:
    connection.execute(
        "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
        "scheduler_candidate_id, created_at) VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, ?)",
        (attempt_id, item, LO_ID, candidate_id, created_at),
    )


def _queued_followup(connection, gate_attempt: str, item: str, created_at: str) -> dict:
    _bound_attempt(connection, gate_attempt, "pi_gate_source", created_at, None)
    connection.execute(
        "INSERT INTO attempt_surprise (attempt_id, observed_joint_bucket_json, triggered_actions_json, "
        "algorithm_version, created_at) VALUES (?, '{}', ?, 'test', ?)",
        (gate_attempt, json.dumps([f"intervention_followup:low_score:pi_gate_source",
                                   f"intervention_followup:queued:{item}"]), created_at),
    )
    return {"site": "followup_selection", "source_attempt_id": gate_attempt, "decision_ref": gate_attempt,
            "chosen_practice_item_id": item, "created_at": created_at}


def test_followup_outcome_joins_only_the_attempt_that_took_the_followup(tmp_path):
    # Review F6: the follow-up was taken only when the learner answered it through
    # the follow-up lane (the attempt's offer is a slate candidate the scheduler
    # inserted as an intervention follow-up) and this decision was the queued one
    # that attempt answered. An unbound or ordinary later attempt on the item is
    # not the follow-up, and two queued decisions never share one answer.
    _vault_obj, repository = _vault(tmp_path)
    slate = repository.record_scheduler_slate(
        [
            {"practice_item_id": "pi_fu_a", "priority": 2.0,
             "components": {"selected": 1.0, "intervention_followup": 1.0}},
            {"practice_item_id": "pi_fu_b", "priority": 1.0, "components": {"selected": 1.0}},
        ],
        session_id="s1", algorithm_version="test", clock=CLOCK,
    )
    with repository.connection() as connection:
        candidate = {
            row["practice_item_id"]: row["id"]
            for row in connection.execute(
                "SELECT id, practice_item_id FROM scheduler_slate_candidates WHERE slate_id = ?", (slate,))
        }
        stale = _queued_followup(connection, "att_gate_1", "pi_fu_a", "2026-05-19T12:00:00Z")
        unbound_target = _queued_followup(connection, "att_gate_0", "pi_fu_u", "2026-05-19T11:00:00Z")
        ordinary_target = _queued_followup(connection, "att_gate_b", "pi_fu_b", "2026-05-19T12:00:00Z")
        pending = _queued_followup(connection, "att_gate_c", "pi_fu_c", "2026-05-19T12:00:00Z")
        # Queued again (a newer decision) before anyone answered: the first is superseded.
        fresh = _queued_followup(connection, "att_gate_2", "pi_fu_a", "2026-05-19T13:00:00Z")
        _bound_attempt(connection, "att_unbound", "pi_fu_u", "2026-05-20T12:00:00Z", None)
        _bound_attempt(connection, "att_followup", "pi_fu_a", "2026-05-20T12:00:00Z", candidate["pi_fu_a"])
        _bound_attempt(connection, "att_ordinary", "pi_fu_b", "2026-05-20T12:00:00Z", candidate["pi_fu_b"])
        connection.commit()
        adapter = LR.LedgerOutcomeAdapter(connection)
        assert adapter.attempt_for(fresh) == ("att_followup", "taken")
        assert adapter.attempt_for(stale) == (None, "superseded")
        assert adapter.attempt_for(unbound_target) == (None, "unbound_attempt")
        assert adapter.attempt_for(ordinary_target) == (None, "not_taken")
        assert adapter.attempt_for(pending) == (None, "pending")


def test_untimed_recurrence_is_not_a_measured_zero(tmp_path):
    # Review F7 (decision-value invariant 7: missing observed time is not zero).
    # A misconception recurs, but none of its attempts was timed and there is no
    # pooled latency to impute from: its cost is unmeasurable, so it must neither
    # count as a measured 0 minutes nor shrink the prior toward 0.
    _vault_obj, repository = _vault(tmp_path)
    common = {"learning_object_id": LO_ID, "cause_scope": "learner_state", "status": "candidate", "clock": CLOCK}
    with repository.connection() as connection:
        for index, when in enumerate(["2026-01-01T10:00:00Z", "2026-01-05T10:00:00Z", "2026-01-09T10:00:00Z"]):
            _attempt(connection, f"att_untimed_{index}", when, None)
        connection.commit()
    for index in range(3):
        repository.append_causal_hypothesis(
            episode_key=f"untimed:{index}", attempt_id=f"att_untimed_{index}", statement="Drops the sign.",
            statement_normalized="drops the sign", **common,
        )
    estimate = UC.estimate_unresolved_cost(repository, pseudo_count=2.0)
    assert estimate.personal_classes == 0
    assert estimate.provenance == "population_prior"
    assert estimate.minutes == pytest.approx(estimate.prior_minutes)
    assert estimate.detail["unmeasurable_classes"] == 1
    assert estimate.detail["untimed_repeat_attempts"] == 2

    # Once another persistent class is timed, the untimed repeats are imputed
    # from the learner's own pooled latency, and the imputation is labelled.
    with repository.connection() as connection:
        _attempt(connection, "att_timed_a", "2026-02-01T10:00:00Z", 120)
        _attempt(connection, "att_timed_b", "2026-02-05T10:00:00Z", 120)
        connection.commit()
    for index, attempt_id in enumerate(("att_timed_a", "att_timed_b")):
        repository.append_causal_hypothesis(
            episode_key=f"timed:{index}", attempt_id=attempt_id, statement="Adds before multiplying.",
            statement_normalized="adds before multiplying", **common,
        )
    imputed = UC.estimate_unresolved_cost(repository, pseudo_count=2.0)
    assert imputed.personal_classes == 2 and imputed.provenance == "measured"
    assert imputed.detail["unmeasurable_classes"] == 0
    assert imputed.detail["imputed_classes"] == 1
    assert imputed.detail["imputation"] == "pooled_personal_median_latency"
    # Two imputed repeats at the pooled 2-minute median, one timed 2-minute repeat.
    assert imputed.personal_mean_minutes == pytest.approx((4.0 + 2.0) / 2)


def test_followup_outcome_maps_into_the_forecasts_alphabet(tmp_path):
    vault, repository = _vault(tmp_path)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "rubric_score, error_type, created_at) VALUES ('att_f', 'pi_svd_define_001', ?, 'short_answer', "
            "'independent_attempt', 0, 'conceptual_slip', '2026-05-20T12:00:00Z')",
            (LO_ID,),
        )
        connection.commit()
        forecast = {"site": "followup_selection", "forecast": {"emission_alphabet": ["low|", "low|conceptual_slip",
                                                                                     "high|"]}}
        assert LR.realized_emission(connection, vault, forecast, "att_f") == ("low|conceptual_slip", "realized")
        other = {"site": "followup_selection", "forecast": {"emission_alphabet": ["low|", "high|"]}}
        # An error the forecast did not model reads as the bucket's null-error outcome.
        assert LR.realized_emission(connection, vault, other, "att_f") == ("low|", "realized")
        assert LR.realized_emission(connection, vault, {"site": "staged_diagnostic_selection"}, "att_f")[1] == (
            "site_without_outcome_mapping"
        )


def test_a_later_teach_back_naming_the_same_cause_confirms_it(tmp_path):
    _vault_obj, repository = _vault(tmp_path)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts (id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "created_at) VALUES ('att_src', 'pi_svd_define_001', ?, 'short_answer', 'independent_attempt', "
            "'2026-05-19T12:00:00Z'), ('att_tb', 'pi_svd_define_001', ?, 'teach_back', 'teach_back', "
            "'2026-05-25T12:00:00Z')",
            (LO_ID, LO_ID),
        )
        connection.commit()
    common = {"learning_object_id": LO_ID, "cause_scope": "learner_state", "status": "candidate", "clock": CLOCK}
    source = repository.append_causal_hypothesis(
        episode_key="src", attempt_id="att_src", statement="Transposes the wrong factor.",
        statement_normalized="transposes the wrong factor", **common,
    )
    repository.append_causal_hypothesis(
        episode_key="tb", attempt_id="att_tb", statement="Transposes the wrong factor.",
        statement_normalized="transposes the wrong factor", **common,
    )
    forecast = {"created_at": "2026-05-20T00:00:00Z", "forecast": {"prior": {source["id"]: 0.6, "other": 0.4}}}
    with repository.connection() as connection:
        truth = LR.truth_for(connection, forecast)
    assert truth == {"confirmed": [source["id"]], "ruled_out": [], "sources": ["teach_back_recurrence"],
                     "repair_effect": []}
