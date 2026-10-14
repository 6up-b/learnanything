"""Router R2b/R2c: the models behind the mixture, asked off the hot path.

docs/specs/plan_router_r2_v1.md §3.4 (timing), §8.4 (spend), owner decisions
2026-10-13. The sidecar answers one RPC at a time, so a model is never waited
on inside a read: a decision's requests run in background threads, keyed by
the decision's **boundary key** (a hash of the plan, the state the chooser
saw, the options, the newest attempt and the router's settings), and the
decision is made by the first call that finds them answered, or by a step
that must serve (Begin, Continue, Next), which waits up to
``router.timeout_seconds`` (8 s) and then lets the rule take the share of any
model still out (G7, ``fallback`` recorded).

* **The budget.** The models have ``router.prefetch_timeout_seconds`` (45 s)
  from the moment a decision is first prefetched (Today's open, the feedback
  after a block's last answer). After it, an unanswered model is a timeout.
* **Readiness** (:meth:`RouteModels.readiness`): a route whose provider is not
  set up (no key, no Codex checkout, a chat profile on the Decider's route)
  is ``not_ready`` and never asked. The Decider's endpoint is confirmed once
  per process by OpenRouter's free model listing (no key, no learner text,
  nothing billed) before its first paid call; an unlisted endpoint is
  ``unreachable`` for an hour. The Decider never falls back to a chat model
  (``ai.routing.DECIDER_TASKS``): its failure moves its weight to the rule.
* **Spend** (:class:`RouterSpend`): ``router.max_daily_cost_usd`` ($5, owner
  2026-10-13) bounds metered spend per UTC day. Every router model call runs
  in :meth:`RouterSpend.metered`, which admits EACH physical request (the
  Decider's, the LLM's and its transport retries and JSON repair, the
  prefetch's query embedding, a teach-back summary's) through the shared
  request gate (``ai.execution.gate_model_requests``), and reserves it in its
  own start receipt: the day's router receipts and this request's estimate
  are checked against the cap and the receipt (carrying the estimate) is
  written in ONE write transaction, before anything is sent, as the reader's
  quick check does (plan §8.4; Codex review F3, F4). A receipt that reported
  no usage (still running, its finish lost to a crash, or a failure) counts
  its reservation, never zero (Codex review F5). A refusal is a fallback
  (``spend``). Subscription routes (Codex on the ChatGPT plan) are never
  capped; their tokens are estimated on the receipt. The provider key's own
  credit limit is the backstop.
* **The router LLM's output room** is the shared output-budget policy for
  ``router_llm`` and never below 16,384 tokens (owner 2026-10-13); a truncated
  answer is retried once at double the room, admitted like the first.
* **Receipts**: every request is a ``model_call`` owned by ``router_decision``
  (``router_teach_back_summary`` for R2c's summaries), labelled with its judge,
  question-set version and the card's hash.

``LEARNLOOP_ROUTER_MODELS=off`` makes every route ``not_ready`` (the rule
chooses, no model is asked): an offline run, and the test suite's default.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
import contextvars
from dataclasses import dataclass, field
from decimal import Decimal
import json
import logging
import math
import os
import threading
import time
from typing import Any

from learnloop.ai.spend import SpendLimitExceeded
from learnloop.daily_plan.types import DecisionPending
from learnloop.router import requests as rq

LOG = logging.getLogger(__name__)

DECIDER = "decider"
LLM = "llm"
COMPONENT_ROUTES = {DECIDER: "router_decider", LLM: "router_llm"}
RECEIPT_OWNER = "router_decision"
SUMMARY_RECEIPT_OWNER = "router_teach_back_summary"
#: Every receipt the router's daily guard counts.
GUARDED_OWNERS = (RECEIPT_OWNER, SUMMARY_RECEIPT_OWNER)
#: Owner 2026-10-13: the router LLM's output room is never below this.
LLM_OUTPUT_FLOOR = 16_384
#: ``LEARNLOOP_ROUTER_MODELS=off``: no router model is asked.
MODELS_ENV = "LEARNLOOP_ROUTER_MODELS"
PROBE_TTL_SECONDS = 3600.0
READINESS_TTL_SECONDS = 30.0
#: The query embedding's own bound inside the prefetch (R2c).
EMBEDDING_TIMEOUT_SECONDS = 15.0
#: Component statuses.
ANSWERED = "answered"
TIMEOUT = "timeout"
FAILED = "failed"
INVALID = "invalid"
SPEND = "spend"
NOT_READY = "not_ready"
UNREACHABLE = "unreachable"


def models_disabled() -> bool:
    return os.environ.get(MODELS_ENV, "").strip().lower() in {"off", "0", "false", "no"}


# -- results -------------------------------------------------------------------------


@dataclass
class ComponentResult:
    """One model's answer to one decision (or why there is none)."""

    name: str
    status: str
    parsed: rq.ParsedChoice | None = None
    p_yes: float | None = None
    rationale: str | None = None
    model: str | None = None
    provider: str | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    subscription: bool = False
    error: str | None = None
    request_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "model": self.model,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "subscription": self.subscription,
            **({"error": self.error} if self.error else {}),
        }


