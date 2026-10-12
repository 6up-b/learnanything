"""The six ``llm_probability`` harness arms: V1-V3 x {decider, llm} (field §7.2).

Each arm is a point predictor over probabilities prepared earlier and cached
outside the vault. It has no store, network or model access: ``predict``
looks up the cached answer for this prediction's position, a key computed
only from the outcome-free features and the rows the harness has already
handed to ``observe``. The current outcome cannot reach the key, and a
cache that does not match the replay's past fails closed (``KeyError``).

Every (variant, judge) is reported twice:

* **raw**: the model's probability, clipped to [0.001, 0.999] so log loss
  stays finite;
* **recalibrated** (``+recal``): one parameter, a logit-intercept shift
  ``delta`` fit by penalized maximum likelihood (prior N(0, 1)) on the arm's
  own past (raw prediction, outcome) pairs only. It is refit after each
  observation, so a prediction never sees its own outcome.

These arms are never active (G11): ``calibrated_uncertainty`` is False, they
are not in the predictor registry, and ``field.active_predictor`` accepts
only the incumbent.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict
from hashlib import sha256
import json
from math import exp, isfinite, log

import numpy as np

from learnloop.field.types import AttemptRow, FacetRow, ItemFeatures, SignalRow

VARIANTS = ("v1", "v2", "v3")
JUDGES = ("decider", "llm")
ARM_PREFIX = "llm_probability"
RECALIBRATION = "logit-intercept-map-prior-n01-v1"
CLIP = (0.001, 0.999)
_NEWTON_STEPS = 50


def arm_name(variant: str, judge: str, *, recalibrated: bool = False) -> str:
    if variant not in VARIANTS or judge not in JUDGES:
        raise ValueError(f"Unknown llm_probability arm {variant}/{judge}")
    return f"{ARM_PREFIX}/{variant}/{judge}" + ("+recal" if recalibrated else "")


def all_arm_names() -> tuple[str, ...]:
    return tuple(
        arm_name(variant, judge, recalibrated=recal)
        for judge in JUDGES for variant in VARIANTS for recal in (False, True)
    )


def parse_arm_selection(values: Iterable[str]) -> tuple[tuple[str, str], ...]:
    """``all``, ``v2``, ``decider``, ``v3/llm`` (repeatable) -> (variant, judge) pairs."""

    chosen: dict[tuple[str, str], None] = {}
    for raw in values:
        for value in (part.strip().lower() for part in raw.split(",")):
            if not value:
                continue
            if value == "all":
                pairs = [(v, j) for j in JUDGES for v in VARIANTS]
            elif value in VARIANTS:
                pairs = [(value, j) for j in JUDGES]
            elif value in JUDGES:
                pairs = [(v, value) for v in VARIANTS]
            elif "/" in value and tuple(value.split("/", 1)) in {(v, j) for v in VARIANTS for j in JUDGES}:
                variant, judge = value.split("/", 1)
                pairs = [(variant, judge)]
            else:
                raise ValueError(
                    f"Unknown probability arm {value!r}: use all, v1|v2|v3, decider|llm or v<n>/<judge>"
                )
            for pair in pairs:
                chosen.setdefault(pair, None)
    if not chosen:
        raise ValueError("Choose at least one probability arm")
    order = {(v, j): i for i, (v, j) in enumerate((v, j) for j in JUDGES for v in VARIANTS)}
    return tuple(sorted(chosen, key=order.__getitem__))


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def position_key(features: ItemFeatures, history: Sequence[tuple[str, float]]) -> str:
    """Where a prediction sits: outcome-free features plus the observed past."""

    if not isinstance(features, ItemFeatures):
        raise TypeError("Prediction requires outcome-free ItemFeatures")
    return _digest({"features": asdict(features), "history": [[a, o] for a, o in history]})


def clip(p: float) -> float:
    return max(CLIP[0], min(CLIP[1], p))


def _logit(p: float) -> float:
    return log(p / (1 - p))


def _sigmoid(x: float) -> float:
    x = max(-50.0, min(50.0, x))
    return 1 / (1 + exp(-x))


def fit_intercept(logits: Sequence[float], outcomes: Sequence[float]) -> float:
    """MAP intercept shift under a N(0, 1) prior, by Newton's method.

    The objective is strictly concave (the prior adds curvature 1), so the
    iteration converges from 0. Outcomes may be fractional rubric scores.
    """

    z = np.asarray(logits, dtype=np.float64)
    y = np.asarray(outcomes, dtype=np.float64)
    delta = 0.0
    for _ in range(_NEWTON_STEPS):
        p = 1.0 / (1.0 + np.exp(-np.clip(z + delta, -50.0, 50.0)))
        step = float((y - p).sum() - delta) / float(1.0 + (p * (1 - p)).sum())
        delta += step
        if abs(step) < 1e-12:
            break
    return delta


class CachedProbabilityArm:
    """A store-free point predictor over a prepared probability cache."""

    granularity = "attempt"
    calibrated_uncertainty = False

    def __init__(
        self, *, variant: str, judge: str, probabilities: Mapping[str, float], model: str,
        provenance: Mapping[str, object] | None = None, recalibrated: bool = False,
    ) -> None:
        self.name = arm_name(variant, judge, recalibrated=recalibrated)
        self.variant, self.judge, self.recalibrated = variant, judge, recalibrated
        self.model = model
        for key, value in probabilities.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Cached probability for {key} is not in [0, 1]")
        self._probabilities = dict(probabilities)
        self.version_hash = _digest({
            "arm": self.name, "model": model, "provenance": dict(provenance or {}),
            "recalibration": RECALIBRATION if recalibrated else "none", "clip": list(CLIP),
            "probabilities": sorted(self._probabilities.items()),
        })
        self._history: list[tuple[str, float]] = []
        self._logits: list[float] = []
        self._outcomes: list[float] = []
        self.intercept = 0.0

    def _raw(self, features: ItemFeatures) -> float:
        key = position_key(features, self._history)
        if key not in self._probabilities:
            raise KeyError(f"{self.name}: no prepared probability for this position; re-run preparation")
        return clip(float(self._probabilities[key]))

    def predict(self, features: ItemFeatures) -> float:
        p = self._raw(features)
        if not self.recalibrated:
            return p
        return clip(_sigmoid(_logit(p) + self.intercept))

    def observe(self, row) -> None:
        if isinstance(row, (SignalRow, FacetRow)) or not isinstance(row, AttemptRow):
            return
        # The harness observes exactly the rows it predicted. The raw value is
        # read from the still-past position, before the row joins the history.
        p = self._raw(row.features)
        self._history.append((row.attempt_id, row.outcome))
        if self.recalibrated:
            self._logits.append(_logit(p))
            self._outcomes.append(row.outcome)
            self.intercept = fit_intercept(self._logits, self._outcomes)


__all__ = [
    "ARM_PREFIX",
    "CLIP",
    "CachedProbabilityArm",
    "JUDGES",
    "RECALIBRATION",
    "VARIANTS",
    "all_arm_names",
    "arm_name",
    "clip",
    "fit_intercept",
    "parse_arm_selection",
    "position_key",
]
