"""Lightweight native-text PDF fallback (spec_source_ingestion_v2 §2.9).

``PyPdfDocumentExtractor`` produces the same IR contract as marker: one block per
page (native text, no OCR/layout/geometry). It satisfies the identical downstream
tests. Raises on scanned/image-only PDFs, where marker is required.
"""

from __future__ import annotations

import io
from typing import Any

from learnloop.ingest.block_roles import classify_block_role
from learnloop.ingest.extractors.base import (
    ExtractionContext,
    single_unit_from_blocks,
    units_from_toc_entries,
)
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, block_content_hash

EXTRACTOR_NAME = "pypdf"


def read_embedded_outline(raw_bytes: bytes) -> list[dict[str, Any]]:
    """Flatten a PDF's embedded outline (bookmarks) into ToC-shaped entries.

    Many PDFs carry an author-curated section tree in their document outline —
    exact titles with resolvable destination pages. Returns
    ``[{"title", "heading_level", "page_id"}, ...]`` with levels from nesting
    depth, ordered as authored. Best-effort: any failure (no outline, encrypted,
    unresolvable destinations) returns ``[]`` and extraction proceeds without it.
    """

    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        if reader.is_encrypted:
            reader.decrypt("")
        outline = reader.outline
    except Exception:
        return []

    entries: list[dict[str, Any]] = []

    def walk(items: Any, level: int) -> None:
        for item in items or []:
            if isinstance(item, list):
                walk(item, level + 1)
                continue
            title = str(getattr(item, "title", "") or "").strip()
            try:
                page = reader.get_destination_page_number(item)
            except Exception:
                page = None
            if title and page is not None and page >= 0:
                entries.append({"title": title, "heading_level": level, "page_id": int(page)})

    try:
        walk(outline, 1)
    except Exception:  # pragma: no cover - malformed outline trees
        return []
    return entries


class PyPdfExtractionError(ValueError):
    pass


class PyPdfDocumentExtractor:
    name = EXTRACTOR_NAME

    # IR-mapping version, mixed into version() (and thus the extraction request
    # hash) so mapping changes never silently reuse cached extractions. 2: units
    # derive from the PDF's embedded outline when one exists.
    IR_MAP_VERSION = 2

    def version(self) -> str:
        try:
            from importlib.metadata import version

            package = version("pypdf")
        except Exception:  # pragma: no cover - best effort
            package = "unknown"
        return f"{package}+map{self.IR_MAP_VERSION}"

    def model_versions(self) -> dict[str, str]:
        return {}

    def extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR:
        try:
            import pypdf
        except ImportError as exc:  # pragma: no cover - hard dependency guard
            raise PyPdfExtractionError("pypdf is required for the native-text fallback") from exc

        try:
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            if reader.is_encrypted:
                # Many "encrypted" PDFs only restrict printing/copying and open
                # with an empty user password; a real password requirement stays
                # a typed, user-actionable refusal.
                try:
                    decrypted = reader.decrypt("")
                except Exception as exc:
                    raise PyPdfExtractionError(
                        "PDF is password-protected; provide a decrypted copy"
                    ) from exc
                if not decrypted:
                    raise PyPdfExtractionError(
                        "PDF is password-protected; provide a decrypted copy"
                    )
            selected = list(context.page_selection) if context.page_selection is not None else list(range(len(reader.pages)))
            if any(page < 0 or page >= len(reader.pages) for page in selected):
                raise PyPdfExtractionError(
                    f"requested PDF page range exceeds the document's {len(reader.pages)} pages"
                )
            page_texts = [(page_index, (reader.pages[page_index].extract_text() or "").strip()) for page_index in selected]
        except PyPdfExtractionError:
            raise
        except Exception as exc:
            raise PyPdfExtractionError(f"failed to read PDF source: {exc}") from exc

        blocks: list[DocumentBlock] = []
        for page_index, text in page_texts:
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
        outline = read_embedded_outline(raw_bytes)
        if outline:
            # drop_empty: an outline covers the whole book while a page-sliced
            # import extracts only part of it.
            units = units_from_toc_entries(
                outline, blocks, document_title=title,
                locator_scheme="pdf_outline", drop_empty=True,
            )
        else:
            units = []
        if not units:
            units = [single_unit_from_blocks(blocks, label=title or "Document")]
        return DocumentIR(
            ir_schema_version=IR_SCHEMA_VERSION,
            extractor=EXTRACTOR_NAME,
            extractor_version=self.version(),
            blocks=blocks,
            units=units,
        )


def _pdf_title(raw_bytes: bytes) -> str | None:
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        return (getattr(reader.metadata, "title", None) or None) if reader.metadata else None
    except Exception:  # pragma: no cover - best effort
        return None
