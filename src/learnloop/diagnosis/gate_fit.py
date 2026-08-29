"""Offline follow-up gate fitting from override + usefulness labels.

The ⇧D manual override is a label generator: every manual trigger where the
gate stayed silent is a gate false negative; every auto-fired follow-up the
learner rated not-useful is a false positive. This module assembles those
labels from the persisted gate diagnostics (+ followup_ratings) and fits the
gate-score logistic weights by hand-rolled gradient descent — pure Python,
seven features, L2 regularization, exact Mann-Whitney AUC.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.numeric import sigmoid
from learnloop.diagnosis.gate_score import GATE_FEATURES, GATE_FEATURE_VERSION, subscores_from_diagnostics

# Rows whose silence says nothing about signal quality (budget gates, item
# availability) are excluded from the negative pool.
_UNINFORMATIVE_SILENT_REASONS = frozenset({"no_time", "session_cap_reached", "no_suitable_item"})
_SILENT_NEGATIVE_WEIGHT = 0.25

STRONG_LABEL_SOURCES = frozenset({"manual_override", "rating_useful", "rating_not_useful"})


@dataclass(frozen=True)
class GateExample:
    attempt_id: str
    features: dict[str, float]  # the seven gate subscores
    label: int  # 1 = should have fired / was useful; 0 = should not
    label_source: str  # "manual_override" | "rating_useful" | "rating_not_useful" | "silent_gate"
    weight: float


@dataclass(frozen=True)
class GateFitResult:
    weights: dict[str, float]
    bias: float
    auc: float
    accuracy: float
    log_loss: float
    n_examples: int
    n_positive: int
    n_negative: int
    n_strong_labels: int
    label_source_counts: dict[str, int]


class GateFitError(ValueError):
    """Raised when the label stream cannot support a fit."""


def assemble_gate_training_set(repository: Repository, config: LearnLoopConfig) -> list[GateExample]:
    followup = config.scheduler.followup
    examples: list[GateExample] = []
    for row in repository.gate_training_rows():
        gate = row.get("gate_diagnostics")
        if not isinstance(gate, dict):
            continue
        if gate.get("feature_version") != GATE_FEATURE_VERSION:
            continue
        features = subscores_from_diagnostics(gate, followup)
        if features is None:
            continue
        manual = bool(gate.get("manual_override"))
        outcome = gate.get("outcome")
        rating = row.get("rating_useful")

        if manual:
            # A user-forced follow-up where the automatic gate would have
            # stayed silent is a gate false negative.
            if gate.get("would_auto_fire") is False:
                examples.append(
                    GateExample(row["attempt_id"], features, 1, "manual_override", 1.0)
                )
            continue
        if outcome == "queued":
            if rating is True:
                examples.append(GateExample(row["attempt_id"], features, 1, "rating_useful", 1.0))
            elif rating is False:
                examples.append(GateExample(row["attempt_id"], features, 0, "rating_not_useful", 1.0))
            continue
        if outcome in ("not_triggered", "suppressed"):
            decisive = gate.get("decisive_reason")
            if decisive in _UNINFORMATIVE_SILENT_REASONS:
                continue
            # Silence the learner never contradicted is only weak evidence the
            # gate was right — downweighted so it can't drown the real labels.
            examples.append(
                GateExample(row["attempt_id"], features, 0, "silent_gate", _SILENT_NEGATIVE_WEIGHT)
            )
    return examples


def fit_gate_weights(
    examples: list[GateExample],
    *,
    l2: float = 0.1,
    epochs: int = 500,
    learning_rate: float = 0.5,
) -> GateFitResult:
    if not examples:
        raise GateFitError("No gate training examples available.")
    if not any(example.label == 1 for example in examples) or not any(
        example.label == 0 for example in examples
    ):
        raise GateFitError("Gate training set needs both positive and negative labels.")

    features = list(GATE_FEATURES)
    weights = {name: 0.0 for name in features}
    bias = 0.0
    total_weight = sum(example.weight for example in examples)

    for _ in range(epochs):
        gradient = {name: 0.0 for name in features}
        bias_gradient = 0.0
        for example in examples:
            activation = bias + sum(weights[name] * example.features[name] for name in features)
            error = sigmoid(activation) - float(example.label)
            scaled = example.weight * error
            for name in features:
                gradient[name] += scaled * example.features[name]
            bias_gradient += scaled
        for name in features:
            # L2 on weights only; bias stays unregularized.
            weights[name] -= learning_rate * (gradient[name] / total_weight + l2 * weights[name] / total_weight)
        bias -= learning_rate * bias_gradient / total_weight

    predictions = [
        (
            sigmoid(bias + sum(weights[name] * example.features[name] for name in features)),
            example,
        )
        for example in examples
    ]
    loss = 0.0
    correct = 0.0
    for predicted, example in predictions:
        clipped = min(max(predicted, 1e-9), 1.0 - 1e-9)
        loss += example.weight * -(
            example.label * log(clipped) + (1 - example.label) * log(1.0 - clipped)
        )
        if (predicted >= 0.5) == bool(example.label):
            correct += example.weight

    counts: dict[str, int] = {}
    for example in examples:
        counts[example.label_source] = counts.get(example.label_source, 0) + 1
    return GateFitResult(
        weights=weights,
        bias=bias,
        auc=_rank_auc(predictions),
        accuracy=correct / total_weight,
        log_loss=loss / total_weight,
        n_examples=len(examples),
        n_positive=sum(1 for example in examples if example.label == 1),
        n_negative=sum(1 for example in examples if example.label == 0),
        n_strong_labels=sum(1 for example in examples if example.label_source in STRONG_LABEL_SOURCES),
        label_source_counts=counts,
    )


def _rank_auc(predictions: list[tuple[float, GateExample]]) -> float:
    """Exact Mann-Whitney AUC with midrank tie handling."""

    ordered = sorted(predictions, key=lambda pair: pair[0])
    ranks: dict[int, float] = {}
    index = 0
    while index < len(ordered):
        tie_end = index
        while tie_end + 1 < len(ordered) and ordered[tie_end + 1][0] == ordered[index][0]:
            tie_end += 1
        midrank = (index + tie_end) / 2.0 + 1.0
        for position in range(index, tie_end + 1):
            ranks[position] = midrank
        index = tie_end + 1
    positive_rank_sum = sum(
        ranks[position] for position, (_, example) in enumerate(ordered) if example.label == 1
    )
    n_positive = sum(1 for _, example in ordered if example.label == 1)
    n_negative = len(ordered) - n_positive
    if n_positive == 0 or n_negative == 0:
        return 0.5
    return (positive_rank_sum - n_positive * (n_positive + 1) / 2.0) / (n_positive * n_negative)
