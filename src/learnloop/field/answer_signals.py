"""Offline answer-signal arms for the learner field's predictor duel.

Owner decision 2026-10-13 ("I agree with an offline predictor arm for
confidence"): the learner's own pre-answer signals are scored as arms in the
prequential replay (``learnloop eval --section field``) and nowhere else. They
never feed serving, mastery, certification or FSRS, so there is no successor:
``calibrated_uncertainty`` is False (G11 keeps them out of
``field.active_predictor``) and no serving module imports this one.

Arms (each predicts from :class:`~learnloop.field.types.AnswerSignals`, which
only arms with ``uses_answer_signals`` receive, and abstains where its signal
is absent, so paired comparisons use the common attempts):

* ``answer_confidence`` - (a) confidence alone: the pre-answer tap (1-5),
  through the duel's mapping (1->.1 ... 5->.9) and a two-parameter logistic
  recalibration ``logit p = a + b * logit(map(c))`` fit on the arm's own past.
  The prior (a ~ N(0, 1), b ~ N(1, 1)) starts it at the duel's mapping.
* ``answer_hedging`` - (c) hedging read from the learner's own answer text
  where the grader already reads it: the share of criteria the grader read as
  ``hedged`` (``grading_evidence.learner_confidence``), as
  ``logit p = a + b * (2h - 1)`` with neutral N(0, 1) priors. The reading
  comes from the call that grades the answer, so it shares that call; reports
  say so.
* ``<base>+answer_confidence`` and ``<base>+answer_hedging`` - (b) an existing
  arm plus the signal: ``logit p = logit(p_base) + a + b * x`` with N(0, 1)
  priors, so it starts exactly at the base arm. The base arm observes every row
  the harness hands it, as it would alone. Registered for the incumbent
  (``mastery_ekf``) and the best exploratory arm on the owner's vault so far
  (``lo_general+composite``, docs/reviews/slice-a-integration-2-3.md); any
  attempt-level registered arm can be stacked with :func:`stacked_arm`.

Every fit is maximum a posteriori by Newton's method on the arm's own past
(prediction, outcome) pairs only, refit after each observation, so a
prediction never sees its own outcome. Outcomes may be fractional rubric
scores.
"""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
import json
from math import exp, isfinite, log

from learnloop.field.predictors import (
    _EKF_INPUTS, _order, create_predictor, register_predictor, registered_predictors,
)
from learnloop.field.types import (
    ANSWER_CONFIDENCE_PROBABILITY, AnswerSignals, AttemptRow, FacetRow, ItemFeatures, SignalRow,
)

CONFIDENCE = "confidence"
HEDGING = "hedging"
SIGNALS = (CONFIDENCE, HEDGING)
ARM_NAMES = {CONFIDENCE: "answer_confidence", HEDGING: "answer_hedging"}
#: Bases the default registry stacks each signal on: the incumbent and the best
#: exploratory arm so far. ``stacked_arm`` stacks any attempt-level arm.
DEFAULT_STACK_BASES = ("mastery_ekf", "lo_general+composite")
FIT = "logistic-map-newton-v1"
CLIP = (1e-4, 1 - 1e-4)
_NEWTON_STEPS = 60
#: What each arm's report row must say about where its signal comes from.
SIGNAL_SOURCES = {
    CONFIDENCE: "learner's pre-answer tap (1-5), taken after composing and before submit",
    HEDGING: "grader-read tone of the learner's answer text (same call as the grade)",
}


def stacked_name(base: str, signal: str) -> str:
    return f"{base}+{ARM_NAMES[signal]}"


def _logit(p: float) -> float:
    p = min(max(p, CLIP[0]), CLIP[1])
    return log(p / (1 - p))


def _sigmoid(x: float) -> float:
    x = max(-50.0, min(50.0, x))
    return 1 / (1 + exp(-x))


