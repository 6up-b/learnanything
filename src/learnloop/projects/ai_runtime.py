"""Routes, spend admission and receipts for project model calls (spec §4, §7).

- **Routes.** Authoring and the closed-book check use ``ai.routing.project``
  (default: the grading route, then the active provider); probe grading uses
  ``ai.routing.grading`` at ``project.grading_reasoning_effort`` (default
  ``high``, spec §5.2's one high-effort pass).
- **Isolation.** Every call promises a scope in its receipt (``diff``,
  ``questions_only``, ``quoted_evidence``), and the project store beside the
  vault holds the reference answers. Clients are built around an *empty
  temporary working directory* instead of the vault root, but a directory
  only sets where an agentic transport starts: Codex can still read absolute
  paths. So with ``project.require_tool_isolation`` (the default) Codex runs
  in the bubblewrap sandbox of ``learnloop.ai.isolation`` (no home, vault or
  repo visible), chat transports are tool-free by construction, and any other
  transport is refused before a request is sent. Receipts record which.
- **Spend** (Slice A plan §5 rule 6). Every logical call is admitted against
  the command's call and candidate caps. Metered routes (OpenRouter, OpenAI
  keys) are also admitted against token and dollar caps; an unknown price
  fails closed unless the owner passes ``--price-per-million``; a hidden
  provider retry is admitted only as a retry against ``max_retries``, and the
  request carries the admitted output budget as its generation limit. The
  Codex subscription (``codex_sdk``) has no physical-request bound and no
  token/dollar cap: its cost is estimated from reported token usage at a
  reference rate and labelled ``estimated_only``.
- **Receipts.** Every model event is written to the project store's
  ``call_receipts`` with the disclosure record of what was sent.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Iterable, Iterator
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import declared_budgets, generation_limit, observe_model_calls
from learnloop.ai.isolation import ToolIsolation, isolation_mode, tool_isolation
from learnloop.ai.routing import ready_client_for_task
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import LearnLoopConfig
from learnloop.projects.experiment_store import ProjectStore

SUBSCRIPTION_PROVIDER_TYPES = frozenset({"codex_sdk"})
# Reference rate for the *estimate* of subscription usage (USD per million
# tokens, input and output alike). Nothing is billed per token on the
# subscription; the figure only makes usage comparable across routes.
SUBSCRIPTION_REFERENCE_USD_PER_MILLION = 10.0
_UNBOUNDED_COUNT = 10**12
_UNBOUNDED_USD = 1e12

ROLE_TASK = {"authoring": "project", "closed_book": "project", "grading": "grading"}


@dataclass(frozen=True)
class ProjectRoute:
    role: str
    task: str
    provider_name: str
    provider_type: str | None
    model: str | None
    subscription: bool
    ready: bool
    message: str | None
    client: Any = None
    reasoning_effort: str | None = None
    # "tool_free" (a chat completion), "bubblewrap" (an agentic transport in
    # the sandbox) or "none" (project.require_tool_isolation = false).
    tool_isolation: str | None = None
    isolation: ToolIsolation | None = None

    def describe(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "task": self.task,
            "provider": self.provider_name,
            "provider_type": self.provider_type,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "subscription": self.subscription,
            "ready": self.ready,
            "message": self.message,
            "tool_isolation": self.tool_isolation,
        }


def _provider_type(config: LearnLoopConfig, provider_name: str) -> str | None:
    profile = config.ai.providers.get(provider_name)
    return None if profile is None else profile.type.strip().lower()


def _config_for_workdir(config: LearnLoopConfig, vault_root: Path) -> LearnLoopConfig:
    """Pin relative Codex checkout paths to the vault before moving the cwd."""

    copy = config.model_copy(deep=True)
    for profile in copy.ai.providers.values():
        checkout = getattr(profile, "checkout_path", None)
        if isinstance(checkout, str) and checkout.strip() and not Path(checkout).expanduser().is_absolute():
            profile.checkout_path = str((Path(vault_root) / checkout).resolve())
    return copy


def config_for_role(config: LearnLoopConfig, role: str) -> LearnLoopConfig:
    """The configuration a role's client is built from.

    Spec §5.2 asks for one *high-effort* grading pass, but the shared grading
    route defaults to a low-effort profile. For the grading role (closed-book
    judgments and answer grades) ``project.grading_reasoning_effort`` replaces
    the routed profile's effort whenever that profile takes one (every Codex
    profile; chat profiles that declare an effort). An empty value keeps the
    route's own effort. Other roles, and every other feature, are untouched.
    """

    effort = (config.project.grading_reasoning_effort or "").strip()
    if role != "grading" or not effort:
        return config
    from learnloop.ai.routing import provider_for_task

    name = provider_for_task(config, ROLE_TASK[role]).provider_name  # type: ignore[arg-type]
    profile = config.ai.providers.get(name)
    if profile is None:
        return config
    takes_effort = _provider_type(config, name) in SUBSCRIPTION_PROVIDER_TYPES or bool(
        (getattr(profile, "reasoning_effort", None) or "").strip()
    )
    if not takes_effort or getattr(profile, "reasoning_effort", None) == effort:
        return config
    copy = config.model_copy(deep=True)
    copy.ai.providers[name].reasoning_effort = effort
    return copy


def describe_routes(config: LearnLoopConfig) -> dict[str, dict[str, Any]]:
    """Which provider each role would use, without building any client."""

    from learnloop.ai.routing import provider_for_task

    routes: dict[str, dict[str, Any]] = {}
    for role, task in ROLE_TASK.items():
        effective = config_for_role(config, role)
        name = provider_for_task(effective, task).provider_name  # type: ignore[arg-type]
        provider_type = _provider_type(effective, name)
        profile = effective.ai.providers.get(name)
        routes[role] = {
            "task": task,
            "provider": name or "manual",
            "provider_type": provider_type,
            "model": getattr(profile, "model", None),
            "reasoning_effort": getattr(profile, "reasoning_effort", None),
            "subscription": provider_type in SUBSCRIPTION_PROVIDER_TYPES,
        }
    return routes


ClientResolver = Callable[[Path, LearnLoopConfig, str], ProjectRoute]


def resolve_route(workdir: Path, config: LearnLoopConfig, role: str) -> ProjectRoute:
    task = ROLE_TASK[role]
    resolved = ready_client_for_task(workdir, config, task)  # type: ignore[arg-type]
    provider_type = _provider_type(config, resolved.provider_name)
    profile = config.ai.providers.get(resolved.provider_name)
    return ProjectRoute(
        role=role,
        task=task,
        provider_name=resolved.provider_name,
        provider_type=provider_type,
        model=getattr(resolved.client, "model", None) or resolved.runtime.model,
        subscription=provider_type in SUBSCRIPTION_PROVIDER_TYPES,
        ready=resolved.ready,
        message=resolved.runtime.message,
        client=resolved.client,
        reasoning_effort=getattr(profile, "reasoning_effort", None),
    )


# Tests replace this with a resolver that returns fake transports.
_route_resolver: ClientResolver = resolve_route


def set_route_resolver(resolver: ClientResolver | None) -> None:
    global _route_resolver
    _route_resolver = resolver or resolve_route


ISOLATION_KILL_SWITCH_HINT = "set project.require_tool_isolation = false to run it unconfined"


def _with_isolation(route: ProjectRoute, isolation: ToolIsolation, *, required: bool) -> ProjectRoute:
    """Attach the isolation a route's calls run under, or mark the route not ready."""

    if route.client is None:
        return route
    mode, reason = isolation_mode(route.client)
    if not required:
        return replace(route, tool_isolation="tool_free" if mode == "tool_free" else "none")
    if mode is None:
        if not route.ready:
            return route
        return replace(route, ready=False, message=f"{reason}; {ISOLATION_KILL_SWITCH_HINT}")
    return replace(route, tool_isolation=mode, isolation=isolation if mode == "bubblewrap" else None)


