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
* An offer is made only when OpenRouter could actually do the work
  (:func:`offer_blocker`, review F2): a feature that refuses a metered route
  until its price is set (``hints.price_per_million`` and the like), or that
  needs a capability OpenRouter lacks (a snapshot diagnosis's workspace),
  says why instead of offering.
* Only a **grant** routes a task to OpenRouter: the desktop's "Use OpenRouter
  instead" (RPC ``ai_use_fallback``) grants the tasks of the feature that
  asked, validated against what this vault was offered, for this sidecar
  session and this vault only (a vault switch clears them; review F4);
  ``LEARNLOOP_AI_FALLBACK=openrouter`` grants every task for one CLI command,
  read by the CLI's entry point alone (:func:`command_grant`) and held in
  that command's context, so a long-lived host (the sidecar, the phone or MCP
  host) or a background thread in a fresh context never sees it. A granted
  request is an ordinary metered request on that profile, so every feature's
  existing spend caps apply to it.

Nothing here sends anything; it is bookkeeping between routing and the
adapters.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import os
from pathlib import Path
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


#: The price a feature needs before it sends anything on a metered route
#: (unset: refused before sending). OpenRouter is offered for these tasks only
#: once the setting is set, so a grant is never a promise the feature refuses.
METERED_PRICE_SETTINGS: dict[str, str] = {
    "hint_writer": "hints.price_per_million",
    "hint_outcome": "hints.price_per_million",
    "approach_map": "hints.price_per_million",
    "workbench_check": "workbench.price_per_million",
    "figure_author": "figures.price_per_million",
    "ad_forecast_llm": "adaptive_difficulty.price_per_million",
    "ad_feature_audit": "adaptive_difficulty.price_per_million",
    "library_organizer": "source_retrieval.llm_price_per_million",
    "passage_cue_judge": "source_retrieval.llm_price_per_million",
    "role_labeller": "source_retrieval.llm_price_per_million",
    "reading_path_judge": "source_retrieval.llm_price_per_million",
    "source_query_rewrite": "source_retrieval.llm_price_per_million",
    "source_rerank": "source_retrieval.llm_price_per_million",
    "practice_rerank": "practice_index.rerank_price_per_million",
    "source_solution_match": "source_service.llm_price_per_million",
    "source_compare": "source_service.llm_price_per_million",
    "exercise_discrimination": "source_service.llm_price_per_million",
    "worked_example_equivalence": "source_service.llm_price_per_million",
}


#: Set inside :func:`priced_by`: the price settings of the feature resolving a route.
_FEATURE_PRICES: ContextVar[tuple[str, ...]] = ContextVar("learnloop_plan_fallback_feature_prices", default=())


@contextmanager
def priced_by(*settings: str) -> Iterator[None]:
    """Resolve routes in this block for a feature held to its own price (re-review F2).

    Some features share another feature's task but refuse an unpriced
    metered route by a setting of their own: the Reader's paid passage
    checks (``reader_inquiry.metered_price_per_million``) and exercise
    imports (``source_service.llm_price_per_million``) ride
    ``canonical_ingest``. While such a setting is unset, the route makes no
    offer and honours no grant of that task (a grant from the question
    build is the build's); the unavailable message names the setting.
    """

    token = _FEATURE_PRICES.set((*_FEATURE_PRICES.get(), *settings))
    try:
        yield
    finally:
        _FEATURE_PRICES.reset(token)


def _setting(config: LearnLoopConfig, dotted: str) -> Any:
    value: Any = config
    for part in dotted.split("."):
        value = getattr(value, part)
    return value


def offer_blocker(config: LearnLoopConfig, task: str) -> str | None:
    """Why OpenRouter could not do ``task`` if the learner chose it, or ``None`` (review F2).

    The offer is then not made (no "Use OpenRouter instead" that the feature
    would refuse anyway); the unavailable message says what to set instead.
    """

    # The task's own price, then the price of the feature resolving it
    # (:func:`priced_by`, re-review F2): a passage check rides
    # ``canonical_ingest`` but is held to ``reader_inquiry.metered_price_per_million``.
    settings = [METERED_PRICE_SETTINGS.get(task), *_FEATURE_PRICES.get()]
    for setting in dict.fromkeys(entry for entry in settings if entry):
        if _setting(config, setting) is None:
            return (f"OpenRouter could do this once {setting} is set (the price it is held to); "
                    "until then nothing is offered or sent.")
    if task == "diagnosis" and config.diagnosis.history_mode == "snapshot":
        return ("OpenRouter can't do a snapshot diagnosis (diagnosis.history_mode = \"snapshot\" reads a "
                "workspace only the ChatGPT plan serves), so it isn't offered.")
    return None


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
#: Set inside ``quiet(honour_grants=True)``: a status read that makes no offer.
_NO_OFFERS: ContextVar[bool] = ContextVar("learnloop_plan_fallback_no_offers", default=False)