@dataclass
class Prefetch:
    """One decision's model requests, from its first prefetch to its answers."""

    key: str
    kind: str
    started: float
    deadline: float
    #: what the chooser built once (the card, the options, the request builder)
    material: dict[str, Any]
    components: dict[str, ComponentResult] = field(default_factory=dict)
    events: dict[str, threading.Event] = field(default_factory=dict)
    #: R2c: the similar decisions shown (or withheld) and the context vector
    similar: dict[str, Any] = field(default_factory=dict)
    request: Any = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    #: components whose call has started (a job that fails before them fails them)
    started_components: set[str] = field(default_factory=set)

    def answered(self, name: str) -> bool:
        event = self.events.get(name)
        return event is None or event.is_set()

    @property
    def complete(self) -> bool:
        return all(event.is_set() for event in self.events.values())

    def remaining(self, now: float) -> float:
        return max(self.deadline - now, 0.0)

    def wait(self, timeout: float) -> None:
        end = time.monotonic() + max(timeout, 0.0)
        for event in list(self.events.values()):
            left = end - time.monotonic()
            if left <= 0:
                break
            event.wait(left)

    def results(self) -> dict[str, ComponentResult]:
        """Every component's result; one still out is a timeout (its late answer is ignored)."""

        out: dict[str, ComponentResult] = {}
        with self.lock:
            for name, event in self.events.items():
                result = self.components.get(name)
                if event.is_set() and result is not None:
                    out[name] = result
                else:
                    out[name] = ComponentResult(name=name, status=TIMEOUT, error="no answer within the budget")
            for name, result in self.components.items():
                out.setdefault(name, result)
        return out




# -- the routes ------------------------------------------------------------------------


