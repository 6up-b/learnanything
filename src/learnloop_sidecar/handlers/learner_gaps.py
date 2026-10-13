"""Learner-text gap RPCs: what a question was read as, and its one-tap undo.

``get_learner_text_gap`` returns the reading of one tutor question (or any
source) once the gaps worker has run it: the kind, the name, what was done
(matched, linked, created, a belief noted) and which reversals the learner
may tap. It reloads the vault when the reading wrote to it (a created LO, an
added edge), so the queue and the map see them. ``reverse_learner_text_gap``
applies one reversal: undo an added edge, undo a created prerequisite, or
"not what I meant" on a belief. Desktop only (never on the phone allowlist).
"""

from __future__ import annotations

from contextlib import closing
import logging
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.stores import learner_gaps as store
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class GetLearnerTextGapInput(ParamsModel):
    source_kind: str = "tutor_question"
    source_id: str


class ReverseLearnerTextGapInput(ParamsModel):
    gap_id: str
    reversal: str


def gap_view(vault: Any, gap: dict[str, Any], reversals: list[str]) -> dict[str, Any]:
    """The learner-facing reading: honest labels, only what happened."""

    named = {key: value for key, value in (gap.get("named") or {}).items() if key != "reading_status"}
    target_title = None
    if gap.get("target_kind") == "learning_object" and gap.get("target_id") in vault.learning_objects:
        target_title = vault.learning_objects[gap["target_id"]].title
    detail = gap.get("detail") or {}
    action = gap["action"]
    label = None
    allowed: list[str] = []
    if action == "created_prerequisite":
        label = f"Added from your question: {target_title or gap.get('target_id')}"
        if gap.get("seed_status") == "review_required":
            label += " (its practice item is waiting for review)"
        elif not gap.get("seed_practice_item_id"):
            label += " (no practice item yet)"
        if "undo_creation" not in reversals:
            allowed.append("undo_creation")
    elif action == "matched_prerequisite":
        label = f"Noted: this builds on {target_title or gap.get('target_id')}"
        if gap.get("edge_id"):
            label += " (link added from your question)"
            if "undo_edge" not in reversals:
                allowed.append("undo_edge")
    elif action in ("belief_sighting", "belief_candidate"):
        label = f"Noted a possible mix-up: {named.get('belief_statement') or 'a belief'}"
        if "not_this_belief" not in reversals:
            allowed.append("not_this_belief")
    if "undo_creation" in reversals:
        label = f"Removed: {target_title or gap.get('target_id')} (undone)"
    elif "undo_edge" in reversals and label:
        label = label.replace(" (link added from your question)", " (link undone)")
    elif "not_this_belief" in reversals:
        label = "Noted: not what you meant"
    return {
        "gap_id": gap["id"],
        "kind": gap["kind"],
        "action": action,
        "named": named,
        "target": {"kind": gap.get("target_kind"), "id": gap.get("target_id"), "title": target_title}
        if gap.get("target_id") else None,
        "edge_id": gap.get("edge_id"),
        "seed_practice_item_id": gap.get("seed_practice_item_id"),
        "seed_status": gap.get("seed_status"),
        "label": label,
        "reversals": reversals,
        "allowed_reversals": allowed,
        "edge": detail.get("edge"),
    }


def _changed_vault(vault: Any, gap: dict[str, Any], reversals: list[str]) -> bool:
    created = gap.get("created_learning_object_id")
    if created and created not in vault.learning_objects and "undo_creation" not in reversals:
        return True
    if created and "undo_creation" in reversals and created in vault.learning_objects and (
        vault.learning_objects[created].status == "active"
    ):
        return True
    edge_ids = {edge.id for edge in vault.edges}
    if gap.get("edge_id") and (gap["edge_id"] not in edge_ids) != ("undo_edge" in reversals or "undo_creation" in reversals):
        return True
    return False


def queue_tutor_question_gap(
    ctx: SidecarContext, vault: Any, repository: Any, event_id: str, reading: dict[str, Any] | None,
) -> dict[str, Any]:
    """Queue an answered question's gap reading and wake the worker.

    Off the request path: the overlay polls :func:`get_learner_text_gap`.
    Never fails the answer.
    """

    if not vault.config.learner_text_gaps.enabled:
        return {"status": "off"}
    try:
        from learnloop.diagnosis.text_gaps.jobs import enqueue_tutor_question

        enqueue_tutor_question(vault, repository, event_id)
        ctx.post_attempt_worker.notify()
    except Exception:  # noqa: BLE001 - the answer stands without its gap reading
        logging.getLogger(__name__).warning("learner-text gap enqueue failed", exc_info=True)
        return {"status": "failed"}
    return {"status": "queued", "kind": (reading or {}).get("kind")}


@method("get_learner_text_gap", GetLearnerTextGapInput)
def get_learner_text_gap(ctx: SidecarContext, params: GetLearnerTextGapInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    if not vault.config.learner_text_gaps.enabled:
        return versioned({"status": "off", "gap": None})
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        gap = store.gap_for_source(connection, params.source_kind, params.source_id)
        job = store.job_for_source(connection, params.source_kind, params.source_id)
        reversals = [row["reversal"] for row in store.reversals(connection, [gap["id"]])] if gap else []
    if gap is None:
        state = (job or {}).get("state")
        status = "pending" if state in ("queued", "leased") else ("skipped" if state == "skipped" else "none")
        return versioned({"status": status, "gap": None})
    if _changed_vault(vault, gap, reversals):
        ctx.reload(maintenance=False)
        vault, repository = ctx.require_vault()
        repository.bump_queue_revision()
    return versioned({"status": "done", "gap": gap_view(vault, gap, reversals)})


@method("reverse_learner_text_gap", ReverseLearnerTextGapInput)
def reverse_learner_text_gap(ctx: SidecarContext, params: ReverseLearnerTextGapInput) -> dict[str, Any]:
    from learnloop.diagnosis.text_gaps.actions import UndoError, reverse_gap

    vault, repository = ctx.require_vault()
    try:
        result = reverse_gap(vault.root, repository, params.gap_id, params.reversal)
    except UndoError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        gap = store.gap(connection, params.gap_id)
        reversals = [row["reversal"] for row in store.reversals(connection, [params.gap_id])]
    return versioned({"status": result["status"], "gap": gap_view(vault, gap, reversals) if gap else None})


__all__ = ["gap_view", "get_learner_text_gap", "queue_tutor_question_gap", "reverse_learner_text_gap"]
