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
- ``glm_ocr``: GLM-OCR's complete pipeline (PP-DocLayout-V3 layout, then
  GLM-OCR recognition of each region) on z.ai or a self-hosted glmocr server
  (``learnloop.ingest.extractors.glm_ocr``). Hosted runs send the whole file
  and need the learner's whole-file OK.
- ``auto``: GLM-OCR when it can run (hosted only with the OK), then marker,
  then pypdf; a GLM-OCR failure falls back the same way.

Marker conversion is model inference and slow (seconds to minutes per
chapter), so results are cached in ``cache_dir`` keyed by the PDF bytes and
the extraction configuration (secrets excluded). Marker runs in a worker
process of its own (``learnloop.ingest.extractors.marker_worker``: pdfium is
not thread-safe, and the Reader renders with it in the sidecar's process),
which loads its models for each conversion. Page images extracted by marker
are dropped: canonical sources are Markdown-only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from learnloop.config import PdfIngestConfig
from learnloop.ingest.extractors.glm_ocr import GlmOcrConsentRequired, GlmOcrExtractionError


class PdfExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class PdfExtraction:
    markdown: str
    engine: str  # "glm_ocr" | "marker" | "pypdf"
    used_llm: bool = False
    from_cache: bool = False
    #: Why ``auto`` passed over GLM-OCR, or that GLM-OCR fell back; None otherwise.
    selection_reason: str | None = None


def extract_pdf_markdown(
    raw_bytes: bytes,
    *,
    config: PdfIngestConfig | None = None,
    cache_dir: Path | None = None,
    whole_file_upload_allowed: bool = False,
) -> PdfExtraction:
    """``whole_file_upload_allowed``: the learner's one-time whole-file OK.
    Hosted GLM-OCR runs only with it; without it ``auto`` reads locally and
    an explicit ``glm_ocr`` engine fails asking for it."""

    config = config or PdfIngestConfig()
    engine, reason = _resolve_engine(config, whole_file_upload_allowed=whole_file_upload_allowed)
    if engine == "glm_ocr":
        try:
            return _extract_with_glm_ocr(raw_bytes, config, cache_dir)
        except PdfExtractionError as exc:
            if config.engine != "auto" or isinstance(exc.__cause__, GlmOcrConsentRequired):
                raise
            engine = _local_engine(config)
            reason = f"glm_ocr_failed_{engine}_fallback"
    if engine == "pypdf":
        return replace(_extract_with_pypdf(raw_bytes), selection_reason=reason)
    options = _marker_options(config)
    cache_key = _cache_key(raw_bytes, options, _marker_cache_fingerprint())
    cached = _read_cache(cache_dir, cache_key)
    if cached is not None:
        return replace(cached, selection_reason=reason)
    extraction = _extract_with_marker(raw_bytes, config, options)
    _write_cache(cache_dir, cache_key, extraction)
    return replace(extraction, selection_reason=reason)


def _extract_with_glm_ocr(raw_bytes: bytes, config: PdfIngestConfig, cache_dir: Path | None) -> PdfExtraction:
    """GLM-OCR's IR rendered as Markdown, cached by file bytes and extractor
    version (backend, models, mapping); endpoint, timeout and price settings
    never change what is read."""

    from learnloop.ingest.extractors import ExtractionContext, pdf_extractor_for
    from learnloop.ingest.ir import render_ir_markdown

    extractor = pdf_extractor_for({"engine": "glm_ocr", "glm_ocr": config.glm_ocr.model_dump()})
    key = _cache_key(raw_bytes, {"engine": "glm_ocr"}, extractor.version())
    cached = _read_cache(cache_dir, key)
    if cached is not None:
        return cached
    try:
        ir = extractor.extract(
            raw_bytes, ExtractionContext(revision_id="legacy", config={"whole_file_upload_allowed": True})
        )
    except GlmOcrExtractionError as exc:
        raise PdfExtractionError(str(exc)) from exc
    markdown = render_ir_markdown(ir)
    if not markdown.strip():
        raise PdfExtractionError("GLM-OCR found no text in this document")
    extraction = PdfExtraction(markdown=markdown, engine="glm_ocr", selection_reason=extractor.selection_reason)
    _write_cache(cache_dir, key, extraction)
    return extraction


def _local_engine(config: PdfIngestConfig) -> str:
    return "marker" if importlib.util.find_spec("marker") is not None else "pypdf"


def _resolve_engine(config: PdfIngestConfig, *, whole_file_upload_allowed: bool = False) -> tuple[str, str | None]:
    """(engine, why it was chosen when ``auto`` passed over GLM-OCR)."""

    if config.engine == "native":
        # The chat-provider path lives in the durable import pipeline only;
        # this one-shot extractor has no model client, so degrading to a
        # local engine here would silently ignore an explicit choice.
        raise PdfExtractionError(
            'ingest.pdf.engine = "native" sends the PDF to the routed chat model and is only '
            "supported by the durable import pipeline (learnloop import / the desktop app); "
            'use "auto", "glm_ocr", "marker", or "pypdf" for this command'
        )
    if config.engine == "pypdf":
        return "pypdf", None
    reason = None
    if config.engine in {"auto", "glm_ocr"}:
        from learnloop.ingest.extractors.glm_ocr import CONSENT_MESSAGE, UNAVAILABLE_MESSAGE, selected_backend

        backend = selected_backend(config.glm_ocr.model_dump())
        if backend == "local" or (backend == "api" and whole_file_upload_allowed):
            return "glm_ocr", None
        if config.engine == "glm_ocr":
            raise PdfExtractionError(CONSENT_MESSAGE if backend == "api" else UNAVAILABLE_MESSAGE)
        reason = "glm_ocr_needs_upload_ok" if backend == "api" else "glm_ocr_unavailable"
    marker_available = importlib.util.find_spec("marker") is not None
    if config.engine == "marker" and not marker_available:
        raise PdfExtractionError(
            "marker-pdf is required when ingest.pdf.engine = \"marker\"; install it "
            "with 'pip install learnloop[pdf]' or set the engine to \"auto\"/\"pypdf\""
        )
    return ("marker" if marker_available else "pypdf"), reason


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
    # Marker runs in a worker process (pdfium is not thread-safe, and the
    # Reader renders with it in the sidecar's process; marker_worker). surya
    # reads TORCH_DEVICE when its settings module first loads: the worker
    # gets it in its environment, and this process's is left alone.
    from learnloop.ingest.extractors.marker_worker import MarkerWorkerError, run_marker

    try:
        text = run_marker("markdown", raw_bytes, options, torch_device=config.torch_device)
    except MarkerWorkerError as exc:
        raise PdfExtractionError(f"marker failed to convert PDF: {exc}") from exc
    markdown = (text or "").strip()
    if not markdown:
        raise PdfExtractionError("PDF produced no extractable content")
    return PdfExtraction(markdown=markdown + "\n", engine="marker", used_llm=bool(config.use_llm))


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
