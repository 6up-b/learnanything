"""Trivial IR for non-PDF sources (spec_source_ingestion_v2 §2.3).

HTML/text files and YouTube captions get honest, geometry-free ExtractionRuns:
HTML/textfile units come from headings, YouTube units from time ranges. This is
additive — the existing markdown outputs keep working; the IR path is a parallel,
non-destructive rendering of the same normalized content.

``transcript_to_ir`` is the transcript-aware path for standalone caption files
(WebVTT/SRT): per-turn blocks that keep speaker labels, and time-segmented units
carrying ``time_range`` locators — the same legacy locator scheme the YouTube
path uses, so span citation/resolution needs nothing new.
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
    extractor_version: str = "2",
) -> DocumentIR:
    """Build trivial IR from a markdown body: blocks by paragraph, units by
    top-level heading, with a level-2 (##) fallback when the level-1 structure
    collapses to a single unit (heading-path section trail, no geometry).

    Version history: "1" derived units from level-1 headings only; "2" adds the
    level-2 fallback, so cached "1" extractions must not be reused for it."""

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
        # A single level-1 heading (or none) collapses the whole document into one
        # unit, which makes unit selection useless. Before falling back to the
        # whole-document unit, try to derive units from the level-2 (##) structure.
        level2 = _units_from_level2(blocks)
        if level2 is not None:
            return level2
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


def _units_from_level2(blocks: list[DocumentBlock]) -> list[DocumentUnit] | None:
    """Derive units from the level-2 (##) section trail.

    Used only when the level-1 heading structure yields a single unit. Groups
    blocks by the second ``section_path`` segment (contiguous runs, first-seen
    order). Blocks with no second segment — content before the first ``##`` —
    form a leading ``(intro)`` unit. Returns ``None`` when there is no level-2
    structure at all, so the caller keeps the whole-document fallback."""

    l1 = blocks[0].section_path[0] if blocks[0].section_path else "root"
    groups: list[tuple[str | None, list[DocumentBlock]]] = []
    for block in blocks:
        seg = block.section_path[1] if len(block.section_path) >= 2 else None
        if groups and groups[-1][0] == seg:
            groups[-1][1].append(block)
        else:
            groups.append((seg, [block]))

    if not any(seg is not None for seg, _ in groups):
        return None

    units: list[DocumentUnit] = []
    for ordinal, (seg, group) in enumerate(groups, start=1):
        if seg is None:
            label = "(intro)"
            path = f"root/{l1}"
        else:
            label = seg
            path = f"root/{l1}/{seg}"
        units.append(
            DocumentUnit(
                unit_id=f"u{ordinal}",
                parent_unit_id=None,
                label=label,
                ordinal=ordinal,
                locator={"scheme": "heading_path", "path": path},
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
    extractor_version: str = "2",
) -> DocumentIR:
    """Build trivial IR from caption cues: one caption block per cue, one unit
    covering the transcript's time range (no geometry).

    Version history: "1" carried no per-cue timing; "2" stamps each block's
    ``extractor_block_id`` with its cue's ``t=<start>-<end>`` locator so the
    reader's watch mode can map playback time to caption spans."""

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
                extractor_block_id=f"t={float(cue.get('start') or 0.0):.1f}-{float(cue.get('end') or 0.0):.1f}",
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


# Transcript segmentation decision parameters: a new unit starts on a silence
# gap or a speaker change, but only once the current segment carries enough
# material to be a meaningful selection/inventory target on its own.
_TRANSCRIPT_GAP_SECONDS = 8.0
_TRANSCRIPT_MIN_SEGMENT_SECONDS = 120.0
_TRANSCRIPT_MAX_SEGMENT_SECONDS = 480.0
# Merge consecutive same-speaker cues into one block up to this many characters
# so blocks read as turns/paragraphs, not caption fragments.
_TRANSCRIPT_BLOCK_CHAR_CAP = 600


def _format_clock(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def transcript_to_ir(
    cues: list[Any],
    *,
    title: str | None,
    extractor_name: str = "transcript",
    extractor_version: str = "1",
) -> DocumentIR:
    """Build IR from parsed transcript cues (``learnloop.ingest.transcripts``).

    Blocks: consecutive cues from the same speaker merge into turn-sized Caption
    blocks (speaker label kept as a ``Name: `` prefix). Units: time segments cut
    on silence gaps / speaker changes, each with a ``time_range`` locator, so a
    long recording yields selectable units rather than one opaque blob.
    """

    # ── merge cues into turn blocks ──
    merged: list[dict[str, Any]] = []  # {start, end, speaker, text}
    for raw in cues:
        cue = raw if isinstance(raw, dict) else {
            "start": getattr(raw, "start", 0.0),
            "end": getattr(raw, "end", 0.0),
            "text": getattr(raw, "text", ""),
            "speaker": getattr(raw, "speaker", None),
        }
        text = str(cue.get("text") or "").strip()
        if not text:
            continue
        start = float(cue.get("start") or 0.0)
        end = float(cue.get("end") or 0.0)
        speaker = cue.get("speaker") or None
        last = merged[-1] if merged else None
        if (
            last is not None
            and last["speaker"] == speaker
            and start - last["end"] < _TRANSCRIPT_GAP_SECONDS
            and len(last["text"]) + len(text) + 1 <= _TRANSCRIPT_BLOCK_CHAR_CAP
        ):
            last["text"] = f"{last['text']} {text}"
            last["end"] = max(last["end"], end)
        else:
            merged.append({"start": start, "end": end, "speaker": speaker, "text": text})

    # ── cut segments (units) on gap / speaker change, bounded by duration ──
    segments: list[list[dict[str, Any]]] = []
    for turn in merged:
        current = segments[-1] if segments else None
        if current is None:
            segments.append([turn])
            continue
        seg_start = current[0]["start"]
        seg_duration = turn["end"] - seg_start
        gap = turn["start"] - current[-1]["end"]
        speaker_changed = turn["speaker"] != current[-1]["speaker"]
        long_enough = current[-1]["end"] - seg_start >= _TRANSCRIPT_MIN_SEGMENT_SECONDS
        if (long_enough and (gap >= _TRANSCRIPT_GAP_SECONDS or speaker_changed)) or (
            seg_duration >= _TRANSCRIPT_MAX_SEGMENT_SECONDS
        ):
            segments.append([turn])
        else:
            current.append(turn)

    blocks: list[DocumentBlock] = []
    units: list[DocumentUnit] = []
    for seg_ordinal, segment in enumerate(segments, start=1):
        seg_start = segment[0]["start"]
        seg_end = max(turn["end"] for turn in segment)
        seg_label = f"{_format_clock(seg_start)}–{_format_clock(seg_end)}"
        speakers = {turn["speaker"] for turn in segment if turn["speaker"]}
        if len(speakers) == 1:
            seg_label = f"{seg_label} · {next(iter(speakers))}"
        section_path = ["transcript", _slug(seg_label)]
        seg_blocks: list[DocumentBlock] = []
        for turn in segment:
            text = f"{turn['speaker']}: {turn['text']}" if turn["speaker"] else turn["text"]
            ordinal = len(blocks) + 1
            block = DocumentBlock(
                span_id=f"s{ordinal}",
                extractor_block_id=f"t={turn['start']:.1f}-{turn['end']:.1f}",
                block_type="Caption",
                role_hint="ordinary_prose",
                page=None,
                bbox=None,
                polygon=None,
                section_path=list(section_path),
                text=text,
                content_hash=block_content_hash(text),
                asset_ids=[],
                ordinal=ordinal,
            )
            blocks.append(block)
            seg_blocks.append(block)
        units.append(
            DocumentUnit(
                unit_id=f"u{seg_ordinal}",
                parent_unit_id=None,
                label=seg_label,
                ordinal=seg_ordinal,
                locator={"scheme": "time_range", "start": seg_start, "end": seg_end},
                semantic_hash=semantic_hash(seg_blocks),
                span_ids=[block.span_id for block in seg_blocks],
            )
        )

    return DocumentIR(
        ir_schema_version=IR_SCHEMA_VERSION,
        extractor=extractor_name,
        extractor_version=extractor_version,
        blocks=blocks,
        units=units,
    )
