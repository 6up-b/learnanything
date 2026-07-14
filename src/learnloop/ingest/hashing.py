"""The source-layer hash model (spec_source_ingestion_v2 §2.2).

Four distinct hashes, each with a different job:

- ``asset_hash`` — raw fetched bytes; identifies the SourceRevision.
- ``extraction_request_hash`` — computable *before* execution (revision +
  extractor + package/model versions + config + page selection + IR schema
  version). It is the retry/idempotency key for an ExtractionRun.
- ``extraction_result_hash`` — request hash + produced IR; the completed run's
  content identity (cache/view identity).
- ``semantic_hash`` — deterministic normalized text view per unit; the LLM-facing
  content, so cosmetic HTML/geometry changes must not invalidate it.

The request/result split exists because a retry key must be computable before a
run completes; a hash that includes the output cannot key the retry ladder.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Iterable, Mapping

from learnloop.ingest.ir import DocumentBlock, DocumentIR

# Block types whose text content is kept verbatim in the semantic view — math and
# tabular content must survive normalization untouched (§2.2).
_VERBATIM_BLOCK_TYPES = {
    "equation",
    "equationnumber",
    "inlinemath",
    "math",
    "table",
    "tablecell",
    "code",
    "codeblock",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_PAGE_NUMBER_RE = re.compile(r"^(?:page\s+)?\d{1,4}$", re.IGNORECASE)


def _sha256(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def asset_hash(raw_bytes: bytes) -> str:
    """Hash of the raw fetched bytes; the SourceRevision identity (§2.2)."""

    return _sha256(raw_bytes)


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def extraction_request_hash(
    *,
    revision_id: str,
    extractor: str,
    extractor_version: str,
    package_version: str | None = None,
    model_versions: Mapping[str, str] | None = None,
    config: Mapping[str, Any] | None = None,
    page_selection: Iterable[int] | None = None,
    ir_schema_version: str,
) -> str:
    """Idempotency/retry key for a *requested* ExtractionRun (§2.2, §2.5).

    Computable before execution. Includes the extractor package version and model
    artifact versions (best-effort), so a marker upgrade changes the key — fixing
    the stale-cache bug where a marker upgrade silently served stale output.
    """

    payload = {
        "revision_id": revision_id,
        "extractor": extractor,
        "extractor_version": extractor_version,
        "package_version": package_version or "",
        "model_versions": dict(sorted((model_versions or {}).items())),
        "config": _sanitized_config(config or {}),
        "page_selection": sorted(page_selection) if page_selection is not None else None,
        "ir_schema_version": ir_schema_version,
    }
    return _sha256(_canonical_json(payload))


def _sanitized_config(config: Mapping[str, Any]) -> dict[str, Any]:
    # Never let a secret enter a durable cache key (mirrors pdf_extraction).
    return {key: value for key, value in config.items() if "api_key" not in key.lower()}


def extraction_result_hash(request_hash: str, ir: DocumentIR) -> str:
    """Completed-run content identity: request hash + produced IR (§2.2)."""

    payload = {
        "request_hash": request_hash,
        "ir": ir.model_dump(mode="json"),
    }
    return _sha256(_canonical_json(payload))


def normalize_semantic_text(blocks: Iterable[DocumentBlock]) -> str:
    """Deterministic normalized text view over a unit's blocks (§2.2).

    Strip markup/styling, collapse whitespace, drop repeated page headers/footers
    and bare page numbers, keep equation/table cell content verbatim, exclude
    geometry/ids. Because math is kept verbatim, a marker upgrade that changes
    LaTeX rendering *will* invalidate math-heavy caches — expected and honest.
    """

    blocks = list(blocks)
    boilerplate = _repeated_boilerplate(blocks)
    lines: list[str] = []
    for block in blocks:
        verbatim = block.block_type.replace(" ", "").lower() in _VERBATIM_BLOCK_TYPES
        text = block.text if verbatim else _strip_markup(block.text)
        if not verbatim:
            stripped = text.strip()
            if not stripped:
                continue
            if _PAGE_NUMBER_RE.match(stripped):
                continue
            if stripped in boilerplate:
                continue
        else:
            text = block.text.strip("\n")
            if not text.strip():
                continue
        lines.append(text.strip() if not verbatim else text)
    return "\n".join(lines).strip()


def _repeated_boilerplate(blocks: list[DocumentBlock]) -> set[str]:
    """Short prose lines that recur across many pages are headers/footers."""

    pages_seen: dict[str, set[int]] = {}
    total_pages: set[int] = set()
    for block in blocks:
        if block.page is None:
            continue
        total_pages.add(block.page)
        if block.block_type.replace(" ", "").lower() in _VERBATIM_BLOCK_TYPES:
            continue
        normalized = _strip_markup(block.text).strip()
        if not normalized or len(normalized) > 120:
            continue
        pages_seen.setdefault(normalized, set()).add(block.page)
    if len(total_pages) < 3:
        return set()
    threshold = max(3, (len(total_pages) + 1) // 2)
    return {text for text, pages in pages_seen.items() if len(pages) >= threshold}


def _strip_markup(text: str) -> str:
    without_tags = _TAG_RE.sub(" ", text)
    unescaped = (
        without_tags.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .replace("&nbsp;", " ")
    )
    return _WS_RE.sub(" ", unescaped).strip()


def semantic_hash(blocks: Iterable[DocumentBlock]) -> str:
    """Per-unit semantic hash over the normalized text view (§2.2)."""

    return _sha256(normalize_semantic_text(blocks))


def block_type_histogram(blocks: Iterable[DocumentBlock]) -> dict[str, int]:
    return dict(Counter(block.block_type for block in blocks))
