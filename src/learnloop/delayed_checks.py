"""The delayed check's item: the candidate rule, the picker and its receipt, the date (spec_teacher_v1 §13).

Shared by the teacher's lesson checks (:mod:`learnloop.teacher.delayed`) and data capture's measurement
checks (:mod:`learnloop.daily_plan.measurement`): one mechanism, DL2's "Check once". Code picks the item
and the date, never a model.

**The pick** (data capture A6, mvp-0.44): the candidate whose own predicted success (:func:`predicted_item_success`,
the one IRT seam) is nearest the middle of adaptive difficulty's band, the house pitch prior. An exact tie is a
uniform draw whose seed, draw and probability 1/n are on the receipt.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from typing import Any

#: The receipt's shape and the picker's rule (data capture A6).
PICK_VERSION = "delayed_pick_v2"
#: Numerical resolution, never a margin: equal predictions differ by no more than float noise.
_EXACT_TIE = 1e-12


def attempted_items(repository: Any) -> set[str]:
    with repository.connection() as connection:
        return {str(row[0]) for row in connection.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}


def revealed_items(repository: Any, lesson_id: str) -> set[str]:
    """Items this lesson exposed (a reveal row with basis ``lesson:<id>``), and items whose summed
    exposure already reaches the auto-prime threshold (an answer would be primed: never cold)."""

    from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD

    with repository.connection() as connection:
        lesson = {str(row[0]) for row in connection.execute(
            "SELECT DISTINCT practice_item_id FROM reveal_events WHERE basis = ?", (f"lesson:{lesson_id}",))}
        primed = {str(row[0]) for row in connection.execute(
            "SELECT practice_item_id FROM reveal_events GROUP BY practice_item_id HAVING SUM(amount) >= ?",
            (AUTO_PRIME_REVEAL_THRESHOLD,))}
    return lesson | primed


def lineage(item: Any) -> set[str]:
    """The structural kin an item declares: its family, its contrast pair, its shared stimulus and the
    source exercise it presents (any shared key makes two items the same material)."""

    keys: set[str] = set()
    if getattr(item, "family_id", None):
        keys.add(f"family:{item.family_id}")
    if getattr(item, "contrast_of", None):
        keys.add("pair:" + "|".join(sorted((str(item.id), str(item.contrast_of)))))
    fingerprint = getattr(item, "evidence_fingerprint", None)
    if fingerprint is not None and getattr(fingerprint, "shared_stimulus_id", None):
        keys.add(f"stimulus:{fingerprint.shared_stimulus_id}")
    exercise = getattr(item, "canonical_exercise", None)
    if exercise is not None:
        keys.add(f"exercise:{exercise.extraction_id}:{','.join(sorted(exercise.span_ids))}")
    return keys


def candidates(vault: Any, repository: Any, learning_object_id: str, *, exclude: Iterable[str],
               withheld: Any, attempted: set[str], revealed: set[str],
               excluded_lineage: set[str] | frozenset[str] = frozenset()) -> list[Any]:
    """The candidate rule (§13 step 1) for one LO, in id order."""

    from learnloop.vault.lifecycle import practice_item_serving_block

    excluded = set(exclude)
    out = []
    for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
        if item.learning_object_id != learning_object_id or item.id in excluded:
            continue
        if excluded_lineage and lineage(item) & excluded_lineage:
            continue
        if item.id in attempted or item.id in revealed:
            continue
        if withheld.reason(item.id) or practice_item_serving_block(vault, item) is not None:
            continue
        out.append(item)
    return out


def predicted_item_success(vault: Any, repository: Any, item: Any) -> float | None:
    """The active predictor's predicted unassisted success on this item: the LO's mastery (its first
    update's prior when it has no evidence yet) through the item's own IRT parameters."""

    from learnloop.clock import utc_now_iso
    from learnloop.learner.lesson_weight import predicted_success
    from learnloop.learner.mastery import initial_mastery_state_for_learning_object, resolve_item_irt_params

    learning_object = vault.learning_objects.get(item.learning_object_id)
    a, b = resolve_item_irt_params(item, learning_object, vault.config.mastery, repository.item_parameter_state(item.id))
    state = repository.mastery_state(item.learning_object_id)
    if state is None and learning_object is not None:
        state = initial_mastery_state_for_learning_object(vault, repository, item.learning_object_id, utc_now_iso())
    if state is None:
        return None
    return float(predicted_success(float(state.logit_mean), float(state.logit_variance), a=a, b=b))


def _band_middle(vault: Any) -> float:
    band = tuple(getattr(vault.config.adaptive_difficulty, "practice_band", (0.70, 0.80)))
    return (float(band[0]) + float(band[1])) / 2.0


def _uniform(seed: str) -> float:
    """A uniform in [0, 1) from the seed (53 bits of a SHA-256, as the router's draws)."""

    digest = hashlib.sha256(f"{seed}:delayed_pick".encode("utf-8")).digest()
    return (int.from_bytes(digest[:8], "big") >> 11) / float(1 << 53)


def pick_with_receipt(vault: Any, repository: Any, items: Sequence[Any], *, seed_key: str = "") -> tuple[Any | None, dict[str, Any]]:
    """The candidate pitched nearest the band's middle by its own prediction, and what was decided.

    An exact tie (equal predictions, or none: a structural tie) is a uniform draw: the seed names the
    decision (``seed_key``), never the candidates, so the check and the forecast about it agree."""

    middle = _band_middle(vault)
    considered = []
    for item in sorted(items, key=lambda value: value.id):
        p = predicted_item_success(vault, repository, item)
        # The tie reads the prediction itself; the receipt keeps it to the brief's display precision.
        considered.append({"item_id": item.id, "p": round(p, 4) if p is not None else None,
                           "distance": abs(p - middle) if p is not None else 1.0})
    receipt: dict[str, Any] = {"version": PICK_VERSION, "predictor": "mastery_ekf_item", "band_middle": middle,
                               "considered": [{"item_id": row["item_id"], "p": row["p"]} for row in considered],
                               "tied": [], "n": 0, "propensity": None, "seed": None, "draw": None, "chosen": None}
    if not considered:
        return None, receipt
    nearest = min(row["distance"] for row in considered)
    tied = [row["item_id"] for row in considered if row["distance"] - nearest <= _EXACT_TIE]
    seed, draw = None, None
    chosen = tied[0]
    if len(tied) > 1:
        seed = hashlib.sha256(f"{PICK_VERSION}|{seed_key}".encode()).hexdigest()
        draw = _uniform(seed)
        chosen = tied[min(int(draw * len(tied)), len(tied) - 1)]
    receipt.update(tied=tied, n=len(tied), propensity=1.0 / len(tied), seed=seed, draw=draw, chosen=chosen)
    return next(item for item in items if item.id == chosen), receipt


def due_days(vault: Any, repository: Any, *, purpose: str, lesson_item_ids: Sequence[str]) -> tuple[float, str]:
    """Days until the check is due, and how they were set (``retrievability`` or ``fallback``)."""

    from learnloop.scheduling.fsrs import interval_for_retention

    config = vault.config.teacher.delayed
    stabilities: list[float] = []
    if lesson_item_ids:
        marks = ",".join("?" for _ in lesson_item_ids)
        with repository.connection() as connection:
            stabilities = [float(row[0]) for row in connection.execute(
                f"SELECT stability FROM practice_item_state WHERE practice_item_id IN ({marks}) AND stability IS NOT NULL",
                list(lesson_item_ids))]
    if stabilities:
        days = interval_for_retention(max(stabilities), float(config.target_retrievability))
        basis = "retrievability"
    else:
        days = float(config.fallback_retention_days if purpose == "retention" else config.fallback_transfer_days)
        basis = "fallback"
    return min(max(days, 0.0), float(config.max_wait_days)), basis


__all__ = ["PICK_VERSION", "attempted_items", "candidates", "due_days", "lineage", "pick_with_receipt",
           "predicted_item_success", "revealed_items"]
