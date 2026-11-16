"""What a figure's author is sent from the learner's books: the passage and its neighbours, or retrieved passages.

:func:`source_context` reads an anchored request's passage and the paragraphs around it (a neighbour that is exam
material is left out), and :func:`crop_image` a figure block's crop. :func:`ground` decides where an unanchored
request's text comes from (:class:`Grounding`: ``anchor``, ``retrieved`` from the sources service under the caller's
derived policy, each pick rechecked by :mod:`.protection`, or ``none``), and :func:`passages_context` turns the kept
passages into the same :class:`SourceContext`. ``find`` (:data:`FindSources`) is the retrieval a test or the
pre-build pass passes in. The build hashes what this module returns into the reuse key; this module imports
:mod:`.request` and :mod:`.protection`, nothing of the view, the listing or the build.
"""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.ai.execution import content_key
from learnloop.db.repositories import Repository
from learnloop.figure_admission import FiguresChanged
from learnloop.figure_admission import GROUNDING_PASSAGES as ADMISSION_GROUNDING_PASSAGES
from learnloop.figures.protection import keys_withheld
from learnloop.figures.request import FigureRefused, FigureRequest, anchored


#: keep: prompt size (:data:`learnloop.figure_admission.GROUNDING_PASSAGES`).
GROUNDING_PASSAGES = ADMISSION_GROUNDING_PASSAGES
FIGURE_BLOCK_TYPES = frozenset({"Figure", "FigureGroup", "Picture", "PictureGroup"})
#: Paragraphs on each side of the selection sent as context.
CONTEXT_BLOCKS = 2
PASSAGE_CHARS = 6_000
CONTEXT_CHARS = 3_000


@dataclass
class SourceContext:
    passage: list[dict[str, Any]] = field(default_factory=list)
    around: list[dict[str, Any]] = field(default_factory=list)
    #: Every sent span's text (for quote verification).
    span_texts: dict[str, str] = field(default_factory=dict)
    figure_span: str | None = None
    #: RW5d: every ``(extraction_id, span_id)`` sent from retrieved passages
    #: (their neighbours too), rechecked for held-out material on every delivery.
    keys: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Grounding:
    """Where a request's source text comes from (spec §8.3): ``anchor`` (the
    learner chose the passage), ``retrieved`` (found in their books for the
    goal) or ``none`` (nothing found: an illustration that quotes nothing)."""

    mode: str
    keys: list[tuple[str, str]] = field(default_factory=list)
    #: The kept passages as the figure line cites them (source title, section).
    passages: list[dict[str, Any]] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The source context (text and the crop only)
# ---------------------------------------------------------------------------

def source_context(vault: Any, repository: Repository, request: FigureRequest) -> SourceContext:
    from learnloop.content.sources.exam_material import exam_material

    ir = repository.load_document_ir(request.extraction_id)
    if ir is None:
        raise FigureRefused("not_found", "That source is not open in the Reader.")
    blocks = list(ir.blocks)
    index = {block.span_id: position for position, block in enumerate(blocks)}
    wanted = [span for span in request.span_ids if span in index]
    if request.region and request.region.get("span_id") in index and request.region["span_id"] not in wanted:
        wanted.append(str(request.region["span_id"]))
    if not wanted:
        raise FigureRefused("validation_error", "The selection names no passage of this source.")
    wanted.sort(key=lambda span: index[span])
    material = exam_material(vault, repository)
    context = SourceContext()
    for span in wanted:
        block = blocks[index[span]]
        text = " ".join((block.text or "").split())
        context.passage.append({"span_id": span, "type": block.block_type, "text": text[:PASSAGE_CHARS]})
        context.span_texts[span] = block.text or ""
        if block.block_type in FIGURE_BLOCK_TYPES and context.figure_span is None:
            context.figure_span = span
    first, last = index[wanted[0]], index[wanted[-1]]
    neighbours = blocks[max(0, first - CONTEXT_BLOCKS):first] + blocks[last + 1:last + 1 + CONTEXT_BLOCKS]
    for block in neighbours:
        if block.span_id in context.span_texts or material.covers(request.extraction_id, block.span_id):
            continue
        context.around.append({"span_id": block.span_id, "type": block.block_type,
                               "text": " ".join((block.text or "").split())[:CONTEXT_CHARS]})
        context.span_texts[block.span_id] = block.text or ""
    return context


