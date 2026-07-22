"""Source render views + display<->source-block crosswalk (spec §3.1-3.3, design
B step 1).

A render view is a REPLACEABLE marker-markdown/KaTeX presentation over the
immutable source bytes and the versioned extraction IR. It is created lazily (one
per actively opened extraction, §13.1.1) and is idempotent on a canonical
``request_hash`` so repeating the render reuses the standing view (§15.10).

For slice 1 the render is derived deterministically from the extraction IR: each
``DocumentBlock`` becomes one display node whose markdown is the block text, with a
1:1 crosswalk carrying disposable highlight-only display offsets. Source text is
treated as UNTRUSTED data (§3.3): it is sanitized for display (no script/embed/
local-file refs) and delimited as data, never executed.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository

RENDER_SCHEMA_VERSION = "render-view-v1"
RENDERER = "marker_markdown"

# Authority layers stated on every response (§3.1).
AUTHORITY_LAYERS = {
    "source_bytes": "authoritative immutable artifact",
    "source_revision": "immutable identity/version of those bytes",
    "extraction_ir": "versioned derived representation; may contain errors",
    "render_view": "replaceable marker-markdown/KaTeX presentation",
    "source_object": "per-source reviewed/proposed semantic object",
    "canonical_domain": "reviewed cross-source facets/LOs/blueprints",
}

_SCRIPT_RE = re.compile(r"<\s*script", re.IGNORECASE)
_EMBED_RE = re.compile(r"<\s*(iframe|embed|object)\b", re.IGNORECASE)
_JS_URI_RE = re.compile(r"javascript:", re.IGNORECASE)
_FILE_URI_RE = re.compile(r"file:/{2}", re.IGNORECASE)


def sanitize_source_text(text: str) -> tuple[str, bool]:
    """Neutralize script execution / external embeds / local-file refs in untrusted
    source text (§3.3). Returns ``(safe_text, was_modified)``. Never blanks the
    content -- unsafe fragments become visible inert text."""

    modified = False
    safe = text
    if _SCRIPT_RE.search(safe) or _EMBED_RE.search(safe):
        safe = _SCRIPT_RE.sub("&lt;script", safe)
        safe = _EMBED_RE.sub(lambda m: "&lt;" + m.group(1), safe)
        modified = True
    if _JS_URI_RE.search(safe):
        safe = _JS_URI_RE.sub("javascript&#58;", safe)
        modified = True
    if _FILE_URI_RE.search(safe):
        safe = _FILE_URI_RE.sub("file&#58;//", safe)
        modified = True
    return safe, modified


def _request_hash(*, revision_id: str, extraction_id: str, renderer_version: str) -> str:
    canonical = "|".join([RENDERER, renderer_version, RENDER_SCHEMA_VERSION, revision_id, extraction_id])
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_crosswalk(ir: Any) -> list[dict[str, Any]]:
    """One display node per source block (1:1), with disposable display offsets."""

    nodes: list[dict[str, Any]] = []
    for ordinal, block in enumerate(sorted(ir.blocks, key=lambda b: b.ordinal)):
        safe, _ = sanitize_source_text(block.text)
        nodes.append(
            {
                "display_node_id": f"node-{block.span_id}",
                "display_ordinal": ordinal,
                "extraction_id": None,  # filled by caller
                "span_id": block.span_id,
                "block_content_hash": block.content_hash,
                "block_ordinal": block.ordinal,
                "display_start": 0,
                "display_end": len(safe),
                "katex_node_ids": [],
                "asset_ids": list(block.asset_ids),
                "status": "mapped",
            }
        )
    return nodes


def resolve_or_create_render_view(
    repository: Repository,
    *,
    revision_id: str | None = None,
    extraction_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Lazy + idempotent render-view resolution keyed on ``request_hash``."""

    run = repository.get_extraction_run(extraction_id)
    if run is None:
        raise ValueError(f"unknown extraction: {extraction_id!r}")
    revision_id = revision_id or run.get("revision_id")
    revision = repository.get_source_revision(revision_id) if hasattr(repository, "get_source_revision") else None
    source_id = (revision or {}).get("source_id") if isinstance(revision, dict) else None
    if source_id is None:
        source_id = run.get("source_id")
    renderer_version = str(run.get("extractor_version") or "1")

    request_hash = _request_hash(revision_id=revision_id, extraction_id=extraction_id, renderer_version=renderer_version)
    existing = repository.render_view_by_request_hash(request_hash)
    if existing is not None:
        return existing

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ValueError(f"extraction has no IR: {extraction_id!r}")

    content_hash = "sha256:" + hashlib.sha256(
        "|".join(b.content_hash for b in sorted(ir.blocks, key=lambda b: b.ordinal)).encode("utf-8")
    ).hexdigest()
    asset_ids = sorted({a for b in ir.blocks for a in b.asset_ids})
    asset_manifest_hash = "sha256:" + hashlib.sha256("|".join(asset_ids).encode("utf-8")).hexdigest()

    view_id = repository.insert_render_view(
        {
            "source_id": source_id,
            "revision_id": revision_id,
            "extraction_id": extraction_id,
            "renderer": RENDERER,
            "renderer_version": renderer_version,
            "schema_version": RENDER_SCHEMA_VERSION,
            "content_hash": content_hash,
            "asset_manifest_hash": asset_manifest_hash,
            "status": "ready",
            "health_summary": {"block_count": len(ir.blocks)},
            "request_hash": request_hash,
            "result_hash": content_hash,
        },
        clock=clock,
    )
    nodes = build_crosswalk(ir)
    for node in nodes:
        node["extraction_id"] = extraction_id
    repository.insert_render_crosswalk_nodes(view_id, nodes, clock=clock)
    view = repository.get_render_view(view_id)
    assert view is not None
    return view


