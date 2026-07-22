"""Pluggable PDF -> Markdown extraction for canonical source ingestion.

Engines:

- ``marker``: high-fidelity structured conversion via marker-pdf — headings,
  tables, LaTeX equations ($$ blocks chunk as ``math`` downstream), and
  built-in OCR for scanned pages. With ``use_llm`` enabled, difficult regions
  (poor scans, dense math, cross-page tables) are additionally sent to an
  OpenAI-compatible VLM endpoint — e.g. a local vLLM serving
  ``deepseek-ai/DeepSeek-OCR``, or any hosted vision model.
- ``pypdf``: plain per-page text extraction. No OCR, layout, tables, or math;
  raises on scanned/image-only PDFs.
- ``auto``: marker when importable, otherwise pypdf.

Marker conversion is model inference and slow (seconds to minutes per
chapter), so results are cached in ``cache_dir`` keyed by the PDF bytes and
the extraction configuration (secrets excluded). Page images extracted by
marker are dropped: canonical sources are Markdown-only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learnloop.config import PdfIngestConfig


class PdfExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class PdfExtraction:
    markdown: str
    engine: str  # "marker" | "pypdf"
    used_llm: bool = False
    from_cache: bool = False


# One converter per marker config; marker model weights load once per process.
_MARKER_CONVERTERS: dict[str, Any] = {}


def extract_pdf_markdown(
    raw_bytes: bytes,
    *,
    config: PdfIngestConfig | None = None,
    cache_dir: Path | None = None,
) -> PdfExtraction:
    config = config or PdfIngestConfig()
    engine = _resolve_engine(config)
    if engine == "pypdf":
        return _extract_with_pypdf(raw_bytes)
    options = _marker_options(config)
    cache_key = _cache_key(raw_bytes, options, _marker_cache_fingerprint())
    cached = _read_cache(cache_dir, cache_key)
    if cached is not None:
        return cached
    extraction = _extract_with_marker(raw_bytes, config, options)
    _write_cache(cache_dir, cache_key, extraction)
    return extraction


def _resolve_engine(config: PdfIngestConfig) -> str:
    if config.engine == "pypdf":
        return "pypdf"
    marker_available = importlib.util.find_spec("marker") is not None
    if config.engine == "marker" and not marker_available:
        raise PdfExtractionError(
            "marker-pdf is required when ingest.pdf.engine = \"marker\"; install it "
            "with 'pip install learnloop[pdf]' or set the engine to \"auto\"/\"pypdf\""
        )
    return "marker" if marker_available else "pypdf"


def _marker_options(config: PdfIngestConfig) -> dict[str, Any]:
    # pdftext otherwise forks its default worker pool after Marker has loaded
    # CUDA models.  Forking a CUDA-initialized, multithreaded process can leave
    # every worker asleep on inherited locks.  Serializing this CPU pre-pass is
    # a safe default and does not disable Surya's batched GPU inference.
    options: dict[str, Any] = {"output_format": "markdown", "pdftext_workers": 1}
    if config.force_ocr:
        options["force_ocr"] = True
    if config.use_llm:
        options["use_llm"] = True
        options["llm_service"] = config.llm_service
        if config.llm_service.endswith("OpenAIService"):
            if config.llm_base_url:
                options["openai_base_url"] = config.llm_base_url
            if config.llm_model:
                options["openai_model"] = config.llm_model
            api_key = os.environ.get(config.llm_api_key_env, "")
            if api_key:
                options["openai_api_key"] = api_key
    options.update(config.marker_options or {})
    return options


def _extract_with_marker(raw_bytes: bytes, config: PdfIngestConfig, options: dict[str, Any]) -> PdfExtraction:
    # surya (marker's model layer) reads TORCH_DEVICE when its settings module
    # first loads, so this must be set before the first marker import.
    if config.torch_device:
        os.environ["TORCH_DEVICE"] = config.torch_device

    from marker.output import text_from_rendered

    converter = _marker_converter(options)
    with tempfile.TemporaryDirectory(prefix="learnloop-pdf-") as tmp:
        pdf_path = Path(tmp) / "source.pdf"
        pdf_path.write_bytes(raw_bytes)
        try:
            rendered = converter(str(pdf_path))
        except Exception as exc:
            raise PdfExtractionError(f"marker failed to convert PDF: {exc}") from exc
    text, _, _images = text_from_rendered(rendered)
    markdown = (text or "").strip()
    if not markdown:
        raise PdfExtractionError("PDF produced no extractable content")
    return PdfExtraction(markdown=markdown + "\n", engine="marker", used_llm=bool(config.use_llm))


def _marker_converter(options: dict[str, Any]) -> Any:
    key = json.dumps(options, sort_keys=True, default=str)
    converter = _MARKER_CONVERTERS.get(key)
    if converter is not None:
        return converter
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    parser = ConfigParser(options)
    converter = PdfConverter(
        config=parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=parser.get_processors(),
        renderer=parser.get_renderer(),
        llm_service=parser.get_llm_service(),
    )
    _MARKER_CONVERTERS[key] = converter
    return converter


def _extract_with_pypdf(raw_bytes: bytes) -> PdfExtraction:
    try:
        import pypdf
    except ImportError as exc:  # pragma: no cover - hard dependency guard
        raise PdfExtractionError("pypdf is required for PDF ingestion; install it with 'uv add pypdf'") from exc

    try:
        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        pages = [text for page in reader.pages if (text := (page.extract_text() or "").strip())]
    except Exception as exc:
        raise PdfExtractionError(f"failed to read PDF source: {exc}") from exc
    markdown = "\n\n".join(pages).strip()
    if not markdown:
        raise PdfExtractionError(
            "PDF contained no extractable text (likely scanned images); "
            "install marker-pdf ('pip install learnloop[pdf]') for OCR support"
        )
    return PdfExtraction(markdown=markdown + "\n", engine="pypdf")


def _marker_cache_fingerprint() -> str:
    """Version fingerprint mixed into the extraction cache key (ING §2.2/§2.5).

    Including the marker package version and the IR schema version means a marker
    upgrade changes the cache key — fixing the stale-cache bug where an upgraded
    marker silently served output cached under the old version. Best-effort: an
    unresolvable version degrades to a stable placeholder, never an exception.
    """

    from learnloop.ingest.ir import IR_SCHEMA_VERSION

    try:
        from importlib.metadata import version

        marker_version = version("marker-pdf")
    except Exception:  # pragma: no cover - best effort
        marker_version = "unknown"
    return f"marker={marker_version};ir={IR_SCHEMA_VERSION}"


def _cache_key(raw_bytes: bytes, options: dict[str, Any], version_fingerprint: str = "") -> str:
    fingerprint = {key: value for key, value in options.items() if key != "openai_api_key"}
    payload = json.dumps(
        {
            "pdf_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "options": fingerprint,
            "version": version_fingerprint,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_cache(cache_dir: Path | None, key: str) -> PdfExtraction | None:
    if cache_dir is None:
        return None
    body_path = cache_dir / f"{key}.md"
    meta_path = cache_dir / f"{key}.json"
    if not body_path.exists() or not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return PdfExtraction(
        markdown=body_path.read_text(encoding="utf-8"),
        engine=str(meta.get("engine", "marker")),
        used_llm=bool(meta.get("used_llm", False)),
        from_cache=True,
    )


def _write_cache(cache_dir: Path | None, key: str, extraction: PdfExtraction) -> None:
    if cache_dir is None:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"{key}.md").write_text(extraction.markdown, encoding="utf-8")
    (cache_dir / f"{key}.json").write_text(
        json.dumps({"engine": extraction.engine, "used_llm": extraction.used_llm}, sort_keys=True),
        encoding="utf-8",
    )