def passages_context(vault: Any, repository: Repository, grounding: Grounding) -> SourceContext:
    """RW5d: the retrieved passages as the author is sent them (spec §8.2,
    §8.3): each kept block with the paragraphs around it (held-out ones left
    out), keyed ``extraction_id:span_id`` so a quote is verified against the
    right block of the right book. Nothing for ``none``."""

    from learnloop.content.sources.exam_material import exam_material

    context = SourceContext()
    if grounding.mode != "retrieved" or not grounding.keys:
        return context
    material = exam_material(vault, repository)
    titles = {(str(item.get("extraction_id")), str(item.get("span_id"))): item.get("source_title")
              for item in grounding.passages}
    documents: dict[str, Any] = {}
    placed: list[tuple[str, list[Any], int]] = []
    for extraction_id, span_id in grounding.keys:
        if extraction_id not in documents:
            documents[extraction_id] = repository.load_document_ir(extraction_id)
        ir = documents[extraction_id]
        if ir is None:
            continue
        blocks = list(ir.blocks)
        index = {block.span_id: position for position, block in enumerate(blocks)}
        if span_id not in index or material.covers(extraction_id, span_id):
            continue
        key = f"{extraction_id}:{span_id}"
        if key in context.span_texts:
            continue
        block = blocks[index[span_id]]
        entry: dict[str, Any] = {"span_id": key, "type": block.block_type,
                                 "text": " ".join((block.text or "").split())[:PASSAGE_CHARS]}
        if titles.get((extraction_id, span_id)):
            entry["source"] = str(titles[(extraction_id, span_id)])[:200]
        context.passage.append(entry)
        context.span_texts[key] = block.text or ""
        context.keys.append((extraction_id, span_id))
        placed.append((extraction_id, blocks, index[span_id]))
    # Then the paragraphs around each (a kept passage is never repeated as a neighbour).
    for extraction_id, blocks, position in placed:
        for neighbour in blocks[max(0, position - CONTEXT_BLOCKS):position] + blocks[position + 1:position + 1 + CONTEXT_BLOCKS]:
            near = f"{extraction_id}:{neighbour.span_id}"
            if near in context.span_texts or material.covers(extraction_id, neighbour.span_id):
                continue
            context.around.append({"span_id": near, "type": neighbour.block_type,
                                   "text": " ".join((neighbour.text or "").split())[:CONTEXT_CHARS]})
            context.span_texts[near] = neighbour.text or ""
            context.keys.append((extraction_id, str(neighbour.span_id)))
    return context


#: ``(vault, repository, query, *, caller, **kwargs) -> SourceHits``: the
#: sources service's verified retrieval (injected in tests).
FindSources = Callable[..., Any]


def _find_sources(vault: Any, repository: Repository, query: str, **kwargs: Any) -> Any:
    from learnloop.source_retrieval.find_sources import find_sources_for_caller

    return find_sources_for_caller(vault, repository, query, **kwargs)


def _reading_learning_objects(vault: Any, repository: Repository, reading_at: Mapping[str, Any] | None) -> list[str]:
    """The learning objects of the passage the learner was reading (retrieval context only)."""

    if not reading_at or not reading_at.get("extraction_id") or not reading_at.get("span_id"):
        return []
    try:
        from learnloop.source_retrieval.reader_tutor import passage_learning_objects

        return list(passage_learning_objects(vault, repository, extraction_id=str(reading_at["extraction_id"]),
                                             span_ids=[str(reading_at["span_id"])]))
    except Exception:  # noqa: BLE001 - context for ranking only; none is fine
        return []


def _passage_ref(hit: Mapping[str, Any]) -> dict[str, Any]:
    return {"extraction_id": str(hit.get("extraction_id")), "span_id": str(hit.get("span_id")),
            "source_id": hit.get("source_id"), "source_title": hit.get("source_title"), "section": hit.get("section"),
            "page": hit.get("page")}


