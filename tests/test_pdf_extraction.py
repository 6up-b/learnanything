from __future__ import annotations

import importlib.util
import os

import pytest

from learnloop.config import PdfIngestConfig
from learnloop.content.sources import pdf_extraction
from learnloop.content.sources.pdf_extraction import PdfExtractionError, extract_pdf_markdown
from learnloop.content.pipeline.source_ingestion import SourceIngestionError, _resolved_pdf_config

from tests.marker_fakes import fake_marker  # noqa: F401 - fixture
from tests.test_source_ingestion_adapters import _make_pdf_bytes


_MARKDOWN = "# Chapter 3\n\nEigenvalues satisfy\n\n$$Av = \\lambda v$$\n"


def _install_fake_marker(monkeypatch, fake_marker, *, markdown: str = _MARKDOWN):
    """The on-disk fake (tests/marker_fakes.py): Marker converts in a worker
    process, which a fake in this process's sys.modules would never reach."""

    monkeypatch.setenv("FAKE_MARKER_MARKDOWN", markdown)
    return fake_marker


def _hide_marker(monkeypatch):
    real_find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name, *args: None if name == "marker" else real_find_spec(name, *args),
    )


def test_auto_engine_falls_back_to_pypdf_when_marker_missing(monkeypatch):
    _hide_marker(monkeypatch)
    extraction = extract_pdf_markdown(_make_pdf_bytes(["Eigenvalues are scalars."]))
    assert extraction.engine == "pypdf"
    assert "Eigenvalues" in extraction.markdown
    assert not extraction.used_llm


def test_native_engine_is_rejected_by_legacy_extractor():
    # The one-shot CLI extractor has no chat client: an explicit "native"
    # choice must not silently become marker/pypdf.
    with pytest.raises(PdfExtractionError, match="native"):
        extract_pdf_markdown(_make_pdf_bytes(["text"]), config=PdfIngestConfig(engine="native"))


def test_explicit_marker_engine_requires_marker(monkeypatch):
    _hide_marker(monkeypatch)
    config = PdfIngestConfig(engine="marker")
    with pytest.raises(PdfExtractionError, match="marker-pdf is required"):
        extract_pdf_markdown(_make_pdf_bytes(["text"]), config=config)


def test_marker_engine_converts_and_caches(monkeypatch, tmp_path, fake_marker):
    _install_fake_marker(monkeypatch, fake_marker)
    cache_dir = tmp_path / "pdf-cache"
    raw = _make_pdf_bytes(["chapter text"])

    extraction = extract_pdf_markdown(raw, config=PdfIngestConfig(), cache_dir=cache_dir)
    assert extraction.engine == "marker"
    assert "$$Av = \\lambda v$$" in extraction.markdown
    assert not extraction.from_cache
    (call,) = fake_marker.calls()
    assert call["pid"] != os.getpid()  # converted in Marker's worker process
    assert call["filepath"].endswith("source.pdf")
    assert call["config"]["pdftext_workers"] == 1
    assert list(cache_dir.glob("*.md")), "converted markdown should be cached"

    again = extract_pdf_markdown(raw, config=PdfIngestConfig(), cache_dir=cache_dir)
    assert again.from_cache
    assert again.markdown == extraction.markdown


def test_marker_pdftext_worker_override_is_preserved(monkeypatch, fake_marker):
    _install_fake_marker(monkeypatch, fake_marker)

    extract_pdf_markdown(
        _make_pdf_bytes(["chapter text"]),
        config=PdfIngestConfig(marker_options={"pdftext_workers": 2}),
    )

    assert fake_marker.calls()[-1]["config"]["pdftext_workers"] == 2