def render_payload(repository: Repository, render_view_id: str) -> dict[str, Any]:
    """The reader render payload: sanitized display nodes + per-block health + the
    six authority layers (§3.1)."""

    view = repository.get_render_view(render_view_id)
    if view is None:
        raise ValueError(f"unknown render view: {render_view_id!r}")
    extraction_id = view["extraction_id"]
    ir = repository.load_document_ir(extraction_id)
    blocks_by_span = {b.span_id: b for b in ir.blocks} if ir else {}
    health_rows = {h["span_id"]: h for h in repository.block_health_for_extraction(extraction_id)}

    blocks: list[dict[str, Any]] = []
    for node in repository.render_crosswalk(render_view_id):
        span_id = node.get("span_id")
        block = blocks_by_span.get(span_id)
        raw_text = block.text if block is not None else ""
        safe, modified = sanitize_source_text(raw_text)
        health = health_rows.get(span_id)
        blocks.append(
            {
                "display_node_id": node["display_node_id"],
                "span_id": span_id,
                "block_type": block.block_type if block is not None else None,
                # Extractor-native block id. For caption blocks (captions_to_ir
                # v2 / transcript_to_ir) this is the cue's "t=<start>-<end>"
                # locator — the watch mode's playback-time ↔ span mapping.
                "extractor_block_id": block.extractor_block_id if block is not None else None,
                "markdown": safe,
                "sanitized": modified,
                "katex_nodes": [],
                "assets": list(block.asset_ids) if block is not None else [],
                "health": {
                    "status": (health or {}).get("status", "unknown"),
                    "recommended_view": (health or {}).get("recommended_view", "derived"),
                    "reason_flags": _loads_list((health or {}).get("reason_flags_json")),
                },
            }
        )
    return {
        "render_view_id": render_view_id,
        "extraction_id": extraction_id,
        "revision_id": view["revision_id"],
        "source_id": view["source_id"],
        "renderer": view["renderer"],
        "renderer_version": view["renderer_version"],
        "content_hash": view["content_hash"],
        "status": view["status"],
        "blocks": blocks,
        "layers": AUTHORITY_LAYERS,
    }


def _loads_list(value: str | None) -> list[Any]:
    import json

    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []
