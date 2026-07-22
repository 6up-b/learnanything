"""Document extractor providers returning the LearnLoop IR (§2.9).

Downstream code imports from here; it never imports marker/pypdf classes directly.
"""

from __future__ import annotations

from learnloop.ingest.extractors.base import (
    DocumentExtractor,
    ExtractionContext,
    single_unit_from_blocks,
    units_from_toc_entries,
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
    "DocumentExtractor",
    "ExtractionContext",
    "MarkerDocumentExtractor",
    "MarkerUnavailableError",
    "PyPdfDocumentExtractor",
    "PyPdfExtractionError",
    "captions_to_ir",
    "chunk_output_to_ir",
    "markdown_to_ir",
    "marker_available",
    "marker_package_version",
    "read_embedded_outline",
    "single_unit_from_blocks",
    "transcript_to_ir",
    "units_from_toc_entries",
]


def pdf_extractor_for(config: dict | None = None) -> DocumentExtractor:
    """Select the PDF extractor (§2.9).

    ``config["engine"]`` decides: ``"pypdf"`` forces the native-text fallback,
    ``"marker"`` requires marker-pdf (raises :class:`MarkerUnavailableError`
    when it is not importable), and ``"auto"``/absent picks the least-expensive
    available engine — marker when importable, else pypdf. The ``engine`` key is
    consumed here and never leaks into marker's runtime options."""

    settings = dict(config or {})
    engine = str(settings.pop("engine", "") or "auto")
    if engine == "pypdf":
        return PyPdfDocumentExtractor()
    if engine == "marker" and not marker_available():
        raise MarkerUnavailableError(
            "PDF engine 'marker' was requested but marker-pdf is not installed; "
            "install learnloop[pdf] or choose the 'pypdf' fallback"
        )
    if marker_available():
        return MarkerDocumentExtractor(config=settings)
    return PyPdfDocumentExtractor()