def test_marker_llm_options_map_to_openai_service(monkeypatch, tmp_path, fake_marker):
    _install_fake_marker(monkeypatch, fake_marker)
    monkeypatch.setenv("LEARNLOOP_PDF_LLM_API_KEY", "sk-test")
    config = PdfIngestConfig(
        use_llm=True,
        llm_base_url="http://127.0.0.1:8000/v1",
        llm_model="deepseek-ai/DeepSeek-OCR",
    )

    extraction = extract_pdf_markdown(_make_pdf_bytes(["x"]), config=config)
    assert extraction.used_llm
    options = fake_marker.calls()[-1]["config"]
    assert options["use_llm"] is True
    assert options["llm_service"] == "marker.services.openai.OpenAIService"
    assert options["openai_base_url"] == "http://127.0.0.1:8000/v1"
    assert options["openai_model"] == "deepseek-ai/DeepSeek-OCR"
    assert options["openai_api_key"] == "sk-test"


def test_cache_key_excludes_api_key(monkeypatch):
    monkeypatch.setenv("LEARNLOOP_PDF_LLM_API_KEY", "sk-one")
    config = PdfIngestConfig(use_llm=True, llm_model="deepseek-ai/DeepSeek-OCR")
    key_one = pdf_extraction._cache_key(b"pdf", pdf_extraction._marker_options(config))
    monkeypatch.setenv("LEARNLOOP_PDF_LLM_API_KEY", "sk-two")
    key_two = pdf_extraction._cache_key(b"pdf", pdf_extraction._marker_options(config))
    assert key_one == key_two


def test_marker_upgrade_changes_cache_key(monkeypatch):
    # The extraction cache key must be version-pinned so a marker upgrade does not
    # silently serve stale output (ING §2.2/§2.5). The version fingerprint is a
    # first-class cache-key input.
    options = pdf_extraction._marker_options(PdfIngestConfig())
    key_v1 = pdf_extraction._cache_key(b"pdf", options, "marker=1.9.0;ir=ir-1")
    key_v2 = pdf_extraction._cache_key(b"pdf", options, "marker=2.0.0;ir=ir-1")
    assert key_v1 != key_v2
    # Same fingerprint is deterministic.
    assert key_v1 == pdf_extraction._cache_key(b"pdf", options, "marker=1.9.0;ir=ir-1")


def test_marker_cache_fingerprint_includes_ir_schema_version():
    from learnloop.ingest.ir import IR_SCHEMA_VERSION

    fingerprint = pdf_extraction._marker_cache_fingerprint()
    assert IR_SCHEMA_VERSION in fingerprint
    assert fingerprint.startswith("marker=")


def test_marker_torch_device_pin_sets_env(monkeypatch, fake_marker):
    # Marker's worker gets the pin in its environment; this process's
    # environment (the sidecar's) is never changed.
    _install_fake_marker(monkeypatch, fake_marker)
    monkeypatch.delenv("TORCH_DEVICE", raising=False)
    extract_pdf_markdown(_make_pdf_bytes(["x"]), config=PdfIngestConfig(torch_device="cuda:1"))
    assert fake_marker.calls()[-1]["torch_device"] == "cuda:1"
    assert "TORCH_DEVICE" not in os.environ

    extract_pdf_markdown(_make_pdf_bytes(["x"]), config=PdfIngestConfig())
    assert fake_marker.calls()[-1]["torch_device"] is None, "auto-detect must not pin a device"


def test_marker_empty_output_raises(monkeypatch, fake_marker):
    _install_fake_marker(monkeypatch, fake_marker, markdown="   ")
    with pytest.raises(PdfExtractionError, match="no extractable content"):
        extract_pdf_markdown(_make_pdf_bytes(["x"]), config=PdfIngestConfig())


def test_resolved_pdf_config_overrides_and_validates():
    base = PdfIngestConfig()
    assert _resolved_pdf_config(base, engine=None, use_llm=None) is base
    overridden = _resolved_pdf_config(base, engine="pypdf", use_llm=True)
    assert overridden.engine == "pypdf"
    assert overridden.use_llm is True
    with pytest.raises(SourceIngestionError, match="invalid PDF extraction settings"):
        _resolved_pdf_config(base, engine="docling", use_llm=None)
