"""Hosted Datalab Marker adapter for debug-time PDF extraction.

The adapter deliberately uses only the Python standard library so enabling the
hosted provider does not pull Marker's local GPU dependencies (or another HTTP
client) onto lightweight development machines.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from learnloop.ingest.extractors.base import ExtractionContext
from learnloop.ingest.extractors.marker import MarkerUnavailableError, chunk_output_to_ir

DATALAB_API_KEY_ENV = "DATALAB_API_KEY"
DATALAB_CONVERT_URL = "https://www.datalab.to/api/v1/convert"
EXTRACTOR_VERSION = "datalab-convert-v1+chunks-map3"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60
DEFAULT_POLL_TIMEOUT_SECONDS = 720


class DatalabExtractionError(RuntimeError):
    """Raised when the hosted conversion request cannot produce Marker chunks."""


def datalab_api_key() -> str:
    return os.environ.get(DATALAB_API_KEY_ENV, "").strip()


class DatalabDocumentExtractor:
    """Marker-compatible DocumentIR extraction backed by Datalab's cloud API."""

    # Keep the canonical provider name stable: downstream treats Marker as the
    # structured PDF engine, while version() distinguishes local and hosted runs.
    name = "marker"

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        self._config = dict(config or {})

    def version(self) -> str:
        return EXTRACTOR_VERSION

    def model_versions(self) -> dict[str, str]:
        return {"provider": "datalab-hosted"}

    def extract(self, raw_bytes: bytes, context: ExtractionContext):
        api_key = datalab_api_key()
        if not api_key:
            raise MarkerUnavailableError(
                f"Datalab Marker was requested but {DATALAB_API_KEY_ENV} is not set"
            )

        result = _convert_pdf(raw_bytes, api_key=api_key, context=context, config=self._config)
        chunks = result.get("chunks")
        if isinstance(chunks, str):
            try:
                chunks = json.loads(chunks)
            except json.JSONDecodeError as exc:
                raise DatalabExtractionError("Datalab returned invalid chunks JSON") from exc

        if isinstance(chunks, dict):
            blocks = chunks.get("blocks") or []
            chunk_metadata = chunks.get("metadata") or {}
            page_info = chunks.get("page_info") or {}
        elif isinstance(chunks, list):
            blocks = chunks
            chunk_metadata = {}
            page_info = {}
        else:
            blocks = []
            chunk_metadata = {}
            page_info = {}

        if not blocks:
            raise DatalabExtractionError("Datalab conversion completed without Marker chunks")

        from learnloop.ingest.extractors.pypdf import read_embedded_outline

        return chunk_output_to_ir(
            blocks=list(blocks),
            metadata=dict(result.get("metadata") or chunk_metadata),
            page_info=dict(page_info),
            extractor_version=self.version(),
            embedded_outline=read_embedded_outline(raw_bytes),
        )


def _convert_pdf(
    raw_bytes: bytes,
    *,
    api_key: str,
    context: ExtractionContext,
    config: dict[str, Any],
) -> dict[str, Any]:
    fields: dict[str, str] = {
        "output_format": "chunks",
        "mode": str(config.get("datalab_mode") or "balanced"),
    }
    pages = context.page_selection
    if pages is not None:
        fields["page_range"] = ",".join(str(page) for page in pages)
    elif config.get("page_range"):
        fields["page_range"] = str(config["page_range"])

    body, content_type = _multipart_body(fields, raw_bytes)
    headers = {"X-API-Key": api_key, "Content-Type": content_type}
    submitted = _request_json(Request(DATALAB_CONVERT_URL, data=body, headers=headers, method="POST"))
    if submitted.get("status") == "complete" or submitted.get("chunks"):
        return _validate_completed(submitted)

    check_url = str(submitted.get("request_check_url") or "").strip()
    if not check_url:
        request_id = str(submitted.get("request_id") or "").strip()
        if request_id:
            check_url = f"{DATALAB_CONVERT_URL}/{request_id}"
    _validate_check_url(check_url)

    deadline = time.monotonic() + _poll_timeout_seconds()
    while time.monotonic() < deadline:
        time.sleep(2)
        current = _request_json(Request(check_url, headers={"X-API-Key": api_key}, method="GET"))
        status = str(current.get("status") or "").lower()
        if status == "complete":
            return _validate_completed(current)
        if status in {"failed", "error", "cancelled", "canceled"} or current.get("success") is False:
            message = str(current.get("error") or "hosted conversion failed")
            raise DatalabExtractionError(f"Datalab conversion failed: {message}")

    raise DatalabExtractionError(
        f"Datalab conversion did not complete within {_poll_timeout_seconds()} seconds"
    )


def _validate_completed(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("success") is False:
        message = str(result.get("error") or "hosted conversion failed")
        raise DatalabExtractionError(f"Datalab conversion failed: {message}")
    return result


def _validate_check_url(url: str) -> None:
    parsed = urlparse(url)
    expected = urlparse(DATALAB_CONVERT_URL)
    if parsed.scheme != "https" or parsed.hostname != expected.hostname:
        raise DatalabExtractionError("Datalab returned an invalid result-check URL")


def _request_json(request: Request) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310 - fixed/validated HTTPS hosts
            payload = response.read()
    except HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise DatalabExtractionError(f"Datalab HTTP {exc.code}{suffix}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise DatalabExtractionError(f"Could not reach Datalab: {exc}") from exc
    try:
        value = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DatalabExtractionError("Datalab returned a non-JSON response") from exc
    if not isinstance(value, dict):
        raise DatalabExtractionError("Datalab returned an unexpected response")
    return value


def _multipart_body(fields: dict[str, str], raw_bytes: bytes) -> tuple[bytes, str]:
    boundary = f"learnloop-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="file"; filename="source.pdf"\r\n',
            b"Content-Type: application/pdf\r\n\r\n",
            raw_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _poll_timeout_seconds() -> int:
    raw = os.environ.get("LEARNLOOP_DATALAB_TIMEOUT_SECS", "").strip()
    try:
        value = int(raw)
    except ValueError:
        value = DEFAULT_POLL_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_POLL_TIMEOUT_SECONDS