class RouteModels:
    """The production model source: the vault's ``router_decider`` / ``router_llm`` routes."""

    def __init__(self, *, probe_http: Any = None) -> None:
        self._probe_http = probe_http
        self._lock = threading.Lock()
        self._readiness: dict[Any, tuple[float, dict[str, str | None]]] = {}
        self._probe: dict[str, tuple[float, bool, str]] = {}

    def readiness(self, vault: Any) -> dict[str, str | None]:
        """``{component: None (ready) | reason}``; cached for a few seconds per vault."""

        if models_disabled():
            return {DECIDER: "disabled", LLM: "disabled"}
        cache_key = (str(vault.root), id(vault.config))
        now = time.monotonic()
        with self._lock:
            cached = self._readiness.get(cache_key)
            if cached is not None and now - cached[0] < READINESS_TTL_SECONDS:
                return dict(cached[1])
        from learnloop.ai.routing import provider_for_task, runtime_for_provider

        out: dict[str, str | None] = {}
        for name, task in COMPONENT_ROUTES.items():
            try:
                selection = provider_for_task(vault.config, task)  # type: ignore[arg-type]
                if not selection.provider_name:
                    out[name] = "unset"
                    continue
                report = runtime_for_provider(vault.root, vault.config, selection.provider_name, task=task)  # type: ignore[arg-type]
                out[name] = None if report.ready else (report.status or "unavailable")
            except Exception as exc:  # noqa: BLE001 - an unreadable route is not ready
                out[name] = type(exc).__name__
        with self._lock:
            self._readiness[cache_key] = (now, dict(out))
        return out

    def client(self, vault: Any, name: str, *, timeout_seconds: float) -> Any:
        from learnloop.ai.routing import ready_client_for_task

        resolved = ready_client_for_task(
            vault.root, vault.config, COMPONENT_ROUTES[name],  # type: ignore[arg-type]
            timeout_seconds=max(1, int(math.ceil(timeout_seconds))),
        )
        if not resolved.ready or resolved.client is None:
            raise _NotReady(resolved.runtime.status or "unavailable")
        return resolved.client

    def decider_reachable(self, client: Any) -> tuple[bool, str]:
        """Once per process (an hour's cache): the Decider's free endpoint listing."""

        profile = getattr(client, "profile", None)
        if profile is None:
            return True, "no profile to probe"
        key = str(getattr(client, "provider_name", "decider"))
        now = time.monotonic()
        with self._lock:
            cached = self._probe.get(key)
            if cached is not None and now - cached[0] < PROBE_TTL_SECONDS:
                return cached[1], cached[2]
        from learnloop.ai.providers.decider import probe_decider_endpoint

        try:
            report = probe_decider_endpoint(profile, http=self._probe_http)
            reachable = report.get("reachable") is not False
            message = str(report.get("message") or "")
        except Exception as exc:  # noqa: BLE001 - a probe that cannot run does not block the paid call
            reachable, message = True, f"probe unavailable ({type(exc).__name__})"
        with self._lock:
            self._probe[key] = (now, reachable, message)
        return reachable, message

    def embedding_client(self, vault: Any) -> Any | None:
        if models_disabled() or not bool(getattr(vault.config.embedding, "enabled", False)):
            return None
        from learnloop.ai.routing import ready_client_for_task

        resolved = ready_client_for_task(vault.root, vault.config, "embedding")
        return resolved.client if resolved.ready else None


class _NotReady(Exception):
    pass


# -- spend -------------------------------------------------------------------------------

#: ``budget_json`` key of a metered router request's start receipt: the dollars
#: its admission reserved (Codex review F5). Counted while the receipt reports
#: no usage, so a request whose finish never landed is never free.
RESERVATION_KEY = "router_reserved_usd"
#: Characters per token for a request's input estimate (the house ~4, on bytes).
_BYTES_PER_TOKEN = 4


def _day_start(now_iso: str) -> str:
    return now_iso[:10] + "T00:00:00"


def _price_per_million(config: Any, provider: str | None) -> float:
    pause = config.ingest.cost_pause
    return float(pause.prices.get(provider or "", pause.default_price_per_million_tokens))


def _reserved_usd(budget_json: Any) -> float | None:
    try:
        declared = json.loads(budget_json) if isinstance(budget_json, str) and budget_json else {}
    except ValueError:
        return None
    value = declared.get(RESERVATION_KEY) if isinstance(declared, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return None
    return max(float(value), 0.0)


def receipt_usd(config: Any, row: Mapping[str, Any]) -> float:
    """What one router receipt counts against the daily guard: the provider's
    cost, else its reported tokens at the route's price; nothing for a
    subscription call. A receipt that reported no usage (the request is still
    running, its finish was lost, or it failed) counts the reservation its
    admission recorded (Codex review F5): unknown usage is never free. An
    operation's own receipt around its requests (no reservation) counts 0."""

    from learnloop.ai.spend import is_subscription_transport

    usage = str(row.get("usage_json") or "")
    profile = config.ai.providers.get(row.get("provider") or "")
    if "estimated_only" in usage or (profile is not None and is_subscription_transport(profile=profile)):
        return 0.0
    if row.get("cost") is not None:
        return float(row["cost"])
    if row.get("input_tokens") is not None or row.get("output_tokens") is not None:
        tokens = int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)
        return tokens * _price_per_million(config, row.get("provider")) / 1_000_000
    return _reserved_usd(row.get("budget_json")) or 0.0


