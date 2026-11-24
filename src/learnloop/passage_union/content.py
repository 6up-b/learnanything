"""``passage.content`` (spec §9.2 "a piece of another source", review finding 12): a range of one reading as the
source has it, so a ``source_piece`` holds the source's words and never a search row's label.

Per passage: its canonical text (the extraction's own, unclipped), its page, its time on a transcript (a cue's
``t=<start>-<end>``) and its section; beside them, once, the source and its title. Exam or held-out material is
withheld (no text; ``withheld`` true), so nothing protected is copied into a pad. Read only: it writes nothing.
"""
from __future__ import annotations

import re
from typing import Any

from learnloop.content.sources.exam_material import exam_withheld, surface_material
from learnloop.content.sources.span_aliases import reading_source
from learnloop.passage_union.union import UnionError, span_range
from learnloop.section_map import extraction_sections

_CUE_TIME = re.compile(r"^t=([0-9.]+)-([0-9.]+)$")


def _title(repository: Any, source_id: str | None) -> str | None:
    if source_id is None:
        return None
    artifact = repository.get_source_artifact(source_id) or {}
    revision = repository.get_source_revision(str(artifact.get("current_revision_id") or "")) or {}
    return str(artifact.get("display_title") or revision.get("original_uri") or artifact.get("canonical_uri")
               or source_id)


def passage_content(vault: Any, repository: Any, *, extraction_id: str, from_span_id: str | None = None,
                    to_span_id: str | None = None, t0: float | None = None, t1: float | None = None,
                    surface: str | None = None) -> dict[str, Any]:
    """``{extraction_id, source_id, title, withheld, spans: [{span_id, text, page, t0, t1, section_id,
    section_label, withheld}]}`` for one range (two passages, or two times over a transcript). A span is withheld
    when it is exam material, or (``surface``) when that surface's row of ``exam_material.SURFACE_SETS`` holds it:
    the exercise sheet reads with the import's own set, so a practice exam that is not held out shows its words."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise UnionError("extraction_not_found", f"No reading {extraction_id!r}.")
    span_ids = span_range(ir, from_span_id=from_span_id, to_span_id=to_span_id, t0=t0, t1=t1)
    sections, blocks, span_to_section = extraction_sections(ir)
    labels = {str(section["id"]): section.get("label") for section in sections}
    by_span = {block.span_id: block for block in ir.blocks}
    if surface is None:
        withheld = set(exam_withheld(vault, repository, [(extraction_id, span) for span in span_ids]))
    else:
        material = surface_material(vault, repository, surface)
        withheld = {(extraction_id, span) for span in span_ids if material.covers(extraction_id, span)}
    out = []
    for span_id in span_ids:
        block = by_span[span_id]
        cue = _CUE_TIME.match(str(getattr(block, "extractor_block_id", "") or ""))
        hidden = (extraction_id, span_id) in withheld
        section_id = span_to_section.get(span_id)
        out.append({
            "span_id": span_id, "text": None if hidden else str(block.text or ""), "page": getattr(block, "page", None),
            "t0": float(cue.group(1)) if cue else None, "t1": float(cue.group(2)) if cue else None,
            "section_id": section_id, "section_label": labels.get(section_id) if section_id else None,
            "withheld": hidden,
        })
    source_id = reading_source(repository, extraction_id)
    return {"extraction_id": extraction_id, "source_id": source_id, "title": _title(repository, source_id),
            "withheld": any(row["withheld"] for row in out), "spans": out}


__all__ = ["passage_content"]