@contextmanager
def quiet(*, honour_grants: bool = False) -> Iterator[None]:
    """Make no offer, and (by default) honour no grant, for routes resolved in this block.

    For readiness probes (the snapshot's health line, startup maintenance):
    they report the plan's state themselves, and the learner is asked about
    OpenRouter only when a feature they used could not run. A grant is for
    the feature the learner used, never for background work: a deferred
    regrade backlog found at startup waits for the plan even while
    "grading" is granted for the session.

    ``honour_grants``: a status read that shows what a feature would use
    (the AI connection sheet, read on every vault load: re-review F1) makes
    no offer but reports a granted route as the one that serves; it sends
    nothing itself.
    """

    token = (_NO_OFFERS if honour_grants else _QUIET).set(True)
    try:
        yield
    finally:
        (_NO_OFFERS if honour_grants else _QUIET).reset(token)


def _collector() -> OfferCollector | None:
    return None if offers_suppressed() else _COLLECTOR.get()


def offers_suppressed() -> bool:
    """True inside :func:`quiet` (either kind): routes resolved here make no offer.

    The unavailable message then says nothing about "Use OpenRouter
    instead" either (fix round L2): no banner shows beside a status read.
    """

    return _QUIET.get() or _NO_OFFERS.get()


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


def relay_job_offer(job: Any) -> None:
    """Relay a finished job's offer on the first read that finds it, then forget it (review F8).

    A later read of the same failed job (a poll, the learner reopening the
    view after "Not now") brings no banner back; a new attempt makes its own
    offer.
    """

    hint = getattr(job, "fallback_offer", None)
    if hint:
        job.fallback_offer = None
        relay_hint(hint)


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

#: Per vault (its resolved root): the tasks the learner granted, and the
#: tasks a request on that vault was offered (a grant must name only those).
_GRANTS: dict[str, set[str]] = {}
_OFFERED: dict[str, set[str]] = {}
_GRANTS_LOCK = threading.Lock()
#: Set by :func:`command_grant` for one CLI command's context only.
_COMMAND_GRANT: ContextVar[bool] = ContextVar("learnloop_plan_fallback_command_grant", default=False)


def _vault_key(vault_root: Any) -> str:
    return str(Path(vault_root).resolve())


@contextmanager
def command_grant(*, host: bool = False) -> Iterator[bool]:
    """The CLI's ``LEARNLOOP_AI_FALLBACK=openrouter``: every task, for this command only.

    Read here, by the CLI's entry point, and nowhere else (review F4): the
    sidecar and the phone and MCP hosts never call this, so the variable in
    the shell that started them grants nothing, and a background thread
    started in a fresh context does not inherit it. ``host``: the command
    starts a long-lived host (`learnloop mcp serve`), which grants nothing.
    """

    chosen = not host and (os.environ.get(FALLBACK_ENV) or "").strip().lower() == FALLBACK_KIND
    token = _COMMAND_GRANT.set(chosen)
    try:
        yield chosen
    finally:
        _COMMAND_GRANT.reset(token)


def remember_offer(vault_root: Any, hint: dict[str, Any] | None) -> None:
    """Record what a request on ``vault_root`` was offered (the sidecar, as it sends the hint)."""

    tasks = [str(task) for task in (hint or {}).get("fallback_tasks") or [] if str(task).strip()]
    if vault_root is None or not tasks:
        return
    with _GRANTS_LOCK:
        _OFFERED.setdefault(_vault_key(vault_root), set()).update(tasks)


def offered_tasks(vault_root: Any) -> list[str]:
    with _GRANTS_LOCK:
        return sorted(_OFFERED.get(_vault_key(vault_root), set()))


def grant(vault_root: Any, tasks: Iterable[str]) -> list[str]:
    """Use OpenRouter for ``tasks`` on this vault while the plan is unavailable, for this session.

    Only tasks this vault was offered are granted (the caller reports the
    rest); returns the tasks granted by this call.
    """

    key = _vault_key(vault_root)
    with _GRANTS_LOCK:
        offered = _OFFERED.get(key, set())
        chosen = sorted({str(task) for task in tasks if str(task) in offered})
        _GRANTS.setdefault(key, set()).update(chosen)
    return chosen


def revoke(vault_root: Any | None = None) -> None:
    """Stop using OpenRouter: for one vault, or (``None``) for every vault, offers included."""

    with _GRANTS_LOCK:
        if vault_root is None:
            _GRANTS.clear()
            _OFFERED.clear()
        else:
            _GRANTS.pop(_vault_key(vault_root), None)


def revoke_all() -> None:
    revoke(None)


def granted_tasks(vault_root: Any) -> list[str]:
    with _GRANTS_LOCK:
        return sorted(_GRANTS.get(_vault_key(vault_root), set()))


def is_granted(task: str, vault_root: Any) -> bool:
    if _QUIET.get():
        return False
    if _COMMAND_GRANT.get():
        return True
    with _GRANTS_LOCK:
        return task in _GRANTS.get(_vault_key(vault_root), set())


__all__ = [
    "FALLBACK_ENV",
    "FALLBACK_KIND",
    "METERED_PRICE_SETTINGS",
    "OfferCollector",
    "collecting",
    "command_grant",
    "current_hint",
    "grant",
    "granted_tasks",
    "is_granted",
    "note_plan_failure",
    "note_plan_route",
    "note_unavailable",
    "offer_blocker",
    "offer_profile",
    "offer_sentence",
    "offered_tasks",
    "offers_suppressed",
    "priced_by",
    "quiet",
    "relay_hint",
    "relay_job_offer",
    "remember_offer",
    "revoke",
    "revoke_all",
    "start_collecting",
]
