"""P2 reader-dialogue sidecar RPC (spec §7.6, U-033; design B.11).

The Python layer of the five-layer recipe for the minimal bidirectional reader
dialogue: the learner->AI Ask, the per-ask answer-mode toggle, owner-placed
reading questions (present/submit/skip), the four-disposition picker, source
restoration, and the replay-derived routing-prior projection. Handlers compose
``services.reader_dialogue`` (+ ``tutor_qa``) and never touch SQL directly.

Method names are dotted (``reader.*``) so the Tauri client maps them 1:1. The
reader ships enabled by default (``tutor_qa.reader_enabled``, owner-flippable), with
a per-source opt-out chosen at ingest (migration 104); the golden path still
completes without ever invoking these (spec §12.3.2).

L8 gating (single-owner threat model): every mutating/answering ``reader.*`` RPC
is gated server-side on ``reader_enabled`` -- ``reader.prompt_contract`` is the sole
exception, because it REPORTS the flag (so a UI can discover the reader is off). Even
in the single-owner local deployment this gate matters: the flag is the one place the
owner turns the reader off, and a client that ignores it (a stale build, a scripted
call) must not be able to open reader exchanges the owner disabled. The service is the
authority; the handler enforces it rather than trusting the caller.
"""

from __future__ import annotations

from typing import Any

from learnloop.codex.client import CodexUnavailable
from learnloop.services import reader_dialogue as RD
from learnloop.services import reader_guidance as RG
from learnloop.services.tutor_qa import QuestionLimitReached, TutorQAError
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import provider_label, ready_tutor_qa_provider
from learnloop_sidecar.registry import method


def _require_reader(ctx: SidecarContext):
    """Require an open vault AND the reader enabled (L8). Every mutating/answering
    ``reader.*`` RPC gates on this; only ``reader.prompt_contract`` (which REPORTS the
    flag) is exempt."""

    vault, repository = ctx.require_vault()
    if not RD.reader_enabled(vault):
        raise SidecarError(
            "reader_disabled",
            "The reader dialogue is disabled (tutor_qa.reader_enabled=False).",
        )
    return vault, repository


def _require_source_reader(repository, source_id: str) -> dict[str, Any]:
    """Per-source reader gate (owner ingest-time choice, migration 104): a source
    opted out of the reader loop (e.g. a practice exam) refuses reader surfaces."""

    artifact = repository.get_source_artifact(source_id)
    if artifact is None:
        raise SidecarError("source_not_found", f"Unknown source {source_id!r}.")
    if not artifact.get("reader_enabled", 1):
        raise SidecarError(
            "reader_disabled_for_source",
            f"Source {source_id!r} was ingested with the reader off (per-source setting).",
        )
    return artifact


def _source_id_for_extraction(repository, extraction_id: str) -> str | None:
    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return None
    revision = repository.get_source_revision(run["revision_id"])
    return revision["source_id"] if revision else None


# ---------------------------------------------------------------------------
# reader.ask (learner -> AI)
# ---------------------------------------------------------------------------

class ReaderAskInput(ParamsModel):
    extraction_id: str
    span_id: str
    question: str
    answer_mode: str = RD.READER_ANSWER_MODE_DEFAULT
    target_key: str | None = None
    revealed_surface_ids: list[str] = []
    cold_active: bool = False
    cold_attempt_id: str | None = None


@method("reader.ask", ReaderAskInput)
def reader_ask(ctx: SidecarContext, params: ReaderAskInput) -> dict[str, Any]:
    vault, repository = _require_reader(ctx)
    ask_source_id = _source_id_for_extraction(repository, params.extraction_id)
    if ask_source_id is not None:
        _require_source_reader(repository, ask_source_id)
    provider_name, runtime, client = ready_tutor_qa_provider(vault)
    if not runtime.ready or client is None:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for reader Ask.",
            retryable=True,
        )
    try:
        result = RD.ask(
            vault,
            repository,
            client,
            extraction_id=params.extraction_id,
            span_id=params.span_id,
            question_md=params.question,
            answer_mode=params.answer_mode,
            target_key=params.target_key,
            revealed_surface_ids=params.revealed_surface_ids,
            cold_active=params.cold_active,
            cold_attempt_id=params.cold_attempt_id,
        )
    except QuestionLimitReached as exc:
        raise SidecarError(
            "question_limit_reached",
            str(exc),
            details={"limit": exc.limit, "used": exc.used, "context": exc.context},
        ) from exc
    except (RD.ReaderDialogueError, TutorQAError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    except (CodexUnavailable, TimeoutError) as exc:
        raise SidecarError(
            "provider_unavailable",
            f"{provider_label(provider_name)} is unavailable for reader Ask.",
            retryable=True,
        ) from exc
    return versioned(
        {
            "event_id": result["event_id"],
            "reader_answer_event_id": result["reader_answer_event_id"],
            "answer_md": result["answer_md"],
            "answer_mode": result["answer_mode"],
            "citations": result["citations"],
            "manifest": result["manifest"],
            "warmed_surface_ids": result["warmed_surface_ids"],
            "burned_surface_ids": result["burned_surface_ids"],
            "hint_equivalent": result["hint_equivalent"],
            "remaining": result["remaining"],
        }
    )


class ReaderAskHistoryInput(ParamsModel):
    extraction_id: str


@method("reader.ask_history", ReaderAskHistoryInput)
def reader_ask_history(ctx: SidecarContext, params: ReaderAskHistoryInput) -> dict[str, Any]:
    """List the durable, completed Ask exchanges for the open source."""

    _vault, repository = _require_reader(ctx)
    source_id = _source_id_for_extraction(repository, params.extraction_id)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    return versioned({"exchanges": RD.ask_history(repository, extraction_id=params.extraction_id)})


class ReaderSetAnswerModeInput(ParamsModel):
    extraction_id: str
    span_id: str
    answer_mode: str


@method("reader.set_answer_mode", ReaderSetAnswerModeInput)
def reader_set_answer_mode(ctx: SidecarContext, params: ReaderSetAnswerModeInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        event_id = RD.set_answer_mode(
            repository,
            extraction_id=params.extraction_id,
            span_id=params.span_id,
            answer_mode=params.answer_mode,
        )
    except RD.ReaderDialogueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"event_id": event_id, "answer_mode": params.answer_mode})


# ---------------------------------------------------------------------------
# reader.present_question / submit / skip (AI -> learner, owner-placed)
# ---------------------------------------------------------------------------

class ReaderPresentQuestionInput(ParamsModel):
    practice_item_id: str
    reading_phase: str
    goal_id: str | None = None
    target_contract_version_id: str | None = None


