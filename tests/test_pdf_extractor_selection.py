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
