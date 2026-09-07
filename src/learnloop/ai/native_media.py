"""Readiness of native media ingestion, per modality.

"Native" ingestion sends a media file (a PDF, an mp3/wav) to the routed
OpenAI-compatible chat provider as a content part instead of extracting it
locally. Whether that can happen is a pure configuration question with one
answer: this module computes it for the ingest pipeline (extraction identity
and extraction), the desktop settings payload, and enqueue-time checks, so
the cache identity, the job outcome and the Settings screen never disagree.

Authority per modality lives in that modality's own table:

* PDF   → ``[ingest.pdf] engine = "native"``
* audio → ``[ingest.audio] mode = "native"``

``[ingest.native]`` only carries shared limits. Capability is declared per
provider profile (``input_modalities``), never probed at run time, so
extraction identity stays deterministic and offline tests stay honest.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from learnloop.ai.routing import AITask, provider_for_task
from learnloop.config.schema import LearnLoopConfig

NATIVE_MODALITIES: tuple[str, ...] = ("pdf", "audio")
NATIVE_TASK: dict[str, AITask] = {"pdf": "canonical_ingest", "audio": "canonical_ingest"}
NATIVE_PROVIDER_TYPES = frozenset({"openai_chat", "openrouter"})

REASON_MANUAL_PROVIDER = "manual_provider"
REASON_PROVIDER_MISSING = "provider_missing"
REASON_PROVIDER_NOT_CHAT = "provider_not_chat"
REASON_MODALITY_NOT_DECLARED = "modality_not_declared"


@dataclass(frozen=True)
class NativeModalityReadiness:
    modality: str
    #: The learner chose native for this modality (vault config or per-run override).
    requested: bool
    #: The AI task whose route carries the media.
    task: str
    provider_name: str | None
    provider_type: str | None
    model: str | None
    #: ``modality`` appears in the routed profile's ``input_modalities``.
    declared: bool
    #: Declared AND the provider is an OpenAI-compatible chat provider.
    ready: bool
    #: ``None`` when ready, else one of the ``REASON_*`` constants.
    reason: str | None
    #: One human sentence for the UI and for typed errors.
    message: str
    #: Upload cap for this modality from ``[ingest.native]``.
    max_mb: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def native_requested(config: LearnLoopConfig, modality: str) -> bool:
    """Whether the vault config selects the native path for ``modality``."""

    if modality == "pdf":
        return config.ingest.pdf.engine == "native"
    if modality == "audio":
        return config.ingest.audio.mode == "native"
    return False


def native_max_mb(config: LearnLoopConfig, modality: str) -> int:
    return config.ingest.native.max_pdf_mb if modality == "pdf" else config.ingest.native.max_audio_mb


def native_modality_readiness(
    config: LearnLoopConfig, modality: str, *, requested: bool | None = None
) -> NativeModalityReadiness:
    """Resolve the routed provider for ``modality`` and judge it.

    ``requested`` overrides the vault-level choice (the pipeline passes the
    effective per-run PDF engine). Provider selection goes through
    ``provider_for_task`` so the ``LEARNLOOP_AI_PROVIDER`` override is honoured
    exactly as at run time.
    """

    if modality not in NATIVE_MODALITIES:
        raise ValueError(f"unknown native modality {modality!r}; expected one of {NATIVE_MODALITIES}")
    task = NATIVE_TASK[modality]
    wanted = native_requested(config, modality) if requested is None else bool(requested)
    max_mb = native_max_mb(config, modality)
    selection = provider_for_task(config, task)
    name = selection.provider_name or None
    profile = config.ai.providers.get(name) if name else None
    provider_type = profile.type.lower() if profile is not None else None
    model = profile.model if profile is not None else None
    declared = bool(profile is not None and modality in (profile.input_modalities or []))

    def result(*, ready: bool, reason: str | None, message: str) -> NativeModalityReadiness:
        return NativeModalityReadiness(
            modality=modality,
            requested=wanted,
            task=task,
            provider_name=name,
            provider_type=provider_type,
            model=model,
            declared=declared,
            ready=ready,
            reason=reason,
            message=message,
            max_mb=max_mb,
        )

    if name is None or name == "manual":
        return result(
            ready=False,
            reason=REASON_MANUAL_PROVIDER,
            message=f"the {task} route is manual mode; native {modality} ingestion needs a chat provider",
        )
    if profile is None:
        return result(
            ready=False,
            reason=REASON_PROVIDER_MISSING,
            message=f"the {task} route names provider {name!r}, which is not configured",
        )
    if provider_type not in NATIVE_PROVIDER_TYPES:
        return result(
            ready=False,
            reason=REASON_PROVIDER_NOT_CHAT,
            message=(
                f"provider {name!r} is type {provider_type!r}; native {modality} ingestion needs an "
                "OpenAI-compatible chat provider (openai_chat or openrouter)"
            ),
        )
    if not declared:
        return result(
            ready=False,
            reason=REASON_MODALITY_NOT_DECLARED,
            message=(
                f"provider {name!r} ({model or 'no model'}) does not declare {modality!r} in "
                "input_modalities"
            ),
        )
    return result(ready=True, reason=None, message=f"{name} ({model or 'no model'}) accepts {modality} natively")


__all__ = [
    "NATIVE_MODALITIES",
    "NATIVE_PROVIDER_TYPES",
    "NATIVE_TASK",
    "REASON_MANUAL_PROVIDER",
    "REASON_MODALITY_NOT_DECLARED",
    "REASON_PROVIDER_MISSING",
    "REASON_PROVIDER_NOT_CHAT",
    "NativeModalityReadiness",
    "native_max_mb",
    "native_modality_readiness",
    "native_requested",
]
