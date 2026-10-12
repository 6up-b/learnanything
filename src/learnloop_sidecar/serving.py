"""Sidecar refusal for serving an item of a put-away Learning Object.

The by-id serve doors (``open_queue_item``, a session ``get_practice_item``,
``start_teach_back``, ``start_overconfidence_probe``) take an id rather than a
queue position, so a deep link, a restored session or a stale client can reach
an item the scheduler would no longer offer. When the owning LO is ``dormant``
or ``resolved`` the door refuses with a typed code instead of serving it
(``learnloop.vault.lifecycle``; daily-loop audit 2026-10-11).

Writes (draft saves, submissions) deliberately do not use this: an answer typed
before the learner put the LO away still saves.
"""

from __future__ import annotations

from learnloop.vault.lifecycle import learning_object_serving_block
from learnloop.vault.models import LoadedVault
from learnloop_sidecar.errors import SidecarError

INACTIVE_LEARNING_OBJECT_ERROR_CODE = "learning_object_inactive"


def refuse_inactive_learning_object(vault: LoadedVault, learning_object_id: str | None) -> None:
    block = learning_object_serving_block(vault, learning_object_id)
    if block is None or block == "learning_object_missing":
        # A missing LO keeps its existing handling at each door.
        return
    learning_object = vault.learning_objects[str(learning_object_id)]
    raise SidecarError(
        INACTIVE_LEARNING_OBJECT_ERROR_CODE,
        f"{learning_object.title} is {learning_object.status}, so its practice is not served. "
        "Set the learning object back to active to practise it again.",
        details={"learning_object_id": learning_object.id, "status": learning_object.status},
    )
