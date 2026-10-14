"""Document extractor providers returning the LearnLoop IR (§2.9).

Downstream code imports from here; it never imports marker/pypdf classes directly.
"""

from __future__ import annotations

import os

from learnloop.ingest.extractors.base import (
    DocumentExtractor,
    ExtractionContext,
    single_unit_from_blocks,
    units_from_toc_entries,
)
from learnloop.ingest.extractors.datalab import (
    DATALAB_API_KEY_ENV,
    DatalabDocumentExtractor,
    DatalabExtractionError,
    datalab_api_key,
)
from learnloop.ingest.extractors.glm_ocr import EXTRACTOR_NAME as EXTRACTOR_NAME_GLM
from learnloop.ingest.extractors.glm_ocr import UNAVAILABLE_MESSAGE as GLM_UNAVAILABLE_MESSAGE
from learnloop.ingest.extractors.glm_ocr import (
    GlmOcrDocumentExtractor,
    GlmOcrExtractionError,
    selected_backend,
)
from learnloop.ingest.extractors.marker import (
    MarkerDocumentExtractor,
    MarkerUnavailableError,
    chunk_output_to_ir,
    marker_available,
    marker_package_version,
)
from learnloop.ingest.extractors.normalizers import captions_to_ir, markdown_to_ir, transcript_to_ir
from learnloop.ingest.extractors.pypdf import (
    PyPdfDocumentExtractor,
    PyPdfExtractionError,
    read_embedded_outline,
)

__all__ = [
    "NativeEngineNotLocalError",
    "DocumentExtractor",
    "DatalabDocumentExtractor",
    "DatalabExtractionError",
    "ExtractionContext",
    "ExtractionFallbackFailed",
    "GlmOcrDocumentExtractor",
    "GlmOcrExtractionError",
    "MarkerDocumentExtractor",
    "MarkerUnavailableError",
    "PyPdfDocumentExtractor",
    "PyPdfExtractionError",
    "captions_to_ir",
    "chunk_output_to_ir",
    "extract_with_fallback",
    "markdown_to_ir",
    "marker_available",
    "marker_package_version",
    "pdf_extractor_for",
    "read_embedded_outline",
    "single_unit_from_blocks",
    "transcript_to_ir",
    "units_from_toc_entries",
]


class ExtractionFallbackFailed(RuntimeError):
    """The chosen extractor failed and so did its local fallback."""


class NativeEngineNotLocalError(ValueError):
    """``engine = "native"`` reached the local extractor registry.

    Native PDF ingestion is a chat-provider path owned by the durable pipeline
    (``learnloop.content.pipeline.jobs``); the registry must never quietly
    substitute marker or pypdf for it."""


