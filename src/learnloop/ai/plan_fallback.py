"""Ask before using OpenRouter while the ChatGPT plan is unavailable.

Plan-first transport T1 (owner decision 2026-10-21): when the plan cannot
serve a route (signed out, paused, usage limit, a refused or unrefreshable
token), the feature reports "unavailable" through its existing degrade path
AND LearnLoop asks whether to use OpenRouter instead. It never falls back
silently:

* An **offer** exists only when ``ai.plan_fallback_profile`` names an
  ``openrouter`` profile whose API key is present (:func:`offer_profile`).
  Routing records it on the unavailable runtime
  (``AIRuntimeReport.fallback_available``) and in the request's
  :class:`OfferCollector`; the sidecar attaches the typed hint
  (``fallback_available: "openrouter"``, ``fallback_tasks``,
  ``fallback_profile``) to the RPC's error or result, the CLI to its JSON.
* Only a **grant** routes a task to OpenRouter: the desktop's "Use OpenRouter
  instead" (RPC ``ai_use_fallback``) grants the feature's tasks for this
  sidecar session; ``LEARNLOOP_AI_FALLBACK=openrouter`` grants every task for
  one CLI command. A granted request is an ordinary metered request on that
  profile, so every feature's existing spend caps apply to it.

Nothing here sends anything; it is bookkeeping between routing and the
adapters.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import os
import threading
from typing import Any

from learnloop.config import LearnLoopConfig

#: The one fallback kind the owner approved.
FALLBACK_KIND = "openrouter"
#: CLI: the learner's choice for one command ("openrouter").
FALLBACK_ENV = "LEARNLOOP_AI_FALLBACK"
_OPENROUTER_TYPE = "openrouter"
_DEFAULT_KEY_ENV = "OPENROUTER_API_KEY"


def offer_profile(config: LearnLoopConfig) -> str | None:
    """The OpenRouter profile LearnLoop may offer, or ``None`` (no profile, wrong type, no key)."""

    name = (config.ai.plan_fallback_profile or "").strip()
    if not name:
        return None
    profile = config.ai.providers.get(name)
    if profile is None or profile.type.strip().lower() != _OPENROUTER_TYPE:
        return None
    key_env = getattr(profile, "api_key_env", None) or _DEFAULT_KEY_ENV
    return name if os.environ.get(key_env) else None


def offer_sentence() -> str:
    return ("OpenRouter is set up and can do this instead if you choose: \"Use OpenRouter instead\" "
            f"(desktop) or {FALLBACK_ENV}={FALLBACK_KIND} (CLI). Nothing is sent to OpenRouter until you do.")


# ---------------------------------------------------------------------------
# Offers made while one request (an RPC, a CLI command) runs
# ---------------------------------------------------------------------------


@dataclass
class OfferCollector:
    #: Tasks whose plan route was unavailable when resolved, and the profile offered.
    unavailable: dict[str, str] = field(default_factory=dict)
    #: Tasks resolved to a ready plan route (offered if a plan call then fails).
    plan_routes: dict[str, str] = field(default_factory=dict)
    #: A plan request failed for availability (usage limit, sign-in, token).
    plan_failed: bool = False
    #: The plan needs a sign-in (the desktop also offers "Continue with ChatGPT").
    signed_out: bool = False

    def hint(self) -> dict[str, Any] | None:
        """The typed hint for the adapter, or ``None`` when nothing was offered."""

        tasks = dict(self.unavailable)
        if self.plan_failed:
            for task, profile in self.plan_routes.items():
                tasks.setdefault(task, profile)
        if not tasks:
            return None
        return {
            "fallback_available": FALLBACK_KIND,
            "fallback_profile": sorted(set(tasks.values()))[0],
            "fallback_tasks": sorted(tasks),
            "plan_signed_out": self.signed_out,
        }


_COLLECTOR: ContextVar[OfferCollector | None] = ContextVar("learnloop_plan_fallback_offers", default=None)
#: Set inside :func:`quiet`: a readiness probe, not a feature the learner used.
_QUIET: ContextVar[bool] = ContextVar("learnloop_plan_fallback_quiet", default=False)


@contextmanager
def quiet() -> Iterator[None]:
    """Make no offer, and honour no grant, for routes resolved in this block.

    For readiness probes (the snapshot's health line, startup maintenance):
    they report the plan's state themselves, and the learner is asked about
    OpenRouter only when a feature they used could not run. A grant is for
    the feature the learner used, never for background work: a deferred
    regrade backlog found at startup waits for the plan even while
    "grading" is granted for the session.
    """

    token = _QUIET.set(True)
    try:
        yield
    finally:
        _QUIET.reset(token)


def _collector() -> OfferCollector | None:
    return None if _QUIET.get() else _COLLECTOR.get()


@contextmanager
def collecting() -> Iterator[OfferCollector]:
    """Collect the offers made while the block runs (one RPC, or one background job).

    A nested block (a job run inline inside its RPC) also hands its offers
    to the enclosing collector when it ends, so neither loses them.
    """

    parent = _COLLECTOR.get()
    collector = OfferCollector()
    token = _COLLECTOR.set(collector)
    try:
        yield collector
    finally:
        _COLLECTOR.reset(token)
        if parent is not None:
            _merge_into(parent, collector.hint())


def _merge_into(collector: OfferCollector, hint: dict[str, Any] | None) -> None:
    if not hint:
        return
    profile = str(hint.get("fallback_profile") or FALLBACK_KIND)
    for task in hint.get("fallback_tasks") or []:
        collector.unavailable.setdefault(str(task), profile)
    collector.signed_out = collector.signed_out or bool(hint.get("plan_signed_out"))


def relay_hint(hint: dict[str, Any] | None) -> None:
    """Offer again, in the current request, what a background job's request offered.

    A job (a hint, a library ask, margin notes, a reading path) runs in its
    own thread with its own collector (:func:`collecting`) and keeps its
    hint; the RPC that reads the finished job relays it here, so the typed
    hint reaches the desktop on that read.
    """

    collector = _collector()
    if collector is not None:
        _merge_into(collector, hint)


def start_collecting() -> OfferCollector:
    """Collect for the rest of this context (one CLI process)."""

    collector = OfferCollector()
    _COLLECTOR.set(collector)
    return collector


def current_hint() -> dict[str, Any] | None:
    collector = _COLLECTOR.get()
    return collector.hint() if collector is not None else None


def note_unavailable(task: str, profile: str, *, signed_out: bool = False) -> None:
    collector = _collector()
    if collector is not None:
        collector.unavailable[task] = profile
        collector.signed_out = collector.signed_out or signed_out


def note_plan_route(task: str, profile: str) -> None:
    collector = _collector()
    if collector is not None:
        collector.plan_routes[task] = profile


def note_plan_failure(*, signed_out: bool = False) -> None:
    """A plan request failed for availability; called by the plan client."""

    collector = _collector()
    if collector is not None:
        collector.plan_failed = True
        collector.signed_out = collector.signed_out or signed_out


# ---------------------------------------------------------------------------
# The learner's choice
# ---------------------------------------------------------------------------

_GRANTS: set[str] = set()
_GRANTS_LOCK = threading.Lock()


def grant(tasks: Iterable[str]) -> list[str]:
    """Use OpenRouter for ``tasks`` while the plan is unavailable, for this process (the session)."""

    chosen = sorted({str(task) for task in tasks if str(task).strip()})
    with _GRANTS_LOCK:
        _GRANTS.update(chosen)
    return chosen


def revoke_all() -> None:
    with _GRANTS_LOCK:
        _GRANTS.clear()


def granted_tasks() -> list[str]:
    with _GRANTS_LOCK:
        return sorted(_GRANTS)


def is_granted(task: str) -> bool:
    if _QUIET.get():
        return False
    if (os.environ.get(FALLBACK_ENV) or "").strip().lower() == FALLBACK_KIND:
        return True
    with _GRANTS_LOCK:
        return task in _GRANTS


__all__ = [
    "FALLBACK_ENV",
    "FALLBACK_KIND",
    "OfferCollector",
    "collecting",
    "current_hint",
    "grant",
    "granted_tasks",
    "is_granted",
    "note_plan_failure",
    "note_plan_route",
    "note_unavailable",
    "offer_profile",
    "offer_sentence",
    "quiet",
    "relay_hint",
    "revoke_all",
    "start_collecting",
]
