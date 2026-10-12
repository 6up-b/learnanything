"""Sidecar refusal for serving an item of a put-away Learning Object.

The by-id serve doors (``open_queue_item``, a session ``get_practice_item``,
``start_teach_back``, ``start_overconfidence_probe``) take an id rather than a
queue position, so a deep link, a restored session or a stale client can reach
an item the scheduler would no longer offer. When the owning LO is ``dormant``
or ``resolved`` the door refuses with a typed code instead of serving it
(``learnloop.vault.lifecycle``; daily-loop audit 2026-10-11).

The same doors refuse a card the reader's reference-question sweep adopted while
the sweep's kill switch (``tutor_qa.adopt_reference_questions``) is off, so a
stale link cannot bring back what the queue no longer serves (re-review F8).

Writes (draft saves, submissions) deliberately do not use this: an answer typed
before the learner put the LO away still saves.
"""

from __future__ import annotations

from learnloop.vault.lifecycle import (
    REFERENCE_ADOPTION_DISABLED,
    learning_object_serving_block,
    practice_item_serving_block,
)
from learnloop.vault.models import LoadedVault, PracticeItem
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


def refuse_unservable_item(vault: LoadedVault, item: PracticeItem) -> None:
    """The item-level door: its LO's refusal, then the adoption kill switch."""

    refuse_inactive_learning_object(vault, item.learning_object_id)
    if practice_item_serving_block(vault, item) == REFERENCE_ADOPTION_DISABLED:
        raise SidecarError(
            REFERENCE_ADOPTION_DISABLED,
            f"{item.id} was adopted from a reader reference question, and adoption is "
            "switched off (tutor_qa.adopt_reference_questions), so it is not served. "
            "Turn the switch back on to practise it again.",
            details={"practice_item_id": item.id},
        )
