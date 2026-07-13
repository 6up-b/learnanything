"""Offline forgetting-model benchmark (spec_probe_eig_redesign.md Checkpoint 5.6).

Benchmarks a DAS3H-style time-window logistic model against frequency
baselines on the vault's own attempt history, with a strict temporal split.
Report-only: per the spec this harness MUST NOT automatically replace durable
learner state or facet mappings — it exists to tell us whether a
forgetting-curve feature family predicts next-attempt success better than
what the current pipeline effectively encodes, before any adoption decision.

DAS3H (González-Brenes et al. 2019) counts attempts and wins per skill in
overlapping time windows; here the "skill" is the Learning Object and the
feature vector per attempt is log(1 + count) of prior attempts/wins in
1-, 7-, and 30-day windows plus lifetime counts. Pure-Python full-batch
gradient descent keeps the fit deterministic and dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository

WINDOWS_DAYS: tuple[float, ...] = (1.0, 7.0, 30.0)
_EPS = 1e-9


def _attempt_succeeded(attempt: dict[str, Any]) -> bool:
    # Mirrors the shared failure predicate (question_signal/followups).
    return not (
        attempt.get("attempt_type") == "dont_know"
        or float(attempt.get("correctness") or 0.0) <= 0.40
        or bool(attempt.get("error_type"))
    )


@dataclass(frozen=True)
class BenchmarkExample:
    learning_object_id: str
    created_at: str
    features: tuple[float, ...]
    outcome: bool


def build_examples(repository: Repository) -> list[BenchmarkExample]:
    """One example per graded attempt, features from strictly earlier attempts."""

    examples: list[BenchmarkExample] = []
    for learning_object_id in sorted(repository.learning_object_ids_with_attempts()):
        attempts = [
            attempt
            for attempt in repository.list_attempts_by_learning_object(learning_object_id)
            if attempt.get("created_at")
        ]
        attempts.sort(key=lambda attempt: (attempt["created_at"], attempt.get("id", "")))
        history: list[tuple[Any, bool]] = []  # (created datetime, succeeded)
        for attempt in attempts:
            created = parse_utc(attempt["created_at"])
            if created is None:
                continue
            features: list[float] = [1.0]  # bias
            for window_days in WINDOWS_DAYS:
                in_window = [
                    succeeded
                    for happened, succeeded in history
                    if (created - happened).total_seconds() <= window_days * 86400.0
                ]
                features.append(log(1.0 + len(in_window)))
                features.append(log(1.0 + sum(1 for s in in_window if s)))
            features.append(log(1.0 + len(history)))
            features.append(log(1.0 + sum(1 for _t, s in history if s)))
            succeeded = _attempt_succeeded(attempt)
            examples.append(
                BenchmarkExample(
                    learning_object_id=learning_object_id,
                    created_at=attempt["created_at"],
                    features=tuple(features),
                    outcome=succeeded,
                )
            )
            history.append((created, succeeded))
    examples.sort(key=lambda example: (example.created_at, example.learning_object_id))
    return examples


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + exp(-z))
    ez = exp(z)
    return ez / (1.0 + ez)


def fit_logistic(
    examples: list[BenchmarkExample],
    *,
    learning_rate: float = 0.1,
    iterations: int = 400,
    l2: float = 0.01,
) -> list[float]:
    """Deterministic full-batch gradient descent (no RNG, fixed iterations)."""

    if not examples:
        return []
    dims = len(examples[0].features)
    weights = [0.0] * dims
    n = float(len(examples))
    for _ in range(iterations):
        gradient = [0.0] * dims
        for example in examples:
            z = sum(w * x for w, x in zip(weights, example.features))
            error = _sigmoid(z) - (1.0 if example.outcome else 0.0)
            for index, x in enumerate(example.features):
                gradient[index] += error * x
        for index in range(dims):
            regularization = l2 * weights[index] if index > 0 else 0.0  # bias unregularized
            weights[index] -= learning_rate * (gradient[index] / n + regularization)
    return weights


def _clamp(probability: float) -> float:
    return min(1.0 - _EPS, max(_EPS, probability))


def _metrics(predictions: list[float], outcomes: list[bool]) -> dict[str, float | int]:
    log_loss = -sum(
        log(_clamp(p)) if outcome else log(_clamp(1.0 - p))
        for p, outcome in zip(predictions, outcomes)
    ) / len(outcomes)
    brier = sum(
        (p - (1.0 if outcome else 0.0)) ** 2 for p, outcome in zip(predictions, outcomes)
    ) / len(outcomes)
    return {"log_loss": round(log_loss, 4), "brier": round(brier, 4), "n": len(outcomes)}


def run_forgetting_benchmark(
    repository: Repository,
    *,
    train_fraction: float = 0.7,
    minimum_examples: int = 20,
) -> dict[str, Any]:
    """Temporal-split benchmark: DAS3H-style model vs frequency baselines.

    Baselines: global train success rate, and per-LO train success rate with
    global fallback. Comparison is on held-out (later-in-time) attempts only.
    """

    examples = build_examples(repository)
    if len(examples) < minimum_examples:
        return {
            "version": 1,
            "status": "insufficient_data",
            "examples": len(examples),
            "minimum_examples": minimum_examples,
        }
    split = max(1, min(len(examples) - 1, int(len(examples) * train_fraction)))
    train, test = examples[:split], examples[split:]

    global_rate = _clamp(sum(1 for e in train if e.outcome) / len(train))
    lo_counts: dict[str, tuple[int, int]] = {}
    for example in train:
        wins, total = lo_counts.get(example.learning_object_id, (0, 0))
        lo_counts[example.learning_object_id] = (wins + (1 if example.outcome else 0), total + 1)

    weights = fit_logistic(train)
    outcomes = [example.outcome for example in test]
    das3h_predictions = [
        _sigmoid(sum(w * x for w, x in zip(weights, example.features))) for example in test
    ]
    global_predictions = [global_rate] * len(test)
    per_lo_predictions = []
    for example in test:
        wins, total = lo_counts.get(example.learning_object_id, (0, 0))
        per_lo_predictions.append(_clamp(wins / total) if total > 0 else global_rate)

    results = {
        "das3h_time_windows": _metrics(das3h_predictions, outcomes),
        "baseline_global_rate": _metrics(global_predictions, outcomes),
        "baseline_per_lo_rate": _metrics(per_lo_predictions, outcomes),
    }
    best = min(results, key=lambda name: results[name]["log_loss"])
    return {
        "version": 1,
        "status": "ok",
        "train_examples": len(train),
        "test_examples": len(test),
        "window_days": list(WINDOWS_DAYS),
        "results": results,
        "best_by_log_loss": best,
        # Checkpoint 5.6: never auto-adopt — a human reads this and decides.
        "note": "report-only benchmark; durable state and facet mappings are never replaced automatically",
    }
