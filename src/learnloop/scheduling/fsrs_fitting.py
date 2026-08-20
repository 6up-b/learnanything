"""Pure-Python FSRS-6 weight fitting on the learner's own review log.

Maximum-likelihood fit of a high-leverage subset of the 21 FSRS weights by
gradient descent (central-difference gradients) in relative space w_j/d_j,
with L2 shrinkage toward the pinned defaults so the fit degrades gracefully at
small N (the N=1 safety mechanism: at tens of reviews the regularizer wins; as
data grows it vanishes).

Fitted indices: initial stabilities (w0-w3) plus the recall-stability /
retention-curve shape (w8, w9, w10, w20). Difficulty dynamics (w4-w7),
forget-stability (w11-w14), and hard/easy modifiers (w15-w16) stay pinned;
w17-w19 are dead in this implementation (no short-term branch) and must never
be fit.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from learnloop.config import FsrsFittingConfig
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, MemoryState, Rating, apply_review, forgetting_curve
from learnloop.scheduling.review_log import ReviewLog

FIT_INDICES: tuple[int, ...] = (0, 1, 2, 3, 8, 9, 10, 20)

# Absolute bounds per fitted index (from the upstream optimizer's clamps,
# adapted to this implementation's live formulas).
FIT_BOUNDS: dict[int, tuple[float, float]] = {
    0: (0.001, 100.0),
    1: (0.001, 100.0),
    2: (0.001, 100.0),
    3: (0.001, 100.0),
    8: (0.0, 4.5),
    9: (0.0, 0.8),
    10: (0.001, 3.5),
    20: (0.1, 0.8),
}

_P_CLIP = 1e-6


class FsrsFittingError(ValueError):
    """Raised when the review log cannot support a fit."""


@dataclass(frozen=True)
class FsrsFitResult:
    weights: tuple[float, ...]  # full 21-tuple, pinned + fitted merged
    fitted_indices: tuple[int, ...]
    review_count: int  # all reconstructed reviews
    predicted_count: int  # loss-contributing reviews
    log_loss_default: float  # unregularized, same data
    log_loss_fitted: float
    improved: bool
    relative_improvement: float
    iterations: int
    converged: bool
    data_through: str | None


def review_log_loss(
    review_log: ReviewLog,
    weights: tuple[float, ...],
    *,
    min_elapsed_days: float,
) -> tuple[float, int]:
    """Weighted mean binary cross-entropy of recall predictions, and its N.

    Chains each item's full (rating, elapsed) sequence through ``apply_review``
    so stabilities evolve exactly as the live path would have under
    ``weights``. Reviews with elapsed < ``min_elapsed_days`` still update the
    state chain but contribute no loss term (no short-term branch here).
    """

    total_loss = 0.0
    total_weight = 0.0
    n_predictions = 0
    for sequence in review_log.sequences.values():
        state: MemoryState | None = None
        for observation in sequence:
            if (
                state is not None
                and observation.elapsed_days >= min_elapsed_days
                and observation.weight > 0.0
            ):
                predicted = forgetting_curve(state.stability, observation.elapsed_days, weights)
                predicted = min(max(predicted, _P_CLIP), 1.0 - _P_CLIP)
                actual = 0.0 if observation.rating == Rating.AGAIN else 1.0
                loss = -(actual * log(predicted) + (1.0 - actual) * log(1.0 - predicted))
                total_loss += observation.weight * loss
                total_weight += observation.weight
                n_predictions += 1
            state = apply_review(state, observation.rating, observation.elapsed_days, weights)
    if n_predictions == 0 or total_weight <= 0.0:
        return 0.0, 0
    return total_loss / total_weight, n_predictions


def fit_fsrs_weights(
    review_log: ReviewLog,
    *,
    config: FsrsFittingConfig,
    initial: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> FsrsFitResult:
    default_loss, predicted_count = review_log_loss(
        review_log, FSRS6_DEFAULT_WEIGHTS, min_elapsed_days=config.min_elapsed_days
    )
    if predicted_count < config.min_reviews:
        raise FsrsFittingError(
            f"Review log has {predicted_count} usable reviews; "
            f"need at least {config.min_reviews} to fit FSRS weights."
        )

    defaults = [max(abs(value), 1e-9) for value in FSRS6_DEFAULT_WEIGHTS]

    def to_weights(relative: list[float]) -> tuple[float, ...]:
        merged = list(initial)
        for j, index in enumerate(FIT_INDICES):
            merged[index] = relative[j] * defaults[index]
        return _project(merged)

    def objective(relative: list[float]) -> float:
        weights = to_weights(relative)
        loss, n = review_log_loss(review_log, weights, min_elapsed_days=config.min_elapsed_days)
        if n == 0:
            return float("inf")
        penalty = sum((relative[j] - 1.0) ** 2 for j in range(len(FIT_INDICES)))
        return loss + (config.l2_lambda / max(n, 1)) * penalty

    relative = [initial[index] / defaults[index] for index in FIT_INDICES]
    relative = _clamp_relative(relative, defaults)
    current = objective(relative)
    step = config.initial_step
    h = 1e-3
    iterations = 0
    converged = False
    consecutive_accepts = 0

    for iterations in range(1, config.max_iterations + 1):
        gradient: list[float] = []
        for j in range(len(relative)):
            plus = list(relative)
            minus = list(relative)
            plus[j] += h
            minus[j] -= h
            gradient.append((objective(_clamp_relative(plus, defaults)) - objective(_clamp_relative(minus, defaults))) / (2 * h))
        norm = max(sum(g * g for g in gradient) ** 0.5, 1e-12)
        accepted = False
        trial_step = step
        for _ in range(10):
            candidate = _clamp_relative(
                [relative[j] - trial_step * gradient[j] / norm for j in range(len(relative))],
                defaults,
            )
            candidate_loss = objective(candidate)
            if candidate_loss < current:
                improvement = (current - candidate_loss) / max(abs(current), 1e-12)
                relative = candidate
                current = candidate_loss
                accepted = True
                consecutive_accepts += 1
                if consecutive_accepts >= 3:
                    step = min(step * 1.2, 0.2)
                if improvement < 1e-6:
                    converged = True
                break
            trial_step *= 0.5
        if not accepted:
            step = trial_step
            consecutive_accepts = 0
            converged = True
        if converged:
            break

    fitted_weights = to_weights(relative)
    fitted_loss, _ = review_log_loss(review_log, fitted_weights, min_elapsed_days=config.min_elapsed_days)
    relative_improvement = (default_loss - fitted_loss) / max(abs(default_loss), 1e-12)
    return FsrsFitResult(
        weights=fitted_weights,
        fitted_indices=FIT_INDICES,
        review_count=review_log.total_reviews,
        predicted_count=predicted_count,
        log_loss_default=default_loss,
        log_loss_fitted=fitted_loss,
        improved=relative_improvement >= config.min_relative_improvement,
        relative_improvement=relative_improvement,
        iterations=iterations,
        converged=converged,
        data_through=review_log.data_through,
    )


def _clamp_relative(relative: list[float], defaults: list[float]) -> list[float]:
    clamped = list(relative)
    for j, index in enumerate(FIT_INDICES):
        low, high = FIT_BOUNDS[index]
        clamped[j] = min(max(clamped[j], low / defaults[index]), high / defaults[index])
    return clamped


def _project(weights: list[float]) -> tuple[float, ...]:
    """Bounds + w0<=w1<=w2<=w3 ordering (initial stability must be monotone in rating)."""

    for index, (low, high) in FIT_BOUNDS.items():
        weights[index] = min(max(weights[index], low), high)
    for index in (1, 2, 3):
        if weights[index] < weights[index - 1]:
            weights[index] = weights[index - 1]
    return tuple(weights)
