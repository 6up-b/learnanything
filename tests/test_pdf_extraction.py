from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import types

import pytest

from learnloop.config import PdfIngestConfig
from learnloop.services import pdf_extraction
from learnloop.services.pdf_extraction import PdfExtractionError, extract_pdf_markdown
from learnloop.services.source_ingestion import SourceIngestionError, _resolved_pdf_config

from tests.test_source_ingestion_adapters import _make_pdf_bytes


class _FakeConfigParser:
    def __init__(self, options):
        self.options = dict(options)

    def generate_config_dict(self):
        return dict(self.options)

    def get_processors(self):
        return []

    def get_renderer(self):
        return "markdown-renderer"

    def get_llm_service(self):
        return self.options.get("llm_service")


class _FakeRendered:
    markdown = "# Chapter 3\n\nEigenvalues satisfy\n\n$$Av = \\lambda v$$\n"


def _install_fake_marker(monkeypatch, *, captured: dict, markdown: str | None = None) -> None:
    rendered = _FakeRendered()
    if markdown is not None:
        rendered.markdown = markdown

    class _FakePdfConverter:
        def __init__(self, config, artifact_dict, processor_list, renderer, llm_service):
            captured["config"] = config
            captured["llm_service"] = llm_service

        def __call__(self, filepath):
            captured["filepath"] = filepath
            return rendered

    package = types.ModuleType("marker")
    package.__spec__ = importlib.machinery.ModuleSpec("marker", loader=None)
    package.__path__ = []

    config_pkg = types.ModuleType("marker.config")
    parser_mod = types.ModuleType("marker.config.parser")
    parser_mod.ConfigParser = _FakeConfigParser
    converters_pkg = types.ModuleType("marker.converters")
    converters_pdf = types.ModuleType("marker.converters.pdf")
    converters_pdf.PdfConverter = _FakePdfConverter
    models_mod = types.ModuleType("marker.models")
    models_mod.create_model_dict = lambda: {"models": "loaded"}
    output_mod = types.ModuleType("marker.output")
    output_mod.text_from_rendered = lambda rendered: (rendered.markdown, "md", {})

    for name, module in {
        "marker": package,
        "marker.config": config_pkg,
        "marker.config.parser": parser_mod,
        "marker.converters": converters_pkg,
        "marker.converters.pdf": converters_pdf,
        "marker.models": models_mod,
        "marker.output": output_mod,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(pdf_extraction, "_MARKER_CONVERTERS", {})


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


def test_explicit_marker_engine_requires_marker(monkeypatch):
    _hide_marker(monkeypatch)
    config = PdfIngestConfig(engine="marker")
    with pytest.raises(PdfExtractionError, match="marker-pdf is required"):
        extract_pdf_markdown(_make_pdf_bytes(["text"]), config=config)


def test_marker_engine_converts_and_caches(monkeypatch, tmp_path):
    captured: dict = {}
    _install_fake_marker(monkeypatch, captured=captured)
    cache_dir = tmp_path / "pdf-cache"
    raw = _make_pdf_bytes(["chapter text"])

    extraction = extract_pdf_markdown(raw, config=PdfIngestConfig(), cache_dir=cache_dir)
    assert extraction.engine == "marker"
    assert "$$Av = \\lambda v$$" in extraction.markdown
    assert not extraction.from_cache
    assert captured["filepath"].endswith("source.pdf")
    assert captured["config"]["pdftext_workers"] == 1
    assert list(cache_dir.glob("*.md")), "converted markdown should be cached"

    again = extract_pdf_markdown(raw, config=PdfIngestConfig(), cache_dir=cache_dir)
    assert again.from_cache
    assert again.markdown == extraction.markdown


def test_marker_pdftext_worker_override_is_preserved(monkeypatch):
    captured: dict = {}
    _install_fake_marker(monkeypatch, captured=captured)

    extract_pdf_markdown(
        _make_pdf_bytes(["chapter text"]),
        config=PdfIngestConfig(marker_options={"pdftext_workers": 2}),
    )

    assert captured["config"]["pdftext_workers"] == 2


def test_marker_llm_options_map_to_openai_service(monkeypatch, tmp_path):
    captured: dict = {}
    _install_fake_marker(monkeypatch, captured=captured)
    monkeypatch.setenv("LEARNLOOP_PDF_LLM_API_KEY", "sk-test")
    config = PdfIngestConfig(
        use_llm=True,
        llm_base_url="http://127.0.0.1:8000/v1",
        llm_model="deepseek-ai/DeepSeek-OCR",
    )

    extraction = extract_pdf_markdown(_make_pdf_bytes(["x"]), config=config)
    assert extraction.used_llm
    options = captured["config"]
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


def test_marker_torch_device_pin_sets_env(monkeypatch):
    captured: dict = {}
    _install_fake_marker(monkeypatch, captured=captured)
    original = os.environ.pop("TORCH_DEVICE", None)
    try:
        extract_pdf_markdown(_make_pdf_bytes(["x"]), config=PdfIngestConfig(torch_device="cuda:1"))
        assert os.environ["TORCH_DEVICE"] == "cuda:1"
        del os.environ["TORCH_DEVICE"]

        extract_pdf_markdown(_make_pdf_bytes(["x"]), config=PdfIngestConfig())
        assert "TORCH_DEVICE" not in os.environ, "auto-detect must not pin a device"
    finally:
        os.environ.pop("TORCH_DEVICE", None)
        if original is not None:
            os.environ["TORCH_DEVICE"] = original


def test_marker_empty_output_raises(monkeypatch):
    captured: dict = {}
    _install_fake_marker(monkeypatch, captured=captured, markdown="   ")
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
