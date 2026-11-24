"""Passage provenance checked at the workbench's text-bearing destinations."""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Any

from pydantic import Field

from learnloop.content.sources.exam_material import SURFACE_SETS, exam_material, exam_withheld, surface_material
from learnloop.db.stores import pad_reads
from learnloop.pads.emission import context_blocks
from learnloop.reader.source_identity import selection_span_ids
from learnloop_sidecar.dto import ParamsModel
from learnloop_sidecar.errors import SidecarError

REFUSAL = "This selection contains exam or held-out material."


class PassageSelection(ParamsModel):
    extraction_id: str = Field(min_length=1)
    span_ids: list[str] = Field(min_length=1)


def reading_places(extraction_id: str | None, spans: Iterable[str | None]) -> list[tuple[str, str]]:
    selected = [span for span in spans if span]
    if selected and not extraction_id:
        raise SidecarError("validation_error", "Selected passages need their reading.")
    return [(extraction_id, span) for span in selected] if extraction_id else []


def payload_places(payload: Mapping[str, Any]) -> list[tuple[str, str]]:
    if not isinstance(payload, Mapping):
        raise SidecarError("validation_error", "A passage anchor needs its reading and passages.")
    extraction = payload.get("extraction_id", payload.get("extractionId"))
    span = payload.get("span_id", payload.get("spanId"))
    spans = payload.get("span_ids", payload.get("spanIds", []))
    if not isinstance(spans, list) or not all(isinstance(s, str) and s for s in spans):
        raise SidecarError("validation_error", "The selected passages must be a list of passage ids.")
    return reading_places(extraction, [*([span] if span else []), *spans])


#: A run of this many words copied verbatim from a protected passage marks a quote as coming from it; shorter overlaps
#: are ordinary phrases ("the kernel of a map") that any learner writes.
QUOTE_RUN_WORDS = 8
_WORD = re.compile(r"\w+")


def _words(text: str) -> list[str]:
    return _WORD.findall(text.casefold())


def repeats_protected_text(vault: Any, repository: Any, text: str) -> bool:
    """Whether words with no recorded passage repeat exam or held-out material: a run of :data:`QUOTE_RUN_WORDS`
    words (or, for a shorter quote, all of it) found verbatim in a protected passage. A protected reading that cannot
    be read counts as repeated (fail closed)."""

    words = _words(text or "")
    material = exam_material(vault, repository).material
    if not words or material.empty:
        return False
    runs = ({" ".join(words[i:i + QUOTE_RUN_WORDS]) for i in range(len(words) - QUOTE_RUN_WORDS + 1)}
            if len(words) >= QUOTE_RUN_WORDS else {" ".join(words)})
    for extraction_id in material.touched:
        ir = repository.load_document_ir(extraction_id)
        if ir is None:
            return True
        whole = extraction_id in material.extractions
        for block in ir.blocks:
            if whole or (extraction_id, str(block.span_id)) in material.spans:
                held = " ".join(_words(str(block.text or "")))
                if any(run in held for run in runs):
                    return True
    return False


def check_placed_quote(vault: Any, repository: Any, origins: list[tuple[str, str]], text: str) -> None:
    # A quote with no recorded passage (an older pad's) is refused only when its words repeat protected material:
    # refusing every such quote while anything is protected would stop the learner reusing their own notes.
    if not origins and repeats_protected_text(vault, repository, text):
        raise SidecarError("exam_material", REFUSAL)


def block_places(vault: Any, repository: Any, block_ids: Iterable[str]) -> list[tuple[str, str]]:
    ids = list(dict.fromkeys(block_ids))
    if not ids:
        return []
    places = []
    with repository.connection() as connection:
        for block_id in ids:
            head = pad_reads.head(connection, block_id)
            if head is None or head["tombstone"]:
                raise SidecarError("block_not_found", "That pad line is gone.")
            blocks, _ = context_blocks(connection, head)
            links = pad_reads.standing_anchors_for_blocks(connection, blocks)
            payload = head["payload"] or {}
            origins = [(row["extraction_id"], row["span_id"]) for row in links]
            origins.extend(payload_places(payload))
            if head["kind"] in {"source_quote", "source_piece"}:
                check_placed_quote(vault, repository, origins, str(head["body_md"] or ""))
            places.extend(origins)
            for origin in [*blocks, *(payload.get("source_block_ids") or [])]:
                if origin not in ids:
                    ids.append(origin)
    return list(dict.fromkeys(places))


