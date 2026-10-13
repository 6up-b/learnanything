"""Canonical-sources service RPCs (spec_source_practice_and_probes_v1).

Desktop only (pinned in tests/test_mobile_allowlist.py). Tools propose and
existing serving paths serve (SC1): nothing here writes attempts, evidence,
mastery, FSRS, scheduler state or plan items.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from learnloop.instructional.practice import record_proposal_impressions
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
SOURCE_SERVICE_RPCS: tuple[str, ...] = (
    "record_proposal_impressions",
    "import_source_exercise",
    "get_source_exercise_import",
)


class ImpressionKey(ParamsModel):
    kind: str = "item"
    practice_item_id: str | None = None
    extraction_id: str | None = None
    span_ids: list[str] = Field(default_factory=list)


class RecordImpressionsInput(ParamsModel):
    proposal_id: str
    keys: list[ImpressionKey] = Field(default_factory=list, max_length=200)
    surface: str
    session_id: str | None = None


@method("record_proposal_impressions", RecordImpressionsInput)
def record_proposal_impressions_rpc(ctx: SidecarContext, params: RecordImpressionsInput) -> dict[str, Any]:
    """Fire-and-forget after render: which proposals a surface showed (§6.5)."""

    vault, repository = ctx.require_vault()
    try:
        result = record_proposal_impressions(
            vault, repository, proposal_id=params.proposal_id,
            keys=[key.model_dump() for key in params.keys], surface=params.surface,
            session_id=params.session_id,
        )
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ImportSourceExerciseInput(ParamsModel):
    proposal_id: str
    extraction_id: str
    span_ids: list[str] = Field(min_length=1, max_length=40)


class GetSourceExerciseImportInput(ParamsModel):
    import_id: str


@method("import_source_exercise", ImportSourceExerciseInput)
def import_source_exercise_rpc(ctx: SidecarContext, params: ImportSourceExerciseInput) -> dict[str, Any]:
    """A learner picked a textbook exercise proposal: queue its import (S1, §6.3).

    The pick is recorded at once; the job authors the exercise around its
    verbatim statement, checks the key within the time box and writes the
    item. The frontend follows it with ``get_source_exercise_import``."""

    from learnloop.db.stores.source_service import insert_import
    from learnloop.ids import new_ulid
    from learnloop.clock import utc_now_iso
    from learnloop.instructional.practice import proposed_exercise, record_exercise_pick

    vault, repository = ctx.require_vault()
    service = vault.config.source_service
    if not (service.enabled and service.exercise_arm):
        raise SidecarError("source_service_disabled", "Textbook exercise imports are switched off.")
    try:
        entry = proposed_exercise(repository, params.proposal_id, params.extraction_id, params.span_ids)
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    import_id = "sei_" + new_ulid()
    with repository.connection() as connection:
        insert_import(connection, id=import_id, created_at=utc_now_iso(), caller="learner",
                      extraction_id=params.extraction_id, span_ids=list(params.span_ids), status="authoring",
                      proposal_id=params.proposal_id, source_id=entry.get("source_id"),
                      revision_id=entry.get("revision_id"), label=entry.get("label"))
    record_exercise_pick(repository, proposal_id=params.proposal_id, entry=entry)
    batch_id = ctx.ingest_jobs.enqueue_source_exercise_import(
        import_id=import_id, extraction_id=params.extraction_id, span_ids=list(params.span_ids),
        proposal_id=params.proposal_id, label=entry.get("label"),
    )
    return versioned({"status": "queued", "import_id": import_id, "batch_id": batch_id})


@method("get_source_exercise_import", GetSourceExerciseImportInput)
def get_source_exercise_import_rpc(ctx: SidecarContext, params: GetSourceExerciseImportInput) -> dict[str, Any]:
    """An import's status, its key's honest label and, once written, the item id."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.source_service import KEY_STATUS_LABELS, effective_key_status, import_row

    vault, repository = ctx.require_vault()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = import_row(connection, params.import_id)
        if row is None:
            raise SidecarError("not_found", f"Unknown import {params.import_id}.")
        item = vault.practice_items.get(row["practice_item_id"]) if row.get("practice_item_id") else None
        key_status = effective_key_status(connection, item) if item is not None else row.get("key_status")
    return versioned({
        "import_id": row["id"], "status": row["status"], "reason": row.get("reason"),
        "practice_item_id": row.get("practice_item_id"), "label": row.get("label"),
        "key_status": key_status, "key_label": KEY_STATUS_LABELS.get(key_status or "", ""),
        "validation": row.get("validation") or {},
    })


__all__ = ["SOURCE_SERVICE_RPCS"]
