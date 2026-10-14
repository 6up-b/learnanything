"""GLM-OCR's complete layout-and-recognition pipeline as a DocumentExtractor.

Both backends run the whole two-stage pipeline (PP-DocLayout-V3 finds the
regions, the 0.9B GLM-OCR model recognises them in parallel), never the bare
recognition model:

- ``api``: z.ai's hosted ``POST /api/paas/v4/layout_parsing`` (Zhipu's
  open.bigmodel.cn serves the same endpoint). The whole file goes out, so the
  durable import asks for the learner's one-time whole-file OK first and a
  book kept on this computer never uses it.
- ``local``: the open-source ``glmocr`` SDK's server (``python -m
  glmocr.server``, ``POST /glmocr/parse``) running its own layout model next to
  a vLLM / SGLang / Ollama recognition server. LearnLoop renders the selected
  PDF pages to PNG (pypdfium2) because that server reads PDFs only from its own
  filesystem.

No SDK is imported: both backends are plain HTTP (stdlib ``urllib``, like the
Datalab adapter). Response shapes were taken from the glmocr 0.1.5 SDK source:
hosted regions carry ``bbox_2d`` in absolute pixels of the provider's own page
rendering, and the SDK scales them by ``data_info.pages`` only (a region's own
``width``/``height`` is a last resort here, when ``data_info`` has no size for
the page); the self-hosted server normalises ``bbox_2d`` to 0-1000 and, for
several input images, returns one ``[[regions]]`` list per image.
Both are mapped to the coordinates the Reader's PDF view uses: PDF points,
top-left origin, the page's crop box after rotation. API page ids are
one-based; IR pages stay zero-based like every other extractor. No remote
image (crop URL) is ever fetched.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import io
import ipaddress
import json
import math
import os
import re
import socket
import time
from html import escape
from html.parser import HTMLParser
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from learnloop.ai.execution import model_call
from learnloop.ingest.block_roles import classify_block_role
from learnloop.ingest.extractors.base import ExtractionContext, units_from_toc_entries
from learnloop.ingest.extractors.pypdf import read_embedded_outline
from learnloop.ingest.hashing import semantic_hash
from learnloop.ingest.ir import (
    IR_SCHEMA_VERSION,
    DocumentBlock,
    DocumentIR,
    DocumentUnit,
    PageHealth,
)

EXTRACTOR_NAME = "glm_ocr"
API_URL = "https://api.z.ai/api/paas/v4/layout_parsing"
LOCAL_URL = "http://127.0.0.1:5002/glmocr/parse"
# The hosted service's documented limits.
PDF_LIMIT = 50 * 1024 * 1024
IMAGE_LIMIT = 10 * 1024 * 1024
MAX_PAGES_PER_REQUEST = 30
# Planning heuristic for previews and request admission, input plus output
# combined; not a provider limit and not a money cap. A dense page is a page
# image (~1-2k tokens per region crop) plus its recognised text.
ESTIMATED_TOKENS_PER_PAGE = 6000
# Page images sent to the self-hosted server: 2x PDF points = 144 dpi.
LOCAL_RENDER_SCALE = 2.0
# Mapping version, part of version() and so of every extraction request hash.
MAP_VERSION = 1
LAYOUT_MODEL = "PP-DocLayout-V3"
RECOGNITION_MODEL = "glm-ocr-0.9B"
UNAVAILABLE_MESSAGE = "Text recognition needs a z.ai API key or a running local GLM-OCR service."
CONSENT_MESSAGE = "Reading this document sends the whole file to z.ai (GLM-OCR). Say OK once to allow that."
KEY_ENV_ALIASES = ("ZAI_API_KEY", "ZHIPU_API_KEY", "ZHIPUAI_API_KEY")
_MAX_ATTEMPTS = 3
_MAX_RETRY_AFTER_SECONDS = 30.0


class GlmOcrExtractionError(RuntimeError):
    """GLM-OCR could not read the document (transport, provider or shape)."""


class GlmOcrConsentRequired(GlmOcrExtractionError):
    """A hosted run was attempted without the whole-file OK."""


# -- selection -----------------------------------------------------------------


def glm_api_key(config: dict | None = None) -> str:
    """The z.ai key from the environment the app loaded (shell, vault .env,
    machine settings.env): the configured variable first, then the aliases."""

    configured = str((config or {}).get("api_key_env") or KEY_ENV_ALIASES[0])
    for name in (configured, *KEY_ENV_ALIASES):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def is_loopback_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").strip().lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


_PROBES: dict[str, tuple[float, bool]] = {}
_PROBE_TTL_SECONDS = 5.0


def local_available(config: dict | None = None) -> bool:
    """Whether the self-hosted server accepts connections: a TCP connect only,
    no upload and no inference. Cached briefly so a library listing that asks
    for every card does not probe once per card."""

    url = str((config or {}).get("local_url") or LOCAL_URL)
    now = time.monotonic()
    cached = _PROBES.get(url)
    if cached is not None and now - cached[0] < _PROBE_TTL_SECONDS:
        return cached[1]
    parsed = urlparse(url)
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((parsed.hostname or "127.0.0.1", port), timeout=0.25):
            reachable = True
    except (OSError, ValueError):
        reachable = False
    _PROBES[url] = (now, reachable)
    return reachable


def selected_backend(
    config: dict | None = None, *, keep_local: bool = False, probe: bool = True
) -> str | None:
    """Which GLM-OCR backend can run now, or None.

    ``backend = "auto"`` (the default) and ``"api"`` use z.ai when a key is
    set; ``"local"`` uses the self-hosted server when it answers (``probe``;
    without probing, a configured local backend counts). A book kept on this
    computer never uses z.ai, and uses a local server only on this computer
    (a loopback ``local_url``)."""

    config = config or {}
    backend = str(config.get("backend") or "auto")
    if backend in {"auto", "api"}:
        if keep_local or not glm_api_key(config):
            return None
        return "api"
    if backend == "local":
        if keep_local and not is_loopback_url(str(config.get("local_url") or LOCAL_URL)):
            return None
        if not probe or local_available(config):
            return "local"
    return None


def estimate(pages: int | None, config: dict | None = None, *, backend: str = "api") -> dict[str, Any]:
    """A planning estimate for previews: pages x ESTIMATED_TOKENS_PER_PAGE at
    the configured price (local runs cost nothing). ``pages`` None: unknown
    until a remote file is downloaded."""

    price = float((config or {}).get("price_per_million_tokens", 0.03))
    if pages is None:
        return {"pages": None, "total_tokens": None, "estimated_usd": None,
                "tokens_per_page": ESTIMATED_TOKENS_PER_PAGE, "backend": backend,
                "basis": "page count unknown until the file is downloaded"}
    tokens = max(int(pages), 0) * ESTIMATED_TOKENS_PER_PAGE
    usd = 0.0 if backend == "local" else tokens * price / 1_000_000
    return {"pages": int(pages), "total_tokens": tokens, "estimated_usd": usd,
            "tokens_per_page": ESTIMATED_TOKENS_PER_PAGE, "backend": backend,
            "basis": "estimated input plus output tokens per page"}


# -- transport -----------------------------------------------------------------


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the Authorization header or a whole document elsewhere.
        return None


def _open(request: Request, timeout: float):
    return build_opener(_NoRedirect).open(request, timeout=timeout)


def _provider_error(exc: HTTPError, secret: str) -> str:
    """The provider's own error code/message, short and without the key.
    The request body (the document) is never part of an error response."""

    try:
        body = exc.read(4096)
    except Exception:
        body = b""
    detail = ""
    try:
        payload = json.loads(body or b"{}")
        if isinstance(payload, dict):
            error = payload.get("error") if isinstance(payload.get("error"), dict) else payload
            code = error.get("code")
            message = error.get("message") or error.get("msg")
            detail = " ".join(str(part) for part in (code, message) if part not in (None, ""))
    except (ValueError, TypeError):
        detail = ""
    detail = " ".join(detail.split())[:200]
    if secret:
        detail = detail.replace(secret, "[key]")
    return detail


def _retry_after(exc: HTTPError, attempt: int) -> float:
    header = exc.headers.get("Retry-After") if exc.headers is not None else None
    try:
        if header is not None:
            return max(0.0, min(float(header), _MAX_RETRY_AFTER_SECONDS))
    except ValueError:
        pass
    return float(2**attempt)


# -- extractor -----------------------------------------------------------------


class GlmOcrDocumentExtractor:
    name = EXTRACTOR_NAME

    def __init__(self, *, config: dict[str, Any] | None = None, backend: str | None = None):
        from learnloop.config.schema import GlmOcrConfig

        self.config = GlmOcrConfig(**(config or {})).model_dump()
        self.backend = backend or selected_backend(self.config)
        if self.backend not in {"api", "local"}:
            raise GlmOcrExtractionError(UNAVAILABLE_MESSAGE)
        # What model_call records on every receipt (provider/model/endpoint).
        self.provider_name = "zai-glm-ocr" if self.backend == "api" else "glm-ocr-local"
        self.provider_type = "glm_ocr"
        self.model = "glm-ocr"
        self.default_base_url = str(self.config["api_url" if self.backend == "api" else "local_url"])
        self.profile = SimpleNamespace(base_url=self.default_base_url, model=self.model)
        self.selection_reason = f"glm_ocr_{self.backend}_selected"

    def version(self) -> str:
        return f"{RECOGNITION_MODEL}+{LAYOUT_MODEL}+{self.backend}+map{MAP_VERSION}"

    def model_versions(self) -> dict[str, str]:
        return {"backend": self.backend, "recognition": RECOGNITION_MODEL, "layout": LAYOUT_MODEL}

    def leaves_this_computer(self) -> bool:
        """Whether reading sends the document off this computer: always for
        z.ai, and for a self-hosted server not on a loopback address."""

        return self.backend == "api" or not is_loopback_url(self.default_base_url)

    def extract(self, raw_bytes: bytes, context: ExtractionContext) -> DocumentIR:
        if self.backend == "api" and not context.config.get("whole_file_upload_allowed"):
            raise GlmOcrConsentRequired(CONSENT_MESSAGE)
        mime = _mime(raw_bytes)
        reader = None
        sizes: list[tuple[float, float]]
        if mime == "application/pdf":
            reader, sizes = _pdf_pages(raw_bytes)
        else:
            if self.backend == "api" and len(raw_bytes) > IMAGE_LIMIT:
                raise GlmOcrExtractionError("Hosted GLM-OCR reads images of at most 10 MB")
            sizes = [_image_size(raw_bytes)]
        pages = sorted(set(context.page_selection if context.page_selection is not None else range(len(sizes))))
        if not pages or any(page < 0 or page >= len(sizes) for page in pages):
            raise GlmOcrExtractionError("Invalid document page selection")
        limit = min(int(self.config["max_pages_per_request"]), MAX_PAGES_PER_REQUEST)
        windows: list[list[int]] = []
        for page in pages:
            if not windows or page != windows[-1][-1] + 1 or len(windows[-1]) >= limit:
                windows.append([])
            windows[-1].append(page)
        # Paid answers are checkpointed per window (by the file's bytes and the
        # pages), so a failure part-way, or reading it again, pays only for
        # the windows not yet answered. Local runs cost nothing to repeat.
        asset = hashlib.sha256(raw_bytes).hexdigest() if self.backend == "api" and context.checkpoints else None
        results: list[tuple[dict, list[int]]] = []
        for window in windows:
            results.extend(
                self._window(raw_bytes, mime, reader, window, total_pages=len(sizes), context=context, asset=asset)
            )
        outline = read_embedded_outline(raw_bytes) if reader is not None else []
        try:
            ir = responses_to_ir(results, sizes=sizes, outline=outline, version=self.version())
        except GlmOcrExtractionError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
            raise GlmOcrExtractionError(
                f"GLM-OCR returned layout details LearnLoop can't read ({type(exc).__name__})"
            ) from None
        ir.health.flags.append(self.selection_reason)
        return ir

    # One request per window; a window too big for the hosted file limit splits.
    def _window(
        self, raw: bytes, mime: str, reader: Any, pages: list[int], *, total_pages: int,
        context: ExtractionContext, asset: str | None = None,
    ) -> list[tuple[dict, list[int]]]:
        key = self._checkpoint_key(asset, pages) if asset else None
        saved = context.checkpoints.load(key) if key else None
        if isinstance(saved, dict):
            try:
                _validated(saved, pages)
                return [(saved, pages)]
            except GlmOcrExtractionError:
                pass  # an answer this mapping can't read is asked for again
        if self.backend == "local":
            images = _render_pages(raw, pages) if reader is not None else [_data_uri(mime, raw)]
            return [(self._answer({"images": images}, pages, context), pages)]
        body = raw
        page_range: tuple[int, int] | None = None
        if reader is not None:
            whole = len(pages) == total_pages
            body = raw if whole and len(raw) <= PDF_LIMIT else _pdf_subset(reader, pages)
            if len(body) > PDF_LIMIT:
                if len(pages) == 1:
                    raise GlmOcrExtractionError("A single PDF page is larger than GLM-OCR's 50 MB limit")
                middle = len(pages) // 2
                return self._window(
                    raw, mime, reader, pages[:middle], total_pages=total_pages, context=context, asset=asset
                ) + self._window(
                    raw, mime, reader, pages[middle:], total_pages=total_pages, context=context, asset=asset
                )
            page_range = (1, len(pages))
        encoded = base64.b64encode(body).decode("ascii")
        payload: dict[str, Any] = {
            "model": "glm-ocr",
            "file": encoded if self.config["base64_style"] == "raw" else f"data:{mime};base64,{encoded}",
            "return_crop_images": False,
            "need_layout_visualization": False,
            "request_id": uuid4().hex,
        }
        if page_range is not None:
            payload["start_page_id"], payload["end_page_id"] = page_range
        result = self._answer(payload, pages, context)
        if key:
            context.checkpoints.save(key, result)
        return [(result, pages)]

    def _answer(self, payload: dict, pages: list[int], context: ExtractionContext) -> dict:
        """One window's answer, read before the next window is paid for: a
        layout LearnLoop can't read stops the run here, not after the book."""

        result = self._request(payload, len(pages), interrupt=context.interrupt)
        _validated(result, pages)
        return result

    def _checkpoint_key(self, asset: str, pages: list[int]) -> str:
        # What decides the answer: the file, the pages, the backend and its
        # models. Endpoint, timeout, price and the mapping never do.
        identity = {"purpose": "glm_ocr_window", "asset_sha256": asset, "pages": list(pages),
                    "backend": self.backend, "recognition": RECOGNITION_MODEL, "layout": LAYOUT_MODEL}
        return "glm_ocr_window:" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()

    def _endpoint(self) -> str:
        url = self.default_base_url.strip().rstrip("/")
        if self.backend == "api" and not url.endswith("/layout_parsing"):
            url += "/layout_parsing"
        parsed = urlparse(url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.scheme not in {"http", "https"}:
            raise GlmOcrExtractionError("The GLM-OCR address is not a plain http(s) URL")
        if self.backend == "api" and parsed.scheme != "https":
            raise GlmOcrExtractionError("Hosted GLM-OCR needs an https address")
        return url

    def _request(self, payload: dict, page_count: int, *, interrupt=None) -> dict:
        from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate

        url = self._endpoint()
        headers = {"Content-Type": "application/json"}
        key = ""
        if self.backend == "api":
            key = glm_api_key(self.config)
            if not key:
                raise GlmOcrExtractionError("The z.ai API key is not set")
            headers["Authorization"] = f"Bearer {key}"
        data = json.dumps(payload).encode("utf-8")
        tokens = max(page_count * ESTIMATED_TOKENS_PER_PAGE, 1)
        usd = estimate(page_count, self.config, backend=self.backend)["estimated_usd"]
        timed_out = False
        for attempt in range(_MAX_ATTEMPTS):
            wait: float | None = None
            if interrupt is not None:
                # Before every request, retries too: a cancellation or a book
                # now kept on this computer stops what has not been sent.
                interrupt()
            # One admission and one receipt per physical request. No money cap
            # of its own (owner policy). A shared spend envelope or metered
            # request gate in force around the call would also apply; the
            # import jobs that run GLM-OCR today install neither.
            budget = SpendBudget(SpendCaps(max_estimated_usd=None, max_total_tokens=tokens))
            with budget.request(SpendEstimate(calls=1, total_tokens=tokens, estimated_usd=usd)) as charge:
                with model_call(self, purpose="document_layout_recognition", budget=tokens) as receipt:
                    receipt.update(page_count=page_count, estimated_tokens=tokens)
                    try:
                        started = time.monotonic()
                        with _open(Request(url, data=data, headers=headers, method="POST"),
                                   float(self.config["request_timeout_seconds"])) as response:
                            result = json.loads(response.read())
                        receipt["latency_ms"] = int((time.monotonic() - started) * 1000)
                        if not isinstance(result, dict):
                            raise GlmOcrExtractionError("GLM-OCR returned an unexpected JSON shape")
                        self._record_usage(receipt, result, page_count)
                        code = result.get("code")
                        if result.get("error") or code not in (None, 0, "0", 200, "200"):
                            error = result.get("error") if isinstance(result.get("error"), dict) else result
                            parts = (error.get("code"), error.get("message") or error.get("msg"))
                            detail = " ".join(str(part) for part in parts if part not in (None, "")) or "unknown"
                            detail = " ".join(detail.split())[:200]
                            raise GlmOcrExtractionError(
                                "GLM-OCR reported an error: " + (detail.replace(key, "[key]") if key else detail)
                            )
                    except HTTPError as exc:
                        detail = _provider_error(exc, key)
                        retryable = exc.code == 429 or 500 <= exc.code < 600
                        if retryable and attempt + 1 < _MAX_ATTEMPTS:
                            wait = _retry_after(exc, attempt)
                        exc.close()
                        receipt.update(status="failed", error_type="HTTPError", http_status=exc.code)
                        if wait is None:
                            suffix = f": {detail}" if detail else ""
                            raise GlmOcrExtractionError(f"GLM-OCR HTTP {exc.code}{suffix}") from None
                    except (URLError, TimeoutError, OSError) as exc:
                        reason = getattr(exc, "reason", exc)
                        if not isinstance(reason, TimeoutError):
                            raise GlmOcrExtractionError("Could not reach GLM-OCR") from None
                        receipt.update(status="failed", error_type="TimeoutError")
                        if timed_out or attempt + 1 >= _MAX_ATTEMPTS:
                            raise GlmOcrExtractionError("GLM-OCR did not answer in time") from None
                        # A slow window is asked once more (a long scanned
                        # window can outlast one wait), then it fails.
                        timed_out, wait = True, 0.0
                    except http.client.HTTPException:
                        # IncompleteRead, BadStatusLine, LineTooLong: not OSErrors.
                        raise GlmOcrExtractionError("GLM-OCR's answer was cut off") from None
                    except (ValueError, TypeError):
                        raise GlmOcrExtractionError("GLM-OCR returned invalid JSON or usage") from None
                    finally:
                        charge.reconcile(
                            total_tokens=int(receipt.get("total_tokens") or 0) or None,
                            estimated_usd=receipt.get("cost"),
                        )
            if wait is None:
                return result
            time.sleep(wait)
        raise GlmOcrExtractionError("GLM-OCR retry limit reached")  # pragma: no cover - loop returns or raises

    def _record_usage(self, receipt: dict, result: dict, page_count: int) -> None:
        receipt["provider_response_id"] = result.get("id") or result.get("request_id")
        receipt["resolved_model"] = result.get("model") or self.model
        receipt["response_keys"] = sorted(str(key) for key in result)
        usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
        if self.backend == "local":
            receipt.update(input_tokens=0, output_tokens=0, cost=0.0, cost_basis="self_hosted")
        elif usage:
            prompt = max(0, int(usage.get("prompt_tokens") or 0))
            completion = max(0, int(usage.get("completion_tokens") or 0))
            total = max(prompt + completion, int(usage.get("total_tokens") or 0))
            cached = int((usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
            receipt.update(
                input_tokens=prompt, output_tokens=completion, cached_input_tokens=cached, total_tokens=total,
                cost=total * float(self.config["price_per_million_tokens"]) / 1_000_000,
                cost_basis="reported_usage",
            )
        else:
            receipt.update(cost=estimate(page_count, self.config)["estimated_usd"], cost_basis="estimated_usage_missing")
        receipt["usage_json"] = json.dumps({
            "pages": page_count,
            "estimated_tokens": page_count * ESTIMATED_TOKENS_PER_PAGE,
            "total_tokens": receipt.get("total_tokens"),
            "cost_basis": receipt.get("cost_basis"),
            "latency_ms": receipt.get("latency_ms"),
            "response_keys": receipt["response_keys"],
        }, sort_keys=True)


# -- document helpers ------------------------------------------------------------


def _mime(raw: bytes) -> str:
    if raw.startswith(b"%PDF-"):
        return "application/pdf"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    raise GlmOcrExtractionError("GLM-OCR reads PDF, PNG and JPG documents")


def is_glm_document(raw: bytes) -> bool:
    try:
        _mime(raw)
    except GlmOcrExtractionError:
        return False
    return True


def is_image_document(raw: bytes) -> bool:
    return is_glm_document(raw) and not raw.startswith(b"%PDF-")


def _data_uri(mime: str, raw: bytes) -> str:
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def _pdf_pages(raw: bytes) -> tuple[Any, list[tuple[float, float]]]:
    """The reader and each page's displayed size in PDF points (crop box,
    width and height swapped for a quarter-turn rotation): the space the
    Reader's PDF view (pdfium's page size) draws block boxes in."""

    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            reader.decrypt("")
        sizes = []
        for page in reader.pages:
            width, height = float(page.cropbox.width), float(page.cropbox.height)
            if (page.rotation or 0) % 180:
                width, height = height, width
            sizes.append((width, height))
    except Exception as exc:
        raise GlmOcrExtractionError("Could not read the PDF's pages") from exc
    if not sizes:
        raise GlmOcrExtractionError("The PDF has no pages")
    return reader, sizes


def _image_size(raw: bytes) -> tuple[float, float]:
    from PIL import Image

    try:
        with Image.open(io.BytesIO(raw)) as image:
            return float(image.size[0]), float(image.size[1])
    except Exception as exc:
        raise GlmOcrExtractionError("Could not read the image") from exc


def _pdf_subset(reader: Any, pages: list[int]) -> bytes:
    from pypdf import PdfWriter

    try:
        writer = PdfWriter()
        for page in pages:
            writer.add_page(reader.pages[page])
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except Exception as exc:
        raise GlmOcrExtractionError("Could not split the PDF into page windows") from exc


def _render_pages(raw: bytes, pages: list[int]) -> list[str]:
    """PNG data URIs of the selected pages for the self-hosted server."""

    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise GlmOcrExtractionError(
            "Local GLM-OCR needs pypdfium2 to show it PDF pages (uv sync --extra glm-ocr)"
        ) from None
    # pdfium's own errors (PdfiumError) are failures to read the document, so
    # under "auto" they fall back like any other GLM-OCR failure.
    try:
        document = pdfium.PdfDocument(raw)
    except Exception as exc:  # noqa: BLE001
        raise GlmOcrExtractionError("Could not render the PDF's pages for local GLM-OCR") from exc
    images: list[str] = []
    try:
        for index in pages:
            page = document[index]
            try:
                bitmap = page.render(scale=LOCAL_RENDER_SCALE)
                try:
                    out = io.BytesIO()
                    bitmap.to_pil().save(out, format="PNG")
                finally:
                    bitmap.close()
            finally:
                page.close()
            images.append(_data_uri("image/png", out.getvalue()))
    except Exception as exc:  # noqa: BLE001
        raise GlmOcrExtractionError("Could not render the PDF's pages for local GLM-OCR") from exc
    finally:
        document.close()
    return images


# -- response normalisation --------------------------------------------------------


def _layout_value(result: dict) -> Any:
    for key in ("layout_details", "json_result", "data"):
        if key in result and result[key] is not None:
            value = result[key]
            break
    else:
        raise GlmOcrExtractionError("GLM-OCR returned no layout details")
    if isinstance(value, str):
        value = json.loads(value)
    if isinstance(value, dict):
        for key in ("layout_details", "pages", "layout", "results"):
            if key in value:
                return value[key]
        raise GlmOcrExtractionError("GLM-OCR returned no layout details")
    return value


def _is_region(value: Any) -> bool:
    return isinstance(value, dict)


def _page_regions(result: dict, count: int, page_ids: list[int] | None = None) -> tuple[list[list[dict]], str]:
    """Per-page region lists for one request's ``count`` pages, and the name
    of the response shape seen (kept in extraction health). ``page_ids``: the
    document pages the request covered, for flat regions that carry absolute
    page numbers."""

    value = _layout_value(result)
    if not isinstance(value, list):
        raise GlmOcrExtractionError("GLM-OCR returned no supported layout details")
    if value and all(isinstance(unit, list) for unit in value) and any(
        isinstance(page, list) for unit in value for page in unit
    ):
        # The self-hosted server, several images: one [[regions]] per image.
        pages = [page for unit in value for page in unit]
        shape = "units"
    elif value and isinstance(value[0], dict) and any(
        key in value[0] for key in ("blocks", "regions", "layout_details", "layout")
    ):
        pages = [
            page.get("blocks", page.get("regions", page.get("layout_details", page.get("layout", []))))
            for page in value
        ]
        shape = "page_objects"
    elif value and isinstance(value[0], dict):
        # The older flat shape: one list of regions tagged with their page.
        pages = [[] for _ in range(count)]
        if count > 1 and not all(any(k in region for k in ("page", "page_id", "page_index")) for region in value):
            raise GlmOcrExtractionError("GLM-OCR's flat regions carry no page numbers")
        zero_based = any(region.get("page_index") is not None for region in value) or any(
            region.get("page_id", region.get("page")) == 0 for region in value
        )
        for region in value:
            raw_page = region.get("page_index", region.get("page_id", region.get("page", 0 if zero_based else 1)))
            index = int(raw_page) - (0 if zero_based else 1)
            if not 0 <= index < count and page_ids and index in page_ids:
                index = page_ids.index(index)
            if not 0 <= index < count:
                raise GlmOcrExtractionError("GLM-OCR returned an invalid page number")
            pages[index].append(region)
        shape = "flat"
    else:
        pages = value
        shape = "nested"
    if len(pages) != count or any(not isinstance(page, list) for page in pages):
        raise GlmOcrExtractionError(
            f"GLM-OCR returned {len(pages)} page(s) for a request of {count}"
        )
    if any(not _is_region(region) for page in pages for region in page):
        raise GlmOcrExtractionError("GLM-OCR returned regions LearnLoop can't read")
    return pages, shape


def _validated(result: dict, pages: list[int]) -> None:
    """Raise unless ``result`` holds a readable layout for exactly ``pages``."""

    try:
        _page_regions(result, len(pages), pages)
    except GlmOcrExtractionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        raise GlmOcrExtractionError(
            f"GLM-OCR returned layout details LearnLoop can't read ({type(exc).__name__})"
        ) from None


def _page_dimensions(result: dict) -> list[dict]:
    pages = (result.get("data_info") or {}).get("pages") if isinstance(result.get("data_info"), dict) else None
    return [page if isinstance(page, dict) else {} for page in pages] if isinstance(pages, list) else []


def _bbox(region: dict, target: tuple[float, float], page: dict) -> list[float] | None:
    """Region box -> PDF points (or image pixels), top-left origin.

    Declared spaces win (``coordinate_system``/``bbox_format``: ``0-1``,
    ``0-1000``, ``pixels``). Otherwise: all values <= 1 are fractions; a box
    with a known page pixel size is in pixels; else 0-1000 (the self-hosted
    SDK). The page size is ``data_info.pages`` (the only size the SDK scales
    hosted boxes by); a region's own ``width``/``height`` serves only when
    that is missing, since it may be the region's size, not the page's."""

    raw = region.get("bbox_2d", region.get("bbox"))
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        values = [float(value) for value in raw]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in values):
        return None
    width = _positive(page.get("width")) or _positive(region.get("width"))
    height = _positive(page.get("height")) or _positive(region.get("height"))
    space = str(region.get("coordinate_system") or region.get("bbox_format") or "").lower()
    if space in {"0-1", "normalized", "normalised", "relative"}:
        scale = (1.0, 1.0)
    elif space in {"0-1000", "normalized_1000", "normalised_1000"}:
        scale = (1000.0, 1000.0)
    elif space in {"pixel", "pixels", "absolute"} and width and height:
        scale = (width, height)
    elif space:
        return None
    elif max(values) <= 1.0:
        scale = (1.0, 1.0)
    elif width and height:
        scale = (width, height)
    elif max(values) <= 1000.0:
        scale = (1000.0, 1000.0)
    else:
        return None
    x0, y0, x1, y1 = (
        max(0.0, min(value / scale[index % 2], 1.0)) * target[index % 2] for index, value in enumerate(values)
    )
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    return [round(left, 2), round(top, 2), round(right, 2), round(bottom, 2)]


def _positive(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


# Region labels -> IR block types. The hosted service and the SDK report a
# coarse ``label`` (text/table/formula/image) and, from the layout model, a
# ``native_label`` (doc_title, paragraph_title, figure_title, ...).
_TITLE_LEVELS = {"doc_title": 1, "title": 1, "paragraph_title": 2, "heading": 2, "sectionheader": 2,
                 "section_header": 2}
_BLOCK_TYPES = {
    "formula": "Equation", "display_formula": "Equation", "inline_formula": "Equation", "equation": "Equation",
    "table": "Table",
    "image": "Figure", "figure": "Figure", "chart": "Figure", "picture": "Figure",
    "header": "PageHeader", "page_header": "PageHeader", "pageheader": "PageHeader",
    "footer": "PageFooter", "page_footer": "PageFooter", "pagefooter": "PageFooter",
    "number": "PageNumber", "page_number": "PageNumber", "pagenumber": "PageNumber",
    "footnote": "Footnote", "vision_footnote": "Footnote",
    "figure_title": "Caption", "caption": "Caption", "table_title": "Caption", "chart_title": "Caption",
    "algorithm": "Code", "code": "Code",
}
_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(\S.*)$")
_MARKDOWN_IMAGE = re.compile(r"^!\[[^\]]*\]\([^)]*\)$")


def _labels(region: dict) -> tuple[str, str]:
    label = str(region.get("label") or region.get("type") or "text").strip().lower()
    native = str(region.get("native_label") or region.get("sub_label") or "").strip().lower()
    return label, native


def _block_type_and_heading(region: dict, text: str) -> tuple[str, int | None, str]:
    """(IR block type, heading level or None, text) for one region."""

    label, native = _labels(region)
    for name in (native, label):
        if name in _TITLE_LEVELS:
            match = _MARKDOWN_HEADING.match(text) if "\n" not in text else None
            level = len(match[1]) if match else int(region.get("level") or _TITLE_LEVELS[name])
            return "SectionHeader", max(1, min(level, 6)), (match[2].strip() if match else text.lstrip("# ").strip())
    block_type = _BLOCK_TYPES.get(native) or _BLOCK_TYPES.get(label) or "Text"
    if block_type == "Text" and "\n" not in text:
        match = _MARKDOWN_HEADING.match(text)
        if match:
            return "SectionHeader", len(match[1]), match[2].strip()
    return block_type, None, text


def _equation_text(text: str) -> str:
    stripped = text.strip()
    if not stripped or stripped.startswith(("$", "\\[", "\\begin{")):
        return stripped
    if stripped.startswith("\\(") and stripped.endswith("\\)"):
        stripped = stripped[2:-2].strip()
    return f"$${stripped}$$"


def _table_cells(cells: Any) -> str:
    """The older flat shape's table cells, as HTML for the Markdown converter."""

    if not isinstance(cells, list):
        raise GlmOcrExtractionError("GLM-OCR returned table cells LearnLoop can't read")
    if cells and isinstance(cells[0], dict):
        rows: dict[int, dict[int, str]] = {}
        for cell in cells:
            row = int(cell.get("row", cell.get("row_index", 0)))
            column = int(cell.get("col", cell.get("column", cell.get("col_index", 0))))
            rows.setdefault(row, {})[column] = str(cell.get("text", cell.get("content", "")))
        cells = [[row[column] for column in sorted(row)] for _, row in sorted(rows.items())]
    return "<table>" + "".join(
        "<tr>" + "".join("<td>" + escape(str(cell)) + "</td>" for cell in row) + "</tr>"
        for row in cells if isinstance(row, list)
    ) + "</table>"


_STRAY_LT = re.compile(
    r"<(?!/?(?:table|thead|tbody|tfoot|tr|th|td|br|caption|colgroup|col|b|i|u|em|strong|sup|sub|span|p|div)"
    r"(?=[\s>/]))",
    re.IGNORECASE,
)


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[tuple[str, int, int]]] = []
        self.parts: list[str] | None = None
        self.spans = (1, 1)

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.rows.append([])
        elif tag in {"th", "td"}:
            if not self.rows:
                self.rows.append([])
            self.parts = []
            values = dict(attrs)

            def span(name: str) -> int:
                try:
                    return max(1, min(64, int(values.get(name) or 1)))
                except ValueError:
                    return 1

            self.spans = (span("rowspan"), span("colspan"))
        elif tag == "br" and self.parts is not None:
            self.parts.append(" ")

    def handle_data(self, data):
        if self.parts is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self.parts is not None:
            self.rows[-1].append(("".join(self.parts).strip(), *self.spans))
            self.parts = None


def _table_markdown(text: str) -> str:
    """HTML tables -> GFM: the Reader renders GFM tables but never raw HTML.
    Row and column spans repeat their cell; text outside a table is kept."""

    if not re.search(r"<table\b", text, re.IGNORECASE):
        return text
    parser = _TableParser()
    # A "<" that opens no tag (LaTeX "$a<b$" in a cell) is text, not markup.
    parser.feed(_STRAY_LT.sub("&lt;", text))
    parser.close()
    grid: dict[tuple[int, int], str] = {}
    for row, cells in enumerate(parser.rows):
        column = 0
        for content, rowspan, colspan in cells:
            while (row, column) in grid:
                column += 1
            for dr in range(rowspan):
                for dc in range(colspan):
                    grid[row + dr, column + dc] = content
            column += colspan
    if not grid:
        return re.sub(r"<[^>]+>", " ", text).strip()
    height = max(r for r, _ in grid) + 1
    width = max(c for _, c in grid) + 1

    def cell_text(value: str) -> str:
        # Angle brackets outside math stay visible text; LaTeX inside $...$
        # is left exactly as recognised.
        parts = re.split(r"(\$\$.*?\$\$|\$[^$]*\$)", value, flags=re.DOTALL)
        value = "".join(part if index % 2 else escape(part, quote=False) for index, part in enumerate(parts))
        return " ".join(value.replace("|", r"\|").split())

    rows = ["| " + " | ".join(cell_text(grid.get((r, c), "")) for c in range(width)) + " |" for r in range(height)]
    rows.insert(1, "| " + " | ".join(["---"] * width) + " |")
    return "\n".join(rows)


def _region_order(region: dict) -> tuple[int, int]:
    try:
        return (0, int(region.get("index", region.get("order", 0))))
    except (TypeError, ValueError):
        return (1, 0)


def responses_to_ir(
    results: list[tuple[dict, list[int]]],
    *,
    sizes: list[tuple[float, float]],
    outline: list[dict],
    version: str,
) -> DocumentIR:
    """Map GLM-OCR responses (each with the zero-based pages it covers) to the IR."""

    ir = DocumentIR(ir_schema_version=IR_SCHEMA_VERSION, extractor=EXTRACTOR_NAME, extractor_version=version)
    headings: list[dict[str, Any]] = []
    sections: list[str] = []
    for result, page_ids in results:
        page_regions, shape = _page_regions(result, len(page_ids), page_ids)
        flag = f"glm_ocr_response_{shape}"
        if flag not in ir.health.flags:
            ir.health.flags.append(flag)
        dimensions = _page_dimensions(result)
        for offset, (page, regions) in enumerate(zip(page_ids, page_regions)):
            dims = dimensions[offset] if offset < len(dimensions) else {}
            health = PageHealth(page=page, text_extraction_method=EXTRACTOR_NAME)
            ir.health.pages.append(health)
            if not regions:
                health.flags.append("no_detected_regions")
            for region in sorted(regions, key=_region_order):
                content = region.get("content", region.get("text"))
                text = str(content).strip() if content is not None else ""
                block_type, level, text = _block_type_and_heading(region, text)
                if block_type == "SectionHeader":
                    if not text:
                        continue
                    sections = sections[: level - 1] + [text]
                    headings.append({"title": text, "heading_level": level, "page_id": page,
                                     "ordinal": len(ir.blocks) + 1})
                elif block_type == "Equation":
                    text = _equation_text(text)
                elif block_type == "Table":
                    if not text and region.get("cells"):
                        text = _table_cells(region["cells"])
                    text = _table_markdown(text)
                elif block_type == "Figure":
                    # Hosted image regions carry a crop URL or a Markdown image
                    # reference, never prose: keep only a caption.
                    caption = str(region.get("caption") or "").strip()
                    if not caption and not (text.startswith(("http:", "https:", "data:")) or _MARKDOWN_IMAGE.match(text)):
                        caption = text
                    text = caption
                if not text and block_type != "Figure":
                    continue
                ordinal = len(ir.blocks) + 1
                index = region.get("index", ordinal - 1)
                ir.blocks.append(DocumentBlock.build(
                    span_id=f"s{ordinal}", ordinal=ordinal,
                    extractor_block_id=f"glm/page/{page}/region/{index}",
                    block_type=block_type,
                    role_hint=classify_block_role(block_type, sections, text),
                    page=page,
                    bbox=_bbox(region, sizes[page], dims),
                    section_path=sections,
                    text=text,
                ))
                health.block_counts[block_type] = health.block_counts.get(block_type, 0) + 1
    if not ir.blocks:
        raise GlmOcrExtractionError("GLM-OCR found no text in this document")
    units: list[DocumentUnit] = []
    if len(outline) >= 2:
        # An author's bookmarks beat detected headings; a lone bookmark is no
        # structure (as for Marker). drop_empty: a page-sliced import.
        units = units_from_toc_entries(outline, ir.blocks, locator_scheme="pdf_outline", drop_empty=True)
    ir.units = units or _heading_units(headings, ir.blocks)
    return ir


def _heading_units(headings: list[dict[str, Any]], blocks: list[DocumentBlock]) -> list[DocumentUnit]:
    """Units at detected headings, split by block (several headings can share
    a page); the text before the first heading belongs to the first unit."""

    if not headings:
        return units_from_toc_entries([], blocks, locator_scheme="detected_headings")
    units: list[DocumentUnit] = []
    parents: list[tuple[int, str]] = []
    for position, heading in enumerate(headings):
        start = 1 if position == 0 else heading["ordinal"]
        end = headings[position + 1]["ordinal"] if position + 1 < len(headings) else len(blocks) + 1
        selected = [block for block in blocks if start <= block.ordinal < end]
        level = int(heading["heading_level"])
        while parents and parents[-1][0] >= level:
            parents.pop()
        unit_id = f"u{position + 1}"
        pages = [block.page for block in selected if block.page is not None]
        units.append(DocumentUnit(
            unit_id=unit_id,
            parent_unit_id=parents[-1][1] if parents else None,
            label=str(heading["title"]),
            ordinal=position + 1,
            locator={"scheme": "detected_headings", "page": heading["page_id"], "heading_level": level},
            semantic_hash=semantic_hash(selected),
            page_start=min(pages) if pages else None,
            page_end=max(pages) if pages else None,
            span_ids=[block.span_id for block in selected],
        ))
        parents.append((level, unit_id))
    return units


__all__ = [
    "API_URL",
    "CONSENT_MESSAGE",
    "ESTIMATED_TOKENS_PER_PAGE",
    "GlmOcrConsentRequired",
    "GlmOcrDocumentExtractor",
    "GlmOcrExtractionError",
    "LOCAL_URL",
    "UNAVAILABLE_MESSAGE",
    "estimate",
    "glm_api_key",
    "is_glm_document",
    "is_image_document",
    "is_loopback_url",
    "local_available",
    "responses_to_ir",
    "selected_backend",
]
