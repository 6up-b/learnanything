"""The Reader and authoring job types: Reader quick checks and exercise imports, a picked source exercise,
practice expansion (with adaptive difficulty's commissions), goal population, question promotion, rung variants
and concept animations, with the authoring clients the runner's services fall back on.

The durable host that runs them is :mod:`learnloop.content.pipeline.jobs`; what each type is (its handler and its
flags) is its row in :mod:`learnloop.content.pipeline.job_types`.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.clock import utc_now_iso
from learnloop.content.pipeline.job_contracts import IngestRunnerError, JobCancelled
from learnloop.content.synthesis.jobs import _routed_task_client
from learnloop.db.repositories import Repository
from learnloop.reader import (
    part_read as PART_READ,
    reader_quick_check as RQC,
    section_generation as SG,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.tutor.promotions import PromotionError, PromotionNoItemError, promote_tutor_question

if TYPE_CHECKING:
    from learnloop.content.pipeline.runner import JobContext


def default_animation_client(ctx: JobContext) -> Any:
    """Resolve the animation route (default: the medium-effort profile) — any
    configured provider works; run_concept_animation is getattr-discovered."""

    return _routed_task_client(ctx, "animation")


def default_video_client(ctx: JobContext) -> Any:
    """Resolve [ai.routing] video_generation to an OpenRouter video client.

    The route is read directly (not through provider_for_task): a
    LEARNLOOP_AI_PROVIDER override names a chat provider and must never
    redirect billable video jobs."""

    from learnloop.ai.client import make_video_generation_client
    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.vault.loader import load_vault

    config = load_vault(ctx.vault_root).config
    route = (config.ai.routing.video_generation or "").strip()
    if not route:
        raise IngestRunnerError(
            "no video model is routed: choose one in Settings → Animation ([ai.routing] video_generation)",
            code="video_provider_unavailable",
        )
    try:
        return make_video_generation_client(config, ctx.vault_root, provider_name=route)
    except AIProviderUnavailable as exc:
        raise IngestRunnerError(str(exc), code="video_provider_unavailable") from exc


def default_rung_variant_client(ctx: JobContext) -> Any:
    """Resolve the rung_variant route (default: the fast low-effort profile).

    A learner-requested variant is a small, instruction-constrained authoring
    task whose output the deterministic rung gate checks — it does not need the
    judgment-heavy synthesis profile, and the learner is actively waiting."""

    return _routed_task_client(ctx, "rung_variant")


def default_promotion_analysis_client(ctx: JobContext) -> Any:
    """Fast classification/dedup pass for a durable promotion request."""

    try:
        return _routed_task_client(ctx, "tutor_qa")
    except IngestRunnerError as exc:
        raise IngestRunnerError(
            str(exc),
            code="provider_unavailable",
            details={"task": "tutor_qa"},
            retryable=True,
        ) from exc


def default_promotion_authoring_client(ctx: JobContext) -> Any:
    """Judgment-heavy practice generation follows the configured authoring route."""

    try:
        return _routed_task_client(ctx, "authoring")
    except IngestRunnerError as exc:
        raise IngestRunnerError(
            str(exc),
            code="provider_unavailable",
            details={"task": "authoring"},
            retryable=True,
        ) from exc


def handle_reader_quick_check(ctx: JobContext) -> dict[str, Any]:
    """Author one section-boundary quick check (reader producer slice).

    Interactive-priority, one section per job. Idempotent through the service:
    an existing row for the section (any status) is reused without a model
    call, so a duplicate enqueue or a retry never double-authors."""

    payload = ctx.payload
    if payload.get("scope_kind") == "inquiry":
        return _handle_reader_inquiry_check(ctx)
    if payload.get("scope_kind") == "selection":
        return _handle_reader_selection_check(ctx)
    extraction_id = str(payload.get("extraction_id") or "")
    section_id = str(payload.get("section_id") or "")
    if not extraction_id or not section_id:
        raise IngestRunnerError("reader_quick_check needs extraction_id and section_id.")
    _refuse_held_out_reader_material(ctx, extraction_id, _section_span_ids(ctx.repo, extraction_id, section_id))
    existing = ctx.repo.latest_reader_authored_question(
        extraction_id=extraction_id, section_id=section_id
    )
    if existing is not None:
        return {"question_id": existing["id"], "deduplicated": True}
    ctx.report("authoring", message="Authoring a quick check for this section")
    client = ctx.services.quick_check_client(ctx)
    row = RQC.author_quick_check(
        ctx.repo, client, extraction_id=extraction_id, section_id=section_id, clock=ctx.clock
    )
    return {"question_id": row["id"], "deduplicated": False}


def _reader_source_sets(vault_root: Path) -> Any:
    """The vault, read when a Reader request is sent (the held-out partition
    reads its source sets; exam protection, Codex review F3). A vault that
    fails to load, or whose source sets do not, raises, so the request fails
    before any model call. A root with no vault config raises too: nothing
    can say it holds no exam material, and an empty list would skip the gate."""

    from learnloop.content.sources.exam_material import SourceSetsUnreadable
    from learnloop.vault.loader import load_vault

    if not (Path(vault_root) / "learnloop.toml").exists():
        raise SourceSetsUnreadable(["the vault's configuration (learnloop.toml) is missing"])
    return load_vault(vault_root)


def _refuse_held_out_reader_material(ctx: JobContext, extraction_id: str, span_ids: Sequence[str]) -> None:
    """Exam protection (2026-10-13): a Reader check over held-out material (the
    one held-out partition, read with the vault's source sets) is refused
    before any model call, and before a check authored before the mark is
    handed back (code ``exam_material``)."""

    from learnloop.content.sources.exam_material import held_out_among, held_out_refusal, surface_material

    material = surface_material(_reader_source_sets(ctx.vault_root), ctx.repo, "reader_checks")
    held = held_out_among(material, extraction_id, span_ids)
    if held:
        raise IngestRunnerError(held_out_refusal(material, extraction_id), code="exam_material",
                                details={"extraction_id": extraction_id, "span_ids": held})


def _section_span_ids(repository: Repository, extraction_id: str, section_id: str) -> list[str]:
    """Every block of one guide section (the quick check's own derivation), or []."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return []
    section_rows, _block_by_span, _span_to_section = RQC.extraction_sections(ir)
    return next((list(row["span_ids"]) for row in section_rows if row["id"] == section_id), [])


def _passage_span_ids(repository: Repository, extraction_id: str, anchors: Sequence[str]) -> list[str]:
    """The anchors and every block of the passage check's view of them."""

    try:
        view = RQC.passage_view(repository, extraction_id=extraction_id, anchor_span_ids=list(anchors))
    except RQC.ReaderQuickCheckError:
        return list(anchors)
    return [*anchors, *(str(block["span_id"]) for block in view["blocks"])]


def _paid_quick_check_client(ctx: JobContext) -> Any:
    """The client of a paid passage check (an inquiry's or a selection's), resolved for that feature.

    It rides ``canonical_ingest`` but is held to its own price (re-review
    F2): while ``reader_inquiry.metered_price_per_million`` is unset, an
    unavailable plan offers nothing here and a grant of the question build
    does not serve it; the unavailable error names the setting.
    """

    from learnloop.ai import plan_fallback

    with plan_fallback.priced_by(RQC.PASSAGE_CHECK_PRICE_SETTING):
        return ctx.services.quick_check_client(ctx)


def _exercise_import_client(ctx: JobContext) -> Any:
    """The authoring client of an exercise import, resolved for that feature (re-review F2).

    Admitted at ``source_service.llm_price_per_million`` on a metered route,
    so, like a passage check, it makes no offer and takes no other
    feature's grant of ``canonical_ingest`` while that price is unset.
    """

    from learnloop.ai import plan_fallback
    from learnloop.content.authoring.source_exercise_import import PRICE_SETTING

    with plan_fallback.priced_by(PRICE_SETTING):
        return ctx.services.exercise_import_client(ctx)


def _passage_check_spend(ctx: JobContext) -> RQC.PassageCheckSpend:
    """The vault's admission settings for one passage check ([reader_inquiry])."""

    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    return RQC.passage_check_spend(vault.config, cancelled=getattr(ctx, "cancelled", None))


# A claim another live job holds (re-review F13) is waited on, polled this
# often, for at most as long as the Reader itself waits (200 polls of 3 s):
# the job stays running, and ends with the holder's question, its own (when
# the holder gave the key back or ended), or a retryable "held" failure.
INQUIRY_HELD_POLL_SECONDS = 5.0
INQUIRY_HELD_MAX_POLLS = 120
# A job in one of these states will never land or release a claim it holds.
_ENDED_JOB_STATUSES = frozenset({"completed", "failed", "cancelled", "blocked"})


def _pause_while_inquiry_held(ctx: JobContext, seconds: float) -> None:
    """Wait between polls of a held inquiry claim (a seam for tests)."""

    threading.Event().wait(seconds)


def _inquiry_owner_ended(repo: Repository, owner: str) -> bool:
    """True when the claim's owner is an ingest job that has finished: it was
    expired, failed or cancelled after claiming, so its claim is abandoned.
    An owner that is not a job is left to its lease."""

    job = repo.get_ingest_job(owner)
    return job is not None and job.get("status") in _ENDED_JOB_STATUSES


def _handle_reader_inquiry_check(ctx: JobContext) -> dict[str, Any]:
    """RW1a: author the reconnect line's quick check for one inquiry's root
    passage. Same job type, lane and client as the section check, but a paid
    call admitted through the spend framework before it is sent (W10), as an
    isolated turn, under a durable claim on (root exchange, prompt version)
    owned by this job (a re-run of the job after a crash takes it back at
    once, and so does any job once the claiming job has ended). A refusal
    fails the job with its reason as the error code (``capped``,
    ``spend_refused`` with its ``refusal``, ``provider_unavailable``), which
    the Reader shows in place. A claim another live job holds makes no call:
    this job waits for it (still running), so it never completes without a
    question; past the wait it fails with the retryable code ``held``."""

    payload = ctx.payload
    extraction_id = str(payload.get("extraction_id") or "")
    root_event_id = str(payload.get("inquiry_root_event_id") or "")
    anchors = [str(span_id) for span_id in payload.get("anchor_span_ids") or [] if span_id]
    if not extraction_id or not root_event_id or not anchors:
        raise IngestRunnerError(
            "an inquiry quick check needs extraction_id, inquiry_root_event_id and anchor_span_ids."
        )
    _refuse_held_out_reader_material(ctx, extraction_id, _passage_span_ids(ctx.repo, extraction_id, anchors))
    existing = ctx.repo.inquiry_reader_authored_question(
        inquiry_root_event_id=root_event_id, prompt_version=RQC.INQUIRY_PROMPT_VERSION
    )
    if existing is not None:
        return {"question_id": existing["id"], "deduplicated": True}
    ctx.report("authoring", message="Authoring a quick check for this passage")
    try:
        client = _paid_quick_check_client(ctx)
    except IngestRunnerError as exc:
        raise IngestRunnerError(str(exc), code="provider_unavailable") from exc
    bind = getattr(ctx, "bind_interruptible", None)
    if callable(bind):
        bind(client)
    spend = _passage_check_spend(ctx)
    owner = str((getattr(ctx, "job", None) or {}).get("id") or "") or None
    polls = 0
    while True:
        if polls:
            ctx.report("authoring", message="Authoring a quick check for this passage")
        try:
            row = RQC.author_inquiry_quick_check(
                ctx.repo, client, extraction_id=extraction_id, inquiry_root_event_id=root_event_id,
                anchor_span_ids=anchors, clock=ctx.clock, spend=spend, owner=owner,
                owner_ended=lambda holder: _inquiry_owner_ended(ctx.repo, holder),
            )
        except RQC.PassageCheckRefused as exc:
            raise IngestRunnerError(str(exc), code=exc.reason, details={
                "refusal": exc.refusal,
                "max_checks_per_day": spend.max_checks_per_day,
                "max_usd_per_check": spend.max_usd_per_check,
                "price_per_million": spend.price_per_million,
            }) from exc
        except RQC.InquiryCheckHeld:
            landed = ctx.repo.inquiry_reader_authored_question(
                inquiry_root_event_id=root_event_id, prompt_version=RQC.INQUIRY_PROMPT_VERSION
            )
            if landed is not None:
                return {"question_id": landed["id"], "deduplicated": True}
            if polls >= INQUIRY_HELD_MAX_POLLS:
                raise IngestRunnerError(
                    "Another job is still writing this quick check.", code="held", retryable=True,
                ) from None
            polls += 1
            # Heartbeats the lease and stops here if the learner cancelled.
            ctx.report("waiting", message="Waiting for the job already writing this quick check")
            _pause_while_inquiry_held(ctx, INQUIRY_HELD_POLL_SECONDS)
            continue
        except AIProviderUnavailable as exc:
            raise IngestRunnerError(str(exc), code="provider_unavailable") from exc
        return {"question_id": row["id"], "deduplicated": False}


def _handle_reader_selection_check(ctx: JobContext) -> dict[str, Any]:
    """RW1b: author one active-reading question on a selection (next step, why
    step, assumptions, reconstruct). The inquiry check's job type, lane,
    client and admission (``[reader_inquiry]``'s caps, an isolated turn), with
    a durable claim on the selection's reuse key; held-out material is refused
    before any call. Refusals fail the job with their reason as its code, as
    the inquiry check's do."""

    payload = ctx.payload
    extraction_id = str(payload.get("extraction_id") or "")
    style = str(payload.get("question_style") or "")
    anchors = [str(span_id) for span_id in payload.get("anchor_span_ids") or [] if span_id]
    if not extraction_id or not anchors or style not in RQC.SELECTION_STYLES:
        raise IngestRunnerError(
            "an active-reading question needs extraction_id, anchor_span_ids and a question_style."
        )
    try:
        view = RQC.selection_view(ctx.repo, extraction_id=extraction_id, anchor_span_ids=anchors, style=style)
    except RQC.ReaderQuickCheckError as exc:
        raise IngestRunnerError(str(exc), code="no_passage") from exc
    passage = [*view["anchor_span_ids"], *(b["span_id"] for b in [*view["before"], *view["selected"], *view["following"]])]
    _refuse_held_out_reader_material(ctx, extraction_id, passage)
    existing = RQC.selection_question(ctx.repo, extraction_id=extraction_id,
                                      anchor_span_ids=view["anchor_span_ids"], style=style)
    if existing is not None:
        return {"question_id": existing["id"], "deduplicated": True}
    ctx.report("authoring", message="Writing the question for this passage")
    try:
        client = _paid_quick_check_client(ctx)
    except IngestRunnerError as exc:
        raise IngestRunnerError(str(exc), code="provider_unavailable") from exc
    bind = getattr(ctx, "bind_interruptible", None)
    if callable(bind):
        bind(client)
    spend = _passage_check_spend(ctx)
    owner = str((getattr(ctx, "job", None) or {}).get("id") or "") or None
    polls = 0
    while True:
        try:
            row = RQC.author_selection_question(
                ctx.repo, client, extraction_id=extraction_id, anchor_span_ids=anchors, style=style,
                clock=ctx.clock, spend=spend, owner=owner,
                owner_ended=lambda holder: _inquiry_owner_ended(ctx.repo, holder),
            )
        except RQC.PassageCheckRefused as exc:
            raise IngestRunnerError(str(exc), code=exc.reason, details={
                "refusal": exc.refusal,
                "max_checks_per_day": spend.max_checks_per_day,
                "max_usd_per_check": spend.max_usd_per_check,
                "price_per_million": spend.price_per_million,
            }) from exc
        except RQC.InquiryCheckHeld:
            landed = RQC.selection_question(ctx.repo, extraction_id=extraction_id,
                                            anchor_span_ids=view["anchor_span_ids"], style=style)
            if landed is not None:
                return {"question_id": landed["id"], "deduplicated": True}
            if polls >= INQUIRY_HELD_MAX_POLLS:
                raise IngestRunnerError(
                    "Another job is still writing this question.", code="held", retryable=True,
                ) from None
            polls += 1
            ctx.report("waiting", message="Waiting for the job already writing this question")
            _pause_while_inquiry_held(ctx, INQUIRY_HELD_POLL_SECONDS)
            continue
        except RQC.ReaderQuickCheckError as exc:
            raise IngestRunnerError(str(exc), code="no_question") from exc
        except AIProviderUnavailable as exc:
            raise IngestRunnerError(str(exc), code="provider_unavailable") from exc
        return {"question_id": row["id"], "deduplicated": False}


def handle_reader_exercise_import(ctx: JobContext) -> dict[str, Any]:
    """reader_exercise_import: author the learner's selected textbook
    exercise(s) into complete, schedulable PracticeItems.

    Interactive-priority but on the MAIN single-writer lane — unlike
    reader_quick_check this job writes vault YAML, so it must never run
    concurrently with another vault-writing job. Idempotent through the
    service's prompt-level dedupe: a retry after a crash mid-batch skips
    already-written exercises as duplicates instead of double-authoring."""

    from learnloop.content.authoring import exercise_authoring as EX

    payload = ctx.payload
    extraction_id = str(payload.get("extraction_id") or "")
    raw_selection = payload.get("raw_selection") or {}
    if not extraction_id or not raw_selection.get("nodes"):
        raise IngestRunnerError("reader_exercise_import needs extraction_id and raw_selection nodes.")
    # Exam protection (2026-10-13): held-out material (the one exam predicate's
    # held-out partition) never becomes practice, whoever selects it. Checked
    # before any model call.
    from learnloop.content.sources.exam_material import scope_only_among, surface_material
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    held_out = surface_material(vault, ctx.repo, "reader_import")
    render_view_id = str(payload.get("render_view_id") or "") or None
    # The blocks the author will read, translated as the author translates them (either key spelling, a
    # render view's display node, a quote re-anchored): a check of the raw nodes' keys misses a selection
    # spelled ``spanId`` or named by its display node. Scope and provenance read the same blocks.
    selected = EX.selected_span_ids(ctx.repo, extraction_id=extraction_id, raw_selection=raw_selection,
                                    render_view_id=render_view_id)
    held = [span for span in selected if held_out.covers(str(extraction_id), str(span))]
    if held:
        raise IngestRunnerError(
            "This passage is held out for evaluation (an exam you'll sit later), so it can't become practice.",
            code="exam_material", details={"extraction_id": extraction_id, "span_ids": held})
    # Curriculum C3 (Codex review F3): a syllabus only scopes a deliverable, never practice
    # (checked again at the write, ``exercise_authoring.write_draft``).
    if scope_only_among(vault, ctx.repo, [(extraction_id, span) for span in selected]):
        raise IngestRunnerError(
            "This is your syllabus: LearnLoop uses it only to scope your deliverables, so it can't become practice.",
            code="scope_only", details={"extraction_id": extraction_id})
    ctx.report("authoring", message="Authoring the selected exercise(s) into practice items")
    client = _exercise_import_client(ctx)
    source_id = str(payload.get("source_id") or "") or None
    revision_id = str(payload.get("revision_id") or "") or None
    try:
        result = EX.import_exercises(
            ctx.vault_root,
            ctx.repo,
            client,
            extraction_id=extraction_id,
            raw_selection=raw_selection,
            render_view_id=render_view_id,
            source_id=source_id,
            revision_id=revision_id,
            learning_object_hint=str(payload.get("learning_object_hint") or "") or None,
            clock=ctx.clock,
            # The Reader's set: a held-out neighbor of the selection never reaches the author.
            context_withheld=held_out,
        )
    except EX.ExerciseAuthoringError as exc:
        raise IngestRunnerError(str(exc)) from exc
    _record_reader_import_keys(ctx, result, extraction_id=extraction_id, span_ids=selected,
                               source_id=source_id, revision_id=revision_id)
    return result


def _record_reader_import_keys(ctx: JobContext, result: dict[str, Any], *, extraction_id: str,
                               span_ids: list[str], source_id: str | None,
                               revision_id: str | None) -> None:
    """Canonical sources S1 (§7.3a): the Reader's import records its key status.

    One ``source_exercise_imports`` row per written item (``caller = reader``,
    ``key_status = model_answer``), and, when ``exercise_verification`` is on,
    the verifier ladder runs in the background. The item written is unchanged
    (G5). Best-effort: a failure here never fails the learner's import.
    """

    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.vault.loader import load_vault

    try:
        vault = load_vault(ctx.vault_root)
        service = vault.config.source_service
        if not service.enabled:
            return
        checking = bool(service.exercise_verification and ctx.services.background_key_checks)
        # The rows keep a durable pending-check marker until each check
        # commits, so startup recovery resumes one a dead process lost (F5).
        rows = SEI.record_reader_import(ctx.vault_root, ctx.repo, result, extraction_id=extraction_id,
                                        span_ids=list(span_ids), source_id=source_id,
                                        revision_id=revision_id, clock=ctx.clock, pending_check=checking)
        if checking and rows:
            threading.Thread(
                target=_verify_quietly, args=(ctx.vault_root, ctx.repo, rows, "background"),
                name="reader-import-key-check", daemon=True,
            ).start()
    except Exception:  # noqa: BLE001 - the import itself already succeeded
        logging.getLogger(__name__).warning("recording the Reader import's key status failed", exc_info=True)


def _verify_quietly(root: Path, repository: Repository, rows: list[dict[str, str]], trigger: str) -> None:
    from learnloop.content.authoring import source_exercise_import as SEI

    for row in rows:
        try:
            SEI.verify_item_key(root, repository, row["practice_item_id"], trigger=trigger,
                                import_id=row.get("import_id"))
        except Exception:  # noqa: BLE001 - the pending marker stays; startup recovery resumes it
            logging.getLogger(__name__).warning("background key check failed for %s", row.get("practice_item_id"),
                                                exc_info=True)


def handle_source_exercise_import(ctx: JobContext) -> dict[str, Any]:
    """source_exercise_import: a learner picked a textbook exercise proposal
    (canonical sources S1, §7.2). Author, check within the time box, write with
    ``canonical_exercise`` and the key's status, attach to a family. Main
    single-writer lane: it writes vault YAML."""

    from learnloop.content.authoring import source_exercise_import as SEI
    from learnloop.vault.loader import load_vault

    payload = ctx.payload
    extraction_id = str(payload.get("extraction_id") or "")
    span_ids = [str(span) for span in payload.get("span_ids") or [] if str(span)]
    if not extraction_id or not span_ids:
        raise IngestRunnerError("source_exercise_import needs extraction_id and span_ids.")
    vault = load_vault(ctx.vault_root)
    ctx.report("authoring", message="Importing the textbook exercise and checking its answer key")
    request = dict(payload.get("request") or {})
    validate = None
    if request:
        # The draft is validated against what the exercise was proposed for
        # (§8.1; Codex re-review F7): a learner's pick is written whatever it
        # says, and a failure is the correction shown on screen.
        # Minutes are the plan estimator's response to the AUTHORED draft (its
        # practice mode and its own expected_minutes), never an estimate made
        # before authoring (Codex third pass F7).
        from learnloop.content.authoring.draft_validation import draft_validator, duration_estimator

        durations = dict(request.get("duration_by_mode") or {})
        validate = draft_validator(
            vault, dict(request.get("constraints") or {}), intent=str(request.get("intent") or "practice"),
            estimator=duration_estimator(durations) if durations else None)
    result = SEI.import_source_exercise(
        ctx.vault_root, ctx.repo, extraction_id=extraction_id, span_ids=span_ids,
        caller=str(payload.get("caller") or "learner"), proposal_id=payload.get("proposal_id"),
        clients={"authoring": _exercise_import_client(ctx)},
        time_box_seconds=float(vault.config.source_service.verify_timeout_seconds),
        import_id=payload.get("import_id"), label=payload.get("label"),
        learning_object_hint=payload.get("learning_object_hint"), clock=ctx.clock,
        validate=validate, screen=request.get("screen"),
    )
    if result.get("status") != "written":
        raise IngestRunnerError(str(result.get("reason") or "the exercise could not be imported"),
                                code="source_exercise_import_" + str(result.get("status")),
                                details={"import_id": result.get("import_id")})
    return result


def ad_commission_batch_id(commission_id: str) -> str:
    """The one durable batch of an adaptive difficulty commission's generation (the store's
    name for it: a commission's expiry reads its job, Codex review F5)."""

    from learnloop.db.stores.ad_serving import commission_batch_id

    return commission_batch_id(commission_id)


#: A commission's job that ran with ``LEARNLOOP_AD_MODELS=off``: failed retryable, requeued by
#: the next schedule with models on unless its batch was cancelled (Codex re-review F10, verify
#: F11). Its commission stays open meanwhile (the store's ``MODELS_OFF_CODE``).
AD_MODELS_OFF_CODE = "ad_models_off"


#: Refactor B8: an AD commission's job that generated nothing because the commission wasn't open to it.
AD_COMMISSION_SKIP = "ad_commission_skip"


def ad_commission_skip_record(*, commission_id: Any, job_id: Any, rule: str) -> Any:
    """Why a commission's job generated nothing (pure): ``commission_closed`` (it landed or expired),
    ``view_unavailable`` (AD's held-out predicate couldn't be read) or ``guard_denied`` (AD's guard refused a read;
    the denial itself is in ``ad_guard_denials.jsonl``). Before this the job's result said "no longer open" for all
    three."""

    import hashlib

    from learnloop import provenance

    def ref(value: Any) -> str | None:
        if value is None or value == "":
            return None
        text = str(value)
        return text if provenance.is_code(text) else "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    job = ref(job_id)
    return provenance.DecisionRecord(
        kind=AD_COMMISSION_SKIP, status="excluded", subject_kind="job" if job else None, subject_id=job,
        decided_by="ad_commission_job", rule=rule,
        facts={key: value for key, value in {"commission_id": ref(commission_id), "generated": 0}.items()
               if value is not None},
        detail_table="ad_selections", detail_id=ref(commission_id),
    )


def _record_commission_skip(ctx: JobContext, commission_id: str, rule: str) -> None:
    """Write :func:`ad_commission_skip_record` in a short transaction of its own, outside every AD operation;
    never raises."""

    from learnloop import provenance
    from learnloop.db.stores.provenance import write_decision

    try:
        record = ad_commission_skip_record(commission_id=commission_id, job_id=ctx.job_id, rule=rule)
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        logging.getLogger(__name__).warning("decision record %r not built (trace %s): %s", AD_COMMISSION_SKIP,
                                            provenance.current_trace(), type(exc).__name__)
        return
    write_decision(ctx.repo, record)


def _handle_ad_commission(ctx: JobContext, lo_ids: list[str], commission_id: str) -> dict[str, Any]:
    """One item at an open AD commission's point, through the ordinary generation path and
    its gates (spec_adaptive_difficulty_v1 §6.1 "runs in the background", §7.1, §7.4). A
    commission that has landed, or one queued before AD was switched off, is a no-op success."""

    from learnloop.adaptive_difficulty.generation import contract_on
    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        generate_post_probe_practice_proposal,
    )
    from learnloop.vault.loader import load_vault

    vault = load_vault(ctx.vault_root)
    if not contract_on(vault.config):
        return {"generated": 0, "skipped_reason": "adaptive_difficulty off"}
    from learnloop.adaptive_difficulty.operation import ad_operation

    # The commission is open as AD's material view sees it (a withheld landing closes nothing);
    # with the held-out predicate unavailable none is, and nothing is generated (A8). Read inside
    # one AD operation (the AD23 redesign); the generation itself runs outside it (E1).
    from learnloop.adaptive_difficulty.operation import is_denial

    unread: str | None = None
    try:
        # The savepoint form (round 4): the operation inside its savepoint, rolled back on poison.
        with ad_operation(vault, ctx.repo, savepoint=True) as op:
            view = op.view
            open_ids = {str(row["id"]) for row in view.open_commissions(ctx.repo.connection(),
                                                                         now=utc_now_iso(ctx.clock))} \
                if view.available else set()
            unread = None if view.available else "view_unavailable"
    except Exception as exc:
        if not is_denial(exc):
            raise
        open_ids = set()  # the AD guard refused something: no commission is open for this job
        unread = "guard_denied"
    if commission_id not in open_ids:
        # The job's result says "no longer open" whether the commission closed or AD couldn't read it; the record,
        # written after the operation has closed (its guard denies the table), says which.
        _record_commission_skip(ctx, commission_id, unread or "commission_closed")
        return {"generated": 0, "skipped_reason": "commission no longer open"}
    from learnloop.adaptive_difficulty.spend import models_off

    # Codex re-review F10: work queued before the switch went off still makes no model call.
    # Only an explicitly injected client (a test's fake) runs with models off. The job fails
    # retryable rather than completing, so its batch stays resumable and the commission open.
    if models_off() and ctx.services.synthesis_client_factory is None:
        raise IngestRunnerError(
            "Adaptive difficulty's models are off, so this question waits until they are back on.",
            code=AD_MODELS_OFF_CODE, retryable=True, details={"ad_commission_id": commission_id},
        )
    ctx.report("generation", message="Writing a question at the level adaptive difficulty asked for")
    client = ctx.services.synthesis_client(ctx)
    try:
        result = generate_post_probe_practice_proposal(
            ctx.vault_root, client, learning_object_ids=lo_ids, require_completed_probe=False,
            target_items_per_lo=1, max_new_per_lo=1, ad_commission_id=commission_id,
        )
    except PracticeExpansionError as exc:
        return {"generated": 0, "skipped_reason": str(exc)}
    commissioned = [t for t in result.plan.targets if t.ad_commission_id == commission_id]
    return {
        "patch_id": result.patch_id,
        "generated": result.plan.requested_new_items,
        "ad_commission_id": commission_id,
        "commissioned_targets": len(commissioned),
        "rung_violations": result.rung_violations,
    }


def handle_practice_expansion(ctx: JobContext) -> dict[str, Any]:
    """practice_expansion: per-LO item generation (reader-first seeding).

    Payload: ``learning_object_ids`` (explicit, from the section→LO provenance
    mapping) + ``reason``. The completed-probe gate is waived — the trigger is
    the learner having READ the material; rung selection and difficulty
    calibration come from the learner claim / mastery through the standard
    generation path. "Nothing needed" is success, not an error."""

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        generate_post_probe_practice_proposal,
        section_questions_key,
    )
    from learnloop.ai.execution import ModelCheckpoint

    payload = ctx.payload
    lo_ids = [str(lo) for lo in (payload.get("learning_object_ids") or []) if str(lo).strip()]
    source_refs = [ref for ref in (payload.get("source_refs") or []) if isinstance(ref, dict)]
    if not lo_ids:
        raise IngestRunnerError("practice_expansion job requires 'learning_object_ids'.")
    if payload.get("ad_commission_id"):
        return _handle_ad_commission(ctx, lo_ids, str(payload["ad_commission_id"]))
    ctx.report("generation", message=f"Generating practice for {len(lo_ids)} learning object(s)")
    client = ctx.services.synthesis_client(ctx)
    saved = None
    topics = _TopicWork.of(ctx, payload, client)
    if topics is None and str(payload.get("reason") or "").startswith("reader_section_completed:"):
        key = section_questions_key(client, lo_ids, source_refs, payload["reason"])
        saved = ModelCheckpoint(ctx.repo, key, "section_questions", dict)
        completed = saved.load()
        if completed is not None:
            ctx.report("generation", current_window=len(lo_ids), total_windows=len(lo_ids))
            return completed

    parts = []

    def part_status(states: list[dict[str, Any]]) -> None:
        parts[:] = states
        ctx.repo.update_ingest_job_payload(ctx.job_id, {**payload, "question_parts": states})
        if topics is not None:
            topics.record(states)

    def progress(done: int, total: int) -> None:
        ctx.report("generation", message=f"Writing questions: {done} of {total} topics finished",
                   current_window=done, total_windows=total)

    by_parts: dict[str, Any] = {}
    if saved is not None:
        by_parts = {"checkpoint_scope": saved.key, "progress": progress, "part_status": part_status}
    elif topics is not None:
        by_parts = {"topic_scopes": topics.scopes, "applied_patch_ids": topics.earlier_waves(),
                    "progress": progress, "part_status": part_status}
    # A first set from the part of a section read is grounded only in passages the learner saw: its line says so
    # (the finish's would tell the writer the whole section was read), and a note's excerpt goes with it only when
    # it lies wholly within those passages (a note standing for the book can hold text not read yet).
    reason = payload.get("reason") or "reader_section_completed"
    if topics is not None and topics.part_read:
        by_parts["note_filter"] = PART_READ.seen_text_filter(ctx.repo, topics.readings())
        seeds = ("These items seed practice for the part of a section the learner has read so far "
                 f"({reason}); they have not finished it. The cited source spans are the passages they have "
                 "read: ground every item in them and ask about nothing beyond them.")
    else:
        seeds = (f"These items seed practice for material the learner just finished reading ({reason}). "
                 "Ground every item in the cited source spans.")
    try:
        result = generate_post_probe_practice_proposal(
            ctx.vault_root,
            client,
            learning_object_ids=lo_ids,
            require_completed_probe=False,
            target_items_per_lo=SG.READER_FIRST_SET_TARGET,
            max_new_per_lo=SG.READER_FIRST_SET_TARGET,
            source_refs=source_refs,
            **by_parts,
            extra_instructions=(
                f"{seeds} For each item, copy the exact proposal-local ref_id values from "
                "context.source_refs whose learning_object_ids contain that item's learning_object_id "
                "into item.source_ref_ids; do not cite bundles assigned to another Learning Object."
            ),
        )
    except PracticeExpansionError as exc:
        # All targeted LOs already supplied — a legitimate no-op for a trigger.
        if topics is not None:
            topics.nothing_needed()
        return {"generated": 0, "skipped_reason": str(exc)}
    outcome = {
        "patch_id": result.patch_id,
        "generated": result.plan.requested_new_items,
        "rung_violations": result.rung_violations,
    }
    if saved is not None or topics is not None:
        outcome["patch_ids"] = [part["patch_id"] for part in parts if part.get("patch_id")]
    if saved is not None:
        saved.save(outcome)
    return outcome


