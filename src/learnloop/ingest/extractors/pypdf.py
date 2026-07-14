"""Lightweight native-text PDF fallback (spec_source_ingestion_v2 §2.9).

``PyPdfDocumentExtractor`` produces the same IR contract as marker: one block per
page (native text, no OCR/layout/geometry). It satisfies the identical downstream
tests. Raises on scanned/image-only PDFs, where marker is required.
"""

from __future__ import annotations

import io
from typing import Any

from learnloop.ingest.block_roles import classify_block_role
from learnloop.ingest.extractors.base import ExtractionContext, single_unit_from_blocks
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, block_content_hash

EXTRACTOR_NAME = "pypdf"


class PyPdfExtractionError(ValueError):
    pass


class PyPdfDocumentExtractor:
    name = EXTRACTOR_NAME

    def version(self) -> str:
        try:
            from importlib.metadata import version

            return version("pypdf")
        except Exception:  # pragma: no cover - best effort
            return "unknown"

    def model_versions(self) -> dict[str, str]:
        return {}

    def extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR:
        try:
            import pypdf
        except ImportError as exc:  # pragma: no cover - hard dependency guard
            raise PyPdfExtractionError("pypdf is required for the native-text fallback") from exc

        try:
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
        except Exception as exc:
            raise PyPdfExtractionError(f"failed to read PDF source: {exc}") from exc

        blocks: list[DocumentBlock] = []
        for page_index, text in enumerate(page_texts):
            if not text:
                continue
            ordinal = len(blocks) + 1
            blocks.append(
                DocumentBlock(
                    span_id=f"s{ordinal}",
                    extractor_block_id=None,
                    block_type="Text",
                    role_hint=classify_block_role("Text", [], text),
                    page=page_index,
                    bbox=None,
                    polygon=None,
                    section_path=[],
                    text=text,
                    content_hash=block_content_hash(text),
                    asset_ids=[],
                    ordinal=ordinal,
                )
            )
        if not blocks:
            raise PyPdfExtractionError(
                "PDF contained no extractable text (likely scanned images); "
                "install marker-pdf for OCR support"
            )

        title = _pdf_title(raw_bytes)
        unit = single_unit_from_blocks(blocks, label=title or "Document")
        return DocumentIR(
            ir_schema_version=IR_SCHEMA_VERSION,
            extractor=EXTRACTOR_NAME,
            extractor_version=self.version(),
            blocks=blocks,
            units=[unit],
        )


def _pdf_title(raw_bytes: bytes) -> str | None:
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        return (getattr(reader.metadata, "title", None) or None) if reader.metadata else None
    except Exception:  # pragma: no cover - best effort
        return None