def request_estimate_usd(config: Any, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> float:
    """One physical request's reservation: its input (~4 bytes a token) plus
    its output room, at the route's price. The Decider prices its input only
    (its output tokens are free); an embedding has no output."""

    if prompt is None:
        text = ""
    elif isinstance(prompt, str):
        text = prompt
    else:
        text = json.dumps(prompt, ensure_ascii=False, default=str)
    input_tokens = (len(text.encode("utf-8")) + _BYTES_PER_TOKEN - 1) // _BYTES_PER_TOKEN
    estimated_cost = getattr(client, "estimated_cost", None)
    if callable(estimated_cost):
        return max(float(estimated_cost(input_tokens)), 0.0)
    output = 0 if purpose == "embedding" else (int(budget) if budget is not None else LLM_OUTPUT_FLOOR)
    return (input_tokens + max(output, 0)) * _price_per_million(config, getattr(client, "provider_name", None)) / 1_000_000


class SpendRefused(SpendLimitExceeded):
    """The router's daily guard refused a request before it was sent."""


class _RouterGate:
    """The router's request gate (``ai.execution.RequestGate``): consulted
    immediately before EACH physical request; it prices the request and hands
    the estimate to the start-receipt observer on the same thread, which
    admits and reserves it (:meth:`RouterSpend.metered`)."""

    def __init__(self, config: Any) -> None:
        self._config = config
        self._pending = threading.local()

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> float | None:
        from learnloop.ai.spend import is_subscription_transport

        self._pending.usd = None
        if is_subscription_transport(client=client):
            return None
        usd = request_estimate_usd(self._config, client, purpose=purpose, prompt=prompt, budget=budget)
        self._pending.usd = usd
        return usd

    def take(self) -> float | None:
        usd = getattr(self._pending, "usd", None)
        self._pending.usd = None
        return usd

    def settle(self, admission: Any, usage: Mapping[str, Any]) -> None:
        # A request whose start receipt was never written (refused, or the
        # write failed) leaves nothing pending for the next one.
        self._pending.usd = None


class RouterSpend:
    """The router's daily guard on metered spend (thread- and process-safe)."""

    def spent_today(self, repository: Any, config: Any, now_iso: str) -> float:
        rows = [
            row for row in repository.model_call_spend_rows(started_since=_day_start(now_iso))
            if row.get("owner_kind") in GUARDED_OWNERS
        ]
        return sum(receipt_usd(config, row) for row in rows)

    @contextmanager
    def metered(self, repository: Any, config: Any, *, owner_kind: str, owner_id: str) -> Iterator[None]:
        """Record every model call in this context under ``owner_kind`` /
        ``owner_id`` and admit each metered physical request against
        ``router.max_daily_cost_usd``.

        The admission and the reservation are one write transaction in the
        request's start receipt (BEGIN IMMEDIATE): the day's guarded receipts
        plus this request's estimate must fit the cap, and the receipt that
        records the estimate (``budget_json.router_reserved_usd``) is written
        before the request is sent, or :class:`SpendRefused` is raised and
        nothing is sent. Threads started in a copy of this context share it.
        Subscription requests are recorded, never refused."""

        from learnloop.ai.execution import gate_model_requests, observe_model_calls

        gate = _RouterGate(config)
        cap = Decimal(str(float(config.router.max_daily_cost_usd)))

        def observe(action: str, event: dict[str, Any]) -> None:
            usd = gate.take() if action == "start" else None
            if usd is None:
                repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)
                return
            try:
                declared = json.loads(event.get("budget_json") or "{}") or {}
            except ValueError:
                declared = {}
            declared[RESERVATION_KEY] = round(float(usd), 10)
            event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
            now_iso = str(event.get("started_at") or _now_iso())
            with repository.atomic():
                spent = Decimal(str(self.spent_today(repository, config, now_iso)))
                amount = Decimal(str(float(usd)))
                if spent + amount > cap:
                    raise SpendRefused(
                        f"router daily guard: ${float(spent + amount):.4f} would pass ${float(cap):.2f}"
                    )
                repository.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)

        with observe_model_calls(observe), gate_model_requests(gate):
            yield