@contextmanager
def project_routes(
    vault_root: Path,
    config: LearnLoopConfig,
    roles: tuple[str, ...],
    *,
    hidden: Iterable[Path] = (),
) -> Iterator[dict[str, ProjectRoute]]:
    """Resolve the requested roles around an empty working directory.

    With ``project.require_tool_isolation`` (the default) every call runs
    either on a tool-free chat transport or, for an agentic transport, in the
    bubblewrap sandbox of ``learnloop.ai.isolation``: the empty directory is
    all of the filesystem it can see besides system files, and ``hidden``
    (the vault, the enrolled repos) is masked even inside those. A transport
    that can be neither is not ready.
    """

    with tempfile.TemporaryDirectory(prefix="learnloop-project-") as workdir:
        pinned = _config_for_workdir(config, vault_root)
        isolation = ToolIsolation(workdir=Path(workdir), hidden=(Path(vault_root), *(Path(path) for path in hidden)))
        required = config.project.require_tool_isolation
        yield {
            role: _with_isolation(
                _route_resolver(Path(workdir), config_for_role(pinned, role), role), isolation, required=required
            )
            for role in roles
        }


@dataclass(frozen=True)
class PlannedCall:
    role: str
    input_tokens: int
    output_tokens: int
    candidates: int = 0


def _physical_start(event: dict[str, Any]) -> bool:
    purpose = str(event.get("purpose") or "")
    return purpose == "chat_request" or purpose.endswith(":sdk_turn")


