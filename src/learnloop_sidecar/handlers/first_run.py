"""UX Phase 1 RPCs: one Add, the AI connection sheet, and the book card's actions.

``add_source`` is the one verb for a book, paper, web page or video (spec §6.2):
a local file is registered and its original stored before the call returns, so
the Reader opens on it at once; extraction and the automatic question build run
in the durable queue (``learnloop.content.pipeline.add_source``).

``get_ai_connection`` / ``connect_ai`` are the "connect once, consent once"
sheet (§6.6, Q4): connecting ChatGPT or an OpenRouter key routes every use case
to it, and the learner's one OK is recorded in the library's config with its
date, then releases every book that was waiting for it.

``source_action`` runs the one action a book card's status line offers: undo,
build now, retry, read scanned pages with text recognition, the separate OK for
sending a whole file out, or keeping a book on this computer.

Desktop only (machine paths, credentials, paid builds): pinned in
tests/test_mobile_allowlist.py.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from learnloop.clock import utc_now_iso
from learnloop.content.pipeline import add_source as core
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams, ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ingest import _parse_page_selection
from learnloop_sidecar.registry import method

logger = logging.getLogger(__name__)

# The use cases "Continue with ChatGPT" / an OpenRouter key take over. Video
# generation stays OpenRouter-video-only and transcription keeps its own route.
_CONNECT_USE_CASES = ("grading", "diagnosis", "ingest", "tutor", "animation")
_DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-chat"


# Seams the tests replace (no network, no sign-in store).
def authoring_route_for(vault) -> core.AuthoringRoute:
    return core.authoring_route_for(vault.root, vault.config)


def chatgpt_plan_ready() -> bool:
    from learnloop.ai.chatgpt_plan.session import PlanSession

    try:
        return PlanSession().status().readiness()[0] == "ready"
    except Exception:  # noqa: BLE001 - an unreadable store reads as not signed in
        return False


def chatgpt_plan_models() -> list[str]:
    from learnloop.ai.providers.chatgpt_plan import list_plan_models

    return [model["slug"] for model in list_plan_models()]


# ---------------------------------------------------------------------------
# add_source
# ---------------------------------------------------------------------------


class AddSourceInput(ParamsModel):
    sources: list[str]
    # Add → More options (spec §8.2). Nothing here is required.
    pages: str | None = None
    problem_set: bool = False
    keep_local: bool = False
    text_recognition: bool = False


@method("add_source", AddSourceInput)
def add_source_rpc(ctx: SidecarContext, params: AddSourceInput) -> dict[str, Any]:
    """Add one or more sources; the first that can open is ``opened``."""

    vault, _repository = ctx.require_vault()
    sources = [source.strip() for source in params.sources if source and source.strip()]
    if not sources:
        raise SidecarError("unsupported_source", core.UNSUPPORTED_MESSAGE)
    page_selection = _parse_page_selection(params.pages) if params.pages and params.pages.strip() else None
    if page_selection is not None and len(sources) > 1:
        raise SidecarError("invalid_page_range", "Only some pages works with one file at a time.")
    options = core.AddSourceOptions(
        page_selection=tuple(page_selection) if page_selection else None,
        problem_set=params.problem_set,
        keep_local=params.keep_local,
        text_recognition=params.text_recognition,
    )
    items = [core.add_source(vault, ctx.ingest_jobs, source, options) for source in sources]
    opened = next((item for item in items if item["status"] in {"added", "existing", "queued"}), None)
    return versioned({"items": items, "opened": opened})


# ---------------------------------------------------------------------------
# get_ai_connection / connect_ai
# ---------------------------------------------------------------------------


def _connection_payload(ctx: SidecarContext) -> dict[str, Any]:
    from learnloop.decider_judgments import connection_note

    vault, _repository = ctx.require_vault()
    route = authoring_route_for(vault)
    record = vault.config.ai.consent.get(route.consent_key)
    label = core.consent_label(route.consent_key)
    # The Decider's small judgments go to Perplexity, not to the AI connected
    # here: the one OK says so in the words Settings uses (Tier 1, D6).
    decider_note = connection_note(vault.config)
    what_leaves = core.what_leaves(label)
    if not route.ready:
        needs: str | None = "connect"
    elif record is None:
        needs = "consent"
    else:
        needs = None
    return {
        "can_author": route.ready,
        "provider": route.provider,
        "provider_label": label,
        "consent_key": route.consent_key,
        "consented": record is not None,
        "consented_at": record.granted_at if record is not None else None,
        "needs": needs,
        "message": None if route.ready else route.message,
        "what_leaves": what_leaves if decider_note is None else f"{what_leaves} {decider_note}",
        "decider_note": decider_note,
        "chatgpt_signed_in": chatgpt_plan_ready(),
        "openrouter_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


@method("get_ai_connection", EmptyParams)
def get_ai_connection(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]:
    """Can an AI write questions in this library, and has the learner said OK?"""

    return versioned(_connection_payload(ctx))


class ConnectAiInput(ParamsModel):
    # "current": the OK for the route already configured (e.g. Codex).
    provider: Literal["chatgpt", "openrouter", "current"]
    model: str | None = None


def _route_every_use_case(updates: dict[tuple[str, ...], Any], target: str) -> None:
    from learnloop.ops.settings_store import USE_CASE_ROUTES

    updates[("ai", "active_provider")] = target
    for use_case in _CONNECT_USE_CASES:
        for task in USE_CASE_ROUTES[use_case]:
            updates[("ai", "routing", task)] = target


@method("connect_ai", ConnectAiInput)
def connect_ai(ctx: SidecarContext, params: ConnectAiInput) -> dict[str, Any]:
    """Connect an AI for every use case and record the learner's one OK."""

    from learnloop.config import global_ai_defaults_path
    from learnloop.ops.settings_store import SettingsStoreError, apply_config_updates, save_ai_settings_to

    vault, _repository = ctx.require_vault()
    config = vault.config
    updates: dict[tuple[str, ...], Any] = {}
    if params.provider == "chatgpt":
        if not chatgpt_plan_ready():
            raise SidecarError("chatgpt_not_signed_in", "Sign in with ChatGPT first, then connect.")
        existing = config.ai.providers.get("chatgpt")
        model = (params.model or "").strip() or (
            existing.model if existing is not None and existing.type == "chatgpt_plan" and existing.model else ""
        )
        if not model:
            try:
                models = chatgpt_plan_models()
            except Exception as exc:  # noqa: BLE001 - surfaced as one plain line
                raise SidecarError(
                    "chatgpt_models_unavailable", "Couldn't reach ChatGPT to finish connecting. Try again.",
                    retryable=True, details={"error": str(exc)},
                ) from exc
            if not models:
                raise SidecarError("chatgpt_no_models", "Your ChatGPT account lists no models LearnLoop can use.")
            model = models[0]
        updates[("ai", "providers", "chatgpt", "type")] = "chatgpt_plan"
        updates[("ai", "providers", "chatgpt", "model")] = model
        _route_every_use_case(updates, "chatgpt")
        key = "chatgpt"
    elif params.provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise SidecarError("openrouter_key_missing", "Add your OpenRouter key first, then connect.")
        if "openrouter" not in config.ai.providers:
            updates[("ai", "providers", "openrouter", "type")] = "openrouter"
            updates[("ai", "providers", "openrouter", "api_key_env")] = "OPENROUTER_API_KEY"
            updates[("ai", "providers", "openrouter", "model")] = (params.model or "").strip() or _DEFAULT_OPENROUTER_MODEL
        elif params.model and params.model.strip():
            updates[("ai", "providers", "openrouter", "model")] = params.model.strip()
        _route_every_use_case(updates, "openrouter")
        key = "openrouter"
    else:
        route = authoring_route_for(vault)
        if not route.ready:
            raise SidecarError(
                "ai_not_connected", "Connect an AI first: Continue with ChatGPT, or add an OpenRouter key.",
                details={"message": route.message},
            )
        key = route.consent_key
    updates[("ai", "consent", key, "granted_at")] = utc_now_iso()
    updates[("ai", "consent", key, "data_flow")] = core.DATA_FLOW

    config_path = vault.root / "learnloop.toml"
    try:
        apply_config_updates(config_path, updates)
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    if params.provider != "current":
        # A freshly routed grading provider must not be shadowed by a
        # session-only override chosen earlier.
        ctx.grading_provider_override = None
    ctx.reload(maintenance=False)
    try:
        save_ai_settings_to(config_path, global_ai_defaults_path())
    except SettingsStoreError as exc:  # best effort, like Settings
        logger.warning("could not persist global AI defaults: %s", exc)
    released = core.release_waiting_builds(ctx.ingest_jobs)
    return versioned({**_connection_payload(ctx), "released": released})


