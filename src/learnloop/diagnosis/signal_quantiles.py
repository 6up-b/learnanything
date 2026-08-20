"""Data-relative follow-up gate thresholds (Fable's-take item 1).

Absolute nats/severity constants are arbitrary in units and drift as the
underlying estimators change (tau_followup_nats already had to be re-tuned 6x
after the EKF migration). Redefining them as quantiles of THIS learner's own
logged signal distribution self-calibrates from ~30 data points: "fire on the
top 15% of my negative surprises" survives unit changes untouched.

Thresholds resolve per evaluation from the last ``quantile_window``
``attempt_surprise`` rows (a single indexed scan). The current attempt's own
row is excluded so the threshold is strictly historical (deterministic under
replay, never self-referential). Below ``quantile_min_samples`` observations
the absolute config constant applies (``source="absolute_fallback"``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.config import SchedulerFollowupConfig
from learnloop.db.repositories import Repository
from learnloop.numeric import empirical_quantile


@dataclass(frozen=True)
class ResolvedThreshold:
    name: str
    value: float  # the threshold actually enforced
    source: str  # "quantile" | "absolute_fallback" | "absolute"
    quantile: float | None  # e.g. 0.85 when source == "quantile"
    sample_size: int  # observations backing the quantile (0 for "absolute")
    absolute_fallback: float  # the config constant

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source,
            "quantile": self.quantile,
            "sample_size": self.sample_size,
            "absolute_fallback": self.absolute_fallback,
        }


def resolve_followup_thresholds(
    repository: Repository,
    config: SchedulerFollowupConfig,
    *,
    exclude_attempt_id: str | None = None,
) -> dict[str, ResolvedThreshold]:
    """Resolve every gate threshold, quantile-relative where configured.

    Quantile-relative: ``tau_followup_nats`` (over negative-direction Bayesian
    surprises) and ``tau_severe_error`` (over nonzero error severities from the
    persisted gate diagnostics). Stay absolute: ``tau_unfamiliar_intervention``
    (already a calibrated posterior probability), ``gamma_min`` (a grader
    property, not a learner property), and the integer failure counts.
    """

    surprise_samples: list[float] = []
    severity_samples: list[float] = []
    if config.threshold_mode == "quantile":
        rows = repository.recent_surprise_signals(
            limit=config.quantile_window, exclude_attempt_id=exclude_attempt_id
        )
        for row in rows:
            if row.get("surprise_direction") == "negative" and row.get("bayesian_surprise") is not None:
                surprise_samples.append(float(row["bayesian_surprise"]))
            gate = row.get("gate_diagnostics")
            if isinstance(gate, dict):
                severity = gate.get("max_error_severity")
                if isinstance(severity, (int, float)) and severity > 0.0:
                    severity_samples.append(float(severity))

    return {
        "tau_followup_nats": _resolve(
            "tau_followup_nats",
            samples=surprise_samples,
            quantile=config.tau_followup_quantile,
            absolute=config.tau_followup_nats,
            config=config,
        ),
        "tau_severe_error": _resolve(
            "tau_severe_error",
            samples=severity_samples,
            quantile=config.tau_severe_error_quantile,
            absolute=config.tau_severe_error,
            config=config,
        ),
        "tau_unfamiliar_intervention": _absolute(
            "tau_unfamiliar_intervention", config.tau_unfamiliar_intervention
        ),
        "gamma_min": _absolute("gamma_min", config.gamma_min),
        "tau_repeated_item_failures": _absolute(
            "tau_repeated_item_failures", float(config.tau_repeated_item_failures)
        ),
        "tau_repeated_facet_failures": _absolute(
            "tau_repeated_facet_failures", float(config.tau_repeated_facet_failures)
        ),
    }


def _resolve(
    name: str,
    *,
    samples: list[float],
    quantile: float,
    absolute: float,
    config: SchedulerFollowupConfig,
) -> ResolvedThreshold:
    if config.threshold_mode != "quantile":
        return _absolute(name, absolute)
    if len(samples) < config.quantile_min_samples:
        return ResolvedThreshold(
            name=name,
            value=absolute,
            source="absolute_fallback",
            quantile=quantile,
            sample_size=len(samples),
            absolute_fallback=absolute,
        )
    value = max(empirical_quantile(samples, quantile), 1e-6)
    return ResolvedThreshold(
        name=name,
        value=value,
        source="quantile",
        quantile=quantile,
        sample_size=len(samples),
        absolute_fallback=absolute,
    )


def _absolute(name: str, value: float) -> ResolvedThreshold:
    return ResolvedThreshold(
        name=name,
        value=value,
        source="absolute",
        quantile=None,
        sample_size=0,
        absolute_fallback=value,
    )