@method("reader.present_question", ReaderPresentQuestionInput)
def reader_present_question(ctx: SidecarContext, params: ReaderPresentQuestionInput) -> dict[str, Any]:
    vault, repository = _require_reader(ctx)
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("validation_error", f"Practice item {params.practice_item_id} not found.")
    try:
        result = RD.administer_reading_question(
            vault,
            repository,
            item,
            reading_phase=params.reading_phase,
            goal_id=params.goal_id,
            target_contract_version_id=params.target_contract_version_id,
        )
    except RD.ReaderDialogueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderSubmitQuestionInput(ParamsModel):
    administration_id: str
    response: str | None = None
    target_key: str | None = None
    outcome_class: str = "unknown"


@method("reader.submit_question", ReaderSubmitQuestionInput)
def reader_submit_question(ctx: SidecarContext, params: ReaderSubmitQuestionInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    event_id = RD.submit_reading_question(
        repository,
        administration_id=params.administration_id,
        response_md=params.response,
        target_key=params.target_key,
        outcome_class=params.outcome_class,
    )
    return versioned({"event_id": event_id})


class ReaderSkipQuestionInput(ParamsModel):
    administration_id: str


@method("reader.skip_question", ReaderSkipQuestionInput)
def reader_skip_question(ctx: SidecarContext, params: ReaderSkipQuestionInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    event_id = RD.skip_reading_question(repository, administration_id=params.administration_id)
    return versioned({"event_id": event_id, "signal": "interaction_policy"})


# ---------------------------------------------------------------------------
# reader.choose_disposition (four dispositions)
# ---------------------------------------------------------------------------

class ReaderChooseDispositionInput(ParamsModel):
    disposition: str
    subject_id: str
    subject_type: str = "reader_span"
    commitment_target: dict[str, Any] | None = None
    goal_id: str | None = None
    client_idempotency_key: str | None = None


@method("reader.choose_disposition", ReaderChooseDispositionInput)
def reader_choose_disposition(ctx: SidecarContext, params: ReaderChooseDispositionInput) -> dict[str, Any]:
    vault, repository = _require_reader(ctx)
    try:
        result = RD.choose_disposition(
            vault,
            repository,
            disposition=params.disposition,
            subject_id=params.subject_id,
            subject_type=params.subject_type,
            commitment_target=params.commitment_target,
            goal_id=params.goal_id,
            client_idempotency_key=params.client_idempotency_key,
        )
    except RD.ReaderDialogueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


# ---------------------------------------------------------------------------
# reader.restore_source
# ---------------------------------------------------------------------------

class ReaderRestoreSourceInput(ParamsModel):
    extraction_id: str
    span_id: str
    cold_surface_id: str | None = None
    cold_administration_id: str | None = None


@method("reader.restore_source", ReaderRestoreSourceInput)
def reader_restore_source(ctx: SidecarContext, params: ReaderRestoreSourceInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = RD.restore_source(
            repository,
            extraction_id=params.extraction_id,
            span_id=params.span_id,
            cold_surface_id=params.cold_surface_id,
            cold_administration_id=params.cold_administration_id,
        )
    except RD.ReaderDialogueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


# ---------------------------------------------------------------------------
# reader.routing_prior (read-only projection) + reader.prompt_contract (review)
# ---------------------------------------------------------------------------

class ReaderRoutingPriorInput(ParamsModel):
    target_key: str
    cold_observation_at: str | None = None


@method("reader.routing_prior", ReaderRoutingPriorInput)
def reader_routing_prior(ctx: SidecarContext, params: ReaderRoutingPriorInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    projection = RD.routing_prior_projection_v1(
        repository,
        target_key=params.target_key,
        cold_observation_at=params.cold_observation_at,
    )
    return versioned(projection)


@method("reader.prompt_contract")
def reader_prompt_contract(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    vault, _repository = ctx.require_vault()
    contract = RD.reader_prompt_contract()
    contract["reader_enabled"] = RD.reader_enabled(vault)
    return versioned(contract)


# ---------------------------------------------------------------------------
# P3 slice 1: render views + crosswalk, block health + crop fallback,
# annotations, and the local-first capture/outbox spine (spec §3-5, §8).
# The Python sidecar owns all anchoring/persistence; TS ships raw display
# selection only (design §A.2). Every P3 reader method gates on reader_enabled
# for parity with the P2 dialogue; local capture never waits for a model job.
# ---------------------------------------------------------------------------

from learnloop.services import annotations as ANN  # noqa: E402
from learnloop.services import block_health as BH  # noqa: E402
from learnloop.services import reader_capture as RC  # noqa: E402
from learnloop.services import source_render_views as RV  # noqa: E402
from learnloop.services import span_view as SV  # noqa: E402
from learnloop.services.source_outline import resolve_extraction_id  # noqa: E402


class ReaderRenderViewInput(ParamsModel):
    # Accepts an extraction id, a revision id, or a source-artifact id — resolved
    # through ``resolve_extraction_id`` so the library can open a source directly.
    extraction_id: str
    revision_id: str | None = None


@method("reader.render_view", ReaderRenderViewInput)
def reader_render_view(ctx: SidecarContext, params: ReaderRenderViewInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError(
            "extraction_not_found", f"No extraction resolves for {params.extraction_id!r}."
        )
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    try:
        view = RV.resolve_or_create_render_view(
            repository,
            extraction_id=resolved,
            revision_id=params.revision_id if resolved == params.extraction_id else None,
        )
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    # Opening a source is the natural moment to resume draining any synthesis
    # requests left queued by a previous session (spec §6.4).
    ctx.ingest_jobs.kick_reader_drain()
    return versioned(RV.render_payload(repository, view["id"]))


class ReaderGuidePlanInput(ParamsModel):
    # Accepts the same extraction/revision/source identifiers as render_view.
    extraction_id: str


@method("reader.guide_plan", ReaderGuidePlanInput)
def reader_guide_plan(ctx: SidecarContext, params: ReaderGuidePlanInput) -> dict[str, Any]:
    """Return optional section-break checks and a personalized second pass.

    Questions come only from reviewed TaskBlueprint placements. Learner state
    ranks restorative passages and supplies plain-language context locally; no
    posterior values enter an AI prompt or the response. A question is not
    administered until the learner elects to answer it.
    """

    vault, repository = _require_reader(ctx)
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError(
            "extraction_not_found", f"No extraction resolves for {params.extraction_id!r}."
        )
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    try:
        return versioned(RG.build_guide_plan(vault, repository, extraction_id=resolved))
    except ValueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class ReaderBlockHealthInput(ParamsModel):
    extraction_id: str
    span_id: str


@method("reader.block_health", ReaderBlockHealthInput)
def reader_block_health(ctx: SidecarContext, params: ReaderBlockHealthInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    row = repository.block_health(params.extraction_id, params.span_id)
    if row is None:
        ir = repository.load_document_ir(params.extraction_id)
        block = ir.block_by_span(params.span_id) if ir is not None else None
        if block is None:
            raise SidecarError("validation_error", "unknown block")
        page_health = None
        if block.page is not None and ir is not None:
            page_health = next((p for p in ir.health.pages if p.page == block.page), None)
        computed = BH.analyze_block_health(block, page_health)
        repository.upsert_block_health({**computed, "extraction_id": params.extraction_id})
        row = repository.block_health(params.extraction_id, params.span_id)
    return versioned(dict(row or {}))


class ReaderBlockRegionInput(ParamsModel):
    extraction_id: str
    span_id: str


@method("reader.block_original_region", ReaderBlockRegionInput)
def reader_block_original_region(ctx: SidecarContext, params: ReaderBlockRegionInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned(SV.build_block_region(repository, params.extraction_id, params.span_id))


class ReaderPdfViewInput(ParamsModel):
    # Same resolution rules as reader.render_view: extraction, revision, or
    # source-artifact id.
    extraction_id: str


@method("reader.pdf_view", ReaderPdfViewInput)
def reader_pdf_view(ctx: SidecarContext, params: ReaderPdfViewInput) -> dict[str, Any]:
    """Tier-2 embedded PDF reader manifest: whether the revision's original PDF
    is available in the vault's content-addressed store (backfilling it from a
    still-present local original on demand), the store file name the llpdf://
    protocol serves, and per-block page/bbox geometry (PDF points, origin
    top-left) for highlight overlay + selection→span hit-testing."""

    from learnloop.ingest.originals import backfill_original, is_pdf_file, stored_original_path

    vault, repository = _require_reader(ctx)
    resolved = resolve_extraction_id(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError(
            "extraction_not_found", f"No extraction resolves for {params.extraction_id!r}."
        )
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    run = repository.get_extraction_run(resolved) or {}
    revision = repository.get_source_revision(run.get("revision_id")) if run.get("revision_id") else None
    digest = (revision or {}).get("asset_hash")
    stored = stored_original_path(vault.root, digest)
    if stored is None and digest:
        _status, stored = backfill_original(
            vault.root, digest=digest, original_uri=(revision or {}).get("original_uri")
        )
    available = stored is not None and is_pdf_file(stored)
    blocks: list[dict[str, Any]] = []
    if available:
        ir = repository.load_document_ir(resolved)
        for block in sorted(ir.blocks, key=lambda b: b.ordinal) if ir is not None else []:
            if block.page is None or not block.bbox:
                continue
            blocks.append(
                {
                    "span_id": block.span_id,
                    "page": block.page,
                    "bbox": list(block.bbox),
                    "block_type": block.block_type,
                    # Extraction text rides along so block-snapped selections can
                    # send the source-owned text as the quote — glyph text off the
                    # pdf.js layer diverges from extraction text (dropped/LaTeX
                    # math) and can never anchor exactly.
                    "text": block.text,
                }
            )
    return versioned(
        {
            "available": available,
            "file_name": stored.name if available and stored is not None else None,
            "extraction_id": resolved,
            "source_id": source_id,
            "revision_id": run.get("revision_id"),
            "blocks": blocks,
        }
    )


class ReaderTranslateSelectionInput(ParamsModel):
    extraction_id: str
    raw_selection: dict[str, Any]
    render_view_id: str | None = None


@method("reader.translate_selection", ReaderTranslateSelectionInput)
def reader_translate_selection(ctx: SidecarContext, params: ReaderTranslateSelectionInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned(
        ANN.translate_selection(
            repository, extraction_id=params.extraction_id,
            raw_selection=params.raw_selection, render_view_id=params.render_view_id,
        )
    )


class ReaderCaptureInput(ParamsModel):
    source_id: str
    revision_id: str
    extraction_id: str
    action: str
    client_idempotency_key: str
    raw_selection: dict[str, Any] | None = None
    render_view_id: str | None = None
    learner_text: str = ""
    what_i_think_is_going_on: str | None = None
    session_id: str | None = None


@method("reader.capture", ReaderCaptureInput)
def reader_capture(ctx: SidecarContext, params: ReaderCaptureInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        receipt = RC.capture(
            repository,
            source_id=params.source_id,
            revision_id=params.revision_id,
            extraction_id=params.extraction_id,
            action=params.action,
            client_idempotency_key=params.client_idempotency_key,
            raw_selection=params.raw_selection,
            render_view_id=params.render_view_id,
            learner_text=params.learner_text,
            what_i_think_is_going_on=params.what_i_think_is_going_on,
            session_id=params.session_id,
        )
    except (RC.CaptureError, ANN.AnnotationError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(receipt)


class ReaderCreateAnnotationInput(ParamsModel):
    source_id: str
    revision_id: str
    extraction_id: str
    annotation_type: str
    raw_selection: dict[str, Any]
    learner_text: str = ""
    what_i_think_is_going_on: str | None = None
    render_view_id: str | None = None
    client_idempotency_key: str | None = None


@method("reader.create_annotation", ReaderCreateAnnotationInput)
def reader_create_annotation(ctx: SidecarContext, params: ReaderCreateAnnotationInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    translation = ANN.translate_selection(
        repository, extraction_id=params.extraction_id,
        raw_selection=params.raw_selection, render_view_id=params.render_view_id,
    )
    try:
        result = ANN.append_annotation(
            repository, source_id=params.source_id, revision_id=params.revision_id,
            extraction_id=params.extraction_id, annotation_type=params.annotation_type,
            learner_text=params.learner_text, what_i_think_is_going_on=params.what_i_think_is_going_on,
            translation=translation, render_view_id=params.render_view_id,
            client_idempotency_key=params.client_idempotency_key,
        )
    except ANN.AnnotationError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderEditAnnotationInput(ParamsModel):
    annotation_id: str
    learner_text: str | None = None
    what_i_think_is_going_on: str | None = None
    annotation_type: str | None = None


@method("reader.edit_annotation", ReaderEditAnnotationInput)
def reader_edit_annotation(ctx: SidecarContext, params: ReaderEditAnnotationInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = ANN.edit_annotation(
            repository, annotation_id=params.annotation_id, learner_text=params.learner_text,
            what_i_think_is_going_on=params.what_i_think_is_going_on, annotation_type=params.annotation_type,
        )
    except ANN.AnnotationError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderDeleteIntentInput(ParamsModel):
    annotation_id: str
    reason: str | None = None


@method("reader.delete_intent_annotation", ReaderDeleteIntentInput)
def reader_delete_intent_annotation(ctx: SidecarContext, params: ReaderDeleteIntentInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    event_id = ANN.delete_intent_annotation(repository, annotation_id=params.annotation_id, reason=params.reason)
    return versioned({"event_id": event_id})


class ReaderReanchorInput(ParamsModel):
    annotation_id: str
    new_extraction_id: str


@method("reader.reanchor", ReaderReanchorInput)
def reader_reanchor(ctx: SidecarContext, params: ReaderReanchorInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = ANN.reanchor_annotation(
            repository, annotation_id=params.annotation_id, new_extraction_id=params.new_extraction_id
        )
    except ANN.AnnotationError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderAnnotationHistoryInput(ParamsModel):
    annotation_id: str


@method("reader.annotation_history", ReaderAnnotationHistoryInput)
def reader_annotation_history(ctx: SidecarContext, params: ReaderAnnotationHistoryInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    head = repository.annotation_head(params.annotation_id)
    history = repository.annotation_history(params.annotation_id)
    return versioned({"head": head, "history": history})


class ReaderSourceAnnotationsInput(ParamsModel):
    source_id: str


@method("reader.source_annotations", ReaderSourceAnnotationsInput)
def reader_source_annotations(ctx: SidecarContext, params: ReaderSourceAnnotationsInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned({"annotations": repository.annotations_for_source(params.source_id)})


class ReaderOutboxStatusInput(ParamsModel):
    client_idempotency_key: str


@method("reader.outbox_status", ReaderOutboxStatusInput)
def reader_outbox_status(ctx: SidecarContext, params: ReaderOutboxStatusInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    row = RC.outbox_status(repository, client_idempotency_key=params.client_idempotency_key)
    return versioned({"outbox": row})


@method("reader.drain_outbox")
def reader_drain_outbox(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    result = RC.drain_outbox(repository)
    # Outbox conversion may have enqueued demand-paged synthesis requests; make
    # sure the background worker is up to drain them (spec §6.4).
    ctx.ingest_jobs.kick_reader_drain()
    return versioned(result)


# ---------------------------------------------------------------------------
# P3 slice 2: nine-preset palette + mode/question controls, demand-paged
# synthesis (reader_background_requests), and source objects / proposals
# (spec §5-§7, design B steps 5-7). Local capture NEVER waits on a model job;
# synthesis is enqueued and drained by a separate worker; results are reviewable
# proposals, never auto-admitted into pools/evidence (§6.4).
# ---------------------------------------------------------------------------

from learnloop.services import reader_requests as RR  # noqa: E402
from learnloop.services import source_objects as SO  # noqa: E402


class ReaderInvokePresetInput(ParamsModel):
    preset: str
    source_id: str
    revision_id: str
    extraction_id: str
    client_idempotency_key: str
    raw_selection: dict[str, Any] | None = None
    render_view_id: str | None = None
    learner_text: str = ""
    what_i_think_is_going_on: str | None = None
    subject_id: str | None = None
    session_id: str | None = None


@method("reader.invoke_preset", ReaderInvokePresetInput)
def reader_invoke_preset(ctx: SidecarContext, params: ReaderInvokePresetInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        receipt = RC.invoke_preset(
            repository,
            preset=params.preset,
            source_id=params.source_id,
            revision_id=params.revision_id,
            extraction_id=params.extraction_id,
            client_idempotency_key=params.client_idempotency_key,
            raw_selection=params.raw_selection,
            render_view_id=params.render_view_id,
            learner_text=params.learner_text,
            what_i_think_is_going_on=params.what_i_think_is_going_on,
            subject_id=params.subject_id,
            session_id=params.session_id,
        )
    except (RC.CaptureError, ANN.AnnotationError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(receipt)


class ReaderSetModeInput(ParamsModel):
    mode: str
    extraction_id: str | None = None
    session_id: str | None = None


@method("reader.set_mode", ReaderSetModeInput)
def reader_set_mode(ctx: SidecarContext, params: ReaderSetModeInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = RD.set_mode(
            repository, mode=params.mode, extraction_id=params.extraction_id, session_id=params.session_id
        )
    except RD.ReaderDialogueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderQuestionControlInput(ParamsModel):
    control: str
    administration_id: str | None = None
    subject_id: str | None = None
    subject_type: str = "reader_span"


@method("reader.question_control", ReaderQuestionControlInput)
def reader_question_control(ctx: SidecarContext, params: ReaderQuestionControlInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = RD.question_control(
            repository, control=params.control, administration_id=params.administration_id,
            subject_id=params.subject_id, subject_type=params.subject_type,
        )
    except RD.ReaderDialogueError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderEnqueueRequestInput(ParamsModel):
    source_id: str
    revision_id: str
    extraction_id: str
    span_id: str
    preset: str
    provider: str = "stub"
    model: str = "stub-1"
    annotation_id: str | None = None
    commitment_id: str | None = None
    client_idempotency_key: str | None = None


@method("reader.enqueue_request", ReaderEnqueueRequestInput)
def reader_enqueue_request(ctx: SidecarContext, params: ReaderEnqueueRequestInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = RR.enqueue_request(
            repository, source_id=params.source_id, revision_id=params.revision_id,
            extraction_id=params.extraction_id, span_id=params.span_id, preset=params.preset,
            provider=params.provider, model=params.model, annotation_id=params.annotation_id,
            commitment_id=params.commitment_id, client_idempotency_key=params.client_idempotency_key,
        )
    except RR.ReaderRequestError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    ctx.ingest_jobs.kick_reader_drain()
    return versioned(result)


class ReaderRequestStatusInput(ParamsModel):
    request_id: str


@method("reader.request_status", ReaderRequestStatusInput)
def reader_request_status(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned({"request": RR.request_status(repository, request_id=params.request_id)})


@method("reader.cancel_request", ReaderRequestStatusInput)
def reader_cancel_request(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned({"request": RR.cancel_request(repository, request_id=params.request_id)})


@method("reader.retry_request", ReaderRequestStatusInput)
def reader_retry_request(ctx: SidecarContext, params: ReaderRequestStatusInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    result = RR.retry_request(repository, request_id=params.request_id)
    ctx.ingest_jobs.kick_reader_drain()
    return versioned({"request": result})


class ReaderSourceRequestsInput(ParamsModel):
    source_id: str


@method("reader.source_requests", ReaderSourceRequestsInput)
def reader_source_requests(ctx: SidecarContext, params: ReaderSourceRequestsInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned({"requests": repository.reader_requests_for_source(params.source_id)})


@method("reader.drain_requests")
def reader_drain_requests(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned(RR.drain_requests(repository))


class ReaderSourceObjectsInput(ParamsModel):
    source_id: str


@method("reader.source_objects", ReaderSourceObjectsInput)
def reader_source_objects(ctx: SidecarContext, params: ReaderSourceObjectsInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned({"source_objects": SO.source_objects_for_source(repository, source_id=params.source_id)})


class ReaderReviewSourceObjectInput(ParamsModel):
    source_object_id: str
    status: str


@method("reader.review_source_object", ReaderReviewSourceObjectInput)
def reader_review_source_object(ctx: SidecarContext, params: ReaderReviewSourceObjectInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = SO.review_source_object(
            repository, source_object_id=params.source_object_id, status=params.status
        )
    except SO.SourceObjectError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderLinkRelationInput(ParamsModel):
    source_object_id: str
    related_object_id: str | None = None
    relation_type: str = SO.CONNECT_IT_RELATION
    learner_text: str | None = None


@method("reader.link_relation", ReaderLinkRelationInput)
def reader_link_relation(ctx: SidecarContext, params: ReaderLinkRelationInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = SO.link_relation(
            repository, source_object_id=params.source_object_id,
            related_object_id=params.related_object_id, relation_type=params.relation_type,
            learner_text=params.learner_text,
        )
    except SO.SourceObjectError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderProposalInboxInput(ParamsModel):
    status: str = "proposed"
    source_object_id: str | None = None


@method("reader.proposal_inbox", ReaderProposalInboxInput)
def reader_proposal_inbox(ctx: SidecarContext, params: ReaderProposalInboxInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned(SO.proposal_inbox(repository, status=params.status, source_object_id=params.source_object_id))


class ReaderDecideProposalInput(ParamsModel):
    proposal_id: str


@method("reader.accept_proposal", ReaderDecideProposalInput)
def reader_accept_proposal(ctx: SidecarContext, params: ReaderDecideProposalInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = SO.accept_mapping(repository, proposal_id=params.proposal_id)
    except SO.SourceObjectError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"proposal": result})


@method("reader.reject_proposal", ReaderDecideProposalInput)
def reader_reject_proposal(ctx: SidecarContext, params: ReaderDecideProposalInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = SO.reject_mapping(repository, proposal_id=params.proposal_id)
    except SO.SourceObjectError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"proposal": result})


# ---------------------------------------------------------------------------
# P3 slice 3: learner Q+A authoring + coach + maintenance, commitment arcs +
# depth controls + primes, and post-cold reader restoration (spec §9-§11,
# design B steps 8-10). Authoring persists Q+A BEFORE any AI; arcs compose the P1
# commitment/depth substrate and never widen an envelope or create an edge; reading
# events remain salience-only (firewall §C).
# ---------------------------------------------------------------------------

from learnloop.services import commitment_arcs as ARC  # noqa: E402
from learnloop.services import commitments as CMT  # noqa: E402
from learnloop.services import reader_authoring as AUTH  # noqa: E402
from learnloop.services import reader_restoration as REST  # noqa: E402

# Commitment-layer domain errors surfaced by authoring (§9): validation, not a crash.
C_ERR = (CMT.InvalidTarget, CMT.PassiveActionCannotCommit, CMT.UnknownCommitment)


class ReaderAuthorQAInput(ParamsModel):
    question: str
    answer: str
    source_id: str | None = None
    revision_id: str | None = None
    annotation_id: str | None = None
    subject_id: str | None = None
    depth_preset: str = "remember_key_ideas"
    client_idempotency_key: str | None = None


@method("reader.author_qa", ReaderAuthorQAInput)
def reader_author_qa(ctx: SidecarContext, params: ReaderAuthorQAInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = AUTH.author_qa(
            repository, question=params.question, answer=params.answer,
            source_id=params.source_id, revision_id=params.revision_id,
            annotation_id=params.annotation_id, subject_id=params.subject_id,
            depth_preset=params.depth_preset, client_idempotency_key=params.client_idempotency_key,
        )
    except (AUTH.AuthoringError, C_ERR) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderCoachLintInput(ParamsModel):
    question: str
    answer: str
    level: str = "expert"


@method("reader.coach_lint", ReaderCoachLintInput)
def reader_coach_lint(ctx: SidecarContext, params: ReaderCoachLintInput) -> dict[str, Any]:
    _require_reader(ctx)
    try:
        result = AUTH.coach_lint(question=params.question, answer=params.answer, level=params.level)
    except AUTH.AuthoringError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderMaintainInput(ParamsModel):
    action: str
    lineage_id: str | None = None
    from_card_version_id: str | None = None
    to_card_version_id: str | None = None
    prev_contract: dict[str, Any] | None = None
    new_contract: dict[str, Any] | None = None
    into_lineage_id: str | None = None
    merged_card_version_id: str | None = None
    split_card_version_id: str | None = None
    forked_card_version_id: str | None = None
    commitment_id: str | None = None
    policy: str | None = None
    bounds: dict[str, Any] | None = None


@method("reader.maintain", ReaderMaintainInput)
def reader_maintain(ctx: SidecarContext, params: ReaderMaintainInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        result = AUTH.maintain(
            repository, action=params.action, lineage_id=params.lineage_id,
            from_card_version_id=params.from_card_version_id,
            to_card_version_id=params.to_card_version_id,
            prev_contract=params.prev_contract, new_contract=params.new_contract,
            into_lineage_id=params.into_lineage_id, merged_card_version_id=params.merged_card_version_id,
            split_card_version_id=params.split_card_version_id,
            forked_card_version_id=params.forked_card_version_id,
            commitment_id=params.commitment_id, policy=params.policy, bounds=params.bounds,
        )
    except (AUTH.AuthoringError, C_ERR) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)


class ReaderArcInput(ParamsModel):
    arc_id: str | None = None
    commitment_id: str | None = None
    source_id: str | None = None


@method("reader.arc", ReaderArcInput)
def reader_arc(ctx: SidecarContext, params: ReaderArcInput) -> dict[str, Any]:
    """Create an arc (with ``commitment_id``) or project an existing one (``arc_id``)."""
    _vault, repository = _require_reader(ctx)
    try:
        if params.arc_id is not None:
            return versioned(ARC.project_arc(repository, arc_id=params.arc_id))
        if params.commitment_id is None:
            raise ARC.ArcError("arc requires arc_id or commitment_id")
        return versioned(
            ARC.create_arc(repository, commitment_id=params.commitment_id, source_id=params.source_id)
        )
    except ARC.ArcError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class ReaderSetDepthPolicyInput(ParamsModel):
    arc_id: str
    policy: str


@method("reader.set_depth_policy", ReaderSetDepthPolicyInput)
def reader_set_depth_policy(ctx: SidecarContext, params: ReaderSetDepthPolicyInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        return versioned(ARC.set_depth_policy(repository, arc_id=params.arc_id, policy=params.policy))
    except ARC.ArcError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class ReaderArcIdInput(ParamsModel):
    arc_id: str
    reason: str | None = None


@method("reader.pause_arc", ReaderArcIdInput)
def reader_pause_arc(ctx: SidecarContext, params: ReaderArcIdInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        return versioned(ARC.pause_arc(repository, arc_id=params.arc_id, reason=params.reason))
    except ARC.ArcError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class ReaderShrinkEnvelopeInput(ParamsModel):
    arc_id: str
    bounds: dict[str, Any]
    reviewed_edges: list[dict[str, Any]] = []


@method("reader.shrink_envelope", ReaderShrinkEnvelopeInput)
def reader_shrink_envelope(ctx: SidecarContext, params: ReaderShrinkEnvelopeInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        return versioned(
            ARC.shrink_envelope(
                repository, arc_id=params.arc_id, bounds=params.bounds,
                reviewed_edges=params.reviewed_edges,
            )
        )
    except (ARC.ArcError, CMT.EnvelopeWideningRejected) as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class ReaderPrimeInput(ParamsModel):
    arc_id: str
    question_ref: str
    section: str | None = None
    answer: bool = False
    gave_up: bool = False


@method("reader.prime", ReaderPrimeInput)
def reader_prime(ctx: SidecarContext, params: ReaderPrimeInput) -> dict[str, Any]:
    """Offer (default) or answer (``answer=True``) an opt-in pretest prime (§10.3)."""
    _vault, repository = _require_reader(ctx)
    try:
        if params.answer:
            return versioned(
                ARC.answer_prime(repository, arc_id=params.arc_id, question_ref=params.question_ref,
                                 gave_up=params.gave_up)
            )
        return versioned(
            ARC.offer_prime(repository, arc_id=params.arc_id, question_ref=params.question_ref,
                            section=params.section)
        )
    except ARC.ArcError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


class ReaderRestoreInput(ParamsModel):
    source_id: str
    extraction_id: str | None = None
    run_id: str | None = None
    idempotency_key: str | None = None


@method("reader.restore", ReaderRestoreInput)
def reader_restore(ctx: SidecarContext, params: ReaderRestoreInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        return versioned(
            REST.restore(
                repository, source_id=params.source_id, extraction_id=params.extraction_id,
                run_id=params.run_id, idempotency_key=params.idempotency_key,
            )
        )
    except REST.ReaderRestorationError as exc:
        raise SidecarError("validation_error", str(exc)) from exc


# ---------------------------------------------------------------------------
# reader.watch_plan — YouTube watch mode (owner request 2026-07-20). Returns the
# embeddable video id plus tutor pause points derived from practice items whose
# provenance cites this video with time_range locators: the player pauses after
# a cited segment ends and administers that item as an instructional reading
# question (never certification-eligible).
# ---------------------------------------------------------------------------

_TIME_LOCATOR_RE = __import__("re").compile(r"^t=(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?$")


def _parse_time_locator(locator: str | None) -> tuple[float, float | None] | None:
    if not locator:
        return None
    match = _TIME_LOCATOR_RE.match(locator.strip())
    if match is None:
        return None
    start = float(match.group(1))
    end = float(match.group(2)) if match.group(2) is not None else None
    return start, end


class ReaderWatchPlanInput(ParamsModel):
    source_id: str


@method("reader.watch_plan", ReaderWatchPlanInput)
def reader_watch_plan(ctx: SidecarContext, params: ReaderWatchPlanInput) -> dict[str, Any]:
    from learnloop.ingest.fetchers import youtube_video_id
    from learnloop.ingest.models import UnsupportedSourceError

    vault, repository = _require_reader(ctx)
    artifact = _require_source_reader(repository, params.source_id)
    uri = artifact.get("canonical_uri") or ""
    try:
        video_id = youtube_video_id(uri)
    except UnsupportedSourceError as exc:
        raise SidecarError(
            "not_a_video", f"Source {params.source_id!r} is not a YouTube video."
        ) from exc

    # Canonical notes for this video (provenance refs cite the NOTE id/path).
    note_ids: set[str] = set()
    note_paths: set[str] = set()
    for note in vault.notes.values():
        metadata = getattr(note, "model_extra", {}) or {}
        canonical = metadata.get("canonical_source")
        canonical = canonical if isinstance(canonical, dict) else {}
        if canonical.get("kind") != "youtube_video":
            continue
        note_uri = canonical.get("original_uri") or canonical.get("canonical_uri") or ""
        try:
            if youtube_video_id(note_uri) != video_id:
                continue
        except UnsupportedSourceError:
            continue
        note_ids.add(note.id)
        if note.path:
            note_paths.add(note.path)

    points: dict[str, dict[str, Any]] = {}
    for item in vault.practice_items.values():
        if getattr(item, "status", "active") not in (None, "active"):
            continue
        for ref in item.provenance.source_refs:
            ref_extra = getattr(ref, "model_extra", None) or {}
            direct_source = (
                ref.ref_id == params.source_id
                or ref_extra.get("source_id") == params.source_id
            )
            if not direct_source and ref.ref_id not in note_ids and getattr(ref, "path", None) not in note_paths:
                continue
            time_range = _parse_time_locator(getattr(ref, "locator", None))
            if time_range is None:
                continue
            start, end = time_range
            # Pause AFTER the cited segment so the question lands on watched
            # material; keep the earliest citation per item.
            pause_at = end if end is not None else start
            existing = points.get(item.id)
            if existing is None or pause_at < existing["time_seconds"]:
                learning_object = vault.learning_objects.get(item.learning_object_id)
                goal = RG.goal_for_item(vault, learning_object, item) if learning_object is not None else None
                golden_run = repository.golden_path_run_for_goal(goal.id) if goal is not None else None
                points[item.id] = {
                    "time_seconds": round(pause_at, 1),
                    "segment_start_seconds": round(start, 1),
                    "practice_item_id": item.id,
                    "learning_object_id": item.learning_object_id,
                    "prompt_preview": (item.prompt or "").strip()[:120],
                    "goal_id": goal.id if goal is not None else None,
                    "goal_title": goal.title if goal is not None else None,
                    "golden_path_run_id": golden_run.get("id") if golden_run else None,
                    "target_contract_version_id": golden_run.get("goal_contract_version_id") if golden_run else None,
                }
            break
    pause_points = sorted(points.values(), key=lambda p: (p["time_seconds"], p["practice_item_id"]))
    return versioned(
        {
            "source_id": params.source_id,
            "video_id": video_id,
            "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?enablejsapi=1",
            "pause_points": pause_points,
        }
    )


# ---------------------------------------------------------------------------
# Reader quick-check producer: authoring as the learner approaches a section
# boundary in anchor mode (spec_reader_quick_check_producer.md). The RPC only
# enqueues a durable interactive-priority job — the reading hot path never
# blocks on a model — and the guide plan surfaces the authored question.
# ---------------------------------------------------------------------------

from learnloop.services import reader_quick_check as RQC  # noqa: E402


def _authored_question_payload(row: dict[str, Any]) -> dict[str, Any]:
    import json as _json_mod

    try:
        span_ids = _json_mod.loads(row.get("span_ids_json") or "[]")
    except (TypeError, ValueError):
        span_ids = []
    return {
        "id": row["id"],
        "extraction_id": row["extraction_id"],
        "section_id": row["section_id"],
        "status": row["status"],
        "question_md": row.get("question_md") or "",
        "expected_answer_md": row.get("expected_answer_md") or "",
        "span_ids": [str(span_id) for span_id in span_ids if isinstance(span_id, str)],
        "practice_item_id": row.get("practice_item_id"),
        "answered_at": row.get("answered_at"),
    }


class ReaderAuthorSectionQuestionInput(ParamsModel):
    extraction_id: str
    section_id: str


@method("reader.author_section_question", ReaderAuthorSectionQuestionInput)
def reader_author_section_question(
    ctx: SidecarContext, params: ReaderAuthorSectionQuestionInput
) -> dict[str, Any]:
    from learnloop.services.source_outline import resolve_extraction_id as _resolve
    from learnloop_sidecar.handlers.ai_providers import ready_canonical_ingest_provider

    vault, repository = _require_reader(ctx)
    resolved = _resolve(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError(
            "extraction_not_found", f"No extraction resolves for {params.extraction_id!r}."
        )
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)

    existing = repository.latest_reader_authored_question(
        extraction_id=resolved, section_id=params.section_id
    )
    if existing is not None:
        return versioned({"status": "exists", "question": _authored_question_payload(existing)})

    # Gate on the same canonical_ingest route the reader_quick_check job resolves
    # (RunnerServices.quick_check_client), so readiness matches the provider that
    # will actually author the question.
    _provider, runtime, client = ready_canonical_ingest_provider(vault)
    if client is None:
        raise SidecarError(
            "provider_unavailable",
            getattr(runtime, "message", None) or "The AI provider is unavailable for quick-check authoring.",
            retryable=True,
        )
    batch_id = ctx.ingest_jobs.enqueue_reader_quick_check(
        extraction_id=resolved, section_id=params.section_id
    )
    return versioned({"status": "queued", "batch_id": batch_id, "question": None})


def _progress_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "extraction_id": row["extraction_id"],
        "section_id": row["section_id"],
        "spans_seen": row.get("spans_seen") or 0,
        "span_count": row.get("span_count") or 0,
        "revealed_at": row.get("revealed_at"),
        "completed_at": row.get("completed_at"),
        "generation_batch_id": row.get("generation_batch_id"),
    }


class ReaderGetProgressInput(ParamsModel):
    extraction_id: str


@method("reader.get_progress", ReaderGetProgressInput)
def reader_get_progress(ctx: SidecarContext, params: ReaderGetProgressInput) -> dict[str, Any]:
    """Durable per-section reading progress for one extraction (migration 106)."""

    from learnloop.services.source_outline import resolve_extraction_id as _resolve

    _vault, repository = _require_reader(ctx)
    resolved = _resolve(repository, params.extraction_id) or params.extraction_id
    rows = repository.reader_section_progress_for(resolved)
    return versioned({"extraction_id": resolved, "sections": [_progress_payload(r) for r in rows]})


class ReaderMarkSectionProgressInput(ParamsModel):
    extraction_id: str
    section_id: str
    spans_seen: int | None = None
    span_count: int | None = None
    revealed: bool = False
    completed: bool = False


@method("reader.mark_section_progress", ReaderMarkSectionProgressInput)
def reader_mark_section_progress(
    ctx: SidecarContext, params: ReaderMarkSectionProgressInput
) -> dict[str, Any]:
    """Persist section progress; on first completion, trigger progressive
    practice generation for the section's provenance-linked Learning Objects.

    Idempotent per section via ``generation_batch_id`` (NULL = untriggered,
    'none_needed' = mapped to zero targets, else the enqueued batch id) — a
    re-completed section never enqueues twice."""

    from learnloop.services.reader_progression import (
        section_generation_candidates,
        source_refs_for_section,
    )
    from learnloop.services.source_outline import resolve_extraction_id as _resolve

    vault, repository = _require_reader(ctx)
    resolved = _resolve(repository, params.extraction_id) or params.extraction_id
    row = repository.upsert_reader_section_progress(
        extraction_id=resolved,
        section_id=params.section_id,
        spans_seen=params.spans_seen,
        span_count=params.span_count,
        revealed=params.revealed,
        completed=params.completed,
    )

    enqueued = False
    batch_id: str | None = None
    if params.completed and row.get("generation_batch_id") is None:
        lo_ids = section_generation_candidates(
            vault, repository, extraction_id=resolved, section_id=params.section_id
        )
        if not lo_ids:
            repository.mark_section_generation(
                extraction_id=resolved, section_id=params.section_id, batch_id="none_needed"
            )
        else:
            # Stamp FIRST so a concurrent completion cannot double-enqueue; the
            # loser of the race sees the stamp and does nothing.
            if repository.mark_section_generation(
                extraction_id=resolved, section_id=params.section_id, batch_id="enqueuing"
            ):
                source_refs = source_refs_for_section(
                    vault,
                    repository,
                    extraction_id=resolved,
                    section_id=params.section_id,
                    learning_object_ids=lo_ids,
                )
                batch_id = ctx.ingest_jobs.enqueue_practice_expansion(
                    learning_object_ids=lo_ids,
                    reason=f"reader_section_completed:{params.section_id}",
                    source_refs=source_refs,
                )
                repository.set_section_generation_batch(
                    extraction_id=resolved, section_id=params.section_id, batch_id=batch_id
                )
                enqueued = True
        row = repository.upsert_reader_section_progress(
            extraction_id=resolved, section_id=params.section_id
        )

    return versioned(
        {
            "progress": _progress_payload(row),
            "enqueued_generation": enqueued,
            "batch_id": batch_id,
        }
    )


class ReaderAuthoredQuestionActionInput(ParamsModel):
    question_id: str
    action: str
    response: str | None = None


@method("reader.authored_question_action", ReaderAuthoredQuestionActionInput)
def reader_authored_question_action(
    ctx: SidecarContext, params: ReaderAuthoredQuestionActionInput
) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    try:
        row = RQC.record_action(
            repository,
            question_id=params.question_id,
            action=params.action,
            response_md=params.response,
        )
    except RQC.ReaderQuickCheckError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned({"question": _authored_question_payload(row)})


class ReaderEscalateAuthoredQuestionInput(ParamsModel):
    question_id: str
    learning_object_id: str


class ReaderImportExerciseInput(ParamsModel):
    extraction_id: str
    raw_selection: dict[str, Any]
    render_view_id: str | None = None
    source_id: str | None = None
    revision_id: str | None = None
    learning_object_id: str | None = None
    client_idempotency_key: str | None = None


@method("reader.import_exercise", ReaderImportExerciseInput)
def reader_import_exercise(ctx: SidecarContext, params: ReaderImportExerciseInput) -> dict[str, Any]:
    """Queue the exact-exercise slice: the learner's selection (ordered
    per-block nodes) becomes one background authoring job that writes complete,
    schedulable PracticeItems around the verbatim exercise text."""

    from learnloop.services.source_outline import resolve_extraction_id as _resolve
    from learnloop_sidecar.handlers.ai_providers import ready_canonical_ingest_provider

    vault, repository = _require_reader(ctx)
    resolved = _resolve(repository, params.extraction_id)
    if resolved is None:
        raise SidecarError(
            "extraction_not_found", f"No extraction resolves for {params.extraction_id!r}."
        )
    nodes = list((params.raw_selection or {}).get("nodes") or [])
    if not nodes:
        raise SidecarError("validation_error", "The selection has no anchorable nodes.")
    source_id = params.source_id or _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)

    # Gate on the same canonical_ingest route the exercise-import job resolves
    # (RunnerServices.exercise_import_client), so readiness honors the configured
    # provider instead of hardcoding Codex.
    _provider, runtime, client = ready_canonical_ingest_provider(vault)
    if client is None:
        raise SidecarError(
            "provider_unavailable",
            getattr(runtime, "message", None) or "The AI provider is unavailable for exercise authoring.",
            retryable=True,
        )
    batch_id = ctx.ingest_jobs.enqueue_reader_exercise_import(
        extraction_id=resolved,
        raw_selection=dict(params.raw_selection),
        render_view_id=params.render_view_id,
        source_id=source_id,
        revision_id=params.revision_id,
        learning_object_hint=params.learning_object_id,
    )
    return versioned({"status": "queued", "batch_id": batch_id})


class ReaderExerciseImportStatusInput(ParamsModel):
    batch_id: str


@method("reader.exercise_import_status", ReaderExerciseImportStatusInput)
def reader_exercise_import_status(
    ctx: SidecarContext, params: ReaderExerciseImportStatusInput
) -> dict[str, Any]:
    """Poll one exercise-import batch. On completion the vault is reloaded
    (once) so the authored cards schedule immediately, then the job's result
    payload — written-card summaries, skips, warnings — rides back to the UI."""

    _vault, repository = _require_reader(ctx)
    jobs = repository.ingest_jobs_for_batch(params.batch_id)
    if not jobs:
        raise SidecarError("batch_not_found", f"No jobs found for batch {params.batch_id!r}.")
    job = jobs[0]
    if job.get("status") == "completed" and ctx.ingest_jobs.needs_reload(job["id"]):
        ctx.reload(maintenance=False)
        ctx.ingest_jobs.mark_reloaded(job["id"])
    return versioned(
        {
            "status": job.get("status"),
            "phase": job.get("phase"),
            "message": job.get("message"),
            "result": job.get("result"),
            "error": job.get("error"),
        }
    )


@method("reader.escalate_authored_question", ReaderEscalateAuthoredQuestionInput)
def reader_escalate_authored_question(
    ctx: SidecarContext, params: ReaderEscalateAuthoredQuestionInput
) -> dict[str, Any]:
    vault, repository = _require_reader(ctx)
    try:
        result = RQC.escalate(
            vault.root,
            repository,
            question_id=params.question_id,
            learning_object_id=params.learning_object_id,
        )
    except RQC.ReaderQuickCheckError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    # The escalated card is vault YAML; reload so it schedules immediately.
    ctx.reload(maintenance=False)
    return versioned(
        {
            "practice_item_id": result["practice_item_id"],
            "question": _authored_question_payload(result["question"]),
        }
    )


# ---------------------------------------------------------------------------
# Across-source text search ("where did I read that?") + manual re-anchor.
# Both are deterministic and local — no model, no evidence.
# ---------------------------------------------------------------------------

from learnloop.services import source_search as SS  # noqa: E402


class ReaderSearchSourcesInput(ParamsModel):
    query: str
    limit: int = SS.MAX_HITS


@method("reader.search_sources", ReaderSearchSourcesInput)
def reader_search_sources(ctx: SidecarContext, params: ReaderSearchSourcesInput) -> dict[str, Any]:
    _vault, repository = _require_reader(ctx)
    return versioned(SS.search_sources(repository, query=params.query, limit=params.limit))


class ReaderManualAnchorInput(ParamsModel):
    annotation_id: str
    extraction_id: str
    raw_selection: dict[str, Any]
    render_view_id: str | None = None


@method("reader.manual_anchor", ReaderManualAnchorInput)
def reader_manual_anchor(ctx: SidecarContext, params: ReaderManualAnchorInput) -> dict[str, Any]:
    """Repair a needs_reanchor annotation with a learner-chosen passage (§4.4).

    The raw display selection is translated through the crosswalk into block
    anchor segments, then appended as a ``manually_anchored`` successor — every
    prior anchor version is preserved."""

    _vault, repository = _require_reader(ctx)
    run = repository.get_extraction_run(params.extraction_id)
    revision = repository.get_source_revision(str((run or {}).get("revision_id") or "")) if run else None
    if run is None or revision is None:
        raise SidecarError(
            "extraction_not_found", f"No extraction resolves for {params.extraction_id!r}."
        )
    translation = ANN.translate_selection(
        repository,
        extraction_id=params.extraction_id,
        raw_selection=params.raw_selection,
        render_view_id=params.render_view_id,
    )
    segments = translation.get("segments") or []
    if not segments:
        raise SidecarError(
            "validation_error",
            "The selected passage could not be anchored — select text directly in the source.",
        )
    try:
        result = ANN.manual_anchor(
            repository,
            annotation_id=params.annotation_id,
            source_id=str(revision["source_id"]),
            revision_id=str(revision["id"]),
            extraction_id=params.extraction_id,
            segments=segments,
        )
    except ANN.AnnotationError as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    return versioned(result)
