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
#: Set by :func:`interactive`: the thread serving one learner request (the
#: sidecar's RPC dispatch, the CLI command). Holds that thread's ident, so a
#: copied context run on another thread (a worker started with
#: ``copy_context()``) is not interactive either.
_INTERACTIVE: ContextVar[int | None] = ContextVar("learnloop_plan_fallback_interactive", default=None)
#: Set by :func:`job_grant`: running a job's work on this thread, with the
#: grant it carries (``None``: none), and the thread it was entered on. Inside a
#: job no learner request and no press counts, only the job's own token.
_JOB_GRANT: ContextVar[tuple["GrantToken | None", int] | None] = ContextVar("learnloop_plan_fallback_job_grant",
                                                                            default=None)
#: Set by :func:`pressed`: the learner pressed a feature in this request, with
#: the token captured for it (narrowed to the feature's tasks) and the thread.
_PRESSED: ContextVar[tuple["GrantToken | None", int] | None] = ContextVar("learnloop_plan_fallback_pressed",
                                                                          default=None)
#: Per batch id: the token an ingest batch the learner pressed carries (process memory only: after a
#: restart a batch runs without one, on the plan).
_BATCH_GRANTS: dict[str, "GrantToken"] = {}

#: The tasks each pressed feature's queued work may use a grant for (T1 landing
#: review round 2: a token names the feature's own tasks, never every task
#: granted on the vault). A feature's offer names its own tasks, so its grant is
#: within this set.
FEATURE_TASKS: dict[str, frozenset[str]] = {
    # Add source / Create study map / Append / Quick add / import / inventory /
    # extraction repair / build retry: the question build (review F3).
    "build": frozenset({"canonical_ingest", "canonical_ingest_retry", "authoring"}),
    # The Reader's paid passage, selection and inquiry checks.
    "reader_check": frozenset({"canonical_ingest", "authoring"}),
    # Exercise imports (Reader, textbook, workbench, the primed retry) and their key checks.
    "exercise_import": frozenset({"canonical_ingest", "authoring", "source_solution_match",
                                  "exercise_discrimination", "worked_example_equivalence"}),
    "rung_variant": frozenset({"rung_variant"}),
    "animation": frozenset({"animation"}),
    "question_promotion": frozenset({"tutor_qa", "authoring"}),
    # Goal population, starter and commissioning practice.
    "practice": frozenset({"canonical_ingest", "authoring"}),
    # Hints and the workbench (check, help, the worked example, compare).
    "hints": frozenset({"hint_writer", "hint_outcome", "approach_map", "workbench_check", "source_query_rewrite",
                        "source_rerank", "source_relevance_judge", "source_query_writer"}),
    # The library ask / notes / compare / tutor, figures, exercise search.
    "library": frozenset({"library_organizer", "tutor_qa", "source_compare", "source_query_rewrite",
                          "source_rerank", "source_relevance_judge", "source_query_writer", "figure_author",
                          "exercise_discrimination"}),
    "reading_path": frozenset({"reading_path_judge"}),
}


def _vault_key(vault_root: Any) -> str:
    return str(Path(vault_root).resolve())


@dataclass(frozen=True)
class GrantToken:
    """A learner's grant captured when they started a job (:func:`capture_grant`).

    It names the vault and the tasks granted at that moment (or, for a CLI
    command's ``LEARNLOOP_AI_FALLBACK``, every task). At use, a session task
    must still be granted, so "Stop using OpenRouter" ends it for the job's
    next route.
    """

    vault_key: str
    tasks: frozenset[str]
    #: The CLI's ``LEARNLOOP_AI_FALLBACK``: these tasks without a session grant.
    command: bool = False
    #: The CLI command's own press: every task, any vault (``vault_key == "*"``).
    every: bool = False

    def covers(self, task: str, key: str) -> bool:
        return self.vault_key in (key, "*") and (self.every or task in self.tasks)


def _here() -> int:
    return threading.get_ident()


@contextmanager
def interactive() -> Iterator[None]:
    """Serve one learner request on this thread: a grant counts only here (or under :func:`job_grant`).

    Set by the sidecar's RPC dispatch and the CLI's entry point (landing
    review of T1: a grant never serves background work, by construction).
    Every other thread, now and in the future, starts without it, and a
    context copied to another thread does not carry it (it is bound to this
    thread's ident).
    """

    token = _INTERACTIVE.set(_here())
    try:
        yield
    finally:
        _INTERACTIVE.reset(token)


def _in_job() -> bool:
    entry = _JOB_GRANT.get()
    return entry is not None and entry[1] == _here()


def is_interactive() -> bool:
    """On the thread serving a learner request, outside a probe and outside any job's work."""

    return _INTERACTIVE.get() == _here() and not _QUIET.get() and not _in_job()


def _job_token() -> "GrantToken | None":
    entry = _JOB_GRANT.get()
    if entry is None or entry[1] != _here():
        return None
    return entry[0]


def _narrowed(token: GrantToken | None, tasks: Iterable[str] | None, key: str) -> GrantToken | None:
    if token is None or token.vault_key not in (key, "*"):
        return None
    if tasks is None:
        return token
    kept = frozenset(tasks) if token.every else token.tasks & frozenset(tasks)
    return GrantToken(key, kept, command=token.command) if kept else None


def _capture_now(key: str, tasks: frozenset[str]) -> GrantToken | None:
    if _COMMAND_GRANT.get():
        return GrantToken(key, tasks, command=True)
    with _GRANTS_LOCK:
        kept = frozenset(_GRANTS.get(key, set())) & tasks
    return GrantToken(key, kept) if kept else None


