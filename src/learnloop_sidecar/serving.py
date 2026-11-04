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

A session serve also refuses an item made from material held out for
evaluation (exam protection, Codex review F1): a queue built, a link copied or
a session restored before the owner marked the unit still cannot put the
exam's question in front of the learner (``refuse_held_out_item``; kill switch
``goals.held_out_selection``).

A by-id door also refuses an item the requesting device cannot answer (mobile
PR-6, ``desktop_only``), and :func:`device_filter` is what a queue build holds back
for the same device. With no request origin, the desktop, neither does anything;
``practice.device_eligibility_enabled`` off turns off both, for the phone too.
"""

from __future__ import annotations

from typing import Any

from learnloop.content.sources.exam_material import (
    HELD_OUT_ITEM_REFUSAL,
    held_out_item_ids,
    held_out_material,
    held_out_selection_active,
)
from learnloop.scheduling.device_eligibility import DEVICE_POLICY, DEVICE_POLICY_OFF, DeviceFilter, ineligibility_reason
from learnloop.vault.lifecycle import (
    LEARNER_TEXT_GAP_DISABLED,
    REFERENCE_ADOPTION_DISABLED,
    learning_object_serving_block,
    practice_item_serving_block,
)
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.request_origin import RequestOrigin, device_class

DESKTOP_ONLY_ERROR_CODE = "desktop_only"
INACTIVE_LEARNING_OBJECT_ERROR_CODE = "learning_object_inactive"
HELD_OUT_MATERIAL_ERROR_CODE = "held_out_material"


def _device_rules_on(vault: Any) -> bool:
    return bool(vault.config.practice.device_eligibility_enabled)


def device_policy(vault: Any) -> str:
    """The rules a phone request is served under, for the router's inputs."""

    return DEVICE_POLICY if _device_rules_on(vault) else DEVICE_POLICY_OFF


def origin_ineligibility(origin: RequestOrigin | None, vault: Any, item: Any) -> str | None:
    """Why the request's device cannot answer ``item``; never asked for the desktop."""

    if origin is None or not _device_rules_on(vault):
        return None
    return ineligibility_reason(vault, item, device_class(origin))


def device_filter(
    origin: RequestOrigin | None, vault: Any, repository: Any = None, session_id: str | None = None
) -> DeviceFilter | None:
    """What a queue build holds back for the request's device (§6.4, D6). None for
    the desktop, and with the switch off: the build is then the desktop's.

    With a session, also the diagnostic presentation it committed here and left for the
    desktop: the phone never renders one, so it is no part of what the phone can be shown."""

    if origin is None or not _device_rules_on(vault):
        return None
    committed = repository.active_probe_presentation_for_session(session_id) if repository and session_id else None
    left = frozenset({committed.practice_item_id}) if committed is not None else frozenset()
    return DeviceFilter(vault, device_class(origin), left_for_desktop=left)


def refuse_device_ineligible_item(origin: RequestOrigin | None, vault: Any, item: Any) -> None:
    """A by-id door (§6.4): a stale list, a deep link or a restored session cannot
    bring the phone an item it cannot show. The desktop is never refused."""

    reason = origin_ineligibility(origin, vault, item)
    if reason is not None:
        raise SidecarError(
            DESKTOP_ONLY_ERROR_CODE,
            f"{item.id} can only be answered on the desktop.",
            details={"practice_item_id": item.id, "reason": reason},
        )


def refuse_inactive_learning_object(vault: LoadedVault, learning_object_id: str | None) -> None:
    block = learning_object_serving_block(vault, learning_object_id)
    if block is None or block == "learning_object_missing":
        # A missing LO keeps its existing handling at each door.
        return
    learning_object = vault.learning_objects[str(learning_object_id)]
    if block == LEARNER_TEXT_GAP_DISABLED:
        raise SidecarError(
            LEARNER_TEXT_GAP_DISABLED,
            f"{learning_object.title} was added from your question, and adding prerequisites that way is "
            "switched off (learner_text_gaps.create_prerequisites_enabled), so it is not served. "
            "Turn the switch back on to practise it again.",
            details={"learning_object_id": learning_object.id},
        )
    raise SidecarError(
        INACTIVE_LEARNING_OBJECT_ERROR_CODE,
        f"{learning_object.title} is {learning_object.status}, so its practice is not served. "
        "Set the learning object back to active to practise it again.",
        details={"learning_object_id": learning_object.id, "status": learning_object.status},
    )


def refuse_generated_probe_door(ctx_origin: RequestOrigin | None, repository: Any, item: PracticeItem,
                                *, serve: bool) -> None:
    """FG1 §4.2: every serve door for a generated probe, before its text leaves.

    A session serve claims the one administration (keyed to surface and presentation),
    atomically; a re-open of that same administration passes. Reserved for its workflow
    until then, and closed afterwards. A read with no session (feedback, the inspector)
    never burns, and sees it only once it has been served. A phone never opens one (§10).
    An item with no identity passes, and the ledger is read whatever the switch says:
    burns persist after a rollback.
    """

    from learnloop.followup_serve import identity, workflow as followup_workflow
    from learnloop.followup_serve.gates import SERVING_SURFACE

    if not identity.is_generated_probe(repository, item.id):
        return
    refusal = None
    if not serve:
        if identity.door_refusal(repository, item.id) == identity.GENERATED_PROBE_RESERVED:
            refusal = identity.GENERATED_PROBE_RESERVED
    elif ctx_origin is not None:
        refusal = identity.GENERATED_PROBE_RESERVED
    else:
        row = followup_workflow.workflow_of_item(repository, item.id)
        owned = row is not None and row["state"] == followup_workflow.READY
        if row is not None and not owned and identity.door_refusal(repository, item.id, workflow_id=row["id"]) is None:
            refusal = identity.GENERATED_PROBE_RESERVED
        else:
            claim = identity.claim_serve(
                repository, item.id, surface=SERVING_SURFACE,
                presentation_id=(row or {}).get("presentation_id"),
                workflow_id=(row or {}).get("id"),
            )
            if not claim.granted:
                refusal = claim.reason or identity.GENERATED_PROBE_CLOSED
    if refusal is not None:
        raise SidecarError(
            refusal,
            f"{item.id} is a single-use question and can't be opened here.",
            details={"practice_item_id": item.id},
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


def refuse_held_out_item(vault: LoadedVault, repository: Any, item: PracticeItem) -> None:
    """A session serve of an item made from held-out material is refused."""

    if not held_out_selection_active(vault):
        return
    if held_out_item_ids([item], held_out_material(vault, repository)):
        raise SidecarError(
            HELD_OUT_MATERIAL_ERROR_CODE,
            f"{item.id}: {HELD_OUT_ITEM_REFUSAL}.",
            details={"practice_item_id": item.id},
        )
