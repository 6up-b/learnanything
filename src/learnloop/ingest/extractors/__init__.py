"""Document extractor providers returning the LearnLoop IR (§2.9).

Downstream code imports from here; it never imports marker/pypdf classes directly.
"""

from __future__ import annotations

from learnloop.ingest.extractors.base import (
    DocumentExtractor,
    ExtractionContext,
    single_unit_from_blocks,
)
from learnloop.ingest.extractors.marker import (
    MarkerDocumentExtractor,
    MarkerUnavailableError,
    chunk_output_to_ir,
    marker_available,
    marker_package_version,
)
from learnloop.ingest.extractors.normalizers import captions_to_ir, markdown_to_ir
from learnloop.ingest.extractors.pypdf import PyPdfDocumentExtractor, PyPdfExtractionError

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
    "single_unit_from_blocks",
]


def pdf_extractor_for(config: dict | None = None) -> DocumentExtractor:
    """Select the least-expensive PDF extractor available (§2.9 ``auto``)."""

    if marker_available():
        return MarkerDocumentExtractor(config=config)
    return PyPdfDocumentExtractor()
