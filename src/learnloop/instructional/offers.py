"""The tutor's "Practice this" offer (spec_source_practice_and_probes_v1 §6.2).

After every tutor answer a practice request is prepared from the learner's
question and the answer's classified facets. It is pure and makes no model
call: the frontend runs it through ``find_practice`` once the answer is on
screen, so the answer waits for nothing, and the server re-derives the caller
context from the question event when it runs (the frontend cannot change the
policy, G2). A proposal reaches the learner only through an existing serving
path (SC1).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from learnloop.instructional.policy import learning_objects_for_event
from learnloop.source_retrieval.policy import ITEM_BOUND_CONTEXTS
from learnloop.vault.models import LoadedVault

#: The deterministic request's own prompt version, recorded on the request so a
#: later change to how it is built is visible in receipts.
PRACTICE_REQUEST_VERSION = "tutor_practice_request.v1"


def practice_request_for_answer(vault: LoadedVault, event: Mapping[str, Any], *,
                                exercise_arm: bool = False) -> dict[str, Any] | None:
    """The practice request for one answered tutor question, or None.

    ``exercise_arm`` adds ``kinds = both`` once S1's source-exercise arm is on;
    before that the request names no ``kinds``.
    """

    if event.get("answer_status") not in (None, "answered"):
        return None
    question = " ".join(str(event.get("question_md") or "").split())
    if not question:
        return None
    context = str(event.get("context") or "")
    item_id = event.get("practice_item_id")
    exclude = [item_id] if item_id and context in ITEM_BOUND_CONTEXTS else []
    facets = sorted({vault.canonical_facet_id(str(facet)) for facet in event.get("facets") or ()})
    request: dict[str, Any] = {
        "query": question[:2000],
        "learning_object_ids": list(learning_objects_for_event(vault, event)),
        "facet_ids": [facet for facet in facets if facet in vault.evidence_facets],
        "exclude_item_ids": exclude,
        "intent": "practice",
    }
    if exercise_arm:
        request["kinds"] = "both"
    return {
        "request": request,
        "caller": {"kind": "tutor", "ref": str(event["id"])},
        "version": PRACTICE_REQUEST_VERSION,
    }


__all__ = ["PRACTICE_REQUEST_VERSION", "practice_request_for_answer"]