# -- the runtime ---------------------------------------------------------------------------


@dataclass
class RouterRuntime:
    """Process-wide router state: the prefetch cache, the model source, the spend guard.

    ``inline`` runs every job on the calling thread (tests, scripted runs);
    otherwise each decision's models run in daemon threads. ``seed`` replaces
    :func:`learnloop.router.mixture.seed_for` (tests pin a draw)."""

    models: Any = field(default_factory=RouteModels)
    inline: bool = False
    seed: Callable[[str, str], str] | None = None
    max_entries: int = 64
    spend: RouterSpend = field(default_factory=RouterSpend)
    clock: Callable[[], float] = time.monotonic

    def __post_init__(self) -> None:
        self._entries: OrderedDict[str, Prefetch] = OrderedDict()
        self._lock = threading.Lock()

    def seed_for(self, key: str, decision_id: str) -> str:
        from learnloop.router.mixture import seed_for

        return self.seed(key, decision_id) if self.seed is not None else seed_for(key, decision_id)

    def lookup(self, scope: str, key: str) -> Prefetch | None:
        with self._lock:
            entry = self._entries.get(f"{scope}:{key}")
            if entry is not None:
                self._entries.move_to_end(f"{scope}:{key}")
            return entry

    def forget(self, scope: str, key: str) -> None:
        with self._lock:
            self._entries.pop(f"{scope}:{key}", None)

    def start(self, scope: str, key: str, *, kind: str, budget: float, material: dict[str, Any],
              job: Callable[[Prefetch], None], components: tuple[str, ...]) -> Prefetch:
        """Register a decision's requests and start them (once per key)."""

        with self._lock:
            existing = self._entries.get(f"{scope}:{key}")
            if existing is not None:
                return existing
            now = self.clock()
            entry = Prefetch(key=key, kind=kind, started=now, deadline=now + float(budget), material=material)
            for name in components:
                entry.events[name] = threading.Event()
            self._entries[f"{scope}:{key}"] = entry
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
        if self.inline:
            _run_job(job, entry)
        else:
            context = contextvars.copy_context()
            thread = threading.Thread(
                target=context.run, args=(_run_job, job, entry), name=f"learnloop-router-{key[:8]}", daemon=True,
            )
            thread.start()
        return entry

    def readiness(self, vault: Any) -> dict[str, str | None]:
        return self.models.readiness(vault)


def _run_job(job: Callable[[Prefetch], None], entry: Prefetch) -> None:
    try:
        job(entry)
    except Exception:  # noqa: BLE001 - a job never takes the plan down; its components fail
        LOG.warning("router: a decision's model job failed", exc_info=True)
    finally:
        # A component whose call never started (the job failed before it)
        # fails; one still running keeps its event unset (a timeout at decision).
        with entry.lock:
            for name, event in entry.events.items():
                if name not in entry.components and name not in entry.started_components:
                    entry.components[name] = ComponentResult(name=name, status=FAILED, error="job_failed")
                    event.set()


_DEFAULT: RouterRuntime | None = None
_DEFAULT_LOCK = threading.Lock()


def default_runtime() -> RouterRuntime:
    """The process's runtime (the sidecar's), created on first use."""

    global _DEFAULT
    with _DEFAULT_LOCK:
        if _DEFAULT is None:
            _DEFAULT = RouterRuntime()
        return _DEFAULT


# -- the model calls -------------------------------------------------------------------------


def _now_iso() -> str:
    from learnloop.clock import utc_now_iso

    return utc_now_iso()


def _finish(entry: Prefetch, result: ComponentResult) -> None:
    with entry.lock:
        entry.components[result.name] = result
        event = entry.events.get(result.name)
    if event is not None:
        event.set()


def _ms(started: float) -> int:
    return int(round((time.monotonic() - started) * 1000))