class _TopicWork:
    """The topic-work rows a practice_expansion job writes for (``topic_keys`` in its payload): their checkpoint
    scopes, the proposals earlier waves of their sections applied, and their state as the parts land."""

    def __init__(self, ctx: JobContext, rows: dict[str, dict[str, Any]], scopes: dict[str, str]) -> None:
        self.ctx, self.rows, self.scopes = ctx, rows, scopes

    @classmethod
    def of(cls, ctx: JobContext, payload: Mapping[str, Any], client: Any) -> "_TopicWork | None":
        keys = payload.get("topic_keys")
        if not isinstance(keys, Mapping) or not keys:
            return None
        from learnloop.ai.execution import model_settings

        batch_id = str(ctx.job.get("batch_id") or "")
        rows = {row["learning_object_id"]: row for row in ctx.repo.topic_question_work_rows(batch_id=batch_id)
                if row["owner"] == "topic"}
        for row in rows.values():
            ctx.repo.update_topic_question_work(row["id"], state="running", model_settings=model_settings(client))
        return cls(ctx, rows, {str(lo): str(key) for lo, key in keys.items()})

    @property
    def part_read(self) -> bool:
        """Whether every topic of this job was claimed from the part of a section read (never mixed: one claim
        is one trigger)."""

        return bool(self.rows) and all(row.get("trigger_event") == "part_read" for row in self.rows.values())

    def readings(self) -> list[str]:
        """The readings this job's topics were claimed on."""

        return list(dict.fromkeys(str(row["extraction_id"]) for row in self.rows.values()))

    def earlier_waves(self) -> list[str]:
        """Proposals of the same sections' topic work queued in other batches: their applied rows are judged with
        this job's parts, so a later wave never repeats or contradicts what an earlier one applied."""

        batch_id = str(self.ctx.job.get("batch_id") or "")
        sections = {(row["extraction_id"], row["section_id"]) for row in self.rows.values()}
        return [patch for extraction_id, section_id in sorted(sections, key=str)
                for row in self.ctx.repo.topic_question_work_rows(extraction_id=extraction_id, section_id=section_id,
                                                                  owner="topic")
                if row["batch_id"] != batch_id for patch in row["proposal_ids"]]

    def record(self, states: list[dict[str, Any]]) -> None:
        for part in states:
            row = self.rows.get(str(part.get("topic_id")))
            if row is None:
                continue
            patch = part.get("patch_id")
            if part.get("error"):
                state = "failed"
            elif not patch:
                continue  # not written yet
            else:
                state = "held" if self.ctx.repo.pending_proposal_items(patch) else "written"
            self.ctx.repo.update_topic_question_work(
                row["id"], state=state, error=part.get("error"), clear_error=not part.get("error"),
                proposal_ids=[patch] if patch else None)

    def nothing_needed(self) -> None:
        for row in self.rows.values():
            self.ctx.repo.update_topic_question_work(row["id"], state="not_needed")