# ---------------------------------------------------------------------------
# source_action
# ---------------------------------------------------------------------------


class SourceActionInput(ParamsModel):
    source_id: str | None = None
    # A link still being fetched has no source yet; its Add batch stands in.
    batch_id: str | None = None
    action: Literal[
        "undo_questions", "build_now", "build_whole_book", "retry", "text_recognition",
        "allow_upload", "keep_local", "share_with_ai",
    ]


def _allow_file_upload(ctx: SidecarContext) -> None:
    """The separate OK for sending whole files out (spec §6.6, review F1),
    recorded once with its date like the connection's OK."""

    from learnloop.config import global_ai_defaults_path
    from learnloop.ops.settings_store import SettingsStoreError, apply_config_updates, save_ai_settings_to

    vault, _repository = ctx.require_vault()
    config_path = vault.root / "learnloop.toml"
    try:
        apply_config_updates(config_path, {
            ("ai", "consent", core.FILE_UPLOAD_CONSENT, "granted_at"): utc_now_iso(),
            ("ai", "consent", core.FILE_UPLOAD_CONSENT, "data_flow"): core.FILE_UPLOAD_DATA_FLOW,
        })
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    ctx.reload(maintenance=False)
    try:
        save_ai_settings_to(config_path, global_ai_defaults_path())
    except SettingsStoreError as exc:  # best effort, like connect_ai
        logger.warning("could not persist global AI defaults: %s", exc)