def withheld_at(vault: Any, repository: Any, places: Iterable[tuple[str, str]], surface: str | None = None) -> bool:
    """Whether any place is withheld: all exam material, or (``surface``) that surface's own row of
    ``exam_material.SURFACE_SETS`` (the Reader's ask, checks and import read the held-out partition only)."""

    places = [(str(e), str(s)) for e, s in places]
    if not places:
        return False
    if surface is None:
        return bool(exam_withheld(vault, repository, places))
    material = surface_material(vault, repository, surface)
    return any(material.covers(e, s) for e, s in places)


#: Each menu verb's destination and the row of ``exam_material.SURFACE_SETS`` it withholds by, the one table the
#: menu's per-verb verdict reads (None: a destination new with the workbench, which withholds all exam material). A
#: verb is withheld exactly when its destination's own check would refuse, so on a practice exam that is not held out
#: the menu offers what the classic Reader offers (its Ask, import and checks read the held-out partition).
VERB_SURFACES: Mapping[str, tuple[str | None, ...]] = MappingProxyType({
    "ask": ("reader_ask",),                         # companion.ask, as the Reader's Ask
    "make_practice": ("reader_import", "reader_checks"),  # reader.import_exercise, reader.author_section_question
    "compare": ("compare",),                        # a desk's compare window, then reader.library_compare
    "show_me": ("figures",),                        # figure.request
    "teach_me": ("teaching",),                      # lesson.turn
    "find": (None,),                                # search.everything with the selection
    "carry": (None,),                               # carried.carry
    "append": (None,),                              # a pad's source quote or piece
})


def withheld_verbs(vault: Any, repository: Any, places: Iterable[tuple[str, str]]) -> list[str]:
    """The menu verbs whose destination withholds any of ``places`` (each set is read once)."""

    places = [(str(e), str(s)) for e, s in places]
    by_set: dict[str, bool] = {}

    def held(surface: str | None) -> bool:
        kind = SURFACE_SETS[surface] if surface is not None else "default"
        if kind not in by_set:
            by_set[kind] = withheld_at(vault, repository, places, surface)
        return by_set[kind]

    return sorted(verb for verb, surfaces in VERB_SURFACES.items() if any(held(surface) for surface in surfaces))


def refuse_protected(vault: Any, repository: Any, places: Iterable[tuple[str, str]], *, surface: str | None = None,
                     code: str = "exam_material", message: str = REFUSAL) -> None:
    """Refuse when any place is withheld. A destination that had its own protection before the workbench passes
    its surface (the set it withholds) and its own refusal's code and words, so this check never changes what
    that path refuses or the contract its callers read."""

    if withheld_at(vault, repository, places, surface):
        raise SidecarError(code, message)


def check_selection(vault: Any, repository: Any, extraction_id: str, raw: Mapping[str, Any],
                    render_view_id: str | None, *, surface: str | None = None) -> None:
    spans = selection_span_ids(raw)
    spans.extend(span for _, span in payload_places({**raw, "extraction_id": extraction_id}))
    unresolved = not spans and not raw.get("nodes")
    crosswalk = None
    for node in raw.get("nodes") or []:
        if not isinstance(node, Mapping):
            raise SidecarError("validation_error", "Each selected node needs its source location.")
        if node.get("spanId") or node.get("span_id"):
            continue
        if crosswalk is None:
            crosswalk = {row["display_node_id"]: row["span_id"] for row in
                         (repository.render_crosswalk(render_view_id) if render_view_id else [])}
        span = crosswalk.get(node.get("displayNodeId") or node.get("display_node_id"))
        if span:
            spans.append(span)
        else:
            unresolved = True
    material = exam_material(vault, repository).material if surface is None else surface_material(vault, repository, surface)
    if unresolved and extraction_id in material.touched:
        raise SidecarError("exam_material", REFUSAL)
    refuse_protected(vault, repository, reading_places(extraction_id, spans), surface=surface)