def call_decider(
    runtime: RouterRuntime, vault: Any, repository: Any, request: Any, *, card_hash: str | None, budget: float,
    purpose: str = rq.PURPOSE,
) -> tuple[ComponentResult, Any]:
    """Ask the Decider one decision's typed questions. Returns the result and the
    raw :class:`~learnloop.ai.decisions.DecisionResult` (None on failure)."""

    from learnloop.ai.decisions import request_body
    from learnloop.ai.execution import call_labels

    started = time.monotonic()
    result = ComponentResult(name=DECIDER, status=FAILED)
    questions = request.decider_questions()
    try:
        client = runtime.models.client(vault, DECIDER, timeout_seconds=budget)
    except _NotReady as exc:
        result.status, result.error = NOT_READY, str(exc)
        return result, None
    except Exception as exc:  # noqa: BLE001
        result.status, result.error = NOT_READY, type(exc).__name__
        return result, None
    result.model = getattr(client, "model", None)
    result.provider = getattr(client, "provider_name", None)
    body = request_body(str(result.model or "decider"), request.state, questions)
    result.request_payload = {"json": body, "text": None, "format_version": request.question_set_version}
    probe = getattr(runtime.models, "decider_reachable", None)
    if callable(probe):
        reachable, message = probe(client)
        if not reachable:
            result.status, result.error = UNREACHABLE, message[:200]
            return result, None
    estimate_cost = getattr(client, "estimated_cost", None)
    usd = 0.0
    if callable(estimate_cost):
        from learnloop.ai.providers.decider import estimate_input_tokens

        usd = float(estimate_cost(estimate_input_tokens(body)))
    try:
        # The request is admitted by the router's daily guard in its start
        # receipt (RouterSpend.metered, around the job): a refusal sends nothing.
        with call_labels(judge="decider", question_set_version=request.question_set_version, state_hash=card_hash):
            if _accepts_timeout(client.decide):
                decided = client.decide(request.state, questions, purpose=purpose, timeout_seconds=budget)
            else:
                decided = client.decide(request.state, questions, purpose=purpose)
    except SpendRefused as exc:
        result.status, result.error = SPEND, str(exc)
        result.latency_ms = _ms(started)
        return result, None
    except Exception as exc:  # noqa: BLE001 - every failure is a fallback (G7)
        result.status = INVALID if type(exc).__name__ == "DecisionResponseInvalid" else (
            TIMEOUT if isinstance(exc, TimeoutError) else FAILED
        )
        result.error = f"{type(exc).__name__}: {str(exc)[:200]}"
        result.latency_ms = _ms(started)
        return result, None
    result.latency_ms = _ms(started)
    result.cost_usd = float(decided.cost) if decided.cost is not None else usd
    result.model = decided.model or result.model
    result.response_payload = {"json": dict(decided.raw), "text": None, "format_version": request.question_set_version}
    result.status = ANSWERED
    return result, decided


def _llm_budget(vault: Any, client: Any) -> int:
    from learnloop.ai.output_budget import output_budget

    return max(LLM_OUTPUT_FLOOR, int(output_budget(vault.config, "router_llm", provider=getattr(client, "provider_name", None))))


