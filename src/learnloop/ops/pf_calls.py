"""Role-routed, spend-admitted, checkpointed model calls for PF-b (Slice A §5 rule 6).

Every paid PF role is its own route (Slice 2 §5.8). This module resolves each
role to pinned clients, admits each physical request against the command's
caps before it is sent, records receipts (``model_call_receipts`` with the caps
in ``budget_json``), and checkpoints every validated result in
``model_work_checkpoints`` under a content key of prompt, schema, settings and
output bound. A resumed run therefore never pays twice for finished work, and a
changed prompt version, model setting or input is a new key.

Billing: metered routes (OpenRouter, OpenAI keys) keep the full cap set, an
explicit owner price (unknown prices fail closed) and the one-physical-request
bound (``single_request``). Codex routes are billed to the owner's subscription:
no physical-request bound, token and dollar caps recorded but not enforced, cost
estimated from reported tokens and labelled ``estimated_only``. The call,
candidate, pair and retry caps are shared across both billing classes.

Isolation: every PF role runs as an isolated, tool-free turn
(``ISOLATED_TURN``). A chat completion is isolated by construction; a Codex
route starts its turn in an empty directory under LearnLoop's permission
profile with the shell and every connector off, so a solver can never read a
persisted candidate's answer and a closed-book model never sees the sources. A
route that cannot isolate is refused before any request, and the isolation
boundary is part of every checkpoint key: a result produced without it is never
reused.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
import json
from typing import Any

from pydantic import BaseModel

from learnloop.ai.errors import AIInterrupted, AIOutputTruncated, AIProviderUnavailable
from learnloop.ai.execution import (
    content_key,
    generation_limit,
    observe_model_calls,
    requested_reasoning_effort,
    single_request,
)
from learnloop.ai.output_budget import TruncationRetry, output_budget, output_ceiling, reasoning_effort
from learnloop.ai.routing import provider_for_task, provider_list_for_task, ready_client_for_task
from learnloop.ai.spend import (
    ESTIMATED_ONLY, SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded,
    is_subscription_transport, subscription_usage_estimate,
)
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, execute_structured_operation
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.vault.models import LoadedVault

METERED_TYPES = frozenset({"openai_chat", "openrouter"})
SCHEMA_ALLOWANCE = 512
CHECKPOINT_PREFIX = "pf:"
# Part of every checkpoint key: results from before the boundary are never reused.
ISOLATION_BOUNDARY = "isolated_tool_free_turn_v1"

# Roles -> the configured AI task route that serves them.
ROLE_TASKS: dict[str, str] = {
    "skeleton": "pf_generator",
    "program": "pf_generator",
    "single_shot": "pf_generator",
    "valid_alternative": "pf_generator",
    "source": "pf_generator",
    "closed_book": "pf_closed_book",
    # The independent check that a cited span supports a source-anchored key.
    "span_support": "pf_reference_verifier",
    "proposer": "pf_proposers",
    "panel": "pf_solver_panel",
    "equivalence": "pf_reference_verifier",
    "structure": "pf_isomorph_judge",
    "freshness": "pf_isomorph_judge",
    "selection": "pf_selection_judge",
    "pairwise": "pf_selection_judge",
    "grading": "grading",
}
LIST_ROLES = frozenset({"proposer", "panel"})
# Roles the scaling check moves between tiers (Slice 2 §5.6): the generators
# and the judges. The verifiers (solver panel, reference verifier, span
# support) stay fixed for comparability, and so does the parent skeleton:
# it is an input both tiers' generators must share.
TIERED_ROLES = frozenset({"program", "single_shot", "source", "proposer", "structure",
                          "freshness", "closed_book", "selection"})


@dataclass
class RoleClient:
    role: str
    provider: str
    model: str | None
    profile_type: str | None
    subscription: bool
    client: Any | None = None
    settings: dict[str, Any] = field(default_factory=dict)


class PFUnavailable(RuntimeError):
    """A route cannot serve its role (unready, unbounded metered transport)."""


def _profile_settings(vault: LoadedVault, provider: str, model: str | None) -> dict[str, Any]:
    profile = vault.config.ai.providers.get(provider)
    return {
        "provider": provider,
        "model": model or (profile.model if profile is not None else None),
        "profile": profile.model_dump(mode="json") if profile is not None else None,
    }


def role_providers(vault: LoadedVault, role: str, *, tier_routes: list[str] | None = None) -> list[str]:
    """The planned provider names for a role, before any client is built."""
    if tier_routes and role in TIERED_ROLES:
        return list(dict.fromkeys(tier_routes)) if role in LIST_ROLES else [tier_routes[0]]
    task = ROLE_TASKS[role]
    if role in LIST_ROLES:
        return [selection.provider_name for selection in provider_list_for_task(vault.config, task)]
    return [provider_for_task(vault.config, task).provider_name]


def planned_role_clients(vault: LoadedVault, role: str, *,
                         tier_routes: list[str] | None = None) -> list[RoleClient]:
    """Profile-level view used by dry runs: no client is constructed."""
    result = []
    for provider in role_providers(vault, role, tier_routes=tier_routes):
        profile = vault.config.ai.providers.get(provider)
        result.append(RoleClient(
            role=role, provider=provider, model=profile.model if profile is not None else None,
            profile_type=profile.type if profile is not None else None,
            subscription=is_subscription_transport(profile=profile),
            settings=_profile_settings(vault, provider, None),
        ))
    return result


def resolve_role_clients(vault: LoadedVault, role: str, *, injected: Any | None = None,
                         tier_routes: list[str] | None = None) -> list[RoleClient]:
    """Pinned, ready clients for a role; ``injected`` replaces them in tests."""
    if injected is not None:
        clients = injected if isinstance(injected, (list, tuple)) else [injected]
        return [RoleClient(
            role=role, provider=getattr(client, "provider_name", None) or "injected",
            model=getattr(client, "model", None), profile_type=getattr(client, "provider_type", None),
            subscription=is_subscription_transport(client=client), client=client,
            settings={"provider": getattr(client, "provider_name", None),
                      "model": getattr(client, "model", None)},
        ) for client in clients]
    result = []
    task = ROLE_TASKS[role]
    for provider in role_providers(vault, role, tier_routes=tier_routes):
        profile = vault.config.ai.providers.get(provider)
        subscription = is_subscription_transport(profile=profile)
        if profile is None or not (profile.type in METERED_TYPES or subscription):
            raise PFUnavailable(
                f"PF role {role!r} needs an openai_chat/openrouter profile (bounded physical "
                f"requests) or a Codex profile (subscription, estimated cost); {provider!r} "
                f"is not one. Set ai.routing.{task}."
            )
        # Pin the planned route: an availability fallback must never silently
        # change the dry-run's model, checkpoint keys or cost estimate.
        resolved = ready_client_for_task(vault.root, vault.config, task, explicit=provider)  # type: ignore[arg-type]
        if not resolved.ready:
            raise PFUnavailable(f"PF role {role!r} route {provider!r} is unavailable: {resolved.runtime.message}")
        client = resolved.client
        if not subscription and not client.supports(BOUNDED_STRUCTURED_COMPLETION):
            raise PFUnavailable(f"PF role {role!r} route {provider!r} cannot bound physical requests")
        if not client.supports(ISOLATED_TURN):
            raise PFUnavailable(f"PF role {role!r} route {provider!r} cannot run an isolated, tool-free turn")
        model = getattr(client, "model", None) or profile.model
        result.append(RoleClient(
            role=role, provider=provider, model=model, profile_type=profile.type,
            subscription=subscription, client=client,
            settings=_profile_settings(vault, provider, model),
        ))
    return result


def distinct_models(clients: list[RoleClient]) -> list[str]:
    return sorted({client.model for client in clients if client.model})


@dataclass(frozen=True)
class CallResult:
    result: Any
    model: str
    input_hash: str
    prompt_version: str
    cached: bool
    usage: dict[str, Any]


def estimate_tokens(prompt: str, result_model: type[BaseModel], output_tokens: int) -> int:
    # UTF-8 bytes safely upper-bound ordinary tokenizer input; output is bounded
    # at the request itself.
    schema = len(json.dumps(result_model.model_json_schema()).encode())
    return len(prompt.encode()) + schema + SCHEMA_ALLOWANCE + output_tokens


class PFCaller:
    """One command's budget, receipts, checkpoints and ledger appends."""

    def __init__(self, vault: LoadedVault, repository: Repository, *, caps: SpendCaps,
                 price_per_million: float | None, run_id: str, owner_kind: str = "pf_generation",
                 cancelled: Callable[[], bool] | None = None) -> None:
        self.vault = vault
        self.repository = repository
        self.caps = caps
        self.price = price_per_million
        self.run_id = run_id
        self.owner_kind = owner_kind
        self.cancelled = cancelled
        self.metered = SpendBudget(caps, cancelled=cancelled)
        self.subscription = SpendBudget(caps, cancelled=cancelled, subscription=True)
        self.calls_by_role: dict[str, int] = defaultdict(int)
        self.cached_by_role: dict[str, int] = defaultdict(int)
        self.calls_by_model: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        #: Truncation events (role, model, budget, what happened next).
        self.truncations: list[dict[str, Any]] = []

    # -- budget -----------------------------------------------------------------
    def _price_per_token(self) -> float | None:
        return self.price / 1_000_000 if self.price is not None else None

    def estimate(self, tokens: int, *, subscription: bool, calls: int = 1,
                 candidates: int = 0, pairs: int = 0, retries: int = 0) -> SpendEstimate:
        usd = tokens * self.price / 1_000_000 if self.price is not None else None
        if usd is None and calls == 0:
            usd = 0.0
        return SpendEstimate(candidates=candidates, pairs=pairs, retries=retries, calls=calls,
                             total_tokens=tokens, estimated_usd=usd)

    def _shared_used(self, name: str) -> int:
        return getattr(self.metered.used, name) + getattr(self.subscription.used, name)

    def check_shared(self, estimate: SpendEstimate) -> None:
        if self.cancelled is not None and self.cancelled():
            raise AIInterrupted("PF run cancelled")
        for name in ("calls", "candidates", "pairs", "retries"):
            if self._shared_used(name) + getattr(estimate, name) > getattr(self.caps, f"max_{name}"):
                raise SpendLimitExceeded(f"{name} exceeds max_{name}")

    def check_plan(self, metered: SpendEstimate, subscription: SpendEstimate) -> None:
        """Admit a whole plan before any request (dry-run and pre-run check)."""
        combined = SpendEstimate(
            candidates=metered.candidates + subscription.candidates,
            pairs=metered.pairs + subscription.pairs, retries=0,
            calls=metered.calls + subscription.calls, total_tokens=0, estimated_usd=0.0,
        )
        self.check_shared(combined)
        if metered.calls:
            self.metered.check(SpendEstimate(total_tokens=metered.total_tokens,
                                             estimated_usd=metered.estimated_usd))
        self.subscription.check(SpendEstimate(total_tokens=subscription.total_tokens,
                                              estimated_usd=subscription.estimated_usd))

    def charged(self) -> dict[str, Any]:
        return {"metered": asdict(self.metered.used), "subscription": asdict(self.subscription.used)}

    def declared(self) -> dict[str, Any]:
        return {"metered": self.metered.declared(), "subscription": self.subscription.declared()}

    # -- calls ------------------------------------------------------------------
    def output_tokens(self, entry: RoleClient) -> int:
        """The role's output budget under the shared policy (``ai.output_budget``)."""
        return output_budget(self.vault.config, ROLE_TASKS.get(entry.role), provider=entry.provider)

    def reasoning_effort(self, entry: RoleClient) -> str | None:
        """The role's route's requested reasoning effort, or None (the profile's)."""
        return reasoning_effort(self.vault.config, ROLE_TASKS.get(entry.role))

    def input_hash(self, entry: RoleClient, prompt: str, result_model: type[BaseModel],
                   output_tokens: int) -> str:
        identity: dict[str, Any] = {
            "prompt": prompt, "schema": result_model.model_json_schema(),
            "settings": entry.settings, "output_tokens": output_tokens,
            "isolation": ISOLATION_BOUNDARY,
        }
        effort = self.reasoning_effort(entry)
        if effort:
            identity["reasoning_effort"] = effort
        return content_key(identity)

    def call(self, entry: RoleClient, *, prompt: str, prompt_version: str,
             result_model: type[BaseModel], output_tokens: int | None = None,
             candidates: int = 0, pairs: int = 0) -> CallResult:
        """One isolated, tool-free structured turn (never the vault, files or tools).

        ``output_tokens`` None is the role's policy budget (:meth:`output_tokens`).
        A truncated answer is logged and retried once at double the budget.
        """
        role = entry.role
        if output_tokens is None:
            output_tokens = self.output_tokens(entry)
        effort = self.reasoning_effort(entry)
        input_hash = self.input_hash(entry, prompt, result_model, output_tokens)
        cache_key = CHECKPOINT_PREFIX + input_hash
        saved = self.repository.model_checkpoint(cache_key)
        if saved is not None:
            try:
                result = result_model.model_validate(saved["result"])
            except ValueError:
                self.repository.discard_model_checkpoint(cache_key)
            else:
                self.cached_by_role[role] += 1
                model = saved["usage"].get("resolved_model") or entry.model or "unknown"
                return CallResult(result, model, input_hash, prompt_version, True, saved["usage"])
        if entry.client is None:
            raise PFUnavailable(f"PF role {role!r} has no client")
        if not entry.client.supports(ISOLATED_TURN):
            # Refused before admission: no request, no retry, no charge.
            raise PFUnavailable(f"PF role {role!r} route {entry.provider!r} cannot run an isolated, tool-free turn")
        budget = self.subscription if entry.subscription else self.metered
        truncation = TruncationRetry(output_tokens, role=role, provider=entry.provider, model=entry.model,
                                     owner_kind=self.owner_kind, owner_id=self.run_id,
                                     ceiling=output_ceiling(entry.client))
        tokens = estimate_tokens(prompt, result_model, output_tokens)
        usage: dict[str, Any] = {}
        attempts = 0

        def observer(action: str, event: dict[str, Any]) -> None:
            if action == "start":
                declared = json.loads(event.get("budget_json") or "{}")
                declared["pf"] = {
                    "role": role, "prompt_version": prompt_version, "input_hash": input_hash,
                    "model_id": entry.model, "price_per_million": self.price,
                    "cost_basis": ESTIMATED_ONLY if entry.subscription else "metered_caps",
                    "planned_total_tokens": tokens,
                }
                event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
            else:
                for key in ("resolved_model", "input_tokens", "output_tokens", "cost"):
                    if event.get(key) is not None:
                        usage[key] = event[key]
                event = {**event, "resolved_model": usage.get("resolved_model") or entry.model}
                if entry.subscription:
                    event["usage_json"] = json.dumps(
                        {**json.loads(event.get("usage_json") or "{}"),
                         **subscription_usage_estimate(event, planned_tokens=tokens,
                                                       price_per_token=self._price_per_token())},
                        sort_keys=True,
                    )
            self.repository.record_model_event(action, event, owner_kind=self.owner_kind,
                                               owner_id=self.run_id)

        while True:
            tokens = estimate_tokens(prompt, result_model, truncation.budget)
            estimate = SpendEstimate(
                candidates=candidates if attempts == 0 else 0, pairs=pairs if attempts == 0 else 0,
                retries=int(attempts > 0), calls=1, total_tokens=tokens,
                estimated_usd=tokens * self.price / 1_000_000 if self.price is not None else None,
            )
            self.check_shared(estimate)
            usage.clear()
            try:
                with budget.request(estimate) as charge, observe_model_calls(observer):
                    bound = nullcontext() if entry.subscription else single_request()
                    try:
                        with bound, generation_limit(truncation.budget), truncation.receipts(), \
                                requested_reasoning_effort(effort):
                            result = execute_structured_operation(
                                entry.client, purpose=f"pf_{role}", prompt=prompt,
                                result_model=result_model, isolated=True,
                            )
                    finally:
                        spent = (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                        if entry.subscription and self.price is None:
                            cost = None
                        else:
                            cost = max(usage.get("cost") or 0.0, spent * (self.price or 0.0) / 1_000_000)
                        charge.reconcile(total_tokens=spent, estimated_usd=cost)
                result = result_model.model_validate(result)
            except AIInterrupted:
                raise
            except AIOutputTruncated:
                # Never accepted: logged with the role and model, then retried
                # once at double the budget (admitted as a retry), else failed.
                retry = truncation.after_truncation(
                    allowed=self._shared_used("retries") < self.caps.max_retries)
                self.truncations.append(truncation.events[-1])
                if not retry:
                    raise
                attempts += 1
                continue
            except AIProviderUnavailable:
                if self._shared_used("retries") >= self.caps.max_retries:
                    raise
                attempts += 1
                continue
            break
        model = usage.get("resolved_model") or entry.model or "unknown"
        record = {
            "resolved_model": model, "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"), "cost": usage.get("cost"),
            "role": role, "prompt_version": prompt_version,
            "billing": "subscription" if entry.subscription else "metered",
        }
        if entry.subscription:
            record.update(subscription_usage_estimate(usage, planned_tokens=tokens,
                                                      price_per_token=self._price_per_token()))
        self.repository.save_model_checkpoint(cache_key, purpose=f"pf_{role}",
                                              result=result.model_dump(mode="json"), usage=record)
        self.calls_by_role[role] += 1
        self.calls_by_model[model][role] += 1
        return CallResult(result, model, input_hash, prompt_version, False, record)

    def embed(self, client: Any, texts: list[Any], *, task_prefix: str,
              price_per_million: float | None,
              estimated_tokens: int | None = None) -> list[list[float]]:
        """One metered embedding request, admitted under the shared caps first.

        Embedding routes are always metered (never Codex) and never fall back.
        Unknown prices fail closed. ``client`` follows ``ai.embedding.EmbeddingClient``.
        ``estimated_tokens`` is the caller's upper bound for non-text inputs
        (Slice 2 T6's B4 page images); text inputs are bounded by their bytes.
        """
        tokens = (estimated_tokens if estimated_tokens is not None
                  else sum(len(text.encode("utf-8")) + 128 for text in texts))
        usd = tokens * price_per_million / 1_000_000 if price_per_million is not None else None
        usage: dict[str, Any] = {}
        attempts = 0

        def observer(action: str, event: dict[str, Any]) -> None:
            if action == "start":
                declared = json.loads(event.get("budget_json") or "{}")
                declared["embedding"] = {"model_id": getattr(client, "model_id", None),
                                         "task_prefix": task_prefix, "price_per_million": price_per_million,
                                         "planned_total_tokens": tokens}
                event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
            else:
                usage.update({key: event.get(key) for key in ("input_tokens", "cost") if event.get(key) is not None})
            self.repository.record_model_event(action, event, owner_kind=self.owner_kind, owner_id=self.run_id)

        while True:
            estimate = SpendEstimate(calls=1, retries=int(attempts > 0), total_tokens=tokens, estimated_usd=usd)
            self.check_shared(estimate)
            try:
                with self.metered.request(estimate) as charge, observe_model_calls(observer):
                    try:
                        vectors = client.embed(list(texts), task_prefix)
                    finally:
                        spent = usage.get("input_tokens")
                        cost = usage.get("cost")
                        if spent is not None and price_per_million is not None:
                            cost = max(cost or 0.0, spent * price_per_million / 1_000_000)
                        charge.reconcile(total_tokens=spent, estimated_usd=cost)
            except AIInterrupted:
                raise
            except AIProviderUnavailable:
                if self._shared_used("retries") >= self.caps.max_retries:
                    raise
                attempts += 1
                continue
            if len(vectors) != len(texts):
                raise ValueError("Embedding provider returned the wrong vector count")
            self.calls_by_role["embedding"] += 1
            self.calls_by_model[getattr(client, "model_id", "unknown")]["embedding"] += 1
            return vectors

    # -- ledger -----------------------------------------------------------------
    def ledger(self, *, task: str, left_kind: str, left_id: str, judge: str, input_hash: str,
               verdict: str, right_kind: str | None = None, right_id: str | None = None,
               judge_model: str | None = None, prompt_version: str | None = None,
               score: float | None = None, rationale: Mapping[str, Any] | str = "",
               supersede: bool = False) -> str:
        """Append once per (task, subjects, judge, input); resumes never duplicate.

        ``supersede``: the question (task, left, right) has one current answer,
        so a new verdict names the latest earlier one as ``supersedes_id``.
        """
        judgment_id = "pfv_" + content_key([task, left_kind, left_id, right_kind, right_id,
                                            judge, judge_model, prompt_version, input_hash])
        text = rationale if isinstance(rationale, str) else json.dumps(rationale, sort_keys=True)
        with self.repository.connection() as connection:
            if connection.execute("SELECT 1 FROM judgment_ledger WHERE id=?", (judgment_id,)).fetchone():
                return judgment_id
            previous = None
            if supersede:
                previous = connection.execute(
                    "SELECT id FROM judgment_ledger WHERE task=? AND left_kind=? AND left_id=? "
                    "AND right_kind IS ? AND right_id IS ? ORDER BY rowid DESC LIMIT 1",
                    (task, left_kind, left_id, right_kind, right_id),
                ).fetchone()
            append_judgment(
                connection, id=judgment_id, task=task, left_kind=left_kind, left_id=left_id,
                right_kind=right_kind, right_id=right_id, judge=judge, judge_model=judge_model,
                prompt_version=prompt_version, input_hash=input_hash, verdict=verdict,
                score=score, rationale=text, supersedes_id=previous["id"] if previous else None,
            )
        return judgment_id

    def report(self) -> dict[str, Any]:
        return {
            "calls_by_role": dict(self.calls_by_role),
            "cached_by_role": dict(self.cached_by_role),
            "calls_by_model": {model: dict(roles) for model, roles in sorted(self.calls_by_model.items())},
            "charged": self.charged(),
            "caps_in_force": self.declared(),
            "truncations": list(self.truncations),
        }


__all__ = [
    "CallResult", "ISOLATION_BOUNDARY", "LIST_ROLES", "METERED_TYPES", "PFCaller", "PFUnavailable", "ROLE_TASKS",
    "RoleClient", "TIERED_ROLES", "distinct_models", "estimate_tokens", "planned_role_clients",
    "resolve_role_clients", "role_providers",
]
