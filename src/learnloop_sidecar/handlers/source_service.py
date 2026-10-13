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
    "find_sources",
    "compare_sources",
    "run_source_tool",
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


class CallerInput(ParamsModel):
    """Who is asking: a kind and a reference only. The server rebuilds the
    context (item, attempt window, cold status) from its own records."""

    kind: str
    ref: str | None = None
    practice_item_id: str | None = None
    post_attempt: bool = False


class FindSourcesInput(ParamsModel):
    query: str = Field(default="", max_length=4000)
    intent: str = "explain"
    scope: str = "library"
    learning_object_ids: list[str] = Field(default_factory=list)
    facet_ids: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    expand: list[str] = Field(default_factory=list)
    exclude_span_ids: list[str] = Field(default_factory=list)
    exclude_span_keys: list[str] = Field(default_factory=list)
    target_hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    learner_work_md: str | None = Field(default=None, max_length=8000)
    personalized: bool = True
    verify: bool = False
    limit: int = Field(default=8, ge=1, le=40)
    cursor: dict[str, Any] | None = None
    policy: str | None = None
    caller: CallerInput


class CompareSourcesInput(ParamsModel):
    query: str = Field(min_length=1, max_length=4000)
    facet_ids: list[str] = Field(default_factory=list)
    requested_perspectives: list[str] = Field(default_factory=list, max_length=8)
    pinned_span_ids: list[str] = Field(default_factory=list, max_length=20)
    pinned_span_keys: list[str] = Field(default_factory=list, max_length=20)
    policy: str | None = None
    caller: CallerInput


#: Caller kinds a frontend may name for passages and comparisons.
SOURCE_CALLER_KINDS = frozenset({"tutor", "reader", "plan", "dl3_box"})


def server_caller(ctx: SidecarContext, caller: CallerInput) -> Any:
    from learnloop.instructional.policy import caller_for, caller_for_question_event

    vault, repository = ctx.require_vault()
    if caller.kind not in SOURCE_CALLER_KINDS:
        raise SidecarError("validation_error", f"Unknown caller kind {caller.kind!r}.")
    if caller.kind == "tutor":
        if not caller.ref:
            raise SidecarError("validation_error", "A tutor caller names its question event.")
        return caller_for_question_event(vault, repository, caller.ref, post_attempt=caller.post_attempt)
    if caller.practice_item_id is not None and caller.practice_item_id not in vault.practice_items:
        raise SidecarError("not_found", f"Unknown Practice Item {caller.practice_item_id}.")
    return caller_for(repository, caller.kind, caller.ref, item_id=caller.practice_item_id,
                      post_attempt=caller.post_attempt,
                      context="practice" if caller.practice_item_id and not caller.post_attempt else None)


@method("find_sources", FindSourcesInput)
def find_sources_rpc(ctx: SidecarContext, params: FindSourcesInput) -> dict[str, Any]:
    """Verbatim passages for an intent, under the caller's derived policy (S3, §9)."""

    from learnloop.instructional.sources import propose_sources
    from learnloop.source_retrieval.policy import PolicyRefused

    vault, repository = ctx.require_vault()
    caller = server_caller(ctx, params.caller)
    try:
        hits = propose_sources(
            vault, repository, params.query, caller=caller, intent=params.intent, policy=params.policy,
            scope=params.scope, learning_object_ids=params.learning_object_ids or list(caller.learning_object_ids),
            facet_ids=params.facet_ids, roles=params.roles, expand=params.expand,
            exclude_span_ids=params.exclude_span_ids, exclude_span_keys=params.exclude_span_keys,
            target_hypotheses=params.target_hypotheses, learner_work_md=params.learner_work_md,
            personalized=params.personalized, verify=params.verify, limit=params.limit, cursor=params.cursor,
        )
    except PolicyRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(hits.as_dict())


@method("compare_sources", CompareSourcesInput)
def compare_sources_rpc(ctx: SidecarContext, params: CompareSourcesInput) -> dict[str, Any]:
    """How the learner's sources treat one question: quote-verified, no consensus (S3, §9.4)."""

    from learnloop.instructional.sources import propose_comparison
    from learnloop.source_retrieval.policy import PolicyRefused

    vault, repository = ctx.require_vault()
    caller = server_caller(ctx, params.caller)
    try:
        comparison = propose_comparison(
            vault, repository, params.query, caller=caller, facet_ids=params.facet_ids,
            requested_perspectives=params.requested_perspectives, pinned_span_ids=params.pinned_span_ids,
            pinned_span_keys=params.pinned_span_keys, policy=params.policy,
        )
    except PolicyRefused as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(comparison.as_dict())


class RunSourceToolInput(ParamsModel):
    tool_call_id: str


@method("run_source_tool", RunSourceToolInput)
def run_source_tool_rpc(ctx: SidecarContext, params: RunSourceToolInput) -> dict[str, Any]:
    """Run a tool request a tutor answer carried (S4, §10.3), under the caller
    context stored with the request: the policy cannot change between the
    answer and the run. find_practice and find_sources run when the offer is
    shown; compare_sources when it is tapped."""

    from learnloop.instructional.tools import ToolArgumentsInvalid, run_requested_tool
    from learnloop.practice_index.retrieval import IntentUnavailable
    from learnloop.source_retrieval.policy import PolicyRefused
    from learnloop_sidecar.handlers.practice_index import _injected

    vault, repository = ctx.require_vault()
    try:
        result = run_requested_tool(vault, repository, params.tool_call_id, injections=_injected(vault, repository))
    except ToolArgumentsInvalid as exc:
        raise SidecarError("not_found" if exc.code == "not_found" else "validation_error", str(exc)) from exc
    except (PolicyRefused, IntentUnavailable) as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    return versioned(result)


__all__ = ["SOURCE_SERVICE_RPCS", "server_caller"]