def signal_feature(signal: str, signals: AnswerSignals | None) -> float | None:
    """The arm's covariate, or None where the learner gave no such signal."""

    if signals is None:
        return None
    if signal == CONFIDENCE:
        if signals.confidence is None:
            return None
        return _logit(ANSWER_CONFIDENCE_PROBABILITY[signals.confidence])
    if signal == HEDGING:
        if signals.hedged_share is None:
            return None
        return 2.0 * signals.hedged_share - 1.0
    raise ValueError(f"unknown answer signal: {signal}")


def fit_logistic(
    features: list[float], offsets: list[float], outcomes: list[float],
    *, prior_mean: tuple[float, float], prior_variance: float = 1.0,
) -> tuple[float, float]:
    """MAP ``(a, b)`` of ``logit p = offset + a + b * x`` under N(prior, v) priors.

    The objective is strictly concave (the priors add curvature), so Newton's
    method converges from the prior mean. Outcomes may be fractional.
    """

    a, b = prior_mean
    precision = 1.0 / prior_variance
    for _ in range(_NEWTON_STEPS):
        ga = -(a - prior_mean[0]) * precision
        gb = -(b - prior_mean[1]) * precision
        haa = hbb = precision
        hab = 0.0
        for x, offset, y in zip(features, offsets, outcomes):
            p = _sigmoid(offset + a + b * x)
            residual, weight = y - p, p * (1 - p)
            ga += residual
            gb += residual * x
            haa += weight
            hab += weight * x
            hbb += weight * x * x
        determinant = haa * hbb - hab * hab
        step_a = (hbb * ga - hab * gb) / determinant
        step_b = (haa * gb - hab * ga) / determinant
        a, b = a + step_a, b + step_b
        if abs(step_a) < 1e-12 and abs(step_b) < 1e-12:
            break
    return a, b


def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _ability_row(row) -> bool:
    """The rows the harness scores ability arms on (``evaluation._eligible``)."""

    if row.revision_status == "excluded" or row.outcome is None or not isfinite(row.outcome):
        return False
    replacement = row.mass_without_assistance
    return (
        isfinite(row.effective_mass) and row.effective_mass > 0
        or bool(row.hints_used or row.help_before_work)
        and replacement is not None and isfinite(replacement) and replacement > 0
    )


