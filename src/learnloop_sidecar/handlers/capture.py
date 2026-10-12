"""Desktop-only inbox operations; no mobile entrypoint dependencies."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Literal

from pydantic import Field

from learnloop import capture
from learnloop.capture.routing import begin_route, read_route_intent, update_route_intent
from learnloop.config.loader import global_settings_path
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method


class ListCaptureInput(ParamsModel):
    status: Literal["new", "routed", "dismissed", "purged"] | None = "new"
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


def route_intent(repository, params, route: str, *, create=True) -> dict | None:
    if params.capture_id is None:
        return None
    request_hash = hashlib.sha256(json.dumps(
        params.model_dump(), sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    return capture_call(begin_route if create else read_route_intent, repository,
                        params.capture_id, route=route, request_hash=request_hash)


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


@method("purge_capture", CaptureInput)
def purge_capture(ctx: SidecarContext, params: CaptureInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return versioned({"capture": capture_call(capture.purge_capture, repository, params.capture_id, root=vault.root)})