def handle_goal_population(ctx: JobContext) -> dict[str, Any]:
    """Generate and apply the missing practicable supply for one active goal."""

    from learnloop.content.proposals.patches import PatchApplicationError
    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        build_goal_practice_plan,
        generate_goal_practice_proposal,
    )
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.vault.loader import load_vault

    goal_id = str(ctx.payload.get("goal_id") or "")
    if not goal_id:
        raise IngestRunnerError(
            "goal_population job requires a 'goal_id'."
        )
    vault = load_vault(ctx.vault_root)
    sync_vault_state(vault, ctx.repo)
    goal = next(
        (
            candidate
            for candidate in vault.goals
            if candidate.id == goal_id and candidate.status == "active"
        ),
        None,
    )
    if goal is None:
        raise IngestRunnerError(
            f"Goal {goal_id} does not exist or is not active.",
            code="invalid_goal",
        )
    try:
        plan, at_risk_facets = build_goal_practice_plan(
            vault,
            ctx.repo,
            goal,
            target_items_per_lo=5,
            max_new_per_lo=3,
        )
    except PracticeExpansionError as exc:
        raise IngestRunnerError(
            str(exc), code="invalid_generation_request"
        ) from exc
    if not plan.targets:
        return {
            "goal_id": goal_id,
            "generated": 0,
            "applied_count": 0,
            "skipped_reason": "Goal already has enough practicable items.",
        }
    ctx.report(
        "generation",
        message=f"Generating practice for {goal.title}",
    )
    client = ctx.services.synthesis_client(ctx)
    try:
        result = generate_goal_practice_proposal(
            ctx.vault_root,
            client,
            goal_id=goal_id,
            target_items_per_lo=5,
            max_new_per_lo=3,
        )
    except PracticeExpansionError as exc:
        raise IngestRunnerError(
            str(exc), code="goal_population_failed"
        ) from exc
    ctx.report(
        "applying",
        message=f"Adding generated practice to {goal.title}",
    )
    try:
        applied = accept_items(
            ctx.vault_root,
            result.patch_id,
            clock=ctx.clock,
        )
    except PatchApplicationError as exc:
        raise IngestRunnerError(
            str(exc), code="goal_population_apply_failed"
        ) from exc
    return {
        "goal_id": goal_id,
        "proposal_id": result.patch_id,
        "generated": result.plan.requested_new_items,
        "applied_count": applied.applied_count,
        "at_risk_facets": at_risk_facets,
    }