def pdf_extractor_for(config: dict | None = None, *, keep_local: bool = False) -> DocumentExtractor:
    """Select the document extractor (§2.9) for a PDF, PNG or JPG.

    ``config["engine"]`` decides. ``"auto"`` (or absent) prefers GLM-OCR's
    complete layout + recognition pipeline (z.ai when a key is set, or a
    configured, reachable self-hosted server), then local Marker, then pypdf;
    the chosen extractor carries ``selection_reason`` for extraction health.
    ``"glm_ocr"``/``"marker"`` fail rather than switch; ``"pypdf"`` forces
    the native-text fallback. ``config["glm_ocr"]`` holds the
    ``[ingest.pdf.glm_ocr]`` settings and, like ``engine``, never reaches a
    provider's options. ``keep_local``: a book kept on this computer never
    selects hosted GLM-OCR in ``"auto"`` (an explicit ``"glm_ocr"`` still
    returns it, so the import's upload guard refuses with its own words)."""

    settings = dict(config or {})
    engine = str(settings.pop("engine", "") or "auto")
    glm_config = dict(settings.pop("glm_ocr", None) or {})
    if engine == "native":
        raise NativeEngineNotLocalError(
            'PDF engine "native" is not a local extractor; the import pipeline routes it to the '
            "canonical_ingest chat provider"
        )
    if engine == "pypdf":
        return PyPdfDocumentExtractor()
    if engine not in {"auto", "glm_ocr", "marker"}:
        raise ValueError(f"Unknown PDF engine: {engine!r}")
    if engine in {"auto", "glm_ocr"}:
        backend = selected_backend(glm_config, keep_local=keep_local)
        if backend is None and engine == "glm_ocr":
            backend = selected_backend(glm_config)
        if backend is not None:
            return GlmOcrDocumentExtractor(config=glm_config, backend=backend)
        if engine == "glm_ocr":
            raise MarkerUnavailableError(GLM_UNAVAILABLE_MESSAGE)
    provider = os.environ.get("LEARNLOOP_MARKER_PROVIDER", "local").strip().lower()
    if provider not in {"", "local", "datalab"}:
        raise MarkerUnavailableError(
            "LEARNLOOP_MARKER_PROVIDER must be either 'local' or 'datalab'"
        )
    if provider == "datalab":
        if not datalab_api_key():
            raise MarkerUnavailableError(
                f"Datalab Marker was requested but {DATALAB_API_KEY_ENV} is not set"
            )
        return DatalabDocumentExtractor(config=settings)
    if engine == "marker" and not marker_available():
        raise MarkerUnavailableError(
            "PDF engine 'marker' was requested but marker-pdf is not installed; "
            "install learnloop[pdf] or choose the 'pypdf' fallback"
        )
    if marker_available():
        extractor = MarkerDocumentExtractor(config=settings)
        if engine == "auto":
            extractor.selection_reason = "glm_ocr_unavailable_marker_selected"
        return extractor
    extractor = PyPdfDocumentExtractor()
    extractor.selection_reason = "glm_ocr_and_marker_unavailable_pypdf_selected"
    return extractor


def extract_with_fallback(
    raw_bytes: bytes, extractor: DocumentExtractor, config: dict, context: ExtractionContext
):
    """Run ``extractor``; under ``engine = "auto"`` a runtime failure degrades
    to the next local extractor with a health flag naming why (§2.9).

    GLM-OCR failing falls back to local Marker, else pypdf (never to hosted
    Marker, which would need its own upload OK); Marker failing falls back to
    pypdf. A PNG/JPG has no fallback. Refusals are never failures to degrade
    from: a missing whole-file OK and spend refusals/cancellations propagate,
    as does every failure under an explicit engine."""

    from learnloop.ai.spend import SpendCancelled, SpendLimitExceeded
    from learnloop.ingest.extractors.glm_ocr import GlmOcrConsentRequired, is_image_document

    try:
        ir = extractor.extract(raw_bytes, context)
    except (GlmOcrConsentRequired, SpendLimitExceeded, SpendCancelled):
        raise
    except Exception as exc:
        if str(config.get("engine") or "auto") != "auto" or is_image_document(raw_bytes):
            raise
        if extractor.name == EXTRACTOR_NAME_GLM and isinstance(exc, GlmOcrExtractionError):
            options = {k: v for k, v in config.items() if k not in {"engine", "glm_ocr"}}
            fallback = MarkerDocumentExtractor(config=options) if marker_available() else PyPdfDocumentExtractor()
        elif extractor.name == "marker":
            fallback = PyPdfDocumentExtractor()
        else:
            raise
        try:
            ir = extract_with_fallback(raw_bytes, fallback, {"engine": "auto"}, context)
        except (SpendLimitExceeded, SpendCancelled):
            raise
        except Exception as fallback_exc:
            raise ExtractionFallbackFailed(
                f"{extractor.name}: {exc}; {fallback.name} fallback: {fallback_exc}"
            ) from fallback_exc
        flag = f"{extractor.name}_failed_{fallback.name}_fallback"
        if flag not in ir.health.flags:
            ir.health.flags.append(flag)
        return ir
    reason = getattr(extractor, "selection_reason", None)
    if reason and reason not in ir.health.flags:
        ir.health.flags.append(reason)
    return ir
