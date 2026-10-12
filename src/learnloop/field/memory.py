"""PF-a memory arms, registered in the learner-field arm registry.

Twelve point predictors: memory keyed per item, family or LO, with the current
fitted FSRS weights or the pinned FSRS-6 defaults, each with and without the
skeleton-distance discount. They share ``FamilyMemory``, the pure fold the
``family_memory_state`` projection also uses, and never read a store: the
caller resolves the current fit and passes it as the frozen ``fsrs_weights``
input. Without that input the current-fit arms use the defaults, and the
report manifest says so.
"""
from __future__ import annotations

from learnloop.field.predictors import register_predictor, registered_predictors
from learnloop.scheduling.family_memory_model import MEMORY_KEYS, FamilyMemory
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS

WEIGHT_LABELS = ("current_fit", "defaults")


def memory_arm_name(key: str, weight_label: str, distance_discount: bool) -> str:
    return f"memory_{key}/{weight_label}" + ("/distance" if distance_discount else "")


def _factory(key: str, weight_label: str, distance_discount: bool):
    def create(*, fsrs_weights: tuple[float, ...] | None = None) -> FamilyMemory:
        weights = (fsrs_weights or FSRS6_DEFAULT_WEIGHTS) if weight_label == "current_fit" else FSRS6_DEFAULT_WEIGHTS
        return FamilyMemory(key, weights, weight_label=weight_label, distance_discount=distance_discount)
    return create


def _register() -> None:
    if memory_arm_name("item", "current_fit", False) in registered_predictors():
        return
    for weight_label in WEIGHT_LABELS:
        for key in MEMORY_KEYS:
            for distance_discount in (False, True):
                register_predictor(
                    memory_arm_name(key, weight_label, distance_discount),
                    _factory(key, weight_label, distance_discount),
                    inputs=("fsrs_weights",), groups=("memory", "families"),
                )


_register()