class AnswerSignalArm:
    """A point predictor over one answer signal, optionally on a base arm."""

    granularity = "attempt"
    calibrated_uncertainty = False
    uses_answer_signals = True

    def __init__(self, *, signal: str, base_name: str | None = None, **base_inputs) -> None:
        if signal not in SIGNALS:
            raise ValueError(f"unknown answer signal: {signal}")
        self.signal = signal
        self.base_name = base_name
        self._base_inputs = dict(base_inputs)
        self.base = self._make_base()
        if self.base is not None and getattr(self.base, "granularity", "attempt") != "attempt":
            raise ValueError("answer-signal arms stack only on attempt-level arms")
        if self.base is not None and getattr(self.base, "uses_answer_signals", False):
            raise ValueError("answer-signal arms do not stack on each other")
        self.name = stacked_name(base_name, signal) if base_name else ARM_NAMES[signal]
        # The confidence-alone arm starts at the duel's own mapping; every other
        # arm starts neutral (hedging alone at 1/2, a stack at its base).
        self.prior_mean = (0.0, 1.0) if signal == CONFIDENCE and base_name is None else (0.0, 0.0)
        self.model = getattr(self.base, "model", "not_used") if self.base is not None else "not_used"
        self.signal_source = SIGNAL_SOURCES[signal]
        # Mirrors so the shared registry contract reads the base's behaviour.
        self.extensions = frozenset(getattr(self.base, "extensions", ()) or ())
        self.constants = getattr(self.base, "constants", None)
        self.version_hash = _hash({
            "implementation": "answer-signal-arm-v1", "signal": self.signal, "fit": FIT,
            "prior_mean": list(self.prior_mean), "prior_variance": 1.0,
            "mapping": {str(k): v for k, v in ANSWER_CONFIDENCE_PROBABILITY.items()},
            "base": getattr(self.base, "version_hash", None),
        })
        self._reset_fit()

    def _make_base(self):
        if self.base_name is None:
            return None
        return create_predictor(self.base_name, **self._base_inputs)

    def _reset_fit(self) -> None:
        self._features: list[float] = []
        self._offsets: list[float] = []
        self._outcomes: list[float] = []
        self.coefficients = self.prior_mean

    def covers_answer(self, signals: AnswerSignals | None) -> bool:
        return signal_feature(self.signal, signals) is not None

    def _offset(self, features: ItemFeatures) -> float:
        return _logit(self.base.predict(features)) if self.base is not None else 0.0

    def predict(self, features: ItemFeatures) -> float:
        """Without an answer signal: the base arm's prediction (1/2 alone).

        The harness never scores this: it calls :meth:`predict_answer` and
        abstains where the signal is absent.
        """

        if not isinstance(features, ItemFeatures):
            raise TypeError("predict requires outcome-free ItemFeatures")
        return min(max(_sigmoid(self._offset(features)), CLIP[0]), CLIP[1])

    def predict_answer(self, features: ItemFeatures, signals: AnswerSignals | None) -> float:
        if not isinstance(features, ItemFeatures):
            raise TypeError("predict requires outcome-free ItemFeatures")
        x = signal_feature(self.signal, signals)
        if x is None:
            raise ValueError(f"{self.name} has no {self.signal} signal for this attempt")
        a, b = self.coefficients
        return min(max(_sigmoid(self._offset(features) + a + b * x), CLIP[0]), CLIP[1])

    def observe(self, row) -> None:
        offset = None
        x = None
        if (
            isinstance(row, AttemptRow) and not isinstance(row, (FacetRow, SignalRow))
            and _ability_row(row)
        ):
            x = signal_feature(self.signal, row.answer_signals)
            if x is not None:
                # The base's prediction for this row, read before the base
                # learns it: the same value the harness scored.
                offset = self._offset(row.features)
        if self.base is not None:
            self.base.observe(row)
        if x is None or offset is None:
            return
        self._features.append(x)
        self._offsets.append(offset)
        self._outcomes.append(float(row.outcome))
        self.coefficients = fit_logistic(
            self._features, self._offsets, self._outcomes, prior_mean=self.prior_mean,
        )

    def rebuild(self, rows: Iterable) -> None:
        self.base = self._make_base()
        self._reset_fit()
        for row in sorted(rows, key=_order):
            self.observe(row)

    def snapshot_bytes(self) -> bytes:
        base = self.base.snapshot_bytes() if self.base is not None else b""
        own = json.dumps({
            "features": self._features, "offsets": self._offsets, "outcomes": self._outcomes,
        }, sort_keys=True).encode()
        return base + b"|" + own


def stacked_arm(base: str, signal: str, **inputs) -> AnswerSignalArm:
    """``<base>+answer_<signal>`` for any registered attempt-level arm."""

    return AnswerSignalArm(signal=signal, base_name=base, **inputs)


def _register() -> None:
    if ARM_NAMES[CONFIDENCE] in registered_predictors():
        return
    for signal in SIGNALS:
        register_predictor(
            ARM_NAMES[signal],
            lambda signal=signal, **_inputs: AnswerSignalArm(signal=signal),
            inputs=(), groups=("answer_signals",),
        )
    for base in DEFAULT_STACK_BASES:
        for signal in SIGNALS:
            register_predictor(
                stacked_name(base, signal),
                lambda base=base, signal=signal, **inputs: stacked_arm(base, signal, **inputs),
                inputs=_EKF_INPUTS, groups=("answer_signals",),
            )


def default_pairs() -> tuple[tuple[str, str], ...]:
    """(base, base+signal) for every registered stack: the duel's pairs."""

    return tuple(
        (base, stacked_name(base, signal))
        for base in DEFAULT_STACK_BASES for signal in SIGNALS
    )


_register()


__all__ = [
    "ARM_NAMES",
    "AnswerSignalArm",
    "CONFIDENCE",
    "DEFAULT_STACK_BASES",
    "FIT",
    "HEDGING",
    "SIGNALS",
    "SIGNAL_SOURCES",
    "default_pairs",
    "fit_logistic",
    "signal_feature",
    "stacked_arm",
    "stacked_name",
]
