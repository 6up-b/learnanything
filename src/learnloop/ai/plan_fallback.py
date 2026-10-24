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
* Only a **grant** routes to OpenRouter, and the offer is the grant (landing
  redesign D, owner Q1-Q3): the desktop's "Use OpenRouter instead" (RPC
  ``ai_use_fallback {offerId}``) answers one offer, which grants the ACTION
  that asked (its RPC method) for this sidecar session and this vault only
  (a vault switch clears it), and the units of work the offer lists; see
  "The learner's choice" below. ``LEARNLOOP_AI_FALLBACK=openrouter`` grants one CLI command,
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
    "ad_relatedness": "adaptive_difficulty.price_per_million",
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
    #: The action this collector's offers belong to (a request's method, a unit's origin).
    origin: str | None = None
    #: An offer relayed from a job or batch keeps that unit's origin (never the poll's).
    relayed_origin: str | None = None
    #: Units created here, or named by a relayed offer: answering tokens the batches.
    units: list[tuple[str, str]] = field(default_factory=list)
    #: A unit's collector: the vault and epoch the unit was created in (round 5,
    #: Medium 1): its offer is minted for them, or not at all.
    vault_key: str | None = None
    epoch: tuple[int, int] | None = None
    #: An offer relayed into this request from a job or batch, and how to put it
    #: back when this request's own offer shows instead (it waits for the next read).
    relayed: tuple[dict[str, Any], Any] | None = None

    def hint(self) -> dict[str, Any] | None:
        """The typed hint for the adapter, or ``None`` when nothing was offered."""

        tasks = dict(self.unavailable)
        if self.plan_failed:
            for task, profile in self.plan_routes.items():
                tasks.setdefault(task, profile)
        if not tasks:
            return None
        hint: dict[str, Any] = {
            "fallback_available": FALLBACK_KIND,
            "fallback_profile": sorted(set(tasks.values()))[0],
            "fallback_tasks": sorted(tasks),
            "plan_signed_out": self.signed_out,
        }
        origin = self.relayed_origin or self.origin
        if origin:
            hint["fallback_origin"] = origin
        if self.units:
            hint["fallback_units"] = [list(unit) for unit in self.units]
        if self.vault_key is not None:
            hint["fallback_vault"] = self.vault_key
            hint["fallback_epoch"] = list(self.epoch or (0, 0))
        return hint


_COLLECTOR: ContextVar[OfferCollector | None] = ContextVar("learnloop_plan_fallback_offers", default=None)
#: Set inside :func:`quiet`: a readiness probe, not a feature the learner used.
_QUIET: ContextVar[bool] = ContextVar("learnloop_plan_fallback_quiet", default=False)
#: Set inside :func:`status_as`: a status read that makes no offer.
_NO_OFFERS: ContextVar[bool] = ContextVar("learnloop_plan_fallback_no_offers", default=False)


@contextmanager
def quiet() -> Iterator[None]:
    """Make no offer and honour no grant for routes resolved in this block; units made here have no origin.

    For readiness probes (the snapshot's health line, startup maintenance)
    and automatic work (keep-ahead on reading progress): they report the
    plan's state themselves, and the learner is asked about OpenRouter only
    when a feature they used could not run. A grant is never for background
    work: a deferred regrade backlog found at startup waits for the plan even
    while "grading" is granted for the session. A status read of what an
    action would use is :func:`status_as`.
    """

    token = _QUIET.set(True)
    try:
        yield
    finally:
        _QUIET.reset(token)


def _collector() -> OfferCollector | None:
    return None if offers_suppressed() else _COLLECTOR.get()


def offers_suppressed() -> bool:
    """True inside :func:`quiet` (either kind): routes resolved here make no offer.

    The unavailable message then says nothing about "Use OpenRouter
    instead" either (fix round L2): no banner shows beside a status read.
    """

    return _QUIET.get() or _NO_OFFERS.get()


