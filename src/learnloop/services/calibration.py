"""Difficulty-miscalibration monitor (spec_irt_difficulty.md §7.4).

The only N=1-safe signal that an authored/LLM difficulty ``b`` is wrong: a
persistently one-sided innovation ``y - p`` on an item. This cannot *fit* ``b``
(theta and b are confounded at N=1, §3) but it *detects* a bad prior and is the
concrete trigger for Phase C calibration. Reads existing data only — no schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from learnloop.vault.models import LoadedVault

DEFAULT_MIN_ATTEMPTS = 5
DEFAULT_INNOVATION_THRESHOLD = 0.5


@dataclass(frozen=True)
class MiscalibrationFlag:
    practice_item_id: str
    learning_object_id: str | None
    attempts: int
    mean_innovation: float
    direction: str  # "too_hard" | "too_easy"

    @property
    def message(self) -> str:
        verdict = "too hard" if self.direction == "too_hard" else "too easy"
        outcome = "beats" if self.direction == "too_hard" else "trails"
        return (
            f"{self.practice_item_id}: difficulty likely miscalibrated (b {verdict}); "
            f"learner {outcome} prediction by mean innovation {self.mean_innovation:+.2f} "
            f"over {self.attempts} attempts - author review."
        )


def difficulty_miscalibration_flags(
    vault: LoadedVault,
    repository,
    *,
    min_attempts: int = DEFAULT_MIN_ATTEMPTS,
    threshold: float = DEFAULT_INNOVATION_THRESHOLD,
) -> list[MiscalibrationFlag]:
    """Per-item flags where the mean innovation ``y - p`` is persistently one-sided.

    ``mean_innovation > +threshold`` (learner consistently beats the predicted
    correctness) ⇒ the item plays easier than its ``b`` implies ⇒ ``b`` likely too
    hard. ``< -threshold`` ⇒ ``b`` likely too easy. Attempts whose surprise row
    predates the IRT trace (no ``expected_correctness``) are skipped.
    """

    samples: dict[str, list[float]] = {}
    learning_objects: dict[str, str | None] = {}
    for sample in repository.attempt_innovation_samples():
        item_id = sample.get("practice_item_id")
        item = vault.practice_items.get(item_id) if item_id else None
        if item is None:
            continue
        expected = _expected_correctness(sample.get("predicted_score_dist_json"))
        if expected is None:
            continue
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        observed_y = (sample.get("rubric_score") or 0) / max(max_points, 1)
        samples.setdefault(item_id, []).append(observed_y - expected)
        learning_objects[item_id] = sample.get("learning_object_id")

    flags: list[MiscalibrationFlag] = []
    for item_id, innovations in samples.items():
        if len(innovations) < min_attempts:
            continue
        mean_innovation = sum(innovations) / len(innovations)
        if mean_innovation > threshold:
            direction = "too_hard"
        elif mean_innovation < -threshold:
            direction = "too_easy"
        else:
            continue
        flags.append(
            MiscalibrationFlag(
                practice_item_id=item_id,
                learning_object_id=learning_objects.get(item_id),
                attempts=len(innovations),
                mean_innovation=mean_innovation,
                direction=direction,
            )
        )
    flags.sort(key=lambda flag: flag.practice_item_id)
    return flags


def _expected_correctness(predicted_score_dist_json: str | None) -> float | None:
    if not predicted_score_dist_json:
        return None
    try:
        payload = json.loads(predicted_score_dist_json)
    except (TypeError, ValueError):
        return None
    value = payload.get("expected_correctness") if isinstance(payload, dict) else None
    return float(value) if isinstance(value, (int, float)) else None
