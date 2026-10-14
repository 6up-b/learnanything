from __future__ import annotations

import pytest

from learnloop.ingest.extractors import (
    NativeEngineNotLocalError,
    PyPdfDocumentExtractor,
    pdf_extractor_for,
)


def test_native_engine_never_resolves_to_a_local_extractor():
    with pytest.raises(NativeEngineNotLocalError, match="native"):
        pdf_extractor_for({"engine": "native"})


def test_pypdf_engine_resolves_locally():
    assert isinstance(pdf_extractor_for({"engine": "pypdf"}), PyPdfDocumentExtractor)


def test_pypdf_text_with_lone_surrogates_reads_with_replacement_characters(monkeypatch):
    # pypdf returns lone UTF-16 surrogates for some unmapped maths-font glyphs
    # (an arXiv paper's equations); hashing them used to fail the extraction.
    import io

    from pypdf import PdfWriter
    from pypdf._page import PageObject

    from learnloop.ingest.extractors.base import ExtractionContext

    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    out = io.BytesIO()
    writer.write(out)
    monkeypatch.setattr(PageObject, "extract_text", lambda self, *a, **kw: " L = \ud835 ∑ p ")
    ir = PyPdfDocumentExtractor().extract(out.getvalue(), ExtractionContext("rev"))
    assert ir.blocks[0].text == "L = � ∑ p"