@contextmanager
def collecting(origin: str | None = None, stamp: tuple[str, tuple[int, int]] | None = None) -> Iterator[OfferCollector]:
    """Collect the offers made while the block runs (one RPC, or one unit's work), as action ``origin``.

    A nested block also hands its offers to the enclosing collector when it
    ends, so neither loses them (a unit's runner clears the request's
    collector first: :func:`job_grant`).
    """

    parent = _COLLECTOR.get()
    collector = OfferCollector(origin=origin)
    if stamp is not None:
        collector.vault_key, collector.epoch = stamp
    token = _COLLECTOR.set(collector)
    try:
        yield collector
    finally:
        _COLLECTOR.reset(token)
        if parent is not None:
            hint = collector.hint()
            if collector.origin is not None and collector.origin != parent.origin:
                _relay_into(parent, hint)  # another action's unit, inline: it asks as itself
            else:
                _merge_into(parent, hint)


def _merge_into(collector: OfferCollector, hint: dict[str, Any] | None) -> None:
    if not hint:
        return
    profile = str(hint.get("fallback_profile") or FALLBACK_KIND)
    for task in hint.get("fallback_tasks") or []:
        collector.unavailable.setdefault(str(task), profile)
    collector.signed_out = collector.signed_out or bool(hint.get("plan_signed_out"))
    relayed = hint.get("fallback_origin")
    if relayed and relayed != collector.origin and collector.relayed_origin is None:
        collector.relayed_origin = str(relayed)
    for unit in hint.get("fallback_units") or []:
        collector.units.append((str(unit[0]), str(unit[1])))


def _relay_into(collector: OfferCollector, hint: dict[str, Any] | None, restore: Any = None) -> bool:
    if not hint or collector.relayed is not None:
        return False
    collector.relayed = (dict(hint), restore)
    return True


def relay_hint(hint: dict[str, Any] | None, restore: Any = None) -> bool:
    """Offer again, in the current request, what a unit (a job, a batch) offered.

    A job (a hint, a library ask, margin notes, a reading path) runs in its
    own thread with its own collector (:func:`collecting`) and keeps its
    hint; the RPC that reads the finished job relays it here, so the typed
    hint reaches the desktop on that read. It stays the unit's own offer: its
    action, units, vault and epoch (round 5); the dispatch mints it only for
    the vault and epoch it was made in. One relay per request; ``restore``
    puts it back when this request shows its own offer instead. False when
    nothing was relayed.
    """

    collector = _collector()
    if collector is None:
        return False
    return _relay_into(collector, hint, restore)


def relay_job_offer(job: Any) -> None:
    """Relay a finished job's offer on the first read that finds it, then forget it (review F8).

    A later read of the same failed job (a poll, the learner reopening the
    view after "Not now") brings no banner back; a new attempt makes its own
    offer.
    """

    hint = getattr(job, "fallback_offer", None)
    if hint and relay_hint(hint, restore=lambda: setattr(job, "fallback_offer", hint)):
        job.fallback_offer = None


def take_offer(collector: OfferCollector, current_vault: Any) -> tuple[dict[str, Any] | None, str | None]:
    """What one response may show: (the hint, its vault key), or (None, None).

    The request's own offer first (its vault is the session's), and a relayed
    one waits (restored for the next read). Otherwise the relayed offer, only
    when its unit's vault is the session's vault and its epoch is current
    (round 5, Medium 1): a relay from another vault or from before a stop
    shows nothing, and is dropped.
    """

    own = collector.hint()
    key = _vault_key(current_vault) if current_vault is not None else None
    if own is not None:
        if collector.relayed is not None and collector.relayed[1] is not None:
            collector.relayed[1]()
        return own, key
    if collector.relayed is None:
        return None, None
    hint = dict(collector.relayed[0])
    vault = hint.pop("fallback_vault", None)
    epoch = hint.pop("fallback_epoch", None)
    if key is None or (vault is not None and vault != key):
        return None, None
    with _GRANTS_LOCK:
        current = _epoch(key)
    if epoch is not None and tuple(epoch) != current:
        return None, None
    return hint, key


def start_collecting() -> OfferCollector:
    """Collect for the rest of this context (one CLI process)."""

    collector = OfferCollector()
    _COLLECTOR.set(collector)
    return collector


