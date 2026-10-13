"""Learner-owned practice-item authoring RPCs: author, edit, retire, split.

Thin composition over ``learnloop.content.authoring.item_authoring`` (the Matuschak reader-control
slice: the learner edits their own collection immediately, no review gate).
Broad mutations still reload the sidecar snapshot; retirement updates its one
validated cached entity and derived serving rows directly.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.content.authoring.item_authoring import (
    ItemAuthoringError,
    author_item,
    edit_item,
    retire_item,
    split_item,
    validate_author_item,
)
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.capture import finish_route, route_intent
from learnloop_sidecar.registry import method


class AuthorPracticeItemInput(ParamsModel):
    capture_id: str | None = None
    learning_object_id: str
    prompt: str
    expected_answer: str
    practice_mode: str = "short_answer"
    hints: list[str] = Field(default_factory=list)


class EditPracticeItemInput(ParamsModel):
    practice_item_id: str
    prompt: str | None = None
    expected_answer: str | None = None
    hints: list[str] | None = None
    reason: str | None = None


class RetirePracticeItemInput(ParamsModel):
    practice_item_id: str
    reason: str
    note: str | None = None


class SplitPracticeItemPart(ParamsModel):
    prompt: str
    expected_answer: str


class SplitPracticeItemInput(ParamsModel):
    practice_item_id: str
    parts: list[SplitPracticeItemPart]
    reason: str | None = None


class RequestRungVariantInput(ParamsModel):
    practice_item_id: str
    direction: str  # easier | harder
    session_id: str | None = None


class RungVariantStatusInput(ParamsModel):
    request_id: str


class RemintDiagnosticProbeInput(ParamsModel):
    attempt_id: str


def _root(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    return vault.root, repository


def _variant_request_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": row["id"],
        "source_practice_item_id": row["source_practice_item_id"],
        "learning_object_id": row["learning_object_id"],
        "direction": row["direction"],
        "variant_kind": row.get("variant_kind") or row["direction"],
        "source_waypoint": row["source_waypoint_slug"],
        "target_waypoint": row["target_waypoint_slug"],
        "status": row["status"],
        "created_practice_item_id": row.get("created_practice_item_id"),
        "failure_reason": row.get("failure_reason"),
        "batch_id": row.get("batch_id"),
    }


@method("request_rung_variant", RequestRungVariantInput)
def request_rung_variant_rpc(ctx: SidecarContext, params: RequestRungVariantInput) -> dict[str, Any]:
    """Learner-initiated re-runging: record the request + evidence package
    synchronously, then enqueue the variant authoring job (interactive band).

    The evidence write (self_report attempt + scoped claim) happens before the
    job and is never rolled back — the request itself was real evidence. The
    reload picks up the recorded attempt's state changes immediately."""

    from learnloop.content.authoring.rung_variants import RungVariantError, request_rung_variant

    vault, repository = ctx.require_vault()
    try:
        summary = request_rung_variant(
            vault,
            repository,
            practice_item_id=params.practice_item_id,
            direction=params.direction,
            session_id=params.session_id,
        )
    except RungVariantError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    learning_object = vault.learning_objects.get(summary["learning_object_id"])
    batch_id = ctx.ingest_jobs.enqueue_rung_variant(
        request_id=summary["request_id"],
        subject_id=(learning_object.subjects[0] if learning_object and learning_object.subjects else None),
    )
    repository.update_rung_variant_request(summary["request_id"], batch_id=batch_id)
    ctx.reload(maintenance=False)
    return versioned({**summary, "batch_id": batch_id})


