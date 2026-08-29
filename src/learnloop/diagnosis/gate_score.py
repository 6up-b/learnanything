"""Continuous follow-up gate score (Fable's-take items 2 + 7).

The trigger/suppression cascade collapses seven continuous signals into
booleans before any log line is written, so near-misses ("scored 0.48 against
a 0.5 gate") are invisible to fitting. Here each signal becomes a subscore in
[0, 1] (a steep sigmoid of its margin over the *resolved* threshold), combined
through one logistic:

    gate_score = sigmoid(bias + sum_i w_i * s_i)   vs   gate_score_threshold

Default weights reproduce the cascade's truth table at threshold 0.5 (module
constant table below). With steep subscores each s_i is ~a step function, so:

    one trigger + error event + confident grader: sigmoid(-11+6+3+3) ~ 0.73  -> fires
    one trigger, low grader confidence:           sigmoid(-11+6+3)   ~ 0.12  -> holds
    one trigger, no error event:                  sigmoid(-11+6+3)   ~ 0.12  -> holds
    no triggers:                                  sigmoid(-11+..6)   ~ 0.01  -> holds
    two triggers overcome one missing suppressor: sigmoid(-11+6+6+3) ~ 0.98  -> fires

The last row is an intentional, documented deviation from the cascade — the
"soft gate" gradient the redesign wants. The cascade's unfamiliar-posterior
exemption from the no-error-event rule is preserved by defining the
error-event feature as max(error_event, unfamiliar_subscore).

Hard budget gates (no_time, session_cap_reached) are NOT features: they are
pacing constraints, not learner evidence — a fitted weight must never be able
to buy time that does not exist. They short-circuit in both gate modes.

Weights live in the fitted-parameters store (scope "followup_gate") or fall
back to the defaults here; they are deliberately not in TOML so fitted values
have a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.numeric import sigmoid
from learnloop.diagnosis.signal_quantiles import ResolvedThreshold

GATE_FEATURES: tuple[str, ...] = (
    "negative_surprise",
    "severe_error",
    "repeated_item_failure",
    "repeated_facet_failure",
    "unfamiliar_posterior",
    "error_event_written",
    "grader_confidence_ok",
)

# Version the *meaning* of the feature vector, not merely its shape. Version 2
# changes the repeated-failure inputs from windowed historical counts to
# trailing failure streaks. Old fitted weights and training rows therefore
# cannot be mixed safely with current evaluations even though the feature names
# are unchanged.
GATE_FEATURE_VERSION: int = 2

# Which trigger-family feature maps to which cascade reason string (the reason
# vocabulary downstream intent selection / action tags already understand).
TRIGGER_FEATURE_REASONS: dict[str, str] = {
    "negative_surprise": "negative_surprise",
    "severe_error": "severe_error_event",
    "repeated_item_failure": "repeated_same_item_failure",
    "repeated_facet_failure": "repeated_same_facet_failure",
    "unfamiliar_posterior": "high_unfamiliar_posterior",
}

DEFAULT_GATE_WEIGHTS: dict[str, float] = {
    "negative_surprise": 6.0,
    "severe_error": 6.0,
    "repeated_item_failure": 6.0,
    "repeated_facet_failure": 6.0,
    "unfamiliar_posterior": 6.0,
    "error_event_written": 3.0,
    "grader_confidence_ok": 3.0,
}
DEFAULT_GATE_BIAS: float = -11.0


@dataclass(frozen=True)
class GateSignalValues:
    """Raw gate inputs, bundled once so cascade and score modes read the same values."""

    surprise_direction: str
    bayesian_surprise: float
    max_error_severity: float
    item_failure_count: float
    facet_failure_count: float
    probe_unfamiliar_probability: float | None
    error_event_written: bool
    grader_confidence: float | None
    deterministic_dont_know: bool


@dataclass(frozen=True)
class GateSubscore:
    name: str
    raw_value: float | None
    threshold: ResolvedThreshold | None
    subscore: float  # in [0, 1]
    weight: float
    contribution: float  # weight * subscore

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "raw_value": self.raw_value,
            "subscore": self.subscore,
            "weight": self.weight,
            "contribution": self.contribution,
        }
        if self.threshold is not None:
            payload["threshold"] = self.threshold.value
            payload["threshold_source"] = self.threshold.source
            payload["threshold_quantile"] = self.threshold.quantile
            payload["threshold_sample_size"] = self.threshold.sample_size
        return payload


@dataclass(frozen=True)
class GateScoreResult:
    score: float  # in [0, 1]
    threshold: float  # gate_score_threshold
    fired: bool
    subscores: tuple[GateSubscore, ...]
    bias: float
    weights_provenance: str  # "default" | "fitted:<params_id>"

    def subscore(self, name: str) -> GateSubscore:
        for entry in self.subscores:
            if entry.name == name:
                return entry
        raise KeyError(name)

    def triggered_reasons(self) -> list[str]:
        """Cascade-vocabulary reasons for trigger features scoring >= 0.5."""

        return [
            TRIGGER_FEATURE_REASONS[entry.name]
            for entry in self.subscores
            if entry.name in TRIGGER_FEATURE_REASONS and entry.subscore >= 0.5
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate_score": self.score,
            "gate_score_threshold": self.threshold,
            "gate_bias": self.bias,
            "weights_provenance": self.weights_provenance,
            "subscores": {entry.name: entry.as_dict() for entry in self.subscores},
        }


def compute_gate_score(
    *,
    signals: GateSignalValues,
    thresholds: dict[str, ResolvedThreshold],
    weights: dict[str, float],
    bias: float,
    gate_score_threshold: float,
    steepness: float,
    weights_provenance: str,
) -> GateScoreResult:
    subscores = _subscores(signals, thresholds, steepness)
    entries: list[GateSubscore] = []
    activation = bias
    for name in GATE_FEATURES:
        weight = float(weights.get(name, DEFAULT_GATE_WEIGHTS[name]))
        value, raw, threshold = subscores[name]
        contribution = weight * value
        activation += contribution
        entries.append(
            GateSubscore(
                name=name,
                raw_value=raw,
                threshold=threshold,
                subscore=value,
                weight=weight,
                contribution=contribution,
            )
        )
    score = sigmoid(activation)
    return GateScoreResult(
        score=score,
        threshold=gate_score_threshold,
        fired=score >= gate_score_threshold,
        subscores=tuple(entries),
        bias=bias,
        weights_provenance=weights_provenance,
    )


def resolve_gate_weights(repository: Repository) -> tuple[dict[str, float], float, str]:
    """Fitted logistic weights from the fitted-parameters store, else defaults.

    Fitted payload shape: {"weights": {feature: float, ...}, "bias": float}.
    Any malformed payload falls back to defaults rather than crashing the gate.
    """

    from learnloop.params.fitted_params import FOLLOWUP_GATE_SCOPE

    record = repository.active_fitted_parameters(FOLLOWUP_GATE_SCOPE)
    if record is None:
        return dict(DEFAULT_GATE_WEIGHTS), DEFAULT_GATE_BIAS, "default"
    params = record.get("params", {})
    if params.get("feature_version") != GATE_FEATURE_VERSION:
        return dict(DEFAULT_GATE_WEIGHTS), DEFAULT_GATE_BIAS, "default"
    raw_weights = params.get("weights")
    raw_bias = params.get("bias")
    if not isinstance(raw_weights, dict) or not isinstance(raw_bias, (int, float)) or isinstance(raw_bias, bool):
        return dict(DEFAULT_GATE_WEIGHTS), DEFAULT_GATE_BIAS, "default"
    weights: dict[str, float] = {}
    for name in GATE_FEATURES:
        value = raw_weights.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return dict(DEFAULT_GATE_WEIGHTS), DEFAULT_GATE_BIAS, "default"
        weights[name] = float(value)
    return weights, float(raw_bias), f"fitted:{record['id']}"


def subscores_from_diagnostics(gate: dict[str, Any], config: Any) -> dict[str, float] | None:
    """Reconstruct the seven subscores from a persisted gate_diagnostics dict.

    Score-mode rows carry them directly; cascade-era rows (migration 015+) are
    reconstructed from the logged raw values so the gate fitter can train on
    history recorded before score mode existed. Returns None when the row is
    missing too much to reconstruct.
    """

    persisted = gate.get("subscores")
    if isinstance(persisted, dict):
        values: dict[str, float] = {}
        for name in GATE_FEATURES:
            entry = persisted.get(name)
            if not isinstance(entry, dict) or not isinstance(entry.get("subscore"), (int, float)):
                return None
            values[name] = float(entry["subscore"])
        return values

    if "bayesian_surprise" not in gate:
        return None
    reasons = gate.get("natural_trigger_reasons")
    if not isinstance(reasons, list):
        return None
    would_suppress = gate.get("would_suppress") or []
    decisive = gate.get("decisive_signal") or {}
    tau = gate.get("tau_followup_nats", config.tau_followup_nats)

    def _step(condition: bool) -> float:
        return 1.0 if condition else 0.0

    surprise = float(gate.get("bayesian_surprise") or 0.0)
    negative = gate.get("surprise_direction") == "negative"
    severity = float(gate.get("max_error_severity") or 0.0)
    confidence = gate.get("grader_confidence")
    unfamiliar = _step("high_unfamiliar_posterior" in reasons)
    if decisive.get("name") == "unfamiliar_posterior" and isinstance(decisive.get("value"), (int, float)):
        unfamiliar = float(decisive["value"] >= float(decisive.get("threshold") or 1.0))
    error_event = _step("no_error_event" not in would_suppress and gate.get("decisive_reason") != "no_error_event")
    return {
        "negative_surprise": _step(negative and surprise > float(tau or 0.0)),
        "severe_error": _step(severity >= config.tau_severe_error),
        "repeated_item_failure": _step("repeated_same_item_failure" in reasons),
        "repeated_facet_failure": _step("repeated_same_facet_failure" in reasons),
        "unfamiliar_posterior": unfamiliar,
        "error_event_written": max(error_event, unfamiliar),
        "grader_confidence_ok": _step(
            isinstance(confidence, (int, float)) and float(confidence) >= config.gamma_min
        )
        if "low_grader_confidence" not in would_suppress and gate.get("decisive_reason") != "low_grader_confidence"
        else 0.0,
    }


def _subscores(
    signals: GateSignalValues,
    thresholds: dict[str, ResolvedThreshold],
    steepness: float,
) -> dict[str, tuple[float, float | None, ResolvedThreshold | None]]:
    """name -> (subscore, raw_value, threshold used)."""

    tau_surprise = thresholds["tau_followup_nats"]
    tau_severity = thresholds["tau_severe_error"]
    tau_unfamiliar = thresholds["tau_unfamiliar_intervention"]
    gamma_min = thresholds["gamma_min"]
    tau_item = thresholds["tau_repeated_item_failures"]
    tau_facet = thresholds["tau_repeated_facet_failures"]

    negative_surprise = (
        _margin_subscore(signals.bayesian_surprise, tau_surprise.value, steepness)
        if signals.surprise_direction == "negative"
        else 0.0
    )
    severe_error = _margin_subscore(signals.max_error_severity, tau_severity.value, steepness, bounded=True)
    repeated_item = sigmoid(steepness * (signals.item_failure_count - tau_item.value + 0.5))
    repeated_facet = sigmoid(steepness * (signals.facet_failure_count - tau_facet.value + 0.5))
    unfamiliar = (
        _margin_subscore(signals.probe_unfamiliar_probability, tau_unfamiliar.value, steepness, bounded=True)
        if signals.probe_unfamiliar_probability is not None
        else 0.0
    )
    # The cascade exempts a high unfamiliar posterior from the no-error-event
    # suppression; encoded as part of the feature rather than a hard branch.
    error_event = max(1.0 if signals.error_event_written else 0.0, unfamiliar)
    if signals.deterministic_dont_know:
        confidence_ok = 1.0
    elif signals.grader_confidence is None:
        confidence_ok = 0.0
    else:
        confidence_ok = _margin_subscore(signals.grader_confidence, gamma_min.value, steepness, bounded=True)

    return {
        "negative_surprise": (negative_surprise, signals.bayesian_surprise, tau_surprise),
        "severe_error": (severe_error, signals.max_error_severity, tau_severity),
        "repeated_item_failure": (repeated_item, signals.item_failure_count, tau_item),
        "repeated_facet_failure": (repeated_facet, signals.facet_failure_count, tau_facet),
        "unfamiliar_posterior": (unfamiliar, signals.probe_unfamiliar_probability, tau_unfamiliar),
        "error_event_written": (error_event, 1.0 if signals.error_event_written else 0.0, None),
        "grader_confidence_ok": (confidence_ok, signals.grader_confidence, gamma_min),
    }


def _margin_subscore(value: float, threshold: float, steepness: float, *, bounded: bool = False) -> float:
    """Steep sigmoid of the margin over the threshold, normalized by its scale.

    For signals bounded in [0, 1] (probabilities, severities) the achievable
    margin above a high threshold is capped at 1 - threshold, so the scale is
    min(threshold, 1 - threshold) — otherwise a 0.95 posterior against tau 0.85
    would read as a weak signal when it is nearly the strongest possible one.
    """

    if bounded:
        scale = max(min(abs(threshold), 1.0 - threshold), 1e-6)
    else:
        scale = max(abs(threshold), 1e-6)
    return sigmoid(steepness * (value - threshold) / scale)
