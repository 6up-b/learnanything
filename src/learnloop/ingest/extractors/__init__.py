"""Document extractor providers returning the LearnLoop IR (§2.9).

Downstream code imports from here; it never imports marker/pypdf classes directly.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import NamedTuple

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
    "PdfExtractorConsent",
    "captions_to_ir",
    "chunk_output_to_ir",
    "document_pdf_config",
    "extract_with_fallback",
    "fallback_model_versions",
    "local_pdf_extractor",
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


def document_pdf_config(config: dict, raw_bytes: bytes) -> dict:
    """Only GLM-OCR reads a PNG/JPG: a PDF-only engine choice (the native
    PDF model, Marker, pypdf) reads an image the automatic way."""

    from learnloop.ingest.extractors.glm_ocr import is_image_document

    if config.get("engine") in {"native", "marker", "pypdf"} and is_image_document(raw_bytes):
        return {**config, "engine": "auto"}
    return config


class PdfExtractorConsent(NamedTuple):
    flow: str
    plain_message: str | None = None
    code: str = "needs_upload_ok"
    retryable: bool = True


def pdf_extractor_for(
    config: dict | None = None, *, local_only: bool = False, raw_bytes: bytes | None = None,
    upload_allowed: bool | Callable[[], bool] = False, require_upload_ok: bool = False,
) -> DocumentExtractor | tuple[DocumentExtractor | None, PdfExtractorConsent | None]:
    """Choose a reader and, when bytes are supplied, the consent it requires.

    Calls without bytes retain the provider-only API for extraction tools.
    Import jobs supply bytes and the upload OK, then render any returned card.
    """
    settings = dict(config or {})
    if raw_bytes is not None:
        settings = document_pdf_config(settings, raw_bytes)
    extractor = _selected_pdf_extractor(settings, local_only=local_only)
    if raw_bytes is None:
        return extractor
    from learnloop.ingest.extractors.glm_ocr import is_image_document

    image = is_image_document(raw_bytes)
    # A repair OK'd as local, of an image only text recognition elsewhere can read.
    local_image = PdfExtractorConsent(
        "glm_ocr_image",
        "Only text recognition can read an image, and none runs on this computer, where this repair was asked "
        'to stay. Turn on "external VLM" to repair it with text recognition, which sends the image off this computer.',
        "local_repair", False,
    )
    if extractor.name != "glm_ocr" and image:
        if local_only and selected_backend(settings.get("glm_ocr")) is not None:
            # Text recognition is set up, only off this computer (never "add
            # a key" when one is set).
            return None, local_image
        raise MarkerUnavailableError(GLM_UNAVAILABLE_MESSAGE)
    if extractor.name != "glm_ocr":
        return extractor, None
    if local_only and extractor.leaves_this_computer():
        # An explicit glm_ocr engine still names a reader off this computer,
        # and the learner OK'd this repair as local: a PDF is read here, and
        # an image, which only text recognition reads, is refused.
        return (None, local_image) if image else (local_pdf_extractor(settings), None)
    if extractor.backend == "api":
        if (
            str(settings.get("engine") or "auto") == "auto" and not image and not require_upload_ok
            and not (upload_allowed() if callable(upload_allowed) else upload_allowed)
        ):
            local = local_pdf_extractor(settings)
            local.selection_reason = "glm_ocr_needs_upload_ok"
            return local, None
        return extractor, PdfExtractorConsent(
            "glm_ocr_upload",
            "Reading this image with GLM-OCR sends it to z.ai, which needs your OK first. "
            "Say OK on its card in the Library." if image else None,
        )
    return extractor, None


def _selected_pdf_extractor(config: dict | None = None, *, local_only: bool = False) -> DocumentExtractor:
    """Select the document extractor (§2.9) for a PDF, PNG or JPG.

    ``config["engine"]`` decides. ``"auto"`` (or absent) prefers GLM-OCR's
    complete layout + recognition pipeline (z.ai when a key is set, or a
    configured, reachable self-hosted server), then local Marker, then pypdf;
    the chosen extractor carries ``selection_reason`` for extraction health.
    ``"glm_ocr"``/``"marker"`` fail rather than switch; ``"pypdf"`` forces
    the native-text fallback. ``config["glm_ocr"]`` holds the
    ``[ingest.pdf.glm_ocr]`` settings and, like ``engine``, never reaches a
    provider's options. ``local_only``: a reading that must stay on this
    computer (an extraction repair the learner OK'd as local) never selects
    hosted GLM-OCR, or a self-hosted server on another computer, in
    ``"auto"``; an explicit ``"glm_ocr"`` still returns either, so the
    consent-aware selection (``pdf_extractor_for``) reads it locally instead."""

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
        backend = selected_backend(glm_config, local_only=local_only)
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


def local_pdf_extractor(config: dict | None = None) -> DocumentExtractor:
    """What reads a PDF without it leaving this computer: local Marker when
    installed, else pypdf (never hosted Marker, which needs its own OK)."""

    options = {k: v for k, v in (config or {}).items() if k not in {"engine", "glm_ocr"}}
    return MarkerDocumentExtractor(config=options) if marker_available() else PyPdfDocumentExtractor()


def fallback_model_versions(extractor_name: str) -> dict[str, str]:
    """The model versions of the local extractor that stood in for the one
    chosen (:func:`extract_with_fallback`), for the stored extraction run."""

    if extractor_name == "marker":
        return MarkerDocumentExtractor().model_versions()
    if extractor_name == "pypdf":
        return PyPdfDocumentExtractor().model_versions()
    return {}


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
            fallback = local_pdf_extractor(config)
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
        # The fallback, and what stopped the reading when it says so (Marker's
        # worker crashed or ran out of time: marker_worker.MarkerWorkerError).
        for flag in (f"{extractor.name}_failed_{fallback.name}_fallback", getattr(exc, "health_flag", None)):
            if flag and flag not in ir.health.flags:
                ir.health.flags.append(flag)
    # Why this extractor was chosen holds whichever read it in the end (a
    # local reading while the z.ai OK is missing stays offered an upgrade).
    reason = getattr(extractor, "selection_reason", None)
    if reason and reason not in ir.health.flags:
        ir.health.flags.append(reason)
    return ir