def current_hint() -> dict[str, Any] | None:
    """The hint of this context's collector (the CLI's JSON), without its unit list."""

    collector = _COLLECTOR.get()
    hint = collector.hint() if collector is not None else None
    if hint is not None:
        hint.pop("fallback_units", None)
    return hint


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
# The learner's choice (landing redesign D, owner Q1-Q3 2026-10-23: the offer is the grant)
# ---------------------------------------------------------------------------
#
# A grant names the ACTION THAT ASKED: the RPC method whose request raised the
# offer (for an offer relayed from a job or a batch, the method that started
# it). Never a task, never a feature table. It is honoured only in
#
# * a REQUEST of that method (``request``: the dispatch opens one per RPC), or
# * a WORK UNIT created in one (an ingest batch, a sidecar job, the import's
#   time-boxed check: each takes ``unit_token()`` when it is created), or named
#   by the answered offer (its ``units``),
#
# and only while the vault's EPOCH is the one the grant was given in: "Stop
# using OpenRouter" (``revoke``) bumps it, so no token captured earlier (a
# waiting worker, a queued batch) ever revives, even after a new yes. Q1: a
# granted action keeps using OpenRouter for the session, including when
# LearnLoop runs it by itself; never another action, never background work.
# Q2: each action asks once ("Not now" mutes it, in the desktop).

#: Per vault: the granted origins, and the tasks their offers named (display only).
_GRANTS: dict[str, dict[str, set[str]]] = {}
#: Per vault: its epoch (a stop bumps it); ``_GLOBAL`` is bumped by revoke_all.
_EPOCH: dict[str, int] = {}
_GLOBAL = {"epoch": 0}
_SEQ = {"n": 0}
#: Offers minted by the dispatch, by id.
_OFFERS: dict[str, "Offer"] = {}
#: Per batch id: its token, its origin (the action that created it) and the offer it keeps.
_BATCH_GRANTS: dict[str, "GrantToken"] = {}
_BATCH_ORIGIN: dict[str, str] = {}
_BATCH_OFFERS: dict[str, dict[str, Any]] = {}
_BATCH_STAMP: dict[str, tuple[str, tuple[int, int]]] = {}
_GRANTS_LOCK = threading.Lock()
#: Set by :func:`command_grant` for one CLI command's context only.
_COMMAND_GRANT: ContextVar[bool] = ContextVar("learnloop_plan_fallback_command_grant", default=False)
#: Set by :func:`request`: (origin, thread ident) of the request this thread serves.
_REQUEST: ContextVar[tuple[str, int] | None] = ContextVar("learnloop_plan_fallback_request", default=None)
#: Set by :func:`job_grant`: (origin, token, thread ident) of the work unit this thread runs.
_JOB: ContextVar[tuple[str | None, "GrantToken | None", int] | None] = ContextVar(
    "learnloop_plan_fallback_job", default=None)
#: Set by :func:`status_as`: (origin, thread ident): a status read of what that action would use.
_STATUS_AS: ContextVar[tuple[str, int] | None] = ContextVar("learnloop_plan_fallback_status_as", default=None)


def _vault_key(vault_root: Any) -> str:
    return str(Path(vault_root).resolve())


def _here() -> int:
    return threading.get_ident()


def _epoch(key: str) -> tuple[int, int]:
    return (_GLOBAL["epoch"], _EPOCH.get(key, 0))


def _next() -> int:
    _SEQ["n"] += 1
    return _SEQ["n"]


@dataclass(frozen=True)
class GrantToken:
    """A unit's grant: the action it belongs to, in the epoch it was given (:func:`unit_token`)."""

    vault_key: str
    origin: str
    epoch: tuple[int, int] = (0, 0)
    #: The CLI's ``LEARNLOOP_AI_FALLBACK``: the command's own grant, any vault, every task.
    command: bool = False

    def live(self, key: str) -> bool:
        if self.command:
            return True
        with _GRANTS_LOCK:
            return (self.vault_key == key and self.epoch == _epoch(key)
                    and self.origin in _GRANTS.get(key, {}))


@dataclass(frozen=True)
class Offer:
    """One "Use OpenRouter instead" the dispatch showed: answering it grants ``origin``."""

    id: str
    vault_key: str
    origin: str
    tasks: tuple[str, ...]
    units: tuple[tuple[str, str], ...]
    epoch: tuple[int, int]


def _request_origin() -> str | None:
    entry = _REQUEST.get()
    if entry is None or entry[1] != _here() or _in_job():
        return None
    return entry[0]


def _job_here() -> tuple[str | None, "GrantToken | None"] | None:
    entry = _JOB.get()
    if entry is None or entry[2] != _here():
        return None
    return entry[0], entry[1]