def call_llm(
    runtime: RouterRuntime, vault: Any, repository: Any, request: Any, *, card_hash: str | None, budget: float,
    purpose: str = rq.PURPOSE,
) -> tuple[ComponentResult, Any]:
    """Ask the router LLM one decision's structured question. Returns the result
    and the raw answer object (None on failure)."""

    from learnloop.ai.errors import AIOutputTruncated
    from learnloop.ai.execution import call_labels, generation_limit, requested_reasoning_effort
    from learnloop.ai.output_budget import TruncationRetry, output_ceiling, reasoning_effort
    from learnloop.ai.spend import is_subscription_transport
    from learnloop.ai.transport import execute_structured_operation

    started = time.monotonic()
    result = ComponentResult(name=LLM, status=FAILED)
    try:
        client = runtime.models.client(vault, LLM, timeout_seconds=budget)
    except _NotReady as exc:
        result.status, result.error = NOT_READY, str(exc)
        return result, None
    except Exception as exc:  # noqa: BLE001
        result.status, result.error = NOT_READY, type(exc).__name__
        return result, None
    result.model = getattr(client, "model", None)
    result.provider = getattr(client, "provider_name", None)
    result.subscription = bool(is_subscription_transport(client=client))
    prompt = request.llm_prompt()
    model_type = rq.llm_result_model(request.llm_schema_version)
    result.request_payload = {"json": None, "text": prompt, "format_version": request.llm_schema_version}
    retry = TruncationRetry(
        _llm_budget(vault, client), role="router_llm", provider=result.provider, model=result.model,
        owner_kind=RECEIPT_OWNER, ceiling=output_ceiling(client),
    )
    answer = None
    total_usd = 0.0
    while True:
        deadline_left = budget - (time.monotonic() - started)
        if deadline_left <= 0:
            result.status, result.error = TIMEOUT, "no time left in the budget"
            result.latency_ms = _ms(started)
            return result, None
        # The row's cost is this attempt's estimate (the guard itself counts
        # the receipts); every physical request inside the operation, a
        # transport retry or a JSON repair included, is admitted on its own by
        # the router's daily guard (RouterSpend.metered; Codex review F4).
        usd = 0.0 if result.subscription else request_estimate_usd(
            vault.config, client, purpose=purpose, prompt=prompt, budget=retry.budget
        )
        try:
            with call_labels(judge="llm", question_set_version=request.llm_schema_version, state_hash=card_hash), \
                    retry.receipts(), generation_limit(retry.budget), \
                    requested_reasoning_effort(reasoning_effort(vault.config, "router_llm")):
                answer = execute_structured_operation(
                    client, purpose=purpose, prompt=prompt, result_model=model_type,  # type: ignore[arg-type]
                    timeout_seconds=deadline_left, isolated=bool(_supports_isolation(client)),
                )
            total_usd += usd
            break
        except SpendRefused as exc:
            result.status, result.error = SPEND, str(exc)
            result.latency_ms = _ms(started)
            return result, None
        except AIOutputTruncated:
            total_usd += usd
            if not retry.after_truncation():
                result.status, result.error = FAILED, "output truncated twice"
                result.latency_ms = _ms(started)
                return result, None
            continue
        except Exception as exc:  # noqa: BLE001 - every failure is a fallback (G7)
            result.status = TIMEOUT if isinstance(exc, TimeoutError) or "Timeout" in type(exc).__name__ else FAILED
            result.error = f"{type(exc).__name__}: {str(exc)[:200]}"
            result.latency_ms = _ms(started)
            return result, None
    result.latency_ms = _ms(started)
    result.cost_usd = None if result.subscription else total_usd
    dumped = answer.model_dump() if hasattr(answer, "model_dump") else answer
    result.response_payload = {"json": dumped, "text": None, "format_version": request.llm_schema_version}
    result.status = ANSWERED
    return result, answer


def _accepts_timeout(method: Any) -> bool:
    import inspect

    try:
        return "timeout_seconds" in inspect.signature(method).parameters
    except (TypeError, ValueError):
        return False


def _supports_isolation(client: Any) -> bool:
    from learnloop.ai.transport import ISOLATED_TURN

    supports = getattr(client, "supports", None)
    return bool(callable(supports) and supports(ISOLATED_TURN))


__all__ = [
    "ANSWERED",
    "ComponentResult",
    "DECIDER",
    "DecisionPending",
    "FAILED",
    "GUARDED_OWNERS",
    "INVALID",
    "LLM",
    "LLM_OUTPUT_FLOOR",
    "MODELS_ENV",
    "NOT_READY",
    "Prefetch",
    "RECEIPT_OWNER",
    "RouteModels",
    "RouterRuntime",
    "RESERVATION_KEY",
    "RouterSpend",
    "SPEND",
    "SUMMARY_RECEIPT_OWNER",
    "SpendRefused",
    "TIMEOUT",
    "UNREACHABLE",
    "call_decider",
    "call_llm",
    "default_runtime",
    "models_disabled",
    "receipt_usd",
    "request_estimate_usd",
]
