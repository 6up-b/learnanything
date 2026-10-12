"""Serving lifecycle of a practice item's owning Learning Object.

``LearningObject.status`` is the learner's lifecycle switch: ``active``,
``dormant`` (parked) or ``resolved`` (done). Only an ``active`` LO's items may be
served; a dormant or resolved LO has been put away by the learner, and bringing
its items back would ignore that choice (daily-loop audit 2026-10-11).

Every serving door asks this one module: the scheduler's candidate loop and its
by-id follow-up lane, the probe pool and the re-probe producer, and the sidecar's
by-id serve doors. It is a pure read of vault YAML. Nothing is persisted or
deactivated, so setting the LO back to ``active`` makes its items servable again
immediately with their history, FSRS state and projections untouched.
"""

from __future__ import annotations

from learnloop.vault.models import LoadedVault

SERVABLE_LEARNING_OBJECT_STATUS = "active"


def learning_object_serving_block(vault: LoadedVault, learning_object_id: str | None) -> str | None:
    """Why the LO's items may not be served now, or ``None`` when they may.

    Returns ``"learning_object_missing"`` for an unknown id and
    ``"learning_object_<status>"`` (``dormant`` / ``resolved``) for an LO the
    learner has put away."""

    learning_object = vault.learning_objects.get(str(learning_object_id or ""))
    if learning_object is None:
        return "learning_object_missing"
    if learning_object.status != SERVABLE_LEARNING_OBJECT_STATUS:
        return f"learning_object_{learning_object.status}"
    return None


def learning_object_servable(vault: LoadedVault, learning_object_id: str | None) -> bool:
    return learning_object_serving_block(vault, learning_object_id) is None