@contextmanager
def pressed(vault_root: Any, feature: str) -> Iterator[GrantToken | None]:
    """The learner pressed ``feature`` in this request: queued work may carry their grant.

    Entered by the sidecar's dispatch for the RPCs a learner press sends
    (``learnloop_sidecar.pressed.PRESSED_RPCS``) and nowhere else (T1 landing
    review round 2: scrolling, polling, Today and status reads are not a
    press). The token is captured now, narrowed to ``FEATURE_TASKS[feature]``;
    ``None`` outside a learner request, inside a probe or a job, or when none
    of the feature's tasks is granted.
    """

    token = None
    if vault_root is not None and is_interactive():
        token = _capture_now(_vault_key(vault_root), FEATURE_TASKS[feature])
    entry = _PRESSED.set((token, _here()))
    try:
        yield token
    finally:
        _PRESSED.reset(entry)


def is_pressed() -> bool:
    """Inside a learner's press on this thread (whether or not anything is granted), outside any job."""

    entry = _PRESSED.get()
    return entry is not None and entry[1] == _here() and not _in_job() and not _QUIET.get()


def pressed_token(vault_root: Any = None) -> GrantToken | None:
    """The token of the press around this call, on its own thread, outside any job's work."""

    entry = _PRESSED.get()
    if entry is None or entry[1] != _here() or entry[0] is None or _in_job() or _QUIET.get():
        return None
    if vault_root is not None and entry[0].vault_key not in (_vault_key(vault_root), "*"):
        return None
    return entry[0]


def capture_grant(vault_root: Any, tasks: Iterable[str] | None = None) -> GrantToken | None:
    """The grant a job started now may carry: the press around it, or the job it runs in.

    ``None`` outside a press and outside a job carrying a token (a request
    that is not a press, a background thread), inside a readiness probe, or
    when none of ``tasks`` is granted. ``tasks`` narrows further (a job keeps
    only its own). The caller keeps it with the job and runs the job under
    :func:`job_grant`; nothing is inherited implicitly.
    """

    if _QUIET.get() or vault_root is None:
        return None
    key = _vault_key(vault_root)
    if _in_job():
        return _narrowed(_job_token(), tasks, key)
    return _narrowed(pressed_token(vault_root), tasks, key)


@contextmanager
def job_grant(token: GrantToken | None) -> Iterator[None]:
    """Run a job's work on this thread under the grant it carries (``None``: none).

    Always entered by a job's runner, token or not: inside it neither the
    learner request nor a press around it counts (a job drained in the
    request's own thread is still a job), only this token.
    """

    entry = _JOB_GRANT.set((token, _here()))
    try:
        yield
    finally:
        _JOB_GRANT.reset(entry)


def remember_batch_grant(batch_id: str, token: GrantToken | None) -> None:
    """Keep ``token`` with ``batch_id``; ``None`` drops any token the batch had."""

    with _GRANTS_LOCK:
        if token is None:
            _BATCH_GRANTS.pop(batch_id, None)
        else:
            _BATCH_GRANTS[batch_id] = token


def batch_grant(batch_id: str | None) -> GrantToken | None:
    with _GRANTS_LOCK:
        return _BATCH_GRANTS.get(batch_id or "")


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
        if host:
            yield chosen
        else:
            # The command is the learner's request, and with the variable set
            # its own press: the work it queues (and drains) carries the grant.
            press = _PRESSED.set((GrantToken("*", frozenset(), command=True, every=True), _here())
                                 if chosen else None)
            try:
                with interactive():
                    yield chosen
            finally:
                _PRESSED.reset(press)
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
            _BATCH_GRANTS.clear()
        else:
            key = _vault_key(vault_root)
            _GRANTS.pop(key, None)
            # Its batches' tokens too: a later grant never revives a queued one (round 2, Low 1).
            for batch_id in [batch for batch, token in _BATCH_GRANTS.items() if token.vault_key == key]:
                del _BATCH_GRANTS[batch_id]


def revoke_all() -> None:
    revoke(None)


def granted_tasks(vault_root: Any) -> list[str]:
    with _GRANTS_LOCK:
        return sorted(_GRANTS.get(_vault_key(vault_root), set()))


def is_granted(task: str, vault_root: Any) -> bool:
    """Whether OpenRouter may serve ``task`` here: a learner request or a job carrying the learner's grant.

    Never inside a readiness probe (:func:`quiet`), never on a thread that is
    neither (a background thread, a worker given a copied context): a grant
    serves only what the learner asked for (landing review of T1).
    """

    if _QUIET.get():
        return False
    key = _vault_key(vault_root)
    if _in_job():
        token = _job_token()
        if token is None or not token.covers(task, key):
            return False
        if token.command:
            return True
        with _GRANTS_LOCK:
            return task in _GRANTS.get(key, set())
    if not is_interactive():
        return False
    if _COMMAND_GRANT.get():
        return True
    with _GRANTS_LOCK:
        return task in _GRANTS.get(key, set())


__all__ = [
    "FALLBACK_ENV",
    "FALLBACK_KIND",
    "METERED_PRICE_SETTINGS",
    "OfferCollector",
    "collecting",
    "FEATURE_TASKS",
    "GrantToken",
    "batch_grant",
    "capture_grant",
    "command_grant",
    "interactive",
    "is_interactive",
    "job_grant",
    "is_pressed",
    "pressed",
    "pressed_token",
    "remember_batch_grant",
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