def _in_job() -> bool:
    return _job_here() is not None


@contextmanager
def request(vault_root: Any, origin: str) -> Iterator[None]:
    """Serve one request of action ``origin`` on this thread (the sidecar's dispatch, per RPC).

    Bound to this thread: a fresh thread, or a context copied to another
    thread, is not in it. ``vault_root`` is informational (grants are read
    per vault at use).
    """

    token = _REQUEST.set((origin, _here()))
    try:
        yield
    finally:
        _REQUEST.reset(token)


def unit_origin() -> str | None:
    """The action a unit of work created now belongs to: the request's, outside any job and any probe."""

    if _QUIET.get():
        return None
    return _request_origin()


def unit_token(vault_root: Any) -> GrantToken | None:
    """The token a unit created now carries (or the time-boxed check runs under).

    In a request of a granted action: that action's token, in the current
    epoch. In a job: the job's own token. ``None`` otherwise, under
    :func:`quiet`, or with no vault.
    """

    if _QUIET.get() or vault_root is None:
        return None
    key = _vault_key(vault_root)
    job = _job_here()
    if job is not None:
        token = job[1]
        return token if token is not None and (token.command or token.vault_key == key) else None
    origin = _request_origin()
    if origin is None:
        return None
    if _COMMAND_GRANT.get():
        return GrantToken("*", origin, command=True)
    with _GRANTS_LOCK:
        if origin not in _GRANTS.get(key, {}):
            return None
        return GrantToken(key, origin, _epoch(key))


def note_unit(kind: str, unit_id: str) -> None:
    """Record a unit created in this request, so its offer lists it (answering tokens it)."""

    collector = _COLLECTOR.get()
    if collector is not None and not offers_suppressed() and not _in_job():
        collector.units.append((kind, str(unit_id)))


@contextmanager
def job_grant(token: GrantToken | None, origin: str | None = None, *,
              keep_collector: bool = False) -> Iterator[None]:
    """Run a unit's work on this thread under its token (``None``: none), as action ``origin``.

    Always entered by a unit's runner. Inside it the request around it (a
    batch drained inline) does not count, and that request's collector is
    cleared: the unit opens its own (``collecting(origin=...)``) when it may
    ask. ``keep_collector``: the unit is part of the request that waits on it
    (the import's time-boxed check), so its offers stay that request's.
    """

    entry = _JOB.set((origin, token, _here()))
    collector = _COLLECTOR.set(_COLLECTOR.get() if keep_collector else None)
    try:
        yield
    finally:
        _COLLECTOR.reset(collector)
        _JOB.reset(entry)


def unit_stamp(vault_root: Any) -> tuple[str, tuple[int, int]] | None:
    """The vault and epoch a unit is created in (taken at its creation; round 5, Medium 1)."""

    if vault_root is None:
        return None
    key = _vault_key(vault_root)
    with _GRANTS_LOCK:
        return key, _epoch(key)


@contextmanager
def unit(token: GrantToken | None, origin: str | None,
         stamp: tuple[str, tuple[int, int]] | None) -> Iterator[OfferCollector]:
    """A unit's work (a sidecar job, a batch's job): :func:`job_grant`, and its own collector.

    A unit that belongs to no action (made under :func:`quiet` or off any
    request) asks nothing; one that does collects its offers as its action,
    stamped with the vault and epoch it was created in (``unit_stamp``), for
    the read that finds it to relay.
    """

    with job_grant(token, origin):
        if origin is None:
            with quiet(), collecting() as offers:
                yield offers
        else:
            with collecting(origin=origin, stamp=stamp) as offers:
                yield offers


@contextmanager
def status_as(origin: str) -> Iterator[None]:
    """A status read of what action ``origin`` would use: no offer, and its grant counts (in a request)."""

    token = _STATUS_AS.set((origin, _here()))
    quiet_token = _NO_OFFERS.set(True)
    try:
        yield
    finally:
        _NO_OFFERS.reset(quiet_token)
        _STATUS_AS.reset(token)


