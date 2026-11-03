"""Mobile PR-5 (``spec_mobile_tailnet_v1`` §6.8, T8): who a request comes from.

The device and surface of a request come from the authenticated token, carried
on the handler context, and never from request parameters. The phone host sets
``SidecarContext.request_origin`` around each call
(:meth:`SidecarContext.acting_as`); the desktop sidecar leaves it ``None``, which
means the desktop, so every desktop write and response stays as it was.

Four things read it:

* **provenance:** an attempt's ``entry_surface`` and an offer's or a binding's
  surface (:func:`practice_surface`, :func:`offer_surface`). A session's
  ``owner_device_id`` changes on handoff, so it never says which device made an
  attempt: the request does;
* **session ownership:** ``SidecarContext.origin_device_id`` (§6.5);
* **device eligibility:** :func:`device_class` (§6.4);
* **desktop freshness:** :func:`host_mutation` (PR-7, §3.3).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from learnloop.scheduling.device_eligibility import DESKTOP, PHONE
from learnloop_sidecar.errors import SidecarError

#: The surfaces the desktop has always recorded (the stores' own defaults).
DESKTOP_PRACTICE = "desktop_practice"
DESKTOP_QUEUE = "desktop_queue"
#: The surfaces of a phone request (§6.8, G11).
PHONE_PRACTICE = "phone_practice"
PHONE_QUEUE = "phone_queue"


@dataclass(frozen=True)
class RequestOrigin:
    """One authenticated caller: the paired device and the surface it runs."""

    device_id: str
    surface: str = PHONE

    def __post_init__(self) -> None:
        if not self.device_id or not self.device_id.strip():
            raise ValueError("A request origin names a device.")
        if self.surface != PHONE:
            raise ValueError(f"Unknown request surface {self.surface!r}.")


def device_class(origin: RequestOrigin | None) -> str:
    """The class the eligibility module asks about (§6.4); None is the desktop."""

    return DESKTOP if origin is None else origin.surface


def practice_surface(origin: RequestOrigin | None) -> str:
    """``entry_surface`` of an attempt and of a submission's binding."""

    return DESKTOP_PRACTICE if origin is None else PHONE_PRACTICE


def offer_surface(origin: RequestOrigin | None) -> str:
    """``entry_surface`` of a published scheduler offer."""

    return DESKTOP_QUEUE if origin is None else PHONE_QUEUE


#: A refusal whose mutation committed all the same: the attempt is in, and only
#: the completion's receipt is missing (``practice._submission_committed``).
_COMMITTED_REFUSALS = frozenset({"submission_committed"})


def bump_for_host(ctx: Any) -> None:
    """Tell the desktop a host request changed what it shows (PR-7, §3.3).

    Attempts and session rows carry no revision of their own, so ``queue_revision``
    is what the desktop's poll sees. The mutation has committed by now: a failed
    bump is logged, never raised, because the learner's write stands. It stays
    owed on its own vault (``SidecarContext.host_bumps_owed``) and the host's next
    request on that vault pays it (:meth:`SidecarContext.acting_as`). Nothing else
    recovers it: the desktop's poll refetches on a token change or a reload, and a
    window's return only reads (orchestrator ruling R1). A debt dies with the
    process, so M2's host bumps once at start, which moves the token. The desktop's
    own writes keep today's behaviour (no origin, no bump): its mutation wrappers
    invalidate.
    """

    if ctx.request_origin is None:
        return
    _vault, repository = ctx.require_vault()
    try:
        repository.bump_queue_revision()
    except sqlite3.Error:
        ctx.host_bumps_owed.add(ctx.vault_root)
        logging.getLogger(__name__).warning("host mutation committed; queue revision not bumped", exc_info=True)
    else:
        ctx.host_bumps_owed.discard(ctx.vault_root)


def host_mutation(handler: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
    """A handler whose committed work changes what the desktop shows (PR-7, §3.3).

    The shared operation is the one place the host and the desktop both go, so the
    bump is here and the M2 host has nothing to remember: its job completions
    (``submit_*``, a clarification's regrade), a skip, a session start, an adopt or
    an end each bump once, after the handler's commit. A typed refusal changed
    nothing and does not bump. A long job with no RPC of its own (M2b's
    transcription) calls :func:`bump_for_host` when it completes.
    """

    @wraps(handler)
    def wrapped(ctx: Any, params: Any) -> Any:
        try:
            result = handler(ctx, params)
        except SidecarError as error:
            if error.code in _COMMITTED_REFUSALS:
                bump_for_host(ctx)
            raise
        bump_for_host(ctx)
        return result

    return wrapped