def handle_question_promotion(ctx: JobContext) -> dict[str, Any]:
    """Run one persisted Open-question → practice request.

    Analysis and authoring use separate routed clients. Every terminal failure
    is copied onto the domain request before the generic ingest runner records
    its own job error, so the Open questions UI can explain and retry it.
    """

    from learnloop.ai.errors import CodexTurnTimeout, CodexUnavailable
    event_id = str(ctx.payload.get("event_id") or "")
    if not event_id:
        raise IngestRunnerError("question_promotion job requires an 'event_id'.")
    request = ctx.repo.question_promotion_request(event_id)
    if request is None:
        raise IngestRunnerError(
            f"question promotion request {event_id!r} does not exist."
        )

    def stage(name: str) -> None:
        ctx.repo.update_question_promotion_request(
            event_id, status="running", stage=name, clock=ctx.clock
        )
        ctx.report(name, message=f"Question promotion: {name}")

    def fail(code: str, exc: BaseException, *, retryable: bool) -> IngestRunnerError:
        message = str(exc) or exc.__class__.__name__
        ctx.repo.update_question_promotion_request(
            event_id,
            status="failed",
            stage="failed",
            error_code=code,
            error_message=message,
            retryable=retryable,
            clock=ctx.clock,
        )
        ctx.repo.bump_queue_revision(clock=ctx.clock)
        return IngestRunnerError(
            message,
            code=code,
            details={
                "event_id": event_id,
                "exception_type": exc.__class__.__name__,
            },
            retryable=retryable,
        )

    stage("analysis")
    try:
        analysis_client = ctx.services.promotion_analysis_client(ctx)
        result = promote_tutor_question(
            ctx.vault_root,
            analysis_client,
            event_id=event_id,
            intent=str(request["intent"]),
            subject_id=request.get("subject_id"),
            learning_object_id=request.get("learning_object_id"),
            authoring_client_factory=lambda: ctx.services.promotion_authoring_client(ctx),
            progress=stage,
            clock=ctx.clock,
        )
    except PromotionNoItemError as exc:
        raise fail("no_practice_item", exc, retryable=True) from exc
    except PromotionError as exc:
        raise fail("validation_error", exc, retryable=False) from exc
    except CodexTurnTimeout as exc:
        raise fail("provider_timeout", exc, retryable=True) from exc
    except TimeoutError as exc:
        raise fail("provider_timeout", exc, retryable=True) from exc
    except CodexUnavailable as exc:
        raise fail("provider_unavailable", exc, retryable=True) from exc
    except IngestRunnerError as exc:
        raise fail(exc.code, exc, retryable=exc.retryable) from exc
    except ValueError as exc:
        raise fail("invalid_structured_output", exc, retryable=True) from exc
    except Exception as exc:  # noqa: BLE001 - domain request must not stay "running"
        raise fail("promotion_failed", exc, retryable=True) from exc

    route = str(result.get("route") or "")
    stage_name = "review" if route == "review_required" else "ready"
    ctx.repo.update_question_promotion_request(
        event_id,
        status="completed",
        stage=stage_name,
        promotion_route=route,
        error_code=None,
        error_message=None,
        retryable=False,
        clock=ctx.clock,
    )
    # The promotion service bumps on the actual queue mutation; bump once more
    # for request-state consumers (review/ready chips) even on diagnostic routes.
    ctx.repo.bump_queue_revision(clock=ctx.clock)
    return {
        "question_event_id": event_id,
        "route": route,
        "promotion": result,
    }