def remember_batch_grant(batch_id: str, token: GrantToken | None, origin: str | None = None,
                         vault_root: Any = None) -> None:
    """Keep a new batch's token, origin and creation stamp. Never replaces what a batch already has."""

    stamp = unit_stamp(vault_root)
    with _GRANTS_LOCK:
        if token is not None and batch_id not in _BATCH_GRANTS:
            _BATCH_GRANTS[batch_id] = token
        if origin is not None:
            _BATCH_ORIGIN.setdefault(batch_id, origin)
            if stamp is not None:
                _BATCH_STAMP.setdefault(batch_id, stamp)


def batch_grant(batch_id: str | None) -> GrantToken | None:
    with _GRANTS_LOCK:
        return _BATCH_GRANTS.get(batch_id or "")


def batch_origin(batch_id: str | None) -> str | None:
    with _GRANTS_LOCK:
        return _BATCH_ORIGIN.get(batch_id or "")


def keep_batch_offer(batch_id: str, hint: dict[str, Any] | None) -> None:
    """A batch's run met the unavailable plan: keep its offer for the next read that shows the batch."""

    if hint:
        with _GRANTS_LOCK:
            _BATCH_OFFERS[batch_id] = {**hint, "fallback_units": [["batch", batch_id]]}


def batch_stamp(batch_id: str, vault_root: Any) -> tuple[str, tuple[int, int]] | None:
    """The vault and epoch the batch was created in (in memory), else now (a batch from before a restart)."""

    with _GRANTS_LOCK:
        stamp = _BATCH_STAMP.get(batch_id)
    return stamp if stamp is not None else unit_stamp(vault_root)


def relay_batch_offer(batch_id: str | None) -> bool:
    """Relay (once) the offer a batch kept, on a read that shows that batch.

    Kept for the next read when this response shows another offer.
    """

    with _GRANTS_LOCK:
        hint = _BATCH_OFFERS.pop(batch_id or "", None)
    if not hint:
        return False

    def restore() -> None:
        with _GRANTS_LOCK:
            _BATCH_OFFERS.setdefault(str(batch_id), hint)

    if relay_hint(hint, restore=restore):
        return True
    restore()
    return False


def relay_batch_offers(batch_ids: Iterable[str | None]) -> None:
    """Relay the first pending offer among the batches a response shows (one offer per response)."""

    for batch_id in batch_ids:
        if batch_id and relay_batch_offer(str(batch_id)):
            return


@contextmanager
def command_grant(*, host: bool = False) -> Iterator[bool]:
    """The CLI's ``LEARNLOOP_AI_FALLBACK=openrouter``: the command's own grant, for this command only.

    Read here, by the CLI's entry point, and nowhere else (review F4): the
    sidecar and the phone and MCP hosts never call this, so the variable in
    the shell that started them grants nothing, and a background thread
    started in a fresh context does not inherit it. ``host``: the command
    starts a long-lived host (`learnloop mcp serve`), which grants nothing.
    The command is one request (``origin = "cli"``); the work it queues
    carries its grant.
    """

    chosen = not host and (os.environ.get(FALLBACK_ENV) or "").strip().lower() == FALLBACK_KIND
    token = _COMMAND_GRANT.set(chosen)
    try:
        if host:
            yield chosen
        else:
            entry = _REQUEST.set(("cli", _here()))
            try:
                yield chosen
            finally:
                _REQUEST.reset(entry)
    finally:
        _COMMAND_GRANT.reset(token)


def mint_offer(vault_root: Any, hint: dict[str, Any], origin: str,
               units: Iterable[tuple[str, str]] = ()) -> str | None:
    """Record the offer one response shows; its id is what "Use OpenRouter instead" answers."""

    if vault_root is None:
        return None
    key = _vault_key(vault_root)
    with _GRANTS_LOCK:
        offer = Offer(id=f"fo_{_next()}_{abs(hash((key, origin))) % 10**8}", vault_key=key, origin=origin,
                      tasks=tuple(sorted(str(task) for task in hint.get("fallback_tasks") or [])),
                      units=tuple((str(kind), str(unit)) for kind, unit in units), epoch=_epoch(key))
        _OFFERS[offer.id] = offer
    return offer.id