@method("source_action", SourceActionInput)
def source_action(ctx: SidecarContext, params: SourceActionInput) -> dict[str, Any]:
    """Run the one action a book card's status line (or its details) offers."""

    vault, repository = ctx.require_vault()
    result: dict[str, Any] = {"source_id": params.source_id, "action": params.action}
    if params.source_id is None:
        if params.action not in {"retry", "allow_upload"} or not params.batch_id:
            raise SidecarError("source_not_found", "Choose a book first.")
        if params.action == "allow_upload":
            _allow_file_upload(ctx)
        batch = ctx.ingest_jobs.resume_batch(params.batch_id)
        if batch is None:
            raise SidecarError("ingest_batch_not_found", "That add is no longer in the queue.")
        return versioned({**result, "batch_id": params.batch_id})
    artifact = repository.get_source_artifact(params.source_id)
    if artifact is None:
        raise SidecarError("source_not_found", "That book is no longer in your library.")

    if params.action == "undo_questions":
        result["reverted"] = core.undo_source_questions(ctx.ingest_jobs, params.source_id)
        ctx.reload(maintenance=False)
    elif params.action == "build_now":
        result["batch_id"] = core.request_auto_build(ctx.ingest_jobs, params.source_id, approved=True)
    elif params.action == "build_whole_book":
        extraction = core._completed_extraction(repository, params.source_id)
        if extraction is None:
            raise SidecarError("not_ready", "This book is still being prepared. Try again in a minute.", retryable=True)
        from learnloop.content.sources.source_outline import build_source_outline

        chapters = core.outline_chapters(build_source_outline(repository, extraction[1]))
        # Every chapter not built or building, failed ones included (F6).
        result["batch_id"] = core.request_auto_build(
            ctx.ingest_jobs, params.source_id, chapter_ids=[chapter.unit_id for chapter in chapters]
        )
    elif params.action == "retry":
        if core._completed_extraction(repository, params.source_id) is None:
            batch_id = core.latest_add_batch(repository, params.source_id)
            if batch_id is None:
                raise SidecarError("nothing_to_retry", "There is nothing to try again for this book.")
            ctx.ingest_jobs.resume_batch(batch_id)
        else:
            _planner, outcome = core.latest_planner(repository, params.source_id)
            if (outcome or {}).get("outcome") == "building":
                # The zero-model repair of a preserved result first (F11).
                batch_id = core.retry_build(ctx.ingest_jobs, params.source_id)
            else:
                # A planner that failed plans again (never as an approval).
                batch_id = core.request_auto_build(ctx.ingest_jobs, params.source_id)
        result["batch_id"] = batch_id
    elif params.action == "allow_upload":
        _allow_file_upload(ctx)
        batch_id = core.latest_add_batch(repository, params.source_id)
        if batch_id is not None:
            ctx.ingest_jobs.resume_batch(batch_id)
        result["batch_id"] = batch_id
    elif params.action == "keep_local":
        core.keep_on_this_computer(ctx.ingest_jobs, params.source_id)
    elif params.action == "share_with_ai":
        # A book not readable yet resumes its Add, which asks for the separate
        # whole-file OK before anything is uploaded (re-review F13).
        result["batch_id"] = core.share_with_ai(ctx.ingest_jobs, params.source_id)
    else:  # text_recognition: read again with OCR; questions already built stay.
        keep_local = bool(artifact.get("keep_local"))
        if not core.text_recognition_available(keep_local=keep_local, config=vault.config):
            # Plain words and how to get it (usability round 2); the shelf
            # offers this only where it can run, so this is a safety net.
            raise SidecarError(
                "text_recognition_unavailable",
                "Text recognition isn't set up, so LearnLoop can't read the words of a scan yet. "
                + core.TEXT_RECOGNITION_HOW_TO,
            )
        source = str(artifact.get("canonical_uri") or "")
        # A book that never had text (a scan) gets its questions once it is
        # read (usability round 1, U7); one already read keeps the ones it has.
        never_read = core._completed_extraction(repository, params.source_id) is None
        result["batch_id"] = ctx.ingest_jobs.enqueue_add_source(
            source,
            source_id=params.source_id,
            options=core.AddSourceOptions(text_recognition=True, keep_local=keep_local),
            auto_build=never_read,
        )
    return versioned(result)
