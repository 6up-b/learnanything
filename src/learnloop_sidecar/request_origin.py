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

from learnloop.scheduling.device_eligibility import DESKTOP, PHONE, PHONE_PLAN
from learnloop_sidecar.errors import SidecarError

#: The surfaces the desktop has always recorded (the stores' own defaults).
DESKTOP_PRACTICE = "desktop_practice"
DESKTOP_QUEUE = "desktop_queue"
#: The surfaces of a phone request (§6.8, G11; mobile v2 §2.2 adds the plan's).
PHONE_PRACTICE = "phone_practice"
PHONE_QUEUE = "phone_queue"


@dataclass(frozen=True)
class RequestOrigin:
    """One authenticated caller: the paired device and the surface it runs."""

    device_id: str
    surface: str = PHONE
    #: A job the host accepted for this session: its acceptance checked the owner, in the
    #: transaction that committed the job, and a handoff since does not refuse it (§6.5).
    #: Only the host's job worker sets it, from the accepted row; never a parameter.
    accepted_session_id: str | None = None
    #: Mobile v2 V3 (owner decision D3): the phone host's kill switch ``phone_probes`` (mobile.toml), which the
    #: host sets from its own config, never a parameter. False (an origin made without it) is V2's phone.
    phone_probes: bool = False
    #: Mobile v2 V4: the phone host's kill switch ``phone_reader`` (mobile.toml), set by the host from its own
    #: config, never a parameter. On, the phone's Reader takes the plan's reading blocks it can show, and the
    #: image, page and asset prompts whose targets the host serves (spec §2.3). False is V3's phone.
    phone_reader: bool = False

    def __post_init__(self) -> None:
        if not self.device_id or not self.device_id.strip():
            raise ValueError("A request origin names a device.")
        if self.surface != PHONE:
            raise ValueError(f"Unknown request surface {self.surface!r}.")


def device_class(origin: RequestOrigin | None) -> str:
    """The class the eligibility module asks about (§6.4); None is the desktop."""

    return DESKTOP if origin is None else origin.surface


def phone_probes_on(origin: RequestOrigin | None, config: Any) -> bool:
    """Mobile v2 V3 (owner decision D3): a phone origin serves and answers phone-eligible probes, diagnostic and
    FG1's generated ones, under the probe contract. The host's switch (``phone_probes``) AND the vault at the
    successor's tag (``PHONE_PROBES_VERSIONS``); below it, or switched off, the phone is V2's exactly. Never true for
    the desktop, whose serving doesn't change."""

    from learnloop.algorithm_versions import PHONE_PROBES_VERSIONS

    if origin is None or not origin.phone_probes:
        return False
    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    return version in PHONE_PROBES_VERSIONS


def phone_reader_on(origin: RequestOrigin | None) -> bool:
    """Mobile v2 V4: a phone origin whose host has its Reader on (``phone_reader``). Never the desktop."""

    return origin is not None and bool(origin.phone_reader)


def practice_surface(origin: RequestOrigin | None) -> str:
    """``entry_surface`` of an attempt and of a submission's binding."""

    return DESKTOP_PRACTICE if origin is None else PHONE_PRACTICE


def offer_surface(origin: RequestOrigin | None) -> str:
    """``entry_surface`` of a published scheduler offer."""

    return DESKTOP_QUEUE if origin is None else PHONE_QUEUE


def plan_surface(origin: RequestOrigin) -> str:
    """Mobile v2 §2.2: the surface a phone's plan step and its boundary decisions record. The
    desktop's plan decisions keep their own (``router.plan_log.SURFACE``); this is never asked
    for a None origin."""

    if origin is None:
        raise ValueError("The desktop's plan surface is the plan log's own.")
    return PHONE_PLAN


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
