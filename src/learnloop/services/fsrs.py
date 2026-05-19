from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import exp


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


# FSRS-6 default parameters from open-spaced-repetition/py-fsrs README
# as observed for the 6.x scheduler line in May 2026.
FSRS6_DEFAULT_WEIGHTS: tuple[float, ...] = (
    0.212,
    1.2931,
    2.3065,
    8.2956,
    6.4133,
    0.8334,
    3.0194,
    0.001,
    1.8722,
    0.1666,
    0.796,
    1.4835,
    0.0614,
    0.2629,
    1.6483,
    0.6014,
    1.8729,
    0.5425,
    0.0912,
    0.0658,
    0.1542,
)

S_MIN = 0.001
D_MIN = 1.0
D_MAX = 10.0


@dataclass(frozen=True)
class MemoryState:
    difficulty: float
    stability: float
    retrievability: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def forgetting_curve(stability: float | None, elapsed_days: float, weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS) -> float:
    if stability is None or stability <= 0:
        return 0.0
    decay = weights[20]
    factor = 0.9 ** (1 / -decay) - 1
    return clamp((1 + factor * max(elapsed_days, 0.0) / stability) ** (-decay), 0.0, 1.0)


def initial_stability(rating: Rating, weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS) -> float:
    return max(weights[int(rating) - 1], S_MIN)


def initial_difficulty(rating: Rating, weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS) -> float:
    return clamp(weights[4] - exp(weights[5] * (int(rating) - 1)) + 1, D_MIN, D_MAX)


def next_difficulty(difficulty: float, rating: Rating, weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS) -> float:
    delta = weights[6] * (int(rating) - 3)
    next_d = difficulty - delta
    easy_difficulty = initial_difficulty(Rating.EASY, weights)
    mean_reversion = weights[7] * easy_difficulty + (1 - weights[7]) * next_d
    return clamp(mean_reversion, D_MIN, D_MAX)


def next_forget_stability(
    difficulty: float,
    stability: float,
    retrievability: float,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> float:
    value = (
        weights[11]
        * difficulty ** (-weights[12])
        * ((stability + 1) ** weights[13] - 1)
        * exp((1 - retrievability) * weights[14])
    )
    return max(value, S_MIN)


def next_recall_stability(
    difficulty: float,
    stability: float,
    retrievability: float,
    rating: Rating,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> float:
    hard_penalty = weights[15] if rating == Rating.HARD else 1.0
    easy_bonus = weights[16] if rating == Rating.EASY else 1.0
    value = stability * (
        1
        + exp(weights[8])
        * (11 - difficulty)
        * stability ** (-weights[9])
        * (exp((1 - retrievability) * weights[10]) - 1)
        * hard_penalty
        * easy_bonus
    )
    if rating == Rating.HARD:
        value = min(value, stability)
    return max(value, S_MIN)


def apply_review(
    previous: MemoryState | None,
    rating: Rating,
    elapsed_days: float,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> MemoryState:
    if previous is None:
        stability = initial_stability(rating, weights)
        difficulty = initial_difficulty(rating, weights)
        return MemoryState(difficulty=difficulty, stability=stability, retrievability=1.0)

    retrievability = forgetting_curve(previous.stability, elapsed_days, weights)
    difficulty = next_difficulty(previous.difficulty, rating, weights)
    if rating == Rating.AGAIN:
        stability = next_forget_stability(difficulty, previous.stability, retrievability, weights)
    else:
        stability = next_recall_stability(difficulty, previous.stability, retrievability, rating, weights)
    return MemoryState(difficulty=difficulty, stability=stability, retrievability=retrievability)


def interval_for_retention(
    stability: float,
    desired_retention: float = 0.9,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> float:
    retention = clamp(desired_retention, 0.01, 0.99)
    decay = weights[20]
    factor = 0.9 ** (1 / -decay) - 1
    return max(0.0, stability * (retention ** (1 / -decay) - 1) / factor)


def rating_from_score(score: int, max_points: int = 4) -> Rating:
    ratio = score / max(max_points, 1)
    if ratio < 0.25:
        return Rating.AGAIN
    if ratio < 0.60:
        return Rating.HARD
    if ratio < 0.90:
        return Rating.GOOD
    return Rating.EASY
