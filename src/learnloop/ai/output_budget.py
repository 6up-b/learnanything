"""One output-budget policy for every LLM role (owner, 2026-10-12).

Before this, each role carried its own hand-set output cap (a 1,200-token
rewrite, a 1,500-token question writer, a 600-token judge...). Reasoning models
spend their thinking from the same budget, so those caps cut answers off: on
the T6 rerun Claude Haiku 5.5 was truncated on 28 of 36 question-writer calls
and 6 of 68 rewrites. The policy:

* **One generous default.** ``ai.output_tokens`` (16,384), large enough for a
  reasoning model's thinking and its answer. ``ai.route_output_tokens.<route>``
  replaces it for one route. A profile's own ``max_tokens`` (the provider or
  profile maximum) is a ceiling: it replaces the default for that profile, and a
  route override above it is held to it, because the chat transport never
  sends more (review F6). The budget is what a request sends as ``max_tokens``
  and what spend admission reserves.
* **A truncation is never accepted.** A response that stops for length
  (``finish_reason = "length"``, or the provider's equivalent) raises
  ``AIOutputTruncated``; it is logged as an event with its role, provider and
  model (:func:`record_truncation`, and the attempt's receipt has status
  ``truncated``), then retried once at double the budget, held to the
  transport's ceiling (:func:`output_ceiling`). A call already at its ceiling,
  or truncated twice, fails. Callers that own their spend admission (one
  physical request per admitted attempt) retry in their own loop with
  :class:`TruncationRetry`, which admits the increased budget it will send and
  tags the retry's receipt; elsewhere the chat transport retries itself, and
  the admitting caller reserves each physical request at the allowance it is
  sent with.
* **Reasoning effort per route.** ``ai.route_reasoning_effort.<route>`` asks
  for an effort where the provider supports one (OpenRouter's
  ``reasoning.effort``, Codex's turn effort); T6's rewrite and verification
  default to ``low``. Empty keeps the profile's own setting.

Exempt: the Decider's typed answers (a 16-token decision API, not a chat
completion) and the owner-set synthesis budgets in ``[ingest.budgets]``.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import logging
from typing import Any

from learnloop.ai.execution import annotate_calls
from learnloop.config.schema import DEFAULT_OUTPUT_TOKENS

logger = logging.getLogger(__name__)

#: A truncated call is retried once with this many times its budget.
TRUNCATION_RETRY_FACTOR = 2
#: Effort values that mean "use the profile's own reasoning setting".
PROFILE_EFFORT = frozenset({"", "profile"})


def _profile_for(config: Any, route: str | None, provider: str | None) -> Any:
    ai = getattr(config, "ai", None)
    if ai is None:
        return None
    name = provider
    if name is None and route:
        from learnloop.ai.routing import provider_for_task

        try:
            name = provider_for_task(config, route, allow_env=False).provider_name  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001 - a route we cannot resolve has no profile maximum
            name = None
    return ai.providers.get(name) if name else None


def output_budget(config: Any | None, route: str | None = None, *, provider: str | None = None) -> int:
    """The output-token budget for one LLM call on ``route``.

    ``ai.route_output_tokens.<route>`` if set (held to the serving profile's
    ``max_tokens``, the transport's ceiling), else the profile's own
    ``max_tokens``, else ``ai.output_tokens``. ``config`` None (a caller with no
    vault) is the code default. ``provider`` names the serving profile when the
    caller already resolved it (an injected or pinned client).
    """

    ai = getattr(config, "ai", None)
    if ai is None:
        return DEFAULT_OUTPUT_TOKENS
    profile = _profile_for(config, route, provider)
    declared = _positive(getattr(profile, "max_tokens", None) if profile is not None else None)
    override = (getattr(ai, "route_output_tokens", None) or {}).get(route or "")
    if override is not None:
        # The profile maximum is a ceiling the transport enforces: a route
        # override above it would be reserved but never sent.
        return min(int(override), declared) if declared is not None else int(override)
    if declared is not None:
        return declared
    return int(getattr(ai, "output_tokens", None) or DEFAULT_OUTPUT_TOKENS)


def _positive(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def output_ceiling(client: Any) -> int | None:
    """The most output tokens ``client``'s transport will ever send, or None.

    The chat transport clamps every request to its profile's ``max_tokens``, so
    a truncation retry above it would re-send the same limit (review F6). Codex
    and other transports without a hard output cap have no ceiling.
    """

    profile = getattr(client, "profile", None)
    return _positive(getattr(profile, "max_tokens", None)) if profile is not None else None


def reasoning_effort(config: Any | None, route: str | None) -> str | None:
    """The reasoning effort ``route`` asks for, or None to keep the profile's."""

    ai = getattr(config, "ai", None)
    if ai is None or not route:
        return None
    effort = (getattr(ai, "route_reasoning_effort", None) or {}).get(route)
    if effort is None:
        return None
    effort = str(effort).strip().lower()
    return None if effort in PROFILE_EFFORT else effort


def record_truncation(*, role: str | None, provider: str | None, model: str | None, budget: int | None,
                      retry_budget: int | None, owner_kind: str | None = None,
                      owner_id: str | None = None, next_step: str | None = None) -> dict[str, Any]:
    """Log one truncation as an event; returns its fields (for receipts and reports).

    The truncated attempt's own receipt already has status ``truncated`` and
    its finish reason; this event names the role and model and says what
    happens next (``retry_budget`` None: the call fails, unless ``next_step``
    is ``caller``: a caller-owned loop decides, and logs its own event).
    """

    step = next_step or ("retry" if retry_budget else "fail")
    event = {"event": "output_truncated", "role": role, "provider": provider, "model": model,
             "budget": budget, "retry_budget": retry_budget, "owner_kind": owner_kind,
             "owner_id": owner_id, "next": step}
    logger.warning(
        "LLM output truncated: role=%s provider=%s model=%s budget=%s; %s",
        role, provider, model, budget,
        f"retrying once with {retry_budget} output tokens" if step == "retry"
        else "the caller decides" if step == "caller" else "failing",
    )
    return event


@dataclass
class TruncationRetry:
    """One logical call's output budget: increased once after a truncation.

    Use in a caller-owned retry loop::

        retry = TruncationRetry(budget, role=role, provider=provider, model=model,
                                ceiling=output_ceiling(client))
        while True:
            admit(estimate(retry.budget))
            try:
                with retry.receipts(), generation_limit(retry.budget):
                    ...
            except AIOutputTruncated:
                if not retry.after_truncation():
                    raise
                continue

    ``after_truncation`` logs the event and returns True at most once: the
    retry asks for double the budget, held to ``ceiling`` (the transport's
    maximum, :func:`output_ceiling`), and a call already at its ceiling fails
    at once, since another request could not have more room (review F6).
    ``budget`` is then what the retry sends, reserves and records.
    """

    budget: int
    role: str | None = None
    provider: str | None = None
    model: str | None = None
    owner_kind: str | None = None
    owner_id: str | None = None
    retried: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)
    #: The most output tokens the transport sends (None: no hard maximum).
    ceiling: int | None = None
    previous_budget: int | None = None

    @property
    def initial_budget(self) -> int:
        return self.previous_budget if self.retried and self.previous_budget is not None else self.budget

    def after_truncation(self, *, allowed: bool = True) -> bool:
        """Record a truncation; True when the call should retry with a larger budget.

        ``allowed`` False (the caller's retry cap is spent) records the event as
        a failure without retrying, as does a budget already at the ceiling.
        """

        retry_budget = None
        if allowed and not self.retried and (self.ceiling is None or self.budget < self.ceiling):
            retry_budget = self.budget * TRUNCATION_RETRY_FACTOR
            if self.ceiling is not None:
                retry_budget = min(retry_budget, self.ceiling)
        event = record_truncation(
            role=self.role, provider=self.provider, model=self.model, budget=self.budget,
            retry_budget=retry_budget, owner_kind=self.owner_kind, owner_id=self.owner_id)
        if self.ceiling is not None and self.budget >= self.ceiling:
            event["reason"] = "at_transport_ceiling"
        self.events.append(event)
        if retry_budget is None:
            return False
        self.retried = True
        self.previous_budget = self.budget
        self.budget = retry_budget
        return True

    @contextmanager
    def receipts(self) -> Iterator[None]:
        """Tag the root receipt of a truncation retry (its ``budget_json``)."""

        if not self.retried:
            yield
            return
        with annotate_calls(truncation_retry={
            "role": self.role, "model": self.model, "previous_budget": self.initial_budget,
            "budget": self.budget,
        }):
            yield


__all__ = [
    "DEFAULT_OUTPUT_TOKENS",
    "PROFILE_EFFORT",
    "TRUNCATION_RETRY_FACTOR",
    "TruncationRetry",
    "output_budget",
    "output_ceiling",
    "reasoning_effort",
    "record_truncation",
]
