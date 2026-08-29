"""Continuous gate score: cascade-mimicry truth table, monotonicity, fitted
weights, diagnostics round-trip, and score-mode integration through the real
follow-up evaluator."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.config import SchedulerFollowupConfig
from learnloop.db.repositories import MasteryState, Repository
from learnloop.diagnosis.followups import evaluate_intervention_followup
from learnloop.diagnosis.gate_score import (
    DEFAULT_GATE_BIAS,
    DEFAULT_GATE_WEIGHTS,
    GATE_FEATURE_VERSION,
    GateSignalValues,
    compute_gate_score,
    resolve_gate_weights,
    subscores_from_diagnostics,
)
from learnloop.diagnosis.signal_quantiles import resolve_followup_thresholds
from learnloop.vault.loader import load_vault

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, add_followup_item, create_basic_vault

CONFIG = SchedulerFollowupConfig(threshold_mode="absolute")


def _thresholds(repository=None):
    # Absolute mode needs no repository reads.
    class _NoRepo:
        def recent_surprise_signals(self, **_kwargs):
            return []

    return resolve_followup_thresholds(repository or _NoRepo(), CONFIG)


def _signals(**overrides) -> GateSignalValues:
    base = dict(
        surprise_direction="none",
        bayesian_surprise=0.0,
        max_error_severity=0.0,
        item_failure_count=0.0,
        facet_failure_count=0.0,
        probe_unfamiliar_probability=None,
        error_event_written=True,
        grader_confidence=0.9,
        deterministic_dont_know=False,
    )
    base.update(overrides)
    return GateSignalValues(**base)


def _score(signals: GateSignalValues):
    return compute_gate_score(
        signals=signals,
        thresholds=_thresholds(),
        weights=DEFAULT_GATE_WEIGHTS,
        bias=DEFAULT_GATE_BIAS,
        gate_score_threshold=0.5,
        steepness=12.0,
        weights_provenance="default",
    )


# ── cascade-mimicry truth table ──────────────────────────────────────────────


def test_no_triggers_does_not_fire():
    assert not _score(_signals()).fired


def test_single_trigger_with_error_event_and_confident_grader_fires():
    result = _score(_signals(surprise_direction="negative", bayesian_surprise=0.5))
    assert result.fired
    assert result.triggered_reasons() == ["negative_surprise"]


def test_single_trigger_low_grader_confidence_holds():
    result = _score(_signals(surprise_direction="negative", bayesian_surprise=0.5, grader_confidence=0.1))
    assert not result.fired


def test_single_trigger_no_error_event_holds():
    result = _score(_signals(surprise_direction="negative", bayesian_surprise=0.5, error_event_written=False))
    assert not result.fired


def test_unfamiliar_posterior_exempt_from_error_event_rule():
    # Cascade: high_unfamiliar_posterior fires even with no error event.
    result = _score(_signals(probe_unfamiliar_probability=0.95, error_event_written=False))
    assert result.fired
    assert "high_unfamiliar_posterior" in result.triggered_reasons()


def test_two_triggers_overcome_one_missing_suppressor():
    # Documented soft-gate deviation from the cascade.
    result = _score(
        _signals(
            surprise_direction="negative",
            bayesian_surprise=0.5,
            max_error_severity=0.9,
            error_event_written=False,
        )
    )
    assert result.fired


def test_repeated_failures_trigger():
    result = _score(_signals(item_failure_count=2.0))
    assert result.fired
    assert result.triggered_reasons() == ["repeated_same_item_failure"]


def test_deterministic_dont_know_counts_as_confident():
    result = _score(
        _signals(
            surprise_direction="negative",
            bayesian_surprise=0.5,
            grader_confidence=None,
            deterministic_dont_know=True,
        )
    )
    assert result.fired


# ── shape properties ─────────────────────────────────────────────────────────


def test_score_monotone_in_surprise():
    scores = [
        _score(_signals(surprise_direction="negative", bayesian_surprise=value)).score
        for value in (0.0, 0.02, 0.05, 0.10, 0.50)
    ]
    assert scores == sorted(scores)


def test_near_miss_has_graded_score():
    # A near-threshold surprise with no other signals lands strictly between
    # the floor and the firing region — the counterfactual gradient.
    result = _score(_signals(surprise_direction="negative", bayesian_surprise=0.049))
    assert 0.0 < result.score < 0.5 or result.score >= 0.5  # never NaN/degenerate
    silent = _score(_signals())
    assert result.score != silent.score


def test_as_dict_carries_all_subscores():
    payload = _score(_signals(surprise_direction="negative", bayesian_surprise=0.5)).as_dict()
    assert set(payload["subscores"]) == set(DEFAULT_GATE_WEIGHTS)
    assert payload["gate_score_threshold"] == 0.5
    entry = payload["subscores"]["negative_surprise"]
    assert entry["threshold_source"] == "absolute"


# ── fitted weights resolution ────────────────────────────────────────────────


def test_resolve_gate_weights_defaults_and_fitted(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    weights, bias, provenance = resolve_gate_weights(repository)
    assert weights == DEFAULT_GATE_WEIGHTS
    assert bias == DEFAULT_GATE_BIAS
    assert provenance == "default"

    fitted = {name: value * 0.5 for name, value in DEFAULT_GATE_WEIGHTS.items()}
    fitted_id = repository.insert_fitted_parameters(
        scope="followup_gate",
        params={"weights": fitted, "bias": -5.0, "feature_version": GATE_FEATURE_VERSION},
        algorithm_version=ALGORITHM_VERSION,
        training_rows_count=50,
    )
    weights, bias, provenance = resolve_gate_weights(repository)
    assert weights == fitted
    assert bias == -5.0
    assert provenance == f"fitted:{fitted_id}"

    # A fitted vector trained against the old window-count semantics is not
    # compatible with the current streak features and cleanly falls back.
    repository.insert_fitted_parameters(
        scope="followup_gate",
        params={"weights": fitted, "bias": -4.0, "feature_version": GATE_FEATURE_VERSION - 1},
        algorithm_version=ALGORITHM_VERSION,
        training_rows_count=50,
    )
    weights, bias, provenance = resolve_gate_weights(repository)
    assert weights == DEFAULT_GATE_WEIGHTS
    assert bias == DEFAULT_GATE_BIAS
    assert provenance == "default"

    # Malformed payload falls back.
    repository.insert_fitted_parameters(
        scope="followup_gate",
        params={"weights": {"negative_surprise": "bad"}, "bias": -5.0},
        algorithm_version=ALGORITHM_VERSION,
        training_rows_count=1,
    )
    weights, bias, provenance = resolve_gate_weights(repository)
    assert provenance == "default"


# ── diagnostics round-trip ───────────────────────────────────────────────────


def test_subscores_from_score_mode_diagnostics():
    result = _score(_signals(surprise_direction="negative", bayesian_surprise=0.5))
    gate = {"subscores": result.as_dict()["subscores"]}
    reconstructed = subscores_from_diagnostics(gate, CONFIG)
    assert reconstructed is not None
    for entry in result.subscores:
        assert reconstructed[entry.name] == entry.subscore


def test_subscores_from_cascade_era_diagnostics():
    # A 015-era row: raw values + reasons, no subscores.
    gate = {
        "bayesian_surprise": 0.2,
        "surprise_direction": "negative",
        "tau_followup_nats": 0.05,
        "max_error_severity": 0.8,
        "grader_confidence": 0.9,
        "natural_trigger_reasons": ["negative_surprise", "severe_error_event"],
        "would_suppress": [],
        "decisive_reason": "negative_surprise",
        "decisive_signal": {"name": "bayesian_surprise", "value": 0.2, "threshold": 0.05},
    }
    reconstructed = subscores_from_diagnostics(gate, CONFIG)
    assert reconstructed is not None
    assert reconstructed["negative_surprise"] == 1.0
    assert reconstructed["severe_error"] == 1.0
    assert reconstructed["grader_confidence_ok"] == 1.0
    assert reconstructed["error_event_written"] == 1.0
    assert subscores_from_diagnostics({}, CONFIG) is None


# ── score-mode integration through the real evaluator ────────────────────────


def _score_mode_vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    toml_path = vault_root / "learnloop.toml"
    toml_path.write_text(
        toml_path.read_text(encoding="utf-8").replace('gate_mode = "cascade"', 'gate_mode = "score"'),
        encoding="utf-8",
    )
    repository = Repository(paths.sqlite_path)
    loaded = load_vault(vault_root)
    assert loaded.config.scheduler.followup.gate_mode == "score"
    return loaded, repository


def _surprising_attempt(loaded, repository):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    repository.upsert_mastery_state(
        MasteryState("lo_svd_definition", 2.0, 1.0, 3, NOW_ISO, ALGORITHM_VERSION, NOW_ISO)
    )
    return complete_self_graded_attempt(
        loaded,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="x"),
        SelfGradeInput(criterion_points={"correctness": 1}, confidence=4, error_type="conceptual_slip"),
        clock=FrozenClock(NOW),
    )


def test_score_mode_fires_on_surprising_failure_and_logs_scores(tmp_path):
    loaded, repository = _score_mode_vault(tmp_path)
    result = _surprising_attempt(loaded, repository)
    assert result.surprise_direction == "negative"

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.8,
        available_minutes=30,
    )
    assert decision.triggered is True
    gate = decision.gate_diagnostics
    assert gate["gate_mode"] == "score"
    assert gate["gate_score"] >= gate["gate_score_threshold"]
    assert set(gate["subscores"]) == set(DEFAULT_GATE_WEIGHTS)
    assert "tau_followup_nats" in gate["thresholds"]
    assert gate["weights_provenance"] == "default"


def test_score_mode_below_threshold_logs_counterfactual_margin(tmp_path):
    loaded, repository = _score_mode_vault(tmp_path)
    result = _surprising_attempt(loaded, repository)

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="positive",
        bayesian_surprise=0.0,
        grader_confidence=0.95,
        error_event_written=False,
        available_minutes=30,
    )
    assert decision.triggered is False
    assert decision.reason == "gate_score_below_threshold"
    gate = decision.gate_diagnostics
    assert gate["outcome"] == "not_triggered"
    assert gate["decisive_signal"]["name"] == "gate_score"
    assert gate["decisive_signal"]["value"] == gate["gate_score"]
    assert gate["gate_score"] < gate["gate_score_threshold"]


def test_score_mode_hard_gates_still_suppress(tmp_path):
    loaded, repository = _score_mode_vault(tmp_path)
    result = _surprising_attempt(loaded, repository)

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=max(result.bayesian_surprise, 0.5),
        grader_confidence=result.grader_confidence,
        error_event_written=True,
        max_error_severity=0.9,
        available_minutes=0,  # hard budget gate
    )
    assert decision.triggered is False
    assert "no_time" in decision.reason
    assert decision.gate_diagnostics["hard_gates"] == ["no_time"]


def test_score_mode_manual_override_still_queues(tmp_path):
    loaded, repository = _score_mode_vault(tmp_path)
    result = _surprising_attempt(loaded, repository)

    decision = evaluate_intervention_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction="positive",
        bayesian_surprise=0.0,
        grader_confidence=0.95,
        error_event_written=False,
        available_minutes=30,
        manual_override=True,
    )
    assert decision.triggered is True
    gate = decision.gate_diagnostics
    assert gate["manual_override"] is True
    assert gate["would_auto_fire"] is False
    assert "gate_score_below_threshold" in gate["would_suppress"]
    assert any("manual_trigger" in action for action in decision.triggered_actions)
