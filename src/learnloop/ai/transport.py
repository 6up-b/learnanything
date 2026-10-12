"""Small provider-neutral transport contract for structured AI work."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Generic, Mapping, Protocol, TypeVar, cast, runtime_checkable

from pydantic import BaseModel

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.schemas import WireModel
from learnloop.ai.usage import TokenUsage
from learnloop.ai.execution import model_call, output_limit

WireResult = TypeVar("WireResult", bound=WireModel)

STRUCTURED_COMPLETION = "structured_completion"
MEDIA_TRANSCRIPTION = "media_transcription"
MEDIA_MARKDOWN = "media_markdown"
INTERRUPT = "interrupt"
EMBEDDING = "embedding"
# Read-only file access to a prepared directory for the turn (Slice 1 §5.6).
# The directory REPLACES the transport's default working directory; a
# transport advertising this capability guarantees the model can read only
# that directory, cannot write anywhere, and has no network.
READ_ONLY_WORKSPACE = "read_only_workspace"
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
    output_budget_tokens: int | None = None
    #: A directory the model may read (never write) during the turn. Only a
    #: transport that declares :data:`READ_ONLY_WORKSPACE` may receive one.
    workspace: Path | None = None

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
    workspace: Path | None = None,
) -> WireResult:
    """Execute one feature-owned structured operation.

    ``workspace`` asks for read-only file access to one prepared directory.
    It is refused, before any request, unless the transport declares
    :data:`READ_ONLY_WORKSPACE`: silently dropping it would run a
    file-reading prompt with no files, and widening it is never an option.

    SDK and chat providers expose one capability and one method:
    :data:`STRUCTURED_COMPLETION` and :meth:`StructuredTransport.complete`.
    The retained endpoint-per-operation HTTP adapter cannot implement that
    contract without changing its wire protocol, so its eight historical
    operations use its generic ``complete_legacy`` adapter method, guarded by
    their declared capability. No provider-specific branching belongs in a
    feature.
    """

    if workspace is not None and not transport.supports(READ_ONLY_WORKSPACE):
        provider = getattr(transport, "provider_name", type(transport).__name__)
        raise AIProviderUnavailable(
            f"AI provider {provider!r} does not support a read-only workspace "
            f"for structured operation {purpose!r}"
        )
    request = StructuredRequest(
        purpose=purpose,
        prompt=prompt,
        result_model=result_model,
        timeout_seconds=timeout_seconds,
        output_budget_tokens=output_limit(),
        workspace=Path(workspace) if workspace is not None else None,
    )
    with model_call(transport, purpose=purpose, prompt=prompt, schema=result_model.model_json_schema(), budget=request.output_budget_tokens) as metadata:
        result = _execute_request(transport, request, legacy_context, legacy_capability)
        if isinstance(result, BaseModel):
            metadata["output_text"] = result.model_dump_json()
        return result


def _execute_request(transport, request, legacy_context, legacy_capability):
    purpose = request.purpose
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
    *,
    context_tail_fields: tuple[str, ...] = (),
) -> str:
    """Render the byte-stable envelope shared by feature-owned operations."""

    def encode(key: str) -> str:
        value = prompt_safe(payload[key])
        if key == "context" and isinstance(value, dict) and context_tail_fields:
            ordered = sorted(value, key=lambda field: (field in context_tail_fields, field))
            return "{" + ", ".join(f"{json.dumps(field)}: {json.dumps(value[field], sort_keys=True, ensure_ascii=False)}" for field in ordered) + "}"
        return json.dumps(value, sort_keys=True, ensure_ascii=False)

    return (
        f"{title}\n"
        f"prompt_version: {prompt_version}\n\n"
        "Return only JSON that matches the provided output schema. Do not include "
        "Markdown fences or explanatory prose.\n\n"
        # Keep stable instructions before changing source content. Each value
        # remains canonically encoded, so identical prefixes stay byte stable.
        + "{" + ", ".join(f"{json.dumps(key)}: {encode(key)}" for key in sorted(payload, key=lambda key: (key == "context", key))) + "}"
    )

__all__ = [
    "EMBEDDING",
    "INTERRUPT",
    "CapabilityTransport",
    "InterruptibleTransport",
    "LegacyOperationTransport",
    "MEDIA_MARKDOWN",
    "MEDIA_TRANSCRIPTION",
    "OperationClient",
    "READ_ONLY_WORKSPACE",
    "STRUCTURED_COMPLETION",
    "StructuredRequest",
    "StructuredTransport",
    "WireResult",
    "execute_structured_operation",
    "interrupt_callback",
    "prompt_safe",
    "render_structured_prompt",
]
