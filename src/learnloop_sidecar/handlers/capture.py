"""Desktop-only inbox operations; no mobile entrypoint dependencies."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Literal

from pydantic import Field

from learnloop import capture
from learnloop.capture.routing import begin_route, pending_route, read_route_intent, update_route_intent
from learnloop.config.loader import global_settings_path
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class ListCaptureInput(ParamsModel):
    status: Literal["new", "routed", "dismissed", "purged", "delete_pending"] | None = "new"
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class CaptureInput(ParamsModel):
    capture_id: str


def capture_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except capture.CaptureError as exc:
        raise SidecarError(exc.code, exc.message) from exc


def record_route(repository, capture_id: str | None, route: str, result_refs: dict[str, Any]) -> None:
    """Call only after the destination's durable operation succeeds."""
    if capture_id is not None:
        capture_call(capture.route_capture, repository, capture_id, route=route, result_refs=result_refs)


def _request_hash(params) -> str:
    return hashlib.sha256(json.dumps(
        params.model_dump(), sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def destination_committed(ctx, repository, route: str | None, destination_id: str) -> bool:
    """Whether an intent's destination exists. Anything uncertain counts as committed."""
    try:
        if route == "make_card":
            from learnloop.vault.loader import load_vault

            vault, _ = ctx.require_vault()
            # Fresh from disk, exactly as author_item's own idempotency check.
            return "pi_capture_" + destination_id.lower() in load_vault(vault.root).practice_items
        if route == "quick_add":
            return repository.get_ingest_batch("batch_capture_" + destination_id) is not None
        if route == "ask_tutor":
            return repository.question_event(destination_id) is not None
    except Exception:
        logging.getLogger(__name__).exception("Could not establish whether a capture destination exists")
    return True


def route_intent(repository, params, route: str, *, create=True, ctx=None) -> dict | None:
    """Read or begin this request's intent.

    With ``ctx``, a different request (or route) replaces an unfinished intent
    once its destination is established absent, e.g. after a crash before the
    destination write when the dialog's inputs were lost. Without it, or if the
    destination may exist, the original request must be finished instead.
    """
    if params.capture_id is None:
        return None
    request_hash = _request_hash(params)
    request = params.model_dump(mode="json")
    try:
        if create:
            return capture_call(begin_route, repository, params.capture_id, route=route,
                                request_hash=request_hash, request=request)
        return capture_call(read_route_intent, repository, params.capture_id,
                            route=route, request_hash=request_hash)
    except SidecarError as exc:
        if ctx is None or exc.code != "capture_conflict":
            raise
        stale = capture_call(pending_route, repository, params.capture_id)
        if (stale is None or "response" in stale
                or destination_committed(ctx, repository, stale["route"], stale["destination_id"])):
            raise
        if not create:
            return None  # The caller validates, then begins the replacement intent.
        return capture_call(begin_route, repository, params.capture_id, route=route,
                            request_hash=request_hash, request=request,
                            supersede=stale["destination_id"])


def finish_route(ctx, repository, capture_id, route, refs, response, *, reload=False):
    """A failed projection/refresh cannot turn a committed destination into failure.

    A later identical retry replays the saved response or recovers the stable
    destination identity if even the response receipt could not be written.
    """
    if capture_id is not None:
        try:
            capture_call(update_route_intent, repository, capture_id, response=response)
            record_route(repository, capture_id, route, refs)
        except Exception:
            logging.getLogger(__name__).exception("Destination committed; capture route receipt needs repair")
            response = {**response, "capture_route_pending": True}
    if reload:
        try:
            ctx.reload(maintenance=False)
        except Exception:
            if capture_id is None:
                raise
            logging.getLogger(__name__).exception("Destination committed; snapshot refresh needs retry")
            response = {**response, "reload_pending": True}
    return versioned(response)


@method("get_inbox_summary")
def get_inbox_summary(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    summary = capture_call(capture.get_inbox_summary, repository)
    pinned = capture.pinned_vault_info(global_settings_path().parent / "mobile.toml", vault.root)
    return versioned({**summary, **pinned})


@method("list_capture_inbox", ListCaptureInput)
def list_capture_inbox(ctx: SidecarContext, params: ListCaptureInput) -> dict[str, Any]:
    _, repository = ctx.require_vault()
    rows = capture_call(capture.list_captures, repository, status=params.status, limit=params.limit, offset=params.offset)
    return versioned({"captures": rows})


@method("dismiss_capture", CaptureInput)
def dismiss_capture(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]:
    _, repository = ctx.require_vault()
    return versioned({"capture": capture_call(capture.dismiss_capture, repository, params.capture_id)})


@method("get_capture_media", CaptureInput)
def get_capture_media(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]:
    """Bounded photo preview for manual routing; resolved from the stored hash only."""
    vault, repository = ctx.require_vault()
    return versioned(capture_call(capture.capture_media_preview, repository, params.capture_id,
                                  root=vault.root))


@method("resume_capture_route", CaptureInput)
def resume_capture_route(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]:
    """Finish a capture's unfinished save from its persisted request.

    Replays the exact original request through its own handler, so committed
    destinations are recovered (never duplicated) and uncommitted ones created.
    """
    from learnloop_sidecar.handlers import ingest, item_authoring, tutor_qa

    _, repository = ctx.require_vault()
    pending = capture_call(pending_route, repository, params.capture_id)
    if pending is None or "request" not in pending:
        raise SidecarError("capture_conflict", "This capture has no unfinished save to resume.")
    handlers = {
        "make_card": (item_authoring.author_practice_item, item_authoring.AuthorPracticeItemInput),
        "quick_add": (ingest.confirm_quick_add_rpc, ingest.ConfirmQuickAddInput),
        "ask_tutor": (tutor_qa.ask_tutor_question, tutor_qa.AskTutorQuestionInput),
    }
    if pending["route"] not in handlers:
        raise SidecarError("capture_conflict", "This capture's unfinished save cannot be resumed.")
    handler, model = handlers[pending["route"]]
    request = model.model_validate(pending["request"])
    if request.capture_id != params.capture_id or _request_hash(request) != pending["request_hash"]:
        raise SidecarError("capture_conflict", "This capture's saved request does not match its intent.")
    return versioned({"route": pending["route"], "result": handler(ctx, request)})


@method("purge_capture", CaptureInput)
def purge_capture(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return versioned({"capture": capture_call(capture.purge_capture, repository, params.capture_id, root=vault.root)})