@method("get_rung_variant_status", RungVariantStatusInput)
def get_rung_variant_status(ctx: SidecarContext, params: RungVariantStatusInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    row = repository.rung_variant_request(params.request_id)
    if row is None:
        raise SidecarError("request_not_found", f"Unknown rung variant request {params.request_id!r}.")
    # The applying-jobs reload normally rides the ingest batch-polling RPCs,
    # which this status poll bypasses. Reload here when the applied variant is
    # not yet in the loaded vault, so the queue/requested-floor see it without
    # requiring the learner to visit the ingest screen.
    created = row.get("created_practice_item_id")
    if row["status"] == "applied" and created and created not in vault.practice_items:
        ctx.reload(maintenance=False)
    return versioned({"request": _variant_request_payload(row)})


@method("remint_diagnostic_probe", RemintDiagnosticProbeInput)
def remint_diagnostic_probe(ctx: SidecarContext, params: RemintDiagnosticProbeInput) -> dict[str, Any]:
    """Keep an administered diagnostic probe as an ordinary practice item.

    Learner-authority direct mint (see ``learnloop.diagnosis.probe_remint`` for the
    governance argument): synchronous, deterministic, no generation job. Stable
    error codes: ``attempt_not_found``, ``item_not_found``,
    ``not_a_diagnostic_probe``, ``already_reminted`` (details carry the existing
    remint's practice item id)."""

    from learnloop.diagnosis.probe_remint import ProbeRemintError, remint_probe_as_practice_item

    vault, repository = ctx.require_vault()
    try:
        summary = remint_probe_as_practice_item(
            vault.root, vault, repository, attempt_id=params.attempt_id
        )
    except ProbeRemintError as exc:
        raise SidecarError(exc.code, str(exc), details=exc.details) from exc
    ctx.reload(maintenance=False)
    return versioned(summary)


@method("author_practice_item", AuthorPracticeItemInput)
def author_practice_item(ctx: SidecarContext, params: AuthorPracticeItemInput) -> dict[str, Any]:
    root, repository = _root(ctx)
    intent = route_intent(repository, params, "make_card", create=False, ctx=ctx)
    if intent and intent.get("response"):
        response = intent["response"]
        return finish_route(ctx, repository, params.capture_id, "make_card",
                            {"practice_item_id": response["practiceItemId"]}, response, reload=True)
    try:
        if intent is None:
            vault, _ = ctx.require_vault()
            validate_author_item(vault, learning_object_id=params.learning_object_id,
                                 prompt=params.prompt, expected_answer=params.expected_answer)
            intent = route_intent(repository, params, "make_card", ctx=ctx)
        row = author_item(
            root,
            repository,
            learning_object_id=params.learning_object_id,
            prompt=params.prompt,
            expected_answer=params.expected_answer,
            practice_mode=params.practice_mode,
            hints=params.hints,
            **({"item_id": "pi_capture_" + intent["destination_id"].lower()} if intent else {}),
        )
    except ItemAuthoringError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return finish_route(ctx, repository, params.capture_id, "make_card",
                        {"practice_item_id": row["id"]}, {"practiceItemId": row["id"]}, reload=True)


@method("edit_practice_item", EditPracticeItemInput)
def edit_practice_item(ctx: SidecarContext, params: EditPracticeItemInput) -> dict[str, Any]:
    root, repository = _root(ctx)
    try:
        result = edit_item(
            root,
            repository,
            practice_item_id=params.practice_item_id,
            prompt=params.prompt,
            expected_answer=params.expected_answer,
            hints=params.hints,
            reason=params.reason,
        )
    except ItemAuthoringError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    ctx.reload(maintenance=False)
    recheck = _queue_key_recheck(ctx, params.practice_item_id) if result["changed"] else None
    response = {"practiceItemId": params.practice_item_id, "changed": result["changed"]}
    if recheck is not None:
        response["keyRecheck"] = recheck
    return versioned(response)


def _queue_key_recheck(ctx: SidecarContext, practice_item_id: str) -> str | None:
    """Canonical sources S1 (§7.3a, D20): an edited exercise import is unverified
    until a check of its NEW prompt, key and rubric passes; with
    ``exercise_verification`` on, that check is queued here (in the background).
    Its signature and response are otherwise unchanged."""

    import threading
    from contextlib import closing

    from learnloop.content.authoring.source_exercise_import import verify_item_key
    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import effective_key_status

    vault, repository = ctx.require_vault()
    service = vault.config.source_service
    item = vault.practice_items.get(practice_item_id)
    if item is None or not (service.enabled and service.exercise_verification):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        status = effective_key_status(connection, item)
    if status not in ("changed_since_check", "model_answer", "checking"):
        return None

    def run() -> None:
        try:
            verify_item_key(vault.root, repository, practice_item_id, trigger="edit")
        except Exception:  # noqa: BLE001 - `learnloop sources exercises verify` covers it
            pass

    threading.Thread(target=run, name="edit-key-recheck", daemon=True).start()
    return "queued"


@method("retire_practice_item", RetirePracticeItemInput)
def retire_practice_item(ctx: SidecarContext, params: RetirePracticeItemInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    try:
        result = retire_item(
            vault.root,
            repository,
            practice_item_id=params.practice_item_id,
            reason=params.reason,
            note=params.note,
            loaded_vault=vault,
        )
    except ItemAuthoringError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    # The primary sidecar serializes interactive calls, so replacing this one
    # validated entity keeps the in-memory snapshot coherent without a global
    # vault reload/state replay. External file changes still flow through the
    # vault watcher/incremental refresh boundary.
    vault.practice_items[params.practice_item_id] = result["item"]
    return versioned(
        {
            "practiceItemId": params.practice_item_id,
            "status": "retired",
            "queueRevision": repository.queue_revision()["revision"],
        }
    )


@method("split_practice_item", SplitPracticeItemInput)
def split_practice_item(ctx: SidecarContext, params: SplitPracticeItemInput) -> dict[str, Any]:
    root, repository = _root(ctx)
    try:
        result = split_item(
            root,
            repository,
            practice_item_id=params.practice_item_id,
            parts=[part.model_dump() for part in params.parts],
            reason=params.reason,
        )
    except ItemAuthoringError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    ctx.reload(maintenance=False)
    return versioned({"practiceItemId": params.practice_item_id, "created": result["created"]})