class PaidCalls:
    """One command's admission, accounting and receipts for model calls."""

    def __init__(
        self,
        store: ProjectStore,
        *,
        caps: SpendCaps,
        run_id: str,
        price_per_million: float | None = None,
        cancelled: Callable[[], bool] | None = None,
        require_tool_isolation: bool = True,
    ) -> None:
        self.store = store
        self.caps = caps
        self.run_id = run_id
        self.price_per_million = price_per_million
        self.require_tool_isolation = require_tool_isolation
        # Calls, candidates and retries bind every route; tokens and dollars
        # bind only metered routes (rule 6: no restraint on the subscription).
        self.counts = SpendBudget(
            replace(caps, max_total_tokens=_UNBOUNDED_COUNT, max_estimated_usd=_UNBOUNDED_USD),
            cancelled=cancelled,
        )
        self.metered = SpendBudget(
            replace(caps, max_candidates=_UNBOUNDED_COUNT, max_pairs=_UNBOUNDED_COUNT, max_calls=_UNBOUNDED_COUNT),
            cancelled=cancelled,
        )
        self.subscription_tokens = 0
        self.subscription_estimated_usd = 0.0
        self.calls = 0

    # --- estimates ------------------------------------------------------------

    def rate(self, route: ProjectRoute | dict[str, Any]) -> float | None:
        subscription = route.subscription if isinstance(route, ProjectRoute) else route["subscription"]
        if self.price_per_million is not None:
            return self.price_per_million
        return SUBSCRIPTION_REFERENCE_USD_PER_MILLION if subscription else None

    def usd(self, route: ProjectRoute | dict[str, Any], tokens: int) -> float | None:
        rate = self.rate(route)
        return None if rate is None else tokens * rate / 1_000_000

    def plan(self, planned: list[PlannedCall], routes: dict[str, Any]) -> dict[str, Any]:
        """Aggregate a dry-run estimate and check it against the caps.

        Raises ``SpendLimitExceeded`` when the plan cannot be admitted
        (including a metered route with an unknown price).
        """

        totals = {"calls": 0, "candidates": 0, "total_tokens": 0}
        metered_tokens, metered_usd, subscription_usd = 0, 0.0, 0.0
        unknown_price = False
        for call in planned:
            route = routes[call.role]
            tokens = call.input_tokens + call.output_tokens
            totals["calls"] += 1
            totals["candidates"] += call.candidates
            totals["total_tokens"] += tokens
            subscription = route.subscription if isinstance(route, ProjectRoute) else route["subscription"]
            usd = self.usd(route, tokens)
            if subscription:
                subscription_usd += usd or 0.0
            elif usd is None:
                unknown_price = True
                metered_tokens += tokens
            else:
                metered_tokens += tokens
                metered_usd += usd
        report = {
            **totals,
            "metered_tokens": metered_tokens,
            "metered_estimated_usd": None if unknown_price else round(metered_usd, 6),
            "subscription_estimated_usd": round(subscription_usd, 6),
            "subscription_cost_label": "estimated_only",
            "caps": self.caps.as_dict(),
        }
        self.counts.check(SpendEstimate(calls=totals["calls"], candidates=totals["candidates"], estimated_usd=0.0))
        self.metered.check(
            SpendEstimate(
                calls=0,
                total_tokens=metered_tokens,
                estimated_usd=None if unknown_price else metered_usd,
            )
        )
        return report

    # --- calls ----------------------------------------------------------------

    def call(
        self,
        route: ProjectRoute,
        *,
        purpose: str,
        prompt: str,
        result_model: type,
        output_tokens: int,
        candidates: int = 0,
        diff_id: str | None = None,
        disclosure: dict[str, Any] | None = None,
    ) -> Any:
        from learnloop.projects.capture import estimate_tokens

        mode, reason = isolation_mode(route.client)
        if self.require_tool_isolation and mode is None:
            # Refused before admission: nothing is spent or sent.
            raise AIProviderUnavailable(f"{reason}; {ISOLATION_KILL_SWITCH_HINT}")
        isolation_label = mode if (self.require_tool_isolation or mode == "tool_free") else "none"
        estimated_tokens = estimate_tokens(prompt) + output_tokens
        usd = self.usd(route, estimated_tokens)
        cost_label = "estimated_only" if route.subscription else (
            "owner_price_estimate" if self.price_per_million is not None else "provider_reported"
        )
        state: dict[str, Any] = {"physical": 0, "root": None, "usage": {}, "root_usage": {}}
        disclosure = {
            **(disclosure or {}), "route_role": route.role, "provider": route.provider_name,
            "reasoning_effort": route.reasoning_effort, "tool_isolation": isolation_label,
        }

        with ExitStack() as stack:
            count_charge = stack.enter_context(
                self.counts.request(SpendEstimate(calls=1, candidates=candidates, total_tokens=estimated_tokens, estimated_usd=0.0))
            )
            metered_charge = stack.enter_context(
                nullcontext() if route.subscription else
                self.metered.request(SpendEstimate(calls=1, total_tokens=estimated_tokens, estimated_usd=usd))
            )
            retries = stack.enter_context(ExitStack())
            stack.enter_context(
                declared_budgets({**self.caps.as_dict(), "subscription": route.subscription, "cost_label": cost_label})
            )
            if isolation_label == "bubblewrap":
                isolation = route.isolation
                if isolation is None:
                    isolation = ToolIsolation(
                        workdir=Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="learnloop-project-")))
                    )
                stack.enter_context(tool_isolation(isolation))
            if not route.subscription:
                # The admitted spend counts ``output_tokens``; the provider
                # request (and its JSON repair, which spends from the same
                # budget) must not be allowed to produce more.
                stack.enter_context(generation_limit(max(1, int(output_tokens))))

            def observe(action: str, event: dict[str, Any]) -> None:
                if action == "start":
                    if event.get("parent_call_id") is None and state["root"] is None:
                        state["root"] = event["id"]
                    if _physical_start(event):
                        state["physical"] += 1
                        if state["physical"] > 1 and not route.subscription:
                            # A hidden provider retry: admit it as a retry first.
                            retries.enter_context(self.counts.request(SpendEstimate(calls=1, retries=1, estimated_usd=0.0)))
                            retries.enter_context(self.metered.request(
                                SpendEstimate(calls=1, retries=1, total_tokens=estimated_tokens, estimated_usd=usd)
                            ))
                self.store.record_model_event(
                    action, event, owner_kind="project_command", owner_id=self.run_id,
                    diff_id=diff_id, disclosure=disclosure, cost_label=cost_label,
                )
                if action == "finish":
                    target = state["root_usage"] if event.get("id") == state["root"] else state["usage"]
                    for name in ("input_tokens", "output_tokens", "cost"):
                        if event.get(name) is not None:
                            target[name] = target.get(name, 0) + event[name]

            try:
                with observe_model_calls(observe):
                    result = execute_structured_operation(
                        route.client, purpose=purpose, prompt=prompt, result_model=result_model
                    )
            finally:
                usage = state["usage"] or state["root_usage"]
                tokens = int(usage.get("input_tokens", 0) + usage.get("output_tokens", 0)) or None
                reported_cost = usage.get("cost")
                actual_usd = reported_cost
                if actual_usd is None and tokens is not None:
                    actual_usd = self.usd(route, tokens)
                count_charge.reconcile(total_tokens=tokens)
                if metered_charge is not None:
                    metered_charge.reconcile(total_tokens=tokens, estimated_usd=actual_usd)
                self.calls += 1
                if route.subscription:
                    used = tokens if tokens is not None else estimated_tokens
                    self.subscription_tokens += used
                    self.subscription_estimated_usd += self.usd(route, used) or 0.0
                if state["root"] is not None:
                    self.store.set_receipt_estimate(
                        state["root"], actual_usd if actual_usd is not None else usd
                    )
        return result

    def summary(self) -> dict[str, Any]:
        metered = self.metered.used
        counts = self.counts.used
        return {
            "calls": self.calls,
            "admitted_calls": counts.calls,
            "retries": counts.retries,
            "candidates": counts.candidates,
            "metered_tokens": metered.total_tokens,
            "metered_estimated_usd": round(metered.estimated_usd or 0.0, 6),
            "subscription_tokens": self.subscription_tokens,
            "subscription_estimated_usd": round(self.subscription_estimated_usd, 6),
            "subscription_cost_label": "estimated_only",
            "caps": self.caps.as_dict(),
        }


def caps_from_options(
    *,
    max_candidates: int,
    max_calls: int,
    max_retries: int,
    max_tokens: int,
    max_cost_usd: float,
) -> SpendCaps:
    return SpendCaps(
        max_candidates=max_candidates,
        max_pairs=0,
        max_retries=max_retries,
        max_calls=max_calls,
        max_total_tokens=max_tokens,
        max_estimated_usd=max_cost_usd,
    )


__all__ = [
    "ISOLATION_KILL_SWITCH_HINT",
    "PaidCalls",
    "PlannedCall",
    "ProjectRoute",
    "ROLE_TASK",
    "SUBSCRIPTION_PROVIDER_TYPES",
    "SUBSCRIPTION_REFERENCE_USD_PER_MILLION",
    "caps_from_options",
    "config_for_role",
    "describe_routes",
    "project_routes",
    "resolve_route",
    "set_route_resolver",
]
