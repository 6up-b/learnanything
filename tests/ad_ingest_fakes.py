"""Readings built by the REAL ingest derivation, for AD's "never extracted" comparisons (the AD23
redesign round 7).

A document is a list of :class:`Element` (a header or a body block, with the span id AD's
references use). :func:`ingest_ir` emulates only what an extractor reports before ingest derives
anything (Marker's blocks with their ``section_hierarchy``, as Marker computes it from the headers
present; GLM-OCR's layout regions) and runs the production converter over it
(``marker.chunk_output_to_ir``, ``glm_ocr.responses_to_ir``): section paths, role hints, ordinals,
layout ids, units and GLM's split-label join are what ingest derives. A "never extracted" copy is
the same document with the withheld elements deleted BEFORE that run, never a copy of stored
derived columns. Span ids are then given back their element's id (ingest numbers spans by
position), so both copies name the same blocks.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable, Sequence

import yaml

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository

from tests.helpers import write_yaml

T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
MARKER, GLM = "marker", "glm"


@dataclass(frozen=True)
class Element:
    span_id: str
    kind: str  # "header" or "text"
    text: str
    level: int = 1


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _marker_blocks(elements: Sequence[Element]) -> list[dict[str, Any]]:
    """Marker's own output for the elements present: ids count blocks per type, and each block's
    ``section_hierarchy`` is the stack of the headers present before it (Marker's derivation)."""

    counters: dict[str, int] = {}
    stack: dict[int, str] = {}
    blocks = []
    for element in elements:
        block_type = "SectionHeader" if element.kind == "header" else "Text"
        index = counters.get(block_type, 0)
        counters[block_type] = index + 1
        block_id = f"/page/0/{block_type}/{index}"
        if element.kind == "header":
            stack = {level: value for level, value in stack.items() if level < element.level}
            stack[element.level] = block_id
        html = f"<h{element.level + 1}>{element.text}</h{element.level + 1}>" if element.kind == "header" \
            else f"<p>{element.text}</p>"
        blocks.append({"id": block_id, "block_type": block_type, "html": html,
                       "section_hierarchy": {str(level): value for level, value in sorted(stack.items())},
                       "page": 0})
    return blocks


def _glm_result(elements: Sequence[Element]) -> dict[str, Any]:
    regions = []
    for index, element in enumerate(elements):
        top = 60 + 60 * index
        region = {"index": index, "label": "text", "content": element.text, "bbox_2d": [100, top, 1100, top + 40],
                  "width": 1224, "height": 1584 + 60 * len(elements)}
        if element.kind == "header":
            # The layout model's title region, its text as recognized (multi-line, double-spaced).
            region.update({"native_label": "paragraph_title", "level": element.level + 1})
        regions.append(region)
    return {"layout_details": [regions], "data_info": {"pages": [{"width": 1224, "height": 1584 + 60 * len(elements)}]}}


def ingest_ir(elements: Sequence[Element], *, style: str) -> Any:
    """The production converter's IR for ``elements``, its spans renamed to the elements' ids."""

    from learnloop.ingest.extractors import glm_ocr, marker

    if style == MARKER:
        ir = marker.chunk_output_to_ir(blocks=_marker_blocks(elements), extractor_version="1")
    else:
        height = 792.0 + 30 * len(elements)
        ir = glm_ocr.responses_to_ir([(_glm_result(elements), [0])], sizes=[(612.0, height)], outline=[], version="v")
    assert len(ir.blocks) == len(elements), [block.text for block in ir.blocks]
    rename = {block.span_id: element.span_id for block, element in zip(ir.blocks, elements)}
    blocks = [block.model_copy(update={"span_id": rename[block.span_id]}) for block in ir.blocks]
    units = [unit.model_copy(update={"span_ids": [rename.get(span, span) for span in unit.span_ids]})
             for unit in ir.units]
    return ir.model_copy(update={"blocks": blocks, "units": units})


def never_extracted(elements: Sequence[Element], withheld: Iterable[str]) -> list[Element]:
    gone = set(withheld)
    return [element for element in elements if element.span_id not in gone]


def build_copy(root, readings: dict[str, Sequence[Element]], *, style: str, cite: Sequence[tuple[str, str]],
               viewed: Sequence[tuple[str, str]], learning_object: str):
    """A vault whose source has the given readings (extraction id -> elements, in order, all of one
    revision), each persisted from :func:`ingest_ir`; ``learning_object`` cites ``cite`` (extraction,
    span) and the Reader viewed ``viewed``."""

    from tests.ad23_fakes import ad23_vault
    from tests.test_source_inventory import _persist

    paths = ad23_vault(root, items=("pi_m1a",))
    made = _iso(T0 - timedelta(days=7))
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                           "VALUES ('src_ne', 'pdf', 'file:///ne.pdf', ?, ?)", (made, made))
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) "
                           "VALUES ('rev_ne', 'src_ne', 'sha256:ne', ?)", (made,))
        connection.commit()
    repository = Repository(paths.sqlite_path)
    for version, (extraction, elements) in enumerate(readings.items(), start=1):
        ir = ingest_ir(elements, style=style)
        ir = ir.model_copy(update={"extractor_version": f"{ir.extractor_version}.{version}"})
        _persist(repository, ir, revision_id="rev_ne", extraction_id=extraction)
    path = paths.learning_object_path("linear-algebra", learning_object)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": "src_ne", "source_id": "src_ne", "extraction_id": extraction,
        "span_ids": [span], "locator": f"span:{extraction}/{span}"} for extraction, span in cite]}
    write_yaml(path, payload)
    for number, (extraction, span) in enumerate(viewed):
        repository.insert_source_exposure_event(
            {"context": "reader", "extraction_id": extraction, "span_id": span, "revision_id": "rev_ne",
             "source_id": "src_ne", "entity_type": "reader", "entity_id": f"visit_ne_{number}",
             "created_at": _iso(T0 - timedelta(hours=5, minutes=number))})
    return paths


__all__ = ["Element", "GLM", "MARKER", "T0", "build_copy", "ingest_ir", "never_extracted"]
