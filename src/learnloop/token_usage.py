"""Provider-reported token accounting (spec_diagnostic_augmentation_v1.md §2 A7).

Migration 131 gives `agent_runs` `actual_input_tokens` / `actual_output_tokens`
so §3 C3's `tokens_per_resolved_diagnostic_episode` has a numerator. Those
numbers only exist inside the provider response, which is discarded well before
the service layer decides the run is finished — so the seam is: every provider
client accumulates what it was told, and the write path *drains* the accumulator
once when it completes the run.

Accumulate-then-drain, rather than "return usage alongside the result", because
one agent run is one logical episode but several HTTP requests: a JSON repair
round (`openai_chat._run_json_messages`), a sharded synthesis, a per-window
ingest. Threading usage back through ~25 `run_*` return types to sum it at the
call site would change every signature; a per-client counter sums it for free.

This module deliberately lives at the package root rather than under
`learnloop.ai`: `learnloop.ai.__init__` imports `learnloop.ai.client`, which
imports `learnloop.codex.client`, so a `learnloop.ai.*` import from inside
`codex/client.py` would be a cycle.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

# Guards only the lazy creation of a client's own mutex (see
# `TokenUsageAccounting`), never a counter update.
_USAGE_INIT_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """What one or more model calls actually cost, as the provider reported it.

    ``calls`` is not persisted (migration 131 has no column for it) but is what
    distinguishes "the run made no model calls" from "the provider reported no
    usage": a run with `calls > 0` and zero tokens is a provider that does not
    expose usage, which is a different fact from a cache hit.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            calls=self.calls + other.calls,
        )

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class TokenUsageAccounting:
    """Per-client token accumulator mixed into every provider client.

    State is materialized lazily on first use instead of in an ``__init__``:
    provider clients are built through several different constructor chains
    (``CodexSDKProviderClient`` -> ``SdkCodexClient``,
    ``OpenRouterProviderClient`` -> ``OpenAIChatProviderClient``) and some of
    them raise ``CodexUnavailable`` partway through, so a client that never
    finished constructing must still answer ``consume_usage()`` rather than
    raising ``AttributeError`` at the point a service is trying to record a
    *failed* run.

    The counters are class-level ints (immutable, so no shared-mutable-default
    hazard); the first ``record_token_usage`` shadows them on the instance.
    """

    _usage_input_tokens = 0
    _usage_output_tokens = 0
    _usage_calls = 0
    _usage_lock: threading.Lock | None = None

    def _usage_mutex(self) -> threading.Lock:
        lock = self.__dict__.get("_usage_lock")
        if lock is None:
            with _USAGE_INIT_LOCK:
                lock = self.__dict__.get("_usage_lock")
                if lock is None:
                    lock = threading.Lock()
                    self._usage_lock = lock
        return lock

    def record_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Add one model call's reported usage. Never raises on junk input.

        Called from the transport before anything can parse or validate the
        response body — a run that produced unparseable JSON still cost tokens,
        and a cost meter that only counts successes understates the denominator
        of every ratio built on it.
        """

        with self._usage_mutex():
            self._usage_input_tokens += _coerce_tokens(input_tokens)
            self._usage_output_tokens += _coerce_tokens(output_tokens)
            self._usage_calls += 1

    def consume_usage(self) -> TokenUsage:
        """Read and reset. One agent run owns everything since the last drain."""

        with self._usage_mutex():
            usage = TokenUsage(
                input_tokens=self._usage_input_tokens,
                output_tokens=self._usage_output_tokens,
                calls=self._usage_calls,
            )
            self._usage_input_tokens = 0
            self._usage_output_tokens = 0
            self._usage_calls = 0
        return usage


def consume_client_usage(client: Any | None) -> TokenUsage:
    """Drain ``client``'s accumulator, tolerating clients that have none.

    Duck-typed on purpose. `AIProviderClient` declares `consume_usage`, but the
    grading/authoring services accept anything with the `run_*` method they
    need — including the many hand-rolled stub clients in the test suite and the
    sidecar's own adapters. A stub without the method means "no usage reported",
    which is exactly `TokenUsage()`; raising there would turn a missing test
    fake method into a failed agent run.
    """

    consume = getattr(client, "consume_usage", None)
    if not callable(consume):
        return TokenUsage()
    try:
        usage = consume()
    except Exception:  # pragma: no cover - a cost meter never breaks a run
        return TokenUsage()
    return usage if isinstance(usage, TokenUsage) else TokenUsage()


def usage_from_chat_response(response: Any) -> tuple[int, int]:
    """Pull (input, output) tokens off an OpenAI-shaped chat completion.

    Handles the attribute-shaped SDK object and the dict-shaped body, and both
    the chat-completions spelling (`prompt_tokens`/`completion_tokens`) and the
    responses/OpenRouter spelling (`input_tokens`/`output_tokens`). Anything
    missing, None, or non-numeric reads as 0: usage is telemetry, and a provider
    that omits it must not turn a good grade into a failed run.
    """

    usage = _attr_or_key(response, "usage")
    if usage is None:
        return 0, 0
    input_tokens = _attr_or_key(usage, "prompt_tokens")
    if input_tokens is None:
        input_tokens = _attr_or_key(usage, "input_tokens")
    output_tokens = _attr_or_key(usage, "completion_tokens")
    if output_tokens is None:
        output_tokens = _attr_or_key(usage, "output_tokens")
    return _coerce_tokens(input_tokens), _coerce_tokens(output_tokens)


def usage_from_codex_turn(result: Any) -> tuple[int, int]:
    """Pull (input, output) tokens off a Codex SDK ``TurnResult``.

    ``TurnResult.usage`` is a ``ThreadTokenUsage`` carrying two
    ``TokenUsageBreakdown``s: ``total`` (this thread, cumulative) and ``last``
    (the most recent model request). ``total`` is the right one — LearnLoop
    starts a fresh thread per structured call, so thread-total *is* turn-total,
    and a turn that used tools made several requests of which ``last`` is only
    the final one. ``output_tokens`` already folds in reasoning output.

    ``usage`` is None whenever the SDK never emitted a
    ``ThreadTokenUsageUpdated`` notification (older app-servers, or a turn that
    failed before the first response), which reads as 0.
    """

    usage = _attr_or_key(result, "usage")
    if usage is None:
        return 0, 0
    breakdown = _attr_or_key(usage, "total")
    if breakdown is None:
        breakdown = _attr_or_key(usage, "last")
    if breakdown is None:
        return 0, 0
    return (
        _coerce_tokens(_attr_or_key(breakdown, "input_tokens")),
        _coerce_tokens(_attr_or_key(breakdown, "output_tokens")),
    )


def _attr_or_key(payload: Any, name: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(name)
    return getattr(payload, name, None)


def _coerce_tokens(value: Any) -> int:
    """Non-negative int or 0. Absorbs None, strings, floats and NaN."""

    if isinstance(value, bool) or value is None:
        return 0
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return count if count > 0 else 0
