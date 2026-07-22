"""Across-source text search for the Reader library.

Deterministic substring search over the current extraction of every ready,
reader-enabled source — the "where did I read that?" journey. Purely local
(no model, no evidence): each hit carries enough identity to open the source
and jump to the exact block span.
"""

from __future__ import annotations

import json
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.source_outline import resolve_extraction_id

MAX_HITS = 40
_SNIPPET_RADIUS = 90


def _artifact_title(artifact: dict[str, Any], revision: dict[str, Any] | None) -> str:
    return str(
        artifact.get("display_title")
        or (revision or {}).get("original_uri")
        or artifact.get("canonical_uri")
        or artifact.get("id")
    )


def _snippet(text: str, needle: str) -> str:
    flat = " ".join(text.split())
    at = flat.lower().find(needle.lower())
    if at < 0:
        return flat[: 2 * _SNIPPET_RADIUS]
    start = max(0, at - _SNIPPET_RADIUS)
    end = min(len(flat), at + len(needle) + _SNIPPET_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(flat) else ""
    return f"{prefix}{flat[start:end]}{suffix}"


def search_sources(
    repository: Repository, *, query: str, limit: int = MAX_HITS
) -> dict[str, Any]:
    """Search every reader-enabled source's current extraction for ``query``."""

    needle = (query or "").strip()
    if len(needle) < 2:
        return {"query": needle, "hits": [], "searched_sources": 0}

    extraction_meta: dict[str, dict[str, Any]] = {}
    for artifact in repository.all_source_artifacts():
        if not artifact.get("reader_enabled", 1):
            continue
        source_id = str(artifact["id"])
        extraction_id = resolve_extraction_id(repository, source_id)
        if extraction_id is None:
            continue
        run = repository.get_extraction_run(extraction_id) or {}
        revision = repository.get_source_revision(str(run.get("revision_id") or ""))
        extraction_meta[extraction_id] = {
            "source_id": source_id,
            "title": _artifact_title(artifact, revision),
        }

    rows = repository.search_source_blocks(
        query=needle, extraction_ids=list(extraction_meta), limit=limit
    )
    hits: list[dict[str, Any]] = []
    for row in rows:
        meta = extraction_meta.get(str(row["extraction_id"]))
        if meta is None:
            continue
        try:
            section_path = json.loads(row.get("section_path_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            section_path = []
        hits.append({
            "source_id": meta["source_id"],
            "source_title": meta["title"],
            "extraction_id": row["extraction_id"],
            "span_id": row["span_id"],
            "section": str(section_path[-1]) if section_path else None,
            "page": row.get("page"),
            "snippet": _snippet(str(row.get("text") or ""), needle),
        })
    return {"query": needle, "hits": hits, "searched_sources": len(extraction_meta)}