def _with_sources(repository: Repository, passages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Each passage with its source's id and title (Codex review F8: the
    Reader's citation chips peek in this book and open another as a detour,
    which needs the source). Read from the stored extraction; a passage whose
    source cannot be read keeps what it had."""

    found: dict[str, tuple[str | None, str | None]] = {}
    shown = []
    for passage in passages:
        extraction_id = str(passage.get("extraction_id") or "")
        if extraction_id not in found:
            source_id, title = None, None
            try:
                run = repository.get_extraction_run(extraction_id) or {}
                revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
                source_id = revision.get("source_id")
                title = (repository.get_source_artifact(str(source_id)) or {}).get("display_title") if source_id else None
            except Exception:  # noqa: BLE001 - the chip only loses its detour
                pass
            found[extraction_id] = (source_id, title)
        source_id, title = found[extraction_id]
        shown.append({**passage, "source_id": passage.get("source_id") or source_id,
                      "source_title": passage.get("source_title") or title})
    return shown


def ground(vault: Any, repository: Repository, request: FigureRequest, *, find: FindSources | None = None
           ) -> Grounding:
    """A request's grounding (spec §8.3). With a passage, the anchor. With
    fixed keys (a tutor goal's cited spans, a revision's), those still allowed
    now. Otherwise the sources service's verified retrieval for the goal,
    under the caller's derived policy (exam material is withheld inside it),
    the reading position's learning objects as context: its verified picks,
    at most :data:`GROUNDING_PASSAGES`, each rechecked here. Nothing verified
    (or retrieval unavailable): ``none``, built anyway and labelled."""

    from learnloop.source_retrieval.policy import CallerContext

    if anchored(request):
        return Grounding("anchor")
    if request.grounding_keys is not None:
        given = list(dict.fromkeys((str(key[0]), str(key[1])) for key in request.grounding_keys))
        kept = [key for key in given if keys_withheld(vault, repository, [key]) is None][:GROUNDING_PASSAGES]
        mode = "none" if request.grounding_fixed == "none" or not kept else "retrieved"
        manifest = {"source": "given", "given": [list(key) for key in given],
                    "kept": [list(key) for key in kept] if mode == "retrieved" else []}
        if mode == "none":
            return Grounding("none", manifest=manifest)
        return Grounding("retrieved", kept, _with_sources(repository, [{"extraction_id": key[0], "span_id": key[1]}
                                                                      for key in kept]), manifest)
    caller = request.caller or CallerContext(kind="reader")
    query = request.goal_text or ""
    try:
        hits = (find or _find_sources)(
            vault, repository, query, caller=caller, intent="explain", verify=True, limit=GROUNDING_PASSAGES,
            learning_object_ids=_reading_learning_objects(vault, repository, request.reading_at),
            owner_id=f"figure_grounding:{content_key([query, request.extraction_id])[:24]}")
    except FiguresChanged:
        raise
    except Exception as exc:  # noqa: BLE001 - nothing found is an honest "not from your books"
        return Grounding("none", manifest={"source": "retrieval", "status": f"unavailable: {type(exc).__name__}"})
    manifest: dict[str, Any] = {"source": "retrieval", "status": getattr(hits, "status", "ok"),
                                "find_sources": dict(getattr(hits, "manifest", None) or {})}
    if manifest["status"] != "ok":
        # Unverified hits are not grounding: only the verification's picks are.
        return Grounding("none", manifest={**manifest, "kept": []})
    kept: list[tuple[str, str]] = []
    passages: list[dict[str, Any]] = []
    for hit in list(getattr(hits, "hits", None) or ()):
        key = (str(hit.get("extraction_id") or ""), str(hit.get("span_id") or ""))
        if not all(key) or key in kept or keys_withheld(vault, repository, [key]) is not None:
            continue
        kept.append(key)
        passages.append(_passage_ref(hit))
        if len(kept) >= GROUNDING_PASSAGES:
            break
    manifest["kept"] = [list(key) for key in kept]
    if not kept:
        return Grounding("none", manifest=manifest)
    return Grounding("retrieved", kept, _with_sources(repository, passages), manifest)


def _decode(render: str | None) -> tuple[str, bytes] | None:
    if not render or not render.startswith("data:") or ";base64," not in render:
        return None
    header, data = render.split(";base64,", 1)
    try:
        return header[len("data:"):], base64.b64decode(data, validate=True)
    except (ValueError, TypeError):
        return None


def crop_image(repository: Repository, request: FigureRequest, context: SourceContext
               ) -> tuple[tuple[str, bytes] | None, str | None, list[float] | None]:
    """``(image, asset span, clipped region box)``: a region's crop only, or
    the figure block's crop; nothing for a selection with no figure."""

    from learnloop.reader.span_view import build_block_region

    if request.region:
        found = build_block_region(repository, request.extraction_id, str(request.region["span_id"]),
                                   bbox=[float(value) for value in request.region.get("bbox") or ()])
        image = _decode(found.get("region_render"))
        if image is None:
            raise FigureRefused("region_unreadable", "LearnLoop couldn't crop that region of the page.")
        return image, str(request.region["span_id"]), found.get("bbox")
    if context.figure_span is not None:
        found = build_block_region(repository, request.extraction_id, context.figure_span)
        if found.get("reason") == "crop":
            return _decode(found.get("region_render")), context.figure_span, None
    return None, None, None


__all__ = [
    "CONTEXT_BLOCKS",
    "CONTEXT_CHARS",
    "FIGURE_BLOCK_TYPES",
    "FindSources",
    "GROUNDING_PASSAGES",
    "Grounding",
    "PASSAGE_CHARS",
    "SourceContext",
    "crop_image",
    "ground",
    "passages_context",
    "source_context",
]