def answer_offer(vault_root: Any, offer_id: str | None) -> Offer | None:
    """The learner chose "Use OpenRouter instead" on offer ``offer_id``: grant its action, token its units.

    ``None`` for an unknown, foreign-vault or stale (pre-stop) offer.
    """

    key = _vault_key(vault_root)
    with _GRANTS_LOCK:
        offer = _OFFERS.get(str(offer_id or ""))
        if offer is None or offer.vault_key != key or offer.epoch != _epoch(key):
            return None
        _GRANTS.setdefault(key, {}).setdefault(offer.origin, set()).update(offer.tasks)
        for kind, unit in offer.units:
            if kind == "batch":
                _BATCH_GRANTS[unit] = GrantToken(key, offer.origin, offer.epoch)
                _BATCH_ORIGIN.setdefault(unit, offer.origin)
    return offer


def grant_origin(vault_root: Any, origin: str, tasks: Iterable[str] = ()) -> None:
    """Grant action ``origin`` on this vault for the session (``answer_offer``'s effect; tests use it)."""

    with _GRANTS_LOCK:
        _GRANTS.setdefault(_vault_key(vault_root), {}).setdefault(origin, set()).update(tasks)


def revoke(vault_root: Any | None = None) -> None:
    """Stop using OpenRouter: for one vault, or (``None``) for every vault.

    Bumps the epoch, so every token captured earlier is dead, even after a
    new yes; drops the vault's grants, offers and batch tokens.
    """

    with _GRANTS_LOCK:
        if vault_root is None:
            _GRANTS.clear()
            _OFFERS.clear()
            _BATCH_GRANTS.clear()
            _BATCH_OFFERS.clear()
            _GLOBAL["epoch"] += 1
            return
        key = _vault_key(vault_root)
        _GRANTS.pop(key, None)
        _EPOCH[key] = _EPOCH.get(key, 0) + 1
        for offer_id in [offer.id for offer in _OFFERS.values() if offer.vault_key == key]:
            del _OFFERS[offer_id]
        for batch_id in [batch for batch, token in _BATCH_GRANTS.items() if token.vault_key == key]:
            del _BATCH_GRANTS[batch_id]


def revoke_all() -> None:
    revoke(None)


def granted_origins(vault_root: Any) -> list[str]:
    with _GRANTS_LOCK:
        return sorted(_GRANTS.get(_vault_key(vault_root), {}))


def granted_tasks(vault_root: Any) -> list[str]:
    """The tasks the answered offers named (display: Settings' "Stop using OpenRouter")."""

    with _GRANTS_LOCK:
        return sorted({task for tasks in _GRANTS.get(_vault_key(vault_root), {}).values() for task in tasks})


def is_granted(task: str, vault_root: Any) -> bool:
    """Whether OpenRouter may serve ``task`` here (redesign D).

    Not under :func:`quiet`. In a unit's work: its token is live (its action
    still granted, in the epoch it was given). Otherwise in a request of a
    granted action (or a status read as one, in a request), or the CLI
    command's own grant. Nothing else counts, on any thread.
    """

    if _QUIET.get():
        return False
    key = _vault_key(vault_root)
    job = _job_here()
    if job is not None:
        token = job[1]
        return token is not None and token.live(key)
    origin = _request_origin()
    if origin is None:
        return False
    if _COMMAND_GRANT.get():
        return True
    status = _STATUS_AS.get()
    if status is not None and status[1] == _here():
        origin = status[0]
    with _GRANTS_LOCK:
        return origin in _GRANTS.get(key, {})


__all__ = [
    "FALLBACK_ENV",
    "FALLBACK_KIND",
    "METERED_PRICE_SETTINGS",
    "GrantToken",
    "Offer",
    "OfferCollector",
    "answer_offer",
    "batch_grant",
    "batch_origin",
    "collecting",
    "command_grant",
    "current_hint",
    "grant_origin",
    "granted_origins",
    "granted_tasks",
    "is_granted",
    "job_grant",
    "keep_batch_offer",
    "mint_offer",
    "note_plan_failure",
    "note_plan_route",
    "note_unavailable",
    "note_unit",
    "offer_blocker",
    "offer_profile",
    "offer_sentence",
    "offers_suppressed",
    "priced_by",
    "quiet",
    "batch_stamp",
    "relay_batch_offer",
    "relay_batch_offers",
    "take_offer",
    "unit_stamp",
    "relay_hint",
    "relay_job_offer",
    "remember_batch_grant",
    "request",
    "revoke",
    "revoke_all",
    "start_collecting",
    "status_as",
    "unit",
    "unit_origin",
    "unit_token",
]
