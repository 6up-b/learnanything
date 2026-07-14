"""Locator schemes (spec_source_ingestion_v2 §2.4). Back-compat is permanent.

New extractions cite ``block_span_v1`` (``span:<extraction_id>/<span_id>``). Three
legacy shapes are today unnamed bare strings pattern-matched by shape and MUST
resolve forever:

- ``heading_path_v1`` — ``root/section-slug/p1``
- ``time_range_v1``   — ``t=<start>-<end>``
- ``arxiv_label_v1``  — native labels like ``thm:4.2``, ``eq:1.2``

Scheme is declared per ref after backfill; schemes are never silently converted.
This module only *detects* a ref's scheme deterministically; legacy resolution
(``source_ingestion._locator_resolves`` / ``analyze_source_change``) is untouched.
"""

from __future__ import annotations

import re

BLOCK_SPAN_V1 = "block_span_v1"
HEADING_PATH_V1 = "heading_path_v1"
TIME_RANGE_V1 = "time_range_v1"
ARXIV_LABEL_V1 = "arxiv_label_v1"

KNOWN_SCHEMES = (BLOCK_SPAN_V1, HEADING_PATH_V1, TIME_RANGE_V1, ARXIV_LABEL_V1)

_BLOCK_SPAN_RE = re.compile(r"^span:(?P<extraction_id>[^/]+)/(?P<span_id>.+)$")
_TIME_RANGE_RE = re.compile(r"^t=[0-9]+(?:\.[0-9]+)?-[0-9]+(?:\.[0-9]+)?$")
# arXiv native labels: a short alpha prefix + ':' + a dotted numeric label
# (thm:4.2, eq:1.2, lem:3, cor:2.1, ...). Deliberately narrow so it never
# swallows a block-span (``span:...``) or time (``t=...``) shape.
_ARXIV_LABEL_RE = re.compile(r"^[a-z]{2,12}:[0-9]+(?:\.[0-9]+)*$", re.IGNORECASE)


def format_block_span(extraction_id: str, span_id: str) -> str:
    """Build a ``block_span_v1`` locator (§2.4)."""

    return f"span:{extraction_id}/{span_id}"


def parse_block_span(locator: str) -> tuple[str, str] | None:
    """Return ``(extraction_id, span_id)`` for a ``block_span_v1`` locator."""

    match = _BLOCK_SPAN_RE.match(locator.strip())
    if not match:
        return None
    return match.group("extraction_id"), match.group("span_id")


def detect_locator_scheme(locator: str) -> str | None:
    """Shape-detect the declared scheme of a (legacy or new) locator ref.

    Returns one of :data:`KNOWN_SCHEMES`, or ``None`` when the shape is
    unrecognized (which callers treat as an undeclared/opaque ref — never
    silently coerced).
    """

    candidate = (locator or "").strip()
    if not candidate:
        return None
    if candidate.startswith("span:") and _BLOCK_SPAN_RE.match(candidate):
        return BLOCK_SPAN_V1
    if _TIME_RANGE_RE.match(candidate):
        return TIME_RANGE_V1
    if "/" in candidate:
        return HEADING_PATH_V1
    if _ARXIV_LABEL_RE.match(candidate):
        return ARXIV_LABEL_V1
    return None
