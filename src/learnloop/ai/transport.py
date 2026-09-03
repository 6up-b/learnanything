"""Small provider-neutral transport contract for structured AI work."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Callable, Generic, Mapping, Protocol, TypeVar, cast, runtime_checkable

from pydantic import BaseModel

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.schemas import WireModel
from learnloop.ai.usage import TokenUsage

WireResult = TypeVar("WireResult", bound=WireModel)

STRUCTURED_COMPLETION = "structured_completion"
MEDIA_TRANSCRIPTION = "media_transcription"
MEDIA_MARKDOWN = "media_markdown"
INTERRUPT = "interrupt"
# Text-to-video generation (an async job API, not a chat completion).
VIDEO_GENERATION = "video_generation"


@dataclass(frozen=True, slots=True)
class StructuredRequest(Generic[WireResult]):
    """One validated completion request independent of provider mechanics.

    ``purpose`` is the stable provenance/debug label currently used by the
    Codex SDK. ``timeout_seconds`` is carried explicitly for transports that
    can enforce a per-request deadline; provider clients with a configured
    request timeout may leave it unset.
    """

    purpose: str
    prompt: str
    result_model: type[WireResult]
    timeout_seconds: float | None = None

    @property
    def model_type(self) -> type[WireResult]:
        """Compatibility spelling for callers that describe a Pydantic type."""

        return self.result_model

    @property
    def wire_model(self) -> type[WireResult]:
        """Make the request's wire contract explicit at call sites."""

        return self.result_model


@runtime_checkable
class OperationClient(Protocol):
    """Common identity/capability surface for structured or legacy operations."""

    provider_name: str
    provider_type: str
    model: str | None

    def supports(self, capability: str) -> bool:
        """Declare optional transport capabilities without method probing."""

        ...


@runtime_checkable
class StructuredTransport(OperationClient, Protocol):
    """The complete provider protocol for shared structured operations."""

    def complete(self, request: StructuredRequest[WireResult]) -> WireResult:
        """Return a response validated as ``request.result_model``."""

        ...


class LegacyOperationTransport(OperationClient, Protocol):
    """Endpoint adapter that executes only explicitly supported operations."""

    def complete_legacy(
        self,
        request: StructuredRequest[WireResult],
        *,
        context: object,
    ) -> WireResult:
        """Execute a feature-owned request over a legacy named endpoint."""

        ...

    def consume_usage(self) -> TokenUsage:
        """Read and reset accumulated provider-reported usage."""

        ...


class InterruptibleTransport(Protocol):
    """Narrow typed view activated only after the capability check."""

    def interrupt(self) -> Any:
        ...


@runtime_checkable
class CapabilityTransport(Protocol):
    """The minimum runtime surface needed for optional capabilities."""

    def supports(self, capability: str) -> bool:
        ...


def interrupt_callback(transport: object) -> Callable[[], Any] | None:
    """Return the typed interrupt hook when the transport declares support."""

    if not isinstance(transport, CapabilityTransport) or not transport.supports(INTERRUPT):
        return None
    return cast(InterruptibleTransport, transport).interrupt


def execute_structured_operation(
    transport: OperationClient,
    *,
    purpose: str,
    prompt: str,
    result_model: type[WireResult],
    timeout_seconds: float | None = None,
    legacy_capability: str | None = None,
    legacy_context: object | None = None,
) -> WireResult:
    """Execute one feature-owned structured operation.

    SDK and chat providers expose one capability and one method:
    :data:`STRUCTURED_COMPLETION` and :meth:`StructuredTransport.complete`.
    The retained endpoint-per-operation HTTP adapter cannot implement that
    contract without changing its wire protocol, so its eight historical
    operations use its generic ``complete_legacy`` adapter method, guarded by
    their declared capability. No provider-specific branching belongs in a
    feature.
    """

    request = StructuredRequest(
        purpose=purpose,
        prompt=prompt,
        result_model=result_model,
        timeout_seconds=timeout_seconds,
    )
    if transport.supports(STRUCTURED_COMPLETION):
        # Advertising the capability is the transport-level guarantee that the
        # operation client implements the complete() contract.  The cast keeps
        # legacy endpoint adapters honest without runtime method probing.
        return cast(StructuredTransport, transport).complete(request)
    if (
        legacy_context is not None
        and legacy_capability is not None
        and transport.supports(legacy_capability)
    ):
        return cast(LegacyOperationTransport, transport).complete_legacy(
            request,
            context=legacy_context,
        )
    provider = getattr(transport, "provider_name", type(transport).__name__)
    raise AIProviderUnavailable(
        f"AI provider {provider!r} does not support structured operation {purpose!r}"
    )


def prompt_safe(value: Any) -> Any:
    """Convert an operation context value into bounded JSON prompt data."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Mapping):
        return {str(key): prompt_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [prompt_safe(child) for child in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def render_structured_prompt(
    title: str,
    prompt_version: str,
    payload: Mapping[str, Any],
) -> str:
    """Render the byte-stable envelope shared by feature-owned operations."""

    return (
        f"{title}\n"
        f"prompt_version: {prompt_version}\n\n"
        "Return only JSON that matches the provided output schema. Do not include "
        "Markdown fences or explanatory prose.\n\n"
        f"{json.dumps(prompt_safe(payload), sort_keys=True, ensure_ascii=False)}"
    )

__all__ = [
    "INTERRUPT",
    "CapabilityTransport",
    "InterruptibleTransport",
    "LegacyOperationTransport",
    "MEDIA_MARKDOWN",
    "MEDIA_TRANSCRIPTION",
    "OperationClient",
    "STRUCTURED_COMPLETION",
    "StructuredRequest",
    "StructuredTransport",
    "WireResult",
    "execute_structured_operation",
    "interrupt_callback",
    "prompt_safe",
    "render_structured_prompt",
]
