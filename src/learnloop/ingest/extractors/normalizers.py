"""Trivial IR for non-PDF sources (spec_source_ingestion_v2 §2.3).

HTML/text files and YouTube captions get honest, geometry-free ExtractionRuns:
HTML/textfile units come from headings, YouTube units from time ranges. This is
additive — the existing markdown outputs keep working; the IR path is a parallel,
non-destructive rendering of the same normalized content.
"""

from __future__ import annotations

import re
from typing import Any

from learnloop.ingest.block_roles import classify_block_role
from learnloop.ingest.hashing import semantic_hash
from learnloop.ingest.ir import (
    IR_SCHEMA_VERSION,
    DocumentBlock,
    DocumentIR,
    DocumentUnit,
    block_content_hash,
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def markdown_to_ir(
    markdown: str,
    *,
    title: str | None,
    extractor_name: str,
    extractor_version: str = "1",
) -> DocumentIR:
    """Build trivial IR from a markdown body: blocks by paragraph, units by
    top-level heading (heading-path section trail, no geometry)."""

    blocks: list[DocumentBlock] = []
    section_path: list[str] = ["root"]
    path_by_level: dict[int, str] = {1: "root"}
    current: list[str] = []
    in_fence = False
    fence_start = ""

    def flush() -> None:
        text = "\n".join(current).strip()
        current.clear()
        if not text:
            return
        ordinal = len(blocks) + 1
        block_type = "Code" if text.startswith("```") else ("Equation" if text.startswith("$$") else "Text")
        blocks.append(
            DocumentBlock(
                span_id=f"s{ordinal}",
                extractor_block_id=None,
                block_type=block_type,
                role_hint=classify_block_role(block_type, section_path, text),
                page=None,
                bbox=None,
                polygon=None,
                section_path=list(section_path),
                text=text,
                content_hash=block_content_hash(text),
                asset_ids=[],
                ordinal=ordinal,
            )
        )

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        heading = _HEADING_RE.match(line)
        if heading and not in_fence:
            flush()
            level = len(heading.group(1))
            slug = _slug(heading.group(2))
            for existing in list(path_by_level):
                if existing >= level:
                    del path_by_level[existing]
            path_by_level[level] = slug
            section_path = [path_by_level[i] for i in sorted(path_by_level)]
            continue
        if line.startswith("```") or line.startswith("$$"):
            current.append(line)
            if not in_fence:
                in_fence = True
                fence_start = line[:3]
            elif line.startswith(fence_start):
                in_fence = False
            continue
        if not line.strip() and not in_fence:
            flush()
            continue
        current.append(line)
    flush()

    units = _units_from_headings(blocks, title=title)
    return DocumentIR(
        ir_schema_version=IR_SCHEMA_VERSION,
        extractor=extractor_name,
        extractor_version=extractor_version,
        blocks=blocks,
        units=units,
    )


def _units_from_headings(blocks: list[DocumentBlock], *, title: str | None) -> list[DocumentUnit]:
    if not blocks:
        return []
    # Group by top-level section. A level-1 heading replaces the synthetic
    # "root" segment, so the first path segment names the section.
    groups: list[tuple[str, list[DocumentBlock]]] = []
    for block in blocks:
        key = block.section_path[0] if block.section_path else "root"
        if groups and groups[-1][0] == key:
            groups[-1][1].append(block)
        else:
            groups.append((key, [block]))

    if len(groups) <= 1:
        return [
            DocumentUnit(
                unit_id="u1",
                parent_unit_id=None,
                label=title or "Document",
                ordinal=1,
                locator={"scheme": "heading_path", "path": "root"},
                semantic_hash=semantic_hash(blocks),
                span_ids=[block.span_id for block in blocks],
            )
        ]

    units: list[DocumentUnit] = []
    for ordinal, (key, group) in enumerate(groups, start=1):
        units.append(
            DocumentUnit(
                unit_id=f"u{ordinal}",
                parent_unit_id=None,
                label=key,
                ordinal=ordinal,
                locator={"scheme": "heading_path", "path": f"root/{key}"},
                semantic_hash=semantic_hash(group),
                span_ids=[block.span_id for block in group],
            )
        )
    return units


def captions_to_ir(
    cues: list[Any],
    *,
    title: str | None,
    extractor_name: str = "youtube",
    extractor_version: str = "1",
) -> DocumentIR:
    """Build trivial IR from caption cues: one caption block per cue, one unit
    covering the transcript's time range (no geometry)."""

    blocks: list[DocumentBlock] = []
    for index, raw in enumerate(cues, start=1):
        cue = raw if isinstance(raw, dict) else {
            "start": getattr(raw, "start", 0.0),
            "end": getattr(raw, "end", 0.0),
            "text": getattr(raw, "text", ""),
        }
        text = str(cue.get("text") or "").strip()
        if not text:
            continue
        ordinal = len(blocks) + 1
        blocks.append(
            DocumentBlock(
                span_id=f"s{ordinal}",
                extractor_block_id=None,
                block_type="Caption",
                role_hint="ordinary_prose",
                page=None,
                bbox=None,
                polygon=None,
                section_path=["transcript"],
                text=text,
                content_hash=block_content_hash(text),
                asset_ids=[],
                ordinal=ordinal,
            )
        )

    if not blocks:
        return DocumentIR(
            ir_schema_version=IR_SCHEMA_VERSION,
            extractor=extractor_name,
            extractor_version=extractor_version,
        )

    starts = [float((cue if isinstance(cue, dict) else {}).get("start", 0.0)) for cue in cues]
    ends = [float((cue if isinstance(cue, dict) else {}).get("end", 0.0)) for cue in cues]
    unit = DocumentUnit(
        unit_id="u1",
        parent_unit_id=None,
        label=title or "Transcript",
        ordinal=1,
        locator={
            "scheme": "time_range",
            "start": min(starts) if starts else 0.0,
            "end": max(ends) if ends else 0.0,
        },
        semantic_hash=semantic_hash(blocks),
        span_ids=[block.span_id for block in blocks],
    )
    return DocumentIR(
        ir_schema_version=IR_SCHEMA_VERSION,
        extractor=extractor_name,
        extractor_version=extractor_version,
        blocks=blocks,
        units=[unit],
    )