def handle_rung_variant(ctx: JobContext) -> dict[str, Any]:
    """rung_variant: author one learner-requested easier/harder sibling item.

    The evidence package was written synchronously at request time; this job is
    only the generation half. Payload: ``request_id``. The service owns the
    request-row status transitions (applied / review_required / failed)."""

    from learnloop.content.authoring.rung_variants import RungVariantError, generate_rung_variant

    request_id = str(ctx.payload.get("request_id") or "")
    if not request_id:
        raise IngestRunnerError("rung_variant job requires a 'request_id'.")
    ctx.report("generation", message="Authoring the requested variant")
    client = ctx.services.rung_variant_client(ctx)
    try:
        result = generate_rung_variant(
            ctx.vault_root, client, request_id=request_id, clock=ctx.clock
        )
    except RungVariantError as exc:
        raise IngestRunnerError(str(exc)) from exc
    if result.get("status") == "failed":
        request = ctx.repo.rung_variant_request(request_id) or {}
        reason = str(request.get("failure_reason") or "Rung variant generation failed.")
        raise IngestRunnerError(
            reason,
            code="rung_variant_failed",
            details={"request_id": request_id, "result": result},
            retryable=True,
        )
    return result


def handle_concept_animation(ctx: JobContext) -> dict[str, Any]:
    """concept_animation: author + validate + render one explainer scene.

    Payload: ``animation_id``. The service owns the row's status machine
    (completed / failed with stage + stderr); consent was checked at request
    time before the row existed."""

    from learnloop.content.authoring.concept_animation import (
        ConceptAnimationError,
        generate_concept_animation,
    )

    animation_id = str(ctx.payload.get("animation_id") or "")
    if not animation_id:
        raise IngestRunnerError("concept_animation job requires an 'animation_id'.")
    row = ctx.repo.concept_animation(animation_id)
    use_video_model = bool(row) and (row.get("renderer") or "manim") == "video_model"
    video_client = None
    try:
        client = ctx.services.animation_client(ctx)
        if use_video_model:
            video_client = ctx.services.video_client(ctx)
    except IngestRunnerError as exc:
        # A provider that cannot be built would leave the row wedged in
        # "queued"; mark it failed so the inspector shows why.
        if row is not None and row.get("status") in ("queued", "generating"):
            ctx.repo.update_concept_animation(
                animation_id,
                status="failed",
                failure_stage="video_model" if use_video_model else "generation",
                failure_reason=str(exc)[:2000],
                clock=ctx.clock,
            )
        raise
    try:
        # The first report is also the first cancellation point: inside the
        # try so a job cancelled before the service ran still gets a terminal row.
        ctx.report(
            "generation",
            message="Writing the video storyboard" if use_video_model else "Authoring the explainer scene",
        )
        row = generate_concept_animation(
            ctx.vault_root,
            client,
            animation_id=animation_id,
            renderer=ctx.services.animation_renderer,
            clock=ctx.clock,
            video_client=video_client,
            report=lambda phase, message: ctx.report(phase, message=message),
            cancellation=(JobCancelled,),
        )
    except ConceptAnimationError as exc:
        raise IngestRunnerError(str(exc), code=exc.code) from exc
    except JobCancelled:
        # The service marks its own row cancelled; this covers a cancellation
        # that landed before it was entered.
        current = ctx.repo.concept_animation(animation_id)
        if current is not None and current.get("status") not in ("completed", "failed", "cancelled"):
            ctx.repo.update_concept_animation(
                animation_id,
                status="cancelled",
                failure_stage="video_model" if use_video_model else "render",
                failure_reason="cancelled by the learner",
                clock=ctx.clock,
            )
        raise
    # Compact job result: the status RPC serves the full row (code, stderr).
    return {
        "animation_id": row["id"],
        "concept_id": row["concept_id"],
        "status": row["status"],
        "video_file_name": row.get("video_file_name"),
        "failure_stage": row.get("failure_stage"),
    }
